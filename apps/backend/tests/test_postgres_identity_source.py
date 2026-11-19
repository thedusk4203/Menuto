"""ITR real PostgreSQL source authority and exact routine classification proofs."""

import copy
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from app.modules.identity.source_replay import validate_identity_source_v1
from app.modules.planning.identity_source_inspection import (
    inspect_authenticated_explicit_plan_intent_v1,
)
from app.modules.validation.identity_source import check_identity_source_v1
from identity_postgres_fixtures import identity_scenario, identity_server  # noqa: F401
from identity_source_fixtures import h
from psycopg import sql

pytestmark = pytest.mark.postgres


def _checked(scenario):
    retained = scenario.capture()
    assert retained["outcome"] == "AVAILABLE_AT_RETAINED_CUT"
    assert validate_identity_source_v1(retained, scenario.raw).outcome == retained["outcome"]
    report = check_identity_source_v1(retained, scenario.raw)
    assert report.decision == "CONSISTENT" and report.numerical_use == "NOT_ADMITTED"
    return retained


def test_itr007_positive_scoped_capture(identity_scenario):  # noqa: F811
    s = identity_scenario
    retained = _checked(s)
    with s.engine().connect() as db, db.begin():
        result = inspect_authenticated_explicit_plan_intent_v1(db, s.raw, context=s.context())
    assert result.outcome == "SOURCE_AND_INTENT_CONSISTENT", (
        result.reason,
        result.source_check,
        result.intent_result.outcome if result.intent_result else None,
        result.intent_check,
    )
    assert result.transport == "UNVERIFIED_TRANSPORT" and result.numerical_use == "NOT_ADMITTED"
    assert not result.planner_ready and not result.activation_ready
    assert retained["frame"]["total_fact_count"] == 4


def test_itr018_legacy_trigger_context(identity_scenario):  # noqa: F811
    s = identity_scenario
    retained = _checked(s)
    routines = [
        o
        for o in retained["frame"]["session_start"]["objects"]
        if o["kind"] == "FUNCTION" and o["schema_name"] == "public"
    ]
    assert len(routines) == 68 and len({o["object_oid"] for o in routines}) == 68
    with s.connect() as db, db.transaction():
        db.execute("SET TRANSACTION READ ONLY")
        db.execute("SET LOCAL ROLE menuto_identity_source_owner")
        db.execute("SET LOCAL search_path=pg_catalog,menuto_identity_source,pg_temp")
        for (signature,) in db.execute("""SELECT p.oid::regprocedure::text FROM pg_proc p
            JOIN pg_namespace n ON n.oid=p.pronamespace
            WHERE n.nspname='public' AND p.prorettype='trigger'::regtype
            ORDER BY p.oid""").fetchall():
            with pytest.raises(psycopg.Error) as error, db.transaction():
                db.execute("SELECT public." + signature.removeprefix("public."))
            assert error.value.sqlstate == "0A000"
    assert s.counts()[:4] == (1, 1, 1, 1)


def test_itr019_no_direct_source_access(identity_scenario):  # noqa: F811
    s = identity_scenario
    with s.connect() as admin:
        for actor in ("issuer", "requester"):
            permissions = admin.execute(
                """SELECT c.relname,
                has_table_privilege(%s,c.oid,
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
                FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname='menuto_identity_source' AND c.relkind='r'""",
                (s.roles[actor],),
            ).fetchall()
            assert len(permissions) == 6 and not any(x[1] for x in permissions)
            assert not admin.execute(
                (
                    "SELECT has_sequence_privilege(%s,'menuto_identity_source.recorde"
                    "d_order','USAGE,SELECT,UPDATE')"
                ),
                (s.roles[actor],),
            ).fetchone()[0]
        prior = admin.execute("""
            SELECT has_function_privilege('menuto_identity_source_owner',p.oid,'EXECUTE')
            FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
            WHERE n.nspname='menuto_prior'
            AND NOT EXISTS(SELECT FROM pg_depend d
                WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid
             AND d.refclassid='pg_extension'::regclass AND d.deptype='e')""").fetchall()
        assert len(prior) == 35 and not any(x[0] for x in prior)
    with s.connect("requester") as db:
        for statement in (
            "SELECT * FROM menuto_identity_source.roots",
            "INSERT INTO menuto_identity_source.roots DEFAULT VALUES",
            "DELETE FROM menuto_identity_source.roots",
            "SELECT menuto_identity_source._tls_fact_v1()",
            "SELECT menuto_prior.backend_tls()",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)


MUTATIONS = (
    "public_definer",
    "dynamic_sql",
    "invoker_to_definer",
    "body",
    "owner",
    "signature",
    "search_path",
    "acl",
    "dependency",
    "omission",
    "protected_public",
)


@pytest.mark.parametrize("mutation", MUTATIONS)
def test_itr020_shadowing_resistance(identity_scenario, mutation):  # noqa: F811
    s = identity_scenario
    before = s.counts()
    with s.connect() as admin, admin.transaction(force_rollback=True):
        if mutation == "public_definer":
            admin.execute(
                "CREATE FUNCTION public.itr_unreviewed() RETURNS bigint LANGUAGE "
                "sql SECURITY DEFINER AS 'SELECT 1::bigint'"
            )
        elif mutation == "dynamic_sql":
            admin.execute(
                "CREATE FUNCTION public.itr_unreviewed(q text) RETURNS bigint LAN"
                "GUAGE plpgsql AS $b$ BEGIN EXECUTE q; RETURN 1; END $b$"
            )
        elif mutation == "invoker_to_definer":
            admin.execute(
                "CREATE FUNCTION public.itr_definer() RETURNS bigint LANGUAGE sql"
                " SECURITY DEFINER AS 'SELECT 1::bigint'"
            )
            admin.execute(
                "CREATE FUNCTION public.itr_unreviewed() RETURNS bigint LANGUAGE "
                "sql AS 'SELECT public.itr_definer()'"
            )
        elif mutation == "body":
            admin.execute(
                "CREATE OR REPLACE FUNCTION public.menuto_preference_canonical(j "
                "jsonb) RETURNS text LANGUAGE sql IMMUTABLE STRICT AS 'SELECT j::"
                "text'"
            )
        elif mutation == "owner":
            admin.execute(
                sql.SQL(
                    "ALTER FUNCTION public.menuto_preference_canonical(jsonb) OWNER TO {}"
                ).format(sql.Identifier(s.roles["requester"]))
            )
        elif mutation == "signature":
            admin.execute(
                "ALTER FUNCTION public.menuto_preference_canonical(jsonb) RENAME "
                "TO itr_unknown_signature"
            )
        elif mutation == "search_path":
            admin.execute(
                "ALTER FUNCTION public.menuto_preference_canonical(jsonb) SET sea"
                "rch_path=pg_temp,public"
            )
        elif mutation == "acl":
            admin.execute(
                sql.SQL(
                    "GRANT EXECUTE ON FUNCTION public.menuto_preference_canonical(jso"
                    "nb) TO {} WITH GRANT OPTION"
                ).format(sql.Identifier(s.roles["requester"]))
            )
        elif mutation == "dependency":
            # Caller body remains exact; independently pinned callee mutation must still deny.
            admin.execute(
                "CREATE OR REPLACE FUNCTION public.menuto_feature_key(aid uuid) R"
                "ETURNS jsonb LANGUAGE sql STABLE AS 'SELECT null::jsonb'"
            )
        elif mutation == "omission":
            admin.execute("DROP FUNCTION public.menuto_preference_canonical(jsonb)")
        else:
            admin.execute(
                "GRANT EXECUTE ON FUNCTION menuto_identity_source.capture_request"
                "_source(text) TO PUBLIC"
            )
        # Entry rechecks this transaction's actual catalog; no supplied author/session facts.
        with pytest.raises(psycopg.errors.InsufficientPrivilege), admin.transaction():
            admin.execute(
                "SELECT menuto_identity_source.change_issuer(%s)",
                (json.dumps(s.commands["ISSUER"]),),
            )
    assert s.counts() == before
    _checked(s)


