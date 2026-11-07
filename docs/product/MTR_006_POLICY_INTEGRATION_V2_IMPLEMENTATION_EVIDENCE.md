# MTR-006 Policy Integration v2 — Implementation Evidence

**STRUCTURAL / TEST_ONLY — IMPLEMENTATION REVIEW CANDIDATE. NOT MERGED / NOT FROZEN.**

Production Nutrition/clinical content gate **CLOSED**. This receipt records engineering
verification, not independent approval, scientific correctness or publication authority.

## 1. Approved identity and narrow exception

- Exact implementation base/main: `5b9441d1c10e5ad010a10f9e1af415c1ef50bd5a`.
- Corrected design tree: `c14d6983eba191c78e2b498a1e17a50391144b6b`.
- [Approved design PR #136](https://github.com/thedusk4203/Menuto/pull/136),
  [architecture PASS 6700956749](https://github.com/thedusk4203/Menuto/pull/136#issuecomment-6700956749).
- [Corrigendum PR #137](https://github.com/thedusk4203/Menuto/pull/137),
  [independent PASS 6703079507](https://github.com/thedusk4203/Menuto/pull/137#issuecomment-6703079507),
  [completion 6703597433](https://github.com/thedusk4203/Menuto/pull/137#issuecomment-6703597433).
- Baseline push [CI 42344993299 SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/42344993299)
  proves the baseline only. Implementation exact-head CI is separately pinned in the PR receipt.
- Frozen MBA implementation: `9d3b580ce2a2d111223b37814612a4072dbfe6a2`,
  tree `3a68035f9c33de152b3899a083d534a537c647e1`.
- Owner separately authorized bounded implementation resumption and two narrow exceptions
  covering seven historical export-count/name guards. No behavior assertion changed.
  Original fixture/hash baselines were not rewritten. The new guard reverses only the
  exact authorized metadata edits before comparing all 126 historical test-file hashes.

## 2. Ownership and module/API inventory

| Owner | Added module | Boundary |
|---|---|---|
| Nutrition | `policy_v2_contracts.py` | 13 immutable, required-field, extra-forbid TEST_ONLY carriers; no origin/admission proof |
| Nutrition | `policy_v2.py` | `derive_policy_v2`; original source pins, child replay and complete joint finite policy |
| Nutrition | `policy_v2_rules.py` | Separate FINITE_EXACT_V1 evaluator, mandatory coverage and temporal containment |
| Nutrition | `policy_v2_limits.py` | Shared structural accounting/exact arithmetic limits, not business derivation |
| Nutrition | `policy_v2_public.py` | Input/wrapping helpers are unverified; production admission always closed |
| Planning | `policy_v2_capture.py` | Existing authenticated owner capture, private one-shot lease, exact expected-use binding |
| Planning | `policy_v2_worker.py` | Fixed explicitly spawned derive/check stages receiving bounded bytes only |
| Validation | `nutrition_policy_v2.py` | Fresh independent Root/rule/NRE/MBA and complete expected-policy reconstruction |
| Validation | `nutrition_policy_v2_rules.py` | Separately implemented instruction/coverage/containment fold |

No frozen v1 policy producer/checker is used as a v2 business oracle. The producer performs
one frozen MBA replay, including its fresh NRE reconstruction. Validation performs one fresh
independent NRE check and one independent MBA reconstruction, then its own complete rule/
coverage/containment/joint reconstruction. Positive MBA uses its frozen public checker once;
negative/null payloads use the explicitly approved frozen Validation-owned reconstruction once.
Together with capture this retains the four-NRE-run composition cap. Nutrition does not
import Validation. Exact additive companion guards preserve all prior import allowlists.

Policy-owned REQUEST_EXPLICIT precision and its complete authenticated subject/membership
witness are pinned. Equal enum values with different version/evidence/actor are not equal
selections. No MTR-008 defaults, override precedence or resolver is implemented.

## 3. Capture, lease, workers and non-authority

One ordinary authenticated reader uses the unchanged frozen owner interfaces in the same
clean caller-owned read-only REPEATABLE READ or SERIALIZABLE transaction. Metadata is read
through existing permitted pg_catalog interfaces; no new protected function/right is added.
Private object identity pins Session, connection, actual transaction, database/login/role
OID/name, backend, snapshot, selector/precision and exact issued registry registration.

Session reservation transitions CAPTURING→READY→CONSUMING→CONSUMED or ABORTED. Concurrent
captures on one Session and concurrent/replayed consumes cannot mint another use. Transaction
close/reopen, context exit, registry advance/revoke, timeout, mismatched expected use and
faithful non-success release no numbers and burn the association. Lock order is lease mutex
then registry mutex; expensive pure checking runs without either mutex held.

The fixed spawned workers receive canonical bytes plus IPC only, with source credentials/
URLs scrubbed before interpreter startup. Startup/output count against the 15s stage and 90s
total deadline. Cancellation or timeout kills and joins the worker and discards partial
output. The existing source capture watchdog remains 60s; SQL cancellation leaves rollback
with the caller. This is not a hostile-Python-code sandbox or a production HTTP ingress gate.

All serialized results/checks/handoffs remain UNVERIFIED_TRANSPORT, NOT_PROVED_OFFLINE,
NOT_CLAIMED current authorization and NOT_CERTIFIED science. A matching hash, supplied
CONSISTENT report, copied object or JSON can never issue a capture lease. Cut-scoped use
does not claim instantaneous cross-session revocation or current authorization on replay.

## 4. Corrected PIV-R136-01 reconciliation

All eight PUBLISH/SUPERSEDE × REVIEW-grant/qualification expiry × without/with later
backdated renewal variants execute. Frozen child is UNAVAILABLE/SOURCE_UNQUALIFIED with
empty witnesses; frozen checker CONSISTENT. Parent is SOURCE_UNAVAILABLE/SOURCE_UNAUTHORIZED,
payload=null; independent v2 check CONSISTENT/NOT_ADMITTED. Later renewal cannot repair
publication-time authorization. Each variant also executes four fully rehashed child,
witness, parent and report forgery controls; all are independently INCONSISTENT/non-admitted.

Actual publisher-capability, malformed GRANT/QUALIFY and journal corruption controls retain
their frozen REJECTED pair and parent rejection. No blanket unavailable mapping is used.
A fresh frozen capture may reject an invalid artifact before issuing any lease; no partial
source result is manufactured. Real-PG faithful non-success and abort/replay cases prove
that an issued association cannot be reused to obtain positive numbers.

## 5. Exact finite semantics

Only PIV2_SAME_MEANING_EXACT_PERIOD_SUM_V1 is admitted. Original source meaning remains
PLANNED_INGREDIENT_INPUT_V1 / NRE_EXACT_PLANNED_INPUT/v1. No offered/consumed/physiological
conversion, clinical coefficient, default or package-size shortcut is introduced.

The retained horizon must cover every declared slot. Every original root and MAKE branch,
including unselected precision branches, is covered independently of COMFORT-only
RequirementSpec. Every assignment projects to the exact retained period witness for the
same configuration tuple. Equal-vector alternative tuples all survive. The canonical
representative is an evidence witness, not a plan/ranking. Marginals/max gaps are not proof.

H is the conjunction of GUIDELINE_HARD and active goal/daily/weekly protection. C adds the
selected soft COMFORT predicates. Empty H and H-present/C-empty produce distinct resolution
non-success without numerical payload. Contradictory protected intervals are POLICY_CONFLICT.
REFERENCE_CENTER/TARGET and weekly centering remain soft; missing opposite bounds stay
absent. Authored period endpoint projections never scale food vectors. Required DAY→WEEK
sums require explicit unit coefficients. Every FINITE_PERIOD_SUM sharing an original
root must have the same complete exact-rational coefficient vector, including roots
outside daily_root_keys. Equal non-unit vectors remain allowed for non-daily roots.
No missing period is manufactured or stitched.

Server-owned caps retain32MiB input,2MiB artifact,16MiB NRE sources,8MiB result,48MiB
handoff,256KiB check, depth32,1M nodes,100K string chars,256-bit rationals/1024-bit temporary
arithmetic,256 history events/operations,128 anchors,16384 assignments and65536 witnesses/
center deltas. Each new evaluator has2M charged work units, including reserved bounded
failure serialization. No overflow truncates history or releases a favorable prefix.

## 6. Executed PIV-D acceptance mapping

All 32 families executed in the corrected single186-case focused run (141 pure +45 real
PostgreSQL executions), including the nine PIV-R138-01 differential additions. Initial
head 4b148213898bd4bacdb7ecc442e91aa2fdaeb48d had177 focused/4360 complete executions;
those historical runs did not cover this finding. Corrected-head full regression and
exact-head CI must be pinned separately in the PR completion receipt. Counts below
overlap where a case checks two families; do not sum them. Exact IDs follow the matrix.

| Family | Verified controls | Executed cases | Test functions |
|---|---|---:|---|
| PIV-D01 | Complete DAY/WEEK composition, full anchors/periods and one-shot capture | 4 | `test_piv_d01_d07_missing_full_anchor_not_hidden_by_comfort_requirements`<br>`test_piv_d01_full_joint_policy` |
| PIV-D02 | Retained JSON/UUID/hash cannot establish privately captured origin | 4 | `test_piv_d02_serialized_origin_cannot_issue_lease` |
| PIV-D03 | Fresh NRE reconstruction rejects rehashed configuration/vector/measurement edits | 3 | `test_piv_d03_fully_rehashed_nre_forgery` |
| PIV-D04 | MBA assertion/qualification/reader forgery and actual REJECTED history remain rejected | 7 | `test_piv_d04_d24_actual_rejected_history_is_not_honest_unavailable`<br>`test_piv_d04_rehashed_mba_authority_forgery` |
| PIV-D05 | Whole-policy claim, trace, root, coverage, assignment and representative tamper | 6 | `test_piv_d05_whole_policy_rehashed_positive_forgery` |
| PIV-D06 | Faithful NRE/material/goal negatives remain nonnumeric; no goal defaults | 4 | `test_piv_d06_consistent_negative_no_numeric_use`<br>`test_piv_d06_d16_goal_missing_does_not_default_to_maintain`<br>`test_piv_d06_faithful_unavailable_nre_is_consistent_but_not_admitted` |
| PIV-D07 | Exact identity pins and complete original/unused-precision anchor coverage | 8 | `test_piv_d01_d07_missing_full_anchor_not_hidden_by_comfort_requirements`<br>`test_piv_d07_complete_identity_pins` |
| PIV-D08 | Original-source meaning absence, duplication and contradiction | 3 | `test_piv_d08_original_source_meaning_not_wrapper_authority` |
| PIV-D09 | No planned/offered/consumed/physiological identity bridge | 4 | `test_piv_d09_no_clinical_identity_bridge` |
| PIV-D10 | Exact subject/database identities; one-sided bounds; soft reference TARGET | 5 | `test_piv_d10_exact_subject_and_descriptor_identity`<br>`test_piv_d10_one_sided_roots_and_reference_target_are_not_invented_intervals` |
| PIV-D11 | Favorable recipe/reference/seal subsets cannot manufacture completeness | 3 | `test_piv_d11_favorable_only_source_is_not_complete` |
| PIV-D12 | Common correlated assignment; equal-vector configuration witnesses retained | 4 | `test_piv_d12_equal_vectors_retain_every_configuration_witness`<br>`test_piv_d12_marginals_do_not_prove_correlated_support`<br>`test_piv_d12_same_assignment_not_marginals` |
| PIV-D13 | Inclusive singleton bands, large unrelated gaps and NO_ADJACENT_STEP/null gap | 2 | `test_piv_d13_inclusive_single_value_band_despite_large_gap`<br>`test_piv_d13_singleton_null_gap_does_not_mean_missing_resolution` |
| PIV-D14 | Joint DAY/WEEK projection and missing retained horizon rejection | 2 | `test_piv_d14_d27_missing_retained_week_period_is_not_manufactured`<br>`test_piv_d14_joint_day_week_coherence` |
| PIV-D15 | Source-authored widening cannot escape the hard root | 1 | `test_piv_d15_authored_hard_widening_is_conflict` |
| PIV-D16 | Authored goal comparators and absent/retracted goals; no MAINTAIN fallback | 4 | `test_piv_d06_d16_goal_missing_does_not_default_to_maintain`<br>`test_piv_d16_goal_direction_comes_from_authored_instruction` |
| PIV-D17 | Mandatory daily protection cannot be dropped | 1 | `test_piv_d17_daily_claim_cannot_be_dropped` |
| PIV-D18 | Weekly center deltas remain soft and do not prove solver infeasibility | 1 | `test_piv_d18_weekly_target_is_soft_delta_not_equality` |
| PIV-D19 | Authenticated explicit precision witness; all three explicit values | 4 | `test_piv_d19_d21_every_explicit_precision_value_is_source_bound`<br>`test_piv_d19_missing_authenticated_precision_witness` |
| PIV-D20 | Full precision version/actor/evidence identity, not only its enum | 3 | `test_piv_d20_equal_precision_enum_different_identity` |
| PIV-D21 | All precision branches retain nesting/containment; non-nutrition axes rejected | 9 | `test_piv_d19_d21_every_explicit_precision_value_is_source_bound`<br>`test_piv_d21_non_nutrition_axes_cannot_become_policy_operands`<br>`test_piv_d21_unselected_precision_branch_remains_checked` |
| PIV-D22 | Separate source failure, interval conflict, H-empty, C-empty and H-minus-C | 3 | `test_piv_d22_separate_hard_and_soft_support` |
| PIV-D23 | Exact publication/registry pins and before/inside/after retained rule withdrawal | 6 | `test_piv_d23_d25_rule_withdrawal_time_is_not_early_or_rewritten`<br>`test_piv_d23_exact_publication_and_cut_identity` |
| PIV-D24 | Eight honest reviewer-expiry negatives and four rehashed forgery seams each | 12 | `test_piv_d04_d24_actual_rejected_history_is_not_honest_unavailable`<br>`test_piv_d24_honest_negative_and_forged_positive` |
| PIV-D25 | Withdrawal/future effectiveness cannot rewrite historical retained replay | 5 | `test_piv_d23_d25_rule_withdrawal_time_is_not_early_or_rewritten`<br>`test_piv_d25_withdrawal_is_distinct_from_historical_replay` |
| PIV-D26 | Private noncopyable lease; actual cut/lifetime/registry/race tests below | 1 | `test_piv_d26_lease_private_noncopyable_and_unissued_rejected` |
| PIV-D27 | Required daily unit maps; per-original-root vector equality, honest negative, rehashed forgery and equal-vector controls; no manufactured week period | 11 | `test_piv_d14_d27_missing_retained_week_period_is_not_manufactured`<br>`test_piv_d27_nonunit_required_period_sum_is_not_food_conversion`<br>`test_piv_d27_r138_conflicting_maps_rehashed_positive_rejected`<br>`test_piv_d27_r138_conflicting_nondaily_maps_faithful_negative`<br>`test_piv_d27_r138_equal_nondaily_map_vectors_remain_supported`<br>`test_piv_d27_r138_nonunit_daily_map_remains_unsupported` |
| PIV-D28 | TEST_ONLY/closed/readiness literals reject retagging | 4 | `test_piv_d28_taint_closed_flags_reject_retagging` |
| PIV-D29 | Independent imports and fresh whole-policy reconstruction | 4 | `test_piv_d29_independent_import_boundaries` |
| PIV-D30 | Bytes/nodes/depth/integers/history/anchors/states/witnesses/work/worker cancellation | 25 | `test_piv_d30_canonical_rational_output_and_temporary_bit_boundaries`<br>`test_piv_d30_collection_limit_and_overflow`<br>`test_piv_d30_encoded_bytes_exact_boundary_and_plus_one`<br>`test_piv_d30_exact_structure_node_cap_and_plus_one`<br>`test_piv_d30_exact_work_and_integer_boundaries`<br>`test_piv_d30_frozen_history_and_anchor_caps_cannot_be_raised`<br>`test_piv_d30_parser_limits_before_arithmetic`<br>`test_piv_d30_spawn_environment_scrubbed_before_interpreter_start`<br>`test_piv_d30_spawned_worker_is_killed_joined_and_output_discarded`<br>`test_piv_d30_structure_integer_and_reserved_failure_output_boundaries` |
| PIV-D31 | Exact 515+13 export set, frozen bytes and all 4183 retained executions | 2 | `test_piv_d31_all_frozen_definition_bodies_files_and_schema`<br>`test_piv_d31_collected_baseline_ids_remain_exactly_available` |
| PIV-D32 | Closed production/downstream admission and terminal UNVERIFIED_TRANSPORT | 1 | `test_piv_d32_no_production_admission_no_authority_factory` |

## 7. Real PostgreSQL — all10 obligations

The corrected focused186-case run includes **45 actual real-PG executions** below on the
protected owner-source/ordinary-reader paths with verified TLS. All10 obligations and
their exact execution mapping are retained. The complete corrected regression must
execute these same45 alongside retained PG regression; its independent receipt is
recorded on the PR. Separate runs are never added. Pure/collection does not satisfy PG.

| Obligation | Actual proof | Executions |
|---|---|---:|
| PIV-PG01 | DAY/WEEK × REPEATABLE READ/SERIALIZABLE capture→derive→fresh check→one-shot use | 4 |
| PIV-PG02 | Actual database/login/OID binding; other database/context/login, owner, SET ROLE and writable schema denied | 6 |
| PIV-PG03 | Dirty/routed/multiple/translated/nonrepeatable/writable transaction controls; close/reopen and Session/context lifetime | 10 |
| PIV-PG04 | Actual precision membership/actor/subject authorization and wrong-role controls | 3 |
| PIV-PG05 | Canonical reference/recipe/tier/rule/serving completeness; old MVCC cut versus concurrent commit and fresh cut | 6 |
| PIV-PG06 | Root/rule reader grant revoke, publication retract and future retirement; old retained replay stays historical | 4 |
| PIV-PG07 | Registry revoke/advance during actual capture and independent checking; association removed | 4 |
| PIV-PG08 | Concurrent exactly-once use, nonserializable/copy controls, exact precision-use pin and faithful non-success burn | 4 |
| PIV-PG09 | Actually blocked SQL cancellation/caller rollback, operation expiry, context-abort worker kill/join | 3 |
| PIV-PG10 | Fresh108-table installation,0017, empty nutrition content and no new v2 SQL object/role | 1 |

Exact executed PG IDs:

```text
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg01_capture_to_exactly_once_use[REPEATABLE READ-DAY]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg01_capture_to_exactly_once_use[REPEATABLE READ-WEEK]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg01_capture_to_exactly_once_use[SERIALIZABLE-DAY]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg01_capture_to_exactly_once_use[SERIALIZABLE-WEEK]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg02_actual_identity_and_unsafe_reader[other-none]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg02_actual_identity_and_unsafe_reader[root-none]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg02_actual_identity_and_unsafe_reader[self-foreign_context]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg02_actual_identity_and_unsafe_reader[self-set_role]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg02_actual_identity_and_unsafe_reader[self-writable_schema]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg02_actual_other_database_cannot_use_original_context
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg03_lifetime_and_session_exclusivity[close_reopen]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg03_lifetime_and_session_exclusivity[context_exit]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg03_lifetime_and_session_exclusivity[dirty]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg03_lifetime_and_session_exclusivity[duplicate_capture]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg03_lifetime_and_session_exclusivity[rollback_reopen]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg03_no_routed_multiple_or_translated_connections[multiple]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg03_no_routed_multiple_or_translated_connections[routed]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg03_no_routed_multiple_or_translated_connections[schema]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg03_transaction_modes_rejected[READ COMMITTED-True]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg03_transaction_modes_rejected[REPEATABLE READ-False]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg04_actual_precision_subject_authority[foreign_member]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg04_actual_precision_subject_authority[precision_actor]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg04_actual_precision_subject_authority[viewer]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg05_complete_old_cut_vs_fresh_source
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg05_missing_canonical_selection_not_favorable_partial[recipe]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg05_missing_canonical_selection_not_favorable_partial[reference]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg05_missing_canonical_selection_not_favorable_partial[rule]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg05_missing_canonical_selection_not_favorable_partial[serving]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg05_missing_canonical_selection_not_favorable_partial[tier]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg06_revocation_and_lifecycle_do_not_rewrite_old_replay[future_retirement]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg06_revocation_and_lifecycle_do_not_rewrite_old_replay[root_grant]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg06_revocation_and_lifecycle_do_not_rewrite_old_replay[rule_grant]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg06_revocation_and_lifecycle_do_not_rewrite_old_replay[rule_retract]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg07_registry_change_during_actual_operation[advance-capture]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg07_registry_change_during_actual_operation[advance-check]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg07_registry_change_during_actual_operation[revoke-capture]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg07_registry_change_during_actual_operation[revoke-check]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg08_concurrent_consumption_exactly_once
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg08_faithful_non_success_burns_lease_without_numbers[H_EMPTY]
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg08_real_capture_does_not_make_serialized_or_copy_authority
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg08_wrong_precision_use_burns_actual_lease
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg09_actual_blocked_capture_cancellation_and_caller_rollback
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg09_context_abort_kills_check_worker_and_burns_lease
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg09_expired_whole_operation_burns_real_lease
apps/backend/tests/test_postgres_policy_v2.py::test_piv_pg10_fresh_install_empty_content_and_existing_protected_objects
```

Exact executed pure IDs (including every parameterized D24 expiry variant):

```text
apps/backend/tests/test_policy_v2.py::test_piv_d01_full_joint_policy[day]
apps/backend/tests/test_policy_v2.py::test_piv_d01_full_joint_policy[week]
apps/backend/tests/test_policy_v2.py::test_piv_d02_serialized_origin_cannot_issue_lease[570098480335dbf7c731fcf0954dd4601a2ccb9d]
apps/backend/tests/test_policy_v2.py::test_piv_d02_serialized_origin_cannot_issue_lease[None]
apps/backend/tests/test_policy_v2.py::test_piv_d02_serialized_origin_cannot_issue_lease[fake1]
apps/backend/tests/test_policy_v2.py::test_piv_d02_serialized_origin_cannot_issue_lease[fake3]
apps/backend/tests/test_policy_v2.py::test_piv_d03_fully_rehashed_nre_forgery[configurations]
apps/backend/tests/test_policy_v2.py::test_piv_d03_fully_rehashed_nre_forgery[measurements]
apps/backend/tests/test_policy_v2.py::test_piv_d03_fully_rehashed_nre_forgery[periods]
apps/backend/tests/test_policy_v2.py::test_piv_d04_rehashed_mba_authority_forgery[assertion]
apps/backend/tests/test_policy_v2.py::test_piv_d04_rehashed_mba_authority_forgery[qualification]
apps/backend/tests/test_policy_v2.py::test_piv_d04_rehashed_mba_authority_forgery[reader]
apps/backend/tests/test_policy_v2.py::test_piv_d05_whole_policy_rehashed_positive_forgery[assignment]
apps/backend/tests/test_policy_v2.py::test_piv_d05_whole_policy_rehashed_positive_forgery[claim]
apps/backend/tests/test_policy_v2.py::test_piv_d05_whole_policy_rehashed_positive_forgery[coverage]
apps/backend/tests/test_policy_v2.py::test_piv_d05_whole_policy_rehashed_positive_forgery[representative]
apps/backend/tests/test_policy_v2.py::test_piv_d05_whole_policy_rehashed_positive_forgery[roots]
apps/backend/tests/test_policy_v2.py::test_piv_d05_whole_policy_rehashed_positive_forgery[trace]
apps/backend/tests/test_policy_v2.py::test_piv_d06_consistent_negative_no_numeric_use
apps/backend/tests/test_policy_v2.py::test_piv_d07_complete_identity_pins[anchor_manifest_fingerprint]
apps/backend/tests/test_policy_v2.py::test_piv_d07_complete_identity_pins[original_meaning_manifest_fingerprint]
apps/backend/tests/test_policy_v2.py::test_piv_d07_complete_identity_pins[requirement_fingerprint]
apps/backend/tests/test_policy_v2.py::test_piv_d07_complete_identity_pins[root_result_fingerprint]
apps/backend/tests/test_policy_v2.py::test_piv_d07_complete_identity_pins[root_source_fingerprint]
apps/backend/tests/test_policy_v2.py::test_piv_d07_complete_identity_pins[rule_case_id]
apps/backend/tests/test_policy_v2.py::test_piv_d08_original_source_meaning_not_wrapper_authority[contradictory]
apps/backend/tests/test_policy_v2.py::test_piv_d08_original_source_meaning_not_wrapper_authority[duplicate]
apps/backend/tests/test_policy_v2.py::test_piv_d08_original_source_meaning_not_wrapper_authority[missing]
apps/backend/tests/test_policy_v2.py::test_piv_d09_no_clinical_identity_bridge[OBSERVED_CONSUMED_FOOD_V1]
apps/backend/tests/test_policy_v2.py::test_piv_d09_no_clinical_identity_bridge[OBSERVED_OFFERED_FOOD_V1]
apps/backend/tests/test_policy_v2.py::test_piv_d09_no_clinical_identity_bridge[PHYSIOLOGICAL_INTAKE_V1]
apps/backend/tests/test_policy_v2.py::test_piv_d09_no_clinical_identity_bridge[PLANNED_OFFERED_FOOD_V1]
apps/backend/tests/test_policy_v2.py::test_piv_d10_exact_subject_and_descriptor_identity[actor_user_id]
apps/backend/tests/test_policy_v2.py::test_piv_d10_exact_subject_and_descriptor_identity[database_name]
apps/backend/tests/test_policy_v2.py::test_piv_d10_exact_subject_and_descriptor_identity[database_oid]
apps/backend/tests/test_policy_v2.py::test_piv_d10_exact_subject_and_descriptor_identity[subject]
apps/backend/tests/test_policy_v2.py::test_piv_d11_favorable_only_source_is_not_complete[recipe]
apps/backend/tests/test_policy_v2.py::test_piv_d11_favorable_only_source_is_not_complete[reference]
apps/backend/tests/test_policy_v2.py::test_piv_d11_favorable_only_source_is_not_complete[seal]
apps/backend/tests/test_policy_v2.py::test_piv_d12_same_assignment_not_marginals
apps/backend/tests/test_policy_v2.py::test_piv_d13_inclusive_single_value_band_despite_large_gap
apps/backend/tests/test_policy_v2.py::test_piv_d14_joint_day_week_coherence
apps/backend/tests/test_policy_v2.py::test_piv_d15_authored_hard_widening_is_conflict
apps/backend/tests/test_policy_v2.py::test_piv_d16_goal_direction_comes_from_authored_instruction[LOWER_GT]
apps/backend/tests/test_policy_v2.py::test_piv_d16_goal_direction_comes_from_authored_instruction[UPPER_LT]
apps/backend/tests/test_policy_v2.py::test_piv_d17_daily_claim_cannot_be_dropped
apps/backend/tests/test_policy_v2.py::test_piv_d18_weekly_target_is_soft_delta_not_equality
apps/backend/tests/test_policy_v2.py::test_piv_d19_missing_authenticated_precision_witness
apps/backend/tests/test_policy_v2.py::test_piv_d20_equal_precision_enum_different_identity[actor_user_id]
apps/backend/tests/test_policy_v2.py::test_piv_d20_equal_precision_enum_different_identity[evidence]
apps/backend/tests/test_policy_v2.py::test_piv_d20_equal_precision_enum_different_identity[version]
apps/backend/tests/test_policy_v2.py::test_piv_d21_unselected_precision_branch_remains_checked
apps/backend/tests/test_policy_v2.py::test_piv_d22_separate_hard_and_soft_support[hard_empty]
apps/backend/tests/test_policy_v2.py::test_piv_d22_separate_hard_and_soft_support[soft_empty]
apps/backend/tests/test_policy_v2.py::test_piv_d22_separate_hard_and_soft_support[soft_violation]
apps/backend/tests/test_policy_v2.py::test_piv_d23_exact_publication_and_cut_identity[issuer_epoch]
apps/backend/tests/test_policy_v2.py::test_piv_d23_exact_publication_and_cut_identity[registry_revision]
apps/backend/tests/test_policy_v2.py::test_piv_d23_exact_publication_and_cut_identity[rule_selection]
apps/backend/tests/test_policy_v2.py::test_piv_d24_honest_negative_and_forged_positive[False-GRANT-PUBLISH]
apps/backend/tests/test_policy_v2.py::test_piv_d24_honest_negative_and_forged_positive[False-GRANT-SUPERSEDE]
apps/backend/tests/test_policy_v2.py::test_piv_d24_honest_negative_and_forged_positive[False-QUALIFY-PUBLISH]
apps/backend/tests/test_policy_v2.py::test_piv_d24_honest_negative_and_forged_positive[False-QUALIFY-SUPERSEDE]
apps/backend/tests/test_policy_v2.py::test_piv_d24_honest_negative_and_forged_positive[True-GRANT-PUBLISH]
apps/backend/tests/test_policy_v2.py::test_piv_d24_honest_negative_and_forged_positive[True-GRANT-SUPERSEDE]
apps/backend/tests/test_policy_v2.py::test_piv_d24_honest_negative_and_forged_positive[True-QUALIFY-PUBLISH]
apps/backend/tests/test_policy_v2.py::test_piv_d24_honest_negative_and_forged_positive[True-QUALIFY-SUPERSEDE]
apps/backend/tests/test_policy_v2.py::test_piv_d25_withdrawal_is_distinct_from_historical_replay[RETIRE]
apps/backend/tests/test_policy_v2.py::test_piv_d25_withdrawal_is_distinct_from_historical_replay[WITHDRAW]
apps/backend/tests/test_policy_v2.py::test_piv_d26_lease_private_noncopyable_and_unissued_rejected
apps/backend/tests/test_policy_v2.py::test_piv_d27_nonunit_required_period_sum_is_not_food_conversion
apps/backend/tests/test_policy_v2.py::test_piv_d28_taint_closed_flags_reject_retagging[activation_ready-True]
apps/backend/tests/test_policy_v2.py::test_piv_d28_taint_closed_flags_reject_retagging[environment-PRODUCTION]
apps/backend/tests/test_policy_v2.py::test_piv_d28_taint_closed_flags_reject_retagging[planner_ready-True]
apps/backend/tests/test_policy_v2.py::test_piv_d28_taint_closed_flags_reject_retagging[production_admission-OPEN]
apps/backend/tests/test_policy_v2.py::test_piv_d29_independent_import_boundaries[app.modules.nutrition.policy_v2-app.modules.validation.nutrition_policy_v2]
apps/backend/tests/test_policy_v2.py::test_piv_d29_independent_import_boundaries[app.modules.validation.nutrition_policy_v2-app.modules.nutrition.policy_v2]
apps/backend/tests/test_policy_v2.py::test_piv_d29_independent_import_boundaries[app.modules.validation.nutrition_policy_v2-app.modules.nutrition.synthesis]
apps/backend/tests/test_policy_v2.py::test_piv_d29_independent_import_boundaries[app.modules.validation.nutrition_policy_v2_rules-app.modules.validation.nutrition_policy]
apps/backend/tests/test_policy_v2.py::test_piv_d30_exact_work_and_integer_boundaries
apps/backend/tests/test_policy_v2.py::test_piv_d30_parser_limits_before_arithmetic[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
apps/backend/tests/test_policy_v2.py::test_piv_d30_parser_limits_before_arithmetic[{"x":0.5}]
apps/backend/tests/test_policy_v2.py::test_piv_d30_parser_limits_before_arithmetic[{"x":1,"x":2}]
apps/backend/tests/test_policy_v2.py::test_piv_d30_parser_limits_before_arithmetic[{"x":115792089237316195423570985008687907853269984665640564039457584007913129639936}]
apps/backend/tests/test_policy_v2.py::test_piv_d30_parser_limits_before_arithmetic[{"x":NaN}]
apps/backend/tests/test_policy_v2.py::test_piv_d31_all_frozen_definition_bodies_files_and_schema
apps/backend/tests/test_policy_v2.py::test_piv_d32_no_production_admission_no_authority_factory
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d01_d07_missing_full_anchor_not_hidden_by_comfort_requirements[root]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d01_d07_missing_full_anchor_not_hidden_by_comfort_requirements[unselected]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d04_d24_actual_rejected_history_is_not_honest_unavailable[GRANT]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d04_d24_actual_rejected_history_is_not_honest_unavailable[QUALIFY]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d04_d24_actual_rejected_history_is_not_honest_unavailable[journal]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d04_d24_actual_rejected_history_is_not_honest_unavailable[publisher]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d06_d16_goal_missing_does_not_default_to_maintain[absent]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d06_d16_goal_missing_does_not_default_to_maintain[retracted]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d06_faithful_unavailable_nre_is_consistent_but_not_admitted
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d10_one_sided_roots_and_reference_target_are_not_invented_intervals
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d12_equal_vectors_retain_every_configuration_witness
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d12_marginals_do_not_prove_correlated_support[20-True]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d12_marginals_do_not_prove_correlated_support[43-False]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d13_singleton_null_gap_does_not_mean_missing_resolution
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d14_d27_missing_retained_week_period_is_not_manufactured
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d19_d21_every_explicit_precision_value_is_source_bound[PRECISION]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d19_d21_every_explicit_precision_value_is_source_bound[RELAXED]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d19_d21_every_explicit_precision_value_is_source_bound[STANDARD]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d21_non_nutrition_axes_cannot_become_policy_operands[BudgetContract]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d21_non_nutrition_axes_cannot_become_policy_operands[CostPreference]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d21_non_nutrition_axes_cannot_become_policy_operands[KitchenEffort]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d21_non_nutrition_axes_cannot_become_policy_operands[TasteFit]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d21_non_nutrition_axes_cannot_become_policy_operands[convenience]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d23_d25_rule_withdrawal_time_is_not_early_or_rewritten[after]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d23_d25_rule_withdrawal_time_is_not_early_or_rewritten[before]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d23_d25_rule_withdrawal_time_is_not_early_or_rewritten[inside]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_canonical_rational_output_and_temporary_bit_boundaries
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_collection_limit_and_overflow[JointPolicySupportV2-assignments]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_collection_limit_and_overflow[JointPolicySupportV2-center_deltas]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_collection_limit_and_overflow[NutritionPolicyBodyV2-claims]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_collection_limit_and_overflow[NutritionPolicyBodyV2-coverage]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_collection_limit_and_overflow[PolicyAssignmentEvaluationV2-configuration_ids]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_encoded_bytes_exact_boundary_and_plus_one[16777216]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_encoded_bytes_exact_boundary_and_plus_one[2097152]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_encoded_bytes_exact_boundary_and_plus_one[262144]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_encoded_bytes_exact_boundary_and_plus_one[33554432]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_encoded_bytes_exact_boundary_and_plus_one[50331648]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_encoded_bytes_exact_boundary_and_plus_one[65536]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_encoded_bytes_exact_boundary_and_plus_one[8388608]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_exact_structure_node_cap_and_plus_one
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_frozen_history_and_anchor_caps_cannot_be_raised
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_spawn_environment_scrubbed_before_interpreter_start
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_spawned_worker_is_killed_joined_and_output_discarded[cancelled]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_spawned_worker_is_killed_joined_and_output_discarded[deadline]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d30_structure_integer_and_reserved_failure_output_boundaries
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d31_collected_baseline_ids_remain_exactly_available
```

PIV-R138-01 additional executed pure IDs (also included in PIV-D27 above):

```text
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d27_r138_conflicting_maps_rehashed_positive_rejected[1-2]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d27_r138_conflicting_maps_rehashed_positive_rejected[2-1]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d27_r138_conflicting_nondaily_maps_faithful_negative[1-2]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d27_r138_conflicting_nondaily_maps_faithful_negative[2-1]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d27_r138_equal_nondaily_map_vectors_remain_supported[1]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d27_r138_equal_nondaily_map_vectors_remain_supported[2]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d27_r138_equal_nondaily_map_vectors_remain_supported[3]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d27_r138_nonunit_daily_map_remains_unsupported[1-2]
apps/backend/tests/test_policy_v2_adversarial.py::test_piv_d27_r138_nonunit_daily_map_remains_unsupported[2-1]
```

## 8. Compatibility, migration and fresh install

**528 = 515 unchanged legacy definitions + 13 exact additive names.** The new PIV-D31 guard
compares every baseline body/hash, requires the complete old name set and the exact new name
set below, and rejects deletion, rename or replacement. A local direct comparison to the
approved git blob additionally verified all 515 bodies, all 503 historical MBA pins and all 53
historical frozen source/migration files byte-for-byte. The new source pin set has 59 files
because it additionally retains the six frozen MBA implementation files. No historical
fixture/hash baseline changed. All4183 prior test executions remain; none skipped/xfail.

- `JointPolicySupportV2`
- `NutritionPolicyBodyV2`
- `NutritionPolicyCheckV2`
- `NutritionPolicyHandoffV2`
- `NutritionPolicyIntegrationInputV2`
- `NutritionPolicyResultV2`
- `PolicyAssignmentEvaluationV2`
- `PolicyCenterDeltaV2`
- `PolicyClaimCoverageV2`
- `PolicyDiagnosticV2`
- `PolicyIntegrationIdentityV2`
- `PolicyV2CaptureFailure`
- `PolicyV2Use`

Only the seven owner-authorized historical files change export metadata: candidate feature
projection, hierarchical affinity compatibility, hierarchy compatibility, nutrition
resolution, nutrition root architecture, TasteFit architecture and shared-target TasteFit
architecture. Their exact historical sets remain; the SMTF historical projection stays403.
The independently authored `policy_v2_export_names.json` contains the 13 approved registration
names, never inferred from actual schema output. PIV-D31 pins that manifest against its own
literal expected set and checks all 515 old bodies. Hash/frozen-file/migration/identity/behavior
assertions remain intact. The new guard reverses only exact authorized metadata before
checking all 126 original test-file hashes; historical fixtures/hashes are not rewritten.

Four historical parameter labels generate UUIDs at collection time. Only four explicitly
enumerated function/field labels normalize that generated label for identity comparison;
all original parameterized executions, values, assertions and cardinalities are retained.

Schema remains **0017 /108 domain tables** (plus Alembic's version table). No 0018, new
persistent model/table/column, SQL function, role, capability or runtime grant is added.
Fresh-install PG10 finds every nutrition_* table empty: **0 production content/providers/
enrollments/qualifications/publications/seeds/defaults**. Synthetic test-authored records
exist only in disposable test databases and private TEST_ONLY fixture contexts.

## 9. Initial-head verification receipts

The table below is the historical initial-head receipt for
`4b148213898bd4bacdb7ecc442e91aa2fdaeb48d`, not proof of the corrected head.
Its [CI 42365950677](https://github.com/thedusk4203/Menuto/actions/runs/42365950677)
does not substitute for the new exact-head run required by PIV-R138-01.

| Check | Actual result |
|---|---|
| Seven authorized historical compatibility cases | 7 passed, 0 skips |
| New exact additive-delta/frozen compatibility guard | 1 passed, 0 skips |
| Single focused PIV run | 177 passed, 0 skips = 132 pure + 45 real PG |
| Single complete regression run | **4360 passed, 0 skips = 4183 retained + 177 additive** |
| Dedicated SCRAM/TLS smoke | **16/16**, actual verified TLS/SCRAM paths |
| Benchmark | **22/22** |
| Client contracts/tests/typecheck/web build | PASS; **10/10** client cases |
| Ruff/architecture/import/export/OpenAPI/synthetic fixtures | PASS; old guards retained |

Commands reproduce the unchanged repository CI workflow: `pytest`, dedicated authentication
smoke, Ruff, architecture/import guards, domain/OpenAPI export checks, synthetic fixtures,
benchmark, client contract generation/typecheck/tests and web build. Local JUnit/guard logs
are retained in the implementation worktree's ignored `.local/` receipt directory. Exact-head
GitHub Actions run ID/SHA/Python/web outcomes are recorded in the implementation PR receipt
after completion; earlier baseline or code-head runs never substitute for final-head CI.

## 10. Local reconciliation and remaining boundaries

The original unfinished branch remains `codex/mtr006-policy-integration-v2` at
`1679d6035dd6685118df6c95fa37628384cc961c`. Before/after inventories retain its exact 19-file
dirty/untracked state and all19 byte SHA-256 values. No reset/discard/overwrite/commit/push
was performed there. Three unrelated graph artifacts were preserved and not transferred.
A separate worktree/branch `codex/mtr006-v2-resumed-implementation` starts at corrected main.

Original 19-file before/after inventory (the same SHA-256 was independently rechecked after
the authorized changes; these files were never committed or published from that worktree):

| Original path | Before SHA-256 = after SHA-256 |
|---|---|
| `graphify-out/GRAPH_REPORT.md` | `4dfa14b5d6f2f7f97b0e2f9c0cf8491fdf53b6b832718a465b1950d5fd2cd637` |
| `graphify-out/graph.html` | `065f982c3cb8a3c5ed3ac2daaa7291790dee245a135325116b1f299d97f44360` |
| `graphify-out/graph.json` | `15d4173af96f59462a1df251032c0bbe23b3219cf37c4337ebd506f91f76f775` |
| `packages/contracts/domain.schema.json` | `06d39b8a2a598ecf97bb62a83cb6dc1ebc6976a4b50f8b026b3d1e1ed80a6b4e` |
| `tools/check_import_boundaries.py` | `1dd2c172456008f1f104a1cf858f3cd43ada7b9e161612f18a5ae0ee82d33086` |
| `tools/export_domain_contracts.py` | `08866964a7859fecd6ba2c9fb7275f368f6aa24c32e838366ebf1d9fad95bc2e` |
| `apps/backend/app/modules/nutrition/policy_v2.py` | `c3da52a681e67c986694d7054b45de37356f90af272fda0d9940a7c10117a162` |
| `apps/backend/app/modules/nutrition/policy_v2_contracts.py` | `392d7a2189bbd6b8661e254a0c2762ce10fb42897f92a30f198ea9086fe64bab` |
| `apps/backend/app/modules/nutrition/policy_v2_limits.py` | `8d5d07586d38ae9cdb57453d35ab47b3eaaffdf93c7011579ea8b1b98bff972a` |
| `apps/backend/app/modules/nutrition/policy_v2_public.py` | `eaa6bdc4e000567c377c176692233010edd3533e6ec60da008e7757276ac8986` |
| `apps/backend/app/modules/nutrition/policy_v2_rules.py` | `3ad222001423c64d22fb893a0574ea069c8eaeb74caacda97d24dd65b223527a` |
| `apps/backend/app/modules/planning/policy_v2_capture.py` | `4c431ecafbeb40b5e5a32a9b560674384c931f2d7a75d8e7e9857d82bba6a208` |
| `apps/backend/app/modules/planning/policy_v2_worker.py` | `cfee27d5811951c2ed58a102ef4c1a0219abc81343a697c19bef91b341827a1d` |
| `apps/backend/app/modules/validation/nutrition_policy_v2.py` | `c460c7f1490b255e4ef69abb7a43f2d78cda9112ea0585015437c125e67f85d4` |
| `apps/backend/app/modules/validation/nutrition_policy_v2_rules.py` | `86449346cb3309e2da5d2eaf35aab6e2f8d49e1d82b3018bc02750f9e42b68b5` |
| `apps/backend/tests/policy_v2_fixtures.py` | `f3d6b34db3e1019880e73ccf28f22f34aad334b67f15902709aa5059851a6fcd` |
| `apps/backend/tests/policy_v2_postgres_fixtures.py` | `9d419d50daaa370c70db295b8330ca85b459a57710c02a7bde0274ec7c39b0df` |
| `apps/backend/tests/test_policy_v2.py` | `51206e52433135e852ab946adc013d42901ddc9c9e546a89601532d6be7f10c7` |
| `apps/backend/tests/test_postgres_policy_v2.py` | `d0ffc035c3dea8bf36d628e6f027bf8b737c8c12c6c1b71571ba26ff298c8181` |

- **Retained:** additive carrier/source pins, separate v2 finite operator semantics, complete
  joint H/C evidence and closed non-authority transport.
- **Adapted:** corrected D24 honest-negative/forged-positive split, fresh negative child
  reconstruction, precise source lifecycle/goal missingness, Session exclusivity, worker
  cancellation/deadline accounting and structural resource limits.
- **Replaced:** git-history-dependent shallow-CI compatibility checks with contained baseline
  pins; thin/manual coverage with executed32-family/10-PG mappings; random UUID tier selection
  in the new WEEK fixture with its exact authored TEST_ONLY one-serving tier.
- **Not implemented, intentionally out of scope:** production science/content/qualification,
  conversions/consumption allocation, MTR-008 precedence, solver/preview/activation and downstream work.

The historical58-pass/1-fail run and interrupted pre-exception full run are diagnostic history,
not acceptance receipts. The exact total above comes from one complete green regression.

Root/MTR-006 v1/MTR-007/MBA structural foundations remain FROZEN and unchanged. Full
MTR-006/007/008 remain INCOMPLETE; issues #5/#6/#7 remain OPEN. Production Nutrition/clinical
content gate CLOSED, planner_ready=False, activation_ready=False, Execution NOT STARTED,
PRECOMMIT FAIL-CLOSED. This implementation is NOT MERGED / NOT FROZEN; independent
implementation review and separate owner merge/freeze authorization are still required.

## 11. Complete changed-file inventory

Exactly 31 files in this bounded implementation:

- `apps/backend/app/modules/nutrition/policy_v2.py`
- `apps/backend/app/modules/nutrition/policy_v2_contracts.py`
- `apps/backend/app/modules/nutrition/policy_v2_limits.py`
- `apps/backend/app/modules/nutrition/policy_v2_public.py`
- `apps/backend/app/modules/nutrition/policy_v2_rules.py`
- `apps/backend/app/modules/planning/policy_v2_capture.py`
- `apps/backend/app/modules/planning/policy_v2_worker.py`
- `apps/backend/app/modules/validation/nutrition_policy_v2.py`
- `apps/backend/app/modules/validation/nutrition_policy_v2_rules.py`
- `apps/backend/tests/fixtures/policy_v2_compatibility.json`
- `apps/backend/tests/fixtures/policy_v2_export_names.json`
- `apps/backend/tests/policy_v2_fixtures.py`
- `apps/backend/tests/policy_v2_postgres_fixtures.py`
- `apps/backend/tests/test_candidate_feature_projection.py`
- `apps/backend/tests/test_hierarchical_affinity_compatibility.py`
- `apps/backend/tests/test_hierarchy_compatibility.py`
- `apps/backend/tests/test_nutrition_resolution.py`
- `apps/backend/tests/test_nutrition_root_architecture.py`
- `apps/backend/tests/test_policy_v2.py`
- `apps/backend/tests/test_policy_v2_adversarial.py`
- `apps/backend/tests/test_postgres_policy_v2.py`
- `apps/backend/tests/test_shared_target_tastefit_architecture.py`
- `apps/backend/tests/test_tastefit_architecture.py`
- `docs/product/BACKLOG.md`
- `docs/product/FOUNDATION_STATUS.md`
- `docs/product/IMPLEMENTATION_BLUEPRINT.md`
- `docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md`
- `docs/product/MTR_006_POLICY_INTEGRATION_V2_IMPLEMENTATION_EVIDENCE.md`
- `packages/contracts/domain.schema.json`
- `tools/check_import_boundaries.py`
- `tools/export_domain_contracts.py`

## 12. PIV-R138-01 — independent period-map differential correction

[Independent review 6706823011](https://github.com/thedusk4203/Menuto/pull/138#issuecomment-6706823011)
identified a producer/checker divergence at initial head
`4b148213898bd4bacdb7ecc442e91aa2fdaeb48d`. The producer already rejects different complete
coefficient vectors for the same original root. Validation recorded only required daily
root presence, so it missed conflicting maps for another root. The correction independently
retains and compares exact rational vectors for every FINITE_PERIOD_SUM. It neither imports
the producer evaluator nor changes producer semantics; daily unit and containment guards
remain in place.

The TEST_ONLY WEEK fixture authors a zero-valued PROTEIN reference center outside
`case.daily_root_keys`, seven explicit period projections and two valid-shape sums of that
same original root. The entire guideline/rule/review/publication/meaning source is reauthored
and rehashed, with fresh NRE and MBA evidence. Frozen contracts accept the fixture unchanged.
The zero reference makes conflicting maps numerically equal, isolating semantic consistency
from arithmetic plausibility. These are symbolic test values, not nutritional content.

| Differential control | Executions | Required and observed corrected result |
|---|---:|---|
| Conflicting same-origin non-daily vectors, integer/fraction | 2 | Producer UNSUPPORTED/UNSUPPORTED_TEMPORAL_MAP, payload=null; checker CONSISTENT/NOT_ADMITTED |
| Fully rehashed favorable policy on the identical conflicting retained sources | 2 | Checker INCONSISTENT/NOT_ADMITTED; matching source/result/support hashes cannot authorize positive use |
| Equal non-daily vectors, coefficient values 1, 2 and 3 | 3 | AVAILABLE_TEST_ONLY and independently CONSISTENT; no global unit-only restriction added |
| Required daily map with integer/fraction non-unit coefficient | 2 | Producer UNSUPPORTED/UNSUPPORTED_TEMPORAL_MAP, payload=null; checker CONSISTENT/NOT_ADMITTED |

Before correction, the nine-case run was **4 failed /5 passed**: both faithful negatives
were wrongly INCONSISTENT and both rehashed favorable claims were wrongly CONSISTENT.
After correction the same nine cases are **9 passed /0 skipped**. The unchanged existing
daily-unit test separately passed. This reproduces and fixes the pure-checker semantic
finding; it does not claim a demonstrated exploit through the trusted capture/lease host.
The forged result uses a genuine equal-vector control and recomputes all changed source,
basis, coverage, support and outer fingerprints without bypassing either producer or checker.
Its helper reuses only joint-witness arithmetic to author the hostile claim, never a checker
decision or the producer evaluator as a correctness oracle.

The corrected focused run is **186 passed /0 skipped =141 pure +45 actual PostgreSQL**,
covering all 32 PIV-D families and all 10 PIV-PG obligations. The seven historical metadata
guards plus the exact additive compatibility guard separately passed (8/8). The corrected
collection is 4369 = 4183 baseline +186 additive; collection is not a full-suite PASS.
Dedicated SCRAM/TLS passed 16/16, benchmark 22/22, client 10/10, and architecture/import/
export/OpenAPI/fixtures/Ruff/typecheck/web-build guards passed on this correction tree.
Corrected-head full regression, dedicated SCRAM/TLS, benchmark, web/client and exact-head
GitHub Actions status must be recorded in the new correction receipt on PR #138 after completion,
not inferred from these focused runs or the initial-head receipt.

Only three existing PR files change for this finding: the Validation-owned rules module,
the additive adversarial test module and this evidence document. The original Nutrition
producer, all historical fixtures/guards and frozen source/migration files remain untouched.
515 legacy definition bodies plus the exact 13 additive names remain 528; all 503 historical
hashes and 53 frozen source/migration files (plus 6 MBA companion pins) remain unchanged.
Schema remains 0017/108, no 0018, no new persistence/SQL objects/roles/privileges. The protected
original worktree's 19 dirty files retain their inventory and byte hashes.

PR #138 must remain OPEN /auto-merge OFF for independent re-review. No self-approval,
merge or structural freeze is recorded here. Production Nutrition/clinical content gate
remains CLOSED; full MTR-006/007/008 INCOMPLETE, planner_ready=False, activation_ready=False,
Execution NOT STARTED and PRECOMMIT FAIL-CLOSED. No downstream authorization is implied.
