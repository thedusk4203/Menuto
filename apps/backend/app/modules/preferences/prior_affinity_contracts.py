"""Exact-target consumer values; no global scalar utility or persistent authority."""

from fractions import Fraction
from math import gcd
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.domain.contracts import Contract, Identifier, Sha256
from app.domain.feature_identity import canonical_bytes, unique_sorted
from app.domain.units import Provenance
from app.modules.preferences.contracts import (
    AffinityValue,
    ExplicitAffinityAmount,
    ExplicitTargetAffinityInput,
    ExplicitTargetAffinityProfileDraft,
    PreferenceTarget,
    TargetKind,
    _profile_content,
    _profile_primitives,
)
from app.modules.preferences.reference_prior_contracts import (
    ReferencePriorAmount,
    ReferencePriorCoordinate,
    ReferencePriorSourceSnapshotDraft,
    ReviewedReferencePriorDraft,
)

KINDS = {"INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"}
AUTHORED_LIMIT = 2_147_483_647
# At most three 31-bit authored denominators participate in the final convex sum.
# 128 bits also accommodate its bounded numerator without rounding/truncation.
DERIVED_LIMIT = (1 << 128) - 1


def consumer_hash(domain, value):
    from hashlib import sha256

    return sha256(canonical_bytes(dict(domain=domain, value=_profile_content(value)))).hexdigest()


