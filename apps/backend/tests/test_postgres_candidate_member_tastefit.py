"""TasteFit capture acceptance uses real PostgreSQL and frozen owner APIs."""

from uuid import uuid4

import pytest
from app.domain.resolution import ResolutionError
from app.modules.households.models import HouseholdMember, Membership
from app.modules.identity.models import User
from app.modules.planning.tastefit_public import capture_candidate_member_tastefit_sources
from app.modules.planning.tastefit_public import derive_candidate_member_tastefit as derive
from app.modules.planning.tastefit_public import validate_candidate_member_tastefit as validate
from sqlalchemy import event, inspect, text
from sqlalchemy.orm import Session
from tastefit_fixtures import request
from tastefit_postgres_fixtures import (
    add_parent,
    author_current_mapping,
    capture,
    clone_recipe_version,
    configure_exact,
    configure_hierarchy,
    declare,
    prepare,
    publish_prior,
    sessions,
)
from tastefit_postgres_fixtures import hierarchy_server as hierarchy_server
from tastefit_postgres_fixtures import tastefit_server as tastefit_server

pytestmark = pytest.mark.postgres


def fails(operation, code=None):
    with pytest.raises(ResolutionError) as exc:
        operation()
    if code:
        assert exc.value.code == code, exc.value.detail
    return exc.value


def row(result, kind="PROTEIN"):
    return next(r for r in result.targets if r.proof.target.kind == kind)


def add_member(s):
    with Session(s["engines"]["root"]) as db:
        m = HouseholdMember(household_id=s["request"].household_id, name="Disposable shared diner")
        db.add(m)
        db.commit()
        return m.id


def rebind_grounding(s, grounding, *, member=None):
    from app.modules.planning.contracts import CandidateFeatureProjectionRequest
    from test_postgres_candidate_grounding import read

    result = read(s["engines"]["root"], grounding)
    assert result.status == "GROUNDED", result
    projection = CandidateFeatureProjectionRequest(
        grounding_request=grounding,
        expected_grounding_fingerprint=result.candidate.fingerprint,
        requested_dimensions=s["request"].projection_request.requested_dimensions,
    )
    return request(
        projection,
        s["request"].member_interpretation,
        s["request"].policy,
        member_id=member or s["request"].member_id,
    )


def test_tf01_real_canonical_capture_derive_validate_one_subject(tastefit_server):
    s = prepare(tastefit_server)
    before = capture(s)
    target = before.member_sources.entries[0].target
    declare(s, target)
    source = capture(s)
    result = derive(source)
    assert validate(result) == result
    assert result.subject.member_id == s["request"].member_id
    assert result.subject.projection_fingerprint == source.projection.fingerprint
    assert any(r.status == "AVAILABLE" for r in result.targets)
    assert result.sources == source


def test_tf02_shared_subject_is_not_replaced_by_tracked_member(tastefit_server):
    s = prepare(tastefit_server)
    target = capture(s).member_sources.entries[0].target
    declare(s, target, value="LIKE")
    member = add_member(s)
    g = s["request"].projection_request.grounding_request
    from app.modules.households.contracts import MealParticipants

    participants = MealParticipants(
        participants=g.participants.participants
        + (dict(member_id=member, portion_factor="0.5", nutrition_role="SHARED"),)
    )
    q = rebind_grounding(s, g.model_copy(update=dict(participants=participants)), member=member)
    result = derive(capture(s, q=q))
    assert result.subject.member_id == member
    assert result.subject.grounding_request.tracked_member_id != member
    assert all(r.member_views.explicit.evidence_strength.level == "NONE" for r in result.targets)
    assert all(r.direct_signal == "NONE" and r.value is None for r in result.targets)


