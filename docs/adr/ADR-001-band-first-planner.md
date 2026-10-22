# ADR-001 — Band-First Planner Architecture

**Status:** ACCEPTED  
**Date:** 2026-10-21

## Context
Point-target nutrition followed by tight epsilon locks can starve package-fit and cooking-batch solutions. Pure weighted utility obscures trade-offs across unlike units. Menuto also needs predictable timeout semantics and a structure that preserves human usability after economic optimization.

## Decision
Planner V4 uses:

1. **Stage 0 — Hard feasibility:** eligibility, participant safety, inventory validity, procurement rules and `SPEND_LIMIT` stress scenarios.
2. **Stage 1 — Comfort + Structural Economics:** minimize normalized comfort-band violation, then economic loss including purchase, expired waste, risky/awkward carryover and procurement fragility. CookingBatch variables exist here.
3. **Stage 2 — Human Utility:** within approved nutrition/economic tolerances, optimize adherence, diversity, preference, schedule fit, batching quality and center drift/stability.
4. **Local refinement:** recipe structure stays frozen; bounded culinary quantity adjustment may reduce awkward remainder and must be revalidated.

## Consequences
- No 7-phase default lexicographic chain.
- No point-target-first nutrition optimization.
- Weekly centering prevents systematic edge-hugging.
- Timeout/UNKNOWN never implies infeasibility.
- Candidate generation and benchmark quality become first-class dependencies.

## Rejected alternatives
- One global weighted sum over nutrition/cost/usability.
- Point target → epsilon → economics → usability.
- Free-form quantity mutation inside the global solver.

## Invariants

INV-001, INV-006, INV-009, INV-010.

## V1.3 alignment — 2026-10-22

Invariant references use the canonical V1.3 numbering; V1.2 numbering is superseded. Local quantity refinement preserves serving-count semantics and is precommit validated (spec §8.4 seam 1; ADR-010).
