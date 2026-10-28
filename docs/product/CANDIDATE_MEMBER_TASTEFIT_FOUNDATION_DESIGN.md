# Candidate × Member TasteFit Foundation — Detailed Design

Status: **DESIGN READY FOR ARCHITECTURE REVIEW — IMPLEMENTATION NOT AUTHORIZED**.
Design date: 2026-10-28. Scope: **one canonical candidate × one explicitly identified member**.
This PR changes Markdown only. Every new model, module and operation below is proposed, not implemented.

## 1. Objective and verdict

Interpret canonical candidate facts against existing member-owned preference evidence under an
explicit authored policy. Return a typed, replayable **structured target-fit result** bound to
that exact household/member/candidate/policy. There is **no aggregate TasteFit scalar** in v1.
This is a fit interpretation, not merely a bag of source affinities: each available row applies
an exact authored mapping to one selected source value, with full evidence selection and diagnostics.

```text
CANDIDATE × MEMBER TASTEFIT FOUNDATION
DESIGN READY FOR ARCHITECTURE REVIEW

IMPLEMENTATION NOT AUTHORIZED
```

Policy is a required explicit **consumer interpretation parameter**, following the existing
040B / PR #100 / 041F parameter pattern. This design supplies no globally published/current/default
TasteFit policy and grants no production policy-selection authority. No new durable policy source
is required for this conditional, non-authorizing interpretation; §10 defines that limitation.
Any requirement for a shared approved-policy registry must return to a separate source-design gate.

## 2. Verified entry gate and exact baseline

