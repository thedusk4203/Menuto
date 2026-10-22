"""Transactional physical commands. Caller commits/rolls back; ORM rows never escape."""

import json
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.domain.units import Quantity
from app.modules.inventory import contracts as c
from app.modules.inventory import models as m
from app.modules.retail.public import read_inventory_mapping


class InventoryService:
    def __init__(self, session: Session):
        self.session = session

    def _fingerprint(self, command):
        body = {"command_type": type(command).__name__, "body": command.model_dump(mode="json")}
        return sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def _lock(self, household_id, *, read=False):
        # DB triggers use the same household fence. Lot row writes still protect stale RR writers.
        fn = "pg_advisory_xact_lock_shared" if read else "pg_advisory_xact_lock"
        self.session.execute(
            text(f"SELECT {fn}(hashtextextended(:key,0))"),
            {"key": "inventory.household:" + str(household_id)},
        )

    def _retry(self, model, command):
        self._lock(command.household_id)
        row = self.session.scalar(
            select(model).where(
                model.household_id == command.household_id,
                model.source_system == command.evidence.source_system,
                model.idempotency_key == command.idempotency_key,
            )
        )
        if row is not None and row.command_fingerprint != self._fingerprint(command):
            raise ValueError("Idempotency key already used for different command content")
        return row

    def _fields(self, command):
        evidence = command.evidence.model_dump(exclude={"contract_version"})
        evidence["source_kind"] = evidence.pop("kind")
        return dict(
            id=uuid4(),
            household_id=command.household_id,
            lot_id=command.lot_id,
            occurred_at=command.occurred_at,
            idempotency_key=command.idempotency_key,
            command_fingerprint=self._fingerprint(command),
            phase=20,
            reason=command.reason,
            **evidence,
        )

    def _movement(self, command, kind):
        existing = self._retry(m.InventoryMovement, command)
        if existing is not None:
            return self._movement_fact(existing)
        quantity = getattr(command, "quantity", None)
        if quantity is None:
            lot = self.session.scalar(
                select(m.InventoryLot).where(
                    m.InventoryLot.id == command.lot_id,
                    m.InventoryLot.household_id == command.household_id,
                )
            )
            if lot is None:
                raise ValueError("Unknown household lot")
            quantity = Quantity(amount=0, basis=lot.basis, item_ref=lot.item_ref)
        row = m.InventoryMovement(
            **self._fields(command),
            movement_type=kind,
            amount=quantity.amount,
            basis=quantity.basis,
            item_ref=quantity.item_ref,
            correction_of=getattr(command, "correction_of", None),
        )
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return self._movement_fact(row)

    def acquire(self, command: c.AcquireInventoryCommand) -> c.InventoryMovement:
        existing = self._retry(m.InventoryMovement, command)
        if existing is not None:
            return self._movement_fact(existing)
        mapping = (
            read_inventory_mapping(self.session, command.retail_mapping_id)
            if command.retail_mapping_id is not None
            else None
        )
        self.session.add(
            m.InventoryLot(
                id=command.lot_id,
                household_id=command.household_id,
                ingredient_id=command.ingredient_id,
                asset_type=command.asset_type,
                acquired_amount=command.quantity.amount,
                basis=command.quantity.basis,
                item_ref=command.quantity.item_ref,
                acquired_at=command.occurred_at,
                usable_until=command.usable_until,
                observation_confidence=command.observation_confidence,
                serving_definition=command.serving_definition,
                retail_mapping_id=command.retail_mapping_id,
                retail_product_id=mapping.retail_product_id if mapping is not None else None,
            )
        )
        self.session.flush()
        return self._movement(command, "ACQUIRE")

    def consume(self, command: c.ConsumeInventoryCommand) -> c.InventoryMovement:
        return self._movement(command, "CONSUME")

    def discard(self, command: c.DiscardInventoryCommand) -> c.InventoryMovement:
        return self._movement(command, "DISCARD")

    def reconcile(self, command: c.ReconcileInventoryCommand) -> c.InventoryMovement:
        return self._movement(command, "RECONCILE_" + command.direction)

    def expire(self, command: c.ExpireInventoryCommand) -> c.InventoryMovement:
        return self._movement(command, "EXPIRE")

    def reserve(self, command: c.ReserveInventoryCommand) -> c.InventoryReservation:
        existing = self._retry(m.InventoryReservation, command)
        if existing is not None:
            return self._reservation_fact(existing)
        row = m.InventoryReservation(
            **(self._fields(command) | {"id": command.reservation_id}),
            basis=command.quantity.basis,
            item_ref=command.quantity.item_ref,
            amount=command.quantity.amount,
            purpose=command.purpose,
        )
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return self._reservation_fact(row)

    def release(self, command: c.ReleaseReservationCommand) -> c.InventoryReservationRelease:
        existing = self._retry(m.InventoryReservationRelease, command)
        if existing is not None:
            return self._release_fact(existing)
        row = m.InventoryReservationRelease(
            **self._fields(command),
            reservation_id=command.reservation_id,
        )
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return self._release_fact(row)

    @staticmethod
    def _common(row):
        return dict(
            id=row.id,
            household_id=row.household_id,
            lot_id=row.lot_id,
            occurred_at=row.occurred_at,
            recorded_at=row.recorded_at,
            ledger_sequence=row.ledger_sequence,
            phase=row.phase,
            idempotency_key=row.idempotency_key,
            command_fingerprint=row.command_fingerprint,
            reason=row.reason,
            evidence=c.PhysicalEvidence(
                kind=row.source_kind,
                source_system=row.source_system,
                external_record_id=row.external_record_id,
                source_version=row.source_version,
                confirmed_by_user_id=row.confirmed_by_user_id,
                confirmation=row.confirmation,
            ),
        )

    def _movement_fact(self, row):
        return c.InventoryMovement(
            **self._common(row),
            movement_type=row.movement_type,
            correction_of=row.correction_of,
            quantity=Quantity(amount=row.amount, basis=row.basis, item_ref=row.item_ref),
        )

    def _reservation_fact(self, row):
        return c.InventoryReservation(
            **self._common(row),
            purpose=row.purpose,
            quantity=Quantity(amount=row.amount, basis=row.basis, item_ref=row.item_ref),
        )

    def _release_fact(self, row):
        return c.InventoryReservationRelease(**self._common(row), reservation_id=row.reservation_id)

    def snapshot(
        self, household_id: UUID, *, as_of: datetime | None = None
    ) -> c.PhysicalInventorySnapshot:
        """Coherent read: DB writers take exclusive household fence; readers share it.

        Use a fresh READ COMMITTED transaction or stable REPEATABLE READ snapshot.
        as_of is an effective-time cutoff over recorded confirmed facts, never a projection.
        """
        self._lock(household_id, read=True)
        now = self.session.scalar(text("SELECT clock_timestamp()"))
        as_of = now if as_of is None else as_of
        if as_of.tzinfo is None or as_of > now:
            raise ValueError("Snapshot requires nonfuture aware effective cutoff")
        lots = []
        for row in self.session.scalars(
            select(m.InventoryLot)
            .where(
                m.InventoryLot.household_id == household_id,
                m.InventoryLot.acquired_at <= as_of,
            )
            .order_by(m.InventoryLot.id)
        ):
            lots.append(
                c.InventoryLot(
                    id=row.id,
                    household_id=row.household_id,
                    ingredient_id=row.ingredient_id,
                    asset_type=row.asset_type,
                    acquired_at=row.acquired_at,
                    created_at=row.created_at,
                    acquired_quantity=Quantity(
                        amount=row.acquired_amount, basis=row.basis, item_ref=row.item_ref
                    ),
                    usable_until=row.usable_until,
                    observation_confidence=row.observation_confidence,
                    serving_definition=row.serving_definition,
                    retail_mapping=(
                        read_inventory_mapping(self.session, row.retail_mapping_id)
                        if row.retail_mapping_id is not None
                        else None
                    ),
                )
            )

        def events(model, builder):
            return tuple(
                builder(row)
                for row in self.session.scalars(
                    select(model)
                    .where(
                        model.household_id == household_id,
                        model.occurred_at <= as_of,
                    )
                    .order_by(model.occurred_at, model.phase, model.ledger_sequence)
                )
            )

        movements = events(m.InventoryMovement, self._movement_fact)
        reservations = events(m.InventoryReservation, self._reservation_fact)
        releases = events(m.InventoryReservationRelease, self._release_fact)
        released = {r.reservation_id for r in releases}
        positions = []
        with localcontext() as ctx:
            ctx.prec = 160
            for lot in lots:
                history = [e for e in movements if e.lot_id == lot.id]
                total = sum(
                    (
                        e.quantity.amount
                        * (
                            1
                            if e.movement_type in {"ACQUIRE", "RECONCILE_INCREASE"}
                            else 0
                            if e.movement_type == "EXPIRE"
                            else -1
                        )
                        for e in history
                    ),
                    Decimal(0),
                )
                reserved = sum(
                    (
                        r.quantity.amount
                        for r in reservations
                        if r.lot_id == lot.id and r.id not in released
                    ),
                    Decimal(0),
                )
                state = "ACTIVE"
                if total == 0:
                    state = "DISCARDED" if history[-1].movement_type == "DISCARD" else "DEPLETED"
                elif (
                    any(e.movement_type == "EXPIRE" for e in history)
                    or lot.usable_until is not None
                    and as_of >= lot.usable_until
                ):
                    state = "EXPIRED"
                positions.append(
                    c.InventoryPosition(
                        lot_id=lot.id,
                        remaining=Quantity(
                            amount=total,
                            basis=lot.acquired_quantity.basis,
                            item_ref=lot.acquired_quantity.item_ref,
                        ),
                        reserved=Quantity(
                            amount=reserved,
                            basis=lot.acquired_quantity.basis,
                            item_ref=lot.acquired_quantity.item_ref,
                        ),
                        lifecycle_state=state,
                    )
                )
        return c.PhysicalInventorySnapshot(
            household_id=household_id,
            as_of=as_of.astimezone(UTC),
            lots=tuple(lots),
            movements=movements,
            reservations=reservations,
            releases=releases,
            positions=tuple(positions),
        )
