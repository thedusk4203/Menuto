"""Additive NRE owner capture surface. Frozen public.py remains byte-exact."""

from sqlalchemy import select

from app.modules.households.models import Household, HouseholdMember, Membership


def capture_resolution_member(session, household_id, member_id, actor_user_id):
    """Read-only planning intent witness. This grants no goal/clinical authorship."""
    actor = session.execute(
        select(Membership.id, Membership.member_id, Membership.role).where(
            Membership.household_id == household_id, Membership.user_id == actor_user_id
        )
    ).one_or_none()
    if actor is None or actor.role not in {"OWNER", "EDITOR"}:
        raise PermissionError("AUTHORIZATION_DENIED: planning intent")
    member = session.scalar(
        select(HouseholdMember.id).where(
            HouseholdMember.household_id == household_id, HouseholdMember.id == member_id
        )
    )
    household = session.scalar(select(Household.id).where(Household.id == household_id))
    return actor.id, actor.member_id, actor.role, member is not None and household is not None
