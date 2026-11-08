# Post-MTR-006 v2 Dependency and Readiness Review — MTR-006 / MTR-007 / MTR-008 Convergence

**DOCUMENTATION-ONLY DEPENDENCY AND READINESS REVIEW — PENDING INDEPENDENT ARCHITECTURE APPROVAL**  
**NO DESIGN, IMPLEMENTATION, CLINICAL CONTENT, MERGE OR DOWNSTREAM WORK AUTHORIZED**

This review conducts a comprehensive dependency and implementation readiness analysis following
the structural freeze of **MTR-006 Policy Integration v2**. It defines the cross-domain interfaces,
blocker register, readiness assessments and recommended next bounded slice for independent
architecture review. It does not introduce new executable contracts, clinical policies, schema
migrations or downstream activation.

---

## 1. Canonical Baseline and Verified Evidence

Reviewed repository: `thedusk4203/Menuto`; exact verified `main` SHA:
**`4b1decc67124eafddb1626dfc6e796a8a77de943`**, tree: **`8425dc9ecf6f1325ac16835f9122a06e7a1d262b`**.
[PR #139](https://github.com/thedusk4203/Menuto/pull/139) (Docs synchronization) is MERGED and
VERIFIED. Exact post-merge **push** [CI 42432677783](https://github.com/thedusk4203/Menuto/actions/runs/42432677783)
is **SUCCESS**, including Python (41m18s) and web (14s) jobs. Completed direct logs confirm
**4,369 passed / 0 skips**, 6 retained dependency warnings, SCRAM/TLS 16/16, benchmark 22/22,
client 10/10, architecture baseline 30 invariants, and import boundaries across 16 registered contexts.

| Capability / Milestone | Canonical Freeze Identity | Retained Evidence / Receipts | Status |
|---|---|---|---|
| **Nutrition Root** | Merge `6a77575fcb0ecf7a02493dae935fab88e94d09f1` | [Freeze receipt](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_FREEZE_RECEIPT.md) | **STRUCTURALLY FROZEN** |
| **MTR-006 v1 Synthesis** | Merge `45ed430ff3306939366bf82e232d02054475b360` | [Evidence](MTR_006_SOURCE_BOUND_NUTRITION_POLICY_SYNTHESIS_CONTAINMENT_EVIDENCE.md), [PASS 6648590537](https://github.com/thedusk4203/Menuto/pull/127#issuecomment-6648590537) | **STRUCTURALLY FROZEN** |
| **MTR-007 Bounded Estimator** | Merge `82b4a7c631acbc04ffbd522702bf3529d7e2e2d2` | [Evidence](MTR_007_SOURCE_BOUND_NUTRITION_RESOLUTION_ESTIMATOR_EVIDENCE.md), [Freeze 6662354375](https://github.com/thedusk4203/Menuto/pull/130#issuecomment-6662354375) | **STRUCTURALLY FROZEN** |
| **Measurement-Basis Applicability (MBA)** | Merge `9d3b580ce2a2d111223b37814612a4072dbfe6a2`, Tree `3a68035f9c33de152b3899a083d534a537c647e1` | [Freeze receipt](MEASUREMENT_BASIS_APPLICABILITY_INDEPENDENT_EVIDENCE_CONTAINMENT_FREEZE_RECEIPT.md), [Freeze 6688245300](https://github.com/thedusk4203/Menuto/pull/133#issuecomment-6688245300) | **STRUCTURALLY FROZEN / TEST_ONLY** |
| **MTR-006 Policy Integration v2** | Merge `45bb2677d3eb657dcf36aaf9fc5b9e146e8bf8fa`, Tree `19c97149aeaaf108894e7a3d01afd0db4558e9e9` | [Freeze receipt](MTR_006_POLICY_INTEGRATION_V2_FREEZE_RECEIPT.md), [Formal freeze 6710492789](https://github.com/thedusk4203/Menuto/pull/138#issuecomment-6710492789), [PR #138](https://github.com/thedusk4203/Menuto/pull/138) | **STRUCTURALLY FROZEN / TEST_ONLY** |
| **V2 Docs Synchronization** | Merge `4b1decc67124eafddb1626dfc6e796a8a77de943`, Tree `8425dc9ecf6f1325ac16835f9122a06e7a1d262b` | [PR #139](https://github.com/thedusk4203/Menuto/pull/139), Push CI [42432677783](https://github.com/thedusk4203/Menuto/actions/runs/42432677783) | **MERGED & VERIFIED** |

### Verified Baseline Invariants
- **Tests:** 4,369 passed / 0 skips = 4,183 retained baseline + 186 additive v2 cases.
- **Exports:** 528 definitions = 515 unchanged legacy definitions + exactly 13 additive v2 names.
- **Pinned Hashes:** All 503 historical definition hashes and 53 historical frozen source/migration files match their pins (59 total in v2 compatibility manifest, including 6 MBA companions).
- **Persistence Boundary:** Schema **0017 / 108 domain tables**; no migration **0018**; **zero new persistence**, SQL tables, functions, roles or database privileges.
- **Production Content:** Fresh-install production Nutrition/clinical content, providers, qualifications, publications, seeds and defaults remain **0**.
- **Parent Issues:** [#5 / MTR-006](https://github.com/thedusk4203/Menuto/issues/5), [#6 / MTR-007](https://github.com/thedusk4203/Menuto/issues/6), and [#7 / MTR-008](https://github.com/thedusk4203/Menuto/issues/7) remain **OPEN**. Full acceptance is incomplete.

---

## 2. Governing Specifications, ADRs, and Architecture Invariants

The governing specifications for policy resolution and validation are:
- [Development Spec V1.3 §8.1, §8.3, §10.3, §10.4, §10.9–§10.10, §21](../MENUTO_DEVELOPMENT_SPEC_V1_3.md).
- [ADR-002: Nutrition Policy Engine](../adr/ADR-002-nutrition-policy-engine.md).
- [ADR-003: Orthogonal Plan Policy Resolution](../adr/ADR-003-plan-policy-resolution.md).
- [ADR-010: Independent Semantic Validator, Primitive Recomputation & Chronological Replay](../adr/ADR-010-independent-validator.md).
- [Architecture Invariants](../ARCHITECTURE_INVARIANTS.md), specifically:
  - **INV-001:** Planning preference must never masquerade as physiology (convenience/thrift cannot lower physiological/guideline floors or erase goal direction).
  - **INV-002:** Observed constraint must never masquerade as user preference (`BudgetPressure`, `CostPreference`, and explicit `BudgetConstraint` are independent signals).
  - **INV-003 / INV-004:** Shared physical/financial assets belong to Household; biological profiles belong to HouseholdMember. Individual safety constraints survive aggregation.
  - **INV-010:** Explicit budget constraints must be verifiable against independently evaluated retail/procurement scenarios.
  - **INV-015–INV-020:** Validation verifies correctness, not optimality; policy definitions may be shared, but correctness enforcement must be independently evaluated; critical validation recomputes from resolved primitive facts; root contracts are checked directly without trusting planner-resolved summaries.
  - **INV-028:** Activating a plan freezes its exact operational snapshot. Subsequent profile changes do not alter an activated plan.

---

## 3. Remaining Requirements Analysis: MTR-006 NutritionPolicyEngine

### What is Structurally Delivered and Frozen
1. **Nutrition Root Contracts:** Versioned member observations, eligibility, delegation, and goal histories under authenticated append-only PostgreSQL storage (`0017_nutrition_roots.py`).
2. **Dedicated Synthesis Authority:** Scoped review and publication of synthesis rules (`0017_nutrition_synthesis_sources.py`).
3. **Four-Layer Policy Synthesis (v1):** Structured guideline hard, reference center, goal protection, and comfort layers with finite exact arithmetic (`apps/backend/app/modules/nutrition/synthesis.py`).
4. **Source-Bound Policy Integration (v2):** Terminal Planning capture over authenticated sources, private one-shot lease binding, joint reachable-value evaluation over NRE candidate universes, MBA same-meaning planned input verification, and independent Validation-owned whole-policy reconstruction (`apps/backend/app/modules/nutrition/policy_v2.py`, `apps/backend/app/modules/validation/nutrition_policy_v2.py`).

### Genuinely Missing Requirements for Full MTR-006 Completion
1. **Production Clinical & Dietary Guidelines Content:** Fresh-install database contains zero guideline rules, reference intakes, or population eligibility criteria. Production content requires independently qualified human reviewers and publishers with active verified credentials.
2. **Input-to-Intake Biological Bridge:** The frozen foundation operates exclusively on `PLANNED_INGREDIENT_INPUT_V1` (offered food). There is no scientific conversion model for cooking retention, culinary nutrient degradation, plate waste, or physiological metabolic absorption.
3. **Multi-Member Serving Allocation Engine:** Nutrition resolution is structurally bound to `WHOLE_TIER_TO_SINGLE_TRACKED_MEMBER_V1`. Dynamic meal division and serving-fraction allocation across multiple participating household members are not supported.
4. **Production Admission:** All current v2 artifacts carry `TEST_ONLY` taint. `admit_production_policy_v2()` fails closed with `PermissionError("PRODUCTION_GATE_CLOSED")`.

**Disposition for MTR-006:** Structurally complete for bounded single-member TEST_ONLY planning. Full business completion is blocked by external scientific content and multi-member allocation. Issue #5 remains **OPEN**.

---

## 4. Remaining Requirements Analysis: MTR-007 NutritionResolutionEstimator

### What is Structurally Delivered and Frozen
1. **Declared Finite Scope & Estimator Primitives:** Recipe portion tiers, candidate ingredient sets, rational joint nutrient vectors, and exact configuration witnesses (`apps/backend/app/modules/nutrition/resolution_estimator.py`).
2. **Exact Gap Quantification:** Reachable delta vectors, band-boundary equality, and discrete gap evidence without scalar maximum-gap approximations.
3. **One-Cut Planning Capture:** Ordinary reader snapshot coordination across Recipe, Catalog, and Household facts (`apps/backend/app/modules/planning/nutrition_resolution_capture.py`).
4. **Measurement-Basis Applicability (MBA):** Pre-policy anchor projection and proof of same-meaning planned input against the synthetic fixture registry (`apps/backend/app/modules/nutrition/basis_applicability.py`).

### Genuinely Missing Requirements for Full MTR-007 Completion
1. **Real-World Catalog Portion Resolution:** The estimator currently evaluates curated recipe portion tiers within a declared synthetic universe. It does not resolve raw packaging sizes, commercial discrete counts, or fractional grocery units against arbitrary retail catalog variants.
2. **Multi-Member Portion Division:** Does not attribute shared multi-portion batches to distinct members with variable attendance or appetite factors.
3. **Catalog Coarseness Advisory:** Spec §10.4 requires structured warnings and advisor options when the available retail catalog is too coarse to reach a requested comfort band, preventing silent widening of goal protection.
4. **Production Ingress:** Operates under `TEST_ONLY` constraints with in-memory fixture registry authority.

**Disposition for MTR-007:** Structurally complete for single-tracked member planned input. Broad catalog ingestion and multi-member attribution are deferred. Issue #6 remains **OPEN**.

---

## 5. Remaining Requirements Analysis: MTR-008 PlanPolicyResolver

### Canonical Responsibilities (ADR-003, Spec §8.1, §10.9–§10.10)
`PlanPolicyResolver` must compile orthogonal inputs into a single immutable, versioned `ResolvedPlanPolicy` snapshot for planner execution:
1. **Orthogonal Inputs:**
   - `UserPolicyDefaults`: Member and household profile defaults.
   - `CurrentWeekContext`: Temporal envelope and calendar availability.
   - `PlanIntentOverride`: Situational user overrides (e.g., "busy week", "strict budget").
   - `BudgetContract`: Explicit spend contract (`amount` + `SPEND_LIMIT` / `TARGET` / `NONE`).
2. **Independent Policy Axes:**
   - `NutritionPrecision`: RELAXED / STANDARD / PRECISION (must consume validated `NutritionPolicyHandoffV2`).
   - `CostPreference`: LOW / NORMAL / HIGH.
   - `KitchenEffort`: MINIMAL / NORMAL / FLEXIBLE + optional `DailyAvailability` prep envelopes.
   - `BudgetConstraint`: Bounded financial limit.
   - `BudgetPressure`: System-derived metric reflecting market reality; distinct from user preference (INV-002).
3. **Strict Constraints:**
   - **No `PlanningMode` Enum:** Banned from canonical domain (ADR-003). Presets must expand into explicit orthogonal fields.
   - **Deterministic Precedence:** Explicit resolution rules between profile defaults, weekly context, and situational overrides.
   - **Snapshot Immutability:** Once activated, a plan's resolved policy snapshot must be immutable against subsequent profile changes (INV-028).

### Current Codebase Reality
- `apps/backend/app/modules/policy/contracts.py` currently contains **only** `ValidationCoveragePolicySnapshot` (`FOUNDATION_NO_CLINICAL_POLICY`).
- `ResolvedPlanPolicy` contract **does not exist**.
- `UserPolicyDefaults`, `PlanIntentOverride`, `KitchenEffort`, and `CostPreference` models do not exist in the policy module.
- `apps/backend/app/domain/snapshots.py` contains early draft types (`BudgetContract`, `PlannerRequestDraft`), but no resolved plan policy snapshot.
- No policy compiler or resolver implementation exists.
- No independent validator for plan policy resolution exists in `apps/backend/app/modules/validation/`.

**Disposition for MTR-008:** High-priority unbuilt foundation. With MTR-006 v2 frozen, MTR-008 is the unblocking link between upstream nutrition foundations and downstream planning orchestration. Issue #7 remains **OPEN**.

---

## 6. Cross-Domain Dependency Matrix and Interface Boundaries

The following matrix maps the exact boundaries, data ownership, and contracts across domains:

| Source Domain | Target Domain | Interface / Contract | Direction & Authority Boundary | Current Status |
|---|---|---|---|---|
| **Policy** | **Nutrition** | `NutritionPrecisionSelection` | **Policy owns planning intent.** Injected into Nutrition synthesis/v2 capture as an authenticated input with subject witness. Nutrition cannot invent defaults. | **FROZEN (v2)** |
| **Nutrition** | **Policy** | `NutritionPolicyHandoffV2` | **Nutrition provides derived policy.** Exposes `NutritionPolicyResultV2` and `NutritionPolicyCheckV2` with `UNVERIFIED_TRANSPORT`. Policy consumes the result only after verifying `AVAILABLE_TEST_ONLY` and `CONSISTENT`. | **FROZEN (v2)** |
| **Planning** | **Policy** | `PlanRequest` / `PlanIntentOverride` | **Planning supplies situational intent.** Planning captures user overrides and week context; Policy resolves them against defaults. | **UNBUILT** |
| **Policy** | **Planning** | `ResolvedPlanPolicy` | **Policy supplies immutable solve envelope.** Planning consumes the resolved policy snapshot for candidate selection and optimization. Planning cannot modify policy fields. | **UNBUILT** |
| **Policy** | **Validation** | `ResolvedPlanPolicy` | **Validation independently checks resolution.** `ValidationOrchestrator` recomputes precedence, verifies orthogonal independence, and checks upstream Nutrition consistency without trusting the Policy compiler. | **UNBUILT** |
| **Household** | **Policy** | `HouseholdMemberIdentity`, `UserPolicyDefaults` | **Household owns profile facts.** Policy reads member identities and stored default preferences. | **PARTIAL (M0)** |
| **Retail / Pricing** | **Policy** | `ReferenceFeasibleCost`, `BudgetPressure` | **Retail supplies economic context.** System-derived budget pressure reflects feasible market costs, distinct from user `CostPreference` (INV-002). | **UNBUILT** |

```text
+-------------------------------------------------------------------------+
|                              HOUSEHOLD                                  |
|   Member profiles, biological identities, goals, policy defaults        |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                               POLICY                                    |
|   UserPolicyDefaults + CurrentWeekContext + PlanIntentOverride          |
|   ├── Emits explicit NutritionPrecisionSelection intent                 |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                              NUTRITION                                  |
|   Root Contracts + Rule Authority + NRE Candidates + MBA Registry       |
|   ├── Synthesizes NutritionPolicyBodyV2                                 |
|   └── Validated via independent ValidationNutritionPolicyV2             |
|   └── Emits NutritionPolicyHandoffV2 (AVAILABLE_TEST_ONLY)             |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                       PLAN POLICY RESOLVER                              |
|   Compiles:                                                             |
|     1. Validated NutritionPolicyHandoffV2                               |
|     2. CostPreference & explicit BudgetContract                         |
|     3. KitchenEffort & DailyAvailability                                |
|     4. Distinct system-derived BudgetPressure                           |
|   ===> Produces ResolvedPlanPolicy (Immutable Versioned Snapshot)       |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                         VALIDATION / PLANNING                           |
|   Independent Validator checks ResolvedPlanPolicy without compiler      |
|   Planning consumes snapshot for candidate solve & validation subject   |
+-------------------------------------------------------------------------+
```

---

## 7. Blocker Register: Technical Gaps vs Closed Clinical Content Gates

To ensure rigorous architectural discipline, blockers are strictly categorized into actionable engineering gaps versus external clinical/content prerequisites:

| ID | Category | Description | Impact | Actionability | Current Gate Status |
|---|---|---|---|---|---|
| **BLK-01** | **Clinical Content** | Absence of production nutritional guidelines, clinical protocols, reference intakes (DRI/RDA/UL), and qualified human clinical authorities. | Prevents production deployment and clinical claims. | External / Non-engineering. | **CLOSED** (`PermissionError: PRODUCTION_GATE_CLOSED`) |
| **BLK-02** | **Scientific Model** | Absence of biological nutrient retention, cooking degradation, and physiological absorption models (offered food != consumed food). | Prevents physiological claims; restricts models to planned ingredient inputs. | Requires verified scientific literature & review. | **BLOCKED** (`PLANNED_INGREDIENT_INPUT_V1` only) |
| **BLK-03** | **Engineering / Schema** | Lack of versioned `ResolvedPlanPolicy` snapshot contract and orthogonal component contracts (`CostPreference`, `KitchenEffort`, `DailyAvailability`). | Blocks MTR-008 completion and prevents planner from consuming resolved policy. | **Actionable in engineering.** | **READY FOR DETAILED DESIGN** |
| **BLK-04** | **Engineering / Logic** | Lack of deterministic precedence resolution rules (Defaults vs Week vs Override) and conflict handling. | Prevents reliable policy compilation. | **Actionable in engineering.** | **READY FOR DETAILED DESIGN** |
| **BLK-05** | **Engineering / Validator** | Lack of independent Validation-owned companion for `ResolvedPlanPolicy` checking (ADR-010). | Violates ADR-010 / INV-016 (planner cannot be sole judge of correctness). | **Actionable in engineering.** | **READY FOR DETAILED DESIGN** |
| **BLK-06** | **Downstream Execution** | Solver integration, CP-SAT formulation, candidate generation, and plan activation. | Depends on `ResolvedPlanPolicy`. | Downstream dependent work. | **NOT STARTED** (`planner_ready=False`, `activation_ready=False`) |

---

## 8. Evaluation of Candidate Next Gates

| Candidate Option | Prerequisites | Scope & Risk Assessment | Disposition |
|---|---|---|---|
| **Option 1: Full MTR-008 Production Implementation (with DB Persistence)** | Requires database schema migration 0018, persistent user defaults tables, UI models, and live integration. | **HIGH RISK / PREMATURE.** Introduces premature persistence schema, migration overhead, and broad UI surface before resolving the core compilation contract. | **REJECTED AS NEXT STEP** |
| **Option 2: Multi-Member MTR-007 Serving Allocation Engine** | Requires dynamic portion-splitting mathematics, shared recipe distribution, and individual member attendance tracking. | **MEDIUM RISK / DEFERRED.** Single-tracked member NRE is already frozen and sufficient for single-member planning. Multi-member allocation does not unblock the core planning pipeline. | **DEFERRED** |
| **Option 3: Production Clinical Content Ingestion** | Requires qualified medical reviewers, signed clinical evidence, and scientific intake conversion. | **BLOCKED.** Production clinical content gate is strictly closed. Cannot be resolved by software engineering alone. | **BLOCKED (GATE CLOSED)** |
| **Option 4: Planner Solver / Feasibility Engine (MTR-020B)** | Requires CP-SAT optimization, candidate generation, and full plan solving. | **BLOCKED ON UPSTREAM.** Solver cannot formulate valid objective functions or constraints without an immutable `ResolvedPlanPolicy` snapshot. | **BLOCKED ON POLICY RESOLUTION** |
| **Option 5: MTR-008 PlanPolicyResolver Foundation — Bounded Detailed Design (STRUCTURAL / TEST_ONLY)** | Requires frozen MTR-006 v2 policy handoff (exists) and explicit orthogonal input models. | **SAFEST / OPTIMAL NEXT SLICE.** Establishes the immutable `ResolvedPlanPolicy` contract, orthogonal axis models, deterministic precedence, and independent validator in an isolated TEST_ONLY boundary. Zero persistence, schema 0017 / 108 preserved. | **SELECTED / RECOMMENDED** |

---

## 9. Recommended Next Slice: MTR-008 PlanPolicyResolver Foundation (STRUCTURAL / TEST_ONLY)

### Recommended Architectural Objective
Design the additive, source-bound **`PlanPolicyResolver`** and versioned **`ResolvedPlanPolicy`** snapshot seam over the frozen `NutritionPolicyHandoffV2`, with explicit orthogonal economic and kitchen preferences.

### Proposed Scope Boundaries
1. **Immutable Contracts (`app.modules.policy.contracts`):**
   - `UserPolicyDefaults`: Member and household profile baseline preferences.
   - `CurrentWeekContext`: Bounded temporal calendar availability and week-level constraints.
   - `PlanIntentOverride`: Explicit, situational plan-level overrides.
   - `CostPreference`: `LOW` / `NORMAL` / `HIGH`.
   - `KitchenEffort`: `MINIMAL` / `NORMAL` / `FLEXIBLE` + `DailyAvailability`.
   - `BudgetContract`: Explicit spend limits (`amount` + `SPEND_LIMIT` / `TARGET` / `NONE`).
   - `ResolvedPlanPolicy`: Top-level versioned snapshot embedding validated nutrition policy, economic constraints, kitchen envelopes, and budget pressure.
2. **Resolution & Precedence Engine (`app.modules.policy.resolver`):**
   - Deterministic precedence: Situational override > Week context > User defaults.
   - Strict separation of `BudgetPressure` (system metric) from `CostPreference` (user intent) (INV-002).
   - Strict elimination of `PlanningMode` (ADR-003).
   - Consumption of `NutritionPolicyHandoffV2`, requiring verified `AVAILABLE_TEST_ONLY` and `CONSISTENT` check before numerical inclusion.
3. **Independent Validation Companion (`app.modules.validation.plan_policy`):**
   - Reconstructs resolution decisions from input primitives and overrides.
   - Independently verifies that nutritional safety constraints were not weakened by cost/effort preferences (INV-001).
   - Verifies snapshot immutability and provenance fingerprinting.
4. **Governance & Persistence:**
   - Pure in-memory / test harness execution.
   - **Zero new persistence:** Schema 0017 / 108 domain tables preserved; no migration 0018.
   - **TEST_ONLY taint:** Production admission remains closed; `planner_ready=False`, `activation_ready=False`.

---

## 10. Proposed Acceptance Families for the Future MTR-008 Design

The following **PPR-D01–PPR-D20** (Plan Policy Resolution Design) families are proposed as the structural acceptance matrix for the future detailed design:

| Family ID | Category | Required Proof / Invariant Verification |
|---|---|---|
| **PPR-D01** | **Orthogonal Independence** | `NutritionPrecision`, `CostPreference`, `KitchenEffort`, and `BudgetContract` vary independently; changing one axis leaves others unchanged (ADR-003). |
| **PPR-D02** | **Preference vs Pressure** | High `BudgetPressure` does not alter user `CostPreference` or convert `TARGET` into `SPEND_LIMIT` (INV-002). |
| **PPR-D03** | **Physiology Protection** | Minimal `KitchenEffort` or low `CostPreference` cannot lower guideline hard roots or goal energy envelopes (INV-001). |
| **PPR-D04** | **PlanningMode Elimination** | Rejection of legacy `PlanningMode` enum or raw shortcut labels at API boundary; requires explicit orthogonal fields (ADR-003). |
| **PPR-D05** | **Precedence Hierarchy** | Plan-level intent override cleanly supersedes weekly context and profile defaults for targeted fields only. |
| **PPR-D06** | **Default Fallback** | Absent situational override faithfully falls back to validated profile default without synthetic defaults. |
| **PPR-D07** | **Nutrition Handoff Consumption** | `ResolvedPlanPolicy` consumes `NutritionPolicyHandoffV2`; non-available or inconsistent nutrition handoff halts resolution with structured failure. |
| **PPR-D08** | **Budget Contract Semantics** | Explicit validation of `NONE` (no amount), `TARGET` (exact amount required), and `SPEND_LIMIT` (ceiling required) (INV-010). |
| **PPR-D09** | **Kitchen Effort Envelope** | Daily availability envelopes and cook-time ceilings correctly bound daily meal slots without Cartesian leakage. |
| **PPR-D10** | **Snapshot Immutability** | Modifying profile defaults after snapshot resolution leaves the resolved plan policy fingerprint unchanged (INV-028). |
| **PPR-D11** | **Independent Validator** | Validation-owned checker independently reconstructs `ResolvedPlanPolicy` without importing the Policy resolver engine (ADR-010, INV-016). |
| **PPR-D12** | **Adversarial Tamper Detection** | Modifying an embedded nutrition constraint or budget amount within a resolved snapshot is detected and rejected by Validation. |
| **PPR-D13** | **Provenance Fingerprinting** | Exact canonical fingerprinting over all component policies, source versions, actor IDs, and timestamps. |
| **PPR-D14** | **Unverified Transport Boundary** | Serialized policy transport retains `UNVERIFIED_TRANSPORT`; cannot be reused as a trusted validator attestation. |
| **PPR-D15** | **Resource Ceilings** | Input size, field counts, and JSON serialization strictly bounded against memory/CPU exhaustion. |
| **PPR-D16** | **TEST_ONLY Taint** | `TEST_ONLY` environment tag propagated across all resolution contracts; stripped or altered tags fail closed. |
| **PPR-D17** | **Zero Persistence Preservation** | Zero new SQL tables, migrations, or database roles; schema 0017 / 108 preserved. |
| **PPR-D18** | **Closed Production Gate** | `admit_production_resolved_policy()` fails closed with `PermissionError("PRODUCTION_GATE_CLOSED")`. |
| **PPR-D19** | **Export & Hash Preservation** | Preserves all 528 existing exports, 503 historical hashes, and 53 frozen files. |
| **PPR-D20** | **Execution Gate Gating** | Emits `planner_ready=False` and `activation_ready=False`; confers zero authorization to solve or activate plans. |

---

## 11. Dependency Order and Roadmap

```text
[Current State: MTR-006 v2 Structurally Frozen (PR #138/#139)]
                                |
                                v
   [Phase 1: Post-MTR-006 v2 Dependency Review (This Document)]
                                |
                                v
     [Phase 2: Independent Architecture Review & Authorization]
                                |
                                v
   [Phase 3: MTR-008 PlanPolicyResolver Bounded Detailed Design]
       - Specification of PPR-D01–PPR-D20 matrix
       - Schema & contract definitions for ResolvedPlanPolicy
       - Precedence rules and independent validator architecture
                                |
                                v
           [Phase 4: Independent Architecture Approval]
                                |
                                v
         [Phase 5: Bounded Structural Implementation & Tests]
       - Pure Python / in-memory implementation
       - Full regression + PPR acceptance execution
                                |
                                v
           [Phase 6: PR Verification, Merge & Freeze]
                                |
                                v
  [Phase 7: Downstream Planner Candidate Shortlist / Solver Feasibility]
```

---

## 12. Preserved Governance Boundaries

- **PRODUCTION NUTRITION/CLINICAL CONTENT GATE — CLOSED.** No production numerical values, guidelines, protocols, conversion coefficients, seeds or defaults are authorized.
- `planner_ready = False`; `activation_ready = False`.
- **Execution: NOT STARTED; PRECOMMIT FAIL-CLOSED.**
- Full **MTR-006 / MTR-007 / MTR-008 INCOMPLETE**; parent issues **#5 / #6 / #7 OPEN**.
- Nutrition Root, MTR-006 v1, MTR-007, MBA, and MTR-006 v2 structural foundations remain **FROZEN**.
- This review does not authorize implementation, schema migrations, production activation, or parent issue closure.
- The review PR remains **OPEN** with **auto-merge OFF** awaiting independent architecture review.

---

**Disposition:**  
`POST-MTR-006 V2 DEPENDENCY REVIEW COMPLETED / READY FOR INDEPENDENT ARCHITECTURE REVIEW / NO IMPLEMENTATION AUTHORIZED / PRODUCTION GATE CLOSED`
