"""Data-bearing 0001 migration checks; only randomly named local test databases."""

import os
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.persistence.database import create_database_engine
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[3]


def migrate(engine, config, revision, *, down=False):
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        operation = command.downgrade if down else command.upgrade
        operation(config, revision)


@pytest.fixture
def legacy_database():
    url = os.environ.get("MENUTO_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set MENUTO_TEST_POSTGRES_URL for real PostgreSQL migration tests")
    parsed = make_url(url)
    if parsed.host not in {"localhost", "127.0.0.1", "::1"} or parsed.database != "postgres":
        pytest.fail("Test admin URL must address the local postgres maintenance database")
    admin = create_database_engine(url).execution_options(isolation_level="AUTOCOMMIT")
    database_name = "menuto_test_" + uuid4().hex
    engine = None
    created = False
    try:
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
            created = True
        engine = create_database_engine(
            parsed.set(database=database_name).render_as_string(hide_password=False)
        )
        config = Config(str(ROOT / "alembic.ini"))
        migrate(engine, config, "0001")
        yield engine, config
    finally:
        if engine is not None:
            engine.dispose()
        if created:
            with admin.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{database_name}"'))
        admin.dispose()


def seed(engine, *, mapping="valid", missing_member_link=False):
    ids = {
        key: uuid4()
        for key in ("alice", "bob", "household", "member", "membership", "ingredient", "fact")
    }
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id,display_name) VALUES "
                "(:alice,'Synthetic Alice'),(:bob,'Synthetic Bob')"
            ),
            ids,
        )
        connection.execute(
            text(
                "INSERT INTO households (id,name,timezone,created_by_user_id) "
                "VALUES (:household,'Synthetic','UTC',:alice)"
            ),
            ids,
        )
        connection.execute(
            text(
                "INSERT INTO household_members (id,household_id,name,user_id) "
                "VALUES (:member,:household,'Synthetic person',:alice)"
            ),
            ids,
        )
        if mapping != "orphan":
            connection.execute(
                text(
                    "INSERT INTO memberships "
                    "(id,household_id,user_id,member_id,role) "
                    "VALUES (:membership,:household,:actor,:linked,'OWNER')"
                ),
                {
                    **ids,
                    "actor": ids["bob" if mapping == "conflict" else "alice"],
                    "linked": None if missing_member_link else ids["member"],
                },
            )
        if mapping == "duplicate_account":
            connection.execute(
                text(
                    "INSERT INTO household_members "
                    "(id,household_id,name,user_id) "
                    "VALUES (:extra,:household,'Second person',:alice)"
                ),
                {**ids, "extra": uuid4()},
            )
        connection.execute(
            text("INSERT INTO ingredients (id,name) VALUES (:ingredient,'Synthetic ingredient')"),
            ids,
        )
        connection.execute(
            text(
                "INSERT INTO nutrition_facts "
                "(id,ingredient_id,basis,reference_amount,energy_kcal,protein_g,"
                "fat_g,carbohydrate_g,status,source_kind,source_ref,source_version,"
                "observed_at) VALUES (:fact,:ingredient,'EP_RAW_G',100,123.456789,"
                "10,2,5,'REVIEWED','REVIEWED_REFERENCE','legacy-record','v1',now())"
            ),
            ids,
        )
    return ids


def assert_still_legacy(engine):
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0001"
        assert "user_id" in {
            c["name"] for c in inspect(connection).get_columns("household_members")
        }
        assert "unit_conversions" in inspect(connection).get_table_names()
        assert connection.scalar(text("SELECT source_ref FROM nutrition_facts")) == "legacy-record"


def test_populated_upgrade_backfills_and_roundtrips_losslessly(legacy_database):
    engine, config = legacy_database
    ids = seed(engine, missing_member_link=True)
    migrate(engine, config, "head")
    with engine.connect() as connection:
        fact = connection.execute(
            text(
                "SELECT source_system,external_record_id,source_version,"
                "energy_kcal FROM nutrition_facts"
            )
        ).one()
        assert tuple(fact) == ("legacy.m0", "legacy-record", "v1", Decimal("123.456789"))
        assert connection.scalar(text("SELECT member_id FROM memberships")) == ids["member"]
        connection.commit()
        config.attributes["connection"] = connection
        command.check(config)
    migrate(engine, config, "0001", down=True)
    assert_still_legacy(engine)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT user_id FROM household_members")) == ids["alice"]
    migrate(engine, config, "head")


