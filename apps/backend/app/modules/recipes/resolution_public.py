"""Additive NRE owner capture surface. Frozen public.py remains byte-exact."""

from sqlalchemy import text

from app.modules.recipes.public import authored_version


def capture_resolution_recipes(session, version_ids, *, row_budget=8192):
    """NRE additive owner read; immutable aggregate and explicit seal/absence checks."""
    if type(row_budget) is not int or not 0 <= row_budget <= 8192:
        raise ValueError("RESOURCE_EXCEEDED: owner row budget")
    ids = tuple(sorted(set(version_ids), key=str))
    if len(ids) > 32:
        raise ValueError("RESOURCE_EXCEEDED: recipes")
    tables = (
        "recipe_versions",
        "recipe_ingredients",
        "recipe_portion_tiers",
        "recipe_tier_quantities",
        "recipe_variant_rules",
        "recipe_rule_combinations",
        "recipe_combination_members",
        "preparation_transformations",
        "recipe_version_seals",
    )
    rows = session.scalar(
        text(
            "SELECT count(DISTINCT recipe_id) FROM public.recipe_versions "
            "WHERE id=ANY(CAST(:ids AS uuid[]))"
        ),
        {"ids": list(ids)},
    )
    for table in tables:
        column = "id" if table == "recipe_versions" else "recipe_version_id"
        rows += session.scalar(
            text(f'SELECT count(*) FROM public."{table}" WHERE {column}=ANY(CAST(:ids AS uuid[]))'),
            {"ids": list(ids)},
        )
        if rows > row_budget:
            raise ValueError("RESOURCE_EXCEEDED: recipe child rows")
    versions, missing, seals = [], [], []
    for identity in ids:
        if not session.scalar(
            text("SELECT count(*) FROM public.recipe_versions WHERE id=:i"), {"i": identity}
        ):
            missing.append(identity)
            continue
        if (
            session.scalar(
                text("SELECT count(*) FROM public.recipe_version_seals WHERE recipe_version_id=:i"),
                {"i": identity},
            )
            != 1
        ):
            raise ValueError("FORGED_SOURCE: incomplete RecipeVersion seal")
        versions.append(authored_version(session, identity))
        seals.append(identity)
    return tuple(versions), tuple(seals), tuple(missing), rows
