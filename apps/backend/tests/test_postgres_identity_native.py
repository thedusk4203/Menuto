"""Native sslinfo dual-layout proofs inside existing Identity obligations; TEST_ONLY."""

import copy
import json
import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from app.modules.identity.source_replay import validate_identity_source_v1
from app.modules.validation.identity_source import check_identity_source_v1
from identity_postgres_fixtures import new_identity_scenario
from identity_source_fixtures import rehash
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.postgres
NAMES = {
    "ssl_is_used",
    "ssl_version",
    "ssl_cipher",
    "ssl_client_cert_present",
    "ssl_client_serial",
    "ssl_client_dn",
    "ssl_issuer_dn",
    "ssl_client_dn_field",
    "ssl_issuer_field",
    "ssl_extension_info",
}


def _upgrade(url, target="head"):
    engine = create_engine(url)
    try:
        with engine.connect() as db:
            cfg = Config(str(ROOT / "alembic.ini"))
            cfg.attributes["connection"] = db
            command.upgrade(cfg, target)
            db.commit()
    finally:
        engine.dispose()


@pytest.fixture(scope="module", params=["menuto_prior", "public"])
def native_server(request):
    url = make_url(os.environ["MENUTO_TEST_POSTGRES_URL"])
    assert url.host in {"localhost", "127.0.0.1", "::1"} and url.query["sslmode"] == "verify-full"
    maintenance = create_engine(url).execution_options(isolation_level="AUTOCOMMIT")
    template = "itr_native_" + uuid4().hex
    with maintenance.connect() as db:
        assert db.exec_driver_sql("SHOW server_version_num").scalar_one() == "180004"
        db.exec_driver_sql(f'CREATE DATABASE "{template}"')
    if request.param == "public":
        engine = create_engine(url.set(database=template))
        with engine.begin() as db:
            db.exec_driver_sql("CREATE EXTENSION sslinfo WITH SCHEMA public")
        engine.dispose()
    try:
        _upgrade(url.set(database=template))
        yield dict(url=url, maintenance=maintenance, template=template, namespace=request.param)
    finally:
        with maintenance.connect() as db:
            db.exec_driver_sql(f'DROP DATABASE "{template}" WITH(FORCE)')
        maintenance.dispose()


@pytest.fixture
def native_scenario(native_server):
    with new_identity_scenario(native_server) as s:
        yield s


def _check(s):
    source = s.capture()
    assert source["outcome"] == "AVAILABLE_AT_RETAINED_CUT"
    assert validate_identity_source_v1(source, s.raw).outcome == source["outcome"]
    report = check_identity_source_v1(source, s.raw)
    assert report.decision == "CONSISTENT" and report.numerical_use == "NOT_ADMITTED"
    return source


