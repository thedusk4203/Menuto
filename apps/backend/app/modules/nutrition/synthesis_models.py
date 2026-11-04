"""Dedicated synthesis authority; immutable content and append-only publication journals."""

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Sequence,
    String,
    Table,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.shared.db import Base

J = JSON().with_variant(JSONB(), "postgresql")
recorded_order_sequence = Sequence("nutrition_synthesis_recorded_order", metadata=Base.metadata)


def fact_columns():
    return [
        Column("id", Uuid, primary_key=True),
        Column("command", J, nullable=False),
        Column("administrator", J, nullable=False),
        Column("recorded_at", DateTime(timezone=True), nullable=False),
        Column("recorded_order", BigInteger, nullable=False, unique=True),
        Column("command_hash", String(64), nullable=False),
        Column("actor_role_oid", BigInteger, nullable=False),
        Column("idempotency_key", String(100), nullable=False),
        UniqueConstraint("actor_role_oid", "idempotency_key"),
        CheckConstraint("isfinite(recorded_at)", name="recorded_time"),
        CheckConstraint("recorded_order>0", name="recorded_order"),
    ]


providers = Table(
    "nutrition_synthesis_providers",
    Base.metadata,
    *fact_columns(),
    Column("provider_id", Uuid, nullable=False),
    Column("generation", BigInteger, nullable=False),
    Column("previous_id", Uuid),
    UniqueConstraint("provider_id", "generation"),
    CheckConstraint("generation>0 AND (generation=1)=(previous_id IS NULL)", name="generation"),
)

principals = Table(
    "nutrition_synthesis_principals",
    Base.metadata,
    *fact_columns(),
    Column("database_oid", BigInteger, nullable=False),
    Column("database_name", String(63), nullable=False),
    Column("role_oid", BigInteger, nullable=False),
    Column("role_name", String(63), nullable=False),
    Column("verified_human_id", Uuid),
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="RESTRICT")),
    Column("service_id", String(100)),
    Column(
        "enrollment_root_id",
        Uuid,
        ForeignKey("nutrition_synthesis_principals.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
    ),
    Column("generation", BigInteger, nullable=False),
    Column("previous_id", Uuid, ForeignKey("nutrition_synthesis_principals.id")),
    UniqueConstraint("enrollment_root_id", "generation"),
    CheckConstraint("generation>0 AND (generation=1)=(previous_id IS NULL)", name="generation"),
    CheckConstraint("(verified_human_id IS NULL)<>(service_id IS NULL)", name="identity_class"),
    CheckConstraint("service_id IS NULL OR user_id IS NULL", name="service_not_user"),
)

principal_frontiers = Table(
    "nutrition_synthesis_principal_frontiers",
    Base.metadata,
    Column(
        "enrollment_root_id",
        Uuid,
        ForeignKey("nutrition_synthesis_principals.id"),
        primary_key=True,
    ),
    Column("revision", BigInteger, nullable=False),
    Column("head_id", Uuid, ForeignKey("nutrition_synthesis_principals.id"), nullable=False),
    Column("head_hash", String(64), nullable=False),
    Column("lock_version", BigInteger, nullable=False),
    CheckConstraint("revision>0 AND lock_version>=0", name="frontier"),
)

grants = Table(
    "nutrition_synthesis_grants",
    Base.metadata,
    *fact_columns(),
    Column("provider_id", Uuid, nullable=False),
    Column("family_id", String(100), nullable=False),
    Column("principal_id", Uuid, ForeignKey("nutrition_synthesis_principals.id"), nullable=False),
    Column("capability", String(40), nullable=False),
    Column("generation", BigInteger, nullable=False),
    Column("previous_id", Uuid),
    UniqueConstraint("provider_id", "family_id", "principal_id", "capability", "generation"),
    CheckConstraint("generation>0 AND (generation=1)=(previous_id IS NULL)", name="generation"),
)

streams = Table(
    "nutrition_synthesis_streams",
    Base.metadata,
    Column("provider_id", Uuid, primary_key=True),
    Column("family_id", String(100), primary_key=True),
    Column("revision", BigInteger, nullable=False),
    Column("head_id", Uuid),
    Column("head_hash", String(64)),
    CheckConstraint(
        "revision>=0 AND (family_id='__AUTHORITY_LOCK__' OR "
        "((revision=0)=(head_id IS NULL) AND "
        "(head_id IS NULL)=(head_hash IS NULL)))",
        name="frontier",
    ),
)

receipts = Table(
    "nutrition_synthesis_receipts",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column("provider_id", Uuid, nullable=False),
    Column("family_id", String(100), nullable=False),
    Column("sequence", BigInteger, nullable=False),
    Column("principal_id", Uuid, ForeignKey("nutrition_synthesis_principals.id"), nullable=False),
    Column("grant_id", Uuid, ForeignKey("nutrition_synthesis_grants.id"), nullable=False),
    Column("actor", J, nullable=False),
    Column("command", J, nullable=False),
    Column("previous_id", Uuid),
    Column("previous_hash", String(64)),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    Column("recorded_order", BigInteger, nullable=False, unique=True),
    Column("command_hash", String(64), nullable=False),
    Column("event_hash", String(64), nullable=False),
    Column("idempotency_key", String(100), nullable=False),
    UniqueConstraint("principal_id", "idempotency_key"),
    UniqueConstraint("provider_id", "family_id", "sequence"),
    CheckConstraint(
        "sequence>0 AND (sequence=1)=(previous_id IS NULL) "
        "AND (previous_id IS NULL)=(previous_hash IS NULL)",
        name="lineage",
    ),
    CheckConstraint("isfinite(recorded_at)", name="recorded_time"),
    CheckConstraint("recorded_order>0", name="recorded_order"),
)

drafts = Table(
    "nutrition_synthesis_drafts",
    Base.metadata,
    Column("id", Uuid, ForeignKey("nutrition_synthesis_receipts.id"), primary_key=True),
    Column("revision_id", Uuid, nullable=False, unique=True),
    Column("body_fingerprint", String(64), nullable=False),
    Column("evidence_fingerprint", String(64), nullable=False),
    Column("body", J, nullable=False),
)

reviews = Table(
    "nutrition_synthesis_reviews",
    Base.metadata,
    Column("id", Uuid, ForeignKey("nutrition_synthesis_receipts.id"), primary_key=True),
    Column(
        "revision_id", Uuid, ForeignKey("nutrition_synthesis_drafts.revision_id"), nullable=False
    ),
    Column("body", J, nullable=False),
)

publications = Table(
    "nutrition_synthesis_publications",
    Base.metadata,
    Column("id", Uuid, ForeignKey("nutrition_synthesis_receipts.id"), primary_key=True),
    Column(
        "revision_id", Uuid, ForeignKey("nutrition_synthesis_drafts.revision_id"), nullable=False
    ),
    Column("body", J, nullable=False),
)

evidence = Table(
    "nutrition_synthesis_evidence",
    Base.metadata,
    Column("evidence_id", String(100), primary_key=True),
    Column("body", J, nullable=False),
    Column("fingerprint", String(64), nullable=False),
)
