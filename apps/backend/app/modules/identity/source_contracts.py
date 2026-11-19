"""Identity-owned immutable source transports; TEST_ONLY and never bearer authority."""

import re
from datetime import UTC, datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    model_validator,
)

from app.domain.contracts import Contract, Sha256
from app.domain.snapshots import Horizon


def _version(value):
    if type(value) is not int or value != 1:
        raise ValueError("Unsupported Identity version")
    return value


def _false(value):
    if type(value) is not bool or value:
        raise ValueError("Authority remains closed")
    return value


def _uuid(value):
    if type(value) is UUID:
        return value
    if type(value) is not str:
        raise ValueError("Canonical UUID required")
    result = UUID(value)
    if str(result) != value:
        raise ValueError("Canonical UUID required")
    return result


def _instant(value):
    if type(value) is str:
        if not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})",
            value,
        ):
            raise ValueError("Zoned RFC3339 required")
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if type(value) is not datetime or type(value.tzinfo) is not timezone:
        raise ValueError("Concrete zoned instant required")
    return value.astimezone(UTC)


def _text(value):
    if (
        type(value) is not str
        or not value
        or any(ord(c) == 0 or 0xD800 <= ord(c) <= 0xDFFF for c in value)
    ):
        raise ValueError("Bounded plain text required")
    value.encode("utf-8", "strict")
    return value


def _role(value):
    value = _text(value)
    if len(value.encode("utf-8")) > 63 or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value):
        raise ValueError("PostgreSQL role-name byte limit")
    return value


def _evidence(value):
    value = _text(value)
    if len(value.encode("utf-8")) > 4096:
        raise ValueError("Evidence byte limit")
    return value


def _request(value):
    value = _text(value)
    if len(value.encode("utf-8")) > 49152:
        raise ValueError("Request byte limit")
    return value


def _horizon(value):
    if type(value) is Horizon:
        value = {"start": value.start, "end": value.end}
    if type(value) is not dict or set(value) != {"start", "end"}:
        raise ValueError("Exact horizon required")
    return {"start": _instant(value["start"]), "end": _instant(value["end"])}


_Version = Annotated[Literal[1], BeforeValidator(_version)]
_Closed = Annotated[Literal[False], BeforeValidator(_false)]
_Id = Annotated[UUID, BeforeValidator(_uuid)]
_Time = Annotated[
    datetime,
    BeforeValidator(_instant),
    PlainSerializer(
        lambda v: v.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        return_type=str,
        when_used="json",
    ),
]
_Text = Annotated[str, Field(strict=True, min_length=1, max_length=256), BeforeValidator(_text)]
_Key = Annotated[
    str,
    Field(strict=True, min_length=1, max_length=64, pattern=r"^[!-~]+$"),
    BeforeValidator(_text),
]
_Role = Annotated[str, Field(strict=True, min_length=1, max_length=63), BeforeValidator(_role)]
_Count = Annotated[int, Field(strict=True, ge=0, le=9_223_372_036_854_775_807)]
_Revision = Annotated[int, Field(strict=True, ge=1, le=9_223_372_036_854_775_807)]
_Oid = Annotated[int, Field(strict=True, ge=1, le=4_294_967_295)]
_Grantee = Annotated[int, Field(strict=True, ge=0, le=4_294_967_295)]
_Bool = Annotated[bool, Field(strict=True)]
_Horizon = Annotated[Horizon, BeforeValidator(_horizon)]
_Privilege = Literal[
    "CONNECT",
    "CREATE",
    "TEMPORARY",
    "USAGE",
    "EXECUTE",
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "TRUNCATE",
    "REFERENCES",
    "TRIGGER",
    "MAINTAIN",
    "SET",
    "ALTER SYSTEM",
]
_AclEntry = tuple[_Grantee, _Oid, _Privilege, _Bool]
_Kind = Literal["ROOT", "ISSUER", "BINDING", "OPERATION_GRANT"]
_SourceOutcome = Literal["AVAILABLE_AT_RETAINED_CUT", "UNAVAILABLE"]
_SourceReason = Literal[
    "SOURCE_AVAILABLE",
    "ROOT_EXPIRED",
    "ROOT_REVOKED",
    "ISSUER_EXPIRED",
    "ISSUER_REVOKED",
    "BINDING_EXPIRED",
    "BINDING_REVOKED",
    "GRANT_ABSENT",
    "GRANT_EXPIRED",
    "GRANT_REVOKED",
    "AUTHORIZATION_DENIED",
]


