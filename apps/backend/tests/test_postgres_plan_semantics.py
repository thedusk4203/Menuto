"""Real PostgreSQL scope/cut-line counterexamples; no production authorization issuer."""

from datetime import timedelta
from uuid import uuid4

import pytest
from alembic import command as alembic_command
from app.domain.units import Quantity
from app.modules.cooking.public import store_batch_intents
from app.modules.inventory.public import InventoryService
from app.modules.planning import contracts as c
from app.modules.planning.public import PlanStore
from app.modules.shopping import models as sm
from app.modules.shopping.public import store_shopping_intents
from plan_fixtures import NOW, graph_data, propose_command
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_foundation_migration import legacy_database as legacy_database
from test_foundation_migration import migrate
from test_postgres_foundation import db as db
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_foundation import seed_household
from test_postgres_plans import fully_populated, propose, publish, seed_recipe
from test_postgres_retail import insert_sql

pytestmark = pytest.mark.postgres


def sql_propose(service, actor, g, *, scope="REMAINING_HORIZON", effective_from=NOW):
    """Bypass aggregate/service validation deliberately; DB must reject independently."""
    store = service.store
    w = store.workspace(g.household_id, g.plan_id)
    request = c.ProposePlanCommand.model_construct(
        proposal_id=uuid4(),
        graph=g,
        actor_user_id=actor,
        source_system="manual",
        idempotency_key=str(uuid4()),
        reason="Direct SQL adversarial fixture",
        expected_generation=w.latest_proposal_no,
        expected_revision=w.active_revision_no,
        scope=scope,
        effective_from=effective_from,
    )
    with service.session.begin_nested():
        store.begin_proposal(request, "f" * 64)
        context = dict(
            proposal_id=request.proposal_id, household_id=g.household_id, plan_id=g.plan_id
        )
        store_batch_intents(
            service.session, **context, batches=g.batches, allocations=g.allocations
        )
        store.store_reservation_intents(request)
        store_shopping_intents(
            service.session,
            **context,
            requirements=g.shopping,
            contributions=g.shopping_contributions,
        )
        store.seal(request.proposal_id)
        return store.proposal(g.household_id, g.plan_id, request.proposal_id)


def attributed(db, *, batch_b=False, shared=False):
    service, actor, g = fully_populated(db)
    d = g.model_dump()
    if batch_b or shared:
        d["meals"][1]["meal_kind"] = "HOME"
        if batch_b:
            d["batches"] = list(d["batches"]) + [dict(d["batches"][0], node_id=uuid4())]
        batch = d["batches"][-1]["node_id"]
        d["allocations"] = list(d["allocations"]) + [
            dict(
                node_id=uuid4(),
                batch_node_id=batch,
                meal_node_id=g.meals[1].node_id,
                servings="1",
                status="PLANNED",
            )
        ]
    else:
        batch = None
    d["reservations"] = list(d["reservations"]) + [
        dict(
            node_id=uuid4(),
            lot_id=g.reservations[0].lot_id,
            batch_node_id=batch,
            meal_node_id=None if batch else g.meals[1].node_id,
            quantity=Quantity(amount="100", basis="EP_RAW_G"),
        )
    ]
    d["shopping_contributions"] = [
        dict(
            node_id=uuid4(),
            requirement_node_id=g.shopping[0].node_id,
            meal_node_id=m.node_id,
            quantity=Quantity(amount=amount, basis="EP_RAW_G"),
        )
        for m, amount in zip(g.meals, [600, 400], strict=True)
    ]
    g = c.PlanIntentGraph.model_validate(d)
    p, _ = propose(service, actor, g, scope="REMAINING_HORIZON")
    publish(db, service, actor, p)
    return service, actor, g


def change_a(g):
    d = g.model_dump()
    d["meals"][0]["scheduled_at"] += timedelta(hours=1)
    return d


