"""Golden wire hashes captured from frozen pre-0010 source; not a regenerated expectation."""

from datetime import UTC, datetime
from uuid import UUID

import inventory_fixtures
import plan_fixtures
import pytest
import recipe_fixtures
import validation_fixtures
from app.modules.planning.contracts import PlanIntentGraph


def fixed_subject(monkeypatch):
    sequence = iter(range(1, 1000))
    for module in (inventory_fixtures, plan_fixtures, recipe_fixtures, validation_fixtures):
        monkeypatch.setattr(module, "uuid4", lambda: UUID(int=next(sequence)))
    fixed = datetime(2026, 10, 23, tzinfo=UTC)
    for module in (plan_fixtures, validation_fixtures):
        monkeypatch.setattr(module, "NOW", fixed)
    return validation_fixtures.subject()


@pytest.mark.parametrize(
    "version,expected",
    [
        ("plan-intent.v1", "7473b9f78953d5c7adbec838fcb51f1e8aa91acb16155a2bf7c44d185b633264"),
        ("plan-intent.v2", "0b6703902664623a60559567e57b982da49794b47cd129006af8135fde4250f3"),
    ],
)
def test_frozen_plan_wire_hashes(monkeypatch, version, expected):
    s = fixed_subject(monkeypatch)
    g = PlanIntentGraph.model_validate(
        s.proposal.graph.model_dump() | {"contract_version": version}
    )
    assert g.fingerprint() == expected


def test_frozen_validation_subject_v1_hash(monkeypatch):
    assert (
        fixed_subject(monkeypatch).fingerprint
        == "7fd32bc476e937427e1b8a3d3034e6ed6876d657f9520588df62693627867287"
    )
