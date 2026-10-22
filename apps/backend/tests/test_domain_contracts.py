"""INV-003/004/018: verify boundaries that would otherwise corrupt later calculations."""

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from app.domain.snapshots import (
    BudgetContract,
    CanonicalMemberSafety,
    Horizon,
    MealSlotInput,
    ParticipantInput,
    PlannerOutputDraft,
    PlannerRequestDraft,
    PreparedFoodAssetFact,
    RawIngredientAssetFact,
    SourceVersion,
    ValidationSubjectDraft,
    snapshot_hash,
)
from app.domain.units import Money, Provenance, Quantity, YieldConversion
from app.modules.catalog.contracts import NutritionFact, NutritionValues
from app.modules.households.contracts import HouseholdCreate, MealParticipants, Participant
from pydantic import ValidationError

NOW = datetime(2026, 10, 22, tzinfo=UTC)


@pytest.fixture
def provenance():
    return Provenance(
        kind="REVIEWED_REFERENCE",
        source_system="synthetic",
        external_record_id="synthetic-test",
        source_version="1",
        observed_at=NOW,
    )


@pytest.mark.parametrize(
    "value", [0.1, True, "NaN", "Infinity", "-Infinity", "bad", "-1", "0.0000001", "1000000000000"]
)
def test_quantity_rejects_inexact_nonfinite_negative_or_unstorable_inputs(value):
    with pytest.raises(ValidationError):
        Quantity(amount=value, basis="EP_RAW_G")


def test_quantity_roundtrip_and_semantically_equal_hashes():
    a = Quantity(amount="100.000000", basis="EP_RAW_G")
    b = Quantity(amount=100, basis="EP_RAW_G")
    assert a.amount == Decimal(100)
    assert Quantity.model_validate_json(a.model_dump_json()) == a
    assert snapshot_hash(a) == snapshot_hash(b)
    assert snapshot_hash(a) != snapshot_hash(Quantity(amount=100, basis="AP_G"))


@pytest.mark.parametrize(
    "other",
    [
        {"amount": "1", "basis": "AP_G"},
        {"amount": "1", "basis": "COOKED_G"},
        {"amount": "1", "basis": "SERVING", "item_ref": "recipe-v1"},
        {"amount": "1", "basis": "COUNT", "item_ref": "egg"},
    ],
)
def test_no_implicit_basis_conversion(other):
    with pytest.raises(ValueError, match="Incompatible"):
        Quantity(amount=100, basis="EP_RAW_G").add(Quantity(**other))


def test_count_and_serving_definitions_are_required_and_cannot_be_mixed():
    for basis in ("COUNT", "SERVING"):
        with pytest.raises(ValidationError):
            Quantity(amount=1, basis=basis)
    egg = Quantity(amount=1, basis="COUNT", item_ref="egg")
    with pytest.raises(ValueError):
        egg.add(Quantity(amount=1, basis="COUNT", item_ref="apple"))
    assert egg.add(egg).amount == 2
    assert Quantity(amount="0.2", basis="EP_RAW_G").add(
        Quantity(amount="0.1", basis="EP_RAW_G")
    ).amount == Decimal("0.3")


def test_separate_edible_and_cooking_yields(provenance):
    edible = YieldConversion(
        kind="EDIBLE_YIELD", context_ref="product-map-v1", factor="0.8", provenance=provenance
    )
    cooking = YieldConversion(
        kind="COOKING_YIELD", context_ref="recipe-prep-v1", factor="2.5", provenance=provenance
    )
    raw = edible.apply(Quantity(amount=100, basis="AP_G"))
    assert raw.amount == 80 and raw.basis == "EP_RAW_G"
    assert cooking.apply(raw).amount == 200 and cooking.apply(raw).basis == "COOKED_G"
    with pytest.raises(ValueError, match="requires"):
        cooking.apply(Quantity(amount=100, basis="AP_G"))
    with pytest.raises(ValueError, match="requires"):
        edible.apply(raw)  # Double application cannot pass.
    with pytest.raises(ValidationError):
        YieldConversion(
            kind="EDIBLE_YIELD", context_ref="mapping", factor="1.1", provenance=provenance
        )


