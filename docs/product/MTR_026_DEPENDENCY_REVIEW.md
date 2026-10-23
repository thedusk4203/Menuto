# MTR-026 Independent Validator — dependency review

Review date: 2026-10-23. **Architecture proposal only; awaiting architecture approval.**

## 1. Reviewed boundary and conclusion

Reviewed `main` and `origin/main`: **219b55658e1e67dca4f9f90356f610ffcac8e946**.
MTR-025 ValidationSubject v1 is **FROZEN / user APPROVED** at this commit. Its
`validation-subject.v1-foundation` coverage, hashes, contracts and non-authorizing semantics
remain unchanged. The previous submission's PARTIAL production-coverage wording does not
override the user's freeze acceptance of this foundation. MTR-016 remains frozen too.

Alembic has one head, **0009** (`0009_plan_revision_semantic_corrections.py`), and registered
domain metadata has **52 tables**, excluding `alembic_version`. The existing real-PostgreSQL
schema assertion was rerun in this review. No migration, runtime code or frozen test was changed.

**MTR-026 cannot be completed now as one validator-only implementation.** Some independent
checks can be written from existing primitives. Other checks lack authoritative domain facts;
the validator must not manufacture these facts, invoke a planner, or query live sources.
Keep PRECOMMIT fail-closed and POSTFACT diagnostic. Execution is not the next task.

The canonical identifiers below come from [BACKLOG](BACKLOG.md), not GitHub issue numbering.
Sub-slice names in this review are proposed scopes under those existing MTR IDs, not newly
invented milestones or claims that those scopes are already implemented/approved.

## 2. Evidence inspected

- Spec V1.3 [§8.4, §9.3, §10.3, §12–14, §16.3 and §18](../MENUTO_DEVELOPMENT_SPEC_V1_3.md);
  [invariants](../ARCHITECTURE_INVARIANTS.md), especially INV-003–007,011–013,015–021,030.
- [ADR-002](../adr/ADR-002-nutrition-policy-engine.md),
  [ADR-003](../adr/ADR-003-plan-policy-resolution.md),
  [ADR-005](../adr/ADR-005-grounded-recipe-variants.md),
  [ADR-006](../adr/ADR-006-retail-procurement-abstraction.md),
  [ADR-007](../adr/ADR-007-spend-limit-robustness.md),
  [ADR-009](../adr/ADR-009-execution-state-machine.md),
  [ADR-010](../adr/ADR-010-independent-validator.md).
- [Blueprint](IMPLEMENTATION_BLUEPRINT_M0_M1.md), [status](FOUNDATION_STATUS.md),
  [M1.3 review](M1_3_INVENTORY_DOMAIN_REVIEW.md),
  [MTR-025 review](VALIDATION_SUBJECT_FOUNDATION_REVIEW.md) and
  [evidence](VALIDATION_SUBJECT_FOUNDATION_EVIDENCE.md).
- Actual modules: `validation/{contracts,public,material}.py`,
  `execution/{validation_capture,public}.py`, `planning/{contracts,models,public}.py`,
  `recipes/{contracts,calculations,repository}.py`, `retail/contracts.py`,
  `inventory/contracts.py`, `nutrition/{contracts,models,public}.py`,
  `catalog/{contracts,models,public}.py`, `policy/contracts.py`, migrations0007–0009,
  import-boundary checks, schema export and validation/plan/PostgreSQL tests.

Graphify was used for source discovery only. Its graph was built at `536785a…`; its edges
describe accepted requirements, not current completion. Every conclusion below was checked
against current source. Synthetic benchmark scenario/policy classes are not production truth.

## 3. Capability dependency matrix

READY means the scoped check has every required canonical primitive. PARTIALLY READY means
useful checks exist or are possible, but a capture/ownership contract still needs design.
BLOCKED means the full capability is missing an upstream source of truth. A READY sub-check
does not make its containing production capability READY. Order numbers refer to §5.

