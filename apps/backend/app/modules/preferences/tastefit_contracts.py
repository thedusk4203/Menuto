"""Additive member-source transport. No candidate interpretation or preference writes."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, Sha256
from app.domain.feature_identity import canonical, canonical_bytes, identity_hash, unique_sorted
from app.modules.catalog.contracts import AffinityFeatureTermFact
from app.modules.preferences.contracts import (
    DerivedTargetAffinity,
    ExplicitTargetAffinityInput,
    ExplicitTargetAffinityPolicy,
    PreferenceTarget,
    _profile_hash,
    preference_target_key,
)
from app.modules.preferences.hierarchical_affinity_contracts import (
    InheritedMemberPreferenceCoordinate,
    OneHopHierarchicalMemberPreferenceDraft,
    OneHopHierarchicalMemberPreferenceInput,
)
from app.modules.preferences.hierarchy_contracts import HierarchyTransferPolicy
from app.modules.preferences.prior_affinity_contracts import (
    ExactTargetPriorBackedAffinityDraft,
    ExactTargetPriorBackedAffinityInput,
    ExactTargetPriorCompatibilityPolicy,
    ExactTargetShrinkagePolicy,
    MemberProfileAffinityCoordinate,
)
from app.modules.recipes.contracts import RecipeFact, RecipeVersionSnapshot

# The two frozen coordinate types are intentionally exposed by this new immutable
# companion, without changing the frozen contracts.py surface or serialization.
__all__ = ["MemberProfileAffinityCoordinate", "InheritedMemberPreferenceCoordinate"]

CaptureMode = Literal["EXPLICIT_ONLY", "EXACT_TARGET", "EXACT_TARGET_AND_ONE_HOP"]


def tastefit_hash(domain, value):
    return identity_hash(dict(domain=domain, value=value))


class TasteFitContract(Contract):
    model_config = ConfigDict(revalidate_instances="always")

    @model_validator(mode="before")
    @classmethod
    def recursive_primitives(cls, value):
        return canonical(value)

    @field_validator(
        "planner_ready",
        "activation_ready",
        "coordinate_version",
        "wrapper_version",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def strict_literals(cls, value, info):
        expected = bool if info.field_name.endswith("ready") else int
        if type(value) is not expected:
            raise ValueError("Strict boolean/integer literal required")
        return value


class TasteFitMemberInterpretationPlan(TasteFitContract):
    explicit_policy: ExplicitTargetAffinityPolicy
    expected_explicit_policy_id: Identifier
    expected_explicit_policy_version: Identifier
    expected_explicit_policy_fingerprint: Sha256
    compatibility_policy: ExactTargetPriorCompatibilityPolicy | None
    expected_compatibility_policy_fingerprint: Sha256 | None
    shrinkage_policy: ExactTargetShrinkagePolicy | None
    expected_shrinkage_policy_fingerprint: Sha256 | None
    hierarchy_provider_id: UUID | None
    hierarchy_provider_command_hash: Sha256 | None
    hierarchy_policy: HierarchyTransferPolicy | None
    expected_hierarchy_policy_fingerprint: Sha256 | None

    @model_validator(mode="after")
    def bindings(self):
        p = self.explicit_policy
        if (p.policy_id, p.policy_version, _profile_hash(p)) != (
            self.expected_explicit_policy_id,
            self.expected_explicit_policy_version,
            self.expected_explicit_policy_fingerprint,
        ):
            raise ValueError("SOURCE_POLICY_BINDING_MISMATCH: explicit policy pins")
        c, s = self.compatibility_policy, self.shrinkage_policy
        if (c is None) != (s is None):
            raise ValueError("Compatibility and shrinkage bodies required together")
        if c is None:
            if any(
                v is not None
                for v in (
                    self.expected_compatibility_policy_fingerprint,
                    self.expected_shrinkage_policy_fingerprint,
                )
            ):
                raise ValueError("Detached exact-target policy pins")
        elif (
            c.fingerprint() != self.expected_compatibility_policy_fingerprint
            or s.fingerprint() != self.expected_shrinkage_policy_fingerprint
            or s.compatibility_policy_fingerprint != c.fingerprint()
            or (c.explicit_policy_id, c.explicit_policy_version, c.explicit_policy_fingerprint)
            != (p.policy_id, p.policy_version, _profile_hash(p))
        ):
            raise ValueError("SOURCE_POLICY_BINDING_MISMATCH: exact-target policy pins")
        h = self.hierarchy_policy
        selectors = (
            self.hierarchy_provider_id,
            self.hierarchy_provider_command_hash,
            self.expected_hierarchy_policy_fingerprint,
        )
        if h is None:
            if any(v is not None for v in selectors):
                raise ValueError("Detached hierarchy policy pins")
        elif (
            any(v is None for v in selectors)
            or h.fingerprint() != self.expected_hierarchy_policy_fingerprint
            or h.explicit_policy != p
            or h.compatibility_policy != c
        ):
            raise ValueError("SOURCE_POLICY_BINDING_MISMATCH: hierarchy policy pins")
        return self


class TasteFitMemberTargetPlan(TasteFitContract):
    target: PreferenceTarget
    capture_mode: CaptureMode


class TasteFitMemberCapturePlan(TasteFitContract):
    household_id: UUID
    member_id: UUID
    interpretation: TasteFitMemberInterpretationPlan
    targets: tuple[TasteFitMemberTargetPlan, ...]
    candidate_recipe: RecipeVersionSnapshot

    @model_validator(mode="after")
    def target_set(self):
        rows = unique_sorted(self.targets, key=lambda r: preference_target_key(r.target))
        object.__setattr__(self, "targets", rows)
        for row in rows:
            if (
                row.capture_mode != "EXPLICIT_ONLY"
                and self.interpretation.compatibility_policy is None
            ):
                raise ValueError("Exact-target capture needs pinned policies/provider")
            if row.capture_mode == "EXACT_TARGET_AND_ONE_HOP" and (
                self.interpretation.hierarchy_policy is None
            ):
                raise ValueError("Hierarchy capture needs pinned provider/policy")
        return self


class TasteFitCaptureFrame(TasteFitContract):
    owner: Literal["CANDIDATE", "MEMBER", "PRIOR", "HIERARCHY"]
    actor_user_id: UUID
    targets: tuple[PreferenceTarget, ...]
    configured_host: str
    configured_port: Annotated[int, Field(strict=True, gt=0)]
    database_name: str
    database_oid: Annotated[int, Field(strict=True, gt=0)]
    server_address: str
    server_port: Annotated[int, Field(strict=True, gt=0)]
    session_user: str
    isolation: Literal["REPEATABLE READ", "SERIALIZABLE"]
    read_only: Literal[True]
    started_at: AwareTime
    completed_at: AwareTime

    @field_validator("read_only", mode="before")
    @classmethod
    def strict_read_only(cls, value):
        if type(value) is not bool:
            raise ValueError("Strict boolean required")
        return value

    @model_validator(mode="after")
    def frame(self):
        object.__setattr__(self, "targets", unique_sorted(self.targets, key=preference_target_key))
        if self.started_at > self.completed_at:
            raise ValueError("Owner capture clock regression")
        if not all(
            (self.configured_host, self.database_name, self.server_address, self.session_user)
        ):
            raise ValueError("Nonsecret canonical connection identity required")
        return self


class TasteFitMemberSourceEntry(TasteFitContract):
    target: PreferenceTarget
    explicit: ExplicitTargetAffinityInput
    exact_target: ExactTargetPriorBackedAffinityInput | None
    one_hop: OneHopHierarchicalMemberPreferenceInput | None


class TasteFitMemberSourceBundle(TasteFitContract):
    plan: TasteFitMemberCapturePlan
    entries: tuple[TasteFitMemberSourceEntry, ...]
    frames: tuple[TasteFitCaptureFrame, ...]

    @model_validator(mode="after")
    def source_sets(self):
        object.__setattr__(
            self,
            "entries",
            unique_sorted(self.entries, key=lambda r: preference_target_key(r.target)),
        )
        object.__setattr__(self, "frames", unique_sorted(self.frames, key=lambda f: f.owner))
        return self


class TasteFitMemberView(TasteFitContract):
    target: PreferenceTarget
    explicit: DerivedTargetAffinity
    exact_target: ExactTargetPriorBackedAffinityDraft | None
    one_hop: OneHopHierarchicalMemberPreferenceDraft | None


def member_ledger_body(snapshot):
    body = canonical(snapshot)
    body.pop("captured_at")
    body["declarations"].sort(key=lambda d: d["member_sequence"])
    body["feature_terms"].sort(key=lambda t: t["id"])
    return body


def check_tastefit_immutable_facts(*roots):
    """Only immutable typed owner facts, never mutable ingredient display labels."""
    seen = {}

    def visit(value):
        if isinstance(value, (AffinityFeatureTermFact, RecipeFact, RecipeVersionSnapshot)):
            key, body = (type(value), value.id), canonical_bytes(value)
            if key in seen and seen[key] != body:
                raise ValueError("SOURCE_CUT_INCOHERENT: conflicting immutable owner fact")
            seen[key] = body
        if isinstance(value, BaseModel):
            for name in type(value).model_fields:
                visit(getattr(value, name))
        elif isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, (tuple, list)):
            for child in value:
                visit(child)

    for root in roots:
        visit(root)


def check_tastefit_frames(frames):
    """Offline agreement only, not proof of deployment/authentication or common MVCC."""
    keys = {
        (
            f.configured_host,
            f.configured_port,
            f.database_name,
            f.database_oid,
            f.server_address,
            f.server_port,
        )
        for f in frames
    }
    if len(keys) != 1 or len({f.actor_user_id for f in frames}) != 1:
        raise ValueError("SOURCE_CUT_INCOHERENT: connection/actor frame mismatch")
