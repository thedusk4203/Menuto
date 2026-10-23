"""Confirmed potential sources, never allocation, reservation or physical mutation."""

from decimal import Inexact, Rounded, localcontext

from app.domain.units import CalculatedQuantity
from app.modules.inventory.contracts import InventoryCandidateLot


def resolve_inventory_sources(snapshot, *, ingredient_id, quantity):
    positions = {p.lot_id: p for p in snapshot.positions}
    result = []
    for lot in sorted(snapshot.lots, key=lambda row: str(row.id)):
        p = positions.get(lot.id)
        if (
            lot.household_id != snapshot.household_id
            or lot.ingredient_id != ingredient_id
            or p is None
            or p.lifecycle_state != "ACTIVE"
            or lot.observation_confidence != "CONFIRMED"
            or (lot.usable_until is not None and lot.usable_until <= snapshot.as_of)
        ):
            continue
        with localcontext() as ctx:
            ctx.prec = 160
            ctx.traps[Inexact] = ctx.traps[Rounded] = True
            amount = p.remaining.amount - p.reserved.amount
        if amount <= 0:
            continue
        usable = CalculatedQuantity(
            amount=amount, basis=p.remaining.basis, item_ref=p.remaining.item_ref
        )
        if usable.basis == "AP_G" and quantity.basis == "EP_RAW_G" and lot.retail_mapping:
            usable = lot.retail_mapping.apply(usable).ep_raw
        if (usable.basis, usable.item_ref) != (quantity.basis, quantity.item_ref):
            continue
        result.append(InventoryCandidateLot(lot=lot, position=p, usable_quantity=usable))
    return tuple(result)
