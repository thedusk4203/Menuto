"""Pure TEST_ONLY source-bound integration. Offline consistency is not source origin."""

from fractions import Fraction

from app.domain.feature_identity import canonical, canonical_bytes
from app.modules.nutrition import policy_v2_contracts as v
from app.modules.nutrition.basis_applicability import resolve_basis_applicability
from app.modules.nutrition.policy_v2_limits import RESULT_BYTES, PolicyWork
from app.modules.nutrition.policy_v2_rules import (
    _calendar,
    _case,
    _coverage,
    _evaluate,
    _period_consistency,
    _PolicyFailure,
)
from app.modules.nutrition.resolution_contracts import resolution_hash
from app.modules.nutrition.root_public import validate_nutrition_root
from app.modules.nutrition.synthesis import nutrition_policy_requirements
from app.modules.nutrition.synthesis_journal import replay_synthesis_sources


class _Failure(ValueError):
    def __init__(
        self, outcome, code, stage, child=None, hard="NOT_EVALUATED", soft="NOT_EVALUATED"
    ):
        self.outcome, self.code, self.stage = outcome, code, stage
        self.child, self.hard, self.soft = child, hard, soft


def _require(ok, code, stage="IDENTITY", outcome="REJECTED"):
    if not ok:
        raise _Failure(outcome, code, stage)


def _identity(s):
    ns, a = s.nre.sources, s.artifact
    ss, q = ns.synthesis_sources, ns.scope
    root, req = ss.request.root, ns.requirements
    _require(
        ss.precision_witness is not None, "PRECISION_UNAUTHORIZED", "SOURCE", "SOURCE_UNAVAILABLE"
    )
    _require(ss.request.precision == q.precision, "PRECISION_IDENTITY_MISMATCH")
    rules = [
        x.command.body.rule
        for x in ss.records
        if x.command.body.kind == "DRAFT"
        and x.command.body.rule.revision_id == q.selection.revision_id
    ]
    _require(len(rules) == 1, "SOURCE_MISSING", "SOURCE", "SOURCE_UNAVAILABLE")
    return v.PolicyIntegrationIdentityV2(
        subject=q.subject,
        actor_user_id=q.actor_user_id,
        root_request=q.root_request,
        root_source_fingerprint=root.source_fingerprint,
        root_result_fingerprint=root.result_fingerprint,
        rule_selection=q.selection,
        rule_case_id=req.case_id,
        requirement_fingerprint=req.fingerprint,
        nre_scope_fingerprint=resolution_hash("scope", q),
        precision=q.precision,
        precision_witness=ss.precision_witness,
        horizon=q.root_request.temporal,
        calendar_cells=rules[0].calendar_cells,
        nre_source_fingerprint=ns.source_fingerprint,
        nre_result_fingerprint=s.nre.estimate.result_fingerprint,
        anchor_manifest_fingerprint=v.policy_v2_hash("anchors", s.anchors),
        original_meaning_manifest_fingerprint=v.policy_v2_hash(
            "meanings",
            tuple(
                (x.key, x.original_source_fingerprint, x.evidence_fingerprint, x.meaning_preimage)
                for x in s.anchors
            ),
        ),
        registry_id=a.registry_id,
        registry_revision=a.revision,
        issuer_epoch=a.issuer_epoch,
        deployment=a.deployment,
        database_oid=a.database_oid,
        database_name=a.database_name,
        basis_source_fingerprint=s.source_fingerprint,
        environment="TEST_ONLY",
    )


