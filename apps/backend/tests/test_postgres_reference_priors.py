"""Real SCRAM sessions, protected SQL, concurrency and replay acceptance.

Only the explicitly configured loopback test server's HBA is temporarily extended for
random test roles. Existing roles/rules are untouched and the exact HBA is restored.
"""

import json
import os
import secrets
import time
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.domain.feature_identity import canonical
from app.modules.catalog.models import Ingredient
from app.modules.preferences.reference_prior_contracts import (
    ReferencePriorCaptureRequest,
    ReferencePriorPublishCommand,
)
from app.modules.preferences.reference_prior_resolution import resolve_reference_priors
from app.modules.preferences.reference_priors import (
    capture_reference_prior_sources,
    change_reference_prior_authority,
    enroll_reference_prior_principal,
    publish_reference_prior,
    register_reference_prior_provider,
)
from app.persistence.database import create_database_engine
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session

pytestmark = [pytest.mark.postgres, pytest.mark.reference_prior_auth]
ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def source_server():
    url = os.environ.get("MENUTO_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set MENUTO_TEST_POSTGRES_URL for isolated real PostgreSQL/SCRAM acceptance")
    parsed = make_url(url)
    assert parsed.host in {"localhost", "127.0.0.1", "::1"} and parsed.database == "postgres"
    maintenance = create_database_engine(url).execution_options(isolation_level="AUTOCOMMIT")
    dbname = "prior_test_" + uuid4().hex
    names = {
        k: "prior_" + k + "_" + uuid4().hex[:12]
        for k in ("admin", "curator", "reader", "other", "trust", "password", "super", "dbowner")
    }
    passwords = {k: secrets.token_urlsafe(32) for k in names}
    engines = {}
    original_hba = hba_path = None
    created = False

    def write_hba(conn, content):
        # Large-object export preserves Windows CRLF and Unix LF byte-for-byte.
        oid = conn.scalar(
            text("SELECT lo_from_bytea(0,convert_to(:content,'UTF8'))"), {"content": content}
        )
        try:
            conn.execute(
                text("SELECT lo_export(CAST(:oid AS oid),:path)"), {"oid": oid, "path": hba_path}
            )
        finally:
            conn.execute(text("SELECT lo_unlink(CAST(:oid AS oid))"), {"oid": oid})
        conn.execute(text("SELECT pg_reload_conf()"))
        time.sleep(0.15)

    try:
        with maintenance.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{dbname}"'))
            created = True
        engine = create_database_engine(
            parsed.set(database=dbname).render_as_string(hide_password=False)
        )
        engines["root"] = engine
        config = Config(str(ROOT / "alembic.ini"))
        with engine.connect() as conn:
            config.attributes["connection"] = conn
            command.upgrade(config, "head")
            assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0015"
            assert len(inspect(conn).get_table_names()) == 86
            for table in (
                "providers",
                "principals",
                "frontiers",
                "streams",
                "authority",
                "revisions",
                "mutations",
            ):
                assert conn.scalar(text(f"SELECT count(*) FROM reference_prior_{table}")) == 0
            command.check(config)
            conn.commit()
            command.downgrade(config, "0013")
            conn.commit()
            assert (
                conn.scalar(text("SELECT count(*) FROM pg_extension WHERE extname='sslinfo'")) == 0
            )
            # A pre-existing shared deployment extension must survive source downgrade.
            conn.execute(text("CREATE EXTENSION sslinfo WITH SCHEMA public"))
            conn.commit()
            command.upgrade(config, "head")
            conn.commit()
            command.downgrade(config, "0013")
            conn.commit()
            assert (
                conn.scalar(text("SELECT count(*) FROM pg_extension WHERE extname='sslinfo'")) == 1
            )
            conn.commit()
            command.upgrade(config, "head")
            expected_tls = conn.scalar(
                text("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")
            )
            conn.execute(text("SET LOCAL ROLE menuto_prior_owner"))
            assert conn.scalar(text("SELECT menuto_prior.backend_tls()")) is expected_tls
            assert not conn.scalar(
                text("SELECT pg_has_role(current_user,'pg_read_all_stats','USAGE')")
            )
            conn.execute(text("RESET ROLE"))
            conn.commit()
        with maintenance.connect() as conn:
            from psycopg import sql

            raw = conn.connection.driver_connection
            with raw.cursor() as cur:
                cur.execute("SET password_encryption='scram-sha-256'")
                for k, name in names.items():
                    cur.execute(
                        sql.SQL("CREATE ROLE {} LOGIN INHERIT PASSWORD {}").format(
                            sql.Identifier(name), sql.Literal(passwords[k])
                        )
                    )
                    group = "menuto_prior_admin" if k == "admin" else "menuto_prior_client"
                    cur.execute(
                        sql.SQL("GRANT {} TO {}").format(
                            sql.Identifier(group), sql.Identifier(name)
                        )
                    )
                    if k == "super":
                        cur.execute(sql.SQL("ALTER ROLE {} SUPERUSER").format(sql.Identifier(name)))
            hba_path = conn.scalar(text("SHOW hba_file"))
            original_hba = conn.scalar(text("SELECT pg_read_file(:path)"), {"path": hba_path})
            rules = []
            actual_address = conn.scalar(text("SELECT host(inet_client_addr())"))
            addresses = {"127.0.0.1/32", "::1/128"}
            if actual_address:
                mask = 32 if ip_address(actual_address).version == 4 else 128
                addresses.add(f"{actual_address}/{mask}")
            for k, name in names.items():
                for address in sorted(addresses):
                    method = k if k in {"trust", "password"} else "scram-sha-256"
                    rules.append(f"host {dbname} {name} {address} {method}")
            write_hba(conn, "\n".join(rules) + "\n" + original_hba)
            assert not conn.scalar(
                text("SELECT count(*) FROM pg_hba_file_rules WHERE error IS NOT NULL")
            )
        for k, name in names.items():
            engines[k] = create_database_engine(
                parsed.set(database=dbname, username=name, password=passwords[k]).render_as_string(
                    hide_password=False
                )
            )
        with Session(engine) as session:
            ingredient = Ingredient(name="Reference source test identity")
            session.add(ingredient)
            session.commit()
            target = {"kind": "INGREDIENT", "ingredient_id": str(ingredient.id)}
        with Session(engines["admin"]) as session:
            principals = {
                k: enroll_reference_prior_principal(
                    session,
                    {
                        "role_name": names[k],
                        "idempotency_key": "enroll-" + k,
                    },
                )
                for k in ("curator", "reader", "other")
            }
            session.commit()
        yield dict(
            engines=engines,
            names=names,
            passwords=passwords,
            parsed=parsed,
            dbname=dbname,
            target=target,
            principals=principals,
            config=config,
        )
    finally:
        for engine in engines.values():
            engine.dispose()
        with maintenance.connect() as conn:
            if original_hba is not None:
                write_hba(conn, original_hba)
                assert (
                    conn.scalar(text("SELECT pg_read_file(:path)"), {"path": hba_path})
                    == original_hba
                )
            if created:
                conn.execute(text(f'DROP DATABASE "{dbname}" WITH (FORCE)'))
            from psycopg import sql

            with conn.connection.driver_connection.cursor() as cur:
                for name in names.values():
                    cur.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(name)))
        maintenance.dispose()


