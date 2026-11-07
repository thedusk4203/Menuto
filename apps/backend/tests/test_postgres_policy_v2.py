"""PIV-PG01–PG10 execute protected readers and real transaction/admission paths."""

import pytest
from app.modules.nutrition import policy_v2_contracts as v
from app.modules.planning import policy_v2_capture as host
from basis_postgres_fixtures import mba_case, nre_case  # noqa: F401
from nutrition_root_postgres_fixtures import nrc_server, reader  # noqa: F401
from policy_v2_postgres_fixtures import piv_case  # noqa: F401
from test_postgres_foundation import postgres_engine  # noqa: F401

pytestmark = pytest.mark.postgres


def use_for(s):
    q = s["basis_selectors"].nre_scope
    return v.PolicyV2Use(
        purpose="STRUCTURAL_TEST_ONLY_INSPECTION",
        subject=q.subject,
        actor_user_id=q.actor_user_id,
        selector_fingerprint=v.policy_v2_hash("selectors", s["basis_selectors"]),
        precision_fingerprint=v.policy_v2_hash("precision", q.precision),
        environment="TEST_ONLY",
    )


@pytest.mark.parametrize("piv_case", ["DAY", "WEEK"], indirect=True)
@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
def test_piv_pg01_capture_to_exactly_once_use(piv_case, isolation):  # noqa: F811
    s = piv_case
    with reader(s, "self", isolation=isolation) as db:
        lease = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        assert not isinstance(lease, v.PolicyV2CaptureFailure), lease
        entry = host._ACTIVE[lease]
        h = host.consume_test_policy_v2(lease, use_for(s))
        if not isinstance(h, v.NutritionPolicyHandoffV2):
            from app.domain.feature_identity import canonical
            from app.modules.validation.nutrition_policy_v2 import check_policy_v2

            pytest.fail(
                str(
                    dict(
                        failure=canonical(h),
                        retained=canonical(entry.result),
                        independently_rechecked=canonical(
                            check_policy_v2(entry.input, entry.result)
                        ),
                    )
                )
            )
        assert h.result.outcome == "AVAILABLE_TEST_ONLY"
        assert h.retained_check.decision == "CONSISTENT"
        assert h.validation_authority == "UNVERIFIED_TRANSPORT"
        assert (
            host.consume_test_policy_v2(lease, use_for(s)).diagnostics[0].code == "CONSUME_REPLAY"
        )


@pytest.mark.parametrize(
    "who,change",
    [
        ("root", "none"),
        ("self", "set_role"),
        ("other", "none"),
        ("self", "foreign_context"),
        ("self", "writable_schema"),
    ],
)
def test_piv_pg02_actual_identity_and_unsafe_reader(piv_case, who, change):  # noqa: F811
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    s = piv_case
    if change == "writable_schema":
        from psycopg import sql

        with s["engines"]["root"].begin() as admin:
            driver = admin.connection.driver_connection
            driver.execute(
                sql.SQL("GRANT CREATE ON SCHEMA public TO {}").format(
                    sql.Identifier(s["engines"]["self"].url.username)
                )
            )
    with Session(s["engines"][who]) as db:
        db.connection(
            execution_options={"isolation_level": "REPEATABLE READ", "postgresql_readonly": True}
        )
        if change == "set_role":
            db.execute(text("SET ROLE menuto_nutrition_client"))
        context = {} if change == "foreign_context" else s["basis_context"]
        result = host.capture_test_policy_v2(db, context, s["basis_selectors"])
        assert isinstance(result, v.PolicyV2CaptureFailure) and not hasattr(result, "payload")


def test_piv_pg02_actual_other_database_cannot_use_original_context(piv_case, postgres_engine):  # noqa: F811
    from app.persistence.database import create_database_engine
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    s = piv_case
    url = s["engines"]["self"].url.set(database=postgres_engine.url.database)
    foreign = create_database_engine(url.render_as_string(hide_password=False))
    try:
        with Session(foreign) as db:
            db.connection(
                execution_options={
                    "isolation_level": "REPEATABLE READ",
                    "postgresql_readonly": True,
                }
            )
            assert db.scalar(text("SELECT current_database()")) != s["basis_artifact"].database_name
            assert db.scalar(text("SELECT session_user")) == s["engines"]["self"].url.username
            result = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
            assert isinstance(result, v.PolicyV2CaptureFailure) and not hasattr(result, "payload")
    finally:
        foreign.dispose()


