# MTR-040C — One-hop Hierarchical Member Preference Consumer Foundation

Status: **MTR-040C IMPLEMENTED — NOT FROZEN**.
**ARCHITECTURE APPROVED. IMPLEMENTATION REVIEW / FREEZE REQUIRED.**
Prepared 2026-10-27. The user authorizes this bounded implementation and opening its PR,
explicitly **not merging** it. No downstream implementation or parent-issue closure is authorized.

## Canonical basis

- Exact implementation base: `b591464e3ca495909851217141f96a55faaa35cc`, PR #106 merge.
- `origin/main` fetched and verified at that exact SHA before branch creation.
- Architecture: [approved consumer design](MTR_040C_ONE_HOP_HIERARCHICAL_MEMBER_PREFERENCE_CONSUMER_DESIGN.md), HC01–HC81, plus the user's mandatory HC81 clarification across every nested explicit/reference/hierarchy identity cut.
- Frozen SOURCE: `ee8a4de1b1c71ccbd56ea565e111718660711fa8`, [freeze receipt](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_FREEZE_RECEIPT.md).
- Retained baseline:2,807 test identities,349 exported definitions, Alembic0015 /85 domain tables.
- Implementation/final-head/CI delivery identities are recorded in the GitHub PR receipt; this file does not claim a self-referential head SHA.

## Implemented boundary

`derive_one_hop_hierarchical_member_preference(subject)` is one lazy public facade over two additive
Preferences modules. It reparses complete primitive inputs and recomputes frozen040B/PR #100 results
and the frozen hierarchy resolver. No frozen child's unavailable fields or semantics are extended.

Parent and destination must have identical complete member-ledger projections, sorted by declaration
sequence and vocabulary ID; only snapshot `captured_at` is excluded from that equivalence projection.
Original capture clocks, complete member histories and manifests remain in the result/fingerprint.
Household/member/typed-target checks and immutable repeated owner facts are validated before outcomes.
The immutable check recursively visits actual typed `AffinityFeatureTermFact`, `RecipeFact` and
`RecipeVersionSnapshot` values across both complete PR #100 inputs and the hierarchy cut, including
all publication/context preimages. It compares full canonical bodies keyed by fact type plus exact ID.
Mutable ingredient names are excluded from immutable identity equivalence and cannot create aliases.

Destination RETRACTED suppresses inheritance, followed by every DECLARED state including NEUTRAL
and explicit zero. Missing/ambiguous hierarchy preserves exact source diagnostics. An eligible unique
relation plus UNDECLARED destination requires a complete parent; omitted required input is an error.
Optional supplied children still validate under suppression or unavailable source.

Only current parent mapped-explicit lineage can propagate. Prior-only, undeclared and retracted
parent states have separate unavailable reasons. Parent blended effective values, prior contributions,
prior-only values and earlier inherited outputs never enter transfer arithmetic. Valid but different
full explicit/compatibility policies give INCOMPATIBLE_COORDINATE; forged policy bodies fail validation.
Destination policies remain independently valid and do not need to match the hierarchy publication.

The frozen semantic lookup checks raw040B `expected_source_amount` separately from the mapped PR #100
descriptor. Raw and mapped scalars are never equated. Semantic state is never inferred from sign.
The authored output maps to `INHERITED_MEMBER_PREFERENCE`, then multiplies the authored positive
attenuation using exact rational arithmetic. Full `HierarchyTransferPolicy.fingerprint()` supplies
coordinate identity; prior/shrinkage provenance does not. Canonical31-bit factors produce bounded
exact128-bit components, with available zero exactly0/1 and no rounding/clipping/defaults.

AVAILABLE, SUPPRESSED and UNAVAILABLE are discriminated branches. Only AVAILABLE has inherited
value/trace. The destination exact-target component stays separate; no blend or final scalar chooser
is provided. Outer owner/targets plus trace provider/policy/relation stream/revision/context supply
exact bindings; scoped numeric equality does not imply target identity, aggregation or planner utility.

Root deserialization reparses full primitives, recomputes every child/field and checks the new-domain
full-input fingerprint. Cached matching checksums are insufficient. Cached inherited descriptors are
also checked against the recomputed published coordinate **before new transfer multiplication**.
Trace parsing itself performs no transfer arithmetic on untrusted cached operands.