@pytest.fixture
def source(source_server):
    s = source_server
    with Session(s["engines"]["admin"]) as session:
        provider = register_reference_prior_provider(
            session,
            {
                "code": "test-" + uuid4().hex,
                "version": "1",
                "source_system": "review-test",
                "remit": "Synthetic acceptance only",
                "idempotency_key": uuid4().hex,
            },
        )
        generation = 0
        for who, caps in (
            ("curator", ("REVIEW_PUBLISH", "RETRACT", "CAPTURE")),
            ("reader", ("CAPTURE",)),
        ):
            for cap in caps:
                change_reference_prior_authority(
                    session,
                    dict(
                        provider_id=provider.id,
                        principal_id=s["principals"][who].id,
                        capability=cap,
                        action="GRANT",
                        expected_authority_generation=generation,
                        reason="Synthetic acceptance grant",
                        idempotency_key=uuid4().hex,
                    ),
                )
                generation += 1
        session.commit()
    return dict(s, provider=provider)


def publication(s, **changes):
    fields = dict(
        provider_id=s["provider"].id,
        target=s["target"],
        amount=dict(numerator=1, denominator=2),
        provenance=dict(
            source_system="review-test",
            external_record_id="review-artifact",
            source_version="1",
            content_hash="a" * 64,
            observed_at=datetime.now(UTC) - timedelta(days=1),
        ),
        review_rationale="Reviewed synthetic anchor, not a member preference",
        expected_provider_generation=0,
        expected_revision=-1,
        predecessor_id=None,
        idempotency_key=uuid4().hex,
    )
    fields.update(changes)
    return ReferencePriorPublishCommand(**fields)


@contextmanager
def reader(s, who="reader", isolation="REPEATABLE READ"):
    engine = s["engines"][who].execution_options(
        isolation_level=isolation, postgresql_readonly=True
    )
    with Session(engine) as session:
        yield session
        session.rollback()


def capture(s, targets=None):
    with reader(s) as session:
        return capture_reference_prior_sources(
            session,
            ReferencePriorCaptureRequest(
                provider_id=s["provider"].id,
                requested_targets=[s["target"]] if targets is None else targets,
            ),
        )


def test_a02_a09_l03_real_scram_publication_and_identical_retry(source):
    s = source
    command = publication(s)
    with Session(s["engines"]["curator"]) as session:
        first = publish_reference_prior(session, command)
        assert first.publication.session.role_name == s["names"]["curator"]
        assert first.publication.session.authentication_method == "scram-sha-256"
        assert first.publication.recorded_at == first.publication.effective_at
        assert first.publication.command.amount.numerator == 1
        session.commit()
    with Session(s["engines"]["curator"]) as session:
        assert publish_reference_prior(session, command) == first
        session.commit()
    snapshot = capture(s)
    result = resolve_reference_priors(snapshot)
    assert result.rows[0].amount.denominator == 2
    assert result.source.frontier.source_generation == 1
    assert result.planner_ready is False


def test_c03_s05_registered_empty_source_is_unavailable(source):
    result = resolve_reference_priors(capture(source))
    assert result.rows[0].reason == "NO_PUBLICATION"
    assert not hasattr(result.rows[0], "amount")
    assert not resolve_reference_priors(capture(source, [])).rows


@pytest.mark.parametrize("who", ["reader", "other", "trust", "password", "root", "admin"])
def test_a01_a04_a05_a09_unauthorized_connection_cannot_publish(source, who):
    with Session(source["engines"][who]) as session, pytest.raises(DBAPIError):
        publish_reference_prior(session, publication(source))


@pytest.mark.parametrize("password", ["incorrect", None])
def test_a09_wrong_or_missing_scram_password(source_server, password):
    s = source_server
    url = s["parsed"].set(database=s["dbname"], username=s["names"]["reader"], password=password)
    engine = create_database_engine(url.render_as_string(hide_password=False))
    try:
        with pytest.raises(OperationalError), engine.connect():
            pass
    finally:
        engine.dispose()


