"""Immutable Nutrition source transport. Shape and measurement algebra are not authority."""

from math import gcd
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, StrictBool, field_validator, model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, Sha256
from app.domain.feature_identity import canonical, identity_hash
from app.modules.households.contracts import HouseholdMemberIdentity
from app.modules.nutrition.root_limits import INTEGER_MAX, check_structure

NrcCounter = Annotated[int, Field(strict=True, ge=0, le=9_223_372_036_854_775_807)]
NrcOid = Annotated[int, Field(strict=True, gt=0, le=4_294_967_295)]
NrcText = Annotated[str, Field(min_length=1, max_length=4000, pattern=r"\S")]
NrcName = Annotated[str, Field(min_length=1, max_length=63, pattern=r"^[^\x00-\x1f\x7f]+$")]
NrcEnvironment = Literal["TEST_ONLY", "REVIEWED_PRODUCTION"]
NrcCapability = Literal[
    "GUIDELINE_REVIEW",
    "GUIDELINE_PUBLISH",
    "GUIDELINE_WITHDRAW",
    "ELIGIBILITY_ATTEST",
    "MEMBER_OBSERVATION_WRITE",
    "MEMBER_GOAL_WRITE",
    "ROOT_SOURCE_READ",
    "VALIDATOR_SOURCE_READ",
]
NrcFact = Literal["BODY_MASS", "HEIGHT"]


def nutrition_root_hash(domain, value):
    return identity_hash({"domain": domain, "value": canonical(value)})


class _NutritionRootTransport(Contract):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True, revalidate_instances="always"
    )

    @model_validator(mode="before")
    @classmethod
    def exact_primitives(cls, value):
        check_structure(value)
        return canonical(value)

    @field_validator(
        "read_only", "planner_ready", "activation_ready", mode="before", check_fields=False
    )
    @classmethod
    def exact_flags(cls, value):
        if type(value) is not bool:
            raise ValueError("Exact boolean required")
        return value


class NutritionSourceInterval(_NutritionRootTransport):
    start: AwareTime
    end: AwareTime

    @model_validator(mode="after")
    def nonempty(self):
        if self.start >= self.end:
            raise ValueError("Nonempty half-open interval required")
        return self


class NutritionRootAmount(_NutritionRootTransport):
    numerator: Annotated[int, Field(strict=True, ge=0, le=INTEGER_MAX)]
    denominator: Annotated[int, Field(strict=True, gt=0, le=INTEGER_MAX)]

    @model_validator(mode="after")
    def reduced(self):
        if gcd(self.numerator, self.denominator) != 1:
            raise ValueError("Canonical reduced exact rational required")
        return self


class NutritionRange(_NutritionRootTransport):
    kind: Literal["RANGE"]
    lower: NutritionRootAmount
    upper: NutritionRootAmount

    @model_validator(mode="after")
    def ordered(self):
        if self.lower.numerator * self.upper.denominator > (
            self.upper.numerator * self.lower.denominator
        ):
            raise ValueError("Range lower exceeds upper")
        return self


class NutritionMinimum(_NutritionRootTransport):
    kind: Literal["MINIMUM"]
    lower: NutritionRootAmount


class NutritionMaximum(_NutritionRootTransport):
    kind: Literal["MAXIMUM"]
    upper: NutritionRootAmount


class NutritionTarget(_NutritionRootTransport):
    kind: Literal["TARGET"]
    center: NutritionRootAmount


NutritionRootConstraint = Annotated[
    NutritionRange | NutritionMinimum | NutritionMaximum | NutritionTarget,
    Field(discriminator="kind"),
]


class NutritionSourceEvidence(_NutritionRootTransport):
    evidence_id: Identifier
    version: Identifier
    environment: NrcEnvironment
    purpose: NrcText
    body: Annotated[str, Field(min_length=1, max_length=16_384)]
    body_fingerprint: Sha256

    @model_validator(mode="after")
    def retained_body(self):
        if self.body_fingerprint != nutrition_root_hash("nutrition.evidence-body.v1", self.body):
            raise ValueError("Evidence body fingerprint differs")
        return self


