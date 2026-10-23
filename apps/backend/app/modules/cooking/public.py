"""Context-local intent storage. Composition/transactions live in execution.public."""

from sqlalchemy import insert

from app.modules.cooking.models import PlannedBatchAllocation, PlannedCookingBatch


def store_batch_intents(session, *, proposal_id, household_id, plan_id, batches, allocations):
    context = dict(proposal_id=proposal_id, household_id=household_id, plan_id=plan_id)
    for model, values in [(PlannedCookingBatch, batches), (PlannedBatchAllocation, allocations)]:
        for value in values:
            session.execute(
                insert(model.__table__).values(
                    **context, **value.model_dump(exclude={"culinary_signature"})
                )
            )
