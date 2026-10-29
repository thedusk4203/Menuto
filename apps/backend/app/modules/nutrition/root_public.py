"""Bounded Nutrition source/root interface; no enrollment or policy synthesis authority."""

from app.modules.nutrition.root_resolution import (
    resolve_nutrition_root,
    validate_nutrition_root,
)

__all__ = [
    "append_nutrition_source",
    "capture_nutrition_root_sources",
    "resolve_nutrition_root",
    "validate_nutrition_root",
]


def append_nutrition_source(session, command):
    from app.modules.nutrition.root_sources import append_nutrition_source as append

    return append(session, command)


def capture_nutrition_root_sources(session, request):
    from app.modules.nutrition.root_sources import capture_nutrition_root_sources as capture

    return capture(session, request)
