"""NRE021–NRE096. Independently expected TEST_ONLY finite values, never clinical content."""

import ast
import hashlib
import json
import os
import re
import runpy
import subprocess
import sys
from collections import Counter
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.modules.nutrition import resolution_contracts as c
from app.modules.nutrition import synthesis_contracts as p
from app.modules.nutrition.resolution_estimator import estimate_nutrition_resolution as estimate
from app.modules.nutrition.resolution_limits import WorkBudget, ingest, structure
from app.modules.nutrition.resolution_public import nutrition_resolution_handoff
from app.modules.nutrition.synthesis import synthesize_nutrition_policy
from app.modules.validation.nutrition_policy import validate_nutrition_policy_independently
from app.modules.validation.nutrition_resolution import (
    check_nutrition_resolution_handoff_independently as handoff_check,
)
from app.modules.validation.nutrition_resolution import (
    check_nutrition_resolution_independently as check,
)
from nutrition_resolution_fixtures import rehash, sources
from nutrition_synthesis_pure_fixtures import derive, reauthor_rule, retained, weekly_sources

ROOT = Path(__file__).resolve().parents[3]
COMPAT = Path(__file__).parent / "fixtures/nutrition_resolution_compatibility.json"


def changed(source, change, **options):
    data = deepcopy(canonical(source))
    change(data)
    return rehash(data, **options)


def forged(result, change):
    data = canonical(result)
    change(data)
    data.pop("result_fingerprint")
    return c.NutritionResolutionEstimateV1(
        **data, result_fingerprint=c.resolution_hash("estimate", data)
    )


def numbers(result, metric="ENERGY"):
    return tuple(
        Fraction(x.numerator, x.denominator)
        for x in next(m for m in result.measurements if m.descriptor.metric == metric).values
    )


def assert_unavailable(value, code=None, state=None):
    result = estimate(value)
    assert result.availability != "AVAILABLE"
    assert not result.configurations and not result.measurements and not result.periods
    if code:
        assert code in result.reasons, result
    if state:
        assert result.availability == state
    assert not result.planner_ready and not result.activation_ready
    return result


def mutate_food(source, mutate):
    return changed(source, mutate, food_manifest=True, counts=True)


def test_nre021_requirement_primitive_replay_and_forged_pin():
    s = sources()
    assert check(s, estimate(s)).decision == "CONSISTENT"
    s = changed(s, lambda d: d["scope"].update(requirement_fingerprint="1" * 64))
    assert_unavailable(s, "REQUIREMENT_IDENTITY")


def test_nre022_descriptor_mismatch_before_arithmetic():
    s = changed(
        sources(),
        lambda d: d["requirements"]["measurements"][0]["descriptor"].update(
            scope_id="TEST_ONLY_foreign_scope"
        ),
    )
    assert_unavailable(s, "REQUIREMENT_IDENTITY")


def test_nre023_missing_goal_or_supported_root_never_available():
    s = sources()
    value = changed(
        s, lambda d: d["synthesis_sources"]["request"]["root"].update(goal_state="ABSENT")
    )
    assert_unavailable(value)
    assert check(value, estimate(s)).decision == "INCONSISTENT"


def test_nre024_exact_declared_universe_and_scoped_identity():
    s = sources()
    r = estimate(s)
    assert len(r.configurations) == 6
    assert {x.serving.tier_id for x in r.configurations} == set(s.scope.recipes[0].tier_ids)
    assert r.scope_fingerprint == c.resolution_hash("scope", s.scope)


def test_nre025_rehashed_favorable_subset_fails_original_scope():
    s = sources()

    def remove(d):
        d["scope"]["slots"][0]["alternatives"].pop()

    assert_unavailable(changed(s, remove), "DECLARED_UNIVERSE_OMISSION")


def test_nre026_duplicate_equal_scope_normalized_conflicting_identity_rejected():
    s = sources()
    data = canonical(s.scope)
    data["recipes"] *= 2
    data["slots"] = data["slots"] + deepcopy(data["slots"])
    assert c.NutritionResolutionScopeV1.model_validate(data) == s.scope
    data["slots"][1]["alternatives"] = []
    with pytest.raises(ValueError, match="Conflicting"):
        c.NutritionResolutionScopeV1.model_validate(data)


def test_nre027_empty_universe_is_not_zero_or_infeasible():
    value = changed(sources(), lambda d: d["scope"].update(slots=[]))
    r = assert_unavailable(value, "EMPTY_UNIVERSE", "UNAVAILABLE")
    assert r.solver_infeasibility == "NOT_PROVEN"


