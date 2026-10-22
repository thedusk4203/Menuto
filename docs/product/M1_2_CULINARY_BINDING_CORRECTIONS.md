# M1.2 Culinary Binding Corrections — decisions and evidence

Baseline: reviewed PR #57, main `2db3ccd163cffe2366105b6e13ae3ab90fb08b01`.
Review verdict: APPROVE WITH 2 REQUIRED CORRECTIONS; M1.2 is not yet FROZEN.
Scope: INV-005/017/018, no M1.3 or seal/version redesign.

## Decisions before code

1. Select net preparation transformation by exact `(requirement_id, resolved ingredient_id)`.
   A transformation on an alternate path does not require the base raw path to transform.
   Preserve the conservative V1 rule: when the base path transforms, a replacement must
   have its own authored transformation; absence cannot silently authorize a raw escape.
   With neither path transformed, both remain valid raw paths. No copied yield evidence.
2. V1 substitutions target only EP_RAW_G/COOKED_G requirements. COUNT requirements remain
   usable unchanged, with their explicit item_ref, but cannot be substitution targets.
   Replacement count identity/conversion is deferred. Enforce in aggregate validation
   and a supplemental PostgreSQL seal check, without changing existing seal functions.
3. Migration 0006 is frozen SQL. Lock relevant tables and reject upgrade if legacy COUNT
   substitutions exist; never rewrite/delete immutable authored data or fabricate identities.
   Such data needs an explicit archival/correction migration outside this slice. Downgrade
   only removes the added policy guard, losing no data/provenance; populated downgrade is
   therefore safe. 0005 and all earlier migrations remain byte-unchanged.
4. Wire shape remains recipe-v1; validation rejects previously accepted invalid COUNT
   rules. Existing invalid snapshots need explicit correction, not a compatibility alias.
5. P2 limitations remain: VariantReason is caller-supplied draft explanation, not verified
   downstream evidence. PreparationTransformation V1 is a net EP_RAW→COOKED transformation
   under the Recipe cooking context, not a multi-step preparation workflow engine.

## Verification

Implementation commit: `9d1233f33f5f5ac7a4f6e5416d598f2e27afb638` (recorded in an evidence-only follow-up).
Local gates and remote CI PASS. This is correction evidence, not user
freeze approval. [Machine-readable results](M1_2_CULINARY_CORRECTIONS_TEST_RESULTS.json).

- Before correction, the new unit corpus reproduced 3 failures (raw default rejected,
  structural/nonstructural COUNT rules accepted), with 10 other cases passing.
- After correction: **585 passed**, **259 PostgreSQL-real**, 0 skipped/errors/failures,
  **83.17 seconds**. One preexisting Starlette/httpx deprecation warning.
- New coverage: 13 unit + 13 PostgreSQL tests. All 559 prior tests remain in the full run.
- Eight preparation matrix cases cover base/substitution paths with/without transforms;
  selected evidence identity, immutable draft roundtrip and wrong-path injection rejection.
- COUNT rules fail in aggregate validation regardless of structural classification;
  SQL bypass attempts fail at seal. Unchanged COUNT item_ref and both mass substitution
  bases remain valid. Persisted snapshots exercise the same preparation matrix.
- Migration 0005→0006→0005→0006 tested on empty and populated databases; snapshots and
  all four original seal/version function definitions stay identical. Legacy COUNT
  upgrade rejects without losing facts or changing revision. Original 0005 populated
  downgrade still refuses data loss, and rollback restores the 0006 policy guard.
- Alembic metadata drift and all historical migration tests PASS. 33 tables unchanged.
- Ruff, 30 INV/11 ADR/50 task consistency, 16 context import boundaries PASS.
- OpenAPI/domain export and generated client drift PASS. 22 synthetic fixtures and
  **22/22 benchmark scenarios** PASS. Client typecheck, **10 client tests**, web build PASS.
- 0001–0005 are byte-identical to baseline Git blobs; SHA-256 values recorded in JSON.
  Models/repository/Retail and the seal architecture remain unchanged.

Commands actually run (locked Python 3.13 runtime; PostgreSQL 18.4 loopback service):

```text
pytest --junitxml=.local/0006-tests.xml --basetemp=.local/pytest-0006-full
ruff check .
python tools/check_architecture_baseline.py
python tools/check_import_boundaries.py
python tools/export_openapi.py --check
python tools/export_domain_contracts.py --check
python tools/generate_synthetic_fixtures.py --check
python -m benchmark.runner --output .local/0006-benchmark.json
npm run contracts:check
npm run typecheck:client
npm run test:client
npm run build:web
```

Real PostgreSQL tests used isolated random test databases, not an application database.
The temporary test cluster was stopped after the run. No M1.3 work was started.
INV-005/017/018 remain PARTIAL_FOUNDATION; correction adds counterexample coverage,
not a production validator or complete grounding pipeline.


## Remote CI verified

[Foundation checks #23](https://github.com/thedusk4203/Menuto/actions/runs/39780039361),
tested head `92c0f5da6d70bdda29473dec579b05ec31b70661`, completed **success**.
Python job `119828655304` and web job `119828655021` both **success**. Logs confirm
**585 passed**, 3 deprecation warnings, **22.99 seconds**, PostgreSQL **18.4** and
**22/22 benchmark scenarios**. The 259 PostgreSQL tests execute with no skipped tests.
All architecture/schema/client/web checks passed. [PR #58](https://github.com/thedusk4203/Menuto/pull/58)
is the publication artifact. This evidence-only follow-up must also pass final-head CI
before merge, under the user's standing push/merge instruction. M1.2 freeze remains a
separate user review verdict; no M1.3 work is included.
