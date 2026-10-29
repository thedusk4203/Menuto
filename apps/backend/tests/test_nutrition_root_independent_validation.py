"""NRC57–69: independent reconstruction and exact scoped containment."""

import json
from pathlib import Path

import pytest
from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as c
from app.modules.nutrition.root_public import resolve_nutrition_root
from app.modules.validation import nutrition_roots as independent
from nutrition_root_fixtures import alternate_test_constraint, amount, evidence


@pytest.fixture
def source():
    return json.loads(
        (Path(__file__).parent / "fixtures/nutrition_root_retained_TEST_ONLY.json").read_text()
    )


@pytest.fixture
def root(source):
    return resolve_nutrition_root(source)


def check(root, claims=(), *, coverage="ROOT_SOURCE_CONSISTENCY_ONLY"):
    return independent.validate_nutrition_root_independently(
        dict(root=root, coverage=coverage, derived_claims=claims)
    )


def claim(root, *, constraint=None, kind="COMFORT", goal=None, baseline=None):
    return c.NutritionDerivedContainmentClaim(
        root=root.roots[0],
        constraint=constraint or root.roots[0].clause.constraint,
        claim_kind=kind,
        policy_evidence=evidence("TEST_ONLY later-policy containment carrier; no policy authority"),
        goal_revision_id=goal,
        baseline_evidence=baseline,
    )


def test_nrc57_source_reconstruction_never_calls_producer(root, monkeypatch):
    from app.modules.nutrition import root_resolution

    def forbidden(*args, **kwargs):
        pytest.fail("Independent checker called producer business logic")

    monkeypatch.setattr(root_resolution, "resolve_nutrition_root", forbidden)
    monkeypatch.setattr(root_resolution, "validate_nutrition_root", forbidden)
    result = check(root)
    assert result.decision == "CONSISTENT" and not result.containment_checked
    assert result.policy_business_correctness == "NOT_EVALUATED" and not result.planner_ready


def test_nrc58_forged_eligibility_goal_authorship_rejected(root):
    forged = canonical(root)
    forged["goal_direction"] = "GAIN"
    forged["result_fingerprint"] = c.nutrition_root_hash(
        "nutrition.root-result.v1", {k: v for k, v in forged.items() if k != "result_fingerprint"}
    )
    assert check(forged).decision == "INCONSISTENT"


def test_nrc59_effective_cut_and_source_frontier_checked(root):
    forged = canonical(root)
    forged["sources"]["streams"][0]["revision"] += 1
    assert check(forged).decision == "INCONSISTENT"


@pytest.mark.parametrize(
    "lower,upper,decision",
    [
        (7, 13, "CONSISTENT"),
        (8, 12, "CONSISTENT"),
        (6, 13, "INCONSISTENT"),
        (7, 14, "INCONSISTENT"),
    ],
)
def test_nrc60_exact_range_containment_and_boundaries(root, lower, upper, decision):
    value = claim(root, constraint=dict(kind="RANGE", lower=amount(lower), upper=amount(upper)))
    report = check(root, (value,), coverage="ROOT_AND_DERIVED_CONTAINMENT")
    assert report.decision == decision and report.containment_checked


@pytest.mark.parametrize(
    "kind,bound,derived,decision",
    [
        ("MINIMUM", 7, 7, "CONSISTENT"),
        ("MINIMUM", 7, 6, "INCONSISTENT"),
        ("MAXIMUM", 13, 13, "CONSISTENT"),
        ("MAXIMUM", 13, 14, "INCONSISTENT"),
    ],
)
def test_nrc61_one_sided_bounds_without_invented_opposites(source, kind, bound, derived, decision):
    key = "lower" if kind == "MINIMUM" else "upper"
    root = resolve_nutrition_root(
        alternate_test_constraint(source, dict(kind=kind, **{key: amount(bound)}))
    )
    report = check(
        root,
        (claim(root, constraint=dict(kind=kind, **{key: amount(derived)})),),
        coverage="ROOT_AND_DERIVED_CONTAINMENT",
    )
    assert report.decision == decision
    assert not hasattr(root.roots[0].clause.constraint, "upper" if key == "lower" else "lower")


@pytest.mark.parametrize(
    "center,decision",
    [(7, "CONSISTENT"), (10, "CONSISTENT"), (13, "CONSISTENT"), (14, "INCONSISTENT")],
)
def test_nrc61_target_is_only_a_center_inside_explicit_protected_range(root, center, decision):
    report = check(
        root,
        (claim(root, constraint=dict(kind="TARGET", center=amount(center))),),
        coverage="ROOT_AND_DERIVED_CONTAINMENT",
    )
    assert report.decision == decision


