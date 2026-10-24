"""Synthetic explicit policy values, never production cooldown defaults."""

from datetime import timedelta
from uuid import uuid4

from app.modules.learning import contracts as c
from app.modules.planning.contracts import BoundPlanIntentGraph
from exposure_fixtures import snapshot


def repeated_graph(graph, offsets=(-3600000000,)):
    data = graph.model_dump()
    target = data["meals"][0]
    data["allocations"][0]["servings"] = "1"
    for offset in offsets:
        meal = {**target, "node_id": uuid4()}
        meal["scheduled_at"] += timedelta(microseconds=offset)
        data["meals"] += (meal,)
        data["allocations"] += (
            {
                **data["allocations"][0],
                "node_id": uuid4(),
                "meal_node_id": meal["node_id"],
                "servings": "0.1",
            },
        )
    return BoundPlanIntentGraph.model_validate(data)


def with_graph(source, data, **changes):
    s = source.snapshot if isinstance(source, c.RecipeCooldownInput) else source
    g = BoundPlanIntentGraph.model_validate(data)
    value = s.model_dump()
    value["sources"][0]["proposal"].update(graph=g.model_dump(), graph_hash=g.fingerprint())
    value.update(changes)
    return c.ExposurePreviewSnapshot.model_validate(value)


def cooldown_input(offsets=(-3600000000,)):
    s = snapshot()
    g = repeated_graph(s.sources[0].proposal.graph, offsets)
    s = with_graph(s, g.model_dump())
    return c.RecipeCooldownInput(
        snapshot=s,
        query=c.RecipeCooldownQuery(
            household_id=s.household_id,
            member_id=s.member_id,
            plan_id=g.plan_id,
            proposal_id=s.sources[0].proposal.id,
            meal_node_id=g.meals[0].node_id,
            recipe_id=s.recipes[0].recipe_id,
        ),
        policy=c.RecipeCooldownPolicy(
            policy_id="synthetic.explicit-cooldown",
            policy_version="test.v1",
            duration_microseconds=7200000000,
            provenance=s.policy.provenance,
        ),
    )
