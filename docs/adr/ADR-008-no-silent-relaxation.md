# ADR-008 — No Silent Relaxation and Verified Alternatives

**Status:** ACCEPTED  
**Date:** 2026-10-21

## Context
Optimizer timeout, weak prechecks or “almost feasible” alternatives must not silently weaken hard user constraints. A relaxed alternative can still be useful if clearly labeled, verified and explicitly accepted.

## Decision
- Hard constraints are never silently relaxed.
- `UNKNOWN`/timeout is not infeasibility evidence.
- Constraint Relaxation Advisor uses three steps: **conflict identification → elastic estimate → verification**.
- Every user-facing relaxation proposal is re-solved/verified with the proposed change and all other original hard constraints intact where applicable.
- Relaxed alternatives have distinct status/reason codes and cannot inherit hard-feasible labels.
- Plan activation after hard-constraint relaxation requires explicit user acceptance and records the accepted policy snapshot.

## Consequences
- Feasibility status is auditable.
- UI can offer useful near-feasible options without misrepresenting them.
- API/telemetry must preserve original constraint, proposed change, verification result and acceptance event.

## Invariants

INV-010, INV-029.

## V1.3 alignment — 2026-10-22

Invariant references use the canonical V1.3 numbering; V1.2 numbering is superseded. Accepted forced alternatives carry FORCED_CONFLICT_RESOLUTION and are quarantined from voluntary taste/context learning unless a separate direct preference signal is supplied (spec §8.4 seam 5; ADR-011).
