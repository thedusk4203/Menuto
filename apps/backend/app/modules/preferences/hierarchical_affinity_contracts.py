"""One-hop member interpretation values; no durable learning or planner authority."""

from math import gcd
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.domain.contracts import Contract, Sha256
from app.domain.feature_identity import canonical
from app.modules.preferences.contracts import AffinityValue, PreferenceTarget, TargetKind
from app.modules.preferences.hierarchy_contracts import (
    HierarchyPolicyAmount,
    HierarchySourceReason,
    HierarchySourceSnapshotDraft,
    HierarchyStreamIdentity,
    HierarchyTransferMapRow,
    ReviewedHierarchySourceDraft,
    hierarchy_hash,
)
from app.modules.preferences.prior_affinity_contracts import (
    ExactTargetPriorBackedAffinityDraft,
    ExactTargetPriorBackedAffinityInput,
    ScopedMemberProfileAffinity,
)

DERIVED_LIMIT = (1 << 128) - 1


class _OneHopContract(Contract):
    model_config = ConfigDict(revalidate_instances="always")

    @model_validator(mode="before")
    @classmethod
    def primitives(cls, value):
        return canonical(value)

    @field_validator(
        "coordinate_version", "planner_ready", "activation_ready", mode="before", check_fields=False
    )
    @classmethod
    def strict_constants(cls, value, info):
        expected = int if info.field_name == "coordinate_version" else bool
        if type(value) is not expected:
            raise ValueError("Strict coordinate version/boolean required")
        return value


class OneHopHierarchicalMemberPreferenceInput(_OneHopContract):
    destination: ExactTargetPriorBackedAffinityInput
    parent: ExactTargetPriorBackedAffinityInput | None = None
    hierarchy_source: HierarchySourceSnapshotDraft


class InheritedMemberPreferenceCoordinate(_OneHopContract):
    coordinate_id: Literal["INHERITED_MEMBER_PREFERENCE"] = "INHERITED_MEMBER_PREFERENCE"
    coordinate_version: Literal[1] = 1
    destination_target_kind: TargetKind
    transfer_policy_semantic_fingerprint: Sha256
    unit: Literal["REVIEWED_TRANSFER_POLICY_UNITS"] = "REVIEWED_TRANSFER_POLICY_UNITS"
    scope: Literal["ONE_TRANSFER_POLICY_ONE_DESTINATION_KIND_BOUND_EXACT_RELATION"] = (
        "ONE_TRANSFER_POLICY_ONE_DESTINATION_KIND_BOUND_EXACT_RELATION"
    )


class InheritedMemberPreferenceAmount(_OneHopContract):
    numerator: Annotated[int, Field(strict=True, ge=-DERIVED_LIMIT, le=DERIVED_LIMIT)]
    denominator: Annotated[int, Field(strict=True, gt=0, le=DERIVED_LIMIT)]

    @model_validator(mode="after")
    def canonical_amount(self):
        if abs(self.numerator) > self.denominator or gcd(self.numerator, self.denominator) != 1:
            raise ValueError("Canonical signed unit rational required")
        return self


class ScopedInheritedMemberPreference(_OneHopContract):
    coordinate: InheritedMemberPreferenceCoordinate
    amount: InheritedMemberPreferenceAmount


class InheritedPreferenceTrace(_OneHopContract):
    provider_id: UUID
    policy_stream_id: UUID
    policy_revision_id: UUID
    relation_stream_id: UUID
    relation_revision_id: UUID
    relation_identity: HierarchyStreamIdentity
    semantic_state: AffinityValue
    mapped_explicit: ScopedMemberProfileAffinity
    mapping_row: HierarchyTransferMapRow
    mapped_inherited: ScopedInheritedMemberPreference
    attenuation: HierarchyPolicyAmount
    product: ScopedInheritedMemberPreference

    @model_validator(mode="after")
    def local_bindings(self):
        identity, row = self.relation_identity, self.mapping_row
        if (
            identity.kind != "RELATION"
            or identity.source.kind != self.mapped_explicit.coordinate.target_kind
            or identity.destination.kind != self.product.coordinate.destination_target_kind
            or row.source_affinity_value != self.semantic_state
            or row.source_descriptor != self.mapped_explicit.coordinate
            or self.mapped_inherited.coordinate != self.product.coordinate
            or self.mapped_inherited.amount.model_dump() != row.output_amount.model_dump()
            or self.attenuation.numerator <= 0
        ):
            raise ValueError("Inherited trace descriptor/semantic binding differs")
        # Local shape validation is not publication authority: root replay must
        # still select this exact row/coefficient from complete source primitives.
        # Do not perform transfer arithmetic while parsing an untrusted cached
        # trace. Complete root replay verifies the published descriptor first.
        return self


