"""INV-005/007/011/018: resolved primitives, never invented facts or physical supply."""

import ast
from datetime import timedelta
from decimal import Decimal, localcontext
from pathlib import Path
from uuid import uuid4

import pytest
from app.domain.units import MeasurementBasis
from app.modules.inventory.contracts import PhysicalInventorySnapshot
from app.modules.planning.contracts import (
    CandidateGroundingRequest,
    CandidateGroundingSources,
    GroundedDishCandidate,
    grounding_canonical_json,
)
from app.modules.planning.grounding import resolve_captured_candidate
from app.modules.recipes.contracts import RecipeVersionSnapshot, VariantGenerationRequest
from app.modules.recipes.public import generate_variants
from grounding_fixtures import empty_inventory, setup


def test_complete_primitives_keep_draft_and_no_authority():
    q, s, _ = setup()
    result = resolve_captured_candidate(q, s)
    assert result.status == "GROUNDED"
    c = result.candidate
    assert c.shortlist_input_ready and not c.activation_ready
    assert c.request.candidate.status == "DRAFT" and not c.request.candidate.activation_ready
    assert c.input_nutrition.energy_kcal == 400 and c.input_nutrition.protein_g == 40
    assert c.preparation_outputs[0].output.amount == Decimal("142.469")
    assert c.ingredient_facts[0].inventory_paths[0].usable_quantity.amount == 200
    assert GroundedDishCandidate.model_validate_json(c.model_dump_json()) == c
    with pytest.raises(ValueError):
        c.activation_ready = True


@pytest.mark.parametrize("mutation", ["ingredient", "quantity", "rule", "tier", "fingerprint"])
def test_forged_culinary_claims_rejected_after_source_recompute(mutation):
    q, s, _ = setup()
    c = q.candidate
    rows = list(c.resolved_ingredients)
    if mutation == "ingredient":
        rows[0] = rows[0].model_copy(update=dict(ingredient_id=uuid4()))
    if mutation == "quantity":
        rows[0] = rows[0].model_copy(
            update=dict(quantity=rows[0].quantity.model_copy(update=dict(amount=Decimal(201))))
        )
    c = c.model_copy(update=dict(resolved_ingredients=tuple(rows)))
    if mutation == "rule":
        c = c.model_copy(update=dict(selected_rule_ids=(uuid4(),)))
    if mutation == "tier":
        c = c.model_copy(update=dict(tier_id=uuid4()))
    c = c.model_copy(update=dict(fingerprint=c.expected_fingerprint()))
    if mutation == "fingerprint":
        c = c.model_copy(update=dict(fingerprint="f" * 64))
        with pytest.raises(ValueError):
            resolve_captured_candidate(q.model_copy(update=dict(candidate=c)), s)
        return
    out = resolve_captured_candidate(q.model_copy(update=dict(candidate=c)), s)
    assert out.status == "REJECTED" and out.candidate is None


@pytest.mark.parametrize(
    "extra", ["nutrition_references", "nutrition_total", "procurement_quotes", "is_safe"]
)
def test_public_command_cannot_inject_nutrition_price_or_safety_claims(extra):
    q, _, _ = setup()
    with pytest.raises(ValueError):
        CandidateGroundingRequest.model_validate(q.model_dump() | {extra: {"protein_g": "999"}})


@pytest.mark.parametrize(
    "case", ["missing", "cooked_basis", "draft", "future", "ambiguous", "nonterminating"]
)
def test_unknown_or_incompatible_nutrition_fails_closed(case):
    q, s, _ = setup()
    r = s.nutrition_references[0]
    fact = r.fact
    if case == "cooked_basis":
        fact = fact.model_copy(
            update=dict(
                reference=fact.reference.model_copy(update=dict(basis=MeasurementBasis.COOKED_G))
            )
        )
    if case == "draft":
        fact = fact.model_copy(update=dict(status="DRAFT"))
    if case == "future":
        fact = fact.model_copy(
            update=dict(
                provenance=fact.provenance.model_copy(
                    update=dict(observed_at=q.as_of + timedelta(days=1))
                )
            )
        )
    if case == "nonterminating":
        fact = fact.model_copy(
            update=dict(reference=fact.reference.model_copy(update=dict(amount=Decimal(3))))
        )
    refs = (r.model_copy(update=dict(fact=fact)),)
    if case == "missing":
        refs = ()
    if case == "ambiguous":
        refs = (r, r.model_copy(update=dict(id=uuid4())))
    result = resolve_captured_candidate(q, s.model_copy(update=dict(nutrition_references=refs)))
    assert result.status == "INCOMPLETE" and result.candidate is None
    assert result.issues[0].code.startswith("NUTRITION_")