def test_tf03_unauthorized_actor_fails_before_preferences_read(tastefit_server):
    s = prepare(tastefit_server)
    statements = []

    def observe(conn, cursor, sql, *args):
        statements.append(sql)

    engine = s["engines"]["root"]
    event.listen(engine, "before_cursor_execute", observe)
    try:
        fails(lambda: capture(s, actor=uuid4()), "CAPTURE_ACCESS_DENIED")
    finally:
        event.remove(engine, "before_cursor_execute", observe)
    assert not any("member_preference_declarations" in sql for sql in statements)


def test_tf04_canonical_member_absent_from_candidate_not_added(tastefit_server):
    s = prepare(tastefit_server)
    member = add_member(s)
    q = rebind_grounding(s, s["request"].projection_request.grounding_request, member=member)
    fails(lambda: capture(s, q=q), "SUBJECT_MEMBER_NOT_IN_CANDIDATE_CONTEXT")


def test_tf05_foreign_household_member_cannot_be_subject(tastefit_server):
    a, b = prepare(tastefit_server), prepare(tastefit_server)
    q = a["request"].model_copy(update=dict(member_id=b["request"].member_id))
    fails(lambda: capture(a, q=q), "SUBJECT_OWNER_MISMATCH")


def test_tf06_expected_grounding_pin_rejects_fresh_substitution(tastefit_server):
    s = prepare(tastefit_server)
    projection = s["request"].projection_request.model_copy(
        update=dict(expected_grounding_fingerprint="f" * 64)
    )
    q = s["request"].model_copy(update=dict(projection_request=projection))
    fails(lambda: capture(s, q=q), "EXPECTED_GROUNDING_MISMATCH")


def test_tf11_actor_and_member_are_distinct_authenticated_read_subjects(tastefit_server):
    s = prepare(tastefit_server)
    with Session(s["engines"]["root"]) as db:
        u = User(display_name="Disposable delegated reader")
        db.add(u)
        db.flush()
        db.add(
            Membership(
                household_id=s["request"].household_id, user_id=u.id, role="VIEWER", member_id=None
            )
        )
        db.commit()
        actor = u.id
    source = capture(s, actor=actor)
    assert source.candidate_frame.actor_user_id == actor
    assert source.request.member_id == s["request"].member_id
    assert all(f.actor_user_id == actor for f in source.member_sources.frames)
    assert derive(source).policy_authority == "EXPLICIT_INTERPRETATION_INPUT_ONLY"


def test_tf12_fresh_projection_identity_not_old_fp_pin(tastefit_server):
    s = prepare(tastefit_server)
    a, b = capture(s), capture(s)
    assert a.projection.fingerprint != b.projection.fingerprint
    assert a.projection.binding.grounding_fingerprint == b.projection.binding.grounding_fingerprint
    assert validate(derive(a)).sources == a
    data = s["request"].model_dump() | dict(
        expected_projection_fingerprint=a.projection.fingerprint
    )
    fails(lambda: capture(s, q=data))


def test_tf14_selected_substitution_only_original_ingredient_absent(tastefit_server):
    from app.modules.preferences.contracts import IngredientPreferenceTarget
    from app.modules.recipes.contracts import VariantGenerationRequest
    from app.modules.recipes.public import generate_variants

    s = prepare(tastefit_server, dimensions=("METHOD",))
    recipe = clone_recipe_version(s, substitution=True)
    variants = generate_variants(
        VariantGenerationRequest(
            recipe=recipe,
            demand=dict(rule_selections=(dict(rule_ids=(recipe.variant_rules[0].id,)),)),
            limits=dict(max_attempts=20, max_candidates=20),
        )
    )
    selected = next(c for c in variants.candidates if c.selected_rule_ids)
    g = s["request"].projection_request.grounding_request.model_copy(
        update=dict(candidate=selected)
    )
    q = rebind_grounding(s, g)
    original = IngredientPreferenceTarget(ingredient_id=recipe.ingredients[0].ingredient_id)
    q = q.model_copy(update=dict(diagnostic_targets=(original,)))
    s = dict(s, request=q)
    selected_target = IngredientPreferenceTarget(
        ingredient_id=selected.resolved_ingredients[0].ingredient_id
    )
    declare(s, selected_target)
    result = derive(capture(s))
    positive = next(r for r in result.targets if r.proof.target == selected_target)
    absent = next(r for r in result.targets if r.proof.target == original)
    assert positive.status == "AVAILABLE" and positive.proof.candidate_state == "PRESENT"
    assert absent.proof.candidate_state == "ABSENT" and absent.value is None
    assert positive.proof.requirement_ids == (recipe.ingredients[0].id,)


