"""Read-only source coordination inside Preferences; caller owns all transactions."""

from sqlalchemy import text

from app.modules.preferences.contracts import (
    ExplicitTargetAffinityInput,
    preference_target_key,
)
from app.modules.preferences.hierarchical_affinity_contracts import (
    OneHopHierarchicalMemberPreferenceInput,
)
from app.modules.preferences.hierarchy_resolution import resolve_hierarchy_sources
from app.modules.preferences.hierarchy_sources import capture_hierarchy_sources
from app.modules.preferences.prior_affinity_contracts import ExactTargetPriorBackedAffinityInput
from app.modules.preferences.profile_capture import capture_explicit_target_affinity_sources
from app.modules.preferences.reference_priors import capture_reference_prior_sources
from app.modules.preferences.tastefit_contracts import (
    TasteFitCaptureFrame,
    TasteFitMemberCapturePlan,
    TasteFitMemberSourceBundle,
    TasteFitMemberSourceEntry,
    check_tastefit_frames,
)


def _clock(session):
    return session.scalar(text("SELECT clock_timestamp()"))


def _start(session, owner, targets, actor):
    if session.new or session.dirty or session.deleted:
        raise ValueError("CAPTURE_CONTEXT_INVALID: clean read-only session required")
    isolation = session.connection().get_isolation_level()
    if isolation not in {"REPEATABLE READ", "SERIALIZABLE"} or (
        session.scalar(text("SHOW transaction_read_only")) != "on"
    ):
        raise ValueError("CAPTURE_CONTEXT_INVALID: read-only RR/SERIALIZABLE required")
    url = session.get_bind().engine.url
    row = (
        session.execute(
            text(
                "SELECT current_database() AS database_name, "
                "(SELECT oid::bigint FROM pg_database "
                "WHERE datname=current_database()) AS database_oid, "
                "host(inet_server_addr()) AS server_address, inet_server_port() AS server_port, "
                "session_user AS session_user"
            )
        )
        .mappings()
        .one()
    )
    now = _clock(session)
    return TasteFitCaptureFrame(
        owner=owner,
        actor_user_id=actor,
        targets=targets,
        configured_host=url.host or "",
        configured_port=url.port or 5432,
        **row,
        isolation=isolation,
        read_only=True,
        started_at=now,
        completed_at=now,
    )


def capture_tastefit_member_sources(sessions, plan, *, actor_user_id):
    from app.modules.preferences.tastefit_public import replay_tastefit_member_sources

    plan = TasteFitMemberCapturePlan.model_validate(plan)
    interpretation = plan.interpretation
    modes = {preference_target_key(r.target): r.capture_mode for r in plan.targets}
    targets = {preference_target_key(r.target): r.target for r in plan.targets}
    need_hierarchy = any(m == "EXACT_TARGET_AND_ONE_HOP" for m in modes.values())
    need_prior = any(m != "EXPLICIT_ONLY" for m in modes.values())
    owners = (
        ["MEMBER"] + (["PRIOR"] if need_prior else []) + (["HIERARCHY"] if need_hierarchy else [])
    )
    if any(o.lower() not in sessions or sessions[o.lower()] is None for o in owners):
        raise ValueError("SOURCE_CAPTURE_FAILED: required owner session missing")
    frames = {o: _start(sessions[o.lower()], o, (), actor_user_id) for o in owners}
    check_tastefit_frames(tuple(frames.values()))
    hierarchy, parent_keys = {}, set()
    if need_hierarchy:
        for row in plan.targets:
            if row.capture_mode != "EXACT_TARGET_AND_ONE_HOP":
                continue
            key = preference_target_key(row.target)
            source = capture_hierarchy_sources(
                sessions["hierarchy"],
                dict(
                    provider_id=interpretation.hierarchy_provider_id,
                    policy_id=interpretation.hierarchy_policy.policy_id,
                    requested_targets=(row.target,),
                ),
            )
            hierarchy[key] = source
            resolved = resolve_hierarchy_sources(source).rows[0]
            if resolved.status == "ELIGIBLE_RELATION":
                parent = resolved.selected_relation.command.identity.source
                parent_key = preference_target_key(parent)
                targets[parent_key] = parent
                parent_keys.add(parent_key)
    explicit, exact = {}, {}
    for key, target in sorted(targets.items()):
        source = capture_explicit_target_affinity_sources(
            sessions["member"],
            dict(
                household_id=plan.household_id,
                member_id=plan.member_id,
                requested_targets=(target,),
            ),
            actor_user_id=actor_user_id,
        )
        explicit[key] = ExplicitTargetAffinityInput(
            source=source, policy=interpretation.explicit_policy
        )
        if modes.get(key, "EXPLICIT_ONLY") != "EXPLICIT_ONLY" or key in parent_keys:
            policy = interpretation.compatibility_policy
            reference = capture_reference_prior_sources(
                sessions["prior"],
                dict(
                    provider_id=policy.provider_id,
                    coordinate=policy.reference_coordinate,
                    requested_targets=(target,),
                ),
            )
            exact[key] = ExactTargetPriorBackedAffinityInput(
                explicit=explicit[key],
                reference_source=reference,
                compatibility_policy=policy,
                shrinkage_policy=interpretation.shrinkage_policy,
            )
    entries = []
    for key, target in sorted(targets.items()):
        one_hop = None
        if key in hierarchy:
            source = hierarchy[key]
            row = resolve_hierarchy_sources(source).rows[0]
            parent = (
                row.selected_relation.command.identity.source
                if row.status == "ELIGIBLE_RELATION"
                else None
            )
            one_hop = OneHopHierarchicalMemberPreferenceInput(
                destination=exact[key],
                parent=exact[preference_target_key(parent)] if parent is not None else None,
                hierarchy_source=source,
            )
        entries.append(
            TasteFitMemberSourceEntry(
                target=target, explicit=explicit[key], exact_target=exact.get(key), one_hop=one_hop
            )
        )
    for owner in owners:
        keys = (
            targets.keys()
            if owner == "MEMBER"
            else (exact.keys() if owner == "PRIOR" else hierarchy.keys())
        )
        frames[owner] = TasteFitCaptureFrame.model_validate(
            frames[owner].model_dump()
            | dict(
                targets=tuple(targets[k] for k in sorted(keys)),
                completed_at=_clock(sessions[owner.lower()]),
            )
        )
    bundle = TasteFitMemberSourceBundle(plan=plan, entries=entries, frames=tuple(frames.values()))
    replay_tastefit_member_sources(bundle)
    return bundle
