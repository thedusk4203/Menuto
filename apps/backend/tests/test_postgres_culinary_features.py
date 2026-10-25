"""Real PostgreSQL source closure, causality, parity, fences and capture."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from app.modules.catalog import contracts as cat
from app.modules.catalog import feature_models as cm
from app.modules.catalog.public import (
    IngredientProteinService,
    add_affinity_feature_term,
    ingredient_protein_frontier,
    ingredient_protein_sources,
)
from app.modules.identity.models import User
from app.modules.planning import contracts as pc
from app.modules.planning.public import (
    capture_culinary_feature_subject,
    discover_culinary_feature_assignments,
    resolve_feature_terms,
)
from app.modules.recipes import contracts as rc
from app.modules.recipes import feature_models as rm
from app.modules.recipes.public import (
    CulinaryFeatureService,
    culinary_feature_frontier,
    culinary_feature_sources,
)
from feature_fixtures import review_command
from preference_fixtures import provenance, term
from sqlalchemy import event, insert, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_foundation_migration import legacy_database as legacy_database
from test_foundation_migration import migrate
from test_postgres_culinary_bindings import bound
from test_postgres_culinary_bindings import request as plan_request
from test_postgres_foundation import db as db
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_recipes import seed as seed_recipe

pytestmark = pytest.mark.postgres


def seed(db, kind="METHOD"):
    recipe, _ = seed_recipe(db)
    actor = User(display_name="Synthetic trusted curator")
    db.add(actor)
    db.flush()
    terms = (term(kind), term(kind))
    for t in terms:
        add_affinity_feature_term(db, t)
    return recipe, actor.id, terms


def catq(db, ingredient, terms, **changes):
    return cat.IngredientProteinReviewCommand(
        **(
            dict(
                command_kind="REPLACE",
                ingredient_id=ingredient,
                expected_revision_no=-1,
                predecessor_id=None,
                expected_catalog_frontier=ingredient_protein_frontier(db),
                coverage="COMPLETE",
                covered_term_ids=tuple(t.id for t in terms),
                positive_term_ids=(terms[0].id,),
                provenance=provenance().model_dump(),
                correction_reason=None,
                idempotency_key=uuid4().hex,
            )
            | changes
        )
    )


def nextq(q, receipt, *, frontier, action="REPLACE", **changes):
    data = q.model_dump() | dict(
        command_kind=action,
        expected_revision_no=0,
        predecessor_id=receipt.review_id,
        correction_reason="Explicit correction",
        idempotency_key=uuid4().hex,
        provenance=provenance().model_dump(),
    )
    if isinstance(q, cat.IngredientProteinReviewCommand):
        data["contract_version"] = (
            "ingredient-protein-retract.v1"
            if action == "RETRACT"
            else "ingredient-protein-write.v1"
        )
        data["expected_catalog_frontier"] = frontier
    else:
        data["contract_version"] = (
            "culinary-feature-retract.v1" if action == "RETRACT" else "culinary-feature-write.v1"
        )
        data |= dict(
            expected_recipe_frontier=frontier, applicability_id=receipt.applicability_id, key=None
        )
    if action == "RETRACT":
        data |= dict(coverage=None, covered_term_ids=(), positive_term_ids=())
    return type(q).model_validate(data | changes)


def force_complete(db):
    db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    db.execute(text("SET CONSTRAINTS ALL DEFERRED"))


@pytest.mark.parametrize("dimension", ["METHOD", "FLAVOR"])
def test_sql_python_key_command_hash_and_provenance_roundtrip(db, dimension):
    recipe, actor, terms = seed(db, dimension)
    q = review_command(
        recipe,
        terms,
        dimension=dimension,
        expected_recipe_frontier=culinary_feature_frontier(db),
        provenance=provenance(
            external_record_id="curated.日本語.độ", source_version="release.α"
        ).model_dump(),
    )
    svc = CulinaryFeatureService(db, actor_user_id=actor)
    a = svc.write(q)
    force_complete(db)
    scopes = culinary_feature_sources(db, recipe.id, (dimension,))
    assert scopes[0].reviews[0].command == q
    assert scopes[0].reviews[0].command_hash == q.fingerprint(actor) == a.command_hash
    assert (
        db.scalar(text("SELECT menuto_feature_key_hash(:a)"), {"a": a.applicability_id})
        == q.key.fingerprint()
    )
    assert svc.write(q).replayed
    bq = nextq(q, a, frontier=culinary_feature_frontier(db), positive_term_ids=())
    b = svc.write(bq)
    rq = type(q).model_validate(
        bq.model_dump()
        | dict(
            contract_version="culinary-feature-retract.v1",
            command_kind="RETRACT",
            expected_revision_no=1,
            predecessor_id=b.review_id,
            expected_recipe_frontier=culinary_feature_frontier(db),
            coverage=None,
            covered_term_ids=(),
            positive_term_ids=(),
            idempotency_key=uuid4().hex,
            provenance=provenance().model_dump(),
        )
    )
    svc.write(rq)
    force_complete(db)
    assert svc.write(q).review_id == a.review_id
    assert len(culinary_feature_sources(db, recipe.id, (dimension,))[0].reviews) == 3
    with pytest.raises(ValueError, match="IDEMPOTENCY_CONFLICT"):
        svc.write(q.model_copy(update={"positive_term_ids": ()}))


def test_catalog_full_history_retract_retry_and_provider_identity(db):
    recipe, actor, terms = seed(db, "PROTEIN")
    svc = IngredientProteinService(db, actor_user_id=actor)
    q = catq(db, recipe.ingredients[0].ingredient_id, terms)
    a = svc.write(q)
    force_complete(db)
    bq = nextq(q, a, frontier=ingredient_protein_frontier(db), positive_term_ids=())
    b = svc.write(bq)
    rq = cat.IngredientProteinReviewCommand.model_validate(
        bq.model_dump()
        | dict(
            contract_version="ingredient-protein-retract.v1",
            command_kind="RETRACT",
            expected_revision_no=1,
            predecessor_id=b.review_id,
            expected_catalog_frontier=ingredient_protein_frontier(db),
            coverage=None,
            covered_term_ids=(),
            positive_term_ids=(),
            idempotency_key=uuid4().hex,
            provenance=provenance().model_dump(),
        )
    )
    svc.write(rq)
    force_complete(db)
    history = ingredient_protein_sources(db, (q.ingredient_id,))[0]
    assert len(history.reviews) == 3 and history.reviews[0].command == q
    assert svc.write(q).replayed
    # Different source provider with the same external record is a distinct source identity.
    other = catq(
        db,
        recipe.ingredients[1].ingredient_id,
        terms,
        provenance=provenance(
            source_system="provider.B", external_record_id=q.provenance.external_record_id
        ).model_dump(),
    )
    svc.write(other)
    force_complete(db)
    bad = catq(db, recipe.ingredients[2].ingredient_id, terms, provenance=q.provenance.model_dump())
    with pytest.raises(DBAPIError), db.begin_nested():
        svc.write(bad)


@pytest.mark.parametrize(
    "table",
    [
        "ingredient_protein_frontier",
        "ingredient_protein_streams",
        "ingredient_protein_reviews",
        "ingredient_protein_review_terms",
        "ingredient_protein_assignments",
        "culinary_feature_frontier",
        "culinary_feature_applicabilities",
        "culinary_feature_applicability_slots",
        "culinary_feature_applicability_tiers",
        "culinary_feature_reviews",
        "culinary_feature_review_terms",
        "culinary_feature_assignments",
        "culinary_feature_main_protein_support",
    ],
)
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE"])
def test_direct_sql_no_mutation_even_empty_tables(db, table, operation):
    # Statement/row triggers require existing rows for UPDATE/DELETE; create relevant families.
    recipe, actor, terms = seed(db, "PROTEIN")
    cr = IngredientProteinService(db, actor_user_id=actor).write(
        catq(db, recipe.ingredients[0].ingredient_id, terms)
    )
    q = mainq(db, recipe, terms, cr)
    CulinaryFeatureService(db, actor_user_id=actor).write(q)
    force_complete(db)
    statement = f"{operation} {table}"
    if operation == "UPDATE":
        model_table = next(t for t in rm.Base.metadata.tables.values() if t.name == table)
        col = next(iter(model_table.columns)).name
        statement = f"UPDATE {table} SET {col}={col}"
    elif operation == "DELETE":
        statement = f"DELETE FROM {table}"
    with pytest.raises(DBAPIError), db.begin_nested():
        db.execute(text(statement))


def mainq(db, recipe, terms, receipt, **changes):
    return review_command(
        recipe,
        terms,
        dimension="MAIN_PROTEIN",
        expected_recipe_frontier=culinary_feature_frontier(db),
        expected_catalog_frontier=ingredient_protein_frontier(db),
        supports=(
            dict(
                term_id=terms[0].id,
                requirement_id=recipe.ingredients[0].id,
                ingredient_id=recipe.ingredients[0].ingredient_id,
                catalog_review_id=receipt.review_id,
            ),
        ),
        **changes,
    )


def test_main_support_current_pinned_and_minimum_envelope(db):
    recipe, actor, terms = seed(db, "PROTEIN")
    cs = IngredientProteinService(db, actor_user_id=actor)
    cq = catq(db, recipe.ingredients[0].ingredient_id, terms)
    cr = cs.write(cq)
    q = mainq(db, recipe, terms, cr)
    rr = CulinaryFeatureService(db, actor_user_id=actor).write(q)
    force_complete(db)
    assert rr.dimension == "MAIN_PROTEIN"
    newer = cs.write(nextq(cq, cr, frontier=ingredient_protein_frontier(db)))
    # Old immutable review persists; publication must pin the new current Catalog review.
    replace = nextq(
        q,
        rr,
        frontier=culinary_feature_frontier(db),
        expected_catalog_frontier=ingredient_protein_frontier(db),
    )
    with pytest.raises(DBAPIError, match="Stale/invalid"), db.begin_nested():
        CulinaryFeatureService(db, actor_user_id=actor).write(replace)
    fixed = replace.model_copy(
        update={
            "supports": (
                rc.MainProteinSupport(
                    **q.supports[0].model_dump() | dict(catalog_review_id=newer.review_id)
                ),
            )
        }
    )
    CulinaryFeatureService(db, actor_user_id=actor).write(fixed)
    force_complete(db)


@pytest.mark.parametrize(
    "mutation",
    [
        "method_children",
        "wrong_hash",
        "missing_children",
        "late_term",
        "declared_count",
        "audit_xid",
        "cross_recipe_slot",
        "wrong_term_kind",
        "unreviewed_term",
        "wrong_catalog_audit",
    ],
)
def test_direct_sql_assembly_adversarial_cases(db, mutation):
    recipe, actor, terms = seed(db, "METHOD")
    q = review_command(recipe, terms, expected_recipe_frontier=culinary_feature_frontier(db))

    if mutation == "audit_xid":
        with pytest.raises(DBAPIError, match="Database-owned registry"), db.begin_nested():
            db.execute(
                insert(rm.CulinaryFeatureApplicability).values(
                    id=uuid4(),
                    recipe_version_id=recipe.id,
                    dimension="METHOD",
                    scope="RECIPE_COOKING_CONTEXT",
                    key_hash=q.key.fingerprint(),
                    declared_tier_count=0,
                    assembly_xid="0",
                )
            )
        return

    # Intercept actual SQL binds to bypass only producer checks; DB remains subject under test.
    def tamper(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO culinary_feature_applicabilities"):
            if mutation == "wrong_hash":
                parameters["key_hash"] = "0" * 64
            if mutation == "audit_xid":
                parameters["assembly_xid"] = "0"
        if statement.startswith("INSERT INTO culinary_feature_reviews"):
            if mutation == "declared_count":
                parameters["declared_covered_count"] = 3
            if mutation == "wrong_catalog_audit":
                parameters["catalog_frontier_at_write"] = 0
        return statement, parameters

    event.listen(db.bind, "before_cursor_execute", tamper, retval=True)
    try:
        if mutation in {"wrong_hash", "declared_count", "audit_xid", "wrong_catalog_audit"}:
            with pytest.raises(DBAPIError), db.begin_nested():
                CulinaryFeatureService(db, actor_user_id=actor).write(q)
                force_complete(db)
            return
    finally:
        event.remove(db.bind, "before_cursor_execute", tamper)
    if mutation == "unreviewed_term":
        draft = term("METHOD", status="DRAFT")
        add_affinity_feature_term(db, draft)
        bad = review_command(
            recipe, (draft,), expected_recipe_frontier=culinary_feature_frontier(db)
        )
        with pytest.raises(DBAPIError), db.begin_nested():
            CulinaryFeatureService(db, actor_user_id=actor).write(bad)
        return
    if mutation == "wrong_term_kind":
        badterm = term("FLAVOR")
        add_affinity_feature_term(db, badterm)
        bad = review_command(
            recipe, (badterm,), expected_recipe_frontier=culinary_feature_frontier(db)
        )
        with pytest.raises(DBAPIError), db.begin_nested():
            CulinaryFeatureService(db, actor_user_id=actor).write(bad)
        return
    if mutation == "missing_children":
        with pytest.raises(DBAPIError), db.begin_nested():
            db.execute(
                insert(cm.IngredientProteinStream).values(
                    id=uuid4(), ingredient_id=recipe.ingredients[0].ingredient_id
                )
            )
            force_complete(db)
        return
    a = CulinaryFeatureService(db, actor_user_id=actor).write(q)
    force_complete(db)
    with pytest.raises(DBAPIError), db.begin_nested():
        if mutation in {"method_children", "cross_recipe_slot"}:
            db.execute(
                insert(rm.CulinaryFeatureApplicabilityTier).values(
                    applicability_id=a.applicability_id,
                    recipe_version_id=recipe.id,
                    tier_id=recipe.portion_tiers[0].id,
                )
            )
        else:
            db.execute(
                insert(rm.CulinaryFeatureReviewTerm).values(
                    review_id=a.review_id,
                    applicability_id=a.applicability_id,
                    recipe_version_id=recipe.id,
                    dimension="METHOD",
                    term_id=uuid4(),
                    term_kind="METHOD",
                )
            )


def test_empty_scope_cannot_commit_and_hash_cannot_be_cached(db):
    recipe, _, _ = seed(db)
    with pytest.raises(DBAPIError, match="Empty feature registry"), db.begin_nested():
        db.execute(
            insert(rm.CulinaryFeatureApplicability).values(
                id=uuid4(),
                recipe_version_id=recipe.id,
                dimension="METHOD",
                scope="RECIPE_COOKING_CONTEXT",
                key_hash=rc.RecipeMethodContextKey(recipe_version_id=recipe.id).fingerprint(),
                declared_tier_count=0,
            )
        )
        force_complete(db)


def test_overlap_registration_and_atomic_rekey(db):
    recipe, actor, terms = seed(db, "FLAVOR")
    svc = CulinaryFeatureService(db, actor_user_id=actor)
    q = review_command(
        recipe, terms, dimension="FLAVOR", expected_recipe_frontier=culinary_feature_frontier(db)
    )
    a = svc.write(q)
    force_complete(db)
    key = rc.CulinaryFeaturePathKey.model_validate(
        q.key.model_dump()
        | dict(tier_ids=tuple(t.id for t in recipe.portion_tiers), scope="REVIEWED_SCOPE")
    )
    other = review_command(
        recipe,
        terms,
        dimension="FLAVOR",
        key=key,
        expected_recipe_frontier=culinary_feature_frontier(db),
    )
    with pytest.raises(DBAPIError, match="Overlapping"), db.begin_nested():
        svc.write(other)
    retract = nextq(q, a, frontier=culinary_feature_frontier(db), action="RETRACT")
    register = other.model_copy(
        update={"expected_recipe_frontier": retract.expected_recipe_frontier + 1}
    )
    x, y = svc.rekey(retract, register)
    force_complete(db)
    assert y.source_sequence == x.source_sequence + 1
    assert all(z.replayed for z in svc.rekey(retract, register))


def capture(engine, actor, q):
    with (
        engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as session,
    ):
        return capture_culinary_feature_subject(session, q, actor_user_id=actor)


def committed_plan(engine, dimension="METHOD"):
    with Session(engine) as s:
        service, actor, graph, recipe = bound(s)
        proposal = service.propose(plan_request(service, actor, graph))
        terms = (term("PROTEIN" if dimension == "MAIN_PROTEIN" else dimension),)
        for t in terms:
            add_affinity_feature_term(s, t)
        if dimension != "MAIN_PROTEIN":
            q = review_command(
                recipe,
                terms,
                dimension=dimension,
                expected_recipe_frontier=culinary_feature_frontier(s),
            )
        if dimension == "MAIN_PROTEIN":
            cs = IngredientProteinService(s, actor_user_id=actor)
            cr = cs.write(catq(s, recipe.ingredients[0].ingredient_id, terms))
            q = mainq(s, recipe, terms, cr)
        a = CulinaryFeatureService(s, actor_user_id=actor).write(q)
        s.commit()
    req = pc.CulinaryFeatureCaptureRequest(
        household_id=graph.household_id,
        plan_id=graph.plan_id,
        proposal_id=proposal.id,
        proposal_hash=proposal.graph_hash,
        batch_node_id=graph.batches[0].node_id,
        requested_dimensions=(dimension,),
    )
    return actor, req, a, terms


@pytest.mark.parametrize("dimension", ["METHOD", "FLAVOR", "MAIN_PROTEIN"])
def test_canonical_readonly_capture_and_zero_io_replay(postgres_engine, dimension):
    actor, q, a, terms = committed_plan(postgres_engine, dimension)
    statements = []

    def sql(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(Engine, "before_cursor_execute", sql)
    try:
        s = capture(postgres_engine, actor, q)
    finally:
        event.remove(Engine, "before_cursor_execute", sql)
    assert all(t.lstrip().split()[0].upper() in {"SHOW", "SELECT"} for t in statements)
    if dimension != "MAIN_PROTEIN":
        assert not any("ingredient_protein_frontier" in t for t in statements)
        assert "catalog_frontier" not in s.evaluation.sources.model_dump()

    def forbidden(*args, **kw):
        raise AssertionError("Live SQL during pure resolution")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        result = discover_culinary_feature_assignments(s)
        resolved = resolve_feature_terms(
            s, (rc.FeatureTermQuery(dimension=dimension, term_ids=(terms[0].id,)),)
        )
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)
    assert result.dimensions[0].positive_term_ids == (terms[0].id,)
    assert resolved.terms[0].state == "PRESENT"
    assert not result.activation_ready
    assert pc.CapturedCulinaryFeatureSubjectDraft.model_validate_json(s.model_dump_json()) == s


def test_no_catalog_lock_for_recipe_only_write(postgres_engine):
    with Session(postgres_engine) as s:
        recipe, actor, terms = seed(s)
        s.commit()
    with Session(postgres_engine) as holder:
        holder.execute(select(cm.IngredientProteinFrontier).with_for_update()).all()
        with ThreadPoolExecutor() as pool:

            def write():
                with Session(postgres_engine) as s:
                    s.execute(text("SET LOCAL lock_timeout='500ms'"))
                    q = review_command(
                        recipe, terms, expected_recipe_frontier=culinary_feature_frontier(s)
                    )
                    CulinaryFeatureService(s, actor_user_id=actor).write(q)
                    s.commit()

            pool.submit(write).result(timeout=5)


def test_concurrent_revision_cas_one_winner(postgres_engine):
    with Session(postgres_engine) as s:
        recipe, actor, terms = seed(s)
        q = review_command(recipe, terms, expected_recipe_frontier=culinary_feature_frontier(s))
        a = CulinaryFeatureService(s, actor_user_id=actor).write(q)
        s.commit()
    barrier = Barrier(2)

    def write():
        with Session(postgres_engine) as s:
            expected = culinary_feature_frontier(s)
            cmd = nextq(q, a, frontier=expected)
            barrier.wait(timeout=5)
            try:
                value = CulinaryFeatureService(s, actor_user_id=actor).write(cmd)
                s.commit()
                return value
            except ValueError:
                s.rollback()
                return None

    with ThreadPoolExecutor() as pool:
        results = list(pool.map(lambda _: write(), range(2)))
    assert sum(x is not None for x in results) == 1


def test_migration_empty_and_existing_data_roundtrip_and_lossy_refusal(legacy_database):
    engine, config = legacy_database
    migrate(engine, config, "0012")
    with Session(engine) as s:
        recipe, actor, terms = seed(s)
        s.commit()
    for revision, down in [("0013", False), ("0012", True), ("0013", False)]:
        migrate(engine, config, revision, down=down)
    with Session(engine) as s:
        q = review_command(recipe, terms, expected_recipe_frontier=0)
        a = CulinaryFeatureService(s, actor_user_id=actor).write(q)
        s.commit()
    with pytest.raises(DBAPIError, match="lose culinary classification history"):
        migrate(engine, config, "0012", down=True)
    with Session(engine) as s:
        assert culinary_feature_sources(s, recipe.id, ("METHOD",))[0].reviews[0].id == a.review_id


@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
def test_direct_sql_writer_isolation_fail_closed(postgres_engine, isolation):
    with Session(postgres_engine) as s:
        recipe, actor, terms = seed(s)
        s.commit()
    with (
        postgres_engine.connect().execution_options(isolation_level=isolation) as conn,
        Session(conn) as s,
    ):
        with pytest.raises(DBAPIError, match="READ COMMITTED"):
            s.execute(
                insert(rm.CulinaryFeatureApplicability).values(
                    id=uuid4(),
                    recipe_version_id=recipe.id,
                    dimension="METHOD",
                    scope="RECIPE_COOKING_CONTEXT",
                    key_hash=rc.RecipeMethodContextKey(recipe_version_id=recipe.id).fingerprint(),
                    declared_tier_count=0,
                )
            )


def test_capture_requires_readonly_repeatable_snapshot_and_access(postgres_engine):
    actor, q, _, _ = committed_plan(postgres_engine)
    with Session(postgres_engine) as s:
        with pytest.raises(ValueError, match="read-only"):
            capture_culinary_feature_subject(s, q, actor_user_id=actor)
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as s,
    ):
        with pytest.raises(PermissionError):
            capture_culinary_feature_subject(s, q, actor_user_id=uuid4())


def test_rr_classification_replacement_preserves_old_capture(postgres_engine):
    actor, q, receipt, terms = committed_plan(postgres_engine, "FLAVOR")
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as reader,
    ):
        before = capture_culinary_feature_subject(reader, q, actor_user_id=actor)
        cmd = before.evaluation.sources.scopes[0].reviews[-1].command

        def write():
            with Session(postgres_engine) as s:
                replacement = nextq(
                    cmd, receipt, frontier=culinary_feature_frontier(s), positive_term_ids=()
                )
                CulinaryFeatureService(s, actor_user_id=actor).write(replacement)
                s.commit()

        with ThreadPoolExecutor(1) as pool:
            pool.submit(write).result(timeout=10)
        same = capture_culinary_feature_subject(reader, q, actor_user_id=actor)
        assert same.evaluation.sources == before.evaluation.sources
    fresh = capture(postgres_engine, actor, q)
    assert discover_culinary_feature_assignments(before).dimensions[0].state == "ASSIGNED"
    assert discover_culinary_feature_assignments(fresh).dimensions[0].state == "REVIEWED_NONE"
    assert fresh.evaluation.sources.recipe_frontier > before.evaluation.sources.recipe_frontier


def test_catalog_change_stales_only_main_protein_and_old_capture_replays(postgres_engine):
    actor, q, _, terms = committed_plan(postgres_engine, "MAIN_PROTEIN")
    old = capture(postgres_engine, actor, q)
    stream = old.evaluation.sources.catalog_streams[0]
    old_review = stream.reviews[-1]
    with Session(postgres_engine) as s:
        receipt = cat.IngredientProteinWriteReceipt(
            ingredient_id=stream.ingredient_id,
            stream_id=stream.id,
            review_id=old_review.id,
            source_sequence=old_review.source_sequence,
            command_hash=old_review.command_hash,
            replayed=False,
        )
        retract = nextq(
            old_review.command, receipt, frontier=ingredient_protein_frontier(s), action="RETRACT"
        )
        IngredientProteinService(s, actor_user_id=actor).write(retract)
        s.commit()
    fresh = capture(postgres_engine, actor, q)
    assert discover_culinary_feature_assignments(old).dimensions[0].state == "ASSIGNED"
    d = discover_culinary_feature_assignments(fresh).dimensions[0]
    assert d.state == "UNRESOLVED" and d.reason == "STALE_ASSOCIATION"
    # No false negative from a stale positive review.
    assert (
        resolve_feature_terms(
            fresh, (rc.FeatureTermQuery(dimension="MAIN_PROTEIN", term_ids=(terms[0].id,)),)
        )
        .terms[0]
        .state
        == "UNRESOLVED"
    )


def test_unrelated_catalog_edit_does_not_enter_method_capture_identity(postgres_engine):
    actor, q, _, _ = committed_plan(postgres_engine, "METHOD")
    before = capture(postgres_engine, actor, q)
    with Session(postgres_engine) as s:
        protein = term("PROTEIN")
        add_affinity_feature_term(s, protein)
        IngredientProteinService(s, actor_user_id=actor).write(
            catq(s, before.evaluation.recipe.ingredients[0].ingredient_id, (protein,))
        )
        s.commit()
    after = capture(postgres_engine, actor, q)
    assert after.evaluation.sources == before.evaluation.sources
    # Audit capture time changes; classification source and semantic METHOD identity do not.
    assert (
        discover_culinary_feature_assignments(after).dimensions
        == discover_culinary_feature_assignments(before).dimensions
    )
    assert "catalog_frontier" not in after.evaluation.sources.model_dump()


def test_proposal_replacement_rr_and_fresh_capture_stale_request(postgres_engine):
    from app.modules.execution.public import PlanRevisionService

    actor, q, _, _ = committed_plan(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as s,
    ):
        before = capture_culinary_feature_subject(s, q, actor_user_id=actor)

        def write():
            with Session(postgres_engine) as w:
                svc = PlanRevisionService(
                    w
                )  # Existing plan intent facade; no Execution work added.
                old_binding = before.proposal.graph.culinary_bindings[0]
                binding = old_binding.model_copy(update={"proposal_id": uuid4()})
                binding = binding.model_copy(update={"fingerprint": binding.expected_fingerprint()})
                g = pc.BoundPlanIntentGraph.model_validate(
                    before.proposal.graph.model_dump() | {"culinary_bindings": (binding,)}
                )
                proposal = svc.propose(plan_request(svc, actor, g))
                w.commit()
                return proposal

        with ThreadPoolExecutor(1) as pool:
            new = pool.submit(write).result(timeout=10)
        same = capture_culinary_feature_subject(s, q, actor_user_id=actor)
        assert before.proposal == same.proposal
    with pytest.raises(ValueError, match="Stale current proposal"):
        capture(postgres_engine, actor, q)
    nq = q.model_copy(update={"proposal_id": new.id, "proposal_hash": new.graph_hash})
    fresh = capture(postgres_engine, actor, nq)
    assert fresh.proposal.id == new.id
    assert fresh.evaluation.sources == before.evaluation.sources


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ"])
def test_next_transaction_late_child_rejected(postgres_engine, isolation):
    actor, q, a, terms = committed_plan(postgres_engine)
    with (
        postgres_engine.connect().execution_options(isolation_level=isolation) as conn,
        Session(conn) as s,
    ):
        s.scalar(
            select(rm.CulinaryFeatureReview.id).where(rm.CulinaryFeatureReview.id == a.review_id)
        )
        with pytest.raises(DBAPIError, match="Closed source|READ COMMITTED"):
            s.execute(
                insert(rm.CulinaryFeatureReviewTerm).values(
                    review_id=a.review_id,
                    applicability_id=a.applicability_id,
                    recipe_version_id=capture(postgres_engine, actor, q).evaluation.recipe.id,
                    dimension="METHOD",
                    term_id=terms[0].id,
                    term_kind="METHOD",
                )
            )


def test_method_context_does_not_require_legacy_path_binding(postgres_engine):
    with Session(postgres_engine) as s:
        svc, actor, graph, recipe = bound(s)
        d = graph.model_dump(exclude={"contract_version", "culinary_bindings"})
        for batch in d["batches"]:
            batch.pop("culinary_signature")
        g = pc.PlanIntentGraph.model_validate(d)
        w = svc.store.workspace(g.household_id, g.plan_id)
        proposal = svc.propose(
            pc.ProposePlanCommand(
                proposal_id=uuid4(),
                graph=g,
                expected_generation=w.latest_proposal_no,
                expected_revision=w.active_revision_no,
                scope="REMAINING_HORIZON",
                effective_from=g.horizon.start,
                actor_user_id=actor,
                source_system="synthetic.legacy",
                idempotency_key=uuid4().hex,
                reason="Legacy path absence",
            )
        )
        terms = (term("METHOD"),)
        for t in terms:
            add_affinity_feature_term(s, t)
        CulinaryFeatureService(s, actor_user_id=actor).write(
            review_command(recipe, terms, expected_recipe_frontier=culinary_feature_frontier(s))
        )
        s.commit()
    q = pc.CulinaryFeatureCaptureRequest(
        household_id=g.household_id,
        plan_id=g.plan_id,
        proposal_id=proposal.id,
        proposal_hash=proposal.graph_hash,
        batch_node_id=g.batches[0].node_id,
        requested_dimensions=("METHOD",),
    )
    assert capture(postgres_engine, actor, q).context.mode == "RECIPE_COOKING_CONTEXT_ONLY"
    with pytest.raises(ValueError, match="CULINARY_BINDING_UNAVAILABLE"):
        capture(postgres_engine, actor, q.model_copy(update={"requested_dimensions": ("FLAVOR",)}))


@pytest.mark.parametrize("damage", ["incomplete", "wrong_hash", "excess_after_complete"])
def test_direct_sql_committed_assembly_protocol_without_service(postgres_engine, damage):
    """No service finalizer is called: only deferred database constraints can reject."""
    with Session(postgres_engine) as s:
        recipe, actor, terms = seed(s, "PROTEIN")
        s.commit()
    with Session(postgres_engine) as s:
        q = catq(s, recipe.ingredients[0].ingredient_id, terms)
        stream_id, review_id = uuid4(), uuid4()
        s.execute(
            insert(cm.IngredientProteinStream).values(id=stream_id, ingredient_id=q.ingredient_id)
        )
        src = q.provenance.model_dump(exclude={"kind", "source_uri"})
        s.execute(
            insert(cm.IngredientProteinReview).values(
                id=review_id,
                stream_id=stream_id,
                ingredient_id=q.ingredient_id,
                revision_no=0,
                predecessor_id=None,
                predecessor_revision_no=None,
                source_sequence=q.expected_catalog_frontier + 1,
                action="REPLACE",
                command_kind="REPLACE",
                coverage="COMPLETE",
                reviewer_user_id=actor,
                idempotency_key=q.idempotency_key,
                command_hash="0" * 64 if damage == "wrong_hash" else q.fingerprint(actor),
                correction_reason=None,
                declared_covered_count=2,
                declared_assigned_count=1,
                source_kind=q.provenance.kind,
                source_uri=None,
                **src,
            )
        )
        for t in terms[:1] if damage == "incomplete" else terms:
            s.execute(
                insert(cm.IngredientProteinReviewTerm).values(
                    review_id=review_id,
                    ingredient_id=q.ingredient_id,
                    term_id=t.id,
                    term_kind="PROTEIN",
                )
            )
        s.execute(
            insert(cm.IngredientProteinAssignment).values(
                review_id=review_id,
                ingredient_id=q.ingredient_id,
                term_id=terms[0].id,
                term_kind="PROTEIN",
            )
        )
        if damage == "excess_after_complete":
            force_complete(s)
            with pytest.raises(DBAPIError, match="Closed source"), s.begin_nested():
                s.execute(
                    insert(cm.IngredientProteinReviewTerm).values(
                        review_id=review_id,
                        ingredient_id=q.ingredient_id,
                        term_id=terms[0].id,
                        term_kind="PROTEIN",
                    )
                )
            s.commit()  # Original complete aggregate remains intact.
        else:
            with pytest.raises(DBAPIError, match="Incomplete immutable|hash mismatch"):
                s.commit()


@pytest.mark.parametrize(
    "damage",
    [
        "foreign_requirement",
        "foreign_tier",
        "method_path",
        "rule_requirement",
        "transformation_ingredient",
        "coverage_none",
        "unsupported_main",
    ],
)
def test_sql_critical_relational_shapes(db, damage):
    from app.domain.feature_identity import identity_hash
    from feature_fixtures import path_key

    dimension = "MAIN_PROTEIN" if damage == "unsupported_main" else "FLAVOR"
    recipe, actor, terms = seed(db, "PROTEIN" if dimension == "MAIN_PROTEIN" else "FLAVOR")
    key = path_key(recipe, dimension)
    slots = []
    for slot in key.slots:
        fields = slot.model_dump()
        if slot.requirement_id == recipe.ingredients[0].id:
            if damage == "foreign_requirement":
                fields["requirement_id"] = uuid4()
            if damage == "rule_requirement":
                fields.update(choice="RULE", selected_rule_id=recipe.variant_rules[1].id)
            if damage == "transformation_ingredient":
                fields.update(
                    preparation="TRANSFORMATION", transformation_id=recipe.transformations[1].id
                )
        slots.append(rc.FeatureSlotApplicability(**fields))
    key = key.model_copy(
        update={
            "slots": tuple(sorted(slots, key=lambda x: str(x.requirement_id))),
            "tier_ids": (uuid4(),) if damage == "foreign_tier" else key.tier_ids,
        }
    )
    payload_key = key
    if damage == "method_path":
        dimension = "METHOD"
        payload_key = rc.RecipeMethodContextKey(recipe_version_id=recipe.id)
    aid, rid = uuid4(), uuid4()
    source = provenance().model_dump()
    command = dict(
        contract_version="culinary-feature-register.v1",
        command_kind="REGISTER",
        dimension=dimension,
        recipe_version_id=recipe.id,
        applicability_id=None,
        key=payload_key,
        expected_revision_no=-1,
        predecessor_id=None,
        expected_recipe_frontier=culinary_feature_frontier(db),
        coverage=None if damage == "coverage_none" else "COMPLETE",
        covered_term_ids=tuple(sorted((t.id for t in terms), key=str)),
        positive_term_ids=(terms[0].id,),
        supports=(),
        provenance=source,
        correction_reason=None,
        idempotency_key=uuid4().hex,
    )
    if dimension == "MAIN_PROTEIN":
        command["expected_catalog_frontier"] = ingredient_protein_frontier(db)
    expected = {
        "foreign_requirement": "foreign key",
        "foreign_tier": "foreign key",
        "method_path": "METHOD forbids",
        "rule_requirement": "Impossible authored slot path",
        "transformation_ingredient": "Impossible authored slot path",
        "coverage_none": "shape",
        "unsupported_main": "Unsupported main-protein",
    }[damage]
    with pytest.raises(DBAPIError, match=expected), db.begin_nested():
        db.execute(
            insert(rm.CulinaryFeatureApplicability).values(
                id=aid,
                recipe_version_id=recipe.id,
                dimension=dimension,
                scope=payload_key.scope,
                key_hash=payload_key.fingerprint(),
                declared_tier_count=0 if dimension == "METHOD" else 1,
            )
        )
        for slot in key.slots:
            db.execute(
                insert(rm.CulinaryFeatureApplicabilitySlot).values(
                    applicability_id=aid, recipe_version_id=recipe.id, **slot.model_dump()
                )
            )
        for tier in key.tier_ids:
            db.execute(
                insert(rm.CulinaryFeatureApplicabilityTier).values(
                    applicability_id=aid, recipe_version_id=recipe.id, tier_id=tier
                )
            )
        source_kind = source.pop("kind")
        source.pop("source_uri")
        db.execute(
            insert(rm.CulinaryFeatureReview).values(
                id=rid,
                applicability_id=aid,
                recipe_version_id=recipe.id,
                dimension=dimension,
                revision_no=0,
                predecessor_id=None,
                predecessor_revision_no=None,
                source_sequence=command["expected_recipe_frontier"] + 1,
                action="REPLACE",
                command_kind="REGISTER",
                coverage=command["coverage"],
                reviewer_user_id=actor,
                idempotency_key=command["idempotency_key"],
                command_hash=identity_hash(dict(command=command, actor_user_id=actor)),
                correction_reason=None,
                declared_covered_count=2,
                declared_assigned_count=1,
                declared_support_count=0,
                catalog_frontier_at_write=command.get("expected_catalog_frontier"),
                source_kind=source_kind,
                source_uri=None,
                **source,
            )
        )
        ctx = dict(
            review_id=rid, applicability_id=aid, recipe_version_id=recipe.id, dimension=dimension
        )
        for t in terms:
            db.execute(
                insert(rm.CulinaryFeatureReviewTerm).values(**ctx, term_id=t.id, term_kind=t.kind)
            )
        db.execute(
            insert(rm.CulinaryFeatureAssignment).values(
                **ctx, term_id=terms[0].id, term_kind=terms[0].kind
            )
        )
        force_complete(db)


def test_count_slot_support_is_identity_only_not_count_to_mass(db):
    recipe, actor, terms = seed(db, "PROTEIN")
    item = next(i for i in recipe.ingredients if i.quantity.basis == "COUNT")
    receipt = IngredientProteinService(db, actor_user_id=actor).write(
        catq(db, item.ingredient_id, terms)
    )
    key = __import__("feature_fixtures").path_key(recipe, "MAIN_PROTEIN")
    q = review_command(
        recipe,
        terms,
        dimension="MAIN_PROTEIN",
        key=key,
        expected_recipe_frontier=culinary_feature_frontier(db),
        expected_catalog_frontier=ingredient_protein_frontier(db),
        supports=(
            dict(
                term_id=terms[0].id,
                requirement_id=item.id,
                ingredient_id=item.ingredient_id,
                catalog_review_id=receipt.review_id,
            ),
        ),
    )
    CulinaryFeatureService(db, actor_user_id=actor).write(q)
    force_complete(db)
    assert item.quantity.item_ref == "garnish.egg"
    assert all(r.requirement_id != item.id for r in recipe.variant_rules)


def test_main_protein_cannot_use_unpinned_wildcard_support(db):
    from feature_fixtures import path_key

    recipe, actor, terms = seed(db, "PROTEIN")
    cr = IngredientProteinService(db, actor_user_id=actor).write(
        catq(db, recipe.ingredients[0].ingredient_id, terms)
    )
    key = path_key(recipe, "MAIN_PROTEIN")
    slots = tuple(
        s.model_copy(update=dict(choice="ANY_AUTHORED_CHOICE"))
        if s.requirement_id == recipe.ingredients[0].id
        else s
        for s in key.slots
    )
    key = rc.CulinaryFeaturePathKey.model_validate(
        key.model_dump() | dict(slots=slots, scope="REVIEWED_SCOPE")
    )
    q = mainq(db, recipe, terms, cr, key=key)
    with pytest.raises(DBAPIError, match="Stale/invalid"), db.begin_nested():
        CulinaryFeatureService(db, actor_user_id=actor).write(q)
