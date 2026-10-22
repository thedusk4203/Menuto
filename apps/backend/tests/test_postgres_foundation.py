"""Real PostgreSQL checks. Each run creates and drops only its own random test database."""

import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.modules.catalog.models import Ingredient, NutritionFact, UnitConversion
from app.modules.households.contracts import HouseholdCreate
from app.modules.households.models import Household, HouseholdMember, Membership
from app.modules.households.public import create_default_household
from app.modules.identity.models import User
from app.modules.nutrition.models import MemberNutritionProfile, MemberSafetyConstraint
from app.persistence.database import create_database_engine
from app.persistence.models import Base
from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def postgres_engine():
    url = os.environ.get("MENUTO_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set MENUTO_TEST_POSTGRES_URL for isolated real-PostgreSQL integration tests")
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
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            assert set(inspect(connection).get_table_names()) == {
                "alembic_version",
                *Base.metadata.tables,
            }
            command.check(config)
            # Inspector starts a transaction; finish it before the downgrade transaction.
            connection.commit()
            command.downgrade(config, "base")
            assert set(inspect(connection).get_table_names()) == {"alembic_version"}
            connection.commit()
            command.upgrade(config, "head")
        yield engine
    finally:
        if engine is not None:
            engine.dispose()
        if created:
            with admin.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{database_name}"'))
        admin.dispose()


@pytest.fixture
def db(postgres_engine):
    with Session(postgres_engine) as session:
        yield session
        session.rollback()


def seed_household(session):
    user = User(display_name="Synthetic test actor")
    session.add(user)
    session.flush()
    result = create_default_household(
        session,
        actor_user_id=user.id,
        request=HouseholdCreate(name="Synthetic household", member_name="Synthetic member"),
    )
    return user, result


def test_atomic_default_household_and_member(db):
    user, result = seed_household(db)
    household = db.get(Household, result.household_id)
    assert household.created_by_user_id == user.id
    member = db.get(HouseholdMember, result.member_id)
    assert member.household_id == household.id
    assert member.user_id == user.id
    membership = db.scalar(select(Membership).where(Membership.household_id == household.id))
    assert (membership.role, membership.user_id, membership.member_id) == (
        "OWNER",
        user.id,
        member.id,
    )


def test_bootstrap_rolls_back_with_callers_transaction(postgres_engine):
    with Session(postgres_engine) as session:
        user, result = seed_household(session)
        user_id = user.id
        session.rollback()
    with Session(postgres_engine) as session:
        assert session.get(User, user_id) is None
        assert session.get(Household, result.household_id) is None
        assert session.get(HouseholdMember, result.member_id) is None


def test_unknown_actor_cannot_create_household(db):
    before = db.scalar(select(func.count()).select_from(Household))
    with pytest.raises(IntegrityError), db.begin_nested():
        create_default_household(
            db,
            actor_user_id=uuid4(),
            request=HouseholdCreate(name="Invalid actor", member_name="Not persisted"),
        )
    assert db.scalar(select(func.count()).select_from(Household)) == before


@pytest.mark.parametrize("record_type", ["membership", "profile", "safety"])
def test_inv003_cross_household_member_links_are_rejected_by_database(db, record_type):
    user, first = seed_household(db)
    _, second = seed_household(db)
    common = {"household_id": first.household_id, "member_id": second.member_id}
    if record_type == "membership":
        # Use a fresh user so the member/household FK is the constraint under test.
        another = User(display_name="Another actor")
        db.add(another)
        db.flush()
        record = Membership(**common, user_id=another.id, role="VIEWER")
    elif record_type == "profile":
        record = MemberNutritionProfile(**common, created_by_user_id=user.id)
    else:
        record = MemberSafetyConstraint(
            **common, kind="ALLERGEN", code="peanut", created_by_user_id=user.id
        )
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add(record)
        db.flush()
    assert (
        error.value.orig.sqlstate == "23503"
    )  # Foreign-key violation, not an unrelated unique key.