def test_itr018_native_layout_catalog(native_scenario, record_property):
    s = native_scenario
    ns = s.server["namespace"]
    source = _check(s)
    manifest = json.loads(
        (ROOT / "docs/product/IDENTITY_NATIVE_SSLINFO_SEMANTIC_MANIFEST.json").read_text()
    )
    with s.connect() as db:
        rows = db.execute(
            "SELECT p.oid::bigint function_oid,e.oid::bigint "
            "extension_oid,e.extversion,n.nspname namespace,\n"
            "            "
            "p.proname,pg_get_function_identity_arguments(p.oid) "
            "arguments,pg_get_function_result(p.oid) result,\n"
            "            p.proowner::bigint owner_oid,r.rolname owner_n"
            "ame,r.rolsuper,l.lanname,p.prosecdef,p.prosrc,p.probin,\n"
            "            p.proacl::text "
            "raw_acl,d.classid::regclass::text "
            "classid,d.objid::bigint,d.refclassid::regclass::text "
            "refclassid,\n"
            "            d.refobjid::bigint,d.deptype\n"
            "            FROM pg_extension e JOIN pg_namespace n ON "
            "n.oid=e.extnamespace JOIN pg_proc p ON "
            "p.pronamespace=n.oid\n"
            "            JOIN pg_depend d ON "
            "d.classid='pg_proc'::regclass AND d.objid=p.oid AND "
            "d.refclassid='pg_extension'::regclass AND d.refobjid=e.oid"
            " AND d.deptype='e'\n"
            "            JOIN pg_roles r ON r.oid=p.proowner JOIN "
            "pg_language l ON l.oid=p.prolang\n"
            "            WHERE e.extname='sslinfo' ORDER BY p.oid"
        ).fetchall()
        assert len(rows) == 10 and {x[4] for x in rows} == NAMES
        facts = {
            x["object_oid"]: x
            for x in source["frame"]["session_start"]["objects"]
            if x["kind"] == "FUNCTION"
        }
        for x in rows:
            assert x[2] == "1.2" and x[3] == ns and x[9] and x[10] == "c" and not x[11]
            assert (
                x[12] == x[4]
                and x[13] == "$libdir/sslinfo"
                and x[16] == x[0]
                and x[18] == x[1]
                and x[19] == "e"
            )
            assert facts[x[0]]["definition_fingerprint"] == manifest["fingerprints"][ns][x[4]]
        public = [x for x in facts.values() if x["schema_name"] == "public"]
        assert len(public) == (68 if ns == "menuto_prior" else 78)
        assert len([x for x in public if x["object_name"] not in NAMES]) == 68
        dep = db.execute(
            "SELECT p.prosqlbody IS NOT NULL,p.proowner::regrole::text,"
            "p.prosecdef,p.proconfig,d.refobjid::bigint\n"
            "            FROM pg_proc p JOIN pg_namespace n ON "
            "n.oid=p.pronamespace JOIN pg_depend d ON d.objid=p.oid AND"
            " d.classid='pg_proc'::regclass\n"
            "            WHERE n.nspname='menuto_identity_source' AND "
            "p.proname='_tls_fact_v1' AND "
            "d.refclassid='pg_proc'::regclass"
        ).fetchall()
        target = next(x[0] for x in rows if x[4] == "ssl_is_used")
        assert any(
            x[0] and x[1] == "menuto_identity_source_owner" and x[2] and x[4] == target for x in dep
        )
        with db.transaction():
            db.execute("SET LOCAL ROLE menuto_identity_source_owner")
            assert db.execute("SELECT menuto_identity_source._tls_fact_v1()").fetchone()[0] == {
                "tls": True
            }
        assert (
            db.execute("SELECT system_user").fetchone()[0]
            == "scram-sha-256:" + s.roles["bootstrap"]
        )
    with s.connect(sslmode="disable") as db, db.transaction():
        db.execute("SET LOCAL ROLE menuto_identity_source_owner")
        assert db.execute("SELECT menuto_identity_source._tls_fact_v1()").fetchone()[0] == {
            "tls": False
        }
    with s.connect("requester", sslmode="disable") as db, db.transaction():
        with pytest.raises(psycopg.Error) as err, db.transaction():
            db.execute(
                "SELECT menuto_identity_source.capture_request_source(%s)", (json.dumps(s.raw),)
            )
        assert err.value.sqlstate == "42501"
    record_property(
        "native_catalog",
        json.dumps(
            dict(namespace=ns, rows=rows, public_count=len(public), parsed_tls_dependency=dep),
            default=str,
        ),
    )


def test_itr019_native_isolation(native_scenario, tmp_path, record_property):
    s = native_scenario
    from test_postgres_identity_source import (
        test_itr008_actual_wrong_password,
        test_itr012_verified_endpoint,
    )

    test_itr008_actual_wrong_password(s)
    test_itr012_verified_endpoint(s, tmp_path)
    with s.connect() as db:
        foreign = db.execute(
            "SELECT n.nspname,p.proname,has_function_privilege('menuto_"
            "identity_source_owner',p.oid,'EXECUTE')\n"
            "            FROM pg_proc p JOIN pg_namespace n ON "
            "n.oid=p.pronamespace WHERE n.nspname IN('menuto_prior','me"
            "nuto_hierarchy','menuto_nutrition','menuto_nutrition_synth"
            "esis')\n"
            "            AND NOT EXISTS(SELECT FROM pg_depend d WHERE "
            "d.classid='pg_proc'::regclass AND d.objid=p.oid AND "
            "d.refclassid='pg_extension'::regclass AND d.deptype='e')"
        ).fetchall()
        assert foreign and not any(x[2] for x in foreign)
        record_property("native_negative_function_matrix", json.dumps(foreign))
        assert not any(
            x[0]
            for x in db.execute(
                "SELECT has_table_privilege('menuto_identity_source_owner',"
                "c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRI"
                "GGER')\n"
                "            FROM pg_class c JOIN pg_namespace n ON "
                "n.oid=c.relnamespace WHERE n.nspname IN('menuto_prior','me"
                "nuto_hierarchy','menuto_nutrition','menuto_nutrition_synth"
                "esis') AND c.relkind='r'"
            )
        )
        assert not db.execute(
            "SELECT pg_has_role('menuto_identity_source_owner','pg_read_all_stats','USAGE')"
        ).fetchone()[0]
    _check(s)


