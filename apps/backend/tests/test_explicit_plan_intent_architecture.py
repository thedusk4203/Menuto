"""Exact nine-definition allowance; no generic or transitive producer permission."""

import json
import runpy
from pathlib import Path

import pytest
from explicit_plan_intent_architecture_checks import (
    independent_graph,
    restore_metadata,
    verify_independence,
    verify_metadata_patch,
    verify_purity,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"
CHECK = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]
CHECKER = "app.modules.validation.explicit_plan_intent"
NAMES = json.loads((FIXTURES / "explicit_plan_intent_export_names.json").read_text())


@pytest.mark.parametrize("name", NAMES)
def test_exact_approved_contract_definition_import(name):
    assert CHECK(f"from app.modules.policy.explicit_intent_contracts import {name}", CHECKER) == []


@pytest.mark.parametrize(
    "target",
    [
        "explicit_intent",
        "explicit_intent_public",
        "explicit_intent_contracts._Outcome",
        "explicit_intent_contracts.resolve",
        "services",
    ],
)
def test_unrelated_imports_remain_forbidden(target):
    errors = CHECK("import app.modules.policy." + target, CHECKER)
    assert any("FACT_READER_IMPORTS_IMPLEMENTATION" in e for e in errors)
    assert any("VALIDATION_CONTRACTS_ONLY" in e for e in errors)


@pytest.mark.parametrize(
    "module", ["app.modules.validation.other_checker", "app.modules.learning.explicit_plan_intent"]
)
def test_exact_module_allowance_is_not_prefix_or_context_grant(module):
    assert CHECK(
        "from app.modules.policy.explicit_intent_contracts import PlanIntentCheckV1", module
    )


def test_no_module_star_or_dynamic_import_allowance():
    for source in (
        "import app.modules.policy.explicit_intent_contracts",
        "from app.modules.policy.explicit_intent_contracts import *",
        "import importlib",
    ):
        assert CHECK(source, CHECKER)


def test_direct_and_transitive_dependency_mutations():
    verify_independence()
    verify_purity()
    verify_metadata_patch()
    for source in (
        "import app.modules.policy.explicit_intent",
        "from app.modules.policy import explicit_intent_public",
    ):
        with pytest.raises(AssertionError):
            independent_graph({CHECKER: source})
        graph = {
            CHECKER: "import app.modules.validation.hidden",
            "app.modules.validation.hidden": source,
        }
        with pytest.raises(AssertionError):
            independent_graph(graph)
        assert CHECK(source, "app.modules.validation.hidden")


@pytest.mark.parametrize(
    "mutation", ["unknown_name", "old_body", "historical_assertion", "incorrect_normalization"]
)
def test_piv_d31_rejects_integrity_mutations(monkeypatch, mutation):
    from test_policy_v2 import test_piv_d31_all_frozen_definition_bodies_files_and_schema

    schema_path = ROOT / "packages/contracts/domain.schema.json"
    historical = ROOT / "apps/backend/tests/test_candidate_feature_projection.py"
    original_text, original_bytes = Path.read_text, Path.read_bytes
    schema = json.loads(schema_path.read_text())
    body = historical.read_bytes()
    if mutation == "unknown_name":
        schema["$defs"]["UnexpectedName"] = schema["$defs"].pop("ExplicitPlanIntentBudgetV1")
    elif mutation == "old_body":
        schema["$defs"]["Money"]["description"] = "MUTATED"
    elif mutation == "historical_assertion":
        body = body.replace(
            b'assert len(pins["definitions"]) == 358', b'assert len(pins["definitions"]) == 359'
        )
    else:
        body = body.replace(b"528 retained +9 additive explicit plan intent.", b"UNKNOWN TEXT")

    def read_text(path, *args, **kwargs):
        return json.dumps(schema) if path == schema_path else original_text(path, *args, **kwargs)

    def read_bytes(path, *args, **kwargs):
        return body if path == historical else original_bytes(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    with pytest.raises(AssertionError):
        test_piv_d31_all_frozen_definition_bodies_files_and_schema()


def test_new_metadata_inverse_rejects_unexpected_assertion():
    path = "apps/backend/tests/test_candidate_feature_projection.py"
    package = json.loads((FIXTURES / "explicit_plan_intent_authorized_metadata.json").read_text())
    body = (ROOT / path).read_text()
    with pytest.raises(AssertionError):
        restore_metadata(path, body.replace("+9 additive", "+10 additive"), package)
