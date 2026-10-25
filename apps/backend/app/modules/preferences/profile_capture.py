"""One caller-owned coherent read-only cut of raw preferences + owner identities."""

from sqlalchemy import text

from app.modules.catalog.public import ingredient_identities, reviewed_affinity_feature_terms
from app.modules.preferences.contracts import (
    CanonicalPreferenceTargetManifest,
    ExplicitTargetAffinityCaptureRequest,
    ExplicitTargetAffinitySourceSnapshotDraft,
    FeatureTargetManifestEntry,
    IngredientTargetManifestEntry,
    RecipeTargetManifestEntry,
)
from app.modules.preferences.public import PreferenceService
from app.modules.recipes.public import recipe_identities


def capture_explicit_target_affinity_sources(session, request, *, actor_user_id):
    request = ExplicitTargetAffinityCaptureRequest.model_validate(request)
    if session.new or session.dirty or session.deleted:
        raise ValueError("Preference capture requires clean read-only RR/SERIALIZABLE")
    # Frozen capture verifies isolation, read-only mode, member/actor access, and full frontier.
    preferences = PreferenceService(session, actor_user_id=actor_user_id).snapshot(
        request.household_id, request.member_id
    )
    ingredient_ids = {t.ingredient_id for t in request.requested_targets if t.kind == "INGREDIENT"}
    recipe_ids = {t.recipe_id for t in request.requested_targets if t.kind == "DIRECT_RECIPE"}
    term_kinds = {
        t.feature_term_id: t.kind
        for t in request.requested_targets
        if t.kind in {"PROTEIN", "METHOD", "FLAVOR"}
    }
    entries = []
    if ingredient_ids:
        entries.extend(
            IngredientTargetManifestEntry(identity=i)
            for i in ingredient_identities(session, ingredient_ids)
        )
    if recipe_ids:
        entries.extend(
            RecipeTargetManifestEntry(identity=i) for i in recipe_identities(session, recipe_ids)
        )
    if term_kinds:
        entries.extend(
            FeatureTargetManifestEntry(kind=term_kinds[t.id], identity=t)
            for t in reviewed_affinity_feature_terms(session, set(term_kinds))
        )
    return ExplicitTargetAffinitySourceSnapshotDraft(
        request=request,
        preferences=preferences,
        manifest=CanonicalPreferenceTargetManifest(
            household_id=request.household_id, member_id=request.member_id, entries=tuple(entries)
        ),
        capture_completed_at=session.scalar(text("SELECT clock_timestamp()")),
    )