def test_yield_does_not_silently_round_to_storage_precision(provenance):
    conversion = YieldConversion(
        kind="EDIBLE_YIELD", context_ref="map", factor="0.333333", provenance=provenance
    )
    assert conversion.apply(Quantity(amount="0.000001", basis="AP_G")).amount == Decimal(
        "0.000000333333"
    )


def test_money_uses_integer_minor_units_and_explicit_currency():
    vnd = Money(amount_minor=1000, currency="VND")
    assert vnd.add(vnd).amount_minor == 2000
    for value in (1.1, "100", True, -1, 2**63):
        with pytest.raises(ValidationError):
            Money(amount_minor=value, currency="VND")
    with pytest.raises(ValueError):
        vnd.add(Money(amount_minor=1000, currency="USD"))


def test_timezones_and_provenance_are_explicit(provenance):
    with pytest.raises(ValidationError):
        Provenance(**{**provenance.model_dump(), "observed_at": datetime(2026, 10, 22)})
    with pytest.raises(ValidationError):
        HouseholdCreate(name="Test", member_name="Member", timezone="Unknown/Place")
    assert HouseholdCreate(name="Test", member_name="Member").timezone == "Asia/Ho_Chi_Minh"
    shifted = provenance.model_dump()
    shifted["observed_at"] = NOW.astimezone(timezone(timedelta(hours=7)))
    assert snapshot_hash(provenance) == snapshot_hash(Provenance(**shifted))


def test_participants_are_unique_and_portion_is_not_nutrition_ratio():
    member_id = uuid4()
    tracked = Participant(member_id=member_id, portion_factor="1.0", nutrition_role="TRACKED")
    shared = Participant(member_id=uuid4(), portion_factor="0.8", nutrition_role="SHARED")
    meal = MealParticipants(participants=(tracked, shared))
    assert meal.attendance_scale == Decimal("1.8")
    with pytest.raises(ValidationError):
        MealParticipants(participants=(tracked, tracked))
    with pytest.raises(ValidationError):
        MealParticipants(
            participants=(
                tracked,
                Participant(member_id=uuid4(), portion_factor=1, nutrition_role="TRACKED"),
            )
        )


@pytest.mark.parametrize("basis", ["AP_G", "SERVING", "COUNT"])
def test_nutrition_cannot_use_purchased_mass_or_unresolved_serving_reference(basis, provenance):
    reference = Quantity(
        amount=100, basis=basis, item_ref="example" if basis in {"SERVING", "COUNT"} else None
    )
    with pytest.raises(ValidationError):
        NutritionFact(
            ingredient_id=uuid4(),
            reference=reference,
            provenance=provenance,
            status="REVIEWED",
            nutrients=NutritionValues(energy_kcal=100, protein_g=1, fat_g=1, carbohydrate_g=1),
        )


@pytest.fixture
def plan_request():
    tracked_id = uuid4()
    return PlannerRequestDraft(
        household_id=uuid4(),
        actor_user_id=uuid4(),
        tracked_member_id=tracked_id,
        horizon=Horizon(start=NOW, end=NOW + timedelta(days=3)),
        nutrition_precision="STANDARD",
        cost_preference="NORMAL",
        kitchen_effort="NORMAL",
        budget=BudgetContract(constraint="NONE"),
        meals=(
            MealSlotInput(
                slot_id=uuid4(),
                at=NOW,
                meal_kind="HOME",
                participants=(
                    ParticipantInput(
                        member_id=tracked_id, portion_factor=1, nutrition_role="TRACKED"
                    ),
                ),
            ),
        ),
        sources=(SourceVersion(source="inventory", version="1", fingerprint="0" * 64),),
        planner_version="draft-1",
        policy_version="draft-1",
    )


