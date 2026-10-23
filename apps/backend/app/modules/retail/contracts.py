"""INV-007/008/009/018: immutable retail facts and explicitly draft planning evidence.

Mass purchases only in M1.1. No count/ml-to-mass inference and no cooking transformation.
"""

from decimal import Decimal, Inexact, Rounded, localcontext
from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.contracts import (
    AwareTime,
    CalculationDecimal,
    Contract,
    Identifier,
    Label,
    NonNegativeDecimal,
    PositiveDecimal,
)
from app.domain.units import CalculatedQuantity, Money, Provenance, Quantity, YieldConversion


class RetailContract(Contract):
    contract_version: Literal["retail-v2"] = "retail-v2"


class Granularity(StrEnum):
    FIXED_PACK = "FIXED_PACK"
    CATCH_WEIGHT = "CATCH_WEIGHT"
    LOOSE_SCALE = "LOOSE_SCALE"


class Availability(StrEnum):
    CONFIRMED = "CONFIRMED"
    LIKELY = "LIKELY"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"


class EvidenceQuality(StrEnum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RetailerFact(RetailContract):
    id: UUID
    name: Label
    country: Annotated[str, Field(pattern=r"^[A-Z]{2}$")]
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]


class RetailerStatusProvenance(Provenance):
    """LEGACY_STATE identifies migrated state; it does not invent a reviewed source."""

    kind: Literal["USER", "REVIEWED_REFERENCE", "RETAIL_OBSERVATION", "RECEIPT", "LEGACY_STATE"]


class RetailerStatusFact(RetailContract):
    id: UUID
    retailer_id: UUID
    status: Literal["ACTIVE", "INACTIVE"]
    effective_at: AwareTime
    provenance: RetailerStatusProvenance


class StoreRegionFact(RetailContract):
    id: UUID
    retailer_id: UUID
    region_code: Identifier
    scope_kind: Literal["STORE", "REGION"]
    scope_code: Identifier


class RetailProductFact(RetailContract):
    id: UUID
    retailer_id: UUID
    sku: Identifier
    version: Identifier
    name: Label
    brand: Label | None = None
    category: Identifier
    canonical_ingredient_id: UUID
    provenance: Provenance


class PackageFact(RetailContract):
    id: UUID
    retail_product_id: UUID
    version: Identifier
    granularity: Granularity
    basis: Literal["AP_G"] = "AP_G"
    fixed_ap_g: PositiveDecimal | None = None
    expected_ap_g: PositiveDecimal | None = None
    low_ap_g: PositiveDecimal | None = None
    high_ap_g: PositiveDecimal | None = None
    minimum_ap_g: PositiveDecimal | None = None
    step_ap_g: PositiveDecimal | None = None
    provenance: Provenance

    @model_validator(mode="after")
    def distinct_purchase_behaviors(self):
        values = (
            self.fixed_ap_g,
            self.expected_ap_g,
            self.low_ap_g,
            self.high_ap_g,
            self.minimum_ap_g,
            self.step_ap_g,
        )
        populated = tuple(v is not None for v in values)
        required = {
            Granularity.FIXED_PACK: (True, False, False, False, False, False),
            Granularity.CATCH_WEIGHT: (False, True, True, True, False, False),
            Granularity.LOOSE_SCALE: (False, False, False, False, True, True),
        }
        if populated != required[self.granularity]:
            raise ValueError("Package fields must match the purchase granularity")
        if self.granularity == Granularity.CATCH_WEIGHT and not (
            self.low_ap_g <= self.expected_ap_g <= self.high_ap_g and self.low_ap_g < self.high_ap_g
        ):
            raise ValueError("Catch weight requires low <= expected <= high and low < high")
        return self

    def validate_purchase(self, purchase: "PurchaseIntent") -> None:
        if purchase.package_id != self.id:
            raise ValueError("Purchase must reference this package version")
        if self.granularity == Granularity.LOOSE_SCALE:
            if purchase.package_count is not None or purchase.ap_g is None:
                raise ValueError("Loose scale requires weight, not a package count")
            with localcontext() as context:
                context.prec = 160
                context.traps[Inexact] = context.traps[Rounded] = True
                if (
                    purchase.ap_g < self.minimum_ap_g
                    or (purchase.ap_g - self.minimum_ap_g) % self.step_ap_g != 0
                ):
                    raise ValueError("Loose quantity must be minimum + an integer number of steps")
        elif purchase.package_count is None or purchase.ap_g is not None:
            raise ValueError("Fixed/catch packages require a discrete package count")