MUTATIONS = (
    "extra_public",
    "eleventh_member",
    "overload",
    "shadow",
    "lost_member",
    "binary",
    "symbol",
    "definer",
    "owner",
    "acl",
    "schema_create",
    "role_escalation",
    "replacement",
    "moved_function",
    "tls_symbol",
    "tls_definer",
)


@pytest.mark.parametrize("mutation", MUTATIONS)
def test_itr020_native_mutations(native_scenario, mutation):
    s = native_scenario
    ns = s.server["namespace"]
    _check(s)
    statements = {
        ("tls_symbol"): (
            f"CREATE OR REPLACE FUNCTION {ns}.ssl_is_used() RETURNS "
            f"boolean AS '$libdir/sslinfo','ssl_client_cert_present' "
            f"LANGUAGE c STRICT PARALLEL RESTRICTED"
        ),
        "tls_definer": f"ALTER FUNCTION {ns}.ssl_is_used() SECURITY DEFINER",
        ("extra_public"): (
            "CREATE FUNCTION public.TEST_ONLY_eleventh() RETURNS int LANGUAGE sql AS $$SELECT 1$$"
        ),
        ("eleventh_member"): (
            f"CREATE FUNCTION {ns}.TEST_ONLY_extra() RETURNS int "
            f"LANGUAGE sql AS $$SELECT 1$$; ALTER EXTENSION sslinfo ADD "
            f"FUNCTION {ns}.TEST_ONLY_extra()"
        ),
        ("overload"): (
            f"CREATE FUNCTION {ns}.ssl_version(text) RETURNS text LANGUAGE sql AS $$SELECT $1$$"
        ),
        ("shadow"): (
            "CREATE SCHEMA TEST_ONLY_shadow; CREATE FUNCTION "
            "TEST_ONLY_shadow.ssl_version() RETURNS text LANGUAGE sql "
            "AS $$SELECT NULL::text$$"
        ),
        "lost_member": f"ALTER EXTENSION sslinfo DROP FUNCTION {ns}.ssl_version()",
        ("binary"): (
            f"CREATE OR REPLACE FUNCTION {ns}.ssl_version() RETURNS "
            f"text AS '$libdir/./sslinfo','ssl_version' LANGUAGE c "
            f"STRICT PARALLEL RESTRICTED"
        ),
        ("symbol"): (
            f"CREATE OR REPLACE FUNCTION {ns}.ssl_version() RETURNS "
            f"text AS '$libdir/sslinfo','ssl_cipher' LANGUAGE c STRICT "
            f"PARALLEL RESTRICTED"
        ),
        "definer": f"ALTER FUNCTION {ns}.ssl_version() SECURITY DEFINER",
        "owner": f"ALTER FUNCTION {ns}.ssl_version() OWNER TO {s.roles['requester']}",
        ("acl"): (
            f"GRANT EXECUTE ON FUNCTION {ns}.ssl_version() TO "
            f"{s.roles['requester']} WITH GRANT OPTION"
        ),
        "schema_create": f"GRANT CREATE ON SCHEMA {ns} TO {s.roles['requester']}",
        "role_escalation": f"GRANT menuto_identity_source_owner TO {s.roles['requester']}",
        ("replacement"): (
            f"ALTER EXTENSION sslinfo DROP FUNCTION {ns}.ssl_version(); "
            f"DROP FUNCTION {ns}.ssl_version(); CREATE FUNCTION "
            f"{ns}.ssl_version() RETURNS text AS "
            f"'$libdir/sslinfo','ssl_version' LANGUAGE c STRICT "
            f"PARALLEL RESTRICTED; ALTER EXTENSION sslinfo ADD FUNCTION "
            f"{ns}.ssl_version()"
        ),
        ("moved_function"): (
            f"CREATE SCHEMA TEST_ONLY_moved; ALTER FUNCTION "
            f"{ns}.ssl_version() SET SCHEMA TEST_ONLY_moved"
        ),
    }
    with s.connect() as db:
        db.execute(statements[mutation])
    with pytest.raises(psycopg.Error) as err:
        s.capture()
    assert err.value.sqlstate == "42501"
    assert s.counts()[:4] == (1, 1, 1, 1)


