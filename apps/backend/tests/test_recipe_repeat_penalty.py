"""INV-018/027: exact scoped interpretation, not global history or composed utility."""

import ast
import json
import subprocess
from datetime import timedelta
from decimal import localcontext
from fractions import Fraction
from pathlib import Path

import pytest
from app.modules.learning import contracts as c
from app.modules.learning.public import interpret_recipe_repeat_penalty, trace_recipe_decay
from decay_fixtures import band, decay_input
from pydantic import ValidationError
from repeat_penalty_fixtures import penalty_input
from test_architecture import check_source


def test_exact_contributions_total_above_one_roundtrip_and_frozen_sources():
    subject = penalty_input()
    old = subject.trace.canonical_json()
    result = interpret_recipe_repeat_penalty(subject)
    assert len(result.contributions) == 4
    assert result.proposal_local_repeat_penalty == c.RepeatPenaltyAmount(numerator=3, denominator=1)
    assert sorted(x.contribution.numerator for x in result.contributions) == [0, 0, 3, 3]
    assert {x.source.witness.fact.event_key() for x in result.contributions} == {
        x.witness.fact.event_key() for x in subject.trace.entries
    }
    assert all(x.unit_penalty == subject.policy.unit_penalty for x in result.contributions)
    assert subject.trace.canonical_json() == old and subject.trace.repeat_penalty == "UNAVAILABLE"
    assert c.RecipeRepeatPenaltyDraft.model_validate_json(
        result.canonical_json()
    ).canonical_json() == (result.canonical_json())
    assert interpret_recipe_repeat_penalty(subject).fingerprint() == result.fingerprint()
    assert not result.activation_ready
    assert result.repeat_penalty == result.novelty == result.taste_fit == "UNAVAILABLE"


def test_empty_is_unavailable_while_explicit_zero_retains_witness():
    empty = penalty_input(trace_recipe_decay(decay_input(())))
    zero = penalty_input(trace_recipe_decay(decay_input((-3, -4))))
    a, b = map(interpret_recipe_repeat_penalty, (empty, zero))
    assert a.outcome == "NO_MATCH_IN_SELECTED_PROPOSAL"
    assert not a.contributions and a.proposal_local_repeat_penalty is None
    assert b.outcome == "INTERPRETED_IN_SELECTED_PROPOSAL"
    assert len(b.contributions) == 2
    assert b.proposal_local_repeat_penalty == c.RepeatPenaltyAmount(numerator=0, denominator=1)
    assert all(x.contribution.numerator == 0 for x in b.contributions)


@pytest.mark.parametrize("n,d,expected", [(2, 4, (1, 2)), (0, 999, (0, 1)), (9, 3, (3, 1))])
def test_amount_is_reduced_and_not_probability(n, d, expected):
    amount = c.RepeatPenaltyAmount(numerator=n, denominator=d)
    assert (amount.numerator, amount.denominator) == expected


@pytest.mark.parametrize(
    "n,d",
    [
        (-1, 1),
        (1, 0),
        (1, -1),
        (True, 1),
        (1, False),
        (1.0, 2),
        (1, 2.0),
        ("1", 2),
        (float("inf"), 1),
        (float("nan"), 1),
    ],
)
def test_invalid_amounts_reject(n, d):
    with pytest.raises(ValueError):
        c.RepeatPenaltyAmount(numerator=n, denominator=d)


def test_equivalent_policy_rationals_have_identical_bytes_and_hashes():
    s = penalty_input()
    a = s.policy.model_dump() | {"unit_penalty": {"numerator": 1, "denominator": 2}}
    b = a | {"unit_penalty": {"numerator": 2, "denominator": 4}}
    x, y = [c.RecipeRepeatPenaltyInput(trace=s.trace, policy=p) for p in (a, b)]
    assert x.policy.fingerprint() == y.policy.fingerprint()
    assert x.canonical_json() == y.canonical_json()
    assert (
        interpret_recipe_repeat_penalty(x).canonical_json()
        == interpret_recipe_repeat_penalty(y).canonical_json()
    )


def test_integer_arithmetic_independent_of_decimal_context():
    s = decay_input()
    n = 10**90
    decay = s.policy.model_dump() | {"bands": (band(0, 0, 2, n, n + 1), band(1, 2, 4, 1, 7))}
    trace = trace_recipe_decay(c.RecipeDecayInput(assessment=s.assessment, policy=decay))
    subject = penalty_input(trace)
    p = subject.policy.model_dump() | {"unit_penalty": {"numerator": n + 3, "denominator": n + 5}}
    with localcontext() as context:
        context.prec = 2
        result = interpret_recipe_repeat_penalty(c.RecipeRepeatPenaltyInput(trace=trace, policy=p))
    expected = Fraction(n + 3, n + 5) * (2 * Fraction(n, n + 1) + Fraction(2, 7))
    amount = result.proposal_local_repeat_penalty
    assert (amount.numerator, amount.denominator) == (expected.numerator, expected.denominator)