def write(s, command=None):
    with Session(s["engines"]["curator"]) as session:
        receipt = publish_reference_prior(session, command or publication(s))
        session.commit()
        return receipt


def authority(s, who, cap, action, generation=None, key=None):
    with Session(s["engines"]["admin"]) as session:
        if generation is None:
            with Session(s["engines"]["root"]) as root:
                generation = root.scalar(
                    text(
                        "SELECT authority_generation FROM reference_prior_frontiers "
                        "WHERE provider_id=:p"
                    ),
                    {"p": s["provider"].id},
                )
        event = change_reference_prior_authority(
            session,
            dict(
                provider_id=s["provider"].id,
                principal_id=s["principals"][who].id,
                capability=cap,
                action=action,
                expected_authority_generation=generation,
                reason="Synthetic reviewed authority change",
                idempotency_key=key or uuid4().hex,
            ),
        )
        session.commit()
        return event


def test_a05_revoked_retry_denied_before_idempotency(source):
    s = source
    c = publication(s)
    write(s, c)
    old = capture(s)
    authority(s, "curator", "REVIEW_PUBLISH", "REVOKE")
    with (
        Session(s["engines"]["curator"]) as session,
        pytest.raises(DBAPIError, match="capability denied"),
    ):
        publish_reference_prior(session, c)
    assert resolve_reference_priors(old).rows[0].amount.numerator == 1
    fresh = capture(s)
    assert resolve_reference_priors(fresh).rows == resolve_reference_priors(old).rows
    assert fresh.fingerprint() != old.fingerprint()


@pytest.mark.parametrize("who", ["reader", "curator"])
@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO reference_prior_providers(id) VALUES (gen_random_uuid())",
        "UPDATE reference_prior_frontiers SET source_generation=0",
        "DELETE FROM reference_prior_revisions",
        "TRUNCATE reference_prior_authority CASCADE",
        "ALTER FUNCTION menuto_prior.publish(jsonb) RENAME TO forged_publish",
        "CREATE FUNCTION menuto_prior.shadow() RETURNS int LANGUAGE sql AS 'SELECT 1'",
        "SET ROLE menuto_prior_owner",
        "SET ROLE menuto_prior_admin",
        "SELECT menuto_prior.register_provider('{}'::jsonb)",
        "SELECT menuto_prior.enroll_principal('{}'::jsonb)",
        "SELECT menuto_prior.change_authority('{}'::jsonb)",
        "SELECT menuto_prior.receipt(gen_random_uuid())",
    ],
)
def test_a04_m01_direct_sql_privilege_isolation(source, who, sql):
    with Session(source["engines"][who]) as session, pytest.raises(DBAPIError):
        session.execute(text(sql))


@pytest.mark.parametrize(
    "field,value",
    [
        ("actor", "forged"),
        ("reviewer_id", "forged"),
        ("evidence_strength", "HIGH"),
        ("recorded_at", "2000-01-01"),
        ("grant_event_id", str(uuid4())),
        ("status", "REVIEWED"),
    ],
)
def test_a01_a02_l04_raw_sql_rejects_claimed_authority(source, field, value):
    c = canonical(publication(source))
    c[field] = value
    with Session(source["engines"]["curator"]) as session, pytest.raises(DBAPIError):
        session.scalar(text("SELECT menuto_prior.publish(CAST(:c AS jsonb))"), {"c": json.dumps(c)})


@pytest.mark.parametrize(
    "n,d",
    [
        (True, 1),
        (1.0, 2),
        ("1", 2),
        (2, 4),
        (0, 2),
        (1, 0),
        (1, -1),
        (2, 1),
        (2147483648, 2147483648),
    ],
)
def test_c02_raw_sql_independently_rejects_noncanonical_amount(source, n, d):
    c = canonical(publication(source))
    c["amount"].update(numerator=n, denominator=d)
    with Session(source["engines"]["curator"]) as session, pytest.raises(DBAPIError):
        session.scalar(text("SELECT menuto_prior.publish(CAST(:c AS jsonb))"), {"c": json.dumps(c)})


def test_a03_guc_and_set_role_preserve_original_reader_identity(source):
    with Session(source["engines"]["reader"]) as session:
        session.execute(text("SET LOCAL menuto.actor='forged-curator'"))
        session.execute(text("SET LOCAL ROLE menuto_prior_client"))
        with pytest.raises(DBAPIError, match="capability denied"):
            publish_reference_prior(session, publication(source))


def test_a05_provider_and_capability_are_separate(source):
    s = source
    authority(s, "curator", "RETRACT", "REVOKE")
    first = write(s)
    from app.modules.preferences.reference_priors import retract_reference_prior

    c = canonical(first.publication.command)
    c.pop("amount")
    c.update(
        operation="RETRACT",
        expected_provider_generation=1,
        expected_revision=0,
        predecessor_id=str(first.publication.id),
        idempotency_key=uuid4().hex,
    )
    with (
        Session(s["engines"]["curator"]) as session,
        pytest.raises(DBAPIError, match="capability denied"),
    ):
        retract_reference_prior(session, c)
    with Session(s["engines"]["admin"]) as session:
        other = register_reference_prior_provider(
            session,
            dict(
                code=uuid4().hex,
                version="1",
                source_system="review-test",
                remit="Separate provider",
                idempotency_key=uuid4().hex,
            ),
        )
        session.commit()
    with (
        Session(s["engines"]["curator"]) as session,
        pytest.raises(DBAPIError, match="capability denied"),
    ):
        publish_reference_prior(session, publication(s, provider_id=other.id))


