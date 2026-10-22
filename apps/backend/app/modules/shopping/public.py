"""Quantitative demand storage/read facts; no purchase/import or actual-spend service."""

from decimal import Decimal, localcontext
from uuid import UUID

from sqlalchemy import insert

from app.domain.units import Quantity
from app.modules.inventory.contracts import PhysicalInventorySnapshot
from app.modules.planning.contracts import PlanProposalSnapshot
from app.modules.shopping.contracts import ObservedAcquisitionCoverageDraft
from app.modules.shopping.models import ShoppingDemandContribution, ShoppingRequirementIntent


def store_shopping_intents(
    session, *, proposal_id, household_id, plan_id, requirements, contributions=()
):
    for model, values in (
        (ShoppingRequirementIntent, requirements),
        (ShoppingDemandContribution, contributions),
    ):
        for value in values:
            fields = value.model_dump(exclude={"quantity"})
            fields.update(
                amount=value.quantity.amount,
                basis=value.quantity.basis,
                item_ref=value.quantity.item_ref,
            )
            session.execute(
                insert(model.__table__).values(
                    **fields, proposal_id=proposal_id, household_id=household_id, plan_id=plan_id
                )
            )


def observed_acquisition_coverage(
    proposal: PlanProposalSnapshot,
    requirement_id: UUID,
    inventory: PhysicalInventorySnapshot,
    movement_ids: tuple[UUID, ...],
):
    """Material acquisition evidence only, not actual-price PurchaseFulfillment proof."""
    proposal = PlanProposalSnapshot.model_validate(proposal.model_dump())
    if proposal.graph.household_id != inventory.household_id:
        raise ValueError("Acquisition coverage crosses household ownership")
    requirement = next((r for r in proposal.graph.shopping if r.node_id == requirement_id), None)
    if requirement is None:
        raise ValueError("Unknown exact proposal requirement")
    if len(set(movement_ids)) != len(movement_ids):
        raise ValueError("Duplicate acquisition evidence")
    events = {m.id: m for m in inventory.movements}
    lots = {lot.id: lot for lot in inventory.lots}
    total = Decimal(0)
    with localcontext() as ctx:
        ctx.prec = 160
        for key in movement_ids:
            m = events.get(key)
            if (
                m is None
                or m.movement_type != "ACQUIRE"
                or (m.quantity.basis, m.quantity.item_ref)
                != (requirement.quantity.basis, requirement.quantity.item_ref)
                or (lots[m.lot_id].ingredient_id != requirement.ingredient_id)
            ):
                raise ValueError("Acquisition source identity/basis/ingredient mismatch")
            total += m.quantity.amount
        kwargs = dict(basis=requirement.quantity.basis, item_ref=requirement.quantity.item_ref)
        return ObservedAcquisitionCoverageDraft(
            household_id=proposal.graph.household_id,
            plan_id=proposal.graph.plan_id,
            proposal_id=proposal.id,
            requirement_node_id=requirement.node_id,
            required=requirement.quantity,
            acquired=Quantity(amount=total, **kwargs),
            shortfall=Quantity(
                amount=max(Decimal(0), requirement.quantity.amount - total), **kwargs
            ),
            movement_ids=movement_ids,
        )
