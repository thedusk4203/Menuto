"""Adversarial independent foundation checks; never a complete semantic PASS."""

from copy import deepcopy
from datetime import timedelta
from decimal import Decimal, localcontext
from uuid import uuid4

import pytest
from app.domain.units import Quantity
from app.modules.nutrition.contracts import MemberSafetyConstraint, MemberSafetySourceFact
from app.modules.validation.contracts import ValidationSubjectSnapshot
from app.modules.validation.public import validate_subject
from plan_fixtures import NOW
from test_architecture import check_source
from validation_fixtures import coverage_policy, subject


def codes(report):
    return {f.code for f in report.findings}


def revise(s, **updates):
    return ValidationSubjectSnapshot.model_validate(s.model_dump() | updates)


def restrict(s, kind="EXCLUDED_INGREDIENT", **changes):
    m = s.member_safety[0]
    c = MemberSafetyConstraint(
        **(
            dict(
                household_id=s.household_id,
                member_id=m.member_id,
                kind=kind,
                code="explicit.rule",
                ingredient_id=s.recipes[0].ingredients[0].ingredient_id
                if kind == "EXCLUDED_INGREDIENT"
                else None,
                actor_user_id=uuid4(),
            )
            | changes
        )
    )
    source = MemberSafetySourceFact(id=uuid4(), recorded_at=NOW, constraint=c)
    return revise(s, member_safety=(m.model_copy(update={"constraints": (source,)}),))


def test_supported_arithmetic_never_authorizes_partial_subject():
    s = subject()
    r = validate_subject(s)
    assert codes(r) == {"REQUIRED_CAPABILITY_UNAVAILABLE"}
    assert r.decision == "BLOCKED_UNSUPPORTED" and not r.activation_authorized
    assert r.default_batch_inputs[0].input_nutrition.energy_kcal == 400
    assert r.default_batch_inputs[0].input_nutrition.protein_g == 40
    assert r.material_balances[0].signed_closing_amount == 400
    assert r.material_balances[0].signed_reserved_amount == 200
    assert r.yield_estimates[0].output.amount == Decimal("142.469")


def test_roundtrip_immutability_semantic_hash_and_deterministic_report():
    s = subject()
    data = s.model_dump()
    data["inventory"]["movements"] = tuple(reversed(data["inventory"]["movements"]))
    data["proposal"]["graph"]["meals"] = tuple(reversed(data["proposal"]["graph"]["meals"]))
    other = ValidationSubjectSnapshot.model_validate(data)
    assert other.fingerprint == s.fingerprint and other.canonical_json() == s.canonical_json()
    assert validate_subject(other) == validate_subject(s)
    assert (
        ValidationSubjectSnapshot.model_validate_json(s.canonical_json()).fingerprint
        == s.fingerprint
    )
    with pytest.raises(ValueError):
        s.validation_ready = True
    with pytest.raises(ValueError):
        s.policy.policy_version = "2"


def test_policy_and_material_change_alter_subject_identity():
    s = subject()
    other = revise(s, policy=coverage_policy(policy_version="2"))
    assert other.fingerprint != s.fingerprint and other.policy.fingerprint != s.policy.fingerprint
    assert "UNSUPPORTED_VALIDATION_POLICY" in codes(validate_subject(other))
    data = s.model_dump()
    data["inventory"]["movements"][1]["quantity"]["amount"] = "101"
    assert ValidationSubjectSnapshot.model_validate(data).fingerprint != s.fingerprint


def test_primitive_exclusion_bypasses_no_planner_summary():
    s = restrict(subject())
    r = validate_subject(s)
    assert "FORBIDDEN_INGREDIENT" in codes(r) and r.decision == "REJECTED"
    data = s.model_dump() | {"is_safe": True}
    with pytest.raises(ValueError):
        ValidationSubjectSnapshot.model_validate(data)
    with pytest.raises(ValueError):
        ValidationSubjectSnapshot.model_validate(s.model_dump() | {"validation_ready": True})


def test_shared_participant_keeps_individual_primitive_safety():
    s = subject()
    new_member = uuid4()
    old_member = s.member_safety[0].member_id
    forbidden = restrict(s, member_id=new_member)
    safety = forbidden.member_safety[0].model_copy(update={"member_id": new_member})
    d = s.model_dump()
    d["members"] = list(d["members"]) + [dict(household_id=s.household_id, member_id=new_member)]
    d["member_safety"] = list(d["member_safety"]) + [safety.model_dump()]
    d["proposal"]["graph"]["meals"][0]["participants"] = list(
        d["proposal"]["graph"]["meals"][0]["participants"]
    ) + [dict(member_id=new_member, portion_factor="0.5", nutrition_role="SHARED")]
    from app.modules.planning.contracts import PlanIntentGraph

    d["proposal"]["graph_hash"] = PlanIntentGraph.model_validate(
        d["proposal"]["graph"]
    ).fingerprint()
    r = validate_subject(ValidationSubjectSnapshot.model_validate(d))
    finding = next(f for f in r.findings if f.code == "FORBIDDEN_INGREDIENT")
    assert str(new_member) in finding.proof_refs and str(old_member) not in finding.proof_refs