def test_l01_l05_s05_lifecycle_and_old_snapshot_replay(source):
    from app.modules.preferences.reference_priors import retract_reference_prior

    s = source
    first = write(s, publication(s, amount=dict(numerator=0, denominator=1)))
    old = capture(s)
    assert resolve_reference_priors(old).rows[0].amount.numerator == 0
    second = write(
        s,
        publication(
            s,
            amount=dict(numerator=-2, denominator=3),
            expected_provider_generation=1,
            expected_revision=0,
            predecessor_id=first.publication.id,
        ),
    )
    c = canonical(second.publication.command)
    c.pop("amount")
    c.update(
        operation="RETRACT",
        expected_provider_generation=2,
        expected_revision=1,
        predecessor_id=str(second.publication.id),
        idempotency_key=uuid4().hex,
    )
    with Session(s["engines"]["curator"]) as session:
        tombstone = retract_reference_prior(session, c)
        session.commit()
    retracted = capture(s)
    assert resolve_reference_priors(retracted).rows[0].reason == "RETRACTED"
    assert not hasattr(tombstone.publication.command, "amount")
    assert resolve_reference_priors(old).rows[0].amount.numerator == 0
    with Session(s["engines"]["curator"]) as session, pytest.raises(DBAPIError, match="No active"):
        retract_reference_prior(
            session,
            dict(
                c,
                expected_provider_generation=3,
                expected_revision=2,
                predecessor_id=str(tombstone.publication.id),
                idempotency_key=uuid4().hex,
            ),
        )
    write(
        s,
        publication(
            s,
            expected_provider_generation=3,
            expected_revision=2,
            predecessor_id=tombstone.publication.id,
        ),
    )
    assert resolve_reference_priors(capture(s)).rows[0].status == "AVAILABLE"
    assert retracted.frontier.source_generation == 3


def test_l02_l03_idempotent_receipt_survives_unrelated_write_and_changed_payload_conflicts(source):
    s = source
    c = publication(s)
    first = write(s, c)
    write(
        s,
        publication(
            s,
            expected_provider_generation=1,
            expected_revision=0,
            predecessor_id=first.publication.id,
        ),
    )
    assert write(s, c) == first
    with (
        Session(s["engines"]["curator"]) as session,
        pytest.raises(DBAPIError, match="Idempotency"),
    ):
        publish_reference_prior(
            session, dict(canonical(c), amount={"numerator": -1, "denominator": 1})
        )
    with Session(s["engines"]["curator"]) as session, pytest.raises(DBAPIError, match="CAS"):
        publish_reference_prior(session, publication(s))
    before = capture(s)
    with Session(s["engines"]["curator"]) as session:
        publish_reference_prior(
            session,
            publication(
                s,
                expected_provider_generation=2,
                expected_revision=1,
                predecessor_id=before.publications[-1].id,
            ),
        )
        session.rollback()
    after = capture(s)
    assert after.frontier == before.frontier and after.publications == before.publications


@pytest.mark.parametrize("mode", ["READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"])
def test_s01_readonly_capture_isolation(source, mode):
    s = source
    with reader(s, isolation=mode) as session:
        req = ReferencePriorCaptureRequest(provider_id=s["provider"].id, requested_targets=[])
        if mode == "READ COMMITTED":
            with pytest.raises(DBAPIError):
                capture_reference_prior_sources(session, req)
        else:
            snapshot = capture_reference_prior_sources(session, req)
            assert snapshot.isolation == mode
            assert session.in_transaction()
    with Session(s["engines"]["reader"]) as session, pytest.raises(DBAPIError):
        capture_reference_prior_sources(session, req)


def test_s01_dirty_capture_denied_before_io(source):
    with reader(source) as session:
        session.add(Ingredient(name="Must not be flushed"))
        with pytest.raises(ValueError, match="Clean"):
            capture_reference_prior_sources(
                session, dict(provider_id=source["provider"].id, requested_targets=[])
            )


@pytest.mark.parametrize(
    "change", ["unknown-target", "unknown-provider", "wrong-source", "future-observation"]
)
def test_t01_t02_l04_fail_closed_requests(source, change):
    s = source
    if change in {"unknown-target", "unknown-provider"}:
        req = dict(provider_id=s["provider"].id, requested_targets=[s["target"]])
        if change == "unknown-target":
            req["requested_targets"] = [dict(kind="INGREDIENT", ingredient_id=uuid4())]
        else:
            req["provider_id"] = uuid4()
        with reader(s) as session, pytest.raises(DBAPIError):
            capture_reference_prior_sources(session, req)
    else:
        c = canonical(publication(s))
        if change == "wrong-source":
            c["provenance"]["source_system"] = "another-provider"
        else:
            c["provenance"]["observed_at"] = canonical(datetime.now(UTC) + timedelta(days=1))
        with Session(s["engines"]["curator"]) as session, pytest.raises(DBAPIError):
            publish_reference_prior(session, c)


def test_a07_empty_rationale_and_provenance_rejected_by_sql(source):
    for field, value in (
        ("review_rationale", "  "),
        ("provenance", {}),
        ("review_rationale", "\u00a0"),
        ("external_record_id", "\u2007"),
        ("source_version", "\u202f"),
        ("external_record_id", "x" * 2049),
        ("source_version", "x" * 201),
    ):
        c = canonical(publication(source))
        if field in {"external_record_id", "source_version"}:
            c["provenance"][field] = value
        else:
            c[field] = value
        with Session(source["engines"]["curator"]) as session, pytest.raises(DBAPIError):
            session.scalar(
                text("SELECT menuto_prior.publish(CAST(:c AS jsonb))"), {"c": json.dumps(c)}
            )


