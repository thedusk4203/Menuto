# MTR-019C — Candidate Grounding evidence

Reviewed frozen main: `23dd0b3bc3245ac9c7ef5493968f8ab120242f00`.
[Architecture A–J](MTR_019C_CANDIDATE_GROUNDING_REVIEW.md) was recorded before code.
MTR-019B is now user FROZEN at that commit. MTR-019C is submitted for review, not self-frozen.
Exact implementation commit/PR/verified remote CI are recorded below when available.

## Delivered contracts / boundaries

- `candidate-grounding-request.v1`: caller supplies culinary draft, household/participants,
  explicit cutoff/region/currency, ProcurementClass IDs and optional nutrition reference IDs;
  never nutrition totals, quotes or a safety summary.
- `candidate-grounding-sources.v1`: immutable canonical Recipe/catalog/member/safety/retail/physical
  snapshots captured under clean read-only REPEATABLE READ/SERIALIZABLE.
- `resolved-nutrition-portion.v1` / ResolvedNutrients: Nutrition-owned compatible reference and
  exact ingredient-input composition; no nutrient-retention/physiological-policy synthesis.
- `preparation-output-estimate.v1`: Recipe-owned net EP_RAW→COOKED output; not executed production.
- `procurement-supply-path.v1`: Retail-owned granularity-specific EP supply coefficients, original
  price reference pair, mapping/status/availability/provenance. Not purchase cost or owned stock.
- `inventory-candidate-lot.v1`: confirmed household lot/position plus usable quantity, UNALLOCATED.
  AP source keeps its reviewed Product→Ingredient mapping; raw/prepared identities remain distinct.
- `grounded-dish-candidate.v1`: nested primitive facts, exact batch input nutrition, context/source
  and deterministic hash. PRIMITIVES_RESOLVED/shortlist_input_ready means supported **input fact
  completeness**, not global feasibility/optimality or production acceptance. activation_ready=False.
- `candidate-grounding-result.v1`: GROUNDED / INCOMPLETE / REJECTED; blocking failures expose no
  eligible candidate. ALLERGEN/DIET_RULE without classification fails closed.

Public `planning.public.ground_candidate(session, request)` reloads canonical sources by identity;
pure captured assembly delegates to owner-domain public resolvers. No DB query after capture.
Existing MTR-019A selected-binding/seal/independent RecipeGroundingValidator path remains unchanged.
No plan/proposal IDs, purchases, lots, movements, reservations or execution are fabricated.

## Compatibility / database

No migration or new table. Alembic **0010_planned_culinary_bindings**, **54 domain tables**.
Migrations0001–0010 byte unchanged. Comparison to reviewed main verified all prior class/function
ASTs in changed Recipe/Planning/Inventory/Nutrition/Retail files unchanged, frozen generator and
validation contracts/implementation byte unchanged. All **146 old schema definitions** unchanged;
bundle13 adds **12 definitions**. Existing wire/hash fixtures retained.
Real PG fixture exercises empty full migration roundtrip and metadata drift; prior populated
roundtrip/lossy downgrade, source immutability and concurrency tests remain in full regression.

## Counterexample evidence

| Finding class | Tests |
| --- | --- |
| Forged culinary with recomputed fingerprint | unit mutation matrix + public real PG source reload |
| Caller-invented nutrition/quotes/is_safe | request extra-forbid matrix; PG reference-ID miss |
| Missing/ambiguous/draft/future/raw-cooked nutrition | unit matrix, explicit selection, COUNT rejection |
| New nutrition reference does not silently replace old | real PG concurrent append/RR capture; fresh capture ambiguous until explicit selection |
| UNKNOWN/reference/calibrated evidence not stock | three origins, no material changes, conditional warning |
| Fixed/catch/loose supply and reference pair != purchase cost | unit + real PG three-granularity matrix |
| Retail AP→EP vs Recipe EP_RAW→COOKED | separate provenance/coefficients/output, no nutrient rescaling |
| Stock/reservations/expiry/confidence | no mutations, allocatable quantities, expired/stale/unknown/full reservation excluded |
| Prepared component vs raw identity | compatible COOKED references and existing prepared identity, no fake raw conversion |
| Canonical participant restrictions / shared safety | exclusions rejected, unresolved classification incomplete, cross-household reject |
| Determinism / provenance / precision | ordering/context tests, provenance identity change, exact arithmetic failure, floats/nonfinite rejected |
| No solver/ranking/utility/learning imports | source/import-guard adversarial matrix |
| No live DB reads/writes after capture | Engine query trap on real PG captured resolution |
| No source SQL bypass | direct INSERT negative nutrient + immutable quote UPDATE rejection |

Canonical nutrition facts are append-only: the concurrency test appends a new source version,
never disables immutable triggers or updates the old fact. No test-only authority bypass is added.

## Verification

Final local full regression: **1158 passed in154.52s**, including **514 PostgreSQL-real cases**,
**0 skipped /0 failures /0 errors**. XML identity comparison retains all **1089 pre-existing tests**;
**69 new =57 unit/adversarial +12 PostgreSQL-real**. No old tests edited/deleted.
One existing Starlette/httpx deprecation warning remains; no dependency change is made.

Executed successfully:

- Full `python -m pytest --junitxml=.local/grounding-full.xml` with real local PostgreSQL18;
  marker collection independently confirms514 real-PG tests, migration/drift/concurrency included.
- Ruff;30-INV/11-ADR/50-task architecture baseline;16-context import boundaries.
- Domain/OpenAPI export and22 synthetic fixture drift checks.
- Synthetic benchmark **22/22** (HARNESS_SMOKE_NOT_PLANNER_V4).
- Client generated-contract check/typecheck; **10/10 client tests**; TypeScript/Vite web build.
- Frozen-source AST/byte comparison and146-old-definition schema comparison against reviewed main.

Local logs/XML:
`.local/grounding-full.log`, `.local/grounding-full.xml`; focused PG `.local/grounding-pg.xml`;
benchmark `.local/grounding-benchmark.json`. Benchmark is HARNESS_SMOKE_NOT_PLANNER_V4.

## Changed files

30 files: new neutral ResolutionError; additive Recipe/Nutrition/Retail/Inventory/Planning contracts
and public facades; new nutrition/resolution.py, retail/grounding.py, inventory/grounding.py,
planning/grounding.py and grounding_capture.py; grounding fixtures/unit/real-PG tests; import guard,
domain export/bundle13/README; review/evidence/status/blueprint/backlog/invariant coverage/glossary.
No ORM model, database migration, frozen generator/validator implementation or prior test changed.

## Deferred / parent status

No MTR-020 Pareto, MTR-021 feasibility, MTR-022 optimizer, MTR-024 utility, execution,
production PRECOMMIT/TOCTOU authorization or full Independent Validator. Unknown retail supply
is conditional; no price freshness/outlier/scenario policy or actual basket checkout-cost evaluator
is invented. Global lot/package/meal/member allocations and chronology remain unresolved by design.
COUNT nutrition/count-to-mass and allergen/diet classification are unavailable, not fake supported.

**Full MTR-019 remains PARTIAL:** supported culinary generation/binding/primitive grounding is
implemented, while evidence-backed generation triggers/reasons and wider source/grounding quality
coverage remain prerequisites. This does not auto-certify the MTR-020 policy/metrics design.
MTR-026 remains incomplete; grounded candidates are not production validation authority.
No following milestone started. **READY FOR ARCHITECTURE/FREEZE REVIEW** for MTR-019C only.
