# MTR-041A — Recent Exposure Source Foundation

Reviewed main: `06dc1dcbf38d474b90f7bfb74f04651e884285e4`; schema0012 /58 tables.
User freeze: MTR-040A APPROVED/FROZEN at that commit. Full040 remains incomplete.
0001–0012 and frozen019A/B/C/020A/040A semantics remain unchanged.

## A. Dependency decision before code

Select **MTR-041A**, the **read-only proposal-preview subset** of Recent Exposure Source
Foundation. It is not a durable exposure history or production RecentExposureModel.

Actual source paths: PlanStore.workspace/proposal, sealed PlanProposalSnapshot and
BoundPlanProposalSnapshot; graph meals/participants, planned batches and allocations;
RecipeVersionSnapshot.recipe.id. Immutable proposal history already belongs to Planning.
Learning is currently a contracts-only fact reader namespace. PRECOMMIT is fail-closed:
accepted revisions exist structurally and in privileged synthetic tests, but cannot be
truthfully produced through the current production authorization path.

Do not add an exposure table that copies proposals or invent a manual confirmed-consumption
producer inside Learning. Current canonical truth can support proposal previews only. This
narrows the preferred041A foundation rather than pretending full041 or020B is unblocked.

## B. Source matrix

| Source | Current truth | Status in041A | Prerequisite for extension |
| --- | --- | --- | --- |
| Sealed latest proposal, explicit participants and batch→meal allocation | Implemented; immutable proposed advice | PROVISIONAL / PROPOSAL_PREVIEW only; not an accepted commitment | None for preview |
| Accepted ActivePlan/PlanRevision schedule | Persistence/contracts exist; production publication gated | Unsupported producer; do not treat a draft as accepted | MTR-026 production PRECOMMIT and later accepted-schedule capture |
| Explicit confirmed consumed/eaten | No member-scoped consumption source | Unavailable | Canonical execution/MealExecution source, MTR-039 attribution; MTR-017 projections |
| USER_CONFIRMED_COOKED | ADR event semantics, no production event source | Unavailable | Cooking execution source and MTR-039 routing |
| AUTOPILOT_ASSUMED | No assumption graph/projection source | Unsupported, never durable confirmed history | MTR-017 + MTR-039; reversible projection only |
| Inventory CONSUME / prepared asset | Physical material evidence, no canonical member meal consumption attribution | Not behavioral exposure input | Execution/member attribution; do not infer eating from movement |
| Explicit preferences | Frozen040A raw declarations | Separate truth; not exposure | Later profile derivation; never copy into exposure |

ADR-011/INV-024 call USER_CONFIRMED_COOKED confirmed *exposure*. This is not confirmed
*consumption* or taste. The user constraint cooking≠consumption is compatible with retaining
separate evidence kinds; no ADR correction is needed.041A implements neither producer.

## C. Fingerprints

Recipe identity is safe: exact RecipeVersion→stable Recipe FK, captured with authored source
provenance. Initial output supports **RECIPE_ID only**. RecipeVersion IDs remain traceability,
not independent repeat identities. Different versions of one recipe in the same meal count once.

Exact culinary binding/candidate hashes exist, but do not define a cross-version variant family.
Variant/family repeat semantics are deferred. Authored recipe cooking_method is an Identifier;
it can be retained in the captured recipe but is not automatically a reviewed METHOD feature FK.
Protein/flavor/family classifications have no canonical Recipe→AffinityFeatureTerm mapping.
Those feature fingerprints remain explicitly unsupported (MTR-046). No inference from names,
ingredient identities, method strings or shared vocabulary spelling.

## D. Contracts and ownership

Learning owns frozen extra-forbid preview policy, source, recipe exposure fact, immutable
snapshot and repeat-evidence contracts. Planning orchestration owns the read-only capture
adapter. It reads only public Household/Planning/Recipe surfaces. Learning core imports contracts
only, performs no DB/IO and has no Execution, attribution, preference mutation or solver runtime.

Capture names a household/member and explicit unique plan IDs; each plan contributes exactly
one latest sealed proposal or a successful empty workspace. No caller-provided proposal graph,
source status, event or cached score is accepted at capture ingress. Unknown/foreign sources
raise, not empty fallback. Capture requires a clean read-only RR/SERIALIZABLE transaction and
canonical actor membership. Full member identities, selected workspace/proposal frontiers and
authored recipe sources are captured coherently; replay requires no live reads.

Coverage is **SELECTED_PLAN_PROPOSAL_PREVIEWS_ONLY**; consumption history is **UNAVAILABLE**.
An empty result means no matching proposal preview in this explicit scope, never never-exposed.
No all-household/current-source or PRECOMMIT authority is implied by serialized hashes.

