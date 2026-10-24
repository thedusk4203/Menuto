# MTR-041B — proposal-local Recipe-ID cooldown evidence

Status: **FROZEN / APPROVED by user** at canonical commit
**`43192c7303e42c7bac321728edecaa8421a58e9a`** ([PR #77](https://github.com/thedusk4203/Menuto/pull/77)).
Approved baseline: `391a53e80e841252cc9fd7389e7d566a5d77907b`.
Implementation commit: **`ac51b3877282666e0798dbaf4b40164b4359e6ea`**.
This evidence file is a documentation-only follow-up.
[PR #77](https://github.com/thedusk4203/Menuto/pull/77).
[Implementation-head CI40073273433](https://github.com/thedusk4203/Menuto/actions/runs/40073273433)
ran against `9ef8f7203e17ad0ae169d75d77694bd8742f6d57`: **SUCCESS Python +web**,
1453 tests and22/22 benchmark; all architecture/import/export/client/typecheck/build steps passed.
[Post-merge CI40073675503](https://github.com/thedusk4203/Menuto/actions/runs/40073675503)
ran against the exact canonical freeze commit: **SUCCESS Python +web**,1453 tests and22/22
benchmark; all architecture/import/export/client/typecheck/build gates passed. This freeze
record changes documentation only; it does not modify or extend the implementation.
Schema remains **0012 /58 domain tables**; migrations0001–0012 unchanged, no new migration.
[Architecture/contract decisions](MTR_041B_RECIPE_COOLDOWN_REVIEW.md).

## Implemented claims

Pure Learning assessment of one current captured proposal, one household/member/target meal/
Recipe ID, using explicit versioned policy with positive integer microsecond duration. Target
comes from PLANNED graph participation and positive PLANNED batch allocation. Interval is
T-duration inclusive through T exclusive; whole target meal excluded. Equal times not earlier.
Full lookback capture required, including the valid case capture-window.end ==T. Five additive
contracts and public assess_recipe_cooldown; output recomputes all summaries from primitives.

Exact positive witnesses preserve proposed meal/recipe/allocation/batch/version identity and
distance. Scoped no-match never means globally safe, never exposed or novel. Policy identity,
duration and provenance participate in deterministic canonical hashes. All results remain DRAFT/
activation_ready=False; accepted schedule, confirmed exposure, consumption history, decay,
novelty, TasteFit and RepeatPenalty remain UNAVAILABLE. Invalid/unavailable inputs reject.

Capture reuses frozen041A's read-only RR/SERIALIZABLE Planning source adapter. Learning core
performs no DB/Execution/Preferences runtime, scoring, optimizer calls or writes. No source
frontier/TOCTOU authority is claimed: sources are current at capture, not continuously current.

## Verification

Local ignored artifacts: `.local/cooldown-full.xml/log`, `.local/cooldown-benchmark.json`.
Local final verification, Python3.13/PostgreSQL18.4:

| Gate | Actual result |
| --- | --- |
| Complete Python suite | **1453 passed**,0 failed/errors/skips,171.29s;1 existing Starlette/httpx deprecation warning |
| PostgreSQL-real | **635** marker-collected cases, all included in complete run (630 prior +5 new) |
| Pre-existing regression | **1403/1403** JUnit identities retained and passed;50 additive tests |
| New tests | **45 unit +5 PostgreSQL-real** |
| Migration/drift | Existing module fixtures perform head→base→head and Alembic check; all migration/data-bearing regressions pass; no new migration |
| Architecture/import/Ruff | PASS:30 invariants,11 ADRs,50 tasks,16 contexts; existing pure-core negative import guards retained |
| Domain/OpenAPI/fixtures | PASS;181 old definitions unchanged +5 new;22 synthetic fixtures unchanged |
| Benchmark | **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client | **10/10**, contracts check and TypeScript check PASS |
| Web | TypeScript/Vite build PASS |

Marker count comes from `.local/cooldown-collection.json`; prior identity comparison uses the
existing041A JUnit artifact, not a guessed subtraction alone. The test PostgreSQL cluster was
started only for verification and stopped afterward. Focused unit tests:
**45 passed**, including policy duration precision, invalid inputs, half-open boundaries,
whole-target exclusion, two versions/batches per meal, per-member filtering and cached-output
tamper rejection. Five new real-PG tests cover canonical read-only capture/zero-IO replay,
concurrent source replacement, invalid transaction isolation/read-only modes, and direct SQL
rejection of immutable-source rewrite. No old test is edited or removed.

Compatibility verified against approved baseline: all **181 old schema definitions** are
structurally identical; five additive definitions, bundle17 /186 total. All12 frozen041A
class/function ASTs in contracts.py and both public functions are identical. Previous migration
files and frozen040A runtime are unchanged. New input/result hashes do not modify old algorithms.

The first concurrency test compared entire result fingerprints across two captures; captured_at
is intentionally part of source identity. Assertion was corrected to compare source frontier,
witnesses and outcome within RR. Identical immutable input still has identical bytes/hash.
No runtime or frozen source behavior was changed to satisfy that assertion.

## Deferred / not certified

Full040 and041 remain incomplete. No accepted publication (026 authority/TOCTOU), confirmed
member-attributed exposure/consumption (Execution/039), operational projection or canonical
cross-horizon bridge (017/038;036 assumptions), reviewed feature/family mappings (046), decay,
novelty, affinity/Profile derivation, RepeatPenalty or Stage-2 composition. No new culinary
possibilities, material movement, reservations, persistence or migration. AP→EP and cooking
yields remain separate; proposal intent is not physical or behavioral history.

MTR-024/020B/021 remain BLOCKED. Execution remains NOT STARTED. PRECOMMIT remains fail-closed.
User freeze certifies only the implemented proposal-local cooldown subset. No correction is
required; do not start any following implementation without its architecture approval.
