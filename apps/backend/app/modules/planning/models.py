"""Plan persistence. All history immutable; workspace is a guarded head/counter cache."""

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
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.domain.contracts import PersistedDecimal
from app.shared.db import Base


class IntentNumeric(TypeDecorator):
    impl = Numeric()
    cache_ok = True
    adapter = TypeAdapter(PersistedDecimal)

    def process_bind_param(self, value, dialect):
        return None if value is None else self.adapter.validate_python(value)


def ck(expr, name):
    return CheckConstraint(expr, name=name)


def fk(cols, table, targets, **kw):
    return ForeignKeyConstraint(cols, [f"{table}.{c}" for c in targets], ondelete="RESTRICT", **kw)


def proposal_fk():
    return fk(
        ["proposal_id", "household_id", "plan_id"],
        "plan_proposals",
        ["id", "household_id", "plan_id"],
    )


class PlanWorkspace(Base):
    __tablename__ = "plan_workspaces"
    __table_args__ = (
        UniqueConstraint("id", "household_id"),
        fk(["household_id", "tracked_member_id"], "household_members", ["household_id", "id"]),
        fk(["household_id", "created_by_user_id"], "memberships", ["household_id", "user_id"]),
        fk(
            ["id", "household_id", "active_revision_no"],
            "plan_revisions",
            ["plan_id", "household_id", "revision_no"],
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        ck(
            "(state='DRAFT' AND active_revision_no IS NULL) OR "
            "(state='ACTIVE' AND active_revision_no>=0)",
            "state",
        ),
        ck("latest_proposal_no>=-1 AND boundary_version>=0", "counters"),
        ck(
            "isfinite(horizon_start) AND isfinite(horizon_end) AND horizon_start<horizon_end",
            "horizon",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID] = mapped_column(ForeignKey("households.id", ondelete="RESTRICT"))
    tracked_member_id: Mapped[UUID]
    created_by_user_id: Mapped[UUID]
    horizon_start: Mapped[datetime]
    horizon_end: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(server_default=func.clock_timestamp())
    state: Mapped[str] = mapped_column(String(20), server_default="DRAFT")
    active_revision_no: Mapped[int | None]
    latest_proposal_no: Mapped[int] = mapped_column(server_default="-1")
    boundary_version: Mapped[int] = mapped_column(BigInteger, server_default="0")


class PlanProposal(Base):
    __tablename__ = "plan_proposals"
    __table_args__ = (
        ck("graph_version IN ('plan-intent.v1','plan-intent.v2')", "graph_version"),
        UniqueConstraint("id", "household_id", "plan_id"),
        UniqueConstraint("plan_id", "proposal_no"),
        UniqueConstraint("plan_id", "source_system", "idempotency_key"),
        fk(["plan_id", "household_id"], "plan_workspaces", ["id", "household_id"]),
        fk(["household_id", "actor_user_id"], "memberships", ["household_id", "user_id"]),
        fk(
            ["id"],
            "plan_proposal_seals",
            ["proposal_id"],
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
            name="fk_plan_proposal_requires_seal",
        ),
        ck("scope IN ('SINGLE_MEAL','MULTI_MEAL','REMAINING_HORIZON','PROCUREMENT_ONLY')", "scope"),
        ck(
            "proposal_no>=0 AND expected_generation>=-1 AND "
            "(expected_revision IS NULL OR expected_revision>=0)",
            "versions",
        ),
        ck("isfinite(effective_from)", "effective_time"),
        ck(
            "source_system ~ '^[A-Za-z0-9_.:-]+$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$' "
            "AND command_fingerprint ~ '^[a-f0-9]{64}$' AND length(trim(reason))>0",
            "source",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    proposal_no: Mapped[int]
    expected_generation: Mapped[int]
    expected_revision: Mapped[int | None]
    scope: Mapped[str] = mapped_column(String(30))
    effective_from: Mapped[datetime]
    actor_user_id: Mapped[UUID]
    source_system: Mapped[str] = mapped_column(String(100))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    command_fingerprint: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(String(200))
    graph_version: Mapped[str] = mapped_column(String(30), server_default="plan-intent.v1")
    created_at: Mapped[datetime] = mapped_column(server_default=func.clock_timestamp())
    authored_transaction: Mapped[str] = mapped_column(String(100), server_default="")


class PlanProposalSeal(Base):
    __tablename__ = "plan_proposal_seals"
    __table_args__ = (ck("graph_hash ~ '^[a-f0-9]{64}$'", "hash"),)
    proposal_id: Mapped[UUID] = mapped_column(
        ForeignKey("plan_proposals.id", ondelete="RESTRICT"), primary_key=True
    )
    graph_hash: Mapped[str] = mapped_column(String(64), server_default="")


class NodeColumns:
    proposal_id: Mapped[UUID] = mapped_column(primary_key=True)
    node_id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID]
    plan_id: Mapped[UUID]


class PlanMealIntent(NodeColumns, Base):
    __tablename__ = "plan_meal_intents"
    __table_args__ = (
        proposal_fk(),
        ck("meal_kind IN ('HOME','OUTSIDE','SKIP')", "kind"),
        ck("status IN ('PLANNED','RETIRED')", "status"),
        ck("isfinite(scheduled_at)", "time"),
    )
    scheduled_at: Mapped[datetime]
    meal_kind: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))


class PlanMealParticipant(Base):
    __tablename__ = "plan_meal_participants"
    __table_args__ = (
        proposal_fk(),
        fk(["proposal_id", "meal_node_id"], "plan_meal_intents", ["proposal_id", "node_id"]),
        fk(["household_id", "member_id"], "household_members", ["household_id", "id"]),
        ck("nutrition_role IN ('TRACKED','SHARED')", "role"),
        ck(
            "portion_factor>0 AND portion_factor<1000000000000 "
            "AND portion_factor=trunc(portion_factor,6)",
            "portion",
        ),
    )
    proposal_id: Mapped[UUID] = mapped_column(primary_key=True)
    meal_node_id: Mapped[UUID] = mapped_column(primary_key=True)
    member_id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    portion_factor: Mapped[Decimal] = mapped_column(IntentNumeric())
    nutrition_role: Mapped[str] = mapped_column(String(20))


class PlanReservationIntent(NodeColumns, Base):
    __tablename__ = "plan_reservation_intents"
    __table_args__ = (
        proposal_fk(),
        fk(["household_id", "lot_id"], "inventory_lots", ["household_id", "id"]),
        fk(["proposal_id", "meal_node_id"], "plan_meal_intents", ["proposal_id", "node_id"]),
        fk(["proposal_id", "batch_node_id"], "planned_cooking_batches", ["proposal_id", "node_id"]),
        ck("(meal_node_id IS NULL) <> (batch_node_id IS NULL)", "target"),
        ck("amount>0 AND amount<1000000000000 AND amount=trunc(amount,6)", "amount"),
        ck(
            "(basis IN ('COUNT','SERVING') AND item_ref IS NOT NULL "
            "AND item_ref ~ '^[A-Za-z0-9_.:-]+$') OR "
            "(basis IN ('AP_G','EP_RAW_G','COOKED_G') AND item_ref IS NULL)",
            "identity",
        ),
    )
    lot_id: Mapped[UUID]
    meal_node_id: Mapped[UUID | None]
    batch_node_id: Mapped[UUID | None]
    amount: Mapped[Decimal] = mapped_column(IntentNumeric())
    basis: Mapped[str] = mapped_column(String(20))
    item_ref: Mapped[str | None] = mapped_column(String(100))


class PlanValidationAuthorization(Base):
    """Unmintable receipt seam until a real validator authority is installed."""

    __tablename__ = "plan_validation_authorizations"
    __table_args__ = (
        proposal_fk(),
        UniqueConstraint("id", "household_id", "plan_id", "proposal_id"),
        ck(
            "graph_hash ~ '^[a-f0-9]{64}$' AND subject_hash ~ '^[a-f0-9]{64}$' "
            "AND report_digest ~ '^[a-f0-9]{64}$' AND validator_version ~ '^[A-Za-z0-9_.:-]+$'",
            "hashes",
        ),
        ck("inventory_frontier>=0 AND boundary_version>=0", "frontier"),
        ck("isfinite(valid_until) AND valid_until>created_at", "deadline"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    proposal_id: Mapped[UUID]
    graph_hash: Mapped[str] = mapped_column(String(64))
    subject_hash: Mapped[str] = mapped_column(String(64))
    report_digest: Mapped[str] = mapped_column(String(64))
    validator_version: Mapped[str] = mapped_column(String(100))
    inventory_frontier: Mapped[int] = mapped_column(BigInteger)
    boundary_version: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(server_default=func.clock_timestamp())
    valid_until: Mapped[datetime]


class PlanRevision(Base):
    __tablename__ = "plan_revisions"
    __table_args__ = (
        proposal_fk(),
        UniqueConstraint("plan_id", "revision_no"),
        UniqueConstraint("plan_id", "household_id", "revision_no"),
        UniqueConstraint("plan_id", "source_system", "idempotency_key"),
        UniqueConstraint("authorization_id"),
        fk(
            ["authorization_id", "household_id", "plan_id", "proposal_id"],
            "plan_validation_authorizations",
            ["id", "household_id", "plan_id", "proposal_id"],
        ),
        fk(
            ["plan_id", "household_id", "parent_revision_no"],
            "plan_revisions",
            ["plan_id", "household_id", "revision_no"],
        ),
        fk(["household_id", "actor_user_id"], "memberships", ["household_id", "user_id"]),
        ck(
            "(revision_no=0 AND parent_revision_no IS NULL) OR "
            "(revision_no>0 AND parent_revision_no=revision_no-1)",
            "chain",
        ),
        ck(
            "source_system ~ '^[A-Za-z0-9_.:-]+$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$' "
            "AND command_fingerprint ~ '^[a-f0-9]{64}$'",
            "source",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    proposal_id: Mapped[UUID]
    revision_no: Mapped[int]
    parent_revision_no: Mapped[int | None]
    authorization_id: Mapped[UUID]
    actor_user_id: Mapped[UUID]
    source_system: Mapped[str] = mapped_column(String(100))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    command_fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(server_default=func.clock_timestamp())
    authored_transaction: Mapped[str] = mapped_column(String(100), server_default="")


class PlanRevisionReservation(Base):
    __tablename__ = "plan_revision_reservations"
    __table_args__ = (
        fk(
            ["plan_id", "household_id", "revision_no"],
            "plan_revisions",
            ["plan_id", "household_id", "revision_no"],
        ),
        proposal_fk(),
        fk(
            ["proposal_id", "intent_node_id"],
            "plan_reservation_intents",
            ["proposal_id", "node_id"],
        ),
        fk(
            ["household_id", "lot_id", "reservation_id"],
            "inventory_reservations",
            ["household_id", "lot_id", "id"],
        ),
    )
    plan_id: Mapped[UUID] = mapped_column(primary_key=True)
    revision_no: Mapped[int] = mapped_column(primary_key=True)
    intent_node_id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID]
    proposal_id: Mapped[UUID]
    lot_id: Mapped[UUID]
    reservation_id: Mapped[UUID]


class PlanMaterializationLink(Base):
    __tablename__ = "plan_materialization_links"
    __table_args__ = (
        proposal_fk(),
        fk(
            ["plan_id", "household_id", "source_revision_no"],
            "plan_revisions",
            ["plan_id", "household_id", "revision_no"],
        ),
        fk(["proposal_id", "meal_node_id"], "plan_meal_intents", ["proposal_id", "node_id"]),
        fk(["proposal_id", "batch_node_id"], "planned_cooking_batches", ["proposal_id", "node_id"]),
        fk(
            ["proposal_id", "shopping_node_id"],
            "shopping_requirement_intents",
            ["proposal_id", "node_id"],
        ),
        fk(
            ["household_id", "lot_id", "movement_id"],
            "inventory_movements",
            ["household_id", "lot_id", "id"],
        ),
        fk(["household_id", "actor_user_id"], "memberships", ["household_id", "user_id"]),
        UniqueConstraint("movement_id"),
        ck("num_nonnulls(meal_node_id,batch_node_id,shopping_node_id)=1", "target"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    proposal_id: Mapped[UUID]
    source_revision_no: Mapped[int]
    meal_node_id: Mapped[UUID | None]
    batch_node_id: Mapped[UUID | None]
    shopping_node_id: Mapped[UUID | None]
    lot_id: Mapped[UUID]
    movement_id: Mapped[UUID]
    actor_user_id: Mapped[UUID]
    created_at: Mapped[datetime] = mapped_column(server_default=func.clock_timestamp())


TABLES = tuple(
    t.__tablename__
    for t in (
        PlanWorkspace,
        PlanProposal,
        PlanProposalSeal,
        PlanMealIntent,
        PlanMealParticipant,
        PlanReservationIntent,
        PlanValidationAuthorization,
        PlanRevision,
        PlanRevisionReservation,
        PlanMaterializationLink,
    )
)
