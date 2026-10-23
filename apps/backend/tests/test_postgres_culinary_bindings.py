"""Real relational/seal/revision tests; authorization setup is test-owner-only."""

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from alembic import command as alembic_command
from app.modules.execution.culinary_capture import capture_culinary_input
from app.modules.inventory.public import InventoryService
from app.modules.planning import contracts as c
from app.modules.validation.recipe_grounding import validate_recipe_grounding
from culinary_fixtures import culinary_source
from plan_fixtures import NOW
from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_foundation_migration import legacy_database as legacy_database
from test_foundation_migration import migrate
from test_postgres_foundation import db as db
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_plans import propose, publish, setup
from test_postgres_recipes import seed

pytestmark = pytest.mark.postgres


def bound(db, *, selected=False):
    service, actor, old = setup(db)
    recipe, _ = seed(db)
    s = culinary_source(recipe, selected=(recipe.variant_rules[0].id,) if selected else ())
    d = s.proposal.graph.model_dump()
    d.update(
        household_id=old.household_id,
        plan_id=old.plan_id,
        tracked_member_id=old.tracked_member_id,
        horizon=old.horizon,
    )
    for meal in d["meals"]:
        meal["participants"] = [
            dict(member_id=old.tracked_member_id, portion_factor=1, nutrition_role="TRACKED")
        ]
    b = s.proposal.graph.culinary_bindings[0].model_copy(
        update={"household_id": old.household_id, "plan_id": old.plan_id}
    )
    b = b.model_copy(update={"fingerprint": b.expected_fingerprint()})
    d["culinary_bindings"] = (b,)
    d["batches"][0]["culinary_signature"] = b.semantic_fingerprint()
    return service, actor, c.BoundPlanIntentGraph.model_validate(d), recipe


def request(service, actor, g, **kw):
    w = service.store.workspace(g.household_id, g.plan_id)
    return c.ProposeBoundPlanCommand(
        **(
            dict(
                proposal_id=g.culinary_bindings[0].proposal_id,
                graph=g,
                expected_generation=w.latest_proposal_no,
                expected_revision=w.active_revision_no,
                scope="REMAINING_HORIZON",
                effective_from=NOW,
                actor_user_id=actor,
                source_system="manual",
                idempotency_key=str(uuid4()),
                reason="Explicit culinary intent",
            )
            | kw
        )
    )


def revise(g, *, delta=0):
    b = g.culinary_bindings[0]
    rows = list(b.requirements)
    row = rows[0]
    rows[0] = row.model_copy(
        update={
            "adjustment_delta": Decimal(delta),
            "quantity": row.quantity.model_copy(update={"amount": Decimal(200 + delta)}),
        }
    )
    b = b.model_copy(update={"proposal_id": uuid4(), "requirements": tuple(rows)})
    b = b.model_copy(update={"fingerprint": b.expected_fingerprint()})
    d = g.model_dump() | {"culinary_bindings": (b,)}
    d["batches"][0]["culinary_signature"] = b.semantic_fingerprint()
    return c.BoundPlanIntentGraph.model_validate(d)


