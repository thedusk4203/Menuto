"""INV-005/006/017/018: authored grounding, exact bases and serving preservation."""

from decimal import Decimal, localcontext
from uuid import uuid4

import pytest
from app.domain.units import CalculatedQuantity, Quantity, QuantizationPolicy
from app.modules.recipes import contracts as c
from app.modules.recipes.calculations import cooking_output
from pydantic import ValidationError
from recipe_fixtures import bind, provenance, recipe_data, snapshot


def test_version_snapshot_roundtrip_and_frozen():
    s = snapshot()
    assert c.RecipeVersionSnapshot.model_validate_json(s.model_dump_json()) == s
    with pytest.raises(ValidationError):
        s.version = 2
    data = s.model_dump()
    data.update(id=uuid4(), version=2)
    # Version children must be republished under the new version identity.
    with pytest.raises(ValidationError, match="Cross-version"):
        c.RecipeVersionSnapshot.model_validate(data)


@pytest.mark.parametrize(
    "basis,item", [("AP_G", None), ("SERVING", "main"), ("g", None), ("COUNT", None), (None, None)]
)
def test_explicit_edible_basis_required(basis, item):
    data = recipe_data()
    data["ingredients"][0]["quantity"].update(basis=basis, item_ref=item)
    with pytest.raises(ValidationError):
        c.RecipeVersionSnapshot.model_validate(data)


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-1", "0", "0.0000001", 1.2, True])
def test_source_quantity_rejects_nonfinite_negative_or_rounding(amount):
    data = recipe_data()
    data["ingredients"][0]["quantity"]["amount"] = amount
    with pytest.raises(ValidationError):
        c.RecipeVersionSnapshot.model_validate(data)


@pytest.mark.parametrize(
    "index,amount", [(0, "401"), (1, "201"), (1, "90"), (2, "11"), (3, "1.5"), (4, "6")]
)
def test_all_scaling_kinds_have_independent_guards(index, amount):
    data = recipe_data()
    data["portion_tiers"][1]["quantities"][index]["amount"] = amount
    with pytest.raises(ValidationError):
        c.RecipeVersionSnapshot.model_validate(data)


def test_all_scaling_kinds_and_authored_tiers():
    s = snapshot()
    result = bind(s, tier_id=s.portion_tiers[1].id)
    assert result.serving_count == 4
    assert [r.quantity.amount for r in result.resolved_ingredients] == [400, 160, 10, 2, 3]
    assert {i.scaling.kind for i in s.ingredients} == set(c.ScalingKind)
    with pytest.raises(ValueError, match="not authored"):
        bind(s, tier_id=uuid4())


@pytest.mark.parametrize(
    "policy",
    [
        dict(kind="LINEAR", quantum="1"),
        dict(kind="DISCRETE"),
        dict(kind="SUBLINEAR", minimum="1", maximum="2"),
        dict(kind="TO_TASTE"),
        dict(kind="TO_TASTE", minimum="2", maximum="1"),
    ],
)
def test_scaling_shape(policy):
    with pytest.raises(ValidationError):
        c.ScalingPolicy(**policy)


@pytest.mark.parametrize(
    "policy",
    [
        dict(kind="NONE", min_delta="0", max_delta="1"),
        dict(kind="SMALL", min_delta="-1", max_delta="2"),
        dict(kind="PORTIONABLE", min_delta="1", max_delta="2"),
        dict(kind="DISCRETE", min_delta="-1", max_delta="1", step="0"),
        dict(kind="DISCRETE", min_delta="-1", max_delta="1", step="0.3"),
        dict(kind="SMALL", min_delta="-1", max_delta="1", step="1"),
        dict(kind="PORTIONABLE", min_delta="0", max_delta="0"),
    ],
)
def test_adjustment_shape(policy):
    with pytest.raises(ValidationError):
        c.QuantityAdjustmentPolicy(**policy)