def _child_failure(result):
    state, reason = result.outcome, next(iter(result.reasons), None)
    if state == "APPLICABLE_TEST_ONLY" and not result.reasons:
        return
    if state == "RESOURCE_EXCEEDED":
        outcome, code = "RESOURCE_EXCEEDED", "RESOURCE_LIMIT"
    elif state == "REJECTED":
        outcome, code = (
            "REJECTED",
            {
                "NRE_RESULT_FORGED": "NRE_INCONSISTENT",
                "ENVIRONMENT_MISMATCH": "ENVIRONMENT_MISMATCH",
            }.get(reason, "MBA_INCONSISTENT"),
        )
    elif state == "UNAVAILABLE":
        outcome = "SOURCE_UNAVAILABLE"
        code = {
            "PUBLICATION_WITHDRAWN": "SOURCE_WITHDRAWN",
            "PUBLICATION_RETIRED": "SOURCE_WITHDRAWN",
            "PUBLICATION_MISSING": "MBA_UNAVAILABLE",
            "MEANING_MISSING": "MBA_UNAVAILABLE",
            "REQUIRED_ANCHOR_MISSING": "ANCHOR_COVERAGE_MISSING",
            "TEMPORAL_COVERAGE_MISSING": "PERIOD_COVERAGE_MISSING",
            "NRE_UNAVAILABLE": "NRE_UNAVAILABLE",
        }.get(reason, "SOURCE_UNAUTHORIZED")
    elif state == "NOT_APPLICABLE":
        outcome = "UNSUPPORTED"
        code = (
            "UNIT_OR_SCOPE_MISMATCH"
            if reason in {"MATERIAL_BASIS_MISMATCH", "POPULATION_SCOPE_MISMATCH"}
            else "MBA_NOT_APPLICABLE"
        )
    elif state == "UNSUPPORTED":
        outcome = "UNSUPPORTED"
        code = (
            "MEANING_MISMATCH"
            if reason in {"CONVERSION_NOT_SUPPORTED", "MEANING_VERSION"}
            else "UNSUPPORTED_TEMPORAL_MAP"
            if reason in {"CROSS_VERSION_INTERVAL", "UNSUPPORTED_LINEAGE"}
            else "UNIT_OR_SCOPE_MISMATCH"
        )
    else:
        outcome, code = "REJECTED", "MBA_INCONSISTENT"
    raise _Failure(outcome, code, "NRE" if code.startswith("NRE_") else "MBA", result)


