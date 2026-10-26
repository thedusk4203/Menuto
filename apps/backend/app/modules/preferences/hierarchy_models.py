"""Registered source relations; all mutations go through protected PostgreSQL functions."""

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.shared.db import Base


def audit():
    return [
        Column("actor_database_oid", BigInteger, nullable=False),
        Column("actor_database_name", String(63), nullable=False),
        Column("actor_role_oid", BigInteger, nullable=False),
        Column("actor_role_name", String(63), nullable=False),
        Column("actor_authentication_method", String(30), nullable=False),
        Column("actor_authenticated_identity", String(63), nullable=False),
        Column("recorded_at", DateTime(timezone=True), nullable=False),
        CheckConstraint(
            "actor_authentication_method='scram-sha-256' AND "
            "actor_authenticated_identity=actor_role_name",
            name="authenticated_actor",
        ),
        CheckConstraint("isfinite(recorded_at)", name="recorded_time"),
    ]


def identifier(column):
    return CheckConstraint(f"{column} ~ '^[A-Za-z0-9_.:-]+$'", name=column + "_identifier")


providers = Table(
    "hierarchy_source_providers",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column("code", String(100), nullable=False),
    Column("version", String(100), nullable=False),
    Column("source_system", String(100), nullable=False),
    Column("remit", Text, nullable=False),
    Column("idempotency_key", String(100), nullable=False),
    Column("command_hash", String(64), nullable=False),
    *audit(),
    UniqueConstraint("code", "version"),
    UniqueConstraint("actor_role_oid", "idempotency_key"),
    UniqueConstraint("id", "source_system"),
    identifier("code"),
    identifier("version"),
    identifier("source_system"),
    identifier("idempotency_key"),
    CheckConstraint("length(remit) BETWEEN 1 AND 4000 AND remit ~ '[^[:space:]]'", name="remit"),
    CheckConstraint("command_hash ~ '^[a-f0-9]{64}$'", name="command_hash"),
)

principals = Table(
    "hierarchy_source_principals",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column("database_oid", BigInteger, nullable=False),
    Column("database_name", String(63), nullable=False),
    Column("role_oid", BigInteger, nullable=False),
    Column("role_name", String(63), nullable=False),
    Column("idempotency_key", String(100), nullable=False),
    Column("command_hash", String(64), nullable=False),
    *audit(),
    UniqueConstraint("database_oid", "role_oid", "role_name"),
    UniqueConstraint("actor_role_oid", "idempotency_key"),
    identifier("idempotency_key"),
    CheckConstraint(
        "database_oid BETWEEN 1 AND 4294967295 AND role_oid BETWEEN 1 AND 4294967295", name="oids"
    ),
    CheckConstraint(
        "database_oid=actor_database_oid AND database_name=actor_database_name",
        name="database_binding",
    ),
    CheckConstraint("command_hash ~ '^[a-f0-9]{64}$'", name="command_hash"),
)

