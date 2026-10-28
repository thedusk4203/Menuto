"""TF public-interface acceptance: replay conditional policy, never production defaults."""

import builtins
import json
import os
import socket
import time
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical_bytes
from app.domain.resolution import ResolutionError
from app.modules.planning import tastefit_contracts as c
from app.modules.planning.tastefit_public import (
    derive_candidate_member_tastefit as derive,
)
from app.modules.planning.tastefit_public import (
    validate_candidate_member_tastefit as validate,
)
from app.modules.preferences.tastefit_contracts import tastefit_hash
from candidate_feature_fixtures import (
    advance_catalog,
    alternate_grounding,
    make_subject,
    replace_review,
)
from tastefit_fixtures import (
    fit_policy,
    make_sources,
    seal,
    wire,
    with_member_modes,
    with_policy,
)


def bad(value, operation=derive, code=None):
    with pytest.raises(ResolutionError) as exc:
        operation(value)
    if code:
        assert exc.value.code == code, exc.value.detail
    return exc.value


def result_row(result, kind="PROTEIN"):
    return next(r for r in result.targets if r.proof.target.kind == kind)


def seal_wire(body, *, result=False):
    body["fingerprint"] = tastefit_hash(
        "candidate-member.tastefit-result.v1" if result else "candidate-member.tastefit-sources.v1",
        {k: v for k, v in body.items() if k != "fingerprint"},
    )
    return body


@pytest.fixture(scope="module")
def raw_source():
    return make_sources()


@pytest.fixture(scope="module")
def inherited_source():
    return with_member_modes(
        make_sources(state="UNDECLARED"),
        hierarchy=True,
        undeclared="ONE_HOP_INHERITED",
        external_parent=True,
    )


@pytest.fixture(scope="module")
def blended_source():
    return with_member_modes(make_sources())


def test_tf07_projection_fingerprint_tamper_rehashed_outer_rejects(raw_source):
    data = wire(derive(raw_source))
    data["sources"]["projection"]["fingerprint"] = "f" * 64
    bad(seal_wire(data, result=True), validate)


def test_tf08_other_recipe_version_cannot_reuse_subject(raw_source):
    other = make_sources()
    data = wire(derive(raw_source))
    data["subject"]["binding"]["recipe_version_id"] = (
        str(other.subject_id)
        if hasattr(other, "subject_id")
        else str(other.projection.binding.recipe_version_id)
    )
    bad(seal_wire(data, result=True), validate)


def test_tf09_other_authored_path_cannot_reuse_old_projection(raw_source):
    q, sources = alternate_grounding(raw_source.projection.source)
    from app.modules.planning.grounding import resolve_captured_candidate

    other = resolve_captured_candidate(q, sources).candidate
    data = wire(raw_source)
    data["projection"]["source"]["grounded_candidate"] = wire(other)
    bad(seal_wire(data))


@pytest.mark.parametrize("field", ["title", "latest_recipe_version", "alias", "current_candidate"])
def test_tf10_noncanonical_subject_selectors_reject(raw_source, field):
    data = wire(raw_source)
    data["request"][field] = "not-authority"
    bad(seal_wire(data))


def test_tf13_direct_recipe_exact_identity_retains_outer_version(raw_source):
    r = derive(raw_source)
    row = result_row(r, "DIRECT_RECIPE")
    assert row.proof.target.recipe_id == r.subject.binding.recipe_id
    assert row.value.coordinate.grounding_fingerprint == r.subject.grounding_fingerprint
    assert r.subject.binding.recipe_version_id == raw_source.projection.binding.recipe_version_id


def test_tf16_method_child_path_none_outer_path_retained():
    r = derive(make_sources(dimensions=("METHOD",)))
    assert r.sources.projection.source.feature_input.path is None
    assert r.subject.binding.path is not None
    assert result_row(r, "METHOD").status == "AVAILABLE"


def test_tf18_proven_but_disabled_kind_has_no_fit(raw_source):
    plan = raw_source.request.member_interpretation
    r = derive(with_policy(raw_source, fit_policy(plan, kinds=("METHOD",))))
    row = result_row(r, "PROTEIN")
    assert row.proof.candidate_state == "PRESENT" and row.policy_admission == "NOT_ADMITTED"
    assert row.value is None and row.reason == "POLICY_TARGET_NOT_ADMITTED"


@pytest.mark.parametrize("kind", ["MAIN_PROTEIN", "ROLE", "FAMILY", "OTHER"])
def test_tf19_no_sixth_preference_kind(raw_source, kind):
    data = wire(raw_source)
    data["request"]["diagnostic_targets"] = [dict(kind=kind, feature_term_id=str(uuid4()))]
    bad(data, code="TARGET_KIND_UNSUPPORTED")


@pytest.mark.parametrize(
    "change,reason",
    [
        (lambda s: s, "NO_SOURCE"),
        (replace_review, "RETRACTED"),
        (advance_catalog, "STALE_ASSOCIATION"),
    ],
)
def test_tf21_exact_unresolved_feature_reason_preserved(change, reason):
    source = (
        make_subject(empty=True)
        if reason == "NO_SOURCE"
        else make_subject(("METHOD",) if reason == "RETRACTED" else ("MAIN_PROTEIN",))
    )
    if reason == "RETRACTED":
        source = change(source, retract=True)
    elif reason == "STALE_ASSOCIATION":
        source = change(source)
    r = derive(make_sources(projection_source=source))
    assert reason in {d.reason for d in r.dimensions}
    assert not any(row.proof.target.kind in {"METHOD", "PROTEIN", "FLAVOR"} for row in r.targets)


def test_tf22_reviewed_none_is_finite_not_blanket_absence():
    s = make_subject(("METHOD",), positives=False)
    term = s.feature_input.sources.terms[0]
    from app.modules.preferences.contracts import FeaturePreferenceTarget

    target = FeaturePreferenceTarget(kind="METHOD", feature_term_id=term.id)
    r = derive(make_sources(projection_source=s, probes=(target,)))
    row = result_row(r, "METHOD")
    assert r.dimensions[0].state == "REVIEWED_NONE"
    assert row.proof.candidate_state == "ABSENT" and row.value is None
    assert row.proof.term_resolution.state == "REVIEWED_ABSENT"