def test_tf15_main_protein_is_reviewed_exact_path_not_mass(tastefit_server):
    s = prepare(tastefit_server)
    result = derive(capture(s))
    r = row(result)
    assert r.proof.dimension.review_id == s["publications"]["MAIN_PROTEIN"][1].review_id
    assert r.proof.term_resolution.state == "PRESENT"
    assert r.proof.target.kind == "PROTEIN"
    support = result.sources.projection.source.feature_input.sources.scopes
    assert any(scope.reviews[-1].command.supports for scope in support)


def test_tf17_flavor_admission_is_exact_reviewed_finite_term(tastefit_server):
    s = prepare(tastefit_server)
    result = derive(capture(s))
    r = row(result, "FLAVOR")
    assert r.proof.dimension.review_id == s["publications"]["FLAVOR"][1].review_id
    assert r.proof.target.feature_term_id == s["terms"]["FLAVOR"][0].id
    assert result.subject.binding.path == result.sources.projection.source.feature_input.path


def test_tf20_nonselected_probes_absent_nonexistent_identity_fails(tastefit_server):
    s = prepare(tastefit_server)
    from app.modules.preferences.contracts import IngredientPreferenceTarget, RecipePreferenceTarget

    probe = IngredientPreferenceTarget.model_validate(add_parent(s))
    other = prepare(tastefit_server)
    recipe_probe = RecipePreferenceTarget(recipe_id=capture(other).projection.binding.recipe_id)
    q = s["request"].model_copy(update=dict(diagnostic_targets=(probe, recipe_probe)))
    result = derive(capture(s, q=q))
    r = next(r for r in result.targets if r.proof.target == probe)
    assert r.proof.candidate_state == "ABSENT" and r.value is None
    recipe_row = next(r for r in result.targets if r.proof.target == recipe_probe)
    assert recipe_row.proof.candidate_state == "ABSENT" and recipe_row.value is None
    missing = probe.model_copy(update=dict(ingredient_id=uuid4()))
    fails(lambda: capture(s, q=q.model_copy(update=dict(diagnostic_targets=(missing,)))))


def test_tf28_catalog_support_correction_stales_reviewed_main_protein(tastefit_server):
    from app.modules.catalog.public import IngredientProteinService, ingredient_protein_frontier

    s = prepare(tastefit_server)
    before = capture(s)
    command, receipt = s["publications"]["catalog"]
    with Session(s["engines"]["root"]) as db:
        replacement = type(command).model_validate(
            command.model_dump()
            | dict(
                expected_revision_no=command.expected_revision_no + 1,
                predecessor_id=receipt.review_id,
                expected_catalog_frontier=ingredient_protein_frontier(db),
                correction_reason="Disposable correction",
                provenance=command.provenance.model_dump() | dict(external_record_id=uuid4().hex),
                idempotency_key=uuid4().hex,
            )
        )
        IngredientProteinService(db, actor_user_id=s["actor"]).write(replacement)
        db.commit()
    fresh = derive(capture(s))
    assert "STALE_ASSOCIATION" in {d.reason for d in fresh.dimensions}
    assert not any(r.proof.target.kind == "PROTEIN" for r in fresh.targets)
    assert row(derive(before)).proof.candidate_state == "PRESENT"


