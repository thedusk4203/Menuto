"""041F adversarial acceptance through public pure APIs; policy numbers are synthetic only."""

import ast
import builtins
import json
import socket
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest
from app.modules.learning import contracts as c
from app.modules.learning.public import (
    assess_feature_cooldown as assess,
)
from app.modules.learning.public import (
    interpret_feature_repeat_penalty as interpret,
)
from app.modules.learning.public import (
    preview_feature_exposure as preview_source,
)
from app.modules.learning.public import (
    trace_feature_decay as decay,
)
from app.modules.planning import contracts as p
from app.modules.planning.culinary import author_binding
from app.modules.planning.feature_preview import discover_culinary_feature_assignments as discover
from feature_exposure_fixtures import remap, source
from feature_repeat_fixtures import HOUR, policies, query_for, repeat_preview, stages

from tools.check_import_boundaries import check_source


def rebuild(preview, edit):
    data = preview.snapshot.model_dump()
    edit(data)
    for child in data["classification_sources"]:
        child.update(
            discover(
                p.CapturedCulinaryFeatureSubjectDraft.model_validate(child["subject"])
            ).model_dump()
        )
    return preview_source(c.FeatureExposureSourceSnapshotDraft.model_validate(data))


def assessment(preview, query=None, **kwargs):
    query = query or query_for(preview)
    policy, _, _ = policies(query, **kwargs)
    return assess(c.FeatureCooldownInput(preview=preview, query=query, policy=policy))


def changed_path(preview, *, meal_index=0, mode="rule"):
    snapshot = preview.snapshot
    graph = snapshot.member_sources[0].sources[0].proposal.graph
    meal = graph.meals[meal_index]
    bid = next(a.batch_node_id for a in graph.allocations if a.meal_node_id == meal.node_id)
    old = next(b for b in graph.culinary_bindings if b.batch_node_id == bid)
    recipe = next(
        s.subject.evaluation.recipe
        for s in snapshot.classification_sources
        if s.subject.request.batch_node_id == bid
    )
    bound = author_binding(
        recipe=recipe,
        tier_id=recipe.portion_tiers[1 if mode == "tier" else 0].id,
        selected_rule_ids=(recipe.variant_rules[0].id,) if mode == "rule" else (),
        deltas={
            i.id: 10 if mode == "delta" and n == 0 else 0 for n, i in enumerate(recipe.ingredients)
        },
        provenance=old.provenance,
        household_id=graph.household_id,
        plan_id=graph.plan_id,
        proposal_id=old.proposal_id,
        batch_node_id=bid,
    )
    data = graph.model_dump()
    data["culinary_bindings"] = tuple(
        bound if b.batch_node_id == bid else b for b in graph.culinary_bindings
    )
    for batch in data["batches"]:
        if batch["node_id"] == bid:
            batch.update(
                tier_id=bound.tier_id,
                planned_servings=bound.planned_servings,
                culinary_signature=bound.semantic_fingerprint(),
            )
    return preview_source(
        c.FeatureExposureSourceSnapshotDraft.model_validate(
            remap(snapshot, graph=p.BoundPlanIntentGraph.model_validate(data))
        )
    )


@pytest.mark.parametrize(
    "dimension,unit", [("METHOD", (3, 7)), ("MAIN_PROTEIN", (5, 11)), ("FLAVOR", (7, 13))]
)
def test_case01_explicit_distinct_dimension_policy(dimension, unit):
    a, trace, result = stages(repeat_preview(dimension=dimension), unit=unit)
    amount = result.proposal_local_feature_repeat_penalty.amount
    assert (amount.numerator, amount.denominator) == (unit[0], 2 * unit[1])
    assert len(a.witnesses) == len(trace.entries) == 1
    assert a.subject.query.dimension == dimension
    assert result.global_repeat_penalty == "UNAVAILABLE"


@pytest.mark.parametrize("stage", ["cooldown", "decay", "penalty"])
@pytest.mark.parametrize("mutation", ["missing", "dimension", "term", "recipe_policy", "list"])
def test_case02_no_missing_mismatched_or_recipe_policy(stage, mutation):
    a, t, final = stages(repeat_preview())
    subject = {"cooldown": a.subject, "decay": t.subject, "penalty": final.subject}[stage]
    data = subject.model_dump()
    if mutation == "missing":
        data.pop("policy")
    elif mutation in {"dimension", "term"}:
        data["policy"]["dimension" if mutation == "dimension" else "feature_term_id"] = (
            "METHOD" if mutation == "dimension" else uuid4()
        )
    elif mutation == "recipe_policy":
        data["policy"]["fingerprint_kind"] = "RECIPE_ID"
    else:
        data["policy"] = (data["policy"],)
    with pytest.raises(ValueError):
        type(subject).model_validate(data)


