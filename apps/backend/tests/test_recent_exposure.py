import ast
import json
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from app.modules.learning import contracts as c
from app.modules.learning.public import deduplicate_preview_facts, preview_recent_exposure
from app.modules.planning import contracts as p
from exposure_fixtures import snapshot
from pydantic import ValidationError
from test_architecture import check_source


def test_preview_is_not_consumption_and_elapsed_time_never_confirms():
    s = snapshot()
    result = preview_recent_exposure(s)
    assert result.facts and all(f.scheduled_at < s.captured_at for f in result.facts)
    assert all(
        f.status == "PROVISIONAL" and f.source_kind == "PROPOSAL_PREVIEW" for f in result.facts
    )
    assert result.activation_ready is False and s.consumption_history == "UNAVAILABLE"
    assert (
        c.RecipeExposurePreviewDraft.model_validate_json(result.canonical_json()).canonical_json()
        == result.canonical_json()
    )
    with pytest.raises(ValidationError):
        result.activation_ready = True


@pytest.mark.parametrize("claim", ["CONFIRMED", "COOKED", "CONSUMED", "AUTOPILOT_ASSUMED"])
def test_status_cannot_be_forged(claim):
    fact = preview_recent_exposure(snapshot()).facts[0]
    with pytest.raises(ValidationError):
        c.RecipeExposurePreviewFact.model_validate(fact.model_dump() | {"status": claim})
    with pytest.raises(ValidationError):
        c.RecipeExposurePreviewFact.model_validate(fact.model_dump() | {"source_kind": claim})


@pytest.mark.parametrize("field", ["repeat_score", "taste_fit", "EvidenceStrength", "consumed_at"])
def test_no_behavioral_summary_or_consumption_input(field):
    s = snapshot()
    with pytest.raises(ValidationError):
        c.ExposurePreviewSnapshot.model_validate(s.model_dump() | {field: 1})


def test_empty_history_is_not_never_exposed():
    s = snapshot()
    empty = c.ExposurePreviewSnapshot.model_validate(
        s.model_dump() | {"sources": (), "recipes": ()}
    )
    evidence = preview_recent_exposure(empty).evidence_for(uuid4())
    assert evidence.occurrence_count == 0
    assert evidence.consumption_history == "UNAVAILABLE"
    assert evidence.absence_semantics == "NOT_EVIDENCE_OF_NEVER_EXPOSED"


def test_lookup_validates_recipe_identity_before_filtering():
    result = preview_recent_exposure(snapshot())
    assert result.evidence_for(str(result.facts[0].recipe_id)).occurrence_count == 1
    with pytest.raises(ValidationError):
        result.evidence_for("not-a-recipe-uuid")


@pytest.mark.parametrize("kind", ["VARIANT_ID", "VARIANT_FAMILY", "METHOD", "PROTEIN", "FLAVOR"])
def test_unsupported_fingerprints_do_not_default_zero(kind):
    result = preview_recent_exposure(snapshot())
    with pytest.raises(ValueError, match="Unsupported"):
        result.evidence_for(result.facts[0].recipe_id, fingerprint_kind=kind)


def test_hash_policy_material_frontier_and_canonical_serialization():
    s = snapshot()
    shuffled = c.ExposurePreviewSnapshot.model_validate(
        s.model_dump()
        | {
            "members": tuple(reversed(s.members)),
            "recipes": tuple(reversed(s.recipes)),
            "sources": tuple(reversed(s.sources)),
        }
    )
    assert s.fingerprint() == shuffled.fingerprint()
    assert (
        preview_recent_exposure(s).canonical_json()
        == preview_recent_exposure(shuffled).canonical_json()
    )
    changed = c.ExposurePreviewSnapshot.model_validate(
        s.model_dump() | {"policy": s.policy.model_copy(update={"policy_version": "test.v2"})}
    )
    assert s.fingerprint() != changed.fingerprint()
    assert s.frontier_hash() == changed.frontier_hash()
    assert (
        s.canonical_json()
        == c.ExposurePreviewSnapshot.model_validate_json(s.canonical_json()).canonical_json()
    )
    raw = json.loads(s.canonical_json())
    raw["recipes"][0]["recipe_id"] = str(uuid4())
    assert c.ExposurePreviewSnapshot.model_validate(raw).fingerprint() != s.fingerprint()


def test_overlapping_windows_deduplicate_and_conflicting_revision_rejects():
    s = snapshot()
    a = preview_recent_exposure(s)
    wider = s.model_copy(
        update={
            "policy": s.policy.model_copy(
                update={
                    "window": s.policy.window.model_copy(
                        update={"start": s.policy.window.start - timedelta(days=1)}
                    )
                }
            )
        }
    )
    b = preview_recent_exposure(wider)
    assert deduplicate_preview_facts((*a.facts, *b.facts)) == a.facts
    changed = a.facts[0].model_copy(update={"proposal_id": uuid4()})
    assert changed.event_key() == a.facts[0].event_key()
    with pytest.raises(ValueError, match="Conflicting"):
        deduplicate_preview_facts((*a.facts, changed))


def test_recipe_changed_between_revisions_cannot_double_count_old_and_new():
    fact = preview_recent_exposure(snapshot()).facts[0]
    changed = fact.model_copy(update={"recipe_id": uuid4(), "proposal_id": uuid4()})
    assert changed.event_key() != fact.event_key()
    with pytest.raises(ValueError, match="Conflicting"):
        deduplicate_preview_facts((fact, changed))


