# MTR-041A recent exposure source foundation — evidence

Baseline: `06dc1dcbf38d474b90f7bfb74f04651e884285e4` (user-frozen040A,0012 /58 tables).
[Architecture review before code](MTR_041A_RECENT_EXPOSURE_DOMAIN_REVIEW.md).
Status: **proposal-preview subset implemented for review, NOT self-FROZEN**.
Implementation: `35a69f5232abff22000a40210ed74d702852dbf3`.
[PR #73](https://github.com/thedusk4203/Menuto/pull/73).

## Actual scope

Nine frozen/extra-forbid source/policy/request/recipe-identity/support/fact/draft contracts.
Planning adapter captures only canonical selected latest sealed proposals and authored recipe
identity/provenance, under clean read-only RR/SERIALIZABLE and canonical household actor/member
access. Learning core is pure contract replay, with no DB/Execution/optimizer/preference runtime.
Selected-plan source manifest supplies a coherent frontier hash; it is not all-household history.

Only recipe-level **PROVISIONAL / PROPOSAL_PREVIEW** evidence is supported. Proposal advice is
not an accepted commitment, cooked event, confirmed consumption or taste evidence. Consumption
history remains UNAVAILABLE; empty preview is not evidence of never having eaten a recipe.
Versioned policy names an explicit half-open window, with no cooldown/decay/weight constants.
Occurrence count is a matching proposed-meal cardinality, not a repeat/novelty/preference score.

One recipe per meal/member is counted once, even when multiple batches/versions supply that meal.
Each fact retains exact source proposal/hash, stable plan/meal/member/recipe identities and batch/
allocation/version support. Source snapshots preserve recipe provenance/review status. Corrections
and retirement use existing immutable Plan proposal lineage; fresh capture selects only current
proposals. Old snapshots/history remain unchanged. No exposure write API or additional ledger.

Overlapping-window facts deduplicate by stable event key. Mixed revisions for one plan/member
are rejected, including recipe swaps with different event keys; callers must recapture current
sources. This is not full MTR-038 bridge merging or confirmed/provisional reconciliation.

Canonical serialization explicitly sorts only unordered sets and delegates frozen graph fact
canonicalization to graph.content(). Ordered future event/procedure sequences must retain an
explicit ordinal/ledger sequence. Wire roundtrip preserves semantic canonical bytes/hash; Python
tuple order for unordered facts need not be identical. Hashes/serialized flags confer no authority.

## Changes and compatibility

- Learning: new contracts/public pure replay; README accurately narrows current capability.
- Planning: read-only exposure_capture adapter, additive latest-proposal source/public wrapper.
- Household: additive read-only actor lookup; frozen write/locking semantics unchanged.
- New unit/PG fixtures/tests; import checker guards IO/solver imports in exposure core.
- Additive domain bundle16/export/README; old definitions unchanged.
- Product review/evidence, status/backlog/blueprint/invariant coverage/glossary updated.

No migration, new table, persisted score or durable behavioral fact. Schema stays **0012 /58**;
migrations0001–0012 unchanged. MTR-040A source contracts/write semantics remain frozen; raw
declarations still have no EvidenceStrength. Frozen019A/B/C/020A behavior/hashes remain unchanged.
Existing source methods remain unchanged; only additive capture/read methods are introduced.

## Verification

Executed locally on Python 3.13 / PostgreSQL18.4:

| Check | Actual result |
| --- | --- |
| Complete Python suite, final code | **1403 passed**, 0 failures/errors/skips;181.75s |
| PostgreSQL-real included above | **630**, independently marker-collected (615 prior +15 new) |
| Frozen/pre-existing regression identities | **1350/1350 retained**, including all040A regressions |
| New tests | **53 =38 unit +15 real PostgreSQL** |
| Concurrency/capture | RR old/new proposal coherence; RO-only SQL; zero-IO replay; ACL/ownership; retirement history PASS |
| Migration/drift | Existing head→base→head and data-bearing migration regressions PASS; no new migration |
| Frozen compatibility | 12 migration files unchanged;172 old schema definitions unchanged;9 additive, bundle16/181 total |
| Architecture/Ruff/imports | PASS:30 invariants,11 ADRs,50 tasks,16 contexts; new core negative-import tests |
| OpenAPI/domain/fixture exports | PASS;22 synthetic fixtures unchanged |
| Benchmark | **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client | **10/10**, generated contracts check/typecheck PASS |
| Web | TypeScript/Vite build PASS |

One existing Starlette/httpx deprecation warning remains. The earlier full run passed1402; a final
UUID-lookup guard/test was added while it was running, so the entire final suite was rerun and
passed1403 as recorded above. Prior tests were not edited. Existing PlanStore methods retain
identical ASTs; Household/Planning additions are read-only. [Implementation CI run40020090768](https://github.com/thedusk4203/Menuto/actions/runs/40020090768)
completed **SUCCESS** for Python and web. Actual logs confirm **1403 passed** and **22/22 benchmark**;
all architecture/import/export/client/typecheck/build steps passed. The documentation-only final
head is checked again before merge; final-head/merge SHA and post-merge CI are reported at delivery. Local ignored artifacts: `.local/exposure-final.xml/log`,
`exposure-pg-collection.log`, `exposure-benchmark.json`, earlier focused/full iteration logs.
An initial roundtrip assertion compared arbitrary unordered tuple order; it was corrected to
compare semantic canonical bytes/hash, with an actual shuffled graph regression added. No frozen
serialization function was changed and no existing test was removed or weakened.

Tests cover source/status forgery, unknown history, unsupported fingerprints, half-open windows,
policy/hash identity, recipe/batch dedup, source-context corruption, zero-IO replay, SQL read-only
capture, cross-household/member/access errors, concurrent current-source replacement, retired
proposal/history preservation, direct SQL sealed-source tampering and core import violations.
Existing intent proposal service is used only by test fixtures to seed/revise canonical proposals;
no new Execution producer, workflow or production import is implemented.

## Deferred claims

Full MTR-041 is NOT COMPLETE. No confirmed consumption/cooked producer, durable exposure history,
manual-consumption source, attribution router (MTR-039), assumption projection (MTR-017), horizon/
asset replay or confirmed/provisional reconciliation (MTR-038), variant-family/method/protein/flavor
classification mapping (MTR-046), decay/cooldown/novelty scores, profile derivation, utility/ranking,
role assignment, feasibility, Execution or PRECOMMIT authority. Accepted schedule exposure capture
requires production authorization/frontier seams; proposal preview cannot stand in for it.
Full040 remains incomplete; MTR-024/020B/021 remain blocked. Stop for architecture/freeze review.


**READY FOR MTR-041 ARCHITECTURE/FREEZE REVIEW** — preview-source subset only.
