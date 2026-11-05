"""CFP acceptance: exact retained source replay and explicitly bounded authority."""

import ast
import builtins
import hashlib
import json
import os
import re
import runpy
import socket
import subprocess
import sys
import time
from collections import Counter
from datetime import timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from app.domain.resolution import ResolutionError
from app.modules.planning import contracts as p
from app.modules.planning.grounding import resolve_captured_candidate
from app.modules.planning.public import (
    project_candidate_features as project,
)
from app.modules.planning.public import (
    validate_candidate_feature_projection as validate,
)
from app.modules.recipes import contracts as r
from candidate_feature_fixtures import (
    advance_catalog,
    alternate_grounding,
    change_feature,
    make_subject,
    replace_review,
    seal_ground,
    seal_result,
    seal_source,
)
from grounding_fixtures import empty_inventory

ROOT = Path(__file__).resolve().parents[3]
CORE = "app.modules.planning.candidate_feature_projection"


def rejected(code, operation, value):
    with pytest.raises(ResolutionError) as exc:
        operation(value)
    assert exc.value.code == code
    return exc.value


def changed_ground(source, candidate):
    candidate = seal_ground(candidate)
    request = source.request.model_copy(
        update=dict(
            grounding_request=candidate.request,
            expected_grounding_fingerprint=candidate.fingerprint,
        )
    )
    return seal_source(
        source.model_copy(update=dict(request=request, grounded_candidate=candidate))
    )


def changed_claim(source, culinary):
    q = source.request.grounding_request.model_copy(update=dict(candidate=culinary))
    return changed_ground(source, source.grounded_candidate.model_copy(update=dict(request=q)))


def test_cfp01_three_dimensions_for_one_canonical_candidate():
    source = make_subject()
    result = project(source)
    assert tuple(d.dimension for d in result.dimensions) == ("FLAVOR", "MAIN_PROTEIN", "METHOD")
    assert all(d.state == "ASSIGNED" for d in result.dimensions)
    assert result.binding.grounding_fingerprint == source.grounded_candidate.fingerprint
    assert result.binding.recipe_id == source.grounded_candidate.sources.recipe.recipe.id
    assert result.source == source and not result.planner_ready and not result.activation_ready


def test_cfp02_method_child_has_no_path_but_outer_binding_does():
    source = make_subject(("METHOD",))
    result = project(source)
    assert source.feature_input.path is None
    assert result.binding.path.tier_id == source.request.grounding_request.candidate.tier_id
    assert all(delta == 0 for _, delta in result.binding.path.deltas)


def test_cfp03_main_protein_retains_pinned_support_and_complete_history():
    source = make_subject(("MAIN_PROTEIN",))
    row = project(source).dimensions[0]
    scope = source.feature_input.sources.scopes[0]
    support = scope.reviews[0].command.supports[0]
    assert support.term_id == row.positive_term_ids[0]
    assert (
        support.catalog_review_id == source.feature_input.sources.catalog_streams[0].reviews[0].id
    )
    assert (
        support.ingredient_id
        == source.request.grounding_request.candidate.resolved_ingredients[0].ingredient_id
    )


def test_cfp04_flavor_exact_path_uses_owner_discovery():
    source = make_subject(("FLAVOR",))
    result = project(source)
    assert result.dimensions == r.discover_feature_input(source.feature_input)
    assert result.dimensions[0].review_id == source.feature_input.sources.scopes[0].reviews[-1].id


def test_cfp05_another_complete_recipe_version_is_not_a_fallback():
    source, other = make_subject(), make_subject()
    rejected(
        "RECIPE_VERSION_MISMATCH",
        project,
        change_feature(source, recipe=other.feature_input.recipe),
    )


def test_cfp06_alternate_authored_tier_does_not_match_first_tier_review():
    source = make_subject(("FLAVOR",))
    alternate = make_subject(("FLAVOR",), grounding=alternate_grounding(source))
    result = project(alternate)
    assert result.binding.path.tier_id != project(source).binding.path.tier_id
    assert result.dimensions[0].reason == "NO_MATCHING_SCOPE"


def test_cfp07_transformation_context_is_retained_and_recomputed():
    source = make_subject(("FLAVOR",))
    assert source.feature_input.sources.scopes[0].key.slots[0].preparation == "TRANSFORMATION"
    assert project(source).dimensions[0].state == "ASSIGNED"
    candidate = source.request.grounding_request.candidate.model_copy(
        update=dict(transformations=())
    )
    candidate = candidate.model_copy(update=dict(fingerprint=candidate.expected_fingerprint()))
    rejected("GROUNDING_REJECTED", project, changed_claim(source, candidate))


