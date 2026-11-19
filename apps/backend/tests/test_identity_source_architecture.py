"""ITR081–096 executable compatibility, ownership and delivery guards."""

import ast
import hashlib
import inspect
import json
import re
import runpy
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from identity_compatibility_metadata import (
    IDENTITY_EXPORT_NAMES,
    _package,
    assert_identity_migration_delta,
    restore_identity_metadata,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"
APP = ROOT / "apps/backend"
CHECKER = "app.modules.validation.identity_source"
EVIDENCE = ROOT / "docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_IMPLEMENTATION_EVIDENCE.md"


def _json(name):
    return json.loads((FIXTURES / (name + ".json")).read_text())


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def _defs():
    return json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]


def _module(name):
    return APP / (name.replace(".", "/") + ".py")


def _imports(body):
    for node in ast.walk(ast.parse(body)):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                child = node.module + "." + alias.name
                yield child if _module(child).is_file() else node.module


def _independent_graph(overrides=None):
    overrides = overrides or {}
    pending = [CHECKER]
    seen = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        body = overrides[name] if name in overrides else _module(name).read_text()
        for target in _imports(body):
            if target.startswith("app.modules.identity"):
                assert target == "app.modules.identity.source_contracts", target
            elif target.startswith("app.modules."):
                assert target.startswith("app.modules.validation."), target
                pending.append(target)
            assert not target.startswith(
                ("app.shared.db", "app.persistence", "psycopg", "sqlalchemy")
            ), target
        tree = ast.parse(body)
        assert not any(
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id in {"eval", "exec", "__import__", "open"}
            for n in ast.walk(tree)
        )
    return seen


def _identity_purity():
    for name in (
        "source_contracts",
        "source_limits",
        "source_primitives",
        "source_replay",
        "source_routine_manifest",
    ):
        body = _module("app.modules.identity." + name).read_text()
        tree = ast.parse(body)
        assert not any(
            target.split(".")[0]
            in {
                "os",
                "time",
                "pathlib",
                "socket",
                "subprocess",
                "sqlalchemy",
                "psycopg",
                "importlib",
            }
            for target in _imports(body)
        ), name
        assert not any(
            isinstance(n, ast.Call)
            and (
                (
                    isinstance(n.func, ast.Name)
                    and n.func.id in {"open", "eval", "exec", "__import__"}
                )
                or (isinstance(n.func, ast.Attribute) and n.func.attr in {"now", "utcnow", "time"})
            )
            for n in ast.walk(tree)
        ), name


def test_itr081_537_body_baseline():
    proof = _json("identity_source_compatibility")
    actual = _defs()
    assert proof["base"] == "120d28f62b66720e8631b64e0b2a50cdc57e6c42"
    assert len(proof["definitions"]) == len(proof["definition_bodies"]) == 537
    for name, body in proof["definition_bodies"].items():
        assert actual[name] == body, name
        assert (
            _hash(json.dumps(actual[name], sort_keys=True, separators=(",", ":")).encode())
            == proof["definitions"][name]
        ), name


def test_itr082_exact19_name_manifest():
    old = set(_json("identity_source_compatibility")["definitions"])
    manifest = _json("identity_source_export_names")
    assert manifest == list(IDENTITY_EXPORT_NAMES) and len(set(manifest)) == 19
    assert len(_defs()) == 556 and set(_defs()) - old == set(manifest)
    # Registration and the literal manifest are separate inputs; actual exports cannot mint names.
    exporter = (ROOT / "tools/export_domain_contracts.py").read_text()
    assert all(re.search(r"\b" + name + r"\b", exporter) for name in manifest)


