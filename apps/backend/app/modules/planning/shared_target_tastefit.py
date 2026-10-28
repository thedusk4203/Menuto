"""Full retained-child replay before any conditional shared-target arithmetic."""

from fractions import Fraction
from math import gcd

from pydantic import BaseModel

from app.domain.feature_identity import canonical, canonical_bytes
from app.domain.resolution import ResolutionError
from app.modules.planning import shared_target_tastefit_contracts as c
from app.modules.planning.tastefit_contracts import CandidateMemberTasteFitRequest
from app.modules.planning.tastefit_public import validate_candidate_member_tastefit


def _fail(code, detail):
    raise ResolutionError(code, detail, rejected=True)


def _bits(value, limit):
    if type(value) is int and value.bit_length() > limit:
        _fail("RESOURCE_LIMIT", "Authored integer bit budget exceeded")
    if isinstance(value, dict):
        for v in value.values():
            _bits(v, limit)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _bits(v, limit)


def _budget(value, mode):
    raw = canonical(value)
    if not isinstance(raw, dict):
        _fail("REPLAY_MISMATCH", "Complete retained object required")
    source = raw.get("sources", {}) if mode == "result" else raw
    request = source.get("request", {}) if mode != "request" else raw
    if not isinstance(source, dict) or not isinstance(request, dict):
        _fail("REPLAY_MISMATCH", "Complete retained request required")
    policy = request.get("policy")
    if not isinstance(policy, dict):
        _fail("POLICY_MISSING", "Explicit complete aggregation policy required")
    for name in (
        "max_members",
        "max_policy_bytes",
        "max_source_bytes",
        "max_result_bytes",
        "max_integer_bits",
    ):
        if type(policy.get(name)) is not int or policy[name] <= 0:
            _fail("RESOURCE_LIMIT", "Positive authored resource budgets required")
    _bits(raw, policy["max_integer_bits"])
    for rows in (request.get("members", ()), source.get("children", ())):
        if isinstance(rows, (tuple, list)) and len(rows) > policy["max_members"]:
            _fail("RESOURCE_LIMIT", "Complete member budget exceeded")
    checks = [(policy, "max_policy_bytes"), (source, "max_source_bytes")]
    if mode == "result":
        checks.append((raw, "max_result_bytes"))
    for body, name in checks:
        if len(canonical_bytes(body)) > policy[name]:
            _fail("RESOURCE_LIMIT", "Complete input exceeds " + name)
    return raw


def _parse_request(request):
    raw = _budget(request, "request")
    try:
        return c.SharedMemberTargetTasteFitRequest.model_validate(raw)
    except (ValueError, TypeError) as exc:
        for code in (
            "POLICY_VERSION_MISMATCH",
            "POLICY_FINGERPRINT_MISMATCH",
            "POLICY_TARGET_KIND_MISMATCH",
            "SUBJECT_OWNER_MISMATCH",
            "PARTICIPANT_SET_MISMATCH",
            "RESOURCE_LIMIT",
        ):
            if code in str(exc):
                _fail(code, str(exc))
        _fail("REPLAY_MISMATCH", str(exc))


def _child_request(request, member):
    return CandidateMemberTasteFitRequest(
        household_id=request.household_id,
        member_id=member.member_id,
        projection_request=request.projection_request,
        projection_mode="FRESH_CANONICAL_PROJECTION",
        diagnostic_targets=(request.target,),
        policy=member.policy,
        expected_policy_id=member.expected_policy_id,
        expected_policy_version=member.expected_policy_version,
        expected_policy_fingerprint=member.expected_policy_fingerprint,
        member_interpretation=member.member_interpretation,
    )


def _participants(request, projection):
    ground = projection.source.grounded_candidate
    if ground.request != request.projection_request.grounding_request:
        _fail("CANDIDATE_BINDING_MISMATCH", "Fresh canonical candidate request differs")
    ids = tuple(sorted((p.member_id for p in ground.request.participants.participants), key=str))
    actual = {(m.household_id, m.member_id) for m in ground.sources.members}
    if (
        not ids
        or ids != tuple(m.member_id for m in request.members)
        or ids != tuple(w.member_id for w in request.policy.member_weights)
    ):
        _fail("PARTICIPANT_SET_MISMATCH", "Entire canonical participant set required")
    if any((request.household_id, mid) not in actual for mid in ids):
        _fail("SUBJECT_OWNER_MISMATCH", "Participant lacks canonical household identity")
    return ids