def test_tf40_retry_history_does_not_increase_strength_or_fit(tastefit_server):
    s = prepare(tastefit_server)
    target = capture(s).member_sources.entries[0].target
    key = uuid4().hex
    a = declare(s, target, key=key)
    from app.modules.preferences.public import PreferenceService

    with Session(s["engines"]["root"]) as db:
        b = PreferenceService(db, actor_user_id=s["actor"]).write(a.command)
        db.commit()
    assert a == b
    result = derive(capture(s))
    r = next(r for r in result.targets if r.proof.target == target)
    assert r.evidence_strength.level == "LOW"
    assert r.value.amount.numerator == 1 and r.value.amount.denominator == 2
    corrected = declare(s, target, old=a, value="DISLIKE")
    declare(s, target, old=corrected, value="LIKE")
    fresh = derive(capture(s))
    current = next(r for r in fresh.targets if r.proof.target == target)
    assert (
        current.value.amount == r.value.amount
        and current.evidence_strength.level == r.evidence_strength.level
    )


def test_tf41_correction_changes_fresh_head_retained_capture_replays(tastefit_server):
    s = prepare(tastefit_server)
    target = capture(s).member_sources.entries[0].target
    a = declare(s, target)
    old = capture(s)
    declare(s, target, value="DISLIKE", old=a)
    fresh = derive(capture(s))
    assert (
        next(r for r in fresh.targets if r.proof.target == target).direct_signal
        == "DECLARED_DISLIKE"
    )
    assert (
        next(r for r in derive(old).targets if r.proof.target == target).direct_signal
        == "DECLARED_LIKE"
    )


def test_tf45_real_empty_prior_source_uses_frozen_explicit_only(tastefit_server):
    s = configure_exact(prepare(tastefit_server))
    declare(s, s["selected_target"])
    s = author_current_mapping(s, prior=True)
    r = row(derive(capture(s, prior=True)))
    assert r.member_views.exact_target.effective.mode == "EXPLICIT_ONLY"
    assert r.member_views.exact_target.mapped_prior.reason == "NO_PUBLICATION"
    assert r.status == "AVAILABLE"


def test_tf48_real_empty_prior_selected_stays_unavailable(tastefit_server):
    s = configure_exact(prepare(tastefit_server))
    r = row(derive(capture(s, prior=True)))
    assert r.reason == "SELECTED_EVIDENCE_UNAVAILABLE" and r.source_reason == "NO_PUBLICATION"
    assert r.value is None and r.selected_mode == "PRIOR_ONLY"


def test_tf49_prior_retraction_preserves_reason_and_explicit_only(tastefit_server):
    s = configure_exact(prepare(tastefit_server))
    declare(s, s["selected_target"])
    published = publish_prior(s)
    before = capture(s, prior=True)
    publish_prior(s, old=published, retract=True)
    result = derive(capture(s, prior=True))
    r = row(result)
    assert r.member_views.exact_target.mapped_prior.reason == "RETRACTED"
    assert r.member_views.exact_target.effective.mode == "EXPLICIT_ONLY"
    assert (
        row(derive(before)).member_views.exact_target.effective.mode == "BLENDED_EXPLICIT_AND_PRIOR"
    )


def test_tf53_required_prior_permission_failure_aborts_whole_capture(tastefit_server):
    s = configure_exact(prepare(tastefit_server))
    with sessions(s, prior=True) as cuts:
        # The hierarchy reader has no prior enrollment/capability for this provider.
        cuts["prior"] = Session(
            s["engines"]["reader"].execution_options(
                isolation_level="REPEATABLE READ", postgresql_readonly=True
            )
        )
        try:
            fails(
                lambda: capture_candidate_member_tastefit_sources(
                    cuts, s["request"], actor_user_id=s["actor"]
                ),
                "SOURCE_CAPTURE_FAILED",
            )
        finally:
            cuts["prior"].close()


