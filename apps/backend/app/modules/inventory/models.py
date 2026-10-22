"""Inventory persistence owns physical facts, never planning projections or yields."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.domain.contracts import PersistedDecimal
from app.shared.db import Base


class InventoryNumeric(TypeDecorator):
    impl = Numeric()
    cache_ok = True
    adapter = TypeAdapter(PersistedDecimal)

    def process_bind_param(self, value, dialect):
        return None if value is None else self.adapter.validate_python(value)


def check(sql, name):
    return CheckConstraint(sql, name=name)


def exact(column, *, positive=False):
    return check(
        f"{column} {'>' if positive else '>='} 0 AND {column} < 1000000000000 "
        f"AND {column} = trunc({column},6)",
        f"{column}_exact",
    )


def quantity_identity():
    return check(
        "(basis IN ('COUNT','SERVING') AND item_ref IS NOT NULL "
        "AND item_ref ~ '^[A-Za-z0-9_.:-]+$') OR "
        "(basis IN ('AP_G','EP_RAW_G','COOKED_G') AND item_ref IS NULL)",
        "quantity_identity",
    )


def lot_fk():
    return ForeignKeyConstraint(
        ["household_id", "lot_id"],
        ["inventory_lots.household_id", "inventory_lots.id"],
        ondelete="RESTRICT",
    )


class InventoryLot(Base):
    __tablename__ = "inventory_lots"
    __table_args__ = (
        UniqueConstraint("household_id", "id"),
        ForeignKeyConstraint(
            ["retail_mapping_id", "retail_product_id", "ingredient_id"],
            [
                "ingredient_product_maps.id",
                "ingredient_product_maps.retail_product_id",
                "ingredient_product_maps.ingredient_id",
            ],
            ondelete="RESTRICT",
        ),
        quantity_identity(),
        exact("acquired_amount", positive=True),
        check("observation_confidence IN ('CONFIRMED','STALE','UNKNOWN')", "confidence"),
        check(
            "isfinite(acquired_at) AND isfinite(created_at) AND "
            "(usable_until IS NULL OR (isfinite(usable_until) AND usable_until > acquired_at))",
            "times",
        ),
        check(
            "(asset_type='RAW_INGREDIENT' AND ingredient_id IS NOT NULL "
            "AND basis IN ('AP_G','EP_RAW_G','COUNT') AND serving_definition IS NULL) OR "
            "(asset_type='PREPARED_COMPONENT' AND ingredient_id IS NOT NULL "
            "AND basis='COOKED_G' AND serving_definition IS NULL) OR "
            "(asset_type='COOKED_DISH' AND ingredient_id IS NULL AND basis='SERVING' "
            "AND serving_definition IS NOT NULL AND length(trim(serving_definition))>0)",
            "asset_identity",
        ),
        check(
            "(retail_mapping_id IS NULL AND retail_product_id IS NULL) OR "
            "(retail_mapping_id IS NOT NULL AND retail_product_id IS NOT NULL "
            "AND asset_type='RAW_INGREDIENT' AND basis='AP_G')",
            "retail_origin",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID] = mapped_column(ForeignKey("households.id", ondelete="RESTRICT"))
    ingredient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT")
    )
    asset_type: Mapped[str] = mapped_column(String(30))
    basis: Mapped[str] = mapped_column(String(20))
    item_ref: Mapped[str | None] = mapped_column(String(100))
    acquired_amount: Mapped[Decimal] = mapped_column(InventoryNumeric())
    acquired_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(server_default=func.clock_timestamp())
    usable_until: Mapped[datetime | None]
    observation_confidence: Mapped[str] = mapped_column(String(20))
    serving_definition: Mapped[str | None] = mapped_column(String(200))
    retail_product_id: Mapped[UUID | None]
    retail_mapping_id: Mapped[UUID | None]


class InventoryLotBalance(Base):
    __tablename__ = "inventory_lot_balances"
    __table_args__ = (
        lot_fk(),
        exact("remaining"),
        exact("reserved"),
        check("reserved <= remaining", "reserved_bound"),
        check("lifecycle_state IN ('ACTIVE','DEPLETED','EXPIRED','DISCARDED')", "lifecycle"),
        check("revision > 0 AND last_phase BETWEEN 0 AND 60", "revision"),
    )
    lot_id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID]
    remaining: Mapped[Decimal] = mapped_column(InventoryNumeric())
    reserved: Mapped[Decimal] = mapped_column(InventoryNumeric())
    lifecycle_state: Mapped[str] = mapped_column(String(20))
    revision: Mapped[int] = mapped_column(BigInteger)
    last_occurred_at: Mapped[datetime]
    last_phase: Mapped[int]


class EventColumns:
    id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID]
    lot_id: Mapped[UUID]
    occurred_at: Mapped[datetime]
    recorded_at: Mapped[datetime] = mapped_column(server_default=func.clock_timestamp())
    ledger_sequence: Mapped[int] = mapped_column(
        BigInteger, server_default=text("nextval('inventory_ledger_sequence')")
    )
    phase: Mapped[int]
    idempotency_key: Mapped[str] = mapped_column(String(100))
    command_fingerprint: Mapped[str] = mapped_column(String(64))
    source_kind: Mapped[str] = mapped_column(String(20))
    source_system: Mapped[str] = mapped_column(String(100))
    external_record_id: Mapped[str] = mapped_column(String(2048))
    source_version: Mapped[str] = mapped_column(String(200))
    confirmed_by_user_id: Mapped[UUID]
    confirmation: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(String(200))


def event_checks():
    return (
        lot_fk(),
        ForeignKeyConstraint(
            ["household_id", "confirmed_by_user_id"],
            ["memberships.household_id", "memberships.user_id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint("household_id", "source_system", "idempotency_key"),
        UniqueConstraint("household_id", "source_system", "external_record_id", "source_version"),
        UniqueConstraint("ledger_sequence"),
        check(
            "source_kind IN ('USER','RECEIPT','BARCODE','EXECUTION') AND confirmation='EXPLICIT'",
            "explicit_evidence",
        ),
        check(
            "source_system ~ '^[A-Za-z0-9_.:-]+$' "
            "AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$' "
            "AND command_fingerprint ~ '^[a-f0-9]{64}$'",
            "identifiers",
        ),
        check(
            "length(trim(external_record_id))>0 AND external_record_id !~ '[[:cntrl:]]' "
            "AND length(trim(source_version))>0 AND source_version !~ '[[:cntrl:]]' "
            "AND length(trim(reason))>0",
            "source_identity",
        ),
        check(
            "isfinite(occurred_at) AND isfinite(recorded_at) "
            "AND occurred_at <= recorded_at AND ledger_sequence>0 "
            "AND phase IN (10,20,30,40,50,60)",
            "event_order",
        ),
    )


class InventoryMovement(EventColumns, Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        *event_checks(),
        quantity_identity(),
        exact("amount"),
        UniqueConstraint("household_id", "lot_id", "id"),
        ForeignKeyConstraint(
            ["household_id", "lot_id", "correction_of"],
            [
                "inventory_movements.household_id",
                "inventory_movements.lot_id",
                "inventory_movements.id",
            ],
            ondelete="RESTRICT",
        ),
        check(
            "(movement_type='EXPIRE' AND amount=0) OR "
            "(movement_type IN ('ACQUIRE','CONSUME','DISCARD',"
            "'RECONCILE_INCREASE','RECONCILE_DECREASE') AND amount>0)",
            "movement_type",
        ),
        check(
            "correction_of IS NULL OR movement_type IN ('RECONCILE_INCREASE','RECONCILE_DECREASE')",
            "correction",
        ),
    )
    movement_type: Mapped[str] = mapped_column(String(30))
    basis: Mapped[str] = mapped_column(String(20))
    item_ref: Mapped[str | None] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(InventoryNumeric())
    correction_of: Mapped[UUID | None]


class InventoryReservation(EventColumns, Base):
    __tablename__ = "inventory_reservations"
    __table_args__ = (
        *event_checks(),
        quantity_identity(),
        exact("amount", positive=True),
        UniqueConstraint("household_id", "lot_id", "id"),
        check("length(trim(purpose))>0", "purpose"),
    )
    basis: Mapped[str] = mapped_column(String(20))
    item_ref: Mapped[str | None] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(InventoryNumeric())
    purpose: Mapped[str] = mapped_column(String(200))


class InventoryReservationRelease(EventColumns, Base):
    __tablename__ = "inventory_reservation_releases"
    __table_args__ = (
        *event_checks(),
        UniqueConstraint("reservation_id"),
        ForeignKeyConstraint(
            ["household_id", "lot_id", "reservation_id"],
            [
                "inventory_reservations.household_id",
                "inventory_reservations.lot_id",
                "inventory_reservations.id",
            ],
            ondelete="RESTRICT",
        ),
    )
    reservation_id: Mapped[UUID]


TABLES = (
    "inventory_lots",
    "inventory_lot_balances",
    "inventory_movements",
    "inventory_reservations",
    "inventory_reservation_releases",
)
