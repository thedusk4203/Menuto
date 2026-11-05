"""R-127-01: matching public hashes do not establish independent validation."""

import runpy
from pathlib import Path

import pytest
from app.domain.feature_identity import canonical
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.synthesis_public import nutrition_policy_reference
from app.modules.validation import nutrition_policy as validation
from nutrition_synthesis_pure_fixtures import hash_policy, retained


def test_r12701_nutrition_rejects_forged_consistent_report_with_matching_hashes():
    policy = retained()
    forged = c.NutritionPolicyValidationReport(
        decision="CONSISTENT",
        coverage="SYNTHESIS_SOURCE_AND_POLICY_SEMANTICS",
        findings=(),
        policy_fingerprint=policy.result_fingerprint,
        source_fingerprint=policy.inputs.source_fingerprint,
    )
    with pytest.raises(ValueError, match="caller-provided|Caller-provided"):
        nutrition_policy_reference(policy, forged)


def forged_consistent_report(policy):
    return c.NutritionPolicyValidationReport(
        decision="CONSISTENT",
        coverage="SYNTHESIS_SOURCE_AND_POLICY_SEMANTICS",
        findings=(),
        policy_fingerprint=policy.result_fingerprint,
        source_fingerprint=policy.inputs.source_fingerprint,
    )


def test_r12701_assembly_runs_fresh_checker_and_accepts_no_report_argument(monkeypatch):
    policy = retained()
    actual = validation.validate_nutrition_policy_independently
    calls = []

    def check(value):
        calls.append(value)
        return actual(value)

    monkeypatch.setattr(validation, "validate_nutrition_policy_independently", check)
    reference = validation.nutrition_policy_reference(canonical(policy))
    assert len(calls) == 1 and calls[0].policy == policy
    assert reference.validation.decision == "CONSISTENT"
    assert reference.validation_authority == "UNVERIFIED_TRANSPORT"
    with pytest.raises(TypeError):
        validation.nutrition_policy_reference(policy, forged_consistent_report(policy))


def test_r12701_consumer_rechecks_even_an_exact_matching_fabricated_report(monkeypatch):
    policy = retained()
    claimed = canonical(validation.nutrition_policy_reference(policy))
    claimed["validation"] = canonical(forged_consistent_report(policy))
    actual = validation.validate_nutrition_policy_independently
    calls = []

    def check(value):
        calls.append(value)
        return actual(value)

    monkeypatch.setattr(validation, "validate_nutrition_policy_independently", check)
    fresh = validation.validate_nutrition_policy_reference_independently(claimed)
    assert len(calls) == 1 and calls[0].policy == policy
    assert fresh.validation == actual(calls[0])
    assert fresh.validation_authority == "UNVERIFIED_TRANSPORT"
    assert not fresh.planner_ready and not fresh.activation_ready


def test_r12701_forged_report_cannot_hide_rehashed_policy_semantic_tampering():
    claimed = canonical(validation.nutrition_policy_reference(retained()))
    raw_policy = claimed["policy"]
    raw_policy["claims"] = []
    forged_policy = hash_policy(raw_policy)
    claimed["policy"] = canonical(forged_policy)
    claimed["validation"] = canonical(forged_consistent_report(forged_policy))
    assert claimed["validation"]["policy_fingerprint"] == forged_policy.result_fingerprint
    assert claimed["validation"]["source_fingerprint"] == forged_policy.inputs.source_fingerprint
    with pytest.raises(ValueError, match="Fresh independent validation"):
        validation.validate_nutrition_policy_reference_independently(claimed)


@pytest.mark.parametrize("pin", ["environment", "precision"])
def test_r12701_consumer_rejects_detached_outer_pins(pin):
    claimed = canonical(validation.nutrition_policy_reference(retained()))
    if pin == "environment":
        claimed[pin] = "REVIEWED_PRODUCTION"
    else:
        claimed[pin]["value"] = "RELAXED"
    with pytest.raises(ValueError):
        validation.validate_nutrition_policy_reference_independently(claimed)


def test_r12701_transport_cannot_assert_verified_authority():
    claimed = canonical(validation.nutrition_policy_reference(retained()))
    claimed["validation_authority"] = "INDEPENDENTLY_VALIDATED"
    with pytest.raises(ValueError):
        c.NutritionPolicyReference.model_validate(claimed)


@pytest.mark.parametrize("decision", ["INCONSISTENT", "UNSUPPORTED"])
def test_r12701_consumer_obeys_fresh_verdict_instead_of_attached_consistent(decision, monkeypatch):
    policy = retained()
    claimed = canonical(validation.nutrition_policy_reference(policy))
    claimed["validation"] = canonical(forged_consistent_report(policy))
    actual_report = forged_consistent_report(policy).model_copy(update={"decision": decision})
    monkeypatch.setattr(
        validation, "validate_nutrition_policy_independently", lambda _: actual_report
    )
    with pytest.raises(ValueError, match="Fresh independent validation"):
        validation.validate_nutrition_policy_reference_independently(claimed)


def test_r12701_reference_ownership_does_not_open_cross_module_business_imports():
    root = Path(__file__).resolve().parents[3]
    checker = runpy.run_path(str(root / "tools/check_import_boundaries.py"))["check_source"]
    assert checker(
        "from app.modules.validation.nutrition_policy import nutrition_policy_reference",
        "app.modules.nutrition.synthesis_public",
    )
    assert checker(
        "from app.modules.nutrition.synthesis import validate_nutrition_policy",
        "app.modules.validation.nutrition_policy",
    )