@pytest.mark.parametrize(
    "field", ["infer_from_title", "ingredient_family", "nearest_term", "dominant_mass"]
)
def test_tf23_inferred_membership_flags_reject(raw_source, field):
    data = wire(raw_source)
    data["request"][field] = True
    bad(data)


def test_tf24_partial_positive_and_unknown_probe_remain_separate():
    s = make_subject(("METHOD",), coverage="PARTIAL")
    from app.modules.preferences.contracts import FeaturePreferenceTarget

    positive = set(s.feature_input.sources.scopes[0].reviews[-1].command.positive_term_ids)
    probe = FeaturePreferenceTarget(
        kind="METHOD",
        feature_term_id=next(t.id for t in s.feature_input.sources.terms if t.id not in positive),
    )
    r = derive(make_sources(projection_source=s, probes=(probe,)))
    assert r.dimensions[0].coverage == "PARTIAL"
    rows = [r for r in r.targets if r.proof.target.kind == "METHOD"]
    assert {r.proof.candidate_state for r in rows} == {"PRESENT", "UNRESOLVED"}
    assert next(r for r in rows if r.proof.candidate_state == "UNRESOLVED").proof.reason == (
        "PARTIAL_COVERAGE"
    )


def test_tf25_uncaptured_dimension_is_not_zero():
    from preference_fixtures import term
    from target_affinity_fixtures import entry

    t = term("FLAVOR")
    from app.modules.preferences.contracts import FeaturePreferenceTarget

    probe = FeaturePreferenceTarget(kind="FLAVOR", feature_term_id=t.id)
    r = derive(
        make_sources(
            dimensions=("METHOD",), probes=(probe,), extra_identities=(entry(probe, identity=t),)
        )
    )
    row = result_row(r, "FLAVOR")
    assert row.proof.reason == "DIMENSION_NOT_CAPTURED" and row.value is None
    assert ("FLAVOR", "DIMENSION_NOT_CAPTURED") in r.dimension_diagnostics


def test_tf26_duplicate_ingredient_target_has_all_requirement_proofs():
    from app.modules.planning.grounding import resolve_captured_candidate
    from app.modules.recipes.contracts import VariantGenerationRequest
    from app.modules.recipes.public import generate_variants
    from candidate_feature_fixtures import seal_ground, seal_source
    from grounding_fixtures import setup

    q, owner, _ = setup()
    recipe = owner.recipe
    first = recipe.ingredients[0]
    second = first.model_copy(update=dict(id=uuid4(), slot="synthetic-second-slot"))
    recipe = recipe.model_copy(
        update=dict(
            ingredients=(first, second),
            variant_rules=(),
            transformations=(),
            portion_tiers=tuple(
                t.model_copy(
                    update=dict(
                        quantities=t.quantities
                        + (t.quantities[0].model_copy(update=dict(requirement_id=second.id)),)
                    )
                )
                for t in recipe.portion_tiers
            ),
        )
    )
    candidate = generate_variants(
        VariantGenerationRequest(
            recipe=recipe, demand={}, limits=dict(max_attempts=1, max_candidates=1)
        )
    ).candidates[0]
    q = q.model_copy(update=dict(candidate=candidate))
    owner = owner.model_copy(update=dict(recipe=recipe))
    ground = resolve_captured_candidate(q, owner)
    assert ground.status == "GROUNDED"
    source = make_subject(("METHOD",), empty=True, grounding=(q, owner))
    source = seal_source(
        source.model_copy(update=dict(grounded_candidate=seal_ground(ground.candidate)))
    )
    result = derive(make_sources(projection_source=source))
    rows = [r for r in result.targets if r.proof.target.kind == "INGREDIENT"]
    assert len(rows) == 1 and len(rows[0].proof.requirement_ids) == 2


def test_tf27_probe_neither_trims_base_nor_expands_feature_cut():
    from app.modules.preferences.contracts import FeaturePreferenceTarget
    from preference_fixtures import term
    from target_affinity_fixtures import entry

    t = term("METHOD")
    probe = FeaturePreferenceTarget(kind="METHOD", feature_term_id=t.id)
    s = make_sources(probes=(probe,), extra_identities=(entry(probe, identity=t),))
    result = derive(s)
    row = next(r for r in result.targets if r.proof.target == probe)
    assert row.proof.reason == "TERM_NOT_CAPTURED" and row.proof.role == "DIAGNOSTIC_ONLY"
    assert row.direct_signal == "DECLARED_LIKE" and row.value is None
    assert len(result.targets) == 6
    assert t.id not in {t.id for t in s.projection.source.feature_input.sources.terms}


def test_tf30_dislike_is_negative_soft_signal_not_safety():
    result = derive(make_sources(value="DISLIKE"))
    assert all(
        r.direct_signal == "DECLARED_DISLIKE" and r.value.amount.numerator < 0
        for r in result.targets
    )
    assert not result.planner_ready and not hasattr(result, "is_safe")


def test_tf31_nonzero_raw_neutral_requires_explicit_mapping():
    from target_affinity_fixtures import policy

    body = policy().model_dump()
    for g in body["target_policies"]:
        next(r for r in g["affinity_rules"] if r["value"] == "NEUTRAL")["amount"].update(
            numerator=1, denominator=5
        )
    p = type(policy()).model_validate(body)
    result = derive(make_sources(value="NEUTRAL", explicit_policy=p))
    assert all(
        r.source_amount.numerator == 1
        and r.value.amount.numerator == 0
        and r.semantic_state == "NEUTRAL"
        for r in result.targets
    )


def test_tf32_undeclared_is_unavailable_not_neutral():
    result = derive(make_sources(state="UNDECLARED"))
    assert all(
        r.value is None and r.reason == "MEMBER_UNDECLARED" and r.evidence_strength.level == "NONE"
        for r in result.targets
    )


def test_tf33_retraction_suppresses_retained_previous_like():
    result = derive(make_sources(state="RETRACTED"))
    assert all(
        r.status == "SUPPRESSED" and r.reason == "MEMBER_RETRACTED" and r.value is None
        for r in result.targets
    )


