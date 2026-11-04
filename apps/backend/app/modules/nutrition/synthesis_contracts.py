"""Additive immutable synthesis transport; publication and scientific authority are distinct."""

from math import gcd
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StrictBool, model_validator

from app.domain.contracts import AwareTime, Identifier, Sha256
from app.modules.nutrition import root_contracts as n

SynthesisCapability = Literal[
    "SYNTHESIS_RULE_REVIEW",
    "SYNTHESIS_RULE_PUBLISH",
    "SYNTHESIS_RULE_WITHDRAW",
    "SYNTHESIS_SOURCE_READ",
    "SYNTHESIS_VALIDATOR_READ",
]
SynthesisPrecision = Literal["RELAXED", "STANDARD", "PRECISION"]
SynthesisRecordedOrder = Annotated[int, Field(strict=True, gt=0, le=9_223_372_036_854_775_807)]
SynthesisLayer = Literal[
    "GOAL_PROTECTION", "DAILY_PROTECTION", "COMFORT", "WEEKLY_GOAL", "WEEKLY_CENTER"
]


class SynthesisRational(n._NutritionRootTransport):
    numerator: Annotated[int, Field(strict=True, ge=-(2**127 - 1), le=2**127 - 1)]
    denominator: Annotated[int, Field(strict=True, gt=0, le=2**127 - 1)]

    @model_validator(mode="after")
    def reduced(self):
        if gcd(self.numerator, self.denominator) != 1:
            raise ValueError("Canonical reduced rational required")
        return self


class NutritionRuleApplicability(n._NutritionRootTransport):
    root_provider_id: UUID
    root_family_id: Identifier
    guideline_revision_id: UUID
    guideline_body_fingerprint: Sha256
    protocol_fingerprint: Sha256
    scope_id: Identifier
    scope_version: Identifier
    temporal: n.NutritionTemporalScope


class NutritionSynthesisOperation(n._NutritionRootTransport):
    """Closed instruction record. Inapplicable fields must be explicitly null/empty."""

    id: Identifier
    kind: Literal[
        "COPY_REFERENCE",
        "AFFINE_SAME_UNIT",
        "MAKE_CONSTRAINT",
        "CHECK_SUBSET",
        "FINITE_PERIOD_SUM",
        "REVIEWED_PERIOD_PROJECTION",
        "CHECK_DIRECTION",
        "SELECT_PRECISION_CASE",
    ]
    inputs: tuple[Identifier, ...] = Field(max_length=64)
    root_key: Identifier | None
    endpoint: Literal["lower", "upper", "center"] | None
    reference_role: Identifier | None
    coefficient: SynthesisRational | None
    offset: SynthesisRational | None
    constraint_kind: Literal["RANGE", "MINIMUM", "MAXIMUM", "TARGET"] | None
    layer: SynthesisLayer | None
    temporal: n.NutritionTemporalScope | None
    coefficients: tuple[SynthesisRational, ...] = Field(max_length=64)
    comparator: Literal["UPPER_LT", "UPPER_LE", "LOWER_GT", "LOWER_GE", "CONTAINS"] | None
    evidence_id: Identifier

    @model_validator(mode="after")
    def shape(self):
        allowed = {
            "COPY_REFERENCE": {"root_key", "endpoint", "reference_role"},
            "AFFINE_SAME_UNIT": {"coefficient", "offset"},
            "MAKE_CONSTRAINT": {"root_key", "constraint_kind", "layer", "temporal"},
            "CHECK_SUBSET": set(),
            "FINITE_PERIOD_SUM": {"coefficients", "temporal"},
            "REVIEWED_PERIOD_PROJECTION": {"coefficient", "offset", "temporal"},
            "CHECK_DIRECTION": {"comparator"},
            "SELECT_PRECISION_CASE": set(),
        }[self.kind]
        for field in (
            "root_key",
            "endpoint",
            "reference_role",
            "coefficient",
            "offset",
            "constraint_kind",
            "layer",
            "temporal",
            "comparator",
        ):
            if (getattr(self, field) is not None) != (field in allowed):
                raise ValueError("Instruction field shape differs: " + field)
        sizes = {
            "COPY_REFERENCE": (0,),
            "AFFINE_SAME_UNIT": (1,),
            "MAKE_CONSTRAINT": (1, 2),
            "CHECK_SUBSET": (2,),
            "FINITE_PERIOD_SUM": tuple(range(1, 65)),
            "REVIEWED_PERIOD_PROJECTION": (1,),
            "CHECK_DIRECTION": (2,),
            "SELECT_PRECISION_CASE": (3,),
        }
        if len(self.inputs) not in sizes[self.kind]:
            raise ValueError("Instruction operand arity differs")
        if self.kind == "FINITE_PERIOD_SUM":
            if len(self.coefficients) != len(self.inputs) or any(
                x.numerator <= 0 for x in self.coefficients
            ):
                raise ValueError("Explicit positive period coefficients required")
        elif self.coefficients:
            raise ValueError("Unexpected coefficients")
        if self.kind == "MAKE_CONSTRAINT" and len(self.inputs) != (
            2 if self.constraint_kind == "RANGE" else 1
        ):
            raise ValueError("Constraint operand arity differs")
        if self.kind == "MAKE_CONSTRAINT":
            if (self.constraint_kind == "TARGET") != (self.layer == "WEEKLY_CENTER"):
                raise ValueError("TARGET is a soft reference center only")
            if self.layer == "COMFORT" and self.constraint_kind != "RANGE":
                raise ValueError("Comfort requires an explicitly bounded band")
        return self