@pytest.mark.parametrize("target", ["meal", "batch"])
@pytest.mark.parametrize("mutation", ["quantity", "remove", "retarget"])
def test_single_meal_cannot_mutate_unrelated_reservation_even_in_sql(db, target, mutation):
    service, actor, g = attributed(db, batch_b=target == "batch")
    original = InventoryService(db).snapshot(g.household_id)
    d = change_a(g)
    d["reservations"] = list(d["reservations"])
    if mutation == "quantity":
        d["reservations"][1]["quantity"]["amount"] = "101"
    if mutation == "remove":
        d["reservations"].pop()
    if mutation == "retarget":
        d["reservations"][1].update(batch_node_id=None, meal_node_id=g.meals[0].node_id)
    with pytest.raises(IntegrityError, match="scope"):
        sql_propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="SINGLE_MEAL")
    current = InventoryService(db).snapshot(g.household_id)
    assert current.movements == original.movements
    assert current.reservations == original.reservations and current.releases == original.releases
    assert current.positions == original.positions
    assert service.store.workspace(g.household_id, g.plan_id).active_revision_no == 1


@pytest.mark.parametrize(
    "mutation", ["unrelated_share", "transfer_shares", "need_by", "retire", "new_b_demand"]
)
def test_single_meal_cannot_change_unrelated_shopping_coverage(db, mutation):
    service, actor, g = attributed(db)
    d = change_a(g)
    if mutation == "unrelated_share":
        d["shopping_contributions"][1]["quantity"]["amount"] = "401"
        d["shopping"][0]["quantity"]["amount"] = "1001"
    if mutation == "transfer_shares":
        d["shopping_contributions"][0]["quantity"]["amount"] = "700"
        d["shopping_contributions"][1]["quantity"]["amount"] = "300"
    if mutation == "need_by":
        d["shopping"][0]["need_by"] += timedelta(hours=1)
    if mutation == "retire":
        d["shopping"][0]["status"] = "RETIRED"
        for v in d["shopping_contributions"]:
            v["status"] = "RETIRED"
    if mutation == "new_b_demand":
        new_id = uuid4()
        d["shopping"] = list(d["shopping"]) + [dict(d["shopping"][0], node_id=new_id)]
        d["shopping_contributions"] = list(d["shopping_contributions"]) + [
            dict(
                node_id=uuid4(),
                requirement_node_id=new_id,
                meal_node_id=g.meals[1].node_id,
                quantity=Quantity(amount=1000, basis="EP_RAW_G"),
            )
        ]
    with pytest.raises(IntegrityError, match="scope"):
        sql_propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="SINGLE_MEAL")


def test_single_meal_can_change_its_share_without_losing_b_coverage_or_reservation(db):
    service, actor, g = attributed(db)
    before = InventoryService(db).snapshot(g.household_id)
    links = service.store.reservation_links(g.household_id, g.plan_id, 1)
    b_reservation = next(
        v["reservation_id"] for v in links if v["intent_node_id"] == g.reservations[1].node_id
    )
    d = change_a(g)
    d["shopping"][0]["quantity"]["amount"] = "900"
    d["shopping_contributions"][0]["quantity"]["amount"] = "500"
    p, _ = propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="SINGLE_MEAL")
    result, _ = publish(db, service, actor, p)
    after = InventoryService(db).snapshot(g.household_id)
    assert after.movements == before.movements
    persisted_shares = {share.node_id: share for share in p.graph.shopping_contributions}
    assert persisted_shares[g.shopping_contributions[1].node_id] == g.shopping_contributions[1]
    assert b_reservation in {
        x["reservation_id"]
        for x in service.store.reservation_links(g.household_id, g.plan_id, result.revision_no)
    }
    assert b_reservation not in {x.reservation_id for x in after.releases}


@pytest.mark.parametrize(
    "mutation", ["quantity", "retire", "assign_ownership", "assign_ownership_unchanged"]
)
def test_unattributed_legacy_demand_cannot_be_claimed_by_single_meal(db, mutation):
    service, actor, g = fully_populated(db)
    d = change_a(g)
    if mutation == "retire":
        d["shopping"][0]["status"] = "RETIRED"
    else:
        amount = "1000" if mutation == "assign_ownership_unchanged" else "900"
        d["shopping"][0]["quantity"]["amount"] = amount
        if mutation.startswith("assign_ownership"):
            d["shopping_contributions"] = [
                dict(
                    node_id=uuid4(),
                    requirement_node_id=g.shopping[0].node_id,
                    meal_node_id=g.meals[0].node_id,
                    quantity=Quantity(amount=amount, basis="EP_RAW_G"),
                )
            ]
    with pytest.raises(IntegrityError, match="scope"):
        sql_propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="SINGLE_MEAL")