def test_itr083_historical_pins():
    actual = _defs()
    for filename, count, files in (
        ("basis_compatibility", 503, 53),
        ("policy_v2_compatibility", 515, 59),
    ):
        proof = _json(filename)
        assert len(proof["definitions"]) == count and len(proof["frozen_files"]) == files
        for name, value in proof["definitions"].items():
            assert (
                _hash(json.dumps(actual[name], sort_keys=True, separators=(",", ":")).encode())
                == value
            ), name
        for name, value in proof["frozen_files"].items():
            assert _hash((ROOT / name).read_bytes()) == value, name
    runtime = _json("identity_source_frozen_runtime")
    assert runtime["base"] == "68fcb688231460f1973077eb20140b8c5db440a2"
    assert len(runtime["files"]) == 185
    for name, value in runtime["files"].items():
        assert _hash((ROOT / name).read_bytes()) == value, name


def test_itr084_baseline_test_identities():
    proof = _json("identity_source_compatibility")
    assert len(proof["baseline_tests"]) == 4611
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-o", "addopts=", "--collect-only", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout[-2000:]
    current = [
        line for line in result.stdout.splitlines() if "::" in line and not line.startswith(" ")
    ]

    def identity(node):
        return re.sub(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", "<UUID>", node)

    assert not (Counter(map(identity, proof["baseline_tests"])) - Counter(map(identity, current)))
    epi = (ROOT / "apps/backend/tests/test_explicit_plan_intent.py").read_text()
    assert {int(x) for x in re.findall(r"def test_epi(\d{3})_", epi)} == set(range(1, 65))


def test_itr085_identity_ownership():
    _identity_purity()
    for path in (APP / "app/modules/identity").glob("source_*.py"):
        for target in _imports(path.read_text()):
            if target.startswith("app.modules."):
                assert target.startswith("app.modules.identity."), target
    from app.modules.identity.source_models import IdentitySourceBase
    from app.shared.db import Base

    assert len(IdentitySourceBase.metadata.tables) == 6
    assert IdentitySourceBase.metadata is not Base.metadata


def test_itr086_validation_independence():
    _independent_graph()
    for body in (
        "from app.modules.identity.source_replay import validate_identity_source_v1",
        "from app.modules.identity import source_capture",
        "from app.modules.identity import source_public",
    ):
        with pytest.raises(AssertionError):
            _independent_graph({CHECKER: body})
        with pytest.raises(AssertionError):
            _independent_graph(
                {
                    CHECKER: "from app.modules.validation.hidden_identity import checker",
                    "app.modules.validation.hidden_identity": body,
                }
            )
    check = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]
    assert check(
        "from app.modules.identity.source_replay import validate_identity_source_v1", CHECKER
    )
    assert not check(
        "from app.modules.identity.source_contracts import IdentitySourceSnapshotV1", CHECKER
    )


def test_itr087_planning_integration():
    from app.modules.planning.identity_source_inspection import (
        inspect_authenticated_explicit_plan_intent_v1 as inspect_live,
    )

    assert list(inspect.signature(inspect_live).parameters) == [
        "connection",
        "request_binding",
        "context",
    ]
    for forbidden in ("source", "report", "lease", "callback", "admission"):
        with pytest.raises(TypeError):
            inspect_live(None, None, context=None, **{forbidden: object()})
    body = _module("app.modules.planning.identity_source_inspection").read_text()
    assert body.index("source = capture_identity_request_source_v1(") < body.index(
        "source_check = check_identity_source_v1("
    )
    assert not any(isinstance(n, ast.Global) for n in ast.walk(ast.parse(body)))


