# Post Hierarchy-Source Freeze — Dependency & Readiness Review

Status: **USER POST-FREEZE REVIEW RECORDED — DEPENDENCY SELECTION PASS; MTR-040C DESIGN-READY;
RUNTIME IMPLEMENTATION NOT AUTHORIZED**.

This document records the user's supplied2026-10-27 review below. Its freeze declaration is
captured in the [canonical hierarchy SOURCE receipt](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_FREEZE_RECEIPT.md).
The bounded consumer is now assigned **MTR-040C — One-hop Hierarchical Member Preference Consumer
Foundation**, selected for detailed architecture/design. This is not an approved detailed consumer
contract and does not authorize runtime work. The source foundation remains separately frozen.

The repository confirmation after the supplied review records actual file inspections, limitations
of the existing navigation graph and the remaining detailed-design choices. No executable type,
export, migration or test is introduced by this documentation PR.


**Review date:** 2026-10-27

**Canonical repository:** `thedusk4203/Menuto`

**Reviewed main:** `ee8a4de1b1c71ccbd56ea565e111718660711fa8`

**Hierarchy SOURCE:** **FROZEN**

**Review verdict:** **PASS — PURE HIERARCHY CONSUMER IS READY FOR DETAILED DESIGN; IMPLEMENTATION NOT YET AUTHORIZED**

---

## 1. Executive decision

Freeze của Canonical Reviewed Hierarchical Preference Relation / Transfer-Policy SOURCE đã đóng blocker kiến trúc cuối cùng trước **pure hierarchy consumer**.

Repo hiện đã có đủ các primitive để thiết kế deterministic consumer:

| Dependency | State | Decision |
|---|---|---|
| 040A explicit member declaration/source | FROZEN | SATISFIED |
| 040B explicit target affinity + `EvidenceStrength` | FROZEN | SATISFIED |
| Reviewed exact-target prior source | FROZEN | SATISFIED |
| Exact-target prior compatibility/shrinkage — PR #100 | FROZEN | SATISFIED |
| 046A reviewed culinary classification | FROZEN | SATISFIED for hierarchy support/context |
| Hierarchy relation / transfer-policy SOURCE | FROZEN | **SATISFIED** |
| MTR-039 SignalAttributionRouter | OPEN | **NOT a prerequisite for bounded hierarchy consumer** |
| Additional MTR-041 slice | Not required | **NOT a prerequisite** |
| Pure hierarchy consumer | Missing | **NEXT DESIGN SLICE** |
| MTR-024 / 020B / 021 | Blocked | Remain blocked |
| Execution / PRECOMMIT | Not started / fail-closed | Unchanged |

Earlier dependency analysis explicitly selected a source-before-consumer decomposition and stated that no additional proposal-local 041 layer or MTR-039 implementation had to precede this bounded hierarchy branch.

The frozen source design now supplies the previously missing exact relation identity, transfer direction, mapping, attenuation, context support, lifecycle, complete capture, ambiguity handling and replay semantics.

**Therefore: the pure hierarchy consumer is DESIGN-READY.**

---

## 2. Recommended milestone assignment

The previous decision to keep `MTR-040C` unassigned was correct while prior semantics, hierarchy relation authority and transfer semantics were still unresolved.

Those prerequisites are now frozen.

I recommend assigning:

> **MTR-040C — One-hop Hierarchical Member Preference Consumer Foundation**

to the bounded consumer described below.

This is now a better fit for `040C` than the earlier exact-target prior slice because canonical MTR-040 is specifically about **MemberBehaviorProfile: hierarchical feature/direct affinity + evidence strength + explicit ownership**.

040A already owns durable member-authored declarations; 040B owns exact-target interpretation and explicit `EvidenceStrength`; PR #100 owns exact-target prior compatibility/shrinkage. The remaining bounded MTR-040 branch is precisely hierarchical member affinity.

This assignment must **not** mean “full MTR-040 complete”. Closure of parent issue #41 should have a separate post-040C review.

---

## 3. Exact MTR-040C boundary

MTR-040C should be a **pure consumer**, not another source.

Conceptually:

```text
Explicit member source
        ↓
frozen 040B derivation
        ↓
frozen PR #100 exact-target derivation
        ↓
             + complete frozen hierarchy source
             + exact relation
             + exact transfer-policy revision
             + classification/context support
        ↓
pure hierarchy consumer
        ↓
Inherited member preference suggestion
```

The output coordinate is already constrained by the frozen hierarchy design:

