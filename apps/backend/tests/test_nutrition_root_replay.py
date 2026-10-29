"""NRC33–56: retained-source interpretation, exact measurements and missingness."""

import copy
import json
from pathlib import Path

import pytest
from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as c
from app.modules.nutrition.root_limits import COMMAND_BYTES, check_structure
from app.modules.nutrition.root_public import resolve_nutrition_root, validate_nutrition_root
from nutrition_root_fixtures import amount, evidence, rebuild_test_journals, rehash_sources


@pytest.fixture
def retained():
    return json.loads(
        (Path(__file__).parent / "fixtures/nutrition_root_retained_TEST_ONLY.json").read_text()
    )


def records(source, kind):
    return [r for r in source["sources"] if r["command"]["body"]["kind"] == kind]


def remove_kind(source, kind):
    source["sources"] = [r for r in source["sources"] if r["command"]["body"]["kind"] != kind]
    return rebuild_test_journals(source)


def test_nrc33_exact_guideline_provider_version_pin(retained):
    original = resolve_nutrition_root(retained)
    assert original.availability == "AVAILABLE"
    retained["request"]["guideline_body_fingerprint"] = "f" * 64
    wrong = resolve_nutrition_root(rehash_sources(retained))
    assert wrong.availability == "UNAVAILABLE" and "VERSION_MISMATCH" in wrong.reasons


def test_nrc34_labels_hashes_and_reviewer_identity_cannot_replace_authority(retained):
    retained["authority"] = []
    with pytest.raises(ValueError, match="history|frontier"):
        resolve_nutrition_root(rehash_sources(retained))


def test_nrc35_duplicate_immutable_id_conflicting_body_rejected(retained):
    duplicate = copy.deepcopy(retained["sources"][0])
    duplicate["command"]["idempotency_key"] = "TEST_ONLY_conflicting_body"
    retained["sources"].append(duplicate)
    with pytest.raises(ValueError, match="Duplicate immutable"):
        resolve_nutrition_root(rehash_sources(retained))


def test_nrc36_absent_publication_differs_from_wrong_applicability(retained):
    absent = remove_kind(copy.deepcopy(retained), "ASSESSMENT")
    # No assessment is a valid absence; changing scope does not select a fallback.
    absent["request"]["scope_id"] = "TEST_ONLY_other_scope"
    result = resolve_nutrition_root(rehash_sources(absent))
    assert "GUIDELINE_NOT_APPLICABLE" in result.reasons and not result.roots
    missing = copy.deepcopy(retained)
    missing["request"]["guideline_revision_id"] = "00000000-0000-0000-0000-000000000099"
    result = resolve_nutrition_root(rehash_sources(missing))
    assert "GUIDELINE_UNAVAILABLE" in result.reasons
    unpublished = remove_kind(copy.deepcopy(retained), "ASSESSMENT")
    unpublished = remove_kind(unpublished, "PUBLICATION")
    result = resolve_nutrition_root(unpublished)
    assert "GUIDELINE_UNAVAILABLE" in result.reasons
    assert "SOURCE_OUT_OF_EFFECTIVE_RANGE" not in result.reasons


def test_nrc37_absent_assessment_never_becomes_supported(retained):
    result = resolve_nutrition_root(remove_kind(retained, "ASSESSMENT"))
    assert result.eligibility == "UNKNOWN" and result.availability == "UNAVAILABLE"
    assert "ELIGIBILITY_UNKNOWN" in result.reasons


@pytest.mark.parametrize(
    "outcome,state",
    [("OUT_OF_SCOPE", "UNSUPPORTED"), ("EXCLUDED", "INELIGIBLE"), ("UNDETERMINED", "UNKNOWN")],
)
def test_nrc38_positive_negative_and_unknown_assertions_distinct(retained, outcome, state):
    records(retained, "ASSESSMENT")[0]["command"]["body"]["outcome"] = outcome
    result = resolve_nutrition_root(rebuild_test_journals(retained))
    assert result.eligibility == state and not result.roots


def test_nrc39_mass_height_and_goal_do_not_infer_healthy_population(retained):
    assert len(records(retained, "OBSERVATION")) == 2 and records(retained, "GOAL")
    result = resolve_nutrition_root(remove_kind(retained, "ASSESSMENT"))
    assert result.eligibility == "UNKNOWN"
    with pytest.raises(ValueError):
        c.NutritionRootRequest(**dict(retained["request"], healthy_adult=True))


