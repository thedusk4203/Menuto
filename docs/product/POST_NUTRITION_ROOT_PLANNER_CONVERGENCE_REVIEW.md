# Post-Nutrition-Root Planner Convergence — dependency review

Review date: 2026-11-04. **REVIEW PROPOSAL / DOCUMENTATION ONLY — AWAITING ARCHITECTURE REVIEW.**
This review reopens the dependency decision after the **structural** Nutrition Root Contract
& Supported-Eligibility Foundation was frozen and synchronized. Its target remains the
shortest defensible path to **Validated Plan Preview**, not activation, Execution, a new
preference abstraction, or automatic completion of the MTR-006 parent.

## 1. Verified entry gate and exact source boundary

| Item | Evidence |
| --- | --- |
| Exact reviewed main / review branch base | `52aed2059fb26162bc5c89caad78eb1e87dcb035` |
| Implementation PR #123, reviewed head | `7953e74c64ce0d2db06d802a9213c0b0ad27dd1d` |
| Implementation review and freeze | [review 6500572389](https://github.com/thedusk4203/Menuto/pull/123#issuecomment-6500572389); [canonical structural freeze 6506156639](https://github.com/thedusk4203/Menuto/pull/123#issuecomment-6506156639) |
| #123 merge/main and post-merge push | `6a77575fcb0ecf7a02493dae935fab88e94d09f1`; [CI 40931231875 — SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/40931231875) |
| #124 status sync reviewed head | `63af8d8c065c9e610242bb85fd5a40888f996da6`; [review 6624588628](https://github.com/thedusk4203/Menuto/pull/124#issuecomment-6624588628) |
| #124 actual merge/current main | `52aed2059fb26162bc5c89caad78eb1e87dcb035`; [push CI 41789357940 — SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/41789357940); [completion 6625566045](https://github.com/thedusk4203/Menuto/pull/124#issuecomment-6625566045) |
| Verified merged tree | `074581ddbae87de8b8882ba87839e2dd99952a8a`, identical to the reviewed #124 documentation tree |
| Full retained regression | **3,782 passed / 0 skips**; NRC01–NRC80; 66 real PostgreSQL executions / 32 obligations; SCRAM/TLS 16/16; benchmark 22/22; client 10/10 |
| Frozen interfaces / schema | 447 exports (403 hash-retained + 44 additive); migration 0016; 98 domain tables; 13 Nutrition source tables, 1 sequence, 60 protected SQL functions |
| Empty fresh install | 0 production provider/enrollment/guideline/eligibility/nutrition content/seed/default rows; this is **fresh-install evidence**, not a live production deployment audit |

Sources: the [repository freeze receipt](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_FREEZE_RECEIPT.md),
[implementation evidence](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_EVIDENCE.md),
[approved Nutrition-root design](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_DESIGN.md),
[prior convergence DAG](POST_PR_120_PLANNER_CONVERGENCE_REVIEW.md), live MTR GitHub issue
acceptance and source files at the exact main above. No new test, migration or data evidence is
claimed by this review. The existing full-suite CI belongs to #124's **post-merge push**,
not to this as-yet-unverified docs review head.

The frozen source machinery has authenticated PostgreSQL authority, review/publish separation
by distinct verified humans, member observation/goal/delegation/eligibility journals,
one-connection coherent capture, pure zero-I/O replay, and an independent Nutrition-root
source/containment validator. It **does not** supply qualified production reviewers/assessors,
production guideline publication, supported-population protocol, production numerical values,
a verified production member assessment, or any NutritionPolicy synthesis.

**NUTRITION ROOT CONTRACT & SUPPORTED-ELIGIBILITY FOUNDATION — FROZEN.**
**PRODUCTION NUTRITION/CLINICAL CONTENT GATE — CLOSED.**

## 2. Evidence inspected and live acceptance reconciliation

- [MTR-006 / issue #5](https://github.com/thedusk4203/Menuto/issues/5): OPEN; canonical
  guideline/goal/comfort/weekly synthesis and versioned root-policy contract remain unsatisfied.
- [MTR-007 / #6](https://github.com/thedusk4203/Menuto/issues/6): OPEN; catalog/portion
  resolution reporting and bounded no-silent-widening behavior are missing.
- [MTR-008 / #7](https://github.com/thedusk4203/Menuto/issues/7): OPEN; four orthogonal
  intent axes require independent source/default/override compilation.
- [MTR-019 / #20](https://github.com/thedusk4203/Menuto/issues/20),
  [020 / #21](https://github.com/thedusk4203/Menuto/issues/21),
  [021 / #22](https://github.com/thedusk4203/Menuto/issues/22),
  [022 / #23](https://github.com/thedusk4203/Menuto/issues/23),
  [024 / #25](https://github.com/thedusk4203/Menuto/issues/25):
  parent acceptance remains OPEN; frozen 019A/B/C and conservative 020A partially satisfy
  input needs, not full heuristic portfolio, feasibility or solver acceptance.
- [MTR-025 / #26](https://github.com/thedusk4203/Menuto/issues/26),
  [026 / #27](https://github.com/thedusk4203/Menuto/issues/27),
  [027 / #28](https://github.com/thedusk4203/Menuto/issues/28): OPEN;
  frozen validation subject and root companion are not a complete plan-verification verdict
  or production planner API.
- [MTR-046 / #47](https://github.com/thedusk4203/Menuto/issues/47):
  full catalog coverage remains PARTIAL; reviewed culinary features do not establish
  ingredient allergen classifications, meal roles or equipment availability.

Reviewed [ADR-002](../adr/ADR-002-nutrition-policy-engine.md) (four-layer synthesis,
no BMR universal floor), [ADR-003](../adr/ADR-003-plan-policy-resolution.md) (independent
intent axes), [ADR-010](../adr/ADR-010-independent-validator.md),
[Spec V1.3](../MENUTO_DEVELOPMENT_SPEC_V1_3.md) and
[INV-001–030](../ARCHITECTURE_INVARIANTS.md).
Current code inspection includes
[Nutrition root contracts](../../apps/backend/app/modules/nutrition/root_contracts.py),
[root public seam](../../apps/backend/app/modules/nutrition/root_public.py),
[pure root resolution](../../apps/backend/app/modules/nutrition/root_resolution.py),
[independent root validator](../../apps/backend/app/modules/validation/nutrition_roots.py),
[policy contracts](../../apps/backend/app/modules/policy/contracts.py),
[draft request](../../apps/backend/app/domain/snapshots.py),
[020A shortlist](../../apps/backend/app/modules/planning/shortlist.py),
[plan validation](../../apps/backend/app/modules/validation/public.py) and
[HTTP entrypoint](../../apps/backend/app/main.py).
These are direct architectural evidence, not completion certificates for broad parent issues.

## 3. What the root freeze actually unlocked

| Boundary | Available in frozen source | Missing next consumer capability |
| --- | --- | --- |
| Exact source identity | `NutritionRootRequest` pins provider, family, guideline revision/body fingerprint, protocol/scope, member and temporal interval | Choose applicable complete *reviewed* source, with no latest/default fallback; production source roster still empty |
| Admission | `NutritionRootContract` has `AVAILABLE/UNAVAILABLE`, `SUPPORTED/UNSUPPORTED/INELIGIBLE/UNKNOWN`, exact `PRESENT/ABSENT/RETRACTED/AMBIGUOUS` goal and reasons | Synthesis must accept only exact complete `AVAILABLE + SUPPORTED + PRESENT` inputs and fail closed on every other state |
| Hard/reference roots | `RANGE/MINIMUM/MAXIMUM/TARGET` with exact metric/unit/temporal/protocol/goal bindings; `TARGET` is reference center only | A versioned NutritionPolicy with **separate** hard, protected goal, comfort, daily/weekly and resolution claims; no new scientific rule is implicit |
| Source and independent containment | Retained coherent histories; replay validation; `ROOT_SOURCE_CONSISTENCY_ONLY` and `ROOT_AND_DERIVED_CONTAINMENT` companion | Independent **policy semantic** verification of goal/comfort/temporal and complete required preview policy coverage, not only pairwise root containment |
| Numerics and production eligibility | Mathematical rational/descriptor machinery and TEST_ONLY fixtures | Approved clinical/nutrition content, actual supported scope, qualified authorities and per-member assessments; **none provided** |
| Policy and product | `ValidationCoveragePolicySnapshot.definition=FOUNDATION_NO_CLINICAL_POLICY`; draft intent axes | MTR-006 synthesis, MTR-007 resolution, MTR-008 compiled policy, Feasibility, Stage1/Stage2, complete independent preview subject/report, API |

Important observed detail: `resolve_nutrition_root` yields nonempty roots only when admission is
`SUPPORTED`, goal state is `PRESENT`, and no missingness reasons remain. It does not infer
`MAINTAIN` or hard numerical policy from mass/height or a guideline label. Its contract explicitly
says `policy_synthesis=NOT_PERFORMED`,
`numeric_goal_protection=NOT_SYNTHESIZED`, `planner_ready=False`,
`activation_ready=False`. These flags describe the *root output*, not a concealed engine.

The independent root validator is under `validation/nutrition_roots.py`, distinct from
`nutrition/root_resolution.py`. Its `CONSISTENT` decision is not independent scientific
certification, a full NutritionPolicy semantic pass, a successful plan check, or PRECOMMIT.

## 4. Product target and two distinct readiness tracks

Target: a single **initial-generation, non-activating Validated Plan Preview** for a declared
finite horizon/pool, with one tracked nutrition member, exact household participants,
complete required hard policy, grounded food/material quantities, planned economics and
causal flow, Stage1 plus versioned Stage2 utility, complete immutable validation subject,
and genuinely independent required-coverage verdict. No activation, acquisition,
cooking execution or behavioral-learning event is implied.

**Track A — structural engineering/test readiness.** A source-bound deterministic MTR-006
synthesis contract can be *designed* with retained `TEST_ONLY` guideline, protocol, eligibility
and goal fixtures while the production source roster is empty. Such work has value for
finite semantics, failure modes, policy/validator interfaces and future solver inputs, but
cannot establish production nutrition correctness, content authority or preview readiness.

**Track B — production scientific/authority readiness.** Before any production-applicable
root or preview can be called supported, independently approve the reference edition and
jurisdiction, evidence and numerical values, interpretation and metric/time bases,
supported/excluded scope and exact evidence/assessment protocol, qualification and enrollment
of distinct reviewer/publisher and assessors, and source publication plus actual qualified
member assessments. Engineering tests, SHA pins, PostgreSQL enrollment, REVIEWED_PRODUCTION
flags and source fingerprints do **not** replace this gate.

Track B is a hard dependency of any **real** supported production preview. Track A can be
designed in parallel, never used to manufacture B. If policy design cannot express
science-dependent decisions as independently reviewed content/rules, it must STOP instead of
inventing constants or claiming provisional production nutrition.

**TEST_ONLY contamination guard (future design obligation).** The frozen source discriminator
is `NrcEnvironment = TEST_ONLY | REVIEWED_PRODUCTION` on the root request and retained source
records; it is not an invented `authority_scope=PRODUCTION` grant. Future NutritionPolicy,
ResolvedPlanPolicy, preview subject and result must preserve and verify all contributing
environment/provenance identities. Any TEST_ONLY dependency forces an explicitly isolated
TEST_ONLY/research result and must be rejected by production preview admission. The
`REVIEWED_PRODUCTION` label by itself also confers no scientific/clinical approval; complete
independent content review, publication authority and member eligibility remain required.
An isolated structural test that passes independent checks is **not** a production-validated
plan, and must not be presented to users as an ordinary Validated Plan Preview.

## 5. Updated capability DAG

~~~mermaid
flowchart TD
    R[Frozen Nutrition root machinery with retained source identity] --> N[MTR-006 source-bound synthesis and containment]
    T[Isolated TEST_ONLY inputs for engineering] --> N
    C[Production nutrition evidence qualification gate CLOSED] -. separate approval required .-> PR[Production-applicable supported source]
    PR -. production source admission only .-> N
    B[Frozen households 019A/B/C 020A inventory retail sources] --> NR[MTR-007 finite catalog and portion resolution evidence]
    N -. approved comfort and resolution contract .-> NR
    N --> P[MTR-008 versioned orthogonal ResolvedPlanPolicy]
    B --> POOL[Complete bounded all-020A-survivor pool]
    S[Reviewed restriction safety role equipment availability facts] --> POOL
    P --> POOL
    B --> E[Source-pinned checkout offers package inventory scenario inputs]
    P --> E
    B --> F[Planned material and batch conservation rules and opening state]
    POOL --> V[MTR-021 feasibility and evidence completeness diagnostics]
    P --> V
    NR --> V
    S --> V
    E --> V
    F --> V
    N --> V
    V --> O[MTR-022 Stage1 joint global solve]
    E --> O
    F --> O
    U[Versioned separable MTR-024 utility input and policy boundary] --> Z[MTR-024 Stage2 within Stage1 hard feasible tolerance envelope]
    O --> Z
    Z --> D[Solver-selected basket batch material flow and member allocations]
    D --> Q[MTR-025 complete additive preview subject]
    P --> Q
    E --> Q
    F --> Q
    NR --> Q
    Q --> I[MTR-026 independent complete preview checks]
    N --> I
    S --> I
    I --> A[MTR-027 non activating API with auth and ingress limits]
    A --> PV[VALIDATED PLAN PREVIEW with complete supported authority]
    H[History novelty and full 020B portfolio] -. optional richer path .-> POOL
~~~

The graph shows **distinct admission paths**, not a claim that TEST_ONLY fixtures and
production content are jointly required for a single policy instance. TEST_ONLY proves
structural behavior only; production use instead requires complete, externally approved
production sources. The root contract and its exact retained pins are shared machinery.
Nodes beyond R remain incomplete. A dependency arrow is not implementation authorization.
The graph separates **upstream** procurement offers, opening inventory, safety, and
causal material/batch *rules* from the **downstream** solver-selected purchase basket, batch
schedule, material ledger and member allocations. Feasibility can reason about the existence of
solutions using canonical inputs but cannot require the final chosen plan as a prerequisite.
Stage1/Stage2 construct or select the actual plan; MTR-025/026 check those chosen outputs
independently. MTR-007 has an independent supply-side input branch and coordinates
policy-dependent resolution semantics with MTR-006; its entire implementation is not a
prerequisite to *designing* MTR-006. The root gate's frozen `REVIEWED_PRODUCTION` label
does not itself authorize production nutrition.

## 6. Candidate-gate comparison and choice

| Candidate | Can define a bounded design now? | Would it remove the most direct remaining blocker? | Decision |
| --- | --- | --- | --- |
| **Source-bound MTR-006 NutritionPolicy synthesis/containment** | **YES**: finite frozen root contract, exact algebra and independent root checker exist | **YES**: first missing derived hard/goal/comfort/weekly semantics needed by policy, feasibility and validator | **SELECT for next detailed-design review**, subject to content stop |
| Production nutrition content/evidence/qualification authority | Authority workflow exists, but **no approved editions, values, population, protocol or qualified actors are in repo evidence** | **YES for production**, irreducible; cannot be completed by coding or synthetic fixtures | **Mandatory parallel external evidence/authority track — CLOSED; not secretly bundled with MTR-006** |
| MTR-008 PlanPolicyResolver | Orthogonal request axes and BudgetContract exist; precedence design possible | Not sufficient: can compile preferences but cannot create root/goal/comfort truth | Follow MTR-006 interface; independent default/override sources still to prove |
| MTR-007 resolution estimator | Grounded quantities and discrete portions exist | Needed to bound comfort/resolution; must not derive precision from packages | Define interface with MTR-006; standalone implementation follows approved policy semantics |
| Safety/role/context classification | Ingredient exclusion primitive and culinary projection exist | Hard safety/source gap remains for enabled restrictions; kitchen/context facts needed for utility | Parallel source design; no guessed allergen safety or meal-role equivalence |
| MTR-011–013 economics, MTR-023 planned flow | Retail, ingredient binding, inventory and plan primitives are reusable | Needed for physical/economic solver but do not synthesize nutrition policy | Parallel contract track; do not mistake price pairs for checkout costs or planned intents for physical assets |
| MTR-021/022/024 solver, MTR-025/026/027 preview validation/API | Partial primitives and synthetic benchmarks exist | Full implementation currently blocked by policy, scenarios, planned-flow and coverage | Not first; keep independent validation and API limits explicit |
| Full MTR-020B, MTR-039/041, additional TasteFit/coordinate reducer | Some upstream preference/exposure sources exist | **NO** on the bounded all-020A-survivor route | Defer; no optional history dimension or unsafe default |

This choice minimizes an immediate *capability* prerequisite. It does not prove a
calendar-time critical path: production content review and independent operational source
gates may take longer and should be initiated separately, with their own explicit authority.

## 7. Selected next gate: exact design boundary

**Recommended gate: MTR-006 SOURCE-BOUND NUTRITION POLICY SYNTHESIS & CONTAINMENT —
BOUNDED DETAILED DESIGN.**

A future design must define a versioned immutable policy output that consumes exactly one
complete frozen `NutritionRootContract` and fully retained source fingerprints, and
keeps the four ADR-002 layers separate:

1. **Guideline/eligibility:** inherit reviewed hard/reference clauses unchanged in meaning;
   reject `UNAVAILABLE`, non-`SUPPORTED`, absent/retracted/ambiguous goal, missing/stale
   publication, protocol mismatch, unsupported time/basis, or partial source coverage.
   `TARGET` does not turn into a hard bound.
2. **Goal protection:** distinguish `CUT/MAINTAIN/GAIN` *intent* from independently approved
   numerical `GoalEnergyEnvelope` and any justified floor. Never infer energy deficit,
   target, rate, BMR/TDEE coefficient or safety constant merely from a direction string.
   Missing goal-protection rule/evidence must be typed `UNSUPPORTED` or `BLOCKED`, not
   an invented neutral envelope.
3. **Resolution and temporal:** daily hard envelope, separately tagged comfort and weekly
   centering/coverage, explicit horizon and time-zone/calendar pins, catalog/portion
   resolution evidence and lossless unit basis. If daily/weekly composition or cross-version
   stitching is unsupported, reject that requested scope; no silent day/week scaling or
   relaxation. Coordinate the MTR-007 estimator interface without marking #6 complete.
4. **NutritionPrecision:** apply user preference **only to authorized comfort policy**
   inside hard/goal protection; never alter publication, physiological root or validated
   safety floor. CostPreference, KitchenEffort, BudgetPressure and TasteFit cannot weaken
   it; DataConfidence cannot be double-counted as band inflation.

Propose a distinct additive `NutritionPolicy` definition; do not mutate/falsify
`NutritionRootContract` literals or treat `NutritionDerivedContainmentClaim` as the
entire policy. Policy identity must pin guideline edition/protocol, root/source and
member goal state, explicit rule/evidence, request/temporal context, supported coverage
and selection policy version. State exactly which derived quantities can be represented
without numerical policy; return structurally precise missingness for the rest.

**Content-dependent computation is not pre-authorized.** A design may define the *slots*
and exact validated algebra for production-reviewed rules, but cannot ship clinical values,
reviewed population flags, formulas/rates, qualification records or production fallback.
There is no global/current/default guideline selector, environment-based policy,
synthetic-production promotion or hidden "reasonable" calorie range.

**Explicit synthesis-rule authority.** The next design must define immutable, version-pinned
rule bodies, exact applicability, complete evidence/publication source identity and environment
(`TEST_ONLY` or `REVIEWED_PRODUCTION` as the frozen root source vocabulary), and independently
checked rule selection. Numeric transformation coefficients, goal-energy calculations and
comfort/weekly rule content must never be hard-coded as unversioned scientific authority.
Missing or ambiguous rule authority blocks synthesis with a typed reason. A fingerprint,
`REVIEWED_PRODUCTION` tag or user-authored coefficient is not sufficient publication/evidence
authority. The source strategy for rules must be explicitly reviewed; this review does not
authorize a new table, registry, migration or production seed.

**Finite composition and empty-set semantics.** The frozen single-guideline contract rejects
duplicate `(metric, temporal, interpretation)` clauses in one bundle. It does **not** currently
authorize combining arbitrary second clinical guidelines, cross-metric addition or unsupported
clinical overrides. Any future combination of multiple compatible hard constraints must first
prove same member, metric, measurement basis, unit, scope, temporal frame and authorized source
selection; conflicting or empty intersections are **BLOCKED/INFEASIBLE POLICY**, never a reason
to widen a hard root. The design must decide how authoritatively specified goal and comfort
claims are admitted within hard constraints and when conflict fails; automatic clipping or
direction-preserving fallbacks are **not** authorized by this review. Any maintenance reference
point or directional test also requires independently reviewed rule evidence.

**Temporal safety without invented floors.** Every independently authored daily hard limit must
hold for every applicable day, even when a separate authorized weekly goal/centering objective
exists. Weekly averages never override applicable daily hard roots. Conversely, a WEEK-only
source does not create an unreviewed DAY hard floor; missing required daily authority blocks
that supported policy scope. Temporal conversion, rolling-window assembly and calendar/timezone
consistency require explicit reviewed rules and independent verification.

**Member boundary.** The first bounded preview has **one explicitly tracked nutrition member**
with a member-owned NutritionPolicy, plus exact participating household members whose applicable
ingredient/allergen/diet safety constraints remain mandatory. No nutrition hard/goal targets may
be summed, averaged, or borrowed between members, and frozen shared-member TasteFit may not
supply physiological policy. Future multi-member nutrition planning requires separately
authorized per-member NutritionPolicy and exact serving allocations; this is not silently
required by the one-tracked-member preview.

Independent Validation must replay/check underlying frozen root authority and separately
verify the **derived policy business claims**, not rely on a producer-compiled envelope or
the producer's semantic validator as its oracle. Existing
`ROOT_AND_DERIVED_CONTAINMENT` tests only source/containment obligations and is
**not** full MTR-006 business correctness. Every mandatory policy claim must have explicit
coverage and no vacuous success when its carrier is absent. Preview remains non-authorizing.

Design-specific questions to settle: exact source/rule publication responsibility,
how reviewed **numerical semantics** and source versions bind without unapproved policy seeds,
goal-protection applicability, required per-nutrient hard vs center coverage, daily/weekly
temporal consistency and rounding/resolution, authority of profile default vs per-request
NutritionPrecision, independent verifier input, structural limits and compatibility/export
seam. If any cannot be settled without unapproved scientific content, report an exact
prerequisite and STOP rather than guessing.

## 8. Bounded preview follow-through and non-bypass conditions

The following is a proposed subsequent partial order, **not** work authorized by this PR:

1. Freeze a bounded MTR-006 structural synthesis implementation under independently approved
   design, with **TEST_ONLY** fixtures and unchanged production-content CLOSED semantics.
   Real production availability still requires separate content/evidence/qualification approval.
2. Settle MTR-007 finite resolution/portion interface and MTR-008 versioned orthogonal
   resolution from explicit authorized default/week/override sources. `NutritionPrecision`
   is a comfort choice, not clinical authority. Required budget pressure/scenarios cannot
   default to zero.
3. Build a complete, source-pinned **all-020A-survivors** bounded candidate pool. System-owned
   count/time/bytes bound; overflow and partial capture reject rather than truncate. Infeasibility
   may only be asserted over the declared complete pool. Full 020B three-portfolio acceptance
   is **not** claimed, and required role/novelty sources re-enter if a richer pool is selected.
4. Resolve supported participant safety, recipe role/effort/equipment and household context.
   Missing allergen/diet classifications **block** those enabled restrictions. "No classification"
   cannot mean safe. Tested exclusion-only scope is not evidence of universal safety.
5. Define source-pinned real quantity-specific procurement offers and scenarios, opening
   physical inventory with reservations, approved loss/fragility policy, and complete
   requirement→acquisition→batch→serving **conservation rules** as Feasibility/Stage1 inputs.
   Stage1/Stage2 must construct or select an actual planned procurement basket, batch
   transformations, chronological material flow and exact member-serving allocation as
   **solver output**. Preview validation checks the output against independently retained
   inputs/rules; the chosen plan is not a prerequisite to running the solver. Planned shopping
   creates no physical stock, and reservations stay binding.
6. MTR-021 complete-scope feasibility (data insufficiency != infeasible) → MTR-022 Stage1 →
   MTR-024 Stage2 under a versioned **multidimensional** utility policy. Stage1 must pass
   an explicit hard-feasible, goal-protected lexicographic/tolerance envelope (not merely an
   unconstrained one-point score). Stage2 may optimize only within that authorized envelope;
   it must not trade away hard constraints or silently expand tolerance. Distinguish taste,
   time, equipment, complexity, repeat and novelty availability. Exact-target shared TasteFit
   alone is **not candidate utility**; a required but missing dimension blocks, whereas
   history/novelty may be explicitly **DISABLED/NOT_USED** by an approved first policy,
   not fake-zero imputed.
7. Add complete preview primitive/source/scenario/flow pins to frozen MTR-025 by additive
   version/companion. Independent MTR-026 must verify *all required preview coverage* with
   exact root, member nutrition, economics, planned causal conservation and source coherence;
   a partial diagnostic result cannot be relabeled PASS.
8. Only then design MTR-027 non-activating preview orchestration with production actor/auth,
   server-owned ingress limits **before** expensive parsing, policy/source size and nesting
   limits, timeout and structured status. Do not expose an unguarded HTTP planner route.
   PRECOMMIT remains FAIL-CLOSED; no activation or Execution is required for preview.

Frozen 040 preference source/TasteFit and 041A–F/046A/019A–C/020A/025 foundations are inputs,
not candidates for another generic adapter, reimplementation or parent auto-closure.

## 9. Outstanding blockers and explicit stop rules

| Blocker | Owner / criterion to unlock | Status after #124 |
| --- | --- | --- |
| Actual guideline values, population, protocol, scientific interpretation | Qualified nutrition/clinical reference and independent evidence review, then protected publication under exact authority | **CLOSED / NO PRODUCTION AUTHORITY** |
| Verified reviewer/publisher/assessor enrollment and actual supported member assessment | Independent administration, two-person source publication, qualified protocol assessment | **EMPTY BY DEFAULT / NOT AUTHORIZED** |
| Complete goal-energy protection and weekly/comfort numeric rules | Reviewed source-bound MTR-006 policy rule content, exact applicability; may not be inferred from `ENERGY_DIRECTION` | **NOT PROVIDED** |
| Policy defaults/overrides, availability, budget pressure, scenario rules | Household/Policy/Retail protected source and exact precedence | **MISSING** |
| Ingredient safety classification, role/time/equipment sources | Catalog/Recipe/Nutrition/Household owners with reviewed applicability | **INCOMPLETE** |
| Planned allocations and robust basket/economics | Planning/Retail/Cooking/Inventory distinct owned primitives and predicted causal flow | **INCOMPLETE** |
| Full independent preview coverage and public ingress security | Validation and application/auth/ops owners | **INCOMPLETE** |
| Rule publication/selection and TEST_ONLY taint propagation | Nutrition/Policy source authority and Validation; versioned rule bodies, independently checked environment/provenance and complete mandatory policy claims | **NOT AUTHORIZED / DESIGN REQUIRED** |
| No arbitrary clinical multi-root combination | Nutrition source owners; current root bundle only, exact same-descriptor future combination if separately designed and approved | **CURRENTLY UNSUPPORTED** |

Nothing in this review changes the mandatory content gate; a docs review, tests using
`TEST_ONLY` sources, PostgreSQL capabilities, hash matching, or the exact-head CI
cannot certify medical/scientific policy. Never treat a frozen **structural** foundation as
an operating clinical recommendation.

If the next design cannot establish complete policy semantics without external reviewed
rules/evidence, its required verdict is:

`DESIGN BLOCKED — MISSING PREREQUISITE: <exact rule / reference / evidence / qualification>.`

It must not narrow mandatory hard constraints silently simply to produce an apparent preview.

## 10. CI and governance

The exact #124 post-merge `push` regression remains the last **verified** baseline:
3,782 passed /0 skips, exports 447, migration 0016 /98. This docs-only review adds no tests,
definitions, schema or persistence; future PR CI must be checked on its *actual* review head.

The full CI run is expensive; staged fast unit/architecture/relevant real-PG/exports/client
feedback may be added in a separately approved tooling gate, but required exact-head full
PR review and exact merged-main `push` gates cannot be substituted by targeted local runs.
No workflow change, split/sharding or weakening is proposed in this PR.

Keep GitHub workflow failures (including billing/spending-limit or expired disposable
certificate infrastructure failures) distinct from successful test evidence; a rerun
qualifies only when the *full* latest attempt finishes SUCCESS on the same reviewed SHA.

PR lifecycle: this review must remain **OPEN**, auto-merge OFF. It does not approve its own
conclusion, authorize detailed design, publish production nutrition content, merge itself,
start implementation, change issue states or lift PRECOMMIT.

## 11. Status preserved

MTR-006 OPEN / partial root-source foundation only; MTR-007 OPEN; MTR-008 OPEN.
MTR-040 COMPLETE; MTR-039 OPEN; full MTR-041/MTR-046 PARTIAL.
MTR-020B/MTR-021/MTR-024 BLOCKED; MTR-022,025,026,027 not complete.
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED.
`policy_synthesis=NOT_PERFORMED`, `numeric_goal_protection=NOT_SYNTHESIZED`,
`planner_ready=False`, `activation_ready=False`. No new policy publication, migration 0017,
runtime code, data, test, tooling, numerical constant, value, seed, default, provider,
reviewer or assessor is part of this documentation proposal.

## 12. Review verdict

**NEXT RECOMMENDED GATE: MTR-006 SOURCE-BOUND NUTRITION POLICY SYNTHESIS & CONTAINMENT —
BOUNDED DETAILED DESIGN**

**STATUS: READY FOR DETAILED DESIGN — PENDING THIS REVIEW'S ARCHITECTURE APPROVAL**

**PRODUCTION NUTRITION/CLINICAL CONTENT GATE: CLOSED — HARD PREREQUISITE FOR REAL PREVIEW**

**IMPLEMENTATION NOT AUTHORIZED.** No next gate starts automatically.
