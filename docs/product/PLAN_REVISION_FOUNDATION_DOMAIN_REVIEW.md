# F — Plan/revision foundation: domain architecture review

Date: 2026-10-23 (Asia/Saigon). Status: **READY FOR ARCHITECTURE/FREEZE REVIEW**.
This is a design review, not runtime implementation or a frozen new milestone.

## Canonical naming, baseline and evidence inspected

Canonical slice: **F — Plan/revision foundation**, from the acceptance table in
[Blueprint M0/M1](IMPLEMENTATION_BLUEPRINT_M0_M1.md). Canonical work item:
**MTR-016 — ActivePlan + PlanRevision schema** in [Backlog](BACKLOG.md).
MTR-023 contributes planned-batch/allocation seams; MTR-025 contributes the future
validation-subject seam. MTR numbering is not a dependency DAG. This review does not
rename F to M1.4, close these work items or start the next slice.

Frozen dependency: M1.3 at `fef629965dd7401e27c98b5a0c523998a27017c4`, head0007,
38 domain tables, 688 Python / 313 PostgreSQL-real tests, benchmark22/22 and
[postmerge CI SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/39817008268).
M1.1/M1.2 stay frozen. Published migrations0001–0007 must remain byte-identical.

Read: blueprint, entry checklist, backlog, architecture/glossary, spec §8.3/8.4,
§9, §13.7–13.14, §16.4, §18; ADR-003/004/005/006/007/008/009/010/011;
[canonical invariants](../ARCHITECTURE_INVARIANTS.md); M1.3 review/evidence;
actual InventoryService/contracts and Recipe binding contracts. The supplied path
`docs/product/ARCHITECTURE_INVARIANTS.md` does not exist; the canonical file is
`docs/ARCHITECTURE_INVARIANTS.md`. No duplicate baseline is created.

Current planning/shopping/cooking/execution namespaces have no business implementation.
GroundedRecipeVariantDraft and PhysicalInventorySnapshot explicitly cannot authorize activation.

## Dependency findings and implementation boundary

No concrete contradiction was found in frozen M1.3. Do not redesign its ledger,
full-release reservations, chronological append rules or advisory-lock protocol.

**Operational activation blocker:** ADR-009 says activation creates baseline revision0;
ADR-010 and the blueprint require PRECOMMIT validation of the exact subject before
activation and revisions. Full source resolution, ValidationSubjectSnapshot and an
independent gate do not exist. A caller boolean, manually supplied successful report,
M0 draft hash or a Recipe culinary binding is not an authorization capability.

Resolution: architecture can be reviewed now; operational activation remains fail-closed.
A later implementation may first implement explicitly DRAFT authoring/proposal persistence
and structural checks. It must not publish an operational ActivePlan, reserve inventory
automatically for each draft, or label draft proposal history PlanRevision0. Missing full
validation must remain visible; it cannot be silently waived to make F appear complete.
This review does not implement migrations, services, contracts, execution or a validator.

## A. Aggregate ownership and mutation

| Entity | Domain owner / scope | Mutation policy |
| --- | --- | --- |
| Plan identity/workspace | Planning; Household | Stable plan_id, owner/tracked member/horizon fixed; guarded head/counters only |
| ActivePlan | Operational view of a validated/activated plan identity | Stable plan_id, active_revision_no via atomic CAS only |
| PlanProposalDraft | Planning; plan-owned preactivation or revision proposal | Immutable complete proposed intent graph; independent proposal identity/generation |
| PlanRevision | Planning; exact plan_id + revision_no | Immutable full accepted intent snapshot, parent hash, actor/provenance/scope |
| MealSlot identity | Planning; exact plan and household | Stable node identity; never reused for a different historical node |
| MealIntent version / participants | Exact proposal/revision + MealSlot | Immutable content; effective current view changes with root pointer |
| ShoppingRequirement identity/version | Shopping context, plan-owned demand | Immutable revision content; future intent may be superseded/retired |
| PlannedCookingBatch identity/version | Cooking context, plan-owned production intent | Immutable authored binding/composition/serving target per revision |
| PlannedBatchAllocation | Cooking context, plan-owned batch-to-meal demand | Immutable revision content; future allocation can change independently of cooked production |
| PlanReservationBinding | Planning intent linkage, household + plan + target | Append-only link to exact M1.3 reservation and target intent version; later release remains Inventory-owned |
| PurchaseFulfillment | Shopping, household-owned confirmed fact | Append-only actual quantity + actual Money + provenance; not part of mutable plan graph |
| CookingBatchExecution / MealExecution | Execution, household-owned evidence | Immutable confirmed reality, referencing exact source intent revision if known |
| InventoryLot / prepared assets / movements | Inventory, household-owned | Frozen M1.3 semantics; no Plan ownership or cascade delete |
| ExecutionBoundary facts | Execution, household-owned | Append-only actual causal links to materialized intents, with monotonic sequence |

