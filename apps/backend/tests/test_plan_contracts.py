"""Frozen intent graph/source identity/hash and architecture negative cases."""

from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

import pytest
from app.modules.planning import contracts as c
from plan_fixtures import NOW, graph_data
from test_architecture import check_source


def test_graph_roundtrip_frozen_hash_order_independent():
    g = c.PlanIntentGraph.model_validate(graph_data())
    data = g.model_dump()
    data["meals"] = list(reversed(data["meals"]))
    assert c.PlanIntentGraph.model_validate(data).fingerprint() == g.fingerprint()
    assert c.PlanIntentGraph.model_validate_json(g.model_dump_json()) == g
    with pytest.raises(ValueError):
        g.plan_id = uuid4()


@pytest.mark.parametrize(
    "mutation",
    [
        "outside_horizon",
        "naive",
        "duplicate_slot",
        "duplicate_member",
        "wrong_tracked",
        "no_home_batch",
        "missing_basis",
        "zero_quantity",
        "negative",
        "nonfinite",
        "float",
        "overprecision",
        "two_reservation_targets",
        "unknown_target",
        "zero_reserve",
    ],
)
def test_invalid_graph_primitives(mutation):
    d = graph_data()
    m = d["meals"][0]
    if mutation == "outside_horizon":
        m["scheduled_at"] = NOW + timedelta(days=9)
    if mutation == "naive":
        m["scheduled_at"] = NOW.replace(tzinfo=None)
    if mutation == "duplicate_slot":
        d["meals"].append(deepcopy(m))
    if mutation == "duplicate_member":
        m["participants"].append(deepcopy(m["participants"][0]))
    if mutation == "wrong_tracked":
        m["participants"][0]["nutrition_role"] = "SHARED"
    if mutation == "no_home_batch":
        m["meal_kind"] = "HOME"
    if mutation in {
        "missing_basis",
        "zero_quantity",
        "negative",
        "nonfinite",
        "float",
        "overprecision",
    }:
        q = dict(amount="1", basis="EP_RAW_G")
        if mutation == "missing_basis":
            q.pop("basis")
        if mutation == "zero_quantity":
            q["amount"] = "0"
        if mutation == "negative":
            q["amount"] = "-1"
        if mutation == "nonfinite":
            q["amount"] = "NaN"
        if mutation == "float":
            q["amount"] = 1.5
        if mutation == "overprecision":
            q["amount"] = "0.0000001"
        d["shopping"] = [dict(node_id=uuid4(), ingredient_id=uuid4(), quantity=q, need_by=NOW)]
    if mutation in {"two_reservation_targets", "unknown_target", "zero_reserve"}:
        r = dict(
            node_id=uuid4(),
            lot_id=uuid4(),
            meal_node_id=m["node_id"],
            quantity=dict(amount="1", basis="EP_RAW_G"),
        )
        if mutation == "two_reservation_targets":
            r["batch_node_id"] = uuid4()
        if mutation == "unknown_target":
            r["meal_node_id"] = uuid4()
        if mutation == "zero_reserve":
            r["quantity"]["amount"] = "0"
        d["reservations"] = [r]
    with pytest.raises(ValueError):
        c.PlanIntentGraph.model_validate(d)


@pytest.mark.parametrize(
    "mutation", ["missing_batch", "future_production", "overallocate", "nonhome", "retired_batch"]
)
def test_batch_allocation_chronology_and_conservation(mutation):
    d = graph_data()
    m = d["meals"][0]
    m["meal_kind"] = "HOME"
    batch = uuid4()
    d["batches"] = [
        dict(
            node_id=batch,
            recipe_version_id=uuid4(),
            tier_id=uuid4(),
            planned_servings="2",
            planned_at=NOW,
        )
    ]
    d["allocations"] = [
        dict(node_id=uuid4(), batch_node_id=batch, meal_node_id=m["node_id"], servings="2")
    ]
    assert c.PlanIntentGraph.model_validate(d)
    if mutation == "missing_batch":
        d["batches"] = []
    if mutation == "future_production":
        d["batches"][0]["planned_at"] = NOW + timedelta(days=2)
    if mutation == "overallocate":
        d["allocations"][0]["servings"] = "3"
    if mutation == "nonhome":
        m["meal_kind"] = "SKIP"
    if mutation == "retired_batch":
        d["batches"][0]["status"] = "RETIRED"
    with pytest.raises(ValueError):
        c.PlanIntentGraph.model_validate(d)


@pytest.mark.parametrize(
    "target",
    [
        "shopping.public",
        "shopping.models",
        "inventory.models",
        "cooking.models",
        "recipes.models",
        "validation.models",
    ],
)
def test_plan_core_cannot_import_foreign_internals(target):
    assert check_source(f"import app.modules.{target}", "app.modules.planning.contracts")


@pytest.mark.parametrize("module", ["shopping", "cooking"])
def test_intent_contracts_cannot_cycle_into_plan(module):
    assert check_source("import app.modules.planning.contracts", f"app.modules.{module}.contracts")


def test_canonical_contract_edge_is_readonly():
    assert not check_source(
        "import app.modules.shopping.contracts", "app.modules.planning.contracts"
    )
    assert check_source("import app.modules.shopping.public", "app.modules.planning.public")


def test_no_physical_produced_or_fulfilled_claims():
    g = c.PlanIntentGraph.model_validate(graph_data())
    assert "produced_servings" not in g.model_dump_json()
    with pytest.raises(ValueError):
        c.PlanIntentGraph.model_validate(g.model_dump() | {"purchased": True})
