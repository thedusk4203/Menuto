"""Static dependency checks for Menuto's modular monolith, no third-party dependency."""

import argparse
import ast
import importlib.util
from pathlib import Path

ALLOWED = {
    "identity": set(),
    "households": {"identity"},
    "catalog": set(),
    "nutrition": {"households", "catalog"},
    "recipes": {"catalog"},
    "retail": {"catalog"},
    "inventory": {"households", "catalog", "retail"},
    "preferences": {"households", "catalog", "recipes"},
    "policy": {"households", "nutrition", "preferences"},
    "cooking": {"households", "catalog", "recipes"},
    "planning": {
        "households",
        "nutrition",
        "catalog",
        "recipes",
        "retail",
        "inventory",
        "policy",
        "cooking",
        "shopping",
        "preferences",
        "validation",
        "learning",
    },
    "shopping": {"households", "retail", "inventory", "planning"},
    "execution": {
        "catalog",
        "nutrition",
        "recipes",
        "households",
        "planning",
        "cooking",
        "inventory",
        "shopping",
        "validation",
        "learning",
    },
    "validation": {
        "households",
        "nutrition",
        "catalog",
        "recipes",
        "retail",
        "inventory",
        "policy",
        "planning",
        "cooking",
        "shopping",
        "execution",
        "preferences",
    },
    "learning": {
        "households",
        "catalog",
        "recipes",
        "retail",
        "preferences",
        "planning",
        "cooking",
        "shopping",
        "execution",
    },
    "assistant": {
        "households",
        "catalog",
        "recipes",
        "retail",
        "policy",
        "planning",
        "preferences",
    },
}
PUBLIC_SURFACES = {"contracts", "public"}
# V1.3 ADR-010/011: immutable facts may cross these seams; runtime facades may not.
CONTRACT_ONLY_CONTEXTS = {"validation", "learning"}


