"""Real SQL, causal source history, transactions and concurrency for explicit assertions."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from app.modules.catalog.models import Ingredient
from app.modules.catalog.public import add_affinity_feature_term
from app.modules.households.models import HouseholdMember, Membership
from app.modules.identity.models import User
from app.modules.preferences import contracts as c
from app.modules.preferences import models as m
from app.modules.preferences.public import PreferenceService
from preference_fixtures import provenance, term
from sqlalchemy import event, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from test_foundation_migration import legacy_database as legacy_database
from test_foundation_migration import migrate
from test_postgres_foundation import db as db
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_preferences import seed
from test_postgres_recipes import seed as seed_recipe
from validation_fixtures import simple_recipe_data

pytestmark = pytest.mark.postgres


def replace(q, receipt, **kw):
    fields = q.model_dump(exclude={"action", "contract_version"})
    fields.update(
        expected_revision=receipt.revision_no,
        predecessor_id=receipt.id,
        reason="PREFERENCE_CHANGED",
        provenance=provenance(),
        idempotency_key=uuid4().hex,
    )
    return c.SetMemberPreferenceCommand(**(fields | kw))


def retract(q, receipt):
    return c.RetractMemberPreferenceCommand(
        **(
            q.model_dump(exclude={"action", "value", "reason"})
            | dict(
                expected_revision=receipt.revision_no,
                predecessor_id=receipt.id,
                idempotency_key=uuid4().hex,
                provenance=provenance(),
            )
        )
    )


def read(engine, q):
    with (
        engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as db,
    ):
        return PreferenceService(db, actor_user_id=q.actor_user_id).snapshot(
            q.household_id, q.member_id
        )


def committed(engine):
    with Session(engine) as db:
        svc, q = seed(db)
        a = svc.write(q)
        db.commit()
    return q, a


def test_correction_retraction_restore_and_retry_before_stale_head(db):
    svc, q = seed(db)
    a = svc.write(q)
    bq = replace(q, a, value="NEUTRAL", reason="INPUT_CORRECTION")
    b = svc.write(bq)
    rq = retract(q, b)
    r = svc.write(rq)
    d = svc.write(replace(q, r, value="DISLIKE"))
    assert [x.revision_no for x in (a, b, r, d)] == [0, 1, 2, 3]
    assert svc.write(q) == a and svc.write(rq) == r
    assert db.scalar(select(m.MemberPreferenceFrontier.generation)) == 4
    with pytest.raises(ValueError, match="Idempotency"):
        svc.write(q.model_copy(update=dict(value="DISLIKE")))
    with pytest.raises(ValueError, match="Stale"):
        svc.write(replace(q, a))


def test_double_retraction_rejected(db):
    svc, q = seed(db)
    a = svc.write(q)
    r = svc.write(retract(q, a))
    with pytest.raises(IntegrityError, match="active assertion"), db.begin_nested():
        svc.write(retract(q, r))


def test_direct_recipe_stable_identity(db):
    svc, q = seed(db)
    recipe, _ = seed_recipe(db, simple_recipe_data())
    target = dict(kind="DIRECT_RECIPE", recipe_id=recipe.recipe.id)
    q = c.SetMemberPreferenceCommand.model_validate(q.model_dump() | dict(target=target))
    assert svc.write(q).command.target.recipe_id == recipe.recipe.id


def test_proxy_subject_is_explicit_not_shared_copy(db):
    svc, q = seed(db)
    guest = HouseholdMember(household_id=q.household_id, name="Synthetic guest")
    db.add(guest)
    db.flush()
    with pytest.raises(PermissionError, match="SELF"):
        svc.write(q.model_copy(update=dict(member_id=guest.id)))
    proxy = q.model_copy(update=dict(member_id=guest.id, authorship="AUTHORIZED_REPRESENTATIVE"))
    r = svc.write(proxy)
    assert r.command.member_id == guest.id and r.command.actor_user_id == q.actor_user_id
    assert r.command.authorship == "AUTHORIZED_REPRESENTATIVE"
    assert db.scalar(select(func.count()).select_from(m.MemberPreferenceDeclaration)) == 1
    with pytest.raises(PermissionError, match="principal"):
        PreferenceService(db, actor_user_id=uuid4()).write(q)


@pytest.mark.parametrize("mode", ["viewer", "foreign_actor", "foreign_subject"])
def test_member_actor_scope(db, mode):
    svc, q = seed(db)
    if mode == "viewer":
        db.execute(
            text("UPDATE memberships SET role='VIEWER' WHERE user_id=:a"), dict(a=q.actor_user_id)
        )
    if mode == "foreign_actor":
        svc = PreferenceService(db, actor_user_id=uuid4())
        q = q.model_copy(update=dict(actor_user_id=svc.actor_user_id))
    if mode == "foreign_subject":
        q = q.model_copy(update=dict(member_id=uuid4()))
    with pytest.raises((PermissionError, LookupError)):
        svc.write(q)


def raw(db, receipt):
    row = dict(
        db.execute(
            select(m.MemberPreferenceDeclaration.__table__).where(
                m.MemberPreferenceDeclaration.id == receipt.id
            )
        )
        .mappings()
        .one()
    )
    for k in ("actor_role", "recorded_at", "member_sequence", "command_fingerprint"):
        row.pop(k)
    row.update(
        id=uuid4(),
        revision_no=receipt.revision_no + 1,
        predecessor_id=receipt.id,
        idempotency_key=uuid4().hex,
        external_record_id=str(uuid4()),
        reason="PREFERENCE_CHANGED",
    )
    return row


def raw_insert(db, fields):
    keys = list(fields)
    db.execute(
        text(
            "INSERT INTO member_preference_declarations ("
            + ",".join(keys)
            + ") VALUES ("
            + ",".join(":" + k for k in keys)
            + ")"
        ),
        fields,
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "sequence",
        "recorded",
        "fingerprint",
        "role",
        "household",
        "member",
        "stream",
        "predecessor",
        "revision",
        "source",
        "provenance",
        "authorship",
        "value",
        "reason",
        "future",
        "blank_source",
        "uri",
        "hash",
    ],
)
def test_direct_sql_critical_fact_constraints(db, mutation):
    svc, q = seed(db)
    a = svc.write(q)
    fields = raw(db, a)
    changes = {
        "sequence": dict(member_sequence=0),
        "recorded": dict(recorded_at=a.recorded_at),
        "fingerprint": dict(command_fingerprint="0" * 64),
        "role": dict(actor_role="OWNER"),
        "household": dict(household_id=uuid4()),
        "member": dict(member_id=uuid4()),
        "stream": dict(stream_id=uuid4()),
        "predecessor": dict(predecessor_id=uuid4()),
        "revision": dict(revision_no=99),
        "source": dict(source="INFERRED"),
        "provenance": dict(source_kind="RETAIL_OBSERVATION"),
        "authorship": dict(authorship="INFERRED"),
        "value": dict(value=None),
        "reason": dict(reason="INITIAL"),
        "future": dict(observed_at=datetime.now(UTC) + timedelta(days=2)),
        "blank_source": dict(external_record_id=""),
        "uri": dict(source_uri="javascript:x"),
        "hash": dict(content_hash="invalid"),
    }
    fields.update(changes[mutation])
    with pytest.raises(IntegrityError), db.begin_nested():
        raw_insert(db, fields)
    assert db.scalar(select(m.MemberPreferenceFrontier.generation)) == 1


@pytest.mark.parametrize(
    "table",
    [
        "affinity_feature_terms",
        "member_preference_declarations",
        "member_preference_streams",
        "member_preference_frontiers",
    ],
)
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE"])
def test_history_identity_cache_and_truncate_protection(db, table, operation):
    svc, q = seed(db)
    svc.write(q)
    add_affinity_feature_term(db, term())
    db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    db.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    update = {
        "affinity_feature_terms": "label='changed'",
        "member_preference_declarations": "value='DISLIKE'",
        "member_preference_streams": "head_revision=99",
        "member_preference_frontiers": "generation=99",
    }[table]
    sql = {
        "UPDATE": f"UPDATE {table} SET {update}",
        "DELETE": f"DELETE FROM {table}",
        "TRUNCATE": f"TRUNCATE {table} CASCADE",
    }[operation]
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(text(sql))


@pytest.mark.parametrize(
    "case", ["missing", "draft", "wrong_kind", "mixed_target", "duplicate_target"]
)
def test_typed_target_fk_and_review(db, case):
    svc, q = seed(db)
    t = term(status="DRAFT" if case == "draft" else "REVIEWED")
    add_affinity_feature_term(db, t)
    with pytest.raises(IntegrityError), db.begin_nested():
        if case in {"mixed_target", "duplicate_target"}:
            a = svc.write(q)
            row = dict(
                db.execute(
                    select(m.MemberPreferenceStream.__table__).where(
                        m.MemberPreferenceStream.id == a.stream_id
                    )
                )
                .mappings()
                .one()
            )
            row.update(id=uuid4(), head_revision=-1, head_id=None)
            if case == "mixed_target":
                row["feature_term_id"] = t.id
            db.execute(m.MemberPreferenceStream.__table__.insert().values(**row))
        else:
            target = dict(
                kind="FLAVOR" if case == "wrong_kind" else "METHOD",
                feature_term_id=uuid4() if case == "missing" else t.id,
            )
            svc.write(
                c.SetMemberPreferenceCommand.model_validate(q.model_dump() | dict(target=target))
            )


def test_empty_stream_commit_fails_closed(db):
    _, q = seed(db)
    with pytest.raises(IntegrityError, match="Incomplete"), db.begin_nested():
        db.execute(
            m.MemberPreferenceStream.__table__.insert().values(
                id=uuid4(),
                household_id=q.household_id,
                member_id=q.member_id,
                target_kind="INGREDIENT",
                ingredient_id=q.target.ingredient_id,
            )
        )
        db.execute(text("SET CONSTRAINTS preference_stream_complete IMMEDIATE"))


def test_provider_identity_and_unicode_hash(db):
    svc, q = seed(db)
    q = c.SetMemberPreferenceCommand.model_validate(
        q.model_dump()
        | dict(
            provenance=q.provenance.model_dump()
            | dict(external_record_id='món "ưa thích"/đậu', source_uri="https://example.org")
        )
    )
    a = svc.write(q)
    assert a.command_fingerprint == q.fingerprint()
    b = svc.write(
        replace(
            q, a, provenance=q.provenance.model_copy(update=dict(source_system="other.provider"))
        )
    )
    with pytest.raises(IntegrityError), db.begin_nested():
        svc.write(replace(q, b, provenance=q.provenance))


def test_no_raw_strength_columns_or_global_conversion(db):
    columns = set(
        db.scalars(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='member_preference_declarations'"
            )
        )
    )
    assert not columns & {
        "evidence_strength",
        "strength_basis",
        "assertion_confidence",
        "taste_fit",
    }
    assert (
        db.scalar(
            text(
                "SELECT count(*) FROM information_schema.tables WHERE table_name='unit_conversions'"
            )
        )
        == 0
    )


def test_empty_missing_source_and_wrong_capture_mode(postgres_engine):
    with Session(postgres_engine) as db:
        _, q = seed(db)
        db.commit()
    empty = read(postgres_engine, q)
    assert empty.frontier == 0 and empty.state_for(q.target).status == "UNDECLARED"
    with pytest.raises(LookupError):
        read(postgres_engine, q.model_copy(update=dict(member_id=uuid4())))
    with Session(postgres_engine) as db, pytest.raises(ValueError, match="read-only"):
        PreferenceService(db, actor_user_id=q.actor_user_id).snapshot(q.household_id, q.member_id)


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ"])
def test_concurrent_same_stream_no_lost_update(postgres_engine, isolation):
    q, a = committed(postgres_engine)
    barrier = Barrier(2)
    commands = [replace(q, a, value=value) for value in ("NEUTRAL", "DISLIKE")]

    def writer(cmd):
        with (
            postgres_engine.connect().execution_options(isolation_level=isolation) as conn,
            Session(conn) as db,
        ):
            db.scalar(text("SELECT count(*) FROM member_preference_streams"))
            barrier.wait(timeout=10)
            try:
                result = PreferenceService(db, actor_user_id=q.actor_user_id).write(cmd)
                db.commit()
                return result
            except (ValueError, DBAPIError) as exc:
                db.rollback()
                return exc

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(writer, commands))
    assert sum(isinstance(r, c.MemberPreferenceDeclarationFact) for r in results) == 1
    s = read(postgres_engine, q)
    assert s.frontier == 2 and len(s.declarations) == 2


def test_concurrent_exact_retry_one_fact(postgres_engine):
    q, a = committed(postgres_engine)
    cmd = replace(q, a)
    barrier = Barrier(2)

    def writer(_):
        with Session(postgres_engine) as db:
            barrier.wait(timeout=10)
            result = PreferenceService(db, actor_user_id=q.actor_user_id).write(cmd)
            db.commit()
            return result

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(writer, range(2)))
    assert results[0] == results[1] and read(postgres_engine, q).frontier == 2


def test_different_target_concurrency_new_target_frontier(postgres_engine):
    q, a = committed(postgres_engine)
    with Session(postgres_engine) as db:
        ing = Ingredient(name="Other synthetic ingredient")
        db.add(ing)
        db.flush()
        iid = ing.id
        db.commit()
    new = c.SetMemberPreferenceCommand.model_validate(
        q.model_dump()
        | dict(
            target=dict(kind="INGREDIENT", ingredient_id=iid),
            provenance=provenance(),
            idempotency_key=uuid4().hex,
        )
    )
    barrier = Barrier(2)

    def writer(cmd):
        with Session(postgres_engine) as db:
            barrier.wait(timeout=10)
            r = PreferenceService(db, actor_user_id=q.actor_user_id).write(cmd)
            db.commit()
            return r

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(writer, [new, replace(q, a)]))
    assert {r.member_sequence for r in results} == {2, 3}
    assert read(postgres_engine, q).frontier == 3


def test_permission_revocation_serialized_with_write(postgres_engine):
    q, a = committed(postgres_engine)
    with Session(postgres_engine) as writer, Session(postgres_engine) as changer:
        PreferenceService(writer, actor_user_id=q.actor_user_id).write(replace(q, a))
        changer.execute(text("SET LOCAL lock_timeout='150ms'"))
        with pytest.raises(DBAPIError):
            changer.execute(
                text("UPDATE memberships SET role='VIEWER' WHERE user_id=:a"),
                dict(a=q.actor_user_id),
            )
        changer.rollback()
        writer.commit()
        changer.execute(
            text("UPDATE memberships SET role='VIEWER' WHERE user_id=:a"), dict(a=q.actor_user_id)
        )
        changer.commit()
    with Session(postgres_engine) as db, pytest.raises(PermissionError):
        PreferenceService(db, actor_user_id=q.actor_user_id).write(replace(q, a))


def test_rr_capture_stable_and_independent_replay_zero_io(postgres_engine):
    q, a = committed(postgres_engine)
    with (
        postgres_engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as conn,
        Session(conn) as reader,
    ):
        svc = PreferenceService(reader, actor_user_id=q.actor_user_id)
        old = svc.snapshot(q.household_id, q.member_id)
        with Session(postgres_engine) as writer:
            PreferenceService(writer, actor_user_id=q.actor_user_id).write(
                replace(q, a, value="DISLIKE")
            )
            writer.commit()
        repeated = svc.snapshot(q.household_id, q.member_id)
        assert old.frontier == repeated.frontier == 1 and old.declarations == repeated.declarations
    fresh = read(postgres_engine, q)
    assert fresh.frontier == 2 and old.state_for(q.target).value == "LIKE"
    assert fresh.state_for(q.target).value == "DISLIKE"

    def forbidden(*args):
        raise AssertionError("Live DB inside snapshot replay")

    event.listen(Engine, "before_cursor_execute", forbidden)
    try:
        assert (
            c.ExplicitMemberPreferenceSnapshot.model_validate_json(fresh.canonical_json()) == fresh
        )
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)


def test_migration_empty_and_data_bearing_roundtrip(legacy_database):
    engine, config = legacy_database
    migrate(engine, config, "0010")
    with Session(engine) as db:
        _, q = seed(db)
        db.commit()
    migrate(engine, config, "0011")
    assert read(engine, q).frontier == 0
    migrate(engine, config, "0010", down=True)
    migrate(engine, config, "0011")
    with Session(engine) as db:
        PreferenceService(db, actor_user_id=q.actor_user_id).write(q)
        db.commit()
    with pytest.raises(IntegrityError, match="Lossy preference downgrade"):
        migrate(engine, config, "0010", down=True)
    assert read(engine, q).frontier == 1


def test_feature_version_does_not_retarget_old_declaration(postgres_engine):
    with Session(postgres_engine) as db:
        svc, q = seed(db)
        t = term()
        add_affinity_feature_term(db, t)
        q = c.SetMemberPreferenceCommand.model_validate(
            q.model_dump() | dict(target=dict(kind="METHOD", feature_term_id=t.id))
        )
        a = svc.write(q)
        newer = t.model_copy(
            update=dict(
                id=uuid4(),
                version=2,
                definition="New explicit meaning",
                provenance=provenance(kind="REVIEWED_REFERENCE"),
            )
        )
        add_affinity_feature_term(db, newer)
        db.commit()
    s = read(postgres_engine, q)
    assert s.feature_terms == (t,) and s.declarations == (a,)
    assert s.state_for(dict(kind="METHOD", feature_term_id=newer.id)).status == "UNDECLARED"


def test_history_survives_membership_removal_without_author_rewrite(postgres_engine):
    q, a = committed(postgres_engine)
    with Session(postgres_engine) as db:
        db.execute(
            text("DELETE FROM memberships WHERE household_id=:h AND user_id=:a"),
            dict(h=q.household_id, a=q.actor_user_id),
        )
        new = User(display_name="Synthetic replacement actor")
        db.add(new)
        db.flush()
        new_id = new.id
        db.add(
            Membership(household_id=q.household_id, user_id=new_id, member_id=None, role="OWNER")
        )
        db.commit()
    s = read(postgres_engine, q.model_copy(update=dict(actor_user_id=new_id)))
    assert s.declarations == (a,) and s.declarations[0].command.actor_user_id == q.actor_user_id
    with pytest.raises(PermissionError):
        read(postgres_engine, q)


def test_raw_sql_cannot_bypass_actor_permission(db):
    svc, q = seed(db)
    a = svc.write(q)
    fields = raw(db, a)
    db.execute(
        text("UPDATE memberships SET role='VIEWER' WHERE user_id=:a"), dict(a=q.actor_user_id)
    )
    with pytest.raises(IntegrityError, match="cannot write"), db.begin_nested():
        raw_insert(db, fields)


def test_same_retry_key_cannot_fan_out_to_another_member(db):
    svc, q = seed(db)
    svc.write(q)
    guest = HouseholdMember(household_id=q.household_id, name="Other diner")
    db.add(guest)
    db.flush()
    with pytest.raises(ValueError, match="Idempotency"):
        svc.write(
            q.model_copy(update=dict(member_id=guest.id, authorship="AUTHORIZED_REPRESENTATIVE"))
        )


def test_typed_predecessor_from_other_stream_is_rejected(db):
    svc, q = seed(db)
    a = svc.write(q)
    t = term()
    add_affinity_feature_term(db, t)
    other = c.SetMemberPreferenceCommand.model_validate(
        q.model_dump()
        | dict(
            target=dict(kind="METHOD", feature_term_id=t.id),
            idempotency_key=uuid4().hex,
            provenance=provenance(),
        )
    )
    b = svc.write(other)
    fields = raw(db, a)
    fields["predecessor_id"] = b.id
    with pytest.raises(IntegrityError, match="predecessor"), db.begin_nested():
        raw_insert(db, fields)


def test_vocabulary_only_populated_downgrade_fails_closed(legacy_database):
    engine, config = legacy_database
    migrate(engine, config, "0011")
    with Session(engine) as db:
        add_affinity_feature_term(db, term())
        db.commit()
    with pytest.raises(IntegrityError, match="Lossy preference downgrade"):
        migrate(engine, config, "0010", down=True)
