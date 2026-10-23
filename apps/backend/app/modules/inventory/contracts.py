"""Physical ledger contracts (INV-011/012/013/018/019), plus legacy draft seam."""

from decimal import Decimal, localcontext
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.contracts import (
    AwareTime,
    Contract,
    Identifier,
    Label,
    Sha256,
)
from app.domain.snapshots import RawIngredientAssetFact
from app.domain.units import CalculatedQuantity, ExternalRecordId, ExternalVersion, Quantity
from app.modules.retail.contracts import IngredientProductMapFact


class InventoryContract(Contract):
    contract_version: Literal["inventory-v1"] = "inventory-v1"


class AssetType(StrEnum):
    RAW_INGREDIENT = "RAW_INGREDIENT"
    PREPARED_COMPONENT = "PREPARED_COMPONENT"
    COOKED_DISH = "COOKED_DISH"


class Lifecycle(StrEnum):
    ACTIVE = "ACTIVE"
    DEPLETED = "DEPLETED"
    EXPIRED = "EXPIRED"
    DISCARDED = "DISCARDED"


class ObservationConfidence(StrEnum):
    CONFIRMED = "CONFIRMED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class PhysicalEvidence(InventoryContract):
    """Source of explicit confirmation; never an inference or availability quote."""

    kind: Literal["USER", "RECEIPT", "BARCODE", "EXECUTION"]
    source_system: Identifier
    external_record_id: ExternalRecordId
    source_version: ExternalVersion
    confirmed_by_user_id: UUID
    confirmation: Literal["EXPLICIT"] = "EXPLICIT"


class InventoryCommand(InventoryContract):
    household_id: UUID
    idempotency_key: Identifier
    occurred_at: AwareTime
    evidence: PhysicalEvidence
    reason: Label


class AcquireInventoryCommand(InventoryCommand):
    lot_id: UUID
    asset_type: AssetType
    ingredient_id: UUID | None = None
    quantity: Quantity
    usable_until: AwareTime | None = None
    observation_confidence: ObservationConfidence = ObservationConfidence.CONFIRMED
    serving_definition: Label | None = None
    retail_mapping_id: UUID | None = None

    @model_validator(mode="after")
    def asset_identity(self):
        if self.quantity.amount <= 0:
            raise ValueError("Acquisition quantity must be positive")
        if self.usable_until is not None and self.usable_until <= self.occurred_at:
            raise ValueError("usable_until must follow acquisition")
        if self.asset_type == AssetType.COOKED_DISH:
            if (
                self.ingredient_id is not None
                or self.quantity.basis != "SERVING"
                or self.serving_definition is None
            ):
                raise ValueError("Cooked dish requires contextual servings and a definition")
        elif (
            self.ingredient_id is None
            or self.serving_definition is not None
            or self.quantity.basis
            not in (
                {"AP_G", "EP_RAW_G", "COUNT"}
                if self.asset_type == AssetType.RAW_INGREDIENT
                else {"COOKED_G"}
            )
        ):
            raise ValueError("Ingredient asset has incompatible measurement basis")
        if self.retail_mapping_id is not None and (
            self.asset_type != AssetType.RAW_INGREDIENT or self.quantity.basis != "AP_G"
        ):
            raise ValueError("Retail mapping origin requires raw AP_G")
        return self


class LotCommand(InventoryCommand):
    lot_id: UUID
    quantity: Quantity

    @model_validator(mode="after")
    def positive(self):
        if self.quantity.amount <= 0:
            raise ValueError("Physical movement/reservation quantity must be positive")
        return self


class ConsumeInventoryCommand(LotCommand):
    pass


class DiscardInventoryCommand(LotCommand):
    pass


class ReconcileInventoryCommand(LotCommand):
    direction: Literal["INCREASE", "DECREASE"]
    correction_of: UUID | None = None


class ExpireInventoryCommand(InventoryCommand):
    lot_id: UUID


class ReserveInventoryCommand(LotCommand):
    reservation_id: UUID
    purpose: Label


class ReleaseReservationCommand(InventoryCommand):
    lot_id: UUID
    reservation_id: UUID