def test_tf55_raw_mode_needs_no_configured_global_provider(tastefit_server):
    s = prepare(tastefit_server)
    result = derive(capture(s))
    assert {f.owner for f in result.sources.member_sources.frames} == {"MEMBER"}
    assert all(
        ("PRIOR_ONLY", "NOT_REQUESTED_BY_POLICY") in r.view_dispositions for r in result.targets
    )


def test_tf57_real_reviewed_one_hop_transfer_maps_parent_explicit(tastefit_server):
    s = configure_hierarchy(prepare(tastefit_server))
    declare(s, s["parent_target"])
    s = author_current_mapping(s, prior=True, hierarchy=True)
    result = derive(capture(s, prior=True, hierarchy=True))
    r = row(result)
    assert r.status == "AVAILABLE" and r.selected_mode == "ONE_HOP_INHERITED"
    assert (
        r.member_views.one_hop.inherited.trace.relation_revision_id
        == s["relation_receipt"].publication.id
    )
    assert not any(r.proof.target == s["parent_target"] for r in result.targets)


def test_tf60_real_parent_retraction_no_destination_prior_fallback(tastefit_server):
    s = configure_hierarchy(prepare(tastefit_server))
    a = declare(s, s["parent_target"])
    publish_prior(s)
    declare(s, s["parent_target"], old=a, retract=True)
    r = row(derive(capture(s, prior=True, hierarchy=True)))
    assert r.source_reason == "PARENT_MEMBER_RETRACTED" and r.value is None
    assert r.member_views.exact_target.effective.mode == "PRIOR_ONLY_COLD_START"


@pytest.mark.parametrize("condition", ["no_relation", "missing_policy", "retracted", "denied"])
def test_tf62_real_hierarchy_unavailability_is_not_neutral(tastefit_server, condition):
    s = configure_hierarchy(
        prepare(tastefit_server),
        publish_policy=condition != "missing_policy",
        publish_relation=condition not in {"no_relation", "missing_policy"},
    )
    from hierarchy_postgres_fixtures import publication, publish

    if condition == "retracted":
        receipt = s["relation_receipt"]
        publish(
            s["hierarchy"],
            publication(
                s["hierarchy"],
                identity=receipt.publication.command.identity,
                operation="RETRACT",
                old=receipt,
            ),
        )
    elif condition == "denied":
        original = s["hierarchy"]["policy"]
        body = original.model_dump()
        body["policy_version"] += 1
        for d in body["directions"]:
            d.update(enabled=False, rows=[], support_modes=[], attenuation=None)
        p = type(original).model_validate(body)
        publish(s["hierarchy"], publication(s["hierarchy"], policy=p, old=s["policy_receipt"]))
        # New pinned conditional request names the actual changed policy body.
        from tastefit_fixtures import fit_policy, interpretation

        old = s["request"].member_interpretation
        mp = interpretation(
            old.explicit_policy,
            old.compatibility_policy,
            old.shrinkage_policy,
            p,
            s["hierarchy"]["provider"],
        )
        fp = fit_policy(
            mp,
            kinds=("PROTEIN",),
            mode="EXACT_TARGET_AND_ONE_HOP",
            undeclared="ONE_HOP_INHERITED",
            mappings={},
        )
        s["request"] = request(s["request"].projection_request, mp, fp)
    r = row(derive(capture(s, prior=True, hierarchy=True)))
    assert r.value is None and r.source_reason is not None
    assert r.member_views.one_hop.inherited.status == "UNAVAILABLE"


def test_tf63_multiple_incoming_relations_no_favorable_parent_filter(tastefit_server):
    s = configure_hierarchy(prepare(tastefit_server))
    declare(s, s["parent_target"])
    second = add_parent(s)
    from hierarchy_postgres_fixtures import publication, publish

    old = s["relation_receipt"].publication.command
    identity = old.identity.model_copy(update=dict(source=second))
    publish(s["hierarchy"], publication(s["hierarchy"], identity=identity, relation=old.relation))
    r = row(derive(capture(s, prior=True, hierarchy=True)))
    assert r.value is None and "MULTIPLE" in r.source_reason
    assert r.member_views.one_hop.parent_target is None


