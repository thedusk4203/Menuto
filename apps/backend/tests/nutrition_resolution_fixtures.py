"""NRE TEST_ONLY primitive fixtures; offline packages prove no canonical DB origin."""

from datetime import timedelta
from uuid import uuid4

from app.domain.feature_identity import canonical
from app.modules.catalog.contracts import IngredientIdentityFact, NutritionReferenceFact
from app.modules.nutrition import resolution_contracts as c
from app.modules.nutrition.synthesis import nutrition_policy_requirements
from app.modules.recipes.contracts import RecipeVersionSnapshot
from nutrition_synthesis_pure_fixtures import retained


def food(observed):
    version, recipe_id = uuid4(), uuid4()
    ingredients = [uuid4(), uuid4()]
    requirements = [uuid4(), uuid4()]
    evidence = dict(
        kind="USER_AUTHORED",
        source_system="TEST_ONLY.recipe",
        external_record_id=str(version),
        source_version="TEST_ONLY_v1",
        observed_at=observed,
    )
    r = RecipeVersionSnapshot.model_validate(
        dict(
            id=version,
            recipe=dict(id=recipe_id, name="TEST_ONLY finite food", cooking_method="TEST_ONLY"),
            version=1,
            serving_definition="TEST_ONLY.whole_tier",
            serving_description="TEST_ONLY",
            base_servings="1",
            procedure="TEST_ONLY structural fixture, no clinical meaning.",
            provenance=evidence,
            review_status="REVIEWED",
            ingredients=tuple(
                dict(
                    id=requirements[i],
                    recipe_version_id=version,
                    slot=f"TEST_ONLY_{i}",
                    ingredient_id=ingredients[i],
                    quantity=dict(amount=str(3 * (i + 1)), basis="EP_RAW_G"),
                    role="TEST_ONLY",
                    scaling=dict(kind="DISCRETE", quantum="1") if i == 0 else dict(kind="LINEAR"),
                    adjustment=dict(kind="DISCRETE", min_delta="-1", max_delta="1", step="1")
                    if i == 0
                    else dict(kind="NONE", min_delta="0", max_delta="0"),
                )
                for i in range(2)
            ),
            portion_tiers=tuple(
                dict(
                    id=uuid4(),
                    recipe_version_id=version,
                    key=f"TEST_ONLY_{n}",
                    servings=str(n),
                    quantities=tuple(
                        dict(requirement_id=requirements[i], amount=str(n * 3 * (i + 1)))
                        for i in range(2)
                    ),
                )
                for n in (1, 2)
            ),
            variant_rules=(),
            approved_combinations=(),
            transformations=(),
        )
    )
    identities = tuple(
        IngredientIdentityFact(id=i, name="TEST_ONLY ingredient") for i in ingredients
    )
    refs = tuple(
        NutritionReferenceFact.model_validate(
            dict(
                id=uuid4(),
                fact=dict(
                    ingredient_id=identity,
                    reference=dict(amount="1", basis="EP_RAW_G"),
                    nutrients=dict(
                        zip(
                            ("energy_kcal", "protein_g", "fat_g", "carbohydrate_g"),
                            map(str, ((2, 1, 0, 3), (1, 3, 1, 0))[i]),
                        )
                    ),
                    provenance=dict(
                        kind="REVIEWED_REFERENCE",
                        source_system="TEST_ONLY.catalog",
                        external_record_id=str(identity),
                        source_version="TEST_ONLY_v1",
                        observed_at=observed,
                    ),
                    status="REVIEWED",
                ),
            )
        )
        for i, identity in enumerate(ingredients)
    )
    return (
        r,
        tuple(sorted(identities, key=lambda x: str(x.id))),
        tuple(sorted(refs, key=lambda x: str(x.id))),
    )


def manifest(recipes, ingredients, refs):
    rows = []
    for owner, values in (("Recipe", recipes), ("Ingredient", ingredients), ("Reference", refs)):
        rows += [
            c.NreFixtureFact(
                owner=owner,
                identity=r.id,
                ingredient_id=r.fact.ingredient_id if owner == "Reference" else None,
                body_fingerprint=c.resolution_hash("fixture", r),
            )
            for r in values
        ]
    return tuple(sorted(rows, key=lambda x: (x.owner, str(x.identity))))