@pytest.mark.parametrize(
    "isolation,readonly", [("READ COMMITTED", True), ("REPEATABLE READ", False)]
)
def test_piv_pg03_transaction_modes_rejected(piv_case, isolation, readonly):  # noqa: F811
    with reader(piv_case, "self", isolation=isolation, readonly=readonly) as db:
        result = host.capture_test_policy_v2(
            db, piv_case["basis_context"], piv_case["basis_selectors"]
        )
        assert isinstance(result, v.PolicyV2CaptureFailure)


@pytest.mark.parametrize(
    "action", ["close_reopen", "rollback_reopen", "dirty", "duplicate_capture", "context_exit"]
)
def test_piv_pg03_lifetime_and_session_exclusivity(piv_case, action):  # noqa: F811
    from uuid import uuid4

    from app.modules.identity.models import User

    s = piv_case
    with reader(s, "self") as db:
        if action == "dirty":
            db.add(User(display_name="TEST_ONLY_" + uuid4().hex))
            assert isinstance(
                host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"]),
                v.PolicyV2CaptureFailure,
            )
            assert db not in host._SESSIONS
            return
        lease = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        assert not isinstance(lease, v.PolicyV2CaptureFailure), lease
        if action == "duplicate_capture":
            denied = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
            assert denied.diagnostics[0].code == "SOURCE_CUT_INCOHERENT"
            assert isinstance(
                host.consume_test_policy_v2(lease, use_for(s)), v.NutritionPolicyHandoffV2
            )
        elif action == "context_exit":
            with lease:
                assert host._ACTIVE[lease].state == "READY"
            assert (
                host.consume_test_policy_v2(lease, use_for(s)).diagnostics[0].code
                == "CONSUME_REPLAY"
            )
        else:
            db.close() if action == "close_reopen" else db.rollback()
            db.connection()
            result = host.consume_test_policy_v2(lease, use_for(s))
            assert result.diagnostics[0].code == "CAPTURE_EXPIRED"
        assert db not in host._SESSIONS


@pytest.mark.parametrize("mode", ["routed", "multiple", "schema"])
def test_piv_pg03_no_routed_multiple_or_translated_connections(piv_case, mode):  # noqa: F811
    from app.modules.catalog.models import Ingredient
    from sqlalchemy.orm import Session

    s = piv_case
    if mode == "routed":
        db = Session(s["engines"]["self"], binds={Ingredient: s["engines"]["root"]})
    elif mode == "schema":
        db = Session(
            s["engines"]["self"], execution_options={"schema_translate_map": {None: "pg_temp"}}
        )
    else:
        with reader(s, "self") as live:
            assert isinstance(
                host.capture_test_policy_v2([live, live], s["basis_context"], s["basis_selectors"]),
                v.PolicyV2CaptureFailure,
            )
        return
    with db:
        assert isinstance(
            host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"]),
            v.PolicyV2CaptureFailure,
        )


@pytest.mark.parametrize("change", ["viewer", "foreign_member", "precision_actor"])
def test_piv_pg04_actual_precision_subject_authority(piv_case, change):  # noqa: F811
    from uuid import uuid4

    from app.domain.feature_identity import canonical
    from app.modules.nutrition.basis_contracts import BasisSelectorsV1
    from sqlalchemy import text

    s = piv_case
    data = canonical(s["basis_selectors"])
    if change == "viewer":
        with s["engines"]["root"].begin() as db:
            db.execute(
                text("UPDATE memberships SET role='VIEWER' WHERE household_id=:h AND user_id=:u"),
                dict(h=s["household_id"], u=s["user_id"]),
            )
    elif change == "foreign_member":
        data["nre_scope"]["subject"]["member_id"] = str(uuid4())
    else:
        data["nre_scope"]["precision"]["actor_user_id"] = str(uuid4())
    with reader(s, "self") as db:
        result = host.capture_test_policy_v2(
            db, s["basis_context"], BasisSelectorsV1.model_validate(data)
        )
        assert isinstance(result, v.PolicyV2CaptureFailure)


