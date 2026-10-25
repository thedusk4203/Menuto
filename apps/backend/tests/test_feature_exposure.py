"""MTR-041E source join: adversarial identity, provenance, coverage and replay."""

from datetime import timedelta
from uuid import uuid4

import pytest
from app.modules.learning import contracts as c
from app.modules.learning.public import preview_feature_exposure as preview
from app.modules.planning import contracts as p
from app.modules.planning.feature_preview import discover_culinary_feature_assignments as discover
from feature_exposure_fixtures import remap, source
from test_architecture import check_source


def test_multi_batch_multi_meal_multi_member_identity_and_complete_support():
    s = source()
    result = preview(s)
    assert len(result.events) == 4  # 2 members × 2 meals, never × 2 batches
    assert len(result.diagnostics) == 8
    for fact in result.events:
        assert len(fact.support) == 2
        assert {w.participant.member_id for w in fact.support} == {fact.member_id}
        assert all(w.assignment.term_id == fact.feature_term_id for w in fact.support)
        assert len({w.batch_node_id for w in fact.support}) == 2
        assert all(
            w.recipe_id
            and w.recipe_version_id
            and w.applicability_id
            and w.assignment.review_id
            and w.subject_hash
            and w.discovery_hash
            for w in fact.support
        )
    assert not result.activation_ready
    assert result.absence_semantics == "NOT_EVIDENCE_OF_NEVER_EXPOSED_OR_GLOBAL_FEATURE_ABSENCE"
    assert result.evidence_cuts[0].authority == "DIAGNOSTIC_ONLY_NOT_LIVENESS_OR_AUTHORIZATION"
    assert (
        c.FeatureExposurePreviewDraft.model_validate_json(result.canonical_json()).canonical_json()
        == result.canonical_json()
    )


@pytest.mark.parametrize("dimension", ["METHOD", "FLAVOR"])
@pytest.mark.parametrize(
    "coverage,positives,empty,state",
    [
        ("PARTIAL", True, False, "ASSIGNED"),
        ("COMPLETE", True, False, "ASSIGNED"),
        ("COMPLETE", False, False, "REVIEWED_NONE"),
        ("PARTIAL", False, False, "UNRESOLVED"),
        ("COMPLETE", False, True, "UNRESOLVED"),
    ],
)
def test_finite_coverage_not_global_absence(dimension, coverage, positives, empty, state):
    result = preview(
        source(dimension=dimension, coverage=coverage, positives=positives, empty=empty)
    )
    assert all(d.discovery.state == state for d in result.diagnostics)
    assert bool(result.events) == (positives and not empty)
    assert result.repeat_penalty == result.novelty == result.taste_fit == "UNAVAILABLE"
    assert result.accepted_schedule == result.consumption_history == "UNAVAILABLE"
    assert result.confirmed_exposure == result.durable_history == "UNAVAILABLE"


def test_empty_eligible_window_has_machine_readable_scoped_absence():
    s = source()
    data = s.model_dump()
    policy = s.request.recipe_eligibility_policy.model_dump()
    first = s.member_sources[0].sources[0].proposal.graph.meals[0].scheduled_at
    policy["window"] = dict(start=first - timedelta(hours=3), end=first)
    data["request"]["recipe_eligibility_policy"] = policy
    for m in data["member_sources"]:
        m["policy"] = policy
    data["classification_sources"] = ()
    result = preview(c.FeatureExposureSourceSnapshotDraft.model_validate(data))
    assert not result.events and not result.diagnostics
    assert result.coverage == "SELECTED_PROPOSAL_FEATURE_PREVIEW_ONLY"
    assert result.absence_semantics == "NOT_EVIDENCE_OF_NEVER_EXPOSED_OR_GLOBAL_FEATURE_ABSENCE"
    assert len(result.evidence_cuts) == 1


def test_two_distinct_terms_and_no_string_mass_inference():
    s = source()
    data = s.model_dump()
    for d in data["classification_sources"]:
        e = d["subject"]["evaluation"]
        scope = e["sources"]["scopes"][0]
        review = scope["reviews"][0]
        review["command"]["positive_term_ids"] = review["command"]["covered_term_ids"]
        from app.modules.recipes.contracts import RecipeOnlyFeatureCommand

        cmd = RecipeOnlyFeatureCommand.model_validate(review["command"])
        review["command_hash"] = cmd.fingerprint(review["reviewer_user_id"])
        child = p.CapturedCulinaryFeatureSubjectDraft.model_validate(d["subject"])
        d.update(discover(child).model_dump())
    result = preview(c.FeatureExposureSourceSnapshotDraft.model_validate(data))
    assert len(result.events) == 8
    assert len({e.feature_term_id for e in result.events}) == 2