def test_a08_admin_cas_idempotency_and_noop(source):
    s = source
    key = uuid4().hex
    event = authority(s, "other", "CAPTURE", "GRANT", generation=4, key=key)
    assert authority(s, "other", "CAPTURE", "GRANT", generation=4, key=key) == event
    with pytest.raises(DBAPIError, match="no-op"):
        authority(s, "other", "CAPTURE", "GRANT", generation=5)
    with pytest.raises(DBAPIError, match="CAS"):
        authority(s, "other", "CAPTURE", "REVOKE", generation=4)
    authority(s, "other", "CAPTURE", "REVOKE", generation=5)
    with pytest.raises(DBAPIError, match="no-op"):
        authority(s, "other", "CAPTURE", "REVOKE", generation=6)


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"])
@pytest.mark.parametrize("replace", [False, True])
def test_l02_competing_real_publications(source, isolation, replace):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    s = source
    extra = {}
    if replace:
        first = write(s)
        extra = dict(
            expected_provider_generation=1, expected_revision=0, predecessor_id=first.publication.id
        )
    commands = [publication(s, **extra), publication(s, **extra)]
    barrier = Barrier(2)

    def compete(c):
        engine = s["engines"]["curator"].execution_options(isolation_level=isolation)
        try:
            with Session(engine) as session:
                session.scalar(text("SELECT 1"))
                barrier.wait(timeout=5)
                receipt = publish_reference_prior(session, c)
                session.commit()
                return receipt.publication.id
        except DBAPIError as exc:
            assert exc.orig.sqlstate == "40001"
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(compete, commands))
    assert sum(r is not None for r in results) == 1
    snapshot = capture(s)
    assert snapshot.frontier.source_generation == (2 if replace else 1)
    assert resolve_reference_priors(snapshot).rows[0].publication.id in results


@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
@pytest.mark.parametrize("retract", [False, True])
def test_a06_stale_snapshot_after_revoke_aborts_whole_transaction(source, isolation, retract):
    from app.modules.preferences.reference_priors import retract_reference_prior

    s = source
    c = publication(s)
    func = publish_reference_prior
    cap = "REVIEW_PUBLISH"
    if retract:
        first = write(s, c)
        c = canonical(c)
        c.pop("amount")
        c.update(
            operation="RETRACT",
            expected_provider_generation=1,
            expected_revision=0,
            predecessor_id=str(first.publication.id),
            idempotency_key=uuid4().hex,
        )
        cap, func = "RETRACT", retract_reference_prior
    engine = s["engines"]["curator"].execution_options(isolation_level=isolation)
    with Session(engine) as session:
        session.scalar(text("SELECT 1"))
        authority(s, "curator", cap, "REVOKE")
        with pytest.raises(DBAPIError) as exc:
            func(session, c)
        assert exc.value.orig.sqlstate == "40001"
        session.rollback()
    assert capture(s).frontier.source_generation == int(retract)


def wait_for_lock(s, login):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        with s["engines"]["root"].connect() as conn:
            if conn.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname=:db "
                    "AND usename=:who AND wait_event_type='Lock'"
                ),
                {"db": s["dbname"], "who": s["names"][login]},
            ):
                return
        time.sleep(0.01)
    pytest.fail("Contending real connection did not reach provider lock")


@pytest.mark.parametrize("retract", [False, True])
@pytest.mark.parametrize("revoke_first", [False, True])
def test_a06_read_committed_revoke_and_publication_share_frontier(source, retract, revoke_first):
    from concurrent.futures import ThreadPoolExecutor

    from app.modules.preferences.reference_priors import retract_reference_prior

    s = source
    c = publication(s)
    cap, func = "REVIEW_PUBLISH", publish_reference_prior
    if retract:
        first = write(s, c)
        c = canonical(c)
        c.pop("amount")
        c.update(
            operation="RETRACT",
            expected_provider_generation=1,
            expected_revision=0,
            predecessor_id=str(first.publication.id),
            idempotency_key=uuid4().hex,
        )
        cap, func = "RETRACT", retract_reference_prior
    ac = dict(
        provider_id=s["provider"].id,
        principal_id=s["principals"]["curator"].id,
        capability=cap,
        action="REVOKE",
        expected_authority_generation=4,
        reason="Ordered revoke race",
        idempotency_key=uuid4().hex,
    )

    def waiting_call():
        who = "curator" if revoke_first else "admin"
        with Session(s["engines"][who]) as session:
            try:
                result = (
                    func(session, c)
                    if revoke_first
                    else change_reference_prior_authority(session, ac)
                )
                session.commit()
                return result
            except DBAPIError as exc:
                assert revoke_first and exc.orig.sqlstate == "42501"
                return None

    first_who = "admin" if revoke_first else "curator"
    with Session(s["engines"][first_who]) as holder, ThreadPoolExecutor(max_workers=1) as pool:
        if revoke_first:
            change_reference_prior_authority(holder, ac)
        else:
            func(holder, c)
        future = pool.submit(waiting_call)
        try:
            wait_for_lock(s, "curator" if revoke_first else "admin")
        finally:
            holder.commit()
        result = future.result(timeout=5)
    assert (result is None) == revoke_first
    snapshot = capture(s)
    assert snapshot.frontier.source_generation == int(retract) + int(not revoke_first)
    resolve_reference_priors(snapshot)


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"])
def test_a08_competing_admin_grant_revoke_have_one_cas_winner(source, isolation):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    s = source
    authority(s, "other", "REVIEW_PUBLISH", "GRANT")
    barrier = Barrier(2)

    def compete(cap_action):
        cap, action = cap_action
        engine = s["engines"]["admin"].execution_options(isolation_level=isolation)
        with Session(engine) as session:
            session.scalar(text("SELECT 1"))
            barrier.wait(timeout=5)
            try:
                change_reference_prior_authority(
                    session,
                    dict(
                        provider_id=s["provider"].id,
                        principal_id=s["principals"]["other"].id,
                        capability=cap,
                        action=action,
                        expected_authority_generation=5,
                        reason="Concurrent admin acceptance",
                        idempotency_key=uuid4().hex,
                    ),
                )
                session.commit()
                return True
            except DBAPIError as exc:
                assert exc.orig.sqlstate == "40001"
                return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(compete, [("CAPTURE", "GRANT"), ("REVIEW_PUBLISH", "REVOKE")])) == 1
    assert capture(s).frontier.authority_generation == 6


