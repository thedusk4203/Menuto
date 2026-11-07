"""NRC70–80: independent/pure source surfaces and frozen baseline retention."""

import ast
import hashlib
import json
import os
import re
import runpy
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from app.modules.nutrition import root_contracts as c

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"
CHECK = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "bad",
    [
        "import sqlalchemy",
        "import os",
        "import pathlib",
        "import socket",
        "import httpx",
        "open('TEST_ONLY')",
        "datetime.now()",
    ],
)
def test_nrc70_pure_resolver_guards_reject_io_and_live_clocks(bad):
    assert CHECK(bad, "app.modules.nutrition.root_resolution")
    source = read("apps/backend/app/modules/nutrition/root_resolution.py")
    assert not CHECK(source, "app.modules.nutrition.root_resolution")


@pytest.mark.parametrize(
    "target", ["root_resolution", "root_public", "root_sources", "root_admin", "models"]
)
def test_nrc71_independent_validation_only_immutable_companion(target):
    source = "from app.modules.nutrition import " + target
    assert CHECK(source, "app.modules.validation.nutrition_roots")
    assert not CHECK(
        "from app.modules.nutrition import root_contracts", "app.modules.validation.nutrition_roots"
    )
    # The exception must not grant other validators a new implementation surface.
    assert CHECK(
        "from app.modules.nutrition import root_contracts", "app.modules.validation.material"
    )


def test_nrc72_empty_ddl_no_production_content_seeding():
    path = ROOT / "apps/backend/migrations/versions/0016_nutrition_root_sources.py"
    tree = ast.parse(path.read_text())
    tables = next(
        n.value.value
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "TABLE_SQL" for t in n.targets)
    )
    assert "INSERT" not in tables and "CREATE SEQUENCE" in tables
    source = path.read_text()
    assert "NOLOGIN NOSUPERUSER" in source and "REVOKE ALL ON FUNCTION" in source
    assert "Refusing destructive downgrade" in source
    assert "seed" not in " ".join(t.name for t in ast.walk(tree) if isinstance(t, ast.FunctionDef))


def test_nrc73_no_environment_numeric_or_metabolic_safety_authority():
    for file in ("root_contracts.py", "root_resolution.py", "root_public.py", "root_limits.py"):
        source = read("apps/backend/app/modules/nutrition/" + file)
        assert not re.search(r"getenv|os\.environ|BMR|TDEE", source)
    assert c.NutritionGoalRevision.model_fields["direction"].is_required()
    assert c.NutritionRootAmount.model_fields["numerator"].is_required()


