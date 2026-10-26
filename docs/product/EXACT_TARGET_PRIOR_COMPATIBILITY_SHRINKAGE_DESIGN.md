# Exact-target Prior Compatibility & Shrinkage Foundation

Status: **DESIGN PROPOSAL — IMPLEMENTATION NOT AUTHORIZED**

Design date: 2026-10-26.

Canonical baseline for this design:

- repository: `thedusk4203/Menuto`
- exact base `main`: `a31de892b61dbf524be4f0008b2756ff39ce162e`
- prior-source freeze: `fce85327cc8c3f4444847522d8ef474ef8d4e670`
- schema: Alembic `0014`, 78 domain tables
- frozen relevant work: MTR-040A/B, MTR-041A/B/C/D/E/F, MTR-046A, Canonical Reviewed Exact-target Preference Prior Source Foundation
- authorization: post-source dependency review selected this slice for **detailed design only**; implementation, `MTR-040C`, migration `0015`, hierarchy, MTR-024/020B/021, Execution and PRECOMMIT remain unauthorized.

This document defines a proposed additive, pure consumer between two already-frozen sources. It does not modify either source and does not claim that full MTR-040 is complete.

---

## 1. Problem and selected scope

The repository now has two independent exact-target facts:

1. MTR-040B derives a member-owned explicit target affinity and `EvidenceStrength` from the current explicit declaration head under one complete `ExplicitTargetAffinityPolicy`.
2. The reviewed reference-prior source resolves one explicitly selected provider's exact-target reference prior under `CURATED_REFERENCE_PREFERENCE / v1`.

The missing capability is **not another source**. The missing capability is an explicit semantic bridge between those two coordinate systems and a deterministic exact-target shrinkage policy.

Selected v1 flow:

```text
frozen ExplicitTargetAffinityInput
    -> frozen 040B derivation
                         \
                          \
                           -> versioned compatibility policy
                          /                +
frozen ReferencePriorSourceSnapshotDraft  versioned shrinkage policy
    -> frozen prior resolution            |
                                           v
                           exact-target member profile affinity
```

One interpretation is scoped to:

```text
one household
× one HouseholdMember
× one exact PreferenceTarget
× one exact frozen explicit-policy version
× one explicitly selected reviewed-reference provider
× one compatibility-policy version
× one shrinkage-policy version
```

Supported target kinds remain exactly:

`INGREDIENT | DIRECT_RECIPE | PROTEIN | METHOD | FLAVOR`.

No cross-target or cross-member transfer is in scope.

---

## 2. Ownership and authority boundary

Preferences owns this exact-target profile-consumer semantic because the output is member preference/profile information. The output belongs to the `HouseholdMember` identified by the frozen explicit source.

The shared reference provider does **not** become a profile owner. The prior publisher does not become an author of member preference. Learning does not own this exact explicit/prior composition and cannot manufacture either child source.

Keep these identities distinct:

```text
member preference owner
!= explicit declaration actor
!= reviewed-reference provider
!= reviewed-reference curator
!= compatibility-policy author
!= shrinkage-policy author
```

The result is soft preference information only. It has no hard-safety, allergy, diet, nutrition, validation, plan-activation or PRECOMMIT authority.

---

## 3. Critical coordinate decision

### 3.1 Existing coordinates are not interchangeable

Frozen 040B:

```text
ExplicitAffinityAmount
unit = POLICY_EXPLICIT_AFFINITY_UNITS
```

Frozen reviewed prior:

```text
ReferencePriorAmount
coordinate_id      = CURATED_REFERENCE_PREFERENCE
coordinate_version = 1
unit               = REVIEWED_REFERENCE_ANCHOR_UNITS
applicability      = GLOBAL_REFERENCE_ONLY
```

Both happen to use exact rationals bounded by `[-1, 1]`. That representational similarity proves **nothing** about convertibility. `1/2` in one coordinate is not automatically `1/2` in the other.

In particular, the reference coordinate does not claim that arbitrary numeric differences are calibrated distances, and 040B's explicit amount is a policy interpretation of an assertion rather than a population statistic or utility.

Therefore v1 explicitly rejects:

- identity conversion;
- affine conversion inferred from common endpoints;
- interpolation over arbitrary reference amounts;
- direct weighted average of raw `ExplicitAffinityAmount` and raw `ReferencePriorAmount`;
- treating either source coordinate as probability or candidate utility.

