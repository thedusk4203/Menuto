"""ADR-005: authored culinary truth, independent of procurement and household assets."""

from decimal import Inexact, Rounded, localcontext
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, TypeAdapter, model_validator

from app.domain.contracts import (
    Contract,
    Identifier,
    Label,
    PersistedDecimal,
    PositiveDecimal,
    Sha256,
)
from app.domain.units import CalculatedQuantity, MeasurementBasis, Provenance, Quantity

PositiveVersion = Annotated[int, Field(strict=True, gt=0, le=2_147_483_647)]


class RecipeProvenance(Provenance):
    kind: Literal["USER_AUTHORED", "CURATED_REFERENCE", "IMPORTED_DRAFT"]


class RecipeContract(Contract):
    contract_version: Literal["recipe-v1"] = "recipe-v1"


class RecipeFact(RecipeContract):
    id: UUID
    name: Label
    cooking_method: Identifier


class ScalingKind(StrEnum):
    LINEAR = "LINEAR"
    SUBLINEAR = "SUBLINEAR"
    FIXED = "FIXED"
    DISCRETE = "DISCRETE"
    TO_TASTE = "TO_TASTE"


class ScalingPolicy(RecipeContract):
    kind: ScalingKind
    quantum: PositiveDecimal | None = None
    minimum: PositiveDecimal | None = None
    maximum: PositiveDecimal | None = None

    @model_validator(mode="after")
    def shape(self):
        if (self.quantum is not None) != (self.kind == ScalingKind.DISCRETE):
            raise ValueError("Only DISCRETE scaling requires a quantum")
        if self.kind == ScalingKind.TO_TASTE:
            if self.minimum is None or self.maximum is None or self.minimum > self.maximum:
                raise ValueError("TO_TASTE requires ordered positive absolute bounds")
        elif self.minimum is not None or self.maximum is not None:
            raise ValueError("Only TO_TASTE scaling takes bounds")
        return self


class AdjustmentKind(StrEnum):
    NONE = "NONE"
    SMALL = "SMALL"
    PORTIONABLE = "PORTIONABLE"
    DISCRETE = "DISCRETE"


class QuantityAdjustmentPolicy(RecipeContract):
    kind: AdjustmentKind
    min_delta: PersistedDecimal
    max_delta: PersistedDecimal
    step: PositiveDecimal | None = None

    @model_validator(mode="after")
    def shape(self):
        if not self.min_delta <= 0 <= self.max_delta:
            raise ValueError("Adjustment bounds must contain zero")
        if self.kind == AdjustmentKind.NONE:
            if self.min_delta != 0 or self.max_delta != 0:
                raise ValueError("NONE allows no delta")
        elif self.min_delta == self.max_delta:
            raise ValueError("Non-NONE adjustment needs a nonzero envelope")
        if self.kind == AdjustmentKind.SMALL and self.min_delta != self.max_delta.copy_negate():
            raise ValueError("SMALL uses a symmetric authored absolute delta")
        if (self.step is not None) != (self.kind == AdjustmentKind.DISCRETE):
            raise ValueError("Only DISCRETE adjustment requires a step")
        with localcontext() as ctx:
            ctx.prec = 160
            ctx.traps[Inexact] = ctx.traps[Rounded] = True
            if self.step is not None and (
                self.min_delta % self.step != 0 or self.max_delta % self.step != 0
            ):
                raise ValueError("DISCRETE bounds must align to step from zero")
        return self


class RecipeIngredientFact(RecipeContract):
    id: UUID
    recipe_version_id: UUID
    slot: Identifier
    ingredient_id: UUID
    quantity: Quantity
    role: Identifier
    scaling: ScalingPolicy
    adjustment: QuantityAdjustmentPolicy

    @model_validator(mode="after")
    def recipe_basis(self):
        if self.quantity.amount <= 0 or self.quantity.basis not in {
            MeasurementBasis.EP_RAW_G,
            MeasurementBasis.COOKED_G,
            MeasurementBasis.COUNT,
        }:
            raise ValueError("Recipe requires positive edible raw/cooked mass or contextual COUNT")
        return self


class TierQuantity(RecipeContract):
    requirement_id: UUID
    amount: PositiveDecimal


class RecipePortionTierFact(RecipeContract):
    id: UUID
    recipe_version_id: UUID
    key: Identifier
    servings: PositiveDecimal
    quantities: tuple[TierQuantity, ...]


