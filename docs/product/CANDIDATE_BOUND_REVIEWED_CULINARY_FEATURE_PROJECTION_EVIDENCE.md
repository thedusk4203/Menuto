# Candidate-bound Reviewed Culinary Feature Projection — Implementation Evidence

Status: **IMPLEMENTATION READY FOR REVIEW / FREEZE CANDIDATE**.
This is an implementation delivery receipt, not a freeze or parent completion declaration.

## Approved design and exact entry gate

- Design: [PR #111](https://github.com/thedusk4203/Menuto/pull/111), approved exact head
  `04dbbb012041be80fc86914b582777812ed32e59`, base `623218e2713faf950dd01325436c9a6e3969f638`.
- Formal approval: [architecture receipt 6441888047](https://github.com/thedusk4203/Menuto/pull/111#issuecomment-6441888047).
- Actual design merge / implementation branch base: `3efcd8c9594cbc0ae154d5bcac4e6315bf09d8f8`.
  Merge parents are the reviewed base and head; merged tree equals the approved head; exactly
  six Markdown files, with no runtime/contracts/tests/tools/migrations/data drift.
- Exact design post-merge push [CI 40507097863](https://github.com/thedusk4203/Menuto/actions/runs/40507097863)
  SUCCESS on that SHA; python/web SUCCESS; 2,978 tests; SCRAM/TLS 16/16; benchmark 22/22;
  client 10/10; exports 358; schema 0015 / 85.
- The user separately authorized implementation only after this gate passed. No new MTR suffix
  is assigned. [Approved design text](CANDIDATE_BOUND_REVIEWED_CULINARY_FEATURE_PROJECTION_DESIGN.md)
  remains unchanged; its design-stage non-authorization statements are historical, superseded
  only for this bounded implementation by the separate authorization and verified entry gate.

## Delivered interface and authority

Four additive shapes in [Planning contracts](../../apps/backend/app/modules/planning/contracts.py):
`CandidateFeatureProjectionRequest`, `CandidateFeatureProjectionSourceSnapshot`,
`CandidateFeatureBinding`, `CandidateFeatureProjectionDraft`, with the approved v1 identifiers.
Strict extra-field rejection remains inherited from Contract. Structural parsing is not semantic
validation or an assertion of canonical database origin.

[Canonical capture](../../apps/backend/app/modules/planning/candidate_feature_capture.py) uses
existing Household membership checks and owner reads in one clean read-only RR/SERIALIZABLE
transaction. It reconstructs frozen 019C grounding, requires the exact expected fingerprint,
captures complete frozen 046A source histories/manifests/frontiers and actual capture times.
METHOD-only never fabricates a path-sensitive child or reads a Catalog association frontier.

[Pure projection and semantic validation](../../apps/backend/app/modules/planning/candidate_feature_projection.py)
re-run frozen 019C and 046A from primitive sources, compare complete grounding and warnings,
derive exact RecipeVersion/path binding and reject incompatible cuts/cached outputs. Result
validation returns a freshly recomputed result. Full-source identity retains request/triggers,
grounding issues, every source history, coverage/diagnostics, frontiers and independent clocks.
Frozen child encodings and classification rules remain unchanged.

The three additive [Planning public operations](../../apps/backend/app/modules/planning/public.py)
are `capture_candidate_feature_projection_sources`, `project_candidate_features`,
`validate_candidate_feature_projection`. There is no new HTTP endpoint. Readiness literals remain
`planner_ready=False`, `activation_ready=False`. A frozen child's shortlist-input flag is not
promoted into planner authority. Offline self-consistency never proves database origin or a
shared real MVCC transaction; canonical ingress accepts selectors/request only.

## Validation receipt

| Check | Result |
| --- | --- |
| Full pytest | **3104 collected** = retained baseline **2,978** + **126 additive**; final execution result and exact-head CI receipt are maintained in the implementation PR |
| New pure/contract/boundary tests | **95 passed** |
| New real PostgreSQL capture tests | **31 passed** |
| SCRAM/TLS smoke | **16/16 passed** on disposable local PostgreSQL 18.4 with TLS enabled |
| Benchmark | **22/22 passed** |
| Client | **10/10 passed**; contracts/typecheck/web build passed |
| Architecture / imports / lint | Passed; new pure-core allowlist added without relaxing existing rules |
| OpenAPI / domain exports / fixtures | Matched; 22 synthetic fixtures verified; no new HTTP surface |
| Domain exports | **358 + 4 = 362**; exactly the four approved new types; every old definition hash retained |
| Persistence / schema | **ZERO NEW PERSISTENCE**, `0015 / 85` domain tables, no `0016`; real PG test observes owner row counts unchanged across capture |

The passed checks above are local checks on the implementation worktree. Full-suite execution
and its exact final head/GitHub Actions run are recorded in the implementation PR after commit.
The collected count is not a claim that collection proves test success. This receipt neither cites
a synthetic head nor treats a pre-commit check as exact-head CI. Green exact-head CI is required
before delivery as a review candidate; merge/freeze still require separate review.

## Deliberate compatibility synchronization

The export snapshot and export registry add exactly four types. Two existing compatibility tests
mechanically update the total export count from 358 to 362. Their old definition hashes remain
unchanged. The hierarchy compatibility fixture itself is untouched.

Planning contracts/public were previously pinned as complete files. Both additions preserve the
entire old file byte-for-byte as a prefix: **38,595** bytes for contracts, **15,904** for public.
The existing 123-file retention check now verifies those exact old hashes over the approved old
prefixes for these two explicitly named additive surfaces; all other frozen files remain full-file
checks. A new [compatibility fixture](../../apps/backend/tests/fixtures/candidate_feature_projection_compatibility.json)
pins all 358 old definitions, the two exact prefix lengths/hashes, frozen grounding/046A owner files
and all migrations 0001–0015. A new
[baseline identity fixture](../../apps/backend/tests/fixtures/candidate_feature_projection_baseline_tests.json)
retains all 2,978 previous test identities. No old test ID or assertion about frozen business
semantics was removed. This is the deliberate additive compatibility change requiring review.

Frozen 046A itself normalizes review revision order; CFP54 verifies that existing rule rather than
introducing a generic new sorter. Frozen Decimal and child fingerprint rules remain authoritative.
No architecture contradiction or classification redesign was required.

## CFP01–CFP60 test mapping

U points to pure/contract/boundary tests; PG points to real PostgreSQL tests. Each ID has its own
named acceptance test. Every PG obligation in the approved matrix has a corresponding PG test;
parameterized variants are additional checks, not replacements for an ID. PostgreSQL cases use
actual owner publication/capture, including concurrent publication during an existing reader
snapshot, support replacement/retraction history, source failure and transaction/access rejection.

| Case | Pure / contract / boundary | Real PostgreSQL |
| --- | --- | --- |
| CFP01 | [test_cfp01_three_dimensions_for_one_canonical_candidate](../../apps/backend/tests/test_candidate_feature_projection.py#L72) | [test_cfp01_real_candidate_three_owner_dimensions_without_plan_or_batch](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L122) |
| CFP02 | [test_cfp02_method_child_has_no_path_but_outer_binding_does](../../apps/backend/tests/test_candidate_feature_projection.py#L82) | [test_cfp02_real_method_capture_keeps_child_path_none_and_no_catalog_reads](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L135) |
| CFP03 | [test_cfp03_main_protein_retains_pinned_support_and_complete_history](../../apps/backend/tests/test_candidate_feature_projection.py#L90) | [test_cfp03_real_main_protein_support_is_pinned_to_owner_publication](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L152) |
| CFP04 | [test_cfp04_flavor_exact_path_uses_owner_discovery](../../apps/backend/tests/test_candidate_feature_projection.py#L105) | [test_cfp04_real_flavor_uses_exact_authored_path](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L161) |
| CFP05 | [test_cfp05_another_complete_recipe_version_is_not_a_fallback](../../apps/backend/tests/test_candidate_feature_projection.py#L112) | [test_cfp05_another_recipe_version_does_not_inherit_review_by_title](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L169) |
| CFP06 | [test_cfp06_alternate_authored_tier_does_not_match_first_tier_review](../../apps/backend/tests/test_candidate_feature_projection.py#L121) | [test_cfp06_real_alternate_tier_has_no_implicit_scope_fallback](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L177) |
| CFP07 | [test_cfp07_transformation_context_is_retained_and_recomputed](../../apps/backend/tests/test_candidate_feature_projection.py#L129) | [test_cfp07_real_transformation_context_is_bound_to_selected_ingredient](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L201) |
| CFP08 | [test_cfp08_forged_culinary_claims_are_rejected](../../apps/backend/tests/test_candidate_feature_projection.py#L141) | — |
| CFP09 | [test_cfp09_same_method_on_different_authored_paths_is_distinct_subject_identity](../../apps/backend/tests/test_candidate_feature_projection.py#L163) | — |
| CFP10 | [test_cfp10_unsupported_dimension_has_no_substitute](../../apps/backend/tests/test_candidate_feature_projection.py#L174) | — |
| CFP11 | [test_cfp11_invalid_request_shape_is_not_normalized_into_authority](../../apps/backend/tests/test_candidate_feature_projection.py#L189) | — |
| CFP12 | [test_cfp12_dimension_set_order_normalizes_deterministically](../../apps/backend/tests/test_candidate_feature_projection.py#L195) | — |
| CFP13 | [test_cfp13_cached_grounding_with_recomputed_hash_is_not_authority](../../apps/backend/tests/test_candidate_feature_projection.py#L207) | — |
| CFP14 | — | [test_cfp14_missing_canonical_recipe_cannot_be_overridden](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L210) |
| CFP15 | [test_cfp15_incomplete_primitive_grounding_is_unavailable_not_rejected](../../apps/backend/tests/test_candidate_feature_projection.py#L219) | [test_cfp15_missing_selected_nutrition_is_incomplete_not_empty_features](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L223) |
| CFP16 | [test_cfp16_rejected_primitive_grounding_preserves_rejection](../../apps/backend/tests/test_candidate_feature_projection.py#L232) | [test_cfp16_forged_culinary_quantity_is_rejected_against_real_owner_source](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L246) |
| CFP17 | — | [test_cfp17_expected_pin_prevents_silent_fresh_candidate_substitution](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L260) |
| CFP18 | [test_cfp18_grounding_warnings_are_retained_and_recomputed](../../apps/backend/tests/test_candidate_feature_projection.py#L245) | — |
| CFP19 | [test_cfp19_outer_request_must_equal_retained_child_request](../../apps/backend/tests/test_candidate_feature_projection.py#L261) | — |
| CFP20 | — | [test_cfp20_household_membership_is_required_for_canonical_read](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L266) |
| CFP21 | [test_cfp21_recipe_version_mismatch_is_explicit](../../apps/backend/tests/test_candidate_feature_projection.py#L268) | — |
| CFP22 | [test_cfp22_same_immutable_recipe_identity_with_different_payload_is_incoherent](../../apps/backend/tests/test_candidate_feature_projection.py#L274) | — |
| CFP23 | [test_cfp23_exact_selected_path_is_checked_before_discovery](../../apps/backend/tests/test_candidate_feature_projection.py#L283) | — |
| CFP24 | [test_cfp24_edited_result_binding_is_recomputed_even_when_rehashed](../../apps/backend/tests/test_candidate_feature_projection.py#L296) | — |
| CFP25 | [test_cfp25_conflicting_duplicate_term_payload_is_never_last_write_wins](../../apps/backend/tests/test_candidate_feature_projection.py#L307) | — |
| CFP26 | [test_cfp26_feature_dimensions_must_equal_requested_dimensions](../../apps/backend/tests/test_candidate_feature_projection.py#L315) | — |
| CFP27 | [test_cfp27_complete_required_manifests_cannot_be_forged](../../apps/backend/tests/test_candidate_feature_projection.py#L323) | — |
| CFP28 | [test_cfp28_support_must_bind_actual_ingredient_path_and_catalog_review](../../apps/backend/tests/test_candidate_feature_projection.py#L344) | [test_cfp28_owner_rejects_invalid_support_and_canonical_capture_remains_valid](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L271) |
| CFP29 | [test_cfp29_invalid_review_hash_and_overlapping_scope_are_rejected](../../apps/backend/tests/test_candidate_feature_projection.py#L362) | [test_cfp29_owner_overlap_guard_is_preserved_at_real_publication](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L287) |
| CFP30 | [test_cfp30_catalog_head_change_remains_stale_not_inferred_support](../../apps/backend/tests/test_candidate_feature_projection.py#L391) | [test_cfp30_catalog_correction_retains_history_and_stales_old_support](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L308) |
| CFP31 | [test_cfp31_missing_review_is_no_source_not_zero](../../apps/backend/tests/test_candidate_feature_projection.py#L401) | [test_cfp31_successful_empty_owner_read_is_explicit_no_source](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L324) |
| CFP32 | [test_cfp32_nonmatching_authored_scope_is_not_implicit_none](../../apps/backend/tests/test_candidate_feature_projection.py#L406) | — |
| CFP33 | [test_cfp33_complete_reviewed_none_is_finite_coverage](../../apps/backend/tests/test_candidate_feature_projection.py#L413) | [test_cfp33_complete_review_with_no_positive_is_finite_reviewed_none](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L330) |
| CFP34 | [test_cfp34_partial_review_without_positive_is_unresolved](../../apps/backend/tests/test_candidate_feature_projection.py#L420) | — |
| CFP35 | [test_cfp35_partial_review_with_positive_preserves_uncovered_unknowns](../../apps/backend/tests/test_candidate_feature_projection.py#L425) | — |
| CFP36 | [test_cfp36_retraction_is_not_reviewed_none](../../apps/backend/tests/test_candidate_feature_projection.py#L430) | [test_cfp36_real_retraction_preserves_history_and_missingness](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L338) |
| CFP37 | — | [test_cfp37_real_source_read_failure_aborts_all_dimensions](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L351) |
| CFP38 | — | [test_cfp38_invalid_capture_transaction_has_no_write_or_commit](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L371)<br>[test_cfp38_clean_serializable_readonly_capture_is_supported](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L400) |
| CFP39 | — | [test_cfp39_concurrent_publication_cannot_splice_live_heads_into_mvcc_cut](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L405) |
| CFP40 | [test_cfp40_independent_clocks_and_frontiers_keep_owner_meanings](../../apps/backend/tests/test_candidate_feature_projection.py#L437) | [test_cfp40_real_independent_clocks_and_counters_are_not_collapsed](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L434) |
| CFP41 | [test_cfp41_feature_review_after_grounding_as_of_may_participate](../../apps/backend/tests/test_candidate_feature_projection.py#L452) | [test_cfp41_review_published_after_grounding_as_of_remains_visible_at_capture](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L447) |
| CFP42 | [test_cfp42_offline_future_cut_is_not_a_current_or_future_origin_certificate](../../apps/backend/tests/test_candidate_feature_projection.py#L461) | [test_cfp42_canonical_ingress_preserves_inventory_future_cutoff_rejection](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L454) |
| CFP43 | [test_cfp43_incoherent_source_cut_is_explicit](../../apps/backend/tests/test_candidate_feature_projection.py#L476) | — |
| CFP44 | [test_cfp44_retained_serialized_cut_replays_without_live_refresh](../../apps/backend/tests/test_candidate_feature_projection.py#L498) | [test_cfp44_old_cut_remains_replayable_after_live_publication_changes](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L467) |
| CFP45 | [test_cfp45_self_consistency_does_not_prove_database_origin_or_common_mvcc](../../apps/backend/tests/test_candidate_feature_projection.py#L505) | — |
| CFP46 | [test_cfp46_cached_grounding_output_cannot_override_primitive_inputs](../../apps/backend/tests/test_candidate_feature_projection.py#L516) | — |
| CFP47 | [test_cfp47_edited_discovery_rehashed_output_still_fails](../../apps/backend/tests/test_candidate_feature_projection.py#L532) | — |
| CFP48 | [test_cfp48_missing_provenance_or_tampered_identity_is_not_accepted](../../apps/backend/tests/test_candidate_feature_projection.py#L541) | — |
| CFP49 | [test_cfp49_pydantic_shape_or_bypass_is_not_semantic_validation](../../apps/backend/tests/test_candidate_feature_projection.py#L563) | — |
| CFP50 | [test_cfp50_replay_and_validation_are_deterministic_under_io_and_clock_traps](../../apps/backend/tests/test_candidate_feature_projection.py#L579) | — |
| CFP51 | [test_cfp51_full_source_identity_changes_even_when_positives_do_not](../../apps/backend/tests/test_candidate_feature_projection.py#L609) | — |
| CFP52 | [test_cfp52_generation_trigger_changes_outer_identity_without_changing_culinary_hash](../../apps/backend/tests/test_candidate_feature_projection.py#L631) | — |
| CFP53 | [test_cfp53_new_envelope_timezones_have_one_utc_identity](../../apps/backend/tests/test_candidate_feature_projection.py#L640) | — |
| CFP54 | [test_cfp54_frozen_child_ordering_and_decimal_rules_are_not_overridden](../../apps/backend/tests/test_candidate_feature_projection.py#L654) | — |
| CFP55 | [test_cfp55_missingness_cannot_become_numeric_default_or_eligibility](../../apps/backend/tests/test_candidate_feature_projection.py#L673) | — |
| CFP56 | [test_cfp56_no_title_mass_or_missing_dimension_inference](../../apps/backend/tests/test_candidate_feature_projection.py#L679) | — |
| CFP57 | [test_cfp57_preference_strength_and_learning_dependencies_are_forbidden](../../apps/backend/tests/test_candidate_feature_projection.py#L692) | — |
| CFP58 | [test_cfp58_no_novelty_repeat_or_candidate_scoring_dependency](../../apps/backend/tests/test_candidate_feature_projection.py#L706) | — |
| CFP59 | [test_cfp59_authority_literals_cannot_be_promoted](../../apps/backend/tests/test_candidate_feature_projection.py#L712) | — |
| CFP60 | [test_cfp60_retained_baseline_contracts_files_and_no_new_persistence](../../apps/backend/tests/test_candidate_feature_projection.py#L719)<br>[test_cfp60_all2978_baseline_test_identities_are_retained](../../apps/backend/tests/test_candidate_feature_projection.py#L756) | [test_cfp60_capture_preserves_schema_owner_rows_and_migration_head](../../apps/backend/tests/test_postgres_candidate_feature_projection.py#L476) |

## Downstream stop boundary

MTR-040 remains COMPLETE, issue #41 CLOSED / COMPLETED; frozen 040A/B/C, prior compatibility,
hierarchy sources and 019B/C / 046A / proposal feature capture semantics remain unchanged.
MTR-039 remains OPEN; full 041 and 046 remain PARTIAL. MTR-024 / 020B / 021 stay BLOCKED.
Execution is NOT STARTED; PRECOMMIT is FAIL-CLOSED.

No member preference/EvidenceStrength, TasteFit join, SignalAttribution, novelty, RepeatPenalty,
utility, role score, ranking, hard feasibility, safety certification, planner activation, Execution
or PRECOMMIT is delivered or authorized here. No persistence, migration, cache, production rows,
coefficients/defaults, materialized member profile or durable publication authority is introduced.
The implementation PR must remain open for review. No implementation merge or self-freeze.

```text
IMPLEMENTATION READY FOR REVIEW / FREEZE CANDIDATE
```
