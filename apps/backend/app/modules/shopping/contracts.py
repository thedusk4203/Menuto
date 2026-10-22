"""Typed shopping intent fragments; neither fulfillment nor physical inventory."""

from typing import Literal
from uuid import UUID

from pydantic import model_validator

from app.domain.contracts import AwareTime, Contract
from app.domain.units import Quantity


class ShoppingRequirementIntent(Contract):
    node_id: UUID
    ingredient_id: UUID
    quantity: Quantity
    need_by: AwareTime
    status: Literal["PLANNED", "RETIRED"] = "PLANNED"

    @model_validator(mode="after")
    def material(self):
        if self.quantity.amount <= 0 or self.quantity.basis == "SERVING":
            raise ValueError("Shopping requires positive ingredient material, not dish servings")
        return self


class ObservedAcquisitionCoverageDraft(Contract):
    contract_version: Literal["shopping-acquisition-coverage.v1-draft"] = (
        "shopping-acquisition-coverage.v1-draft"
    )
    activation_ready: Literal[False] = False
    household_id: UUID
    plan_id: UUID
    proposal_id: UUID
    requirement_node_id: UUID
    required: Quantity
    acquired: Quantity
    shortfall: Quantity
    movement_ids: tuple[UUID, ...]
