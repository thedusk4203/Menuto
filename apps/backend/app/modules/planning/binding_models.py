"""Planning-owned append-only proposal children, with no copied recipe truth."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.planning.models import proposal_fk
from app.shared.db import Base, ProvenanceMixin


class PlannedCulinaryBinding(ProvenanceMixin, Base):
    __tablename__ = "planned_culinary_bindings"
    __table_args__ = (
        proposal_fk(),
        ForeignKeyConstraint(
            ["proposal_id", "batch_node_id"],
            ["planned_cooking_batches.proposal_id", "planned_cooking_batches.node_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tier_id", "recipe_version_id"],
            ["recipe_portion_tiers.id", "recipe_portion_tiers.recipe_version_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["approved_combination_id", "recipe_version_id"],
            ["recipe_rule_combinations.id", "recipe_rule_combinations.recipe_version_id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint("proposal_id", "batch_node_id", "recipe_version_id"),
        CheckConstraint("contract_version='planned-culinary-binding.v1'", name="version"),
        CheckConstraint("fingerprint ~ '^[a-f0-9]{64}$'", name="fingerprint"),
        CheckConstraint(
            "planned_servings>0 AND planned_servings<1000000000000 AND "
            "planned_servings=trunc(planned_servings,6)",
            name="servings",
        ),
        CheckConstraint("source_kind IN ('USER_AUTHORED','CURATED_REFERENCE')", name="source_kind"),
        CheckConstraint(
            "source_system ~ '^[A-Za-z0-9_.:-]+$' AND length(trim(external_record_id))>0 AND "
            "length(trim(source_version))>0 AND isfinite(observed_at)",
            name="source_identity",
        ),
        CheckConstraint(
            "content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'", name="content_hash"
        ),
    )
    proposal_id: Mapped[UUID] = mapped_column(primary_key=True)
    batch_node_id: Mapped[UUID] = mapped_column(primary_key=True)
    household_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    recipe_version_id: Mapped[UUID]
    tier_id: Mapped[UUID]
    planned_servings: Mapped[Decimal] = mapped_column(Numeric())
    approved_combination_id: Mapped[UUID | None]
    contract_version: Mapped[str] = mapped_column(String(50))
    fingerprint: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime]


class CulinaryRequirementBinding(Base):
    __tablename__ = "culinary_requirement_bindings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["proposal_id", "batch_node_id", "recipe_version_id"],
            [
                "planned_culinary_bindings.proposal_id",
                "planned_culinary_bindings.batch_node_id",
                "planned_culinary_bindings.recipe_version_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["requirement_id", "recipe_version_id"],
            ["recipe_ingredients.id", "recipe_ingredients.recipe_version_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["selected_rule_id", "recipe_version_id"],
            ["recipe_variant_rules.id", "recipe_variant_rules.recipe_version_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["transformation_id", "recipe_version_id"],
            ["preparation_transformations.id", "preparation_transformations.recipe_version_id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "amount>0 AND amount<1e36::numeric AND amount=trunc(amount,36)", name="calculation"
        ),
        CheckConstraint(
            "abs(adjustment_delta)<1000000000000 AND adjustment_delta=trunc(adjustment_delta,6)",
            name="adjustment",
        ),
        CheckConstraint(
            "(basis IN ('EP_RAW_G','COOKED_G') AND item_ref IS NULL) OR (basis='COUNT' AND "
            "item_ref IS NOT NULL AND item_ref ~ '^[A-Za-z0-9_.:-]+$' "
            "AND selected_rule_id IS NULL)",
            name="basis",
        ),
    )
    proposal_id: Mapped[UUID] = mapped_column(primary_key=True)
    batch_node_id: Mapped[UUID] = mapped_column(primary_key=True)
    requirement_id: Mapped[UUID] = mapped_column(primary_key=True)
    recipe_version_id: Mapped[UUID]
    selected_rule_id: Mapped[UUID | None]
    ingredient_id: Mapped[UUID] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    amount: Mapped[Decimal] = mapped_column(Numeric())
    basis: Mapped[str] = mapped_column(String(20))
    item_ref: Mapped[str | None] = mapped_column(String(100))
    adjustment_delta: Mapped[Decimal] = mapped_column(Numeric())
    transformation_id: Mapped[UUID | None]