## E. Policy, chronology and repeat primitives

Caller supplies a versioned policy identity/provenance and explicit half-open time window.
No universal cooldown/decay, weights, probability, novelty/TasteFit/RecipeScore or penalty.
Output reports matching provisional recipe/meal facts and occurrence count only, preserving
coverage/unknown-history semantics. Count is evidence cardinality, not a preference/utility score.
Windows can span horizons, including a Sunday before a Monday horizon start; this is filtering
captured proposals, not chronological HorizonBridgeResolver replay or stock projection.

The preview event key is household/member/plan/meal/recipe. Count once per distinct recipe per
meal/member, merging all supporting active batch allocations; a shared cooked batch allocated
to two meals yields two proposed meal facts, never a cooking/consumption event. Include only
PLANNED meals/batches/allocations with positive authored allocations and explicit participants.
Past scheduled timestamps remain provisional; elapsed time cannot promote status.

Deterministic serialization sorts only unordered fact sets; explicit source identities/ordinals
remain inside facts. Any future ordered execution/assumption sequence needs a ledger sequence,
not generic tuple sorting. All new output is DRAFT/activation_ready=False and recomputed from
captured source primitives, not trusted cached fields.

## F. Corrections, deduplication and frontier

No new writes, so retry/concurrency/append-only integrity stays with frozen Plan proposals/seals.
Latest proposal selection is coherent under RR. A corrected/retired proposal supersedes an older
preview: fresh capture uses only the latest selected plan proposal. Never combine proposal
history as repeated exposures. Immutable old snapshots remain reproducible. Replacing a batch
recipe removes its old preview and introduces the new one; physical inventory is unaffected.

Source frontier is the explicit selected-plan manifest (latest generation, proposal identity/hash,
workspace head/boundary facts), not a new household exposure counter. Additions outside selected
plans are outside coverage; a future all-plan history source/frontier is still required. Same
event identities deduplicate overlapping windows; complete MTR-038 bridge producer merging and
confirmed-vs-provisional reconciliation remain unimplemented, not silently additive.

## G. Dependencies and invariants

- MTR-017: confirmed/operational/planning and reversible assumption projection unavailable.
- MTR-038: causal horizon/asset/exposure bridge and producer reconciliation unavailable.
- MTR-039: no router/event classification implemented; preview is a fixed explicit source category.
- MTR-046: family/protein/flavor/reviewed method feature mapping unavailable.
- MTR-024 consumes future evidence dimensions only after its own reviewed coverage semantics.

INV-022 passive assumptions excluded;023/024/025 no friction/execution/rejection→taste;
026 per-member explicit participant filtering;027 dimensions separate;028 no policy mutation;
029 forced choices never become learned taste;030 stable meal identities and half-open windows
support a later no-double-count bridge but do not complete it. INV-013/018/021 preserve evidence,
provenance and fail-closed authority. Exact invariant wording in canonical docs remains unchanged.

## H. Adversarial review

1. Scheduled meal time passes: same PROVISIONAL/PROPOSAL_PREVIEW, never confirmed eaten.
2. Raw stock consumed or cooked output exists: ignored as exposure; no producer exists here.
3. Two participants: each member's preview includes only their explicit meal participation;
   no preference update, self/proxy copying or implicit household membership participation.
4. Two batches/versions of one recipe feed one meal: one recipe exposure with all support links.
5. A proposal is corrected/retracted/retired: latest source replaces old preview; history is not
   replayed as durable exposure. No deletion or rewrite of the old source/snapshot.
6. Concurrent proposal commit: RR sees a coherent old manifest; fresh capture sees the new one.
7. Sunday captured by two overlapping windows: stable event key supports set-union/dedup, not
   count addition. Duplicate plan/source IDs reject; no full bridge or consumption reconciliation.
8. Empty/missing/foreign source: successful empty preview differs from unavailable/not authorized.
9. Caller claims CONFIRMED/COOKED/AUTOPILOT or supplies a repeat score: closed contracts reject.
10. Missing method/family/protein mapping: unsupported lookup raises, never score0 or inferred label.

## I. Deferred and acceptance

No migration/new table: durable history source does not exist yet and intent truth is already
versioned in Planning. Full041 remains PARTIAL; no durable facts/confirmed producer, manual eating
workflow, decay/cooldown, novelty, family features, attribution/learning, assumption graph,
Execution, MTR-038 resolver, MTR-020B roles, MTR-021 or production PRECOMMIT.

Implement this subset with unit and real-PG capture/revision/concurrency/read-only negative tests,
all frozen regressions, migration/drift, schema export, architecture checks, benchmark/client/web
and CI. Do not self-freeze; stop for **MTR-041 ARCHITECTURE/FREEZE REVIEW**.
