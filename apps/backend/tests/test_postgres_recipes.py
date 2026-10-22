"""Real PostgreSQL recipe constraints, aggregate seals and frozen migration safety."""

from copy import deepcopy
from uuid import uuid4

import pytest
from alembic import command
from app.modules.catalog.models import Ingredient
from app.modules.recipes import contracts as c
from app.modules.recipes import models as m
from app.modules.recipes.repository import RecipeRepository
from recipe_fixtures import provenance, recipe_data, snapshot
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from test_foundation_migration import legacy_database as legacy_database
from test_foundation_migration import migrate
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_retail import db as db

pytestmark = pytest.mark.postgres


def seed(db, data=None, repository=RecipeRepository):
    s = c.RecipeVersionSnapshot.model_validate(data) if data else snapshot()
    ids = {i.ingredient_id for i in s.ingredients} | {
        r.replacement_ingredient_id for r in s.variant_rules
    }
    for identity in ids:
        db.add(Ingredient(id=identity, name="Synthetic recipe ingredient"))
    db.flush()
    repo = repository(db)
    repo.add_recipe(s.recipe)
    repo.add_version(s)
    return s, repo


class SqlWriter(RecipeRepository):
    """Bypasses ORM numeric validation to exercise only PostgreSQL enforcement."""

    mutation = staticmethod(lambda table, fields: fields)
    skip_seal = False

    def _insert(self, model, fields):
        if model is m.RecipeVersionSeal and self.skip_seal:
            return
        fields = self.mutation(model.__tablename__, dict(fields))
        self.session.execute(
            text(
                f"INSERT INTO {model.__tablename__} ({','.join(fields)}) "
                f"VALUES ({','.join(':' + key for key in fields)})"
            ),
            fields,
        )


def test_snapshot_roundtrip_and_correction_is_new_version(db):
    first, repo = seed(db)
    assert repo.version(first.id) == first
    second = deepcopy(first.model_dump())
    second.update(
        id=uuid4(), version=2, procedure="A corrected authored procedure.", provenance=provenance()
    )
    id_map = {}
    for field in ("ingredients", "portion_tiers", "variant_rules", "transformations"):
        for row in second[field]:
            old = row["id"]
            row.update(id=uuid4(), recipe_version_id=second["id"])
            id_map[old] = row["id"]
            if "provenance" in row:
                row["provenance"] = provenance()
    for tier in second["portion_tiers"]:
        for quantity in tier["quantities"]:
            quantity["requirement_id"] = id_map[quantity["requirement_id"]]
    for field in ("variant_rules", "transformations"):
        for row in second[field]:
            row["requirement_id"] = id_map[row["requirement_id"]]
    corrected = c.RecipeVersionSnapshot.model_validate(second)
    repo.add_version(corrected)
    assert repo.version(first.id) == first
    assert repo.version(corrected.id) == corrected
    assert corrected.recipe == first.recipe and corrected.procedure != first.procedure
    db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))


@pytest.mark.parametrize("table", m.TABLES)
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE"])
def test_every_recipe_fact_is_append_only_even_in_sql(db, table, operation):
    data = recipe_data()
    data["approved_combinations"] = [
        dict(
            id=uuid4(),
            recipe_version_id=data["id"],
            key="both",
            rule_ids=[r["id"] for r in data["variant_rules"]],
            provenance=provenance(),
        )
    ]
    seed(db, data)
    db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    if operation == "UPDATE":
        column = (
            "recipe_version_id"
            if table
            in {"recipe_version_seals", "recipe_combination_members", "recipe_tier_quantities"}
            else "id"
        )
        sql = f"UPDATE {table} SET {column}={column}"
    else:
        sql = f"DELETE FROM {table}" if operation == "DELETE" else f"TRUNCATE {table} CASCADE"
    with db.begin_nested():
        with pytest.raises(IntegrityError, match="immutable"):
            db.execute(text(sql))
        db.rollback()


