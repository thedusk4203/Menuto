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
INV-008, INV-009, INV-010, INV-011, INV-012.
