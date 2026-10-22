# ADR-007 — `SPEND_LIMIT` and Deterministic Robust Budget Scenarios

**Status:** ACCEPTED  
**Date:** 2026-10-21

## Context
Worst-case sum is overly conservative; a flat 10% buffer ignores basket-specific evidence; `γ × price spread` is not a calibrated P90 and can ignore correlated category/store risk.

## Decision
Budget contract values are `SPEND_LIMIT | TARGET | NONE`.

For `SPEND_LIMIT`, V1 uses versioned deterministic stress scenarios generated from retail evidence, for example:

- `BASE`;
- `ADVERSE_WEIGHT`;
- `BACKUP`;
- `CATEGORY_STRESS`.

A plan is `WITHIN_LIMIT_ROBUST` only if every required scenario satisfies the user limit. If only expected/base spend fits, the result is `EXPECTED_WITHIN_LIMIT_ONLY` and is a relaxation candidate, not a hard-feasible plan.

No `P90`, probability or guaranteed-checkout claim is made until a model has been empirically calibrated/backtested with actual outcomes.

## Consequences
- Correlated category/store stress can be represented explicitly.
- CP-SAT remains linear because scenario coefficients are resolved before model construction.
- User-facing text says “within limit under current planning/risk policy”, not guaranteed receipt total.
- Receipt-vs-plan data becomes a calibration asset for future stochastic/quantile models.

## Invariants

INV-007, INV-008, INV-009, INV-010.

## V1.3 alignment — 2026-10-22

Invariant references use the canonical V1.3 numbering; V1.2 numbering is superseded. Mid-week revision cost for every required scenario is ConfirmedActualSpend(t) + StressScenarioSpend_s(RemainingUnfulfilled(t)). Fulfilled purchases are sunk facts, never re-stressed or omitted (spec §8.4 seam 2).
