"""ADR-005: authored culinary truth, independent of procurement and household assets."""

from decimal import Inexact, Rounded, localcontext
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, TypeAdapter, model_validator

from app.domain.contracts import (
    AwareTime,
    Contract,
    Identifier,
    Label,
    PersistedDecimal,
    PositiveDecimal,
    Sha256,
)
from app.domain.feature_identity import identity_hash, unique_sorted
from app.domain.units import CalculatedQuantity, MeasurementBasis, Provenance, Quantity
from app.modules.catalog.contracts import (
    AffinityFeatureTermFact,
    FeatureExpectedRevision,
    FeatureFrontier,
    FeatureReviewSource,
    FeatureRevision,
    FeatureSequence,
    IngredientProteinStreamFact,
)

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


# Additive MTR-019B contracts. Frozen recipe-v1 contracts/encoders above are unchanged.
class CulinaryGenerationTrigger(StrEnum):
    DEFAULT = "DEFAULT"
    AUTHORED_SELECTION = "AUTHORED_SELECTION"
    INGREDIENT_TARGET = "INGREDIENT_TARGET"


class CulinaryRuleSelection(Contract):
    rule_ids: Annotated[tuple[UUID, ...], Field(min_length=1)]


class CulinaryDemand(Contract):
    """Caller hints, never evidence of nutrition, safety, price or physical ownership."""

    serving_counts: tuple[PositiveDecimal, ...] = ()
    ingredient_targets: tuple[UUID, ...] = ()
    rule_selections: tuple[CulinaryRuleSelection, ...] = ()
    excluded_ingredient_ids: tuple[UUID, ...] = ()


class CulinaryGenerationLimits(Contract):
    max_attempts: Annotated[int, Field(strict=True, gt=0)]
    max_candidates: Annotated[int, Field(strict=True, gt=0)]


class VariantGenerationRequest(Contract):
    contract_version: Literal["culinary-generation-request.v1"] = "culinary-generation-request.v1"
    recipe: RecipeVersionSnapshot
    demand: CulinaryDemand
    limits: CulinaryGenerationLimits

    @model_validator(mode="after")
    def reviewed_source(self):
        if self.recipe.review_status != "REVIEWED":
            raise ValueError("Generation requires reviewed authored recipe facts")
        return self


class CulinaryCandidateDraft(Contract):
    """Culinary-only possibility; selecting it still requires independent validation."""

    contract_version: Literal["culinary-candidate.v1"] = "culinary-candidate.v1"
    status: Literal["DRAFT"] = "DRAFT"
    activation_ready: Literal[False] = False
    recipe_version_id: UUID
    recipe_source_hash: Sha256
    tier_id: UUID
    serving_count: PositiveDecimal
    selected_rule_ids: tuple[UUID, ...]
    resolved_ingredients: Annotated[tuple[ResolvedRecipeIngredient, ...], Field(min_length=1)]
    transformations: tuple[PreparationTransformationFact, ...]
    provenance: RecipeProvenance
    triggers: Annotated[tuple[CulinaryGenerationTrigger, ...], Field(min_length=1)]
    fingerprint: Sha256

    def expected_fingerprint(self):
        import json

        data = self.model_dump(mode="json", exclude={"fingerprint", "triggers"})
        data["selected_rule_ids"] = sorted(data["selected_rule_ids"])
        data["resolved_ingredients"] = sorted(
            data["resolved_ingredients"], key=lambda r: r["requirement_id"]
        )
        data["transformations"] = sorted(data["transformations"], key=lambda t: t["id"])
        return sha256(
            json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        ).hexdigest()

    @model_validator(mode="after")
    def shape(self):
        unique(self.selected_rule_ids, "candidate selected rule")
        unique([r.requirement_id for r in self.resolved_ingredients], "candidate requirement")
        unique([t.id for t in self.transformations], "candidate transformation")
        unique(self.triggers, "generation trigger")
        if any(r.adjustment_delta != 0 for r in self.resolved_ingredients):
            raise ValueError("MTR-019B does not perform post-selection quantity refinement")
        if self.provenance.kind == "IMPORTED_DRAFT":
            raise ValueError("Imported drafts are not reviewed generation evidence")
        if self.fingerprint != self.expected_fingerprint():
            raise ValueError("Candidate fingerprint mismatch")
        return self


