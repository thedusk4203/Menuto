"""Hierarchy-specific real SCRAM/TLS smoke, never superuser session impersonation."""

import pytest
from app.modules.preferences.hierarchy_sources import capture_hierarchy_sources
from app.persistence.database import create_database_engine
from hierarchy_postgres_fixtures import capture
from hierarchy_postgres_fixtures import hierarchy_server as hierarchy_server
from hierarchy_postgres_fixtures import hierarchy_source as hierarchy_source
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session

pytestmark = pytest.mark.postgres


def test_a01_real_scram_login_and_immutable_enrollment(hierarchy_source):
    s = hierarchy_source
    source = capture(s)
    assert source.reader_session.authentication_method == "scram-sha-256"
    assert source.reader_session.role_name == s["names"]["reader"]
    assert source.reader_principal_id == s["principals"]["reader"].id
    assert source.reader_session.role_oid == s["principals"]["reader"].role_oid


def test_a01_wrong_password_rejected_by_postgresql(hierarchy_source):
    s = hierarchy_source
    url = s["engines"]["reader"].url.set(password="intentionally-wrong-test-password")
    engine = create_database_engine(url.render_as_string(hide_password=False))
    try:
        with pytest.raises(OperationalError, match="password authentication failed"):
            with engine.connect():
                pass
    finally:
        engine.dispose()


@pytest.mark.parametrize("who", ["trust", "password"])
def test_a01_trust_and_unsupported_auth_cannot_be_authority(hierarchy_source, who):
    s = hierarchy_source
    with Session(
        s["engines"][who].execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        )
    ) as session:
        with pytest.raises(DBAPIError, match="SCRAM authenticated original session required"):
            capture_hierarchy_sources(
                session,
                dict(
                    provider_id=s["provider"].id,
                    policy_id=s["policy"].policy_id,
                    requested_targets=[],
                ),
            )


@pytest.mark.parametrize("who", ["super", "admin"])
def test_a01_real_unsafe_superuser_admin_sessions_denied_normal_interface(hierarchy_source, who):
    s = hierarchy_source
    with Session(
        s["engines"][who].execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        )
    ) as session:
        # Admin requires EXECUTE to demonstrate the independent normal-interface guard.
        if who == "admin":
            with s["engines"]["root"].begin() as root:
                root.execute(text(f'GRANT menuto_hierarchy_client TO "{s["names"][who]}"'))
        try:
            with pytest.raises(DBAPIError, match="Unsafe source login"):
                capture_hierarchy_sources(
                    session,
                    dict(
                        provider_id=s["provider"].id,
                        policy_id=s["policy"].policy_id,
                        requested_targets=[],
                    ),
                )
        finally:
            session.rollback()
            if who == "admin":
                with s["engines"]["root"].begin() as root:
                    root.execute(text(f'REVOKE menuto_hierarchy_client FROM "{s["names"][who]}"'))


def test_a01_verified_tls_and_server_certificate(hierarchy_source, tmp_path):
    s = hierarchy_source
    with s["engines"]["root"].connect() as root:
        assert root.scalar(text("SHOW ssl")) == "on", "Disposable PostgreSQL TLS must be configured"
        certificate = root.scalar(text("SELECT pg_read_file(current_setting('ssl_cert_file'))"))
    path = tmp_path / "hierarchy-test-root.crt"
    path.write_text(certificate, encoding="utf-8")
    engine = create_database_engine(
        s["engines"]["reader"]
        .url.update_query_dict(dict(sslmode="verify-full", sslrootcert=str(path)))
        .render_as_string(hide_password=False)
    )
    try:
        with Session(
            engine.execution_options(isolation_level="REPEATABLE READ", postgresql_readonly=True)
        ) as session:
            assert (
                session.scalar(text("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()"))
                is True
            )
            source = capture_hierarchy_sources(
                session,
                dict(
                    provider_id=s["provider"].id,
                    policy_id=s["policy"].policy_id,
                    requested_targets=[],
                ),
            )
            assert source.reader_session.role_name == s["names"]["reader"]
    finally:
        engine.dispose()


def test_a01_remote_interface_requires_verify_full_before_connection(hierarchy_source):
    s = hierarchy_source
    engine = create_database_engine(
        s["engines"]["reader"]
        .url.set(host="remote.invalid")
        .update_query_dict(dict(sslmode="disable"))
        .render_as_string(hide_password=False)
    )
    try:
        with Session(engine) as session, pytest.raises(ValueError, match="sslmode=verify-full"):
            capture_hierarchy_sources(
                session,
                dict(
                    provider_id=s["provider"].id,
                    policy_id=s["policy"].policy_id,
                    requested_targets=[],
                ),
            )
    finally:
        engine.dispose()