@pytest.mark.parametrize("case", ("unchanged", "mutation_before_cut", "mutation_after_cut"))
def test_itr040_coherent_cut(identity_scenario, case, record_property):  # noqa: F811
    from identity_catalog_cut_checks import (
        assert_mutation_after_cut,
        assert_mutation_before_cut,
        assert_unchanged_and_observed_mismatch,
    )

    handlers = {
        "unchanged": assert_unchanged_and_observed_mismatch,
        "mutation_before_cut": assert_mutation_before_cut,
        "mutation_after_cut": assert_mutation_after_cut,
    }
    evidence = handlers[case](identity_scenario)
    record_property("ITR040_native_proof", json.dumps(evidence, sort_keys=True))


def test_itr020_attacker_temp_view_cannot_bridge_owner(identity_scenario):  # noqa: F811
    s = identity_scenario
    before = s.counts()
    with s.connect("requester") as db:
        db.execute(
            "CREATE TEMP VIEW inventory_movements WITH (security_invoker=true"
            ") AS SELECT root_id AS household_id,recorded_order AS ledger_seq"
            "uence FROM menuto_identity_source.roots"
        )
        db.execute("GRANT SELECT ON pg_temp.inventory_movements TO PUBLIC")
        # Ordinary INVOKER remains ordinary even with an attacker-authored security-invoker view.
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            db.execute("SELECT public.menuto_plan_inventory_frontier(%s)", (s.root_id,))
        with pytest.raises(psycopg.errors.InsufficientPrivilege), db.transaction():
            db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            db.execute(
                "SELECT menuto_identity_source.capture_request_source(%s)", (json.dumps(s.raw),)
            )
    assert s.counts() == before
    _checked(s)


# Remaining exact source/authentication/lifecycle obligations use actual protected paths.


def _renew_or_revoke(s, kind, action="REVOKE", **changes):
    current = s.commands[kind]
    receipt = s.receipts[kind]
    body = dict(
        current,
        idempotency_key=str(uuid4()),
        action=action,
        expected_revision=receipt["revision"],
        predecessor_id=receipt["fact_id"],
        effective=None,
    )
    body.update(changes)
    return body


def test_itr001_fresh_install_and_downgrade(identity_server, record_property):  # noqa: F811
    from alembic import command
    from alembic.config import Config
    from identity_postgres_fixtures import ROOT, new_identity_scenario
    from sqlalchemy import inspect, text

    with new_identity_scenario(identity_server, provision=False, fresh=True) as s:
        assert s.counts() == (0, 0, 0, 0, 0, 0)
        with s.connect() as native:
            tables = native.execute("""SELECT schemaname,tablename FROM pg_tables
                WHERE schemaname NOT LIKE 'pg_%%' AND schemaname<>'information_schema'
                AND tablename<>'alembic_version' ORDER BY schemaname,tablename""").fetchall()
            counts = {
                schema + "." + name: native.execute(
                    sql.SQL("SELECT count(*) FROM {}.{}").format(
                        sql.Identifier(schema), sql.Identifier(name)
                    )
                ).fetchone()[0]
                for schema, name in tables
            }
            assert len(counts) == 114
            # Every new Identity authority row and all production nutrition/reference truth
            # remain absent before the separate TEST_ONLY fixture enrollment.
            assert all(
                count == 0
                for name, count in counts.items()
                if name.startswith("menuto_identity_source.")
                or any(
                    key in name
                    for key in (
                        "nutrition",
                        "guideline",
                        "eligibility",
                        "goal",
                        "provider",
                        "qualification",
                    )
                )
            )
            roles = native.execute("""SELECT rolname,oid::bigint,rolcanlogin,rolsuper,rolcreaterole,
                rolcreatedb,rolreplication,rolbypassrls FROM pg_roles
                WHERE rolname IN ('menuto_identity_source_owner','menuto_identity_bootstrap',
                                 'menuto_identity_issuer','menuto_identity_requester')
                ORDER BY rolname""").fetchall()
            assert len(roles) == 4 and not any(any(row[2:]) for row in roles)
            functions = native.execute("""SELECT p.oid::bigint,p.proname,
                pg_get_function_identity_arguments(p.oid),r.rolname,p.prosecdef,l.lanname,
                p.proconfig,pg_get_functiondef(p.oid),EXISTS(SELECT FROM
                  aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) acl
                  WHERE acl.grantee=0 AND acl.privilege_type='EXECUTE')
                FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                JOIN pg_roles r ON r.oid=p.proowner JOIN pg_language l ON l.oid=p.prolang
                WHERE n.nspname='menuto_identity_source' ORDER BY p.proname""").fetchall()
            assert len(functions) == 17 and not any(row[-1] for row in functions)
            inventory = [
                dict(
                    oid=row[0],
                    name=row[1],
                    arguments=row[2],
                    owner=row[3],
                    security_definer=row[4],
                    language=row[5],
                    configuration=row[6],
                    definition_sha256=hashlib.sha256(row[7].encode()).hexdigest(),
                    public_execute=row[8],
                )
                for row in functions
            ]
            record_property(
                "ITR001_fresh_install",
                json.dumps(
                    dict(
                        revision="0018",
                        table_count=114,
                        row_counts=counts,
                        roles=roles,
                        functions=inventory,
                        production_nutrition_content=0,
                    ),
                    sort_keys=True,
                ),
            )
        engine = s.engine("bootstrap", readonly=False)
        cfg = Config(str(ROOT / "alembic.ini"))
        with engine.connect() as db:
            cfg.attributes["connection"] = db
            inspector = inspect(db)
            assert len(inspector.get_table_names(schema="public")) - 1 == 108
            assert len(inspector.get_table_names(schema="menuto_identity_source")) == 6
            before = db.scalar(text("SELECT oid FROM pg_extension WHERE extname='sslinfo'"))
            db.commit()
            command.downgrade(cfg, "0017")
            db.commit()
            assert not inspect(db).has_schema("menuto_identity_source")
            assert db.scalar(text("SELECT oid FROM pg_extension WHERE extname='sslinfo'")) == before
            db.commit()
            command.upgrade(cfg, "head")
            db.commit()
        s.provision()
        with engine.connect() as db:
            cfg.attributes["connection"] = db
            with pytest.raises(Exception, match="refuses retained"):
                command.downgrade(cfg, "0017")
            db.rollback()
        assert s.counts()[:4] == (1, 1, 1, 1)