## Verification receipt

| Check | Local result |
| --- | --- |
| Initial local full Python/PostgreSQL regression | **2,975 passed**, one frozen export-namespace check failed; corrected without changing that frozen test; no errors/skips |
| Real PostgreSQL regression | **1,070 passed**, including retained authority, migration and support replay cases |
| Corrected frozen export / compatibility retry | **86 passed**; bundle `$id` retained at frozen foundation:20, all349 old definitions unchanged |
| Final test inventory | **2,978 =2,807 retained +171 additive**; retained identities checked mechanically |
| New consumer/interface replay suite |166 passed, then the final optional-parent boundary and additional distinct-target equality case passed in focused checks;3 new compatibility checks also passed |
| HC76 later-published policy replay | **1 passed** with coherent full journal after the member capture; runtime unchanged |
| SCRAM/TLS smoke | **16/16** real PostgreSQL tests |
| Architecture/docs/import boundaries | PASS;30 invariants,11 ADRs,50 linked tasks,16 contexts |
| OpenAPI/domain exports/synthetic fixtures | PASS;358 domain definitions,22 fixture scenarios |
| Synthetic benchmark | **22/22** |
| Client/typecheck/web build | **10/10** client; contract generation/typecheck/build PASS |
| Schema/frozen compatibility | **0015 /85 domain tables**,349 old definitions/123 runtime-migration files/public prefix retained |

The local full run collected before the final optional-parent omission checks and one additional
HC60 distinct-target test were finalized. Those final boundary checks passed separately; the exact
final-head GitHub CI runs the complete2,978-test inventory again. Its SHA/run/job receipt is recorded
in the PR delivery record. Local smoke/full tests use a disposable loopback TLS PostgreSQL cluster;
no production database is accessed. Focused tests exercise actual frozen child/source replay,
including Catalog partial coverage/corrections and METHOD/FLAVOR/MAIN_PROTEIN pinned contexts.

## Compatibility and production-content proof

New exports are additive: **349 retained +9 new =358 definitions**. The compatibility fixture pins
all349 baseline definition digests,123 pre-existing runtime/migration Python files and the exact
pre-existing public-facade prefix to canonical base b591464. All2,807 old test identities are retained.
The only existing test edit mechanically updates the total export count349→358; its retained318
definition checks, frozen file checks and prior baseline test identities remain unchanged.

Migrations0001–0015 remain byte-identical; no0016. There are no model/table/SQL/seed changes,
no production hierarchy rows/default coefficients/providers/grants and no production database writes.
All new numeric policies, journals and publications live only in clearly synthetic test fixtures.
The existing real-PG migration checks still require0015,85 domain tables and empty seven hierarchy
source tables after migration. No production row inventory is claimed from access to a live database.

Zero-IO tests seal filesystem, network, engine/session, clock and randomness surfaces while the actual
public derivation and result replay still succeed. Static import checks independently prevent IO and
downstream dependencies in the two new modules. No capture helper, repository, cache, HTTP endpoint,
persistence or generic graph engine is introduced.

## Acceptance mapping

Every HC obligation below maps to concrete public-interface/result-replay tests. Parameterized tests
cover additional target kinds, invalid forms and lifecycle states; HC IDs are obligations, not a claim
that exactly81 tests were added. Frozen SOURCE H01–H09, PR #100,040A/B, reference-prior authority and
hierarchy PostgreSQL/SCRAM/TLS regression suites remain present and run in the full suite.

