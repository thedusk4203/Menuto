"""EPI001–EPI064: executed through producer/checker interfaces, no source authority."""

import ast
import hashlib
import itertools
import json
import os
import re
import subprocess
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest
from app.domain.canonical import canonical_hash
from app.modules.policy import explicit_intent as producer
from app.modules.policy import explicit_intent_contracts as c
from app.modules.policy.explicit_intent_public import resolve_explicit_plan_intent_v1 as resolve
from app.modules.validation import explicit_plan_intent as checker
from explicit_plan_intent_fixtures import money, rehash, source, wire

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"


def positive(s):
    r = resolve(s)
    assert r.outcome == "AVAILABLE_TEST_ONLY", r
    report = checker.check_explicit_plan_intent_v1(s, r)
    assert report.decision == "CONSISTENT", report
    assert report.numerical_use == "NOT_ADMITTED"
    return r


def negative(s, outcome=None, consistent=True):
    r = resolve(s)
    assert r.outcome != "AVAILABLE_TEST_ONLY" and r.payload is None
    if outcome:
        assert r.outcome == outcome, r
    report = checker.check_explicit_plan_intent_v1(s, r)
    assert report.decision == ("CONSISTENT" if consistent else "NOT_CHECKABLE"), report
    assert report.numerical_use == "NOT_ADMITTED"
    return r


@pytest.mark.parametrize(
    "precision,cost,effort,kind",
    list(
        itertools.product(
            ("RELAXED", "STANDARD", "PRECISION"),
            ("LOW", "NORMAL", "HIGH"),
            ("MINIMAL", "NORMAL", "FLEXIBLE"),
            ("NONE", "TARGET", "SPEND_LIMIT"),
        )
    ),
)
def test_epi001_all_81_combinations(precision, cost, effort, kind):
    s = source()
    s.update(nutrition_precision=precision, cost_preference=cost, kitchen_effort=effort)
    s["budget"] = {"constraint": "NONE", "amount": None} if kind == "NONE" else money(kind)
    assert positive(s).payload.values.model_dump(mode="json") == {
        k: s[k] for k in ("nutrition_precision", "cost_preference", "kitchen_effort", "budget")
    }


def axis_change(axis, value):
    a = source()
    b = deepcopy(a)
    b[axis] = value
    left, right = positive(a).payload, positive(b).payload
    for key in ("nutrition_precision", "cost_preference", "kitchen_effort", "budget"):
        if key != axis:
            assert getattr(left.values, key) == getattr(right.values, key)
    for before, after in zip(left.axis_evidence, right.axis_evidence, strict=True):
        assert (before.value_fingerprint == after.value_fingerprint) == (
            before.axis != axis.upper()
        )
        assert before.input_fingerprint != after.input_fingerprint


def test_epi002_precision_orthogonal():
    axis_change("nutrition_precision", "RELAXED")


def test_epi003_cost_orthogonal():
    axis_change("cost_preference", "HIGH")


def test_epi004_effort_orthogonal():
    axis_change("kitchen_effort", "MINIMAL")


def test_epi005_budget_orthogonal():
    axis_change("budget", money())


def test_epi006_no_numerical_policy():
    r = positive(source())
    assert set(r.payload.values.model_dump()) == {
        "nutrition_precision",
        "cost_preference",
        "kitchen_effort",
        "budget",
    }
    assert not any(
        x in r.model_dump_json()
        for x in ("BudgetPressure", "calorie", "tolerance", "coefficient", "minutes", "utility")
    )


def test_epi007_none_not_zero_or_absence():
    assert positive(source()).payload.values.budget.amount is None


def test_epi008_target_is_intent_only():
    s = source()
    s["budget"] = money("TARGET", 123)
    assert positive(s).payload.values.budget.constraint == "TARGET"


def test_epi009_limit_not_feasibility():
    s = source()
    s["budget"] = money("SPEND_LIMIT", 123)
    assert positive(s).payload.values.budget.constraint == "SPEND_LIMIT"
    assert "feasible" not in positive(s).model_dump_json().lower()