def scope(synthesis, recipe, refs):
    req = nutrition_policy_requirements(synthesis)
    actor, subject = synthesis.request.precision.actor_user_id, req.subject
    alternatives = tuple(
        c.NreServingDeclaration(
            kind="WHOLE_TIER_TO_SINGLE_TRACKED_MEMBER_V1",
            subject=subject,
            actor_user_id=actor,
            slot_id="TEST_ONLY_slot",
            recipe_version_id=recipe.id,
            tier_id=t.id,
            rule_ids=(),
            serving_definition=recipe.serving_definition,
        )
        for t in recipe.portion_tiers
    )
    return c.NutritionResolutionScopeV1(
        kind="EXACT_DECLARED_RECIPE_VERSION_SET_V1",
        subject=subject,
        actor_user_id=actor,
        root_request=synthesis.request.root.sources.request,
        selection=synthesis.request.selection,
        precision=synthesis.request.precision,
        requirement_fingerprint=req.fingerprint,
        recipes=(
            c.NreRecipeSelection(
                recipe_version_id=recipe.id,
                tier_ids=tuple(t.id for t in recipe.portion_tiers),
                rule_selections=((),),
            ),
        ),
        references=tuple(
            c.NreReferenceSelection(
                ingredient_id=r.fact.ingredient_id,
                basis=r.fact.reference.basis.value,
                reference_id=r.id,
            )
            for r in refs
        ),
        slots=(
            c.NreSlot(
                slot_id="TEST_ONLY_slot", interval=req.temporal.interval, alternatives=alternatives
            ),
        ),
        environment="TEST_ONLY",
    )


def row_count(recipes, ingredients, refs):
    return (
        3
        + len(ingredients)
        + len(refs)
        + len({r.recipe.id for r in recipes})
        + sum(
            2
            + len(r.ingredients)
            + len(r.portion_tiers)
            + sum(len(t.quantities) for t in r.portion_tiers)
            + len(r.variant_rules)
            + len(r.approved_combinations)
            + sum(len(x.rule_ids) for x in r.approved_combinations)
            + len(r.transformations)
            for r in recipes
        )
    )


def rehash(value, *, food_manifest=False, counts=False):
    data = canonical(value)
    if food_manifest:
        recipes = tuple(RecipeVersionSnapshot.model_validate(x) for x in data["recipes"])
        ingredients = tuple(IngredientIdentityFact.model_validate(x) for x in data["ingredients"])
        refs = tuple(NutritionReferenceFact.model_validate(x) for x in data["references"])
        proof = manifest(recipes, ingredients, refs)
        data["frame"]["fixture_manifest"] = canonical(proof)
        data["frame"]["fixture_food_fingerprint"] = c.resolution_hash("fixture-manifest", proof)
        data["recipe_seals"] = [
            dict(
                recipe_version_id=r.id, sealed=True, body_fingerprint=c.resolution_hash("recipe", r)
            )
            for r in recipes
        ]
        if counts:
            data["frame"]["owner_row_count"] = row_count(recipes, ingredients, refs)
    data["source_fingerprint"] = "0" * 64
    value = c.NutritionResolutionSourcesV1.model_validate(data)
    data = canonical(value)
    data.pop("source_fingerprint")
    return c.NutritionResolutionSourcesV1(
        **data, source_fingerprint=c.resolution_hash("sources", data)
    )


def sources(synthesis=None):
    synthesis = retained().inputs if synthesis is None else synthesis
    recipe, ingredients, refs = food(synthesis.frame.completed_at - timedelta(hours=1))
    request = scope(synthesis, recipe, refs)
    witness = synthesis.frame.reader_subject_witness
    from app.modules.planning.nutrition_resolution_capture import READ_RELATIONS

    frame = c.NreCaptureFrame(
        source_frame=synthesis.frame,
        actor_user_id=request.actor_user_id,
        subject=request.subject,
        membership_id=witness.membership_id,
        membership_role=witness.role,
        member_id=witness.actor_member_id,
        started_at=synthesis.request.root.sources.capture.started_at,
        completed_at=synthesis.frame.completed_at,
        owner_row_count=row_count((recipe,), ingredients, refs),
        owner_relations=READ_RELATIONS,
        fixture_database_oid=synthesis.frame.session.database_oid,
        fixture_database_name=synthesis.frame.session.database_name,
        fixture_food_fingerprint=c.resolution_hash(
            "fixture-manifest", manifest((recipe,), ingredients, refs)
        ),
        fixture_manifest=manifest((recipe,), ingredients, refs),
    )
    return rehash(
        c.NutritionResolutionSourcesV1(
            scope=request,
            synthesis_sources=synthesis,
            requirements=nutrition_policy_requirements(synthesis),
            recipes=(recipe,),
            recipe_seals=(
                c.NreRecipeSeal(
                    recipe_version_id=recipe.id,
                    sealed=True,
                    body_fingerprint=c.resolution_hash("recipe", recipe),
                ),
            ),
            ingredients=ingredients,
            references=refs,
            absences=(),
            frame=frame,
            source_fingerprint="0" * 64,
        )
    )
