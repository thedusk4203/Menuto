# MTR-041D — RepeatPenalty interpretation implementation evidence

Status: IMPLEMENTED / local verification PASS / NOT FROZEN.
Baseline59cc0a48b52addc5c7d612fae6b81b0681e90a00, PR #80 architecture approval.
Implementation commit and CI are recorded after verification below.
[Architecture](MTR_041D_REPEAT_PENALTY_REVIEW.md).

Schema:0012 /58 domain tables. No migration;0001–0012 unchanged.
Frozen040A/041A/B/C unchanged. Full040/041 incomplete;024/020B/021 BLOCKED;
Execution NOT STARTED; PRECOMMIT fail-closed.

## Scope and exact claims

Five additive frozen/extra-forbid contracts and one pure API. Fully revalidated source→041B→041C
chain, explicit AS_OF_CAPTURE versioned policy, positive unit penalty, only
SUM_RETAINED_OCCURRENCES. Exact GCD-reduced integer rational arithmetic in named policy units;
no float/rounding/quantization or probability. Each contribution retains source and policy.
Empty→None, witnessed zero→exact0 with provenance. Recompute all output; no trusted cache.
No DB persistence or new source truth. Bundle19 retains192 old definitions plus5 additive.

## Verification record

Focused unit/adversarial tests and real-PG capture/concurrency tests added. Initial focused
checks caught two test expectations: nested unordered facts require canonical roundtrip comparison;
separate captures can have distinct captured_at despite equal source frontiers. Those expectations
were corrected without modifying frozen runtime. No full-suite pass is claimed until recorded.

## Deferred / not claimed

Global RepeatPenalty/history, novelty, TasteFit, member/shared aggregation, ranking, portfolio role,
Stage-2 utility/weights, optimizer, accepted/confirmed/consumption evidence, cross-horizon bridge,
Execution and production PRECOMMIT remain unavailable. No default production penalty parameters,
cap/saturation, generic aggregation DSL or retrospective mode. Policy units are not automatically
comparable across policies. No self-freeze or next milestone implementation.


## Local gates already completed

- ruff check .: PASS.
- tools/check_architecture_baseline.py: PASS,30 invariants/11 ADRs/50 linked tasks.
- tools/check_import_boundaries.py: PASS,16 contexts and independent Learning/Validation.
- tools/export_openapi.py --check: PASS (OpenAPI unchanged).
- tools/export_domain_contracts.py --check: PASS; bundle19,197 definitions.
- tools/generate_synthetic_fixtures.py --check: PASS,22 fixtures.
- menuto-benchmark --output .local/repeat-penalty-benchmark.json:22/22 PASS,
  HARNESS_SMOKE_NOT_PLANNER_V4 (not optimizer correctness evidence).
- npm run contracts:check; npm run typecheck:client: PASS.
- npm run test:client:10/10 PASS; npm run build:web: PASS.
- AST compatibility vs59cc0a4:26 old Learning contract/helper definitions and4 old
  public functions unchanged. All192 previous exported definitions structurally identical,
  plus5 additive. Existing migration files unchanged.
- Alembic graph/registered metadata:head0012,58 tables; no new ORM or schema persistence.

New tests cover typed unbounded/reduced penalty amounts, rational equivalence, positive explicit
policy base, large integers under Decimal precision2, supported operator only, policy identity
and cutoff, full nested model_construct/copy revalidation, tampered contributions/retention/
witness/total/unit/outcome, foreign query identities, immutable result and scope/claim rejection.
Real-PG tests cover read-only canonical ingress, zero-IO interpretation, no side effects,
sealed-source direct-SQL rejection, RR concurrent replacement, recapture/new query, old replay,
explicit zero with real witnesses, invalid transaction rejection.


## Full local regression — PASS

Command: MENUTO_TEST_POSTGRES_URL targeting isolated local PostgreSQL18.4, pytest
--basetemp=.local/repeat-penalty-full --junitxml=.local/repeat-penalty-full.xml.
Result: **1626 passed**,179.44s,0 failures/errors/skips;1 pre-existing Starlette/httpx
TestClient deprecation warning. Collection confirms **645 PostgreSQL-real** tests.
JUnit identity comparison with frozen041C local artifact: **1540/1540 prior regressions
retained**,86 additive tests (**81 unit/negative +5 real-PG**).

The PostgreSQL suite ran actual concurrency/direct-SQL negative checks. Its fixture upgrades
base→0012, independently inspects tables and Alembic metadata drift, downgrades empty DB to
base and upgrades again; existing populated downgrade/fail-closed migration tests also pass.
No new migration is needed or edited. No live production database verification is claimed.
Local logs: .local/repeat-penalty-full.log/.xml, collection.json and benchmark.json.

## Delivery

Implementation commit and PR/CI references are recorded in the following evidence update.
This slice is ready for architecture/freeze review after CI; it is not self-frozen.
