"""Internal onboarding transaction. The caller supplies an authenticated existing user."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.households.contracts import (
    HouseholdCreate,
    HouseholdCreated,
    HouseholdMemberIdentity,
)
from app.modules.households.models import Household, HouseholdMember, Membership


def create_default_household(
    session: Session, *, actor_user_id: UUID, request: HouseholdCreate
) -> HouseholdCreated:
    """Flush only; caller owns transaction/rollback. Not a public HTTP auth endpoint."""
    household = Household(
        name=request.name, timezone=request.timezone, created_by_user_id=actor_user_id
    )
    session.add(household)
    session.flush()
    member = HouseholdMember(household_id=household.id, name=request.member_name)
    session.add(member)
    session.flush()
    session.add(
        Membership(
            household_id=household.id, user_id=actor_user_id, member_id=member.id, role="OWNER"
        )
    )
    session.flush()
    return HouseholdCreated(
        household_id=household.id, member_id=member.id, owner_user_id=actor_user_id
    )


def member_identities(session, household_id):
    return tuple(
        HouseholdMemberIdentity(household_id=row.household_id, member_id=row.id)
        for row in session.scalars(
            select(HouseholdMember)
            .where(HouseholdMember.household_id == household_id)
            .order_by(HouseholdMember.id)
        )
    )


def lock_household_actor(session, household_id, actor_user_id, *, write=False):
    """Canonical access check for an authenticated internal caller; no ORM escapes."""
    row = session.execute(
        select(Membership.member_id, Membership.role)
        .where(Membership.household_id == household_id, Membership.user_id == actor_user_id)
        .with_for_update(read=True)
    ).one_or_none()
    if row is None or (write and row.role not in {"OWNER", "EDITOR"}):
        raise PermissionError("Household actor access denied")
    return row.member_id, row.role


def read_household_actor(session, household_id, actor_user_id):
    """Read-only capture access; permission is coherent with the caller's source snapshot."""
    row = session.execute(
        select(Membership.member_id, Membership.role).where(
            Membership.household_id == household_id, Membership.user_id == actor_user_id
        )
    ).one_or_none()
    if row is None:
        raise PermissionError("Household actor access denied")
    return row.member_id, row.role


def capture_resolution_member(session, household_id, member_id, actor_user_id):
    """Read-only planning intent witness. This grants no goal/clinical authorship."""
    actor = session.execute(select(Membership.id, Membership.member_id, Membership.role).where(
        Membership.household_id == household_id, Membership.user_id == actor_user_id
    )).one_or_none()
    if actor is None or actor.role not in {"OWNER", "EDITOR"}:
        raise PermissionError("AUTHORIZATION_DENIED: planning intent")
    member = session.scalar(select(HouseholdMember.id).where(
        HouseholdMember.household_id == household_id, HouseholdMember.id == member_id
    ))
    household = session.scalar(select(Household.id).where(Household.id == household_id))
    return actor.id, actor.member_id, actor.role, member is not None and household is not None
