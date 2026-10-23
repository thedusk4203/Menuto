"""Read canonical sources only. No caller-provided nutrition/retail summaries accepted."""

from pydantic import ValidationError
from sqlalchemy import text

from app.modules.catalog.public import catalog_facts
from app.modules.households.public import member_identities
from app.modules.inventory.public import InventoryService
from app.modules.nutrition.public import canonical_member_safety
from app.modules.planning.contracts import (
    CandidateGroundingRequest,
    CandidateGroundingResult,
    CandidateGroundingSources,
    GroundingIssue,
)
from app.modules.planning.grounding import resolve_captured_candidate
from app.modules.recipes.public import authored_version
from app.modules.retail.public import capture_procurement_sources


def capture_candidate_sources(session, request):
    if (
        session.connection().get_isolation_level() not in {"REPEATABLE READ", "SERIALIZABLE"}
        or session.scalar(text("SHOW transaction_read_only")) != "on"
        or session.new
        or session.dirty
        or session.deleted
    ):
        raise ValueError(
            "Grounding requires a clean read-only REPEATABLE READ/SERIALIZABLE transaction"
        )
    request = CandidateGroundingRequest.model_validate(request.model_dump())
    recipe = authored_version(session, request.candidate.recipe_version_id)
    identities, references = catalog_facts(
        session,
        {
            *(i.ingredient_id for i in recipe.ingredients),
            *(r.replacement_ingredient_id for r in recipe.variant_rules),
        },
    )
    procurements, statuses = capture_procurement_sources(session, request.procurement_class_ids)
    members = member_identities(session, request.household_id)
    safety = canonical_member_safety(session, request.household_id, [m.member_id for m in members])
    return CandidateGroundingSources(
        recipe=recipe,
        ingredients=identities,
        nutrition_references=references,
        procurements=procurements,
        retailer_statuses=statuses,
        members=members,
        member_safety=safety,
        inventory=InventoryService(session).snapshot(request.household_id, as_of=request.as_of),
    )


def ground_candidate(session, request):
    try:
        sources = capture_candidate_sources(session, request)
    except (LookupError, ValidationError):
        return CandidateGroundingResult(
            status="INCOMPLETE",
            candidate=None,
            issues=(
                GroundingIssue(
                    code="CANONICAL_SOURCE_UNRESOLVED",
                    severity="ERROR",
                    detail="Requested canonical source is missing or incomplete",
                ),
            ),
        )
    return resolve_captured_candidate(request, sources)
