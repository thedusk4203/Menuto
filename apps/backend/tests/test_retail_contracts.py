"""ADR-006; INV-007/008/009/017/018: independent primitive evidence boundaries."""

from datetime import timedelta
from decimal import Decimal, localcontext
from pathlib import Path
from uuid import uuid4

import pytest
from app.domain.units import CalculatedQuantity, Money, Quantity, QuantizationPolicy
from app.modules.inventory.contracts import RetailSourcedAPAssetDraft
from app.modules.retail.contracts import (
    IngredientProductMapFact,
    PackageFact,
    PlanningPriceQuoteDraft,
    PriceObservationFact,
    ProcurementSnapshotDraft,
    ProductIngredientConversionFact,
    PurchaseIntent,
    ReferencePriceBookFact,
)
from app.modules.retail.public import derive_price_quote
from app.persistence.models import Base
from pydantic import ValidationError
from retail_fixtures import NOW, chain, provenance


def changed(fact, **fields):
    # model_copy(update=...) intentionally skips validation in Pydantic; validate new data.
    return type(fact).model_validate(fact.model_dump() | fields)


@pytest.mark.parametrize("granularity", ["FIXED_PACK", "CATCH_WEIGHT", "LOOSE_SCALE"])
def test_three_package_behaviors_roundtrip(granularity):
    pack = chain(granularity)["package"]
    assert PackageFact.model_validate_json(pack.model_dump_json()) == pack
    intent = PurchaseIntent(
        package_id=pack.id,
        **({"ap_g": "150"} if granularity == "LOOSE_SCALE" else {"package_count": 2}),
    )
    pack.validate_purchase(intent)


@pytest.mark.parametrize(
    "fields",
    [
        {"fixed_ap_g": None},
        {"expected_ap_g": "500"},
        {"step_ap_g": "25"},
        {"fixed_ap_g": "-1"},
        {"fixed_ap_g": "NaN"},
        {"fixed_ap_g": 500.0},
    ],
)
def test_fixed_pack_invalid(fields):
    with pytest.raises(ValidationError):
        changed(chain()["package"], **fields)


@pytest.mark.parametrize(
    "fields",
    [
        {"low_ap_g": "501"},
        {"high_ap_g": "499"},
        {"low_ap_g": "550", "expected_ap_g": "550"},
        {"high_ap_g": None},
        {"low_ap_g": "-1"},
        {"fixed_ap_g": "500"},
    ],
)
def test_catch_weight_invalid_bounds(fields):
    with pytest.raises(ValidationError):
        changed(chain("CATCH_WEIGHT")["package"], **fields)


@pytest.mark.parametrize("value", [0, -1, 1.5, True, "2"])
def test_pack_count_is_strict_positive_integer(value):
    with pytest.raises(ValidationError):
        PurchaseIntent(package_id=uuid4(), package_count=value)


@pytest.mark.parametrize("granularity", ["FIXED_PACK", "CATCH_WEIGHT"])
def test_pack_weight_is_not_fake_checkout_weight(granularity):
    pack = chain(granularity)["package"]
    with pytest.raises(ValueError):
        pack.validate_purchase(PurchaseIntent(package_id=pack.id, ap_g="500"))


@pytest.mark.parametrize(
    "weight,valid",
    [("100", True), ("125", True), ("150", True), ("99", False), ("126", False), ("0.1", False)],
)
def test_loose_scale_minimum_plus_steps(weight, valid):
    pack = chain("LOOSE_SCALE")["package"]
    intent = PurchaseIntent(package_id=pack.id, ap_g=weight)
    if valid:
        pack.validate_purchase(intent)
    else:
        with pytest.raises(ValueError):
            pack.validate_purchase(intent)


def test_inv018_ap_ep_precision_and_mapping_identity_survive_wire_handoff():
    mapping = chain()["mapping"]
    with localcontext() as context:
        context.prec = 3
        fact = mapping.apply(Quantity(amount="123.456789", basis="AP_G"))
    assert fact.ep_raw.amount == Decimal("108.215184200427")
    assert fact.mapping.id == mapping.id
    assert fact.mapping.retail_product_id == mapping.retail_product_id
    assert fact.mapping.provenance == mapping.provenance
    restored = ProductIngredientConversionFact.model_validate_json(fact.model_dump_json())
    assert restored == fact
    stored = fact.ep_raw.to_stored(QuantizationPolicy(version="test", rounding="FLOOR"))
    assert stored.stored.amount == Decimal("108.215184")
    assert stored.residual == Decimal("0.000000200427")
    with pytest.raises(ValidationError):
        changed(fact, ep_raw=CalculatedQuantity(amount="108.215184", basis="EP_RAW_G"))


