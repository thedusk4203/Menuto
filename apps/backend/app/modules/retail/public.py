"""Draft evidence derivation only. No optimization, checkout or activation service."""

from uuid import UUID, uuid4

from app.domain.contracts import AwareTime, Identifier
from app.modules.retail.contracts import (
    IngredientProductMapFact,
    PackageFact,
    PlanningPriceQuoteDraft,
    PriceObservationFact,
    ReferencePriceEntryFact,
    ReferencePricePair,
    RetailPriceCalibrationFact,
    calibrated_money,
)
from app.modules.retail.grounding import capture_procurement_sources as capture_procurement_sources
from app.modules.retail.grounding import resolve_procurement_sources as resolve_procurement_sources


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

    Category calibration applies only to reference baselines. A
    production multi-source freshness/outlier eligibility policy remains unimplemented.
    """
    if (observation is None) == (reference is None) or (observation and calibration):
        raise ValueError("Choose direct observation OR reference (optionally calibrated)")
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
            "CALIBRATED_REFERENCE"
            if calibration
            else ("RETAIL_OBSERVED" if observation else "REFERENCE_BASELINE")
        ),
        reference_price_pair=ReferencePricePair(
            money_for_reference_quantity=price,
            priced_ap_g=source.priced_ap_g,
        ),
        observation=observation,
        calibration=calibration,
        reference=reference,
    )


def read_inventory_mapping(session, mapping_id: UUID) -> IngredientProductMapFact:
    """Read-only physical-origin seam; confirms neither purchase nor physical stock."""
    from app.modules.retail.repository import RetailEvidenceRepository

    return RetailEvidenceRepository(session).get(IngredientProductMapFact, mapping_id)