def _joint(root, claims, estimate, work):
    horizon = root.sources.request.temporal
    periods = sorted(estimate.periods, key=lambda p: canonical_bytes(p.temporal))
    hp = [p for p in periods if p.temporal == horizon]
    _require(len(hp) == 1, "PERIOD_COVERAGE_MISSING", "JOINT", "SOURCE_UNAVAILABLE")
    hp = hp[0]
    configs = {x.configuration_id: x for x in estimate.configurations}
    slots = tuple(sorted({x.serving.slot_id for x in configs.values()}))
    _require(hp.slot_ids == slots, "JOINT_WITNESS_MISMATCH", "JOINT")
    witness_count = sum(len(vec.configurations) for p in periods for vec in p.vectors)
    _require(witness_count <= 65536, "RESOURCE_LIMIT", "JOINT", "RESOURCE_EXCEEDED")
    work.charge(witness_count)
    tables = {}
    for p in periods:
        table = {}
        for vector in p.vectors:
            for ids in vector.configurations:
                _require(ids not in table, "JOINT_WITNESS_MISMATCH", "JOINT")
                table[ids] = vector
        tables[canonical_bytes(p.temporal)] = table
    hard = [
        ("root:" + r.clause.root_key, r.clause.descriptor, r.clause.constraint)
        for r in root.roots
        if r.clause.interpretation == "GUIDELINE_HARD"
    ]
    hard.extend(
        (x.id, x.descriptor, x.constraint)
        for x in claims
        if x.layer in {"GOAL_PROTECTION", "DAILY_PROTECTION", "WEEKLY_GOAL"}
    )
    comfort = [(x.id, x.descriptor, x.constraint) for x in claims if x.layer == "COMFORT"]
    centers = [x for x in claims if x.layer == "WEEKLY_CENTER"]
    assignments, protected, supported, deltas = [], [], [], []
    representative = None
    ids_in_horizon = sorted(ids for vector in hp.vectors for ids in vector.configurations)
    _require(1 <= len(ids_in_horizon) <= 16384, "RESOURCE_LIMIT", "JOINT", "RESOURCE_EXCEEDED")
    for ids in ids_in_horizon:
        work.charge(len(periods) + len(hard) + len(comfort) + len(centers))
        mapping = dict(zip(slots, ids, strict=True))
        vectors, hashes = {}, []
        for p in periods:
            subset_ids = tuple(mapping[k] for k in p.slot_ids)
            vector = tables[canonical_bytes(p.temporal)].get(subset_ids)
            _require(vector is not None, "JOINT_WITNESS_MISMATCH", "JOINT")
            for slot, cid in zip(p.slot_ids, subset_ids, strict=True):
                _require(
                    cid in configs and configs[cid].serving.slot_id == slot,
                    "JOINT_WITNESS_MISMATCH",
                    "JOINT",
                )
            totals = []
            for j in range(4):
                total = Fraction()
                for cid in subset_ids:
                    amount = configs[cid].nutrients[j]
                    total = work.add(total, Fraction(amount.numerator, amount.denominator))
                totals.append(work.number(total))
            totals = tuple(totals)
            _require(
                totals == tuple(Fraction(x.numerator, x.denominator) for x in vector.nutrients),
                "JOINT_WITNESS_MISMATCH",
                "JOINT",
            )
            vectors[canonical_bytes(p.temporal)] = totals
            hashes.append(
                v.policy_v2_hash(
                    "vector", dict(temporal=p.temporal, slot_ids=p.slot_ids, vector=vector)
                )
            )

        def value(desc):
            row = vectors.get(canonical_bytes(desc.temporal))
            _require(row is not None, "PERIOD_COVERAGE_MISSING", "JOINT", "SOURCE_UNAVAILABLE")
            return work.number(row[("ENERGY", "PROTEIN", "FAT", "CARBOHYDRATE").index(desc.metric)])

        def violated(rows):
            bad = []
            for key, desc, clause in rows:
                x = value(desc)
                if (
                    hasattr(clause, "lower")
                    and x < Fraction(clause.lower.numerator, clause.lower.denominator)
                ) or (
                    hasattr(clause, "upper")
                    and x > Fraction(clause.upper.numerator, clause.upper.denominator)
                ):
                    bad.append(key)
            return tuple(sorted(bad))

        aid = v.policy_v2_hash("assignment", dict(slot_ids=slots, configuration_ids=ids))
        hv, cv = violated(hard), violated(comfort)
        assignments.append(
            v.PolicyAssignmentEvaluationV2(
                assignment_fingerprint=aid,
                configuration_ids=ids,
                period_vector_fingerprints=tuple(hashes),
                hard_violations=hv,
                comfort_violations=cv,
                environment="TEST_ONLY",
            )
        )
        if not hv:
            protected.append(aid)
            if not cv:
                supported.append(aid)
                if representative is None:
                    representative = aid
        for center in centers:
            _require(len(deltas) < 65536, "RESOURCE_LIMIT", "JOINT", "RESOURCE_EXCEEDED")
            delta = work.number(
                work.add(
                    value(center.descriptor),
                    -Fraction(
                        center.constraint.center.numerator, center.constraint.center.denominator
                    ),
                )
            )
            deltas.append(
                v.PolicyCenterDeltaV2(
                    assignment_fingerprint=aid,
                    claim_id=center.id,
                    descriptor=center.descriptor,
                    amount_minus_center=dict(
                        numerator=delta.numerator, denominator=delta.denominator
                    ),
                    environment="TEST_ONLY",
                )
            )
    if not protected:
        raise _Failure(
            "RESOLUTION_INSUFFICIENT",
            "NO_PROTECTED_JOINT_WITNESS",
            "JOINT",
            hard="ABSENT_IN_DECLARED_UNIVERSE",
        )
    if not supported:
        raise _Failure(
            "RESOLUTION_INSUFFICIENT",
            "NO_JOINT_COMFORT_SUPPORT",
            "JOINT",
            hard="PRESENT",
            soft="SOFT_UNSUPPORTED",
        )
    data = dict(
        slot_ids=slots,
        assignments=tuple(assignments),
        protected_assignment_ids=tuple(sorted(protected)),
        comfort_assignment_ids=tuple(sorted(supported)),
        representative_comfort_assignment_id=representative,
        center_deltas=tuple(sorted(deltas, key=lambda x: (x.assignment_fingerprint, x.claim_id))),
        environment="TEST_ONLY",
    )
    return v.JointPolicySupportV2(**data, support_fingerprint=v.policy_v2_hash("support", data))


