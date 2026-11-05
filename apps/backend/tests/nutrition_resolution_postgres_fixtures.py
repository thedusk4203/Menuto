"""Actual ordinary readers and server-owned TEST_ONLY fixture registration."""

from datetime import timedelta

import pytest
from app.modules.catalog.models import Ingredient, NutritionFact
from app.modules.catalog.public import catalog_facts
from app.modules.nutrition.resolution_contracts import (
    NutritionResolutionScopeRequestV1,
    resolution_hash,
)
from app.modules.planning.nutrition_resolution_capture import (
    READ_RELATIONS,
    _configure_isolated_test_capture,
    capture_nutrition_resolution_sources,
)
from app.modules.recipes.public import authored_version
from app.modules.recipes.repository import RecipeRepository, source_fields
from nutrition_resolution_fixtures import food, manifest, scope
from nutrition_root_postgres_fixtures import reader
from nutrition_synthesis_postgres_fixtures import capture_rules, publish, setup_synthesis
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.orm import Session


def configure_fixture(s, recipe_id):
    with Session(s["engines"]["root"]) as admin:
        recipe = authored_version(admin, recipe_id)
        ids = {i.ingredient_id for i in recipe.ingredients}
        ids.update(r.replacement_ingredient_id for r in recipe.variant_rules)
        ingredients, refs = catalog_facts(admin, ids)
        oid, name = admin.execute(
            text("SELECT oid,datname FROM pg_database WHERE datname=current_database()")
        ).one()
    return (
        _configure_isolated_test_capture(oid, name, manifest((recipe,), ingredients, refs)),
        recipe,
        refs,
    )


@pytest.fixture
def nre_case(nrc_server):
    s = setup_synthesis(nrc_server)
    publish(s)
    synthesis = capture_rules(s)
    recipe, identities, refs = food(synthesis.frame.completed_at - timedelta(hours=1))
    with Session(s["engines"]["root"]) as admin:
        admin.add_all(Ingredient(id=x.id, name=x.name) for x in identities)
        admin.flush()
        repo = RecipeRepository(admin)
        repo.add_recipe(recipe.recipe)
        repo.add_version(recipe)
        for ref in refs:
            fact = ref.fact
            admin.add(
                NutritionFact(
                    id=ref.id,
                    ingredient_id=fact.ingredient_id,
                    reference_amount=fact.reference.amount,
                    basis=fact.reference.basis.value,
                    **fact.nutrients.model_dump(),
                    status=fact.status,
                    **source_fields(fact.provenance),
                )
            )
        admin.commit()
    with s["engines"]["root"].connect() as admin:
        for relation in READ_RELATIONS:
            admin.connection.driver_connection.execute(
                sql.SQL("GRANT SELECT ON public.{} TO {}").format(
                    sql.Identifier(relation), sql.Identifier(s["names"]["self"])
                )
            )
        admin.connection.driver_connection.commit()
    ctx, canonical_recipe, canonical_refs = configure_fixture(s, recipe.id)
    bound = scope(synthesis, canonical_recipe, canonical_refs)
    request = NutritionResolutionScopeRequestV1.model_validate(
        bound.model_dump(exclude={"requirement_fingerprint"})
        | {"contract_version": "nutrition-resolution-scope-request.v1"}
    )
    s.update(
        nre_context=ctx,
        nre_scope=request,
        nre_recipe=canonical_recipe,
        nre_references=canonical_refs,
        nre_synthesis=synthesis,
    )
    return s


def capture_nre(s, *, scope_value=None, who="self", isolation="REPEATABLE READ", readonly=True):
    with reader(s, who, isolation=isolation, readonly=readonly) as db:
        return capture_nutrition_resolution_sources(
            db, s["nre_context"], scope_value or s["nre_scope"]
        )


def fingerprint_rows(s):
    with Session(s["engines"]["root"]) as db:
        return (
            tuple(
                (r, db.scalar(text('SELECT count(*) FROM public."' + r + '"')))
                for r in READ_RELATIONS
            ),
            db.scalar(text("SELECT sum(revision) FROM nutrition_source_streams")),
            resolution_hash("scope", s["nre_scope"]),
        )
