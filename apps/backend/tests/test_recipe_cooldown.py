"""INV-012/022/026/027: a policy predicate on proposed meals, never behavioral history."""

import json
from datetime import timedelta
from uuid import uuid4

import pytest
from app.modules.learning import contracts as c
from app.modules.learning.public import assess_recipe_cooldown
from app.modules.planning.contracts import PlanIntentGraph, PlanProposalSnapshot
from cooldown_fixtures import cooldown_input, with_graph
from pydantic import ValidationError


def test_positive_witness_has_exact_policy_relative_distance_and_primitive_identity():
    s = cooldown_input((-3600000000, -1, 0, 1))
    a = assess_recipe_cooldown(s)
    assert a.outcome == "MATCH_IN_SELECTED_PROPOSAL"
    assert sorted(w.distance_microseconds for w in a.witnesses) == [1, 3600000000]
    assert all(w.fact.meal_node_id != a.target.meal_node_id for w in a.witnesses)
    assert a.lookback_start == a.target.scheduled_at - timedelta(microseconds=7200000000)
    assert a.target.proposal_id == s.query.proposal_id
    assert a.target.status == "PROVISIONAL" and a.target.source_kind == "PROPOSAL_PREVIEW"


@pytest.mark.parametrize(
    "offset,match", [(-7200000001, False), (-7200000000, True), (-1, True), (0, False), (1, False)]
)
def test_half_open_temporal_boundaries(offset, match):
    a = assess_recipe_cooldown(cooldown_input((offset,)))
    assert bool(a.witnesses) is match


def test_target_alone_is_scoped_absence_not_safe_or_never_exposed():
    a = assess_recipe_cooldown(cooldown_input(()))
    assert a.outcome == "NO_MATCH_IN_SELECTED_PROPOSAL" and not a.witnesses
    assert a.absence_semantics == "NOT_GLOBAL_COOLDOWN_SAFETY_OR_NEVER_EXPOSED"
    assert not a.activation_ready
    for name in (
        "accepted_schedule",
        "confirmed_exposure",
        "consumption_history",
        "decay",
        "novelty",
        "taste_fit",
        "repeat_penalty",
    ):
        assert getattr(a, name) == "UNAVAILABLE"


@pytest.mark.parametrize("duration", [0, -1, True, 1.5, "5", float("nan"), float("inf")])
def test_policy_requires_positive_exact_integer(duration):
    p = cooldown_input().policy.model_dump() | {"duration_microseconds": duration}
    with pytest.raises(ValidationError):
        c.RecipeCooldownPolicy.model_validate(p)


def test_no_policy_or_duration_default_and_time_overflow_rejects():
    s = cooldown_input()
    for data in (s.model_dump(exclude={"policy"}), s.model_dump() | {"policy": None}):
        with pytest.raises(ValidationError):
            c.RecipeCooldownInput.model_validate(data)
    with pytest.raises(ValidationError):
        c.RecipeCooldownPolicy.model_validate(
            s.policy.model_dump(exclude={"duration_microseconds"})
        )
    with pytest.raises(ValueError, match="representable"):
        assess_recipe_cooldown(
            s.model_copy(
                update={"policy": s.policy.model_copy(update={"duration_microseconds": 10**30})}
            )
        )


@pytest.mark.parametrize(
    "field", ["household_id", "member_id", "plan_id", "proposal_id", "meal_node_id", "recipe_id"]
)
def test_wrong_target_identity_is_rejected(field):
    s = cooldown_input()
    with pytest.raises(ValueError):
        assess_recipe_cooldown(
            s.model_copy(update={"query": s.query.model_copy(update={field: uuid4()})})
        )


@pytest.mark.parametrize("mode", ["zero_sources", "empty_workspace", "multiple_sources"])
def test_exactly_one_nonempty_proposal_required(mode):
    s = cooldown_input()
    data = s.model_dump()
    if mode == "zero_sources":
        data["snapshot"].update(sources=(), recipes=())
    elif mode == "empty_workspace":
        data["snapshot"]["sources"][0]["proposal"] = None
        data["snapshot"]["sources"][0]["workspace"]["latest_proposal_no"] = -1
        data["snapshot"]["recipes"] = ()
    else:
        workspace = s.snapshot.sources[0].workspace.model_dump()
        workspace.update(id=uuid4(), latest_proposal_no=-1)
        data["snapshot"]["sources"] += ({"workspace": workspace, "proposal": None},)
        c.ExposurePreviewSnapshot.model_validate(data["snapshot"])  # Valid041A, invalid041B.
    with pytest.raises(ValueError):
        c.RecipeCooldownInput.model_validate(data)


@pytest.mark.parametrize("side", ["start", "end"])
def test_full_capture_window_required(side):
    s = cooldown_input()
    target = s.snapshot.sources[0].proposal.graph.meals[0].scheduled_at
    window = s.snapshot.policy.window.model_dump()
    window[side] = (
        target - timedelta(microseconds=s.policy.duration_microseconds - 1)
        if side == "start"
        else target - timedelta(microseconds=1)
    )
    source = s.snapshot.model_dump()
    source["policy"]["window"] = window
    with pytest.raises(ValueError, match="full cooldown"):
        assess_recipe_cooldown(
            s.model_copy(update={"snapshot": c.ExposurePreviewSnapshot.model_validate(source)})
        )