Participant records reference exact HouseholdMember identity with composite household FK;
V1 tracked role binds the plan's one tracked member. Shared resource/attendance aggregates
never replace individual safety sources. Safety remains independently resolved/validated.
No member biology or preferences are copied into household resource identity.

Draft workspace identity may later become ActivePlan **with the same plan_id**. Before
activation active_revision_no is absent; proposal generation is a distinct concurrency
counter, not a live PlanRevision number. Activation alone produces revision0 with reason
INITIAL_ACTIVATED_BASELINE. No detached plan primary key is created by a revision.

## B. Canonical revision representation

Choose **full immutable relational intent graph + explicit change metadata**. Do not use
a diff as the reconstruction source of truth. Each revision retains all meals, participants,
requirements, batches, resolved ingredients, allocations and reservation intent references,
including retained historical/superseded nodes. Content/status are typed relational rows.

Root is (household_id, plan_id). Each versioned node has stable node_id and exact
(household_id, plan_id, revision_no, node_id) identity; child FKs bind the same revision.
Identity, membership, basis, quantities, revision linkage and ownership are not JSONB.
Exact immutable cross-context source snapshots may eventually use versioned frozen payloads
only when justified, alongside canonical FKs and typed primitive facts; this review does
not approve a generic JSON graph store.

Current Working Graph is the **logical mutable head view** of this canonical graph,
selected by active_revision_no (or selected proposal before activation). No second set
of independently writable mutable child rows duplicates revision truth. A view changing
by atomic pointer switch still supplies revisable current intent. An editing UI later
builds a new proposal; it does not modify accepted children in place.

Metadata: parent revision/hash, graph hash, scope, exact changed node IDs and changed
components, actor, requested/effective/recorded times, reason and source, command identity,
validation subject/report identities, source frontier versions. A diff/explanation may be
derived, but is not required to reproduce a revision. Full snapshots cost more rows than
diffs; V1 accepts that cost for deterministic audit and direct relational checks.

Hash canonicalization must version timestamp/Decimal normalization, tuple ordering by
stable keys and optional-field semantics. Equal graphs with different caller ordering
must hash equally. Store no cached valid=true. Historical reads select an exact revision,
not 'latest recipe' or a mutable join through the current head.

## C. Past/future cut line and materialization

Two independent boundaries:

1. **Advice cut line:** explicit monotonic revision effective_from freezes earlier advice
   for audit; elapsed time alone produces no execution or physical state transition.
2. **Materialization boundary:** confirmed purchase, started/materialized cooking or meal
   execution pins the affected historical intent version/components, even before scheduled_at.

A consumed meal locks its exact intent/participant version. A cooked batch locks production
identity, resolved composition, method and produced facts; it does not freeze every future
meal allocation. Purchase fulfillment locks actual purchase facts, not every future recipe
that might use the ingredient. A physical lot remains a household asset independently.

A due-but-unexecuted meal is unresolved, not consumed. Preserve past advice; an explicit
reschedule may add a future slot linked to the old stable slot, preserving the original.
Do not silently move the old historical node or infer eating from scheduled_at < now.

Future execution must acquire the same household/plan coordination locks before atomically
recording execution and boundary facts. A future validator's boundary version must be
rechecked before revision commit. Unknown execution is not equivalent to executed=false.

