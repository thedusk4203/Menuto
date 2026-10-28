# Candidate-bound Shared-member Exact-target TasteFit Compatibility & Aggregation Foundation — implementation evidence

Status: **IMPLEMENTATION READY FOR REVIEW / FREEZE CANDIDATE — NOT FROZEN**.
Final full CI must succeed on the documentation-inclusive review head; its exact SHA/run receipt
is recorded in the implementation PR body after completion. No self-merge or self-freeze.

## Authorized entry gate

- Approved [design PR #119](https://github.com/thedusk4203/Menuto/pull/119), exact head
  `8295f19a705cc085471a9dab7948072cc3054534`, base
  `7dcb0b1b9b7f35b80b3f86c24064c920f1d8a2ec`.
- [Architecture approval6472672563](https://github.com/thedusk4203/Menuto/pull/119#issuecomment-6472672563).
- Actual design merge / verified main: `f16508270ac159d07cc01757b3459aa4e4764f62`.
  Merged tree `242760c394e19f164e612f9dc6c557923be231a1` equals the approved head's tree;
  one commit, six Markdown files, no runtime drift.
- Exact post-merge push [CI40763687731](https://github.com/thedusk4203/Menuto/actions/runs/40763687731)
  **SUCCESS**, Python/web and all required steps SUCCESS: **3,396 passed /0 skips**;
  SCRAM/TLS16/16; benchmark22/22; client10/10;384 exports;0015 /85;no0016.
- Implementation began only after that successful push gate and separate explicit user authorization.
  Fresh branch: `codex/shared-member-target-tastefit-implementation`; base is the actual merge above.
  Initial code head: `f0d5193295048a15f50ddce09065f34374041182`.
  Corrected implementation code head: `2b343fa47ed5de059fa4919d4326ac8863153a78`.
  The evidence-inclusive review head and its full CI receipt are recorded separately in PR metadata;
  this avoids treating an earlier code head or a self-referential document hash as final-head proof.

## Implemented boundary

The [approved design](CANDIDATE_SHARED_MEMBER_EXACT_TARGET_TASTEFIT_AGGREGATION_DESIGN.md) remains
unchanged. Exactly four new Planning Modules expose capture, derive and semantic validation through
[the three-operation Interface](../../apps/backend/app/modules/planning/shared_target_tastefit_public.py).
The four new Planning Modules import no Preferences implementation/companion, and add no endpoint,
source authority or public reducer. PostgreSQL test setup/revoke uses existing owner APIs only in tests.

One canonical candidate × one exact typed target × the complete canonical participant set.
Full child replay, exact target/candidate/cohort and owner-cut coherence, full policy admission and
an exact finite authored bridge precede every new multiplication/sum/denominator.
The only operator is EXACT_POSITIVE_WEIGHTED_MEAN using strictly positive authored rational weights.
Missing or incompatible numeric coverage withholds value, totals and every new arithmetic contribution.
Direct dislike is retained independently, without veto, exclusion or implicit additional weight.

The new coordinate binds exact candidate, target, household, complete participant context, full
aggregation policy and retained cohort. Same rational alone never licenses comparison/ranking.
Complete sources, unavailable/unselected lineage, histories, frames/clocks, bridges, weights,
diagnostics and traces remain fingerprinted; offline replay is consistency, not canonical-origin,
current-permission or common-MVCC certification.

## Acceptance and regression verification

All **SMTF01–SMTF120** are indexed to concrete test nodes in the
[test-only acceptance index](../../apps/backend/tests/fixtures/shared_target_tastefit_acceptance.json).
**44 real PostgreSQL cases cover all36 required PG obligations.** The complete local run executed
all44 successfully through actual canonical capture/protected source paths; fault-injection wrappers
still call the real child capture, not a mocked success or collected-only substitute.

| Verification | Receipt |
| --- | --- |
| First complete local run, initial code head | **3,632 executed:3,629 passed /3 failed /0 skips**,2531.75s. All236 additive cases passed, including44 PG. The three failures were old export-total assertions still expecting384; no behavioral failure was observed. |
| Corrected code-head focused regression | **201 passed /0 skips**,128.43s:160 new pure tests +38 new architecture tests +the3 repaired legacy export assertions. Includes6 further tests for exact fractional weights and carry/allocation limits. |
| Final complete test inventory | **3,638 =3,396 retained baseline +242 additive**, comprising160 pure +38 architecture +44 PG. Collection is not execution; full exact-head GitHub CI must verify this complete inventory before the completion receipt. |
| SCRAM/TLS smoke | **16/16 passed** using actual PostgreSQL authentication and verified TLS. An expired disposable-local certificate was renewed only for this run; original SSL configuration was restored and the task-started server stopped afterward. No deployment/repository TLS change. |
| Benchmark /synthetic fixtures | **22/22 scenarios**,22 fixture snapshots verified |
| Client /typecheck /web | **10/10 tests**, contracts:check, TypeScript checks and production web build passed |
| Repository guards | Ruff,30-invariant/11-ADR/50-task baseline,16-context imports, OpenAPI/domain exports passed |
| Compatibility | All384 old definitions unchanged;120 baseline module/migration files byte-exact;3,396 baseline identities retained; no0016 |

The final exact-head CI receipt in the PR body supplies the complete post-correction execution
result, including Python/web jobs, exact head SHA and run ID. An initial local run or test collection
is not used as a substitute for that gate. The PR remains OPEN after CI; only a later user review
may approve merge/freeze.

## Compatibility, persistence and authority

**403 exports =384 unchanged +19 additive**. All384 old definitions are hash-checked;
all120 frozen runtime/migration file bytes and all3,396 baseline test identities are pinned.
Exactly four legacy export-total/set assertions are mechanically extended for the19 additions;
all existing behavioral expectations, old schema hashes, frozen bytes and test identities remain checked.
The existing Preferences companion allowlist is unchanged; new exact Module guards are additive.

**ZERO NEW PERSISTENCE**. Schema remains **0015 /85**; no0016, table, cache, materialized aggregate,
member matrix, policy registry, source/default coefficients, grants or production seeds/rows.
Numeric fixtures are explicit disposable test policies, never runtime production authority.
Policy authority remains EXPLICIT_INTERPRETATION_INPUT_ONLY, with complete bodies and independent pins;
no global/current/default/environment/production selection or publication exists.

Frozen child TasteFit,040A/B/C, prior/shrinkage, hierarchy SOURCE,041A–F,046A and candidate projection
remain unchanged. MTR-040 COMPLETE /issue41 CLOSED—COMPLETED;039 OPEN;full041/046 PARTIAL;
024/020B/021 BLOCKED;Execution NOT STARTED;PRECOMMIT FAIL-CLOSED;
planner_ready=False;activation_ready=False. No new MTR suffix or downstream work.
The implementation PR must remain OPEN for review. No self-merge or self-freeze.

## Module and API inventory

| Module | Responsibility |
| --- | --- |
| [shared_target_tastefit_contracts.py](../../apps/backend/app/modules/planning/shared_target_tastefit_contracts.py) | Required authored policy/pins, finite bridge/weight contracts, complete retained sources and inseparable result coordinates |
| [shared_target_tastefit_capture.py](../../apps/backend/app/modules/planning/shared_target_tastefit_capture.py) | Fresh authenticated preflight and full-cohort capture on the caller's same clean read-only RR/SERIALIZABLE Session per owner; all-or-fail |
| [shared_target_tastefit.py](../../apps/backend/app/modules/planning/shared_target_tastefit.py) | Public frozen-child semantic replay, exact typed cohort/owner-cut agreement, compatibility/coverage and private exact weighted reduction |
| [shared_target_tastefit_public.py](../../apps/backend/app/modules/planning/shared_target_tastefit_public.py) | Only capture_shared_member_target_tastefit_sources /derive_shared_member_target_tastefit /validate_shared_member_target_tastefit; lazy capture import |

No public bare-rational reducer. New pure/transport/capture/public import guards apply only to these
new Modules; old TASTEFIT_COMPANIONS and existing cross-context grants remain unchanged.
Old child results retain aggregate/shared_member_aggregation/candidate_comparison=NOT_PERFORMED.
The new enclosing result does not change any frozen child field or algorithm.

The capture request rejects missing/duplicate/extra/nonparticipant member inputs or weights, empty
participants and foreign household identity. Participant authority is the freshly grounded canonical
MealParticipants context, with actual per-member read access still required. TRACKED is nutrition
context, not preference ownership or taste priority. All five existing preference kinds work;
MAIN_PROTEIN factual support maps to PROTEIN, never a sixth preference kind.

Compatibility requires the full pinned child policy, complete mapping row/source descriptor,
source mode, semantic state and direct signal, plus an explicit authored common-unit amount.
Same policy label/body or same rational alone is insufficient. Bridges preserve child fit sign/zero,
not raw-affinity sign. Weight/amount integers are strict and exact. The sum guard materializes a carry threshold only
when actual operand bits can reach the authored limit; a huge budget with tiny operands stays cheap.
Exact fractional weights3/7 and2/5 retain weight_total29/35, not an implicit unit denominator.
Products/totals carry unbounded
signed rational trace units; the final shared fit stays in[-1,1]. No floats, clipping or hidden weights.

Only projection-source capture_started_at /capture_completed_at and feature_input.captured_at are
excluded for the typed cross-child integrity comparison, with the two derived projection hashes.
All original clocks/hashes remain in full source/cohort identity. Authored/effective/review times,
full classification sources, histories, frontiers and target resolution remain binding. A correction
cut or overlapping protected reader/journal conflict is SOURCE_CUT_INCOHERENT, never latest-selected.
Typed immutable fact identity is global across the cohort; member ledgers remain keyed by member.

## SMTF acceptance index — concrete test inventory

Each method below has an executed local receipt (the initial full run or post-correction focused
run). Final exact-head full CI re-executes the complete inventory; its receipt is in PR metadata.
Full parameterized node IDs are in the linked JSON index, validated against retained/current nodes.
PG11 expands to3 cases,PG22 to2,PG29 to3,PG36 to4: **44 actual PG cases /36 obligations**.
P/B includes160 pure public replay/validation cases and38 architecture negatives/compatibility guards.

| Case | Required layer | Concrete test method(s) |
| --- | --- | --- |
| SMTF01 | PG | [test_smtf01_actual_ingredient_cohort_distinct_member_declarations](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF02 | PG | [test_smtf02_actual_recipe_version_source_and_path](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF03 | PG | [test_smtf03_actual_reviewed_main_protein_support](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF04 | PG | [test_smtf04_actual_method_version_wide_child_and_outer_path](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF05 | PG | [test_smtf05_actual_flavor_exact_path_finite_coverage](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF06 | PG | [test_smtf06_tracked_and_multiple_shared_never_copy_preferences](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF07 | PG | [test_smtf07_single_actual_member_not_scope_copy](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF08 | PG | [test_smtf08_denied_actor_before_preference_reads](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF09 | PG | [test_smtf09_foreign_member_not_local_participant](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF10 | PG | [test_smtf10_nonexistent_member_cannot_be_empty_preference](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF11 | PG | [test_smtf11_invalid_caller_transaction_rejected_unchanged](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF12 | PG | [test_smtf12_actual_serializable_read_only_capture](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF13 | PG | [test_smtf13_primary_rr_cut_during_actual_concurrent_correction](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF14 | PG | [test_smtf14_actual_wrong_database_oid_not_same_label](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF15 | PG | [test_smtf15_actual_denied_prior_reader_aborts](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF16 | PG | [test_smtf16_prior_cannot_supply_hierarchy_capability](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF17 | PG | [test_smtf17_actual_declared_and_prior_only_modes](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF18 | PG | [test_smtf18_actual_one_hop_mapped_explicit_no_strength_propagation](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF19 | PG | [test_smtf19_full_protected_journal_retains_hidden_publications](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF20 | PG | [test_smtf20_actual_pre_post_review_cuts_cannot_splice](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF21 | PG | [test_smtf21_actual_later_member_connection_failure_aborts_whole_capture](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF22 | PG | [test_smtf22_actual_required_protected_db_failure_after_partial_read](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF23 | PG | [test_smtf23_correction_fresh_trace_old_cohort_historical_replay](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF24 | PG | [test_smtf24_current_retraction_withholds_no_resurrection](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF25 | PG | [test_smtf25_actual_unmapped_dislike_remains_visible](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF26 | PG | [test_smtf26_real_neutral_available_zero](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF27 | PG | [test_smtf27_undeclared_diner_not_omitted_or_zero](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF28 | PG | [test_smtf28_actual_known_absence_and_nonexistent_target](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF29 | PG | [test_smtf29_actual_finite_feature_missingness_not_fit](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF30 | PG | [test_smtf30_different_actual_policies_require_own_bridges](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF31 | PG | [test_smtf31_actual_unadmitted_policy_no_arithmetic](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF32 | PG | [test_smtf32_full_retry_recaptures_every_actual_member](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF33 | PG | [test_smtf33_actual_sql_read_only_no_transactions_connections_or_row_drift](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF34 | PG | [test_smtf34_real_schema_0015_85_zero_persistence](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF35 | PG | [test_smtf35_independent_real_frames_and_replay_after_revoke](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF36 | PG | [test_smtf36_actual_metadata_not_extra_member_weight](../../apps/backend/tests/test_postgres_shared_target_tastefit.py) |
| SMTF37 | P/B | [test_smtf37_full_sources_and_numeric_coverage_separate](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF38 | P/B | [test_smtf38_duplicate_input_rejected_before_dictionary_collapse](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF39 | P/B | [test_smtf39_missing_required_input_or_child](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF40 | P/B | [test_smtf40_extra_favorable_child_rejects](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF41 | P/B | [test_smtf41_member_slot_request_subject_binding](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF42 | P/B | [test_smtf42_empty_participants_never_zero](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF43 | P/B | [test_smtf43_tracked_only_substitution_rejects](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF44 | P/B | [test_smtf44_context_tamper_not_coherent_candidate](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF45 | P/B | [test_smtf45_other_candidate_same_amount_rejects](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF46 | P/B | [test_smtf46_version_source_path_binding_before_arithmetic](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF47 | P/B | [test_smtf47_exact_target_identity_not_uuid_only](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF48 | P/B | [test_smtf48_five_independent_kinds](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf48_no_sixth_main_protein_kind](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF49 | P/B | [test_smtf49_diagnostic_probe_cannot_mint_presence](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF50 | P/B | [test_smtf50_child_dimensions_must_equal_root_construction](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF51 | P/B | [test_smtf51_child_configuration_revalidated](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF52 | P/B | [test_smtf52_no_missing_policy_fallback](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF53 | P/B | [test_smtf53_exact_root_policy_pins](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF54 | P/B | [test_smtf54_changed_body_requires_independent_pin](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF55 | P/B | [test_smtf55_new_coherent_authored_policy_conditional_only](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF56 | P/B | [test_smtf56_unknown_contract_versions](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF57 | P/B | [test_smtf57_valid_unadmitted_policy_is_not_forgery](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF58 | P/B | [test_smtf58_equal_numeric_amount_different_policy_not_compatible](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf58_same_policy_id_version_different_full_body_not_compatible](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF59 | P/B | [test_smtf59_same_child_policy_body_still_needs_bridge](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF60 | P/B | [test_smtf60_smtf61_smtf62_smtf63_complete_mapping_identity](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF61 | P/B | [test_smtf60_smtf61_smtf62_smtf63_complete_mapping_identity](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF62 | P/B | [test_smtf60_smtf61_smtf62_smtf63_complete_mapping_identity](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF63 | P/B | [test_smtf60_smtf61_smtf62_smtf63_complete_mapping_identity](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF64 | P/B | [test_smtf64_direct_signal_is_exact_bridge_key](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF65 | P/B | [test_smtf65_detached_mapping_rejected](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF66 | P/B | [test_smtf66_duplicate_or_contradictory_admission](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF67 | P/B | [test_smtf67_equivalent_fraction_duplicate_key](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF68 | P/B | [test_smtf68_no_first_or_last_rule_wins](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF69 | P/B | [test_smtf69_policy_mapping_kind_exact](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF70 | P/B | [test_smtf70_smtf71_smtf72_fit_sign_and_zero_preserved](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF71 | P/B | [test_smtf70_smtf71_smtf72_fit_sign_and_zero_preserved](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF72 | P/B | [test_smtf70_smtf71_smtf72_fit_sign_and_zero_preserved](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF73 | P/B | [test_smtf73_no_interpolation_identity_or_zero_fallback](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF74 | P/B | [test_smtf74_independent_exact_rational_reference](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf74_positive_fractional_weights_keep_exact_nonunit_total](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf74_weighted_products_unbounded_but_final_fit_bounded](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF75 | P/B | [test_smtf75_single_member_has_new_descriptor_and_bridge](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF76 | P/B | [test_smtf76_missing_weight_rejected_even_unavailable](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF77 | P/B | [test_smtf77_duplicate_extra_weights_reject](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF78 | P/B | [test_smtf78_amounts_strict_and_bounded](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf78_strict_authored_rationals](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF79 | P/B | [test_smtf36_actual_metadata_not_extra_member_weight](../../apps/backend/tests/test_postgres_shared_target_tastefit.py)<br>[test_smtf79_smtf80_portions_and_roles_not_weights](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF80 | P/B | [test_smtf36_actual_metadata_not_extra_member_weight](../../apps/backend/tests/test_postgres_shared_target_tastefit.py)<br>[test_smtf79_smtf80_portions_and_roles_not_weights](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF81 | P/B | [test_smtf36_actual_metadata_not_extra_member_weight](../../apps/backend/tests/test_postgres_shared_target_tastefit.py)<br>[test_smtf81_ordinal_strength_retained_not_multiplier](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF82 | P/B | [test_smtf36_actual_metadata_not_extra_member_weight](../../apps/backend/tests/test_postgres_shared_target_tastefit.py)<br>[test_smtf82_smtf105_history_changes_identity_not_member_influence](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF83 | P/B | [test_smtf83_smtf107_new_set_order_normalizes_frozen_order_preserved](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF84 | P/B | [test_smtf84_rescaled_weights_same_amount_different_scope](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF85 | P/B | [test_smtf85_cancellation_is_not_neutral_declaration](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF86 | P/B | [test_smtf86_available_zero_unavailable_none_wire_distinct](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF87 | P/B | [test_smtf87_all_zero_keeps_every_weight](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF88 | P/B | [test_smtf88_unavailable_member_no_new_subtotal](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF89 | P/B | [test_smtf89_smtf95_retraction_suppresses_not_neutral](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF90 | P/B | [test_smtf90_child_unmapped_is_distinct_from_bridge_unmapped](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF91 | P/B | [test_smtf91_all_required_ids_reasons_retained](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF92 | P/B | [test_smtf92_dislike_survives_every_aggregate_outcome](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF93 | P/B | [test_smtf93_smtf94_unfavorable_prior_inheritance_not_direct_dislike](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF94 | P/B | [test_smtf93_smtf94_unfavorable_prior_inheritance_not_direct_dislike](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF95 | P/B | [test_smtf89_smtf95_retraction_suppresses_not_neutral](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF96 | P/B | [test_smtf96_grounding_safety_cannot_be_favorable_fit_rescue](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF97 | P/B | [test_smtf97_only_current_direct_heads_retained](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF98 | P/B | [test_smtf98_full_unselected_child_replay_not_only_outer_row](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF99 | P/B | [test_smtf99_construct_copy_are_untrusted](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF100 | P/B | [test_smtf100_candidate_and_member_frame_require_same_owner_session](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf100_rehashed_fiction_no_authority](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF101 | P/B | [test_smtf19_full_protected_journal_retains_hidden_publications](../../apps/backend/tests/test_postgres_shared_target_tastefit.py)<br>[test_smtf101_overlapping_owner_reader_conflict_rejects](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF102 | P/B | [test_smtf102_global_typed_identity_registry_ignores_mutable_ingredient_labels](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf102_individually_valid_children_conflicting_unselected_typed_term](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF103 | P/B | [test_smtf103_review_source_clock_cannot_be_normalized_away](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf103_smtf104_exact_read_clock_allowlist_changes_full_identity](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF104 | P/B | [test_smtf103_smtf104_exact_read_clock_allowlist_changes_full_identity](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF105 | P/B | [test_smtf19_full_protected_journal_retains_hidden_publications](../../apps/backend/tests/test_postgres_shared_target_tastefit.py)<br>[test_smtf82_smtf105_history_changes_identity_not_member_influence](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF106 | P/B | [test_smtf106_unavailable_states_and_policy_full_identity](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF107 | P/B | [test_smtf83_smtf107_new_set_order_normalizes_frozen_order_preserved](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF108 | P/B | [test_smtf108_complete_semantic_validation_returns_fresh](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF109 | P/B | [test_smtf109_actual_public_interface_zero_io](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf109_smtf110_pure_core_no_io_learning_or_policy_environment](../../apps/backend/tests/test_shared_target_tastefit_architecture.py) |
| SMTF110 | P/B | [test_smtf110_no_environment_policy_or_mutable_cache](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf109_smtf110_pure_core_no_io_learning_or_policy_environment](../../apps/backend/tests/test_shared_target_tastefit_architecture.py)<br>[test_smtf110_policy_fields_required_no_numeric_defaults](../../apps/backend/tests/test_shared_target_tastefit_architecture.py) |
| SMTF111 | P/B | [test_smtf111_mismatch_before_new_reduction](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF112 | P/B | [test_smtf112_complete_authored_resource_budgets](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF113 | P/B | [test_smtf113_exact_carry_budget_and_cancellation](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf113_huge_authored_bit_budget_tiny_operands_no_huge_allocation](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf113_integer_and_intermediate_budget_no_truncation](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF114 | P/B | [test_smtf114_stripped_or_forged_descriptors_fail](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF115 | P/B | [test_smtf115_no_cross_target_kind_or_whole_candidate_scalar](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF116 | P/B | [test_smtf116_equality_requires_complete_scope](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF117 | P/B | [test_smtf117_no_mtr039_behavioral_operands](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF118 | P/B | [test_smtf118_history_and_novelty_never_operands](../../apps/backend/tests/test_shared_target_tastefit.py) |
| SMTF119 | P/B | [test_smtf119_non_authority_literals_cannot_promote](../../apps/backend/tests/test_shared_target_tastefit.py)<br>[test_smtf119_no_capture_access_from_learning_validation](../../apps/backend/tests/test_shared_target_tastefit_architecture.py)<br>[test_smtf119_small_three_operation_public_surface_and_lazy_capture](../../apps/backend/tests/test_shared_target_tastefit_architecture.py) |
| SMTF120 | P/B | [test_smtf120_all3396_baseline_test_identities_retained](../../apps/backend/tests/test_shared_target_tastefit_architecture.py)<br>[test_smtf120_all384_definitions_unchanged_exact_new_exports](../../apps/backend/tests/test_shared_target_tastefit_architecture.py)<br>[test_smtf120_all_frozen_runtime_and_migrations_byte_exact](../../apps/backend/tests/test_shared_target_tastefit_architecture.py)<br>[test_smtf120_immutable_transport_no_runtime_facades](../../apps/backend/tests/test_shared_target_tastefit_architecture.py)<br>[test_smtf120_no_new_preferences_companion_or_private_access](../../apps/backend/tests/test_shared_target_tastefit_architecture.py) |

## Exact changed-file inventory

Production additions are exactly the four Planning Modules listed above. Other changes:

- Test helpers: `shared_target_tastefit_fixtures.py`, `shared_target_tastefit_postgres_fixtures.py`.
- New tests: `test_shared_target_tastefit.py`, `test_postgres_shared_target_tastefit.py`,
  `test_shared_target_tastefit_architecture.py`.
- Test-only fixtures: `shared_target_tastefit_acceptance.json`, `shared_target_tastefit_baseline_tests.json`,
  `shared_target_tastefit_compatibility.json` under `apps/backend/tests/fixtures/`.
- Mechanical namespace assertions only: `test_tastefit_architecture.py`,
  `test_candidate_feature_projection.py`, `test_hierarchical_affinity_compatibility.py`,
  `test_hierarchy_compatibility.py`.
- Additive registration/guards: `tools/export_domain_contracts.py`, `tools/check_import_boundaries.py`.
- Additive draft export: `packages/contracts/domain.schema.json`,19 additions with384 old bodies pinned.
- Evidence and the exact shared-target sections in `BACKLOG.md`, `FOUNDATION_STATUS.md`,
  `IMPLEMENTATION_BLUEPRINT.md`, `IMPLEMENTATION_BLUEPRINT_M0_M1.md`: five documentation files total.

**24 files total**; no other runtime, frozen contract, migration, production data or tooling behavior
is modified. Existing graph-output workspace changes are excluded from this PR. All other content
in the four tracking documents, including the50-work-item backlog table, remains byte-preserved.

## Final gate

CANDIDATE-BOUND SHARED-MEMBER EXACT-TARGET TASTEFIT COMPATIBILITY & AGGREGATION FOUNDATION

**IMPLEMENTATION READY FOR REVIEW / FREEZE CANDIDATE**

Not frozen. No automatic merge, new MTR suffix, parent closure or downstream implementation.