def test_unordered_fact_permutation_preserves_bytes_and_digest():
    s = source()
    data = s.model_dump()
    for name in ("member_sources", "classification_sources", "frontiers"):
        data[name] = data[name][::-1]
    data["request"]["selected_member_ids"] = data["request"]["selected_member_ids"][::-1]
    for m in data["member_sources"]:
        m["members"] = m["members"][::-1]
        g = m["sources"][0]["proposal"]["graph"]
        for name in ("meals", "allocations", "batches", "culinary_bindings"):
            g[name] = g[name][::-1]
    for d in data["classification_sources"]:
        d["subject"]["evaluation"]["sources"]["terms"] = d["subject"]["evaluation"]["sources"][
            "terms"
        ][::-1]
    again = c.FeatureExposureSourceSnapshotDraft.model_validate(data)
    assert s.canonical_json() == again.canonical_json()
    assert preview(s).canonical_json() == preview(again).canonical_json()


def test_child_clock_differences_change_audit_hash_not_semantic_cut():
    s = source()
    data = s.model_dump()
    data["member_sources"][0]["captured_at"] += timedelta(seconds=1)
    d = data["classification_sources"][0]
    d["subject"]["evaluation"]["captured_at"] += timedelta(seconds=2)
    d.update(
        discover(p.CapturedCulinaryFeatureSubjectDraft.model_validate(d["subject"])).model_dump()
    )
    again = c.FeatureExposureSourceSnapshotDraft.model_validate(data)
    a, b = preview(s), preview(again)
    assert a.fingerprint() != b.fingerprint()
    assert a.evidence_cuts == b.evidence_cuts
    assert [f.event_key() for f in a.events] == [f.event_key() for f in b.events]


def test_equal_timestamps_do_not_order_or_merge_distinct_meals():
    s = source()
    g = s.member_sources[0].sources[0].proposal.graph
    data = g.model_dump()
    for m in data["meals"]:
        m["scheduled_at"] = g.meals[0].scheduled_at
    result = preview(
        c.FeatureExposureSourceSnapshotDraft.model_validate(
            remap(s, graph=p.BoundPlanIntentGraph.model_validate(data))
        )
    )
    assert len(result.events) == 4
    assert len({e.scheduled_at for e in result.events}) == 1


@pytest.mark.parametrize("field", ["selected_member_ids", "requested_dimensions"])
def test_request_duplicate_rejected(field):
    q = source().request.model_dump()
    q[field] += q[field][:1]
    with pytest.raises(ValueError):
        c.FeatureExposurePreviewRequest.model_validate(q)


@pytest.mark.parametrize(
    "field,value",
    [
        ("requested_dimensions", ("PROTEIN",)),
        ("requested_dimensions", ("FAMILY",)),
        ("requested_dimensions", ("RECIPE_ID",)),
        ("requested_dimensions", ()),
        ("selected_member_ids", ()),
        ("term_ids", (uuid4(),)),
        ("is_safe", True),
        ("feature_weight", 1),
    ],
)
def test_closed_request_no_invented_semantics(field, value):
    with pytest.raises(ValueError):
        c.FeatureExposurePreviewRequest.model_validate(
            source().request.model_dump() | {field: value}
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_source",
        "extra_source",
        "frontier",
        "foreign_member",
        "foreign_plan",
        "foreign_recipe",
        "future_capture",
        "policy",
        "mixed_proposal",
        "catalog_on_flavor",
        "discovery",
        "conflicting_scope",
        "recipe_identity",
        "nonpositive_allocation",
    ],
)
def test_forged_or_mixed_capture_fails_closed(mutation):
    s = source()
    data = s.model_dump()
    child = data["classification_sources"][0]
    if mutation == "missing_source":
        data["classification_sources"] = data["classification_sources"][1:]
    elif mutation == "extra_source":
        data["classification_sources"] += data["classification_sources"][:1]
    elif mutation == "frontier":
        data["frontiers"][0]["recipe_frontier"] += 1
    elif mutation == "foreign_member":
        data["request"]["selected_member_ids"] = (uuid4(),)
    elif mutation == "foreign_plan":
        data["request"]["plan_id"] = uuid4()
    elif mutation == "foreign_recipe":
        child["subject"]["evaluation"]["recipe"]["id"] = uuid4()
    elif mutation == "future_capture":
        data["capture_completed_at"] -= timedelta(days=1)
    elif mutation == "policy":
        data["member_sources"][0]["policy"]["policy_version"] = "other"
    elif mutation == "mixed_proposal":
        data["request"]["proposal_id"] = uuid4()
    elif mutation == "catalog_on_flavor":
        data["frontiers"][0]["catalog_frontier"] = 0
    elif mutation == "discovery":
        child["dimensions"][0]["positive_term_ids"] = ()
    elif mutation == "conflicting_scope":
        child["subject"]["evaluation"]["sources"]["scopes"] = ()
    elif mutation == "recipe_identity":
        data["member_sources"][0]["recipes"][0]["recipe_id"] = uuid4()
    else:
        data["member_sources"][0]["sources"][0]["proposal"]["graph"]["allocations"][0][
            "servings"
        ] = 0
    with pytest.warns(UserWarning, match="Pydantic serializer"), pytest.raises(ValueError):
        preview(c.FeatureExposureSourceSnapshotDraft.model_construct(**data))


