"""Check canonical V1.3 document integrity; does not certify business invariants."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_INVARIANTS = {f"INV-{n:03d}" for n in range(1, 31)}
EXPECTED_TASKS = {f"MTR-{n:03d}" for n in range(1, 51)}


def check_numbered_set(text: str, pattern: str, expected: set[str], label: str) -> list[str]:
    found = re.findall(pattern, text, flags=re.MULTILINE)
    errors = []
    if set(found) != expected:
        errors.append(
            f"{label}: missing={sorted(expected - set(found))}; "
            f"unexpected={sorted(set(found) - expected)}"
        )
    if len(found) != len(set(found)):
        errors.append(f"{label}: duplicate identifiers")
    return errors


def check_links(root: Path, paths: list[Path]) -> list[str]:
    errors = []
    for path in paths:
        for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if ":" in target or target.startswith("#"):
                continue
            target = target.split("#", 1)[0]
            if target and not (path.parent / target).exists():
                errors.append(f"{path.relative_to(root)}: missing linked file {target}")
    return errors


def check_baseline(root: Path = ROOT) -> list[str]:
    errors = []
    spec_path = root / "docs/MENUTO_DEVELOPMENT_SPEC_V1_3.md"
    invariants_path = root / "docs/ARCHITECTURE_INVARIANTS.md"
    coverage_path = root / "docs/product/INVARIANT_COVERAGE.md"
    backlog_path = root / "docs/product/BACKLOG.md"
    required = [spec_path, invariants_path, coverage_path, backlog_path]
    if any(not path.exists() for path in required):
        return ["Missing canonical V1.3 baseline document"]
    spec = spec_path.read_text(encoding="utf-8")
    invariants = invariants_path.read_text(encoding="utf-8")
    coverage = coverage_path.read_text(encoding="utf-8")
    backlog = backlog_path.read_text(encoding="utf-8")
    for text, pattern, expected, label in [
        (spec, r"^\*\*(INV-\d{3}) —", EXPECTED_INVARIANTS, "spec invariants"),
        (invariants, r"^- \*\*(INV-\d{3}) —", EXPECTED_INVARIANTS, "invariant mirror"),
        (coverage, r"^\| (INV-\d{3}) \|", EXPECTED_INVARIANTS, "invariant coverage"),
        (spec, r"^\| (MTR-\d{3}) \|", EXPECTED_TASKS, "spec tasks"),
        (backlog, r"^\| \[(MTR-\d{3})\]", EXPECTED_TASKS, "linked backlog"),
    ]:
        errors.extend(check_numbered_set(text, pattern, expected, label))
    spec_titles = dict(re.findall(r"^\*\*(INV-\d{3}) — (.*?)\.\*\*", spec, re.MULTILINE))
    mirror_titles = dict(re.findall(r"^- \*\*(INV-\d{3}) — (.*?)\.\*\*", invariants, re.MULTILINE))
    if spec_titles != mirror_titles or len(spec_titles) != 30:
        errors.append("Spec/invariant mirror titles disagree")
    adr_paths = sorted((root / "docs/adr").glob("ADR-*.md"))
    expected_adrs = {f"ADR-{n:03d}" for n in range(1, 12)}
    if {p.name[:7] for p in adr_paths} != expected_adrs or len(adr_paths) != 11:
        errors.append("Expected exactly ADR-001..011")
    for path in adr_paths:
        text = path.read_text(encoding="utf-8")
        if not re.search(r"Status.*?accepted", text, re.IGNORECASE):
            errors.append(f"{path.name}: accepted status missing")
        if set(re.findall(r"INV-\d{3}", text)) - EXPECTED_INVARIANTS:
            errors.append(f"{path.name}: unknown invariant reference")
    issue_links = re.findall(
        r"^\| \[MTR-\d{3}\]\(https://github.com/thedusk4203/Menuto/issues/(\d+)\)",
        backlog,
        re.MULTILINE,
    )
    if len(issue_links) != 50 or len(set(issue_links)) != 50:
        errors.append("Backlog must have 50 distinct linked GitHub issues")
    if (root / "docs/MENUTO_DEVELOPMENT_SPEC_V1_2.md").exists():
        errors.append("Superseded V1.2 spec must remain in history, not active docs")
    active_docs = [
        root / "README.md",
        root / "CONTRIBUTING.md",
        *root.glob("docs/product/*.md"),
        root / "benchmark/README.md",
        root / "benchmark/V1_3_SCENARIO_MATRIX.md",
        *adr_paths,
    ]
    errors.extend(check_links(root, active_docs))
    return errors


def main():
    errors = check_baseline()
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print(
        "V1.3 baseline passed: 30 invariants, 11 ADRs, 50 linked tasks. "
        "This checks documentation integrity, not business correctness."
    )


if __name__ == "__main__":
    main()
