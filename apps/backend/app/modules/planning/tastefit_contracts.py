"""Conditional exact-target fit values, never a household/candidate utility scalar."""

from math import gcd
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.contracts import AwareTime, Identifier, Sha256
from app.domain.feature_identity import canonical_bytes, unique_sorted
from app.domain.units import Provenance
from app.modules.planning.contracts import (
    CandidateFeatureBinding,
    CandidateFeatureProjectionDraft,
    CandidateFeatureProjectionRequest,
    CandidateGroundingRequest,
)
from app.modules.preferences.contracts import (
    DerivedExplicitEvidenceStrength,
    PreferenceTarget,
    TargetKind,
    TargetManifestEntry,
    preference_target_key,
)
from app.modules.preferences.tastefit_contracts import (
    CaptureMode,
    InheritedMemberPreferenceCoordinate,
    MemberProfileAffinityCoordinate,
    TasteFitCaptureFrame,
    TasteFitContract,
    TasteFitMemberInterpretationPlan,
    TasteFitMemberSourceBundle,
    TasteFitMemberView,
    tastefit_hash,
)
from app.modules.recipes.contracts import FeatureDimensionDiscovery, FeatureTermResolution

SelectedMode = Literal[
    "RAW_EXPLICIT", "EXACT_TARGET_EFFECTIVE", "NO_EVIDENCE", "PRIOR_ONLY", "ONE_HOP_INHERITED"
]
SemanticState = Literal["LIKE", "DISLIKE", "NEUTRAL", "NO_DECLARATION"]


