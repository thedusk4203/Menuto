# F — Plan/revision foundation: implementation evidence

Date: 2026-10-23, Asia/Saigon. **READY FOR ARCHITECTURE/FREEZE REVIEW**, not FROZEN.
Canonical work item remains MTR-016; no milestone renumbering.

## Source and exact scope

Architecture-first baseline: main `e8eea4190623a989739f5dbb91f20bfbc9e546b3`, PR #60.
Frozen M1.3: `fef629965dd7401e27c98b5a0c523998a27017c4`.
Implementation commit: de669c63601522f00860fe4f4389860dbd90aefc. PR/CI: awaiting remote verification; recorded below when available.
[A–J review and implementation addendum](PLAN_REVISION_FOUNDATION_DOMAIN_REVIEW.md)
records decisions before implementation; no frozen architecture was reopened.

This delivers draft authoring plus guarded accepted-revision transaction machinery.
**Production PRECOMMIT authority is absent, so activation/publish fails closed.**
No application function mints authorizations or accepts a PASS boolean. Successful
publish tests seed explicit synthetic receipts by disabling the insertion trigger as
the isolated test database owner, then immediately restoring it. This fixture is not
an Independent Validator, production permission, or a substitute for source validation.

## Final table model

Migration **0008_plan_revision_foundation.py** adds 13 tables, **51 total domain tables**:

| Context | Tables | Ownership |
| --- | --- | --- |
| Planning | plan_workspaces | Household-owned stable plan identity; guarded head/counters |
| Planning | plan_proposals, plan_proposal_seals | Immutable complete relational intent and DB-computed content hash |
| Planning | plan_meal_intents, plan_meal_participants | Exact proposal/household/plan; stable logical meal identity |
| Planning | plan_reservation_intents | Allocation intent; no physical movement |
| Planning | plan_validation_authorizations | Immutable future authorization seam; insertion disabled |
| Planning | plan_revisions, plan_revision_reservations | Accepted history, exact parent/source, immutable reservation links |
| Planning | plan_materialization_links | Exact accepted source intent ↔ existing confirmed Inventory movement |
| Cooking | planned_cooking_batches, planned_batch_allocations | Default authored recipe/tier production intent and meal allocations |
| Shopping | shopping_requirement_intents | Quantitative demand with ingredient and measurement identity |

No JSONB graph persistence. Composite FKs bind owner, plan, exact proposal and stable
node identity. DB protects finite exact numeric storage, serving tiers, participant
ownership, allocation bounds, immutable seals/history and same-transaction assembly.
Current Working Graph is a coherent view selected by the accepted head, not a second
independently writable copy. Proposal generation is separate from revision numbering.
PlanRevisionSnapshot includes the immutable parent graph hash.

## Transactions and chronology

Writers take the frozen M1.3 household advisory fence, then the plan row lock, then use
Inventory public commands. Expected proposal generation and active revision implement
optimistic concurrency checks. READ COMMITTED competing writers cannot both publish N+1;
stale REPEATABLE READ fails with 40001. Retry the entire transaction on serialization
failure/deadlock with the same command key/body.

Idempotency returns the original immutable result before stale-head checks; a changed
payload using the same scoped key is rejected. Command/source identity is explicit.
Each orchestration command uses a savepoint; caller owns the outer commit/rollback.

Publishing atomically inserts the immutable revision, retains unchanged eligible
reservations, fully releases affected reservations, creates replacements and switches
the head. A deferred DB constraint rejects missing reservation effects even through
direct SQL. Reservations never alter physical quantity. Existing manual reservations
cannot silently be commandeered. Failure while replacing a reservation rolls back all
revision/head/release/command effects.

The explicit non-regressing effective_from freezes earlier advice without claiming
elapsed time proves execution. Confirmed materialization pins source production or the
meal's full allocation path even when confirmed before its scheduled time. Late source
links do not create a revision. Inventory facts remain household-owned and immutable.

## Regression and adversarial evidence

Local complete regression: **791 passed**, including **385 PostgreSQL-real**; **103 new**
(31 unit/import + 72 PostgreSQL), **688 pre-existing regressions** retained. No tests skipped, removed or weakened.
PostgreSQL: real **18.4**, isolated databases; local loopback fixture, not SQLite/mock.
Full command: `python -m pytest --junitxml=.local/0008-tests.xml --tb=short` with
`PYTHONPATH=apps/backend` and `MENUTO_TEST_POSTGRES_URL` set to the test server.