def test_itr002_bootstrap_root(identity_server):  # noqa: F811
    from identity_postgres_fixtures import new_identity_scenario

    with new_identity_scenario(identity_server, provision=False) as s:
        receipt = s.append(s.body("ROOT", "INITIALIZE", 24))
        with s.connect() as db:
            fact = db.execute(
                "SELECT author_session,database_oid,database_name FROM menuto_identity_source.roots"
            ).fetchone()
            assert fact[0]["system_user"] == "scram-sha-256:" + s.roles["bootstrap"]
            assert fact[0]["tls"] and fact[1] == fact[0]["database_oid"] and fact[2] == s.name
        assert receipt["revision"] == 1
        with pytest.raises(psycopg.Error):
            s.append(s.body("ROOT", "INITIALIZE", 24, root_id=str(uuid4())))
        assert s.counts()[0] == 1


def test_itr003_administrator_issuer_separation(identity_scenario):  # noqa: F811
    s = identity_scenario
    before = s.counts()
    for actor in ("issuer", "requester"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            s.append(s.commands["ROOT"], actor=actor)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        s.append(s.commands["BINDING"], actor="bootstrap")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        s.capture(actor="bootstrap")
    assert s.counts() == before


def test_itr004_privileged_requester_rejection(identity_scenario):  # noqa: F811
    s = identity_scenario
    # Use the already privileged disposable installer; do not elevate any requester.
    with s.connect() as admin:
        assert admin.execute("SELECT rolsuper FROM pg_roles WHERE rolname=session_user").fetchone()[
            0
        ]
        assert admin.execute(
            "SELECT datdba=(SELECT oid FROM pg_roles WHERE "
            "rolname=session_user) FROM pg_database WHERE "
            "datname=current_database()"
        ).fetchone()[0]
        owner = admin.execute(
            "SELECT rolcanlogin,rolsuper,rolcreaterole,rolcreatedb FROM "
            "pg_roles WHERE rolname='menuto_identity_source_owner'"
        ).fetchone()
        assert owner == (False, False, False, False)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        s.capture(actor="bootstrap")
    with s.connect() as admin, admin.transaction():
        admin.execute("SET LOCAL ROLE menuto_identity_source_owner")
        with pytest.raises(psycopg.errors.InsufficientPrivilege), admin.transaction():
            admin.execute(
                "SELECT menuto_identity_source.capture_request_source(%s)", (json.dumps(s.raw),)
            )


def test_itr005_issuer_enrollment_and_exact_user(identity_scenario):  # noqa: F811
    from uuid import uuid4

    s = identity_scenario
    before = s.counts()
    for changes in (dict(user_id=str(uuid4())), dict(role_name="itr_NO_SUCH_ROLE")):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            s.append(s.body("BINDING", "ENROLL", 3, binding_id=str(uuid4()), **changes))
    assert s.counts() == before


def test_itr006_alias_and_role_reservation(identity_scenario):  # noqa: F811
    from uuid import uuid4

    s = identity_scenario
    before = s.counts()
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        s.append(s.body("BINDING", "ENROLL", 2, binding_id=str(uuid4()), user_id=s.issuer_user_id))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        s.append(s.body("ISSUER", "ENROLL", 2, issuer_id=str(uuid4()), user_id=s.user_id))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        s.append(s.body("BINDING", "ENROLL", 2, binding_id=str(uuid4())))
    assert s.counts() == before


def test_itr008_actual_wrong_password(identity_scenario):  # noqa: F811
    with pytest.raises(psycopg.OperationalError):
        identity_scenario.connect("requester", password="TEST_ONLY_INVALID_PASSWORD")


def test_itr009_actual_trust_rejection(identity_scenario):  # noqa: F811
    from identity_postgres_fixtures import identity_hba_method

    s = identity_scenario
    with identity_hba_method(s, "trust"):
        with s.connect("requester") as db:
            observed = db.execute("SELECT system_user").fetchone()[0]
            assert observed != "scram-sha-256:" + s.roles["requester"]
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            s.capture()
    _checked(s)


def test_itr010_actual_non_scram_rejection(identity_scenario):  # noqa: F811
    from identity_postgres_fixtures import identity_hba_method

    s = identity_scenario
    with identity_hba_method(s, "password"):
        with s.connect("requester") as db:
            assert (
                db.execute("SELECT system_user").fetchone()[0] == "password:" + s.roles["requester"]
            )
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            s.capture()
    _checked(s)


def test_itr011_actual_tls_requirement(identity_scenario):  # noqa: F811
    s = identity_scenario
    with s.connect("requester", sslmode="disable") as db, db.transaction():
        assert not db.execute("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()").fetchone()[
            0
        ]
        with pytest.raises(psycopg.errors.InsufficientPrivilege), db.transaction():
            db.execute(
                "SELECT menuto_identity_source.capture_request_source(%s)", (json.dumps(s.raw),)
            )


def test_itr012_verified_endpoint(identity_scenario, tmp_path):  # noqa: F811
    s = identity_scenario
    with pytest.raises(psycopg.OperationalError):
        s.connect("requester", host="invalid.test", hostaddr=s.url.host)
    import os
    import shutil
    import subprocess

    binary = shutil.which("openssl") or r"C:\Program Files\Git\usr\bin\openssl.exe"
    assert Path(binary).is_file()
    config = tmp_path / "openssl.cnf"
    config.write_text("[req]\ndistinguished_name=dn\n[dn]\n")
    wrong = tmp_path / "wrong.crt"
    subprocess.run(
        [
            binary,
            "req",
            "-config",
            str(config),
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-keyout",
            str(tmp_path / "wrong.key"),
            "-out",
            str(wrong),
            "-subj",
            "/CN=TEST_ONLY_UNRELATED_CA",
        ],
        check=True,
        timeout=20,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    with pytest.raises(psycopg.OperationalError):
        s.connect("requester", sslrootcert=str(wrong))


def test_itr013_set_role_spoofing(identity_scenario):  # noqa: F811
    s = identity_scenario
    with s.connect("requester") as db, db.transaction():
        db.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(s.roles["requester"])))
        with pytest.raises(psycopg.errors.InsufficientPrivilege), db.transaction():
            db.execute(
                "SELECT menuto_identity_source.capture_request_source(%s)", (json.dumps(s.raw),)
            )