@pytest.mark.parametrize("context", ["version", "path"])
def test_tf66_valid_other_recipe_context_unavailable_forged_binding_rejects(
    tastefit_server, context
):
    from app.modules.recipes.contracts import FeatureSelectedPath
    from feature_fixtures import review_command
    from preference_fixtures import term
    from tastefit_fixtures import wire

    s = prepare(tastefit_server)
    recipe = capture(s).projection.source.grounded_candidate.sources.recipe
    if context == "version":
        other = clone_recipe_version(s)
        binding = dict(endpoint="DESTINATION", recipe_version_id=other.id, key=None, path=None)
    else:
        command = review_command(recipe, (term("FLAVOR"),), dimension="FLAVOR")
        key = command.key.model_copy(update=dict(tier_ids=(recipe.portion_tiers[-1].id,)))
        path = FeatureSelectedPath(
            tier_id=recipe.portion_tiers[-1].id,
            selected_rule_ids=(),
            deltas=tuple((r.id, 0) for r in recipe.ingredients),
        )
        binding = dict(endpoint="DESTINATION", recipe_version_id=recipe.id, key=key, path=path)
    s = configure_hierarchy(s, destination_kind="DIRECT_RECIPE", recipe_bindings=(binding,))
    declare(s, s["parent_target"])
    source = capture(s, prior=True, hierarchy=True)
    result = derive(source)
    r = row(result, "DIRECT_RECIPE")
    assert r.member_views.one_hop.inherited.status == "AVAILABLE"
    assert r.reason == "INHERITED_DESTINATION_CONTEXT_MISMATCH" and r.value is None
    data = wire(result)
    claim = next(r for r in data["targets"] if r["proof"]["target"]["kind"] == "DIRECT_RECIPE")
    claim["member_views"]["one_hop"]["inherited"]["trace"]["relation_identity"]["recipe_bindings"][
        0
    ]["recipe_version_id"] = str(recipe.id if context == "version" else uuid4())
    fails(lambda: validate(data))


def test_tf89_all_member_children_share_full_ledger_on_one_rr_cut(tastefit_server):
    s = configure_hierarchy(prepare(tastefit_server))
    declare(s, s["parent_target"])
    source = capture(s, prior=True, hierarchy=True)
    from app.modules.preferences.tastefit_contracts import member_ledger_body

    ledgers = [
        member_ledger_body(e.explicit.source.preferences) for e in source.member_sources.entries
    ]
    assert all(b == ledgers[0] for b in ledgers)
    assert len(source.member_sources.entries) == 6
    clocks = {e.explicit.source.preferences.captured_at for e in source.member_sources.entries}
    assert len(clocks) > 1


def test_tf92_independent_legal_owner_clocks_and_frontiers_not_common_mvcc(tastefit_server):
    s = configure_hierarchy(prepare(tastefit_server))
    declare(s, s["parent_target"])
    publish_prior(s)
    source = capture(s, prior=True, hierarchy=True)
    result = derive(source)
    assert len({f.started_at for f in source.member_sources.frames}) > 1
    assert result.common_mvcc == "NOT_CLAIMED"
    entry = next(e for e in source.member_sources.entries if e.one_hop)
    assert entry.exact_target.reference_source.frontier != entry.one_hop.hierarchy_source.frontier


def test_tf93_feature_capture_after_grounding_asof_is_not_forced_historical_cut(tastefit_server):
    s = prepare(tastefit_server)
    source = capture(s)
    asof = source.request.projection_request.grounding_request.as_of
    assert any(
        review.recorded_at > asof
        for scope in source.projection.source.feature_input.sources.scopes
        for review in scope.reviews
    )
    assert derive(source).interpretation_mode == "VERSIONED_CONSUMER_POLICY_REPLAY"


