"""M0 draft handoffs shared by planner and validation, never planner implementation.

These are explicitly draft source contracts, not a validation-ready full plan.
No solve, activation or successful validation capability is implied by these types.
"""

import hashlib
import json
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.contracts import (
    AwareTime,
    Contract,
    Identifier,
    PositiveDecimal,
    Sha256,
    Version,
)
from app.domain.units import Money, Provenance, Quantity


class Horizon(Contract):
    start: AwareTime
    end: AwareTime

    @model_validator(mode="after")
    def nonempty(self):
        if self.start >= self.end:
            raise ValueError("Horizon uses a nonempty half-open [start,end) interval")
        return self


class BudgetContract(Contract):
    constraint: Literal["NONE", "TARGET", "SPEND_LIMIT"]
    amount: Money | None = None

    @model_validator(mode="after")
    def explicit_budget(self):
        if (self.constraint == "NONE") != (self.amount is None):
            raise ValueError("NONE has no amount; TARGET/SPEND_LIMIT require an amount")
        return self


class SourceVersion(Contract):
    source: Identifier
    version: Identifier
    fingerprint: Sha256


class ParticipantInput(Contract):
    member_id: UUID
    portion_factor: PositiveDecimal
    nutrition_role: Literal["TRACKED", "SHARED"]


class MealSlotInput(Contract):
    slot_id: UUID
    at: AwareTime
    participants: tuple[ParticipantInput, ...] = Field(min_length=1)
    meal_kind: Literal["HOME", "OUTSIDE", "SKIP"]

    @model_validator(mode="after")
    def distinct_participants(self):
        ids = [p.member_id for p in self.participants]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate meal participant")
        if sum(p.nutrition_role == "TRACKED" for p in self.participants) > 1:
            raise ValueError("Only one tracked nutrition member in V1")
        return self


class PlannerRequestDraft(Contract):
    contract_version: Literal["planner-request.m0-draft.1"] = "planner-request.m0-draft.1"
    household_id: UUID
    actor_user_id: UUID
    tracked_member_id: UUID
    horizon: Horizon
    nutrition_precision: Literal["RELAXED", "STANDARD", "PRECISION"]
    cost_preference: Literal["LOW", "NORMAL", "HIGH"]
    kitchen_effort: Literal["MINIMAL", "NORMAL", "FLEXIBLE"]
    budget: BudgetContract
    meals: tuple[MealSlotInput, ...] = Field(min_length=1)
    sources: tuple[SourceVersion, ...] = Field(min_length=1)
    planner_version: Identifier
    policy_version: Identifier
    # Initial generation has no active revision. Revisions must identify all three fields.
    plan_id: UUID | None = None
    expected_revision: Version | None = None
    baseline_hash: Sha256 | None = None

    @model_validator(mode="after")
    def draft_consistency(self):
        if len({m.slot_id for m in self.meals}) != len(self.meals):
            raise ValueError("Duplicate slot")
        if len({s.source for s in self.sources}) != len(self.sources):
            raise ValueError("Duplicate source version")
        for meal in self.meals:
            if not self.horizon.start <= meal.at < self.horizon.end:
                raise ValueError("Meal must be inside the horizon")
            for participant in meal.participants:
                if (participant.nutrition_role == "TRACKED") != (
                    participant.member_id == self.tracked_member_id
                ):
                    raise ValueError("Participant role disagrees with tracked member identity")
        revision = (self.plan_id, self.expected_revision, self.baseline_hash)
        if any(v is not None for v in revision) and not all(v is not None for v in revision):
            raise ValueError("Revision requires plan_id, expected_revision and baseline_hash")
        return self


class PlannerOutputDraft(Contract):
    contract_version: Literal["planner-output.m0-draft.1"] = "planner-output.m0-draft.1"
    run_id: UUID
    request_hash: Sha256
    status: Literal[
        "OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNKNOWN_TIME_LIMIT", "DATA_INSUFFICIENT", "ERROR"
    ]
    reasons: tuple[Identifier, ...]
    subject_hash: Sha256 | None = None
    # A solver status must never silently imply authorization to activate.
    activation_ready: Literal[False] = False


