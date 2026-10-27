# Hierarchical Preference Relation / Policy Source — Neutral Anchor Correction

Status: **DESIGN APPROVED — SOURCE IMPLEMENTATION AUTHORIZED; IMPLEMENTATION REVIEW PENDING**.

Current authorization: the user approved this design/correction pair at canonical
`4ad3f682554b7feee9f333eca1f1f5c258852f5e` and authorized SOURCE ONLY implementation,
including additive0015. See [implementation evidence](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_IMPLEMENTATION_EVIDENCE.md).
The implementation PR remains OPEN / NOT MERGED; source readiness awaits review/freeze.
Pure consumer, MTR-040C and downstream work remain unauthorized. The original review-stage
baseline, delivery receipts and stop statements below are historical; no approved semantic
requirement is relaxed. The correction supersedes only stricter finite-map semantics.


Reviewed against canonical `main`:

`16454439c4a628de9473374cbd62c2d278a5b958`

This document corrects one semantic blocker in the merged design
`HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_DESIGN.md`. It does not widen authority, authorize runtime work, reserve a migration, assign MTR-040C, or change any frozen runtime semantics.

## 1. Problem

The merged source design defines a future inherited coordinate in which negative / zero / positive mean negative / balanced / positive inherited suggestion, while the finite transfer mapping only requires ordered mapped outputs.

That is insufficient because frozen 040B deliberately does **not** define a universal numeric anchor such as `NEUTRAL=0`. A valid explicit policy may encode DISLIKE, NEUTRAL and LIKE as any strictly ordered exact rationals in its own policy coordinate.

Therefore the hierarchy transfer source must bind **semantic declaration state** in addition to the exact expected source amount. Numeric sign in the frozen source coordinate is not an authority substitute for semantic LIKE / DISLIKE / NEUTRAL.

Without this correction a formally monotonic map such as:

```text
DISLIKE -> +1/10
NEUTRAL -> +2/10
LIKE    -> +3/10
```

would satisfy ordering but would mint a positive inherited suggestion from a member's explicit NEUTRAL declaration. That would inject a global bias / prior into transfer policy instead of preserving member-authored valence.

## 2. Corrected finite-map row semantics

A transfer-policy mapping row must be semantically equivalent to:

```text
source_descriptor
source_affinity_value = DISLIKE | NEUTRAL | LIKE
expected_source_amount
output_amount
```

The exact exported contract names remain implementation work and are not reserved by this correction.

The hierarchy source must pin the complete frozen explicit interpretation policy body/fingerprint and revalidate the semantic row against that policy. A caller-supplied label or amount cannot establish the pair.

For each row:

```text
(source_affinity_value, expected_source_amount)
```

must exactly match the corresponding frozen explicit-policy rule for the source target kind. A forged semantic label paired with a valid amount from another row must reject.

The future consumer continues to use only the recomputed mapped-explicit operand from the frozen member source. Blended effective prior-backed values, prior-only cold start and inherited values remain ineligible hierarchy parents.

## 3. Semantic anchor invariants

For every enabled direction and every authored row:

```text
source NEUTRAL
    => mapped output == 0/1

source DISLIKE
    => mapped output <= 0

source LIKE
    => mapped output >= 0
```

For a mapping containing all three semantic states, strict ordering therefore implies:

```text
mapped(DISLIKE) < 0
mapped(NEUTRAL) = 0
mapped(LIKE)    > 0
```

A real mapped `0/1` is an **AVAILABLE balanced inherited suggestion**, not missingness, denial, retraction, unresolved support or source absence.

A semantic state may be intentionally absent from a finite map. Absence means `SOURCE_VALUE_NOT_MAPPED`; it must never synthesize zero, neutral, a default mapping or a nearest row.

Attenuation is applied only after semantic mapping and therefore preserves the anchor:

```text
0 * attenuation = 0
```

with exact rational arithmetic. Attenuation still satisfies the existing source design's positive bounded coefficient rule and cannot reverse sign or amplify magnitude.

## 4. No hidden use of source numeric sign

Do **not** infer member semantic state from the sign of `ExplicitAffinityAmount` or any later mapped numeric amount.

Frozen 040B defines only semantic row identity plus strict policy-local ordering:

```text
DISLIKE < NEUTRAL < LIKE
```

