"""Protected-entry native MVCC proofs; every connection belongs to the TEST_ONLY fixture."""

import copy
import json
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from uuid import uuid4

import psycopg
import pytest
from app.modules.validation.identity_source import check_identity_source_v1
from identity_source_fixtures import h
from psycopg import sql


def _source_check(s, source):
    assert source["outcome"] == "AVAILABLE_AT_RETAINED_CUT"
    checked = check_identity_source_v1(source, s.raw)
    assert checked.decision == "CONSISTENT" and checked.numerical_use == "NOT_ADMITTED"
    assert checked.transport == "UNVERIFIED_TRANSPORT"
    return checked


def _acl(db, action, name, target):
    db.execute(
        sql.SQL("{} ALL ON PARAMETER {} {} {}").format(
            sql.SQL(action),
            sql.Identifier(name),
            sql.SQL("TO" if action == "GRANT" else "FROM"),
            sql.Identifier(target),
        )
    )


def _mutate_between_boundaries(
    s, mutate, *, isolation="REPEATABLE READ", cross_database=False, use_facade=False
):
    # Trusted fixture synchronization ONLY. No runtime observer connection/catalog lock is added.
    # Wait until the real protected entry passed its first session capture and reached Membership.
    with ExitStack() as stack:
        locker = stack.enter_context(s.connect())
        observer = stack.enter_context(s.connect())
        reader = stack.enter_context(s.connect("requester")) if not use_facade else None
        facade_connection = (
            stack.enter_context(s.engine(isolation=isolation).connect()) if use_facade else None
        )
        driver = facade_connection.connection.driver_connection if use_facade else reader
        writer = observer
        if cross_database:
            owner_connection = stack.enter_context(s.server["maintenance"].connect())
            writer = owner_connection.connection.driver_connection
        pid = driver.info.backend_pid

        def capture():
            if use_facade:
                from app.modules.identity.source_capture import capture_identity_request_source_v1

                with facade_connection.begin():
                    return capture_identity_request_source_v1(
                        facade_connection, s.raw, context=context
                    ).model_dump(mode="json")
            try:
                with reader.transaction():
                    reader.execute(
                        sql.SQL("SET TRANSACTION ISOLATION LEVEL {} READ ONLY").format(
                            sql.SQL(isolation)
                        )
                    )
                    return reader.execute(
                        "SELECT menuto_identity_source.capture_request_source(%s)",
                        (json.dumps(s.raw),),
                    ).fetchone()[0]
            except psycopg.Error as error:
                return {"sqlstate": error.sqlstate}

        context = s.context() if use_facade else None
        with ThreadPoolExecutor(max_workers=1) as pool:
            with locker.transaction():
                locker.execute("LOCK public.memberships IN ACCESS EXCLUSIVE MODE")
                future = pool.submit(capture)
                until = time.monotonic() + 2
                while time.monotonic() < until:
                    if observer.execute(
                        """SELECT EXISTS(SELECT FROM pg_locks
                         WHERE pid=%s AND relation='public.memberships'::regclass
                         AND NOT granted)""",
                        (pid,),
                    ).fetchone()[0]:
                        break
                    if future.done():
                        raise AssertionError(
                            (
                                "Protected entry ended before boundary synchronization",
                                future.result(),
                            )
                        )
                    time.sleep(0.005)
                else:
                    raise AssertionError(
                        "Actual protected entry did not reach the source-read boundary"
                    )
                with writer.transaction():
                    xid = str(writer.execute("SELECT pg_current_xact_id()").fetchone()[0])
                    mutate(writer)
                committed_at = str(writer.execute("SELECT clock_timestamp()").fetchone()[0])
            result = future.result(timeout=5)
        return result, {
            "isolation": isolation,
            "writer_database": "other" if cross_database else "same",
            "writer_xid": xid,
            "commit_confirmed_at": committed_at,
            "protected_entry": "capture_request_source",
            "sqlstate": result.get("sqlstate"),
        }


