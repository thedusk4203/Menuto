"""Recipe-owned immutable relational facts. No Retail or Inventory runtime imports."""

from decimal import Decimal
from hashlib import sha256
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.domain.contracts import PersistedDecimal
from app.shared.db import Base, IdentityMixin, ProvenanceMixin


class RecipeNumeric(TypeDecorator):
    """Unconstrained numeric + checks reject direct SQL scale loss, NaN and infinity."""

    impl = Numeric()
    cache_ok = True
    adapter = TypeAdapter(PersistedDecimal)

    def process_bind_param(self, value, dialect):
        return None if value is None else self.adapter.validate_python(value)


def number(column, *, positive=False):
    return CheckConstraint(
        f"abs({column}) < 1000000000000 AND {column} = trunc({column},6)"
        + (f" AND {column}>0" if positive else ""),
        name=f"{column}_numeric",
    )


def ident(column):
    return CheckConstraint(f"{column} ~ '^[A-Za-z0-9_.:-]+$'", name=column)


def fk(columns, table, targets):
    identity = "_".join([table, *columns, *targets])
    return ForeignKeyConstraint(
        columns,
        [f"{table}.{c}" for c in targets],
        ondelete="RESTRICT",
        name="fk_recipe_" + sha256(identity.encode()).hexdigest()[:16],
    )


def provenance():
    return (
        CheckConstraint(
            "source_kind IN ('USER_AUTHORED','CURATED_REFERENCE','IMPORTED_DRAFT')",
            name="source_kind",
        ),
        ident("source_system"),
        CheckConstraint(
            "length(trim(external_record_id))>0 AND length(trim(source_version))>0 "
            "AND external_record_id !~ '[[:cntrl:]]' "
            "AND source_version !~ '[[:cntrl:]]'",
            name="source_identity",
        ),
        CheckConstraint("isfinite(observed_at)", name="observed_at"),
        CheckConstraint(
            "content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'", name="content_hash"
        ),
        CheckConstraint(
            "source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' "
            "AND source_uri !~ '^https?://[^/]*@' "
            "AND source_uri !~ '[[:cntrl:]]')",
            name="source_uri",
        ),
        UniqueConstraint("source_system", "external_record_id", "source_version"),
    )


class Recipe(IdentityMixin, Base):
    __tablename__ = "recipes"
    __table_args__ = (ident("cooking_method"), CheckConstraint("length(trim(name))>0", name="name"))
    name: Mapped[str] = mapped_column(String(200))
    cooking_method: Mapped[str] = mapped_column(String(100))


