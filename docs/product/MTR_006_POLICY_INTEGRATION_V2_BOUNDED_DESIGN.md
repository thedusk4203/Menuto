# MTR-006 Policy Integration v2 — bounded detailed design

**Source-Bound, Independently Verified NutritionPolicy Integration — STRUCTURAL / TEST_ONLY**

**MTR-006 V2 BOUNDED DETAILED DESIGN — READY FOR INDEPENDENT ARCHITECTURE REVIEW / IMPLEMENTATION NOT AUTHORIZED**

This document proposes additive contracts and future executable obligations. No contract,
runtime, test, database object, privilege, scientific content or production path is implemented
by this PR. Full MTR-006/007/008 remain INCOMPLETE; issues #5/#6/#7 remain OPEN.

## 1. Authorization, exact baseline and primary evidence

The maintainer's separate design authorization follows the accepted
[Post-MBA dependency review](POST_MBA_POLICY_INTEGRATION_V2_DEPENDENCY_REVIEW.md),
[PR #135](https://github.com/thedusk4203/Menuto/pull/135),
[independent architecture PASS 6692295427](https://github.com/thedusk4203/Menuto/pull/135#issuecomment-6692295427)
and [merge completion 6693282259](https://github.com/thedusk4203/Menuto/pull/135#issuecomment-6693282259).
The completion receipt's DESIGN START PENDING was accurate then; the later explicit design
authorization supersedes only that disposition. It does not authorize implementation/merge/freeze.

Before authoring, main was re-fetched as exactly **`73a4c1c668516f6c719661c7225d84a758221450`**.
Exact main **push** [CI 42271106826 — SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/42271106826)
retains **4,183 tests /0 skips**, SCRAM/TLS16/16, benchmark22/22 and client10/10. Python/web
and all guards passed. No material baseline drift was found. Live parent issues were re-read.

Frozen MBA implementation remains **`9d3b580ce2a2d111223b37814612a4072dbfe6a2`**,
tree **`3a68035f9c33de152b3899a083d534a537c647e1`**;
[formal freeze 6688245300](https://github.com/thedusk4203/Menuto/pull/133#issuecomment-6688245300)
and its [canonical receipt](MEASUREMENT_BASIS_APPLICABILITY_INDEPENDENT_EVIDENCE_CONTAINMENT_FREEZE_RECEIPT.md)
govern. A documentation commit is not a replacement implementation identity.

Primary semantics: [Spec V1.3 §10.3–10.4](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[ADR-002](../adr/ADR-002-nutrition-policy-engine.md),
[ADR-003](../adr/ADR-003-plan-policy-resolution.md),
[ADR-010](../adr/ADR-010-independent-validator.md),
[INV-001–030](../ARCHITECTURE_INVARIANTS.md), especially001/003/004/005/006/015–020.
Inspected frozen designs/evidence: [Root](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_DESIGN.md),
[NPS v1](MTR_006_SOURCE_BOUND_NUTRITION_POLICY_SYNTHESIS_CONTAINMENT_DESIGN.md),
[NRE](MTR_007_SOURCE_BOUND_NUTRITION_RESOLUTION_ESTIMATOR_DESIGN.md),
[MBA](MEASUREMENT_BASIS_APPLICABILITY_INDEPENDENT_EVIDENCE_CONTAINMENT_DESIGN.md).
The existing graph query is only a source locator; its truncated older graph is not proof.

Concrete owning source anchors:

| Source | Frozen fact this design must preserve |
|---|---|
| [synthesis.py](../../apps/backend/app/modules/nutrition/synthesis.py), `_requirements`, `_evaluate`, `_coverage`, `_period_consistency`, `_resolution` | COMFORT-only resolution projection; finite exact reviewed rule operations; distinct hard/goal/comfort/weekly semantics; v1 accepts only its TEST_ONLY interface fixture |
| [synthesis_contracts.py](../../apps/backend/app/modules/nutrition/synthesis_contracts.py), `NutritionPrecisionSelection`, `NutritionSynthesisSourceSnapshot` | REQUEST_EXPLICIT/version/actor/subject/evidence plus authenticated membership witness; no full MTR-008 precedence |
| [resolution_contracts.py](../../apps/backend/app/modules/nutrition/resolution_contracts.py), `NrePeriodVectors`, `NutritionResolutionHandoffV2` | Joint vectors with every configuration tuple; original measurement basis; unverified terminal transport |
| [NRE capture](../../apps/backend/app/modules/planning/nutrition_resolution_capture.py) | One clean actual ordinary reader, isolated TEST_ONLY database, complete owner reads and one read-only repeatable cut |
| [basis_projection.py](../../apps/backend/app/modules/nutrition/basis_projection.py), [basis_capture.py](../../apps/backend/app/modules/planning/basis_capture.py) | Separate complete all-layer anchor manifest; original meaning preimages; privately issued registry context pinned before/after capture, not shared MVCC |
| [NRE checker](../../apps/backend/app/modules/validation/nutrition_resolution.py), [MBA checker](../../apps/backend/app/modules/validation/basis_applicability.py) | Independently reconstructed children; CONSISTENT negative is possible; fingerprints do not prove origin |
| [v1 policy checker](../../apps/backend/app/modules/validation/nutrition_policy.py), reference functions | Fresh consumer revalidation; no caller-supplied CONSISTENT report can supply validation authority (R-127-01) |

## 2. Bounded ownership, interfaces and dependency DAG

| Owner | Proposed responsibility | Explicit exclusion |
|---|---|---|
| Planning | Trusted source capture, process-local one-shot capture association, resource hosting and consumer orchestration | No rule evaluation/containment oracle; no production enrollment; no Policy defaults |
| Nutrition | Pure additive v2 rule evaluation, complete claim/coverage construction and finite witness predicates | No Validation imports, I/O, current authorization lookup, scientific conversion or v1 fixture cast |
| Validation | Fresh independent child reconstruction and whole-policy reconstruction, including the consumer check | No producer evaluator/projection as correctness oracle; no source publication |
| Policy | Owns the meaning/authorship of explicit precision; future MTR-008 consumes a checked policy | No guideline, member-goal or measurement-science authorship |
| Root/rule owners; Catalog/Recipes/Households | Existing canonical facts and existing reader permissions | No new source rights or persistent authority |

```text
Root + reviewed synthesis rules + Policy-owned explicit precision
    -> frozen pre-policy RequirementSpec (COMFORT resolution only)
    + complete declared Catalog/Recipe/Household/serving source universe
    -> frozen one-reader NRE capture and retained primitive evidence
    + original-source meaning + pinned TEST_ONLY MBA fixture registry
    -> separate full root/MAKE_CONSTRAINT anchor manifest
    -> additive Nutrition v2 producer (no Validation dependency)
    -> Validation consumer: fresh NRE + MBA + full v2 policy reconstruction
    -> Planning atomic one-shot use at the captured cut
    -> unverified serialized handoff for retained replay
    -> separately gated future MTR-008 consumer
```

All requirements/applicability come from root/rule/precision sources before the final policy.
No final NutritionPolicy or ResolvedPlanPolicy is an input to its own requirements. Arrows
describe evidence/orchestration, not an import from Nutrition to Validation. The final v2
policy interface terminates this chain; no new generic coordinate/compatibility layer is added.

Proposed future files, not files added now: Nutrition `policy_v2_contracts.py`, `policy_v2.py`,
`policy_v2_public.py`; Planning `policy_v2_capture.py`; Validation `nutrition_policy_v2.py`.
The future implementation must add exact companion import guards without loosening existing
allowlists or editing frozen producers/checkers. Cross-context reads use existing owner interfaces.

## 3. Normative notation and integration profile

The following IDL is a **design specification**, not executable Python/JSON Schema. Every record
is immutable, extra-forbid, strictly revalidated even from model instances. All fields of new records are
required; imported frozen types retain their original schemas/defaults; `?` means explicit null is permitted, never an omitted/default value. Arrays are ordered
tuples; ID sets are sorted and unique. No float/Decimal coercion, duplicate JSON keys or bool→int.
Times are explicit aware instants and intervals remain half-open `[start,end)`.
Every **new** record below has a required common `environment:"TEST_ONLY"` field, including
the auxiliary coverage/assignment/delta/support/body records where it is elided for readability.
Imported frozen carriers gain no fields: their taint/provenance is bound by the complete new
parent body, source identity and coverage. A detached imported claim has no admission authority.

Imported frozen types retain their exact definition bodies. `Sha` is a canonical SHA-256 hex
identity; `Id` is the existing Identifier; `UUID` and `Time` are strict existing primitives.
`Rat` is a reduced exact signed rational, denominator>0, numerator/denominator each at most
256 bits; zero is0/1. Nutrient amounts are nonnegative. Root/policy endpoint arithmetic also
retains the frozen NPS signed127-bit rational and NRC nonnegative127-bit output limits.
Intermediate products are bounded before use (see §11); no rounding or implicit unit conversion.

The one supported profile is **`PIV2_SAME_MEANING_EXACT_PERIOD_SUM_V1`**:

- TEST_ONLY only; one exact tracked member; one DAY or one WEEK horizon; exact authored calendar.
- Frozen WHOLE_TIER_TO_SINGLE_TRACKED_MEMBER_V1 is planned offered-food attribution only.
- Every original/derived anchor has original-source `PLANNED_INGREDIENT_INPUT_V1`, interpretation
  `NRE_EXACT_PLANNED_INPUT/v1`, with independently reconstructed MBA applicability.
- Every required period, including the entire horizon, already exists in retained NRE output.
  The horizon period covers **all** declared slots. Missing periods are not manufactured.
- DAY→WEEK `FINITE_PERIOD_SUM` maps used for required temporal-protection consistency have
  **explicitly authored coefficients all equal to canonical1/1**. Non-unit maps are
  `UNSUPPORTED/UNSUPPORTED_TEMPORAL_MAP` in this new consumer; they remain valid/unchanged where
  frozen v1 supports them. This is a consumer subset, not a clinical default or source rewrite.
- `REVIEWED_PERIOD_PROJECTION` may use exact source-authored coefficients to derive **bound
  endpoints** in the reviewed finite language. These never scale NRE food vectors. For example,
  the frozen TEST_ONLY weekly fixture's authored daily-endpoint projection is distinct from
  its unweighted period-sum map. No projection creates missing measurement meaning.

These restrictions make raw NRE period sum meaning unambiguous without a conversion engine.
EXACT_INTERVAL, overlapping unrelated calendars, multi-week frames, missing horizon periods,
cross-version stitching and non-unit required period maps fail closed; no fallback profile.

## 4. Proposed exact versioned contracts

### 4.1 Source/input and identity

```text
PolicyIntegrationIdentityV2 {
  subject: HouseholdMemberIdentity; actor_user_id: UUID;
  root_request: NutritionRootRequest;
  root_source_fingerprint: Sha; root_result_fingerprint: Sha;
  rule_selection: NutritionSynthesisSelection; rule_case_id: Id;
  requirement_fingerprint: Sha; nre_scope_fingerprint: Sha;
  precision: NutritionPrecisionSelection;
  precision_witness: NutritionSubjectWitness;
  horizon: NutritionTemporalScope; calendar_cells: tuple<NutritionTemporalScope>[1..64];
  nre_source_fingerprint: Sha; nre_result_fingerprint: Sha;
  anchor_manifest_fingerprint: Sha; original_meaning_manifest_fingerprint: Sha;
  registry_id: Id; registry_revision: int>0; issuer_epoch: Id; deployment: Id;
  database_oid: positive existing NrcOid; database_name: Id;
  basis_source_fingerprint: Sha;
  environment: "TEST_ONLY";
}

NutritionPolicyIntegrationInputV2 {
  contract_version: "nutrition-policy-integration-input.v2";
  profile: "PIV2_SAME_MEANING_EXACT_PERIOD_SUM_V1";
  basis_sources: BasisApplicabilitySourcesV1;
  identity: PolicyIntegrationIdentityV2;
  source_fingerprint: Sha;
  environment: "TEST_ONLY";
}
```

`basis_sources` retains the complete NRE sources/claimed estimate, root/rule histories,
precision witness, owner facts/seals/absences, original meaning preimages, complete MBA
artifact, selectors, anchors and capture frame **once**. No detached summary replaces them. Frozen NRE/MBA `policy_integration=NOT_AUTHORIZED`,
`UNVERIFIED_TRANSPORT` and all other closed literals remain unchanged. A separately authorized
v2 companion defines only its own structural use; it neither flips nor treats child literals
as permission. Current authorization is design only, so no such use is executed by this PR.
The producer/checker independently reconstruct every duplicated identity field from this
one retained tree; any disagreement rejects before policy arithmetic. A pin never supplies
authority missing from its preimage. Actor/member/household must agree across all nested scopes.

The anchor manifest hashes the full sorted frozen MBA anchor tuple, including all source
roots and every MAKE_CONSTRAINT branch, even unselected precision branches. The original
meaning manifest hashes sorted `(anchor_key, original_source_fingerprint,
evidence_fingerprint, exact meaning_preimage)` entries; missing/duplicate/conflicting entries
cannot be normalized away. RequirementSpec is compared unchanged and **does not** stand in
for this wider manifest or precision identity; it contains COMFORT measurements only.

Source identity includes every retained frame/frontier/history, not just visible selected rows.
The precision pin is canonical equality of the complete existing selection and DB-observed
witness, not merely its enum or version. Its source stays REQUEST_EXPLICIT. Reader human/user,
OWNER/EDITOR membership, exact subject and environment are independently reconstructed using
the frozen rules. No goal-authoring or guideline authority follows from that membership.

### 4.2 Policy body, coverage and finite support

```text
PolicyClaimCoverageV2 {
  anchor_key: Id; anchor_fingerprint: Sha; root_key: Id;
  operation_id: Id?; descriptor: NutritionRootDescriptor;
  layer: existing root interpretation | SynthesisLayer;
  disposition: "RETAINED_ROOT" | "ACTIVE_CLAIM" | "UNSELECTED_PRECISION_BRANCH";
  claim_id: Id?; meaning_fingerprint: Sha; basis_witness_fingerprint: Sha;
}
PolicyAssignmentEvaluationV2 {
  assignment_fingerprint: Sha;
  configuration_ids: tuple<Sha>[1..14];  // aligned to sorted horizon slot_ids
  period_vector_fingerprints: tuple<Sha>[1..32];
  hard_violations: sorted tuple<Id>[0..256];
  comfort_violations: sorted tuple<Id>[0..256];
}
PolicyCenterDeltaV2 {
  assignment_fingerprint: Sha; claim_id: Id;
  descriptor: NutritionRootDescriptor; amount_minus_center: Rat;
}
JointPolicySupportV2 {
  slot_ids: sorted tuple<Id>[1..14];
  assignments: sorted tuple<PolicyAssignmentEvaluationV2>[1..16384];
  protected_assignment_ids: sorted tuple<Sha>[1..16384];
  comfort_assignment_ids: sorted tuple<Sha>[1..16384];
  representative_comfort_assignment_id: Sha;
  center_deltas: sorted tuple<PolicyCenterDeltaV2>[0..65536];
  support_fingerprint: Sha;
}
NutritionPolicyBodyV2 {
  retained_roots: exact tuple<NutritionResolvedRoot>[1..16];
  claims: tuple<NutritionPolicyClaim>[1..256];
  trace: tuple<NutritionPolicyTrace>[1..256];
  coverage: sorted tuple<PolicyClaimCoverageV2>[1..128];
  requirements: unchanged NutritionPolicyRequirementSpec;
  reconstructed_basis_result: BasisApplicabilityResultV1;
  support: JointPolicySupportV2;
}
```

Imported claims/traces are immutable carriers only. V2 arithmetic and coverage are separately
specified/reconstructed; reusing the carrier is not calling the frozen v1 producer/checker
for correctness. `retained_roots` copies **all** resolved roots verbatim: GUIDELINE_HARD roots
remain conjuncts, REFERENCE_CENTER roots remain references. Their distinct interpretation
must not disappear behind the field name. Mandatory required claims are taken from the
published rule case, never an optional caller-supplied subset.

Trace includes all authored operations. Requiredness means their constraint values must be
constructed and valid; it does not turn unselected comfort branches into simultaneous active
comfort constraints. Coverage includes those branches for meaning, nesting and containment.
Every active claim, original root and unselected branch links to the exact matching MBA anchor
and witness, without cross-root/kind/period substitution.

### 4.3 Result, diagnostics and terminal handoff

```text
PolicyV2Outcome = AVAILABLE_TEST_ONLY | SOURCE_UNAVAILABLE | UNSUPPORTED |
                 REJECTED | POLICY_CONFLICT | RESOLUTION_INSUFFICIENT | RESOURCE_EXCEEDED
PolicyV2Stage = PARSE | IDENTITY | SOURCE | NRE | MBA | RULE | COVERAGE | JOINT | CONSUMER
PolicyDiagnosticV2 {
  stage: PolicyV2Stage; code: PolicyV2Reason;
  subject_path: Id?;
  child_outcome: BasisOutcome?; child_reason: Id?; // finite frozen MBA code or explicit null
  hard_support: "NOT_EVALUATED" | "ABSENT_IN_DECLARED_UNIVERSE" | "PRESENT";
  soft_support: "NOT_EVALUATED" | "SOFT_UNSUPPORTED" | "PRESENT";
}
NutritionPolicyResultV2 {
  contract_version: "nutrition-policy.v2";
  input_fingerprint: Sha; identity_fingerprint: Sha;
  outcome: PolicyV2Outcome; diagnostics: tuple<PolicyDiagnosticV2>[0..64];
  payload: NutritionPolicyBodyV2?;
  result_fingerprint: Sha;
  environment: "TEST_ONLY";
  validation_authority: "UNVERIFIED_TRANSPORT";
  scientific_correctness: "NOT_CERTIFIED";
  source_origin: "NOT_PROVED_OFFLINE"; current_authorization: "NOT_CLAIMED";
  production_admission: "CLOSED"; plan_validation: "NOT_PERFORMED";
  solver_infeasibility: "NOT_PROVEN";
  planner_ready: false; activation_ready: false;
}
NutritionPolicyCheckV2 {
  contract_version: "nutrition-policy-check.v2";
  coverage: "FULL_V2_SOURCE_JOINT_POLICY_CONTAINMENT";
  decision: "CONSISTENT" | "INCONSISTENT";
  reconstructed_outcome: PolicyV2Outcome?;
  numerical_use: "AVAILABLE_RETAINED_ONLY" | "NOT_ADMITTED";
  environment: "TEST_ONLY";
  findings: sorted tuple<PolicyV2Reason>[0..64];
  input_fingerprint: Sha?; reconstructed_result_fingerprint: Sha?;
  validation_authority: "UNVERIFIED_TRANSPORT";
  source_origin: "NOT_PROVED_OFFLINE"; current_authorization: "NOT_CLAIMED";
  scientific_correctness: "NOT_CERTIFIED"; production_admission: "CLOSED";
  planner_ready: false; activation_ready: false;
}
NutritionPolicyHandoffV2 {
  contract_version: "nutrition-policy-handoff.v2";
  input: NutritionPolicyIntegrationInputV2; result: NutritionPolicyResultV2;
  retained_check: NutritionPolicyCheckV2?;
  validation_authority: "UNVERIFIED_TRANSPORT";
  production_admission: "CLOSED";
  planner_ready: false; activation_ready: false;
}
```

`payload != null` iff outcome is AVAILABLE_TEST_ONLY. Non-success exposes no usable derived
claims, arithmetic trace, counts or positive numeric witnesses. Input primitives remain retained
for audit/replay, not implicitly admitted. Source-invalid or unverified evidence always has
both support fields NOT_EVALUATED. A fully source-verified resolution failure may distinguish
PRESENT hard support from SOFT_UNSUPPORTED, but still releases no numeric policy payload.
Invalid/unparseable input cannot supply a trustworthy fingerprint; consumer/capture failure
uses explicit null, not a magic all-zero fingerprint.

Check CONSISTENT is possible for a faithfully reconstructed non-success. Only a reconstructed
AVAILABLE_TEST_ONLY result may say AVAILABLE_RETAINED_ONLY, still not origin or current-use
authority. An attached check is optional retained audit data; if present, compare every field
with fresh checking, and reject stale/forged disagreement. It is never an input oracle. The consumer
handoff function calls the full v2 checker exactly once; capture/wrapping performs no earlier
v2 check and reattaching that fresh report performs no second check within the same invocation.
A later consumer invocation must check afresh and obtain its own capture association.

```text
PolicyV2Use {
  purpose: "STRUCTURAL_TEST_ONLY_INSPECTION";
  subject: HouseholdMemberIdentity; actor_user_id: UUID;
  selector_fingerprint: Sha; precision_fingerprint: Sha;
  environment: "TEST_ONLY";
}
PolicyV2CaptureFailure {
  contract_version: "nutrition-policy-capture-failure.v2";
  outcome: "CAPTURE_REJECTED" | "ADMISSION_REJECTED" | "RESOURCE_EXCEEDED";
  diagnostics: tuple<PolicyDiagnosticV2>[1..64];
  input_fingerprint: Sha?;
  environment: "TEST_ONLY"; production_admission: "CLOSED";
  planner_ready: false; activation_ready: false;
}
```

No failure carrier has numeric payload, trusted boolean or transferable admission token.
Fresh capture binds the selector hash to frozen BasisSelectorsV1, not a caller-invented complete
scope fingerprint. PolicyV2Use must equal the server's independently bound expected subject,
actor, selector and precision identity; accepting its shape does not authorize it.

All new fingerprints use existing canonical primitive encoding with a new domain-separated
preimage `{domain:"nutrition-policy-integration.<kind>.v2",body:<complete record minus its
own fingerprint>}`. Kinds are `input`, `identity`, `anchors`, `meanings`, `assignment`, `vector`,
`support`, `result`, `selectors`, `precision`, `check`. Do not change frozen child hash domains.
Sets use deterministic key order; assignments sort by configuration-ID tuple and periods by
canonical temporal identity. Caller-computed hashes are checked, never trusted as authority.

## 5. Trusted capture/admission versus offline replay

The proposed interfaces are small; type names above are carriers, not new authority layers:

```text
Nutrition.derive_policy_v2(retained_input) -> NutritionPolicyResultV2              // pure
Validation.check_policy_v2(input, claimed_result) -> NutritionPolicyCheckV2       // pure
Validation.check_policy_handoff_v2(handoff, expected_use) -> NutritionPolicyCheckV2 // fresh, pure
Planning.capture_test_policy_v2(session, issued_basis_context, selectors) -> private lease | CaptureFailure
Planning.consume_test_policy_v2(private_lease, expected_use) -> HandoffV2 | CaptureFailure
```

### 5.1 Process-local capture lease

Planning privately constructs a nonserializable, noncopyable, identity-keyed one-shot lease;
it is **not exported in JSON Schema** and not constructible from bytes/UUID/hash. A private
registry stores the exact immutable input/candidate, ordinary Session and connection object,
actual transaction object, endpoint/database identity, reader/actor/subject, selector/precision
pins, captured source frames, and exact issued MBA registry registration object. A lease proves
only association with this invocation's trusted capture, not semantic correctness/science.

Capture calls the unchanged frozen MBA capture, which invokes the unchanged NRE adapter and
protected Root/rule readers on one caller-owned read-only REPEATABLE READ/SERIALIZABLE cut.
No preliminary ORM read may dirty the Session. No routed binds, cached ORM identities,
writable schema, unsafe login or multiple owner sessions are accepted. Selectors may be
caller-authored; completeness and authorization cannot be. Source capture failure returns
CaptureFailure; it must not manufacture a successful input with absence rows removed.

The new Planning companion may inspect the **existing private registry's object identity
under its existing lock**, read-only, to pin the original registration before capture and
through consumption. This is an exact internal dependency on frozen MBA, not a new public
registry mutation/enrollment interface. No frozen file edit or broader database grant is needed.
Its use must be covered by companion-specific imports/tests, and cannot be generalized into
a public capability factory. Trusted Python host/bootstrap remains outside hostile-input
protection; arbitrary in-process code execution is not defended by a Python private object.

Run pure derivation in bounded hosting, retain the candidate privately, then issue the lease.
State transitions are CAPTURING→READY→CONSUMING→CONSUMED or terminal ABORTED. Only Planning
may transition them. No final v2 validation report is supplied by a caller or accepted at capture.
The trusted host exclusively owns the Session during this bounded invocation; callers cannot
run concurrent transaction/SET ROLE operations or inject callbacks. Before consumption compare
actual session_user/current_user, database/role identity, read-only/isolation and snapshot with
the captured values using existing permitted metadata reads. No new protected SQL function
or privilege is introduced. The lease expires at the90s operation deadline and on context exit;
copy/deepcopy/pickle are forbidden and every terminal path removes the private association.

### 5.2 Atomic numerical consumption

Consumption performs these steps in order:

1. Under the private lease mutex reject a forged, copied, unknown, expired, already consumed or concurrently consuming lease.
   Verify the expected use against server-bound identity; verify the **same still-active
   transaction object and connection**, read-only/isolation/snapshot pins and original Session.
   Closing then opening a new transaction on the same Session is not a match.
2. Using the fixed lock order **lease mutex→existing registry lock**, check the issued context still exists and its exact
   registration object/revision/epoch/database/actor/reader equals the captured registration;
   atomically change READY→CONSUMING. Do not hold a lock during expensive verification.
3. Invoke the Validation-owned fresh handoff/consumer check. It reconstructs NRE, MBA and the
   whole v2 policy. A supplied stored report, result label or matching hash is never a shortcut.
4. Recheck transaction/connection lifetime and registry registration **after** verification.
   Under the registry lock, atomically burn the lease and finalize the one-shot use. A changed
   registry/context during checking discards the result. One of simultaneous consumes may
   succeed at most once. Exceptions, negative checking, cancellation and timeout burn it too.
5. Admit numbers only inside this trusted invocation when every source/identity/cut check
   passed, fresh check is CONSISTENT with AVAILABLE_TEST_ONLY and all required coverage/joint
   support is present. Return an explicitly UNVERIFIED_TRANSPORT handoff for audit, not the
   lease or a serialized admission fact. Consistent non-success returns diagnostics only.

This is **admission at the captured cut**, not instantaneous revocation linearizability.
Database changes committed after that repeatable snapshot do not retroactively alter retained
history. Every new consumption requires a new capture/lease; revocation committed before the
new snapshot must block fresh admission. No present authorization outside the captured
invocation is claimed. Registry changes are separately detectable by object pinning; it and
PostgreSQL do **not** share MVCC. Caller owns transaction completion; the module never commits
or silently rolls back a caller transaction to obtain a different favorable cut.

Offline derive/check interfaces accept retained bytes for deterministic consistency, with no
DB/network/filesystem/wall-clock/global lookup. A perfectly self-consistent fabricated ledger
may be arithmetically consistent offline: that does not prove DB origin. It cannot construct
a Planning lease and cannot pass numerical admission. An old valid handoff also cannot replace
a fresh capture. Future MTR-008 must use a separately reviewed consumer composition, not treat
this structural test purpose as production/ResolvedPlanPolicy permission.

## 6. Exact rule, root, precision and temporal semantics

Both producer and checker reconstruct the single exact published rule case matching the current
member goal; reject ambiguity, absence, missing SOURCE_READ authority, withdrawal or expired
applicability. Retain publication/effective interval and complete immutable-prefix history.
No latest/provider/default fallback or cross-publication stitching. The producer uses frozen
Nutrition source replay/requirement functions but a **new v2 evaluator**; it does not call v1
policy synthesis with fake fixtures. The checker has its own evaluator, coverage and interval
logic and never calls either Nutrition evaluator or the v1 checker as its oracle.

The eight FINITE_EXACT_V1 operators retain their authored semantics:

| Operator | V2 interpretation |
|---|---|
| COPY_REFERENCE | Exact existing clause endpoint, descriptor, root key and retained reference identity; no absent endpoint→zero |
| AFFINE_SAME_UNIT | Exact source-authored coefficient/offset on a bound value, unchanged measurement descriptor |
| MAKE_CONSTRAINT | All operands same exact descriptor/root; nonnegative final endpoints; ordered RANGE; one-sided MINIMUM/MAXIMUM; TARGET only soft WEEKLY_CENTER |
| CHECK_SUBSET | Exact same descriptor/root; explicit lower/upper containment; no invented opposite bound |
| FINITE_PERIOD_SUM | Exact authored calendar partition, same root/measurement and explicit coefficients; required DAY→WEEK maps restricted to authored unit sums by §3 |
| REVIEWED_PERIOD_PROJECTION | Source-authored endpoint transformation to an exact reviewed cell/horizon with original meaning for its resulting claim; not food/physiological conversion |
| CHECK_DIRECTION | Exact member ENERGY goal and source-authored comparator/reference; UPPER_LT/UPPER_LE/LOWER_GT/LOWER_GE/CONTAINS as published, no heuristic CUT/GAIN formula |
| SELECT_PRECISION_CASE | Three authored COMFORT RANGE operands with identical descriptors; PRECISION⊆STANDARD⊆RELAXED, select exact REQUEST_EXPLICIT value; all branches remain checked |

No new numerical coefficient/offset/clinical rule is supplied.
For CHECK_DIRECTION, with existing goal bounds `l/u` and authored reference `r`, comparators
are respectively `u<r`, `u<=r`, `l>r`, `l>=r`, or `(l absent or l<=r) and (u absent or r<=u)`.
An upper/lower comparator requires that bound to exist; it cannot create one. For each emitted
goal claim a successful published direction check is mandatory. A new v2 evaluator cannot
substitute a generic CUT/GAIN comparator table for the selected reviewed instruction.

For matching descriptors, subset requires each present outer lower/upper to be preserved by
an inner bound at least/as strict. TARGET is a center point for reference containment only,
never a hard equality imposed on NRE. Goal/daily/weekly protected claims conjoin with every
applicable GUIDELINE_HARD clause. Cost/budget/effort/convenience/TasteFit are not operands.

Coverage obligations:

- Root AVAILABLE, eligibility SUPPORTED, exact member goal PRESENT; observations, assessment,
  legacy anchor, publication and delegation must be independently valid for the retained cut.
- Every mandatory root and published required claim is preserved; root IDs cannot be dropped
  because a caller did not ask for them. All MAKE branches have source-meaning/containment checks.
- Every `daily_root_key` has DAILY_PROTECTION for every authored DAY cell; no weekly-only
  reference supplies a daily permission without explicit reviewed endpoint/claim authority.
- DAY requires the published weekly profile NOT_APPLICABLE. WEEK requires explicit protected
  WEEKLY_GOAL and soft WEEKLY_CENTER, complete DAY partition and retained horizon vectors.
- Daily hard/goal constraints remain conjuncts; weekly protected envelope is an additional
  conjunct, not a replacement. Weekly centering and selected COMFORT are soft. Keep aggregate
  roots even when daily intervals are wider; never require all soft daily combinations to pass.
- Same-descriptor hard/protected intervals must intersect. For supported unweighted period
  maps, sum applicable daily protected lower/upper endpoints only when every corresponding
  bound exists, and intersect this **necessary interval** with aggregate hard/goal intervals.
  Empty interval is POLICY_CONFLICT, not solver infeasibility. Missing bounds remain missing.
- Exact finite assignment comparison (§7) supplies actual nutrient correlation; interval
  overlap alone never proves a common configuration or complete planner feasibility.

Precision identity must agree through root/rule request, NRE scope, retained witness, MBA scope
and v2 identity/result. Version/evidence or actor changes are not interchangeable even at the
same enum. No missing selection→STANDARD, absent/retracted goal→MAINTAIN, or old-goal resurrection.
Future defaults/week/override precedence remains Policy/MTR-008 work, not implemented here.

## 7. Joint finite-resolution predicates and witnesses

Let `S` be all declared slot IDs in canonical order. Require exactly one retained horizon period
with `slot_ids=S`. Its complete joint vectors and **every** configuration tuple define `A`:
all distinct assignments `a:S→configuration_id`. Each configuration must be a permitted
alternative for that exact slot, recipe/tier/rule/serving/member; IDs from another source scope
are not interchangeable. Multiple configurations producing equal vectors are all retained.

For each required period `p`, restrict an assignment to that period's exact retained slot IDs.
Its tuple must occur in that period's retained witness set, with the exact component-wise sum
of its configurations equal to that retained vector. Require this for every original/derived
anchor period, not just COMFORT requirement periods. Missing period/support is non-success;
do not construct a new period by Cartesian joining days or invent a weekly estimator.

For claim/root `c`, obtain `x(a,c)` from that exact period vector component, after MBA same-meaning
and descriptor checks. The root/rule scope/unit/protocol/member and calendar must match before
comparison. Evaluate closed predicates:

```text
RANGE(l,u): l <= x <= u     MINIMUM(l): l <= x     MAXIMUM(u): x <= u
TARGET(t): reference/soft delta x-t only; never a protected equality
hard(a) = all GUIDELINE_HARD + active GOAL_PROTECTION/DAILY_PROTECTION/WEEKLY_GOAL predicates
soft(a) = all active selected COMFORT predicates   // not unselected precision branches
H = {a in A : hard(a)}
C = {a in H : soft(a)}
```

Compute all per-assignment hard/comfort violations and exact WEEKLY_CENTER deltas without
combining metrics into a score. Canonical representative is lexicographically least
configuration tuple in C, solely a reproducible evidence witness, **not a chosen plan or ranking**.

- `H=∅`: RESOLUTION_INSUFFICIENT / NO_PROTECTED_JOINT_WITNESS, hard_support=ABSENT_IN_DECLARED_UNIVERSE.
  Consistent hard intervals may lack catalog support; this is not POLICY_CONFLICT.
- `H≠∅, C=∅`: RESOLUTION_INSUFFICIENT / NO_JOINT_COMFORT_SUPPORT, hard_support=PRESENT and
  soft_support=SOFT_UNSUPPORTED. No usable numeric payload; no hard-relaxation fallback.
- `C≠∅`: AVAILABLE_TEST_ONLY with full bounded A evaluations, H/C IDs and representative.
  Assignments in H\C have soft comfort violations, not hard failures. CENTER deltas remain soft.
- An independently established contradictory protected interval is POLICY_CONFLICT before
  these sets are used. Invalid sources short-circuit all support evaluation and witnesses.

Thus resolution support, constraint compliance of one finite assignment and solver feasibility
are distinct. Empty H/C proves only the stated finite declared-universe fact. No economics,
inventory, equipment, participant safety or full planner search is represented; no global
INFEASIBLE claim or validated plan preview follows.

Projected maximum/minimum gaps, marginal extrema and GCD-like values are diagnostics only.
A singleton has NO_ADJACENT_STEP/maximum_gap=null, not zero resolution; its actual vector may
still support a band. Inclusive band equality is allowed. A band may contain a real witness
despite a larger unrelated maximum gap. Individually attainable nutrient/day values cannot
be combined unless **the same assignment** supports them across all periods.

## 8. Independent Validation and report-forgery resistance

The new Validation module independently executes, in order:

1. Bounded strict parse and canonical identities; reconstruct entire retained input and pins.
2. Independently validate retained Root and synthesis authority, eligibility/observation/goal,
   publication selection and precision witness before child numeric comparison. Use independent
   Validation-owned root/rule reconstruction, never the producer source validator. Classify
   source failures before NRE; no authenticated source claim is supplied by a report label.
3. Fresh independent NRE check on primitive sources/claimed estimate. Require CONSISTENT and
   AVAILABLE_RETAINED_ONLY **and** the estimate's AVAILABLE state before numeric use.
4. Fresh independent MBA check on sources and the producer-claimed basis result retained
   inside an AVAILABLE payload (or independently reconstruct the expected child for a negative
   result). Require APPLICABLE_TEST_ONLY for a positive parent, not merely CONSISTENT.
   Positive path calls the frozen public MBA checker once. On a negative/null-payload parent,
   a new Validation-owned companion invokes the frozen **Validation-owned** `_reconstruct`
   and its typed failure semantics once to recover the expected child outcome/reason; it does
   not call the public checker again. Never call the Nutrition basis resolver to manufacture
   that expected result. Exact private-child imports are pinned to the frozen MBA identity;
   no frozen file edit or general cross-context exception.
5. Reconstruct complete original anchor/meaning coverage using independent Validation-owned logic. Reuse immutable contracts
   and already independent child checks, not producer projection/evaluation predicates.
6. Reimplement FINITE_EXACT_V1 evaluation, selected precision, mandatory claim coverage,
   containment and supported temporal interval reasoning. No call/import of `synthesis.py`,
   `policy_v2.py`, `basis_projection.py` or producer semantic validators as an oracle.
7. Independently reconstruct A by slot-keyed witness maps, then period membership/projection,
   every exact comparison, H/C, violation sets, deltas and representative. Producer may scan
   horizon tuples; checker uses a separate keyed assignment/projection fold. Do not trust
   supplied counts, vector hashes, representative IDs or source-order claims.
8. Rebuild the entire expected result, diagnostics/closed flags and fingerprints; compare
   canonical equality to the supplied result. Any favorable omitted branch or rehashed
   arithmetic/identity tamper is INCONSISTENT/POLICY_SEMANTICS_INCONSISTENT.

The report-only MBA interface cannot be used as an expected-negative-outcome oracle. Reusing
the independently owned child reconstruction is permitted; reusing Nutrition business logic
is not. The new companion must reconstruct the same child outcome/hash as the frozen checker
and is tested against its positive/negative cases, including publication-time authority. Each
branch makes one MBA reconstruction, so both retain the four-NRE-run host cap in §11.
Calling children alone cannot certify the parent rule/joint/containment semantics.
The producer uses exactly one frozen MBA replay, which itself freshly reconstructs NRE; it
does not add a redundant standalone NRE run. Neither branch uses the frozen MBA host helper,
which would introduce an extra producer/checker pair. A source-invalid/REJECTED child cannot
receive a consistent positive parent report: even when the parent's non-success is faithfully
represented, the checker returns INCONSISTENT/NOT_ADMITTED for corrupted source history.
Faithful non-success on otherwise valid unavailable/unsupported evidence may be CONSISTENT.

Publication-time checks preserve MBA-R133-01: the original reviewer's exact grant and symbolic
TEST_ONLY qualification must be valid at each publication recorded_at and for the full
assertion interval, reconstructed from the prefix known then. Later backdated renewal cannot
repair an unauthorized publication. Publisher separation/authority and capture-time reader
scope remain required. Retained historical replay does not claim present authorization.

Handoff checking always reruns the full checker; wrong coverage or stale attached report
cannot mint authority. Even a faithfully matching newly fabricated CONSISTENT report remains
UNVERIFIED_TRANSPORT and cannot obtain a capture lease. Perfect retained semantic consistency
is not origin proof. These requirements preserve, rather than reopen, R-127-01.

## 9. Typed failures and deterministic processing

`PolicyV2Reason` is the finite vocabulary in this table and the named reasons in §7/§12;
no arbitrary exception text, scientific inference or permissive unknown-code fallback is output.
Diagnostic paths identify structural locations without leaking another member's source history.

Frozen MBA mapping is on **(outcome, reason)**, in this precedence order. Preserve both
original fields in `child_outcome/child_reason`; other-stage diagnostics set both null.

1. RESOURCE_EXCEEDED maps to parent RESOURCE_EXCEEDED/RESOURCE_LIMIT.
2. REJECTED maps to parent REJECTED/MBA_INCONSISTENT (NRE_RESULT_FORGED maps instead to
   NRE_INCONSISTENT; ENVIRONMENT_MISMATCH retains that exact reason). It is never demoted to
   benign unavailability or incompatibility. CAPABILITY_INVALID/QUALIFICATION_INVALID and
   malformed enrollment/review/lineage remain source-integrity rejection.
3. UNAVAILABLE with PUBLICATION_WITHDRAWN/PUBLICATION_RETIRED maps to SOURCE_UNAVAILABLE/
   SOURCE_WITHDRAWN; PUBLICATION_MISSING/MEANING_MISSING to MBA_UNAVAILABLE;
   REQUIRED_ANCHOR_MISSING to ANCHOR_COVERAGE_MISSING; TEMPORAL_COVERAGE_MISSING to
   PERIOD_COVERAGE_MISSING; NRE_UNAVAILABLE to NRE_UNAVAILABLE. Other legitimate missing
   authority/qualification maps to SOURCE_UNAVAILABLE/SOURCE_UNAUTHORIZED.
4. NOT_APPLICABLE with MATERIAL_BASIS_MISMATCH/POPULATION_SCOPE_MISMATCH maps to UNSUPPORTED/
   UNIT_OR_SCOPE_MISMATCH; other legitimate NOT_APPLICABLE maps to MBA_NOT_APPLICABLE.
5. UNSUPPORTED with CONVERSION_NOT_SUPPORTED/MEANING_VERSION maps to UNSUPPORTED/MEANING_MISMATCH;
   CROSS_VERSION_INTERVAL/UNSUPPORTED_LINEAGE maps to UNSUPPORTED/UNSUPPORTED_TEMPORAL_MAP;
   other unsupported descriptor/period semantics maps to UNSUPPORTED/UNIT_OR_SCOPE_MISMATCH.
6. APPLICABLE_TEST_ONLY proceeds only after exact positive reconstruction. Unknown outcome/code
   or impossible pair maps to REJECTED/MBA_INCONSISTENT, never favorable fallback.

In particular MATERIAL_BASIS_MISMATCH+REJECTED is a forged material-reference identity, while
MATERIAL_BASIS_MISMATCH+NOT_APPLICABLE is legitimate incompatible material meaning. Code-only
mapping would erase that distinction. Producer and checker implement this same normative
mapping independently; neither shares the other's business predicate.

| Earliest failed stage / reason | Outcome / payload |
|---|---|
| Missing required retained evidence: SOURCE_MISSING, GOAL_SOURCE_UNAVAILABLE, PRECISION_UNAUTHORIZED | SOURCE_UNAVAILABLE; null |
| Malformed/duplicate/extra fields, bad rational/hash, SOURCE_MALFORMED, SOURCE_IDENTITY_MISMATCH | REJECTED; null |
| SOURCE_UNAUTHORIZED, SOURCE_WITHDRAWN, expired source/reader | SOURCE_UNAVAILABLE; null; support NOT_EVALUATED |
| NRE_INCONSISTENT, MBA_INCONSISTENT or forged favorable child | REJECTED; null |
| NRE_UNAVAILABLE, MBA_UNAVAILABLE, PERIOD_COVERAGE_MISSING, ANCHOR_COVERAGE_MISSING, CLAIM_COVERAGE_MISSING, DAILY_PROTECTION_MISSING | SOURCE_UNAVAILABLE; null |
| MBA_NOT_APPLICABLE, MEANING_MISMATCH, UNIT_OR_SCOPE_MISMATCH, UNSUPPORTED_TEMPORAL_MAP | UNSUPPORTED; null; no conversion |
| PRECISION_IDENTITY_MISMATCH, SOURCE_CUT_INCOHERENT, REQUIREMENT_COVERAGE_MISSING, JOINT_WITNESS_MISMATCH, GAP_SUBSTITUTION | REJECTED; null |
| HARD_CONTAINMENT_FAILED, GOAL_DIRECTION_CONFLICT, PRECISION_NESTING_FAILED, PROTECTED_INTERVAL_CONFLICT | POLICY_CONFLICT; null |
| NO_PROTECTED_JOINT_WITNESS, NO_JOINT_COMFORT_SUPPORT | RESOLUTION_INSUFFICIENT; null; distinct nonnumeric support diagnostics (§7) |
| RESOURCE_LIMIT | RESOURCE_EXCEEDED; null; no truncation |
| ORIGIN_NOT_ESTABLISHED, REGISTRY_CHANGED, CAPTURE_EXPIRED, CONSUME_REPLAY, REPORT_NOT_AUTHORITY | Host ADMISSION_REJECTED; no numeric payload |
| ENVIRONMENT_MISMATCH, PRODUCTION_GATE_CLOSED | REJECTED or host ADMISSION_REJECTED at ingress; no production path |
| CAPTURE_FAILED, HOST_TIMEOUT | Host CAPTURE_REJECTED or RESOURCE_EXCEEDED respectively; no partial capture/use |
| POLICY_SEMANTICS_INCONSISTENT | Checker INCONSISTENT; host ADMISSION_REJECTED |

Missing versus malformed, withdrawn versus unknown, consistent non-success versus fabricated
positive, soft violations versus hard conflicts remain distinct. Source authority is checked
before arithmetic. Phase order is PARSE→IDENTITY→SOURCE→NRE→MBA→RULE→COVERAGE→JOINT; choose the
first failure. Within a phase sort by canonical subject path then reason. Do not catch an
unrecognized internal error and synthesize AVAILABLE; hosting maps it to CAPTURE_FAILED or
SOURCE_MALFORMED without exposing partial data. Trace/data sizes are checked before release.
An all-or-error **frozen capture exception may be opaque**: after the unchanged adapter starts,
unknown source/SQL exceptions map to host CAPTURE_REJECTED/CAPTURE_FAILED, not a guessed missing,
withdrawn or safe state. Specific source taxonomy above applies when retained primitive
evidence permits reconstruction. No partial source tree is extracted from a failed capture
just to improve its error message. Known resource timeout maps to RESOURCE_EXCEEDED/HOST_TIMEOUT.
This limitation withholds numerical use; it never relaxes source requirements.

## 10. Security and source-time boundaries

No new credentials/enrollment/publication interface, HTTP endpoint, persistent source or broad
database grants. Reuse only existing isolated TEST_ONLY reader rights. Existing verified
database/login OID, role graph/SCRAM/TLS checks remain in protected paths. SET ROLE, shared-login
actor labels, source-owner/superuser as ordinary reader, forged contexts and favorable-row
selection do not become authorized inputs. Household role permits the existing bounded
planning intent, never member-goal representation, clinical qualification or guideline publication.

Member facts/goals remain member-owned, not copied into a guideline/rule source or another
member. No unrelated household histories are exposed. Valid/effective time, recorded order,
publication time, capture interval and requested calendar are separate. Future-effective
supersession must not erase current history early; retrospective correction cannot rewrite an
old retained cut. Required interval spanning two source versions remains unsupported.

TEST_ONLY taint is mandatory in every nested source/evidence/authority, estimate, meaning,
claim, report and handoff. Retagging the outer record cannot wash a child taint or create a
production-positive mode. Structural source integrity is not medical/scientific correctness.
All admitted numerical examples in future tests must be unmistakably synthetic TEST_ONLY,
not installed providers, real population protocols, production qualification or numerical defaults.

## 11. Server-owned resource limits and all-or-error hosting

These are structural design caps, not clinical constants. Existing child limits remain unchanged
and cannot be raised by a v2 wrapper. Inputs have no caller-authored budget that can increase them.

| Resource | Absolute proposed v2 cap / enforcement |
|---|---|
| Selector ingress | Frozen selector cap64KiB before recursive parsing |
| Integration input / nested source | 32MiB total; MBA artifact2MiB; embedded NRE sources16MiB |
| Result / complete handoff / check | 8MiB /48MiB /256KiB encoded; reject whole output on overflow |
| Structure | Depth32; at most1,000,000 visited nodes; string100,000 chars; reject duplicate keys before canonicalization |
| Integers/rationals | Frozen endpoint127-bit limits; NRE/Rat operands256 bits; bounded temporary arithmetic<=1024 bits; reduced results checked after each operation |
| Scope / retained evidence | Frozen maxima:32 recipes,14 slots,512 reference selections,8192 owner rows,32 periods;256 MBA events,128 anchors; no source truncation |
| Claims/trace/support | <=256 claims/operations;128 coverage rows;16384 assignments;65536 retained witness tuples and65536 center deltas; output cap still applies |
| New producer/checker work | Each<=2,000,000 charged scalar/parse/lookup/comparison/output steps, deterministic fixed iteration order |
| Child composition | Fixed call graph: capture NRE once; producer MBA replay includes one fresh NRE; checker explicit NRE plus MBA's independent NRE. At most4 complete NRE runs per capture/use, each retaining frozen1,000,000 work cap; no recursion/retry/cache shortcuts |
| Total logical reservation | <=11,000,000 charged work units: four NRE caps + three MBA artifact/replay caps (capture, producer, checker) at1,000,000 each + producer/checker2,000,000 each; bounded source/parser cardinalities additionally apply; not CPU instruction accounting |
| Hosting | Capture watchdog60s; pure producer/checker each15s; complete capture/use<=90s including parsing/output, no fresh budget on retries |

Charge before growing a cross-product/table and before rational operations; check output bounds
before materialization grows beyond a cap. Existing source-limit failures remain failures even
if parent has spare budget. A repeated capture/consume attempt is a new operation, never a way
to continue partial favorable history. Cancelled/failed leases are burned; no successful prefix.

Pure work limits deterministically replay. Wall-time timeout is operational, not claimed
deterministic replay evidence. For new v2 pure hosting use killable isolated worker processes,
using an explicit spawn start method and bounded canonical JSON bytes, never fork-inherited
connections, a database Session, credentials, registry handles or caller-defined executables.
The host scrubs source credentials/URLs from the worker environment; no environment-selected
numeric content is read. Kill/join on timeout and discard output before returning. A timed-out Python thread continuing
to run is not a hard execution budget. Process startup/copy/output count toward the90s cap. Each phase receives at most the lesser
of its stage cap and the remaining operation budget; no phase resets the total deadline.
The trusted parent retains the actual capture/session/registry association and rechecks it at
consumption. This is not a hostile-code sandbox. Public HTTP/concurrency/production ingress
controls remain a separate Planner API gate; no endpoints are added here.

## 12. Future executable acceptance specification

**DESIGNED OBLIGATIONS ONLY — NONE OF THE FOLLOWING ARE IMPLEMENTED OR EXECUTED BY THIS PR.**
Each family below has an invariant, separate Producer(P)/Validation(V)/Admission(A) expectation,
positive/adversarial fixture, expected outcome/reason, exact evidence/tamper seam, test class
and compatibility assertion. Parameterized negatives are mandatory, not optional examples. Whenever P/V
shorthand is used, execute separate producer and independent-checker assertions against each
positive and listed mutation; producer output is never the checker oracle. A assertions test
the actual host interface; pure lease controls do not substitute for the PG rows below.

Fixture catalog (all synthetic TEST_ONLY; re-author test source histories without editing frozen fixtures):

- **D+**: one DAY, complete real captured Root/rule/precision/owner evidence, same-meaning full MBA
  manifest, complete horizon witness set and H/C nonempty, canonical bounds from its published fixture.
- **W+**: one WEEK with exact authored DAY partition, explicit daily/weekly hard/goal/comfort/center
  coverage, required unweighted period maps and retained complete DAY+WEEK NRE periods, H/C nonempty.
- **R+**: archived D+/W+ bytes for offline replay; never a trusted capture lease.
- **J+**: correlated joint vectors with at least one common H/C assignment and another H\C soft
  violation; equal-vector alternative configurations and inclusive-boundary support included.
- **L+**: independently retained valid review/publication/delegation/source lifecycle, including
  legitimate retrospective publication and future-effective supersession before/at/after its boundary.
- **X**: each named negative mutation below. Recompute every public hash/parent pin after semantic
  edits; a failing stale hash alone does not satisfy a semantic-forgery test. Re-author authorized
  TEST_ONLY histories where a test targets arithmetic rather than integrity; do not fake admission.

Compatibility keys are mandatory assertions per row: **K1**=all515 baseline definition bodies,
503 historical hashes and53 frozen files unchanged; **K2**=frozen v1 fixture-only semantics and
NRE/MBA closed literals/source behavior unchanged; **K3**=0017/108,no0018,no persistence/DB grants;
**K4**=TEST_ONLY/scientific non-authority/production CLOSED/readinessFalse/parent status unchanged.
Every family includes K1/K4; the additional listed keys are explicit per-family requirements.

### PIV-D01 — Complete positive structural composition
- P: D+/W+ produce AVAILABLE_TEST_ONLY, complete payload and canonical fingerprints. V: independently reconstruct identical payload, CONSISTENT/AVAILABLE_RETAINED_ONLY. A: fresh issued lease consumed once, correct expected use, no transferable authority.
- Fixtures: D+, W+; X removes one mandatory anchor or retained period. Evidence/tamper: full primitive tree, coverage, source and result pins. Expected negative: SOURCE_UNAVAILABLE/ANCHOR_COVERAGE_MISSING or PERIOD_COVERAGE_MISSING; V confirms negative only if faithfully reconstructed; A releases no numbers.
- Class: pure plus PG01. Compatibility: K1/K2/K3/K4.

### PIV-D02 — Capture identity is not serialized origin proof
- P: R+ and a completely self-consistent fabricated retained ledger may derive only offline semantics. V: may be CONSISTENT when every retained semantic relation is valid; must still claim NOT_PROVED_OFFLINE. A: rejects any JSON/hash/UUID/copy-created lease with ORIGIN_NOT_ESTABLISHED.
- Fixtures: actual D+ capture versus X reconstructs all public frames/OIDs/hashes and trusted-looking labels without the privately issued object. Evidence/tamper: input bytes, process identity/registry and active transaction. No fabricated truth may pass solely because P/V accept its arithmetic.
- Expected: real D+ one-shot inspection succeeds; forged/copy-created lease gives host ADMISSION_REJECTED/ORIGIN_NOT_ESTABLISHED even if its offline arithmetic is CONSISTENT. No fabricated truth may acquire origin authority.
- Class: pure forgery plus PG08. Compatibility: K1/K2/K3/K4.

### PIV-D03 — Forged NRE report cannot skip fresh verification
- P: recomputes retained NRE through frozen MBA producer replay. V: freshly invokes independent NRE, rejects edited ingredient contribution/configuration even with fabricated CONSISTENT and matching hashes. A: never accepts a supplied report parameter.
- Fixtures: D+; X alters joint vector/contribution, fully rehashes and attaches a positive NRE report. Evidence: ingredient quantities/references/configurations. Expected: REJECTED/NRE_INCONSISTENT; V INCONSISTENT for forged positive; no numeric admission.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D04 — Forged MBA positive cannot mint applicability
- P: reconstructs all source meaning/authority; missing or contradictory anchors withholds applicability. V: independently reconstructs journal/anchors, not supplied APPLICABLE_TEST_ONLY/CONSISTENT. A: burns lease after failed checking.
- Fixtures: D+; X forges a favorable assertion/witness, missing original preimage or expired grant while rehashing all records. Evidence: original guideline/rule evidence and complete registry prefix. Expected: REJECTED/MBA_INCONSISTENT for a forged positive, or faithful SOURCE_UNAVAILABLE/MBA_UNAVAILABLE for missing evidence; no favorable partial witnesses.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D05 — Whole-policy/check/reference forgery
- P: creates canonical complete result, never accepts validation as input. V: edited claim, H/C count, representative or arithmetic with matching public pins and forged CONSISTENT is INCONSISTENT/POLICY_SEMANTICS_INCONSISTENT. A: accepts no caller result/report override.
- Fixtures: J+; X independently mutates each field listed and attaches stale/forged check. Evidence: source-bound rule trace and assignment proof. A genuinely matching attached report remains only unverified audit data; cannot substitute for a lease.
- Expected: genuine complete result is CONSISTENT; altered favorable policy is INCONSISTENT/POLICY_SEMANTICS_INCONSISTENT; disagreeing attached report is REPORT_NOT_AUTHORITY. Serialized matching claims without a lease still give ADMISSION_REJECTED/ORIGIN_NOT_ESTABLISHED.
- Class: pure plus PG08 origin control. Compatibility: K1/K2/K4.

### PIV-D06 — Consistent negative is not positive use
- P: faithful NRE_UNAVAILABLE or MBA_NOT_APPLICABLE yields null payload. V: can return CONSISTENT with NOT_ADMITTED/reconstructed non-success, never AVAILABLE_RETAINED_ONLY. A: returns diagnostics only and burns lease.
- Fixtures: D+ positive; X removes required source/meaning evidence with faithful negative child. Evidence: child state plus complete reasons, not report label. Expected: SOURCE_UNAVAILABLE/NRE_UNAVAILABLE for the NRE control, or UNSUPPORTED/UNIT_OR_SCOPE_MISMATCH for genuine material-basis NOT_APPLICABLE; support NOT_EVALUATED.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D07 — Exact root/rule/requirement and full coverage
- P: compares unchanged COMFORT-only RequirementSpec and separately complete MBA manifest. V: reconstructs both independently; no subset requestedness. A: binds exact source pins.
- Fixtures: W+; X changes root/rule/case/requirement pin, drops a hard/weekly or unselected precision anchor, or treats RequirementSpec as complete coverage. Evidence: retained root/rule operations and all MAKE branches. Expected: REJECTED/REQUIREMENT_COVERAGE_MISSING or SOURCE_UNAVAILABLE/ANCHOR_COVERAGE_MISSING; forged favorable parent inconsistent.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D08 — Original-source measurement meaning
- P: every original/derived/unused-precision anchor needs matching original preimage. V: recomputes meaning/evidence manifest, no downstream assertion replacement. A: no origin/meaning shortcut.
- Fixtures: D+/W+; X removes, duplicates or contradicts one original meaning then forges a wrapper meaning. Evidence: guideline evidence_manifest, rule.evidence, exact source body hashes. Expected: SOURCE_UNAVAILABLE/MBA_UNAVAILABLE or REJECTED/MBA_INCONSISTENT; no usable policy.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D09 — No planned/offered/consumed/physiological conversion
- P/V: only original PLANNED_INGREDIENT_INPUT_V1 with NRE_EXACT_PLANNED_INPUT/v1 is positive; each other vocabulary transition fails before comparison. A: production interpretation/retagging rejected.
- Fixtures: D+; X replaces original meaning with planned/observed offered, observed consumed, physiological or unspecified while keeping equal metric/unit/amount. Evidence: original preimages, assertion and interpretation version. Expected: UNSUPPORTED/MEANING_MISMATCH (missing meaning may be SOURCE_UNAVAILABLE/MBA_UNAVAILABLE); no coefficient or identity bridge.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D10 — Descriptor/subject/unit and one-sided bounds
- P/V: same exact descriptor required before arithmetic; MINIMUM/MAXIMUM preserve absent opposite bound, TARGET stays soft. A: mismatched expected subject/actor rejected.
- Fixtures: D+ with RANGE/MINIMUM/MAXIMUM/TARGET; X independently changes metric/unit/material basis/scope/protocol/member/household, or adds an inferred opposite bound/target interval. Evidence: complete descriptor, material refs and subject. Expected: UNSUPPORTED/UNIT_OR_SCOPE_MISMATCH or REJECTED/SOURCE_IDENTITY_MISMATCH; altered favorable policy inconsistent.
- Class: pure plus PG04 exact actor/subject source control. Compatibility: K1/K2/K4.

### PIV-D11 — Canonical finite-universe completeness
- P/V: full declared recipes/tiers/rules/references/slots and all equal-vector witnesses required; caller completeness label is not proof. A: actual source capture reconstructs owner rows/seals/absence evidence.
- Fixtures: D+/W+; X deletes an unfavorable reference/rule/slot, omits a recipe child, duplicates a seal or supplies favorable-only rows. Evidence: exact owner snapshots/manifests/counts and serving selections. Expected: capture rejection or REJECTED/NRE_INCONSISTENT; faithful absence SOURCE_UNAVAILABLE/NRE_UNAVAILABLE, never silent truncation.
- Class: pure plus PG05. Compatibility: K1/K2/K3/K4.

### PIV-D12 — Correlated nutrients require the same assignment
- P/V: compute A/H/C from full joint vectors, retain all configuration tuples. A: no marginal-positive substitute.
- Fixtures: J+; X uses individually supported low/high components from different configurations to claim common H/C support. Evidence: tuple→configuration→ingredient/reference lineage. Expected: faithful RESOLUTION_INSUFFICIENT/NO_PROTECTED_JOINT_WITNESS or NO_JOINT_COMFORT_SUPPORT; forged favorable parent INCONSISTENT/JOINT_WITNESS_MISMATCH or POLICY_SEMANTICS_INCONSISTENT.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D13 — Gaps, singleton and exact boundary support
- P/V: actual vectors, inclusive equality and every equal-vector witness determine support; singleton has no adjacent step. A: no v1 fixture cast.
- Fixtures: J+ and singleton D+ with a band containing a vector despite a larger unrelated maximum gap; X substitutes maximum_gap/minimum_gap/GCD/extrema or zero singleton step for the full set. Evidence: full projected gaps and underlying joint tuples. Expected: genuine support AVAILABLE_TEST_ONLY; replacement REJECTED/GAP_SUBSTITUTION or forged parent INCONSISTENT/POLICY_SEMANTICS_INCONSISTENT.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D14 — DAY/WEEK assignment coherence
- P/V: each period uses the restriction of one complete horizon assignment; no independent day choices inconsistent with its week. A: binds the same calendar/source scope.
- Fixtures: W+; X supplies mutually incompatible day/week witnesses or removes the horizon period while all day marginals remain. Evidence: sorted slot IDs, complete horizon tuples and exact period vectors. Expected: REJECTED/JOINT_WITNESS_MISMATCH or SOURCE_UNAVAILABLE/PERIOD_COVERAGE_MISSING; no synthesized week or full-solver infeasibility claim.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D15 — Hard-root preservation and containment
- P/V: retain every root byte-for-byte; conjoin hard roots and exact protected ranges/floors/ceilings, preserve reference TARGET distinction. A: no favorable partial payload on conflict.
- Fixtures: D+ all four root types; X drops a hard clause, widens a protected bound, changes interpretation or removes an opposite bound required by the source. Evidence: original resolved roots, claims/trace/descriptors. Expected: POLICY_CONFLICT/HARD_CONTAINMENT_FAILED for authored conflict, or INCONSISTENT/POLICY_SEMANTICS_INCONSISTENT for forged result.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D16 — Exact current member goal lineage
- P/V: one exact goal revision/direction/reference/comparator, no cross-member copying or resurrection. A: subject remains the captured member.
- Fixtures: D+ with valid goal; X absent/retracted/ambiguous/expired goal, later replacement or another member's goal with rehashed pins. Evidence: source observation/delegation/goal journal and effective interval. Expected: SOURCE_UNAVAILABLE/GOAL_SOURCE_UNAVAILABLE or POLICY_CONFLICT/GOAL_DIRECTION_CONFLICT; no MAINTAIN fallback.
- Class: pure plus PG06 new-cut source selection (opaque adapter failures are CAPTURE_REJECTED/CAPTURE_FAILED). Compatibility: K1/K2/K4.

### PIV-D17 — Daily protection authority is explicit
- P/V: each daily_root_key has exact source-authored protection for every cell; weekly authority cannot fill a missing day. A: no omitted requiredness override.
- Fixtures: W+; X drops daily authority/claim or allows one daily hard breach while keeping an acceptable weekly total. Evidence: published daily manifest, per-day claims/roots and shared assignment. Expected: SOURCE_UNAVAILABLE/DAILY_PROTECTION_MISSING or RESOLUTION_INSUFFICIENT/NO_PROTECTED_JOINT_WITNESS; not a softened hard bound.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D18 — Weekly hard conjunction versus soft centering
- P/V: keep aggregate hard/goal root, explicit weekly protected claim and soft center; all DAY protections survive. A: no global-feasible label.
- Fixtures: W+ with H\C and nonzero symbolic center deltas; X drops aggregate hard goal, turns TARGET into equality or claims all soft daily combinations satisfy the week. Evidence: retained week/day roots, unit period map and configurations. Expected: POLICY_CONFLICT/PROTECTED_INTERVAL_CONFLICT for authored contradiction; forged favorable result inconsistent; soft deltas/violations alone are not hard conflict.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D19 — Authenticated explicit precision
- P/V: exact REQUEST_EXPLICIT/version/actor/subject/evidence plus retained DB witness; enum alone is insufficient. A: source login/member checks and expected use must match.
- Fixtures: D+ authorized OWNER/EDITOR intent; X forged membership/user/subject, missing witness or unauthorized role. Evidence: actual synthesis reader principal/membership and selection. Expected: capture rejection/PRECISION_UNAUTHORIZED or REJECTED/PRECISION_IDENTITY_MISMATCH; no goal/publisher authority inferred.
- Class: pure plus PG04. Compatibility: K1/K2/K3/K4.

### PIV-D20 — Same precision identity throughout
- P/V: unchanged complete selection propagates request→NRE→MBA→v2; equal enum with different version/evidence/actor is not equality. A: use precision fingerprint equals private captured value.
- Fixtures: D+; X changes a single nested precision pin or omits it and requests a default/week override. Evidence: full identity trees, not a naked enum. Expected: REJECTED/PRECISION_IDENTITY_MISMATCH or SOURCE_UNAVAILABLE/PRECISION_UNAUTHORIZED; no STANDARD default or MTR-008 precedence.
- Class: pure plus PG04 source control. Compatibility: K1/K2/K4.

### PIV-D21 — Reviewed nested comfort only
- P/V: every unselected branch retains source meaning/containment; selected PRECISION⊆STANDARD⊆RELAXED; other preference axes cannot become operands. A: no permissive override.
- Fixtures: D+ for each explicit enum; X unnests branches or injects Cost/Budget/Effort/convenience/TasteFit to widen hard/goal bounds. Evidence: complete authored finite instructions and all MAKE anchors. Expected: POLICY_CONFLICT/PRECISION_NESTING_FAILED or HARD_CONTAINMENT_FAILED; injected fields REJECTED/SOURCE_MALFORMED.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D22 — Non-success taxonomy and soft violations
- P/V: separately prove valid sources, interval consistency, H and C. A: only complete AVAILABLE payload is numerically used; negative carries no numeric witness.
- Fixtures: separate source-missing, contradictory-interval, H-empty, H-present/C-empty and J+ H\C controls. Evidence: full finite sets plus exact protected intervals. Expected: SOURCE_UNAVAILABLE, POLICY_CONFLICT, RESOLUTION_INSUFFICIENT/NO_PROTECTED_JOINT_WITNESS, RESOLUTION_INSUFFICIENT/NO_JOINT_COMFORT_SUPPORT with hard_support=PRESENT, and AVAILABLE with soft violation rows respectively; never solver INFEASIBLE.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D23 — Exact publication/temporal identity
- P/V: exact source/provider/family/publication/version and effective scope with recorded-prefix order; no latest fallback. A: captured cut/pins only, no mutable global lookup.
- Fixtures: L+; X swaps publication/provider, shortens coverage or supplies later facts to an older retained prefix. Evidence: root/rule/MBA complete histories, source frames and valid times. Expected: SOURCE_UNAVAILABLE/SOURCE_WITHDRAWN or REJECTED/SOURCE_IDENTITY_MISMATCH; unchanged historical replay stays deterministic.
- Class: pure plus PG06. Compatibility: K1/K2/K4.

### PIV-D24 — Publication-time reviewer/publisher authority
- P/V: original reviewer and publisher scoped capability/symbolic qualification valid at PUBLISH/SUPERSEDE recorded_at and whole assertion interval, using that immutable prefix; correct distinct identities. A: does not repair failed source semantics.
- Fixtures: legitimate retrospective L+; X grant or qualification expired before publication without REVOKE, with/without later backdated renewal/requalification, for PUBLISH and SUPERSEDE. Evidence: full authority/review/publication prefix and exact reviewed body. Expected: the unauthorized MBA publication is child REJECTED and parent REJECTED/MBA_INCONSISTENT, with exact child capability/qualification reason retained; V returns INCONSISTENT/NOT_ADMITTED even for a faithful rejection of corrupted source history. No partial witnesses.
- Class: pure (MBA authority is not a new PG journal). Compatibility: K1/K2/K4; retains MBA-R133-01 behavior.

### PIV-D25 — Withdrawal, future succession and replay scope
- P/V: L+ current and historical cuts differ only as their retained knowledge/effective boundaries require; future succession not early. A: an old success cannot authorize a new use after revoke/withdrawal.
- Fixtures: before/at/after effective boundary; X old handoff reused after a real source revoke or registry withdrawal, or retroactively edits old snapshot. Evidence: captured histories/frontiers, lease and exact interval. Expected: new capture SOURCE_UNAVAILABLE/SOURCE_WITHDRAWN or SOURCE_UNAUTHORIZED; old replay may remain CONSISTENT; reused lease ADMISSION_REJECTED/CONSUME_REPLAY or CAPTURE_EXPIRED.
- Class: pure plus PG06/PG07. Compatibility: K1/K2/K3/K4.

### PIV-D26 — One actual cut and stable registry through consume
- P/V: retain coherent source frames and period/subject identity. A: same live transaction/connection, private registry object before/after capture and after Validation; registry advance/revoke during checking burns lease atomically.
- Fixtures: actual D+/W+; X mixes independent owner cuts, closes/reopens transaction on same Session, switches connection or changes registry/context during checker; race two consumes. Evidence: DB snapshot/connection/transaction identity plus object association. Expected: SOURCE_CUT_INCOHERENT, REGISTRY_CHANGED, CAPTURE_EXPIRED or CONSUME_REPLAY; no partial numerical admission.
- Class: pure race tests plus PG02/PG03/PG07/PG08. Compatibility: K1/K2/K3/K4.

### PIV-D27 — Unsupported temporal maps fail closed
- P/V: one exact supported DAY/WEEK, calendar/timezone and reviewed partition; required sums authored unit coefficients only. A: expected scope cannot change mid-use.
- Fixtures: W+; X non-unit required FINITE_PERIOD_SUM, EXACT_INTERVAL/multi-week frame, slot straddling day, calendar/timezone mismatch, absent week period or cross-version stitching. Evidence: original rule/calendar, NRE slots/periods, all anchors. Expected: UNSUPPORTED/UNSUPPORTED_TEMPORAL_MAP or SOURCE_UNAVAILABLE/PERIOD_COVERAGE_MISSING; source-authored endpoint projection does not scale food values.
- Class: pure. Compatibility: K1/K2/K4.

### PIV-D28 — TEST_ONLY taint is transitive
- P/V: every nested source/authority/meaning/claim/report is TEST_ONLY and non-scientific. A: private isolated context required, production mode rejected.
- Fixtures: D+; X changes outer/inner environment independently, strips taint or requests a production provider/publication/default/qualification. Evidence: entire retained tree and host context. Expected: REJECTED/ENVIRONMENT_MISMATCH or ADMISSION_REJECTED/PRODUCTION_GATE_CLOSED; no production-positive result.
- Class: pure plus PG02/PG10 isolated-environment proof. Compatibility: K1/K2/K3/K4.

### PIV-D29 — Whole-policy independent reconstruction
- P: pure v2 evaluator distinct from checker. V: forbidden producer/Planning/solver imports fail architecture checks; independently changed primitive forces a different expected policy despite rehashing. A: invokes fresh checker, not producer semantic validator.
- Fixtures: D+/J+; X producer-only arithmetic/coverage/witness mutation plus AST forbidden import or stale check. Evidence: source-defined operation trace and checker import/call graph. Expected: checker INCONSISTENT/POLICY_SEMANTICS_INCONSISTENT; structural guard failure for forbidden import; no numeric use.
- Class: pure/static guard. Compatibility: K1/K2/K4.

### PIV-D30 — Absolute resources, cancellation and no favorable prefixes
- P/V: exact bound and bound+1 cases for bytes/depth/nodes/integer/history/manifest/state/witness/output/work; checked finite operations. A: real capture cancellation and pure-worker deadline burn lease and discard all partial output, no budget reset/retry.
- Fixtures: bounded D+; X exceeds each cap, supplies duplicate keys/nonfinite/float, forces a large product or races timeout with consumption. Evidence: server profile, work counters, actual worker/DB cancellation. Expected: REJECTED/SOURCE_MALFORMED or RESOURCE_EXCEEDED/RESOURCE_LIMIT/HOST_TIMEOUT; deterministic pure failures and operational timeout distinguished.
- Class: pure plus PG09 actual capture cancellation. Compatibility: K1/K2/K3/K4.

### PIV-D31 — Frozen compatibility and no persistence expansion
- P/V/A: all existing public definitions, historical files/accepted v1 behavior and old source permissions remain; only additive proposed v2 contracts can later be registered. No current test is replaced.
- Fixtures: exact approved baseline pins; X mutates an old definition/file/migration/grant or casts NRE into the v1 fixture. Evidence: all515 schema bodies,503 historical hashes,53 frozen files plus frozen MBA implementation files,4183 baseline node IDs, metadata and actual migrations. Expected: compatibility failure, not an updated permissive pin or waived test.
- Class: pure/static plus PG10. Compatibility: K1/K2/K3/K4, all mandatory.

### PIV-D32 — Closed production/downstream gates
- P/V/A: results retain all non-authority literals; no production source/provider/qualification/publication/seed/default, MTR-008, solver, activation or parent completion. No new DB object/right.
- Fixtures: D+/W+ synthetic inspection; X attempts production admission, readiness=True, policy-as-full-plan validation or parent COMPLETE. Evidence: source/install inventory, transport flags and status docs. Expected: REJECTED or ADMISSION_REJECTED/PRODUCTION_GATE_CLOSED; false/closed literals reject mutation; no clinical numbers published.
- Class: pure/static plus PG10 fresh-install rows. Compatibility: K1/K2/K3/K4.

## 13. Mandatory future real-PostgreSQL obligations — exactly10

These ten are independent source/admission failure seams requiring an actual reader/transaction
or installation, not ten arbitrarily chosen test functions. Parameterization may produce more
than10 executions; implementation must report obligation→executed-case mapping and actual count.
No obligation is satisfied by mocks, collection-only output or rerunning a pure test with a
database fixture. Existing frozen suites remain mandatory but do not prove a new composition.

| ID | Mandatory real-PG proof and controls | Why PG is required / families |
|---|---|---|
| PIV-PG01 | Full D+ and W+ capture→derive→fresh independent consumer→one-shot use; exact source identities and terminal unverified status | Actual canonical owner/source path must work together; D01 |
| PIV-PG02 | Actual DB/login/OID/role binding; wrong database/context, unsafe/source-owner actor, SET ROLE/shared-login/writable-schema controls; no additional grants | A fabricated reader frame cannot prove authentication/privilege behavior; D26/28 |
| PIV-PG03 | Clean actual read-only RR/SERIALIZABLE transaction; reject dirty/routed/multiple-connection/non-repeatable paths; close/reopen same Session cannot reuse lease | Real transaction/connection lifetime, not a serialized field; D26 |
| PIV-PG04 | Precision actor/member/household membership positive and revoked/wrong-role/other-subject negatives through the protected capture | DB-observed planning-intent authorization is source truth; D10/19/20 |
| PIV-PG05 | Actual complete recipe/tier/rule/seal/reference/slot capture; missing/unfavorable owner row control and concurrent commit prove coherent old cut versus next fresh cut | Source enumeration/completeness/MVCC cannot be proved by a caller manifest; D11 |
| PIV-PG06 | Root and synthesis reader grant revocation, publication withdrawal/effective successor before a fresh snapshot reject the exact stale selector; retained older replay stays historical. Opaque frozen adapter exception gives CAPTURE_REJECTED/CAPTURE_FAILED, never partial input | Real protected authority/selection state coupled to new consumer; D16/23/25 |
| PIV-PG07 | Change/revoke issued MBA registry context during actual PG capture and during independent checking; no successful use after final registration mismatch | Proves combined database/registry operation without claiming shared MVCC; D25/26 |
| PIV-PG08 | After a real capture, forged/copy/replayed/transplanted lease and fully matching serialized evidence cannot admit use; concurrent consumption exactly-once | Proves binding of real capture to the trusted host seam, not report arithmetic; D02/05/26 |
| PIV-PG09 | Actual database capture timeout/cancel plus whole-operation timeout yields no successful source/use, burns association and leaves caller responsible for rollback | In-memory timer mock cannot prove DB cancellation/transaction behavior; D30 |
| PIV-PG10 | Fresh migrated install0017/108,no0018,new tables/functions/roles/grants=0; existing Nutrition source/provider/qualification/content/publication/seed/default rows empty before isolated TEST_ONLY setup | Installation/source permission assertions require real migrated DB, not metadata alone; D28/31/32 |

Publication-time symbolic MBA qualification/reviewer replay, finite arithmetic, report forgery,
joint-set semantics and pure worker cancellation remain pure tests unless the row above
explicitly exercises actual capture. No new PG basis authority journal is invented. Reuse
existing disposable test setup and its exact grants; do not install qualified production actors.

## 14. Compatibility, persistence and review checklist

The design requires **no new persistence, SQL functions, roles, source capabilities or database
privileges**, and no0018. Frozen source ownership and isolation remain sufficient for the
bounded TEST_ONLY path. This PR changes only this document and four minimal current-status
notices; approved prior designs/evidence/freeze receipts are not rewritten.

Future implementation must retain every one of the4183 baseline tests and515 exported bodies,
the503 historical definition hashes,53 frozen source/migration files, and the entire frozen
MBA implementation semantics/bytes. New definitions may only be additive. Future companion
guards/export registration must name exact new files and preserve old guards; no global
cross-context import permission. This design does not reserve a final export delta.

Review checklist:

- Source/identity/meaning is established before comparison; original source remains authoritative.
- Process-local one-shot association cannot be reconstructed from JSON; current transaction and
  registry are pinned, race/timeout burns association; no present authorization outside its cut.
- Full independently checked child and parent semantics, all-layer coverage and authenticated
  precision; no producer business oracle, cached reports, scalar-gap substitution or invented week.
- UNIT-only required period maps are an explicit v2 subset; source-authored bound projections
  remain distinct from measuring/transforming actual food or intake.
- Every family has executable positive/adversarial outcomes and a compatibility assertion;
  all10 PG obligations have an execution plan but are not yet executed.
- Resource limits/host liveness and deterministic replay are distinct; no favorable prefixes.
- Production science, qualification, defaults and content remain CLOSED; full MTR-006/007/008
  incomplete, issues OPEN, planner/activation=False, Execution NOT STARTED, PRECOMMIT FAIL-CLOSED.

## 15. Open questions, risks and disposition

No unresolved **structural design blocker** was found within this narrowed profile. The design
chooses cut-scoped, single-use inspection rather than pretending to offer instantaneous
revocation, and refuses unsupported periods/maps instead of expanding frozen estimators.
The private Planning/MBA registry dependency and killable-worker/transaction lifetime behavior
are explicit implementation risks requiring the acceptance controls above, not hidden authority.
Unsupported rule/calendar cases return typed non-success; broadening them requires another
reviewed version, never a permissive fallback.

Production numerical content, qualified authorities, clinical populations/protocols and any
scientific measurement equivalence remain **unresolved production prerequisites and CLOSED**.
This design neither needs nor fabricates a production-positive pathway. Full MTR-008 precedence,
solver feasibility, independent whole-plan validation, product APIs and activation are deferred.

If implementation cannot preserve frozen bytes/semantics, existing reader rights, process-local
capture identity or no-persistence scope, stop and request a separate governance decision.
Do not silently add durable basis authority, privileged reads, a clinical bridge or new defaults.

**MTR-006 V2 BOUNDED DETAILED DESIGN — READY FOR INDEPENDENT ARCHITECTURE REVIEW / IMPLEMENTATION NOT AUTHORIZED**

Leave the design PR OPEN, auto-merge OFF. No self-approval, merge, freeze, runtime/contracts/tests/
tooling/data changes, migration, production publication, issue closure or downstream work is authorized.
