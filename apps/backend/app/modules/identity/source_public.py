"""Caller-transaction command facade; PostgreSQL alone reconstructs write authority."""

from sqlalchemy import Connection, text

from app.modules.identity.source_contracts import (
    IdentityBindingCommandV1,
    IdentityCommandReceiptV1,
    IdentityIssuerCommandV1,
    IdentityOperationGrantCommandV1,
    IdentityRootCommandV1,
)
from app.modules.identity.source_primitives import canonical, parse


def _command(connection, value, model, entry):
    if entry not in {"bootstrap_root", "change_issuer", "change_binding", "change_operation_grant"}:
        raise ValueError("Only exact protected command entries are supported")
    if not isinstance(connection, Connection) or not connection.in_transaction():
        raise ValueError("Caller-owned write transaction required")
    command = parse(model, value, maximum=16_384)
    # Entry names below are private, finite literals; never caller-built SQL identifiers.
    result = connection.execute(
        text("SELECT menuto_identity_source." + entry + "(:body)"),
        {"body": canonical(command).decode("utf-8")},
    ).scalar_one()
    return parse(IdentityCommandReceiptV1, result, maximum=16_384)


def bootstrap_identity_root_v1(connection, command):
    return _command(connection, command, IdentityRootCommandV1, "bootstrap_root")


def change_identity_issuer_v1(connection, command):
    return _command(connection, command, IdentityIssuerCommandV1, "change_issuer")


def change_identity_binding_v1(connection, command):
    return _command(connection, command, IdentityBindingCommandV1, "change_binding")


def change_identity_operation_grant_v1(connection, command):
    return _command(connection, command, IdentityOperationGrantCommandV1, "change_operation_grant")
