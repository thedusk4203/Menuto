"""Authored test-only conditional policies and retained cuts, never runtime defaults."""

from datetime import timedelta
from uuid import uuid4

from app.domain.feature_identity import canonical
from app.modules.planning import tastefit_contracts as c
from app.modules.planning.candidate_feature_projection import project_candidate_features
from app.modules.planning.tastefit import candidate_target_set, member_capture_plan
from app.modules.preferences import contracts as p
from app.modules.preferences import tastefit_contracts as m
from candidate_feature_fixtures import make_subject
from preference_fixtures import command, declaration, provenance
from target_affinity_fixtures import entry, policy, revision

KINDS = ("INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR")


def interpretation(
    explicit=None, compatibility=None, shrinkage=None, hierarchy=None, hierarchy_provider=None
):
    explicit = explicit or policy()
    return m.TasteFitMemberInterpretationPlan(
        explicit_policy=explicit,
        expected_explicit_policy_id=explicit.policy_id,
        expected_explicit_policy_version=explicit.policy_version,
        expected_explicit_policy_fingerprint=p._profile_hash(explicit),
        compatibility_policy=compatibility,
        expected_compatibility_policy_fingerprint=compatibility.fingerprint()
        if compatibility
        else None,
        shrinkage_policy=shrinkage,
        expected_shrinkage_policy_fingerprint=shrinkage.fingerprint() if shrinkage else None,
        hierarchy_provider_id=hierarchy_provider.id if hierarchy_provider else None,
        hierarchy_provider_command_hash=hierarchy_provider.command_hash
        if hierarchy_provider
        else None,
        hierarchy_policy=hierarchy,
        expected_hierarchy_policy_fingerprint=hierarchy.fingerprint() if hierarchy else None,
    )


def fit_policy(
    plan,
    *,
    kinds=KINDS,
    mode="EXPLICIT_ONLY",
    declared="RAW_EXPLICIT",
    undeclared="NO_EVIDENCE",
    mappings=None,
    **changes,
):
    groups = []
    for kind in kinds:
        rows = []
        for rule in next(
            g for g in plan.explicit_policy.target_policies if g.target_kind == kind
        ).affinity_rules:
            descriptor = c.RawExplicitTasteFitCoordinate(
                target_kind=kind,
                explicit_policy_id=plan.expected_explicit_policy_id,
                explicit_policy_version=plan.expected_explicit_policy_version,
                explicit_policy_fingerprint=plan.expected_explicit_policy_fingerprint,
            )
            if declared == "RAW_EXPLICIT":
                rows.append(
                    c.TasteFitMappingRow(
                        target_kind=kind,
                        source_mode=declared,
                        semantic_state=rule.value,
                        source_coordinate=descriptor,
                        source_amount=dict(
                            numerator=rule.amount.numerator, denominator=rule.amount.denominator
                        ),
                        fit_amount=dict(
                            numerator={"LIKE": 1, "DISLIKE": -1, "NEUTRAL": 0}[rule.value],
                            denominator=2,
                        ),
                    )
                )
        groups.append(
            dict(
                target_kind=kind,
                capture_mode=mode,
                declared_selection=declared,
                undeclared_selection=undeclared,
                mappings=rows if mappings is None else mappings.get(kind, ()),
            )
        )
    return c.TasteFitInterpretationPolicy.model_validate(
        dict(
            contract_version="candidate-member-tastefit-policy.v1",
            policy_id="synthetic.fit",
            policy_version="1",
            provenance=provenance(),
            interpretation_mode="VERSIONED_CONSUMER_POLICY_REPLAY",
            admitted_kinds=kinds,
            kind_policies=groups,
            operator="PER_TARGET_FINITE_EXACT_LOOKUP",
            aggregation="NOT_PERFORMED",
            evidence_strength_effect="LINEAGE_ONLY",
            retraction="SUPPRESS",
            max_targets=100,
            max_policy_bytes=2000000,
            max_source_bytes=100000000,
        )
        | changes
    )


def request(projection_request, member_plan=None, fit=None, *, member_id=None, probes=()):
    member_plan = member_plan or interpretation()
    fit = fit or fit_policy(member_plan)
    return c.CandidateMemberTasteFitRequest(
        household_id=projection_request.grounding_request.household_id,
        member_id=member_id or projection_request.grounding_request.tracked_member_id,
        projection_request=projection_request,
        projection_mode="FRESH_CANONICAL_PROJECTION",
        diagnostic_targets=probes,
        policy=fit,
        expected_policy_id=fit.policy_id,
        expected_policy_version=fit.policy_version,
        expected_policy_fingerprint=fit.fingerprint(),
        member_interpretation=member_plan,
    )


