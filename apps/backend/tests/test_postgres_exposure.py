"""Read-only current-proposal capture; no real activation or behavioral execution fixture."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from app.modules.households.models import HouseholdMember
from app.modules.learning import contracts as c
from app.modules.learning.public import preview_recent_exposure
from app.modules.planning.contracts import BoundPlanIntentGraph
from app.modules.planning.public import capture_exposure_preview
from preference_fixtures import provenance
from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session
from test_postgres_culinary_bindings import bound, request, revise
from test_postgres_foundation import postgres_engine as postgres_engine

pytestmark = pytest.mark.postgres


def seed(engine, *, empty=False, participants=False):
    with Session(engine) as db:
        service, actor, graph, recipe = bound(db)
        others = []
        if participants:
            for _ in range(2):
                member = HouseholdMember(household_id=graph.household_id, name="Synthetic diner")
                db.add(member)
                db.flush()
                others.append(member.id)
            data = graph.model_dump()
            data["meals"][0]["participants"] += (
                dict(
                    member_id=others[0],
                    portion_factor=1,
                    nutrition_role="SHARED",
                ),
            )
            graph = BoundPlanIntentGraph.model_validate(data)
        p = None if empty else service.propose(request(service, actor, graph))
        db.commit()
    q = c.ExposurePreviewRequest(
        household_id=graph.household_id,
        member_id=graph.tracked_member_id,
        plan_ids=(graph.plan_id,),
        policy=c.ExposurePreviewPolicy(
            policy_id="explicit.preview-window",
            policy_version="test.1",
            provenance=provenance(),
            window=graph.horizon,
        ),
    )
    return actor, q, graph, p, recipe, others


def capture(engine, actor, q):
    with (
        engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as db,
    ):
        return capture_exposure_preview(db, q, actor_user_id=actor)


def test_canonical_source_roundtrip_and_no_side_effects(postgres_engine):
    actor, q, graph, p, recipe, _ = seed(postgres_engine)
    with postgres_engine.connect() as conn:
        before = {
            t: conn.scalar(text(f"SELECT count(*) FROM {t}"))
            for t in (
                "inventory_movements",
                "inventory_reservations",
                "member_preference_declarations",
                "plan_revisions",
                "plan_proposals",
            )
        }
    statements = []

    def sql(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lstrip().split()[0].upper())

    event.listen(Engine, "before_cursor_execute", sql)
    try:
        s = capture(postgres_engine, actor, q)
    finally:
        event.remove(Engine, "before_cursor_execute", sql)
    assert set(statements) <= {"SELECT", "SHOW"}
    result = preview_recent_exposure(s)
    assert result.facts[0].recipe_id == recipe.recipe.id
    assert s.recipes[0].provenance == recipe.provenance
    assert s.sources[0].proposal.graph_hash == p.graph_hash
    assert s.sources[0].workspace.state == "DRAFT"
    assert result.facts[0].source_kind == "PROPOSAL_PREVIEW"
    with postgres_engine.connect() as conn:
        assert {t: conn.scalar(text(f"SELECT count(*) FROM {t}")) for t in before} == before
        # 98 domain tables + Alembic; Nutrition adds 13 source tables.
        assert len(inspect(conn).get_table_names()) == 99
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0016"


def test_replay_has_zero_live_queries(postgres_engine):
    actor, q, *_ = seed(postgres_engine)
    s = capture(postgres_engine, actor, q)

    def forbidden(*args):
        raise AssertionError("Live IO during exposure replay")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        a = preview_recent_exposure(s)
        b = preview_recent_exposure(
            c.ExposurePreviewSnapshot.model_validate_json(s.canonical_json())
        )
        assert a.canonical_json() == b.canonical_json()
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)


def test_explicit_participants_only_and_no_member_copy(postgres_engine):
    actor, q, graph, p, recipe, others = seed(postgres_engine, participants=True)
    own = preview_recent_exposure(capture(postgres_engine, actor, q))
    guest = preview_recent_exposure(
        capture(postgres_engine, actor, q.model_copy(update={"member_id": others[0]}))
    )
    absent = preview_recent_exposure(
        capture(postgres_engine, actor, q.model_copy(update={"member_id": others[1]}))
    )
    assert own.facts[0].member_id == q.member_id
    assert guest.facts[0].member_id == others[0]
    assert own.facts[0].event_key() != guest.facts[0].event_key()
    assert not absent.facts and absent.snapshot.consumption_history == "UNAVAILABLE"


def test_empty_workspace_and_empty_selection_are_not_never_exposed(postgres_engine):
    actor, q, *_ = seed(postgres_engine, empty=True)
    s = capture(postgres_engine, actor, q)
    assert s.sources[0].proposal is None
    assert not preview_recent_exposure(s).facts
    empty = capture(postgres_engine, actor, q.model_copy(update={"plan_ids": ()}))
    assert not empty.sources and empty.consumption_history == "UNAVAILABLE"


@pytest.mark.parametrize("mutation", ["actor", "member", "plan", "household", "duplicate_plan"])
def test_missing_foreign_and_untrusted_sources_do_not_become_empty(postgres_engine, mutation):
    actor, q, *_ = seed(postgres_engine)
    changes = {
        "actor": {},
        "member": {"member_id": uuid4()},
        "plan": {"plan_ids": (uuid4(),)},
        "household": {"household_id": uuid4()},
        "duplicate_plan": {"plan_ids": q.plan_ids * 2},
    }
    with pytest.raises((PermissionError, LookupError, NoResultFound, ValueError)):
        capture(
            postgres_engine,
            uuid4() if mutation == "actor" else actor,
            q.model_copy(update=changes[mutation]),
        )


@pytest.mark.parametrize(
    "isolation,readonly",
    [("READ COMMITTED", False), ("READ COMMITTED", True), ("REPEATABLE READ", False)],
)
def test_capture_requires_readonly_repeatable_source(postgres_engine, isolation, readonly):
    actor, q, *_ = seed(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level=isolation, postgresql_readonly=readonly
        ) as conn,
        Session(conn) as db,
        pytest.raises(ValueError, match="read-only"),
    ):
        capture_exposure_preview(db, q, actor_user_id=actor)


def test_source_replacement_coherent_under_concurrent_revision(postgres_engine):
    actor, q, graph, p, recipe, _ = seed(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as reader,
    ):
        before = capture_exposure_preview(reader, q, actor_user_id=actor)

        def write():
            from app.modules.execution.public import PlanRevisionService

            with Session(postgres_engine) as db:
                service = PlanRevisionService(db)  # Existing intent proposal facade only.
                replacement = revise(graph, delta=10)
                service.propose(request(service, actor, replacement))
                db.commit()

        with ThreadPoolExecutor(1) as pool:
            pool.submit(write).result(timeout=15)
        same = capture_exposure_preview(reader, q, actor_user_id=actor)
        assert same.frontier_hash() == before.frontier_hash()
    fresh = capture(postgres_engine, actor, q)
    assert fresh.sources[0].proposal.proposal_no == p.proposal_no + 1
    assert fresh.frontier_hash() != before.frontier_hash()
    a, b = preview_recent_exposure(before), preview_recent_exposure(fresh)
    assert len(a.facts) == len(b.facts) == 1  # Old proposals do not become extra history.
    assert a.facts[0].event_key() == b.facts[0].event_key()
    assert a.facts[0].proposal_id != b.facts[0].proposal_id


def test_direct_sql_cannot_relabel_a_sealed_proposal_as_confirmed(postgres_engine):
    actor, q, graph, p, *_ = seed(postgres_engine)
    with Session(postgres_engine) as db, pytest.raises(IntegrityError):
        db.execute(
            text("UPDATE plan_meal_intents SET status='CONFIRMED' WHERE proposal_id=:p"),
            {"p": p.id},
        )
        db.commit()
    assert all(
        f.status == "PROVISIONAL"
        for f in preview_recent_exposure(capture(postgres_engine, actor, q)).facts
    )


def test_retired_intent_removes_preview_without_deleting_history(postgres_engine):
    actor, q, graph, p, *_ = seed(postgres_engine)
    old = preview_recent_exposure(capture(postgres_engine, actor, q))
    with Session(postgres_engine) as db:
        from app.modules.execution.public import PlanRevisionService

        service = PlanRevisionService(db)
        data = revise(graph).model_dump()
        data["meals"][0]["status"] = "RETIRED"
        for row in data["batches"] + data["allocations"]:
            row["status"] = "RETIRED"
        replacement = BoundPlanIntentGraph.model_validate(data)
        service.propose(request(service, actor, replacement))
        db.commit()
    fresh = preview_recent_exposure(capture(postgres_engine, actor, q))
    assert old.facts and not fresh.facts
    with Session(postgres_engine) as db:
        from app.modules.planning.public import PlanStore

        assert (
            PlanStore(db).proposal(q.household_id, graph.plan_id, p.id).graph_hash == p.graph_hash
        )
