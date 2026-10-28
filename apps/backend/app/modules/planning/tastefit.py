"""Pure conditional per-target interpretation; no ambient policy or scalar utility."""

from pydantic import ValidationError

from app.domain.feature_identity import canonical, canonical_bytes
from app.domain.resolution import ResolutionError
from app.modules.planning import tastefit_contracts as c
from app.modules.planning.candidate_feature_projection import validate_candidate_feature_projection
from app.modules.preferences.contracts import (
    FeaturePreferenceTarget,
    IngredientPreferenceTarget,
    RecipePreferenceTarget,
    preference_target_key,
)
from app.modules.preferences.tastefit_contracts import (
    TasteFitMemberCapturePlan,
    TasteFitMemberTargetPlan,
    check_tastefit_frames,
    check_tastefit_immutable_facts,
)
from app.modules.preferences.tastefit_public import replay_tastefit_member_sources
from app.modules.recipes.contracts import FeatureTermQuery, resolve_feature_input


def _fail(code, detail):
    raise ResolutionError(code, detail, rejected=True)


def _budget(raw, *, source=False):
    """Wire budgets precede deep child replay; canonical budgets are checked again."""
    body = canonical(raw)
    if not isinstance(body, dict):
        _fail("REPLAY_MISMATCH", "A complete retained object is required")
    request = body.get("request", {}) if source else body
    if not isinstance(request, dict):
        _fail("REPLAY_MISMATCH", "A complete request is required")
    policy = request.get("policy")
    if policy is None:
        _fail("POLICY_MISSING", "An explicit authored policy is required")
    if not isinstance(policy, dict):
        _fail("POLICY_MISSING", "A complete policy body is required")
    target_limit = policy.get("max_targets")
    if type(target_limit) is not int or target_limit <= 0:
        _fail("RESOURCE_LIMIT", "Positive authored target budget required")
    if source:
        bundle = body.get("member_sources")
        entries = bundle.get("entries") if isinstance(bundle, dict) else None
        if isinstance(entries, (list, tuple)) and len(entries) > target_limit:
            _fail("RESOURCE_LIMIT", "Retained target entries exceed the authored budget")
    for field, value in (("max_policy_bytes", policy), ("max_source_bytes", body)):
        limit = policy.get(field)
        if type(limit) is not int or limit <= 0:
            _fail("RESOURCE_LIMIT", "Positive authored resource limits required")
        if len(canonical_bytes(value)) > limit:
            _fail("RESOURCE_LIMIT", "Complete retained input exceeds " + field)
    return body


def _parse_request(request):
    raw = _budget(request)
    p = raw["policy"]
    if (
        p.get("contract_version") != "candidate-member-tastefit-policy.v1"
        or p.get("policy_id") != raw.get("expected_policy_id")
        or p.get("policy_version") != raw.get("expected_policy_version")
    ):
        _fail("POLICY_VERSION_MISMATCH", "Exact policy contract/id/version required")
    kinds = {"INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"}
    probes = raw.get("diagnostic_targets", ())
    if not isinstance(probes, (list, tuple)):
        _fail("REPLAY_MISMATCH", "Diagnostic target set required")
    if any(not isinstance(t, dict) or t.get("kind") not in kinds for t in probes):
        _fail("TARGET_KIND_UNSUPPORTED", "Only five existing preference kinds are supported")
    admitted = p.get("admitted_kinds", ())
    if not isinstance(admitted, (list, tuple)):
        _fail("REPLAY_MISMATCH", "Admitted kind set required")
    if any(k not in kinds for k in admitted):
        _fail("TARGET_KIND_UNSUPPORTED", "No additional preference kind is supported")
    try:
        result = c.CandidateMemberTasteFitRequest.model_validate(raw)
    except (ValueError, TypeError) as exc:
        for code in (
            "POLICY_FINGERPRINT_MISMATCH",
            "SUBJECT_OWNER_MISMATCH",
            "SOURCE_POLICY_BINDING_MISMATCH",
        ):
            if code in str(exc):
                _fail(code, str(exc))
        _fail("REPLAY_MISMATCH", str(exc))
    _budget(result)
    return result