@pytest.mark.parametrize("selected", [False, True])
def test_authoritative_binding_roundtrip_and_no_physical_changes(db, selected):
    service, actor, g, r = bound(db, selected=selected)
    before = InventoryService(db).snapshot(g.household_id)
    cmd = request(service, actor, g)
    p = service.propose(cmd)
    assert p.graph.content() == g.content() and p.graph_hash == g.fingerprint()
    assert service.propose(cmd) == p
    assert service.store.proposal(g.household_id, g.plan_id, p.id) == p
    after = InventoryService(db).snapshot(g.household_id)
    assert (
        before.lots,
        before.movements,
        before.positions,
        before.reservations,
        before.releases,
    ) == (after.lots, after.movements, after.positions, after.reservations, after.releases)
    assert (
        db.scalar(
            text("SELECT count(*) FROM planned_culinary_bindings WHERE proposal_id=:p"), {"p": p.id}
        )
        == 1
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_rule",
        "wrong_requirement",
        "wrong_ingredient",
        "wrong_basis",
        "wrong_item_ref",
        "below_min",
        "above_max",
        "amount",
        "wrong_transform",
        "missing_transform",
        "fingerprint",
        "wrong_household",
        "wrong_plan",
        "wrong_proposal",
        "wrong_batch",
        "wrong_version",
        "wrong_tier",
        "servings",
        "missing_requirement",
        "count_substitution",
    ],
)
def test_sql_cannot_seal_invalid_binding(db, mutation, monkeypatch):
    service, actor, g, r = bound(db)
    original = service.store.store_bindings

    def corrupt(graph):
        original(graph)
        params = {"p": g.culinary_bindings[0].proposal_id, "i": r.ingredients[0].id, "bad": uuid4()}
        assignments = {
            "unknown_rule": "selected_rule_id=:bad",
            "wrong_requirement": "requirement_id=:bad",
            "wrong_ingredient": "ingredient_id=:bad",
            "wrong_basis": "basis='COOKED_G'",
            "wrong_item_ref": "item_ref='wrong.ref'",
            "below_min": "adjustment_delta=-21",
            "above_max": "adjustment_delta=61",
            "amount": "amount=201",
            "wrong_transform": "transformation_id=:bad",
            "missing_transform": "transformation_id=NULL",
        }
        # Test database owner disables UPDATE immutability solely to inject malformed
        # unsealed assembly; seal/FKs/checks must still reject it independently.
        if mutation in assignments:
            db.execute(
                text("ALTER TABLE culinary_requirement_bindings DISABLE TRIGGER culinary_immutable")
            )
            db.execute(
                text(
                    f"UPDATE culinary_requirement_bindings SET {assignments[mutation]} "
                    "WHERE proposal_id=:p AND requirement_id=:i"
                ),
                params,
            )
            db.execute(
                text("ALTER TABLE culinary_requirement_bindings ENABLE TRIGGER culinary_immutable")
            )
        elif mutation == "missing_requirement":
            db.execute(
                text("ALTER TABLE culinary_requirement_bindings DISABLE TRIGGER culinary_immutable")
            )
            db.execute(
                text(
                    "DELETE FROM culinary_requirement_bindings WHERE proposal_id=:p "
                    "AND requirement_id=:i"
                ),
                params,
            )
            db.execute(
                text("ALTER TABLE culinary_requirement_bindings ENABLE TRIGGER culinary_immutable")
            )
        elif mutation == "count_substitution":
            db.execute(
                text("ALTER TABLE culinary_requirement_bindings DISABLE TRIGGER culinary_immutable")
            )
            db.execute(
                text(
                    "UPDATE culinary_requirement_bindings SET selected_rule_id=:rule "
                    "WHERE proposal_id=:p AND requirement_id=:count"
                ),
                params | {"rule": r.variant_rules[0].id, "count": r.ingredients[3].id},
            )
        else:
            assignments = {
                "fingerprint": "fingerprint=repeat('f',64)",
                "wrong_household": "household_id=:bad",
                "wrong_plan": "plan_id=:bad",
                "wrong_proposal": "proposal_id=:bad",
                "wrong_batch": "batch_node_id=:bad",
                "wrong_version": "recipe_version_id=:bad",
                "wrong_tier": "tier_id=:bad",
                "servings": "planned_servings=3",
            }
            db.execute(
                text("ALTER TABLE planned_culinary_bindings DISABLE TRIGGER culinary_immutable")
            )
            db.execute(
                text(
                    f"UPDATE planned_culinary_bindings SET {assignments[mutation]} "
                    "WHERE proposal_id=:p"
                ),
                params,
            )
            db.execute(
                text("ALTER TABLE planned_culinary_bindings ENABLE TRIGGER culinary_immutable")
            )

    monkeypatch.setattr(service.store, "store_bindings", corrupt)
    with pytest.raises(IntegrityError):
        service.propose(request(service, actor, g))


@pytest.mark.parametrize("table", ["planned_culinary_bindings", "culinary_requirement_bindings"])
@pytest.mark.parametrize("action", ["UPDATE", "DELETE", "TRUNCATE", "INSERT"])
def test_direct_sql_sealed_immutability(db, table, action):
    service, actor, g, r = bound(db)
    p = service.propose(request(service, actor, g))
    sql = {
        "UPDATE": f"UPDATE {table} SET proposal_id=proposal_id WHERE proposal_id=:p",
        "DELETE": f"DELETE FROM {table} WHERE proposal_id=:p",
        "TRUNCATE": f"TRUNCATE {table} CASCADE",
        "INSERT": f"INSERT INTO {table} SELECT * FROM {table} WHERE proposal_id=:p",
    }[action]
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(text(sql), {"p": p.id})