def check_source(source: str, module: str, *, is_package: bool = False) -> list[str]:
    tree = ast.parse(source)
    parts = module.split(".")
    context = parts[2] if len(parts) > 2 and parts[:2] == ["app", "modules"] else None
    contract = len(parts) > 3 and parts[3] == "contracts"
    shared = module == "app.shared" or module.startswith("app.shared.")
    neutral = module == "app.domain" or module.startswith("app.domain.")
    errors = []

    def audit(target, line):
        shortlist_imports = {
            "app.modules.planning.shortlist": {
                "json", "dataclasses", "hashlib", "app.modules.planning.contracts",
            },
            "app.modules.planning.shortlist_capture": {
                "app.modules.planning.contracts", "app.modules.planning.grounding_capture",
                "app.modules.planning.shortlist",
            },
        }
        if module in shortlist_imports and not any(
            target == allowed or target.startswith(allowed + ".")
            for allowed in shortlist_imports[module]
        ):
            errors.append(f"{line}: SHORTLIST_NARROW_BOUNDARY: {target}")
        if module in {"app.modules.planning.grounding", "app.modules.planning.grounding_capture"}:
            if target.startswith(
                (
                    "ortools",
                    "benchmark",
                    "app.modules.learning",
                    "app.modules.assistant",
                    "app.modules.planning.optimizer",
                    "app.modules.planning.ranking",
                    "app.modules.planning.shortlist",
                    "app.modules.planning.objectives",
                    "app.modules.planning.utility",
                )
            ):
                errors.append(f"{line}: GROUNDING_NOT_OPTIMIZATION: {target}")
        if (context == "validation" or contract) and (
            target == "ortools" or target.startswith("ortools.")
        ):
            errors.append(f"{line}: VALIDATION_OR_CONTRACT_IMPORTS_SOLVER: {target}")
        if context == "validation":
            if target.endswith((".resolve_culinary_binding", ".bind_culinary_draft")):
                errors.append(f"{line}: VALIDATION_PRODUCER_ENFORCEMENT: {target}")
            if target.split(".")[0] in {
                "ortools",
                "sqlalchemy",
                "psycopg",
                "sqlite3",
                "benchmark",
                "socket",
                "subprocess",
                "httpx",
                "requests",
                "urllib",
                "os",
                "pathlib",
            } or (target.startswith(("app.persistence", "app.shared.db"))):
                errors.append(f"{line}: VALIDATION_INDEPENDENCE: {target}")
            if target.startswith("app.modules.") and target.split(".")[2] != "validation":
                tail = target.split(".")[3:]
                if not tail or tail[0] != "contracts":
                    errors.append(f"{line}: VALIDATION_CONTRACTS_ONLY: {target}")
        if neutral and target.startswith(("app.modules", "app.persistence", "app.shared.db")):
            errors.append(f"{line}: NEUTRAL_DOMAIN_IMPORTS_IMPLEMENTATION: {target}")
        if target == "benchmark" or target.startswith("benchmark."):
            errors.append(f"{line}: BACKEND_IMPORTS_SYNTHETIC_BENCHMARK: {target}")
        if context and (target == "importlib" or target.startswith("importlib.")):
            errors.append(f"{line}: DYNAMIC_IMPORT_REQUIRES_REVIEW: {target}")
        if context and target in {"app", "app.modules"}:
            errors.append(f"{line}: INDIRECT_APP_NAMESPACE_IMPORT: {target}")
        if not target.startswith("app.modules."):
            if context and target in {"app.main"}:
                errors.append(f"{line}: DOMAIN_IMPORTS_ENTRYPOINT: {target}")
            return
        destination = target.split(".")[2]
        if shared:
            errors.append(f"{line}: SHARED_IMPORTS_DOMAIN: {target}")
            return
        if context is None:
            return
        if context not in ALLOWED or destination not in ALLOWED:
            errors.append(f"{line}: UNREGISTERED_CONTEXT: {target}")
            return
        tail = target.split(".")[3:]
        if (
            context == "planning"
            and destination == "shopping"
            and (not tail or tail[0] != "contracts")
        ):
            errors.append(f"{line}: PLAN_SHOPPING_CONTRACTS_ONLY: {target}")
            return
        if contract and context in {"shopping", "cooking"} and destination == "planning":
            errors.append(f"{line}: PLAN_CONTRACT_CYCLE: {target}")
            return
        if contract and (not tail or tail[0] != "contracts"):
            errors.append(f"{line}: CONTRACT_IMPORTS_IMPLEMENTATION: {target}")
            return
        if destination == context:
            return
        if destination not in ALLOWED[context]:
            errors.append(f"{line}: FORBIDDEN_DIRECTION: {context} -> {destination}")
            return
        if context in CONTRACT_ONLY_CONTEXTS and (not tail or tail[0] != "contracts"):
            errors.append(f"{line}: FACT_READER_IMPORTS_IMPLEMENTATION: {target}")
            return
        if not tail or tail[0] not in PUBLIC_SURFACES:
            errors.append(f"{line}: CROSS_CONTEXT_INTERNAL_IMPORT: {target}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                audit(item.name, node.lineno)
        elif isinstance(node, ast.ImportFrom):
            target = node.module or ""
            if node.level:
                package = module if is_package else module.rpartition(".")[0]
                try:
                    target = importlib.util.resolve_name("." * node.level + target, package)
                except ImportError:
                    errors.append(f"{node.lineno}: INVALID_RELATIVE_IMPORT")
                    continue
            for item in node.names:
                audit(target + "." + item.name if item.name != "*" else target, node.lineno)
                if item.name == "*" and context:
                    errors.append(f"{node.lineno}: WILDCARD_IMPORT_REQUIRES_REVIEW")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if context == "validation" and node.func.id == "open":
                errors.append(f"{node.lineno}: VALIDATION_INDEPENDENCE: file IO")
            if context and node.func.id in {"__import__", "eval", "exec"}:
                errors.append(f"{node.lineno}: DYNAMIC_IMPORT_REQUIRES_REVIEW")
    return sorted(set(errors))


def check_tree(app_root: Path) -> list[str]:
    issues = []
    module_root = app_root / "modules"
    actual = {p.name for p in module_root.iterdir() if p.is_dir() and p.name != "__pycache__"}
    for name in sorted(actual - ALLOWED.keys()):
        issues.append(f"app.modules.{name}: UNREGISTERED_CONTEXT")
    for path in sorted(app_root.rglob("*.py")):
        relative = path.relative_to(app_root.parent).with_suffix("")
        is_package = relative.name == "__init__"
        module = ".".join(relative.parts[:-1] if is_package else relative.parts)
        try:
            errors = check_source(
                path.read_text(encoding="utf-8-sig"), module, is_package=is_package
            )
        except SyntaxError as error:
            errors = [f"SYNTAX_ERROR: {error}"]
        issues.extend(f"{path.relative_to(app_root)}:{error}" for error in errors)
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--app-root", type=Path, default=Path(__file__).resolve().parents[1] / "apps/backend/app"
    )
    args = parser.parse_args()
    failures = check_tree(args.app_root)
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    print(
        f"Import boundaries passed: {len(ALLOWED)} registered contexts, public/contract surfaces, "
        "independent validation/learning, no backend benchmark dependency."
    )


if __name__ == "__main__":
    main()