def test_itr088_sql_inventory():
    migration = runpy.run_path(
        str(ROOT / "apps/backend/migrations/versions/0018_identity_principal_user_sources.py")
    )
    table_sql, functions = migration["TABLE_SQL"], migration["FUNCTION_SQL"]
    names = re.findall(r"CREATE FUNCTION menuto_identity_source\.([a-z0-9_]+)\(", functions)
    assert len(names) == len(set(names)) == 17
    entries = {
        "bootstrap_root",
        "change_issuer",
        "change_binding",
        "change_operation_grant",
        "capture_request_source",
    }
    assert (
        set(migration["ENTRIES"]) == entries
        and set(n for n in names if not n.startswith("_")) == entries
    )
    definers = {
        block.split("(", 1)[0]
        for block in functions.split("CREATE FUNCTION menuto_identity_source.")[1:]
        if "SECURITY DEFINER" in block.split("AS $", 1)[0]
    }
    assert definers == entries | {"_tls_fact_v1"}  # Private OID-bound helper, never an actor entry.
    assert functions.count("SET search_path=pg_catalog,menuto_identity_source,pg_temp") == 17
    assert set(re.findall(r"CREATE TABLE menuto_identity_source\.([a-z_]+)", table_sql)) == set(
        migration["TABLES"]
    )
    assert len(migration["TABLES"]) == 6 and len(migration["ROLES"]) == 4
    text = (
        ROOT / "apps/backend/migrations/versions/0018_identity_principal_user_sources.py"
    ).read_text()
    upgrade = inspect.getsource(migration["upgrade"])
    assert "GRANT USAGE ON SCHEMA {namespace} TO menuto_identity_source_owner" in upgrade
    assert (
        "GRANT EXECUTE ON FUNCTION {namespace}.ssl_is_used() TO menuto_identity_source_owner"
        in upgrade
    )
    assert "pg_read_all_stats" not in text and "menuto_prior.backend_tls(" not in functions
    assert "THEN __TLS_NAMESPACE__.ssl_is_used()" in functions
    assert "__TLS_FUNCTION_OID__" in functions and "__TLS_EXTENSION_OID__" in functions
    assert "p.prosecdef" in migration["NATIVE_CATALOG_SQL"]
    assert set(migration["NATIVE_SSLINFO_PINS"]) == {"public", "menuto_prior"}
    assert all(len(v) == 10 for v in migration["NATIVE_SSLINFO_PINS"].values())


def test_itr089_migration_safety():
    assert_identity_migration_delta(ROOT)
    source = (
        ROOT / "apps/backend/migrations/versions/0018_identity_principal_user_sources.py"
    ).read_text()
    tree = ast.parse(source)
    downgrade = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "downgrade"
    )
    body = ast.get_source_segment(source, downgrade)
    assert body.index("downgrade refuses retained history") < body.index("DROP TRIGGER")
    assert "CASCADE" not in "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith("#")
    )
    assert "DROP EXTENSION" not in body and "DROP OWNED" not in body


def test_itr090_production_isolation():
    from app.modules.identity.source_contracts import IdentityRootCommandV1
    from identity_source_fixtures import authored

    body = authored("ROOT", 1)["command"]
    body["environment"] = "PRODUCTION"
    with pytest.raises(ValueError):
        IdentityRootCommandV1.model_validate_json(json.dumps(body))
    source = (
        ROOT / "apps/backend/migrations/versions/0018_identity_principal_user_sources.py"
    ).read_text()
    upgrade = next(
        n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "upgrade"
    )
    for n in ast.walk(upgrade):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            assert not re.match(r"\s*(INSERT|UPDATE|DELETE)\b", n.value, re.I)


def test_itr091_no_source_secrets():
    schema = _defs()
    for name in IDENTITY_EXPORT_NAMES:
        keys = set(schema[name].get("properties", {}))
        assert not keys & {
            "password",
            "rolpassword",
            "credential",
            "secret",
            "token",
            "verifier",
            "connection_url",
        }, name
    body = _module("app.modules.identity.source_capture").read_text()
    tree = ast.parse(body)
    assert not any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print"
        for n in ast.walk(tree)
    )
    assert (
        "rolpassword"
        not in (
            ROOT / "apps/backend/migrations/versions/0018_identity_principal_user_sources.py"
        ).read_text()
    )


def test_itr092_public_surface():
    for name in ("source_capture", "source_public", "source_replay"):
        body = _module("app.modules.identity." + name).read_text()
        assert not any(
            target.startswith(("fastapi", "app.api", "app.modules.nutrition", "app.modules.policy"))
            for target in _imports(body)
        )
    from app.modules.policy.authenticated_intent_contracts import (
        AuthenticatedPlanIntentInspectionV1,
    )

    fields = AuthenticatedPlanIntentInspectionV1.model_fields
    for name in ("planner_ready", "activation_ready", "resolved_plan_policy_ready"):
        assert fields[name].annotation.__origin__.__name__ == "Literal"
        assert fields[name].annotation.__args__ == (False,)