class RecipeVersion(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "recipe_versions"
    __table_args__ = (
        *provenance(),
        UniqueConstraint("recipe_id", "version"),
        CheckConstraint("version>0", name="version"),
        ident("serving_definition"),
        CheckConstraint("length(trim(serving_description))>0", name="serving_description"),
        CheckConstraint(
            "length(trim(procedure))>0 AND length(procedure)<=100000", name="procedure"
        ),
        number("base_servings", positive=True),
        CheckConstraint(
            "review_status IN ('DRAFT','REVIEWED') AND "
            "(source_kind!='IMPORTED_DRAFT' OR review_status='DRAFT')",
            name="review",
        ),
        ForeignKeyConstraint(
            ["id"],
            ["recipe_version_seals.recipe_version_id"],
            name="fk_recipe_version_required_seal",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
    )
    recipe_id: Mapped[UUID] = mapped_column(ForeignKey("recipes.id", ondelete="RESTRICT"))
    # DB-controlled assembly transaction; prevents stale-isolation child insertion.
    authored_transaction: Mapped[str] = mapped_column(
        String(30), server_default=text("pg_current_xact_id()::text")
    )
    version: Mapped[int]
    serving_definition: Mapped[str] = mapped_column(String(100))
    serving_description: Mapped[str] = mapped_column(String(200))
    base_servings: Mapped[Decimal] = mapped_column(RecipeNumeric())
    procedure: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(20))


class RecipeIngredient(IdentityMixin, Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        UniqueConstraint("id", "recipe_version_id"),
        UniqueConstraint("recipe_version_id", "slot"),
        UniqueConstraint("recipe_version_id", "ordinal"),
        ident("slot"),
        ident("role"),
        CheckConstraint("ordinal>=0", name="ordinal"),
        number("amount", positive=True),
        CheckConstraint(
            "(basis IN ('EP_RAW_G','COOKED_G') AND item_ref IS NULL) OR "
            "(basis='COUNT' AND item_ref IS NOT NULL "
            "AND item_ref ~ '^[A-Za-z0-9_.:-]+$')",
            name="quantity_basis",
        ),
        CheckConstraint(
            "scaling_kind IN ('LINEAR','SUBLINEAR','FIXED','DISCRETE','TO_TASTE')",
            name="scaling_kind",
        ),
        number("scaling_quantum", positive=True),
        number("scaling_minimum", positive=True),
        number("scaling_maximum", positive=True),
        CheckConstraint(
            "(scaling_kind='DISCRETE') = (scaling_quantum IS NOT NULL) AND "
            "((scaling_kind='TO_TASTE' AND scaling_minimum IS NOT NULL "
            "AND scaling_maximum IS NOT NULL AND scaling_minimum<=scaling_maximum) OR "
            "(scaling_kind!='TO_TASTE' AND scaling_minimum IS NULL "
            "AND scaling_maximum IS NULL))",
            name="scaling_shape",
        ),
        CheckConstraint(
            "adjustment_kind IN ('NONE','SMALL','PORTIONABLE','DISCRETE')", name="adjustment_kind"
        ),
        number("min_delta"),
        number("max_delta"),
        number("adjustment_step", positive=True),
        CheckConstraint(
            "min_delta<=0 AND max_delta>=0 AND "
            "((adjustment_kind='NONE' AND min_delta=0 AND max_delta=0) OR "
            "(adjustment_kind!='NONE' AND min_delta<max_delta)) AND "
            "(adjustment_kind!='SMALL' OR min_delta=-max_delta) AND "
            "((adjustment_kind='DISCRETE' AND adjustment_step IS NOT NULL "
            "AND mod(min_delta,adjustment_step)=0 "
            "AND mod(max_delta,adjustment_step)=0) OR "
            "(adjustment_kind!='DISCRETE' AND adjustment_step IS NULL))",
            name="adjustment_shape",
        ),
    )
    recipe_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("recipe_versions.id", ondelete="RESTRICT")
    )
    ordinal: Mapped[int]
    slot: Mapped[str] = mapped_column(String(100))
    ingredient_id: Mapped[UUID] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    amount: Mapped[Decimal] = mapped_column(RecipeNumeric())
    basis: Mapped[str] = mapped_column(String(20))
    item_ref: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(100))
    scaling_kind: Mapped[str] = mapped_column(String(20))
    scaling_quantum: Mapped[Decimal | None] = mapped_column(RecipeNumeric())
    scaling_minimum: Mapped[Decimal | None] = mapped_column(RecipeNumeric())
    scaling_maximum: Mapped[Decimal | None] = mapped_column(RecipeNumeric())
    adjustment_kind: Mapped[str] = mapped_column(String(20))
    min_delta: Mapped[Decimal] = mapped_column(RecipeNumeric())
    max_delta: Mapped[Decimal] = mapped_column(RecipeNumeric())
    adjustment_step: Mapped[Decimal | None] = mapped_column(RecipeNumeric())


class RecipePortionTier(IdentityMixin, Base):
    __tablename__ = "recipe_portion_tiers"
    __table_args__ = (
        UniqueConstraint("id", "recipe_version_id"),
        UniqueConstraint("recipe_version_id", "key"),
        UniqueConstraint("recipe_version_id", "servings"),
        UniqueConstraint("recipe_version_id", "ordinal"),
        ident("key"),
        number("servings", positive=True),
        CheckConstraint("ordinal>=0", name="ordinal"),
    )
    recipe_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("recipe_versions.id", ondelete="RESTRICT")
    )
    ordinal: Mapped[int]
    key: Mapped[str] = mapped_column(String(100))
    servings: Mapped[Decimal] = mapped_column(RecipeNumeric())


class RecipeTierQuantity(Base):
    __tablename__ = "recipe_tier_quantities"
    __table_args__ = (
        fk(["tier_id", "recipe_version_id"], "recipe_portion_tiers", ["id", "recipe_version_id"]),
        fk(
            ["requirement_id", "recipe_version_id"],
            "recipe_ingredients",
            ["id", "recipe_version_id"],
        ),
        UniqueConstraint("tier_id", "ordinal"),
        number("amount", positive=True),
        CheckConstraint("ordinal>=0", name="ordinal"),
    )
    tier_id: Mapped[UUID] = mapped_column(primary_key=True)
    requirement_id: Mapped[UUID] = mapped_column(primary_key=True)
    recipe_version_id: Mapped[UUID]
    ordinal: Mapped[int]
    amount: Mapped[Decimal] = mapped_column(RecipeNumeric())