@pytest.mark.parametrize("mapping", ["conflict", "orphan", "duplicate_account"])
def test_ambiguous_account_mapping_aborts_transaction(legacy_database, mapping):
    engine, config = legacy_database
    seed(engine, mapping=mapping)
    with pytest.raises(IntegrityError, match="account/person"):
        migrate(engine, config, "head")
    assert_still_legacy(engine)


def test_populated_legacy_yields_are_never_dropped(legacy_database):
    engine, config = legacy_database
    ids = seed(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO unit_conversions "
                "(id,ingredient_id,kind,context_ref,source_basis,target_basis,factor,"
                "source_kind,source_ref,source_version,observed_at) "
                "VALUES (:yield_id,:ingredient,'EDIBLE_YIELD','synthetic-product',"
                "'AP_G','EP_RAW_G',0.8,'USER','legacy-yield','1',now())"
            ),
            {**ids, "yield_id": uuid4()},
        )
    with pytest.raises(IntegrityError, match="Legacy yields"):
        migrate(engine, config, "head")
    assert_still_legacy(engine)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM unit_conversions")) == 1


def test_duplicate_ingredient_exclusions_need_explicit_resolution(legacy_database):
    engine, config = legacy_database
    ids = seed(engine)
    with engine.begin() as connection:
        for label in ("old-label", "another-label"):
            connection.execute(
                text(
                    "INSERT INTO member_safety_constraints "
                    "(id,household_id,member_id,kind,code,ingredient_id,"
                    "created_by_user_id) VALUES (:safety,:household,:member,"
                    "'EXCLUDED_INGREDIENT',:label,:ingredient,:alice)"
                ),
                {**ids, "safety": uuid4(), "label": label},
            )
    with pytest.raises(IntegrityError, match="Duplicate canonical ingredient"):
        migrate(engine, config, "head")
    assert_still_legacy(engine)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM member_safety_constraints")) == 2


def test_downgrade_refuses_to_discard_modern_provenance(legacy_database):
    engine, config = legacy_database
    ids = seed(engine)
    migrate(engine, config, "head")
    locator = "provider/" + "x" * 150
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO nutrition_facts "
                "(id,ingredient_id,basis,reference_amount,energy_kcal,protein_g,"
                "fat_g,carbohydrate_g,status,source_kind,source_system,"
                "external_record_id,source_version,source_uri,observed_at) VALUES "
                "(:modern,:ingredient,'EP_RAW_G',100,123.456789,10,2,5,'REVIEWED',"
                "'REVIEWED_REFERENCE','provider',:locator,'2026 release 1',"
                "'https://example.com/records/1',now())"
            ),
            {**ids, "modern": uuid4(), "locator": locator},
        )
    with pytest.raises(IntegrityError, match="losslessly"):
        migrate(engine, config, "0001", down=True)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0003"
        assert connection.scalar(text("SELECT count(*) FROM nutrition_facts")) == 2
        assert (
            connection.scalar(
                text(
                    "SELECT external_record_id FROM nutrition_facts WHERE source_system='provider'"
                )
            )
            == locator
        )


def test_downgrade_refuses_new_safety_identity_collision(legacy_database):
    engine, config = legacy_database
    ids = seed(engine)
    migrate(engine, config, "head")
    other_ingredient = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO ingredients (id,name) VALUES (:other,'Synthetic second ingredient')"),
            {"other": other_ingredient},
        )
        for ingredient in (ids["ingredient"], other_ingredient):
            connection.execute(
                text(
                    "INSERT INTO member_safety_constraints "
                    "(id,household_id,member_id,kind,code,ingredient_id,created_by_user_id) "
                    "VALUES (:safety,:household,:member,'EXCLUDED_INGREDIENT',"
                    "'shared-label',:excluded,:alice)"
                ),
                {**ids, "safety": uuid4(), "excluded": ingredient},
            )
    with pytest.raises(IntegrityError, match="legacy unique code"):
        migrate(engine, config, "0001", down=True)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0003"
        assert connection.scalar(text("SELECT count(*) FROM member_safety_constraints")) == 2
        indexes = {
            item["name"] for item in inspect(connection).get_indexes("member_safety_constraints")
        }
        assert "uq_member_safety_excluded_ingredient" in indexes
