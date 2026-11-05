"""Terminal NRE surface, deliberately separate from frozen synthesis v1."""

from app.modules.nutrition.resolution_contracts import NutritionResolutionHandoffV2
from app.modules.nutrition.resolution_estimator import estimate_nutrition_resolution

__all__ = ("estimate_nutrition_resolution", "nutrition_resolution_handoff")


def nutrition_resolution_handoff(sources):
    """Wire transport only; consumers must invoke fresh independent Validation."""
    return NutritionResolutionHandoffV2(
        sources=sources, estimate=estimate_nutrition_resolution(sources)
    )
