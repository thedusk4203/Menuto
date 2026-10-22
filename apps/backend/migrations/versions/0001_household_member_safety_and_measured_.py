"""household member safety and measured catalog foundation

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Frozen DDL: do not import current ORM metadata into an applied migration.
    op.create_table(
        "ingredients",
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingredients")),
    )
    op.create_table(
        "users",
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_table(
        "households",
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_households_created_by_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_households")),
    )
    op.create_table(
        "nutrition_facts",
        sa.Column("ingredient_id", sa.Uuid(), nullable=False),
        sa.Column("basis", sa.String(length=20), nullable=False),
        sa.Column("reference_amount", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("energy_kcal", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("protein_g", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("fat_g", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("carbohydrate_g", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source_kind", sa.String(length=30), nullable=False),
        sa.Column("source_ref", sa.String(length=100), nullable=False),
        sa.Column("source_version", sa.String(length=100), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "basis IN ('EP_RAW_G','COOKED_G')", name=op.f("ck_nutrition_facts_nutrition_basis")
        ),
        sa.CheckConstraint(
            "source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')",
            name=op.f("ck_nutrition_facts_source_kind"),
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT','REVIEWED')", name=op.f("ck_nutrition_facts_status")
        ),
        sa.CheckConstraint(
            "energy_kcal >= 0 AND energy_kcal < 1000000000000 AND "
            "protein_g >= 0 AND protein_g < 1000000000000 AND "
            "fat_g >= 0 AND fat_g < 1000000000000 AND "
            "carbohydrate_g >= 0 AND carbohydrate_g < 1000000000000",
            name=op.f("ck_nutrition_facts_nutrients_nonnegative_finite"),
        ),
        sa.CheckConstraint(
            "length(trim(source_ref)) > 0 AND length(trim(source_version)) > 0",
            name=op.f("ck_nutrition_facts_source_identity"),
        ),
        sa.CheckConstraint(
            "reference_amount > 0 AND reference_amount < 1000000000000",
            name=op.f("ck_nutrition_facts_reference_positive_finite"),
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_nutrition_facts_ingredient_id_ingredients"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_nutrition_facts")),
        sa.UniqueConstraint(
            "ingredient_id",
            "source_ref",
            "source_version",
            "basis",
            name=op.f("uq_nutrition_facts_ingredient_id_source_ref_source_version_basis"),
        ),
    )
    op.create_table(
        "unit_conversions",
        sa.Column("ingredient_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("context_ref", sa.String(length=100), nullable=False),
        sa.Column("source_basis", sa.String(length=20), nullable=False),
        sa.Column("target_basis", sa.String(length=20), nullable=False),
        sa.Column("factor", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source_kind", sa.String(length=30), nullable=False),
        sa.Column("source_ref", sa.String(length=100), nullable=False),
        sa.Column("source_version", sa.String(length=100), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(kind='EDIBLE_YIELD' AND source_basis='AP_G' AND target_basis='EP_RAW_G' "
            "AND factor <= 1) OR "
            "(kind='COOKING_YIELD' AND source_basis='EP_RAW_G' AND target_basis='COOKED_G')",
            name=op.f("ck_unit_conversions_yield_chain"),
        ),
        sa.CheckConstraint(
            "source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')",
            name=op.f("ck_unit_conversions_source_kind"),
        ),
        sa.CheckConstraint(
            "factor > 0 AND factor < 1000000000000",
            name=op.f("ck_unit_conversions_factor_positive_finite"),
        ),
        sa.CheckConstraint(
            "length(trim(context_ref)) > 0", name=op.f("ck_unit_conversions_context_required")
        ),
        sa.CheckConstraint(
            "length(trim(source_ref)) > 0 AND length(trim(source_version)) > 0",
            name=op.f("ck_unit_conversions_source_identity"),
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_unit_conversions_ingredient_id_ingredients"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_unit_conversions")),
    )
    op.create_table(
        "household_members",
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            name=op.f("fk_household_members_household_id_households"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_household_members_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_household_members")),
        sa.UniqueConstraint(
            "household_id", "id", name=op.f("uq_household_members_household_id_id")
        ),
    )
    op.create_table(
        "member_nutrition_profiles",
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("body_mass_kg", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("height_cm", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("row_version", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "body_mass_kg IS NULL OR (body_mass_kg > 0 AND body_mass_kg < 1000000000000)",
            name=op.f("ck_member_nutrition_profiles_mass_positive_finite"),
        ),
        sa.CheckConstraint(
            "height_cm IS NULL OR (height_cm > 0 AND height_cm < 1000000000000)",
            name=op.f("ck_member_nutrition_profiles_height_positive_finite"),
        ),
        sa.CheckConstraint(
            "row_version > 0", name=op.f("ck_member_nutrition_profiles_version_positive")
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_member_nutrition_profiles_created_by_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["household_id", "member_id"],
            ["household_members.household_id", "household_members.id"],
            name=op.f("fk_member_nutrition_profiles_household_id_household_members"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_nutrition_profiles")),
        sa.UniqueConstraint(
            "household_id",
            "member_id",
            name=op.f("uq_member_nutrition_profiles_household_id_member_id"),
        ),
    )
    op.create_table(
        "member_safety_constraints",
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("ingredient_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(kind='EXCLUDED_INGREDIENT' AND ingredient_id IS NOT NULL) OR "
            "(kind <> 'EXCLUDED_INGREDIENT' AND ingredient_id IS NULL)",
            name=op.f("ck_member_safety_constraints_ingredient_scope"),
        ),
        sa.CheckConstraint(
            "kind IN ('ALLERGEN','DIET_RULE','EXCLUDED_INGREDIENT')",
            name=op.f("ck_member_safety_constraints_kind"),
        ),
        sa.CheckConstraint(
            "length(trim(code)) > 0", name=op.f("ck_member_safety_constraints_code_required")
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_member_safety_constraints_created_by_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["household_id", "member_id"],
            ["household_members.household_id", "household_members.id"],
            name=op.f("fk_member_safety_constraints_household_id_household_members"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_member_safety_constraints_ingredient_id_ingredients"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_safety_constraints")),
        sa.UniqueConstraint(
            "household_id",
            "member_id",
            "kind",
            "code",
            name=op.f("uq_member_safety_constraints_household_id_member_id_kind_code"),
        ),
    )
    op.create_table(
        "memberships",
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('OWNER', 'EDITOR', 'VIEWER')", name=op.f("ck_memberships_role")
        ),
        sa.ForeignKeyConstraint(
            ["household_id", "member_id"],
            ["household_members.household_id", "household_members.id"],
            name=op.f("fk_memberships_household_id_household_members"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            name=op.f("fk_memberships_household_id_households"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_memberships_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memberships")),
        sa.UniqueConstraint(
            "household_id", "member_id", name=op.f("uq_memberships_household_id_member_id")
        ),
        sa.UniqueConstraint(
            "household_id", "user_id", name=op.f("uq_memberships_household_id_user_id")
        ),
    )
    op.execute("""
        CREATE FUNCTION menuto_reject_catalog_fact_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Catalog facts are append-only; insert a new source version'
                USING ERRCODE = '23514';
        END;
        $$
    """)
    for table in ("nutrition_facts", "unit_conversions"):
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION menuto_reject_catalog_fact_mutation()"
        )


def downgrade() -> None:
    op.drop_table("memberships")
    op.drop_table("member_safety_constraints")
    op.drop_table("member_nutrition_profiles")
    op.drop_table("household_members")
    op.drop_table("unit_conversions")
    op.drop_table("nutrition_facts")
    op.drop_table("households")
    op.drop_table("users")
    op.drop_table("ingredients")
    op.execute("DROP FUNCTION menuto_reject_catalog_fact_mutation()")
