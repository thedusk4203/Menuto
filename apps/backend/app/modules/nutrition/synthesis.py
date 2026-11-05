"""Finite exact source-bound policy derivation. This module performs no I/O."""

import json
from dataclasses import dataclass
from fractions import Fraction

from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition import root_public
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.synthesis_journal import digest, replay_synthesis_sources, require


def ratio(value):
    return Fraction(value.numerator, value.denominator)


def rational(value):
    return c.SynthesisRational(numerator=value.numerator, denominator=value.denominator)


def amount(value):
    return n.NutritionRootAmount(numerator=value.numerator, denominator=value.denominator)


def endpoints(constraint):
    return (
        ratio(constraint.lower) if hasattr(constraint, "lower") else None,
        ratio(constraint.upper) if hasattr(constraint, "upper") else None,
    )


def subset(inner, outer):
    il, iu = endpoints(inner)
    ol, ou = endpoints(outer)
    if inner.kind == "TARGET":
        il = iu = ratio(inner.center)
    if outer.kind == "TARGET":
        return inner.kind == "TARGET" and inner.center == outer.center
    return (ol is None or (il is not None and il >= ol)) and (
        ou is None or (iu is not None and iu <= ou)
    )


def same_measure(a, b):
    return canonical(a) | {"temporal": None} == canonical(b) | {"temporal": None}


@dataclass(frozen=True)
class _Value:
    descriptor: n.NutritionRootDescriptor
    root_key: str
    number: Fraction | None = None
    claim: c.NutritionPolicyClaim | None = None


class _PolicyFailure(ValueError):
    def __init__(self, state, reason):
        self.state, self.reason = state, reason


def _fail(ok, state, reason):
    if not ok:
        raise _PolicyFailure(state, reason)


def _calendar(rule):
    span = rule.applicability.temporal
    next_start = span.interval.start
    for cell in rule.calendar_cells:
        _fail(
            cell.interval.start == next_start
            and cell.calendar == span.calendar
            and cell.timezone == span.timezone,
            "UNSUPPORTED",
            "CALENDAR_MAPPING_UNSUPPORTED",
        )
        next_start = cell.interval.end
    _fail(next_start == span.interval.end, "UNSUPPORTED", "CALENDAR_COVERAGE_INCOMPLETE")
    if span.kind == "DAY":
        _fail(rule.calendar_cells == (span,), "UNSUPPORTED", "DAY_ROOT_OUTSIDE_COVERED_FRAME")


def _case(root, rule):
    matches = [case for case in rule.cases if case.direction == root.goal_direction]
    _fail(
        len(matches) == 1,
        "CONFLICT" if matches else "UNAVAILABLE",
        "RULE_CASE_MISSING" if not matches else "RULE_CASE_AMBIGUOUS",
    )
    return matches[0]


def _requirements(sources, rule, case):
    root = sources.request.root
    clauses = {r.clause.root_key: r.clause for r in root.roots}
    measurements = {}
    for op in case.operations:
        if op.kind == "MAKE_CONSTRAINT" and op.layer == "COMFORT":
            _fail(
                op.root_key in clauses and op.root_key in case.comfort_root_keys,
                "UNAVAILABLE",
                "COMFORT_MANIFEST_MISMATCH",
            )
            descriptor = n.NutritionRootDescriptor.model_validate(
                canonical(clauses[op.root_key].descriptor) | {"temporal": canonical(op.temporal)}
            )
            measurement = c.NutritionResolutionRequirement(
                root_key=op.root_key, descriptor=descriptor
            )
            measurements[digest("measurement", measurement)] = measurement
    _fail(bool(measurements), "UNAVAILABLE", "COMFORT_COVERAGE_MISSING")
    data = dict(
        subject=root.sources.request.subject,
        root_fingerprint=root.result_fingerprint,
        rule_body_fingerprint=digest("rule", rule),
        case_id=case.id,
        temporal=root.sources.request.temporal,
        root_keys=case.comfort_root_keys,
        measurements=tuple(value for key, value in sorted(measurements.items())),
        environment=root.sources.request.environment,
    )
    return c.NutritionPolicyRequirementSpec(**data, fingerprint=digest("requirements", data))


