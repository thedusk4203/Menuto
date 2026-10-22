"""Regression cases grounded in ADR-006/V1.3 §12.7, not the former implementation."""

from datetime import timedelta
from uuid import uuid4

import pytest
from app.modules.retail import contracts as c
from app.modules.retail.public import derive_price_quote
from pydantic import ValidationError
from retail_fixtures import NOW, chain, provenance
from test_retail_contracts import changed


def test_reference_60000_per_kg_times_1_1_is_66000_with_no_stock_claim():
    f = chain()
    quote = derive_price_quote(
        **f["quote_inputs"], reference=f["reference"], calibration=f["calibration"]
    )
    assert quote.evidence_kind == "CALIBRATED_REFERENCE"
    assert quote.reference_price_pair.money_for_reference_quantity.amount_minor == 66_000
    assert quote.reference_price_pair.priced_ap_g == 1000
    assert quote.availability == "UNKNOWN" and quote.observation is None
    assert quote.reference.book.provenance == f["book"].provenance
    assert quote.calibration.provenance == f["calibration"].provenance
    assert c.PlanningPriceQuoteDraft.model_validate_json(quote.model_dump_json()) == quote


def test_direct_retail_50000_is_unchanged_and_cannot_be_calibrated():
    f = chain()
    assert f["quote"].reference_price_pair.money_for_reference_quantity.amount_minor == 50_000
    with pytest.raises(ValueError, match="direct observation"):
        derive_price_quote(
            **f["quote_inputs"], observation=f["observation"], calibration=f["calibration"]
        )
    with pytest.raises(ValidationError):
        changed(f["quote"], evidence_kind="CALIBRATED", calibration=f["calibration"])
    with pytest.raises(ValidationError):
        changed(f["quote"], evidence_kind="CALIBRATED_REFERENCE", calibration=f["calibration"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("retailer_id", uuid4()),
        ("store_region_id", uuid4()),
        ("category", "vegetables"),
    ],
)
def test_reference_calibration_context_is_not_global(field, value):
    f = chain()
    with pytest.raises(ValueError):
        derive_price_quote(
            **f["quote_inputs"],
            reference=f["reference"],
            calibration=changed(f["calibration"], **{field: value}),
        )


def test_quote_rate_pair_is_not_the_cost_of_its_500g_package():
    f = chain()
    quote = derive_price_quote(**f["quote_inputs"], reference=f["reference"])
    pair = quote.reference_price_pair
    assert pair.price_basis == "REFERENCE_WEIGHT_RATE"
    assert pair.money_for_reference_quantity.amount_minor == 60_000
    assert pair.priced_ap_g == 1000 and quote.package.fixed_ap_g == 500
    assert "price" not in type(quote).model_fields and "priced_ap_g" not in type(quote).model_fields
    with pytest.raises(AttributeError):
        _ = quote.price
    with pytest.raises(ValidationError):
        changed(quote, price=f["observation"].price)
    with pytest.raises(ValidationError):
        changed(pair, price_basis="PACKAGE_TOTAL")


@pytest.mark.parametrize("promotion", [True, False])
def test_promotion_dependence_is_read_from_observation_not_authored(promotion):
    f = chain()
    quote = derive_price_quote(
        **f["quote_inputs"],
        observation=changed(
            f["observation"],
            is_promotion=promotion,
        ),
    )
    option = changed(f["option"], quote=quote)
    assert option.depends_on_promotion is promotion
    with pytest.raises(ValidationError):
        changed(option, depends_on_promotion=not promotion)
    with pytest.raises(ValidationError):
        changed(option, depends_on_single_source=False)
    fallback = derive_price_quote(
        **f["quote_inputs"], reference=f["reference"], calibration=f["calibration"]
    )
    assert not changed(option, quote=fallback).depends_on_promotion


def snapshot(f, options):
    return c.ProcurementSnapshotDraft(
        procurement_class=f["cls"], members=(f["member"],), options=tuple(options)
    )


def test_one_retailer_two_stores_and_providers_still_has_retailer_dependency():
    f = chain()
    other_store = uuid4()
    obs = changed(
        f["observation"],
        id=uuid4(),
        store_region_id=other_store,
        provenance=provenance("RETAIL_OBSERVATION", source_system="provider-b"),
    )
    q = derive_price_quote(
        **(f["quote_inputs"] | {"store_region_id": other_store}), observation=obs
    )
    coverage = snapshot(
        f, [f["option"], changed(f["option"], id=uuid4(), rank=1, quote=q)]
    ).source_coverage
    assert coverage.observed_path_count == 2
    assert coverage.observed_retailer_count == 1
    assert coverage.observation_provider_count == 2
    assert coverage.depends_on_single_source


def test_single_source_coverage_is_snapshot_derived_and_fallback_cannot_inflate_it():
    f = chain()
    coverage = snapshot(f, [f["option"]]).source_coverage
    assert coverage.depends_on_single_source
    fallback = derive_price_quote(**f["quote_inputs"], reference=f["reference"])
    coverage = snapshot(f, [changed(f["option"], quote=fallback)]).source_coverage
    assert coverage.candidate_path_count == 1 and coverage.observed_path_count == 0
    assert coverage.depends_on_single_source
    unavailable = changed(f["observation"], availability="UNAVAILABLE")
    quote = derive_price_quote(**f["quote_inputs"], observation=unavailable)
    coverage = snapshot(f, [changed(f["option"], quote=quote)]).source_coverage
    assert coverage.candidate_path_count == 0
    assert coverage.observed_retailer_count == 0
    with pytest.raises(ValidationError):
        changed(snapshot(f, [f["option"]]), source_coverage=coverage)


def test_brittleness_needs_explicit_versioned_assessment_and_retailer_has_no_status():
    f = chain()
    fields = f["option"].model_dump()
    fields.pop("brittleness_policy_version")
    with pytest.raises(ValidationError):
        c.PlanningProcurementOptionDraft(**fields)
    with pytest.raises(ValidationError):
        changed(f["retailer"], status="INACTIVE")
    assert (
        changed(
            f["retailer_status"], status="INACTIVE", effective_at=NOW + timedelta(days=1)
        ).retailer_id
        == f["retailer"].id
    )