def test_window_may_end_exactly_at_target_target_resolved_from_graph():
    s = cooldown_input()
    data = s.snapshot.model_dump()
    data["policy"]["window"]["end"] = data["sources"][0]["proposal"]["graph"]["meals"][0][
        "scheduled_at"
    ]
    a = assess_recipe_cooldown(
        s.model_copy(update={"snapshot": c.ExposurePreviewSnapshot.model_validate(data)})
    )
    assert a.witnesses  # Target itself need not be inside the half-open source window.


@pytest.mark.parametrize(
    "mutation",
    ["retired_meal", "absent_member", "retired_allocation", "zero_allocation", "retired_batch"],
)
def test_target_requires_active_positive_allocation_and_participation(mutation):
    s = cooldown_input()
    g = s.snapshot.sources[0].proposal.graph.model_dump()
    if mutation == "retired_meal":
        g["meals"][0]["status"] = "RETIRED"
    elif mutation == "absent_member":
        g["meals"][0]["participants"][0]["member_id"] = uuid4()
    elif mutation == "retired_allocation":
        g["allocations"][0]["status"] = "RETIRED"
    elif mutation == "zero_allocation":
        g["allocations"][0]["servings"] = 0
    else:
        g["batches"][0]["status"] = "RETIRED"
    with pytest.raises(ValueError):
        assess_recipe_cooldown(s.model_copy(update={"snapshot": with_graph(s, g)}))


def test_nonparticipating_prior_meal_is_not_member_exposure():
    s = cooldown_input()
    data = s.snapshot.model_dump()
    other = uuid4()
    data["members"] += ({"household_id": s.snapshot.household_id, "member_id": other},)
    g = data["sources"][0]["proposal"]["graph"]
    g["meals"][-1]["participants"] = (
        {"member_id": other, "portion_factor": "1", "nutrition_role": "SHARED"},
    )
    a = assess_recipe_cooldown(
        s.model_copy(
            update={
                "snapshot": with_graph(
                    c.ExposurePreviewSnapshot.model_validate(
                        s.snapshot.model_dump() | {"members": data["members"]}
                    ),
                    g,
                )
            }
        )
    )
    assert a.outcome == "NO_MATCH_IN_SELECTED_PROPOSAL"


def test_result_recomputed_and_frozen_and_extra_fields_forbidden():
    a = assess_recipe_cooldown(cooldown_input())
    for changes in (
        {"witnesses": ()},
        {"outcome": "NO_MATCH_IN_SELECTED_PROPOSAL"},
        {"activation_ready": True},
        {"novelty": 0},
        {"is_safe": True},
        {"lookback_start": a.target.scheduled_at},
    ):
        with pytest.raises(ValidationError):
            c.RecipeCooldownAssessmentDraft.model_validate(a.model_dump() | changes)
    with pytest.raises(ValidationError):
        a.outcome = "NO_MATCH_IN_SELECTED_PROPOSAL"
    bad = a.model_dump()
    bad["witnesses"][0]["distance_microseconds"] += 1
    with pytest.raises(ValueError, match="primitives"):
        c.RecipeCooldownAssessmentDraft.model_validate(bad)


def test_deterministic_hash_roundtrip_unordered_sources_policy_and_material_identity():
    s = cooldown_input((-3600000000, -1))
    a = assess_recipe_cooldown(s)
    shuffled = s.snapshot.model_dump()
    g = shuffled["sources"][0]["proposal"]["graph"]
    for key in ("meals", "allocations"):
        g[key] = tuple(reversed(g[key]))
    b = assess_recipe_cooldown(
        s.model_copy(update={"snapshot": c.ExposurePreviewSnapshot.model_validate(shuffled)})
    )
    assert a.canonical_json() == b.canonical_json() and a.fingerprint() == b.fingerprint()
    wire = c.RecipeCooldownAssessmentDraft.model_validate_json(a.canonical_json())
    assert wire.canonical_json() == a.canonical_json()
    for key, value in (
        ("policy_version", "test.v2"),
        ("policy_id", "other"),
        ("duration_microseconds", 7199999999),
    ):
        changed = assess_recipe_cooldown(
            s.model_copy(update={"policy": s.policy.model_copy(update={key: value})})
        )
        assert changed.fingerprint() != a.fingerprint()
        assert changed.subject.policy.fingerprint() != s.policy.fingerprint()
    provenance = s.policy.provenance.model_copy(update={"source_version": "changed"})
    changed = assess_recipe_cooldown(
        s.model_copy(update={"policy": s.policy.model_copy(update={"provenance": provenance})})
    )
    assert changed.fingerprint() != a.fingerprint()
    assert json.loads(a.canonical_json())["subject"]["policy"]["provenance"]


