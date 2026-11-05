# Post-MTR-006 Structural Freeze — MTR-007 vs MTR-008 Dependency Review

**DOCUMENTATION-ONLY PROPOSAL — PENDING INDEPENDENT ARCHITECTURE APPROVAL.**
**NO DESIGN, IMPLEMENTATION, CLINICAL CONTENT, MERGE OR DOWNSTREAM WORK AUTHORIZED.**

## 1. Exact canonical entry

| Evidence | Verified baseline / authority limit |
| --- | --- |
| Main at review | 45ed430ff3306939366bf82e232d02054475b360 |
| Structural synthesis implementation | [PR #127](https://github.com/thedusk4203/Menuto/pull/127), reviewed head fa3c63e1706add51de1e43a70a4496d4fd9a7817 |
| Formal structural freeze | [receipt 6649728687](https://github.com/thedusk4203/Menuto/pull/127#issuecomment-6649728687) |
| Actual merged-main push CI | [41963344853 — SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/41963344853) |
| Baseline regression | 3,912 passed / 0 skips; 1,285 PostgreSQL cases including 32 NPS new obligations; SCRAM/TLS 16/16; benchmark 22/22; client 10/10 |
| Export/schema freeze | 480 exports = 447 frozen definition hashes + 33 additive; migration 0017 / 108 domain tables, no 0018 |
| Production authority | Ten new synthesis and 13 root source tables empty on fresh install; zero production nutrition content, qualified actors, providers, publications, seeds and defaults |
| Parent issues | [MTR-006 #5](https://github.com/thedusk4203/Menuto/issues/5), [MTR-007 #6](https://github.com/thedusk4203/Menuto/issues/6), [MTR-008 #7](https://github.com/thedusk4203/Menuto/issues/7) remain OPEN and incomplete |

Frozen source/authority is structural only. Production Nutrition/clinical content gate remains **CLOSED**.
These historical CI results verify the merged baseline, not execution of any future MTR-007 test.
No detailed design is approved by the existence of this review.

Canonical sources: [Development Spec V1.3 §§8.1, 10.3–10.4](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[ADR-002](../adr/ADR-002-nutrition-policy-engine.md),
[ADR-003](../adr/ADR-003-plan-policy-resolution.md),
[approved MTR-006 detailed design](MTR_006_SOURCE_BOUND_NUTRITION_POLICY_SYNTHESIS_CONTAINMENT_DESIGN.md),
[MTR-006 implementation evidence](MTR_006_SOURCE_BOUND_NUTRITION_POLICY_SYNTHESIS_CONTAINMENT_EVIDENCE.md),
and the [pre-synthesis dependency review](POST_NUTRITION_ROOT_PLANNER_CONVERGENCE_REVIEW.md).

## 2. Frozen capability vs still-missing truth

| Inspected source | Actual current behavior | Limitation |
| --- | --- | --- |
| [MTR-006 synthesis](../../apps/backend/app/modules/nutrition/synthesis.py) | Pure NutritionPolicyRequirementSpec can be obtained before final synthesis; source-bound policy needs resolution evidence. | Only explicit TEST_ONLY_RESOLUTION_FIXTURE_V1 is interpreted as estimator input; no canonical MTR-007 estimator/capture/checker. |
| [Synthesis contracts](../../apps/backend/app/modules/nutrition/synthesis_contracts.py) | Typed requirement measurements and NutritionResolutionInput include complete_pool, pool_fingerprint, portion_step, expected_step and source evidence. | A caller-supplied complete_pool assertion and internally equal values do not prove an exhaustive catalog universe or independently derived granularity. Existing fixture semantics are not production authority. |
| [Nutrition resolution](../../apps/backend/app/modules/nutrition/resolution.py) | Exact scaling of one compatible REVIEWED ingredient nutrient reference; sum of ingredient-input nutrition. | Not MTR-007: no comprehensive portion/candidate granularity certificate; not cooked nutrient retention, absorption, per-member meal allocation or a physiological policy. |
| [Recipe contracts](../../apps/backend/app/modules/recipes/contracts.py) | Authored portion tiers, scaling, adjustments, substitutions, version identities, transformation facts. | No complete reachable nutrient-step lattice or independent certification of all supported candidate/serving combinations. |
| [Planning grounding](../../apps/backend/app/modules/planning/grounding.py) and [capture](../../apps/backend/app/modules/planning/grounding_capture.py) | Canonical recipe, catalog references, participants, inventory and retail source binding under a read-only capture. | Grounded input composition is not proof that a consumer can safely achieve a comfort band. Allergen/diet classifications beyond excluded ingredients fail closed. |
| [MTR-020A shortlist](../../apps/backend/app/modules/planning/shortlist.py) | Deterministic bounded shortlist and input/frontier limit errors. | Full MTR-020B remains incomplete. A restricted candidate universe must be exact and complete within its claimed scope; no silent truncation or global-feasibility inference. |
| [Validation-owned policy checker](../../apps/backend/app/modules/validation/nutrition_policy.py) and [Nutrition facade](../../apps/backend/app/modules/nutrition/synthesis_public.py) | Independent policy reconstruction, fresh reference assembly and consumer revalidation; R-127-01 fixed. | NutritionPolicyReference carries UNVERIFIED_TRANSPORT and is not a current-authority, database-origin or scientific certificate. |
| [Policy contracts](../../apps/backend/app/modules/policy/contracts.py) | Only foundational validation coverage contract, FOUNDATION_NO_CLINICAL_POLICY. | Full Policy default/week/override precedence, budget/cost/kitchen resolution and ResolvedPlanPolicy are not implemented. |

Catalog REVIEWED nutrition reference means a source record was reviewed, not that any nutrient
limit, clinical target, population, formula or production safety threshold is approved.

## 3. The acyclic ordering and critical seam

1. Frozen root and synthesis-rule sources produce **NutritionPolicyRequirementSpec** before
   requiring a final NutritionPolicy. This projection contains scoped member, metric/unit/basis,
   rule case, temporal frame and required measurement identities.
2. Canonical catalog/recipe/portion facts and a **finite, fully declared candidate universe**
   combine with the requirement spec. MTR-007 must produce independently verifiable, source-bound
   nutrition-resolution evidence; failure/unknown completeness is a typed non-success state.
3. Frozen MTR-006 then synthesizes NutritionPolicy from that resolution evidence and a separately
   authenticated **explicit NutritionPrecision** selection. REQUEST_EXPLICIT plus isolated
   TEST_ONLY inputs permit structural contract work without full MTR-008 default precedence.
4. Validation independently reconstructs the policy and any serialized policy reference, not
   relying on producer validation or a caller-supplied CONSISTENT report.
5. MTR-008 compiles the **downstream ResolvedPlanPolicy** using a freshly independently validated
   policy reference and separate versioned CostPreference, KitchenEffort, DailyAvailability,
   BudgetContract, and source-authorized user defaults/week/plan overrides; system BudgetPressure
   is distinct and cannot weaken nutrition hard/goal protection.
6. Feasibility, solve and whole-plan validation remain downstream on complete nutrition, safety,
   economics, inventory/material and member-allocation inputs.

Acyclic diagram:

    Frozen Nutrition Root + MTR-006 synthesis-rule authority
      -> NutritionPolicyRequirementSpec
         + exact catalog / recipe / portion / grounded candidate source cut
      -> MTR-007 source-bound estimator + independent resolution checker
         + authenticated explicitly pinned NutritionPrecision (isolated TEST_ONLY path)
      -> MTR-006 immutable NutritionPolicy
      -> Validation-owned fresh independent NutritionPolicy reference check
         + separate approved Policy defaults/week/override, cost, kitchen, budget
      -> MTR-008 versioned ResolvedPlanPolicy
      -> MTR-021/022 and complete independent MTR-025/026 preview checks

**MTR-008 has two sides, not a recursive self-dependency.** Upstream Policy-owned
NutritionPrecision selection precedes MTR-006 synthesis. Downstream MTR-008 compilation
consumes the complete independently checked NutritionPolicy. Future design must specify two
separate stages/identities for this relationship; it must not try to obtain a completed
ResolvedPlanPolicy before it can choose the precision required to build NutritionPolicy.
Explicit pinned request selection is a bounded structural option, not a substitute for
production default/week/override provenance.

A separate production authority track remains mandatory before any real supported
production preview. TEST_ONLY verification cannot publish human nutrition rules, qualified
actor records or approved populations.

## 4. Gate comparison

| Candidate | Design-ready now? | Dependency verdict |
| --- | --- | --- |
| **MTR-007 NutritionResolutionEstimator — bounded detailed design** | **YES.** Frozen requirement projection + catalog/recipe/grounding source primitives exist. | **SELECT.** First missing upstream source-bound estimator evidence for completing NutritionPolicy/feeding MTR-008. Design must still settle real source completeness and finite granularity semantics. |
| Full MTR-008 PlanPolicyResolver runtime | Provenance/precedence contracts can be designed separately, but NutritionPolicy input lacks real estimator evidence; default/week/override source ownership remains open. | Not first full runtime gate. Explicit precision requests let 007 design proceed. Parallel policy source/precedence design may be proposed separately, not assumed implemented. |
| Production guideline/scientific rule/qualifications | No evidence/qualification/content gate approval. | Hard prerequisite for real supported production preview, not a prerequisite to TEST_ONLY structural 007 design. **CLOSED.** |
| Catalog nutrition and allergen/diet source completion | Existing references and excluded-ingredient logic have limited coverage. | Data/safety admission prerequisite for real usage; fail closed when unknown. Do not extend 007 into generic safety-classification or clinical-content authority. |
| Full MTR-020B portfolio pruning | Not complete. | Can defer for a tightly bounded complete MTR-020A survivor scope; overflow must be a resource error, not silent truncation or false infeasibility. |
| Full MTR-006 and MTR-021/022/025/026 | Frozen MTR-006 structural work exists; no solver or validated preview. | Stay incomplete/blocked until separately approved source, resolution, policy and plan-validation prerequisites. |

This is a **capability-dependency ordering**, not a claim about calendar duration.
Scientific qualification or operational source review may take longer and requires its
own explicit owner and authority.

## 5. Mandatory MTR-007 detailed-design deliverables

1. Exact scope: one tracked nutrition member, finite horizon, required metric/unit/basis,
   root/rule/requirement pins, recipe versions, authored tier/step/adjustment facts,
   reviewed nutrition references and declared candidate universe. Completeness is
   relative to the declared universe, never automatically all production catalog.
2. An ownership/source map: Catalog/Recipes/Planning/Nutrition source responsibility,
   authorized coherent capture, effective-time/version and source absence/frontier evidence.
   A submitted complete_pool flag or fingerprint cannot mint canonical source authority.
3. A finite exact estimator: derive nutrient granularity from authored portion steps,
   discrete ingredient quantities and grounded composition. Distinguish EP_RAW_G,
   COOKED_G and COUNT; no implicit AP→EP, cooking nutrient retention, package-size
   resolution, or per-member allocation. Unknown transformation or TO_TASTE range fails
   closed or needs a separately approved explicit finite semantics.
4. Independent resolution checker: recompute granularity and coverage from primitive
   facts rather than trusting the fixture's portion_step == expected_step, authored pool
   digest or producer's business algorithm. Reject source tampering and favorable subsets.
5. Hard/soft semantics: coarse serving resolution may yield INSUFFICIENT/warning/advisor,
   **not** a hard physiological violation or solver-proven infeasibility. Never widen
   hard/goal protection or silently inflate comfort from package or DataConfidence.
   Retain frozen MTR-006 NPS084 distinction.
6. Acyclic handoff: use existing NutritionPolicyRequirementSpec prior to synthesis.
   Specify the replacement for TEST_ONLY fixture protocol without changing frozen
   MTR-006 root/synthesis/business semantics; additive changes need separate review.
7. Authority and production isolation: TEST_ONLY taint end-to-end, no clinical formula,
   population, numerical floor/goal rate, qualified publisher, production provider,
   content seed or default invented. Catalog REVIEWED is not clinical approval.
8. Candidate cardinality and status: complete canonical bounded pool, explicit
   server-owned resource limits, no silent shortlist truncation, no presumption
   that a resolution estimate proves a globally feasible menu.
9. Test/PG matrix: good/bad portion steps, incompatible bases, stale/missing reference,
   unreviewed sources, fake hashes, mixed environments, unsupported member/period,
   zero/missingness, partial universe, boundary arithmetic, independent replay and
   adversarial producer-forged data. Real PostgreSQL tests are required only for
   genuinely DB-owned new source paths; propose counts rather than claiming execution.
10. MTR-008 downstream seam: preserve Validation-owned fresh admission for
    NutritionPolicyReference and separate Policy-owned precision source selection from
    final ResolvedPlanPolicy assembly. No raw PlanningMode, BudgetPressure-as-preference,
    defaults, economic/kitchen solver or unrelated adapter implementation.
11. Deterministic interfaces with exact provenance, source/version/calendars, bounded
    bytes/rows/time and all-or-error overflow. No new migration/persistence is presumed
    necessary until the design proves the source gap and receives separate approval.

If the source corpus, authored portion semantics or exact universe completeness cannot be
proved, the future **implementation gate must STOP** rather than guess a numerical
resolution or silently expand frozen authority.

## 6. Exact next-gate recommendation and stop

**NEXT RECOMMENDED GATE: MTR-007 SOURCE-BOUND NUTRITION RESOLUTION ESTIMATOR —
BOUNDED DETAILED DESIGN.**

**STATUS: PROPOSED / READY FOR INDEPENDENT ARCHITECTURE REVIEW, NOT APPROVED.**

No automatic next-gate start follows. MTR-008 may have a separate scoped design of
precision/default/week/override provenance, but full MTR-008 and all downstream execution
remain incomplete. The structural MTR-006 foundation and earlier Nutrition Root remain
FROZEN; full MTR-006/007/008 issues remain OPEN. MTR-040 COMPLETE; MTR-039 OPEN;
full MTR-041/046 PARTIAL; full MTR-020B/021/024 BLOCKED. Production Nutrition/clinical
content/qualification gate CLOSED. planner_ready=False, activation_ready=False;
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED.

This documentation review alone does not authorize design, implementation, migration,
production content, issue closure, merge or planner activation. It needs exact-head
independent architecture review, separate merge authorization and successful exact merged
main push CI, followed by separately authorized MTR-007 design work.
