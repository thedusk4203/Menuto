"""Additive exports, exact companion allowlist, frozen files and baseline retention."""

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

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"
CHECK = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]


def test_tf130_frozen_owner_runtime_and_migrations_byte_exact():
    pins = json.loads((FIXTURES / "tastefit_compatibility.json").read_text())
    nutrition = json.loads((FIXTURES / "nutrition_root_compatibility.json").read_text())[
        "append_only_files"
    ]
    for path, digest in pins["frozen_files"].items():
        data = (ROOT / path).read_bytes()
        if path in nutrition:
            assert nutrition[path]["sha256"] == digest
            assert data[nutrition[path]["prefix_bytes"] :] == nutrition[path]["suffix"].encode()
            data = data[: nutrition[path]["prefix_bytes"]]
        assert hashlib.sha256(data).hexdigest() == digest, path
    assert sorted(
        p.name[:4]
        for p in (ROOT / "apps/backend/migrations/versions").glob("*.py")
        if p.name[:4].isdigit()
    ) == [f"{n:04}" for n in range(1, 17)]


def test_tf131_all3104_baseline_test_identities_retained():
    baseline = json.loads((FIXTURES / "tastefit_baseline_tests.json").read_text())
    assert len(baseline) == 3104
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-o", "addopts="],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
    )
    current = [
        s.strip()
        for s in result.stdout.splitlines()
        if s.startswith(("apps/", "benchmark/")) and "::" in s
    ]

    def normalize(s):
        return re.sub(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", "<uuid>", s)

    assert not Counter(map(normalize, baseline)) - Counter(map(normalize, current))


def test_tf132_all362_old_definitions_unchanged_exact_additive_export_set():
    pins = json.loads((FIXTURES / "tastefit_compatibility.json").read_text())
    defs = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
    assert len(pins["definitions"]) == 362
    shared = json.loads((FIXTURES / "shared_target_tastefit_compatibility.json").read_text())
    nutrition = json.loads((FIXTURES / "nutrition_root_compatibility.json").read_text())
    assert len(defs) == 384 + len(shared["new_definitions"]) + len(nutrition["new_definitions"])
    assert sorted(set(defs) - set(pins["definitions"])) == sorted(
        pins["new_definitions"] + shared["new_definitions"] + nutrition["new_definitions"]
    )
    for name, digest in pins["definitions"].items():
        assert (
            hashlib.sha256(json.dumps(defs[name], sort_keys=True).encode()).hexdigest() == digest
        ), name


@pytest.mark.parametrize("module", ["tastefit", "tastefit_contracts", "tastefit_capture"])
@pytest.mark.parametrize(
    "target",
    [
        "reference_priors",
        "hierarchy_sources",
        "profile_capture",
        "prior_affinity",
        "hierarchical_affinity",
    ],
)
def test_tf130_planning_cannot_import_private_preferences_even_from_new_modules(module, target):
    errors = CHECK(f"import app.modules.preferences.{target}", f"app.modules.planning.{module}")
    assert any("CROSS_CONTEXT_INTERNAL_IMPORT" in e for e in errors)


@pytest.mark.parametrize("module", ["grounding", "optimizer", "utility", "ranking", "public"])
@pytest.mark.parametrize("target", ["tastefit_contracts", "tastefit_public"])
def test_tf130_companion_allowlist_does_not_extend_other_planning_modules(module, target):
    errors = CHECK(f"import app.modules.preferences.{target}", f"app.modules.planning.{module}")
    assert any("CROSS_CONTEXT_INTERNAL_IMPORT" in e for e in errors)


@pytest.mark.parametrize(
    "target",
    [
        "sqlalchemy",
        "psycopg",
        "socket",
        "pathlib",
        "os",
        "time",
        "datetime",
        "httpx",
        "requests",
        "ortools",
        "app.persistence.database",
        "app.modules.learning.contracts",
        "app.modules.planning.ranking",
        "app.modules.planning.feature_preview",
        "app.modules.planning.utility",
    ],
)
def test_tf114_tf117_tf121_tf122_pure_core_rejects_io_learning_history_utility(target):
    assert any(
        "TASTEFIT_PURE_CORE" in e
        for e in CHECK(f"import {target}", "app.modules.planning.tastefit")
    )


@pytest.mark.parametrize("context", ["validation", "learning"])
def test_tf130_validation_learning_contract_only_rules_unchanged(context):
    assert CHECK("import app.modules.preferences.tastefit_public", f"app.modules.{context}.public")


def test_tf130_exact_approved_companion_imports_work():
    for module, targets in {
        "tastefit": ("tastefit_contracts", "tastefit_public"),
        "tastefit_contracts": ("tastefit_contracts",),
        "tastefit_capture": ("tastefit_contracts", "tastefit_public"),
    }.items():
        for target in targets:
            assert not CHECK(
                f"from app.modules.preferences.{target} import X", f"app.modules.planning.{module}"
            )


@pytest.mark.parametrize(
    "target",
    [
        "sqlalchemy",
        "socket",
        "os",
        "datetime",
        "app.modules.preferences.tastefit_sources",
        "app.modules.preferences.public",
    ],
)
def test_tf114_member_replay_cannot_import_io_or_frozen_io_facade(target):
    assert any(
        "TASTEFIT_MEMBER_PURE_REPLAY" in e
        for e in CHECK(f"import {target}", "app.modules.preferences.tastefit_public")
    )


@pytest.mark.parametrize("module", ["planning", "preferences"])
@pytest.mark.parametrize("target", ["app.modules.preferences.public",
    "app.modules.preferences.tastefit_sources", "app.modules.planning.tastefit_public",
    "app.modules.catalog.models", "app.modules.recipes.public"])
def test_tf130_transport_accepts_only_immutable_owner_shapes(module,target):
    assert any("TASTEFIT_IMMUTABLE_TRANSPORT" in e for e in CHECK(
        f"import {target}",f"app.modules.{module}.tastefit_contracts"))