def test_nre028_unsupported_original_scope_cannot_return_surviving_subset():
    def continuous(d):
        item = d["recipes"][0]["ingredients"][0]
        item["scaling"] = dict(kind="LINEAR")
        item["adjustment"] = dict(kind="PORTIONABLE", min_delta="-1", max_delta="1")

    s = mutate_food(
        sources(),
        continuous,
    )
    r = assert_unavailable(s, "CONTINUOUS_ENVELOPE", "UNSUPPORTED")
    assert check(s, r).decision == "CONSISTENT"


def test_nre029_completeness_flags_or_capture_context_json_cannot_mint_authority():
    s = sources()
    with pytest.raises(ValueError):
        c.NutritionResolutionSourcesV1.model_validate(canonical(s) | {"complete_pool": True})
    from app.modules.planning.nutrition_resolution_capture import NutritionResolutionCaptureContext

    with pytest.raises(TypeError):
        NutritionResolutionCaptureContext(1, "nrc_test_fake", ())


def test_nre030_arbitrary_shortlist_input_cannot_claim_resolution_scope():
    with pytest.raises(ValueError):
        c.NutritionResolutionScopeV1.model_validate({"candidates": [], "status": "COMPLETE"})
    s = sources()
    assert len(estimate(s).configurations) == 6  # no dominance/pruning hides a tier


def test_nre031_foreign_recipe_version_or_body_detected_even_with_outer_hash():
    s = changed(sources(), lambda d: d["recipes"][0].update(procedure="TEST_ONLY forged body"))
    assert_unavailable(s, "ENVIRONMENT_MISMATCH")


def test_nre032_missing_seal_and_unauthorized_tier_detected():
    s = changed(sources(), lambda d: d.update(recipe_seals=[]))
    assert_unavailable(s, "RECIPE_SEAL_COVERAGE")
    data = canonical(sources())
    data["recipes"][0]["portion_tiers"][0]["quantities"] = []
    with pytest.raises(ValueError):
        rehash(data)


@pytest.mark.parametrize("approved", [False, True])
def test_nre032_nre036_exact_substitution_and_structural_combination(approved):
    def substitute(d):
        recipe = d["recipes"][0]
        rules = []
        for index, item in enumerate(recipe["ingredients"]):
            rules.append(
                dict(
                    id=str(uuid4()),
                    recipe_version_id=recipe["id"],
                    key=f"TEST_ONLY_swap_{index}",
                    version=1,
                    requirement_id=item["id"],
                    replacement_ingredient_id=recipe["ingredients"][1 - index]["ingredient_id"],
                    quantity_factor="2" if index == 0 else "0.5",
                    structural=True,
                    provenance=recipe["provenance"],
                )
            )
        ids = sorted(r["id"] for r in rules)
        recipe["variant_rules"] = rules
        if approved:
            recipe["approved_combinations"] = [
                dict(
                    id=str(uuid4()),
                    recipe_version_id=recipe["id"],
                    key="TEST_ONLY_both",
                    rule_ids=ids,
                    provenance=recipe["provenance"],
                )
            ]
        d["scope"]["recipes"][0]["rule_selections"] = [ids]
        for serving in d["scope"]["slots"][0]["alternatives"]:
            serving["rule_ids"] = ids

    s = mutate_food(sources(), substitute)
    result = estimate(s)
    if approved:
        assert numbers(result) == (11, 12, 13, 23, 24, 25)
        assert check(s, result).decision == "CONSISTENT"
    else:
        assert_unavailable(s, "UNAUTHORIZED_RULE_COMBINATION")


def test_nre033_no_interpolation_between_authored_tiers():
    s = sources()
    assert {x.serving.tier_id for x in estimate(s).configurations} == set(
        s.scope.recipes[0].tier_ids
    )
    assert numbers(estimate(s)) == (10, 12, 14, 22, 24, 26)


def test_nre034_none_and_discrete_envelope_include_both_endpoints():
    r = estimate(sources())
    delta_sets = {}
    for conf in r.configurations:
        for i in conf.ingredients:
            delta_sets.setdefault(i.requirement_id, set()).add(
                Fraction(i.delta.numerator, i.delta.denominator)
            )
    assert sorted(map(len, delta_sets.values())) == [1, 3]
    assert {Fraction(-1), Fraction(0), Fraction(1)} in list(delta_sets.values())


def test_nre035_negative_delta_is_exact_and_keeps_positive_composition():
    r = estimate(sources())
    negative = [i for x in r.configurations for i in x.ingredients if i.delta.numerator < 0]
    assert negative and all(
        Fraction(i.amount.numerator, i.amount.denominator) in {2, 5} for i in negative
    )


