import pytest
from app.modules.catalog.models import Ingredient
from app.modules.catalog.public import add_affinity_feature_term
from app.modules.preferences.public import PreferenceService
from preference_fixtures import command, term
from sqlalchemy.orm import Session
from test_postgres_foundation import db as db
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_foundation import seed_household

pytestmark = pytest.mark.postgres


def seed(db):
    user, house = seed_household(db)
    ingredient = Ingredient(name="Synthetic preference ingredient")
    db.add(ingredient)
    db.flush()
    q = command(
        household_id=house.household_id,
        member_id=house.member_id,
        actor_user_id=user.id,
        target=dict(kind="INGREDIENT", ingredient_id=ingredient.id),
    )
    return PreferenceService(db, actor_user_id=user.id), q


def test_initial_set_idempotent_db_fingerprint(db):
    svc, q = seed(db)
    a = svc.write(q)
    assert a.command_fingerprint == q.fingerprint() and a.member_sequence == 1
    assert svc.write(q) == a


@pytest.mark.parametrize("kind", ["PROTEIN", "METHOD", "FLAVOR"])
def test_reviewed_feature_target(db, kind):
    svc, q = seed(db)
    t = term(kind)
    add_affinity_feature_term(db, t)
    q = type(q).model_validate(q.model_dump() | dict(target=dict(kind=kind, feature_term_id=t.id)))
    assert svc.write(q).command.target.feature_term_id == t.id


def test_coherent_snapshot_roundtrip(postgres_engine):
    with Session(postgres_engine) as db:
        svc, q = seed(db)
        a = svc.write(q)
        db.commit()
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as db,
    ):
        s = PreferenceService(db, actor_user_id=q.actor_user_id).snapshot(
            q.household_id, q.member_id
        )
        assert s.declarations == (a,) and s.frontier == 1
        assert s.state_for(q.target).value == "LIKE"
