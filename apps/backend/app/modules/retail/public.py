"""Draft evidence derivation only. No optimization, checkout or activation service."""

from uuid import UUID, uuid4

from app.domain.contracts import AwareTime, Identifier
from app.modules.retail.contracts import (
    IngredientProductMapFact,
    PackageFact,
    PlanningPriceQuoteDraft,
    PriceObservationFact,
    ReferencePriceEntryFact,
    RetailPriceCalibrationFact,
    calibrated_money,
)


def derive_price_quote(
    *,
    procurement_class_id: UUID,
    mapping: IngredientProductMapFact,
    package: PackageFact,
    retailer_id: UUID,
    store_region_id: UUID,
    region_code: Identifier,
    product_category: Identifier,
    as_of: AwareTime,
    policy_version: Identifier,
    observation: PriceObservationFact | None = None,
    calibration: RetailPriceCalibrationFact | None = None,
    reference: ReferencePriceEntryFact | None = None,
) -> PlanningPriceQuoteDraft:
    """Caller explicitly selects evidence/policy; nothing silently falls back.

    M1.1 supports passthrough or an externally supplied category calibration. A
    production multi-source freshness/outlier eligibility policy remains unimplemented.
    """
    if (observation is None) == (reference is None) or (reference and calibration):
        raise ValueError("Choose an observation (optionally calibrated) OR explicit reference")
    source = observation if observation is not None else reference
    price = calibrated_money(source.price, calibration.factor) if calibration else source.price
    return PlanningPriceQuoteDraft(
        id=uuid4(),
        procurement_class_id=procurement_class_id,
        mapping=mapping,
        package=package,
        retailer_id=retailer_id,
        store_region_id=store_region_id,
        region_code=region_code,
        product_category=product_category,
        as_of=as_of,
        policy_version=policy_version,
        evidence_kind=(
            "CALIBRATED"
            if calibration
            else ("RETAIL_OBSERVED" if observation else "REFERENCE_BASELINE")
        ),
        price=price,
        priced_ap_g=source.priced_ap_g,
        observation=observation,
        calibration=calibration,
        reference=reference,
    )