def test_epi010_target_zero():
    s = source()
    s["budget"] = money()
    assert positive(s).payload.values.budget.amount.amount_minor == 0


def test_epi011_limit_zero():
    s = source()
    s["budget"] = money("SPEND_LIMIT")
    assert positive(s).payload.values.budget.amount.amount_minor == 0


@pytest.mark.parametrize("amount", [0, 1])
def test_epi012_none_with_amount_invalid(amount):
    s = source()
    s["budget"] = money("NONE", amount)
    assert negative(s).diagnostics[0].code == "BUDGET_INVALID"


@pytest.mark.parametrize("kind", ["TARGET", "SPEND_LIMIT"])
def test_epi013_non_none_requires_amount(kind):
    s = source()
    s["budget"]["constraint"] = kind
    assert negative(s).diagnostics[0].code == "BUDGET_INVALID"


def test_epi014_integer_boundary():
    s = source()
    s["budget"] = money(amount=2**63 - 1)
    positive(s)
    s["budget"] = money(amount=2**63)
    negative(s, "RESOURCE_EXCEEDED", False)


@pytest.mark.parametrize("amount", [-1, True, 1.0, "1"])
def test_epi015_no_numeric_coercion(amount):
    s = source()
    s["budget"] = money(amount=amount)
    r = resolve(s)
    assert r.payload is None and r.outcome == "INVALID_INPUT"
    report = checker.check_explicit_plan_intent_v1(s, r)
    assert report.decision == "CONSISTENT"
    assert report.numerical_use == "NOT_ADMITTED"


@pytest.mark.parametrize("currency", ["vnd", "VN", "VNDD", "€UR"])
def test_epi016_currency_exact(currency):
    s = source()
    s["budget"] = money(currency=currency)
    negative(s)


def test_epi017_currency_semantic_identity_not_support():
    a, b = source(), source()
    a["budget"], b["budget"] = money(currency="VND"), money(currency="ZZZ")
    assert positive(a).payload.semantic_fingerprint != positive(b).payload.semantic_fingerprint


@pytest.mark.parametrize(
    "axis", ["nutrition_precision", "cost_preference", "kitchen_effort", "budget"]
)
def test_epi018_null_axis_is_missing(axis):
    s = source()
    s[axis] = None
    r = negative(s, "MISSING_INPUT")
    assert r.input_fingerprint is not None and r.diagnostics[0].code == "AXIS_UNDECLARED"


@pytest.mark.parametrize("field", list(source()))
def test_epi019_absent_field_not_default(field):
    s = source()
    del s[field]
    assert negative(s, "MISSING_INPUT").diagnostics[0].code == "MISSING_FIELD"


@pytest.mark.parametrize("value", ["standard", "UNKNOWN", 1, True, []])
def test_epi020_invalid_axis_not_missing(value):
    s = source()
    s["nutrition_precision"] = value
    assert negative(s, "INVALID_INPUT").diagnostics[0].code == "AXIS_INVALID"


@pytest.mark.parametrize(
    "field,value",
    [
        ("request_id", "bad"),
        ("request_revision", True),
        ("request_revision", -1),
        ("declared_at", "2026-01-01"),
    ],
)
def test_epi021_context_invalid(field, value):
    s = source()
    s["context"][field] = value
    assert negative(s).diagnostics[0].code == "CONTEXT_INVALID"


def test_epi022_horizon_and_offset_normalization():
    a, b = source(), source()
    b["context"]["horizon"]["start"] = "2026-01-01T07:00:00+07:00"
    assert positive(a) == positive(b)
    b["context"]["horizon"]["end"] = b["context"]["horizon"]["start"]
    negative(b)


@pytest.mark.parametrize(
    "key",
    [
        "request_id",
        "household_id",
        "actor_user_id",
        "tracked_member_id",
        "request_revision",
        "declared_at",
        "horizon",
    ],
)
def test_epi023_context_identity_changes(key):
    s, t = source(), source()
    t["context"][key] = {
        "request_revision": 1,
        "declared_at": "2030-01-01T00:00:00Z",
        "horizon": {"start": "2027-01-01T00:00:00Z", "end": "2027-01-08T00:00:00Z"},
    }.get(key, "00000000-0000-0000-0000-000000000099")
    assert positive(s).input_fingerprint != positive(t).input_fingerprint


