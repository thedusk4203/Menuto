"""Explicit conditional shared-target transport; no policy selection or persistence."""

from math import gcd
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.contracts import AwareTime, Identifier, Sha256
from app.domain.feature_identity import canonical_bytes, identity_hash, unique_sorted
from app.domain.units import Provenance
from app.modules.households.contracts import MealParticipants
from app.modules.planning import tastefit_contracts as child
from app.modules.planning.contracts import (
    CandidateFeatureBinding,
    CandidateFeatureProjectionRequest,
)

DirectSignal = Literal["NONE", "DECLARED_LIKE", "DECLARED_DISLIKE", "DECLARED_NEUTRAL"]
Compatibility = Literal["COMPATIBLE", "INCOMPATIBLE", "NOT_EVALUABLE"]


def shared_tastefit_hash(domain, value):
    return identity_hash(dict(domain=domain, value=value))


class _Rational(child.TasteFitContract):
    numerator: Annotated[int, Field(strict=True)]
    denominator: Annotated[int, Field(strict=True, gt=0)]

    @model_validator(mode="after")
    def canonical_rational(self):
        divisor = gcd(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", self.numerator // divisor)
        object.__setattr__(self, "denominator", self.denominator // divisor)
        return self


class SharedTargetTasteFitAmount(_Rational):
    @model_validator(mode="after")
    def bounded(self):
        if abs(self.numerator) > self.denominator:
            raise ValueError("Signed unit shared-target rational required")
        return self


class SharedTasteFitWeight(_Rational):
    @model_validator(mode="after")
    def positive(self):
        if self.numerator <= 0:
            raise ValueError("Explicit strictly positive member influence required")
        return self


class SharedTasteFitMemberWeight(child.TasteFitContract):
    member_id: UUID
    weight: SharedTasteFitWeight


class SharedTasteFitPolicyAdmission(child.TasteFitContract):
    policy: child.TasteFitInterpretationPolicy
    expected_policy_id: Identifier
    expected_policy_version: Identifier
    expected_policy_fingerprint: Sha256

    @model_validator(mode="after")
    def pins(self):
        p = self.policy
        if (p.policy_id, p.policy_version) != (
            self.expected_policy_id,
            self.expected_policy_version,
        ):
            raise ValueError("POLICY_VERSION_MISMATCH: child admission")
        if p.fingerprint() != self.expected_policy_fingerprint:
            raise ValueError("POLICY_FINGERPRINT_MISMATCH: child admission")
        return self

    def key(self):
        return (
            self.expected_policy_id,
            self.expected_policy_version,
            self.expected_policy_fingerprint,
        )


class SharedTasteFitBridgeRule(child.TasteFitContract):
    rule_id: Identifier
    admission: SharedTasteFitPolicyAdmission
    target_kind: child.TargetKind
    mapping: child.TasteFitMappingRow
    direct_signal: DirectSignal
    mapped_amount: SharedTargetTasteFitAmount

    @model_validator(mode="after")
    def exact_semantics(self):
        row = self.mapping
        group = next(
            (g for g in self.admission.policy.kind_policies if g.target_kind == self.target_kind),
            None,
        )
        if group is None or row.target_kind != self.target_kind or row not in group.mappings:
            raise ValueError("BRIDGE_MAPPING_NOT_ADMITTED")
        expected = (
            "DECLARED_" + row.semantic_state
            if row.source_mode in {"RAW_EXPLICIT", "EXACT_TARGET_EFFECTIVE"}
            else "NONE"
        )
        if self.direct_signal != expected:
            raise ValueError("BRIDGE_DIRECT_SIGNAL_MISMATCH")
        left, right = row.fit_amount.numerator, self.mapped_amount.numerator
        if (left > 0) != (right > 0) or (left < 0) != (right < 0):
            raise ValueError("BRIDGE_FIT_SIGN_MISMATCH")
        return self

    def key(self):
        return canonical_bytes(
            dict(
                admission=self.admission,
                target_kind=self.target_kind,
                mapping=self.mapping,
                direct_signal=self.direct_signal,
            )
        ).decode()


class SharedMemberTargetTasteFitPolicy(child.TasteFitContract):
    contract_version: Literal["candidate-shared-member-target-tastefit-policy.v1"]
    policy_id: Identifier
    policy_version: Identifier
    provenance: Provenance
    interpretation_mode: Literal["VERSIONED_CONSUMER_POLICY_REPLAY"]
    target_kind: child.TargetKind
    participant_scope: Literal["EXACT_CANONICAL_PARTICIPANTS"]
    compatibility: Literal["FINITE_PINNED_CHILD_MAPPING_BRIDGES"]
    policy_admissions: Annotated[tuple[SharedTasteFitPolicyAdmission, ...], Field(min_length=1)]
    bridge_rules: Annotated[tuple[SharedTasteFitBridgeRule, ...], Field(min_length=1)]
    member_weights: Annotated[tuple[SharedTasteFitMemberWeight, ...], Field(min_length=1)]
    operator: Literal["EXACT_POSITIVE_WEIGHTED_MEAN"]
    incomplete_coverage: Literal["WITHHOLD_AGGREGATE"]
    direct_signal_effect: Literal["RETAIN_SEPARATELY_NO_IMPLICIT_VETO_OR_WEIGHT"]
    evidence_strength_effect: Literal["LINEAGE_ONLY"]
    max_members: Annotated[int, Field(strict=True, gt=0)]
    max_policy_bytes: Annotated[int, Field(strict=True, gt=0)]
    max_source_bytes: Annotated[int, Field(strict=True, gt=0)]
    max_result_bytes: Annotated[int, Field(strict=True, gt=0)]
    max_integer_bits: Annotated[int, Field(strict=True, gt=0)]

    @model_validator(mode="after")
    def authored_sets(self):
        if self.provenance.kind not in {"USER", "REVIEWED_REFERENCE"}:
            raise ValueError("Explicit authored policy required")
        admissions = unique_sorted(self.policy_admissions, key=lambda a: a.key()[:2])
        if len({a.expected_policy_fingerprint for a in admissions}) != len(admissions):
            raise ValueError("Duplicate admitted policy body")
        if any(self.target_kind not in a.policy.admitted_kinds for a in admissions):
            raise ValueError("POLICY_TARGET_KIND_MISMATCH")
        rules = unique_sorted(self.bridge_rules, key=lambda r: r.key())
        if len({r.rule_id for r in rules}) != len(rules):
            raise ValueError("Duplicate bridge rule ID")
        if any(r.target_kind != self.target_kind or r.admission not in admissions for r in rules):
            raise ValueError("Detached bridge admission/kind")
        weights = unique_sorted(self.member_weights, key=lambda w: str(w.member_id))
        if len(weights) > self.max_members:
            raise ValueError("RESOURCE_LIMIT: member budget")
        for name, value in (
            ("policy_admissions", admissions),
            ("bridge_rules", rules),
            ("member_weights", weights),
        ):
            object.__setattr__(self, name, value)
        return self

    def fingerprint(self):
        return shared_tastefit_hash("shared-target.policy.v1", self)


class SharedTasteFitMemberInput(SharedTasteFitPolicyAdmission):
    member_id: UUID
    member_interpretation: child.TasteFitMemberInterpretationPlan


class SharedMemberTargetTasteFitRequest(child.TasteFitContract):
    contract_version: Literal["candidate-shared-member-target-tastefit-request.v1"] = (
        "candidate-shared-member-target-tastefit-request.v1"
    )
    household_id: UUID
    projection_request: CandidateFeatureProjectionRequest
    target: child.PreferenceTarget
    members: Annotated[tuple[SharedTasteFitMemberInput, ...], Field(min_length=1)]
    projection_mode: Literal["FRESH_CANONICAL_CHILD_CAPTURE"]
    policy: SharedMemberTargetTasteFitPolicy
    expected_policy_id: Identifier
    expected_policy_version: Identifier
    expected_policy_fingerprint: Sha256

    @model_validator(mode="after")
    def complete_request(self):
        p, g = self.policy, self.projection_request.grounding_request
        if self.household_id != g.household_id:
            raise ValueError("SUBJECT_OWNER_MISMATCH")
        if (p.policy_id, p.policy_version) != (
            self.expected_policy_id,
            self.expected_policy_version,
        ):
            raise ValueError("POLICY_VERSION_MISMATCH")
        if p.fingerprint() != self.expected_policy_fingerprint:
            raise ValueError("POLICY_FINGERPRINT_MISMATCH")
        if p.target_kind != self.target.kind:
            raise ValueError("POLICY_TARGET_KIND_MISMATCH")
        members = unique_sorted(self.members, key=lambda m: str(m.member_id))
        expected = {m.member_id for m in g.participants.participants}
        if (
            not expected
            or {m.member_id for m in members} != expected
            or {w.member_id for w in p.member_weights} != expected
        ):
            raise ValueError("PARTICIPANT_SET_MISMATCH")
        if len(members) > p.max_members:
            raise ValueError("RESOURCE_LIMIT")
        object.__setattr__(self, "members", members)
        return self


class SharedMemberTargetTasteFitSources(child.TasteFitContract):
    contract_version: Literal["candidate-shared-member-target-tastefit-sources.v1"] = (
        "candidate-shared-member-target-tastefit-sources.v1"
    )
    request: SharedMemberTargetTasteFitRequest
    children: tuple[child.CandidateMemberTasteFitDraft, ...]
    owner_frames: tuple[tuple[UUID, tuple[child.TasteFitCaptureFrame, ...]], ...]
    capture_started_at: AwareTime
    capture_completed_at: AwareTime
    fingerprint: Sha256

    @model_validator(mode="after")
    def source_sets(self):
        object.__setattr__(
            self, "children", unique_sorted(self.children, key=lambda c: str(c.subject.member_id))
        )
        object.__setattr__(
            self, "owner_frames", unique_sorted(self.owner_frames, key=lambda f: str(f[0]))
        )
        if self.capture_started_at > self.capture_completed_at:
            raise ValueError("SOURCE_CUT_INCOHERENT: outer clock regression")
        return self

    def expected_fingerprint(self):
        return shared_tastefit_hash(
            "shared-target.sources.v1", self.model_dump(exclude={"fingerprint"})
        )


class SharedMemberTargetTasteFitCoordinate(child.TasteFitContract):
    coordinate_id: Literal["SHARED_MEMBER_EXACT_TARGET_TASTEFIT"] = (
        "SHARED_MEMBER_EXACT_TARGET_TASTEFIT"
    )
    coordinate_version: Literal[1] = 1
    unit: Literal["POLICY_SHARED_EXACT_TARGET_TASTEFIT_UNITS"] = (
        "POLICY_SHARED_EXACT_TARGET_TASTEFIT_UNITS"
    )
    scope: Literal["ONE_CANDIDATE_ONE_TARGET_EXACT_PARTICIPANTS_ONE_POLICY_ONE_RETAINED_COHORT"] = (
        "ONE_CANDIDATE_ONE_TARGET_EXACT_PARTICIPANTS_ONE_POLICY_ONE_RETAINED_COHORT"
    )
    household_id: UUID
    binding: CandidateFeatureBinding
    grounding_fingerprint: Sha256
    target: child.PreferenceTarget
    participant_context_fingerprint: Sha256
    aggregation_policy_fingerprint: Sha256
    retained_cohort_fingerprint: Sha256

    @model_validator(mode="after")
    def exact_grounding_binding(self):
        if self.grounding_fingerprint != self.binding.grounding_fingerprint:
            raise ValueError("Shared TasteFit descriptor grounding differs from full binding")
        return self


class ScopedSharedMemberTargetTasteFit(child.TasteFitContract):
    coordinate: SharedMemberTargetTasteFitCoordinate
    amount: SharedTargetTasteFitAmount

    def scoped_numeric_equal(self, other):
        left, right = type(self).model_validate(self), type(self).model_validate(other)
        if left.coordinate != right.coordinate:
            raise ValueError("Shared TasteFit descriptor mismatch: comparison not defined")
        return left.amount == right.amount


class SharedTasteFitRationalTrace(_Rational):
    coordinate: SharedMemberTargetTasteFitCoordinate
    unit: Literal["MEMBER_INFLUENCE", "MEMBER_INFLUENCE_X_SHARED_TARGET_FIT"]

    @model_validator(mode="after")
    def trace_unit(self):
        if self.unit == "MEMBER_INFLUENCE" and self.numerator <= 0:
            raise ValueError("Weight total must be strictly positive")
        return self


class SharedTasteFitCohortProof(child.TasteFitContract):
    household_id: UUID
    binding: CandidateFeatureBinding
    target: child.PreferenceTarget
    participants: MealParticipants
    tracked_member_id: UUID
    participant_context_fingerprint: Sha256
    integrity_projection_fingerprint: Sha256
    child_identities: tuple[tuple[UUID, Sha256, Sha256, Sha256], ...]


class SharedTasteFitMemberDiagnostic(child.TasteFitContract):
    member_id: UUID
    child_fingerprint: Sha256
    row: child.TasteFitTargetInterpretation
    compatibility: Compatibility
    reasons: tuple[str, ...]


class SharedTasteFitMemberContribution(child.TasteFitContract):
    diagnostic: SharedTasteFitMemberDiagnostic
    selected_bridge: SharedTasteFitBridgeRule | None
    original_value: child.ScopedTargetTasteFit | None
    authored_weight: SharedTasteFitMemberWeight
    common_operand: ScopedSharedMemberTargetTasteFit | None
    weighted_contribution: SharedTasteFitRationalTrace | None


class SharedTasteFitDirectSignalTrace(child.TasteFitContract):
    member_id: UUID
    target: child.PreferenceTarget
    direct_signal: DirectSignal
    declaration_id: UUID | None
    child_fingerprint: Sha256
    row: child.TasteFitTargetInterpretation


class SharedTasteFitCompatibilityDecision(child.TasteFitContract):
    status: Compatibility
    members: tuple[SharedTasteFitMemberDiagnostic, ...]
    compatible_member_ids: tuple[UUID, ...]
    reasons: tuple[str, ...]


class SharedTasteFitCoverage(child.TasteFitContract):
    source_coverage: Literal["COMPLETE"] = "COMPLETE"
    numeric_coverage: Literal["COMPLETE", "INCOMPLETE"]
    required_member_ids: tuple[UUID, ...]
    captured_member_ids: tuple[UUID, ...]
    available_member_ids: tuple[UUID, ...]
    compatible_member_ids: tuple[UUID, ...]
    required_count: Annotated[int, Field(strict=True, gt=0)]
    captured_count: Annotated[int, Field(strict=True, gt=0)]
    available_count: Annotated[int, Field(strict=True, ge=0)]
    compatible_count: Annotated[int, Field(strict=True, ge=0)]


class SharedMemberTargetTasteFitDraft(child.TasteFitContract):
    contract_version: Literal["candidate-shared-member-target-tastefit.v1-draft"] = (
        "candidate-shared-member-target-tastefit.v1-draft"
    )
    sources: SharedMemberTargetTasteFitSources
    cohort: SharedTasteFitCohortProof
    compatibility: SharedTasteFitCompatibilityDecision
    coverage: SharedTasteFitCoverage
    contributions: tuple[SharedTasteFitMemberContribution, ...]
    direct_signals: tuple[SharedTasteFitDirectSignalTrace, ...]
    direct_dislikes: tuple[SharedTasteFitDirectSignalTrace, ...]
    coordinate: SharedMemberTargetTasteFitCoordinate
    value: ScopedSharedMemberTargetTasteFit | None
    weight_total: SharedTasteFitRationalTrace | None
    weighted_total: SharedTasteFitRationalTrace | None
    aggregate_availability: Literal["AVAILABLE", "UNAVAILABLE"]
    reasons: tuple[str, ...]
    operator: Literal["EXACT_POSITIVE_WEIGHTED_MEAN"] = "EXACT_POSITIVE_WEIGHTED_MEAN"
    status: Literal["DERIVED"] = "DERIVED"
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
    cross_target_reduction: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    cross_kind_reduction: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    whole_candidate_scalar: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    candidate_comparison: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    repeat_penalty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    novelty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    learned_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    contextual_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    passive_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False
    fingerprint: Sha256

    @model_validator(mode="after")
    def arithmetic_shape(self):
        available = self.aggregate_availability == "AVAILABLE"
        if available != (self.coverage.numeric_coverage == "COMPLETE"):
            raise ValueError("Availability/coverage mismatch")
        numbers = (self.value, self.weight_total, self.weighted_total)
        numbers += tuple(
            v for c in self.contributions for v in (c.common_operand, c.weighted_contribution)
        )
        if any((n is not None) != available for n in numbers):
            raise ValueError("All new arithmetic is present together or withheld together")
        return self

    def expected_fingerprint(self):
        return shared_tastefit_hash(
            "shared-target.result.v1", self.model_dump(exclude={"fingerprint"})
        )
