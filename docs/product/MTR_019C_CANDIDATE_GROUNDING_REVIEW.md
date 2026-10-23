# MTR-019C — Candidate Grounding / architecture A–J

Reviewed main: `23dd0b3bc3245ac9c7ef5493968f8ab120242f00`. MTR-019B is user FROZEN
at that commit; MTR-019A/Recipe/MTR-025 semantics and migrations0001–0010 stay unchanged.
Sources: ADR-002/004/005/006/009/010; spec §14/18.3; INV-003–009/011/013/015–021.
No contradiction requires reopening a frozen slice. Scope is additive and needs no persistence.

## A. Scope: what grounded means

Implement MTR-019C, the next narrow part of canonical MTR-019, before MTR-020. A candidate
is PRIMITIVES_RESOLVED only if every selected ingredient has a compatible reviewed nutrition
reference, exact nutrient arithmetic, and at least one explicitly captured procurement or confirmed
physical source possibility. Exact authored culinary choices and participant exclusions must pass.
This is shortlist-input completeness, **not feasibility, safety-policy approval or activation**.
activation_ready remains False. Missing critical evidence yields INCOMPLETE; invalid/forbidden
choices yield REJECTED, with no eligible candidate. CulinaryCandidateDraft stays DRAFT unchanged.

## B. Ownership and dependency direction

Recipe resolves authored culinary facts/preparation outputs; Nutrition resolves compatible nutrient
references and canonical member restrictions; Retail resolves procurement evidence/supply coefficients;
Inventory resolves read-only physical possibilities. Planning assembles nested immutable facts.
No domain imports Planning to define its rules. Validation imports no producer/runtime helper.
Planning source capture uses public facades under read-only REPEATABLE READ/SERIALIZABLE;
the subsequent pure assembler performs no live reads/writes. This is coherent capture, not TOCTOU
authorization. No new table, generic yield persistence, ranking or solver dependency.

## C. Frozen culinary handoff

Take the frozen MTR-019B candidate, reload exact canonical RecipeVersion, check source hash and
recompute every ingredient/rule/quantity/tier/transformation via Recipe's existing producer resolver.
Reject forged self-consistent candidate fingerprints too. No fake plan/proposal/batch identity is
created just to call a plan-bound validator. After real selection, the existing MTR-019A adapter,
v3 seal/capture and independent RecipeGroundingValidator still apply unchanged. Producer culinary
resolution is not independent PRECOMMIT validation; this slice claims no new validation authority.

## D. Nutrition / basis

Capture canonical Ingredient/NutritionReference rows, not caller-supplied nutrients or totals.
Require exactly one compatible reviewed reference, or an explicit reference-ID selection resolved
against captured canonical rows. Duplicate/ambiguous references do not silently choose latest.
Nutrition owns exact quantity×reference arithmetic, batch totals and primitive evidence.
These are **ingredient-input composition**, not an invented nutrient-retention/as-eaten model.
EP_RAW_G uses EP_RAW references; COOKED_G uses COOKED references. Cooking mass yield never
rescales nutrient values. COUNT nutrition/count-to-mass is unsupported until an authored source
exists. Nonterminating/out-of-range Decimal arithmetic produces INCOMPLETE, never rounding.
No NutritionPolicyEngine, goal synthesis or member/day nutrient allocation is implemented.

## E. Retail/procurement evidence

Capture explicit persisted ProcurementClass/member/options, quotes and retailer-status facts.
Retail filters exact ingredient, region/currency, active retailer and nonfuture evidence. Missing
or UNAVAILABLE paths cannot silently become purchasable. UNKNOWN/reference fallback may be
represented as conditional evidence, never confirmation or guaranteed checkout.
Resolve supply coefficients by applying Product→Ingredient mapping: fixed EP per pack; catch-weight
low/expected/high EP; loose-scale minimum/step EP. Preserve original quote price/AP reference pair,
granularity, source quality, mapping and provenance. No inverse AP division or hidden rounding is
needed. No fake per-dish purchase cost or pro-rating recipe grams into checkout cost.
Freshness/outlier/scenario eligibility and basket cost evaluation are separate MTR-011/012/013 work;
grounding exposes evidence/as_of, not a claim that those policies passed.
Every supply path explicitly carries CONDITIONAL_EVIDENCE / freshness_assessment=NOT_IMPLEMENTED.

