"""Real PostgreSQL proof of canonical identities, isolation, frontiers and no profile writes."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from uuid import uuid4

import pytest
from app.modules.catalog.models import Ingredient
from app.modules.catalog.public import add_affinity_feature_term
from app.modules.households.models import HouseholdMember
from app.modules.preferences import contracts as c
from app.modules.preferences.public import (
    PreferenceService,
    capture_explicit_target_affinity_sources,
    derive_explicit_target_affinity_profile,
)
from app.modules.recipes.contracts import RecipeFact
from app.modules.recipes.repository import RecipeRepository
from preference_fixtures import command, provenance, term
from sqlalchemy import event, inspect, text, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from target_affinity_fixtures import policy
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_foundation import seed_household
from test_postgres_preference_authorship import membership
from test_postgres_preference_integrity import replace, retract

pytestmark = pytest.mark.postgres


@contextmanager
def reader(engine, *, isolation="REPEATABLE READ", readonly=True):
    with (
        engine.connect().execution_options(
            isolation_level=isolation, postgresql_readonly=readonly
        ) as conn,
        Session(conn) as db,
    ):
        yield db


def setup(engine, *, declared=True):
    with Session(engine) as db:
        user, house = seed_household(db)
        ingredient = Ingredient(name="Synthetic target affinity")
        db.add(ingredient)
        db.flush()
        recipe = RecipeFact(id=uuid4(), name="Synthetic stable recipe", cooking_method="synthetic")
        RecipeRepository(db).add_recipe(recipe)  # Deliberately no RecipeVersion.
        terms = tuple(term(k) for k in ("PROTEIN", "METHOD", "FLAVOR"))
        for t in terms:
            add_affinity_feature_term(db, t)
        q = command(
            household_id=house.household_id,
            member_id=house.member_id,
            actor_user_id=user.id,
            target=dict(kind="INGREDIENT", ingredient_id=ingredient.id),
        )
        receipt = PreferenceService(db, actor_user_id=user.id).write(q) if declared else None
        request = c.ExplicitTargetAffinityCaptureRequest(
            household_id=house.household_id,
            member_id=house.member_id,
            requested_targets=(
                q.target,
                c.RecipePreferenceTarget(recipe_id=recipe.id),
                *(c.FeaturePreferenceTarget(kind=t.kind, feature_term_id=t.id) for t in terms),
            ),
        )
        db.commit()
    return q, receipt, request, terms


def capture(db, q, request):
    return capture_explicit_target_affinity_sources(db, request, actor_user_id=q.actor_user_id)


def profile(source):
    return derive_explicit_target_affinity_profile(
        c.ExplicitTargetAffinityInput(source=source, policy=policy())
    )


def row_for(result, target):
    return next(r for r in result.rows if r.target == target)


@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
def test_owner_identity_capture_and_never_declared_targets(postgres_engine, isolation):
    q, receipt, request, terms = setup(postgres_engine)
    with reader(postgres_engine, isolation=isolation) as db:
        source = capture(db, q, request)
        assert db.in_transaction()  # No internal commit or replacement connection.
        result = profile(source)
    assert len(source.manifest.entries) == len(result.rows) == 5
    assert source.preferences.declarations == (receipt,)
    assert row_for(result, q.target).raw_state.value == "LIKE"
    for row in result.rows:
        assert row.prior.status == row.shrunk_affinity.status == "UNAVAILABLE"
        if row.target != q.target:
            assert row.raw_state.status == "UNDECLARED"
            assert row.evidence_strength.level == "NONE"
    assert {
        e.identity.id for e in source.manifest.entries if e.kind in {"PROTEIN", "METHOD", "FLAVOR"}
    } == {t.id for t in terms}


@pytest.mark.parametrize("kind", ["INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"])
def test_random_nonexistent_target_rejected_by_owner_read(postgres_engine, kind):
    q, _, request, _ = setup(postgres_engine)
    field = {"INGREDIENT": "ingredient_id", "DIRECT_RECIPE": "recipe_id"}.get(
        kind, "feature_term_id"
    )
    bad = c.ExplicitTargetAffinityCaptureRequest(
        **(request.model_dump() | dict(requested_targets=(dict(kind=kind, **{field: uuid4()}),)))
    )
    with (
        reader(postgres_engine) as db,
        pytest.raises(ValueError, match="TARGET_IDENTITY_UNRESOLVED"),
    ):
        capture(db, q, bad)


@pytest.mark.parametrize(
    "case", ["draft", "wrong_kind", "missing_member", "foreign_member", "actor"]
)
def test_capture_rejects_invalid_owner_or_term(postgres_engine, case):
    q, _, request, terms = setup(postgres_engine)
    if case == "draft":
        t = term(status="DRAFT")
        with Session(postgres_engine) as db:
            add_affinity_feature_term(db, t)
            db.commit()
        request = request.model_copy(
            update=dict(
                requested_targets=(c.FeaturePreferenceTarget(kind=t.kind, feature_term_id=t.id),)
            )
        )
    if case == "wrong_kind":
        request = request.model_copy(
            update=dict(
                requested_targets=(
                    c.FeaturePreferenceTarget(kind="METHOD", feature_term_id=terms[0].id),
                )
            )
        )
    if case == "missing_member":
        request = request.model_copy(update=dict(member_id=uuid4()))
    if case == "foreign_member":
        _, _, other, _ = setup(postgres_engine)
        request = request.model_copy(update=dict(member_id=other.member_id))
    if case == "actor":
        q = q.model_copy(update=dict(actor_user_id=uuid4()))
    with reader(postgres_engine) as db, pytest.raises((ValueError, LookupError, PermissionError)):
        capture(db, q, request)


@pytest.mark.parametrize("case", ["read_committed", "writable", "new", "dirty", "deleted"])
def test_capture_requires_clean_readonly_repeatable_transaction(postgres_engine, case):
    q, _, request, _ = setup(postgres_engine)
    with reader(
        postgres_engine,
        isolation="READ COMMITTED" if case == "read_committed" else "REPEATABLE READ",
        readonly=case != "writable",
    ) as db:
        if case == "new":
            db.add(Ingredient(name="Pending synthetic ingredient"))
        if case in {"dirty", "deleted"}:
            row = db.get(Ingredient, q.target.ingredient_id)
            if case == "dirty":
                row.name = "Pending edit"
            else:
                db.delete(row)
        with pytest.raises(ValueError, match="clean read-only"):
            capture(db, q, request)


def test_hundred_idempotent_retries_do_not_change_frontier_or_strength(postgres_engine):
    q, first, request, _ = setup(postgres_engine)
    with reader(postgres_engine) as db:
        before = capture(db, q, request)
    with Session(postgres_engine) as db:
        svc = PreferenceService(db, actor_user_id=q.actor_user_id)
        for _ in range(100):
            assert svc.write(q) == first
        db.commit()
    with reader(postgres_engine) as db:
        after = capture(db, q, request)
    assert before.preferences.declarations == after.preferences.declarations == (first,)
    assert before.preferences.frontier == after.preferences.frontier == 1
    assert profile(before).rows == profile(after).rows
    assert row_for(profile(after), q.target).evidence_strength.level == "LOW"


@pytest.mark.parametrize("mode", ["correction", "neutral", "retract"])
def test_real_head_replacements_preserve_full_history(postgres_engine, mode):
    q, first, request, _ = setup(postgres_engine)
    with Session(postgres_engine) as db:
        svc = PreferenceService(db, actor_user_id=q.actor_user_id)
        nextq = (
            retract(q, first)
            if mode == "retract"
            else replace(
                q,
                first,
                value="NEUTRAL" if mode == "neutral" else "DISLIKE",
                reason="PREFERENCE_CHANGED" if mode == "neutral" else "INPUT_CORRECTION",
            )
        )
        second = svc.write(nextq)
        db.commit()
    with reader(postgres_engine) as db:
        source = capture(db, q, request)
    assert source.preferences.declarations == (first, second)
    row = row_for(profile(source), q.target)
    assert row.current_declaration == second
    if mode == "retract":
        assert row.raw_state.status == "RETRACTED" and row.evidence_strength.level == "NONE"
    else:
        assert row.raw_state.value == nextq.value and row.evidence_strength.level == "LOW"
        if mode == "neutral":
            assert row.affinity.status == "AVAILABLE" and row.affinity.amount.numerator == 0


@pytest.mark.parametrize("empty", [True, False])
def test_requested_scope_never_trims_full_raw_history(postgres_engine, empty):
    q, first, request, _ = setup(postgres_engine)
    with Session(postgres_engine) as db:
        target = next(t for t in request.requested_targets if t.kind == "FLAVOR")
        extra = command(
            **(
                q.model_dump(exclude={"action", "contract_version"})
                | dict(target=target, idempotency_key=uuid4().hex, provenance=provenance())
            )
        )
        second = PreferenceService(db, actor_user_id=q.actor_user_id).write(extra)
        db.commit()
    request = request.model_copy(update=dict(requested_targets=() if empty else (q.target,)))
    with reader(postgres_engine) as db:
        source = capture(db, q, request)
    assert source.preferences.declarations == (first, second)
    assert source.preferences.frontier == 2
    assert len(profile(source).rows) == (0 if empty else 1)
    assert source.preferences.feature_terms  # Retained even when requested set has no terms.


def test_same_code_new_id_does_not_gain_old_term_assertion(postgres_engine):
    q, _, request, terms = setup(postgres_engine, declared=False)
    old = terms[0]
    new = term(old.kind, code=old.code, version=2)
    with Session(postgres_engine) as db:
        add_affinity_feature_term(db, new)
        q = command(
            **(
                q.model_dump(exclude={"action", "contract_version"})
                | dict(target=dict(kind=old.kind, feature_term_id=old.id))
            )
        )
        PreferenceService(db, actor_user_id=q.actor_user_id).write(q)
        db.commit()
    new_target = c.FeaturePreferenceTarget(kind=new.kind, feature_term_id=new.id)
    request = request.model_copy(update=dict(requested_targets=(q.target, new_target)))
    with reader(postgres_engine) as db:
        result = profile(capture(db, q, request))
    assert row_for(result, q.target).raw_state.status == "DECLARED"
    assert row_for(result, new_target).raw_state.status == "UNDECLARED"


def test_members_are_independent_and_membership_changes_preserve_authorship(postgres_engine):
    q, first, request, _ = setup(postgres_engine)
    with Session(postgres_engine) as db:
        guest = HouseholdMember(household_id=q.household_id, name="Synthetic proxy subject")
        db.add(guest)
        db.flush()
        guest_id = guest.id
        db.commit()
    other_request = request.model_copy(update=dict(member_id=guest_id))
    with reader(postgres_engine) as db:
        untouched = capture(db, q, other_request)
    with Session(postgres_engine) as db:
        svc = PreferenceService(db, actor_user_id=q.actor_user_id)
        svc.write(replace(q, first, value="DISLIKE"))
        db.commit()
    with reader(postgres_engine) as db:
        unchanged = capture(db, q, other_request)
    assert untouched.preferences.declarations == unchanged.preferences.declarations == ()
    assert profile(untouched).rows == profile(unchanged).rows
    with Session(postgres_engine) as db:
        proxy = command(
            **(
                q.model_dump(exclude={"action", "contract_version"})
                | dict(
                    member_id=guest_id,
                    authorship="AUTHORIZED_REPRESENTATIVE",
                    idempotency_key=uuid4().hex,
                    provenance=provenance(),
                )
            )
        )
        receipt = PreferenceService(db, actor_user_id=q.actor_user_id).write(proxy)
        # Later actor now links to guest and has a different role. Do not rewrite old facts.
        membership(db, proxy, "same", "VIEWER")
        db.commit()
    with reader(postgres_engine) as db:
        original = capture(db, q, request)
        other = capture(db, q, other_request)
    assert original.preferences.declarations[0] == first
    assert first.command.authorship == "SELF" and first.actor_role == "OWNER"
    row = row_for(profile(other), q.target)
    assert row.current_declaration == receipt
    assert row.current_declaration.command.authorship == "AUTHORIZED_REPRESENTATIVE"
    assert row.current_declaration.actor_role == "OWNER"
    assert row.evidence_strength.level == "HIGH"  # Only this fixture's explicit proxy mapping.


@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
def test_old_capture_coherent_during_concurrent_declaration_and_identity_edit(
    postgres_engine, monkeypatch, isolation
):
    from app.modules.preferences import profile_capture as adapter

    q, first, request, _ = setup(postgres_engine)
    original_read = adapter.ingredient_identities
    changed = []

    def writer():
        with Session(postgres_engine) as db:
            receipt = PreferenceService(db, actor_user_id=q.actor_user_id).write(
                replace(q, first, value="DISLIKE")
            )
            db.execute(
                update(Ingredient)
                .where(Ingredient.id == q.target.ingredient_id)
                .values(name="Concurrent canonical name")
            )
            db.commit()
            return receipt

    def during_owner_read(session, ids):
        # Actual separate PostgreSQL transaction commits between preference and identity reads.
        with ThreadPoolExecutor(max_workers=1) as pool:
            changed.append(pool.submit(writer).result(timeout=15))
        return original_read(session, ids)

    with monkeypatch.context() as patch:
        patch.setattr(adapter, "ingredient_identities", during_owner_read)
        with reader(postgres_engine, isolation=isolation) as db:
            old = capture(db, q, request)
    with reader(postgres_engine, isolation=isolation) as db:
        fresh = capture(db, q, request)
    assert old.preferences.declarations == (first,) and old.preferences.frontier == 1
    assert fresh.preferences.declarations == (first, changed[0]) and fresh.preferences.frontier == 2
    old_identity = next(e.identity for e in old.manifest.entries if e.kind == "INGREDIENT")
    fresh_identity = next(e.identity for e in fresh.manifest.entries if e.kind == "INGREDIENT")
    assert old_identity.name == "Synthetic target affinity"
    assert fresh_identity.name == "Concurrent canonical name"
    assert row_for(profile(old), q.target).raw_state.value == "LIKE"
    assert row_for(profile(fresh), q.target).raw_state.value == "DISLIKE"
    assert profile(old).source_fingerprint != profile(fresh).source_fingerprint


def test_identity_insert_after_rr_cut_is_not_visible_until_fresh_capture(postgres_engine):
    q, _, request, _ = setup(postgres_engine)
    identity = uuid4()
    request = request.model_copy(
        update=dict(requested_targets=(c.IngredientPreferenceTarget(ingredient_id=identity),))
    )
    with reader(postgres_engine) as db:
        db.scalar(text("SELECT count(*) FROM ingredients"))  # Establish old RR cut.
        with Session(postgres_engine) as writer:
            writer.add(Ingredient(id=identity, name="Inserted after old cut"))
            writer.commit()
        with pytest.raises(ValueError, match="TARGET_IDENTITY_UNRESOLVED"):
            capture(db, q, request)
    with reader(postgres_engine) as db:
        assert profile(capture(db, q, request)).rows[0].raw_state.status == "UNDECLARED"


def test_capture_and_derivation_only_read_without_schema_or_row_changes(postgres_engine):
    q, _, request, _ = setup(postgres_engine)

    def stored():
        with postgres_engine.connect() as conn:
            tables = inspect(conn).get_table_names()
            assert len(tables) == 99 and "alembic_version" in tables
            assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0016"
            return {
                t: conn.execute(text(f'SELECT to_jsonb(t)::text FROM "{t}" t ORDER BY 1')).all()
                for t in tables
            }

    before = stored()
    statements = []

    def sql(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(Engine, "before_cursor_execute", sql)
    try:
        with reader(postgres_engine) as db:
            source = capture(db, q, request)
        assert statements
        assert {s.lstrip().split()[0].upper() for s in statements} <= {"SELECT", "SHOW"}
        assert not any("FOR UPDATE" in s.upper() or "ADVISORY" in s.upper() for s in statements)
        count = len(statements)
        profile(source)
        assert len(statements) == count
    finally:
        event.remove(Engine, "before_cursor_execute", sql)
    assert before == stored()


def test_feature_exposure_proposals_cannot_change_explicit_profile(postgres_engine):
    from app.modules.planning.public import PlanStore
    from test_postgres_feature_exposure import capture as capture_exposure
    from test_postgres_feature_exposure import setup as setup_exposure

    actor, exposure_request, _, terms = setup_exposure(postgres_engine)
    with Session(postgres_engine) as db:
        workspace, _ = PlanStore(db).latest_proposal_source(
            exposure_request.household_id, exposure_request.plan_id
        )
    request = c.ExplicitTargetAffinityCaptureRequest(
        household_id=workspace.household_id,
        member_id=workspace.tracked_member_id,
        requested_targets=(dict(kind="FLAVOR", feature_term_id=terms[0].id),),
    )
    with reader(postgres_engine) as db:
        before = capture_explicit_target_affinity_sources(db, request, actor_user_id=actor)
    # Replaying real captured 041E source does not create preference observations.
    from app.modules.learning.public import preview_feature_exposure

    exposure = capture_exposure(postgres_engine, actor, exposure_request)
    for _ in range(100):
        preview_feature_exposure(exposure)
    with reader(postgres_engine) as db:
        after = capture_explicit_target_affinity_sources(db, request, actor_user_id=actor)
    assert before.preferences.declarations == after.preferences.declarations == ()
    assert profile(before).rows == profile(after).rows
