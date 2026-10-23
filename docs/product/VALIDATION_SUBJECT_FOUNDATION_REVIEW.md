# MTR-025 — ValidationSubject v1 / Independent Validator foundation review

2026-10-23. Architecture review before code; implementation scope is a foundation subset,
not a complete production Independent Validator or authorization gate.

## A. Frozen boundary

MTR-016 is user **APPROVED/FROZEN** at main751a40e847dd2e664a6fe3667c272bc740a44e49,
schema0009,52 tables. Stable identity, immutable full proposal/revision history, old/new
dependency closure, own-anchor cut line, independent materialization pins, atomic reservation
effects and v1 compatibility are closed. No concrete contradiction was found. This slice
does not change them or migrations0001–0009.

MTR-016 does not supply production validation authority, root nutrition policy, exact
grounded variant/composition, actual purchase allocation/cost or CookingBatchExecution.
Its authorization insert guard remains installed and fail-closed.

## B. Actual dependency graph

Frozen household/catalog + Retail + Recipe + Inventory + Plan proposal/revision sources
→ coherent read-only source capture (application orchestration, stable DB snapshot)
→ MTR-025 immutable self-contained validation subject, policy/source hashes
→ MTR-026 independent supported primitive checks and structured diagnostics
→ deferred full root policy, grounding/scenario/bridge/execution inputs + complete suite
→ deferred production PRECOMMIT authority/source-frontier commit recheck
→ later CookingBatchExecution / execution materialization.

G in the M0/M1 blueprint is a completion audit, not permission to invent M1.4 or bypass
validation. MTR-025/026 are existing canonical backlog IDs. MTR-006 full policy synthesis
is required before production nutrition/root-policy PASS, but not before building this
honest partial immutable input boundary. No second NutritionPolicyEngine is introduced.

## C. Selected slice

**MTR-025 ValidationSubject v1 foundation, with the source-supported subset of MTR-026.**
Subject v1 is explicitly FOUNDATION_ONLY/validation_ready=False. It captures household and
canonical members/constraints, exact sealed proposal + revision/source frontier, authored
default RecipeVersion/tier facts, ingredient identities/nutrition references and physical
Inventory primitive arrays. Supported validators independently check identity/exclusions,
default recipe source/tier, compatible nutrient arithmetic, yield estimates, conservation,
chronological stock/reservations/expiry and raw/prepared identity. These estimates are not
physical output, final per-member meal nutrition or planned material allocation feasibility.

Unknown allergen/diet classification is an error, never an empty-safe set. Missing policy,
scenario resolution, complete grounding, batch-flow, assumptions and bridge inputs remain
typed deferred capabilities. Callers cannot label a partial report production-ready or mint
authority. PRECOMMIT is blocked; POSTFACT reports diagnostics without mutating/rejecting reality.

No new tables or migration: subject/report are immutable contract artifacts, not another
source of truth. The existing52-table persistence continues supplying canonical facts.

## D. Ownership

- households/nutrition/catalog own read-only canonical source contracts/facades; Recipe
  public facade exposes its existing repository read without exposing ORM instances.
- policy owns immutable validation coverage definitions and policy identity/hash, with
  provenance; this policy defines the supported checks, not clinical numeric defaults.
- execution application capture coordinates source public facades under REPEATABLE READ
  or SERIALIZABLE; no hidden reads are performed by the validator. READ COMMITTED capture
  is rejected so mutable safety and plan/inventory cannot drift between source reads.
- validation owns subject/report, deterministic canonicalization, finding/proof contracts,
  orchestration and independently written checks. It imports source contracts and neutral
  types only, never runtime facades/ORM/solver/recipe binder or Inventory replay helpers.
- Household owns physical lots; proposed shopping and reservations do not create matter.
  Validation reports own no material or repair state.

## E. Canonical invariants (exact wording)

- INV-013 — Inference may update a projection; only evidence may update confirmed reality.
- INV-015 — Validation verifies correctness, not optimality.
- INV-016 — Policy definitions may be shared; correctness enforcement must be independently evaluated.
- INV-017 — Critical validation derives from resolved primitive facts, not planner-computed summaries.
- INV-018 — Primitive facts must carry explicit measurement basis and provenance before independent recomputation.
- INV-019 — Material feasibility must hold globally and at every causal point in time.
- INV-020 — Root contract validation must not trust planner-resolved safety summaries.
- INV-021 — Validation of intent is gating; validation of reality is diagnostic.

ADR-010/spec18 require global conservation AND causal replay; one does not substitute for
the other. Source/household identity and unsupported safety are checked independently of
any supplied summary. Source contract validation is not treated as proof of complete validity.
INV-003/004/005/006/011/012/030 boundaries remain relevant; none is claimed complete here.

## F. Deferred and adversarial acceptance

No policy synthesis/clinical guidance, catalog allergen inference, variant generator,
ProcurementCostEvaluator/scenario validator, planned allocation resolver, batch execution,
assumptions, projections, bridge, solver/optimality/ranking, repair, AI or UX. No production
authorization issuance. Exact grounded binding is still required before execution.

Adversarial cases: forbidden ingredient for one shared participant; missing/cross-household
member; unknown safety code; forged safe summary; missing recipe/nutrition/basis evidence;
nonterminating calculation without rounding; closing-balance mismatch; consume before
acquire/after expiry; duplicate causal order; reservation mistaken for stock; raw/prepared
identity conflation; stale/missing source revision; postfact diagnostics preserving history;
no DB/write imports or calls during validation; semantic hash invariant under ordering.

## G. Blockers

No architecture contradiction blocks this foundation. The missing capabilities above are
real production authorization blockers, not facts to fabricate or silently waive. Reports
must include the gap and remain non-authorizing even when all supported checks pass.
The foundation is submitted for architecture/freeze review, not full MTR-026 completion.