def test_nrc40_assessed_observation_value_and_version_are_exact(retained):
    assessment = records(retained, "ASSESSMENT")[0]["command"]["body"]
    assessment["observations"][0]["value"] = {"numerator": 999, "denominator": 1}
    with pytest.raises(ValueError, match="observation identity|value|anchor"):
        resolve_nutrition_root(rebuild_test_journals(retained))


def test_nrc41_jurisdiction_and_edition_require_explicit_source_meaning(retained):
    body = records(retained, "DRAFT")[0]["command"]["body"]["guideline"]
    body["jurisdiction_status"] = "REVIEWED_SPECIFIED"
    with pytest.raises(ValueError, match="jurisdiction"):
        c.NutritionGuidelineBody.model_validate(body)
    body["jurisdiction_status"] = "SOURCE_NOT_SPECIFIED"
    body["edition"] = ""
    with pytest.raises(ValueError):
        c.NutritionGuidelineBody.model_validate(body)


def test_nrc42_metric_unit_mismatch_before_comparison(retained):
    descriptor = records(retained, "DRAFT")[0]["command"]["body"]["guideline"]["clauses"][0][
        "descriptor"
    ]
    with pytest.raises(ValueError, match="metric/unit"):
        c.NutritionRootDescriptor(**dict(descriptor, unit="G"))


@pytest.mark.parametrize("field,value", [("metric", "TEST_ONLY_UNKNOWN_NUTRIENT"), ("unit", "KJ")])
def test_nrc43_finite_supported_measurements_only(retained, field, value):
    descriptor = records(retained, "DRAFT")[0]["command"]["body"]["guideline"]["clauses"][0][
        "descriptor"
    ]
    with pytest.raises(ValueError):
        c.NutritionRootDescriptor(**dict(descriptor, **{field: value}))
    with pytest.raises(ValueError):
        c.NutritionRootRequest(
            **dict(retained["request"], contract_version="nutrition-root-request.v9")
        )


@pytest.mark.parametrize(
    "bad",
    [
        {"numerator": 1.0, "denominator": 1},
        {"numerator": True, "denominator": 1},
        {"numerator": 2, "denominator": 4},
        {"numerator": 0, "denominator": 2},
        {"numerator": 1, "denominator": 0},
    ],
)
def test_nrc44_strict_canonical_rationals_and_range_shape(bad):
    with pytest.raises(ValueError):
        c.NutritionRootAmount(**bad)
    assert amount(0) == c.NutritionRootAmount(numerator=0, denominator=1)
    with pytest.raises(ValueError):
        c.NutritionRange(kind="RANGE", lower=amount(13), upper=amount(7))


def test_nrc45_target_center_does_not_author_hard_interval(retained):
    body = records(retained, "DRAFT")[0]["command"]["body"]["guideline"]
    clause = body["clauses"][0]
    target = dict(clause, constraint=dict(kind="TARGET", center=canonical(amount(0))))
    with pytest.raises(ValueError, match="TARGET"):
        c.NutritionGuidelineClause(**target)
    target["interpretation"] = "REFERENCE_CENTER"
    assert c.NutritionGuidelineClause(**target).constraint.kind == "TARGET"
    body["clauses"] = [target]
    body["mandatory_hard_roots"] = []
    with pytest.raises(ValueError):
        c.NutritionGuidelineBody(**body)


def test_nrc46_whole_interval_required_without_source_stitching(retained):
    retained["request"]["temporal"]["interval"]["end"] = "2026-09-03T00:00:00.000000Z"
    result = resolve_nutrition_root(rehash_sources(retained))
    assert not result.roots and "SOURCE_OUT_OF_EFFECTIVE_RANGE" in result.reasons


def test_nrc47_daily_weekly_periods_never_implicitly_scale(retained):
    retained["request"]["temporal"]["kind"] = "WEEK"
    result = resolve_nutrition_root(rehash_sources(retained))
    assert not result.roots and "TEMPORAL_SCOPE_MISMATCH" in result.reasons


