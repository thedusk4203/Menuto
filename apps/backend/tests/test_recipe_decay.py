"""Policy interpretation is neither behavioral evidence nor aggregated utility."""

from datetime import timedelta

import pytest
from app.modules.learning import contracts as c
from app.modules.learning.public import trace_recipe_decay
from decay_fixtures import band, decay_input
from pydantic import ValidationError
from test_architecture import check_source


def test_exact_band_selection_preserves_each_source_even_at_zero_retention():
    s = decay_input()
    original = s.assessment.canonical_json()
    result = trace_recipe_decay(s)
    by_age = {e.witness.distance_microseconds: e for e in result.entries}
    assert set(by_age) == {1, 2, 3, 4}
    assert [by_age[age].band.ordinal for age in (1, 2, 3, 4)] == [0, 0, 1, 1]
    assert by_age[3].band.retention_multiplier.numerator == 0
    assert {e.witness.fact.event_key() for e in result.entries} == {
        w.fact.event_key() for w in s.assessment.witnesses
    }
    assert s.assessment.canonical_json() == original
    assert s.assessment.decay == "UNAVAILABLE"  # Frozen041B result is never rewritten.
    assert not result.activation_ready and result.interpretation_mode == "AS_OF_CAPTURE"


@pytest.mark.parametrize(
    "numerator,denominator,expected",
    [
        (2, 4, (1, 2)),
        (0, 999, (0, 1)),
        (999, 999, (1, 1)),
        (2**160, 2**161, (1, 2)),
        (1, 3, (1, 3)),
    ],
)
def test_exact_reduced_canonical_rational(numerator, denominator, expected):
    r = c.RetentionMultiplier(numerator=numerator, denominator=denominator)
    assert (r.numerator, r.denominator) == expected


@pytest.mark.parametrize(
    "numerator,denominator",
    [
        (-1, 2),
        (1, 0),
        (0, 0),
        (1, -2),
        (3, 2),
        (True, 2),
        (1, False),
        (0.5, 1),
        (1, 2.0),
        ("1", 2),
        (1, "2"),
        (float("nan"), 1),
        (1, float("inf")),
    ],
)
def test_invalid_or_inexact_rational_rejected(numerator, denominator):
    with pytest.raises(ValidationError):
        c.RetentionMultiplier(numerator=numerator, denominator=denominator)


def test_equivalent_rationals_have_identical_policy_input_result_bytes_and_hashes():
    s = decay_input()
    equivalent = s.policy.model_dump()
    equivalent["bands"][0]["retention_multiplier"] = dict(numerator=2, denominator=4)
    equivalent["bands"][1]["retention_multiplier"] = dict(numerator=0, denominator=9)
    p = c.RecipeDecayPolicy.model_validate(equivalent)
    other = c.RecipeDecayInput(assessment=s.assessment, policy=p)
    assert p.fingerprint() == s.policy.fingerprint()
    assert other.canonical_json() == s.canonical_json()
    a, b = trace_recipe_decay(s), trace_recipe_decay(other)
    assert a.canonical_json() == b.canonical_json() and a.fingerprint() == b.fingerprint()
    assert c.RecipeDecayTraceDraft.model_validate_json(a.canonical_json()).canonical_json() == (
        a.canonical_json()
    )


@pytest.mark.parametrize(
    "bands",
    [
        (),
        (band(0, 1, 4, 1, 2),),  # No coverage from zero.
        (band(0, 0, 1, 1, 2), band(1, 2, 4, 0, 1)),  # Gap.
        (band(0, 0, 3, 1, 2), band(1, 2, 4, 0, 1)),  # Overlap.
        (band(1, 0, 4, 1, 2),),  # Wrong ordinal.
        (band(0, 0, 2, 1, 2), band(0, 2, 4, 0, 1)),  # Duplicate ordinal.
        (band(1, 2, 4, 0, 1), band(0, 0, 2, 1, 2)),  # Order cannot be silently sorted.
        (band(0, 0, 2, 1, 3), band(1, 2, 4, 1, 2)),  # Increasing retention.
        (band(0, 0, 2, 0, 1), band(1, 2, 4, 1, 999)),
        (band(0, -1, 4, 1, 2),),
        (band(0, 0, 0, 1, 2),),
        (band(0, 2, 2, 1, 2),),
        (band(0, 0, 4.0, 1, 2),),
        (band(False, 0, 4, 1, 2),),
    ],
)
def test_invalid_band_policy_rejects_without_gaps_tails_or_sorting(bands):
    p = decay_input().policy.model_dump() | {"bands": bands}
    with pytest.raises(ValidationError):
        c.RecipeDecayPolicy.model_validate(p)