def test_epi024_future_metadata_not_authentication():
    s = source()
    s["context"]["declared_at"] = "2200-01-01T00:00:00Z"
    assert positive(s).source_authority == "UNAUTHENTICATED_DECLARATION"


def test_epi025_context_not_semantic_equality():
    s, t = source(), source()
    t["context"]["request_revision"] = 1
    a, b = positive(s).payload, positive(t).payload
    assert a.semantic_fingerprint == b.semantic_fingerprint
    assert [x.value_fingerprint for x in a.axis_evidence] == [
        x.value_fingerprint for x in b.axis_evidence
    ]


def test_epi026_full_source_identity():
    r = positive(source())
    assert all(e.input_fingerprint == r.input_fingerprint for e in r.payload.axis_evidence)
    assert len({e.axis for e in r.payload.axis_evidence}) == 4


def test_epi027_evidence_unique_order_before_hash():
    s = source()
    original = positive(s)
    for mutation in ("reverse", "duplicate", "missing"):
        r = wire(original)
        e = r["payload"]["axis_evidence"]
        if mutation == "reverse":
            e.reverse()
        elif mutation == "duplicate":
            e[1] = e[0]
        else:
            e.pop()
        assert checker.check_explicit_plan_intent_v1(s, rehash(r)).decision == "INCONSISTENT"


def test_epi028_replay_across_process_hash_seeds_and_environment():
    code = (
        "from explicit_plan_intent_fixtures import source;"
        "from app.modules.policy.explicit_intent import resolve_explicit_plan_intent_v1 as r;"
        "from app.modules.validation.explicit_plan_intent import "
        "check_explicit_plan_intent_v1 as c;"
        "x=r(source());print(x.model_dump_json());print(c(source(),x).model_dump_json())"
    )
    outputs = [
        subprocess.check_output(
            [sys.executable, "-B", "-c", code],
            cwd=ROOT,
            env={
                **os.environ,
                "PYTHONPATH": os.pathsep.join(
                    (
                        str(ROOT / "apps/backend"),
                        str(ROOT / "apps/backend/tests"),
                        str(ROOT),
                        os.environ.get("PYTHONPATH", ""),
                    )
                ),
                "PYTHONHASHSEED": seed,
                "NUTRITION_DEFAULT": "MALICIOUS",
            },
            text=True,
        )
        for seed in ("1", "987")
    ]
    assert outputs[0] == outputs[1]


def test_epi029_json_spelling_not_identity():
    s = source()
    assert positive(s) == positive(json.dumps(s, sort_keys=True, indent=2).encode())


def test_epi030_domain_separation_and_no_recursive_hash():
    s = source()
    r = positive(s)
    body = wire(r)
    digest = body.pop("result_fingerprint")
    assert digest == canonical_hash({"domain": "menuto.explicit-intent.result.v1", "body": body})
    assert digest != canonical_hash({"domain": "menuto.explicit-intent.input.v1", "body": body})


@pytest.mark.parametrize(
    "raw",
    [
        b'{"source":1,"source":2}',
        b"\xff",
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":1e3}',
        b'{"x":1.0}',
    ],
)
def test_epi031_strict_wire_parser(raw):
    negative(raw)


@pytest.mark.parametrize(
    "key", ["PlanningMode", "preset", "defaults", "week", "overrides", "learned", "BudgetPressure"]
)
def test_epi032_no_hidden_selection(key):
    s = source()
    s[key] = "MALICIOUS"
    assert negative(s).diagnostics[0].code == "UNKNOWN_FIELD"


@pytest.mark.parametrize("key", ["contract_version", "source", "environment"])
def test_epi033_unsupported_headers(key):
    s = source()
    s[key] = "UNREVIEWED"
    negative(s, "UNSUPPORTED")