def test_old_revision_retains_binding_new_revision_is_new_owned_fact(db):
    service, actor, g, r = bound(db)
    p = service.propose(request(service, actor, g))
    rev, _ = publish(db, service, actor, p)
    nextg = revise(g, delta=10)
    p2 = service.propose(request(service, actor, nextg, scope="SINGLE_MEAL"))
    rev2, _ = publish(db, service, actor, p2)
    assert p.graph_hash != p2.graph_hash and rev2.revision_no == 1
    assert service.store.revision(g.household_id, g.plan_id, 0) == rev
    assert (
        next(
            x
            for x in rev.proposal.graph.culinary_bindings[0].requirements
            if x.requirement_id == r.ingredients[0].id
        ).quantity.amount
        == 200
    )
    assert (
        next(
            x
            for x in rev2.proposal.graph.culinary_bindings[0].requirements
            if x.requirement_id == r.ingredients[0].id
        ).quantity.amount
        == 210
    )
    assert service.current_plan(g.household_id, g.plan_id).revision == rev2


def test_binding_change_of_shared_batch_requires_multi_meal_closure(db):
    service, actor, g, r = bound(db)
    d = g.model_dump()
    d["meals"][1]["meal_kind"] = "HOME"
    d["allocations"][0]["servings"] = 1
    d["allocations"] = list(d["allocations"]) + [
        dict(d["allocations"][0], node_id=uuid4(), meal_node_id=g.meals[1].node_id)
    ]
    g = c.BoundPlanIntentGraph.model_validate(d)
    p = service.propose(request(service, actor, g))
    publish(db, service, actor, p)
    with pytest.raises(IntegrityError, match="scope"):
        service.propose(request(service, actor, revise(g, delta=10), scope="SINGLE_MEAL"))
    assert service.propose(request(service, actor, revise(g, delta=10), scope="MULTI_MEAL"))


def test_historical_binding_cannot_be_rewritten_through_binding_only_delta(db):
    service, actor, g, r = bound(db)
    p = service.propose(request(service, actor, g))
    publish(db, service, actor, p)
    with pytest.raises(IntegrityError, match="past advice"):
        service.propose(
            request(service, actor, revise(g, delta=10), effective_from=NOW + timedelta(hours=2))
        )


def test_materialization_pin_covers_binding_only_change(db):
    from app.domain.units import Quantity
    from inventory_fixtures import acquire

    service, actor, g, r = bound(db)
    p = service.propose(request(service, actor, g))
    publish(db, service, actor, p)
    command = acquire(
        g.household_id,
        actor,
        r.ingredients[0].ingredient_id,
        asset_type="PREPARED_COMPONENT",
        quantity=Quantity(amount=100, basis="COOKED_G"),
    )
    InventoryService(db).acquire(command)
    movement = db.scalar(
        text("SELECT id FROM inventory_movements WHERE lot_id=:l"), {"l": command.lot_id}
    )
    service.store.link_materialization(
        household_id=g.household_id,
        plan_id=g.plan_id,
        source_revision_no=0,
        lot_id=command.lot_id,
        movement_id=movement,
        actor_user_id=actor,
        batch_node_id=g.batches[0].node_id,
    )
    with pytest.raises(IntegrityError, match="materialized"):
        service.propose(request(service, actor, revise(g, delta=10)))
    assert service.propose(request(service, actor, revise(g)))


def test_capture_then_validator_has_zero_queries_or_writes(postgres_engine):
    with Session(postgres_engine) as db:
        service, actor, g, r = bound(db)
        p = service.propose(request(service, actor, g))
        db.commit()
    with postgres_engine.connect().execution_options(
        isolation_level="REPEATABLE READ", postgresql_readonly=True
    ) as conn:
        with Session(conn) as db:
            captured = capture_culinary_input(
                db, household_id=g.household_id, plan_id=g.plan_id, proposal_id=p.id
            )

    def forbidden(*args):
        raise AssertionError("DB access during independent validation")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        assert validate_recipe_grounding(captured).culinary_checks_passed
        assert not validate_recipe_grounding(captured).activation_authorized
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)


@pytest.mark.parametrize("populated", [False, True])
def test_0009_0010_legacy_roundtrip_and_hashes(legacy_database, populated):
    engine, config = legacy_database
    migrate(engine, config, "0009")
    saved = []
    if populated:
        with Session(engine) as db:
            service, actor, g = setup(db)
            for version in ["plan-intent.v1", "plan-intent.v2"]:
                g = c.PlanIntentGraph.model_validate(g.model_dump() | {"contract_version": version})
                p, _ = propose(service, actor, g)
                saved.append((g, p))
            db.commit()
    for _ in range(2):
        migrate(engine, config, "0010")
        with engine.connect() as conn:
            assert len(inspect(conn).get_table_names()) == 55
        if populated:
            with Session(engine) as db:
                from app.modules.planning.public import PlanStore

                for g, p in saved:
                    assert PlanStore(db).proposal(g.household_id, g.plan_id, p.id) == p
        migrate(engine, config, "0009", down=True)
    migrate(engine, config, "0010")
    # Keep exact0009↔0010/hash coverage above; current ORM drift belongs at current head.
    migrate(engine, config, "head")
    with engine.connect() as conn:
        config.attributes["connection"] = conn
        alembic_command.check(config)
    migrate(engine, config, "0010", down=True)