@pytest.mark.parametrize("dimension", ["METHOD", "MAIN_PROTEIN", "FLAVOR"])
def test_case03_multiple_versions_supports_one_meal_occurrence(dimension):
    a, t, final = stages(
        repeat_preview(dimension=dimension, rows=(("positive", "positive"), ("positive",)))
    )
    assert len(a.occurrences) == len(a.witnesses) == len(t.entries) == 1
    assert len(a.witnesses[0].fact.support) == 2
    assert len({s.recipe_version_id for s in a.witnesses[0].fact.support}) == 2
    assert len(final.contributions) == 1


def test_case04_separate_meals_sum_exact_occurrences():
    a, _, result = stages(repeat_preview(rows=(("positive",),) * 3))
    assert len(a.witnesses) == 2
    assert result.proposal_local_feature_repeat_penalty.amount == c.FeatureRepeatPenaltyAmount(
        numerator=7, denominator=3
    )


def test_case05_equal_and_future_times_are_not_prior():
    s = source(meals=4, members=1, batches=1)
    graph = s.member_sources[0].sources[0].proposal.graph
    time = graph.meals[1].scheduled_at
    gd = graph.model_dump()
    for m, offset in zip(gd["meals"], (-1, 0, 0, 1), strict=True):
        m["scheduled_at"] = time + timedelta(hours=offset)
    preview = preview_source(
        c.FeatureExposureSourceSnapshotDraft.model_validate(
            remap(s, graph=p.BoundPlanIntentGraph.model_validate(gd))
        )
    )
    target = next(e for e in preview.events if e.meal_node_id == graph.meals[1].node_id)
    a = assessment(preview, query_for(preview, target=target))
    assert len(a.witnesses) == 1 and a.witnesses[0].distance_microseconds == HOUR


def test_case06_start_and_integer_microsecond_boundaries():
    base = repeat_preview()
    time = query_for(base)
    target = next(e for e in base.events if e.meal_node_id == time.meal_node_id).scheduled_at
    preview = repeat_preview(
        rows=(("positive",),) * 4,
        times=(
            target - timedelta(microseconds=HOUR + 1),
            target - timedelta(microseconds=HOUR),
            target - timedelta(microseconds=1),
            target,
        ),
    )
    a = assessment(preview, duration=HOUR)
    assert sorted(w.distance_microseconds for w in a.witnesses) == [1, HOUR]


@pytest.mark.parametrize("mutation", ["window_start", "horizon_start", "target_end"])
def test_case07_containment_not_truncation(mutation):
    preview = repeat_preview()
    q = query_for(preview)
    t = next(e.scheduled_at for e in preview.events if e.meal_node_id == q.meal_node_id)
    if mutation == "window_start":

        def edit(data):
            policy = data["request"]["recipe_eligibility_policy"]
            policy["window"]["start"] = t - timedelta(minutes=90)
            for m in data["member_sources"]:
                m["policy"] = policy

        preview = rebuild(preview, edit)
    elif mutation == "horizon_start":
        graph = preview.snapshot.member_sources[0].sources[0].proposal.graph
        delta = t - graph.horizon.start
        duration = (delta.days * 86400 + delta.seconds) * 1_000000 + delta.microseconds + 1

        def edit(data):
            policy = data["request"]["recipe_eligibility_policy"]
            policy["window"]["start"] = graph.horizon.start - timedelta(days=1)
            for m in data["member_sources"]:
                m["policy"] = policy

        preview = rebuild(preview, edit)
        with pytest.raises(ValueError, match="LOOKBACK_NOT_CAPTURED"):
            assessment(preview, duration=duration)
        return
    else:

        def edit(data):
            policy = data["request"]["recipe_eligibility_policy"]
            policy["window"]["end"] = t
            graph = preview.snapshot.member_sources[0].sources[0].proposal.graph
            excluded = {
                a.batch_node_id for a in graph.allocations if a.meal_node_id == q.meal_node_id
            }
            data["classification_sources"] = tuple(
                s
                for s in data["classification_sources"]
                if s["subject"]["request"]["batch_node_id"] not in excluded
            )
            for m in data["member_sources"]:
                m["policy"] = policy

        preview = rebuild(preview, edit)
    with pytest.raises(ValueError, match="LOOKBACK_NOT_CAPTURED|TARGET_OUTSIDE_CAPTURE"):
        assessment(preview, q)