def _subject_member(request, projection):
    g = projection.source.grounded_candidate
    members = {(m.household_id, m.member_id) for m in g.sources.members}
    if (request.household_id, request.member_id) not in members:
        _fail("SUBJECT_OWNER_MISMATCH", "Exact subject is not a canonical household member")
    if request.member_id not in {p.member_id for p in g.request.participants.participants}:
        _fail("SUBJECT_MEMBER_NOT_IN_CANDIDATE_CONTEXT", "Subject is not a candidate participant")


def candidate_target_set(projection, diagnostic_targets):
    """Canonical base before policy filtering; diagnostic probes never trim this set."""
    targets = [RecipePreferenceTarget(recipe_id=projection.binding.recipe_id)]
    targets.extend(
        IngredientPreferenceTarget(ingredient_id=r.ingredient_id)
        for r in projection.source.grounded_candidate.request.candidate.resolved_ingredients
    )
    for d in projection.dimensions:
        targets.extend(
            FeaturePreferenceTarget(
                kind="PROTEIN" if d.dimension == "MAIN_PROTEIN" else d.dimension,
                feature_term_id=tid,
            )
            for tid in d.positive_term_ids
        )
    base = {preference_target_key(t): t for t in targets}
    all_targets = base | {preference_target_key(t): t for t in diagnostic_targets}
    return base, dict(sorted(all_targets.items()))


def member_capture_plan(request, projection):
    """Planning supplies destinations only; Preferences independently discovers parents."""
    _subject_member(request, projection)
    _, targets = candidate_target_set(projection, request.diagnostic_targets)
    groups = {p.target_kind: p for p in request.policy.kind_policies}
    # Candidate proof (without member evidence) determines which modes are needed.
    rows = []
    for target in targets.values():
        state, _, _, _ = _candidate_state(projection, target)
        group = groups.get(target.kind)
        mode = group.capture_mode if group and state == "PRESENT" else "EXPLICIT_ONLY"
        rows.append(TasteFitMemberTargetPlan(target=target, capture_mode=mode))
    return TasteFitMemberCapturePlan(
        household_id=request.household_id,
        member_id=request.member_id,
        interpretation=request.member_interpretation,
        targets=rows,
        candidate_recipe=projection.source.grounded_candidate.sources.recipe,
    )


def _candidate_state(projection, target):
    candidate = projection.source.grounded_candidate
    if target.kind == "DIRECT_RECIPE":
        present = target.recipe_id == projection.binding.recipe_id
        return ("PRESENT" if present else "ABSENT"), None, None, ()
    if target.kind == "INGREDIENT":
        refs = tuple(
            sorted(
                {
                    r.requirement_id
                    for r in candidate.request.candidate.resolved_ingredients
                    if r.ingredient_id == target.ingredient_id
                },
                key=str,
            )
        )
        return ("PRESENT" if refs else "ABSENT"), None, None, refs
    dimension = "MAIN_PROTEIN" if target.kind == "PROTEIN" else target.kind
    discovery = next((d for d in projection.dimensions if d.dimension == dimension), None)
    if discovery is None:
        return "UNRESOLVED", "DIMENSION_NOT_CAPTURED", None, ()
    resolution = resolve_feature_input(
        projection.source.feature_input,
        (FeatureTermQuery(dimension=dimension, term_ids=(target.feature_term_id,)),),
    )[0]
    state = {"PRESENT": "PRESENT", "REVIEWED_ABSENT": "ABSENT", "UNRESOLVED": "UNRESOLVED"}[
        resolution.state
    ]
    return state, resolution.reason, resolution, ()


