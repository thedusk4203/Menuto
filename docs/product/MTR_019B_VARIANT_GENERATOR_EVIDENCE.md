# MTR-019B — VariantGenerator evidence

Reviewed frozen main: `4a6207ac52bc5ba0ce95de2df54c0c949f36066e`.
[Architecture A–J](MTR_019B_VARIANT_GENERATOR_REVIEW.md) was recorded before implementation.
Status: **READY FOR ARCHITECTURE/FREEZE REVIEW**, not self-frozen.
Implementation commit: `7ecc2d1c9c2bde5faee02498dbabeb4d35edd055`.
PR: https://github.com/thedusk4203/Menuto/pull/66.
Remote CI is recorded after verification below; no pending result is claimed as success.

## Remote verification checkpoints

[Code-checkpoint CI](https://github.com/thedusk4203/Menuto/actions/runs/39931815374)
on implementation commit7ecc2d1: Python **SUCCESS**, logs confirm **1089 passed in63.59s**
and benchmark **22/22**. Web was still in setup-node at09:35UTC on2026-10-23; that checkpoint
does not yet establish web success. The final PR head must pass both jobs before merge.
Final check results are linked from [PR66 checks](https://github.com/thedusk4203/Menuto/pull/66/checks).

## Implemented

Pure Recipe-owned demand expansion over reviewed authored snapshots. Default composition,
exact serving tiers, target-matching rules, exact approved combos and explicit rule selections.
No Cartesian product or hidden ranking. Caller supplies max_attempts/max_candidates; overflow
returns LIMIT_EXCEEDED with no candidates. Invalid demand/path and exclusions have structured
diagnostics; NO_CANDIDATES is not a global infeasibility certificate.

New immutable, extra-forbid contracts: culinary-generation-request.v1, culinary-candidate.v1,
culinary-generation-result.v1, with typed demand, rule selection, limits, triggers/rejections.
Source/candidate/request fingerprints canonicalize unordered fact collections; authored procedure
order is preserved. Candidate identity excludes trigger/limit context, preserves rule provenance.
All quantities remain exact; adjustments are explicitly zero. No float/rounding/yield magic.

Recipe public facade exposes generate_variants. Planning public facade exposes
bind_generated_candidate, which rechecks source hash and recomputes selected culinary claims
before calling the unchanged frozen author_binding. No physical mutation or authority is issued.
Frozen independent RecipeGroundingValidator still enforces captured selected primitives.

## Database and compatibility

No migration required: generation is pure/transient and selections use existing0010 persistence.
Head **0010_planned_culinary_bindings**, **54 domain tables**. Migrations0001–0010 are unchanged.
Real PostgreSQL tests retain existing empty upgrade/downgrade/upgrade, populated legacy roundtrip,
v3 lossy-downgrade refusal, schema/ORM drift, concurrency and direct-SQL guards.

Compatibility comparison against reviewed main verified: frozen recipe-contract source prefix,
author_binding AST, planning contracts, validator contracts/implementation and all prior migrations
unchanged. All **138 old exported schema definitions** are unchanged; bundle12 adds8 definitions.
Frozen plan v1/v2/ValidationSubject hash fixtures remain green. MTR-019A is user FROZEN at4a6207a;
RecipeGroundingValidator is accepted as one completed MTR-026 capability, not full MTR-026.

## Adversarial test map

| Scenario | Evidence |
| --- | --- |
| Demand default vs target, unknown ingredient | default/target/unknown-target unit tests |
| Unsupported tier/rule, schema and draft sources | invalid-demand/contract negative matrices |
| Structural pair/exact approved set/extra nonstructural rule | combination tests + independent validator |
| Nonstructural sets, duplicate/same-slot rules | explicit-set and authorization tests |
| Duplicate demand/context, distinct authored provenance | dedup-trigger/distinct-rule tests |
| All five scaling policies, exact tiers/COUNT identity | authored tier quantity test |
| COUNT substitution, float/nonfinite, unauthorized adjustment/reason | contract negative tests |
| Base-only/substitute-only/neither preparation path | three-way transformation regression |
| Zero refinement, no serving inference | adjustment envelope/serving tests |
| Canonical ordering, decimal spelling/context, primitive identity changes | hash/determinism tests |
| Limits, many alternatives without Cartesian expansion | fail-closed budgets/linear expansion tests |
| Forged candidate with self-consistent fingerprint | adapter mutation matrix |
| Forged selected binding with self-consistent graph hashes | independent validator negative test |
| Generator/validator independence, no live reads/writes | import checks + real PG query trap |
| Default/substitute/tier persistence without stock changes | real PostgreSQL roundtrip tests |
| SQL amount/ingredient/rule corruption | real PostgreSQL seal/FK negatives |

SQL corruption tests disable only UPDATE immutability on *unsealed test assembly* as DB owner;
Fks/checks/seal remain active and reject it. Existing append-only tests run with guards enabled.
No test-only authorization bypass or production capability was introduced.

## Local verification

Final local full run (Python3.13/PostgreSQL18): **1089 passed in80.61s**, **0 skipped,
0 failures, 0 errors**; **502 PostgreSQL-real cases** are included in that total.
All **1034 pre-existing test identities** retained (XML identity comparison:0 missing);
**55 new cases =48 unit/adversarial +7 PostgreSQL-real**. One existing Starlette/httpx
deprecation warning remains; no dependency change is made in this slice.

Executed successfully:

- `python -m pytest --junitxml=.local/variant-full.xml` with local real PG URL;
  marker collection independently confirms502 PostgreSQL cases.
- `python -m ruff check .`; `tools/check_architecture_baseline.py` (30 INV,11 ADR,50 tasks);
  `tools/check_import_boundaries.py` (16 contexts).
- Domain/OpenAPI export checks;22 synthetic fixture drift checks; no schema/ORM drift.
- `python -m benchmark.runner --output .local/variant-benchmark.json`: **22/22**.
- `npm run contracts:check`, `typecheck:client`, `test:client`: **10/10 client tests**.
- `npm run build:web`: TypeScript and Vite production build pass.

Artifacts: `.local/variant-full.xml`, `.local/variant-full.log`, `.local/variant-benchmark.json`.
The benchmark is **HARNESS_SMOKE_NOT_PLANNER_V4**, not production optimizer evidence.

## Deliberately deferred

No Pareto/MTR-020, feasibility/MTR-021, Stage1/MTR-022, nutrition/procurement grounding,
inventory allocation, evidence-backed PRICE_ADVANTAGE/EXPIRY_RESCUE reasons, MTR-030 refinement,
CookingBatchExecution/MealExecution, assumptions, full Independent Validator or production
PRECOMMIT/TOCTOU authorization. Culinary demand exclusions do not constitute member-safety
validation. Candidates remain DRAFT/activation_ready=False. Neither full MTR-019 nor MTR-026
is complete. Stop here pending architecture/freeze review; no next milestone started.

## Changed files

- Recipe: additive contracts, new generation.py, public producer facade.
- Planning: additive selected-candidate adapter and public export; frozen binding unchanged.
- Tests: test_variant_generation.py; test_postgres_variant_generation.py. No old tests changed.
- Export: tools/export_domain_contracts.py; packages/contracts/domain.schema.json and README.
- Docs: this evidence/review, FOUNDATION_STATUS, IMPLEMENTATION_BLUEPRINT_M0_M1, BACKLOG,
  INVARIANT_COVERAGE and GLOSSARY. No canonical ADR/invariant text rewritten.
