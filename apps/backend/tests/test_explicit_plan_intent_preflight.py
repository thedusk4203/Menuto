"""Independent 528-body baseline and exact nine-name additive compatibility proof."""

import hashlib
import json
import runpy
from pathlib import Path

import pytest
from app.modules.policy import explicit_intent_contracts as c
from pydantic import ValidationError
from pydantic.json_schema import models_json_schema

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"
NAMES = (
    "ExplicitPlanIntentContextV1",
    "ExplicitPlanIntentBudgetV1",
    "ExplicitPlanIntentRequestV1",
    "ExplicitPlanIntentValuesV1",
    "PlanIntentAxisEvidenceV1",
    "ResolvedExplicitPlanIntentV1",
    "PlanIntentDiagnosticV1",
    "PlanIntentResolutionV1",
    "PlanIntentCheckV1",
)


def test_preflight_exact_nine_names_and_virtual_delta_without_export_changes():
    manifest = json.loads((FIXTURES / "explicit_plan_intent_export_names.json").read_text())
    assert len(manifest) == 9 and set(manifest) == set(NAMES)
    actual = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
    baseline = json.loads((FIXTURES / "explicit_plan_intent_compatibility.json").read_text())
    assert len(baseline["definitions"]) == 528 and len(actual) == 537
    old = {name: actual[name] for name in baseline["definitions"]}
    registered = runpy.run_path(str(ROOT / "tools/export_domain_contracts.py"))["CONTRACTS"]
    _, proposed = models_json_schema([(model, "validation") for model in registered])
    new = proposed["$defs"]
    assert len(new) == 537
    assert set(new) - set(old) == set(NAMES)
    assert set(old) <= set(new)
    for name, body in old.items():
        assert new[name] == body, name
    assert new == actual
    assert baseline["base"] == "b7992898698a8a8a3493b3c260939325cc494063"
    assert set(baseline["definitions"]) == set(old)
    for name, digest in baseline["definitions"].items():
        assert (
            hashlib.sha256(
                json.dumps(old[name], sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            == digest
        ), name


def test_preflight_all_fields_required_frozen_and_no_extra():
    for name in NAMES:
        model = getattr(c, name)
        assert model.model_config["frozen"] is True
        assert model.model_config["extra"] == "forbid"
        assert all(field.is_required() for field in model.model_fields.values()), name
    budget = c.ExplicitPlanIntentBudgetV1(constraint="NONE", amount=None)
    with pytest.raises(ValidationError):
        budget.constraint = "TARGET"
    with pytest.raises(ValidationError):
        c.ExplicitPlanIntentBudgetV1(constraint="NONE", amount=None, hidden_default=True)


@pytest.mark.parametrize("kind", ["TARGET", "SPEND_LIMIT"])
def test_preflight_zero_money_is_preserved_as_a_shape(kind):
    budget = c.ExplicitPlanIntentBudgetV1(
        constraint=kind, amount={"amount_minor": 0, "currency": "VND"}
    )
    assert budget.constraint == kind and budget.amount.amount_minor == 0
    assert budget.amount.currency == "VND"


@pytest.mark.parametrize("amount", [-1, True, 1.0, "1", 2**63])
def test_preflight_money_rejects_coercion_or_overflow(amount):
    with pytest.raises(ValidationError):
        c.ExplicitPlanIntentBudgetV1(
            constraint="TARGET", amount={"amount_minor": amount, "currency": "VND"}
        )


@pytest.mark.parametrize("name", ["PlanIntentResolutionV1", "PlanIntentCheckV1"])
def test_preflight_outputs_have_closed_authority_literal_shapes(name):
    fields = getattr(c, name).model_fields
    from typing import get_args

    for key, expected in {
        "environment": "TEST_ONLY",
        "source_authority": "UNAUTHENTICATED_DECLARATION",
        "validation_authority": "UNVERIFIED_TRANSPORT",
        "numerical_use": "NOT_ADMITTED",
        "production_admission": "CLOSED",
        "resolved_plan_policy_ready": False,
        "planner_ready": False,
        "activation_ready": False,
    }.items():
        assert get_args(fields[key].annotation) == (expected,)