def test_explicit_nutrition_id_selection_resolves_ambiguity_without_inventing_values():
    q, s, _ = setup()
    r = s.nutrition_references[0]
    s = s.model_copy(update=dict(nutrition_references=(r, r.model_copy(update=dict(id=uuid4())))))
    d = q.model_dump() | dict(
        nutrition_selections=[
            dict(
                requirement_id=q.candidate.resolved_ingredients[0].requirement_id, reference_id=r.id
            )
        ]
    )
    result = resolve_captured_candidate(CandidateGroundingRequest.model_validate(d), s)
    assert result.status == "GROUNDED"
    assert result.candidate.ingredient_facts[0].nutrition.reference == r


@pytest.mark.parametrize("granularity", ["FIXED_PACK", "CATCH_WEIGHT", "LOOSE_SCALE"])
def test_granularity_coefficients_are_distinct_exact_and_unallocated(granularity):
    q, s, f = setup(granularity)
    out = resolve_captured_candidate(q, empty_inventory(s))
    p = out.candidate.ingredient_facts[0].procurement_paths[0]
    y = f["mapping"].edible_yield
    if granularity == "FIXED_PACK":
        assert p.nominal_ep_g == 500 * y and p.low_ep_g is None
    elif granularity == "CATCH_WEIGHT":
        assert (p.low_ep_g, p.nominal_ep_g, p.high_ep_g) == (450 * y, 500 * y, 550 * y)
    else:
        assert p.minimum_ep_g == 100 * y and p.step_ep_g == 25 * y and p.nominal_ep_g is None
    assert not hasattr(p, "purchase_cost") and not hasattr(p, "package_count")


@pytest.mark.parametrize(
    "origin", ["RETAIL_OBSERVED", "REFERENCE_BASELINE", "CALIBRATED_REFERENCE"]
)
def test_reference_and_unknown_evidence_never_imply_physical_stock(origin):
    q, s, f = setup(origin=origin, availability="UNKNOWN")
    s = empty_inventory(s)
    before = s.inventory.model_dump_json()
    result = resolve_captured_candidate(q, s)
    assert result.status == "GROUNDED" and not result.activation_ready
    line = result.candidate.ingredient_facts[0]
    assert line.inventory_paths == ()
    p = line.procurement_paths[0]
    assert p.option.quote.evidence_kind == origin and p.availability == "UNKNOWN"
    assert p.interpretation == "CONDITIONAL_EVIDENCE"
    assert p.freshness_assessment == "NOT_IMPLEMENTED"
    assert any(i.code == "UNKNOWN_RETAIL_AVAILABILITY" for i in result.issues)
    assert s.inventory.model_dump_json() == before
    if origin != "RETAIL_OBSERVED":
        assert p.option.quote.observation is None
        assert p.option.quote.reference_price_pair.money_for_reference_quantity.amount_minor == (
            66_000 if origin == "CALIBRATED_REFERENCE" else 60_000
        )
        assert p.priced_ep_raw.amount == 1000 * f["mapping"].edible_yield
        assert p.nominal_ep_g == 500 * f["mapping"].edible_yield


@pytest.mark.parametrize(
    "case", ["missing", "unavailable", "currency", "region", "inactive", "future"]
)
def test_no_eligible_procurement_and_no_stock_is_incomplete(case):
    q, s, f = setup(availability="UNAVAILABLE" if case == "unavailable" else "LIKELY")
    s = empty_inventory(s)
    if case == "missing":
        s = s.model_copy(update=dict(procurements=()))
    if case == "currency":
        q = q.model_copy(update=dict(currency="USD"))
    if case == "region":
        q = q.model_copy(update=dict(region_code="VN-HN"))
    if case == "inactive":
        s = s.model_copy(
            update=dict(
                retailer_statuses=(f["retailer_status"].model_copy(update=dict(status="INACTIVE")),)
            )
        )
    if case == "future":
        q = q.model_copy(update=dict(as_of=f["quote"].as_of - timedelta(seconds=1)))
        s = s.model_copy(update=dict(inventory=s.inventory.model_copy(update=dict(as_of=q.as_of))))
    out = resolve_captured_candidate(q, s)
    assert out.status == "INCOMPLETE" and out.candidate is None


