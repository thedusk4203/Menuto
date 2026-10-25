# MTR-046A — Reviewed Culinary Feature Assignment Implementation Evidence

Status: **IMPLEMENTED; LOCAL VERIFICATION PASS; NOT FROZEN**.

Authorized implementation baseline: `c1dcf48907fa4dcb1acc210acd15ceba670345f0` (PR #84).
Exact implementation/test/export commit: `b02c5aa6c74889c9f7c73200ef3925dc1a33337d`.
Verification date: 2026-10-25, Asia/Saigon. The following documentation commit does not change
that tested runtime. PR/head and exact merge/CI identities are reported in the delivery record;
remote gates are not claimed passed before they run.

## Architecture and actual ownership

The user approved the corrected [design](MTR_046A_CULINARY_FEATURE_ASSIGNMENT_DESIGN.md).
Catalog owns immutable Ingredient→PROTEIN review streams; Recipes owns companion culinary
classification, independently from sealed RecipeVersion aggregates. METHOD has one exact
RecipeVersion cooking-context key and no path selectors/children. FLAVOR/MAIN_PROTEIN use typed
authored path scopes, explicit tiers/choices/preparations/adjustment controls. No inferred labels,
methods, culinary equivalences or unsafe count-to-mass conversion are introduced.

Coverage is separate from positive assignment: COMPLETE means complete within a finite pinned
reviewed universe only. PARTIAL empty, COMPLETE empty, missing/retracted scope, outside universe
and an uncaptured term remain distinct. MAIN_PROTEIN requires positive explicit slot support
pinned to a current Catalog association review; association alone never designates a dish label.
A later association replacement/retraction makes fresh MAIN_PROTEIN results unresolved/stale;
old immutable captures still replay as-of-capture.

## Schema and aggregate protocol

New frozen-DDL forward migration: `0013_culinary_feature_assignments.py`, revision `0013`, parent
`0012`. PostgreSQL18/SQLAlchemy2/Alembic; no mutable ORM metadata is imported by the migration.
**13 tables added, 58 → 71 domain tables**:

- Catalog: ingredient_protein_frontier, ingredient_protein_streams, ingredient_protein_reviews,
  ingredient_protein_review_terms, ingredient_protein_assignments.
- Recipes: culinary_feature_frontier, culinary_feature_applicabilities,
  culinary_feature_applicability_slots, culinary_feature_applicability_tiers,
  culinary_feature_reviews, culinary_feature_review_terms, culinary_feature_assignments,
  culinary_feature_main_protein_support.

Immutable facts forbid UPDATE/DELETE/TRUNCATE. Only protected append triggers may advance
frontiers/heads. Assembly xid is database-authored, children require that same transaction,
counts are immutable, child inserts have capacity checks and deferred closure independently
reconstructs key/command hashes and validates full relational/source/structural/support rules.
No new seal tables, JSON persistence, old seal rewrite or trigger-disabling workaround.
Service receipts describe writes pending caller commit; a complete subject is captured only
from committed sources in a separate clean read-only transaction.

Tests include **raw SQL followed by actual COMMIT without calling a service finalizer**:
incomplete assembly and bad command hash fail; excess same-transaction insertion fails while
original complete facts can commit. Cross-transaction/stale-isolation late insertion, cache
spoofing and immutable-history tampering fail. Python/SQL identity parity includes Unicode
provenance and path controls. These prove the approved closure protocol within the existing
ordinary-writer threat model; superusers disabling triggers are outside that model.

## Transactions and capture

V1 writers require READ COMMITTED. Catalog writes fence Catalog only. METHOD/FLAVOR writes
fence Recipes only, without Catalog CAS/lock/hash/read. MAIN_PROTEIN fences Catalog before
Recipes and verifies pinned support. CAS/idempotency preserve actor+provider+payload identity;
retry resolves before stale-CAS checks. Same-dimension retire/register rekey is atomic, exact
pair replay only. Arbitrary mixed direct-SQL lock order may abort; deadlock-free global batching
is not claimed.

Capture requires clean read-only REPEATABLE READ/SERIALIZABLE and current canonical proposal
identity/hash. It receives dimensions only, not terms. METHOD-only needs no selected path;
FLAVOR/MAIN_PROTEIN require exact frozen binding and the existing independent grounding check.
It retains relevant complete registry/review histories, universe/assignment/support primitives,
immutable vocabulary and dimension-sensitive source frontier manifests.

Pure discovery and optional term resolution reparse the entire subject and recompute results.
Different queries share source bytes/hash. Unknown term IDs yield TERM_NOT_CAPTURED, never a
live lookup or false absence. Cached/constructed source/result tampering fails revalidation.
Hashes identify captured evidence, not trusted live completeness or authorization. Future
TOCTOU must recheck current proposal, Recipes source, pinned vocabulary and, only for
MAIN_PROTEIN, Catalog source/head under the commit boundary. No authority is implemented here.

## Actual verification

Final full local run on the exact implementation above:

| Gate | Actual result |
| --- | --- |
| Full Python + PostgreSQL | **1758 passed**, 0 failures/errors/skips, 163.90s |
| PostgreSQL-real subset (marker + XML case identity cross-check) | **728 passed** |
| Prior regression identities retained | **1626 /1626** |
| Additive tests | **132 =49 unit +83 PostgreSQL-real** |
| Database | PostgreSQL18.4, local isolated random test databases, actual network/transactions |
| Alembic metadata/schema | **0013 /71 tables**, drift check PASS |
| Empty up/down/up | PASS, including head→base→head via shared PG fixture |
| Existing populated foundation + empty new slice | **0012→0013→0012→0013 PASS**, preserved authored Recipe data |
| Populated new slice downgrade | FAIL CLOSED as required, all source history retained |
| Concurrency | One CAS revision winner; RR coherent old capture/proposal; fresh source/request checks; Catalog lock independence |
| Direct SQL | All13 tables reject UPDATE/DELETE/TRUNCATE; actual COMMIT rejects incomplete/bad-hash assembly; child/path/owner/kind/support negatives |
| SQL/Python canonical identity | METHOD and path key + full command hash parity, Unicode/provenance roundtrip |
| Frozen compatibility | **197 old definitions unchanged +29 additive**; old top-level function/class AST hashes and all0001–0012 migration hashes retained |
| Architecture / imports | PASS:30 invariants /11 ADRs /50 linked tasks,16 registered contexts; new pure-core negative imports |
| Ruff / contract + OpenAPI exports / synthetic fixtures | PASS; OpenAPI unchanged,22 fixture files verified |
| Synthetic benchmark | **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client tests / typecheck / generated contract checks | **10/10**, PASS |
| Web typecheck + build | PASS |
| Remote PR and exact post-merge CI | Recorded below/with final delivery after GitHub completes; no inference from local green |

Exact full command: `.venv/Scripts/python -m pytest --basetemp=.local/046a-complete
--junitxml=.local/046a-complete.xml`, with MENUTO_TEST_POSTGRES_URL set for local PostgreSQL18.
The XML confirms no skipped tests and retains all1626 prior identities. The only local warning
is the pre-existing FastAPI/Starlette httpx deprecation; no new failing condition is suppressed.
`.local` run logs/XML are local verification artifacts, not production data or checked-in source.

## Files and boundaries

Additive owner contracts/models/repositories under Catalog and Recipes; pure source matching
surface; Planning capture/preview and contracts; neutral canonical-byte helpers; explicit
composition-root registration; migration0013; domain export; pure-core import restrictions;
unit/real-PG/adversarial tests and fixed compatibility receipts. Existing live-head/table/bundle
expectations are updated to0013/71/bundle20; historical0011/0012 migration-path expectations are
preserved. No prior test is deleted or weakened.

## Explicitly deferred / no completion claim

MTR-046A is not self-frozen. Full MTR-040/041/046 remain incomplete. No multi-fingerprint exposure
integration, member profile derivation, novelty, TasteFit, utility/ranking, family identity,
allergen/diet classification, quick/high-protein tags, receipt import or Execution is started.
MTR-024/020B/021 remain BLOCKED. Existing RecipeGroundingValidator enforcement is reused, not
reimplemented; full MTR-026 is incomplete. No production curation permission/UI is claimed:
internal services receive a trusted curator actor; Household OWNER/EDITOR is not global curator
permission. No physical stock/reservation change and no new AP/EP/cooked conversion ownership.
PRECOMMIT remains fail-closed; classification captures have activation_ready=False and provide
no production TOCTOU authorization. POSTFACT remains diagnostic.

**READY FOR MTR-046A ARCHITECTURE/FREEZE REVIEW** after remote PR/exact-merge gates are verified in delivery.