def test_epi034_constructed_models_revalidated():
    model = c.ExplicitPlanIntentRequestV1.model_validate(source())
    positive(model)
    bad = model.model_copy(update={"cost_preference": "FORGED"})
    negative(bad)
    bad = model.model_copy(update={"hidden_default": True})
    assert resolve(bad).payload is None
    assert checker.check_explicit_plan_intent_v1(bad, positive(source())).decision != "CONSISTENT"


def test_epi035_unsafe_objects_never_execute_hooks():
    class Evil(dict):
        def items(self):
            raise AssertionError("must not execute")

        def __str__(self):
            raise AssertionError("must not execute")

    for value in (Evil(source()), (x for x in []), object()):
        assert resolve(value).payload is None
        assert (
            checker.check_explicit_plan_intent_v1(value, positive(source())).decision
            == "NOT_CHECKABLE"
        )
    cycle = []
    cycle.append(cycle)
    negative(cycle, "RESOURCE_EXCEEDED", False)


def test_epi036_encoded_byte_boundary():
    raw = json.dumps(source()).encode()
    exact = raw + b" " * (49152 - len(raw))
    positive(exact)
    negative(exact + b" ", "RESOURCE_EXCEEDED", False)


@pytest.mark.parametrize("kind", ["depth", "nodes", "container", "string", "key", "integer"])
def test_epi037_absolute_structure_limits(kind):
    s = source()
    if kind == "depth":
        v = 1
        for _ in range(9):
            v = [v]
        s["extra"] = v
    elif kind == "nodes":
        s["extra"] = [[[1] * 32 for _ in range(32)] for _ in range(3)]
    elif kind == "container":
        s["extra"] = list(range(33))
    elif kind == "string":
        s["extra"] = "a" * 257
    elif kind == "key":
        s["a" * 65] = 1
    else:
        s["budget"] = money(amount=10**19)
    negative(s, "RESOURCE_EXCEEDED", False)
    negative(json.dumps(s).encode(), "RESOURCE_EXCEEDED", False)


def test_epi038_work_budget_no_partial_success():
    reader = producer._Reader()
    reader.charge(4096)
    with pytest.raises(producer._Fault):
        reader.charge()
    budget = checker._Bounds()
    budget.work = 4096
    with pytest.raises(checker._Problem):
        budget.spend()


def test_epi039_claim_limit_is_not_checkable():
    s = source()
    report = checker.check_explicit_plan_intent_v1(s, b" " * 49153)
    assert report.decision == "NOT_CHECKABLE" and report.numerical_use == "NOT_ADMITTED"


def test_epi040_deterministic_failure_precedence():
    s = source()
    s.update(nutrition_precision=None, cost_preference="BAD", budget=money("NONE"))
    assert negative(s).diagnostics[0].path == "$.cost_preference"
    s["extra"] = "x" * 257
    assert negative(s, "RESOURCE_EXCEEDED", False).diagnostics[0].code == "STRUCTURE_LIMIT"


def test_epi041_fresh_positive_independent_check():
    positive(source())


@pytest.mark.parametrize("case", ["missing", "invalid", "unsupported", "malformed"])
def test_epi042_faithful_negative_consistent(case):
    s = source()
    if case == "missing":
        s["budget"] = None
    elif case == "invalid":
        s["budget"] = money("NONE")
    elif case == "unsupported":
        s["source"] = "PROFILE"
    else:
        s = b"{"
    negative(s)


def test_epi043_rehashed_changed_axis_rejected():
    s, forged = source(), source()
    forged["cost_preference"] = "HIGH"
    assert checker.check_explicit_plan_intent_v1(s, positive(forged)).decision == "INCONSISTENT"


@pytest.mark.parametrize(
    "change", [money("TARGET", 1), money("SPEND_LIMIT", 0), money(currency="USD")]
)
def test_epi044_rehashed_budget_substitution(change):
    s = source()
    forged = source()
    forged["budget"] = change
    assert checker.check_explicit_plan_intent_v1(s, positive(forged)).decision == "INCONSISTENT"


