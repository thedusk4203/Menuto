# Post-MTR-020A dependency review

Review date:2026-10-23. **APPROVED WITH REQUIRED ORDERING CORRECTION.**

Correction reviewed against `a50f7c275793b126d9f4f9d40097a1f3ca00f2e7` (PR69). The user
accepted the capability findings but rejected MTR-019D as the single next prerequisite.
The corrected critical path below supersedes that recommendation; no frozen runtime changes.

## 1. Reviewed baseline and verdict

Reviewed clean `main`/`origin/main`: **87278ed1ea79771f80b09b161ff711ff066556a8**.
MTR-020A is user **FROZEN / APPROVED** at this commit. Schema head is Alembic revision
`0010`, migration `0010_planned_culinary_bindings.py`; registered domain metadata contains
**54 tables**, excluding alembic_version. No migration0001–0010 is changed.

MTR-019A/B/C and MTR-020A remain frozen. Full MTR-019, MTR-020 and MTR-026 are NOT COMPLETE.
MTR-021 and Execution are NOT STARTED. Production PRECOMMIT remains fail-closed.
No concrete defect or contradiction justifies reopening a frozen implementation.

**MTR-020B: BLOCKED.** A semantically useful three-role portfolio cannot currently be built
from canonical EXPLOIT/STRUCTURAL_CHAMPION/EXPLORE inputs. Declaring three buckets, assigning
hash-ordered candidates to them, setting missing signals to zero, or calling missing history
novelty would create unsupported meaning. A contracts-only shell returning unsupported is
possible, but would not implement this capability.

**Next critical-path slice: MTR-040A — Explicit Member Preference Foundation.**
Durable member-owned declarations precede MTR-041 exposure foundation, MTR-024 separable
utility inputs and MTR-020B. See [MTR-040A design](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_REVIEW.md).
MTR-019D is useful optional STRUCTURAL_CHAMPION support, to do later/in parallel; it does not
remove the hard preference/exposure blockers and is not the next prerequisite of MTR-020B.

## 2. Evidence inspected

Canonical requirements: spec [§10.5, §14.4–14.10, §19.1–19.6 and §21](../MENUTO_DEVELOPMENT_SPEC_V1_3.md);
[invariants](../ARCHITECTURE_INVARIANTS.md); ADRs
[001](../adr/ADR-001-band-first-planner.md),
[002](../adr/ADR-002-nutrition-policy-engine.md),
[003](../adr/ADR-003-plan-policy-resolution.md),
[004](../adr/ADR-004-household-first-model.md),
[005](../adr/ADR-005-grounded-recipe-variants.md),
[006](../adr/ADR-006-retail-procurement-abstraction.md),
[007](../adr/ADR-007-spend-limit-robustness.md),
[009](../adr/ADR-009-execution-state-machine.md),
[010](../adr/ADR-010-independent-validator.md),
[011](../adr/ADR-011-behavioral-learning-loop.md).

Planning/status: [backlog](BACKLOG.md), [blueprint](IMPLEMENTATION_BLUEPRINT_M0_M1.md),
[status](FOUNDATION_STATUS.md), [MTR-026 dependency review](MTR_026_DEPENDENCY_REVIEW.md),
MTR-019[A](MTR_019A_CULINARY_BINDING_REVIEW.md)/[B](MTR_019B_VARIANT_GENERATOR_REVIEW.md)/
[C](MTR_019C_CANDIDATE_GROUNDING_REVIEW.md) and
[MTR-020A review](MTR_020A_PARETO_SHORTLIST_REVIEW.md)/[evidence](MTR_020A_PARETO_SHORTLIST_EVIDENCE.md).

Concrete source evidence (repository-relative paths, all at reviewed commit):

