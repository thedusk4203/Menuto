"""INV-011/012/013/018/019: explicit identity, evidence and primitive replay."""

from datetime import timedelta
from uuid import uuid4

import pytest
from app.domain.units import Quantity
from app.modules.inventory import contracts as c
from inventory_fixtures import NOW, acquire, command, evidence
from pydantic import ValidationError
from test_architecture import check_source


@pytest.mark.parametrize(
    "basis,item,asset,ingredient,definition",
    [
        ("AP_G", None, "RAW_INGREDIENT", True, None),
        ("EP_RAW_G", None, "RAW_INGREDIENT", True, None),
        ("COUNT", "egg.large", "RAW_INGREDIENT", True, None),
        ("COOKED_G", None, "PREPARED_COMPONENT", True, None),
        ("SERVING", "dish.serving.v1", "COOKED_DISH", False, "One authored bowl"),
    ],
)
def test_physical_asset_identity(basis, item, asset, ingredient, definition):
    a = acquire(
        asset_type=asset,
        ingredient_id=uuid4() if ingredient else None,
        quantity=Quantity(amount=2, basis=basis, item_ref=item),
        serving_definition=definition,
    )
    assert c.AcquireInventoryCommand.model_validate_json(a.model_dump_json()) == a
    with pytest.raises(ValidationError):
        a.reason = "changed"


@pytest.mark.parametrize(
    "overrides",
    [
        {"quantity": {"amount": 1}},
        {"quantity": {"amount": 1, "basis": "COUNT"}},
        {"quantity": {"amount": 1, "basis": "SERVING", "item_ref": "x"}},
        {"quantity": {"amount": 1, "basis": "COOKED_G"}},
        {"quantity": {"amount": 0, "basis": "EP_RAW_G"}},
        {"ingredient_id": None},
        {"is_planned": True},
        {"state": "PROJECTED"},
        {"plan_id": str(uuid4())},
        {"retail_mapping_id": uuid4()},
        {"usable_until": NOW},
    ],
)
def test_invalid_or_planned_acquisition(overrides):
    with pytest.raises(ValueError):
        c.AcquireInventoryCommand.model_validate(acquire().model_dump() | overrides)


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-Infinity", "-1", 1.5, "0.0000001"])
def test_no_nonfinite_negative_float_or_silent_rounding(amount):
    with pytest.raises(ValueError):
        acquire(quantity={"amount": amount, "basis": "EP_RAW_G"})


@pytest.mark.parametrize("kind", ["SYSTEM", "AUTOPILOT_ASSUMED", "RETAIL_OBSERVATION", "PLANNED"])
def test_inference_and_retail_not_confirmation(kind):
    with pytest.raises(ValueError):
        evidence(kind=kind)


@pytest.mark.parametrize(
    "target",
    [
        "planning.optimizer",
        "execution.contracts",
        "validation.implementation",
        "learning.contracts",
        "assistant.contracts",
        "recipes.contracts",
        "retail.models",
    ],
)
def test_inventory_core_import_boundaries(target):
    assert check_source(f"import app.modules.{target}", "app.modules.inventory.public")


def test_domain_has_no_yield_persistence_or_lifecycle_projection():
    from app.persistence.models import Base

    assert set(c.Lifecycle) == {"ACTIVE", "DEPLETED", "EXPIRED", "DISCARDED"}
    assert not any("conversion" in n or "yield" in n for n in Base.metadata.tables)
    assert "recipe_version_id" not in Base.metadata.tables["inventory_lots"].columns
    assert "plan_id" not in Base.metadata.tables["inventory_lots"].columns


