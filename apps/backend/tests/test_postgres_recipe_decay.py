"""Canonical read-only source capture and pure as-of-capture policy interpretation."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from app.modules.learning import contracts as c
from app.modules.learning.public import assess_recipe_cooldown, trace_recipe_decay
from app.modules.planning.public import capture_exposure_preview
from decay_fixtures import band, policy_for
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_postgres_culinary_bindings import request, revise
from test_postgres_exposure import capture
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_recipe_cooldown import counts, seed

pytestmark = pytest.mark.postgres


def subject_for(snapshot, query, cooldown_policy):
    assessment = assess_recipe_cooldown(
        c.RecipeCooldownInput(snapshot=snapshot, query=query, policy=cooldown_policy)
    )
    return c.RecipeDecayInput(assessment=assessment, policy=policy_for(assessment))


def test_canonical_ingress_then_trace_and_roundtrip_with_zero_io_or_writes(postgres_engine):
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
        raise AssertionError("Decay interpretation attempted IO")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        subject = subject_for(snapshot, query, cooldown_policy)
        old_bytes = subject.assessment.canonical_json()
        result = trace_recipe_decay(subject)
        assert result.entries[0].witness == subject.assessment.witnesses[0]
        assert c.RecipeDecayTraceDraft.model_validate_json(
            result.canonical_json()
        ).canonical_json() == (result.canonical_json())
        assert subject.assessment.canonical_json() == old_bytes
        assert result.subject.assessment.decay == "UNAVAILABLE"
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)
    assert counts(postgres_engine) == before
    with Session(postgres_engine) as db, pytest.raises(IntegrityError):
        db.execute(
            text("UPDATE plan_meal_intents SET status='RETIRED' WHERE proposal_id=:p"),
            {"p": query.proposal_id},
        )
        db.commit()


def test_concurrent_source_replacement_preserves_old_trace_requires_new_query(postgres_engine):
    actor, q, query, cooldown_policy, graph = seed(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as reader,
    ):
        old = capture_exposure_preview(reader, q, actor_user_id=actor)
        a = trace_recipe_decay(subject_for(old, query, cooldown_policy))

        def write():
            from app.modules.execution.public import PlanRevisionService

            with Session(postgres_engine) as db:
                service = PlanRevisionService(db)  # Existing proposal facade only.
                data = revise(graph).model_dump()
                data["meals"][-1]["status"] = "RETIRED"
                data["allocations"][-1]["status"] = "RETIRED"
                new_graph = type(graph).model_validate(data)
                service.propose(request(service, actor, new_graph))
                db.commit()

        with ThreadPoolExecutor(1) as pool:
            pool.submit(write).result(timeout=15)
        same = capture_exposure_preview(reader, q, actor_user_id=actor)
        assert same.frontier_hash() == old.frontier_hash()
        assert trace_recipe_decay(subject_for(same, query, cooldown_policy)).entries == a.entries
    fresh = capture(postgres_engine, actor, q)
    with pytest.raises(ValueError, match="plan/proposal"):
        subject_for(fresh, query, cooldown_policy)
    new_query = query.model_copy(update={"proposal_id": fresh.sources[0].proposal.id})
    b = trace_recipe_decay(subject_for(fresh, new_query, cooldown_policy))
    assert not b.entries and b.repeat_penalty == "UNAVAILABLE" and b.global_history == "UNAVAILABLE"
    assert trace_recipe_decay(a.subject).fingerprint() == a.fingerprint()  # Immutable replay.


def test_canonical_zero_rational_retains_real_captured_witness(postgres_engine):
    actor, q, query, cooldown_policy, _ = seed(postgres_engine)
    subject = subject_for(capture(postgres_engine, actor, q), query, cooldown_policy)
    duration = subject.assessment.subject.policy.duration_microseconds
    policy = policy_for(subject.assessment, (band(0, 0, duration, 0, 999),))
    a = trace_recipe_decay(c.RecipeDecayInput(assessment=subject.assessment, policy=policy))
    assert len(a.entries) == 1
    r = a.entries[0].band.retention_multiplier
    assert (r.numerator, r.denominator) == (0, 1)
    assert a.entries[0].witness.fact.proposal_id == query.proposal_id
    assert not a.activation_ready and a.repeat_penalty == "UNAVAILABLE"


@pytest.mark.parametrize(
    "isolation,readonly", [("READ COMMITTED", True), ("REPEATABLE READ", False)]
)
def test_invalid_capture_transaction_cannot_feed_decay(postgres_engine, isolation, readonly):
    actor, q, *_ = seed(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level=isolation, postgresql_readonly=readonly
        ) as conn,
        Session(conn) as db,
        pytest.raises(ValueError, match="read-only"),
    ):
        capture_exposure_preview(db, q, actor_user_id=actor)
