"""Household ownership and participant input, independent of planning internals."""

from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator

from app.domain.contracts import Contract, Label, PositiveDecimal


class HouseholdCreate(Contract):
    name: Label
    member_name: Label
    timezone: Label = "Asia/Ho_Chi_Minh"

    @field_validator("timezone")
    @classmethod
    def known_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("Use a known IANA timezone") from error
        return value


class HouseholdCreated(Contract):
    household_id: UUID
    member_id: UUID
    owner_user_id: UUID


class Participant(Contract):
    member_id: UUID
    portion_factor: PositiveDecimal
    nutrition_role: Literal["TRACKED", "SHARED"]


class MealParticipants(Contract):
    participants: tuple[Participant, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_members_and_single_tracked(self):
        if len({p.member_id for p in self.participants}) != len(self.participants):
            raise ValueError("Each member may participate only once per meal")
        if sum(p.nutrition_role == "TRACKED" for p in self.participants) > 1:
            raise ValueError("V1 supports at most one tracked nutrition member")
        return self

    @property
    def attendance_scale(self):
        return sum(p.portion_factor for p in self.participants)