@pytest.mark.parametrize(
    "fields",
    [
        {"edible_yield": "0"},
        {"edible_yield": "1.1"},
        {"edible_yield": "NaN"},
        {"source_basis": "EP_RAW_G"},
        {"target_basis": "COOKED_G"},
        {"reviewed_at": None},
        {"reviewed_at": NOW - timedelta(seconds=1)},
    ],
)
def test_mapping_review_basis_and_factor(fields):
    with pytest.raises(ValidationError):
        changed(chain()["mapping"], **fields)


def test_no_generic_or_cooking_yield_persistence_and_mapping_owned_by_retail():
    assert "unit_conversions" not in Base.metadata.tables
    assert "edible_yield" in Base.metadata.tables["ingredient_product_maps"].c
    assert not any("cooking_yield" in table.c for table in Base.metadata.tables.values())
    assert "edible_yield" not in Base.metadata.tables["ingredients"].c
    with pytest.raises(ValueError):
        chain()["mapping"].apply(Quantity(amount="500", basis="EP_RAW_G"))


def test_future_retail_ap_inventory_handoff_cannot_discard_mapping():
    mapping = chain()["mapping"]
    fields = dict(
        fact_id=uuid4(),
        household_id=uuid4(),
        asset_kind="RAW_INGREDIENT",
        inventory_lot_id=uuid4(),
        ingredient_id=mapping.ingredient_id,
        quantity=Quantity(amount="500", basis="AP_G"),
        available_from=NOW,
        usable_until=NOW + timedelta(days=1),
        provenance=provenance(),
        retail_mapping=mapping,
    )
    asset = RetailSourcedAPAssetDraft(**fields)
    assert not asset.validation_ready
    assert asset.retail_mapping.retail_product_id == mapping.retail_product_id
    assert RetailSourcedAPAssetDraft.model_validate_json(asset.model_dump_json()) == asset
    for changes in (
        {"retail_mapping": None},
        {"ingredient_id": uuid4()},
        {"quantity": Quantity(amount="500", basis="EP_RAW_G")},
    ):
        with pytest.raises(ValidationError):
            RetailSourcedAPAssetDraft(**(fields | changes))


@pytest.mark.parametrize("amount", [-1, 1.2, True, "NaN", "Infinity", 2**63])
def test_money_no_negative_float_nonfinite_overflow(amount):
    with pytest.raises(ValidationError):
        Money(amount_minor=amount, currency="VND")


def test_currency_is_explicit_and_not_mixed():
    with pytest.raises(ValueError):
        Money(amount_minor=1, currency="VND").add(Money(amount_minor=1, currency="USD"))
    with pytest.raises(ValidationError):
        Money(amount_minor=1, currency="vnd")


@pytest.mark.parametrize("availability", ["CONFIRMED", "LIKELY", "UNKNOWN", "UNAVAILABLE"])
def test_observation_availability_roundtrip(availability):
    obs = changed(chain()["observation"], availability=availability)
    assert PriceObservationFact.model_validate_json(obs.model_dump_json()) == obs


@pytest.mark.parametrize(
    "fields",
    [
        {"availability": "GUARANTEED"},
        {"priced_ap_g": "NaN"},
        {"priced_ap_g": "Infinity"},
        {"priced_ap_g": "-1"},
        {"priced_ap_g": 0.1},
        {"priced_ap_g": "0.0000001"},
        {"provenance": provenance("REVIEWED_REFERENCE")},
    ],
)
def test_bad_observation(fields):
    with pytest.raises(ValidationError):
        changed(chain()["observation"], **fields)