@pytest.mark.parametrize("kind", ["ALLERGEN", "DIET_RULE"])
def test_missing_classification_fails_closed_without_guessing(kind):
    r = validate_subject(restrict(subject(), kind))
    assert "SAFETY_CLASSIFICATION_UNAVAILABLE" in codes(r) and not r.activation_authorized


@pytest.mark.parametrize(
    "mutation",
    [
        "member_household",
        "missing_safety",
        "missing_member",
        "foreign_constraint",
        "missing_recipe",
        "missing_ingredient",
        "duplicate_member",
        "stale_revision",
        "missing_parent",
        "source_household",
    ],
)
def test_root_source_mutations_are_rejected(mutation):
    s = subject()
    d = s.model_dump()
    expected = "CANONICAL_MEMBER_SOURCE_MISSING"
    if mutation == "member_household":
        d["members"][0]["household_id"] = uuid4()
        expected = "MEMBER_HOUSEHOLD_MISMATCH"
    if mutation == "missing_safety":
        d["member_safety"] = ()
    if mutation == "missing_member":
        d["members"] = ()
    if mutation == "foreign_constraint":
        d = restrict(s, household_id=uuid4()).model_dump()
        expected = "SAFETY_SOURCE_OWNER_MISMATCH"
    if mutation == "missing_recipe":
        d["recipes"] = ()
        expected = "RECIPE_SOURCE_MISSING"
    if mutation == "missing_ingredient":
        d["ingredients"] = ()
        expected = "UNKNOWN_INGREDIENT_SOURCE"
    if mutation == "duplicate_member":
        d["members"] = d["members"] * 2
        expected = "DUPLICATE_CANONICAL_FACT"
    if mutation == "stale_revision":
        d["source_frontier"]["current_revision_no"] = 1
        expected = "STALE_PLAN_REVISION"
    if mutation == "missing_parent":
        d["source_frontier"]["current_revision_no"] = 0
        expected = "REVISION_SOURCE_MISMATCH"
    if mutation == "source_household":
        d["inventory"]["household_id"] = uuid4()
        expected = "SUBJECT_HOUSEHOLD_MISMATCH"
    assert expected in codes(validate_subject(ValidationSubjectSnapshot.model_validate(d)))