@pytest.mark.parametrize("upper", [3, 5])
def test_last_bound_must_match_frozen_witness_domain_for_this_subset(upper):
    s = decay_input()
    p = c.RecipeDecayPolicy.model_validate(
        s.policy.model_dump() | {"bands": (band(0, 0, upper, 1, 2),)}
    )
    with pytest.raises(ValueError, match="exactly cover"):
        c.RecipeDecayInput(assessment=s.assessment, policy=p)


def test_no_bands_or_policy_defaults():
    s = decay_input()
    for changes in ({"policy": None}, {"policy": {}}, {"witnesses": ()}):
        with pytest.raises(ValidationError):
            c.RecipeDecayInput.model_validate(s.model_dump() | changes)
    with pytest.raises(ValidationError):
        c.RecipeDecayInput.model_validate(s.model_dump(exclude={"policy"}))
    with pytest.raises(ValidationError):
        c.RecipeDecayPolicy.model_validate(s.policy.model_dump(exclude={"bands"}))


def test_empty_trace_is_scoped_absence_not_a_zero_penalty_or_novelty():
    a = trace_recipe_decay(decay_input(()))
    assert a.entries == ()
    assert a.subject.assessment.outcome == "NO_MATCH_IN_SELECTED_PROPOSAL"
    for name in (
        "repeat_penalty",
        "novelty",
        "taste_fit",
        "confirmed_exposure",
        "consumption_history",
        "accepted_schedule",
        "global_history",
    ):
        assert getattr(a, name) == "UNAVAILABLE"
    assert a.absence_semantics == "NO_GLOBAL_PENALTY_OR_NOVELTY_CONCLUSION"


@pytest.mark.parametrize("field", ["witnesses", "outcome", "target", "lookback_start", "subject"])
def test_forged_nested_frozen_assessment_is_fully_revalidated(field):
    s = decay_input()
    data = s.assessment.model_dump()
    if field == "witnesses":
        data[field][0]["distance_microseconds"] += 1
    elif field == "outcome":
        data[field] = "NO_MATCH_IN_SELECTED_PROPOSAL"
    elif field == "target":
        data[field]["member_id"] = "00000000-0000-0000-0000-000000000001"
    elif field == "lookback_start":
        data[field] += timedelta(microseconds=1)
    else:
        data[field]["query"]["recipe_id"] = "00000000-0000-0000-0000-000000000001"
    forged = c.RecipeCooldownAssessmentDraft.model_construct(**data)
    with pytest.warns(UserWarning, match="serializer warnings"), pytest.raises(ValueError):
        c.RecipeDecayInput(assessment=forged, policy=s.policy)


@pytest.mark.parametrize("field", ["band", "age", "witness", "duplicate", "omit", "reorder"])
def test_cached_trace_cannot_override_source_or_policy(field):
    a = trace_recipe_decay(decay_input())
    data = a.model_dump()
    if field == "band":
        data["entries"][0]["band"]["retention_multiplier"] = dict(numerator=1, denominator=7)
    elif field == "age":
        data["entries"][0]["witness"]["distance_microseconds"] += 1
    elif field == "witness":
        data["entries"][0]["witness"]["fact"]["recipe_id"] = "00000000-0000-0000-0000-000000000001"
    elif field == "duplicate":
        data["entries"] += (data["entries"][0],)
    elif field == "omit":
        data["entries"] = ()
    else:
        data["entries"] = tuple(reversed(data["entries"]))
    with pytest.raises(ValueError, match="trace differs"):
        c.RecipeDecayTraceDraft.model_validate(data)


def test_policy_identity_provenance_and_band_changes_affect_result_hash():
    s = decay_input()
    original = trace_recipe_decay(s)
    changes = [
        {"policy_id": "different"},
        {"policy_version": "test.v2"},
        {"provenance": s.policy.provenance.model_copy(update={"source_version": "v2"})},
        {"bands": (band(0, 0, 4, 1, 3),)},
    ]
    for change in changes:
        policy = c.RecipeDecayPolicy.model_validate(s.policy.model_dump() | change)
        updated = trace_recipe_decay(c.RecipeDecayInput(assessment=s.assessment, policy=policy))
        assert updated.fingerprint() != original.fingerprint()
        assert updated.subject.policy.fingerprint() != s.policy.fingerprint()