def test_nrc62_goal_intent_is_not_numeric_protection_authority(root):
    value = claim(root, kind="GOAL_PROTECTION", goal=root.goal_revision_id)
    result = check(root, (value,), coverage="ROOT_AND_DERIVED_CONTAINMENT")
    assert result.decision != "CONSISTENT"
    assert "GOAL_PROTECTION_BASELINE_PROVENANCE_UNAVAILABLE" in result.findings
    weak = claim(
        root,
        kind="GOAL_PROTECTION",
        goal=root.goal_revision_id,
        baseline=evidence("TEST_ONLY baseline carrier; not production numeric policy"),
        constraint=dict(kind="RANGE", lower=amount(6), upper=amount(13)),
    )
    assert (
        "HARD_ROOT_CONTAINMENT_FAILED"
        in check(root, (weak,), coverage="ROOT_AND_DERIVED_CONTAINMENT").findings
    )


@pytest.mark.parametrize("axis", ["CostPreference", "Budget"])
def test_nrc63_cost_budget_cannot_weaken_roots(root, axis):
    weak = claim(root, constraint=dict(kind="RANGE", lower=amount(6), upper=amount(13)))
    assert check(root, (weak,), coverage="ROOT_AND_DERIVED_CONTAINMENT").decision == "INCONSISTENT"
    with pytest.raises(ValueError):
        c.NutritionRootRequest(**dict(canonical(root.sources.request), **{axis: "TEST_ONLY"}))


@pytest.mark.parametrize("axis", ["KitchenEffort", "convenience"])
def test_nrc64_effort_convenience_cannot_weaken_roots(root, axis):
    weak = claim(root, constraint=dict(kind="RANGE", lower=amount(7), upper=amount(14)))
    assert check(root, (weak,), coverage="ROOT_AND_DERIVED_CONTAINMENT").decision == "INCONSISTENT"
    with pytest.raises(ValueError):
        c.NutritionRootRequest(**dict(canonical(root.sources.request), **{axis: "TEST_ONLY"}))


def test_nrc65_tastefit_cannot_create_or_replace_nutrition_truth(root):
    with pytest.raises(ValueError):
        c.NutritionRootRequest(**dict(canonical(root.sources.request), taste_fit="TEST_ONLY_score"))
    assert (
        check(
            root,
            (claim(root, constraint=dict(kind="MINIMUM", lower=amount(0))),),
            coverage="ROOT_AND_DERIVED_CONTAINMENT",
        ).decision
        == "INCONSISTENT"
    )


def test_nrc66_nutrition_precision_does_not_mint_root_truth(root):
    with pytest.raises(ValueError):
        c.NutritionRootRequest(
            **dict(canonical(root.sources.request), nutrition_precision="FLEXIBLE")
        )
    assert (
        check(
            root,
            (claim(root, constraint=dict(kind="RANGE", lower=amount(0), upper=amount(99))),),
            coverage="ROOT_AND_DERIVED_CONTAINMENT",
        ).decision
        == "INCONSISTENT"
    )


def test_nrc67_temporal_identity_checked_before_any_containment_arithmetic(root, monkeypatch):
    value = canonical(claim(root))
    value["root"]["clause"]["descriptor"]["temporal"]["kind"] = "WEEK"

    def forbidden(*args, **kwargs):
        pytest.fail("Descriptor mismatch reached arithmetic")

    monkeypatch.setattr(independent, "Fraction", forbidden)
    report = check(root, (value,), coverage="ROOT_AND_DERIVED_CONTAINMENT")
    assert "CONTAINMENT_DESCRIPTOR_MISMATCH" in report.findings


def test_nrc68_required_derived_claims_not_vacuously_accepted(root):
    result = check(root, coverage="ROOT_AND_DERIVED_CONTAINMENT")
    assert result.decision == "UNSUPPORTED" and not result.containment_checked
    value = canonical(claim(root))
    value["root"]["guideline_body_fingerprint"] = "f" * 64
    assert check(root, (value,), coverage="ROOT_AND_DERIVED_CONTAINMENT").decision == "INCONSISTENT"


def test_nrc69_rehashed_wrong_claim_rejected_and_source_only_scope_honest(root):
    forged = canonical(root)
    forged["roots"][0]["clause"]["constraint"]["lower"] = {"numerator": 6, "denominator": 1}
    forged["result_fingerprint"] = c.nutrition_root_hash(
        "nutrition.root-result.v1", {k: v for k, v in forged.items() if k != "result_fingerprint"}
    )
    assert check(forged).decision == "INCONSISTENT"
    source_only = check(root)
    assert source_only.decision == "CONSISTENT" and not source_only.containment_checked
    assert source_only.scientific_correctness == "NOT_CERTIFIED"
    assert source_only.canonical_database_origin == "NOT_PROVED_OFFLINE"