| Evidence | What it establishes |
| --- | --- |
| `apps/backend/app/modules/planning/contracts.py`: CandidateGroundingSources, GroundedDishCandidate, ShortlistPolicyDraft | Captured recipe/nutrition/retail/inventory/member primitives; no utility/exposure/role inputs. Current shortlist policy only covers exact supply containment and resource budgets. |
| `planning/shortlist.py`: _comparison/_dominates; `shortlist_capture.py` | Same-context exact source/path containment, no fitness/ranking semantics. Canonical capture precedes pure core; serialized candidate hash is not ingress authority. |
| `preferences/__init__.py`; `learning/{__init__.py,README.md}` | Namespace only; no declared-preference store, behavior profile, attribution router or exposure model. |
| `policy/contracts.py`: ValidationCoveragePolicySnapshot | Explicit FOUNDATION_NO_CLINICAL_POLICY, not NutritionPolicyEngine or PlanPolicyResolver. |
| `app/domain/snapshots.py`: PlannerRequestDraft | Draft nutrition/cost/kitchen axes and meal dates exist; they are not resolved policy, effort facts or utility observations. |
| `recipes/contracts.py`: RecipeFact, RecipeIngredientFact, RecipeVersionSnapshot, VariantReason; `recipes/generation.py` | Stable recipe/method, authored ingredient-slot roles/rules/tiers, mechanical generation triggers. No recipe-level meal-role taxonomy, effort duration/equipment facts, TasteFit or evidence-backed benefit resolver. Ingredient slot role is not a meal/portfolio role. |
| `catalog/contracts.py`: IngredientIdentityFact, NutritionFact; `nutrition/{contracts,models,resolution}.py` | Identity names, raw/cooked mass nutrition, member mass/height and hard restrictions. No ingredient classification/count conversion/root goal policy. Unknown allergen/diet classification blocks grounding. |
| `retail/contracts.py`: PlanningProcurementOptionDraft, SourceCoverageDraft, ProcurementSnapshotDraft, ProcurementSupplyPath; `retail/grounding.py` | Promotion/source-coverage/brittleness primitives and conditional supply coefficients. No freshness/scenario/candidate fragility policy or checkout evaluator. |
| `inventory/{contracts,grounding}.py` | Household lot/basis/expiry/confidence/reservation/ledger-frontier facts; eligible unallocated InventoryCandidateLot paths. No planned consumption allocation or rescued-waste estimate. |
| `validation/contracts.py`; `execution/validation_capture.py`; `planning/public.py` | Partial subject/report and source capture; reports non-authorizing, no production PRECOMMIT issuer. Execution directory/capture functions do not imply execution workflows. |
| `tests/test_candidate_grounding.py`, `test_pareto_shortlist.py`, real-PG counterparts; `tools/check_import_boundaries.py` | Fail-closed unsupported facts, explicit quantity bases, canonical ingress, immutable evidence and no solver/physical side effects. |

The synthetic benchmark is HARNESS_SMOKE_NOT_PLANNER_V4. Its utility/scenario fixture fields
are not production domain sources. Old OPEN labels in the baseline backlog are not proof of
absence/completion; actual code and later user freeze decisions control the assessment here.

## 3. Capability dependency matrix

READY means the named narrow capability can use existing canonical facts. PARTIALLY READY
means raw support exists but a typed derivation/capture/policy seam is absent. BLOCKED means
a required upstream source of truth is missing. A READY sub-primitive does not certify its
containing production capability. Order is a recommended dependency wave, not numeric MTR order
or permission to implement. Critical-path order: C1=MTR-040A, C2=MTR-041,
C3=MTR-024, C4=MTR-020B, C5=MTR-021 (still gated). S marks independent source-support
work before consuming its signal; optional MTR-019D is not ahead of C1/C2.

