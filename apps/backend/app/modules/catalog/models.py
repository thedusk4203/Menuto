"""Catalog facts; transformations require reviewed contextual evidence."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base, IdentityMixin, ProvenanceMixin

SOURCE_CHECK = "source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')"


class Ingredient(IdentityMixin, Base):
    __tablename__ = "ingredients"
    name: Mapped[str] = mapped_column(String(200))


class NutritionFact(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "nutrition_facts"
    __table_args__ = (
        UniqueConstraint("ingredient_id", "source_ref", "source_version", "basis"),
        CheckConstraint("basis IN ('EP_RAW_G','COOKED_G')", name="nutrition_basis"),
        CheckConstraint(
            "reference_amount > 0 AND reference_amount < 1000000000000",
            name="reference_positive_finite",
        ),
        CheckConstraint(
            "energy_kcal >= 0 AND energy_kcal < 1000000000000 AND "
            "protein_g >= 0 AND protein_g < 1000000000000 AND "
            "fat_g >= 0 AND fat_g < 1000000000000 AND "
            "carbohydrate_g >= 0 AND carbohydrate_g < 1000000000000",
            name="nutrients_nonnegative_finite",
        ),
        CheckConstraint("status IN ('DRAFT','REVIEWED')", name="status"),
        CheckConstraint(SOURCE_CHECK, name="source_kind"),
        CheckConstraint(
            "length(trim(source_ref)) > 0 AND length(trim(source_version)) > 0",
            name="source_identity",
        ),
    )
    ingredient_id: Mapped[UUID] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    basis: Mapped[str] = mapped_column(String(20))
    reference_amount: Mapped[Decimal]
    energy_kcal: Mapped[Decimal]
    protein_g: Mapped[Decimal]
    fat_g: Mapped[Decimal]
    carbohydrate_g: Mapped[Decimal]
    status: Mapped[str] = mapped_column(String(20))


class UnitConversion(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "unit_conversions"
    __table_args__ = (
        CheckConstraint("factor > 0 AND factor < 1000000000000", name="factor_positive_finite"),
        CheckConstraint(
            "(kind='EDIBLE_YIELD' AND source_basis='AP_G' AND target_basis='EP_RAW_G' "
            "AND factor <= 1) OR "
            "(kind='COOKING_YIELD' AND source_basis='EP_RAW_G' AND target_basis='COOKED_G')",
            name="yield_chain",
        ),
        CheckConstraint(SOURCE_CHECK, name="source_kind"),
        CheckConstraint("length(trim(context_ref)) > 0", name="context_required"),
        CheckConstraint(
            "length(trim(source_ref)) > 0 AND length(trim(source_version)) > 0",
            name="source_identity",
        ),
    )
    ingredient_id: Mapped[UUID] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    kind: Mapped[str] = mapped_column(String(20))
    # Context identifies a product-map version or recipe-preparation version, never universal.
    context_ref: Mapped[str] = mapped_column(String(100))
    source_basis: Mapped[str] = mapped_column(String(20))
    target_basis: Mapped[str] = mapped_column(String(20))
    factor: Mapped[Decimal]
    reviewed_at: Mapped[datetime | None]
