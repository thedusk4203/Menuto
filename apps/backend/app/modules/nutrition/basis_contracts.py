"""Additive TEST_ONLY measurement meaning. No numerical transformation or authority token."""

from typing import Annotated, Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, Sha256
from app.domain.feature_identity import canonical, identity_hash
from app.modules.households.contracts import HouseholdMemberIdentity
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition.resolution_contracts import (
    NutritionResolutionHandoffV2,
    NutritionResolutionScopeRequestV1,
)
from app.modules.nutrition.resolution_limits import ingest, structure

BasisOutcome = Literal[
    "APPLICABLE_TEST_ONLY",
    "NOT_APPLICABLE",
    "UNAVAILABLE",
    "UNSUPPORTED",
    "REJECTED",
    "RESOURCE_EXCEEDED",
]
BasisCapability = Literal[
    "TEST_BASIS_REVIEW",
    "TEST_BASIS_PUBLISH",
    "TEST_BASIS_WITHDRAW",
    "TEST_BASIS_SOURCE_READ",
]


def basis_hash(kind, body):
    structure(body, 32 * 1024 * 1024)
    return identity_hash({"domain": "measurement-basis." + kind + ".v1", "body": canonical(body)})


class BasisTransport(Contract):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")

    @model_validator(mode="before")
    @classmethod
    def exact(cls, value):
        value = ingest(value, 32 * 1024 * 1024)
        if isinstance(value, dict) and "artifact" in value:
            structure(value["artifact"], 2 * 1024 * 1024)
        return canonical(value)

    @field_validator("planner_ready", "activation_ready", mode="before", check_fields=False)
    @classmethod
    def exact_flags(cls, value):
        if type(value) is not bool:
            raise ValueError("Exact false readiness flags required")
        return value


class MeasurementMeaningV1(BasisTransport):
    vocabulary: Literal["measurement-meaning.v1"] = "measurement-meaning.v1"
    meaning: Literal[
        "PLANNED_INGREDIENT_INPUT_V1",
        "PLANNED_OFFERED_FOOD_V1",
        "OBSERVED_OFFERED_FOOD_V1",
        "OBSERVED_CONSUMED_FOOD_V1",
        "PHYSIOLOGICAL_INTAKE_V1",
        "UNSPECIFIED_V1",
    ]
    interpretation_id: Identifier
    interpretation_version: Identifier
    estimator_version: Literal["EXACT_FINITE_RESOLUTION_V1"] = "EXACT_FINITE_RESOLUTION_V1"
    nre_contract: Literal["nutrition-resolution-handoff.v2"] = "nutrition-resolution-handoff.v2"
    material_bases: tuple[Literal["EP_RAW_G", "COOKED_G"], ...] = Field(min_length=1, max_length=2)
    descriptor: n.NutritionRootDescriptor
    environment: Literal["TEST_ONLY"] = "TEST_ONLY"


class BasisClaimAnchorV1(BasisTransport):
    key: Identifier
    layer: Literal[
        "GUIDELINE_HARD",
        "REFERENCE_CENTER",
        "GOAL_PROTECTION",
        "DAILY_PROTECTION",
        "COMFORT",
        "WEEKLY_GOAL",
        "WEEKLY_CENTER",
    ]
    root_key: Identifier
    descriptor: n.NutritionRootDescriptor
    subject: HouseholdMemberIdentity
    original_source_fingerprint: Sha256
    evidence_fingerprint: Sha256
    meaning_preimage: str | None = Field(max_length=16384)
    stable_scope_fingerprint: Sha256
    root_fingerprint: Sha256
    requirement_fingerprint: Sha256
    nre_source_fingerprint: Sha256
    nre_result_fingerprint: Sha256
    anchor_fingerprint: Sha256


class BasisAssertionV1(BasisTransport):
    id: Identifier
    revision: Identifier
    subject: HouseholdMemberIdentity
    scope_id: Identifier
    scope_version: Identifier
    protocol_fingerprint: Sha256
    stable_scope_fingerprint: Sha256
    original_sources: tuple[Sha256, ...] = Field(min_length=1, max_length=128)
    original_evidence: tuple[Sha256, ...] = Field(min_length=1, max_length=128)
    required_keys: tuple[Identifier, ...] = Field(min_length=1, max_length=128)
    meanings: tuple[MeasurementMeaningV1, ...] = Field(min_length=1, max_length=128)
    material_reference_fingerprint: Sha256
    effective: n.NutritionSourceInterval
    environment: Literal["TEST_ONLY"] = "TEST_ONLY"


class BasisFixtureEventV1(BasisTransport):
    id: Identifier
    sequence: Annotated[int, Field(strict=True, gt=0, le=256)]
    previous_hash: Sha256 | None
    recorded_at: AwareTime
    effective: n.NutritionSourceInterval
    kind: Literal[
        "ENROLL",
        "GRANT",
        "REVOKE",
        "QUALIFY",
        "DISQUALIFY",
        "REVIEW",
        "PUBLISH",
        "SUPERSEDE",
        "RETIRE",
        "WITHDRAW",
    ]
    principal: Identifier
    principal_subject: Identifier | None
    capability: BasisCapability | None
    scope: Identifier
    qualification: Literal["SYMBOLIC_TEST_ONLY_NOT_SCIENTIFIC"] | None
    assertion: BasisAssertionV1 | None
    assertion_fingerprint: Sha256 | None
    review_id: Identifier | None
    predecessor_publication_id: Identifier | None
    event_hash: Sha256