def snapshot():
    a = acquire()
    q = a.quantity
    lot = c.InventoryLot(
        id=a.lot_id,
        household_id=a.household_id,
        ingredient_id=a.ingredient_id,
        asset_type=a.asset_type,
        acquired_quantity=q,
        acquired_at=NOW,
        created_at=NOW,
        usable_until=NOW + timedelta(days=1),
        observation_confidence="CONFIRMED",
        serving_definition=None,
    )

    def movement(kind, amount, sequence, seconds):
        return c.InventoryMovement(
            id=uuid4(),
            household_id=a.household_id,
            lot_id=a.lot_id,
            movement_type=kind,
            quantity=Quantity(amount=amount, basis=q.basis),
            occurred_at=NOW + timedelta(seconds=seconds),
            recorded_at=NOW + timedelta(hours=1),
            ledger_sequence=sequence,
            phase=c.event_phase(a.asset_type, kind),
            idempotency_key=str(uuid4()),
            command_fingerprint="a" * 64,
            evidence=a.evidence,
            reason="test",
        )

    return c.PhysicalInventorySnapshot(
        household_id=a.household_id,
        as_of=NOW + timedelta(hours=2),
        lots=(lot,),
        movements=(movement("ACQUIRE", 500, 1, 0), movement("CONSUME", 100, 2, 1)),
        reservations=(),
        releases=(),
        positions=(
            c.InventoryPosition(
                lot_id=a.lot_id,
                remaining=Quantity(amount=400, basis=q.basis),
                reserved=Quantity(amount=0, basis=q.basis),
                lifecycle_state="ACTIVE",
            ),
        ),
    )


def test_snapshot_replay_roundtrip_and_immutable():
    s = snapshot()
    assert c.PhysicalInventorySnapshot.model_validate_json(s.model_dump_json()) == s
    assert not s.activation_ready
    with pytest.raises(ValidationError):
        s.activation_ready = True


@pytest.mark.parametrize(
    "mutation",
    [
        "overconsume",
        "missing_opening",
        "wrong_basis",
        "wrong_household",
        "wrong_phase",
        "duplicate_sequence",
        "future",
        "summary_lie",
        "expired_consume",
        "cross_lot_correction",
    ],
)
def test_primitive_replay_rejects_corruption(mutation):
    data = snapshot().model_dump(mode="json")
    e = data["movements"][1]
    if mutation == "overconsume":
        e["quantity"]["amount"] = "600"
    if mutation == "missing_opening":
        data["movements"] = data["movements"][1:]
    if mutation == "wrong_basis":
        e["quantity"]["basis"] = "AP_G"
    if mutation == "wrong_household":
        e["household_id"] = str(uuid4())
    if mutation == "wrong_phase":
        e["phase"] = 60
    if mutation == "duplicate_sequence":
        e["ledger_sequence"] = 1
    if mutation == "future":
        e["occurred_at"] = (NOW + timedelta(days=10)).isoformat()
    if mutation == "summary_lie":
        data["positions"][0]["remaining"]["amount"] = "999"
    if mutation == "expired_consume":
        data["lots"][0]["usable_until"] = (NOW + timedelta(microseconds=1)).isoformat()
    if mutation == "cross_lot_correction":
        e["movement_type"] = "RECONCILE_DECREASE"
        e["phase"] = 20
        e["correction_of"] = str(uuid4())
    with pytest.raises(ValueError):
        c.PhysicalInventorySnapshot.model_validate(data)


def test_reservation_command_not_physical_movement():
    a = acquire()
    r = command(c.ReserveInventoryCommand, a, reservation_id=uuid4(), purpose="Dinner")
    assert not isinstance(r, c.ConsumeInventoryCommand)
    with pytest.raises(ValueError):
        c.ReserveInventoryCommand.model_validate(
            r.model_dump() | {"quantity": {"amount": 0, "basis": "EP_RAW_G"}}
        )


@pytest.mark.parametrize("mutation", ["identity", "overreserved"])
def test_standalone_position_rejects_invalid_reservation(mutation):
    data = snapshot().positions[0].model_dump()
    data["reserved"] = {
        "amount": "401" if mutation == "overreserved" else "1",
        "basis": "AP_G" if mutation == "identity" else "EP_RAW_G",
    }
    with pytest.raises(ValueError):
        c.InventoryPosition.model_validate(data)


def test_batch_flow_draft_separates_raw_and_prepared_identities():
    raw, prepared = uuid4(), uuid4()
    fact = c.BatchFlowLinkDraft(
        household_id=uuid4(),
        input_lot_ids=(raw,),
        output_lot_ids=(prepared,),
        recipe_version_id=uuid4(),
        grounded_variant_fingerprint="b" * 64,
        input_movement_ids=(uuid4(),),
        output_movement_ids=(uuid4(),),
    )
    assert not fact.execution_ready
    assert c.BatchFlowLinkDraft.model_validate_json(fact.model_dump_json()) == fact
    with pytest.raises(ValueError):
        c.BatchFlowLinkDraft.model_validate(fact.model_dump() | {"output_lot_ids": (raw,)})
