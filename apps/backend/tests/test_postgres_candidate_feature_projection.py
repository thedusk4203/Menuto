"""CFP PostgreSQL cases use real owner publication and coherent candidate capture."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.domain.resolution import ResolutionError
from app.modules.catalog.public import (
    IngredientProteinService,
    add_affinity_feature_term,
    ingredient_protein_frontier,
)
from app.modules.households.models import Membership
from app.modules.identity.models import User
from app.modules.planning.contracts import CandidateFeatureProjectionRequest
from app.modules.planning.public import (
    capture_candidate_feature_projection_sources as capture_sources,
)
from app.modules.planning.public import (
    project_candidate_features as project,
)
from app.modules.planning.public import (
    validate_candidate_feature_projection as validate,
)
from app.modules.recipes.contracts import CulinaryFeaturePathKey, VariantGenerationRequest
from app.modules.recipes.public import (
    CulinaryFeatureService,
    authored_version,
    culinary_feature_frontier,
    generate_variants,
)
from feature_fixtures import review_command
from preference_fixtures import term
from sqlalchemy import event, inspect, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_postgres_candidate_grounding import read as read_grounding
from test_postgres_candidate_grounding import seed as seed_grounding
from test_postgres_culinary_features import catq, mainq, nextq
from test_postgres_foundation import postgres_engine as postgres_engine

pytestmark = pytest.mark.postgres


def prepared(
    engine,
    dimensions=("METHOD", "MAIN_PROTEIN", "FLAVOR"),
    *,
    empty=False,
    coverage="COMPLETE",
    positives=True,
):
    q, _ = seed_grounding(engine)
    grounded = read_grounding(engine, q)
    assert grounded.status == "GROUNDED"
    publications, vocabulary = {}, {}
    with Session(engine) as db:
        actor = db.scalar(
            select(Membership.user_id).where(Membership.household_id == q.household_id)
        )
        recipe = authored_version(db, q.candidate.recipe_version_id)
        if not empty:
            for dimension in dimensions:
                terms = tuple(
                    term("PROTEIN" if dimension == "MAIN_PROTEIN" else dimension) for _ in range(2)
                )
                vocabulary[dimension] = terms
                for t in terms:
                    add_affinity_feature_term(db, t)
                if dimension == "MAIN_PROTEIN":
                    cq = catq(db, recipe.ingredients[0].ingredient_id, terms)
                    cr = IngredientProteinService(db, actor_user_id=actor).write(cq)
                    publications["catalog"] = (cq, cr)
                    command = mainq(db, recipe, terms, cr)
                else:
                    command = review_command(
                        recipe,
                        terms,
                        dimension=dimension,
                        expected_recipe_frontier=culinary_feature_frontier(db),
                        coverage=coverage,
                        positive_term_ids=(terms[0].id,) if positives else (),
                    )
                receipt = CulinaryFeatureService(db, actor_user_id=actor).write(command)
                publications[dimension] = (command, receipt)
        db.commit()
    request = CandidateFeatureProjectionRequest(
        grounding_request=q,
        expected_grounding_fingerprint=grounded.candidate.fingerprint,
        requested_dimensions=dimensions,
    )
    return actor, request, publications, vocabulary


def capture(engine, actor, request, *, isolation="REPEATABLE READ", readonly=True):
    with (
        engine.connect().execution_options(
            isolation_level=isolation, postgresql_readonly=readonly
        ) as conn,
        Session(conn) as db,
    ):
        return capture_sources(db, request, actor_user_id=actor)


def expect(code, operation):
    with pytest.raises(ResolutionError) as exc:
        operation()
    assert exc.value.code == code
    return exc.value


def clear_method(engine, actor, publication):
    command, receipt = publication
    with Session(engine) as db:
        command = nextq(
            command, receipt, frontier=culinary_feature_frontier(db), positive_term_ids=()
        )
        CulinaryFeatureService(db, actor_user_id=actor).write(command)
        db.commit()


def test_cfp01_real_candidate_three_owner_dimensions_without_plan_or_batch(postgres_engine):
    actor, q, publications, _ = prepared(postgres_engine)
    source = capture(postgres_engine, actor, q)
    result = project(source)
    assert {d.dimension for d in result.dimensions} == {"METHOD", "MAIN_PROTEIN", "FLAVOR"}
    assert all(d.state == "ASSIGNED" for d in result.dimensions)
    assert {d.review_id for d in result.dimensions} == {
        publications[d][1].review_id for d in q.requested_dimensions
    }
    assert result.binding.grounding_fingerprint == q.expected_grounding_fingerprint
    assert not result.activation_ready and not result.planner_ready


def test_cfp02_real_method_capture_keeps_child_path_none_and_no_catalog_reads(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine, ("METHOD",))
    statements = []

    def observe(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(postgres_engine, "before_cursor_execute", observe)
    try:
        source = capture(postgres_engine, actor, q)
    finally:
        event.remove(postgres_engine, "before_cursor_execute", observe)
    assert source.feature_input.path is None and project(source).binding.path.deltas
    assert not any("ingredient_protein_" in s for s in statements)
    assert "catalog_frontier" not in source.feature_input.sources.model_dump()


def test_cfp03_real_main_protein_support_is_pinned_to_owner_publication(postgres_engine):
    actor, q, pubs, _ = prepared(postgres_engine, ("MAIN_PROTEIN",))
    source = capture(postgres_engine, actor, q)
    support = source.feature_input.sources.scopes[0].reviews[-1].command.supports[0]
    assert support.catalog_review_id == pubs["catalog"][1].review_id
    assert project(source).dimensions[0].review_id == pubs["MAIN_PROTEIN"][1].review_id
    assert source.feature_input.path == project(source).binding.path


def test_cfp04_real_flavor_uses_exact_authored_path(postgres_engine):
    actor, q, pubs, terms = prepared(postgres_engine, ("FLAVOR",))
    source = capture(postgres_engine, actor, q)
    row = project(source).dimensions[0]
    assert row.applicability_id == pubs["FLAVOR"][1].applicability_id
    assert row.positive_term_ids == (terms["FLAVOR"][0].id,)


def test_cfp05_another_recipe_version_does_not_inherit_review_by_title(postgres_engine):
    prepared(postgres_engine, ("METHOD",))
    actor, q, _, _ = prepared(postgres_engine, ("METHOD",), empty=True)
    source = capture(postgres_engine, actor, q)
    assert source.feature_input.recipe.id == q.grounding_request.candidate.recipe_version_id
    assert project(source).dimensions[0].reason == "NO_SOURCE"


def test_cfp06_real_alternate_tier_has_no_implicit_scope_fallback(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine, ("FLAVOR",))
    source = capture(postgres_engine, actor, q)
    recipe = source.grounded_candidate.sources.recipe
    candidate = generate_variants(
        VariantGenerationRequest(
            recipe=recipe,
            demand=dict(serving_counts=(recipe.portion_tiers[1].servings,)),
            limits=dict(max_attempts=20, max_candidates=20),
        )
    ).candidates[-1]
    assert candidate.tier_id != q.grounding_request.candidate.tier_id
    grounding = q.grounding_request.model_copy(update=dict(candidate=candidate))
    fresh = read_grounding(postgres_engine, grounding)
    q = q.model_copy(
        update=dict(
            grounding_request=grounding, expected_grounding_fingerprint=fresh.candidate.fingerprint
        )
    )
    projected = project(capture(postgres_engine, actor, q))
    assert projected.dimensions[0].reason == "NO_MATCHING_SCOPE"
    assert projected.binding.path.tier_id == candidate.tier_id


def test_cfp07_real_transformation_context_is_bound_to_selected_ingredient(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine, ("FLAVOR",))
    source = capture(postgres_engine, actor, q)
    slot = source.feature_input.sources.scopes[0].key.slots[0]
    transformation = source.grounded_candidate.request.candidate.transformations[0]
    assert slot.preparation == "TRANSFORMATION" and slot.transformation_id == transformation.id
    assert project(source).dimensions[0].state == "ASSIGNED"


def test_cfp14_missing_canonical_recipe_cannot_be_overridden(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine, ("METHOD",))
    candidate = q.grounding_request.candidate.model_copy(update=dict(recipe_version_id=uuid4()))
    candidate = candidate.model_copy(update=dict(fingerprint=candidate.expected_fingerprint()))
    q = q.model_copy(
        update=dict(
            grounding_request=q.grounding_request.model_copy(update=dict(candidate=candidate))
        )
    )
    error = expect("CANONICAL_SOURCE_UNAVAILABLE", lambda: capture(postgres_engine, actor, q))
    assert not error.rejected


def test_cfp15_missing_selected_nutrition_is_incomplete_not_empty_features(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine, ("METHOD",))
    request = q.grounding_request.model_copy(
        update=dict(
            nutrition_selections=(
                dict(
                    requirement_id=q.grounding_request.candidate.resolved_ingredients[
                        0
                    ].requirement_id,
                    reference_id=uuid4(),
                ),
            )
        )
    )
    error = expect(
        "GROUNDING_INCOMPLETE",
        lambda: capture(
            postgres_engine, actor, q.model_copy(update=dict(grounding_request=request))
        ),
    )
    assert "NUTRITION" in error.detail and not error.rejected


def test_cfp16_forged_culinary_quantity_is_rejected_against_real_owner_source(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine, ("METHOD",))
    c = q.grounding_request.candidate
    c = c.model_copy(update=dict(serving_count=c.serving_count + 1))
    c = c.model_copy(update=dict(fingerprint=c.expected_fingerprint()))
    request = q.grounding_request.model_copy(update=dict(candidate=c))
    assert expect(
        "GROUNDING_REJECTED",
        lambda: capture(
            postgres_engine, actor, q.model_copy(update=dict(grounding_request=request))
        ),
    ).rejected


def test_cfp17_expected_pin_prevents_silent_fresh_candidate_substitution(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine, ("METHOD",))
    q = q.model_copy(update=dict(expected_grounding_fingerprint="f" * 64))
    expect("EXPECTED_GROUNDING_MISMATCH", lambda: capture(postgres_engine, actor, q))


def test_cfp20_household_membership_is_required_for_canonical_read(postgres_engine):
    _, q, _, _ = prepared(postgres_engine, ("METHOD",))
    expect("CAPTURE_ACCESS_DENIED", lambda: capture(postgres_engine, uuid4(), q))


def test_cfp28_owner_rejects_invalid_support_and_canonical_capture_remains_valid(postgres_engine):
    actor, q, pubs, _ = prepared(postgres_engine, ("MAIN_PROTEIN",))
    command, receipt = pubs["MAIN_PROTEIN"]
    with Session(postgres_engine) as db:
        bad = nextq(
            command,
            receipt,
            frontier=culinary_feature_frontier(db),
            expected_catalog_frontier=ingredient_protein_frontier(db),
            supports=(command.supports[0].model_copy(update=dict(ingredient_id=uuid4())),),
        )
        with pytest.raises((ValueError, DBAPIError)), db.begin_nested():
            CulinaryFeatureService(db, actor_user_id=actor).write(bad)
    assert project(capture(postgres_engine, actor, q)).dimensions[0].review_id == receipt.review_id


def test_cfp29_owner_overlap_guard_is_preserved_at_real_publication(postgres_engine):
    actor, q, pubs, terms = prepared(postgres_engine, ("FLAVOR",))
    command, _ = pubs["FLAVOR"]
    with Session(postgres_engine) as db:
        recipe = authored_version(db, q.grounding_request.candidate.recipe_version_id)
        key = CulinaryFeaturePathKey.model_validate(
            command.key.model_dump()
            | dict(scope="REVIEWED_SCOPE", tier_ids=tuple(t.id for t in recipe.portion_tiers))
        )
        bad = review_command(
            recipe,
            terms["FLAVOR"],
            dimension="FLAVOR",
            key=key,
            expected_recipe_frontier=culinary_feature_frontier(db),
        )
        with pytest.raises((ValueError, DBAPIError)), db.begin_nested():
            CulinaryFeatureService(db, actor_user_id=actor).write(bad)
    assert project(capture(postgres_engine, actor, q)).dimensions[0].state == "ASSIGNED"


def test_cfp30_catalog_correction_retains_history_and_stales_old_support(postgres_engine):
    actor, q, pubs, _ = prepared(postgres_engine, ("MAIN_PROTEIN",))
    before = capture(postgres_engine, actor, q)
    command, receipt = pubs["catalog"]
    with Session(postgres_engine) as db:
        newer = nextq(
            command, receipt, frontier=ingredient_protein_frontier(db), positive_term_ids=()
        )
        IngredientProteinService(db, actor_user_id=actor).write(newer)
        db.commit()
    after = capture(postgres_engine, actor, q)
    assert len(after.feature_input.sources.catalog_streams[0].reviews) == 2
    assert project(after).dimensions[0].reason == "STALE_ASSOCIATION"
    assert project(before).dimensions[0].state == "ASSIGNED"


def test_cfp31_successful_empty_owner_read_is_explicit_no_source(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine, empty=True)
    result = project(capture(postgres_engine, actor, q))
    assert all(d.state == "UNRESOLVED" and d.reason == "NO_SOURCE" for d in result.dimensions)


def test_cfp33_complete_review_with_no_positive_is_finite_reviewed_none(postgres_engine):
    actor, q, _, terms = prepared(postgres_engine, ("METHOD",), positives=False)
    row = project(capture(postgres_engine, actor, q)).dimensions[0]
    assert row.state == "REVIEWED_NONE" and set(row.covered_term_ids) == {
        t.id for t in terms["METHOD"]
    }


def test_cfp36_real_retraction_preserves_history_and_missingness(postgres_engine):
    actor, q, pubs, _ = prepared(postgres_engine, ("METHOD",))
    command, receipt = pubs["METHOD"]
    with Session(postgres_engine) as db:
        CulinaryFeatureService(db, actor_user_id=actor).write(
            nextq(command, receipt, frontier=culinary_feature_frontier(db), action="RETRACT")
        )
        db.commit()
    source = capture(postgres_engine, actor, q)
    assert len(source.feature_input.sources.scopes[0].reviews) == 2
    assert project(source).dimensions[0].reason == "RETRACTED"


def test_cfp37_real_source_read_failure_aborts_all_dimensions(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine)

    def fail(conn, cursor, statement, parameters, context, executemany):
        if (
            statement.lstrip().startswith("SELECT")
            and "culinary_feature_applicabilities" in statement
        ):
            return "SELECT 1/0", {}
        return statement, parameters

    event.listen(postgres_engine, "before_cursor_execute", fail, retval=True)
    try:
        error = expect("CAPTURE_IO_FAILURE", lambda: capture(postgres_engine, actor, q))
        assert not error.rejected and isinstance(error.__cause__, DBAPIError)
    finally:
        event.remove(postgres_engine, "before_cursor_execute", fail)


@pytest.mark.parametrize("case", ["writable", "read_committed", "new", "dirty", "deleted"])
def test_cfp38_invalid_capture_transaction_has_no_write_or_commit(postgres_engine, case):
    actor, q, _, _ = prepared(postgres_engine, ("METHOD",))
    if case in {"writable", "read_committed"}:
        expect(
            "CAPTURE_CONTEXT_INVALID",
            lambda: capture(
                postgres_engine,
                actor,
                q,
                readonly=case != "writable",
                isolation="READ COMMITTED" if case == "read_committed" else "REPEATABLE READ",
            ),
        )
        return
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as db,
    ):
        if case == "new":
            db.add(User(display_name="Unflushed test object"))
        elif case == "dirty":
            db.get(User, actor).display_name = "Unflushed edit"
        else:
            db.delete(db.get(User, actor))
        expect("CAPTURE_CONTEXT_INVALID", lambda: capture_sources(db, q, actor_user_id=actor))


def test_cfp38_clean_serializable_readonly_capture_is_supported(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine, ("METHOD",))
    assert project(capture(postgres_engine, actor, q, isolation="SERIALIZABLE")).status == "DERIVED"


def test_cfp39_concurrent_publication_cannot_splice_live_heads_into_mvcc_cut(postgres_engine):
    actor, q, pubs, _ = prepared(postgres_engine, ("METHOD",))
    fired = []
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as db,
    ):

        def publish(connection, cursor, statement, *args):
            if (
                not fired
                and statement.lstrip().startswith("SELECT")
                and "culinary_feature_applicabilities" in statement
            ):
                fired.append(True)
                clear_method(postgres_engine, actor, pubs["METHOD"])

        event.listen(conn, "before_cursor_execute", publish)
        source = capture_sources(db, q, actor_user_id=actor)
    assert fired and project(source).dimensions[0].state == "ASSIGNED"
    fresh = capture(postgres_engine, actor, q)
    assert project(fresh).dimensions[0].state == "REVIEWED_NONE"
    assert (
        fresh.feature_input.sources.recipe_frontier > source.feature_input.sources.recipe_frontier
    )


def test_cfp40_real_independent_clocks_and_counters_are_not_collapsed(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine)
    source = capture(postgres_engine, actor, q)
    assert q.grounding_request.as_of < source.feature_input.captured_at
    assert (
        source.capture_started_at <= source.feature_input.captured_at <= source.capture_completed_at
    )
    assert (
        source.feature_input.sources.recipe_frontier
        != source.feature_input.sources.catalog_frontier
    )


def test_cfp41_review_published_after_grounding_as_of_remains_visible_at_capture(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine, ("METHOD",))
    source = capture(postgres_engine, actor, q)
    assert q.grounding_request.as_of < source.feature_input.sources.scopes[0].reviews[0].recorded_at
    assert project(source).dimensions[0].state == "ASSIGNED"


def test_cfp42_canonical_ingress_preserves_inventory_future_cutoff_rejection(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine, ("METHOD",))
    grounding = q.grounding_request.model_copy(
        update=dict(as_of=datetime.now(UTC) + timedelta(days=1))
    )
    expect(
        "INVALID_REQUEST",
        lambda: capture(
            postgres_engine, actor, q.model_copy(update=dict(grounding_request=grounding))
        ),
    )


def test_cfp44_old_cut_remains_replayable_after_live_publication_changes(postgres_engine):
    actor, q, pubs, _ = prepared(postgres_engine, ("METHOD",))
    before = capture(postgres_engine, actor, q)
    result = project(before)
    clear_method(postgres_engine, actor, pubs["METHOD"])
    assert validate(result) == result
    assert project(capture(postgres_engine, actor, q)).dimensions[0].state == "REVIEWED_NONE"


def test_cfp60_capture_preserves_schema_owner_rows_and_migration_head(postgres_engine):
    actor, q, _, _ = prepared(postgres_engine)
    tables = inspect(postgres_engine).get_table_names()
    assert len(tables) == 109
    watched = [
        "culinary_feature_reviews",
        "ingredient_protein_reviews",
        "inventory_movements",
        "plan_proposals",
    ]

    def counts():
        with postgres_engine.connect() as conn:
            return {name: conn.scalar(text(f'SELECT count(*) FROM "{name}"')) for name in watched}

    before = counts()
    statements = []

    def observe(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(postgres_engine, "before_cursor_execute", observe)
    try:
        source = capture(postgres_engine, actor, q)
    finally:
        event.remove(postgres_engine, "before_cursor_execute", observe)
    assert (
        before == counts()
        and source.grounded_candidate.fingerprint == q.expected_grounding_fingerprint
    )
    assert all(s.lstrip().split()[0].upper() in {"SHOW", "SELECT"} for s in statements)
    with postgres_engine.connect() as conn:
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
