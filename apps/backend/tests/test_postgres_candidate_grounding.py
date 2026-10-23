"""Read-only canonical capture on real PostgreSQL; no mocked source authority."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from app.modules.catalog.models import NutritionFact
from app.modules.inventory.public import InventoryService
from app.modules.planning.contracts import CandidateGroundingRequest
from app.modules.planning.grounding import resolve_captured_candidate
from app.modules.planning.grounding_capture import capture_candidate_sources
from app.modules.planning.public import ground_candidate
from app.modules.recipes.contracts import VariantGenerationRequest
from app.modules.recipes.public import generate_variants
from app.modules.retail.repository import RetailEvidenceRepository
from grounding_fixtures import retail_for
from inventory_fixtures import acquire
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_foundation import seed_household
from test_postgres_recipes import seed as seed_recipe
from validation_fixtures import simple_recipe_data

pytestmark = pytest.mark.postgres


def seed(engine, granularity="FIXED_PACK", physical=True):
    with Session(engine) as db:
        user, house = seed_household(db)
        recipe, _ = seed_recipe(db, simple_recipe_data())
        ingredient = recipe.ingredients[0].ingredient_id
        f = retail_for(ingredient, granularity)
        f["cls"] = f["cls"].model_copy(update=dict(code="grounding-" + uuid4().hex))
        f["book"] = f["book"].model_copy(update=dict(code="grounding-book-" + uuid4().hex))
        f["reference"] = f["reference"].model_copy(update=dict(book=f["book"]))
        repo = RetailEvidenceRepository(db)
        for key in (
            "retailer",
            "retailer_status",
            "region",
            "product",
            "package",
            "mapping",
            "observation",
            "cls",
            "member",
            "calibration",
            "book",
            "reference",
            "quote",
            "option",
        ):
            repo.add(f[key])
        ref = NutritionFact(
            ingredient_id=ingredient,
            basis="EP_RAW_G",
            reference_amount=100,
            energy_kcal=200,
            protein_g=20,
            fat_g=5,
            carbohydrate_g=10,
            status="REVIEWED",
            source_kind="REVIEWED_REFERENCE",
            source_system="synthetic.grounding",
            external_record_id=str(uuid4()),
            source_version="1",
            observed_at=f["quote"].as_of,
        )
        db.add(ref)
        db.flush()
        ref_id = ref.id
        if physical:
            InventoryService(db).acquire(acquire(house.household_id, user.id, ingredient))
        db.commit()
        candidate = generate_variants(
            VariantGenerationRequest(
                recipe=recipe, demand={}, limits=dict(max_attempts=1, max_candidates=1)
            )
        ).candidates[0]
        q = CandidateGroundingRequest(
            candidate=candidate,
            household_id=house.household_id,
            tracked_member_id=house.member_id,
            participants=dict(
                participants=[
                    dict(member_id=house.member_id, portion_factor="1", nutrition_role="TRACKED")
                ]
            ),
            region_code=f["region"].region_code,
            currency="VND",
            as_of=datetime.now(UTC),
            procurement_class_ids=(f["cls"].id,),
        )
        return q, ref_id


def read(engine, q, *, sources=False):
    with engine.connect().execution_options(
        isolation_level="REPEATABLE READ", postgresql_readonly=True
    ) as conn:
        with Session(conn) as db:
            return capture_candidate_sources(db, q) if sources else ground_candidate(db, q)


@pytest.mark.parametrize("granularity", ["FIXED_PACK", "CATCH_WEIGHT", "LOOSE_SCALE"])
def test_real_source_capture_grounding_and_no_material_or_reservation_mutation(
    postgres_engine, granularity
):
    q, ref_id = seed(postgres_engine, granularity)
    before = read(postgres_engine, q, sources=True)
    result = read(postgres_engine, q)
    after = read(postgres_engine, q, sources=True)
    assert result.status == "GROUNDED" and not result.activation_ready
    c = result.candidate
    assert c.ingredient_facts[0].nutrition.reference.id == ref_id
    assert c.input_nutrition.protein_g == 40
    assert c.sources.inventory == before.inventory == after.inventory
    assert c.sources.inventory.movements and c.sources.inventory.reservations == ()
    assert (
        c.ingredient_facts[0].procurement_paths[0].option.quote.package.granularity == granularity
    )


def test_public_capture_rejects_non_readonly_transaction(postgres_engine):
    q, _ = seed(postgres_engine)
    with Session(postgres_engine) as db, pytest.raises(ValueError, match="read-only"):
        ground_candidate(db, q)


@pytest.mark.parametrize("forged", ["quantity", "reference", "foreign_member"])
def test_public_grounding_uses_canonical_sources_not_caller_claims(postgres_engine, forged):
    q, _ = seed(postgres_engine)
    if forged == "quantity":
        c = q.candidate
        row = c.resolved_ingredients[0]
        row = row.model_copy(
            update=dict(quantity=row.quantity.model_copy(update=dict(amount=Decimal(999))))
        )
        c = c.model_copy(update=dict(resolved_ingredients=(row,)))
        c = c.model_copy(update=dict(fingerprint=c.expected_fingerprint()))
        q = q.model_copy(update=dict(candidate=c))
    elif forged == "reference":
        q = CandidateGroundingRequest.model_validate(
            q.model_dump()
            | dict(
                nutrition_selections=[
                    dict(
                        requirement_id=q.candidate.resolved_ingredients[0].requirement_id,
                        reference_id=uuid4(),
                    )
                ]
            )
        )
    else:
        q = q.model_copy(update=dict(tracked_member_id=uuid4()))
    out = read(postgres_engine, q)
    assert out.candidate is None and out.status == (
        "INCOMPLETE" if forged == "reference" else "REJECTED"
    )


def test_missing_procurement_is_not_inferred_as_stock_or_zero_cost(postgres_engine):
    q, _ = seed(postgres_engine, physical=False)
    q = q.model_copy(update=dict(procurement_class_ids=()))
    out = read(postgres_engine, q)
    assert out.status == "INCOMPLETE" and out.issues[0].code == "MATERIAL_SOURCE_UNRESOLVED"


def test_captured_resolution_performs_no_queries_or_writes(postgres_engine):
    q, _ = seed(postgres_engine)
    sources = read(postgres_engine, q, sources=True)

    def forbidden(*a):
        raise AssertionError("Live DB read/write inside captured resolution")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        out = resolve_captured_candidate(q, sources)
        assert out.status == "GROUNDED"
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)


def test_repeatable_read_capture_stable_but_new_source_changes_identity(postgres_engine):
    q, ref_id = seed(postgres_engine)
    with postgres_engine.connect().execution_options(
        isolation_level="REPEATABLE READ", postgresql_readonly=True
    ) as conn:
        with Session(conn) as db:
            before = capture_candidate_sources(db, q)
            with Session(postgres_engine) as writer:
                old = writer.get(NutritionFact, ref_id)
                fields = {
                    c.name: getattr(old, c.name)
                    for c in old.__table__.columns
                    if c.name not in {"id", "created_at"}
                }
                added = NutritionFact(**(fields | dict(protein_g=21, source_version="2")))
                writer.add(added)
                writer.flush()
                new_ref_id = added.id
                writer.commit()
            repeated = capture_candidate_sources(db, q)
    fresh = read(postgres_engine, q, sources=True)
    a = resolve_captured_candidate(q, before).candidate
    assert resolve_captured_candidate(q, fresh).status == "INCOMPLETE"
    selected_request = CandidateGroundingRequest.model_validate(
        q.model_dump()
        | dict(
            nutrition_selections=[
                dict(
                    requirement_id=q.candidate.resolved_ingredients[0].requirement_id,
                    reference_id=new_ref_id,
                )
            ]
        )
    )
    b = resolve_captured_candidate(selected_request, fresh).candidate
    assert before.fingerprint() == repeated.fingerprint()
    assert a.input_nutrition.protein_g == 40 and b.input_nutrition.protein_g == 42
    assert a.fingerprint != b.fingerprint
    assert not a.activation_ready and not b.activation_ready


@pytest.mark.parametrize("mutation", ["negative_nutrition", "immutable_quote"])
def test_direct_sql_cannot_bypass_existing_source_constraints(postgres_engine, mutation):
    q, ref_id = seed(postgres_engine)
    with Session(postgres_engine) as db:
        with pytest.raises(IntegrityError), db.begin_nested():
            if mutation == "negative_nutrition":
                db.execute(
                    text("""INSERT INTO nutrition_facts
                        (id,ingredient_id,basis,reference_amount,energy_kcal,protein_g,fat_g,
                         carbohydrate_g,status,source_kind,source_system,external_record_id,
                         source_version,observed_at)
                        SELECT :new_id,ingredient_id,basis,reference_amount,energy_kcal,-1,fat_g,
                         carbohydrate_g,status,source_kind,source_system,:record,'invalid',observed_at
                        FROM nutrition_facts WHERE id=:id"""),
                    dict(id=ref_id, new_id=uuid4(), record=str(uuid4())),
                )
            else:
                db.execute(
                    text(
                        "UPDATE planning_price_quotes SET reference_amount_minor=1 "
                        "WHERE procurement_class_id=:id"
                    ),
                    dict(id=q.procurement_class_ids[0]),
                )
