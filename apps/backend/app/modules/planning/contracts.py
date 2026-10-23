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
from app.modules.catalog.contracts import IngredientIdentityFact, NutritionReferenceFact
from app.modules.cooking.contracts import PlannedBatchAllocationIntent, PlannedCookingBatchIntent
from app.modules.households.contracts import HouseholdMemberIdentity, MealParticipants
from app.modules.inventory.contracts import InventoryCandidateLot, PhysicalInventorySnapshot
from app.modules.nutrition.contracts import (
    CanonicalMemberSafetySnapshot,
    ResolvedNutrients,
    ResolvedNutritionPortion,
)
from app.modules.recipes.contracts import (
    CulinaryCandidateDraft,
    PreparationOutputEstimate,
    RecipeProvenance,
    RecipeVersionSnapshot,
)
from app.modules.retail.contracts import (
    ProcurementSnapshotDraft,
    ProcurementSupplyPath,
    RetailerStatusFact,
)
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


class BoundCookingBatchIntent(Contract):
    node_id: UUID
    recipe_version_id: UUID
    tier_id: UUID
    planned_servings: PositiveDecimal
    planned_at: AwareTime
    status: Literal["PLANNED", "RETIRED"] = "PLANNED"
    culinary_signature: Sha256


class BoundPlanIntentGraph(Contract):
    household_id: UUID
    plan_id: UUID
    tracked_member_id: UUID
    horizon: Horizon
    meals: tuple[MealIntent, ...] = Field(min_length=1)
    allocations: tuple[PlannedBatchAllocationIntent, ...] = ()
    shopping: tuple[ShoppingRequirementIntent, ...] = ()
    shopping_contributions: tuple[ShoppingDemandContributionIntent, ...] = ()
    reservations: tuple[ReservationIntent, ...] = ()
    contract_version: Literal["plan-intent.v3"] = "plan-intent.v3"
    batches: tuple[BoundCookingBatchIntent, ...] = ()
    culinary_bindings: tuple[PlannedCulinaryBinding, ...] = ()

    def content(self):
        result = PlanIntentGraph.content(self)
        result["culinary_bindings"] = [
            b.payload() | {"fingerprint": b.fingerprint}
            for b in sorted(self.culinary_bindings, key=lambda b: str(b.batch_node_id))
        ]
        return result

    def fingerprint(self):
        return PlanIntentGraph.fingerprint(self)

    @model_validator(mode="after")
    def structural_graph(self):
        return PlanIntentGraph.graph_integrity(self)

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


class ProposeBoundPlanCommand(Contract):
    proposal_id: UUID
    expected_generation: Annotated[int, Field(strict=True, ge=-1)]
    expected_revision: Annotated[int, Field(strict=True, ge=0)] | None = None
    scope: RevisionScope
    effective_from: AwareTime
    actor_user_id: UUID
    source_system: Identifier
    idempotency_key: Identifier
    reason: Label
    contract_version: Literal["plan-propose.v2-culinary"] = "plan-propose.v2-culinary"
    graph: BoundPlanIntentGraph

    @model_validator(mode="after")
    def proposal_owner(self):
        if any(b.proposal_id != self.proposal_id for b in self.graph.culinary_bindings):
            raise ValueError("Binding belongs to another proposal")
        return self


class BoundPlanProposalSnapshot(Contract):
    status: Literal["IMMUTABLE_INTENT_PROPOSAL"] = "IMMUTABLE_INTENT_PROPOSAL"
    activation_ready: Literal[False] = False
    id: UUID
    proposal_no: int
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
        return PlanProposalSnapshot.recompute_hash(self)

    contract_version: Literal["plan-proposal.v2-culinary"] = "plan-proposal.v2-culinary"
    graph: BoundPlanIntentGraph

    @model_validator(mode="after")
    def proposal_owner(self):
        if any(b.proposal_id != self.id for b in self.graph.culinary_bindings):
            raise ValueError("Binding belongs to another proposal")
        return self


class BoundPlanRevisionSnapshot(Contract):
    household_id: UUID
    plan_id: UUID
    revision_no: int
    parent_revision_no: int | None
    parent_graph_hash: Sha256 | None
    reason_kind: Literal["INITIAL_ACTIVATED_BASELINE", "PLAN_REVISION"]
    authorization_id: UUID
    created_at: AwareTime

    @model_validator(mode="after")
    def exact_revision_chain(self):
        return PlanRevisionSnapshot.exact_revision_chain(self)

    contract_version: Literal["plan-revision.v2-culinary"] = "plan-revision.v2-culinary"
    proposal: BoundPlanProposalSnapshot


class BoundActivePlanSnapshot(Contract):
    workspace: PlanWorkspaceDraft

    @model_validator(mode="after")
    def exact_head(self):
        return ActivePlanSnapshot.exact_head(self)

    contract_version: Literal["active-plan.v2-culinary"] = "active-plan.v2-culinary"
    revision: BoundPlanRevisionSnapshot


# MTR-019C is additive; frozen plan/candidate wire types above retain their semantics.
_GROUNDING_SET_FIELDS = frozenset(
    {
        "procurement_class_ids",
        "nutrition_selections",
        "participants",
        "ingredients",
        "nutrition_references",
        "procurements",
        "retailer_statuses",
        "members",
        "member_safety",
        "constraints",
        "lots",
        "positions",
        "portion_tiers",
        "variant_rules",
        "approved_combinations",
        "transformations",
        "quantities",
        "rule_ids",
        "selected_rule_ids",
        "resolved_ingredients",
        "triggers",
        "options",
        "ingredient_facts",
        "preparation_outputs",
        "procurement_paths",
        "inventory_paths",
        "issues",
    }
)
_GROUNDING_LEDGER_FIELDS = frozenset({"movements", "reservations", "releases"})