def test_t01_s02_all_five_exact_identities_and_complete_unrequested_history(source):
    from app.modules.catalog.public import add_affinity_feature_term
    from app.modules.recipes.models import Recipe
    from preference_fixtures import term

    s = source
    with Session(s["engines"]["root"]) as session:
        recipe = Recipe(name="Exact stable recipe", cooking_method="synthetic")
        session.add(recipe)
        terms = [term(k) for k in ("PROTEIN", "METHOD", "FLAVOR")]
        for t in terms:
            add_affinity_feature_term(session, t)
        session.commit()
        targets = [
            s["target"],
            dict(kind="DIRECT_RECIPE", recipe_id=recipe.id),
            *[dict(kind=t.kind, feature_term_id=t.id) for t in terms],
        ]
    for seq, target in enumerate(targets):
        write(s, publication(s, target=target, expected_provider_generation=seq))
    snapshot = capture(s)
    assert len(snapshot.publications) == len(snapshot.streams) == len(snapshot.identities) == 5
    assert len(resolve_reference_priors(snapshot).rows) == 1
    assert {i.target.kind for i in snapshot.identities} == {
        "INGREDIENT",
        "DIRECT_RECIPE",
        "PROTEIN",
        "METHOD",
        "FLAVOR",
    }
    bad = dict(kind="FLAVOR", feature_term_id=terms[0].id)
    with reader(s) as session, pytest.raises(DBAPIError, match="TARGET_NOT_REVIEWED"):
        capture_reference_prior_sources(
            session, dict(provider_id=s["provider"].id, requested_targets=[bad])
        )
    draft = term("METHOD", status="DRAFT")
    with Session(s["engines"]["root"]) as session:
        add_affinity_feature_term(session, draft)
        session.commit()
    with reader(s) as session, pytest.raises(DBAPIError, match="TARGET_NOT_REVIEWED"):
        capture_reference_prior_sources(
            session,
            dict(
                provider_id=s["provider"].id,
                requested_targets=[dict(kind="METHOD", feature_term_id=draft.id)],
            ),
        )


def rehash_parts(parts):
    """Adversary rehashes caches; semantic contradictions must still fail replay."""
    from app.modules.preferences.reference_prior_contracts import prior_hash

    for e in parts["authority_events"]:
        e["command_hash"] = prior_hash("prior.authority-command.v1", e["command"])
        e["fact_hash"] = prior_hash(
            "prior.authority.v1", {k: v for k, v in e.items() if k != "fact_hash"}
        )
    for p in parts["publications"]:
        p["command_hash"] = prior_hash("prior.publication-command.v1", p["command"])
        p["fact_hash"] = prior_hash(
            "prior.publication.v1", {k: v for k, v in p.items() if k != "fact_hash"}
        )
    children = {e["id"]: e for e in parts["authority_events"] + parts["publications"]}
    previous = None
    for m in sorted(parts["mutations"], key=lambda v: v["mutation_sequence"]):
        if m["child_id"] in children:
            m["child_hash"] = children[m["child_id"]]["fact_hash"]
        m["predecessor_hash"] = previous
        m["journal_hash"] = prior_hash(
            "prior.mutation.v1", {k: v for k, v in m.items() if k != "journal_hash"}
        )
        previous = m["journal_hash"]
    parts["frontier"]["mutation_head_hash"] = previous
    return parts


