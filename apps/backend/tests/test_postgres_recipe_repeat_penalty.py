"""Real capture/immutability/concurrency seam; penalty interpretation remains zero-IO."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from app.modules.learning import contracts as c
from app.modules.learning.public import interpret_recipe_repeat_penalty, trace_recipe_decay
from app.modules.planning.public import capture_exposure_preview
from decay_fixtures import band, policy_for
from repeat_penalty_fixtures import penalty_input
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_postgres_culinary_bindings import request, revise
from test_postgres_exposure import capture
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_recipe_cooldown import counts, seed
from test_postgres_recipe_decay import subject_for

pytestmark = pytest.mark.postgres


def test_readonly_capture_then_exact_penalty_zero_io_and_no_side_effects(postgres_engine):
    actor, q, query, cooldown_policy, _ = seed(postgres_engine)
    before = counts(postgres_engine)
    statements = []

    def audit(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lstrip().split()[0].upper())

    event.listen(Engine, "before_cursor_execute", audit)
    try:
        snapshot = capture(postgres_engine, actor, q)
    finally:
        event.remove(Engine, "before_cursor_execute", audit)
    assert set(statements) <= {"SELECT", "SHOW"}

    def forbidden(*args):
        raise AssertionError("Penalty interpretation attempted DB IO")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        trace = trace_recipe_decay(subject_for(snapshot, query, cooldown_policy))
        result = interpret_recipe_repeat_penalty(penalty_input(trace))
        assert result.proposal_local_repeat_penalty == c.RepeatPenaltyAmount(
            numerator=3, denominator=2
        )
        assert result.contributions[0].source.witness.fact.proposal_id == query.proposal_id
        assert (
            c.RecipeRepeatPenaltyDraft.model_validate_json(result.canonical_json()).canonical_json()
            == result.canonical_json()
        )
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)
    assert counts(postgres_engine) == before
    with Session(postgres_engine) as db, pytest.raises(IntegrityError):
        db.execute(
            text("UPDATE plan_meal_intents SET status='RETIRED' WHERE proposal_id=:p"),
            {"p": query.proposal_id},
        )
        db.commit()
    assert interpret_recipe_repeat_penalty(result.subject).fingerprint() == result.fingerprint()


def test_concurrent_replacement_keeps_old_rr_result_fresh_query_sees_absence(postgres_engine):
    actor, q, query, cooldown_policy, graph = seed(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as reader,
    ):
        old = capture_exposure_preview(reader, q, actor_user_id=actor)
        a = interpret_recipe_repeat_penalty(
            penalty_input(trace_recipe_decay(subject_for(old, query, cooldown_policy)))
        )

        def write():
            from app.modules.execution.public import PlanRevisionService

            with Session(postgres_engine) as db:
                service = PlanRevisionService(
                    db
                )  # Existing proposal facade, no Execution workflow.
                data = revise(graph).model_dump()
                data["meals"][-1]["status"] = "RETIRED"
                data["allocations"][-1]["status"] = "RETIRED"
                service.propose(request(service, actor, type(graph).model_validate(data)))
                db.commit()

        with ThreadPoolExecutor(1) as pool:
            pool.submit(write).result(timeout=15)
        same = capture_exposure_preview(reader, q, actor_user_id=actor)
        b = interpret_recipe_repeat_penalty(
            penalty_input(trace_recipe_decay(subject_for(same, query, cooldown_policy)))
        )
        assert same.frontier_hash() == old.frontier_hash()
        assert a.contributions == b.contributions
        assert a.proposal_local_repeat_penalty == b.proposal_local_repeat_penalty
    fresh = capture(postgres_engine, actor, q)
    with pytest.raises(ValueError, match="plan/proposal"):
        subject_for(fresh, query, cooldown_policy)
    query = query.model_copy(update={"proposal_id": fresh.sources[0].proposal.id})
    result = interpret_recipe_repeat_penalty(
        penalty_input(trace_recipe_decay(subject_for(fresh, query, cooldown_policy)))
    )
    assert result.outcome == "NO_MATCH_IN_SELECTED_PROPOSAL"
    assert result.proposal_local_repeat_penalty is None
    assert interpret_recipe_repeat_penalty(a.subject).fingerprint() == a.fingerprint()


def test_zero_retention_keeps_real_source_and_zero_contribution(postgres_engine):
    actor, q, query, cooldown_policy, _ = seed(postgres_engine)
    subject = subject_for(capture(postgres_engine, actor, q), query, cooldown_policy)
    duration = subject.assessment.subject.policy.duration_microseconds
    policy = policy_for(subject.assessment, (band(0, 0, duration, 0, 13),))
    trace = trace_recipe_decay(c.RecipeDecayInput(assessment=subject.assessment, policy=policy))
    result = interpret_recipe_repeat_penalty(penalty_input(trace))
    assert result.outcome == "INTERPRETED_IN_SELECTED_PROPOSAL"
    assert result.proposal_local_repeat_penalty.numerator == 0
    assert len(result.contributions) == 1
    assert result.contributions[0].source.witness.fact.proposal_id == query.proposal_id
    assert result.contributions[0].contribution.denominator == 1


@pytest.mark.parametrize(
    "isolation,readonly", [("READ COMMITTED", True), ("REPEATABLE READ", False)]
)
def test_invalid_capture_cannot_supply_penalty(postgres_engine, isolation, readonly):
    actor, q, *_ = seed(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level=isolation, postgresql_readonly=readonly
        ) as conn,
        Session(conn) as db,
        pytest.raises(ValueError, match="read-only"),
    ):
        capture_exposure_preview(db, q, actor_user_id=actor)
