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

INV-001, INV-002, INV-010, INV-028.

## V1.3 alignment — 2026-10-22

Invariant references use the canonical V1.3 numbering; V1.2 numbering is superseded. The accepted decision is retained; closed-loop contracts are defined by ADR-009..011 and spec §8.4.
