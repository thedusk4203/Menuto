"""Hierarchy publication/capture through authenticated PostgreSQL sessions."""

from uuid import uuid4

import pytest
from app.modules.preferences.hierarchy_resolution import resolve_hierarchy_sources
from app.modules.preferences.hierarchy_sources import register_hierarchy_provider
from hierarchy_postgres_fixtures import capture, publication, publish
from hierarchy_postgres_fixtures import hierarchy_server as hierarchy_server
from hierarchy_postgres_fixtures import hierarchy_source as hierarchy_source
from sqlalchemy.orm import Session

pytestmark = pytest.mark.postgres


def test_r01_durable_rows_hold_owner_pins_not_capture_snapshots(hierarchy_source):
    from sqlalchemy import inspect, text

    s = hierarchy_source
    receipt = publish(s, publication(s))
    with s["engines"]["root"].connect() as root:
        columns = {c["name"] for c in inspect(root).get_columns("hierarchy_source_revisions")}
        assert "owner_pins" in columns and "owner_source" not in columns
        pins = root.scalar(
            text("SELECT owner_pins FROM hierarchy_source_revisions WHERE id=:id"),
            {"id": receipt.publication.id},
        )
        assert set(pins) == {"targets", "facts", "catalog_frontier", "recipe_frontier"}
        assert all(set(f) == {"kind", "id", "fingerprint"} for f in pins["facts"])
    assert capture(s).publications[0].owner_source == receipt.publication.owner_source


def test_a01_separate_hierarchy_registration_and_enrollment(hierarchy_server):
    s = hierarchy_server
    with Session(s["engines"]["admin"]) as session:
        provider = register_hierarchy_provider(
            session,
            dict(
                code="synthetic." + uuid4().hex,
                version="1",
                source_system="hierarchy.test",
                remit="Synthetic source only",
                idempotency_key=uuid4().hex,
            ),
        )
        session.commit()
    assert provider.administrator.role_name == s["names"]["admin"]


def test_l01_policy_publication_and_complete_source_replay(hierarchy_source):
    s = hierarchy_source
    receipt = publish(s, publication(s))
    source = capture(s)
    result = resolve_hierarchy_sources(source)
    assert receipt.publication.command.policy == s["policy"]
    assert source.frontier.source_generation == 1
    assert result.rows[0].reason == "NO_RELATION"
    assert not result.planner_ready and not result.activation_ready


def test_i01_exact_relation_publication_and_eligibility(hierarchy_source):
    s = hierarchy_source
    policy = publish(s, publication(s))
    identity = dict(
        kind="RELATION",
        policy_id=s["policy"].policy_id,
        source=s["target"],
        destination=s["destination"],
        recipe_bindings=[],
    )
    relation = dict(
        policy_revision_id=policy.publication.id,
        policy_fingerprint=s["policy"].fingerprint(),
        support_mode="REVIEWED_EXACT_PAIR",
        support_review_id=None,
        catalog_review_ids=[],
    )
    publish(s, publication(s, identity=identity, relation=relation))
    result = resolve_hierarchy_sources(capture(s, [s["destination"]]))
    assert result.rows[0].status == "ELIGIBLE_RELATION"
    assert (
        result.rows[0].selected_relation.command.identity.source.ingredient_id
        == s["target"]["ingredient_id"]
        or str(result.rows[0].selected_relation.command.identity.source.ingredient_id)
        == s["target"]["ingredient_id"]
    )
