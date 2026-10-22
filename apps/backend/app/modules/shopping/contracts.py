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


class ShoppingDemandContributionIntent(Contract):
    node_id: UUID
    requirement_node_id: UUID
    meal_node_id: UUID | None = None
    batch_node_id: UUID | None = None
    quantity: Quantity
    status: Literal["PLANNED", "RETIRED"] = "PLANNED"

    @model_validator(mode="after")
    def target(self):
        if (self.meal_node_id is None) == (self.batch_node_id is None):
            raise ValueError("Contribution requires exactly one meal or batch target")
        if self.quantity.amount <= 0 or self.quantity.basis == "SERVING":
            raise ValueError("Contribution requires positive ingredient material")
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
