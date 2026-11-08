"""Mechanical baseline retention, additive exports and pure module boundaries."""

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"


def test_hc78_hc79_all349_definitions_and_123_frozen_runtime_files_retained():
    pins = json.loads((FIXTURES / "hierarchical_affinity_compatibility.json").read_text())
    assert pins["base"] == "b591464e3ca495909851217141f96a55faaa35cc"
    schema = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
    assert len(pins["definitions"]) == 349 and len(schema) == 537  # 528 retained +9 intent.
    assert len(pins["frozen_files"]) == 123
    for name, digest in pins["definitions"].items():
        assert (
            hashlib.sha256(json.dumps(schema[name], sort_keys=True).encode()).hexdigest() == digest
        ), name
    additive = json.loads(
        (FIXTURES / "candidate_feature_projection_compatibility.json").read_text()
    )["append_only_files"]
    nutrition = json.loads((FIXTURES / "nutrition_root_compatibility.json").read_text())[
        "append_only_files"
    ]
    for name, digest in pins["frozen_files"].items():
        data = (ROOT / name).read_bytes()
        if name in nutrition:
            assert nutrition[name]["sha256"] == digest
            assert data[nutrition[name]["prefix_bytes"] :] == nutrition[name]["suffix"].encode()
            data = data[: nutrition[name]["prefix_bytes"]]
        if name in additive:
            # Only these two approved additive surfaces may grow; every old byte stays pinned.
            assert additive[name]["sha256"] == digest
            data = data[: additive[name]["prefix_bytes"]]
        assert hashlib.sha256(data).hexdigest() == digest, name
    public = (ROOT / "apps/backend/app/modules/preferences/public.py").read_bytes()
    assert (
        hashlib.sha256(public[: pins["public_prefix_bytes"]]).hexdigest()
        == pins["public_prefix_sha256"]
    )
    assert sorted(
        p.name[:4]
        for p in (ROOT / "apps/backend/migrations/versions").glob("*.py")
        if p.name[:4].isdigit()
    ) == [f"{n:04}" for n in range(1, 18)]


def test_hc79_retained_all2807_test_identities():
    baseline = json.loads((FIXTURES / "hierarchical_affinity_baseline_tests.json").read_text())
    assert len(baseline) == 2807
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-o", "addopts="],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
    )
    current = [
        s.strip()
        for s in result.stdout.splitlines()
        if s.startswith(("apps/", "benchmark/")) and "::" in s
    ]

    def normalize(node):
        return re.sub(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            "<uuid>",
            node,
        )

    assert not Counter(map(normalize, baseline)) - Counter(map(normalize, current))


def test_hc78_hc80_pure_modules_cannot_import_persistence_or_downstream():
    directory = ROOT / "apps/backend/app/modules/preferences"
    allowed = {
        "fractions",
        "math",
        "typing",
        "uuid",
        "pydantic",
        "app.domain",
        "app.modules.preferences",
        "app.modules.catalog.contracts",
        "app.modules.recipes.contracts",
    }
    for filename in ("hierarchical_affinity.py", "hierarchical_affinity_contracts.py"):
        tree = ast.parse((directory / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = (
                [n.name for n in node.names]
                if isinstance(node, ast.Import)
                else ([node.module] if isinstance(node, ast.ImportFrom) else [])
            )
            for module in modules:
                assert any(module == p or module.startswith(p + ".") for p in allowed), module