@pytest.mark.parametrize("duration", [10**100, 315537897600_000000, True, 1.0, 0, -1])
def test_case08_duration_underflow_overflow_and_strictness(duration):
    with pytest.raises(ValueError):
        assessment(repeat_preview(), duration=duration)


@pytest.mark.parametrize(
    "field",
    ["household_id", "member_id", "plan_id", "proposal_id", "proposal_hash", "meal_node_id"],
)
def test_case09_foreign_query_rejects(field):
    preview = repeat_preview()
    query = query_for(preview).model_copy(
        update={field: "0" * 64 if field == "proposal_hash" else uuid4()}
    )
    with pytest.raises(ValueError):
        assessment(preview, query)


@pytest.mark.parametrize("state", ["absent", "no_source", "retracted"])
def test_case10_nonpositive_target_is_never_successful_zero(state):
    preview = repeat_preview(rows=(("positive",), (state,)))
    q = query_for(preview)
    graph = preview.snapshot.member_sources[0].sources[0].proposal.graph
    q = q.model_copy(update={"meal_node_id": graph.meals[-1].node_id})
    with pytest.raises(ValueError, match="TARGET_NOT_PRESENT|TARGET_FEATURE_UNRESOLVED"):
        assessment(preview, q)


@pytest.mark.parametrize("field,value", [("feature_term_id", uuid4()), ("dimension", "METHOD")])
def test_case10_random_term_or_wrong_dimension(field, value):
    preview = repeat_preview()
    with pytest.raises(ValueError):
        assessment(preview, query_for(preview).model_copy(update={field: value}))


def test_case11_complete_finite_reviewed_absence_is_scoped_unavailable():
    a, t, result = stages(repeat_preview(rows=(("absent",), ("positive",))))
    assert a.occurrences[0].state == "REVIEWED_ABSENT"
    assert a.occurrences[0].cells[0].resolution.reason is None
    assert not t.entries and a.outcome == "NO_MATCH_IN_SELECTED_PROPOSAL"
    assert result.proposal_local_feature_repeat_penalty.reason == "NO_MATCH_IN_SELECTED_PROPOSAL"
    assert "amount" not in result.proposal_local_feature_repeat_penalty.model_dump()


@pytest.mark.parametrize(
    "state,reason",
    [("outside", "OUTSIDE_REVIEWED_UNIVERSE"), ("not_captured", "TERM_NOT_CAPTURED")],
)
def test_case12_reviewed_none_does_not_prove_outside_universe_absence(state, reason):
    a, _, result = stages(repeat_preview(rows=((state,), ("positive",))))
    assert a.occurrences[0].cells[0].diagnostic.discovery.state == "REVIEWED_NONE"
    assert a.occurrences[0].cells[0].resolution.reason == reason
    assert result.proposal_local_feature_repeat_penalty.reason == "UNRESOLVED_TERM_OCCURRENCES"


def test_case13_partial_positive_is_proof_only_for_its_term():
    a, _, result = stages(repeat_preview(rows=(("partial",), ("positive",))))
    assert len(a.witnesses) == 1 and a.occurrences[0].state == "PRESENT"
    assert result.proposal_local_feature_repeat_penalty.status == "AVAILABLE"
    a, _, result = stages(repeat_preview(rows=(("partial_absent",), ("positive",))))
    assert a.occurrences[0].cells[0].resolution.reason == "PARTIAL_COVERAGE"
    assert result.proposal_local_feature_repeat_penalty.status == "UNAVAILABLE"


def test_case14_known_witness_does_not_hide_separate_unknown_meal():
    a, trace, result = stages(repeat_preview(rows=(("positive",), ("no_source",), ("positive",))))
    assert a.outcome == "MATCH_IN_SELECTED_PROPOSAL"
    assert a.occurrence_resolution == "HAS_UNRESOLVED_MEALS"
    assert len(a.witnesses) == len(trace.entries) == len(result.contributions) == 1
    assert result.proposal_local_feature_repeat_penalty.reason == "UNRESOLVED_TERM_OCCURRENCES"
    assert not hasattr(result.proposal_local_feature_repeat_penalty, "amount")
    assert not {"subtotal", "lower_bound", "total"} & set(type(result).model_fields)


def test_case15_positive_plus_unknown_sibling_is_one_decidable_occurrence():
    a, _, result = stages(repeat_preview(rows=(("positive", "no_source"), ("positive",))))
    assert a.occurrence_resolution == "ALL_QUERIED_TERM_OCCURRENCES_DECIDABLE"
    assert len(a.witnesses) == 1 and len(a.occurrences[0].cells) == 2
    assert {x.resolution.state for x in a.occurrences[0].cells} == {"PRESENT", "UNRESOLVED"}
    assert result.proposal_local_feature_repeat_penalty.status == "AVAILABLE"


