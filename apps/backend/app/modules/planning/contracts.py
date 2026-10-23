"""Immutable plan intent contracts; authorization is never a caller boolean."""

import json
from datetime import datetime
from decimal import Decimal, localcontext
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.contracts import (
    AwareTime,
    Contract,
    Identifier,
    Label,
    PersistedDecimal,
    PositiveDecimal,
    Sha256,
)
from app.domain.snapshots import Horizon
from app.domain.units import CalculatedQuantity, Quantity
from app.modules.cooking.contracts import PlannedBatchAllocationIntent, PlannedCookingBatchIntent
from app.modules.recipes.contracts import RecipeProvenance
from app.modules.shopping.contracts import (
    ShoppingDemandContributionIntent,
    ShoppingRequirementIntent,
)


class RevisionScope(StrEnum):
    SINGLE_MEAL = "SINGLE_MEAL"
    MULTI_MEAL = "MULTI_MEAL"
    REMAINING_HORIZON = "REMAINING_HORIZON"
    PROCUREMENT_ONLY = "PROCUREMENT_ONLY"


class MealParticipantIntent(Contract):
    member_id: UUID
    portion_factor: PositiveDecimal
    nutrition_role: Literal["TRACKED", "SHARED"]


class MealIntent(Contract):
    node_id: UUID
    scheduled_at: AwareTime
    meal_kind: Literal["HOME", "OUTSIDE", "SKIP"]
    status: Literal["PLANNED", "RETIRED"] = "PLANNED"
    participants: tuple[MealParticipantIntent, ...] = Field(min_length=1)


class ReservationIntent(Contract):
    node_id: UUID
    lot_id: UUID
    meal_node_id: UUID | None = None
    batch_node_id: UUID | None = None
    quantity: Quantity

    @model_validator(mode="after")
    def allocation(self):
        if (self.meal_node_id is None) == (self.batch_node_id is None) or self.quantity.amount <= 0:
            raise ValueError("Reservation requires exactly one target and positive quantity")
        return self


def canonical_value(value):
    if isinstance(value, datetime):
        return value.isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: canonical_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [canonical_value(v) for v in value]
    return value