class NutritionRuleCase(n._NutritionRootTransport):
    id: Identifier
    direction: Literal["CUT", "MAINTAIN", "GAIN"]
    operations: tuple[NutritionSynthesisOperation, ...] = Field(min_length=1, max_length=256)
    required_claims: tuple[Identifier, ...] = Field(min_length=1, max_length=64)
    daily_root_keys: tuple[Identifier, ...] = Field(min_length=1, max_length=16)
    comfort_root_keys: tuple[Identifier, ...] = Field(min_length=1, max_length=16)
    weekly: Literal["REQUIRED", "NOT_APPLICABLE"]

    @model_validator(mode="after")
    def finite(self):
        seen = set()
        types = {}
        for op in self.operations:
            if op.id in seen or any(ref not in seen for ref in op.inputs):
                raise ValueError("Duplicate, forward or recursive instruction reference")
            required = {
                "COPY_REFERENCE": (),
                "AFFINE_SAME_UNIT": ("NUMBER",),
                "MAKE_CONSTRAINT": ("NUMBER",) * len(op.inputs),
                "CHECK_SUBSET": ("CONSTRAINT", "CONSTRAINT"),
                "FINITE_PERIOD_SUM": ("NUMBER",) * len(op.inputs),
                "REVIEWED_PERIOD_PROJECTION": ("NUMBER",),
                "CHECK_DIRECTION": ("CONSTRAINT", "NUMBER"),
                "SELECT_PRECISION_CASE": ("CONSTRAINT",) * 3,
            }[op.kind]
            if tuple(types[ref] for ref in op.inputs) != required:
                raise ValueError("Finite instruction operand type differs")
            types[op.id] = (
                "BOOLEAN"
                if op.kind in {"CHECK_SUBSET", "CHECK_DIRECTION"}
                else "CONSTRAINT"
                if op.kind in {"MAKE_CONSTRAINT", "SELECT_PRECISION_CASE"}
                else "NUMBER"
            )
            seen.add(op.id)
        if (
            len(set(self.required_claims)) != len(self.required_claims)
            or not set(self.required_claims) <= seen
        ):
            raise ValueError("Exact required claim IDs required")
        if any(types[key] != "CONSTRAINT" for key in self.required_claims):
            raise ValueError("Required claim must refer to a constraint, not a scalar or predicate")
        for keys in (self.daily_root_keys, self.comfort_root_keys):
            if tuple(sorted(set(keys))) != keys:
                raise ValueError("Canonical complete metric manifest required")
        return self


