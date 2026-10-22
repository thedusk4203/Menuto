"""Real PostgreSQL checks. Each run creates and drops only its own random test database."""

import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.modules.catalog.models import Ingredient, NutritionFact
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
    assert "user_id" not in inspect(HouseholdMember).columns
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
        source_system="synthetic",
        external_record_id="synthetic-only",
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
        {"source_kind": "AUTOPILOT_ASSUMED"},
        {"external_record_id": " "},
    ],
)
def test_inv018_catalog_constraints_cannot_be_bypassed_by_direct_orm(db, fields):
    fact = nutrition_record(db, **fields)
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add(fact)
        db.flush()
    assert error.value.orig.sqlstate == "23514"


def test_catalog_does_not_own_retail_or_recipe_yield_persistence(postgres_engine):
    assert "unit_conversions" not in inspect(postgres_engine).get_table_names()
    assert "unit_conversions" not in Base.metadata.tables


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


def test_raw_sql_nonfinite_nutrition_is_still_rejected_by_database(db):
    fact = nutrition_record(db, energy_kcal=Decimal("NaN"))
    fields = {key: value for key, value in fact.__dict__.items() if key != "_sa_instance_state"}
    fields["id"] = uuid4()
    columns = ", ".join(fields)
    values = ", ".join(":" + key for key in fields)
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.execute(text(f"INSERT INTO nutrition_facts ({columns}) VALUES ({values})"), fields)
    assert error.value.orig.sqlstate == "23514"


def test_exclusions_use_ingredient_identity_not_display_code(db):
    user, result = seed_household(db)
    first = Ingredient(name="Synthetic tomato")
    second = Ingredient(name="Synthetic other")
    db.add_all([first, second])
    db.flush()
    common = dict(
        household_id=result.household_id,
        member_id=result.member_id,
        created_by_user_id=user.id,
        kind="EXCLUDED_INGREDIENT",
    )
    db.add(MemberSafetyConstraint(**common, ingredient_id=first.id, code="tomato"))
    db.flush()
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add(MemberSafetyConstraint(**common, ingredient_id=first.id, code="no-tomato"))
        db.flush()
    assert error.value.orig.sqlstate == "23505"
    assert error.value.orig.diag.constraint_name == "uq_member_safety_excluded_ingredient"
    db.add(MemberSafetyConstraint(**common, ingredient_id=second.id, code="tomato"))
    db.flush()


@pytest.mark.parametrize("kind", ["ALLERGEN", "DIET_RULE"])
def test_named_safety_codes_are_unique_within_member_and_kind(db, kind):
    user, result = seed_household(db)
    fields = dict(
        household_id=result.household_id,
        member_id=result.member_id,
        created_by_user_id=user.id,
        kind=kind,
        code="canonical-code",
    )
    db.add(MemberSafetyConstraint(**fields))
    db.flush()
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add(MemberSafetyConstraint(**fields))
        db.flush()
    assert error.value.orig.sqlstate == "23505"
    assert error.value.orig.diag.constraint_name == "uq_member_safety_code"


def test_account_person_mapping_has_only_membership_as_truth(db):
    _, result = seed_household(db)
    other = User(display_name="Synthetic Bob")
    db.add(other)
    db.flush()
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add(
            Membership(
                household_id=result.household_id,
                user_id=other.id,
                member_id=result.member_id,
                role="VIEWER",
            )
        )
        db.flush()
    assert error.value.orig.sqlstate == "23505"
    assert "user_id" not in {
        c["name"] for c in inspect(db.connection()).get_columns("household_members")
    }
    # An account may participate without claiming to represent a biological member.
    db.add(Membership(household_id=result.household_id, user_id=other.id, role="VIEWER"))
    db.flush()


def test_provider_identity_and_long_locators_roundtrip_without_collision(db):
    fact = nutrition_record(
        db,
        external_record_id="provider/path/" + "x" * 120,
        source_version="feed/2026-10-22 rev 2",
        source_uri="https://retail.example.invalid/item?region=hcm",
        content_hash="a" * 64,
    )
    db.add(fact)
    db.flush()
    fields = {
        key: value
        for key, value in fact.__dict__.items()
        if key not in {"_sa_instance_state", "id", "created_at"}
    }
    db.add(NutritionFact(**{**fields, "source_system": "other-provider"}))
    db.flush()
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add(NutritionFact(**fields))
        db.flush()
    assert error.value.orig.sqlstate == "23505"
    db.expire(fact)
    assert fact.external_record_id.endswith("x" * 120)
    assert fact.source_uri.startswith("https://retail.example.invalid/")
    assert fact.content_hash == "a" * 64


def test_orm_does_not_round_high_precision_bind_behind_policy(db):
    from sqlalchemy.exc import StatementError

    fact = nutrition_record(db, reference_amount=Decimal("108.215184200427"))
    with pytest.raises(StatementError) as error, db.begin_nested():
        db.add(fact)
        db.flush()
    assert "decimal_max_places" in str(error.value.orig)