def test_case16_all_absent_cells_do_not_become_never_exposed():
    a, _, result = stages(repeat_preview(rows=(("absent", "absent"), ("positive",))))
    assert a.occurrences[0].state == "REVIEWED_ABSENT" and not a.unresolved_meal_ids
    assert a.absence_semantics == "NO_GLOBAL_REPEAT_NOVELTY_OR_NEVER_EXPOSED_CONCLUSION"
    assert result.proposal_local_feature_repeat_penalty.status == "UNAVAILABLE"


def test_case17_no_prior_meals_distinct_from_resolved_absence_and_zero():
    a, t, result = stages(repeat_preview(rows=(("positive",),)))
    assert not a.occurrences and not a.witnesses and not t.entries
    assert a.occurrence_resolution == "NO_ELIGIBLE_PRIOR_MEALS"
    assert result.proposal_local_feature_repeat_penalty.reason == "NO_MATCH_IN_SELECTED_PROPOSAL"


@pytest.mark.parametrize(
    "mutation",
    [
        "remove_cell",
        "duplicate_cell",
        "extra_cell",
        "remove_source",
        "remove_support",
        "forge_discovery",
    ],
)
def test_case18_full_source_manifest_cannot_hide_cells(mutation):
    a, _, _ = stages(repeat_preview(rows=(("no_source",), ("positive",))))
    data = a.subject.model_dump()
    pre = data["preview"]
    if mutation == "remove_cell":
        pre["diagnostics"] = pre["diagnostics"][1:]
    elif mutation == "duplicate_cell":
        pre["diagnostics"] += pre["diagnostics"][:1]
    elif mutation == "extra_cell":
        pre["diagnostics"] += (pre["diagnostics"][0] | dict(meal_node_id=uuid4()),)
    elif mutation == "remove_source":
        pre["snapshot"]["classification_sources"] = pre["snapshot"]["classification_sources"][1:]
    elif mutation == "remove_support":
        pre["events"][0]["support"] = ()
    else:
        # Diagnostics sort by UUID, so index 0 may already be the positive target cell.
        # Always forge the unresolved cell; changing ASSIGNED to itself is a valid no-op.
        unresolved = next(d for d in pre["diagnostics"] if d["discovery"]["state"] == "UNRESOLVED")
        unresolved["discovery"]["state"] = "ASSIGNED"
    with pytest.warns(UserWarning, match="Pydantic serializer"), pytest.raises(ValueError):
        assess(c.FeatureCooldownInput.model_construct(**data))


@pytest.mark.parametrize(
    "state,reason", [("retracted", "RETRACTED"), ("no_source", "TERM_NOT_CAPTURED")]
)
def test_case19_owner_reasons_retained(state, reason):
    a, _, result = stages(repeat_preview(rows=((state,), ("positive",))))
    assert a.occurrences[0].cells[0].resolution.reason == reason
    if state == "no_source":
        assert a.occurrences[0].cells[0].diagnostic.discovery.reason == "NO_SOURCE"
    assert result.proposal_local_feature_repeat_penalty.status == "UNAVAILABLE"


def test_case20_same_code_new_id_is_not_the_query_term():
    preview = repeat_preview(rows=(("absent",), ("positive",)))
    query = query_for(preview)

    def edit(data):
        for child in data["classification_sources"]:
            for t in child["subject"]["evaluation"]["sources"]["terms"]:
                t["code"] = "identical-code"

    preview = rebuild(preview, edit)
    assert assessment(preview, query).outcome == "NO_MATCH_IN_SELECTED_PROPOSAL"


@pytest.mark.parametrize("dimension", ["METHOD", "FLAVOR", "MAIN_PROTEIN"])
@pytest.mark.parametrize("mode", ["tier", "rule", "delta"])
def test_case21_method_invariant_and_exact_path_dimensions(dimension, mode):
    preview = repeat_preview(dimension=dimension)
    updated = changed_path(preview, mode=mode)
    a, _, result = stages(updated)
    if dimension == "METHOD":
        assert a.occurrences[0].state == "PRESENT" and len(a.witnesses) == 1
    else:
        assert a.occurrences[0].cells[0].resolution.reason == "NO_MATCHING_SCOPE"
        assert result.proposal_local_feature_repeat_penalty.reason == "UNRESOLVED_TERM_OCCURRENCES"