Late evidence referencing revision4 after revision5 is accepted by future POSTFACT intake
as reality against revision4; it does not rewrite revision5 or automatically create revision6.
A conflicting current graph is diagnosed EXECUTION_CONFLICT and blocks unsafe future advice
until explicit repair. This execution/diagnostic workflow is **not implemented** here.

## D. Shopping: demand, fulfillment, stock

ShoppingRequirement is typed plan demand (ingredient/procurement context, quantity+basis,
need-by time, evidence references). It is not a purchase order guarantee or physical asset.
Requirement changes produce new intent versions; old versions and fulfillment links remain.
Retiring a requirement means no further planned demand, not a refund or destruction of stock.

PurchaseFulfillment is an independent household fact: actual measured quantity, item/basis,
actual integer-minor-unit Money/currency, source/provider/event identity, actor and timestamps.
A partial fulfillment references the exact requirement version it fulfilled. Actual product
mapping and AP/EP evidence stay explicit; no quantity subtraction across incompatible bases.

Future confirmed fulfillment transaction records the fulfillment, its exact actual quantity
and acquisition movement/lot atomically. It does not create expected remainder as stock.
One fulfillment may later require explicit allocation rows to multiple requirements; an
allocation cannot spend the same actual quantity twice. No new allocation schema is claimed now.

1000 AP_G demanded and 600 AP_G confirmed gives 400 AP_G outstanding under that exact
version. If a revision retires or changes the demand, recompute outstanding against the
new requirement version and explicitly retained allocations; retain the 600g purchase/lot.
Never set purchased=true or rewrite required_qty to600 as if the original demand was met.

ADR-007 future revision accounting is ConfirmedActualSpend + stress cost of the remaining
unfulfilled requirements. Confirmed spend remains even when its requirement is retired;
no re-stressing actual receipts or dropping historical overspend. Cost evaluator deferred.

## E. Reservation lifecycle and M1.3 compatibility

Physical reservations remain M1.3 immutable intent rows plus full-release facts. Plan links
are separately typed by target kind (meal/batch/allocation) and exact intent version, using
composite FK ownership. Never add plan_id as ownership to InventoryLot or change frozen
reservation rows. No generic string context_ref stands in for canonical target identity. A stable immutable
binding maps one reservation to one plan/stable target; revision membership retains that
binding across unchanged content. Do not retarget a reservation to another plan/meal by
adding a new row. DB guards must reject cross-target reuse while allowing legitimate
unchanged binding membership in successive revisions.

Revision computes an explicit reservation impact set:

- Same target/material basis/quantity/need and usable lot: retain exact reservation and
  append a binding in the new revision as necessary; do not double reserve it.
- Retired/changed unexecuted target: full release the linked reservation, then create new
  intent reservation(s) only after revalidation against actual available stock.
- Partial retain: release whole old reservation, reacquire the retained fraction + changed
  allocations atomically; M1.3 has no UPDATE or partial release. If reacquire fails, rollback
  releases and the complete revision transaction.
- Materialized input already consumed/released by execution: keep historical binding;
  do not release it twice or fabricate a new reservation over consumed stock.
- A shared reservation spanning multiple targets must be prohibited in first implementation
  unless an explicit quantified allocation model exists. V1 proposed rule is one target
  per reservation; same lot can have multiple independently bounded reservations.

Release/reserve are inventory intent operations, not material movements. Revision must
never invoke acquire/consume/discard/reconcile to make its graph fit. External unlinked
manual reservations are not the plan's to release. Expired lot material and stale reservation
intent remain auditable; allocation eligibility uses M1.3 allocatable/lifecycle semantics.

Use M1.3 chronological commands at the actual reconciliation/recording time, not a future
meal timestamp. For a new plan reservation, occurred_at must not regress prior lot phase/time;
choose an explicit valid current command timestamp after prior ledger order, or report a
retryable ordering conflict. Do not change old M1.3 timestamps to force ordering.

Preactivation proposals contain desired reservation intents only. No automatic reserve/release
side effects occur before a validated activation/revision capability exists.

## F. Planned batch and future physical execution

