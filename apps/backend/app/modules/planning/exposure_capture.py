"""Planning-side capture adapter; no Learning IO, writes or consumption inference."""

from sqlalchemy import text

from app.modules.households.public import member_identities, read_household_actor
from app.modules.learning.contracts import (
    ExposurePreviewRequest,
    ExposurePreviewSnapshot,
    ProposalExposureSource,
    RecipeExposureIdentity,
)
from app.modules.planning.public import PlanStore
from app.modules.recipes.public import authored_version


def capture_exposure_preview_sources(session, request, *, actor_user_id):
    if (
        session.new
        or session.dirty
        or session.deleted
        or session.connection().get_isolation_level() not in {"REPEATABLE READ", "SERIALIZABLE"}
        or session.scalar(text("SHOW transaction_read_only")) != "on"
    ):
        raise ValueError("Exposure capture requires clean read-only RR/SERIALIZABLE")
    request = ExposurePreviewRequest.model_validate(request.model_dump())
    read_household_actor(session, request.household_id, actor_user_id)
    members = member_identities(session, request.household_id)
    if request.member_id not in {m.member_id for m in members}:
        raise LookupError("Unknown household member")
    store = PlanStore(session)
    sources = tuple(
        ProposalExposureSource(workspace=w, proposal=p)
        for w, p in (
            store.latest_proposal_source(request.household_id, pid)
            for pid in sorted(request.plan_ids, key=str)
        )
    )
    recipe_ids = {
        batch.recipe_version_id
        for s in sources
        if s.proposal is not None
        for batch in s.proposal.graph.batches
    }
    recipes = []
    for version_id in sorted(recipe_ids, key=str):
        version = authored_version(session, version_id)
        recipes.append(
            RecipeExposureIdentity(
                recipe_version_id=version.id,
                recipe_id=version.recipe.id,
                version=version.version,
                review_status=version.review_status,
                provenance=version.provenance,
            )
        )
    return ExposurePreviewSnapshot(
        household_id=request.household_id,
        member_id=request.member_id,
        captured_at=store.clock(),
        policy=request.policy,
        members=members,
        sources=sources,
        recipes=tuple(recipes),
    )