def test_case22_main_protein_multiple_slots_do_not_multiply_occurrence():
    a, t, result = stages(repeat_preview(dimension="MAIN_PROTEIN", main_slots=2))
    assert len(a.witnesses) == len(t.entries) == len(result.contributions) == 1
    prior = a.occurrences[0].cells[0].diagnostic.classification_source.batch_node_id
    child = next(
        s
        for s in a.subject.preview.snapshot.classification_sources
        if s.subject.request.batch_node_id == prior
    )
    assert len(child.subject.evaluation.sources.scopes[0].reviews[0].command.supports) == 2


def bands(duration=2 * HOUR):
    return [
        dict(
            ordinal=0,
            lower_age_microseconds=0,
            upper_age_microseconds=HOUR,
            retention_multiplier=dict(numerator=1, denominator=2),
        ),
        dict(
            ordinal=1,
            lower_age_microseconds=HOUR,
            upper_age_microseconds=duration,
            retention_multiplier=dict(numerator=0, denominator=1),
        ),
    ]


@pytest.mark.parametrize(
    "mutation", ["empty", "gap", "overlap", "reverse", "ordinal", "increase", "short", "long"]
)
def test_case23_invalid_authored_decay_bands(mutation):
    b = bands()
    if mutation == "empty":
        b = []
    elif mutation == "gap":
        b[1]["lower_age_microseconds"] += 1
    elif mutation == "overlap":
        b[1]["lower_age_microseconds"] -= 1
    elif mutation == "reverse":
        b.reverse()
    elif mutation == "ordinal":
        b[1]["ordinal"] = 3
    elif mutation == "increase":
        b[1]["retention_multiplier"]["numerator"] = 1
    elif mutation == "short":
        b[1]["upper_age_microseconds"] -= 1
    else:
        b[1]["upper_age_microseconds"] += 1
    with pytest.raises(ValueError):
        stages(repeat_preview(), bands=b)


def test_case24_exact_band_age_boundaries_keep_zero_entries():
    target = max(e.scheduled_at for e in repeat_preview().events)
    pre = repeat_preview(
        rows=(("positive",),) * 4,
        times=(
            target - timedelta(microseconds=2 * HOUR),
            target - timedelta(microseconds=HOUR + 1),
            target - timedelta(microseconds=HOUR),
            target,
        ),
    )
    a, t, result = stages(pre, bands=bands())
    assert {e.age_microseconds: e.band.ordinal for e in t.entries} == {
        2 * HOUR: 1,
        HOUR + 1: 1,
        HOUR: 0,
    }
    assert len(result.contributions) == 3 and len(a.witnesses) == 3
    assert result.proposal_local_feature_repeat_penalty.amount.numerator == 7


@pytest.mark.parametrize("model", [c.FeatureRetentionMultiplier, c.FeatureRepeatPenaltyAmount])
@pytest.mark.parametrize("value", [True, False, 0.5, float("nan"), float("inf"), "1", -1])
@pytest.mark.parametrize("field", ["numerator", "denominator"])
def test_case25_rational_strict_integer_validation(model, value, field):
    with pytest.raises(ValueError):
        model(**(dict(numerator=1, denominator=2) | {field: value}))


@pytest.mark.parametrize("model", [c.FeatureRetentionMultiplier, c.FeatureRepeatPenaltyAmount])
def test_case25_zero_denominator_equivalent_and_zero_canonical(model):
    with pytest.raises(ValueError):
        model(numerator=1, denominator=0)
    assert (
        model(numerator=6, denominator=8).model_dump_json()
        == model(numerator=3, denominator=4).model_dump_json()
    )
    assert model(numerator=0, denominator=99).denominator == 1
    if model is c.FeatureRetentionMultiplier:
        with pytest.raises(ValueError):
            model(numerator=3, denominator=2)


def test_case26_nonempty_explicit_zero_available():
    b = [
        dict(
            ordinal=0,
            lower_age_microseconds=0,
            upper_age_microseconds=2 * HOUR,
            retention_multiplier=dict(numerator=0, denominator=19),
        )
    ]
    _, trace, result = stages(repeat_preview(), bands=b)
    assert trace.entries and result.contributions
    assert result.proposal_local_feature_repeat_penalty.amount == c.FeatureRepeatPenaltyAmount(
        numerator=0, denominator=1
    )


