"""Authored disposable test policies; never imported by production modules."""

from datetime import timedelta
from uuid import uuid4

from app.domain.feature_identity import canonical
from app.modules.households.contracts import HouseholdMemberIdentity, MealParticipants
from app.modules.nutrition.contracts import CanonicalMemberSafetySnapshot
from app.modules.planning import shared_target_tastefit_contracts as c
from app.modules.planning import tastefit_contracts as child
from app.modules.planning.tastefit_public import derive_candidate_member_tastefit
from app.modules.preferences.contracts import (
    RetractMemberPreferenceCommand,
    SetMemberPreferenceCommand,
)
from candidate_feature_fixtures import make_subject
from grounding_fixtures import setup
from preference_fixtures import provenance
from tastefit_fixtures import make_sources, seal, with_policy


def admission(policy):
    return c.SharedTasteFitPolicyAdmission(
        policy=policy,
        expected_policy_id=policy.policy_id,
        expected_policy_version=policy.policy_version,
        expected_policy_fingerprint=policy.fingerprint(),
    )


def authored_policy(
    children, target, *, weights=None, admissions=None, child_requests=None, **changes
):
    requests = child_requests or tuple(ch.sources.request for ch in children)
    policies = {q.policy.fingerprint(): q.policy for q in requests}
    admitted = tuple(admission(p) for p in policies.values()) if admissions is None else admissions
    rules = []
    for a in admitted:
        group = next(g for g in a.policy.kind_policies if g.target_kind == target.kind)
        for mapping in group.mappings:
            sign = (mapping.fit_amount.numerator > 0) - (mapping.fit_amount.numerator < 0)
            # Independently authored finite test policy, deliberately not an identity bridge.
            mapped = {1: (2, 3), -1: (-1, 3), 0: (0, 1)}[sign]
            rules.append(
                c.SharedTasteFitBridgeRule(
                    rule_id="synthetic.bridge." + str(len(rules)),
                    admission=a,
                    target_kind=target.kind,
                    mapping=mapping,
                    direct_signal=(
                        "DECLARED_" + mapping.semantic_state
                        if mapping.source_mode in {"RAW_EXPLICIT", "EXACT_TARGET_EFFECTIVE"}
                        else "NONE"
                    ),
                    mapped_amount=dict(numerator=mapped[0], denominator=mapped[1]),
                )
            )
    ids = sorted((q.member_id for q in requests), key=str)
    return c.SharedMemberTargetTasteFitPolicy.model_validate(
        dict(
            contract_version="candidate-shared-member-target-tastefit-policy.v1",
            policy_id="synthetic.shared.fit",
            policy_version="1",
            provenance=provenance(),
            interpretation_mode="VERSIONED_CONSUMER_POLICY_REPLAY",
            target_kind=target.kind,
            participant_scope="EXACT_CANONICAL_PARTICIPANTS",
            compatibility="FINITE_PINNED_CHILD_MAPPING_BRIDGES",
            policy_admissions=admitted,
            bridge_rules=rules,
            member_weights=tuple(
                dict(
                    member_id=mid,
                    weight=dict(
                        numerator=(weights or {}).get(mid, 2 if i == 0 else 1), denominator=1
                    ),
                )
                for i, mid in enumerate(ids)
            ),
            operator="EXACT_POSITIVE_WEIGHTED_MEAN",
            incomplete_coverage="WITHHOLD_AGGREGATE",
            direct_signal_effect="RETAIN_SEPARATELY_NO_IMPLICIT_VETO_OR_WEIGHT",
            evidence_strength_effect="LINEAGE_ONLY",
            max_members=100,
            max_policy_bytes=20000000,
            max_source_bytes=100000000,
            max_result_bytes=200000000,
            max_integer_bits=256,
        )
        | changes
    )


def shared_request(children, target, policy=None, *, child_requests=None):
    requests = child_requests or tuple(ch.sources.request for ch in children)
    policy = policy or authored_policy(children, target, child_requests=requests)
    first = requests[0]
    return c.SharedMemberTargetTasteFitRequest(
        household_id=first.household_id,
        projection_request=first.projection_request,
        target=target,
        members=tuple(
            c.SharedTasteFitMemberInput(
                **admission(q.policy).model_dump(),
                member_id=q.member_id,
                member_interpretation=q.member_interpretation,
            )
            for q in requests
        ),
        projection_mode="FRESH_CANONICAL_CHILD_CAPTURE",
        policy=policy,
        expected_policy_id=policy.policy_id,
        expected_policy_version=policy.policy_version,
        expected_policy_fingerprint=policy.fingerprint(),
    )


