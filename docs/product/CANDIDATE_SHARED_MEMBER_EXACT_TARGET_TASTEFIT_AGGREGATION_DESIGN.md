# Candidate-bound Shared-member Exact-target TasteFit Compatibility & Aggregation Foundation

Status: **DESIGN READY FOR ARCHITECTURE REVIEW — IMPLEMENTATION NOT AUTHORIZED**.
Design only, 2026-10-28. No MTR suffix assigned. No runtime, contract, test, tool, migration or data
implementation is included. This proposal consumes frozen children without changing their semantics.

## 1. Approved entry gate and exact baseline

| Receipt | Verified value |
| --- | --- |
| Repository / design base | `thedusk4203/Menuto`, main `7dcb0b1b9b7f35b80b3f86c24064c920f1d8a2ec` |
| Approved dependency review | [PR #118](https://github.com/thedusk4203/Menuto/pull/118), exact head `67a2b05e804f32082233cad6ff46f89e73f84b3d`; [formal PASS6469738543](https://github.com/thedusk4203/Menuto/pull/118#issuecomment-6469738543) |
| Immediate pre-merge verification | OPEN /MERGEABLE /CLEAN; same one commit and one Markdown file; exact-head CI40689482722 SUCCESS; no unresolved technical blocker |
| Actual merge / verified main | `7dcb0b1b9b7f35b80b3f86c24064c920f1d8a2ec`; parents `4e660d18ce636fa0bd4556141f3cc3aa358d3670` and approved head above |
| Reviewed / merged tree | `c0a043bb9ea0bb2b8cb91c2daba8e4ddf999e398`, identical; only the approved review document changed |
| Exact post-merge push CI | [40693646450](https://github.com/thedusk4203/Menuto/actions/runs/40693646450), event=push /exact merge SHA; SUCCESS, Python/web and every required step SUCCESS |
| Baseline receipt | **3,396 passed /0 skips**; SCRAM/TLS16/16; benchmark22/22; client10/10; architecture/import/lint/export/fixtures/contracts/typecheck/build green |
| Exports / schema / persistence | **384 /0015 /85 domain tables /ZERO NEW PERSISTENCE**; no0016 |
| Verified gate | [Post-merge receipt6470394467](https://github.com/thedusk4203/Menuto/pull/118#issuecomment-6470394467); main re-fetched after CI and unchanged |

Merge used an exact-head guard, without auto-merge. The implementation freeze remains
[PR #116](https://github.com/thedusk4203/Menuto/pull/116) at
`7ac0547b3df621fb19c614c27edaca268a901169`; [PR #117](https://github.com/thedusk4203/Menuto/pull/117)
at `4e660d18ce636fa0bd4556141f3cc3aa358d3670` synchronized its FROZEN status.
Those identities do not become the design base. This design began only after the separate user
authorization and the successful PR118 push gate. A documentation merge is not design approval.

## 2. Requirements, inspected interfaces and preserved ownership

Canonical requirements: [V1.3](../MENUTO_DEVELOPMENT_SPEC_V1_3.md) §8.4 seam4, §9.2–9.5,
§14.10, §19.3–19.8; [INV-001..030](../ARCHITECTURE_INVARIANTS.md), especially003/004/009/017/018/
022–029; [ADR-004](../adr/ADR-004-household-first-model.md),
[ADR-011](../adr/ADR-011-behavioral-learning-loop.md) and
[ADR-010](../adr/ADR-010-independent-validator.md).

Inspected current source: [TasteFit contracts](../../apps/backend/app/modules/planning/tastefit_contracts.py),
[pure interpreter](../../apps/backend/app/modules/planning/tastefit.py),
[capture](../../apps/backend/app/modules/planning/tastefit_capture.py),
[public interface](../../apps/backend/app/modules/planning/tastefit_public.py),
[candidate projection contracts](../../apps/backend/app/modules/planning/contracts.py),
[projection replay](../../apps/backend/app/modules/planning/candidate_feature_projection.py),
[Preferences companion replay](../../apps/backend/app/modules/preferences/tastefit_public.py),
[companion transport](../../apps/backend/app/modules/preferences/tastefit_contracts.py),
[MealParticipants](../../apps/backend/app/modules/households/contracts.py),
[TF real PostgreSQL cases](../../apps/backend/tests/test_postgres_candidate_member_tastefit.py).
The [approved child design](CANDIDATE_MEMBER_TASTEFIT_FOUNDATION_DESIGN.md),
[freeze receipt](CANDIDATE_MEMBER_TASTEFIT_FOUNDATION_FREEZE_RECEIPT.md) and
[approved dependency review](POST_CANDIDATE_MEMBER_TASTEFIT_NEXT_GATE_REVIEW.md) remain unchanged
except for a subsequent-gate status notice on the dependency review.

Planning owns this new consumer/reduction Module and canonical coordination. Preferences owns
member preference truth and frozen interpretation; Household owns participant identity/context;
Recipes/Catalog own factual targets; Learning owns attributed events and exposure interpretation.
No preference is copied, published or written. Shared is not a new preference owner.

## 3. Exact scope and non-goals

**One canonical candidate × one exact typed preference target × its exact participating member set.**
Supported kinds are INGREDIENT /DIRECT_RECIPE /PROTEIN /METHOD /FLAVOR, as frozen. MAIN_PROTEIN
is factual evidence for PROTEIN, not a sixth preference kind. A result is a conditional shared
interpretation of that single target, not a whole dish, meal or household preference score.

The new operation may compare/reduce member-bound child coordinates only through the explicit
compatibility rules below. It does not relax a child's own equality/comparison restrictions.
Children retain aggregate/shared_member_aggregation/candidate_comparison=NOT_PERFORMED; the new
operation is in an additive enclosing result, not a mutation of those frozen outputs.

Non-goals: cross-target/kind reduction; whole-candidate scalar; full shared-meal utility;
cross-candidate ranking; shared RepeatPenalty; history/novelty; MTR-039 evidence; new hierarchy or
EvidenceStrength; hard safety/feasibility; planner utility/activation; production/default policy
selection; global policy publication; HTTP endpoints; persistence/cache/materialized profiles.

## 4. Chosen Module and three-operation Interface

All proposed files are under `apps/backend/app/modules/planning/`; none is created by this PR.

| Proposed Module | Responsibility |
| --- | --- |
| `shared_target_tastefit_contracts.py` | Immutable new request/policy/source/result transport and exact rational shapes; frozen Planning/Household contracts plus neutral transport primitives, no Preferences internals |
| `shared_target_tastefit_capture.py` | Fresh authenticated cohort capture using caller-owned sessions and the frozen public child capture/derive Interface |
| `shared_target_tastefit.py` | Pure full child replay, cohort coherence, compatibility, coverage, finite bridges, reduction and complete semantic validation |
| `shared_target_tastefit_public.py` | Small external Interface; lazily imports the capture Adapter, exposing only the three operations below |

```text
capture_shared_member_target_tastefit_sources(sessions, request, *, actor_user_id)
    -> SharedMemberTargetTasteFitSources
derive_shared_member_target_tastefit(sources)
    -> SharedMemberTargetTasteFitDraft
validate_shared_member_target_tastefit(result)
    -> freshly recomputed SharedMemberTargetTasteFitDraft
```

Tests cross the same Interface. There is no public bare-rational reducer, arbitrary child callback,
policy factory, registry lookup or generic household-scoring Interface. No new Preferences
companion/private import is needed: Planning consumes frozen Planning TasteFit public/contracts.
Existing cross-context restrictions remain unchanged. Future implementation may add narrowly named
pure/transport guards and additive export registration, never broaden old allowlists or models.

## 5. Request, exact participants and child construction

`SharedMemberTargetTasteFitRequest` requires:

- contract_version=`candidate-shared-member-target-tastefit-request.v1`;
- one common frozen CandidateFeatureProjectionRequest, including its exact expected grounding pin;
- household_id and one exact PreferenceTarget; no caller `target_present` flag;
- one `SharedTasteFitMemberInput` per canonical participant: member_id, full frozen child TasteFit
  policy with expected id/version/body-fingerprint pins, and full frozen member interpretation plan;
- explicit aggregation policy with independent expected id/version/body-fingerprint pins;
- projection_mode=FRESH_CANONICAL_CHILD_CAPTURE; no cached children accepted at canonical ingress.

The participant authority is the **entire MealParticipants in the freshly re-grounded canonical
candidate**, not a separate caller-selected list. All member-input keys and policy weight keys must
equal that set exactly, before member reads/arithmetic. Duplicates, omissions, extras, empty sets,
foreign household/member identity or tracked-only substitution reject. Preserve nutrition_role,
portion_factor, tracked_member_id and full grounding context as identity, never taste coefficients.

Each child request is constructed deterministically from the common projection request, the exact
member's supplied policy/interpretation pins, and diagnostic_targets=(the one outer target,).
Do not accept an independent child candidate/participant/target selector. Frozen children still
enumerate and retain **all** candidate base rows before filtering; the outer target does not trim
their source/history or add feature facts to an uncaptured dimension. Parent-only targets stay lineage.

The chosen target must have a canonical owner identity. Nonexistent identity is an error. A known
absent/unresolved target can produce explicit unavailable diagnostics, never a positive contribution.
Numeric contributions require its recomputed child proof to be BASE/PRESENT and policy-admitted.
All children retain exact household/member/candidate/target, child policy body/pins, source descriptor,
source mode/semantic state/direct signal, missingness, complete sources and unselected lineage.

## 6. Explicit conditional policy and finite compatibility model

`SharedMemberTargetTasteFitPolicy` is immutable/extra-forbid and has no numeric defaults:

| Required field | V1 decision |
| --- | --- |
| contract_version | `candidate-shared-member-target-tastefit-policy.v1` |
| policy_id /policy_version /provenance | Authored identity; USER or REVIEWED_REFERENCE metadata; neither grants publication authority |
| interpretation_mode | VERSIONED_CONSUMER_POLICY_REPLAY |
| target_kind | Exactly the request's one supported kind |
| participant_scope | EXACT_CANONICAL_PARTICIPANTS |
| compatibility | FINITE_PINNED_CHILD_MAPPING_BRIDGES |
| policy_admissions | Nonempty finite complete frozen child policy bodies, each with expected id/version/fingerprint pins |
| bridge_rules | Nonempty finite exact rules as defined below; no implicit identity conversion |
| member_weights | One strictly positive canonical rational explicitly authored for every participant ID |
| operator | EXACT_POSITIVE_WEIGHTED_MEAN, explicitly supplied; the only permitted V1 reducer |
| incomplete_coverage | WITHHOLD_AGGREGATE; no omit/zero/renormalize strategy |
| direct_signal_effect | RETAIN_SEPARATELY_NO_IMPLICIT_VETO_OR_WEIGHT |
| evidence_strength_effect | LINEAGE_ONLY |
| resource limits | Required positive max_members, max_policy_bytes, max_source_bytes, max_result_bytes, max_integer_bits; no production values |

Admissions reject duplicate (policy_id,policy_version), duplicate body identity or contradictory
pins. This is uniqueness **inside this authored policy**, not a global version registry. Each full
child body must validate under the frozen contract, admit target_kind and match its local pins.
An independently valid child with a different/unadmitted body is ordinary POLICY_INCOMPATIBLE,
not a license to fall back; a forged child's own pins/semantics are an invalid input instead.

Each `SharedTasteFitBridgeRule` requires a stable rule_id, exact admitted child-policy key,
target_kind, the **complete frozen TasteFitMappingRow**, exact direct_signal, and an explicitly
authored `mapped_amount` in the new common shared-target units. The frozen row includes source_mode,
semantic_state, full discriminated source_coordinate, canonical source_amount and child fit_amount.
It must occur exactly in that admitted body's kind policy; root-policy malformed/detached rules reject.
Duplicate semantic keys or rule IDs reject. Canonical equivalent fractions cannot hide duplicates.
Impossible direct/mode combinations also reject: RAW_EXPLICIT/EXACT_TARGET_EFFECTIVE require the
corresponding DECLARED_LIKE/DISLIKE/NEUTRAL matching the mapping semantic; PRIOR_ONLY requires
NO_DECLARATION/NONE; ONE_HOP_INHERITED requires the parent LIKE/DISLIKE/NEUTRAL semantic and
destination direct_signal=NONE. These rules preserve the frozen child selection model.

Match the recomputed child row's full policy body/id/version/fingerprint, exact current mapping row,
source descriptor/mode/semantic state and direct signal, after its complete TasteFitCoordinate binds
the expected household/member/candidate/target. Member IDs may differ **only as the specifically
bound contributor slots**; this is the new policy's explicit permission, not descriptor erasure.
Each selected bridge retains the original full member-scoped coordinate and mapping.

The bridge key deliberately excludes EvidenceStrength, portion, role, history length and recency.
There is no nearest value, interpolation, affine shortcut, sign-only lookup, cross-kind rule, source
chooser, strongest-member search or fallback. Missing exact bridge yields BRIDGE_RULE_NOT_FOUND.
Equal numeric values or a common child policy body are never sufficient by themselves.

### Common operand meaning

`mapped_amount` is an exact reduced rational in [-1,1]: positive is policy-favorable for this
shared exact-target interpretation, negative unfavorable, zero an explicitly mapped zero. The
bridge must preserve the sign/zero of the **frozen child TasteFit fit_amount**: positive→positive,
negative→negative, zero→zero. This refers to the child's defined fit coordinate, never the sign of
raw040B/profile/hierarchy affinity. No statistical, calibrated interpersonal utility or probability
claim is made. Magnitudes are authored in the bridge; this design ships none.

This rule allows different admitted child policy bodies/versions only through their own exact
bridge rows. It does not claim those bodies shared a natural scale. Conditional common units are
defined by this new authored policy and may not be reused outside this exact result scope.

## 7. Complete compatibility gate before new arithmetic

The pure operation performs these phases, in order:

1. Validate wire-size/member/bit budgets, strict transport, root policy and independent pins.
2. Reparse and completely revalidate/recompute every frozen child through its public Interface,
   including unselected children/rows. A parse, hash or supplied cached result is insufficient.
3. Prove exact participants, deterministic child-request construction, full candidate/target/cohort
   coherence and typed immutable identity. Invalid input rejects; no partial numeric result.
4. Decide every member's factual presence, policy admission, current child availability and exact
   policy/mapping bridge compatibility. Retain every direct signal and diagnostic.
5. Only if **all participants** have available, admitted, compatible positive-proof operands, build
   a common scoped operand for each member and enter the private reduction step.

No new fit multiplication, sum, denominator or shared subtotal is computed in phases1–4. Strict
rational parsing/canonicalization is transport validation, not aggregation authority. Frozen child
replay may perform its already-authorized child arithmetic; this gate does not change that behavior.
Mismatch-before-arithmetic tests instrument the new private reduction step, not frozen replay math.

A complete valid bundle may contain compatible and incompatible/unavailable members. It is still
replayable, but the shared value and **all new arithmetic fields remain None**. Do not emit a
partial sum or reduced subset. Individual frozen values remain visible inside their retained children.

Per-member compatibility is COMPATIBLE only with an available eligible row and exact admitted bridge;
INCOMPATIBLE for a valid unadmitted policy or available row without a bridge; NOT_EVALUABLE for a
valid absent/unresolved/unavailable/suppressed child row. Root compatibility is INCOMPATIBLE if any
member is incompatible, otherwise NOT_EVALUABLE if any member is not evaluable, otherwise COMPATIBLE.
All individual reasons remain visible. Numeric coverage is COMPLETE only when every expected ID is
available and compatible; its required/captured/available/compatible sets are reported separately.

## 8. Coverage, missingness and failures

Two different completeness questions are explicit:

- **Source coverage:** exactly one fully valid captured child per participant. Missing/extra child
  is malformed SOURCE_COVERAGE_INCOMPLETE/PARTICIPANT_SET_MISMATCH, not a valid empty preference.
- **Numeric coverage:** every expected participant's chosen target is available, admitted and has
  a compatible bridge. A structurally complete source may have INCOMPLETE numeric coverage; the
  aggregate is UNAVAILABLE. Counts/required member IDs and all member-specific reasons are retained.

| Condition | Observable handling |
| --- | --- |
| Available compatible nonzero child | Contribution eligible only after the global gate passes |
| Genuine child neutral fit zero | AVAILABLE zero with semantic/direct lineage; does not mean missing |
| Valid child UNAVAILABLE /no declaration | UNAVAILABLE with original reason; no new prior or zero |
| Frozen child source value/mapping unavailable | CHILD_FIT_UNMAPPED or CHILD_FIT_UNAVAILABLE plus exact child reason |
| Valid available child lacks new exact bridge | BRIDGE_RULE_NOT_FOUND; compatibility incomplete; no arithmetic |
| Valid child policy/body/version not admitted | POLICY_INCOMPATIBLE; no automatic common-scale conversion |
| Member retracted/suppressed | MEMBER_RETRACTED/SUPPRESSED; no prior/inheritance resurrection |
| Canonical target absent | CANDIDATE_TARGET_ABSENT; diagnostic only, no contribution |
| Canonical target unresolved/dimension uncaptured | CANDIDATE_TARGET_UNRESOLVED and original finite-coverage reason |
| Some expected member lacks numeric contribution | PARTICIPANT_COVERAGE_INCOMPLETE alongside all individual reasons |
| Required member/source read unavailable or denied | Capture fails MEMBER_SOURCE_UNAVAILABLE or CAPTURE_ACCESS_DENIED with nonsecret member/stage; **no successful partial source/result** |
| Duplicate/missing/extra member or forged candidate/target | Rejected participant/binding input; not a soft numeric outcome |
| Contradictory immutable facts or spliced owner cuts | Rejected SOURCE_CUT_INCOHERENT; full recapture required |

Unavailability reasons are a deterministic sorted set, not one priority reason hiding another.
Every member keeps its original status/reason; root reasons do not replace those diagnostics.
Suppression is not NEUTRAL; UNDECLARED is not NEUTRAL; finite REVIEWED_NONE is not never-exposed.
Source failure never becomes NO_DECLARATION, NO_PUBLICATION or a dummy unavailable child.

## 9. Reduction and explicit member influence

The only V1 operator is an **explicit positive-weight exact mean**. Let m range over the entire
canonical participant set; b_m is the bridged scoped operand and w_m its authored positive rational.
After the full gate succeeds:

```text
weighted_contribution_m = w_m × b_m
weight_total = sum(w_m over ALL required participants)
weighted_total = sum(weighted_contribution_m over ALL required participants)
shared_target_fit = weighted_total / weight_total
```

All arithmetic is exact rational, canonical reduced form; denominator>0 follows from a nonempty
canonical set and strictly positive authored weights. Zero/negative/missing/extra weights reject.
There is no default1, equal-weight constructor, implicit normalization by observed members,
rounding, clipping, floating-point math, probability interpretation or arithmetic on raw child units.
The bounded input operands and positive weights imply a result in [-1,1]; violation rejects rather
than clamps. Authored bit limits apply before dangerous intermediate multiplication/addition;
overflow is RESOURCE_LIMIT, never member removal or a partial result.

Products and weighted_total are **unbounded signed rational trace values**, limited by authored bit
budgets, not by the final signed-unit range; weight_total is a positive rational and need not equal1.
They carry their enclosing common coordinate and explicit units (member influence or member
influence×shared-target fit). Do not store weighted products in the bounded fit-amount type.

Equal influence is possible only when the caller explicitly authors equal positive weights.
Portion_factor, attendance, TRACKED/SHARED status, member role, EvidenceStrength, repeated capture,
source-history length and capture order never create or modify weights. Body fingerprints change
when authored weights change, even when a common rescaling produces the same rational result.

Single-member handling uses the same explicit bridge and required weight, not a shortcut returning
the child value/descriptor. Available zero may arise from all-zero mapped values or exact cancellation;
retain that arithmetic trace. Cancellation does not declare the household or all members NEUTRAL.

## 10. Direct dislike and preserved per-member meaning

Retain each member's current direct_signal, declaration_id, semantic state, selected/unselected
views and complete source lineage. Also expose a deterministic direct-dislike trace list by member
and declaration, independently of result availability or sign. LIKE and NEUTRAL remain visible too.

Only current DECLARED_DISLIKE supplies that direct trace. Low affinity, prior/inherited unfavorable
fit, retraction, allergy/diet restriction or another member's declaration never supplies it. There
is no new EXPLICIT_AVOID enum. An unmapped direct dislike remains visible even when numeric coverage
is incomplete. A positive/zero group value never erases a participant's direct dislike.

There is no hard veto, exclusion, implicit negative bonus, automatic weight escalation or safety
decision. Different direct-signal bridge magnitudes, if authored, are explicit conditional policy
values, not shipped defaults. Hard safety stays independent and must precede eventual production
utility use; no favorable aggregate repairs failed grounding or missing root/classification coverage.

## 11. Canonical multi-member capture and coherent owner cuts

The capture Adapter accepts the caller's clean read-only RR/SERIALIZABLE session mapping
(`member`, plus required `prior`/`hierarchy`). It opens no connection, commits/rolls back nothing,
switches no role and performs no mutation. The same session object per owner is used for the whole
cohort; dedicated protected roots retain their distinct authenticated principals/capabilities.
Different owners are not a distributed transaction.

Preflight validates policy pins/limits/exact member-input and weight-key sets. Then, in deterministic
member-ID order, construct each child request and call frozen canonical capture, then frozen derive.
The frozen common grounding request and expected grounding fingerprint must revalidate against
owner truth for every child, including every participant's actual identity/household membership.
Keep all child sources/results, candidate/member/prior/hierarchy frames and the outer capture interval.

Authenticated household/member access is checked by the frozen source path for every child.
Being in MealParticipants is not an extra read grant. Actual DB endpoint/name/OID/address/port,
trusted requesting actor and root-specific session identity must agree as frozen frames require;
labels/URLs alone are insufficient. Prior/hierarchy capabilities are not interchangeable. No new
grant, global publication authority, auth bypass or SELF/representative reuse is introduced.

On any required read/permission/timeout/semantic failure abort the entire operation. Do not return
already captured members as a valid source, splice in old children, continue with a smaller set,
retry one member alone or convert failure to empty evidence. The caller can perform a **full fresh
cohort retry** in clean transactions. Retained old sources remain historical replay, not a substitute
for fresh authorized capture or proof of current access.

### Exact cohort-coherence projection

This comparison is a typed integrity projection, **not a replacement for full-source fingerprints**:

1. Require identical common projection request, expected grounding pin, complete grounded-candidate
   canonical body/issues and CandidateFeatureBinding across children. The frozen full participant
   context/RecipeVersion/path and source identities must agree.
2. Compare complete feature_input.recipe/requested_dimensions/path/**sources** (all terms, scopes,
   reviews/support, Catalog streams and frontiers), recomputed dimension discovery, and the chosen
   complete target proof. This includes hidden histories, not only positive/visible rows.
3. Only these candidate-read metadata may differ: projection source capture_started_at,
   capture_completed_at and feature_input.captured_at; their derived source/projection fingerprints
   consequently differ. Preserve each original value/fingerprint in retained sources and root
   fingerprints. No recursive wildcard timestamp stripping. Authored effective/review times,
   source bodies, frontiers, as_of, dimensions and target resolution are never normalized away.
4. If capture clocks cross a classification boundary and discovery/proof differs, reject the
   whole cohort as SOURCE_CUT_INCOHERENT. Do not choose the latest/favorable classification.
5. For overlapping protected (owner root,provider_id) cuts compare full provider, principals,
   authority_events, publications, mutations, streams, frontier, reader_principal_id,
   reader_session and reader_grant_id. Requests/manifests/read intervals may differ; retain them
   fully and compare overlapping typed identities. Different providers stay separate; no fallback.
6. Repeated member-ledger comparisons are keyed by (household_id,member_id), never across different
   members. Preserve frozen normalization: exclude captured_at only for this comparison, order
   declarations by member_sequence and feature terms by ID. Full histories/frontiers still agree.
7. Across the whole cohort, repeated immutable **typed** AffinityFeatureTermFact, RecipeFact and
   RecipeVersionSnapshot IDs must have identical bodies, following frozen TasteFit identity rules.
   Sharing a UUID across different types is not identity. Mutable Ingredient display labels are
   not immutable-identity corruption; differing candidate-cut bodies still fail cohort coherence.

New Planning checks operate on transported, already revalidated frozen child data; they do not
import Preferences private normalizers/resolvers or widen the frozen companion allowlist.
Structural mismatch rejects rather than averaging conflicting cuts. Every child source/frame time
must remain inside its frozen owner interval and the new outer interval, including nesting order.
Independent owner clocks and actual source cuts retain their original meanings. Common MVCC,
simultaneous historical policy truth, offline DB origin and current authorization are NOT_CLAIMED.

## 12. Pure replay and semantic validation

Pure derive accepts complete retained sources, never sessions. It has zero DB/network/filesystem/
live-clock/environment-policy I/O, no provider registry or mutable/global policy cache. Reparse raw
primitives even when passed model_construct/model_copy instances; apply root wire limits before
deep replay, then canonical size/bit checks after normalization. No truncation or top-K members.

Call frozen validate_candidate_member_tastefit for **every full child**, using its freshly recomputed
return value, and validate that its complete child request equals deterministic construction from
the root request/member input. Replay includes all unrelated target rows, unselected views, prior/
hierarchy sources and complete member histories; the selected outer row is not a hash-only shortcut.
Only then perform §§7–9. There is no independent alternate interpretation of frozen source affinity.

Semantic validation re-derives the entire expected root result from retained sources and compares
all fields: participant/candidate/target binding, compatibility/coverage, direct signals, bridges,
weights, products/totals/value, scopes, reasons, frames and fingerprints. Return the new recomputed
object, not the supplied instance. Hash equality/parsing alone is not semantic validation.

A coherently authored different policy with matching new independent pins defines a different
conditional request; offline validation cannot declare it globally approved/current. A fully
self-consistent retained bundle is not proof of canonical DB origin, common MVCC or ongoing access.

## 13. Result coordinate, units and comparability

The result uses a new **SharedMemberTargetTasteFitCoordinate**, not a modified frozen coordinate:

| Identity field | Required meaning |
| --- | --- |
| coordinate_id /coordinate_version | SHARED_MEMBER_EXACT_TARGET_TASTEFIT /1 |
| unit | POLICY_SHARED_EXACT_TARGET_TASTEFIT_UNITS |
| scope | ONE_CANDIDATE_ONE_TARGET_EXACT_PARTICIPANTS_ONE_POLICY_ONE_RETAINED_COHORT |
| household_id | Exact owner |
| candidate binding /grounding fingerprint | Complete common frozen CandidateFeatureBinding and grounding identity |
| target | Full typed exact PreferenceTarget |
| participant_context_fingerprint | Full canonical MealParticipants context, roles/portions and tracked context retained, never weights |
| aggregation policy fingerprint | Full authored policy body/version, admissions/bridges/explicit weights/limits included |
| retained cohort fingerprint | Complete normalized root source identity, including full child sources/results and clocks |

Every mapped member operand shares this newly defined coordinate; its enclosing contribution also
retains member_id and original child scoped coordinate/mapping. The private reducer checks equality
of the complete new descriptors and member-weight identities before any new arithmetic. Merely
constructing an amount class or stripping a child descriptor cannot supply this license.

`ScopedSharedMemberTargetTasteFit` inseparably carries coordinate + exact SharedTargetTasteFitAmount.
Do not expose a naked amount reducer. Same complete descriptor and same canonical rational permits
scoped numeric equality only. Different target, kind, candidate, household, participant context,
policy body or retained cohort has **no comparison, aggregation or ranking operation**. Same amount,
policy ID/version or Recipe ID alone is insufficient. No universal TasteFit/utility/fairness scale.

Changing source history/child capture can change the cohort coordinate even when the numeric result
does not. Changing weight ratios or bridges changes policy identity. Different policy/capture
results are not interchangeable just because their rationals coincide.
The participant-context digest covers the full frozen MealParticipants representation together
with tracked_member_id, not just sorted member IDs; its existing frozen ordering is preserved.

## 14. Proposed immutable contract inventory

All new transport is frozen/extra-forbid, strict on integers/booleans/literals and recursively
revalidated; canonical set collections reject duplicates before deterministic sorting.

| Proposed shape | Required content |
| --- | --- |
| SharedMemberTargetTasteFitRequest | §5 common candidate/target, exact member inputs, root policy/pins |
| SharedTasteFitMemberInput | Member ID; full frozen child policy/pins and interpretation plan; no supplied child result |
| SharedMemberTargetTasteFitPolicy | §6 complete authored semantics and resource limits |
| SharedTasteFitPolicyAdmission | Complete frozen child policy, expected id/version/body fingerprint |
| SharedTasteFitBridgeRule | Exact child admission/mapping/direct-signal key; rule ID; mapped common-unit amount |
| SharedTasteFitMemberWeight /SharedTasteFitWeight | Member ID and strict positive exact reduced rational; no default |
| SharedTargetTasteFitAmount | Strict signed-unit exact reduced rational; only used inside scoped operands/values or authored rule fields |
| SharedTasteFitRationalTrace | Strict exact rational for potentially unbounded signed weighted products/totals; enclosing coordinate and trace unit retained, no public arithmetic/comparison |
| SharedMemberTargetTasteFitSources | Full root request, sorted complete frozen child results (including sources), capture interval and all retained owner frames; source fingerprint |
| SharedTasteFitCohortProof | Complete expected participant/candidate/target binding, normalized typed integrity projection/digests and all per-child identities; recomputed, not authority |
| SharedTasteFitMemberDiagnostic | Member/child/target proof; availability/compatibility reasons, source mode/descriptor/semantic state/direct signal; full retained child reference |
| SharedTasteFitMemberContribution | Diagnostic, selected exact bridge, original scoped child value, authored weight, common scoped operand and weighted contribution; arithmetic fields None unless the global gate passes |
| SharedTasteFitDirectSignalTrace | Member/declaration/target/direct signal and full child lineage; no veto |
| SharedTasteFitCompatibilityDecision | Policy admissions/rule matches/descriptor checks for all participants, exact compatible IDs and reasons |
| SharedTasteFitCoverage | Required/captured/available-compatible member IDs/counts and complete/incomplete numeric coverage; no denominator shortcut |
| SharedMemberTargetTasteFitCoordinate /ScopedSharedMemberTargetTasteFit | §13 inseparable new context/policy/cohort coordinate and amount |
| SharedMemberTargetTasteFitDraft | Full sources/cohort proof, all diagnostics/contributions/direct signals, compatibility/coverage, operator, totals/value or None, reasons/non-authority/fingerprint |

Root contract versions are `candidate-shared-member-target-tastefit-sources.v1` and
`candidate-shared-member-target-tastefit.v1-draft`; nested coordinate version is1.
Root result status=DERIVED, aggregate_availability=AVAILABLE/UNAVAILABLE; source coverage is complete
for every valid result. AVAILABLE iff the global gate passes and exact reduction is present;
otherwise value/weight_total/weighted_total/new arithmetic fields are None. DERIVED is not ready.

Required non-authority literals: policy_authority=EXPLICIT_INTERPRETATION_INPUT_ONLY;
interpretation_mode=VERSIONED_CONSUMER_POLICY_REPLAY; source_origin=RETAINED_EVIDENCE_NOT_OFFLINE_ORIGIN_PROOF;
common_mvcc=NOT_CLAIMED; cross_target_reduction=NOT_PERFORMED; cross_kind_reduction=NOT_PERFORMED;
whole_candidate_scalar=NOT_PERFORMED; candidate_comparison=NOT_PERFORMED;
repeat_penalty=UNAVAILABLE; novelty=UNAVAILABLE; learned_evidence=UNAVAILABLE;
contextual_evidence=UNAVAILABLE; passive_evidence=UNAVAILABLE; planner_ready=False; activation_ready=False.

## 15. Complete fingerprints and deterministic order

Use domain-separated canonical identities for policy, source/cohort and result, with the contract
version in each domain. Policy fingerprint covers its full authored body, including explicit
admissions/mapping rows/weights/limits/provenance, but never itself or the derived result descriptor.
Materialize source/cohort identity after complete child replay, then descriptors, then the result
fingerprint; no recursive self-hashing.

Root source fingerprint includes full request, exact candidate/target/participant context, all
complete child sources/results/frames and intervals, including unavailable/unselected member and
target states. It is not a digest of only contributing visible rows. The coherence projection in
§11 does not discard clocks, manifests or journals from source identity.

Result fingerprint covers full retained sources and child identities, compatibility decisions,
coverage/reasons, direct signals, exact selected bridges, all member contributions/weights, totals,
scoped result, capture provenance and non-authority literals. Retraction, correction, policy change,
hidden history or unavailable-state change must affect retained identity as appropriate, even when
the final amount is unchanged.

Sort new member tables by member UUID, admissions by exact policy key, bridges by complete semantic
key and diagnostics by stable typed reason/member/target keys. Canonicalize rational components
before duplicate detection/hashing. Normalize new set ordering only; do **not** rewrite frozen
MealParticipants order/context or an existing child fingerprint. Child request/projection/source
serialization and all384 frozen definitions remain unchanged. Fingerprints are replay/tamper
identity, never publication authority, canonical-origin proof or current authorization.

## 16. Policy authority and persistence decision

**EXPLICIT INTERPRETATION INPUT ONLY.** Root/child policies arrive as explicit complete arguments
with independent expected pins. The new Module neither publishes nor selects a global/current/
default/production policy. No numeric policy, fixture, environment setting, reviewer ID, hash,
REVIEWED_REFERENCE label or member authorship role can mint that authority. Prior/hierarchy trust
roots authorize only their existing frozen source paths, never this policy.

No new durable/global source authority was found necessary for this conditional design. If that
assumption changes, stop with:

```text
DESIGN BLOCKED — MISSING PREREQUISITE: canonical shared TasteFit policy publication/selection authority
```

Do not smuggle the missing authority into a helper, constant, seed or adapter configuration.
No global version uniqueness/currentness/CAS promise is made for these caller-authored policies.

**ZERO NEW PERSISTENCE.** No aggregate table, member matrix, cache, materialized profile, policy
registry/rows, grant, production coefficients/defaults/seeds or migration0016. Existing0001–0015
and85 domain tables are unchanged. A genuine new durable source requirement is a separate stop
gate, not permission to expand this implementation later.

## 17. Alternatives, trade-offs and future implementation limits

- Bare sum/mean of child rationals: rejected; descriptors do not grant cross-member arithmetic.
- Same-policy-body automatically compatible: rejected; explicit bridge/context/coverage gates
  still apply. Finite bridges permit deliberate differences without assuming a shared natural scale.
- Implicit equal/portion/strength weights: rejected; all weights must be explicitly authored.
- Min/max or direct-dislike hard veto: not a V1 operator; would change reduction semantics and risk
  confusing soft preference with safety. Direct evidence stays observable with the exact mean.
- Partial-member mean/zero imputation: rejected; missing diners cannot disappear from the denominator.
- Whole-candidate/shared-meal scalar now: rejected; requires additional target/kind policies.
- Registry before any pure conditional consumer: unnecessary for this scope, mandatory as a separate
  prerequisite before future claims of canonical production/default selection.

Finite rules can be verbose and exact matching may withhold many results; that is intentional.
No policy tooling/production seed is included to fill missing rules. Different retained captures
are deliberately not globally comparable. Caller-owned sessions require correct orchestration;
source/canonical capture tests must prove it rather than trusting mock flags.

If later separately authorized, implementation is additive: the four new Planning Modules, focused
public-Interface tests/fixtures, additive contract-export registration and narrow new architecture
guards. Preserve frozen child Modules, source algorithms, migrations and all384 old schema bodies;
only mechanically required export-total assertions may advance. No new context or broad private
cross-context dependency. Numeric fixtures are authored test inputs, never production authority.

## 18. Acceptance matrix — future obligations, not claimed execution

**SMTF01–SMTF120:120 stable design cases.** PG means a required real PostgreSQL obligation;
P means pure public-Interface replay/validation; B means architecture/compatibility. There are
**36 PG obligations (01–36)** and84 P/B cases. These do not claim120 new tests already exist.
Implementation must map every case to actual executed tests and report any parameter expansion;
collection-only/mocked source success cannot satisfy PG obligations. Retain all3,396 baseline tests
and frozen TF01–TF132, including the existing42 child PG cases/35 child obligations.

SMTF cases follow in the table below. All numeric policies/weights used by future tests must be
explicitly authored fixtures and independently checked, never inferred defaults or production rows.

| Case | Layer | Required observable acceptance |
| --- | --- | --- |
| SMTF01 | PG | Fresh canonical INGREDIENT cohort with distinct member declarations; exact target proof, member lineage and independently verified reduction |
| SMTF02 | PG | DIRECT_RECIPE cohort binds stable Recipe plus exact RecipeVersion/source/path; no latest/version substitution |
| SMTF03 | PG | PROTEIN cohort uses actual reviewed MAIN_PROTEIN support/path; ingredient association alone cannot mint dish membership |
| SMTF04 | PG | METHOD cohort preserves frozen version-wide METHOD child/path semantics and exact outer candidate binding |
| SMTF05 | PG | FLAVOR cohort uses finite reviewed universe and exact selected-path support |
| SMTF06 | PG | TRACKED plus multiple SHARED diners captured independently; a tracked LIKE never fills an undeclared SHARED row |
| SMTF07 | PG | Single canonical participant still uses actual capture, exact bridge and explicit authored weight |
| SMTF08 | PG | Unauthorized actor denied by actual household/member source path before preference reads |
| SMTF09 | PG | Foreign-household/member input cannot become a participant or substitute a local child |
| SMTF10 | PG | Required member identity/source missing or access denied aborts capture; no empty-preference substitute |
| SMTF11 | PG | Dirty, writable or READ COMMITTED session rejected; caller session/transaction not mutated |
| SMTF12 | PG | Clean read-only SERIALIZABLE path succeeds under the same Interface and ownership rules |
| SMTF13 | PG | Shared primary RR session retains one actual candidate/member source cut despite concurrent external correction; fresh recapture reflects new truth |
| SMTF14 | PG | Same configured DB name/labels with different actual DB OID/endpoint cannot form a coherent cohort |
| SMTF15 | PG | Required reviewed-prior capture uses actual separate reader capability; denied/revoked reader aborts, not explicit-only fallback |
| SMTF16 | PG | Prior and hierarchy readers/capabilities are not interchangeable in real protected paths |
| SMTF17 | PG | Declared/prior-only member modes coexist with their actual frozen child/source semantics; only exact authored bridge rows participate |
| SMTF18 | PG | One-hop child reuses actual source/publication and mapped-explicit parent only; no second inheritance or EvidenceStrength propagation |
| SMTF19 | PG | Complete protected owner journals/frontiers retained across members, including hidden/unselected publications; no visible-row-only source digest |
| SMTF20 | PG | Actual independently captured pre/post-review-correction children cannot be spliced into a coherent cohort when full classification cuts/discovery differ; no favorable/latest choice |
| SMTF21 | PG | Fault on a later member read after an earlier success aborts the entire canonical capture with member/stage diagnostic |
| SMTF22 | PG | Required prior/hierarchy DB failure after partial capture yields no successful partial source/result |
| SMTF23 | PG | Explicit correction changes fresh child/root trace and identity; retained old full cohort replays historically without live reads |
| SMTF24 | PG | Current retraction suppresses that member and withholds aggregate; no prior/inherited resurrection |
| SMTF25 | PG | Actual direct dislike with unavailable child fit remains visible even though the aggregate has no amount |
| SMTF26 | PG | Real declared NEUTRAL and actual compatible zero mapping produce AVAILABLE zero with complete coverage |
| SMTF27 | PG | One undeclared/unavailable diner plus known available diners withholds aggregate and denominator; no omit/zero imputation |
| SMTF28 | PG | Canonical known-but-absent target stays diagnostic with no positive contribution; nonexistent target is a capture error |
| SMTF29 | PG | Partial/REVIEWED_NONE/uncaptured feature evidence stays explicit absence or unresolved under frozen discovery, never invented fit |
| SMTF30 | PG | Different actual child policies are compatible only with their own pinned full admissions and exact bridge rows |
| SMTF31 | PG | Independently valid but unadmitted child policy produces POLICY_INCOMPATIBLE without new arithmetic |
| SMTF32 | PG | Full retry after failure/correction recaptures every participant in clean transactions; no earlier-child cache splicing |
| SMTF33 | PG | Observe capture SQL: read-only statements; no session role switching, writes, commits/rollbacks or new connections by the Module; row/frontier counts unchanged |
| SMTF34 | PG | Migrated disposable DB remains0015/85 domain tables plus Alembic; no shared-fit table/cache/registry/production rows or0016 |
| SMTF35 | PG | Real independent owner clocks stay inside actual frames; offline replay after live revoke proves retained consistency only, not current access/common MVCC |
| SMTF36 | PG | Actual valid strength/history/portion/role variations do not add member influence when authored bridges/weights and mapped operands are held fixed |
| SMTF37 | P | Exactly one member input per canonical participant; complete source and numeric coverage reported separately |
| SMTF38 | P | Duplicate member input rejected before sorting/dictionary collapse |
| SMTF39 | P | Missing required child/input rejected as source coverage incomplete; no placeholder child |
| SMTF40 | P | Extra/nonparticipant child rejected, even if it has favorable valid TasteFit |
| SMTF41 | P | Child slot/request/subject/source member identities all agree; no copied member preference |
| SMTF42 | P | Empty participant set rejected, never AVAILABLE zero or zero denominator |
| SMTF43 | P | Tracked-only/arbitrary subset cannot match the full frozen candidate context and grounding pin |
| SMTF44 | P | Participant roles/portions/set tampering without a coherently new candidate/request rejects |
| SMTF45 | P | Valid other candidate with same Recipe ID or amount cannot enter this exact candidate cohort |
| SMTF46 | P | RecipeVersion/source/tier/rule/path binding mismatch rejected before arithmetic |
| SMTF47 | P | Exact target kind/ID mismatch rejects; same UUID in another kind is not interchangeable |
| SMTF48 | P | All five supported preference kinds work independently; MAIN_PROTEIN is never a sixth kind |
| SMTF49 | P | Diagnostic-only/absent/parent-only row cannot become a positive contribution or trim child base targets |
| SMTF50 | P | All child projection requests/dimensions match deterministic construction; no hidden context bag |
| SMTF51 | P | Frozen child request/policy/provider/interpretation pins revalidated; detached child configuration rejects |
| SMTF52 | P | Missing explicit aggregation policy fails; no registry/default/fixture fallback |
| SMTF53 | P | Root expected policy ID/version mismatch rejects before source work |
| SMTF54 | P | Root body fingerprint mismatch rejects; matching visible fields cannot hide changed weights/bridges |
| SMTF55 | P | Coherently different body with new matching pins is a different conditional request, not globally approved/current publication |
| SMTF56 | P | Unsupported root/child contract versions reject under their actual typed contracts |
| SMTF57 | P | Valid unadmitted child body/version remains POLICY_INCOMPATIBLE, distinct from forged child data |
| SMTF58 | P | Same numeric fit under different policy bodies does not imply compatibility |
| SMTF59 | P | Same child policy body/target still requires exact authored bridge and complete context/coverage checks |
| SMTF60 | P | Full discriminated raw/profile/inherited source descriptor mismatch cannot be ignored |
| SMTF61 | P | Source amount or complete child mapping row mismatch cannot reuse an admitted bridge |
| SMTF62 | P | RAW_EXPLICIT/EXACT_TARGET_EFFECTIVE/PRIOR_ONLY/ONE_HOP source-mode mismatch is not a fallback option |
| SMTF63 | P | Semantic LIKE/DISLIKE/NEUTRAL/NO_DECLARATION remains part of exact mapping identity |
| SMTF64 | P | Direct-signal bridge key distinguishes direct dislike from prior/inherited unfavorable fit |
| SMTF65 | P | Authored bridge pointing to a mapping absent from its full admitted child body rejects |
| SMTF66 | P | Duplicate/contradictory child admission identity or pins reject; no local ambiguous version |
| SMTF67 | P | Equivalent rational representations normalize before duplicate bridge-key detection |
| SMTF68 | P | Duplicate rule ID or semantic bridge key rejects; no first/last wins |
| SMTF69 | P | Aggregation policy target_kind and every bridge/mapping kind match the exact outer typed target |
| SMTF70 | P | Positive frozen fit maps only to positive common operand; no unsupported sign reversal |
| SMTF71 | P | Negative frozen fit maps only to negative common operand; raw affinity sign is not consulted |
| SMTF72 | P | Zero fit maps exactly to zero; NO_DECLARATION/lineage is not turned into a direct NEUTRAL declaration |
| SMTF73 | P | Missing bridge yields unavailable, never interpolation, nearest lookup, implicit identity or default zero |
| SMTF74 | P | Exact weighted reduction matches an independent rational reference for complete compatible cohorts |
| SMTF75 | P | Single-member result equals its bridged operand through the authored reducer but has a new shared scope, not a copied child descriptor |
| SMTF76 | P | Missing weight rejects even if that member has unavailable data |
| SMTF77 | P | Duplicate/extra weight member IDs reject; no zero-weight exclusion shortcut |
| SMTF78 | P | Zero/negative/boolean/float/nonfinite/invalid-denominator weights or amounts reject strictly |
| SMTF79 | P | Two legal portion contexts with fixed authored weights/operands do not rescale taste; context coordinates still differ |
| SMTF80 | P | TRACKED/SHARED/member-role status supplies no implicit taste priority or weight |
| SMTF81 | P | EvidenceStrength is retained ordinal lineage only, never an added numeric multiplier/confidence |
| SMTF82 | P | More declaration history, retries or recency do not increase member weight or mint evidence |
| SMTF83 | P | Capture/member iteration order cannot affect the exact result or normalized new collection identity |
| SMTF84 | P | Common positive rescaling of authored weights can preserve the amount but changes policy/coordinate identity; no cross-policy equality |
| SMTF85 | P | Exact positive/negative cancellation yields AVAILABLE zero without declaring group/member NEUTRAL |
| SMTF86 | P | AVAILABLE zero and UNAVAILABLE None remain distinct through wire round-trip and validation |
| SMTF87 | P | Complete all-zero compatible operands yield AVAILABLE0/1 with every contributor and authored weight retained |
| SMTF88 | P | One unavailable member with other valid members leaves every new arithmetic field None, not a partial subtotal |
| SMTF89 | P | Suppressed/retracted child cannot use prior/parent/other-member fallback or numeric zero |
| SMTF90 | P | Child fit unmapped and new bridge unmapped have distinct retained reasons; neither is absence/neutral |
| SMTF91 | P | Incomplete numeric coverage preserves all required IDs and reasons; no observed-member denominator |
| SMTF92 | P | Direct dislike trace survives an available positive/zero aggregate and unavailable aggregate alike |
| SMTF93 | P | Unfavorable prior-only fit never mints a current direct-dislike declaration |
| SMTF94 | P | Unfavorable inheritance never mints destination direct dislike or inherited EvidenceStrength |
| SMTF95 | P | Retraction remains suppression, not dislike/neutral or household preference memory |
| SMTF96 | P | Allergy/diet constraint or child grounding rejection is not a taste veto, bridge operand or favorable-fit rescue |
| SMTF97 | P | Direct LIKE/NEUTRAL retains only the current declaration head and exact member lineage |
| SMTF98 | P | Tampering any frozen child, including unrelated/unselected rows or cached outputs, is rejected by complete replay |
| SMTF99 | P | model_construct/model_copy bypasses are untrusted; nested policies/sources/results reparse and recompute |
| SMTF100 | P | Rehashed frames/source fiction cannot certify canonical DB origin/current permission/common MVCC |
| SMTF101 | P | Overlapping provider journal/frontier/reader conflict rejects even with equal visible target rows |
| SMTF102 | P | Same typed immutable ID with conflicting body rejects; cross-type UUID reuse is not conflict; mutable Ingredient labels are handled as cut facts, not immutable identity |
| SMTF103 | P | Only the three documented candidate read-clock fields are normalized for coherence; authored/effective/source times remain binding |
| SMTF104 | P | Different projection hashes solely from allowed clocks can pass coherence, while full retained source/cohort identity still changes |
| SMTF105 | P | Hidden/unselected source history changes full identity even when the final amount stays equal |
| SMTF106 | P | Unavailable-member states, direct signals, bridge/weight/policy changes affect complete source/result fingerprints |
| SMTF107 | P | New member/rule/set order and equivalent fractions normalize deterministically; frozen participant order/child serialization is never rewritten |
| SMTF108 | P | Semantic validator returns a fresh fully recomputed result; parsing or hash-only agreement cannot substitute |
| SMTF109 | P/B | Pure derive/validate performs zero DB/network/filesystem/live-clock I/O through the actual public Interface |
| SMTF110 | P/B | Environment/current/default/registry policy lookup and hidden global cache cannot supply policy authority |
| SMTF111 | P | Any compatibility/context/coverage mismatch prevents the new reduction step before multiplication/sum/denominator; frozen child math remains separately authorized |
| SMTF112 | P | Member/policy/source/result byte budgets reject overflow without dropping members, rows, histories or selected sources |
| SMTF113 | P | Authored integer/intermediate bit limits reject arithmetic overflow; no rounding/clipping/partial result |
| SMTF114 | P | Stripped or forged common/original descriptors fail; bare amounts cannot become licensed operands |
| SMTF115 | P/B | Cross-target or cross-kind reduction rejected; no overall candidate/shared-meal scalar |
| SMTF116 | P/B | Different candidate/participant/policy/cohort scopes have no comparison/ranking operator; scoped equality requires full descriptor identity |
| SMTF117 | P/B | MTR-039 learned/contextual/passive/cooked/friction/forced signals cannot enter this consumer |
| SMTF118 | P/B | RepeatPenalty, exposure, novelty and other behavioral dimensions are not operands or implicit multipliers |
| SMTF119 | P/B | No hard-safety/feasibility, global policy publication, planner or activation authority; literals cannot be promoted |
| SMTF120 | B | All384 old definitions/frozen runtime/migrations and baseline tests retained; no persistence/0016; exact additive exports/import guards; planner_ready=False and activation_ready=False |

## 19. Frozen compatibility, review checks and stop boundary

Future implementation must preserve384 existing schema definitions byte-for-byte in canonical
form, frozen source/TasteFit runtime semantics and0001–0015 migration bytes. All3,396 baseline
tests must remain collected/executed without skips alongside the new acceptance mapping. New
architecture negatives must prove no broadened Preferences private imports, no validation/Learning
or transport access to capture internals, and zero-I/O pure replay. This design adds no tests now.

Documentation validation uses the existing architecture/baseline checks and relative-link/scope
checks; exact-head PR CI supplies a separate receipt. Baseline CI40693646450 is the verified entry
gate, not a substitute for the final design-head run. No new acceptance test is claimed executed.
Existing graph-output workspace changes are excluded from this docs-only PR.
Local receipt:51 existing architecture/baseline tests passed; Ruff,30-invariant/11-ADR/50-task
baseline,16-context import checks, OpenAPI/domain exports,22 fixtures and generated client
contracts passed. All120 case IDs are contiguous/unique, exactly36 marked PG; relative links resolve.

| Work | Unchanged status |
| --- | --- |
| Candidate × Member TasteFit | FROZEN, existing exact implementation/freeze receipts unchanged |
| MTR-040 /issue41 | COMPLETE /CLOSED—COMPLETED; no profile aggregate or reopening |
| MTR-039 | OPEN |
| Full MTR-041 /MTR-046 | PARTIAL /PARTIAL; frozen041A–F/046A unchanged |
| MTR-024 /MTR-020B /MTR-021 | BLOCKED /NOT STARTED |
| Execution | NOT STARTED |
| PRECOMMIT | FAIL-CLOSED |
| This new foundation | DESIGN READY FOR ARCHITECTURE REVIEW; IMPLEMENTATION NOT AUTHORIZED |

No production/default policy selection, downstream milestone, parent-issue closure or planner
authority follows from this design. No runtime/contracts/tests/tooling/migration/data implementation
is authorized. Open the docs-only design PR, leave it OPEN, and stop for architecture review.

```text
CANDIDATE-BOUND SHARED-MEMBER EXACT-TARGET TASTEFIT COMPATIBILITY & AGGREGATION FOUNDATION

DESIGN READY FOR ARCHITECTURE REVIEW

IMPLEMENTATION NOT AUTHORIZED
```