def grounding_canonical_json(data):
    """Only declared sets sort. Future ordered arrays need an explicit ordinal policy."""

    def canonical(value, field=None):
        if isinstance(value, dict):
            return {k: canonical(v, k) for k, v in value.items()}
        if isinstance(value, list):
            rows = [canonical(v) for v in value]
            if field in _GROUNDING_LEDGER_FIELDS:
                return sorted(
                    rows, key=lambda r: (r["occurred_at"], r["phase"], r["ledger_sequence"])
                )
            if field not in _GROUNDING_SET_FIELDS:
                raise ValueError(f"Undeclared collection ordering: {field}")
            return sorted(rows, key=lambda r: json.dumps(r, sort_keys=True, separators=(",", ":")))
        return value

    return json.dumps(canonical(data), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class GroundingNutritionSelection(Contract):
    requirement_id: UUID
    reference_id: UUID


class CandidateGroundingRequest(Contract):
    contract_version: Literal["candidate-grounding-request.v1"] = "candidate-grounding-request.v1"
    candidate: CulinaryCandidateDraft
    household_id: UUID
    tracked_member_id: UUID
    participants: MealParticipants
    region_code: Identifier
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    as_of: AwareTime
    procurement_class_ids: tuple[UUID, ...] = ()
    nutrition_selections: tuple[GroundingNutritionSelection, ...] = ()

    @model_validator(mode="after")
    def unique_selection(self):
        ids = [s.requirement_id for s in self.nutrition_selections]
        if len(ids) != len(set(ids)):
            raise ValueError("Ambiguous nutrition selection for requirement")
        return self


class CandidateGroundingSources(Contract):
    contract_version: Literal["candidate-grounding-sources.v1"] = "candidate-grounding-sources.v1"
    recipe: RecipeVersionSnapshot
    ingredients: tuple[IngredientIdentityFact, ...]
    nutrition_references: tuple[NutritionReferenceFact, ...]
    procurements: tuple[ProcurementSnapshotDraft, ...]
    retailer_statuses: tuple[RetailerStatusFact, ...]
    members: tuple[HouseholdMemberIdentity, ...]
    member_safety: tuple[CanonicalMemberSafetySnapshot, ...]
    inventory: PhysicalInventorySnapshot

    @model_validator(mode="after")
    def unique_sources(self):
        times = [(s.retailer_id, s.effective_at) for s in self.retailer_statuses]
        if len(times) != len(set(times)):
            raise ValueError("Ambiguous retailer status effective timestamp")
        for collection, ids in (
            (self.ingredients, [i.id for i in self.ingredients]),
            (self.nutrition_references, [r.id for r in self.nutrition_references]),
            (self.procurements, [s.procurement_class.id for s in self.procurements]),
            (self.retailer_statuses, [s.id for s in self.retailer_statuses]),
            (self.members, [m.member_id for m in self.members]),
            (self.member_safety, [m.member_id for m in self.member_safety]),
        ):
            if len(collection) != len(set(ids)):
                raise ValueError("Duplicate captured source identity")
        return self

    def fingerprint(self):
        return sha256(grounding_canonical_json(self.model_dump(mode="json")).encode()).hexdigest()


class GroundedIngredientFacts(Contract):
    requirement_id: UUID
    nutrition: ResolvedNutritionPortion
    procurement_paths: tuple[ProcurementSupplyPath, ...]
    inventory_paths: tuple[InventoryCandidateLot, ...]


class GroundingIssue(Contract):
    code: Identifier
    severity: Literal["ERROR", "WARNING"]
    scope: UUID | None = None
    detail: Label


class GroundedDishCandidate(Contract):
    """Complete supported primitives for shortlist input, never global feasibility/authority."""

    contract_version: Literal["grounded-dish-candidate.v1"] = "grounded-dish-candidate.v1"
    status: Literal["PRIMITIVES_RESOLVED"] = "PRIMITIVES_RESOLVED"
    shortlist_input_ready: Literal[True] = True
    activation_ready: Literal[False] = False
    request: CandidateGroundingRequest
    sources: CandidateGroundingSources
    ingredient_facts: tuple[GroundedIngredientFacts, ...] = Field(min_length=1)
    preparation_outputs: tuple[PreparationOutputEstimate, ...]
    input_nutrition: ResolvedNutrients
    fingerprint: Sha256

    def canonical_json(self):
        return grounding_canonical_json(self.model_dump(mode="json"))

    def expected_fingerprint(self):
        return sha256(
            grounding_canonical_json(self.model_dump(mode="json", exclude={"fingerprint"})).encode()
        ).hexdigest()

    @model_validator(mode="after")
    def identity(self):
        if self.fingerprint != self.expected_fingerprint():
            raise ValueError("Grounded candidate fingerprint differs")
        return self


class CandidateGroundingResult(Contract):
    contract_version: Literal["candidate-grounding-result.v1"] = "candidate-grounding-result.v1"
    status: Literal["GROUNDED", "INCOMPLETE", "REJECTED"]
    activation_ready: Literal[False] = False
    candidate: GroundedDishCandidate | None
    issues: tuple[GroundingIssue, ...]

    @model_validator(mode="after")
    def readiness(self):
        if (self.status == "GROUNDED") != (self.candidate is not None):
            raise ValueError("Incomplete/rejected grounding exposes no eligible candidate")
        if self.candidate is not None and any(i.severity == "ERROR" for i in self.issues):
            raise ValueError("Blocking findings cannot accompany an eligible candidate")
        return self