```text
coordinate_id = INHERITED_MEMBER_PREFERENCE
coordinate_version = 1
destination_target_kind
transfer_policy_semantic_fingerprint
unit = REVIEWED_TRANSFER_POLICY_UNITS
scope = ONE_TRANSFER_POLICY_ONE_DESTINATION_KIND_BOUND_EXACT_RELATION
```

It is explicitly distinct from 040B's direct affinity and PR #100's `MEMBER_PROFILE_AFFINITY`; it is not probability, utility, direct declaration or a globally comparable score.

No persistence is needed for the derived result.

**Expected schema after MTR-040C consumer implementation remains `0015 / 85 domain tables`.**

A new migration would require a separately discovered persistent source requirement and a new architecture review.

---

## 4. Parent eligibility is now settled

The consumer must not use PR #100's final blended amount as inheritable member evidence.

The frozen hierarchy architecture already establishes the rule:

| Parent state | Hierarchy behavior |
|---|---|
| Explicit declaration + PR #100 `EXPLICIT_ONLY` | Eligible |
| Explicit declaration + `BLENDED_EXPLICIT_AND_PRIOR` | Eligible, but use **mapped explicit operand only** |
| `PRIOR_ONLY_COLD_START` | **Ineligible as parent** |
| Parent `UNDECLARED` | No inheritable member evidence |
| Parent `RETRACTED` | Suppressed |
| Prior amount alone | Never inheritable |
| Previously inherited result | Never eligible as another parent |

This is important: a shared reference prior cannot be laundered through PR #100 and emerge as if it were member-specific evidence.

The source design explicitly freezes **one-hop only**, forbids inherited outputs from becoming parents and forbids transitive propagation.

---

## 5. Destination precedence is also settled

The consumer does not need to invent precedence policy.

| Destination member state | Required result |
|---|---|
| Direct `LIKE` | Direct declaration wins; inheritance suppressed |
| Direct `DISLIKE` | Direct declaration wins; inheritance suppressed |
| Direct `NEUTRAL` / explicit zero | Direct declaration wins; inheritance suppressed |
| `RETRACTED` | `MEMBER_RETRACTED`; inheritance blocked |
| `UNDECLARED` | May expose one inherited suggestion if every hierarchy gate passes |
| Prior-only exact-target value | Remains separate; no automatic blend with inherited suggestion |

This preserves ADR-011's rule that learned/inferred material cannot silently rewrite explicit user policy.

It also preserves `UNDECLARED != NEUTRAL != RETRACTED`.

---

## 6. EvidenceStrength decision

No new `EvidenceStrength` should be minted by hierarchy traversal.

Existing literals remain:

```text
NONE | LOW | MEDIUM | HIGH
```

The parent 040B result retains its original strength in provenance/lineage. The inherited suggestion itself does **not** receive a derived HIGH/MEDIUM/LOW simply because:

- a relation exists;
- a classification review exists;
- attenuation is high;
- multiple reviews support it;
- the parent has been seen repeatedly;
- a path is short;
- the recipe was cooked repeatedly.

Hierarchy mapping is interpretation, not new observed evidence.

That is consistent with ADR-011's separation of explicit, inferred and passive evidence classes, and its rule that explicit policy must not be silently rewritten.

No `EvidenceStrength` propagation formula is needed for MTR-040C v1.

---

## 7. Mapping and arithmetic boundary

The consumer should consume the exact mapping selected by the frozen transfer policy.

Sequence:

```text
validate/recompute parent
        ↓
verify exact member + source PreferenceTarget
        ↓
verify exact destination PreferenceTarget
        ↓
resolve complete hierarchy source
        ↓
require exactly one eligible incoming relation
        ↓
lookup exact semantic mapping row
        ↓
mapped inherited amount
        ↓
× exact authored attenuation
        ↓
InheritedMemberPreference
```

Mapping happens before attenuation.

Attenuation must remain:

```text
0 < attenuation <= 1
```

No sign reversal, amplification, interpolation, nearest-neighbor fallback, implicit zero or hidden reuse of PR #100's prior influence weight is allowed.

`NEUTRAL → 0/1` remains the semantic anchor inherited from the frozen source correction.

---

## 8. Multi-parent and graph behavior

No new aggregation design is required for MTR-040C v1.

The SOURCE already freezes:

```text
one hop
single usable incoming parent
no recursive propagation
no favorable-parent selection
no averaging
no sum
no max
no voting
no strongest/newest winner
no diamond double-count
```

Two active incoming relations yield:

```text
MULTIPLE_INCOMING_RELATIONS
```

and therefore no inherited amount.

This restriction is desirable for 040C because it allows hierarchy interpretation to become executable without prematurely designing a general graph-ranking or multi-parent preference algebra.

---

## 9. Input authority and tamper resistance