class PurchaseIntent(RetailContract):
    """A request, never an actual catch-weight checkout quantity."""

    package_id: UUID
    package_count: Annotated[int, Field(strict=True, gt=0, le=2_147_483_647)] | None = None
    ap_g: PositiveDecimal | None = None

    @model_validator(mode="after")
    def exactly_one_quantity(self):
        if (self.package_count is None) == (self.ap_g is None):
            raise ValueError("Specify either package_count or ap_g")
        return self


class IngredientProductMapFact(RetailContract):
    id: UUID
    retail_product_id: UUID
    ingredient_id: UUID
    version: Identifier
    source_basis: Literal["AP_G"] = "AP_G"
    target_basis: Literal["EP_RAW_G"] = "EP_RAW_G"
    edible_yield: Annotated[PositiveDecimal, Field(le=1)]
    status: Literal["DRAFT", "REVIEWED", "REJECTED"]
    confidence: EvidenceQuality
    reviewed_at: AwareTime | None = None
    provenance: Provenance

    @model_validator(mode="after")
    def review_evidence(self):
        if (self.status == "DRAFT") != (self.reviewed_at is None):
            raise ValueError("Reviewed/rejected mappings need a review time; drafts have none")
        if self.reviewed_at is not None and self.reviewed_at < self.provenance.observed_at:
            raise ValueError("Review cannot precede mapping evidence")
        return self

    def apply(self, ap: Quantity | CalculatedQuantity) -> "ProductIngredientConversionFact":
        if self.status != "REVIEWED":
            raise ValueError("AP to EP requires a reviewed mapping version")
        result = YieldConversion(
            kind="EDIBLE_YIELD",
            context_ref=str(self.id),
            factor=self.edible_yield,
            provenance=self.provenance,
        ).apply(ap)
        return ProductIngredientConversionFact(mapping=self, ap=ap, ep_raw=result)


class ProductIngredientConversionFact(RetailContract):
    """Future AP inventory handoff MUST retain this mapping, not only ingredient_id.

    Not an InventoryLot or validator-ready asset. No persistence/physical ledger here.
    """

    mapping: IngredientProductMapFact
    ap: Quantity | CalculatedQuantity
    ep_raw: CalculatedQuantity

    @model_validator(mode="after")
    def independently_checkable_chain(self):
        if self.mapping.status != "REVIEWED":
            raise ValueError("Conversion evidence requires a reviewed mapping")
        expected = YieldConversion(
            kind="EDIBLE_YIELD",
            context_ref=str(self.mapping.id),
            factor=self.mapping.edible_yield,
            provenance=self.mapping.provenance,
        ).apply(self.ap)
        if self.ep_raw != expected:
            raise ValueError("Conversion result disagrees with primitive mapping facts")
        return self


class PriceObservationFact(RetailContract):
    """RetailOffer is a time-bound observation, including CONFIRMED availability."""

    id: UUID
    retailer_id: UUID
    store_region_id: UUID
    retail_product_id: UUID
    package_id: UUID
    price: Money
    priced_ap_g: PositiveDecimal
    availability: Availability
    is_promotion: bool
    source_quality: EvidenceQuality
    provenance: Provenance

    @model_validator(mode="after")
    def retail_source(self):
        if self.provenance.kind != "RETAIL_OBSERVATION":
            raise ValueError("A raw retail observation requires retail observation provenance")
        return self


class ReferencePriceBookFact(RetailContract):
    id: UUID
    code: Identifier
    version: Identifier
    region_code: Identifier
    provenance: Provenance

    @model_validator(mode="after")
    def reference_source(self):
        if self.provenance.kind != "REVIEWED_REFERENCE":
            raise ValueError("Reference book must be explicit reference evidence")
        return self