@pytest.mark.parametrize("table", m.TABLES[2:-1])
def test_insert_child_after_seal_rejected(db, table):
    data = recipe_data()
    data["approved_combinations"] = [
        dict(
            id=uuid4(),
            recipe_version_id=data["id"],
            key="both",
            rule_ids=[r["id"] for r in data["variant_rules"]],
            provenance=provenance(),
        )
    ]
    seed(db, data)
    fields = dict(db.execute(text(f"SELECT * FROM {table} LIMIT 1")).mappings().one())
    if "id" in fields:
        fields["id"] = uuid4()
    with pytest.raises(IntegrityError, match="sealed"):
        db.execute(
            text(
                f"INSERT INTO {table} ({','.join(fields)}) "
                f"VALUES ({','.join(':' + key for key in fields)})"
            ),
            fields,
        )


@pytest.mark.parametrize(
    "column,value",
    [
        ("basis", "AP_G"),
        ("basis", "SERVING"),
        ("amount", "NaN"),
        ("amount", "Infinity"),
        ("amount", "-1"),
        ("amount", "0"),
        ("amount", "1.0000001"),
        ("scaling_kind", "MAGIC"),
        ("scaling_quantum", "0"),
        ("adjustment_kind", "MAGIC"),
        ("min_delta", "1"),
        ("max_delta", "-1"),
        ("adjustment_step", "1"),
        ("item_ref", "unexpected.mass.context"),
    ],
)
def test_direct_sql_requirement_checks(db, column, value):
    class Invalid(SqlWriter):
        @staticmethod
        def mutation(table, fields):
            if table == "recipe_ingredients":
                fields[column] = value
            return fields

    with pytest.raises(DBAPIError):
        seed(db, repository=Invalid)


@pytest.mark.parametrize(
    "index,amount", [(0, "401"), (1, "201"), (1, "90"), (2, "11"), (3, "1.5"), (4, "6")]
)
def test_direct_sql_seal_recomputes_all_scaling_policies(db, index, amount):
    data = recipe_data()
    requirement = data["ingredients"][index]["id"]
    tier = data["portion_tiers"][1]["id"]

    class Invalid(SqlWriter):
        @staticmethod
        def mutation(table, fields):
            if (
                table == "recipe_tier_quantities"
                and fields["requirement_id"] == requirement
                and fields["tier_id"] == tier
            ):
                fields["amount"] = amount
            return fields

    with pytest.raises(IntegrityError):
        seed(db, data, Invalid)


@pytest.mark.parametrize(
    "column,value",
    [
        ("factor", "NaN"),
        ("factor", "0"),
        ("source_basis", "AP_G"),
        ("target_basis", "EP_RAW_G"),
        ("method", "BOIL"),
        ("ingredient_id", uuid4()),
    ],
)
def test_direct_sql_cooking_context_and_factor(db, column, value):
    class Invalid(SqlWriter):
        @staticmethod
        def mutation(table, fields):
            if table == "preparation_transformations":
                fields[column] = value
            return fields

    with pytest.raises(IntegrityError):
        seed(db, repository=Invalid)


def test_incomplete_version_cannot_commit_without_seal(db):
    class Unsealed(SqlWriter):
        skip_seal = True

    seed(db, repository=Unsealed)
    with pytest.raises(IntegrityError, match="required_seal"):
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))


def test_seal_rejects_missing_tier_quantity_and_rolls_back_whole_version(db):
    class Incomplete(SqlWriter):
        def _insert(self, model, fields):
            if model is m.RecipeTierQuantity and fields["ordinal"] == 0:
                return
            super()._insert(model, fields)

    with pytest.raises(IntegrityError, match="Incomplete"):
        seed(db, repository=Incomplete)
    assert db.scalar(text("SELECT count(*) FROM recipe_versions")) == 0


@pytest.mark.parametrize(
    "table",
    [
        "recipe_tier_quantities",
        "recipe_variant_rules",
        "preparation_transformations",
        "recipe_combination_members",
    ],
)
def test_cross_version_fk_rejects_bare_identity_mismatch(db, table):
    class Invalid(SqlWriter):
        @staticmethod
        def mutation(target, fields):
            if target == table:
                fields["recipe_version_id"] = uuid4()
            return fields

    data = recipe_data()
    data["approved_combinations"] = [
        dict(
            id=uuid4(),
            recipe_version_id=data["id"],
            key="both",
            rule_ids=[r["id"] for r in data["variant_rules"]],
            provenance=provenance(),
        )
    ]
    with pytest.raises(IntegrityError):
        seed(db, data, Invalid)


