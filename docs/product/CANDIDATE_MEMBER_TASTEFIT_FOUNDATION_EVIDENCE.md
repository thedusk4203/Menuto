# Candidate × Member TasteFit Foundation — Implementation Evidence

Status: **IMPLEMENTATION READY FOR REVIEW / FREEZE CANDIDATE — NOT FROZEN**. No downstream gate is authorized.

## Approved entry gate

| Receipt | Exact value |
| --- | --- |
| Design | [PR #115](https://github.com/thedusk4203/Menuto/pull/115), reviewed head `676ff2aca51cf4c4870c15d830a2f8e9048d9f42` |
| Reviewed design base | `622c108d2e8fe150ada521c645a643a362baa520` |
| Formal design approval | [Comment 6461639717](https://github.com/thedusk4203/Menuto/pull/115#issuecomment-6461639717) |
| Pre-merge verification | OPEN / MERGEABLE; exactly one commit, six Markdown files; exact-head CI40635909745 SUCCESS; no unresolved review threads/blocking review |
| Actual design merge / implementation base | `89320203d1f64c274585cbcee0d5cef9045eacd1` |
| Merged tree | `60ce863425e3cbe4d8b6af5ba40cf47489de8185`, identical to the reviewed design head; parents are the reviewed base/head |
| Exact post-merge push CI | [40643470453](https://github.com/thedusk4203/Menuto/actions/runs/40643470453), event=push / head=89320203…; SUCCESS, python/web SUCCESS |
| Green design-merge baseline | **3,104 passed, 0 skips**; SCRAM/TLS16/16; benchmark22/22; client10/10; exports362; schema0015 /85; no0016 |
| Implementation code head | `fd5031abfda324e09eafc6682f8858029ef190b4`; subsequent evidence/status commit is part of the review head, resolved by the implementation PR receipt |

Implementation was separately authorized only after the design merge and exact push CI succeeded.
The fresh implementation branch starts at that verified merge. The original
[approved design](CANDIDATE_MEMBER_TASTEFIT_FOUNDATION_DESIGN.md) remains the unchanged design-stage
record; this evidence records its subsequent authorization and implementation, without redesign.

## Capability and authority

This implements deterministic **conditional Candidate × Member TasteFit** under one exact supplied,
versioned, independently body-pinned interpretation policy. It returns structured target-fit rows
for one household / one canonical candidate / one explicitly selected participating member.
A SHARED subject is supported without replacing it by tracked_member_id. Other participants and
portion factors remain grounding context, not additional fit subjects or multipliers.

Supported preference kinds remain INGREDIENT / DIRECT_RECIPE / PROTEIN / METHOD / FLAVOR.
MAIN_PROTEIN is a reviewed culinary dimension used to prove a PROTEIN preference target; no sixth
preference kind is added. Positive base targets are canonical recipe/selected ingredients/reviewed
positive terms, before policy filtering. Exact diagnostic probes cannot trim that set or expand
frozen feature coverage. ABSENT / UNRESOLVED / REVIEWED_NONE / DIMENSION_NOT_CAPTURED /
POLICY_TARGET_NOT_ADMITTED stay distinct from available zero.

Policy is **EXPLICIT_INTERPRETATION_INPUT_ONLY**, never globally current/default/published or
production-selected policy. There is no shipped numeric policy, hidden registry, seed, environment
selection, fixture fallback, shared utility, ranking or HTTP endpoint. The finite map keys include
kind / selected source mode / semantic state / full source coordinate / canonical rational.
New fit LIKE is positive, DISLIKE negative, NEUTRAL zero; NO_DECLARATION remains distinct.
Raw frozen affinity signs/neutral coordinates are not reinterpreted. No new coefficients exist.

Scoped values retain complete household/member/candidate/target/policy identity. Equal amounts
under different descriptors have no comparison or aggregation operation. Shrinkage provenance stays
in frozen child/result identity; it is not added to frozen coordinate identity. A valid scoped
numeric equality is not ranking, cross-target transfer or planner utility comparability.

## Ownership and interface inventory

All module paths below are under `apps/backend/app/modules/`.

| Module | Implemented responsibility |
| --- | --- |
| preferences/tastefit_contracts.py | Immutable member interpretation/capture plans, source bundle, views and nonsecret owner frames; full frozen policy bodies/pins and typed owner facts |
| preferences/tastefit_sources.py | Read-only frozen owner capture, hierarchy-selected parent discovery, exact single-target child inputs and same-member-cut capture; no publication or connection creation |
| preferences/tastefit_public.py | `capture_tastefit_member_sources(sessions, plan, *, actor_user_id)` and pure `replay_tastefit_member_sources(bundle)`; no candidate fit calculation |
| planning/tastefit_contracts.py | Request/policy, target proofs, source/subject/result, mapping and scoped fit contracts; immutable, extra-forbid and recursively reparsed |
| planning/tastefit_capture.py | Fresh canonical projection, member participation and owner-session coordination; one caller-owned member session plus optional dedicated prior/hierarchy sessions |
| planning/tastefit.py | Pure complete replay, canonical target proof, categorical source selection, exact finite lookup and semantic validation; zero DB/network/filesystem/live-clock/policy-environment/cache I/O |
| planning/tastefit_public.py | `capture_candidate_member_tastefit_sources`, `derive_candidate_member_tastefit`, `validate_candidate_member_tastefit`; capture import is lazy |

Planning consumes only the new immutable Preferences companion and its public replay/capture seam.
The exact-module import allowlist applies only to the three named Planning TasteFit modules.
Private prior/profile/hierarchy imports from Planning remain prohibited. New transport and pure
core guards reject runtime/I/O/learning/history/utility imports. Existing validation/Learning rules
and frozen pure-core allowlists are unchanged; negative architecture tests exercise those denials.

## Source capture, replay and precedence

Canonical capture re-grounds through frozen019C/projection/046A and generates the actual fresh
projection fingerprint after capture; an old projection fingerprint cannot be supplied as authority.
The existing expected grounding pin still applies. Offline consumption replays complete retained
sources and never recertifies an old result as a new database capture.

Caller-owned sessions are clean read-only REPEATABLE READ/SERIALIZABLE. No connection creation,
commit, rollback, SET ROLE or SESSION AUTHORIZATION occurs in the production adapter. Configured
endpoint/database plus actual nonsecret DB/session identity must agree. Frames retain trusted
requesting actor and each owner's actual read interval. Member ledgers share their complete
canonical body apart from captured_at/declared normalization; each protected owner retains its
complete journal/frontier on its own cut. Different clocks/frontiers are legal. No global MVCC,
historical frontier, simultaneous liveness, origin or current-permission claim follows from replay.

The actual disposable PostgreSQL tests use **separate** hierarchy and prior admin/curator/reader
roles, separate root-specific enrollment/capabilities and real SCRAM/TLS. Hierarchy's frozen SQL
rejects prior-role authority; the source coordinator does not relax that trust separation.

Current member RETRACTED always suppresses fit. DECLARED chooses authored RAW_EXPLICIT or
EXACT_TARGET_EFFECTIVE. UNDECLARED chooses NO_EVIDENCE / PRIOR_ONLY / ONE_HOP_INHERITED.
Unavailable selected evidence never switches branches. Captured coexisting views are retained
NOT_SELECTED; no max/sum/average/strongest/recency/favorable-parent rule exists. 040C still transfers
mapped explicit only, with one eligible parent and no recursion/aggregation. Parent-only inputs
stay lineage, not candidate positives. A valid other-version/path DIRECT_RECIPE destination stays
retained as INHERITED_DESTINATION_CONTEXT_MISMATCH; a forged binding or immutable body rejects.
EvidenceStrength is lineage only; no probability, numeric multiplier, extra threshold or inherited
strength is created. Prior/inherited negative fit cannot mint a direct dislike declaration.
Direct DISLIKE remains a member soft signal even when fit mapping is missing, never a safety veto.

Every supplied child is reparsed/recomputed, including unselected optional children. Duplicate
sets, detached targets/parents, incoherent member/immutable facts, source splicing, unsupported
policy pins and tampered caches reject. Semantic validation compares the complete freshly derived
result, not hash equality or Pydantic construction alone, and returns the freshly recomputed object.
Fingerprints are domain-separated canonical identities covering complete retained policy/source/
lineage/frames/history and all non-authority literals, excluding only the hash currently calculated.
Hidden retained history can change source/result identity while available target values stay equal.

## Persistence, regression and export compatibility

**ZERO NEW PERSISTENCE.** Schema remains **0015 /85 domain tables** (86 including alembic_version).
No0016, TasteFit table/cache/profile/matrix/policy registry, production default/seed/row or grant.
All128 pre-existing runtime/migration files are byte-pinned in
[tastefit_compatibility.json](../../apps/backend/tests/fixtures/tastefit_compatibility.json).
Frozen040A/B/C, PR100, prior/hierarchy SOURCE,019C,046A/projection and0001–0015 are unchanged.

Exports are **384 = 362 retained +22 additive definitions**. Every old definition's normalized
schema hash is unchanged. Only three old compatibility tests' total-export count assertions change
from362 to384; their per-definition/frozen-file/baseline checks remain. All3,104 baseline identities
are retained; no old semantic test is removed or weakened. The new acceptance and compatibility
fixtures are test evidence, not production source/publication authority.

### Additive public shape inventory

| New definition | Why public |
| --- | --- |
| `CandidateMemberTasteFitDraft` | Complete replayable result and fail-closed authority literals |
| `CandidateMemberTasteFitRequest` | Canonical selectors, explicit subject and independent policy pins |
| `CandidateMemberTasteFitSources` | Complete retained multi-owner evidence envelope |
| `InheritedTasteFitSourceCoordinate` | Complete frozen inherited descriptor wrapper |
| `ProfileTasteFitSourceCoordinate` | Complete frozen member-profile descriptor wrapper |
| `RawExplicitTasteFitCoordinate` | 040B kind/unit/policy-scoped raw descriptor wrapper |
| `ScopedTargetTasteFit` | Inseparable exact-subject/target coordinate and fit rational |
| `TasteFitAmount` | Strict reduced signed unit rational component |
| `TasteFitCaptureFrame` | Nonsecret owner/session/actor/target/time capture provenance |
| `TasteFitCoordinate` | Full policy/household/member/candidate/target value identity |
| `TasteFitInterpretationPolicy` | Required conditional policy body, selections, finite maps and limits |
| `TasteFitKindPolicy` | Explicit dimension-separable capture and selection rules |
| `TasteFitMappingRow` | One exact scoped semantic source-to-fit mapping |
| `TasteFitMemberCapturePlan` | Derived destination closure with owner interpretation and recipe context |
| `TasteFitMemberInterpretationPlan` | Full frozen member policy bodies and exact source selectors/pins |
| `TasteFitMemberSourceBundle` | Owner retained raw/exact/hierarchy primitives and capture frames |
| `TasteFitMemberSourceEntry` | One typed destination/parent primitive entry |
| `TasteFitMemberTargetPlan` | Exact derived target and required capture mode |
| `TasteFitMemberView` | Recomputed frozen raw/exact/one-hop views, kept distinct |
| `TasteFitSubject` | Exact participant/candidate/version/path/grounding context identity |
| `TasteFitTargetInterpretation` | Proof, selected/unselected evidence, mapping, missingness and scoped fit |
| `TasteFitTargetProof` | Canonical membership/absence/unknown proof and all requirement references |

## Verification receipt

| Check | Actual local receipt |
| --- | --- |
| Full pytest | **3,396 passed, 0 skips**,3 warnings; 1,814.38 seconds; complete JUnit receipt checked |
| Baseline / additive | **3,104 retained +292 additive**;188 pure TasteFit,62 architecture/compatibility,42 real PostgreSQL TasteFit |
| All real PostgreSQL | **1,143 cases executed**, including all42 TasteFit PG cases;35/35 required design PG obligations covered |
| TF matrix | **TF01–TF132 mapped and executed**, including parameterized semantic branches; no collection-only PG substitutes |
| Real SCRAM/TLS | **16/16 passed**, both frozen source roots; separate actual TasteFit prior/hierarchy principals/capabilities |
| Resource preflight |14/14 focused input/pin/budget tests passed after early target-budget rejection was tightened; no malformed over-budget child is replayed |
| Participant/source-selection strengthening |4/4 focused cases passed after final test review: two legal portion contexts, tracked LIKE versus undeclared SHARED subject, a genuinely blended parent versus mapped explicit, and destination prior1/1 versus inherited1/2. Runtime unchanged; final exact-head CI reruns the whole suite. |
| Benchmark / fixtures | **22/22 scenarios**;22 synthetic fixtures unchanged and verified |
| Client / build | **10/10 client**; contracts generation check, client typecheck and web typecheck/build SUCCESS |
| Architecture / exports | Ruff,30-invariant/11-ADR baseline, import boundaries, OpenAPI/domain exports SUCCESS;51 documentation/architecture checks also passed |
| Frozen compatibility |128 old runtime/migration Git blobs unchanged; all362 old definition hashes unchanged; no0016;0015 /85 |
| Final exact-head CI | Required before final handoff; the implementation PR receipt identifies the final head/run and python/web results. This evidence does not substitute a local or earlier code-head run for that gate. |

The full local suite executed every collected case, including all source-authentication smoke tests.
The final GitHub exact-head full run is the authoritative receipt for the complete review tree,
including evidence/status. The implementation PR must remain OPEN; this is not a freeze receipt.

## TF01–TF132 concrete acceptance mapping

The [machine-readable mapping](../../apps/backend/tests/fixtures/tastefit_acceptance.json) records
all132 stable cases. All35 design PG obligations map to actual PostgreSQL tests. Parameter expansion
currently gives42 real PostgreSQL TasteFit tests; the pure/static suite is additive. The final full
run must execute every obligation without skips. The mapping itself is not a substitute for execution.

| Case | Design layer | Concrete test names (apps/backend/tests/) |
| --- | --- | --- |
| TF01 | PG | `test_postgres_candidate_member_tastefit.py::test_tf01_real_canonical_capture_derive_validate_one_subject` |
| TF02 | PG | `test_postgres_candidate_member_tastefit.py::test_tf02_shared_subject_is_not_replaced_by_tracked_member` |
| TF03 | PG | `test_postgres_candidate_member_tastefit.py::test_tf03_unauthorized_actor_fails_before_preferences_read` |
| TF04 | PG | `test_postgres_candidate_member_tastefit.py::test_tf04_canonical_member_absent_from_candidate_not_added` |
| TF05 | PG | `test_postgres_candidate_member_tastefit.py::test_tf05_foreign_household_member_cannot_be_subject` |
| TF06 | PG | `test_postgres_candidate_member_tastefit.py::test_tf06_expected_grounding_pin_rejects_fresh_substitution` |
| TF07 | P | `test_candidate_member_tastefit.py::test_tf07_projection_fingerprint_tamper_rehashed_outer_rejects` |
| TF08 | P | `test_candidate_member_tastefit.py::test_tf08_other_recipe_version_cannot_reuse_subject` |
| TF09 | P | `test_candidate_member_tastefit.py::test_tf09_other_authored_path_cannot_reuse_old_projection` |
| TF10 | P | `test_candidate_member_tastefit.py::test_tf10_noncanonical_subject_selectors_reject` |
| TF11 | PG | `test_postgres_candidate_member_tastefit.py::test_tf11_actor_and_member_are_distinct_authenticated_read_subjects` |
| TF12 | PG | `test_postgres_candidate_member_tastefit.py::test_tf12_fresh_projection_identity_not_old_fp_pin` |
| TF13 | P | `test_candidate_member_tastefit.py::test_tf13_direct_recipe_exact_identity_retains_outer_version` |
| TF14 | PG | `test_postgres_candidate_member_tastefit.py::test_tf14_selected_substitution_only_original_ingredient_absent` |
| TF15 | PG | `test_postgres_candidate_member_tastefit.py::test_tf15_main_protein_is_reviewed_exact_path_not_mass` |
| TF16 | P | `test_candidate_member_tastefit.py::test_tf16_method_child_path_none_outer_path_retained` |
| TF17 | PG | `test_postgres_candidate_member_tastefit.py::test_tf17_flavor_admission_is_exact_reviewed_finite_term` |
| TF18 | P | `test_candidate_member_tastefit.py::test_tf18_proven_but_disabled_kind_has_no_fit` |
| TF19 | P | `test_candidate_member_tastefit.py::test_tf19_no_sixth_preference_kind` |
| TF20 | PG | `test_postgres_candidate_member_tastefit.py::test_tf20_nonselected_probes_absent_nonexistent_identity_fails` |
| TF21 | P | `test_candidate_member_tastefit.py::test_tf21_exact_unresolved_feature_reason_preserved` |
| TF22 | P | `test_candidate_member_tastefit.py::test_tf22_reviewed_none_is_finite_not_blanket_absence` |
| TF23 | P | `test_candidate_member_tastefit.py::test_tf23_inferred_membership_flags_reject` |
| TF24 | P | `test_candidate_member_tastefit.py::test_tf24_partial_positive_and_unknown_probe_remain_separate` |
| TF25 | P | `test_candidate_member_tastefit.py::test_tf25_uncaptured_dimension_is_not_zero` |
| TF26 | P | `test_candidate_member_tastefit.py::test_tf26_duplicate_ingredient_target_has_all_requirement_proofs` |
| TF27 | P | `test_candidate_member_tastefit.py::test_tf27_probe_neither_trims_base_nor_expands_feature_cut` |
| TF28 | PG | `test_postgres_candidate_member_tastefit.py::test_tf28_catalog_support_correction_stales_reviewed_main_protein` |
| TF29 | P | `test_candidate_member_tastefit.py::test_tf29_raw_like_has_one_exact_policy_mapping_per_target` |
| TF30 | P | `test_candidate_member_tastefit.py::test_tf30_dislike_is_negative_soft_signal_not_safety` |
| TF31 | P | `test_candidate_member_tastefit.py::test_tf31_nonzero_raw_neutral_requires_explicit_mapping` |
| TF32 | P | `test_candidate_member_tastefit.py::test_tf32_undeclared_is_unavailable_not_neutral` |
| TF33 | P | `test_candidate_member_tastefit.py::test_tf33_retraction_suppresses_retained_previous_like`<br>`test_candidate_member_tastefit.py::test_tf33_tf59_policy_cannot_override_retraction_even_for_disabled_kind` |
| TF34 | P | `test_candidate_member_tastefit.py::test_tf34_available_like_zero_is_not_missing` |
| TF35 | P | `test_candidate_member_tastefit.py::test_tf35_tf36_tf37_strength_is_lineage_not_another_multiplier` |
| TF36 | P | `test_candidate_member_tastefit.py::test_tf35_tf36_tf37_strength_is_lineage_not_another_multiplier` |
| TF37 | P | `test_candidate_member_tastefit.py::test_tf35_tf36_tf37_strength_is_lineage_not_another_multiplier` |
| TF38 | P | `test_candidate_member_tastefit.py::test_tf38_prior_and_inherited_never_mint_destination_strength` |
| TF39 | P | `test_candidate_member_tastefit.py::test_tf39_caller_strength_fields_reject` |
| TF40 | PG | `test_postgres_candidate_member_tastefit.py::test_tf40_retry_history_does_not_increase_strength_or_fit` |
| TF41 | PG | `test_postgres_candidate_member_tastefit.py::test_tf41_correction_changes_fresh_head_retained_capture_replays` |
| TF42 | P | `test_candidate_member_tastefit.py::test_tf42_dislike_without_mapping_keeps_soft_signal` |
| TF43 | P | `test_candidate_member_tastefit.py::test_tf43_negative_prior_is_not_direct_dislike`<br>`test_candidate_member_tastefit.py::test_tf43_inherited_semantic_preserved_without_direct_signal_or_strength` |
| TF44 | P | `test_candidate_member_tastefit.py::test_tf44_other_participants_never_become_fit_subjects` |
| TF45 | PG | `test_postgres_candidate_member_tastefit.py::test_tf45_real_empty_prior_source_uses_frozen_explicit_only` |
| TF46 | P | `test_candidate_member_tastefit.py::test_tf46_frozen_blend_mapped_once` |
| TF47 | P | `test_candidate_member_tastefit.py::test_tf47_prior_only_cold_start_not_neutral` |
| TF48 | PG | `test_postgres_candidate_member_tastefit.py::test_tf48_real_empty_prior_selected_stays_unavailable` |
| TF49 | PG | `test_postgres_candidate_member_tastefit.py::test_tf49_prior_retraction_preserves_reason_and_explicit_only` |
| TF50 | P | `test_candidate_member_tastefit.py::test_tf50_unmapped_reference_keeps_frozen_explicit_fallback` |
| TF51 | P | `test_candidate_member_tastefit.py::test_tf51_policy_bindings_fail_before_lookup` |
| TF52 | P | `test_candidate_member_tastefit.py::test_tf52_reference_provider_binding_never_falls_back` |
| TF53 | PG | `test_postgres_candidate_member_tastefit.py::test_tf53_required_prior_permission_failure_aborts_whole_capture` |
| TF54 | P | `test_candidate_member_tastefit.py::test_tf54_effective_without_fit_mapping_does_not_use_raw` |
| TF55 | PG | `test_postgres_candidate_member_tastefit.py::test_tf55_raw_mode_needs_no_configured_global_provider` |
| TF56 | P | `test_candidate_member_tastefit.py::test_tf56_only_shrinkage_provenance_changes_full_identity` |
| TF57 | PG | `test_postgres_candidate_member_tastefit.py::test_tf57_real_reviewed_one_hop_transfer_maps_parent_explicit` |
| TF58 | P | `test_candidate_member_tastefit.py::test_tf58_destination_direct_wins_without_magnitude_comparison` |
| TF59 | P | `test_candidate_member_tastefit.py::test_tf33_tf59_policy_cannot_override_retraction_even_for_disabled_kind`<br>`test_candidate_member_tastefit.py::test_tf59_retracted_destination_wins_even_prior_and_parent` |
| TF60 | PG | `test_postgres_candidate_member_tastefit.py::test_tf60_real_parent_retraction_no_destination_prior_fallback` |
| TF61 | P | `test_candidate_member_tastefit.py::test_tf61_parent_prior_only_is_not_inherited_and_blend_is_not_operand` |
| TF62 | PG | `test_postgres_candidate_member_tastefit.py::test_tf62_real_hierarchy_unavailability_is_not_neutral` |
| TF63 | PG | `test_postgres_candidate_member_tastefit.py::test_tf63_multiple_incoming_relations_no_favorable_parent_filter` |
| TF64 | P | `test_candidate_member_tastefit.py::test_tf64_recursive_parent_result_cannot_enter_primitives` |
| TF65 | P | `test_candidate_member_tastefit.py::test_tf65_wrong_parent_target_rejects_even_matching_kind` |
| TF66 | PG | `test_postgres_candidate_member_tastefit.py::test_tf66_valid_other_recipe_context_unavailable_forged_binding_rejects` |
| TF67 | P | `test_candidate_member_tastefit.py::test_tf67_different_source_recipe_is_valid_lineage` |
| TF68 | P | `test_candidate_member_tastefit.py::test_tf68_prior_selected_inherited_not_selected` |
| TF69 | P | `test_candidate_member_tastefit.py::test_tf69_inherited_selected_even_when_prior_larger` |
| TF70 | P | `test_candidate_member_tastefit.py::test_tf70_unused_malformed_hierarchy_child_still_rejects` |
| TF71 | P | `test_candidate_member_tastefit.py::test_tf71_exact_policy_pins_and_replay_determinism` |
| TF72 | P | `test_candidate_member_tastefit.py::test_tf72_body_edit_without_independent_pin_rejects` |
| TF73 | P | `test_candidate_member_tastefit.py::test_tf73_missing_policy_never_selects_default` |
| TF74 | P | `test_candidate_member_tastefit.py::test_tf74_exact_version_only` |
| TF75 | P | `test_candidate_member_tastefit.py::test_tf75_duplicate_semantic_keys_reject` |
| TF76 | P | `test_candidate_member_tastefit.py::test_tf76_equal_value_under_unmapped_descriptor_is_not_selected` |
| TF77 | P | `test_candidate_member_tastefit.py::test_tf77_mapping_for_another_kind_never_transfers` |
| TF78 | P | `test_candidate_member_tastefit.py::test_tf78_admission_and_capture_selections_are_required` |
| TF79 | P | `test_candidate_member_tastefit.py::test_tf79_reviewed_label_is_still_conditional_input` |
| TF80 | P | `test_candidate_member_tastefit.py::test_tf80_complete_frozen_descriptors_retained` |
| TF81 | P | `test_candidate_member_tastefit.py::test_tf81_no_declaration_neutral_and_zero_have_separate_keys` |
| TF82 | P | `test_candidate_member_tastefit.py::test_tf82_exact_rational_miss_no_nearest_interpolation` |
| TF83 | P | `test_candidate_member_tastefit.py::test_tf83_sets_and_equivalent_rationals_normalize_policy_identity` |
| TF84 | P | `test_candidate_member_tastefit.py::test_tf84_semantic_choices_and_limits_cannot_be_omitted`<br>`test_candidate_member_tastefit.py::test_tf84_rational_components_strict_signed_unit_not_probability` |
| TF85 | P | `test_candidate_member_tastefit.py::test_tf85_new_coherent_body_is_another_conditional_request` |
| TF86 | P | `test_candidate_member_tastefit.py::test_tf86_authored_resource_overflow_rejects_without_partial_result` |
| TF87 | P | `test_candidate_member_tastefit.py::test_tf87_scoped_numeric_equality_requires_entire_descriptor` |
| TF88 | P | `test_candidate_member_tastefit.py::test_tf88_descriptor_semantics_reject_before_lookup`<br>`test_candidate_member_tastefit.py::test_tf88_forged_frozen_descriptor_never_enters_fit_lookup` |
| TF89 | PG | `test_postgres_candidate_member_tastefit.py::test_tf89_all_member_children_share_full_ledger_on_one_rr_cut` |
| TF90 | P | `test_candidate_member_tastefit.py::test_tf90_wrong_member_parent_rejects` |
| TF91 | P | `test_candidate_member_tastefit.py::test_tf91_wrong_household_even_with_matching_numeric_value` |
| TF92 | PG | `test_postgres_candidate_member_tastefit.py::test_tf92_independent_legal_owner_clocks_and_frontiers_not_common_mvcc` |
| TF93 | PG | `test_postgres_candidate_member_tastefit.py::test_tf93_feature_capture_after_grounding_asof_is_not_forced_historical_cut` |
| TF94 | P | `test_candidate_member_tastefit.py::test_tf94_typed_immutable_fact_conflicts_any_depth_reject`<br>`test_candidate_member_tastefit.py::test_tf94_coherently_edited_member_term_still_conflicts_with_candidate` |
| TF95 | P | `test_candidate_member_tastefit.py::test_tf95_mutable_ingredient_label_is_not_identity_conflict` |
| TF96 | PG | `test_postgres_candidate_member_tastefit.py::test_tf96_retained_all_owner_cuts_replay_after_live_corrections` |
| TF97 | PG | `test_postgres_candidate_member_tastefit.py::test_tf97_independent_hierarchy_capability_not_minted_by_prior_read` |
| TF98 | P | `test_candidate_member_tastefit.py::test_tf98_offline_origin_and_auth_claims_cannot_be_minted` |
| TF99 | PG | `test_postgres_candidate_member_tastefit.py::test_tf99_revoked_capture_cannot_reuse_old_valid_child` |
| TF100 | PG | `test_postgres_candidate_member_tastefit.py::test_tf100_rr_owner_cut_is_coherent_during_concurrent_publication` |
| TF101 | PG | `test_postgres_candidate_member_tastefit.py::test_tf101_invalid_capture_transaction_rejected_without_commit`<br>`test_postgres_candidate_member_tastefit.py::test_tf101_dirty_session_rejected_and_wrong_database_is_not_spliced`<br>`test_postgres_candidate_member_tastefit.py::test_tf101_real_wrong_database_identity_aborts_before_owner_capture` |
| TF102 | P | `test_candidate_member_tastefit.py::test_tf102_same_frontier_different_ledger_body_is_incoherent`<br>`test_candidate_member_tastefit.py::test_tf102_tf105_hidden_unrelated_ledger_history_changes_identity_not_fit` |
| TF103 | P | `test_candidate_member_tastefit.py::test_tf103_identical_serialized_sources_have_identical_semantics` |
| TF104 | P | `test_candidate_member_tastefit.py::test_tf104_new_set_order_normalizes_frozen_journals_stay_owned` |
| TF105 | P | `test_candidate_member_tastefit.py::test_tf105_frame_provenance_changes_identity_without_fit`<br>`test_candidate_member_tastefit.py::test_tf102_tf105_hidden_unrelated_ledger_history_changes_identity_not_fit` |
| TF106 | P | `test_candidate_member_tastefit.py::test_tf106_rehashed_cached_projection_does_not_override_sources` |
| TF107 | P | `test_candidate_member_tastefit.py::test_tf107_cached_explicit_strength_cannot_override_ledger` |
| TF108 | P | `test_candidate_member_tastefit.py::test_tf108_cached_blend_rehash_rejects` |
| TF109 | P | `test_candidate_member_tastefit.py::test_tf109_cached_transfer_arithmetic_rehash_rejects` |
| TF110 | P | `test_candidate_member_tastefit.py::test_tf110_all_semantic_output_fields_compared_not_only_hash` |
| TF111 | P | `test_candidate_member_tastefit.py::test_tf111_model_construct_nested_policy_is_untrusted` |
| TF112 | P | `test_candidate_member_tastefit.py::test_tf112_model_copy_bypass_reparsed` |
| TF113 | P | `test_candidate_member_tastefit.py::test_tf113_scoped_descriptor_forgery_rejects` |
| TF114 | P | `test_candidate_member_tastefit.py::test_tf114_pure_derivation_validation_zero_io`<br>`test_tastefit_architecture.py::test_tf114_tf117_tf121_tf122_pure_core_rejects_io_learning_history_utility`<br>`test_tastefit_architecture.py::test_tf114_member_replay_cannot_import_io_or_frozen_io_facade` |
| TF115 | P | `test_candidate_member_tastefit.py::test_tf115_hashes_bind_complete_bodies_without_self_recursion` |
| TF116 | P | `test_candidate_member_tastefit.py::test_tf116_validator_returns_new_recomputed_result` |
| TF117 | B/P | `test_candidate_member_tastefit.py::test_tf117_learning_events_are_not_inputs`<br>`test_tastefit_architecture.py::test_tf114_tf117_tf121_tf122_pure_core_rejects_io_learning_history_utility` |
| TF118 | P | `test_candidate_member_tastefit.py::test_tf118_behavioral_events_cannot_become_like` |
| TF119 | P | `test_candidate_member_tastefit.py::test_tf119_operational_friction_is_not_taste` |
| TF120 | P | `test_candidate_member_tastefit.py::test_tf120_passive_forced_assumptions_reject` |
| TF121 | B/P | `test_candidate_member_tastefit.py::test_tf121_repeat_chain_cannot_be_input_or_multiplier`<br>`test_tastefit_architecture.py::test_tf114_tf117_tf121_tf122_pure_core_rejects_io_learning_history_utility` |
| TF122 | B/P | `test_candidate_member_tastefit.py::test_tf122_no_history_or_novelty_substitution`<br>`test_tastefit_architecture.py::test_tf114_tf117_tf121_tf122_pure_core_rejects_io_learning_history_utility` |
| TF123 | P | `test_candidate_member_tastefit.py::test_tf123_favorable_fit_cannot_override_unsafe_grounding` |
| TF124 | P | `test_candidate_member_tastefit.py::test_tf124_no_feasibility_or_hidden_cost_weight` |
| TF125 | P | `test_candidate_member_tastefit.py::test_tf125_main_protein_remains_preference_protein` |
| TF126 | P | `test_candidate_member_tastefit.py::test_tf126_no_candidate_comparison_scalar_or_ranking` |
| TF127 | P | `test_candidate_member_tastefit.py::test_tf127_no_household_reducer_or_other_member_copy` |
| TF128 | P | `test_candidate_member_tastefit.py::test_tf128_non_authority_literals_cannot_be_promoted` |
| TF129 | PG | `test_postgres_candidate_member_tastefit.py::test_tf129_tf132_read_only_no_rows_frontiers_schema_or_production_defaults` |
| TF130 | B | `test_tastefit_architecture.py::test_tf130_frozen_owner_runtime_and_migrations_byte_exact`<br>`test_tastefit_architecture.py::test_tf130_planning_cannot_import_private_preferences_even_from_new_modules`<br>`test_tastefit_architecture.py::test_tf130_companion_allowlist_does_not_extend_other_planning_modules`<br>`test_tastefit_architecture.py::test_tf130_validation_learning_contract_only_rules_unchanged`<br>`test_tastefit_architecture.py::test_tf130_exact_approved_companion_imports_work`<br>`test_tastefit_architecture.py::test_tf130_transport_accepts_only_immutable_owner_shapes` |
| TF131 | B | `test_tastefit_architecture.py::test_tf131_all3104_baseline_test_identities_retained` |
| TF132 | PG/B | `test_postgres_candidate_member_tastefit.py::test_tf129_tf132_read_only_no_rows_frontiers_schema_or_production_defaults`<br>`test_tastefit_architecture.py::test_tf132_all362_old_definitions_unchanged_exact_additive_export_set` |

## Remaining blockers and stop boundary

| Work | Status |
| --- | --- |
| Candidate × Member TasteFit | IMPLEMENTATION READY FOR REVIEW / FREEZE CANDIDATE; NOT FROZEN; no milestone suffix assigned |
| MTR-040 / issue41 | COMPLETE / CLOSED — COMPLETED; frozen semantics unchanged |
| Candidate feature projection | FROZEN, unchanged |
| MTR-039 | OPEN; no new learned/contextual/passive/behavioral-event admission |
| Full MTR-041 /046 | PARTIAL /PARTIAL; local repeat is not global history/novelty |
| MTR-024 /020B /021 | BLOCKED; no composition/utility/EXPLOIT/EXPLORE/portfolio/activation claim |
| Execution /PRECOMMIT | NOT STARTED /FAIL-CLOSED |
| Shared-member reducer, ranking, planner activation | NOT AUTHORIZED /NOT PERFORMED |
| Canonical/default/shared TasteFit policy publication | NOT PROVIDED /NOT AUTHORIZED |

No learned/cooked/consumed/passive/friction/forced-choice signals, repeat/novelty/history, safety,
nutrition, procurement or SPEND_LIMIT values become TasteFit operands or durable preference truth.
No favorable fit can rescue failed grounding or certify hard feasibility. planner_ready=False and
activation_ready=False. This task stops with a separate implementation PR left OPEN; no auto-merge,
self-freeze, parent-issue closure or next-milestone selection is authorized.