| Capability | Owner | Existing primitives | Missing primitives | Status | Prerequisite MTR | Recommended order |
| --- | --- | --- | --- | --- | --- | --- |
| 1. ShortlistPortfolioPolicy | Policy defines immutable policy; Planning applies portfolio selection | ShortlistPolicyDraft ID/version, input/frontier limits and exact containment relation | Three-role capacity/eligibility definitions, signal availability handling, duplicate role membership/accounting, protected diversity reserves, overflow/tie rules and binding to supported source snapshots. Existing resource limits are not portfolio quotas. | PARTIALLY READY | MTR-020B policy contract after MTR-024 signal definitions and required source branches; MTR-008 for applicable resolved user axes. No separate existing portfolio-policy MTR. | C3 definitions →C4 selection |
| 2a. EXPLOIT | Preferences/Learning supply signals; Planning selects | Member IDs/participants and exact culinary identities | Member-owned declared/learned affinity, reviewed cold-start priors, evidence strength, shrunk TasteFit/available fit dimensions and provenance. No known neutral baseline source. | BLOCKED | MTR-040 member source; MTR-039 for learned event attribution, MTR-046 for feature priors; MTR-024 separable fit inputs. Explicit direct declarations can precede learned-event routing. | C1 →C3 →C4; learned extensions S |
| 2b. STRUCTURAL_CHAMPION | Domain sources + Planning grounding/portfolio | Exact nutrition composition; unallocated lot matches; retail price/granularity/coverage primitives | Candidate-bound inventory-match evidence; policy-defined nutrient/economic/expiry/fragility comparison where enabled. A's containment witness is not a quality/champion score. | PARTIALLY READY | Optional MTR-019D for inventory-match branch; MTR-006/007/008 for nutrition branch; MTR-011/012/013 and material resolution for economics/fragility. Not all branches must be enabled simultaneously. | S alongside C1–C3 →C4 |
| 2c. EXPLORE | Learning/Preferences sources; Planning portfolio | Recipe/version/method identities and candidate fingerprints | Authoritative exposure coverage/frontier, novelty/feature-fit inputs, cold-start priors, evidence availability and bounded exploration policy. Absence of an exposure implementation is not proof of never tried. | BLOCKED | MTR-041 exposure source + MTR-040 priors/affinity + MTR-046 features; MTR-039 where events contribute; MTR-024 input vector. Cross-horizon provisional exposure additionally MTR-038/017. | C1/C2 →C3 →C4 |
| 3. Preference / TasteFit | Preferences, member-owned; Learning attribution | HouseholdMember identity, MealParticipants, exact recipe/ingredients | Explicit preference source and correction semantics; direct/feature affinity, evidence strength, prior/shrink policy and member aggregation. Hard ingredient exclusion is not taste. | BLOCKED | MTR-040; MTR-039 for learned evidence; MTR-046 feature vocabulary/priors; MTR-024 fit derivation. Do not require Execution to store an explicit declared preference. | C1 →C3 (member affinity); other sources S |
| 4. Adherence vector | Source domains; MTR-024 utility boundary | Ingredient counts/quantities, methods and serving/batch intent identities | Separate time/equipment/complexity/ingredient-count/batch/schedule/repeat/novelty fit facts, applicability, source provenance and policy. Raw count is not fit; no canonical scalar adherence truth. | BLOCKED | MTR-024 input/vector foundation after MTR-008/046 effort/context and MTR-040/041/039 applicable member signals. Actual batch-fit extensions need MTR-023 planning facts, not execution success as taste. | S →C3 when that dimension is enabled |
| 5. Recent exposure / repeat cooldown | Learning, member-scoped; projection lineage separate | Recipe ID/method, scheduled MealIntent/plan revisions, participant IDs | Exposure events with confirmation/provisional/reversal status and actor scope; completeness window/frontier; multi-level family/protein/flavor identity; versioned repeat/decay policy. Scheduled meals do not prove eating. | BLOCKED | MTR-041; MTR-039 attribution; MTR-046 descriptors; MTR-038/017 for horizon/provisional extensions. Later actual execution may supply confirmed events, but must not be started for this review. | C2 after C1; horizon extension S/later |
| 6. Kitchen effort / schedule convenience | Household kitchen/context + Policy; authored recipe descriptors | Draft KitchenEffort axis, meal/batch timestamps, recipe method/procedure | Authored prep/cook/active time, equipment and effort descriptors; household equipment/daily availability source; versioned compatibility/fit policy. Method text cannot establish minutes/equipment. | PARTIALLY READY | MTR-008 resolved KitchenEffort/DailyAvailability + MTR-046 reviewed recipe coverage/effort facts (Recipe-owned companion); MTR-024 separable fit inputs. | S →C3 when that dimension is enabled |
| 7. Nutrition / goal fit | Nutrition/Policy; participant-specific allocation | Reviewed EP_RAW_G/COOKED_G references, exact input-composition totals, servings/participants, member mass/height | Eligible root goal/guideline source, applicable per-role/meal/serving demand and member allocations, supported resolution/comfort/weekly policy. Protein amount alone is not fit or health approval. | PARTIALLY READY | MTR-006 root/goal policy →MTR-007 resolution + MTR-008 policy binding; MTR-005 member allocation boundary/MTR-019 grounding extensions; MTR-046 culinary roles where used. | S before enabling nutrition signal; independent root enforcement MTR-026 |
| 8. Structural economics | Retail/Shopping/Inventory facts; global Planning economics | Money/reference AP quantity, mapping yield, fixed/catch/loose coefficients, inventory and batch intent | Granularity-specific purchase cost and explicit quantization, marginal/shared package/lot/batch decision context, waste/carryover policy and stress scenario evidence. No legitimate per-dish checkout cost. | PARTIALLY READY | Remaining MTR-011/012 cost-resolution seam →MTR-013 scenarios; MTR-008/009 budget context. True marginal economic effects belong to later MTR-021/022 material/global decisions; shortlist must not recreate that solver. | S before enabling economic signal; global decisions later, no solver inside shortlist |
| 9. Inventory / expiry-rescue signals | Inventory owns stock; Planning owns derived candidate-match context | Confirmed active lots, exact usable basis/quantity, retained AP→EP mapping, usable_until, reservations and captured frontier | Typed candidate-bound unallocated match witness/reason; for expiry-rescue additionally planned-use time, urgency policy/window and resolved consumption/competition before claiming rescued quantity/waste. | PARTIALLY READY | **MTR-019D proposed inventory-match-only slice** reusing frozen MTR-015/C; expiry urgency later MTR-019 policy extension, MTR-008 schedule context; actual saved quantity requires MTR-021/023 planned allocation/global replay. | Optional S; rescue later |
| 10. Procurement fragility signals | Retail facts; Planning derives candidate structural context | Promotion derived from observation; retailer/provider/path coverage; package brittleness assessment/version; granularity/bounds and provenance | Candidate-demand-specific eligible coverage, comparable package sensitivity, freshness/source-quality eligibility and versioned fragility interpretation. Existing counts need not be resolved candidate-eligible coverage. No calibrated probability. | PARTIALLY READY | Remaining MTR-011 builder/fragility and MTR-012 quality/evidence policy; MTR-013 deterministic scenarios for spend-stress claims; MTR-019 signal handoff. | S →C3 when that dimension is enabled |
| 11. Evidence-backed generation / shortlist reasons | Planning contextual grounding, not Recipe authoring | Frozen B DEFAULT/AUTHORED_SELECTION/INGREDIENT_TARGET triggers; C nested evidence; VariantReason enum in older culinary draft | Reason-to-candidate/source/cutoff witness and deterministic predicates; explicit distinction between selection hint, source possibility and demonstrated benefit. Enum existence is not proof. | PARTIALLY READY | Optional **MTR-019D** inventory-match support; later MTR-006/008 nutrition, MTR-011/012/013 price/package and expiry policy branches. Portfolio-selected-for-role reasons later MTR-020B must cite the actual policy/signal. | S alongside critical path; role reasons C4 |
| 12. Allergen / diet classification | Catalog reviewed source; Nutrition canonical member enforcement; Validation independent | Member ALLERGEN/DIET_RULE codes, ingredient IDs, EXCLUDED_INGREDIENT enforcement | Reviewed positive/negative/unknown ingredient classification; controlled code vocabulary, semantics/version/provenance and coverage. Ingredient names and feature tags cannot substitute. | BLOCKED | MTR-046 proposed ingredient-safety classification source scope + MTR-005 enforcement seam; MTR-026 independent check. Existing MTR-046 coverage wording alone does not implement that source model. | S; required before admitting affected candidates |
| 13. COUNT nutrition / count-to-mass | Catalog authored item definition/nutrition; neutral Units; Recipe retains ownership of culinary quantity | COUNT item_ref identity; explicit recipe count requirement; current nutrition source permits only edible raw/cooked mass | Authored item_ref-specific mass/edible basis or reviewed count nutrient reference, version/provenance, applicability/uncertainty/quantization rules; no generic unit magic. | BLOCKED | MTR-003 count measurement-source contract + MTR-046 authored catalog truth, MTR-014 yield-boundary compatibility, MTR-019 grounding extension. COUNT substitutions remain prohibited under frozen Recipe policy. | S; required before COUNT candidate eligibility |
| 14a. Deterministic identity/ties and preservation of current distinctions | Planning/Recipe immutable contracts | Frozen A/B/C hashes, exact recipe/method/rule/tier/source identities; canonical serialization, duplicate/tie handling and resource overflow in A | None for this narrow identity/preservation sub-capability. It proves no novelty/preference/quality. | READY | Frozen MTR-019A/B/C + MTR-020A; no new prerequisite for keeping these identities | Existing, preserve |
| 14b. Semantic diversity / protected reserve rules | Catalog/Recipe descriptors; Policy definition; Planning selection | Existing recipe ID/method and preserved culinary differences | Reviewed role/family/protein/flavor descriptors and candidate-path applicability; explicit reserve/overlap/capacity/overflow rules, signal availability handling and policy provenance. Ingredient-slot role cannot stand in for dish role; structural diversity is not behavioral novelty. | PARTIALLY READY | MTR-046 descriptors + MTR-020B policy; MTR-024/040/041 only for utility/exposure-based reserve labels. A restricted future ID/method-only diversity reserve can be designed without claiming learned roles. | S descriptors →C3/C4 policy |