class _SourceContract(Contract):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        validate_default=True,
        revalidate_instances="always",
    )


class IdentityEffectiveRequestV1(_SourceContract):
    version: _Version
    mode: Literal["IMMEDIATE", "SCHEDULED"]
    start: _Time | None
    end: _Time

    @model_validator(mode="after")
    def shape(self):
        if (self.mode == "IMMEDIATE") != (self.start is None):
            raise ValueError("Effective mode/start mismatch")
        if self.start is not None and self.start >= self.end:
            raise ValueError("Empty effective interval")
        return self


class IdentityRoleFactV1(_SourceContract):
    version: _Version
    role_oid: _Oid
    role_name: _Role
    can_login: _Bool
    superuser: _Bool
    create_role: _Bool
    create_db: _Bool
    replication: _Bool
    bypass_rls: _Bool
    inherit: _Bool
    valid_until: _Time | None


class IdentityRoleEdgeV1(_SourceContract):
    version: _Version
    role_oid: _Oid
    member_oid: _Oid
    grantor_oid: _Oid
    inherit_option: _Bool
    set_option: _Bool
    admin_option: _Bool


class IdentityPrivilegeObjectFactV1(_SourceContract):
    version: _Version
    kind: Literal["DATABASE", "SCHEMA", "TABLE", "COLUMN", "SEQUENCE", "FUNCTION", "PARAMETER"]
    object_oid: _Oid
    sub_id: _Count
    schema_name: _Text | None
    object_name: _Text
    owner_oid: _Oid | None
    acl: tuple[_AclEntry, ...] | None
    definition_fingerprint: Sha256 | None

    @model_validator(mode="after")
    def owner_and_acl(self):
        if (self.kind == "PARAMETER") != (self.owner_oid is None):
            raise ValueError("Only PARAMETER is ownerless")
        if self.kind == "PARAMETER":
            if (
                self.sub_id
                or self.schema_name is not None
                or self.definition_fingerprint is not None
            ):
                raise ValueError("Parameter row descriptor mismatch")
        elif self.acl is None:
            raise ValueError("Owned object requires reconstructed ACL")
        allowed = {
            "DATABASE": {"CREATE", "CONNECT", "TEMPORARY"},
            "SCHEMA": {"CREATE", "USAGE"},
            "TABLE": {
                "SELECT",
                "INSERT",
                "UPDATE",
                "DELETE",
                "TRUNCATE",
                "REFERENCES",
                "TRIGGER",
                "MAINTAIN",
            },
            "COLUMN": {"SELECT", "INSERT", "UPDATE", "REFERENCES"},
            "SEQUENCE": {"USAGE", "SELECT", "UPDATE"},
            "FUNCTION": {"EXECUTE"},
            "PARAMETER": {"SET", "ALTER SYSTEM"},
        }[self.kind]
        if self.acl is not None:
            if len(set(self.acl)) != len(self.acl) or tuple(sorted(self.acl)) != self.acl:
                raise ValueError("ACL must be complete, uniquely ordered")
            if any(entry[2] not in allowed or entry[0] == 0 and entry[3] for entry in self.acl):
                raise ValueError("ACL privilege/kind mismatch")
        return self


class IdentitySessionFactV1(_SourceContract):
    version: _Version
    database_oid: _Oid
    database_owner_oid: _Oid
    login_role_oid: _Oid
    execution_owner_oid: _Oid
    database_name: _Role
    endpoint_id: _Text
    client_address: _Text
    server_address: _Text
    server_port: _Revision
    backend_pid: _Revision
    session_user: _Role
    system_user: _Text
    requested_role: _Text
    authentication_method: _Text
    tls: _Bool
    isolation: Literal["READ_COMMITTED", "REPEATABLE_READ", "SERIALIZABLE"]
    read_only: _Bool
    observed_at: _Time
    roles: Annotated[tuple[IdentityRoleFactV1, ...], Field(min_length=1, max_length=64)]
    edges: Annotated[tuple[IdentityRoleEdgeV1, ...], Field(max_length=128)]
    objects: Annotated[tuple[IdentityPrivilegeObjectFactV1, ...], Field(max_length=4096)]


