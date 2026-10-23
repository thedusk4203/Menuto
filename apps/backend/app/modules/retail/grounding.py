"""Retail-owned supply coefficients. No ranking, acquisition or checkout costing."""

from app.domain.units import CalculatedQuantity
from app.modules.retail.contracts import ProcurementSupplyPath


def resolve_procurement_sources(
    *, ingredient_id, quantity, sources, statuses, region_code, currency, as_of
):
    if quantity.basis != "EP_RAW_G":
        return ()
    result = []
    for source in sorted(sources, key=lambda s: str(s.procurement_class.id)):
        cls = source.procurement_class
        if cls.ingredient_id != ingredient_id or cls.provenance.observed_at > as_of:
            continue
        for option in sorted(source.options, key=lambda o: str(o.id)):
            q = option.quote
            states = [
                s
                for s in statuses
                if s.retailer_id == q.retailer_id
                and s.effective_at <= as_of
                and s.provenance.observed_at <= as_of
            ]
            latest = max(states, key=lambda s: s.effective_at) if states else None
            if (
                latest is None
                or latest.status != "ACTIVE"
                or q.availability == "UNAVAILABLE"
                or q.region_code != region_code
                or q.reference_price_pair.money_for_reference_quantity.currency != currency
                or q.as_of > as_of
                or option.provenance.observed_at > as_of
            ):
                continue
            mapping, pack = q.mapping, q.package

            def ep(amount):
                return mapping.apply(CalculatedQuantity(amount=amount, basis="AP_G")).ep_raw

            coefficients = {}
            if pack.granularity == "FIXED_PACK":
                coefficients["nominal_ep_g"] = ep(pack.fixed_ap_g).amount
            elif pack.granularity == "CATCH_WEIGHT":
                coefficients = dict(
                    nominal_ep_g=ep(pack.expected_ap_g).amount,
                    low_ep_g=ep(pack.low_ap_g).amount,
                    high_ep_g=ep(pack.high_ap_g).amount,
                )
            else:
                coefficients = dict(
                    minimum_ep_g=ep(pack.minimum_ap_g).amount, step_ep_g=ep(pack.step_ap_g).amount
                )
            result.append(
                ProcurementSupplyPath(
                    procurement_class_id=cls.id,
                    option=option,
                    retailer_status=latest,
                    availability=q.availability,
                    priced_ep_raw=ep(q.reference_price_pair.priced_ap_g),
                    **coefficients,
                )
            )
    return tuple(result)


def capture_procurement_sources(session, class_ids):
    from sqlalchemy import select

    from app.modules.retail import contracts as c
    from app.modules.retail import models as m
    from app.modules.retail.repository import RetailEvidenceRepository

    repo = RetailEvidenceRepository(session)
    sources = []
    for identity in sorted(set(class_ids), key=str):
        cls = repo.get(c.ProcurementClassFact, identity)
        members = tuple(
            repo._fact(c.ProcurementClassMemberFact, r)
            for r in session.scalars(
                select(m.ProcurementClassMember).where(
                    m.ProcurementClassMember.procurement_class_id == identity
                )
            )
        )
        options = tuple(
            repo.get(c.PlanningProcurementOptionDraft, r.id)
            for r in session.scalars(
                select(m.PlanningProcurementOption).where(
                    m.PlanningProcurementOption.procurement_class_id == identity
                )
            )
        )
        sources.append(
            c.ProcurementSnapshotDraft(procurement_class=cls, members=members, options=options)
        )
    retailers = {o.quote.retailer_id for s in sources for o in s.options}
    statuses = tuple(
        repo.get(c.RetailerStatusFact, r.id)
        for r in session.scalars(
            select(m.RetailerStatusFact).where(m.RetailerStatusFact.retailer_id.in_(retailers))
        )
    )
    return tuple(sources), statuses
