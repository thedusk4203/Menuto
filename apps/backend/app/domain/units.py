"""INV-018: a gram is insufficient without its material measurement basis."""

from decimal import Decimal, localcontext
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.domain.contracts import (
    AwareTime,
    Contract,
    Identifier,
    NonNegativeDecimal,
    PositiveDecimal,
)


class MeasurementBasis(StrEnum):
    AP_G = "AP_G"
    EP_RAW_G = "EP_RAW_G"
    COOKED_G = "COOKED_G"
    SERVING = "SERVING"
    COUNT = "COUNT"


class EvidenceKind(StrEnum):
    USER = "USER"
    REVIEWED_REFERENCE = "REVIEWED_REFERENCE"
    RETAIL_OBSERVATION = "RETAIL_OBSERVATION"
    RECEIPT = "RECEIPT"


class Provenance(Contract):
    kind: EvidenceKind
    source_ref: Identifier
    source_version: Identifier
    observed_at: AwareTime


class Quantity(Contract):
    amount: NonNegativeDecimal
    basis: MeasurementBasis
    # COUNT is meaningful only for a specific item; SERVING for a recipe/batch definition.
    item_ref: Identifier | None = None

    @model_validator(mode="after")
    def contextual_units(self):
        if self.basis in {MeasurementBasis.COUNT, MeasurementBasis.SERVING}:
            if self.item_ref is None:
                raise ValueError("COUNT and SERVING require an explicit item/serving definition")
        elif self.item_ref is not None:
            raise ValueError("Mass identity belongs to the enclosing ingredient/product fact")
        return self

    def add(self, other: "Quantity") -> "Quantity":
        if (self.basis, self.item_ref) != (other.basis, other.item_ref):
            raise ValueError("Incompatible measurement basis or item definition")
        return Quantity(amount=self.amount + other.amount, basis=self.basis, item_ref=self.item_ref)


class Money(Contract):
    amount_minor: Annotated[int, Field(strict=True, ge=0, le=9_223_372_036_854_775_807)]
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Money arithmetic requires matching currencies")
        return Money(amount_minor=self.amount_minor + other.amount_minor, currency=self.currency)


class YieldConversion(Contract):
    """Yield evidence is contextual. Cooking yield may exceed 1 (e.g. cooked rice)."""

    kind: Literal["EDIBLE_YIELD", "COOKING_YIELD"]
    context_ref: Identifier
    factor: PositiveDecimal
    provenance: Provenance

    @model_validator(mode="after")
    def edible_yield_bound(self):
        if self.kind == "EDIBLE_YIELD" and self.factor > Decimal(1):
            raise ValueError("Edible yield must be in (0, 1]")
        return self

    def apply(self, quantity: Quantity) -> Quantity:
        source, target = (
            (MeasurementBasis.AP_G, MeasurementBasis.EP_RAW_G)
            if self.kind == "EDIBLE_YIELD"
            else (MeasurementBasis.EP_RAW_G, MeasurementBasis.COOKED_G)
        )
        if quantity.basis != source:
            raise ValueError(f"{self.kind} requires {source}")
        # Never round implicitly; a conversion that needs rounding must have a later policy.
        with localcontext() as context:
            context.prec = 60
            amount = quantity.amount * self.factor
        return Quantity(amount=amount, basis=target)