def test_itr014_set_session_authorization_spoofing(identity_scenario):  # noqa: F811
    s = identity_scenario
    with s.connect() as db, db.transaction():
        db.execute(
            sql.SQL("SET LOCAL SESSION AUTHORIZATION {}").format(
                sql.Identifier(s.roles["requester"])
            )
        )
        assert (
            db.execute("SELECT system_user").fetchone()[0]
            == "scram-sha-256:" + s.roles["bootstrap"]
        )
        with pytest.raises(psycopg.errors.InsufficientPrivilege), db.transaction():
            db.execute(
                "SELECT menuto_identity_source.capture_request_source(%s)", (json.dumps(s.raw),)
            )


def test_itr015_role_recreation(identity_scenario):  # noqa: F811
    s = identity_scenario
    with s.connect() as db:
        old = db.execute(
            "SELECT oid FROM pg_roles WHERE rolname=%s", (s.roles["requester"],)
        ).fetchone()[0]
        db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(s.roles["requester"])))
        db.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                sql.Identifier(s.roles["requester"]), sql.Literal(s.credentials["requester"])
            )
        )
        db.execute(
            sql.SQL(
                "GRANT menuto_identity_requester TO {} WITH INHERIT TRUE,SET FALSE,ADMIN FALSE"
            ).format(sql.Identifier(s.roles["requester"]))
        )
        assert (
            db.execute(
                "SELECT oid FROM pg_roles WHERE rolname=%s", (s.roles["requester"],)
            ).fetchone()[0]
            != old
        )
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        s.capture()


def test_itr016_role_rename(identity_scenario):  # noqa: F811
    from uuid import uuid4

    s = identity_scenario
    renamed = "itr_renamed_" + uuid4().hex[:12]
    with s.connect() as db:
        db.execute(
            sql.SQL("ALTER ROLE {} RENAME TO {}").format(
                sql.Identifier(s.roles["requester"]), sql.Identifier(renamed)
            )
        )
        try:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                with s.connect("requester", user=renamed) as actor, actor.transaction():
                    actor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                    actor.execute(
                        "SELECT menuto_identity_source.capture_request_source(%s)",
                        (json.dumps(s.raw),),
                    )
            db.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(s.roles["requester"]), sql.Literal(s.credentials["requester"])
                )
            )
            db.execute(
                sql.SQL(
                    "GRANT menuto_identity_requester TO {} WITH INHERIT TRUE,SET FALSE,ADMIN FALSE"
                ).format(sql.Identifier(s.roles["requester"]))
            )
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                s.capture()
        finally:
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(renamed)))


def test_itr017_database_root_identity(identity_scenario):  # noqa: F811
    from uuid import uuid4

    s = identity_scenario
    name = "itr_clone_" + uuid4().hex
    for engine in s.engines:
        engine.dispose()
    with s.server["maintenance"].connect() as admin:
        admin.exec_driver_sql(f'CREATE DATABASE "{name}" TEMPLATE "{s.name}"')
        try:
            with s.connect("requester", dbname=name) as db, db.transaction():
                db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    db.execute(
                        "SELECT menuto_identity_source.capture_request_source(%s)",
                        (json.dumps(s.raw),),
                    )
        finally:
            admin.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')