class InventoryLot(InventoryContract):
    id: UUID
    household_id: UUID
    asset_type: AssetType
    ingredient_id: UUID | None
    acquired_quantity: Quantity
    acquired_at: AwareTime
    created_at: AwareTime
    usable_until: AwareTime | None
    observation_confidence: ObservationConfidence
    serving_definition: Label | None
    retail_mapping: IngredientProductMapFact | None = None

    @model_validator(mode="after")
    def identity(self):
        # Reuse the exact command identity policy without fabricating acquisition evidence.
        if self.acquired_quantity.amount <= 0:
            raise ValueError("Lot must retain positive acquisition quantity")
        q = self.acquired_quantity
        if self.asset_type == AssetType.COOKED_DISH:
            if (
                self.ingredient_id is not None
                or q.basis != "SERVING"
                or not self.serving_definition
            ):
                raise ValueError("Cooked dish identity requires defined servings")
        elif (
            not self.ingredient_id
            or self.serving_definition is not None
            or q.basis
            not in (
                {"AP_G", "EP_RAW_G", "COUNT"}
                if self.asset_type == AssetType.RAW_INGREDIENT
                else {"COOKED_G"}
            )
        ):
            raise ValueError("Ingredient lot basis incompatible")
        if self.usable_until is not None and self.usable_until <= self.acquired_at:
            raise ValueError("Invalid lot expiry")
        if self.retail_mapping is not None and (
            self.asset_type != AssetType.RAW_INGREDIENT
            or q.basis != "AP_G"
            or self.retail_mapping.ingredient_id != self.ingredient_id
            or self.retail_mapping.status != "REVIEWED"
        ):
            raise ValueError("Retail mapping evidence must bind exact raw AP ingredient")
        return self


class MovementType(StrEnum):
    ACQUIRE = "ACQUIRE"
    CONSUME = "CONSUME"
    DISCARD = "DISCARD"
    RECONCILE_INCREASE = "RECONCILE_INCREASE"
    RECONCILE_DECREASE = "RECONCILE_DECREASE"
    EXPIRE = "EXPIRE"


class LedgerFact(InventoryContract):
    id: UUID
    household_id: UUID
    lot_id: UUID
    occurred_at: AwareTime
    recorded_at: AwareTime
    ledger_sequence: Annotated[int, Field(strict=True, gt=0)]
    phase: Annotated[int, Field(strict=True, ge=10, le=60)]
    idempotency_key: Identifier
    command_fingerprint: Sha256
    evidence: PhysicalEvidence
    reason: Label

    @model_validator(mode="after")
    def recording_order(self):
        if self.occurred_at > self.recorded_at:
            raise ValueError("Physical occurrence cannot follow recording")
        return self


class InventoryMovement(LedgerFact):
    movement_type: MovementType
    quantity: Quantity
    correction_of: UUID | None = None

    @model_validator(mode="after")
    def amount_and_correction(self):
        if (self.movement_type == "EXPIRE") != (self.quantity.amount == 0):
            raise ValueError("Only expiry is a zero-quantity lifecycle fact")
        if self.correction_of is not None and not self.movement_type.startswith("RECONCILE_"):
            raise ValueError("Correction reference belongs to reconciliation")
        return self


class InventoryReservation(LedgerFact):
    quantity: Quantity
    purpose: Label

    @model_validator(mode="after")
    def positive(self):
        if self.quantity.amount <= 0:
            raise ValueError("Reservation quantity must be positive")
        return self


class InventoryReservationRelease(LedgerFact):
    reservation_id: UUID


class InventoryPosition(InventoryContract):
    lot_id: UUID
    remaining: Quantity
    reserved: Quantity
    lifecycle_state: Lifecycle

    @model_validator(mode="after")
    def quantity_identity(self):
        if (self.remaining.basis, self.remaining.item_ref) != (
            self.reserved.basis,
            self.reserved.item_ref,
        ) or self.reserved.amount > self.remaining.amount:
            raise ValueError("Position reservation must share identity and fit physical stock")
        return self

    @property
    def allocatable(self) -> Quantity:
        """Unusable/expired matter is retained physically, but cannot be allocated."""
        with localcontext() as ctx:
            ctx.prec = 160
            amount = (
                self.remaining.amount - self.reserved.amount
                if self.lifecycle_state == Lifecycle.ACTIVE
                else Decimal(0)
            )
        return Quantity(amount=amount, basis=self.remaining.basis, item_ref=self.remaining.item_ref)