def test_tf33_tf59_policy_cannot_override_retraction_even_for_disabled_kind():
    source = make_sources(state="RETRACTED")
    result = derive(
        with_policy(source, fit_policy(source.request.member_interpretation, kinds=("METHOD",)))
    )
    assert all(
        r.status == "SUPPRESSED" and r.reason == "MEMBER_RETRACTED" and r.value is None
        for r in result.targets
    )
    assert any(r.policy_admission == "NOT_ADMITTED" for r in result.targets)
    assert all(
        len(e.explicit.source.preferences.declarations) == 10
        for e in result.sources.member_sources.entries
    )


def test_tf34_available_like_zero_is_not_missing():
    from target_affinity_fixtures import policy

    body = policy().model_dump()
    for g in body["target_policies"]:
        for r in g["affinity_rules"]:
            r["amount"].update(
                numerator={"DISLIKE": -2, "NEUTRAL": -1, "LIKE": 0}[r["value"]], denominator=3
            )
    result = derive(make_sources(explicit_policy=type(policy()).model_validate(body)))
    assert all(
        r.source_amount.numerator == 0 and r.status == "AVAILABLE" and r.value.amount.numerator > 0
        for r in result.targets
    )


@pytest.mark.parametrize("strength", ["LOW", "MEDIUM", "HIGH"], ids=["TF35", "TF36", "TF37"])
def test_tf35_tf36_tf37_strength_is_lineage_not_another_multiplier(strength):
    result = derive(make_sources(strength=strength))
    assert all(
        r.evidence_strength.level == strength
        and r.value.amount == c.TasteFitAmount(numerator=1, denominator=2)
        for r in result.targets
    )


def test_tf38_prior_and_inherited_never_mint_destination_strength(inherited_source):
    row = result_row(derive(inherited_source))
    assert row.status == "AVAILABLE" and row.evidence_strength.level == "NONE"
    assert row.member_views.one_hop.evidence_strength == "NOT_DERIVED"
    assert row.member_views.one_hop.parent_exact_target.explicit_profile.rows[
        0
    ].evidence_strength.level == ("LOW")


@pytest.mark.parametrize(
    "field", ["evidence_strength", "confidence", "sample_count", "strength_multiplier"]
)
def test_tf39_caller_strength_fields_reject(raw_source, field):
    data = wire(raw_source)
    data["request"]["policy"][field] = 1
    bad(data)


def test_tf42_dislike_without_mapping_keeps_soft_signal():
    source = make_sources(value="DISLIKE")
    body = source.request.policy.model_dump()
    for g in body["kind_policies"]:
        g["mappings"] = [r for r in g["mappings"] if r["semantic_state"] != "DISLIKE"]
    result = derive(with_policy(source, c.TasteFitInterpretationPolicy.model_validate(body)))
    assert all(r.direct_signal == "DECLARED_DISLIKE" and r.value is None for r in result.targets)
    assert not hasattr(result, "excluded")


def test_tf43_negative_prior_is_not_direct_dislike():
    source = with_member_modes(make_sources(state="UNDECLARED"), prior_amount=(-1, 1))
    row = result_row(derive(source))
    assert row.value.amount.numerator < 0 and row.direct_signal == "NONE"
    assert row.semantic_state == "NO_DECLARATION"


@pytest.mark.parametrize("semantic", ["LIKE", "DISLIKE", "NEUTRAL"])
def test_tf43_inherited_semantic_preserved_without_direct_signal_or_strength(semantic):
    source = with_member_modes(
        make_sources(state="UNDECLARED"),
        hierarchy=True,
        undeclared="ONE_HOP_INHERITED",
        parent_value=semantic,
    )
    row = result_row(derive(source))
    assert row.semantic_state == semantic and row.direct_signal == "NONE"
    assert row.evidence_strength.level == "NONE"
    assert row.value.amount.numerator == {"LIKE": 1, "DISLIKE": -1, "NEUTRAL": 0}[semantic]


def test_tf44_other_participants_never_become_fit_subjects(raw_source):
    result = derive(raw_source)
    assert all(r.value.coordinate.member_id == result.subject.member_id for r in result.targets)
    assert not hasattr(result, "member_totals")
    assert result.shared_member_aggregation == "NOT_PERFORMED"


def test_tf46_frozen_blend_mapped_once(blended_source):
    row = result_row(derive(blended_source))
    assert row.member_views.exact_target.effective.mode == "BLENDED_EXPLICIT_AND_PRIOR"
    assert (
        row.source_amount.model_dump()
        == row.member_views.exact_target.effective.value.amount.model_dump()
    )
    assert row.value.amount == row.mapping.fit_amount
    assert row.value.amount == c.TasteFitAmount(numerator=1, denominator=2)


def test_tf47_prior_only_cold_start_not_neutral():
    row = result_row(derive(with_member_modes(make_sources(state="UNDECLARED"))))
    assert row.member_views.exact_target.effective.mode == "PRIOR_ONLY_COLD_START"
    assert row.semantic_state == "NO_DECLARATION" and row.evidence_strength.level == "NONE"


def test_tf50_unmapped_reference_keeps_frozen_explicit_fallback():
    row = result_row(derive(with_member_modes(make_sources(), prior_amount=(1, 3))))
    assert row.member_views.exact_target.mapped_prior.reason == "PRIOR_VALUE_NOT_MAPPED"
    assert row.member_views.exact_target.effective.mode == "EXPLICIT_ONLY"


@pytest.mark.parametrize(
    "field",
    [
        "expected_explicit_policy_fingerprint",
        "expected_compatibility_policy_fingerprint",
        "expected_shrinkage_policy_fingerprint",
    ],
)
def test_tf51_policy_bindings_fail_before_lookup(blended_source, field):
    data = wire(blended_source)
    data["request"]["member_interpretation"][field] = "f" * 64
    bad(data)


@pytest.mark.parametrize("field", ["provider_id", "provider_command_hash"])
def test_tf52_reference_provider_binding_never_falls_back(blended_source, field):
    data = wire(blended_source)
    child = next(e["exact_target"] for e in data["member_sources"]["entries"] if e["exact_target"])
    child["compatibility_policy"][field] = str(uuid4()) if field == "provider_id" else "f" * 64
    bad(seal_wire(data))


