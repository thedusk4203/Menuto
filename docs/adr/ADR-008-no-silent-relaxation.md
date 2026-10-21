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
INV-012. Also reinforces product principle `No silent relaxation`.
