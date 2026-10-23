# MTR-019A / Independent RecipeGroundingValidator evidence

Reviewed base: `33297e89f3db68e4695ae8659f01cb16cbf1504d`.
[Architecture A–J](MTR_019A_CULINARY_BINDING_REVIEW.md) was written before code.
Final implementation commit: `10c1693eaa3aaa2735d9cb073e56ad193c81d0a4` (initial implementation checkpoint `522f44e297a5402a4ff75d4749a105bd31070b61`).
PR: https://github.com/thedusk4203/Menuto/pull/65. Final CI is recorded after remote verification below.
Status: submitted for architecture/freeze review, never self-FROZEN.

## Delivered model

Planning owns `planned_culinary_bindings` and `culinary_requirement_bindings`.
Header ownership is exact household/plan/proposal/batch; each requirement record contains
its own rule, ingredient, calculated quantity/basis/item_ref, adjustment and transformation.
No parallel arrays, generic conversion table, physical lot or execution event is introduced.
New proposal rows copy intent; old proposal/revision history remains immutable.

Migration: `0010_planned_culinary_bindings.py`; **54 domain tables** (two added).
Changed existing schema: plan_proposals version CHECK admits v3; preparation_transformations
adds a redundant unique(id,recipe_version_id) as target of the new composite provenance FK.
No recipe fact or historical migration0001–0009 is rewritten. Migration contains frozen SQL,
not ORM imports. Downgrade rejects any v3 proposal/history rather than guessing a legacy graph.

Versions: planned-culinary-binding.v1; plan-intent.v3; plan-propose.v2-culinary;
plan-proposal.v2-culinary; plan-revision.v2-culinary; active-plan.v2-culinary;
culinary-validation-input.v1; recipe-grounding-report.v1. Domain export bundle11.
The original plan-intent.v1/v2 and validation-subject.v1-foundation remain separate unchanged types.

Full binding fingerprint includes proposal ownership. The semantic batch signature excludes
proposal_id/fingerprint but retains household/plan/batch, resolved facts and provenance. Thus
an unchanged copy does not falsely revise every meal, while an actual binding change affects
closure, cut-line, reservation target, graph hash and materialization pins. V3 cannot silently
downgrade future intent to an unbound legacy graph. Legacy rows remain readable/migratable.

Calculated quantities are preserved as exact calculated-intent facts (72 digits /36 places),
not coerced to StoredQuantity or physical stock. Adjustments retain Foundation18/6. PostgreSQL
unconstrained NUMERIC + finite/range/scale CHECKs reject loss, rather than typmod rounding.
This slice does not persist a calculated physical quantity or invent quantization policy.

## Independence

The explicit producer invokes the frozen authored culinary resolver. The validator does not:
it reconstructs expected ingredients/amounts/rules/combination/tier/path in its own imperative
pass over authored primitive facts, then checks captured claims and independently serialized
fingerprints. It does not trust GroundedRecipeVariantDraft or cached valid fields. No solver,
generator, planning runtime, database, repair or physical writes enter the enforcement path.

Source capture reads exact sealed proposal and RecipeVersions through public facades in a
read-only RR/SERIALIZABLE transaction. The companion is self-contained and versioned; it does
not append fields to frozen MTR-025. All reports remain activation_authorized=False.
PRECOMMIT authority guard is unchanged. POSTFACT only reports discrepancies.

## Named regression matrix