@pytest.mark.parametrize(
    "mutation",
    (
        "omission",
        "fingerprint",
        "owner",
        "acl",
        "new_function",
        "oid_contradiction",
        "unrelated_schema_create",
    ),
)
def test_itr055_native_offline_forgeries(native_scenario, mutation):
    s = native_scenario
    source = _check(s)
    sessions = [source["frame"]["session_start"], source["frame"]["session_end"]] + [
        x["author"]
        for key in ("root_history", "issuer_history", "binding_history", "grant_history")
        for x in source[key]
    ]
    for session in sessions:
        item = next(
            x
            for x in session["objects"]
            if x["kind"] == "FUNCTION" and x["object_name"] == "ssl_version"
        )
        if mutation == "unrelated_schema_create":
            schema = next(
                x
                for x in session["objects"]
                if x["kind"] == "SCHEMA" and x["object_name"] == s.server["namespace"]
            )
            schema["acl"].append(
                [session["execution_owner_oid"], schema["owner_oid"], "CREATE", False]
            )
            schema["acl"].sort()
        if mutation == "omission":
            session["objects"].remove(item)
        elif mutation == "fingerprint":
            item["definition_fingerprint"] = "0" * 64
        elif mutation == "owner":
            item["owner_oid"] = session["execution_owner_oid"]
        elif mutation == "acl":
            item["acl"].append([session["login_role_oid"], item["owner_oid"], "EXECUTE", True])
            item["acl"].sort()
        elif mutation == "new_function":
            copied = copy.deepcopy(item)
            copied.update(object_name="TEST_ONLY_unknown_native", object_oid=2000000000)
            session["objects"].append(copied)
            session["objects"].sort(key=lambda x: (x["kind"], x["object_oid"], x["sub_id"]))
    if mutation == "oid_contradiction":
        next(
            x
            for x in source["frame"]["session_end"]["objects"]
            if x["object_name"] == "ssl_version"
        )["object_oid"] = 2000000001
    rehash(source)
    assert check_identity_source_v1(source, s.raw).decision == "INCONSISTENT"
    with pytest.raises(ValueError):
        validate_identity_source_v1(source, s.raw)


def test_itr066_native_coherent_transport_limit(native_scenario):
    s = native_scenario
    source = _check(s)
    for session in [source["frame"]["session_start"], source["frame"]["session_end"]] + [
        x["author"]
        for k in ("root_history", "issuer_history", "binding_history", "grant_history")
        for x in source[k]
    ]:
        for row in session["objects"]:
            if row["kind"] == "FUNCTION" and row["object_name"] in NAMES:
                row["object_oid"] += 100000000
        session["objects"].sort(key=lambda x: (x["kind"], x["object_oid"], x["sub_id"]))
    rehash(source)
    report = check_identity_source_v1(source, s.raw)
    assert report.decision == "CONSISTENT" and report.numerical_use == "NOT_ADMITTED"
    assert validate_identity_source_v1(source, s.raw).frame.transport == "UNVERIFIED_TRANSPORT"