class CulinaryGenerationRejection(Contract):
    code: Literal[
        "INVALID_DEMAND",
        "UNAUTHORIZED_SELECTION",
        "EXCLUDED_INGREDIENT",
        "UNRESOLVABLE_PATH",
        "LIMIT_EXCEEDED",
    ]
    tier_id: UUID | None = None
    rule_ids: tuple[UUID, ...] = ()
    detail: Label


class VariantGenerationResult(Contract):
    contract_version: Literal["culinary-generation-result.v1"] = "culinary-generation-result.v1"
    status: Literal["COMPLETE", "NO_CANDIDATES", "INVALID_DEMAND", "LIMIT_EXCEEDED"]
    activation_ready: Literal[False] = False
    request_hash: Sha256
    recipe_source_hash: Sha256
    candidates: tuple[CulinaryCandidateDraft, ...]
    rejections: tuple[CulinaryGenerationRejection, ...]
    attempts: Annotated[int, Field(strict=True, ge=0)]

    @model_validator(mode="after")
    def result_shape(self):
        if (self.status == "COMPLETE") != bool(self.candidates):
            raise ValueError("Only complete demand expansion may expose candidates")
        unique([c.fingerprint for c in self.candidates], "candidate identity")
        if any(c.recipe_source_hash != self.recipe_source_hash for c in self.candidates):
            raise ValueError("Cross-source candidate")
        return self


class PreparationOutputEstimate(Contract):
    contract_version: Literal["preparation-output-estimate.v1"] = "preparation-output-estimate.v1"
    transformation: PreparationTransformationFact
    input: CalculatedQuantity
    output: CalculatedQuantity


# Additive MTR-046A contracts. No frozen RecipeVersion/binding semantics changed.


FeatureDimension = Literal["METHOD", "FLAVOR", "MAIN_PROTEIN"]


class FeatureSlotApplicability(Contract):
    requirement_id: UUID
    choice: Literal["BASE", "RULE", "ANY_AUTHORED_CHOICE"]
    selected_rule_id: UUID | None
    preparation: Literal["NONE", "TRANSFORMATION", "ANY_AUTHORED_PATH_CONTEXT"]
    transformation_id: UUID | None
    adjustment: Literal["ZERO_ONLY", "AUTHORED_ENVELOPE"]

    @model_validator(mode="after")
    def shape(self):
        if (self.choice == "RULE") != (self.selected_rule_id is not None) or (
            self.preparation == "TRANSFORMATION"
        ) != (self.transformation_id is not None):
            raise ValueError("Conditional path identity required/forbidden")
        return self


class RecipeMethodContextKey(Contract):
    contract_version: Literal["culinary-feature-applicability.v1"] = (
        "culinary-feature-applicability.v1"
    )
    recipe_version_id: UUID
    dimension: Literal["METHOD"] = "METHOD"
    scope: Literal["RECIPE_COOKING_CONTEXT"] = "RECIPE_COOKING_CONTEXT"

    def canonical_bytes(self):
        return (
            f"menuto.culinary-feature-key.v1\nversion={self.recipe_version_id}\n"
            "dimension=METHOD\nscope=RECIPE_COOKING_CONTEXT\n"
        ).encode()

    def fingerprint(self):
        return sha256(self.canonical_bytes()).hexdigest()