class NutritionSynthesisRuleBody(n._NutritionRootTransport):
    contract_version: Literal["nutrition-synthesis-rule.v1"] = "nutrition-synthesis-rule.v1"
    revision_id: UUID
    provider_id: UUID
    family_id: Identifier
    authored_version: Identifier
    language_version: Literal["FINITE_EXACT_V1"]
    purpose: Literal["BOUNDED_COMPLETE_POLICY_V1"]
    environment: n.NrcEnvironment
    effective: n.NutritionSourceInterval
    applicability: NutritionRuleApplicability
    evidence: tuple[n.NutritionSourceEvidence, ...] = Field(min_length=1, max_length=32)
    calendar_evidence_id: Identifier
    calendar_cells: tuple[n.NutritionTemporalScope, ...] = Field(min_length=1, max_length=64)
    cases: tuple[NutritionRuleCase, ...] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def bindings(self):
        ids = tuple(e.evidence_id for e in self.evidence)
        if ids != tuple(sorted(set(ids))) or any(
            e.environment != self.environment for e in self.evidence
        ):
            raise ValueError("Exact evidence identity/environment required")
        if self.calendar_evidence_id not in ids:
            raise ValueError("Calendar evidence missing")
        if any(op.evidence_id not in ids for case in self.cases for op in case.operations):
            raise ValueError("Instruction evidence missing")
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError("Duplicate case identity")
        return self


class NutritionSynthesisProviderEnrollment(n._NutritionRootTransport):
    provider_id: UUID
    code: Identifier
    version: Identifier
    remit: n.NrcText
    environment: n.NrcEnvironment
    evidence: n.NutritionSourceEvidence
    expected_generation: n.NrcCounter
    predecessor_id: UUID | None
    idempotency_key: Identifier


class NutritionSynthesisPrincipalEnrollment(n._NutritionRootTransport):
    role_name: n.NrcName
    verified_human_id: UUID | None
    user_id: UUID | None
    service_id: Identifier | None
    evidence: n.NutritionSourceEvidence
    idempotency_key: Identifier
    expected_generation: n.NrcCounter = 0
    previous_enrollment_id: UUID | None = None

    @model_validator(mode="after")
    def principal_class(self):
        if (self.verified_human_id is None) == (self.service_id is None) or (
            self.service_id is not None and self.user_id is not None
        ):
            raise ValueError("Exact human or service identity required")
        return self


class NutritionSynthesisGrant(n._NutritionRootTransport):
    provider_id: UUID
    family_id: Identifier
    principal_id: UUID
    capability: SynthesisCapability
    action: Literal["GRANT", "REVOKE"]
    applicability: NutritionRuleApplicability
    effective: n.NutritionSourceInterval
    evidence: n.NutritionSourceEvidence
    expected_generation: n.NrcCounter
    predecessor_id: UUID | None
    idempotency_key: Identifier


class NutritionSynthesisDraft(n._NutritionRootTransport):
    kind: Literal["DRAFT"]
    rule: NutritionSynthesisRuleBody


class NutritionSynthesisReview(n._NutritionRootTransport):
    kind: Literal["REVIEW"]
    revision_id: UUID
    body_fingerprint: Sha256
    evidence_fingerprint: Sha256
    decision: Literal["APPROVE", "CANCEL"]
    prior_review_id: UUID | None


class NutritionSynthesisPublication(n._NutritionRootTransport):
    kind: Literal["PUBLICATION"]
    revision_id: UUID
    body_fingerprint: Sha256
    action: Literal["PUBLISH", "SUPERSEDE", "RETIRE", "RETRACT"]
    review_id: UUID | None
    predecessor_publication_id: UUID | None
    effective_at: AwareTime

    @model_validator(mode="after")
    def explicit_lifecycle(self):
        if (self.action == "PUBLISH") != (self.predecessor_publication_id is None):
            raise ValueError("Exact publication predecessor required")
        if (self.action in {"PUBLISH", "SUPERSEDE"}) != (self.review_id is not None):
            raise ValueError("Exact review for publication; withdrawal carries no review")
        return self


class NutritionSynthesisCommand(n._NutritionRootTransport):
    provider_id: UUID
    family_id: Identifier
    event_id: UUID
    expected_revision: n.NrcCounter
    predecessor_id: UUID | None
    idempotency_key: Identifier
    body: Annotated[
        NutritionSynthesisDraft | NutritionSynthesisReview | NutritionSynthesisPublication,
        Field(discriminator="kind"),
    ]


class NutritionSynthesisRecorded(n._NutritionRootTransport):
    id: UUID
    command: NutritionSynthesisCommand
    principal_id: UUID
    grant_id: UUID
    session: n.NutritionSourceSession
    sequence: n.NrcCounter
    previous_hash: Sha256 | None
    recorded_at: AwareTime
    recorded_order: SynthesisRecordedOrder
    command_hash: Sha256
    event_hash: Sha256