@pytest.mark.parametrize("field", ["delta", "servings", "ingredient", "transformation"])
def test_cfp08_forged_culinary_claims_are_rejected(field):
    source = make_subject()
    c = source.request.grounding_request.candidate
    if field in {"delta", "ingredient"}:
        row = c.resolved_ingredients[0].model_copy(
            update=(
                dict(adjustment_delta=Decimal(1))
                if field == "delta"
                else dict(ingredient_id=uuid4())
            )
        )
        c = c.model_copy(update=dict(resolved_ingredients=(row,)))
    elif field == "servings":
        c = c.model_copy(update=dict(serving_count=Decimal(999)))
    else:
        c = c.model_copy(update=dict(transformations=()))
    c = c.model_copy(update=dict(fingerprint=c.expected_fingerprint()))
    with pytest.raises(ResolutionError) as exc:
        project(changed_claim(source, c))
    assert exc.value.code in {"INVALID_REQUEST", "GROUNDING_REJECTED"} and exc.value.rejected


def test_cfp09_same_method_on_different_authored_paths_is_distinct_subject_identity():
    source = make_subject(("METHOD",))
    q, sources = alternate_grounding(source)
    fresh = resolve_captured_candidate(q, sources)
    other = changed_ground(source, fresh.candidate)
    a, b = project(source), project(other)
    assert a.dimensions == b.dimensions and a.binding.path != b.binding.path
    assert a.fingerprint != b.fingerprint


@pytest.mark.parametrize("dimension", ["INGREDIENT", "PROTEIN", "UTILITY", 0])
def test_cfp10_unsupported_dimension_has_no_substitute(dimension):
    source = make_subject()
    request = source.request.model_dump() | dict(requested_dimensions=(dimension,))
    rejected("UNSUPPORTED_DIMENSION", project, source.model_copy(update=dict(request=request)))


@pytest.mark.parametrize(
    "change",
    [
        dict(requested_dimensions=()),
        dict(requested_dimensions=("METHOD", "METHOD")),
        dict(canonical=True),
        dict(contract_version="candidate-feature-projection-request.v2"),
    ],
)
def test_cfp11_invalid_request_shape_is_not_normalized_into_authority(change):
    source = make_subject()
    request = source.request.model_dump() | change
    rejected("INVALID_REQUEST", project, source.model_copy(update=dict(request=request)))


def test_cfp12_dimension_set_order_normalizes_deterministically():
    source = make_subject()
    q = p.CandidateFeatureProjectionRequest.model_validate(
        source.request.model_dump()
        | dict(
            requested_dimensions=tuple(reversed(source.request.requested_dimensions)),
        )
    )
    other = source.model_copy(update=dict(request=q))
    assert project(source).fingerprint == project(other).fingerprint


def test_cfp13_cached_grounding_with_recomputed_hash_is_not_authority():
    source = make_subject()
    candidate = source.grounded_candidate.model_copy(
        update=dict(
            input_nutrition=source.grounded_candidate.input_nutrition.model_copy(
                update=dict(protein_g=Decimal(999))
            ),
        )
    )
    rejected("REPLAY_MISMATCH", project, changed_ground(source, candidate))


def test_cfp15_incomplete_primitive_grounding_is_unavailable_not_rejected():
    source = make_subject()
    candidate = source.grounded_candidate.model_copy(
        update=dict(
            sources=source.grounded_candidate.sources.model_copy(
                update=dict(nutrition_references=())
            ),
        )
    )
    error = rejected("GROUNDING_INCOMPLETE", project, changed_ground(source, candidate))
    assert not error.rejected and "NUTRITION" in error.detail


def test_cfp16_rejected_primitive_grounding_preserves_rejection():
    source = make_subject()
    c = source.request.grounding_request.candidate
    row = c.resolved_ingredients[0]
    row = row.model_copy(
        update=dict(quantity=row.quantity.model_copy(update=dict(amount=Decimal(201))))
    )
    c = c.model_copy(update=dict(resolved_ingredients=(row,)))
    c = c.model_copy(update=dict(fingerprint=c.expected_fingerprint()))
    assert rejected("GROUNDING_REJECTED", project, changed_claim(source, c)).rejected


