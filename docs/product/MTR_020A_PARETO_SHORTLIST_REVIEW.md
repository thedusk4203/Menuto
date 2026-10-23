# MTR-020A — Conservative Pareto Shortlist Foundation

Reviewed main: `ffaa009031d8def0e32a654266a871cced44d35e`. Architecture recorded before
runtime implementation. MTR-019A/B/C are user FROZEN, C at this commit. Schema0010,
54 domain tables; migrations0001–0010 and frozen wire/hash semantics stay unchanged.

## A. Frozen boundary and remaining MTR-019

A persists exact authored selected culinary intent; B generates finite authored possibilities;
C captures canonical sources and resolves supported candidate-local primitives. C is not global
feasibility, as-eaten nutrition, a price guarantee, safety-policy clearance or PRECOMMIT authority.
Full MTR-019 remains PARTIAL. Evidence-backed generation reasons are not used for pruning;
mechanical triggers remain explanation context only. COUNT nutrition/count-to-mass needs an
authored measurement source (MTR-003/014/046); allergen/diet classification needs catalog truth
(MTR-046). Unknown restrictions/unsupported bases remain blocked by C. Freshness/outlier/scenario
eligibility belongs to MTR-011/012/013, not an invented shortlist quality score.

## B. Dependency decision

RecipeVersion → frozen B generator → frozen C canonical grounding → **MTR-020A** → later
MTR-020 role/policy portfolio → MTR-021 feasibility → MTR-022 optimization.
Selected candidates still pass frozen A binding/seal and independent RecipeGroundingValidator.
None of the deferred MTR-019 responsibilities is needed to compare *exact source-path coverage*
within an otherwise identical supported candidate. No unresolved fact is converted into a metric.
This is a conservative sub-slice of canonical MTR-020 (issue21), not full MTR-020 completion.

| Remaining responsibility | Canonical prerequisite | Impact on this supported scope |
| --- | --- | --- |
| Evidence-backed generation reasons | Remaining MTR-019 context/evidence orchestration | Not a comparison dimension; preserve mechanical trigger/context, never assert price/expiry reason. |
| Source quality/freshness/scenarios | Remaining MTR-011/012/013 policy/evidence work | Preserve conditional facts exactly; no quality score, availability guarantee or spend claim. |
| COUNT nutrition/count-to-mass | MTR-003/014 basis boundary and MTR-046 authored catalog source | Frozen C returns INCOMPLETE for unsupported COUNT; cannot enter eligible frontier. |
| Allergen/diet classification | MTR-046 canonical ingredient classification prerequisite | Frozen C blocks unresolved hard classification; no name-based safety inference. |
| Role-aware nutrient/goal fit | MTR-006/007/008 policy and role/serving allocation primitives | Exact composition retained, no directional nutrient metric invented. |
| Marginal checkout economics | Remaining MTR-011/012/013 and global package/material resolution | Price/reference pairs retained, never compare prorated grams as purchase cost. |
| Effort/preference/exposure roles | MTR-024/039/040/041 canonical utility/exposure sources | No role quota or fabricated novelty/effort; preserve distinct culinary possibilities. |

These gaps block broader ranking/portfolio claims, not exact optional source containment. If any
future comparison needs one of these facts, add the prerequisite first; do not default it to zero.

## C. Representation and ownership

Planning owns immutable versioned policy/result/witness contracts, a process-local captured pool,
a read-only capture adapter and a pure shortlist core. No persistence/migration is warranted.
The public capture adapter accepts only CandidateGroundingRequest values, invokes frozen
ground_candidate in one clean read-only RR/SERIALIZABLE transaction, then issues a non-wire pool.
The pure core accepts only that pool, never raw caller GroundedDishCandidate/result/JSON. A
fingerprint/shortlist_input_ready flag does not establish canonical capture. The internal mint
boundary is trusted server code, not cryptographic authentication or a production capability.
Pool/result are non-authorizing; deserializing a result cannot restore ingress eligibility.
No DB, source re-grounding or domain resolution occurs in the pure core.