def _chosen(child, target):
    rows = tuple(r for r in child.targets if r.proof.target == target)
    if len(rows) != 1:
        _fail("TARGET_BINDING_MISMATCH", "Exactly one complete chosen target proof required")
    return rows[0]


def _integrity_projection(child, row):
    # Exactly the reviewed three read-clock fields and their two derived hashes.
    # Every authored/effective/source clock, hidden history and frontier stays binding.
    body = canonical(child.sources.projection)
    body.pop("fingerprint")
    source = body["source"]
    for key in ("fingerprint", "capture_started_at", "capture_completed_at"):
        source.pop(key)
    source["feature_input"].pop("captured_at")
    return dict(projection=body, target_proof=row.proof)


def _owner_identities(children):
    """Typed transported facts only; no Preferences private helper imports."""
    immutable, cuts, ledgers = {}, {}, {}
    fact_types = {
        "app.modules.catalog.contracts.AffinityFeatureTermFact",
        "app.modules.recipes.contracts.RecipeFact",
        "app.modules.recipes.contracts.RecipeVersionSnapshot",
    }
    source_types = {
        (
            "app.modules.preferences.reference_prior_contracts.ReferencePriorSourceSnapshotDraft"
        ): "PRIOR",
        "app.modules.preferences.hierarchy_contracts.HierarchySourceSnapshotDraft": "HIERARCHY",
    }
    cut_fields = (
        "provider",
        "principals",
        "authority_events",
        "publications",
        "mutations",
        "streams",
        "frontier",
        "reader_principal_id",
        "reader_session",
        "reader_grant_id",
    )

    def agree(index, key, value):
        body = canonical_bytes(value)
        if key in index and index[key] != body:
            _fail(
                "SOURCE_CUT_INCOHERENT", "Conflicting complete typed owner cut/immutable identity"
            )
        index[key] = body

    def visit(value):
        qualified = type(value).__module__ + "." + type(value).__name__
        if qualified in fact_types:
            agree(immutable, (qualified, value.id), value)
        if qualified in source_types:
            agree(
                cuts,
                (source_types[qualified], value.provider.id),
                {name: getattr(value, name) for name in cut_fields},
            )
        if qualified == "app.modules.preferences.contracts.ExplicitMemberPreferenceSnapshot":
            body = canonical(value)
            body.pop("captured_at")
            body["declarations"].sort(key=lambda d: d["member_sequence"])
            body["feature_terms"].sort(key=lambda t: t["id"])
            agree(ledgers, (value.household_id, value.member_id), body)
        if isinstance(value, BaseModel):
            for name in type(value).model_fields:
                visit(getattr(value, name))
        elif isinstance(value, dict):
            for v in value.values():
                visit(v)
        elif isinstance(value, (tuple, list)):
            for v in value:
                visit(v)

    for child in children:
        visit(child)


def _coherence(source):
    request, children = source.request, source.children
    expected = tuple(m.member_id for m in request.members)
    captured = tuple(ch.subject.member_id for ch in children)
    if captured != expected:
        _fail(
            "SOURCE_COVERAGE_INCOMPLETE", "Exactly one full captured child per participant required"
        )
    rows, reference = [], None
    endpoints, actors, readers = set(), set(), {}
    frames = []
    for member, ch in zip(request.members, children, strict=True):
        if ch.sources.request != _child_request(request, member):
            _fail("CANDIDATE_BINDING_MISMATCH", "Child differs from deterministic member request")
        _participants(request, ch.sources.projection)
        row = _chosen(ch, request.target)
        projection = _integrity_projection(ch, row)
        digest = c.shared_tastefit_hash("shared-target.integrity.v1", projection)
        if reference is not None and digest != reference:
            _fail("SOURCE_CUT_INCOHERENT", "Complete candidate/classification/target cuts differ")
        reference = digest
        rows.append(row)
        s = ch.sources
        if (
            not source.capture_started_at
            <= s.capture_started_at
            <= s.capture_completed_at
            <= (source.capture_completed_at)
        ):
            _fail("SOURCE_CUT_INCOHERENT", "Child outside outer capture interval")
        owner_frames = (s.candidate_frame,) + s.member_sources.frames
        frames.append((member.member_id, owner_frames))
        for f in owner_frames:
            endpoints.add(
                (
                    f.configured_host,
                    f.configured_port,
                    f.database_name,
                    f.database_oid,
                    f.server_address,
                    f.server_port,
                )
            )
            actors.add(f.actor_user_id)
            owner = "MEMBER" if f.owner == "CANDIDATE" else f.owner
            if owner in readers and readers[owner] != f.session_user:
                _fail("SOURCE_CUT_INCOHERENT", "Owner session principal changed across cohort")
            readers[owner] = f.session_user
    if len(endpoints) != 1 or len(actors) != 1 or tuple(frames) != source.owner_frames:
        _fail("SOURCE_CUT_INCOHERENT", "Actual endpoint/actor/retained owner frames differ")
    _owner_identities(children)
    g = request.projection_request.grounding_request
    context = c.shared_tastefit_hash(
        "shared-target.participants.v1",
        dict(participants=g.participants, tracked_member_id=g.tracked_member_id),
    )
    proof = c.SharedTasteFitCohortProof(
        household_id=request.household_id,
        binding=children[0].subject.binding,
        target=request.target,
        participants=g.participants,
        tracked_member_id=g.tracked_member_id,
        participant_context_fingerprint=context,
        integrity_projection_fingerprint=reference,
        child_identities=tuple(
            (
                ch.subject.member_id,
                ch.fingerprint,
                ch.sources.fingerprint,
                ch.sources.projection.fingerprint,
            )
            for ch in children
        ),
    )
    return proof, tuple(rows)