def test_nre036_discrete_quantum_survives_every_enumerated_state():
    s = sources()
    discrete_id = next(i.id for i in s.recipes[0].ingredients if i.scaling.kind == "DISCRETE")
    for conf in estimate(s).configurations:
        amount = next(i.amount for i in conf.ingredients if i.requirement_id == discrete_id)
        assert amount.denominator == 1


def test_nre037_continuous_and_to_taste_are_not_discretized():
    def alter(d):
        i = d["recipes"][0]["ingredients"][0]
        i["scaling"] = dict(kind="TO_TASTE", minimum="1", maximum="9")

    s = mutate_food(sources(), alter)
    assert_unavailable(s, "CONTINUOUS_ENVELOPE", "UNSUPPORTED")


def test_nre038_count_without_approved_bridge_is_unsupported():
    def alter(d):
        item = d["recipes"][0]["ingredients"][0]
        item["quantity"].update(basis="COUNT", item_ref="TEST_ONLY.unit")
        target = item["ingredient_id"]
        next(r for r in d["scope"]["references"] if r["ingredient_id"] == target)["basis"] = "COUNT"

    s = mutate_food(sources(), alter)
    assert_unavailable(s, "COUNT_NUTRITION_SOURCE_UNAVAILABLE", "UNSUPPORTED")


def test_nre039_nonzero_analysis_is_not_a_frozen_planner_candidate():
    r = estimate(sources())
    assert any(i.delta.numerator for x in r.configurations for i in x.ingredients)
    assert all(type(x) is c.ResolutionConfigurationV1 for x in r.configurations)
    assert r.planner_ready is False and r.policy_synthesis == "NOT_PERFORMED"


def test_nre040_pinned_reviewed_compatible_reference_matches_every_ingredient():
    s = sources()
    refs = {r.id: r for r in s.references}
    for conf in estimate(s).configurations:
        for line in conf.ingredients:
            reference = refs[line.reference_id]
            assert reference.fact.ingredient_id == line.ingredient_id
            assert reference.fact.reference.basis == line.basis
            assert reference.fact.status == "REVIEWED"


def test_nre041_draft_reference_never_falls_back():
    s = mutate_food(sources(), lambda d: d["references"][0]["fact"].update(status="DRAFT"))
    assert_unavailable(s, "REFERENCE_UNREVIEWED", "UNAVAILABLE")


def test_nre042_raw_cooked_reference_mismatch_is_not_a_conversion():
    s = mutate_food(
        sources(), lambda d: d["references"][0]["fact"]["reference"].update(basis="COOKED_G")
    )
    assert_unavailable(s, "REFERENCE_BASIS_MISMATCH", "UNSUPPORTED")


def test_nre043_cooking_mass_yield_does_not_change_input_nutrients():
    s = sources()

    def add(d):
        r = d["recipes"][0]
        i = r["ingredients"][0]
        r["transformations"] = [
            dict(
                id=str(uuid4()),
                recipe_version_id=r["id"],
                requirement_id=i["id"],
                ingredient_id=i["ingredient_id"],
                preparation_key="TEST_ONLY",
                method=r["recipe"]["cooking_method"],
                version=1,
                source_basis="EP_RAW_G",
                target_basis="COOKED_G",
                factor="0.5",
                provenance=r["provenance"],
            )
        ]

    other = mutate_food(s, add)
    assert numbers(estimate(s)) == numbers(estimate(other))
    assert estimate(other).measurement_basis == "PLANNED_INGREDIENT_INPUT_V1"


def test_nre044_nonterminating_rational_never_rounded_to_decimal_or_float():
    s = mutate_food(
        sources(), lambda d: [r["fact"]["reference"].update(amount="3") for r in d["references"]]
    )
    r = estimate(s)
    assert numbers(r) == tuple(Fraction(v, 3) for v in (10, 12, 14, 22, 24, 26))
    assert check(s, r).decision == "CONSISTENT"


def test_nre045_explicit_numeric_zero_distinct_from_absence():
    s = sources()
    assert any(
        i.nutrients[2].numerator == 0 for x in estimate(s).configurations for i in x.ingredients
    )
    raw = canonical(s)
    del raw["references"][0]["fact"]["nutrients"]["fat_g"]
    with pytest.raises(ValueError):
        rehash(raw)


@pytest.mark.parametrize("value", [True, 1.5, float("nan"), float("inf"), "1"])
def test_nre046_coercion_float_boolean_and_nonfinite_rejected(value):
    with pytest.raises(ValueError):
        c.NreRational(numerator=value, denominator=1)


def test_nre047_exact_reduction_and_signed_delta_are_distinct():
    with pytest.raises(ValueError):
        c.NreRational(numerator=2, denominator=4)
    with pytest.raises(ValueError):
        c.NreRational(numerator=-1, denominator=1)
    assert c.NreDelta(numerator=-1, denominator=1).numerator == -1


