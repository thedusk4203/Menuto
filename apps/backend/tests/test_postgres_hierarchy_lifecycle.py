"""Immutable source lifecycle, graph restrictions, replay and real competing transactions."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command as alembic_command
from app.domain.feature_identity import canonical
from app.modules.catalog.models import Ingredient
from app.modules.preferences import hierarchy_contracts as h
from app.modules.preferences.hierarchy_resolution import resolve_hierarchy_sources
from app.modules.preferences.hierarchy_sources import (
    capture_hierarchy_sources,
    publish_hierarchy_source,
)
from hierarchy_postgres_fixtures import capture, publication, publish
from hierarchy_postgres_fixtures import hierarchy_server as hierarchy_server
from hierarchy_postgres_fixtures import hierarchy_source as hierarchy_source
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

pytestmark = pytest.mark.postgres


def relation_command(s, receipt, source=None, destination=None, **changes):
    identity = dict(
        kind="RELATION",
        policy_id=s["policy"].policy_id,
        source=source or s["target"],
        destination=destination or s["destination"],
        recipe_bindings=[],
    )
    relation = dict(
        policy_revision_id=receipt.publication.id,
        policy_fingerprint=s["policy"].fingerprint(),
        support_mode="REVIEWED_EXACT_PAIR",
        support_review_id=None,
        catalog_review_ids=[],
    )
    return publication(s, identity=identity, relation=relation) | changes


def test_l01_l03_immutable_receipts_replacement_retraction_republish(hierarchy_source):
    s = hierarchy_source
    first_command = publication(s)
    first = publish(s, first_command)
    assert publish(s, first_command) == first
    second_policy = s["policy"].model_dump() | dict(policy_version=2)
    second = publish(s, publication(s, policy=second_policy, old=first))
    assert publish(s, first_command) == first
    tombstone = publish(s, publication(s, operation="RETRACT", old=second))
    assert resolve_hierarchy_sources(capture(s)).rows[0].reason == "POLICY_RETRACTED"
    third = publish(
        s, publication(s, policy=s["policy"].model_dump() | dict(policy_version=3), old=tombstone)
    )
    assert [p.revision for p in capture(s).publications] == [0, 1, 2, 3]
    assert third.publication.command.policy.policy_version == 3
    with pytest.raises(DBAPIError, match="Idempotency conflict"):
        publish(s, first_command | dict(review_rationale="Changed same key"))


def test_l01_relation_tombstone_not_absence_and_old_cut_stable(hierarchy_source):
    s = hierarchy_source
    policy = publish(s, publication(s))
    first = publish(s, relation_command(s, policy))
    old = capture(s, [s["destination"]])
    assert resolve_hierarchy_sources(old).rows[0].status == "ELIGIBLE_RELATION"
    tombstone = publish(
        s,
        publication(s, identity=first.publication.command.identity, operation="RETRACT", old=first),
    )
    assert (
        resolve_hierarchy_sources(capture(s, [s["destination"]])).rows[0].reason
        == "RELATION_RETRACTED"
    )
    assert (
        resolve_hierarchy_sources(
            h.HierarchySourceSnapshotDraft.model_validate(canonical(old))
        ).result_fingerprint
        == resolve_hierarchy_sources(old).result_fingerprint
    )
    publish(
        s,
        publication(
            s,
            identity=first.publication.command.identity,
            relation=first.publication.command.relation,
            old=tombstone,
        ),
    )
    assert (
        resolve_hierarchy_sources(capture(s, [s["destination"]])).rows[0].status
        == "ELIGIBLE_RELATION"
    )


def test_l01_policy_supersession_needs_explicit_relation_repin(hierarchy_source):
    s = hierarchy_source
    first = publish(s, publication(s))
    relation = publish(s, relation_command(s, first))
    old = capture(s, [s["destination"]])
    second = publish(
        s, publication(s, policy=s["policy"].model_dump() | dict(policy_version=2), old=first)
    )
    assert (
        resolve_hierarchy_sources(capture(s, [s["destination"]])).rows[0].reason
        == "POLICY_SUPERSEDED"
    )
    with pytest.raises(DBAPIError, match="current active policy"):
        publish(
            s,
            publication(
                s,
                identity=relation.publication.command.identity,
                relation=relation.publication.command.relation,
                old=relation,
            ),
        )
    new_relation = relation.publication.command.relation.model_dump() | dict(
        policy_revision_id=second.publication.id,
        policy_fingerprint=second.publication.command.policy.fingerprint(),
    )
    publish(
        s,
        publication(
            s, identity=relation.publication.command.identity, relation=new_relation, old=relation
        ),
    )
    assert (
        resolve_hierarchy_sources(capture(s, [s["destination"]])).rows[0].status
        == "ELIGIBLE_RELATION"
    )
    assert resolve_hierarchy_sources(old).rows[0].selected_relation.id == relation.publication.id


@pytest.mark.parametrize("kind", ["POLICY", "RELATION"])
def test_l02_stale_cas_and_transaction_rollback_leave_no_partial_source(hierarchy_source, kind):
    s = hierarchy_source
    policy = publish(s, publication(s)) if kind == "RELATION" else None
    cmd = relation_command(s, policy) if policy else publication(s)
    baseline = capture(s)
    with Session(
        s["engines"]["curator"].execution_options(isolation_level="SERIALIZABLE")
    ) as session:
        publish_hierarchy_source(session, cmd)
        session.rollback()
    assert capture(s).frontier == baseline.frontier
    first = publish(s, cmd)
    with pytest.raises(DBAPIError, match="CAS conflict"):
        publish(s, cmd | dict(idempotency_key=uuid4().hex))
    assert capture(s).frontier.source_generation == first.frontier.source_generation


@pytest.mark.parametrize("kind", ["POLICY", "RELATION"])
def test_l02_real_two_writers_one_provider_frontier_winner(hierarchy_source, kind):
    s = hierarchy_source
    parent = publish(s, publication(s)) if kind == "RELATION" else None
    cmd = relation_command(s, parent) if parent else publication(s)
    gate = Barrier(2)

    def write(index):
        with Session(
            s["engines"]["curator"].execution_options(isolation_level="SERIALIZABLE")
        ) as session:
            try:
                gate.wait(timeout=5)
                result = publish_hierarchy_source(session, cmd | dict(idempotency_key=uuid4().hex))
                session.commit()
                return result
            except DBAPIError as exc:
                assert exc.orig.sqlstate in {"40001", "40P01"}
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, range(2)))
    assert sum(r is not None for r in results) == 1
    assert capture(s).frontier.source_generation == 1 + int(parent is not None)


def test_g01_same_kind_reverse_cycle_rejected_including_stale_policy_heads(hierarchy_source):
    s = hierarchy_source
    p = publish(s, publication(s))
    publish(s, relation_command(s, p))
    p2 = publish(s, publication(s, policy=s["policy"].model_dump() | dict(policy_version=2), old=p))
    with pytest.raises(DBAPIError, match="cycle"):
        publish(
            s,
            relation_command(s, p2, source=s["destination"], destination=s["target"])
            | dict(
                relation=dict(
                    policy_revision_id=p2.publication.id,
                    policy_fingerprint=p2.publication.command.policy.fingerprint(),
                    support_mode="REVIEWED_EXACT_PAIR",
                    support_review_id=None,
                    catalog_review_ids=[],
                )
            ),
        )
    assert capture(s).frontier.source_generation == 3


def test_g02_multiple_reviewed_parents_unavailable_without_selection(hierarchy_source):
    s = hierarchy_source
    p = publish(s, publication(s))
    publish(s, relation_command(s, p))
    with Session(s["engines"]["root"]) as session:
        other = Ingredient(name="Second exact parent")
        session.add(other)
        session.commit()
        target = dict(kind="INGREDIENT", ingredient_id=str(other.id))
    publish(s, relation_command(s, p, source=target))
    row = resolve_hierarchy_sources(capture(s, [s["destination"]])).rows[0]
    assert row.reason == "MULTIPLE_INCOMING_RELATIONS" and row.selected_relation is None
    assert len(row.relations) == 2


@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
def test_r01_coherent_capture_and_zero_io_recursive_replay(
    hierarchy_source, isolation, monkeypatch
):
    s = hierarchy_source
    p = publish(s, publication(s))
    publish(s, relation_command(s, p))
    source = capture(s, [s["destination"]], isolation=isolation)
    content = canonical(source)
    expected = resolve_hierarchy_sources(source)

    def forbidden(*args, **kwargs):
        raise AssertionError("IO during pure source replay")

    event.listen(Engine, "before_cursor_execute", forbidden)
    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr("socket.socket", forbidden)
    try:
        actual = resolve_hierarchy_sources(content)
        assert actual == expected
    finally:
        event.remove(Engine, "before_cursor_execute", forbidden)


@pytest.mark.parametrize(
    "field", ["mutations", "publications", "authority_events", "principals", "streams"]
)
def test_r01_omitted_complete_source_child_rejected_even_rehashed(hierarchy_source, field):
    s = hierarchy_source
    publish(s, publication(s))
    source = canonical(capture(s))
    source[field].pop()
    assert len(h.hierarchy_hash("hierarchy.source.v1", source)) == 64
    with pytest.raises(ValueError):
        h.HierarchySourceSnapshotDraft.model_validate(source)


@pytest.mark.parametrize(
    "isolation,readonly",
    [("READ COMMITTED", True), ("REPEATABLE READ", False), ("SERIALIZABLE", False)],
)
def test_r01_capture_requires_clean_readonly_coherent_transaction(
    hierarchy_source, isolation, readonly
):
    s = hierarchy_source
    with Session(
        s["engines"]["reader"].execution_options(
            isolation_level=isolation, postgresql_readonly=readonly
        )
    ) as session:
        with pytest.raises(DBAPIError, match="read-only RR/SERIALIZABLE"):
            capture_hierarchy_sources(
                session,
                dict(
                    provider_id=s["provider"].id,
                    policy_id=s["policy"].policy_id,
                    requested_targets=[],
                ),
            )


def test_l03_caller_time_unknown_fields_and_invalid_tombstone_rejected(hierarchy_source):
    s = hierarchy_source
    for field in ("recorded_at", "effective_at", "actor_user_id"):
        with pytest.raises(ValueError):
            h.HierarchyPublicationCommand.model_validate(
                publication(s) | {field: "2026-01-01T00:00:00Z"}
            )
    first = publish(s, publication(s))
    tombstone = publication(s, operation="RETRACT", old=first)
    with pytest.raises(ValueError, match="payload-free"):
        h.HierarchyPublicationCommand.model_validate(tombstone | dict(policy=s["policy"]))


def test_s02_populated_source_downgrade_refuses_history_loss(hierarchy_source):
    s = hierarchy_source
    publish(s, publication(s))
    with s["engines"]["root"].connect() as conn:
        config = s["config"]
        config.attributes["connection"] = conn
        conn.commit()
        with pytest.raises(DBAPIError, match="Refusing destructive"):
            alembic_command.downgrade(config, "0014")
        conn.rollback()
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
        assert (
            conn.scalar(
                text("SELECT count(*) FROM hierarchy_source_revisions WHERE provider_id=:p"),
                {"p": s["provider"].id},
            )
            == 1
        )


@pytest.mark.parametrize("retract", [False, True])
@pytest.mark.parametrize("revoke_first", [False, True])
def test_a04_l02_revoke_publication_races_order_on_shared_frontier(
    hierarchy_source, retract, revoke_first
):
    from app.modules.preferences.hierarchy_sources import change_hierarchy_authority
    from test_postgres_reference_priors import wait_for_lock

    s = hierarchy_source
    previous = publish(s, publication(s)) if retract else None
    cmd = publication(s, operation="RETRACT", old=previous) if retract else publication(s)
    cap = "RETRACT" if retract else "REVIEW_PUBLISH"
    revoke = dict(
        provider_id=s["provider"].id,
        principal_id=s["principals"]["curator"].id,
        capability=cap,
        action="REVOKE",
        expected_authority_generation=4,
        reason="Ordered concurrency test",
        idempotency_key=uuid4().hex,
    )

    def waiting():
        if revoke_first:
            try:
                return publish(s, cmd)
            except DBAPIError as exc:
                assert exc.orig.sqlstate in {"40001", "42501"}
                return None
        with Session(s["engines"]["admin"]) as session:
            result = change_hierarchy_authority(session, revoke)
            session.commit()
            return result

    engine = (
        s["engines"]["admin"]
        if revoke_first
        else s["engines"]["curator"].execution_options(isolation_level="SERIALIZABLE")
    )
    with Session(engine) as holder, ThreadPoolExecutor(max_workers=1) as pool:
        if revoke_first:
            change_hierarchy_authority(holder, revoke)
        else:
            publish_hierarchy_source(holder, cmd)
        future = pool.submit(waiting)
        try:
            wait_for_lock(s, "curator" if revoke_first else "admin")
        finally:
            holder.commit()
        result = future.result(timeout=10)
    assert (result is None) == revoke_first
    assert capture(s).frontier.source_generation == int(retract) + int(not revoke_first)
    if revoke_first:
        with pytest.raises(DBAPIError, match="capability denied"):
            publish(s, cmd)


@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
def test_r01_existing_capture_cut_is_stable_during_committed_publication(
    hierarchy_source, isolation
):
    s = hierarchy_source
    cmd = publication(s)
    with Session(
        s["engines"]["reader"].execution_options(
            isolation_level=isolation, postgresql_readonly=True
        )
    ) as reader:
        req = dict(
            provider_id=s["provider"].id, policy_id=s["policy"].policy_id, requested_targets=[]
        )
        first = capture_hierarchy_sources(reader, req)
        publish(s, cmd)
        same_cut = capture_hierarchy_sources(reader, req)
        assert same_cut.frontier == first.frontier
        assert not same_cut.publications
    assert capture(s).frontier.source_generation == 1


def test_l02_two_relation_retractors_have_one_cas_winner(hierarchy_source):
    s = hierarchy_source
    p = publish(s, publication(s))
    relation = publish(s, relation_command(s, p))
    cmd = publication(
        s, identity=relation.publication.command.identity, operation="RETRACT", old=relation
    )
    gate = Barrier(2)

    def retract(index):
        gate.wait(timeout=5)
        try:
            return publish(s, cmd | dict(idempotency_key=uuid4().hex))
        except DBAPIError as exc:
            assert exc.orig.sqlstate in {"40001", "40P01"}
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(retract, range(2)))
    assert sum(r is not None for r in results) == 1
    assert (
        resolve_hierarchy_sources(capture(s, [s["destination"]])).rows[0].reason
        == "RELATION_RETRACTED"
    )


def test_g02_diamond_merge_has_no_double_count_or_automatic_parent_selection(hierarchy_source):
    s = hierarchy_source
    p = publish(s, publication(s))
    with Session(s["engines"]["root"]) as root:
        nodes = [Ingredient(name="Diamond node") for _ in range(3)]
        root.add_all(nodes)
        root.commit()
        targets = [dict(kind="INGREDIENT", ingredient_id=str(i.id)) for i in nodes]
    a = s["target"]
    b, c, d = targets
    for source, destination in ((a, b), (a, c), (b, d), (c, d)):
        publish(s, relation_command(s, p, source=source, destination=destination))
    row = resolve_hierarchy_sources(capture(s, [d])).rows[0]
    assert row.reason == "MULTIPLE_INCOMING_RELATIONS" and row.selected_relation is None
    assert len(row.relations) == 2


def test_g01_cross_kind_cycle_rejects_without_recursive_preference_derivation(hierarchy_source):
    from app.modules.catalog.public import add_affinity_feature_term
    from hierarchy_fixtures import enable_direction, policy
    from preference_fixtures import term

    s = hierarchy_source
    with Session(s["engines"]["root"]) as root:
        t = term("PROTEIN")
        add_affinity_feature_term(root, t)
        root.commit()
    feature = dict(kind="PROTEIN", feature_term_id=str(t.id))
    s = dict(
        s,
        policy=enable_direction(
            policy(source_kind="INGREDIENT", destination_kind="PROTEIN"), "PROTEIN", "INGREDIENT"
        ),
    )
    p = publish(s, publication(s))
    publish(s, relation_command(s, p, destination=feature))
    with pytest.raises(DBAPIError, match="cycle"):
        publish(s, relation_command(s, p, source=feature, destination=s["target"]))


def test_r01_capture_authority_is_at_its_cut_not_a_live_token(hierarchy_source):
    from app.modules.preferences.hierarchy_sources import change_hierarchy_authority

    s = hierarchy_source
    with Session(
        s["engines"]["reader"].execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        )
    ) as reader:
        req = dict(
            provider_id=s["provider"].id, policy_id=s["policy"].policy_id, requested_targets=[]
        )
        old = capture_hierarchy_sources(reader, req)
        with Session(s["engines"]["admin"]) as admin:
            change_hierarchy_authority(
                admin,
                dict(
                    provider_id=s["provider"].id,
                    principal_id=s["principals"]["reader"].id,
                    capability="CAPTURE",
                    action="REVOKE",
                    expected_authority_generation=4,
                    reason="Capture permission revoked",
                    idempotency_key=uuid4().hex,
                ),
            )
            admin.commit()
        same = capture_hierarchy_sources(reader, req)
        assert same.reader_grant_id == old.reader_grant_id and same.frontier == old.frontier
        resolve_hierarchy_sources(same)
    with pytest.raises(DBAPIError, match="capability denied"):
        capture(s)


def test_i02_policy_lineage_has_no_fallback(hierarchy_source):
    s = hierarchy_source
    publish(s, publication(s))
    with Session(
        s["engines"]["reader"].execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        )
    ) as reader:
        cut = capture_hierarchy_sources(
            reader,
            dict(provider_id=s["provider"].id, policy_id=uuid4(), requested_targets=[s["target"]]),
        )
    assert resolve_hierarchy_sources(cut).rows[0].reason == "POLICY_MISSING"