@pytest.mark.parametrize(
    "kind,delta", [("NONE", "1"), ("SMALL", "11"), ("PORTIONABLE", "61"), ("DISCRETE", "3")]
)
def test_binding_rejects_out_of_envelope(kind, delta):
    data = recipe_data()
    policies = {
        "NONE": dict(min_delta="0", max_delta="0"),
        "SMALL": dict(min_delta="-10", max_delta="10"),
        "PORTIONABLE": dict(min_delta="-20", max_delta="60"),
        "DISCRETE": dict(min_delta="-10", max_delta="10", step="2"),
    }
    data["ingredients"][0]["adjustment"] = dict(kind=kind, **policies[kind])
    s = c.RecipeVersionSnapshot.model_validate(data)
    deltas = {i.id: "0" for i in s.ingredients} | {s.ingredients[0].id: delta}
    with pytest.raises(ValueError):
        bind(s, adjustment_deltas=deltas)


def test_micro_adjustment_preserves_servings_and_has_no_ap_conversion():
    s = snapshot()
    base = bind(s)
    adjusted = bind(
        s, adjustment_deltas={i.id: "0" for i in s.ingredients} | {s.ingredients[0].id: "60"}
    )
    assert base.serving_count == adjusted.serving_count == 2
    assert adjusted.resolved_ingredients[0].quantity.amount == 260
    assert adjusted.resolved_ingredients[0].quantity.basis == "EP_RAW_G"
    assert not hasattr(adjusted, "produced_servings")


def test_structural_substitution_and_exact_approved_combination():
    data = recipe_data()
    s = c.RecipeVersionSnapshot.model_validate(data)
    single = bind(s, selected_rule_ids=(s.variant_rules[0].id,))
    assert (
        single.resolved_ingredients[0].ingredient_id == s.variant_rules[0].replacement_ingredient_id
    )
    assert single.resolved_ingredients[0].quantity.amount == 220
    assert single.transformations[0].ingredient_id == single.resolved_ingredients[0].ingredient_id
    ids = tuple(r.id for r in s.variant_rules)
    with pytest.raises(ValueError, match="combination"):
        bind(s, selected_rule_ids=ids)
    with pytest.raises(ValueError, match="not authored"):
        bind(s, selected_rule_ids=(uuid4(),))
    data["approved_combinations"] = [
        dict(
            id=uuid4(),
            recipe_version_id=s.id,
            key="approved.pair",
            rule_ids=ids,
            provenance=provenance(),
        )
    ]
    approved = c.RecipeVersionSnapshot.model_validate(data)
    assert len(bind(approved, selected_rule_ids=ids).selected_rule_ids) == 2


def test_substitution_cannot_reuse_original_ingredient_cooking_yield():
    data = recipe_data()
    data["transformations"] = data["transformations"][:1]
    s = c.RecipeVersionSnapshot.model_validate(data)
    with pytest.raises(ValueError, match="own|authored cooking"):
        bind(s, selected_rule_ids=(s.variant_rules[0].id,))


@pytest.mark.parametrize(
    "change",
    [
        dict(source_basis="AP_G"),
        dict(target_basis="EP_RAW_G"),
        dict(method="BOIL"),
        dict(ingredient_id=uuid4()),
    ],
)
def test_transformation_requires_correct_chain_and_context(change):
    data = recipe_data()
    data["transformations"][0].update(change)
    with pytest.raises(ValidationError):
        c.RecipeVersionSnapshot.model_validate(data)


def test_yield_precision_and_explicit_storage_policy():
    t = snapshot().transformations[0]
    with localcontext() as ctx:
        ctx.prec = 6
        result = cooking_output(t, Quantity(amount="123.456789", basis="EP_RAW_G"))
    assert result.amount == Decimal("87.943826360205")
    assert result.basis == "COOKED_G"
    stored = result.to_stored(QuantizationPolicy(version="test.1", rounding="FLOOR"))
    assert stored.stored.amount == Decimal("87.943826")
    assert stored.residual == Decimal("0.000000360205")
    with pytest.raises(ValueError):
        cooking_output(t, Quantity(amount="100", basis="AP_G"))
    # Rice cooking gain is legitimate; no edible-yield <=1 cap leaks here.
    gain = c.PreparationTransformationFact.model_validate(t.model_dump() | {"factor": "2.5"})
    assert cooking_output(gain, Quantity(amount="100", basis="EP_RAW_G")).amount == 250