def test_nre048_omitted_ingredient_or_line_fails_independent_recomputation():
    s = sources()
    original = estimate(s)
    bad = forged(original, lambda d: d["configurations"][0]["ingredients"].pop())
    assert check(s, bad).decision == "INCONSISTENT"


def test_nre049_exact_single_member_whole_tier_binding_retained():
    s = sources()
    for conf in estimate(s).configurations:
        assert conf.serving.kind == "WHOLE_TIER_TO_SINGLE_TRACKED_MEMBER_V1"
        assert conf.serving.subject == s.scope.subject
        assert conf.serving.actor_user_id == s.scope.actor_user_id


def test_nre050_missing_assignment_is_not_inferred():
    s = changed(sources(), lambda d: d["scope"]["slots"][0].update(alternatives=[]))
    assert_unavailable(s, "EMPTY_UNIVERSE", "UNAVAILABLE")


def test_nre051_no_divide_by_serving_count_or_portion_factor():
    s = sources()
    r = estimate(s)
    assert 24 in numbers(r)  # whole authored two-serving tier, not 24/2
    assert 6 in {
        Fraction(i.nutrients[2].numerator, i.nutrients[2].denominator)
        for x in r.configurations
        for i in x.ingredients
        if i.nutrients[2].numerator
    }
    # The larger tier's fixed second-ingredient fat is 12, never attendance-scaled.
    assert (
        max(
            Fraction(x.nutrients[2].numerator, x.nutrients[2].denominator) for x in r.configurations
        )
        == 12
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("nutrition_role", "SHARED"),
        ("kind", "FRACTIONAL_TIER"),
        ("fraction", "0.5"),
        ("leftovers", True),
        ("participants", []),
    ],
)
def test_nre052_partial_shared_leftover_allocation_rejected(field, value):
    raw = canonical(sources().scope.slots[0].alternatives[0]) | {field: value}
    with pytest.raises(ValueError):
        c.NreServingDeclaration.model_validate(raw)


def test_nre053_cross_member_slot_or_serving_definition_does_not_transfer():
    s = changed(
        sources(),
        lambda d: d["scope"]["slots"][0]["alternatives"][0].update(slot_id="TEST_ONLY_other"),
    )
    assert_unavailable(s, "SERVING_IDENTITY")


def test_nre054_planned_offered_never_consumed_or_accepted_exposure():
    r = estimate(sources())
    assert r.consumption == "NOT_ASSERTED"
    assert r.hard_policy_feasibility == "NOT_EVALUATED"
    assert r.solver_infeasibility == "NOT_PROVEN"


def test_nre055_joint_vector_correlation_not_marginal_extrema():
    s = sources()
    r = estimate(s)
    vectors = [
        tuple(Fraction(v.numerator, v.denominator) for v in x.nutrients)
        for x in r.periods[0].vectors
    ]
    forged_extrema = (
        min(x[0] for x in vectors),
        max(x[1] for x in vectors),
        min(x[2] for x in vectors),
        max(x[3] for x in vectors),
    )
    assert forged_extrema not in vectors


def test_nre056_equal_vectors_keep_all_configuration_witnesses():
    s = mutate_food(
        sources(),
        lambda d: [
            r["fact"]["nutrients"].update(
                energy_kcal="0", protein_g="0", fat_g="0", carbohydrate_g="0"
            )
            for r in d["references"]
        ],
    )
    r = estimate(s)
    assert len(r.periods[0].vectors) == 1
    assert len(r.periods[0].vectors[0].configurations) == 6
    assert len(r.configurations) == 6
    assert check(s, r).decision == "CONSISTENT"


def test_nre057_multi_slot_sums_match_small_independent_expected_set():
    s = sources()

    def add_slot(d):
        second = deepcopy(d["scope"]["slots"][0])
        second["slot_id"] = "TEST_ONLY_second"
        for a in second["alternatives"]:
            a["slot_id"] = second["slot_id"]
        d["scope"]["slots"].append(second)

    s = changed(s, add_slot)
    r = estimate(s)
    expected = sorted({x + y for x in (10, 12, 14, 22, 24, 26) for y in (10, 12, 14, 22, 24, 26)})
    assert numbers(r) == tuple(expected)
    assert sum(len(v.configurations) for v in r.periods[0].vectors) == 36
    assert check(s, r).decision == "CONSISTENT"


def test_nre058_gcd_does_not_fill_reachability_holes():
    r = estimate(sources())
    assert numbers(r) == (10, 12, 14, 22, 24, 26)
    assert 16 not in numbers(r) and 18 not in numbers(r)