## 4. Corrected immediate priority: MTR-040A

The original recommendation optimized for an easy available evidence branch rather than the
hard dependency. Three-role MTR-020B needs member affinity for EXPLOIT and covered exposure/
novelty semantics for EXPLORE. An inventory-match witness supplies neither. Therefore the next
slice is **MTR-040A**, not MTR-019D.

Design durable, explicit member-owned declarations for ingredient/protein/method/flavor/direct
recipe targets, evidence strength/provenance and append-only replacement/retraction. No learning,
inferred preference, Execution, TasteFit scalar or copied household preference. MTR-040A uses
canonical MTR-040 ownership; its minimum reviewed feature vocabulary does not invent ingredient/
recipe feature classification. The [focused design](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_REVIEW.md)
separates storage of a declaration from later candidate feature matching and utility derivation.

MTR-019D remains a valid optional side slice: derive non-exclusive inventory-match evidence from
captured confirmed lot possibilities; no reservation/allocation, expiry-rescue or global benefit
claim. It may be done later/in parallel after approval, but must not displace preference/exposure
on the critical path. No MTR-019D implementation is requested or started.

## 5. Corrected dependency order

```text
MTR-040A Explicit Member Preference Foundation
    ↓
MTR-041 Exposure Foundation
    ↓
MTR-024 Separable Utility Inputs
    ↓
MTR-020B Role-aware Portfolio (EXPLOIT / STRUCTURAL_CHAMPION / EXPLORE)
    ↓
MTR-021 Feasibility — still subject to its independent input/validation prerequisites

Support branches before the corresponding dimension is enabled:
  MTR-046 reviewed features/classification/count sources
  MTR-006/007/008 nutrition/goal/kitchen policy
  MTR-011/012/013 procurement quality/economics/scenarios
  MTR-039 learned attribution (not required for explicit declarations)
  optional MTR-019D inventory-match signals, later/in parallel
```

