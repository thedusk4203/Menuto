"""Member-owned capture/replay companion; no candidate fit or ranking semantics."""

from app.domain.feature_identity import canonical_bytes
from app.modules.preferences.contracts import preference_target_key
from app.modules.preferences.hierarchical_affinity import (
    derive_one_hop_hierarchical_member_preference,
)
from app.modules.preferences.hierarchy_resolution import resolve_hierarchy_sources
from app.modules.preferences.prior_affinity import derive_exact_target_prior_backed_affinity
from app.modules.preferences.profile_derivation import derive_explicit_target_affinity_profile
from app.modules.preferences.tastefit_contracts import (
    TasteFitMemberSourceBundle,
    TasteFitMemberView,
    check_tastefit_frames,
    check_tastefit_immutable_facts,
    member_ledger_body,
)


def capture_tastefit_member_sources(sessions, plan, *, actor_user_id):
    from app.modules.preferences.tastefit_sources import capture_tastefit_member_sources

    return capture_tastefit_member_sources(sessions, plan, actor_user_id=actor_user_id)


def replay_tastefit_member_sources(bundle):
    """Recompute all children and exact owner-derived closure, including unselected views."""
    bundle = TasteFitMemberSourceBundle.model_validate(bundle)
    plan, entries = bundle.plan, bundle.entries
    interpretation = plan.interpretation
    expected = {preference_target_key(r.target): r for r in plan.targets}
    closure = set(expected)
    parents = set()
    for entry in entries:
        if entry.one_hop is not None:
            selected = resolve_hierarchy_sources(entry.one_hop.hierarchy_source).rows[0]
            if selected.status == "ELIGIBLE_RELATION":
                parents.add(
                    preference_target_key(selected.selected_relation.command.identity.source)
                )
    views, ledgers = [], []
    owner_cuts = {}
    required_frames = {"MEMBER"}
    for entry in entries:
        key = preference_target_key(entry.target)
        row = expected.get(key)
        # Non-destination entries may only be a selected one-hop parent, checked below.
        mode = row.capture_mode if row else "EXPLICIT_ONLY"
        explicit = entry.explicit
        if (
            (explicit.source.request.household_id, explicit.source.request.member_id)
            != (plan.household_id, plan.member_id)
            or explicit.source.request.requested_targets != (entry.target,)
            or explicit.policy != interpretation.explicit_policy
        ):
            raise ValueError("SUBJECT_OWNER_MISMATCH: exact explicit owner/target/policy required")
        ledgers.append(member_ledger_body(explicit.source.preferences))
        raw = derive_explicit_target_affinity_profile(explicit).rows[0]
        exact, one_hop = None, None
        if (entry.exact_target is not None) != (mode != "EXPLICIT_ONLY" or key in parents):
            raise ValueError("Missing or detached exact-target child")
        if entry.exact_target is not None:
            required_frames.add("PRIOR")
            child = entry.exact_target
            if (
                child.explicit != explicit
                or child.compatibility_policy != interpretation.compatibility_policy
                or child.shrinkage_policy != interpretation.shrinkage_policy
            ):
                raise ValueError("SOURCE_POLICY_BINDING_MISMATCH: detached exact-target child")
            exact = derive_exact_target_prior_backed_affinity(child)
            _same_owner_cut(owner_cuts, "PRIOR", child.reference_source)
        if (entry.one_hop is not None) != (mode == "EXACT_TARGET_AND_ONE_HOP"):
            raise ValueError("Missing or detached one-hop child")
        if entry.one_hop is not None:
            required_frames.add("HIERARCHY")
            child = entry.one_hop
            h = child.hierarchy_source
            _same_owner_cut(owner_cuts, "HIERARCHY", h)
            if (
                child.destination != entry.exact_target
                or h.request.requested_targets != (entry.target,)
                or h.request.provider_id != interpretation.hierarchy_provider_id
                or h.provider.command_hash != interpretation.hierarchy_provider_command_hash
                or h.request.policy_id != interpretation.hierarchy_policy.policy_id
            ):
                raise ValueError("SOURCE_POLICY_BINDING_MISMATCH: hierarchy selectors")
            resolved = resolve_hierarchy_sources(h)
            selected = resolved.rows[0]
            if selected.status == "ELIGIBLE_RELATION":
                if selected.policy.command.policy != interpretation.hierarchy_policy:
                    raise ValueError("SOURCE_POLICY_BINDING_MISMATCH: published transfer policy")
                parent = selected.selected_relation.command.identity.source
                closure.add(preference_target_key(parent))
                if (
                    child.parent is None
                    or child.parent.explicit.source.request.requested_targets != (parent,)
                ):
                    raise ValueError("Missing selected parent primitive")
            elif child.parent is not None:
                raise ValueError("Detached parent without eligible relation")
            one_hop = derive_one_hop_hierarchical_member_preference(child)
            if child.parent is not None:
                parent_entry = next((e for e in entries if e.target == one_hop.parent_target), None)
                if parent_entry is None or parent_entry.exact_target != child.parent:
                    raise ValueError("Detached parent source entry")
        views.append(
            TasteFitMemberView(
                target=entry.target, explicit=raw, exact_target=exact, one_hop=one_hop
            )
        )
    if {preference_target_key(e.target) for e in entries} != closure:
        raise ValueError("Member source closure has missing/extra targets")
    if not ledgers or any(canonical_bytes(b) != canonical_bytes(ledgers[0]) for b in ledgers):
        raise ValueError("SOURCE_CUT_INCOHERENT: full member ledger differs")
    check_tastefit_immutable_facts(bundle)
    frames = {f.owner: f for f in bundle.frames}
    if set(frames) != required_frames:
        raise ValueError("Missing or detached member owner frame")
    check_tastefit_frames(bundle.frames)
    for owner, frame in frames.items():
        wanted = {
            preference_target_key(e.target)
            for e in entries
            if owner == "MEMBER"
            or (owner == "PRIOR" and e.exact_target is not None)
            or (owner == "HIERARCHY" and e.one_hop is not None)
        }
        if {preference_target_key(t) for t in frame.targets} != wanted:
            raise ValueError("Owner capture frame target closure differs")
        for e in entries:
            source = (
                e.explicit.source
                if owner == "MEMBER"
                else e.exact_target.reference_source
                if owner == "PRIOR" and e.exact_target
                else e.one_hop.hierarchy_source
                if owner == "HIERARCHY" and e.one_hop
                else None
            )
            if source is None:
                continue
            start = (
                source.preferences.captured_at if owner == "MEMBER" else source.capture_started_at
            )
            end = source.capture_completed_at
            if not frame.started_at <= start <= end <= frame.completed_at:
                raise ValueError("Owner child clock outside its capture frame")
            if owner != "MEMBER":
                reader = source.reader_session
                if (reader.database_name, reader.database_oid, reader.role_name) != (
                    frame.database_name,
                    frame.database_oid,
                    frame.session_user,
                ):
                    raise ValueError("Protected source reader differs from capture frame")
    return tuple(views)


def _same_owner_cut(cuts, owner, source):
    # All reads on one owner session must share its complete journal/frontier,
    # while requests/manifests and actual read clocks legitimately differ.
    fields = (
        "provider",
        "principals",
        "authority_events",
        "publications",
        "mutations",
        "streams",
        "frontier",
        "reader_principal_id",
        "reader_session",
        "reader_grant_id",
    )
    body = canonical_bytes({name: getattr(source, name) for name in fields})
    if owner in cuts and cuts[owner] != body:
        raise ValueError("SOURCE_CUT_INCOHERENT: spliced owner journal/frontier")
    cuts[owner] = body
