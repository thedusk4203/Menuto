# Source-Bound Measurement-Basis Applicability & Independent Evidence Containment

**BOUNDED DETAILED DESIGN — STRUCTURAL / TEST_ONLY.**
**DESIGN CANDIDATE — NOT ARCHITECTURE APPROVED; IMPLEMENTATION NOT AUTHORIZED.**

## 1. Authority, baseline and scope

| Record | Pinned identity |
| --- | --- |
| Exact main / design base | `bd2ad5308a58138be0c58a40f3100e60305fca58` |
| Governing dependency review | [PR #131](https://github.com/thedusk4203/Menuto/pull/131); [retained review](POST_MTR_007_MEASUREMENT_BASIS_POLICY_V2_DEPENDENCY_REVIEW.md) |
| Architecture disposition | [PASS 6675396778](https://github.com/thedusk4203/Menuto/pull/131#issuecomment-6675396778) |
| Exact merge completion | [6676086123](https://github.com/thedusk4203/Menuto/pull/131#issuecomment-6676086123) |
| Baseline main push | [42153146331 — SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/42153146331) |
| Retained footprint | 4,047 tests / 0 skips; 503 frozen exported definitions; migration 0017 / 108 domain tables |

This document designs one additive measurement-meaning applicability module. It does
not implement a basis conversion, nutrition policy integration, clinical interpretation,
source database, or production publication service. All contracts and test obligations
below are **proposals, not implemented exports or executed acceptance tests**.

Governing requirements: [ADR-002](../adr/ADR-002-nutrition-policy-engine.md),
[ADR-003](../adr/ADR-003-plan-policy-resolution.md),
[ADR-010](../adr/ADR-010-independent-validator.md),
[INV-001/003/004/016–020](../ARCHITECTURE_INVARIANTS.md), and
[Development Spec V1.3 §§8.1, 8.3, 10.3–10.4, 18.2–18.3](../MENUTO_DEVELOPMENT_SPEC_V1_3.md).
The [Root](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_DESIGN.md),
[MTR-006 v1](MTR_006_SOURCE_BOUND_NUTRITION_POLICY_SYNTHESIS_CONTAINMENT_DESIGN.md), and
[MTR-007](MTR_007_SOURCE_BOUND_NUTRITION_RESOLUTION_ESTIMATOR_DESIGN.md) structural
foundations remain frozen.

### Decisions

1. V1 permits **only explicitly authored same-meaning planned-input applicability in
   isolated TEST_ONLY fixtures**. It performs no numerical transformation or policy synthesis.
2. A companion pins the original guideline/rule evidence, pre-policy requirement and
   complete retained NRE scope. It cannot reinterpret an old root or change a frozen descriptor.
3. Nutrition owns interpretation/source semantics; Validation independently reconstructs
   applicability; Planning owns authenticated composition. Member facts remain member-owned.
4. A server-owned immutable TEST_ONLY fixture registry supplies publication/evidence
   history. There is **no new PostgreSQL authority or persistence** in the proposed slice.
5. Production applicability is unavailable. Scientific evidence, qualified actors and
   production publication governance require separate source/content authorization.

## 2. Frozen facts and the problem being solved

`NutritionRootDescriptor` pins metric, unit, scope/version, protocol and exact temporal
scope, but has no explicit measured-quantity interpretation. Equal ENERGY/KCAL or
PROTEIN/G is not evidence of equal meaning. The original reviewed source must establish
that meaning; a companion cannot declare all roots to measure physiological intake.

`ResolutionMeasurementV1.basis=PLANNED_INGREDIENT_INPUT_V1` retains authored ingredient
quantities and compatible reference-based contributions. `WHOLE_TIER_TO_SINGLE_TRACKED_MEMBER_V1`
binds **planned offered-food attribution**, not actual offering, eating, absorption or
shared-meal allocation. Underlying EP_RAW_G/COOKED_G material/reference bases remain
explicit and distinct from the measured-quantity vocabulary below.

Frozen `synthesis.py::_resolution()` only accepts `TEST_ONLY_RESOLUTION_FIXTURE_V1`.
Frozen `NutritionResolutionHandoffV2` is `UNVERIFIED_TRANSPORT` with
`policy_integration=NOT_AUTHORIZED`. This design changes neither contract nor behavior.

The question answered here is: **does retained, explicitly scoped TEST_ONLY source
evidence authorize treating this exact requirement's measurement meaning as the same
planned-input quantity represented by this independently reconstructed NRE scope?**
It does not answer whether a nutrient amount is healthy, whether a plan meets its roots,
whether portions will be eaten, or whether a solver has a feasible solution.

## 3. Versioned measurement vocabulary

The proposed `measurement-meaning.v1` vocabulary is closed. Tokens describe different
claims; they do not imply conversions or a hierarchy of interchangeable quantities.

| Meaning token | Exact interpretation | V1 positive support |
| --- | --- | --- |
| `PLANNED_INGREDIENT_INPUT_V1` | NRE's complete authored ingredient-input contribution calculation, retaining each ingredient/reference material basis, recipe/tier/rule/configuration witness and planned member/slot scope | Only if original TEST_ONLY source meaning and all exact scope bindings match |
| `PLANNED_OFFERED_FOOD_V1` | Intention to offer a declared food/portion to a member; does not measure actual offered nutrients or prove ingredient-input equivalence | No; serving intent is evidence context only |
| `OBSERVED_OFFERED_FOOD_V1` | A source-protocol-specific observation of food actually offered, with an independently defined measurement procedure | No; no observation source is implemented here |
| `OBSERVED_CONSUMED_FOOD_V1` | A source-protocol-specific observation of food actually consumed by the exact member, distinct from offer, attendance or leftovers assumptions | No; no consumption source is implemented here |
| `PHYSIOLOGICAL_INTAKE_V1` | A physiological quantity whose precise meaning and measurement protocol must be supplied by an independently qualified source; the token alone does not decide ingested versus absorbed quantity | No; an unspecified physiological protocol is not an interpretable comparison quantity |
| `UNSPECIFIED_V1` | Source meaning is absent or cannot be represented by this closed version | No; never an unrestricted or neutral basis |

Unknown version/token is UNSUPPORTED. V1 rejects physiological-intake, cooked-retention,
yield/loss, consumed/offered, absorbed/ingested, AP/EP, food-basis and unit conversions,
including a proposed `IDENTITY`, zero-loss, 100%-retention or caller-authored coefficient.
No converter field, formula interpreter, numeric conversion coefficient or transformed
nutrient value belongs in this companion.

For the supported token, meaning identity also includes a closed interpretation ID/version,
the NRE estimator/contract versions, exact material-basis/reference manifest and original
source meaning preimages. Matching the top-level token alone is insufficient. Unsupported
tokens are retained as explicit diagnostics, never accepted as positive measurement evidence.

## 4. Ownership, authority and evidence

| Owner / actor | Owns or may do | Does not gain |
| --- | --- | --- |
| Nutrition domain | Closed vocabulary, source-bound interpretation contract, pure producer and fixture-source semantics | Scientific qualification or publication rights merely from owning code |
| Trusted test-harness maintainer | Author an immutable isolated fixture registry and its synthetic principal/capability history | Production guideline, clinical, eligibility or qualification authority |
| Synthetic fixture reviewer / publisher | Distinct TEST_ONLY review and publication duties, exact body/protocol/evidence scope | Verified-human or qualified-clinician status |
| Planning | Compose existing authenticated NRE capture with the exact server-selected basis fixture snapshot | Author scientific meaning, widen member scope or select a favorable subset |
| Validation | Independently reconstruct authority history, original meanings, required coverage and applicability | Source publication or permission to infer an intake bridge |
| Household / member | Existing physiological truth, goal authorship and request subject, through frozen owners | Global reference publication; OWNER/EDITOR alone grants no basis authorship |
| Future scientific source authority | Must separately establish evidence, qualification, protocol, population, review, publication and withdrawal governance | Any existence or approval claimed by this TEST_ONLY design |

### 4.1 Structural source chosen for V1

The only new source adapter is an **immutable TEST_ONLY fixture artifact registry**,
installed explicitly by the isolated test harness, never by production migrations or
application startup defaults. It has a closed artifact schema and a server-owned registry
identity/generation. It is not a user-upload format, environment variable path, HTTP
endpoint, general provider plugin, or arbitrary filesystem loader.

A future fixture installer may author the artifact in test setup, but the request cannot
register it. A private non-wire context supplied by the harness pins the exact complete
artifact bytes, registry revision, deployment identity and actual isolated database OID/name
already used by NRE. Only this trusted installation path grants the artifact test-source
status. A body hash, a Git SHA, `TEST_ONLY`, reviewer ID or a model-constructed context does
not grant authority. The capture entry rejects contexts not issued by the trusted harness.
No capability is recoverable from a serialized source snapshot or report.

Concretely, the private context is an opaque in-process handle whose object identity and
issuer epoch must be present in the live server-owned issuance registry, with immutable
deployment/database/artifact bindings. Reconstructed objects with identical fields fail.
This protects against untrusted request data, not hostile Python code executing with test
installer privileges. There is no production context factory or request-triggered installer.

The immutable artifact contains a complete finite synthetic journal: principal identity,
scope-specific fixture capabilities, test qualification attestations, reviews, publications,
replacement/withdrawal events and reader admission. A new artifact revision appends history;
the test installer atomically advances its registry frontier. There is no ordinary mutable
command service, online enrollment interface, CAS/idempotency API, SQL grant, or new durable
publication log in this slice. Exact repeated selection of the same retained artifact is
deterministic. Conflicting revision/frontier preimages are rejected rather than merged.

### 4.2 Review, publication and qualification

Fixture capabilities are separate test concepts: `TEST_BASIS_REVIEW`,
`TEST_BASIS_PUBLISH`, `TEST_BASIS_WITHDRAW`, `TEST_BASIS_SOURCE_READ`.
Only the privileged test installer may enroll synthetic principals or author grants.
Existing Root/NPS, Catalog, Preferences and Household grants confer none of these rights.

A publication requires a complete review over exactly the body, meaning anchors, evidence
manifest, protocol/version, population/scope, effective interval and environment. Reviewer
and publisher must have different synthetic **principal-subject identities**; two login
aliases for one identity do not satisfy separation. Both must possess their exact scoped
capability and a current test qualification at the publication cut. Qualification is
explicitly `SYMBOLIC_TEST_ONLY_NOT_SCIENTIFIC`, never a claim about a real human.
Changed content/evidence/scope requires a new review and publication revision.

Journal events have unique identity, monotonically increasing sequence, preceding-event
identity/hash, recorded time and effective interval. Capabilities, qualification scope,
author identity and review binding are replayed from retained preimages. PUBLISH,
SUPERSEDE, RETIRE and WITHDRAW append events; UPDATE/DELETE or an edited old artifact body
is invalid. There is no latest/provider fallback or aggregation of competing assertions.
An explicit selected revision must resolve uniquely and cover the complete requested scope.

### 4.3 Original source meaning cannot be rewritten

Each positive assertion must point to measurement meaning **already authored inside the
exact original guideline/rule evidence**. New positive TEST_ONLY fixtures may use the
existing free-form retained evidence bodies to carry a closed
`test-only.measurement-meaning.v1` preimage, reviewed before their original publication.
No frozen contract fields, old fixtures, source histories or exported hashes are edited.

This preimage declares the exact claim anchor, meaning ID/version, planned-input token,
material/reference basis scope and TEST_ONLY environment. The companion's review must
reference those exact preimages, not supply a new interpretation in place of them. A legacy
root/rule with absent meaning stays UNAVAILABLE; an opaque clinical text cannot be parsed
or relabeled as planned-input authority. A fixture saying physiological intake cannot be
overridden to planned ingredient input by an external assertion.

Clinical publication would require qualified real actors, reviewed scientific evidence,
an independently approved applicability protocol, actual jurisdiction/population scope,
effective-time and withdrawal governance, and authenticated source capture. None exists by
virtue of this fixture model. Those are separate production blockers, not seeded records.

## 5. Additive contracts and small interface

All names below are proposed new definitions, not additions to the current 503 exports.
They live in a Nutrition-owned companion; they do not subclass or amend frozen Root/NPS/NRE
models. Cross-context imports remain exact, additive and subject to import-guard review.

| Proposed carrier | Required semantic payload |
| --- | --- |
| `MeasurementMeaningV1` | Closed meaning token, interpretation ID/version, environment, exact original evidence preimage, material/reference manifest, metric/unit/temporal identity; no amount or converter |
| `BasisClaimAnchorV1` | Exact member; Root result and original guideline revision/body/evidence/protocol; root key or published synthesis rule/case/operation ID and layer; exact output descriptor and declared temporal scope |
| `BasisApplicabilitySourcesV1` | Full retained NRE v2 handoff; freshly reconstructed pre-policy requirement; all required claim anchors; exact selected assertion/publication; complete fixture artifact history/absence witnesses and capture frame |
| `BasisApplicabilityResultV1` | Outcome/reasons, complete required-anchor identity set and comparison witnesses when successful; full source/result identity; explicit non-authority flags; no nutrient value or derived policy |
| `BasisApplicabilityCheckV1` | CONSISTENT/INCONSISTENT, reconstructed identities and findings; retained-semantic coverage only, never authority transferable through a report |
| `BasisApplicabilityHandoffV1` | Complete sources and claimed result, `UNVERIFIED_TRANSPORT`; no detached successful-report admission path |

Nested assertion records retain provider/artifact family, assertion/revision identity,
original meaning anchors, exact subject/population/protocol applicability, scope manifests,
review/publication/qualification evidence, effective interval and immutable lifecycle. They
are source facts, not a new coordinate/mapping framework. Fingerprints use domain-separated
schema-versioned canonical preimages; complete manifests and absence witnesses are included.
Visible positive rows alone are not the source fingerprint.

**Authored selection versus fresh capture binding:** published assertions name stable
original guideline/rule revisions, original evidence preimages, exact member and authored
recipe/reference/slot identities. They do not predict a future Root result fingerprint,
NRE capture fingerprint or capture-bound requirement fingerprint. Selectors carry these
stable identities only. After canonical capture, the adapter constructs distinct bound
`BasisClaimAnchorV1` instances with the actual Root/requirement/NRE cut identities and
proves that every stable authored anchor matches. A caller cannot provide the bound frame
or upgrade a precomputed favorable result into a freshly captured source.

One selected fixture registry/provider revision supplies the complete scope. Its selector
manifest names exactly one assertion revision per required anchor; one assertion may cover
several explicitly authored anchors. Multiple competing matches, overlapping conflicting
publications or cross-provider pooling are rejected, never ranked or aggregated.

The proposed interface has four operations:

```text
capture_test_basis_sources(trusted_context, caller_owned_nre_session, exact_selectors)
resolve_basis_applicability(retained_sources)
check_basis_applicability_independently(retained_sources, claimed_result)
check_basis_handoff_independently(untrusted_handoff)
```

Capture orchestrates the existing frozen NRE capture; it does not accept an untrusted
handoff as freshly captured truth. Selectors name exact existing source/assertion revisions,
member and scope; they cannot provide authority, completeness, qualification or applicability
booleans. Pure resolution/checking receive retained primitives, never a live source callback.

Results explicitly retain:

```text
environment=TEST_ONLY                 scientific_correctness=NOT_CERTIFIED
source_origin=NOT_PROVED_OFFLINE       validation_authority=UNVERIFIED_TRANSPORT
current_authorization=NOT_CLAIMED      hard_policy_feasibility=NOT_EVALUATED
policy_integration=NOT_AUTHORIZED      production_admission=CLOSED
policy_synthesis=NOT_PERFORMED         consumption=NOT_ASSERTED
solver_infeasibility=NOT_PROVEN
planner_ready=False                   activation_ready=False
```

## 6. Pre-policy projection and acyclic architecture

```text
Frozen Root source + frozen published synthesis rule + explicit precision selection
       -> existing NutritionPolicyRequirementSpec (before policy)
       -> companion required-anchor projection from original root/rule metadata

Existing authenticated NRE capture -> frozen finite NRE v2 sources and estimate
       -> fresh Validation-owned NRE reconstruction

Trusted isolated fixture registry + original source meaning preimages
       -> complete retained basis artifact/cut + exact assertion selection

Pre-policy anchors + independently checked NRE primitives + basis source history
       -> Nutrition applicability producer
       -> Validation-owned independent applicability reconstruction
       -> unverified terminal BasisApplicabilityHandoffV1

SEPARATE FUTURE GATE: trusted fresh NRE + basis checks + independently checked v2 policy
       -> MTR-006 policy-integration v2 -> future MTR-008 -> later preview validation
```

The frozen NRE producer does **not** acquire a basis-authority dependency. It may still
report planned-input vectors when basis applicability is unavailable. Successful numeric
policy integration is what requires the additional proof. There is no edge from a completed
NutritionPolicy, final comfort interval, ResolvedPlanPolicy or solver to basis applicability.

The companion reconstructs required anchors from every original hard/reference root in
the retained Root result and every required constraint operation in the exact published
rule case. Operation IDs and frozen rule grammar determine layer, root lineage, descriptor
and temporal scope **without evaluating nutrient values, goal/comfort bounds or selecting
a favorable precision result**. Branches of SELECT_PRECISION_CASE must preserve descriptor
identity; otherwise this version returns UNSUPPORTED. The original requirement fingerprint,
rule body/case, precision source and complete required-claim set are pinned.

The frozen `NutritionPolicyRequirementSpec` is specifically the comfort-resolution
projection (`synthesis.py::_requirements()`), **not** a manifest of every hard, goal and
weekly policy claim. It remains unchanged. The companion therefore retains two distinct
manifests: that exact frozen requirement, and the independently reconstructed complete
root/required-claim anchor set. It must never claim that the first proves the second.

Required derived anchors are metadata about future claims, not supplied NutritionPolicy
claims. A claim may use a corresponding exact NRE root/metric/temporal measurement only
when independently reconstructed lineage and descriptors establish the relation. New or
ambiguous lineage, unsupported instruction/version, missing weekly cells or incompatible
temporal descriptors fail closed. No evaluator of future policy arithmetic is introduced.

For a required anchor not represented by an existing `ResolutionMeasurementV1`, a witness
may name the exact already-retained `NrePeriodVectors` identity and its fixed metric
component (ENERGY/PROTEIN/FAT/CARBOHYDRATE), provided the independent NRE checker has
reconstructed that complete period and original descriptor compatibility is exact. This
is a metadata binding to original joint vectors, not a new measurement/value/gap export.
The companion cannot add a period, sum days, expand the candidate universe or invent a
missing component. Absent required periods yield UNAVAILABLE even if comfort resolution
is AVAILABLE. Positive fixtures must already supply full required periods through the
frozen NRE scope; no frozen estimator or requirement projection is changed to make them pass.

The finite metadata projection has the following closed rules; none propagates scientific
applicability merely because an arithmetic operation preserves units:

| Frozen instruction | Metadata-only treatment |
| --- | --- |
| COPY_REFERENCE | Resolve the exact original root/reference-role descriptor and lineage, retaining its original meaning preimage |
| AFFINE_SAME_UNIT | Retain operand lineage/unit for endpoint metadata; do not evaluate coefficients or assume output meaning without explicit source-authored claim evidence |
| MAKE_CONSTRAINT | Reconstruct operation ID, root key, layer, constraint kind and descriptor from authored metadata; require exact claim meaning |
| FINITE_PERIOD_SUM / REVIEWED_PERIOD_PROJECTION | Reconstruct only declared lineage and output temporal descriptor; require separately authored output-period meaning, never implicit daily/weekly conversion |
| CHECK_SUBSET / CHECK_DIRECTION | Retain relation/operand identities for completeness; do not execute policy containment/direction arithmetic |
| SELECT_PRECISION_CASE | Require compatible descriptors and lineage across all authored branches, pin precision source, and retain metadata without choosing a numeric band |

Repeated/forward/recursive/unknown instructions, malformed arity, incompatible operands or
an output descriptor not uniquely reconstructible by these rules fail closed. A complete
NutritionPolicy can neither supply the missing descriptor nor decide its own applicability.

Nutrition may reuse frozen producer requirement projection. Validation independently
reconstructs requirement and claim metadata from retained Root/rule primitives, using the
existing independent NRE authority reconstruction where appropriate, never Nutrition's
producer projection as its correctness oracle. Shared immutable contracts and canonical
measurement primitives are permitted; shared applicability/projection business logic is not.

This is the terminal measurement-meaning companion for the bounded v2 handoff. A future
integrator consumes the original NRE values/witnesses plus independently established
comparability; it must not create chains of scalar coordinate adapters or reinterpret a
positive result as candidate utility, nutrition safety or production permission.

## 7. Complete applicability semantics

A positive result is `APPLICABLE_TEST_ONLY`, with relation
`SAME_DECLARED_PLANNED_INPUT_MEANING_V1`. It requires **all** of:

1. Fresh trusted capture selected the registered isolated TEST_ONLY artifact and exact
   NRE database/deployment; all retained sources and original meanings are TEST_ONLY.
2. Fresh independent NRE reconstruction agrees, its result is AVAILABLE, and the complete
   root/rule requirement, member, exact finite recipe/tier/rule/configuration and slot scope
   is retained. A serialized NRE CONSISTENT report is ignored as proof.
3. Every required root/derived anchor is reconstructed from original source semantics;
   no missing/duplicate/extra/favorable-subset coverage, cross-member copy or empty vacuous pass.
4. The exact selected assertion has valid review/publication/capability/qualification
   history, unambiguous applicability and complete evidence. Reader admission is current
   at fresh capture. No household membership or unrelated source grant supplies it.
5. Original claim meaning and NRE meaning are both the exact supported planned-input
   interpretation, including original evidence, underlying material/reference basis and
   estimator/version semantics. Metric/unit equality is checked **after meaning**, not
   used to infer meaning. No conversion or missing bound is manufactured.
6. Exact subject, eligibility/scope/protocol, original evidence versions and request
   interval match. The publication/evidence covers the entire interval, and every period's
   calendar/timezone/slot manifest is complete. There is no cross-version horizon stitching.

The result contains witnesses for the entire required-anchor set or none. There is no
partial numeric-use success, confidence score, preferred-source fallback or cross-target
aggregation. It contains no amounts and never checks policy containment arithmetic.

| Outcome | Required reasons / meaning | Numeric policy admission |
| --- | --- | --- |
| `APPLICABLE_TEST_ONLY` | Complete exact same-declared planned-input meaning under isolated fixture authority | Still NOT_AUTHORIZED; future separately reviewed TEST_ONLY v2 consumer only |
| `NOT_APPLICABLE` | Complete authoritative fixture evidence explicitly describes a different quantity/basis | None; not a physiological conflict or solver result |
| `UNAVAILABLE` | Meaning/evidence/qualification/publication/coverage absent; selected publication withdrawn/retired for fresh use; source authority unavailable | None; never zero, safe or unrestricted |
| `UNSUPPORTED` | Unknown vocabulary/protocol/instruction version, any required conversion, shared/consumed/intake interpretation, cross-version interval, unsupported lineage | None; never an identity bridge |
| `REJECTED` | Forged context, bad principal/body/sequence/review binding, conflicting selection, tampered source/version, unit/subject mismatch or contradictory purported coverage | None; no favorable partial witnesses |
| `RESOURCE_EXCEEDED` | Any server-owned byte/structure/work/time cap exceeded | None; all-or-error, no truncation |

Reasons are finite versioned identifiers, including `MEANING_MISSING`,
`EVIDENCE_INCOMPLETE`, `SOURCE_UNQUALIFIED`, `PUBLICATION_WITHDRAWN`,
`READER_REVOKED`, `TEMPORAL_COVERAGE_MISSING`, `POPULATION_SCOPE_MISMATCH`,
`CONVERSION_NOT_SUPPORTED`, `SOURCE_CUT_INCOHERENT`, `REQUIRED_ANCHOR_MISSING`,
`UNIT_MISMATCH`, `ORIGINAL_MEANING_CONTRADICTION`, and `ENVIRONMENT_MISMATCH`.
Scope/population mismatch with otherwise valid evidence is NOT_APPLICABLE; forged identity
or contradictory source binding is REJECTED. Multiple valid alternatives for one explicit
selection are REJECTED as ambiguous; absence is UNAVAILABLE, not a weaker positive result.

## 8. Capture, lifecycle and temporal replay

The Planning-owned additive adapter uses **one actual ordinary clean caller-owned NRE
reader session**, read-only REPEATABLE READ or SERIALIZABLE, with unchanged frozen
Root/NPS/NRE privilege guards. It obtains the canonical Root/rule/recipe/ingredient/serving
cut by the existing protected captures and exact owner reads. No new database capability,
grant, table, role, privileged function or broad schema SELECT is introduced.

The separately trusted artifact registry is not part of PostgreSQL MVCC. Capture pins its
immutable revision and exact bytes before composition and checks that the registry frontier
and reader admission did not change before completion. A change aborts the entire capture;
there is no claimed shared transaction across artifact memory and PostgreSQL. The frame
retains both identities, capture interval and exact scope/original-source anchors. This
proves a bounded coherent composition under the trusted harness, not universal distributed
snapshot semantics. Mutable external files, multiple DB sessions or unprovable cuts are rejected.

Publication and qualification are checked at review/publication cuts and over requested
effective scope. A grant revocation blocks subsequent actions, not a rewrite of a previously
valid publication. An explicit qualification withdrawal makes dependent assertions unusable
for fresh admission; a withdrawn publication or reader authorization also blocks fresh use.
Retained old cuts replay their recorded history and make no current-authorization claim.

Future-effective replacement does not invalidate the current selected revision before its
boundary. A whole request must fit one applicable revision; crossing a replacement boundary
is UNSUPPORTED, not stitched or silently clipped. A retired/withdrawn revision cannot be
freshly admitted after its admission cutoff even for a retrospective request; replay of a
previously retained cut remains possible. Recorded sequence/time and valid/effective interval
are separate. Retrospective correction appends a new revision and cannot alter an old snapshot.

No live lookup, DB, filesystem, network, wall-clock or mutable global source access occurs
inside pure replay or independent checking. Capture supplies explicit times and complete
retained histories/absence witnesses. Request time cannot be silently replaced by now.

## 9. Independent validation and consumer trust

The proposed Validation-owned checker must independently:

1. Parse bounded complete primitive sources; reconstruct original Root/rule and pre-policy
   anchors, member/eligibility/version/temporal bindings and complete required coverage.
2. Invoke the frozen independent NRE checker on original sources/claimed estimate, require
   AVAILABLE retained evidence, and reconstruct measurement interpretation and manifests.
3. Replay the fixture registry's complete source authority, qualification, review and
   publication history; verify original meaning preimages and effective-time selection.
4. Independently decide each exact meaning relation and reconstruct the entire expected
   result and reasons, including non-success and all non-authority flags.
5. Compare the reconstructed result with the claimed one. Rehashed tampering or a forged
   CONSISTENT report cannot short-circuit any step.

It must not import/call the applicability producer, producer projection, eventual policy-v2
business logic, NutritionPolicyEngine, PlanPolicyResolver or solver internals as an oracle.
An additive Validation module may reuse its own frozen independent NRE/Root source checking;
it must not call Nutrition producer semantic validators to decide applicability correctness.

**Offline limitation:** a perfectly self-consistent fabricated retained bundle may satisfy
offline semantic reconstruction; neither its embedded registry anchor nor its fingerprints
prove trusted capture. The checker must label this retained consistency only. Fresh consumer
admission must obtain sources through the private trusted capture path and perform fresh
independent checks; accepting arbitrary wire sources/results/reports as authentication is
forbidden. No serializable `validated=True` or capability token is returned.

Capture establishes authorization at its retained cut, not indefinitely afterward. Future
v2 admission must separately define its live-generation/freshness check before any claim
about current authorization. Retained replay never silently refreshes grants or publication.

A future independently implemented MTR-006 v2 consumer must require both fresh NRE and
basis reconstruction over the same retained inputs and trusted capture origin, then a fresh
independent reconstruction of the **resulting v2 policy**. A valid basis witness alone does
not validate derived hard/goal/comfort bounds, daily safety, weekly semantics or precision.
Frozen MTR-006 v1 is not called with, cast from or taught to accept this handoff.

## 10. Security and absolute structural limits

All limits are server-owned structural design values, **not nutrition/clinical constants**.
They are applied before canonicalization/recursive model construction wherever applicable;
the existing NRE limits remain unchanged and cannot be raised by this companion.

| Limit | Proposed absolute cap / behavior |
| --- | --- |
| Selector ingress | 64 KiB UTF-8; reject duplicate JSON keys and unsupported fields |
| Basis artifact | 2 MiB encoded bytes; never load from a caller-specified path |
| Total retained composition | 32 MiB; embedded NRE still independently limited by its frozen 16 MiB source cap |
| Required anchors / assertions | 128 anchors; 128 selected assertions; reject overflow rather than drop roots |
| Fixture history | 256 events; complete retained history or error |
| Periods / evidence manifest | 32 periods; 256 evidence entries; exact sorted unique identities |
| Parsing | Maximum depth 32; string 100,000 characters; integer bit length 256; no float coercion |
| Pure replay work | 1,000,000 checked operations; no unbounded recursion or candidate cross-product expansion |
| Capture | Combined watchdog 60 seconds; frozen DB statement limits remain in force |
| Producer/checker hosting | Separate server execution budget 10 seconds each; host timeout aborts with no successful partial result |

Pure work counters give deterministic resource outcomes. Host cancellation/timeouts are
operational failure controls, not a claim that wall-time failures reproduce deterministically
offline. Capture/source overflow returns no partial source success; semantic failures retain
diagnostics without favorable partial witnesses. Caller-requested limits can only lower caps.

No public HTTP endpoints are added. These source/semantic caps are not a complete hostile
HTTP ingress defense; server request-body, concurrency and execution controls still belong
to the later Planner API gate. Fixture installation credentials/context must never be
accepted from browser fields, Household roles, user headers or serialized reports.

## 11. Persistence decision and production blockers

**Chosen structural strategy: ZERO NEW POSTGRESQL PERSISTENCE.** The immutable versioned
TEST_ONLY artifact and retained snapshots are sufficient to exercise applicability semantics,
authority reconstruction and negative cases. This does not pretend to provide durable
production source enrollment, verified qualifications or multi-writer publication service.

No 0018, new domain table, protected SQL function, DB role/capability, automatic grant,
production provider/enrollment, qualification, source publication, content or seed is proposed.
The artifact is only explicitly installed in disposable test setup; no default production
registry or fallback artifact is shipped. Original physiological/goal/reference truth stays
with frozen owners; this slice adds no write path to it.

If production or durable authenticated basis publication is later required, return for a
separate source-governance design. It must settle the actual Nutrition scientific source
owner, independently verified qualifications, review/publish/withdraw permissions, exact
population/protocol/evidence authority, immutable retention, concurrency/CAS/idempotency,
reader authorization and independent capture. A PostgreSQL implementation would need its
own forward-migration and protected-role review after authorization; no migration number or
table count is reserved here. Existing unrelated grants cannot be reused by implication.

Unresolved **production** blockers are real: no independently approved scientific evidence
for a planned-input/intake relation, no authorized qualified production reviewers/publishers,
no production applicability/population protocol, and no approved publication/withdrawal source.
The structural design intentionally provides no positive production path around them.
Within this bounded symbolic TEST_ONLY strategy there is no unresolved numerical-content
requirement. If implementation needs a scientific bridge or new durable authority, STOP.

## 12. Acceptance matrix — future implementation obligations

Namespace **MBA001–MBA080**, all mandatory in a separately authorized implementation.
**12 real PostgreSQL obligations (MBA001–MBA012)** exercise the composed existing protected
NRE source path; **68 pure/adversarial/compatibility obligations (MBA013–MBA080)** exercise
the new immutable artifact and independent semantics. Parameterization may increase executed
counts. None of these tests exists or is claimed executed by this docs-only PR.

PG obligations require actual PostgreSQL/authenticated sessions, existing protected source
functions and canonical owner reads; mocks/collection cannot satisfy them. They do not
claim a new PostgreSQL basis-authority implementation.

| ID | Class | Required independent expected behavior |
| --- | --- | --- |
| MBA001 | PG | Authenticated ordinary NRE reader plus registered isolated artifact yields complete sources without new privileges |
| MBA002 | PG | Actual DB OID/name or deployment mismatch rejects fixture context, despite matching caller labels |
| MBA003 | PG | Wrong login/SET ROLE/shared actor spoof cannot satisfy existing protected Root/NPS reader identity |
| MBA004 | PG | Revoke existing reader permission on another connection; subsequent fresh composition fails, old retained cut remains replayable |
| MBA005 | PG | Concurrent canonical recipe/reference change cannot mix before/after values in one retained NRE cut |
| MBA006 | PG | Missing canonical recipe/tier/rule/reference/serving row is not replaced by fixture manifest assertions |
| MBA007 | PG | Cross-member/household request and non-authorized membership fail through real source reads |
| MBA008 | PG | Writable/dirty/routed/multi-session or schema-translated source capture remains rejected by frozen NRE guards |
| MBA009 | PG | Changed original guideline/rule/evidence revision invalidates an assertion pinned to the previous source cut |
| MBA010 | PG | Registry frontier/reader admission changed during real DB capture aborts whole composition; no common-MVCC claim |
| MBA011 | PG | Fresh installation remains 0017/108 with no new source grants, basis rows, providers, qualifications or production content |
| MBA012 | PG | End-to-end real canonical capture and fresh independent NRE/basis checks reject a forged positive report with matching public hashes |
| MBA013 | Pure | Exact authored planned-input original meaning and complete same-scope assertion gives APPLICABLE_TEST_ONLY |
| MBA014 | Pure | Token equality without original interpretation/version/material preimages is not positive |
| MBA015 | Pure | Planned offered intent is distinct from planned ingredient-input contributions |
| MBA016 | Pure | Observed offered food is unsupported without an observation source, never inferred from planning |
| MBA017 | Pure | Actual consumption cannot be inferred from offering/attendance/elapsed time |
| MBA018 | Pure | Physiological intake with absent or supplied unapproved protocol remains unsupported |
| MBA019 | Pure | Ingested and absorbed interpretations cannot be silently equated |
| MBA020 | Pure | Unknown meaning/version yields UNSUPPORTED, never permissive fallback |
| MBA021 | Pure | Missing original root meaning yields UNAVAILABLE, including legacy TEST_ONLY fixtures |
| MBA022 | Pure | Companion cannot contradict or replace original physiological meaning with planned-input meaning |
| MBA023 | Pure | Wrong guideline provider/revision/body/evidence/protocol anchor rejects |
| MBA024 | Pure | Wrong rule provider/body/case/operation/layer anchor rejects |
| MBA025 | Pure | Exact subject identity required; no copied member/Household aggregate applicability |
| MBA026 | Pure | Valid evidence with wrong population/supported scope is NOT_APPLICABLE |
| MBA027 | Pure | Unqualified source/absent qualification produces no positive result |
| MBA028 | Pure | Reviewer/publisher missing exact scoped fixture capability cannot publish |
| MBA029 | Pure | Same principal-subject under different login aliases cannot review and publish |
| MBA030 | Pure | Changed body/evidence/protocol after review requires a new exact review |
| MBA031 | Pure | Root/NPS/Catalog/Household grants cannot become basis capabilities |
| MBA032 | Pure | A Git hash, reviewer string or REVIEWED label cannot enroll a fixture source |
| MBA033 | Pure | Duplicate/edited/reordered/missing journal event or wrong predecessor rejects |
| MBA034 | Pure | Complete append-only publication and exact repeated retained selection replay deterministically |
| MBA035 | Pure | Withdrawn publication blocks fresh applicability; old retained replay makes no current claim |
| MBA036 | Pure | Retired revision beyond admission cutoff blocks retrospective fresh admission |
| MBA037 | Pure | Future-effective replacement preserves pre-boundary current semantics |
| MBA038 | Pure | Cross-version request interval is unsupported; never stitched/clipped |
| MBA039 | Pure | Retrospective correction cannot mutate an older retained snapshot |
| MBA040 | Pure | Capability revocation blocks later publication actions without rewriting prior recorded events |
| MBA041 | Pure | Qualification withdrawal blocks dependent fresh applicability |
| MBA042 | Pure | Missing/ambiguous explicit assertion selection has no latest/provider fallback |
| MBA043 | Pure | Exact period ID/calendar/timezone/effective interval required |
| MBA044 | Pure | Daily/weekly metric/unit coincidence cannot substitute temporal semantics |
| MBA045 | Pure | Unit or metric mismatch rejects before any policy comparison |
| MBA046 | Pure | AP/EP/raw/cooked/reference material-basis mismatch cannot be an identity bridge |
| MBA047 | Pure | Retention/yield/loss/absorption coefficient or converter field is unsupported |
| MBA048 | Pure | Shared/fractional serving or inferred member portion is unsupported |
| MBA049 | Pure | Root/rule/precision/requirement fingerprint pins are recomputed from complete primitives |
| MBA050 | Pure | Comfort-only frozen requirement is distinct from the complete anchor manifest; hard/goal/weekly anchors need existing exact period/component coverage |
| MBA051 | Pure | Ambiguous lineage/unsupported instruction/version/precision descriptor divergence fails closed |
| MBA052 | Pure | No completed NutritionPolicy/ResolvedPlanPolicy is required or accepted as source truth |
| MBA053 | Pure | Missing, extra, duplicate or favorable-subset anchors prevent whole-result success |
| MBA054 | Pure | Missing slot/period/configuration coverage cannot become zero or unrestricted |
| MBA055 | Pure | NRE AVAILABLE and fresh independent consistency are both required for a positive result |
| MBA056 | Pure | Forged NRE CONSISTENT report cannot replace fresh reconstruction |
| MBA057 | Pure | Forged basis APPLICABLE/CONSISTENT labels with matching fingerprints cannot replace checks |
| MBA058 | Pure | Rehashed meaning/source/coverage mutation is caught by independent semantic reconstruction |
| MBA059 | Pure | Self-consistent fabricated offline source may be retained-consistent but cannot prove trusted origin/admission |
| MBA060 | Pure | Serialized context/authority stamp/report cannot be used as private harness capture credentials |
| MBA061 | Pure | Producer/cache-constructed result is fully recomputed, including every non-authority flag |
| MBA062 | Pure | Validation imports no applicability producer/projection, solver or future v2 producer oracle |
| MBA063 | Pure | Fixture qualification never claims real human/scientific authority |
| MBA064 | Pure | TEST_ONLY relabeling to production/mixed environment is rejected |
| MBA065 | Pure | No fixture registry/default artifact exists in production deployment behavior |
| MBA066 | Pure | Source fingerprints retain full artifact history, scopes and absences, not only positive rows |
| MBA067 | Pure | Request/body byte and duplicate-key limits apply before recursive parsing |
| MBA068 | Pure | Depth/string/integer/manifest/history/anchor caps are server-owned; caller cannot raise them |
| MBA069 | Pure | Work overflow produces RESOURCE_EXCEEDED with no partial positive witnesses |
| MBA070 | Pure | Host timeout/cancellation returns no success; pure replay uses no wall clock |
| MBA071 | Pure | Pure producer/checker perform no DB/network/filesystem/live source/global policy lookup |
| MBA072 | Pure | No numeric converter, transformed amount, nutrient target or production constant is exposed |
| MBA073 | Pure | Hard/goal constraints and original reference-center semantics remain untouched |
| MBA074 | Pure | NutritionPrecision/cost/budget/effort/TasteFit cannot mint meaning or widen protection |
| MBA075 | Pure | Maximum gap/GCD/exact NRE values do not constitute policy or solver feasibility |
| MBA076 | Pure | Handoff remains UNVERIFIED_TRANSPORT; consumer cannot use a detached report as validation proof |
| MBA077 | Pure | Frozen Root/NPS v1/NRE exported definitions, files, accepted behavior and 4,047 baseline tests retained |
| MBA078 | Pure | Existing 503 definition hashes unchanged; any future additive definitions explicitly inventoried |
| MBA079 | Pure | No migration0018/persistence/SQL role/grant/production seed added by the structural implementation |
| MBA080 | Pure | planner/activation False, production CLOSED, no full-parent completion or downstream authorization |

## 13. Compatibility, downstream prerequisites and design verdict

The present PR is **five Markdown files only**: this design plus synchronized BACKLOG,
FOUNDATION_STATUS and both implementation blueprints. No runtime, contracts, tests,
tooling/CI, migrations, schema, permissions or data are modified. Keep the PR OPEN with
auto-merge OFF for independent architecture review. Do not self-approve or merge it.

A separately authorized structural implementation must retain all 4,047 tests / 0 skips,
all 503 existing definition bodies/hashes, frozen source behavior and migration0017/108;
execute MBA001–MBA080 including the 12 real PG obligations; inventory any additive exports;
and run complete Python/web/architecture/import/export/SCRAM/TLS/benchmark/client guards.
No production scientific applicability claim or v2 policy integration may be bundled with it.

Future MTR-006 policy-integration v2 still needs its own detailed design and authorization:
trusted fresh NRE capture/checking, this companion's independently reconstructed complete
basis evidence, a separately versioned producer, and independently reconstructed policy
semantics/containment. Hard roots, goal protection, daily safety, weekly centering and
NutritionPrecision must each remain explicit. No largest-gap fixture cast is permitted.
Full MTR-008 separately owns plan-policy axes/default/override precedence and cannot supply
missing nutrition measurement meaning or scientific authority.

**SOURCE-BOUND MEASUREMENT-BASIS APPLICABILITY & INDEPENDENT EVIDENCE CONTAINMENT**

**BOUNDED STRUCTURAL / TEST_ONLY DESIGN READY FOR INDEPENDENT ARCHITECTURE REVIEW.**

**IMPLEMENTATION NOT AUTHORIZED. PRODUCTION NUTRITION/CLINICAL CONTENT GATE CLOSED.**

Nutrition Root, MTR-006 synthesis and MTR-007 estimator structural foundations remain
FROZEN. Full MTR-006/007/008 remain INCOMPLETE and parent issues OPEN. Planner/activation
False; Execution NOT STARTED; PRECOMMIT FAIL-CLOSED. No downstream work starts here.
