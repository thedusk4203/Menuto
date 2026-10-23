"""Authored Recipe sources, explicit binding and demand-driven culinary generation."""

from uuid import UUID

from pydantic import TypeAdapter

from app.domain.contracts import Identifier
from app.modules.recipes.contracts import (
    GroundedRecipeVariantDraft,
    RecipeProvenance,
    RecipeVersionSnapshot,
    VariantReason,
    resolve_culinary_binding,
)

# Public producer surface; validation must not import it.
from app.modules.recipes.generation import generate_variants as generate_variants
from app.modules.recipes.generation import recipe_source_hash as recipe_source_hash
from app.modules.recipes.repository import RecipeRepository


def authored_version(session, version_id):
    return RecipeRepository(session).version(version_id)


def bind_culinary_draft(
    *,
    snapshot,
    tier_id,
    selected_rule_ids,
    adjustment_deltas,
    variant_reason,
    derivation_policy_version,
    provenance,
):
    snapshot = RecipeVersionSnapshot.model_validate(snapshot.model_dump())
    tier_id = TypeAdapter(UUID).validate_python(tier_id)
    selected_rule_ids = TypeAdapter(tuple[UUID, ...]).validate_python(selected_rule_ids)
    derivation_policy_version = TypeAdapter(Identifier).validate_python(derivation_policy_version)
    resolved, transformations, servings = resolve_culinary_binding(
        snapshot,
        tier_id,
        selected_rule_ids,
        adjustment_deltas,
    )
    fields = dict(
        recipe_version=snapshot,
        tier_id=tier_id,
        serving_count=servings,
        selected_rule_ids=selected_rule_ids,
        resolved_ingredients=resolved,
        transformations=transformations,
        variant_reason=VariantReason(variant_reason),
        derivation_policy_version=derivation_policy_version,
        provenance=RecipeProvenance.model_validate(provenance),
    )
    # Construct solely to hash; only a fully validated object is returned.
    temporary = GroundedRecipeVariantDraft.model_construct(**fields)
    return GroundedRecipeVariantDraft(**fields, fingerprint=temporary.expected_fingerprint())


def resolve_candidate_source(candidate, recipe):
    """Recompute untrusted culinary claims from the canonical captured authored version."""
    from app.domain.resolution import ResolutionError
    from app.modules.recipes.calculations import cooking_output
    from app.modules.recipes.contracts import CulinaryCandidateDraft, PreparationOutputEstimate

    candidate = CulinaryCandidateDraft.model_validate(candidate.model_dump())
    recipe = RecipeVersionSnapshot.model_validate(recipe.model_dump())
    if (
        recipe.review_status != "REVIEWED"
        or candidate.recipe_version_id != recipe.id
        or candidate.recipe_source_hash != recipe_source_hash(recipe)
        or candidate.provenance != recipe.provenance
    ):
        raise ResolutionError(
            "CULINARY_SOURCE_MISMATCH", "Exact reviewed RecipeVersion is required", rejected=True
        )
    try:
        rows, transforms, servings = resolve_culinary_binding(
            recipe,
            candidate.tier_id,
            candidate.selected_rule_ids,
            {i.requirement_id: 0 for i in candidate.resolved_ingredients},
        )
    except ValueError as exc:
        raise ResolutionError(
            "CULINARY_SELECTION_REJECTED", "Selection was not authored", rejected=True
        ) from exc
    if (
        sorted(rows, key=lambda i: str(i.requirement_id))
        != sorted(candidate.resolved_ingredients, key=lambda i: str(i.requirement_id))
        or sorted(transforms, key=lambda t: str(t.id))
        != sorted(candidate.transformations, key=lambda t: str(t.id))
        or servings != candidate.serving_count
    ):
        raise ResolutionError(
            "CULINARY_RESOLUTION_MISMATCH", "Resolved claims differ from authorship", rejected=True
        )
    return rows, tuple(
        PreparationOutputEstimate(
            transformation=t,
            input=next(i.quantity for i in rows if i.requirement_id == t.requirement_id),
            output=cooking_output(
                t, next(i.quantity for i in rows if i.requirement_id == t.requirement_id)
            ),
        )
        for t in sorted(transforms, key=lambda t: str(t.id))
    )
