"""Persistence primitives; model registration lives outside shared."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, MetaData, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
    type_annotation_map = {Decimal: Numeric(18, 6), datetime: DateTime(timezone=True)}


class IdentityMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ProvenanceMixin:
    source_kind: Mapped[str] = mapped_column(String(30))
    source_ref: Mapped[str] = mapped_column(String(100))
    source_version: Mapped[str] = mapped_column(String(100))
    observed_at: Mapped[datetime]