class BasisFixtureArtifactV1(BasisTransport):
    schema_version: Literal["test-only.basis-artifact.v1"] = "test-only.basis-artifact.v1"
    registry_id: Identifier
    revision: Annotated[int, Field(strict=True, gt=0)]
    previous_artifact_fingerprint: Sha256 | None
    deployment: Identifier
    database_oid: n.NrcOid
    database_name: Identifier
    issuer_epoch: Identifier
    events: tuple[BasisFixtureEventV1, ...] = Field(min_length=1, max_length=256)
    artifact_fingerprint: Sha256
    environment: Literal["TEST_ONLY"] = "TEST_ONLY"


class BasisSelectorsV1(BasisTransport):
    nre_scope: NutritionResolutionScopeRequestV1
    publication_id: Identifier
    assertion_id: Identifier
    assertion_revision: Identifier
    reader_principal: Identifier
    max_work: Annotated[int, Field(strict=True, gt=0, le=1000000)] = 1000000


class BasisCaptureFrameV1(BasisTransport):
    registry_id: Identifier
    registry_revision: Annotated[int, Field(strict=True, gt=0)]
    artifact_fingerprint: Sha256
    deployment: Identifier
    issuer_epoch: Identifier
    database_oid: n.NrcOid
    database_name: Identifier
    started_at: AwareTime
    completed_at: AwareTime
    registry_coherence: Literal["PINNED_BEFORE_AFTER_NOT_SHARED_MVCC"] = (
        "PINNED_BEFORE_AFTER_NOT_SHARED_MVCC"
    )
    origin: Literal["RETAINED_NOT_OFFLINE_PROOF"] = "RETAINED_NOT_OFFLINE_PROOF"


class BasisApplicabilitySourcesV1(BasisTransport):
    contract_version: Literal["basis-applicability-sources.v1"] = "basis-applicability-sources.v1"
    nre: NutritionResolutionHandoffV2
    artifact: BasisFixtureArtifactV1
    selectors: BasisSelectorsV1
    anchors: tuple[BasisClaimAnchorV1, ...] = Field(min_length=1, max_length=128)
    frame: BasisCaptureFrameV1
    absences: tuple[Identifier, ...] = Field(max_length=256)
    source_fingerprint: Sha256


class BasisComparisonWitnessV1(BasisTransport):
    anchor_fingerprint: Sha256
    period_fingerprint: Sha256
    component: Literal["ENERGY", "PROTEIN", "FAT", "CARBOHYDRATE"]
    assertion_fingerprint: Sha256
    original_meaning_fingerprint: Sha256
    relation: Literal["SAME_DECLARED_PLANNED_INPUT_MEANING_V1"] = (
        "SAME_DECLARED_PLANNED_INPUT_MEANING_V1"
    )


class BasisApplicabilityResultV1(BasisTransport):
    contract_version: Literal["basis-applicability-result.v1"] = "basis-applicability-result.v1"
    outcome: BasisOutcome
    reasons: tuple[Identifier, ...]
    required_anchor_fingerprints: tuple[Sha256, ...]
    witnesses: tuple[BasisComparisonWitnessV1, ...]
    source_fingerprint: Sha256
    result_fingerprint: Sha256
    environment: Literal["TEST_ONLY"] = "TEST_ONLY"
    scientific_correctness: Literal["NOT_CERTIFIED"] = "NOT_CERTIFIED"
    source_origin: Literal["NOT_PROVED_OFFLINE"] = "NOT_PROVED_OFFLINE"
    validation_authority: Literal["UNVERIFIED_TRANSPORT"] = "UNVERIFIED_TRANSPORT"
    current_authorization: Literal["NOT_CLAIMED"] = "NOT_CLAIMED"
    hard_policy_feasibility: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"
    policy_integration: Literal["NOT_AUTHORIZED"] = "NOT_AUTHORIZED"
    production_admission: Literal["CLOSED"] = "CLOSED"
    policy_synthesis: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    consumption: Literal["NOT_ASSERTED"] = "NOT_ASSERTED"
    solver_infeasibility: Literal["NOT_PROVEN"] = "NOT_PROVEN"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False

    @model_validator(mode="after")
    def complete_or_none(self):
        if self.outcome != "APPLICABLE_TEST_ONLY" and self.witnesses:
            raise ValueError("No partial positive witnesses")
        return self


class BasisApplicabilityCheckV1(BasisTransport):
    decision: Literal["CONSISTENT", "INCONSISTENT"]
    findings: tuple[Identifier, ...]
    reconstructed_result_fingerprint: Sha256 | None
    validation_authority: Literal["UNVERIFIED_TRANSPORT"] = "UNVERIFIED_TRANSPORT"
    source_origin: Literal["NOT_PROVED_OFFLINE"] = "NOT_PROVED_OFFLINE"
    scientific_correctness: Literal["NOT_CERTIFIED"] = "NOT_CERTIFIED"
    production_admission: Literal["CLOSED"] = "CLOSED"


class BasisApplicabilityHandoffV1(BasisTransport):
    sources: BasisApplicabilitySourcesV1
    result: BasisApplicabilityResultV1
    validation_authority: Literal["UNVERIFIED_TRANSPORT"] = "UNVERIFIED_TRANSPORT"
    policy_integration: Literal["NOT_AUTHORIZED"] = "NOT_AUTHORIZED"


def parse_basis(value, model, limit=32 * 1024 * 1024):
    """Limits precede canonicalization and recursive transport validation."""
    return model.model_validate(ingest(value, limit))