def _proof(projection, target, base, entry):
    identity = entry.explicit.source.manifest.entries[0]
    if identity.target() != target:
        _fail("CANONICAL_TARGET_UNAVAILABLE", "Exact owner target identity required")
    state, reason, term, refs = _candidate_state(projection, target)
    dimension = next(
        (
            d
            for d in projection.dimensions
            if d.dimension == ("MAIN_PROTEIN" if target.kind == "PROTEIN" else target.kind)
        ),
        None,
    )
    candidate = projection.source.grounded_candidate
    if target.kind == "DIRECT_RECIPE" and state == "PRESENT":
        if identity.identity != candidate.sources.recipe.recipe:
            _fail("SOURCE_CUT_INCOHERENT", "Immutable stable recipe identity differs")
    if target.kind == "INGREDIENT" and state == "PRESENT":
        if target.ingredient_id not in {i.id for i in candidate.sources.ingredients}:
            _fail("CANONICAL_TARGET_UNAVAILABLE", "Selected ingredient proof missing")
    return c.TasteFitTargetProof(
        target=target,
        role="BASE" if preference_target_key(target) in base else "DIAGNOSTIC_ONLY",
        identity=identity,
        candidate_state=state,
        reason=reason,
        requirement_ids=refs,
        term_resolution=term,
        dimension=dimension,
    )


def _inherited_applicable(view, projection):
    if view.one_hop is None or view.one_hop.inherited.status != "AVAILABLE":
        return True
    if view.target.kind != "DIRECT_RECIPE":
        return True
    identity = view.one_hop.inherited.trace.relation_identity
    binding = next(b for b in identity.recipe_bindings if b.endpoint == "DESTINATION")
    if binding.recipe_version_id != projection.binding.recipe_version_id:
        return False
    # Frozen METHOD keys are version-wide cooking context; non-METHOD paths are
    # explicitly authored by the relation and remain exact, even for reviewed scope.
    return binding.path is None or binding.path == projection.binding.path


def _select(view, group, plan):
    raw = view.explicit
    state = raw.raw_state
    mode = group.declared_selection if state.status == "DECLARED" else group.undeclared_selection
    if state.status == "RETRACTED":
        return None, None, None, None, "MEMBER_RETRACTED"
    if mode == "NO_EVIDENCE":
        return mode, None, None, None, "MEMBER_UNDECLARED"
    if mode == "RAW_EXPLICIT":
        if raw.affinity.status != "AVAILABLE":
            return mode, None, None, None, state.status
        descriptor = c.RawExplicitTasteFitCoordinate(
            target_kind=view.target.kind,
            explicit_policy_id=plan.expected_explicit_policy_id,
            explicit_policy_version=plan.expected_explicit_policy_version,
            explicit_policy_fingerprint=plan.expected_explicit_policy_fingerprint,
        )
        return mode, state.value, descriptor, raw.affinity.amount, None
    if mode in {"EXACT_TARGET_EFFECTIVE", "PRIOR_ONLY"}:
        exact = view.exact_target
        if exact is None:
            raise ValueError("Required exact-target source was not captured")
        expected_modes = (
            {"PRIOR_ONLY_COLD_START"}
            if mode == "PRIOR_ONLY"
            else {"EXPLICIT_ONLY", "BLENDED_EXPLICIT_AND_PRIOR"}
        )
        if exact.effective.status != "AVAILABLE" or exact.effective.mode not in expected_modes:
            reason = (
                exact.mapped_prior.reason
                if exact.mapped_prior.status == "UNAVAILABLE"
                else exact.effective.reason
                if exact.effective.status == "UNAVAILABLE"
                else "SELECTED_MODE_UNAVAILABLE"
            )
            return mode, None, None, None, reason
        return (
            mode,
            "NO_DECLARATION" if mode == "PRIOR_ONLY" else state.value,
            c.ProfileTasteFitSourceCoordinate(coordinate=exact.effective.value.coordinate),
            exact.effective.value.amount,
            None,
        )
    inherited = view.one_hop.inherited if view.one_hop else None
    if inherited is None:
        raise ValueError("Required one-hop source was not captured")
    if inherited.status != "AVAILABLE":
        reason = (
            inherited.source_reason
            if getattr(inherited, "source_reason", None)
            else inherited.reason
        )
        return mode, None, None, None, reason
    return (
        mode,
        inherited.trace.semantic_state,
        c.InheritedTasteFitSourceCoordinate(coordinate=inherited.value.coordinate),
        inherited.value.amount,
        None,
    )


