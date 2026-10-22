"""Synthetic authored examples; no production culinary calibration claims."""

from datetime import UTC, datetime
from uuid import uuid4

from app.modules.recipes.contracts import RecipeVersionSnapshot


def provenance(kind="USER_AUTHORED"):
    return dict(
        kind=kind,
        source_system="synthetic.recipe",
        external_record_id=str(uuid4()),
        source_version="1",
        observed_at=datetime(2026, 10, 22, tzinfo=UTC),
    )


def recipe_data():
    version_id = uuid4()
    ingredients = []
    for index, (policy, amount, extra) in enumerate(
        (
            ("LINEAR", "200", {}),
            ("SUBLINEAR", "100", {}),
            ("FIXED", "10", {}),
            ("DISCRETE", "1", {"quantum": "1"}),
            ("TO_TASTE", "2", {"minimum": "1", "maximum": "5"}),
        )
    ):
        ingredients.append(
            dict(
                id=uuid4(),
                recipe_version_id=version_id,
                slot=f"slot-{index}",
                ingredient_id=uuid4(),
                quantity=dict(
                    amount=amount,
                    basis="COUNT" if index == 3 else "EP_RAW_G",
                    item_ref="garnish.egg" if index == 3 else None,
                ),
                role=f"role-{index}",
                scaling=dict(kind=policy, **extra),
                adjustment=dict(kind="PORTIONABLE", min_delta="-20", max_delta="60")
                if index == 0
                else dict(kind="NONE", min_delta="0", max_delta="0"),
            )
        )
    tiers = [
        dict(
            id=uuid4(),
            recipe_version_id=version_id,
            key=key,
            servings=servings,
            quantities=[
                dict(requirement_id=i["id"], amount=amount)
                for i, amount in zip(ingredients, amounts)
            ],
        )
        for key, servings, amounts in (
            ("STANDARD_2", "2", ("200", "100", "10", "1", "2")),
            ("STANDARD_4", "4", ("400", "160", "10", "2", "3")),
        )
    ]
    rules = [
        dict(
            id=uuid4(),
            recipe_version_id=version_id,
            key=f"replacement-{index}",
            version=1,
            requirement_id=ingredients[index]["id"],
            replacement_ingredient_id=uuid4(),
            quantity_factor="1.1" if index == 0 else "1",
            structural=True,
            provenance=provenance(),
        )
        for index in range(2)
    ]
    transformations = [
        dict(
            id=uuid4(),
            recipe_version_id=version_id,
            requirement_id=ingredients[0]["id"],
            ingredient_id=ingredient_id,
            preparation_key="protein.fry",
            method="STIR_FRY",
            version=1,
            factor="0.712345",
            provenance=provenance(),
        )
        for ingredient_id in (
            ingredients[0]["ingredient_id"],
            rules[0]["replacement_ingredient_id"],
        )
    ]
    return dict(
        id=version_id,
        recipe=dict(id=uuid4(), name="Synthetic stir fry", cooking_method="STIR_FRY"),
        version=1,
        serving_definition="adult.main",
        serving_description="One main portion",
        base_servings="2",
        procedure="Stir fry the authored ingredients.",
        provenance=provenance(),
        review_status="REVIEWED",
        ingredients=ingredients,
        portion_tiers=tiers,
        variant_rules=rules,
        approved_combinations=[],
        transformations=transformations,
    )


def snapshot():
    return RecipeVersionSnapshot.model_validate(recipe_data())


def bind(snapshot, **overrides):
    from app.modules.recipes.public import bind_culinary_draft

    fields = dict(
        snapshot=snapshot,
        tier_id=snapshot.portion_tiers[0].id,
        selected_rule_ids=(),
        adjustment_deltas={i.id: "0" for i in snapshot.ingredients},
        variant_reason="DEFAULT",
        derivation_policy_version="culinary.binding.test.1",
        provenance=provenance(),
    )
    fields.update(overrides)
    # Binding API accepts exact string decimals like other public contracts.
    return bind_culinary_draft(**fields)