@pytest.mark.parametrize(
    "attack",
    [
        "drop-pub",
        "drop-authority",
        "drop-journal",
        "duplicate-pub",
        "forge-head",
        "forge-frontier",
        "forge-identity",
        "old-grant",
        "forge-binding",
        "forge-sequence",
        "forge-predecessor",
        "extra-field",
    ],
)
def test_s03_rehashed_primitive_forgery_rejected(source, attack):
    from pydantic import ValidationError

    s = source
    write(s)
    parts = canonical(capture(s))
    if attack == "drop-pub":
        parts["publications"] = []
    elif attack == "drop-authority":
        parts["authority_events"].pop(0)
    elif attack == "drop-journal":
        parts["mutations"].pop(0)
    elif attack == "duplicate-pub":
        parts["publications"].append(parts["publications"][0])
    elif attack == "forge-head":
        parts["streams"][0]["head_revision"] = 99
    elif attack == "forge-frontier":
        parts["frontier"]["source_generation"] = 0
    elif attack == "forge-identity":
        parts["identities"][0]["identity"]["id"] = str(uuid4())
    elif attack == "forge-binding":
        parts["publications"][0]["session"]["role_oid"] += 1
    elif attack == "forge-sequence":
        parts["publications"][0]["source_sequence"] += 1
    elif attack == "forge-predecessor":
        parts["publications"][0]["command"]["predecessor_id"] = str(uuid4())
    elif attack == "extra-field":
        parts["publications"][0]["command"]["reviewer_id"] = str(uuid4())
    else:
        authority(s, "curator", "REVIEW_PUBLISH", "REVOKE")
        parts = canonical(capture(s))
        pub, revoke = parts["publications"][0], parts["authority_events"][-1]
        # Move a real publication after revocation while pinning its formerly valid grant.
        pub["mutation_sequence"], revoke["mutation_sequence"] = (
            revoke["mutation_sequence"],
            pub["mutation_sequence"],
        )
        pub["authority_generation"] = 5
        timestamp = pub["recorded_at"]
        revoke["recorded_at"] = timestamp
        for m in parts["mutations"]:
            if m["kind"] == "PUBLICATION":
                m["mutation_sequence"] = pub["mutation_sequence"]
            elif m["child_id"] == revoke["id"]:
                m["mutation_sequence"] = revoke["mutation_sequence"]
                m["recorded_at"] = timestamp
    with pytest.raises((ValidationError, ValueError)):
        resolve_reference_priors(rehash_parts(parts))


def test_s04_s06_permutations_and_offline_origin_boundary(source):
    from app.modules.preferences.reference_prior_contracts import prior_hash

    s = source
    write(s)
    snapshot = capture(s)
    parts = canonical(snapshot)
    for field in (
        "principals",
        "authority_events",
        "publications",
        "mutations",
        "streams",
        "identities",
    ):
        parts[field].reverse()
    assert resolve_reference_priors(parts) == resolve_reference_priors(snapshot)
    # Coherent forged content can pass offline replay; this does not certify origin.
    parts["provider"]["command"]["remit"] = "A wholly forged but coherent reference remit"
    parts["provider"]["command_hash"] = prior_hash(
        "prior.provider-command.v1", parts["provider"]["command"]
    )
    forged = resolve_reference_priors(parts)
    assert forged.source_fingerprint != snapshot.fingerprint()
    assert forged.rows == resolve_reference_priors(snapshot).rows


def test_a03_m01_drop_recreate_and_rotation_requires_new_binding(source):
    from psycopg import sql

    s = source
    authority(s, "other", "REVIEW_PUBLISH", "GRANT")
    name = s["names"]["other"]
    s["engines"]["other"].dispose()
    with s["engines"]["root"].connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        with conn.connection.driver_connection.cursor() as cur:
            cur.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))
            cur.execute("SET password_encryption='scram-sha-256'")
            cur.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(name), sql.Literal(s["passwords"]["other"])
                )
            )
            cur.execute(sql.SQL("GRANT menuto_prior_client TO {}").format(sql.Identifier(name)))
    with Session(s["engines"]["other"]) as session, pytest.raises(DBAPIError, match="not enrolled"):
        publish_reference_prior(session, publication(s))
    with (
        Session(s["engines"]["admin"]) as session,
        pytest.raises(DBAPIError, match="binding conflict"),
    ):
        enroll_reference_prior_principal(
            session, dict(role_name=name, idempotency_key="enroll-other")
        )
    with Session(s["engines"]["admin"]) as session:
        rotated = enroll_reference_prior_principal(
            session, dict(role_name=name, idempotency_key=uuid4().hex)
        )
        session.commit()
    assert rotated.role_oid != s["principals"]["other"].role_oid
    assert rotated.id != s["principals"]["other"].id
    # Old grant remains attached to the old binding. No authority silently transfers.
    with (
        Session(s["engines"]["other"]) as session,
        pytest.raises(DBAPIError, match="capability denied"),
    ):
        publish_reference_prior(session, publication(s))
    # Revoke the old binding, then grant the rotated binding explicitly.
    authority(s, "other", "REVIEW_PUBLISH", "REVOKE")
    with Session(s["engines"]["admin"]) as session:
        change_reference_prior_authority(
            session,
            dict(
                provider_id=s["provider"].id,
                principal_id=rotated.id,
                capability="REVIEW_PUBLISH",
                action="GRANT",
                expected_authority_generation=6,
                reason="Explicit rotated binding grant",
                idempotency_key=uuid4().hex,
            ),
        )
        session.commit()
    with Session(s["engines"]["other"]) as session:
        receipt = publish_reference_prior(session, publication(s))
        assert receipt.publication.principal_id == rotated.id
        session.commit()
    resolve_reference_priors(capture(s))
    s["principals"]["other"] = rotated


def test_f02_cached_results_and_boolean_scope_flags_cannot_be_minted(source):
    from app.modules.preferences.reference_prior_contracts import (
        ReviewedReferencePriorDraft,
        prior_hash,
    )
    from pydantic import ValidationError

    write(source)
    result = resolve_reference_priors(capture(source))
    for field, value in (
        ("planner_ready", True),
        ("activation_ready", 0),
        ("evidence_strength", "HIGH"),
        ("shrinkage", "AVAILABLE"),
    ):
        parts = canonical(result)
        parts[field] = value
        with pytest.raises(ValidationError):
            ReviewedReferencePriorDraft.model_validate(parts)
    parts = canonical(result)
    parts["rows"][0]["amount"]["numerator"] = -1
    parts["result_fingerprint"] = prior_hash(
        "reviewed-reference-prior.v1", dict(source=parts["source"], rows=parts["rows"])
    )
    with pytest.raises(ValidationError):
        ReviewedReferencePriorDraft.model_validate(parts)
    parts = canonical(result.source)
    parts["read_only"] = 1
    with pytest.raises(ValidationError):
        resolve_reference_priors(parts)