MTR-040A alone does not unblock MTR-020B. Exposure remains MTR-041's separate truth; declaration
absence is not novelty. MTR-024 captures separable supported inputs; it does not manufacture
missing fields. Full Stage-1/2 objective composition stays in later Planner V4. Unknown dimensions
remain unavailable, not zero. MTR-019D cannot stand in for any of these missing behavioral sources.
No Execution implementation is required to persist an explicit member declaration.

## 6. Direct answers and counterexamples

**Can valid MTR-020B be implemented now? NO for the requested semantic role-aware portfolio.**
Basic recipe-ID/method diversity and an empty quota contract are possible now, but cannot truthfully
produce EXPLOIT or EXPLORE and would not close the requested gap. No fake scalar utility is needed.

**Does full MTR-019 need further slices? YES; does it precede MTR-040A? NO.** Evidence-backed
benefit/context reasons and wider grounding quality coverage remain incomplete. MTR-019D can
address one optional inventory branch later/in parallel; completing full MTR-019 is not the next
critical-path task. COUNT/classification remain conditional eligibility blockers for affected
candidates, not a reason to delay the explicit preference source.

**Can full MTR-020 finish now? NO.** Multi-role inputs, source availability/quality and portfolio
policy/reserve semantics are absent. Frozen A only preserves contained supply-evidence choices.