class ReferencePriceEntryFact(RetailContract):
    id: UUID
    book: ReferencePriceBookFact
    ingredient_id: UUID
    price: Money
    priced_ap_g: PositiveDecimal
    basis: Literal["AP_G"] = "AP_G"
    confidence: EvidenceQuality


class RetailPriceCalibrationFact(RetailContract):
    """Adjusts reference baselines only; never multiplies retailer observations."""

    id: UUID
    retailer_id: UUID
    store_region_id: UUID
    category: Identifier
    version: Identifier
    factor: PositiveDecimal
    evidence_count: Annotated[int, Field(strict=True, gt=0, le=2_147_483_647)]
    confidence: EvidenceQuality
    method_version: Identifier
    provenance: Provenance


class ProcurementClassFact(RetailContract):
    id: UUID
    code: Identifier
    version: Identifier
    ingredient_id: UUID
    granularity: Granularity
    status: Literal["DRAFT"] = "DRAFT"
    provenance: Provenance


class ProcurementClassMemberFact(RetailContract):
    procurement_class_id: UUID
    mapping: IngredientProductMapFact
    equivalence: Literal["EXACT_PRODUCT", "REVIEWED_EQUIVALENT"]
    rationale: Label
    provenance: Provenance


class ReferencePricePair(RetailContract):
    """Money for a reference AP quantity, NEVER a package/purchase cost.

    Future planners need a separate ProcurementCostEvaluator and explicit money
    quantization policy. In particular 60,000/1000g is not the cost of a 500g pack.
    """

    price_basis: Literal["REFERENCE_WEIGHT_RATE"] = "REFERENCE_WEIGHT_RATE"
    basis: Literal["AP_G"] = "AP_G"
    money_for_reference_quantity: Money
    priced_ap_g: PositiveDecimal


class PlanningPriceQuoteDraft(RetailContract):
    id: UUID
    status: Literal["DRAFT"] = "DRAFT"
    procurement_class_id: UUID
    mapping: IngredientProductMapFact
    package: PackageFact
    retailer_id: UUID
    store_region_id: UUID
    region_code: Identifier
    product_category: Identifier
    evidence_kind: Literal["RETAIL_OBSERVED", "CALIBRATED_REFERENCE", "REFERENCE_BASELINE"]
    reference_price_pair: ReferencePricePair
    as_of: AwareTime
    policy_version: Identifier
    observation: PriceObservationFact | None = None
    calibration: RetailPriceCalibrationFact | None = None
    reference: ReferencePriceEntryFact | None = None

    @model_validator(mode="after")
    def derivation_chain(self):
        if self.mapping.status != "REVIEWED":
            raise ValueError("Planning evidence requires a reviewed mapping")
        if self.package.retail_product_id != self.mapping.retail_product_id:
            raise ValueError("Package and mapping must belong to the same product")
        expected_shape = {
            "RETAIL_OBSERVED": (True, False, False),
            "CALIBRATED_REFERENCE": (False, True, True),
            "REFERENCE_BASELINE": (False, False, True),
        }
        if (
            tuple(
                x is not None
                for x in (
                    self.observation,
                    self.calibration,
                    self.reference,
                )
            )
            != expected_shape[self.evidence_kind]
        ):
            raise ValueError("Quote origin must be explicit and exclusive")
        if self.as_of < self.mapping.reviewed_at or (
            self.as_of < self.package.provenance.observed_at
        ):
            raise ValueError("Quote cannot predate its mapping/package evidence")
        if self.observation:
            obs = self.observation
            if (obs.retailer_id, obs.store_region_id, obs.retail_product_id, obs.package_id) != (
                self.retailer_id,
                self.store_region_id,
                self.mapping.retail_product_id,
                self.package.id,
            ):
                raise ValueError("Observation context mismatch")
            if self.as_of < obs.provenance.observed_at:
                raise ValueError("Quote cannot predate observation")
            base_price, base_qty = obs.price, obs.priced_ap_g
            if self.package.granularity == Granularity.FIXED_PACK:
                if base_qty != self.package.fixed_ap_g:
                    raise ValueError("Fixed-pack observed price must price one fixed package")
        else:
            ref = self.reference
            if (ref.ingredient_id, ref.book.region_code) != (
                self.mapping.ingredient_id,
                self.region_code,
            ):
                raise ValueError("Reference ingredient/region mismatch")
            if self.as_of < ref.book.provenance.observed_at:
                raise ValueError("Quote cannot predate reference")
            base_price, base_qty = ref.price, ref.priced_ap_g
        if self.calibration:
            cal = self.calibration
            if (cal.retailer_id, cal.store_region_id, cal.category) != (
                self.retailer_id,
                self.store_region_id,
                self.product_category,
            ) or self.as_of < cal.provenance.observed_at:
                raise ValueError("Calibration context/time mismatch")
            base_price = calibrated_money(base_price, cal.factor)
        if (
            self.reference_price_pair.money_for_reference_quantity != base_price
            or self.reference_price_pair.priced_ap_g != base_qty
        ):
            raise ValueError("Quote must preserve/recompute its source price and quantity")
        return self

    @property
    def availability(self) -> Availability:
        return self.observation.availability if self.observation else Availability.UNKNOWN


