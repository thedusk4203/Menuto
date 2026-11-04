"""Bounded policy capability. No enrollment, production content or planner authority."""

from app.domain.feature_identity import canonical
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.synthesis import (
    admit_production_nutrition_policy,
    nutrition_policy_requirements,
    synthesize_nutrition_policy,
    validate_nutrition_policy,
)

__all__ = [
    "admit_production_nutrition_policy",
    "capture_nutrition_synthesis_sources",
    "nutrition_policy_requirements",
    "nutrition_policy_reference",
    "synthesize_nutrition_policy",
    "validate_nutrition_policy",
]


def capture_nutrition_synthesis_sources(session, value):
    from app.modules.nutrition.synthesis_sources import (
        capture_nutrition_synthesis_sources as capture,
    )

    return capture(session, value)


def nutrition_policy_reference(value, report):
    policy = validate_nutrition_policy(value)
    report = c.NutritionPolicyValidationReport.model_validate(canonical(report))
    if (
        policy.outcome != "AVAILABLE"
        or report.decision != "CONSISTENT"
        or report.policy_fingerprint != policy.result_fingerprint
        or report.source_fingerprint != policy.inputs.source_fingerprint
        or policy.inputs.request.precision is None
    ):
        raise ValueError("Exact complete policy and independent report required")
    return c.NutritionPolicyReference(
        policy=policy,
        validation=report,
        environment=policy.environment,
        precision=policy.inputs.request.precision,
    )