@pytest.mark.parametrize(
    "constraint,amount",
    [("NONE", {"amount_minor": 1, "currency": "VND"}), ("TARGET", None), ("SPEND_LIMIT", None)],
)
def test_budget_axes_cannot_be_conflated(constraint, amount):
    with pytest.raises(ValidationError):
        BudgetContract(constraint=constraint, amount=amount)


def test_horizon_and_revision_lock_and_extra_fields(plan_request):
    data = plan_request.model_dump()
    data["plan_id"] = uuid4()
    with pytest.raises(ValidationError, match="Revision requires"):
        PlannerRequestDraft(**data)
    for extra in ("PlanningMode", "budget_pressure", "attendance_scale"):
        with pytest.raises(ValidationError):
            PlannerRequestDraft(**{**plan_request.model_dump(), extra: "user supplied"})
    with pytest.raises(ValidationError):
        Horizon(start=NOW, end=NOW)
    meal = plan_request.meals[0].model_dump()
    meal["at"] = plan_request.horizon.end
    with pytest.raises(ValidationError):
        PlannerRequestDraft(**{**plan_request.model_dump(), "meals": [meal]})


def test_draft_subject_requires_canonical_participant_safety_and_matching_assets(
    plan_request, provenance
):
    safety = CanonicalMemberSafety(
        member_id=plan_request.tracked_member_id,
        source_version="1",
        allergen_codes=("peanut",),
        diet_rule_codes=(),
        excluded_ingredient_ids=(),
    )
    subject = ValidationSubjectDraft(
        household_id=plan_request.household_id,
        request=plan_request,
        canonical_members=(safety,),
        opening_assets=(),
    )
    assert ValidationSubjectDraft.model_validate_json(subject.model_dump_json()) == subject
    assert subject.validation_ready is False
    assert subject.missing_contracts
    with pytest.raises(ValidationError):
        subject.canonical_members = ()
    assert isinstance(subject.canonical_members, tuple)
    with pytest.raises(ValidationError):
        ValidationSubjectDraft(**{**subject.model_dump(), "household_id": uuid4()})
    with pytest.raises(ValidationError):
        ValidationSubjectDraft(
            **{
                **subject.model_dump(),
                "canonical_members": [{**safety.model_dump(), "member_id": uuid4()}],
            }
        )
    foreign_asset = RawIngredientAssetFact(
        asset_kind="RAW_INGREDIENT",
        inventory_lot_id=uuid4(),
        fact_id=uuid4(),
        household_id=uuid4(),
        ingredient_id=uuid4(),
        quantity=Quantity(amount=100, basis="EP_RAW_G"),
        available_from=NOW,
        usable_until=NOW + timedelta(days=1),
        provenance=provenance,
    )
    with pytest.raises(ValidationError):
        ValidationSubjectDraft(**{**subject.model_dump(), "opening_assets": [foreign_asset]})


def test_draft_status_cannot_authorize_activation():
    with pytest.raises(ValidationError):
        PlannerOutputDraft(
            run_id=uuid4(),
            request_hash="0" * 64,
            status="OPTIMAL",
            reasons=(),
            activation_ready=True,
        )


@pytest.mark.parametrize(
    "module,source",
    [
        ("app.modules.validation.service", "from app.persistence.database import session_factory"),
        ("app.modules.validation.service", "from sqlalchemy import select"),
        ("app.domain.snapshots", "from app.modules.planning.contracts import Anything"),
    ],
)
def test_neutral_fact_reader_cannot_import_database_or_domain_implementation(module, source):
    import runpy
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    checker = runpy.run_path(str(root / "tools/check_import_boundaries.py"))
    assert checker["check_source"](source, module)