def test_itr021_scope_issuance_authority(identity_scenario):  # noqa: F811
    from datetime import UTC, datetime, timedelta
    from uuid import uuid4

    s = identity_scenario
    before = s.counts()
    overlong = s.body("OPERATION_GRANT", "GRANT", 24, grant_id=str(uuid4()))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        s.append(overlong)
    backdated = s.body("OPERATION_GRANT", "GRANT", 1, grant_id=str(uuid4()))
    backdated["effective"].update(
        mode="SCHEDULED", start=(datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    )
    with pytest.raises(psycopg.Error):
        s.append(backdated)
    assert s.counts() == before


def test_itr022_foreign_scope(identity_scenario):  # noqa: F811
    from uuid import uuid4

    s = identity_scenario
    request = dict(s.raw)
    foreign = str(uuid4())
    child = json.loads(request["request_utf8"])
    child["context"]["household_id"] = foreign
    raw = json.dumps(child)
    request.update(
        household_id=foreign,
        request_utf8=raw,
        request_preimage_fingerprint=hashlib.sha256(
            b"identity.request-preimage.v1\x00" + raw.encode()
        ).hexdigest(),
    )
    retained = s.capture(request)
    assert retained["outcome"] == "UNAVAILABLE" and retained["reason"] == "GRANT_ABSENT"
    assert retained["membership"] is None and retained["grant_history"] == []
    assert check_identity_source_v1(retained, request).decision == "CONSISTENT"


def test_itr023_membership_eligibility(identity_scenario):  # noqa: F811
    s = identity_scenario
    with s.connect() as db:
        db.execute("UPDATE public.memberships SET role='VIEWER' WHERE user_id=%s", (s.user_id,))
    retained = s.capture()
    assert retained["reason"] == "AUTHORIZATION_DENIED" and retained["outcome"] == "UNAVAILABLE"
    assert retained["membership"]["target_member_exists"] is None
    assert check_identity_source_v1(retained, s.raw).decision == "CONSISTENT"


def test_itr024_membership_pin_change(identity_scenario):  # noqa: F811
    s = identity_scenario
    with s.connect() as db:
        db.execute("UPDATE public.memberships SET role='EDITOR' WHERE user_id=%s", (s.user_id,))
    retained = s.capture()
    assert (
        retained["reason"] == "AUTHORIZATION_DENIED"
        and retained["membership"]["target_member_exists"] is None
    )
    assert check_identity_source_v1(retained, s.raw).decision == "CONSISTENT"


def test_itr025_operation_isolation(identity_scenario):  # noqa: F811
    s = identity_scenario
    request = dict(s.raw, operation="MEMBER_GOAL_WRITE")
    with pytest.raises(psycopg.Error):
        s.capture(request)
    with s.connect("requester") as db:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            db.execute(
                "SELECT menuto_identity_source.change_operation_grant(%s)",
                (json.dumps(s.commands["OPERATION_GRANT"]),),
            )


def test_itr026_root_revocation(identity_scenario):  # noqa: F811
    s = identity_scenario
    s.append(_renew_or_revoke(s, "ROOT"))
    retained = s.capture()
    assert retained["reason"] == "ROOT_REVOKED" and retained["membership"] is None
    assert check_identity_source_v1(retained, s.raw).decision == "CONSISTENT"


def test_itr027_issuer_revocation(identity_scenario):  # noqa: F811
    s = identity_scenario
    s.append(_renew_or_revoke(s, "ISSUER"))
    retained = s.capture()
    assert retained["reason"] == "ISSUER_REVOKED" and retained["membership"] is None
    assert check_identity_source_v1(retained, s.raw).decision == "CONSISTENT"


def test_itr028_binding_revocation(identity_scenario):  # noqa: F811
    s = identity_scenario
    s.append(_renew_or_revoke(s, "BINDING"))
    retained = s.capture()
    assert retained["reason"] == "BINDING_REVOKED" and retained["membership"] is None
    assert check_identity_source_v1(retained, s.raw).decision == "CONSISTENT"


def test_itr029_grant_revocation(identity_scenario):  # noqa: F811
    s = identity_scenario
    s.append(_renew_or_revoke(s, "OPERATION_GRANT"))
    retained = s.capture()
    assert retained["reason"] == "GRANT_REVOKED" and retained["membership"] is None
    assert check_identity_source_v1(retained, s.raw).decision == "CONSISTENT"


def test_itr031_credential_expiry_and_reset(identity_scenario):  # noqa: F811
    s = identity_scenario
    with s.connect("requester") as actor, s.connect() as admin:
        admin.execute(
            sql.SQL("ALTER ROLE {} VALID UNTIL '2000-01-01 UTC'").format(
                sql.Identifier(s.roles["requester"])
            )
        )
        try:
            with pytest.raises(psycopg.errors.InsufficientPrivilege), actor.transaction():
                actor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                actor.execute(
                    "SELECT menuto_identity_source.capture_request_source(%s)", (json.dumps(s.raw),)
                )
        finally:
            admin.execute(
                sql.SQL("ALTER ROLE {} VALID UNTIL 'infinity'").format(
                    sql.Identifier(s.roles["requester"])
                )
            )
    s.append(_renew_or_revoke(s, "BINDING"))
    assert s.capture()["reason"] == "BINDING_REVOKED"


def test_itr033_future_effective_renewal(identity_scenario):  # noqa: F811
    from datetime import datetime, timedelta

    s = identity_scenario
    old = s.commands["OPERATION_GRANT"]["effective"]["end"]
    end = (datetime.fromisoformat(old) + timedelta(hours=1)).isoformat()
    body = _renew_or_revoke(
        s,
        "OPERATION_GRANT",
        "RENEW",
        effective=dict(version=1, mode="SCHEDULED", start=old, end=end),
    )
    s.append(body)
    assert s.capture()["outcome"] == "AVAILABLE_AT_RETAINED_CUT"
    s.append(_renew_or_revoke(s, "OPERATION_GRANT"))
    assert s.capture()["reason"] == "GRANT_REVOKED"


def test_itr034_concurrent_cas(identity_scenario):  # noqa: F811
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timedelta

    s = identity_scenario
    old_end = s.commands["OPERATION_GRANT"]["effective"]["end"]
    effective = dict(
        version=1,
        mode="SCHEDULED",
        start=old_end,
        end=(datetime.fromisoformat(old_end) + timedelta(hours=1)).isoformat(),
    )
    bodies = [
        _renew_or_revoke(s, "OPERATION_GRANT", "RENEW", effective=effective) for _ in range(2)
    ]

    def write(body):
        try:
            return s.append(body)["revision"]
        except psycopg.Error as error:
            return error.sqlstate

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, bodies))
    assert sorted(results, key=str) == [2, "40001"]
    assert s.counts()[3] == 2 and s.counts()[-1] == 5


def test_itr035_idempotency(identity_scenario):  # noqa: F811
    s = identity_scenario
    before = s.counts()
    body = s.commands["OPERATION_GRANT"]
    original = s.receipts["OPERATION_GRANT"]
    assert s.append(body) == original and s.counts() == before
    changed = dict(body, evidence_preimage="TEST_ONLY DIFFERENT")
    with pytest.raises(psycopg.errors.SerializationFailure):
        s.append(changed)
    assert s.counts() == before


def test_itr036_revoked_issuer_retry(identity_scenario):  # noqa: F811
    s = identity_scenario
    old = s.commands["BINDING"]
    s.append(_renew_or_revoke(s, "ISSUER"))
    before = s.counts()
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        s.append(old)
    assert s.counts() == before


def test_itr037_atomic_failure(identity_scenario):  # noqa: F811
    s = identity_scenario
    before = s.counts()
    body = _renew_or_revoke(s, "BINDING")
    with s.connect("issuer") as db:
        with pytest.raises(psycopg.errors.DivisionByZero), db.transaction():
            db.execute("SELECT menuto_identity_source.change_binding(%s)", (json.dumps(body),))
            db.execute("SELECT 1/0")
    assert s.counts() == before


def test_itr038_read_only_transaction_shape(identity_scenario):  # noqa: F811
    from app.modules.identity.source_capture import capture_identity_request_source_v1

    s = identity_scenario
    for isolation, readonly in (("READ COMMITTED", True), ("REPEATABLE READ", False)):
        with pytest.raises(psycopg.Error):
            s.capture(isolation=isolation, readonly=readonly)
    with s.engine().connect() as db, db.begin():
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        result = capture_identity_request_source_v1(db, s.raw, context=s.context())
        assert result.reason == "INVALID_TRANSACTION"


def test_itr039_no_cache_or_split_capture(identity_scenario):  # noqa: F811
    from app.modules.identity.source_capture import capture_identity_request_source_v1

    s = identity_scenario
    with pytest.raises(TypeError):
        capture_identity_request_source_v1(None, s.raw, context=s.context(), source=s.capture())
    failure = capture_identity_request_source_v1(object(), s.raw, context=s.context())
    assert failure.reason == "UNSUPPORTED_DEPLOYMENT" and failure.payload is None