class RecipeVariantRuleFact(RecipeContract):
    """V1 mass-only substitution; replacement COUNT identity/conversion is deferred."""

    id: UUID
    recipe_version_id: UUID
    key: Identifier
    version: PositiveVersion
    requirement_id: UUID
    replacement_ingredient_id: UUID
    quantity_factor: PositiveDecimal
    structural: bool = Field(strict=True)
    provenance: RecipeProvenance


class RecipeRuleCombinationFact(RecipeContract):
    id: UUID
    recipe_version_id: UUID
    key: Identifier
    rule_ids: tuple[UUID, ...]
    provenance: RecipeProvenance


class PreparationTransformationFact(RecipeContract):
    """Net EP_RAW→COOKED yield under Recipe context, not multi-step preparation."""

    id: UUID
    recipe_version_id: UUID
    requirement_id: UUID
    ingredient_id: UUID
    preparation_key: Identifier
    method: Identifier
    version: PositiveVersion
    source_basis: Literal[MeasurementBasis.EP_RAW_G] = MeasurementBasis.EP_RAW_G
    target_basis: Literal[MeasurementBasis.COOKED_G] = MeasurementBasis.COOKED_G
    factor: PositiveDecimal
    provenance: RecipeProvenance


def unique(values, label):
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {label}")