def nutrition_policy_requirements(value):
    sources, rule, reason = replay_synthesis_sources(value)
    root = root_public.validate_nutrition_root(sources.request.root)
    if (
        reason
        or root.availability != "AVAILABLE"
        or root.eligibility != "SUPPORTED"
        or root.goal_state != "PRESENT"
    ):
        raise ValueError(reason or "Complete supported root/goal required")
    return _requirements(sources, rule, _case(root, rule))


def _evaluate(root, rule, case, precision):
    clauses = {r.clause.root_key: r.clause for r in root.roots}
    values, traces = {}, []
    selected, direction_checked = set(), set()
    subject = root.sources.request.subject
    for op in case.operations:
        operands = [values[key] for key in op.inputs]
        result, passed = None, None
        if op.kind == "COPY_REFERENCE":
            clause = clauses.get(op.root_key)
            _fail(
                clause is not None and hasattr(clause.constraint, op.endpoint),
                "UNAVAILABLE",
                "REVIEWED_REFERENCE_ENDPOINT_UNAVAILABLE",
            )
            result = _Value(
                clause.descriptor, op.root_key, ratio(getattr(clause.constraint, op.endpoint))
            )
        elif op.kind in {"AFFINE_SAME_UNIT", "REVIEWED_PERIOD_PROJECTION"}:
            source = operands[0]
            _fail(source.number is not None, "UNSUPPORTED", "NUMERIC_OPERAND_REQUIRED")
            descriptor = source.descriptor
            if op.kind == "REVIEWED_PERIOD_PROJECTION":
                horizon = root.sources.request.temporal
                _fail(
                    horizon.kind != "DAY" or op.temporal == horizon,
                    "UNSUPPORTED",
                    "DAY_ROOT_OUTSIDE_COVERED_FRAME",
                )
                _fail(
                    op.temporal in rule.calendar_cells or op.temporal == horizon,
                    "UNSUPPORTED",
                    "REVIEWED_TEMPORAL_CELL_UNAVAILABLE",
                )
                descriptor = n.NutritionRootDescriptor.model_validate(
                    dict(canonical(descriptor), temporal=canonical(op.temporal))
                )
            number = ratio(op.coefficient) * source.number + ratio(op.offset)
            rational(number)  # bound intermediate integer work after every finite operation
            result = _Value(descriptor, source.root_key, number)
        elif op.kind == "MAKE_CONSTRAINT":
            base = clauses.get(op.root_key)
            _fail(
                base is not None and all(v.number is not None for v in operands),
                "UNSUPPORTED",
                "CONSTRAINT_REFERENCE_UNAVAILABLE",
            )
            descriptor = n.NutritionRootDescriptor.model_validate(
                dict(canonical(base.descriptor), temporal=canonical(op.temporal))
            )
            _fail(
                all(v.descriptor == descriptor for v in operands),
                "UNSUPPORTED",
                "DESCRIPTOR_MISMATCH_BEFORE_ARITHMETIC",
            )
            nums = [v.number for v in operands]
            _fail(all(v >= 0 for v in nums), "CONFLICT", "NEGATIVE_FINAL_AMOUNT")
            _fail(
                op.constraint_kind != "RANGE" or nums[0] <= nums[1],
                "CONFLICT",
                "EMPTY_PROTECTED_INTERVAL",
            )
            fields = {"kind": op.constraint_kind}
            if op.constraint_kind == "RANGE":
                fields.update(lower=amount(nums[0]), upper=amount(nums[1]))
            else:
                fields[
                    {"MINIMUM": "lower", "MAXIMUM": "upper", "TARGET": "center"}[op.constraint_kind]
                ] = amount(nums[0])
            claim = c.NutritionPolicyClaim(
                id=op.id,
                subject=subject,
                root_key=op.root_key,
                descriptor=descriptor,
                layer=op.layer,
                constraint=fields,
                rule_revision_id=rule.revision_id,
                evidence_id=op.evidence_id,
            )
            result = _Value(descriptor, op.root_key, claim=claim)
        elif op.kind == "FINITE_PERIOD_SUM":
            base = operands[0]
            _fail(
                all(
                    v.number is not None
                    and same_measure(v.descriptor, base.descriptor)
                    and v.root_key == base.root_key
                    for v in operands
                ),
                "UNSUPPORTED",
                "PERIOD_DESCRIPTOR_MISMATCH",
            )
            _fail(
                tuple(v.descriptor.temporal for v in operands) == rule.calendar_cells
                and op.temporal == rule.applicability.temporal,
                "UNSUPPORTED",
                "EXACT_PERIOD_PARTITION_REQUIRED",
            )
            number = sum(
                (ratio(co) * v.number for co, v in zip(op.coefficients, operands, strict=True)),
                Fraction(),
            )
            rational(number)
            descriptor = n.NutritionRootDescriptor.model_validate(
                dict(canonical(base.descriptor), temporal=canonical(op.temporal))
            )
            result = _Value(descriptor, base.root_key, number)
        elif op.kind == "CHECK_SUBSET":
            a, b = operands
            _fail(
                a.descriptor == b.descriptor
                and a.root_key == b.root_key
                and a.claim is not None
                and b.claim is not None,
                "UNSUPPORTED",
                "SUBSET_DESCRIPTOR_MISMATCH",
            )
            passed = subset(a.claim.constraint, b.claim.constraint)
            _fail(passed, "CONFLICT", "AUTHORED_SUBSET_FAILED")
        elif op.kind == "CHECK_DIRECTION":
            goal, reference = operands
            _fail(
                goal.claim is not None
                and goal.claim.layer in {"GOAL_PROTECTION", "WEEKLY_GOAL"}
                and goal.descriptor.metric == "ENERGY"
                and reference.number is not None
                and goal.descriptor == reference.descriptor,
                "UNSUPPORTED",
                "GOAL_COMPARATOR_REFERENCE_UNAVAILABLE",
            )
            lower, upper = endpoints(goal.claim.constraint)
            ref = reference.number
            passed = {
                "UPPER_LT": upper is not None and upper < ref,
                "UPPER_LE": upper is not None and upper <= ref,
                "LOWER_GT": lower is not None and lower > ref,
                "LOWER_GE": lower is not None and lower >= ref,
                "CONTAINS": (lower is None or lower <= ref) and (upper is None or ref <= upper),
            }[op.comparator]
            _fail(passed, "CONFLICT", "REVIEWED_GOAL_DIRECTION_RELATION_FAILED")
            direction_checked.add(goal.claim.id)
        else:  # closed SELECT_PRECISION_CASE
            _fail(
                all(v.claim is not None and v.claim.layer == "COMFORT" for v in operands),
                "UNSUPPORTED",
                "AUTHORED_COMFORT_CASES_REQUIRED",
            )
            relaxed, standard, precise = operands
            _fail(
                relaxed.descriptor == standard.descriptor == precise.descriptor
                and relaxed.root_key == standard.root_key == precise.root_key,
                "UNSUPPORTED",
                "PRECISION_DESCRIPTOR_MISMATCH",
            )
            _fail(
                subset(precise.claim.constraint, standard.claim.constraint)
                and subset(standard.claim.constraint, relaxed.claim.constraint),
                "CONFLICT",
                "PRECISION_NESTING_FAILED",
            )
            _fail(precision is not None, "UNAVAILABLE", "PRECISION_SOURCE_UNAVAILABLE")
            result = operands[{"RELAXED": 0, "STANDARD": 1, "PRECISION": 2}[precision.value]]
            selected.add(result.claim.id)
        if result is not None:
            values[op.id] = result
        else:
            # A boolean instruction cannot be used as an arithmetic operand.
            values[op.id] = None
        traces.append(
            c.NutritionPolicyTrace(
                operation_id=op.id,
                descriptor=result.descriptor if result else None,
                amount=rational(result.number) if result and result.number is not None else None,
                claim=result.claim if result else None,
                passed=passed,
            )
        )
    claims = [
        v.claim
        for op_id, v in values.items()
        if v
        and v.claim
        and op_id == v.claim.id
        and (v.claim.layer != "COMFORT" or v.claim.id in selected)
    ]
    goals = {x.id for x in claims if x.layer in {"GOAL_PROTECTION", "WEEKLY_GOAL"}}
    _fail(
        goals and goals <= direction_checked, "UNAVAILABLE", "GOAL_COMPARATOR_REFERENCE_UNAVAILABLE"
    )
    _fail(
        set(case.required_claims) <= {op.id for op in case.operations if values[op.id] is not None},
        "UNAVAILABLE",
        "REQUIRED_CLAIM_UNAVAILABLE",
    )
    return tuple(claims), tuple(traces)


