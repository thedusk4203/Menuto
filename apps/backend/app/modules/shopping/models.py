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


class ShoppingRequirementIntent(NodeColumns, Base):
    __tablename__ = "shopping_requirement_intents"
    __table_args__ = (
        proposal_fk(),
        ck("status IN ('PLANNED','RETIRED')", "status"),
        ck("isfinite(need_by)", "time"),
        ck("amount>0 AND amount<1000000000000 AND amount=trunc(amount,6)", "amount"),
        ck(
            "(basis='COUNT' AND item_ref IS NOT NULL AND item_ref ~ '^[A-Za-z0-9_.:-]+$') OR "
            "(basis IN ('AP_G','EP_RAW_G','COOKED_G') AND item_ref IS NULL)",
            "basis",
        ),
    )
    ingredient_id: Mapped[UUID] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    amount: Mapped[Decimal] = mapped_column(IntentNumeric())
    basis: Mapped[str] = mapped_column(String(20))
    item_ref: Mapped[str | None] = mapped_column(String(100))
    need_by: Mapped[datetime]
    status: Mapped[str] = mapped_column(String(20))


TABLES = ("shopping_requirement_intents",)