PlannedCookingBatch holds explicit RecipeVersion + authored binding fingerprint, selected
rules/tier, planned_servings, resolved planned ingredients with basis/requirement identity,
planned production time and optional future asset/storage policy references. Recipe owns
EP_RAW→COOKED; Retail still owns AP→EP. No global preparation or yield table is introduced.

PlannedBatchAllocation maps batch-version to meal-version with defined serving quantity;
planned total allocated servings cannot exceed planned production. Excess planned production
is an explicitly planned carryover, not an owned PreparedFoodLot. Existing prepared assets
may be referenced through separate typed allocation intent/reservation, never by pretending
that a future planned batch has already produced them.

Future CookingBatchExecution records produced_servings and actual resolved_batch_ingredients,
consumes raw inputs and produces separate prepared identity atomically with explicit yield
and source traceability. planned_servings != produced_servings by default; neither is derived
from grams. Quantity micro-adjustment changes composition, not serving count. COOKED != CONSUMED.

A cooked Monday batch feeding Tuesday remains household stock if Tuesday changes; only the
future allocation is revised. Already cooked production rows stay pinned to their historical
recipe/composition. Planned output must never count as both raw and prepared physical stock.
Execution, multi-step preparation, consumption UX and batch conservation engine are deferred.

## G. Idempotency, concurrency and atomic revision protocol

Command identity: household + plan + command source namespace + idempotency key. Fingerprint
covers concrete command kind, expected revision/hash, proposed graph hash, scope, affected
nodes, evidence and source frontier. Persist unique command result linked to exact revision.
Retry the same body/key returns that immutable result, **before** checking whether head has
advanced; different content with the same key is a conflict, not a new revision.

Concurrent A/B against revision4: lock/CAS head4 with expected hash. Exactly one can publish5;
other returns STALE_REVISION. Unique(plan_id, revision_no) and parent/head guards protect
SQL callers too. No last-writer-wins and no independent detached plan IDs. REPEATABLE READ
or serialization conflicts require rollback/retry of the whole command, not a lost update.

Operational revision transaction proposal:

```text
BEGIN
  acquire exclusive household fence matching frozen M1.3 inventory protocol
  lock plan root; verify owner/editor actor and idempotency result/body
  compare expected active revision/hash; read locked execution/materialization frontier
  assemble new immutable proposal graph + typed reservation impact set
  enforce scope, exact revision FKs, participant identities, immutable historical components
  verify one PRECOMMIT capability for this exact final subject/source frontier
  append Revision N+1 + child graph + audit/command result
  release/rebuild changed future reservations through Inventory public facade
  verify actual reservation outcome matches the validated proposed effects
  CAS active_revision_no/hash and commit complete revision
COMMIT
```

Graph content, required reservations and their eligibility are part of the validation subject.
Do not validate one graph and then silently alter it after reserve fails. Use deterministic
reserved operation identities; new reservation row IDs are command facts, while allocation
quantities/basis/lot/targets must match validated intents. If source/current balance changes,
abort and rebuild/revalidate. Scope lists are computed/checked, not trusted caller assertions.

One connection/transaction across contexts; no per-repository commits or after-commit release.
Lock order: household fence → plan root → affected lot balances (stable lot-id order). Any
future execution writer must follow this coordination order. This prevents revision holding
plan then waiting on inventory while another holds inventory then waits on that plan. Cross-
household operations are out of V1. A failed reservation, child insert or head CAS rolls back
revision, head, command result and reservation releases together.

Long independent validation can run outside writer locks over an immutable proposed subject.
On commit, compare all captured frontier versions under locks; any change requires fresh
validation, never trusting a cached pass. A short final check under locks is mandatory. This
review does not introduce a fake PRECOMMIT service or lock the household during a long solve.

## H. Deletion policy, revision scope and database plan

No committed revision/proposal graph, stable identity with history, command result, execution
fact, physical inventory or fulfillment fact is deleted/updated. Future graph retirement is
new revision content; immutable old content remains. Head views exclude retired future nodes
when appropriate, but historical reads still retrieve them. Uncommitted assembly disappears
by rollback; maintenance/archive design must preserve provenance and is outside this slice.