def calibrated_money(price: Money, factor: Decimal) -> Money:
    """No minor-unit rounding policy is invented in this slice."""
    with localcontext() as context:
        context.prec = 160
        context.traps[Inexact] = context.traps[Rounded] = True
        result = price.amount_minor * factor
        if result != result.to_integral_value():
            raise ValueError("Calibration produces fractional minor units; policy not implemented")
    return Money(amount_minor=int(result), currency=price.currency)


class PlanningProcurementOptionDraft(RetailContract):
    id: UUID
    rank: Annotated[int, Field(strict=True, ge=0, le=2_147_483_647)]
    quote: PlanningPriceQuoteDraft
    package_size_brittleness: EvidenceQuality
    brittleness_policy_version: Identifier
    substitution_group: Identifier
    rationale: Label
    provenance: Provenance

    @property
    def depends_on_promotion(self) -> bool:
        observation = self.quote.observation
        return observation is not None and observation.is_promotion


class SourceCoverageDraft(RetailContract):
    """Structural counts of non-UNAVAILABLE direct evidence, not probabilities.

    Multiple references/target stores do not manufacture independent retail evidence.
    Single-source remains true if retailer OR provider OR purchasing-path coverage <2.
    """

    candidate_path_count: Annotated[int, Field(strict=True, ge=0)]
    observed_path_count: Annotated[int, Field(strict=True, ge=0)]
    observed_retailer_count: Annotated[int, Field(strict=True, ge=0)]
    observation_provider_count: Annotated[int, Field(strict=True, ge=0)]

    @property
    def depends_on_single_source(self) -> bool:
        return (
            min(
                self.observed_path_count,
                self.observed_retailer_count,
                self.observation_provider_count,
            )
            < 2
        )