class RecipeVersionSnapshot(RecipeContract):
    id: UUID
    recipe: RecipeFact
    version: PositiveVersion
    serving_definition: Identifier
    serving_description: Label
    base_servings: PositiveDecimal
    procedure: Annotated[str, Field(min_length=1, max_length=100_000, pattern=r"\S")]
    provenance: RecipeProvenance
    review_status: Literal["DRAFT", "REVIEWED"]
    ingredients: Annotated[tuple[RecipeIngredientFact, ...], Field(min_length=1)]
    portion_tiers: Annotated[tuple[RecipePortionTierFact, ...], Field(min_length=1)]
    variant_rules: tuple[RecipeVariantRuleFact, ...] = ()
    approved_combinations: tuple[RecipeRuleCombinationFact, ...] = ()
    transformations: tuple[PreparationTransformationFact, ...] = ()

    @model_validator(mode="after")
    def authored_aggregate(self):
        if self.review_status == "REVIEWED" and any(
            p.kind == "IMPORTED_DRAFT"
            for p in (
                self.provenance,
                *(r.provenance for r in self.variant_rules),
                *(c.provenance for c in self.approved_combinations),
                *(t.provenance for t in self.transformations),
            )
        ):
            raise ValueError("Imported draft evidence cannot masquerade as reviewed authorship")
        for rows, key in (
            (self.ingredients, "slot"),
            (self.portion_tiers, "key"),
            (self.variant_rules, "key"),
            (self.approved_combinations, "key"),
        ):
            unique([r.id for r in rows], "identity")
            unique([getattr(r, key) for r in rows], key)
        unique([t.servings for t in self.portion_tiers], "tier serving count")
        unique([t.id for t in self.transformations], "transformation identity")
        unique(
            [(t.requirement_id, t.ingredient_id) for t in self.transformations],
            "binding transformation",
        )
        children = (
            *self.ingredients,
            *self.portion_tiers,
            *self.variant_rules,
            *self.approved_combinations,
            *self.transformations,
        )
        if any(c.recipe_version_id != self.id for c in children):
            raise ValueError("Cross-version child")
        requirements = {i.id: i for i in self.ingredients}
        rules = {r.id: r for r in self.variant_rules}
        for rule in self.variant_rules:
            item = requirements.get(rule.requirement_id)
            if item is None or item.ingredient_id == rule.replacement_ingredient_id:
                raise ValueError(
                    "Substitution requires an authored slot and a different ingredient"
                )
            if item.quantity.basis == MeasurementBasis.COUNT:
                raise ValueError(
                    "V1 COUNT substitution requires deferred replacement count identity"
                )
        for combo in self.approved_combinations:
            unique(combo.rule_ids, "combination member")
            if len(combo.rule_ids) < 2 or any(r not in rules for r in combo.rule_ids):
                raise ValueError("Combination needs at least two same-version authored rules")
            unique([rules[r].requirement_id for r in combo.rule_ids], "combination slot")
        for transformation in self.transformations:
            item = requirements.get(transformation.requirement_id)
            allowed = {item.ingredient_id} if item else set()
            allowed.update(
                r.replacement_ingredient_id
                for r in self.variant_rules
                if r.requirement_id == transformation.requirement_id
            )
            if (
                item is None
                or item.quantity.basis != MeasurementBasis.EP_RAW_G
                or transformation.ingredient_id not in allowed
                or transformation.method != self.recipe.cooking_method
            ):
                raise ValueError("Cooking transformation requires authored raw binding and method")
        if not any(t.servings == self.base_servings for t in self.portion_tiers):
            raise ValueError("A base-serving tier is required")
        for tier in self.portion_tiers:
            unique([q.requirement_id for q in tier.quantities], "tier slot")
            if {q.requirement_id for q in tier.quantities} != requirements.keys():
                raise ValueError("Every tier must supply every required slot exactly once")
        # All arithmetic uses a bounded exact context, independent of ambient Decimal settings.
        from decimal import Inexact, Rounded, localcontext

        with localcontext() as ctx:
            ctx.prec = 160
            ctx.traps[Inexact] = ctx.traps[Rounded] = True
            for item in self.ingredients:
                points = sorted(
                    (
                        t.servings,
                        next(q.amount for q in t.quantities if q.requirement_id == item.id),
                    )
                    for t in self.portion_tiers
                )
                for servings, amount in points:
                    p, a = item.scaling, item.adjustment
                    base = item.quantity.amount
                    if servings == self.base_servings and amount != base:
                        raise ValueError("Base tier must reproduce base ingredient quantity")
                    if p.kind == ScalingKind.LINEAR and (
                        amount * self.base_servings != base * servings
                    ):
                        raise ValueError("LINEAR tier must be exactly proportional")
                    if p.kind == ScalingKind.FIXED and amount != base:
                        raise ValueError("FIXED quantity cannot change with production size")
                    if p.kind == ScalingKind.TO_TASTE and not p.minimum <= amount <= p.maximum:
                        raise ValueError("TO_TASTE tier exceeds authored bounds")
                    factors = [
                        1,
                        *(
                            r.quantity_factor
                            for r in self.variant_rules
                            if r.requirement_id == item.id
                        ),
                    ]
                    for factor in factors:
                        bound = amount * factor
                        if bound + a.min_delta <= 0:
                            raise ValueError("Adjustment would remove a required ingredient")
                        if p.kind == ScalingKind.DISCRETE and (
                            bound % p.quantum != 0
                            or a.min_delta % p.quantum != 0
                            or a.max_delta % p.quantum != 0
                            or (
                                a.kind != AdjustmentKind.NONE
                                and (a.kind != AdjustmentKind.DISCRETE or a.step % p.quantum != 0)
                            )
                        ):
                            raise ValueError(
                                "Discrete scaling must survive substitution/adjustment"
                            )
                if item.scaling.kind == ScalingKind.SUBLINEAR:
                    for (s1, q1), (s2, q2) in zip(points, points[1:]):
                        if not q1 < q2 or q2 * s1 >= q1 * s2:
                            raise ValueError(
                                "SUBLINEAR authored points must grow less than proportionally"
                            )
        return self


class VariantReason(StrEnum):
    DEFAULT = "DEFAULT"
    INVENTORY_MATCH = "INVENTORY_MATCH"
    EXPIRY_RESCUE = "EXPIRY_RESCUE"
    PRICE_ADVANTAGE = "PRICE_ADVANTAGE"
    NUTRITION_FIT = "NUTRITION_FIT"
    PACKAGE_FIT = "PACKAGE_FIT"


class ResolvedRecipeIngredient(RecipeContract):
    requirement_id: UUID
    ingredient_id: UUID
    quantity: CalculatedQuantity
    adjustment_delta: PersistedDecimal