@pytest.mark.parametrize(
    "rows,reason",
    [
        ((("positive",),), "NO_MATCH_IN_SELECTED_PROPOSAL"),
        ((("no_source",), ("positive",)), "UNRESOLVED_TERM_OCCURRENCES"),
    ],
)
def test_cases27_28_unknown_zero_band_never_zero_penalty(rows, reason):
    b = [
        dict(
            ordinal=0,
            lower_age_microseconds=0,
            upper_age_microseconds=2 * HOUR,
            retention_multiplier=dict(numerator=0, denominator=1),
        )
    ]
    _, t, result = stages(repeat_preview(rows=rows), bands=b)
    assert not t.entries and result.proposal_local_feature_repeat_penalty.reason == reason
    assert not hasattr(result.proposal_local_feature_repeat_penalty, "amount")


def test_case29_large_exact_products_sum_without_cap():
    large = 10**150 + 3
    _, _, result = stages(repeat_preview(rows=(("positive",),) * 3), unit=(large, 7))
    assert result.proposal_local_feature_repeat_penalty.amount == c.FeatureRepeatPenaltyAmount(
        numerator=large, denominator=7
    )


@pytest.mark.parametrize(
    "mutation",
    ["zero", "mean", "max", "cap", "normalize", "unit", "recipe_weight", "missing_operator"],
)
def test_case30_no_default_zero_or_alternate_operator(mutation):
    query = query_for(repeat_preview())
    policy = policies(query)[2].model_dump()
    if mutation == "zero":
        policy["unit_penalty"]["numerator"] = 0
    elif mutation == "unit":
        policy["unit_penalty"]["unit"] = "PROBABILITY"
    elif mutation == "recipe_weight":
        policy["recipe_weight"] = 1
    elif mutation == "missing_operator":
        policy.pop("operator")
    else:
        policy["operator"] = mutation.upper()
    with pytest.raises(ValueError):
        c.FeatureRepeatPenaltyPolicy.model_validate(policy)


@pytest.mark.parametrize("stage", ["cooldown", "decay", "penalty"])
@pytest.mark.parametrize("older", ["member", "classification"])
def test_case31_minimum_consumed_child_not_completion(stage, older):
    preview = repeat_preview()
    cutoff = min(m.captured_at for m in preview.snapshot.member_sources)

    def edit(data):
        if older == "member":
            data["member_sources"][0]["captured_at"] -= timedelta(seconds=2)
        else:
            data["classification_sources"][0]["subject"]["evaluation"]["captured_at"] -= timedelta(
                seconds=2
            )

    preview = rebuild(preview, edit)
    a, t, result = stages(preview, observed=cutoff - timedelta(seconds=2))
    assert a.policy_cutoff == cutoff - timedelta(seconds=2)
    subject = {"cooldown": a.subject, "decay": t.subject, "penalty": result.subject}[stage]
    data = subject.model_dump()
    data["policy"]["provenance"]["observed_at"] = cutoff - timedelta(seconds=1)
    with pytest.raises(ValueError, match="AS_OF_CAPTURE"):
        type(subject).model_validate(data)


def test_case31_unconsumed_later_meal_child_clock_is_excluded():
    pre = repeat_preview(rows=(("positive",),) * 3)
    graph = pre.snapshot.member_sources[0].sources[0].proposal.graph
    target = next(e for e in pre.events if e.meal_node_id == graph.meals[1].node_id)
    future_batch = next(
        a.batch_node_id for a in graph.allocations if a.meal_node_id == graph.meals[2].node_id
    )
    cutoff = min(m.captured_at for m in pre.snapshot.member_sources)

    def edit(data):
        for child in data["classification_sources"]:
            if child["subject"]["request"]["batch_node_id"] == future_batch:
                child["subject"]["evaluation"]["captured_at"] -= timedelta(minutes=1)

    pre = rebuild(pre, edit)
    assert assessment(pre, query_for(pre, target=target), observed=cutoff).policy_cutoff == cutoff


def test_case31_other_member_clock_is_not_consumed():
    pre = preview_source(source(members=2, meals=2, batches=1))
    query = query_for(pre)
    cutoff = assessment(pre, query).policy_cutoff

    def edit(data):
        for member in data["member_sources"]:
            if member["member_id"] != query.member_id:
                member["captured_at"] -= timedelta(seconds=5)

    pre = rebuild(pre, edit)
    assert assessment(pre, query, observed=cutoff).policy_cutoff == cutoff