def test_itr093_readiness_gates():
    design = (
        ROOT / "docs/product/IDENTITY_PRINCIPAL_USER_ENROLLMENT_BOUNDED_DESIGN.md"
    ).read_text()
    assert "Full MTR-006/007/008 INCOMPLETE" in design
    assert "#5/#6/#7 OPEN" in design
    assert "Production Nutrition/clinical gate CLOSED" in design
    assert "PRECOMMIT FAIL-CLOSED" in design
    from app.modules.validation.identity_source import check_identity_source_v1
    from identity_source_fixtures import available_source

    source = available_source()
    report = check_identity_source_v1(source, source["binding"])
    assert report.transport == "UNVERIFIED_TRANSPORT" and report.numerical_use == "NOT_ADMITTED"
    assert not report.planner_ready and not report.activation_ready


def test_itr094_compatibility_approval():
    package = _package()
    assert len(package["files"]) == 35
    for name, proof in package["files"].items():
        body = (ROOT / name).read_text()
        original = restore_identity_metadata(name, body)
        assert _hash(original.encode()) == proof["before_sha256"], name
        with pytest.raises(AssertionError):
            restore_identity_metadata(name, body + "\n# unapproved change\n")
    # An unedited historical file remains hash-pinned; no generic pass-through allowance.
    baseline = _json("identity_source_compatibility")
    name = next(x for x in baseline["baseline_files"] if x not in package["files"])
    with pytest.raises(AssertionError):
        restore_identity_metadata(name, (ROOT / name).read_text() + "\n")
    with pytest.raises(AssertionError):
        restore_identity_metadata("unapproved/path.py", "")


def test_itr095_original_worktree_preservation():
    proof = _json("identity_original_worktree_preservation")
    assert proof["evidence"] == "AUTHOR_LOCAL_BYTE_VERIFICATION_NOT_REMOTE_ORIGIN_PROOF"
    assert proof["head_before"] == proof["head_after"] == "1679d6035dd6685118df6c95fa37628384cc961c"
    assert proof["status_sha256_before"] == proof["status_sha256_after"]
    assert len(proof["before"]) == len(proof["after"]) == 19
    assert (
        proof["before"] == proof["after"] == _json("identity_source_compatibility")["original_19"]
    )
    # CI verifies this retained attestation's integrity; actual external worktree bytes are
    # checked by the author before/after execution, never claimed as GitHub-origin proof.


def test_itr096_full_execution_evidence():
    paths = [
        ROOT / "apps/backend/tests" / name
        for name in (
            "test_postgres_identity_source.py",
            "test_postgres_identity_native.py",
            "test_identity_source.py",
            "test_identity_source_architecture.py",
        )
    ]
    by_group = {}
    for path in paths:
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.FunctionDef) and (
                match := re.match(r"test_itr(\d{3})_", node.name)
            ):
                by_group.setdefault(int(match[1]), []).append(
                    str(path.relative_to(ROOT)).replace("\\", "/") + "::" + node.name
                )
    assert set(by_group) == set(range(1, 97))
    assert all(
        any(
            name in path
            for name in ("test_postgres_identity_source.py", "test_postgres_identity_native.py")
        )
        for n in range(1, 49)
        for path in by_group[n]
    )
    matrix = _json("identity_itr_execution")
    assert matrix["baseline"] == "68fcb688231460f1973077eb20140b8c5db440a2"
    assert matrix["obligation_functions"] == {
        f"ITR{key:03}": sorted(val) for key, val in sorted(by_group.items())
    }
    assert matrix["real_postgres_groups"] == list(range(1, 49))
    doc = EVIDENCE.read_text()
    assert "ITR001–ITR096" in doc and "P1–P7" in doc and "PRODUCTION GATE CLOSED" in doc
    assert "not" in doc.lower() and "independent" in doc.lower()
    # Actual final full-suite/CI completion is a delivery gate, not a circular test that
    # pretends the in-progress CI run is already complete. Receipts record measured runs.
