"""Default authored tier planning only; no physical production or consumption."""

from typing import Literal
from uuid import UUID

from app.domain.contracts import AwareTime, Contract, PositiveDecimal


class PlannedCookingBatchIntent(Contract):
    node_id: UUID
    recipe_version_id: UUID
    tier_id: UUID
    planned_servings: PositiveDecimal
    planned_at: AwareTime
    status: Literal["PLANNED", "RETIRED"] = "PLANNED"


class PlannedBatchAllocationIntent(Contract):
    node_id: UUID
    batch_node_id: UUID
    meal_node_id: UUID
    servings: PositiveDecimal
    status: Literal["PLANNED", "RETIRED"] = "PLANNED"
