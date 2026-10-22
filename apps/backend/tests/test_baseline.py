"""Document integrity regressions, not claims of domain-invariant enforcement."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKER = runpy.run_path(str(ROOT / "tools/check_architecture_baseline.py"))


def test_actual_canonical_baseline_is_consistent():
    assert CHECKER["check_baseline"](ROOT) == []


def test_renumbering_check_catches_missing_and_duplicate_ids():
    errors = CHECKER["check_numbered_set"](
        "INV-001\nINV-001\nINV-031", r"^(INV-\d{3})$", {"INV-001", "INV-002"}, "test"
    )
    assert len(errors) == 2
    assert "INV-002" in errors[0] and "INV-031" in errors[0]
    assert "duplicate" in errors[1]


def test_link_check_catches_stale_local_spec_link(tmp_path):
    path = tmp_path / "README.md"
    path.write_text("[old](docs/MENUTO_DEVELOPMENT_SPEC_V1_2.md)", encoding="utf-8")
    assert "missing linked file" in CHECKER["check_links"](tmp_path, [path])[0]
