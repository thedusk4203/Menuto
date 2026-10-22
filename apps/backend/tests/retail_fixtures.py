"""Synthetic fixtures only; no retailer/price/calibration production claims."""

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.units import Money, Provenance
from app.modules.retail.contracts import (
    IngredientProductMapFact,
    PackageFact,
    PlanningProcurementOptionDraft,
    PriceObservationFact,
    ProcurementClassFact,
    ProcurementClassMemberFact,
    ReferencePriceBookFact,
    ReferencePriceEntryFact,
    RetailerFact,
    RetailPriceCalibrationFact,
    RetailProductFact,
    StoreRegionFact,
)
from app.modules.retail.public import derive_price_quote

NOW = datetime(2026, 10, 22, tzinfo=UTC)


def provenance(kind="REVIEWED_REFERENCE", **overrides):
    return Provenance(
        **dict(
            kind=kind,
            source_system="synthetic",
            external_record_id=str(uuid4()),
            source_version="1",
            observed_at=NOW,
            source_uri="https://example.com/synthetic",
            content_hash="a" * 64,
        )
        | overrides,
    )


def chain(granularity="FIXED_PACK"):
    retailer = RetailerFact(
        id=uuid4(),
        name="Synthetic retailer",
        country="VN",
        currency="VND",
        status="ACTIVE",
    )
    region = StoreRegionFact(
        id=uuid4(),
        retailer_id=retailer.id,
        region_code="VN-SG",
        scope_kind="STORE",
        scope_code="synthetic-branch",
    )
    product = RetailProductFact(
        id=uuid4(),
        retailer_id=retailer.id,
        sku="synthetic-sku",
        version="1",
        name="Synthetic chicken",
        category="poultry",
        provenance=provenance(),
    )
    package = PackageFact(
        id=uuid4(),
        retail_product_id=product.id,
        version="1",
        granularity=granularity,
        provenance=provenance(),
        **{
            "FIXED_PACK": dict(fixed_ap_g="500"),
            "CATCH_WEIGHT": dict(expected_ap_g="500", low_ap_g="450", high_ap_g="550"),
            "LOOSE_SCALE": dict(minimum_ap_g="100", step_ap_g="25"),
        }[granularity],
    )
    mapping = IngredientProductMapFact(
        id=uuid4(),
        retail_product_id=product.id,
        ingredient_id=uuid4(),
        version="1",
        edible_yield="0.876543",
        status="REVIEWED",
        confidence="HIGH",
        reviewed_at=NOW,
        provenance=provenance(),
    )
    observation = PriceObservationFact(
        id=uuid4(),
        retailer_id=retailer.id,
        store_region_id=region.id,
        retail_product_id=product.id,
        package_id=package.id,
        price=Money(amount_minor=50_000, currency="VND"),
        priced_ap_g="500",
        availability="LIKELY",
        is_promotion=False,
        source_quality="MEDIUM",
        provenance=provenance("RETAIL_OBSERVATION"),
    )
    cls = ProcurementClassFact(
        id=uuid4(),
        code="chicken-mass",
        version="1",
        ingredient_id=mapping.ingredient_id,
        granularity=granularity,
        provenance=provenance(),
    )
    member = ProcurementClassMemberFact(
        procurement_class_id=cls.id,
        mapping=mapping,
        equivalence="EXACT_PRODUCT",
        rationale="Synthetic accepted product",
        provenance=provenance(),
    )
    quote_inputs = dict(
        procurement_class_id=cls.id,
        mapping=mapping,
        package=package,
        retailer_id=retailer.id,
        store_region_id=region.id,
        region_code=region.region_code,
        product_category=product.category,
        as_of=NOW,
        policy_version="synthetic-passthrough-1",
    )
    quote = derive_price_quote(**quote_inputs, observation=observation)
    option = PlanningProcurementOptionDraft(
        id=uuid4(),
        rank=0,
        quote=quote,
        package_size_brittleness="UNKNOWN",
        depends_on_single_source=True,
        depends_on_promotion=False,
        substitution_group="chicken",
        rationale="Synthetic primary",
        provenance=provenance(),
    )
    calibration = RetailPriceCalibrationFact(
        id=uuid4(),
        retailer_id=retailer.id,
        store_region_id=region.id,
        category=product.category,
        version="1",
        factor="1.1",
        evidence_count=3,
        confidence="LOW",
        method_version="synthetic-test-only",
        provenance=provenance(),
    )
    book = ReferencePriceBookFact(
        id=uuid4(),
        code="synthetic-book",
        version="1",
        region_code=region.region_code,
        provenance=provenance(),
    )
    reference = ReferencePriceEntryFact(
        id=uuid4(),
        book=book,
        ingredient_id=mapping.ingredient_id,
        price=Money(amount_minor=60_000, currency="VND"),
        priced_ap_g="1000",
        confidence="LOW",
    )
    return dict(
        retailer=retailer,
        region=region,
        product=product,
        package=package,
        mapping=mapping,
        observation=observation,
        cls=cls,
        member=member,
        quote=quote,
        option=option,
        calibration=calibration,
        book=book,
        reference=reference,
        quote_inputs=quote_inputs,
    )
