# MTR-020A — Conservative Pareto Shortlist / evidence

Reviewed/frozen dependency baseline: `ffaa009031d8def0e32a654266a871cced44d35e`.
MTR-019A/B/C remain user FROZEN. Full MTR-019/020/026 remain PARTIAL.
[Architecture decision before implementation](MTR_020A_PARETO_SHORTLIST_REVIEW.md).
Implementation commit and CI evidence are recorded below after verification.

## Implemented claim

Planning-owned pure deterministic exact supply-coverage frontier. Canonical ingress accepts
grounding requests, captures supported source primitives through frozen C in read-only coherent
transactions, and issues a process-local pool. Pure core never reads sources/DB or resolves facts.
Untrusted candidate JSON/ready flags/self-consistent hashes cannot mint that pool. Python private
mint code is trusted server internals, not cryptographic authentication or PRECOMMIT authority.

Comparison requires identical culinary/serving/nutrition/inventory/member/cutoff facts. A survivor
must contain every exact procurement source/status/path of a removed input and strictly more
resolved paths. Distinct non-contained source alternatives survive. Witnesses identify removed,
retained and comparison identities. Exact duplicates/ties have deterministic handling; original
candidate facts/hashes survive unchanged. canonical_json provides deterministic wire identity even
when unordered fact tuples were serialized differently. Any failed grounding or resource overflow
returns no eligible candidates. No cheapest-first prefix, implicit feasibility or quality scoring.
Counts not computed after a failed input/grounding gate are explicitly null, not fake zero counts.

## Contracts and database

- Additive ShortlistPolicyDraft, ShortlistInputFailure, ShortlistDominanceWitness,
  ParetoShortlistDraft. Frozen/extra-forbid; versioned policy/result; activation_ready=False.
- Process-local CapturedShortlistPool is deliberately not a wire/API activation capability.
- No persistence or migration. Head `0010_planned_culinary_bindings`,54 domain tables unchanged.
- All migrations0001–0010 untouched. All158 prior exported definitions unchanged; bundle14 has
  162 definitions. Existing Planning contract class/function ASTs unchanged.
- Full regression includes real PostgreSQL metadata drift, empty migration roundtrips and
  populated fail-closed downgrade checks; no new migration path is invented for transient logic.

## Adversarial coverage

- Strict path coverage removal with full source containment; non-contained source facts prevent it.
- Incomparable package paths and different nutrition/cutoff/culinary trigger/inventory facts survive.
- Exact duplicates, semantic duplicates with reordered tuples, input permutations and tie provenance.
- Unknown observation/reference/calibrated availability remains conditional, never stock/checkout cost.
- INCOMPLETE/REJECTED grounding cannot expose a shortlist; raw serialized candidates/results rejected.
- Self-consistent forged culinary quantity rejected through canonical real-PG capture.
- Real FIXED_PACK/CATCH_WEIGHT/LOOSE_SCALE capture, unchanged inventory/reservations/source snapshots.
- Pure core executes under an Engine query/write trap after capture; non-readonly capture rejected.
- Input limit before source reads; frontier overflow preserves no arbitrary partial subset.
- Narrow import guard rejects solver, execution, IO, runtime grounding and physical service imports.
- Wire roundtrip/immutability/no activation; policy identity changes result identity appropriately.

## Local and CI verification

Executed on Windows/Python3.13 with real local PostgreSQL18.4:

| Check | Actual result |
| --- | --- |
| Complete Python suite | **1217 passed**,0 failed/errors/skipped;153.31s |
| Pre-existing regression identities | **1158/1158 retained** against frozen C JUnit XML |
| New cases | **59 =48 unit +11 PostgreSQL-real** |
| All PostgreSQL-real cases | **525 passed** (514 prior +11 new); independently marker-collected |
| Migration/metadata | Existing real-PG up/down/up, populated fail-closed paths and Alembic check pass; head0010 /54 tables |
| Architecture |30 invariants /11 ADRs /50 linked tasks;16-context import guard PASS |
| Compatibility |158 old definitions and prior Planning contract ASTs unchanged;4 additive definitions |
| Export checks | Domain/OpenAPI/generated client +22 fixture drift checks PASS |
| Synthetic benchmark | **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client | **10/10 tests**, TypeScript typecheck/generated contracts PASS |
| Web | TypeScript/Vite production build PASS |
| Ruff / diff whitespace | PASS |

One existing Starlette/httpx deprecation warning remains. Intermediate checks caught a missing
evidence-file link while documentation was being assembled and a sandbox temp-directory permission
error in a focused run. The file now exists, focused checks pass with a workspace basetemp, and
the final complete real-PG run above has no failures/errors/skips. No old test was weakened/deleted.
PR/code commit/CI links are recorded after the remote workflow finishes below.
Local artifacts are ignored `.local/shortlist-full.xml`, `.local/shortlist-full.log`,
`.local/shortlist-pg.xml`, `.local/shortlist-benchmark.json`.

## Files

| Area | Files |
| --- | --- |
| Planning | contracts.py (additive), public.py (additive exports), shortlist.py, shortlist_capture.py |
| Tests | test_pareto_shortlist.py, test_postgres_pareto_shortlist.py |
| Architecture/export | tools/check_import_boundaries.py, tools/export_domain_contracts.py, packages/contracts/domain.schema.json, packages/contracts/README.md |
| Documentation | this evidence, MTR_020A_PARETO_SHORTLIST_REVIEW.md, BACKLOG.md, FOUNDATION_STATUS.md, IMPLEMENTATION_BLUEPRINT_M0_M1.md, INVARIANT_COVERAGE.md, GLOSSARY.md |

## Explicitly deferred

No complete role-aware MTR-020 portfolio/quota policy, numeric Pareto score, learned roles,
preference/effort/goal synthesis, novel variant reason, COUNT nutrition or allergen/diet catalog.
No price freshness/outlier/scenario assessment, basket cost, package selection, physical allocations,
reservation writes, chronological/global feasibility, solver, Execution, full validator or
production PRECOMMIT/TOCTOU capability. No following milestone started. This conservative relation
intentionally prunes little: different culinary possibilities remain even if future metrics might
rank them similarly. Resource overflow is a data/limit outcome, never proof of infeasibility.

**READY FOR ARCHITECTURE/FREEZE REVIEW** for MTR-020A only; not self-FROZEN.