class CanonicalMemberSafety(Contract):
    member_id: UUID
    source_version: Identifier
    allergen_codes: tuple[Identifier, ...]
    diet_rule_codes: tuple[Identifier, ...]
    excluded_ingredient_ids: tuple[UUID, ...]


class MaterialFact(Contract):
    fact_id: UUID
    household_id: UUID
    ingredient_id: UUID
    quantity: Quantity
    available_from: AwareTime
    usable_until: AwareTime
    provenance: Provenance

    @model_validator(mode="after")
    def usable_window(self):
        if self.usable_until <= self.available_from:
            raise ValueError("Asset requires a positive usable interval")
        return self


class ValidationSubjectDraft(Contract):
    contract_version: Literal["validation-subject.m0-draft.1"] = "validation-subject.m0-draft.1"
    validation_ready: Literal[False] = False
    household_id: UUID
    request: PlannerRequestDraft
    canonical_members: tuple[CanonicalMemberSafety, ...] = Field(min_length=1)
    opening_assets: tuple[MaterialFact, ...]
    # Full root goal, ingredient allocations, authored envelopes, chronological events,
    # scenario quote primitives and horizon bridge are required before ready v1 can exist.
    missing_contracts: tuple[
        Literal[
            "ROOT_GOAL_POLICY",
            "GROUNDED_RECIPE_FACTS",
            "CHRONOLOGICAL_EVENTS",
            "SCENARIO_QUOTES",
            "HORIZON_BRIDGE",
        ],
        ...,
    ] = (
        "ROOT_GOAL_POLICY",
        "GROUNDED_RECIPE_FACTS",
        "CHRONOLOGICAL_EVENTS",
        "SCENARIO_QUOTES",
        "HORIZON_BRIDGE",
    )

    @model_validator(mode="after")
    def source_identity_consistency(self):
        if self.household_id != self.request.household_id:
            raise ValueError("Subject/request household mismatch")
        members = {m.member_id for m in self.canonical_members}
        if len(members) != len(self.canonical_members):
            raise ValueError("Duplicate canonical member")
        if self.request.tracked_member_id not in members:
            raise ValueError("Tracked member must have canonical source safety")
        required = {p.member_id for meal in self.request.meals for p in meal.participants}
        if not required <= members:
            raise ValueError("Every participant must have canonical source safety")
        if any(a.household_id != self.household_id for a in self.opening_assets):
            raise ValueError("Asset from a different household")
        if len({a.fact_id for a in self.opening_assets}) != len(self.opening_assets):
            raise ValueError("Duplicate opening asset")
        return self


class ValidationFinding(Contract):
    code: Identifier
    severity: Literal["FATAL", "ERROR", "WARNING", "INFO"]
    source_domain: Identifier
    scope_ref: Identifier
    proof_refs: tuple[Identifier, ...]


class ValidationReportDraft(Contract):
    contract_version: Literal["validation-report.m0-draft.1"] = "validation-report.m0-draft.1"
    mode: Literal["PRECOMMIT_VALIDATION", "POSTFACT_VALIDATION"]
    subject_hash: Sha256
    expected_revision: Version | None
    findings: tuple[ValidationFinding, ...]
    activation_authorized: Literal[False] = False


class MutationFixtureDraft(Contract):
    """Frozen fixture description, not evidence of a running independent validator."""

    fixture_version: Literal["validator-mutation.m0-draft.1"] = "validator-mutation.m0-draft.1"
    base_subject_ref: Identifier
    mutation: Literal[
        "FORBIDDEN_INGREDIENT",
        "BASIS_MISMATCH",
        "YIELD_OMISSION",
        "CONSUME_BEFORE_BUY",
        "EXPIRED_ASSET",
        "SPEND_SCENARIO_BREACH",
        "BROKEN_ASSUMPTION_PARENT",
        "REWRITE_MATERIALIZED_PAST",
    ]
    target_ref: Identifier
    expected_code: Identifier
    expected_severity: Literal["FATAL", "ERROR"]


def snapshot_hash(contract: Contract) -> str:
    """Contract-versioned canonical JSON; decimals normalized, timestamps normalized to UTC."""
    content = json.dumps(
        contract.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


IdempotencyKey = Annotated[str, Field(min_length=16, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")]


class WriteCommand(Contract):
    household_id: UUID
    actor_user_id: UUID
    idempotency_key: IdempotencyKey
    expected_version: Version
