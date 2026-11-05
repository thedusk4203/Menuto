# MTR-007 Source-Bound NutritionResolutionEstimator — implementation evidence

**IMPLEMENTATION CANDIDATE — NOT REVIEWED / NOT FROZEN.**

This implements the bounded structural design, not complete MTR-007, a nutrition policy
integration, production scientific content, consumption attribution or planner activation.
The implementation PR must remain OPEN with auto-merge OFF for independent review.

## 1. Authorization and immutable baseline

- Approved design: [PR #129](https://github.com/thedusk4203/Menuto/pull/129), reviewed head
  `e376686f58c0f5ecbaed25138188841951237ea9`.
- [Architecture PASS 6655233374](https://github.com/thedusk4203/Menuto/pull/129#issuecomment-6655233374).
- Design merge / implementation base: `88440a270602aed78e2d28ee9bc9a1be049b267e`.
- [Post-merge completion 6657069463](https://github.com/thedusk4203/Menuto/pull/129#issuecomment-6657069463).
- Exact baseline main push [CI 42014306050](https://github.com/thedusk4203/Menuto/actions/runs/42014306050):
  SUCCESS, **3,912 tests / 0 skips**, **480 exported definitions**, **0017 / 108 domain tables**.
- Implementation is separately authorized by the task following that approved design merge.

The original design remains the reviewed design artifact. Its pre-implementation gate wording
is historical; this evidence and the current status notices record the implementation candidate.
No frozen Root, MTR-006 v1, preference, inventory or recipe-grounding semantics are changed.

## 2. Implemented boundary and module inventory

| Owner / file | Responsibility |
| --- | --- |
| Nutrition `resolution_contracts.py` | Immutable request, captured scope, complete sources, finite configuration/vector/gap results, untrusted check transport and terminal `NutritionResolutionHandoffV2` |
| Nutrition `resolution_limits.py` | Server-owned parser/structure/integer/cardinality/arithmetic budgets; checked exact rational primitives |
| Nutrition `resolution_estimator.py` | Fresh primitive replay and exact enumeration of the declared finite scope; no I/O or clinical/policy synthesis |
| Nutrition `resolution_public.py` | Estimate export and freshly constructed unverified terminal handoff; no v1 cast or integration adapter |
| Planning `nutrition_resolution_capture.py` | One authenticated actual PostgreSQL reader, coherent cut, owner reads, complete capture/absence witnesses and TEST_ONLY deployment binding |
| Validation `nutrition_resolution_authority.py` | Additive independent reconstruction of retained synthesis-rule enrollment, grants, review, publication, selection and effective-time history |
| Validation `nutrition_resolution.py` | Independent root/requirement/source verification, separately implemented ingredient fold and period sumset, fresh handoff verification |
| Catalog `public.py` addition | Count-before-materialize bounded reads of exact ingredient identities and **all** their nutrition-reference rows |
| Recipes `public.py` addition | Explicit version/child/seal counts and immutable owner snapshot reconstruction |
| Households `public.py` addition | Exact actor membership and planning-subject witness; no member-goal or clinical authorship authority |
| `tools/check_import_boundaries.py` addition | Closed per-file NRE companion import lists; independent checker cannot import estimator, synthesis business implementation or live-source adapters |
| `tools/export_domain_contracts.py` / domain schema | Additive export registration; all 480 baseline definition bodies remain unchanged |

The producer replays the frozen source-bound requirement projection. The checker independently
reconstructs requirements from retained published rule and independently verified roots. Its
authority replay is an additive Validation-owned companion, not an import/call of producer
business logic or the frozen policy checker as an oracle for resolution arithmetic.

## 3. Source capture and permissions

NRE001 proves the composed ordinary reader works on real PostgreSQL with existing Root and
synthesis authority protections intact. The reader needs its independently enrolled
`ROOT_SOURCE_READ` and `SYNTHESIS_SOURCE_READ` grants, plus SELECT on exactly these owner
relations for this additive capture seam:

```text
households                       household_members
ingredients                      memberships
nutrition_facts                  preparation_transformations
recipe_combination_members       recipe_ingredients
recipe_portion_tiers             recipe_rule_combinations
recipe_tier_quantities           recipe_variant_rules
recipe_version_seals             recipe_versions
recipes
```

These fifteen SELECT grants are provisioned only on isolated TEST_ONLY fixture logins in the
tests. No migration, automatic production grant, blanket schema/table privilege, direct source
journal read, DML privilege, table ownership or new source capability is installed. Ordinary
root/rule authority is still checked by the frozen protected PostgreSQL paths against actual
authenticated database/login OIDs, role membership and privilege graphs. Household OWNER/EDITOR
permits bounded planning intent, never guideline publication or another member's goal authorship.

Capture requires one clean caller-owned ordinary, single-Engine SQLAlchemy Session, read-only
REPEATABLE READ or SERIALIZABLE. It rejects cached ORM identities, mapper-bind maps and custom
routing Session subclasses: one Session object alone does not prove one actual connection/cut,
and old identity-map objects cannot replace fresh owner reads. It does not flush, commit, roll
back, change isolation or combine separate sessions.
The retained frame binds endpoint/database/login, backend PID, native MVCC snapshot, root/rule
frontiers and grants, exact membership/subject, observed capture interval and all owner rows.
Concurrent catalog commits and authority revocations are tested using separate real connections.
Retained old-cut replay makes no present-authority claim.

The fixed capture search path places trusted `pg_catalog,public` before `pg_temp`; writable
public schemas and unsafe actors are rejected. A pre-existing temporary shadow table cannot
replace canonical owner rows. Reader/source-owner/superuser/SET ROLE failures stay failures.
Source counts precede materialization, a statement timeout bounds each read, and a server-owned
watchdog cancels blocked PostgreSQL work. Failure returns no partial successful capture; recovery
of an aborted transaction remains the caller's responsibility.

### Capture-specific requirement identity

`NutritionResolutionScopeRequestV1` is selection-only ingress: exact subject/actor, root request,
rule selection, explicit precision, complete recipe/tier/rule/reference and serving selectors.
It has no caller-authored requirement fingerprint. Frozen root result identity includes its
capture frame, so callers cannot predict the identity of a future fresh capture.

After canonical root/rule capture and fresh requirement replay, capture constructs the distinct
`NutritionResolutionScopeV1` and pins that exact requirement fingerprint. Retained source identity
includes both the bound scope and primitive source cut. Neither cached requirements nor a caller
claim of completeness replaces fresh canonical capture. This is request/retained-capture
separation; it does not alter frozen Root/NPS contracts or introduce a policy integration.

## 4. Finite arithmetic and scope

Each authored tier/rule choice retains its exact configuration witnesses. Per ingredient:

```text
quantity = authored_tier_quantity * authored_substitution_factor + authored_delta
contribution = quantity * reviewed_nutrient_amount / reviewed_reference_amount
```

All arithmetic uses reduced exact rationals. NONE supplies only delta zero; finite DISCRETE
includes both authored endpoints and enforces quantum alignment and positive final quantity.
Authored multi-structural substitutions require the exact reviewed combination. Unsupported
continuous/TO_TASTE envelopes or COUNT nutrition without a reviewed bridge block the whole
declared scope. No tier interpolation, decimal-storage grid, package-derived step or fallback
reference is synthesized. Raw/cooked reference bases must match; recipe yield is not nutrient
retention, absorption or an intake conversion.

`WHOLE_TIER_TO_SINGLE_TRACKED_MEMBER_V1` binds the exact authenticated author, member, slot,
RecipeVersion, authored tier/rules and serving definition. It means **planned offered food**.
Tier serving counts, portion factors, attendance, leftovers and SHARED participants cannot
silently rescale or allocate it. Partial/shared serving is unsupported.

Every reachable vector retains nutrient correlation and all equivalent configuration witnesses.
Period vectors are exact sums of declared slot choices. Reviewed calendar identity and exact
interval containment are required. A WEEK parent requires complete contiguous reviewed DAY cells
with declared contributions in each required cell; missing days never become zero. Parent sums
add the same planned-input basis and do not convert daily/weekly physiological constraints.

Sorted attainable values retain holes, exact adjacent gaps and endpoint witnesses. Singleton is
`NO_ADJACENT_STEP` with no numeric step. A gap larger than a comfort width is diagnostic only;
it proves neither no band intersection nor joint plan infeasibility. Empty/missing/unsupported
coverage exposes no partial numeric vectors. Resolution insufficiency, selected comfort violation,
hard-policy conflict and solver-proven infeasibility remain separate downstream concepts.

## 5. Resource, environment and trust boundaries

The versioned server profile is `NRE_STRUCTURAL_LIMITS_V1`: request 256 KiB; retained package
16 MiB; 32 versions; 512 references; 8,192 owner rows; 32 ingredients/version; 16 tiers and
16 rule sets/version; 14 slots; 64 alternatives/slot; 32 periods; 64 deltas/ingredient;
16,384 states/vectors; 65,536 witnesses; 1,000,000 arithmetic-work units; 256-bit integers;
nesting 32; string 100,000 characters; statement 15 s and whole-capture 60 s deadlines.
Caller budgets can tighten but never raise absolute ceilings. Cardinality is checked before
large products; overflow/timeout fails the entire operation. `work_used` is a deterministic
output-work footprint, not a wall-clock measurement or calibrated complexity score.

Production default is **no enabled capture context**. Internal trusted test/deployment bootstrap
supplies an immutable in-process `NutritionResolutionCaptureContext`, bound to the actual isolated
`nrc_test_` database OID/name and complete TEST_ONLY food-row manifest. Request JSON, fixture
labels, REVIEWED catalog status or fingerprints cannot mint that dependency. Unclassified/changed
rows reject. The Python process/bootstrap is trusted; the private context seal is not presented
as a hostile-Python-code security sandbox or a database-issued certificate. No HTTP endpoint or
public production ingress is introduced.

Pure replay verifies the retained TEST_ONLY manifest and source semantics. Complete coordinated
offline replacement can describe another internally consistent package; it still does not prove
database origin, current authorization/publication or scientific correctness. Reports and
handoffs remain `UNVERIFIED_TRANSPORT`. Consumers must call the independent checker freshly on
the complete retained sources and estimate. A supplied CONSISTENT report or matching public hash
cannot substitute for that check; adversarial tests cover this trust boundary explicitly.

## 6. Frozen integration and non-authority

`NutritionResolutionHandoffV2` uses `CANONICAL_FINITE_RESOLUTION_V2`. It is a terminal estimator
handoff, not the separately authorized future MTR-006 policy-integration v2 companion. No such
companion is implemented. Frozen MTR-006 v1 producer/checker remain fixture-only with unchanged
bodies, hashes, tests and accepted behavior. No v1 `expected_step` or fixture wrapper is minted.

Planned ingredient-input contribution and physiological intake are different measurement bases.
Metric/unit equality does not bridge them. Production basis applicability and scientific content
remain separately reviewed source prerequisites. Cost, budget, KitchenEffort, convenience,
TasteFit, DataConfidence and NutritionPrecision cannot create source truth or widen root/goal bounds.

All estimator/handoff results preserve:

```text
planner_ready=False                  activation_ready=False
policy_synthesis=NOT_PERFORMED        hard_policy_feasibility=NOT_EVALUATED
solver_infeasibility=NOT_PROVEN       consumption=NOT_ASSERTED
policy_integration=NOT_AUTHORIZED     production_admission=CLOSED
```

## 7. Persistence, compatibility and fresh install

- **No new persistence, migration, table, protected SQL function, role or durable authority.**
- Migration remains **0017**; domain tables remain **108**; no **0018**.
- **503 exported definitions = 480 retained + 23 additive**. The compatibility fixture stores
  canonical hashes of all 480 baseline definitions, 33 frozen source/migration files and the
  complete 3,912 baseline test identity multiset. NRE094/095 verify their retention.
- Fresh-install NRE020 executes actual migrations and inventories all 108 tables. All content
  tables are empty. Only the two unchanged 0013 zero-generation structural frontier sentinels
  exist (`ingredient_protein_frontier`, `culinary_feature_frontier`); they are not nutrition
  providers, qualifications, publications, fixtures, reference content or policy defaults.
- Production nutrition/clinical content, providers, enrollments, qualifications, publications,
  seeds and defaults added by this implementation: **0**. Test data is installed only in
  disposable test databases through privileged fixture setup, never migration/install state.

## 8. Executed acceptance and verification receipts

The final executed-test matrix and measured receipts are recorded below once verification
completes. Exact implementation-head CI is a required implementation-PR gate; it is not
substituted with the approved design CI or an earlier implementation head.

The matrix binds **NRE001–NRE096** to **135 additive executions: 36 real PostgreSQL
tests and 99 pure/adversarial/compatibility tests**. The first twenty obligations are executed
against real authenticated PostgreSQL protected/owner reads; collection or mocks do not satisfy
them. Parameterized node names below identify each execution, including real concurrent commits,
actual privilege failures, source limits, blocked-read cancellation and fresh installation.

The full implementation gate is **4,047 tests = 3,912 retained +135 additive, with 0 skips**.
The exact implementation head, full-suite execution result, actual PostgreSQL count, separate
16/16 SCRAM/TLS smoke, 22/22 benchmarks, 10/10 client tests and Python/web guard receipts are
recorded in the implementation PR verification receipt/body after CI completes. This avoids
putting a circular final-head SHA inside its own commit. No earlier-head/design CI or a collected
node list substitutes for that final-head execution. Until that receipt is SUCCESS, this
candidate is not verified or eligible for independent implementation acceptance.

Reproduction (with the disposable PostgreSQL test URL configured):

```text
uv run pytest --junitxml=<local-full-regression.xml>
uv run pytest apps/backend/tests/test_postgres_reference_prior_authority_extra.py apps/backend/tests/test_postgres_hierarchy_authentication.py
uv run python tools/check_architecture_baseline.py
uv run python tools/check_import_boundaries.py
uv run ruff check .
uv run python tools/export_domain_contracts.py --check
uv run python tools/export_openapi.py --check
uv run python tools/generate_synthetic_fixtures.py --check
uv run menuto-benchmark --output <benchmark-result.json>
npm run contracts:check
npm run typecheck:client
npm run test:client
npm run build:web
```

Tests below are in
[test_postgres_nutrition_resolution.py](../../apps/backend/tests/test_postgres_nutrition_resolution.py)
for PG and [test_nutrition_resolution.py](../../apps/backend/tests/test_nutrition_resolution.py)
for Pure. Each ID retains the exact approved assertion in the design matrix; helper tests may
cover several IDs, while parameterization expands individual executions.

| Case | Execution | Exact pytest test names / parameterizations |
| --- | --- | --- |
| NRE001 | PG | `test_nre001_composed_ordinary_reader_preflight`<br>`test_nre001_full_canonical_capture_and_independent_check` |
| NRE002 | PG | `test_nre002_payload_actor_uuid_cannot_spoof_database_author` |
| NRE003 | PG | `test_nre003_viewer_and_foreign_household_no_planning_authorship[VIEWER]`<br>`test_nre003_viewer_and_foreign_household_no_planning_authorship[NO_MEMBERSHIP]`<br>`test_nre003_viewer_and_foreign_household_no_planning_authorship[FOREIGN_HOUSEHOLD]` |
| NRE004 | PG | `test_nre004_independent_reader_grants_required[ROOT]`<br>`test_nre004_independent_reader_grants_required[SYNTHESIS]` |
| NRE005 | PG | `test_nre005_unsafe_actual_postgres_identity_rejected[superuser]`<br>`test_nre005_unsafe_actual_postgres_identity_rejected[set_role]`<br>`test_nre005_unsafe_actual_postgres_identity_rejected[source_owner]`<br>`test_nre005_nre016_temp_shadowing_does_not_change_canonical_owner_reads` |
| NRE006 | PG | `test_nre006_actual_transaction_mode_must_be_read_only_repeatable[READ COMMITTED-True]`<br>`test_nre006_actual_transaction_mode_must_be_read_only_repeatable[REPEATABLE READ-False]` |
| NRE007 | PG | `test_nre007_dirty_session_never_flushed[new]`<br>`test_nre007_dirty_session_never_flushed[dirty]`<br>`test_nre007_dirty_session_never_flushed[deleted]`<br>`test_nre007_dirty_session_never_flushed[cached]` |
| NRE008 | PG | `test_nre008_concurrent_catalog_commit_cannot_mix_snapshot` |
| NRE009 | PG | `test_nre009_concurrent_rule_revoke_respects_retained_knowledge_cut` |
| NRE010 | PG | `test_nre010_multiple_sessions_and_foreign_endpoint_not_one_cut` |
| NRE011 | PG | `test_nre011_missing_declared_source_captured_as_absence_not_partial_success[version]`<br>`test_nre011_missing_declared_source_captured_as_absence_not_partial_success[tier]`<br>`test_nre011_missing_declared_source_captured_as_absence_not_partial_success[reference]` |
| NRE012 | PG | `test_nre012_capture_retains_unselected_draft_reference_rows` |
| NRE013 | PG | `test_nre013_owner_recipe_seal_and_complete_children_reconstructed` |
| NRE014 | PG | `test_nre014_serving_authority_cannot_move_between_subject_slot_or_definition[subject]`<br>`test_nre014_serving_authority_cannot_move_between_subject_slot_or_definition[slot]`<br>`test_nre014_serving_authority_cannot_move_between_subject_slot_or_definition[serving_definition]` |
| NRE015 | PG | `test_nre015_revocation_blocks_fresh_capture_not_historical_replay` |
| NRE016 | PG | `test_nre016_actual_oid_role_frame_and_session_settings_retained`<br>`test_nre005_nre016_temp_shadowing_does_not_change_canonical_owner_reads` |
| NRE017 | PG | `test_nre017_future_observed_source_or_outside_root_interval_cannot_admit` |
| NRE018 | PG | `test_nre018_server_reference_limit_checks_real_sql_count_before_materialization`<br>`test_nre018_real_postgres_blocked_read_is_cancelled_without_partial_capture` |
| NRE019 | PG | `test_nre019_capture_has_no_writes_frontier_or_durable_cache` |
| NRE020 | PG | `test_nre020_fresh_install_0017_108_all_content_rows_zero` |
| NRE021 | Pure | `test_nre021_requirement_primitive_replay_and_forged_pin` |
| NRE022 | Pure | `test_nre022_descriptor_mismatch_before_arithmetic` |
| NRE023 | Pure | `test_nre023_missing_goal_or_supported_root_never_available` |
| NRE024 | Pure | `test_nre024_exact_declared_universe_and_scoped_identity` |
| NRE025 | Pure | `test_nre025_rehashed_favorable_subset_fails_original_scope` |
| NRE026 | Pure | `test_nre026_duplicate_equal_scope_normalized_conflicting_identity_rejected` |
| NRE027 | Pure | `test_nre027_empty_universe_is_not_zero_or_infeasible` |
| NRE028 | Pure | `test_nre028_unsupported_original_scope_cannot_return_surviving_subset` |
| NRE029 | Pure | `test_nre029_completeness_flags_or_capture_context_json_cannot_mint_authority` |
| NRE030 | Pure | `test_nre030_arbitrary_shortlist_input_cannot_claim_resolution_scope` |
| NRE031 | Pure | `test_nre031_foreign_recipe_version_or_body_detected_even_with_outer_hash` |
| NRE032 | Pure | `test_nre032_missing_seal_and_unauthorized_tier_detected`<br>`test_nre032_nre036_exact_substitution_and_structural_combination[False]`<br>`test_nre032_nre036_exact_substitution_and_structural_combination[True]` |
| NRE033 | Pure | `test_nre033_no_interpolation_between_authored_tiers` |
| NRE034 | Pure | `test_nre034_none_and_discrete_envelope_include_both_endpoints` |
| NRE035 | Pure | `test_nre035_negative_delta_is_exact_and_keeps_positive_composition` |
| NRE036 | Pure | `test_nre032_nre036_exact_substitution_and_structural_combination[False]`<br>`test_nre032_nre036_exact_substitution_and_structural_combination[True]`<br>`test_nre036_discrete_quantum_survives_every_enumerated_state` |
| NRE037 | Pure | `test_nre037_continuous_and_to_taste_are_not_discretized` |
| NRE038 | Pure | `test_nre038_count_without_approved_bridge_is_unsupported` |
| NRE039 | Pure | `test_nre039_nonzero_analysis_is_not_a_frozen_planner_candidate` |
| NRE040 | Pure | `test_nre040_pinned_reviewed_compatible_reference_matches_every_ingredient` |
| NRE041 | Pure | `test_nre041_draft_reference_never_falls_back` |
| NRE042 | Pure | `test_nre042_raw_cooked_reference_mismatch_is_not_a_conversion` |
| NRE043 | Pure | `test_nre043_cooking_mass_yield_does_not_change_input_nutrients` |
| NRE044 | Pure | `test_nre044_nonterminating_rational_never_rounded_to_decimal_or_float` |
| NRE045 | Pure | `test_nre045_explicit_numeric_zero_distinct_from_absence` |
| NRE046 | Pure | `test_nre046_coercion_float_boolean_and_nonfinite_rejected[True]`<br>`test_nre046_coercion_float_boolean_and_nonfinite_rejected[1.5]`<br>`test_nre046_coercion_float_boolean_and_nonfinite_rejected[nan]`<br>`test_nre046_coercion_float_boolean_and_nonfinite_rejected[inf]`<br>`test_nre046_coercion_float_boolean_and_nonfinite_rejected[1]` |
| NRE047 | Pure | `test_nre047_exact_reduction_and_signed_delta_are_distinct` |
| NRE048 | Pure | `test_nre048_omitted_ingredient_or_line_fails_independent_recomputation` |
| NRE049 | Pure | `test_nre049_exact_single_member_whole_tier_binding_retained` |
| NRE050 | Pure | `test_nre050_missing_assignment_is_not_inferred` |
| NRE051 | Pure | `test_nre051_no_divide_by_serving_count_or_portion_factor` |
| NRE052 | Pure | `test_nre052_partial_shared_leftover_allocation_rejected[nutrition_role-SHARED]`<br>`test_nre052_partial_shared_leftover_allocation_rejected[kind-FRACTIONAL_TIER]`<br>`test_nre052_partial_shared_leftover_allocation_rejected[fraction-0.5]`<br>`test_nre052_partial_shared_leftover_allocation_rejected[leftovers-True]`<br>`test_nre052_partial_shared_leftover_allocation_rejected[participants-value4]` |
| NRE053 | Pure | `test_nre053_cross_member_slot_or_serving_definition_does_not_transfer` |
| NRE054 | Pure | `test_nre054_planned_offered_never_consumed_or_accepted_exposure` |
| NRE055 | Pure | `test_nre055_joint_vector_correlation_not_marginal_extrema` |
| NRE056 | Pure | `test_nre056_equal_vectors_keep_all_configuration_witnesses` |
| NRE057 | Pure | `test_nre057_multi_slot_sums_match_small_independent_expected_set` |
| NRE058 | Pure | `test_nre058_gcd_does_not_fill_reachability_holes` |
| NRE059 | Pure | `test_nre059_exact_gaps_endpoint_witnesses_and_maximum` |
| NRE060 | Pure | `test_nre060_singleton_has_no_adjacent_step_not_zero` |
| NRE061 | Pure | `test_nre061_large_gap_elsewhere_does_not_imply_band_emptiness` |
| NRE062 | Pure | `test_nre062_marginal_hit_is_not_whole_plan_feasibility` |
| NRE063 | Pure | `test_nre063_no_proportional_slot_splitting_across_boundary`<br>`test_nre063_nre064_nre065_parent_period_sums_exact_declared_day_contributions[False]`<br>`test_nre063_nre064_nre065_parent_period_sums_exact_declared_day_contributions[True]` |
| NRE064 | Pure | `test_nre064_no_implicit_zero_for_missing_required_cell`<br>`test_nre063_nre064_nre065_parent_period_sums_exact_declared_day_contributions[False]`<br>`test_nre063_nre064_nre065_parent_period_sums_exact_declared_day_contributions[True]` |
| NRE065 | Pure | `test_nre065_temporal_sums_are_same_basis_contributions_not_clinical_conversion`<br>`test_nre063_nre064_nre065_parent_period_sums_exact_declared_day_contributions[False]`<br>`test_nre063_nre064_nre065_parent_period_sums_exact_declared_day_contributions[True]` |
| NRE066 | Pure | `test_nre066_cross_publication_horizon_change_cannot_reuse_requirement` |
| NRE067 | Pure | `test_nre067_source_after_cut_rejected_no_invented_ttl` |
| NRE068 | Pure | `test_nre068_retained_replay_stable_after_different_source_package` |
| NRE069 | Pure | `test_nre069_hostile_integer_nesting_duplicate_fields_preparse[9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999]`<br>`test_nre069_hostile_integer_nesting_duplicate_fields_preparse[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[0]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]`<br>`test_nre069_hostile_integer_nesting_duplicate_fields_preparse[{"a":1,"a":2}]` |
| NRE070 | Pure | `test_nre070_cartesian_limit_checked_without_allocating_product` |
| NRE071 | Pure | `test_nre071_intermediate_rational_and_complete_output_work_limit` |
| NRE072 | Pure | `test_nre072_caller_cannot_raise_profile_or_budget` |
| NRE073 | Pure | `test_nre073_pure_replay_survives_disabled_environment_and_file_access` |
| NRE074 | Pure | `test_nre074_operational_timeout_not_part_of_pure_estimator` |
| NRE075 | Pure | `test_nre075_server_fixture_manifest_required_not_test_label` |
| NRE076 | Pure | `test_nre076_mixed_environment_and_production_relabel_rejected` |
| NRE077 | Pure | `test_nre077_reviewed_catalog_and_test_pass_cannot_open_content_gate` |
| NRE078 | Pure | `test_nre078_rehashed_wrong_values_fail_independent_arithmetic` |
| NRE079 | Pure | `test_nre079_forged_consistent_report_with_matching_public_hashes_not_proof` |
| NRE080 | Pure | `test_nre080_model_copy_and_omitted_absence_not_trusted` |
| NRE081 | Pure | `test_nre081_import_guards_enforce_independence[app.modules.nutrition.resolution_estimator]`<br>`test_nre081_import_guards_enforce_independence[app.modules.nutrition.synthesis]`<br>`test_nre081_import_guards_enforce_independence[app.modules.recipes.public]`<br>`test_nre081_import_guards_enforce_independence[app.modules.planning.grounding]`<br>`test_nre081_import_guards_enforce_independence[sqlalchemy]`<br>`test_nre081_import_guards_enforce_independence[os]` |
| NRE082 | Pure | `test_nre082_independent_checker_catches_delta_and_serving_scale_corruption` |
| NRE083 | Pure | `test_nre083_rehashed_calendar_mutation_fails_reconstruction` |
| NRE084 | Pure | `test_nre084_consistent_unavailable_never_numerically_admitted` |
| NRE085 | Pure | `test_nre085_internally_reauthored_package_does_not_prove_database_origin` |
| NRE086 | Pure | `test_nre086_canonical_handoff_not_castable_to_fixture_v1` |
| NRE087 | Pure | `test_nre087_frozen_producer_and_independent_v1_checker_still_accept_old_fixture` |
| NRE088 | Pure | `test_nre088_handoff_rechecks_retained_sources_not_caller_expected_step` |
| NRE089 | Pure | `test_nre089_planned_input_not_admitted_as_physiological_intake` |
| NRE090 | Pure | `test_nre090_resolution_soft_hard_and_solver_states_not_collapsed` |
| NRE091 | Pure | `test_nre091_package_size_and_data_confidence_are_not_resolution_operands` |
| NRE092 | Pure | `test_nre092_preferences_cannot_supply_or_weaken_root_truth[CostPreference]`<br>`test_nre092_preferences_cannot_supply_or_weaken_root_truth[BudgetPressure]`<br>`test_nre092_preferences_cannot_supply_or_weaken_root_truth[BudgetContract]`<br>`test_nre092_preferences_cannot_supply_or_weaken_root_truth[KitchenEffort]`<br>`test_nre092_preferences_cannot_supply_or_weaken_root_truth[TasteFit]` |
| NRE093 | Pure | `test_nre093_estimator_needs_no_completed_resolved_plan_policy` |
| NRE094 | Pure | `test_nre094_480_export_hashes_and_frozen_files_remain_identical` |
| NRE095 | Pure | `test_nre095_all_3912_baseline_test_identities_retained` |
| NRE096 | Pure | `test_nre096_no_new_persistence_or_activation_authority` |

The 23 additive definitions are:

```text
NreCaptureFrame
NreDelta
NreFixtureFact
NreIngredientContribution
NreOwnerAbsence
NrePeriodVectors
NreRational
NreReachableVector
NreRecipeSeal
NreRecipeSelection
NreReferenceSelection
NreResolutionGap
NreResourceProfile
NreServingDeclaration
NreSlot
NutritionResolutionCheckV1
NutritionResolutionEstimateV1
NutritionResolutionHandoffV2
NutritionResolutionScopeRequestV1
NutritionResolutionScopeV1
NutritionResolutionSourcesV1
ResolutionConfigurationV1
ResolutionMeasurementV1
```

## 9. Review gate and remaining blockers

This bounded implementation is a review candidate, not a self-approved freeze or completion of
full MTR-007. The remaining policy-integration v2 companion, reviewed measurement-basis authority,
production scientific/qualification content and MTR-008 policy compilation remain separate gates.
No downstream implementation is authorized by this evidence.

Nutrition Root and MTR-006 structural foundations remain FROZEN. Full MTR-006/007/008 remain
INCOMPLETE; parent issues stay OPEN. MTR-040 COMPLETE; MTR-039 OPEN; full MTR-041/046 PARTIAL;
MTR-020B/021/024 BLOCKED. Execution NOT STARTED; PRECOMMIT FAIL-CLOSED. Planner/activation remain
False. **PRODUCTION NUTRITION/CLINICAL CONTENT GATE — CLOSED.**