@pytest.mark.parametrize(
    "alteration",
    ["serving_count", "ingredient", "quantity", "fingerprint", "rule", "ready", "retail"],
)
def test_grounded_draft_recomputes_authored_primitives(alteration):
    draft = bind(snapshot())
    data = draft.model_dump()
    if alteration == "serving_count":
        data["serving_count"] = "2.6"
    elif alteration == "ingredient":
        data["resolved_ingredients"][0]["ingredient_id"] = uuid4()
    elif alteration == "quantity":
        data["resolved_ingredients"][0]["quantity"]["amount"] = "260"
    elif alteration == "rule":
        data["selected_rule_ids"] = (uuid4(),)
    elif alteration == "ready":
        data["activation_ready"] = True
    elif alteration == "retail":
        data["price_quote"] = "forbidden"
    else:
        data["fingerprint"] = "0" * 64
    with pytest.raises(ValidationError):
        c.GroundedRecipeVariantDraft.model_validate(data)


def test_grounded_draft_roundtrip_and_deep_immutability():
    d = bind(snapshot())
    assert c.GroundedRecipeVariantDraft.model_validate_json(d.model_dump_json()) == d
    assert d.status == "DRAFT" and d.activation_ready is False
    with pytest.raises(ValidationError):
        d.resolved_ingredients[0].quantity.amount = 1
    assert isinstance(d.resolved_ingredients[0].quantity, CalculatedQuantity)


@pytest.mark.parametrize("field", ["version", "rule", "transformation"])
def test_import_provenance_never_implies_review(field):
    data = recipe_data()
    target = (
        data
        if field == "version"
        else data["variant_rules" if field == "rule" else "transformations"][0]
    )
    target["provenance"]["kind"] = "IMPORTED_DRAFT"
    with pytest.raises(ValidationError, match="Imported draft"):
        c.RecipeVersionSnapshot.model_validate(data)
    data["review_status"] = "DRAFT"
    assert c.RecipeVersionSnapshot.model_validate(data).review_status == "DRAFT"


def test_duplicate_tier_servings_and_missing_tier_slots():
    data = recipe_data()
    data["portion_tiers"][1]["servings"] = "2"
    with pytest.raises(ValidationError, match="Duplicate"):
        c.RecipeVersionSnapshot.model_validate(data)
    data = recipe_data()
    data["portion_tiers"][1]["quantities"].pop()
    with pytest.raises(ValidationError, match="Every tier"):
        c.RecipeVersionSnapshot.model_validate(data)


@pytest.mark.parametrize(
    "policy,delta",
    [
        (dict(kind="NONE", min_delta="0", max_delta="0"), "0"),
        (dict(kind="SMALL", min_delta="-10", max_delta="10"), "10"),
        (dict(kind="PORTIONABLE", min_delta="-20", max_delta="60"), "60"),
        (dict(kind="DISCRETE", min_delta="-10", max_delta="10", step="2"), "4"),
    ],
)
def test_each_adjustment_policy_accepts_authored_delta_without_changing_servings(policy, delta):
    data = recipe_data()
    data["ingredients"][0]["adjustment"] = policy
    s = c.RecipeVersionSnapshot.model_validate(data)
    d = bind(s, adjustment_deltas={i.id: "0" for i in s.ingredients} | {s.ingredients[0].id: delta})
    assert d.resolved_ingredients[0].quantity.amount == 200 + Decimal(delta)
    assert d.serving_count == s.base_servings


def test_explicit_nonstructural_rules_do_not_consume_structural_limit():
    data = recipe_data()
    data["variant_rules"][1]["structural"] = False
    s = c.RecipeVersionSnapshot.model_validate(data)
    assert (
        len(bind(s, selected_rule_ids=tuple(r.id for r in s.variant_rules)).selected_rule_ids) == 2
    )


def test_one_rule_per_slot_even_with_approved_combination():
    data = recipe_data()
    data["variant_rules"][1]["requirement_id"] = data["variant_rules"][0]["requirement_id"]
    s = c.RecipeVersionSnapshot.model_validate(data)
    with pytest.raises(ValueError, match="selected substitution slot"):
        bind(s, selected_rule_ids=tuple(r.id for r in s.variant_rules))
    data["approved_combinations"] = [
        dict(
            id=uuid4(),
            recipe_version_id=data["id"],
            key="invalid",
            rule_ids=[r["id"] for r in data["variant_rules"]],
            provenance=provenance(),
        )
    ]
    with pytest.raises(ValidationError, match="combination slot"):
        c.RecipeVersionSnapshot.model_validate(data)
