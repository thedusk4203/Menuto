"""Read-only source capture outside validation; never publishes or mints authority."""

from sqlalchemy import text

from app.modules.catalog.public import catalog_facts
from app.modules.households.public import member_identities
from app.modules.inventory.public import InventoryService
from app.modules.nutrition.public import canonical_member_safety
from app.modules.planning.public import PlanStore
from app.modules.recipes.public import authored_version
from app.modules.validation.contracts import (
    InventoryValidationFacts,
    ValidationSourceFrontier,
    ValidationSubjectSnapshot,
)


def capture_validation_subject(session, *, household_id, plan_id, proposal_id, policy):
    """Caller supplies a read-only REPEATABLE READ/SERIALIZABLE transaction.

    No live source lookup is required once this frozen subject has been returned.
    This is snapshot consistency, not authenticated production PRECOMMIT authority.
    """
    connection = session.connection()
    isolation = connection.get_isolation_level()
    if (
        isolation not in {"REPEATABLE READ", "SERIALIZABLE"}
        or session.scalar(text("SHOW transaction_read_only")) != "on"
    ):
        raise ValueError("Capture requires a read-only REPEATABLE READ or SERIALIZABLE transaction")
    if session.new or session.dirty or session.deleted:
        raise ValueError("Capture cannot contain pending source mutations")
    store = PlanStore(session)
    workspace = store.workspace(household_id, plan_id)
    proposal = store.proposal(household_id, plan_id, proposal_id)
    parent = (
        store.revision(household_id, plan_id, workspace.active_revision_no)
        if workspace.active_revision_no is not None
        else None
    )
    members = member_identities(session, household_id)
    safety = canonical_member_safety(session, household_id, [m.member_id for m in members])
    recipes = tuple(
        authored_version(session, key)
        for key in sorted({b.recipe_version_id for b in proposal.graph.batches}, key=str)
    )
    physical = InventoryService(session).snapshot(household_id)
    ingredient_ids = {r.ingredient_id for recipe in recipes for r in recipe.ingredients}
    ingredient_ids |= {
        r.replacement_ingredient_id for recipe in recipes for r in recipe.variant_rules
    }
    ingredient_ids |= {r.ingredient_id for r in proposal.graph.shopping}
    ingredient_ids |= {lot.ingredient_id for lot in physical.lots if lot.ingredient_id is not None}
    ingredients, nutrients = catalog_facts(session, ingredient_ids)
    return ValidationSubjectSnapshot(
        household_id=household_id,
        proposal=proposal,
        parent_revision=parent,
        source_frontier=ValidationSourceFrontier(
            current_revision_no=workspace.active_revision_no,
            inventory_ledger_sequence=store.inventory_frontier(household_id),
            materialization_boundary_version=workspace.boundary_version,
            capture_consistency=isolation.replace(" ", "_"),
        ),
        members=members,
        member_safety=safety,
        recipes=recipes,
        ingredients=ingredients,
        nutrition_references=nutrients,
        inventory=InventoryValidationFacts(
            **physical.model_dump(exclude={"contract_version", "status", "activation_ready"})
        ),
        policy=policy,
    )
