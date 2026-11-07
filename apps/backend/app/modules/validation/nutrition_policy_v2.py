"""Independent whole-policy reconstruction; no Nutrition business evaluator imports."""

from fractions import Fraction

from app.domain.feature_identity import canonical, canonical_bytes
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition import policy_v2_contracts as v
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.policy_v2_limits import CHECK_BYTES, RESULT_BYTES, PolicyWork
from app.modules.nutrition.resolution_contracts import resolution_hash
from app.modules.nutrition.resolution_limits import WorkBudget
from app.modules.validation import basis_applicability as mba
from app.modules.validation.nutrition_policy_v2_rules import (
    InvalidPolicy,
    check_coverage,
    demand,
    q,
    reconstruct_claims,
)
from app.modules.validation.nutrition_resolution import check_nutrition_resolution_independently
from app.modules.validation.nutrition_resolution_authority import verify_resolution_rule_sources
from app.modules.validation.nutrition_roots import validate_nutrition_root_independently


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


def _requirements(root, rule, case):
    rows = {}
    clauses = {r.clause.root_key: r.clause for r in root.roots}

    def old_hash(kind, value):
        return n.nutrition_root_hash("nutrition-synthesis." + kind + ".v1", value)

    for op in case.operations:
        if op.kind == "MAKE_CONSTRAINT" and op.layer == "COMFORT":
            demand(
                op.root_key in case.comfort_root_keys, "REQUIREMENT_COVERAGE_MISSING", "REJECTED"
            )
            desc = n.NutritionRootDescriptor.model_validate(
                canonical(clauses[op.root_key].descriptor) | {"temporal": canonical(op.temporal)}
            )
            row = c.NutritionResolutionRequirement(root_key=op.root_key, descriptor=desc)
            rows[old_hash("measurement", row)] = row
    data = dict(
        subject=root.sources.request.subject,
        root_fingerprint=root.result_fingerprint,
        rule_body_fingerprint=old_hash("rule", rule),
        case_id=case.id,
        temporal=root.sources.request.temporal,
        root_keys=case.comfort_root_keys,
        measurements=tuple(row for _, row in sorted(rows.items())),
        environment=root.sources.request.environment,
    )
    return c.NutritionPolicyRequirementSpec(**data, fingerprint=old_hash("requirements", data))


def _rule_source(ss):
    try:
        return verify_resolution_rule_sources(ss)
    except ValueError as exc:
        if str(exc) in {"AUTHORITY_ABSENT", "AUTHORITY_REVOKED_OR_EXPIRED"}:
            raise _Failure("SOURCE_UNAVAILABLE", "SOURCE_UNAUTHORIZED", "SOURCE") from exc
        if str(exc) not in {"PUBLICATION_COVERAGE", "CROSS_VERSION_STITCHING"}:
            raise
        # The frozen independent authority verifier has checked the COMPLETE
        # journal before reaching its publication-coverage failure. Classify that
        # legitimate negative with a separate retained-time boundary grid; never
        # turn a malformed authority/history failure into an unavailable source.
        interval = ss.request.root.sources.request.temporal.interval
        drafts = {
            r.command.body.rule.revision_id: r.command.body.rule
            for r in ss.records
            if r.command.body.kind == "DRAFT"
        }
        publications = [r for r in ss.records if r.command.body.kind == "PUBLICATION"]
        points = {interval.start, interval.end}
        for row in publications:
            points.update(
                (row.command.body.effective_at, drafts[row.command.body.revision_id].effective.end)
            )
        grid = sorted(points)
        cells = {(a, z): None for a, z in zip(grid, grid[1:])}
        for row in publications:
            op = row.command.body
            for (a, z), state in list(cells.items()):
                if op.action in {"PUBLISH", "SUPERSEDE"}:
                    if op.effective_at <= a and z <= drafts[op.revision_id].effective.end:
                        cells[a, z] = (row.id, True)
                elif (
                    state is not None
                    and state[0] == op.predecessor_publication_id
                    and z > op.effective_at
                ):
                    cells[a, z] = (row.id, False)
        selected = {
            state for (a, z), state in cells.items() if interval.start <= a and z <= interval.end
        }
        withdrawn = len(selected) == 1 and None not in selected and not next(iter(selected))[1]
        raise _Failure(
            "SOURCE_UNAVAILABLE",
            "SOURCE_WITHDRAWN" if withdrawn else "SOURCE_UNAUTHORIZED",
            "SOURCE",
        ) from exc


