"""One read-only source cut; frozen adapters keep the caller's transaction and child clocks."""

from sqlalchemy import text

from app.modules.catalog.public import ingredient_protein_frontier
from app.modules.learning.contracts import (
    ExposurePreviewRequest,
    FeatureExposurePreviewRequest,
    FeatureExposureSourceSnapshotDraft,
    MainProteinExposureFrontier,
    RecipeExposureFrontier,
    derive_preview_facts,
)
from app.modules.planning.contracts import CulinaryFeatureCaptureRequest
from app.modules.planning.exposure_capture import capture_exposure_preview_sources
from app.modules.planning.feature_capture import capture_culinary_feature_subject
from app.modules.planning.feature_preview import discover_culinary_feature_assignments
from app.modules.planning.public import PlanStore
from app.modules.recipes.public import culinary_feature_frontier


def capture_feature_exposure_sources(session, request, *, actor_user_id):
    if (
        session.new
        or session.dirty
        or session.deleted
        or session.connection().get_isolation_level() not in {"REPEATABLE READ", "SERIALIZABLE"}
        or session.scalar(text("SHOW transaction_read_only")) != "on"
    ):
        raise ValueError("Feature exposure capture requires clean read-only RR/SERIALIZABLE")
    q = FeatureExposurePreviewRequest.model_validate(request.model_dump())
    members = tuple(
        capture_exposure_preview_sources(
            session,
            ExposurePreviewRequest(
                household_id=q.household_id,
                member_id=mid,
                plan_ids=(q.plan_id,),
                policy=q.recipe_eligibility_policy,
            ),
            actor_user_id=actor_user_id,
        )
        for mid in q.selected_member_ids
    )
    proposal = members[0].sources[0].proposal
    if proposal is None or (proposal.id, proposal.graph_hash) != (q.proposal_id, q.proposal_hash):
        raise ValueError("Selected current proposal required; stale feature exposure request")
    batch_ids = {
        s.batch_node_id for m in members for f in derive_preview_facts(m) for s in f.support
    }
    sources = tuple(
        discover_culinary_feature_assignments(
            capture_culinary_feature_subject(
                session,
                CulinaryFeatureCaptureRequest(
                    household_id=q.household_id,
                    plan_id=q.plan_id,
                    proposal_id=q.proposal_id,
                    proposal_hash=q.proposal_hash,
                    batch_node_id=bid,
                    requested_dimensions=(d,),
                ),
                actor_user_id=actor_user_id,
            )
        )
        for bid in sorted(batch_ids, key=str)
        for d in q.requested_dimensions
    )
    recipe_frontier = culinary_feature_frontier(session)
    frontiers = tuple(
        MainProteinExposureFrontier(
            recipe_frontier=recipe_frontier,
            catalog_frontier=ingredient_protein_frontier(session),
        )
        if d == "MAIN_PROTEIN"
        else RecipeExposureFrontier(
            dimension=d,
            recipe_frontier=recipe_frontier,
        )
        for d in q.requested_dimensions
    )
    return FeatureExposureSourceSnapshotDraft(
        request=q,
        member_sources=members,
        classification_sources=sources,
        frontiers=frontiers,
        capture_completed_at=PlanStore(session).clock(),
    )
