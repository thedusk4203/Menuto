"""Read-only capture of sealed authoritative intent; no materialization or authority."""

from sqlalchemy import text

from app.modules.planning.public import PlanStore
from app.modules.recipes.public import authored_version
from app.modules.validation.contracts import CulinaryValidationInput


def capture_culinary_input(session, *, household_id, plan_id, proposal_id):
    if (
        session.connection().get_isolation_level() not in {"REPEATABLE READ", "SERIALIZABLE"}
        or session.scalar(text("SHOW transaction_read_only")) != "on"
    ):
        raise ValueError("Culinary capture requires read-only RR/SERIALIZABLE")
    if session.new or session.dirty or session.deleted:
        raise ValueError("Capture cannot contain pending mutations")
    p = PlanStore(session).proposal(household_id, plan_id, proposal_id)
    return CulinaryValidationInput(
        proposal=p,
        recipes=tuple(
            authored_version(session, key)
            for key in sorted({b.recipe_version_id for b in p.graph.batches}, key=str)
        ),
    )