| Capability | Existing canonical primitives | Missing primitives / boundary | Classification | Exact prerequisite backlog scope | Order |
| --- | --- | --- | --- | --- | --- |
| 1. Root Nutrition Policy | Member identity; `MemberNutritionProfile` mass/height + row_version; canonical safety; ingredient nutrition references; orthogonal request axes | Eligibility/guideline evidence, goal source, applicable root contracts, resolved daily/weekly envelopes, policy selection/version and member/day nutrient allocation. `ValidationCoveragePolicySnapshot` explicitly says NO_CLINICAL_POLICY. | **BLOCKED** | **MTR-006 NutritionPolicyEngine** source/root-policy foundation; **MTR-008 PlanPolicyResolver** compiled binding; **MTR-007** resolution facts where used. MTR-019 exact allocations are needed to evaluate actual plan totals. | 2, then 3/6 |
| 2. Allergen / diet-rule classification and enforcement | Member ALLERGEN/DIET_RULE codes; EXCLUDED_INGREDIENT IDs; MealParticipants; catalog Ingredient identity | Reviewed ingredient classification, code vocabulary/rule semantics, explicit known/unknown coverage and provenance, plus exact selected ingredient paths. Ingredient name is not classification evidence. | **BLOCKED** | **MTR-046 Catalog coverage**, proposed ingredient-safety classification source sub-slice, coordinated with **MTR-005 MealParticipants canonical safety resolution** and MTR-006 eligibility. MTR-046's current coverage-matrix criterion alone is insufficient; approve this explicit source-model scope first. No dedicated allergen-classification MTR currently exists. | 2, then 3/6 |
| 3. Exact grounded recipe/ingredient binding | Sealed `RecipeVersionSnapshot`; contextual rules/combinations; tiers/scaling/adjustment; `ResolvedRecipeIngredient`; `GroundedRecipeVariantDraft`; corrected COUNT and transformation-path policy | Plan batch binds only recipe_version/tier/planned_servings; no selected-rule/delta/quantity/fingerprint association to exact batch. Draft culinary binding is not full nutrition/retail grounding. Need versioned capture handoff, not solver invention. | **PARTIALLY READY** | **MTR-019 Grounded Variant Generator**, narrow explicit culinary-binding handoff only, using frozen **MTR-018** authored truth; **MTR-026 RecipeGroundingValidator** independent enforcement. Full demand-driven generation is not required to verify an explicitly supplied selection. | **1** |
| 4. Procurement scenario validation | Reviewed Product→Ingredient maps; package granularity; offers/reference/calibrated-reference price pairs; ProcurementClass/members/options; primary/backup rank and availability evidence | Selected purchase quantities/path and granularity-specific cost evaluation; required scenario set, deterministic coefficients, category correlation/evidence policy, budget-policy binding; actual-spend/unfulfilled allocation for revisions. None is captured by current subject. | **PARTIALLY READY** | **MTR-011/012** production procurement quantity/cost-resolution seam → **MTR-013 SPEND_LIMIT stress scenarios** + **MTR-008** budget contract. **MTR-034 quantitative fulfillment** prerequisite for sunk-spend revision checks; do not implement its execution workflow now. | 3, revision extension later |
| 5. Planned material allocation validation | Physical lots/events/positions; plan reservation intents; batch→meal serving allocations; quantitative shopping contributions; retail and recipe yield facts | Exact requirement→source-lot/planned-acquisition allocations, quantity/basis chains and explicit planned flow identities; no correspondence from reservation quantity to a recipe requirement. Shopping demand is not projected acquisition or owned stock. | **BLOCKED** | **MTR-019** exact binding → **MTR-023** planned batch input/output/allocation contracts; **MTR-015** inventory-resolution seam and **MTR-021** feasibility input/resolution subset. MTR-013/011 procurement acquisition facts where purchasing is required. These are planning contracts, not execution or optimization. | 3/4 |
| 6. Revision/materialization boundary validation | Current/parent revision and proposal graph, scope/effective_from; DB historical anchors/closure checks; `PlanMaterializationLink`, `PlanRevisionReservation` and boundary counter exist | Current subject carries no materialization-link collection, pinned source graphs or prior reservation ownership links; a counter cannot identify what is pinned. Initial draft-to-draft baseline is not captured either. Full fulfillment/batch facts do not exist. | **PARTIALLY READY** | **MTR-026 RevisionBoundaryValidator** + **MTR-016** read-only source handoff of existing links/required historical graphs; no redesign of frozen revision semantics. **MTR-034/023** later supply richer actual purchase/batch facts. | 1b/4 |
| 7. CookingBatch / prepared-food validation | Distinct raw/component/dish InventoryLots; prepared SERVING identity; planned batches/allocations; net recipe yield; `BatchFlowLinkDraft` | Authoritative exact input/output movement relationships, resolved batch composition, produced_servings, actual member consumption and conservation/loss accounting. Draft arrays are not a confirmed transformation aggregate. | **BLOCKED** | **MTR-023 CookingBatch/PreparedFood**, first a planned/resolved material-flow contract subset after MTR-019, then independent BatchFlow checks. Actual execution source model/workflows belong to later approved MTR-023 execution scope, not this review. | 4; POSTFACT execution later |
| 8. Assumption graph validation | Physical ledger explicitly excludes inference; source types and compensating physical corrections exist | Operational assumption identities, confirmed/provisional status, causal parents/dependencies, reversal/conflict rules, policy and captured graph. Physical correction_of is not an assumption parent. | **BLOCKED** | **MTR-017 Execution state projections** contract/source boundary → **MTR-036 Assumption graph + compensation**. Needs a separate approved architecture slice; do not generate assumptions in validation. | 5, no implementation now |
| 9. Horizon / carryover replay | Horizon, active revision commitments draft, exact scheduled/planned times; physical stock/expiry/reservations | PlanningState reconciliation; resolved pre-start future transformations/consumption; projected opening assets/exposure with lineage and unique contribution IDs. Current physical stock is not a projected opening balance. | **BLOCKED** | **MTR-017** projection contracts + **MTR-023** planned flow → **MTR-038 HorizonBridgeResolver**; **MTR-036** if assumptions contribute. No solver or execution workflow is required merely to define these immutable inputs. | 5 |
| 10. Production PRECOMMIT authorization | Unmintable authorization table; exact proposal seal/hash; revision CAS/actor/expiry/frontier checks; single-use authorization FK; reports always non-authorizing | Complete required-capability evaluation, trusted report provenance, source manifest/frontiers, issuer privilege boundary, policy binding and atomic recheck/consume protocol. `0 ERROR` alone would not prove coverage. | **BLOCKED** | Required source sub-slices above → **MTR-026** complete enforcement and production issuer/commit guard, coordinated with **MTR-016** publish seam and **MTR-027 Planner API** authority boundary. No new standalone authorization MTR exists; approve this named scope under MTR-026. | **6, last** |
| 11. TOCTOU source-frontier recheck | RR/SERIALIZABLE read-only capture; current revision, HH inventory ledger frontier (movements + reserves + releases), materialization boundary; HH inventory advisory write fence | Authoritative safety/membership/profile/classification/policy frontiers and source-set completeness; all-writer fencing; trusted manifest/policy selection; fresh locked recheck + receipt binding. Current frontier is not a full source revision. | **PARTIALLY READY** | **MTR-026/MTR-016** source-manifest/commit protocol, with writer hooks owned by **MTR-004/005/006/008/046** sources; inventory part reuses frozen MTR-015 fence. Implement metadata/frontiers only after approval; authority stays blocked until row10 is ready. | Design now; source hooks 2–5; activate only 6 |