def test_actual_unordered_graph_facts_can_be_permuted_without_hash_change():
    s = snapshot()
    source = s.sources[0]
    g = source.proposal.graph
    binding = g.culinary_bindings[0].model_copy(
        update={
            "requirements": tuple(reversed(g.culinary_bindings[0].requirements)),
        }
    )
    graph = g.model_copy(
        update={
            "meals": tuple(reversed(g.meals)),
            "culinary_bindings": (binding,),
        }
    )
    other = s.model_copy(
        update={
            "sources": (
                source.model_copy(
                    update={
                        "proposal": source.proposal.model_copy(update={"graph": graph}),
                    }
                ),
            )
        }
    )
    assert (
        preview_recent_exposure(s).canonical_json()
        == preview_recent_exposure(other).canonical_json()
    )


def test_forced_reason_is_only_intent_metadata_not_voluntary_preference():
    s = snapshot()
    source = s.sources[0]
    changed = s.model_copy(
        update={
            "sources": (
                source.model_copy(
                    update={
                        "proposal": source.proposal.model_copy(
                            update={"reason": "FORCED_CONFLICT_RESOLUTION"}
                        )
                    }
                ),
            )
        }
    )
    result = preview_recent_exposure(changed)
    assert result.facts == preview_recent_exposure(s).facts
    assert "taste" not in type(result).model_fields and not result.activation_ready


@pytest.mark.parametrize(
    "source",
    [
        "import sqlalchemy",
        "import psycopg",
        "import ortools",
        "import httpx",
        "from app.persistence.database import create_database_engine",
        "from app.modules.execution.public import PlanRevisionService",
        "from app.modules.preferences.public import PreferenceService",
        "from app.modules.planning.public import PlanStore",
    ],
)
def test_checker_rejects_io_and_mutation_dependencies_in_exposure_core(source):
    assert check_source(source, "app.modules.learning.public")


def test_half_open_window_and_unparticipating_member():
    s = snapshot()
    instant = preview_recent_exposure(s).facts[0].scheduled_at

    def window(start, end):
        return preview_recent_exposure(
            s.model_copy(
                update={
                    "policy": s.policy.model_copy(
                        update={"window": s.policy.window.__class__(start=start, end=end)}
                    )
                }
            )
        )

    assert not window(instant - timedelta(days=1), instant).facts
    assert window(instant, instant + timedelta(seconds=1)).facts
    other = s.members[0].model_copy(update={"member_id": uuid4()})
    absent = s.model_copy(update={"member_id": other.member_id, "members": (*s.members, other)})
    assert not preview_recent_exposure(absent).facts


@pytest.mark.parametrize(
    "mutation", ["household", "participant", "missing_recipe", "duplicate_source", "cutoff"]
)
def test_invalid_source_primitives_rejected(mutation):
    s = snapshot()
    changes = {
        "household": {"household_id": uuid4()},
        "participant": {"members": (s.members[0].model_copy(update={"member_id": uuid4()}),)},
        "missing_recipe": {"recipes": ()},
        "duplicate_source": {"sources": s.sources * 2},
        "cutoff": {"captured_at": s.policy.provenance.observed_at - timedelta(days=1)},
    }
    with pytest.raises(ValidationError):
        preview_recent_exposure(s.model_copy(update=changes[mutation]))


def test_cached_output_cannot_override_primitives():
    result = preview_recent_exposure(snapshot())
    with pytest.raises(ValidationError, match="captured primitives"):
        c.RecipeExposurePreviewDraft.model_validate(result.model_dump() | {"facts": ()})


def test_two_versions_batches_one_recipe_meal_count_once():
    s = snapshot()
    src = s.sources[0]
    data = src.proposal.graph.model_dump(exclude={"culinary_bindings"})
    data["contract_version"] = "plan-intent.v2"
    for b in data["batches"]:
        b.pop("culinary_signature")
    recipe = s.recipes[0].model_copy(update={"recipe_version_id": uuid4(), "version": 2})
    data["batches"] += (
        {**data["batches"][0], "node_id": uuid4(), "recipe_version_id": recipe.recipe_version_id},
    )
    data["allocations"] += (
        {
            **data["allocations"][0],
            "node_id": uuid4(),
            "batch_node_id": data["batches"][-1]["node_id"],
        },
    )
    graph = p.PlanIntentGraph.model_validate(data)
    proposal = p.PlanProposalSnapshot.model_validate(
        src.proposal.model_dump(exclude={"contract_version"})
        | {"graph": graph, "graph_hash": graph.fingerprint()}
    )
    updated = s.model_copy(
        update={
            "recipes": (*s.recipes, recipe),
            "sources": (c.ProposalExposureSource(workspace=src.workspace, proposal=proposal),),
        }
    )
    result = preview_recent_exposure(updated)
    assert len(result.facts) == 1 and len(result.facts[0].support) == 2
    assert result.evidence_for(recipe.recipe_id).occurrence_count == 1


def test_learning_core_has_no_io_execution_optimizer_or_preference_runtime():
    root = Path(__file__).resolve().parents[1] / "app/modules/learning"
    for file in (root / "public.py", root / "contracts.py"):
        for node in ast.walk(ast.parse(file.read_text())):
            if isinstance(node, ast.Import):
                names = [n.name for n in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(
                n.startswith(("sqlalchemy", "psycopg", "ortools", "socket", "httpx")) for n in names
            )
            for name in names:
                if name.startswith("app.modules.") and not name.startswith("app.modules.learning"):
                    assert name.endswith(".contracts")
                    assert not name.startswith(("app.modules.execution", "app.modules.preferences"))
