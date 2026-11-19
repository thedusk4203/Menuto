"""Actual PostgreSQL Identity fixtures. All logins, content and secrets are TEST_ONLY."""

import json
import os
import secrets
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from app.modules.identity.models import User
from app.modules.identity.source_capture import IdentityDeploymentContext
from identity_source_fixtures import available_source
from psycopg import sql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from test_postgres_foundation import seed_household

ROOT = Path(__file__).resolve().parents[3]


@dataclass
class IdentityScenario:
    server: object
    name: str
    url: object
    root_id: str = field(default_factory=lambda: str(uuid4()))
    issuer_id: str = field(default_factory=lambda: str(uuid4()))
    binding_id: str = field(default_factory=lambda: str(uuid4()))
    grant_id: str = field(default_factory=lambda: str(uuid4()))
    credentials: dict = field(default_factory=dict, repr=False)
    roles: dict = field(default_factory=dict)
    commands: dict = field(default_factory=dict)
    receipts: dict = field(default_factory=dict)
    engines: list = field(default_factory=list, repr=False)
    raw: dict | None = None
    issuer_user_id: str | None = None
    user_id: str | None = None
    household_id: str | None = None
    member_id: str | None = None

    def connect(self, actor="bootstrap", **options):
        params = dict(self.url.query)
        params.update(
            host=self.url.host,
            port=self.url.port,
            dbname=self.name,
            user=self.roles[actor],
            password=self.credentials[actor],
            connect_timeout=3,
            autocommit=True,
        )
        params.update(options)
        return psycopg.connect(**params)

    def engine(self, actor="requester", *, readonly=True, isolation="REPEATABLE READ"):
        engine = create_engine(
            self.url.set(username=self.roles[actor], password=self.credentials[actor])
        )
        if readonly:
            engine = engine.execution_options(isolation_level=isolation, postgresql_readonly=True)
        self.engines.append(engine)
        return engine

    def body(self, kind, action, hours=1, **extra):
        identity = {
            "ROOT": {},
            "ISSUER": dict(
                issuer_id=self.issuer_id,
                user_id=self.issuer_user_id,
                role_name=self.roles["issuer"],
                capability="BINDINGS_AND_SCOPE_GRANTS",
            ),
            "BINDING": dict(
                binding_id=self.binding_id,
                issuer_id=self.issuer_id,
                user_id=self.user_id,
                role_name=self.roles["requester"],
            ),
            "OPERATION_GRANT": dict(
                grant_id=self.grant_id,
                binding_id=self.binding_id,
                issuer_id=self.issuer_id,
                household_id=self.household_id,
                tracked_member_id=self.member_id,
                operation="CAPTURE_EXPLICIT_PLAN_INTENT",
            ),
        }[kind]
        value = dict(
            version=1,
            root_id=self.root_id,
            idempotency_key=str(uuid4()),
            expected_revision=0,
            predecessor_id=None,
            evidence_id="TEST_ONLY",
            evidence_version="v1",
            evidence_preimage="TEST_ONLY Identity source assertion",
            environment="TEST_ONLY",
            kind=kind,
            action=action,
            effective=None
            if action == "REVOKE"
            else dict(
                version=1,
                mode="IMMEDIATE",
                start=None,
                end=(datetime.now(UTC) + timedelta(hours=hours)).isoformat(),
            ),
        )
        return value | identity | extra

    def append(self, body, *, actor=None):
        entries = {
            "ROOT": "bootstrap_root",
            "ISSUER": "change_issuer",
            "BINDING": "change_binding",
            "OPERATION_GRANT": "change_operation_grant",
        }
        actor = actor or ("bootstrap" if body["kind"] in {"ROOT", "ISSUER"} else "issuer")
        with self.connect(actor) as db, db.transaction():
            receipt = db.execute(
                sql.SQL("SELECT menuto_identity_source.{}(%s)").format(
                    sql.Identifier(entries[body["kind"]])
                ),
                (json.dumps(body),),
            ).fetchone()[0]
        self.commands[body["kind"]] = body
        self.receipts[body["kind"]] = receipt
        return receipt

    def capture(
        self, request=None, *, actor="requester", isolation="REPEATABLE READ", readonly=True
    ):
        with self.connect(actor) as db, db.transaction():
            db.execute(
                sql.SQL("SET TRANSACTION ISOLATION LEVEL {} {}").format(
                    sql.SQL(isolation), sql.SQL("READ ONLY" if readonly else "READ WRITE")
                )
            )
            return db.execute(
                "SELECT menuto_identity_source.capture_request_source(%s)",
                (json.dumps(request or self.raw),),
            ).fetchone()[0]

    def counts(self):
        with self.connect() as db:
            return tuple(
                db.execute(
                    sql.SQL("SELECT count(*) FROM menuto_identity_source.{}").format(
                        sql.Identifier(name)
                    )
                ).fetchone()[0]
                for name in (
                    "roots",
                    "issuers",
                    "principal_bindings",
                    "operation_grants",
                    "frontiers",
                    "command_receipts",
                )
            )

    def context(self):
        with self.connect() as db:
            oid = db.execute(
                "SELECT oid FROM pg_database WHERE datname=current_database()"
            ).fetchone()[0]
            address, port = db.execute(
                "SELECT host(inet_server_addr()),inet_server_port()"
            ).fetchone()
        return IdentityDeploymentContext(
            root_id=self.root_id,
            database_oid=oid,
            database_name=self.name,
            endpoint_id=f"PG18:{oid}:{address}:{port}",
            host=self.url.host,
            sslrootcert=self.url.query["sslrootcert"],
        )

    def provision(self, *, lifetimes=None):
        engine = self.engine("bootstrap", readonly=False)
        with Session(engine) as session:
            issuer = User(display_name="TEST_ONLY Identity issuer")
            session.add(issuer)
            session.flush()
            actor, result = seed_household(session)
            self.issuer_user_id = str(issuer.id)
            self.user_id, self.household_id, self.member_id = map(
                str, (actor.id, result.household_id, result.member_id)
            )
            session.commit()
        origin = datetime.now(UTC)
        durations = lifetimes or (86400, 43200, 21600, 10800)
        for kind, action, seconds in zip(
            ("ROOT", "ISSUER", "BINDING", "OPERATION_GRANT"),
            ("INITIALIZE", "ENROLL", "ENROLL", "GRANT"),
            durations,
            strict=True,
        ):
            end = (origin + timedelta(seconds=seconds)).isoformat()
            self.append(
                self.body(
                    kind, action, effective=dict(version=1, mode="IMMEDIATE", start=None, end=end)
                )
            )
        request = available_source()["binding"]
        child = json.loads(request["request_utf8"])
        child["context"].update(
            actor_user_id=self.user_id,
            household_id=self.household_id,
            tracked_member_id=self.member_id,
        )
        raw = json.dumps(child, ensure_ascii=False, separators=(",", ":"))
        import hashlib

        request.update(
            actor_user_id=self.user_id,
            household_id=self.household_id,
            tracked_member_id=self.member_id,
            request_utf8=raw,
            request_preimage_fingerprint=hashlib.sha256(
                b"identity.request-preimage.v1\x00" + raw.encode()
            ).hexdigest(),
        )
        self.raw = request
        return self


