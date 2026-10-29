"""Nutrition-owned durable sources. Runtime actors have no direct DML interface."""

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Sequence,
    String,
    Table,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.shared.db import Base

J = JSON().with_variant(JSONB(), "postgresql")


def ref(name, target, *, nullable=False):
    return Column(
        name,
        Uuid,
        ForeignKey(
            target,
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            use_alter=target.startswith("nutrition_"),
        ),
        nullable=nullable,
    )


def subject():
    return [
        Column("household_id", Uuid, nullable=False),
        Column("member_id", Uuid, nullable=False),
        ForeignKeyConstraint(
            ["household_id", "member_id"],
            ["household_members.household_id", "household_members.id"],
            ondelete="RESTRICT",
        ),
    ]


def interval():
    return [
        Column("effective_from", DateTime(timezone=True), nullable=False),
        Column("effective_until", DateTime(timezone=True), nullable=False),
        CheckConstraint(
            "isfinite(effective_from) AND isfinite(effective_until) "
            "AND effective_from<effective_until",
            name="effective_interval",
        ),
    ]


providers = Table(
    "nutrition_source_providers",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    ref("provider_id", "nutrition_source_providers.id"),
    ref("previous_id", "nutrition_source_providers.id", nullable=True),
    Column("generation", BigInteger, nullable=False),
    Column("database_oid", BigInteger, nullable=False),
    Column("database_name", String(63), nullable=False),
    Column("actor_role_oid", BigInteger, nullable=False),
    Column("code", String(100), nullable=False),
    Column("version", String(100), nullable=False),
    Column("environment", String(30), nullable=False),
    Column("command", J, nullable=False),
    Column("administrator", J, nullable=False),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    Column("command_hash", String(64), nullable=False),
    Column("idempotency_key", String(100), nullable=False),
    UniqueConstraint("provider_id", "generation"),
    UniqueConstraint("database_oid", "actor_role_oid", "idempotency_key"),
    CheckConstraint("generation>0 AND (generation=1)=(previous_id IS NULL)", name="generation"),
    CheckConstraint("isfinite(recorded_at)", name="recorded_time"),
    CheckConstraint("environment IN ('TEST_ONLY','REVIEWED_PRODUCTION')", name="environment"),
)

Index(
    "uq_nutrition_provider_identity",
    providers.c.code,
    providers.c.version,
    unique=True,
    postgresql_where=providers.c.generation == 1,
)

principals = Table(
    "nutrition_source_principals",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column("database_oid", BigInteger, nullable=False),
    Column("database_name", String(63), nullable=False),
    Column("role_oid", BigInteger, nullable=False),
    Column("role_name", String(63), nullable=False),
    Column("verified_human_id", Uuid),
    ref("user_id", "users.id", nullable=True),
    Column("service_id", String(100)),
    Column("delegation_registrar", Boolean, nullable=False),
    Column("command", J, nullable=False),
    Column("administrator", J, nullable=False),
    Column("actor_role_oid", BigInteger, nullable=False),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    Column("command_hash", String(64), nullable=False),
    Column("idempotency_key", String(100), nullable=False),
    UniqueConstraint("database_oid", "role_oid", "role_name"),
    UniqueConstraint("database_oid", "actor_role_oid", "idempotency_key"),
    CheckConstraint("(verified_human_id IS NULL)<>(service_id IS NULL)", name="identity_class"),
    CheckConstraint(
        "service_id IS NULL OR (user_id IS NULL AND NOT delegation_registrar)",
        name="service_not_author",
    ),
    CheckConstraint("isfinite(recorded_at)", name="recorded_time"),
)

streams = Table(
    "nutrition_source_streams",
    Base.metadata,
    Column("stream_key", String(64), primary_key=True),
    Column("kind", String(20), nullable=False),
    Column("identity", J, nullable=False),
    Column("revision", BigInteger, nullable=False),
    ref("head_id", "nutrition_source_receipts.id", nullable=True),
    Column("head_hash", String(64)),
    CheckConstraint("kind IN ('SOURCE','AUTHORITY','LOCK')", name="kind"),
    CheckConstraint(
        "revision>=0 AND (kind='LOCK' OR ((revision=0)=(head_id IS NULL) "
        "AND (revision=0)=(head_hash IS NULL)))",
        name="frontier",
    ),
)