## D. Comparison semantics

Comparison partition includes the entire request except procurement-class selection, all
non-retail sources (including complete physical snapshot/member restrictions/reference provenance),
exact resolved nutrition and inventory paths, preparation outputs, culinary rules/triggers,
servings/tier and cutoff. No comparison across any difference in these primitives.

Within one partition compare **sets of exact immutable facts**, not price/availability scores:
per-requirement procurement paths, complete captured ProcurementSnapshots and retailer statuses.
A dominates B only if all three sets of A contain B's sets and the resolved path set is a strict
superset. The survivor retains every quote/package/mapping/status/provenance alternative of B;
extra conditional choices are optional evidence, never required purchases or guaranteed supply.
Including complete source facts prevents hiding a different source frontier behind equal totals.
No numerical nutrition direction/target, checkout cost, kitchen effort, taste or fragility weight
is manufactured. Different recipes, tiers, rules, references, lots, participants, timestamps,
prices or non-contained evidence alternatives survive. This intentionally prunes little.

## E. Determinism, duplicates and ties

Deduplicate exact grounded fingerprints only, after canonical capture. Different provenance with
equal arithmetic is not a duplicate. Equal coverage without exact identity remains a tie and both
survive. Sort final candidates/failures/witnesses explicitly; choose lowest frontier fingerprint
when several survivors cover the same removed input. A witness binds removed/survivor identities
and comparison partition. Original candidate values/provenance/hashes are returned unchanged.
Policy is explicit/versioned; input/frontier limits are resource budgets, not learned quotas.
On overflow return no candidates, never cheapest-first/random truncation. Any failed grounding
returns GROUNDING_FAILED with diagnostics and no eligible output; EMPTY does not prove infeasibility.

## F. Portfolio and deferred dimensions

The frontier preserves structural diversity rather than guessing missing role/effort/utility facts.
No EXPLOIT/EXPLORE assignment is claimed: MTR-024/039/040/041 evidence/policies do not yet exist.
No full role-aware ShortlistPortfolioPolicy/quota implementation or MTR-020 closure is claimed.
Future target-aware nutrition, structural economics, inventory/expiry rescue and role reserves
need their own canonical source/policy/review; they cannot silently broaden this coverage relation.

## G. Invariants

INV-003/004: preserve household/member identities and every participating member restriction.
INV-005/006: retain exact authored culinary possibilities, no new choices or quantity adjustment.
INV-007/008/009: quotes remain evidence, no cheapest-starvation/probability claim.
INV-011/013: inventory is confirmed material truth, no reservation/projection/physical mutation.
INV-015–018/020/021: no validator/optimality/safety-summary authority; retain primitive provenance
and explicit bases; PRECOMMIT remains fail-closed. INV-019 global/causal feasibility is deferred.

## H. Adversarial review before implementation

- Same recipe/nutrition/inventory/context; classA vs classA+classB: remove the narrower candidate
  only when exact paths AND complete source sets are contained; preserve all facts in survivor.
- Cheaper dish/different ingredient/tier/reference/lot/cutoff: different partition or incomparable;
  never discard by fabricated cost/nutrition ranking.
- Two different package paths, equal counts: neither covers the other; preserve both.
- New quote replacing old quote: not set containment; preserve both, no implicit latest/freshest.
- Unknown retail availability/reference baseline: optional conditional evidence, not checkout stock.
- Forged self-consistent candidate hash/ready flag: not accepted at public ingress; canonical
  request capture reloads sources. INCOMPLETE/REJECTED cannot mint an eligible shortlist.
- Pool reordered/retried: deterministic result identity; exact duplicates do not alter frontier.
- Too many incomparable candidates: explicit failure, never lose structural diversity silently.
- Competing inventory/late materialization: no lot allocations/feasibility/commit authority asserted.

No blocker/contradiction found. Implement this single additive slice; no execution or following
milestone. Submit READY FOR ARCHITECTURE/FREEZE REVIEW, do not self-freeze.