def test_itr001_native_downgrade_ledger(native_server, record_property):
    server = native_server
    name = "itr_native_down_" + uuid4().hex
    ns = server["namespace"]
    url = server["url"].set(database=name)
    with server["maintenance"].connect() as db:
        db.exec_driver_sql(f'CREATE DATABASE "{name}"')
    engine = create_engine(url)
    try:
        if ns == "public":
            with engine.begin() as db:
                db.exec_driver_sql("CREATE EXTENSION sslinfo WITH SCHEMA public")
        _upgrade(url, "0017")
        with engine.begin() as db:
            # These same two approved privileges preexist this particular install and must survive.
            db.exec_driver_sql(f"GRANT USAGE ON SCHEMA {ns} TO menuto_identity_source_owner")
            db.exec_driver_sql(
                f"GRANT EXECUTE ON FUNCTION {ns}.ssl_is_used() TO menuto_identity_source_owner"
            )
        query = (
            "SELECT n.nspacl::text,(SELECT "
            "jsonb_agg(jsonb_build_array(p.oid::bigint,p.proacl::text) "
            "ORDER BY p.oid) FROM pg_proc p WHERE p.pronamespace=n.oid)"
            "\n"
            "            FROM pg_namespace n WHERE n.nspname=:ns"
        )
        from sqlalchemy import text

        with engine.connect() as db:
            before = db.execute(text(query), {"ns": ns}).one()
        _upgrade(url)
        with engine.connect() as db:
            cfg = Config(str(ROOT / "alembic.ini"))
            cfg.attributes["connection"] = db
            command.downgrade(cfg, "0017")
            db.commit()
            after = db.execute(text(query), {"ns": ns}).one()
            assert before == after
            record_property(
                "shared_acl_downgrade",
                json.dumps(dict(namespace=ns, before=list(before), after=list(after))),
            )
            assert (
                db.exec_driver_sql(
                    "SELECT count(*) FROM pg_extension WHERE extname='sslinfo'"
                ).scalar_one()
                == 1
            )
    finally:
        engine.dispose()
        with server["maintenance"].connect() as db:
            db.exec_driver_sql(f'DROP DATABASE "{name}" WITH(FORCE)')


@pytest.mark.parametrize("fault", ("namespace", "fake_member", "unsafe_create", "extra_member"))
def test_itr020_native_install_preconditions(native_server, fault):
    server = native_server
    name = "itr_native_reject_" + uuid4().hex
    url = server["url"].set(database=name)
    with server["maintenance"].connect() as db:
        db.exec_driver_sql(f'CREATE DATABASE "{name}"')
    engine = create_engine(url)
    try:
        namespace = "TEST_ONLY_unsupported" if fault == "namespace" else server["namespace"]
        if fault == "namespace" or namespace == "public":
            with engine.begin() as db:
                if fault == "namespace":
                    db.exec_driver_sql('CREATE SCHEMA "TEST_ONLY_unsupported"')
                db.exec_driver_sql(f'CREATE EXTENSION sslinfo WITH SCHEMA "{namespace}"')
        _upgrade(url, "0017")
        with engine.begin() as db:
            if fault == "fake_member":
                db.exec_driver_sql(
                    f"ALTER EXTENSION sslinfo DROP FUNCTION {namespace}.ssl_version()"
                )
            elif fault == "unsafe_create":
                db.exec_driver_sql(f"GRANT CREATE ON SCHEMA {namespace} TO PUBLIC")
            elif fault == "extra_member":
                db.exec_driver_sql(
                    f"CREATE FUNCTION {namespace}.TEST_ONLY_extra() RETURNS int "
                    f"LANGUAGE sql AS $$SELECT 1$$"
                )
                db.exec_driver_sql(
                    f"ALTER EXTENSION sslinfo ADD FUNCTION {namespace}.TEST_ONLY_extra()"
                )
        with pytest.raises(RuntimeError, match="Identity"):
            _upgrade(url)
        with engine.connect() as db:
            assert (
                db.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one() == "0017"
            )
            assert (
                db.exec_driver_sql(
                    "SELECT count(*) FROM pg_namespace WHERE nspname='menuto_identity_source'"
                ).scalar_one()
                == 0
            )
    finally:
        engine.dispose()
        with server["maintenance"].connect() as db:
            db.exec_driver_sql(f'DROP DATABASE "{name}" WITH(FORCE)')