@pytest.mark.parametrize("mutation", ["omit", "edit"])
def test_cfp18_grounding_warnings_are_retained_and_recomputed(mutation):
    source = make_subject(availability="UNKNOWN")
    assert source.grounding_issues[0].code == "UNKNOWN_RETAIL_AVAILABILITY"
    assert project(source).source.grounding_issues == source.grounding_issues
    issues = (
        ()
        if mutation == "omit"
        else (source.grounding_issues[0].model_copy(update=dict(detail="forged")),)
    )
    rejected(
        "REPLAY_MISMATCH",
        project,
        seal_source(source.model_copy(update=dict(grounding_issues=issues))),
    )


def test_cfp19_outer_request_must_equal_retained_child_request():
    source = make_subject()
    q = source.request.grounding_request.model_copy(update=dict(currency="USD"))
    request = source.request.model_copy(update=dict(grounding_request=q))
    rejected("REPLAY_MISMATCH", project, source.model_copy(update=dict(request=request)))


def test_cfp21_recipe_version_mismatch_is_explicit():
    source = make_subject()
    other_recipe = make_subject().feature_input.recipe
    rejected("RECIPE_VERSION_MISMATCH", project, change_feature(source, recipe=other_recipe))


def test_cfp22_same_immutable_recipe_identity_with_different_payload_is_incoherent():
    source = make_subject()
    recipe = source.feature_input.recipe.model_copy(
        update=dict(procedure="Forged immutable procedure")
    )
    rejected("SOURCE_CUT_INCOHERENT", project, seal_source(change_feature(source, recipe=recipe)))


@pytest.mark.parametrize("case", ["tier", "rule", "delta", "method_path"])
def test_cfp23_exact_selected_path_is_checked_before_discovery(case):
    source = make_subject(("METHOD",) if case == "method_path" else ("FLAVOR",))
    path = project(source).binding.path
    if case == "tier":
        path = path.model_copy(update=dict(tier_id=uuid4()))
    if case == "rule":
        path = path.model_copy(update=dict(selected_rule_ids=(uuid4(),)))
    if case == "delta":
        path = path.model_copy(update=dict(deltas=((path.deltas[0][0], Decimal(1)),)))
    rejected("PATH_MISMATCH", project, change_feature(source, path=path))


@pytest.mark.parametrize("field", ["recipe_id", "grounding_fingerprint", "path"])
def test_cfp24_edited_result_binding_is_recomputed_even_when_rehashed(field):
    result = project(make_subject())
    value = uuid4() if field == "recipe_id" else "f" * 64
    if field == "path":
        value = result.binding.path.model_copy(update=dict(tier_id=uuid4()))
    result = seal_result(
        result.model_copy(update=dict(binding=result.binding.model_copy(update={field: value})))
    )
    rejected("PATH_MISMATCH" if field == "path" else "REPLAY_MISMATCH", validate, result)


def test_cfp25_conflicting_duplicate_term_payload_is_never_last_write_wins():
    source = make_subject()
    sources = source.feature_input.sources
    term = sources.terms[0].model_copy(update=dict(label="Conflicting identity"))
    sources = sources.model_copy(update=dict(terms=(*sources.terms, term)))
    rejected("FEATURE_SOURCE_INVALID", project, change_feature(source, sources=sources))


def test_cfp26_feature_dimensions_must_equal_requested_dimensions():
    source = make_subject()
    rejected(
        "SOURCE_CUT_INCOHERENT", project, change_feature(source, requested_dimensions=("METHOD",))
    )


@pytest.mark.parametrize("case", ["missing_term", "extra_term", "missing_stream"])
def test_cfp27_complete_required_manifests_cannot_be_forged(case):
    source = make_subject()
    sources = source.feature_input.sources
    changes = dict(terms=sources.terms[1:])
    if case == "extra_term":
        changes = dict(
            terms=(
                *sources.terms,
                sources.terms[0].model_copy(update=dict(id=uuid4(), code=uuid4().hex)),
            )
        )
    if case == "missing_stream":
        changes = dict(catalog_streams=())
    rejected(
        "FEATURE_SOURCE_INVALID",
        project,
        change_feature(source, sources=sources.model_copy(update=changes)),
    )