def test_inventory_only_is_a_possibility_not_zero_cost_or_global_feasibility():
    q, s, _ = setup()
    s = s.model_copy(update=dict(procurements=(), retailer_statuses=()))
    before = s.inventory.model_dump_json()
    result = resolve_captured_candidate(q, s)
    assert result.status == "GROUNDED"
    line = result.candidate.ingredient_facts[0]
    assert line.procurement_paths == ()
    assert line.inventory_paths[0].allocation == "UNALLOCATED"
    assert line.inventory_paths[0].usable_quantity.amount == 200
    assert s.inventory.model_dump_json() == before
    assert not hasattr(result.candidate, "is_feasible")


@pytest.mark.parametrize("case", ["expired", "stale", "unknown", "fully_reserved"])
def test_unusable_inventory_does_not_silently_become_supply(case):
    q, s, _ = setup()
    d = s.inventory.model_dump()
    if case == "expired":
        d["lots"][0]["usable_until"] = q.as_of - timedelta(minutes=1)
        d["positions"][0]["lifecycle_state"] = "EXPIRED"
    elif case in {"stale", "unknown"}:
        d["lots"][0]["observation_confidence"] = case.upper()
    else:
        d["reservations"][0]["quantity"]["amount"] = Decimal(400)
        d["positions"][0]["reserved"]["amount"] = Decimal(400)
    physical = PhysicalInventorySnapshot.model_validate(d)
    result = resolve_captured_candidate(
        q, s.model_copy(update=dict(inventory=physical, procurements=()))
    )
    assert result.status == "INCOMPLETE" and result.candidate is None


def test_inventory_ap_mapping_retained_and_recipe_cooking_yield_separate():
    q, s, f = setup()
    d = s.inventory.model_dump()
    d["lots"][0]["acquired_quantity"]["basis"] = "AP_G"
    d["lots"][0]["retail_mapping"] = f["mapping"].model_dump()
    for event in (*d["movements"], *d["reservations"]):
        event["quantity"]["basis"] = "AP_G"
    d["positions"][0]["remaining"]["basis"] = "AP_G"
    d["positions"][0]["reserved"]["basis"] = "AP_G"
    physical = PhysicalInventorySnapshot.model_validate(d)
    result = resolve_captured_candidate(q, s.model_copy(update=dict(inventory=physical)))
    p = result.candidate.ingredient_facts[0].inventory_paths[0]
    assert p.lot.retail_mapping == f["mapping"] and p.lot.acquired_quantity.basis == "AP_G"
    assert p.usable_quantity.amount == 200 * f["mapping"].edible_yield
    assert result.candidate.preparation_outputs[0].output.amount == Decimal("142.469")
    assert result.candidate.input_nutrition.protein_g == 40


@pytest.mark.parametrize("kind", ["ALLERGEN", "DIET_RULE", "EXCLUDED_INGREDIENT"])
def test_primitive_member_safety_cannot_be_overridden_by_caller(kind):
    from app.modules.nutrition.contracts import MemberSafetySourceFact

    q, s, _ = setup()
    safety = s.member_safety[0]
    source = MemberSafetySourceFact(
        id=uuid4(),
        recorded_at=q.as_of,
        constraint=dict(
            household_id=q.household_id,
            member_id=q.tracked_member_id,
            kind=kind,
            code="hard.rule",
            ingredient_id=s.recipe.ingredients[0].ingredient_id
            if kind == "EXCLUDED_INGREDIENT"
            else None,
            actor_user_id=uuid4(),
        ),
    )
    safety = safety.model_copy(update=dict(constraints=(source,)))
    result = resolve_captured_candidate(q, s.model_copy(update=dict(member_safety=(safety,))))
    assert result.status == ("REJECTED" if kind == "EXCLUDED_INGREDIENT" else "INCOMPLETE")
    assert result.candidate is None