@pytest.mark.parametrize(
    "field", ["operator", "unit_penalty", "policy_id", "policy_version", "provenance"]
)
def test_required_policy_fields_have_no_defaults(field):
    data = penalty_input().policy.model_dump()
    del data[field]
    with pytest.raises(ValueError):
        c.RecipeRepeatPenaltyPolicy.model_validate(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("operator", "MAX"),
        ("operator", "MEAN"),
        ("cap", 1),
        ("saturation", 1),
        ("fingerprint_kind", "METHOD"),
        ("source_kind", "CONFIRMED"),
        ("interpretation_mode", "RETROSPECTIVE"),
        ("unit_penalty", {"numerator": 0, "denominator": 1}),
        ("unit_penalty", {"numerator": 1, "denominator": 1, "unit": "VND"}),
    ],
)
def test_unsupported_policy_rejects(field, value):
    with pytest.raises(ValueError):
        c.RecipeRepeatPenaltyPolicy.model_validate(
            penalty_input().policy.model_dump() | {field: value}
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("rank", 1),
        ("portfolio_role", "EXPLORE"),
        ("utility", 1),
        ("stage2_weight", 1),
        ("probability", 1),
        ("confidence", 1),
        ("EvidenceStrength", "HIGH"),
        ("activation_ready", True),
        ("novelty", 0),
        ("accepted_schedule", "AVAILABLE"),
        ("confirmed_exposure", "AVAILABLE"),
        ("consumption_history", "AVAILABLE"),
        ("global_history", "AVAILABLE"),
        ("taste_fit", 0),
    ],
)
def test_no_extra_claims(field, value):
    result = interpret_recipe_repeat_penalty(penalty_input())
    with pytest.raises(ValueError):
        c.RecipeRepeatPenaltyDraft.model_validate(result.model_dump() | {field: value})


@pytest.mark.parametrize(
    "mutation",
    [
        "total",
        "unit",
        "contribution",
        "retention",
        "witness",
        "outcome",
        "remove",
        "duplicate",
        "unit_penalty",
    ],
)
def test_result_recomputes_entire_trace_not_cached_fields(mutation):
    data = interpret_recipe_repeat_penalty(penalty_input()).model_dump()
    entries = list(data["contributions"])
    if mutation == "total":
        data["proposal_local_repeat_penalty"]["numerator"] += 1
    elif mutation == "unit":
        data["proposal_local_repeat_penalty"]["unit"] = "GRAMS"
    elif mutation == "contribution":
        entries[0]["contribution"]["numerator"] += 1
    elif mutation == "retention":
        entries[0]["source"]["band"]["retention_multiplier"]["numerator"] = 999
    elif mutation == "witness":
        entries[0]["source"]["witness"]["distance_microseconds"] += 1
    elif mutation == "outcome":
        data["outcome"] = "NO_MATCH_IN_SELECTED_PROPOSAL"
    elif mutation == "remove":
        entries.pop()
    elif mutation == "duplicate":
        entries.append(entries[0])
    else:
        entries[0]["unit_penalty"]["numerator"] += 1
    data["contributions"] = entries
    with pytest.raises(ValueError):
        c.RecipeRepeatPenaltyDraft.model_validate(data)


@pytest.mark.parametrize(
    "mutation", ["witness", "retention", "trace_entries", "target", "policy_time", "policy_amount"]
)
def test_forged_copied_and_constructed_inputs_fail(mutation):
    subject = penalty_input()
    data = subject.model_dump()
    trace = data["trace"]
    if mutation == "witness":
        trace["subject"]["assessment"]["witnesses"][0]["distance_microseconds"] += 1
    elif mutation == "retention":
        trace["entries"][0]["band"]["retention_multiplier"]["numerator"] = 1
        trace["entries"][0]["band"]["retention_multiplier"]["denominator"] = 99
    elif mutation == "trace_entries":
        trace["entries"] = ()
    elif mutation == "target":
        trace["subject"]["assessment"]["target"]["member_id"] = "foreign"
    elif mutation == "policy_time":
        data["policy"]["provenance"]["observed_at"] = (
            subject.trace.subject.assessment.subject.snapshot.captured_at
            + timedelta(microseconds=1)
        )
    else:
        data["policy"]["unit_penalty"]["numerator"] = -1
    forged = c.RecipeRepeatPenaltyInput.model_construct(**data)
    with pytest.warns(UserWarning), pytest.raises(ValueError):
        interpret_recipe_repeat_penalty(forged)
    with pytest.raises(ValueError):
        c.RecipeRepeatPenaltyInput.model_validate(data)


