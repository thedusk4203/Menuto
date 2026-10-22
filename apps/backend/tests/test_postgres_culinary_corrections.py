"""0006 policy guard, legacy fail-closed upgrade and persisted culinary path regressions."""

import pytest
from alembic import command
from app.modules.recipes import models as m
from app.modules.recipes.repository import RecipeRepository
from recipe_fixtures import bind, recipe_data
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_foundation_migration import legacy_database as legacy_database
from test_foundation_migration import migrate
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_recipes import SqlWriter, seed
from test_postgres_retail import db as db

pytestmark = pytest.mark.postgres


class CountWriter(SqlWriter):
    def _insert(self, model, fields):
        if model is m.RecipeIngredient and fields["basis"] == "COUNT":
            self.count_slot = fields["id"]
        if model is m.RecipeVariantRule and fields["ordinal"] == 1:
            fields = fields | {"requirement_id": self.count_slot}
        super()._insert(model, fields)


def rows(connection):
    return {
        name: list(
            connection.execute(
                text(
                    f"SELECT * FROM {name} ORDER BY "
                    + ",".join(c.name for c in m.Base.metadata.tables[name].primary_key.columns)
                )
            ).mappings()
        )
        for name in m.TABLES
    }


@pytest.mark.parametrize("structural", [False, True])
def test_direct_sql_count_substitution_rejected_at_seal(db, structural):
    data = recipe_data()
    data["variant_rules"][1]["structural"] = structural
    with pytest.raises(IntegrityError, match="V1 COUNT substitution"):
        seed(db, data, CountWriter)
    assert db.scalar(text("SELECT count(*) FROM recipe_versions")) == 0


@pytest.mark.parametrize(
    "base_transform,substitute_transform",
    [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ],
)
@pytest.mark.parametrize("substitute", [False, True])
def test_persisted_snapshot_binds_only_selected_preparation_path(
    db,
    base_transform,
    substitute_transform,
    substitute,
):
    data = recipe_data()
    base, replacement = data["transformations"]
    data["transformations"] = ([base] if base_transform else []) + (
        [replacement] if substitute_transform else []
    )
    original, repo = seed(db, data)
    snapshot = repo.version(original.id)
    assert snapshot == original
    selection = (snapshot.variant_rules[0].id,) if substitute else ()
    if substitute and base_transform and not substitute_transform:
        with pytest.raises(ValueError, match="authored cooking transformation"):
            bind(snapshot, selected_rule_ids=selection)
        return
    result = bind(snapshot, selected_rule_ids=selection)
    expected = replacement if substitute else base
    has_transform = substitute_transform if substitute else base_transform
    assert [t.id for t in result.transformations] == ([expected["id"]] if has_transform else [])


def test_legacy_count_upgrade_fails_closed_preserving_facts(legacy_database):
    engine, config = legacy_database
    migrate(engine, config, "0005")
    with Session(engine) as session:
        seed(session, repository=CountWriter)
        session.commit()
    with engine.connect() as connection:
        before = rows(connection)
    with pytest.raises(IntegrityError, match="0006: legacy COUNT substitutions"):
        migrate(engine, config, "0006")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0005"
        assert rows(connection) == before
        assert (
            connection.scalar(
                text("SELECT to_regprocedure('menuto_recipe_count_substitution_policy()')")
            )
            is None
        )


@pytest.mark.parametrize("populated", [False, True])
def test_0006_roundtrip_preserves_facts_and_original_seal_functions(legacy_database, populated):
    engine, config = legacy_database
    migrate(engine, config, "0005")
    if populated:
        with Session(engine) as session:
            snapshot, _ = seed(session)
            session.commit()
    with engine.connect() as connection:
        before = rows(connection)
        functions = {
            name: connection.scalar(text(f"SELECT pg_get_functiondef('{name}()'::regprocedure)"))
            for name in (
                "menuto_recipe_seal",
                "menuto_recipe_child_insert",
                "menuto_recipe_begin_version",
                "menuto_recipe_immutable",
            )
        }
    for _ in range(2):
        migrate(engine, config, "0006")
        migrate(engine, config, "head")
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.check(config)
            assert rows(connection) == before
            for name, definition in functions.items():
                assert (
                    connection.scalar(text(f"SELECT pg_get_functiondef('{name}()'::regprocedure)"))
                    == definition
                )
        migrate(engine, config, "0005", down=True)
        with engine.connect() as connection:
            assert rows(connection) == before
    migrate(engine, config, "0006")
    if populated:
        with Session(engine) as session:
            assert RecipeRepository(session).version(snapshot.id) == snapshot
        # 0006 may loosen policy on downgrade, but 0005's loss-prevention is untouched.
        with pytest.raises(IntegrityError, match="0005 downgrade would lose"):
            migrate(engine, config, "0004", down=True)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0006"
            assert (
                connection.scalar(
                    text("SELECT to_regprocedure('menuto_recipe_count_substitution_policy()')")
                )
                is not None
            )
