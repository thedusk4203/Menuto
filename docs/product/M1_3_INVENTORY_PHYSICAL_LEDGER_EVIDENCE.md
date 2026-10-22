# M1.3 Inventory Physical Ledger — evidence

Status: **APPROVED/FROZEN** by user on 2026-10-23.
Canonical freeze commit: `fef629965dd7401e27c98b5a0c523998a27017c4` (PR #59),
migrations0001–0007, **38 domain tables**. M1.1/M1.2 remain FROZEN at
`05382b6425a072433e38db99a1de101b577804a0`.

Implementation commit (complete code/tests): `6fafe913c3da33eba572fbaa477f1f82b4e84f96`.
Subsequent evidence-only commits record this exact implementation, without a self-referential SHA claim.
CI: **SUCCESS**, [Foundation checks #26](https://github.com/thedusk4203/Menuto/actions/runs/39815450061),
exact tested head `93a24750841dbdf63357f4db41434240aff03a21` (implementation + local evidence).
Python job `119952719751`, web job `119952720289`: all steps successful. Logs directly
confirm **688 passed**, 3 warnings, 28.57 seconds, PostgreSQL **18.4**, benchmark **22/22**.
This evidence-only update triggers a new final-head run; final head and postmerge results
are recorded in PR #59/checks and delivery, without claiming an unrun SHA passed.
[PR #59](https://github.com/thedusk4203/Menuto/pull/59).

## Delivered boundary

[Architecture review A–J](M1_3_INVENTORY_DOMAIN_REVIEW.md) was written before code.
0007 adds five tables (38 total): inventory_lots, inventory_lot_balances,
inventory_movements, inventory_reservations, inventory_reservation_releases.
0001–0006 are unchanged. No Recipe seal/version or Retail pricing semantics changed.
Retail public facade adds only a read-only mapping accessor, keeping Inventory away from
Retail ORM internals; exact mapping/product/ingredient composite FK retains provenance.

Frozen inventory-v1 contracts and InventoryService cover acquire, explicit consume,
discard, reconcile, reserve, full release, explicit expiry and read snapshots. There are
no business HTTP endpoints or UX. Cooked dish uses defined SERVING identity; prepared
component uses COOKED_G; raw remains AP_G/EP_RAW_G/COUNT. No conversion is inferred.

All history is append-only. A lot needs exact confirmed opening movement before commit.
Corrections append same-lot evidence with reason/actor, never rewrite old facts. Reserve
and release have separate tables and do not contribute material inflow/outflow. Cache
writes outside nested canonical trigger path fail, including direct SQL. Explicit actor
must be a household OWNER/EDITOR; source SYSTEM/AUTOPILOT/RETAIL_OBSERVATION is rejected.
This is not a complete HTTP authentication/authorization layer.

## Concurrency and chronology

DB inventory writers first take exclusive household advisory transaction fence. Readers
use shared fence for coherent multi-query snapshots. Every movement/reservation also locks
AND UPDATES per-lot balance/revision; this prevents stale REPEATABLE READ overdraw.
V1 serializes writes within a household, a deliberate correctness/performance trade-off.

Two 300g consumes from 500g: exactly one commits; other SQLSTATE23514. Two 300g reservations:
exactly one commits. Concurrent acquire retries preserve one opening/lot. Stale RR writer
fails SQLSTATE40001, not negative stock. Caller must rollback/retry entire transaction with
same idempotency key/body. Fingerprint includes concrete command type. Idempotency and
external source uniqueness are scoped per household/provider/event family.

Physical order uses occurred_at, canonical phase and server-assigned ledger_sequence;
recorded_at and sequence cannot be supplied as trusted client facts. Backdated insertion
before lot history and future physical claims fail. Current quantity is reconstructable
from primitive immutable events. Snapshot validates primitive replay, not a cached valid flag.
Unknown usable_until means unknown expiry, not a shelf-life guarantee for future planning.
Expiry leaves material remaining; allocatable is zero when unusable. Existing reservation
intent remains auditable until explicit release; no silent release or consumption.

## Verification

Final complete regression: **688 passed**, **313 real PostgreSQL tests**, **0 skipped/errors/failures**,
99.59 seconds. PostgreSQL **18.4** verified directly; test cluster STOPPED after checks.
One pre-existing Starlette/httpx deprecation warning. All 585 baseline tests
remain covered; 49 new inventory unit tests and 54 inventory PostgreSQL tests.
[Machine-readable results and frozen migration hashes](M1_3_INVENTORY_TEST_RESULTS.json).

Commands actually run from repository root (PYTHONPATH=apps/backend, PostgreSQL URL set):

```text
.venv/Scripts/python.exe -m pytest --tb=short --junitxml=.local/0007-tests.xml
.venv/Scripts/ruff.exe check .
.venv/Scripts/python.exe tools/check_architecture_baseline.py
.venv/Scripts/python.exe tools/check_import_boundaries.py
.venv/Scripts/python.exe tools/export_openapi.py --check
.venv/Scripts/python.exe tools/export_domain_contracts.py --check
.venv/Scripts/python.exe tools/generate_synthetic_fixtures.py --check
.venv/Scripts/python.exe -m benchmark.runner --output .local/0007-benchmark.json
npm run contracts:check
npm run typecheck:client
npm run test:client
npm run build:web
```

0001–0006 were byte-compared against freeze commit; all six BYTE_IDENTICAL. Their hashes
are recorded in the JSON evidence. No migrations or frozen recipe facts were rewritten.

Tests include direct SQL UPDATE/DELETE/TRUNCATE for all five tables, orphan lot rejection,
wrong household/actor, source identity, nonfinite/negative/excess precision quantities,
wrong basis/count identity, overdraw, future/backdated order, exact source mapping roundtrip,
reservation/release, source provider isolation, primitive snapshot corruption and races.

Migration 0006→0007→0006→0007 is tested twice on empty schema and populated pre-existing
Foundation data (lossless because no inventory history). With inventory populated,
downgrade to0006 fails closed and exact snapshot/history/revision survive rollback.
Alembic metadata drift and original complete upgrade/downgrade/upgrade fixture pass.

Ruff, architecture/import/export drift, 22 fixtures / 22 benchmark scenarios, generated
client drift/typecheck, 10 client tests and web production build are part of verification.
Benchmark remains synthetic harness evidence, NOT a production Planner V4 claim.

## Invariant coverage and deferred scope

INV-003/011/012/013/017/018/019 have physical foundation evidence; coverage remains PARTIAL,
not complete production execution/validation. INV-014/021/030 are not completed by this slice.

PhysicalInventorySnapshot and BatchFlowLinkDraft are DRAFT and not activation/execution
ready. Future orchestrator must bind inputs/outputs atomically, carry RecipeVersion/resolved
composition/yields and independent material checks. The draft link records identities and
exact movement references, not an implemented CookingBatch or proof of conservation.

Deferred: ActivePlan/PlanRevision, execution/assumption state machine, POSTFACT late-evidence
diagnostic ingestion, full Independent Validator, batch execution/production, nutrition,
OperationalState/PlanningState builders, HorizonBridgeResolver, planned stock, scheduled
reservation windows/partial fulfillment, storage transfer/cost basis, confidence history,
receipt/barcode production import, replan/optimizer/AI/behavior learning and inventory UX.
M1.3 is FROZEN within the scope/limitations above; no redesign or execution-readiness claim.
Postmerge freeze-point [CI SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/39817008268)
was reverified on 2026-10-23 for exact commit fef629965dd7401e27c98b5a0c523998a27017c4.
Review of the next canonical slice F is separate from this frozen implementation.