MTR-040C must not accept caller-computed child outputs as authority.

In particular, these are insufficient by themselves:

```text
ScopedMemberProfileAffinity
ELIGIBLE_RELATION
mapped amount
attenuated amount
child result fingerprint
```

The consumer needs the underlying frozen primitives and must recursively recompute:

```text
040B explicit derivation
PR #100 exact-target derivation
hierarchy source validation/resolution
transfer lookup
attenuation
```

before returning the final suggestion.

This follows the hierarchy source's explicit downstream-consumer seam: the complete captured source plus exact member/source/destination primitives must be supplied; a naked caller relation policy or pre-resolved eligible relation is insufficient.

The computation remains **zero DB IO / zero writes**.

---

## 10. Capture and provenance

MTR-040C does not need to invent a single global transaction spanning every source.

The existing sources have distinct authority/capture cuts.

A valid result can therefore bind, for example:

```text
explicit/member cut A
reference-prior cut B
exact-target consumer policies C
hierarchy source cut D
classification/support cuts contained in D
```

The output fingerprint must retain those inputs and provenance.

It may claim:

> deterministic interpretation of these immutable inputs

but must not claim:

> all underlying authorities/data were simultaneously current at one instant.

This matches the earlier exact-target dependency review's accepted mixed-cut replay model.

---

## 11. MTR-039 readiness

**Do not start MTR-039 merely to unblock 040C.**

MTR-039 owns:

```text
DIRECT / CONTEXTUAL / INFERRED / PASSIVE
→ taste / context / exposure / retail / no-learn
```

Its canonical issue remains open.

040C does not ingest new cooking, rejection, execution, retail or behavioral events. Its parent member evidence is already the frozen explicit declaration branch.

MTR-039 becomes necessary when Menuto starts deriving/updating preference from **new behavioral observations**, not when it interprets an already-frozen direct declaration through a reviewed one-hop relation.

---

## 12. Production-policy/content caveat

The hierarchy SOURCE foundation intentionally seeds:

```text
0 providers
0 grants
0 relations
0 enabled directions
0 production mapping rows
0 production attenuation values
```

Therefore a future 040C implementation may be architecturally complete while returning no production inherited suggestion until separately reviewed production policies/relations are actually published.

That is acceptable for a **foundation slice**, just as the reviewed prior consumer can exist while the production prior corpus remains empty.

It does mean:

> successful framework implementation must not be presented as evidence that production hierarchical taste coverage exists.

---

## 13. Documentation drift discovered

There is one governance/documentation issue after the freeze.

Current `main` documentation still contains the pre-freeze statement:

> “Source readiness requires implementation review/freeze … 040C NOT ASSIGNED / NOT AUTHORIZED.”

That wording appears in the blueprints/status/backlog/invariant coverage because the freeze was declared after merge.

This is **not a semantic blocker for beginning the MTR-040C design**, because the user freeze declaration supersedes that review-stage status.

It **should be corrected before runtime implementation authorization** so future reviews do not have two conflicting canonical status records.

Recommended documentation action is a post-freeze receipt/review recording:

```text
Hierarchy SOURCE = FROZEN
MTR-040C = selected next bounded consumer design
implementation = NOT AUTHORIZED
```

No runtime change is required for that cleanup.

---

## 14. Downstream readiness after this review

| Workstream | Current state |
|---|---|
| Hierarchy SOURCE | **FROZEN** |
| MTR-040C pure consumer | **READY FOR DETAILED DESIGN** |
| MTR-040C runtime | **NOT AUTHORIZED YET** |
| Full MTR-040 | **PARTIAL** |
| MTR-039 | OPEN; not prerequisite for bounded 040C, required for broader learned preference |
| Full MTR-041 | PARTIAL |
| Full MTR-046 | PARTIAL |
| MTR-024 | **BLOCKED** |
| MTR-020B | **BLOCKED** |
| MTR-021 | **BLOCKED** |
| Execution | NOT STARTED |
| PRECOMMIT | FAIL-CLOSED |
| `planner_ready` | `False` |
| `activation_ready` | `False` |

MTR-024 must not start merely because hierarchical affinity becomes available. It still lacks the reviewed composition/projection/aggregation seam for converting member-level components into candidate-level separable utility, and broader history/profile inputs remain incomplete.

020B consequently remains behind 024, and 021 remains behind 020B.

---

## 15. Parent MTR-040 closure rule

Do **not** automatically close issue #41 when 040C is eventually frozen.

Canonical MTR-040 acceptance requires hierarchical feature/direct affinity, evidence strength and explicit ownership.

