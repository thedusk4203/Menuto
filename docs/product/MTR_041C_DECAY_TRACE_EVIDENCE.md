# MTR-041C — proposal-local Recipe-ID decay trace evidence

Status: **IMPLEMENTED / NOT FROZEN — awaiting architecture/freeze review**.
Baseline: `378cb36615b7f9445b500ce961627669e99cb858`.
Implementation commit: **`92c937366424462bfbbf47e6f116a6ed74a7fe76`**.
This evidence file is a documentation-only follow-up.
[PR #79](https://github.com/thedusk4203/Menuto/pull/79).
[Implementation-head CI40076441139](https://github.com/thedusk4203/Menuto/actions/runs/40076441139)
ran against `fa543d5838f4e9b6b9fa61534862a8bc18f01b7b`: **SUCCESS Python +web**,
1540 tests and22/22 benchmark; architecture/import/export/client/typecheck/build gates passed.
This final CI-note update changes documentation only; final-head/merge CI is verified at delivery.
Schema **0012 /58 domain tables**; no persistence/migration.
[Approved boundary and implemented contracts](MTR_041C_DECAY_TRACE_REVIEW.md).

## Actual scope

Six additive frozen/extra-forbid contracts and pure Learning public trace_recipe_decay.
Input fully revalidates frozen041B assessment before interpreting its eligible witnesses.
Witness source evidence and derived age remain separate from the exact rational policy
multiplier and derived diagnostic trace. No aggregation, score, confidence or utility.

Explicit ordinal age bands cover(0,D] exactly for this subset only. Lower bounds are
non-negative, upper positive, no gaps/overlaps/tail/interpolation, retention non-increasing.
Reduced rational canonicalization makes equivalent ratios identical under identical metadata;
zero retention retains the original witness. Policy/provenance/bands enter deterministic hashes.
AS_OF_CAPTURE is explicit; later observed policy rejects here, without forbidding a separately
designed retrospective evaluation mode. No future full-decay/cooldown horizon equality invariant.

041A/B runtime definitions and canonical algorithms remain unchanged; nested041B.decay remains
UNAVAILABLE. Output activation_ready=False; RepeatPenalty, novelty, TasteFit, confirmed exposure,
consumption/accepted/global history UNAVAILABLE. No DB IO, writes, Execution, Preferences runtime,
ranking, solver, assumptions or blocked source branch.

## Verification

Focused final unit run: **82 passed**. New real-PostgreSQL integration: **5 passed**.
Final local verification:

| Gate | Actual result |
| --- | --- |
| Full Python suite | **1540 passed**,0 failures/errors/skips,185.77s;1 existing Starlette/httpx deprecation warning |
| PostgreSQL-real | **640** marker-collected, included in the full pass (635 prior +5 new) |
| Pre-existing regression | **1453/1453** JUnit identities retained and passed |
| New tests | **87 =82 unit +5 PostgreSQL-real** |
| Migration/drift | Existing module fixtures run head→base→head +Alembic check and populated migration regressions; all pass; no new migration |
| Architecture/import/Ruff | PASS:30 invariants,11 ADRs,50 tasks,16 contexts; pure-core negative guards retained |
| OpenAPI/domain/fixtures | PASS;186 old definitions unchanged +6 additive;22 synthetic fixtures unchanged |
| Benchmark | **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client | **10/10**, generated-contract check and typecheck PASS |
| Web | TypeScript/Vite build PASS |

PG count comes from marker-based collection in `.local/decay-collection.json`; prior identities
were compared with the existing041B JUnit artifact. The local test cluster was stopped after
verification. PR/head/merge CI is checked and reported at delivery.
Local ignored logs/JUnit: `.local/decay-full.xml/log`, `.local/decay-pg.xml`,
`.local/decay-benchmark.json`.

Coverage: exact rational normalization including0/1 and1/1; bool/float/NaN/Inf rejection; exact
cross-product comparison beyond float precision; band endpoints, order/gaps/overlaps/monotonicity;
zero witness retention; empty scoped trace; missing policy and lookback mismatch; equal-time
exclusion; as-of cutoff and retrospective-mode rejection; policy/hash changes; output tampering;
forged nested model_construct assessment; unsupported source/fingerprint and no aggregate fields.

Real-PG checks canonical RO RR capture, zero-IO replay/serialization, no row-count side effects,
concurrent replacement/old immutable replay, fresh-query binding, explicit zero retention,
invalid capture isolation/read-only modes and direct-SQL sealed-source rewrite rejection.
Existing migration fixtures execute upgrade/downgrade/upgrade and metadata checks.

Compatibility check against baseline: **186 old definitions unchanged +6 additive** (bundle18,
192 total); all19 frozen class/function ASTs in Learning contracts and3 public functions remain
identical. Migrations0001–0012 and frozen040A/041A/041B tests/semantics remain untouched.

An adversarial model_construct test initially reached041B's after-validator with malformed nested
types before new-input validation.041C ingress now serializes/reparses that instance in a before
validator, then fully recomputes041B; no frozen041B fix/change. Expected serializer warnings in
those deliberate forged-instance cases are asserted by the tests, not globally suppressed.

The first full run started before the linked evidence document existed:1539 passed, one
documentation baseline-link failure. The missing document was completed, architecture checks
passed, and the entire suite was rerun. Initial log/JUnit are retained separately as
`.local/decay-initial.log/xml`; no test was skipped, weakened or removed to close that failure.

## Deferred claims

Full041 remains blocked/incomplete. No full RepeatPenalty, novelty, TasteFit or Stage-2 utility;
no production parameter defaults/calibration, multi-fingerprint mappings046, confirmed member
events/039, accepted authority026, projections/bridge017/038 or assumptions036. Full040 profile
derivation incomplete;024/020B/021 blocked, Execution unstarted, PRECOMMIT fail-closed.
No retrospective policy mode, new physical fact, material allocation, reservation, AP/EP/cooked
conversion, generic persistence or migration. Do not self-freeze or start another milestone.