def test_piv_pg05_complete_old_cut_vs_fresh_source(piv_case):  # noqa: F811
    from sqlalchemy import text
    from test_postgres_nutrition_resolution import add_reference

    s = piv_case
    with reader(s, "self") as db:
        snapshot = db.scalar(text("SELECT pg_current_snapshot()::text"))
        add_reference(s)
        lease = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        assert not isinstance(lease, v.PolicyV2CaptureFailure), lease
        h = host.consume_test_policy_v2(lease, use_for(s))
        assert isinstance(h, v.NutritionPolicyHandoffV2), h
        assert h.input.basis_sources.nre.sources.frame.source_frame.mvcc_snapshot == snapshot
    with reader(s, "self") as db:
        assert isinstance(
            host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"]),
            v.PolicyV2CaptureFailure,
        )


@pytest.mark.parametrize("missing", ["reference", "recipe", "tier", "rule", "serving"])
def test_piv_pg05_missing_canonical_selection_not_favorable_partial(piv_case, missing):  # noqa: F811
    from uuid import uuid4

    from app.domain.feature_identity import canonical
    from app.modules.nutrition.basis_contracts import BasisSelectorsV1

    s = piv_case
    data = canonical(s["basis_selectors"])
    q = data["nre_scope"]
    if missing == "reference":
        q["references"][0]["reference_id"] = str(uuid4())
    elif missing == "recipe":
        q["recipes"][0]["recipe_version_id"] = str(uuid4())
    elif missing == "tier":
        q["recipes"][0]["tier_ids"] = [str(uuid4())]
    elif missing == "rule":
        q["recipes"][0]["rule_selections"] = [[str(uuid4())]]
    else:
        q["slots"][0]["alternatives"] = []
    selectors = BasisSelectorsV1.model_validate(data)
    with reader(s, "self") as db:
        result = host.capture_test_policy_v2(db, s["basis_context"], selectors)
        if not isinstance(result, v.PolicyV2CaptureFailure):
            result = host.consume_test_policy_v2(result, use_for(s))
        assert isinstance(result, v.PolicyV2CaptureFailure)


@pytest.mark.parametrize(
    "change", ["root_grant", "rule_grant", "rule_retract", "future_retirement"]
)
def test_piv_pg06_revocation_and_lifecycle_do_not_rewrite_old_replay(piv_case, change):  # noqa: F811
    from datetime import timedelta

    from app.modules.validation.nutrition_policy_v2 import check_policy_handoff_v2
    from nutrition_root_postgres_fixtures import grant
    from nutrition_synthesis_postgres_fixtures import append, command, grant_rule

    s = piv_case
    with reader(s, "self") as db:
        lease = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        assert not isinstance(lease, v.PolicyV2CaptureFailure), lease
        h = host.consume_test_policy_v2(lease, use_for(s))
        assert isinstance(h, v.NutritionPolicyHandoffV2), h
    if change == "root_grant":
        grant(s, "self", "ROOT_SOURCE_READ", action="REVOKE")
    elif change == "rule_grant":
        grant_rule(s, "self", "SYNTHESIS_SOURCE_READ", action="REVOKE")
    else:
        append(
            s,
            "publisher",
            command(
                s,
                dict(
                    kind="PUBLICATION",
                    revision_id=s["rule"].revision_id,
                    body_fingerprint=s["rule_publication"].command.body.body_fingerprint,
                    action="RETIRE" if change == "future_retirement" else "RETRACT",
                    review_id=None,
                    predecessor_publication_id=s["rule_publication"].id,
                    effective_at=s["rule"].effective.start
                    + (timedelta(hours=12) if change == "future_retirement" else timedelta()),
                ),
            ),
        )
    with reader(s, "self") as db:
        result = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        assert isinstance(result, v.PolicyV2CaptureFailure), result
        assert result.diagnostics[0].code == "CAPTURE_FAILED"
    assert check_policy_handoff_v2(h, use_for(s)).decision == "CONSISTENT"