### 3.2 New consumer/output coordinate

Introduce a distinct proposed coordinate:

```text
coordinate_id      = MEMBER_PROFILE_AFFINITY
coordinate_version = 1
unit               = POLICY_MEMBER_PROFILE_AFFINITY_UNITS
scope              = ONE_POLICY_VERSION_EXACT_TARGET_ONLY
```

Proposed `MemberProfileAffinityAmount` is a canonical signed exact rational in `[-1,1]`.

Its meaning is:

> a policy-linear exact-target member-profile affinity coordinate produced only after explicit source values and reviewed reference values have been mapped by an approved compatibility policy.

Unlike the two source coordinates, this output coordinate explicitly permits **convex interpolation after mapping**, because the compatibility policy authors the source anchors into this policy-linear space.

It is still **not**:

- probability of liking;
- population prevalence;
- planner utility;
- EvidenceStrength;
- hard exclusion/safety policy;
- comparable across different compatibility/shrinkage policy versions without another explicit policy.

A reference prior mapped into this coordinate remains reference evidence. It never becomes an `ExplicitAffinityAmount` or an explicit declaration.

---

## 4. Compatibility policy — exact authored mapping, never guessed conversion

Proposed contract: `ExactTargetPriorCompatibilityPolicy`.

It is immutable, versioned, extra-forbid, deterministic, and complete for the explicit side. Proposed top-level fields:

- `policy_id`
- `policy_version`
- `provenance`, restricted to `REVIEWED_REFERENCE`
- `interpretation_mode = VERSIONED_CONSUMER_POLICY_REPLAY`
- exact expected 040B explicit policy identity/version/fingerprint
- exact expected reviewed-reference provider identity plus immutable provider command hash
- expected reference coordinate ID/version/unit/applicability
- output coordinate identity/version/unit
- five exact target-kind explicit mapping groups
- five exact target-kind reference mapping groups

No production mappings/default values are supplied by this design.

### 4.1 Explicit-side mapping

For each of the five target kinds, require exactly three authored mapping rows:

```text
(target_kind, DISLIKE, expected ExplicitAffinityAmount) -> MemberProfileAffinityAmount
(target_kind, NEUTRAL, expected ExplicitAffinityAmount) -> MemberProfileAffinityAmount
(target_kind, LIKE,    expected ExplicitAffinityAmount) -> MemberProfileAffinityAmount
```

The `expected ExplicitAffinityAmount` must exactly equal the amount in the pinned frozen `ExplicitTargetAffinityPolicy`. The compatibility policy cannot reinterpret the explicit source under a different hidden rule.

For each target kind require strict output ordering:

```text
mapped(DISLIKE) < mapped(NEUTRAL) < mapped(LIKE)
```

Do **not** require:

- `NEUTRAL = 0`;
- `DISLIKE = -LIKE`;
- endpoints `-1`/`+1`;
- equal spacing across the three values;
- equal mapping across target kinds.

This preserves 040B semantics while explicitly embedding its discrete policy outputs into the new blend coordinate.

### 4.2 Reference-side mapping

The reviewed-reference coordinate accepts exact rationals but does not establish cardinal spacing. V1 therefore chooses:

```text
reference_mapping_mode = FINITE_EXACT_LOOKUP
```

For each target kind, the compatibility policy contains a finite authored set:

```text
(target_kind, exact ReferencePriorAmount) -> MemberProfileAffinityAmount
```

Rules:

- source reference amounts are unique within a target kind;
- output mappings are unique for different source values unless a future design explicitly allows plateaus;
- when rows are ordered by exact source amount, mapped output must be strictly increasing;
- no interpolation between mapped source values;
- no nearest-neighbor mapping;
- no endpoint extrapolation;
- no target-kind fallback;
- no use of a mapping row from another provider or another coordinate version.

A valid provider publication whose exact amount is not present in the selected compatibility policy is **not corrupt source data**. It resolves as an explicit consumer incompatibility:

`PRIOR_VALUE_NOT_MAPPED`.

A later compatibility-policy version may add a mapping without mutating old source snapshots or old policy replay.

### 4.3 Provider binding

One compatibility policy pins exactly one provider identity. The frozen reference capture request must name exactly that provider and its immutable provider fact must match the policy binding.

No:

- provider fallback;
- provider priority list;
- best-provider search;
- provider averaging/voting;
- household-inferred provider;
- cohort/locale inference.

