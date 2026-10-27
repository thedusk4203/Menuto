"""Additional authority rotation, ordering and malformed replay boundary regressions."""

import secrets
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.modules.preferences import hierarchy_contracts as h
from app.modules.preferences.hierarchy_resolution import resolve_hierarchy_sources
from app.modules.preferences.hierarchy_sources import (
    capture_hierarchy_sources,
    change_hierarchy_authority,
    enroll_hierarchy_principal,
)
from hierarchy_postgres_fixtures import capture, publication, publish
from hierarchy_postgres_fixtures import hierarchy_server as hierarchy_server
from hierarchy_postgres_fixtures import hierarchy_source as hierarchy_source
from psycopg import sql
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_postgres_hierarchy_lifecycle import relation_command

pytestmark = pytest.mark.postgres


def test_a04_recreated_same_login_name_cannot_reuse_old_oid_grants(hierarchy_source):
    s = hierarchy_source
    name = s["names"]["other"]
    with Session(s["engines"]["admin"]) as admin:
        change_hierarchy_authority(
            admin,
            dict(
                provider_id=s["provider"].id,
                principal_id=s["principals"]["other"].id,
                capability="CAPTURE",
                action="GRANT",
                expected_authority_generation=4,
                reason="Synthetic rotation test",
                idempotency_key=uuid4().hex,
            ),
        )
        admin.commit()
    assert capture(s, who="other").reader_principal_id == s["principals"]["other"].id
    s["engines"]["other"].dispose()
    with s["engines"]["root"].begin() as root:
        with root.connection.driver_connection.cursor() as cur:
            cur.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))
            cur.execute("SET password_encryption='scram-sha-256'")
            cur.execute(
                sql.SQL("CREATE ROLE {} LOGIN INHERIT PASSWORD {}").format(
                    sql.Identifier(name), sql.Literal(s["passwords"]["other"])
                )
            )
            cur.execute(sql.SQL("GRANT menuto_hierarchy_client TO {}").format(sql.Identifier(name)))
    with pytest.raises(DBAPIError, match="enrolled"):
        capture(s, who="other")
    with Session(s["engines"]["admin"]) as admin:
        replacement = enroll_hierarchy_principal(
            admin, dict(role_name=name, idempotency_key=secrets.token_hex(12))
        )
        admin.commit()
    assert replacement.role_oid != s["principals"]["other"].role_oid
    assert replacement.id != s["principals"]["other"].id
    # Enrollment is not a grant, even when the textual login name is unchanged.
    with pytest.raises(DBAPIError, match="capability denied"):
        capture(s, who="other")


def test_l02_competing_admin_grants_have_one_frontier_winner(hierarchy_source):
    s = hierarchy_source
    gate = Barrier(2)

    def grant(capability):
        with Session(s["engines"]["admin"]) as admin:
            gate.wait(timeout=5)
            try:
                result = change_hierarchy_authority(
                    admin,
                    dict(
                        provider_id=s["provider"].id,
                        principal_id=s["principals"]["other"].id,
                        capability=capability,
                        action="GRANT",
                        expected_authority_generation=4,
                        reason="Competing authority CAS",
                        idempotency_key=uuid4().hex,
                    ),
                )
                admin.commit()
                return result
            except DBAPIError as exc:
                assert exc.orig.sqlstate == "40001"
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(grant, ["REVIEW_PUBLISH", "CAPTURE"]))
    assert sum(r is not None for r in results) == 1
    cut = capture(s)
    assert cut.frontier.authority_generation == 5
    assert len(cut.authority_events) == 5


@pytest.mark.parametrize("missing", [True, False])
def test_i01_missing_or_wrong_kind_owner_identity_never_publishes(hierarchy_source, missing):
    s = hierarchy_source
    p = publish(s, publication(s))
    target = (
        dict(kind="INGREDIENT", ingredient_id=uuid4())
        if missing
        else dict(kind="PROTEIN", feature_term_id=s["target"]["ingredient_id"])
    )
    command = relation_command(s, p, source=target)
    before = capture(s)
    with pytest.raises(DBAPIError):
        publish(s, command)
    assert capture(s).frontier == before.frontier


@pytest.mark.parametrize("field", ["capture_started_at", "capture_completed_at"])
def test_l03_capture_clock_regression_rejected(hierarchy_source, field):
    s = hierarchy_source
    cut = capture(s)
    body = canonical(cut)
    body[field] = canonical(cut.provider.recorded_at - timedelta(days=1))
    with pytest.raises(ValueError, match="clock|after capture"):
        h.HierarchySourceSnapshotDraft.model_validate(body)


def test_l03_equal_server_times_order_by_journal_and_regression_rejects(hierarchy_source):
    s = hierarchy_source
    body = canonical(capture(s))
    # Offline self-consistency checks do not certify database origin. Rebuild a
    # valid equal-time source to exercise journal order independently of clocks.
    now = body["capture_started_at"]
    previous = None
    for event, mutation in zip(body["authority_events"], body["mutations"], strict=True):
        event["recorded_at"] = now
        event["fact_hash"] = h.hierarchy_hash(
            "hierarchy.authority.v1", {k: v for k, v in event.items() if k != "fact_hash"}
        )
        mutation.update(recorded_at=now, child_hash=event["fact_hash"], predecessor_hash=previous)
        mutation["journal_hash"] = h.hierarchy_hash(
            "hierarchy.mutation.v1", {k: v for k, v in mutation.items() if k != "journal_hash"}
        )
        previous = mutation["journal_hash"]
    body["frontier"]["mutation_head_hash"] = previous
    equal = h.HierarchySourceSnapshotDraft.model_validate(body)
    assert resolve_hierarchy_sources(equal).rows[0].reason == "POLICY_MISSING"
    # Rehash an internally coherent child/mutation pair with an earlier clock.
    event, mutation = body["authority_events"][-1], body["mutations"][-1]
    older = canonical(equal.provider.recorded_at - timedelta(days=1))
    event["recorded_at"] = older
    event["fact_hash"] = h.hierarchy_hash(
        "hierarchy.authority.v1", {k: v for k, v in event.items() if k != "fact_hash"}
    )
    mutation.update(recorded_at=older, child_hash=event["fact_hash"])
    mutation["journal_hash"] = h.hierarchy_hash(
        "hierarchy.mutation.v1", {k: v for k, v in mutation.items() if k != "journal_hash"}
    )
    body["frontier"]["mutation_head_hash"] = mutation["journal_hash"]
    with pytest.raises(ValueError, match="clock regression"):
        h.HierarchySourceSnapshotDraft.model_validate(body)


@pytest.mark.parametrize("counter", [-1, True, 9223372036854775808])
def test_l03_counter_bounds_reject_before_database_work(hierarchy_source, counter):
    with pytest.raises(ValueError):
        h.HierarchyPublicationCommand.model_validate(
            publication(hierarchy_source) | dict(expected_provider_generation=counter)
        )


def test_r01_capture_with_pending_orm_writes_rejects(hierarchy_source):
    from app.modules.catalog.models import Ingredient

    s = hierarchy_source
    with Session(s["engines"]["reader"]) as reader:
        reader.add(Ingredient(name="Uncommitted work cannot enter capture"))
        with pytest.raises(ValueError, match="Clean read-only"):
            capture_hierarchy_sources(
                reader,
                dict(
                    provider_id=s["provider"].id,
                    policy_id=s["policy"].policy_id,
                    requested_targets=[],
                ),
            )