| Required case | Evidence tests |
| --- | --- |
| Default / single authored substitution | test_exact_default_roundtrip_determinism_and_immutability; test_valid_single_authored_substitution; PG roundtrip[False/True] |
| Unauthorized, foreign version/requirement, duplicate slot rules | test_requirement_mutation_matrix; test_wrong_version_rule_and_count_substitution_fail_independently; PG invalid SQL assembly |
| Multiple structural rules / exact approved set | test_structural_combination_exact_approval; test_db_exact_structural_combination |
| COUNT substitution / wrong item_ref | independent requirement matrix and PG count_substitution/wrong_item_ref |
| Wrong ingredient / basis / quantity | unit matrix + PG wrong_ingredient/wrong_basis/amount |
| Below/above adjustment envelope / discrete step | unit below_min/above_max + test_discrete_step_rejected_and_scaling_recomputed; SQL bounds |
| Tier / serving count / gram-adjustment seam | owner_tier_serving mutations; test_micro_adjustment_preserves_explicit_servings; SQL tier/servings |
| Wrong/missing path; substitute-only transform | unit wrong_transform/missing_transform; test_raw_base_when_only_substitute_has_preparation_path; SQL transforms |
| Forged fingerprint / bad producer output | owner fingerprint mutation; test_forged_producer_output_caught_without_using_producer; SQL fingerprint |
| Cross-household/plan/proposal/batch | owner mutations; composite FK/SQL invalid assembly |
| Seal UPDATE/DELETE/TRUNCATE/late INSERT | test_direct_sql_sealed_immutability, both new tables |
| Revision retains old binding; new rows/hash | test_old_revision_retains_binding_new_revision_is_new_owned_fact |
| SINGLE_MEAL includes binding-only shared-batch changes | test_binding_change_of_shared_batch_requires_multi_meal_closure |
| Historical own-anchor / materialization pin | test_historical_binding_cannot_be_rewritten_through_binding_only_delta; test_materialization_pin_covers_binding_only_change |
| Stale revision / exact idempotent retry | test_bound_retry_and_stale_revision_are_deterministic |
| Legacy graph and frozen subject hashes | test_culinary_legacy_compatibility.py golden cases; populated0009/0010 roundtrip |
| Zero DB reads/writes and producer enforcement independence | real Engine query trap after capture; producer monkeypatch trap; import negative matrix; diagnostic immutability |
| Migration / populated loss / drift | 0009→0010→0009→0010 empty + populated legacy, populated v3 downgrade fails; existing metadata checks |

Golden hashes were captured only after AST comparison proved the original PlanIntentGraph,
PlanProposalSnapshot/PlanRevisionSnapshot and ValidationSubjectSnapshot/frontier class bodies
match approved commit219b556. New types are additive. The golden constants are not regenerated
during tests. Existing tests are retained; head/table assertions move to0010/54; the expanded old immutability matrix seeds real binding rows, and the old
0008/0009 migration test checks current metadata at head before returning to the older revision.

Some PostgreSQL tests deliberately disable an immutable UPDATE trigger as test database owner
to corrupt private unsealed assembly, then verify FK/CHECK/seal validation rejects it. Production
has no such bypass. Historical UPDATE/DELETE/TRUNCATE/late inserts are separately tested with
all guards enabled. Activation/revision transaction plumbing uses the existing explicitly
synthetic DB-owner receipt fixture, never a production issuer. Prepared manual assets used to
test materialization pins are existing confirmed ledger fixtures, not new CookingBatch execution.

## Executed verification

Final full local regression: **1034 passed**, **495 real PostgreSQL tests** (pytest postgres
marker count), **938 prior tests retained**, **96 new cases** (47 standalone unit/golden,
43 new PostgreSQL cases,6 additional cases in the existing table immutability matrix).
**0 skipped,0 failures,0 errors**. One pre-existing Starlette/httpx deprecation warning.
Command: `.venv/Scripts/python.exe -m pytest --junitxml=.local/culinary-strict-final.xml --tb=short`,
MENUTO_TEST_POSTGRES_URL points to isolated PostgreSQL18.4 on localhost; duration147.86s.
Schema/ORM drift, empty and data-bearing migration roundtrips, lossy downgrade refusal,
concurrent proposal writes, direct SQL guards and all previous regressions pass.
Ruff,30-invariant/11-ADR baseline,16-context import checks, domain/OpenAPI/fixture export
checks and documentation links pass. Benchmark **22/22**, explicitly synthetic harness only;
client **10/10**, generated contract check, client/web TypeScript and web production build pass.
Remote PR/postmerge CI results follow after execution; no future success is claimed here.

## Explicitly deferred / no claims

