"""Primitive nutrition references carry their own measurement basis and evidence."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.contracts import Contract, Identifier, Label, NonNegativeDecimal
from app.domain.units import MeasurementBasis, Provenance, Quantity


class IngredientCreate(Contract):
    name: Label


class IngredientIdentityFact(Contract):
    contract_version: Literal["ingredient-identity.v1"] = "ingredient-identity.v1"
    id: UUID
    name: Label


class NutritionValues(Contract):
    energy_kcal: NonNegativeDecimal
    protein_g: NonNegativeDecimal
    fat_g: NonNegativeDecimal
    carbohydrate_g: NonNegativeDecimal


class NutritionFact(Contract):
    ingredient_id: UUID
    reference: Quantity
    nutrients: NutritionValues
    provenance: Provenance
    status: Literal["DRAFT", "REVIEWED"]

    @model_validator(mode="after")
    def usable_reference(self):
        if self.reference.amount <= 0:
            raise ValueError("Nutrition reference amount must be positive")
        if self.reference.basis not in {MeasurementBasis.EP_RAW_G, MeasurementBasis.COOKED_G}:
            raise ValueError("Nutrition reference must use edible raw or cooked mass")
        return self


class NutritionReferenceFact(Contract):
    contract_version: Literal["nutrition-reference-source.v1"] = "nutrition-reference-source.v1"
    id: UUID
    fact: NutritionFact


class AffinityFeatureTermFact(Contract):
    """Reviewed vocabulary meaning only, never inferred recipe/ingredient classification."""

    contract_version: Literal["affinity-feature-term.v1"] = "affinity-feature-term.v1"
    id: UUID
    kind: Literal["PROTEIN", "METHOD", "FLAVOR"]
    code: Identifier
    version: Annotated[int, Field(strict=True, gt=0, le=2_147_483_647)]
    label: Label
    definition: Annotated[str, Field(min_length=1, max_length=4000, pattern=r"\S")]
    status: Literal["DRAFT", "REVIEWED"]
    provenance: Provenance

    @model_validator(mode="after")
    def authored_source(self):
        if self.provenance.kind not in {"USER", "REVIEWED_REFERENCE"}:
            raise ValueError("Feature vocabulary requires authored/curated source")
        return self
