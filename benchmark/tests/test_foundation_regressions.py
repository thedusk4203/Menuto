import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import benchmark.cpsat as solver_module
from benchmark.audit.independent_data_check import audit_solution_data
from benchmark.cpsat import SyntheticCpSatAdapter
from benchmark.reference import solve_reference
from benchmark.runner import FIXTURES, run_case
from benchmark.schema import Scenario, SolveConfig, StressScenarioPolicy


def load(name="01-baseline"):
    return Scenario.model_validate_json((FIXTURES / f"{name}.json").read_bytes())


@pytest.mark.parametrize("path", sorted(FIXTURES.glob("*.json")), ids=lambda p: p.stem)
def test_tags_describe_actual_final_fields(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    tags = set(data["tags"])
    assert ("no-budget" in tags) == (data["budget_mode"] == "NONE")
    assert ("target-budget" in tags) == (data["budget_mode"] == "TARGET")
    assert ("spend-limit" in tags) == (data["budget_mode"] == "SPEND_LIMIT")
    assert ("no-inventory" in tags) == (not any(lot["units"] for lot in data["lots"]))
    assert ("has-inventory" in tags) == any(lot["units"] > 0 for lot in data["lots"])
    price_states = {p["price_state"] for p in data["products"]}
    assert ("fresh-price" in tags) == (price_states == {"fresh"})
    assert ("stale-price" in tags) == (price_states == {"stale"})
    assert tags.intersection({"maintain", "high-protein", "calorie-deficit"}) == {
        data["goal_preset"]
    }
    count = len(data["candidates"])
    expected = (
        "small-catalog" if count <= 4 else "medium-catalog" if count <= 12 else "large-catalog"
    )
    assert tags.intersection({"small-catalog", "medium-catalog", "large-catalog"}) == {expected}
    assert f"candidate-count-{count}" in tags


def test_unused_stale_product_does_not_poison_feasible_solution():
    scenario = load("19-unused-stale-product")
    actual = SyntheticCpSatAdapter().solve(scenario, SolveConfig())
    reference, _ = solve_reference(scenario, 100_000)
    assert actual.status == reference.status == "OPTIMAL"
    assert actual.objective == reference.objective == [0, 600]
    assert actual.packages["unused"] == 0


def test_inventory_can_cover_demand_without_a_purchase_price():
    scenario = load("20-inventory-covers-missing-price")
    actual = SyntheticCpSatAdapter().solve(scenario, SolveConfig())
    assert actual.status == "OPTIMAL"
    assert actual.objective == [0, 0]
    assert actual.packages["food"] == 0


def test_unusable_alternative_is_not_a_global_data_rejection():
    scenario = load("22-stale-alternative")
    actual = SyntheticCpSatAdapter().solve(scenario, SolveConfig())
    assert actual.status == "OPTIMAL"
    assert actual.packages["stale_food"] == 0
    assert actual.selected["s0"] != "s0_c0"


def test_mutating_solver_evidence_gate_is_caught_by_reference_and_audit(monkeypatch):
    scenario = load("12-stale-price")
    monkeypatch.setattr(solver_module, "purchasable", lambda _product: True)
    report = run_case(scenario, SyntheticCpSatAdapter(), SolveConfig(), 100_000)
    assert report["result"]["status"] == "OPTIMAL"
    assert report["reference"]["result"]["status"] == "DATA_INSUFFICIENT"
    assert "REFERENCE_STATUS_DISAGREEMENT" in report["failures"]
    assert "PURCHASE_EVIDENCE_UNUSABLE" in report["failures"]
    assert report["passed"] is False


def test_data_auditor_catches_missing_purchase_price():
    scenario = load("18-missing-price")
    baseline = SyntheticCpSatAdapter().solve(load(), SolveConfig())
    assert "PURCHASE_PRICE_MISSING" in audit_solution_data(scenario, baseline)


def test_reference_and_auditor_do_not_import_solver_eligibility():
    root = Path(__file__).resolve().parents[2]
    for relative in ("benchmark/reference.py", "benchmark/audit/independent_data_check.py"):
        tree = ast.parse((root / relative).read_text(encoding="utf-8"))
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert "benchmark.cpsat" not in imports
        assert "benchmark.eligibility" not in imports


@pytest.mark.parametrize(
    "policy",
    [
        None,
        {"version": "test", "required_scenarios": []},
        {"version": "test", "required_scenarios": ["BASE"]},
        {"version": "test", "required_scenarios": ["BASE", "BASE"]},
        {"version": "test", "required_scenarios": ["BACKUP"]},
        {"version": "test", "required_scenarios": ["BASE", "BACKUP"]},
    ],
)
def test_spend_limit_requires_explicit_complete_policy(policy):
    raw = load("05-tight-budget").model_dump()
    raw["stress_policy"] = policy
    raw["stress_prices"] = {}
    with pytest.raises(ValidationError):
        Scenario.model_validate(raw)


def test_explicit_base_only_policy_is_valid_for_justified_fixed_pack_case():
    scenario = load("05-tight-budget")
    assert scenario.stress_policy.required_scenarios == ["BASE"]
    assert scenario.stress_policy.base_only_justification
    assert SyntheticCpSatAdapter().solve(scenario, SolveConfig()).objective == [0, 600]


def test_required_backup_is_enforced_but_optional_sensitivity_is_not_a_hard_constraint():
    raw = load("05-tight-budget").model_dump()
    raw["stress_prices"] = {"BACKUP": {"food": 400}, "OPTIONAL": {"food": 9999}}
    raw["stress_policy"] = {
        "version": "fixture-policy",
        "required_scenarios": ["BASE", "BACKUP"],
    }
    scenario = Scenario.model_validate(raw)
    assert SyntheticCpSatAdapter().solve(scenario, SolveConfig()).status == "PROVEN_INFEASIBLE"
    assert solve_reference(scenario, 100_000)[0].status == "PROVEN_INFEASIBLE"
    raw["budget_minor"] = 800
    feasible = Scenario.model_validate(raw)
    assert SyntheticCpSatAdapter().solve(feasible, SolveConfig()).status == "OPTIMAL"
    assert solve_reference(feasible, 100_000)[0].status == "OPTIMAL"


def test_base_price_cannot_be_overridden_by_a_conflicting_scenario():
    raw = load("05-tight-budget").model_dump()
    raw["stress_prices"] = {"BASE": {"food": 0}}
    with pytest.raises(ValidationError):
        Scenario.model_validate(raw)


def test_invalid_empty_policy_is_not_silently_normalized():
    with pytest.raises(ValidationError):
        StressScenarioPolicy(version="test", required_scenarios=[])
