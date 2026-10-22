"""Quantity contribution identities and v1/v2 immutable graph compatibility."""

from copy import deepcopy
from uuid import uuid4

import pytest
from app.modules.planning.contracts import PlanIntentGraph
from plan_fixtures import NOW, graph_data


def attributed_data():
    d = graph_data()
    requirement = uuid4()
    d["shopping"] = [
        dict(
            node_id=requirement,
            ingredient_id=uuid4(),
            quantity=dict(amount="1000", basis="EP_RAW_G"),
            need_by=NOW,
        )
    ]
    d["shopping_contributions"] = [
        dict(
            node_id=uuid4(),
            requirement_node_id=requirement,
            meal_node_id=meal["node_id"],
            quantity=dict(amount=amount, basis="EP_RAW_G"),
        )
        for meal, amount in zip(d["meals"], ["600", "400"], strict=True)
    ]
    return d


def test_contribution_exact_sum_hash_roundtrip_and_immutability():
    d = attributed_data()
    g = PlanIntentGraph.model_validate(d)
    assert g.contract_version == "plan-intent.v2"
    d["shopping_contributions"].reverse()
    assert PlanIntentGraph.model_validate(d).fingerprint() == g.fingerprint()
    assert PlanIntentGraph.model_validate_json(g.model_dump_json()) == g
    with pytest.raises(ValueError):
        g.shopping_contributions[0].meal_node_id = uuid4()


@pytest.mark.parametrize(
    "mutation",
    [
        "sum",
        "basis",
        "item_ref",
        "missing_requirement",
        "missing_target",
        "both_targets",
        "no_target",
        "duplicate",
        "negative",
        "nonfinite",
        "float",
        "precision",
        "retired_target",
        "retired_requirement",
        "v1",
    ],
)
def test_invalid_contribution_semantics(mutation):
    d = deepcopy(attributed_data())
    c = d["shopping_contributions"][0]
    if mutation == "sum":
        c["quantity"]["amount"] = "601"
    if mutation == "basis":
        c["quantity"]["basis"] = "AP_G"
    if mutation == "item_ref":
        c["quantity"] = dict(amount="600", basis="COUNT", item_ref="egg.large")
    if mutation == "missing_requirement":
        c["requirement_node_id"] = uuid4()
    if mutation == "missing_target":
        c["meal_node_id"] = uuid4()
    if mutation == "both_targets":
        c["batch_node_id"] = uuid4()
    if mutation == "no_target":
        c.pop("meal_node_id")
    if mutation == "duplicate":
        d["shopping_contributions"].append(deepcopy(c))
    if mutation == "negative":
        c["quantity"]["amount"] = "-600"
    if mutation == "nonfinite":
        c["quantity"]["amount"] = "NaN"
    if mutation == "float":
        c["quantity"]["amount"] = 600.0
    if mutation == "precision":
        c["quantity"]["amount"] = "600.0000001"
    if mutation == "retired_target":
        d["meals"][0]["status"] = "RETIRED"
    if mutation == "retired_requirement":
        d["shopping"][0]["status"] = "RETIRED"
    if mutation == "v1":
        d["contract_version"] = "plan-intent.v1"
    with pytest.raises(ValueError):
        PlanIntentGraph.model_validate(d)


def test_legacy_v1_content_hash_does_not_grow_new_empty_field():
    import json
    from hashlib import sha256

    from app.modules.planning.contracts import canonical_value

    g = PlanIntentGraph.model_validate(graph_data() | {"contract_version": "plan-intent.v1"})
    original = g.model_dump(exclude={"shopping_contributions"})
    for name in ("meals", "batches", "allocations", "shopping", "reservations"):
        original[name] = sorted(original[name], key=lambda v: str(v["node_id"]))
    expected = sha256(
        json.dumps(
            canonical_value(original), sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()
    assert g.fingerprint() == expected


def test_v1_command_fingerprint_remains_replay_compatible():
    import json
    from hashlib import sha256

    from app.modules.execution.public import fingerprint
    from app.modules.planning.contracts import canonical_value
    from plan_fixtures import propose_command

    g = PlanIntentGraph.model_validate(graph_data() | {"contract_version": "plan-intent.v1"})
    command = propose_command(g, uuid4())
    original = command.model_dump()
    original["graph"].pop("shopping_contributions")
    old_hash = sha256(
        json.dumps(
            canonical_value(original), sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()
    assert fingerprint(command) == old_hash