### READY work that does not need missing domain truth

1. Independent authored culinary checks from RecipeVersion + explicit selected rule IDs,
   requirement deltas and tier: rule ownership, one rule/slot, structural-combination limit,
   exact quantity/basis/item_ref, adjustment bounds/steps, tier/serving identity and resolved
   transformation path. Do not call `resolve_culinary_binding` or trust its cached output.
   Primitive structures already exist; integration into a plan-specific capture remains row3.
2. Parent/current graph historical-anchor and old/new dependency-closure checks for captured
   active revisions. Existing graphs/scopes/cut lines suffice; materialized pin replay and
   initial draft-generation checks need row6's extra source capture.
3. Canonical excluded-ingredient safety for current authored default paths; current physical
   conservation, chronological nonnegative stock, expiry and separate reservation accounting;
   context-specific Retail AP→EP and Recipe EP_RAW→COOKED arithmetic. Already supported by
   the foundation; they are not complete grounding, meal nutrition or future material flow.
4. Retail evidence-origin, package-bound and price-reference-pair consistency can be checked
   independently from existing retail facts. It cannot prove a basket total or robust budget.

Unknown/ambiguous references remain unresolved, not a guessed provider selection. COUNT→mass,
cross-basis conversion and cooked nutrition retention are not synthesized inside validation.

## 4. Ownership and dependency rules

Nutrition owns member source records; policy owns guideline/goal/compiled policy definitions.
Catalog owns reviewed ingredient classifications/nutrition references; its coverage explicitly
distinguishes unknown from reviewed absence. Recipe owns authored culinary possibilities.
Grounding/application orchestration owns exact selection/capture, never policy enforcement.
Retail owns edible yield, package/price/scenario evidence; shopping owns quantitative demand
and eventual fulfillment. Household inventory owns physical lots and immutable movements.
Planning owns intent/revisions/links; future execution owns confirmed batch/meal facts;
operational projection owns assumptions. Validation owns independent enforcement/findings.

