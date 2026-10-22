from datetime import UTC, datetime
from decimal import Decimal, Inexact, Rounded, localcontext

import pytest
from app.domain.units import (
    CalculatedQuantity,
    Provenance,
    Quantity,
    QuantizationPolicy,
    YieldConversion,
)
from pydantic import ValidationError


def test_valid_yield_chain_keeps_full_precision_before_storage():
    evidence = Provenance(
        kind="REVIEWED_REFERENCE",
        source_system="synthetic",
        external_record_id="fixture",
        source_version="1",
        observed_at=datetime(2026, 10, 22, tzinfo=UTC),
    )
    edible = YieldConversion(
        kind="EDIBLE_YIELD", context_ref="product-map-v1", factor="0.876543", provenance=evidence
    )
    cooked = YieldConversion(
        kind="COOKING_YIELD", context_ref="recipe-prep-v1", factor="1.234567", provenance=evidence
    )
    with localcontext() as context:
        context.prec = 3  # Ambient caller precision must not corrupt food arithmetic.
        raw = edible.apply(Quantity(amount="123.456789", basis="AP_G"))
        actual = cooked.apply(raw)
    assert raw.amount == Decimal("108.215184200427")
    assert actual.amount == Decimal("133.598895312768560109")


@pytest.mark.parametrize(
    "direction,stored,residual",
    [
        ("FLOOR", "0", "0.000000333333"),
        ("CEILING", "0.000001", "-0.000000666667"),
        ("HALF_EVEN", "0", "0.000000333333"),
    ],
)
def test_storage_boundary_is_explicit_and_preserves_rounding_residual(direction, stored, residual):
    value = CalculatedQuantity(amount="0.000000333333", basis="EP_RAW_G")
    policy = QuantizationPolicy(version="synthetic-storage-v1", rounding=direction)
    with localcontext() as context:
        context.prec = 3
        context.traps[Inexact] = context.traps[Rounded] = True
        result = value.to_stored(policy)
    assert result.stored.amount == Decimal(stored)
    assert result.residual == Decimal(residual)
    assert result.original_amount == value.amount
    assert result.policy == policy
    assert value.amount == Decimal("0.000000333333")


@pytest.mark.parametrize("value,result", [("0.0000005", "0"), ("0.0000015", "0.000002")])
def test_half_even_ties_are_not_an_implicit_default(value, result):
    receipt = CalculatedQuantity(amount=value, basis="COOKED_G").to_stored(
        QuantizationPolicy(version="synthetic-ties-v1", rounding="HALF_EVEN")
    )
    assert receipt.stored.amount == Decimal(result)
    with pytest.raises(ValidationError):
        QuantizationPolicy(version="missing-direction")


def test_calculation_limits_and_storage_overflow_reject_without_rounding():
    with pytest.raises(ValidationError):
        CalculatedQuantity(amount="0." + "0" * 36 + "1", basis="AP_G")
    value = CalculatedQuantity(amount="999999999999.9999999", basis="EP_RAW_G")
    with pytest.raises(ValidationError):
        value.to_stored(QuantizationPolicy(version="overflow", rounding="CEILING"))
    with localcontext() as context:
        context.prec = 3
        assert Quantity(amount="12345.000001", basis="EP_RAW_G").add(
            Quantity(amount="0.000001", basis="EP_RAW_G")
        ).amount == Decimal("12345.000002")


def test_storage_bind_rejects_calculated_scale_until_policy_applied():
    from app.shared.db import StoredNumeric

    numeric = StoredNumeric()
    with pytest.raises(ValidationError):
        numeric.process_bind_param(Decimal("108.215184200427"), None)
    receipt = CalculatedQuantity(amount="108.215184200427", basis="EP_RAW_G").to_stored(
        QuantizationPolicy(version="explicit-storage", rounding="FLOOR")
    )
    assert numeric.process_bind_param(receipt.stored.amount, None) == Decimal("108.215184")