def test_tf96_retained_all_owner_cuts_replay_after_live_corrections(tastefit_server):
    s = configure_hierarchy(prepare(tastefit_server))
    old = declare(s, s["parent_target"])
    publication = publish_prior(s)
    before = capture(s, prior=True, hierarchy=True)
    declare(s, s["parent_target"], old=old, retract=True)
    publish_prior(s, old=publication, retract=True)
    from hierarchy_postgres_fixtures import publication as command
    from hierarchy_postgres_fixtures import publish

    relation = s["relation_receipt"]
    publish(
        s["hierarchy"],
        command(
            s["hierarchy"],
            identity=relation.publication.command.identity,
            operation="RETRACT",
            old=relation,
        ),
    )
    after = capture(s, prior=True, hierarchy=True)
    assert row(derive(before)).member_views.one_hop.inherited.status == "AVAILABLE"
    assert row(derive(after)).value is None
    assert validate(derive(before)).sources == before


def test_tf97_independent_hierarchy_capability_not_minted_by_prior_read(tastefit_server):
    s = configure_hierarchy(prepare(tastefit_server))
    with sessions(s, prior=True, hierarchy=True, who="prior_reader") as cuts:
        # This principal has real prior CAPTURE and no hierarchy authority.
        fails(
            lambda: capture_candidate_member_tastefit_sources(
                cuts, s["request"], actor_user_id=s["actor"]
            ),
            "SOURCE_CAPTURE_FAILED",
        )


@pytest.mark.parametrize("owner", ["PRIOR", "HIERARCHY"])
def test_tf99_revoked_capture_cannot_reuse_old_valid_child(tastefit_server, owner):
    s = configure_hierarchy(prepare(tastefit_server))
    before = capture(s, prior=True, hierarchy=True)
    if owner == "PRIOR":
        from app.modules.preferences.reference_priors import (
            capture_reference_prior_sources,
        )
        from app.modules.preferences.reference_priors import (
            change_reference_prior_authority as change,
        )

        with sessions(s, prior=True) as cuts:
            cut = capture_reference_prior_sources(
                cuts["prior"],
                dict(provider_id=s["prior_provider"].id, requested_targets=(s["selected_target"],)),
            )
        provider, principal = s["prior_provider"].id, s["prior_principals"]["reader"].id
    else:
        from app.modules.preferences.hierarchy_sources import (
            capture_hierarchy_sources,
        )
        from app.modules.preferences.hierarchy_sources import (
            change_hierarchy_authority as change,
        )

        with sessions(s, hierarchy=True) as cuts:
            cut = capture_hierarchy_sources(
                cuts["hierarchy"],
                dict(
                    provider_id=s["hierarchy"]["provider"].id,
                    policy_id=s["hierarchy"]["policy"].policy_id,
                    requested_targets=(s["selected_target"],),
                ),
            )
        provider, principal = s["hierarchy"]["provider"].id, s["principals"]["reader"].id
    with Session(s["engines"]["prior_admin" if owner == "PRIOR" else "admin"]) as db:
        change(
            db,
            dict(
                provider_id=provider,
                principal_id=principal,
                capability="CAPTURE",
                action="REVOKE",
                expected_authority_generation=cut.frontier.authority_generation,
                reason="Disposable revoke",
                idempotency_key=uuid4().hex,
            ),
        )
        db.commit()
    fails(lambda: capture(s, prior=True, hierarchy=True), "SOURCE_CAPTURE_FAILED")
    assert validate(derive(before)).sources == before