def test_nrc48_absent_goal_is_not_maintain(retained):
    result = resolve_nutrition_root(remove_kind(retained, "GOAL"))
    assert result.goal_state == "ABSENT" and result.goal_direction is None and not result.roots


def test_nrc49_retracted_goal_does_not_resurrect_old_declarations(retained):
    goal = records(retained, "GOAL")[0]
    tombstone = copy.deepcopy(goal)
    from uuid import uuid4

    tombstone["id"] = tombstone["command"]["revision_id"] = str(uuid4())
    tombstone["sequence"] = 2
    tombstone["recorded_order"] = (
        max(r["recorded_order"] for r in [*retained["authority"], *retained["sources"]]) + 1
    )
    tombstone["command"].update(
        expected_revision=1, predecessor_id=goal["id"], idempotency_key="TEST_ONLY_retract"
    )
    tombstone["command"]["body"].update(operation="RETRACT", direction=None, replaces=[goal["id"]])
    retained["sources"].append(tombstone)
    result = resolve_nutrition_root(rebuild_test_journals(retained))
    assert (
        result.goal_state == "RETRACTED"
        and result.goal_direction is None
        and "GOAL_RETRACTED" in result.reasons
    )


def test_nrc50_recorded_frontier_order_is_not_authored_valid_time(retained):
    root = resolve_nutrition_root(retained)
    assert root.sources.capture.started_at > root.sources.request.temporal.interval.end
    observation = next(r for r in root.sources.sources if r.command.body.kind == "OBSERVATION")
    assert observation.command.body.observed_at < observation.recorded_at
    forged = copy.deepcopy(retained)
    records(forged, "ASSESSMENT")[0]["recorded_order"] = records(forged, "OBSERVATION")[0][
        "recorded_order"
    ]
    with pytest.raises(ValueError, match="order"):
        resolve_nutrition_root(rebuild_test_journals(forged))


def test_nrc51_reordered_sets_replay_deterministically(retained):
    before = resolve_nutrition_root(retained)
    for key in ("principals", "sources", "streams", "authority", "provider_enrollments"):
        retained[key].reverse()
    assert resolve_nutrition_root(retained) == before


def test_nrc52_entire_capture_frame_affects_identity(retained):
    root = resolve_nutrition_root(retained)
    retained["capture"]["endpoint"] = "TEST_ONLY_another_retained_endpoint"
    changed = resolve_nutrition_root(rehash_sources(retained))
    assert changed.roots == root.roots and changed.source_fingerprint != root.source_fingerprint
    assert changed.result_fingerprint != root.result_fingerprint


def test_nrc53_cached_constructed_copied_results_recomputed(retained):
    root = resolve_nutrition_root(retained)
    forged = canonical(root)
    forged["goal_direction"] = "GAIN"
    forged["result_fingerprint"] = c.nutrition_root_hash(
        "nutrition.root-result.v1", {k: v for k, v in forged.items() if k != "result_fingerprint"}
    )
    with pytest.raises(ValueError, match="recomputation"):
        validate_nutrition_root(c.NutritionRootContract.model_construct(**forged))


def test_nrc54_retained_replay_does_not_claim_current_authorization(retained):
    root = resolve_nutrition_root(retained)
    assert root.current_authorization == "NOT_CLAIMED"
    assert root.source_origin == "RETAINED_SELF_CONSISTENCY_NOT_OFFLINE_DATABASE_PROOF"
    assert validate_nutrition_root(root) == root


def test_nrc55_absence_requires_a_complete_authorized_frontier(retained):
    missing = remove_kind(retained, "GOAL")
    missing["capture"]["absence_stream_keys"] = []
    with pytest.raises(ValueError, match="absence"):
        resolve_nutrition_root(rehash_sources(missing))


def test_nrc56_absolute_structural_budgets_before_recursive_parsing():
    with pytest.raises(ValueError, match="byte"):
        check_structure({"body": "TEST_ONLY_" * COMMAND_BYTES}, byte_limit=COMMAND_BYTES)
    with pytest.raises(ValueError, match="integer"):
        check_structure({"value": 1 << 128})
    deep = {}
    for _ in range(40):
        deep = {"nested": deep}
    with pytest.raises(ValueError, match="structural"):
        check_structure(deep)
    assert evidence("TEST_ONLY no production source").environment == "TEST_ONLY"