def test_shared_batch_reservation_is_not_local_to_one_meal(db):
    service, actor, g = attributed(db, shared=True)
    d = change_a(g)
    d["reservations"][1]["quantity"]["amount"] = "101"
    with pytest.raises(IntegrityError, match="scope"):
        sql_propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="SINGLE_MEAL")


def test_contribution_cannot_change_its_stable_parent_identity(db):
    service, actor, g = attributed(db)
    d = g.model_dump()
    new_id = uuid4()
    new_parent = dict(d["shopping"][0])
    new_parent.update(node_id=new_id, quantity=dict(amount="600", basis="EP_RAW_G"))
    d["shopping"] = list(d["shopping"]) + [new_parent]
    d["shopping"][0]["quantity"]["amount"] = "400"
    d["shopping_contributions"][0]["requirement_node_id"] = new_id
    with pytest.raises(IntegrityError, match="parent identity"):
        sql_propose(service, actor, c.PlanIntentGraph.model_validate(d))


def test_shared_batch_shopping_contribution_is_not_local_to_one_meal(db):
    service, actor, g = attributed(db, shared=True)
    d = g.model_dump()
    d["shopping_contributions"][0].update(meal_node_id=None, batch_node_id=g.batches[0].node_id)
    g = c.PlanIntentGraph.model_validate(d)
    p, _ = propose(service, actor, g)
    publish(db, service, actor, p)
    d = change_a(g)
    d["shopping_contributions"][0]["quantity"]["amount"] = "500"
    d["shopping"][0]["quantity"]["amount"] = "900"
    with pytest.raises(IntegrityError, match="scope"):
        sql_propose(service, actor, c.PlanIntentGraph.model_validate(d), scope="SINGLE_MEAL")


@pytest.mark.parametrize("scope", ["PROCUREMENT_ONLY", "REMAINING_HORIZON"])
def test_explicit_broad_scope_can_replace_b_reservation(db, scope):
    service, actor, g = attributed(db)
    d = g.model_dump()
    d["reservations"][1]["quantity"]["amount"] = "101"
    p, _ = propose(service, actor, c.PlanIntentGraph.model_validate(d), scope=scope)
    before = InventoryService(db).snapshot(g.household_id)
    publish(db, service, actor, p)
    after = InventoryService(db).snapshot(g.household_id)
    assert after.movements == before.movements
    assert after.positions[0].reserved.amount == 201


@pytest.mark.parametrize("family", ["batch", "shopping"])
def test_anchor_equal_to_cutline_is_revisable_future_intent(db, family):
    service, actor, g = fully_populated(db)
    d = g.model_dump()
    if family == "batch":
        d["batches"][0]["planned_at"] += timedelta(minutes=1)
    else:
        d["shopping"][0]["quantity"]["amount"] = "900"
    p, _ = propose(service, actor, c.PlanIntentGraph.model_validate(d), effective_from=NOW)
    result, _ = publish(db, service, actor, p)
    assert result.revision_no == 1


@pytest.mark.parametrize("family", ["batch", "shopping"])
@pytest.mark.parametrize("mutation", ["time", "quantity_or_source", "retire"])
def test_own_temporal_anchor_freezes_advice_even_with_future_meals(db, family, mutation):
    service, actor, g = fully_populated(db)
    d = g.model_dump()
    if family == "batch":
        if mutation == "time":
            d["batches"][0]["planned_at"] += timedelta(minutes=1)
        if mutation == "quantity_or_source":
            recipe, _ = seed_recipe(db)
            d["batches"][0].update(
                recipe_version_id=recipe.id,
                tier_id=recipe.portion_tiers[0].id,
                planned_servings=recipe.portion_tiers[0].servings,
            )
        if mutation == "retire":
            d["batches"][0]["status"] = "RETIRED"
            d["allocations"][0]["status"] = "RETIRED"
            d["meals"][0]["meal_kind"] = "OUTSIDE"
    else:
        if mutation == "time":
            d["shopping"][0]["need_by"] += timedelta(hours=2)
        if mutation == "quantity_or_source":
            d["shopping"][0]["quantity"]["amount"] = "900"
        if mutation == "retire":
            d["shopping"][0]["status"] = "RETIRED"
    with pytest.raises(IntegrityError, match="past advice"):
        sql_propose(
            service,
            actor,
            c.PlanIntentGraph.model_validate(d),
            effective_from=NOW + timedelta(hours=1),
        )