class ProcurementSnapshotDraft(RetailContract):
    """No scoring/activation claims. rank 0 is primary; positive ranks are backups."""

    status: Literal["DRAFT"] = "DRAFT"
    procurement_class: ProcurementClassFact
    members: tuple[ProcurementClassMemberFact, ...]
    options: tuple[PlanningProcurementOptionDraft, ...]

    @model_validator(mode="after")
    def coherent_options(self) -> Self:
        cls = self.procurement_class
        ids = [member.mapping.id for member in self.members]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("Accepted mappings must be nonempty and unique")
        for member in self.members:
            if member.procurement_class_id != cls.id or (
                member.mapping.ingredient_id != cls.ingredient_id
                or member.mapping.status != "REVIEWED"
            ):
                raise ValueError("Class membership requires a reviewed map of its ingredient")
        ranks = [option.rank for option in self.options]
        if ranks.count(0) != 1 or len(ranks) != len(set(ranks)):
            raise ValueError("Exactly one primary and distinct backup ranks required")
        quote_ids = [option.quote.id for option in self.options]
        if len(quote_ids) != len(set(quote_ids)):
            raise ValueError("Duplicate quote cannot provide backup coverage")
        purchase_paths = [
            (
                option.quote.mapping.retail_product_id,
                option.quote.package.id,
                option.quote.store_region_id,
            )
            for option in self.options
        ]
        if len(purchase_paths) != len(set(purchase_paths)):
            raise ValueError("Requoting the same purchasing path does not create a backup")
        for option in self.options:
            quote = option.quote
            if (
                quote.procurement_class_id != cls.id
                or quote.mapping.id not in ids
                or (quote.package.granularity != cls.granularity)
            ):
                raise ValueError("Option must belong to class, accepted mapping and granularity")
            member = next(m for m in self.members if m.mapping.id == quote.mapping.id)
            if member.mapping != quote.mapping:
                raise ValueError("Mapping facts cannot conflict under the same identity")
        currencies = {
            option.quote.reference_price_pair.money_for_reference_quantity.currency
            for option in self.options
        }
        if len(currencies) != 1:
            raise ValueError("Procurement options require a common currency")
        return self

    @property
    def source_coverage(self) -> SourceCoverageDraft:
        candidates = [o.quote for o in self.options if o.quote.availability != "UNAVAILABLE"]
        observed = [q for q in candidates if q.observation is not None]
        return SourceCoverageDraft(
            candidate_path_count=len(candidates),
            observed_path_count=len(observed),
            observed_retailer_count=len({q.retailer_id for q in observed}),
            observation_provider_count=len(
                {q.observation.provenance.source_system for q in observed}
            ),
        )


class PriceEvidenceAssessmentDraft(RetailContract):
    """Optional policy input, not a computed risk score or probability."""

    sample_count: Annotated[int, Field(strict=True, ge=0)]
    dispersion_minor: NonNegativeDecimal | None
    coverage: EvidenceQuality
    policy_version: Identifier


_SupplyPositive = Annotated[CalculationDecimal, Field(gt=0)]


class ProcurementSupplyPath(Contract):
    """Unallocated supply coefficients, not checkout quantity/cost or stock."""

    contract_version: Literal["procurement-supply-path.v1"] = "procurement-supply-path.v1"
    interpretation: Literal["CONDITIONAL_EVIDENCE"] = "CONDITIONAL_EVIDENCE"
    freshness_assessment: Literal["NOT_IMPLEMENTED"] = "NOT_IMPLEMENTED"
    procurement_class_id: UUID
    option: PlanningProcurementOptionDraft
    retailer_status: RetailerStatusFact
    supplied_basis: Literal["EP_RAW_G"] = "EP_RAW_G"
    availability: Availability
    nominal_ep_g: _SupplyPositive | None = None
    low_ep_g: _SupplyPositive | None = None
    high_ep_g: _SupplyPositive | None = None
    minimum_ep_g: _SupplyPositive | None = None
    step_ep_g: _SupplyPositive | None = None
    priced_ep_raw: CalculatedQuantity

    @model_validator(mode="after")
    def coefficients(self):
        q, p = self.option.quote, self.option.quote.package
        if (
            q.procurement_class_id != self.procurement_class_id
            or self.retailer_status.retailer_id != q.retailer_id
            or self.retailer_status.status != "ACTIVE"
            or self.availability != q.availability
            or self.availability == "UNAVAILABLE"
        ):
            raise ValueError("Supply path must retain eligible evidence context")
        source = dict(
            nominal_ep_g=p.fixed_ap_g if p.granularity == "FIXED_PACK" else p.expected_ap_g,
            low_ep_g=p.low_ap_g,
            high_ep_g=p.high_ap_g,
            minimum_ep_g=p.minimum_ap_g,
            step_ep_g=p.step_ap_g,
        )
        for name, amount in source.items():
            expected = (
                q.mapping.apply(CalculatedQuantity(amount=amount, basis="AP_G")).ep_raw.amount
                if amount is not None
                else None
            )
            if getattr(self, name) != expected:
                raise ValueError("Supply coefficients disagree with package/mapping primitives")
        expected_price = q.mapping.apply(
            CalculatedQuantity(
                amount=q.reference_price_pair.priced_ap_g,
                basis="AP_G",
            )
        ).ep_raw
        if self.priced_ep_raw != expected_price:
            raise ValueError("Priced EP quantity must preserve the AP reference pair conversion")
        return self