class _ConsumerContract(Contract):
    model_config = ConfigDict(revalidate_instances="always")

    @model_validator(mode="before")
    @classmethod
    def recursive_primitives(cls, value):
        return _profile_primitives(value)

    @field_validator(
        "planner_ready",
        "activation_ready",
        "coordinate_version",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def strict_constants(cls, value, info):
        expected = int if info.field_name == "coordinate_version" else bool
        if type(value) is not expected:
            raise ValueError("Strict coordinate version/boolean required")
        return value

    def canonical_json(self):
        return canonical_bytes(_profile_content(self)).decode()


class MemberProfileAffinityCoordinate(_ConsumerContract):
    coordinate_id: Literal["MEMBER_PROFILE_AFFINITY"] = "MEMBER_PROFILE_AFFINITY"
    coordinate_version: Literal[1] = 1
    target_kind: TargetKind
    compatibility_policy_fingerprint: Sha256
    unit: Literal["POLICY_MEMBER_PROFILE_AFFINITY_UNITS"] = "POLICY_MEMBER_PROFILE_AFFINITY_UNITS"
    scope: Literal["ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY"] = (
        "ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY"
    )


class MemberProfileAffinityAmount(_ConsumerContract):
    """Numeric component only. Consumer operations require ScopedMemberProfileAffinity."""

    numerator: Annotated[int, Field(strict=True, ge=-DERIVED_LIMIT, le=DERIVED_LIMIT)]
    denominator: Annotated[int, Field(strict=True, gt=0, le=DERIVED_LIMIT)]

    @model_validator(mode="after")
    def canonical_amount(self):
        if abs(self.numerator) > self.denominator or gcd(self.numerator, self.denominator) != 1:
            raise ValueError("Canonical signed unit rational required")
        return self


class ScopedMemberProfileAffinity(_ConsumerContract):
    coordinate: MemberProfileAffinityCoordinate
    amount: MemberProfileAffinityAmount


def _authored(amount):
    if max(abs(amount.numerator), amount.denominator) > AUTHORED_LIMIT:
        raise ValueError("Authored rational components exceed 31-bit resource bound")


def _fraction(amount):
    return Fraction(amount.numerator, amount.denominator)


class ExplicitProfileMappingRule(_ConsumerContract):
    value: AffinityValue
    expected_explicit_amount: ExplicitAffinityAmount
    output_amount: MemberProfileAffinityAmount

    @field_validator("expected_explicit_amount", "output_amount", mode="before")
    @classmethod
    def bound_serialized_components(cls, value):
        # Frozen ExplicitAffinityAmount reduces on parse. Bound the authored wire
        # components first so oversized multiples cannot hide behind that reduction.
        if isinstance(value, dict):
            for name in ("numerator", "denominator"):
                component = value.get(name)
                if type(component) is int and abs(component) > AUTHORED_LIMIT:
                    raise ValueError("Authored rational components exceed 31-bit resource bound")
        return value

    @model_validator(mode="after")
    def authored_components(self):
        _authored(self.expected_explicit_amount)
        _authored(self.output_amount)
        return self


class ExplicitTargetKindCompatibilityMap(_ConsumerContract):
    target_kind: TargetKind
    rows: Annotated[tuple[ExplicitProfileMappingRule, ...], Field(min_length=3, max_length=3)]

    @model_validator(mode="after")
    def complete_ordered(self):
        rows = unique_sorted(self.rows, key=lambda r: r.value)
        if {r.value for r in rows} != {"DISLIKE", "NEUTRAL", "LIKE"}:
            raise ValueError("Exactly three explicit value mappings required")
        values = {r.value: _fraction(r.output_amount) for r in rows}
        if not values["DISLIKE"] < values["NEUTRAL"] < values["LIKE"]:
            raise ValueError("Mapped DISLIKE < NEUTRAL < LIKE required")
        object.__setattr__(self, "rows", rows)
        return self


class ReferenceProfileMappingRule(_ConsumerContract):
    reference_amount: ReferencePriorAmount
    output_amount: MemberProfileAffinityAmount

    @model_validator(mode="after")
    def authored_components(self):
        _authored(self.output_amount)
        return self


class ReferenceTargetKindCompatibilityMap(_ConsumerContract):
    target_kind: TargetKind
    rows: tuple[ReferenceProfileMappingRule, ...]

    @model_validator(mode="after")
    def finite_ordered(self):
        rows = unique_sorted(self.rows, key=lambda r: _fraction(r.reference_amount))
        if any(
            _fraction(a.output_amount) >= _fraction(b.output_amount) for a, b in zip(rows, rows[1:])
        ):
            raise ValueError("Reference finite lookup must be strictly increasing")
        # Empty groups explicitly mean no compatible reference amount for this kind.
        object.__setattr__(self, "rows", rows)
        return self


class ExactTargetPriorCompatibilityPolicy(_ConsumerContract):
    contract_version: Literal["exact-target-prior-compatibility-policy.v1"] = (
        "exact-target-prior-compatibility-policy.v1"
    )
    policy_id: Identifier
    policy_version: Identifier
    provenance: Provenance
    interpretation_mode: Literal["VERSIONED_CONSUMER_POLICY_REPLAY"] = (
        "VERSIONED_CONSUMER_POLICY_REPLAY"
    )
    explicit_policy_id: Identifier
    explicit_policy_version: Identifier
    explicit_policy_fingerprint: Sha256
    provider_id: UUID
    provider_command_hash: Sha256
    reference_coordinate: ReferencePriorCoordinate
    coordinate_id: Literal["MEMBER_PROFILE_AFFINITY"] = "MEMBER_PROFILE_AFFINITY"
    coordinate_version: Literal[1] = 1
    unit: Literal["POLICY_MEMBER_PROFILE_AFFINITY_UNITS"] = "POLICY_MEMBER_PROFILE_AFFINITY_UNITS"
    scope: Literal["ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY"] = (
        "ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY"
    )
    reference_mapping_mode: Literal["FINITE_EXACT_LOOKUP"] = "FINITE_EXACT_LOOKUP"
    explicit_maps: Annotated[
        tuple[ExplicitTargetKindCompatibilityMap, ...], Field(min_length=5, max_length=5)
    ]
    reference_maps: Annotated[
        tuple[ReferenceTargetKindCompatibilityMap, ...], Field(min_length=5, max_length=5)
    ]

    @model_validator(mode="after")
    def canonical_policy(self):
        if self.provenance.kind != "REVIEWED_REFERENCE":
            raise ValueError("Reviewed compatibility-policy provenance required")
        for field in ("explicit_maps", "reference_maps"):
            rows = unique_sorted(getattr(self, field), key=lambda r: r.target_kind)
            if {r.target_kind for r in rows} != KINDS:
                raise ValueError("Exactly five target-kind mapping groups required")
            object.__setattr__(self, field, rows)
        return self

    def fingerprint(self):
        # Authored body only: descriptors are constructed AFTER hashing this policy.
        return consumer_hash("exact-target-prior-compatibility-policy.v1", self)

    def coordinate_for(self, target_kind):
        policy = type(self).model_validate(self)
        return MemberProfileAffinityCoordinate(
            coordinate_id=policy.coordinate_id,
            coordinate_version=policy.coordinate_version,
            target_kind=target_kind,
            compatibility_policy_fingerprint=policy.fingerprint(),
            unit=policy.unit,
            scope=policy.scope,
        )


class PriorInfluenceWeight(_ConsumerContract):
    numerator: Annotated[int, Field(strict=True, ge=0, le=AUTHORED_LIMIT)]
    denominator: Annotated[int, Field(strict=True, gt=0, le=AUTHORED_LIMIT)]

    @model_validator(mode="after")
    def canonical_weight(self):
        if self.numerator >= self.denominator or gcd(self.numerator, self.denominator) != 1:
            raise ValueError("Canonical active prior influence in [0,1) required")
        return self


class EvidenceStrengthShrinkageRule(_ConsumerContract):
    level: Literal["LOW", "MEDIUM", "HIGH"]
    prior_weight: PriorInfluenceWeight


class ExactTargetShrinkagePolicy(_ConsumerContract):
    contract_version: Literal["exact-target-shrinkage-policy.v1"] = (
        "exact-target-shrinkage-policy.v1"
    )
    policy_id: Identifier
    policy_version: Identifier
    provenance: Provenance
    compatibility_policy_fingerprint: Sha256
    coordinate_id: Literal["MEMBER_PROFILE_AFFINITY"] = "MEMBER_PROFILE_AFFINITY"
    coordinate_version: Literal[1] = 1
    unit: Literal["POLICY_MEMBER_PROFILE_AFFINITY_UNITS"] = "POLICY_MEMBER_PROFILE_AFFINITY_UNITS"
    scope: Literal["ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY"] = (
        "ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY"
    )
    rules: Annotated[tuple[EvidenceStrengthShrinkageRule, ...], Field(min_length=3, max_length=3)]

    @model_validator(mode="after")
    def complete_monotonic(self):
        if self.provenance.kind != "REVIEWED_REFERENCE":
            raise ValueError("Reviewed shrinkage-policy provenance required")
        rules = unique_sorted(self.rules, key=lambda r: r.level)
        weights = {r.level: _fraction(r.prior_weight) for r in rules}
        if set(weights) != {"LOW", "MEDIUM", "HIGH"}:
            raise ValueError("Complete ordinal EvidenceStrength policy required")
        if not weights["LOW"] >= weights["MEDIUM"] >= weights["HIGH"]:
            raise ValueError("Prior influence must be monotonic LOW >= MEDIUM >= HIGH")
        object.__setattr__(self, "rules", rules)
        return self

    def fingerprint(self):
        return consumer_hash("exact-target-shrinkage-policy.v1", self)


class ExactTargetPriorBackedAffinityInput(_ConsumerContract):
    explicit: ExplicitTargetAffinityInput
    reference_source: ReferencePriorSourceSnapshotDraft
    compatibility_policy: ExactTargetPriorCompatibilityPolicy
    shrinkage_policy: ExactTargetShrinkagePolicy

    @model_validator(mode="after")
    def exact_bindings(self):
        explicit, source, policy = self.explicit, self.reference_source, self.compatibility_policy
        targets = explicit.source.request.requested_targets
        if len(targets) != 1 or source.request.requested_targets != targets:
            raise ValueError("Exactly one identical typed target required in both sources")
        from app.modules.preferences.contracts import _profile_hash

        if (
            explicit.policy.policy_id != policy.explicit_policy_id
            or explicit.policy.policy_version != policy.explicit_policy_version
            or _profile_hash(explicit.policy) != policy.explicit_policy_fingerprint
        ):
            raise ValueError("Pinned explicit policy ID/version/fingerprint differs")
        if (
            source.request.provider_id != policy.provider_id
            or source.provider.id != policy.provider_id
            or source.provider.command_hash != policy.provider_command_hash
            or source.request.coordinate != policy.reference_coordinate
            or source.provider.command.coordinate != policy.reference_coordinate
        ):
            raise ValueError("Exact provider command/coordinate binding differs")
        if self.shrinkage_policy.compatibility_policy_fingerprint != policy.fingerprint():
            raise ValueError("Shrinkage compatibility-policy binding differs")
        for field in ("coordinate_id", "coordinate_version", "unit", "scope"):
            if getattr(self.shrinkage_policy, field) != getattr(policy, field):
                raise ValueError("Shrinkage output coordinate family differs")
        # Validate every explicit mapping, including non-requested groups, against the
        # complete pinned source policy. Matching one active amount is insufficient.
        rules = {
            (group.target_kind, row.value): row.amount
            for group in explicit.policy.target_policies
            for row in group.affinity_rules
        }
        for group in policy.explicit_maps:
            for row in group.rows:
                if row.expected_explicit_amount != rules[group.target_kind, row.value]:
                    raise ValueError("Expected explicit mapping amount differs from frozen policy")
        return self


class MappedExplicitProfileAffinity(_ConsumerContract):
    status: Literal["AVAILABLE"] = "AVAILABLE"
    rule_key: tuple[TargetKind, AffinityValue]
    value: ScopedMemberProfileAffinity


class MappedReferenceProfileAffinity(_ConsumerContract):
    status: Literal["AVAILABLE"] = "AVAILABLE"
    rule_key: tuple[TargetKind, ReferencePriorAmount]
    value: ScopedMemberProfileAffinity


class UnavailableReferenceCompatibility(_ConsumerContract):
    status: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    reason: Literal["NO_PUBLICATION", "RETRACTED", "PRIOR_VALUE_NOT_MAPPED"]


class ExactTargetShrinkageContribution(_ConsumerContract):
    side: Literal["EXPLICIT", "PRIOR"]
    weight_numerator: Annotated[int, Field(strict=True, ge=0, le=AUTHORED_LIMIT)]
    weight_denominator: Annotated[int, Field(strict=True, gt=0, le=AUTHORED_LIMIT)]
    value: ScopedMemberProfileAffinity

    @model_validator(mode="after")
    def canonical_coefficient(self):
        n, d = self.weight_numerator, self.weight_denominator
        if n > d or gcd(n, d) != 1:
            raise ValueError("Canonical contribution coefficient in [0,1] required")
        return self


class AvailableExactTargetProfileAffinity(_ConsumerContract):
    status: Literal["AVAILABLE"] = "AVAILABLE"
    mode: Literal["BLENDED_EXPLICIT_AND_PRIOR", "EXPLICIT_ONLY", "PRIOR_ONLY_COLD_START"]
    value: ScopedMemberProfileAffinity


class UnavailableExactTargetProfileAffinity(_ConsumerContract):
    status: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    reason: Literal["MEMBER_RETRACTED", "NO_EXPLICIT_OR_COMPATIBLE_PRIOR"]


class ExactTargetPriorBackedAffinityDraft(_ConsumerContract):
    contract_version: Literal["exact-target-prior-backed-affinity.v1-draft"] = (
        "exact-target-prior-backed-affinity.v1-draft"
    )
    subject: ExactTargetPriorBackedAffinityInput
    household_id: UUID
    member_id: UUID
    target: PreferenceTarget
    target_kind: TargetKind
    coordinate: MemberProfileAffinityCoordinate
    explicit_profile: ExplicitTargetAffinityProfileDraft
    reviewed_prior: ReviewedReferencePriorDraft
    mapped_explicit: MappedExplicitProfileAffinity | None
    mapped_prior: Annotated[
        MappedReferenceProfileAffinity | UnavailableReferenceCompatibility,
        Field(discriminator="status"),
    ]
    shrinkage: Literal["APPLIED", "NOT_APPLIED"]
    contributions: tuple[ExactTargetShrinkageContribution, ...]
    effective: Annotated[
        AvailableExactTargetProfileAffinity | UnavailableExactTargetProfileAffinity,
        Field(discriminator="status"),
    ]
    compatibility_policy_fingerprint: Sha256
    shrinkage_policy_fingerprint: Sha256
    fingerprint: Sha256
    coverage: Literal["ONE_MEMBER_ONE_EXACT_TARGET_PRIOR_BACKED_ONLY"] = (
        "ONE_MEMBER_ONE_EXACT_TARGET_PRIOR_BACKED_ONLY"
    )
    interpretation_mode: Literal["VERSIONED_CONSUMER_POLICY_REPLAY"] = (
        "VERSIONED_CONSUMER_POLICY_REPLAY"
    )
    member_owner: Literal["PRESERVED"] = "PRESERVED"
    explicit_evidence_strength: Literal["PRESERVED_NOT_MODIFIED"] = "PRESERVED_NOT_MODIFIED"
    learned_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    contextual_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    passive_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    cross_target_inference: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    hierarchical_inference: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    provider_aggregation: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    candidate_aggregation: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    taste_fit: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False

    def expected_fingerprint(self):
        body = _profile_content(self)
        del body["fingerprint"]
        return consumer_hash("exact-target-prior-backed-affinity.v1", body)

    @model_validator(mode="after")
    def recompute(self):
        from app.modules.preferences.prior_affinity import _derive_fields

        expected = _derive_fields(self.subject)
        for name, value in expected.items():
            if getattr(self, name) != value:
                raise ValueError("Consumer result differs from primitive replay: " + name)
        if self.fingerprint != self.expected_fingerprint():
            raise ValueError("Consumer fingerprint differs from primitive replay")
        return self
