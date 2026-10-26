"""Real hierarchy SCRAM/TLS roles and isolated source database; no impersonated actors."""

import os
import secrets
import time
from ipaddress import ip_address
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.modules.catalog.models import Ingredient
from app.modules.preferences.hierarchy_contracts import HierarchyProvenance
from app.modules.preferences.hierarchy_sources import (
    capture_hierarchy_sources,
    change_hierarchy_authority,
    enroll_hierarchy_principal,
    publish_hierarchy_source,
    register_hierarchy_provider,
)
from app.persistence.database import create_database_engine
from hierarchy_fixtures import policy as authored_policy
from preference_fixtures import provenance
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def hierarchy_server():
    url = os.environ.get("MENUTO_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set MENUTO_TEST_POSTGRES_URL for isolated real PostgreSQL/SCRAM acceptance")
    parsed = make_url(url)
    assert parsed.host in {"localhost", "127.0.0.1", "::1"} and parsed.database == "postgres"
    maintenance = create_database_engine(url).execution_options(isolation_level="AUTOCOMMIT")
    dbname = "hierarchy_test_" + uuid4().hex
    names = {
        k: "hierarchy_" + k + "_" + uuid4().hex[:12]
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
                assert conn.scalar(text(f"SELECT count(*) FROM hierarchy_source_{table}")) == 0
            command.check(config)
            conn.commit()
            command.downgrade(config, "0014")
            conn.commit()
            assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0014"
            command.upgrade(config, "head")
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
                    group = "menuto_hierarchy_admin" if k == "admin" else "menuto_hierarchy_client"
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
                k: enroll_hierarchy_principal(
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


def capture(s, targets=None, *, who="reader", isolation="REPEATABLE READ"):
    with Session(
        s["engines"][who].execution_options(isolation_level=isolation, postgresql_readonly=True)
    ) as session:
        return capture_hierarchy_sources(
            session,
            dict(
                provider_id=s["provider"].id,
                policy_id=s["policy"].policy_id,
                requested_targets=[s["target"]] if targets is None else targets,
            ),
        )


@pytest.fixture
def hierarchy_source(hierarchy_server):
    s = hierarchy_server
    with Session(s["engines"]["admin"]) as session:
        provider = register_hierarchy_provider(
            session,
            dict(
                code="synthetic." + uuid4().hex,
                version="1",
                source_system="hierarchy.test",
                remit="Synthetic test only",
                idempotency_key=uuid4().hex,
            ),
        )
        generation = 0
        for who, caps in (
            ("curator", ("REVIEW_PUBLISH", "RETRACT", "CAPTURE")),
            ("reader", ("CAPTURE",)),
        ):
            for cap in caps:
                change_hierarchy_authority(
                    session,
                    dict(
                        provider_id=provider.id,
                        principal_id=s["principals"][who].id,
                        capability=cap,
                        action="GRANT",
                        expected_authority_generation=generation,
                        reason="Synthetic grant",
                        idempotency_key=uuid4().hex,
                    ),
                )
                generation += 1
        session.commit()
    with Session(s["engines"]["root"]) as session:
        destination = Ingredient(name="Synthetic exact destination")
        session.add(destination)
        session.commit()
        target = dict(kind="INGREDIENT", ingredient_id=str(destination.id))
    return dict(
        s,
        provider=provider,
        policy=authored_policy(source_kind="INGREDIENT", destination_kind="INGREDIENT"),
        destination=target,
    )


def publication(
    s, *, identity=None, policy=None, relation=None, operation="REPLACE", old=None, key=None
):
    source = capture(s)
    return dict(
        provider_id=s["provider"].id,
        identity=identity
        or dict(
            kind="POLICY",
            policy_id=s["policy"].policy_id,
            source=None,
            destination=None,
            recipe_bindings=[],
        ),
        operation=operation,
        policy=policy
        if policy is not None
        else (
            s["policy"]
            if relation is None and operation == "REPLACE" and identity is None
            else None
        ),
        relation=relation,
        provenance=HierarchyProvenance(
            **(
                provenance(kind="REVIEWED_REFERENCE").model_dump()
                | dict(source_system="hierarchy.test", content_hash="a" * 64)
            )
        ),
        review_rationale="Synthetic reviewed permission, no member data",
        expected_provider_generation=source.frontier.source_generation,
        expected_mutation_head_hash=source.frontier.mutation_head_hash,
        expected_revision=old.publication.revision if old else -1,
        predecessor_id=old.publication.id if old else None,
        idempotency_key=key or uuid4().hex,
    )


def publish(s, command, who="curator"):
    with Session(s["engines"][who].execution_options(isolation_level="SERIALIZABLE")) as session:
        receipt = publish_hierarchy_source(session, command)
        session.commit()
        return receipt