@pytest.mark.parametrize("field", ["ingredient_id", "requirement_id", "catalog_review_id"])
def test_cfp28_support_must_bind_actual_ingredient_path_and_catalog_review(field):
    source = make_subject(("MAIN_PROTEIN",))
    sources = source.feature_input.sources
    scope = sources.scopes[0]
    old = scope.reviews[0]
    support = old.command.supports[0].model_copy(update={field: uuid4()})
    command = old.command.model_copy(update=dict(supports=(support,)))
    review = old.model_copy(
        update=dict(command=command, command_hash=command.fingerprint(old.reviewer_user_id))
    )
    scopes = (scope.model_copy(update=dict(reviews=(review,))),)
    rejected(
        "FEATURE_SOURCE_INVALID",
        project,
        change_feature(source, sources=sources.model_copy(update=dict(scopes=scopes))),
    )


def test_cfp29_invalid_review_hash_and_overlapping_scope_are_rejected():
    source = make_subject(("METHOD",))
    scope = source.feature_input.sources.scopes[0]
    old = scope.reviews[0]
    bad = old.model_copy(update=dict(command_hash="f" * 64))
    sources = source.feature_input.sources.model_copy(
        update=dict(scopes=(scope.model_copy(update=dict(reviews=(bad,))),))
    )
    rejected("FEATURE_SOURCE_INVALID", project, change_feature(source, sources=sources))
    command = old.command.model_copy(
        update=dict(expected_recipe_frontier=1, idempotency_key=uuid4().hex)
    )
    aid = uuid4()
    review = old.model_copy(
        update=dict(
            id=uuid4(),
            applicability_id=aid,
            source_sequence=2,
            command=command,
            command_hash=command.fingerprint(old.reviewer_user_id),
        )
    )
    duplicate = scope.model_copy(update=dict(id=aid, reviews=(review,)))
    sources = source.feature_input.sources.model_copy(
        update=dict(scopes=(scope, duplicate), recipe_frontier=2)
    )
    rejected("FEATURE_SOURCE_INVALID", project, change_feature(source, sources=sources))


def test_cfp30_catalog_head_change_remains_stale_not_inferred_support():
    source = advance_catalog(make_subject(("MAIN_PROTEIN",)))
    row = project(source).dimensions[0]
    assert row.state == "UNRESOLVED" and row.reason == "STALE_ASSOCIATION"
    assert (
        row.positive_term_ids == ()
        and len(source.feature_input.sources.catalog_streams[0].reviews) == 2
    )


def test_cfp31_missing_review_is_no_source_not_zero():
    row = project(make_subject(("METHOD",), empty=True)).dimensions[0]
    assert row.state == "UNRESOLVED" and row.reason == "NO_SOURCE" and row.coverage is None


def test_cfp32_nonmatching_authored_scope_is_not_implicit_none():
    source = make_subject(("FLAVOR",))
    source = make_subject(("FLAVOR",), grounding=alternate_grounding(source))
    row = project(source).dimensions[0]
    assert row.state == "UNRESOLVED" and row.reason == "NO_MATCHING_SCOPE"


def test_cfp33_complete_reviewed_none_is_finite_coverage():
    source = make_subject(("METHOD",), positives=False)
    row = project(source).dimensions[0]
    assert row.state == "REVIEWED_NONE" and row.coverage == "COMPLETE"
    assert len(row.covered_term_ids) == 2 and row.positive_term_ids == ()


def test_cfp34_partial_review_without_positive_is_unresolved():
    row = project(make_subject(("METHOD",), coverage="PARTIAL", positives=False)).dimensions[0]
    assert row.state == "UNRESOLVED" and row.reason == "PARTIAL_COVERAGE"


def test_cfp35_partial_review_with_positive_preserves_uncovered_unknowns():
    row = project(make_subject(("METHOD",), coverage="PARTIAL")).dimensions[0]
    assert row.state == "ASSIGNED" and row.coverage == "PARTIAL" and len(row.positive_term_ids) == 1


def test_cfp36_retraction_is_not_reviewed_none():
    source = replace_review(make_subject(("METHOD",)), retract=True)
    row = project(source).dimensions[0]
    assert row.state == "UNRESOLVED" and row.reason == "RETRACTED"
    assert len(source.feature_input.sources.scopes[0].reviews) == 2