def test_tf54_effective_without_fit_mapping_does_not_use_raw(blended_source):
    body = blended_source.request.policy.model_dump()
    body["kind_policies"][0]["mappings"] = []
    row = result_row(
        derive(with_policy(blended_source, c.TasteFitInterpretationPolicy.model_validate(body)))
    )
    assert row.selected_mode == "EXACT_TARGET_EFFECTIVE" and row.value is None
    assert row.reason == "SOURCE_COORDINATE_NOT_ADMITTED"


def test_tf56_only_shrinkage_provenance_changes_full_identity(blended_source):
    from app.modules.preferences.tastefit_contracts import TasteFitMemberInterpretationPlan

    # All equal weights: change only policy labels while preserving effective value.
    source = blended_source
    old = source.request.member_interpretation
    sh = old.shrinkage_policy.model_copy(update=dict(policy_version="2"))
    plan = TasteFitMemberInterpretationPlan.model_validate(
        old.model_dump()
        | dict(shrinkage_policy=sh, expected_shrinkage_policy_fingerprint=sh.fingerprint())
    )
    q = source.request.model_copy(update=dict(member_interpretation=plan))
    cp = source.member_sources.plan.model_copy(update=dict(interpretation=plan))
    entries = [
        e.model_copy(
            update=dict(exact_target=e.exact_target.model_copy(update=dict(shrinkage_policy=sh)))
        )
        if e.exact_target
        else e
        for e in source.member_sources.entries
    ]
    other = seal(
        source.model_copy(
            update=dict(
                request=q,
                member_sources=source.member_sources.model_copy(
                    update=dict(plan=cp, entries=tuple(entries))
                ),
            )
        )
    )
    a, b = result_row(derive(source)), result_row(derive(other))
    assert (
        a.value == b.value
        and a.member_views.exact_target.coordinate == b.member_views.exact_target.coordinate
    )
    assert derive(source).fingerprint != derive(other).fingerprint


@pytest.mark.parametrize("value", ["LIKE", "DISLIKE", "NEUTRAL"])
def test_tf58_destination_direct_wins_without_magnitude_comparison(value):
    row = result_row(
        derive(
            with_member_modes(
                make_sources(value=value),
                hierarchy=True,
                declared="RAW_EXPLICIT",
                undeclared="ONE_HOP_INHERITED",
            )
        )
    )
    assert row.selected_mode == "RAW_EXPLICIT" and row.direct_signal == "DECLARED_" + value
    assert row.member_views.one_hop.inherited.reason == "DESTINATION_DIRECT_DECLARATION"


def test_tf59_retracted_destination_wins_even_prior_and_parent():
    row = result_row(
        derive(
            with_member_modes(
                make_sources(state="RETRACTED"), hierarchy=True, undeclared="ONE_HOP_INHERITED"
            )
        )
    )
    assert row.status == "SUPPRESSED" and row.value is None
    assert row.member_views.one_hop.inherited.reason == "MEMBER_RETRACTED"


def test_tf61_parent_prior_only_is_not_inherited_and_blend_is_not_operand(inherited_source):
    row = result_row(derive(inherited_source))
    parent = row.member_views.one_hop.parent_exact_target
    assert row.member_views.one_hop.inherited.trace.mapped_explicit == parent.mapped_explicit.value
    assert (
        parent.mapped_explicit.value != parent.effective.value
        or parent.effective.mode == "EXPLICIT_ONLY"
    )
    source = with_member_modes(
        make_sources(state="UNDECLARED"),
        hierarchy=True,
        undeclared="ONE_HOP_INHERITED",
        parent_state="UNDECLARED",
        prior_on_parent=True,
    )
    unavailable = result_row(derive(source))
    assert unavailable.value is None and unavailable.source_reason == "PARENT_PRIOR_ONLY_COLD_START"


def test_tf64_recursive_parent_result_cannot_enter_primitives(inherited_source):
    data = wire(inherited_source)
    child = next(e["one_hop"] for e in data["member_sources"]["entries"] if e["one_hop"])
    child["parent"] = wire(result_row(derive(inherited_source)).member_views.one_hop)
    bad(seal_wire(data))


def test_tf65_wrong_parent_target_rejects_even_matching_kind(inherited_source):
    data = wire(inherited_source)
    child = next(e["one_hop"] for e in data["member_sources"]["entries"] if e["one_hop"])
    child["parent"]["explicit"]["source"]["request"]["requested_targets"][0]["ingredient_id"] = str(
        uuid4()
    )
    bad(seal_wire(data))


def test_tf67_different_source_recipe_is_valid_lineage():
    parent = make_subject().grounded_candidate.sources.recipe
    source = with_member_modes(
        make_sources(state="UNDECLARED"),
        kind="DIRECT_RECIPE",
        hierarchy=True,
        parent_recipe=parent,
        undeclared="ONE_HOP_INHERITED",
    )
    result = derive(source)
    r = result_row(result, "DIRECT_RECIPE")
    assert (
        r.status == "AVAILABLE"
        and r.member_views.one_hop.parent_target.recipe_id == parent.recipe.id
    )
    assert r.member_views.one_hop.parent_target != r.proof.target
    assert len(result.targets) == 5
    assert len(source.member_sources.entries) == 6


def test_tf68_prior_selected_inherited_not_selected():
    source = with_member_modes(
        make_sources(state="UNDECLARED"), hierarchy=True, undeclared="PRIOR_ONLY"
    )
    row = result_row(derive(source))
    assert (
        row.selected_mode == "PRIOR_ONLY"
        and row.member_views.one_hop.inherited.status == "AVAILABLE"
    )
    assert ("ONE_HOP_INHERITED", "NOT_SELECTED") in row.view_dispositions


def test_tf69_inherited_selected_even_when_prior_larger(inherited_source):
    row = result_row(derive(inherited_source))
    assert row.selected_mode == "ONE_HOP_INHERITED" and row.value is not None
    assert ("PRIOR_ONLY", "NOT_SELECTED") in row.view_dispositions