def _interpret(proof, view, request, subject, projection):
    raw = view.explicit
    state = raw.raw_state
    group = next(
        (p for p in request.policy.kind_policies if p.target_kind == proof.target.kind), None
    )
    direct = "DECLARED_" + state.value if state.status == "DECLARED" else "NONE"
    fields = dict(
        proof=proof,
        member_views=view,
        policy_admission="ADMITTED" if group else "NOT_ADMITTED",
        selected_mode=None,
        status="UNAVAILABLE",
        reason=None,
        source_reason=None,
        direct_signal=direct,
        declaration_id=state.declaration_id,
        evidence_strength=raw.evidence_strength,
        semantic_state=None,
        source_coordinate=None,
        source_amount=None,
        mapping=None,
        value=None,
    )
    if state.status == "RETRACTED":
        fields.update(status="SUPPRESSED", reason="MEMBER_RETRACTED")
    elif not group:
        fields["reason"] = "POLICY_TARGET_NOT_ADMITTED"
    elif proof.candidate_state != "PRESENT":
        fields["reason"] = (
            "CANDIDATE_TARGET_ABSENT"
            if proof.candidate_state == "ABSENT"
            else proof.reason or "CANDIDATE_TARGET_UNRESOLVED"
        )
    else:
        mode, semantic, descriptor, amount, error = _select(
            view, group, request.member_interpretation
        )
        fields.update(selected_mode=mode, semantic_state=semantic, source_coordinate=descriptor)
        if mode == "ONE_HOP_INHERITED" and not _inherited_applicable(view, projection):
            fields.update(
                reason="INHERITED_DESTINATION_CONTEXT_MISMATCH",
                semantic_state=None,
                source_coordinate=None,
            )
        elif error is not None:
            fields.update(
                reason="MEMBER_UNDECLARED"
                if mode == "NO_EVIDENCE"
                else "SELECTED_EVIDENCE_UNAVAILABLE",
                source_reason=error,
            )
        else:
            operand = c.TasteFitAmount(numerator=amount.numerator, denominator=amount.denominator)
            fields["source_amount"] = operand
            # Descriptor/kind/mode/semantic gates precede rational equality. No
            # arithmetic, interpolation, evidence multiplier or fallback exists.
            rows = tuple(
                r
                for r in group.mappings
                if r.source_mode == mode
                and r.semantic_state == semantic
                and r.source_coordinate == descriptor
            )
            selected = next((r for r in rows if r.source_amount == operand), None)
            if selected is None:
                fields["reason"] = (
                    "SOURCE_VALUE_NOT_MAPPED" if rows else "SOURCE_COORDINATE_NOT_ADMITTED"
                )
            else:
                coordinate = c.TasteFitCoordinate(
                    policy_fingerprint=request.policy.fingerprint(),
                    household_id=subject.household_id,
                    member_id=subject.member_id,
                    grounding_fingerprint=subject.grounding_fingerprint,
                    projection_fingerprint=subject.projection_fingerprint,
                    target=proof.target,
                )
                fields.update(
                    status="AVAILABLE",
                    mapping=selected,
                    value=c.ScopedTargetTasteFit(coordinate=coordinate, amount=selected.fit_amount),
                )
    selected_mode = fields["selected_mode"]
    fields["view_dispositions"] = tuple(
        (
            mode,
            (
                "SELECTED"
                if mode == selected_mode
                else "NOT_SELECTED"
                if captured
                else "NOT_REQUESTED_BY_POLICY"
            ),
        )
        for mode, captured in (
            ("RAW_EXPLICIT", True),
            ("EXACT_TARGET_EFFECTIVE", view.exact_target is not None),
            ("PRIOR_ONLY", view.exact_target is not None),
            ("ONE_HOP_INHERITED", view.one_hop is not None),
        )
    )
    return c.TasteFitTargetInterpretation(**fields)