def _body(i, work):
    s = i.basis_sources
    expected = _identity(s)
    _require(
        i.identity.precision == expected.precision
        and i.identity.precision_witness == expected.precision_witness,
        "PRECISION_IDENTITY_MISMATCH",
    )
    _require(i.identity == expected, "SOURCE_IDENTITY_MISMATCH")
    _require(
        i.source_fingerprint
        == v.policy_v2_hash(
            "input", {k: val for k, val in canonical(i).items() if k != "source_fingerprint"}
        ),
        "SOURCE_IDENTITY_MISMATCH",
    )
    ss = s.nre.sources.synthesis_sources
    root = validate_nutrition_root(ss.request.root)
    _require(
        root.goal_state == "PRESENT", "GOAL_SOURCE_UNAVAILABLE", "SOURCE", "SOURCE_UNAVAILABLE"
    )
    _require(root.availability == "AVAILABLE", "SOURCE_MISSING", "SOURCE", "SOURCE_UNAVAILABLE")
    try:
        sources, rule, reason = replay_synthesis_sources(ss)
    except ValueError as exc:
        if str(exc) == "Retained exact capability unavailable":
            raise _Failure("SOURCE_UNAVAILABLE", "SOURCE_UNAUTHORIZED", "SOURCE") from exc
        raise
    _require(
        not reason,
        "SOURCE_WITHDRAWN" if reason == "RULE_WITHDRAWN" else "SOURCE_UNAUTHORIZED",
        "SOURCE",
        "SOURCE_UNAVAILABLE",
    )
    _require(
        nutrition_policy_requirements(sources) == s.nre.sources.requirements,
        "REQUIREMENT_COVERAGE_MISSING",
    )
    case = _case(root, rule)
    keys = [a.key for a in s.anchors]
    expected_keys = {"root:" + x.clause.root_key for x in root.roots} | {
        "rule:" + case.id + ":" + op.id for op in case.operations if op.kind == "MAKE_CONSTRAINT"
    }
    _require(len(keys) == len(set(keys)) and set(keys) <= expected_keys, "MBA_INCONSISTENT", "MBA")
    _require(
        set(keys) == expected_keys, "ANCHOR_COVERAGE_MISSING", "COVERAGE", "SOURCE_UNAVAILABLE"
    )
    _require(
        root.sources.request.temporal.kind in {"DAY", "WEEK"},
        "UNSUPPORTED_TEMPORAL_MAP",
        "RULE",
        "UNSUPPORTED",
    )
    child = resolve_basis_applicability(s)
    _child_failure(child)
    _calendar(rule)
    claims, trace = _evaluate(root, rule, case, ss.request.precision, work)
    _coverage(root, rule, case, claims, trace)
    _period_consistency(root, rule, case, claims, trace)
    active = {x.id for x in claims}
    witnesses = {x.anchor_fingerprint: x for x in child.witnesses}
    coverage = []
    for anchor in s.anchors:
        work.charge()
        op_id = None if anchor.key.startswith("root:") else anchor.key.rsplit(":", 1)[1]
        witness = witnesses.get(anchor.anchor_fingerprint)
        _require(witness is not None, "ANCHOR_COVERAGE_MISSING", "COVERAGE", "SOURCE_UNAVAILABLE")
        coverage.append(
            v.PolicyClaimCoverageV2(
                anchor_key=anchor.key,
                anchor_fingerprint=anchor.anchor_fingerprint,
                root_key=anchor.root_key,
                operation_id=op_id,
                descriptor=anchor.descriptor,
                layer=anchor.layer,
                disposition=(
                    "RETAINED_ROOT"
                    if op_id is None
                    else "ACTIVE_CLAIM"
                    if op_id in active
                    else "UNSELECTED_PRECISION_BRANCH"
                ),
                claim_id=op_id,
                meaning_fingerprint=witness.original_meaning_fingerprint,
                basis_witness_fingerprint=v.policy_v2_hash("check", witness),
                environment="TEST_ONLY",
            )
        )
    return v.NutritionPolicyBodyV2(
        retained_roots=root.roots,
        claims=claims,
        trace=trace,
        coverage=tuple(coverage),
        requirements=s.nre.sources.requirements,
        reconstructed_basis_result=child,
        support=_joint(root, claims, s.nre.estimate, work),
        environment="TEST_ONLY",
    )