def test_tf70_unused_malformed_hierarchy_child_still_rejects():
    source = with_member_modes(
        make_sources(), hierarchy=True, declared="RAW_EXPLICIT", undeclared="ONE_HOP_INHERITED"
    )
    data = wire(source)
    child = next(e["one_hop"] for e in data["member_sources"]["entries"] if e["one_hop"])
    child["parent"]["shrinkage_policy"]["rules"] = []
    bad(seal_wire(data))


def test_tf71_exact_policy_pins_and_replay_determinism(raw_source):
    a, b = derive(raw_source), derive(wire(raw_source))
    assert a == b and a.fingerprint == b.fingerprint
    assert all(
        r.value.coordinate.policy_fingerprint == raw_source.request.expected_policy_fingerprint
        for r in a.targets
    )


def test_tf72_body_edit_without_independent_pin_rejects(raw_source):
    data = wire(derive(raw_source))
    data["sources"]["request"]["policy"]["max_targets"] += 1
    bad(seal_wire(data, result=True), validate, code="POLICY_FINGERPRINT_MISMATCH")


def test_tf73_missing_policy_never_selects_default(raw_source):
    data = wire(raw_source)
    data["request"].pop("policy")
    bad(data, code="POLICY_MISSING")


@pytest.mark.parametrize(
    "field,value",
    [
        ("contract_version", "candidate-member-tastefit-policy.v2"),
        ("policy_id", "other"),
        ("policy_version", "999"),
    ],
)
def test_tf74_exact_version_only(raw_source, field, value):
    data = wire(raw_source)
    data["request"]["policy"][field] = value
    bad(data, code="POLICY_VERSION_MISMATCH")


@pytest.mark.parametrize("duplicate", ["row", "kind"])
def test_tf75_duplicate_semantic_keys_reject(raw_source, duplicate):
    data = wire(raw_source)
    groups = data["request"]["policy"]["kind_policies"]
    if duplicate == "row":
        groups[0]["mappings"].append(groups[0]["mappings"][0])
    else:
        groups.append(groups[0])
    bad(data)


def test_tf76_equal_value_under_unmapped_descriptor_is_not_selected(raw_source):
    body = raw_source.request.policy.model_dump()
    for group in body["kind_policies"]:
        for row in group["mappings"]:
            row["source_coordinate"]["explicit_policy_fingerprint"] = "f" * 64
    result = derive(with_policy(raw_source, c.TasteFitInterpretationPolicy.model_validate(body)))
    assert all(
        r.reason == "SOURCE_COORDINATE_NOT_ADMITTED" and r.value is None for r in result.targets
    )


def test_tf77_mapping_for_another_kind_never_transfers(raw_source):
    body = raw_source.request.policy.model_dump()
    body["kind_policies"][-1]["mappings"] = []
    result = derive(with_policy(raw_source, c.TasteFitInterpretationPolicy.model_validate(body)))
    protein = result_row(result)
    assert protein.value is None and result_row(result, "METHOD").value is not None


@pytest.mark.parametrize("change", ["missing_group", "bad_mode", "missing_choice"])
def test_tf78_admission_and_capture_selections_are_required(raw_source, change):
    data = wire(raw_source)
    groups = data["request"]["policy"]["kind_policies"]
    if change == "missing_group":
        groups.pop()
    elif change == "bad_mode":
        groups[0]["undeclared_selection"] = "ONE_HOP_INHERITED"
    else:
        groups[0].pop("declared_selection")
    bad(data)


def test_tf79_reviewed_label_is_still_conditional_input(raw_source):
    body = raw_source.request.policy.model_dump()
    body["provenance"]["kind"] = "REVIEWED_REFERENCE"
    result = derive(with_policy(raw_source, c.TasteFitInterpretationPolicy.model_validate(body)))
    assert result.policy_authority == "EXPLICIT_INTERPRETATION_INPUT_ONLY"
    assert not result.planner_ready and not hasattr(result, "published_policy")


def test_tf80_complete_frozen_descriptors_retained(raw_source, blended_source, inherited_source):
    raw = result_row(derive(raw_source))
    profile = result_row(derive(blended_source))
    inherited = result_row(derive(inherited_source))
    assert (
        raw.source_coordinate.explicit_policy_fingerprint
        == raw_source.request.member_interpretation.expected_explicit_policy_fingerprint
    )
    assert (
        profile.source_coordinate.coordinate
        == profile.member_views.exact_target.effective.value.coordinate
    )
    assert (
        inherited.source_coordinate.coordinate
        == inherited.member_views.one_hop.inherited.value.coordinate
    )


def test_tf81_no_declaration_neutral_and_zero_have_separate_keys(raw_source):
    mapping = raw_source.request.policy.kind_policies[0].mappings[0]
    body = mapping.model_dump()
    body["semantic_state"] = "NO_DECLARATION"
    with pytest.raises(ValueError):
        c.TasteFitMappingRow.model_validate(body)
    neutral = derive(make_sources(value="NEUTRAL"))
    assert all(
        r.semantic_state == "NEUTRAL" and r.value.amount.numerator == 0 for r in neutral.targets
    )


def test_tf82_exact_rational_miss_no_nearest_interpolation(raw_source):
    body = raw_source.request.policy.model_dump()
    for group in body["kind_policies"]:
        for row in group["mappings"]:
            if row["semantic_state"] == "LIKE":
                row["source_amount"].update(numerator=1, denominator=2)
    result = derive(with_policy(raw_source, c.TasteFitInterpretationPolicy.model_validate(body)))
    assert all(r.reason == "SOURCE_VALUE_NOT_MAPPED" and r.value is None for r in result.targets)


def test_tf83_sets_and_equivalent_rationals_normalize_policy_identity(raw_source):
    old = raw_source.request.policy
    body = old.model_dump()
    body["admitted_kinds"] = list(reversed(body["admitted_kinds"]))
    body["kind_policies"] = list(reversed(body["kind_policies"]))
    for group in body["kind_policies"]:
        group["mappings"] = list(reversed(group["mappings"]))
        for row in group["mappings"]:
            for amount in (row["source_amount"], row["fit_amount"]):
                amount["numerator"] *= 7
                amount["denominator"] *= 7
    new = c.TasteFitInterpretationPolicy.model_validate(body)
    assert new == old and new.fingerprint() == old.fingerprint()