| Receipt | Verified value |
| --- | --- |
| Repository / design base | `thedusk4203/Menuto`, `622c108d2e8fe150ada521c645a643a362baa520` |
| Approved dependency review | [PR #114](https://github.com/thedusk4203/Menuto/pull/114), head `1452e72621f45d06d191a069c63785c00571eaee`, base `5530da00df9f6c9d8510cb02ac5b5e5a04ba52dc` |
| Formal PASS | [Comment6460614980](https://github.com/thedusk4203/Menuto/pull/114#issuecomment-6460614980) |
| Revalidated before merge | OPEN, MERGEABLE; one commit, five Markdown files; exact-head CI40629120966 SUCCESS; no unresolved threads/blocking review |
| Actual merge/main | `622c108d2e8fe150ada521c645a643a362baa520`; parents are the approved base/head; complete tree equals the reviewed head; exactly five documents changed |
| Exact post-merge push CI | [40632359346](https://github.com/thedusk4203/Menuto/actions/runs/40632359346), SUCCESS on that actual SHA; python/web SUCCESS |
| Verification | **3,104 passed, 0 skips**; SCRAM/TLS16/16; benchmark22/22; client10/10; architecture/import/export/fixtures/contracts/typecheck/build SUCCESS |
| Baseline exports / persistence | **362 / 0015 / 85 domain tables**; no0016, runtime/contracts/tests/tooling/data drift |

Main was fetched and independently checked after merge and after CI. Only then was the fresh
design branch created. The user separately authorized this detailed design, not implementation.

## 3. Canonical requirements and frozen source inventory

[Spec V1.3](../MENUTO_DEVELOPMENT_SPEC_V1_3.md) §8.4 seam4, §9, §10.5/10.8, §14.10,
§19.2–19.6; [ADR-011](../adr/ADR-011-behavioral-learning-loop.md),
[ADR-004](../adr/ADR-004-household-first-model.md),
[ADR-005](../adr/ADR-005-grounded-recipe-variants.md),
[ADR-010](../adr/ADR-010-independent-validator.md), and
[INV-001..030](../ARCHITECTURE_INVARIANTS.md) remain unchanged.
The [approved dependency review](POST_CANDIDATE_FEATURE_PROJECTION_NEXT_GATE_REVIEW.md)
selects this gate without authorizing downstream utility or behavioral events.

| Frozen source | What is reused; limit retained |
| --- | --- |
| 019B/C + [candidate projection](CANDIDATE_BOUND_REVIEWED_CULINARY_FEATURE_PROJECTION_FREEZE_RECEIPT.md) | Canonical request/grounding/projection, exact selected ingredients, stable Recipe/RecipeVersion/source/path, full histories/frontiers; no full feasibility/activation authority |
| [046A](MTR_046A_CULINARY_FEATURE_ASSIGNMENT_DESIGN.md) | Source-owned METHOD cooking context, exact-path MAIN_PROTEIN/FLAVOR, finite discovery and term resolution; no inferred classification |
| [040B capture](../../apps/backend/app/modules/preferences/profile_capture.py) / [contracts](../../apps/backend/app/modules/preferences/contracts.py) | Canonical target manifests, full member ledger, exact head interpretation and ordinal strength; raw prior/shrinkage fields remain UNAVAILABLE |
| [PR #100](EXACT_TARGET_PRIOR_SHRINKAGE_FREEZE_RECEIPT.md) | Exact-target explicit/prior compatibility and shrinkage; one provider; scoped coordinates, explicit-only and prior-only outcomes; no TasteFit or naked scalar authority |
| [Hierarchy SOURCE](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_FREEZE_RECEIPT.md) / [040C](MTR_040C_ONE_HOP_HIERARCHICAL_MEMBER_PREFERENCE_CONSUMER_DESIGN.md) | Protected source capture and one-hop mapped-explicit-only suggestion, exact relation/context, destination suppression, same-ledger and immutable-fact checks; no recursive parent, aggregation or inherited strength |
| Household/actor sources | Existing membership reads and canonical member identities, distinct actor/subject; no new public authentication/curation workflow |

The existing graphify index was queried for navigation only; it predates these capabilities.
Current contracts, capture adapters and pure consumers establish the decisions below. No graph
rebuild/semantic extraction was performed (0 extraction tokens). No frozen incompatibility needs
changing; the currently missing public transport seam is addressed additively in §19.

## 4. Ownership and module decision

Planning owns candidate/member **source integration and fit interpretation**, not member truth.
Preferences owns member ledgers, affinity modes and replay of its frozen consumers. Recipes/Catalog
own identities, feature admission/support and classification. Learning owns future attributed events.
No new member preference is written by Planning; Preferences does not rank candidates.

The module exposes three Planning operations: canonical capture, pure derivation, semantic validation.
Complex child-source capture/replay stays behind an additive Preferences interface. This keeps a
small external interface while centralizing ownership/coherence rather than distributing it to callers.
No generic scoring engine, plug-in matcher or interchangeable arithmetic strategy is introduced.

## 5. Exact subject identity and context

`CandidateMemberTasteFitRequest` contains household_id, member_id, the complete frozen
`CandidateFeatureProjectionRequest`, projection_mode=FRESH_CANONICAL_PROJECTION, required diagnostic_targets
(a tuple of existing PreferenceTarget, explicitly empty if none), expected_policy_id/version/
fingerprint, the full TasteFit policy, and the member interpretation plan described in §9.
No candidate/result JSON is accepted by canonical capture as authority.

The request supplies only `TasteFitMemberInterpretationPlan` (frozen policy bodies/provider selectors),
not a target set, parent choice or prepared member capture plan. The coordinator derives
`TasteFitMemberCapturePlan` from canonical candidate proofs and policy; pure replay derives it again.

The projection fingerprint includes real capture clocks: it is generated **after** fresh capture,
not a pre-capture pin to an older projection. The frozen expected grounding fingerprint still pins
the exact requested grounded candidate. A caller requiring an already captured projection must use
pure replay of its complete retained TasteFit sources; this interface does not re-certify an old cut
from fresh DB reads. An expected-old-projection field is not accepted at canonical ingress.

The derived `TasteFitSubject` retains household_id/member_id, grounding fingerprint, projection
fingerprint, full CandidateFeatureBinding (culinary fingerprint, stable recipe_id, recipe_version_id,
recipe_source_hash and exact selected path), and the original grounding request context.
The exact member must appear in both canonical captured member identities and candidate participants;
a SHARED participant is legal, the subject need not be tracked_member_id. Household membership
alone does not prove the candidate was grounded for that subject. No new grounding or participant
inference is performed here. Other participants remain grounding context, not TasteFit subjects.

Context is the retained canonical grounding/projection request: participant set, tracked member,
region/currency, grounding as_of, authored selection/triggers and source pins. There is no arbitrary
context bag or user-defined time/equipment/role modifier. Portion factors are not taste weights.
No title, latest version, family, implicit current candidate, alias or caller `ready` flag is ingress.

## 6. Supported target kinds and factual admission

V1 explicitly supports the existing **five** kinds below. A policy must explicitly select a
nonempty subset; support does not mean automatic participation. All proven candidate targets are
enumerated before policy filtering, with disabled rows observable as POLICY_TARGET_NOT_ADMITTED.
No `MAIN_PROTEIN` preference kind or sixth kind is introduced.

| Preference kind | Exact candidate proof |
| --- | --- |
| DIRECT_RECIPE | Frozen projection binding.recipe_id equals the canonical RecipeFact ID. Preference identity is stable-Recipe-scoped; result identity still includes exact RecipeVersion/source/path, so another version cannot reuse the old TasteFit result. |
| INGREDIENT | Actual selected `resolved_ingredients` from re-grounded culinary candidate, joined by requirement_id to canonical captured IngredientIdentityFact. Original substituted-away ingredient is not present. Repeated selected ingredient IDs form one row with all requirement proofs, never multiple contributions. |
| PROTEIN | Frozen feature discovery/term resolution proves PRESENT for a reviewed MAIN_PROTEIN assignment with exact path and pinned Catalog support; the immutable term kind must be PROTEIN. Association or protein grams alone cannot prove dish main protein. |
| METHOD | Frozen METHOD discovery/term resolution proves PRESENT for the reviewed METHOD term in that RecipeVersion cooking context. Preserve the frozen METHOD child path semantics, including path=None for METHOD-only capture, while the outer subject retains the exact candidate path. |
| FLAVOR | Frozen exact-path discovery/term resolution proves PRESENT for a reviewed FLAVOR term inside the captured finite universe. No inferred neighboring flavor/family. |

Base target keys are the deduplicated union of stable Recipe, selected ingredients and proven
positive terms. The requested feature dimensions remain exactly the frozen projection request;
uncaptured dimensions yield DIMENSION_NOT_CAPTURED diagnostics, never fabricated completeness.
ASSIGNED with PARTIAL coverage admits known positives while preserving uncovered unknowns.

`diagnostic_targets` adds exact canonical probes for explanations, not positive membership or a
filter on the base set. Owner reads must prove probe identity. A nonexistent target is a source
identity error, not candidate absence. DIRECT_RECIPE/INGREDIENT probes outside the exact selected
set are ABSENT. Feature probes reuse `resolve_feature_input`: REVIEWED_ABSENT is finite absence,
TERM_NOT_CAPTURED / OUTSIDE_REVIEWED_UNIVERSE / partial/stale/retracted remain UNRESOLVED.
Do not append probe facts to a frozen feature cut to make it appear captured.

Retain separate candidate target state (PRESENT/ABSENT/UNRESOLVED), full frozen dimension
discovery (including REVIEWED_NONE), term resolution and policy admission. Unsupported kind is
TARGET_KIND_UNSUPPORTED; a known but policy-disabled kind is not unsupported source truth.
Absent/unresolved/disabled rows perform no member fit mapping. Never infer identity from title,
category, dominant mass, family, alias or latest version. A parent-only hierarchy target is lineage,
not an additional candidate-positive target.

## 7. Member modes and deterministic precedence

For every admitted PRESENT target, retain a re-derived 040B row. Optionally retain complete PR #100
and040C results according to the explicit capture plan; all supplied/captured children are validated,
including unselected children. Output separates raw state, each view's mode/availability, selected
view, exact mapping rule and unselected-view diagnostics. There is one selected value per target.

| Current destination head | Selection rule |
| --- | --- |
| RETRACTED | Always SUPPRESSED / MEMBER_RETRACTED, no fit amount. No policy override, prior, parent or stale declaration may resurrect it. |
| DECLARED LIKE/DISLIKE/NEUTRAL | Kind policy must choose RAW_EXPLICIT or EXACT_TARGET_EFFECTIVE. RAW_EXPLICIT uses040B. EXACT_TARGET_EFFECTIVE uses the frozen PR #100 EXPLICIT_ONLY or BLENDED_EXPLICIT_AND_PRIOR result. No second blend, raw fallback or inheritance chooser. |
| UNDECLARED | Kind policy must choose NO_EVIDENCE, PRIOR_ONLY or ONE_HOP_INHERITED. NO_EVIDENCE remains unavailable. PRIOR_ONLY requires actual PR #100 PRIOR_ONLY_COLD_START. ONE_HOP requires actual040C AVAILABLE inheritance. Unavailable selected branch stays unavailable; no fallback to another view. |

These are required authored enum choices, not constructor defaults. The kind's capture mode is
EXPLICIT_ONLY, EXACT_TARGET, or EXACT_TARGET_AND_ONE_HOP and must support its selections.
EXACT_TARGET_AND_ONE_HOP captures/replays both exact and inherited views even when a current direct
declaration suppresses inheritance. A parent is captured only when the frozen resolver selects an
eligible relation; an optional supplied parent is still fully validated. No favorable-parent search.

Destination prior-only and inherited suggestion may coexist. Choosing PRIOR_ONLY records inherited
as NOT_SELECTED; choosing ONE_HOP records the prior-only view as NOT_SELECTED. This is an authored
categorical choice, independent of amounts/strength/recency. No max, average, sum or automatic
strongest-evidence rule exists. A missing selected branch cannot silently switch the choice.
040C still uses mapped_explicit lineage, never the parent's effective blend or prior-only value.

RAW_EXPLICIT supports an initial deployment with no configured prior/hierarchy provider. When a
configured source cannot be captured, fail the whole capture; do not synthesize NO_PUBLICATION or
an unavailable child to manufacture explicit-only success. Genuine frozen resolver unavailability
inside a successful source capture remains an ordinary observable outcome.

## 8. EvidenceStrength and direct dislike

TasteFit retains the complete frozen DerivedExplicitEvidenceStrength as lineage **only**.
No new eligibility threshold, count or numeric multiplier is applied. PR #100 may already have
used that ordinal under its frozen authored shrinkage policy; TasteFit does not apply it again.
NONE/LOW/MEDIUM/HIGH remain ordinal metadata, never probability or Bayesian precision.
For prior-only/inherited selections, the destination's explicit strength remains NONE; inherited
strength is NOT_DERIVED. Parent strength is retained solely inside parent lineage, not propagated.

`direct_signal` is NONE or the exact current DECLARED_LIKE / DECLARED_DISLIKE / DECLARED_NEUTRAL
head, with declaration identity. DECLARED_DISLIKE is retained even if mapping is unavailable.
It is a soft signal for this member, not a safety failure, candidate exclusion or household veto.
Prior/inherited unfavorable values never mint DECLARED_DISLIKE. No frozen EXPLICIT_AVOID value
exists here; adding one or treating a dietary exclusion as taste is outside v1.

## 9. Policy shape and member interpretation plan

`TasteFitInterpretationPolicy` is immutable, extra-forbid and versioned:

- contract_version=`candidate-member-tastefit-policy.v1`, policy_id, policy_version, Provenance
  (USER or REVIEWED_REFERENCE), interpretation_mode=VERSIONED_CONSUMER_POLICY_REPLAY;
- required admitted_kinds and exactly one kind-policy per admitted kind; no omitted-kind default;
- kind-policy: target_kind, capture_mode, declared_selection, undeclared_selection and finite
  exact mapping rows; disabled/nonselected modes cannot appear as alternate fallback strategies;
- operator=PER_TARGET_FINITE_EXACT_LOOKUP, aggregation=NOT_PERFORMED,
  evidence_strength_effect=LINEAGE_ONLY, retraction=SUPPRESS;
- required positive resource limits max_targets, max_policy_bytes, max_source_bytes; these bound
  processing, not taste. Overflow is RESOURCE_LIMIT, never trimming history/targets or top-K ranking.

Target budgeting counts the distinct base/probe/parent closure, including parent-only inputs;
source-byte budgeting includes complete retained histories, not just relevant rows. Check available
wire-size budgets before deep semantic replay, then canonical sizes after normalization. No truncation.

Each mapping row key is **(target kind, selected source mode, semantic state, complete source
descriptor, canonical source rational)**. Semantic state is the actual destination declaration for
direct/exact-with-explicit, NO_DECLARATION for prior-only, or the retained parent semantic_state for
inherited. NO_DECLARATION is not NEUTRAL. The output is one explicitly authored TasteFitAmount.
Exact matching only: no ranges, interpolation, nearest amount, sign inference or default zero.
Duplicate keys reject; an unmapped value is unavailable. Rows for non-admitted kinds/modes reject.

Source descriptor is a discriminated union: RAW_EXPLICIT wraps the040B unit, exact kind and full
explicit-policy fingerprint (the frozen raw amount remains unchanged); PROFILE retains the complete
MemberProfileAffinityCoordinate; INHERITED retains the complete InheritedMemberPreferenceCoordinate.
The RAW_EXPLICIT wrapper has family=FROZEN_040B_EXPLICIT, wrapper_version=1 and
scope=ONE_EXACT_CURRENT_DECLARATION; it never invents a coordinate inside the frozen040B amount.
Never compare amounts before descriptors/kinds and selected semantic mode agree. The full exact
target is attached outside these source descriptors as required by the frozen owners.

The member interpretation plan separately supplies the complete frozen040B policy, and where
required full compatibility/shrinkage policies, one prior provider selector and one hierarchy
provider/policy selector. It pins expected bodies/identities, is retained in full, and must satisfy
all original frozen bindings. No registry lookup, latest policy, provider fallback or inferred
hierarchy direction is performed. This plan is provenance/inputs, not a new fit coordinate family.

## 10. Policy authority decision

Policy comes from an explicit internal caller argument, accompanied by independent expected
id/version/body-fingerprint pins in the request. Caller selection is not a global publication.
The source coordinator verifies authenticated member/source reads; it **does not certify that a
policy is globally reviewed, current, calibrated, clinically safe or production-approved**.
Output literal: policy_authority=EXPLICIT_INTERPRETATION_INPUT_ONLY.

This is the same distinction already used by authored040B/PR #100/041F consumer policies:
interpretation input may be conditionally replayed without minting persistent reference truth.
No reviewer ID, provenance label, fixture or hash grants publication authority. Existing prior and
hierarchy publication capabilities continue to be checked only by their frozen protected paths.
SELF/AUTHORIZED_REPRESENTATIVE never grants global policy/source publication rights.

There is no shipped numeric policy, default body, selection registry, hidden fixture fallback or
HTTP entrypoint. Missing policy fails POLICY_MISSING. Unsupported contract version or expected
id/version mismatch fails POLICY_VERSION_MISMATCH; body-pin mismatch fails POLICY_FINGERPRINT_MISMATCH.
A coherently authored different body with new matching pins is a **different conditional request**,
not proof of tampering or approved publication. Reusing id/version with another body changes its
semantic fingerprint; no global version uniqueness/CAS is promised without a durable registry.
Future production/default selection requires separate authority review; this design cannot mint it.

## 11. TasteFit meaning and coordinate

Choose **structured per-target fit values only**. Each AVAILABLE row applies its single exact
mapping row; no aggregate, dimension total, overall neutral, best target or scalar shortcut exists.
TasteFitAmount is a strict exact reduced rational in [-1,1], denominator>0; no floats, rounding,
clipping or statistical claim. Parse integer components strictly (bool is not int here), check the
signed-unit range, then reduce by GCD, including0/x→0/1. Mapping-key rationals normalize likewise;
equivalent fractions cannot hide duplicate keys or acquire different policy identities.
Positive means policy-favorable for this subject/target, negative
policy-unfavorable; zero is an explicitly authored neutral fit coordinate, not absent evidence.

Mappings with semantic LIKE must produce >0, DISLIKE <0 and NEUTRAL exactly0; these are definitions
of the new fit coordinate, not raw-affinity sign rules or numeric weights. Prior-only mappings have
NO_DECLARATION and may author either sign or zero without creating a member declaration. The raw
040B neutral/zero coordinate can differ; the exact semantic-plus-amount key prevents sign inference.
All nonzero magnitudes are caller-authored. No numeric production values are included in this design.

`TasteFitCoordinate` carries coordinate_id=CANDIDATE_MEMBER_TARGET_FIT, coordinate_version=1,
unit=POLICY_TARGET_TASTEFIT_UNITS, scope=ONE_POLICY_ONE_HOUSEHOLD_ONE_MEMBER_ONE_CANDIDATE_ONE_TARGET,
full TasteFit policy fingerprint, household_id, member_id, grounding/projection fingerprints and
exact PreferenceTarget. `ScopedTargetTasteFit` inseparably contains descriptor and amount.
Descriptor materialization occurs **after** hashing authored policy; no self-reference in policy hash.

| Comparison | V1 meaning |
| --- | --- |
| Same complete descriptor + same canonical rational | Scoped numeric equality allowed; evidence mode/lineage still distinct in the enclosing row |
| Same policy id/version only | Insufficient; full body and subject/target bindings must also match |
| Same member/policy, different target mixes or targets | No defined scalar comparison or aggregation |
| Different candidates, even same member/policy | No comparison/ranking; candidate fingerprints are part of descriptor |
| Different members | No comparison or household reducer |

Shrinkage policy fingerprints remain derivation provenance in frozen children and full result
identity, not new fields of their coordinates. Changing only shrinkage does not redefine the
TasteFit coordinate if fit policy and exact subject remain unchanged; mapped values/trace may change.

## 12. Proposed immutable transport/result contracts

All new models are frozen, extra-forbid, strict on literals/booleans/rational integers and recursively
reparse primitive content. Existing frozen model definitions and serialization remain untouched.

| Model | Required content |
| --- | --- |
| CandidateMemberTasteFitRequest | §5 selectors/pins, full policy and member interpretation plan; no supplied child result as canonical ingress |
| TasteFitInterpretationPolicy / TasteFitKindPolicy / TasteFitMappingRow | §9–10 complete authored semantic inputs; deterministic sorted kind/key sets |
| TasteFitSourceCoordinate | Discriminated RAW_EXPLICIT / PROFILE / INHERITED descriptor; full policy/kind/unit/scope retained |
| TasteFitMemberInterpretationPlan | Full frozen policy bodies and exact optional provider/policy selectors required by the capture modes; no requested target set or caller-chosen parent |
| TasteFitMemberCapturePlan | Owner/member, derived target set and required capture modes, frozen policy bodies/provider selectors, candidate recipe context pins as Recipes immutable types; no Planning contracts inside Preferences |
| TasteFitMemberSourceBundle | Full040B snapshots plus optional exact-target/040C primitive inputs by target, canonical target manifests and member ledger identity; never just cached outputs |
| TasteFitCaptureFrame | Owner session kind, exact requested target set, requesting actor where applicable, available nonsecret DB/principal identity, isolation/read-only mode and actual start/end; provenance, not an authority token |
| CandidateMemberTasteFitSources | Request, full validated projection source/result, member source bundle, coordinator start/end and per-owner capture frames; no common-MVCC certificate |
| TasteFitSubject | §5 complete binding and exact member identity |
| TasteFitTargetProof | Typed target, role=BASE or DIAGNOSTIC_ONLY, all candidate proof references, candidate state/term resolution and dimension diagnostics |
| TasteFitTargetInterpretation | Proof, raw/member views and diagnostics, policy admission, selection/mode/reason, direct_signal, strength lineage, mapping key/full row, AVAILABLE scoped value or UNAVAILABLE/SUPPRESSED without amount |
| TasteFitCoordinate / TasteFitAmount / ScopedTargetTasteFit | §11 inseparable result value; no naked amount operation |
| CandidateMemberTasteFitDraft | Full sources/subject, sorted target interpretations and complete dimension diagnostics, fingerprint; status=DERIVED; coverage=EXACT_RETAINED_SCOPE_ONLY; aggregate=NOT_PERFORMED; policy_authority literal; planner_ready=False; activation_ready=False |

DERIVED means replayable interpretation, not all-target availability, positive fit, eligibility or
production readiness. Parent-only targets are retained in lineage, not output fit contributions.
There is no implicit empty aggregate; empty/unknown rows remain explicit structured diagnostics.

## 13. Canonical capture model

Capture receives caller-owned clean read-only RR/SERIALIZABLE sessions: candidate/member session,
and optional dedicated prior and hierarchy sessions when the selected capture modes require them.
Do not open connections, select credentials, commit/rollback caller transactions or issue
SET ROLE/SESSION AUTHORIZATION. Existing protected SECURITY DEFINER read functions retain their
frozen privilege semantics; this is not permission to broaden caller grants.
The configured sessions must address the same canonical Menuto deployment/database; canonical
adapter checks configured connection endpoint/database and available DB/session identities without
serializing secrets. Prior/hierarchy retain independent credentials/CAPTURE grants/SCRAM/TLS paths.
Do not reuse the prior trust root as hierarchy authority or use household authorship for either.
Retain the trusted requesting actor_user_id and every owner frame in source identity. Their presence
in serialized input does not itself prove authentication; canonical ingress obtains them from the
actual caller-owned sessions. Actor identity is audit provenance, never the preference subject.

1. Validate policy/pins/resource budgets and request selectors before source work. Verify trusted
   actor membership; verify explicit member is part of the re-grounded candidate participant context.
2. Reuse frozen candidate capture and full projection validation; require the expected grounding
   pin and retain the actual fresh projection fingerprint. A grounding mismatch is not silently
   substituted. Fresh feature capture is explicit in projection_mode, never replay of an old cut.
3. Enumerate base/probe targets and owner identity proofs; keep the candidate/member session open
   on one RR/SERIALIZABLE cut. Capture full member ledgers/manifests for these exact targets.
4. Preferences adapter captures configured exact-target and hierarchy sources on their own coherent
   sessions. It uses the frozen hierarchy resolver to discover at most one eligible parent per
   destination, then captures parent preference inputs on the **same member cut**. Parent-only
   identities never enlarge candidate-positive admission. Preserve every frozen child's own source cut.
5. Build exact single-target frozen inputs (their requests require exactly one destination); per-target
   captures on a given owner session share that owner's snapshot/frontier but not necessarily clocks.
   Recompute all frozen children. All members/targets/manifests/provider policies must agree. The
   member bundle has exactly the derived base/probe/eligible-parent closure, no extra parent or
   detached source payload. Capture-frame records enumerate that exact set and its owner sessions.
   This exact-set rule governs top-level target entries/requests: nested frozen provider histories
   and owner manifests retain their complete required union, including unrelated publications/targets.
   Do not trim frozen global sources to the candidate closure or turn every nested identity into a
   candidate target. max_targets bounds the top-level closure; max_source_bytes bounds the full cuts.
6. Return complete retained sources only after pure TasteFit derivation/validation succeeds.
   Any required read failure aborts the whole capture result; no silent partial retry/dimension drop.

Disabled prior/hierarchy capture is NOT_REQUESTED_BY_POLICY, not NO_PUBLICATION. A successful
capture with no publication/relation retains the actual frozen unavailable reason. Serialization
retry recaptures the entire multi-owner envelope; never splice a retried owner into an old envelope.

## 14. Cross-source coherence and time

- Same household and exact subject member throughout candidate context, manifest and every direct/
  parent input. No actor=member assumption; use existing actor authentication and subject selection.
- All040B snapshots share the full canonical ledger body, excluding only captured_at, with declaration
  sequence and feature-term ID normalization matching040C. Same frontier alone is insufficient.
- Same typed immutable AffinityFeatureTermFact, RecipeFact and RecipeVersion ID means identical
  complete body at every depth, including prior and hierarchy manifests. Different typed owners
  sharing a UUID are not duplicates. Mutable ingredient display-label differences across owner cuts
  do not imply a new identity; never use labels for matching. Retain them in source identity.
- Validate exact projection request/path/RecipeVersion/source hash and selected ingredient proof.
  A DIRECT_RECIPE **destination** hierarchy suggestion is applicable only when its binding matches
  the candidate RecipeVersion and, when authored, exact path/context. A valid source relation for
  another version/path remains retained as INHERITED_DESTINATION_CONTEXT_MISMATCH: selected
  inheritance is unavailable, not transferred; other already-selected views are not invalidated.
  It is not falsely classified as corrupted immutable data. An edited cached binding or conflicting
  body for the same immutable version still rejects. Version-only or METHOD-invariant relation
  scopes retain their authored meaning; do not invent a path. Parent SOURCE recipe context may legitimately describe
  another recipe; verify its frozen parent target/context, never substitute it for the candidate.
- Preserve every PR #100 provider/coordinate/explicit-policy/shrinkage binding and040C relation/
  mapping/semantic-policy binding. Wrong canonical selectors or malformed children reject; genuine
  frozen unavailable/incompatible outcomes remain observable. Never normalize incoherence away.
- Each owner's complete frontier/history and own time rules hold independently. Grounding as_of,
  feature captured_at, member captured_at and global capture times are not one historical frontier.
  Capture frames retain actual start/end around each read; unequal clocks are legal. No universal
  historical policy-knowledge, simultaneous liveness or common MVCC assertion is introduced.

The mode is VERSIONED_CONSUMER_POLICY_REPLAY over coherent retained owner cuts. Offline replay
cannot prove authenticated database origin, same deployment, current permission or a shared real
transaction merely because hashes and repeated facts agree. New live publication/correction affects
a fresh capture; it does not mutate or retroactively certify an old retained result.

## 15. Missingness and error taxonomy

Error codes are proposed explicit outcomes, not new source states. Capture/parse rejection returns
structured ResolutionError and **no TasteFit result**; an ordinary row outcome retains its source
and policy trace with no fabricated amount. Unavailable never means zero or hard infeasible.

| Condition | Outcome |
| --- | --- |
| Candidate source unavailable / required source I/O fails | Whole-capture CANDIDATE_SOURCE_UNAVAILABLE / SOURCE_CAPTURE_FAILED; no fake partial sources |
| Candidate projection pin/binding wrong | Rejected CANDIDATE_BINDING_MISMATCH |
| Feature not captured / unresolved | Dimension and affected probe retain DIMENSION_NOT_CAPTURED / exact frozen reason; no target-fit amount |
| Feature REVIEWED_NONE | Full finite discovery retained; no positive target invented; applicable probe absence comes only from frozen term resolution |
| Canonical target absent from candidate | ABSENT / CANDIDATE_TARGET_ABSENT; not member dislike or zero fit |
| Unsupported target kind / nonexistent canonical identity | Rejected TARGET_KIND_UNSUPPORTED / CANONICAL_TARGET_UNAVAILABLE |
| Target kind not admitted by policy | NOT_ADMITTED / POLICY_TARGET_NOT_ADMITTED; no mapping |
| Member undeclared + NO_EVIDENCE | UNAVAILABLE / MEMBER_UNDECLARED; strength NONE |
| Member retracted | SUPPRESSED / MEMBER_RETRACTED regardless of alternate views |
| Selected member view unavailable | UNAVAILABLE / SELECTED_EVIDENCE_UNAVAILABLE with exact nested frozen reason; no fallback |
| Prior NO_PUBLICATION / RETRACTED / unmapped amount | Preserve frozen reason; declared PR #100 may legitimately be EXPLICIT_ONLY; selected prior-only remains unavailable |
| Incompatible prior provider/policy/coordinate binding | Rejected SOURCE_POLICY_BINDING_MISMATCH under frozen input validation; no forced explicit fallback |
| Hierarchy source successfully resolved unavailable | Preserve exact reason (including multiple incoming, no relation, superseded support); inherited selection has no amount |
| Inherited suggestion unavailable/incompatible | Preserve040C reason (parent retracted/prior-only/undeclared, source value unmapped or incompatible); no strength minted |
| Valid inherited destination authored for another candidate version/path | UNAVAILABLE / INHERITED_DESTINATION_CONTEXT_MISMATCH when inheritance is selected; retain valid child/context diagnostic, no other-relation search |
| Valid source descriptor/value has no fit mapping | UNAVAILABLE / SOURCE_COORDINATE_NOT_ADMITTED or SOURCE_VALUE_NOT_MAPPED; direct signal remains retained |
| Policy missing / unsupported version / expected pin mismatch | POLICY_MISSING / POLICY_VERSION_MISMATCH / POLICY_FINGERPRINT_MISMATCH; no result |
| Source-cut incoherence / wrong household/member | Rejected SOURCE_CUT_INCOHERENT / SUBJECT_OWNER_MISMATCH |
| Tampered replay, forged descriptor or cached child | Rejected REPLAY_MISMATCH; no availability fallback |
| Resource budget exceeded | RESOURCE_LIMIT; no truncated histories, partial total or ranking |

Genuine available0/1 requires an exact selected source and an authored mapping to neutral fit.
Its source semantic state/mode remains attached; it is distinct from all unavailable/suppressed rows.

## 16. Pure replay and semantic validation

`derive_candidate_member_tastefit(sources)` recursively reparses primitives, recomputes frozen019C/
projection and every supplied040B/PR #100/040C child, validates coherence/proofs/policy selection,
applies exact row lookup and builds a fresh typed result. No DB, network, filesystem, live clock,
environment policy lookup or mutable cache is allowed. Reuse owner public operations, never copy
affinity/shrinkage/hierarchy/classification algorithms into Planning.
Planning recomputes the base/probe set and checks the owner-derived eligible-parent closure against
the member bundle; caller-edited capture plans, missing targets or added parents cannot shrink or
enlarge the interpreted candidate. Valid full provider manifests remain nested source evidence.

`validate_candidate_member_tastefit(result)` reconstructs solely from retained sources and compares
the **complete** subject, proofs, views, selection, mapping rows, values, missingness, diagnostics,
flags and fingerprint. It returns the newly derived result. Compare semantic content, not only a
claimed hash. Pydantic parse success, model_construct/model_copy, detached scoped values and cached
children supply no authority. Even an unused malformed optional child fails full replay.

## 17. Fingerprint and canonical ordering

New envelope canonicalization uses domain-separated SHA-256 over explicit UTF-8 canonical JSON:
sorted object keys, UTC instants, strict reduced integer rationals, exact frozen child encodings.
New declared sets sort by typed target key / mapping composite key / source frame key; ordered
source journals keep frozen ordering. Unknown collections/duplicate semantic keys reject rather
than acquiring a generic new sorting rule. Never rewrite frozen Decimal/clock/fingerprint semantics.
Serialize each child using its existing frozen canonical rules, then embed that canonical wire
content; new envelope normalization must not reinterpret nested owner timestamps or numeric encodings.

- Policy fingerprint hashes its complete authored body (id/version/provenance, admitted kinds,
  choices, mapping keys/values, operator, limits), excluding only an optional own hash field.
  Construct output descriptors afterwards. No materialized descriptor recursively contains its hash.
- Source fingerprint includes the complete request, policy and member plan, candidate projection
  source/result, all member/parent inputs/manifests/ledgers, prior/hierarchy cuts, capture frames,
  unselected views' primitive inputs and diagnostic probes. Source history invisible in positive
  target rows still changes source identity.
- Result fingerprint includes complete sources/subject/targets/proofs/views/mapping/missingness/
  diagnostics and every non-authority literal, excluding only its own fingerprint. No semantic
  field or policy input may live outside that identity.

Same replayed bytes under the declared normalizations produce the same identity. A change only to
shrinkage/capture/history can change full source/result identity without changing fit amounts or
their policy coordinate. Fingerprints are identity/tamper checks, not origin/publication authority.

## 18. Non-authority and no learning coupling

Required output literals: planner_ready=False, activation_ready=False, aggregate=NOT_PERFORMED,
shared_member_aggregation=NOT_PERFORMED, candidate_comparison=NOT_PERFORMED,
learned_evidence=UNAVAILABLE, contextual_evidence=UNAVAILABLE, passive_evidence=UNAVAILABLE.
No MTR-039 event, cooked=>liked interpretation, retail friction, forced-choice signal, passive
assumption, RecentExposureModel,041 repeat chain, global history, novelty or exploration admission
is an input. TasteFit cannot emit preference/exposure writes or become a hierarchy parent.

Hard safety/nutrition/SPEND_LIMIT/inventory/procurement remain independent. Rejected grounding
cannot be rescued by favorable taste. A valid safety/price/context change may change frozen subject
identity, but none is a fit mapping operand or hidden weight. No safety certification, eligibility,
role score, utility, ranking, portfolio selection or shared-meal reducer is produced. Later shared
utility must separately resolve all participant hard constraints before any member aggregation.

## 19. Exact proposed modules and public interface

All paths below are under `apps/backend/app/modules/`; no files are added there by this design PR.

| Proposed module | Responsibility / allowed seam |
| --- | --- |
| `preferences/tastefit_contracts.py` | Additive immutable member plan/bundle transport, referring to existing frozen member/prior/hierarchy types within their owner context; no Planning contracts or new affinity semantics |
| `preferences/tastefit_sources.py` | Owner adapter calls frozen capture functions, discovers exact eligible parents via frozen resolver, captures same member ledger and retains source cuts; no new grant or publication |
| `preferences/tastefit_public.py` | New companion interface: `capture_tastefit_member_sources(sessions, plan, *, actor_user_id)` and pure `replay_tastefit_member_sources(bundle)`; return full typed frozen views, not fit or ranking. Adapter imports are lazy only in capture operation. |
| `planning/tastefit_contracts.py` | §12 new immutable request/policy/source/result types; imports only immutable owner contract transport and neutral types |
| `planning/tastefit_capture.py` | Canonical candidate/member coordinator in §13; no commits, connection creation or serialized-source authority |
| `planning/tastefit.py` | Pure target proof, authored selection/mapping, descriptor checks, result construction and semantic validation; no I/O or owner algorithm duplication |
| `planning/tastefit_public.py` | Three lazy companion operations: `capture_candidate_member_tastefit_sources(sessions, request, *, actor_user_id)`, `derive_candidate_member_tastefit(sources)`, `validate_candidate_member_tastefit(result)` |

The current import checker recognizes only `contracts`/`public` as cross-context seams. Do **not**
import private prior/hierarchy modules directly from Planning, add opaque unvalidated dict payloads,
create a circular re-export from frozen preferences/contracts.py, or broadly permit private imports.
Later implementation needs a **strict exact-module allowlist** for the new Preferences companion
transport/interface used only by the named Planning TasteFit modules, plus pure-core negative checks.
Existing validation/Learning contract-only rules and all frozen pure-core allowlists stay intact.
This is additive interface exposure, not a change to frozen contracts/public prefixes or behavior.
No new registered domain context, neutral domain importing contexts, HTTP endpoint or planner call.

## 20. Persistence and implementation scope

**ZERO NEW PERSISTENCE.** No TasteFit table, member-candidate matrix, profile cache, policy rows,
production seed, migration0016, grant, background worker or publication endpoint. Frozen0001–0015
stay byte-exact; schema0015 /85. A later implementation may add only the reviewed immutable shapes,
companion modules, narrow architecture guard coverage, exports and tests after separate authorization.
All362 old export definitions must remain unchanged; new exported shapes require explicit review
and an exact export receipt, not a count reserved by this design.

If implementation cannot satisfy the explicit-input authority limitation or needs durable default/
shared policy publication, stop: that is a separate source-design prerequisite. Fixtures may author
test policies and disposable source publications; they never become runtime defaults or source truth.

## 21. Implementation acceptance matrix

The stable cases below are **future acceptance requirements, not tests implemented by this PR**.
P = pure public-interface test; PG = actual PostgreSQL capture/source test; B = static/compatibility
check. Every case must have a named implementation test and receipt. Parameterized expansions are
welcome; they do not replace a listed branch or real-PG obligation. No CFP IDs are reused.

### Identity and ownership — TF01–TF12

| ID | Layer | Scenario / required observation |
| --- | --- | --- |
| TF01 | PG | Canonical same-household participating member: capture/derive/validate agree on one exact subject, all retained owner sources and actual projection fingerprint. |
| TF02 | PG | A SHARED participant may be selected explicitly; tracked_member_id remains grounding context and is not silently substituted as preference owner. |
| TF03 | PG | Actor with no household membership fails capture; caller-authored access/ready flags do not grant permission. |
| TF04 | PG | Existing household member absent from candidate participants fails SUBJECT_MEMBER_NOT_IN_CANDIDATE_CONTEXT; no implicit participant addition. |
| TF05 | PG | Another household's member or request fails owner validation without preference reads for that foreign subject. |
| TF06 | PG | Replace expected grounding fingerprint: frozen ingress rejects mismatch; no fresh candidate silently substituted. |
| TF07 | P | Change retained projection fingerprint and rehash only outer result: full primitive replay rejects. |
| TF08 | P | Same stable Recipe with another RecipeVersion cannot reuse the old result, source hash or projection binding. |
| TF09 | P | Change selected tier/rule/delta/path while retaining old feature or member result: candidate proof/replay rejects. |
| TF10 | P | Title, latest-version selector, alias or implicit-current-candidate fields reject rather than resolve another subject. |
| TF11 | PG | Distinct actor/subject with existing authorized household read is retained correctly; no SELF authorship/publication right is inferred. |
| TF12 | PG | Fresh canonical capture records its newly created projection identity; passing an expected old-projection field rejects, while exact retained sources replay without refresh. |

### Target admission — TF13–TF28

| ID | Layer | Scenario / required observation |
| --- | --- | --- |
| TF13 | P | DIRECT_RECIPE proves the stable Recipe ID, retains version/path outer binding and maps only the exact member Recipe target. |
| TF14 | PG | INGREDIENT proves the actual selected canonical ingredient; a substituted-away ingredient is absent and receives no fit contribution. |
| TF15 | PG | PROTEIN comes only from frozen MAIN_PROTEIN PRESENT with exact-path reviewed Catalog support; term kind remains PROTEIN. |
| TF16 | P | METHOD-only projection keeps child path=None and outer candidate path; the same frozen METHOD classification is consumed without new path rules. |
| TF17 | PG | FLAVOR admits only exact reviewed positive finite term IDs for the selected authored path. |
| TF18 | P | Supported candidate kind excluded by policy remains proven PRESENT but NOT_ADMITTED, with no fit mapping or numeric zero. |
| TF19 | P | A sixth kind, MAIN_PROTEIN preference target, role alias or unsupported target discriminator rejects TARGET_KIND_UNSUPPORTED. |
| TF20 | PG | Canonical nonselected ingredient/recipe diagnostic probe is ABSENT; nonexistent identity fails capture instead of becoming absent. |
| TF21 | P | Frozen unresolved feature reasons (no source/scope, partial, retracted, stale) survive verbatim; no positive/neutral candidate target is fabricated. |
| TF22 | P | REVIEWED_NONE dimension remains finite classification absence; probe resolution uses the frozen covered universe, not blanket absence. |
| TF23 | P | Title/category/family/nearest-term/dominant-mass changes cannot mint target membership or replace exact IDs. |
| TF24 | P | PARTIAL review with known positive admits that positive but preserves uncovered unknowns; no completeness claim or zero contribution for unknowns. |
| TF25 | P | Policy-admitted feature dimension not captured yields DIMENSION_NOT_CAPTURED diagnostics; existing captured dimensions are not reinterpreted as full coverage. |
| TF26 | P | Same ingredient selected in multiple requirements yields one exact target row with all proof refs; no multiplied contribution. |
| TF27 | P | Diagnostic probes cannot trim the base target set, become positive because a declaration exists, or enlarge frozen feature capture to resolve TERM_NOT_CAPTURED. |
| TF28 | PG | MAIN_PROTEIN support replacement/staleness is replayed from retained sources; an Ingredient→PROTEIN association alone does not establish dish main protein. |

### Member state and strength — TF29–TF44

| ID | Layer | Scenario / required observation |
| --- | --- | --- |
| TF29 | P | Current LIKE under RAW_EXPLICIT selects exactly040B's value and the matching positive fit row; direct declaration identity survives. |
| TF30 | P | Current DISLIKE selects a matching negative authored fit row and retains DECLARED_DISLIKE as a soft member signal. |
| TF31 | P | Current NEUTRAL requires an explicit semantic/value mapping to fit0/1; a nonzero frozen raw neutral coordinate is not silently replaced before lookup. |
| TF32 | P | UNDECLARED + NO_EVIDENCE gives unavailable MEMBER_UNDECLARED with strength NONE, no neutral fit. |
| TF33 | P | Destination RETRACTED suppresses raw/prior/inherited alternatives with no fit amount, even if older LIKE or prior remains retained. |
| TF34 | P | Genuine available source zero remains an exact lookup operand; an authored LIKE-zero source mapping may produce positive fit and is not treated as missing. |
| TF35 | P | LOW explicit strength remains exact lineage; no implicit0.25 coefficient or new eligibility threshold. |
| TF36 | P | MEDIUM explicit strength remains exact lineage; no implicit0.5 coefficient. |
| TF37 | P | HIGH explicit strength remains exact lineage; no automatic universal weight or extra taste preference. |
| TF38 | P | NONE belongs to no active declaration; prior-only/inherited output does not promote it or copy parent strength. |
| TF39 | P | Caller-authored strength/confidence/sample-count or numeric-strength policy fields reject rather than override frozen derivation. |
| TF40 | PG | Idempotent retry/history length cannot increase strength, target count or fit; only newly captured source identity may change. |
| TF41 | PG | Corrected current declaration changes fresh replay as frozen semantics require; old retained capture remains historically replayable. |
| TF42 | P | Missing fit mapping for a direct DISLIKE withholds amount but retains the direct soft signal; no hard exclusion/safety result is issued. |
| TF43 | P | Prior/inherited unfavorable fit cannot mint DECLARED_DISLIKE or a veto; weak affinity remains its own lineage. |
| TF44 | P | Other participants and portion factors never multiply/copy the selected member's preference contribution; no secondary-member fits are generated. |

### Exact-target prior modes — TF45–TF56

| ID | Layer | Scenario / required observation |
| --- | --- | --- |
| TF45 | PG | Valid source with NO_PUBLICATION and current declaration yields frozen EXPLICIT_ONLY under EXACT_TARGET_EFFECTIVE, with prior missingness retained. |
| TF46 | P | Compatible explicit+prior blend is recomputed by PR #100 and mapped exactly once; no second weighting/blend is applied. |
| TF47 | P | UNDECLARED + PRIOR_ONLY consumes only actual PRIOR_ONLY_COLD_START, preserves NO_DECLARATION and strength NONE. |
| TF48 | PG | Selected PRIOR_ONLY with successful empty prior capture stays unavailable; no raw, inherited, zero-prior or neutral fallback. |
| TF49 | PG | Prior retraction reason remains observable; declared exact-target may legitimately become explicit-only on fresh capture. |
| TF50 | P | Unmapped published reference amount preserves PRIOR_VALUE_NOT_MAPPED and frozen fallback semantics, without approximate interpolation. |
| TF51 | P | Explicit-policy ID/version/fingerprint or shrinkage→compatibility binding mismatch fails frozen validation before fit lookup. |
| TF52 | P | Wrong reference coordinate/provider immutable command binding rejects; it is not turned into fabricated unavailable prior plus explicit success. |
| TF53 | PG | Required prior CAPTURE permission/connection failure aborts the whole envelope; it cannot masquerade as NO_PUBLICATION. |
| TF54 | P | Frozen EXPLICIT_ONLY mode without a corresponding fit mapping is unavailable; no RAW_EXPLICIT fallback under another descriptor. |
| TF55 | PG | Policy capture_mode=EXPLICIT_ONLY needs no prior session/provider and records NOT_REQUESTED_BY_POLICY, without claiming publication absence. |
| TF56 | P | Changing only shrinkage provenance with the same actual effective amount retains its source coordinate and fit descriptor, but changes complete result identity. |

### Hierarchy and coexistence — TF57–TF70

| ID | Layer | Scenario / required observation |
| --- | --- | --- |
| TF57 | PG | Eligible reviewed one-hop relation selects the correct parent and040C mapped-explicit transfer, then exact inherited fit mapping; no parent fit row is minted. |
| TF58 | P | Destination direct LIKE/DISLIKE/NEUTRAL suppresses inheritance regardless of parent magnitude; the authored declared branch alone is selected. |
| TF59 | P | Destination retraction wins over hierarchy and destination prior-only availability; no policy option can resurrect it. |
| TF60 | PG | Parent retraction makes selected inheritance unavailable under the exact frozen reason, with no destination-prior fallback. |
| TF61 | P | Parent prior-only cold start cannot supply inheritance; parent effective blend is never the transferred operand. |
| TF62 | PG | No relation / retracted relation / denied direction / missing policy retains frozen hierarchy source reasons, not invented neutral fit. |
| TF63 | PG | Multiple incoming relations remain unavailable before member eligibility filtering; no favorable parent or strongest row is chosen. |
| TF64 | P | A nested inherited result or recursive parent cannot enter frozen parent primitives or become another transfer parent. |
| TF65 | P | Wrong hierarchy destination or selected parent target rejects; matching kind alone is insufficient. |
| TF66 | PG | Valid DIRECT_RECIPE destination relation for another version/path is retained but selected inheritance is unavailable; a forged same-version binding rejects rather than being treated as mere inapplicability. |
| TF67 | P | A legitimate different SOURCE recipe/version remains parent lineage when the destination is candidate-relevant; it is not falsely forced to equal the candidate. |
| TF68 | P | Destination prior-only plus available inheritance, policy chooses PRIOR_ONLY: prior-only alone is mapped; inherited is retained NOT_SELECTED, no numeric comparison. |
| TF69 | P | Same coexistence, policy chooses ONE_HOP: inherited alone is mapped; prior remains NOT_SELECTED even when its magnitude is larger. |
| TF70 | P | Malformed optional/unselected parent or hierarchy child fails complete replay, even when a direct declaration would suppress its use. |

### Policy and coordinates — TF71–TF88

| ID | Layer | Scenario / required observation |
| --- | --- | --- |
| TF71 | P | Exact policy contract/id/version/body pins select the same finite mapping and output coordinate deterministically. |
| TF72 | P | Edit policy mapping/body and rehash only result: expected body pin or full replay rejects. |
| TF73 | P | Missing policy fails POLICY_MISSING, with no implicit built-in or fixture policy. |
| TF74 | P | Unsupported contract version or expected id/version mismatch yields POLICY_VERSION_MISMATCH, not nearest/latest policy selection. |
| TF75 | P | Duplicate composite mapping keys, duplicate kind groups or ambiguous selections reject rather than last-wins. |
| TF76 | P | A valid but unmapped full source descriptor is unavailable; equal amount in a different descriptor cannot match. |
| TF77 | P | Same rational across two target kinds requires their distinct authored mapping rows; one kind's rule never transfers implicitly. |
| TF78 | P | Missing admitted-kind configuration or capture mode inconsistent with selected view rejects; omitted kinds are not silently enabled. |
| TF79 | P | Reviewer/provenance label, matching hash or SELF authorship cannot turn explicit policy input into canonical publication, default selection or readiness authority. |
| TF80 | P | Raw explicit descriptor pins the complete040B policy; profile/inherited descriptors pin their complete frozen semantic coordinates. |
| TF81 | P | Zero source amount, declared NEUTRAL and NO_DECLARATION use distinct semantic keys; no amount-sign inference supplies a missing state. |
| TF82 | P | Sparse finite map misses the exact source rational: SOURCE_VALUE_NOT_MAPPED, never nearest row, clipping or interpolation. |
| TF83 | P | Equivalent declared-set order normalizes identically; changed semantic rows/body change policy identity even under the same id/version labels. |
| TF84 | P | Missing resource/selection/fit values reject; no anonymous coefficient, duration, numeric-strength or production-default field is accepted. |
| TF85 | P | A coherently authored alternate policy with matching new pins yields a different conditional interpretation, without claiming a global publication lifecycle/version uniqueness. |
| TF86 | P | Any authored target/policy/source-size resource budget overflow returns RESOURCE_LIMIT; no history truncation, skipped targets or top-K ranking. |
| TF87 | P | Scoped numeric equality requires complete output descriptor: different member, candidate, target, kind or policy body forbids comparison/aggregation. |
| TF88 | P | Descriptor/semantic mismatches reject before any new fit processing; naked scalar or forged inherited/profile policy fingerprint cannot enter lookup. |

### Source coherence and capture — TF89–TF102

| ID | Layer | Scenario / required observation |
| --- | --- | --- |
| TF89 | PG | All per-target and parent preferences on one member RR cut share the full ledger identity despite different captured_at values. |
| TF90 | P | Parent/member input for another member rejects, even with the same numeric profile and household. |
| TF91 | P | Same UUID-like target/member payload from another household cannot satisfy owner identity or source manifest checks. |
| TF92 | PG | Prior/hierarchy/candidate/member captures with distinct legal clocks/frontiers are accepted without requiring one wall-clock timestamp. |
| TF93 | PG | Grounding as_of precedes a feature review visible at feature capture: frozen projection semantics are retained, not forced into historical AS_OF grounding policy. |
| TF94 | P | Conflicting same-typed immutable term/Recipe/RecipeVersion body anywhere in candidate/member/prior/hierarchy inputs rejects, including nested inputs. |
| TF95 | P | Same canonical ingredient ID with changed mutable display label across independent cuts is retained/fingerprinted without alias matching or false immutable-identity rejection. |
| TF96 | PG | Retained result replays after live declaration/prior/hierarchy correction; a fresh capture observes new owner cuts and never mutates old results. |
| TF97 | PG | Dedicated prior/hierarchy sessions enforce their own CAPTURE grants/SCRAM/TLS; ordinary household read or prior-root authority cannot authorize hierarchy capture. |
| TF98 | P | Offline consistent sources cannot claim canonical DB origin/current permission/common MVCC merely by editing provenance or equality flags. |
| TF99 | PG | Revoked source CAPTURE grant prevents fresh capture; no stale validated child is reused to bypass the protected path. |
| TF100 | PG | Concurrent source publication during an owner RR read yields that owner's coherent cut; independently captured owners are not falsely advertised as globally simultaneous. |
| TF101 | PG | Dirty/non-read-only/incorrect-isolation sessions, wrong configured database or any required read failure produce no partial source/result and no commit/role switch. |
| TF102 | P | Same member frontier with different retained ledger body is incoherent; unrelated retained source-history/frontier changes affect identity even with unchanged fit rows. |

### Replay and tamper resistance — TF103–TF116

| ID | Layer | Scenario / required observation |
| --- | --- | --- |
| TF103 | P | Repeated pure derivation from identical serialized sources yields identical structured rows, diagnostics and fingerprints. |
| TF104 | P | Declared new sets normalize by exact keys; frozen journal/Decimal/ordering semantics remain unchanged; duplicate semantic keys reject. |
| TF105 | P | Change an unselected valid source cut, diagnostic probe, capture frame or source history: complete source/result identity changes, even when available fit amounts do not. |
| TF106 | P | Edited cached projection/grounding, rehashed by caller, fails full frozen primitive recomputation. |
| TF107 | P | Edited cached explicit/member-strength output fails owner replay; caller state/count cannot override the ledger head. |
| TF108 | P | Edited prior mapping/blend/cached result fails PR #100 and full TasteFit replay, including malformed currently unused child. |
| TF109 | P | Edited hierarchy parent/trace/attenuation/coefficient or source support fails040C/source replay rather than being trusted as an inherited value. |
| TF110 | P | Edited selected mode, mapping row, fit amount, direct signal, missingness, proof or flags rejects even after recomputing only outer hashes. |
| TF111 | P | model_construct bypass at any nested policy/source/result level is reparsed to primitives and cannot mint validity. |
| TF112 | P | model_copy(update=...) nested tampering is treated the same as untrusted JSON and rejects. |
| TF113 | P | Descriptor stripping/forged kind/member/candidate/policy fingerprint is detected before fit mapping; equal rationals supply no authority. |
| TF114 | P | DB/network/filesystem/live-clock/environment/cache traps confirm zero I/O throughout pure derivation and semantic validation. |
| TF115 | P | Policy/output/source hash construction has no self-field recursion; canonical rational/UTC forms and full semantic bodies determine identity. |
| TF116 | P | Validator returns a fresh recomputed result and compares complete semantic content, not merely hash equality or parsing success. |

### Separation, retention and persistence — TF117–TF132

| ID | Layer | Scenario / required observation |
| --- | --- | --- |
| TF117 | B/P | MTR-039 learned/event payloads and routing dependencies are forbidden; current explicit evidence needs no router. |
| TF118 | P | Cooked/consumed/skip/rejection events cannot become liking or a new direct declaration. |
| TF119 | P | NO_TIME/OUT_OF_STOCK/price/equipment/context friction cannot alter target-fit mapping operands or preference truth. |
| TF120 | P | Passive/autopilot/forced-conflict signals reject; no durable voluntary taste is inferred. |
| TF121 | B/P | Frozen041 repeat chains and proposal-local exposure cannot be inputs, multipliers, missingness substitutes or fit totals. |
| TF122 | B/P | No history/novelty/exploration admission dependency; REVIEWED_NONE never becomes never-exposed. |
| TF123 | P | Valid candidate safety/nutrition/context changes may change subject identity but do not enter fit arithmetic; favorable taste cannot certify/override unsafe grounding. |
| TF124 | P | Inventory/procurement/SPEND_LIMIT values cannot become fit weights or a hard-feasible status. |
| TF125 | P | MAIN_PROTEIN feature remains PROTEIN preference identity, not meal-role taxonomy or a role-aware nutrition score. |
| TF126 | P | No cross-candidate comparison/ranking or convenience total can be requested, returned or inferred from coordinate equality. |
| TF127 | P | No household/shared-meal reducer, multi-member profile copy or cross-dimension sum exists; exact single-member ownership persists. |
| TF128 | P | planner_ready/activation_ready and non-authority literals cannot be promoted via JSON, policy extras or model construction. |
| TF129 | PG | Capture runs read-only, preserves all watched owner rows/frontiers/schema and performs no publication/cache/profile/TasteFit write or transaction commit. |
| TF130 | B | Frozen040/019C/046A/projection files and0001–0015 remain byte-exact; only new companion interfaces/guards are added after approval, with existing import restrictions retained. |
| TF131 | B | All3,104 baseline test identities/assertions remain; new TF cases add coverage rather than rewriting old semantics or genericizing041B/C/D. |
| TF132 | PG/B | Head stays0015 with85 domain tables and no0016/production seed/default rows; all362 old export definitions remain unchanged, with only the separately reviewed new TasteFit shapes added. |

**132 stable cases: TF01–TF132.** Each PG obligation must use actual owner captures/publication
fixtures and authenticated disposable PostgreSQL, not simulated booleans or a pure-collection count.
Implementation receipt must map every ID to test names/results and exact-head CI. No acceptance
case is evidence of implementation merely because it appears in this design document.

## 22. Explicit non-goals

No member preference write or materialized MemberBehaviorProfile; no cross-target inference beyond
consuming existing frozen040C lineage; no recursive hierarchy, parent aggregation or inherited strength;
no inferred candidate classification; no new prior/provider fallback; no global policy publication;
no shared-member reducer; no ranking, portfolio, solver, full MTR-024, novelty or RepeatPenalty;
no MTR-039, history model, remaining041/046 expansion, Execution, PRECOMMIT or planner activation.
No production fit values, weights, defaults, source corpus, grants, endpoint, persistence or migration.

## 23. Remaining downstream blockers

| Work | Status after this design PR |
| --- | --- |
| Candidate-bound feature projection | FROZEN, unchanged; this design is a separate additive consumer proposal |
| MTR-040 / issue #41 | COMPLETE / CLOSED — COMPLETED; frozen040A/B/C and supporting sources unchanged |
| TasteFit foundation | DESIGN READY FOR ARCHITECTURE REVIEW; not implemented, not frozen, no new MTR suffix |
| MTR-039 | OPEN; attributed event admission/correction and actual applicable producers remain separate |
| Full MTR-041 / MTR-046 | PARTIAL / PARTIAL; local repeat is not global history/novelty; coverage/role/effort/family/safety sources remain incomplete |
| MTR-024 | BLOCKED; full separable input/participant/context policies and Stage-1/tolerance/utility semantics are not supplied here |
| MTR-020B | BLOCKED; meaningful EXPLOIT, covered novelty/EXPLORE, structural roles and explicit quota/reserve policies remain |
| MTR-021 | BLOCKED; root nutrition/goal/plan policy, applicable safety, procurement scenarios/cost, portfolio and planned material flow remain |
| Execution / PRECOMMIT / planner activation | NOT STARTED / FAIL-CLOSED / NOT AUTHORIZED |

## 24. Implementation-readiness verdict and stop rule

The design closes the scoped policy/source questions without inventing a durable publisher: full
source evidence stays owned by frozen sources; conditional interpretation is explicitly selected
and versioned; structured output has no aggregate/comparability/authorization claim. The remaining
work is architecture review of this design, especially explicit-input authority, authored selection,
finite mapping, multiple owner cuts, public companion seams and the132-case matrix.

**Implementation is not authorized.** Green documentation CI is not architecture approval or a
production policy decision. If review requires canonical shared policy publication rather than
conditional explicit interpretation, the verdict for that expanded scope becomes DESIGN BLOCKED
on a separately reviewed policy-source authority; do not hide it in a fixture or constant.

This task stops with a separate docs-only PR, left OPEN. Do not merge it automatically, implement
TasteFit, assign a milestone, close another parent issue or begin any downstream design/implementation.
