# M1.2 Recipe / Preparation — architecture review before implementation

Baseline: V1.3 §8.4 seam 1, §14, §18; ADR-005/009/010; INV-005/006/017/018.
M1.1 at f49e9b1 is reviewed and approved to freeze. No contradiction found; no
Foundation or Retail ownership redesign is needed. This review precedes code.

## A. Identity and immutable authored version

Recipe is a stable global culinary identity, including its cooking-method identity.
RecipeVersion is an immutable aggregate with positive integer version, procedure text,
serving definition, provenance and review status. Every correction creates another
version. Versions and all children are inserted atomically and sealed; adding a child
later must be rejected as strongly as UPDATE/DELETE/TRUNCATE. No lifecycle until needed.

## B. Ingredient requirements and basis

Each version owns named required ingredient slots, ingredient FK, positive StoredQuantity,
culinary role, scaling policy and adjustment envelope. V1 supports EP_RAW_G, COOKED_G,
and contextual COUNT. AP_G and SERVING are not ingredient requirements. COUNT uses an
explicit item definition and does not imply grams; all slots are required in this slice.
Optional omission rules and count-to-mass conversion are deferred.

## C. Preparation transformations

Version-owned transformations reference a slot and its actual base/substitution ingredient,
preparation key, method, positive factor, version and provenance. Only
EP_RAW_G -> COOKED_G is supported. Several transformation records are alternatives for
different authored ingredient bindings, never an implicit chain. Selecting a substituted
raw slot requires its own transformation if the original slot has one. Method must match
the Recipe identity. AP->EP remains exclusively M1.1 Product->Ingredient mapping;
no retail mapping or generic persisted yield abstraction is copied here.

## D. Authored substitution

One contextual rule replaces one slot with an ingredient at an exact quantity factor,
preserving its measurement basis/item definition. Rule identity, version and provenance
are explicit. At most one structural rule may be selected unless the exact selected
rule set is an authored approved combination. One selected rule per slot. Combinations
are relational membership sets scoped to the same version; no global compatibility table.
Different cooking method requires a different Recipe, never a substitution rule.

## E. Scaling versus adjustment

V1 production sizes are explicitly authored tiers, including a tier equal to base_servings.
Each tier supplies every slot's unadjusted quantity. LINEAR must match exact proportional
scaling, FIXED must equal base, SUBLINEAR uses authored monotonic points with growth less
than proportional, DISCRETE requires exact multiples of an authored quantum, TO_TASTE
requires an authored absolute min/max range. No invented exponent, rounding or continuous
interpolation. Arbitrary continuous production sizes are intentionally deferred.

Adjustment is a separate absolute delta in the slot's basis, applied after scaling and
substitution: NONE=0, SMALL=symmetric bounded delta, PORTIONABLE=bounded delta,
DISCRETE=bounded step-aligned delta. Bounds include zero; every tier and allowed binding
must remain positive at the lower bound. Discrete scaling remains step-aligned after
adjustment. Calculation retains precision; storing calculated output requires the existing
explicit QuantizationPolicy. No calculated candidate quantities are persisted in M1.2.

## F. Serving and portion semantics

Serving definition belongs to the immutable version, with an explicit contextual key and
description. Base servings and each tier's servings are authored numbers, not total grams.
Tier selection sets serving count; +60g adjustment cannot change it. Recipe production
tiers and later member allocation/produced-servings events remain distinct. Tier names
may express STANDARD/HIGH_PROTEIN etc.; unique serving counts are the V1 production-size
policy (composition-only alternate tiers at identical counts deferred).

## G. Grounded boundary

GroundedRecipeVariantDraft embeds the complete RecipeVersion snapshot, exact selected rules,
tier, resolved ingredient identities/CalculatedQuantities, matching transformations,
canonical VariantReason, deterministic fingerprint and derivation provenance/policy version.
It recomputes culinary binding/envelope/serving/yield consistency from primitives, without
cached valid=true. DRAFT and activation_ready=False are mandatory: nutrition, household
safety, retail/inventory resolution and independent precommit validation are missing.
This contract is not a solver-ready DishCandidate and does not implement a generator.

## H. Tables, trade-offs and deferred scope

Ten tables: recipes, recipe_versions, recipe_ingredients, recipe_portion_tiers,
recipe_tier_quantities, recipe_variant_rules, recipe_rule_combinations,
recipe_combination_members, preparation_transformations, recipe_version_seals.
Serving definition/procedure live on the version; typed scaling and adjustment columns
live on ingredient rows, avoiding redundant one-to-one policy tables. Composite FKs bind
children to their version and slot. A deferred seal FK and insert guards freeze complete
aggregates; seal validation checks relational completeness and tier arithmetic. The DB
stamps an assembly transaction identity and permits child writes only in that transaction,
including nested savepoints. This also rejects stale REPEATABLE READ insertion after commit.
Provenance kinds USER_AUTHORED/CURATED_REFERENCE/IMPORTED_DRAFT are contextual Recipe
types; source provenance and DRAFT/REVIEWED status are separate. Imported drafts cannot
claim REVIEWED; human review creates a new version with reviewed authorship provenance.

Deferred: production AI/import, VariantGenerator, CulinaryAdjustmentPass service,
full independent validators, nutrition totals/resolver, procurement costs, physical
inventory, CookingBatch/PreparedFoodLot execution, ActivePlan and Planner V4.
Migration 0005 is frozen DDL/SQL; 0001-0004 remain unchanged. Populated recipe downgrade
fails closed. Recipe core only imports neutral/shared primitives and Catalog contracts;
Retail does not depend on Recipes. No JSONB is needed.
