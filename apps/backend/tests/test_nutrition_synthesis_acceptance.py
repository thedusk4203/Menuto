"""NPS033–120: TEST_ONLY finite semantics, hostile edits and frozen compatibility.

Synthetic retained-journal reauthoring below tests algebra, not database origin or
clinical correctness. PostgreSQL authority evidence is in the separate PG suite.
"""

import ast
import hashlib
import json
import re
import runpy
import subprocess
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.root_limits import check_structure
from app.modules.nutrition.synthesis import (
    admit_production_nutrition_policy,
    nutrition_policy_requirements,
    synthesize_nutrition_policy,
    validate_nutrition_policy,
)
from app.modules.nutrition.synthesis_journal import replay_synthesis_sources
from app.modules.validation.nutrition_policy import validate_nutrition_policy_independently
from nutrition_root_fixtures import alternate_test_constraint, amount
from nutrition_synthesis_fixtures import instruction, resolution
from nutrition_synthesis_pure_fixtures import (
    derive,
    hash_policy,
    hash_sources,
    reauthor_root,
    reauthor_rule,
    rehash_rule_records,
    remove_root_records,
    retained,
    retract_goal,
    weekly_sources,
    withdraw,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"


def independent(policy):
    return validate_nutrition_policy_independently(
        c.NutritionPolicyValidationInput(
            policy=policy, coverage="SYNTHESIS_SOURCE_AND_POLICY_SEMANTICS"
        )
    )


def mutate_policy(policy, mutate):
    body = canonical(policy)
    mutate(body)
    return hash_policy(body)


def mutate_rule(sources, mutate):
    return reauthor_rule(sources, lambda b: mutate(b["cases"][0]["operations"]))


def altered_root_constraint(sources, constraint):
    def change(primitive):
        changed = alternate_test_constraint(primitive, constraint)
        primitive.clear()
        primitive.update(changed)

    return reauthor_root(sources, change)


def authored_bound(sources, *, layer="GOAL_PROTECTION", which="upper", offset=1):
    def change(ops):
        op = instruction(
            "TEST_ONLY_adjusted",
            "AFFINE_SAME_UNIT",
            (which,),
            coefficient=dict(numerator=1, denominator=1),
            offset=dict(numerator=offset, denominator=1),
        )
        ops.insert(2, canonical(op))
        for item in ops:
            if item["kind"] == "MAKE_CONSTRAINT" and item["layer"] == layer:
                item["inputs"] = [op.id if ref == which else ref for ref in item["inputs"]]

    return mutate_rule(sources, change)


def source_goal(sources, direction):
    def change(primitive):
        next(r for r in primitive["sources"] if r["command"]["body"]["kind"] == "GOAL")["command"][
            "body"
        ]["direction"] = direction

    return reauthor_root(sources, change)


@pytest.mark.parametrize("case", [f"NPS{i:03d}" for i in range(33, 121)])
def test_source_bound_nutrition_acceptance(case):
    p = retained()
    s = p.inputs
    if case == "NPS033":
        assert validate_nutrition_policy(p) == p
        assert p.outcome == "AVAILABLE" and independent(p).decision == "CONSISTENT"
    elif case == "NPS034":
        result = derive(remove_root_records(s, "ASSESSMENT"))
        assert result.outcome == "UNAVAILABLE" and not result.claims
    elif case == "NPS035":
        observed = {}
        for assertion, expected in (
            ("OUT_OF_SCOPE", "UNSUPPORTED"),
            ("EXCLUDED", "INELIGIBLE"),
            ("UNDETERMINED", "UNKNOWN"),
        ):

            def change(primitive):
                next(
                    r for r in primitive["sources"] if r["command"]["body"]["kind"] == "ASSESSMENT"
                )["command"]["body"]["outcome"] = assertion

            result = derive(reauthor_root(s, change))
            assert (
                result.inputs.request.root.eligibility == expected
                and result.outcome == "UNAVAILABLE"
            )
            observed[expected] = result.reasons
        assert len(set(observed.values())) == 3
    elif case == "NPS036":
        result = derive(remove_root_records(s, "GOAL"))
        assert result.inputs.request.root.goal_direction is None
        assert result.inputs.request.root.goal_state == "ABSENT" and result.outcome == "UNAVAILABLE"
    elif case == "NPS037":
        result = derive(retract_goal(s))
        assert result.inputs.request.root.goal_state == "RETRACTED"
        assert result.inputs.request.root.goal_direction is None and not result.claims
    elif case == "NPS038":

        def change(primitive):
            primitive["request"]["subject"]["member_id"] = str(uuid4())

        with pytest.raises(ValueError):
            reauthor_root(s, change)
    elif case == "NPS039":
        raw = canonical(s)
        raw["request"]["root"]["roots"][0]["clause"]["constraint"]["upper"]["numerator"] += 1
        with pytest.raises(ValueError):
            synthesize_nutrition_policy(hash_sources(raw), p.resolution)
    elif case == "NPS040":
        root = p.inputs.request.root
        assert (
            root.policy_synthesis == "NOT_PERFORMED"
            and root.numeric_goal_protection == "NOT_SYNTHESIZED"
        )
        assert not root.planner_ready and not root.activation_ready
    elif case in {"NPS041", "NPS042"}:
        raw = canonical(s)
        field = "body_fingerprint" if case == "NPS041" else "publication_id"
        raw["request"]["selection"][field] = "f" * 64 if case == "NPS041" else str(uuid4())
        with pytest.raises(ValueError):
            replay_synthesis_sources(hash_sources(raw))
    elif case == "NPS043":
        missing = reauthor_rule(s, lambda b: b["cases"][0].update(direction="CUT"))
        assert derive(missing).reasons == ("RULE_CASE_MISSING",)

        def duplicate(b):
            b["cases"].append(deepcopy(b["cases"][0]) | dict(id="TEST_ONLY_ambiguous"))

        result = derive(reauthor_rule(s, duplicate))
        assert result.outcome == "CONFLICT" and result.reasons == ("RULE_CASE_AMBIGUOUS",)
    elif case == "NPS044":
        for field, value in (
            ("scope_version", "TEST_ONLY_wrong"),
            ("protocol_fingerprint", "f" * 64),
            ("root_provider_id", str(uuid4())),
        ):
            with pytest.raises(ValueError):
                derive(reauthor_rule(s, lambda b: b["applicability"].update({field: value})))
    elif case == "NPS045":
        result = derive(withdraw(s))
        assert result.outcome == "UNAVAILABLE" and result.reasons == ("RULE_WITHDRAWN",)
        stale = reauthor_rule(
            s,
            lambda b: b["effective"].update(
                start="2026-08-01T00:00:00Z", end="2026-08-02T00:00:00Z"
            ),
        )
        stale_body = canonical(stale)
        stale_body["records"][-1]["command"]["body"]["effective_at"] = "2026-08-01T00:00:00Z"
        assert derive(rehash_rule_records(stale_body)).reasons == ("RULE_OUTSIDE_EFFECTIVE_RANGE",)
    elif case == "NPS046":
        new = withdraw(s)
        assert derive(s).outcome == "AVAILABLE" and derive(new).outcome == "UNAVAILABLE"
        assert s.source_fingerprint != new.source_fingerprint
    elif case == "NPS047":
        raw = canonical(s)
        raw["records"] = raw["records"][:-1]
        with pytest.raises(ValueError):
            replay_synthesis_sources(hash_sources(raw))
        raw = canonical(s)
        raw["frame"]["absence_stream_keys"] = ["0" * 64]
        with pytest.raises(ValueError):
            replay_synthesis_sources(hash_sources(raw))
    elif case == "NPS048":
        raw = canonical(s)
        raw["grant_facts"] = []
        raw["frame"]["row_count"] -= len(s.grant_facts)
        with pytest.raises(ValueError):
            replay_synthesis_sources(hash_sources(raw))
    elif case == "NPS049":
        for kind in ("BMR", "TDEE", "SCRIPT", "CALLBACK", "NONLINEAR"):
            with pytest.raises(ValueError):
                mutate_rule(s, lambda ops: ops[0].update(kind=kind))
        with pytest.raises(ValueError):
            reauthor_rule(s, lambda b: b.update(language_version="UNREVIEWED_v9"))
    elif case == "NPS050":
        for refs in (["upper"], ["lower"]):
            with pytest.raises(ValueError):
                mutate_rule(s, lambda ops: ops[0].update(inputs=refs))
        with pytest.raises(ValueError):
            mutate_rule(s, lambda ops: ops.append(deepcopy(ops[0])))
    elif case == "NPS051":
        for value in (True, 1.0, "1"):
            with pytest.raises(ValueError):
                c.SynthesisRational(numerator=value, denominator=1)
        for num, den in ((2, 4), (0, 2)):
            with pytest.raises(ValueError):
                c.SynthesisRational(numerator=num, denominator=den)
    elif case == "NPS052":
        assert c.SynthesisRational(numerator=0, denominator=1).numerator == 0
        for missing in ("coefficient", "offset"):
            fields = dict(
                coefficient=dict(numerator=0, denominator=1),
                offset=dict(numerator=0, denominator=1),
            )
            fields[missing] = None
            with pytest.raises(ValueError):
                instruction("TEST_ONLY_zero", "AFFINE_SAME_UNIT", ("lower",), **fields)
    elif case == "NPS053":
        for num, den in ((2**128, 1), (1, 0)):
            with pytest.raises(ValueError):
                c.SynthesisRational(numerator=num, denominator=den)
        result = derive(authored_bound(s, which="lower", offset=-100))
        assert result.outcome == "CONFLICT" and "NEGATIVE_FINAL_AMOUNT" in result.reasons
    elif case == "NPS054":

        def mismatch(ops):
            next(o for o in ops if o["id"] == "goal")["temporal"]["period_id"] = (
                "TEST_ONLY_wrong_period"
            )

        result = derive(mutate_rule(s, mismatch))
        assert (
            result.outcome == "UNSUPPORTED"
            and "DESCRIPTOR_MISMATCH_BEFORE_ARITHMETIC" in result.reasons
        )
        with pytest.raises(ValueError):
            n.NutritionRootDescriptor.model_validate(
                canonical(p.hard_roots[0].clause.descriptor) | dict(unit="G")
            )
    elif case == "NPS055":
        assert p.hard_roots == s.request.root.roots
        assert validate_nutrition_policy(p).hard_roots == p.hard_roots
    elif case == "NPS056":
        result = derive(
            altered_root_constraint(
                s, n.NutritionRange(kind="RANGE", lower=amount(7), upper=amount(7))
            )
        )
        assert (
            result.hard_roots[0].clause.constraint.lower
            == result.hard_roots[0].clause.constraint.upper
        )
        assert "EMPTY_PROTECTED_INTERVAL" not in result.reasons
    elif case == "NPS057":
        for value, missing in (
            (n.NutritionMinimum(kind="MINIMUM", lower=amount(7)), "upper"),
            (n.NutritionMaximum(kind="MAXIMUM", upper=amount(13)), "lower"),
        ):
            result = derive(altered_root_constraint(s, value))
            assert not hasattr(result.hard_roots[0].clause.constraint, missing)
            assert result.outcome != "AVAILABLE"
    elif case == "NPS058":
        with pytest.raises(ValueError):
            n.NutritionGuidelineClause(
                root_key="TEST_ONLY_center",
                descriptor=p.hard_roots[0].clause.descriptor,
                interpretation="GUIDELINE_HARD",
                constraint=dict(kind="TARGET", center=amount(7)),
            )
        with pytest.raises(ValueError):
            instruction(
                "TEST_ONLY_fake_hard",
                "MAKE_CONSTRAINT",
                ("lower",),
                root_key=p.hard_roots[0].clause.root_key,
                constraint_kind="TARGET",
                layer="GOAL_PROTECTION",
                temporal=s.request.root.sources.request.temporal,
            )
    elif case == "NPS059":
        root = s.request.root
        body = next(
            r.command.body.guideline for r in root.sources.sources if r.command.body.kind == "DRAFT"
        )
        with pytest.raises(ValueError):
            n.NutritionGuidelineBody.model_validate(
                canonical(body) | dict(clauses=canonical(body.clauses) * 2)
            )
    elif case == "NPS060":
        assert derive(authored_bound(s)).outcome == "CONFLICT"
    elif case == "NPS061":
        from app.modules.nutrition.synthesis import subset

        assert not subset(
            n.NutritionMinimum(kind="MINIMUM", lower=amount(6)),
            n.NutritionMinimum(kind="MINIMUM", lower=amount(7)),
        )
        assert not subset(
            n.NutritionMaximum(kind="MAXIMUM", upper=amount(14)),
            n.NutritionMaximum(kind="MAXIMUM", upper=amount(13)),
        )
    elif case == "NPS062":

        def reverse(ops):
            next(o for o in ops if o["id"] == "goal")["inputs"] = ["upper", "lower"]

        result = derive(mutate_rule(s, reverse))
        assert result.outcome == "CONFLICT" and result.reasons == ("EMPTY_PROTECTED_INTERVAL",)
    elif case == "NPS063":
        result = derive(mutate_rule(s, lambda ops: ops.pop(-2)))
        assert result.outcome == "UNAVAILABLE" and result.reasons == (
            "GOAL_COMPARATOR_REFERENCE_UNAVAILABLE",
        )
    elif case in {"NPS064", "NPS065", "NPS066"}:
        direction = {"NPS064": "CUT", "NPS065": "MAINTAIN", "NPS066": "GAIN"}[case]
        changed = source_goal(s, direction)
        if direction != "MAINTAIN":
            assert derive(changed).outcome == "UNAVAILABLE"

        def authored(b):
            b["cases"][0]["direction"] = direction
            ops = b["cases"][0]["operations"]
            if direction == "MAINTAIN":
                next(o for o in ops if o["kind"] == "CHECK_DIRECTION")["comparator"] = "CONTAINS"
                return
            endpoint = "upper" if direction == "CUT" else "lower"
            delta = -1 if direction == "CUT" else 1
            numeric = instruction(
                "TEST_ONLY_goal_endpoint",
                "AFFINE_SAME_UNIT",
                (endpoint,),
                coefficient=dict(numerator=1, denominator=1),
                offset=dict(numerator=delta, denominator=1),
            )
            ops.insert(2, canonical(numeric))
            for op in ops:
                if op["kind"] == "MAKE_CONSTRAINT" and op["layer"] in {
                    "GOAL_PROTECTION",
                    "COMFORT",
                }:
                    op["inputs"] = [numeric.id if ref == endpoint else ref for ref in op["inputs"]]
                if op["kind"] == "CHECK_DIRECTION":
                    op.update(
                        inputs=["goal", endpoint],
                        comparator="UPPER_LT" if direction == "CUT" else "LOWER_GT",
                    )

        result = derive(reauthor_rule(changed, authored))
        assert result.outcome == "AVAILABLE" and independent(result).decision == "CONSISTENT"
    elif case == "NPS067":
        result = derive(
            mutate_rule(
                s,
                lambda ops: next(o for o in ops if o["kind"] == "CHECK_DIRECTION").update(
                    comparator="LOWER_GT"
                ),
            )
        )
        assert result.outcome == "CONFLICT" and result.reasons == (
            "REVIEWED_GOAL_DIRECTION_RELATION_FAILED",
        )
    elif case == "NPS068":
        result = derive(authored_bound(s, which="lower", offset=-1))
        assert result.outcome == "CONFLICT" and not result.claims
    elif case == "NPS069":
        forged = mutate_policy(
            p, lambda body: body["claims"][0]["subject"].update(member_id=str(uuid4()))
        )
        assert independent(forged).decision == "INCONSISTENT"
    elif case == "NPS070":
        result = derive(mutate_rule(s, lambda ops: ops[0].update(root_key="BODY_MASS")))
        assert result.outcome == "UNAVAILABLE"
        assert result.reasons == ("REVIEWED_REFERENCE_ENDPOINT_UNAVAILABLE",)
        for op in (
            next(r.command.body.rule for r in s.records if r.command.body.kind == "DRAFT")
            .cases[0]
            .operations
        ):
            assert op.kind != "PHYSIOLOGY_FORMULA"
        with pytest.raises(ValueError):
            instruction("TEST_ONLY_bmr", "BMR", ("lower",))
    elif case == "NPS071":
        assert all(
            r.clause.descriptor.temporal == s.request.root.sources.request.temporal
            for r in p.hard_roots
        )
        wider = weekly_sources(s)
        assert all(r.clause.descriptor.temporal.kind == "WEEK" for r in wider.request.root.roots)
        req = nutrition_policy_requirements(wider)
        weekly = synthesize_nutrition_policy(
            wider, resolution(req, wider.request.root, step=amount(1, 100))
        )
        assert weekly.outcome == "AVAILABLE" and independent(weekly).decision == "CONSISTENT"
        daily = [x for x in weekly.claims if x.layer == "DAILY_PROTECTION"]
        assert len(daily) == 7
        assert all(
            x.constraint.lower == amount(1) and x.constraint.upper == amount(13, 7) for x in daily
        )
        assert (
            next(x for x in weekly.claims if x.layer == "WEEKLY_CENTER").constraint.kind == "TARGET"
        )
    elif case in {"NPS072", "NPS073", "NPS075", "NPS076", "NPS077", "NPS078", "NPS080"}:
        wider = weekly_sources(s)

        def bad(b):
            ops = b["cases"][0]["operations"]
            if case == "NPS072":
                for op in ops:
                    if op["kind"] == "REVIEWED_PERIOD_PROJECTION":
                        op.update(kind="AFFINE_SAME_UNIT", temporal=None)
            elif case == "NPS073":
                removed = {
                    o["id"]
                    for o in ops
                    if o["kind"] == "MAKE_CONSTRAINT" and o["layer"] == "DAILY_PROTECTION"
                }
                b["cases"][0]["operations"] = [o for o in ops if o["id"] not in removed]
                b["cases"][0]["required_claims"] = [
                    k for k in b["cases"][0]["required_claims"] if k not in removed
                ]
            elif case in {"NPS075", "NPS080"}:
                next(o for o in ops if o["kind"] == "FINITE_PERIOD_SUM")["coefficients"] = [
                    dict(numerator=100, denominator=1)
                ] * 7
            elif case == "NPS076":
                next(o for o in ops if o["kind"] == "FINITE_PERIOD_SUM")["coefficients"] = []
            elif case == "NPS077":
                b["calendar_cells"][1]["interval"]["start"] = b["calendar_cells"][0]["interval"][
                    "start"
                ]
            elif case == "NPS078":
                b["calendar_cells"][1]["timezone"] = "TEST_ONLY_unretained_DST"

        if case == "NPS076":
            with pytest.raises(ValueError):
                reauthor_rule(wider, bad)
        else:
            result = derive(reauthor_rule(wider, bad), provide_resolution=False)
            assert result.outcome != "AVAILABLE"
            if case in {"NPS075", "NPS080"}:
                assert result.outcome == "CONFLICT" and result.reasons == (
                    "DAILY_AGGREGATE_INTERVAL_CONFLICT",
                )
    elif case == "NPS074":

        def bad(ops):
            next(o for o in ops if o["id"] == "daily")["temporal"]["interval"]["end"] = (
                "2026-09-03T00:00:00Z"
            )

        assert derive(mutate_rule(s, bad)).outcome == "UNSUPPORTED"
    elif case == "NPS079":
        wider = weekly_sources(s)
        changed = withdraw(wider, effective_at="2026-09-04T00:00:00Z")
        assert derive(changed).outcome == "UNSUPPORTED"
        assert derive(changed).reasons == ("CROSS_PUBLICATION_HORIZON_UNSUPPORTED",)
    elif case == "NPS081":
        raw = canonical(s)
        raw["request"]["precision"] = None
        raw["precision_witness"] = None
        result = derive(hash_sources(raw))
        assert result.outcome == "UNAVAILABLE" and result.reasons == (
            "PRECISION_SOURCE_UNAVAILABLE",
        )
    elif case == "NPS082":

        def bad(ops):
            numeric = instruction(
                "TEST_ONLY_narrow",
                "AFFINE_SAME_UNIT",
                ("upper",),
                coefficient=dict(numerator=1, denominator=1),
                offset=dict(numerator=-1, denominator=1),
            )
            ops.insert(2, canonical(numeric))
            next(o for o in ops if o["id"] == "relaxed")["inputs"] = ["lower", numeric.id]

        result = derive(mutate_rule(s, bad))
        assert result.outcome == "CONFLICT" and result.reasons == ("PRECISION_NESTING_FAILED",)
    elif case == "NPS083":
        # Even unselected RELAXED must remain contained when PRECISE is requested.
        raw = canonical(s)
        raw["request"]["precision"]["value"] = "PRECISION"

        def bad(ops):
            numeric = instruction(
                "TEST_ONLY_wide",
                "AFFINE_SAME_UNIT",
                ("upper",),
                coefficient=dict(numerator=1, denominator=1),
                offset=dict(numerator=1, denominator=1),
            )
            ops.insert(2, canonical(numeric))
            next(o for o in ops if o["id"] == "relaxed")["inputs"] = ["lower", numeric.id]

        assert derive(mutate_rule(hash_sources(raw), bad)).outcome == "CONFLICT"
    elif case == "NPS084":
        req = nutrition_policy_requirements(s)
        coarse = resolution(req, s.request.root, step=amount(100))
        result = synthesize_nutrition_policy(s, coarse)
        assert result.outcome == "UNAVAILABLE" and result.reasons == ("RESOLUTION_INSUFFICIENT",)
        assert result.hard_roots == p.hard_roots and not result.claims
    elif case == "NPS085":
        for field in ("package_size", "data_confidence", "band_inflation"):
            with pytest.raises(ValueError):
                c.NutritionResolutionInput.model_validate(canonical(p.resolution) | {field: 1})
    elif case == "NPS086":
        without = synthesize_nutrition_policy(s)
        assert without.outcome == "UNAVAILABLE"
        assert nutrition_policy_requirements(s) == without.requirements
    elif case == "NPS087":
        raw = canonical(p.resolution)
        for field, value in (
            ("requirements_fingerprint", "f" * 64),
            ("pool_fingerprint", "f" * 64),
            ("estimator_version", ""),
        ):
            raw = canonical(p.resolution) | {field: value}
            try:
                result = synthesize_nutrition_policy(s, raw)
            except ValueError:
                continue
            assert result.outcome != "AVAILABLE"
    elif case == "NPS088":
        forged = canonical(p.resolution)
        forged["facts"][0]["portion_step"]["numerator"] = 2
        assert synthesize_nutrition_policy(s, forged).outcome != "AVAILABLE"
    elif case == "NPS089":
        raw = canonical(p.resolution) | dict(facts=[])
        assert synthesize_nutrition_policy(s, raw).outcome != "AVAILABLE"
        assert "TEST_ONLY" in p.resolution.estimator_version
    elif case == "NPS090":
        from app.modules.nutrition.synthesis_public import nutrition_policy_reference

        handoff = nutrition_policy_reference(p, independent(p))
        assert handoff.policy == p and handoff.validation.policy_fingerprint == p.result_fingerprint
        wrong = canonical(independent(p)) | dict(policy_fingerprint="f" * 64)
        with pytest.raises(ValueError):
            nutrition_policy_reference(p, wrong)
    elif case == "NPS091":
        raw = canonical(s)
        raw["request"]["precision"]["source"] = "DEFAULT_STANDARD"
        with pytest.raises(ValueError):
            hash_sources(raw)
    elif case in {"NPS092", "NPS093", "NPS094", "NPS095"}:
        field = {
            "NPS092": "cost_preference",
            "NPS093": "budget_pressure",
            "NPS094": "kitchen_effort",
            "NPS095": "shared_tastefit",
        }[case]
        raw = canonical(s)
        raw["request"][field] = dict(numerator=1, denominator=1)
        with pytest.raises(ValueError):
            hash_sources(raw)
    elif case == "NPS096":
        identities = set()
        for value in ("RELAXED", "STANDARD", "PRECISION"):
            raw = canonical(s)
            raw["request"]["precision"]["value"] = value
            result = derive(hash_sources(raw))
            assert result.outcome == "AVAILABLE" and result.hard_roots == p.hard_roots
            assert [x for x in result.claims if x.layer != "COMFORT"] == [
                x for x in p.claims if x.layer != "COMFORT"
            ]
            identities.add(result.result_fingerprint)
        assert len(identities) == 3
    elif case == "NPS097":
        unavailable = derive(remove_root_records(s, "ASSESSMENT"))
        report = independent(unavailable)
        assert report.decision == "UNSUPPORTED"
        forged = mutate_policy(
            p, lambda body: body["inputs"]["request"]["root"].update(goal_state="ABSENT")
        )
        assert independent(forged).decision != "CONSISTENT"
    elif case == "NPS098":
        path = ROOT / "apps/backend/app/modules/validation/nutrition_policy.py"
        tree = ast.parse(path.read_text())
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert not any(
            name.endswith((".synthesis", ".synthesis_journal", ".root_resolution"))
            for name in imports
        )
        checker = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]
        assert checker(
            "from app.modules.nutrition.synthesis import synthesize_nutrition_policy",
            "app.modules.validation.nutrition_policy",
        )
    elif case in {"NPS099", "NPS100", "NPS101", "NPS102", "NPS103", "NPS104", "NPS105"}:

        def tamper(body):
            if case == "NPS099":
                body["inputs"]["grant_facts"] = []
            elif case == "NPS100":
                body["claims"] = [x for x in body["claims"] if x["layer"] != "DAILY_PROTECTION"]
            elif case == "NPS101":
                body["claims"][0]["layer"] = "WEEKLY_CENTER"
            elif case == "NPS102":
                body["claims"][0]["constraint"]["upper"]["numerator"] -= 1
            elif case == "NPS103":
                body["claims"][0]["descriptor"]["temporal"]["period_id"] = "TEST_ONLY_other"
            elif case == "NPS104":
                body["trace"][0]["amount"]["numerator"] += 1
            elif case == "NPS105":
                body["trace"] = []

        forged = mutate_policy(p, tamper)
        assert independent(forged).decision == "INCONSISTENT"
    elif case == "NPS106":
        report = independent(p)
        assert report.canonical_database_origin == "NOT_PROVED_OFFLINE"
        assert (
            report.current_authorization == "NOT_CLAIMED"
            and report.scientific_correctness == "NOT_CERTIFIED"
        )
    elif case == "NPS107":
        from app.modules.nutrition.synthesis_public import nutrition_policy_reference

        handoff = nutrition_policy_reference(p, independent(p))
        assert handoff.environment == handoff.policy.environment == "TEST_ONLY"
    elif case == "NPS108":
        with pytest.raises(ValueError, match="GATE_CLOSED"):
            admit_production_nutrition_policy(p)
        raw = canonical(p.resolution) | dict(environment="REVIEWED_PRODUCTION")
        assert synthesize_nutrition_policy(s, raw).outcome != "AVAILABLE"
    elif case == "NPS109":
        forbidden = {
            "sqlalchemy",
            "psycopg",
            "os",
            "pathlib",
            "socket",
            "requests",
            "datetime",
            "time",
        }
        for filename in ("synthesis.py", "synthesis_journal.py"):
            tree = ast.parse((ROOT / "apps/backend/app/modules/nutrition" / filename).read_text())
            imports = {
                node.module.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            }
            assert not imports & forbidden
        assert synthesize_nutrition_policy(s, p.resolution) == synthesize_nutrition_policy(
            s, p.resolution
        )
    elif case == "NPS110":
        before = json.loads((FIXTURES / "nutrition_synthesis_compatibility.json").read_text())[
            "baseline_definitions"
        ]
        now = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
        assert len(before) == 447 and len(now) > 447
        assert all(
            hashlib.sha256(json.dumps(now[k], sort_keys=True).encode()).hexdigest() == v
            for k, v in before.items()
        )
    elif case in {"NPS111", "NPS112", "NPS113", "NPS114"}:
        pins = json.loads((FIXTURES / "nutrition_root_compatibility.json").read_text())
        for name, expected in pins["frozen_files"].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
        own = json.loads((FIXTURES / "nutrition_synthesis_compatibility.json").read_text())
        for name, expected in own["root_and_migration_files"].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
        if case == "NPS111":
            baseline = json.loads(
                (FIXTURES / "nutrition_synthesis_baseline_tests.json").read_text()
            )
            assert len(baseline) == 3782
            collection = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q", "-o", "addopts="],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            current = [
                line.strip()
                for line in collection.stdout.splitlines()
                if line.startswith(("apps/", "benchmark/")) and "::" in line
            ]

            def normalized(identity):
                return re.sub(
                    r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", "<uuid>", identity
                )

            assert not Counter(map(normalized, baseline)) - Counter(map(normalized, current))
        assert p.inputs.request.root.numeric_goal_protection == "NOT_SYNTHESIZED"
        assert not p.planner_ready and not p.activation_ready
    elif case == "NPS115":
        migration = runpy.run_path(
            str(ROOT / "apps/backend/migrations/versions/0017_nutrition_synthesis_sources.py")
        )
        assert "INSERT" not in migration["TABLE_SQL"]
        assert "Production content gate CLOSED" in migration["FUNCTION_SQL"]
        assert all(
            e.environment == "TEST_ONLY"
            for r in s.records
            if r.command.body.kind == "DRAFT"
            for e in r.command.body.rule.evidence
        )
    elif case == "NPS116":
        migration = runpy.run_path(
            str(ROOT / "apps/backend/migrations/versions/0017_nutrition_synthesis_sources.py")
        )
        assert "CREATE ROLE" in migration["FUNCTION_SQL"] and "NOLOGIN" in migration["FUNCTION_SQL"]
        assert "VALUES" not in migration["TABLE_SQL"]
        with pytest.raises(ValueError):
            admit_production_nutrition_policy(p)
    elif case == "NPS117":
        assert validate_nutrition_policy(p) == synthesize_nutrition_policy(s, p.resolution)
        assert independent(p) == independent(c.NutritionPolicy.model_validate(canonical(p)))
    elif case == "NPS118":
        result = synthesize_nutrition_policy(s)
        assert result.outcome == "UNAVAILABLE" and not result.claims and not result.trace
        assert (
            result.hard_roots == s.request.root.roots
        )  # immutable source facts, not policy fallback
    elif case == "NPS119":
        with pytest.raises(ValueError):
            check_structure({"TEST_ONLY": 2**200})
        raw = canonical(s)
        raw["records"] *= 2000
        with pytest.raises(ValueError):
            replay_synthesis_sources(raw)
    elif case == "NPS120":
        report = independent(p)
        assert not p.planner_ready and not p.activation_ready
        assert not report.planner_ready and not report.activation_ready
        for extra in ("planner_ready", "activation_ready"):
            with pytest.raises(ValueError):
                c.NutritionPolicy.model_validate(canonical(p) | {extra: True})
    else:
        raise AssertionError("Unmapped acceptance case " + case)
