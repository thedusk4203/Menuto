"""Member source records, not clinical guidance or compiled nutrition policy."""

from typing import Literal
from uuid import UUID

from pydantic import model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, PositiveDecimal
from app.domain.snapshots import WriteCommand


class MemberNutritionProfileWrite(WriteCommand):
    member_id: UUID
    body_mass_kg: PositiveDecimal | None = None
    height_cm: PositiveDecimal | None = None


class MemberSafetyConstraint(Contract):
    household_id: UUID
    member_id: UUID
    kind: Literal["ALLERGEN", "DIET_RULE", "EXCLUDED_INGREDIENT"]
    code: Identifier
    ingredient_id: UUID | None = None
    actor_user_id: UUID

    @model_validator(mode="after")
    def ingredient_scope(self):
        if (self.kind == "EXCLUDED_INGREDIENT") != (self.ingredient_id is not None):
            raise ValueError("Only EXCLUDED_INGREDIENT requires ingredient_id")
        return self


class MemberSafetySourceFact(Contract):
    contract_version: Literal["member-safety-source.v1"] = "member-safety-source.v1"
    source_system: Literal["menuto.member_safety_constraints"] = "menuto.member_safety_constraints"
    id: UUID
    recorded_at: AwareTime
    constraint: MemberSafetyConstraint


class CanonicalMemberSafetySnapshot(Contract):
    contract_version: Literal["canonical-member-safety.v1"] = "canonical-member-safety.v1"
    household_id: UUID
    member_id: UUID
    constraints: tuple[MemberSafetySourceFact, ...]