def derive_candidate_member_tastefit(sources):
    try:
        raw = _budget(sources, source=True)
        request = _parse_request(raw.get("request"))
        projection = validate_candidate_feature_projection(raw.get("projection"))
        source = c.CandidateMemberTasteFitSources.model_validate(raw)
        if (
            source.projection != projection
            or request.projection_request != projection.source.request
        ):
            _fail("CANDIDATE_BINDING_MISMATCH", "Projection/request differs from primitive replay")
        if source.fingerprint != source.expected_fingerprint():
            _fail("REPLAY_MISMATCH", "Complete retained source fingerprint differs")
        plan = member_capture_plan(request, projection)
        if source.member_sources.plan != plan:
            _fail("SOURCE_CUT_INCOHERENT", "Member plan differs from candidate/policy proof")
        base, targets = candidate_target_set(projection, request.diagnostic_targets)
        views = replay_tastefit_member_sources(source.member_sources)
        if len(views) > request.policy.max_targets:
            _fail(
                "RESOURCE_LIMIT", "Complete base/probe/eligible-parent closure exceeds max_targets"
            )
        check_tastefit_immutable_facts(projection, source.member_sources)
        frame = source.candidate_frame
        frames = (frame,) + source.member_sources.frames
        check_tastefit_frames(frames)
        if frame.owner != "CANDIDATE" or tuple(targets.values()) != frame.targets:
            _fail("SOURCE_CUT_INCOHERENT", "Candidate frame target set differs")
        psource = projection.source
        if not (
            source.capture_started_at
            <= frame.started_at
            <= psource.capture_started_at
            <= psource.capture_completed_at
            <= frame.completed_at
            <= source.capture_completed_at
        ):
            _fail("SOURCE_CUT_INCOHERENT", "Candidate capture interval differs")
        member_frame = next(f for f in source.member_sources.frames if f.owner == "MEMBER")
        if (
            not source.capture_started_at
            <= member_frame.started_at
            <= (member_frame.completed_at)
            <= source.capture_completed_at
        ):
            _fail("SOURCE_CUT_INCOHERENT", "Same-session member capture interval differs")
        subject = c.TasteFitSubject(
            household_id=request.household_id,
            member_id=request.member_id,
            grounding_fingerprint=projection.binding.grounding_fingerprint,
            projection_fingerprint=projection.fingerprint,
            binding=projection.binding,
            grounding_request=projection.source.grounded_candidate.request,
        )
        entry_by_key = {preference_target_key(e.target): e for e in source.member_sources.entries}
        view_by_key = {preference_target_key(v.target): v for v in views}
        rows = tuple(
            _interpret(
                _proof(projection, t, base, entry_by_key[k]),
                view_by_key[k],
                request,
                subject,
                projection,
            )
            for k, t in targets.items()
        )
        dims = {d.dimension for d in projection.dimensions}
        fields = dict(
            sources=source,
            subject=subject,
            targets=rows,
            dimensions=projection.dimensions,
            dimension_diagnostics=tuple(
                (d, "CAPTURED" if d in dims else "DIMENSION_NOT_CAPTURED")
                for d in ("FLAVOR", "MAIN_PROTEIN", "METHOD")
            ),
        )
        temporary = c.CandidateMemberTasteFitDraft.model_construct(**fields, fingerprint="0" * 64)
        result = c.CandidateMemberTasteFitDraft(
            **fields, fingerprint=temporary.expected_fingerprint()
        )
        _budget(source, source=True)
        return result
    except ResolutionError:
        raise
    except (ValidationError, ValueError, TypeError, KeyError, AttributeError) as exc:
        code = "SOURCE_CUT_INCOHERENT" if "SOURCE_CUT_INCOHERENT" in str(exc) else "REPLAY_MISMATCH"
        raise ResolutionError(code, str(exc), rejected=True) from exc


def validate_candidate_member_tastefit(result):
    try:
        raw = canonical(result)
        expected = derive_candidate_member_tastefit(raw.get("sources"))
        parsed = c.CandidateMemberTasteFitDraft.model_validate(raw)
        if parsed != expected:
            _fail("REPLAY_MISMATCH", "Complete TasteFit semantics differ from retained primitives")
        return expected
    except ResolutionError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ResolutionError("REPLAY_MISMATCH", str(exc), rejected=True) from exc