def nutrition_record(db, **overrides):
    ingredient = Ingredient(name="Synthetic ingredient")
    db.add(ingredient)
    db.flush()
    fields = dict(
        ingredient_id=ingredient.id,
        basis="EP_RAW_G",
        reference_amount=Decimal(100),
        energy_kcal=Decimal("123.456789"),
        protein_g=Decimal(10),
        fat_g=Decimal(2),
        carbohydrate_g=Decimal(5),
        status="REVIEWED",
        source_kind="REVIEWED_REFERENCE",
        source_ref="synthetic-only",
        source_version="1",
        observed_at=datetime.now(UTC),
    )
    fields.update(overrides)
    return NutritionFact(**fields)


def test_nutrition_decimal_and_timezone_roundtrip(db):
    fact = nutrition_record(db)
    db.add(fact)
    db.flush()
    db.expire(fact)
    assert fact.energy_kcal == Decimal("123.456789")
    assert fact.observed_at.utcoffset().total_seconds() == 0


@pytest.mark.parametrize(
    "fields",
    [
        {"basis": "AP_G"},
        {"basis": "SERVING"},
        {"reference_amount": Decimal(0)},
        {"energy_kcal": Decimal(-1)},
        {"energy_kcal": Decimal("NaN")},
        {"source_kind": "AUTOPILOT_ASSUMED"},
        {"source_ref": " "},
    ],
)
def test_inv018_catalog_constraints_cannot_be_bypassed_by_direct_orm(db, fields):
    fact = nutrition_record(db, **fields)
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add(fact)
        db.flush()
    assert error.value.orig.sqlstate == "23514"


def test_conversion_context_and_yield_chain_constraints(db):
    ingredient = Ingredient(name="Synthetic conversion ingredient")
    db.add(ingredient)
    db.flush()
    fields = dict(
        ingredient_id=ingredient.id,
        kind="EDIBLE_YIELD",
        context_ref="product-map-v1",
        source_basis="AP_G",
        target_basis="EP_RAW_G",
        factor=Decimal("0.8"),
        source_kind="REVIEWED_REFERENCE",
        source_ref="synthetic",
        source_version="1",
        observed_at=datetime.now(UTC),
    )
    for changed in (
        {"factor": Decimal("1.1")},
        {"target_basis": "COOKED_G"},
        {"context_ref": ""},
        {"source_ref": ""},
        {"factor": Decimal("NaN")},
    ):
        with pytest.raises(IntegrityError), db.begin_nested():
            db.add(UnitConversion(**{**fields, **changed}))
            db.flush()
    db.add(UnitConversion(**fields))
    db.flush()


@pytest.mark.parametrize("mutation", ["UPDATE", "DELETE"])
def test_catalog_source_facts_are_append_only_even_for_sql(db, mutation):
    fact = nutrition_record(db)
    db.add(fact)
    db.flush()
    sql = (
        "UPDATE nutrition_facts SET energy_kcal = 999 WHERE id = :id"
        if mutation == "UPDATE"
        else "DELETE FROM nutrition_facts WHERE id = :id"
    )
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.execute(text(sql), {"id": fact.id})
    assert error.value.orig.sqlstate == "23514"


def test_stale_profile_write_is_rejected_across_sessions(postgres_engine):
    with Session(postgres_engine) as setup:
        user, result = seed_household(setup)
        profile = MemberNutritionProfile(
            household_id=result.household_id,
            member_id=result.member_id,
            created_by_user_id=user.id,
            body_mass_kg=Decimal(60),
        )
        setup.add(profile)
        setup.commit()
        profile_id = profile.id
    with Session(postgres_engine) as first, Session(postgres_engine) as second:
        a = first.get(MemberNutritionProfile, profile_id)
        b = second.get(MemberNutritionProfile, profile_id)
        a.body_mass_kg = Decimal(61)
        first.commit()
        b.body_mass_kg = Decimal(62)
        with pytest.raises(StaleDataError):
            second.commit()