@pytest.mark.parametrize(
    "field",
    ["max_targets", "max_policy_bytes", "max_source_bytes", "operator", "evidence_strength_effect"],
)
def test_tf84_semantic_choices_and_limits_cannot_be_omitted(raw_source, field):
    body = raw_source.request.policy.model_dump()
    body.pop(field)
    with pytest.raises(ValueError):
        c.TasteFitInterpretationPolicy.model_validate(body)


def test_tf85_new_coherent_body_is_another_conditional_request(raw_source):
    old = derive(raw_source)
    body = raw_source.request.policy.model_dump()
    body["max_targets"] += 1
    new = derive(with_policy(raw_source, c.TasteFitInterpretationPolicy.model_validate(body)))
    assert old.sources.request.policy.policy_version == new.sources.request.policy.policy_version
    assert old.fingerprint != new.fingerprint
    assert old.targets[0].value.coordinate != new.targets[0].value.coordinate
    assert new.policy_authority == "EXPLICIT_INTERPRETATION_INPUT_ONLY"


@pytest.mark.parametrize("field", ["max_targets", "max_policy_bytes", "max_source_bytes"])
def test_tf86_authored_resource_overflow_rejects_without_partial_result(raw_source, field):
    policy = c.TasteFitInterpretationPolicy.model_validate(
        raw_source.request.policy.model_dump() | {field: 1}
    )
    bad(with_policy(raw_source, policy), code="RESOURCE_LIMIT")
    if field == "max_targets":
        data = wire(with_policy(raw_source, policy))
        data["member_sources"]["entries"][0]["explicit"] = "malformed untrusted child"
        # An already visible target overflow is rejected before parsing/replaying children.
        bad(data, code="RESOURCE_LIMIT")


@pytest.mark.parametrize(
    "field",
    [
        "member_id",
        "household_id",
        "projection_fingerprint",
        "grounding_fingerprint",
        "target",
        "policy_fingerprint",
    ],
)
def test_tf87_scoped_numeric_equality_requires_entire_descriptor(raw_source, field):
    value = derive(raw_source).targets[0].value
    coordinate = value.coordinate.model_dump()
    if field == "target":
        coordinate[field] = dict(kind="INGREDIENT", ingredient_id=uuid4())
    else:
        coordinate[field] = uuid4() if field.endswith("_id") else "f" * 64
    other = c.ScopedTargetTasteFit(coordinate=coordinate, amount=value.amount)
    with pytest.raises(ValueError, match="descriptor mismatch"):
        value.scoped_numeric_equal(other)
    assert value.scoped_numeric_equal(value.model_dump())


@pytest.mark.parametrize("change", ["kind", "family", "naked"])
def test_tf88_descriptor_semantics_reject_before_lookup(raw_source, change):
    data = wire(raw_source)
    row = data["request"]["policy"]["kind_policies"][0]["mappings"][0]
    if change == "kind":
        row["source_coordinate"]["target_kind"] = "METHOD"
    elif change == "family":
        row["source_coordinate"]["family"] = "INHERITED"
    else:
        row.pop("source_coordinate")
    bad(data)


def test_tf90_wrong_member_parent_rejects(inherited_source):
    data = wire(inherited_source)
    child = next(e["one_hop"] for e in data["member_sources"]["entries"] if e["one_hop"])
    child["parent"]["explicit"]["source"]["request"]["member_id"] = str(uuid4())
    bad(seal_wire(data))


def test_tf91_wrong_household_even_with_matching_numeric_value(raw_source):
    data = wire(raw_source)
    data["member_sources"]["entries"][0]["explicit"]["source"]["manifest"]["household_id"] = str(
        uuid4()
    )
    bad(seal_wire(data))


@pytest.mark.parametrize("location", ["manifest", "feature_source", "recipe"])
def test_tf94_typed_immutable_fact_conflicts_any_depth_reject(raw_source, location):
    data = wire(raw_source)
    if location == "manifest":
        e = next(e for e in data["member_sources"]["entries"] if e["target"]["kind"] == "PROTEIN")
        e["explicit"]["source"]["manifest"]["entries"][0]["identity"]["definition"] = (
            "forged meaning"
        )
    elif location == "feature_source":
        data["projection"]["source"]["feature_input"]["recipe"]["recipe"]["name"] = (
            "forged immutable"
        )
    else:
        data["member_sources"]["plan"]["candidate_recipe"]["recipe"]["name"] = "forged immutable"
    bad(seal_wire(data))


def test_tf95_mutable_ingredient_label_is_not_identity_conflict(raw_source):
    data = wire(raw_source)
    e = next(e for e in data["member_sources"]["entries"] if e["target"]["kind"] == "INGREDIENT")
    e["explicit"]["source"]["manifest"]["entries"][0]["identity"]["name"] = "Renamed label"
    a, b = derive(raw_source), derive(seal_wire(data))
    assert [r.value for r in a.targets] == [r.value for r in b.targets]
    assert a.fingerprint != b.fingerprint


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_origin", "CANONICAL_DATABASE"),
        ("common_mvcc", "CERTIFIED"),
        ("policy_authority", "PUBLISHED"),
    ],
)
def test_tf98_offline_origin_and_auth_claims_cannot_be_minted(raw_source, field, value):
    data = wire(derive(raw_source))
    data[field] = value
    bad(seal_wire(data, result=True), validate)


def test_tf102_same_frontier_different_ledger_body_is_incoherent(raw_source):
    data = wire(raw_source)
    ledger = data["member_sources"]["entries"][0]["explicit"]["source"]["preferences"]
    # Change audit detail and correctly rehash command, keeping the frontier unchanged.
    from app.modules.preferences.contracts import SetMemberPreferenceCommand

    d = ledger["declarations"][0]
    d["command"]["idempotency_key"] = uuid4().hex
    d["command_fingerprint"] = SetMemberPreferenceCommand.model_validate(d["command"]).fingerprint()
    bad(seal_wire(data), code="SOURCE_CUT_INCOHERENT")


def test_tf103_identical_serialized_sources_have_identical_semantics(raw_source):
    a, b = derive(raw_source), derive(json.loads(json.dumps(wire(raw_source))))
    assert a == b


