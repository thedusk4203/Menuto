"""Real PostgreSQL F tests. Synthetic authorization fixture is NOT a validator.

Only this test module's database-owner fixture disables the authorization insertion
trigger around seeding a receipt, then restores it. No production bypass/issuer exists.
This exercises downstream transaction plumbing without claiming production validation.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command as alembic_command
from app.domain.units import Quantity
from app.modules.execution.public import PlanRevisionService
from app.modules.inventory.contracts import ConsumeInventoryCommand
from app.modules.inventory.public import InventoryService
from app.modules.planning import contracts as c
from app.modules.planning import models as m
from app.modules.planning.public import PlanStore
from app.modules.shopping.public import observed_acquisition_coverage
from inventory_fixtures import acquire
from inventory_fixtures import command as inventory_command
from plan_fixtures import NOW, graph_data, propose_command, publish_command
from sqlalchemy import func, insert, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from test_foundation_migration import legacy_database as legacy_database
from test_foundation_migration import migrate
from test_postgres_foundation import db as db
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_foundation import seed_household
from test_postgres_recipes import seed as seed_recipe

pytestmark = pytest.mark.postgres


def setup(db):
    user, house = seed_household(db)
    data = graph_data(house.household_id, member=house.member_id)
    graph = c.PlanIntentGraph.model_validate(data)
    service = PlanRevisionService(db)
    store = service.store
    store.create_workspace(
        plan_id=graph.plan_id,
        household_id=graph.household_id,
        tracked_member_id=graph.tracked_member_id,
        horizon=graph.horizon,
        actor_user_id=user.id,
    )
    return service, user.id, graph


def propose(service, actor, graph, **kw):
    w = service.store.workspace(graph.household_id, graph.plan_id)
    request = propose_command(
        graph,
        actor,
        expected_generation=w.latest_proposal_no,
        expected_revision=w.active_revision_no,
        **kw,
    )
    return service.propose(request), request


def synthetic_authorization(db, proposal, **kw):
    """Explicit TEST DATABASE OWNER setup, never an app/runtime capability issuer."""
    store = PlanStore(db)
    g = proposal.graph
    fields = (
        dict(
            created_at=store.clock() - timedelta(hours=2),
            id=uuid4(),
            household_id=g.household_id,
            plan_id=g.plan_id,
            proposal_id=proposal.id,
            graph_hash=proposal.graph_hash,
            subject_hash="a" * 64,
            report_digest="b" * 64,
            validator_version="SYNTHETIC_TEST_FIXTURE_NOT_INDEPENDENT_VALIDATOR",
            inventory_frontier=store.inventory_frontier(g.household_id),
            boundary_version=store.workspace(g.household_id, g.plan_id).boundary_version,
            valid_until=store.clock() + timedelta(hours=1),
        )
        | kw
    )
    db.execute(text("ALTER TABLE plan_validation_authorizations DISABLE TRIGGER plan_insert"))
    db.execute(insert(m.PlanValidationAuthorization.__table__).values(**fields))
    db.execute(text("ALTER TABLE plan_validation_authorizations ENABLE TRIGGER plan_insert"))
    return fields["id"]


def publish(db, service, actor, proposal, **kw):
    receipt = synthetic_authorization(db, proposal, **kw)
    request = publish_command(proposal, actor, receipt)
    return service.publish(request), request


def changed(graph, index=0):
    d = graph.model_dump()
    d["meals"][index]["meal_kind"] = (
        "SKIP" if d["meals"][index]["meal_kind"] == "OUTSIDE" else "OUTSIDE"
    )
    return c.PlanIntentGraph.model_validate(d)


def test_authoring_roundtrip_hash_and_no_physical_side_effect(db):
    service, actor, g = setup(db)
    p, request = propose(service, actor, g)
    assert p.graph_hash == g.fingerprint()
    assert service.propose(request) == p
    assert c.PlanProposalSnapshot.model_validate_json(p.model_dump_json()) == p
    w = service.store.workspace(g.household_id, g.plan_id)
    assert w.state == "DRAFT" and w.active_revision_no is None and w.latest_proposal_no == 0
    assert db.scalar(select(func.count()).select_from(m.PlanRevision)) == 0
    assert not p.activation_ready
    with pytest.raises(ValueError, match="Idempotency"):
        service.propose(
            c.ProposePlanCommand.model_validate(request.model_dump() | {"reason": "different"})
        )


def test_production_gate_cannot_mint_or_activate(db):
    service, actor, g = setup(db)
    p, _ = propose(service, actor, g)
    with pytest.raises(IntegrityError, match="authority not installed"), db.begin_nested():
        db.execute(
            insert(m.PlanValidationAuthorization.__table__).values(
                id=uuid4(),
                household_id=g.household_id,
                plan_id=g.plan_id,
                proposal_id=p.id,
                graph_hash=p.graph_hash,
                subject_hash="a" * 64,
                report_digest="b" * 64,
                validator_version="caller",
                inventory_frontier=0,
                boundary_version=0,
                valid_until=NOW + timedelta(hours=1),
            )
        )
    with pytest.raises(IntegrityError, match="authorization absent"):
        service.publish(publish_command(p, actor, uuid4()))
    assert service.store.workspace(g.household_id, g.plan_id).state == "DRAFT"
    assert db.scalar(select(func.count()).select_from(m.PlanRevision)) == 0


def test_synthetic_gate_revision0_stable_id_cas_and_retry(db):
    service, actor, g = setup(db)
    p, _ = propose(service, actor, g)
    baseline, request = publish(db, service, actor, p)
    assert baseline.revision_no == 0 and baseline.reason_kind == "INITIAL_ACTIVATED_BASELINE"
    p1, _ = propose(service, actor, changed(g), scope="SINGLE_MEAL")
    revision, _ = publish(db, service, actor, p1)
    assert revision.revision_no == 1 and revision.parent_revision_no == 0
    assert service.publish(request) == baseline  # retry original result even after head moved
    assert service.store.workspace(g.household_id, g.plan_id).id == g.plan_id
    assert service.store.revision(g.household_id, g.plan_id, 0) == baseline


@pytest.mark.parametrize("scope", ["SINGLE_MEAL", "PROCUREMENT_ONLY"])
def test_direct_sql_scope_and_dependency_closure(db, scope):
    service, actor, g = setup(db)
    p, _ = propose(service, actor, g)
    publish(db, service, actor, p)
    data = changed(changed(g), 1) if scope == "SINGLE_MEAL" else changed(g)
    with pytest.raises(IntegrityError, match="scope"):
        propose(service, actor, data, scope=scope)
    assert service.store.workspace(g.household_id, g.plan_id).latest_proposal_no == 0


def test_past_advice_not_consumption_and_no_rewrite(db):
    service, actor, g = setup(db)
    p, _ = propose(service, actor, g)
    publish(db, service, actor, p)
    with pytest.raises(IntegrityError, match="past advice"):
        propose(
            service,
            actor,
            changed(g),
            scope="SINGLE_MEAL",
            effective_from=NOW + timedelta(days=1, hours=1),
        )
    assert db.scalar(text("SELECT count(*) FROM inventory_movements")) == 0


@pytest.mark.parametrize(
    "table",
    [
        *m.TABLES,
        "planned_cooking_batches",
        "planned_batch_allocations",
        "shopping_requirement_intents",
    ],
)
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE"])
def test_direct_sql_immutability(db, table, operation):
    if table in {"planned_culinary_bindings", "culinary_requirement_bindings"}:
        from test_postgres_culinary_bindings import bound, request

        service, actor, g, _ = bound(db)
        service.propose(request(service, actor, g))
    else:
        service, actor, g = fully_populated(db)
    # Statement TRUNCATE guards fire on empty tables too. Row guards need an existing row.
    if operation == "TRUNCATE":
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        sql = f"TRUNCATE {table} CASCADE"
    elif operation == "DELETE":
        sql = f"DELETE FROM {table}"
    else:
        col = (
            "id"
            if table
            in {
                "plan_workspaces",
                "plan_proposals",
                "plan_validation_authorizations",
                "plan_revisions",
                "plan_materialization_links",
            }
            else "proposal_id"
        )
        sql = f"UPDATE {table} SET {col}={col}"
    assert db.scalar(text(f"SELECT count(*) FROM {table}")) > 0
    with pytest.raises(IntegrityError, match="immutable|transaction-controlled"), db.begin_nested():
        db.execute(text(sql))


@pytest.mark.parametrize(
    "frontier", ["inventory_frontier", "boundary_version", "graph_hash", "valid_until"]
)
def test_authorization_context_and_frontiers_fail_closed(db, frontier):
    service, actor, g = setup(db)
    p, _ = propose(service, actor, g)
    value = (
        NOW - timedelta(hours=1)
        if frontier == "valid_until"
        else "c" * 64
        if frontier == "graph_hash"
        else 999
    )
    receipt = synthetic_authorization(db, p, **{frontier: value})
    with pytest.raises(IntegrityError, match="authorization absent"):
        service.publish(publish_command(p, actor, receipt))
    assert service.store.workspace(g.household_id, g.plan_id).active_revision_no is None


def test_late_child_or_unsealed_aggregate_cannot_commit(db):
    service, actor, g = setup(db)
    p, _ = propose(service, actor, g)
    with pytest.raises(IntegrityError, match="assembly is closed"), db.begin_nested():
        db.execute(
            text(
                "INSERT INTO plan_meal_intents "
                "(proposal_id,node_id,household_id,plan_id,scheduled_at,meal_kind,status) "
                "SELECT proposal_id,:id,household_id,plan_id,"
                "scheduled_at,meal_kind,status FROM plan_meal_intents LIMIT 1"
            ),
            {"id": uuid4()},
        )


def test_reservation_swap_atomic_and_stock_unchanged(db):
    service, actor, g = setup(db)
    inv = InventoryService(db)
    from app.modules.catalog.models import Ingredient

    ingredient = Ingredient(name="Confirmed inventory")
    db.add(ingredient)
    db.flush()
    a = acquire(g.household_id, actor, ingredient.id)
    inv.acquire(a)
    d = g.model_dump()
    key = uuid4()
    d["reservations"] = [
        dict(
            node_id=key,
            meal_node_id=g.meals[0].node_id,
            lot_id=a.lot_id,
            quantity=Quantity(amount=300, basis="EP_RAW_G"),
        )
    ]
    graph = c.PlanIntentGraph.model_validate(d)
    p, _ = propose(service, actor, graph)
    publish(db, service, actor, p)
    initial = inv.snapshot(g.household_id)
    old_res = initial.reservations[0].id
    p1, _ = propose(service, actor, changed(graph), scope="SINGLE_MEAL")
    publish(db, service, actor, p1)
    snap = inv.snapshot(g.household_id)
    assert len(snap.movements) == 1 and snap.positions[0].remaining.amount == 500
    assert old_res in {r.reservation_id for r in snap.releases}
    assert snap.positions[0].reserved.amount == 300 and len(snap.reservations) == 2


def test_failed_rebuild_rolls_back_head_release_revision_and_command(db):
    service, actor, g = setup(db)
    from app.modules.catalog.models import Ingredient

    i = Ingredient(name="Confirmed stock")
    db.add(i)
    db.flush()
    inv = InventoryService(db)
    a = acquire(g.household_id, actor, i.id)
    inv.acquire(a)
    d = g.model_dump()
    d["reservations"] = [
        dict(
            node_id=uuid4(),
            meal_node_id=g.meals[0].node_id,
            lot_id=a.lot_id,
            quantity=Quantity(amount=300, basis="EP_RAW_G"),
        )
    ]
    g = c.PlanIntentGraph.model_validate(d)
    p, _ = propose(service, actor, g)
    publish(db, service, actor, p)
    d = changed(g).model_dump()
    d["reservations"][0]["quantity"]["amount"] = "600"
    next_graph = c.PlanIntentGraph.model_validate(d)
    p1, _ = propose(service, actor, next_graph, scope="SINGLE_MEAL")
    receipt = synthetic_authorization(db, p1)
    request = publish_command(p1, actor, receipt)
    with pytest.raises(IntegrityError, match="insufficient"):
        service.publish(request)
    w = service.store.workspace(g.household_id, g.plan_id)
    assert w.active_revision_no == 0
    snap = inv.snapshot(g.household_id)
    assert (
        not snap.releases
        and len(snap.reservations) == 1
        and snap.positions[0].remaining.amount == 500
    )
    assert db.scalar(select(func.count()).select_from(m.PlanRevision)) == 1


def test_partial_acquisition_not_boolean_fulfillment_and_lot_survives_revision(db):
    service, actor, g = setup(db)
    from app.modules.catalog.models import Ingredient

    i = Ingredient(name="Chicken")
    db.add(i)
    db.flush()
    d = g.model_dump()
    key = uuid4()
    d["shopping"] = [
        dict(
            node_id=key,
            ingredient_id=i.id,
            quantity=Quantity(amount=1000, basis="EP_RAW_G"),
            need_by=NOW + timedelta(days=1),
        )
    ]
    g = c.PlanIntentGraph.model_validate(d)
    p, _ = propose(service, actor, g)
    publish(db, service, actor, p)
    inv = InventoryService(db)
    a = acquire(g.household_id, actor, i.id, quantity=Quantity(amount=600, basis="EP_RAW_G"))
    movement = inv.acquire(a)
    service.store.link_materialization(
        household_id=g.household_id,
        plan_id=g.plan_id,
        source_revision_no=0,
        lot_id=a.lot_id,
        movement_id=movement.id,
        actor_user_id=actor,
        shopping_node_id=key,
    )
    progress = observed_acquisition_coverage(
        p, g.shopping[0].node_id, inv.snapshot(g.household_id), (movement.id,)
    )
    assert (
        progress.acquired.amount == 600
        and progress.shortfall.amount == 400
        and not progress.activation_ready
    )
    d = g.model_dump()
    d["shopping"][0]["status"] = "RETIRED"
    p1, _ = propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="PROCUREMENT_ONLY")
    publish(db, service, actor, p1)
    assert inv.snapshot(g.household_id).positions[0].remaining.amount == 600


def test_batch_already_cooked_production_pinned_future_allocation_revisable(db):
    service, actor, g = setup(db)
    recipe, _ = seed_recipe(db)
    tier = recipe.portion_tiers[0]
    d = g.model_dump()
    batch = uuid4()
    d["meals"][0]["meal_kind"] = "HOME"
    d["meals"][1]["meal_kind"] = "HOME"
    d["batches"] = [
        dict(
            node_id=batch,
            recipe_version_id=recipe.id,
            tier_id=tier.id,
            planned_servings=tier.servings,
            planned_at=NOW,
        )
    ]
    d["allocations"] = [
        dict(node_id=uuid4(), batch_node_id=batch, meal_node_id=m["node_id"], servings="1")
        for m in d["meals"]
    ]
    g = c.PlanIntentGraph.model_validate(d)
    p, _ = propose(service, actor, g)
    publish(db, service, actor, p)
    inv = InventoryService(db)
    a = acquire(
        g.household_id,
        actor,
        asset_type="COOKED_DISH",
        ingredient_id=None,
        quantity=Quantity(amount="1.5", basis="SERVING", item_ref="synthetic.batch.serving"),
        serving_definition="One authored serving",
    )
    movement = inv.acquire(a)
    service.store.link_materialization(
        household_id=g.household_id,
        plan_id=g.plan_id,
        source_revision_no=0,
        batch_node_id=batch,
        lot_id=a.lot_id,
        movement_id=movement.id,
        actor_user_id=actor,
    )
    d = g.model_dump()
    d["meals"][1]["meal_kind"] = "OUTSIDE"
    d["allocations"][1]["status"] = "RETIRED"
    p1, _ = propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="SINGLE_MEAL")
    publish(db, service, actor, p1)
    assert (
        inv.snapshot(g.household_id).positions[0].remaining.amount
        == c.Quantity(amount="1.5", basis="SERVING", item_ref="synthetic.batch.serving").amount
    )
    assert p1.graph.batches[0].planned_servings == tier.servings
    d = p1.graph.model_dump()
    d["batches"][0]["planned_at"] = NOW + timedelta(minutes=1)
    with pytest.raises(IntegrityError, match="materialized"):
        propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="MULTI_MEAL")


def test_execution_deviation_and_late_source_do_not_create_revision(db):
    service, actor, g = setup(db)
    p, _ = propose(service, actor, g)
    publish(db, service, actor, p)
    from app.modules.catalog.models import Ingredient

    i = Ingredient(name="Explicit meal food")
    db.add(i)
    db.flush()
    inv = InventoryService(db)
    a = acquire(g.household_id, actor, i.id)
    inv.acquire(a)
    meal = inv.consume(inventory_command(ConsumeInventoryCommand, a, amount="100"))
    p1, _ = propose(service, actor, changed(g), scope="SINGLE_MEAL")
    publish(db, service, actor, p1)
    service.store.link_materialization(
        household_id=g.household_id,
        plan_id=g.plan_id,
        source_revision_no=0,
        meal_node_id=g.meals[0].node_id,
        lot_id=a.lot_id,
        movement_id=meal.id,
        actor_user_id=actor,
    )
    assert service.store.workspace(g.household_id, g.plan_id).active_revision_no == 1
    with pytest.raises(IntegrityError, match="materialized"):
        propose(service, actor, changed(changed(g), 1), scope="MULTI_MEAL")


def test_concurrent_revision4_writers_no_two_revision5s(postgres_engine):
    with Session(postgres_engine) as db:
        service, actor, g = setup(db)
        p, _ = propose(service, actor, g)
        publish(db, service, actor, p)
        for index in range(4):
            g = changed(g)
            p, _ = propose(service, actor, g, scope="SINGLE_MEAL")
            publish(db, service, actor, p)
        a, _ = propose(service, actor, changed(g), scope="SINGLE_MEAL")
        d = g.model_dump()
        d["meals"][0]["scheduled_at"] += timedelta(hours=1)
        b, _ = propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="SINGLE_MEAL")
        requests = [publish_command(p, actor, synthetic_authorization(db, p)) for p in [a, b]]
        db.commit()
    barrier = Barrier(2)

    def writer(request):
        with Session(postgres_engine) as session:
            barrier.wait(timeout=10)
            try:
                PlanRevisionService(session).publish(request)
                session.commit()
                return "ok"
            except DBAPIError as error:
                session.rollback()
                return error.orig.sqlstate

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(writer, requests))
    assert sorted(results) == ["23514", "ok"]
    with Session(postgres_engine) as session:
        assert PlanStore(session).workspace(g.household_id, g.plan_id).active_revision_no == 5
        assert (
            session.scalar(
                select(func.count())
                .select_from(m.PlanRevision)
                .where(m.PlanRevision.plan_id == g.plan_id)
            )
            == 6
        )


@pytest.mark.parametrize("populated", [False, True])
def test_migration_roundtrip_lossless_foundation_and_populated_guard(legacy_database, populated):
    engine, config = legacy_database
    migrate(engine, config, "0007")
    if populated:
        with Session(engine) as session:
            seed_household(session)
            session.commit()
    for _ in range(2):
        migrate(engine, config, "head")
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            alembic_command.check(config)
        migrate(engine, config, "0007", down=True)
    migrate(engine, config, "head")
    with Session(engine) as session:
        service, actor, g = setup(session)
        p, _ = propose(service, actor, g)
        session.commit()
    with pytest.raises(IntegrityError, match="would lose intent"):
        migrate(engine, config, "0007", down=True)
    with Session(engine) as session:
        assert PlanStore(session).proposal(g.household_id, g.plan_id, p.id) == p
        assert session.scalar(text("SELECT version_num FROM alembic_version")) == "0011"


def fully_populated(db):
    """Every new table has rows: guards are tested on actual history, not no-op SQL."""
    from app.modules.catalog.models import Ingredient

    service, actor, g = setup(db)
    recipe, _ = seed_recipe(db)
    ingredient = Ingredient(name="Physical stock")
    db.add(ingredient)
    db.flush()
    inv = InventoryService(db)
    raw = acquire(g.household_id, actor, ingredient.id)
    movement = inv.acquire(raw)
    d = g.model_dump()
    batch = uuid4()
    tier = recipe.portion_tiers[0]
    d["batches"] = [
        dict(
            node_id=batch,
            recipe_version_id=recipe.id,
            tier_id=tier.id,
            planned_servings=tier.servings,
            planned_at=NOW,
        )
    ]
    d["meals"][0]["meal_kind"] = "HOME"
    d["allocations"] = [
        dict(node_id=uuid4(), batch_node_id=batch, meal_node_id=g.meals[0].node_id, servings="1")
    ]
    shop = uuid4()
    d["shopping"] = [
        dict(
            node_id=shop,
            ingredient_id=ingredient.id,
            quantity=Quantity(amount=1000, basis="EP_RAW_G"),
            need_by=NOW,
        )
    ]
    d["reservations"] = [
        dict(
            node_id=uuid4(),
            meal_node_id=g.meals[0].node_id,
            lot_id=raw.lot_id,
            quantity=Quantity(amount=100, basis="EP_RAW_G"),
        )
    ]
    g = c.PlanIntentGraph.model_validate(d)
    p, _ = propose(service, actor, g)
    publish(db, service, actor, p)
    service.store.link_materialization(
        household_id=g.household_id,
        plan_id=g.plan_id,
        source_revision_no=0,
        shopping_node_id=shop,
        lot_id=raw.lot_id,
        movement_id=movement.id,
        actor_user_id=actor,
    )
    return service, actor, g


@pytest.mark.parametrize(
    "mutation", ["household", "member", "tier", "basis", "negative", "nonfinite", "precision"]
)
def test_sql_cannot_bypass_critical_graph_context(db, mutation):
    from app.modules.catalog.models import Ingredient
    from app.modules.cooking.models import PlannedCookingBatch

    service, actor, g = setup(db)
    other_user, other_house = seed_household(db)
    ingredient = Ingredient(name="Test source")
    db.add(ingredient)
    db.flush()
    recipe, _ = seed_recipe(db)
    request = propose_command(g, actor)
    with pytest.raises(IntegrityError), db.begin_nested():
        service.store.begin_proposal(request, "a" * 64)
        ctx = dict(proposal_id=request.proposal_id, household_id=g.household_id, plan_id=g.plan_id)
        if mutation in {"household", "member"}:
            db.execute(
                insert(m.PlanMealParticipant.__table__).values(
                    **(
                        ctx
                        | (
                            {"household_id": other_house.household_id}
                            if mutation == "household"
                            else {}
                        )
                    ),
                    meal_node_id=g.meals[0].node_id,
                    member_id=other_house.member_id,
                    portion_factor=1,
                    nutrition_role="SHARED",
                )
            )
        elif mutation == "tier":
            db.execute(
                insert(PlannedCookingBatch.__table__).values(
                    **ctx,
                    node_id=uuid4(),
                    recipe_version_id=recipe.id,
                    tier_id=recipe.portion_tiers[0].id,
                    planned_servings=999,
                    planned_at=NOW,
                    status="PLANNED",
                )
            )
        else:
            amount = {"negative": "-1", "nonfinite": "NaN", "precision": "0.0000001"}.get(
                mutation, "1"
            )
            from test_postgres_retail import insert_sql

            insert_sql(
                db,
                "shopping_requirement_intents",
                dict(
                    **ctx,
                    node_id=uuid4(),
                    ingredient_id=ingredient.id,
                    amount=amount,
                    basis="SERVING" if mutation == "basis" else "EP_RAW_G",
                    item_ref=None,
                    need_by=NOW,
                    status="PLANNED",
                ),
            )
        service.store.seal(request.proposal_id)
    assert service.store.workspace(g.household_id, g.plan_id).latest_proposal_no == -1


def test_unsealed_proposal_cannot_commit(db):
    service, actor, g = setup(db)
    with pytest.raises(IntegrityError), db.begin_nested():
        service.store.begin_proposal(propose_command(g, actor), "a" * 64)
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    assert service.store.workspace(g.household_id, g.plan_id).latest_proposal_no == -1


def test_acquisition_coverage_rejects_foreign_household_and_duplicate_evidence(db):
    service, actor, g = fully_populated(db)
    p = service.store.proposal(
        g.household_id,
        g.plan_id,
        db.scalar(select(m.PlanProposal.id).where(m.PlanProposal.plan_id == g.plan_id)),
    )
    _, other_actor, other_graph = setup(db)
    foreign = InventoryService(db).snapshot(other_graph.household_id)
    with pytest.raises(ValueError, match="household"):
        observed_acquisition_coverage(p, g.shopping[0].node_id, foreign, ())
    inventory = InventoryService(db).snapshot(g.household_id)
    movement = inventory.movements[0].id
    with pytest.raises(ValueError, match="Duplicate"):
        observed_acquisition_coverage(p, g.shopping[0].node_id, inventory, (movement, movement))


def test_direct_revision_cannot_skip_retired_reservation_release(db):
    service, actor, g = fully_populated(db)
    d = g.model_dump()
    d["reservations"] = []
    p, _ = propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="PROCUREMENT_ONLY")
    auth = synthetic_authorization(db, p)
    command = publish_command(p, actor, auth)
    with pytest.raises(IntegrityError, match="release or retain"), db.begin_nested():
        service.store.publish_header(command, "a" * 64)
        service.store.complete()
    assert service.store.workspace(g.household_id, g.plan_id).active_revision_no == 0


def test_concurrent_plan_and_manual_reservation_share_frozen_inventory_fence(postgres_engine):
    from app.modules.catalog.models import Ingredient
    from app.modules.inventory.contracts import ReserveInventoryCommand

    with Session(postgres_engine) as db:
        service, actor, g = setup(db)
        i = Ingredient(name="Shared real stock")
        db.add(i)
        db.flush()
        a = acquire(g.household_id, actor, i.id)
        InventoryService(db).acquire(a)
        d = g.model_dump()
        d["reservations"] = [
            dict(
                node_id=uuid4(),
                meal_node_id=g.meals[0].node_id,
                lot_id=a.lot_id,
                quantity=Quantity(amount=300, basis="EP_RAW_G"),
            )
        ]
        g = c.PlanIntentGraph.model_validate(d)
        p, _ = propose(service, actor, g)
        request = publish_command(p, actor, synthetic_authorization(db, p))
        manual = inventory_command(
            ReserveInventoryCommand, a, amount="300", reservation_id=uuid4(), purpose="Manual"
        )
        db.commit()
    barrier = Barrier(2)

    def writer(kind):
        with Session(postgres_engine) as session:
            barrier.wait(timeout=10)
            try:
                if kind == "plan":
                    PlanRevisionService(session).publish(request)
                else:
                    InventoryService(session).reserve(manual)
                session.commit()
                return "ok"
            except DBAPIError as exc:
                session.rollback()
                return exc.orig.sqlstate

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(writer, ["plan", "manual"]))
    assert sorted(results) == ["23514", "ok"]
    with Session(postgres_engine) as session:
        snap = InventoryService(session).snapshot(g.household_id)
        assert (
            snap.positions[0].remaining.amount == 500 and snap.positions[0].reserved.amount == 300
        )


def test_repeatable_read_revision_writer_rejects_stale_snapshot(postgres_engine):
    with Session(postgres_engine) as db:
        service, actor, g = setup(db)
        p, _ = propose(service, actor, g)
        publish(db, service, actor, p)
        a, _ = propose(service, actor, changed(g), scope="SINGLE_MEAL")
        b, _ = propose(service, actor, changed(g, 1), scope="SINGLE_MEAL")
        requests = [publish_command(p, actor, synthetic_authorization(db, p)) for p in (a, b)]
        db.commit()
    with postgres_engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
        with Session(conn) as stale:
            PlanStore(stale).workspace(g.household_id, g.plan_id)
            with Session(postgres_engine) as fresh:
                PlanRevisionService(fresh).publish(requests[0])
                fresh.commit()
            with pytest.raises(DBAPIError) as exc:
                PlanRevisionService(stale).publish(requests[1])
            assert exc.value.orig.sqlstate == "40001"
            stale.rollback()


def test_real_home_recipe_swap_replaces_only_future_intent_and_reservation(db):
    service, actor, g = fully_populated(db)
    old = service.current_plan(g.household_id, g.plan_id)
    old_inventory = InventoryService(db).snapshot(g.household_id)
    recipe2, _ = seed_recipe(db)
    d = g.model_dump()
    d["batches"] = list(d["batches"])
    d["allocations"] = list(d["allocations"])
    d["batches"][0]["status"] = "RETIRED"
    d["allocations"][0]["status"] = "RETIRED"
    batch = uuid4()
    tier = recipe2.portion_tiers[0]
    d["batches"].append(
        dict(
            node_id=batch,
            recipe_version_id=recipe2.id,
            tier_id=tier.id,
            planned_servings=tier.servings,
            planned_at=NOW + timedelta(minutes=1),
            status="PLANNED",
        )
    )
    d["allocations"].append(
        dict(
            node_id=uuid4(),
            batch_node_id=batch,
            meal_node_id=g.meals[0].node_id,
            servings="1",
            status="PLANNED",
        )
    )
    proposal, _ = propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="SINGLE_MEAL")
    result, _ = publish(db, service, actor, proposal)
    assert result.revision_no == 1 and result.parent_graph_hash == old.revision.proposal.graph_hash
    assert service.current_plan(g.household_id, g.plan_id).workspace.id == g.plan_id
    snap = InventoryService(db).snapshot(g.household_id)
    assert snap.movements == old_inventory.movements
    assert len(snap.reservations) == 2 and len(snap.releases) == 1
    assert service.store.revision(g.household_id, g.plan_id, 0) == old.revision
    handoff = service.horizon_handoff(g.household_id, g.plan_id, NOW + timedelta(days=6))
    assert not handoff.activation_ready and handoff.revision.revision_no == 1


def test_materialized_future_meal_pins_its_allocation_path(db):
    service, actor, g = fully_populated(db)
    inv = InventoryService(db)
    lot = inv.snapshot(g.household_id).lots[0]
    # Explicit confirmation can arrive before the scheduled meal; time is no proof.
    a = acquire(g.household_id, actor, lot.ingredient_id)
    inv.acquire(a)
    consumed = inv.consume(inventory_command(ConsumeInventoryCommand, a, amount="100"))
    service.store.link_materialization(
        household_id=g.household_id,
        plan_id=g.plan_id,
        source_revision_no=0,
        meal_node_id=g.meals[0].node_id,
        lot_id=a.lot_id,
        movement_id=consumed.id,
        actor_user_id=actor,
    )
    d = g.model_dump()
    d["allocations"][0]["servings"] = "0.5"
    with pytest.raises(IntegrityError, match="materialized"):
        propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="SINGLE_MEAL")