def test_revalidation_of_nested_trace_instance_and_frozen_result():
    s = penalty_input()
    forged = s.trace.model_copy(update={"entries": ()})
    with pytest.raises(ValueError):
        c.RecipeRepeatPenaltyInput(trace=forged, policy=s.policy)
    r = interpret_recipe_repeat_penalty(s)
    with pytest.raises(ValidationError):
        r.outcome = "NO_MATCH_IN_SELECTED_PROPOSAL"


def test_unordered_graph_facts_canonicalize_without_sorting_authored_bands():
    s = penalty_input()
    data = s.trace.subject.assessment.model_dump()
    graph = data["subject"]["snapshot"]["sources"][0]["proposal"]["graph"]
    graph["meals"] = tuple(reversed(graph["meals"]))
    graph["allocations"] = tuple(reversed(graph["allocations"]))
    assessment = c.RecipeCooldownAssessmentDraft.model_validate(data)
    trace = trace_recipe_decay(
        c.RecipeDecayInput(assessment=assessment, policy=s.trace.subject.policy)
    )
    other = c.RecipeRepeatPenaltyInput(trace=trace, policy=s.policy)
    assert other.canonical_json() == s.canonical_json()
    assert interpret_recipe_repeat_penalty(other).fingerprint() == (
        interpret_recipe_repeat_penalty(s).fingerprint()
    )


@pytest.mark.parametrize(
    "field", ["household_id", "member_id", "plan_id", "proposal_id", "meal_id", "recipe_id"]
)
def test_foreign_query_cannot_mint_penalty(field):
    data = penalty_input().model_dump()
    data["trace"]["subject"]["assessment"]["subject"]["query"][field] = "foreign"
    with pytest.raises(ValueError):
        c.RecipeRepeatPenaltyInput.model_validate(data)


def test_policy_at_capture_inclusive_newer_policy_rejects():
    s = penalty_input()
    data = s.policy.model_dump()
    captured = s.trace.subject.assessment.subject.snapshot.captured_at
    data["provenance"]["observed_at"] = captured
    c.RecipeRepeatPenaltyInput(trace=s.trace, policy=data)
    data["provenance"]["observed_at"] = captured + timedelta(microseconds=1)
    with pytest.raises(ValueError, match="observed after capture"):
        c.RecipeRepeatPenaltyInput(trace=s.trace, policy=data)


@pytest.mark.parametrize("field", ["policy_id", "policy_version", "provenance", "unit_penalty"])
def test_policy_semantic_change_changes_identity(field):
    s = penalty_input()
    data = s.policy.model_dump()
    if field == "provenance":
        data[field]["source_version"] = "changed"
    elif field == "unit_penalty":
        data[field]["numerator"] = 5
    else:
        data[field] = "changed"
    other = c.RecipeRepeatPenaltyInput(trace=s.trace, policy=data)
    assert other.policy.fingerprint() != s.policy.fingerprint()
    assert other.fingerprint() != s.fingerprint()
    assert (
        interpret_recipe_repeat_penalty(other).fingerprint()
        != interpret_recipe_repeat_penalty(s).fingerprint()
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
def test_core_boundaries(source):
    assert check_source(source, "app.modules.learning.public")


def test_frozen_definitions_and_schema_unchanged():
    baseline = "59cc0a48b52addc5c7d612fae6b81b0681e90a00"
    # Compatibility is tested from checked-in exports too, without requiring Git in CI.
    schema = json.loads(Path("packages/contracts/domain.schema.json").read_text(encoding="utf-8"))
    assert schema["$id"] == "urn:menuto:domain:foundation:20"
    assert "RepeatPenaltyAmount" in schema["$defs"]
    assert "RecipeDecayTraceDraft" in schema["$defs"]
    if not Path(".git").exists():
        return
    old = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={Path.cwd().as_posix()}",
            "show",
            f"{baseline}:apps/backend/app/modules/learning/contracts.py",
        ],
        capture_output=True,
        text=True,
    )
    if old.returncode:  # Shallow CI checkouts need not contain the baseline object.
        return

    def definitions(source):
        return {
            n.name: ast.dump(n)
            for n in ast.parse(source).body
            if isinstance(n, (ast.ClassDef, ast.FunctionDef))
        }

    before = definitions(old.stdout)
    now = definitions(
        Path("apps/backend/app/modules/learning/contracts.py").read_text(encoding="utf-8")
    )
    assert all(now[k] == v for k, v in before.items())