def test_cross_household_participant_is_rejected():
    q, s, _ = setup()
    q = q.model_copy(update=dict(tracked_member_id=uuid4()))
    out = resolve_captured_candidate(q, s)
    assert out.status == "REJECTED" and out.issues[0].code == "PARTICIPANT_OWNER_MISMATCH"


def test_canonical_ordering_and_ambient_precision_do_not_change_identity():
    q, s, _ = setup()
    a = resolve_captured_candidate(q, s).candidate
    physical = s.inventory.model_copy(update=dict(movements=tuple(reversed(s.inventory.movements))))
    s2 = s.model_copy(update=dict(inventory=physical))
    with localcontext() as ctx:
        ctx.prec = 3
        b = resolve_captured_candidate(q, s2).candidate
    assert a is not None and b is not None
    assert a.fingerprint == b.fingerprint and a.canonical_json() == b.canonical_json()
    assert s.fingerprint() == s2.fingerprint()


def test_primitive_provenance_change_changes_candidate_identity():
    q, s, _ = setup()
    a = resolve_captured_candidate(q, s).candidate
    ref = s.nutrition_references[0]
    ref = ref.model_copy(
        update=dict(
            fact=ref.fact.model_copy(
                update=dict(
                    provenance=ref.fact.provenance.model_copy(update=dict(source_version="2"))
                )
            )
        )
    )
    b = resolve_captured_candidate(
        q, s.model_copy(update=dict(nutrition_references=(ref,)))
    ).candidate
    assert a.fingerprint != b.fingerprint


def test_new_undeclared_ordered_sequence_is_not_silently_sorted():
    with pytest.raises(ValueError, match="Undeclared collection"):
        grounding_canonical_json(
            dict(future_preparation_steps=[dict(text="boil"), dict(text="fry")])
        )


def test_assembler_is_not_a_solver_and_keeps_frozen_validator_independent():
    import app.modules.planning.grounding as assembler
    import app.modules.validation.recipe_grounding as validator

    for module in (assembler, validator):
        source = Path(module.__file__).read_text(encoding="utf-8")
        imports = [
            n.module or "" for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ImportFrom)
        ]
        assert not any(
            any(s in name for s in ("ortools", "optimizer", "ranking", "shortlist", "learning"))
            for name in imports
        )
    assert "recipes.public" not in Path(validator.__file__).read_text(encoding="utf-8")


def test_sources_and_recipe_count_basis_remain_explicit_not_inferred():
    q, s, _ = setup()
    d = s.recipe.model_dump()
    d["ingredients"][0]["quantity"].update(basis="COUNT", item_ref="author.count")
    d["transformations"] = []
    recipe = RecipeVersionSnapshot.model_validate(d)
    c = generate_variants(
        VariantGenerationRequest(
            recipe=recipe, demand={}, limits=dict(max_attempts=1, max_candidates=1)
        )
    ).candidates[0]
    out = resolve_captured_candidate(
        q.model_copy(update=dict(candidate=c)), s.model_copy(update=dict(recipe=recipe))
    )
    assert out.status == "INCOMPLETE" and out.issues[0].code == "NUTRITION_REFERENCE_UNRESOLVED"


def test_source_contract_rejects_duplicate_canonical_identity():
    _, s, _ = setup()
    with pytest.raises(ValueError, match="Duplicate captured"):
        CandidateGroundingSources.model_validate(
            s.model_dump() | dict(nutrition_references=s.nutrition_references * 2)
        )


