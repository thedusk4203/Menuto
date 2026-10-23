"""Explicit binding of authored culinary choices, not demand-driven candidate generation."""

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