class PlanIntentGraph(Contract):
    contract_version: Literal["plan-intent.v1", "plan-intent.v2"] = "plan-intent.v2"
    household_id: UUID
    plan_id: UUID
    tracked_member_id: UUID
    horizon: Horizon
    meals: tuple[MealIntent, ...] = Field(min_length=1)
    batches: tuple[PlannedCookingBatchIntent, ...] = ()
    allocations: tuple[PlannedBatchAllocationIntent, ...] = ()
    shopping: tuple[ShoppingRequirementIntent, ...] = ()
    shopping_contributions: tuple[ShoppingDemandContributionIntent, ...] = ()
    reservations: tuple[ReservationIntent, ...] = ()

    def content(self):
        fields = self.model_dump()
        for key in (
            "meals",
            "batches",
            "allocations",
            "shopping",
            "reservations",
            "shopping_contributions",
        ):
            fields[key] = sorted(fields[key], key=lambda row: str(row["node_id"]))
        if self.contract_version == "plan-intent.v1":
            fields.pop("shopping_contributions")
        for meal in fields["meals"]:
            meal["participants"] = sorted(
                meal["participants"], key=lambda row: str(row["member_id"])
            )
        return canonical_value(fields)

    def fingerprint(self):
        return sha256(
            json.dumps(
                self.content(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()

    @model_validator(mode="after")
    def graph_integrity(self):
        for values in (
            self.meals,
            self.batches,
            self.allocations,
            self.shopping,
            self.reservations,
            self.shopping_contributions,
        ):
            if len({v.node_id for v in values}) != len(values):
                raise ValueError("Duplicate stable node identity")
        meals = {m.node_id: m for m in self.meals}
        batches = {b.node_id: b for b in self.batches}
        for meal in self.meals:
            if not self.horizon.start <= meal.scheduled_at < self.horizon.end:
                raise ValueError("Meal outside horizon")
            if len({p.member_id for p in meal.participants}) != len(meal.participants):
                raise ValueError("Duplicate participant")
            if any(
                (p.member_id == self.tracked_member_id) != (p.nutrition_role == "TRACKED")
                for p in meal.participants
            ):
                raise ValueError("Tracked participant identity mismatch")
        for batch in self.batches:
            if batch.planned_at >= self.horizon.end:
                raise ValueError("Batch outside upper horizon")
        totals = dict.fromkeys(batches, Decimal(0))
        for a in self.allocations:
            b, m = batches.get(a.batch_node_id), meals.get(a.meal_node_id)
            if b is None or m is None:
                raise ValueError("Allocation crosses graph identity")
            if a.status == "PLANNED":
                if b.status != "PLANNED" or m.status != "PLANNED" or m.meal_kind != "HOME":
                    raise ValueError("Allocation requires active home meal and batch")
                if b.planned_at > m.scheduled_at:
                    raise ValueError("Meal cannot precede planned production")
                with localcontext() as ctx:
                    ctx.prec = 160
                    totals[b.node_id] += a.servings
        if any(totals[b.node_id] > b.planned_servings for b in self.batches):
            raise ValueError("Allocated servings exceed planned production")
        for m in self.meals:
            if (
                m.status == "PLANNED"
                and m.meal_kind == "HOME"
                and not any(
                    a.meal_node_id == m.node_id and a.status == "PLANNED" for a in self.allocations
                )
            ):
                raise ValueError("Home meal requires a concrete authored batch allocation")
        for r in self.reservations:
            target = meals.get(r.meal_node_id) if r.meal_node_id else batches.get(r.batch_node_id)
            if target is None or target.status != "PLANNED":
                raise ValueError("Reservation target must be current planned intent")
        if any(s.need_by > self.horizon.end for s in self.shopping):
            raise ValueError("Shopping beyond horizon")
        if self.contract_version == "plan-intent.v1" and self.shopping_contributions:
            raise ValueError("Legacy v1 cannot carry contribution facts")
        requirements = {s.node_id: s for s in self.shopping}
        contribution_totals = {}
        with localcontext() as ctx:
            ctx.prec = 160
            for c in self.shopping_contributions:
                s = requirements.get(c.requirement_node_id)
                target = (
                    meals.get(c.meal_node_id) if c.meal_node_id else batches.get(c.batch_node_id)
                )
                if s is None or target is None:
                    raise ValueError("Contribution crosses requirement/target graph identity")
                if (c.quantity.basis, c.quantity.item_ref) != (
                    s.quantity.basis,
                    s.quantity.item_ref,
                ):
                    raise ValueError("Contribution measurement identity disagrees with demand")
                contribution_totals.setdefault(s.node_id, Decimal(0))
                if c.status == "PLANNED":
                    if s.status != "PLANNED" or target.status != "PLANNED":
                        raise ValueError("Active contribution requires active demand and target")
                    contribution_totals[s.node_id] += c.quantity.amount
        for key, total in contribution_totals.items():
            s = requirements[key]
            if total != (s.quantity.amount if s.status == "PLANNED" else Decimal(0)):
                raise ValueError("Contribution quantities must conserve exact demand")
        return self


class PlanWorkspaceDraft(Contract):
    contract_version: Literal["plan-workspace.v1"] = "plan-workspace.v1"
    id: UUID
    household_id: UUID
    tracked_member_id: UUID
    horizon: Horizon
    created_by_user_id: UUID
    state: Literal["DRAFT", "ACTIVE"]
    latest_proposal_no: int
    active_revision_no: int | None
    boundary_version: int


class ProposePlanCommand(Contract):
    contract_version: Literal["plan-propose.v1"] = "plan-propose.v1"
    proposal_id: UUID
    graph: PlanIntentGraph
    expected_generation: Annotated[int, Field(strict=True, ge=-1)]
    expected_revision: Annotated[int, Field(strict=True, ge=0)] | None = None
    scope: RevisionScope
    effective_from: AwareTime
    actor_user_id: UUID
    source_system: Identifier
    idempotency_key: Identifier
    reason: Label


class PlanProposalSnapshot(Contract):
    contract_version: Literal["plan-proposal.v1"] = "plan-proposal.v1"
    status: Literal["IMMUTABLE_INTENT_PROPOSAL"] = "IMMUTABLE_INTENT_PROPOSAL"
    activation_ready: Literal[False] = False
    id: UUID
    proposal_no: int
    graph: PlanIntentGraph
    graph_hash: Sha256
    expected_revision: int | None
    scope: RevisionScope
    effective_from: AwareTime
    actor_user_id: UUID
    source_system: Identifier
    idempotency_key: Identifier
    reason: Label
    created_at: AwareTime

    @model_validator(mode="after")
    def recompute_hash(self):
        if self.graph.fingerprint() != self.graph_hash:
            raise ValueError("Snapshot hash disagrees with immutable primitives")
        return self


class PublishPlanRevisionCommand(Contract):
    contract_version: Literal["plan-publish.v1"] = "plan-publish.v1"
    household_id: UUID
    plan_id: UUID
    proposal_id: UUID
    authorization_id: UUID
    actor_user_id: UUID
    source_system: Identifier
    idempotency_key: Identifier


class PlanRevisionSnapshot(Contract):
    contract_version: Literal["plan-revision.v1"] = "plan-revision.v1"
    household_id: UUID
    plan_id: UUID
    revision_no: int
    parent_revision_no: int | None
    parent_graph_hash: Sha256 | None
    reason_kind: Literal["INITIAL_ACTIVATED_BASELINE", "PLAN_REVISION"]
    proposal: PlanProposalSnapshot
    authorization_id: UUID
    created_at: AwareTime

    @model_validator(mode="after")
    def exact_revision_chain(self):
        if (
            (self.household_id, self.plan_id)
            != (self.proposal.graph.household_id, self.proposal.graph.plan_id)
            or self.parent_revision_no != self.proposal.expected_revision
            or (
                self.revision_no == 0
                and (
                    self.parent_revision_no is not None
                    or self.parent_graph_hash is not None
                    or self.reason_kind != "INITIAL_ACTIVATED_BASELINE"
                )
            )
            or (
                self.revision_no > 0
                and (
                    self.parent_revision_no != self.revision_no - 1
                    or self.parent_graph_hash is None
                    or self.reason_kind != "PLAN_REVISION"
                )
            )
            or self.revision_no < 0
        ):
            raise ValueError("Revision identity/parent/hash chain mismatch")
        return self


class HorizonCommitmentsDraft(Contract):
    contract_version: Literal["plan-horizon-handoff.v1-draft"] = "plan-horizon-handoff.v1-draft"
    activation_ready: Literal[False] = False
    revision: PlanRevisionSnapshot
    inventory_frontier: int
    boundary_version: int
    cutoff: AwareTime


class CreatePlanWorkspaceCommand(Contract):
    contract_version: Literal["plan-workspace-create.v1"] = "plan-workspace-create.v1"
    household_id: UUID
    plan_id: UUID
    tracked_member_id: UUID
    horizon: Horizon
    actor_user_id: UUID


class ActivePlanSnapshot(Contract):
    contract_version: Literal["active-plan.v1"] = "active-plan.v1"
    workspace: PlanWorkspaceDraft
    revision: PlanRevisionSnapshot

    @model_validator(mode="after")
    def exact_head(self):
        if self.workspace.state != "ACTIVE" or (
            self.workspace.household_id,
            self.workspace.id,
            self.workspace.active_revision_no,
        ) != (self.revision.household_id, self.revision.plan_id, self.revision.revision_no):
            raise ValueError("ActivePlan snapshot requires exact accepted stable head")
        return self


class CulinaryRequirementBinding(Contract):
    requirement_id: UUID
    selected_rule_id: UUID | None
    ingredient_id: UUID
    quantity: CalculatedQuantity
    adjustment_delta: PersistedDecimal
    transformation_id: UUID | None


class PlannedCulinaryBinding(Contract):
    """Captured claims, independently checked at seal/validation; never cached valid=true."""

    contract_version: Literal["planned-culinary-binding.v1"] = "planned-culinary-binding.v1"
    household_id: UUID
    plan_id: UUID
    proposal_id: UUID
    batch_node_id: UUID
    recipe_version_id: UUID
    tier_id: UUID
    planned_servings: PositiveDecimal
    approved_combination_id: UUID | None
    requirements: tuple[CulinaryRequirementBinding, ...] = Field(min_length=1)
    provenance: RecipeProvenance
    fingerprint: Sha256

    def payload(self):
        result = self.model_dump(mode="json", exclude={"fingerprint"})
        result["planned_servings"] = format(self.planned_servings, "f")
        result["provenance"]["observed_at"] = self.provenance.observed_at.isoformat(
            timespec="microseconds"
        ).replace("+00:00", "Z")
        for row, fact in zip(result["requirements"], self.requirements, strict=True):
            row["quantity"]["amount"] = format(fact.quantity.amount, "f")
            row["adjustment_delta"] = format(fact.adjustment_delta, "f")
        result["requirements"] = sorted(result["requirements"], key=lambda r: r["requirement_id"])
        return result

    def expected_fingerprint(self):
        return sha256(
            json.dumps(
                self.payload(), sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode()
        ).hexdigest()

    def semantic_fingerprint(self):
        result = self.payload()
        result.pop("proposal_id")
        return sha256(
            json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        ).hexdigest()


class BoundCookingBatchIntent(PlannedCookingBatchIntent):
    culinary_signature: Sha256


class BoundPlanIntentGraph(PlanIntentGraph):
    contract_version: Literal["plan-intent.v3"] = "plan-intent.v3"
    batches: tuple[BoundCookingBatchIntent, ...] = ()
    culinary_bindings: tuple[PlannedCulinaryBinding, ...] = ()

    def content(self):
        result = super().content()
        result["culinary_bindings"] = [
            b.payload() | {"fingerprint": b.fingerprint}
            for b in sorted(self.culinary_bindings, key=lambda b: str(b.batch_node_id))
        ]
        return result

    @model_validator(mode="after")
    def exact_binding_ownership(self):
        bindings = {b.batch_node_id: b for b in self.culinary_bindings}
        if len(bindings) != len(self.culinary_bindings) or set(bindings) != {
            b.node_id for b in self.batches
        }:
            raise ValueError("Exactly one binding per batch is required")
        for batch in self.batches:
            b = bindings[batch.node_id]
            if (b.household_id, b.plan_id, b.recipe_version_id, b.tier_id, b.planned_servings) != (
                self.household_id,
                self.plan_id,
                batch.recipe_version_id,
                batch.tier_id,
                batch.planned_servings,
            ) or b.semantic_fingerprint() != batch.culinary_signature:
                raise ValueError("Binding batch/owner/signature mismatch")
        return self


class ProposeBoundPlanCommand(ProposePlanCommand):
    contract_version: Literal["plan-propose.v2-culinary"] = "plan-propose.v2-culinary"
    graph: BoundPlanIntentGraph

    @model_validator(mode="after")
    def proposal_owner(self):
        if any(b.proposal_id != self.proposal_id for b in self.graph.culinary_bindings):
            raise ValueError("Binding belongs to another proposal")
        return self


class BoundPlanProposalSnapshot(PlanProposalSnapshot):
    contract_version: Literal["plan-proposal.v2-culinary"] = "plan-proposal.v2-culinary"
    graph: BoundPlanIntentGraph

    @model_validator(mode="after")
    def proposal_owner(self):
        if any(b.proposal_id != self.id for b in self.graph.culinary_bindings):
            raise ValueError("Binding belongs to another proposal")
        return self


class BoundPlanRevisionSnapshot(PlanRevisionSnapshot):
    contract_version: Literal["plan-revision.v2-culinary"] = "plan-revision.v2-culinary"
    proposal: BoundPlanProposalSnapshot


class BoundActivePlanSnapshot(ActivePlanSnapshot):
    contract_version: Literal["active-plan.v2-culinary"] = "active-plan.v2-culinary"
    revision: BoundPlanRevisionSnapshot