def _coverage(root, rule, case, claims, trace):
    hard = {
        r.clause.root_key: r.clause
        for r in root.roots
        if r.clause.interpretation == "GUIDELINE_HARD"
    }
    _fail(
        any(r.clause.descriptor.metric == "ENERGY" for r in root.roots),
        "UNSUPPORTED",
        "ENERGY_ROOT_REQUIRED",
    )
    for key in case.daily_root_keys:
        _fail(key in hard, "UNAVAILABLE", "DAILY_PROTECTION_AUTHORITY_MISSING")
        for cell in rule.calendar_cells:
            _fail(
                any(
                    x.root_key == key
                    and x.layer == "DAILY_PROTECTION"
                    and x.descriptor.temporal == cell
                    for x in claims
                ),
                "UNAVAILABLE",
                "DAILY_PROTECTION_AUTHORITY_MISSING",
            )
    for key in case.comfort_root_keys:
        _fail(
            any(x.root_key == key and x.layer == "COMFORT" for x in claims),
            "UNAVAILABLE",
            "COMFORT_COVERAGE_MISSING",
        )
    _fail(
        any(x.layer == "GOAL_PROTECTION" and x.descriptor.metric == "ENERGY" for x in claims),
        "UNAVAILABLE",
        "GOAL_PROTECTION_MISSING",
    )
    if root.sources.request.temporal.kind == "DAY":
        _fail(case.weekly == "NOT_APPLICABLE", "UNSUPPORTED", "WEEKLY_PROFILE_UNSUPPORTED")
    else:
        _fail(
            case.weekly == "REQUIRED"
            and any(x.layer == "WEEKLY_GOAL" for x in claims)
            and any(x.layer == "WEEKLY_CENTER" for x in claims),
            "UNAVAILABLE",
            "WEEKLY_COVERAGE_MISSING",
        )
    authored_claims = {t.claim.id: t.claim for t in trace if t.claim is not None}
    for claim in authored_claims.values():
        root_clause = hard.get(claim.root_key)
        if root_clause and claim.descriptor == root_clause.descriptor:
            _fail(
                subset(claim.constraint, root_clause.constraint),
                "CONFLICT",
                "HARD_ROOT_CONTAINMENT_FAILED",
            )
        if claim.layer in {"COMFORT", "WEEKLY_CENTER"}:
            protections = [
                x
                for x in claims
                if x.layer in {"GOAL_PROTECTION", "DAILY_PROTECTION", "WEEKLY_GOAL"}
                and x.descriptor == claim.descriptor
            ]
            _fail(
                protections and all(subset(claim.constraint, x.constraint) for x in protections),
                "CONFLICT",
                "COMFORT_PROTECTION_CONTAINMENT_FAILED",
            )
    # All protected conjuncts on one descriptor must intersect. TARGET remains soft.
    groups = {}
    for claim in claims:
        if claim.layer not in {"COMFORT", "WEEKLY_CENTER"}:
            groups.setdefault(digest("descriptor", claim.descriptor), []).append(claim.constraint)
    for clause in hard.values():
        groups.setdefault(digest("descriptor", clause.descriptor), []).append(clause.constraint)
    for constraints in groups.values():
        lows, highs = [], []
        for constraint in constraints:
            lower, upper = endpoints(constraint)
            if lower is not None:
                lows.append(lower)
            if upper is not None:
                highs.append(upper)
        _fail(
            not lows or not highs or max(lows) <= min(highs), "CONFLICT", "EMPTY_PROTECTED_INTERVAL"
        )