class _Command(_SourceContract):
    version: _Version
    root_id: _Id
    idempotency_key: _Id
    expected_revision: _Count
    predecessor_id: _Id | None
    evidence_id: _Key
    evidence_version: _Key
    evidence_preimage: Annotated[
        str, Field(strict=True, min_length=1, max_length=4096), BeforeValidator(_evidence)
    ]
    environment: Literal["TEST_ONLY"]


class IdentityRootCommandV1(_Command):
    kind: Literal["ROOT"]
    action: Literal["INITIALIZE", "RENEW", "REVOKE"]
    effective: IdentityEffectiveRequestV1 | None


class IdentityIssuerCommandV1(_Command):
    kind: Literal["ISSUER"]
    issuer_id: _Id
    role_name: _Role
    user_id: _Id
    capability: Literal["BINDINGS_AND_SCOPE_GRANTS"]
    action: Literal["ENROLL", "RENEW", "REVOKE"]
    effective: IdentityEffectiveRequestV1 | None


class IdentityBindingCommandV1(_Command):
    kind: Literal["BINDING"]
    binding_id: _Id
    issuer_id: _Id
    user_id: _Id
    role_name: _Role
    action: Literal["ENROLL", "RENEW", "REVOKE"]
    effective: IdentityEffectiveRequestV1 | None


class IdentityOperationGrantCommandV1(_Command):
    kind: Literal["OPERATION_GRANT"]
    grant_id: _Id
    binding_id: _Id
    issuer_id: _Id
    household_id: _Id
    tracked_member_id: _Id
    operation: Literal["CAPTURE_EXPLICIT_PLAN_INTENT"]
    action: Literal["GRANT", "RENEW", "REVOKE"]
    effective: IdentityEffectiveRequestV1 | None


class IdentityMembershipWitnessV1(_SourceContract):
    version: _Version
    user_id: _Id
    household_id: _Id
    user_exists: _Bool
    membership_id: _Id | None
    membership_user_id: _Id | None
    membership_household_id: _Id | None
    actor_member_id: _Id | None
    role: Literal["OWNER", "EDITOR", "VIEWER"] | None
    actor_member_household_id: _Id | None
    target_member_id: _Id | None
    target_member_household_id: _Id | None
    target_member_exists: _Bool | None


class IdentityRecordedFactV1(_SourceContract):
    version: _Version
    fact_id: _Id
    root_id: _Id
    stream_id: _Id
    stream_kind: _Kind
    revision: _Revision
    recorded_order: _Revision
    recorded_at: _Time
    previous_fact_id: _Id | None
    previous_fact_fingerprint: Sha256 | None
    command: Annotated[
        IdentityRootCommandV1
        | IdentityIssuerCommandV1
        | IdentityBindingCommandV1
        | IdentityOperationGrantCommandV1,
        Field(discriminator="kind"),
    ]
    command_fingerprint: Sha256
    effective_start: _Time | None
    effective_end: _Time | None
    author: IdentitySessionFactV1
    author_issuer_fact_id: _Id | None
    target_role: IdentityRoleFactV1 | None
    membership_at_issue: IdentityMembershipWitnessV1 | None
    fact_fingerprint: Sha256


class IdentityCommandReceiptV1(_SourceContract):
    version: _Version
    root_id: _Id
    fact_id: _Id
    stream_id: _Id
    idempotency_key: _Id
    author_role_oid: _Oid
    revision: _Revision
    command_fingerprint: Sha256
    fact_fingerprint: Sha256
    recorded_at: _Time
    result: Literal["APPENDED"]


class IdentityRequestBindingV1(_SourceContract):
    version: _Version
    operation: Literal["CAPTURE_EXPLICIT_PLAN_INTENT"]
    actor_user_id: _Id
    household_id: _Id
    tracked_member_id: _Id
    request_id: _Id
    request_revision: _Count
    horizon: _Horizon
    request_utf8: Annotated[
        str, Field(strict=True, min_length=1, max_length=49152), BeforeValidator(_request)
    ]
    request_preimage_fingerprint: Sha256
    environment: Literal["TEST_ONLY"]