A different provider requires a different explicit policy binding/version.

---

## 5. Shrinkage policy

Proposed contract: `ExactTargetShrinkagePolicy`.

It is immutable, versioned and restricted to `REVIEWED_REFERENCE` provenance. It pins the exact compatibility-policy fingerprint and output coordinate.

### 5.1 Prior influence coefficient

Proposed `PriorInfluenceWeight` is an exact canonical rational:

```text
0 <= numerator / denominator < 1
```

The value means **policy influence of a compatible reviewed prior in the blend coordinate**. It is not statistical confidence, posterior probability, pseudo-count or sample size.

For active explicit declarations, require exactly one authored weight for each non-NONE frozen `EvidenceStrength`:

```text
LOW
MEDIUM
HIGH
```

No weight is derived from:

- authorship directly;
- declaration history length;
- retry count;
- support count;
- proposal exposures;
- recipe/feature repeat count;
- cooking/consumption events;
- retail/context friction.

Require monotonicity:

```text
prior_weight(LOW) >= prior_weight(MEDIUM) >= prior_weight(HIGH)
```

Equal values are allowed. Zero is allowed. `1` is forbidden for an active declaration so that a current explicit assertion can never be numerically erased by the shared prior.

All exact coefficients are authored policy data. This design defines no production numeric defaults.

### 5.2 Exact blend algebra

Only after both inputs have been mapped into `MemberProfileAffinityAmount`:

```text
explicit_weight = 1 - prior_weight

effective =
    explicit_weight * mapped_explicit
  + prior_weight    * mapped_prior
```

Use integer rational multiplication/addition followed by canonical gcd reduction. No float, decimal rounding, epsilon comparison or hidden clipping.

Because both mapped inputs lie in `[-1,1]` and weights form an exact convex pair, the effective value must remain in `[-1,1]`. Any implementation that requires clipping indicates an arithmetic or validation bug and must reject rather than clip.

Retain an exact audit trace:

- mapped explicit amount;
- mapped prior amount;
- explicit weight;
- prior weight;
- exact explicit contribution;
- exact prior contribution;
- final canonical amount;
- rule keys and policy fingerprints.

A valid `prior_weight = 0` remains an explicit policy decision. If the compatible prior exists, keep the zero prior contribution in the trace rather than pretending no prior was available.

---

## 6. Member-state and missingness matrix

V1 makes the following decisions explicit.

### 6.1 `DECLARED` + compatible `AVAILABLE` prior

Result:

```text
status = AVAILABLE
mode   = BLENDED_EXPLICIT_AND_PRIOR
```

Use the active explicit row's frozen `EvidenceStrength` to select the shrinkage weight and run the exact blend.

`EvidenceStrength` itself remains unchanged and comes only from frozen 040B.

### 6.2 `DECLARED` + unavailable/incompatible prior

Prior reasons include:

- `NO_PUBLICATION`
- source `RETRACTED`
- `PRIOR_VALUE_NOT_MAPPED`

Result:

```text
status = AVAILABLE
mode   = EXPLICIT_ONLY
```

Map the active explicit assertion into the output coordinate. Preserve the exact prior availability/incompatibility reason and set shrinkage to `NOT_APPLIED`.

This is an **observable explicit fallback**, not a synthesized prior of zero.

### 6.3 `UNDECLARED` + compatible `AVAILABLE` prior

Result:

```text
status = AVAILABLE
mode   = PRIOR_ONLY_COLD_START
EvidenceStrength = NONE
```

Use the mapped prior directly as the effective output amount. No blend weight is applied because no explicit member amount exists.

Prior-only cold start does not create a declaration, does not create DIRECT evidence and does not mint EvidenceStrength.

### 6.4 `UNDECLARED` + unavailable/incompatible prior

Result:

```text
status = UNAVAILABLE
reason = NO_EXPLICIT_OR_COMPATIBLE_PRIOR
```

No neutral/zero baseline is synthesized.

### 6.5 `RETRACTED` member target

V1 chooses the conservative behavior:

```text
status = UNAVAILABLE
reason = MEMBER_RETRACTED
```

This applies even when a compatible shared prior exists.

Rationale: a current member retraction is intentionally distinct from never having declared anything. V1 must not immediately reintroduce a shared reference value after the member deliberately removed their explicit target state. A future design may revisit this policy, but it may not silently reinterpret this v1 result.

Do not treat historical pre-retraction explicit values as active inputs.