def event_phase(asset_type: AssetType, kind: str) -> int:
    if kind == "ACQUIRE":
        return 10 if asset_type == "RAW_INGREDIENT" else 40
    if kind == "CONSUME":
        return 30 if asset_type == "RAW_INGREDIENT" else 50
    return 60 if kind in {"DISCARD", "EXPIRE"} else 20


class PhysicalInventorySnapshot(InventoryContract):
    """Confirmed facts only; not an activation-ready PlanningState/ValidationSubject."""

    status: Literal["DRAFT"] = "DRAFT"
    activation_ready: Literal[False] = False
    household_id: UUID
    as_of: AwareTime
    lots: tuple[InventoryLot, ...]
    movements: tuple[InventoryMovement, ...]
    reservations: tuple[InventoryReservation, ...]
    releases: tuple[InventoryReservationRelease, ...]
    positions: tuple[InventoryPosition, ...]

    @model_validator(mode="after")
    def replay_primitives(self):
        lots = {lot.id: lot for lot in self.lots}
        if len(lots) != len(self.lots) or any(
            lot.household_id != self.household_id or lot.acquired_at > self.as_of
            for lot in self.lots
        ):
            raise ValueError("Snapshot lot ownership/time/identity mismatch")
        remaining = dict.fromkeys(lots, Decimal(0))
        reserved = dict.fromkeys(lots, Decimal(0))
        states = dict.fromkeys(lots, Lifecycle.ACTIVE)
        opened, seen, active = set(), {}, {}
        events = (*self.movements, *self.reservations, *self.releases)
        sequences = [e.ledger_sequence for e in events]
        if len(set(sequences)) != len(sequences):
            raise ValueError("Ledger sequences must be unique")
        for e in sorted(events, key=lambda e: (e.occurred_at, e.phase, e.ledger_sequence)):
            lot = lots.get(e.lot_id)
            if not lot or e.household_id != self.household_id or e.occurred_at > self.as_of:
                raise ValueError("Event ownership/time mismatch")
            if e.occurred_at < lot.acquired_at or e.phase != event_phase(
                lot.asset_type, e.movement_type if isinstance(e, InventoryMovement) else "RESERVE"
            ):
                raise ValueError("Event chronology/phase mismatch")
            if hasattr(e, "quantity") and (e.quantity.basis, e.quantity.item_ref) != (
                lot.acquired_quantity.basis,
                lot.acquired_quantity.item_ref,
            ):
                raise ValueError("Event quantity identity mismatch")
            with localcontext() as ctx:
                ctx.prec = 160
                if isinstance(e, InventoryMovement):
                    kind = e.movement_type
                    if kind == "ACQUIRE":
                        if (
                            e.lot_id in opened
                            or e.quantity != lot.acquired_quantity
                            or e.occurred_at != lot.acquired_at
                        ):
                            raise ValueError("Invalid opening acquisition")
                        opened.add(e.lot_id)
                    elif e.lot_id not in opened:
                        raise ValueError("Movement before acquisition")
                    if kind == "CONSUME" and (
                        states[e.lot_id] == Lifecycle.EXPIRED
                        or lot.usable_until is not None
                        and e.occurred_at >= lot.usable_until
                    ):
                        raise ValueError("Consumption after expiry")
                    if kind == "EXPIRE":
                        if (
                            lot.usable_until is None
                            or e.occurred_at < lot.usable_until
                            or remaining[e.lot_id] == 0
                        ):
                            raise ValueError("Premature expiry")
                        states[e.lot_id] = Lifecycle.EXPIRED
                    else:
                        if e.correction_of is not None and seen.get(e.correction_of) != e.lot_id:
                            raise ValueError("Correction must reference prior same-lot movement")
                        remaining[e.lot_id] += e.quantity.amount * (
                            1 if kind in {"ACQUIRE", "RECONCILE_INCREASE"} else -1
                        )
                        if remaining[e.lot_id] == 0:
                            states[e.lot_id] = (
                                Lifecycle.DISCARDED if kind == "DISCARD" else Lifecycle.DEPLETED
                            )
                        elif states[e.lot_id] != Lifecycle.EXPIRED:
                            states[e.lot_id] = Lifecycle.ACTIVE
                    seen[e.id] = e.lot_id
                elif isinstance(e, InventoryReservation):
                    if (
                        e.lot_id not in opened
                        or states[e.lot_id] != Lifecycle.ACTIVE
                        or lot.usable_until is not None
                        and e.occurred_at >= lot.usable_until
                    ):
                        raise ValueError("Reservation on unusable stock")
                    active[e.id] = e
                    reserved[e.lot_id] += e.quantity.amount
                else:
                    r = active.pop(e.reservation_id, None)
                    if r is None or r.lot_id != e.lot_id:
                        raise ValueError("Release requires active same-lot reservation")
                    reserved[e.lot_id] -= r.quantity.amount
            if remaining[e.lot_id] < reserved[e.lot_id] or reserved[e.lot_id] < 0:
                raise ValueError("Chronological stock/reservation deficit")
            if states[e.lot_id] == Lifecycle.EXPIRED and reserved[e.lot_id] != 0:
                raise ValueError("Release reservation before explicit expiry")
        if opened != set(lots):
            raise ValueError("Every lot requires opening acquisition")
        expected = {}
        for identity, lot in lots.items():
            state = states[identity]
            if (
                remaining[identity] > 0
                and lot.usable_until is not None
                and self.as_of >= lot.usable_until
            ):
                state = Lifecycle.EXPIRED
            expected[identity] = InventoryPosition(
                lot_id=identity,
                remaining=Quantity(
                    amount=remaining[identity],
                    basis=lot.acquired_quantity.basis,
                    item_ref=lot.acquired_quantity.item_ref,
                ),
                reserved=Quantity(
                    amount=reserved[identity],
                    basis=lot.acquired_quantity.basis,
                    item_ref=lot.acquired_quantity.item_ref,
                ),
                lifecycle_state=state,
            )
        if (
            len(self.positions) != len(expected)
            or {p.lot_id: p for p in self.positions} != expected
        ):
            raise ValueError("Position summary disagrees with immutable primitive replay")
        return self


