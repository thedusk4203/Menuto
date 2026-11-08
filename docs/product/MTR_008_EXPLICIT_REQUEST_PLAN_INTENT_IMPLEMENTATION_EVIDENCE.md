# MTR-008 Explicit-Request Orthogonal Plan-Intent Resolution — implementation evidence

**STRUCTURAL / TEST_ONLY — IMPLEMENTATION READY FOR INDEPENDENT REVIEW — NOT MERGED / NOT FROZEN**

## Approved scope and identity

- Baseline: `b7992898698a8a8a3493b3c260939325cc494063`; tree `1933ed1b5bee14a2a4800c08d42b477a3ef89fc6`.
- [Approved design PR142](https://github.com/thedusk4203/Menuto/pull/142), head `584ef315ce46bf9304d85de724c2fbdf85575c90`.
- [Independent detailed-design PASS6719067953](https://github.com/thedusk4203/Menuto/pull/142#issuecomment-6719067953).
- [Design completion6719670106](https://github.com/thedusk4203/Menuto/pull/142#issuecomment-6719670106).
- Exact baseline push CI42461830258 SUCCESS;4,369 retained tests, not new EPI execution.
- Owner separately authorized implementation and then the narrow conditional8-file/17-block
  metadata edits plus exact named-contract import allowance. That authorization is not an
  independent implementation review, merge or structural freeze.

## Final capability / ownership

Policy interprets one fully explicit retained declaration. Immutable versioned companions
carry four independent axes and explicit NONE/TARGET/SPEND_LIMIT money semantics. Zero is a
real declared value. Unknown/missing/invalid/resource cases never produce a partial payload.
No inferred defaults, week/override precedence, BudgetPressure, coefficients or numeric policy.

Producer uses bounded recursive descent after a complete lexical resource preflight.
Validation uses its own lexical limits, standard strict JSON decoding and independent semantic
reconstruction. No producer/public/helper import is available to Validation. Both bound
bytes/structure/integers before canonicalization and inspect only exact accepted model/container
classes; custom serialization hooks, cycles and arbitrary mappings cannot supply authority.
Checks compare whole reconstructed claims, including evidence ordering despite order-insensitive
collection hashes. Fresh CONSISTENT reports remain UNVERIFIED_TRANSPORT/NOT_ADMITTED.

Coherent replacement of both source and result can be offline consistent; it is still an
unauthenticated declaration. UUIDs, hashes, revisions and future timestamps do not prove
member/household access, authorship, source origin, freshness or a PIV lease.

No adapter to frozen PlannerRequestDraft, NutritionPrecisionSelection or PolicyV2Use.
No numerical consumer, HTTP endpoint, DB capture, source publication or production admission.
No DB objects/roles/privileges/persistence/migration added. Schema remains0017/108.
Fresh-install proof independently migrated a disposable DB to0017/108 and checked every
canonical Root table plus every synthesis table:all23 are empty. Production content/providers/
enrollments/qualifications/publications/defaults remain0. No new production content installed.

## Module / export inventory

- `apps/backend/app/modules/policy/explicit_intent_contracts.py`: exact nine immutable contracts.
- `apps/backend/app/modules/policy/explicit_intent.py`: pure bounded producer.
- `apps/backend/app/modules/policy/explicit_intent_public.py`: one pure interface, no admission facade.
- `apps/backend/app/modules/validation/explicit_plan_intent.py`: independent checker.
- `tools/export_domain_contracts.py`: additive import/registration only.
- `packages/contracts/domain.schema.json`: exact9 additive definitions, every528 old body retained.

Exact independently authored [nine-name manifest](../../apps/backend/tests/fixtures/explicit_plan_intent_export_names.json):

```json
[
  "ExplicitPlanIntentContextV1",
  "ExplicitPlanIntentBudgetV1",
  "ExplicitPlanIntentRequestV1",
  "ExplicitPlanIntentValuesV1",
  "PlanIntentAxisEvidenceV1",
  "ResolvedExplicitPlanIntentV1",
  "PlanIntentDiagnosticV1",
  "PlanIntentResolutionV1",
  "PlanIntentCheckV1"
]
```

**537 =528 retained +9 additive.** New
[compatibility manifest](../../apps/backend/tests/fixtures/explicit_plan_intent_compatibility.json)
pins all528 original body hashes and4,369 retained test identities. Four historical tests use
UUID4 parameter values generated at collection time; the new retention proof follows existing
UUID normalization, preserves module/function/parameter structure and uses Counter multiplicity.
No retained test, name, hash assertion, skip/xfail policy or frozen behavior was removed.

## Narrow historical adjustments and integrity proof

The actual full unified diff for exactly9 historical files is retained in
[MTR_008_EXPLICIT_INTENT_AUTHORIZED_COMPATIBILITY.diff](MTR_008_EXPLICIT_INTENT_AUTHORIZED_COMPATIBILITY.diff).
The8-test-file17-block map is
[authorized metadata](../../apps/backend/tests/fixtures/explicit_plan_intent_authorized_metadata.json).
Before/after hashes for all9 files are
[guard hashes](../../apps/backend/tests/fixtures/explicit_plan_intent_changed_guard_hashes.json).

| Historical file | Authorized replacement blocks |
| --- | ---: |
| test_candidate_feature_projection.py |1|
| test_hierarchical_affinity_compatibility.py |1|
| test_hierarchy_compatibility.py |1|
| test_nutrition_resolution.py |2|
| test_nutrition_root_architecture.py |3|
| test_tastefit_architecture.py |4|
| test_shared_target_tastefit_architecture.py |2|
| test_policy_v2.py |3|

PIV-D31 preserves its original13 literal names,515 legacy definitions,4,183 baseline test IDs,
all original inverse rules and all expected hashes. The export-name block also checks exact9
EPI names separately and total537; the difference from515 is precisely13 PIV union9 EPI.
The new preimage pass restores only exact approved EPI metadata occurring once to528-era
source, then executes the original PIV inverse rules and original full-file hash comparison.
No historical fixture/digest is updated. New metadata proof reverses all17 blocks and compares
full original8 source hashes. Mutation tests prove unknown exports, altered old bodies,
modified historical assertions and incorrect normalization fail the retained PIV-D31 guard.

The9th historical file, `tools/check_import_boundaries.py`, permits only imports of the9
named immutable definitions from the exact Validation checker. It is not a module/prefix
permission or early return: existing checks still execute. Wildcards, helpers, producer,
public facade, other contexts/modules and dynamic imports remain rejected. Direct/transitive
negative tests and runtime producer-oracle sabotage prove independence.

## Execution evidence

- Focused run: **242 passed /0 skips**; source/type/shape/preimage/architecture/adversarial cases.
- Additional deterministic byte-mutation differential diagnostic:700 cases,0 mismatches;
  this is a diagnostic and is not added to pytest totals.
- Real local PostgreSQL18 disposable test cluster with SCRAM and TLS verify-full: **16/16**
  authentication smoke cases passed. New EPI PostgreSQL obligations: **zero** for the pure scope.
- Ruff, architecture30 invariants/11 ADRs/50 tasks, import16 contexts, OpenAPI, domain exports,
 22 synthetic fixtures, benchmark22/22, client10/10, client typecheck and web build PASS.
- **Full local regression: 4,611 passed /0 skips**,4 retained warnings in5253.69s, from a single
  run with real PostgreSQL enabled:4,369 baseline+242 additive. JUnit records1,384 executions
  in test_postgres_* modules (this label is not a new EPI PG-obligation count).
- **Exact-head GitHub Actions: PENDING**, must run after implementation submission.

Focused counts are not summed with earlier baseline/diagnostic runs. A single successful full
run and exact-head CI must independently execute the retained corpus plus additive tests.
The first focused iteration exposed nondeterministic UUID4 parameter IDs in the new retention
proof; only that new proof was corrected to the existing normalization pattern. Historical
fixtures/test identities remain unchanged. Subsequent focused execution passed all242 cases.

## EPI001–EPI064 → executed named-test mapping

Individual parameter executions are retained in
[acceptance mapping](../../apps/backend/tests/fixtures/explicit_plan_intent_acceptance_mapping.json).
This table comes from actual full-suite JUnit XML, not collection-only or a prose checklist.
Counts per family overlap only for the explicitly combined resource/precedence adversarial test;
never sum family counts into a full-suite result.

| ID | Executed function(s) | Parameter executions |
| --- | --- | ---: |
| EPI001 | `test_epi001_all_81_combinations` | 81 |
| EPI002 | `test_epi002_precision_orthogonal` | 1 |
| EPI003 | `test_epi003_cost_orthogonal` | 1 |
| EPI004 | `test_epi004_effort_orthogonal` | 1 |
| EPI005 | `test_epi005_budget_orthogonal` | 1 |
| EPI006 | `test_epi006_no_numerical_policy` | 1 |
| EPI007 | `test_epi007_none_not_zero_or_absence` | 1 |
| EPI008 | `test_epi008_target_is_intent_only` | 1 |
| EPI009 | `test_epi009_limit_not_feasibility` | 1 |
| EPI010 | `test_epi010_target_zero` | 1 |
| EPI011 | `test_epi011_limit_zero` | 1 |
| EPI012 | `test_epi012_none_with_amount_invalid` | 2 |
| EPI013 | `test_epi013_non_none_requires_amount` | 2 |
| EPI014 | `test_epi014_integer_boundary` | 1 |
| EPI015 | `test_epi015_no_numeric_coercion` | 4 |
| EPI016 | `test_epi016_currency_exact` | 4 |
| EPI017 | `test_epi017_currency_semantic_identity_not_support` | 1 |
| EPI018 | `test_epi018_null_axis_is_missing` | 4 |
| EPI019 | `test_epi019_absent_field_not_default` | 8 |
| EPI020 | `test_epi020_invalid_axis_not_missing` | 5 |
| EPI021 | `test_epi021_context_invalid` | 4 |
| EPI022 | `test_epi022_horizon_and_offset_normalization` | 1 |
| EPI023 | `test_epi023_context_identity_changes` | 7 |
| EPI024 | `test_epi024_future_metadata_not_authentication` | 1 |
| EPI025 | `test_epi025_context_not_semantic_equality` | 1 |
| EPI026 | `test_epi026_full_source_identity` | 1 |
| EPI027 | `test_epi027_evidence_unique_order_before_hash` | 1 |
| EPI028 | `test_epi028_replay_across_process_hash_seeds_and_environment` | 1 |
| EPI029 | `test_epi029_json_spelling_not_identity` | 1 |
| EPI030 | `test_epi030_domain_separation_and_no_recursive_hash` | 1 |
| EPI031 | `test_epi031_strict_wire_parser` | 6 |
| EPI032 | `test_epi032_no_hidden_selection` | 7 |
| EPI033 | `test_epi033_unsupported_headers` | 3 |
| EPI034 | `test_epi034_claim_epoch_coercion_not_accepted`, `test_epi034_constructed_models_revalidated` | 2 |
| EPI035 | `test_epi035_unsafe_objects_never_execute_hooks` | 1 |
| EPI036 | `test_epi036_encoded_byte_boundary` | 1 |
| EPI037 | `test_epi037_absolute_structure_limits`, `test_epi037_epi040_wire_resources_before_semantic_or_duplicate_errors`, `test_epi037_huge_integer_model_guard_before_stringification` | 10 |
| EPI038 | `test_epi038_work_budget_no_partial_success` | 1 |
| EPI039 | `test_epi039_claim_limit_is_not_checkable` | 1 |
| EPI040 | `test_epi037_epi040_wire_resources_before_semantic_or_duplicate_errors`, `test_epi040_deterministic_failure_precedence` | 4 |
| EPI041 | `test_epi041_fresh_positive_independent_check` | 1 |
| EPI042 | `test_epi042_faithful_negative_consistent` | 4 |
| EPI043 | `test_epi043_rehashed_changed_axis_rejected` | 1 |
| EPI044 | `test_epi044_rehashed_budget_substitution` | 3 |
| EPI045 | `test_epi045_forged_context_and_evidence` | 1 |
| EPI046 | `test_epi046_tampered_hash_rejected` | 1 |
| EPI047 | `test_epi047_forged_positive_for_negative` | 1 |
| EPI048 | `test_epi048_forged_negative_for_positive` | 1 |
| EPI049 | `test_epi049_report_not_validation_proof` | 1 |
| EPI050 | `test_epi050_coherent_source_replacement_not_authority` | 1 |
| EPI051 | `test_epi051_absent_primitives_not_checkable` | 1 |
| EPI052 | `test_epi052_checker_never_calls_producer` | 1 |
| EPI053 | `test_epi053_static_direct_transitive_independence` | 1 |
| EPI054 | `test_epi054_no_taint_or_flag_promotion` | 6 |
| EPI055 | `test_epi055_no_lease_or_numeric_policy` | 1 |
| EPI056 | `test_epi056_no_physiological_policy_claims` | 1 |
| EPI057 | `test_epi057_no_feasibility_or_activation` | 1 |
| EPI058 | `test_epi058_pure_modules_no_io_or_globals` | 1 |
| EPI059 | `test_epi059_all_528_bodies_and_exact_nine_delta` | 1 |
| EPI060 | `test_epi060_frozen_files_no_new_migration_or_persistence` | 1 |
| EPI061 | `test_epi061_all_retained_identities_and_metadata_integrity` | 1 |
| EPI062 | `test_epi062_no_content_or_authority_installation` | 1 |
| EPI063 | `test_epi063_governance_and_non_authority` | 1 |
| EPI064 | `test_epi064_exact_bounded_public_surface` | 1 |

## Compatibility / stop boundaries

All528 old definition bodies,515 legacy/503 historical hashes,53 historical frozen files and
59 full PIV pins are preserved. Earlier broader frozen manifests still execute unchanged.
No0018, persistence, SQL, roles or DB privileges shipped. Root/NPS/NRE/MBA/PIV implementation
identities and semantics unchanged. Original19 local files are checked against the protected
pre-task SHA256/status/HEAD snapshot; original worktree is never reset/discarded/committed/pushed.

Full MTR-006/007/008 INCOMPLETE; issues#5/#6/#7 OPEN. Production Nutrition/clinical gate CLOSED;
planner_ready=False;activation_ready=False;Execution NOT STARTED;PRECOMMIT FAIL-CLOSED.
No merge, freeze, clinical publication, source capture, downstream work or parent closure.
Implementation PR must remain OPEN /auto-merge OFF for independent exact-head review.

Machine-readable executed totals, fresh-install counts and artifact SHA256s: [execution receipt](MTR_008_EXPLICIT_INTENT_EXECUTION_RECEIPT.json).

## CI portability correction — EPI028

Initial PR run42476517519 on951dea7dd0e7714cfd9dedf8bf2fba2e60f5e2f2 failed only
EPI028:4,610 passed/1 failed because the subprocess did not inherit pytest's tests-directory
sys.path on Linux. Only the new replay test now supplies explicit backend/tests/project paths
using os.pathsep; it still compares independent subprocess results under two hash seeds and
malicious unrelated environment settings. No runtime, historical guard or fixture was changed.
The corrected test passed with the parent PYTHONPATH containing only apps/backend; the entire
focused242-case set was rerun under that clean parent environment. Final exact-head full CI
must pass; the earlier failed run is not used as success evidence.