frontiers = Table(
    "hierarchy_source_frontiers",
    Base.metadata,
    Column(
        "provider_id",
        Uuid,
        ForeignKey("hierarchy_source_providers.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
    Column("source_generation", BigInteger, nullable=False),
    Column("authority_generation", BigInteger, nullable=False),
    Column("mutation_generation", BigInteger, nullable=False),
    Column("source_head_id", Uuid),
    Column("authority_head_id", Uuid),
    Column("mutation_head_hash", String(64)),
    CheckConstraint(
        "source_generation>=0 AND authority_generation>=0 AND mutation_generation>=0 "
        "AND mutation_generation=source_generation+authority_generation",
        name="generations",
    ),
    CheckConstraint(
        "(source_generation=0)=(source_head_id IS NULL) AND "
        "(authority_generation=0)=(authority_head_id IS NULL) AND "
        "(mutation_generation=0)=(mutation_head_hash IS NULL)",
        name="heads",
    ),
)

streams = Table(
    "hierarchy_source_streams",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "provider_id",
        Uuid,
        ForeignKey("hierarchy_source_providers.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("kind", String(20), nullable=False),
    Column("policy_id", Uuid, nullable=False),
    Column("identity", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("stream_key", String(64), nullable=False),
    Column("head_id", Uuid, nullable=False),
    Column("head_revision", Integer, nullable=False),
    UniqueConstraint("id", "provider_id"),
    UniqueConstraint("provider_id", "stream_key"),
    CheckConstraint("kind IN ('POLICY','RELATION') AND head_revision>=0", name="kind_revision"),
)

authority = Table(
    "hierarchy_source_authority",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "provider_id",
        Uuid,
        ForeignKey("hierarchy_source_providers.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "principal_id",
        Uuid,
        ForeignKey("hierarchy_source_principals.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("capability", String(30), nullable=False),
    Column("action", String(10), nullable=False),
    Column("expected_authority_generation", BigInteger, nullable=False),
    Column("reason", Text, nullable=False),
    Column("idempotency_key", String(100), nullable=False),
    Column("authority_sequence", BigInteger, nullable=False),
    Column("mutation_sequence", BigInteger, nullable=False),
    Column("command_hash", String(64), nullable=False),
    Column("fact_hash", String(64), nullable=False),
    *audit(),
    UniqueConstraint("provider_id", "authority_sequence"),
    UniqueConstraint("provider_id", "actor_role_oid", "idempotency_key"),
    UniqueConstraint("id", "provider_id", "mutation_sequence"),
    CheckConstraint("capability IN ('REVIEW_PUBLISH','RETRACT','CAPTURE')", name="capability"),
    CheckConstraint("action IN ('GRANT','REVOKE')", name="action"),
    CheckConstraint(
        "expected_authority_generation>=0 AND "
        "authority_sequence=expected_authority_generation+1 AND mutation_sequence>0",
        name="sequences",
    ),
    CheckConstraint("length(reason) BETWEEN 1 AND 4000 AND reason ~ '[^[:space:]]'", name="reason"),
    CheckConstraint(
        "command_hash ~ '^[a-f0-9]{64}$' AND fact_hash ~ '^[a-f0-9]{64}$'", name="hashes"
    ),
    identifier("idempotency_key"),
)

revisions = Table(
    "hierarchy_source_revisions",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column("stream_id", Uuid, nullable=False),
    Column("provider_id", Uuid, nullable=False),
    Column(
        "principal_id",
        Uuid,
        ForeignKey("hierarchy_source_principals.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "grant_event_id",
        Uuid,
        ForeignKey("hierarchy_source_authority.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("operation", String(10), nullable=False),
    Column("command", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("owner_pins", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("expected_provider_generation", BigInteger, nullable=False),
    Column("expected_revision", Integer, nullable=False),
    Column(
        "predecessor_id",
        Uuid,
        ForeignKey(
            "hierarchy_source_revisions.id",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
    ),
    Column("idempotency_key", String(100), nullable=False),
    Column("authority_generation", BigInteger, nullable=False),
    Column("revision", Integer, nullable=False),
    Column("source_sequence", BigInteger, nullable=False),
    Column("mutation_sequence", BigInteger, nullable=False),
    Column("effective_at", DateTime(timezone=True), nullable=False),
    Column("command_hash", String(64), nullable=False),
    Column("fact_hash", String(64), nullable=False),
    *audit(),
    ForeignKeyConstraint(
        ["stream_id", "provider_id"],
        ["hierarchy_source_streams.id", "hierarchy_source_streams.provider_id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    ),
    UniqueConstraint("id", "stream_id", "provider_id", "revision"),
    UniqueConstraint("id", "provider_id", "mutation_sequence"),
    UniqueConstraint("provider_id", "source_sequence"),
    UniqueConstraint("stream_id", "revision"),
    UniqueConstraint("provider_id", "principal_id", "idempotency_key"),
    CheckConstraint(
        "expected_provider_generation>=0 AND source_sequence=expected_provider_generation+1 "
        "AND authority_generation>=0 AND mutation_sequence>0 AND revision>=0 "
        "AND revision=expected_revision+1 AND expected_revision>=-1",
        name="sequences",
    ),
    CheckConstraint("(expected_revision=-1)=(predecessor_id IS NULL)", name="predecessor"),
    CheckConstraint(
        "operation IN ('REPLACE','RETRACT') AND effective_at=recorded_at "
        "AND isfinite(effective_at)",
        name="operation_time",
    ),
    CheckConstraint(
        "command_hash ~ '^[a-f0-9]{64}$' AND fact_hash ~ '^[a-f0-9]{64}$'", name="hashes"
    ),
    identifier("idempotency_key"),
)

mutations = Table(
    "hierarchy_source_mutations",
    Base.metadata,
    Column(
        "provider_id",
        Uuid,
        ForeignKey("hierarchy_source_providers.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
    Column("mutation_sequence", BigInteger, primary_key=True),
    Column("kind", String(20), nullable=False),
    Column("authority_event_id", Uuid),
    Column("publication_id", Uuid),
    Column("child_hash", String(64), nullable=False),
    Column("predecessor_hash", String(64)),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    Column("journal_hash", String(64), nullable=False),
    ForeignKeyConstraint(
        ["authority_event_id", "provider_id", "mutation_sequence"],
        [
            "hierarchy_source_authority.id",
            "hierarchy_source_authority.provider_id",
            "hierarchy_source_authority.mutation_sequence",
        ],
        deferrable=True,
        initially="DEFERRED",
        ondelete="RESTRICT",
    ),
    ForeignKeyConstraint(
        ["publication_id", "provider_id", "mutation_sequence"],
        [
            "hierarchy_source_revisions.id",
            "hierarchy_source_revisions.provider_id",
            "hierarchy_source_revisions.mutation_sequence",
        ],
        deferrable=True,
        initially="DEFERRED",
        ondelete="RESTRICT",
    ),
    CheckConstraint("mutation_sequence>0 AND isfinite(recorded_at)", name="sequence_time"),
    CheckConstraint(
        "(kind='AUTHORITY' AND authority_event_id IS NOT NULL AND publication_id IS NULL) "
        "OR (kind='PUBLICATION' AND publication_id IS NOT NULL AND authority_event_id IS NULL)",
        name="typed_child",
    ),
    CheckConstraint(
        "child_hash ~ '^[a-f0-9]{64}$' AND journal_hash ~ '^[a-f0-9]{64}$'", name="hashes"
    ),
)
ForeignKeyConstraint(
    [streams.c.head_id, streams.c.id, streams.c.provider_id, streams.c.head_revision],
    [revisions.c.id, revisions.c.stream_id, revisions.c.provider_id, revisions.c.revision],
    name="fk_hierarchy_source_stream_head",
    use_alter=True,
    deferrable=True,
    initially="DEFERRED",
    ondelete="RESTRICT",
)


class HierarchyProvider(Base):
    __table__ = providers


class HierarchyPrincipal(Base):
    __table__ = principals


class HierarchyProviderFrontier(Base):
    __table__ = frontiers


class HierarchyStream(Base):
    __table__ = streams


class HierarchyAuthority(Base):
    __table__ = authority


class HierarchyRevision(Base):
    __table__ = revisions


class HierarchyMutation(Base):
    __table__ = mutations