class AvailableInheritedMemberPreference(_OneHopContract):
    status: Literal["AVAILABLE"] = "AVAILABLE"
    value: ScopedInheritedMemberPreference
    trace: InheritedPreferenceTrace

    @model_validator(mode="after")
    def exact_trace_value(self):
        if self.value != self.trace.product:
            raise ValueError("Inherited value differs from traced scoped product")
        return self


class SuppressedInheritedMemberPreference(_OneHopContract):
    status: Literal["SUPPRESSED"] = "SUPPRESSED"
    reason: Literal["MEMBER_RETRACTED", "DESTINATION_DIRECT_DECLARATION"]


class UnavailableInheritedMemberPreference(_OneHopContract):
    status: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    reason: Literal[
        "HIERARCHY_SOURCE_UNAVAILABLE",
        "PARENT_MEMBER_RETRACTED",
        "PARENT_PRIOR_ONLY_COLD_START",
        "PARENT_UNDECLARED",
        "INCOMPATIBLE_COORDINATE",
        "SOURCE_VALUE_NOT_MAPPED",
    ]
    source_reason: HierarchySourceReason | None = None

    @model_validator(mode="after")
    def source_reason_binding(self):
        if (self.reason == "HIERARCHY_SOURCE_UNAVAILABLE") != (self.source_reason is not None):
            raise ValueError("Exact frozen source reason required iff hierarchy unavailable")
        return self


class OneHopHierarchicalMemberPreferenceDraft(_OneHopContract):
    contract_version: Literal["one-hop-hierarchical-member-preference.v1-draft"] = (
        "one-hop-hierarchical-member-preference.v1-draft"
    )
    subject: OneHopHierarchicalMemberPreferenceInput
    household_id: UUID
    member_id: UUID
    destination_target: PreferenceTarget
    parent_target: PreferenceTarget | None
    destination_exact_target: ExactTargetPriorBackedAffinityDraft
    parent_exact_target: ExactTargetPriorBackedAffinityDraft | None
    hierarchy: ReviewedHierarchySourceDraft
    member_ledger_fingerprint: Sha256
    inherited: Annotated[
        AvailableInheritedMemberPreference
        | SuppressedInheritedMemberPreference
        | UnavailableInheritedMemberPreference,
        Field(discriminator="status"),
    ]
    fingerprint: Sha256
    coverage: Literal["ONE_MEMBER_ONE_DESTINATION_ONE_HOP_ONLY"] = (
        "ONE_MEMBER_ONE_DESTINATION_ONE_HOP_ONLY"
    )
    interpretation_mode: Literal["VERSIONED_CONSUMER_POLICY_REPLAY"] = (
        "VERSIONED_CONSUMER_POLICY_REPLAY"
    )
    member_owner: Literal["PRESERVED"] = "PRESERVED"
    evidence_strength: Literal["NOT_DERIVED"] = "NOT_DERIVED"
    learned_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    contextual_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    passive_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    recursive_transfer: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    parent_aggregation: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    candidate_aggregation: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    taste_fit: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False

    def expected_fingerprint(self):
        body = canonical(self)
        del body["fingerprint"]
        return hierarchy_hash("member-preference.one-hop-result.v1", body)

    @model_validator(mode="after")
    def primitive_replay(self):
        from app.modules.preferences.hierarchical_affinity import _derive_fields

        for name, value in _derive_fields(self.subject, claimed=self.inherited).items():
            if getattr(self, name) != value:
                raise ValueError("One-hop result differs from primitive replay: " + name)
        if self.fingerprint != self.expected_fingerprint():
            raise ValueError("One-hop fingerprint differs from complete primitive replay")
        return self