class GroundedRecipeVariantDraft(RecipeContract):
    """Culinary binding input only; nutrition/retail/safety resolution still missing."""

    status: Literal["DRAFT"] = "DRAFT"
    activation_ready: Literal[False] = False
    recipe_version: RecipeVersionSnapshot
    tier_id: UUID
    serving_count: PositiveDecimal
    selected_rule_ids: tuple[UUID, ...]
    resolved_ingredients: tuple[ResolvedRecipeIngredient, ...]
    transformations: tuple[PreparationTransformationFact, ...]
    variant_reason: VariantReason
    derivation_policy_version: Identifier
    provenance: RecipeProvenance
    fingerprint: Sha256

    @model_validator(mode="after")
    def grounded_binding(self):
        deltas = {r.requirement_id: r.adjustment_delta for r in self.resolved_ingredients}
        expected, transforms, servings = resolve_culinary_binding(
            self.recipe_version,
            self.tier_id,
            self.selected_rule_ids,
            deltas,
        )
        unique([r.requirement_id for r in self.resolved_ingredients], "resolved slot")
        if (
            set(self.resolved_ingredients) != set(expected)
            or set(self.transformations) != set(transforms)
            or self.serving_count != servings
        ):
            raise ValueError("Resolved culinary facts disagree with authored primitives")
        unique([t.id for t in self.transformations], "selected transformation")
        if self.fingerprint != self.expected_fingerprint():
            raise ValueError("Culinary fingerprint mismatch")
        return self

    def expected_fingerprint(self):
        import json

        payload = self.model_dump(mode="json", exclude={"fingerprint"})
        # Snapshot tuple order is authored, selected sets are canonicalized.
        payload["selected_rule_ids"] = sorted(payload["selected_rule_ids"])
        payload["resolved_ingredients"] = sorted(
            payload["resolved_ingredients"], key=lambda r: r["requirement_id"]
        )
        payload["transformations"] = sorted(payload["transformations"], key=lambda r: r["id"])
        return sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def resolve_culinary_binding(snapshot, tier_id, selected_rule_ids, deltas):
    tier_id = TypeAdapter(UUID).validate_python(tier_id)
    selected_rule_ids = TypeAdapter(tuple[UUID, ...]).validate_python(selected_rule_ids)
    deltas = TypeAdapter(dict[UUID, PersistedDecimal]).validate_python(deltas)
    unique(selected_rule_ids, "selected rule")
    tiers = {t.id: t for t in snapshot.portion_tiers}
    rules = {r.id: r for r in snapshot.variant_rules}
    if tier_id not in tiers or any(r not in rules for r in selected_rule_ids):
        raise ValueError("Tier/substitution was not authored for this recipe version")
    selected = [rules[r] for r in selected_rule_ids]
    unique([r.requirement_id for r in selected], "selected substitution slot")
    if sum(r.structural for r in selected) > 1 and not any(
        set(c.rule_ids) == set(selected_rule_ids) for c in snapshot.approved_combinations
    ):
        raise ValueError("Multiple structural substitutions require exact authored combination")
    if set(deltas) != {i.id for i in snapshot.ingredients}:
        raise ValueError("Explicit adjustment delta required for every slot")
    replacements = {r.requirement_id: r for r in selected}
    amounts = {q.requirement_id: q.amount for q in tiers[tier_id].quantities}
    resolved, transforms = [], []
    with localcontext() as ctx:
        ctx.prec = 160
        ctx.traps[Inexact] = ctx.traps[Rounded] = True
        for item in snapshot.ingredients:
            delta = deltas[item.id]
            policy = item.adjustment
            if not policy.min_delta <= delta <= policy.max_delta or (
                policy.kind == AdjustmentKind.DISCRETE and delta % policy.step != 0
            ):
                raise ValueError("Quantity adjustment outside authored envelope")
            rule = replacements.get(item.id)
            ingredient = rule.replacement_ingredient_id if rule else item.ingredient_id
            amount = amounts[item.id] * (rule.quantity_factor if rule else 1) + delta
            resolved.append(
                ResolvedRecipeIngredient(
                    requirement_id=item.id,
                    ingredient_id=ingredient,
                    adjustment_delta=delta,
                    quantity=CalculatedQuantity(
                        amount=amount, basis=item.quantity.basis, item_ref=item.quantity.item_ref
                    ),
                )
            )
            path_transformations = {
                t.ingredient_id: t for t in snapshot.transformations if t.requirement_id == item.id
            }
            matching = path_transformations.get(ingredient)
            # An alternate cooked path cannot impose a transform on the raw base path.
            # A cooked base still requires its replacement's own authored yield evidence.
            if item.ingredient_id in path_transformations and matching is None:
                raise ValueError("Substituted ingredient needs its authored cooking transformation")
            if matching is not None:
                transforms.append(matching)
    return tuple(resolved), tuple(transforms), tiers[tier_id].servings