def _resolution(requirements, resolution, claims):
    _fail(resolution is not None, "UNAVAILABLE", "RESOLUTION_SOURCE_UNAVAILABLE")
    _fail(
        resolution.environment == requirements.environment == "TEST_ONLY",
        "UNSUPPORTED",
        "PRODUCTION_ESTIMATOR_NOT_IMPLEMENTED",
    )
    _fail(
        resolution.requirements_fingerprint == requirements.fingerprint,
        "UNSUPPORTED",
        "RESOLUTION_REQUIREMENT_IDENTITY_MISMATCH",
    )
    _fail(resolution.availability == "AVAILABLE", "UNAVAILABLE", "RESOLUTION_INSUFFICIENT")
    # This is a retained TEST_ONLY interface fixture, never the future MTR-007
    # estimator/capture authority. Independent expected values and preimages remain visible.
    retained = json.loads(resolution.evidence.body)
    _fail(
        retained.get("kind") == "TEST_ONLY_RESOLUTION_FIXTURE_V1"
        and retained.get("estimator_version")
        == resolution.estimator_version
        == "TEST_ONLY_fixture_v1"
        and resolution.evidence.environment == "TEST_ONLY",
        "UNSUPPORTED",
        "RESOLUTION_PRIMITIVE_AUTHORITY_UNAVAILABLE",
    )
    _fail(
        retained.get("facts") == canonical(resolution.facts)
        and digest("pool", resolution.facts) == resolution.pool_fingerprint,
        "UNSUPPORTED",
        "COMPLETE_RESOLUTION_PREIMAGES_REQUIRED",
    )
    required_keys = {
        (x.root_key, digest("descriptor", x.descriptor)) for x in requirements.measurements
    }
    _fail(
        {(x.root_key, digest("descriptor", x.descriptor)) for x in resolution.facts}
        == required_keys,
        "UNAVAILABLE",
        "RESOLUTION_COVERAGE_MISSING",
    )
    for fact in resolution.facts:
        data = canonical(fact)
        data.pop("primitive_fingerprint")
        _fail(
            fact.primitive_fingerprint == digest("resolution-primitive", data)
            and fact.portion_step == fact.expected_step
            and ratio(fact.portion_step) > 0,
            "UNSUPPORTED",
            "RESOLUTION_PRIMITIVE_EXPECTATION_MISMATCH",
        )
        for claim in claims:
            if (
                claim.layer == "COMFORT"
                and claim.root_key == fact.root_key
                and claim.descriptor == fact.descriptor
            ):
                _fail(
                    claim.descriptor == fact.descriptor,
                    "UNSUPPORTED",
                    "RESOLUTION_DESCRIPTOR_MISMATCH",
                )
                lower, upper = endpoints(claim.constraint)
                _fail(
                    lower is not None
                    and upper is not None
                    and ratio(fact.portion_step) <= upper - lower,
                    "UNAVAILABLE",
                    "RESOLUTION_INSUFFICIENT",
                )


