"""Independent v2 instruction fold and containment; no Nutrition producer imports."""

from fractions import Fraction

from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition import synthesis_contracts as c


class InvalidPolicy(ValueError):
    def __init__(self, code, outcome="POLICY_CONFLICT", stage="RULE"):
        self.code, self.outcome, self.stage = code, outcome, stage


def demand(ok, code, outcome="POLICY_CONFLICT", stage="RULE"):
    if not ok:
        raise InvalidPolicy(code, outcome, stage)


def q(value):
    return Fraction(value.numerator, value.denominator)


def bounds(clause):
    return (
        q(clause.lower) if hasattr(clause, "lower") else None,
        q(clause.upper) if hasattr(clause, "upper") else None,
    )


def contained(inner, outer):
    lo, hi = bounds(inner)
    if inner.kind == "TARGET":
        lo = hi = q(inner.center)
    if outer.kind == "TARGET":
        return inner.kind == "TARGET" and inner.center == outer.center
    a, z = bounds(outer)
    return (a is None or lo is not None and lo >= a) and (z is None or hi is not None and hi <= z)


def reconstruct_claims(root, rule, case, precision, work):
    clauses = {r.clause.root_key: r.clause for r in root.roots}
    nodes, trace, chosen, directions = {}, [], set(), set()
    for op in case.operations:
        work.charge(1 + len(op.inputs))
        operands = [nodes[k] for k in op.inputs]
        # Each node is (root_key, descriptor, exact endpoint, claim).
        node, passed = None, None
        if op.kind == "COPY_REFERENCE":
            clause = clauses.get(op.root_key)
            demand(
                clause is not None and hasattr(clause.constraint, op.endpoint),
                "CLAIM_COVERAGE_MISSING",
                "SOURCE_UNAVAILABLE",
            )
            node = (
                op.root_key,
                clause.descriptor,
                q(getattr(clause.constraint, op.endpoint)),
                None,
            )
        elif op.kind in {"AFFINE_SAME_UNIT", "REVIEWED_PERIOD_PROJECTION", "FINITE_PERIOD_SUM"}:
            key, desc, number, claim = operands[0]
            demand(number is not None, "UNSUPPORTED_TEMPORAL_MAP", "UNSUPPORTED")
            if op.kind == "FINITE_PERIOD_SUM":
                demand(
                    all(
                        x[0] == key
                        and x[2] is not None
                        and canonical(x[1]) | {"temporal": None}
                        == canonical(desc) | {"temporal": None}
                        for x in operands
                    ),
                    "UNSUPPORTED_TEMPORAL_MAP",
                    "UNSUPPORTED",
                )
                demand(
                    tuple(x[1].temporal for x in operands) == rule.calendar_cells
                    and op.temporal == rule.applicability.temporal,
                    "UNSUPPORTED_TEMPORAL_MAP",
                    "UNSUPPORTED",
                )
                demand(
                    key not in case.daily_root_keys or all(q(x) == 1 for x in op.coefficients),
                    "UNSUPPORTED_TEMPORAL_MAP",
                    "UNSUPPORTED",
                )
                number = Fraction()
                for weight, node in zip(op.coefficients, operands, strict=True):
                    number = work.add(number, work.multiply(q(weight), node[2]))
            else:
                number = work.add(work.multiply(q(op.coefficient), number), q(op.offset))
            work.number(number)
            # The frozen endpoint carrier keeps its signed 127-bit boundary.
            c.SynthesisRational(numerator=number.numerator, denominator=number.denominator)
            if op.temporal is not None:
                demand(
                    op.temporal in rule.calendar_cells
                    or op.temporal == root.sources.request.temporal,
                    "UNSUPPORTED_TEMPORAL_MAP",
                    "UNSUPPORTED",
                )
                demand(
                    root.sources.request.temporal.kind != "DAY"
                    or op.temporal == root.sources.request.temporal,
                    "UNSUPPORTED_TEMPORAL_MAP",
                    "UNSUPPORTED",
                )
                desc = n.NutritionRootDescriptor.model_validate(
                    canonical(desc) | {"temporal": canonical(op.temporal)}
                )
            node = (key, desc, number, None)
        elif op.kind == "MAKE_CONSTRAINT":
            base = clauses.get(op.root_key)
            demand(base is not None, "UNSUPPORTED_TEMPORAL_MAP", "UNSUPPORTED")
            desc = n.NutritionRootDescriptor.model_validate(
                canonical(base.descriptor) | {"temporal": canonical(op.temporal)}
            )
            demand(
                all(x[0] == op.root_key and x[1] == desc and x[2] is not None for x in operands),
                "UNSUPPORTED_TEMPORAL_MAP",
                "UNSUPPORTED",
            )
            nums = [x[2] for x in operands]
            demand(all(x >= 0 for x in nums), "HARD_CONTAINMENT_FAILED")
            demand(
                op.constraint_kind != "RANGE" or nums[0] <= nums[1], "PROTECTED_INTERVAL_CONFLICT"
            )
            fields = {
                "RANGE": ("lower", "upper"),
                "MINIMUM": ("lower",),
                "MAXIMUM": ("upper",),
                "TARGET": ("center",),
            }[op.constraint_kind]
            constraint = {"kind": op.constraint_kind} | {
                k: dict(numerator=x.numerator, denominator=x.denominator)
                for k, x in zip(fields, nums, strict=True)
            }
            claim = c.NutritionPolicyClaim(
                id=op.id,
                subject=root.sources.request.subject,
                root_key=op.root_key,
                descriptor=desc,
                layer=op.layer,
                constraint=constraint,
                rule_revision_id=rule.revision_id,
                evidence_id=op.evidence_id,
            )
            node = (op.root_key, desc, None, claim)
        elif op.kind == "SELECT_PRECISION_CASE":
            demand(
                all(
                    x[3] is not None and x[3].layer == "COMFORT" and x[3].constraint.kind == "RANGE"
                    for x in operands
                ),
                "UNSUPPORTED_TEMPORAL_MAP",
                "UNSUPPORTED",
            )
            demand(
                all(x[:2] == operands[0][:2] for x in operands),
                "UNSUPPORTED_TEMPORAL_MAP",
                "UNSUPPORTED",
            )
            demand(
                contained(operands[2][3].constraint, operands[1][3].constraint)
                and contained(operands[1][3].constraint, operands[0][3].constraint),
                "PRECISION_NESTING_FAILED",
            )
            node = operands[{"RELAXED": 0, "STANDARD": 1, "PRECISION": 2}[precision.value]]
            chosen.add(node[3].id)
        elif op.kind == "CHECK_SUBSET":
            inner, outer = operands
            demand(
                inner[:2] == outer[:2] and inner[3] is not None and outer[3] is not None,
                "UNSUPPORTED_TEMPORAL_MAP",
                "UNSUPPORTED",
            )
            demand(contained(inner[3].constraint, outer[3].constraint), "HARD_CONTAINMENT_FAILED")
            passed = True
        elif op.kind == "CHECK_DIRECTION":
            goal, ref = operands
            demand(
                goal[:2] == ref[:2]
                and goal[3] is not None
                and ref[2] is not None
                and goal[1].metric == "ENERGY"
                and goal[3].layer in {"GOAL_PROTECTION", "WEEKLY_GOAL"},
                "UNSUPPORTED_TEMPORAL_MAP",
                "UNSUPPORTED",
            )
            lo, hi = bounds(goal[3].constraint)
            r = ref[2]
            ok = {
                "UPPER_LT": hi is not None and hi < r,
                "UPPER_LE": hi is not None and hi <= r,
                "LOWER_GT": lo is not None and lo > r,
                "LOWER_GE": lo is not None and lo >= r,
                "CONTAINS": (lo is None or lo <= r) and (hi is None or r <= hi),
            }[op.comparator]
            demand(ok, "GOAL_DIRECTION_CONFLICT")
            directions.add(goal[3].id)
            passed = True
        else:
            raise InvalidPolicy("SOURCE_MALFORMED", "REJECTED")
        nodes[op.id] = node
        number = node[2] if node else None
        trace.append(
            c.NutritionPolicyTrace(
                operation_id=op.id,
                descriptor=node[1] if node else None,
                amount=dict(numerator=number.numerator, denominator=number.denominator)
                if number is not None
                else None,
                claim=node[3] if node else None,
                passed=passed,
            )
        )
    claims = tuple(
        t.claim
        for t in trace
        if t.claim is not None
        and t.operation_id == t.claim.id
        and (t.claim.layer != "COMFORT" or t.claim.id in chosen)
    )
    goal_ids = {x.id for x in claims if x.layer in {"GOAL_PROTECTION", "WEEKLY_GOAL"}}
    demand(
        goal_ids
        and goal_ids <= directions
        and all(nodes[x] is not None for x in case.required_claims),
        "CLAIM_COVERAGE_MISSING",
        "SOURCE_UNAVAILABLE",
    )
    return claims, tuple(trace)


