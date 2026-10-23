"""Read source safety facts, not planner exclusions or synthesized policy."""

from sqlalchemy import select

from app.modules.nutrition.contracts import (
    CanonicalMemberSafetySnapshot,
    MemberSafetyConstraint,
    MemberSafetySourceFact,
)
from app.modules.nutrition.models import MemberSafetyConstraint as SafetyRow


def canonical_member_safety(session, household_id, member_ids):
    rows = tuple(
        session.scalars(
            select(SafetyRow).where(SafetyRow.household_id == household_id).order_by(SafetyRow.id)
        )
    )
    return tuple(
        CanonicalMemberSafetySnapshot(
            household_id=household_id,
            member_id=member,
            constraints=tuple(
                MemberSafetySourceFact(
                    id=r.id,
                    recorded_at=r.created_at,
                    constraint=MemberSafetyConstraint(
                        household_id=r.household_id,
                        member_id=r.member_id,
                        kind=r.kind,
                        code=r.code,
                        ingredient_id=r.ingredient_id,
                        actor_user_id=r.created_by_user_id,
                    ),
                )
                for r in rows
                if r.member_id == member
            ),
        )
        for member in sorted(member_ids, key=str)
    )
