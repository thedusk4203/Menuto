"""Additive TEST_ONLY v2 transport. Serialized records never authorize numerical use."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.domain.contracts import Contract, Identifier, Sha256
from app.domain.feature_identity import canonical, identity_hash
from app.modules.households.contracts import HouseholdMemberIdentity
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition import synthesis_contracts as s
from app.modules.nutrition.resolution_contracts import NreDelta
from app.modules.nutrition.resolution_limits import ingest, structure

PolicyV2Outcome = Literal[
    "AVAILABLE_TEST_ONLY",
    "SOURCE_UNAVAILABLE",
    "UNSUPPORTED",
    "REJECTED",
    "POLICY_CONFLICT",
    "RESOLUTION_INSUFFICIENT",
    "RESOURCE_EXCEEDED",
]
PolicyV2Stage = Literal[
    "PARSE",
    "IDENTITY",
    "SOURCE",
    "NRE",
    "MBA",
    "RULE",
    "COVERAGE",
    "JOINT",
    "CONSUMER",
]
PolicyV2Reason = Literal[
    "SOURCE_MISSING",
    "GOAL_SOURCE_UNAVAILABLE",
    "PRECISION_UNAUTHORIZED",
    "SOURCE_MALFORMED",
    "SOURCE_IDENTITY_MISMATCH",
    "SOURCE_UNAUTHORIZED",
    "SOURCE_WITHDRAWN",
    "NRE_INCONSISTENT",
    "MBA_INCONSISTENT",
    "NRE_UNAVAILABLE",
    "MBA_UNAVAILABLE",
    "PERIOD_COVERAGE_MISSING",
    "ANCHOR_COVERAGE_MISSING",
    "CLAIM_COVERAGE_MISSING",
    "DAILY_PROTECTION_MISSING",
    "MBA_NOT_APPLICABLE",
    "MEANING_MISMATCH",
    "UNIT_OR_SCOPE_MISMATCH",
    "UNSUPPORTED_TEMPORAL_MAP",
    "PRECISION_IDENTITY_MISMATCH",
    "SOURCE_CUT_INCOHERENT",
    "REQUIREMENT_COVERAGE_MISSING",
    "JOINT_WITNESS_MISMATCH",
    "GAP_SUBSTITUTION",
    "HARD_CONTAINMENT_FAILED",
    "GOAL_DIRECTION_CONFLICT",
    "PRECISION_NESTING_FAILED",
    "PROTECTED_INTERVAL_CONFLICT",
    "NO_PROTECTED_JOINT_WITNESS",
    "NO_JOINT_COMFORT_SUPPORT",
    "RESOURCE_LIMIT",
    "ORIGIN_NOT_ESTABLISHED",
    "REGISTRY_CHANGED",
    "CAPTURE_EXPIRED",
    "CONSUME_REPLAY",
    "REPORT_NOT_AUTHORITY",
    "ENVIRONMENT_MISMATCH",
    "PRODUCTION_GATE_CLOSED",
    "CAPTURE_FAILED",
    "HOST_TIMEOUT",
    "POLICY_SEMANTICS_INCONSISTENT",
]


def policy_v2_hash(kind, body):
    structure(body, 48 * 1024 * 1024)
    return identity_hash(
        {"domain": "nutrition-policy-integration." + kind + ".v2", "body": canonical(body)}
    )


class _V2(Contract):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")
    environment: Literal["TEST_ONLY"]

    @model_validator(mode="before")
    @classmethod
    def bounded(cls, value):
        return canonical(ingest(value, 48 * 1024 * 1024))

    @field_validator("planner_ready", "activation_ready", mode="before", check_fields=False)
    @classmethod
    def false_only(cls, value):
        if type(value) is not bool or value:
            raise ValueError("Exact false flag required")
        return value


class PolicyIntegrationIdentityV2(_V2):
    subject: HouseholdMemberIdentity
    actor_user_id: UUID
    root_request: n.NutritionRootRequest
    root_source_fingerprint: Sha256
    root_result_fingerprint: Sha256
    rule_selection: s.NutritionSynthesisSelection
    rule_case_id: Identifier
    requirement_fingerprint: Sha256
    nre_scope_fingerprint: Sha256
    precision: s.NutritionPrecisionSelection
    precision_witness: n.NutritionSubjectWitness
    horizon: n.NutritionTemporalScope
    calendar_cells: tuple[n.NutritionTemporalScope, ...] = Field(min_length=1, max_length=64)
    nre_source_fingerprint: Sha256
    nre_result_fingerprint: Sha256
    anchor_manifest_fingerprint: Sha256
    original_meaning_manifest_fingerprint: Sha256
    registry_id: Identifier
    registry_revision: Annotated[int, Field(strict=True, gt=0)]
    issuer_epoch: Identifier
    deployment: Identifier
    database_oid: n.NrcOid
    database_name: Identifier
    basis_source_fingerprint: Sha256


class NutritionPolicyIntegrationInputV2(_V2):
    contract_version: Literal["nutrition-policy-integration-input.v2"]
    profile: Literal["PIV2_SAME_MEANING_EXACT_PERIOD_SUM_V1"]
    basis_sources: b.BasisApplicabilitySourcesV1
    identity: PolicyIntegrationIdentityV2
    source_fingerprint: Sha256


class PolicyClaimCoverageV2(_V2):
    anchor_key: Identifier
    anchor_fingerprint: Sha256
    root_key: Identifier
    operation_id: Identifier | None
    descriptor: n.NutritionRootDescriptor
    layer: Literal[
        "GUIDELINE_HARD",
        "REFERENCE_CENTER",
        "GOAL_PROTECTION",
        "DAILY_PROTECTION",
        "COMFORT",
        "WEEKLY_GOAL",
        "WEEKLY_CENTER",
    ]
    disposition: Literal["RETAINED_ROOT", "ACTIVE_CLAIM", "UNSELECTED_PRECISION_BRANCH"]
    claim_id: Identifier | None
    meaning_fingerprint: Sha256
    basis_witness_fingerprint: Sha256


class PolicyAssignmentEvaluationV2(_V2):
    assignment_fingerprint: Sha256
    configuration_ids: tuple[Sha256, ...] = Field(min_length=1, max_length=14)
    period_vector_fingerprints: tuple[Sha256, ...] = Field(min_length=1, max_length=32)
    hard_violations: tuple[Identifier, ...] = Field(max_length=256)
    comfort_violations: tuple[Identifier, ...] = Field(max_length=256)


class PolicyCenterDeltaV2(_V2):
    assignment_fingerprint: Sha256
    claim_id: Identifier
    descriptor: n.NutritionRootDescriptor
    amount_minus_center: NreDelta


class JointPolicySupportV2(_V2):
    slot_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=14)
    assignments: tuple[PolicyAssignmentEvaluationV2, ...] = Field(min_length=1, max_length=16384)
    protected_assignment_ids: tuple[Sha256, ...] = Field(min_length=1, max_length=16384)
    comfort_assignment_ids: tuple[Sha256, ...] = Field(min_length=1, max_length=16384)
    representative_comfort_assignment_id: Sha256
    center_deltas: tuple[PolicyCenterDeltaV2, ...] = Field(max_length=65536)
    support_fingerprint: Sha256


class NutritionPolicyBodyV2(_V2):
    retained_roots: tuple[n.NutritionResolvedRoot, ...] = Field(min_length=1, max_length=16)
    claims: tuple[s.NutritionPolicyClaim, ...] = Field(min_length=1, max_length=256)
    trace: tuple[s.NutritionPolicyTrace, ...] = Field(min_length=1, max_length=256)
    coverage: tuple[PolicyClaimCoverageV2, ...] = Field(min_length=1, max_length=128)
    requirements: s.NutritionPolicyRequirementSpec
    reconstructed_basis_result: b.BasisApplicabilityResultV1
    support: JointPolicySupportV2


class PolicyDiagnosticV2(_V2):
    stage: PolicyV2Stage
    code: PolicyV2Reason
    subject_path: Identifier | None
    child_outcome: b.BasisOutcome | None
    child_reason: Identifier | None
    hard_support: Literal["NOT_EVALUATED", "ABSENT_IN_DECLARED_UNIVERSE", "PRESENT"]
    soft_support: Literal["NOT_EVALUATED", "SOFT_UNSUPPORTED", "PRESENT"]


class NutritionPolicyResultV2(_V2):
    contract_version: Literal["nutrition-policy.v2"]
    input_fingerprint: Sha256
    identity_fingerprint: Sha256
    outcome: PolicyV2Outcome
    diagnostics: tuple[PolicyDiagnosticV2, ...] = Field(max_length=64)
    payload: NutritionPolicyBodyV2 | None
    result_fingerprint: Sha256
    validation_authority: Literal["UNVERIFIED_TRANSPORT"]
    scientific_correctness: Literal["NOT_CERTIFIED"]
    source_origin: Literal["NOT_PROVED_OFFLINE"]
    current_authorization: Literal["NOT_CLAIMED"]
    production_admission: Literal["CLOSED"]
    plan_validation: Literal["NOT_PERFORMED"]
    solver_infeasibility: Literal["NOT_PROVEN"]
    planner_ready: Literal[False]
    activation_ready: Literal[False]

    @model_validator(mode="after")
    def payload_iff_available(self):
        if (self.payload is not None) != (self.outcome == "AVAILABLE_TEST_ONLY"):
            raise ValueError("Only complete AVAILABLE_TEST_ONLY exposes numerical payload")
        return self


class NutritionPolicyCheckV2(_V2):
    contract_version: Literal["nutrition-policy-check.v2"]
    coverage: Literal["FULL_V2_SOURCE_JOINT_POLICY_CONTAINMENT"]
    decision: Literal["CONSISTENT", "INCONSISTENT"]
    reconstructed_outcome: PolicyV2Outcome | None
    numerical_use: Literal["AVAILABLE_RETAINED_ONLY", "NOT_ADMITTED"]
    findings: tuple[PolicyV2Reason, ...] = Field(max_length=64)
    input_fingerprint: Sha256 | None
    reconstructed_result_fingerprint: Sha256 | None
    validation_authority: Literal["UNVERIFIED_TRANSPORT"]
    source_origin: Literal["NOT_PROVED_OFFLINE"]
    current_authorization: Literal["NOT_CLAIMED"]
    scientific_correctness: Literal["NOT_CERTIFIED"]
    production_admission: Literal["CLOSED"]
    planner_ready: Literal[False]
    activation_ready: Literal[False]


class NutritionPolicyHandoffV2(_V2):
    contract_version: Literal["nutrition-policy-handoff.v2"]
    input: NutritionPolicyIntegrationInputV2
    result: NutritionPolicyResultV2
    retained_check: NutritionPolicyCheckV2 | None
    validation_authority: Literal["UNVERIFIED_TRANSPORT"]
    production_admission: Literal["CLOSED"]
    planner_ready: Literal[False]
    activation_ready: Literal[False]


class PolicyV2Use(_V2):
    purpose: Literal["STRUCTURAL_TEST_ONLY_INSPECTION"]
    subject: HouseholdMemberIdentity
    actor_user_id: UUID
    selector_fingerprint: Sha256
    precision_fingerprint: Sha256


class PolicyV2CaptureFailure(_V2):
    contract_version: Literal["nutrition-policy-capture-failure.v2"]
    outcome: Literal["CAPTURE_REJECTED", "ADMISSION_REJECTED", "RESOURCE_EXCEEDED"]
    diagnostics: tuple[PolicyDiagnosticV2, ...] = Field(min_length=1, max_length=64)
    input_fingerprint: Sha256 | None
    production_admission: Literal["CLOSED"]
    planner_ready: Literal[False]
    activation_ready: Literal[False]


def parse_policy_v2(value, model, limit=32 * 1024 * 1024):
    return model.model_validate(ingest(value, limit))
