"""Explicit contract/row boundary. Caller owns transaction; no ORM objects escape reads."""

from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.contracts import AwareTime
from app.domain.units import Money, Provenance
from app.modules.retail import contracts as c
from app.modules.retail import models as m

FACT_MODELS = {
    c.RetailerFact: m.Retailer,
    c.RetailerStatusFact: m.RetailerStatusFact,
    c.StoreRegionFact: m.StoreRegion,
    c.RetailProductFact: m.RetailProduct,
    c.PackageFact: m.RetailPackage,
    c.IngredientProductMapFact: m.IngredientProductMap,
    c.PriceObservationFact: m.PriceObservation,
    c.ReferencePriceBookFact: m.ReferencePriceBook,
    c.ReferencePriceEntryFact: m.ReferencePriceEntry,
    c.RetailPriceCalibrationFact: m.RetailPriceCalibration,
    c.ProcurementClassFact: m.ProcurementClass,
    c.ProcurementClassMemberFact: m.ProcurementClassMember,
    c.PlanningPriceQuoteDraft: m.PlanningPriceQuote,
    c.PlanningProcurementOptionDraft: m.PlanningProcurementOption,
}


class RetailEvidenceRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, fact: c.RetailContract) -> None:
        """Referenced facts must already exist. No cascaded fake source creation."""
        references = []
        if isinstance(fact, c.ReferencePriceEntryFact):
            references.append(fact.book)
        if isinstance(fact, c.ProcurementClassMemberFact):
            references.append(fact.mapping)
        if isinstance(fact, c.PlanningPriceQuoteDraft):
            references.extend(
                (fact.mapping, fact.package, fact.observation, fact.calibration, fact.reference)
            )
        if isinstance(fact, c.PlanningProcurementOptionDraft):
            references.append(fact.quote)
        if isinstance(fact, c.IngredientProductMapFact):
            product = self.get(c.RetailProductFact, fact.retail_product_id)
            if product.canonical_ingredient_id != fact.ingredient_id:
                raise ValueError("Product version has exactly one canonical procurement ingredient")
        for reference in references:
            if reference is not None and self.get(type(reference), reference.id) != reference:
                raise ValueError("Nested evidence disagrees with its persisted immutable identity")
        model = FACT_MODELS[type(fact)]
        fields = fact.model_dump(exclude={"contract_version"})
        provenance = fields.pop("provenance", None)
        if provenance is not None:
            fields.update(provenance)
            fields["source_kind"] = fields.pop("kind")
            if fields["source_uri"] is not None:
                fields["source_uri"] = str(fields["source_uri"])
        price = fields.pop("price", None)
        if price is not None:
            fields.update(price)
        if isinstance(fact, c.ReferencePriceEntryFact):
            fields.pop("book")
            fields["book_id"] = fact.book.id
        if isinstance(fact, (c.ProcurementClassMemberFact, c.PlanningPriceQuoteDraft)):
            fields.pop("mapping")
            fields.update(
                mapping_id=fact.mapping.id,
                retail_product_id=fact.mapping.retail_product_id,
                ingredient_id=fact.mapping.ingredient_id,
            )
        if isinstance(fact, c.PlanningPriceQuoteDraft):
            pair = fields.pop("reference_price_pair")
            fields.update(
                reference_amount_minor=pair["money_for_reference_quantity"]["amount_minor"],
                currency=pair["money_for_reference_quantity"]["currency"],
                reference_ap_g=pair["priced_ap_g"],
                price_basis=pair["price_basis"],
            )
            for key in ("package", "observation", "calibration", "reference"):
                fields.pop(key)
            fields.update(
                package_id=fact.package.id,
                granularity=fact.package.granularity,
                observation_id=fact.observation.id if fact.observation else None,
                calibration_id=fact.calibration.id if fact.calibration else None,
                reference_entry_id=fact.reference.id if fact.reference else None,
            )
        if isinstance(fact, c.PlanningProcurementOptionDraft):
            fields.pop("quote")
            fields.update(
                quote_id=fact.quote.id,
                procurement_class_id=fact.quote.procurement_class_id,
            )
        self.session.add(model(**fields))
        self.session.flush()

    def get(self, contract_type: type[c.RetailContract], identity: UUID):
        model = FACT_MODELS[contract_type]
        row = self.session.get(model, identity)
        if row is None:
            raise LookupError(f"Missing {contract_type.__name__}: {identity}")
        return self._fact(contract_type, row)

    def _fact(self, contract_type, row):
        fields = {column.name: getattr(row, column.name) for column in row.__table__.columns}
        fields.pop("created_at")
        if "source_kind" in fields:
            provenance = {
                key: fields.pop(key)
                for key in (
                    "source_kind",
                    "source_system",
                    "external_record_id",
                    "source_version",
                    "source_uri",
                    "content_hash",
                    "observed_at",
                )
            }
            provenance["kind"] = provenance.pop("source_kind")
            provenance_type = (
                c.RetailerStatusProvenance if contract_type == c.RetailerStatusFact else Provenance
            )
            fields["provenance"] = provenance_type(**provenance)
        if "amount_minor" in fields:
            fields["price"] = Money(
                amount_minor=fields.pop("amount_minor"),
                currency=fields.pop("currency"),
            )
        if contract_type == c.ReferencePriceEntryFact:
            fields["book"] = self.get(c.ReferencePriceBookFact, fields.pop("book_id"))
        if contract_type in (c.ProcurementClassMemberFact, c.PlanningPriceQuoteDraft):
            fields["mapping"] = self.get(c.IngredientProductMapFact, fields.pop("mapping_id"))
            fields.pop("retail_product_id")
            fields.pop("ingredient_id")
        if contract_type == c.ProcurementClassMemberFact:
            fields.pop("id")
        if contract_type == c.PlanningPriceQuoteDraft:
            fields["reference_price_pair"] = c.ReferencePricePair(
                money_for_reference_quantity=Money(
                    amount_minor=fields.pop("reference_amount_minor"),
                    currency=fields.pop("currency"),
                ),
                priced_ap_g=fields.pop("reference_ap_g"),
                price_basis=fields.pop("price_basis"),
            )
            fields["package"] = self.get(c.PackageFact, fields.pop("package_id"))
            fields.pop("granularity")
            for key, field, target in (
                ("observation_id", "observation", c.PriceObservationFact),
                ("calibration_id", "calibration", c.RetailPriceCalibrationFact),
                ("reference_entry_id", "reference", c.ReferencePriceEntryFact),
            ):
                identity = fields.pop(key)
                fields[field] = self.get(target, identity) if identity is not None else None
        if contract_type == c.PlanningProcurementOptionDraft:
            fields["quote"] = self.get(c.PlanningPriceQuoteDraft, fields.pop("quote_id"))
            fields.pop("procurement_class_id")
        return contract_type.model_validate(fields)

    def retailer_status_at(
        self, retailer_id: UUID, as_of: AwareTime
    ) -> c.RetailerStatusFact | None:
        """No fact means unknown status. Scheduled facts do not change earlier views."""
        timestamp = TypeAdapter(AwareTime).validate_python(as_of)
        row = self.session.scalar(
            select(m.RetailerStatusFact)
            .where(
                m.RetailerStatusFact.retailer_id == retailer_id,
                m.RetailerStatusFact.effective_at <= timestamp,
            )
            .order_by(m.RetailerStatusFact.effective_at.desc())
            .limit(1)
        )
        return self._fact(c.RetailerStatusFact, row) if row is not None else None

    def procurement_snapshot(self, class_id: UUID) -> c.ProcurementSnapshotDraft:
        cls = self.get(c.ProcurementClassFact, class_id)
        members = self.session.scalars(
            select(m.ProcurementClassMember)
            .where(
                m.ProcurementClassMember.procurement_class_id == class_id,
            )
            .order_by(m.ProcurementClassMember.mapping_id)
        ).all()
        options = self.session.scalars(
            select(m.PlanningProcurementOption)
            .where(
                m.PlanningProcurementOption.procurement_class_id == class_id,
            )
            .order_by(m.PlanningProcurementOption.rank)
        ).all()
        return c.ProcurementSnapshotDraft(
            procurement_class=cls,
            members=tuple(self._fact(c.ProcurementClassMemberFact, row) for row in members),
            options=tuple(self._fact(c.PlanningProcurementOptionDraft, row) for row in options),
        )