@pytest.mark.parametrize(
    "mutation",
    [
        "no_reference",
        "wrong_basis",
        "ambiguous",
        "draft",
        "recurring_ratio",
        "negative",
        "nonfinite",
        "float",
    ],
)
def test_nutrition_primitives_precision_and_missing_evidence(mutation):
    s = subject()
    d = s.model_dump()
    n = d["nutrition_references"][0]["fact"]
    if mutation == "no_reference":
        d["nutrition_references"] = ()
    if mutation == "wrong_basis":
        n["reference"]["basis"] = "COOKED_G"
    if mutation == "ambiguous":
        d["nutrition_references"] = d["nutrition_references"] * 2
    if mutation == "draft":
        n["status"] = "DRAFT"
    if mutation == "recurring_ratio":
        n["reference"]["amount"] = "3"
    if mutation == "negative":
        n["nutrients"]["energy_kcal"] = "-1"
    if mutation == "nonfinite":
        n["nutrients"]["energy_kcal"] = "NaN"
    if mutation == "float":
        n["nutrients"]["energy_kcal"] = 200.1
    if mutation in {"negative", "nonfinite", "float"}:
        with pytest.raises(ValueError):
            ValidationSubjectSnapshot.model_validate(d)
    else:
        r = validate_subject(ValidationSubjectSnapshot.model_validate(d))
        expected = (
            "NUTRITION_ARITHMETIC_UNRESOLVED"
            if mutation == "recurring_ratio"
            else "NUTRITION_SOURCE_UNRESOLVED"
        )
        assert expected in codes(r) and r.default_batch_inputs[0].input_nutrition is None


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("closing", "MATERIAL_CONSERVATION"),
        ("before_buy", "MATERIAL_BEFORE_ACQUIRE"),
        ("expired", "CONSUME_EXPIRED_MATERIAL"),
        ("negative", "CHRONOLOGICAL_STOCK_DEFICIT"),
        ("overreserve", "CHRONOLOGICAL_RESERVATION_DEFICIT"),
        ("phase", "MATERIAL_PHASE_MISMATCH"),
        ("basis", "MATERIAL_BASIS_MISMATCH"),
        ("sequence", "AMBIGUOUS_CAUSAL_ORDER"),
        ("unknown_lot", "UNKNOWN_MATERIAL_LOT"),
        ("missing_acquire", "MISSING_ACQUISITION"),
        ("duplicate_consume", "DUPLICATE_MATERIAL_FACT"),
        ("frontier", "INVENTORY_FRONTIER_MISMATCH"),
        ("foreign_lot", "MATERIAL_HOUSEHOLD_MISMATCH"),
        ("correction", "INVALID_CORRECTION_PARENT"),
        ("cutoff", "MATERIAL_AFTER_CUTOFF"),
        ("missing_position", "MATERIAL_POSITION_COVERAGE"),
    ],
)
def test_independent_material_mutations(mutation, expected):
    d = subject().model_dump()
    inv = d["inventory"]
    movement = inv["movements"][1]
    if mutation == "closing":
        inv["positions"][0]["remaining"]["amount"] = "401"
    if mutation == "before_buy":
        movement["occurred_at"] = inv["lots"][0]["acquired_at"] - timedelta(seconds=1)
    if mutation == "expired":
        inv["lots"][0]["usable_until"] = movement["occurred_at"]
    if mutation == "negative":
        movement["quantity"]["amount"] = "600"
    if mutation == "overreserve":
        inv["reservations"][0]["quantity"]["amount"] = "600"
    if mutation == "phase":
        movement["phase"] = 40
    if mutation == "basis":
        movement["quantity"]["basis"] = "AP_G"
    if mutation == "sequence":
        movement["ledger_sequence"] = 1
    if mutation == "unknown_lot":
        movement["lot_id"] = uuid4()
    if mutation == "missing_acquire":
        inv["movements"] = inv["movements"][1:]
    if mutation == "duplicate_consume":
        extra = deepcopy(movement)
        extra["ledger_sequence"] = 4
        inv["movements"] = (*inv["movements"], extra)
        d["source_frontier"]["inventory_ledger_sequence"] = 4
    if mutation == "frontier":
        d["source_frontier"]["inventory_ledger_sequence"] = 4
    if mutation == "foreign_lot":
        inv["lots"][0]["household_id"] = uuid4()
    if mutation == "correction":
        movement.update(movement_type="RECONCILE_DECREASE", phase=20, correction_of=uuid4())
    if mutation == "cutoff":
        inv["as_of"] = inv["lots"][0]["acquired_at"]
    if mutation == "missing_position":
        inv["positions"] = ()
    r = validate_subject(ValidationSubjectSnapshot.model_validate(d))
    assert expected in codes(r) and not r.activation_authorized
    if mutation == "basis":
        assert not r.material_balances


def test_raw_prepared_identity_is_never_converted_by_replay():
    d = subject().model_dump()
    lot = d["inventory"]["lots"][0]
    lot.update(
        asset_type="COOKED_DISH",
        ingredient_id=None,
        serving_definition="Dish portions",
        acquired_quantity=dict(amount="2", basis="SERVING", item_ref="batch.serving"),
    )
    r = validate_subject(ValidationSubjectSnapshot.model_validate(d))
    assert "MATERIAL_BASIS_MISMATCH" in codes(r) and not r.material_balances


def test_postfact_diagnoses_and_never_rewrites_history():
    s = restrict(subject())
    before = s.canonical_json()
    r = validate_subject(s, phase="POSTFACT_VALIDATION")
    assert r.decision == "DIAGNOSTIC" and "FORBIDDEN_INGREDIENT" in codes(r)
    assert not r.activation_authorized and s.canonical_json() == before
    with pytest.raises(ValueError):
        validate_subject(s, phase="AUTO_REPAIR")


def test_validation_has_no_external_io_or_ambient_decimal_dependency(monkeypatch):
    import builtins
    import socket

    s = subject()
    expected = validate_subject(s)

    def blocked(*a, **k):
        raise AssertionError("Validator attempted external IO")

    monkeypatch.setattr(builtins, "open", blocked)
    monkeypatch.setattr(socket, "socket", blocked)
    with localcontext() as ctx:
        ctx.prec = 3
        assert validate_subject(s) == expected


def test_reservation_release_is_not_physical_inflow():
    from app.modules.inventory.contracts import InventoryReservationRelease

    s = subject()
    reserve = s.inventory.reservations[0]
    fields = reserve.model_dump(exclude={"quantity", "purpose"})
    fields.update(
        id=uuid4(),
        ledger_sequence=4,
        reservation_id=reserve.id,
        occurred_at=NOW - timedelta(minutes=1),
        recorded_at=NOW,
    )
    d = s.model_dump()
    d["inventory"]["releases"] = (InventoryReservationRelease(**fields),)
    d["inventory"]["positions"][0]["reserved"]["amount"] = "0"
    d["source_frontier"]["inventory_ledger_sequence"] = 4
    r = validate_subject(ValidationSubjectSnapshot.model_validate(d))
    assert r.decision == "BLOCKED_UNSUPPORTED"
    assert r.material_balances[0].signed_closing_amount == 400
    assert r.material_balances[0].signed_reserved_amount == 0


