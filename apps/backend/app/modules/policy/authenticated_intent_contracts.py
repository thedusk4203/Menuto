"""Policy-owned, non-admitting inspection of fresh Identity and frozen EPI evidence."""

from typing import Literal

from pydantic import ConfigDict, model_validator

from app.domain.contracts import Contract, Sha256
from app.modules.identity.source_contracts import (
    IdentityCaptureFailureV1,
    IdentitySourceCheckV1,
    IdentitySourceSnapshotV1,
)
from app.modules.policy.explicit_intent_contracts import PlanIntentCheckV1, PlanIntentResolutionV1


class AuthenticatedPlanIntentInspectionV1(Contract):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        validate_default=True,
        revalidate_instances="always",
    )
    version: Literal[1]
    source: IdentitySourceSnapshotV1 | None
    source_failure: IdentityCaptureFailureV1 | None
    source_check: IdentitySourceCheckV1 | None
    intent_result: PlanIntentResolutionV1 | None
    intent_check: PlanIntentCheckV1 | None
    outcome: Literal["SOURCE_AND_INTENT_CONSISTENT", "UNAVAILABLE", "REJECTED"]
    reason: Literal[
        "INSPECTION_COMPLETE",
        "SOURCE_NON_SUCCESS",
        "INTENT_NON_SUCCESS",
        "INDEPENDENT_INCONSISTENCY",
    ]
    inspection_fingerprint: Sha256
    environment: Literal["TEST_ONLY"]
    transport: Literal["UNVERIFIED_TRANSPORT"]
    numerical_use: Literal["NOT_ADMITTED"]
    resolved_plan_policy_ready: Literal[False]
    planner_ready: Literal[False]
    activation_ready: Literal[False]

    @model_validator(mode="before")
    @classmethod
    def strict_flags(cls, value):
        if type(value) is dict:
            if "version" in value and (type(value["version"]) is not int or value["version"] != 1):
                raise ValueError("Unsupported inspection version")
            for flag in ("resolved_plan_policy_ready", "planner_ready", "activation_ready"):
                if flag in value and (type(value[flag]) is not bool or value[flag]):
                    raise ValueError("Non-authorizing inspection required")
        return value
