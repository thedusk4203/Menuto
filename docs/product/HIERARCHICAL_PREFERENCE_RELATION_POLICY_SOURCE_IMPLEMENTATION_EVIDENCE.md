# Hierarchical preference relation / transfer-policy source — implementation evidence

Status: **IMPLEMENTED / NOT FROZEN / IMPLEMENTATION REVIEW PENDING — NOT MERGED**.
Prepared 2026-10-27. SOURCE ONLY; milestone number unassigned; this is not MTR-040C.

## Authorization and exact baseline

The user approved the combination of the [source design](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_DESIGN.md)
and [neutral-anchor correction](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_NEUTRAL_ANCHOR_CORRECTION.md),
then separately authorized this implementation and additive migration0015. The correction supersedes
only stricter finite-map semantics. The current instruction explicitly requires an open implementation
PR: green CI does not authorize merge, freeze or a consumer implementation.

| Receipt | Value |
| --- | --- |
| Repository | `thedusk4203/Menuto` |
| Exact implementation base / canonical main independently verified before edits | `4ad3f682554b7feee9f333eca1f1f5c258852f5e` |
| Exact baseline push CI | [40386371459](https://github.com/thedusk4203/Menuto/actions/runs/40386371459), SUCCESS; python/web SUCCESS |
| Dedicated branch | `codex/hierarchy-relation-policy-source` |
| Baseline Python identities | 2,597, captured before implementation |
| Baseline schema / definitions | Alembic0014 /78 domain tables /318 exported definitions; no competing migration at start |
| Implementation code/test head | `64a78f3944f0e2d863164c3d47c34d4274168187` |
| PR | [#104](https://github.com/thedusk4203/Menuto/pull/104), OPEN / NOT MERGED; final review head and exact-head CI in PR delivery receipt |

The final review head and its CI receipt will be recorded in the PR delivery body without a
self-referential commit hash. This document's follow-up receipt may cite an earlier code/test commit;
the PR's final-head CI must cover any later evidence/status-only commit as well.

## Implemented boundary and persistence

Preferences owns global reviewed transfer semantics and publication. Household/member authorship,
Catalog/Recipes classification and the frozen prior publisher grant no hierarchy authority. The
internal public facade exposes registration, enrollment, grant/revoke, publication, authorized capture
and pure source resolution. No HTTP endpoint or UI is added. No member declarations are read.

`hierarchy_contracts.py` holds closed, immutable, recursively reconstructed source primitives.
`hierarchy_sources.py` owns caller-transaction SQL entry points and the remote verify-full guard.
`hierarchy_resolution.py` replays primitive authority/publication/owner histories with zero IO.
`hierarchy_models.py` and standalone migration0015 provide the additive persistence boundary.
The frozen explicit/compatibility bodies are pinned for hierarchy replay only, without global
ownership/default authority. The source lookup returns an authored mapping row, not an inherited
member result; attenuation is stored and validated but no member arithmetic is performed.

Seven new domain tables bring78→85 (86 physical tables including `alembic_version`):

| Table | Responsibility |
| --- | --- |
| `hierarchy_source_providers` | Immutable independently registered provider and database identity |
| `hierarchy_source_principals` | Enrolled database OID/name and login OID/name binding |
| `hierarchy_source_authority` | Append-only provider capability GRANT/REVOKE events |
| `hierarchy_source_frontiers` | Atomically advanced source/authority/interleaved-journal heads |
| `hierarchy_source_streams` | Exact typed policy/relation stream identity and checked head cache |
| `hierarchy_source_revisions` | Immutable complete replacements/tombstones, actor, policy/context/support pins |
| `hierarchy_source_mutations` | Complete interleaved append-only publication/authority journal |

Publication rows store owner-controlled fact IDs, fingerprints and frontier cuts in `owner_pins`.
They do **not** store capture snapshots, resolved child results, member preferences or inferred values.
At capture/receipt time, narrow owner-controlled adapters reconstruct historical Catalog/Recipes
primitives from canonical immutable owner storage and verify those pins. Captures contain both those
historical publication cuts and current canonical support facts for fresh applicability. The full
source fingerprint covers the complete captured journal/manifests, including unfavorable history.

Migration0015 imports no older migration implementation. Empty→0015 and0014→0015 upgrades,
metadata parity, empty downgrade→0014→upgrade, and populated loss-refusing downgrade are exercised
against PostgreSQL. All seven tables are asserted empty immediately after upgrade: no provider,
principal, grant, relation, enabled direction, transfer row, production coefficient or prior is seeded.
Migrations0001–0014 remain byte-identical. Historical tests only update the current head/table-count
expectations and retain verification of the frozen migration prefix.

## Authority, lifecycle and replay evidence

The hierarchy-specific protected non-login owners, admin/client roles and publication/capture grants
are independent of the frozen prior source. Authentication derives from actual PostgreSQL SCRAM
sessions (`system_user` plus session role OID/name), with remote server-identity TLS verification.
Current unsafe superuser, database owner, hierarchy admin/function owner and reachable privilege
graphs are rejected on normal application interfaces. Dropping/recreating or renaming a login cannot
transfer an enrolled binding/grant. GUCs, UUIDs, hashes and REVIEWED_REFERENCE provenance are data,
not credentials. Privileged deployment administrators remain a trust root, not an application actor.

PostgreSQL itself enforces all protected operations: application roles have no direct table SELECT/
DML/TRUNCATE, enrollment/frontier bypass, private-function execution, role escalation or owner-support
write capability. Functions use qualified objects and hardened search paths; owner adapters have
narrow SELECT-only permissions. Tests use actual separate SCRAM connections, including wrong-password,
trust/password rejection, wrong login/provider, unsafe role graphs and certificate verification.

Publication locks the provider frontier, rechecks the current capability, then considers an exact
idempotent retry. Revocation therefore defeats an old receipt. CAS binds the interleaved journal
head, source generation, predecessor and stream revision. The caller owns commit/rollback; receipts
explicitly say `CALLER_TRANSACTION_NOT_CERTIFIED`. Replacements, policy supersession, tombstones,
republishing and current support changes never rewrite old publication facts or silently repin them.
Server clocks are immediate; equal clocks use journal order; regression/overflow fail closed.

Real concurrency coverage includes competing policy/relation/admin writes, stale CAS, grant/revoke
versus publish/retract in both lock orders, competing relation retractors, rollback, and existing
RR/SERIALIZABLE read-only cuts while a writer commits. Fresh capture requires current CAPTURE at its
snapshot cut; an earlier coherent cut can finish after a later revoke and is not a portable live token.

The complete closed25-cell matrix is explicit; deny cells carry no mapping data. Finite semantic rows
bind the full kind/compatibility fingerprint, explicit semantic state and exact frozen raw amount.
NEUTRAL→0/1, DISLIKE≤0, LIKE≥0, and strict order where multiple states exist are checked in Python
and raw PostgreSQL publication. Exact cross-products avoid rounded comparisons. No interpolation,
nearest-row fallback, implicit zero, sign reversal, amplification, policy/provider fallback or
classification-only relation creation is permitted.

Exact recipe endpoints always pin RecipeVersion; classified METHOD/FLAVOR/MAIN_PROTEIN additionally
pin the frozen applicability/path and reviewed support chain. New versions do not retarget relations.
Ingredient positive partial/complete support is distinct from reviewed-none, absence, unresolved,
retraction and supersession. Current unresolved competing parents remain visible diagnostics and
prevent silent selection. Cycle validation may inspect topology to reject forbidden publication;
it does not perform recursive preference propagation, path scoring or transitive member derivation.

Offline replay checks internal self-consistency; a rehashed fabricated source is not proof of canonical
database origin or live authority. Trust in the database capture boundary is still required.

## Acceptance map — complete source categories and correction

All names below are concrete test functions in `apps/backend/tests/`. Parametrized variants are
included. Prefixes identify these files: **P**=`test_hierarchy_policy.py`,
**A**=`test_postgres_hierarchy_authority.py`, **Auth**=`test_postgres_hierarchy_authentication.py`,
**C**=`test_postgres_hierarchy_classification.py`, **L**=`test_postgres_hierarchy_lifecycle.py`,
**R**=`test_postgres_hierarchy_replay_guards.py`, **DBP**=`test_postgres_hierarchy_policy_parity.py`,
**Src**=`test_postgres_hierarchy_source.py`, **Compat**=`test_hierarchy_compatibility.py`.
The normative design calls C01/C02 coordinate/mapping cases; context/classification is also covered
explicitly under I03/I04/R02. No case is renamed to narrow its meaning.

| Case | Concrete enforcement tests |
| --- | --- |
| A01 Authentication | Auth:`test_a01_real_scram_login_and_immutable_enrollment`, `test_a01_wrong_password_rejected_by_postgresql`, `test_a01_trust_and_unsupported_auth_cannot_be_authority`, `test_a01_real_unsafe_superuser_admin_sessions_denied_normal_interface`, `test_a01_verified_tls_and_server_certificate`, `test_a01_remote_interface_requires_verify_full_before_connection`; A:`test_a01_actual_scram_database_owner_denied` |
| A02 Authority separation | A:`test_a02_no_provider_or_principal_fallback`, `test_a02_raw_sql_claimed_authority_fields_rejected`, `test_a02_guc_and_temp_shadow_cannot_mint_or_change_actor`, `test_a02_prior_credentials_and_grants_not_hierarchy_authority`, `test_a02_real_household_roles_and_self_authorship_do_not_authorize_source`; C:`test_i03_hierarchy_curator_cannot_publish_classification_fact` |
| A03 Database enforcement | A:`test_a03_no_direct_source_table_bypass` (all7 tables ×5 operations), `test_a03_function_role_search_path_and_classification_escalation_denied`, `test_a03_current_unsafe_membership_denied_after_enrollment` |
| A04 Enrollment/revocation | Src:`test_a01_separate_hierarchy_registration_and_enrollment`; A:`test_a04_revoke_precedes_idempotent_receipt_and_old_replay_stays_stable`, `test_a04_renamed_login_does_not_inherit_old_binding`, `test_a04_registry_idempotency_does_not_grant_other_provider_access`, `test_a04_grant_retry_is_history_not_regrant_and_fresh_noop_rejected`; R:`test_a04_recreated_same_login_name_cannot_reuse_old_oid_grants`; L:`test_a04_l02_revoke_publication_races_order_on_shared_frontier` |
| I01 Typed identity | P:`test_i01_self_edge_same_kind_exact_identity_rejected` (all5 kinds); Src:`test_i01_exact_relation_publication_and_eligibility`; C:`test_i03_reviewed_reverse_direction_requires_its_own_policy_and_relation`; R:`test_i01_missing_or_wrong_kind_owner_identity_never_publishes` |
| I02 Direction matrix | P:`test_i02_complete_closed25_cells_no_automatic_relation` (all25 pairs), `test_i02_invalid_matrix_never_wildcard`; DBP:`test_h01_h06_raw_sql_semantic_and_coordinate_guard`; L:`test_i02_policy_lineage_has_no_fallback` |
| I03 Classification | C:`test_i03_canonical_ingredient_positive_support_partial_or_complete`, `test_i03_no_absence_unresolved_or_reviewed_none_can_publish_relation`, `test_r02_catalog_correction_changes_fresh_support_but_old_cut_replays`, `test_g02_unresolved_parent_is_diagnostic_not_silently_dropped`; frozen `test_postgres_culinary_features.py::test_overlap_registration_and_atomic_rekey` rejects canonical overlapping scopes |
| I04 Recipe binding | P:`test_i04_recipe_version_binding_is_explicit`; C:`test_i04_frozen_recipe_classification_full_support_and_exact_context` (METHOD/FLAVOR/MAIN_PROTEIN), `test_i04_missing_or_forged_recipe_context_never_selects_latest`, `test_i04_reviewed_scope_uses_exact_nonzero_authored_path`, `test_i04_reviewed_exact_recipe_pair_needs_version_but_no_classification_claim` |
| C01 Coordinates | P:`test_c01_forged_descriptor_rejected`, `test_h05_h06_rehashed_forged_semantic_amount_pair_rejected`; DBP:`test_h01_h06_raw_sql_semantic_and_coordinate_guard` |
| C02 Finite mapping/attenuation | P:`test_c02_strict_authored_components_before_reduction`, `test_c02_no_default_zero_negative_amplifying_or_noncanonical_attenuation`, `test_h08_missing_semantic_row_has_no_zero_fallback`; DBP:`test_c02_exact_nearby_rationals_use_cross_products_not_rounded_division`, `test_h08_partial_finite_semantic_map_is_published_without_filling_rows` |
| L01 Lifecycle | L:`test_l01_l03_immutable_receipts_replacement_retraction_republish`, `test_l01_relation_tombstone_not_absence_and_old_cut_stable`, `test_l01_policy_supersession_needs_explicit_relation_repin`, `test_l02_stale_cas_and_transaction_rollback_leave_no_partial_source` |
| L02 Concurrency | L:`test_l02_real_two_writers_one_provider_frontier_winner`, `test_l02_stale_cas_and_transaction_rollback_leave_no_partial_source`, `test_a04_l02_revoke_publication_races_order_on_shared_frontier`, `test_l02_two_relation_retractors_have_one_cas_winner`; R:`test_l02_competing_admin_grants_have_one_frontier_winner` |
| L03 Idempotency/time | L:`test_l01_l03_immutable_receipts_replacement_retraction_republish`, `test_l03_caller_time_unknown_fields_and_invalid_tombstone_rejected`; R:`test_l03_capture_clock_regression_rejected`, `test_l03_equal_server_times_order_by_journal_and_regression_rejects`, `test_l03_counter_bounds_reject_before_database_work` |
| G01 Graph limits | L:`test_g01_same_kind_reverse_cycle_rejected_including_stale_policy_heads`, `test_g01_cross_kind_cycle_rejects_without_recursive_preference_derivation`; P:`test_i01_self_edge_same_kind_exact_identity_rejected`; source result contract has no inherited parent/member arithmetic |
| G02 Ambiguity | L:`test_g02_multiple_reviewed_parents_unavailable_without_selection`, `test_g02_diamond_merge_has_no_double_count_or_automatic_parent_selection`; C:`test_g02_unresolved_parent_is_diagnostic_not_silently_dropped` |
| R01 Capture/replay | Src:`test_r01_durable_rows_hold_owner_pins_not_capture_snapshots`, `test_l01_policy_publication_and_complete_source_replay`; L:`test_r01_coherent_capture_and_zero_io_recursive_replay`, `test_r01_omitted_complete_source_child_rejected_even_rehashed`, `test_r01_capture_requires_clean_readonly_coherent_transaction`, `test_r01_existing_capture_cut_is_stable_during_committed_publication`, `test_r01_capture_authority_is_at_its_cut_not_a_live_token`; R:`test_r01_capture_with_pending_orm_writes_rejects` |
| R02 Corrections | C:`test_r02_catalog_correction_changes_fresh_support_but_old_cut_replays`, `test_i04_frozen_recipe_classification_full_support_and_exact_context`; L:`test_l01_policy_supersession_needs_explicit_relation_repin`, `test_l01_relation_tombstone_not_absence_and_old_cut_stable`; source reads neither declarations nor priors, so changes there cannot authorize source transfer |
| S01 State separation | L:`test_i02_policy_lineage_has_no_fallback`, `test_l01_relation_tombstone_not_absence_and_old_cut_stable`, `test_l01_policy_supersession_needs_explicit_relation_repin`; C:positive/negative/correction cases above; P:H07/H08 and DBP:H07/H08 distinguish authored zero from absence |
| S02 Frozen/soft boundary | Compat:`test_s02_all318_definitions_and_frozen_dependencies_retained`, `test_s02_retained_2597_baseline_node_identities`; L:`test_s02_populated_source_downgrade_refuses_history_loss`, `test_r01_coherent_capture_and_zero_io_recursive_replay`; all existing frozen acceptance suites retained |
| H01 NEUTRAL nonzero | P:`test_h01_neutral_nonzero_rejected`; DBP:`test_h01_h06_raw_sql_semantic_and_coordinate_guard` |
| H02 DISLIKE positive | P:`test_h02_h03_anti_correlation_rejected[DISLIKE-1]`; DBP:raw SQL `H02` case |
| H03 LIKE negative | P:`test_h02_h03_anti_correlation_rejected[LIKE--1]`; DBP:raw SQL `H03` case |
| H04 Positive raw NEUTRAL | P:`test_h04_h07_positive_source_neutral_is_available_exact_zero`; DBP:`test_h04_h07_h09_positive_source_neutral_publishes_zero_without_global_ownership` |
| H05 Forged semantic pair, rehashed | P:`test_h05_h06_rehashed_forged_semantic_amount_pair_rejected`; DBP:raw SQL `H05` mismatched semantic/amount pair |
| H06 Wrong expected frozen amount | Same parametrized P/DBP pair; raw amount and frozen-policy fingerprint checked independently |
| H07 Zero is AVAILABLE | P:H04/H07; DBP:H04/H07/H09 asserts exact numerator0 /denominator1 |
| H08 Missing semantic row | P:`test_h08_missing_semantic_row_has_no_zero_fallback` (all3 states); DBP:`test_h08_partial_finite_semantic_map_is_published_without_filling_rows` |
| H09 Replay-only policy ownership | P:`test_h09_policy_pin_is_replay_only_no_global_ownership`; DBP:`test_h04_h07_h09_positive_source_neutral_publishes_zero_without_global_ownership` also asserts no prior-provider/member-declaration writes |

Member-dependent clauses (destination direct/retraction precedence, inherited-only parent rejection,
opposite-sign member values, strength propagation) remain constraints on the **future consumer**.
This source exposes no such member input/result or arithmetic and cannot choose or aggregate those
values. Source G02 rejects multiple active incoming relations before favorable-support selection.
That is source-boundary coverage, not a claim that a hierarchy consumer was implemented.

## Regression and delivery receipts

Final collection: **2,807 =2,597 retained +210 additive**. PostgreSQL collection:
**1,070 =918 retained +152 hierarchy source tests**;58 additional policy/compatibility cases
complete the210. The complete final local suite passed **2,807/2,807, zero skips**, in424.78s
(Python3.13.14 /PostgreSQL18.4, verified TLS). All1,070 real PostgreSQL cases ran. One retained
Starlette/httpx deprecation warning is unrelated to this slice.

| New test file | Cases |
| --- | ---: |
| `test_hierarchy_policy.py` | 56 |
| `test_hierarchy_compatibility.py` | 2 |
| `test_postgres_hierarchy_authentication.py` | 8 |
| `test_postgres_hierarchy_authority.py` | 64 |
| `test_postgres_hierarchy_classification.py` | 17 |
| `test_postgres_hierarchy_lifecycle.py` | 32 |
| `test_postgres_hierarchy_policy_parity.py` | 16 |
| `test_postgres_hierarchy_replay_guards.py` | 11 |
| `test_postgres_hierarchy_source.py` | 4 |
| **Total additive** | **210** |

Verified locally: lint, architecture baseline (30 invariants/11 ADR/50 linked tasks),
import boundaries (16 contexts), OpenAPI/domain export parity,22 synthetic fixtures,22/22 benchmark,
generated client contracts/typecheck,10/10 client tests and web build. Real SCRAM/TLS smoke runs both
the retained8 prior-source cases and8 hierarchy cases: **16/16 passed locally in5.52s**.
The complete suite uses real PostgreSQL
18.4 with verified TLS; no hierarchy PostgreSQL acceptance is substituted with mocks/SQLite.

The frozen318 definition digests and42 frozen runtime/migration files are checked against a baseline
fixture captured before edits. Existing2597 test identities are retained as a multiset, normalizing
only pre-existing UUID-valued parameter spellings. New contracts add31 definitions, total349.
No old test is deleted or renamed. Existing test edits only acknowledge the additive current schema
head/table count and preserve the frozen migration-prefix assertion. CI adds the hierarchy8-case
SCRAM/TLS smoke file to the existing dedicated smoke step without removing any required check.

## Changed files

Complete inventory: **46 files**. The existing-test changes are mechanical schema
expectations/frozen-prefix assertions; all2597 baseline test identities remain. Canonical ADR/
invariant wording and frozen implementations are untouched.

- [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)
- [`README.md`](../../README.md)
- [`apps/backend/README.md`](../../apps/backend/README.md)
- [`apps/backend/app/modules/preferences/hierarchy_contracts.py`](../../apps/backend/app/modules/preferences/hierarchy_contracts.py)
- [`apps/backend/app/modules/preferences/hierarchy_models.py`](../../apps/backend/app/modules/preferences/hierarchy_models.py)
- [`apps/backend/app/modules/preferences/hierarchy_resolution.py`](../../apps/backend/app/modules/preferences/hierarchy_resolution.py)
- [`apps/backend/app/modules/preferences/hierarchy_sources.py`](../../apps/backend/app/modules/preferences/hierarchy_sources.py)
- [`apps/backend/app/modules/preferences/public.py`](../../apps/backend/app/modules/preferences/public.py)
- [`apps/backend/app/persistence/models.py`](../../apps/backend/app/persistence/models.py)
- [`apps/backend/migrations/versions/0015_reviewed_hierarchy_source.py`](../../apps/backend/migrations/versions/0015_reviewed_hierarchy_source.py)
- [`apps/backend/tests/fixtures/hierarchy_source_baseline_tests.json`](../../apps/backend/tests/fixtures/hierarchy_source_baseline_tests.json)
- [`apps/backend/tests/fixtures/hierarchy_source_compatibility.json`](../../apps/backend/tests/fixtures/hierarchy_source_compatibility.json)
- [`apps/backend/tests/hierarchy_fixtures.py`](../../apps/backend/tests/hierarchy_fixtures.py)
- [`apps/backend/tests/hierarchy_postgres_fixtures.py`](../../apps/backend/tests/hierarchy_postgres_fixtures.py)
- [`apps/backend/tests/test_foundation_migration.py`](../../apps/backend/tests/test_foundation_migration.py)
- [`apps/backend/tests/test_hierarchy_compatibility.py`](../../apps/backend/tests/test_hierarchy_compatibility.py)
- [`apps/backend/tests/test_hierarchy_policy.py`](../../apps/backend/tests/test_hierarchy_policy.py)
- [`apps/backend/tests/test_postgres_exposure.py`](../../apps/backend/tests/test_postgres_exposure.py)
- [`apps/backend/tests/test_postgres_feature_exposure.py`](../../apps/backend/tests/test_postgres_feature_exposure.py)
- [`apps/backend/tests/test_postgres_feature_repeat.py`](../../apps/backend/tests/test_postgres_feature_repeat.py)
- [`apps/backend/tests/test_postgres_hierarchy_authentication.py`](../../apps/backend/tests/test_postgres_hierarchy_authentication.py)
- [`apps/backend/tests/test_postgres_hierarchy_authority.py`](../../apps/backend/tests/test_postgres_hierarchy_authority.py)
- [`apps/backend/tests/test_postgres_hierarchy_classification.py`](../../apps/backend/tests/test_postgres_hierarchy_classification.py)
- [`apps/backend/tests/test_postgres_hierarchy_lifecycle.py`](../../apps/backend/tests/test_postgres_hierarchy_lifecycle.py)
- [`apps/backend/tests/test_postgres_hierarchy_policy_parity.py`](../../apps/backend/tests/test_postgres_hierarchy_policy_parity.py)
- [`apps/backend/tests/test_postgres_hierarchy_replay_guards.py`](../../apps/backend/tests/test_postgres_hierarchy_replay_guards.py)
- [`apps/backend/tests/test_postgres_hierarchy_source.py`](../../apps/backend/tests/test_postgres_hierarchy_source.py)
- [`apps/backend/tests/test_postgres_plans.py`](../../apps/backend/tests/test_postgres_plans.py)
- [`apps/backend/tests/test_postgres_recipes.py`](../../apps/backend/tests/test_postgres_recipes.py)
- [`apps/backend/tests/test_postgres_reference_prior_authority_extra.py`](../../apps/backend/tests/test_postgres_reference_prior_authority_extra.py)
- [`apps/backend/tests/test_postgres_reference_priors.py`](../../apps/backend/tests/test_postgres_reference_priors.py)
- [`apps/backend/tests/test_postgres_retail.py`](../../apps/backend/tests/test_postgres_retail.py)
- [`apps/backend/tests/test_postgres_target_affinity.py`](../../apps/backend/tests/test_postgres_target_affinity.py)
- [`apps/backend/tests/test_postgres_validation.py`](../../apps/backend/tests/test_postgres_validation.py)
- [`apps/backend/tests/test_prior_shrinkage.py`](../../apps/backend/tests/test_prior_shrinkage.py)
- [`apps/backend/tests/test_target_affinity.py`](../../apps/backend/tests/test_target_affinity.py)
- [`docs/product/BACKLOG.md`](../../docs/product/BACKLOG.md)
- [`docs/product/FOUNDATION_STATUS.md`](../../docs/product/FOUNDATION_STATUS.md)
- [`docs/product/HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_DESIGN.md`](../../docs/product/HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_DESIGN.md)
- [`docs/product/HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_IMPLEMENTATION_EVIDENCE.md`](../../docs/product/HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_IMPLEMENTATION_EVIDENCE.md)
- [`docs/product/HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_NEUTRAL_ANCHOR_CORRECTION.md`](../../docs/product/HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_NEUTRAL_ANCHOR_CORRECTION.md)
- [`docs/product/IMPLEMENTATION_BLUEPRINT.md`](../../docs/product/IMPLEMENTATION_BLUEPRINT.md)
- [`docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md`](../../docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md)
- [`docs/product/INVARIANT_COVERAGE.md`](../../docs/product/INVARIANT_COVERAGE.md)
- [`packages/contracts/domain.schema.json`](../../packages/contracts/domain.schema.json)
- [`tools/export_domain_contracts.py`](../../tools/export_domain_contracts.py)

## Non-goals, remaining gates and deviations

No approved source-design deviation is intended. Physical responsibility is implemented with seven
tables; policies/relations share a typed revision journal. Resource limits (31-bit authored rational
components,2MiB commands,16MiB complete captures) fail rather than truncate or invent data. They do
not change frozen policy ownership or numerical semantics. Canonical overlapping culinary scopes
are already rejected by frozen046A; replay still reconstructs frozen children rather than trusting a
copied positive support result.

No pure hierarchy consumer, inherited member amount, MemberBehaviorProfile,040C,039, learned/
contextual/passive evidence, history/repeat/novelty, TasteFit, household/candidate aggregation, planner
utility, hard-safety authority, Execution or PRECOMMIT is implemented. No production relation corpus,
direction, attenuation, alias, automatic inversion, automatic RecipeVersion reconciliation or
anti-correlation type exists. No profile/cache/result snapshots are persisted. Explicit EvidenceStrength
remains ordinal and is not minted or propagated by source review.

Source readiness awaits implementation review/freeze; consumer readiness remains false.
`planner_ready=False`, `activation_ready=False`. Full040/041/046 remain PARTIAL;024/020B/021 BLOCKED;
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED. The PR must remain OPEN / NOT MERGED.

**READY FOR HIERARCHICAL PREFERENCE RELATION/POLICY SOURCE IMPLEMENTATION REVIEW — NOT MERGED**
