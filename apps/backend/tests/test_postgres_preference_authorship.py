"""Authorship is an exact claim about the canonical membership, never a caller label."""

import pytest
from app.modules.households.models import HouseholdMember
from app.modules.preferences import models as m
from app.modules.preferences.public import PreferenceService
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_foundation_migration import legacy_database as legacy_database
from test_foundation_migration import migrate
from test_postgres_foundation import db as db
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_preference_integrity import raw, raw_insert, read, replace
from test_postgres_preferences import seed

pytestmark = pytest.mark.postgres


# Same matrix reaches the application path and direct SQL independently.
CASES = [
    ("same", "OWNER", "SELF", True),
    ("different", "EDITOR", "SELF", False),
    ("none", "OWNER", "SELF", False),
    ("different", "OWNER", "AUTHORIZED_REPRESENTATIVE", True),
    ("different", "EDITOR", "AUTHORIZED_REPRESENTATIVE", True),
    ("same", "OWNER", "AUTHORIZED_REPRESENTATIVE", False),
    ("same", "EDITOR", "AUTHORIZED_REPRESENTATIVE", False),
    ("none", "OWNER", "AUTHORIZED_REPRESENTATIVE", True),
    ("none", "EDITOR", "AUTHORIZED_REPRESENTATIVE", True),
    ("different", "VIEWER", "AUTHORIZED_REPRESENTATIVE", False),
    ("none", "VIEWER", "AUTHORIZED_REPRESENTATIVE", False),
    ("same", "VIEWER", "SELF", False),
]


def membership(db, q, linked, role):
    member_id = q.member_id if linked == "same" else None
    if linked == "different":
        other = HouseholdMember(household_id=q.household_id, name="Another synthetic member")
        db.add(other)
        db.flush()
        member_id = other.id
    db.execute(
        text("UPDATE memberships SET member_id=:m,role=:r WHERE household_id=:h AND user_id=:a"),
        dict(m=member_id, r=role, h=q.household_id, a=q.actor_user_id),
    )


@pytest.mark.parametrize("linked,role,authorship,allowed", CASES)
def test_service_authorship_exact_match(db, linked, role, authorship, allowed):
    svc, q = seed(db)
    first = svc.write(q)
    membership(db, q, linked, role)
    command = replace(q, first, authorship=authorship)
    if allowed:
        receipt = svc.write(command)
        assert receipt.command.authorship == authorship  # No silent normalization.
        assert receipt.command.member_id == q.member_id
    else:
        with pytest.raises(PermissionError), db.begin_nested():
            svc.write(command)
    assert db.scalar(select(func.count()).select_from(m.MemberPreferenceDeclaration)) == (
        2 if allowed else 1
    )


def stored_state(engine):
    """Compare every preference row, including audit/hash/cache values, across DDL."""
    with engine.connect() as conn:
        tables = (
            "affinity_feature_terms",
            "member_preference_streams",
            "member_preference_declarations",
            "member_preference_frontiers",
        )
        rows = {
            name: conn.execute(text(f"SELECT * FROM {name} t ORDER BY to_jsonb(t)::text")).all()
            for name in tables
        }
        functions = dict(
            conn.execute(
                text(
                    "SELECT proname,pg_get_functiondef(oid) FROM pg_proc "
                    "WHERE pronamespace='public'::regnamespace "
                    "AND proname LIKE 'menuto_preference_%'"
                )
            ).all()
        )
        oid = conn.scalar(text("SELECT 'menuto_preference_append()'::regprocedure::oid"))
        return rows, functions, oid


@pytest.mark.parametrize("populated", [False, True])
def test_authorship_migration_roundtrip_preserves_history(legacy_database, populated):
    engine, config = legacy_database
    migrate(engine, config, "0011")
    if populated:
        with Session(engine) as db:
            svc, q = seed(db)
            first = svc.write(q)
            # Persist the exact old defect through frozen 0011 SQL, not the corrected service.
            wrong = raw(db, first) | dict(authorship="AUTHORIZED_REPRESENTATIVE")
            raw_insert(db, wrong)
            db.commit()
        history = read(engine, q)
        assert [d.command.authorship for d in history.declarations] == [
            "SELF",
            "AUTHORIZED_REPRESENTATIVE",
        ]
    before_rows, before_functions, before_oid = stored_state(engine)
    for revision, down in (("0012", False), ("0011", True), ("0012", False)):
        migrate(engine, config, revision, down=down)
        rows, functions, oid = stored_state(engine)
        assert rows == before_rows and oid == before_oid
        old_append = before_functions["menuto_preference_append"]
        append = functions.pop("menuto_preference_append")
        assert functions == {
            k: v for k, v in before_functions.items() if k != "menuto_preference_append"
        }
        assert (append == old_append) == (revision == "0011")
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT version_num FROM alembic_version")) == revision
            assert (
                conn.scalar(
                    text(
                        "SELECT count(*) FROM information_schema.tables "
                        "WHERE table_schema='public' AND table_type='BASE TABLE' "
                        "AND table_name<>'alembic_version'"
                    )
                )
                == 58
            )
        if populated:
            # Preserve even historically mislabeled facts; never relabel/re-hash them.
            assert read(engine, q).declarations == history.declarations
            with Session(engine) as db:
                latest = history.declarations[-1]
                fields = raw(db, latest) | dict(authorship="AUTHORIZED_REPRESENTATIVE")
                if revision == "0011":
                    raw_insert(db, fields)  # Downgrade restores actual old acceptance semantics.
                else:
                    with pytest.raises(IntegrityError, match="REPRESENTATIVE"), db.begin_nested():
                        raw_insert(db, fields)
                    # Correct SELF replacement is still possible on that historical stream.
                    receipt = PreferenceService(db, actor_user_id=q.actor_user_id).write(
                        replace(q, latest)
                    )
                    assert receipt.command.authorship == "SELF"
                db.rollback()  # Probes never change the historical rows used in the roundtrip.
    assert stored_state(engine)[0] == before_rows


@pytest.mark.parametrize("linked,role,authorship,allowed", CASES)
def test_sql_authorship_exact_match(db, linked, role, authorship, allowed):
    svc, q = seed(db)
    first = svc.write(q)
    fields = raw(db, first) | dict(authorship=authorship)
    membership(db, q, linked, role)
    if allowed:
        raw_insert(db, fields)
        assert (
            db.scalar(
                select(m.MemberPreferenceDeclaration.authorship).where(
                    m.MemberPreferenceDeclaration.id == fields["id"]
                )
            )
            == authorship
        )
    else:
        error = "cannot write" if role == "VIEWER" else "SELF|REPRESENTATIVE"
        with pytest.raises(IntegrityError, match=error), db.begin_nested():
            raw_insert(db, fields)
    assert db.scalar(select(func.count()).select_from(m.MemberPreferenceDeclaration)) == (
        2 if allowed else 1
    )
