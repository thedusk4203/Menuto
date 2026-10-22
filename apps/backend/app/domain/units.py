"""INV-018: a gram is insufficient without its material measurement basis."""

from decimal import (
    ROUND_CEILING,
    ROUND_FLOOR,
    ROUND_HALF_EVEN,
    Decimal,
    Inexact,
    Rounded,
    localcontext,
)
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, AnyHttpUrl, Field, UrlConstraints, model_validator

from app.domain.contracts import (
    AwareTime,
    CalculationDecimal,
    Contract,
    Identifier,
    NonNegativeCalculationDecimal,
    NonNegativeDecimal,
    PositiveDecimal,
    Sha256,
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


def external_text(value: str) -> str:
    if not value.strip() or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("External references must be nonblank and contain no control characters")
    return value


ExternalRecordId = Annotated[
    str, Field(min_length=1, max_length=2048), AfterValidator(external_text)
]
ExternalVersion = Annotated[str, Field(min_length=1, max_length=200), AfterValidator(external_text)]
SourceUri = Annotated[AnyHttpUrl, UrlConstraints(max_length=2048)]


class Provenance(Contract):
    kind: EvidenceKind
    source_system: Identifier
    external_record_id: ExternalRecordId
    source_version: ExternalVersion
    source_uri: SourceUri | None = None
    content_hash: Sha256 | None = None
    observed_at: AwareTime

    @model_validator(mode="after")
    def no_credentials_in_locator(self):
        if self.source_uri is not None and (
            self.source_uri.username is not None or self.source_uri.password is not None
        ):
            raise ValueError("Provenance URI cannot contain credentials")
        return self


class QuantityIdentity(Contract):
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


class Quantity(QuantityIdentity):
    """Stored/source quantity, restricted to NUMERIC(18,6); no implicit rounding."""

    amount: NonNegativeDecimal

    def add(self, other: "Quantity") -> "Quantity":
        if (self.basis, self.item_ref) != (other.basis, other.item_ref):
            raise ValueError("Incompatible measurement basis or item definition")
        with localcontext() as context:
            context.prec = 160
            context.traps[Inexact] = context.traps[Rounded] = True
            amount = self.amount + other.amount
        return Quantity(amount=amount, basis=self.basis, item_ref=self.item_ref)


StoredQuantity = Quantity


class QuantizationPolicy(Contract):
    """Caller chooses direction at an explicit storage seam, never a hidden default."""

    version: Identifier
    rounding: Literal["FLOOR", "CEILING", "HALF_EVEN"]
    decimal_places: Literal[6] = 6


class QuantizationResult(Contract):
    original_amount: CalculationDecimal
    stored: Quantity
    # original - stored; signed so upward rounding is auditable too.
    residual: CalculationDecimal
    policy: QuantizationPolicy


class CalculatedQuantity(QuantityIdentity):
    """Bounded exact working value (72 digits/36 decimal places), not a DB row."""

    amount: NonNegativeCalculationDecimal

    def add(self, other: "Quantity | CalculatedQuantity") -> "CalculatedQuantity":
        if (self.basis, self.item_ref) != (other.basis, other.item_ref):
            raise ValueError("Incompatible measurement basis or item definition")
        with localcontext() as context:
            context.prec = 160
            context.traps[Inexact] = context.traps[Rounded] = True
            amount = self.amount + other.amount
        return CalculatedQuantity(amount=amount, basis=self.basis, item_ref=self.item_ref)

    def to_stored(self, policy: QuantizationPolicy) -> QuantizationResult:
        modes = {"FLOOR": ROUND_FLOOR, "CEILING": ROUND_CEILING, "HALF_EVEN": ROUND_HALF_EVEN}
        with localcontext() as context:
            context.prec = 160
            # This is the only intentional rounding operation. Caller ambient traps do not apply.
            context.traps[Inexact] = context.traps[Rounded] = False
            stored_amount = self.amount.quantize(
                Decimal("0.000001"), rounding=modes[policy.rounding]
            )
            residual = self.amount - stored_amount
        return QuantizationResult(
            original_amount=self.amount,
            stored=Quantity(amount=stored_amount, basis=self.basis, item_ref=self.item_ref),
            residual=residual,
            policy=policy,
        )


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

    def apply(self, quantity: Quantity | CalculatedQuantity) -> CalculatedQuantity:
        source, target = (
            (MeasurementBasis.AP_G, MeasurementBasis.EP_RAW_G)
            if self.kind == "EDIBLE_YIELD"
            else (MeasurementBasis.EP_RAW_G, MeasurementBasis.COOKED_G)
        )
        if quantity.basis != source:
            raise ValueError(f"{self.kind} requires {source}")
        # Keep all significant digits across transformations; storage policy is separate.
        with localcontext() as context:
            context.prec = 160
            context.traps[Inexact] = context.traps[Rounded] = True
            amount = quantity.amount * self.factor
        return CalculatedQuantity(amount=amount, basis=target)