class NutritionEvidenceRequirements(_NutritionRootTransport):
    observations: tuple[NrcFact, ...] = Field(max_length=2)
    evidence_slots: tuple[Identifier, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def canonical_sets(self):
        for values in (self.observations, self.evidence_slots):
            if tuple(sorted(set(values))) != values:
                raise ValueError("Unique sorted requirement keys required")
        return self


class NutritionEligibilityProtocol(_NutritionRootTransport):
    protocol_id: Identifier
    version: Identifier
    scope_id: Identifier
    scope_version: Identifier
    environment: NrcEnvironment
    meaning: NutritionSourceEvidence
    admitted: NutritionEvidenceRequirements
    excluded: NutritionEvidenceRequirements
    out_of_scope: NutritionEvidenceRequirements

    @model_validator(mode="after")
    def environment_binding(self):
        if self.meaning.environment != self.environment:
            raise ValueError("Protocol evidence environment differs")
        return self


class NutritionTemporalScope(_NutritionRootTransport):
    kind: Literal["EXACT_INTERVAL", "DAY", "WEEK"]
    period_id: Identifier
    calendar: Identifier
    timezone: Identifier
    interval: NutritionSourceInterval


class NutritionRootDescriptor(_NutritionRootTransport):
    metric: Literal["ENERGY", "PROTEIN", "FAT", "CARBOHYDRATE"]
    unit: Literal["KCAL", "G"]
    scope_id: Identifier
    scope_version: Identifier
    protocol_fingerprint: Sha256
    temporal: NutritionTemporalScope

    @model_validator(mode="after")
    def supported_pair(self):
        if (self.unit == "KCAL") != (self.metric == "ENERGY"):
            raise ValueError("Unsupported metric/unit pair; no conversion")
        return self


class NutritionGuidelineClause(_NutritionRootTransport):
    root_key: Identifier
    descriptor: NutritionRootDescriptor
    interpretation: Literal["GUIDELINE_HARD", "REFERENCE_CENTER"]
    constraint: NutritionRootConstraint

    @model_validator(mode="after")
    def target_is_not_hard(self):
        if (self.constraint.kind == "TARGET") != (self.interpretation == "REFERENCE_CENTER"):
            raise ValueError("TARGET is a reference center, never a hard interval")
        return self


class NutritionGuidelineBody(_NutritionRootTransport):
    contract_version: Literal["nutrition-guideline-body.v1"] = "nutrition-guideline-body.v1"
    revision_id: UUID
    provider_id: UUID
    family_id: Identifier
    guideline_id: Identifier
    guideline_version: Identifier
    edition: NrcText
    jurisdiction: NrcText | None
    jurisdiction_status: Literal["REVIEWED_SPECIFIED", "SOURCE_NOT_SPECIFIED"]
    environment: NrcEnvironment
    effective: NutritionSourceInterval
    protocol: NutritionEligibilityProtocol
    evidence_manifest: tuple[NutritionSourceEvidence, ...] = Field(min_length=1, max_length=32)
    clauses: tuple[NutritionGuidelineClause, ...] = Field(min_length=1, max_length=16)
    mandatory_hard_roots: tuple[Identifier, ...] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def complete_bundle_shape(self):
        if (self.jurisdiction is not None) != (self.jurisdiction_status == "REVIEWED_SPECIFIED"):
            raise ValueError("Explicit jurisdiction applicability required")
        if self.protocol.environment != self.environment or any(
            e.environment != self.environment for e in self.evidence_manifest
        ):
            raise ValueError("Reference environment mismatch")
        ids = tuple(e.evidence_id for e in self.evidence_manifest)
        if ids != tuple(sorted(set(ids))):
            raise ValueError("Unique sorted evidence identities required")
        keys = tuple(c.root_key for c in self.clauses)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("Unique sorted root keys required")
        hard = tuple(c.root_key for c in self.clauses if c.interpretation == "GUIDELINE_HARD")
        if self.mandatory_hard_roots != hard:
            raise ValueError("Complete nonempty hard-root manifest required")
        semantic_keys = []
        protocol_hash = nutrition_root_hash("nutrition.protocol.v1", self.protocol)
        for clause in self.clauses:
            d = clause.descriptor
            if (d.scope_id, d.scope_version, d.protocol_fingerprint) != (
                self.protocol.scope_id,
                self.protocol.scope_version,
                protocol_hash,
            ):
                raise ValueError("Clause applicability/protocol mismatch")
            if (
                not self.effective.start
                <= d.temporal.interval.start
                < (d.temporal.interval.end)
                <= self.effective.end
            ):
                raise ValueError("Clause outside guideline interval")
            key = (
                d.metric,
                nutrition_root_hash("nutrition.temporal.v1", d.temporal),
                clause.interpretation,
            )
            if key in semantic_keys:
                raise ValueError("Duplicate metric/temporal/role clause")
            semantic_keys.append(key)
        return self


class NutritionSourceSession(_NutritionRootTransport):
    database_oid: NrcOid
    database_name: NrcName
    role_oid: NrcOid
    role_name: NrcName
    authentication_method: Literal["scram-sha-256"]
    authenticated_identity: NrcName

    @model_validator(mode="after")
    def authenticated_binding(self):
        if self.authenticated_identity != self.role_name:
            raise ValueError("Actual authenticated principal differs")
        return self


class NutritionPrincipalEnrollment(_NutritionRootTransport):
    role_name: NrcName
    verified_human_id: UUID | None
    user_id: UUID | None
    service_id: Identifier | None
    delegation_registrar: StrictBool
    identity_evidence: NutritionSourceEvidence
    idempotency_key: Identifier

    @model_validator(mode="after")
    def human_or_service(self):
        if (self.verified_human_id is None) == (self.service_id is None):
            raise ValueError("Exactly one verified human or service identity required")
        if self.service_id is not None and (self.user_id is not None or self.delegation_registrar):
            raise ValueError("Service cannot become a member author or delegation registrar")
        return self


class NutritionPrincipalFact(_NutritionRootTransport):
    id: UUID
    command: NutritionPrincipalEnrollment
    database_oid: NrcOid
    database_name: NrcName
    role_oid: NrcOid
    administrator: NutritionSourceSession
    recorded_at: AwareTime
    command_hash: Sha256


class NutritionProviderEnrollment(_NutritionRootTransport):
    provider_id: UUID
    code: Identifier
    version: Identifier
    remit: NrcText
    environment: NrcEnvironment
    authority_evidence: NutritionSourceEvidence
    expected_generation: NrcCounter
    previous_enrollment_id: UUID | None
    idempotency_key: Identifier

    @model_validator(mode="after")
    def source_environment(self):
        if self.environment != self.authority_evidence.environment:
            raise ValueError("Provider authority environment differs")
        if (self.expected_generation == 0) != (self.previous_enrollment_id is None):
            raise ValueError("Provider enrollment CAS predecessor required")
        return self


class NutritionProviderFact(_NutritionRootTransport):
    id: UUID
    command: NutritionProviderEnrollment
    generation: NrcCounter
    administrator: NutritionSourceSession
    recorded_at: AwareTime
    command_hash: Sha256


class NutritionAuthorityScope(_NutritionRootTransport):
    provider_id: UUID | None
    family_id: Identifier | None
    household_id: UUID | None
    member_id: UUID | None

    @model_validator(mode="after")
    def exact_scope(self):
        if (
            (self.provider_id is None) != (self.family_id is None)
            or ((self.household_id is None) != (self.member_id is None))
            or (self.provider_id is None and self.member_id is None)
        ):
            raise ValueError("Exact provider/family or household/member scope required")
        return self


class NutritionAuthorityCommand(_NutritionRootTransport):
    principal_id: UUID
    scope: NutritionAuthorityScope
    capability: NrcCapability
    protocol_fingerprint: Sha256 | None
    fact_key: NrcFact | None
    action: Literal["GRANT", "REVOKE"]
    effective: NutritionSourceInterval
    qualification_evidence: NutritionSourceEvidence
    expected_generation: NrcCounter
    predecessor_id: UUID | None
    idempotency_key: Identifier

    @model_validator(mode="after")
    def finite_capability_scope(self):
        s, cap = self.scope, self.capability
        reference = cap.startswith("GUIDELINE_")
        if reference and (s.provider_id is None or s.member_id is not None):
            raise ValueError("Reference permission is provider/family scoped")
        if cap in {"ELIGIBILITY_ATTEST", "ROOT_SOURCE_READ", "VALIDATOR_SOURCE_READ"} and (
            s.provider_id is None or s.member_id is None
        ):
            raise ValueError("Exact reference and member scope required")
        if cap.startswith("MEMBER_") and (s.provider_id is not None or s.member_id is None):
            raise ValueError("Member permission is not global reference authority")
        if (cap == "ELIGIBILITY_ATTEST") != (self.protocol_fingerprint is not None):
            raise ValueError("Exact assessor protocol qualification required")
        if (cap == "MEMBER_OBSERVATION_WRITE") != (self.fact_key is not None):
            raise ValueError("Observation fact scope required")
        if (self.expected_generation == 0) != (self.predecessor_id is None):
            raise ValueError("Authority CAS predecessor required")
        return self


class NutritionAuthorityFact(_NutritionRootTransport):
    id: UUID
    recorded_order: Annotated[int, Field(strict=True, gt=0, le=9_223_372_036_854_775_807)]
    command: NutritionAuthorityCommand
    stream_key: Sha256
    sequence: NrcCounter
    previous_hash: Sha256 | None
    administrator: NutritionSourceSession
    recorded_at: AwareTime
    command_hash: Sha256
    fact_hash: Sha256


class NutritionLegacyProfile(_NutritionRootTransport):
    id: UUID
    household_id: UUID
    member_id: UUID
    row_version: Annotated[int, Field(strict=True, gt=0)]
    body_mass_kg: Annotated[str, Field(max_length=32, pattern=r"^[0-9]+(?:\.[0-9]+)?$")] | None
    height_cm: Annotated[str, Field(max_length=32, pattern=r"^[0-9]+(?:\.[0-9]+)?$")] | None
    created_by_user_id: UUID
    created_at: AwareTime


class NutritionLegacyAnchor(_NutritionRootTransport):
    subject: HouseholdMemberIdentity
    profile: NutritionLegacyProfile | None
    body_fingerprint: Sha256

    @model_validator(mode="after")
    def complete_preimage(self):
        if self.profile is not None and (
            self.profile.household_id != self.subject.household_id
            or self.profile.member_id != self.subject.member_id
        ):
            raise ValueError("Legacy profile subject differs")
        if self.body_fingerprint != nutrition_root_hash(
            "nutrition.legacy-anchor.v1", dict(subject=self.subject, profile=self.profile)
        ):
            raise ValueError("Legacy anchor preimage differs")
        return self


class NutritionSubjectWitness(_NutritionRootTransport):
    subject: HouseholdMemberIdentity
    actor_user_id: UUID | None
    membership_id: UUID | None
    actor_member_id: UUID | None
    role: Literal["OWNER", "EDITOR", "VIEWER"] | None


class NutritionStreamIdentity(_NutritionRootTransport):
    kind: Literal["GUIDELINE", "OBSERVATION", "GOAL", "ASSESSMENT", "DELEGATION"]
    provider_id: UUID | None
    family_id: Identifier | None
    household_id: UUID | None
    member_id: UUID | None
    code: Identifier

    @model_validator(mode="after")
    def finite_owner(self):
        if (self.provider_id is None) != (self.family_id is None) or (
            (self.household_id is None) != (self.member_id is None)
        ):
            raise ValueError("Incomplete source identity")
        if self.kind == "GUIDELINE":
            if self.provider_id is None or self.member_id is not None or self.code != "FAMILY":
                raise ValueError("Exact guideline-family stream required")
        elif self.member_id is None or (
            (self.kind == "ASSESSMENT") != (self.provider_id is not None)
        ):
            raise ValueError("Member truth is not global reference truth")
        if self.kind == "OBSERVATION" and self.code not in {"BODY_MASS", "HEIGHT"}:
            raise ValueError("Unsupported observation fact")
        if self.kind == "GOAL" and self.code != "ENERGY_DIRECTION":
            raise ValueError("Only ENERGY_DIRECTION goal intent is supported")
        return self


class NutritionGuidelineDraft(_NutritionRootTransport):
    kind: Literal["DRAFT"]
    guideline: NutritionGuidelineBody


class NutritionGuidelineReview(_NutritionRootTransport):
    kind: Literal["REVIEW"]
    draft_revision_id: UUID
    body_fingerprint: Sha256
    evidence_fingerprint: Sha256
    protocol_fingerprint: Sha256
    decision: Literal["APPROVE", "CANCEL"]
    prior_review_id: UUID | None
    rationale: NrcText


class NutritionGuidelinePublication(_NutritionRootTransport):
    kind: Literal["PUBLICATION"]
    action: Literal["PUBLISH", "SUPERSEDE", "RETIRE", "RETRACT"]
    draft_revision_id: UUID
    body_fingerprint: Sha256
    review_event_id: UUID | None
    prior_publication_id: UUID | None
    effective_at: AwareTime
    rationale: NrcText


class NutritionObservationRevision(_NutritionRootTransport):
    kind: Literal["OBSERVATION"]
    operation: Literal["CREATE", "REPLACE", "CORRECT", "RETRACT"]
    fact_key: NrcFact
    value: NutritionRootAmount | None
    unit: Literal["KG", "CM"]
    observed_at: AwareTime
    provenance: NutritionSourceEvidence
    effective: NutritionSourceInterval
    replaces: tuple[UUID, ...] = Field(max_length=64)

    @model_validator(mode="after")
    def fact_shape(self):
        if (self.fact_key == "BODY_MASS") != (self.unit == "KG"):
            raise ValueError("Physiological metric/unit mismatch")
        if (self.operation == "RETRACT") != (self.value is None):
            raise ValueError("Retraction is not a numeric observation")
        if self.value is not None and self.value.numerator == 0:
            raise ValueError("Positive physiological measurement required")
        if self.observed_at > self.effective.start:
            raise ValueError("Observation cannot postdate its effective start")
        return self


class NutritionObservationReference(_NutritionRootTransport):
    fact_key: NrcFact
    revision_id: UUID
    fact_hash: Sha256
    value: NutritionRootAmount
    unit: Literal["KG", "CM"]
    legacy_anchor_fingerprint: Sha256


class NutritionEligibilityRevision(_NutritionRootTransport):
    kind: Literal["ASSESSMENT"]
    operation: Literal["CREATE", "REPLACE", "CORRECT", "RETRACT"]
    guideline_revision_id: UUID
    guideline_body_fingerprint: Sha256
    protocol_fingerprint: Sha256
    outcome: Literal["ADMITTED", "OUT_OF_SCOPE", "EXCLUDED", "UNDETERMINED"]
    observations: tuple[NutritionObservationReference, ...] = Field(max_length=2)
    evidence: tuple[NutritionSourceEvidence, ...] = Field(max_length=32)
    missing_observations: tuple[NrcFact, ...] = Field(max_length=2)
    missing_evidence_slots: tuple[Identifier, ...] = Field(max_length=32)
    effective: NutritionSourceInterval
    replaces: tuple[UUID, ...] = Field(max_length=64)


class NutritionGoalRevision(_NutritionRootTransport):
    kind: Literal["GOAL"]
    operation: Literal["CREATE", "REPLACE", "CORRECT", "RETRACT"]
    goal_id: UUID
    goal_type: Literal["ENERGY_DIRECTION"]
    direction: Literal["CUT", "MAINTAIN", "GAIN"] | None
    effective: NutritionSourceInterval
    replaces: tuple[UUID, ...] = Field(max_length=64)
    provenance: NutritionSourceEvidence

    @model_validator(mode="after")
    def intent_only(self):
        if (self.operation == "RETRACT") != (self.direction is None):
            raise ValueError("Retraction is not MAINTAIN or resurrection")
        return self


class NutritionDelegationRevision(_NutritionRootTransport):
    kind: Literal["DELEGATION"]
    action: Literal["GRANT", "REVOKE"]
    grantee_principal_id: UUID
    operation_scope: Literal["MEMBER_GOAL_WRITE", "BODY_MASS_WRITE", "HEIGHT_WRITE"]
    effective: NutritionSourceInterval
    authorization_evidence: NutritionSourceEvidence
    previous_grant_id: UUID | None


NutritionSourceBody = Annotated[
    NutritionGuidelineDraft
    | NutritionGuidelineReview
    | NutritionGuidelinePublication
    | NutritionObservationRevision
    | NutritionEligibilityRevision
    | NutritionGoalRevision
    | NutritionDelegationRevision,
    Field(discriminator="kind"),
]


class NutritionSourceCommand(_NutritionRootTransport):
    contract_version: Literal["nutrition-source-command.v1"] = "nutrition-source-command.v1"
    revision_id: UUID
    identity: NutritionStreamIdentity
    body: NutritionSourceBody
    expected_revision: NrcCounter
    predecessor_id: UUID | None
    idempotency_key: Identifier

    @model_validator(mode="after")
    def source_class_and_lineage(self):
        expected_kind = (
            "GUIDELINE"
            if self.body.kind in {"DRAFT", "REVIEW", "PUBLICATION"}
            else (self.body.kind)
        )
        if self.identity.kind != expected_kind:
            raise ValueError("Source body and stream owner differ")
        if (self.expected_revision == 0) != (self.predecessor_id is None):
            raise ValueError("Exact stream predecessor required")
        if self.body.kind == "DRAFT" and (
            self.body.guideline.revision_id != self.revision_id
            or self.body.guideline.provider_id != self.identity.provider_id
            or self.body.guideline.family_id != self.identity.family_id
        ):
            raise ValueError("Draft immutable identity differs")
        if self.body.kind == "OBSERVATION" and self.body.fact_key != self.identity.code:
            raise ValueError("Observation stream fact differs")
        if self.body.kind == "ASSESSMENT" and self.body.protocol_fingerprint != self.identity.code:
            raise ValueError("Assessment stream protocol differs")
        if self.body.kind == "DELEGATION" and self.identity.code != (
            self.body.operation_scope + ":" + str(self.body.grantee_principal_id)
        ):
            raise ValueError("Exact delegated operation/actor stream required")
        body = self.body
        if body.kind in {"OBSERVATION", "ASSESSMENT", "GOAL"}:
            if tuple(sorted(set(body.replaces), key=str)) != body.replaces:
                raise ValueError("Unique sorted replacement identities required")
            if (body.operation == "CREATE") != (not body.replaces):
                raise ValueError("Explicit replacement lineage required")
        if body.kind == "REVIEW" and (
            (body.decision == "CANCEL") != (body.prior_review_id is not None)
        ):
            raise ValueError("Review cancellation requires an exact prior review")
        if body.kind == "PUBLICATION":
            if (body.action in {"PUBLISH", "SUPERSEDE"}) != (body.review_event_id is not None):
                raise ValueError("Publication requires review; withdrawal cannot publish")
            if (body.action == "PUBLISH") != (body.prior_publication_id is None):
                raise ValueError("Explicit publication predecessor required")
        if body.kind == "DELEGATION" and (
            (body.action == "REVOKE") != (body.previous_grant_id is not None)
        ):
            raise ValueError("Delegation revoke requires exact grant")
        if body.kind == "ASSESSMENT":
            facts = tuple(o.fact_key for o in body.observations)
            evidence = tuple(e.evidence_id for e in body.evidence)
            for keys in (facts, evidence, body.missing_observations, body.missing_evidence_slots):
                if tuple(sorted(set(keys))) != keys:
                    raise ValueError("Unique sorted assessment keys required")
            if any((o.fact_key == "BODY_MASS") != (o.unit == "KG") for o in body.observations):
                raise ValueError("Assessment observation unit mismatch")
        return self


class NutritionRecordedSource(_NutritionRootTransport):
    id: UUID
    recorded_order: Annotated[int, Field(strict=True, gt=0, le=9_223_372_036_854_775_807)]
    command: NutritionSourceCommand
    stream_key: Sha256
    sequence: NrcCounter
    previous_hash: Sha256 | None
    principal_id: UUID
    grant_event_id: UUID
    authority_generation: NrcCounter
    provider_enrollment_id: UUID | None
    author: NutritionSourceSession
    subject_witness: NutritionSubjectWitness | None
    delegation_event_id: UUID | None
    legacy_anchor: NutritionLegacyAnchor | None
    recorded_at: AwareTime
    command_hash: Sha256
    fact_hash: Sha256


class NutritionStreamManifest(_NutritionRootTransport):
    stream_key: Sha256
    source_identity: NutritionStreamIdentity | None
    authority_scope: NutritionAuthorityScope | None
    revision: NrcCounter
    head_id: UUID | None
    head_hash: Sha256 | None

    @model_validator(mode="after")
    def typed_frontier(self):
        if (self.source_identity is None) == (self.authority_scope is None):
            raise ValueError("One typed stream identity required")
        if (self.revision == 0) != (self.head_id is None) or (
            (self.revision == 0) != (self.head_hash is None)
        ):
            raise ValueError("Complete frontier/absence witness required")
        return self


class NutritionRootRequest(_NutritionRootTransport):
    contract_version: Literal["nutrition-root-request.v1"] = "nutrition-root-request.v1"
    subject: HouseholdMemberIdentity
    provider_id: UUID
    family_id: Identifier
    guideline_revision_id: UUID
    guideline_body_fingerprint: Sha256
    protocol_fingerprint: Sha256
    scope_id: Identifier
    scope_version: Identifier
    temporal: NutritionTemporalScope
    environment: NrcEnvironment
    purpose: Literal["ROOT", "VALIDATOR"]
    goal_type: Literal["ENERGY_DIRECTION"]


class NutritionCaptureFrame(_NutritionRootTransport):
    session: NutritionSourceSession
    reader_principal_id: UUID
    reader_subject_witness: NutritionSubjectWitness
    reader_grant_id: UUID
    endpoint: NrcText
    backend_pid: NrcCounter
    mvcc_snapshot: NrcText
    transaction_id: Literal["UNASSIGNED_READ_ONLY"]
    isolation: Literal["REPEATABLE READ", "SERIALIZABLE"]
    read_only: Literal[True]
    started_at: AwareTime
    completed_at: AwareTime
    provider_enrollment_id: UUID
    row_count: NrcCounter
    absence_stream_keys: tuple[Sha256, ...]


class NutritionRootSourceSnapshot(_NutritionRootTransport):
    contract_version: Literal["nutrition-root-sources.v1"] = "nutrition-root-sources.v1"
    request: NutritionRootRequest
    provider_enrollments: tuple[NutritionProviderFact, ...] = Field(min_length=1, max_length=64)
    principals: tuple[NutritionPrincipalFact, ...] = Field(min_length=1, max_length=512)
    authority: tuple[NutritionAuthorityFact, ...] = Field(max_length=4096)
    sources: tuple[NutritionRecordedSource, ...] = Field(max_length=4096)
    streams: tuple[NutritionStreamManifest, ...] = Field(max_length=512)
    current_legacy_anchor: NutritionLegacyAnchor
    capture: NutritionCaptureFrame
    source_fingerprint: Sha256


class NutritionResolvedRoot(_NutritionRootTransport):
    publication_event_id: UUID
    guideline_revision_id: UUID
    guideline_body_fingerprint: Sha256
    clause: NutritionGuidelineClause


class NutritionRootContract(_NutritionRootTransport):
    contract_version: Literal["nutrition-root-contract.v1"] = "nutrition-root-contract.v1"
    sources: NutritionRootSourceSnapshot
    availability: Literal["AVAILABLE", "UNAVAILABLE"]
    eligibility: Literal["SUPPORTED", "UNSUPPORTED", "INELIGIBLE", "UNKNOWN"]
    goal_state: Literal["PRESENT", "ABSENT", "RETRACTED", "AMBIGUOUS"]
    goal_revision_id: UUID | None
    goal_direction: Literal["CUT", "MAINTAIN", "GAIN"] | None
    roots: tuple[NutritionResolvedRoot, ...]
    reasons: tuple[Identifier, ...]
    source_fingerprint: Sha256
    result_fingerprint: Sha256
    policy_synthesis: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    numeric_goal_protection: Literal["NOT_SYNTHESIZED"] = "NOT_SYNTHESIZED"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False
    source_origin: Literal["RETAINED_SELF_CONSISTENCY_NOT_OFFLINE_DATABASE_PROOF"] = (
        "RETAINED_SELF_CONSISTENCY_NOT_OFFLINE_DATABASE_PROOF"
    )
    current_authorization: Literal["NOT_CLAIMED"] = "NOT_CLAIMED"
    scientific_correctness: Literal["NOT_CERTIFIED"] = "NOT_CERTIFIED"


class NutritionDerivedContainmentClaim(_NutritionRootTransport):
    """Later-policy claim carrier; its content is not new policy/source authority."""

    root: NutritionResolvedRoot
    constraint: NutritionRootConstraint
    claim_kind: Literal["PROTECTED", "COMFORT", "GOAL_PROTECTION"]
    policy_evidence: NutritionSourceEvidence
    goal_revision_id: UUID | None
    baseline_evidence: NutritionSourceEvidence | None


class NutritionRootValidationInput(_NutritionRootTransport):
    contract_version: Literal["nutrition-root-validation-input.v1"] = (
        "nutrition-root-validation-input.v1"
    )
    root: NutritionRootContract
    coverage: Literal["ROOT_SOURCE_CONSISTENCY_ONLY", "ROOT_AND_DERIVED_CONTAINMENT"]
    derived_claims: tuple[NutritionDerivedContainmentClaim, ...] = Field(max_length=32)


class NutritionRootValidationReport(_NutritionRootTransport):
    contract_version: Literal["nutrition-root-validation-report.v1"] = (
        "nutrition-root-validation-report.v1"
    )
    coverage: Literal["ROOT_SOURCE_CONSISTENCY_ONLY", "ROOT_AND_DERIVED_CONTAINMENT"]
    decision: Literal["CONSISTENT", "INCONSISTENT", "UNSUPPORTED"]
    findings: tuple[Identifier, ...]
    source_fingerprint: Sha256
    root_fingerprint: Sha256
    containment_checked: StrictBool
    policy_business_correctness: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"
    scientific_correctness: Literal["NOT_CERTIFIED"] = "NOT_CERTIFIED"
    current_authorization: Literal["NOT_CLAIMED"] = "NOT_CLAIMED"
    canonical_database_origin: Literal["NOT_PROVED_OFFLINE"] = "NOT_PROVED_OFFLINE"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False