def _diagnose(request, ch, row):
    p = request.policy
    admitted = any(a.policy == ch.sources.request.policy for a in p.policy_admissions)
    reasons, rule = set(), None
    eligible = row.proof.role == "BASE" and row.proof.candidate_state == "PRESENT"
    if not eligible:
        reasons.add(
            "CANDIDATE_TARGET_ABSENT"
            if row.proof.candidate_state == "ABSENT"
            else "CANDIDATE_TARGET_UNRESOLVED"
        )
    if row.reason:
        reasons.add(row.reason)
    if row.source_reason:
        reasons.add(row.source_reason)
    if row.status == "SUPPRESSED":
        reasons.update(("MEMBER_RETRACTED", "SUPPRESSED"))
    elif row.status != "AVAILABLE":
        reasons.add(
            "CHILD_FIT_UNMAPPED" if row.source_amount is not None else "CHILD_FIT_UNAVAILABLE"
        )
    if not admitted:
        reasons.add("POLICY_INCOMPATIBLE")
        status = "INCOMPATIBLE"
    elif not eligible or row.status != "AVAILABLE":
        status = "NOT_EVALUABLE"
    else:
        rule = next(
            (
                r
                for r in p.bridge_rules
                if r.admission.policy == ch.sources.request.policy
                and r.target_kind == request.target.kind
                and r.mapping == row.mapping
                and r.direct_signal == row.direct_signal
            ),
            None,
        )
        status = "COMPATIBLE" if rule else "INCOMPATIBLE"
        if rule is None:
            reasons.add("BRIDGE_RULE_NOT_FOUND")
    return c.SharedTasteFitMemberDiagnostic(
        member_id=ch.subject.member_id,
        child_fingerprint=ch.fingerprint,
        row=row,
        compatibility=status,
        reasons=tuple(sorted(reasons)),
    ), rule


def _integer(value, limit):
    if abs(value).bit_length() > limit:
        _fail("RESOURCE_LIMIT", "Arithmetic integer budget exceeded")
    return value


def _multiply_int(a, b, limit):
    # Prove the product fits *before* creating a potentially oversized integer.
    if a and b and abs(a).bit_length() + abs(b).bit_length() > limit:
        if abs(a) > ((1 << limit) - 1) // abs(b):
            _fail("RESOURCE_LIMIT", "Arithmetic product budget exceeded")
    return _integer(a * b, limit)


