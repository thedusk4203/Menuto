# Menuto Architecture Invariants — V1.2

**Status:** Canonical  
**Effective date:** 2026-10-21  
**Applies to:** Planner, Nutrition, Policy, Household, Recipe, Retail, Budget, API and UX semantics.

These invariants are guardrails, not implementation suggestions. A change that intentionally violates an invariant requires a superseding ADR.

## INV-001 — Planning preference must never masquerade as physiology
User cost/convenience preferences cannot silently weaken physiological/guideline constraints.

## INV-002 — Observed constraint must never masquerade as user preference
System-observed pressure (for example tight budget) is not proof of subjective user preference.

## INV-003 — Shared resource != shared physiology
Household owns shared physical/financial resources; HouseholdMember owns physiological and personal safety data.

## INV-004 — Aggregate demand must never erase individual safety constraints
Aggregation for portion/procurement must preserve participant allergy/diet restrictions.

## INV-005 — Recipe flexibility must be authored, not inferred
Allowed substitutions, quantity envelopes and compatibility are curated culinary facts, not optimizer inventions.

## INV-006 — Global optimization may choose among culinary possibilities; it may not create culinary possibilities
Global CP-SAT only selects grounded immutable candidates.

## INV-007 — Attendance != production
Meal participation/consumption demand and cooking batch production/allocation are separate concepts.

## INV-008 — Retail observations are evidence, not guarantees
Observed price/availability at planning time does not imply future shelf availability or checkout price.

## INV-009 — The planner optimizes procurement resilience, not merely observed price
Fragility and substitution coverage are legitimate quality dimensions even when they cost slightly more.

## INV-010 — Mathematical budget feasibility must not be presented as checkout certainty
Without locked price/stock, Menuto may claim policy-based planning feasibility, not guaranteed receipt total.

## INV-011 — A risk score is not a probability unless it has been calibrated as one
Heuristic score/reserve/confidence must never be labeled P90/90%/probability without empirical calibration.

## INV-012 — A hard user constraint may produce a relaxed alternative, but the alternative must never inherit the hard-feasible label without explicit user acceptance
Relaxed alternatives use a distinct status, are independently verified, and require explicit acceptance before activation.

## Enforcement guidance

- PRs that change planner semantics should cite affected invariant IDs.
- Tests should encode each invariant where it is mechanically testable.
- AI-generated explanation may paraphrase verified facts but cannot override invariant-derived statuses.
- A future exception must be documented in a new ADR that explicitly supersedes the affected invariant/ADR.
