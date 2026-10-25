"""Reviewed classification from primitive facts, never inferred utility/safety/exposure."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest
from app.modules.planning import contracts as p
from app.modules.planning.feature_preview import (
    discover_culinary_feature_assignments as discover,
)
from app.modules.planning.feature_preview import (
    resolve_feature_terms as resolve,
)
from app.modules.recipes import contracts as r
from feature_fixtures import feature_subject, path_key, review_command
from test_architecture import check_source


@pytest.mark.parametrize("dimension", ["METHOD", "FLAVOR"])
@pytest.mark.parametrize("coverage", ["PARTIAL", "COMPLETE"])
@pytest.mark.parametrize("positives", [True, False])
def test_positive_coverage_and_absence_are_separate(dimension, coverage, positives):
    s, terms = feature_subject(dimension=dimension, coverage=coverage, positives=positives)
    d = discover(s)
    assert not d.activation_ready
    state = (
        "ASSIGNED" if positives else ("REVIEWED_NONE" if coverage == "COMPLETE" else "UNRESOLVED")
    )
    assert d.dimensions[0].state == state
    q = r.FeatureTermQuery(dimension=dimension, term_ids=tuple(t.id for t in terms))
    rows = {x.term_id: x for x in resolve(s, (q,)).terms}
    assert rows[terms[0].id].state == (
        "PRESENT" if positives else ("REVIEWED_ABSENT" if coverage == "COMPLETE" else "UNRESOLVED")
    )
    assert rows[terms[1].id].state == (
        "REVIEWED_ABSENT" if coverage == "COMPLETE" else "UNRESOLVED"
    )


def test_dimension_only_capture_and_query_independent_identity():
    s, terms = feature_subject()
    raw = s.request.model_dump()
    for forbidden in ["term_ids", "queries", "context_ref"]:
        with pytest.raises(ValueError):
            p.CulinaryFeatureCaptureRequest.model_validate(raw | {forbidden: ()})
    before = s.canonical_bytes()
    a = resolve(s, (r.FeatureTermQuery(dimension="METHOD", term_ids=(terms[0].id,)),))
    b = resolve(s, (r.FeatureTermQuery(dimension="METHOD", term_ids=(uuid4(),)),))
    assert a.subject.fingerprint == b.subject.fingerprint == s.fingerprint
    assert a.fingerprint != b.fingerprint and before == s.canonical_bytes()
    assert b.terms[0].reason == "TERM_NOT_CAPTURED"


def test_no_source_not_reviewed_none_or_inferred_method():
    s, _ = feature_subject(empty=True)
    assert discover(s).dimensions[0].reason == "NO_SOURCE"
    assert discover(s).dimensions[0].state == "UNRESOLVED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("tier_ids", (uuid4(),)),
        ("slots", ()),
        ("selected_rule_id", uuid4()),
        ("cooking_method", "roast"),
        ("candidate_fingerprint", "a" * 64),
        ("adjustment", "ZERO_ONLY"),
    ],
)
def test_method_has_no_variant_path(field, value):
    s, _ = feature_subject()
    with pytest.raises(ValueError):
        r.RecipeMethodContextKey.model_validate(
            s.evaluation.sources.scopes[0].key.model_dump() | {field: value}
        )


def test_method_invariant_across_valid_tier_rule_and_adjustment():
    s, _ = feature_subject()
    original = discover(s).dimensions
    recipe = s.evaluation.recipe
    for tier in recipe.portion_tiers:
        for selected in [(), (recipe.variant_rules[0].id,)]:
            # METHOD input may omit paths; if supplied for direct evaluation it must be authored.
            e = r.CulinaryFeatureEvaluationInput.model_validate(
                s.evaluation.model_dump()
                | dict(
                    path=r.FeatureSelectedPath(
                        tier_id=tier.id,
                        selected_rule_ids=selected,
                        deltas=tuple((i.id, 0) for i in recipe.ingredients),
                    )
                )
            )
            assert r.discover_feature_input(e) == original
    assert len(s.evaluation.sources.scopes[0].key.canonical_bytes().splitlines()) == 4


def test_unknown_or_wrong_kind_query_and_uncaptured_dimension():
    s, terms = feature_subject()
    with pytest.raises(ValueError, match="not captured"):
        resolve(s, (r.FeatureTermQuery(dimension="FLAVOR", term_ids=(terms[0].id,)),))
    # Cross-kind vocabulary cannot be smuggled into a reviewed universe.
    data = s.model_dump()
    data["evaluation"]["sources"]["terms"][0]["kind"] = "FLAVOR"
    with pytest.raises(ValueError):
        p.CapturedCulinaryFeatureSubjectDraft.model_validate(data)


@pytest.mark.parametrize("kind", ["discover", "resolve"])
def test_forged_outputs_and_constructed_input_not_trusted(kind):
    s, terms = feature_subject()
    result = (
        discover(s)
        if kind == "discover"
        else resolve(s, (r.FeatureTermQuery(dimension="METHOD", term_ids=(terms[0].id,)),))
    )
    with pytest.raises(ValueError):
        type(result).model_validate(result.model_dump() | {"fingerprint": "0" * 64})
    bad = s.model_copy(update={"request": s.request.model_copy(update={"proposal_hash": "0" * 64})})
    with pytest.raises(ValueError):
        discover(bad)


@pytest.mark.parametrize(
    "mutate",
    [
        "missing_term",
        "missing_review",
        "duplicate_scope",
        "bad_sequence",
        "future_time",
        "wrong_recipe",
        "missing_path",
        "extra_catalog_frontier",
        "wrong_cached_hash",
    ],
)
def test_forged_or_incomplete_source_manifest_rejected(mutate):
    s, _ = feature_subject(dimension="FLAVOR")
    d = deepcopy(s.model_dump())
    e = d["evaluation"]
    scopes = e["sources"]["scopes"]
    if mutate == "missing_term":
        e["sources"]["terms"] = ()
    if mutate == "missing_review":
        scopes[0]["reviews"] = ()
    if mutate == "duplicate_scope":
        e["sources"]["scopes"] += scopes
    if mutate == "bad_sequence":
        scopes[0]["reviews"][0]["source_sequence"] = 2
    if mutate == "future_time":
        e["captured_at"] = e["recipe"]["provenance"]["observed_at"]
    if mutate == "wrong_recipe":
        scopes[0]["key"]["recipe_version_id"] = uuid4()
    if mutate == "missing_path":
        e["path"] = None
    if mutate == "extra_catalog_frontier":
        e["sources"]["catalog_frontier"] = 0
    if mutate == "wrong_cached_hash":
        scopes[0]["reviews"][0]["command_hash"] = "0" * 64
    with pytest.raises(ValueError):
        p.CapturedCulinaryFeatureSubjectDraft.model_validate(d)


def test_canonical_unordered_sets_and_frozen_roundtrip():
    s, _ = feature_subject(dimension="FLAVOR")
    d = s.model_dump()
    e = d["evaluation"]
    e["sources"]["terms"] = e["sources"]["terms"][::-1]
    sc = e["sources"]["scopes"][0]
    sc["key"]["slots"] = sc["key"]["slots"][::-1]
    sc["reviews"][0]["command"]["key"]["slots"] = sc["reviews"][0]["command"]["key"]["slots"][::-1]
    sc["reviews"][0]["command"]["covered_term_ids"] = sc["reviews"][0]["command"][
        "covered_term_ids"
    ][::-1]
    again = p.CapturedCulinaryFeatureSubjectDraft.model_validate(d)
    assert again.fingerprint == s.fingerprint and again.canonical_bytes() == s.canonical_bytes()
    assert p.CapturedCulinaryFeatureSubjectDraft.model_validate_json(s.model_dump_json()) == s
    with pytest.raises((ValueError, FrozenInstanceError)):
        s.activation_ready = True


def test_path_key_not_candidate_hash_and_tier_scope_is_explicit():
    s, _ = feature_subject(dimension="FLAVOR")
    recipe = s.evaluation.recipe
    key = path_key(recipe)
    assert key.scope == "EXACT_PATH"
    with pytest.raises(ValueError):
        r.CulinaryFeaturePathKey.model_validate(key.model_dump() | dict(scope="REVIEWED_SCOPE"))
    with pytest.raises(ValueError):
        r.CulinaryFeaturePathKey.model_validate(key.model_dump() | dict(tier_ids=()))
    with pytest.raises(ValueError):
        r.validate_applicability(recipe, key.model_copy(update={"tier_ids": (uuid4(),)}))


def test_catalog_frontier_is_forbidden_on_method_flavor_commands():
    s, terms = feature_subject()
    q = review_command(s.evaluation.recipe, terms)
    with pytest.raises(ValueError):
        r.RecipeOnlyFeatureCommand.model_validate(
            q.model_dump() | dict(expected_catalog_frontier=0)
        )
    assert "expected_catalog_frontier" not in q.model_dump()


@pytest.mark.parametrize("number", [True, "1", -1, 2**63])
def test_frontier_strict_bounded(number):
    s, terms = feature_subject()
    with pytest.raises(ValueError):
        review_command(s.evaluation.recipe, terms, expected_recipe_frontier=number)


def test_raw_preference_evidence_strength_and_blocked_capabilities_unchanged():
    from app.modules.preferences.contracts import SetMemberPreferenceCommand

    assert "evidence_strength" not in SetMemberPreferenceCommand.model_fields
    s, _ = feature_subject()
    assert set(type(discover(s)).model_fields) == {
        "contract_version",
        "activation_ready",
        "subject",
        "dimensions",
        "fingerprint",
    }


def test_pure_module_boundary_negative_cases():
    for target in [
        "sqlalchemy",
        "psycopg",
        "ortools",
        "requests",
        "app.modules.preferences.public",
        "app.modules.execution.public",
    ]:
        assert check_source(f"import {target}", "app.modules.recipes.feature_resolution")


def test_frozen_definitions_hashes_schema_and_released_migrations():
    import ast
    import json
    from hashlib import sha256
    from pathlib import Path

    frozen = json.loads(Path(__file__).with_name("feature_compatibility.json").read_text())

    def digest(s):
        return sha256(s.encode()).hexdigest()

    for path, defs in frozen["definitions"].items():
        current = {
            n.name: digest(ast.dump(n, include_attributes=False))
            for n in ast.parse(Path(path).read_text(encoding="utf-8")).body
            if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert all(current.get(k) == v for k, v in defs.items()), path
    current = json.loads(Path("packages/contracts/domain.schema.json").read_text(encoding="utf-8"))[
        "$defs"
    ]
    assert len(frozen["schema_definitions"]) == 197
    for k, v in frozen["schema_definitions"].items():
        assert (
            digest(
                json.dumps(current[k], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            )
            == v
        ), k
    for path, v in frozen["released_migrations"].items():
        assert digest(Path(path).read_text(encoding="utf-8")) == v, path


@pytest.mark.parametrize("mode", ["tier", "delta", "rule"])
def test_path_scope_only_matches_its_explicit_authored_controls(mode):
    s, _ = feature_subject(dimension="FLAVOR")
    e = s.evaluation
    path = e.path.model_dump()
    if mode == "tier":
        path["tier_id"] = e.recipe.portion_tiers[1].id
    if mode == "delta":
        path["deltas"] = tuple(
            (i.id, 10 if n == 0 else 0) for n, i in enumerate(e.recipe.ingredients)
        )
    if mode == "rule":
        path["selected_rule_ids"] = (e.recipe.variant_rules[0].id,)
    changed = r.CulinaryFeatureEvaluationInput.model_validate(e.model_dump() | dict(path=path))
    d = r.discover_feature_input(changed)[0]
    assert d.state == "UNRESOLVED" and d.reason == "NO_MATCHING_SCOPE"


@pytest.mark.parametrize("mode", ["rule", "preparation", "count_rule", "multiple_structural"])
def test_impossible_scope_cannot_register_even_with_valid_identifiers(mode):
    s, _ = feature_subject(dimension="FLAVOR")
    recipe = s.evaluation.recipe
    key = path_key(recipe)
    slots = []
    for slot in key.slots:
        data = slot.model_dump()
        if slot.requirement_id == recipe.ingredients[0].id:
            if mode == "rule":
                data |= dict(choice="RULE", selected_rule_id=recipe.variant_rules[1].id)
            if mode == "preparation":
                data |= dict(transformation_id=recipe.transformations[1].id)
            if mode == "multiple_structural":
                data |= dict(
                    choice="RULE",
                    selected_rule_id=recipe.variant_rules[0].id,
                    transformation_id=recipe.transformations[1].id,
                )
        if mode == "count_rule" and slot.requirement_id == recipe.ingredients[3].id:
            data |= dict(choice="RULE", selected_rule_id=recipe.variant_rules[0].id)
        if mode == "multiple_structural" and slot.requirement_id == recipe.ingredients[1].id:
            data |= dict(choice="RULE", selected_rule_id=recipe.variant_rules[1].id)
        slots.append(r.FeatureSlotApplicability(**data))
    invalid = r.CulinaryFeaturePathKey.model_validate(key.model_dump() | dict(slots=tuple(slots)))
    with pytest.raises(ValueError, match="Impossible|structural"):
        r.validate_applicability(recipe, invalid)


def test_approved_exact_structural_combination_can_support_scope():
    s, _ = feature_subject(dimension="FLAVOR")
    recipe = s.evaluation.recipe
    data = recipe.model_dump()
    data["approved_combinations"] = (
        dict(
            id=uuid4(),
            recipe_version_id=recipe.id,
            key="explicit.combo",
            rule_ids=tuple(x.id for x in recipe.variant_rules),
            provenance=recipe.provenance.model_dump(),
        ),
    )
    recipe = r.RecipeVersionSnapshot.model_validate(data)
    key = path_key(recipe)
    slots = []
    for slot in key.slots:
        rule = next(
            (x for x in recipe.variant_rules if x.requirement_id == slot.requirement_id), None
        )
        changes = {}
        if rule:
            t = next(
                (
                    t
                    for t in recipe.transformations
                    if t.ingredient_id == rule.replacement_ingredient_id
                    and t.requirement_id == slot.requirement_id
                ),
                None,
            )
            changes = dict(
                choice="RULE",
                selected_rule_id=rule.id,
                preparation="TRANSFORMATION" if t else "NONE",
                transformation_id=t.id if t else None,
            )
        slots.append(slot.model_copy(update=changes))
    valid = r.CulinaryFeaturePathKey.model_validate(key.model_dump() | dict(slots=tuple(slots)))
    r.validate_applicability(recipe, valid)


def test_float_and_unversioned_retraction_are_rejected():
    from app.domain.feature_identity import canonical_bytes

    with pytest.raises(ValueError, match="Float"):
        canonical_bytes({"factor": 0.5})
    s, terms = feature_subject()
    q = s.evaluation.sources.scopes[0].reviews[0].command
    with pytest.raises(ValueError, match="version mismatch"):
        type(q).model_validate(q.model_dump() | dict(command_kind="RETRACT"))


def test_duplicate_review_identity_cannot_reappear_under_new_revision():
    s, _ = feature_subject()
    scope = s.evaluation.sources.scopes[0]
    old = scope.reviews[0]
    q = r.RecipeOnlyFeatureCommand.model_validate(
        old.command.model_dump()
        | dict(
            contract_version="culinary-feature-write.v1",
            command_kind="REPLACE",
            applicability_id=scope.id,
            key=None,
            expected_revision_no=0,
            predecessor_id=old.id,
            expected_recipe_frontier=1,
            correction_reason="Explicit correction",
            idempotency_key=uuid4().hex,
        )
    )
    new = r.CulinaryFeatureReviewFact(
        id=old.id,
        applicability_id=scope.id,
        recipe_version_id=q.recipe_version_id,
        dimension="METHOD",
        revision_no=1,
        predecessor_revision_no=0,
        source_sequence=2,
        reviewer_user_id=old.reviewer_user_id,
        recorded_at=old.recorded_at,
        command=q,
        command_hash=q.fingerprint(old.reviewer_user_id),
    )
    with pytest.raises(ValueError, match="Duplicate"):
        r.CulinaryFeatureScopeFact(id=scope.id, key=scope.key, reviews=(old, new))