### 6.6 Real zeros remain real

- explicit declared `NEUTRAL` is a real declaration, and its mapped output need not equal zero;
- reviewed prior `AVAILABLE 0/1` is a real prior value if the compatibility policy explicitly maps it;
- no source / retracted source / unmapped source are never converted into zero.

Always preserve:

```text
UNDECLARED != DECLARED NEUTRAL != RETRACTED
NO_PUBLICATION != prior RETRACTED != AVAILABLE 0/1
```

---

## 7. Proposed input boundary

Proposed `ExactTargetPriorBackedAffinityInput` contains primitives/policies, not trusted child result caches:

- `explicit: ExplicitTargetAffinityInput`
- `reference_source: ReferencePriorSourceSnapshotDraft`
- `compatibility_policy: ExactTargetPriorCompatibilityPolicy`
- `shrinkage_policy: ExactTargetShrinkagePolicy`

Structural requirements:

1. frozen explicit request contains **exactly one** requested target;
2. frozen reference request contains **exactly the same one** typed target;
3. reference provider exactly equals compatibility-policy provider;
4. explicit policy exactly equals the identity/version/fingerprint pinned by the compatibility policy;
5. reference source coordinate exactly equals the pinned closed v1 coordinate;
6. shrinkage policy exactly pins the compatibility-policy fingerprint;
7. no caller-supplied mapped amounts, prior rows, EvidenceStrength, weights, contributions, totals or cached child result fingerprints are accepted as authoritative inputs.

This singleton slice is deliberate. Multi-target assembly is deferred until exact-target semantics are frozen.

---

## 8. Pure derivation and recursive distrust

Proposed pure function:

`derive_exact_target_prior_backed_affinity(subject)`

Required flow:

1. recursively reparse all input primitives;
2. invoke/reproduce the frozen `derive_explicit_target_affinity_profile()` semantics from the frozen `ExplicitTargetAffinityInput`;
3. invoke/reproduce frozen `resolve_reference_priors()` semantics from the frozen `ReferencePriorSourceSnapshotDraft`;
4. verify one exact target and all provider/policy/coordinate bindings;
5. resolve the exact member state and frozen EvidenceStrength;
6. map explicit/prior branches by the compatibility policy;
7. apply the exact state matrix and, when applicable, the shrinkage policy;
8. recompute all contribution traces and fingerprints;
9. return a new immutable result.

The core path must have **zero DB IO, zero writes, zero network IO and no hidden source refresh**.

Do not accept cached `ExplicitTargetAffinityProfileDraft` or cached `ReviewedReferencePriorDraft` as source authority. If such outputs are included later for diagnostics, they must be recomputed and equality-checked, never trusted.

Forging/re-hashing any of these must not mint a valid result:

- explicit affinity;
- EvidenceStrength;
- prior row;
- source status;
- mapped amount;
- selected weight;
- contribution;
- effective result;
- result fingerprint.

---

## 9. Capture cuts and policy replay semantics

The two frozen sources have different canonical capture/authority seams. Do **not** weaken either source merely to obtain one transaction or one timestamp.

A valid input can be:

```text
explicit member snapshot @ cut A
reviewed-reference snapshot @ cut B
compatibility policy      @ version C
shrinkage policy          @ version S
```

The result must retain at least:

- explicit source fingerprint;
- explicit manifest fingerprint;
- explicit-policy fingerprint;
- explicit capture clocks/frontier already present in the frozen source;
- reference source fingerprint;
- reference provider/frontier/capture clocks already present in the frozen source;
- compatibility-policy fingerprint;
- shrinkage-policy fingerprint.

Selected interpretation mode:

```text
VERSIONED_CONSUMER_POLICY_REPLAY
```

Compatibility/shrinkage policies are **interpretation policy**, not historical source evidence. A later immutable policy version may deterministically reinterpret an older coherent source snapshot. Therefore this slice does not impose `policy.provenance.observed_at <= source.captured_at` as if the policy were evidence available at the source cut.

Consequences:

- replay is deterministic for the same source+policy fingerprints;
- result must expose/preserve selected policy provenance/version;
- result does **not** claim "what the system knew at source capture time" unless a future separately designed AS-OF policy mode establishes that claim;
- result does **not** claim simultaneous liveness of cuts A and B;
- result is not a current authorization or PRECOMMIT token.

Do not invent a caller clock merely to make a pure function appear current.

---