def frame(owner, targets, actor, clock, *, session_user="synthetic.reader"):
    return m.TasteFitCaptureFrame(
        owner=owner,
        targets=targets,
        actor_user_id=actor,
        configured_host="synthetic.local",
        configured_port=5432,
        database_name="synthetic",
        database_oid=42,
        server_address="127.0.0.1",
        server_port=5432,
        session_user=session_user,
        isolation="REPEATABLE READ",
        read_only=True,
        started_at=clock - timedelta(days=10),
        completed_at=clock + timedelta(days=10),
    )


def seal(source):
    return source.model_copy(update=dict(fingerprint=source.expected_fingerprint()))


def seal_result(result):
    return result.model_copy(update=dict(fingerprint=result.expected_fingerprint()))


def make_sources(
    *,
    state="DECLARED",
    value="LIKE",
    strength="LOW",
    dimensions=("METHOD", "MAIN_PROTEIN", "FLAVOR"),
    projection_source=None,
    kinds=KINDS,
    explicit_policy=None,
    extra_identities=(),
    probes=(),
    values=None,
):
    projection = project_candidate_features(projection_source or make_subject(dimensions))
    plan = interpretation(explicit_policy or policy(self_level=strength))
    q = request(projection.source.request, plan, fit_policy(plan, kinds=kinds), probes=probes)
    capture_plan = member_capture_plan(q, projection)
    _, targets = candidate_target_set(projection, probes)
    candidate = projection.source.grounded_candidate
    ingredients = {i.id: i for i in candidate.sources.ingredients}
    terms = {t.id: t for t in projection.source.feature_input.sources.terms}
    extra = {p.preference_target_key(e.target()): e for e in extra_identities}
    identities = {}
    declarations = []
    actor = uuid4()
    for key, target in targets.items():
        identity = (
            ingredients.get(target.ingredient_id)
            if target.kind == "INGREDIENT"
            else candidate.sources.recipe.recipe
            if target.kind == "DIRECT_RECIPE" and target.recipe_id == projection.binding.recipe_id
            else terms.get(target.feature_term_id)
            if target.kind in {"PROTEIN", "METHOD", "FLAVOR"}
            else None
        )
        identities[key] = extra.get(key) or entry(target, identity=identity)
        chosen_state = (values or {}).get(key, state)
        if chosen_state == "UNDECLARED":
            continue
        cmd = command(
            household_id=q.household_id,
            member_id=q.member_id,
            actor_user_id=actor,
            target=target,
            value=value,
        )
        first = declaration(cmd, sequence=len(declarations) + 1)
        declarations.append(first)
        if chosen_state == "RETRACTED":
            declarations.append(revision(first, retract=True))
    clock = projection.source.capture_completed_at + timedelta(days=1)
    ledger = p.ExplicitMemberPreferenceSnapshot(
        household_id=q.household_id,
        member_id=q.member_id,
        frontier=len(declarations),
        captured_at=clock,
        declarations=declarations,
        feature_terms=tuple(
            e.identity
            for e in identities.values()
            if e.kind in {"METHOD", "FLAVOR", "PROTEIN"}
            and any(d.command.target == e.target() for d in declarations)
        ),
    )
    entries = []
    for key, target in targets.items():
        explicit = p.ExplicitTargetAffinityInput(
            source=p.ExplicitTargetAffinitySourceSnapshotDraft(
                request=dict(
                    household_id=q.household_id, member_id=q.member_id, requested_targets=(target,)
                ),
                preferences=ledger,
                manifest=dict(
                    household_id=q.household_id, member_id=q.member_id, entries=(identities[key],)
                ),
                capture_completed_at=clock,
            ),
            policy=plan.explicit_policy,
        )
        entries.append(
            m.TasteFitMemberSourceEntry(
                target=target, explicit=explicit, exact_target=None, one_hop=None
            )
        )
    member_frame = frame("MEMBER", tuple(targets.values()), actor, clock)
    candidate_frame = frame("CANDIDATE", tuple(targets.values()), actor, clock)
    source = c.CandidateMemberTasteFitSources(
        request=q,
        projection=projection,
        member_sources=m.TasteFitMemberSourceBundle(
            plan=capture_plan, entries=entries, frames=(member_frame,)
        ),
        candidate_frame=candidate_frame,
        capture_started_at=clock - timedelta(days=11),
        capture_completed_at=clock + timedelta(days=11),
        fingerprint="0" * 64,
    )
    return seal(source)