class IdentitySourceFrontierV1(_SourceContract):
    version: _Version
    root_id: _Id
    stream_id: _Id
    kind: Literal["ROOT", "ISSUER_DIRECTORY", "BINDING", "OPERATION_GRANT"]
    revision: _Count
    head_id: _Id | None
    head_fingerprint: Sha256 | None
    fact_count: _Count
    directory_fingerprint: Sha256 | None
    directory_entries: tuple[tuple[_Id, _Count, _Id, Sha256, _Count], ...]


class IdentityCaptureFrameV1(_SourceContract):
    version: _Version
    root_id: _Id
    deployment_context_id: _Key
    started_at: _Time
    finished_at: _Time
    transaction_started_at: _Time
    snapshot_id: _Text
    session_start: IdentitySessionFactV1
    session_end: IdentitySessionFactV1
    frontiers: tuple[IdentitySourceFrontierV1, ...]
    total_fact_count: _Count
    environment: Literal["TEST_ONLY"]
    transport: Literal["UNVERIFIED_TRANSPORT"]


class IdentitySourceSnapshotV1(_SourceContract):
    version: _Version
    binding: IdentityRequestBindingV1
    frame: IdentityCaptureFrameV1
    root_history: Annotated[tuple[IdentityRecordedFactV1, ...], Field(max_length=256)]
    issuer_history: Annotated[tuple[IdentityRecordedFactV1, ...], Field(max_length=2048)]
    binding_history: Annotated[tuple[IdentityRecordedFactV1, ...], Field(max_length=256)]
    grant_history: Annotated[tuple[IdentityRecordedFactV1, ...], Field(max_length=2048)]
    membership: IdentityMembershipWitnessV1 | None
    absences: tuple[tuple[_Kind | Literal["MEMBERSHIP"], _Id], ...]
    outcome: _SourceOutcome
    reason: _SourceReason
    source_fingerprint: Sha256


class IdentityCaptureFailureV1(_SourceContract):
    version: _Version
    request_id: _Id | None
    outcome: Literal[
        "INVALID_INPUT",
        "UNSUPPORTED",
        "CAPTURE_REJECTED",
        "SOURCE_CUT_INCOHERENT",
        "RESOURCE_EXCEEDED",
    ]
    reason: Literal[
        "INVALID_STRUCTURE",
        "UNSUPPORTED_VERSION",
        "UNSUPPORTED_DEPLOYMENT",
        "AUTHENTICATION_FAILED",
        "AUTHORIZATION_DENIED",
        "WRONG_ROOT",
        "INVALID_TRANSACTION",
        "INCOMPLETE_SOURCE",
        "CATALOG_CHANGED",
        "LIMIT_EXCEEDED",
        "CANCELLED",
    ]
    payload: None
    environment: Literal["TEST_ONLY"]
    transport: Literal["UNVERIFIED_TRANSPORT"]
    numerical_use: Literal["NOT_ADMITTED"]
    planner_ready: _Closed
    activation_ready: _Closed


class IdentitySourceCheckV1(_SourceContract):
    version: _Version
    decision: Literal["CONSISTENT", "INCONSISTENT", "NOT_CHECKABLE"]
    reconstructed_outcome: _SourceOutcome | None
    reason: Literal[
        "SOURCE_AVAILABLE",
        "FAITHFUL_NEGATIVE",
        "INVALID_AUTHORITY_HISTORY",
        "INVALID_AUTHENTICATION",
        "SUBJECT_MISMATCH",
        "INCOMPLETE_SOURCE",
        "FINGERPRINT_MISMATCH",
        "INVALID_CLAIM",
        "NO_SOURCE",
    ]
    checked_source_fingerprint: Sha256 | None
    checked_request_fingerprint: Sha256 | None
    check_fingerprint: Sha256
    environment: Literal["TEST_ONLY"]
    transport: Literal["UNVERIFIED_TRANSPORT"]
    numerical_use: Literal["NOT_ADMITTED"]
    planner_ready: _Closed
    activation_ready: _Closed