def check_coverage(root, rule, case, claims, trace, work):
    qscope = root.sources.request.temporal
    cursor = qscope.interval.start
    for cell in rule.calendar_cells:
        work.charge()
        demand(
            (cell.calendar, cell.timezone, cell.interval.start)
            == (qscope.calendar, qscope.timezone, cursor),
            "UNSUPPORTED_TEMPORAL_MAP",
            "UNSUPPORTED",
        )
        cursor = cell.interval.end
    demand(cursor == qscope.interval.end, "UNSUPPORTED_TEMPORAL_MAP", "UNSUPPORTED")
    demand(qscope.kind in {"DAY", "WEEK"}, "UNSUPPORTED_TEMPORAL_MAP", "UNSUPPORTED")
    demand(
        qscope.kind != "DAY" or rule.calendar_cells == (qscope,),
        "UNSUPPORTED_TEMPORAL_MAP",
        "UNSUPPORTED",
    )
    hard = [r.clause for r in root.roots if r.clause.interpretation == "GUIDELINE_HARD"]
    for key in case.daily_root_keys:
        demand(
            any(r.root_key == key for r in hard), "DAILY_PROTECTION_MISSING", "SOURCE_UNAVAILABLE"
        )
        for cell in rule.calendar_cells:
            demand(
                any(
                    x.root_key == key
                    and x.layer == "DAILY_PROTECTION"
                    and x.descriptor.temporal == cell
                    for x in claims
                ),
                "DAILY_PROTECTION_MISSING",
                "SOURCE_UNAVAILABLE",
            )
    for key in case.comfort_root_keys:
        demand(
            any(x.root_key == key and x.layer == "COMFORT" for x in claims),
            "CLAIM_COVERAGE_MISSING",
            "SOURCE_UNAVAILABLE",
        )
    demand(
        any(x.layer == "GOAL_PROTECTION" and x.descriptor.metric == "ENERGY" for x in claims),
        "CLAIM_COVERAGE_MISSING",
        "SOURCE_UNAVAILABLE",
    )
    if qscope.kind == "DAY":
        demand(case.weekly == "NOT_APPLICABLE", "UNSUPPORTED_TEMPORAL_MAP", "UNSUPPORTED")
    else:
        demand(
            case.weekly == "REQUIRED"
            and {"WEEKLY_GOAL", "WEEKLY_CENTER"} <= {x.layer for x in claims},
            "CLAIM_COVERAGE_MISSING",
            "SOURCE_UNAVAILABLE",
        )
    protective = [
        x for x in claims if x.layer in {"GOAL_PROTECTION", "DAILY_PROTECTION", "WEEKLY_GOAL"}
    ]
    for t in trace:
        if t.claim is None:
            continue
        claim = t.claim
        for original in hard:
            if original.root_key == claim.root_key and original.descriptor == claim.descriptor:
                demand(contained(claim.constraint, original.constraint), "HARD_CONTAINMENT_FAILED")
        if claim.layer in {"COMFORT", "WEEKLY_CENTER"}:
            matches = [x for x in protective if x.descriptor == claim.descriptor]
            demand(
                matches and all(contained(claim.constraint, x.constraint) for x in matches),
                "HARD_CONTAINMENT_FAILED",
            )
    groups = {}
    for x in [*hard, *protective]:
        groups.setdefault(str(canonical(x.descriptor)), []).append(x.constraint)
    for constraints in groups.values():
        lows = [low for x in constraints if (low := bounds(x)[0]) is not None]
        highs = [h for x in constraints if (h := bounds(x)[1]) is not None]
        demand(not lows or not highs or max(lows) <= min(highs), "PROTECTED_INTERVAL_CONFLICT")
    if qscope.kind == "WEEK":
        roots = {}
        maps = {}
        byid = {x.operation_id: x for x in trace}
        for op in case.operations:
            roots[op.id] = op.root_key or (roots.get(op.inputs[0]) if op.inputs else None)
            if op.kind == "FINITE_PERIOD_SUM":
                key = roots[op.id]
                demand(
                    all(roots[k] == key for k in op.inputs)
                    and tuple(byid[k].descriptor.temporal for k in op.inputs)
                    == rule.calendar_cells,
                    "UNSUPPORTED_TEMPORAL_MAP",
                    "UNSUPPORTED",
                )
                coefficients = tuple(q(value) for value in op.coefficients)
                demand(
                    key not in maps or maps[key] == coefficients,
                    "UNSUPPORTED_TEMPORAL_MAP",
                    "UNSUPPORTED",
                )
                maps[key] = coefficients
                if key in case.daily_root_keys:
                    demand(
                        all(q(x) == 1 for x in op.coefficients),
                        "UNSUPPORTED_TEMPORAL_MAP",
                        "UNSUPPORTED",
                    )
        for key in case.daily_root_keys:
            demand(key in maps, "CLAIM_COVERAGE_MISSING", "SOURCE_UNAVAILABLE")
            day_bounds = []
            for cell in rule.calendar_cells:
                rows = [
                    x
                    for x in protective
                    if x.root_key == key
                    and x.descriptor.temporal == cell
                    and x.layer in {"GOAL_PROTECTION", "DAILY_PROTECTION"}
                ]
                lower = [lo for x in rows if (lo := bounds(x.constraint)[0]) is not None]
                upper = [hi for x in rows if (hi := bounds(x.constraint)[1]) is not None]
                day_bounds.append((max(lower) if lower else None, min(upper) if upper else None))
            aggregate = [
                x
                for x in [*hard, *protective]
                if x.root_key == key and x.descriptor.temporal == qscope
            ]
            lo = [a for x in aggregate if (a := bounds(x.constraint)[0]) is not None]
            hi = [a for x in aggregate if (a := bounds(x.constraint)[1]) is not None]
            if all(x[0] is not None for x in day_bounds):
                lo.append(sum(x[0] for x in day_bounds))
            if all(x[1] is not None for x in day_bounds):
                hi.append(sum(x[1] for x in day_bounds))
            demand(not lo or not hi or max(lo) <= min(hi), "PROTECTED_INTERVAL_CONFLICT")
