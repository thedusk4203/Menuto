"""MTR-008 explicit TEST_ONLY declaration shapes; no source or consumer authority.

These nine additive models carry declarations, never source authority.
Cross-field interpretation belongs to the
producer and must be independently reconstructed by Validation, not shared here.
"""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from app.domain.contracts import AwareTime, Contract, Sha256
from app.domain.snapshots import Horizon
from app.domain.units import Money

_Precision = Literal["RELAXED", "STANDARD", "PRECISION"]
_Cost = Literal["LOW", "NORMAL", "HIGH"]
_Effort = Literal["MINIMAL", "NORMAL", "FLEXIBLE"]
_Outcome = Literal[
    "AVAILABLE_TEST_ONLY", "MISSING_INPUT", "INVALID_INPUT", "UNSUPPORTED", "RESOURCE_EXCEEDED"
]
_Code = Literal[
    "MISSING_FIELD",
    "AXIS_UNDECLARED",
    "MALFORMED_ENCODING",
    "MALFORMED_SHAPE",
    "DUPLICATE_KEY",
    "UNKNOWN_FIELD",
    "CONTEXT_INVALID",
    "AXIS_INVALID",
    "BUDGET_INVALID",
    "VERSION_UNSUPPORTED",
    "SOURCE_UNSUPPORTED",
    "ENVIRONMENT_UNSUPPORTED",
    "STRUCTURE_LIMIT",
    "CLAIM_INVALID",
    "CLAIM_MISMATCH",
    "SOURCE_NOT_CHECKABLE",
    "CHECK_RESOURCE_LIMIT",
]


class ExplicitPlanIntentContextV1(Contract):
    request_id: UUID
    request_revision: Annotated[int, Field(strict=True, ge=0, le=9_223_372_036_854_775_807)]
    household_id: UUID
    actor_user_id: UUID
    tracked_member_id: UUID
    horizon: Horizon
    declared_at: AwareTime


class ExplicitPlanIntentBudgetV1(Contract):
    constraint: Literal["NONE", "TARGET", "SPEND_LIMIT"]
    amount: Money | None


class ExplicitPlanIntentRequestV1(Contract):
    contract_version: Literal["explicit-plan-intent-request.v1"]
    source: Literal["REQUEST_EXPLICIT"]
    environment: Literal["TEST_ONLY"]
    context: ExplicitPlanIntentContextV1
    nutrition_precision: _Precision | None
    cost_preference: _Cost | None
    kitchen_effort: _Effort | None
    budget: ExplicitPlanIntentBudgetV1 | None


class ExplicitPlanIntentValuesV1(Contract):
    nutrition_precision: _Precision
    cost_preference: _Cost
    kitchen_effort: _Effort
    budget: ExplicitPlanIntentBudgetV1


class PlanIntentAxisEvidenceV1(Contract):
    axis: Literal["NUTRITION_PRECISION", "COST_PREFERENCE", "KITCHEN_EFFORT", "BUDGET"]
    source: Literal["REQUEST_EXPLICIT"]
    input_fingerprint: Sha256
    context_fingerprint: Sha256
    value_fingerprint: Sha256
    interpretation_version: Literal["EXPLICIT_IDENTITY_V1"]


class ResolvedExplicitPlanIntentV1(Contract):
    contract_version: Literal["resolved-explicit-plan-intent.v1"]
    context: ExplicitPlanIntentContextV1
    values: ExplicitPlanIntentValuesV1
    axis_evidence: Annotated[
        tuple[PlanIntentAxisEvidenceV1, ...], Field(min_length=4, max_length=4)
    ]
    semantic_fingerprint: Sha256
    environment: Literal["TEST_ONLY"]


class PlanIntentDiagnosticV1(Contract):
    code: _Code
    path: Annotated[str, Field(min_length=1, max_length=256, pattern=r"^\$[A-Za-z0-9_.]*$")]


class PlanIntentResolutionV1(Contract):
    contract_version: Literal["plan-intent-resolution.v1"]
    interpretation_version: Literal["EXPLICIT_IDENTITY_V1"]
    outcome: _Outcome
    payload: ResolvedExplicitPlanIntentV1 | None
    input_fingerprint: Sha256 | None
    diagnostics: Annotated[tuple[PlanIntentDiagnosticV1, ...], Field(max_length=1)]
    result_fingerprint: Sha256
    environment: Literal["TEST_ONLY"]
    source_authority: Literal["UNAUTHENTICATED_DECLARATION"]
    validation_authority: Literal["UNVERIFIED_TRANSPORT"]
    numerical_use: Literal["NOT_ADMITTED"]
    production_admission: Literal["CLOSED"]
    resolved_plan_policy_ready: Literal[False]
    planner_ready: Literal[False]
    activation_ready: Literal[False]


class PlanIntentCheckV1(Contract):
    contract_version: Literal["plan-intent-check.v1"]
    decision: Literal["CONSISTENT", "INCONSISTENT", "NOT_CHECKABLE"]
    reconstructed_outcome: _Outcome | None
    source_fingerprint: Sha256 | None
    claim_fingerprint: Sha256 | None
    diagnostics: Annotated[tuple[PlanIntentDiagnosticV1, ...], Field(max_length=1)]
    check_fingerprint: Sha256
    environment: Literal["TEST_ONLY"]
    source_authority: Literal["UNAUTHENTICATED_DECLARATION"]
    validation_authority: Literal["UNVERIFIED_TRANSPORT"]
    numerical_use: Literal["NOT_ADMITTED"]
    production_admission: Literal["CLOSED"]
    resolved_plan_policy_ready: Literal[False]
    planner_ready: Literal[False]
    activation_ready: Literal[False]