@pytest.mark.parametrize("phase", ["capture", "check"])
@pytest.mark.parametrize("change", ["revoke", "advance"])
def test_piv_pg07_registry_change_during_actual_operation(piv_case, monkeypatch, phase, change):  # noqa: F811
    from app.modules.planning.basis_capture import (
        _advance_isolated_basis_fixture,
        _revoke_isolated_basis_context,
    )

    s = piv_case

    def mutate():
        if change == "revoke":
            _revoke_isolated_basis_context(s["basis_context"])
        else:
            from app.domain.feature_identity import canonical
            from basis_fixtures import rehash_artifact

            data = canonical(s["basis_artifact"])
            data.update(
                revision=2, previous_artifact_fingerprint=s["basis_artifact"].artifact_fingerprint
            )
            event = next(x for x in data["events"] if x["capability"] == "TEST_BASIS_SOURCE_READ")
            data["events"].append(event | {"id": "TEST_ONLY_v2_reader_revoke", "kind": "REVOKE"})
            _advance_isolated_basis_fixture(s["basis_context"], rehash_artifact(data))

    if phase == "capture":
        original = host.mba.capture_test_basis_sources

        def capturing(*args):
            sources = original(*args)
            mutate()
            return sources

        monkeypatch.setattr(host.mba, "capture_test_basis_sources", capturing)
    else:
        original = host._run

        def checking(stage, *args):
            result = original(stage, *args)
            if stage == "check":
                mutate()
            return result

        monkeypatch.setattr(host, "_run", checking)
    with reader(s, "self") as db:
        result = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        if phase == "check":
            assert not isinstance(result, v.PolicyV2CaptureFailure), result
            lease = result
            result = host.consume_test_policy_v2(lease, use_for(s))
            assert lease not in host._ACTIVE
        assert isinstance(result, v.PolicyV2CaptureFailure)
        assert result.diagnostics[0].code == "REGISTRY_CHANGED"
        assert db not in host._SESSIONS


def test_piv_pg08_concurrent_consumption_exactly_once(piv_case):  # noqa: F811
    from concurrent.futures import ThreadPoolExecutor

    s = piv_case
    with reader(s, "self") as db:
        lease = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        assert not isinstance(lease, v.PolicyV2CaptureFailure), lease
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(host.consume_test_policy_v2, lease, use_for(s)) for _ in range(2)
            ]
            results = [f.result() for f in futures]
        assert sum(isinstance(x, v.NutritionPolicyHandoffV2) for x in results) == 1, results
        assert [
            x.diagnostics[0].code for x in results if isinstance(x, v.PolicyV2CaptureFailure)
        ] == ["CONSUME_REPLAY"]
        assert lease not in host._ACTIVE and db not in host._SESSIONS


def test_piv_pg08_real_capture_does_not_make_serialized_or_copy_authority(piv_case):  # noqa: F811
    import pickle
    from copy import copy, deepcopy

    from app.domain.feature_identity import canonical

    s = piv_case
    with reader(s, "self") as db:
        lease = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        assert not isinstance(lease, v.PolicyV2CaptureFailure), lease
        for copier in (copy, deepcopy, pickle.dumps):
            with pytest.raises(TypeError):
                copier(lease)
        fake = object.__new__(type(lease))
        assert (
            host.consume_test_policy_v2(fake, use_for(s)).diagnostics[0].code
            == "ORIGIN_NOT_ESTABLISHED"
        )
        h = host.consume_test_policy_v2(lease, use_for(s))
        assert isinstance(h, v.NutritionPolicyHandoffV2), h
        assert (
            host.consume_test_policy_v2(canonical(h), use_for(s)).diagnostics[0].code
            == "ORIGIN_NOT_ESTABLISHED"
        )


def test_piv_pg08_wrong_precision_use_burns_actual_lease(piv_case):  # noqa: F811
    s = piv_case
    with reader(s, "self") as db:
        lease = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        assert not isinstance(lease, v.PolicyV2CaptureFailure), lease
        use = use_for(s).model_copy(update={"precision_fingerprint": "f" * 64})
        assert (
            host.consume_test_policy_v2(lease, use).diagnostics[0].code
            == "SOURCE_IDENTITY_MISMATCH"
        )
        assert (
            host.consume_test_policy_v2(lease, use_for(s)).diagnostics[0].code == "CONSUME_REPLAY"
        )
        assert lease not in host._ACTIVE and db not in host._SESSIONS


@pytest.mark.parametrize("piv_case", ["H_EMPTY"], indirect=True)
def test_piv_pg08_faithful_non_success_burns_lease_without_numbers(piv_case):  # noqa: F811
    s = piv_case
    with reader(s, "self") as db:
        lease = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        assert not isinstance(lease, v.PolicyV2CaptureFailure), lease
        retained = host._ACTIVE[lease]
        assert (
            retained.result.outcome == "RESOLUTION_INSUFFICIENT" and retained.result.payload is None
        )
        result = host.consume_test_policy_v2(lease, use_for(s))
        assert result.diagnostics[0].code == "NO_PROTECTED_JOINT_WITNESS" and not hasattr(
            result, "payload"
        )
        assert (
            host.consume_test_policy_v2(lease, use_for(s)).diagnostics[0].code == "CONSUME_REPLAY"
        )
        assert lease not in host._ACTIVE and db not in host._SESSIONS