def test_provenance_accepts_opaque_provider_identity_and_separate_uri():
    evidence = Provenance(
        kind="RETAIL_OBSERVATION",
        source_system="synthetic-store",
        external_record_id="catalog/rau củ/offer?id=abc 123",
        source_version="feed/2026-10-22 rev 2",
        source_uri="https://retail.example.invalid/products/123?region=hcm",
        content_hash="a" * 64,
        observed_at=NOW,
    )
    assert evidence.external_record_id == "catalog/rau củ/offer?id=abc 123"
    assert evidence.source_system == "synthetic-store"
    assert Provenance.model_validate_json(evidence.model_dump_json()) == evidence


@pytest.mark.parametrize(
    "overrides",
    [
        {"external_record_id": " "},
        {"external_record_id": "opaque\nrecord"},
        {"source_system": "https://wrong-identity.invalid"},
        {"source_version": " "},
        {"source_uri": "ftp://invalid.example.invalid/file"},
        {"source_uri": "https://user:password@example.invalid/path"},
        {"content_hash": "bad-hash"},
        {"source_ref": "legacy-must-migrate"},
    ],
)
def test_provenance_does_not_silently_accept_bad_or_legacy_identity(provenance, overrides):
    with pytest.raises(ValidationError):
        Provenance.model_validate({**provenance.model_dump(), **overrides})


def test_subject_preserves_typed_raw_and_prepared_opening_assets(plan_request, provenance):
    safety = CanonicalMemberSafety(
        member_id=plan_request.tracked_member_id,
        source_version="1",
        allergen_codes=(),
        diet_rule_codes=(),
        excluded_ingredient_ids=(),
    )
    common = dict(
        household_id=plan_request.household_id,
        available_from=NOW,
        usable_until=NOW + timedelta(days=2),
        provenance=provenance,
    )
    raw = RawIngredientAssetFact(
        **common,
        fact_id=uuid4(),
        asset_kind="RAW_INGREDIENT",
        inventory_lot_id=uuid4(),
        ingredient_id=uuid4(),
        quantity=Quantity(amount=100, basis="EP_RAW_G"),
    )
    prepared = PreparedFoodAssetFact(
        **common,
        fact_id=uuid4(),
        asset_kind="PREPARED_FOOD",
        prepared_food_lot_id=uuid4(),
        cooking_batch_id=uuid4(),
        recipe_version_id=uuid4(),
        serving_definition_ref="batch-v1-serving",
        quantity=Quantity(amount=2, basis="SERVING", item_ref="batch-v1-serving"),
    )
    subject = ValidationSubjectDraft(
        household_id=plan_request.household_id,
        request=plan_request,
        canonical_members=(safety,),
        opening_assets=(raw, prepared),
    )
    restored = ValidationSubjectDraft.model_validate_json(subject.model_dump_json())
    assert restored.opening_assets == (raw, prepared)
    assert isinstance(restored.opening_assets[0], RawIngredientAssetFact)
    assert isinstance(restored.opening_assets[1], PreparedFoodAssetFact)
    assert restored.validation_ready is False
    assert "HORIZON_BRIDGE" in restored.missing_contracts
    duplicate = raw.model_dump()
    duplicate["fact_id"] = uuid4()
    with pytest.raises(ValidationError, match="Duplicate physical"):
        ValidationSubjectDraft.model_validate(
            {**subject.model_dump(), "opening_assets": [raw, duplicate]}
        )
    for bad_asset in [
        {**raw.model_dump(), "asset_kind": "PREPARED_FOOD"},
        {**raw.model_dump(), "quantity": prepared.quantity.model_dump()},
        {**prepared.model_dump(), "serving_definition_ref": "other-serving"},
        {**prepared.model_dump(), "ingredient_id": uuid4()},
    ]:
        with pytest.raises(ValidationError):
            ValidationSubjectDraft.model_validate(
                {**subject.model_dump(), "opening_assets": [bad_asset]}
            )
    old = subject.model_dump()
    old["contract_version"] = "validation-subject.m0-draft.1"
    with pytest.raises(ValidationError):
        ValidationSubjectDraft.model_validate(old)