def test_tf100_rr_owner_cut_is_coherent_during_concurrent_publication(tastefit_server):
    s = configure_exact(prepare(tastefit_server))
    with sessions(s, prior=True) as cuts:
        from app.modules.preferences.reference_priors import capture_reference_prior_sources

        before = capture_reference_prior_sources(
            cuts["prior"],
            dict(provider_id=s["prior_provider"].id, requested_targets=(s["selected_target"],)),
        )
        publish_prior(s)
        # An established read-only RR reader either retains the exact old cut or
        # protected lock protocol rejects the transaction. No splicing is accepted.
        try:
            source = capture_candidate_member_tastefit_sources(
                cuts, s["request"], actor_user_id=s["actor"]
            )
        except ResolutionError as exc:
            assert exc.code == "SOURCE_CAPTURE_FAILED"
        else:
            entry = next(e for e in source.member_sources.entries if e.exact_target)
            assert entry.exact_target.reference_source.frontier == before.frontier
    fresh = capture(s, prior=True)
    assert row(derive(fresh)).member_views.exact_target.effective.mode == "PRIOR_ONLY_COLD_START"


@pytest.mark.parametrize(
    "isolation,readonly", [("READ COMMITTED", True), ("REPEATABLE READ", False)]
)
def test_tf101_invalid_capture_transaction_rejected_without_commit(
    tastefit_server, isolation, readonly
):
    s = prepare(tastefit_server)
    fails(lambda: capture(s, isolation=isolation, readonly=readonly), "SOURCE_CAPTURE_FAILED")


def test_tf101_dirty_session_rejected_and_wrong_database_is_not_spliced(tastefit_server):
    s = configure_exact(prepare(tastefit_server))
    with sessions(s, prior=True) as cuts:
        cuts["member"].add(User(display_name="Unflushed test write"))
        fails(
            lambda: capture_candidate_member_tastefit_sources(
                cuts, s["request"], actor_user_id=s["actor"]
            ),
            "SOURCE_CAPTURE_FAILED",
        )
        assert cuts["member"].new


def test_tf101_real_wrong_database_identity_aborts_before_owner_capture(tastefit_server):
    from app.persistence.database import create_database_engine

    s = configure_exact(prepare(tastefit_server))
    maintenance = create_database_engine(
        s["parsed"].render_as_string(hide_password=False)
    ).execution_options(isolation_level="AUTOCOMMIT")
    name = "tastefit_wrong_" + uuid4().hex
    engine = None
    try:
        with maintenance.connect() as db:
            db.execute(text('CREATE DATABASE "' + name + '"'))
        engine = create_database_engine(
            s["parsed"].set(database=name).render_as_string(hide_password=False)
        )
        with (
            sessions(s) as cuts,
            Session(
                engine.execution_options(
                    isolation_level="REPEATABLE READ", postgresql_readonly=True
                )
            ) as other,
        ):
            cuts["prior"] = other
            fails(
                lambda: capture_candidate_member_tastefit_sources(
                    cuts, s["request"], actor_user_id=s["actor"]
                ),
                "SOURCE_CAPTURE_FAILED",
            )
    finally:
        if engine:
            engine.dispose()
        with maintenance.connect() as db:
            db.execute(text('DROP DATABASE "' + name + '" WITH (FORCE)'))
        maintenance.dispose()


def test_tf129_tf132_read_only_no_rows_frontiers_schema_or_production_defaults(tastefit_server):
    s = configure_hierarchy(prepare(tastefit_server))
    engine = s["engines"]["root"]

    def inventory():
        with engine.connect() as conn:
            tables = inspect(conn).get_table_names()
            assert len(tables) == 99
            return {t: conn.scalar(text('SELECT count(*) FROM "' + t + '"')) for t in tables}

    before = inventory()
    statements = []

    def observe(conn, cursor, sql, *args):
        statements.append(sql)

    event.listen(engine, "before_cursor_execute", observe)
    try:
        source = capture(s, prior=True, hierarchy=True)
    finally:
        event.remove(engine, "before_cursor_execute", observe)
    assert before == inventory()
    assert all(sql.lstrip().split()[0].upper() in {"SHOW", "SELECT"} for sql in statements)
    assert not any("tastefit" in t.lower() for t in before)
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0016"
    assert validate(derive(source)).sources == source
