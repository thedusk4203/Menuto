import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from benchmark.cpsat import SyntheticCpSatAdapter
from benchmark.reference import solve_reference
from benchmark.runner import FIXTURES, run_case
from benchmark.schema import Scenario, SolveConfig
from benchmark.verify import verify


@pytest.fixture
def base():
    return Scenario.model_validate_json((FIXTURES / "01-baseline.json").read_bytes())


@pytest.mark.parametrize("path", sorted(FIXTURES.glob("*.json")), ids=lambda p: p.stem)
def test_fixture_cpsat_agrees_with_independent_reference(path: Path):
    scenario = Scenario.model_validate_json(path.read_bytes())
    report = run_case(scenario, SyntheticCpSatAdapter(), SolveConfig(), 100_000)
    assert report["passed"], json.dumps(report, indent=2)


def test_analytically_known_package_optimum(base):
    # Two meals need at least 7 units for zero comfort loss; 5-unit packs cost 300.
    # One pack cannot cover demand. Two packs give the known optimum 600.
    actual = SyntheticCpSatAdapter().solve(base, SolveConfig())
    assert actual.status == "OPTIMAL"
    assert actual.objective == [0, 600]


def test_time_limit_is_never_infeasible(base):
    actual = SyntheticCpSatAdapter().solve(base, SolveConfig(time_limit_seconds=0))
    assert actual.status == "UNKNOWN_TIME_LIMIT"
    assert actual.selected == {}
    assert actual.objective is None


def test_checker_rejects_missing_procurement(base):
    actual = SyntheticCpSatAdapter().solve(base, SolveConfig())
    corrupted = actual.model_copy(update={"packages": {"food": 0}})
    assert "INSUFFICIENT_PROCUREMENT" in verify(base, corrupted)


def test_checker_rejects_wrong_objective(base):
    actual = SyntheticCpSatAdapter().solve(base, SolveConfig())
    corrupted = actual.model_copy(update={"objective": [0, 0]})
    assert "OBJECTIVE_MISMATCH" in verify(base, corrupted)


def test_checker_rejects_expired_and_overdrawn_stock(base):
    raw = base.model_dump()
    raw["horizon_days"] = 2
    raw["slots"][1]["day"] = 1
    raw["bands"] = [
        {
            "nutrient": "calories",
            "hard_min": 400,
            "hard_max": 600,
            "comfort_min": 450,
            "comfort_max": 500,
            "normalization_unit": 500,
        }
    ]
    raw["lots"] = [{"id": "old", "ingredient_id": "food", "units": 4, "expires_day": 0}]
    scenario = Scenario.model_validate(raw)
    actual = SyntheticCpSatAdapter().solve(scenario, SolveConfig())
    bad = actual.model_copy(update={"lot_use": {"old": {"s0": 4, "s1": 4}}})
    errors = verify(scenario, bad)
    assert "EXPIRED_LOT" in errors
    assert "LOT_OVERDRAW" in errors


def test_reference_limit_is_explicit_and_fails_correctness_gate(base):
    reference, reason = solve_reference(base, max_combinations=1)
    assert reference is None
    assert reason == "COMBINATION_LIMIT"
    report = run_case(base, SyntheticCpSatAdapter(), SolveConfig(), 1)
    assert "REFERENCE_NOT_CERTIFIED" in report["failures"]


def test_malformed_budget_contract_rejected(base):
    raw = base.model_dump()
    raw["budget_mode"] = "SPEND_LIMIT"
    with pytest.raises(ValidationError):
        Scenario.model_validate(raw)


def test_duplicate_candidate_id_rejected(base):
    raw = base.model_dump()
    raw["candidates"][1]["id"] = raw["candidates"][0]["id"]
    with pytest.raises(ValidationError):
        Scenario.model_validate(raw)
