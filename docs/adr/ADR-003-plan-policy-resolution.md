# ADR-003 — Orthogonal Plan Policy Resolution

**Status:** ACCEPTED  
**Date:** 2026-10-21

## Context
`BALANCED | BUDGET_FIRST | CONVENIENCE_FIRST | STRICT_NUTRITION` forces orthogonal user needs into mutually exclusive boxes and couples unrelated solver parameters.

## Decision
No canonical `PlanningMode` enum exists in domain/solver. `PlanPolicyResolver` combines independent domains:

- `NutritionPrecision`;
- `CostPreference`;
- `KitchenEffort` + optional `DailyAvailability`;
- explicit budget contract: `SPEND_LIMIT | TARGET | NONE`;
- system-derived `BudgetPressure` is separate from user preference.

Profile defaults and per-plan situational overrides are merged into a versioned `ResolvedPlanPolicy`. UI presets may exist only as shortcuts that expand into these fields.

## Consequences
- A user can be strict on both budget and nutrition while also preferring minimal prep.
- Tight budget may trigger a recommendation but not silently change `CostPreference`.
- Chips like “tuần này bận” override only relevant fields and do not rewrite profile defaults.

## Invariants
INV-001, INV-002, INV-012.
