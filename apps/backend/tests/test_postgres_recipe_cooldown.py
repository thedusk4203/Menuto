"""Real-PG canonical ingress and source replacement; no execution/accepted-publication fixture."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from app.modules.learning import contracts as c
from app.modules.learning.public import assess_recipe_cooldown
from app.modules.planning.public import capture_exposure_preview
from cooldown_fixtures import repeated_graph
from preference_fixtures import provenance
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_postgres_culinary_bindings import bound, request, revise
from test_postgres_exposure import capture
from test_postgres_foundation import postgres_engine as postgres_engine

pytestmark = pytest.mark.postgres


def seed(engine):
    with Session(engine) as db:
        service, actor, g, recipe = bound(db)
        g = repeated_graph(g)
        p = service.propose(request(service, actor, g))
        db.commit()
    q = c.ExposurePreviewRequest(
        household_id=g.household_id,
        member_id=g.tracked_member_id,
        plan_ids=(g.plan_id,),
        policy=c.ExposurePreviewPolicy(
            policy_id="test.capture", policy_version="1", provenance=provenance(), window=g.horizon
        ),
    )
    policy = c.RecipeCooldownPolicy(
        policy_id="test.cooldown",
        policy_version="1",
        provenance=provenance(),
        duration_microseconds=7200000000,
    )
    query = c.RecipeCooldownQuery(
        household_id=g.household_id,
        member_id=g.tracked_member_id,
        plan_id=g.plan_id,
        proposal_id=p.id,
        meal_node_id=g.meals[0].node_id,
        recipe_id=recipe.recipe.id,
    )
    return actor, q, query, policy, g


def counts(engine):
    with engine.connect() as conn:
        return {
            t: conn.scalar(text(f"SELECT count(*) FROM {t}"))
            for t in (
                "inventory_movements",
                "inventory_reservations",
                "member_preference_declarations",
                "plan_revisions",
                "plan_proposals",
            )
        }


def test_readonly_canonical_capture_then_zero_io_evaluation(postgres_engine):
    actor, q, query, policy, _ = seed(postgres_engine)
    before = counts(postgres_engine)
    statements = []

    def sql(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lstrip().split()[0].upper())

    event.listen(Engine, "before_cursor_execute", sql)
    try:
        s = capture(postgres_engine, actor, q)
    finally:
        event.remove(Engine, "before_cursor_execute", sql)
    assert set(statements) <= {"SELECT", "SHOW"}

    def forbidden(*args):
        raise AssertionError("Cooldown core attempted live IO")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        subject = c.RecipeCooldownInput(snapshot=s, query=query, policy=policy)
        a = assess_recipe_cooldown(subject)
        b = c.RecipeCooldownAssessmentDraft.model_validate_json(a.canonical_json())
        assert a.canonical_json() == b.canonical_json()
        assert a.witnesses[0].distance_microseconds == 3600000000
        assert not a.activation_ready and a.consumption_history == "UNAVAILABLE"
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)
    assert counts(postgres_engine) == before


def test_concurrent_proposal_replacement_requires_fresh_query_and_capture(postgres_engine):
    actor, q, query, policy, graph = seed(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as reader,
    ):
        old = capture_exposure_preview(reader, q, actor_user_id=actor)
        a = assess_recipe_cooldown(c.RecipeCooldownInput(snapshot=old, query=query, policy=policy))

        def write():
            from app.modules.execution.public import PlanRevisionService

            with Session(postgres_engine) as db:
                service = PlanRevisionService(
                    db
                )  # Existing proposal service, no execution workflow.
                data = revise(graph).model_dump()
                data["meals"][-1]["status"] = "RETIRED"
                data["allocations"][-1]["status"] = "RETIRED"
                updated = type(graph).model_validate(data)
                service.propose(request(service, actor, updated))
                db.commit()

        with ThreadPoolExecutor(1) as pool:
            pool.submit(write).result(timeout=15)
        same = capture_exposure_preview(reader, q, actor_user_id=actor)
        same_result = assess_recipe_cooldown(
            c.RecipeCooldownInput(snapshot=same, query=query, policy=policy)
        )
        assert same.frontier_hash() == old.frontier_hash()
        assert same_result.witnesses == a.witnesses and same_result.outcome == a.outcome
        # A new captured_at may change snapshot/result identity, not the captured source frontier.
    fresh = capture(postgres_engine, actor, q)
    with pytest.raises(ValueError, match="plan/proposal"):
        c.RecipeCooldownInput(snapshot=fresh, query=query, policy=policy)
    fresh_query = query.model_copy(update={"proposal_id": fresh.sources[0].proposal.id})
    b = assess_recipe_cooldown(
        c.RecipeCooldownInput(snapshot=fresh, query=fresh_query, policy=policy)
    )
    assert b.outcome == "NO_MATCH_IN_SELECTED_PROPOSAL" and not b.witnesses
    assert a.witnesses and old.sources[0].proposal.id != fresh.sources[0].proposal.id


@pytest.mark.parametrize(
    "isolation,readonly", [("READ COMMITTED", True), ("REPEATABLE READ", False)]
)
def test_noncoherent_or_writable_ingress_is_rejected(postgres_engine, isolation, readonly):
    actor, q, *_ = seed(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level=isolation, postgresql_readonly=readonly
        ) as conn,
        Session(conn) as db,
        pytest.raises(ValueError, match="read-only"),
    ):
        capture_exposure_preview(db, q, actor_user_id=actor)


def test_sql_cannot_rewrite_source_used_by_cooldown(postgres_engine):
    actor, q, query, policy, _ = seed(postgres_engine)
    s = capture(postgres_engine, actor, q)
    a = assess_recipe_cooldown(c.RecipeCooldownInput(snapshot=s, query=query, policy=policy))
    with Session(postgres_engine) as db, pytest.raises(IntegrityError):
        db.execute(
            text("UPDATE plan_meal_intents SET status='RETIRED' WHERE proposal_id=:p"),
            {"p": query.proposal_id},
        )
        db.commit()
    assert (
        assess_recipe_cooldown(
            c.RecipeCooldownInput(
                snapshot=capture(postgres_engine, actor, q), query=query, policy=policy
            )
        ).witnesses
        == a.witnesses
    )