## F. Inventory

Capture household-owned confirmed snapshot at explicit as_of, with ledger sequence frontier.
Inventory computes potential exact-basis lots and explicit AP→EP paths only when the physical lot
retains its reviewed mapping. Preserve raw/prepared identity, expiry, confidence, remaining and
reservation quantities. Exclude expired/inactive/unconfirmed-quantity/fully reserved paths.
No allocation, reservation, procurement, acquire/consume or physical mutation. An individual
possibility is not a promise of supply across meals; chronology and competition remain global.

## G. Immutability / identity

Version request/source/result/DishCandidate and nested new domain facts. Capture full primitive
snapshots with explicit provenance/bases. Canonical hashes sort declared unordered fact sets;
ledger facts retain explicit occurred_at/phase/ledger_sequence. Unknown future array fields fail
serialization until order semantics are declared. Ordered kitchen steps require explicit ordinals.
Candidate hash includes source identities/provenance, member context, as_of and resolved facts.
No ORM objects or caller nutrition/procurement summaries cross the public command boundary.

## H. Unknowns / restrictions

Canonical participant identities and safety facts must belong to the household; exactly one V1
tracked participant. EXCLUDED_INGREDIENT derives rejection from actual resolved ingredient IDs.
ALLERGEN/DIET_RULE classification is absent: return INCOMPLETE (MTR-046 classification prerequisite),
never safe-by-name or a planner is_safe flag. Missing nutrition, ambiguous sources, COUNT nutrition,
no procurement/physical path and unsupported basis/precision are explicit incomplete findings.
Unknown retail availability is a warning/conditional source, not a quantity guarantee.

## I. MTR-020 seam / unresolved global decisions

Legally eligible **input** to future MTR-020 must carry: reviewed resolved culinary identity;
exact tier/servings/ingredient bases; selected nutrition references and exact input composition;
separate Recipe cooking-yield facts; primitive procurement options with Retail edible yields and
granularity coefficients OR confirmed physical possibilities; canonical participant/restriction
context without unresolved hard classification. Exclusions must pass; zero blocking findings.

Remain unresolved until later global resolution: selected lot allocations; shared reservations;
integer package/loose purchase quantities; primary/backup/scenario purchases and actual basket cost;
batch/meal/member serving allocation; chronological feasibility; cross-meal resource competition;
root nutrition/goal policy and production validation/commit. These are not unresolved culinary choices.
MTR-020 itself is not implemented or certified ready: its scoring/quality policy still requires its
own approved design. Full MTR-019 stays PARTIAL (broader grounding/quality coverage remains);
full MTR-026 and production PRECOMMIT remain incomplete.
Future MTR-020 must consume the canonical grounding service output, not treat a caller-serialized
shortlist_input_ready flag or fingerprint as authentication/validation authority.

## J. Counterexamples

- Forged culinary ingredient/quantity with correct-looking hash: recomputation rejects.
- User submits nutrients/quotes through command: extra-forbid rejects; only source IDs accepted.
- Nutrition raw/cooked mismatch, duplicate references, COUNT or nonfinite arithmetic: incomplete.
- Raw nutrition plus cooking mass loss: no fabricated nutrient-retention transformation.
- Reference fallback/UNKNOWN availability: explicit conditional evidence, no stock or guarantee.
- Fixed500g pack with60,000/1000g quote: preserve price pair; never call60,000 purchase cost.
- Catch/loose paths: distinct coefficients, no fixed-pack semantics.
- Bought stock after a plan revision, prepared lot, reservations: read only, no identity rewriting.
- Source ordering changes: same canonical identity; provenance or quantity changes: different identity.
- Missing classification for one shared member: whole candidate incomplete, not averaged safety.