def test_quote_is_not_raw_observation_and_reference_never_claims_availability():
    f = chain()
    quote = derive_price_quote(**f["quote_inputs"], reference=f["reference"])
    assert quote.evidence_kind == "REFERENCE_BASELINE"
    assert quote.availability == "UNKNOWN"
    assert quote.observation is None and quote.reference.book.provenance == f["book"].provenance
    assert PlanningPriceQuoteDraft.model_validate_json(quote.model_dump_json()) == quote
    with pytest.raises(ValidationError):
        PriceObservationFact.model_validate(quote.model_dump())
    with pytest.raises(ValidationError):
        PlanningPriceQuoteDraft.model_validate(f["observation"].model_dump())
    with pytest.raises(ValidationError):
        ReferencePriceBookFact.model_validate(
            f["book"].model_dump()
            | {
                "provenance": provenance("RETAIL_OBSERVATION"),
            }
        )


def test_calibration_is_category_scoped_and_preserves_both_sources():
    f = chain()
    quote = derive_price_quote(
        **f["quote_inputs"], observation=f["observation"], calibration=f["calibration"]
    )
    assert quote.evidence_kind == "CALIBRATED"
    assert quote.price.amount_minor == 55_000
    assert quote.observation == f["observation"] and quote.calibration == f["calibration"]
    with pytest.raises(ValueError):
        derive_price_quote(
            **f["quote_inputs"],
            observation=f["observation"],
            calibration=changed(f["calibration"], category="another-category"),
        )
    with pytest.raises(ValueError, match="fractional minor"):
        derive_price_quote(
            **f["quote_inputs"],
            observation=f["observation"],
            calibration=changed(f["calibration"], factor="1.000001"),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("amount_minor", 49_999),
        ("currency", "USD"),
    ],
)
def test_quote_rejects_forged_price(field, value):
    quote = chain()["quote"]
    with pytest.raises(ValidationError):
        changed(quote, price=Money(**(quote.price.model_dump() | {field: value})))


@pytest.mark.parametrize("mutation", ["package", "mapping", "time", "origin", "quantity"])
def test_quote_cannot_lose_context_or_derivation(mutation):
    f = chain()
    fields = {
        "package": {"package": changed(f["package"], retail_product_id=uuid4())},
        "mapping": {"mapping": changed(f["mapping"], status="DRAFT", reviewed_at=None)},
        "time": {"as_of": NOW - timedelta(seconds=1)},
        "origin": {"evidence_kind": "REFERENCE_BASELINE"},
        "quantity": {"priced_ap_g": "499"},
    }[mutation]
    with pytest.raises(ValidationError):
        changed(f["quote"], **fields)


def test_procurement_draft_has_real_primary_and_distinct_backups():
    f = chain()
    snapshot = ProcurementSnapshotDraft(
        procurement_class=f["cls"],
        members=(f["member"],),
        options=(f["option"],),
    )
    assert ProcurementSnapshotDraft.model_validate_json(snapshot.model_dump_json()) == snapshot
    assert snapshot.options[0].rank == 0
    for options in [(), (changed(f["option"], rank=1),), (f["option"], f["option"])]:
        with pytest.raises(ValidationError):
            changed(snapshot, options=options)
    with pytest.raises(ValidationError):
        changed(snapshot, members=())
    quote_clone = changed(f["quote"], id=uuid4())
    false_backup = changed(f["option"], id=uuid4(), rank=1, quote=quote_clone)
    with pytest.raises(ValidationError, match="same purchasing path"):
        changed(snapshot, options=(f["option"], false_backup))


def test_retail_wire_contracts_frozen_forbid_extra_and_versioned():
    f = chain()
    for fact in (value for value in f.values() if hasattr(value, "contract_version")):
        with pytest.raises(ValidationError):
            fact.contract_version = "another-version"
        with pytest.raises(ValidationError):
            changed(fact, checkout_guarantee=True)
    assert IngredientProductMapFact.model_fields["provenance"].is_required()


def test_migration_is_frozen_and_retail_cannot_import_recipe_or_inventory():
    root = Path(__file__).resolve().parents[3]
    migration = root / "apps/backend/migrations/versions/0003_retail_procurement_foundation.py"
    assert "app.modules" not in migration.read_text()
    assert "metadata" not in migration.read_text().split("from alembic")[1]
    from tools.check_import_boundaries import check_source

    for destination in ("recipes", "inventory", "planning", "execution"):
        assert check_source(
            f"from app.modules.{destination}.contracts import FutureFact",
            "app.modules.retail.contracts",
        )
    assert (
        check_source(
            "from app.modules.retail.contracts import IngredientProductMapFact",
            "app.modules.validation.contracts",
        )
        == []
    )
