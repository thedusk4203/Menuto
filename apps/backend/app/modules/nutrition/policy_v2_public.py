"""Retained, unverified v2 transport. No consumer validation or admission authority."""

from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition import policy_v2_contracts as v
from app.modules.nutrition.policy_v2 import _identity, derive_policy_v2


def prepare_policy_v2_input(basis_sources):
    s = b.parse_basis(basis_sources, b.BasisApplicabilitySourcesV1)
    data = dict(
        contract_version="nutrition-policy-integration-input.v2",
        profile="PIV2_SAME_MEANING_EXACT_PERIOD_SUM_V1",
        basis_sources=s,
        identity=_identity(s),
        environment="TEST_ONLY",
    )
    return v.NutritionPolicyIntegrationInputV2(
        **data, source_fingerprint=v.policy_v2_hash("input", data)
    )


def policy_v2_handoff(retained_input):
    i = v.parse_policy_v2(retained_input, v.NutritionPolicyIntegrationInputV2)
    return v.NutritionPolicyHandoffV2(
        contract_version="nutrition-policy-handoff.v2",
        input=i,
        result=derive_policy_v2(i),
        retained_check=None,
        environment="TEST_ONLY",
        validation_authority="UNVERIFIED_TRANSPORT",
        production_admission="CLOSED",
        planner_ready=False,
        activation_ready=False,
    )


def admit_production_policy_v2(value):
    # Parsing or a rehashed positive TEST_ONLY result cannot open production admission.
    raise PermissionError("PRODUCTION_GATE_CLOSED")
