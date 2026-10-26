"""Registered source relations; all mutations go through protected PostgreSQL functions."""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)

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
    "reference_prior_providers",
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
    "reference_prior_principals",
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
    "reference_prior_frontiers",
    Base.metadata,
    Column(
        "provider_id",
        Uuid,
        ForeignKey("reference_prior_providers.id", ondelete="RESTRICT"),
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
    "reference_prior_streams",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "provider_id",
        Uuid,
        ForeignKey("reference_prior_providers.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("target_kind", String(20), nullable=False),
    Column("ingredient_id", Uuid, ForeignKey("ingredients.id", ondelete="RESTRICT")),
    Column("recipe_id", Uuid, ForeignKey("recipes.id", ondelete="RESTRICT")),
    Column("feature_term_id", Uuid),
    Column("head_id", Uuid, nullable=False),
    Column("head_revision", Integer, nullable=False),
    UniqueConstraint("id", "provider_id"),
    ForeignKeyConstraint(
        ["feature_term_id", "target_kind"],
        ["affinity_feature_terms.id", "affinity_feature_terms.kind"],
        ondelete="RESTRICT",
    ),
    CheckConstraint(
        "(target_kind='INGREDIENT' AND ingredient_id IS NOT NULL AND recipe_id IS NULL "
        "AND feature_term_id IS NULL) OR (target_kind='DIRECT_RECIPE' AND recipe_id IS NOT NULL "
        "AND ingredient_id IS NULL AND feature_term_id IS NULL) OR "
        "(target_kind IN ('PROTEIN','METHOD','FLAVOR') AND feature_term_id IS NOT NULL "
        "AND ingredient_id IS NULL AND recipe_id IS NULL)",
        name="typed_target",
    ),
    CheckConstraint("head_revision>=0", name="head_revision"),
)
for kind, column in (
    ("INGREDIENT", "ingredient_id"),
    ("DIRECT_RECIPE", "recipe_id"),
    ("PROTEIN", "feature_term_id"),
    ("METHOD", "feature_term_id"),
    ("FLAVOR", "feature_term_id"),
):
    Index(
        f"uq_prior_stream_{kind.lower()}",
        streams.c.provider_id,
        streams.c[column],
        unique=True,
        postgresql_where=text(f"target_kind='{kind}'"),
    )

authority = Table(
    "reference_prior_authority",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "provider_id",
        Uuid,
        ForeignKey("reference_prior_providers.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "principal_id",
        Uuid,
        ForeignKey("reference_prior_principals.id", ondelete="RESTRICT"),
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
    "reference_prior_revisions",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column("stream_id", Uuid, nullable=False),
    Column("provider_id", Uuid, nullable=False),
    Column(
        "principal_id",
        Uuid,
        ForeignKey("reference_prior_principals.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "grant_event_id",
        Uuid,
        ForeignKey("reference_prior_authority.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("operation", String(10), nullable=False),
    Column("numerator", Integer),
    Column("denominator", Integer),
    Column("source_kind", String(30), nullable=False),
    Column("source_system", String(100), nullable=False),
    Column("external_record_id", String(2048), nullable=False),
    Column("source_version", String(200), nullable=False),
    Column("source_uri", String(2048)),
    Column("content_hash", String(64), nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("review_rationale", Text, nullable=False),
    Column("expected_provider_generation", BigInteger, nullable=False),
    Column("expected_revision", Integer, nullable=False),
    Column(
        "predecessor_id",
        Uuid,
        ForeignKey(
            "reference_prior_revisions.id",
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
        ["reference_prior_streams.id", "reference_prior_streams.provider_id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    ),
    ForeignKeyConstraint(
        ["provider_id", "source_system"],
        ["reference_prior_providers.id", "reference_prior_providers.source_system"],
        ondelete="RESTRICT",
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
        "(operation='REPLACE' AND numerator IS NOT NULL AND denominator IS NOT NULL "
        "AND denominator>0 AND "
        "numerator BETWEEN -2147483647 AND 2147483647 AND abs(numerator::bigint)<=denominator "
        "AND gcd(abs(numerator::bigint),denominator::bigint)=1) OR "
        "(operation='RETRACT' AND numerator IS NULL AND denominator IS NULL "
        "AND expected_revision>=0)",
        name="exact_amount",
    ),
    CheckConstraint(
        "source_kind='REVIEWED_REFERENCE' AND isfinite(observed_at) AND "
        "observed_at<=recorded_at AND effective_at=recorded_at",
        name="source_time",
    ),
    CheckConstraint(
        "length(trim(external_record_id))>0 AND length(trim(source_version))>0 AND "
        "external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'",
        name="reference_identity",
    ),
    CheckConstraint(
        "source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' "
        "AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')",
        name="uri",
    ),
    CheckConstraint(
        "content_hash ~ '^[a-f0-9]{64}$' AND command_hash ~ '^[a-f0-9]{64}$' "
        "AND fact_hash ~ '^[a-f0-9]{64}$'",
        name="hashes",
    ),
    CheckConstraint(
        "length(review_rationale) BETWEEN 1 AND 4000 AND review_rationale ~ '[^[:space:]]'",
        name="rationale",
    ),
    identifier("idempotency_key"),
    identifier("source_system"),
)

mutations = Table(
    "reference_prior_mutations",
    Base.metadata,
    Column(
        "provider_id",
        Uuid,
        ForeignKey("reference_prior_providers.id", ondelete="RESTRICT"),
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
            "reference_prior_authority.id",
            "reference_prior_authority.provider_id",
            "reference_prior_authority.mutation_sequence",
        ],
        deferrable=True,
        initially="DEFERRED",
        ondelete="RESTRICT",
    ),
    ForeignKeyConstraint(
        ["publication_id", "provider_id", "mutation_sequence"],
        [
            "reference_prior_revisions.id",
            "reference_prior_revisions.provider_id",
            "reference_prior_revisions.mutation_sequence",
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
    name="fk_reference_prior_stream_head",
    use_alter=True,
    deferrable=True,
    initially="DEFERRED",
    ondelete="RESTRICT",
)


class ReferencePriorProvider(Base):
    __table__ = providers


class ReferencePriorPrincipal(Base):
    __table__ = principals


class ReferencePriorProviderFrontier(Base):
    __table__ = frontiers


class ReferencePriorStream(Base):
    __table__ = streams


class ReferencePriorAuthority(Base):
    __table__ = authority


class ReferencePriorRevision(Base):
    __table__ = revisions


class ReferencePriorMutation(Base):
    __table__ = mutations
