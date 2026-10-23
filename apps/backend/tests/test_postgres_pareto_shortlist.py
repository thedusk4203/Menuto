"""Canonical ingress and zero-side-effect core, using real PostgreSQL source facts."""

from decimal import Decimal

import pytest
from app.modules.planning.contracts import CandidateGroundingRequest
from app.modules.planning.public import (
    build_pareto_shortlist,
    capture_shortlist_pool,
    shortlist_grounded_pool,
)
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from test_pareto_shortlist import policy
from test_postgres_candidate_grounding import read, seed
from test_postgres_foundation import postgres_engine as postgres_engine

pytestmark = pytest.mark.postgres


def build(engine, requests, p=None):
    with engine.connect().execution_options(
        isolation_level="REPEATABLE READ", postgresql_readonly=True
    ) as conn:
        with Session(conn) as db:
            return build_pareto_shortlist(db, requests, p or policy())


@pytest.mark.parametrize("granularity", ["FIXED_PACK", "CATCH_WEIGHT", "LOOSE_SCALE"])
def test_canonical_capture_and_coverage_no_inventory_reservation_or_source_writes(
    postgres_engine, granularity
):
    q, _ = seed(postgres_engine, granularity)
    narrower = q.model_copy(update=dict(procurement_class_ids=()))
    before = read(postgres_engine, q, sources=True)
    out = build(postgres_engine, (q, narrower))
    after = read(postgres_engine, q, sources=True)
    assert out.status == "COMPLETE" and len(out.candidates) == len(out.dominance) == 1
    assert out.candidates[0].request == q
    assert out.candidates[0].sources == before == after
    assert out == build(postgres_engine, (narrower, q, q))
    assert not out.activation_ready


def test_core_performs_zero_database_queries_or_writes_after_capture(postgres_engine):
    q, _ = seed(postgres_engine)
    with postgres_engine.connect().execution_options(
        isolation_level="REPEATABLE READ", postgresql_readonly=True
    ) as conn:
        with Session(conn) as db:
            pool = capture_shortlist_pool(db, (q,))

    def forbidden(*args):
        raise AssertionError("DB query/write during pure shortlist")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        assert shortlist_grounded_pool(pool, policy()).status == "COMPLETE"
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)


@pytest.mark.parametrize("kind", ["candidate", "result", "forged_quantity", "incomplete"])
def test_noncanonical_or_failed_inputs_cannot_enter_shortlist(postgres_engine, kind):
    q, _ = seed(postgres_engine)
    grounded = read(postgres_engine, q)
    if kind in {"candidate", "result"}:
        raw = grounded.candidate if kind == "candidate" else grounded
        with pytest.raises(ValueError):
            build(postgres_engine, (raw,))
        return
    if kind == "forged_quantity":
        c = q.candidate
        row = c.resolved_ingredients[0]
        row = row.model_copy(
            update=dict(quantity=row.quantity.model_copy(update=dict(amount=Decimal(999))))
        )
        c = c.model_copy(update=dict(resolved_ingredients=(row,)))
        c = c.model_copy(update=dict(fingerprint=c.expected_fingerprint()))
        q = q.model_copy(update=dict(candidate=c))
    else:
        q = CandidateGroundingRequest.model_validate(
            q.model_dump()
            | dict(
                nutrition_selections=[
                    dict(
                        requirement_id=q.candidate.resolved_ingredients[0].requirement_id,
                        reference_id="00000000-0000-0000-0000-000000000000",
                    )
                ]
            )
        )
    out = build(postgres_engine, (q,))
    assert out.status == "GROUNDING_FAILED" and out.candidates == ()
    assert out.failures[0].status == ("REJECTED" if kind == "forged_quantity" else "INCOMPLETE")


def test_capture_requires_clean_coherent_readonly_transaction(postgres_engine):
    q, _ = seed(postgres_engine)
    with Session(postgres_engine) as db, pytest.raises(ValueError, match="read-only"):
        build_pareto_shortlist(db, (q,), policy())


def test_input_budget_rejected_before_any_source_read(postgres_engine):
    q, _ = seed(postgres_engine)
    # No session is usable here; resource failure occurs before canonical capture.
    out = build_pareto_shortlist(None, (q, q), policy(max_inputs=1))
    assert out.status == "INPUT_LIMIT_EXCEEDED" and not out.candidates


def test_frontier_budget_cannot_drop_different_nutrition_selection_provenance(postgres_engine):
    q, ref_id = seed(postgres_engine)
    explicit = CandidateGroundingRequest.model_validate(
        q.model_dump()
        | dict(
            nutrition_selections=[
                dict(
                    requirement_id=q.candidate.resolved_ingredients[0].requirement_id,
                    reference_id=ref_id,
                )
            ]
        )
    )
    out = build(postgres_engine, (q, explicit), policy(max_frontier=1))
    assert out.status == "FRONTIER_LIMIT_EXCEEDED"
    assert out.frontier_count == 2 and out.candidates == ()