def test_tf104_new_set_order_normalizes_frozen_journals_stay_owned(raw_source):
    data = wire(raw_source)
    data["member_sources"]["entries"].reverse()
    # A normalized set has one source identity; unordered input cannot choose last-wins.
    from app.modules.planning.tastefit_contracts import CandidateMemberTasteFitSources

    normalized = CandidateMemberTasteFitSources.model_validate(data)
    assert derive(seal(normalized)) == derive(raw_source)
    data["member_sources"]["entries"].append(data["member_sources"]["entries"][0])
    bad(data)


def test_tf105_frame_provenance_changes_identity_without_fit(raw_source):
    data = wire(raw_source)
    actor = str(uuid4())
    data["candidate_frame"]["actor_user_id"] = actor
    data["member_sources"]["frames"][0]["actor_user_id"] = actor
    a, b = derive(raw_source), derive(seal_wire(data))
    assert [r.value for r in a.targets] == [r.value for r in b.targets]
    assert a.fingerprint != b.fingerprint


def test_tf102_tf105_hidden_unrelated_ledger_history_changes_identity_not_fit(raw_source):
    from preference_fixtures import command, declaration

    data = wire(raw_source)
    ledger = raw_source.member_sources.entries[0].explicit.source.preferences
    cmd = command(
        household_id=ledger.household_id,
        member_id=ledger.member_id,
        actor_user_id=raw_source.candidate_frame.actor_user_id,
    )
    hidden = declaration(cmd, sequence=ledger.frontier + 1)
    for entry in data["member_sources"]["entries"]:
        body = entry["explicit"]["source"]["preferences"]
        body["declarations"].append(wire(hidden))
        body["frontier"] += 1
    a, b = derive(raw_source), derive(seal_wire(data))
    assert [r.value for r in a.targets] == [r.value for r in b.targets]
    assert a.fingerprint != b.fingerprint


@pytest.mark.parametrize("which", ["PROFILE", "INHERITED"])
def test_tf88_forged_frozen_descriptor_never_enters_fit_lookup(
    blended_source, inherited_source, which
):
    source = blended_source if which == "PROFILE" else inherited_source
    data = wire(derive(source))
    target = next(r for r in data["targets"] if r["proof"]["target"]["kind"] == "PROTEIN")
    descriptor = target["source_coordinate"]["coordinate"]
    descriptor[
        "compatibility_policy_fingerprint"
        if which == "PROFILE"
        else "transfer_policy_semantic_fingerprint"
    ] = "f" * 64
    bad(seal_wire(data, result=True), validate)


def test_tf94_coherently_edited_member_term_still_conflicts_with_candidate(raw_source):
    data = wire(raw_source)
    target_id = str(result_row(derive(raw_source)).proof.target.feature_term_id)
    for entry in data["member_sources"]["entries"]:
        source = entry["explicit"]["source"]
        for t in source["preferences"]["feature_terms"]:
            if t["id"] == target_id:
                t["definition"] = "Coherent forged member-only meaning"
        for e in source["manifest"]["entries"]:
            if e["kind"] == "PROTEIN" and e["identity"]["id"] == target_id:
                e["identity"]["definition"] = "Coherent forged member-only meaning"
    bad(seal_wire(data), code="SOURCE_CUT_INCOHERENT")


@pytest.mark.parametrize("n,d", [(True, 2), (1, True), (0, 0), (1, -1), (1.0, 2), ("1", 2), (2, 1)])
def test_tf84_rational_components_strict_signed_unit_not_probability(n, d):
    with pytest.raises(ValueError):
        c.TasteFitAmount(numerator=n, denominator=d)


def test_tf106_rehashed_cached_projection_does_not_override_sources(raw_source):
    data = wire(raw_source)
    data["projection"]["dimensions"][0]["positive_term_ids"] = []
    bad(seal_wire(data))


def test_tf107_cached_explicit_strength_cannot_override_ledger(raw_source):
    data = wire(derive(raw_source))
    data["targets"][0]["member_views"]["explicit"]["evidence_strength"]["level"] = "HIGH"
    bad(seal_wire(data, result=True), validate)


def test_tf108_cached_blend_rehash_rejects(blended_source):
    data = wire(derive(blended_source))
    row = next(r for r in data["targets"] if r["member_views"]["exact_target"])
    row["member_views"]["exact_target"]["effective"]["value"]["amount"]["numerator"] = 0
    bad(seal_wire(data, result=True), validate)


def test_tf109_cached_transfer_arithmetic_rehash_rejects(inherited_source):
    data = wire(derive(inherited_source))
    row = next(r for r in data["targets"] if r["member_views"]["one_hop"])
    row["member_views"]["one_hop"]["inherited"]["trace"]["attenuation"]["numerator"] = 0
    bad(seal_wire(data, result=True), validate)


@pytest.mark.parametrize(
    "field,value",
    [
        ("selected_mode", "NO_EVIDENCE"),
        ("direct_signal", "NONE"),
        ("reason", "fake"),
        ("semantic_state", "NEUTRAL"),
        ("policy_admission", "NOT_ADMITTED"),
        ("source_reason", "fake"),
    ],
)
def test_tf110_all_semantic_output_fields_compared_not_only_hash(raw_source, field, value):
    data = wire(derive(raw_source))
    data["targets"][0][field] = value
    bad(seal_wire(data, result=True), validate)


def test_tf111_model_construct_nested_policy_is_untrusted(raw_source):
    forged = raw_source.request.policy.model_construct(
        **(raw_source.request.policy.model_dump() | dict(operator="SUM"))
    )
    q = raw_source.request.model_construct(
        **(raw_source.request.model_dump() | dict(policy=forged))
    )
    bad(raw_source.model_construct(**(raw_source.model_dump() | dict(request=q))))


def test_tf112_model_copy_bypass_reparsed(raw_source):
    q = raw_source.request.model_copy(update=dict(member_id=uuid4()))
    bad(raw_source.model_copy(update=dict(request=q)))