Capture/orchestration may query source public facades. Validation consumes immutable captured
contracts only: no DB, ORM, live source facade, solver, generator, objective, repair or LLM.
Shared neutral types/immutable definitions are allowed; shared enforcement calculators are not.
Root safety is canonical participants × member restrictions × exact selected ingredients,
including substitutes/prepared composition, never a planner `is_safe` summary.

No duplicated truth or generic conversion/event persistence is proposed. Raw facts retain
source IDs, scope/household relationships, measurement basis and provenance. Safety/policy
data must not be smuggled into a JSON blob or encoded by arbitrary context strings.

## 5. Recommended order and next slice

**Recommended next implementation: MTR-019 explicit culinary-binding handoff + MTR-026
independent RecipeGroundingValidator, as a narrow contract/checking sub-slice.**

This has the strongest existing primitive support and removes default-only ingredient
ambiguity needed by safety, nutrition and material validation. It does not need a full
VariantGenerator, candidate search/ranking, optimizer, execution or invented nutrition policy.
Bind `(household, plan, proposal, batch_node)` explicitly to exact RecipeVersion/tier,
selected authored rules, per-requirement deltas, resolved quantities and transformation IDs.
Independent checks recompute all claims. Reason labels remain authored/selection explanation,
not evidence of price/nutrition/inventory benefit. Keep COUNT substitution forbidden.

Preserve frozen MTR-025 wire/hash behavior. A future approved companion capture contract or
new explicitly versioned aggregate can reference the frozen subject hash and carry new
primitive facts. Never mutate v1's literals, silently append production facts to v1, or
canonical-sort an embedded GroundedVariantDraft then trust its old fingerprint. No new
persistence is inherently needed for this verification-only handoff; durable binding ownership
can be designed later if activation genuinely requires it.

Recommended implementation order (not authorization to begin it):

1. Exact culinary input handoff + independent grounding check above. **1b:** independent
   captured parent-graph scope/history checks; then read-only existing-pin/link handoff.
2. In parallel dependency branches: MTR-006 root-policy/source foundations + MTR-008 compiled
   policy binding; MTR-046 ingredient-safety source + MTR-005 canonical enforcement input.
   Evidence for guideline constants remains an explicit review gate, not fixture defaults.
3. MTR-011/012 quantity/cost resolution + MTR-013 scenario snapshots; exact member/meal
   nutrient allocations and independent root/nutrition/safety/scenario checks.
4. MTR-023 planned resolved batch-flow + MTR-015/021 material allocations; independent causal
   feasibility and revision-pin checks. Planned outputs stay projection facts, not InventoryLots.
5. MTR-017/036 assumptions/projection inputs and MTR-038 horizon lineage/replay, when approved.
6. Complete capability coverage + production source-frontier hooks + TOCTOU/authority commit
   protocol. Only then may PRECOMMIT authorize supported intent. Later actual execution
   supplies POSTFACT source facts; execution must be preceded by checks for its own commands.

This avoids a false dependency cycle: planned batch-flow verification can precede execution.
Actual batch/meal history cannot be diagnosed before its source model exists. Do not claim
all ten validators complete by treating empty actual/assumption graphs as implicit success.
Any future narrower production profile needs explicit approved applicability rules and proof
that unsupported facts cannot enter; this review does not authorize such a bypass.

## 6. Canonical serialization audit

`app/domain/canonical.py` recursively sorts **every** tuple/list by canonical JSON; dictionary
keys are sorted at serialization. It is an unordered-fact encoder, not a universal sequence
encoder, and does not deduplicate. Source identity, multiplicity, Decimal normalization,
UTC timestamps and version tags remain represented. The subject hash includes proposal IDs,
recording metadata and provenance: it is not a cross-import culinary equivalence fingerprint.

Current frozen subject collections can safely be canonical-sorted for its declared semantics:

| Current collection | Why order is not implicit meaning |
| --- | --- |
| Members, per-member safety facts, ingredient identities, nutrition references, recipe versions | Identity-addressed fact sets; ambiguity/duplicate sources are rejected, never resolved by first list entry. |
| Recipe ingredients, tiers/tier quantities, rules, approved rule-ID combinations, transformations | Requirement/rule/tier/transformation IDs encode relationships. Combinations are sets. Procedure is a single ordered string, retained verbatim; there is no ordered multi-step prep array. |
| Plan meals/batches/allocations/shopping/contributions/reservations; meal participants | Stable node/member IDs encode relationships. Scheduled/planned/need-by timestamps carry temporal intent; tuple order does not. Frozen plan-intent.v1/v2 own graph hashes remain untouched. |
| Inventory lots/positions/movements/reservations/releases | Identity fields and `(occurred_at, phase, ledger_sequence)` define causality. Replay sorts by those fields independently. UUID/list order is never event order. |
| Nested Retail mapping/price provenance and coverage policy | Scalar facts/identities; no positional sequence currently enters via these fields. |

Future ordered data **must not rely on array position** under this generic sorter:

- Procedure/preparation steps: stable step ID + explicit ordinal/dependency edges; unique
  ordinals or a separately specified ordered encoder. RecipeVersion is not a multi-step engine.
- Event replay/action traces and compensation chains: explicit causal parent, effective time,
  phase/sequence. Sorting bytes is not an execution schedule.
- Ranked alternatives/scenario evaluation priority: explicit rank/scenario ID. Existing retail
  option rank already preserves primary/backup meaning, but options are not in v1 subject.
- Batch input/output pairings: use relationship records containing lot ID **and** movement ID,
  plus quantity/basis/role. `BatchFlowLinkDraft` currently has parallel lot/movement arrays
  outside the subject; independently sorting those arrays would erase pair association.
- Embedded `GroundedRecipeVariantDraft`: its own fingerprint deliberately retains authored
  snapshot tuple order. It is outside the current subject. A future wrapper must preserve that
  wire fingerprint or define an explicit new encoder/version, not reuse generic sorting blindly.
- Proof paths/traces: explicit ordinal/parent if path order matters; do not hash an ordered path
  as a set of proof refs. New fields require a collection-by-collection semantics audit.

Counterexamples are reproduced in `test_validation_canonical_review.py`: implicit
`[boil,drain]` and `[drain,boil]` hash equally under the unordered encoder; explicit ordinals
distinguish them. Parallel arrays also collide when pairings are swapped, while relationship
records do not. These future shapes are **not** accepted frozen subject fields. No concrete
defect in current MTR-025 scope was found, and no frozen serialization was changed.

## 7. Future production TOCTOU protocol — design, not implementation

TOCTOU means data can change between checking it and using that check to authorize a write.
Read-only REPEATABLE READ gives coherent capture, not freshness until commit. Current
`ValidationSourceFrontier` contains only revision, inventory sequence and boundary counter.
`plan_validation_authorizations` stores hashes/validator version plus inventory/boundary/expiry;
`menuto_plan_revision` checks proposal/frontiers/expiry. It does not implement complete
safety/policy freshness. `menuto_plan_no_authority` rejects every production receipt insertion.
Do not remove that trigger merely because some checks return no errors.

### 7.1 Authoritative source manifest

Future capture must include immutable source versions/content hashes plus authoritative
selection/completeness frontiers for all inputs used by the relevant production profile:

- plan head, sealed proposal hash, pinned historical graphs and materialization links;
- HH inventory **and reservation/release** frontier (reuse the current HH writer fence);
- member/participant identity, canonical restriction-set frontier, profile/root-policy inputs;
- reviewed classification/reference-set identity, exact selected RecipeVersion/binding facts;
- active guideline/compiled policy/scenario selection and resolved version/hash;
- applicable fulfillment, projections/assumptions and horizon inputs once implemented.

An immutable row ID alone does not prove that a newer applicable policy/reference or a new
restriction has not appeared. Capture source-set completeness and active-selection identity.
An empty restriction set also needs a protected frontier: locking existing restriction rows
cannot stop a new-row phantom. Use monotonically advancing authoritative generations with
content digests; all INSERT/UPDATE/DELETE/bulk writers participate, even when content changes
back (ABA). Source capture times and policy pointers are not supplied by an untrusted caller.

### 7.2 Capture → validate → fresh locked recheck → authorize/publish

1. **Capture:** read-only RR/SERIALIZABLE transaction through source public facades. Freeze
   primitive facts, exact policy selection, subject hash and complete source manifest. End
   capture transaction; never pass a live session into validation.
2. **Validate:** pure independent enforcement. Return immutable report binding subject hash,
   policy/profile identity, evaluator/capability version and findings. Missing required
   capability, unknown safety, FATAL or ERROR forbids authorization. POSTFACT never issues it.