Not full MTR-019: no demand-driven VariantGenerator, candidate search, shortlist or ranking.
Not full MTR-026: no root nutrition policy, allergen classification, nutrition grounding,
retail/procurement/scenario grounding, planned physical material allocation, batch-flow execution,
assumption graph, horizon bridge, source-frontier TOCTOU issuer or production authorization.
No Planner V4, optimizer, AI, CookingBatchExecution, MealExecution or physical materialization.
No generic UnitConversion; Retail AP→EP and Recipe EP_RAW→COOKED retain their frozen owners.
No live UX/import workflow. Stop at this slice; do not start another prerequisite automatically.


## Changed-file manifest

- `README.md`
- `apps/backend/README.md`
- `apps/backend/app/modules/cooking/public.py`
- `apps/backend/app/modules/execution/culinary_capture.py`
- `apps/backend/app/modules/execution/public.py`
- `apps/backend/app/modules/planning/binding_models.py`
- `apps/backend/app/modules/planning/contracts.py`
- `apps/backend/app/modules/planning/culinary.py`
- `apps/backend/app/modules/planning/models.py`
- `apps/backend/app/modules/planning/public.py`
- `apps/backend/app/modules/recipes/models.py`
- `apps/backend/app/modules/validation/README.md`
- `apps/backend/app/modules/validation/contracts.py`
- `apps/backend/app/modules/validation/recipe_grounding.py`
- `apps/backend/app/persistence/models.py`
- `apps/backend/migrations/versions/0010_planned_culinary_bindings.py`
- `apps/backend/tests/culinary_fixtures.py`
- `apps/backend/tests/test_culinary_grounding.py`
- `apps/backend/tests/test_culinary_legacy_compatibility.py`
- `apps/backend/tests/test_foundation_migration.py`
- `apps/backend/tests/test_postgres_culinary_bindings.py`
- `apps/backend/tests/test_postgres_plan_semantics.py`
- `apps/backend/tests/test_postgres_plans.py`
- `apps/backend/tests/test_postgres_retail.py`
- `apps/backend/tests/test_postgres_validation.py`
- `docs/product/BACKLOG.md`
- `docs/product/FOUNDATION_STATUS.md`
- `docs/product/GLOSSARY.md`
- `docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md`
- `docs/product/INVARIANT_COVERAGE.md`
- `docs/product/MTR_019A_CULINARY_BINDING_EVIDENCE.md`
- `docs/product/MTR_019A_CULINARY_BINDING_REVIEW.md`
- `packages/contracts/README.md`
- `packages/contracts/domain.schema.json`
- `tools/check_import_boundaries.py`
- `tools/export_domain_contracts.py`


Final boundary correction: v3 classes are separate contracts rather than legacy subclasses.
A reproduced Pydantic nested-instance case accepted a v3 object under the old type before
rejecting its JSON. Two new regression cases enforce both object and wire rejection without
changing any frozen class/hash. The final implementation SHA and full local counts above include this correction; the
initial implementation checkpoint is retained only for audit history.

The producer-disagreement test also recomputes internally consistent forged binding/graph hashes: the independent semantic check still emits CULINARY_RESOLUTION with no fingerprint/signature mismatch. Focused unit/golden suite47/47 passes after strengthening that assertion.


## Remote CI evidence

PR **#65**: https://github.com/thedusk4203/Menuto/pull/65.
Final implementation: `10c1693eaa3aaa2735d9cb073e56ad193c81d0a4`.
Verified PR head `379f5db0bfc229436817746dde251b43cf05f8fe`,
[Foundation checks run43](https://github.com/thedusk4203/Menuto/actions/runs/39899290204):
**python SUCCESS; web SUCCESS**. Python log confirms **1034 passed** in59.13s,
zero skipped/failures/errors and benchmark **22/22**. Web confirms client **10/10**,
contract/type checks and production build success.
This evidence-only commit changes no runtime/tests/migration. Its own CI and postmerge
CI must also pass before delivery; exact merge SHA and final run links are recorded in
the delivery report, rather than claiming a future result here.

**READY FOR ARCHITECTURE/FREEZE REVIEW** — MTR-019A only. Full MTR-019/MTR-026 are
incomplete. No self-freeze, Execution or following prerequisite implementation.