| Obligation | Concrete tests (all in apps/backend/tests) |
| --- | --- |
| HC01 | [test_hierarchical_affinity.py::test_hc01_hc42_hc69_all25_exact_typed_directions](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC02 | [test_hierarchical_affinity.py::test_hc02_exact_target_child_rule](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC03 | [test_hierarchical_affinity.py::test_hc03_exact_hierarchy_destination_request](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC04 | [test_hierarchical_affinity.py::test_hc04_foreign_member_rejected](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC05 | [test_hierarchical_affinity.py::test_hc05_missing_required_parent_fails](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC06 | [test_hierarchical_affinity.py::test_hc06_hc21_optional_parent_for_suppression](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity_source_replay.py::test_hc06_hc36_no_relation_and_tombstone_are_distinct](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC07 | [test_hierarchical_affinity.py::test_hc07_malformed_optional_parent_fails_before_suppression](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC08 | [test_hierarchical_affinity.py::test_hc08_parent_exact_target_checked_before_suppression](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC09 | [test_hierarchical_affinity.py::test_hc09_untrusted_input_extras_rejected](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC10 | [test_hierarchical_affinity.py::test_hc10_constructed_and_dictionary_inputs_revalidate](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC11 | [test_hierarchical_affinity.py::test_hc11_hc14_incoherent_member_frontiers_fail](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC12 | [test_hierarchical_affinity.py::test_hc12_same_frontier_changed_ledger_fails](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC13 | [test_hierarchical_affinity.py::test_hc13_hc16_hc74_different_observation_clocks_preserved](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC14 | [test_hierarchical_affinity.py::test_hc11_hc14_incoherent_member_frontiers_fail](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC15 | [test_hierarchical_affinity.py::test_hc15_member_ledger_order_is_canonical_only_for_equivalence](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC16 | [test_hierarchical_affinity.py::test_hc13_hc16_hc74_different_observation_clocks_preserved](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC17 | [test_hierarchical_affinity.py::test_hc17_hc18_hc19_destination_declaration_wins](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC18 | [test_hierarchical_affinity.py::test_hc17_hc18_hc19_destination_declaration_wins](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC19 | [test_hierarchical_affinity.py::test_hc17_hc18_hc19_destination_declaration_wins](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity.py::test_hc19_hc20_nonzero_neutral_and_explicit_zero_suppress](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC20 | [test_hierarchical_affinity.py::test_hc19_hc20_nonzero_neutral_and_explicit_zero_suppress](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC21 | [test_hierarchical_affinity.py::test_hc06_hc21_optional_parent_for_suppression](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC22 | [test_hierarchical_affinity_source_replay.py::test_hc22_direct_suppression_keeps_ambiguous_source_diagnostics](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC23 | [test_hierarchical_affinity_source_replay.py::test_hc23_hc73_invalid_source_not_masked_by_suppression](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC24 | [test_hierarchical_affinity.py::test_hc24_destination_prior_keeps_separate_component](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC25 | [test_hierarchical_affinity.py::test_hc25_hc48_mapping_then_attenuation](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC26 | [test_hierarchical_affinity.py::test_hc26_hc31_hc32_hc65_prior_and_shrinkage_do_not_enter_transfer](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC27 | [test_hierarchical_affinity.py::test_hc27_hc28_hc29_parent_no_explicit_fallback](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC28 | [test_hierarchical_affinity.py::test_hc27_hc28_hc29_parent_no_explicit_fallback](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC29 | [test_hierarchical_affinity.py::test_hc27_hc28_hc29_parent_no_explicit_fallback](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC30 | [test_hierarchical_affinity.py::test_hc30_inherited_result_is_not_parent_input](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC31 | [test_hierarchical_affinity.py::test_hc26_hc31_hc32_hc65_prior_and_shrinkage_do_not_enter_transfer](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC32 | [test_hierarchical_affinity.py::test_hc26_hc31_hc32_hc65_prior_and_shrinkage_do_not_enter_transfer](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC33 | [test_hierarchical_affinity.py::test_hc33_prior_cannot_mint_explicit_eligibility](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC34 | [test_hierarchical_affinity.py::test_hc34_hc80_non_authority_flags_and_member_lineage](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC35 | [test_hierarchical_affinity_source_replay.py::test_hc35_policy_states_preserved](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC36 | [test_hierarchical_affinity_source_replay.py::test_hc06_hc36_no_relation_and_tombstone_are_distinct](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC37 | [test_hierarchical_affinity_source_replay.py::test_hc37_hc39_no_favorable_parent_or_diamond_choice](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC38 | [test_hierarchical_affinity_source_replay.py::test_hc38_unusable_competing_support_is_still_ambiguous](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC39 | [test_hierarchical_affinity_source_replay.py::test_hc37_hc39_no_favorable_parent_or_diamond_choice](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py)<br>[test_hierarchical_affinity_source_replay.py::test_hc39_same_source_different_recipe_contexts_not_deduplicated](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC40 | [test_hierarchical_affinity_source_replay.py::test_hc40_cycle_rejected_without_traversal_or_inverse_inference](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC41 | [test_hierarchical_affinity_source_replay.py::test_hc41_hc44_catalog_partial_positive_and_fresh_correction](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC42 | [test_hierarchical_affinity.py::test_hc01_hc42_hc69_all25_exact_typed_directions](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity_source_replay.py::test_hc42_hc43_exact_recipe_classification_context](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC43 | [test_hierarchical_affinity_source_replay.py::test_hc42_hc43_exact_recipe_classification_context](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC44 | [test_hierarchical_affinity_source_replay.py::test_hc41_hc44_catalog_partial_positive_and_fresh_correction](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py)<br>[test_hierarchical_affinity_source_replay.py::test_hc44_hc66_policy_replacement_requires_fresh_relation_pin](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC45 | [test_hierarchical_affinity.py::test_hc45_forged_published_parent_descriptor_rejected](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC46 | [test_hierarchical_affinity.py::test_hc46_hc47_valid_but_different_full_parent_policy_unavailable](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC47 | [test_hierarchical_affinity.py::test_hc46_hc47_valid_but_different_full_parent_policy_unavailable](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC48 | [test_hierarchical_affinity.py::test_hc25_hc48_mapping_then_attenuation](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC49 | [test_hierarchical_affinity_source_replay.py::test_hc49_hc50_hc55_hc56_forged_published_policy_fails_after_rehash](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC50 | [test_hierarchical_affinity_source_replay.py::test_hc49_hc50_hc55_hc56_forged_published_policy_fails_after_rehash](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC51 | [test_hierarchical_affinity.py::test_hc51_hc52_hc53_semantics_not_raw_sign](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC52 | [test_hierarchical_affinity.py::test_hc51_hc52_hc53_semantics_not_raw_sign](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC53 | [test_hierarchical_affinity.py::test_hc51_hc52_hc53_semantics_not_raw_sign](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC54 | [test_hierarchical_affinity.py::test_hc54_missing_semantic_row_has_no_implicit_zero](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC55 | [test_hierarchical_affinity_source_replay.py::test_hc49_hc50_hc55_hc56_forged_published_policy_fails_after_rehash](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC56 | [test_hierarchical_affinity_source_replay.py::test_hc49_hc50_hc55_hc56_forged_published_policy_fails_after_rehash](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC57 | [test_hierarchical_affinity.py::test_hc57_hc58_forged_descriptor_rejects_before_transfer_math](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity.py::test_hc57_all_cached_descriptors_forged_reject_before_transfer_math](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC58 | [test_hierarchical_affinity.py::test_hc57_hc58_forged_descriptor_rejects_before_transfer_math](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity.py::test_hc58_stripping_descriptor_or_naked_number_never_available](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC59 | [test_hierarchical_affinity.py::test_hc59_hc60_hc67_coordinate_full_policy_and_scoped_equality](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC60 | [test_hierarchical_affinity.py::test_hc59_hc60_hc67_coordinate_full_policy_and_scoped_equality](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity.py::test_hc60_hc69_equal_scoped_numbers_do_not_imply_equal_exact_targets](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC61 | [test_hierarchical_affinity.py::test_hc61_hc63_hc64_exact_product_near_authored_bound](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC62 | [test_hierarchical_affinity.py::test_hc62_hc63_hc64_noncanonical_or_oversized_derived_amount_rejected](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity_source_replay.py::test_hc62_invalid_authored_attenuation_rejected](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC63 | [test_hierarchical_affinity.py::test_hc61_hc63_hc64_exact_product_near_authored_bound](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity.py::test_hc62_hc63_hc64_noncanonical_or_oversized_derived_amount_rejected](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC64 | [test_hierarchical_affinity.py::test_hc61_hc63_hc64_exact_product_near_authored_bound](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity.py::test_hc62_hc63_hc64_noncanonical_or_oversized_derived_amount_rejected](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC65 | [test_hierarchical_affinity.py::test_hc26_hc31_hc32_hc65_prior_and_shrinkage_do_not_enter_transfer](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC66 | [test_hierarchical_affinity_source_replay.py::test_hc44_hc66_policy_replacement_requires_fresh_relation_pin](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC67 | [test_hierarchical_affinity.py::test_hc59_hc60_hc67_coordinate_full_policy_and_scoped_equality](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC68 | [test_hierarchical_affinity.py::test_hc68_repeated_member_history_does_not_increase_strength_or_magnitude](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity_source_replay.py::test_hc68_review_history_does_not_amplify_or_mint_strength](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC69 | [test_hierarchical_affinity.py::test_hc01_hc42_hc69_all25_exact_typed_directions](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity.py::test_hc60_hc69_equal_scoped_numbers_do_not_imply_equal_exact_targets](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC70 | [test_hierarchical_affinity.py::test_hc70_edited_cached_children_rejected_even_outer_rehashed](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity.py::test_hc70_valid_replayed_child_cannot_be_transplanted](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC71 | [test_hierarchical_affinity_source_replay.py::test_hc71_edited_cached_hierarchy_rejects_even_rehashed](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC72 | [test_hierarchical_affinity.py::test_hc72_rehashed_trace_tampering_rejects](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC73 | [test_hierarchical_affinity_source_replay.py::test_hc23_hc73_invalid_source_not_masked_by_suppression](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC74 | [test_hierarchical_affinity.py::test_hc13_hc16_hc74_different_observation_clocks_preserved](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity.py::test_hc74_hc75_hc76_full_input_replay_not_visible_amount_hash](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC75 | [test_hierarchical_affinity.py::test_hc74_hc75_hc76_full_input_replay_not_visible_amount_hash](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC76 | [test_hierarchical_affinity.py::test_hc74_hc75_hc76_full_input_replay_not_visible_amount_hash](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity_source_replay.py::test_hc76_policy_published_after_member_capture_is_versioned_replay](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| HC77 | [test_hierarchical_affinity.py::test_hc77_pure_entry_and_replay_without_io_clock_randomness](../../apps/backend/tests/test_hierarchical_affinity.py) |
| HC78 | [test_hierarchical_affinity_compatibility.py::test_hc78_hc79_all349_definitions_and_123_frozen_runtime_files_retained](../../apps/backend/tests/test_hierarchical_affinity_compatibility.py)<br>[test_hierarchical_affinity_compatibility.py::test_hc78_hc80_pure_modules_cannot_import_persistence_or_downstream](../../apps/backend/tests/test_hierarchical_affinity_compatibility.py) |
| HC79 | [test_hierarchical_affinity_compatibility.py::test_hc78_hc79_all349_definitions_and_123_frozen_runtime_files_retained](../../apps/backend/tests/test_hierarchical_affinity_compatibility.py)<br>[test_hierarchical_affinity_compatibility.py::test_hc79_retained_all2807_test_identities](../../apps/backend/tests/test_hierarchical_affinity_compatibility.py) |
| HC80 | [test_hierarchical_affinity.py::test_hc34_hc80_non_authority_flags_and_member_lineage](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity_compatibility.py::test_hc78_hc80_pure_modules_cannot_import_persistence_or_downstream](../../apps/backend/tests/test_hierarchical_affinity_compatibility.py) |
| HC81 | [test_hierarchical_affinity.py::test_hc81_all_nested_identity_manifests_checked](../../apps/backend/tests/test_hierarchical_affinity.py)<br>[test_hierarchical_affinity.py::test_hc81_mutable_ingredient_names_do_not_alias_or_grant_transfer](../../apps/backend/tests/test_hierarchical_affinity.py) |

## Remaining authority and status

Member ownership is PRESERVED; inherited EvidenceStrength is NOT_DERIVED. Learned/contextual/passive
evidence and TasteFit remain UNAVAILABLE; recursive transfer, parent/candidate aggregation remain
NOT_PERFORMED; planner_ready=False and activation_ready=False. No DIRECT declaration or durable
learned observation is minted. Proposal-local041 repeat signals never become behavioral history here.

SOURCE040A/B,041A–F,046A, prior source, PR #100 and hierarchy SOURCE remain frozen unchanged.
Full040/041/046 remain PARTIAL. Parent MTR-040 issue #41 remains OPEN pending a separate completion
review after any eventual040C freeze. MTR-039 is not started;024/020B/021 stay BLOCKED;
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED. No next slice is authorized.

**MTR-040C IMPLEMENTED — NOT FROZEN — IMPLEMENTATION REVIEW / FREEZE REQUIRED.**
