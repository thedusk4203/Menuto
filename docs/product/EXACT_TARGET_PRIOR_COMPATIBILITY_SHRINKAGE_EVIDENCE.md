# Exact-target Prior Compatibility & Shrinkage — implementation evidence

Current canonical status: **FROZEN / APPROVED** at `5728411ac12555f583f8df72ac71861998978aa4`.
The [freeze receipt](EXACT_TARGET_PRIOR_SHRINKAGE_FREEZE_RECEIPT.md) records PR #100's accepted
head, merge and successful exact post-merge CI. It supersedes only the current-status interpretation
of this historical delivery record. [Next dependency/design gate](POST_EXACT_TARGET_PRIOR_SHRINKAGE_DEPENDENCY_REVIEW.md).

Historical delivery status: **IMPLEMENTED / NOT FROZEN — dedicated implementation review required; NOT MERGED**.

Implementation authorization is limited to the additive slice named here. This is **not MTR-040C**;
MTR-040C remains **NOT ASSIGNED / NOT AUTHORIZED**. Full MTR-040/041/046 remain incomplete;
MTR-024/020B/021 remain BLOCKED; Execution NOT STARTED; PRECOMMIT FAIL-CLOSED.

## Canonical baseline and receipt identity

- exact implementation base: `12048deeffd8c0b30368df0684de1d971a2c4b9c`;
- approved design: PR #99, approved head `097557cc7b52676393c78e44f23c1ef313c989f5`;
- approved design merge is the implementation base above;
- implementation code/test/export head: `090ef5f2a752b16fb20c876e057562a3a5e503ba`;
- dedicated implementation PR: [#100](https://github.com/thedusk4203/Menuto/pull/100), OPEN / NOT MERGED at delivery; now merged/frozen per the canonical receipt above;
- full implementation CI: [40334554571](https://github.com/thedusk4203/Menuto/actions/runs/40334554571),
  SUCCESS on that exact code/test/export head; both python and web succeeded;
- final documentation-receipt PR head and its exact CI run: recorded in PR #100's receipt;
- schema: Alembic `0014 / 78 domain tables` (79 relations including Alembic);
- new migration, persistence table, cache/store or production numeric policy: **NONE**.

The code/test/export head identifies immutable implementation content. A later documentation-only
receipt commit can record that SHA without a recursive self-reference. The PR body binds the final
review head to its exact CI run. Neither CI success nor this document authorizes merge/freeze.

## Delivered interface and ownership

Preferences owns the pure member-owned consumer. The canonical reference provider remains a
global source, not a member author; no source/publication authority is added or relaxed.

Public entry point: `preferences.public.derive_exact_target_prior_backed_affinity(subject)`.
The independently importable zero-IO implementation is `preferences.prior_affinity`.
`ExactTargetPriorBackedAffinityInput` accepts exactly the frozen explicit input, frozen coherent
reference snapshot, complete authored compatibility policy and authored shrinkage policy.

The result retains household/member/typed target, complete coordinate, both recomputed frozen
child results (including their original sources, frontiers, clocks, identities and fingerprints),
mapped values, exact contributions, effective availability and both consumer-policy fingerprints.
Every draft is recursively reparsed and independently recomputed from primitive sources/policies.
Constructed/copied nested models, cached results and plausible re-hashed forgeries grant no authority.

Complete coordinate identity:

```text
MEMBER_PROFILE_AFFINITY / 1
target_kind
full compatibility_policy_fingerprint
POLICY_MEMBER_PROFILE_AFFINITY_UNITS
ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY
```

`ScopedMemberProfileAffinity` structurally binds descriptor + canonical amount. Mapping results,
contributions and effective values all use this wrapper. Naked amounts are numeric components only;
the consumer interface rejects them. No comparison/sum/aggregation operator exists on scoped values.
Same descriptor and canonical fraction permit deterministic equality, without planner authority.
Same fraction across kinds/policies establishes no comparison/aggregation semantics.

Compatibility hashing covers the canonical authored body, including exact source bindings,
coordinate family constants and all five explicit/reference mapping groups/rows. Derived descriptors
are materialized only after hashing; they cannot supply their own identity. Shrinkage fingerprint
is derivation provenance, outside the coordinate descriptor. It may change the selected point on
the same scale without redefining that scale.

Each explicit kind has all three authored values bound to the complete frozen 040B policy.
Reference maps are finite exact lookup only with strict order; an explicitly empty kind group
means every reference amount for that kind is unmapped. All five groups are mandatory. There is
no interpolation, extrapolation, nearest-neighbor mapping, provider fallback or provider aggregation.
Policy identity binds one provider ID plus immutable provider command hash and reference coordinate.
No production/default mapping anchors or shrinkage weights ship in runtime configuration.

## State, arithmetic and replay

- member RETRACTED always yields `MEMBER_RETRACTED`, even with compatible prior;
- active assertion + unavailable/unmapped prior yields observable `EXPLICIT_ONLY`;
- UNDECLARED + mapped prior yields `PRIOR_ONLY_COLD_START`, strength NONE;
- no compatible source yields unavailable, never a synthesized neutral/zero;
- real mapped zero remains AVAILABLE; declared NEUTRAL may map to nonzero;
- LOW/MEDIUM/HIGH remain ordinal frozen EvidenceStrength, never probabilities;
- active prior weights are canonical exact fractions in `[0,1)`, with LOW >= MEDIUM >= HIGH;
- both blend operands must match the independently constructed descriptor before arithmetic;
- exact weighted contributions retain descriptors, including a real zero-weight contribution;
- no float, rounding, clipping or statistical-confidence interpretation.

Authored rational components have a 31-bit magnitude bound matching the reference source's
component limit. Derived amounts allow 128-bit components: the convex sum has at most three
31-bit authored denominator factors (explicit output, prior output, weight), so its reduced
denominator needs at most 93 bits and its bounded numerator no more. This resource bound does
not truncate/round any reachable result. Oversized authored inputs reject before blending.

`VERSIONED_CONSUMER_POLICY_REPLAY` preserves separate coherent cuts; a later interpretation policy
may replay old source snapshots. No simultaneous-liveness, atomic dual-source capture or historical
AS_OF_CAPTURE policy-knowledge claim is made. Offline self-consistency does not prove canonical DB origin.

## Changed files

Runtime additions:

- `apps/backend/app/modules/preferences/prior_affinity_contracts.py`
- `apps/backend/app/modules/preferences/prior_affinity.py`
- `apps/backend/app/modules/preferences/public.py` — one additive lazy facade only

Export additions:

- `tools/export_domain_contracts.py`
- `packages/contracts/domain.schema.json`

Test/evidence additions:

- `apps/backend/tests/prior_shrinkage_fixtures.py`
- `apps/backend/tests/test_prior_shrinkage.py`
- `apps/backend/tests/fixtures/prior_shrinkage_compatibility.json`
- `apps/backend/tests/fixtures/prior_shrinkage_baseline_tests.json`
- `apps/backend/tests/fixtures/prior_shrinkage_acceptance.json`
- `docs/product/EXACT_TARGET_PRIOR_COMPATIBILITY_SHRINKAGE_EVIDENCE.md`

Documentation status updates:

- `README.md`
- `docs/product/BACKLOG.md`
- `docs/product/IMPLEMENTATION_BLUEPRINT.md`
- `docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md`
- `docs/product/INVARIANT_COVERAGE.md`
- `docs/product/EXACT_TARGET_PRIOR_COMPATIBILITY_SHRINKAGE_DESIGN.md`

## Regression receipts

New suite: **220 passed**. Complete local real-PostgreSQL regression: **2,597 passed**, no skips,
one existing dependency deprecation warning, 882.23s. Exact implementation-head CI above:
**2,597 passed**, no skips, three dependency warnings, 253.00s; real SCRAM/TLS smoke **8/8**.
Collected tests: **2,597 = 2,377 retained + 220 additive**. All new tests are pure tests in the new
test module; no existing test is modified/removed. Baseline node IDs are pinned before new exports.
One frozen parametrized test creates a uuid4 at collection, so retained-ID comparison normalizes
UUID spelling only and preserves the multiplicity of every case; all baseline source files are
unchanged. Real PostgreSQL count: **918**, including **120 reference_prior_auth** source/authority
cases. CI separately reruns the existing 8-case real SCRAM/TLS smoke; these are not 8 additional tests.

Local lint, architecture/import checks, OpenAPI/domain/client snapshot checks and synthetic fixture
verification passed. Benchmark **22/22**; client tests **10/10**; client typecheck and web build passed.
Real schema verification comes from retained PG source/migration regressions: upgrade to 0014,
79 tables including Alembic, metadata check, downgrade/re-upgrade and unchanged source enforcement.

All **299** pre-existing exported definitions are SHA-256 pinned and unchanged; **19** additive
definitions produce **318** total. The existing bundle identifier is retained for frozen compatibility.
Migrations **0001–0014** and frozen Preferences/041/046A semantic implementations are file-hash
pinned. No existing frozen contracts or source derivation semantics are modified.

New exported definitions:

- `AvailableExactTargetProfileAffinity`
- `EvidenceStrengthShrinkageRule`
- `ExactTargetPriorBackedAffinityDraft`
- `ExactTargetPriorBackedAffinityInput`
- `ExactTargetPriorCompatibilityPolicy`
- `ExactTargetShrinkageContribution`
- `ExactTargetShrinkagePolicy`
- `ExplicitProfileMappingRule`
- `ExplicitTargetKindCompatibilityMap`
- `MappedExplicitProfileAffinity`
- `MappedReferenceProfileAffinity`
- `MemberProfileAffinityAmount`
- `MemberProfileAffinityCoordinate`
- `PriorInfluenceWeight`
- `ReferenceProfileMappingRule`
- `ReferenceTargetKindCompatibilityMap`
- `ScopedMemberProfileAffinity`
- `UnavailableExactTargetProfileAffinity`
- `UnavailableReferenceCompatibility`

Zero-IO evidence: static import allowlist on both new modules and frozen pure child entry points,
plus runtime guards denying filesystem open, sockets and SQLAlchemy Session.execute during full
derivation. The implementation imports no persistence/service modules, creates no session, performs
no capture, writes no state and installs no endpoint/adapter/repository/worker. The old Preferences
public facade retains its existing IO imports; its new function delegates to the pure implementation.

## Approved acceptance cases 1–68

All named tests below are in `apps/backend/tests/test_prior_shrinkage.py`; parametrized expansions
include all five kinds and all declaration/prior availability combinations. The machine-readable
mapping is `apps/backend/tests/fixtures/prior_shrinkage_acceptance.json`.

| Case | Approved requirement | Test functions |
| --- | --- | --- |
| 1 | Same rational `1/2` in source coordinates does not auto-convert. | `test_c01_source_fractions_have_no_automatic_conversion` |
| 2 | Wrong explicit policy ID rejects. | `test_c02_c03_explicit_policy_identity_version` |
| 3 | Wrong explicit policy version rejects. | `test_c02_c03_explicit_policy_identity_version` |
| 4 | Wrong explicit policy fingerprint rejects. | `test_c04_explicit_policy_fingerprint` |
| 5 | Compatibility row's expected explicit amount differing from the pinned 040B policy rejects. | `test_c05_all_explicit_amount_bindings` |
| 6 | Missing/duplicate explicit mapping row rejects. | `test_c06_missing_duplicate_explicit_mapping` |
| 7 | Explicit mapped outputs not satisfying DISLIKE < NEUTRAL < LIKE reject. | `test_c07_explicit_mapping_order` |
| 8 | Wrong reference coordinate ID/version/unit/applicability rejects. | `test_c08_reference_coordinate_is_closed` |
| 9 | Wrong provider ID/provider immutable identity rejects. | `test_c09_provider_immutable_binding` |
| 10 | Multiple-provider aggregation/fallback is impossible by contract. | `test_c10_provider_aggregation_not_in_contract` |
| 11 | Empty or duplicate reference mapping rules are handled according to the complete policy shape; duplicate exact source values reject. | `test_c11_empty_reference_group_is_explicitly_unmapped_duplicate_rejects` |
| 12 | Reference mapping order inversion rejects. | `test_c12_reference_mapping_strict_order` |
| 13 | Valid reference amount absent from finite map yields `PRIOR_VALUE_NOT_MAPPED`, not guessed conversion. | `test_c13_no_reference_interpolation` |
| 14 | `NO_PUBLICATION` never synthesizes zero. | `test_c14_no_publication_does_not_synthesize_zero`<br>`test_c14_to_c25_exhaustive_missingness_by_kind` |
| 15 | Prior `RETRACTED` never reuses historical amount. | `test_c15_prior_retracted_does_not_reuse_amount` |
| 16 | Actual mapped `AVAILABLE 0/1` remains real available prior. | `test_c16_real_available_zero` |
| 17 | Explicit `UNDECLARED` never becomes declared NEUTRAL. | `test_c17_undeclared_distinct_from_neutral` |
| 18 | Explicit `RETRACTED` never collapses into UNDECLARED. | `test_c18_retracted_distinct_from_undeclared` |
| 19 | Member RETRACTED + available prior yields `UNAVAILABLE / MEMBER_RETRACTED` in v1. | `test_c19_member_retraction_blocks_all_prior_branches` |
| 20 | DECLARED + mapped available prior yields exact blended result. | `test_c20_exact_blend_all_five_kinds` |
| 21 | DECLARED + no publication yields explicit-only result with preserved reason. | `test_c21_c22_c23_observable_explicit_only` |
| 22 | DECLARED + retracted prior yields explicit-only result with preserved reason. | `test_c21_c22_c23_observable_explicit_only` |
| 23 | DECLARED + unmapped prior yields explicit-only result with preserved incompatibility reason. | `test_c21_c22_c23_observable_explicit_only` |
| 24 | UNDECLARED + mapped prior yields prior-only cold-start result with EvidenceStrength NONE. | `test_c24_cold_start_does_not_mint_strength` |
| 25 | UNDECLARED + unavailable/unmapped prior yields unavailable result, no neutral baseline. | `test_c25_no_explicit_or_compatible_prior`<br>`test_c14_to_c25_exhaustive_missingness_by_kind` |
| 26 | Declared NEUTRAL mapping is not forced to output zero. | `test_c26_neutral_mapping_need_not_be_zero` |
| 27 | LOW/MEDIUM/HIGH are never parsed/used as probabilities. | `test_c27_strength_is_ordinal_not_probability` |
| 28 | Missing/duplicate shrinkage strength rules reject. | `test_c28_strength_rules_complete` |
| 29 | Invalid/noncanonical prior weights reject. | `test_c29_malformed_weights` |
| 30 | Active-declaration prior weight `1` rejects. | `test_c30_active_weight_one_rejects` |
| 31 | Monotonicity violation `LOW < MEDIUM` or `MEDIUM < HIGH` rejects. | `test_c31_nonmonotonic_weights` |
| 32 | Zero prior weight is valid and retains zero prior contribution in a compatible blend trace. | `test_c32_zero_weight_preserves_prior_trace` |
| 33 | Stronger evidence never receives greater prior influence under the selected policy. | `test_c33_ordinal_policy_chooses_exact_authored_weight` |
| 34 | Exact blend arithmetic canonicalizes by gcd and never uses float. | `test_c34_exact_rational_canonical_reduction` |
| 35 | Blend outside `[-1,1]` is treated as validation/arithmetic failure, never clipped. | `test_c35_no_clipping_or_noncanonical_output` |
| 36 | Explicit request with zero or multiple targets rejects for this singleton slice. | `test_c36_exactly_one_requested_target` |
| 37 | Explicit target and reference target mismatch rejects. | `test_c37_c38_mismatched_identity_or_kind` |
| 38 | Same UUID under a different target kind rejects. | `test_c37_c38_mismatched_identity_or_kind`<br>`test_c38_identical_uuid_different_typed_kind_rejects` |
| 39 | New reviewed feature-term/version ID is an independent exact target; no alias reconciliation. | `test_c39_new_feature_version_identity_independent` |
| 40 | Forged cached explicit affinity/EvidenceStrength cannot be supplied as authority. | `test_c40_c41_cached_children_not_input_authority` |
| 41 | Forged cached prior result cannot be supplied as authority. | `test_c40_c41_cached_children_not_input_authority` |
| 42 | Forged mapped amount/weight/contribution/final result/fingerprint rejects or is independently recomputed. | `test_c42_rehashed_derived_forgery_rejects` |
| 43 | Old coherent explicit source + old coherent reference source + same policies replays byte-deterministically. | `test_c43_old_cuts_replay_byte_deterministically` |
| 44 | Fresh prior source revision can change only the fresh consumer result; old immutable replay remains stable. | `test_c44_fresh_prior_changes_only_fresh_result` |
| 45 | Different child capture timestamps remain deterministic and do not create simultaneous-liveness claims. | `test_c45_separate_capture_cuts_are_retained` |
| 46 | Later compatibility policy can reinterpret old snapshots only under a new policy fingerprint/version; old result replay unchanged. | `test_c46_new_mapping_version_does_not_mutate_old_replay` |
| 47 | Policy provenance after child capture is allowed only under `VERSIONED_CONSUMER_POLICY_REPLAY` and does not masquerade as AS_OF_CAPTURE knowledge. | `test_c47_later_policy_is_replay_not_as_of_capture` |
| 48 | Proposal-local 041 recipe/feature repeat data cannot enter this contract or alter affinity. | `test_c48_c49_c50_unrelated_evidence_cannot_enter` |
| 49 | Cooking, out-of-stock, too-expensive, no-time, no-equipment and operational friction cannot enter this exact explicit/prior contract. | `test_c48_c49_c50_unrelated_evidence_cannot_enter` |
| 50 | Forced conflict resolution cannot enter voluntary preference derivation. | `test_c48_c49_c50_unrelated_evidence_cannot_enter` |
| 51 | Cross-target/hierarchical transfer is impossible by contract. | `test_c51_no_hierarchy_or_cross_target_policy` |
| 52 | Cross-member aggregation/fan-out is impossible by contract. | `test_c52_no_cross_member_fanout` |
| 53 | Pure derivation performs zero DB/network IO and zero writes. | `test_c53_zero_io_closed_imports_and_runtime_guards` |
| 54 | No migration `0015`; schema remains `0014 / 78`. | `test_c54_c55_c56_frozen_files_migrations_and_299_definitions` |
| 55 | Frozen 040A/B, 041A-F, 046A and all 299 existing exported definitions remain structurally compatible. | `test_c54_c55_c56_frozen_files_migrations_and_299_definitions` |
| 56 | Frozen reviewed-prior source contracts/hashes/migration0014 remain unchanged. | `test_c54_c55_c56_frozen_files_migrations_and_299_definitions` |
| 57 | No production prior records or production policy numeric values are added. | `test_c57_no_production_policy_values_and_retained_test_baseline` |
| 58 | `planner_ready=False` and `activation_ready=False` are immutable. | `test_c58_fixed_scope_flags_reject_widening` |
| 59 | No hard-safety, validator or PRECOMMIT authority can be minted. | `test_c59_cannot_mint_authority` |
| 60 | Canonicalization is deterministic under semantically unordered policy-row shuffles while preserving order where policy order is meaningful. | `test_c60_unordered_policy_shuffle_same_fingerprint_and_result` |
| 61 | Same rational `1/2` under INGREDIENT vs FLAVOR has no defined comparison or aggregation semantics, even with the same coordinate family label/version. | `test_c61_same_fraction_different_kind_no_comparison_or_aggregation` |
| 62 | Same rational `1/2` under compatibility policy A vs B has no defined comparison or aggregation semantics, even if both policies happen to contain identical numeric mappings. | `test_c62_same_fraction_different_mapping_policy_no_comparison` |
| 63 | Blend operands carrying different complete output coordinate descriptors reject before arithmetic; coercion/relabeling is forbidden. | `test_c63_mismatched_descriptor_rejects_before_arithmetic` |
| 64 | Forged mapped/contribution/effective output with the correct numeric value but wrong descriptor target kind rejects, even if re-hashed. | `test_c64_c65_correct_numeric_wrong_descriptor_rehashed` |
| 65 | Forged mapped/contribution/effective output with the correct numeric value but wrong compatibility-policy fingerprint rejects, even if re-hashed. | `test_c64_c65_correct_numeric_wrong_descriptor_rehashed` |
| 66 | Same exact descriptor + same canonical rational permits deterministic scoped-value equality; distinct result provenance is still preserved and equality grants no planner authority. | `test_c66_equal_descriptor_equal_fraction_deterministic_equality` |
| 67 | Changing only shrinkage-policy version while holding compatibility policy and target kind fixed changes derivation/provenance, not the coordinate; changed weights may change the selected point on that same scale. | `test_c67_shrinkage_version_changes_provenance_not_coordinate` |
| 68 | A future consumer cannot strip the descriptor and treat the numeric component as globally comparable planner utility: naked consumer values reject, scoped serialization retains the complete descriptor, and this interface grants no cross-scope comparison/aggregation operation. | `test_c68_descriptor_stripping_naked_downstream_value_rejects` |

## Preserved exclusions and authority

Frozen 040A/B, 041A–F, 046A, prior source and migrations0001–0014 retain their semantics.
040B's own prior/shrunk_affinity remain UNAVAILABLE. This consumer uses new additive result types.
No hierarchy/direct-to-feature propagation/cross-member or cross-target transfer; no learned,
contextual, inferred or passive evidence; no durable behavioral updates; no TasteFit, novelty,
accepted/confirmed/global history, candidate aggregation, planner scoring/weights, safety authority,
hard exclusion, Execution or PRECOMMIT. `planner_ready=False`; `activation_ready=False`.

No deviations from the approved design. Empty reference-map groups and the justified arithmetic
resource bounds make the design's explicitly allowed complete-policy/resource choices concrete.

**READY FOR EXACT-TARGET PRIOR COMPATIBILITY/SHRINKAGE IMPLEMENTATION REVIEW — NOT MERGED**
