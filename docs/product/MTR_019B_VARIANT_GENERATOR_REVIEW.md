# MTR-019B — Demand-driven culinary VariantGenerator

Reviewed main: `4a6207ac52bc5ba0ce95de2df54c0c949f36066e`. Architecture recorded
before runtime changes. ADR-005/010, spec §14.1–14.7, INV-005/006/015–018/021;
frozen Recipe v1, MTR-019A and MTR-025 inspected. No architecture contradiction found.

## A. Scope and ownership

Recipe owns authored possibilities and a pure, deterministic generator. The generator consumes
an immutable reviewed RecipeVersionSnapshot, culinary demand and explicit resource limits.
It returns immutable culinary candidates, generation triggers and rejected-path diagnostics.
Planning owns the later selected binding; household/plan/proposal/batch ownership begins there.
Candidates are DRAFT, activation_ready=False: not fully grounded DishCandidates, safety clearance,
nutrition facts, retail quotes, inventory allocations or evidence of execution.
No persistence is required; no migration or tables. Frozen migrations0001–0010 stay unchanged.

## B. Demand/context and authored rules

Demand supplies exact serving counts (default: authored base tier), ingredient target IDs,
explicit sets of authored rule IDs, and ingredient exclusions. These are caller selection hints,
not verified inventory, expiry, price, nutrition or member-safety evidence. Unknown target IDs
do not invent a path. Unknown serving counts/rule IDs reject demand explicitly.
For each requested authored tier consider default; each rule whose replacement matches a target;
each approved combination whose replacement ingredients all match targets; and explicit rule sets.
No Cartesian product, equivalence inference, nearest-tier rounding or recipe-method change.
Output is complete only for this finite demand expansion, never exhaustive over all legal variants.

## C. Structural and nonstructural choices

At most one rule per requirement. More than one structural rule requires the exact selected set
to match an approved combination. Extra nonstructural rules cannot be appended to such a combo
without exact approval. Nonstructural sets can be requested explicitly; no powerset enumeration.
Different rules yielding the same ingredient remain distinct authored provenance paths.

## D. Quantity, scaling and portions

Use only complete authored tier quantities; LINEAR/SUBLINEAR/FIXED/DISCRETE/TO_TASTE are
interpreted by frozen Recipe contracts/resolver, not interpolation or a new policy engine.
MTR-019B always emits explicit zero adjustment for every requirement. Bounded post-selection
refinement belongs to MTR-030, not this generator. No delta grid, endpoint sampling or residual
absorption. Servings come only from the selected tier, never ingredient mass.

## E. Preparation and COUNT

Resolve the exact authored ingredient path and its net preparation transformation. A raw base
remains valid when only the substitute has a transformation. A cooked base replacement missing
its own transformation is rejected. No global yield or method inference; Retail AP→EP remains
separate from Recipe EP_RAW→COOKED. COUNT default paths retain item_ref; COUNT substitution
remains forbidden by frozen Recipe aggregate validation. Count-to-mass conversion is deferred.

## F. Identity and determinism

Version all new request/candidate/result contracts. A source hash canonicalizes only unordered
Recipe fact collections (including tier quantities and combo rule sets), preserving procedure text
and every primitive/provenance value. Future ordered steps require explicit ordinals, not sorting.
Candidate fingerprint includes source hash, recipe/tier/servings, selected rules, resolved quantities
and transformations. Exclude demand triggers from culinary identity; merge triggers for the same
candidate. Preserve distinct selected rule identities. No random UUIDs, clock, DB or ambient Decimal
context. Sort source sets, selections, findings and final candidates by explicit stable keys.

## G. Limits and failures

Caller-configured max_attempts bounds tier×unique-selection resolutions; max_candidates bounds
unique outputs. These are resource controls, not learned thresholds or ranking policy. On either
overflow return LIMIT_EXCEEDED with **no candidates**, never an arbitrary truncated shortlist.
Invalid demand returns INVALID_DEMAND; unsupported schema/invalid authored snapshots raise contract
errors. Invalid authored selection/path is rejected with a structured diagnostic while independent
valid paths may survive. Excluded paths never pass. If no path survives return NO_CANDIDATES;
this does not prove global infeasibility. Unexpected programmer errors must propagate, not vanish.

## H. Frozen binding and independent validator handoff

An explicit planning adapter takes candidate + exact RecipeVersion + planning owner/provenance,
revalidates source identity and recomputes culinary resolution before calling the existing
author_binding producer. Candidate hash is not authority. Binding schema/hash/seal/revision semantics
remain unchanged. Persist through the existing v3 proposal transaction, capture the frozen
culinary-validation-input.v1, then run the independent RecipeGroundingValidator. It never imports
the generator or producer and can reject forged selected bindings even with self-consistent hashes.

If several authored combination identities authorize the same exact rule set, the adapter uses
the lowest canonical combination ID. This is deterministic provenance selection, not ranking;
the frozen author_binding itself is unchanged. Generation triggers are transient context, not
new durable plan truth; the binding retains exact RecipeVersion/rule/transform/combination facts.

## I. Deferred boundaries

No ranking/score/Pareto/MTR-020, optimizer/MTR-021/022, nutrition/procurement/inventory resolution,
MTR-030 refinement, execution, assumptions, production PRECOMMIT/TOCTOU issuer or full validator.
Generation trigger INGREDIENT_TARGET does not claim INVENTORY_MATCH/PRICE_ADVANTAGE/etc. Those
explanations require downstream evidence. Full MTR-019 and MTR-026 remain incomplete.

## J. Adversarial review

- Two targeted structural substitutions without approved combo: only singles; explicit pair rejected.
- Approved pair plus extra nonstructural rule: rejected unless exact set approved.
- Same selection requested twice/from several contexts: one candidate with merged triggers.
- Same ingredient via different authored rules: separate candidates/provenance.
- Unknown ingredient target/unsupported portion: no invented substitution/tier.
- More candidates than budget: no partial set and no ranking claim.
- Different tuple ordering/Decimal spelling/ambient precision: same hashes and candidate ordering.
- Forged candidate ingredient or source hash: adapter rejects; validator independently rejects
  forged selected binding even if producer checks are bypassed.
- Generated selected binding persists/seals/captures via existing0010 with no stock movement;
  malformed direct SQL still fails under frozen seal/FK checks.

Decision: implement additive contracts, pure Recipe generation, selected-binding adapter and tests.
MTR-019A is user FROZEN at the reviewed commit; MTR-019B will be submitted, not self-frozen.
