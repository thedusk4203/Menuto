"""Review counterexamples: path-specific preparation and contextual COUNT identity."""

import pytest
from app.modules.recipes import contracts as c
from pydantic import ValidationError
from recipe_fixtures import bind, recipe_data


@pytest.mark.parametrize(
    "base_transform,substitute_transform",
    [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ],
)
@pytest.mark.parametrize("substitute", [False, True])
def test_preparation_selection_follows_resolved_path(
    base_transform,
    substitute_transform,
    substitute,
):
    data = recipe_data()
    base, replacement = data["transformations"]
    data["transformations"] = ([base] if base_transform else []) + (
        [replacement] if substitute_transform else []
    )
    snapshot = c.RecipeVersionSnapshot.model_validate(data)
    selection = (snapshot.variant_rules[0].id,) if substitute else ()
    if substitute and base_transform and not substitute_transform:
        with pytest.raises(ValueError, match="authored cooking transformation"):
            bind(snapshot, selected_rule_ids=selection)
        return
    draft = bind(snapshot, selected_rule_ids=selection)
    selected_transform = replacement if substitute else base
    requires_transform = substitute_transform if substitute else base_transform
    assert [t.id for t in draft.transformations] == (
        [selected_transform["id"]] if requires_transform else []
    )
    assert draft.serving_count == snapshot.base_servings
    assert c.GroundedRecipeVariantDraft.model_validate_json(draft.model_dump_json()) == draft
    # Wrong-path evidence cannot be injected into an otherwise valid draft.
    if base_transform != substitute_transform:
        changed = draft.model_dump()
        changed["transformations"] = [replacement if not substitute else base]
        with pytest.raises(ValidationError):
            c.GroundedRecipeVariantDraft.model_validate(changed)


@pytest.mark.parametrize("structural", [False, True])
def test_count_targeted_substitution_rejected_even_if_not_selected(structural):
    data = recipe_data()
    data["variant_rules"][1].update(
        requirement_id=data["ingredients"][3]["id"],
        structural=structural,
    )
    with pytest.raises(ValidationError, match="COUNT.*substitution|substitution.*COUNT"):
        c.RecipeVersionSnapshot.model_validate(data)


def test_unsubstituted_count_retains_its_item_identity():
    snapshot = c.RecipeVersionSnapshot.model_validate(recipe_data())
    draft = bind(snapshot)
    source = snapshot.ingredients[3]
    result = draft.resolved_ingredients[3]
    assert result.ingredient_id == source.ingredient_id
    assert result.quantity.basis == "COUNT" and result.quantity.item_ref == "garnish.egg"
    assert result.quantity.amount == 1


@pytest.mark.parametrize("basis", ["EP_RAW_G", "COOKED_G"])
def test_v1_mass_substitutions_remain_available(basis):
    data = recipe_data()
    data["ingredients"][1]["quantity"]["basis"] = basis
    snapshot = c.RecipeVersionSnapshot.model_validate(data)
    rule = snapshot.variant_rules[1]
    result = bind(snapshot, selected_rule_ids=(rule.id,)).resolved_ingredients[1]
    assert result.ingredient_id == rule.replacement_ingredient_id
    assert result.quantity.basis == basis and result.quantity.item_ref is None