def test_nre059_exact_gaps_endpoint_witnesses_and_maximum():
    s = sources()
    m = estimate(s).measurements[0]
    assert tuple(Fraction(g.amount.numerator, g.amount.denominator) for g in m.gaps) == (
        2,
        2,
        8,
        2,
        2,
    )
    assert m.maximum_gap == c.NreRational(numerator=8, denominator=1)
    assert all(g.lower_witnesses and g.upper_witnesses for g in m.gaps)


def test_nre060_singleton_has_no_adjacent_step_not_zero():
    def change(d):
        r = d["recipes"][0]
        r["ingredients"][0]["adjustment"] = dict(kind="NONE", min_delta="0", max_delta="0")
        first = d["scope"]["recipes"][0]["tier_ids"][0]
        d["scope"]["recipes"][0]["tier_ids"] = [first]
        d["scope"]["slots"][0]["alternatives"] = [
            a for a in d["scope"]["slots"][0]["alternatives"] if a["tier_id"] == first
        ]

    s = mutate_food(sources(), change)
    m = estimate(s).measurements[0]
    assert len(m.values) == 1 and m.step_state == "NO_ADJACENT_STEP"
    assert m.maximum_gap is None and not m.gaps


def test_nre061_large_gap_elsewhere_does_not_imply_band_emptiness():
    r = estimate(sources())
    assert r.measurements[0].maximum_gap.numerator == 8
    assert {v for v in numbers(r) if 11 <= v <= 13} == {12}
    assert r.availability == "AVAILABLE"  # width 2 is smaller than an unrelated gap 8


def test_nre062_marginal_hit_is_not_whole_plan_feasibility():
    r = estimate(sources())
    assert 12 in numbers(r)
    assert r.hard_policy_feasibility == "NOT_EVALUATED" and r.solver_infeasibility == "NOT_PROVEN"


def test_nre063_no_proportional_slot_splitting_across_boundary():
    s = sources()

    def straddle(d):
        d["scope"]["slots"][0]["interval"]["end"] = s.scope.slots[0].interval.end + timedelta(
            seconds=1
        )

    assert_unavailable(changed(s, straddle), "TEMPORAL_MAPPING_UNSUPPORTED", "UNSUPPORTED")


def test_nre064_no_implicit_zero_for_missing_required_cell():
    s = sources()

    def move(d):
        d["scope"]["slots"][0]["interval"] = dict(
            start=s.scope.slots[0].interval.end,
            end=s.scope.slots[0].interval.end + timedelta(hours=1),
        )

    assert_unavailable(changed(s, move), "UNASSIGNED_SLOT", "UNSUPPORTED")


def test_nre065_temporal_sums_are_same_basis_contributions_not_clinical_conversion():
    r = estimate(sources())
    assert r.measurement_basis == "PLANNED_INGREDIENT_INPUT_V1"
    assert all(x.basis == r.measurement_basis for x in r.measurements)
    raw = canonical(sources().scope) | {"daily_to_weekly_factor": "7"}
    with pytest.raises(ValueError):
        c.NutritionResolutionScopeV1.model_validate(raw)


@pytest.mark.parametrize("missing_day", [False, True])
def test_nre063_nre064_nre065_parent_period_sums_exact_declared_day_contributions(missing_day):
    synthesis = weekly_sources(retained().inputs)

    def add_week_measurement(body):
        case = body["cases"][0]
        operation = deepcopy(
            next(
                x
                for x in case["operations"]
                if x["kind"] == "MAKE_CONSTRAINT" and x["layer"] == "COMFORT"
            )
        )
        operation.update(
            id="TEST_ONLY_week_comfort",
            inputs=["lower", "upper"],
            temporal=canonical(synthesis.request.root.sources.request.temporal),
        )
        case["operations"].append(operation)

    synthesis = reauthor_rule(synthesis, add_week_measurement)
    s = sources(synthesis)

    def one_tier_per_day(d):
        recipe = d["recipes"][0]
        recipe["ingredients"][0]["adjustment"] = dict(kind="NONE", min_delta="0", max_delta="0")
        tier = next(x for x in recipe["portion_tiers"] if x["servings"] == "1")
        d["scope"]["recipes"][0]["tier_ids"] = [tier["id"]]
        template = next(
            a for a in d["scope"]["slots"][0]["alternatives"] if a["tier_id"] == tier["id"]
        )
        slots = []
        start = s.scope.root_request.temporal.interval.start
        for index in range(7):
            name = f"TEST_ONLY_day_{index}"
            slots.append(
                dict(
                    slot_id=name,
                    interval=dict(
                        start=start + timedelta(days=index), end=start + timedelta(days=index + 1)
                    ),
                    alternatives=[template | {"slot_id": name}],
                )
            )
        d["scope"]["slots"] = slots

    s = mutate_food(s, one_tier_per_day)
    if missing_day:
        s = changed(s, lambda d: d["scope"]["slots"].pop())
        result = assert_unavailable(s, "TEMPORAL_COVERAGE_MISSING", "UNAVAILABLE")
        assert check(s, result).decision == "CONSISTENT"
        return
    result = estimate(s)
    assert result.availability == "AVAILABLE", result.reasons
    assert len(result.periods) == 8
    assert [
        p.vectors[0].nutrients[0].numerator for p in result.periods if p.temporal.kind == "WEEK"
    ] == [84]
    assert {
        p.vectors[0].nutrients[0].numerator for p in result.periods if p.temporal.kind == "DAY"
    } == {12}
    assert check(s, result).decision == "CONSISTENT"


