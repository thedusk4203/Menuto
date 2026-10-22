import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CHECKER = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))
check_source = CHECKER["check_source"]


def test_actual_backend_respects_registered_boundaries():
    assert CHECKER["check_tree"](ROOT / "apps/backend/app") == []


@pytest.mark.parametrize(
    "target",
    [
        "retail.contracts",
        "retail.models",
        "inventory.contracts",
        "inventory.models",
        "planning.contracts",
        "planning.optimizer",
        "execution.contracts",
        "validation.contracts",
    ],
)
def test_recipe_core_cannot_reach_runtime_grounding_domains(target):
    errors = check_source(f"import app.modules.{target}", "app.modules.recipes.contracts")
    assert any(
        "FORBIDDEN_DIRECTION" in error or "CONTRACT_IMPORTS_IMPLEMENTATION" in error
        for error in errors
    )


def test_retail_cannot_depend_on_recipes():
    assert check_source("import app.modules.recipes.contracts", "app.modules.retail.contracts")


def test_recipe_may_use_catalog_contracts_and_neutral_primitives():
    assert not check_source(
        "from app.modules.catalog.contracts import IngredientCreate\n"
        "from app.domain.units import Quantity, Provenance",
        "app.modules.recipes.contracts",
    )


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


@pytest.mark.parametrize(
    ("module", "source", "expected"),
    [
        (
            "app.modules.validation.service",
            "from app.modules.planning.optimizer import solve",
            "FACT_READER_IMPORTS_IMPLEMENTATION",
        ),
        (
            "app.modules.validation.service",
            "from app.modules.planning.public import PlannerFacade",
            "FACT_READER_IMPORTS_IMPLEMENTATION",
        ),
        (
            "app.modules.validation.replay",
            "from ..planning.candidates import CandidateGenerator",
            "FACT_READER_IMPORTS_IMPLEMENTATION",
        ),
        (
            "app.modules.validation.service",
            "from ortools.sat.python import cp_model",
            "VALIDATION_OR_CONTRACT_IMPORTS_SOLVER",
        ),
        (
            "app.modules.planning.contracts.snapshot",
            "from ..optimizer import solve",
            "CONTRACT_IMPORTS_IMPLEMENTATION",
        ),
        (
            "app.modules.policy.contracts",
            "from .public import resolve_policy",
            "CONTRACT_IMPORTS_IMPLEMENTATION",
        ),
        (
            "app.modules.planning.contracts",
            "from ortools.sat.python import cp_model",
            "VALIDATION_OR_CONTRACT_IMPORTS_SOLVER",
        ),
        (
            "app.modules.learning.router",
            "from app.modules.execution.public import mutate",
            "FACT_READER_IMPORTS_IMPLEMENTATION",
        ),
        (
            "app.modules.learning.router",
            "from app.modules.planning.objectives import score",
            "FACT_READER_IMPORTS_IMPLEMENTATION",
        ),
    ],
)
def test_v13_independence_cannot_use_solver_facade_or_contract_backdoor(module, source, expected):
    assert any(expected in error for error in check_source(source, module))


@pytest.mark.parametrize(
    ("module", "source"),
    [
        ("app.modules.validation.service", "from app.modules.planning.contracts import Snapshot"),
        ("app.modules.validation.service", "from ..households.contracts import MemberSafety"),
        ("app.modules.validation.replay", "from .facts import PrimitiveFacts"),
        ("app.modules.validation.service", "from app.shared.units import Quantity"),
        ("app.modules.learning.router", "from app.modules.execution.contracts import Event"),
        ("app.modules.planning.service", "from app.modules.validation.public import validate"),
        ("app.modules.execution.service", "from app.modules.learning.public import route_signal"),
        ("app.modules.planning.contracts.snapshot", "from .facts import PrimitiveFact"),
    ],
)
def test_v13_independent_contracts_and_orchestration_imports_are_allowed(module, source):
    assert check_source(source, module) == []