3. **Commit boundary:** trusted application authority starts a new transaction. Use fresh
   READ COMMITTED reads after acquiring writer fences, or an explicitly proven serializable
   protocol that conflicts/retries stale snapshots. Reusing capture's old RR snapshot is wrong.
   Require all writers to use the same protected source generations/fences; checking counters
   without holding their writer locks until COMMIT leaves another race.
4. **Lock/recheck:** define one global lock order for policy/catalog scopes, then HH inventory/
   safety scope, then plan head. Preserve the existing HH-before-plan order. Reread trusted
   proposal/head, every source generation/selection/hash, materialization boundary and deadline.
   The exact new cross-source lock order/writer hooks require approval and concurrency tests.
   Any inventory/safety/policy mutation committed after capture invalidates authorization;
   changes begun during recheck must block or produce serialization failure/retry, never slip
   between comparison and COMMIT. Newer applicable data or source deletions also invalidate it.
5. **Authorize and publish atomically:** only the trusted issuer may append a one-use receipt
   bound to HH/plan/proposal, graph/subject/report/policy hashes, evaluator version, expected
   revision and validated source manifest. Caller flags, report-shaped JSON or session GUCs
   cannot mint it. Restrict DB privileges/functions so direct SQL under application credentials
   cannot bypass the guard; a DB owner remains an administrative trust boundary.
6. In the same transaction, consume that authorization, append Revision N+1, release/rebuild
   controlled future reservations and advance the stable head. Treat these deliberate
   reservation changes as the validated command's effects on its checked pre-state, not an
   excuse to ignore unrelated mutations. Preserve physical lots/materialized history.
   Roll back every effect on mismatch. If issuance and publication are ever separated,
   publication must repeat the entire frontier check; a receipt TTL alone is insufficient.
7. Idempotent retry of an already committed identical command returns its recorded result;
   a changed payload/key or competing revision is a conflict. A stale uncommitted report
   requires recapture/revalidation, never report-hash relabeling or silent repair.

Clock-sensitive expiry/freshness must also be checked at the commit boundary. Use a bounded
validity deadline derived from authoritative policies/assets, then reject or recapture when
it passes even if no rows changed. Comparing a fresh whole subject with a new `as_of` blindly
is not a substitute for a versioned manifest; capture metadata and semantic inputs differ.

### 7.3 Mandatory future adversarial cases

Inventory consume/reserve/release after capture; new safety restriction including an initially
empty set; safety update/delete/ABA; policy activation/retirement; new applicable nutrition or
classification source; materialization pin added; concurrent revision; mutation after recheck
but before commit; direct SQL writers bypassing normal services; expired receipt/lot; replayed
authorization; rollback during reservation assembly. Each must fail stale authorization or
serialize/retry deterministically without partial revision. These are acceptance tests for a
future approved guard, not capabilities certified by this documentation.

## 8. Verification, migrations and stopping point

Added only review evidence tests: **9** canonical/sequence/frontier unit tests and **1** real
PostgreSQL source-frontier test. Targeted review + existing validation regression: **78 passed**
(68 unit,10 PostgreSQL), zero failures/skips, in6.80s. The PostgreSQL test inserts a restriction
after capture and proves source_frontier unchanged, subject hash changed, and both reports
still non-authorizing. Existing PG capture/no-query/no-write/authority guards were rerun.
The policy-content test demonstrates a changed policy can also leave today's frontier equal;
there is no authoritative mutable policy store today, so it is not a policy-DB race test.

Full local regression subsequently passed: **938 Python tests**, including **446 real
PostgreSQL tests**, all **928 pre-existing tests** retained, zero skipped/errors/failures,
84.11s. Ruff, architecture/import boundaries, domain/OpenAPI export drift and review links
pass. Synthetic benchmark **22/22** (HARNESS_SMOKE_NOT_PLANNER_V4); client **10/10**, generated
contracts/typecheck and web production build pass. PR/CI results are reported with the
delivery commit; successful tests do not turn any proposed capability into an implementation.

No migration is required for **this review**, nor inherently for the proposed pure culinary
checker/handoff. New persistent classification, policy selection/version sources or complete
DB-enforced authority/frontier records may require **0010 or later** in their own approved
implementation slices. Do not preallocate a migration or edit0001–0009 now. No live application
database is migrated by the review; isolated tests upgrade their own temporary databases.

MTR-026 remains **incomplete / not frozen**. This document requests architecture approval of
the matrix, next sub-slice and future freshness protocol. Stop here: no next-slice implementation,
Execution, CookingBatchExecution, planner, optimizer or production authorization is started.
