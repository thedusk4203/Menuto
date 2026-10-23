"""Real PostgreSQL handoff: generated choices still obey frozen0010 truth/seal guards."""

from uuid import uuid4

import pytest
from app.modules.execution.culinary_capture import capture_culinary_input
from app.modules.inventory.public import InventoryService
from app.modules.planning.culinary import bind_generated_candidate
from app.modules.recipes.public import generate_variants
from app.modules.validation.recipe_grounding import validate_recipe_grounding
from culinary_fixtures import culinary_source
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_postgres_culinary_bindings import bound
from test_postgres_culinary_bindings import request as propose_request
from test_postgres_foundation import db as db
from test_postgres_foundation import postgres_engine as postgres_engine
from test_variant_generation import owner, request, selected, source_with_binding

pytestmark = pytest.mark.postgres


def generated(db, case="single"):
    service, actor, g, r = bound(db)
    options = dict(serving_counts=[4]) if case == "tier" else {}
    if case == "single":
        options["ingredient_targets"] = [r.variant_rules[0].replacement_ingredient_id]
    result = generate_variants(request(r, **options))
    c = selected(result, (r.variant_rules[0].id,) if case == "single" else ())
    s = culinary_source(r)
    original = g.culinary_bindings[0]
    ownership = owner(s) | dict(
        household_id=g.household_id,
        plan_id=g.plan_id,
        proposal_id=original.proposal_id,
        batch_node_id=original.batch_node_id,
    )
    b = bind_generated_candidate(candidate=c, recipe=r, **ownership)
    batch = g.batches[0].model_copy(
        update=dict(
            tier_id=b.tier_id,
            planned_servings=b.planned_servings,
            culinary_signature=b.semantic_fingerprint(),
        )
    )
    g = type(g).model_validate(g.model_dump() | dict(culinary_bindings=(b,), batches=(batch,)))
    return service, actor, g, r


@pytest.mark.parametrize("case", ["default", "single", "tier"])
def test_generated_selection_persists_roundtrips_without_physical_stock_change(db, case):
    service, actor, g, r = generated(db, case)
    before = InventoryService(db).snapshot(g.household_id)
    p = service.propose(propose_request(service, actor, g))
    assert service.store.proposal(g.household_id, g.plan_id, p.id) == p
    after = InventoryService(db).snapshot(g.household_id)
    assert (before.lots, before.movements, before.reservations) == (
        after.lots,
        after.movements,
        after.reservations,
    )
    source = source_with_binding(culinary_source(r), g.culinary_bindings[0])
    # The generated proposal's exact household ownership is captured from persistence below.
    source = source.model_copy(update=dict(proposal=p))
    assert validate_recipe_grounding(source).culinary_checks_passed
    assert not validate_recipe_grounding(source).activation_authorized


@pytest.mark.parametrize("mutation", ["amount", "ingredient", "rule"])
def test_generated_path_does_not_bypass_direct_sql_seal_enforcement(db, monkeypatch, mutation):
    service, actor, g, r = generated(db)
    original = service.store.store_bindings

    def corrupt(graph):
        original(graph)
        # Test-owner only: malformed *unsealed* assembly; seal/FK/checks stay enabled.
        db.execute(
            text("ALTER TABLE culinary_requirement_bindings DISABLE TRIGGER culinary_immutable")
        )
        assignment = dict(
            amount="amount=amount+1", ingredient="ingredient_id=:bad", rule="selected_rule_id=:bad"
        )[mutation]
        db.execute(
            text(
                f"UPDATE culinary_requirement_bindings SET {assignment} "
                "WHERE proposal_id=:p AND requirement_id=:i"
            ),
            dict(p=g.culinary_bindings[0].proposal_id, i=r.ingredients[0].id, bad=uuid4()),
        )
        db.execute(
            text("ALTER TABLE culinary_requirement_bindings ENABLE TRIGGER culinary_immutable")
        )

    monkeypatch.setattr(service.store, "store_bindings", corrupt)
    with pytest.raises(IntegrityError):
        service.propose(propose_request(service, actor, g))


def test_generation_and_independent_validation_after_capture_make_zero_db_calls(postgres_engine):
    with Session(postgres_engine) as session:
        service, actor, g, r = generated(session)
        p = service.propose(propose_request(service, actor, g))
        session.commit()
    with postgres_engine.connect().execution_options(
        isolation_level="REPEATABLE READ",
        postgresql_readonly=True,
    ) as connection:
        with Session(connection) as session:
            captured = capture_culinary_input(
                session,
                household_id=g.household_id,
                plan_id=g.plan_id,
                proposal_id=p.id,
            )

    def forbidden(*a):
        raise AssertionError("Generator/validator accessed live database")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        result = generate_variants(request(captured.recipes[0]))
        assert result.status == "COMPLETE"
        assert validate_recipe_grounding(captured).culinary_checks_passed
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)
