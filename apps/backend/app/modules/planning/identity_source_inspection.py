"""Fresh source inspection only; no report, source, callback, lease or numerical admission."""

import hashlib
import json

from app.modules.identity.source_capture import capture_identity_request_source_v1
from app.modules.identity.source_contracts import IdentityCaptureFailureV1
from app.modules.policy.authenticated_intent_contracts import AuthenticatedPlanIntentInspectionV1
from app.modules.policy.explicit_intent_public import resolve_explicit_plan_intent_v1
from app.modules.validation.explicit_plan_intent import check_explicit_plan_intent_v1
from app.modules.validation.identity_source import check_identity_source_v1


def inspect_authenticated_explicit_plan_intent_v1(connection, request_binding, *, context):
    source = capture_identity_request_source_v1(connection, request_binding, context=context)
    failure = source if type(source) is IdentityCaptureFailureV1 else None
    retained = None if failure is not None else source
    source_check = check_identity_source_v1(source, request_binding)
    result = intent_check = None
    outcome, reason = "UNAVAILABLE", "SOURCE_NON_SUCCESS"
    if (
        retained is not None
        and source_check.decision == "CONSISTENT"
        and (source_check.reconstructed_outcome == "AVAILABLE_AT_RETAINED_CUT")
    ):
        raw_request = retained.binding.request_utf8.encode("utf-8", "strict")
        result = resolve_explicit_plan_intent_v1(raw_request)
        intent_check = check_explicit_plan_intent_v1(raw_request, result)
        if intent_check.decision != "CONSISTENT":
            outcome, reason = "REJECTED", "INDEPENDENT_INCONSISTENCY"
        elif result.outcome != "AVAILABLE_TEST_ONLY":
            reason = "INTENT_NON_SUCCESS"
        else:
            outcome, reason = "SOURCE_AND_INTENT_CONSISTENT", "INSPECTION_COMPLETE"
    elif retained is not None and source_check.decision != "CONSISTENT":
        outcome, reason = "REJECTED", "INDEPENDENT_INCONSISTENCY"
    data = dict(
        version=1,
        source=retained,
        source_failure=failure,
        source_check=source_check,
        intent_result=result,
        intent_check=intent_check,
        outcome=outcome,
        reason=reason,
        environment="TEST_ONLY",
        transport="UNVERIFIED_TRANSPORT",
        numerical_use="NOT_ADMITTED",
        resolved_plan_policy_ready=False,
        planner_ready=False,
        activation_ready=False,
    )
    # Contracts provide immutable transport; this digest makes no source-origin claim.
    carrier = AuthenticatedPlanIntentInspectionV1(**data, inspection_fingerprint="0" * 64)
    preimage = carrier.model_dump(mode="json", exclude={"inspection_fingerprint"})
    encoded = json.dumps(
        preimage, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = hashlib.sha256(b"policy.identity-inspection.v1\x00" + encoded).hexdigest()
    return AuthenticatedPlanIntentInspectionV1(**data, inspection_fingerprint=digest)