040A/B + 040C would cover those core mechanics substantially, but repository architecture also describes a broader MemberBehaviorProfile that eventually receives properly attributed learned observations.

Therefore after 040C freeze, perform a dedicated:

> **Post-MTR-040C Parent MTR-040 Completion Review**

That review should decide whether issue #41's canonical acceptance is satisfied by the explicit/prior/hierarchy foundation or whether MTR-039-backed learned-profile integration is required before closing it.

Until that review:

**MTR-040 remains PARTIAL.**

---

# Final verdict

**POST-FREEZE DEPENDENCY REVIEW: PASS.**

**Selected next slice:**

> **MTR-040C — One-hop Hierarchical Member Preference Consumer Foundation**

**Readiness:**

> **READY FOR DETAILED ARCHITECTURE/DESIGN**

**Not authorized by this review:**

> runtime implementation, new migration, production transfer values, multi-parent aggregation, recursive hierarchy, MTR-039 implementation, TasteFit, MTR-024, MTR-020B, MTR-021, Execution or PRECOMMIT.

The correct next gate is:

> **MTR-040C PURE HIERARCHY CONSUMER DESIGN REVIEW — IMPLEMENTATION NOT AUTHORIZED**

Điểm quan trọng nhất là **giờ đã đủ điều kiện gán `MTR-040C` cho pure hierarchy consumer**; không cần chèn thêm một source milestone hay MTR-039 ở giữa. Tôi cũng phát hiện status docs trên `main` đang lệch một bước vì vẫn ghi SOURCE “awaits freeze”; phần đó nên được cập nhật cùng receipt của dependency review trước khi cấp quyền implementation.

## Repository confirmation and detailed-design handoff