def test_future_policy_cannot_enter_captured_subject():
    s = cooldown_input()
    with pytest.raises(ValueError, match="after capture"):
        assess_recipe_cooldown(
            s.model_copy(
                update={
                    "policy": s.policy.model_copy(
                        update={
                            "provenance": s.policy.provenance.model_copy(
                                update={
                                    "observed_at": s.snapshot.captured_at
                                    + timedelta(microseconds=1)
                                }
                            )
                        }
                    )
                }
            )
        )


@pytest.mark.parametrize(
    "kind", ["RECIPE_VERSION", "METHOD", "PROTEIN", "FLAVOR", "VARIANT_FAMILY"]
)
def test_unsupported_fingerprints_never_default_zero(kind):
    s = cooldown_input()
    with pytest.raises(ValueError):
        assess_recipe_cooldown(
            s.model_copy(update={"policy": s.policy.model_copy(update={"fingerprint_kind": kind})})
        )


def test_one_microsecond_policy_and_elapsed_time_do_not_promote_evidence():
    s = cooldown_input((-1,))
    a = assess_recipe_cooldown(
        s.model_copy(update={"policy": s.policy.model_copy(update={"duration_microseconds": 1})})
    )
    assert a.witnesses[0].distance_microseconds == 1
    assert a.target.scheduled_at < s.snapshot.captured_at
    assert a.witnesses[0].fact.status == "PROVISIONAL"


def test_multiple_batches_and_versions_count_once_and_entire_target_is_excluded():
    s = cooldown_input()
    src = s.snapshot.sources[0]
    data = src.proposal.graph.model_dump(exclude={"culinary_bindings"})
    data["contract_version"] = "plan-intent.v2"
    for batch in data["batches"]:
        batch.pop("culinary_signature")
    identity = s.snapshot.recipes[0].model_copy(update={"recipe_version_id": uuid4(), "version": 2})
    second = {
        **data["batches"][0],
        "node_id": uuid4(),
        "recipe_version_id": identity.recipe_version_id,
    }
    data["batches"] += (second,)
    data["allocations"] += tuple(
        {**a, "node_id": uuid4(), "batch_node_id": second["node_id"]} for a in data["allocations"]
    )
    graph = PlanIntentGraph.model_validate(data)
    p = PlanProposalSnapshot.model_validate(
        src.proposal.model_dump(exclude={"contract_version"})
        | {"graph": graph, "graph_hash": graph.fingerprint()}
    )
    source = c.ExposurePreviewSnapshot.model_validate(
        s.snapshot.model_dump()
        | {
            "sources": ({"workspace": src.workspace, "proposal": p},),
            "recipes": (*s.snapshot.recipes, identity),
        }
    )
    a = assess_recipe_cooldown(s.model_copy(update={"snapshot": source}))
    assert len(a.target.support) == 2 and len(a.witnesses) == 1
    assert len(a.witnesses[0].fact.support) == 2


def test_prior_recipe_change_alters_result_and_identity():
    s = cooldown_input()
    a = assess_recipe_cooldown(s)
    source = s.snapshot
    original = source.recipes[0]
    other = original.model_copy(update={"recipe_id": uuid4()})
    changed = source.model_copy(update={"recipes": (other,)})
    # Same source meal paths now resolve to a different recipe identity; query must agree.
    b = assess_recipe_cooldown(
        s.model_copy(
            update={
                "snapshot": changed,
                "query": s.query.model_copy(update={"recipe_id": other.recipe_id}),
            }
        )
    )
    assert a.fingerprint() != b.fingerprint()
    assert b.target.recipe_id == other.recipe_id


def test_other_recipe_prior_meal_does_not_match_even_with_same_method_and_time():
    s = cooldown_input()
    src = s.snapshot.sources[0]
    data = src.proposal.graph.model_dump(exclude={"culinary_bindings"})
    data["contract_version"] = "plan-intent.v2"
    for batch in data["batches"]:
        batch.pop("culinary_signature")
    other = s.snapshot.recipes[0].model_copy(
        update={"recipe_version_id": uuid4(), "recipe_id": uuid4()}
    )
    batch = {**data["batches"][0], "node_id": uuid4(), "recipe_version_id": other.recipe_version_id}
    data["batches"] += (batch,)
    data["allocations"][-1]["batch_node_id"] = batch["node_id"]
    graph = PlanIntentGraph.model_validate(data)
    p = PlanProposalSnapshot.model_validate(
        src.proposal.model_dump(exclude={"contract_version"})
        | {"graph": graph, "graph_hash": graph.fingerprint()}
    )
    source = c.ExposurePreviewSnapshot.model_validate(
        s.snapshot.model_dump()
        | {
            "sources": ({"workspace": src.workspace, "proposal": p},),
            "recipes": (*s.snapshot.recipes, other),
        }
    )
    a = assess_recipe_cooldown(s.model_copy(update={"snapshot": source}))
    assert a.outcome == "NO_MATCH_IN_SELECTED_PROPOSAL"