def _multiply(a, b, limit):
    g1, g2 = gcd(a.numerator, b.denominator), gcd(b.numerator, a.denominator)
    return Fraction(
        _multiply_int(a.numerator // g1, b.numerator // g2, limit),
        _multiply_int(a.denominator // g2, b.denominator // g1, limit),
    )


def _add(a, b, limit):
    divisor = gcd(a.denominator, b.denominator)
    left = _multiply_int(a.numerator, b.denominator // divisor, limit)
    right = _multiply_int(b.numerator, a.denominator // divisor, limit)
    # Only materialize the carry threshold when the actual operands can reach
    # that budget. A huge authored limit with tiny operands must stay cheap.
    if (
        left
        and right
        and (left > 0) == (right > 0)
        and max(abs(left).bit_length(), abs(right).bit_length()) + 1 > limit
    ):
        if abs(left) > ((1 << limit) - 1) - abs(right):
            _fail("RESOURCE_LIMIT", "Arithmetic sum budget exceeded")
    numerator = _integer(left + right, limit)
    denominator = _multiply_int(a.denominator, b.denominator // divisor, limit)
    return Fraction(numerator, denominator)


def _trace(value, coordinate, unit):
    return c.SharedTasteFitRationalTrace(
        numerator=value.numerator, denominator=value.denominator, coordinate=coordinate, unit=unit
    )


def _reduce(coordinate, contributions, policy):
    """Private scoped reducer: descriptor/member gates precede its first arithmetic."""
    coordinate = c.SharedMemberTargetTasteFitCoordinate.model_validate(coordinate)
    policy = c.SharedMemberTargetTasteFitPolicy.model_validate(policy)
    contributions = tuple(
        c.SharedTasteFitMemberContribution.model_validate(v) for v in contributions
    )
    if (
        tuple(v.diagnostic.member_id for v in contributions)
        != tuple(w.member_id for w in policy.member_weights)
        or coordinate.aggregation_policy_fingerprint != policy.fingerprint()
    ):
        _fail("DESCRIPTOR_MISMATCH", "Exact policy/member-weight identity required")
    for v, weight in zip(contributions, policy.member_weights, strict=True):
        row, rule, operand = v.diagnostic.row, v.selected_bridge, v.common_operand
        if (
            v.diagnostic.compatibility != "COMPATIBLE"
            or operand is None
            or rule is None
            or operand.coordinate != coordinate
            or v.authored_weight != weight
            or v.original_value != row.value
            or row.value is None
            or row.value.coordinate.member_id != weight.member_id
            or row.value.coordinate.household_id != coordinate.household_id
            or row.value.coordinate.target != coordinate.target
            or row.value.coordinate.grounding_fingerprint != coordinate.grounding_fingerprint
            or rule not in policy.bridge_rules
            or rule.mapping != row.mapping
            or rule.direct_signal != row.direct_signal
            or rule.admission.expected_policy_fingerprint != row.value.coordinate.policy_fingerprint
            or operand.amount != rule.mapped_amount
        ):
            _fail(
                "DESCRIPTOR_MISMATCH",
                "Complete original/common operands required before arithmetic",
            )
    limit = policy.max_integer_bits
    weight_total, weighted_total, values = Fraction(0), Fraction(0), []
    for v in contributions:
        w, b = v.authored_weight.weight, v.common_operand.amount
        weight = Fraction(w.numerator, w.denominator)
        product = _multiply(weight, Fraction(b.numerator, b.denominator), limit)
        weight_total = _add(weight_total, weight, limit)
        weighted_total = _add(weighted_total, product, limit)
        values.append(
            v.model_copy(
                update=dict(
                    weighted_contribution=_trace(
                        product, coordinate, "MEMBER_INFLUENCE_X_SHARED_TARGET_FIT"
                    )
                )
            )
        )
    if weight_total <= 0:
        _fail("DESCRIPTOR_MISMATCH", "Complete nonempty positive weight set required")
    final = _multiply(
        weighted_total, Fraction(weight_total.denominator, weight_total.numerator), limit
    )
    value = c.ScopedSharedMemberTargetTasteFit(
        coordinate=coordinate, amount=dict(numerator=final.numerator, denominator=final.denominator)
    )
    return (
        tuple(values),
        value,
        _trace(weight_total, coordinate, "MEMBER_INFLUENCE"),
        _trace(weighted_total, coordinate, "MEMBER_INFLUENCE_X_SHARED_TARGET_FIT"),
    )


def derive_shared_member_target_tastefit(sources):
    try:
        raw = _budget(sources, "source")
        request = _parse_request(raw.get("request"))
        # Recompute every FULL frozen child before cohort selection or new arithmetic.
        children = tuple(validate_candidate_member_tastefit(ch) for ch in raw.get("children", ()))
        source = c.SharedMemberTargetTasteFitSources.model_validate(raw)
        if source.fingerprint != source.expected_fingerprint():
            _fail("REPLAY_MISMATCH", "Complete retained cohort fingerprint differs")
        if source.children != tuple(sorted(children, key=lambda ch: str(ch.subject.member_id))):
            _fail("REPLAY_MISMATCH", "Full child semantics differ from frozen replay")
        # Bind subsequent work to the freshly recomputed children, after comparing
        # every supplied semantic field. Cached input objects never become operands.
        source = source.model_copy(
            update=dict(
                request=request,
                children=tuple(sorted(children, key=lambda ch: str(ch.subject.member_id))),
            )
        )
        proof, rows = _coherence(source)
        coordinate = c.SharedMemberTargetTasteFitCoordinate(
            household_id=request.household_id,
            binding=proof.binding,
            grounding_fingerprint=proof.binding.grounding_fingerprint,
            target=request.target,
            participant_context_fingerprint=proof.participant_context_fingerprint,
            aggregation_policy_fingerprint=request.policy.fingerprint(),
            retained_cohort_fingerprint=source.fingerprint,
        )
        contributions, diagnostics, signals = [], [], []
        for ch, row, weight in zip(
            source.children, rows, request.policy.member_weights, strict=True
        ):
            diagnostic, rule = _diagnose(request, ch, row)
            diagnostics.append(diagnostic)
            contributions.append(
                c.SharedTasteFitMemberContribution(
                    diagnostic=diagnostic,
                    selected_bridge=rule,
                    original_value=row.value,
                    authored_weight=weight,
                    common_operand=None,
                    weighted_contribution=None,
                )
            )
            signals.append(
                c.SharedTasteFitDirectSignalTrace(
                    member_id=ch.subject.member_id,
                    target=request.target,
                    direct_signal=row.direct_signal,
                    declaration_id=row.declaration_id,
                    child_fingerprint=ch.fingerprint,
                    row=row,
                )
            )
        required = tuple(m.member_id for m in request.members)
        available = tuple(
            d.member_id
            for d in diagnostics
            if d.row.status == "AVAILABLE"
            and d.row.proof.role == "BASE"
            and d.row.proof.candidate_state == "PRESENT"
        )
        compatible = tuple(d.member_id for d in diagnostics if d.compatibility == "COMPATIBLE")
        complete = required == available == compatible
        statuses = {d.compatibility for d in diagnostics}
        compatibility = (
            "INCOMPATIBLE"
            if "INCOMPATIBLE" in statuses
            else "NOT_EVALUABLE"
            if "NOT_EVALUABLE" in statuses
            else "COMPATIBLE"
        )
        reasons = {r for d in diagnostics for r in d.reasons}
        if not complete:
            reasons.add("PARTICIPANT_COVERAGE_INCOMPLETE")
        value = weight_total = weighted_total = None
        if complete:
            contributions = [
                v.model_copy(
                    update=dict(
                        common_operand=(
                            c.ScopedSharedMemberTargetTasteFit(
                                coordinate=coordinate, amount=v.selected_bridge.mapped_amount
                            )
                        )
                    )
                )
                for v in contributions
            ]
            contributions, value, weight_total, weighted_total = _reduce(
                coordinate, contributions, request.policy
            )
        fields = dict(
            sources=source,
            cohort=proof,
            coordinate=coordinate,
            contributions=tuple(contributions),
            direct_signals=tuple(signals),
            direct_dislikes=tuple(s for s in signals if s.direct_signal == "DECLARED_DISLIKE"),
            compatibility=c.SharedTasteFitCompatibilityDecision(
                status=compatibility,
                members=tuple(diagnostics),
                compatible_member_ids=compatible,
                reasons=tuple(sorted(reasons)),
            ),
            coverage=c.SharedTasteFitCoverage(
                numeric_coverage="COMPLETE" if complete else "INCOMPLETE",
                required_member_ids=required,
                captured_member_ids=required,
                available_member_ids=available,
                compatible_member_ids=compatible,
                required_count=len(required),
                captured_count=len(required),
                available_count=len(available),
                compatible_count=len(compatible),
            ),
            aggregate_availability="AVAILABLE" if complete else "UNAVAILABLE",
            reasons=tuple(sorted(reasons)),
            value=value,
            weight_total=weight_total,
            weighted_total=weighted_total,
        )
        temporary = c.SharedMemberTargetTasteFitDraft.model_construct(
            **fields, fingerprint="0" * 64
        )
        result = c.SharedMemberTargetTasteFitDraft(
            **fields, fingerprint=temporary.expected_fingerprint()
        )
        _budget(result, "result")
        return result
    except ResolutionError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
        _fail("REPLAY_MISMATCH", str(exc))


def validate_shared_member_target_tastefit(result):
    try:
        raw = _budget(result, "result")
        expected = derive_shared_member_target_tastefit(raw.get("sources"))
        parsed = c.SharedMemberTargetTasteFitDraft.model_validate(raw)
        if parsed != expected:
            _fail(
                "REPLAY_MISMATCH", "Complete shared-target semantics differ from primitive replay"
            )
        return expected
    except ResolutionError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        _fail("REPLAY_MISMATCH", str(exc))