class CulinaryFeaturePathKey(Contract):
    contract_version: Literal["culinary-feature-applicability.v1"] = (
        "culinary-feature-applicability.v1"
    )
    recipe_version_id: UUID
    dimension: Literal["FLAVOR", "MAIN_PROTEIN"]
    scope: Literal["EXACT_PATH", "REVIEWED_SCOPE"]
    tier_ids: Annotated[tuple[UUID, ...], Field(min_length=1)]
    slots: Annotated[tuple[FeatureSlotApplicability, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def shape(self):
        object.__setattr__(self, "tier_ids", unique_sorted(self.tier_ids))
        object.__setattr__(self, "slots", unique_sorted(self.slots, key=lambda s: s.requirement_id))
        exact = len(self.tier_ids) == 1 and all(
            s.choice != "ANY_AUTHORED_CHOICE"
            and s.preparation != "ANY_AUTHORED_PATH_CONTEXT"
            and s.adjustment == "ZERO_ONLY"
            for s in self.slots
        )
        if (self.scope == "EXACT_PATH") != exact:
            raise ValueError("EXACT_PATH iff one exact zero-adjustment path")
        return self

    def canonical_bytes(self):
        result = (
            f"menuto.culinary-feature-key.v1\nversion={self.recipe_version_id}\n"
            f"dimension={self.dimension}\nscope={self.scope}\n"
        )
        result += "tiers=" + ",".join(str(t) for t in self.tier_ids) + "\n"
        result += "".join(
            f"slot={s.requirement_id}|{s.choice}|{s.selected_rule_id or '-'}|"
            f"{s.preparation}|{s.transformation_id or '-'}|{s.adjustment}\n"
            for s in self.slots
        )
        return result.encode()

    def fingerprint(self):
        return sha256(self.canonical_bytes()).hexdigest()


CulinaryFeatureApplicabilityKey = Annotated[
    RecipeMethodContextKey | CulinaryFeaturePathKey, Field(discriminator="dimension")
]


class MainProteinSupport(Contract):
    term_id: UUID
    requirement_id: UUID
    ingredient_id: UUID
    catalog_review_id: UUID


class CulinaryReviewPayload(Contract):
    dimension: FeatureDimension
    command_kind: Literal["REGISTER", "REPLACE", "RETRACT"]
    recipe_version_id: UUID
    applicability_id: UUID | None
    key: CulinaryFeatureApplicabilityKey | None
    expected_revision_no: FeatureExpectedRevision
    predecessor_id: UUID | None
    expected_recipe_frontier: FeatureFrontier
    coverage: Literal["PARTIAL", "COMPLETE"] | None
    covered_term_ids: tuple[UUID, ...]
    positive_term_ids: tuple[UUID, ...]
    supports: tuple[MainProteinSupport, ...]
    provenance: FeatureReviewSource
    correction_reason: Label | None
    idempotency_key: Identifier

    @model_validator(mode="after")
    def shape(self):
        expected_version = {
            "REGISTER": "culinary-feature-register.v1",
            "REPLACE": "culinary-feature-write.v1",
            "RETRACT": "culinary-feature-retract.v1",
        }[self.command_kind]
        if self.contract_version != expected_version:
            raise ValueError("Command kind/version mismatch")
        object.__setattr__(self, "covered_term_ids", unique_sorted(self.covered_term_ids))
        object.__setattr__(self, "positive_term_ids", unique_sorted(self.positive_term_ids))
        object.__setattr__(
            self,
            "supports",
            unique_sorted(self.supports, key=lambda s: (str(s.term_id), str(s.requirement_id))),
        )
        if (self.expected_revision_no == -1) != (self.predecessor_id is None):
            raise ValueError("Predecessor/revision mismatch")
        if self.command_kind == "REGISTER":
            if (
                self.key is None
                or self.applicability_id is not None
                or self.expected_revision_no != -1
                or self.key.dimension != self.dimension
                or self.key.recipe_version_id != self.recipe_version_id
            ):
                raise ValueError("Registration requires exact semantic key and initial revision")
        elif self.key is not None or self.applicability_id is None or self.expected_revision_no < 0:
            raise ValueError("Existing scope requires identity and predecessor, no key mutation")
        if self.expected_revision_no >= 0 and self.correction_reason is None:
            raise ValueError("Correction reason required")
        if self.command_kind == "RETRACT":
            if (
                self.coverage is not None
                or self.covered_term_ids
                or self.positive_term_ids
                or self.supports
            ):
                raise ValueError("Retraction cannot carry children/coverage")
        elif (
            self.coverage is None
            or not self.covered_term_ids
            or not set(self.positive_term_ids) <= set(self.covered_term_ids)
        ):
            raise ValueError("Replacement requires coverage and positive subset")
        if self.dimension != "MAIN_PROTEIN" and self.supports:
            raise ValueError("Support only belongs to MAIN_PROTEIN")
        if self.dimension == "MAIN_PROTEIN" and (
            {s.term_id for s in self.supports} != set(self.positive_term_ids)
        ):
            raise ValueError("Every main-protein assignment requires explicit support")
        return self

    def fingerprint(self, actor_user_id):
        return identity_hash(dict(command=self, actor_user_id=actor_user_id))


class RecipeOnlyFeatureCommand(CulinaryReviewPayload):
    contract_version: Literal[
        "culinary-feature-register.v1", "culinary-feature-write.v1", "culinary-feature-retract.v1"
    ] = "culinary-feature-write.v1"
    dimension: Literal["METHOD", "FLAVOR"]


class MainProteinFeatureCommand(CulinaryReviewPayload):
    contract_version: Literal[
        "culinary-feature-register.v1", "culinary-feature-write.v1", "culinary-feature-retract.v1"
    ] = "culinary-feature-write.v1"
    dimension: Literal["MAIN_PROTEIN"] = "MAIN_PROTEIN"
    expected_catalog_frontier: FeatureFrontier


CulinaryFeatureWriteCommand = Annotated[
    RecipeOnlyFeatureCommand | MainProteinFeatureCommand, Field(discriminator="dimension")
]


class CulinaryFeatureReviewFact(Contract):
    contract_version: Literal["culinary-feature-review.v1"] = "culinary-feature-review.v1"
    id: UUID
    applicability_id: UUID
    recipe_version_id: UUID
    dimension: FeatureDimension
    revision_no: FeatureRevision
    predecessor_revision_no: FeatureRevision | None
    source_sequence: FeatureSequence
    reviewer_user_id: UUID
    recorded_at: AwareTime
    command: CulinaryFeatureWriteCommand
    command_hash: Sha256

    @model_validator(mode="after")
    def lineage(self):
        q = self.command
        if (
            self.recipe_version_id != q.recipe_version_id
            or self.dimension != q.dimension
            or (q.command_kind != "REGISTER" and self.applicability_id != q.applicability_id)
            or self.revision_no != q.expected_revision_no + 1
            or self.predecessor_revision_no != (self.revision_no - 1 if self.revision_no else None)
            or self.command_hash != q.fingerprint(self.reviewer_user_id)
            or q.provenance.observed_at > self.recorded_at
            or self.source_sequence != q.expected_recipe_frontier + 1
        ):
            raise ValueError("Recipe review ownership/lineage/hash/time mismatch")
        return self


class CulinaryFeatureScopeFact(Contract):
    contract_version: Literal["culinary-feature-scope.v1"] = "culinary-feature-scope.v1"
    id: UUID
    key: CulinaryFeatureApplicabilityKey
    reviews: Annotated[tuple[CulinaryFeatureReviewFact, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def history(self):
        unique_sorted(self.reviews, key=lambda r: r.id)
        rows = unique_sorted(self.reviews, key=lambda r: r.revision_no)
        object.__setattr__(self, "reviews", rows)
        for n, r in enumerate(rows):
            if (
                r.revision_no != n
                or r.applicability_id != self.id
                or r.recipe_version_id != self.key.recipe_version_id
                or r.dimension != self.key.dimension
                or r.command.predecessor_id != (rows[n - 1].id if n else None)
                or (
                    n
                    and (
                        r.source_sequence <= rows[n - 1].source_sequence
                        or r.recorded_at < rows[n - 1].recorded_at
                    )
                )
                or (not n and (r.command.command_kind != "REGISTER" or r.command.key != self.key))
                or (
                    r.command.command_kind == "RETRACT"
                    and (not n or rows[n - 1].command.command_kind == "RETRACT")
                )
            ):
                raise ValueError("Incomplete/conflicting Recipe source history")
        return self


class CulinaryFeatureWriteReceipt(Contract):
    contract_version: Literal["culinary-feature-write-receipt.v1"] = (
        "culinary-feature-write-receipt.v1"
    )
    recipe_version_id: UUID
    applicability_id: UUID
    dimension: FeatureDimension
    review_id: UUID
    source_sequence: FeatureSequence
    command_hash: Sha256
    replayed: Annotated[bool, Field(strict=True)]


class RecipeFeatureSources(Contract):
    contract_version: Literal["recipe-feature-sources.v1"] = "recipe-feature-sources.v1"
    recipe_frontier: FeatureFrontier
    scopes: tuple[CulinaryFeatureScopeFact, ...]
    terms: tuple[AffinityFeatureTermFact, ...]

    @model_validator(mode="after")
    def source_sets(self):
        object.__setattr__(self, "scopes", unique_sorted(self.scopes, key=lambda s: s.id))
        object.__setattr__(self, "terms", unique_sorted(self.terms, key=lambda t: t.id))
        unique_sorted(self.scopes, key=lambda s: (s.key.dimension, s.key.fingerprint()))
        if sum(s.key.dimension == "METHOD" for s in self.scopes) > 1:
            raise ValueError("Only one METHOD registry per RecipeVersion")
        return self


class MainProteinFeatureSources(RecipeFeatureSources):
    catalog_frontier: FeatureFrontier
    catalog_streams: tuple[IngredientProteinStreamFact, ...]

    @model_validator(mode="after")
    def catalog_sets(self):
        unique_sorted(self.catalog_streams, key=lambda s: s.id)
        object.__setattr__(
            self,
            "catalog_streams",
            unique_sorted(self.catalog_streams, key=lambda s: s.ingredient_id),
        )
        return self


class FeatureSelectedPath(Contract):
    tier_id: UUID
    selected_rule_ids: tuple[UUID, ...]
    deltas: tuple[tuple[UUID, PersistedDecimal], ...]

    @model_validator(mode="after")
    def sets(self):
        object.__setattr__(self, "selected_rule_ids", unique_sorted(self.selected_rule_ids))
        object.__setattr__(self, "deltas", unique_sorted(self.deltas, key=lambda x: x[0]))
        return self


class CulinaryFeatureEvaluationInput(Contract):
    contract_version: Literal["culinary-feature-evaluation.v1"] = "culinary-feature-evaluation.v1"
    recipe: RecipeVersionSnapshot
    requested_dimensions: Annotated[tuple[FeatureDimension, ...], Field(min_length=1)]
    path: FeatureSelectedPath | None
    sources: MainProteinFeatureSources | RecipeFeatureSources
    captured_at: AwareTime

    @model_validator(mode="after")
    def primitives(self):
        object.__setattr__(self, "requested_dimensions", unique_sorted(self.requested_dimensions))
        validate_feature_input(self)
        return self


class FeatureTermQuery(Contract):
    dimension: FeatureDimension
    term_ids: Annotated[tuple[UUID, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def sets(self):
        object.__setattr__(self, "term_ids", unique_sorted(self.term_ids))
        return self


class FeatureDimensionDiscovery(Contract):
    dimension: FeatureDimension
    state: Literal["ASSIGNED", "REVIEWED_NONE", "UNRESOLVED"]
    reason: (
        Literal[
            "NO_SOURCE", "NO_MATCHING_SCOPE", "RETRACTED", "PARTIAL_COVERAGE", "STALE_ASSOCIATION"
        ]
        | None
    )
    applicability_id: UUID | None
    review_id: UUID | None
    coverage: Literal["PARTIAL", "COMPLETE"] | None
    covered_term_ids: tuple[UUID, ...]
    positive_term_ids: tuple[UUID, ...]


class FeatureTermResolution(Contract):
    dimension: FeatureDimension
    term_id: UUID
    state: Literal["PRESENT", "REVIEWED_ABSENT", "UNRESOLVED"]
    reason: (
        Literal[
            "NO_SOURCE",
            "NO_MATCHING_SCOPE",
            "RETRACTED",
            "PARTIAL_COVERAGE",
            "STALE_ASSOCIATION",
            "OUTSIDE_REVIEWED_UNIVERSE",
            "TERM_NOT_CAPTURED",
        ]
        | None
    )
    review_id: UUID | None


def _options(recipe, slot):
    item = next(i for i in recipe.ingredients if i.id == slot.requirement_id)
    choices = [(None, item.ingredient_id, False, 1)]
    choices += [
        (r.id, r.replacement_ingredient_id, r.structural, r.quantity_factor)
        for r in recipe.variant_rules
        if r.requirement_id == item.id and item.quantity.basis != "COUNT"
    ]
    paths = {t.ingredient_id: t.id for t in recipe.transformations if t.requirement_id == item.id}
    result = []
    for rule, ingredient, structural, factor in choices:
        transform = paths.get(ingredient)
        if slot.choice == "BASE" and rule is not None:
            continue
        if slot.choice == "RULE" and rule != slot.selected_rule_id:
            continue
        if item.ingredient_id in paths and transform is None:
            continue
        if slot.preparation == "NONE" and transform is not None:
            continue
        if slot.preparation == "TRANSFORMATION" and transform != slot.transformation_id:
            continue
        result.append((rule, ingredient, transform, structural, factor))
    return result


def validate_applicability(recipe, key):
    if recipe.id != key.recipe_version_id or recipe.review_status != "REVIEWED":
        raise ValueError("Classification needs exact reviewed RecipeVersion")
    if key.dimension == "METHOD":
        return
    if set(key.tier_ids) - {t.id for t in recipe.portion_tiers}:
        raise ValueError("Foreign/unrecognized tier")
    if {s.requirement_id for s in key.slots} != {i.id for i in recipe.ingredients}:
        raise ValueError("Complete exact requirement set required")
    options = {s.requirement_id: _options(recipe, s) for s in key.slots}
    if not all(options.values()):
        raise ValueError("Impossible authored slot path")
    forced = sum(all(o[3] for o in opts) for opts in options.values())
    if forced > 1 and not any(
        all(
            any(
                (
                    o[0] in combo.rule_ids
                    if o[0]
                    else not any(
                        r.id in combo.rule_ids and r.requirement_id == rid
                        for r in recipe.variant_rules
                    )
                )
                for o in opts
            )
            for rid, opts in options.items()
        )
        for combo in recipe.approved_combinations
    ):
        raise ValueError("Scope has no approved structural path")


def _overlap(recipe, a, b):
    if a.dimension == "METHOD":
        return True
    if not set(a.tier_ids) & set(b.tier_ids):
        return False
    bs = {s.requirement_id: s for s in b.slots}
    return all(
        {(o[0], o[2]) for o in _options(recipe, s)}
        & {(o[0], o[2]) for o in _options(recipe, bs[s.requirement_id])}
        for s in a.slots
    )


def _term_kind(dimension):
    return "PROTEIN" if dimension == "MAIN_PROTEIN" else dimension


def validate_feature_input(subject):
    recipe, sources = subject.recipe, subject.sources
    if recipe.review_status != "REVIEWED":
        raise ValueError("Classification needs exact reviewed RecipeVersion")
    if ("MAIN_PROTEIN" in subject.requested_dimensions) != isinstance(
        sources, MainProteinFeatureSources
    ):
        raise ValueError("Dimension-sensitive Catalog dependency shape mismatch")
    if set(subject.requested_dimensions) != {"METHOD"} and subject.path is None:
        raise ValueError("CULINARY_BINDING_UNAVAILABLE")
    if subject.path is not None:
        resolve_culinary_binding(
            recipe, subject.path.tier_id, subject.path.selected_rule_ids, dict(subject.path.deltas)
        )
    elif set(subject.requested_dimensions) != {"METHOD"}:
        raise ValueError("Path-sensitive source requires exact path")
    scopes = unique_sorted(sources.scopes, key=lambda s: s.id)
    terms = unique_sorted(sources.terms, key=lambda t: t.id)
    term_map = {t.id: t for t in terms}
    required_terms = set()
    sequence = set()
    review_ids = set()
    streams = ()
    if isinstance(sources, MainProteinFeatureSources):
        streams = unique_sorted(sources.catalog_streams, key=lambda s: s.ingredient_id)
        catseq = set()
        cat_ids = set()
        for stream in streams:
            for r in stream.reviews:
                if r.source_sequence > sources.catalog_frontier or r.source_sequence in catseq:
                    raise ValueError("Invalid Catalog frontier/source sequence")
                if r.id in cat_ids:
                    raise ValueError("Duplicate Catalog review identity")
                cat_ids.add(r.id)
                catseq.add(r.source_sequence)
                _review_terms(
                    r.command,
                    r.recorded_at,
                    "PROTEIN",
                    term_map,
                    required_terms,
                    subject.captured_at,
                )
    required_streams = set()
    for scope in scopes:
        validate_applicability(recipe, scope.key)
        if scope.key.dimension not in subject.requested_dimensions:
            raise ValueError("Source dimension not requested")
        for r in scope.reviews:
            if r.source_sequence > sources.recipe_frontier or r.source_sequence in sequence:
                raise ValueError("Invalid Recipes frontier/source sequence")
            if r.id in review_ids:
                raise ValueError("Duplicate Recipe review identity")
            review_ids.add(r.id)
            sequence.add(r.source_sequence)
            _review_terms(
                r.command,
                r.recorded_at,
                _term_kind(r.dimension),
                term_map,
                required_terms,
                subject.captured_at,
            )
            if r.dimension == "MAIN_PROTEIN":
                if r.command.expected_catalog_frontier > sources.catalog_frontier:
                    raise ValueError("Catalog audit exceeds captured frontier")
                _supports(recipe, scope.key, r, streams, required_streams)
    if required_terms != set(term_map):
        raise ValueError("Vocabulary manifest must exactly cover captured review universes")
    if {s.ingredient_id for s in streams} != required_streams:
        raise ValueError("Catalog support stream manifest mismatch")
    for i, scope in enumerate(scopes):
        for other in scopes[:i]:
            if (
                scope.key.dimension == other.key.dimension
                and scope.reviews[-1].command.command_kind != "RETRACT"
                and other.reviews[-1].command.command_kind != "RETRACT"
                and _overlap(recipe, scope.key, other.key)
            ):
                raise ValueError("SOURCE_CONFLICT: overlapping active scopes")


def _review_terms(q, recorded, kind, terms, required, captured):
    if recorded > captured:
        raise ValueError("Future review relative to capture")
    for tid in q.covered_term_ids:
        required.add(tid)
        t = terms.get(tid)
        if (
            t is None
            or t.kind != kind
            or t.status != "REVIEWED"
            or t.provenance.observed_at > recorded
        ):
            raise ValueError("Unreviewed/foreign/missing/future vocabulary")


def _supports(recipe, key, review, streams, required):
    by_ingredient = {s.ingredient_id: s for s in streams}
    slots = {s.requirement_id: s for s in getattr(key, "slots", ())}
    items = {i.id: i for i in recipe.ingredients}
    tiers = {t.id: t for t in recipe.portion_tiers}
    for support in review.command.supports:
        required.add(support.ingredient_id)
        slot = slots.get(support.requirement_id)
        stream = by_ingredient.get(support.ingredient_id)
        if slot is None or slot.choice == "ANY_AUTHORED_CHOICE" or stream is None:
            raise ValueError("Unpinned main-protein slot support")
        candidates = [
            r
            for r in stream.reviews
            if r.source_sequence <= review.command.expected_catalog_frontier
        ]
        # Publication used current pinned head, not any historical positive association.
        if not candidates:
            raise ValueError("Missing Catalog publication frontier")
        source = candidates[-1]
        if (
            source.id != support.catalog_review_id
            or support.term_id not in source.command.positive_term_ids
            or source.recorded_at > review.recorded_at
        ):
            raise ValueError("Invalid Catalog association publication support")
        opts = _options(recipe, slot)
        if not opts or any(o[1] != support.ingredient_id for o in opts):
            raise ValueError("Ingredient path support mismatch")
        with localcontext() as ctx:
            ctx.prec = 160
            for tier_id in key.tier_ids:
                base = next(
                    q.amount
                    for q in tiers[tier_id].quantities
                    if q.requirement_id == slot.requirement_id
                )
                minimum = (
                    0
                    if slot.adjustment == "ZERO_ONLY"
                    else items[slot.requirement_id].adjustment.min_delta
                )
                if any(base * o[4] + minimum <= 0 for o in opts):
                    raise ValueError("Nonpositive main-protein support envelope")


def _matches(key, subject):
    if key.dimension == "METHOD":
        return True
    p = subject.path
    if p.tier_id not in key.tier_ids:
        return False
    rules = {
        r.requirement_id: r.id for r in subject.recipe.variant_rules if r.id in p.selected_rule_ids
    }
    _, transforms, _ = resolve_culinary_binding(
        subject.recipe, p.tier_id, p.selected_rule_ids, dict(p.deltas)
    )
    paths = {t.requirement_id: t.id for t in transforms}
    for slot in key.slots:
        rid = slot.requirement_id
        if slot.choice == "BASE" and rid in rules:
            return False
        if slot.choice == "RULE" and rules.get(rid) != slot.selected_rule_id:
            return False
        if slot.preparation == "NONE" and rid in paths:
            return False
        if slot.preparation == "TRANSFORMATION" and paths.get(rid) != slot.transformation_id:
            return False
        if slot.adjustment == "ZERO_ONLY" and dict(p.deltas)[rid] != 0:
            return False
    return True


def discover_feature_input(subject):
    """Reparse to reject model_construct/model_copy and recompute every classification."""
    subject = CulinaryFeatureEvaluationInput.model_validate(subject.model_dump())
    results = []
    for d in subject.requested_dimensions:
        all_scopes = [s for s in subject.sources.scopes if s.key.dimension == d]
        matching = [s for s in all_scopes if _matches(s.key, subject)]
        active = [s for s in matching if s.reviews[-1].command.command_kind != "RETRACT"]
        if len(active) > 1:
            raise ValueError("SOURCE_CONFLICT")
        scope = active[0] if active else (matching[0] if len(matching) == 1 else None)
        reason = "NO_SOURCE" if not all_scopes else "NO_MATCHING_SCOPE"
        positives, covered, coverage, state = (), (), None, "UNRESOLVED"
        r = scope.reviews[-1] if scope else None
        if r:
            q = r.command
            coverage, covered = q.coverage, q.covered_term_ids
            if q.command_kind == "RETRACT":
                reason = "RETRACTED"
            elif d == "MAIN_PROTEIN" and any(
                next(
                    s for s in subject.sources.catalog_streams if s.ingredient_id == p.ingredient_id
                )
                .reviews[-1]
                .id
                != p.catalog_review_id
                for p in q.supports
            ):
                reason = "STALE_ASSOCIATION"
            else:
                positives = q.positive_term_ids
                state = (
                    "ASSIGNED"
                    if positives
                    else ("REVIEWED_NONE" if coverage == "COMPLETE" else "UNRESOLVED")
                )
                reason = "PARTIAL_COVERAGE" if state == "UNRESOLVED" else None
        results.append(
            FeatureDimensionDiscovery(
                dimension=d,
                state=state,
                reason=reason,
                applicability_id=scope.id if scope else None,
                review_id=r.id if r else None,
                coverage=coverage,
                covered_term_ids=covered,
                positive_term_ids=positives,
            )
        )
    return tuple(results)


def resolve_feature_input(subject, queries):
    subject = CulinaryFeatureEvaluationInput.model_validate(subject.model_dump())
    discoveries = {d.dimension: d for d in discover_feature_input(subject)}
    queries = unique_sorted(
        tuple(FeatureTermQuery.model_validate(q.model_dump()) for q in queries),
        key=lambda q: q.dimension,
    )
    terms = {t.id: t for t in subject.sources.terms}
    result = []
    for q in queries:
        if q.dimension not in discoveries:
            raise ValueError("Query dimension was not captured")
        d = discoveries[q.dimension]
        for tid in q.term_ids:
            state, reason = "UNRESOLVED", d.reason
            if tid not in terms:
                reason = "TERM_NOT_CAPTURED"
            elif terms[tid].kind != _term_kind(q.dimension):
                raise ValueError("TERM_KIND_MISMATCH")
            elif d.reason in {"RETRACTED", "STALE_ASSOCIATION", "NO_SOURCE", "NO_MATCHING_SCOPE"}:
                pass
            elif tid not in d.covered_term_ids:
                reason = "OUTSIDE_REVIEWED_UNIVERSE"
            elif tid in d.positive_term_ids:
                state, reason = "PRESENT", None
            elif d.coverage == "COMPLETE":
                state, reason = "REVIEWED_ABSENT", None
            else:
                reason = "PARTIAL_COVERAGE"
            result.append(
                FeatureTermResolution(
                    dimension=q.dimension,
                    term_id=tid,
                    state=state,
                    reason=reason,
                    review_id=d.review_id,
                )
            )
    return tuple(result)