def test_freeze_of_past_shopping_also_blocks_reallocation_of_its_shares(db):
    service, actor, g = attributed(db)
    d = g.model_dump()
    d["shopping_contributions"][0]["quantity"]["amount"] = "700"
    d["shopping_contributions"][1]["quantity"]["amount"] = "300"
    with pytest.raises(IntegrityError, match="past advice"):
        sql_propose(
            service,
            actor,
            c.PlanIntentGraph.model_validate(d),
            effective_from=NOW + timedelta(hours=1),
        )


def test_new_backdated_requirement_is_not_new_future_advice(db):
    service, actor, g = fully_populated(db)
    d = g.model_dump()
    d["shopping"] = list(d["shopping"]) + [
        dict(d["shopping"][0], node_id=uuid4(), need_by=NOW - timedelta(hours=1))
    ]
    with pytest.raises(IntegrityError, match="past advice"):
        sql_propose(service, actor, c.PlanIntentGraph.model_validate(d))


@pytest.mark.parametrize(
    "mutation", ["sum", "basis", "target", "requirement", "retired_target", "missing_history"]
)
def test_sql_cannot_bypass_contribution_aggregate_checks(db, mutation):
    service, actor, g = attributed(db)
    shares = list(g.shopping_contributions)
    if mutation == "sum":
        shares[0] = shares[0].model_copy(
            update={"quantity": Quantity(amount=601, basis="EP_RAW_G")}
        )
    if mutation == "basis":
        shares[0] = shares[0].model_copy(update={"quantity": Quantity(amount=600, basis="AP_G")})
    if mutation == "target":
        shares[0] = shares[0].model_copy(update={"meal_node_id": uuid4()})
    if mutation == "requirement":
        shares[0] = shares[0].model_copy(update={"requirement_node_id": uuid4()})
    if mutation == "missing_history":
        shares = []
    data = {"shopping_contributions": tuple(shares)}
    if mutation == "retired_target":
        data["meals"] = (g.meals[0], g.meals[1].model_copy(update={"status": "RETIRED"}))
    with pytest.raises(IntegrityError):
        sql_propose(service, actor, g.model_copy(update=data))


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE", "late_insert"])
def test_contribution_rows_share_aggregate_immutability(db, operation):
    _, _, g = attributed(db)
    row = dict(db.execute(select(sm.ShoppingDemandContribution.__table__)).mappings().first())
    with pytest.raises(IntegrityError), db.begin_nested():
        if operation == "late_insert":
            row["node_id"] = uuid4()
            insert_sql(db, "shopping_demand_contributions", row)
        else:
            statement = {
                "UPDATE": "UPDATE shopping_demand_contributions SET amount=amount",
                "DELETE": "DELETE FROM shopping_demand_contributions",
                "TRUNCATE": "TRUNCATE shopping_demand_contributions",
            }[operation]
            db.execute(text(statement))