def assert_unchanged_and_observed_mismatch(s):
    evidence = []
    for isolation in ("REPEATABLE READ", "SERIALIZABLE"):
        retained = s.capture(isolation=isolation)
        _source_check(s, retained)
        a, b = (
            copy.deepcopy(retained["frame"]["session_start"]),
            copy.deepcopy(retained["frame"]["session_end"]),
        )
        a.pop("observed_at")
        b.pop("observed_at")
        assert a == b
        evidence.append(
            {
                "control": "unchanged",
                "isolation": isolation,
                "snapshot": retained["frame"]["snapshot_id"],
                "outcome": retained["outcome"],
            }
        )
    # A native login descriptor really changes after the first protected boundary.
    # This is not a test-local DO predicate or a mocked producer observation.
    renamed = "itr_renamed_" + uuid4().hex[:12]

    def rename(db):
        db.execute(
            sql.SQL("ALTER ROLE {} RENAME TO {}").format(
                sql.Identifier(s.roles["requester"]), sql.Identifier(renamed)
            )
        )

    try:
        result, observation = _mutate_between_boundaries(s, rename)
        assert result.get("sqlstate") == "40001", result
        assert "frame" not in result and "source_fingerprint" not in result
        observation["case"] = "actually_observed_login_descriptor_change"
        observation["whole_capture_rejected"] = True
        evidence.append(observation)
    finally:
        with s.connect() as db:
            if db.execute(
                "SELECT EXISTS(SELECT FROM pg_roles WHERE rolname=%s)", (renamed,)
            ).fetchone()[0]:
                db.execute(
                    sql.SQL("ALTER ROLE {} RENAME TO {}").format(
                        sql.Identifier(renamed), sql.Identifier(s.roles["requester"])
                    )
                )
    # The actual public Python source boundary must map that native whole failure.
    try:
        failure, observation = _mutate_between_boundaries(s, rename, use_facade=True)
        assert failure["outcome"] == "SOURCE_CUT_INCOHERENT"
        assert failure["reason"] == "CATALOG_CHANGED" and failure["payload"] is None
        assert failure["numerical_use"] == "NOT_ADMITTED"
        observation.update(
            case="observed_descriptor_change_at_public_capture_boundary",
            outcome=failure["outcome"],
            reason=failure["reason"],
            payload=None,
        )
        evidence.append(observation)
    finally:
        with s.connect() as db:
            if db.execute(
                "SELECT EXISTS(SELECT FROM pg_roles WHERE rolname=%s)", (renamed,)
            ).fetchone()[0]:
                db.execute(
                    sql.SQL("ALTER ROLE {} RENAME TO {}").format(
                        sql.Identifier(renamed), sql.Identifier(s.roles["requester"])
                    )
                )

    # Independently reject a fully rehashed contradictory retained end boundary.
    raw = copy.deepcopy(retained)
    raw["frame"]["session_end"]["database_oid"] += 1
    raw["source_fingerprint"] = h(
        "identity.source.v1", {k: v for k, v in raw.items() if k != "source_fingerprint"}
    )
    checked = check_identity_source_v1(raw, s.raw)
    assert checked.decision == "INCONSISTENT" and checked.numerical_use == "NOT_ADMITTED"
    assert checked.reconstructed_outcome is None
    return evidence