Confirmed against exact `ee8a4de1b1c71ccbd56ea565e111718660711fa8` before documentation edits.
GitHub main matched that SHA; push [CI40432057006](https://github.com/thedusk4203/Menuto/actions/runs/40432057006)
was SUCCESS on that exact SHA, with python/web SUCCESS. Schema0015 /85,349 definitions and the
2807-test baseline remain the implementation baseline; this PR changes Markdown only.

| Inspected canonical source | Confirmed capability / design consequence |
| --- | --- |
| [ADR-011](../adr/ADR-011-behavioral-learning-loop.md); [INV-022–030](../ARCHITECTURE_INVARIANTS.md) | Member ownership; independent affinity dimensions; evidence-class separation; no passive durable learning, cooked=liked or friction=taste; explicit policy cannot be silently rewritten. Canonical wording is untouched. |
| [040A/B contracts](../../apps/backend/app/modules/preferences/contracts.py), [040B derivation](../../apps/backend/app/modules/preferences/profile_derivation.py), [capture](../../apps/backend/app/modules/preferences/profile_capture.py) | Exact typed identity and raw semantic declaration; current-head strength. Frozen explicit amounts are policy-local; NEUTRAL need not be numeric zero. |
| [PR #100 contracts](../../apps/backend/app/modules/preferences/prior_affinity_contracts.py), [runtime](../../apps/backend/app/modules/preferences/prior_affinity.py), [freeze receipt](EXACT_TARGET_PRIOR_SHRINKAGE_FREEZE_RECEIPT.md) | A complete input covers exactly one identical target in explicit/reference sources. Recomputed mapped_explicit is separate from blended effective, prior operand and contributions. Source/member identity is retained outside the descriptor. |
| [Reference-prior source contracts](../../apps/backend/app/modules/preferences/reference_prior_contracts.py), [replay](../../apps/backend/app/modules/preferences/reference_prior_resolution.py), [freeze receipt](PREFERENCE_PRIOR_SOURCE_FREEZE_RECEIPT.md) | Distinct global reference authority, complete capture/history and pure replay; reference truth is not member evidence or hierarchy permission. |
| [Hierarchy contracts](../../apps/backend/app/modules/preferences/hierarchy_contracts.py), [source interface](../../apps/backend/app/modules/preferences/hierarchy_sources.py), [replay](../../apps/backend/app/modules/preferences/hierarchy_resolution.py), [models](../../apps/backend/app/modules/preferences/hierarchy_models.py), [migration0015](../../apps/backend/migrations/versions/0015_reviewed_hierarchy_source.py) | Separate publication/capture authority, exact support/context pins, complete histories, semantic map and deterministic per-destination eligibility. Source output explicitly says member_affinity/evidence_strength NOT_DERIVED. |
| [Frozen hierarchy design §§7–11](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_DESIGN.md), [neutral correction](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_NEUTRAL_ANCHOR_CORRECTION.md) | Distinct inherited coordinate; mapping-before-attenuation; one-hop; direct/retracted destination precedence; explicit-only parent operand; no strength propagation; mixed-cut replay limitations. |
| [Catalog contracts](../../apps/backend/app/modules/catalog/contracts.py), [Recipes contracts](../../apps/backend/app/modules/recipes/contracts.py), [feature resolution](../../apps/backend/app/modules/recipes/feature_resolution.py), [046A evidence](MTR_046A_IMPLEMENTATION_EVIDENCE.md) | Reviewed support is food truth. RecipeVersion/applicability/path and MAIN_PROTEIN support remain frozen owner semantics, not automatic permission or target selection. |
| [Learning contracts](../../apps/backend/app/modules/learning/contracts.py), [feature repeat](../../apps/backend/app/modules/learning/feature_repeat.py), [041F evidence](MTR_041F_FEATURE_REPEAT_POLICY_EVIDENCE.md) | Proposal-local exposure/repeat does not provide member evidence or global history; another041 slice is not on this bounded consumer's prerequisite path. |
| [Planning contracts](../../apps/backend/app/modules/planning/contracts.py), [shortlist](../../apps/backend/app/modules/planning/shortlist.py), [backlog](BACKLOG.md) | Existing supply-path shortlist is not participant utility composition.024 remains blocked;020B remains behind024 and021 behind020B. Freeze does not close issue #41. |

The actual source resolution order remains: full-history validation → selected policy state →
active incoming-head count → withdrawal/absence → policy pin/direction → support. G02 counts active
heads **before** member values or favorable support filtering. An unresolved competing parent
cannot be dropped to manufacture one usable parent. Parent eligibility never overrides this gate.

Two interface details must be made explicit in the next detailed design, without modifying any
frozen source:

1. **Semantic key and numeric coordinate are separate checks.** Frozen
   `HierarchyTransferMapRow.expected_source_amount` is the raw frozen040B explicit-rule amount;
   `source_descriptor` identifies the pinned PR #100 compatibility coordinate. The consumer must
   recompute040B and PR #100, verify the raw semantic/expected-amount pair, verify the complete
   compatibility policy/descriptor and its mapped_explicit operand, then perform the frozen
   semantic-row lookup. It must never compare that raw expected amount directly with a mapped
   scalar, infer the semantic key from either sign, or substitute the blended effective amount.
   This is a clarification of the existing correction/interface, not a changed mapping policy.
2. **Per-target children and capture cuts remain explicit.** PR #100 accepts one target per input;
   a two-endpoint consumer must compose complete per-target frozen inputs rather than widen or
   slice that frozen contract. The detailed design must define validation/order/diagnostics for
   the exact same household/member, target identities, policy bindings and supplied member cuts.
   Each capture retains its own identity; no simultaneous-live or canonical-database-origin
   guarantee follows from a composite fingerprint. Output must bind the exact relation/context
   externally as well as its inseparable inherited descriptor.

These are detailed-design tasks, not missing durable primitives or reasons to insert another source
milestone. No incompatibility requiring modification of frozen040A/B,041A–F,046A, PR #100 or the
hierarchy source was found. Output contract shape, reason precedence, exact replay traces, primitive
tamper acceptance cases and the bounded128-bit product representation still need detailed design
approval before implementation. Use the frozen full transfer-policy fingerprint; do not invent a
different semantic-only hash or silently default to another policy/provider.

Navigation note: the existing graph has484 nodes and returned10 navigation nodes for the selected
vocabulary `preference hierarchical member affinity evidence strength policy source learning exposure`
under a1200-token query budget. It points to ADR/spec seams, not the newly frozen source implementation.
No graph rebuild or LLM extraction was performed (0 extraction tokens). Capability claims above
come from the actual canonical files, not inferred graph edges; stale graph contents confer no
implementation authority.

## Documentation delivery boundary

This PR records the source freeze and this dependency/readiness verdict, assigns040C to the bounded
consumer design and reconciles current status documents. The complete supplied review is retained
above. The detailed consumer design belongs to the next dedicated design PR; it is not silently
approved by recording this review. The existing source implementation evidence remains a historical
receipt; the canonical freeze receipt supersedes only its former delivery status.

No runtime, executable contracts, tests, fixtures, schema exports, migrations, production policy data,
canonical ADR/invariant wording or issue closure is changed. Source0015/85 and349 definitions remain.
MTR-039 is not a bounded040C prerequisite; broader learned-profile work still needs its own attribution
and evidence sources. No additional041,024/020B/021, Execution or PRECOMMIT work is authorized.

**MTR-040C PURE HIERARCHY CONSUMER DESIGN REVIEW — IMPLEMENTATION NOT AUTHORIZED**
