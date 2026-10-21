"""Extension seam for future production and reference planner adapters."""

from typing import Protocol

from benchmark.schema import Scenario, SolveConfig, SolveResult


class BenchmarkAdapter(Protocol):
    version: str

    def solve(self, scenario: Scenario, config: SolveConfig) -> SolveResult: ...
