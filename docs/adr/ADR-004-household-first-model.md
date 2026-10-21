# ADR-004 — Household-First Data, Single Tracked Nutrition Member in V1

**Status:** ACCEPTED  
**Date:** 2026-10-21

## Context
A user-centric schema would force later migrations for shared inventory/shopping. Conversely, individualized multi-member macro allocation would materially expand solver complexity and UX burden in V1.

## Decision
- Shared physical/financial resources are owned by `Household` from day one: inventory, shopping, kitchen, plans, cooking batches and budget defaults.
- Physiology/safety/personal data are owned by `HouseholdMember`.
- Every account starts with a default household/member.
- V1 has exactly one `TrackedMember` for individualized nutrition optimization.
- Canonical meal input is `MealParticipants`; derived `AttendanceScale` is only a coefficient.
- Participant allergy/diet constraints are intersected for a shared meal.
- `ConsumptionDemand` is separate from `BatchProduction`/`BatchAllocation`.

## Consequences
- Couples/small households affect package, expiry and batch quantities in V1 without multi-member macro optimization.
- Secondary-member personalized component allocation is a V2 concern.
- Plan ownership is household-scoped; actor/audit user IDs remain separate.

## Invariants
INV-003, INV-004, INV-007.