def test_epi045_forged_context_and_evidence():
    s = source()
    forged = deepcopy(s)
    forged["context"]["request_revision"] = 1
    assert checker.check_explicit_plan_intent_v1(s, positive(forged)).decision == "INCONSISTENT"
    claim = wire(positive(s))
    claim["payload"]["axis_evidence"][0]["source"] = "PROFILE"
    assert checker.check_explicit_plan_intent_v1(s, rehash(claim)).decision == "INCONSISTENT"


def test_epi046_tampered_hash_rejected():
    s = source()
    claim = wire(positive(s))
    claim["payload"]["semantic_fingerprint"] = "0" * 64
    assert checker.check_explicit_plan_intent_v1(s, rehash(claim)).decision == "INCONSISTENT"


def test_epi047_forged_positive_for_negative():
    s = source()
    s["budget"] = None
    claim = wire(positive(source()))
    claim["input_fingerprint"] = resolve(s).input_fingerprint
    assert checker.check_explicit_plan_intent_v1(s, rehash(claim)).decision == "INCONSISTENT"


def test_epi048_forged_negative_for_positive():
    bad = source()
    bad["nutrition_precision"] = None
    assert checker.check_explicit_plan_intent_v1(source(), resolve(bad)).decision == "INCONSISTENT"


def test_epi049_report_not_validation_proof():
    s = source()
    r = positive(s)
    report = checker.check_explicit_plan_intent_v1(s, r)
    assert report.decision == "CONSISTENT"
    assert checker.check_explicit_plan_intent_v1(s, report).decision == "INCONSISTENT"
    with pytest.raises(TypeError):
        checker.check_explicit_plan_intent_v1(s, r, report)


def test_epi050_coherent_source_replacement_not_authority():
    s = source()
    s["context"]["actor_user_id"] = "00000000-0000-0000-0000-000000000099"
    r = positive(s)
    assert r.source_authority == "UNAUTHENTICATED_DECLARATION"
    assert checker.check_explicit_plan_intent_v1(s, r).production_admission == "CLOSED"


def test_epi051_absent_primitives_not_checkable():
    report = checker.check_explicit_plan_intent_v1(None, positive(source()))
    assert report.decision == "NOT_CHECKABLE"


def test_epi052_checker_never_calls_producer(monkeypatch):
    s = source()
    r = positive(s)
    monkeypatch.setattr(
        producer,
        "resolve_explicit_plan_intent_v1",
        lambda *a: (_ for _ in ()).throw(AssertionError("oracle")),
    )
    monkeypatch.setattr(
        producer, "_interpret", lambda *a: (_ for _ in ()).throw(AssertionError("oracle"))
    )
    assert checker.check_explicit_plan_intent_v1(s, r).decision == "CONSISTENT"
    claim = wire(r)
    claim["payload"]["values"]["cost_preference"] = "HIGH"
    assert checker.check_explicit_plan_intent_v1(s, rehash(claim)).decision == "INCONSISTENT"


def test_epi053_static_direct_transitive_independence():
    from explicit_plan_intent_architecture_checks import verify_independence

    verify_independence()


@pytest.mark.parametrize(
    "key,value",
    [
        ("environment", "PRODUCTION"),
        ("planner_ready", True),
        ("activation_ready", True),
        ("production_admission", "OPEN"),
        ("numerical_use", "ADMITTED"),
        ("planner_ready", 0),
    ],
)
def test_epi054_no_taint_or_flag_promotion(key, value):
    s = source()
    claim = wire(positive(s))
    claim[key] = value
    assert checker.check_explicit_plan_intent_v1(s, rehash(claim)).decision == "INCONSISTENT"


def test_epi055_no_lease_or_numeric_policy():
    from app.modules.nutrition.policy_v2_contracts import PolicyV2Use

    r = positive(source())
    with pytest.raises(ValueError):
        PolicyV2Use.model_validate(wire(r))
    assert r.numerical_use == "NOT_ADMITTED" and not r.resolved_plan_policy_ready


def test_epi056_no_physiological_policy_claims():
    result = wire(positive(source()))
    assert not ({"hard", "goal", "comfort", "weekly", "measurement_basis"} & set(result))


def test_epi057_no_feasibility_or_activation():
    result = positive(source())
    assert result.planner_ready is result.activation_ready is False
    assert result.outcome == "AVAILABLE_TEST_ONLY"