## 10. Proposed additive contracts

Names below are concrete design proposals; they are not implemented or exported yet.

### Coordinate and mapping

- `MemberProfileAffinityCoordinate`
- `MemberProfileAffinityAmount`
- `ExplicitProfileMappingRule`
- `ExplicitTargetKindCompatibilityMap`
- `ReferenceProfileMappingRule`
- `ReferenceTargetKindCompatibilityMap`
- `ExactTargetPriorCompatibilityPolicy`

### Shrinkage

- `PriorInfluenceWeight`
- `EvidenceStrengthShrinkageRule`
- `ExactTargetShrinkagePolicy`
- `ExactTargetShrinkageContribution`

### Mapped/availability branches

- `MappedExplicitProfileAffinity`
- `MappedReferenceProfileAffinity`
- `UnavailableReferenceCompatibility`
- `AvailableExactTargetProfileAffinity`
- `UnavailableExactTargetProfileAffinity`

### Input/result

- `ExactTargetPriorBackedAffinityInput`
- `ExactTargetPriorBackedAffinityDraft`

Do not modify frozen 040B types to make `UnavailablePreferencePrior` suddenly available. The new consumer is additive and wraps/recomputes frozen child semantics without widening their contracts.

---

## 11. Proposed result boundary

`ExactTargetPriorBackedAffinityDraft` belongs to the exact household/member from the explicit source and contains one exact target result.

Required audit fields include:

- canonical subject input;
- target;
- frozen member raw state;
- frozen EvidenceStrength;
- explicit mapping status/rule;
- prior source status;
- prior compatibility status/rule;
- exact shrinkage mode/trace when applicable;
- effective availability/result;
- all child/policy fingerprints;
- result fingerprint.

Fixed scope flags:

```text
coverage                    = ONE_MEMBER_ONE_EXACT_TARGET_PRIOR_BACKED_ONLY
interpretation_mode          = VERSIONED_CONSUMER_POLICY_REPLAY
member_owner                 = PRESERVED
explicit_evidence_strength   = PRESERVED_NOT_MODIFIED
learned_evidence             = UNAVAILABLE
contextual_evidence          = UNAVAILABLE
passive_evidence             = UNAVAILABLE
cross_target_inference       = NOT_PERFORMED
hierarchical_inference       = NOT_PERFORMED
provider_aggregation         = NOT_PERFORMED
candidate_aggregation        = NOT_PERFORMED
taste_fit                    = UNAVAILABLE
planner_ready                = False
activation_ready             = False
```

No `is_safe`, `PRECOMMIT`, current-source certificate or liveness token exists.

---

## 12. Hierarchical preference remains a separate future slice

This design must not infer:

- Recipe preference -> Flavor preference;
- Recipe preference -> Method preference;
- Ingredient preference -> Protein preference;
- Protein prior -> Ingredient prior;
- Recipe/Ingredient preference -> any 046A classification term;
- feature code/name/version aliases;
- one member's preference -> another member.

Frozen 046A classification proves culinary classification, not taste transfer.

A later hierarchical design still requires separately approved:

- mapping ownership;
- direction;
- versioning;
- attenuation;
- direct-vs-inherited precedence;
- multi-parent conflict handling;
- missingness;
- correction/invalidation;
- provenance;
- EvidenceStrength behavior.

Do not name this exact-target slice `MTR-040C` until the user separately approves milestone scope/numbering.

---

## 13. Explicit non-goals

Not in this slice:

- production prior content/publication;
- provider selection UI/default/fallback;
- cohort/locale priors;
- hierarchical/cross-target inference;
- learned, contextual, inferred or passive evidence;
- MTR-039 attribution router;
- accepted/confirmed exposure history;
- global/cross-week novelty;
- candidate TasteFit;
- shared-household preference aggregation;
- MTR-024 utility composition;
- MTR-020B portfolio roles;
- MTR-021 feasibility;
- Execution;
- PRECOMMIT;
- allergy/diet/safety exclusion;
- validation authority;
- production policy values;
- persisted behavior score/profile cache.

Proposal-local MTR-041 repeat penalties are not inputs to this affinity derivation.

---

## 14. Persistence and migration decision

Selected design is a pure additive consumer over already-persisted/captured sources.

Expected implementation persistence:

```text
Alembic head: 0014
Domain tables: 78
New migration: NONE
New profile table/cache: NONE
```

Do not reserve or create `0015` merely for this derived result.

