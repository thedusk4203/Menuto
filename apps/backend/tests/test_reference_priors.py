"""Approved reference-source interface semantics, independent exact expectations."""

import pytest
from app.modules.preferences.reference_prior_contracts import ReferencePriorAmount
from pydantic import ValidationError


@pytest.mark.parametrize(
    "numerator,denominator",
    [
        (True, 1),
        (1.0, 1),
        ("1", 1),
        (1, 0),
        (1, -1),
        (2, 4),
        (0, 2),
        (2, 1),
        (2147483648, 2147483648),
        (1, "2"),
    ],
)
def test_c02_reject_noncanonical_reference_amount(numerator, denominator):
    with pytest.raises(ValidationError):
        ReferencePriorAmount(numerator=numerator, denominator=denominator)


@pytest.mark.parametrize("numerator,denominator", [(-1, 1), (0, 1), (1, 1), (-2, 3)])
def test_c01_c02_reference_coordinate_is_exact_and_distinct(numerator, denominator):
    amount = ReferencePriorAmount(numerator=numerator, denominator=denominator)
    assert (amount.numerator, amount.denominator) == (numerator, denominator)
    assert amount.unit == "REVIEWED_REFERENCE_ANCHOR_UNITS"


def test_f01_frozen_migration_bytes_and_all_276_definitions():
    import json
    from hashlib import sha256
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    pins = json.loads(
        (Path(__file__).parent / "fixtures/reference_prior_compatibility.json").read_text()
    )
    assert len(pins["definitions"]) == 276
    assert len(pins["migrations"]) == 13
    definitions = json.loads((root / "packages/contracts/domain.schema.json").read_text())["$defs"]
    for name, expected in pins["definitions"].items():
        actual = json.dumps(
            definitions[name], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        assert sha256(actual.encode()).hexdigest() == expected, name
    for name, expected in pins["migrations"].items():
        assert (
            sha256((root / "apps/backend/migrations/versions" / name).read_bytes()).hexdigest()
            == expected
        )


@pytest.mark.parametrize(
    "coordinate",
    [
        {"coordinate_version": True},
        {"coordinate_version": 1.0},
        {"coordinate_version": 2},
        {"applicability": "MEMBER"},
    ],
)
def test_c01_closed_coordinate_rejects_implicit_conversion(coordinate):
    from app.modules.preferences.reference_prior_contracts import ReferencePriorCoordinate

    with pytest.raises(ValidationError):
        ReferencePriorCoordinate(**coordinate)


def test_c01_reference_amount_cannot_substitute_explicit_affinity():
    from app.modules.preferences.contracts import ExplicitAffinityAmount

    reference = ReferencePriorAmount(numerator=1, denominator=2)
    with pytest.raises(ValidationError):
        ExplicitAffinityAmount.model_validate(reference.model_dump())