def test_cfp40_independent_clocks_and_frontiers_keep_owner_meanings():
    source = make_subject()
    result = project(source)
    assert source.request.grounding_request.as_of != source.feature_input.captured_at
    assert (
        source.feature_input.sources.recipe_frontier
        != source.feature_input.sources.catalog_frontier
    )
    assert (
        result.source.capture_started_at
        <= result.source.feature_input.captured_at
        <= result.source.capture_completed_at
    )


def test_cfp41_feature_review_after_grounding_as_of_may_participate():
    source = make_subject(("METHOD",))
    assert (
        source.request.grounding_request.as_of
        < source.feature_input.sources.scopes[0].reviews[0].recorded_at
    )
    assert project(source).dimensions[0].state == "ASSIGNED"


def test_cfp42_offline_future_cut_is_not_a_current_or_future_origin_certificate():
    source = make_subject(("METHOD",))
    q = source.request.grounding_request.model_copy(
        update=dict(as_of=source.request.grounding_request.as_of + timedelta(days=3650))
    )
    sources = empty_inventory(source.grounded_candidate.sources)
    sources = sources.model_copy(
        update=dict(inventory=sources.inventory.model_copy(update=dict(as_of=q.as_of)))
    )
    future = make_subject(("METHOD",), grounding=(q, sources))
    assert project(future).status == "DERIVED"
    assert not project(future).activation_ready


@pytest.mark.parametrize("case", ["clock", "frontier", "interval"])
def test_cfp43_incoherent_source_cut_is_explicit(case):
    source = make_subject(("METHOD",))
    if case == "interval":
        bad = source.model_copy(
            update=dict(capture_completed_at=source.capture_started_at - timedelta(seconds=1))
        )
        rejected("CAPTURE_CONTEXT_INVALID", project, bad)
        return
    sources = source.feature_input.sources
    if case == "frontier":
        sources = sources.model_copy(update=dict(recipe_frontier=0))
    else:
        scope = sources.scopes[0]
        review = scope.reviews[0].model_copy(
            update=dict(recorded_at=source.feature_input.captured_at + timedelta(seconds=1))
        )
        sources = sources.model_copy(
            update=dict(scopes=(scope.model_copy(update=dict(reviews=(review,))),))
        )
    rejected("SOURCE_CUT_INCOHERENT", project, change_feature(source, sources=sources))


def test_cfp44_retained_serialized_cut_replays_without_live_refresh():
    result = project(make_subject())
    reloaded = p.CandidateFeatureProjectionDraft.model_validate_json(result.model_dump_json())
    assert validate(reloaded) == result
    assert validate(reloaded) is not reloaded


def test_cfp45_self_consistency_does_not_prove_database_origin_or_common_mvcc():
    a, b = make_subject(), make_subject()
    assert project(a).fingerprint != project(b).fingerprint
    for source in (a, b):
        assert validate(project(source)).status == "DERIVED"
        with pytest.raises(ValueError):
            p.CandidateFeatureProjectionRequest.model_validate(
                source.request.model_dump() | dict(canonical=True, sources=source)
            )


def test_cfp46_cached_grounding_output_cannot_override_primitive_inputs():
    source = make_subject()
    candidate = source.grounded_candidate.model_copy(update=dict(preparation_outputs=()))
    rejected("REPLAY_MISMATCH", project, changed_ground(source, candidate))


@pytest.mark.parametrize(
    "change",
    [
        dict(positive_term_ids=(uuid4(),)),
        dict(coverage="PARTIAL"),
        dict(reason="RETRACTED"),
        dict(applicability_id=uuid4()),
        dict(review_id=uuid4()),
    ],
)
def test_cfp47_edited_discovery_rehashed_output_still_fails(change):
    result = project(make_subject(("METHOD",)))
    result = seal_result(
        result.model_copy(update=dict(dimensions=(result.dimensions[0].model_copy(update=change),)))
    )
    rejected("REPLAY_MISMATCH", validate, result)


@pytest.mark.parametrize("case", ["source_hash", "result_hash", "provenance", "extra"])
def test_cfp48_missing_provenance_or_tampered_identity_is_not_accepted(case):
    source = make_subject(("METHOD",))
    if case == "source_hash":
        rejected("REPLAY_MISMATCH", project, source.model_copy(update=dict(fingerprint="f" * 64)))
    elif case == "result_hash":
        rejected(
            "REPLAY_MISMATCH",
            validate,
            project(source).model_copy(update=dict(fingerprint="f" * 64)),
        )
    else:
        raw = source.model_dump()
        if case == "provenance":
            del raw["feature_input"]["sources"]["scopes"][0]["reviews"][0]["command"]["provenance"]
        else:
            raw["canonical"] = True
        rejected(
            "FEATURE_SOURCE_INVALID" if case == "provenance" else "REPLAY_MISMATCH", project, raw
        )


