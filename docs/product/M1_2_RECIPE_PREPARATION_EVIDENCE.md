# M1.2 Recipe / Preparation Foundation — evidence

Implementation commit: `bc0524bf5e18e4d3eb778acbc4156965b37dd9cd` (recorded in the evidence-only follow-up).
Local checks PASS. CI is PENDING publication; the slice is not claimed merged/CI-approved here.
Machine-readable results: [M1_2_RECIPE_TEST_RESULTS.json](M1_2_RECIPE_TEST_RESULTS.json).

Architecture: [review A–H](M1_2_RECIPE_DOMAIN_REVIEW.md); canonical ADR-005/009/010,
INV-005/006/017/018. Frozen dependency M1.1 at `f49e9b1` remains unchanged.

## Implemented boundary

10 tables: recipes, recipe_versions, recipe_ingredients, recipe_portion_tiers,
recipe_tier_quantities, recipe_variant_rules, recipe_rule_combinations,
recipe_combination_members, preparation_transformations, recipe_version_seals.
33 domain tables total. No JSONB. Explicit relational ownership/composite FKs.

Version + children are immutable; deferred mandatory seal and assembly transaction guard
protect against later INSERT as well as UPDATE/DELETE/TRUNCATE. SQL independently checks
tier coverage/scaling/discrete steps/positivity/context/review when sealing. No persisted
candidate nutrition or derived purchase cost. Recipe repository returns frozen snapshots.

## Deliberate draft and deferred decisions

`GroundedRecipeVariantDraft` is DRAFT, activation_ready=False, contract recipe-v1.
It binds authored culinary choices only; it does not assert full downstream grounding.
No nutrition resolver, household safety evaluation, Retail/Inventory Resolver,
VariantGenerator, Pareto shortlist, CP-SAT, Independent Validator orchestration,
CulinaryAdjustmentPass service, InventoryLot/Movement/Reservation, CookingBatch execution,
PreparedFoodLot persistence, ActivePlan, PlanRevision, learning or production AI/import.

V1 uses authored production tiers only. Continuous scaling/interpolation, composition-only
tiers with identical serving count, optional slot omission and count-to-mass conversions
are deferred. SUBLINEAR means authored monotonic less-than-proportional tier points,
not an invented exponent or a globally calibrated cooking constant. Scaling discrete
quanta and adjustment deltas remain explicit; no rounding.

Reviewing/importing data is not a production workflow here. Imported draft provenance
cannot claim REVIEWED; human review must publish another authored version. Recipe
lifecycle and household-private authoring/access control are not implemented; identities
are global catalog identities, not tenant-owned assets.

## Scope of acceptance

This slice can support a separate M1.3 architecture review once all listed gates pass.
It does not claim full M0/M1 completion, production planning readiness, activation safety,
or real cooking/checkout correctness. No M1.3 work is included.

## Verification actually run

Commands use the locked `.venv` runtime (Python 3.13) and real PostgreSQL 18.4 on
loopback, port 55443, in a temporary isolated cluster. Tests create/drop only random
`menuto_test_<uuid>` databases. No application database was migrated.

```text
pytest --junitxml=.local/m12-verified-tests.xml --basetemp=.local/pytest-m12-verified
ruff check .
python tools/check_architecture_baseline.py
python tools/check_import_boundaries.py
python tools/export_openapi.py --check
python tools/export_domain_contracts.py --check
python tools/generate_synthetic_fixtures.py --check
python -m benchmark.runner --output .local/m12-benchmark.json
npm run contracts:check
npm run typecheck:client
npm run test:client
npm run build:web
```

Final local Python: **559 passed**, **246 PostgreSQL-real**, 0 skipped/errors/failures, 105.319 seconds. One preexisting Starlette/httpx deprecation warning. All 398 prior tests remain covered.

| Test group | Passed |
| --- | ---: |
| `apps.backend.tests.test_architecture` | 48 |
| `apps.backend.tests.test_baseline` | 3 |
| `apps.backend.tests.test_domain_contracts` | 42 |
| `apps.backend.tests.test_foundation_migration` | 8 |
| `apps.backend.tests.test_health` | 3 |
| `apps.backend.tests.test_postgres_foundation` | 24 |
| `apps.backend.tests.test_postgres_recipes` | 89 |
| `apps.backend.tests.test_postgres_retail` | 109 |
| `apps.backend.tests.test_postgres_retail_corrections` | 16 |
| `apps.backend.tests.test_precision_corrections` | 8 |
| `apps.backend.tests.test_recipe_contracts` | 62 |
| `apps.backend.tests.test_retail_contracts` | 68 |
| `apps.backend.tests.test_retail_semantic_corrections` | 11 |
| `benchmark.tests.test_foundation_regressions` | 38 |
| `benchmark.tests.test_harness` | 30 |

Architecture: 30 invariants/11 ADRs/50 linked tasks check PASS; 16 context boundaries PASS,
with explicit negative Recipe→Retail/Inventory/Planning/Execution/Validation and
Retail→Recipe tests. OpenAPI/domain drift PASS. 22 fixtures and 22/22 benchmark scenarios
PASS. Client generated contracts/typecheck, 10 client tests and web build PASS.

Migration tests cover empty 0004→0005→0004→0005 and full legacy base→head→base→head,
Alembic metadata drift, populated Recipe downgrade rejection without data loss, and
legacy Retail source preservation through upgrade. Frozen 0001–0004 and Retail
implementation are unchanged (`git diff main -- ...` empty at verification).
0005 imports only Alembic, never mutable ORM metadata. DB facts reject UPDATE/DELETE/
TRUNCATE; child INSERT after seal and after commit is rejected, including stale
READ COMMITTED/REPEATABLE READ snapshots. Subtransactions remain supported.

## Invariant coverage change and remaining gates

- INV-005 moves SCAFFOLD_ONLY→PARTIAL_FOUNDATION: authored version/rule/tier/combo facts,
  exact selection and non-authored rejection; production generation remains absent.
- INV-006 moves MICRO_MODEL_ONLY→PARTIAL_FOUNDATION: immutable bound quantities and
  explicit servings survive micro-adjustment; production solver/batch refinement absent.
- INV-017/018 remain PARTIAL_FOUNDATION: recipe-owned cooking primitives add to the
  frozen Retail AP→EP path, with independent recomputation inputs and SQL checks.
  Full Independent Validator/nutrition/activation gates remain unimplemented.
- Other invariant statuses are unchanged. No production completeness claim.

Recommendation: after CI PASS, the schema/primitive dependency is sufficient to begin
the separate M1.3 Inventory Physical Ledger architecture review. That review must keep
Retail AP origin/mapping evidence and Recipe preparation/serving identity distinct;
this does not authorize or implement M1.3 within this slice.
