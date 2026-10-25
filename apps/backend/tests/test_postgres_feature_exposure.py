"""Real RR/SERIALIZABLE coordinated source capture, no materialization or learning writes."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from app.modules.catalog.public import IngredientProteinService, ingredient_protein_frontier
from app.modules.households.models import HouseholdMember
from app.modules.learning import contracts as c
from app.modules.learning.public import preview_feature_exposure
from app.modules.planning import contracts as p
from app.modules.planning.public import PlanStore, capture_feature_exposure_preview
from app.modules.recipes.public import CulinaryFeatureService, culinary_feature_frontier
from preference_fixtures import provenance
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, NoResultFound
from sqlalchemy.orm import Session
from test_postgres_culinary_bindings import request as plan_request
from test_postgres_culinary_features import (
    committed_plan,
    nextq,
)
from test_postgres_foundation import postgres_engine as postgres_engine

pytestmark = pytest.mark.postgres


def setup(engine, dimension="FLAVOR"):
    actor, fq, receipt, terms = committed_plan(engine, dimension)
    with Session(engine) as db:
        workspace, proposal = PlanStore(db).latest_proposal_source(fq.household_id, fq.plan_id)
    q = c.FeatureExposurePreviewRequest(
        household_id=fq.household_id,
        plan_id=fq.plan_id,
        proposal_id=fq.proposal_id,
        proposal_hash=fq.proposal_hash,
        selected_member_ids=(workspace.tracked_member_id,),
        requested_dimensions=(dimension,),
        recipe_eligibility_policy=c.ExposurePreviewPolicy(
            policy_id="explicit.feature-window",
            policy_version="test.v1",
            provenance=provenance(),
            window=proposal.graph.horizon,
        ),
    )
    return actor, q, receipt, terms


def capture(engine, actor, q, isolation="REPEATABLE READ"):
    with (
        engine.connect().execution_options(
            isolation_level=isolation,
            postgresql_readonly=True,
        ) as conn,
        Session(conn) as db,
    ):
        return capture_feature_exposure_preview(db, q, actor_user_id=actor)


@pytest.mark.parametrize("dimension", ["METHOD", "FLAVOR", "MAIN_PROTEIN"])
@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
def test_single_readonly_capture_and_pure_zero_io_replay(postgres_engine, dimension, isolation):
    actor, q, receipt, _ = setup(postgres_engine, dimension)
    statements = []

    def sql(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(Engine, "before_cursor_execute", sql)
    try:
        source = capture(postgres_engine, actor, q, isolation)
    finally:
        event.remove(Engine, "before_cursor_execute", sql)
    assert {s.lstrip().split()[0].upper() for s in statements} <= {"SELECT", "SHOW"}
    if dimension != "MAIN_PROTEIN":
        assert not any("ingredient_protein_frontier" in s for s in statements)
        assert "catalog_frontier" not in source.frontiers[0].model_dump()

    def forbidden(*args):
        raise AssertionError("Live IO during feature exposure replay")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        a = preview_feature_exposure(source)
        b = preview_feature_exposure(
            c.FeatureExposureSourceSnapshotDraft.model_validate_json(source.canonical_json())
        )
        assert a.fingerprint() == b.fingerprint()
        assert all(w.assignment.review_id == receipt.review_id for f in a.events for w in f.support)
        assert a.events and a.diagnostics and not a.activation_ready
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)


def test_capture_has_no_physical_preference_plan_or_schema_side_effects(postgres_engine):
    actor, q, *_ = setup(postgres_engine)
    tables = (
        "inventory_movements",
        "inventory_reservations",
        "member_preference_declarations",
        "plan_revisions",
        "plan_proposals",
        "culinary_feature_reviews",
    )

    def counts():
        with postgres_engine.connect() as conn:
            return {t: conn.scalar(text(f"SELECT count(*) FROM {t}")) for t in tables}

    before = counts()
    preview_feature_exposure(capture(postgres_engine, actor, q))
    assert before == counts()
    with postgres_engine.connect() as conn:
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0013"


@pytest.mark.parametrize("mutation", ["actor", "member", "household", "proposal", "hash", "plan"])
def test_canonical_source_access_and_stale_owner_rejected(postgres_engine, mutation):
    actor, q, *_ = setup(postgres_engine)
    change = {
        "actor": {},
        "member": {"selected_member_ids": (uuid4(),)},
        "household": {"household_id": uuid4()},
        "proposal": {"proposal_id": uuid4()},
        "hash": {"proposal_hash": "0" * 64},
        "plan": {"plan_id": uuid4()},
    }[mutation]
    with pytest.raises((LookupError, ValueError, PermissionError, NoResultFound)):
        capture(
            postgres_engine, uuid4() if mutation == "actor" else actor, q.model_copy(update=change)
        )


@pytest.mark.parametrize("shape", ["read_committed", "writable", "dirty"])
def test_capture_requires_clean_readonly_snapshot_transaction(postgres_engine, shape):
    actor, q, *_ = setup(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level="READ COMMITTED" if shape == "read_committed" else "REPEATABLE READ",
            postgresql_readonly=shape != "writable",
        ) as conn,
        Session(conn) as db,
    ):
        if shape == "dirty":
            db.add(HouseholdMember(household_id=q.household_id, name="Unflushed"))
        with pytest.raises(ValueError, match="clean read-only"):
            capture_feature_exposure_preview(db, q, actor_user_id=actor)


@pytest.mark.parametrize("dimension", ["METHOD", "FLAVOR", "MAIN_PROTEIN"])
def test_empty_window_captures_actual_frontier_and_explicit_absence(postgres_engine, dimension):
    actor, q, *_ = setup(postgres_engine, dimension)
    with Session(postgres_engine) as db:
        _, p0 = PlanStore(db).latest_proposal_source(q.household_id, q.plan_id)
        first = min(m.scheduled_at for m in p0.graph.meals)
        expected = culinary_feature_frontier(db)
    policy = c.ExposurePreviewPolicy.model_validate(
        q.recipe_eligibility_policy.model_dump()
        | {"window": dict(start=first - timedelta(hours=1), end=first)}
    )
    q = q.model_copy(update={"recipe_eligibility_policy": policy})
    result = preview_feature_exposure(capture(postgres_engine, actor, q))
    assert (
        not result.events and not result.diagnostics and not result.snapshot.classification_sources
    )
    assert result.snapshot.frontiers[0].recipe_frontier == expected
    assert result.absence_semantics == "NOT_EVIDENCE_OF_NEVER_EXPOSED_OR_GLOBAL_FEATURE_ABSENCE"


def test_catalog_replacement_old_replay_fresh_main_stale_other_dimensions_unchanged(
    postgres_engine,
):
    # Add METHOD/FLAVOR to the same canonical plan, then capture all singleton branches together.
    actor, q, _, terms = setup(postgres_engine, "MAIN_PROTEIN")
    from app.modules.catalog.public import add_affinity_feature_term
    from app.modules.recipes.public import authored_version
    from feature_fixtures import review_command
    from preference_fixtures import term

    with Session(postgres_engine) as db:
        _, p0 = PlanStore(db).latest_proposal_source(q.household_id, q.plan_id)
        recipe = authored_version(db, p0.graph.batches[0].recipe_version_id)
        for d in ("METHOD", "FLAVOR"):
            t = term(d)
            add_affinity_feature_term(db, t)
            CulinaryFeatureService(db, actor_user_id=actor).write(
                review_command(
                    recipe,
                    (t,),
                    dimension=d,
                    expected_recipe_frontier=culinary_feature_frontier(db),
                )
            )
        db.commit()
    q = q.model_copy(update={"requested_dimensions": ("METHOD", "FLAVOR", "MAIN_PROTEIN")})
    old = capture(postgres_engine, actor, q)
    before = preview_feature_exposure(old)
    with Session(postgres_engine) as db:
        from app.modules.catalog.public import ingredient_protein_sources

        stream = ingredient_protein_sources(db, (recipe.ingredients[0].ingredient_id,))[0]
        r0 = stream.reviews[-1]
        cq = nextq(
            r0.command,
            type("Receipt", (), {"review_id": r0.id})(),
            frontier=ingredient_protein_frontier(db),
        )
        IngredientProteinService(db, actor_user_id=actor).write(cq)
        db.commit()
    after = preview_feature_exposure(capture(postgres_engine, actor, q))
    assert before.fingerprint() == preview_feature_exposure(old).fingerprint()

    def cuts(result):
        return {x.dimension: x.digest for x in result.evidence_cuts}

    assert cuts(before)["METHOD"] == cuts(after)["METHOD"]
    assert cuts(before)["FLAVOR"] == cuts(after)["FLAVOR"]
    assert cuts(before)["MAIN_PROTEIN"] != cuts(after)["MAIN_PROTEIN"]
    assert any(d.discovery.reason == "STALE_ASSOCIATION" for d in after.diagnostics)
    assert not any(e.dimension == "MAIN_PROTEIN" for e in after.events)


def test_concurrent_proposal_replacement_cannot_mix_member_or_classification_reads(postgres_engine):
    actor, q, *_ = setup(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ",
            postgresql_readonly=True,
        ) as conn,
        Session(conn) as db,
    ):
        db.execute(text("SELECT 1 FROM plan_workspaces WHERE id=:id"), {"id": q.plan_id}).all()

        def replace():
            from app.modules.execution.public import PlanRevisionService

            with Session(postgres_engine) as writer:
                _, p0 = PlanStore(writer).latest_proposal_source(q.household_id, q.plan_id)
                service = PlanRevisionService(writer)
                bindings = tuple(
                    b.model_copy(update={"proposal_id": uuid4()})
                    for b in p0.graph.culinary_bindings
                )
                bindings = tuple(
                    b.model_copy(update={"fingerprint": b.expected_fingerprint()}) for b in bindings
                )
                graph = p.BoundPlanIntentGraph.model_validate(
                    p0.graph.model_dump() | dict(culinary_bindings=bindings)
                )
                result = service.propose(plan_request(service, actor, graph))
                writer.commit()
                return result

        with ThreadPoolExecutor() as pool:
            fresh = pool.submit(replace).result(timeout=10)
        old = capture_feature_exposure_preview(db, q, actor_user_id=actor)
        assert {s.subject.proposal.id for s in old.classification_sources} == {q.proposal_id}
        assert old.member_sources[0].sources[0].proposal.id == q.proposal_id
    with pytest.raises(ValueError, match="stale"):
        capture(postgres_engine, actor, q)
    current = capture(
        postgres_engine,
        actor,
        q.model_copy(update={"proposal_id": fresh.id, "proposal_hash": fresh.graph_hash}),
    )
    a, b = preview_feature_exposure(old), preview_feature_exposure(current)
    assert {e.event_key() for e in a.events} == {e.event_key() for e in b.events}
    assert a.fingerprint() != b.fingerprint()


@pytest.mark.parametrize(
    "table,operation",
    [
        ("plan_proposals", "DELETE"),
        ("culinary_feature_reviews", "DELETE"),
        ("culinary_feature_assignments", "TRUNCATE"),
    ],
)
def test_direct_sql_cannot_rewrite_sealed_feature_source(postgres_engine, table, operation):
    actor, q, *_ = setup(postgres_engine)
    old = capture(postgres_engine, actor, q)
    before = preview_feature_exposure(old).fingerprint()
    with Session(postgres_engine) as db, pytest.raises(DBAPIError):
        db.execute(text(f"{operation} {table}"))
        db.commit()
    assert preview_feature_exposure(old).fingerprint() == before


def test_selected_members_capture_once_per_batch_dimension_with_explicit_participation(
    postgres_engine,
):
    from app.modules.execution.public import PlanRevisionService

    actor, q, *_ = setup(postgres_engine)
    with Session(postgres_engine) as db:
        _, p0 = PlanStore(db).latest_proposal_source(q.household_id, q.plan_id)
        guest = HouseholdMember(household_id=q.household_id, name="Participating guest")
        absent = HouseholdMember(household_id=q.household_id, name="Not participating")
        db.add_all((guest, absent))
        db.flush()
        bindings = tuple(
            b.model_copy(update={"proposal_id": uuid4()}) for b in p0.graph.culinary_bindings
        )
        bindings = tuple(
            b.model_copy(update={"fingerprint": b.expected_fingerprint()}) for b in bindings
        )
        data = p0.graph.model_dump() | dict(culinary_bindings=bindings)
        for meal in data["meals"]:
            meal["participants"] += (
                dict(member_id=guest.id, portion_factor=1, nutrition_role="SHARED"),
            )
        graph = p.BoundPlanIntentGraph.model_validate(data)
        svc = PlanRevisionService(db)
        new = svc.propose(plan_request(svc, actor, graph))
        ids = q.selected_member_ids + (guest.id, absent.id)
        absent_id = absent.id
        db.commit()
    q = q.model_copy(
        update={"proposal_id": new.id, "proposal_hash": new.graph_hash, "selected_member_ids": ids}
    )
    snapshot = capture(postgres_engine, actor, q)
    result = preview_feature_exposure(snapshot)
    assert len(snapshot.member_sources) == 3
    assert len(snapshot.classification_sources) == 1
    assert {e.member_id for e in result.events} == set(ids) - {absent_id}
    assert len({e.event_key() for e in result.events}) == len(result.events)


def test_missing_binding_fails_whole_request_and_explicit_method_retry_succeeds(postgres_engine):
    from app.modules.catalog.public import add_affinity_feature_term
    from feature_fixtures import review_command
    from preference_fixtures import term
    from test_postgres_culinary_bindings import bound

    with Session(postgres_engine) as db:
        service, actor, initial_graph, recipe = bound(db)
        data = initial_graph.model_dump(exclude={"contract_version", "culinary_bindings"})
        for b in data["batches"]:
            b.pop("culinary_signature")
        graph = p.PlanIntentGraph.model_validate(data)
        workspace = service.store.workspace(graph.household_id, graph.plan_id)
        new = service.propose(
            p.ProposePlanCommand(
                proposal_id=uuid4(),
                graph=graph,
                expected_generation=workspace.latest_proposal_no,
                expected_revision=workspace.active_revision_no,
                scope="REMAINING_HORIZON",
                effective_from=graph.horizon.start,
                actor_user_id=actor,
                source_system="synthetic.legacy",
                idempotency_key=uuid4().hex,
                reason="Explicit legacy recipe intent without exact path",
            )
        )
        t = term("METHOD")
        add_affinity_feature_term(db, t)
        CulinaryFeatureService(db, actor_user_id=actor).write(
            review_command(recipe, (t,), expected_recipe_frontier=culinary_feature_frontier(db))
        )
        db.commit()
    q = c.FeatureExposurePreviewRequest(
        household_id=graph.household_id,
        plan_id=graph.plan_id,
        proposal_id=new.id,
        proposal_hash=new.graph_hash,
        selected_member_ids=(graph.tracked_member_id,),
        requested_dimensions=("METHOD",),
        recipe_eligibility_policy=c.ExposurePreviewPolicy(
            policy_id="explicit.legacy-window",
            policy_version="1",
            provenance=provenance(),
            window=graph.horizon,
        ),
    )
    for dims in (("FLAVOR",), ("METHOD", "FLAVOR"), ("MAIN_PROTEIN",)):
        with pytest.raises(ValueError, match="CULINARY_BINDING_UNAVAILABLE"):
            capture(postgres_engine, actor, q.model_copy(update={"requested_dimensions": dims}))
    assert preview_feature_exposure(capture(postgres_engine, actor, q)).events


def test_concurrent_classification_replacement_keeps_old_source_cut_coherent(postgres_engine):
    from app.modules.recipes.public import culinary_feature_sources

    actor, q, receipt, _ = setup(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ",
            postgresql_readonly=True,
        ) as conn,
        Session(conn) as reader,
    ):
        before = capture_feature_exposure_preview(reader, q, actor_user_id=actor)
        recipe = before.classification_sources[0].subject.evaluation.recipe

        def replace():
            with Session(postgres_engine) as writer:
                scope = culinary_feature_sources(writer, recipe.id, ("FLAVOR",))[0]
                command = nextq(
                    scope.reviews[-1].command,
                    receipt,
                    frontier=culinary_feature_frontier(writer),
                    positive_term_ids=(),
                )
                CulinaryFeatureService(writer, actor_user_id=actor).write(command)
                writer.commit()

        with ThreadPoolExecutor() as pool:
            pool.submit(replace).result(timeout=10)
        same = capture_feature_exposure_preview(reader, q, actor_user_id=actor)
        assert (
            preview_feature_exposure(before).evidence_cuts
            == preview_feature_exposure(same).evidence_cuts
        )
    old = preview_feature_exposure(before)
    fresh = preview_feature_exposure(capture(postgres_engine, actor, q))
    assert old.events and not fresh.events
    assert {d.discovery.state for d in fresh.diagnostics} == {"REVIEWED_NONE"}
    assert old.evidence_cuts != fresh.evidence_cuts
