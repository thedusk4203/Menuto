"""Household and membership are separate from member physiology."""

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base, IdentityMixin


class Household(IdentityMixin, Base):
    __tablename__ = "households"
    name: Mapped[str] = mapped_column(String(200))
    timezone: Mapped[str] = mapped_column(String(100), default="Asia/Ho_Chi_Minh")
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class HouseholdMember(IdentityMixin, Base):
    __tablename__ = "household_members"
    __table_args__ = (UniqueConstraint("household_id", "id"),)
    household_id: Mapped[UUID] = mapped_column(ForeignKey("households.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(200))
    # A shared diner need not have an account. Binding to an actor is explicit.
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class Membership(IdentityMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("household_id", "user_id"),
        UniqueConstraint("household_id", "member_id"),
        ForeignKeyConstraint(
            ["household_id", "member_id"],
            ["household_members.household_id", "household_members.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("role IN ('OWNER', 'EDITOR', 'VIEWER')", name="role"),
    )
    household_id: Mapped[UUID] = mapped_column(ForeignKey("households.id", ondelete="RESTRICT"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    member_id: Mapped[UUID | None]
    role: Mapped[str] = mapped_column(String(20))
