"""Reproducible runner with JSON output and nonzero exit on correctness failure."""

import argparse
import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

from benchmark.cpsat import SyntheticCpSatAdapter
from benchmark.protocol import BenchmarkAdapter
from benchmark.reference import solve_reference
from benchmark.schema import Scenario, SolveConfig
from benchmark.verify import verify

FIXTURES = Path(__file__).parent / "scenarios"


def run_case(
    scenario: Scenario,
    adapter: BenchmarkAdapter,
    config: SolveConfig,
    max_combinations: int,
) -> dict:
    start = perf_counter()
    result = adapter.solve(scenario, config)
    solve_ms = (perf_counter() - start) * 1000
    validation_errors = verify(scenario, result)
    start = perf_counter()
    reference, certification = solve_reference(scenario, max_combinations)
    reference_ms = (perf_counter() - start) * 1000
    reference_errors = verify(scenario, reference) if reference else []
    failures = list(validation_errors)
    failures += ["REFERENCE_" + error for error in reference_errors]
    if result.status != scenario.expected_status:
        failures.append("UNEXPECTED_STATUS")
    delta = None
    if reference and reference.status != result.status:
        failures.append("REFERENCE_STATUS_DISAGREEMENT")
    if reference and reference.objective is not None and result.objective is not None:
        delta = [a - b for a, b in zip(result.objective, reference.objective, strict=True)]
        if result.status == "OPTIMAL" and delta != [0, 0]:
            failures.append("WRONG_OPTIMUM")
    if reference is None:
        failures.append("REFERENCE_NOT_CERTIFIED")
    return {
        "scenario_id": scenario.id,
        "tags": scenario.tags,
        "passed": not failures,
        "failures": failures,
        "result": result.model_dump(),
        "metrics": {
            "solve_ms": solve_ms,
            "candidate_count": len(scenario.candidates),
            "phases_completed": result.phases_completed,
            "objective_vector": result.objective,
            "objective_names": ["synthetic_comfort_violation_bp", "purchase_cost_minor"],
            "inventory_units_used": sum(sum(x.values()) for x in result.lot_use.values())
            if result.objective is not None
            else None,
            "reference_ms": reference_ms,
            "objective_delta_vs_reference": delta,
        },
        "reference": {
            "certification": certification,
            "result": reference.model_dump() if reference else None,
        },
        "fixture_fingerprint": hashlib.sha256(
            scenario.model_dump_json().encode("utf-8")
        ).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", type=Path, default=FIXTURES)
    parser.add_argument("--output", type=Path, default=Path("benchmark/results/latest.json"))
    parser.add_argument("--time-limit", type=float, default=5.0, help="Seconds per CP-SAT phase")
    parser.add_argument("--reference-max-combinations", type=int, default=100_000)
    args = parser.parse_args()
    if args.reference_max_combinations <= 0:
        parser.error("reference-max-combinations must be positive")
    try:
        config = SolveConfig(time_limit_seconds=args.time_limit)
        paths = sorted(args.scenarios.glob("*.json"))
        if not paths:
            parser.error("No scenario JSON files found")
        scenarios = [Scenario.model_validate_json(path.read_bytes()) for path in paths]
        if len({s.id for s in scenarios}) != len(scenarios):
            parser.error("Duplicate scenario IDs")
        results = [
            run_case(s, SyntheticCpSatAdapter(), config, args.reference_max_combinations)
            for s in scenarios
        ]
        report = {
            "report_schema_version": "synthetic-benchmark-v1",
            "scope": "HARNESS_SMOKE_NOT_PLANNER_V4",
            "generated_at": datetime.now(UTC).isoformat(),
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "ortools": version("ortools"),
                "adapter": SyntheticCpSatAdapter.version,
                "config": config.model_dump(),
                "reference": {
                    "algorithm": "independent exhaustive+FEFO",
                    "max_combinations": args.reference_max_combinations,
                },
            },
            "production_launch_thresholds": None,
            "cases": results,
            "passed": all(r["passed"] for r in results),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"{sum(r['passed'] for r in results)}/{len(results)} scenarios passed; {args.output}")
        raise SystemExit(0 if report["passed"] else 1)
    except (ValueError, OSError) as error:
        print(f"Benchmark input/output error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