def test_nre066_cross_publication_horizon_change_cannot_reuse_requirement():
    s = sources()
    value = changed(
        s,
        lambda d: d["scope"]["root_request"]["temporal"]["interval"].update(
            end=s.scope.root_request.temporal.interval.end + timedelta(days=1)
        ),
    )
    assert_unavailable(value, "SUBJECT_REQUEST_IDENTITY")


def test_nre067_source_after_cut_rejected_no_invented_ttl():
    s = sources()
    value = mutate_food(
        s,
        lambda d: d["references"][0]["fact"]["provenance"].update(
            observed_at=s.frame.completed_at + timedelta(seconds=1)
        ),
    )
    assert_unavailable(value, "SOURCE_AFTER_CUT")
    with pytest.raises(ValueError):
        c.NutritionResolutionScopeV1.model_validate(canonical(s.scope) | {"freshness_ttl": 0})


def test_nre068_retained_replay_stable_after_different_source_package():
    s = sources()
    original = estimate(s)
    different = mutate_food(
        s, lambda d: d["references"][0]["fact"]["nutrients"].update(energy_kcal="9")
    )
    assert numbers(estimate(different)) != numbers(original)
    assert estimate(s) == original
    assert check(s, original).current_authorization == "NOT_CLAIMED"


@pytest.mark.parametrize("value", ["9" * 1000, "[" * 33 + "0" + "]" * 33, '{"a":1,"a":2}'])
def test_nre069_hostile_integer_nesting_duplicate_fields_preparse(value):
    with pytest.raises(ValueError):
        ingest(value)
    with pytest.raises(ValueError):
        structure(Decimal("1e1000000000"))
    with pytest.raises(ValueError, match="encoded bytes"):
        structure({"\x00" * 100: ""}, byte_limit=500)
    with pytest.raises(ValueError, match="encoded bytes"):
        structure([{}] * 400, byte_limit=1000)


def test_nre070_cartesian_limit_checked_without_allocating_product():
    with pytest.raises(ValueError, match="Cartesian"):
        WorkBudget().product([64] * 32)
    s = changed(sources(), lambda d: d["scope"].update(max_states=2))
    assert_unavailable(s, state="RESOURCE_EXCEEDED")


def test_nre071_intermediate_rational_and_complete_output_work_limit():
    with pytest.raises(ValueError, match="rational"):
        WorkBudget().number(Fraction(1 << 256, 1))
    s = changed(sources(), lambda d: d["scope"].update(max_work=1))
    r = assert_unavailable(s, "WORK_LIMIT", "RESOURCE_EXCEEDED")
    assert check(s, r).decision == "CONSISTENT"


def test_nre072_caller_cannot_raise_profile_or_budget():
    with pytest.raises(ValueError):
        c.NreResourceProfile(states=1_000_000)
    with pytest.raises(ValueError):
        c.NutritionResolutionScopeV1.model_validate(
            canonical(sources().scope) | {"max_work": 1_000_001}
        )


def test_nre073_pure_replay_survives_disabled_environment_and_file_access(monkeypatch):
    s = sources()
    expected = estimate(s)

    def forbidden(*args, **kwargs):
        raise AssertionError("pure replay attempted external access")

    monkeypatch.setattr(os, "getenv", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    assert estimate(s) == expected
    assert check(s, expected).decision == "CONSISTENT"


def test_nre074_operational_timeout_not_part_of_pure_estimator():
    guards = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]
    bad = guards("import time\nx = time.time()", "app.modules.nutrition.resolution_estimator")
    assert any("NRE" in x for x in bad)
    assert estimate(sources()).solver_infeasibility == "NOT_PROVEN"