@pytest.mark.parametrize("construction", ["construct", "copy", "shape_parse"])
def test_cfp49_pydantic_shape_or_bypass_is_not_semantic_validation(construction):
    result = project(make_subject(("METHOD",)))
    wrong = result.dimensions[0].model_copy(
        update=dict(state="REVIEWED_NONE", positive_term_ids=())
    )
    data = {field: getattr(result, field) for field in type(result).model_fields}
    data["dimensions"] = (wrong,)
    if construction == "construct":
        bad = p.CandidateFeatureProjectionDraft.model_construct(**data)
    elif construction == "copy":
        bad = result.model_copy(update=dict(dimensions=(wrong,)))
    else:
        bad = p.CandidateFeatureProjectionDraft.model_validate(data)
    rejected("REPLAY_MISMATCH", validate, seal_result(bad))


def test_cfp50_replay_and_validation_are_deterministic_under_io_and_clock_traps(monkeypatch):
    from app.modules.planning.public import PlanStore
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session

    source = make_subject()
    expected = project(source)

    def forbidden(*a, **kw):
        raise AssertionError("I/O or clock access in pure replay")

    with monkeypatch.context() as patch:
        for owner, name in (
            (Engine, "connect"),
            (Session, "execute"),
            (builtins, "open"),
            (Path, "read_text"),
            (Path, "read_bytes"),
            (socket, "create_connection"),
            (socket, "socket"),
            (time, "time"),
            (time, "monotonic"),
            (PlanStore, "clock"),
        ):
            patch.setattr(owner, name, forbidden)
        a, b = project(source), validate(expected)
    assert a == b == expected and a.model_dump_json() == b.model_dump_json()


@pytest.mark.parametrize("change", ["clock", "frontier", "history"])
def test_cfp51_full_source_identity_changes_even_when_positives_do_not(change):
    source = make_subject(("METHOD",))
    if change == "history":
        other = replace_review(source)
    elif change == "frontier":
        other = seal_source(
            change_feature(
                source,
                sources=source.feature_input.sources.model_copy(update=dict(recipe_frontier=7)),
            )
        )
    else:
        other = seal_source(
            source.model_copy(
                update=dict(capture_completed_at=source.capture_completed_at + timedelta(seconds=1))
            )
        )
    a, b = project(source), project(other)
    assert a.dimensions[0].positive_term_ids == b.dimensions[0].positive_term_ids
    assert a.source.fingerprint != b.source.fingerprint and a.fingerprint != b.fingerprint


def test_cfp52_generation_trigger_changes_outer_identity_without_changing_culinary_hash():
    source = make_subject(("METHOD",))
    c = source.request.grounding_request.candidate
    changed = c.model_copy(update=dict(triggers=(r.CulinaryGenerationTrigger.AUTHORED_SELECTION,)))
    assert changed.expected_fingerprint() == c.fingerprint
    other = changed_claim(source, changed)
    assert project(source).fingerprint != project(other).fingerprint


def test_cfp53_new_envelope_timezones_have_one_utc_identity():
    source = make_subject()
    tz = timezone(timedelta(hours=7))
    other = seal_source(
        source.model_copy(
            update=dict(
                capture_started_at=source.capture_started_at.astimezone(tz),
                capture_completed_at=source.capture_completed_at.astimezone(tz),
            )
        )
    )
    assert project(source).fingerprint == project(other).fingerprint


def test_cfp54_frozen_child_ordering_and_decimal_rules_are_not_overridden():
    source = replace_review(make_subject(("METHOD",)))
    scope = source.feature_input.sources.scopes[0]
    sources = source.feature_input.sources.model_copy(
        update=dict(scopes=(scope.model_copy(update=dict(reviews=tuple(reversed(scope.reviews)))),))
    )
    # Frozen 046A itself normalizes revision order; the new layer adds no ordering rule.
    assert project(change_feature(source, sources=sources)) == project(source)
    c = source.request.grounding_request.candidate
    row = c.resolved_ingredients[0]
    row = row.model_copy(
        update=dict(quantity=row.quantity.model_copy(update=dict(amount=Decimal("200.00"))))
    )
    c = c.model_copy(update=dict(resolved_ingredients=(row,)))
    c = c.model_copy(update=dict(fingerprint=c.expected_fingerprint()))
    rejected("INVALID_REQUEST", project, changed_claim(source, c))


