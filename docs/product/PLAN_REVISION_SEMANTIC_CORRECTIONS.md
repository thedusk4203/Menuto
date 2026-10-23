# Plan/Revision Semantic Corrections — 0009

> Current decision: user APPROVED/FROZEN MTR-016 at `751a40e847dd2e664a6fe3667c272bc740a44e49` (0009,52 tables). READY/not-FROZEN statements below record the earlier submission, not the current freeze decision. Production authority remains fail-closed.
Date: 2026-10-23. Status: **READY FOR ARCHITECTURE/FREEZE REVIEW**, not FROZEN.
Canonical slice remains F / MTR-016. No CookingBatchExecution or next milestone work.

## Baseline and changes

Reviewed baseline: PR61 / merge `85945b1a288f7ae227dd662e8a348fc6e6d2b79d`.
Its 791 Python / 385 PostgreSQL-real tests and green postmerge CI are historical
foundation evidence, not proof of the two newly reported counterexamples.
Implementation commit: `869ea0efda33e59b44ce3fca413047d9754496e9`.
Remote PR/CI recorded below after verification.

No redesign of stable plan identity, revision/seal history, authorization or Inventory.
Published migrations0001–0008 stay unchanged. Forward migration **0009** adds exactly one
table, **shopping_demand_contributions**, plus proposal graph_version; **52 domain tables**.
Frozen migration SQL imports no ORM metadata and does not rewrite old immutable facts.

ShoppingDemandContributionIntent carries stable node identity, exact requirement,
exactly one meal/batch target, quantity/basis/item_ref and PLANNED/RETIRED status. Composite
FKs preserve proposal/household/plan ownership. Pydantic and PostgreSQL independently check
active contribution sum = requirement amount, measurement identity, active target and
parent, positive finite exact numeric values. Historical contribution nodes must be retained;
changing their parent requirement identity is rejected. Corrections retire/add facts.

## Scope enforcement

SINGLE_MEAL identifies exactly one changed culinary meal, including old and new allocation
targets and every active dependent meal of a changed batch. Reservation and contribution
deltas then expand both old/new target paths; unrelated, shared or orphan paths fail closed.
Checks run while sealing and again during publication, not only in the service.

Shopping amount-only changes may keep other meals' exact unchanged shares. Ingredient,
basis, item identity, need_by or status changes affect all contributing targets. Requirement
changes without explicit contribution ownership cannot use SINGLE_MEAL; legacy unknown
ownership is not guessed. The existing PROCUREMENT_ONLY and other wider scopes remain available for explicit broader changes.

Publish still retains unchanged reservations and fully releases/rebuilds affected ones
atomically, with no physical movement. Batch-target reservations are assembled after batch
rows, respecting their existing immediate FK; no FK relaxation or schema redesign is used.

## Historical cut line

The monotonic effective_from freezes advice by each node's own anchor:

| Intent | Anchor |
| --- | --- |
| Meal | scheduled_at |
| Planned batch | planned_at |
| Shopping requirement | need_by |

Anchor strictly before cut line means exact historical content is preserved; new backdated
nodes are rejected. Equality remains revisable. Contributions also respect their parent
requirement and target anchors; reservation intent inherits its target anchor. Earlier meal
allocations remain frozen. Future allocations from an already planned/cooked batch may
change without rewriting production. Materialization pins remain independent and stronger:
confirmed source intent remains pinned even before its scheduled time.

Time still creates no purchase, consumption or execution fact. Explicit Inventory release
remains a separate allocation operation; the correction never mutates Inventory history.

## Wire and migration compatibility

New graphs use **plan-intent.v2**, including the contribution collection and canonical hash.
Existing rows default to explicit plan-intent.v1; v1 serialization excludes the new field,
preserving exact graph/seal hashes and prior command fingerprints. V1 cannot hide contribution
facts. No backfill infers missing ownership. Existing root command/snapshot envelope versions
remain unchanged; their nested graph version explicitly distinguishes v1 and v2.