def test_as_of_capture_time_boundary_is_explicit_not_retrospective():
    s = decay_input()
    capture = s.assessment.subject.snapshot.captured_at
    data = s.policy.model_dump()
    data["provenance"]["observed_at"] = capture
    at_capture = c.RecipeDecayPolicy.model_validate(data)
    trace_recipe_decay(c.RecipeDecayInput(assessment=s.assessment, policy=at_capture))
    data["provenance"]["observed_at"] += timedelta(microseconds=1)
    with pytest.raises(ValueError, match="AS_OF_CAPTURE"):
        c.RecipeDecayInput(assessment=s.assessment, policy=c.RecipeDecayPolicy.model_validate(data))
    with pytest.raises(ValueError):
        c.RecipeDecayPolicy.model_validate(
            s.policy.model_dump() | {"interpretation_mode": "RETROSPECTIVE"}
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("activation_ready", True),
        ("repeat_penalty", 0),
        ("novelty", 1),
        ("taste_fit", 1),
        ("confirmed_exposure", "CONFIRMED"),
        ("score", 0),
        ("sum", 0),
        ("mean", 0),
        ("max", 0),
        ("rank", 1),
        ("portfolio_role", "EXPLORE"),
        ("EvidenceStrength", "HIGH"),
        ("confidence", 1),
        ("probability", 1),
    ],
)
def test_no_aggregation_authority_or_behavioral_claims(field, value):
    a = trace_recipe_decay(decay_input())
    with pytest.raises(ValueError):
        c.RecipeDecayTraceDraft.model_validate(a.model_dump() | {field: value})
    with pytest.raises(ValidationError):
        a.activation_ready = True


@pytest.mark.parametrize(
    "field,value",
    [
        ("fingerprint_kind", "METHOD"),
        ("fingerprint_kind", "RECIPE_VERSION"),
        ("source_kind", "CONFIRMED"),
        ("source_kind", "AUTOPILOT_ASSUMED"),
        ("band_interval", "INTERPOLATED"),
        ("default_retention", 0),
    ],
)
def test_unsupported_policy_semantics_fail_closed(field, value):
    s = decay_input()
    with pytest.raises(ValueError):
        c.RecipeDecayPolicy.model_validate(s.policy.model_dump() | {field: value})


def test_unordered_source_facts_canonicalize_but_policy_band_order_is_not_generic_sorted():
    s = decay_input()
    data = s.assessment.model_dump()
    g = data["subject"]["snapshot"]["sources"][0]["proposal"]["graph"]
    g["meals"] = tuple(reversed(g["meals"]))
    g["allocations"] = tuple(reversed(g["allocations"]))
    other = c.RecipeCooldownAssessmentDraft.model_validate(data)
    assert trace_recipe_decay(
        c.RecipeDecayInput(assessment=other, policy=s.policy)
    ).canonical_json() == (trace_recipe_decay(s).canonical_json())
    with pytest.raises(ValueError):
        c.RecipeDecayPolicy.model_validate(
            s.policy.model_dump() | {"bands": tuple(reversed(s.policy.bands))}
        )


@pytest.mark.parametrize(
    "source",
    [
        "import sqlalchemy",
        "import psycopg",
        "import ortools",
        "import httpx",
        "from app.modules.preferences.public import PreferenceService",
        "from app.modules.execution.public import PlanRevisionService",
        "from app.modules.planning.shortlist import shortlist_candidates",
    ],
)
def test_pure_learning_boundary_still_guards_decay_core(source):
    assert check_source(source, "app.modules.learning.public")


def test_monotonic_comparison_uses_exact_cross_products_beyond_float_precision():
    s = decay_input()
    n = 10**60
    bands = (band(0, 0, 2, n, n + 1), band(1, 2, 4, n - 1, n))
    policy = c.RecipeDecayPolicy.model_validate(s.policy.model_dump() | {"bands": bands})
    trace_recipe_decay(c.RecipeDecayInput(assessment=s.assessment, policy=policy))
    bands = (band(0, 0, 2, n - 1, n), band(1, 2, 4, n, n + 1))
    with pytest.raises(ValueError, match="not increase"):
        c.RecipeDecayPolicy.model_validate(s.policy.model_dump() | {"bands": bands})


def test_single_microsecond_domain_covers_eligible_age_one_excludes_equal_time():
    from app.modules.learning.public import assess_recipe_cooldown
    from cooldown_fixtures import cooldown_input
    from decay_fixtures import policy_for

    b = cooldown_input((-1, 0))
    b = b.model_copy(update={"policy": b.policy.model_copy(update={"duration_microseconds": 1})})
    assessment = assess_recipe_cooldown(b)
    policy = policy_for(assessment, (band(0, 0, 1, 1, 3),))
    a = trace_recipe_decay(c.RecipeDecayInput(assessment=assessment, policy=policy))
    assert len(a.entries) == 1 and a.entries[0].witness.distance_microseconds == 1


def test_untrusted_policy_instance_is_normalized_again_at_ingress():
    s = decay_input()
    first = s.policy.bands[0]
    unreduced = first.retention_multiplier.model_copy(update={"numerator": 2, "denominator": 4})
    policy = s.policy.model_copy(
        update={
            "bands": (
                first.model_copy(update={"retention_multiplier": unreduced}),
                s.policy.bands[1],
            )
        }
    )
    subject = c.RecipeDecayInput(assessment=s.assessment, policy=policy)
    assert subject.policy.fingerprint() == s.policy.fingerprint()
    assert trace_recipe_decay(subject).fingerprint() == trace_recipe_decay(s).fingerprint()
