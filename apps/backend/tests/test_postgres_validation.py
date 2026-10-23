"""Real source capture consistency and production fail-closed integration."""

from datetime import timedelta
from uuid import uuid4

import pytest
from app.modules.catalog.models import NutritionFact
from app.modules.execution.public import PlanRevisionService
from app.modules.execution.validation_capture import capture_validation_subject
from app.modules.inventory.public import InventoryService
from app.modules.nutrition.models import MemberSafetyConstraint
from app.modules.planning import contracts as plans
from app.modules.validation.public import validate_subject
from inventory_fixtures import acquire
from plan_fixtures import NOW, publish_command
from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_plans import propose, setup
from test_postgres_recipes import seed as seed_recipe
from validation_fixtures import coverage_policy, simple_recipe_data

pytestmark = pytest.mark.postgres


def seed_source(engine, *, unsafe=False):
    with Session(engine) as db:
        service, actor, g = setup(db)
        recipe, _ = seed_recipe(db, simple_recipe_data())
        ingredient = recipe.ingredients[0].ingredient_id
        raw = acquire(g.household_id, actor, ingredient)
        InventoryService(db).acquire(raw)
        db.add(
            NutritionFact(
                ingredient_id=ingredient,
                basis="EP_RAW_G",
                reference_amount="100",
                energy_kcal="200",
                protein_g="20",
                fat_g="5",
                carbohydrate_g="10",
                status="REVIEWED",
                source_kind="REVIEWED_REFERENCE",
                source_system="synthetic.nutrition",
                external_record_id=str(uuid4()),
                source_version="1",
                observed_at=NOW - timedelta(days=1),
            )
        )
        d = g.model_dump()
        batch = uuid4()
        d["meals"][0]["meal_kind"] = "HOME"
        d["batches"] = [
            dict(
                node_id=batch,
                recipe_version_id=recipe.id,
                tier_id=recipe.portion_tiers[0].id,
                planned_servings="2",
                planned_at=NOW + timedelta(hours=1),
            )
        ]
        d["allocations"] = [
            dict(
                node_id=uuid4(), batch_node_id=batch, meal_node_id=g.meals[0].node_id, servings="2"
            )
        ]
        if unsafe:
            db.add(
                MemberSafetyConstraint(
                    household_id=g.household_id,
                    member_id=g.tracked_member_id,
                    kind="EXCLUDED_INGREDIENT",
                    code="explicit.exclusion",
                    ingredient_id=ingredient,
                    created_by_user_id=actor,
                )
            )
        db.flush()
        p, _ = propose(service, actor, plans.PlanIntentGraph.model_validate(d))
        db.commit()
        return (
            dict(household_id=g.household_id, plan_id=g.plan_id, proposal_id=p.id),
            actor,
            ingredient,
        )


def capture(engine, keys, *, isolation="REPEATABLE READ", readonly=True):
    with engine.connect().execution_options(
        isolation_level=isolation, postgresql_readonly=readonly
    ) as conn:
        with Session(conn) as session:
            return capture_validation_subject(session, **keys, policy=coverage_policy())


@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
def test_readonly_capture_is_self_contained_and_does_not_write(postgres_engine, isolation):
    keys, _, _ = seed_source(postgres_engine)
    statements = []

    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lstrip().split()[0].upper())

    event.listen(Engine, "before_cursor_execute", record)
    try:
        s = capture(postgres_engine, keys, isolation=isolation)
    finally:
        event.remove(Engine, "before_cursor_execute", record)
    assert not set(statements) & {"INSERT", "UPDATE", "DELETE", "TRUNCATE"}
    assert s.source_frontier.capture_consistency == isolation.replace(" ", "_")
    assert s.source_frontier.inventory_ledger_sequence == s.inventory.movements[0].ledger_sequence
    assert s.nutrition_references[0].fact.provenance.source_system == "synthetic.nutrition"
    report = validate_subject(s)
    assert report.decision == "BLOCKED_UNSUPPORTED" and not report.activation_authorized
    assert report.default_batch_inputs[0].input_nutrition.energy_kcal == 400
    assert report.material_balances[0].signed_closing_amount == 500


