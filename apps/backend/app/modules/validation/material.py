"""Independent imperative ledger arithmetic. No Inventory replay/helper imports."""

from decimal import Decimal, Inexact, Rounded, localcontext

from app.domain.units import QuantityIdentity
from app.modules.validation.contracts import MaterialBalanceDerivation


def check_material(subject, emit):
    facts = subject.inventory
    lots = {lot.id: lot for lot in facts.lots}
    events = (*facts.movements, *facts.reservations, *facts.releases)
    if len(lots) != len(facts.lots):
        emit("DUPLICATE_LOT", "ERROR", "DATA", "inventory", "Duplicate physical identity")
    for collection in (facts.movements, facts.reservations, facts.releases, facts.positions):
        keys = [getattr(e, "id", getattr(e, "lot_id", None)) for e in collection]
        if len(set(keys)) != len(keys):
            emit(
                "DUPLICATE_MATERIAL_FACT", "ERROR", "DATA", "inventory", "Duplicate source identity"
            )
    closing = dict.fromkeys(lots, Decimal(0))
    incompatible = {
        e.lot_id
        for e in (*facts.movements, *facts.reservations)
        if e.lot_id in lots
        and (e.quantity.basis, e.quantity.item_ref)
        != (lots[e.lot_id].acquired_quantity.basis, lots[e.lot_id].acquired_quantity.item_ref)
    }
    # Whole-history conservation starts at zero. ACQUIRE is opening, never counted twice.
    with localcontext() as ctx:
        ctx.prec = 160
        ctx.traps[Inexact] = ctx.traps[Rounded] = True
        for e in facts.movements:
            if e.lot_id in lots and e.lot_id not in incompatible:
                if e.movement_type in {"ACQUIRE", "RECONCILE_INCREASE"}:
                    closing[e.lot_id] += e.quantity.amount
                elif e.movement_type in {"CONSUME", "DISCARD", "RECONCILE_DECREASE"}:
                    closing[e.lot_id] -= e.quantity.amount
        cache = {p.lot_id: p for p in facts.positions}
        if set(cache) != set(lots):
            emit(
                "MATERIAL_POSITION_COVERAGE",
                "ERROR",
                "DATA",
                "inventory",
                "Missing/foreign closing position",
            )
        for key, amount in closing.items():
            if key not in incompatible and key in cache and cache[key].remaining.amount != amount:
                emit(
                    "MATERIAL_CONSERVATION",
                    "ERROR",
                    "EXECUTION",
                    key,
                    "ACQUIRE + reconcile inflows - outflows differs from closing",
                    str(amount),
                    str(cache[key].remaining.amount),
                )
        sequences = [e.ledger_sequence for e in events]
        if len(sequences) != len(set(sequences)):
            emit(
                "AMBIGUOUS_CAUSAL_ORDER",
                "FATAL",
                "DATA",
                "inventory",
                "Ledger sequence must distinguish events; UUID is not ordering",
            )
            return ()
        frontier = max(sequences, default=0)
        if frontier != subject.source_frontier.inventory_ledger_sequence:
            emit(
                "INVENTORY_FRONTIER_MISMATCH",
                "ERROR",
                "DATA",
                "inventory",
                "Source frontier disagrees with supplied event primitives",
            )
        balance = dict.fromkeys(lots, Decimal(0))
        reserved = dict.fromkeys(lots, Decimal(0))
        lifecycle = dict.fromkeys(lots, "ACTIVE")
        opened, active, previous_movements = set(), {}, {}
        for e in sorted(events, key=lambda v: (v.occurred_at, v.phase, v.ledger_sequence)):
            lot = lots.get(e.lot_id)
            if lot is None:
                emit(
                    "UNKNOWN_MATERIAL_LOT",
                    "ERROR",
                    "DATA",
                    e.id,
                    "Event has no physical lot",
                    str(e.lot_id),
                )
                continue
            if e.household_id != subject.household_id or lot.household_id != subject.household_id:
                emit(
                    "MATERIAL_HOUSEHOLD_MISMATCH",
                    "ERROR",
                    "DATA",
                    e.id,
                    "Physical ownership crosses household",
                )
            if e.occurred_at > facts.as_of:
                emit(
                    "MATERIAL_AFTER_CUTOFF",
                    "ERROR",
                    "DATA",
                    e.id,
                    "Event is after effective snapshot cutoff",
                )
            is_movement = hasattr(e, "movement_type")
            is_reservation = hasattr(e, "purpose")
            kind = e.movement_type if is_movement else ("RESERVE" if is_reservation else "RELEASE")
            expected_phase = (
                (10 if lot.asset_type == "RAW_INGREDIENT" else 40)
                if kind == "ACQUIRE"
                else (
                    (30 if lot.asset_type == "RAW_INGREDIENT" else 50)
                    if kind == "CONSUME"
                    else (60 if kind in {"DISCARD", "EXPIRE"} else 20)
                )
            )
            if e.phase != expected_phase:
                emit(
                    "MATERIAL_PHASE_MISMATCH",
                    "ERROR",
                    "DATA",
                    e.id,
                    "Asset kind and event phase disagree",
                )
            q = getattr(e, "quantity", None)
            identity = (lot.acquired_quantity.basis, lot.acquired_quantity.item_ref)
            if q is not None and (q.basis, q.item_ref) != identity:
                emit(
                    "MATERIAL_BASIS_MISMATCH",
                    "ERROR",
                    "DATA",
                    e.id,
                    "No AP/EP/cooked/count/serving conversion is implicit",
                )
                continue
            if kind == "ACQUIRE":
                if e.lot_id in opened:
                    emit(
                        "DUPLICATE_ACQUISITION",
                        "ERROR",
                        "EXECUTION",
                        e.id,
                        "Lot cannot acquire twice",
                    )
                if e.occurred_at != lot.acquired_at or q != lot.acquired_quantity:
                    emit(
                        "LOT_ACQUISITION_MISMATCH",
                        "ERROR",
                        "DATA",
                        e.id,
                        "Opening evidence disagrees with lot identity",
                    )
                opened.add(e.lot_id)
            elif e.lot_id not in opened:
                emit(
                    "MATERIAL_BEFORE_ACQUIRE",
                    "ERROR",
                    "EXECUTION",
                    e.id,
                    "Material used before opening acquisition",
                )
            expired = lot.usable_until is not None and e.occurred_at >= lot.usable_until
            if kind == "CONSUME" and (expired or lifecycle[e.lot_id] == "EXPIRED"):
                emit(
                    "CONSUME_EXPIRED_MATERIAL",
                    "ERROR",
                    "EXECUTION",
                    e.id,
                    "Consumption violates resolved usable_until",
                )
            if is_movement:
                if (
                    e.correction_of is not None
                    and previous_movements.get(e.correction_of) != e.lot_id
                ):
                    emit(
                        "INVALID_CORRECTION_PARENT",
                        "ERROR",
                        "EXECUTION",
                        e.id,
                        "Correction must reference prior same-lot movement",
                    )
                if kind in {"ACQUIRE", "RECONCILE_INCREASE"}:
                    balance[e.lot_id] += q.amount
                elif kind in {"CONSUME", "RECONCILE_DECREASE", "DISCARD"}:
                    balance[e.lot_id] -= q.amount
                elif kind == "EXPIRE":
                    if not expired or balance[e.lot_id] <= 0 or reserved[e.lot_id] != 0:
                        emit(
                            "INVALID_EXPIRY_TRANSITION",
                            "ERROR",
                            "EXECUTION",
                            e.id,
                            "Explicit expiry needs expired positive stock and released intent",
                        )
                    lifecycle[e.lot_id] = "EXPIRED"
                if kind != "EXPIRE":
                    if balance[e.lot_id] == 0:
                        lifecycle[e.lot_id] = "DISCARDED" if kind == "DISCARD" else "DEPLETED"
                    elif lifecycle[e.lot_id] != "EXPIRED":
                        lifecycle[e.lot_id] = "ACTIVE"
                previous_movements[e.id] = e.lot_id
            elif is_reservation:
                if expired or lifecycle[e.lot_id] != "ACTIVE":
                    emit(
                        "RESERVE_UNUSABLE_MATERIAL",
                        "ERROR",
                        "PLAN",
                        e.id,
                        "Allocation intent requires usable physical stock",
                    )
                active[e.id] = e
                reserved[e.lot_id] += q.amount
            else:
                r = active.pop(e.reservation_id, None)
                if r is None or r.lot_id != e.lot_id:
                    emit(
                        "INVALID_RESERVATION_RELEASE",
                        "ERROR",
                        "EXECUTION",
                        e.id,
                        "Release must reference active same-lot reservation",
                    )
                else:
                    reserved[e.lot_id] -= r.quantity.amount
            if balance[e.lot_id] < 0:
                emit(
                    "CHRONOLOGICAL_STOCK_DEFICIT",
                    "ERROR",
                    "EXECUTION",
                    e.id,
                    "Stock becomes negative",
                    str(balance[e.lot_id]),
                )
            if reserved[e.lot_id] < 0 or reserved[e.lot_id] > balance[e.lot_id]:
                emit(
                    "CHRONOLOGICAL_RESERVATION_DEFICIT",
                    "ERROR",
                    "PLAN",
                    e.id,
                    "Reservation intent exceeds physical stock",
                )
        if opened != set(lots):
            emit(
                "MISSING_ACQUISITION",
                "ERROR",
                "DATA",
                "inventory",
                "Each lot needs opening evidence",
            )
        result = []
        for key, lot in sorted(lots.items(), key=lambda v: str(v[0])):
            if lot.household_id != subject.household_id:
                emit(
                    "MATERIAL_HOUSEHOLD_MISMATCH",
                    "ERROR",
                    "DATA",
                    key,
                    "Lot owner differs from subject",
                )
            state = lifecycle[key]
            if (
                balance[key] > 0
                and lot.usable_until is not None
                and facts.as_of >= lot.usable_until
            ):
                state = "EXPIRED"
            p = cache.get(key)
            if p is not None and (
                (p.remaining.basis, p.remaining.item_ref)
                != (lot.acquired_quantity.basis, lot.acquired_quantity.item_ref)
                or p.reserved.amount != reserved[key]
                or p.lifecycle_state != state
            ):
                emit(
                    "MATERIAL_POSITION_MISMATCH",
                    "ERROR",
                    "DATA",
                    key,
                    "Cached lifecycle/reservation/identity differs from primitive replay",
                )
            if key in incompatible:
                continue  # An incompatible unit cannot produce a closing quantity estimate.
            result.append(
                MaterialBalanceDerivation(
                    lot_id=key,
                    quantity_identity=QuantityIdentity(
                        basis=lot.acquired_quantity.basis, item_ref=lot.acquired_quantity.item_ref
                    ),
                    signed_closing_amount=balance[key],
                    signed_reserved_amount=reserved[key],
                )
            )
        return tuple(result)