def test_retail_edible_yield_is_estimate_not_material_conversion():
    from app.domain.units import Provenance
    from app.modules.retail.contracts import IngredientProductMapFact

    s = subject()
    d = s.model_dump()
    lot = d["inventory"]["lots"][0]
    mapping = IngredientProductMapFact(
        id=uuid4(),
        retail_product_id=uuid4(),
        ingredient_id=lot["ingredient_id"],
        version="1",
        edible_yield="0.812345",
        status="REVIEWED",
        confidence="UNKNOWN",
        reviewed_at=NOW,
        provenance=Provenance(
            kind="USER",
            source_system="synthetic.mapping",
            external_record_id="mapping.1",
            source_version="1",
            observed_at=NOW - timedelta(days=1),
        ),
    )
    lot["retail_mapping"] = mapping
    lot["acquired_quantity"]["basis"] = "AP_G"
    for e in (*d["inventory"]["movements"], *d["inventory"]["reservations"]):
        e["quantity"]["basis"] = "AP_G"
    d["inventory"]["positions"][0]["remaining"]["basis"] = "AP_G"
    d["inventory"]["positions"][0]["reserved"]["basis"] = "AP_G"
    updated = ValidationSubjectSnapshot.model_validate(d)
    r = validate_subject(updated)
    estimate = next(y for y in r.yield_estimates if y.owner == "RETAIL_MAPPING")
    assert estimate.owner_id == mapping.id and estimate.output.amount == Decimal("406.1725")
    assert r.material_balances[0].quantity_identity.basis == "AP_G"
    assert r.material_balances[0].signed_closing_amount == 400
    assert updated.inventory.lots[0].retail_mapping.provenance == mapping.provenance


def test_prepared_and_raw_balances_are_separate_even_when_both_present():
    from app.modules.inventory.contracts import InventoryLot, InventoryMovement, InventoryPosition

    s = subject()
    moment = NOW - timedelta(minutes=30)
    lot = InventoryLot(
        id=uuid4(),
        household_id=s.household_id,
        asset_type="COOKED_DISH",
        ingredient_id=None,
        acquired_quantity=Quantity(amount="2", basis="SERVING", item_ref="prepared.batch.1"),
        acquired_at=moment,
        created_at=moment,
        usable_until=None,
        observation_confidence="CONFIRMED",
        serving_definition="Two servings of prepared dish",
    )
    movement = s.inventory.movements[0].model_copy(
        update=dict(
            id=uuid4(),
            lot_id=lot.id,
            quantity=lot.acquired_quantity,
            phase=40,
            ledger_sequence=4,
            occurred_at=moment,
            recorded_at=NOW,
        )
    )
    d = s.model_dump()
    d["inventory"]["lots"] = (*s.inventory.lots, lot)
    d["inventory"]["movements"] = (
        *s.inventory.movements,
        InventoryMovement.model_validate(movement.model_dump()),
    )
    d["inventory"]["positions"] = (
        *s.inventory.positions,
        InventoryPosition(
            lot_id=lot.id,
            remaining=lot.acquired_quantity,
            reserved=Quantity(amount="0", basis="SERVING", item_ref="prepared.batch.1"),
            lifecycle_state="ACTIVE",
        ),
    )
    d["source_frontier"]["inventory_ledger_sequence"] = 4
    r = validate_subject(ValidationSubjectSnapshot.model_validate(d))
    assert r.decision == "BLOCKED_UNSUPPORTED"
    balances = {b.lot_id: b for b in r.material_balances}
    assert balances[lot.id].signed_closing_amount == 2
    assert balances[lot.id].quantity_identity.item_ref == "prepared.batch.1"
    assert balances[s.inventory.lots[0].id].signed_closing_amount == 400


@pytest.mark.parametrize(
    "source",
    [
        "import ortools",
        "import sqlalchemy",
        "import psycopg",
        "import sqlite3",
        "from app.modules.planning.public import PlanStore",
        "import app.modules.planning.optimizer",
        "import app.modules.recipes.calculations",
        "from app.modules.inventory.public import InventoryService",
        "import pathlib",
        "import socket",
        "open('report.json', 'w')",
        "import requests",
    ],
)
def test_validator_import_and_io_boundaries(source):
    assert check_source(source, "app.modules.validation.public")
