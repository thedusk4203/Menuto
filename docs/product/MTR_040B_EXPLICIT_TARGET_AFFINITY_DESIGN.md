# MTR-040B — Explicit-source Target Affinity Profile Foundation

Status: **DESIGN APPROVED by user; additive implementation authorized from
`5cb39464fd1f07c55c82bb221dde3255c3773e64`; NOT FROZEN**.

[Implementation evidence](MTR_040B_EXPLICIT_TARGET_AFFINITY_EVIDENCE.md) records the subsequent
implementation and verification. The design-stage observations and proposed wording below
remain the historical approved specification; their earlier authorization limits were superseded
by the user's explicit implementation request. No next milestone is authorized.

Canonical reviewed `main`: **`b3d381966126822d7fd9544034c9bb3bf1bab92d`**, PR #88.
User authorized this design only. Schema **0013 /71 domain tables**,237 exported definitions.
Frozen040A,041A/B/C/D/E and046A remain unchanged. No runtime/contracts/tests/exports/migrations
are modified in this PR. No migration or profile table is proposed.

```text
captured frozen ExplicitMemberPreferenceSnapshot
 + finite canonical target manifest
 + explicit versioned interpretation policy
 → pure deterministic ExplicitTargetAffinityProfileDraft
```

This is a member-owned exact-target **explicit assertion interpretation**, not the complete
ADR-011 MemberBehaviorProfile, a learned model, candidate TasteFit or planner-ready utility.
The name/scope040B is the user's current design task; this document does not authorize its code.

## 1. Canonical basis and inspected implementation