def test_nrc74_no_preferences_learning_or_foreign_authority_reuse():
    for path in (ROOT / "apps/backend/app/modules/nutrition").glob("root_*.py"):
        tree = ast.parse(path.read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
        assert not any(
            "preferences" in name or "learning" in name or "planning" in name for name in imports
        )
    assert set(c.NrcCapability.__args__) == {
        "GUIDELINE_REVIEW",
        "GUIDELINE_PUBLISH",
        "GUIDELINE_WITHDRAW",
        "ELIGIBILITY_ATTEST",
        "MEMBER_OBSERVATION_WRITE",
        "MEMBER_GOAL_WRITE",
        "ROOT_SOURCE_READ",
        "VALIDATOR_SOURCE_READ",
    }


def test_nrc75_no_http_planner_activation_or_full_policy_completion():
    for path in (ROOT / "apps/backend/app/modules/nutrition").glob("root_*.py"):
        source = path.read_text()
        assert "APIRouter" not in source and "@router" not in source
    schema = c.NutritionRootContract.model_json_schema()["properties"]
    assert (
        schema["planner_ready"]["const"] is False and schema["activation_ready"]["const"] is False
    )
    assert schema["policy_synthesis"]["const"] == "NOT_PERFORMED"
    assert schema["numeric_goal_protection"]["const"] == "NOT_SYNTHESIZED"
    facade = read("apps/backend/app/modules/nutrition/root_public.py")
    assert "root_admin" not in facade and "enroll_" not in facade


def test_nrc76_all_frozen_preference_learning_feature_definitions_unchanged():
    pins = json.loads((FIXTURES / "nutrition_root_compatibility.json").read_text())
    for name, digest in pins["frozen_files"].items():
        if (
            any("/" + part + "/" in name for part in ("preferences", "learning", "catalog"))
            or "tastefit" in name
        ):
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name


def test_nrc77_old_inventory_recipe_validation_and_migration_bytes_unchanged():
    pins = json.loads((FIXTURES / "nutrition_root_compatibility.json").read_text())
    for name, receipt in pins["append_only_files"].items():
        body = (ROOT / name).read_bytes()
        assert hashlib.sha256(body[: receipt["prefix_bytes"]]).hexdigest() == receipt["sha256"]
        assert body[receipt["prefix_bytes"] :] == receipt["suffix"].encode()
    for name, digest in pins["frozen_files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    files = sorted(
        p.name[:4]
        for p in (ROOT / "apps/backend/migrations/versions").glob("*.py")
        if p.name[:4].isdigit()
    )
    assert files == [f"{i:04d}" for i in range(1, 18)]


def test_nrc78_all403_definition_hashes_retained_exact_additive_exports():
    pins = json.loads((FIXTURES / "nutrition_root_compatibility.json").read_text())
    schema = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
    assert len(pins["definitions"]) == 403
    synthesis = json.loads((FIXTURES / "nutrition_synthesis_compatibility.json").read_text())
    resolution = json.loads((FIXTURES / "nutrition_resolution_compatibility.json").read_text())
    basis = json.loads((FIXTURES / "basis_compatibility.json").read_text())
    policy_v2 = json.loads((FIXTURES / "policy_v2_export_names.json").read_text())
    assert len(schema) == 528  # 515 retained +13 additive policy v2 definitions.
    assert len(pins["new_definitions"]) == 44
    assert set(schema) - set(pins["definitions"]) == set(pins["new_definitions"]) | set(
        synthesis["new_definitions"]
    ) | set(resolution["new_definitions"]) | set(basis["new_definitions"]) | set(policy_v2)
    for name, digest in pins["definitions"].items():
        assert (
            hashlib.sha256(json.dumps(schema[name], sort_keys=True).encode()).hexdigest() == digest
        ), name


def test_nrc78_all3638_baseline_test_identities_retained():
    ids = json.loads((FIXTURES / "nutrition_root_baseline_tests.json").read_text())
    assert len(ids) == 3638
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-o", "addopts="],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
    )
    actual = [
        s.strip()
        for s in result.stdout.splitlines()
        if s.startswith(("apps/", "benchmark/")) and "::" in s
    ]

    def normalized(value):
        return re.sub(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", "<uuid>", value)

    assert not Counter(map(normalized, ids)) - Counter(map(normalized, actual))
    acceptance = json.loads((FIXTURES / "nutrition_root_acceptance.json").read_text())["cases"]
    assert set(acceptance) == {f"NRC{i:02}" for i in range(1, 81)}
    for case, proof in acceptance.items():
        assert proof["tests"] and all("test_" + case.lower() + "_" in t for t in proof["tests"])
        assert not set(map(normalized, proof["tests"])) - set(map(normalized, actual)), case
    assert sum(len(p["tests"]) for p in acceptance.values() if p["layer"] == "PG") == 66


def test_nrc79_test_fixtures_do_not_approve_production_content():
    source = json.loads((FIXTURES / "nutrition_root_retained_TEST_ONLY.json").read_text())
    pending = [source]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if "environment" in value:
                assert value["environment"] == "TEST_ONLY"
            if "evidence_id" in value:
                assert "TEST_ONLY" in value["purpose"] and "TEST_ONLY" in value["body"]
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    assert source["request"]["environment"] == "TEST_ONLY"


def test_nrc80_no_downstream_or_heuristic_pool_implementation():
    for context in ("planning", "execution", "learning", "preferences", "policy"):
        prefix = f"apps/backend/app/modules/{context}/"
        pins = json.loads((FIXTURES / "nutrition_root_compatibility.json").read_text())
        for name, digest in pins["frozen_files"].items():
            if name.startswith(prefix):
                assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
