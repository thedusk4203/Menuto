"""Actual owner writes/capture; synthetic explicit policies remain test-only inputs."""

from app.domain.feature_identity import canonical_bytes
from app.modules.households.contracts import MealParticipants
from app.modules.planning import tastefit_contracts as child
from app.modules.planning.shared_target_tastefit_public import (
    capture_shared_member_target_tastefit_sources,
)
from app.modules.planning.tastefit_public import derive_candidate_member_tastefit
from app.modules.preferences.contracts import FeaturePreferenceTarget
from shared_target_tastefit_fixtures import shared_request
from tastefit_fixtures import request
from tastefit_postgres_fixtures import author_current_mapping, capture, declare, prepare, sessions
from test_postgres_candidate_member_tastefit import add_member, rebind_grounding


def group(s, *, count=2, kind="PROTEIN", states=None):
    g = s["request"].projection_request.grounding_request
    ids = [g.tracked_member_id] + [add_member(s) for _ in range(count - 1)]
    g = g.model_copy(
        update=dict(
            participants=MealParticipants(
                participants=g.participants.participants
                + tuple(
                    dict(member_id=mid, portion_factor="0.5", nutrition_role="SHARED")
                    for mid in ids[1:]
                )
            )
        )
    )
    s = dict(s, request=rebind_grounding(s, g))
    first = capture(s, prior=bool(s.get("prior_provider")), hierarchy=bool(s.get("hierarchy")))
    target = next((e.target for e in first.member_sources.entries if e.target.kind == kind), None)
    if target is None:
        dim = "MAIN_PROTEIN" if kind == "PROTEIN" else kind
        target = FeaturePreferenceTarget(kind=kind, feature_term_id=s["terms"][dim][0].id)
    s.update(ids=tuple(ids), target=target)
    if states is not None:
        for mid, value in zip(ids, states, strict=True):
            if value != "UNDECLARED":
                declare_for(s, mid, target, value=value)
    s["requests"] = tuple(
        request(
            s["request"].projection_request,
            s["request"].member_interpretation,
            s["request"].policy,
            member_id=mid,
            probes=(target,),
        )
        for mid in ids
    )
    return s


def prepared_group(server, *, kind="PROTEIN", states=("LIKE", "DISLIKE"), **kw):
    return group(prepare(server, **kw), count=len(states), kind=kind, states=states)


def declare_for(s, member, target, **kw):
    return declare(
        dict(s, request=s["request"].model_copy(update=dict(member_id=member))),
        target,
        authorship="SELF" if member == s["ids"][0] else "AUTHORIZED_REPRESENTATIVE",
        **kw,
    )


def root_request(s, policy=None):
    return shared_request((), s["target"], policy, child_requests=s["requests"])


def shared_capture(s, *, q=None, **kw):
    with sessions(
        s, prior=bool(s.get("prior_provider")), hierarchy=bool(s.get("hierarchy")), **kw
    ) as cuts:
        return capture_shared_member_target_tastefit_sources(
            cuts, q or root_request(s), actor_user_id=s["actor"]
        )


def author_for_members(s):
    policies = []
    for mid in s["ids"]:
        configured = dict(s, request=s["request"].model_copy(update=dict(member_id=mid)))
        current = author_current_mapping(
            configured, prior=bool(s.get("prior_provider")), hierarchy=bool(s.get("hierarchy"))
        )
        policies.append(current["request"].policy)
    body = policies[0].model_dump()
    for group in body["kind_policies"]:
        rows = [
            r
            for p in policies
            for g in p.kind_policies
            if g.target_kind == group["target_kind"]
            for r in g.mappings
        ]
        group["mappings"] = tuple({canonical_bytes(r): r for r in rows}.values())
    policy = child.TasteFitInterpretationPolicy.model_validate(body)
    requests = tuple(
        request(
            q.projection_request,
            q.member_interpretation,
            policy,
            member_id=q.member_id,
            probes=q.diagnostic_targets,
        )
        for q in s["requests"]
    )
    return dict(s, requests=requests)


def child_results(s):
    return tuple(
        derive_candidate_member_tastefit(
            capture(s, q=q, prior=bool(s.get("prior_provider")), hierarchy=bool(s.get("hierarchy")))
        )
        for q in s["requests"]
    )
