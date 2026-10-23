"""Explicit authored selection producer; not a variant generator or validator."""

from uuid import UUID

from pydantic import TypeAdapter

from app.modules.planning.contracts import CulinaryRequirementBinding, PlannedCulinaryBinding
from app.modules.recipes.contracts import resolve_culinary_binding


def author_binding(
    *,
    recipe,
    tier_id,
    selected_rule_ids,
    deltas,
    provenance,
    household_id,
    plan_id,
    proposal_id,
    batch_node_id,
):
    selected_rule_ids = TypeAdapter(tuple[UUID, ...]).validate_python(selected_rule_ids)
    resolved, transformations, servings = resolve_culinary_binding(
        recipe, tier_id, selected_rule_ids, deltas
    )
    rules = {r.requirement_id: r.id for r in recipe.variant_rules if r.id in selected_rule_ids}
    chosen = [r for r in recipe.variant_rules if r.id in selected_rule_ids]
    combo = (
        next(
            (
                c.id
                for c in recipe.approved_combinations
                if set(c.rule_ids) == set(selected_rule_ids)
            ),
            None,
        )
        if sum(r.structural for r in chosen) > 1
        else None
    )
    paths = {t.requirement_id: t.id for t in transformations}
    b = PlannedCulinaryBinding(
        household_id=household_id,
        plan_id=plan_id,
        proposal_id=proposal_id,
        batch_node_id=batch_node_id,
        recipe_version_id=recipe.id,
        tier_id=tier_id,
        planned_servings=servings,
        approved_combination_id=combo,
        provenance=provenance,
        requirements=tuple(
            CulinaryRequirementBinding(
                requirement_id=r.requirement_id,
                selected_rule_id=rules.get(r.requirement_id),
                ingredient_id=r.ingredient_id,
                quantity=r.quantity,
                adjustment_delta=r.adjustment_delta,
                transformation_id=paths.get(r.requirement_id),
            )
            for r in resolved
        ),
        fingerprint="0" * 64,
    )
    return b.model_copy(update={"fingerprint": b.expected_fingerprint()})


def bind_generated_candidate(*, candidate, recipe, **owner):
    """Select a culinary possibility into frozen intent, never confer validation authority."""
    from app.modules.recipes.contracts import CulinaryCandidateDraft, RecipeVersionSnapshot
    from app.modules.recipes.public import recipe_source_hash

    candidate = CulinaryCandidateDraft.model_validate(candidate.model_dump())
    recipe = RecipeVersionSnapshot.model_validate(recipe.model_dump())
    if (
        recipe.review_status != "REVIEWED"
        or candidate.recipe_version_id != recipe.id
        or candidate.recipe_source_hash != recipe_source_hash(recipe)
        or candidate.provenance != recipe.provenance
    ):
        raise ValueError("Candidate does not belong to the exact reviewed RecipeVersion snapshot")
    resolved, transforms, count = resolve_culinary_binding(
        recipe,
        candidate.tier_id,
        candidate.selected_rule_ids,
        {r.requirement_id: r.adjustment_delta for r in candidate.resolved_ingredients},
    )
    if (
        sorted(resolved, key=lambda r: str(r.requirement_id))
        != sorted(candidate.resolved_ingredients, key=lambda r: str(r.requirement_id))
        or sorted(transforms, key=lambda t: str(t.id))
        != sorted(candidate.transformations, key=lambda t: str(t.id))
        or count != candidate.serving_count
    ):
        raise ValueError("Candidate resolved claims disagree with authored primitives")
    return author_binding(
        recipe=recipe.model_copy(
            update={
                "approved_combinations": tuple(
                    sorted(recipe.approved_combinations, key=lambda c: str(c.id))
                )
            }
        ),
        tier_id=candidate.tier_id,
        selected_rule_ids=candidate.selected_rule_ids,
        deltas={r.requirement_id: r.adjustment_delta for r in candidate.resolved_ingredients},
        **owner,
    )