@pytest.mark.parametrize(
    "mutation",
    [
        "negative",
        "nonfinite",
        "precision",
        "zero",
        "household",
        "plan",
        "both_targets",
        "no_target",
    ],
)
def test_raw_sql_contribution_primitives_and_owner_cannot_be_bypassed(db, mutation):
    service, actor, g = attributed(db)
    store = service.store
    w = store.workspace(g.household_id, g.plan_id)
    request = propose_command(
        g, actor, expected_generation=w.latest_proposal_no, expected_revision=w.active_revision_no
    )
    row = dict(
        proposal_id=request.proposal_id,
        node_id=uuid4(),
        household_id=g.household_id,
        plan_id=g.plan_id,
        requirement_node_id=g.shopping[0].node_id,
        meal_node_id=g.meals[0].node_id,
        batch_node_id=None,
        amount="600",
        basis="EP_RAW_G",
        item_ref=None,
        status="PLANNED",
    )
    if mutation == "negative":
        row["amount"] = "-600"
    if mutation == "nonfinite":
        row["amount"] = "NaN"
    if mutation == "precision":
        row["amount"] = "600.0000001"
    if mutation == "zero":
        row["amount"] = "0"
    if mutation == "household":
        row["household_id"] = uuid4()
    if mutation == "plan":
        row["plan_id"] = uuid4()
    if mutation == "both_targets":
        row["batch_node_id"] = g.batches[0].node_id
    if mutation == "no_target":
        row["meal_node_id"] = None
    with pytest.raises(IntegrityError), db.begin_nested():
        store.begin_proposal(request, "a" * 64)
        store_shopping_intents(
            db,
            proposal_id=request.proposal_id,
            household_id=g.household_id,
            plan_id=g.plan_id,
            requirements=g.shopping,
        )
        insert_sql(db, "shopping_demand_contributions", row)


@pytest.mark.parametrize("populated", [False, True])
def test_0008_0009_roundtrip_preserves_legacy_hash_without_guessed_ownership(
    legacy_database, populated
):
    engine, config = legacy_database
    migrate(engine, config, "0008")
    if populated:
        with Session(engine) as db:
            user, house = seed_household(db)
            g = c.PlanIntentGraph.model_validate(
                graph_data(house.household_id, member=house.member_id)
                | {"contract_version": "plan-intent.v1"}
            )
            insert_sql(
                db,
                "plan_workspaces",
                dict(
                    id=g.plan_id,
                    household_id=g.household_id,
                    tracked_member_id=g.tracked_member_id,
                    created_by_user_id=user.id,
                    horizon_start=g.horizon.start,
                    horizon_end=g.horizon.end,
                ),
            )
            pid = uuid4()
            insert_sql(
                db,
                "plan_proposals",
                dict(
                    id=pid,
                    household_id=g.household_id,
                    plan_id=g.plan_id,
                    proposal_no=0,
                    expected_generation=-1,
                    scope="REMAINING_HORIZON",
                    effective_from=NOW,
                    actor_user_id=user.id,
                    source_system="legacy",
                    idempotency_key=str(uuid4()),
                    command_fingerprint="f" * 64,
                    reason="Original v1 source fact",
                ),
            )
            for meal in g.meals:
                insert_sql(
                    db,
                    "plan_meal_intents",
                    dict(
                        proposal_id=pid,
                        household_id=g.household_id,
                        plan_id=g.plan_id,
                        **meal.model_dump(exclude={"participants"}),
                    ),
                )
                for p in meal.participants:
                    insert_sql(
                        db,
                        "plan_meal_participants",
                        dict(
                            proposal_id=pid,
                            household_id=g.household_id,
                            plan_id=g.plan_id,
                            meal_node_id=meal.node_id,
                            **p.model_dump(),
                        ),
                    )
            insert_sql(db, "plan_proposal_seals", dict(proposal_id=pid))
            digest = db.scalar(
                text("SELECT graph_hash FROM plan_proposal_seals WHERE proposal_id=:p"), {"p": pid}
            )
            assert digest == g.fingerprint()
            db.commit()
    for _ in range(2):
        migrate(engine, config, "0009")
        with engine.connect() as conn:
            config.attributes["connection"] = conn
            alembic_command.check(config)
        if populated:
            with Session(engine) as db:
                saved = PlanStore(db).proposal(g.household_id, g.plan_id, pid)
                assert (
                    saved.graph_hash == digest and saved.graph.contract_version == "plan-intent.v1"
                )
                assert not saved.graph.shopping_contributions
        migrate(engine, config, "0008", down=True)
    migrate(engine, config, "head")
    with Session(engine) as db:
        from test_postgres_plans import setup

        service, actor, current = setup(db)
        p, _ = propose(service, actor, current)
        db.commit()
    with pytest.raises(IntegrityError, match="would lose intent"):
        migrate(engine, config, "0008", down=True)
    with Session(engine) as db:
        assert PlanStore(db).proposal(current.household_id, current.plan_id, p.id) == p
