"""Correct foundation ownership, account binding, safety identity and provenance.

Revision ID: 0002
Revises: 0001

Never edits 0001 or silently discards populated legacy yields/ambiguous identity.
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        LOCK TABLE unit_conversions, household_members, memberships,
            member_safety_constraints, nutrition_facts IN ACCESS EXCLUSIVE MODE;
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM unit_conversions) THEN
                RAISE EXCEPTION 'Legacy yields need explicit Retail/Recipe ownership migration'
                    USING ERRCODE = '23514';
            END IF;
            IF EXISTS (SELECT 1 FROM household_members WHERE user_id IS NOT NULL
                       GROUP BY household_id, user_id HAVING count(*) > 1) THEN
                RAISE EXCEPTION 'Ambiguous legacy account/person mapping; resolve before migration'
                    USING ERRCODE = '23514';
            END IF;
            IF EXISTS (
                SELECT 1 FROM household_members h LEFT JOIN memberships m
                ON m.household_id=h.household_id AND m.user_id=h.user_id
                WHERE h.user_id IS NOT NULL AND
                (m.id IS NULL OR (m.member_id IS NOT NULL AND m.member_id <> h.id))
            ) OR EXISTS (
                SELECT 1 FROM memberships m JOIN household_members h
                ON h.household_id=m.household_id AND h.id=m.member_id
                WHERE h.user_id IS NOT NULL AND h.user_id <> m.user_id
            ) THEN
                RAISE EXCEPTION 'Conflicting account/person mapping; resolve before migration'
                    USING ERRCODE = '23514';
            END IF;
            IF EXISTS (SELECT 1 FROM member_safety_constraints
                       WHERE kind='EXCLUDED_INGREDIENT'
                       GROUP BY household_id, member_id, ingredient_id HAVING count(*) > 1) THEN
                RAISE EXCEPTION 'Duplicate canonical ingredient exclusion; resolve before migration'
                    USING ERRCODE = '23514';
            END IF;
        END $$;
        UPDATE memberships m SET member_id=h.id FROM household_members h
        WHERE m.household_id=h.household_id AND m.user_id=h.user_id AND m.member_id IS NULL;
    """)
    op.drop_constraint(
        op.f("fk_household_members_user_id_users"), "household_members", type_="foreignkey"
    )
    op.drop_column("household_members", "user_id")
    # Both yield kinds belong to their future owner-specific mappings, not Catalog.
    # Preflight above guarantees no evidence is deleted by this removal.
    op.drop_table("unit_conversions")
    op.drop_constraint(
        op.f("uq_member_safety_constraints_household_id_member_id_kind_code"),
        "member_safety_constraints",
        type_="unique",
    )
    op.create_index(
        "uq_member_safety_code",
        "member_safety_constraints",
        ["household_id", "member_id", "kind", "code"],
        unique=True,
        postgresql_where=sa.text("kind IN ('ALLERGEN','DIET_RULE')"),
    )
    op.create_index(
        "uq_member_safety_excluded_ingredient",
        "member_safety_constraints",
        ["household_id", "member_id", "ingredient_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'EXCLUDED_INGREDIENT'"),
    )
    op.drop_constraint(
        op.f("uq_nutrition_facts_ingredient_id_source_ref_source_version_basis"),
        "nutrition_facts",
        type_="unique",
    )
    op.drop_constraint(op.f("ck_nutrition_facts_source_identity"), "nutrition_facts", type_="check")
    op.alter_column(
        "nutrition_facts",
        "source_ref",
        new_column_name="external_record_id",
        existing_type=sa.String(100),
        type_=sa.String(2048),
    )
    op.alter_column(
        "nutrition_facts", "source_version", existing_type=sa.String(100), type_=sa.String(200)
    )
    # A migration label, never an inferred real provider identity; original locator is intact.
    op.add_column(
        "nutrition_facts",
        sa.Column("source_system", sa.String(100), nullable=False, server_default="legacy.m0"),
    )
    op.alter_column("nutrition_facts", "source_system", server_default=None)
    op.add_column("nutrition_facts", sa.Column("source_uri", sa.String(2048), nullable=True))
    op.add_column("nutrition_facts", sa.Column("content_hash", sa.String(64), nullable=True))
    op.create_unique_constraint(
        "uq_nutrition_fact_source",
        "nutrition_facts",
        ["ingredient_id", "source_system", "external_record_id", "source_version", "basis"],
    )
    op.create_check_constraint(
        op.f("ck_nutrition_facts_source_identity"),
        "nutrition_facts",
        "length(trim(source_system)) > 0 AND "
        "length(trim(external_record_id)) > 0 AND "
        "length(trim(source_version)) > 0",
    )
    op.create_check_constraint(
        op.f("ck_nutrition_facts_source_system"),
        "nutrition_facts",
        "source_system ~ '^[A-Za-z0-9_.:-]+$'",
    )
    op.create_check_constraint(
        op.f("ck_nutrition_facts_content_hash"),
        "nutrition_facts",
        "content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'",
    )


