"""Internal onboarding transaction. The caller supplies an authenticated existing user."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.households.contracts import HouseholdCreate, HouseholdCreated
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
