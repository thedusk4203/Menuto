"""One actual clean caller-owned reader transaction; no retained-source admission."""

from dataclasses import dataclass
from time import monotonic

import psycopg
from psycopg.pq import TransactionStatus
from sqlalchemy import Connection, text
from sqlalchemy.exc import DBAPIError

from app.modules.identity.source_contracts import (
    IdentityCaptureFailureV1,
    IdentityRequestBindingV1,
    IdentitySourceSnapshotV1,
)
from app.modules.identity.source_primitives import IdentityResourceError, canonical, parse
from app.modules.identity.source_replay import validate_identity_source_v1


@dataclass(frozen=True)
class IdentityDeploymentContext:
    """Internal server configuration, not caller credentials or a bearer capability."""

    root_id: str
    database_oid: int
    database_name: str
    endpoint_id: str
    host: str
    sslrootcert: str


def _failure(request_id, outcome, reason):
    return IdentityCaptureFailureV1(
        version=1,
        request_id=request_id,
        outcome=outcome,
        reason=reason,
        payload=None,
        environment="TEST_ONLY",
        transport="UNVERIFIED_TRANSPORT",
        numerical_use="NOT_ADMITTED",
        planner_ready=False,
        activation_ready=False,
    )


def capture_identity_request_source_v1(connection, request_binding, *, context):
    """No commit/rollback, cached result, alternate session, callback or caller budget."""
    request_id = None
    try:
        binding = parse(IdentityRequestBindingV1, request_binding, maximum=131_072)
        request_id = binding.request_id
    except IdentityResourceError:
        return _failure(None, "RESOURCE_EXCEEDED", "LIMIT_EXCEEDED")
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return _failure(None, "INVALID_INPUT", "INVALID_STRUCTURE")
    if type(context) is not IdentityDeploymentContext or not isinstance(connection, Connection):
        return _failure(request_id, "UNSUPPORTED", "UNSUPPORTED_DEPLOYMENT")
    if connection.closed or not connection.in_transaction() or connection.in_nested_transaction():
        return _failure(request_id, "CAPTURE_REJECTED", "INVALID_TRANSACTION")
    driver = connection.connection.driver_connection
    if type(driver) is not psycopg.Connection:
        return _failure(request_id, "UNSUPPORTED", "UNSUPPORTED_DEPLOYMENT")
    if (
        driver.info.transaction_status != TransactionStatus.IDLE
        or driver.read_only is not True
        or (
            driver.isolation_level
            not in {psycopg.IsolationLevel.REPEATABLE_READ, psycopg.IsolationLevel.SERIALIZABLE}
        )
    ):
        return _failure(request_id, "CAPTURE_REJECTED", "INVALID_TRANSACTION")
    parameters = driver.info.get_parameters()
    if (
        parameters.get("sslmode") != "verify-full"
        or parameters.get("sslrootcert") != context.sslrootcert
        or parameters.get("host") != context.host
        or parameters.get("dbname") != context.database_name
    ):
        return _failure(request_id, "CAPTURE_REJECTED", "AUTHENTICATION_FAILED")
    started = monotonic()
    try:
        raw = connection.execute(
            text("SELECT menuto_identity_source.capture_request_source(:body)"),
            {"body": canonical(binding).decode("utf-8")},
        ).scalar_one()
        source = parse(IdentitySourceSnapshotV1, raw)
        session = source.frame.session_start
        if (
            str(source.frame.root_id) != context.root_id
            or session.database_oid != context.database_oid
            or session.database_name != context.database_name
            or session.endpoint_id != context.endpoint_id
        ):
            return _failure(request_id, "CAPTURE_REJECTED", "WRONG_ROOT")
        source = validate_identity_source_v1(source, binding)
        if monotonic() - started > 15:
            return _failure(request_id, "RESOURCE_EXCEEDED", "LIMIT_EXCEEDED")
        return source
    except DBAPIError as error:
        code = getattr(error.orig, "sqlstate", None)
        if code in {"57014", "55P03"}:
            return _failure(request_id, "RESOURCE_EXCEEDED", "CANCELLED")
        if code == "54000":
            return _failure(request_id, "RESOURCE_EXCEEDED", "LIMIT_EXCEEDED")
        if code in {"40001", "40P01"}:
            return _failure(request_id, "SOURCE_CUT_INCOHERENT", "CATALOG_CHANGED")
        if code in {"25001", "25006"}:
            return _failure(request_id, "CAPTURE_REJECTED", "INVALID_TRANSACTION")
        return _failure(request_id, "CAPTURE_REJECTED", "AUTHORIZATION_DENIED")
    except IdentityResourceError:
        return _failure(request_id, "RESOURCE_EXCEEDED", "LIMIT_EXCEEDED")
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return _failure(request_id, "SOURCE_CUT_INCOHERENT", "INCOMPLETE_SOURCE")