@pytest.mark.parametrize(
    "field", ["target", "member_id", "policy_fingerprint", "projection_fingerprint"]
)
def test_tf113_scoped_descriptor_forgery_rejects(raw_source, field):
    data = wire(derive(raw_source))
    coord = data["targets"][0]["value"]["coordinate"]
    coord[field] = (
        dict(kind="INGREDIENT", ingredient_id=str(uuid4()))
        if field == "target"
        else (str(uuid4()) if field == "member_id" else "f" * 64)
    )
    bad(seal_wire(data, result=True), validate)


def test_tf114_pure_derivation_validation_zero_io(raw_source, monkeypatch):
    # Construct/import everything before traps; production pure execution gets no
    # filesystem/network/clock/environment escape, including frozen child replay.
    result = derive(raw_source)
    import pathlib

    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session

    def forbidden(*args, **kw):
        raise AssertionError("Unexpected IO or live ambient lookup")

    def framework_environment(name, default=None):
        # Frozen Pydantic probes its own plugin flag when building UUID adapters.
        # It is not TasteFit policy selection; every other environment key traps.
        assert name == "PYDANTIC_DISABLE_PLUGINS", name
        return None

    for obj, name in (
        (builtins, "open"),
        (socket, "socket"),
        (socket, "create_connection"),
        (time, "time"),
        (time, "monotonic"),
        (pathlib.Path, "read_text"),
        (pathlib.Path, "read_bytes"),
        (Engine, "connect"),
        (Session, "execute"),
    ):
        monkeypatch.setattr(obj, name, forbidden)
    monkeypatch.setattr(os, "getenv", framework_environment)
    assert derive(raw_source) == result
    assert validate(result) == result


def test_tf115_hashes_bind_complete_bodies_without_self_recursion(raw_source):
    result = derive(raw_source)
    assert result.fingerprint == result.expected_fingerprint()
    assert raw_source.fingerprint == raw_source.expected_fingerprint()
    assert result.targets[0].mapping.source_amount.denominator > 0
    assert c.TasteFitAmount(numerator=0, denominator=7).denominator == 1
    assert canonical_bytes(result) == canonical_bytes(wire(result))


def test_tf116_validator_returns_new_recomputed_result(raw_source):
    result = derive(raw_source)
    fresh = validate(result)
    assert fresh == result and fresh is not result and fresh.subject is not result.subject


@pytest.mark.parametrize("field", ["learned_events", "signal_router", "contextual_evidence_input"])
def test_tf117_learning_events_are_not_inputs(raw_source, field):
    data = wire(raw_source)
    data["request"][field] = []
    bad(data)


@pytest.mark.parametrize("field", ["cooked", "consumed", "skip", "rejected"])
def test_tf118_behavioral_events_cannot_become_like(raw_source, field):
    data = wire(raw_source)
    data["request"][field] = True
    bad(data)


@pytest.mark.parametrize("reason", ["NO_TIME", "OUT_OF_STOCK", "PRICE", "EQUIPMENT"])
def test_tf119_operational_friction_is_not_taste(raw_source, reason):
    data = wire(raw_source)
    data["request"]["friction"] = reason
    bad(data)


@pytest.mark.parametrize("field", ["passive", "autopilot", "forced_conflict"])
def test_tf120_passive_forced_assumptions_reject(raw_source, field):
    data = wire(raw_source)
    data["request"][field] = True
    bad(data)


@pytest.mark.parametrize("field", ["repeat_penalty", "exposure_preview", "recent_exposure"])
def test_tf121_repeat_chain_cannot_be_input_or_multiplier(raw_source, field):
    data = wire(raw_source)
    data["request"]["policy"][field] = dict(numerator=1, denominator=2)
    bad(data)


@pytest.mark.parametrize("field", ["history", "novelty", "exploration", "never_exposed"])
def test_tf122_no_history_or_novelty_substitution(raw_source, field):
    data = wire(raw_source)
    data["request"][field] = True
    bad(data)


def test_tf123_favorable_fit_cannot_override_unsafe_grounding(raw_source):
    data = wire(raw_source)
    data["projection"]["source"]["grounded_candidate"]["sources"]["member_safety"] = []
    bad(seal_wire(data))


@pytest.mark.parametrize(
    "field", ["inventory_weight", "procurement_feasible", "SPEND_LIMIT", "is_safe"]
)
def test_tf124_no_feasibility_or_hidden_cost_weight(raw_source, field):
    data = wire(raw_source)
    data["request"]["policy"][field] = 1
    bad(data)


def test_tf125_main_protein_remains_preference_protein(raw_source):
    row = result_row(derive(raw_source))
    assert row.proof.target.kind == "PROTEIN" and row.proof.dimension.dimension == "MAIN_PROTEIN"
    assert not hasattr(row, "meal_role")


@pytest.mark.parametrize("field", ["candidate_comparison", "rank", "total", "utility"])
def test_tf126_no_candidate_comparison_scalar_or_ranking(raw_source, field):
    data = wire(derive(raw_source))
    data[field] = 1
    bad(data, validate)


@pytest.mark.parametrize(
    "field", ["shared_meal", "household_total", "all_members", "dimension_sum"]
)
def test_tf127_no_household_reducer_or_other_member_copy(raw_source, field):
    data = wire(raw_source)
    data["request"][field] = True
    bad(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("planner_ready", True),
        ("activation_ready", True),
        ("learned_evidence", "AVAILABLE"),
        ("aggregate", "AVAILABLE"),
        ("planner_ready", 0),
        ("activation_ready", "false"),
    ],
)
def test_tf128_non_authority_literals_cannot_be_promoted(raw_source, field, value):
    data = wire(derive(raw_source))
    data[field] = value
    bad(seal_wire(data, result=True), validate)


def test_tf29_raw_like_has_one_exact_policy_mapping_per_target():
    source = make_sources()
    result = derive(source)
    assert {r.proof.target.kind for r in result.targets} == {
        "INGREDIENT",
        "DIRECT_RECIPE",
        "PROTEIN",
        "METHOD",
        "FLAVOR",
    }
    assert all(r.status == "AVAILABLE" and r.value.amount.numerator == 1 for r in result.targets)
    assert all(
        r.direct_signal == "DECLARED_LIKE" and r.selected_mode == "RAW_EXPLICIT"
        for r in result.targets
    )
    assert validate(result) == result