| Counterexample | Executable evidence |
| --- | --- |
| Local HOME recipe A→B | Retire old batch/allocation, add authored B, same stable meal/plan; replace reservation, no physical movement |
| Already purchased chicken | Retire future shopping demand; confirmed acquisition and lot remain |
| Already cooked batch | Existing prepared asset survives Tuesday allocation revision; source production cannot change |
| Two devices revise #4 | Exactly one #5; stale competitor fails without lost update |
| Late execution deviation | Explicit existing consumption link to revision0 after head1; head unchanged |
| Partial shopping | 1000g requirement vs 600g confirmed acquisition → 400g shortfall; no purchased boolean |
| Failure after releasing reservation | Head/revision/release/new-command all roll back |
| Manual reservation races revision | One wins, one fails; frozen Inventory quantity/allocation guards remain effective |
| Early confirmed meal | Allocation path cannot change even though scheduled_at is still future |
| Forged/stale authority | Production receipt insert fails; fixture wrong graph/frontier/deadline fails publish |
| SQL history mutation | 39 UPDATE/DELETE/TRUNCATE negative cases against populated rows across all 13 tables |
| SQL malformed authoring | Cross-household/member/tier/basis, negative/NaN/excess precision rejected; unsealed proposal cannot commit |
| Proposal/revision boundaries | Late child inserts blocked, content hash independently recomputed in DB; draft authoring has no stock effects |

Migration tests exercise **0007→0008→0007→0008** on empty and populated foundation
data where lossless. Populated plan/intent downgrade fails closed, preserving history.
Metadata drift uses Alembic compare_metadata. Published migrations0001–0007 are compared as unchanged Git blobs
against the M1.3 freeze commit; no mutable ORM metadata is imported by migration0008.

Other actual local checks:

- Ruff; architecture baseline; 16-context import boundary checker.
- New negative tests enforce planning→shopping contracts-only and no recursive contracts.
- Domain schema export `urn:menuto:domain:foundation:8`, OpenAPI and fixture drift checks.
- Synthetic benchmark **22/22**, `HARNESS_SMOKE_NOT_PLANNER_V4` only.
- Generated API contracts unchanged; client typecheck and **10 client tests pass**.
- Web TypeScript check and production Vite build pass.

Remote CI and exact commits are recorded below after verification.

## Files and contract surfaces

- `app/modules/planning/{contracts,models,public}.py`: root, immutable graph/seal,
  exact revision snapshots, history/head facade and existing Inventory boundary links.
- `app/modules/cooking/{contracts,models,public}.py`: authored tier production and allocation intent.
- `app/modules/shopping/{contracts,models,public}.py`: quantitative demand and draft coverage.
- `app/modules/execution/public.py`: application transaction orchestration only.
- `app/persistence/models.py`: registers the 13 new relational tables.
- `migrations/versions/0008_plan_revision_foundation.py`: frozen DDL/SQL with fail-closed downgrade.
- `tests/plan_fixtures.py`, `test_plan_contracts.py`, `test_postgres_plans.py`: new regression corpus.
- Existing migration tests only advance expected head/table set; prior negative assertions remain.
- `tools/check_import_boundaries.py`, `tools/export_domain_contracts.py`,
  `packages/contracts/domain.schema.json`: guarded new contract edge and versioned export.
- Review, blueprint, foundation status, invariant coverage, backlog, glossary and READMEs:
  current implementation scope and unfinished production gates.

## Invariant coverage and limitations

INV-003/004: household/participant identity; individual nutrition/safety resolution is not done.
INV-006: authored production tier and separate allocations, no inferred serving adjustment.
INV-011/012: requirements and elapsed time cannot create acquisition or consumption.
INV-017/019: immutable primitive intent/history and Inventory linkage, coherent handoff.
INV-021: partial receipt/hash/frontier/CAS seam only; full independent PRECOMMIT/POSTFACT
validation and authority security remain absent. INV-030: draft horizon handoff, no resolver.

Deferred explicitly:

- Production authority issuance/security, full source/policy/safety frontiers and resolved
  ValidationSubjectSnapshot. Stored receipt guards are not a complete production gate.
- Recipe substitutions/micro-adjustment selection in plan bindings; V1 foundation references
  only immutable default RecipeVersion + authored tier, with explicit planned servings.
- Full PurchaseFulfillment with actual Money, cross-requirement allocation and receipt import.
  ObservedAcquisitionCoverageDraft checks exact household/ingredient/basis and unique event
  identities; caller-selected evidence does not establish global fulfillment allocation.
- CookingBatchExecution, MealExecution state machine, actual produced ingredients/servings,
  batch conservation and PreparedFood UX. Materialization links only associate existing
  confirmed Inventory facts; they do not certify recipe execution or actual-spend correctness.
- Operational/Planning projections, assumptions, HorizonBridgeResolver, planner/optimizer,
  replan, AI, behavioral learning and full Independent Validator.

No production activation readiness, full execution readiness, full M0/M1 completion or
freeze is claimed. Stop at **READY FOR ARCHITECTURE/FREEZE REVIEW**.
