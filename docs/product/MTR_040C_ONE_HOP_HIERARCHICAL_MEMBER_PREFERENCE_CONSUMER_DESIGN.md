# MTR-040C — One-hop Hierarchical Member Preference Consumer Foundation

Status: **MTR-040C FROZEN / APPROVED**.
Exact implementation head `b138ae7eee9ca9a94dd0a00a0f4e2eb0782d80b0` was accepted by the user
in [review receipt6434925372](https://github.com/thedusk4203/Menuto/pull/107#issuecomment-6434925372).
PR #107 merge/main/freeze SHA is `69241affc2d85ee534ca682a0ff9a4d23a7c7862`;
exact push [CI40459191498](https://github.com/thedusk4203/Menuto/actions/runs/40459191498) SUCCESS,
python/web;2,978 tests;358 definitions;0015 /85 tables. The user declared FROZEN after verification.

The [accepted parent review and closure receipt](POST_MTR_040C_PARENT_MTR_040_COMPLETION_REVIEW.md#12-approved-closure-receipt)
record **MTR-040 COMPLETE / issue #41 CLOSED — COMPLETED** after PR #108 merged at
`959e7fa3488e0c379ab37044c25da74292c2d76b` and exact push CI 40486320021 succeeded.
Original design/delivery-stage authorization wording below is historical; this header supersedes
status only. Frozen semantics and HC01–HC81 remain unchanged. No downstream implementation.

## 1. Canonical basis and authorization

| Basis | Exact receipt |
| --- | --- |
| Repository | `thedusk4203/Menuto` |
| Design branch base / freeze-readiness documentation merge | `eeaea0a969a732946e25aeb67ff501869bc51a9d`, [PR #105](https://github.com/thedusk4203/Menuto/pull/105) |
| Exact docs-freeze post-merge push CI | [40444577292](https://github.com/thedusk4203/Menuto/actions/runs/40444577292), SUCCESS on that exact base; python/web SUCCESS;2,807 tests |
| Hierarchy SOURCE implementation freeze | `ee8a4de1b1c71ccbd56ea565e111718660711fa8`, [canonical receipt](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_FREEZE_RECEIPT.md) |
| Exact SOURCE post-merge push CI | [40432057006](https://github.com/thedusk4203/Menuto/actions/runs/40432057006), SUCCESS, python/web SUCCESS |
| Approved dependency selection | [Post-freeze review](POST_HIERARCHY_SOURCE_FREEZE_DEPENDENCY_REVIEW.md), PASS; MTR-040C selected for detailed design |
| Frozen runtime baseline | 2,807 tests; 349 domain definitions; Alembic0015 /85 domain tables |
| Other frozen dependencies | 040A/B,041A–F,046A, reviewed exact-target reference-prior source, PR #100 exact-target compatibility/shrinkage |
| Authorized activity | Detailed consumer DESIGN only; no implementation, new migration or production transfer content |

The [SOURCE design](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_DESIGN.md) §§7–11 and
[neutral-anchor correction](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_NEUTRAL_ANCHOR_CORRECTION.md)
already constrain the consumer. This proposal fills the consumer input/output, ordering,
same-member-history, arithmetic and replay seams without changing those frozen decisions.
It does not reopen the SOURCE trust root or turn a captured source into a live authorization token.

## 2. Selected scope and ownership

Preferences owns one pure module whose interface interprets **one destination for one member,
through at most one reviewed one-hop relation**. Its future public entry point is proposed as:

```text
derive_one_hop_hierarchical_member_preference(subject)
    -> OneHopHierarchicalMemberPreferenceDraft
```

Proposed implementation location, only after authorization:

- `preferences/hierarchical_affinity_contracts.py`: new additive immutable contracts and replay guards;
- `preferences/hierarchical_affinity.py`: pure orchestration, exact lookup and attenuation;
- one additive lazy facade in `preferences/public.py`;
- tests through that same interface, preserving all frozen baseline tests.

Dependencies are in-process frozen computations over supplied immutable primitives. No repository,
DB session, clock, network client, file loader, new adapter or generic graph/policy engine belongs
in this interface. The existing SOURCE capture interface remains its own independently authorized
operation; this module neither authenticates a live caller nor performs a capture.

No batch profile, persistent result/cache, MemberBehaviorProfile update, household/candidate
aggregation, learned observation, MTR-039 routing, exposure/repeat/novelty, TasteFit, planner utility,
hard-safety authority, Execution, PRECOMMIT or production corpus is included. No frozen result is
genericized to carry inherited amounts. Full MTR-040 remains PARTIAL; issue #41 is not closed.

## 3. Proposed contract responsibilities

Names below describe the proposed interface; no executable class/export is added in this PR.

| Proposed contract | Responsibility |
| --- | --- |
| `OneHopHierarchicalMemberPreferenceInput` | Complete destination PR #100 input, optional complete parent PR #100 input and complete frozen hierarchy-source snapshot |
| `InheritedMemberPreferenceCoordinate` | Complete frozen inherited-coordinate descriptor; derived from selected published policy and exact destination kind |
| `InheritedMemberPreferenceAmount` | Canonical bounded rational numeric component; never an accepted root input or standalone authority |
| `ScopedInheritedMemberPreference` | Descriptor and amount inseparable; no public conversion/comparison/aggregation operation |
| `InheritedPreferenceTrace` | Recomputed semantic key, verified parent operand, authored row, mapped inherited value, attenuation and final scoped product |
| Available / Suppressed / Unavailable inherited outcome | Tagged mutually exclusive value versus policy suppression versus valid missing/incompatible source/evidence state |
| `OneHopHierarchicalMemberPreferenceDraft` | Original primitives, recomputed frozen children, member/exact relation/context bindings, trace/outcome, fingerprints and fixed non-authority flags |

All new contracts are immutable, extra-forbid, and reconstruct canonical primitives even when
given an existing model instance. Strict flags reject booleans disguised as numbers or strings
disguised as flags. Cached child outputs, naked scalars, caller statuses, caller fingerprints and
`model_construct` instances cannot bypass reconstruction/recomputation.

The root has no caller-writable EvidenceStrength or final globally comparable member score.
The inherited outcome's amount exists only in the Available branch; Suppressed/Unavailable branches
carry no amount, no zero placeholder and no default weight.

## 4. Input seam and conditional parent requirement

The input contains exactly:

```text
destination: ExactTargetPriorBackedAffinityInput
parent: ExactTargetPriorBackedAffinityInput | None
hierarchy_source: HierarchySourceSnapshotDraft
```

Both PR #100 children retain their frozen **one identical target per explicit/reference input**
requirement. They are composed, never widened to two targets or synthesized by slicing/relabeling
another capture. The hierarchy request must name exactly the destination's one typed target.
Its full provider journal/history still includes all relations, competing heads and owner support;
the single-destination request is not permission to omit unfavorable provider facts.

There is no caller-supplied alternate provider, policy, relation ID, parent selector, eligibility,
mapping row, coefficient or current time. Provider/policy selection comes from the frozen captured
hierarchy request; the unique relation comes from recomputed source resolution. Reference-prior
provider selection remains inside each unchanged PR #100 input and grants no hierarchy authority.

Parent is optional so callers can represent direct suppression, policy absence or ambiguous source
without inventing a parent declaration/reference capture. After all provided primitives validate:

- a direct/retracted destination, or an unavailable hierarchy row, does not require parent input;
- an UNDECLARED destination with exactly one ELIGIBLE_RELATION **requires** a complete parent input;
- missing required parent is an input failure, never PARENT_UNDECLARED, default zero or a guess;
- every provided parent is fully recomputed and owner/history checked, even if the ultimate outcome
  is suppressed/unavailable. A malformed optional input is not silently ignored;
- when the source is eligible, provided parent target must exactly equal the selected relation
  source. Wrong target/member is input forgery, not a selectable fallback;
- when the source is unavailable, a provided valid parent cannot override source diagnostics or
  make a favorable parent count as the selected relation.

This interface returns a deterministic interpretation of supplied primitives. Capture orchestration
and provisioning actual production policies/relations remain outside the slice.

## 5. Same-member history consistency

Parent and destination must name the same exact household/member. In addition, when parent is
provided, both explicit inputs must contain **the same complete member declaration ledger**.
Comparing only member IDs is insufficient: a newer parent cut plus an older UNDECLARED destination
cut could hide a later direct declaration/retraction already visible in that member's history.

Define a consumer-only canonical ledger projection from the already validated frozen
`ExplicitMemberPreferenceSnapshot`:

- retain contract/coverage metadata, household_id, member_id, frontier and every declaration fact;
- sort declarations by member_sequence and vocabulary facts by exact ID, preserving full contents;
- retain all recorded times, authorship, stream/revision/predecessor IDs, target kinds and values;
- exclude only the snapshot's `captured_at` observation clock from this comparison projection.

Compare the full projected primitive bodies, not supplied hashes. Different frontier, declaration,
vocabulary fact or metadata yields input failure `INCOHERENT_MEMBER_HISTORY`. The derived
`member_ledger_fingerprint` hashes that projection under a new consumer-specific domain. It is
lineage, not a credential or a replacement for complete member history.

Capture request/manifests and both original capture clocks remain intact in the input and result.
Two independently captured per-target inputs can satisfy this condition without one global
transaction if the member history did not change. Callers may also capture the existing per-target
sources in one appropriate transaction; this design adds no capture helper or authority protocol.
Different ordering of equivalent ledger facts may share this projection while frozen child/source
fingerprints still retain their original serialized identities. Exact-input replay remains stable.

Repeated facts that frozen owner contracts declare immutable must also agree across the supplied
children and hierarchy cuts: in particular, the same feature-term ID/full fact and the same stable
RecipeFact ID/full fact in endpoint manifests or pinned recipe contexts cannot have contradictory
bodies. Compare by typed fact kind plus exact ID, never UUID alone across different fact kinds.
Conflicts are input failures, not a newest/favorable version choice. This does not make
mutable display metadata an identity rule: ingredient labels never create aliases or relation
permission, and canonical typed IDs remain the target keys. Frozen SOURCE already verifies its
own repeated immutable RecipeVersion/support facts; do not replace that child validation.

This narrow same-member requirement does **not** require one simultaneous cut for reference priors,
hierarchy authority, Catalog/Recipes support and every policy. Those independent immutable cuts
remain separately labeled as specified in §12. There is no simultaneous-current or live-state claim.

## 6. Deterministic validation and outcome order

Input failures take precedence over any numeric/suppressed outcome. Reparse every supplied primitive,
recompute destination and any provided parent with frozen040B/PR #100, and independently resolve the
complete frozen hierarchy source. Validate request/owner bindings and §5 ledger consistency.
If an eligible source and a parent are both provided, exact parent-to-relation target binding is
also a common input check, including when destination policy will suppress inheritance. No child
cache supplies authority. After those common checks, apply this exact order:

| Order | Condition | Result; no hierarchy arithmetic before all Available gates pass |
| --- | --- | --- |
| 1 | Destination raw state RETRACTED | Suppressed, reason `MEMBER_RETRACTED` |
| 2 | Destination raw state DECLARED (LIKE/DISLIKE/NEUTRAL) | Suppressed, reason `DESTINATION_DIRECT_DECLARATION` |
| 3 | Destination UNDECLARED; hierarchy row UNAVAILABLE | Unavailable, reason `HIERARCHY_SOURCE_UNAVAILABLE`, preserving the exact frozen source reason/support/per-head diagnostics |
| 4 | Destination UNDECLARED; source eligible; parent missing | Input failure `MISSING_REQUIRED_PARENT_INPUT` |
| 5 | Parent raw state RETRACTED | Unavailable, reason `PARENT_MEMBER_RETRACTED` |
| 6 | Parent UNDECLARED; PR #100 prior-only cold start | Unavailable, reason `PARENT_PRIOR_ONLY_COLD_START` |
| 7 | Parent UNDECLARED without compatible prior | Unavailable, reason `PARENT_UNDECLARED` |
| 8 | Parent DECLARED; valid parent interpretation/compatibility differs from the published binding | Unavailable, reason `INCOMPATIBLE_COORDINATE` |
| 9 | Parent DECLARED; published finite semantic row absent | Unavailable, reason `SOURCE_VALUE_NOT_MAPPED` |
| 10 | All identity, policy, semantic/operand and coordinate gates pass | Available scoped inherited suggestion; exact mapped amount × exact authored attenuation |

Rows1–2 preserve source diagnostics even if that source is ambiguous/unavailable, but direct member
policy suppresses application. That is no source-eligibility override and produces no inherited
amount. Invalid source history/capture proof still fails common validation; it is not masked by a
direct declaration. A parent supplied while suppressed must still be valid and share member history;
no relation-source match is asserted where the source has no eligible unique relation to match.

Wrong provided parent target fails `PARENT_TARGET_MISMATCH` in common validation. Different valid
published/parent policies at row8 are observable incompatibility, not conversion.
Forged descriptors or inconsistent policy bodies/hashes are input failures in common validation,
not row8. No exception is caught and converted to AVAILABLE zero. Exact exception class/text may
follow repository conventions; the failure versus valid-outcome categories above are normative.

## 7. Parent eligibility and prior isolation

| Recomputed parent | Inheritable operand |
| --- | --- |
| DECLARED + EXPLICIT_ONLY | `mapped_explicit.value` and its verified semantic lineage only |
| DECLARED + BLENDED_EXPLICIT_AND_PRIOR | The same `mapped_explicit.value`; never effective blended value or weighted contribution |
| PRIOR_ONLY_COLD_START | None; unavailable, not member evidence |
| UNDECLARED / RETRACTED | None; distinct reasons as above |
| Previous inherited result | Invalid input type; never a parent |

For DECLARED parents, frozen PR #100 guarantees mapped_explicit exists and the effective mode is
one of the two eligible modes. Recompute/assert that relationship; a forged contradictory child
fails rather than inventing a new eligibility rule. Semantic state comes from040B's current
declaration, never from either raw or mapped rational sign.

Prior or shrinkage changes can alter the recomputed child's mode/effective value and fingerprint.
With the same valid explicit/compatibility/hierarchy mapping, they must not change the inherited
amount or coordinate: neither prior operand, prior influence weight, contribution nor blended
effective value enters hierarchy arithmetic. Their complete child provenance still changes the
composite result fingerprint. A shared reference prior never becomes an inherited member assertion.

Explicit EvidenceStrength remains NONE/LOW/MEDIUM/HIGH inside frozen child lineage. No strength
value, statistical confidence, probability, review count, path length or repeated history supplies
attenuation or a new inherited strength. The inherited outcome exposes no derived ordinal strength.

## 8. Raw semantic binding, mapped operand and finite lookup

This is the bridge between the two frozen interfaces; it introduces no new mapping semantics:

1. Recompute the raw040B state, raw amount and current declaration head from complete primitives.
2. Recompute PR #100 and obtain its mapped_explicit operand with the full source-kind/compatibility
   descriptor. Check its outer member/target, semantic rule_key and mapped amount against the
   complete authored compatibility mapping; never trust a detached ScopedMemberProfileAffinity.
3. From the eligible relation's exact current published transfer policy, revalidate the pinned
   complete040B explicit-policy body and PR #100 compatibility body/fingerprints. Valid different
   parent bodies are INCOMPATIBLE_COORDINATE; forged/internally inconsistent bodies fail input validation.
4. Require the parent descriptor to equal the published compatibility coordinate for the exact
   source kind, including family/version/unit/scope/full compatibility fingerprint.
5. Call the frozen policy semantic lookup for exact source kind, destination kind and raw semantic
   DISLIKE/NEUTRAL/LIKE. Revalidate the returned row against the selected published policy.
6. `expected_source_amount` must equal the corresponding **raw040B explicit-rule amount**, while
   the row's source_descriptor must match the recomputed **PR #100 mapped-explicit descriptor**.
   These are two checks at different coordinates. Do not compare the raw expected amount directly
   with the mapped PR #100 scalar or substitute either into an implicit numeric conversion.
7. The row's authored output_amount is the mapped value in the new inherited coordinate. Only
   this inherited mapped value is multiplied by the row direction's authored attenuation.

The finite lookup is an authorized interpretation of the verified mapped-explicit semantic lineage,
not interpolation of its numeric position. The correction intentionally carries semantic state
because raw or mapped NEUTRAL can be nonzero under frozen policies. No nearest row, implicit zero,
identity coercion, sign-derived label, affine conversion or prior-backed scalar lookup is defined.

## 9. Inherited coordinate and exact rational trace

The descriptor is exactly the frozen architecture's new coordinate:

```text
coordinate_id = INHERITED_MEMBER_PREFERENCE
coordinate_version = 1
destination_target_kind
transfer_policy_semantic_fingerprint
unit = REVIEWED_TRANSFER_POLICY_UNITS
scope = ONE_TRANSFER_POLICY_ONE_DESTINATION_KIND_BOUND_EXACT_RELATION
```

`transfer_policy_semantic_fingerprint` is the **existing frozen full**
`HierarchyTransferPolicy.fingerprint()` over its canonical published body. Do not invent a reduced
numeric-only or provenance-excluding hash. Build the descriptor after hashing; it is not inserted
into its own hash preimage. Policy revision/stream/provider/journal identities are additionally
retained in outer lineage, never silently substituted for policy-coordinate identity.

The scoped value carries descriptor plus canonical amount inseparably. The outer result binds exact
household/member, source/destination targets and relation/context; these IDs are not implied by a
matching coordinate. Same descriptor + same rational permits scoped numeric equality only. It grants
no exact-target equality, cross-relation transfer/aggregation/ranking or planner utility comparability.
Different descriptor has no defined comparison/aggregation operation. There is no conversion back
to040B direct affinity, reference anchor or PR #100 MEMBER_PROFILE_AFFINITY.

Before constructing a Fraction or multiplying for the hierarchy transfer, validate the published row, its descriptor, typed
endpoints and complete policies. Construct the mapped inherited scoped value under the derived
descriptor; revalidate that exact descriptor before attenuation. The only arithmetic is:

```text
mapped = authored row output a/b
attenuation = authored positive coefficient c/d
inherited = reduce_exact((a*c)/(b*d))
```

Authored row/coefficient components retain frozen31-bit bounds; denominator positive, gcd=1,
signed magnitude≤1, zero exactly0/1; strict JSON integers only. Attenuation satisfies0<c/d≤1.
Derived product components are bounded by2^128−1 after exact reduction, with positive denominator,
canonical zero and no rounding, clipping or saturation. Reject oversized serialized result values.
Valid two-factor31-bit products fit inside128 bits; acceptance must not pretend overflow is
reachable from otherwise valid V1 factors. The guard still rejects malformed/oversized inputs/results.

Trace retains semantic key, raw expected amount, full mapped-explicit operand, authored row/policy
fingerprint, mapped inherited scoped value, exact coefficient and final scoped product. NEUTRAL
maps to0/1 and stays exactly0/1 after attenuation; it is AVAILABLE, never missingness. DISLIKE
cannot map positive, LIKE cannot map negative, and attenuation cannot reverse sign/amplify magnitude.
No numeric production defaults/examples, recipe-repeat weights or strength-derived coefficients
are introduced by this design.

Frozen PR #100 child recomputation may perform its own already-validated shrinkage arithmetic to
reconstruct truthful lineage. The gates above precede **new hierarchy transfer arithmetic**; they
do not bypass frozen child replay or claim that its independent numeric computation never happens.

## 10. Destination precedence and separate exact-target result

Destination raw state is taken from the recomputed destination040B child, not the sign or mode
of its PR #100 effective value. LIKE, DISLIKE, NEUTRAL and explicit zero all suppress inheritance.
RETRACTED gives MEMBER_RETRACTED, never neutral and never automatic re-inference. UNDECLARED alone
permits the remaining gates. Correcting/retracting either endpoint requires a fresh composite input;
no old inherited cache is reused.

The complete destination PR #100 result is retained **unchanged as a separate component**. A
destination prior-only result is neither a direct declaration nor an inheritance parent. If all
hierarchy gates pass, prior-only exact-target value and inherited suggestion may both be visible
as separate components; no effective chooser, blend, sum, precedence-by-magnitude or shared scale
between them is defined. Destination's valid independent interpretation/prior policies need not
become globally owned/defaulted by hierarchy publication. Only the parent transfer operand must
match the published compatibility binding; destination's raw declaration still controls precedence.

## 11. SOURCE delegation, context and graph restrictions

Use frozen `resolve_hierarchy_sources()` on the complete source input. Preserve its selected-policy
state before incoming-head count and its exact reasons/diagnostics. Two active incoming heads remain
MULTIPLE_INCOMING_RELATIONS before member eligibility/support/mapping filtering, including same
source/different contexts, stale support, opposite member signs and diamonds. Supplying only one
parent child never reduces this count. Retracted heads remain diagnostic history as frozen.

Do not reinterpret classification. Frozen SOURCE validates REVIEWED_EXACT_PAIR versus
CLASSIFICATION_BOUND_PAIR, Catalog positive membership/coverage and exact RecipeVersion/key/path/
MAIN_PROTEIN support. The consumer verifies the selected exact relation pin and propagates the
frozen support/context lineage, with no latest/default/proposal selection, alias, family fan-out,
inverse relation, automatic repin, favorable support omission or owner-state write.

No inherited value becomes another parent. No traversal, path search, recursive propagation,
multi-hop attenuation or parent aggregation is added. Cycles were already rejected/validated by the
frozen source; consumer replay delegates that validation and derives no graph-ranking result.

## 12. Result replay, fingerprints and mixed cuts

The root result contains original input primitives, recomputed destination/optional-parent040B and
PR #100 results, recomputed hierarchy resolution, common member-ledger fingerprint, exact outer
bindings, inherited outcome/trace and deterministic result fingerprint. Inherited amount-bearing
fields exist only in the Available branch; separate frozen child results keep their own amounts
unchanged. Suppressed/Unavailable inherited outcomes retain exact reasons without hidden values.

The proposed root shape is fixed at these responsibilities:

| Field | Recomputed meaning |
| --- | --- |
| `subject` | Complete original input; never replace its primitives with child hash strings |
| `household_id`, `member_id`, `destination_target` | Exact owner and typed target from destination input |
| `parent_target` | Exact provided parent target, or None when no parent was supplied; not an invented evidence parent from a source edge |
| `destination_exact_target` | Complete unchanged frozen destination PR #100 draft, including its040B/reference children |
| `parent_exact_target` | Complete unchanged frozen parent draft when supplied; otherwise None |
| `hierarchy` | Complete recomputed frozen hierarchy draft, including all source/per-head diagnostics |
| `member_ledger_fingerprint` | Consumer-only projection identity from §5, never input authority |
| `inherited` | The tagged outcome below |
| `fingerprint` and fixed guard literals | Complete consumer replay identity and §12 non-authority claims |

Outcome shapes:

```text
Available:
    status = AVAILABLE
    value = ScopedInheritedMemberPreference
    trace = InheritedPreferenceTrace

Suppressed:
    status = SUPPRESSED
    reason = MEMBER_RETRACTED | DESTINATION_DIRECT_DECLARATION

Unavailable:
    status = UNAVAILABLE
    reason = HIERARCHY_SOURCE_UNAVAILABLE | PARENT_MEMBER_RETRACTED |
             PARENT_PRIOR_ONLY_COLD_START | PARENT_UNDECLARED |
             INCOMPATIBLE_COORDINATE | SOURCE_VALUE_NOT_MAPPED
    source_reason = exact frozen HierarchySourceReason
                    iff reason == HIERARCHY_SOURCE_UNAVAILABLE
```

Non-Available outcomes do not have value, numeric trace or implicit coefficient fields. Available
trace binds exact source/destination, hierarchy provider/policy/stream/revision, relation identity
and recipe context directly to the eligible frozen child, in addition to §9's numeric lineage.
Its final scoped product must exactly equal `inherited.value`. A frozen child's diagnostic
`selected_relation` under an UNAVAILABLE status is never promoted to this Available trace.
Root owner/parent/destination plus this verified relation/context lineage supplies the exact outer
binding that the coordinate descriptor alone deliberately does not contain.

Result deserialization reparses the subject and independently recomputes every child, binding,
selected policy/relation, lookup, descriptor and product before comparing expected fields and hashes.
Never validate just the outer checksum or trust edited cached children. A shared private pure
derivation routine may serve the entry point and result validator without trusting its caller;
its call graph must remain bounded and must not recursively invoke the root validator forever.

The result fingerprint uses a new versioned consumer hash domain over the complete canonical subject
and all recomputed result fields, excluding only its own fingerprint field. Child fingerprints are
retained but cannot replace their primitive preimages. The fingerprint includes all raw capture cuts,
policies, full hierarchy history/manifests, unsuccessful diagnostics, separate destination prior
result and optional parent input, not merely the visible inherited amount or selected relation row.

Retain individually: parent/destination capture clocks and manifest identities, the shared member
ledger identity, each reference-source cut/provider/journal, compatibility/shrinkage fingerprints,
hierarchy provider/policy/journal/capture/reader proof and owner support cuts. Interpretation mode
remains VERSIONED_CONSUMER_POLICY_REPLAY. Policies may be later than captured facts according to
the frozen replay model; never relabel this AS_OF_CAPTURE policy knowledge.

Exact immutable inputs replay deterministically. Fresh relation/policy/support corrections change
fresh eligibility/coordinate/provenance without mutating old cuts. Fresh member changes require
both per-target member ledgers to be refreshed consistently. Independent prior/shrinkage changes
can change provenance without changing the inherited point, as §7 requires. No composite hash
proves simultaneous currency, current live grants, commit completion or canonical DB origin.

Fixed non-authority claims include member ownership preserved, EvidenceStrength NOT_DERIVED,
learned/contextual/passive evidence UNAVAILABLE, recursive transfer/parent aggregation/candidate
aggregation NOT_PERFORMED, TasteFit UNAVAILABLE, planner_ready=False and activation_ready=False.
Do not present inherited interpretation as a new DIRECT declaration or durable learned observation.
ADR-011 DIRECT/CONTEXTUAL/INFERRED/PASSIVE remain distinct; this slice ingests no new behavioral event.

## 13. Acceptance plan for a later authorized implementation

These are proposed acceptance obligations, **not new tests or a test-count commitment in this PR**.
All frozen baseline tests/definitions and migrations remain retained; this additive interface does
not replace frozen test suites. Tests cross the public pure interface/result-deserialization seam.
Use actual frozen child derivation/resolution on primitive fixtures, not mocks of cached child outputs.

| ID | Required observable acceptance |
| --- | --- |
| HC01 | All five typed kinds can be exact source/destination under an explicitly enabled published direction; no sixth MAIN_PROTEIN target kind. |
| HC02 | Destination PR #100 input retains one-target rule; empty/multiple/different explicit-reference targets fail. |
| HC03 | Hierarchy request must be exactly the destination target; wrong UUID/kind and batch request fail. |
| HC04 | Provided parent/destination household/member mismatch fails before lookup/arithmetic. |
| HC05 | Required parent omitted for UNDECLARED+eligible source fails; it does not become UNDECLARED or zero. |
| HC06 | Parent may be absent for direct/retracted destination or unavailable source, with honest suppressed/unavailable outcome. |
| HC07 | A provided malformed optional parent fails even when destination would otherwise suppress. |
| HC08 | Eligible relation source must equal exact provided parent outer typed target, including suppressed destination; equal fraction/label is insufficient. |
| HC09 | Caller eligibility/row/coefficient/parent-selector/actor/strength fields are extra-forbid. |
| HC10 | Existing model/model_construct input and dictionaries undergo identical primitive reconstruction. |
| HC11 | Same member IDs but different ledger frontiers fail INCOHERENT_MEMBER_HISTORY. |
| HC12 | Same frontier with changed declaration/body/authorship/revision/predecessor fails. |
| HC13 | Same ledger plus different capture clocks can compose; original clocks and child fingerprints are retained. |
| HC14 | A newer destination direct/retraction cannot be hidden by an older destination child paired with newer parent history. |
| HC15 | Complete ledger fact ordering is canonicalized for the comparison projection, without rewriting frozen child identities. |
| HC16 | Reference/hierarchy cuts may differ from member clocks; no simultaneous-current claim appears. |
| HC17 | Destination LIKE suppresses inherited amount regardless of parent sign/magnitude. |
| HC18 | Destination DISLIKE suppresses positive inheritance. |
| HC19 | Destination NEUTRAL suppresses inheritance even under a valid nonzero raw/mapped neutral policy. |
| HC20 | Declared explicit numeric zero suppresses; it is distinct from UNDECLARED. |
| HC21 | Destination RETRACTED returns MEMBER_RETRACTED and no inherited amount, even with prior/source available. |
| HC22 | Direct/retracted suppression retains unavailable/ambiguous source diagnostics without applying inheritance. |
| HC23 | Invalid source history/reader proof is not masked by destination suppression. |
| HC24 | Destination prior-only remains separate; it does not suppress or blend with an otherwise available inherited suggestion. |
| HC25 | Parent EXPLICIT_ONLY is eligible through its mapped_explicit semantic lineage. |
| HC26 | Parent BLENDED_EXPLICIT_AND_PRIOR uses mapped_explicit, never blended value/contribution. |
| HC27 | Parent PRIOR_ONLY_COLD_START is unavailable as parent. |
| HC28 | Parent UNDECLARED without prior returns PARENT_UNDECLARED, not NEUTRAL. |
| HC29 | Parent RETRACTED returns PARENT_MEMBER_RETRACTED; no fallback. |
| HC30 | An inherited result cannot satisfy the frozen parent input type or become a recursive parent. |
| HC31 | Changing only compatible prior source values may change child/result provenance but not inherited point. |
| HC32 | Changing only valid shrinkage weights/version may change child/result provenance but not inherited coordinate/point. |
| HC33 | Prior-only to explicit-only/blended eligibility requires a real member declaration, never a changed prior. |
| HC34 | Parent strength/authorship is retained in frozen lineage; no inherited LOW/MEDIUM/HIGH or confidence is minted. |
| HC35 | Source POLICY_MISSING/RETRACTED/SUPERSEDED are preserved as unavailable source reasons. |
| HC36 | NO_RELATION differs from RELATION_RETRACTED; neither produces zero. |
| HC37 | Multiple active incoming parents remain ambiguous with only one supplied/usable explicit parent. |
| HC38 | An unresolved/retracted-support competing parent is not omitted to obtain one favorable parent. |
| HC39 | Duplicate source/different contexts and diamond merge remain ambiguous; no dedup/sum/vote/max/newest choice. |
| HC40 | Frozen same/cross-kind/cycle/tombstone replay constraints are delegated without propagation. |
| HC41 | Ingredient partial positive support can remain eligible; reviewed-none/absent/unresolved stay distinct. |
| HC42 | METHOD/FLAVOR/MAIN_PROTEIN preserve exact frozen support/context semantics, with no new target kind. |
| HC43 | New RecipeVersion does not retarget a pinned relation; no latest/proposal/default-path inference. |
| HC44 | Fresh support/policy/relation correction changes fresh outcome, while old full-cut replay remains stable. |
| HC45 | Forged compatibility kind/fingerprint relative to its full policy fails before new hierarchy transfer arithmetic. |
| HC46 | A different but internally valid parent policy/descriptor yields INCOMPATIBLE_COORDINATE, never implicit conversion. |
| HC47 | Full explicit and compatibility bodies are checked, including inactive target groups, not one active row/hash label. |
| HC48 | Raw040B expected amount and PR #100 mapped operand may differ; the distinct prescribed checks succeed without equating scalars. |
| HC49 | Forged semantic label plus another row's valid raw amount rejects even if outer objects are rehashed. |
| HC50 | Correct semantic label with wrong frozen raw expected amount rejects. |
| HC51 | Raw or mapped rational sign never supplies DISLIKE/NEUTRAL/LIKE. |
| HC52 | Nonzero raw/mapped semantic NEUTRAL maps exactly to inherited0/1. |
| HC53 | Available inherited0/1 stays available after positive attenuation and differs from missingness. |
| HC54 | An intentionally omitted semantic state yields SOURCE_VALUE_NOT_MAPPED; no nearest/default row. |
| HC55 | DISLIKE→positive or LIKE→negative mapping is rejected through frozen policy replay. |
| HC56 | Missing/unknown/duplicate25-cell policy data and denied payloads fail frozen validation. |
| HC57 | Wrong destination kind or transfer-policy fingerprint in an inherited descriptor rejects before product arithmetic. |
| HC58 | Descriptor stripping, naked numeric input or PR #100 descriptor relabeling cannot produce an Available inherited result. |
| HC59 | Full frozen transfer-policy fingerprint is used without recursive self-hashing or reduced ad-hoc semantic hash. |
| HC60 | Same descriptor/rational gives scoped numeric equality only; distinct targets/relations grant no ranking/aggregation interface. |
| HC61 | Mapping precedes attenuation; exact product/reduction is verified, including near-bound authored fractions. |
| HC62 | Attenuation0/negative/>1, booleans, strings, floats and noncanonical fractions reject. |
| HC63 | Canonical Available product stays within signed unit bounds, with denominator positive and zero denominator1. |
| HC64 | Valid31-bit factors fit128-bit product; oversized serialized/forged result components reject without rounding/clipping. |
| HC65 | Changing parent shrinkage provenance alone does not redefine inherited coordinate identity. |
| HC66 | A published transfer-policy replacement changes the descriptor/fresh pin behavior, with no automatic old-result relabeling. |
| HC67 | Source versus destination versus inherited coordinates remain separate; no reverse conversion or final scalar chooser exists. |
| HC68 | Repeated source reviews/history/retries do not increase strength, attenuation or inherited magnitude. |
| HC69 | Outer result binds household/member/exact targets/relation/context even when scoped fractions match another result. |
| HC70 | Edited cached040B/PR #100 child fields/fingerprints reject on root deserialization after recomputation. |
| HC71 | Edited cached source eligibility/selected relation/diagnostics reject even with a recomputed outer checksum. |
| HC72 | Edited trace row/coefficient/mapped/product/descriptor fields reject against complete primitives. |
| HC73 | Omitted unfavorable hierarchy history/support/grant/counter facts fail frozen full-source replay. |
| HC74 | Exact immutable input round-trip is deterministic; no ambient clock/random value enters output. |
| HC75 | Full-input changes can change fingerprint while equal visible amount remains; visible-row hash is insufficient. |
| HC76 | Policy-after-capture replay preserves VERSIONED_CONSUMER_POLICY_REPLAY and no AS_OF_CAPTURE/liveness claim. |
| HC77 | Database engine, filesystem open and network calls can be made fail-fast while the pure interface still succeeds on valid primitives. |
| HC78 | No writes/capture helper/repository/cache/HTTP endpoint/schema migration/production rows are introduced. |
| HC79 | All baseline definitions/tests/frozen code/migrations remain compatible; new exports are additive only after authorization. |
| HC80 | No learned/contextual/passive event,041 repeat signal,TasteFit/utility/safety/Execution/PRECOMMIT capability enters or emerges from the interface. |
| HC81 | Conflicting repeated immutable feature-term/RecipeFact bodies across member/hierarchy cuts fail; mutable labels never become alias or transfer authority. |

Implementation evidence must map every HC case to concrete tests and retain SOURCE H01–H09 and
PR #100 acceptance suites. Current2807 is a baseline, not a promised final implementation count.
The future pure tests need no new PostgreSQL source primitive; all existing real-PG authority,
capture/migration/concurrency regression still runs. Interface tests must not replace those trust-root
tests with mocks or treat fixture hashes as proof of production DB origin.

## 14. Persistence, production content and compatibility

Expected implementation schema remains **0015 /85 domain tables**. No migration, result persistence,
cache invalidator, provider/grant publication, transfer corpus, policy default or production number
is needed or authorized. A newly discovered durable truth requirement is a separate architecture
gate; do not reserve another migration number. The existing349 definitions remain unchanged;
any later authorized consumer types use additive exports with retained definition digests.

No frozen040A/B,041A–F,046A, reference-prior source, PR #100, hierarchy source or migration0001–0015
is changed/genericized. Existing unavailable/not-performed fields stay exactly as they are; the new
consumer result is additive. Empty production source/corpus can legitimately yield no usable input
or inherited suggestion; framework completion is not evidence of production taste coverage.

## 15. Decisions, alternatives and risks

- **Selected:** optional complete parent with a conditional requirement. Always requiring a fake
  parent for absent/ambiguous source was rejected; accepting omitted parent as absence was also rejected.
- **Selected:** same complete member ledger for both endpoint children, separate original capture
  clocks. Arbitrary mixed member histories risk bypassing destination corrections; requiring one
  global transaction across unrelated sources would invent a new orchestration/authority contract.
- **Selected:** retain separate destination exact-target result and inherited component. Blending
  them, ranking them by equal-looking fractions or supplying a new effective score is outside this slice.
- **Selected:** frozen semantic-row lookup after raw/mapped lineage checks. A numeric-only conversion
  of PR #100 blended output would launder reference prior and violate the neutral-anchor correction.
- **Selected:** one pure module and one public interface. Source/capture changes, injected repositories
  and a generic graph abstraction add authority/complexity without serving the bounded computation.

Reviewers should focus on conditional-parent failure versus unavailable outcomes, member-ledger
comparison, raw-versus-mapped checks, independent destination policy lineage, descriptor inseparability
and precise suppression/source reason order. These are design decisions proposed here, not claims
that consumer contracts/tests already exist. No actual incompatibility requiring frozen SOURCE
modification has been identified.

## 16. Review and authorization stop

This PR changes documentation only. It introduces no executable contracts, tests, fixtures, exports,
migrations, seeds or runtime behavior. Required CI/docs/architecture checks apply to this design PR;
their exact head/merge receipts belong in its GitHub delivery record, not a self-referential SHA.
Standing documentation merge authorization does not grant architecture approval or runtime authority.

After detailed architecture approval, implementation still needs explicit separate authorization.
After eventual040C freeze, perform the separate Parent MTR-040 Completion Review before considering
issue #41 closure.039-backed broader learning remains separate. Full040/041/046 remain PARTIAL;
024/020B/021 BLOCKED; Execution NOT STARTED; PRECOMMIT FAIL-CLOSED. No additional041 or039 work is
a prerequisite for this bounded consumer, and none is started here.

**MTR-040C PURE HIERARCHY CONSUMER DESIGN REVIEW — IMPLEMENTATION NOT AUTHORIZED**