def test_nre075_server_fixture_manifest_required_not_test_label():
    s = changed(sources(), lambda d: d["frame"].update(fixture_manifest=[]))
    assert_unavailable(s, "ENVIRONMENT_MISMATCH")


def test_nre076_mixed_environment_and_production_relabel_rejected():
    with pytest.raises(ValueError):
        c.NutritionResolutionScopeV1.model_validate(
            canonical(sources().scope) | {"environment": "REVIEWED_PRODUCTION"}
        )
    s = changed(sources(), lambda d: d["frame"].update(fixture_database_name="production"))
    assert_unavailable(s, "ENVIRONMENT_MISMATCH")


def test_nre077_reviewed_catalog_and_test_pass_cannot_open_content_gate():
    h = nutrition_resolution_handoff(sources())
    assert handoff_check(h).decision == "CONSISTENT"
    assert h.production_admission == "CLOSED" and h.policy_integration == "NOT_AUTHORIZED"


def test_nre078_rehashed_wrong_values_fail_independent_arithmetic():
    s = sources()
    r = forged(
        estimate(s),
        lambda d: d["configurations"][0]["nutrients"][0].update(numerator=999, denominator=1),
    )
    assert check(s, r).decision == "INCONSISTENT"


def test_nre079_forged_consistent_report_with_matching_public_hashes_not_proof():
    s = sources()
    r = forged(
        estimate(s),
        lambda d: d["measurements"][0].update(maximum_gap=dict(numerator=1, denominator=1)),
    )
    fake = c.NutritionResolutionCheckV1(
        decision="CONSISTENT",
        numerical_use="AVAILABLE_RETAINED_ONLY",
        findings=(),
        source_fingerprint=s.source_fingerprint,
        reconstructed_result_fingerprint=r.result_fingerprint,
    )
    assert fake.source_fingerprint == s.source_fingerprint
    assert check(s, r).decision == "INCONSISTENT"
    with pytest.raises(TypeError):
        check(s, r, fake)
    assert (
        handoff_check(
            canonical(c.NutritionResolutionHandoffV2(sources=s, estimate=r))
            | {"validation": canonical(fake)}
        ).decision
        == "INCONSISTENT"
    )


def test_nre080_model_copy_and_omitted_absence_not_trusted():
    s = sources()
    forged_source = s.model_copy(update={"recipes": ()})
    assert estimate(forged_source).availability != "AVAILABLE"
    data = canonical(s)
    data["references"].pop()
    data["frame"]["owner_row_count"] -= 1
    missing = rehash(data)
    assert_unavailable(missing, "ABSENCE_MANIFEST")


@pytest.mark.parametrize(
    "target",
    [
        "app.modules.nutrition.resolution_estimator",
        "app.modules.nutrition.synthesis",
        "app.modules.recipes.public",
        "app.modules.planning.grounding",
        "sqlalchemy",
        "os",
    ],
)
def test_nre081_import_guards_enforce_independence(target):
    audit = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]
    assert audit("import " + target, "app.modules.validation.nutrition_resolution")


def test_nre082_independent_checker_catches_delta_and_serving_scale_corruption():
    s = sources()
    r = forged(
        estimate(s),
        lambda d: d["configurations"][0]["ingredients"][0]["delta"].update(
            numerator=99, denominator=1
        ),
    )
    assert check(s, r).decision == "INCONSISTENT"


def test_nre083_rehashed_calendar_mutation_fails_reconstruction():
    s = sources()
    r = forged(
        estimate(s),
        lambda d: d["measurements"][0]["descriptor"]["temporal"].update(calendar="TEST_ONLY_wrong"),
    )
    assert check(s, r).decision == "INCONSISTENT"


def test_nre084_consistent_unavailable_never_numerically_admitted():
    s = mutate_food(sources(), lambda d: d["references"][0]["fact"].update(status="DRAFT"))
    r = estimate(s)
    report = check(s, r)
    assert report.decision == "CONSISTENT" and report.numerical_use == "NOT_ADMITTED"


def test_nre085_internally_reauthored_package_does_not_prove_database_origin():
    s = mutate_food(
        sources(), lambda d: d["references"][0]["fact"]["nutrients"].update(energy_kcal="19")
    )
    report = check(s, estimate(s))
    assert report.decision == "CONSISTENT"
    assert report.source_origin == "RETAINED_CONSISTENCY_NOT_DATABASE_PROOF"
    assert (
        report.current_authorization == "NOT_CLAIMED"
        and report.scientific_correctness == "NOT_CERTIFIED"
    )