class TasteFitAmount(TasteFitContract):
    numerator: Annotated[int, Field(strict=True)]
    denominator: Annotated[int, Field(strict=True, gt=0)]

    @model_validator(mode="after")
    def rational(self):
        if abs(self.numerator) > self.denominator:
            raise ValueError("Signed unit rational required")
        divisor = gcd(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", self.numerator // divisor)
        object.__setattr__(self, "denominator", self.denominator // divisor)
        return self


class RawExplicitTasteFitCoordinate(TasteFitContract):
    family: Literal["FROZEN_040B_EXPLICIT"] = "FROZEN_040B_EXPLICIT"
    wrapper_version: Literal[1] = 1
    scope: Literal["ONE_EXACT_CURRENT_DECLARATION"] = "ONE_EXACT_CURRENT_DECLARATION"
    target_kind: TargetKind
    explicit_policy_id: Identifier
    explicit_policy_version: Identifier
    explicit_policy_fingerprint: Sha256
    unit: Literal["POLICY_EXPLICIT_AFFINITY_UNITS"] = "POLICY_EXPLICIT_AFFINITY_UNITS"


class ProfileTasteFitSourceCoordinate(TasteFitContract):
    family: Literal["PROFILE"] = "PROFILE"
    coordinate: MemberProfileAffinityCoordinate


class InheritedTasteFitSourceCoordinate(TasteFitContract):
    family: Literal["INHERITED"] = "INHERITED"
    coordinate: InheritedMemberPreferenceCoordinate


TasteFitSourceCoordinate = Annotated[
    RawExplicitTasteFitCoordinate
    | ProfileTasteFitSourceCoordinate
    | InheritedTasteFitSourceCoordinate,
    Field(discriminator="family"),
]


class TasteFitMappingRow(TasteFitContract):
    target_kind: TargetKind
    source_mode: Literal[
        "RAW_EXPLICIT", "EXACT_TARGET_EFFECTIVE", "PRIOR_ONLY", "ONE_HOP_INHERITED"
    ]
    semantic_state: SemanticState
    source_coordinate: TasteFitSourceCoordinate
    source_amount: TasteFitAmount
    fit_amount: TasteFitAmount

    @model_validator(mode="after")
    def semantic_coordinate(self):
        c = self.source_coordinate
        family, kind = (
            c.family,
            (
                c.target_kind
                if c.family == "FROZEN_040B_EXPLICIT"
                else c.coordinate.target_kind
                if c.family == "PROFILE"
                else c.coordinate.destination_target_kind
            ),
        )
        expected = {
            "RAW_EXPLICIT": "FROZEN_040B_EXPLICIT",
            "EXACT_TARGET_EFFECTIVE": "PROFILE",
            "PRIOR_ONLY": "PROFILE",
            "ONE_HOP_INHERITED": "INHERITED",
        }[self.source_mode]
        if kind != self.target_kind or family != expected:
            raise ValueError("Mapping source descriptor kind/family differs")
        if (self.semantic_state == "NO_DECLARATION") != (self.source_mode == "PRIOR_ONLY"):
            raise ValueError("Prior-only semantic must be NO_DECLARATION, never NEUTRAL")
        n = self.fit_amount.numerator
        if (
            (self.semantic_state == "LIKE" and n <= 0)
            or (self.semantic_state == "DISLIKE" and n >= 0)
            or (self.semantic_state == "NEUTRAL" and n != 0)
        ):
            raise ValueError("Fit LIKE > 0, DISLIKE < 0, NEUTRAL = 0 required")
        return self

    def key(self):
        return canonical_bytes(
            dict(
                target_kind=self.target_kind,
                source_mode=self.source_mode,
                semantic_state=self.semantic_state,
                source_coordinate=self.source_coordinate,
                source_amount=self.source_amount,
            )
        ).decode()


class TasteFitKindPolicy(TasteFitContract):
    target_kind: TargetKind
    capture_mode: CaptureMode
    declared_selection: Literal["RAW_EXPLICIT", "EXACT_TARGET_EFFECTIVE"]
    undeclared_selection: Literal["NO_EVIDENCE", "PRIOR_ONLY", "ONE_HOP_INHERITED"]
    mappings: tuple[TasteFitMappingRow, ...]

    @model_validator(mode="after")
    def selections(self):
        if (
            self.capture_mode == "EXPLICIT_ONLY"
            and (
                self.declared_selection != "RAW_EXPLICIT"
                or self.undeclared_selection != "NO_EVIDENCE"
            )
        ) or (
            self.undeclared_selection == "ONE_HOP_INHERITED"
            and self.capture_mode != "EXACT_TARGET_AND_ONE_HOP"
        ):
            raise ValueError("Capture mode cannot supply selected view")
        rows = unique_sorted(self.mappings, key=lambda r: r.key())
        choices = {self.declared_selection, self.undeclared_selection}
        if any(r.target_kind != self.target_kind or r.source_mode not in choices for r in rows):
            raise ValueError("Mapping not in admitted kind/selected modes")
        object.__setattr__(self, "mappings", rows)
        return self


class TasteFitInterpretationPolicy(TasteFitContract):
    contract_version: Literal["candidate-member-tastefit-policy.v1"]
    policy_id: Identifier
    policy_version: Identifier
    provenance: Provenance
    interpretation_mode: Literal["VERSIONED_CONSUMER_POLICY_REPLAY"]
    admitted_kinds: Annotated[tuple[TargetKind, ...], Field(min_length=1)]
    kind_policies: Annotated[tuple[TasteFitKindPolicy, ...], Field(min_length=1)]
    operator: Literal["PER_TARGET_FINITE_EXACT_LOOKUP"]
    aggregation: Literal["NOT_PERFORMED"]
    evidence_strength_effect: Literal["LINEAGE_ONLY"]
    retraction: Literal["SUPPRESS"]
    max_targets: Annotated[int, Field(strict=True, gt=0)]
    max_policy_bytes: Annotated[int, Field(strict=True, gt=0)]
    max_source_bytes: Annotated[int, Field(strict=True, gt=0)]

    @model_validator(mode="after")
    def authored_sets(self):
        kinds = unique_sorted(self.admitted_kinds)
        groups = unique_sorted(self.kind_policies, key=lambda p: p.target_kind)
        if kinds != tuple(g.target_kind for g in groups):
            raise ValueError("Exactly one policy per admitted kind required")
        if self.provenance.kind not in {"USER", "REVIEWED_REFERENCE"}:
            raise ValueError("Authored interpretation policy required")
        object.__setattr__(self, "admitted_kinds", kinds)
        object.__setattr__(self, "kind_policies", groups)
        return self

    def fingerprint(self):
        return tastefit_hash("candidate-member.tastefit-policy.v1", self)


class CandidateMemberTasteFitRequest(TasteFitContract):
    contract_version: Literal["candidate-member-tastefit-request.v1"] = (
        "candidate-member-tastefit-request.v1"
    )
    household_id: UUID
    member_id: UUID
    projection_request: CandidateFeatureProjectionRequest
    projection_mode: Literal["FRESH_CANONICAL_PROJECTION"]
    diagnostic_targets: tuple[PreferenceTarget, ...]
    expected_policy_id: Identifier
    expected_policy_version: Identifier
    expected_policy_fingerprint: Sha256
    policy: TasteFitInterpretationPolicy
    member_interpretation: TasteFitMemberInterpretationPlan

    @model_validator(mode="after")
    def request_sets(self):
        if self.household_id != self.projection_request.grounding_request.household_id:
            raise ValueError("SUBJECT_OWNER_MISMATCH: request household differs")
        object.__setattr__(
            self,
            "diagnostic_targets",
            unique_sorted(self.diagnostic_targets, key=preference_target_key),
        )
        p = self.policy
        if (p.policy_id, p.policy_version) != (
            self.expected_policy_id,
            self.expected_policy_version,
        ):
            raise ValueError("POLICY_VERSION_MISMATCH")
        if p.fingerprint() != self.expected_policy_fingerprint:
            raise ValueError("POLICY_FINGERPRINT_MISMATCH")
        return self


class CandidateMemberTasteFitSources(TasteFitContract):
    contract_version: Literal["candidate-member-tastefit-sources.v1"] = (
        "candidate-member-tastefit-sources.v1"
    )
    request: CandidateMemberTasteFitRequest
    projection: CandidateFeatureProjectionDraft
    member_sources: TasteFitMemberSourceBundle
    candidate_frame: TasteFitCaptureFrame
    capture_started_at: AwareTime
    capture_completed_at: AwareTime
    fingerprint: Sha256

    def expected_fingerprint(self):
        return tastefit_hash(
            "candidate-member.tastefit-sources.v1", self.model_dump(exclude={"fingerprint"})
        )


class TasteFitSubject(TasteFitContract):
    household_id: UUID
    member_id: UUID
    grounding_fingerprint: Sha256
    projection_fingerprint: Sha256
    binding: CandidateFeatureBinding
    grounding_request: CandidateGroundingRequest


class TasteFitTargetProof(TasteFitContract):
    target: PreferenceTarget
    role: Literal["BASE", "DIAGNOSTIC_ONLY"]
    identity: TargetManifestEntry
    candidate_state: Literal["PRESENT", "ABSENT", "UNRESOLVED"]
    reason: str | None
    requirement_ids: tuple[UUID, ...]
    term_resolution: FeatureTermResolution | None
    dimension: FeatureDimensionDiscovery | None


class TasteFitCoordinate(TasteFitContract):
    coordinate_id: Literal["CANDIDATE_MEMBER_TARGET_FIT"] = "CANDIDATE_MEMBER_TARGET_FIT"
    coordinate_version: Literal[1] = 1
    unit: Literal["POLICY_TARGET_TASTEFIT_UNITS"] = "POLICY_TARGET_TASTEFIT_UNITS"
    scope: Literal["ONE_POLICY_ONE_HOUSEHOLD_ONE_MEMBER_ONE_CANDIDATE_ONE_TARGET"] = (
        "ONE_POLICY_ONE_HOUSEHOLD_ONE_MEMBER_ONE_CANDIDATE_ONE_TARGET"
    )
    policy_fingerprint: Sha256
    household_id: UUID
    member_id: UUID
    grounding_fingerprint: Sha256
    projection_fingerprint: Sha256
    target: PreferenceTarget


class ScopedTargetTasteFit(TasteFitContract):
    coordinate: TasteFitCoordinate
    amount: TasteFitAmount

    def scoped_numeric_equal(self, other):
        left = type(self).model_validate(self)
        right = type(self).model_validate(other)
        if left.coordinate != right.coordinate:
            raise ValueError("TasteFit descriptor mismatch: comparison not defined")
        return left.amount == right.amount


class TasteFitTargetInterpretation(TasteFitContract):
    proof: TasteFitTargetProof
    member_views: TasteFitMemberView
    policy_admission: Literal["ADMITTED", "NOT_ADMITTED"]
    selected_mode: SelectedMode | None
    view_dispositions: tuple[
        tuple[str, Literal["SELECTED", "NOT_SELECTED", "NOT_REQUESTED_BY_POLICY"]], ...
    ]
    status: Literal["AVAILABLE", "UNAVAILABLE", "SUPPRESSED"]
    reason: str | None
    source_reason: str | None
    direct_signal: Literal["NONE", "DECLARED_LIKE", "DECLARED_DISLIKE", "DECLARED_NEUTRAL"]
    declaration_id: UUID | None
    evidence_strength: DerivedExplicitEvidenceStrength
    semantic_state: SemanticState | None
    source_coordinate: TasteFitSourceCoordinate | None
    source_amount: TasteFitAmount | None
    mapping: TasteFitMappingRow | None
    value: ScopedTargetTasteFit | None

    @model_validator(mode="after")
    def available_shape(self):
        if (self.status == "AVAILABLE") != (self.value is not None):
            raise ValueError("Only available fit may carry a value")
        if self.value is not None and (self.mapping is None or self.reason is not None):
            raise ValueError("Available fit needs exact mapping without unavailable reason")
        return self


class CandidateMemberTasteFitDraft(TasteFitContract):
    contract_version: Literal["candidate-member-tastefit.v1-draft"] = (
        "candidate-member-tastefit.v1-draft"
    )
    sources: CandidateMemberTasteFitSources
    subject: TasteFitSubject
    targets: tuple[TasteFitTargetInterpretation, ...]
    dimensions: tuple[FeatureDimensionDiscovery, ...]
    dimension_diagnostics: tuple[tuple[str, str], ...]
    status: Literal["DERIVED"] = "DERIVED"
    coverage: Literal["EXACT_RETAINED_SCOPE_ONLY"] = "EXACT_RETAINED_SCOPE_ONLY"
    policy_authority: Literal["EXPLICIT_INTERPRETATION_INPUT_ONLY"] = (
        "EXPLICIT_INTERPRETATION_INPUT_ONLY"
    )
    interpretation_mode: Literal["VERSIONED_CONSUMER_POLICY_REPLAY"] = (
        "VERSIONED_CONSUMER_POLICY_REPLAY"
    )
    source_origin: Literal["RETAINED_EVIDENCE_NOT_OFFLINE_ORIGIN_PROOF"] = (
        "RETAINED_EVIDENCE_NOT_OFFLINE_ORIGIN_PROOF"
    )
    common_mvcc: Literal["NOT_CLAIMED"] = "NOT_CLAIMED"
    aggregate: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    shared_member_aggregation: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    candidate_comparison: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    learned_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    contextual_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    passive_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False
    fingerprint: Sha256

    def expected_fingerprint(self):
        return tastefit_hash(
            "candidate-member.tastefit-result.v1", self.model_dump(exclude={"fingerprint"})
        )
