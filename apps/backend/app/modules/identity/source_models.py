"""Private Identity source metadata; the frozen public Base is deliberately untouched."""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Index,
    MetaData,
    Sequence,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class IdentitySourceBase(DeclarativeBase):
    metadata = MetaData(schema="menuto_identity_source")


SCHEMA = "menuto_identity_source"
IDENTITY_ROLE_NAMES = (
    "menuto_identity_source_owner",
    "menuto_identity_bootstrap",
    "menuto_identity_issuer",
    "menuto_identity_requester",
)
IDENTITY_ENTRY_NAMES = (
    "bootstrap_root",
    "change_issuer",
    "change_binding",
    "change_operation_grant",
    "capture_request_source",
)
RECORDED_ORDER = Sequence("recorded_order", schema=SCHEMA, start=1)


def _history(name, kind, actions, extras, constraints=()):
    fields = [
        Column("id", Uuid, primary_key=True),
        Column("root_id", Uuid, nullable=False),
        Column("stream_id", Uuid, nullable=False),
        Column("revision", BigInteger, nullable=False),
        Column("recorded_order", BigInteger, nullable=False),
        Column("recorded_at", DateTime(timezone=True), nullable=False),
        Column("previous_id", Uuid),
        Column("previous_fingerprint", String(64)),
        Column("action", Text, nullable=False),
        Column("effective_start", DateTime(timezone=True)),
        Column("effective_end", DateTime(timezone=True)),
        Column("actor_database_oid", BigInteger, nullable=False),
        Column("actor_role_oid", BigInteger, nullable=False),
        Column("actor_database_name", String(63), nullable=False),
        Column("actor_role_name", String(63), nullable=False),
        Column("author_session", JSONB, nullable=False),
        Column("command_body", JSONB, nullable=False),
        Column("command_fingerprint", String(64), nullable=False),
        Column("fact_fingerprint", String(64), nullable=False),
        Column("idempotency_key", Uuid, nullable=False),
        Column("environment", Text, nullable=False),
    ]
    table = Table(
        name,
        IdentitySourceBase.metadata,
        *fields,
        *extras,
        UniqueConstraint("id", "root_id", "stream_id", name=name + "_id_root_stream"),
        UniqueConstraint("id", "root_id", name=name + "_id_root"),
        UniqueConstraint("root_id", "stream_id", "revision", name=name + "_revision"),
        UniqueConstraint("recorded_order", name=name + "_order"),
        ForeignKeyConstraint(
            ["previous_id", "root_id", "stream_id"],
            [f"{SCHEMA}.{name}.id", f"{SCHEMA}.{name}.root_id", f"{SCHEMA}.{name}.stream_id"],
            name=name + "_predecessor",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint("revision>0 AND recorded_order>0", name=name + "_positive"),
        CheckConstraint(
            "((revision=1 AND previous_id IS NULL AND previous_fingerprint IS NULL) OR "
            "(revision>1 AND previous_id IS NOT NULL AND "
            "previous_fingerprint ~ '^[a-f0-9]{64}$'))",
            name=name + "_previous",
        ),
        CheckConstraint(
            "isfinite(recorded_at) AND ((action='REVOKE' AND effective_start IS NULL "
            "AND effective_end IS NULL) OR (action<>'REVOKE' AND effective_start IS NOT NULL "
            "AND effective_end IS NOT NULL AND isfinite(effective_start) "
            "AND isfinite(effective_end) "
            "AND effective_start<effective_end))",
            name=name + "_effective",
        ),
        CheckConstraint(
            "action IN (" + ",".join("'" + a + "'" for a in actions) + ")", name=name + "_action"
        ),
        CheckConstraint(
            "actor_database_oid BETWEEN 1 AND 4294967295 AND "
            "actor_role_oid BETWEEN 1 AND 4294967295",
            name=name + "_oids",
        ),
        CheckConstraint(
            "octet_length(actor_database_name) BETWEEN 1 AND 63 AND "
            "octet_length(actor_role_name) BETWEEN 1 AND 63",
            name=name + "_names",
        ),
        CheckConstraint(
            "command_fingerprint ~ '^[a-f0-9]{64}$' AND fact_fingerprint ~ '^[a-f0-9]{64}$'",
            name=name + "_fingerprints",
        ),
        CheckConstraint(
            "environment='TEST_ONLY' AND jsonb_typeof(author_session)='object' AND "
            "jsonb_typeof(command_body)='object' AND command_body->>'version'='1' AND "
            f"command_body->>'kind'='{kind}' AND command_body->>'action'=action AND "
            "command_body->>'environment'='TEST_ONLY' AND "
            "(command_body->>'root_id')::uuid=root_id AND "
            "(command_body->>'idempotency_key')::uuid=idempotency_key",
            name=name + "_typed",
        ),
        *constraints,
    )
    Index(name + "_latest", table.c.root_id, table.c.stream_id, table.c.revision.desc())
    Index(name + "_root_order", table.c.root_id, table.c.recorded_order)
    return table


def _root_fk(name):
    return ForeignKeyConstraint(
        ["root_initial_fact_id", "root_id"],
        [f"{SCHEMA}.roots.id", f"{SCHEMA}.roots.root_id"],
        name=name + "_root_initializer",
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )


ROOTS = _history(
    "roots",
    "ROOT",
    ("INITIALIZE", "RENEW", "REVOKE"),
    [
        Column("database_oid", BigInteger, nullable=False),
        Column("database_name", String(63), nullable=False),
        Column("deployment_context_id", String(64), nullable=False),
    ],
    [
        CheckConstraint(
            "stream_id=root_id AND database_oid BETWEEN 1 AND 4294967295", name="roots_identity"
        ),
    ],
)
Index(
    "roots_one_initializer",
    ROOTS.c.action,
    unique=True,
    postgresql_where=ROOTS.c.action == "INITIALIZE",
)

ISSUERS = _history(
    "issuers",
    "ISSUER",
    ("ENROLL", "RENEW", "REVOKE"),
    [
        Column("root_initial_fact_id", Uuid, nullable=False),
        Column("issuer_user_id", Uuid, nullable=False),
        Column("issuer_role_oid", BigInteger, nullable=False),
        Column("issuer_role_name", String(63), nullable=False),
        Column("target_role", JSONB, nullable=False),
        Column("capability", Text, nullable=False),
    ],
    [
        _root_fk("issuers"),
        CheckConstraint(
            "capability='BINDINGS_AND_SCOPE_GRANTS' AND issuer_role_oid BETWEEN 1 AND 4294967295",
            name="issuers_capability",
        ),
    ],
)
Index("issuers_user", ISSUERS.c.root_id, ISSUERS.c.issuer_user_id)

BINDINGS = _history(
    "principal_bindings",
    "BINDING",
    ("ENROLL", "RENEW", "REVOKE"),
    [
        Column("root_initial_fact_id", Uuid, nullable=False),
        Column("enrolling_issuer_id", Uuid, nullable=False),
        Column("author_issuer_fact_id", Uuid, nullable=False),
        Column("user_id", Uuid, nullable=False),
        Column("role_oid", BigInteger, nullable=False),
        Column("role_name", String(63), nullable=False),
        Column("target_role", JSONB, nullable=False),
    ],
    [
        _root_fk("bindings"),
        ForeignKeyConstraint(
            ["author_issuer_fact_id", "root_id"],
            [f"{SCHEMA}.issuers.id", f"{SCHEMA}.issuers.root_id"],
            name="bindings_author",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint(
            "role_oid BETWEEN 1 AND 4294967295 AND octet_length(role_name) BETWEEN 1 AND 63",
            name="bindings_role",
        ),
    ],
)
for suffix, col in (("oid", "role_oid"), ("name", "role_name")):
    Index(
        "bindings_reserve_" + suffix,
        BINDINGS.c.root_id,
        BINDINGS.c[col],
        unique=True,
        postgresql_where=BINDINGS.c.action == "ENROLL",
    )
Index("bindings_user", BINDINGS.c.root_id, BINDINGS.c.user_id, BINDINGS.c.stream_id)

GRANTS = _history(
    "operation_grants",
    "OPERATION_GRANT",
    ("GRANT", "RENEW", "REVOKE"),
    [
        Column("root_initial_fact_id", Uuid, nullable=False),
        Column("binding_initial_fact_id", Uuid, nullable=False),
        Column("binding_id", Uuid, nullable=False),
        Column("author_issuer_fact_id", Uuid, nullable=False),
        Column("operation", Text, nullable=False),
        Column("household_id", Uuid, nullable=False),
        Column("tracked_member_id", Uuid, nullable=False),
        Column("membership_id", Uuid, nullable=False),
        Column("actor_member_id", Uuid, nullable=False),
        Column("membership_role", Text, nullable=False),
        Column("membership_at_issue", JSONB, nullable=False),
    ],
    [
        _root_fk("grants"),
        ForeignKeyConstraint(
            ["binding_initial_fact_id", "root_id", "binding_id"],
            [
                f"{SCHEMA}.principal_bindings.id",
                f"{SCHEMA}.principal_bindings.root_id",
                f"{SCHEMA}.principal_bindings.stream_id",
            ],
            name="grants_binding",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["author_issuer_fact_id", "root_id"],
            [f"{SCHEMA}.issuers.id", f"{SCHEMA}.issuers.root_id"],
            name="grants_author",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint(
            "operation='CAPTURE_EXPLICIT_PLAN_INTENT' AND membership_role IN ('OWNER','EDITOR')",
            name="grants_scope",
        ),
    ],
)
Index(
    "grants_scope_latest",
    GRANTS.c.root_id,
    GRANTS.c.binding_id,
    GRANTS.c.operation,
    GRANTS.c.household_id,
    GRANTS.c.tracked_member_id,
    GRANTS.c.revision.desc(),
)

FRONTIERS = Table(
    "frontiers",
    IdentitySourceBase.metadata,
    Column("root_id", Uuid, primary_key=True),
    Column("kind", Text, primary_key=True),
    Column("stream_id", Uuid, primary_key=True),
    Column("root_initial_fact_id", Uuid, nullable=False),
    Column("revision", BigInteger, nullable=False),
    Column("fact_count", BigInteger, nullable=False),
    Column("head_id", Uuid),
    Column("head_fingerprint", String(64)),
    Column("directory_entries", JSONB, nullable=False),
    Column("directory_fingerprint", String(64)),
    _root_fk("frontiers"),
    CheckConstraint(
        "kind IN ('ROOT','ISSUER_DIRECTORY','BINDING','OPERATION_GRANT')", name="frontiers_kind"
    ),
    CheckConstraint(
        "revision>=0 AND fact_count>=0 AND "
        "((revision=0 AND fact_count=0 AND head_id IS NULL AND head_fingerprint IS NULL) OR "
        "(revision>0 AND fact_count>0 AND head_id IS NOT NULL AND "
        "head_fingerprint ~ '^[a-f0-9]{64}$'))",
        name="frontiers_shape",
    ),
    CheckConstraint(
        "(kind='ISSUER_DIRECTORY' AND directory_fingerprint ~ '^[a-f0-9]{64}$') OR "
        "(kind<>'ISSUER_DIRECTORY' AND directory_entries='[]'::jsonb AND "
        "directory_fingerprint IS NULL)",
        name="frontiers_directory",
    ),
)

RECEIPTS = Table(
    "command_receipts",
    IdentitySourceBase.metadata,
    Column("id", Uuid, primary_key=True),
    Column("root_id", Uuid, nullable=False),
    Column("actor_role_oid", BigInteger, nullable=False),
    Column("idempotency_key", Uuid, nullable=False),
    Column("kind", Text, nullable=False),
    Column("stream_id", Uuid, nullable=False),
    Column("revision", BigInteger, nullable=False),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    Column("command_fingerprint", String(64), nullable=False),
    Column("fact_fingerprint", String(64), nullable=False),
    *[Column(name + "_fact_id", Uuid) for name in ("root", "issuer", "binding", "grant")],
    UniqueConstraint("root_id", "actor_role_oid", "idempotency_key", name="receipts_actor_key"),
    CheckConstraint(
        "revision>0 AND actor_role_oid BETWEEN 1 AND 4294967295 AND isfinite(recorded_at) AND "
        "command_fingerprint ~ '^[a-f0-9]{64}$' AND fact_fingerprint ~ '^[a-f0-9]{64}$'",
        name="receipts_values",
    ),
    CheckConstraint(
        "(kind='ROOT' AND root_fact_id IS NOT NULL AND num_nonnulls(issuer_fact_id,binding_fact_id,"
        "grant_fact_id)=0) OR "
        "(kind='ISSUER' AND issuer_fact_id IS NOT NULL "
        "AND num_nonnulls(root_fact_id,binding_fact_id,"
        "grant_fact_id)=0) OR "
        "(kind='BINDING' AND binding_fact_id IS NOT NULL "
        "AND num_nonnulls(root_fact_id,issuer_fact_id,"
        "grant_fact_id)=0) OR "
        "(kind='OPERATION_GRANT' AND grant_fact_id IS NOT NULL AND "
        "num_nonnulls(root_fact_id,issuer_fact_id,binding_fact_id)=0)",
        name="receipts_typed",
    ),
    *[
        ForeignKeyConstraint(
            [column + "_fact_id", "root_id"],
            [f"{SCHEMA}.{target}.id", f"{SCHEMA}.{target}.root_id"],
            name="receipts_" + column + "_fact",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        )
        for column, target in [
            ("root", "roots"),
            ("issuer", "issuers"),
            ("binding", "principal_bindings"),
            ("grant", "operation_grants"),
        ]
    ],
)
for name in ("root", "issuer", "binding", "grant"):
    Index("receipts_" + name + "_lookup", RECEIPTS.c[name + "_fact_id"])
IDENTITY_SOURCE_TABLES = (ROOTS, ISSUERS, BINDINGS, GRANTS, FRONTIERS, RECEIPTS)