def _period_consistency(root, rule, case, claims, trace):
    if root.sources.request.temporal.kind == "DAY":
        return
    horizon = root.sources.request.temporal
    origins, maps = {}, {}
    by_id = {t.operation_id: t for t in trace}
    for op in case.operations:
        origin = op.root_key or (origins.get(op.inputs[0]) if op.inputs else None)
        origins[op.id] = origin
        if op.kind == "FINITE_PERIOD_SUM":
            _fail(
                all(origins.get(k) == origin for k in op.inputs),
                "UNSUPPORTED",
                "CROSS_METRIC_PERIOD_MAP",
            )
            _fail(
                tuple(by_id[k].descriptor.temporal for k in op.inputs) == rule.calendar_cells,
                "UNSUPPORTED",
                "PERIOD_MAP_COVERAGE_MISSING",
            )
            vector = tuple(ratio(x) for x in op.coefficients)
            _fail(
                origin not in maps or maps[origin] == vector,
                "UNSUPPORTED",
                "COUPLED_PERIOD_SYSTEM_UNSUPPORTED",
            )
            maps[origin] = vector
    for key in case.daily_root_keys:
        _fail(key in maps, "UNAVAILABLE", "REVIEWED_PERIOD_SUM_AUTHORITY_MISSING")
        cell_lows, cell_highs = [], []
        for cell in rule.calendar_cells:
            protected = [
                x
                for x in claims
                if x.root_key == key
                and x.descriptor.temporal == cell
                and x.layer in {"DAILY_PROTECTION", "GOAL_PROTECTION"}
            ]
            lows = [lo for x in protected if (lo := endpoints(x.constraint)[0]) is not None]
            highs = [hi for x in protected if (hi := endpoints(x.constraint)[1]) is not None]
            cell_lows.append(max(lows) if lows else None)
            cell_highs.append(min(highs) if highs else None)
        lower = (
            sum((w * x for w, x in zip(maps[key], cell_lows, strict=True)), Fraction())
            if all(x is not None for x in cell_lows)
            else None
        )
        upper = (
            sum((w * x for w, x in zip(maps[key], cell_highs, strict=True)), Fraction())
            if all(x is not None for x in cell_highs)
            else None
        )
        aggregate = [
            x.constraint
            for x in claims
            if x.root_key == key
            and x.descriptor.temporal == horizon
            and x.layer in {"GOAL_PROTECTION", "WEEKLY_GOAL"}
        ]
        aggregate += [
            r.clause.constraint
            for r in root.roots
            if r.clause.root_key == key and r.clause.interpretation == "GUIDELINE_HARD"
        ]
        lows = ([lower] if lower is not None else []) + [
            lo for x in aggregate if (lo := endpoints(x)[0]) is not None
        ]
        highs = ([upper] if upper is not None else []) + [
            hi for x in aggregate if (hi := endpoints(x)[1]) is not None
        ]
        _fail(
            not lows or not highs or max(lows) <= min(highs),
            "CONFLICT",
            "DAILY_AGGREGATE_INTERVAL_CONFLICT",
        )