@pytest.mark.parametrize("mutation", ["digest", "event", "witness", "coverage", "duplicate"])
def test_cached_result_cannot_mint_evidence_or_digest(mutation):
    result = preview(source())
    data = result.model_dump()
    if mutation == "digest":
        data["evidence_cuts"][0]["digest"] = "0" * 64
    elif mutation == "event":
        data["events"][0]["feature_term_id"] = uuid4()
    elif mutation == "witness":
        data["events"][0]["support"][0]["subject_hash"] = "0" * 64
    elif mutation == "coverage":
        data["diagnostics"][0]["discovery"]["state"] = "REVIEWED_NONE"
    else:
        data["events"][0]["support"] += data["events"][0]["support"][:1]
    with pytest.raises(ValueError):
        c.FeatureExposurePreviewDraft.model_validate(data)


def test_core_is_immutable_and_reproducible_with_no_feature_policy():
    a = preview(source())
    with pytest.raises(ValueError):
        a.activation_ready = True
    assert preview(a.snapshot).fingerprint() == a.fingerprint()
    for field in ("score", "probability", "evidence_strength", "profile", "rank", "is_safe"):
        with pytest.raises(ValueError):
            c.FeatureExposurePreviewDraft.model_validate(a.model_dump() | {field: 0})


@pytest.mark.parametrize(
    "target",
    [
        "sqlalchemy",
        "psycopg",
        "ortools",
        "requests",
        "app.modules.planning.feature_preview",
        "app.modules.planning.public",
        "app.modules.preferences.public",
        "app.modules.execution.public",
    ],
)
def test_learning_core_import_boundaries(target):
    assert check_source(f"import {target}", "app.modules.learning.contracts")
    assert check_source(f"import {target}", "app.modules.learning.public")


@pytest.mark.parametrize("mode", ["tier", "rule", "delta"])
@pytest.mark.parametrize("dimension", ["METHOD", "FLAVOR"])
def test_method_context_invariant_but_flavor_uses_exact_selected_path(mode, dimension):
    from app.modules.planning.culinary import author_binding

    s = source(dimension=dimension, batches=1, meals=1, members=1)
    recipe = s.classification_sources[0].subject.evaluation.recipe
    g = s.member_sources[0].sources[0].proposal.graph
    old = g.culinary_bindings[0]
    binding = author_binding(
        recipe=recipe,
        tier_id=recipe.portion_tiers[1 if mode == "tier" else 0].id,
        selected_rule_ids=(recipe.variant_rules[0].id,) if mode == "rule" else (),
        deltas={
            i.id: (10 if mode == "delta" and n == 0 else 0)
            for n, i in enumerate(recipe.ingredients)
        },
        provenance=old.provenance,
        household_id=g.household_id,
        plan_id=g.plan_id,
        proposal_id=old.proposal_id,
        batch_node_id=old.batch_node_id,
    )
    data = g.model_dump()
    data["culinary_bindings"] = (binding,)
    data["batches"][0].update(
        tier_id=binding.tier_id,
        planned_servings=binding.planned_servings,
        culinary_signature=binding.semantic_fingerprint(),
    )
    updated = c.FeatureExposureSourceSnapshotDraft.model_validate(
        remap(s, graph=p.BoundPlanIntentGraph.model_validate(data))
    )
    a, b = preview(s), preview(updated)
    if dimension == "METHOD":
        assert a.diagnostics[0].discovery == b.diagnostics[0].discovery
        assert a.events[0].event_key() == b.events[0].event_key()
    else:
        assert not b.events
        assert b.diagnostics[0].discovery.reason == "NO_MATCHING_SCOPE"
    assert a.fingerprint() != b.fingerprint()