receipts = Table(
    "nutrition_source_receipts",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column("kind", String(20), nullable=False),
    Column(
        "recorded_order",
        BigInteger,
        Sequence("nutrition_source_recorded_order", metadata=Base.metadata),
        nullable=False,
    ),
    Column(
        "stream_key",
        String(64),
        ForeignKey(
            "nutrition_source_streams.stream_key",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        nullable=False,
    ),
    Column("sequence", BigInteger, nullable=False),
    ref("previous_id", "nutrition_source_receipts.id", nullable=True),
    Column("previous_hash", String(64)),
    ref("principal_id", "nutrition_source_principals.id", nullable=True),
    ref("grant_event_id", "nutrition_source_authority.id", nullable=True),
    Column("authority_generation", BigInteger, nullable=False),
    ref("provider_enrollment_id", "nutrition_source_providers.id", nullable=True),
    Column("actor_database_oid", BigInteger, nullable=False),
    Column("actor_role_oid", BigInteger, nullable=False),
    Column("actor", J, nullable=False),
    Column("subject_witness", J),
    ref("delegation_event_id", "nutrition_member_delegations.id", nullable=True),
    Column("legacy_anchor", J),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    Column("idempotency_key", String(100), nullable=False),
    Column("command_hash", String(64), nullable=False),
    Column("fact_hash", String(64), nullable=False),
    UniqueConstraint("stream_key", "sequence"),
    UniqueConstraint("recorded_order"),
    UniqueConstraint("actor_database_oid", "actor_role_oid", "idempotency_key"),
    CheckConstraint(
        "kind IN ('AUTHORITY','DRAFT','REVIEW','PUBLICATION','DELEGATION',"
        "'OBSERVATION','ASSESSMENT','GOAL')",
        name="kind",
    ),
    CheckConstraint(
        "sequence>0 AND authority_generation>=0 AND isfinite(recorded_at)", name="sequence_time"
    ),
    CheckConstraint(
        "(sequence=1)=(previous_id IS NULL) AND (sequence=1)=(previous_hash IS NULL)",
        name="predecessor",
    ),
    CheckConstraint(
        "(kind='AUTHORITY')=(principal_id IS NULL) AND (kind='AUTHORITY')=(grant_event_id IS NULL)",
        name="authority_class",
    ),
)

authority = Table(
    "nutrition_source_authority",
    Base.metadata,
    Column(
        "id",
        Uuid,
        ForeignKey(
            "nutrition_source_receipts.id",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        primary_key=True,
    ),
    ref("principal_id", "nutrition_source_principals.id"),
    ref("provider_id", "nutrition_source_providers.id", nullable=True),
    Column("family_id", String(100)),
    Column("household_id", Uuid),
    Column("member_id", Uuid),
    Column("capability", String(40), nullable=False),
    Column("action", String(10), nullable=False),
    Column("protocol_fingerprint", String(64)),
    Column("fact_key", String(20)),
    *interval(),
    Column("body", J, nullable=False),
    ForeignKeyConstraint(
        ["household_id", "member_id"],
        ["household_members.household_id", "household_members.id"],
        ondelete="RESTRICT",
    ),
    CheckConstraint("action IN ('GRANT','REVOKE')", name="action"),
    CheckConstraint(
        "capability IN ('GUIDELINE_REVIEW','GUIDELINE_PUBLISH','GUIDELINE_WITHDRAW',"
        "'ELIGIBILITY_ATTEST','MEMBER_OBSERVATION_WRITE','MEMBER_GOAL_WRITE',"
        "'ROOT_SOURCE_READ','VALIDATOR_SOURCE_READ')",
        name="capability",
    ),
)

drafts = Table(
    "nutrition_guideline_drafts",
    Base.metadata,
    Column(
        "id",
        Uuid,
        ForeignKey(
            "nutrition_source_receipts.id",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        primary_key=True,
    ),
    ref("provider_id", "nutrition_source_providers.id"),
    Column("family_id", String(100), nullable=False),
    Column("body_fingerprint", String(64), nullable=False),
    Column("body", J, nullable=False),
)

reviews = Table(
    "nutrition_guideline_reviews",
    Base.metadata,
    Column(
        "id",
        Uuid,
        ForeignKey(
            "nutrition_source_receipts.id",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        primary_key=True,
    ),
    ref("draft_revision_id", "nutrition_guideline_drafts.id"),
    Column("decision", String(10), nullable=False),
    ref("prior_review_id", "nutrition_guideline_reviews.id", nullable=True),
    Column("body", J, nullable=False),
    CheckConstraint("decision IN ('APPROVE','CANCEL')", name="decision"),
)

publications = Table(
    "nutrition_guideline_publications",
    Base.metadata,
    Column(
        "id",
        Uuid,
        ForeignKey(
            "nutrition_source_receipts.id",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        primary_key=True,
    ),
    ref("draft_revision_id", "nutrition_guideline_drafts.id"),
    Column("action", String(10), nullable=False),
    ref("review_event_id", "nutrition_guideline_reviews.id", nullable=True),
    ref("prior_publication_id", "nutrition_guideline_publications.id", nullable=True),
    Column("effective_at", DateTime(timezone=True), nullable=False),
    Column("body", J, nullable=False),
    CheckConstraint("action IN ('PUBLISH','SUPERSEDE','RETIRE','RETRACT')", name="action"),
    CheckConstraint("isfinite(effective_at)", name="effective_time"),
)

delegations = Table(
    "nutrition_member_delegations",
    Base.metadata,
    Column(
        "id",
        Uuid,
        ForeignKey(
            "nutrition_source_receipts.id",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        primary_key=True,
    ),
    *subject(),
    ref("grantee_principal_id", "nutrition_source_principals.id"),
    Column("operation_scope", String(30), nullable=False),
    Column("action", String(10), nullable=False),
    ref("previous_grant_id", "nutrition_member_delegations.id", nullable=True),
    *interval(),
    Column("body", J, nullable=False),
    CheckConstraint(
        "operation_scope IN ('MEMBER_GOAL_WRITE','BODY_MASS_WRITE','HEIGHT_WRITE')",
        name="operation_scope",
    ),
    CheckConstraint("action IN ('GRANT','REVOKE')", name="action"),
)


def member_revision_table(name, *extra):
    return Table(
        name,
        Base.metadata,
        Column(
            "id",
            Uuid,
            ForeignKey(
                "nutrition_source_receipts.id",
                ondelete="RESTRICT",
                deferrable=True,
                initially="DEFERRED",
            ),
            primary_key=True,
        ),
        *subject(),
        Column("operation", String(10), nullable=False),
        *interval(),
        *extra,
        Column("body", J, nullable=False),
        CheckConstraint("operation IN ('CREATE','REPLACE','CORRECT','RETRACT')", name="operation"),
    )


observations = member_revision_table(
    "nutrition_physiology_revisions",
    Column("fact_key", String(20), nullable=False),
    Column("unit", String(10), nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    CheckConstraint(
        "(fact_key='BODY_MASS' AND unit='KG') OR (fact_key='HEIGHT' AND unit='CM')",
        name="fact_unit",
    ),
)
assessments = member_revision_table(
    "nutrition_eligibility_revisions",
    ref("guideline_revision_id", "nutrition_guideline_drafts.id"),
    Column("protocol_fingerprint", String(64), nullable=False),
    Column("outcome", String(20), nullable=False),
    CheckConstraint(
        "outcome IN ('ADMITTED','OUT_OF_SCOPE','EXCLUDED','UNDETERMINED')", name="outcome"
    ),
)
goals = member_revision_table(
    "nutrition_goal_revisions",
    Column("goal_id", Uuid, nullable=False),
    Column("goal_type", String(30), nullable=False),
    Column("direction", String(10)),
    CheckConstraint("goal_type='ENERGY_DIRECTION'", name="goal_type"),
    CheckConstraint(
        "(operation='RETRACT' AND direction IS NULL) OR "
        "(operation<>'RETRACT' AND direction IN ('CUT','MAINTAIN','GAIN'))",
        name="intent_only",
    ),
)

evidence_artifacts = Table(
    "nutrition_source_evidence_artifacts",
    Base.metadata,
    Column("environment", String(30), primary_key=True),
    Column("evidence_id", String(100), primary_key=True),
    Column("version", String(100), primary_key=True),
    Column("body_fingerprint", String(64), nullable=False),
    Column("body", J, nullable=False),
    CheckConstraint("environment IN ('TEST_ONLY','REVIEWED_PRODUCTION')", name="environment"),
)

NUTRITION_ROOT_TABLES = (
    providers,
    principals,
    streams,
    receipts,
    authority,
    drafts,
    reviews,
    publications,
    delegations,
    observations,
    assessments,
    goals,
    evidence_artifacts,
)
for table in NUTRITION_ROOT_TABLES:
    for foreign_key in table.foreign_key_constraints:
        columns = tuple(c.name for c in foreign_key.columns)
        if not any(
            tuple(c.name for c in con.columns)[: len(columns)] == columns
            for con in table.constraints
            if con.__class__.__name__ in {"PrimaryKeyConstraint", "UniqueConstraint"}
        ):
            Index("ix_" + table.name + "_" + "_".join(columns), *foreign_key.columns)