def _basis(s, claimed):
    if claimed.payload is not None:
        child = claimed.payload.reconstructed_basis_result
        report = mba.check_basis_applicability_independently(s, child)
        demand(report.decision == "CONSISTENT", "MBA_INCONSISTENT", "REJECTED", "MBA")
        return child
    # Negative/null payloads have no child result to check. Use only the independently
    # owned reconstruction, once, preserving the frozen typed outcome/reason semantics.
    try:
        witnesses = mba._reconstruct(s, WorkBudget(s.selectors.max_work))
        outcome, reasons = "APPLICABLE_TEST_ONLY", ()
    except mba._Invalid as exc:
        outcome, reasons, witnesses = exc.state, (exc.code,), ()
    except (ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
        outcome = "RESOURCE_EXCEEDED" if str(exc).startswith("RESOURCE_EXCEEDED") else "REJECTED"
        reasons = ("RESOURCE_LIMIT" if outcome == "RESOURCE_EXCEEDED" else "SOURCE_INVALID",)
        witnesses = ()
    temp = b.BasisApplicabilityResultV1(
        outcome=outcome,
        reasons=reasons,
        witnesses=witnesses,
        required_anchor_fingerprints=tuple(x.anchor_fingerprint for x in s.anchors),
        source_fingerprint=s.source_fingerprint,
        result_fingerprint="0" * 64,
    )
    data = canonical(temp)
    data.pop("result_fingerprint")
    return b.BasisApplicabilityResultV1(**data, result_fingerprint=b.basis_hash("result", data))


def _assignments(root, claims, estimate, work):
    """Keyed projection fold, independent of the producer's horizon-vector scan."""
    periods = sorted(estimate.periods, key=lambda p: canonical_bytes(p.temporal))
    demand(
        sum(len(vec.configurations) for period in periods for vec in period.vectors) <= 65536,
        "RESOURCE_LIMIT",
        "RESOURCE_EXCEEDED",
        "JOINT",
    )
    configs = {x.configuration_id: x for x in estimate.configurations}
    byslot = {}
    for config in configs.values():
        byslot.setdefault(config.serving.slot_id, set()).add(config.configuration_id)
    slots = tuple(sorted(byslot))
    period_maps, horizon_rows = {}, None
    for p in periods:
        table = {}
        for vector in p.vectors:
            for witness in vector.configurations:
                work.charge(1 + len(witness))
                demand(
                    len(witness) == len(p.slot_ids) and witness not in table,
                    "JOINT_WITNESS_MISMATCH",
                    "REJECTED",
                    "JOINT",
                )
                mapping = dict(zip(p.slot_ids, witness, strict=True))
                demand(
                    all(cid in byslot.get(slot, ()) for slot, cid in mapping.items()),
                    "JOINT_WITNESS_MISMATCH",
                    "REJECTED",
                    "JOINT",
                )
                components = []
                for j in range(4):
                    number = Fraction()
                    for cid in witness:
                        number = work.add(number, q(configs[cid].nutrients[j]))
                    components.append(work.number(number))
                amounts = tuple(components)
                demand(
                    amounts == tuple(q(x) for x in vector.nutrients),
                    "JOINT_WITNESS_MISMATCH",
                    "REJECTED",
                    "JOINT",
                )
                table[witness] = (
                    amounts,
                    v.policy_v2_hash(
                        "vector", dict(temporal=p.temporal, slot_ids=p.slot_ids, vector=vector)
                    ),
                )
        period_maps[canonical_bytes(p.temporal)] = (p.slot_ids, table)
        if p.temporal == root.sources.request.temporal:
            demand(
                horizon_rows is None and p.slot_ids == slots,
                "JOINT_WITNESS_MISMATCH",
                "REJECTED",
                "JOINT",
            )
            horizon_rows = table
    demand(horizon_rows, "PERIOD_COVERAGE_MISSING", "SOURCE_UNAVAILABLE", "JOINT")
    demand(len(horizon_rows) <= 16384, "RESOURCE_LIMIT", "RESOURCE_EXCEEDED", "JOINT")
    hard = [
        ("root:" + r.clause.root_key, r.clause.descriptor, r.clause.constraint)
        for r in root.roots
        if r.clause.interpretation == "GUIDELINE_HARD"
    ]
    hard += [
        (x.id, x.descriptor, x.constraint)
        for x in claims
        if x.layer in {"GOAL_PROTECTION", "DAILY_PROTECTION", "WEEKLY_GOAL"}
    ]
    soft = [(x.id, x.descriptor, x.constraint) for x in claims if x.layer == "COMFORT"]
    centers = [x for x in claims if x.layer == "WEEKLY_CENTER"]
    rows, hids, cids, deltas = [], [], [], []
    representative = None
    for assignment in sorted(horizon_rows):
        whole = dict(zip(slots, assignment, strict=True))
        amounts, hashes = {}, []
        for key, (pslots, table) in period_maps.items():
            part = tuple(whole[k] for k in pslots)
            demand(part in table, "JOINT_WITNESS_MISMATCH", "REJECTED", "JOINT")
            amounts[key], fp = table[part]
            hashes.append(fp)

        def component(desc):
            work.charge()
            key = canonical_bytes(desc.temporal)
            demand(key in amounts, "PERIOD_COVERAGE_MISSING", "SOURCE_UNAVAILABLE", "JOINT")
            return amounts[key][("ENERGY", "PROTEIN", "FAT", "CARBOHYDRATE").index(desc.metric)]

        def breaches(predicates):
            bad = []
            for key, desc, bound in predicates:
                number = component(desc)
                if (hasattr(bound, "lower") and number < q(bound.lower)) or (
                    hasattr(bound, "upper") and number > q(bound.upper)
                ):
                    bad.append(key)
            return tuple(sorted(bad))

        hid, sid = breaches(hard), breaches(soft)
        aid = v.policy_v2_hash("assignment", dict(slot_ids=slots, configuration_ids=assignment))
        rows.append(
            v.PolicyAssignmentEvaluationV2(
                assignment_fingerprint=aid,
                configuration_ids=assignment,
                period_vector_fingerprints=tuple(hashes),
                hard_violations=hid,
                comfort_violations=sid,
                environment="TEST_ONLY",
            )
        )
        if not hid:
            hids.append(aid)
            if not sid:
                cids.append(aid)
                representative = representative or aid
        for center in centers:
            demand(len(deltas) < 65536, "RESOURCE_LIMIT", "RESOURCE_EXCEEDED", "JOINT")
            delta = work.number(
                work.add(component(center.descriptor), -q(center.constraint.center))
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
    if not hids:
        raise _Failure(
            "RESOLUTION_INSUFFICIENT",
            "NO_PROTECTED_JOINT_WITNESS",
            "JOINT",
            hard="ABSENT_IN_DECLARED_UNIVERSE",
        )
    if not cids:
        raise _Failure(
            "RESOLUTION_INSUFFICIENT",
            "NO_JOINT_COMFORT_SUPPORT",
            "JOINT",
            hard="PRESENT",
            soft="SOFT_UNSUPPORTED",
        )
    data = dict(
        slot_ids=slots,
        assignments=tuple(rows),
        protected_assignment_ids=tuple(sorted(hids)),
        comfort_assignment_ids=tuple(sorted(cids)),
        representative_comfort_assignment_id=representative,
        center_deltas=tuple(sorted(deltas, key=lambda x: (x.assignment_fingerprint, x.claim_id))),
        environment="TEST_ONLY",
    )
    return v.JointPolicySupportV2(**data, support_fingerprint=v.policy_v2_hash("support", data))


def _rebuild(i, claimed, work):
    s, ss = i.basis_sources, i.basis_sources.nre.sources.synthesis_sources
    expected_identity = _identity(s)
    _require(
        i.identity.precision == expected_identity.precision
        and i.identity.precision_witness == expected_identity.precision_witness,
        "PRECISION_IDENTITY_MISMATCH",
    )
    _require(i.identity == expected_identity, "SOURCE_IDENTITY_MISMATCH")
    data = canonical(i)
    data.pop("source_fingerprint")
    _require(v.policy_v2_hash("input", data) == i.source_fingerprint, "SOURCE_IDENTITY_MISMATCH")
    root = ss.request.root
    rcheck = validate_nutrition_root_independently(
        n.NutritionRootValidationInput(
            root=root, coverage="ROOT_SOURCE_CONSISTENCY_ONLY", derived_claims=()
        )
    )
    _require(rcheck.decision == "CONSISTENT", "SOURCE_MALFORMED", "SOURCE")
    _require(
        root.goal_state == "PRESENT", "GOAL_SOURCE_UNAVAILABLE", "SOURCE", "SOURCE_UNAVAILABLE"
    )
    _require(root.availability == "AVAILABLE", "SOURCE_MISSING", "SOURCE", "SOURCE_UNAVAILABLE")
    rule = _rule_source(ss)
    cases = [x for x in rule.cases if x.direction == root.goal_direction]
    _require(len(cases) == 1, "CLAIM_COVERAGE_MISSING", "RULE", "SOURCE_UNAVAILABLE")
    case = cases[0]
    _require(
        _requirements(root, rule, case) == s.nre.sources.requirements,
        "REQUIREMENT_COVERAGE_MISSING",
    )
    wanted = set("root:" + row.clause.root_key for row in root.roots)
    for operation in case.operations:
        if operation.kind == "MAKE_CONSTRAINT":
            wanted.add("rule:" + case.id + ":" + operation.id)
    supplied = tuple(row.key for row in s.anchors)
    _require(
        len(set(supplied)) == len(supplied) and not (set(supplied) - wanted),
        "MBA_INCONSISTENT",
        "MBA",
    )
    _require(
        not (wanted - set(supplied)), "ANCHOR_COVERAGE_MISSING", "COVERAGE", "SOURCE_UNAVAILABLE"
    )
    _require(
        root.sources.request.temporal.kind in {"DAY", "WEEK"},
        "UNSUPPORTED_TEMPORAL_MAP",
        "RULE",
        "UNSUPPORTED",
    )
    ncheck = check_nutrition_resolution_independently(s.nre.sources, s.nre.estimate)
    _require(ncheck.decision == "CONSISTENT", "NRE_INCONSISTENT", "NRE")
    child = _basis(s, claimed)
    _child_failure(child)
    _require(
        s.nre.estimate.availability == "AVAILABLE", "NRE_UNAVAILABLE", "NRE", "SOURCE_UNAVAILABLE"
    )
    claims, trace = reconstruct_claims(root, rule, case, ss.request.precision, work)
    check_coverage(root, rule, case, claims, trace, work)
    active = {x.id for x in claims}
    coverage = []
    byanchor = {x.anchor_fingerprint: x for x in child.witnesses}
    for anchor in s.anchors:
        work.charge()
        operation = None if anchor.key.startswith("root:") else anchor.key.rsplit(":", 1)[1]
        witness = byanchor[anchor.anchor_fingerprint]
        coverage.append(
            v.PolicyClaimCoverageV2(
                anchor_key=anchor.key,
                anchor_fingerprint=anchor.anchor_fingerprint,
                root_key=anchor.root_key,
                operation_id=operation,
                descriptor=anchor.descriptor,
                layer=anchor.layer,
                disposition="RETAINED_ROOT"
                if operation is None
                else "ACTIVE_CLAIM"
                if operation in active
                else "UNSELECTED_PRECISION_BRANCH",
                claim_id=operation,
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
        support=_assignments(root, claims, s.nre.estimate, work),
        environment="TEST_ONLY",
    )


def check_policy_v2(retained_input, claimed_result):
    i, expected = None, None
    try:
        i = v.parse_policy_v2(retained_input, v.NutritionPolicyIntegrationInputV2)
        claimed = v.parse_policy_v2(claimed_result, v.NutritionPolicyResultV2, RESULT_BYTES)
        work, payload, outcome, diagnostics = PolicyWork(), None, "AVAILABLE_TEST_ONLY", ()
        work.reserve_control()
        try:
            work.tree(canonical(i))
            payload = _rebuild(i, claimed, work)
        except InvalidPolicy as exc:
            outcome = exc.outcome
            diagnostics = (_diagnostic(_Failure(outcome, exc.code, exc.stage)),)
        except _Failure as exc:
            outcome, diagnostics = exc.outcome, (_diagnostic(exc),)
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            IndexError,
            ArithmeticError,
        ) as exc:
            outcome = (
                "RESOURCE_EXCEEDED" if str(exc).startswith("RESOURCE_EXCEEDED") else "REJECTED"
            )
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
            expected = v.NutritionPolicyResultV2(
                **data, result_fingerprint=v.policy_v2_hash("result", data)
            )
            work.output(expected, RESULT_BYTES)
        except ValueError as exc:
            if not str(exc).startswith("RESOURCE_EXCEEDED"):
                raise
            data.update(
                payload=None,
                outcome="RESOURCE_EXCEEDED",
                diagnostics=(
                    _diagnostic(_Failure("RESOURCE_EXCEEDED", "RESOURCE_LIMIT", "SOURCE")),
                ),
            )
            expected = v.NutritionPolicyResultV2(
                **data, result_fingerprint=v.policy_v2_hash("result", data)
            )
            work.failure_output(expected, RESULT_BYTES)
        _require(outcome != "REJECTED" and expected == claimed, "POLICY_SEMANTICS_INCONSISTENT")
        report = _report(i, expected, True, ())
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, ArithmeticError):
        report = _report(i, expected, False, ("POLICY_SEMANTICS_INCONSISTENT",))
    v.parse_policy_v2(report, v.NutritionPolicyCheckV2, CHECK_BYTES)
    return report


def _report(i, expected, consistent, findings):
    return v.NutritionPolicyCheckV2(
        contract_version="nutrition-policy-check.v2",
        coverage="FULL_V2_SOURCE_JOINT_POLICY_CONTAINMENT",
        decision="CONSISTENT" if consistent else "INCONSISTENT",
        reconstructed_outcome=expected.outcome if expected else None,
        numerical_use="AVAILABLE_RETAINED_ONLY"
        if consistent and expected.outcome == "AVAILABLE_TEST_ONLY"
        else "NOT_ADMITTED",
        findings=findings,
        input_fingerprint=i.source_fingerprint if i else None,
        reconstructed_result_fingerprint=expected.result_fingerprint if expected else None,
        environment="TEST_ONLY",
        validation_authority="UNVERIFIED_TRANSPORT",
        source_origin="NOT_PROVED_OFFLINE",
        current_authorization="NOT_CLAIMED",
        scientific_correctness="NOT_CERTIFIED",
        production_admission="CLOSED",
        planner_ready=False,
        activation_ready=False,
    )


def check_policy_handoff_v2(handoff, expected_use):
    try:
        h = v.parse_policy_v2(handoff, v.NutritionPolicyHandoffV2, 48 * 1024 * 1024)
        use = v.parse_policy_v2(expected_use, v.PolicyV2Use, 64 * 1024)
        report = check_policy_v2(h.input, h.result)
        expected = v.PolicyV2Use(
            purpose="STRUCTURAL_TEST_ONLY_INSPECTION",
            subject=h.input.identity.subject,
            actor_user_id=h.input.identity.actor_user_id,
            selector_fingerprint=v.policy_v2_hash("selectors", h.input.basis_sources.selectors),
            precision_fingerprint=v.policy_v2_hash("precision", h.input.identity.precision),
            environment="TEST_ONLY",
        )
        _require(use == expected, "SOURCE_IDENTITY_MISMATCH")
        if h.retained_check is not None and h.retained_check != report:
            return _report(h.input, None, False, ("REPORT_NOT_AUTHORITY",))
        return report
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        return _report(None, None, False, ("POLICY_SEMANTICS_INCONSISTENT",))
