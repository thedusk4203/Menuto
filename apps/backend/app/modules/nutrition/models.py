"""Member-owned source data. These records are not resolved nutrition policies."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base, IdentityMixin


class MemberNutritionProfile(IdentityMixin, Base):
    __tablename__ = "member_nutrition_profiles"
    __table_args__ = (
        UniqueConstraint("household_id", "member_id"),
        ForeignKeyConstraint(
            ["household_id", "member_id"],
            ["household_members.household_id", "household_members.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "body_mass_kg IS NULL OR (body_mass_kg > 0 AND body_mass_kg < 1000000000000)",
            name="mass_positive_finite",
        ),
        CheckConstraint(
            "height_cm IS NULL OR (height_cm > 0 AND height_cm < 1000000000000)",
            name="height_positive_finite",
        ),
        CheckConstraint("row_version > 0", name="version_positive"),
    )
    household_id: Mapped[UUID]
    member_id: Mapped[UUID]
    body_mass_kg: Mapped[Decimal | None]
    height_cm: Mapped[Decimal | None]
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    row_version: Mapped[int] = mapped_column(default=1)
    __mapper_args__ = {"version_id_col": row_version}


class MemberSafetyConstraint(IdentityMixin, Base):
    __tablename__ = "member_safety_constraints"
    __table_args__ = (
        Index(
            "uq_member_safety_code",
            "household_id",
            "member_id",
            "kind",
            "code",
            unique=True,
            postgresql_where=text("kind IN ('ALLERGEN','DIET_RULE')"),
        ),
        Index(
            "uq_member_safety_excluded_ingredient",
            "household_id",
            "member_id",
            "ingredient_id",
            unique=True,
            postgresql_where=text("kind = 'EXCLUDED_INGREDIENT'"),
        ),
        ForeignKeyConstraint(
            ["household_id", "member_id"],
            ["household_members.household_id", "household_members.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("kind IN ('ALLERGEN','DIET_RULE','EXCLUDED_INGREDIENT')", name="kind"),
        CheckConstraint(
            "(kind='EXCLUDED_INGREDIENT' AND ingredient_id IS NOT NULL) OR "
            "(kind <> 'EXCLUDED_INGREDIENT' AND ingredient_id IS NULL)",
            name="ingredient_scope",
        ),
        CheckConstraint("length(trim(code)) > 0", name="code_required"),
    )
    household_id: Mapped[UUID]
    member_id: Mapped[UUID]
    kind: Mapped[str] = mapped_column(String(30))
    code: Mapped[str] = mapped_column(String(100))
    ingredient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT")
    )
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