def test_same_recipe_different_versions_not_a_representative_group_join():
    from app.modules.recipes import contracts as r
    from feature_fixtures import review_command, scope

    s = source(dimension="METHOD", meals=1, members=1)
    recipe = s.classification_sources[0].subject.evaluation.recipe
    rid = uuid4()

    def owner_ids(value):
        if isinstance(value, dict):
            return {k: rid if k == "recipe_version_id" else owner_ids(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [owner_ids(v) for v in value]
        return value

    rd = owner_ids(recipe.model_dump()) | dict(id=rid, version=2)
    second = r.RecipeVersionSnapshot.model_validate(rd)
    from app.modules.planning.culinary import author_binding

    g = s.member_sources[0].sources[0].proposal.graph
    batch = g.batches[1]
    bound = author_binding(
        recipe=second,
        tier_id=second.portion_tiers[0].id,
        selected_rule_ids=(),
        deltas={i.id: 0 for i in second.ingredients},
        provenance=second.provenance,
        household_id=g.household_id,
        plan_id=g.plan_id,
        proposal_id=s.request.proposal_id,
        batch_node_id=batch.node_id,
    )
    gd = g.model_dump()
    gd["batches"][1].update(recipe_version_id=rid, culinary_signature=bound.semantic_fingerprint())
    gd["culinary_bindings"] = (gd["culinary_bindings"][0], bound)
    g = p.BoundPlanIntentGraph.model_validate(gd)
    # Update proposal references before aggregate validation; preserve two exact source versions.
    data = remap(s, graph=g, revalidate=False)
    for m in data["member_sources"]:
        m["recipes"] += (
            c.RecipeExposureIdentity(
                recipe_version_id=rid,
                recipe_id=second.recipe.id,
                version=2,
                review_status="REVIEWED",
                provenance=second.provenance,
            ).model_dump(),
        )
    for d in data["classification_sources"]:
        d["subject"]["evaluation"]["sources"]["recipe_frontier"] = 2
        if d["subject"]["request"]["batch_node_id"] == batch.node_id:
            d["subject"]["evaluation"]["recipe"] = second
            terms = s.classification_sources[0].subject.evaluation.sources.terms
            sc = scope(
                review_command(
                    second,
                    terms,
                    positive_term_ids=(s.classification_sources[0].dimensions[0].positive_term_ids),
                )
            )
            command = sc.reviews[0].command.model_copy(update={"expected_recipe_frontier": 1})
            review = sc.reviews[0].model_copy(
                update={
                    "source_sequence": 2,
                    "command": command,
                    "command_hash": command.fingerprint(sc.reviews[0].reviewer_user_id),
                }
            )
            d["subject"]["evaluation"]["sources"]["scopes"] = (
                sc.model_copy(update={"reviews": (review,)}),
            )
        d.update(
            discover(
                p.CapturedCulinaryFeatureSubjectDraft.model_validate(d["subject"])
            ).model_dump()
        )
    data["frontiers"][0]["recipe_frontier"] = 2
    result = preview(c.FeatureExposureSourceSnapshotDraft.model_validate(data))
    assert len(result.events) == 1
    assert {w.recipe_version_id for w in result.events[0].support} == {recipe.id, second.id}
    assert len({w.recipe_event_key for w in result.events[0].support}) == 1


@pytest.mark.parametrize("mutation", ["frontier", "scope", "term", "recipe"])
def test_individually_valid_children_still_cannot_disagree_about_source_cut(mutation):
    s = source()
    data = s.model_dump()
    child = data["classification_sources"][0]
    e = child["subject"]["evaluation"]
    if mutation == "frontier":
        e["sources"]["recipe_frontier"] += 1
    elif mutation == "scope":
        e["sources"]["scopes"] = ()
        e["sources"]["terms"] = ()
    elif mutation == "term":
        e["sources"]["terms"][0]["label"] = "Conflicting immutable term"
    else:
        e["recipe"]["procedure"] = "Changed immutable procedure"
    # Each child is internally valid. Shared cross-batch identity is the rejecting boundary.
    child.update(
        discover(
            p.CapturedCulinaryFeatureSubjectDraft.model_validate(child["subject"])
        ).model_dump()
    )
    with pytest.raises(ValueError, match="Conflicting"):
        c.FeatureExposureSourceSnapshotDraft.model_validate(data)


def test_member_nonparticipation_produces_no_event_and_retires_no_physical_fact():
    s = source()
    g = s.member_sources[0].sources[0].proposal.graph
    data = g.model_dump()
    selected = s.request.selected_member_ids[0]
    for m in data["meals"]:
        m["participants"] = tuple(x for x in m["participants"] if x["member_id"] != selected)
    updated = c.FeatureExposureSourceSnapshotDraft.model_validate(
        remap(s, graph=p.BoundPlanIntentGraph.model_validate(data))
    )
    assert {f.member_id for f in preview(updated).events} == set(s.request.selected_member_ids) - {
        selected
    }


@pytest.mark.parametrize("value", [-1, True, "1", 1.0, 2**63])
def test_frontiers_are_strict_canonical_source_generations(value):
    with pytest.raises(ValueError):
        c.RecipeExposureFrontier(dimension="METHOD", recipe_frontier=value)


def test_source_observed_time_policy_and_term_version_remain_in_cut_identity():
    s = source()
    policy = s.request.recipe_eligibility_policy.model_dump()
    policy["provenance"]["observed_at"] -= timedelta(seconds=1)
    data = s.model_dump()
    data["request"]["recipe_eligibility_policy"] = policy
    for m in data["member_sources"]:
        m["policy"] = policy
    updated = c.FeatureExposureSourceSnapshotDraft.model_validate(data)
    assert preview(s).evidence_cuts != preview(updated).evidence_cuts
    assert {f.event_key() for f in preview(s).events} == {
        f.event_key() for f in preview(updated).events
    }


def test_positive_and_unresolved_paths_in_same_meal_remain_separate_diagnostics():
    from app.modules.planning.culinary import author_binding

    s = source()
    g = s.member_sources[0].sources[0].proposal.graph
    recipe = s.classification_sources[0].subject.evaluation.recipe
    old = g.culinary_bindings[1]
    binding = author_binding(
        recipe=recipe,
        tier_id=recipe.portion_tiers[0].id,
        selected_rule_ids=(recipe.variant_rules[0].id,),
        deltas={i.id: 0 for i in recipe.ingredients},
        provenance=old.provenance,
        household_id=g.household_id,
        plan_id=g.plan_id,
        proposal_id=old.proposal_id,
        batch_node_id=old.batch_node_id,
    )
    data = g.model_dump() | dict(culinary_bindings=(g.culinary_bindings[0], binding))
    data["batches"][1]["culinary_signature"] = binding.semantic_fingerprint()
    result = preview(
        c.FeatureExposureSourceSnapshotDraft.model_validate(
            remap(s, graph=p.BoundPlanIntentGraph.model_validate(data))
        )
    )
    assert len(result.events) == 4 and all(len(e.support) == 1 for e in result.events)
    assert {d.discovery.state for d in result.diagnostics} == {"ASSIGNED", "UNRESOLVED"}
    assert len(result.diagnostics) == 8


def test_member_and_recipe_source_provenance_remains_primitive_not_a_safety_summary():
    s = source()
    data = s.model_dump()
    child = data["classification_sources"][0]
    child["subject"]["evaluation"]["recipe"]["review_status"] = "DRAFT"
    with pytest.raises(ValueError):
        c.FeatureExposureSourceSnapshotDraft.model_validate(data)
    assert "evidence_strength" not in c.FeatureExposurePreviewFact.model_fields


def test_all_frozen_algorithms_contract_definitions_and_migrations_are_retained():
    import ast
    import json
    from hashlib import sha256
    from pathlib import Path

    receipt = json.loads(
        Path(__file__).with_name("feature_exposure_compatibility.json").read_text(encoding="utf-8")
    )

    def digest(text):
        return sha256(text.encode("utf-8")).hexdigest()

    for path, definitions in receipt["definitions"].items():
        current = {
            n.name: digest(ast.dump(n, include_attributes=False))
            for n in ast.parse(Path(path).read_text(encoding="utf-8")).body
            if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert all(current.get(k) == v for k, v in definitions.items()), path
    schema = json.loads(Path("packages/contracts/domain.schema.json").read_text(encoding="utf-8"))
    assert len(receipt["schema_definitions"]) == 226
    for name, expected in receipt["schema_definitions"].items():
        assert (
            digest(
                json.dumps(
                    schema["$defs"][name], sort_keys=True, separators=(",", ":"), ensure_ascii=False
                )
            )
            == expected
        ), name
    for path, expected in receipt["released_migrations"].items():
        assert digest(Path(path).read_text(encoding="utf-8")) == expected, path