**Is MTR-021 allowed to start? BLOCKED / NOT STARTED in this task.** Beyond this explicit scope
gate, canonical root nutrition/goal policy, supported procurement scenarios/quantity cost, exact
planned material allocations/causal batch flows and required independent checks are incomplete.
A conservative shortlist or inventory-match witness cannot certify hard feasibility. Future
MTR-021 input-contract prerequisite work may be reviewed separately; no solver is authorized here.

**Migration required? None for this documentation correction/design.** MTR-040A needs durable
member-owned preference sources and is designed for forward migration **0011** after architecture
approval. No migration is created here and0001–0010 remain unchanged. Optional transient MTR-019D
still would not require persistence; this does not determine priority.

Counterexamples checked against current source/tests:

- No preference rows/implementation: UNKNOWN, not TasteFit=0, disliked, or population prior.
- No exposure model: UNKNOWN coverage, not never tried; scheduled meal is not confirmed exposure.
- Cooked successfully / swapped because NO_TIME / stock unavailable: not taste evidence
  (INV-023/024); a forced compromise is not voluntary preference (INV-029).
- Protein40g for two dishes: neither has proven goal fit without role/member policy/allocation.
- Quote60000/1000g and500g pack: preserve reference pair; no60000 package cost or per-dish checkout.
- Several supply paths but one retailer/provider: not independent backup coverage/probability;
  old source coverage is not automatically an eligible candidate fragility score.
- Two candidates match the same50g lot: both may have non-exclusive match witnesses; neither
  owns50g, and their sum does not create100g. Reservations are not physical movement.
- usable_until is near as_of: not expiry rescue without use time/urgency/allocation evidence.
- Substitute changes chicken to tofu: feature/role safety cannot be inherited by name or guessed
  from base recipe; exact selected ingredient/path facts govern future descriptors.
- Member has ALLERGEN/DIET_RULE restriction or COUNT nutrition lacks source: C remains INCOMPLETE;
  missing classification/conversion is not false/zero/implicitly safe.
- A candidate dominates under frozen A: only exact conservative supply-evidence containment,
  never a label meaning healthier, cheaper, tastier or globally feasible.
- Hash/capacity/COMPLETE shortlist result: no PRECOMMIT authority; unknown critical sources remain
  fail-closed. Past material facts, AP→EP Retail yield and Recipe cooking yield remain separate.

Applicable invariants: INV-001–009,011–013,015–021 and022–030; particularly INV-023/024/026/027/028
for separable member utility, INV-017/018 for evidence identity/basis, and INV-019/030 for deferred
causal feasibility/exposure. No canonical wording or accepted ADR is changed.

## 7. Review verification and stop boundary

Head/table count verified from Alembic revision graph and registered SQLAlchemy metadata.
Source searches and contract inspection establish absence of the listed preference/learning/policy
implementations; directory names and draft fields are not treated as completed capabilities.
Executed locally: **156 existing tests passed** across architecture, baseline, frozen shortlist
and candidate grounding (workspace basetemp). Architecture baseline30 invariants/11 ADRs/50 tasks,
16-context import boundaries, domain-schema and OpenAPI drift checks all PASS. No PostgreSQL-local
rerun is claimed for this documentation-only change. Frozen baseline full-suite/real-PG evidence
remains in [MTR-020A evidence](MTR_020A_PARETO_SHORTLIST_EVIDENCE.md); PR CI independently runs the
full configured suite on this documentation revision before delivery.
No new test, production-code, migration or domain-schema change is needed to prove these findings.
Frozen A implementation/evidence remain untouched; only current status documents acknowledge the
user freeze. This review implements no preference/learning/role policy. The approved ordering correction is
recorded; MTR-040A implementation still awaits review of its focused design.

**READY FOR ARCHITECTURE REVIEW**