def derive_policy_v2(retained_input):
    i = v.parse_policy_v2(retained_input, v.NutritionPolicyIntegrationInputV2)
    work, payload, diagnostics, outcome = PolicyWork(), None, (), "AVAILABLE_TEST_ONLY"
    work.reserve_control()
    try:
        work.tree(canonical(i))
        payload = _body(i, work)
    except _PolicyFailure as exc:
        code = {
            "PRECISION_NESTING_FAILED": "PRECISION_NESTING_FAILED",
            "REVIEWED_GOAL_DIRECTION_RELATION_FAILED": "GOAL_DIRECTION_CONFLICT",
            "DAILY_PROTECTION_AUTHORITY_MISSING": "DAILY_PROTECTION_MISSING",
            "EMPTY_PROTECTED_INTERVAL": "PROTECTED_INTERVAL_CONFLICT",
            "DAILY_AGGREGATE_INTERVAL_CONFLICT": "PROTECTED_INTERVAL_CONFLICT",
            "COUPLED_DAILY_WEEKLY_INTERVAL_CONFLICT": "PROTECTED_INTERVAL_CONFLICT",
        }.get(
            exc.reason,
            "HARD_CONTAINMENT_FAILED"
            if exc.state == "CONFLICT"
            else "UNSUPPORTED_TEMPORAL_MAP"
            if exc.state == "UNSUPPORTED"
            else "CLAIM_COVERAGE_MISSING",
        )
        outcome = {
            "CONFLICT": "POLICY_CONFLICT",
            "UNSUPPORTED": "UNSUPPORTED",
            "UNAVAILABLE": "SOURCE_UNAVAILABLE",
        }.get(exc.state, "REJECTED")
        diagnostics = (_diagnostic(_Failure(outcome, code, "RULE")),)
    except _Failure as exc:
        outcome, diagnostics = exc.outcome, (_diagnostic(exc),)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, ArithmeticError) as exc:
        outcome = "RESOURCE_EXCEEDED" if str(exc).startswith("RESOURCE_EXCEEDED") else "REJECTED"
        diagnostics = (
            _diagnostic(
                _Failure(
                    outcome,
                    "RESOURCE_LIMIT" if outcome == "RESOURCE_EXCEEDED" else "SOURCE_MALFORMED",
                    "SOURCE",
                )
            ),
        )
    data = dict(
        contract_version="nutrition-policy.v2",
        input_fingerprint=i.source_fingerprint,
        identity_fingerprint=v.policy_v2_hash("identity", i.identity),
        outcome=outcome,
        diagnostics=diagnostics,
        payload=payload,
        environment="TEST_ONLY",
        validation_authority="UNVERIFIED_TRANSPORT",
        scientific_correctness="NOT_CERTIFIED",
        source_origin="NOT_PROVED_OFFLINE",
        current_authorization="NOT_CLAIMED",
        production_admission="CLOSED",
        plan_validation="NOT_PERFORMED",
        solver_infeasibility="NOT_PROVEN",
        planner_ready=False,
        activation_ready=False,
    )
    try:
        result = v.NutritionPolicyResultV2(
            **data, result_fingerprint=v.policy_v2_hash("result", data)
        )
        work.output(result, RESULT_BYTES)
    except ValueError as exc:
        if not str(exc).startswith("RESOURCE_EXCEEDED"):
            raise
        data.update(
            payload=None,
            outcome="RESOURCE_EXCEEDED",
            diagnostics=(_diagnostic(_Failure("RESOURCE_EXCEEDED", "RESOURCE_LIMIT", "SOURCE")),),
        )
        result = v.NutritionPolicyResultV2(
            **data, result_fingerprint=v.policy_v2_hash("result", data)
        )
        work.failure_output(result, RESULT_BYTES)
    return result


def _diagnostic(exc):
    return v.PolicyDiagnosticV2(
        stage=exc.stage,
        code=exc.code,
        subject_path=None,
        child_outcome=exc.child.outcome if exc.child else None,
        child_reason=next(iter(exc.child.reasons), None) if exc.child else None,
        hard_support=exc.hard,
        soft_support=exc.soft,
        environment="TEST_ONLY",
    )