def test_case32_utc_offsets_preserve_exact_scheduled_age():
    pre = repeat_preview()
    a, _, result = stages(pre)
    encoded = json.loads(pre.canonical_json())

    def offset(value):
        if isinstance(value, dict):
            return {k: offset(v) for k, v in value.items()}
        if isinstance(value, list):
            return [offset(v) for v in value]
        if isinstance(value, str) and value.endswith("Z") and "T" in value:
            return (
                datetime.fromisoformat(value).astimezone(timezone(timedelta(hours=7))).isoformat()
            )
        return value

    alt = c.FeatureExposurePreviewDraft.model_validate(offset(encoded))
    b, _, again = stages(
        alt, query=a.subject.query, observed=a.subject.policy.provenance.observed_at
    )
    assert a.witnesses == b.witnesses and alt.fingerprint() == pre.fingerprint()
    assert (
        again.proposal_local_feature_repeat_penalty == result.proposal_local_feature_repeat_penalty
    )


@pytest.mark.parametrize(
    "field,value",
    [("policy_version", "test.2"), ("policy_id", "other"), ("duration_microseconds", HOUR)],
)
def test_case33_policy_changes_identity_not_source(field, value):
    pre = repeat_preview()
    a = assessment(pre)
    data = a.subject.model_dump()
    data["policy"][field] = value
    b = assess(c.FeatureCooldownInput.model_validate(data))
    assert a.fingerprint() != b.fingerprint()
    assert a.source_preview_fingerprint == b.source_preview_fingerprint


def test_case34_unordered_shuffle_canonicalizes_but_does_not_sort_bands():
    _, _, final = stages(
        repeat_preview(rows=(("positive", "positive"), ("no_source",), ("positive",)))
    )
    data = final.model_dump()
    trace = data["subject"]["trace"]
    trace["entries"] = trace["entries"][::-1]
    cd = trace["subject"]["assessment"]
    for field in ("occurrences", "witnesses", "unresolved_meal_ids"):
        cd[field] = cd[field][::-1]
    for o in cd["occurrences"]:
        o["cells"] = o["cells"][::-1]
    pre = cd["subject"]["preview"]
    for field in ("events", "diagnostics", "evidence_cuts"):
        pre[field] = pre[field][::-1]
    snapshot = pre["snapshot"]
    snapshot["classification_sources"] = snapshot["classification_sources"][::-1]
    for m in snapshot["member_sources"]:
        for field in ("meals", "allocations", "batches", "culinary_bindings"):
            g = m["sources"][0]["proposal"]["graph"]
            g[field] = g[field][::-1]
    data["contributions"] = data["contributions"][::-1]
    again = c.FeatureRepeatPenaltyDraft.model_validate(data)
    assert again.canonical_json() == final.canonical_json()
    assert again.fingerprint() == final.fingerprint()


@pytest.mark.parametrize(
    "mutation",
    [
        "target",
        "cells",
        "occurrence",
        "unknowns",
        "witness",
        "age",
        "band",
        "retention",
        "contribution",
        "total",
        "source_hash",
        "cut_hash",
    ],
)
@pytest.mark.parametrize("ingress", ["wire", "copy", "construct"])
def test_case35_forged_and_rehashed_results_reject(mutation, ingress):
    _, _, final = stages(repeat_preview())
    data = final.model_dump()
    trace = data["subject"]["trace"]
    cd = trace["subject"]["assessment"]
    if mutation == "target":
        cd["target"]["feature_term_id"] = uuid4()
    elif mutation == "cells":
        cd["occurrences"][0]["cells"] = ()
    elif mutation == "occurrence":
        cd["occurrences"][0]["state"] = "REVIEWED_ABSENT"
    elif mutation == "unknowns":
        cd["unresolved_meal_ids"] = (uuid4(),)
    elif mutation == "witness":
        cd["witnesses"] = ()
    elif mutation == "age":
        trace["entries"][0]["age_microseconds"] += 1
    elif mutation == "band":
        trace["entries"][0]["band"]["ordinal"] += 1
    elif mutation == "retention":
        trace["entries"][0]["band"]["retention_multiplier"]["numerator"] = 0
    elif mutation == "contribution":
        data["contributions"][0]["contribution"]["numerator"] += 1
    elif mutation == "total":
        data["proposal_local_feature_repeat_penalty"]["amount"]["numerator"] += 1
    elif mutation == "source_hash":
        data["source_preview_fingerprint"] = "0" * 64
    else:
        data["dimension_evidence_cut_digest"] = "0" * 64
    if ingress != "wire":
        forged = (
            final.model_copy(update=data)
            if ingress == "copy"
            else c.FeatureRepeatPenaltyDraft.model_construct(**data)
        )
        # A caller may rehash an arbitrary fake payload. Validation independently rederives it.
        assert len(forged.fingerprint()) == 64
        with pytest.raises(ValueError):
            c.FeatureRepeatPenaltyDraft.model_validate(forged)
        return
    with pytest.raises(ValueError):
        c.FeatureRepeatPenaltyDraft.model_validate(data)