def test_empty_upgrade_downgrade_upgrade_and_metadata_drift(legacy_database):
    engine, config = legacy_database
    migrate(engine, config, "0004")
    with engine.connect() as conn:
        old = set(inspect(conn).get_table_names())
    migrate(engine, config, "0005")
    migrate(engine, config, "head")
    with engine.connect() as conn:
        assert set(inspect(conn).get_table_names()) == old | set(m.TABLES)
        config.attributes["connection"] = conn
        command.check(config)
    migrate(engine, config, "0004", down=True)
    migrate(engine, config, "0005")
    migrate(engine, config, "head")
    with engine.connect() as conn:
        config.attributes["connection"] = conn
        command.check(config)


def test_populated_downgrade_fails_closed_and_preserves_snapshot(legacy_database):
    engine, config = legacy_database
    migrate(engine, config, "0005")
    with Session(engine) as session:
        s, _ = seed(session)
        session.commit()
    with pytest.raises(IntegrityError, match="would lose Recipe"):
        migrate(engine, config, "0004", down=True)
    with Session(engine) as session:
        assert RecipeRepository(session).version(s.id) == s
        assert session.scalar(text("SELECT version_num FROM alembic_version")) == "0005"


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ"])
def test_stale_reader_cannot_append_after_writer_commit(legacy_database, isolation):
    engine, config = legacy_database
    migrate(engine, config, "0005")
    with engine.connect().execution_options(isolation_level=isolation) as reader:
        reader.execute(text("SELECT count(*) FROM recipe_versions"))
        with Session(engine) as writer:
            s, _ = seed(writer)
            fields = dict(
                writer.execute(
                    text("SELECT * FROM recipe_ingredients WHERE recipe_version_id=:id LIMIT 1"),
                    {"id": s.id},
                )
                .mappings()
                .one()
            )
            writer.commit()
        fields.update(id=uuid4(), slot="late.slot", ordinal=99)
        with pytest.raises(IntegrityError, match="assembly transaction is closed"):
            reader.execute(
                text(
                    f"INSERT INTO recipe_ingredients ({','.join(fields)}) "
                    f"VALUES ({','.join(':' + key for key in fields)})"
                ),
                fields,
            )
        reader.rollback()
    with Session(engine) as session:
        assert RecipeRepository(session).version(s.id) == s


@pytest.mark.parametrize(
    "table,changes",
    [
        ("recipe_portion_tiers", {"servings": "0"}),
        ("recipe_portion_tiers", {"servings": "NaN"}),
        ("recipe_versions", {"base_servings": "NaN"}),
        ("recipe_versions", {"version": 0}),
        ("recipe_versions", {"review_status": "REVIEWED", "source_kind": "IMPORTED_DRAFT"}),
        ("recipe_versions", {"source_uri": "https://user:password@example.test/recipe"}),
        ("recipe_variant_rules", {"source_kind": "IMPORTED_DRAFT"}),
        ("preparation_transformations", {"source_kind": "IMPORTED_DRAFT"}),
        ("recipe_ingredients", {"scaling_kind": "DISCRETE", "scaling_quantum": "3"}),
        ("recipe_ingredients", {"adjustment_kind": "SMALL", "min_delta": "-20", "max_delta": "30"}),
        ("recipe_ingredients", {"adjustment_kind": "DISCRETE", "adjustment_step": "3"}),
        ("recipe_ingredients", {"min_delta": "-1000"}),
        ("recipe_variant_rules", {"quantity_factor": "-1"}),
    ],
)
def test_sql_policy_provenance_and_aggregate_checks(db, table, changes):
    class Invalid(SqlWriter):
        @staticmethod
        def mutation(target, fields):
            if target == table:
                fields.update(changes)
            return fields

    with pytest.raises(DBAPIError):
        seed(db, repository=Invalid)


def test_source_provider_identity_roundtrip_and_duplicate_rejected(db):
    s, repo = seed(db)
    assert repo.version(s.id).provenance == s.provenance
    with pytest.raises(IntegrityError):
        repo.add_version(s)


def test_no_generic_yield_or_retail_cooking_persistence():
    from app.persistence.models import Base

    assert "unit_conversions" not in Base.metadata.tables
    for table in Base.metadata.tables.values():
        if table.name.startswith("retail") or table.name == "ingredient_product_maps":
            assert not any("cooking" in c.name for c in table.columns)
    assert not any("edible" in c.name for c in m.PreparationTransformation.__table__.columns)