def pack(children, target, policy=None, request=None):
    children = tuple(sorted(children, key=lambda ch: str(ch.subject.member_id)))
    request = request or shared_request(children, target, policy)
    source = c.SharedMemberTargetTasteFitSources(
        request=request,
        children=children,
        owner_frames=tuple(
            (ch.subject.member_id, (ch.sources.candidate_frame,) + ch.sources.member_sources.frames)
            for ch in children
        ),
        capture_started_at=min(ch.sources.capture_started_at for ch in children)
        - timedelta(seconds=1),
        capture_completed_at=max(ch.sources.capture_completed_at for ch in children)
        + timedelta(seconds=1),
        fingerprint="0" * 64,
    )
    return reseal(source)


def reseal(source):
    return source.model_copy(update=dict(fingerprint=source.expected_fingerprint()))


def replace_policy(source, policy):
    body = source.request.model_dump() | dict(
        policy=policy,
        expected_policy_id=policy.policy_id,
        expected_policy_version=policy.policy_version,
        expected_policy_fingerprint=policy.fingerprint(),
    )
    request = c.SharedMemberTargetTasteFitRequest.model_validate(body)
    return reseal(source.model_copy(update=dict(request=request)))


def rebind_member(source, member_id, actor):
    raw = canonical(source)
    raw["request"]["member_id"] = str(member_id)
    raw["candidate_frame"]["actor_user_id"] = str(actor)

    def visit(v):
        if isinstance(v, dict):
            if "member_id" in v:
                v["member_id"] = str(member_id)
            if "actor_user_id" in v:
                v["actor_user_id"] = str(actor)
            for item in v.values():
                visit(item)
            if v.get("contract_version") == "member-preference-declaration.v1":
                cls = (
                    SetMemberPreferenceCommand
                    if v["command"]["action"] == "SET"
                    else (RetractMemberPreferenceCommand)
                )
                v["command_fingerprint"] = cls.model_validate(v["command"]).fingerprint()
        elif isinstance(v, list):
            for item in v:
                visit(item)

    visit(raw["member_sources"])
    return seal(child.CandidateMemberTasteFitSources.model_validate(raw))


def make_cohort(*, kind="PROTEIN", states=("LIKE", "DISLIKE"), portion="0.5", projection=None):
    if projection is None:
        q, facts, _ = setup()
        ids = [q.tracked_member_id] + [uuid4() for _ in states[1:]]
        facts = facts.model_copy(
            update=dict(
                members=facts.members
                + tuple(
                    HouseholdMemberIdentity(household_id=q.household_id, member_id=mid)
                    for mid in ids[1:]
                ),
                member_safety=facts.member_safety
                + tuple(
                    CanonicalMemberSafetySnapshot(
                        household_id=q.household_id, member_id=mid, constraints=()
                    )
                    for mid in ids[1:]
                ),
            )
        )
        q = q.model_copy(
            update=dict(
                participants=MealParticipants(
                    participants=(
                        q.participants.participants
                        + tuple(
                            dict(member_id=mid, portion_factor=portion, nutrition_role="SHARED")
                            for mid in ids[1:]
                        )
                    )
                )
            )
        )
        projection = make_subject(grounding=(q, facts))
    ids = [p.member_id for p in projection.request.grounding_request.participants.participants]
    actor, explicit, fit = uuid4(), None, None
    children, target = [], None
    for mid, state in zip(ids, states, strict=True):
        source = make_sources(
            projection_source=projection,
            explicit_policy=explicit,
            state=state if state in {"UNDECLARED", "RETRACTED"} else "DECLARED",
            value=state if state in {"LIKE", "DISLIKE", "NEUTRAL"} else "LIKE",
        )
        explicit = source.request.member_interpretation.explicit_policy
        fit = fit or source.request.policy
        source = with_policy(source, fit)
        target = target or next(
            e.target for e in source.member_sources.entries if e.target.kind == kind
        )
        source = seal(
            source.model_copy(
                update=dict(
                    request=source.request.model_copy(update=dict(diagnostic_targets=(target,)))
                )
            )
        )
        children.append(derive_candidate_member_tastefit(rebind_member(source, mid, actor)))
    return pack(children, target)
