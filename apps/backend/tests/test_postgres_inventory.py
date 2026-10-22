"""Real PostgreSQL ledger, SQL constraints, chronology, races and migration evidence."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command as alembic_command
from app.domain.units import Quantity
from app.modules.catalog.models import Ingredient
from app.modules.inventory import contracts as c
from app.modules.inventory import models as m
from app.modules.inventory.public import InventoryService
from inventory_fixtures import NOW, acquire, command, evidence
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from test_foundation_migration import legacy_database as legacy_database
from test_foundation_migration import migrate
from test_postgres_foundation import db as db
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_foundation import seed_household
from test_postgres_retail import insert_sql
from test_postgres_retail import seed as seed_retail

pytestmark = pytest.mark.postgres


def setup(db, **kw):
    user, house = seed_household(db)
    ingredient = Ingredient(name="Synthetic ingredient")
    db.add(ingredient)
    db.flush()
    a = acquire(house.household_id, user.id, ingredient.id, **kw)
    svc = InventoryService(db)
    first = svc.acquire(a)
    return svc, a, first


def position(svc, a, **kw):
    return next(p for p in svc.snapshot(a.household_id, **kw).positions if p.lot_id == a.lot_id)


def raw_fields(db, model, identity):
    result = dict(
        db.execute(text(f"SELECT * FROM {model.__tablename__} WHERE id=:id"), {"id": identity})
        .mappings()
        .one()
    )
    result.update(id=uuid4(), idempotency_key=str(uuid4()), external_record_id=str(uuid4()))
    return result


def reject(db, table, fields, match=None):
    with pytest.raises(IntegrityError, match=match), db.begin_nested():
        insert_sql(db, table, fields)


def test_acquire_idempotency_snapshot_and_source(db):
    svc, a, movement = setup(db)
    assert svc.acquire(a) == movement
    assert db.scalar(select(func.count()).select_from(m.InventoryLot)) == 1
    assert position(svc, a).remaining.amount == 500
    snapshot = svc.snapshot(a.household_id)
    assert c.PhysicalInventorySnapshot.model_validate_json(snapshot.model_dump_json()) == snapshot
    assert snapshot.movements[0].evidence == a.evidence
    assert snapshot.lots[0].acquired_at == a.occurred_at
    with pytest.raises(ValueError, match="Idempotency"):
        svc.acquire(
            c.AcquireInventoryCommand.model_validate(a.model_dump() | {"reason": "different"})
        )


def test_consume_idempotent_depletion_and_no_elapsed_consumption(db):
    svc, a, _ = setup(db)
    request = command(c.ConsumeInventoryCommand, a, amount="500")
    fact = svc.consume(request)
    assert svc.consume(request) == fact
    p = position(svc, a)
    assert p.remaining.amount == 0 and p.lifecycle_state == "DEPLETED"
    assert len(svc.snapshot(a.household_id).movements) == 2
    assert position(svc, a, as_of=NOW).remaining.amount == 500
    with pytest.raises(IntegrityError, match="insufficient"), db.begin_nested():
        svc.consume(command(c.ConsumeInventoryCommand, a, seconds=2))


def test_discard_partial_then_complete(db):
    svc, a, _ = setup(db)
    svc.discard(command(c.DiscardInventoryCommand, a, amount="100"))
    assert position(svc, a).remaining.amount == 400
    svc.discard(command(c.DiscardInventoryCommand, a, amount="400", seconds=2))
    assert position(svc, a).lifecycle_state == "DISCARDED"


def test_corrections_append_compensating_events(db):
    svc, a, opening = setup(db)
    svc.reconcile(
        command(
            c.ReconcileInventoryCommand,
            a,
            amount="50",
            direction="DECREASE",
            correction_of=opening.id,
        )
    )
    assert position(svc, a).remaining.amount == 450
    svc.reconcile(
        command(
            c.ReconcileInventoryCommand,
            a,
            amount="50",
            seconds=2,
            direction="INCREASE",
            correction_of=opening.id,
        )
    )
    assert position(svc, a).remaining.amount == 500
    assert len(svc.snapshot(a.household_id).movements) == 3
    assert db.get(m.InventoryMovement, opening.id).amount == 500


def test_reservation_release_not_physical_movement(db):
    svc, a, _ = setup(db)
    request = command(
        c.ReserveInventoryCommand, a, amount="300", reservation_id=uuid4(), purpose="Dinner"
    )
    r = svc.reserve(request)
    assert svc.reserve(request) == r
    assert position(svc, a).remaining.amount == 500
    assert position(svc, a).reserved.amount == 300
    with pytest.raises(IntegrityError, match="insufficient"), db.begin_nested():
        svc.consume(command(c.ConsumeInventoryCommand, a, amount="300", seconds=2))
    with pytest.raises(IntegrityError, match="insufficient"), db.begin_nested():
        svc.reserve(
            command(
                c.ReserveInventoryCommand,
                a,
                amount="201",
                seconds=2,
                reservation_id=uuid4(),
                purpose="Breakfast",
            )
        )
    release = command(c.ReleaseReservationCommand, a, seconds=2, reservation_id=r.id)
    assert svc.release(release) == svc.release(release)
    assert position(svc, a).reserved.amount == 0
    svc.consume(command(c.ConsumeInventoryCommand, a, amount="300", seconds=3))
    assert position(svc, a).remaining.amount == 200
    assert len(svc.snapshot(a.household_id).movements) == 2


def test_expiry_time_derived_without_mutation_and_explicit_transition(db):
    svc, a, _ = setup(db, usable_until=NOW + timedelta(hours=1))
    assert position(svc, a).lifecycle_state == "EXPIRED"
    assert position(svc, a).allocatable.amount == 0
    assert db.get(m.InventoryLotBalance, a.lot_id).lifecycle_state == "ACTIVE"
    assert position(svc, a, as_of=NOW).lifecycle_state == "ACTIVE"
    with pytest.raises(IntegrityError, match="expired"), db.begin_nested():
        svc.consume(command(c.ConsumeInventoryCommand, a, seconds=3600))
    with pytest.raises(IntegrityError, match="usable"), db.begin_nested():
        svc.reserve(
            command(
                c.ReserveInventoryCommand,
                a,
                seconds=3600,
                reservation_id=uuid4(),
                purpose="Late meal",
            )
        )
    svc.expire(command(c.ExpireInventoryCommand, a, seconds=3600))
    assert position(svc, a).remaining.amount == 500
    assert db.get(m.InventoryLotBalance, a.lot_id).lifecycle_state == "EXPIRED"
    svc.discard(command(c.DiscardInventoryCommand, a, amount="500", seconds=3601))
    assert position(svc, a).lifecycle_state == "DISCARDED"


@pytest.mark.parametrize(
    "asset,basis,item,definition",
    [
        ("RAW_INGREDIENT", "AP_G", None, None),
        ("RAW_INGREDIENT", "EP_RAW_G", None, None),
        ("RAW_INGREDIENT", "COUNT", "egg.large", None),
        ("PREPARED_COMPONENT", "COOKED_G", None, None),
        ("COOKED_DISH", "SERVING", "soup.v1", "One defined bowl"),
    ],
)
def test_raw_and_prepared_distinct_identity_no_conversion(db, asset, basis, item, definition):
    kwargs = dict(
        asset_type=asset,
        quantity=Quantity(amount=2, basis=basis, item_ref=item),
        serving_definition=definition,
    )
    if asset == "COOKED_DISH":
        kwargs["ingredient_id"] = None
    svc, a, _ = setup(db, **kwargs)
    assert svc.snapshot(a.household_id).lots[0].acquired_quantity.basis == basis
    with pytest.raises(IntegrityError, match="append-only"), db.begin_nested():
        db.execute(
            text("UPDATE inventory_lots SET asset_type='COOKED_DISH' WHERE id=:id"),
            {"id": a.lot_id},
        )


def test_retail_mapping_provenance_preserved_exactly(db):
    retail, _ = seed_retail(db)
    user, house = seed_household(db)
    a = acquire(
        house.household_id,
        user.id,
        retail["mapping"].ingredient_id,
        quantity=Quantity(amount="500", basis="AP_G"),
        retail_mapping_id=retail["mapping"].id,
    )
    svc = InventoryService(db)
    svc.acquire(a)
    lot = svc.snapshot(a.household_id).lots[0]
    assert lot.retail_mapping == retail["mapping"]
    assert lot.retail_mapping.apply(lot.acquired_quantity).mapping == retail["mapping"]
    fields = dict(
        db.execute(text("SELECT * FROM inventory_lots WHERE id=:id"), {"id": a.lot_id})
        .mappings()
        .one()
    )
    fields.update(id=uuid4(), ingredient_id=uuid4())
    reject(db, "inventory_lots", fields, "reviewed exact mapping")


@pytest.mark.parametrize("table", m.TABLES)
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE"])
def test_direct_sql_history_and_balance_protection(db, table, operation):
    svc, a, _ = setup(db)
    r = svc.reserve(command(c.ReserveInventoryCommand, a, reservation_id=uuid4(), purpose="Intent"))
    svc.release(command(c.ReleaseReservationCommand, a, seconds=2, reservation_id=r.id))
    if operation == "TRUNCATE":
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        sql = f"TRUNCATE {table} CASCADE"
    elif operation == "DELETE":
        sql = f"DELETE FROM {table}"
    else:
        column = "remaining" if table == "inventory_lot_balances" else "household_id"
        sql = f"UPDATE {table} SET {column}={column}"
    with pytest.raises(IntegrityError, match="append-only|ledger-controlled"), db.begin_nested():
        db.execute(text(sql))
    assert position(svc, a).remaining.amount == 500


@pytest.mark.parametrize(
    "mutation",
    [
        "negative",
        "nonfinite",
        "precision",
        "wrong_basis",
        "item_ref",
        "source",
        "inferred",
        "future",
        "backdate",
        "overconsume",
        "cross_household",
        "wrong_actor",
        "duplicate_source",
        "confirmation",
        "unknown_type",
        "missing_basis",
        "correction_cross_lot",
    ],
)
def test_direct_sql_critical_checks(db, mutation):
    svc, a, opening = setup(db)
    f = raw_fields(db, m.InventoryMovement, opening.id)
    f.update(movement_type="CONSUME", amount="100", occurred_at=NOW + timedelta(seconds=1))
    if mutation == "negative":
        f["amount"] = "-1"
    if mutation == "nonfinite":
        f["amount"] = "NaN"
    if mutation == "precision":
        f["amount"] = "0.0000001"
    if mutation == "wrong_basis":
        f["basis"] = "AP_G"
    if mutation == "item_ref":
        f["item_ref"] = "egg.large"
    if mutation == "source":
        f["source_kind"] = "RETAIL_OBSERVATION"
    if mutation == "inferred":
        f["source_kind"] = "SYSTEM"
    if mutation == "future":
        f["occurred_at"] = NOW + timedelta(days=100)
    if mutation == "backdate":
        f["occurred_at"] = NOW - timedelta(seconds=1)
    if mutation == "overconsume":
        f["amount"] = "501"
    if mutation == "cross_household":
        f["household_id"] = uuid4()
    if mutation == "wrong_actor":
        f["confirmed_by_user_id"] = uuid4()
    if mutation == "duplicate_source":
        f["external_record_id"] = opening.evidence.external_record_id
    if mutation == "confirmation":
        f["confirmation"] = "ASSUMED"
    if mutation == "unknown_type":
        f["movement_type"] = "PLANNED_ACQUISITION"
    if mutation == "missing_basis":
        f["basis"] = None
    if mutation == "correction_cross_lot":
        _, _, other = setup(db)
        f.update(movement_type="RECONCILE_DECREASE", correction_of=other.id)
    with pytest.raises(DBAPIError), db.begin_nested():
        insert_sql(db, "inventory_movements", f)
    assert position(svc, a).remaining.amount == 500


def test_direct_sql_orphan_lot_cannot_commit(db):
    svc, a, _ = setup(db)
    f = dict(
        db.execute(text("SELECT * FROM inventory_lots WHERE id=:id"), {"id": a.lot_id})
        .mappings()
        .one()
    )
    f["id"] = uuid4()
    with pytest.raises(IntegrityError, match="opening acquisition"), db.begin_nested():
        insert_sql(db, "inventory_lots", f)
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))


def test_direct_sql_cannot_seed_balance(db):
    _, a, _ = setup(db)
    with pytest.raises(IntegrityError, match="ledger-controlled"), db.begin_nested():
        db.execute(text("INSERT INTO inventory_lot_balances SELECT * FROM inventory_lot_balances"))


def test_same_time_canonical_order_and_db_sequence_overrides(db):
    svc, a, opening = setup(db)
    f = raw_fields(db, m.InventoryMovement, opening.id)
    f.update(movement_type="CONSUME", amount=100, ledger_sequence=1, phase=60)
    insert_sql(db, "inventory_movements", f)
    consume = db.get(m.InventoryMovement, f["id"])
    assert consume.phase == 30 and consume.ledger_sequence > opening.ledger_sequence
    f = raw_fields(db, m.InventoryMovement, opening.id)
    f.update(movement_type="RECONCILE_INCREASE", amount=100)
    reject(db, "inventory_movements", f, "nonchronological")
    assert position(svc, a).remaining.amount == 400


def test_sql_external_record_different_providers_no_collision(db):
    svc, a, opening = setup(db)
    for i, provider in enumerate(["provider.a", "provider.b"]):
        svc.reconcile(
            command(
                c.ReconcileInventoryCommand,
                a,
                amount="1",
                seconds=i + 1,
                direction="INCREASE",
                evidence=evidence(
                    a.evidence.confirmed_by_user_id,
                    source_system=provider,
                    external_record_id="same.external.record",
                ),
            )
        )
    assert position(svc, a).remaining.amount == 502


@pytest.mark.parametrize("operation", ["consume", "reserve", "acquire_retry"])
def test_concurrent_commands_cannot_double_allocate(postgres_engine, operation):
    with Session(postgres_engine) as session:
        _, a, _ = setup(session)
        session.commit()
    barrier = Barrier(2)

    def worker(i):
        with Session(postgres_engine) as session:
            barrier.wait(timeout=10)
            svc = InventoryService(session)
            try:
                if operation == "acquire_retry":
                    svc.acquire(a)
                elif operation == "consume":
                    svc.consume(command(c.ConsumeInventoryCommand, a, amount="300"))
                else:
                    svc.reserve(
                        command(
                            c.ReserveInventoryCommand,
                            a,
                            amount="300",
                            reservation_id=uuid4(),
                            purpose="Intent",
                        )
                    )
                session.commit()
                return "ok"
            except DBAPIError as error:
                session.rollback()
                return error.orig.sqlstate

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, range(2)))
    with Session(postgres_engine) as session:
        p = position(InventoryService(session), a)
        if operation == "acquire_retry":
            assert results == ["ok", "ok"] and p.remaining.amount == 500
        else:
            assert sorted(results) == ["23514", "ok"]
            assert p.remaining.amount == (200 if operation == "consume" else 500)
            assert p.reserved.amount == (300 if operation == "reserve" else 0)


def test_repeatable_read_stale_writer_serializes(postgres_engine):
    with Session(postgres_engine) as session:
        _, a, _ = setup(session)
        session.commit()
    with postgres_engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
        with Session(conn) as stale:
            stale.scalar(
                select(m.InventoryLotBalance).where(m.InventoryLotBalance.lot_id == a.lot_id)
            )
            with Session(postgres_engine) as fresh:
                InventoryService(fresh).consume(command(c.ConsumeInventoryCommand, a, amount="300"))
                fresh.commit()
            with pytest.raises(DBAPIError) as exc:
                InventoryService(stale).consume(command(c.ConsumeInventoryCommand, a, amount="300"))
            assert exc.value.orig.sqlstate == "40001"
            stale.rollback()
    with Session(postgres_engine) as session:
        assert position(InventoryService(session), a).remaining.amount == 200


@pytest.mark.parametrize("foundation_data", [False, True])
def test_0006_0007_lossless_roundtrip_and_drift(legacy_database, foundation_data):
    engine, config = legacy_database
    migrate(engine, config, "0006")
    user = None
    if foundation_data:
        with Session(engine) as session:
            user, house = seed_household(session)
            identity = user.id
            session.commit()
    for _ in range(2):
        migrate(engine, config, "0007")
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            alembic_command.check(config)
        migrate(engine, config, "0006", down=True)
        if foundation_data:
            with engine.connect() as connection:
                assert (
                    connection.scalar(
                        text("SELECT count(*) FROM users WHERE id=:id"), {"id": identity}
                    )
                    == 1
                )
    migrate(engine, config, "0007")
    with Session(engine) as session:
        svc, a, _ = setup(session)
        session.commit()
        before = svc.snapshot(a.household_id)
        session.rollback()
    with pytest.raises(IntegrityError, match="0007 downgrade would lose physical history"):
        migrate(engine, config, "0006", down=True)
    with Session(engine) as session:
        assert session.scalar(text("SELECT version_num FROM alembic_version")) == "0007"
        after = InventoryService(session).snapshot(a.household_id)
        assert after.model_dump(exclude={"as_of"}) == before.model_dump(exclude={"as_of"})
