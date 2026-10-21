# ADR-002 — Nutrition Policy Engine

**Status:** ACCEPTED  
**Date:** 2026-10-21

## Context
A single `target ± x%` rule is biologically and mathematically inadequate. Nutrients have asymmetric semantics; goal preservation differs from safety; discrete food portions limit achievable resolution; data uncertainty must not be double-counted by widening solver bands.

## Decision
`NutritionPolicyEngine` synthesizes policy in four layers:

1. **Guideline / Eligibility** — supported healthy-adult scope, adequacy/guideline rules and explicit unsupported cases.
2. **Goal Policy** — cut/maintain/gain direction, `GoalEnergyEnvelope`, goal protein floor where justified.
3. **Resolution & Temporal** — daily reasonableness, daily comfort, weekly centering and catalog/portion resolution.
4. **NutritionPrecision** — user preference may adjust comfort precision but cannot rewrite physiology/guideline constraints.

Nutrients may use `RANGE`, `MINIMUM`, `MAXIMUM` or `TARGET` semantics. Protein is primarily modeled as one-sided floor; discreteness should overshoot a floor rather than silently lower it.

## Consequences
- BMR is not used as a universal safe-intake floor.
- `DataConfidence` affects candidate eligibility/scoring, not band inflation.
- UI avoids fake precision and can show target zones.
- Numerical defaults remain versioned policy data and require evidence/benchmark review.

## Invariants
INV-001, INV-011.