class NutritionPrecisionSelection(n._NutritionRootTransport):
    value: SynthesisPrecision
    source: Literal["REQUEST_EXPLICIT"]
    version: Identifier
    actor_user_id: UUID
    subject: n.HouseholdMemberIdentity
    evidence: n.NutritionSourceEvidence


class NutritionSynthesisSelection(n._NutritionRootTransport):
    provider_id: UUID
    family_id: Identifier
    revision_id: UUID
    publication_id: UUID
    body_fingerprint: Sha256
    evidence_fingerprint: Sha256
    selection_version: Literal["EXACT_SINGLE_CASE_V1"]
    language_version: Literal["FINITE_EXACT_V1"]


class NutritionSynthesisRequest(n._NutritionRootTransport):
    root: n.NutritionRootContract
    selection: NutritionSynthesisSelection
    precision: NutritionPrecisionSelection | None
    purpose: Literal["BOUNDED_COMPLETE_POLICY_V1"]
    required_claims: tuple[Identifier, ...] = Field(max_length=64)


class NutritionSynthesisCaptureCommand(n._NutritionRootTransport):
    root_request: n.NutritionRootRequest
    root_frame: n.NutritionCaptureFrame
    selection: NutritionSynthesisSelection
    precision: NutritionPrecisionSelection | None


class NutritionSynthesisProviderFact(n._NutritionRootTransport):
    id: UUID
    command: NutritionSynthesisProviderEnrollment
    generation: n.NrcCounter
    administrator: n.NutritionSourceSession
    recorded_at: AwareTime
    recorded_order: SynthesisRecordedOrder
    command_hash: Sha256


class NutritionSynthesisPrincipalFact(n._NutritionRootTransport):
    id: UUID
    command: NutritionSynthesisPrincipalEnrollment
    database_oid: n.NrcOid
    database_name: n.NrcName
    role_oid: n.NrcOid
    enrollment_root_id: UUID
    generation: SynthesisRecordedOrder
    administrator: n.NutritionSourceSession
    recorded_at: AwareTime
    recorded_order: SynthesisRecordedOrder
    command_hash: Sha256


class NutritionSynthesisGrantFact(n._NutritionRootTransport):
    id: UUID
    command: NutritionSynthesisGrant
    generation: n.NrcCounter
    administrator: n.NutritionSourceSession
    recorded_at: AwareTime
    recorded_order: SynthesisRecordedOrder
    command_hash: Sha256


class NutritionSynthesisAuthorityFrontier(n._NutritionRootTransport):
    principal_id: UUID
    capability: SynthesisCapability
    revision: n.NrcCounter
    head_id: UUID | None
    head_hash: Sha256 | None


class NutritionSynthesisPrincipalFrontier(n._NutritionRootTransport):
    enrollment_root_id: UUID
    revision: SynthesisRecordedOrder
    head_id: UUID
    head_hash: Sha256


class NutritionSynthesisSourceSnapshot(n._NutritionRootTransport):
    contract_version: Literal["nutrition-synthesis-sources.v1"] = "nutrition-synthesis-sources.v1"
    request: NutritionSynthesisRequest
    provider_facts: tuple[NutritionSynthesisProviderFact, ...] = Field(max_length=64)
    principal_facts: tuple[NutritionSynthesisPrincipalFact, ...] = Field(max_length=512)
    principal_frontiers: tuple[NutritionSynthesisPrincipalFrontier, ...] = Field(max_length=512)
    grant_facts: tuple[NutritionSynthesisGrantFact, ...] = Field(max_length=4096)
    authority_frontiers: tuple[NutritionSynthesisAuthorityFrontier, ...] = Field(max_length=2560)
    records: tuple[NutritionSynthesisRecorded, ...] = Field(max_length=64)
    frame: n.NutritionCaptureFrame
    frontier_revision: n.NrcCounter
    frontier_id: UUID | None
    frontier_hash: Sha256 | None
    precision_witness: n.NutritionSubjectWitness | None
    source_fingerprint: Sha256


class NutritionResolutionRequirement(n._NutritionRootTransport):
    root_key: Identifier
    descriptor: n.NutritionRootDescriptor


