"""Persistence primitives; model registration lives outside shared."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import TypeAdapter
from sqlalchemy import DateTime, MetaData, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.domain.contracts import PersistedDecimal


class StoredNumeric(TypeDecorator):
    """Reject excess scale before PostgreSQL can round a NUMERIC(18,6) bind value."""

    impl = Numeric(18, 6)
    cache_ok = True
    _value_adapter = TypeAdapter(PersistedDecimal)

    def process_bind_param(self, value, dialect):
        return None if value is None else self._value_adapter.validate_python(value)


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
    type_annotation_map = {Decimal: StoredNumeric(), datetime: DateTime(timezone=True)}


class IdentityMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ProvenanceMixin:
    source_kind: Mapped[str] = mapped_column(String(30))
    source_system: Mapped[str] = mapped_column(String(100))
    external_record_id: Mapped[str] = mapped_column(String(2048))
    source_version: Mapped[str] = mapped_column(String(200))
    source_uri: Mapped[str | None] = mapped_column(String(2048))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    observed_at: Mapped[datetime]
