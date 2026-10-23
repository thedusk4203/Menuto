"""Primitive nutrition references carry their own measurement basis and evidence."""

from typing import Literal
from uuid import UUID

from pydantic import model_validator

from app.domain.contracts import Contract, Label, NonNegativeDecimal
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
