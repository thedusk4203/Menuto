"""Synthetic authoring fixtures. No planner/validator or production activation claim."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.snapshots import Horizon
from app.modules.planning import contracts as c

NOW = datetime.now(UTC)


def graph_data(household=None, plan=None, member=None):
    member = member or uuid4()
    return dict(
        household_id=household or uuid4(),
        plan_id=plan or uuid4(),
        tracked_member_id=member,
        horizon=Horizon(start=NOW - timedelta(days=1), end=NOW + timedelta(days=7)),
        meals=[
            dict(
                node_id=uuid4(),
                scheduled_at=NOW + timedelta(days=i + 1),
                meal_kind="OUTSIDE",
                participants=[dict(member_id=member, portion_factor="1", nutrition_role="TRACKED")],
            )
            for i in range(2)
        ],
    )


def propose_command(graph, actor, **kw):
    return c.ProposePlanCommand(
        **(
            dict(
                proposal_id=uuid4(),
                graph=graph,
                expected_generation=-1,
                scope="REMAINING_HORIZON",
                effective_from=NOW,
                actor_user_id=actor,
                source_system="manual",
                idempotency_key=str(uuid4()),
                reason="Explicit authored planning intent",
            )
            | kw
        )
    )


def publish_command(proposal, actor, authorization_id, **kw):
    return c.PublishPlanRevisionCommand(
        **(
            dict(
                household_id=proposal.graph.household_id,
                plan_id=proposal.graph.plan_id,
                proposal_id=proposal.id,
                authorization_id=authorization_id,
                actor_user_id=actor,
                source_system="manual",
                idempotency_key=str(uuid4()),
            )
            | kw
        )
    )
