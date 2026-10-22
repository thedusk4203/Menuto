"""Immutable wire values. No database, solver, policy or framework service dependencies."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


def exact_decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
        raise ValueError("Use a decimal string, integer or Decimal; floats are not exact inputs")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("Invalid decimal") from error
    if not number.is_finite():
        raise ValueError("Decimal must be finite")
    # Canonicalize spelling (1.0 and 1.00) without Decimal.normalize's context rounding.
    sign, digits, exponent = number.as_tuple()
    digits = list(digits)
    while digits and digits[-1] == 0:
        digits.pop()
        exponent += 1
    return Decimal((sign if digits else 0, tuple(digits or [0]), exponent if digits else 0))


ExactDecimal = Annotated[
    Decimal, BeforeValidator(exact_decimal), Field(max_digits=18, decimal_places=6)
]
NonNegativeDecimal = Annotated[ExactDecimal, Field(ge=0)]
PositiveDecimal = Annotated[ExactDecimal, Field(gt=0)]
Identifier = Annotated[str, Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")]
Label = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
Sha256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Version = Annotated[int, Field(strict=True, ge=0)]


def aware_time(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must include a timezone")
    from datetime import UTC

    return value.astimezone(UTC)


AwareTime = Annotated[datetime, AfterValidator(aware_time)]