def test_piv_pg09_actual_blocked_capture_cancellation_and_caller_rollback(piv_case):  # noqa: F811
    from threading import Event, Thread
    from time import sleep

    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    s, cancelled = piv_case, Event()
    with s["engines"]["root"].begin() as blocker:
        blocker.execute(text("LOCK TABLE nutrition_source_providers IN ACCESS EXCLUSIVE MODE"))
        with reader(s, "self") as db:
            pid = db.scalar(text("SELECT pg_backend_pid()"))
            driver = db.connection().connection.driver_connection

            def cancel_blocked():
                for _ in range(100):
                    with s["engines"]["root"].connect() as observer:
                        wait = observer.scalar(
                            text("SELECT wait_event_type FROM pg_stat_activity WHERE pid=:pid"),
                            dict(pid=pid),
                        )
                    if wait == "Lock":
                        driver.cancel()
                        cancelled.set()
                        return
                    sleep(0.05)

            t = Thread(target=cancel_blocked)
            t.start()
            try:
                result = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
            finally:
                t.join(6)
            assert cancelled.is_set() and not t.is_alive()
            assert (
                isinstance(result, v.PolicyV2CaptureFailure)
                and result.diagnostics[0].code == "CAPTURE_FAILED"
            )
            assert db not in host._SESSIONS
            with pytest.raises(DBAPIError):
                db.scalar(text("SELECT 1"))
            db.rollback()  # Caller owns transaction completion; host did not hide the failed cut.
            assert db.scalar(text("SELECT 1")) == 1


def test_piv_pg09_expired_whole_operation_burns_real_lease(piv_case):  # noqa: F811
    from time import monotonic

    s = piv_case
    with reader(s, "self") as db:
        lease = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        assert not isinstance(lease, v.PolicyV2CaptureFailure), lease
        host._ACTIVE[lease].deadline = monotonic() - 1
        result = host.consume_test_policy_v2(lease, use_for(s))
        assert result.diagnostics[0].code == "CAPTURE_EXPIRED"
        assert lease not in host._ACTIVE and db not in host._SESSIONS


def test_piv_pg09_context_abort_kills_check_worker_and_burns_lease(piv_case, monkeypatch):  # noqa: F811
    from threading import Timer
    from time import monotonic

    from test_policy_v2_adversarial import slow_test_worker

    s = piv_case
    with reader(s, "self") as db:
        lease = host.capture_test_policy_v2(db, s["basis_context"], s["basis_selectors"])
        assert not isinstance(lease, v.PolicyV2CaptureFailure), lease
        monkeypatch.setattr(host, "execute", slow_test_worker)
        timer = Timer(0.5, lease.__exit__, args=(None, None, None))
        started = monotonic()
        timer.start()
        try:
            result = host.consume_test_policy_v2(lease, use_for(s))
        finally:
            timer.cancel()
            timer.join()
        assert monotonic() - started < 8
        assert isinstance(result, v.PolicyV2CaptureFailure) and not hasattr(result, "payload")
        assert lease not in host._ACTIVE and db not in host._SESSIONS


def test_piv_pg10_fresh_install_empty_content_and_existing_protected_objects(postgres_engine):  # noqa: F811
    from app.persistence.models import Base
    from sqlalchemy import inspect, text

    with postgres_engine.connect() as db:
        assert len(Base.metadata.tables) == 108
        assert set(inspect(db).get_table_names()) == set(Base.metadata.tables) | {"alembic_version"}
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
        nutrition = sorted(n for n in Base.metadata.tables if n.startswith("nutrition_"))
        assert nutrition
        for table in nutrition:
            assert db.scalar(text('SELECT count(*) FROM "' + table + '"')) == 0, table
        # No v2 SQL object or role is installed by the additive pure/capture modules.
        assert db.scalar(text("SELECT count(*) FROM pg_proc WHERE proname LIKE '%policy_v2%'")) == 0
        assert (
            db.scalar(text("SELECT count(*) FROM pg_roles WHERE rolname LIKE '%policy_v2%'")) == 0
        )
