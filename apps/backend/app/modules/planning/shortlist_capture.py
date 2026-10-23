"""Canonical ingress; capture first, pure shortlist second. No serialized candidate ingress."""

from app.modules.planning.contracts import CandidateGroundingRequest, ShortlistPolicyDraft
from app.modules.planning.grounding_capture import ground_candidate
from app.modules.planning.shortlist import _captured_pool, _digest, _result, shortlist_grounded_pool


def capture_shortlist_pool(session, requests):
    requests = tuple(CandidateGroundingRequest.model_validate(q.model_dump()) for q in requests)
    return _captured_pool((q, ground_candidate(session, q)) for q in requests)


def build_pareto_shortlist(session, requests, policy):
    """Only caller selection IDs/culinary demand enter canonical grounding, not claimed metrics."""
    policy = ShortlistPolicyDraft.model_validate(policy.model_dump())
    requests = tuple(CandidateGroundingRequest.model_validate(q.model_dump()) for q in requests)
    if len(requests) > policy.max_inputs:
        from app.modules.planning.contracts import grounding_canonical_json

        return _result(
            policy=policy,
            identity=_digest(
                sorted({grounding_canonical_json(q.model_dump(mode="json")) for q in requests})
            ),
            status="INPUT_LIMIT_EXCEEDED",
        )
    return shortlist_grounded_pool(capture_shortlist_pool(session, requests), policy)