def assert_mutation_before_cut(s):
    evidence = []
    for cross_database in (False, True):
        with ExitStack() as stack:
            db = stack.enter_context(s.connect())
            if cross_database:
                wrapper = stack.enter_context(s.server["maintenance"].connect())
                db = wrapper.connection.driver_connection
            name = "menuto_itr.before_" + uuid4().hex
            try:
                _acl(db, "GRANT", name, s.roles["requester"])
                assert db.execute(
                    "SELECT has_parameter_privilege(%s,%s,'SET')", (s.roles["requester"], name)
                ).fetchone()[0]
                for isolation in ("REPEATABLE READ", "SERIALIZABLE"):
                    with pytest.raises(psycopg.errors.InsufficientPrivilege) as error:
                        s.capture(isolation=isolation)
                    assert error.value.sqlstate == "42501"
                    evidence.append(
                        {
                            "case": "unsafe_grant_before_fresh_cut",
                            "isolation": isolation,
                            "writer_database": "other" if cross_database else "same",
                            "sqlstate": "42501",
                        }
                    )
                _acl(db, "REVOKE", name, s.roles["requester"])
                for isolation in ("REPEATABLE READ", "SERIALIZABLE"):
                    _source_check(s, s.capture(isolation=isolation))
            finally:
                _acl(db, "REVOKE", name, s.roles["requester"])
    return evidence


def assert_mutation_after_cut(s):
    evidence = []
    other = "itr_cut_other_" + uuid4().hex[:12]
    with s.connect() as db:
        db.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(other)))
        try:
            for isolation in ("REPEATABLE READ", "SERIALIZABLE"):
                for cross_database in (False, True):
                    for action in ("GRANT", "REVOKE"):
                        name = "menuto_itr.after_" + uuid4().hex
                        target = s.roles["requester"] if action == "GRANT" else other
                        if action == "REVOKE":
                            _acl(db, "GRANT", name, target)
                        try:
                            result, observation = _mutate_between_boundaries(
                                s,
                                lambda writer: _acl(writer, action, name, target),
                                isolation=isolation,
                                cross_database=cross_database,
                            )
                            _source_check(s, result)
                            arrays = []
                            for boundary in ("session_start", "session_end"):
                                arrays.append(
                                    [
                                        o
                                        for o in result["frame"][boundary]["objects"]
                                        if o["kind"] == "PARAMETER" and o["object_name"] == name
                                    ]
                                )
                            assert arrays[0] == arrays[1]
                            assert bool(arrays[0]) == (action == "REVOKE")
                            assert db.execute(
                                "SELECT has_parameter_privilege(%s,%s,'SET')", (target, name)
                            ).fetchone()[0] == (action == "GRANT")
                            observation.update(
                                case="invisible_" + action.lower(),
                                snapshot=result["frame"]["snapshot_id"],
                                historical_outcome=result["outcome"],
                                numerical_use="NOT_ADMITTED",
                                equal_retained_catalog=True,
                            )
                            if action == "GRANT":
                                with pytest.raises(psycopg.errors.InsufficientPrivilege) as error:
                                    s.capture()
                                observation["next_fresh_capture_sqlstate"] = error.value.sqlstate
                                assert error.value.sqlstate == "42501"
                            else:
                                _source_check(s, s.capture())
                            evidence.append(observation)
                        finally:
                            _acl(db, "REVOKE", name, target)
            # Removing an unsafe privilege later must not repair its earlier unsafe cut.
            name = "menuto_itr.old_unsafe_" + uuid4().hex
            _acl(db, "GRANT", name, s.roles["requester"])
            try:
                with s.connect("requester") as reader, reader.transaction():
                    reader.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                    old = reader.execute("SELECT pg_current_snapshot()::text").fetchone()[0]
                    _acl(db, "REVOKE", name, s.roles["requester"])
                    with (
                        pytest.raises(psycopg.errors.InsufficientPrivilege) as error,
                        reader.transaction(),
                    ):
                        reader.execute(
                            "SELECT menuto_identity_source.capture_request_source(%s)",
                            (json.dumps(s.raw),),
                        )
                    assert error.value.sqlstate == "42501"
                    evidence.append(
                        {
                            "case": "unsafe_old_cut_not_repaired_by_revoke",
                            "snapshot": old,
                            "sqlstate": "42501",
                        }
                    )
                _source_check(s, s.capture())
            finally:
                _acl(db, "REVOKE", name, s.roles["requester"])
        finally:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(other)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(other)))
    return evidence