class BatchFlowLinkDraft(InventoryContract):
    """Future orchestration seam only: not permission to create a physical batch."""

    status: Literal["DRAFT"] = "DRAFT"
    execution_ready: Literal[False] = False
    household_id: UUID
    input_lot_ids: Annotated[tuple[UUID, ...], Field(min_length=1)]
    output_lot_ids: Annotated[tuple[UUID, ...], Field(min_length=1)]
    recipe_version_id: UUID
    grounded_variant_fingerprint: Sha256
    input_movement_ids: tuple[UUID, ...]
    output_movement_ids: tuple[UUID, ...]

    @model_validator(mode="after")
    def separate_assets(self):
        if (
            len(set(self.input_lot_ids)) != len(self.input_lot_ids)
            or len(set(self.output_lot_ids)) != len(self.output_lot_ids)
            or set(self.input_lot_ids) & set(self.output_lot_ids)
            or len(self.input_lot_ids) != len(self.input_movement_ids)
            or len(self.output_lot_ids) != len(self.output_movement_ids)
        ):
            raise ValueError("Draft batch link needs separate assets and exact event references")
        return self


class RetailSourcedAPAssetDraft(RawIngredientAssetFact):
    """Inventory owns this future handoff. AP source evidence must not be discarded.

    The old neutral m0 RawIngredientAssetFact is still an incomplete validator draft,
    not an accepted retail acquisition handoff. This contract grants no physical stock.
    """

    contract_version: Literal["inventory-retail-origin.m1-draft.2"] = (
        "inventory-retail-origin.m1-draft.2"
    )
    validation_ready: Literal[False] = False
    retail_mapping: IngredientProductMapFact

    @model_validator(mode="after")
    def preserve_product_mapping(self):
        if self.quantity.basis != "AP_G":
            raise ValueError("Retail AP asset handoff requires AP_G")
        if self.ingredient_id != self.retail_mapping.ingredient_id:
            raise ValueError("Inventory ingredient and product mapping must agree")
        if self.retail_mapping.status != "REVIEWED":
            raise ValueError("Retail origin requires reviewed mapping evidence")
        return self


class InventoryCandidateLot(Contract):
    contract_version: Literal["inventory-candidate-lot.v1"] = "inventory-candidate-lot.v1"
    allocation: Literal["UNALLOCATED"] = "UNALLOCATED"
    lot: InventoryLot
    position: InventoryPosition
    usable_quantity: CalculatedQuantity