def test_itr041_fresh_versus_retained_revoke(identity_scenario):  # noqa: F811
    s = identity_scenario
    old = _checked(s)
    s.append(_renew_or_revoke(s, "OPERATION_GRANT"))
    assert s.capture()["reason"] == "GRANT_REVOKED"
    assert check_identity_source_v1(old, s.raw).decision == "CONSISTENT"
    with pytest.raises(TypeError):
        inspect_authenticated_explicit_plan_intent_v1(None, s.raw, context=s.context(), source=old)


def test_itr042_complete_source_and_absences(identity_scenario):  # noqa: F811
    s = identity_scenario
    source = _checked(s)
    assert (
        sum(
            len(source[k])
            for k in ("root_history", "issuer_history", "binding_history", "grant_history")
        )
        == source["frame"]["total_fact_count"]
    )
    directory = next(f for f in source["frame"]["frontiers"] if f["kind"] == "ISSUER_DIRECTORY")
    assert directory["fact_count"] == 1 and len(directory["directory_entries"]) == 1
    malformed = copy.deepcopy(source)
    malformed["issuer_history"] = []
    malformed["source_fingerprint"] = h(
        "identity.source.v1", {k: v for k, v in malformed.items() if k != "source_fingerprint"}
    )
    assert check_identity_source_v1(malformed, s.raw).decision == "INCONSISTENT"


def test_itr043_privacy(identity_scenario):  # noqa: F811
    s = identity_scenario
    source = _checked(s)
    text = json.dumps(source)
    assert "TEST_ONLY Identity issuer" not in text and "Synthetic test actor" not in text
    assert s.credentials["issuer"] not in text and s.credentials["requester"] not in text
    assert not any(key in text for key in ('"password"', '"rolpassword"', '"verifier"'))


def test_itr045_timeout_and_cancellation(identity_scenario):  # noqa: F811
    from app.modules.identity.source_capture import capture_identity_request_source_v1
    from psycopg.pq import TransactionStatus
    from sqlalchemy import create_engine

    s = identity_scenario
    before = s.counts()
    with s.connect() as blocker, blocker.transaction():
        blocker.execute("SELECT pg_advisory_xact_lock(17492711,0)")
        with pytest.raises(psycopg.errors.LockNotAvailable):
            s.append(_renew_or_revoke(s, "BINDING"))
    assert s.counts() == before
    engine = create_engine(
        s.url.set(username=s.roles["requester"], password=s.credentials["requester"]),
        connect_args={"options": "-c statement_timeout=1"},
    ).execution_options(isolation_level="REPEATABLE READ", postgresql_readonly=True)
    try:
        with engine.connect() as db:
            transaction = db.begin()
            result = capture_identity_request_source_v1(db, s.raw, context=s.context())
            assert result.reason == "CANCELLED" and result.payload is None
            assert (
                db.connection.driver_connection.info.transaction_status == TransactionStatus.INERROR
            )
            transaction.rollback()
            assert db.connection.driver_connection.info.transaction_status == TransactionStatus.IDLE
    finally:
        engine.dispose()


def test_itr046_complete_request_preimage(identity_scenario):  # noqa: F811
    s = identity_scenario
    bad = dict(s.raw, request_preimage_fingerprint="f" * 64)
    with pytest.raises(psycopg.Error):
        s.capture(bad)
    bad = dict(s.raw, request_revision=s.raw["request_revision"] + 1)
    with pytest.raises(psycopg.Error):
        s.capture(bad)


def test_itr047_authenticated_invalid_intent(identity_scenario):  # noqa: F811
    import hashlib

    s = identity_scenario
    request = dict(s.raw)
    child = json.loads(request["request_utf8"])
    child["nutrition_precision"] = 1.5
    raw = json.dumps(child)
    request.update(
        request_utf8=raw,
        request_preimage_fingerprint=hashlib.sha256(
            b"identity.request-preimage.v1\x00" + raw.encode()
        ).hexdigest(),
    )
    with s.engine().connect() as db, db.begin():
        result = inspect_authenticated_explicit_plan_intent_v1(db, request, context=s.context())
    assert result.reason == "INTENT_NON_SUCCESS" and result.outcome == "UNAVAILABLE"
    assert result.source_check.decision == "CONSISTENT" and result.intent_result.payload is None
    assert result.numerical_use == "NOT_ADMITTED"


def test_itr048_unrelated_authority_rejected(identity_scenario):  # noqa: F811
    s = identity_scenario
    with s.connect() as admin:
        admin.execute(
            sql.SQL("REVOKE menuto_identity_requester FROM {}").format(
                sql.Identifier(s.roles["requester"])
            )
        )
        admin.execute(
            sql.SQL(
                "GRANT menuto_nutrition_client TO {} WITH INHERIT TRUE,SET FALSE,ADMIN FALSE"
            ).format(sql.Identifier(s.roles["requester"]))
        )
        try:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                s.capture()
        finally:
            admin.execute(
                sql.SQL("REVOKE menuto_nutrition_client FROM {}").format(
                    sql.Identifier(s.roles["requester"])
                )
            )
            admin.execute(
                sql.SQL(
                    "GRANT menuto_identity_requester TO {} WITH INHERIT TRUE,SET FALSE,ADMIN FALSE"
                ).format(sql.Identifier(s.roles["requester"]))
            )
    _checked(s)


@pytest.mark.parametrize("expired", ("root", "issuer", "binding", "grant"))
def test_itr030_expiry_without_revoke(identity_server, expired):  # noqa: F811
    import time
    from datetime import UTC, datetime

    from identity_postgres_fixtures import new_identity_scenario

    durations = {
        "root": (12, 11, 10, 9),
        "issuer": (86400, 12, 11, 10),
        "binding": (86400, 43200, 12, 11),
        "grant": (86400, 43200, 21600, 8),
    }[expired]
    with new_identity_scenario(identity_server, provision=False) as s:
        s.provision(lifetimes=durations)
        before = _checked(s)
        end = datetime.fromisoformat(
            s.commands[
                {
                    "root": "ROOT",
                    "issuer": "ISSUER",
                    "binding": "BINDING",
                    "grant": "OPERATION_GRANT",
                }[expired]
            ]["effective"]["end"]
        )
        time.sleep(max(0, (end - datetime.now(UTC)).total_seconds()) + 0.05)
        result = s.capture()
        assert (
            result["outcome"] == "UNAVAILABLE" and result["reason"] == expired.upper() + "_EXPIRED"
        )
        assert check_identity_source_v1(result, s.raw).decision == "CONSISTENT"
        assert check_identity_source_v1(before, s.raw).decision == "CONSISTENT"


