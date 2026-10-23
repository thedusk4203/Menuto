"""Catalog facts; transformations require reviewed contextual evidence."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base, IdentityMixin, ProvenanceMixin

SOURCE_CHECK = "source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')"


class Ingredient(IdentityMixin, Base):
    __tablename__ = "ingredients"
    name: Mapped[str] = mapped_column(String(200))


class NutritionFact(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "nutrition_facts"
    __table_args__ = (
        UniqueConstraint(
            "ingredient_id",
            "source_system",
            "external_record_id",
            "source_version",
            "basis",
            name="uq_nutrition_fact_source",
        ),
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
        CheckConstraint("source_system ~ '^[A-Za-z0-9_.:-]+$'", name="source_system"),
        CheckConstraint(
            "content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'", name="content_hash"
        ),
        CheckConstraint(
            "length(trim(source_system)) > 0 AND length(trim(external_record_id)) > 0 "
            "AND length(trim(source_version)) > 0",
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


class AffinityFeatureTerm(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "affinity_feature_terms"
    __table_args__ = (
        UniqueConstraint("kind", "code", "version"),
        UniqueConstraint("id", "kind"),
        CheckConstraint("kind IN ('PROTEIN','METHOD','FLAVOR')", name="kind"),
        CheckConstraint("code ~ '^[A-Za-z0-9_.:-]+$'", name="code"),
        CheckConstraint("version>0", name="version"),
        CheckConstraint("length(trim(label))>0 AND length(trim(definition))>0", name="definition"),
        CheckConstraint("status IN ('DRAFT','REVIEWED')", name="status"),
        CheckConstraint("source_kind IN ('USER','REVIEWED_REFERENCE')", name="source_kind"),
        CheckConstraint("source_system ~ '^[A-Za-z0-9_.:-]+$'", name="source_system"),
        CheckConstraint(
            "length(trim(external_record_id))>0 AND length(trim(source_version))>0 "
            "AND external_record_id !~ '[[:cntrl:]]' "
            "AND source_version !~ '[[:cntrl:]]'",
            name="source_identity",
        ),
        CheckConstraint("isfinite(observed_at)", name="observed_at"),
        CheckConstraint("content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'", name="hash"),
        CheckConstraint(
            "source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' "
            "AND source_uri !~ '^https?://[^/]*@' "
            "AND source_uri !~ '[[:cntrl:]]')",
            name="uri",
        ),
        UniqueConstraint("source_system", "external_record_id", "source_version"),
    )
    kind: Mapped[str] = mapped_column(String(20))
    code: Mapped[str] = mapped_column(String(100))
    version: Mapped[int]
    label: Mapped[str] = mapped_column(String(200))
    definition: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