def with_policy(source, policy):
    q = c.CandidateMemberTasteFitRequest.model_validate(
        source.request.model_dump()
        | dict(
            policy=policy,
            expected_policy_id=policy.policy_id,
            expected_policy_version=policy.policy_version,
            expected_policy_fingerprint=policy.fingerprint(),
        )
    )
    plan = member_capture_plan(q, source.projection)
    return seal(
        source.model_copy(
            update=dict(
                request=q, member_sources=source.member_sources.model_copy(update=dict(plan=plan))
            )
        )
    )


def wire(value):
    return canonical(value)


def with_member_modes(
    source,
    *,
    kind="PROTEIN",
    declared="EXACT_TARGET_EFFECTIVE",
    undeclared="PRIOR_ONLY",
    prior_state="AVAILABLE",
    prior_amount=(1, 2),
    hierarchy=False,
    parent_state="DECLARED",
    parent_value="LIKE",
    external_parent=False,
    hierarchy_operations=None,
    parent_recipe=None,
    destination_recipe=None,
    prior_on_parent=False,
):
    from app.modules.preferences.hierarchical_affinity_contracts import (
        OneHopHierarchicalMemberPreferenceInput,
    )
    from app.modules.preferences.prior_affinity_contracts import ExactTargetPriorBackedAffinityInput
    from hierarchical_affinity_fixtures import hierarchy_cut
    from hierarchy_fixtures import policy as transfer_policy
    from prior_shrinkage_fixtures import compatibility, reference_source, shrinkage

    selected = next(e for e in source.member_sources.entries if e.target.kind == kind)
    entries = list(source.member_sources.entries)
    parent_entry = None
    if hierarchy:
        if external_parent or kind == "INGREDIENT" or parent_recipe is not None:
            t = (
                p.RecipePreferenceTarget(recipe_id=parent_recipe.recipe.id)
                if parent_recipe
                else p.IngredientPreferenceTarget(ingredient_id=uuid4())
            )
            identity = entry(t, identity=parent_recipe.recipe if parent_recipe else None)
            explicit = selected.explicit.model_copy(
                update=dict(
                    source=selected.explicit.source.model_copy(
                        update=dict(
                            request=selected.explicit.source.request.model_copy(
                                update=dict(requested_targets=(t,))
                            ),
                            manifest=selected.explicit.source.manifest.model_copy(
                                update=dict(entries=(identity,))
                            ),
                        )
                    )
                )
            )
            parent_entry = m.TasteFitMemberSourceEntry(
                target=t, explicit=explicit, exact_target=None, one_hop=None
            )
            entries.append(parent_entry)
        else:
            parent_entry = next(e for e in entries if e.target.kind == "INGREDIENT")
        # Rebuild one complete ledger for every primitive, not a sliced parent ledger.
        ledger = selected.explicit.source.preferences
        rows = [r for r in ledger.declarations if r.command.target != parent_entry.target]
        # Preserve every destination revision (especially RETRACT); only the
        # independent synthetic parent's stream is rebuilt for this scenario.
        from preference_fixtures import NOW

        rows = [
            type(r).model_validate(
                r.model_dump() | dict(member_sequence=i, recorded_at=NOW + timedelta(seconds=i))
            )
            for i, r in enumerate(rows, 1)
        ]
        if parent_state != "UNDECLARED":
            first = declaration(
                command(
                    household_id=source.request.household_id,
                    member_id=source.request.member_id,
                    actor_user_id=source.candidate_frame.actor_user_id,
                    target=parent_entry.target,
                    value=parent_value,
                ),
                sequence=len(rows) + 1,
            )
            rows.append(first)
            if parent_state == "RETRACTED":
                rows.append(revision(first, retract=True))
        terms = {
            e.explicit.source.manifest.entries[0].identity.id: e.explicit.source.manifest.entries[
                0
            ].identity
            for e in entries
            if e.target.kind in {"METHOD", "FLAVOR", "PROTEIN"}
            and any(r.command.target == e.target for r in rows)
        }
        ledger = p.ExplicitMemberPreferenceSnapshot.model_validate(
            ledger.model_dump()
            | dict(declarations=rows, frontier=len(rows), feature_terms=tuple(terms.values()))
        )
        entries = [
            e.model_copy(
                update=dict(
                    explicit=e.explicit.model_copy(
                        update=dict(
                            source=e.explicit.source.model_copy(update=dict(preferences=ledger))
                        )
                    )
                )
            )
            for e in entries
        ]
        selected = next(e for e in entries if e.target == selected.target)
        parent_entry = next(e for e in entries if e.target == parent_entry.target)
    identity = selected.explicit.source.manifest.entries[0]
    reference_entry = parent_entry if prior_on_parent else selected
    template = reference_source(
        reference_entry.target,
        reference_entry.explicit.source.manifest.entries[0].identity,
        state=prior_state,
        amount=prior_amount,
    )
    comp = compatibility(selected.explicit, template)
    sh = shrinkage(comp)
    transfer = None
    hsource = None
    if hierarchy:
        transfer = transfer_policy(source_kind=parent_entry.target.kind, destination_kind=kind)
        body = transfer.model_dump()
        body.update(
            explicit_policy=source.request.member_interpretation.explicit_policy,
            compatibility_policy=comp,
        )
        for direction in body["directions"]:
            for row in direction["rows"]:
                row["source_descriptor"] = comp.coordinate_for(
                    direction["source_kind"]
                ).model_dump()
        transfer = type(transfer).model_validate(body)
        from app.modules.preferences.hierarchy_contracts import (
            HierarchyOwnerManifest,
            HierarchyTargetIdentity,
        )

        endpoint_entries = (parent_entry.explicit.source.manifest.entries[0], identity)
        owner = HierarchyOwnerManifest(
            identities=tuple(
                HierarchyTargetIdentity(target=e.target(), identity=e.identity)
                for e in endpoint_entries
            ),
            catalog_frontier=0,
            catalog_streams=(),
            recipe_frontier=0,
            recipes=tuple(
                r
                for r in (
                    parent_recipe,
                    destination_recipe or source.projection.source.grounded_candidate.sources.recipe
                    if selected.target.kind == "DIRECT_RECIPE"
                    else None,
                )
                if r is not None
            ),
            scopes=(),
            terms=tuple(
                e.identity for e in endpoint_entries if e.kind in {"METHOD", "FLAVOR", "PROTEIN"}
            ),
        )

        hsource = hierarchy_cut(
            HierarchyTargetIdentity(
                target=parent_entry.target,
                identity=parent_entry.explicit.source.manifest.entries[0].identity,
            ),
            HierarchyTargetIdentity(target=selected.target, identity=identity.identity),
            transfer,
            operations=hierarchy_operations,
            owner=owner,
        )
    plan = interpretation(
        source.request.member_interpretation.explicit_policy,
        comp,
        sh,
        transfer,
        hsource.provider if hsource else None,
    )
    needed = {p.preference_target_key(selected.target)}
    if parent_entry:
        needed.add(p.preference_target_key(parent_entry.target))
    by_key = {}
    for e in entries:
        exact = None
        if p.preference_target_key(e.target) in needed:
            identities = {
                p.preference_target_key(i.target): i
                for i in template.identities
                if template.publications
            }
            from app.modules.preferences.reference_prior_contracts import (
                ReferencePriorTargetIdentity,
            )

            identities[p.preference_target_key(e.target)] = ReferencePriorTargetIdentity(
                target=e.target, identity=e.explicit.source.manifest.entries[0].identity
            )
            ref = template.model_copy(
                update=dict(
                    request=template.request.model_copy(update=dict(requested_targets=(e.target,))),
                    identities=tuple(identities.values()),
                )
            )
            exact = ExactTargetPriorBackedAffinityInput(
                explicit=e.explicit,
                reference_source=ref,
                compatibility_policy=comp,
                shrinkage_policy=sh,
            )
        by_key[p.preference_target_key(e.target)] = e.model_copy(update=dict(exact_target=exact))
    if hierarchy:
        e = by_key[p.preference_target_key(selected.target)]
        parent = by_key[p.preference_target_key(parent_entry.target)]
        e = e.model_copy(
            update=dict(
                one_hop=OneHopHierarchicalMemberPreferenceInput(
                    destination=e.exact_target, parent=parent.exact_target, hierarchy_source=hsource
                )
            )
        )
        by_key[p.preference_target_key(e.target)] = e
    mode = "EXACT_TARGET_AND_ONE_HOP" if hierarchy else "EXACT_TARGET"
    fit = fit_policy(
        plan, kinds=(kind,), mode=mode, declared=declared, undeclared=undeclared, mappings={}
    )
    q = request(
        source.request.projection_request,
        plan,
        fit,
        member_id=source.request.member_id,
        probes=source.request.diagnostic_targets,
    )
    capture_plan = member_capture_plan(q, source.projection)
    clock, actor = source.capture_completed_at, source.candidate_frame.actor_user_id
    all_targets = tuple(e.target for e in by_key.values())
    frames = [
        frame("MEMBER", all_targets, actor, clock),
        frame(
            "PRIOR",
            tuple(e.target for e in by_key.values() if e.exact_target),
            actor,
            template.capture_completed_at,
            session_user=template.reader_session.role_name,
        ),
    ]
    if hierarchy:
        frames.append(
            frame(
                "HIERARCHY",
                (selected.target,),
                actor,
                hsource.capture_completed_at,
                session_user=hsource.reader_session.role_name,
            )
        )
    # Keep the member cut inside the original same-session coordinator interval.
    frames[0] = source.member_sources.frames[0].model_copy(update=dict(targets=all_targets))
    bundle = m.TasteFitMemberSourceBundle(
        plan=capture_plan, entries=tuple(by_key.values()), frames=frames
    )
    result = seal(source.model_copy(update=dict(request=q, member_sources=bundle)))
    # Author only the finite values actually intended for this synthetic scenario.
    from app.modules.preferences.tastefit_public import replay_tastefit_member_sources

    view = next(v for v in replay_tastefit_member_sources(bundle) if v.target == selected.target)
    mappings = []
    if view.explicit.raw_state.status == "DECLARED":
        state = view.explicit.raw_state.value
        exact = view.exact_target.effective
        if declared == "RAW_EXPLICIT":
            descriptor = c.RawExplicitTasteFitCoordinate(
                target_kind=kind,
                explicit_policy_id=plan.expected_explicit_policy_id,
                explicit_policy_version=plan.expected_explicit_policy_version,
                explicit_policy_fingerprint=plan.expected_explicit_policy_fingerprint,
            )
            amount = view.explicit.affinity.amount
        else:
            descriptor = c.ProfileTasteFitSourceCoordinate(coordinate=exact.value.coordinate)
            amount = exact.value.amount
        mappings.append(
            c.TasteFitMappingRow(
                target_kind=kind,
                source_mode=declared,
                semantic_state=state,
                source_coordinate=descriptor,
                source_amount=dict(numerator=amount.numerator, denominator=amount.denominator),
                fit_amount=dict(
                    numerator={"LIKE": 1, "DISLIKE": -1, "NEUTRAL": 0}[state], denominator=2
                ),
            )
        )
    if (
        undeclared == "PRIOR_ONLY"
        and view.exact_target.effective.status == "AVAILABLE"
        and (view.exact_target.effective.mode == "PRIOR_ONLY_COLD_START")
    ):
        v = view.exact_target.effective.value
        mappings.append(
            c.TasteFitMappingRow(
                target_kind=kind,
                source_mode="PRIOR_ONLY",
                semantic_state="NO_DECLARATION",
                source_coordinate=c.ProfileTasteFitSourceCoordinate(coordinate=v.coordinate),
                source_amount=v.amount.model_dump(),
                fit_amount=dict(numerator=-1 if v.amount.numerator < 0 else 1, denominator=3),
            )
        )
    if (
        hierarchy
        and undeclared == "ONE_HOP_INHERITED"
        and view.one_hop.inherited.status == "AVAILABLE"
    ):
        v = view.one_hop.inherited
        mappings.append(
            c.TasteFitMappingRow(
                target_kind=kind,
                source_mode="ONE_HOP_INHERITED",
                semantic_state=v.trace.semantic_state,
                source_coordinate=c.InheritedTasteFitSourceCoordinate(
                    coordinate=v.value.coordinate
                ),
                source_amount=v.value.amount.model_dump(),
                fit_amount=dict(numerator={"LIKE":1,"DISLIKE":-1,"NEUTRAL":0}[
                    v.trace.semantic_state], denominator=4),
            )
        )
    return with_policy(
        result,
        fit_policy(
            plan,
            kinds=(kind,),
            mode=mode,
            declared=declared,
            undeclared=undeclared,
            mappings={kind: mappings},
        ),
    )