SINGLE_MEAL changes one future meal and only its declared dependency closure (allocation,
shopping/reservation effects); cannot silently alter another meal served by a shared batch.
Changing shared production or a second allocation requires MULTI_MEAL with exact affected
meals. An aggregated shopping requirement needs typed quantitative demand allocations to
its contributing targets; changing one meal may change only its own contribution. Do not
silently reduce another meal's material coverage by editing the shared aggregate total. PROCUREMENT_ONLY changes future requirements/options/reservations without changing
meal identity, participants, composition or batch servings. REMAINING_HORIZON may replace
future unexecuted advice, never confirmed facts or locked past. Any ingredient/portion change
outside an existing authored binding/tier requires a new valid binding/explicit revision.

Proposed relational families, **not created tables**:

| Family | Typed persistence representation |
| --- | --- |
| Plan identity/head | plan roots (household/actor/tracked member/horizon), active-head/revision gate, proposal generation |
| Revision history | plan revision snapshots + exact parent/hash + immutable command result and proposed effects |
| Stable intent identities | meal_slots, shopping_requirements, planned cooking_batches, batch allocations |
| Versioned full graphs | per-revision meal intents/participants, shopping demand rows, planned batch rows/ingredients/allocations |
| Inventory intent seams | typed reservation bindings and immutable per-revision desired allocations, real reservation FKs when materialized |
| Future execution seams | typed fulfillment/batch/meal links only when real canonical source tables exist |

Do not persist bare execution UUIDs before their canonical tables exist. A draft wire seam
can describe future ownership without pretending an FK or physical evidence exists. Exact
future table names/count are not frozen by this review; avoid a generic polymorphic target
UUID whose kind string bypasses composite FK checks.

A future migration0008 must be frozen DDL, append-only to0007. It needs deferred aggregate
completeness/seal and transition guards so incomplete revisions/children/head switches cannot
commit. Structural scope/past-child equality, ownership, parent chain and source linkage must
be protected by DB constraints/guards, not Pydantic alone. Draft assembly/proposal persistence
must remain visibly separate from validated active state. Populated downgrade must fail closed.

## I. Validation handoff and authorization capability

Freeze a proposed subject with exact plan identity, expected head/parent hash, complete intent
snapshot, member root safety/participant sources, RecipeVersion/bindings, retail/reference/
scenario facts, confirmed inventory primitives, current reservations + proposed effects,
fulfilled actual spend and execution boundary frontier, horizon-bridge facts and policy versions.
These are different state classes, not one undifferentiated availability array.

A future ValidationSubjectSnapshot is independently serializable/frozen and captured from a
consistent read transaction/source frontier; validator reads that immutable artifact, never
queries a working graph while it changes. Future proposal identity/hash and actual accepted
revision hash both remain available; a report for proposalA cannot activate proposalB.

Full source set unresolved → DATA_INSUFFICIENT/DRAFT, not successful validation. Independent
validator mints/persists an authentic report/capability with subject hash, expected parent,
validator version, source frontier and zero ERROR/FATAL. Accepted policy/relaxation provenance
must match exact subject. Trusted application authorization and DB transition boundary must
ensure callers cannot INSERT their own 'PASS' capability. Signature/grant/storage mechanism
requires the validator/security implementation; do not freeze a magic boolean in this slice.

Operational activation and revision cannot be enabled until this capability is real. Read-only
schema/proposal authoring can precede it, with activation_ready=False and no physical effects.
No full Independent Validator, policy synthesis, clinical safety, nutrition totals, robust-cost
proof or production feasibility claim is introduced by this review.

## J. Horizon bridge and replan boundary

Each plan has explicit nonempty half-open horizon; future plans keep their own stable plan_id.
Do not globally prohibit a second horizon/plan as a shortcut for missing HorizonBridgeResolver.
Activation of an overlapping/bridged horizon remains gated until the bridge input is resolved.

Handoff must name source plan/revision/hash, boundary/ledger/reservation frontiers, cutoff,
future scheduled consumption/production/allocation/remaining commitments and carryover intent,
plus provisional exposure facts (never durable learning). HorizonBridgeResolver later replays
these chronologically. Raw reservations and their future prepared outputs are a linked material
flow, not two independent opening assets. Confirmed prepared assets are distinct from scheduled
outputs. A source revision or execution change invalidates the old bridge/validation subject.