def test_itr032_renewal_cannot_repair_past(identity_server):  # noqa: F811
    import time
    from datetime import UTC, datetime, timedelta

    from identity_postgres_fixtures import new_identity_scenario

    with new_identity_scenario(identity_server, provision=False) as s:
        s.provision(lifetimes=(86400, 10, 9, 8))
        original = _checked(s)
        old = s.commands["BINDING"]
        before = s.counts()
        end = datetime.fromisoformat(s.commands["ISSUER"]["effective"]["end"])
        time.sleep(max(0, (end - datetime.now(UTC)).total_seconds()) + 0.05)
        with pytest.raises(psycopg.Error):
            s.append(old)
        assert s.counts() == before
        renewal = _renew_or_revoke(
            s,
            "ISSUER",
            "RENEW",
            effective=dict(
                version=1,
                mode="IMMEDIATE",
                start=None,
                end=(datetime.now(UTC) + timedelta(hours=5)).isoformat(),
            ),
        )
        s.append(renewal)
        assert s.capture()["reason"] == "BINDING_EXPIRED"
        assert check_identity_source_v1(original, s.raw).decision == "CONSISTENT"
        backdated = _renew_or_revoke(
            s,
            "BINDING",
            "RENEW",
            effective=dict(
                version=1,
                mode="SCHEDULED",
                start=old["effective"]["end"],
                end=renewal["effective"]["end"],
            ),
        )
        with pytest.raises(psycopg.Error):
            s.append(backdated)


def test_itr044_server_limits(identity_scenario):  # noqa: F811
    s = identity_scenario
    before = s.counts()
    large = dict(s.commands["BINDING"], evidence_preimage="x" * 16385)
    with pytest.raises(psycopg.errors.ProgramLimitExceeded):
        s.append(large)
    assert s.counts() == before
    with s.connect() as admin, admin.transaction():
        # Trusted fault fixture only: exceed retained row limits with actual constrained PG rows.
        # It is not publication through ordinary paths or evidence that the history is canonical.
        admin.execute(
            "ALTER TABLE menuto_identity_source.operation_grants DISABLE "
            "TRIGGER identity_write_guard"
        )
        columns = admin.execute(
            "SELECT attname FROM pg_attribute WHERE "
            "attrelid='menuto_identity_source.operation_grants'::regclass AND "
            "attnum>0 AND NOT attisdropped ORDER BY attnum"
        ).fetchall()
        projections = []
        special = {
            "id": "generated.id",
            "revision": "generated.n+1",
            "recorded_order": "nextval('menuto_identity_source.recorded_order')",
            "previous_id": "g.id",
            "previous_fingerprint": "g.fact_fingerprint",
            "idempotency_key": "generated.id",
            "command_body": "jsonb_set(g.command_body,'{idempotency_key}',to_jsonb(generated.id))",
        }
        for (column,) in columns:
            projections.append(
                sql.SQL(special[column])
                if column in special
                else sql.SQL("g.{}").format(sql.Identifier(column))
            )
        query = sql.SQL(
            "INSERT INTO menuto_identity_source.operation_grants ({}) SELECT {} "
            "FROM menuto_identity_source.operation_grants g CROSS JOIN (SELECT "
            "n,gen_random_uuid() id FROM generate_series(1,2048) n) generated "
            "WHERE g.revision=1"
        ).format(
            sql.SQL(",").join(sql.Identifier(c[0]) for c in columns), sql.SQL(",").join(projections)
        )
        admin.execute(query)
        admin.execute("SET CONSTRAINTS ALL IMMEDIATE")
        admin.execute(
            "ALTER TABLE menuto_identity_source.operation_grants ENABLE TRIGGER "
            "identity_write_guard"
        )
    with pytest.raises(psycopg.errors.ProgramLimitExceeded):
        s.capture()


PARAMETER_CASES = (
    "p1_default",
    "p2_real_row",
    "p3_set",
    "p3_set_grant_option",
    "p3_alter_system",
    "p3_alter_system_grant_option",
    "p4_public_set",
    "p4_public_alter_system",
    "p4_inherit_true_set",
    "p4_inherit_true_alter_system",
    "p4_inherit_false_set",
    "p4_inherit_false_alter_system",
    "p5_grant_set",
    "p5_grant_alter_system",
    "p5_revoke_set",
    "p5_revoke_alter_system",
    "p5_cross_database_set",
    "p5_cross_database_alter_system",
    "p6_absent",
    "p6_null",
    "p6_empty",
    "p7_custom",
    "p7_other_grantee",
    "p7_overflow",
)


def _actual_parameter_facts(admin, actor_oid):
    with admin.transaction():
        admin.execute("SET LOCAL ROLE menuto_identity_source_owner")
        return admin.execute(
            "SELECT menuto_identity_source._parameter_acl_facts_v1(%s)", (actor_oid,)
        ).fetchone()[0]