It intentionally does not impose:

```text
NEUTRAL = 0
LIKE = +1
DISLIKE = -1
symmetry
```

The hierarchy source therefore must carry and verify the semantic row key explicitly.

## 5. Anti-correlation remains out of scope

This correction preserves V1 hierarchy as **valence-preserving inheritance**.

A relation such as:

```text
LIKE source A -> negative suggestion for destination B
```

must not be encoded by silently flipping sign in the finite map.

If a future product need requires complement / substitution / anti-correlation semantics, that requires a separately reviewed relation semantic/type, coordinate meaning, precedence and acceptance model. It is not an optional mapping trick inside this foundation.

No such anti-correlation relation type is authorized here.

## 6. Authority guardrail

Hierarchy publication may pin and independently revalidate frozen 040B / PR #100 policy bodies and fingerprints **for hierarchy-source compatibility and replay only**.

It does not become the canonical publisher, owner or production authority for those frozen policies outside this hierarchy source.

In particular:

```text
hierarchy publisher reviewed/pinned compatibility policy X
!= hierarchy publisher owns policy X globally
!= policy X becomes a default for other consumers
!= policy X becomes a production prior
```

Frozen policy ownership and all existing source authorities remain unchanged.

## 7. Required acceptance additions

A later source implementation must add independent/adversarial evidence for at least:

| ID | Required behavior |
| --- | --- |
| H01 | `NEUTRAL -> nonzero` mapped output rejects the policy. |
| H02 | `DISLIKE -> positive` mapped output rejects the policy. |
| H03 | `LIKE -> negative` mapped output rejects the policy. |
| H04 | A frozen source rational may be numerically positive while its semantic row is NEUTRAL; semantic NEUTRAL wins and output must still be `0/1`. |
| H05 | Forged `source_affinity_value` paired with the amount belonging to another frozen explicit-policy row rejects, even if the outer policy is re-hashed. |
| H06 | Correct semantic label with the wrong `expected_source_amount` rejects. |
| H07 | `NEUTRAL -> 0/1` is a valid AVAILABLE mapped value and remains distinct from missingness/unavailability. |
| H08 | An intentionally omitted semantic state returns `SOURCE_VALUE_NOT_MAPPED`; no default zero/neutral or nearest-match behavior. |
| H09 | Hierarchy publication/review of pinned frozen compatibility policy does not grant global publication/ownership/default authority for that policy outside the hierarchy source. |

These are additive to the source design's existing A/I/C/L/G/R/S acceptance categories.

## 8. Unchanged decisions

This correction does **not** change:

- separate hierarchy authentication/enrollment/grant trust root;
- provider-scoped publication/retraction/capture authority;
- full 5x5 default-deny direction matrix;
- exact typed source/destination relation identities;
- explicit DIRECT_RECIPE RecipeVersion/context bindings;
- classification fact != preference-transfer permission;
- finite exact lookup only;
- explicit exact rational attenuation;
- append-only policy/relation lifecycle, CAS, idempotency and tombstones;
- current authorization check before idempotent retry receipt lookup;
- complete coherent capture and primitive replay;
- policy supersession requiring explicit relation repinning;
- one-hop only;
- inherited values cannot become parents;
- no multi-parent aggregation;
- exact member/household binding;
- active direct declaration/retraction precedence at destination;
- no EvidenceStrength minting/upgrading/mutation;
- no learned/contextual/passive evidence;
- no TasteFit/planner/safety/Execution/PRECOMMIT authority;
- `planner_ready=False` and `activation_ready=False`;
- source/consumer implementation NOT AUTHORIZED;
- MTR-040C NOT ASSIGNED / NOT AUTHORIZED;
- migration `0015` NOT RESERVED / NOT AUTHORIZED.

## 9. Design status after correction

If this correction is approved, it is normative together with the merged
`HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_DESIGN.md` and supersedes only that document's finite-map semantics where the older text is less restrictive.

No runtime/contracts/tests/fixtures/generated schemas/migrations or production policy values are modified by this documentation-only correction.

**READY FOR HIERARCHICAL PREFERENCE RELATION/POLICY SOURCE ARCHITECTURE RE-REVIEW — IMPLEMENTATION NOT AUTHORIZED**