If implementation discovers a genuine missing persistent source primitive, stop and return for architecture review rather than silently adding storage.

---

## 15. Arithmetic discipline

All authored numeric policy values and all derived amounts use exact integer rational arithmetic.

Required:

- strict integers; bool/float/string rejected;
- positive denominator;
- gcd canonicalization;
- canonical zero;
- explicit signed-unit range for mapped amounts;
- exact cross-product ordering checks;
- no float conversion in comparison/multiplication/sum;
- no epsilon;
- no hidden clamp.

Input policy components should use bounded integer components consistent with existing source contracts. Intermediate computation may use arbitrary-precision integer arithmetic; because the expression has a fixed finite number of factors, implementation must reject maliciously oversized serialized policy components before arithmetic rather than truncate exact results.

The detailed implementation may adopt a derived structural bit-length guard, but it must be justified as a resource bound and must not change preference semantics or round values.

---

## 16. Minimum adversarial acceptance matrix

Implementation, if separately authorized later, must cover at least these categories with exact expected outcomes.

1. Same rational `1/2` in source coordinates does not auto-convert.
2. Wrong explicit policy ID rejects.
3. Wrong explicit policy version rejects.
4. Wrong explicit policy fingerprint rejects.
5. Compatibility row's expected explicit amount differing from the pinned 040B policy rejects.
6. Missing/duplicate explicit mapping row rejects.
7. Explicit mapped outputs not satisfying DISLIKE < NEUTRAL < LIKE reject.
8. Wrong reference coordinate ID/version/unit/applicability rejects.
9. Wrong provider ID/provider immutable identity rejects.
10. Multiple-provider aggregation/fallback is impossible by contract.
11. Empty or duplicate reference mapping rules are handled according to the complete policy shape; duplicate exact source values reject.
12. Reference mapping order inversion rejects.
13. Valid reference amount absent from finite map yields `PRIOR_VALUE_NOT_MAPPED`, not guessed conversion.
14. `NO_PUBLICATION` never synthesizes zero.
15. Prior `RETRACTED` never reuses historical amount.
16. Actual mapped `AVAILABLE 0/1` remains real available prior.
17. Explicit `UNDECLARED` never becomes declared NEUTRAL.
18. Explicit `RETRACTED` never collapses into UNDECLARED.
19. Member RETRACTED + available prior yields `UNAVAILABLE / MEMBER_RETRACTED` in v1.
20. DECLARED + mapped available prior yields exact blended result.
21. DECLARED + no publication yields explicit-only result with preserved reason.
22. DECLARED + retracted prior yields explicit-only result with preserved reason.
23. DECLARED + unmapped prior yields explicit-only result with preserved incompatibility reason.
24. UNDECLARED + mapped prior yields prior-only cold-start result with EvidenceStrength NONE.
25. UNDECLARED + unavailable/unmapped prior yields unavailable result, no neutral baseline.
26. Declared NEUTRAL mapping is not forced to output zero.
27. LOW/MEDIUM/HIGH are never parsed/used as probabilities.
28. Missing/duplicate shrinkage strength rules reject.
29. Invalid/noncanonical prior weights reject.
30. Active-declaration prior weight `1` rejects.
31. Monotonicity violation `LOW < MEDIUM` or `MEDIUM < HIGH` rejects.
32. Zero prior weight is valid and retains zero prior contribution in a compatible blend trace.
33. Stronger evidence never receives greater prior influence under the selected policy.
34. Exact blend arithmetic canonicalizes by gcd and never uses float.
35. Blend outside `[-1,1]` is treated as validation/arithmetic failure, never clipped.
36. Explicit request with zero or multiple targets rejects for this singleton slice.
37. Explicit target and reference target mismatch rejects.
38. Same UUID under a different target kind rejects.
39. New reviewed feature-term/version ID is an independent exact target; no alias reconciliation.
40. Forged cached explicit affinity/EvidenceStrength cannot be supplied as authority.
41. Forged cached prior result cannot be supplied as authority.
42. Forged mapped amount/weight/contribution/final result/fingerprint rejects or is independently recomputed.
43. Old coherent explicit source + old coherent reference source + same policies replays byte-deterministically.
44. Fresh prior source revision can change only the fresh consumer result; old immutable replay remains stable.
45. Different child capture timestamps remain deterministic and do not create simultaneous-liveness claims.
46. Later compatibility policy can reinterpret old snapshots only under a new policy fingerprint/version; old result replay unchanged.
47. Policy provenance after child capture is allowed only under `VERSIONED_CONSUMER_POLICY_REPLAY` and does not masquerade as AS_OF_CAPTURE knowledge.
48. Proposal-local 041 recipe/feature repeat data cannot enter this contract or alter affinity.
49. Cooking, out-of-stock, too-expensive, no-time, no-equipment and operational friction cannot enter this exact explicit/prior contract.
50. Forced conflict resolution cannot enter voluntary preference derivation.
51. Cross-target/hierarchical transfer is impossible by contract.
52. Cross-member aggregation/fan-out is impossible by contract.
53. Pure derivation performs zero DB/network IO and zero writes.
54. No migration `0015`; schema remains `0014 / 78`.
55. Frozen 040A/B, 041A-F, 046A and all 299 existing exported definitions remain structurally compatible.
56. Frozen reviewed-prior source contracts/hashes/migration0014 remain unchanged.
57. No production prior records or production policy numeric values are added.
58. `planner_ready=False` and `activation_ready=False` are immutable.
59. No hard-safety, validator or PRECOMMIT authority can be minted.
60. Canonicalization is deterministic under semantically unordered policy-row shuffles while preserving order where policy order is meaningful.