class NutritionPolicyRequirementSpec(n._NutritionRootTransport):
    subject: n.HouseholdMemberIdentity
    root_fingerprint: Sha256
    rule_body_fingerprint: Sha256
    case_id: Identifier
    temporal: n.NutritionTemporalScope
    root_keys: tuple[Identifier, ...]
    measurements: tuple[NutritionResolutionRequirement, ...] = Field(min_length=1, max_length=64)
    environment: n.NrcEnvironment
    fingerprint: Sha256


class NutritionResolutionFact(n._NutritionRootTransport):
    root_key: Identifier
    descriptor: n.NutritionRootDescriptor
    # Finite TEST_ONLY interface fixture preimages; no estimator is implemented.
    candidate_id: Identifier
    recipe_version_id: UUID
    portion_step: n.NutritionRootAmount
    discrete_unit: Identifier
    ingredient_amounts: tuple[n.NutritionRootAmount, ...] = Field(min_length=1, max_length=32)
    source_nutrients: tuple[n.NutritionRootAmount, ...] = Field(min_length=1, max_length=32)
    expected_step: n.NutritionRootAmount
    primitive_fingerprint: Sha256


class NutritionResolutionInput(n._NutritionRootTransport):
    requirements_fingerprint: Sha256
    pool_fingerprint: Sha256
    complete_pool: Literal[True]
    estimator_version: Identifier
    environment: n.NrcEnvironment
    evidence: n.NutritionSourceEvidence
    availability: Literal["AVAILABLE", "UNAVAILABLE", "INSUFFICIENT"]
    facts: tuple[NutritionResolutionFact, ...] = Field(max_length=1024)


class NutritionPolicyClaim(n._NutritionRootTransport):
    id: Identifier
    subject: n.HouseholdMemberIdentity
    root_key: Identifier
    descriptor: n.NutritionRootDescriptor
    layer: SynthesisLayer
    constraint: n.NutritionRootConstraint
    rule_revision_id: UUID
    evidence_id: Identifier


class NutritionPolicyTrace(n._NutritionRootTransport):
    operation_id: Identifier
    descriptor: n.NutritionRootDescriptor | None
    amount: SynthesisRational | None
    claim: NutritionPolicyClaim | None
    passed: StrictBool | None


class NutritionPolicy(n._NutritionRootTransport):
    contract_version: Literal["nutrition-policy.v1"] = "nutrition-policy.v1"
    inputs: NutritionSynthesisSourceSnapshot
    resolution: NutritionResolutionInput | None
    outcome: Literal["AVAILABLE", "UNAVAILABLE", "UNSUPPORTED", "CONFLICT"]
    environment: n.NrcEnvironment
    hard_roots: tuple[n.NutritionResolvedRoot, ...]
    claims: tuple[NutritionPolicyClaim, ...]
    trace: tuple[NutritionPolicyTrace, ...]
    reasons: tuple[Identifier, ...]
    requirements: NutritionPolicyRequirementSpec | None
    result_fingerprint: Sha256
    scientific_correctness: Literal["NOT_CERTIFIED"] = "NOT_CERTIFIED"
    canonical_database_origin: Literal["NOT_PROVED_OFFLINE"] = "NOT_PROVED_OFFLINE"
    current_authorization: Literal["NOT_CLAIMED"] = "NOT_CLAIMED"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False


class NutritionPolicyValidationInput(n._NutritionRootTransport):
    coverage: Literal["SYNTHESIS_SOURCE_AND_POLICY_SEMANTICS"]
    policy: NutritionPolicy


class NutritionPolicyValidationReport(n._NutritionRootTransport):
    decision: Literal["CONSISTENT", "INCONSISTENT", "UNSUPPORTED"]
    coverage: Literal["SYNTHESIS_SOURCE_AND_POLICY_SEMANTICS"]
    findings: tuple[Identifier, ...]
    policy_fingerprint: Sha256
    source_fingerprint: Sha256
    scientific_correctness: Literal["NOT_CERTIFIED"] = "NOT_CERTIFIED"
    canonical_database_origin: Literal["NOT_PROVED_OFFLINE"] = "NOT_PROVED_OFFLINE"
    current_authorization: Literal["NOT_CLAIMED"] = "NOT_CLAIMED"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False


class NutritionPolicyReference(n._NutritionRootTransport):
    """Pinned handoff only; no MTR-008 precedence or ResolvedPlanPolicy is synthesized."""

    policy: NutritionPolicy
    validation: NutritionPolicyValidationReport
    environment: n.NrcEnvironment
    precision: NutritionPrecisionSelection
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False
