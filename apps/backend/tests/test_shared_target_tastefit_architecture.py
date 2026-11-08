"""SMTF109–120: additive-only surface, exact old contracts and baseline retention."""

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
from app.modules.planning.shared_target_tastefit_contracts import SharedMemberTargetTasteFitPolicy

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"
CHECK = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]


def test_smtf120_all384_definitions_unchanged_exact_new_exports():
    pins = json.loads((FIXTURES / "shared_target_tastefit_compatibility.json").read_text())
    defs = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
    # NRC adds a separate source surface; retain the exact original SMTF export delta.
    nutrition = json.loads((FIXTURES / "nutrition_root_compatibility.json").read_text())
    synthesis = json.loads((FIXTURES / "nutrition_synthesis_compatibility.json").read_text())
    resolution = json.loads((FIXTURES / "nutrition_resolution_compatibility.json").read_text())
    basis = json.loads((FIXTURES / "basis_compatibility.json").read_text())
    policy_v2 = json.loads((FIXTURES / "policy_v2_export_names.json").read_text())
    explicit_intent = json.loads(
        (FIXTURES / "explicit_plan_intent_export_names.json").read_text()
    )
    later = (set(nutrition["new_definitions"]) | set(synthesis["new_definitions"])
             | set(resolution["new_definitions"]) | set(basis["new_definitions"]) | set(policy_v2)
             | set(explicit_intent))
    defs = {name: body for name, body in defs.items() if name not in later}
    assert len(pins["definitions"]) == 384
    assert len(defs) == 384 + len(pins["new_definitions"]) == 403
    assert sorted(set(defs) - set(pins["definitions"])) == pins["new_definitions"]
    for name, digest in pins["definitions"].items():
        assert hashlib.sha256(json.dumps(defs[name], sort_keys=True).encode()).hexdigest() == digest


def test_smtf120_all_frozen_runtime_and_migrations_byte_exact():
    pins = json.loads((FIXTURES / "shared_target_tastefit_compatibility.json").read_text())
    for path, digest in pins["frozen_files"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    assert sorted(
        p.name[:4]
        for p in (ROOT / "apps/backend/migrations/versions").glob("*.py")
        if p.name[:4].isdigit()
    ) == [f"{i:04}" for i in range(1, 18)]


def test_smtf120_all3396_baseline_test_identities_retained():
    ids = json.loads((FIXTURES / "shared_target_tastefit_baseline_tests.json").read_text())
    assert len(ids) == 3396
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

    def normalize(s):
        return re.sub(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", "<uuid>", s)

    assert not Counter(map(normalize, ids)) - Counter(map(normalize, actual))
    index = json.loads((FIXTURES / "shared_target_tastefit_acceptance.json").read_text())["cases"]
    assert set(index) == {f"SMTF{i:02}" for i in range(1, 121)}
    current = set(map(normalize, actual))
    for i in range(1, 121):
        case = index[f"SMTF{i:02}"]
        assert case["tests"] and set(map(normalize, case["tests"])) <= current
        assert (case["required_layer"] == "PG") == (i <= 36)
        if i <= 36:
            assert all("test_postgres_shared_target_tastefit.py::" in t for t in case["tests"])


@pytest.mark.parametrize(
    "module",
    [
        "shared_target_tastefit",
        "shared_target_tastefit_contracts",
        "shared_target_tastefit_capture",
    ],
)
@pytest.mark.parametrize(
    "target",
    [
        "profile_derivation",
        "tastefit_public",
        "tastefit_contracts",
        "hierarchy_sources",
        "reference_priors",
    ],
)
def test_smtf120_no_new_preferences_companion_or_private_access(module, target):
    errors = CHECK(f"import app.modules.preferences.{target}", f"app.modules.planning.{module}")
    assert any("SHARED_TARGET_TASTEFIT_BOUNDARY" in e for e in errors)


@pytest.mark.parametrize(
    "target",
    [
        "sqlalchemy",
        "psycopg",
        "socket",
        "os",
        "pathlib",
        "time",
        "datetime",
        "httpx",
        "app.modules.learning.contracts",
        "app.modules.planning.utility",
        "app.modules.planning.shared_target_tastefit_capture",
    ],
)
def test_smtf109_smtf110_pure_core_no_io_learning_or_policy_environment(target):
    assert any(
        "SHARED_TARGET_TASTEFIT_BOUNDARY" in e
        for e in CHECK(f"import {target}", "app.modules.planning.shared_target_tastefit")
    )


@pytest.mark.parametrize(
    "target",
    [
        "sqlalchemy",
        "datetime",
        "app.modules.planning.tastefit_public",
        "app.modules.planning.shared_target_tastefit_public",
        "app.modules.households.public",
    ],
)
def test_smtf120_immutable_transport_no_runtime_facades(target):
    assert any(
        "SHARED_TARGET_TASTEFIT_BOUNDARY" in e
        for e in CHECK(f"import {target}", "app.modules.planning.shared_target_tastefit_contracts")
    )


@pytest.mark.parametrize("context", ["validation", "learning"])
def test_smtf119_no_capture_access_from_learning_validation(context):
    assert CHECK(
        "import app.modules.planning.shared_target_tastefit_capture",
        f"app.modules.{context}.public",
    )


def test_smtf119_small_three_operation_public_surface_and_lazy_capture():
    path = ROOT / "apps/backend/app/modules/planning/shared_target_tastefit_public.py"
    tree = ast.parse(path.read_text())
    assert {n.name for n in tree.body if isinstance(n, ast.FunctionDef)} == {
        "capture_shared_member_target_tastefit_sources",
        "derive_shared_member_target_tastefit",
        "validate_shared_member_target_tastefit",
    }
    assert not CHECK(path.read_text(), "app.modules.planning.shared_target_tastefit_public")
    assert CHECK(
        "from app.modules.planning.shared_target_tastefit_capture "
        "import capture_shared_member_target_tastefit_sources",
        "app.modules.planning.shared_target_tastefit_public",
    )


def test_smtf110_policy_fields_required_no_numeric_defaults():
    assert all(f.is_required() for f in SharedMemberTargetTasteFitPolicy.model_fields.values())