def test_epi058_pure_modules_no_io_or_globals():
    from explicit_plan_intent_architecture_checks import verify_purity

    verify_purity()


def test_epi059_all_528_bodies_and_exact_nine_delta():
    from test_explicit_plan_intent_preflight import (
        test_preflight_exact_nine_names_and_virtual_delta_without_export_changes,
    )

    test_preflight_exact_nine_names_and_virtual_delta_without_export_changes()


def test_epi060_frozen_files_no_new_migration_or_persistence():
    for name in ("basis_compatibility", "policy_v2_compatibility"):
        proof = json.loads((FIXTURES / f"{name}.json").read_text())
        for file, digest in proof["frozen_files"].items():
            assert hashlib.sha256((ROOT / file).read_bytes()).hexdigest() == digest, file
    assert not list((ROOT / "apps/backend/migrations/versions").glob("0018*"))


def test_epi061_all_retained_identities_and_metadata_integrity():
    proof = json.loads((FIXTURES / "explicit_plan_intent_compatibility.json").read_text())
    assert len(proof["baseline_tests"]) == 4369
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-o", "addopts=", "--collect-only", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout[-2000:]
    current = {x for x in result.stdout.splitlines() if "::" in x and not x.startswith(" ")}

    def identity(node):
        # Four retained parametrizations generate UUID4 values during collection.
        # Keep module/function/parameter structure and multiplicity, as older guards do.
        return re.sub(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", "<UUID>", node)

    assert not (Counter(map(identity, proof["baseline_tests"])) - Counter(map(identity, current)))
    from explicit_plan_intent_architecture_checks import verify_metadata_patch

    verify_metadata_patch()


def test_epi062_no_content_or_authority_installation():
    for name in ("explicit_intent.py", "explicit_intent_contracts.py", "explicit_intent_public.py"):
        tree = ast.parse((ROOT / "apps/backend/app/modules/policy" / name).read_text())
        assert not any(
            isinstance(n, ast.ImportFrom)
            and n.module
            and n.module.startswith(("app.persistence", "app.modules.nutrition"))
            for n in ast.walk(tree)
        )


def test_epi063_governance_and_non_authority():
    r = positive(source())
    check = checker.check_explicit_plan_intent_v1(source(), r)
    for item in (r, check):
        assert item.production_admission == "CLOSED"
        assert not item.planner_ready and not item.activation_ready
    doc = (ROOT / "docs/product/MTR_008_EXPLICIT_REQUEST_PLAN_INTENT_BOUNDED_DESIGN.md").read_text()
    assert "issues #5/#6/#7 OPEN" in doc


def test_epi064_exact_bounded_public_surface():
    from app.modules.policy import explicit_intent_public

    assert explicit_intent_public.__all__ == ("resolve_explicit_plan_intent_v1",)
    assert not hasattr(explicit_intent_public, "admit")
    import inspect

    assert list(inspect.signature(resolve).parameters) == ["source"]
    assert list(inspect.signature(checker.check_explicit_plan_intent_v1).parameters) == [
        "source",
        "claimed_resolution",
    ]


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":0,"x":1,"later":"' + b"a" * 257 + b'"}',
        b'{"extra":' + b"[" * 9 + b"0" + b"]" * 9 + b"}",
        b'{"extra":[' + b"0," * 32 + b"0]}",
    ],
)
def test_epi037_epi040_wire_resources_before_semantic_or_duplicate_errors(raw):
    negative(raw, "RESOURCE_EXCEEDED", False)


def test_epi037_huge_integer_model_guard_before_stringification():
    s = source()
    s["budget"] = money(amount=1 << 100000)
    negative(s, "RESOURCE_EXCEEDED", False)


def test_epi034_claim_epoch_coercion_not_accepted():
    s = source()
    claim = wire(positive(s))
    # Pydantic alone could interpret epoch seconds as an AwareTime; wire protocol cannot.
    claim["payload"]["context"]["declared_at"] = 1767139200
    assert checker.check_explicit_plan_intent_v1(s, rehash(claim)).decision == "INCONSISTENT"