def test_populated_culinary_downgrade_fails_closed(legacy_database):
    engine, config = legacy_database
    migrate(engine, config, "head")
    with Session(engine) as db:
        service, actor, g, r = bound(db)
        service.propose(request(service, actor, g))
        db.commit()
    with pytest.raises(IntegrityError, match="culinary binding history"):
        migrate(engine, config, "0009", down=True)


@pytest.mark.parametrize("approved", [True, False])
def test_db_exact_structural_combination(db, approved):
    from recipe_fixtures import provenance, recipe_data

    data = recipe_data()
    other = dict(
        data["variant_rules"][0],
        id=uuid4(),
        key="second.slot",
        requirement_id=data["ingredients"][1]["id"],
        replacement_ingredient_id=uuid4(),
    )
    other["provenance"] = provenance()
    data["variant_rules"] = [data["variant_rules"][0], other]
    ids = tuple(row["id"] for row in data["variant_rules"])
    data["approved_combinations"] = [
        dict(
            id=uuid4(),
            recipe_version_id=data["id"],
            key="combo",
            rule_ids=ids,
            provenance=provenance(),
        )
    ]
    recipe, _ = seed(db, data)
    service, actor, old = setup(db)
    s = culinary_source(recipe, selected=ids)
    b = s.proposal.graph.culinary_bindings[0].model_copy(
        update={"household_id": old.household_id, "plan_id": old.plan_id}
    )
    if not approved:
        b = b.model_copy(update={"approved_combination_id": None})
    b = b.model_copy(update={"fingerprint": b.expected_fingerprint()})
    d = s.proposal.graph.model_dump() | {
        "household_id": old.household_id,
        "plan_id": old.plan_id,
        "tracked_member_id": old.tracked_member_id,
        "horizon": old.horizon,
        "culinary_bindings": (b,),
    }
    for meal in d["meals"]:
        meal["participants"] = [
            dict(member_id=old.tracked_member_id, portion_factor=1, nutrition_role="TRACKED")
        ]
    d["batches"][0]["culinary_signature"] = b.semantic_fingerprint()
    g = c.BoundPlanIntentGraph.model_validate(d)
    if approved:
        assert service.propose(request(service, actor, g))
    else:
        with pytest.raises(IntegrityError, match="combination"):
            service.propose(request(service, actor, g))


def test_bound_retry_and_stale_revision_are_deterministic(db):
    service, actor, g, r = bound(db)
    cmd = request(service, actor, g)
    p = service.propose(cmd)
    assert service.propose(cmd) == p
    with pytest.raises(ValueError, match="Idempotency"):
        service.propose(cmd.model_copy(update={"reason": "Different request"}))
    publish(db, service, actor, p)
    stale = request(service, actor, revise(g, delta=20))
    p2 = service.propose(request(service, actor, revise(g, delta=10)))
    publish(db, service, actor, p2)
    with pytest.raises(IntegrityError, match="STALE_"):
        service.propose(stale)


def test_bound_plan_cannot_silently_downgrade_to_unbound_legacy(db):
    service, actor, g, r = bound(db)
    p = service.propose(request(service, actor, g))
    publish(db, service, actor, p)
    d = g.model_dump(exclude={"culinary_bindings"}) | {"contract_version": "plan-intent.v2"}
    for batch in d["batches"]:
        batch.pop("culinary_signature")
    with pytest.raises(IntegrityError, match="legacy downgrade"):
        propose(service, actor, c.PlanIntentGraph.model_validate(d))


def test_concurrent_bound_proposals_do_not_lose_generation_updates(postgres_engine):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from app.modules.execution.public import PlanRevisionService

    with Session(postgres_engine) as db:
        service, actor, g, r = bound(db)
        db.commit()
    barrier = Barrier(2)

    def writer(delta):
        with Session(postgres_engine) as db:
            service = PlanRevisionService(db)
            cmd = request(service, actor, revise(g, delta=delta))
            barrier.wait(timeout=10)
            try:
                p = service.propose(cmd)
                db.commit()
                return p.id
            except IntegrityError as error:
                db.rollback()
                assert "STALE_PLAN_GENERATION_OR_REVISION" in str(error)
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(writer, [10, 20]))
    assert sum(value is not None for value in results) == 1