@pytest.mark.parametrize("field", ["affinity", "eligible", "default_zero", "utility"])
def test_cfp55_missingness_cannot_become_numeric_default_or_eligibility(field):
    result = project(make_subject(("METHOD",), empty=True))
    assert result.dimensions[0].state == "UNRESOLVED"
    rejected("REPLAY_MISMATCH", validate, result.model_dump() | {field: 0})


def test_cfp56_no_title_mass_or_missing_dimension_inference():
    source = make_subject(("METHOD",), empty=True)
    recipe = source.feature_input.recipe
    assert recipe.ingredients[0].quantity.amount > 0
    row = project(source).dimensions[0]
    assert row.positive_term_ids == () and row.reason == "NO_SOURCE"
    assert len(project(source).dimensions) == 1
    rejected("REPLAY_MISMATCH", project, source.model_dump() | dict(infer_main_protein=True))


@pytest.mark.parametrize(
    "target", ["app.modules.preferences.contracts", "app.modules.learning.public"]
)
def test_cfp57_preference_strength_and_learning_dependencies_are_forbidden(target):
    checker = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]
    assert any("CANDIDATE_FEATURE_PURE_CORE" in e for e in checker(f"import {target}", CORE))


@pytest.mark.parametrize(
    "target",
    [
        "ortools",
        "app.modules.planning.ranking",
        "app.modules.planning.utility",
        "app.modules.learning.contracts",
    ],
)
def test_cfp58_no_novelty_repeat_or_candidate_scoring_dependency(target):
    checker = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]
    assert any("CANDIDATE_FEATURE_PURE_CORE" in e for e in checker(f"import {target}", CORE))


@pytest.mark.parametrize("flag", ["planner_ready", "activation_ready"])
def test_cfp59_authority_literals_cannot_be_promoted(flag):
    result = project(make_subject())
    rejected("REPLAY_MISMATCH", validate, result.model_dump() | {flag: True})
    assert result.source.grounded_candidate.shortlist_input_ready is True
    assert result.activation_ready is False and result.planner_ready is False


def test_cfp60_retained_baseline_contracts_files_and_no_new_persistence():
    pins = json.loads(
        (
            Path(__file__).parent / "fixtures/candidate_feature_projection_compatibility.json"
        ).read_text()
    )
    definitions = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
    assert len(pins["definitions"]) == 358 and len(definitions) == 503  # 480 +23 NRE.
    for name, digest in pins["definitions"].items():
        assert (
            hashlib.sha256(json.dumps(definitions[name], sort_keys=True).encode()).hexdigest()
            == digest
        ), name
    for name, pin in pins["append_only_files"].items():
        assert (
            hashlib.sha256((ROOT / name).read_bytes()[: pin["prefix_bytes"]]).hexdigest()
            == pin["sha256"]
        ), name
    for name, digest in pins["frozen_files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    assert sorted(
        p.name[:4]
        for p in (ROOT / "apps/backend/migrations/versions").glob("*.py")
        if p.name[:4].isdigit()
    ) == [f"{n:04}" for n in range(1, 18)]
    tree = ast.parse(
        (ROOT / "apps/backend/app/modules/planning/candidate_feature_projection.py").read_text()
    )
    assert not any(
        isinstance(n, ast.Import)
        and any(
            a.name in {"sqlalchemy", "datetime", "time", "os", "socket", "pathlib"} for a in n.names
        )
        for n in ast.walk(tree)
    )


def test_cfp60_all2978_baseline_test_identities_are_retained():
    baseline = json.loads(
        (
            Path(__file__).parent / "fixtures/candidate_feature_projection_baseline_tests.json"
        ).read_text(encoding="utf-8")
    )
    assert len(baseline) == 2978
    collection = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-o", "addopts="],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
    )
    current = [
        line.strip()
        for line in collection.stdout.splitlines()
        if line.startswith(("apps/", "benchmark/")) and "::" in line
    ]

    def normalize(node):
        return re.sub(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            "<uuid>",
            node,
        )

    assert not Counter(map(normalize, baseline)) - Counter(map(normalize, current))