Remaining-week replan creates N+1 of the same active horizon, not another plan identity.
Inventory/execution events may recommend repair but do not invoke a planner, automatically
rewrite intent or create a revision. Cross-horizon exposure resolution, assumptions, planner,
AI and behavioral learning are not implemented or claimed.

## Module dependency decisions

Preserve source-context ownership: planning owns plan/revision/meal; cooking owns planned
batch/allocation; shopping owns requirement/fulfillment; inventory owns reservations/ledger;
execution owns physical execution boundary and coordinates the future operational transaction.
All cross-context access uses public/contracts, not ORM imports. SQL composite FKs express
relational ownership without Python import loops.

Existing allowlist permits execution→planning/cooking/shopping/inventory/validation, but not
planning→shopping. Therefore do not place a cross-context revision transaction in planning
and bypass the checker. Planning assembles its own fragments; execution application
orchestration later combines public fragments atomically on one transaction.

A full PlanRevisionSnapshot belongs to planning contracts and contains immutable typed
shopping/cooking intent fragments. This requires a **new, contract-only planning→shopping
edge** at implementation time, with explicit negative import tests. Shopping/cooking
contracts refer to exact plan/household/revision IDs and must not import planning contracts;
this prevents recursive contract imports. Planning must not call shopping internals/public
through that new contract-only edge; operational writes stay in execution orchestration.
No allowlist changes are made by this documentation-only review.

ValidationSubjectSnapshot belongs to validation.contracts (which is already allowed to
read source contracts), composing the full intent snapshot plus independently captured
source facts. Source planning/execution fact contracts must not import that complete subject
back. Permit application happens at the orchestration boundary; source commands do not
accept a caller-constructed complete PASS artifact. Neutral app.domain remains independent
of source contexts and carries only neutral primitives/references, not a new business-policy
module. This resolves the actual import-direction ambiguity without a shared mutable graph
or a runtime import cycle.

## Adversarial review: concrete traces and expected enforcement

These are **design counterexamples**, manually traced against A–J; they are not new executed
unit/PostgreSQL tests. Actual implementation must turn the matrix into regression tests.

| Scenario | Required trace / rejection | Verdict for proposed design |
| --- | --- | --- |
| 1. Monday A→B, no execution | Revision4→5; retain A history; release only A's plan-bound future reservation; reserve B after eligibility checks; no material movement; rollback all on failure | Consistent via E/G/H; DB atomic test still required |
| 2. Chicken bought, meal→fish | Immutable600g purchase/acquire stays; retire/reduce future chicken demand; explicit release of unused chicken reservation; fish is new unfulfilled demand | Consistent via A/D/E; no DELETE/cascade path |
| 3. Monday batch cooked for Mon/Tue, Tue changes | Pin Monday batch production/composition/execution and prepared lot; revise Tuesday allocation only; leftovers remain household assets, not deleted stock | Consistent via C/F; planned_servings never overwrites produced_servings |
| 4. A/B both expect4 | A CAS4→5 succeeds; B stale rejects; unique revision prevents two5s; replay of A key returns original5 even after head6 | Consistent by G; real concurrent transaction test remains mandatory |
| 5. Ate differently, no future change requested | Append independent execution/deviation against exact advice version; diagnose effects; no implicit PlanRevision or preference update | Consistent by C/J; runtime execution deferred |
| 6. Need1000g, bought600g | 600g actual acquisition only;400g outstanding in compatible basis; price is actual600g receipt, not quote; retirement never erases spend/lot | Consistent by D; fulfillment/allocation arithmetic must be independently tested |
| 7. Due time passes, no evidence | Advice may become past/unresolved; zero consume/batch/lot events; later explicit reschedule preserves original advice | Consistent; time does not become physical truth |
| 8. Shared batch change under SINGLE_MEAL | Changing another meal's production/allocation rejected; require MULTI_MEAL with affected dependency closure | Consistent by H; no false single-meal scope |
| 9. One reservation serves two meals, retire one | Disallowed V1 shared reservation; alternatively release/reacquire with quantified ownership, never release another meal's allocation silently | Consistent with frozen M1.3 full release |
| 10. Unrelated manual reserve races revision | Household fence serializes; stale frontier invalidates PRECOMMIT; reserve failure rolls back release/head/revision | Consistent by E/G; no half-revised state |
| 11. Late cooked revision4 arrives after5 | Record immutable reality with source4; conflict diagnosis for current5; no rewriting4/5, no automatic6, no rejection merely because old advice is stale | Requires future POSTFACT workflow; not promised as implemented |
| 12. Invalid fake PASS / missing safety or inventory source | Do not activate/revise operational state; draft subject remains non-ready; reject caller boolean or report for another hash | Activation blocker explicitly preserved |
| 13. Old recipe version changes / wrong COUNT substitution | Bind immutable RecipeVersion; retain authored rules and frozen mass-only policy; cannot use latest version or old ingredient item_ref | Preserves frozen M1.2 without redesign |
| 14. Raw reservation + future prepared carryover at horizon start | Replay linked flow once; output becomes projected opening only after scheduled input consumption/production; no physical acquire from schedule | Bridge contract required, resolver deferred |
| 15. Failure after releasing A but before reserving B/head switch | Roll back entire transaction; A release disappears with uncommitted revision and B attempt; balances and head match original | Mandatory fault-injection test for implementation |