class RecipeVariantRule(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "recipe_variant_rules"
    __table_args__ = (
        *provenance(),
        UniqueConstraint("id", "recipe_version_id"),
        UniqueConstraint("recipe_version_id", "key"),
        UniqueConstraint("recipe_version_id", "ordinal"),
        fk(
            ["requirement_id", "recipe_version_id"],
            "recipe_ingredients",
            ["id", "recipe_version_id"],
        ),
        ident("key"),
        CheckConstraint("version>0 AND ordinal>=0", name="version_ordinal"),
        number("quantity_factor", positive=True),
    )
    recipe_version_id: Mapped[UUID]
    ordinal: Mapped[int]
    key: Mapped[str] = mapped_column(String(100))
    version: Mapped[int]
    requirement_id: Mapped[UUID]
    replacement_ingredient_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT")
    )
    quantity_factor: Mapped[Decimal] = mapped_column(RecipeNumeric())
    structural: Mapped[bool]


class RecipeRuleCombination(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "recipe_rule_combinations"
    __table_args__ = (
        *provenance(),
        UniqueConstraint("id", "recipe_version_id"),
        UniqueConstraint("recipe_version_id", "key"),
        UniqueConstraint("recipe_version_id", "ordinal"),
        ident("key"),
        CheckConstraint("ordinal>=0", name="ordinal"),
    )
    recipe_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("recipe_versions.id", ondelete="RESTRICT")
    )
    ordinal: Mapped[int]
    key: Mapped[str] = mapped_column(String(100))


class RecipeCombinationMember(Base):
    __tablename__ = "recipe_combination_members"
    __table_args__ = (
        fk(
            ["combination_id", "recipe_version_id"],
            "recipe_rule_combinations",
            ["id", "recipe_version_id"],
        ),
        fk(["rule_id", "recipe_version_id"], "recipe_variant_rules", ["id", "recipe_version_id"]),
        UniqueConstraint("combination_id", "ordinal"),
        CheckConstraint("ordinal>=0", name="ordinal"),
    )
    combination_id: Mapped[UUID] = mapped_column(primary_key=True)
    rule_id: Mapped[UUID] = mapped_column(primary_key=True)
    recipe_version_id: Mapped[UUID]
    ordinal: Mapped[int]


class PreparationTransformation(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "preparation_transformations"
    __table_args__ = (
        UniqueConstraint("id", "recipe_version_id"),
        *provenance(),
        UniqueConstraint("recipe_version_id", "requirement_id", "ingredient_id"),
        UniqueConstraint("recipe_version_id", "ordinal"),
        fk(
            ["requirement_id", "recipe_version_id"],
            "recipe_ingredients",
            ["id", "recipe_version_id"],
        ),
        ident("preparation_key"),
        ident("method"),
        CheckConstraint("version>0 AND ordinal>=0", name="version_ordinal"),
        CheckConstraint("source_basis='EP_RAW_G' AND target_basis='COOKED_G'", name="yield_chain"),
        number("factor", positive=True),
    )
    recipe_version_id: Mapped[UUID]
    ordinal: Mapped[int]
    requirement_id: Mapped[UUID]
    ingredient_id: Mapped[UUID] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    preparation_key: Mapped[str] = mapped_column(String(100))
    method: Mapped[str] = mapped_column(String(100))
    version: Mapped[int]
    source_basis: Mapped[str] = mapped_column(String(20))
    target_basis: Mapped[str] = mapped_column(String(20))
    factor: Mapped[Decimal] = mapped_column(RecipeNumeric())


class RecipeVersionSeal(Base):
    __tablename__ = "recipe_version_seals"
    recipe_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("recipe_versions.id", ondelete="RESTRICT"), primary_key=True
    )


TABLES = (
    "recipes",
    "recipe_versions",
    "recipe_ingredients",
    "recipe_portion_tiers",
    "recipe_tier_quantities",
    "recipe_variant_rules",
    "recipe_rule_combinations",
    "recipe_combination_members",
    "preparation_transformations",
    "recipe_version_seals",
)