@pytest.mark.parametrize(
    "isolation,readonly", [("READ COMMITTED", True), ("REPEATABLE READ", False)]
)
def test_capture_rejects_unstable_or_writable_transaction(postgres_engine, isolation, readonly):
    keys, _, _ = seed_source(postgres_engine)
    with pytest.raises(ValueError, match="read-only"):
        capture(postgres_engine, keys, isolation=isolation, readonly=readonly)


def test_validator_performs_zero_database_queries_or_writes(postgres_engine):
    keys, _, _ = seed_source(postgres_engine)
    s = capture(postgres_engine, keys)

    def blocked(*args):
        raise AssertionError("Independent validator queried database")

    event.listen(Engine, "before_cursor_execute", blocked)
    try:
        assert validate_subject(s) == validate_subject(s)
    finally:
        event.remove(Engine, "before_cursor_execute", blocked)


def test_canonical_safety_source_is_checked_without_planner_summary(postgres_engine):
    keys, _, ingredient = seed_source(postgres_engine, unsafe=True)
    s = capture(postgres_engine, keys)
    assert s.member_safety[0].constraints[0].constraint.ingredient_id == ingredient
    report = validate_subject(s)
    assert any(f.code == "FORBIDDEN_INGREDIENT" for f in report.findings)
    assert report.decision == "REJECTED" and not report.activation_authorized


def test_rr_capture_sees_one_source_state_during_concurrent_safety_change(postgres_engine):
    keys, actor, ingredient = seed_source(postgres_engine)
    changed = []
    with postgres_engine.connect().execution_options(
        isolation_level="REPEATABLE READ", postgresql_readonly=True
    ) as conn:

        def mutate_after_first_source_read(
            connection, cursor, statement, parameters, context, executemany
        ):
            if "FROM plan_workspaces" in statement and not changed:
                changed.append(True)
                with Session(postgres_engine) as writer:
                    member = writer.scalar(
                        text("SELECT tracked_member_id FROM plan_workspaces WHERE id=:p"),
                        {"p": keys["plan_id"]},
                    )
                    writer.add(
                        MemberSafetyConstraint(
                            household_id=keys["household_id"],
                            member_id=member,
                            kind="EXCLUDED_INGREDIENT",
                            code="explicit.exclusion",
                            ingredient_id=ingredient,
                            created_by_user_id=actor,
                        )
                    )
                    writer.commit()

        event.listen(conn, "after_cursor_execute", mutate_after_first_source_read)
        try:
            with Session(conn) as session:
                original = capture_validation_subject(session, **keys, policy=coverage_policy())
        finally:
            event.remove(conn, "after_cursor_execute", mutate_after_first_source_read)
    assert changed and not original.member_safety[0].constraints
    old_report = validate_subject(original)
    latest = capture(postgres_engine, keys)
    assert latest.member_safety[0].constraints and original.fingerprint != latest.fingerprint
    assert any(f.code == "FORBIDDEN_INGREDIENT" for f in validate_subject(latest).findings)
    assert validate_subject(original) == old_report


def test_partial_precommit_report_cannot_mint_or_publish_authority(postgres_engine):
    keys, actor, _ = seed_source(postgres_engine)
    s = capture(postgres_engine, keys)
    report = validate_subject(s)
    assert report.decision == "BLOCKED_UNSUPPORTED" and not report.activation_authorized
    with Session(postgres_engine) as db:
        with pytest.raises(IntegrityError, match="authority not installed"), db.begin_nested():
            db.execute(
                text("INSERT INTO plan_validation_authorizations (id) VALUES (:id)"),
                {"id": uuid4()},
            )
        with pytest.raises(IntegrityError, match="authorization"):
            PlanRevisionService(db).publish(publish_command(s.proposal, actor, uuid4()))
        assert (
            db.scalar(
                text("SELECT active_revision_no FROM plan_workspaces WHERE id=:id"),
                {"id": keys["plan_id"]},
            )
            is None
        )
        assert (
            InventoryService(db).snapshot(keys["household_id"]).positions[0].remaining.amount == 500
        )


def test_source_capture_cannot_cross_household_and_schema_is_unchanged(postgres_engine):
    keys, _, _ = seed_source(postgres_engine)
    with pytest.raises(NoResultFound):
        capture(postgres_engine, keys | {"household_id": uuid4()})
    with postgres_engine.connect() as conn:
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0009"
        assert len(set(inspect(conn).get_table_names()) - {"alembic_version"}) == 52
