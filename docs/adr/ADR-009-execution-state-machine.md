# ADR-009: Execution State Machine, Single ActivePlan Graph & Reversible Operational Assumptions

- **Status:** Accepted — 2026-10-22
- **Supersedes:** V1.2 open decision on Execution State Machine

## Context

Real-world execution diverges from a generated plan: partial shopping, substitutions, eat-out/skip events, cooking delays and leftovers. Mutating the original plan without history destroys baseline auditability; spawning detached plan primary keys for every change causes reference drift across shopping, reservations and multi-day batches. Requiring manual “Mark Cooked” for every meal creates refrigerator-accounting friction, while silently treating elapsed time as confirmed consumption corrupts truth.

## Decision

### 1. Single ActivePlan working graph + immutable revisions

Each activated horizon keeps a stable `plan_id`. Activation freezes `PlanRevision #0 (INITIAL_ACTIVATED_BASELINE)`. Local swap, intent-changing culinary adjustment and remaining-week replan create atomic immutable revision snapshots/diffs while updating only future/unexecuted nodes in the working graph. Materialized past/execution facts are not rewritten by later revisions.

### 2. PlanRevisionHistory != ExecutionLedger

Revision history records how Menuto's recommendation changed. Execution ledger records what happened in reality. A deviation in actual cooking is not automatically a plan revision.

### 3. Three state views

- `ConfirmedState`: explicit evidence only.
- `OperationalState`: confirmed facts + reversible operational assumptions used by Today/Expiry/repair.
- `PlanningState`: reconciled/resolved snapshot used by Planner.

### 4. Physical food lifecycle

Confirmed purchase materializes household `InventoryLot`. `CookingBatchExecution` consumes raw inventory and creates `PreparedFoodLot` tracked in servings. `COOKED != CONSUMED`; batch production/allocation/meal consumption are distinct.

### 5. Reversible optimistic autopilot

Elapsed time never mutates confirmed reality. If an active home meal is due, inputs are operationally available and no conflicting shortfall/revision exists, Menuto may create `AUTOPILOT_ASSUMED` provisional consume/batch/leftover events. Corrections create compensating reversal entries rather than deleting history. Assumption dependency chains cascade reversals; contradiction with confirmed child state yields `EXECUTION_CONFLICT`.

Autopilot cannot create purchases, actual prices, discard events, hard-constraint acceptance, confirmed behavioral labels or irreversible replan.

### 6. Local-first impact handling

`ExecutionImpactAnalyzer` returns `NONE | LOCAL_REPAIR | REPLAN_RECOMMENDED | REPLAN_REQUIRED`, using local adjustment/substitution/reschedule/swap before remaining-week reoptimization.

### 7. Cross-horizon bridge

When a future horizon is generated before the active horizon ends, `HorizonBridgeResolver` chronologically projects remaining commitments to `T_start`, producing opening assets and provisional exposure without double-counting raw reserved inputs and their future prepared outputs.

## Alternatives considered

- In-place plan mutation without baseline snapshots — rejected: erases planned-vs-actual history.
- New plan primary key for every swap/replan — rejected: fragments active shopping/batch references.
- Blocking manual confirmation for every meal — rejected: excessive friction and broken leftovers when user forgets.
- Time-passed equals truth — rejected: violates confirmed-state integrity.

## Consequences

- Stable references for active week.
- Zero-tap compliant happy path without false confirmed reality.
- More explicit event/projection/reversal contracts and concurrency requirements.
- Reconcile remains necessary when assumption debt becomes material.

## Invariants

`INV-011`, `INV-012`, `INV-013`, `INV-014`, `INV-030`.

## V1 boundary

Manual/receipt-assisted purchase confirmation, exception-only meal correction, one-tap reconcile, prepared leftovers and remaining-week replan. No passive sensor-based meal detection required.