Real PostgreSQL tests are not intrinsically required for the pure arithmetic core, but the full regression suite must retain the existing real-PostgreSQL/SCRAM/source tests to prove that this additive consumer does not weaken frozen source enforcement.

---

## 17. Freeze/compatibility requirements for any future implementation

Any separately authorized implementation must be additive.

Must remain byte/semantic compatible:

- MTR-040A
- MTR-040B
- MTR-041A/B/C/D/E/F
- MTR-046A
- Canonical Reviewed Exact-target Preference Prior Source Foundation
- migrations `0001–0014`
- all 299 existing exported domain definitions

Do not edit frozen 040B classes so their old `prior` or `shrunk_affinity` fields suddenly become available. New capability belongs to new additive result types.

A future compatibility fixture should pin the 299 pre-existing definitions plus relevant frozen algorithm AST/hash receipts before adding new definitions.

---

## 18. Downstream status after this design

Even if this exact-target slice is later implemented and frozen:

- full MTR-040 remains incomplete until separately approved hierarchical and broader learned profile work exists;
- MTR-041 remains partial because accepted/confirmed/cross-horizon/family/global history is absent;
- MTR-046 remains partial beyond frozen A;
- MTR-024 remains blocked on broader separable utility inputs/policies and candidate projection/aggregation;
- MTR-020B remains blocked on 024 and role/exploration policy;
- MTR-021 remains blocked on 020B plus feasibility/validation prerequisites;
- Execution remains not started;
- PRECOMMIT remains fail-closed.

This design supplies one exact-target member-profile input coordinate. It does not create planner-ready utility.

---

## 19. Architecture review decisions required

Before implementation may be authorized, review must explicitly approve or correct:

1. the new `MEMBER_PROFILE_AFFINITY / v1` policy-linear output coordinate;
2. finite exact lookup rather than interpolation for the reference coordinate;
3. per-target-kind explicit and reference mappings;
4. exact provider binding with no fallback/aggregation;
5. the state matrix, especially `RETRACTED -> MEMBER_RETRACTED` even when a prior exists;
6. explicit-only fallback for an active declaration when prior is unavailable/incompatible;
7. prior-only cold-start for an undeclared target when a compatible prior exists;
8. exact EvidenceStrength-to-prior-weight policy and monotonicity;
9. convex exact-rational shrinkage algebra;
10. `VERSIONED_CONSUMER_POLICY_REPLAY` allowing retrospective policy interpretation without pretending AS_OF_CAPTURE knowledge;
11. recomputation from frozen child primitives rather than trusting cached child results;
12. zero persistence / no `0015`;
13. strict exclusion of hierarchy, learned evidence, candidate scoring and planner authority.

If any of these decisions is rejected, correct the design first. Do not implement around an unresolved semantic point.

---

## 20. Authorization boundary

This document is **design only**.

It authorizes no runtime change, no new contract export, no test addition, no migration, no production policy values, no MTR-040C assignment and no downstream milestone.

Stop at:

**READY FOR PRIOR COMPATIBILITY/SHRINKAGE DESIGN REVIEW — IMPLEMENTATION NOT AUTHORIZED**