@pytest.fixture(scope="module")
def identity_server():
    raw = os.environ.get("MENUTO_TEST_POSTGRES_URL")
    if not raw:
        pytest.fail("ITR requires actual disposable PostgreSQL18.4; no mock/skip substitution")
    url = make_url(raw)
    assert url.host in {"127.0.0.1", "localhost", "::1"} and url.database == "postgres"
    assert url.query.get("sslmode") == "verify-full" and url.query.get("sslrootcert")
    maintenance = create_engine(url).execution_options(isolation_level="AUTOCOMMIT")
    template = "itr_template_" + uuid4().hex
    with maintenance.connect() as db:
        assert db.scalar(text("SHOW server_version_num")) == "180004"
        db.exec_driver_sql(f'CREATE DATABASE "{template}"')
    engine = create_engine(url.set(database=template))
    cfg = Config(str(ROOT / "alembic.ini"))
    with engine.connect() as db:
        cfg.attributes["connection"] = db
        command.upgrade(cfg, "head")
        db.commit()
    engine.dispose()
    server = dict(url=url, maintenance=maintenance, template=template)
    try:
        yield server
    finally:
        with maintenance.connect() as db:
            db.exec_driver_sql(f'DROP DATABASE "{template}" WITH (FORCE)')
        maintenance.dispose()


