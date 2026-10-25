# Post-MTR-041D dependency review

Status: **DEPENDENCY SELECTION APPROVED by user** after PR #82. Documentation only.
The [046A design proposal](MTR_046A_CULINARY_FEATURE_ASSIGNMENT_DESIGN.md) is now submitted
for separate architecture/design review; implementation remains NOT AUTHORIZED.
Reviewed fetched main/origin/main: `091daa81ae9bc67b536fec4956ba1f52780fe9c9`.
The user has **FROZEN / APPROVED MTR-041D** at that exact commit (PR #81).
Schema: **0012 /58 domain tables**; migrations0001–0012 remain immutable.
Frozen040A/041A/B/C/D runtime, contracts, tests and hashes remain untouched.

## 1. Decision

**Recommend a dedicated design for MTR-046A — Reviewed Culinary Feature Assignment
Foundation**, a proposed source sub-slice of canonical **MTR-046 Catalog coverage matrix**.
This suffix identifies the user-approved foundation design area, not a completed backlog item
or permission to implement.
Do not add an041E arithmetic wrapper. No new implementation is authorized by this review.

The missing source truth is: which reviewed PROTEIN/METHOD/FLAVOR terms apply to an exact
authored recipe/selected ingredient path, and what was actually reviewed versus unresolved?
Catalog vocabulary definitions already exist. Assignments and their coverage/frontier do not.
This is a common prerequisite for multi-fingerprint exposure and feature-aware candidate fit.
An explicit preference about a term does not establish which recipes have that feature.

**Full041 cannot complete now.024/020B/021 remain BLOCKED.** Classification alone will not
unblock them: profile/priors, complete applicable exposure sources/coverage, novelty and
remaining separable utility policies still require their own designs. Execution remains
NOT STARTED; PRECOMMIT remains fail-closed. No new migration in this documentation task.

## 2. Inspected canonical sources and code

Canonical references: [spec§19.2–19.6,§21](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[ADR-011](../adr/ADR-011-behavioral-learning-loop.md),
[ADR-009](../adr/ADR-009-execution-state-machine.md),
[ADR-010](../adr/ADR-010-independent-validator.md),
[INV-001..030](../ARCHITECTURE_INVARIANTS.md), [backlog](BACKLOG.md),
[blueprint](IMPLEMENTATION_BLUEPRINT_M0_M1.md), [status](FOUNDATION_STATUS.md),
[040A design](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_REVIEW.md),
[post041C review](POST_MTR_041C_DEPENDENCY_REVIEW.md),
[041D review](MTR_041D_REPEAT_PENALTY_REVIEW.md)/[evidence](MTR_041D_REPEAT_PENALTY_EVIDENCE.md),
[026 dependency review](MTR_026_DEPENDENCY_REVIEW.md).

Paths below are relative to apps/backend; these are current-code findings, not namespace claims.

| Current source | Verified boundary |
| --- | --- |
| `app/modules/catalog/contracts.py`: AffinityFeatureTermFact; `catalog/models.py`: affinity_feature_terms | Versioned reviewed vocabulary for PROTEIN/METHOD/FLAVOR only. No ingredient/recipe/path assignment or family membership source. |
| `preferences/contracts.py`: ExplicitMemberPreferenceSnapshot | EXPLICIT_DECLARATIONS_ONLY; profile_derivation=NOT_IMPLEMENTED. Canonical member frontier/SET/retraction replay exists; UNDECLARED and RETRACTED are not NEUTRAL. |
| `preferences/public.py`: PreferenceService.snapshot/write | Member-owned raw declarations and authoritative source history; no derived affinity/strength/shrinkage/prior or candidate TasteFit. |
| `recipes/contracts.py`: RecipeFact, RecipeVersionSnapshot, GroundedRecipeVariantDraft, CulinaryCandidateDraft | Exact reviewed culinary IDs, ingredients, rules, quantities, preparation context and fingerprints exist. cooking_method is Identifier, not a reviewed METHOD term FK. Binding hash is not family identity. |
| `planning/exposure_capture.py`: capture_exposure_preview_sources | Read-only RR/SERIALIZABLE capture selects canonical proposal/recipe/member facts. RecipeExposureIdentity retains recipe/version provenance, not culinary feature assignments or a full selected ingredient binding. |
| `learning/contracts.py`: ExposurePreviewSnapshot, RecipeExposurePreviewFact, RecipeRepeatPenaltyInput/Draft | Selected proposal previews, Recipe-ID facts, source support and complete nested B/C/D revalidation. Global/history/accepted/confirmed/taste/novelty unavailable; activation_ready=False. |
| `learning/public.py` | Five pure APIs through interpret_recipe_repeat_penalty. No DB, attribution/profile mutation, ranking, optimizer or Execution calls. |
| `validation/contracts.py`: DeferredCapability; `validation/public.py`: validate_subject | Production/source capability gaps remain explicit; PRECOMMIT BLOCKED_UNSUPPORTED/REJECTED, POSTFACT DIAGNOSTIC. Separate accepted RecipeGroundingValidator does not complete026. |
| `execution/public.py`: PlanRevisionService.publish; frozen0008 authority guard | Plan publication structures exist, but production authority is not installed. A proposal reader cannot turn them into accepted-schedule exposure. |
| Registered ORM metadata |58 domain tables. Only affinity_feature_terms and three member_preference tables match feature/preference/exposure/behavior/assumption/execution source categories; no durable behavior profile, attributed exposure history or feature assignment table. |

Graphify provided ADR/spec orientation only; its historical graph is not evidence of current
implementation. Current code/contracts/tests and registered schema govern this review.
No concrete contradiction requiring changes to frozen code was found.

## 3. Capability dependency matrix

READY applies only to the stated scope. PARTIALLY READY means some primitives exist but new
source/policy/capture design is required. BLOCKED identifies missing upstream canonical truth.
N=proposed next design, P=independent/parallel design, S=source prerequisite, L=later consumer.

| Capability | Owner | Existing primitives | Missing primitive | Status | Prerequisite MTR | Recommended order |
| --- | --- | --- | --- | --- | --- | --- |
| Proposal-local Recipe-ID source/cooldown/decay/penalty | Learning; Planning capture | Frozen041A/B/C/D, exact policy/source trace | None within this bounded scope | READY /FROZEN | None | Preserve |
| Reviewed feature term identities | Catalog | AffinityFeatureTermFact/table; PROTEIN/METHOD/FLAVOR, versions/status/provenance | No missing identity within those three kinds; actual curated data still required | READY as vocabulary infrastructure | Frozen040A source subset | Reuse; never infer assignments |
| METHOD fingerprint | Recipes/Catalog source; Learning reader | Recipe.cooking_method Identifier; METHOD term identity | Reviewed identity bridge, exact context/applicability, coverage, correction/frontier; equal string is insufficient | BLOCKED | Proposed046A with018/019 path contracts → later041 reader | **N**, then L |
| PROTEIN/main-protein fingerprint | Catalog/Recipes | Ingredient IDs, authored selected slots/rules and PROTEIN terms | Reviewed ingredient associations and contextual main-protein designation; mixed dishes cannot pick largest mass/name | BLOCKED | Proposed046A source design with018/019 | **N**, then L |
| FLAVOR fingerprint | Recipes/Catalog | Reviewed FLAVOR vocabulary; recipe/version/path identity | Authored exact-path assignment, applicability/coverage/frontier | BLOCKED | Proposed046A source design with018/019 | **N**, then L |
| Variant-family fingerprint | Recipes/Catalog | Exact candidate/binding signatures | Stable authored family identity/membership, correction and cross-version reconciliation | BLOCKED | Separate046 family source sub-slice, coordinated018/019 | S; not hash clustering |
| Multi-fingerprint exposure capture | Planning capture; Learning contracts | Canonical selected-proposal capture, exact current culinary binding available elsewhere | Versioned companion source capture joining exact selected paths to reviewed assignments; distinct source identity/coverage/dedup | BLOCKED |046 assignments → new041 capture/interpretation profile | After N; preserve frozen A/D schemas |
| Member target-level profile derivation | Preferences/member profile; pure Learning derivation where allowed | Explicit declarations, subject/actor identity, current target state, member frontier | Reviewed derivation policy, target affinity/EvidenceStrength semantics, explicit prior applicability/provenance and unavailable states | PARTIALLY READY | Remaining040, proposed explicit-only profile sub-slice;028/046 only for applicable priors/features | **P**; not completed by046 |
| Recipe/candidate feature fit | Preferences/Learning; later024 consumer | Exact ingredient/direct-recipe declarations and culinary binding; reviewed term preferences | Feature assignments, profile/prior policy, coverage-aware match and separate fit contract | BLOCKED for full feature fit |046 +remaining040 →024 | N/P →L |
| Learned profile updates /attribution | Learning router/profile, member-owned |040A explicit source subset; ADR-011 routing categories | Other actual signal producers, attribution/reason/context policy and derived evidence lineage | PARTIALLY READY for explicit-source router design; BLOCKED for full runtime |039 +applicable040/045 sources;023/035 only for actual execution events | P/S; router must not fabricate events |
| Accepted-schedule exposure | Plan source; Learning interpretation |016 stable identity/revisions and publication schema | Production authorization, complete required validators, all-source commit frontier rechecks, accepted-source capture | BLOCKED |026 plus006/008/011–013/046 source prerequisites from026 review;016/027 authority seam →041 | S; no Learning shortcut |
| Confirmed cooked/consumed/member history | Execution source;039 attribution;041 consumer | Household/member/recipe IDs and physical ledger, ADR distinctions | Canonical evidence events, exact participation/attribution, cooking versus eating semantics and correction/source frontier | BLOCKED |023/034/035 evidence producers under independently approved authority/dependency design →039 →041 | S; do not start Execution here |
| Assumed provisional exposure |017 projections/036 compensation;039/041 consumers | Proposal preview only, not an assumption | Operational assumption IDs/status/parents, reversal/conflict lineage, attribution and bounded coverage | BLOCKED |017 →036, with039 and041 capture | S; no passive durable history |
| Cross-horizon/cross-week replay |017/038;041 exposure consumer | Scheduled timestamps, horizon and immutable proposal/revision IDs | Confirmed/operational/planning reconciliation; future commitment bridge with contribution lineage and complete source cut | BLOCKED |017 +023 planned flow →038;036 if assumptions contribute →041 | S/L; no concatenated previews as history |
| History coverage /global RepeatPenalty | Source owners and041 | Selected-source manifests; local absence marker | Authoritative source-set coverage/frontiers, cross-source same-event identity, supersession/reconciliation and source-kind policy | BLOCKED | Relevant accepted/confirmed/assumed/bridge source MTRs above +remaining041 coverage design | After applicable S; source applicability must be approved |
| Novelty /never-exposed claims |041;024 consumer | Local no-match and explicit unavailable markers | Covered applicable history, reviewed novelty policy and046 feature/family definitions where used | BLOCKED | Remaining041 sources/coverage +046;040/028 where preference/priors are used | After S; missing evidence is not novelty |
| Policy defaults /calibration |041 policy curation | Explicit versioned cooldown/decay/penalty contracts | Reviewed applicability/parameter evidence; no universal constants or empirical calibration currently | PARTIALLY READY for supplied policy; BLOCKED for production-default claim |041 policy curation/benchmark evidence, spec§24.3 | Separate from source design |
| Allergen/diet eligibility | Catalog safety source; Nutrition/root validator | Canonical member hard restrictions and exact grounded ingredients | Reviewed ingredient safety taxonomy/assignments, explicit unknown/negative coverage and enforcement semantics | BLOCKED | Separate046 safety source design coordinated005/006/026 | S; affinity labels cannot stand in |
| Full separable utility /role-aware portfolio /feasibility |024 →020B →021 | Local repeat-only dimension and explicit preference sources,020A containment | Full applicable profile/exposure/novelty inputs, nutrition/effort/policy sources and role/diversity policy | BLOCKED | Remaining040/041 +046 +006/007/008 and relevant supply sources →024 →020B →021 | L; no missing-as-zero |

## 4. Why classification next, rather than profile or history?

This is a recommended topological choice, not a new canonical total ordering.

**046 assignments** fill an actual reusable source gap in full041's multi-fingerprint acceptance
criteria and in member feature-fit matching. They need authored culinary truth and reviewed
vocabulary that already exist, not eating events or PRECOMMIT authority. They support both
the exposure and profile-consumer branches without inventing behavior or weights.

**Remaining040 target-level derivation** can be designed independently from046 for exact target
identities: a member's explicit LIKE for a METHOD term can be interpreted at that target without
knowing which recipes match. It still needs an approved derivation/prior/strength policy.
Do not claim046 blocks every profile operation; conversely, a numeric direct-recipe affinity
does not supply missing METHOD/PROTEIN/FLAVOR assignments or exposure coverage.
Full041 itself does not require TasteFit or a MemberBehaviorProfile.024 later consumes both branches.

**Source/history path** is required for full041, but is not a smaller implementation-ready
prerequisite here. Accepted schedule needs026 authority/source completeness; confirmed history
needs actual attributed events; assumptions need017/036; bridge replay needs017/038 and resolved
flow semantics. No router, preview hash or inventory movement can manufacture member eating
history. These source designs can proceed separately when approved; this review authorizes none.

```text
Frozen040A declarations ──→ remaining040 target profile/priors policy ──┐
FrozenRecipe/019 + reviewed terms → proposed046A assignments ─┬→ feature-aware041
                                                            └→ candidate feature fit
026 authority → accepted source ──────────────────────────────┐
Execution evidence →039 attribution ──────────────────────────┤→ full applicable041 coverage
017/036 assumptions +017/038 bridge ───────────────────────────┘
                 remaining040 + remaining041 + other separable inputs →024 →020B →021
```

Arrows show dependencies, not permission to start those milestones or an assertion that all
upstream branches are ready.041A/B/C/D stay immutable and useful within their current scope.

## 5. Proposed046A design envelope — approval required before implementation

Smallest coherent source capability: reviewed culinary feature assignments with applicability,
coverage and correction semantics. This is source truth, not a new penalty operator or score.

- Reuse exact reviewed AffinityFeatureTerm identities/versions; do not seed inferred taxonomy.
- Catalog owns vocabulary and ingredient→PROTEIN association facts. Recipes owns culinary
  applicability to exact RecipeVersion/selected authored paths, including explicit contextual
  main-protein and FLAVOR designations. METHOD needs a reviewed bridge from authored cooking
  context to the METHOD identity. A future capture layer may coordinate the sources.
- Preserve frozen RecipeVersion aggregates/seals. Prefer additive immutable source/companion
  facts with typed exact-version/path relationships; do not insert late children into sealed
  recipe versions or rewrite existing culinary fingerprints. The exact schema is a design task.
- Define the path key and authored applicability explicitly. Base-recipe labels must not
  automatically cover substitutions, every tier/quantity adjustment or a new method. No fuzzy
  equivalence, solver/LLM invention or implicit ingredient-name matching. Reject/mark unresolved
  when the requested selected path is outside the reviewed applicability.
- Review status and provenance are distinct. Missing assignment is UNRESOLVED, not absence of
  a feature, global neutrality or dietary safety. Coverage must identify the reviewed source set
  and applicable path; reviewing one property does not certify every feature for the recipe.
- Corrections append new assignment versions/supersession facts; keep prior term/version/path
  evidence. Define deterministic current source selection and frontier including newly added
  mappings/coverage, not only updates to known rows. Recheck belongs to future commit authority.
- Immutable capture must include exact assignments, reviewed terms, applicability/coverage,
  provenance and source frontier/hash. Pure consumers must not query live mapping tables.
- Direct-SQL integrity, exact ownership FKs, append-only history, concurrency and deterministic
  snapshots are implementation requirements after design approval, not claims of this review.

Defer family identity/membership to its own source design, safety/allergen/diet taxonomy to
its own safety source design, and time/equipment/complexity annotations to applicable coverage
work.046A would not complete full046, full041 or full040. Do not reuse the affinity vocabulary
as allergen/diet truth, or call these assignments new culinary possibilities.

Durable curated assignments **likely require a new forward migration0013 or the next available
head**, but table layout/count must be justified during046A design. No migration is needed or
created now. Do not edit0001–0012 or claim persistence can be replaced by a transient JSON blob.

## 6. Adversarial design checks

| Counterexample | Required interpretation /missing source |
| --- | --- |
| Member LIKEs FLAVOR.spicy; recipe title contains “spicy” | Term preference is valid; candidate feature match remains unresolved without reviewed assignment. |
| Recipe.cooking_method string equals a METHOD term code | Text equality is not a canonical identity bridge or evidence of review. |
| Chicken base substitutes authored tofu; old labels say main-protein chicken | Base classification cannot propagate to replacement path. New exact-path coverage is required. |
| Mixed chicken/tofu dish has more tofu grams | Neither mass nor ingredient order defines canonical main-protein designation. Author it or retain unresolved. |
| Two binding fingerprints differ only in tier/quantity | Hashes distinguish exact facts; they do not establish different/same culinary family. Applicability/family truth is separately authored. |
| Member directly LIKEs recipeA; recipeB shares feature label | No automatic preference propagation, shrinkage or EvidenceStrength without approved040 derivation policy. |
| New preference or mapping arrives after immutable capture | Old snapshot is reproducible; not current authorization. Future commit guard must recheck all applicable source frontiers. |
| Proposal revision removes Tuesday meal | Old preview remains historical proposal evidence; it is neither actual eating nor a second active commitment. |
| No matching witness; or witnesses explicitly retain0 | Keep None versus exact0 as frozen041D; neither becomes global never-exposed or novelty. |
| Two proposal captures cover the same week | Union/dedup can preserve known preview facts; it cannot prove complete cross-week history or resolve all cross-source identity. |
| Raw inventory CONSUME exists | Does not identify who ate which recipe or distinguish cooking input from meal consumption. |
| Allergen code happens to equal a PROTEIN label | Feature preference classification is not safety eligibility. Unknown safety must still fail closed. |

These are architectural counterexamples, not new production tests or implemented assignments.
No defect was found that warrants a correction PR or changing frozen semantics.

## 7. Invariants, ordering and stop

INV-005/006: assignments describe authored possibilities; never create substitutions/methods.
INV-009: risk/penalty/policy multipliers are not calibrated probabilities. INV-011/012/013:
historical physical facts stay immutable, elapsed schedule/proposal is not consumption or
confirmed reality. INV-015–021: independent validation uses captured primitives; no DB inside
validator, safety summaries are not truth, PRECOMMIT fail-closed and POSTFACT diagnostic.
INV-022–029: no passive durable learning, operational friction→taste, cooked→liked, member
fan-out, caller-authored EvidenceStrength or early cross-dimension utility. INV-030 bridge
remains incomplete. Reservations stay intent, not material movement. Retail AP→EP and Recipe
EP_RAW→COOKED ownership remain separate.

Next action recommended: **046A source architecture design**, then a separately approved narrow
implementation. Remaining040 profile-policy design may proceed in parallel only if requested.
No041E,024,020B,021,Execution or source/history implementation starts here.

## 8. Verification /delivery evidence

Reviewed exact fetched main091daa81; Alembic revision graph and registered ORM metadata confirm
0012 /58 (not a live-production database claim). Frozen baseline evidence:1626 Python,645 real-PG,
1540 prior regressions retained,86 additive tests, benchmark22/22, client10/10; exact-merge
[CI40088853692](https://github.com/thedusk4203/Menuto/actions/runs/40088853692) SUCCESS.
This documentation review adds no validator, source runtime, migration or test capability.
Task-specific local verification: **405 existing tests passed**,23.83s, covering recent exposure,
cooldown/decay/penalty, explicit preferences, validation foundation/canonical review and architecture.
The first run had404 passed and one temporary-directory setup error in the sandbox; rerunning
the same tests with an explicit workspace basetemp passed405/405, without code/test changes.
Architecture baseline (30 invariants/11 ADRs/50 linked tasks),16-context import checks, ruff,
domain/OpenAPI drift, document links and whitespace checks PASS. Diff is eight product documents
only; frozen runtime/contracts/tests/exports/migrations unchanged. No local PostgreSQL rerun
is claimed for this documentation task. Full PR and exact-merge CI are checked at delivery;
baseline counts above are not presented as a newly run local PostgreSQL suite.

**READY FOR ARCHITECTURE REVIEW**
