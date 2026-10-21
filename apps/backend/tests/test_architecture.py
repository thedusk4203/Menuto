import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CHECKER = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))
check_source = CHECKER["check_source"]


def test_actual_backend_respects_registered_boundaries():
    assert CHECKER["check_tree"](ROOT / "apps/backend/app") == []


@pytest.mark.parametrize(
    ("module", "source", "expected"),
    [
        (
            "app.modules.recipes.domain",
            "from app.modules.planning.contracts import Plan",
            "FORBIDDEN_DIRECTION",
        ),
        (
            "app.modules.retail.domain",
            "import app.modules.shopping.contracts",
            "FORBIDDEN_DIRECTION",
        ),
        (
            "app.modules.assistant.service",
            "from app.modules.planning.repositories import PlanRepository",
            "CROSS_CONTEXT_INTERNAL_IMPORT",
        ),
        (
            "app.modules.planning.domain",
            "from app.modules.recipes.models import Recipe",
            "CROSS_CONTEXT_INTERNAL_IMPORT",
        ),
        (
            "app.modules.planning.domain",
            "from app.modules import recipes",
            "CROSS_CONTEXT_INTERNAL_IMPORT",
        ),
        (
            "app.modules.recipes.domain",
            "from ..planning.contracts import Plan",
            "FORBIDDEN_DIRECTION",
        ),
        (
            "app.shared.types",
            "from app.modules.catalog.contracts import Ingredient",
            "SHARED_IMPORTS_DOMAIN",
        ),
        (
            "app.main",
            "from benchmark.cpsat import SyntheticCpSatAdapter",
            "BACKEND_IMPORTS_SYNTHETIC_BENCHMARK",
        ),
        ("app.modules.planning.domain", "import app", "INDIRECT_APP_NAMESPACE_IMPORT"),
        (
            "app.modules.planning.domain",
            "import importlib as loader",
            "DYNAMIC_IMPORT_REQUIRES_REVIEW",
        ),
        (
            "app.modules.planning.domain",
            "__import__('app.modules.recipes.models')",
            "DYNAMIC_IMPORT_REQUIRES_REVIEW",
        ),
        (
            "app.modules.planning.domain",
            "from app.modules.recipes.contracts import *",
            "WILDCARD_IMPORT_REQUIRES_REVIEW",
        ),
    ],
)
def test_checker_catches_real_dependency_violations(module, source, expected):
    errors = check_source(source, module)
    assert any(expected in error for error in errors), errors


@pytest.mark.parametrize(
    ("module", "source"),
    [
        ("app.modules.planning.domain", "from app.modules.recipes.contracts import Recipe"),
        ("app.modules.planning.domain", "from ..inventory.public import InventoryReader"),
        ("app.modules.recipes.domain", "from .models import Recipe"),
        ("app.modules.assistant.service", "from app.modules.planning.public import PlanFacade"),
        ("app.modules.planning.domain", "from app.modules.recipes import contracts"),
        ("app.modules.recipes.domain", "from app.shared.units import Quantity"),
    ],
)
def test_checker_allows_public_interfaces_and_same_context_internals(module, source):
    assert check_source(source, module) == []


def test_relative_import_in_package_is_resolved():
    errors = check_source(
        "from ..planning.contracts import Plan", "app.modules.recipes", is_package=True
    )
    assert any("FORBIDDEN_DIRECTION" in error for error in errors)


def test_unknown_new_context_cannot_silently_bypass_policy(tmp_path):
    (tmp_path / "modules/new_domain").mkdir(parents=True)
    (tmp_path / "modules/new_domain/__init__.py").write_text("", encoding="utf-8")
    assert any("UNREGISTERED_CONTEXT" in issue for issue in CHECKER["check_tree"](tmp_path))