def downgrade():
    op.execute("""
        LOCK TABLE household_members, memberships, member_safety_constraints,
            nutrition_facts IN ACCESS EXCLUSIVE MODE;
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM nutrition_facts WHERE source_system <> 'legacy.m0'
                       OR source_uri IS NOT NULL OR content_hash IS NOT NULL
                       OR length(external_record_id)>100 OR length(source_version)>100) THEN
                RAISE EXCEPTION 'Provenance cannot be downgraded losslessly; export/migrate first'
                    USING ERRCODE = '23514';
            END IF;
            IF EXISTS (SELECT 1 FROM member_safety_constraints
                       GROUP BY household_id, member_id, kind, code HAVING count(*) > 1) THEN
                RAISE EXCEPTION 'Safety identities cannot fit legacy unique code; migrate first'
                    USING ERRCODE = '23514';
            END IF;
        END $$;
    """)
    op.drop_constraint("uq_nutrition_fact_source", "nutrition_facts", type_="unique")
    for name in ("source_identity", "source_system", "content_hash"):
        op.drop_constraint(op.f("ck_nutrition_facts_" + name), "nutrition_facts", type_="check")
    for name in ("source_system", "source_uri", "content_hash"):
        op.drop_column("nutrition_facts", name)
    op.alter_column(
        "nutrition_facts",
        "external_record_id",
        new_column_name="source_ref",
        existing_type=sa.String(2048),
        type_=sa.String(100),
    )
    op.alter_column(
        "nutrition_facts", "source_version", existing_type=sa.String(200), type_=sa.String(100)
    )
    op.create_unique_constraint(
        op.f("uq_nutrition_facts_ingredient_id_source_ref_source_version_basis"),
        "nutrition_facts",
        ["ingredient_id", "source_ref", "source_version", "basis"],
    )
    op.create_check_constraint(
        op.f("ck_nutrition_facts_source_identity"),
        "nutrition_facts",
        "length(trim(source_ref)) > 0 AND length(trim(source_version)) > 0",
    )
    op.add_column("household_members", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_household_members_user_id_users"),
        "household_members",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.execute("""UPDATE household_members h SET user_id=m.user_id FROM memberships m
               WHERE h.household_id=m.household_id AND h.id=m.member_id""")
    op.drop_index("uq_member_safety_code", table_name="member_safety_constraints")
    op.drop_index("uq_member_safety_excluded_ingredient", table_name="member_safety_constraints")
    op.create_unique_constraint(
        op.f("uq_member_safety_constraints_household_id_member_id_kind_code"),
        "member_safety_constraints",
        ["household_id", "member_id", "kind", "code"],
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

    op.execute(
        "CREATE TRIGGER unit_conversions_immutable BEFORE UPDATE OR DELETE ON unit_conversions "
        "FOR EACH ROW EXECUTE FUNCTION menuto_reject_catalog_fact_mutation()"
    )