## Invariant mapping and readiness

| Canonical rules | Proposed enforcement / current limit |
| --- | --- |
| INV-003/004/020, ADR-004 | Household composite FKs, tracked identity + per-member source safety; full safety validation missing |
| INV-005/006, ADR-005 | Immutable RecipeVersion/binding/tier, explicit servings vs composition; no arbitrary culinary edits |
| INV-007/009/010, ADR-006/007/008 | Quote vs actual spend separated; no fake robust-feasible status or unaccepted relaxation |
| INV-011/012/013, ADR-009 | No planned lot/auto-consumption; explicit physical evidence remains M1.3-owned |
| INV-014, ADR-009 | Local repair advice vs explicit accepted revision; optimizer/escalation not implemented |
| INV-015–018/021, ADR-010 | Exact immutable subject/frontier + real PRECOMMIT gate; full validator/activation unavailable |
| INV-019/030, ADR-009/010 | Chronological input/output commitments and source-frontier invalidation; no bridge/batch replay implementation |
| INV-022–029, ADR-011 | No learning from revision/deviation/assumption; no behavioral code or claims |

Architecture choices are coherent with the frozen dependencies. **Operational ActivePlan
implementation is not ready to be enabled:** validation capability, full source resolution
and execution boundary facts must exist first. Proposed draft-authoring persistence can be
implemented separately without calling it operational activation or freezing F as complete.

Next implementation acceptance corpus: stable identity/revision0, immutable child/late inserts,
exact full snapshot hash/roundtrip, composite household/revision FKs, scope and cut line,
retained materialized production vs revisable allocations, quantitative partial fulfillment
seam, concurrent CAS/idempotency replay, reservation release/rebuild rollback and lock order,
invalid capability/source frontier, nonfinite/precision/basis errors, direct SQL protection,
empty/populated migrations, metadata drift, boundary/export checks and full regression/CI.
No old test may be removed/weakened. New test counts, new tables and migration0008 are not
claimed in this architecture review.

**READY FOR ARCHITECTURE/FREEZE REVIEW** — review artifact only; not F implementation complete.


## Verification of this review artifact

Local checks actually run: architecture baseline (30 invariants /11 ADRs /50 linked tasks),
16-context import boundaries, domain/OpenAPI export drift, Ruff and Git whitespace checks.
All published0001–0007 were byte-compared to the M1.3 freeze commit. No schema, ORM,
Pydantic contract, application service or existing test was changed by this review.

Runtime counts688/313 and benchmark22/22 above describe the verified M1.3 baseline;
there are **zero new Python/PostgreSQL runtime tests** for F in this review. The fifteen
counterexamples are manual design traces; they are not reported as passing transaction tests.
PR/final delivery records CI regression results on the review commit separately.