def test_t03_providers_can_disagree_without_aggregation(source):
    s = source
    write(s)
    with Session(s["engines"]["admin"]) as session:
        provider = register_reference_prior_provider(
            session,
            dict(
                code=uuid4().hex,
                version="1",
                source_system="review-test",
                remit="Independent reference",
                idempotency_key=uuid4().hex,
            ),
        )
        for generation, (who, cap) in enumerate(
            (("curator", "REVIEW_PUBLISH"), ("reader", "CAPTURE"))
        ):
            change_reference_prior_authority(
                session,
                dict(
                    provider_id=provider.id,
                    principal_id=s["principals"][who].id,
                    capability=cap,
                    action="GRANT",
                    expected_authority_generation=generation,
                    reason="Second provider grant",
                    idempotency_key=uuid4().hex,
                ),
            )
        session.commit()
    other = dict(s, provider=provider)
    write(other, publication(other, amount=dict(numerator=-1, denominator=1)))
    assert resolve_reference_priors(capture(s)).rows[0].amount.numerator == 1
    assert resolve_reference_priors(capture(other)).rows[0].amount.numerator == -1


@pytest.mark.parametrize(
    "uri",
    [
        "https://reference.example/artifact/v1?revision=1#review",
        "http://127.0.0.1:8080/reference.json",
    ],
)
def test_a07_sql_locator_round_trips_without_parser_rewriting(source, uri):
    c = canonical(publication(source))
    c["provenance"]["source_uri"] = uri
    with Session(source["engines"]["curator"]) as session:
        raw = session.scalar(
            text("SELECT menuto_prior.publish(CAST(:c AS jsonb))"), {"c": json.dumps(c)}
        )
        assert raw["publication"]["command"]["provenance"]["source_uri"] == uri
        session.commit()
    resolve_reference_priors(capture(source))


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.com",
        "https://EXAMPLE.com/",
        "https://x:443/",
        "https://x/../artifact",
        "http://127.1/",
        "http://example.1/",
        "http://x:99999/",
        "https://user:secret@x/",
    ],
)
def test_a07_sql_rejects_noncanonical_locator_before_it_can_poison_capture(source, uri):
    c = canonical(publication(source))
    c["provenance"]["source_uri"] = uri
    with Session(source["engines"]["curator"]) as session, pytest.raises(DBAPIError):
        session.scalar(text("SELECT menuto_prior.publish(CAST(:c AS jsonb))"), {"c": json.dumps(c)})
    assert capture(source).frontier.source_generation == 0


def test_s01_even_a_manually_assigned_write_xid_cannot_claim_clean_capture(source):
    with reader(source) as session:
        session.scalar(text("SELECT pg_current_xact_id()"))
        with pytest.raises(DBAPIError, match="Clean read-only"):
            capture_reference_prior_sources(
                session, dict(provider_id=source["provider"].id, requested_targets=[])
            )


def test_l04_equal_timestamps_are_ordered_by_actual_sequences(source):
    write(source)
    parts = canonical(capture(source))
    instant = parts["publications"][0]["recorded_at"]
    for event in parts["authority_events"]:
        event["recorded_at"] = instant
    for pub in parts["publications"]:
        pub["recorded_at"] = pub["effective_at"] = instant
    for mutation in parts["mutations"]:
        mutation["recorded_at"] = instant
    result = resolve_reference_priors(rehash_parts(parts))
    assert result.source.frontier.mutation_generation == 5
    assert result.rows[0].status == "AVAILABLE"


def test_a08_admin_rollback_leaves_authority_and_mutation_unchanged(source):
    s = source
    before = capture(s)
    with Session(s["engines"]["admin"]) as session:
        change_reference_prior_authority(
            session,
            dict(
                provider_id=s["provider"].id,
                principal_id=s["principals"]["reader"].id,
                capability="CAPTURE",
                action="REVOKE",
                expected_authority_generation=4,
                reason="Rolled back administration",
                idempotency_key=uuid4().hex,
            ),
        )
        session.rollback()
    after = capture(s)
    assert after.frontier == before.frontier
    assert after.authority_events == before.authority_events


def test_l04_clock_regression_fails_without_fabricating_ticks(source):
    s = source
    # Trusted test root simulates a provider registration ahead of the physical clock;
    # no OS clock changes and no frozen owner data are involved.
    with s["engines"]["root"].begin() as conn:
        conn.execute(text("ALTER TABLE reference_prior_providers DISABLE TRIGGER prior_immutable"))
        conn.execute(
            text(
                "UPDATE reference_prior_providers SET recorded_at="
                "clock_timestamp()+interval '1 day' "
                "WHERE id=:p"
            ),
            {"p": s["provider"].id},
        )
        conn.execute(text("ALTER TABLE reference_prior_providers ENABLE TRIGGER prior_immutable"))
    with (
        Session(s["engines"]["curator"]) as session,
        pytest.raises(DBAPIError, match="clock regression"),
    ):
        publish_reference_prior(session, publication(s))
    with s["engines"]["root"].connect() as conn:
        assert (
            conn.scalar(
                text(
                    "SELECT source_generation FROM reference_prior_frontiers WHERE provider_id=:p"
                ),
                {"p": s["provider"].id},
            )
            == 0
        )
