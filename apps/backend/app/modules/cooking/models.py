from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, Numeric, String
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


def fk(cols, table, targets):
    return ForeignKeyConstraint(cols, [f"{table}.{c}" for c in targets], ondelete="RESTRICT")


def proposal_fk():
    return fk(
        ["proposal_id", "household_id", "plan_id"],
        "plan_proposals",
        ["id", "household_id", "plan_id"],
    )


class NodeColumns:
    proposal_id: Mapped[UUID] = mapped_column(primary_key=True)
    node_id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID]
    plan_id: Mapped[UUID]


class PlannedCookingBatch(NodeColumns, Base):
    __tablename__ = "planned_cooking_batches"
    __table_args__ = (
        proposal_fk(),
        fk(["tier_id", "recipe_version_id"], "recipe_portion_tiers", ["id", "recipe_version_id"]),
        ck("status IN ('PLANNED','RETIRED')", "status"),
        ck("isfinite(planned_at)", "time"),
        ck(
            "planned_servings>0 AND planned_servings<1000000000000 "
            "AND planned_servings=trunc(planned_servings,6)",
            "servings",
        ),
    )
    recipe_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("recipe_versions.id", ondelete="RESTRICT")
    )
    tier_id: Mapped[UUID]
    planned_servings: Mapped[Decimal] = mapped_column(IntentNumeric())
    planned_at: Mapped[datetime]
    status: Mapped[str] = mapped_column(String(20))


class PlannedBatchAllocation(NodeColumns, Base):
    __tablename__ = "planned_batch_allocations"
    __table_args__ = (
        proposal_fk(),
        fk(["proposal_id", "batch_node_id"], "planned_cooking_batches", ["proposal_id", "node_id"]),
        fk(["proposal_id", "meal_node_id"], "plan_meal_intents", ["proposal_id", "node_id"]),
        ck("status IN ('PLANNED','RETIRED')", "status"),
        ck("servings>0 AND servings<1000000000000 AND servings=trunc(servings,6)", "servings"),
    )
    batch_node_id: Mapped[UUID]
    meal_node_id: Mapped[UUID]
    servings: Mapped[Decimal] = mapped_column(IntentNumeric())
    status: Mapped[str] = mapped_column(String(20))


TABLES = ("planned_cooking_batches", "planned_batch_allocations")
