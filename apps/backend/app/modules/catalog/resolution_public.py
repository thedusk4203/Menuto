"""Additive NRE owner capture surface. Frozen public.py remains byte-exact."""

from sqlalchemy import func, select

from app.modules.catalog.models import Ingredient
from app.modules.catalog.models import NutritionFact as NutritionRow
from app.modules.catalog.public import catalog_facts


def capture_resolution_catalog(session, ingredient_ids, *, row_budget=8192):
    """NRE owner read: bound the complete selected closure before materializing rows."""
    if type(row_budget) is not int or not 0 <= row_budget <= 8192:
        raise ValueError("RESOURCE_EXCEEDED: owner row budget")
    ids = tuple(sorted(set(ingredient_ids), key=str))
    if len(ids) > 1024:
        raise ValueError("RESOURCE_EXCEEDED: ingredient closure")
    count = session.scalar(
        select(func.count()).select_from(NutritionRow).where(NutritionRow.ingredient_id.in_(ids))
    )
    identity_count = session.scalar(
        select(func.count()).select_from(Ingredient).where(Ingredient.id.in_(ids))
    )
    if count > 512 or count + identity_count > row_budget:
        raise ValueError("RESOURCE_EXCEEDED: nutrition reference rows")
    # All statuses/versions, including unselected references, are retained.
    return catalog_facts(session, ids)