@pytest.mark.parametrize("case", PARAMETER_CASES)
def test_itr018_privilege_graph_closure(identity_scenario, case):  # noqa: F811
    s = identity_scenario
    other = "itr_parameter_" + uuid4().hex[:12]
    parameter = "menuto_itr.p_" + uuid4().hex
    privilege = "ALTER SYSTEM" if "alter_system" in case else "SET"
    with s.connect() as admin:
        admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(other)))
        actor_oid = admin.execute(
            "SELECT oid FROM pg_roles WHERE rolname=%s", (s.roles["requester"],)
        ).fetchone()[0]

        def grant(target, *, option=False, connection=admin):
            connection.execute(
                sql.SQL("GRANT {} ON PARAMETER {} TO {}{}").format(
                    sql.SQL(privilege),
                    sql.Identifier(parameter),
                    sql.SQL("PUBLIC") if target == "PUBLIC" else sql.Identifier(target),
                    sql.SQL(" WITH GRANT OPTION" if option else ""),
                )
            )

        def revoke(target):
            admin.execute(
                sql.SQL("REVOKE ALL ON PARAMETER {} FROM {}").format(
                    sql.Identifier(parameter),
                    sql.SQL("PUBLIC") if target == "PUBLIC" else sql.Identifier(target),
                )
            )

        try:
            if case == "p1_default":
                assert not admin.execute(
                    "SELECT has_parameter_privilege(%s,'work_mem','SET')", (actor_oid,)
                ).fetchone()[0]
                # Native GUC USERSET permission is independent of extra parameter ACLs.
                with s.connect("requester") as requester:
                    requester.execute("SET work_mem='8MB'")
                    assert requester.execute("SHOW work_mem").fetchone()[0] == "8MB"
                facts = _actual_parameter_facts(admin, actor_oid)
                assert not any(f["object_name"] == "work_mem" for f in facts)
                _checked(s)
                return
            if case.startswith("p6_"):
                # Actual native row/OID first; only the impossible NULL/empty/absence shape is
                # controlled catalog fault injection, visible to the private helper in this txn.
                grant(other)
                original = admin.execute(
                    "SELECT oid,paracl FROM pg_parameter_acl WHERE parname=%s", (parameter,)
                ).fetchone()
                with admin.transaction(force_rollback=True):
                    if case == "p6_absent":
                        admin.execute("DELETE FROM pg_parameter_acl WHERE parname=%s", (parameter,))
                    else:
                        admin.execute(
                            "UPDATE pg_parameter_acl SET paracl="
                            + ("NULL" if case == "p6_null" else "'{}'::aclitem[]")
                            + " WHERE parname=%s",
                            (parameter,),
                        )
                    facts = _actual_parameter_facts(admin, actor_oid)
                    selected = [f for f in facts if f["object_name"] == parameter]
                    if case == "p6_absent":
                        assert selected == []
                    else:
                        assert (
                            len(selected) == 1
                            and selected[0]["object_oid"] == original[0]
                            and selected[0]["owner_oid"] is None
                        )
                        assert selected[0]["acl"] == (None if case == "p6_null" else [])
                    from app.modules.identity.source_primitives import fingerprint

                    vector = fingerprint("identity.source.v1", selected)
                    if case != "p6_absent":
                        alternate = copy.deepcopy(selected)
                        alternate[0]["acl"] = [] if case == "p6_null" else None
                        assert fingerprint("identity.source.v1", alternate) != vector
                assert (
                    admin.execute(
                        "SELECT oid,paracl FROM pg_parameter_acl WHERE parname=%s", (parameter,)
                    ).fetchone()
                    == original
                )
                return
            if case == "p7_overflow":
                prefix = "menuto_itr.overflow_" + uuid4().hex[:12] + "_"
                try:
                    for n in range(4097):
                        admin.execute(
                            sql.SQL("GRANT SET ON PARAMETER {} TO {}").format(
                                sql.Identifier(prefix + str(n)), sql.Identifier(other)
                            )
                        )
                    assert (
                        admin.execute(
                            "SELECT count(*) FROM pg_parameter_acl WHERE parname LIKE %s",
                            (prefix + "%",),
                        ).fetchone()[0]
                        == 4097
                    )
                    with pytest.raises(psycopg.errors.ProgramLimitExceeded):
                        s.capture()
                finally:
                    # Dedicated fixture role has no content objects; revoke its actual native ACLs.
                    admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(other)))

                return
            public = case.startswith("p4_public")
            inherited = "inherit_" in case
            positive = (
                case in {"p2_real_row", "p7_custom", "p7_other_grantee"}
                or "inherit_false" in case
                or "revoke_" in case
            )
            target = (
                "PUBLIC" if public else other if inherited or positive else s.roles["requester"]
            )
            # The revoke variants first exercise an actual unsafe requester grant.
            if "revoke_" in case:
                target = s.roles["requester"]
            if inherited:
                admin.execute(
                    sql.SQL("GRANT {} TO {} WITH INHERIT {},SET FALSE,ADMIN FALSE").format(
                        sql.Identifier(other),
                        sql.Identifier(s.roles["requester"]),
                        sql.SQL("FALSE" if "inherit_false" in case else "TRUE"),
                    )
                )
            # Capture the actual native graph AFTER role membership, BEFORE the unsafe ACL.
            # Otherwise the forged frame contains another role's ACL but omits the only edge
            # that could make that ACL effective for this login.
            before_source = _checked(s)
            if inherited:
                native = admin.execute(
                    """SELECT roleid::bigint,member::bigint,grantor::bigint,
                    inherit_option,set_option,admin_option FROM pg_auth_members
                    WHERE roleid=(SELECT oid FROM pg_roles WHERE rolname=%s) AND member=%s""",
                    (other, actor_oid),
                ).fetchone()
                edge = dict(
                    zip(
                        (
                            "role_oid",
                            "member_oid",
                            "grantor_oid",
                            "inherit_option",
                            "set_option",
                            "admin_option",
                        ),
                        native,
                        strict=True,
                    ),
                    version=1,
                )
                for retained in (
                    before_source["frame"]["session_start"],
                    before_source["frame"]["session_end"],
                ):
                    assert edge in retained["edges"]
                    assert native[0] in {r["role_oid"] for r in retained["roles"]}
            if "cross_database" in case:
                with s.server["maintenance"].connect() as connection:
                    grant(target, connection=connection.connection.driver_connection)
            else:
                grant(target, option="grant_option" in case)
            if "revoke_" in case:
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    s.capture()
                revoke(target)
            facts = _actual_parameter_facts(admin, actor_oid)
            selected = next((f for f in facts if f["object_name"] == parameter), None)
            if "revoke_" not in case:
                assert selected is not None and selected["owner_oid"] is None
                oid = admin.execute(
                    "SELECT oid FROM pg_parameter_acl WHERE parname=%s", (parameter,)
                ).fetchone()[0]
                assert selected["object_oid"] == oid
            oracle = admin.execute(
                "SELECT has_parameter_privilege(%s,%s,%s)", (actor_oid, parameter, privilege)
            ).fetchone()[0]
            if positive:
                assert not oracle
                source = _checked(s)
                actual = [
                    o
                    for o in source["frame"]["session_start"]["objects"]
                    if o["kind"] == "PARAMETER" and o["object_name"] == parameter
                ]
                assert actual == ([] if selected is None else [selected])
            else:
                assert oracle
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    s.capture()
                # Rehashed favorable classifications cannot override an actual unsafe raw ACL.
                forged = copy.deepcopy(before_source)
                for session in (forged["frame"]["session_start"], forged["frame"]["session_end"]):
                    session["objects"].append(copy.deepcopy(selected))
                forged["source_fingerprint"] = h(
                    "identity.source.v1",
                    {k: v for k, v in forged.items() if k != "source_fingerprint"},
                )
                checked = check_identity_source_v1(forged, s.raw)
                assert checked.decision == "INCONSISTENT" and checked.reconstructed_outcome is None
                assert checked.numerical_use == "NOT_ADMITTED"
        finally:
            # Only this random TEST_ONLY parameter/role is changed, in the disposable cluster.
            try:
                revoke("PUBLIC")
            except psycopg.Error:
                pass
            try:
                revoke(s.roles["requester"])
            except psycopg.Error:
                pass
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(other)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(other)))