@contextmanager
def new_identity_scenario(server, *, provision=True, fresh=False):
    url, admin = server["url"], server["maintenance"]
    name = "itr_test_" + uuid4().hex
    scenario = IdentityScenario(server, name, url.set(database=name))
    scenario.roles["bootstrap"], scenario.credentials["bootstrap"] = url.username, url.password
    with admin.connect() as db:
        if fresh:
            db.exec_driver_sql(f'CREATE DATABASE "{name}"')
            engine = create_engine(url.set(database=name))
            cfg = Config(str(ROOT / "alembic.ini"))
            with engine.connect() as source:
                cfg.attributes["connection"] = source
                command.upgrade(cfg, "head")
                source.commit()
            engine.dispose()
        else:
            db.exec_driver_sql(f'CREATE DATABASE "{name}" TEMPLATE "{server["template"]}"')
        for actor in ("issuer", "requester"):
            role = "itr_" + actor + "_" + uuid4().hex[:16]
            password = secrets.token_urlsafe(24)
            scenario.roles[actor], scenario.credentials[actor] = role, password
            cur = db.connection.driver_connection.cursor()
            cur.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )
            cur.execute(
                sql.SQL("GRANT {} TO {} WITH INHERIT TRUE, SET FALSE, ADMIN FALSE").format(
                    sql.Identifier("menuto_identity_" + actor), sql.Identifier(role)
                )
            )
            cur.close()
        db.exec_driver_sql(f'GRANT menuto_identity_bootstrap TO "{url.username}"')
    try:
        yield scenario.provision() if provision else scenario
    finally:
        for engine in scenario.engines:
            engine.dispose()
        with admin.connect() as db:
            db.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
            for actor in ("requester", "issuer"):
                cur = db.connection.driver_connection.cursor()
                cur.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(scenario.roles[actor])))
                cur.close()


@pytest.fixture
def identity_scenario(identity_server):
    with new_identity_scenario(identity_server) as scenario:
        yield scenario


@contextmanager
def identity_hba_method(scenario, method):
    """Trusted disposable fixture only; original file is restored even on assertion failure."""
    import time

    with scenario.connect() as admin:
        path = admin.execute("SHOW hba_file").fetchone()[0]
        original = admin.execute("SELECT pg_read_file(%s)", (path,)).fetchone()[0]
        actual_address = admin.execute("SELECT host(inet_client_addr())").fetchone()[0]
        assert actual_address is not None
        address = ip_address(actual_address)
        addresses = {"127.0.0.1/32", "::1/128", f"{address}/{address.max_prefixlen}"}
        body = "".join(
            f"host {scenario.name} {scenario.roles['requester']} {cidr} {method}\n"
            for cidr in sorted(addresses)
        ) + original

        def write(value):
            oid = admin.execute(
                "SELECT lo_from_bytea(0,convert_to(%s,'UTF8'))", (value,)
            ).fetchone()[0]
            try:
                admin.execute("SELECT lo_export(%s,%s)", (oid, path))
            finally:
                admin.execute("SELECT lo_unlink(%s)", (oid,))
            admin.execute("SELECT pg_reload_conf()")
            time.sleep(0.2)

        try:
            write(body)
            yield
        finally:
            write(original)