def synthesize_nutrition_policy(value, resolution=None):
    sources, rule, reason = replay_synthesis_sources(value)
    root = root_public.validate_nutrition_root(sources.request.root)
    if resolution is not None:
        resolution = c.NutritionResolutionInput.model_validate(canonical(resolution))
    claims, trace, requirements, reasons = (), (), None, ()
    outcome = "AVAILABLE"
    try:
        _fail(
            reason is None,
            "UNSUPPORTED" if reason and "UNSUPPORTED" in reason else "UNAVAILABLE",
            reason,
        )
        _fail(
            root.availability == "AVAILABLE"
            and root.eligibility == "SUPPORTED"
            and root.goal_state == "PRESENT",
            "UNAVAILABLE",
            "ROOT_" + (root.reasons[0] if root.reasons else root.goal_state),
        )
        _calendar(rule)
        case = _case(root, rule)
        require(
            not sources.request.required_claims
            or set(sources.request.required_claims) == set(case.required_claims),
            "Caller cannot replace published requiredness",
        )
        requirements = _requirements(sources, rule, case)
        claims, trace = _evaluate(root, rule, case, sources.request.precision)
        _coverage(root, rule, case, claims, trace)
        _period_consistency(root, rule, case, claims, trace)
        _resolution(requirements, resolution, claims)
    except _PolicyFailure as exc:
        outcome, reasons = exc.state, (exc.reason,)
        claims, trace = (), ()
    data = dict(
        inputs=sources,
        resolution=resolution,
        outcome=outcome,
        environment=root.sources.request.environment,
        hard_roots=root.roots,
        claims=claims,
        trace=trace,
        reasons=reasons,
        requirements=requirements,
        result_fingerprint="0" * 64,
    )
    result = c.NutritionPolicy(**data)
    payload = canonical(result)
    payload.pop("result_fingerprint")
    return c.NutritionPolicy.model_validate(
        dict(payload, result_fingerprint=digest("policy", payload))
    )


def validate_nutrition_policy(value):
    parsed = c.NutritionPolicy.model_validate(canonical(value))
    expected = synthesize_nutrition_policy(parsed.inputs, parsed.resolution)
    require(parsed == expected, "Full NutritionPolicy semantic reconstruction differs")
    return expected


def admit_production_nutrition_policy(value):
    validate_nutrition_policy(value)
    raise ValueError("PRODUCTION_NUTRITION_CLINICAL_CONTENT_GATE_CLOSED")