def test_prepared_component_requires_cooked_nutrition_and_keeps_physical_identity():
    q, s, _ = setup()
    rd = s.recipe.model_dump()
    rd["ingredients"][0]["quantity"]["basis"] = "COOKED_G"
    rd["transformations"] = []
    recipe = RecipeVersionSnapshot.model_validate(rd)
    candidate = generate_variants(
        VariantGenerationRequest(
            recipe=recipe, demand={}, limits=dict(max_attempts=1, max_candidates=1)
        )
    ).candidates[0]
    d = s.inventory.model_dump()
    d["lots"][0]["asset_type"] = "PREPARED_COMPONENT"
    d["lots"][0]["acquired_quantity"]["basis"] = "COOKED_G"
    for e in (*d["movements"], *d["reservations"]):
        e["quantity"]["basis"] = "COOKED_G"
        if e.get("movement_type") == "ACQUIRE":
            e["phase"] = 40
        if e.get("movement_type") == "CONSUME":
            e["phase"] = 50
    for key in ("remaining", "reserved"):
        d["positions"][0][key]["basis"] = "COOKED_G"
    ref = s.nutrition_references[0]
    fact = ref.fact.model_copy(
        update=dict(
            reference=ref.fact.reference.model_copy(update=dict(basis=MeasurementBasis.COOKED_G))
        )
    )
    sources = s.model_copy(
        update=dict(
            recipe=recipe,
            inventory=PhysicalInventorySnapshot.model_validate(d),
            nutrition_references=(ref.model_copy(update=dict(fact=fact)),),
        )
    )
    out = resolve_captured_candidate(q.model_copy(update=dict(candidate=candidate)), sources)
    assert out.status == "GROUNDED" and out.candidate.preparation_outputs == ()
    line = out.candidate.ingredient_facts[0]
    assert line.procurement_paths == ()
    assert line.inventory_paths[0].lot.id == s.inventory.lots[0].id
    assert line.inventory_paths[0].lot.asset_type == "PREPARED_COMPONENT"
    assert line.inventory_paths[0].usable_quantity.basis == "COOKED_G"


def test_shared_participant_unknown_safety_is_not_erased_by_tracked_member():
    from app.modules.households.contracts import HouseholdMemberIdentity, MealParticipants
    from app.modules.nutrition.contracts import (
        CanonicalMemberSafetySnapshot,
        MemberSafetySourceFact,
    )

    q, s, _ = setup()
    other = uuid4()
    participants = MealParticipants(
        participants=(
            *q.participants.participants,
            dict(member_id=other, portion_factor="1", nutrition_role="SHARED"),
        )
    )
    member = HouseholdMemberIdentity(household_id=q.household_id, member_id=other)
    safety = CanonicalMemberSafetySnapshot(
        household_id=q.household_id,
        member_id=other,
        constraints=(
            MemberSafetySourceFact(
                id=uuid4(),
                recorded_at=q.as_of,
                constraint=dict(
                    household_id=q.household_id,
                    member_id=other,
                    kind="ALLERGEN",
                    code="unknown.class",
                    actor_user_id=uuid4(),
                ),
            ),
        ),
    )
    out = resolve_captured_candidate(
        q.model_copy(update=dict(participants=participants)),
        s.model_copy(
            update=dict(members=(*s.members, member), member_safety=(*s.member_safety, safety))
        ),
    )
    assert out.status == "INCOMPLETE" and out.issues[0].code == "SAFETY_CLASSIFICATION_UNAVAILABLE"


def test_portion_factor_does_not_silently_rescale_authored_quantities():
    q, s, _ = setup()
    d = q.model_dump()
    d["participants"]["participants"][0]["portion_factor"] = "1.5"
    out = resolve_captured_candidate(CandidateGroundingRequest.model_validate(d), s)
    assert out.candidate.request.candidate.serving_count == 2
    assert out.candidate.input_nutrition.protein_g == 40


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1.2])
def test_nonfinite_or_float_source_quantity_is_rejected(value):
    q, _, _ = setup()
    d = q.model_dump()
    d["candidate"]["resolved_ingredients"][0]["quantity"]["amount"] = value
    with pytest.raises(ValueError):
        CandidateGroundingRequest.model_validate(d)


@pytest.mark.parametrize(
    "target",
    [
        "ortools.sat.python.cp_model",
        "app.modules.planning.optimizer",
        "app.modules.planning.ranking",
        "app.modules.planning.shortlist",
        "app.modules.planning.utility",
        "app.modules.learning.public",
    ],
)
def test_grounding_import_guard_blocks_solver_ranking_and_learning(target):
    import runpy

    root = Path(__file__).resolve().parents[3]
    checker = runpy.run_path(str(root / "tools/check_import_boundaries.py"))["check_source"]
    assert any(
        "GROUNDING_NOT_OPTIMIZATION" in e
        for e in checker(f"import {target}", "app.modules.planning.grounding")
    )
