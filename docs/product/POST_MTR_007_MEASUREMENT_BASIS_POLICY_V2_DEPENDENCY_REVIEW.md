# Post-MTR-007 Structural Freeze — Measurement-Basis Applicability vs MTR-006 Policy Integration v2

**DOCUMENTATION-ONLY DEPENDENCY / ARCHITECTURE PROPOSAL — NOT YET INDEPENDENTLY APPROVED.**
**NOT A CLINICAL EVIDENCE REVIEW, POLICY-INTEGRATION DESIGN, IMPLEMENTATION AUTHORIZATION OR PRODUCTION GATE OPENING.**

## 1. Canonical identity, evidence and requested decision

| Gate | Current verified record |
| --- | --- |
| Exact merged main at review | `82b4a7c631acbc04ffbd522702bf3529d7e2e2d2` |
| MTR-007 approved structural design | [PR #129](https://github.com/thedusk4203/Menuto/pull/129); [architecture PASS 6655233374](https://github.com/thedusk4203/Menuto/pull/129#issuecomment-6655233374) |
| MTR-007 bounded structural implementation | [PR #130](https://github.com/thedusk4203/Menuto/pull/130); [independent implementation PASS 6660975134](https://github.com/thedusk4203/Menuto/pull/130#issuecomment-6660975134); [structural freeze 6662354375](https://github.com/thedusk4203/Menuto/pull/130#issuecomment-6662354375) |
| Exact merged-main post-freeze CI | [42050943839 — SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/42050943839): event=push, actual merged main SHA above |
| Frozen footprint | 4,047 passed / 0 skips = 3,912 retained + 135 NRE; 36 real PostgreSQL executions / 20 NRE PG obligations; SCRAM/TLS 16/16, benchmark 22/22, client 10/10 |
| Compatibility | 503 exported schema definitions = 480 old definitions/hash bodies unchanged + 23 NRE additions; schema migration 0017 / 108 domain tables; no 0018, no new persistence |
| Production evidence | Fresh-install new production clinical/nutrition content, providers, qualifications, publications, seeds and defaults zero; NOT an audit of a live production DB |
| Parent issues | [MTR-006 #5](https://github.com/thedusk4203/Menuto/issues/5), [MTR-007 #6](https://github.com/thedusk4203/Menuto/issues/6), [MTR-008 #7](https://github.com/thedusk4203/Menuto/issues/7): OPEN, full acceptance incomplete |

**Requested decision:** which *bounded design gate* precedes successful MTR-006 canonical
policy-integration v2: a source-bound measurement-basis applicability / evidence-admission
contract, or the additive v2 policy producer and independent checker? The proposed ordering
below is a **capability dependency**, not a calendar commitment.

Canonical specifications: [Development Spec V1.3 §§8.1, 8.3, 10.3–10.4](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[ADR-002](../adr/ADR-002-nutrition-policy-engine.md),
[ADR-003](../adr/ADR-003-plan-policy-resolution.md),
[ADR-010](../adr/ADR-010-independent-validator.md),
[Architecture Invariants](../ARCHITECTURE_INVARIANTS.md),
[approved MTR-006 bounded design](MTR_006_SOURCE_BOUND_NUTRITION_POLICY_SYNTHESIS_CONTAINMENT_DESIGN.md),
[approved MTR-007 bounded design](MTR_007_SOURCE_BOUND_NUTRITION_RESOLUTION_ESTIMATOR_DESIGN.md),
[MTR-007 structural evidence](MTR_007_SOURCE_BOUND_NUTRITION_RESOLUTION_ESTIMATOR_EVIDENCE.md),
and the [previous dependency gate](POST_MTR_006_SYNTHESIS_RESOLUTION_PLAN_POLICY_DEPENDENCY_REVIEW.md).

## 2. Concrete frozen-code evidence — two dimensions that are not interchangeable

| Exact code | Verified retained capability | What it does not establish |
| --- | --- | --- |
| [Root descriptor](../../apps/backend/app/modules/nutrition/root_contracts.py) `NutritionRootDescriptor` | Pins metric, unit, source scope/version, protocol fingerprint and exact temporal scope. Units are KCAL for ENERGY and G for others. | No declared intake/consumed/planned-input measurement-basis semantics or reviewed cross-basis applicability is encoded in this descriptor. Its clinical meaning cannot be inferred from equal metric/unit. |
| [Synthesis source/requirement contracts](../../apps/backend/app/modules/nutrition/synthesis_contracts.py) | `NutritionPolicyRequirementSpec` is available pre-policy; frozen `NutritionResolutionInput` contains TEST_ONLY portion_step/expected_step fixture facts and `NutritionPolicy` v1 contracts. | No canonical NRE v2 source, finite set or basis authority is accepted by the frozen v1 policy producer/checker. |
| [Frozen MTR-006 producer](../../apps/backend/app/modules/nutrition/synthesis.py) `_resolution()` | Requires exact `TEST_ONLY_RESOLUTION_FIXTURE_V1` / `TEST_ONLY_fixture_v1` with fixture step equality and comfort-width guard; `admit_production_nutrition_policy()` rejects production admission. | Cannot accept `NutritionResolutionHandoffV2` or equate an exact finite set's maximum gap with a fixture portion step. |
| [NRE contract](../../apps/backend/app/modules/nutrition/resolution_contracts.py) `ResolutionMeasurementV1` | Explicit `PLANNED_INGREDIENT_INPUT_V1`, member/requirement/root/temporal scope, finite exact value sets, gaps and witnesses. `NutritionResolutionEstimateV1` has `policy_synthesis=NOT_PERFORMED` and clinical/feasibility non-claims. | Not food actually eaten, physiologically absorbed nutrients, proven cooked nutrient retention, shared allocation, or an assessment that roots may be measured using planned offered input. |
| [NRE producer and capture](../../apps/backend/app/modules/nutrition/resolution_estimator.py), [Planning source capture](../../apps/backend/app/modules/planning/nutrition_resolution_capture.py) | Complete declared, bounded recipe/tier/rule/slot scopes, trusted isolated TEST_ONLY snapshot, exact rational joint vector arithmetic; only `WHOLE_TIER_TO_SINGLE_TRACKED_MEMBER_V1` planned offering. | No production source/clinical authority, current use of untrusted serialized reports, full consumption or complete nutritional feasibility. |
| [Independent NRE verifier](../../apps/backend/app/modules/validation/nutrition_resolution.py), [authority replay](../../apps/backend/app/modules/validation/nutrition_resolution_authority.py) | Rebuilds retained source authority, requirement identities, culinary selections, vectors and gaps separately from the producer. | `CONSISTENT` establishes retained semantic agreement, not a clinically approved input-to-intake bridge, current production database origin, or production permission. |
| [Terminal NRE public handoff](../../apps/backend/app/modules/nutrition/resolution_public.py) | `NutritionResolutionHandoffV2` retains full unverified sources and estimate with `UNVERIFIED_TRANSPORT`, `policy_integration=NOT_AUTHORIZED`, `production_admission=CLOSED`. | No v2 MTR-006 policy assembler/checker or MTR-008 consumer exists by this handoff alone. |
| [Frozen Validation-owned policy reference](../../apps/backend/app/modules/validation/nutrition_policy.py) | Fresh v1 independent policy reconstruction and reference revalidation; detached caller-supplied CONSISTENT report is not an attestation. | No independent v2 checker for joint finite NRE + explicit source-qualified measurement-basis applicability. |
| [Policy foundation](../../apps/backend/app/modules/policy/contracts.py) | `ValidationCoveragePolicySnapshot.definition=FOUNDATION_NO_CLINICAL_POLICY`. | No full MTR-008 defaults/week/override precedence or versioned `ResolvedPlanPolicy`. |

**Architectural mismatch is substantive, not a missing field spelling:** the
`NutritionRootDescriptor` has no explicit quantity-interpretation basis. The NRE v2
numerics are explicitly *planned ingredient-input* contributions. Their values happen
to share energy/protein/fat/carbohydrate metric and KCAL/G units with some root descriptors,
but exact metric/unit/time equality never establishes the same physiological quantity.
Do not silently declare all root constraints to be intake-based either: the meaning of each
root/derived claim needs source-authorized interpretation evidence.

Also distinguish **four authority layers**: (1) root/rule publication and member
eligibility, (2) authenticated Catalog/Recipe/Planning source cut and independent finite
resolution checking, (3) scientifically reviewed **basis-applicability and any necessary
conversion** with its own named owner, and (4) independent final policy semantics and
subsequent plan/clinical admission. A successful check in one layer never certifies another.
A Git SHA, REVIEWED Catalog status, `REVIEWED_PRODUCTION` label, complete fixture manifest
or a `CONSISTENT` verifier report cannot mint layer (3).

## 3. Decision — the next bounded design gate

| Option | Capability dependency | Review decision |
| --- | --- | --- |
| **A. Source-Bound Measurement-Basis Applicability & Evidence Containment — BOUNDED DETAILED DESIGN** | Defines what it would mean for an exact root/derived policy measurement to be comparable with a planned-input NRE measurement and how to prove/reject the claimed applicability independently. No clinical facts are approved merely by typing a contract. | **SELECT AS NEXT DESIGN GATE**, subject to separate independent architecture review, merge gate and explicit design-start authorization. |
| B. Full MTR-006 policy-integration v2 producer/checker | Needs a trustworthy answer to whether a particular `ResolutionMeasurementV1` represents the same measured quantity as a root/derived claim before any comfort-band or numeric admission. No such answer exists in frozen contracts. | **NOT FIRST SUCCESSFUL INTEGRATION GATE.** A contract-only fail-closed interface sketch can be developed in parallel after scoping; numerical admission and implementation stay blocked. |
| C. Production scientific/qualification/evidence authority | The product needs qualified source review, approved guideline and population semantics, actual evidence for planned→intake applicability or reviewed transformation, and publication/withdrawal lifecycle. | **SEPARATE EXTERNAL/CONTENT TRACK — CLOSED.** Mandatory before any supported production policy, not a reason to invent a clinical bridge in structural code. |
| D. Full MTR-008 PlanPolicyResolver | Requires a separately independently checked NutritionPolicy and distinct Policy-owned precision/default/override, cost, effort and budget sources. | **LATER.** Upstream explicit `NutritionPrecision` selection still precedes NutritionPolicy; compiled ResolvedPlanPolicy remains downstream. |

The word **authority** in option A names the *source-bound proof/admission contract*
that must be designed. It does **not** mean the repo currently possesses the medical,
scientific, reviewer or publication authority to accept production basis statements.
No design-only or TEST_ONLY artifact can close production track C.

## 4. Acyclic capability and evidence DAG

```text
FROZEN Root guideline/goal/scope + published MTR-006 rule + member assessment
    -> NutritionPolicyRequirementSpec (pre-policy projection)
       + source-qualified measurement meaning for each root/derived requirement
       + exact NRE source cut and complete declared member/slot/period scope
    -> FROZEN MTR-007 NRE v2: exact joint reachable planned-input values and witnesses
    -> fresh Validation-owned retained NRE consistency check

Separately reviewed scientific / measurement-basis interpretation authority
    -> source-bound applicability decision (per exact source, metric, unit, basis,
       subject, temporal scope and scope/population), with independent replay
    -> only if legitimately comparable: permitted numeric comparison input

Fresh NRE check + verified applicability (and exact root/rule/precision inputs)
    -> separately authorized additive MTR-006 policy integration v2
    -> fresh independent v2 policy/containment verification
    -> future downstream MTR-008 ResolvedPlanPolicy compiler
    -> future feasibility/solver/complete preview validator

Production clinical/content/eligibility qualification & publication gate: CLOSED.
```

There is **no cycle**: applicability can be designed against the *pre-policy*
`NutritionPolicyRequirementSpec` and `NutritionRootDescriptor` plus the NRE measurement
scope, without requiring a completed NutritionPolicy or ResolvedPlanPolicy. Upstream
Policy-owned authenticated `NutritionPrecision` selection remains separate from downstream
MTR-008 policy compilation. A v2 integrator must never evaluate its own basis statement
as validated merely because it constructed the output.

## 5. Mandatory acceptance questions for the next design (not implementation claims)

1. **Exact meaning and ownership.** Define a closed, versioned vocabulary for
   root/derived claim measurement interpretation versus NRE `PLANNED_INGREDIENT_INPUT_V1`,
   and identify the authoritative source owner and independent reviewer. Preserve the
   frozen Root descriptor and NRE 503-export identities; use a separately versioned
   additive companion/claim rather than retroactively changing the root descriptor.
2. **No implicit identity conversion.** Matching ENERGY/KCAL or PROTEIN/G, root key,
   source scope, period or recipe identity is necessary for a comparison but not sufficient.
   Document exact supported/no-bridge cases: EP_RAW vs COOKED, cooking retention/yield,
   measured offered vs consumed, shared/fractional portions, losses, leftovers,
   preparation and absorption. An unreviewed transformation cannot be an `IDENTITY`
   bridge or an invented zero/100% coefficient.
3. **Source-bound clinical applicability.** Any claimed comparable or transformed basis
   must name its source evidence, scientific protocol/version, exact scope/population,
   jurisdiction if applicable, effective interval, reviewer/qualification and publication/
   withdrawal authority; these require a separately approved source/governance design
   if absent. No owner is silently inferred from existing Root/NPS or Catalog grants.
4. **Independent verifier and consumers.** Define a new Validation-owned checker for
   basis source identity, qualification, applicability, temporal coverage, conversions
   and non-authority. It must be independent of producer summaries, stamps, rehashed
   fingerprints, published `CONSISTENT` text and any eventual policy integrator. Offline
   replay consistency does not prove current DB origin or source publication; fresh
   consumer admission must use trusted capture and fresh validation.
5. **Complete subject/time basis.** Match root/rule/case/requirement/subject, member serving
   mapping, measurement metric/unit, period/calendar/timezone and source version. A
   planned offered whole-tier input for one member is not a consumed-intake measurement.
   Day/week aggregation requires independently approved semantics, not unit coincidence
   or reusing a root numeric bound in a different temporal basis.
6. **Explicit typed failures.** Unknown basis, absent applicability evidence, withdrawn
   authorization, unmatched interval/population, unsupported shared allocation, unapproved
   retention/conversion or incomplete source scope must produce deterministic non-success
   and **no numerical policy admission**. Do not relabel them as hard physiological
   conflict, solver-proven infeasibility, safe clinical tolerance, or all-zero intake.
7. **TEST_ONLY containment.** Structural contracts can specify negative tests, a
   deliberately isolated symbolic TEST_ONLY case and non-admission behavior. TEST_ONLY
   synthetic comparability is never a scientific production source, cannot be promoted
   through `REVIEWED_PRODUCTION` labels or hashes, and may not open clinical-content
   or eligibility gates. Do not introduce clinical numerical constants in fixtures as
   implicit production defaults.
8. **Bounded data and authorization.** State whether an immutable retained basis assertion
   and fresh independent checker are sufficient for a TEST_ONLY structural slice, or
   whether actual source enrollment/publication requires new protected PostgreSQL
   owner/journal/grant machinery. Such a DB/authority design would require its **own
   separate authorization and forward-migration review**; do not presume migration
   0018 or modify any frozen SQL/role/reader privileges.
9. **No source-content circularity.** The basis-eligibility checker consumes pre-policy
   requirements and original reviewed source evidence; it never depends on the final
   nutrition-policy comfort band/claimed applicability verdict. Future integration
   consumes the checker output, not vice versa.
10. **Future v2 integration seam.** Spell out a separate `NutritionPolicy v2` or
    additive versioned producer/checker contract that accepts a complete retained NRE v2
    handoff only after fresh independent resolution and basis admission. Preserve v1
    `TEST_ONLY_fixture_v1` *unchanged*. Compare supported **exact reachable values and
    joint witnesses** against separately authorized soft bands; maximum gap or GCD is
    diagnostic only. Retain all hard/goal constraints; do not claim solver feasibility.
11. **Testing, reproducibility and compatibility.** The next detailed design should propose
    enumerated positive/negative/adversarial cases, mutation tests, explicit real-PostgreSQL
    obligations *only if* new authority reads warrant them, resource/time bounds, exact
    source/version pins and all-or-error semantics. Tests are **not** claimed implemented.
    Preserve 4,047 baseline tests /0 skips, all 503 frozen exported definition hashes,
    schema 0017/108 until separately authorized additive changes; no old migrations or
    frozen files may be rewritten.
12. **Product boundary.** No PlanPolicyResolver defaults, per-week overrides,
    CostPreference/KitchenEffort/BudgetContract, economic solver, MTR-021/022/025/026,
    active plan, Execution or PRECOMMIT route is part of the proposed next design.

A crucial **design stop question** is whether an existing authenticated source can
supply reviewed basis-applicability semantics *without* inventing medical interpretation.
If not, specify a separate source-governance gate and leave all positive basis admission
unavailable. Merely creating a Pydantic model that says `APPROVED` does not resolve it.

## 6. Policy-integration v2 prerequisites and hard stop points

A future separately scoped integration design cannot claim readiness for successful
numeric policy admission until all these are explicit:

- Frozen NRE handoff source/requirements/scope is freshly independently checked and
  `AVAILABLE`; `UNVERIFIED_TRANSPORT` is never an admission token.
- Basis applicability for the exact root/derived policy measurement is separately
  source-authorized **and independently validated**; absent or incomparable means
  UNSUPPORTED/UNAVAILABLE with no accepted numeric policy claim.
- The specific root/rule purpose, case, protections, precision source, member and
  interval are coherent; policy integration does not broaden hard/goal bounds, infer
  NRE `portion_step`, or promote source-data REVIEWED to clinical qualification.
- A separately versioned Nutrition producer and independent Validation v2 reconstruction
  exist; frozen `synthesis.py::_resolution()` and frozen v1 independent checker remain
  byte/semantic unchanged. Future policy references remain unverified wire transports
  requiring fresh checks.
- Full MTR-008 remains a later independent gate, and cannot confer missing Nutrition
  source authority by selecting defaults/week/override or BudgetPressure.

A design for a **fail-closed-only v2 transport** may occur in parallel, but a successful
`AVAILABLE` policy pathway cannot be implemented or approved on unverifiable basis
assertions. If no reviewed bridge is possible within the selected scope, STOP instead of
inventing intake transformations or weakening frozen hard/goal protection.

## 7. Exact disposition / non-authorizations

**NEXT RECOMMENDED GATE: SOURCE-BOUND MEASUREMENT-BASIS APPLICABILITY &
INDEPENDENT EVIDENCE CONTAINMENT — BOUNDED DETAILED DESIGN (STRUCTURAL / TEST_ONLY).**

**REVIEW STATUS: PROPOSED — READY FOR INDEPENDENT ARCHITECTURE REVIEW, NOT APPROVED.**

This document records only architecture/dependency ordering. It does not implement or
approve a clinical measurement bridge, an authority provider, a new publication flow,
policy integration v2, migration, runtime code, clinical content or production eligibility.
It does not begin detailed design. Separate exact-head architecture review, separate
merge authorization and merged-main push CI are required before a separate explicit
design-start decision.

Nutrition Root, MTR-006 synthesis and MTR-007 estimator structural foundations:
**FROZEN**. Full MTR-006/007/008 issues OPEN and **INCOMPLETE**. Production
Nutrition/clinical content/qualifications: **CLOSED**. Planner/activation=False;
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED. MTR-040 COMPLETE, MTR-039 OPEN;
full MTR-041/046 PARTIAL; full MTR-020B/021/024 BLOCKED. No downstream work
starts from the mere presence of this review. **STOP.**