def test_case35_next_stage_rejects_constructed_assessment_and_trace():
    a, t, result = stages(repeat_preview())
    fake = a.model_copy(update={"witnesses": ()})
    with pytest.raises(ValueError):
        decay(t.subject.model_copy(update={"assessment": fake}))
    fake = t.model_copy(update={"entries": ()})
    with pytest.raises(ValueError):
        interpret(result.subject.model_copy(update={"trace": fake}))


def test_case36_replay_retries_do_not_add_occurrences_or_accept_source_unions():
    a, _, result = stages(repeat_preview())
    again = interpret(result.subject)
    assert again.canonical_json() == result.canonical_json() and len(again.contributions) == 1
    with pytest.raises(ValueError):
        c.FeatureCooldownInput.model_validate(
            a.subject.model_dump() | dict(previews=(a.subject.preview,) * 2)
        )


@pytest.mark.parametrize(
    "field",
    [
        "accepted_schedule",
        "confirmed_exposure",
        "durable_history",
        "consumption_history",
        "cross_horizon_history",
        "global_repeat_penalty",
        "novelty",
        "taste_fit",
        "planner_ready",
        "activation_ready",
        "member_behavior_profile",
        "cross_dimension_aggregation",
    ],
)
def test_cases40_43_44_fixed_unavailable_authority_and_no_aggregation(field):
    _, _, result = stages(repeat_preview())
    with pytest.raises(ValueError):
        c.FeatureRepeatPenaltyDraft.model_validate(result.model_dump() | {field: True})


@pytest.mark.parametrize(
    "field",
    [
        "events",
        "coverage",
        "witnesses",
        "cached_count",
        "penalty",
        "accepted_plan",
        "consumed",
        "variant_family",
        "prior",
        "shrinkage",
        "candidate_total",
        "recipe_weight",
    ],
)
def test_cases40_43_closed_input_rejects_unauthorized_sources_and_totals(field):
    a = assessment(repeat_preview())
    with pytest.raises(ValueError):
        c.FeatureCooldownInput.model_validate(a.subject.model_dump() | {field: 0})


def test_case41_pure_apis_zero_file_network_io(monkeypatch):
    _, _, result = stages(repeat_preview())

    def forbidden(*args, **kwargs):
        raise AssertionError("IO in pure interpretation")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    assert interpret(result.subject).fingerprint() == result.fingerprint()


@pytest.mark.parametrize(
    "target",
    [
        "sqlalchemy",
        "psycopg",
        "ortools",
        "requests",
        "socket",
        "pathlib",
        "app.modules.planning.public",
        "app.modules.preferences.public",
        "app.modules.execution.public",
    ],
)
def test_case41_static_pure_import_boundary(target):
    assert check_source(f"import {target}", "app.modules.learning.feature_repeat")


def test_case42_all_frozen_definitions_and_migrations_unchanged():
    receipt = json.loads(Path(__file__).with_name("feature_repeat_compatibility.json").read_text())

    def digest(s):
        return sha256(s.encode()).hexdigest()

    for path, definitions in receipt["definitions"].items():
        current = {
            n.name: digest(ast.dump(n, include_attributes=False))
            for n in ast.parse(Path(path).read_text(encoding="utf-8")).body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        assert all(current.get(k) == v for k, v in definitions.items()), path
    schema = json.loads(Path("packages/contracts/domain.schema.json").read_text())["$defs"]
    assert len(receipt["schema_definitions"]) == 256
    for k, v in receipt["schema_definitions"].items():
        assert (
            digest(json.dumps(schema[k], sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            == v
        ), k
    for path, v in receipt["released_migrations"].items():
        assert digest(Path(path).read_text(encoding="utf-8")) == v, path
    assert len(receipt["released_migrations"]) == 13


def test_case44_hash_is_replay_identity_and_fixed_non_authority():
    a, t, result = stages(repeat_preview())
    assert a.source_preview_fingerprint == a.subject.preview.fingerprint()
    assert (
        c.FeatureRepeatPenaltyDraft.model_validate_json(result.canonical_json()).fingerprint()
        == result.fingerprint()
    )
    for obj in (a, t, result):
        assert obj.planner_ready is False and obj.activation_ready is False
        assert obj.member_behavior_profile == "NOT_MODIFIED"
    assert a.subject.preview.feature_cooldown == "UNAVAILABLE"
    assert a.subject.preview.feature_decay == "UNAVAILABLE"
    assert a.subject.preview.repeat_penalty == "UNAVAILABLE"
