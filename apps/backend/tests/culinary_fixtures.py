"""Explicit synthetic culinary intent, never production activation evidence."""

from uuid import uuid4

from app.modules.planning.contracts import BoundPlanIntentGraph, BoundPlanProposalSnapshot
from app.modules.planning.culinary import author_binding
from app.modules.recipes.contracts import RecipeProvenance, RecipeVersionSnapshot
from app.modules.validation.contracts import CulinaryValidationInput
from recipe_fixtures import provenance, recipe_data
from validation_fixtures import subject


def culinary_source(recipe=None, selected=(), deltas=None):
    s = subject()
    r = recipe or RecipeVersionSnapshot.model_validate(recipe_data())
    p_id = uuid4()
    batch_id = s.proposal.graph.batches[0].node_id
    b = author_binding(
        recipe=r,
        tier_id=r.portion_tiers[0].id,
        selected_rule_ids=selected,
        deltas=deltas or {i.id: 0 for i in r.ingredients},
        provenance=RecipeProvenance(**provenance()),
        household_id=s.household_id,
        plan_id=s.proposal.graph.plan_id,
        proposal_id=p_id,
        batch_node_id=batch_id,
    )
    data = s.proposal.graph.model_dump() | {
        "contract_version": "plan-intent.v3",
        "culinary_bindings": (b,),
        "batches": (
            dict(
                node_id=batch_id,
                recipe_version_id=r.id,
                tier_id=b.tier_id,
                planned_servings=b.planned_servings,
                planned_at=s.proposal.graph.batches[0].planned_at,
                culinary_signature=b.semantic_fingerprint(),
            ),
        ),
    }
    g = BoundPlanIntentGraph.model_validate(data)
    p = BoundPlanProposalSnapshot.model_validate(
        s.proposal.model_dump(exclude={"contract_version"})
        | {"id": p_id, "graph": g, "graph_hash": g.fingerprint()}
    )
    return CulinaryValidationInput(proposal=p, recipes=(r,))


def altered(source, **changes):
    b = source.proposal.graph.culinary_bindings[0].model_copy(update=changes)
    g = source.proposal.graph.model_copy(update={"culinary_bindings": (b,)})
    return source.model_copy(update={"proposal": source.proposal.model_copy(update={"graph": g})})
