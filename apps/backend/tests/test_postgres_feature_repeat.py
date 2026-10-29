"""041F on real PostgreSQL: old/fresh source cuts, concurrent owner writes, no persistence."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from app.modules.catalog.public import (
    IngredientProteinService,
    add_affinity_feature_term,
    ingredient_protein_frontier,
    ingredient_protein_sources,
)
from app.modules.execution.public import PlanRevisionService
from app.modules.learning import contracts as c
from app.modules.learning.public import (
    assess_feature_cooldown,
    interpret_feature_repeat_penalty,
    preview_feature_exposure,
)
from app.modules.planning import contracts as p
from app.modules.planning import feature_exposure_capture as adapter
from app.modules.planning.public import PlanStore
from app.modules.recipes.public import (
    CulinaryFeatureService,
    authored_version,
    culinary_feature_frontier,
    culinary_feature_sources,
)
from feature_fixtures import review_command
from feature_repeat_fixtures import HOUR, query_for, stages
from preference_fixtures import term
from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from test_postgres_culinary_bindings import request as plan_request
from test_postgres_culinary_features import nextq
from test_postgres_feature_exposure import capture, setup
from test_postgres_foundation import postgres_engine as postgres_engine

pytestmark = pytest.mark.postgres


def repeat_plan(engine, dimension="FLAVOR", *, mixed=False):
    actor, old_request, receipt, terms = setup(engine, dimension)
    with Session(engine) as db:
        _, previous = PlanStore(db).latest_proposal_source(
            old_request.household_id, old_request.plan_id
        )
        recipe = authored_version(db, previous.graph.batches[0].recipe_version_id)
        bindings = tuple(
            b.model_copy(update={"proposal_id": uuid4()}) for b in previous.graph.culinary_bindings
        )
        bindings = tuple(
            b.model_copy(update={"fingerprint": b.expected_fingerprint()}) for b in bindings
        )
        gd = previous.graph.model_dump() | dict(culinary_bindings=bindings)
        first = gd["meals"][0]["scheduled_at"]
        for n, meal in enumerate(gd["meals"]):
            meal.update(meal_kind="HOME", scheduled_at=first + timedelta(hours=n))
        gd["allocations"] = tuple(
            dict(
                node_id=previous.graph.allocations[0].node_id if n == 0 else uuid4(),
                batch_node_id=gd["batches"][0]["node_id"],
                meal_node_id=m["node_id"],
                servings=1,
            )
            for n, m in enumerate(gd["meals"])
        )
        graph = p.BoundPlanIntentGraph.model_validate(gd)
        service = PlanRevisionService(db)  # Existing intent authoring; no Execution changes.
        proposal = service.propose(plan_request(service, actor, graph))
        dimensions = (dimension,)
        if mixed:
            assert dimension == "MAIN_PROTEIN"
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
            dimensions = ("METHOD", "FLAVOR", "MAIN_PROTEIN")
        db.commit()
    return (
        actor,
        old_request.model_copy(
            update={
                "proposal_id": proposal.id,
                "proposal_hash": proposal.graph_hash,
                "requested_dimensions": dimensions,
            }
        ),
        receipt,
        terms,
    )


def reinterpret(preview, result):
    # Preserve the exact explicit policies and rebind only a newly captured source/query.
    subject = result.subject.model_dump()
    cd = subject["trace"]["subject"]["assessment"]["subject"]
    query = query_for(
        preview, dimension=cd["query"]["dimension"], term_id=cd["query"]["feature_term_id"]
    )
    a = assess_feature_cooldown(
        c.FeatureCooldownInput(
            preview=preview,
            query=query,
            policy=cd["policy"],
        )
    )
    from app.modules.learning.public import trace_feature_decay

    trace = trace_feature_decay(
        c.FeatureDecayInput(assessment=a, policy=subject["trace"]["subject"]["policy"])
    )
    return interpret_feature_repeat_penalty(
        c.FeatureRepeatPenaltyInput(trace=trace, policy=subject["policy"])
    )


@pytest.mark.parametrize("dimension", ["METHOD", "MAIN_PROTEIN", "FLAVOR"])
@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
def test_cases03_36_41_real_capture_zero_io_and_no_occurrence_inflation(
    postgres_engine, dimension, isolation
):
    actor, q, receipt, _ = repeat_plan(postgres_engine, dimension)
    tables = (
        "plan_proposals",
        "plan_revisions",
        "inventory_movements",
        "inventory_reservations",
        "member_preference_declarations",
        "culinary_feature_reviews",
    )

    def counts():
        with postgres_engine.connect() as db:
            return {t: db.scalar(text(f"SELECT count(*) FROM {t}")) for t in tables}

    before = counts()
    source = capture(postgres_engine, actor, q, isolation)

    def forbidden(*args, **kwargs):
        raise AssertionError("SQL during pure 041F interpretation")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        pre = preview_feature_exposure(source)
        a, t, result = stages(pre, duration=2 * HOUR)
        again = interpret_feature_repeat_penalty(result.subject)
        assert again.fingerprint() == result.fingerprint()
        assert len(a.witnesses) == len(t.entries) == len(result.contributions) == 1
        assert a.witnesses[0].fact.support[0].assignment.review_id == receipt.review_id
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)
    assert counts() == before
    with postgres_engine.connect() as db:
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0016"
        assert len(set(inspect(db).get_table_names()) - {"alembic_version"}) == 98


@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
@pytest.mark.parametrize("change", ["proposal", "classification", "association"])
def test_cases37_38_owner_write_between_member_and_classification_reads(
    postgres_engine, monkeypatch, isolation, change
):
    dimension = "MAIN_PROTEIN" if change == "association" else "FLAVOR"
    actor, q, receipt, _ = repeat_plan(postgres_engine, dimension)
    old_pre = preview_feature_exposure(capture(postgres_engine, actor, q, isolation))
    _, _, result = stages(old_pre)
    recipe = old_pre.snapshot.classification_sources[0].subject.evaluation.recipe
    new_proposal = None

    def write():
        nonlocal new_proposal
        with Session(postgres_engine) as db:
            if change == "proposal":
                _, prior = PlanStore(db).latest_proposal_source(q.household_id, q.plan_id)
                bindings = tuple(
                    b.model_copy(update={"proposal_id": uuid4()})
                    for b in prior.graph.culinary_bindings
                )
                bindings = tuple(
                    b.model_copy(update={"fingerprint": b.expected_fingerprint()}) for b in bindings
                )
                graph = p.BoundPlanIntentGraph.model_validate(
                    prior.graph.model_dump() | dict(culinary_bindings=bindings)
                )
                svc = PlanRevisionService(db)
                new_proposal = svc.propose(plan_request(svc, actor, graph))
            elif change == "classification":
                sc = culinary_feature_sources(db, recipe.id, (dimension,))[0]
                cmd = nextq(
                    sc.reviews[-1].command,
                    receipt,
                    frontier=culinary_feature_frontier(db),
                    positive_term_ids=(),
                )
                CulinaryFeatureService(db, actor_user_id=actor).write(cmd)
            else:
                sc = ingredient_protein_sources(db, (recipe.ingredients[0].ingredient_id,))[0]
                prior = sc.reviews[-1]
                cmd = nextq(
                    prior.command,
                    type("Receipt", (), {"review_id": prior.id})(),
                    frontier=ingredient_protein_frontier(db),
                )
                IngredientProteinService(db, actor_user_id=actor).write(cmd)
            db.commit()

    original = adapter.capture_culinary_feature_subject
    fired = False

    def interleave(*args, **kwargs):
        nonlocal fired
        if not fired:
            fired = True
            with ThreadPoolExecutor() as pool:
                pool.submit(write).result(timeout=15)
        return original(*args, **kwargs)

    monkeypatch.setattr(adapter, "capture_culinary_feature_subject", interleave)
    captured = capture(postgres_engine, actor, q, isolation)
    assert fired
    old = preview_feature_exposure(captured)
    replay = reinterpret(old, result)
    assert (
        replay.proposal_local_feature_repeat_penalty == result.proposal_local_feature_repeat_penalty
    )
    assert old.evidence_cuts == old_pre.evidence_cuts
    assert len(replay.contributions) == 1
    if change == "proposal":
        with pytest.raises(ValueError, match="stale"):
            capture(postgres_engine, actor, q, isolation)
        q = q.model_copy(
            update={"proposal_id": new_proposal.id, "proposal_hash": new_proposal.graph_hash}
        )
        fresh = preview_feature_exposure(capture(postgres_engine, actor, q, isolation))
        assert (
            reinterpret(fresh, result).proposal_local_feature_repeat_penalty
            == result.proposal_local_feature_repeat_penalty
        )
        assert fresh.fingerprint() != old.fingerprint()
    else:
        fresh = preview_feature_exposure(capture(postgres_engine, actor, q, isolation))
        assert not fresh.events
        expected = "STALE_ASSOCIATION" if change == "association" else None
        assert all(d.discovery.reason == expected for d in fresh.diagnostics)
        raw = result.subject.trace.subject.assessment.subject.model_dump() | dict(preview=fresh)
        with pytest.raises(ValueError, match="TARGET_FEATURE_UNRESOLVED|TARGET_NOT_PRESENT"):
            assess_feature_cooldown(c.FeatureCooldownInput.model_validate(raw))
    # Replay of the immutable original is still coherent after all owner changes.
    assert interpret_feature_repeat_penalty(result.subject).fingerprint() == result.fingerprint()


def test_cases31_39_unrelated_catalog_frontier_and_dimension_clocks(postgres_engine):
    actor, q, _, _ = repeat_plan(postgres_engine, "MAIN_PROTEIN", mixed=True)
    old = preview_feature_exposure(capture(postgres_engine, actor, q))
    outcomes = {}
    for d in ("METHOD", "FLAVOR", "MAIN_PROTEIN"):
        target = max((e for e in old.events if e.dimension == d), key=lambda e: e.scheduled_at)
        outcomes[d] = stages(old, query=query_for(old, target=target))[2]
    recipe = old.snapshot.classification_sources[0].subject.evaluation.recipe
    with Session(postgres_engine) as db:
        stream = ingredient_protein_sources(db, (recipe.ingredients[0].ingredient_id,))[0]
        prior = stream.reviews[-1]
        cmd = nextq(
            prior.command,
            type("Receipt", (), {"review_id": prior.id})(),
            frontier=ingredient_protein_frontier(db),
        )
        IngredientProteinService(db, actor_user_id=actor).write(cmd)
        db.commit()
    fresh = preview_feature_exposure(capture(postgres_engine, actor, q))
    for d in ("METHOD", "FLAVOR"):
        current = reinterpret(fresh, outcomes[d])
        assert (
            current.proposal_local_feature_repeat_penalty
            == outcomes[d].proposal_local_feature_repeat_penalty
        )
        assert current.dimension_evidence_cut_digest == outcomes[d].dimension_evidence_cut_digest
        # Other dimensions' clocks cannot tighten this atomic dimension's cutoff.
        data = old.model_dump()
        for child in data["snapshot"]["classification_sources"]:
            if child["subject"]["request"]["requested_dimensions"] != (d,):
                child["subject"]["evaluation"]["captured_at"] -= timedelta(milliseconds=10)
                from app.modules.planning.feature_preview import (
                    discover_culinary_feature_assignments,
                )

                child.update(
                    discover_culinary_feature_assignments(
                        p.CapturedCulinaryFeatureSubjectDraft.model_validate(child["subject"])
                    ).model_dump()
                )
        source = c.FeatureExposureSourceSnapshotDraft.model_validate(data["snapshot"])
        shifted = preview_feature_exposure(source)
        base = outcomes[d].subject.trace.subject.assessment
        assert (
            reinterpret(shifted, outcomes[d]).subject.trace.subject.assessment.policy_cutoff
            == base.policy_cutoff
        )
    assert not any(e.dimension == "MAIN_PROTEIN" for e in fresh.events)
    assert any(d.discovery.reason == "STALE_ASSOCIATION" for d in fresh.diagnostics)