Migration tests build actual sealed v1 source facts at0008, upgrade, read/recompute the same
hash, downgrade losslessly and upgrade again. Empty and populated legacy paths are tested.
Downgrade fails closed if any contribution or v2 graph would lose provenance. It restores
the literal frozen0008 functions only on the permitted lossless path. Metadata drift is checked.

## Tests and evidence

Full local regression: **860 passed**, **436 PostgreSQL-real**, **69 new**
(18 unit + 51 PostgreSQL). **791 pre-existing tests retained**, zero skipped/errors/failures. No test
is deleted or weakened. Head assertions/metadata checks advance to0009 while historical
migration paths remain exercised. PostgreSQL tests use real18.4 and isolated databases.

New regression corpus includes:

- SINGLE_MEAL A change plus B reservation quantity/removal/retarget, for meal and batch targets.
- Unrelated shopping share, unchanged-total share transfer, aggregated need_by/status change,
  unrelated new requirement, and attempts to assign unknown old ownership locally.
- Shared batch reservation/contribution rejection; valid local A quantity delta preserves B.
- Wider-scope reservation replacement remains valid and physical movements stay unchanged.
- Batch planned before cut line but serving a future meal: time/source/retirement changes fail.
- Past shopping time/quantity/status and contribution redistribution fail; new backdated demand fails.
- Anchor equal to cut line remains revisable, and existing early materialization tests still pass.
- Direct SQL contribution sum/basis/FK/ownership/numeric checks, immutable UPDATE/DELETE/TRUNCATE,
  and late inserts after seal; raw SQL tests deliberately bypass ORM/Pydantic adapters.
- Frozen Pydantic contracts, v2 roundtrip/order-independent hash, v1 hash/retry compatibility.
- 0008→0009→0008→0009 empty and populated legacy roundtrips, populated loss guard and drift.

PRECOMMIT authorization remains fail-closed in production. Successful accepted-revision
tests reuse the explicit isolated DB-owner synthetic receipt fixture, not a real validator.

Other verification: Ruff; architecture/import boundaries; domain/OpenAPI/fixture exports;
22/22 synthetic benchmark (HARNESS_SMOKE_NOT_PLANNER_V4);10 client tests/typecheck; web build.
Exact completed results, commit and remote CI are recorded after execution below.

## Capability clarification and deferred work

The main A–J review now distinguishes target exact grounded cooking binding from implemented
default RecipeVersion + authored tier only. Selected rules, resolved planned ingredients and
binding fingerprint are deferred. They are mandatory before CookingBatchExecution; a version
and tier alone must not authorize raw consumption when authored variants exist.

Full fulfillment/actual Money, execution, projections, horizon resolution, production authority
and Independent Validator remain deferred. No new activation bypass, optimizer, AI or UX.
The correction is submitted for architecture/freeze review; it does not freeze MTR-016 itself.


## Completed verification

Local complete suite: `python -m pytest --junitxml=.local/0009-tests.xml --tb=short`,
PYTHONPATH=apps/backend, MENUTO_TEST_POSTGRES_URL set to the isolated PostgreSQL18.4
server. 860 passed in178.40s; one existing Starlette/httpx deprecation warning.
Ruff, architecture/import boundaries, exports/fixtures and Alembic metadata drift pass.
Benchmark22/22, client10/10 + typecheck/generated contracts, web build pass. Published
0001–0008 have no Git diff against the reviewed baseline. Migration0009 is frozen DDL/SQL.
Remote PR/CI and exact implementation commit are recorded after verification.


## Remote verification

[PR62](https://github.com/thedusk4203/Menuto/pull/62), evidence head
`7c47a31dee19faed4f21aa669af48c852ede991c`: **python + web SUCCESS** on
[CI run34](https://github.com/thedusk4203/Menuto/actions/runs/39838627343).
Remote logs confirm860 tests and22/22 benchmark; PostgreSQL service18.4 is real.
The subsequent evidence-only commit is checked again before merge. Postmerge CI is
verified and reported in the final delivery, not predicted in this historical record.
