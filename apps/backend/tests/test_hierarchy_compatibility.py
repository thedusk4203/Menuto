"""Retain canonical baseline semantics and test identities across the additive source slice."""

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


def test_s02_all318_definitions_and_frozen_dependencies_retained():
    pins = json.loads((FIXTURES / "hierarchy_source_compatibility.json").read_text())
    assert pins["base"] == "4ad3f682554b7feee9f333eca1f1f5c258852f5e"
    schema = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
    assert len(pins["definitions"]) == 318
    assert len(schema) == 403  # 384 retained + 19 additive shared-target TasteFit definitions.
    for name, expected in pins["definitions"].items():
        assert (
            hashlib.sha256(json.dumps(schema[name], sort_keys=True).encode()).hexdigest()
            == expected
        ), name
    for name, expected in pins["frozen_files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name


def test_s02_retained_2597_baseline_node_identities():
    baseline = json.loads((FIXTURES / "hierarchy_source_baseline_tests.json").read_text())
    assert len(baseline) == 2597
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
        line.strip()
        for line in result.stdout.splitlines()
        if line.startswith(("apps/", "benchmark/")) and "::" in line
    ]

    def normalize(node):
        return re.sub(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            "<uuid>",
            node,
        )

    expected = Counter(map(normalize, baseline))
    actual = Counter(map(normalize, current))
    assert not expected - actual, expected - actual