def test_nre086_canonical_handoff_not_castable_to_fixture_v1():
    h = nutrition_resolution_handoff(sources())
    with pytest.raises(ValueError):
        p.NutritionResolutionInput.model_validate(canonical(h))
    with pytest.raises(ValueError):
        c.NutritionResolutionHandoffV2.model_validate(
            canonical(h) | {"protocol": "TEST_ONLY_RESOLUTION_FIXTURE_V1"}
        )


def test_nre087_frozen_producer_and_independent_v1_checker_still_accept_old_fixture():
    old = retained()
    assert derive(old.inputs).outcome == "AVAILABLE"
    report = validate_nutrition_policy_independently(
        p.NutritionPolicyValidationInput(
            policy=old, coverage="SYNTHESIS_SOURCE_AND_POLICY_SEMANTICS"
        )
    )
    assert report.decision == "CONSISTENT"


def test_nre088_handoff_rechecks_retained_sources_not_caller_expected_step():
    h = nutrition_resolution_handoff(sources())
    assert handoff_check(h).decision == "CONSISTENT"
    bad = canonical(h)
    bad["estimate"]["source_fingerprint"] = "1" * 64
    assert handoff_check(bad).decision == "INCONSISTENT"


def test_nre089_planned_input_not_admitted_as_physiological_intake():
    s = sources()
    h = nutrition_resolution_handoff(s)
    assert h.estimate.measurement_basis == "PLANNED_INGREDIENT_INPUT_V1"
    assert h.policy_integration == "NOT_AUTHORIZED"
    with pytest.raises((ValueError, AttributeError, TypeError)):
        synthesize_nutrition_policy(s.synthesis_sources, h)


def test_nre090_resolution_soft_hard_and_solver_states_not_collapsed():
    r = estimate(sources())
    assert not {v for v in numbers(r) if 15 <= v <= 21}  # local scalar gap only
    assert r.availability == "AVAILABLE" and r.hard_policy_feasibility == "NOT_EVALUATED"
    assert r.solver_infeasibility == "NOT_PROVEN"


def test_nre091_package_size_and_data_confidence_are_not_resolution_operands():
    for field in ("package_size", "DataConfidence", "hard_bound_widening"):
        with pytest.raises(ValueError):
            c.NutritionResolutionScopeV1.model_validate(
                canonical(sources().scope) | {field: "TEST_ONLY"}
            )


@pytest.mark.parametrize(
    "field", ["CostPreference", "BudgetPressure", "BudgetContract", "KitchenEffort", "TasteFit"]
)
def test_nre092_preferences_cannot_supply_or_weaken_root_truth(field):
    with pytest.raises(ValueError):
        c.NutritionResolutionScopeV1.model_validate(
            canonical(sources().scope) | {field: "TEST_ONLY"}
        )


def test_nre093_estimator_needs_no_completed_resolved_plan_policy():
    s = sources()
    assert estimate(s).availability == "AVAILABLE"
    assert "ResolvedPlanPolicy" not in c.NutritionResolutionScopeV1.model_fields
    assert not estimate(s).planner_ready


def test_nre094_480_export_hashes_and_frozen_files_remain_identical():
    proof = json.loads(COMPAT.read_text())
    schema = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
    for name, expected in proof["baseline_definitions"].items():
        actual = hashlib.sha256(
            json.dumps(schema[name], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        assert actual == expected, name
    assert len(proof["baseline_definitions"]) == 480
    assert len(proof["new_definitions"]) == 23
    assert set(schema) == set(proof["baseline_definitions"]) | set(proof["new_definitions"])
    for path, expected in proof["frozen_files"].items():
        assert hashlib.sha256((ROOT / path).read_text().encode()).hexdigest() == expected, path


def test_nre095_all_3912_baseline_test_identities_retained():
    proof = json.loads(COMPAT.read_text())
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-o", "addopts="],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )

    def normalize(value):
        return re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<UUID>", value
        )

    current = Counter(normalize(line) for line in result.stdout.splitlines() if "::" in line)
    assert len(proof["baseline_tests"]) == 3912
    baseline = Counter(map(normalize, proof["baseline_tests"]))
    assert not (baseline - current)


def test_nre096_no_new_persistence_or_activation_authority():
    import app.persistence.models  # noqa: F401
    from app.shared.db import Base

    assert len(Base.metadata.tables) == 108
    h = nutrition_resolution_handoff(sources())
    assert not h.planner_ready and not h.activation_ready
    assert h.production_admission == "CLOSED" and h.policy_integration == "NOT_AUTHORIZED"
    # AST only: no live publication or policy-integration method appears in the facade.
    tree = ast.parse((ROOT / "apps/backend/app/modules/nutrition/resolution_public.py").read_text())
    assert {n.name for n in tree.body if isinstance(n, ast.FunctionDef)} == {
        "nutrition_resolution_handoff"
    }