References: [ADR-011](../adr/ADR-011-behavioral-learning-loop.md),
[ADR-004](../adr/ADR-004-household-first-model.md),
[ADR-009](../adr/ADR-009-execution-state-machine.md),
[ADR-010](../adr/ADR-010-independent-validator.md),
[spec§19.2–19.5](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[invariants](../ARCHITECTURE_INVARIANTS.md),
[post041E dependency review](POST_MTR_041E_DEPENDENCY_REVIEW.md),
[040A source design](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_REVIEW.md),
[0012 authorship evidence](MTR_040A_AUTHORSHIP_CORRECTION_EVIDENCE.md),
[041E frozen evidence](MTR_041E_FEATURE_EXPOSURE_EVIDENCE.md),
[blueprint](IMPLEMENTATION_BLUEPRINT_M0_M1.md) and [backlog](BACKLOG.md).

Direct source inspection confirms:

| Current source | Actual capability / constraint |
| --- | --- |
| `preferences/contracts.py` | Typed INGREDIENT/DIRECT_RECIPE/PROTEIN/METHOD/FLAVOR targets, raw LIKE/DISLIKE/NEUTRAL, full SET/RETRACT lineage, historical actor/authorship/role, complete member sequence/frontier and deterministic snapshot. No affinity, EvidenceStrength, priors or profile. |
| `PreferenceService.snapshot()` | Already requires clean read-only RR/SERIALIZABLE; canonical member/actor authorization and full history/terms capture in caller-owned session. It does not take write locks or commit. |
| Frozen `state_for()` | Correctly resolves UNDECLARED/DECLARED/RETRACTED from history. A typed target UUID supplied to it is **not proof that the target exists**. |
| Catalog `IngredientIdentityFact`, `catalog_facts()` | Existing typed ingredient identity; current facade also reads nutrients, which this slice does not need. A thin identity-only owner read is an additive implementation seam, not new source truth. |
| Catalog `affinity_feature_terms()` | Canonical exact term ID/kind/version/definition/provenance; target must be REVIEWED. No aliases by code or inferred classification. |
| Recipes `RecipeFact`, `authored_version()` | Existing stable recipe identity type. Existing version facade requires a version ID, not the stable Recipe ID used by040A. A stable-ID identity-only read facade is still needed for implementation. Do not select a guessed latest RecipeVersion. |
|046A classification /041E exposure | Available frozen sources, but **not inputs** to this exact-target preference interpretation. |
| ORM/schema / policy namespace | No behavior-profile/prior store or profile interpretation policy exists. No source data for production onboarding/catalog priors exists. |

Graph-index traversal was orientation only; current code/docs above determine the design.
No concrete frozen contradiction was found. New owner-read facades would be small additive
interfaces over existing rows, not migrations or an excuse to change040A/Recipes/Catalog truth.

## 2. Ownership and placement

HouseholdMember owns the derived profile, scoped by Household. Preferences owns explicit
preference/profile semantics. Actor is an author, not the profile owner. One request/result
belongs to **one household/member**. No household-level average, participant fan-out or shared
utility is introduced.

Proposed placement, only after implementation approval:

- Additive immutable models in `preferences/contracts.py`.
- Pure enforcement/derivation in `preferences/profile_derivation.py`; imports only immutable
  Preferences/Catalog/Recipes contracts and neutral canonical/numeric primitives.
- Canonical read orchestration in `preferences/profile_capture.py`, exposed by a lazy public
  facade. It may call existing PreferenceService and identity-only owner public reads.
- Public capture/derive facades may be exposed through `preferences/public.py`; that existing
  module imports SQLAlchemy for source services. Purity is enforced on the **new core and its
  call path**, not falsely asserted for the entire existing service module.

No second Learning preference store, observation ingest, generic event store or runtime
dependency on Learning/Planning/Execution/optimizer. MTR-039 attribution is not required to read
an already typed EXPLICIT_DECLARATION source, and is not implemented here.

## 3. Proposed additive contracts — common discipline

All proposed models are frozen, `extra="forbid"`, tuple-based and explicitly versioned at wire
boundaries. Closed discriminator unions are used instead of generic UUID/JSON payloads.
Names below are concrete design proposals, **not existing exports or tested runtime**.
Static scope/tag literals may have defaults; all policy mappings described as required have
**no constructor/data defaults**. Existing040A models and canonical encodings are not edited.

Reuse frozen `PreferenceTarget`, `AffinityValue`, `MemberPreferenceState`,
`MemberPreferenceDeclarationFact`, `ExplicitMemberPreferenceSnapshot`, `IngredientIdentityFact`,
`RecipeFact`, `AffinityFeatureTermFact`, AwareTime, Identifier, Sha256 and Provenance.
`TargetKind` is the closed five-kind projection of frozen PreferenceTarget. Derived
`EvidenceStrength` is NONE/LOW/MEDIUM/HIGH; it is never added to040A raw declarations.

### 3.1 Identity/capture contracts

| Proposed model/version | Exact fields and structural rules |
| --- | --- |
| `ExplicitTargetAffinityCaptureRequest` / `explicit-target-affinity-capture.v1` | household_id, member_id, requested_targets: tuple[PreferenceTarget,...]. Unique by typed target key; empty tuple allowed and means an explicitly empty requested set, never all targets. No embedded identity facts, policy, caller history, confidence or prior. Actor comes from authenticated application context. |
| `IngredientTargetManifestEntry` | kind=INGREDIENT, identity:IngredientIdentityFact. Target projection is (INGREDIENT, identity.id); no second caller-authored ingredient_id. |
| `RecipeTargetManifestEntry` | kind=DIRECT_RECIPE, identity:RecipeFact. Projection is (DIRECT_RECIPE, identity.id), **stable recipe identity**. No RecipeVersion selector or latest-version inference. |
| `FeatureTargetManifestEntry` | kind:PROTEIN/METHOD/FLAVOR, identity:AffinityFeatureTermFact. Require kind==identity.kind, status REVIEWED, exact ID/version/provenance. Projection is (kind, identity.id). |
| `CanonicalPreferenceTargetManifest` / `preference-target-manifest.v1` | household_id, member_id, coverage=REQUESTED_CANONICAL_TARGETS_ONLY, entries:tuple[the three entry types,...] discriminated by kind. Unique typed keys; projections exactly equal request.requested_targets. No missing/extra entries or cross-member manifest. |
| `ExplicitTargetAffinitySourceSnapshotDraft` / `explicit-target-affinity-source.v1-draft` | activation_ready=False; request; preferences:full frozen ExplicitMemberPreferenceSnapshot; manifest; capture_completed_at:AwareTime. Owners agree, raw capture≤completion, exact manifest, all requested feature provenance observed≤completion; repeated term IDs in raw source/manifest must have identical immutable content. Source history remains full and untrimmed. |

The three entry variants are nested under the versioned manifest; no free polymorphic context_ref
or authority flag. IngredientIdentityFact/RecipeFact do not have authored provenance/version
fields. Do **not** invent source_version=1 or fake USER provenance for those identity reads.
Their evidence is the canonical owner read in this captured transaction, with outer capture time;
they prove identity only, not culinary review, nutrition, feature assignment or current liveness.

### 3.2 Numeric and policy contracts

| Proposed model/version | Exact fields and constraints |
| --- | --- |
| `ExplicitAffinityAmount` / `explicit-affinity-amount.v1` | numerator:strict int, denominator:strict int>0; -denominator≤numerator≤denominator; reduce by gcd,0/x→0/1; unit=POLICY_EXPLICIT_AFFINITY_UNITS. No float/bool/string coercion or probability/money/quantity semantics. |
| `ExplicitAffinityValueRule` | value:LIKE/DISLIKE/NEUTRAL, amount:ExplicitAffinityAmount. A policy row, not observed preference/prior evidence. |
| `ExplicitAuthorshipStrengthRule` | authorship:SELF/AUTHORIZED_REPRESENTATIVE, level:LOW/MEDIUM/HIGH. No implicit order/equality between the two authorship rows. NONE is not an active-source level. |
| `ExplicitTargetKindPolicy` | target_kind; affinity_rules:exactly3 unique value rows, covering LIKE/DISLIKE/NEUTRAL; strength_rules:exactly2 unique authorship rows; undeclared_strength:required literal NONE; retracted_strength:required literal NONE. No role/count/recency/source-vote weights. |
| `ExplicitTargetAffinityPolicy` / `explicit-target-affinity-policy.v1` | policy_id, policy_version, provenance:Provenance restricted to USER/REVIEWED_REFERENCE; interpretation_mode=EXPLICIT_POLICY_VERSION_REPLAY; evidence_basis=LATEST_ACTIVE_EXPLICIT_DECLARATION_ONLY; target_policies:exactly5 unique complete kind rows; prior_mode=UNAVAILABLE_ONLY; shrinkage_mode=UNAVAILABLE_ONLY. No defaults for target_policies or nested mappings. |
| `ExplicitTargetAffinityInput` / `explicit-target-affinity-input.v1` | source:ExplicitTargetAffinitySourceSnapshotDraft; policy:ExplicitTargetAffinityPolicy. No other behavioral/source input union. Full recursive reparse is required. |

The bounded signed rational range is a **type/coordinate convention**, not a calibrated score
or production constant. A larger coordinate means a more positive explicit valence under that
policy. For each kind require exact strict ordering DISLIKE<NEUTRAL<LIKE by cross-product.
Do not impose a hidden NEUTRAL=0, LIKE=1, DISLIKE=-1 or symmetry rule. Each numeric coordinate
must be explicitly supplied. A supplied zero for a real NEUTRAL assertion is valid; an absent
assertion can never obtain that numeric value by default.

No comparison or aggregation across different profile policies/scales is defined. This is not
candidate desirability, a probability or a RecipeScore. Production policy values/curation are
not supplied or seeded by this document. Synthetic mapping values belong only to future tests.

### 3.3 Derived contracts

| Proposed model/version | Exact fields and cross-field meaning |
| --- | --- |
| `AvailableExplicitAffinity` | status=AVAILABLE, amount:ExplicitAffinityAmount, policy_rule_key:(target_kind,value), declaration_id. Only a current SET may produce this branch. |
| `UnavailableExplicitAffinity` | status=UNAVAILABLE, reason:UNDECLARED/RETRACTED. No numeric amount field, nullable numeric fallback or baseline. |
| `DerivedExplicitEvidenceStrength` / `explicit-evidence-strength.v1` | scope=CURRENT_EXPLICIT_TARGET_ONLY; level:NONE/LOW/MEDIUM/HIGH; basis:NO_ACTIVE_DECLARATION/SINGLE_CURRENT_EXPLICIT_DECLARATION; active_declaration_id:UUID or None; rule_key:(target_kind,authorship) or None. NONE iff no active SET; then IDs/rule=None. Active branch has exact head ID and policy-selected non-NONE level. |
| `UnavailablePreferencePrior` / `preference-prior-availability.v1` | status=UNAVAILABLE, reason=NO_CANONICAL_PREFERENCE_PRIOR_SOURCE. No value, provider observations, pseudo count, population statistic or policy baseline. |
| `UnavailableShrunkAffinity` / `shrunk-affinity-availability.v1` | status=UNAVAILABLE, reason=PRIOR_UNAVAILABLE. No amount, blend weight or identity transform passing raw affinity off as shrunk. |
| `DerivedTargetAffinity` / `derived-explicit-target-affinity.v1` | target:PreferenceTarget; raw_state:MemberPreferenceState; current_declaration:MemberPreferenceDeclarationFact or None; affinity:available/unavailable discriminator union; evidence_strength:DerivedExplicitEvidenceStrength; prior:UnavailablePreferencePrior; shrunk_affinity:UnavailableShrunkAffinity. Everything matches the exact requested target and recomputed current head. |
| `ExplicitTargetAffinityProfileDraft` / `explicit-target-affinity-profile.v1-draft` | subject:ExplicitTargetAffinityInput; rows:tuple[DerivedTargetAffinity,...], exactly one per manifest target; source_fingerprint, manifest_fingerprint, policy_fingerprint, fingerprint:Sha256. Plus fixed scope/availability literals below. All rows/hashes are recomputed, never trusted cache. |

Profile fixed literals:

```text
coverage              = EXPLICIT_SOURCE_TARGETS_ONLY
absence_semantics     = NO_TARGET_ROWS_IS_NOT_GLOBAL_PREFERENCE_NEUTRALITY
learned_evidence      = UNAVAILABLE
contextual_evidence   = UNAVAILABLE
passive_evidence      = UNAVAILABLE
cross_target_inference= NOT_PERFORMED
candidate_aggregation = NOT_PERFORMED
planner_ready         = False
activation_ready      = False
```

No cached is_valid/is_safe/activation token exists. The result is not named MemberBehaviorProfile
without qualification; this exact proposed class name and scope make its incompleteness explicit.

## 4. Canonical capture and identity proof

Choose **requested canonical targets**, including undeclared targets, rather than restricting
v1 to previously declared targets. This adds identity reads over existing sources, not a new
durable truth. It makes UNDECLARED useful without accepting arbitrary UUIDs as existing objects.

Proposed `capture_explicit_target_affinity_sources(session, request, actor_user_id=...)`:

1. Require the caller's one clean read-only REPEATABLE READ/SERIALIZABLE transaction; reject
   READ COMMITTED, dirty/writable sessions. No internal commit/new connection or write locks.
2. Reparse the closed request. Call frozen PreferenceService.snapshot for its household/member,
   with authenticated actor; retain the complete returned source and its original bytes/clocks.
3. Partition requested target IDs by typed kind. Read canonical identities through owner facades
   in the **same session**: Catalog ingredient identities, Recipes stable recipe identities,
   Catalog reviewed vocabulary terms. Add identity-only public read facades during future
   implementation where current facade signatures are insufficient; do not cross owner internals.
4. Require exact returned identity coverage. Missing/deleted/unknown row or wrong kind/review
   fails the **whole capture** with TARGET_IDENTITY_UNRESOLVED/TARGET_NOT_REVIEWED as appropriate.
   No fabricated unresolved-target row, zero or empty success substitutes for a requested target.
5. Assemble the typed manifest; validate owner, duplicate/cross-kind/reference consistency.
   Read final clock as capture_completed_at after reads; preserve the child source captured_at.
6. Return the immutable source. No profile table, learning write or inventory/plan mutation.

An existing never-declared ingredient has a canonical manifest entry and raw state UNDECLARED.
A nonexistent random ingredient UUID has **no manifest proof** and capture fails. Same for a
random recipe/term ID. A known DRAFT term also fails; a new REVIEWED version uses its own ID.
A stable recipe target requires identity, not a reviewed culinary version; it does not claim
that the recipe is executable, nutritionally resolved or classified.

The member's full raw history may contain targets outside the requested manifest. Keep those
history facts in040A's original snapshot for complete replay/frontier proof; derive rows only
for the exact requested set. Do not require extra manifest entries for unrelated history targets
or trim the frozen source to make it fit a smaller declaration count.

**Trust boundary:** authoritative capture proves database existence by owner reads. A typed UUID,
caller-supplied identity model, content hash or offline self-consistent payload alone cannot
authenticate database origin. Public capture accepts IDs only, not caller manifests/rows. Pure
replay verifies internal primitive consistency over a captured subject; it cannot re-prove origin
without IO and must not claim to do so. Production use must obtain source through the canonical
adapter; imported synthetic/offline drafts are not authority. No signature/receipt/PRECOMMIT
subsystem is invented to hide this boundary.

Catalog association and Recipes classification generations are **not dependencies** of an
exact-target preference profile. Immutable term identity/provenance is retained, but no046A
assignment or041E exposure is read. A PROTEIN target is that term, not inferred MAIN_PROTEIN
assignment to a dish. Ingredient/recipe identity descriptors remain captured as read; no fake
authored version/provenance is added to compensate for fields their source contracts lack.

## 5. Pure derivation and correction/retraction algebra

Proposed `derive_explicit_target_affinity_profile(subject)` is a zero-IO Preferences operation.
Recursively serialize/reparse the full input, including every frozen040A child, owner identity
and policy row, to reject constructed/copied invalid objects. Recompute the source/manifest/
policy identities and the exact result; no field supplied as cached affinity/strength/prior is
accepted as independent evidence.

For each typed target key in the manifest:

1. Recompute raw state through frozen040A replay/state_for. Find the current target head by
   canonical member_sequence after validating complete stream predecessor/revision history.
   Do not use UUID order, largest occurred_at or caller latest flags.
2. If UNDECLARED, current_declaration=None. Produce unavailable affinity(reason UNDECLARED)
   and strength NONE under the policy's explicit undeclared_strength rule.
3. If RETRACTED, retain the exact RETRACT head as current_declaration. Produce unavailable
   affinity(reason RETRACTED), strength NONE under retracted_strength, and no active declaration
   strength basis. The old SETs and retraction remain in the attached full source.
4. If DECLARED, current_declaration is the exact SET head. Select the policy row by **target kind**;
   affinity is the explicit value rule for that head's LIKE/DISLIKE/NEUTRAL. Strength is selected
   independently by that same row's authorship rule, not by the value or affinity magnitude.
5. Attach unavailable prior and unavailable shrunk affinity in every row. Do not perform a
   multiplication/blend or rename raw affinity as shrunk. Build the exact manifest-ordered result.

| Source transition | Current interpretation | Preserved audit / excluded influence |
| --- | --- | --- |
| No target stream | UNDECLARED; affinity unavailable; strength NONE | No fabricated neutral value or historical observation count. |
| First SET LIKE/DISLIKE/NEUTRAL | DECLARED; supplied policy maps the exact value; separate supplied authorship strength | One current explicit declaration, not a learned observation collection. |
| SET→INPUT_CORRECTION SET | New head/value wins | Superseded incorrect assertion stays audit; never an independent positive/negative vote. |
| SET→PREFERENCE_CHANGED SET | New head/value wins | Prior preference remains history, not a second current assertion. |
| SET→RETRACT | RETRACTED; affinity unavailable; strength NONE | Full prior assertion/retraction identity retained; no soft/hard penalty manufactured. |
| RETRACT→new SET | New DECLARED head under normal040A lineage | No revival/summing of old values or evidence-count bonus. |
| Same idempotent request retried100 times | Same declaration/head/frontier | No strength or affinity inflation. Fresh capture audit time may still change source hash. |
|100 genuinely appended replacements | Latest head only under the same policy rule | More history does not mechanically increase strength. Policy rule cannot inspect revision count in v1. |

No weight is derived from history length, member_sequence, revision, age, source retry count,
actor role, repeated statement, sign/magnitude of affinity,041E occurrence count or meal outcome.
These fields remain available for source audit, not hidden policy features.

This algebra deliberately keeps five observable raw cases: UNDECLARED, DECLARED LIKE, DECLARED
DISLIKE, DECLARED NEUTRAL, RETRACTED. NONE is scoped **lack of an active explicit assertion**,
not proof the member has no historical preference, never ate the target, or has no future
learned/contextual evidence. A numeric zero from an explicit policy-mapped declaration remains
AVAILABLE and distinct from either unavailable affinity branch.

## 6. EvidenceStrength meaning and provenance

EvidenceStrength is a separate **ordinal policy interpretation** of the current explicit source:

- NONE: no active explicit assertion for this exact canonical target in the complete captured
  member source. Both absence and retraction produce this level, but remain different raw states.
- LOW/MEDIUM/HIGH: policy-selected influence class for one current explicit assertion. These
  levels are not number of observations, empirical reliability estimates, calibrated confidence,
  probabilities, weights or numeric multipliers.

The explicit two-row authorship mapping may assign equal levels or different levels. Neither
SELF>representative nor the reverse is a code invariant. LIKE/DISLIKE/NEUTRAL share the same
source-strength rule for a given kind/authorship; raw valence never chooses the strength class.
There is no HIGH default and no caller EvidenceStrength field in the declaration or capture request.
The user/curator supplies a complete **policy**, not mutable strength on raw source facts.

Every derived row preserves/references the full current MemberPreferenceDeclarationFact:
subject household/member, actor_user_id, SELF/representative mode, role-at-write, source=explicit,
declaration/stream/revision, member_sequence, action/reason, occurred_at, recorded_at, provenance
and command fingerprint. Attached raw history preserves all superseded facts. The source retains
member frontier and original capture identity. Policy retains ID/version/provenance and exact rules.

Current membership controls a **new capture's access**, not historical authorship labels. Pure
derivation performs no membership query and cannot relabel an old SELF as representative when
an account/member link changes. The bidirectional0012 write guard remains authoritative at append
time; it is neither relaxed nor duplicated as a guessed historical membership rule in this slice.

## 7. Priors, shrinkage and policy-time semantics

There is no production onboarding/catalog preference-prior source. Vocabulary, classification,
numeric midpoint, no declarations and explicit NEUTRAL are **not** prior evidence.
V1 therefore supports only the two closed UNAVAILABLE contracts in §3.3. Supplying prior amount,
prior samples, population average, baseline, alpha, shrinkage coefficient or an AVAILABLE branch
is an extra/unsupported input and fails. No0/0.5/neutral fallback is silently inserted.

An explicit policy coordinate for NEUTRAL is a **policy interpretation of that actual assertion**,
not a baseline or observed prior. This design does not even add a separate policy baseline;
it is unnecessary while shrinkage is unavailable. Future prior support requires a separately
reviewed source owner, target applicability, identity/provenance and compatible scale. It cannot
arrive as an unversioned extra numeric field on this v1 contract.

Interpretation mode is explicitly **EXPLICIT_POLICY_VERSION_REPLAY**, not AS_OF_SOURCE_CAPTURE.
This operation asks: "How does this supplied policy version interpret this captured source?"
It does not claim that policy existed when the source was captured. A later policy may interpret
an older immutable source; its observed_at stays in policy provenance and changes derived identity.
No rule copied from frozen041B/C/D forbids that. Those source/policy time semantics remain frozen.

There is no ambient now, default policy lookup or wall-clock IO during derivation. The source's
raw/canonical capture cutoff and owner-read completion rules remain enforced independently.
This is replay/comparison semantics, not a current-policy/liveness or PRECOMMIT claim. Actual
selection/authorization of production policy versions is external and is not implemented here.

Policy ID/version reuse with a changed definition is invalid version governance. The pure operation
has no registry to detect unseen prior definitions; its full content fingerprint prevents changed
bodies from silently sharing result identity. A consuming application must pin the expected policy
definition/fingerprint, rather than trusting an ID/version label alone. No policy store or HTTP
policy-authoring/permission workflow is added by this design.

## 8. Exact arithmetic

Use strict signed integer rationals in the new affinity type, with positive denominator and
canonical gcd reduction. Equivalent encodings1/2 and2/4 yield the same policy numeric value and
bytes;0/x canonicalizes to0/1. Reject denominator0/negative, bool, floats, NaN/Infinity and
values outside the explicit affinity coordinate range. Exact comparisons use cross-products.

V1 performs **lookup**, canonical rational normalization and exact ordering checks only. It does
not multiply by EvidenceStrength, average targets or members, calculate posterior/shrunk values
or add an objective coefficient. No Decimal-context rounding or quantization is needed; no value
is persisted. This type is not Quantity, CalculatedQuantity, Money or RetentionMultiplier.
There is no AP/EP/cooked/count conversion. Engineering resource limits on payload size must not
be disguised as calibrated affinity/strength parameters.

## 9. Deterministic identity and validation of cached results

Define a versioned typed target key from `(kind, canonical UUID)` only. PROTEIN/METHOD/FLAVOR
use exact term row ID, not code, label or version alone. DIRECT_RECIPE uses stable Recipe ID;
its declared scope across versions is inherited from040A. No feature/generalization is implied.

Canonicalization of **new** contracts: UTF-8, sorted object keys, compact separators, canonical
UUIDs, explicit UTC microsecond timestamps and strict integer rational fields. Explicitly
unordered target/manifest/result rows sort by typed key; target policy rows sort by kind,
affinity rules by value and strength rules by authorship. Validate exact sets/duplicates first.
Raw history retains **member_sequence** order and exact frozen040A canonical_json encoding.
Source occurrence/recorded times are not silently normalized away or used as tie-breakers.
The nested040A snapshot's literal `profile_derivation=NOT_IMPLEMENTED` also remains unchanged:
that source contract supplies raw declarations, not this new derived result. Only the additive040B
outer contract carries interpretation; do not "upgrade" the frozen source flag or its schema/hash.

Identity definitions:

```text
manifest_fingerprint = H(versioned canonical manifest)
policy_fingerprint   = H(versioned complete canonical policy)
source_fingerprint   = H(versioned source envelope, using frozen040A canonical source)
result fingerprint   = H(full canonical result payload EXCLUDING only its fingerprint field)
```

The result payload includes the full subject, exact rows and recomputed source/manifest/policy
fingerprints. No self-referential hash. Child raw source fingerprint remains its frozen value;
do not redefine it to omit captured_at. Any source primitive, requested manifest, actor/mode,
frontier, policy version/provenance/rule or availability change is therefore traceable in result
identity. Fresh capture can change audit hash with no affinity/strength change. Replaying identical
captured input/policy, or permuting only explicitly unordered sets, gives identical bytes/result.

Constructors/result validators must recursively reparse source/manifest/policy and independently
recompute every row, availability and hash from primitives. `model_construct`/`model_copy` instances
and cached fingerprint/affinity/strength/prior/row fields are never trusted. Forged cached fields
reject; the pure API constructs only the recomputed canonical result. Semantic consistency checks
are not origin authentication; the source trust boundary in §4 still applies.

## 10. Concurrency, frontiers and future authorization boundary

The existing member frontier is the authoritative **whole-member preference source frontier**.
A concurrent declaration/replacement/retraction cannot mix with owner identity reads in a single
RR/SERIALIZABLE capture. The old cut stays replayable; a fresh capture sees the new frontier.
On serialization failure retry the whole capture, not only one target or identity fragment.
No source fact or profile history is rewritten. There is no profile persistence to mutate.

A declaration about another target may change member frontier and exact profile audit identity
even when requested-target interpretations stay equal. Do not invent a per-target frontier to
claim stronger invalidation granularity. Target metadata comes from the same owner-read cut;
immutable vocabulary IDs/content are cross-checked against the full raw source.

An old derived profile/hash is **not** evidence the source is still current. Future production
commit flow must capture/validate, then recheck authoritative member/identity/policy and other
applicable safety/material frontiers inside its authorization transaction. This design adds no
such authority, receipt issuer or current-policy store; PRECOMMIT remains fail-closed.

## 11. Adversarial design cases and future test plan

All cases below are **proposed implementation acceptance tests**, not tests added in this
documentation PR. U=pure unit/contract, PG=real PostgreSQL adapter/integrity/concurrency,
C=compatibility/import/export checks. Mocks cannot prove database behavior.

| # | Required case | Expected result / future layer |
| --- | --- | --- |
|1 |100 idempotent retries | Same head/frontier under040A; no affinity/strength increase; canonical replay of same input identical. U/PG |
|2 |LIKE→INPUT_CORRECTION DISLIKE | Latest DISLIKE mapped alone; old LIKE audit retained, never counted as independent evidence. U/PG |
|3 |LIKE→PREFERENCE_CHANGED NEUTRAL | AVAILABLE explicit policy-mapped NEUTRAL, separate strength rule; not missing input. U |
|4 |LIKE→RETRACT | RETRACTED, affinity unavailable, strength NONE, retraction/current head and full history preserved. U/PG |
|5 |Never-declared existing target | Canonical identity captured, UNDECLARED, unavailable affinity, NONE; no fake neutral/prior. U/PG |
|6 |Same feature code, new ID/version | Exact independent target; no transfer/summing/alias by code. U/PG |
|7 |Direct recipe LIKE | No FLAVOR/METHOD/PROTEIN row or derived feature preference outside manifest/source. U |
|8 |Ingredient LIKE | No inferred PROTEIN preference from046A association or string/name. U |
|9 |MemberA edit | MemberB source/profile cannot change through fan-out; foreign household/member input rejected. U/PG |
|10 |SELF/proxy modes | Provenance retained. Equal/different strength only as explicitly supplied; no automatic ordering. U/PG |
|11 |Later membership link/role change | Old facts/replay retain historical actor/mode/role; fresh capture access uses current permissions. U/PG |
|12 |041E has0/100 proposed events | Cannot be an input; explicit-only result unchanged from same valid subject. U/C |
|13 |Cooked/skipped/out-of-stock | No event input/mutation or profile effect; source union remains explicit040A only. U/C |
|14 |Missing prior | Closed UNAVAILABLE prior/shrunk affinity; numeric/AVAILABLE/baseline injection rejected. U |
|15 |Concurrent declaration | Old RR member/identity cut coherent, fresh capture new frontier; no writes/locks in capture. PG |
|16 |Policy version/provenance change | New result identity; old raw source and040A hash/history unchanged; later policy replay permitted explicitly. U |
|17 |Forged cached affinity/strength/prior/result/digest | Recursive reparse/recomputation rejects tampering, including constructed/copied models. U |
|18 |Derivation IO/write attempt | Engine/network traps and static core boundaries; capture SQL SELECT/SHOW only; source/profile/physical row counts unchanged. U/PG/C |
|19 |Random nonexistent target UUID | Authoritative owner lookup fails whole capture, never UNDECLARED valid-target output. Offline fabricated models are not origin proof. PG |
|20 |Migration/profile persistence | No new tables/migration; frozen0001–0013 and metadata/head unchanged. C/PG |
|21 |Missing/duplicate/incomplete kind/value/authorship policy row | Reject; no default map, fallthrough, HIGH or implicit neutral. U |
|22 |Equivalent rational/nonfinite/float input | Reduced equivalents identical; invalid int/range/denominator/float/bool rejected. U |
|23 |Shuffled manifest/policy/term sets | Canonical output identical; member-sequence lineage and source chronology remain fixed. U |
|24 |DRAFT/wrong-kind term or foreign/missing/extra manifest proof | Capture/contract fails exact manifest/identity/review coverage. U/PG |
|25 |Policy-mapped explicit zero vs unavailable | AVAILABLE zero keeps actual declaration/non-NONE strength; never coalesce with UNDECLARED/RETRACTED. U |
|26 |Requested set empty or omits historically declared target | Exactly requested rows, explicit scope; complete040A history retained, no global-neutral/all-catalog claim. U/PG |
|27 |Affinity sign/magnitude changes with same source authorship rule | Strength stays policy-selected; no implicit LIKE/DISLIKE→HIGH. U |
|28 |Source/head/manifest/policy cross-owner conflicts | Fail exact member/target/head matching, term equality and source cutoff validation. U/PG |

Future PG tests must create real canonical target rows and source writes, exercise missing-target
lookups/read-only requirements and concurrent declarations, and retain existing append-only,
idempotency/authorship/direct-SQL guards. No new persistence means no new trigger to test; existing
DB facts and migration/drift regressions still run. Future compatibility tests must pin old040A,
041A–E/046A classes/functions, contract definitions and migration contents; do not replace old tests.

## 12. Persistence, invariants and explicit deferred work

**No migration, no0014, no profile table/cache/source frontier table.** Durable source truth is
already040A plus existing target identity rows. Policy is an explicit immutable versioned input,
not a new prior observation. A future durable policy/prior distribution repository would need
its own justification/review; it is not installed by this slice.

INV-026 member ownership,027 separability,028 explicit policy preservation and022–025/029
non-inference/attribution boundaries directly apply. INV-012/013 keep proposal/elapsed/assumed
events out of confirmed or learned truth. INV-015–021 preserve primitive validation, hard safety
precedence and gating/diagnostic separation. No full invariant is claimed implemented by this
design;030 cross-horizon source semantics remain unavailable.

Do not design-expand or implement TasteFit, candidate/shared-member aggregation, feature
cooldown/decay/RepeatPenalty, novelty, Stage-2 utility/rank/portfolio/optimizer, learned/contextual/
passive observations,039 attribution, Execution, PRECOMMIT authority, cross-target generalization
or profile persistence. Hard restrictions remain Nutrition/root-validation truth; a profile
DISLIKE is soft and a LIKE cannot override a restriction.

Full040 remains incomplete after a future040B implementation: no complete ADR-011 hierarchical
shrunk profile, production priors or broader observations/fit consumers are delivered. Full041/046
remain incomplete;024/020B/021 **BLOCKED**. Execution NOT STARTED; PRECOMMIT fail-closed.

## 13. Decisions requiring review versus deferred configuration

This document proposes concrete contract/ownership/capture/numeric/state/time/identity choices
for review. No structural blocker was found. Specifically approve or revise: canonical requested
target proof capture (including undeclared targets), complete five-kind policy matrices, bounded
exact policy coordinates with ordered valence, current-head-only strength classes, fixed unavailable
prior/shrinkage and explicit later-policy replay semantics. None is implemented yet.

Production coordinate/strength choices, curator approval/distribution of policy versions, real
onboarding/catalog prior sources and future hierarchy/shrinkage semantics remain **unsupplied or
deferred**, not fabricated architecture constants. They must not be inferred from this design's
type bounds or test examples. The planned identity-only facades are absent today; approval would
allow additive owner reads during implementation, not a redesign of frozen domains.

## 14. Verification evidence for this design PR

Existing regression/CI gates are run to verify documentation integrity and unchanged baseline,
not proposed profile semantics. Reviewed baseline b3d381966126822d7fd9544034c9bb3bf1bab92d has
exact [post-merge CI40208671947](https://github.com/thedusk4203/Menuto/actions/runs/40208671947)
SUCCESS, independently rechecked in this task.

Local gates on2026-10-25:

| Gate | Actual result |
| --- | --- |
| Full Python with real PostgreSQL18 | **1860 passed**,0 failures/errors/skips;244.89s; one existing Starlette/httpx deprecation warning |
| PostgreSQL-real | All755 existing marked tests included/passed within full run; no database tests replaced by mocks |
| Prior regressions | **1860/1860 identities retained**,0 new tests, XML compared to frozen041E run |
| Migration/drift/direct SQL/concurrency | Existing real-PG suite PASS; no migration/runtime changes |
| Ruff / architecture / imports | PASS;30 invariants,11 ADRs,50 linked tasks,16 registered contexts |
| OpenAPI / domain exports | PASS; all237 existing domain definitions byte-identical |
| Synthetic fixtures / benchmark |22 fixtures verified; **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client contracts / typecheck / tests | PASS; **10/10** |
| Web typecheck/build | PASS |
| Diff scope/whitespace |7 Markdown files only; no runtime/contracts/tests/migrations/exports modified; `git diff --check` PASS |
| PR/exact post-merge CI | Exact base/head/merge and run links recorded in final delivery after remote gates; no advance PASS claim |

Full command: `.venv/Scripts/python -m pytest --basetemp=.local/040b-design
--junitxml=.local/040b-design.xml` with MENUTO_TEST_POSTGRES_URL set to loopback PostgreSQL18
and random isolated test databases. Other gates match `.github/workflows/ci.yml`; ignored
`.local/040b-design*` logs/XML are local verification artifacts, not source or production data.
No proposed040B contract/runtime/adversarial behavior is claimed tested before implementation exists.

**READY FOR MTR-040B ARCHITECTURE/DESIGN REVIEW**
