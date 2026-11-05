"""Bounded policy capability. No enrollment, production content or planner authority."""

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
    """Fail closed for the former producer-owned report-acceptance entry point.

    Validation owns reference assembly and consumer revalidation. A serialized report
    is a caller claim, even when its public fingerprints match the complete policy.
    """
    raise ValueError(
        "Caller-provided reports are not independent validation proof; "
        "use the Validation-owned nutrition_policy_reference boundary"
    )
