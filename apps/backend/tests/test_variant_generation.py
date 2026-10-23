"""INV-005/006: demand selects authored possibilities; generation never invents them."""

import ast
from decimal import Decimal, localcontext
from pathlib import Path
from uuid import uuid4

import pytest
from app.modules.planning.culinary import bind_generated_candidate
from app.modules.recipes import generation
from app.modules.recipes.contracts import (
    CulinaryCandidateDraft,
    RecipeVersionSnapshot,
    VariantGenerationRequest,
    VariantGenerationResult,
)
from app.modules.validation.recipe_grounding import validate_recipe_grounding
from culinary_fixtures import culinary_source
from recipe_fixtures import provenance, recipe_data, snapshot


def request(recipe=None, *, limits=None, **demand):
    return VariantGenerationRequest(
        recipe=recipe or snapshot(),
        demand=demand,
        limits=limits or dict(max_attempts=128, max_candidates=64),
    )


def selected(result, rules=()):
    return next(c for c in result.candidates if set(c.selected_rule_ids) == set(rules))


def combo_data():
    d = recipe_data()
    d["approved_combinations"] = [
        dict(
            id=uuid4(),
            recipe_version_id=d["id"],
            key="approved-pair",
            rule_ids=[r["id"] for r in d["variant_rules"]],
            provenance=provenance(),
        )
    ]
    return d


def owner(source):
    b = source.proposal.graph.culinary_bindings[0]
    return dict(
        household_id=b.household_id,
        plan_id=b.plan_id,
        proposal_id=b.proposal_id,
        batch_node_id=b.batch_node_id,
        provenance=b.provenance,
    )


def source_with_binding(source, binding):
    g = source.proposal.graph
    batch = g.batches[0].model_copy(
        update=dict(
            recipe_version_id=binding.recipe_version_id,
            tier_id=binding.tier_id,
            planned_servings=binding.planned_servings,
            culinary_signature=binding.semantic_fingerprint(),
        )
    )
    g = g.model_copy(update=dict(culinary_bindings=(binding,), batches=(batch,)))
    return source.model_copy(
        update=dict(
            proposal=source.proposal.model_copy(
                update=dict(
                    graph=g,
                    graph_hash=g.fingerprint(),
                )
            )
        )
    )


def test_default_is_only_default_not_all_authored_rules():
    r = snapshot()
    out = generation.generate_variants(request(r))
    assert out.status == "COMPLETE" and out.attempts == len(out.candidates) == 1
    c = out.candidates[0]
    assert c.selected_rule_ids == () and c.serving_count == r.base_servings
    assert c.status == "DRAFT" and c.activation_ready is False
    assert c.provenance == r.provenance
    assert all(i.adjustment_delta == 0 for i in c.resolved_ingredients)
    assert VariantGenerationResult.model_validate_json(out.model_dump_json()) == out
    with pytest.raises(ValueError):
        c.serving_count = 7


def test_target_ingredient_only_activates_contextual_authored_rules():
    r = snapshot()
    out = generation.generate_variants(
        request(
            r,
            ingredient_targets=(r.variant_rules[0].replacement_ingredient_id, uuid4()),
        )
    )
    assert {c.selected_rule_ids for c in out.candidates} == {(), (r.variant_rules[0].id,)}
    c = selected(out, (r.variant_rules[0].id,))
    assert c.triggers == ("INGREDIENT_TARGET",)
    row = next(i for i in c.resolved_ingredients if i.requirement_id == r.ingredients[0].id)
    assert row.ingredient_id == r.variant_rules[0].replacement_ingredient_id
    assert row.quantity.amount == Decimal("220") and row.quantity.basis == "EP_RAW_G"


def test_unknown_target_does_not_invent_equivalence():
    assert len(generation.generate_variants(request(ingredient_targets=(uuid4(),))).candidates) == 1


def test_unapproved_structural_pair_never_generated_or_accepted():
    r = snapshot()
    pair = tuple(t.id for t in r.variant_rules)
    out = generation.generate_variants(
        request(
            r,
            ingredient_targets=tuple(t.replacement_ingredient_id for t in r.variant_rules),
            rule_selections=[dict(rule_ids=pair)],
        )
    )
    assert len(out.candidates) == 3
    assert all(len(c.selected_rule_ids) <= 1 for c in out.candidates)
    assert [e.code for e in out.rejections] == ["UNAUTHORIZED_SELECTION"]


def test_exact_approved_combination_generated_for_target_context():
    r = RecipeVersionSnapshot.model_validate(combo_data())
    out = generation.generate_variants(
        request(
            r,
            ingredient_targets=tuple(t.replacement_ingredient_id for t in r.variant_rules),
        )
    )
    assert len(out.candidates) == 4
    c = selected(out, tuple(t.id for t in r.variant_rules))
    s = culinary_source(r)
    b = bind_generated_candidate(candidate=c, recipe=r, **owner(s))
    assert b.approved_combination_id == r.approved_combinations[0].id
    report = validate_recipe_grounding(source_with_binding(s, b))
    assert report.culinary_checks_passed and report.activation_authorized is False


def test_approved_pair_cannot_append_nonstructural_rule_without_exact_approval():
    d = combo_data()
    d["variant_rules"].append(
        dict(
            id=uuid4(),
            recipe_version_id=d["id"],
            key="extra-spice",
            version=1,
            requirement_id=d["ingredients"][2]["id"],
            replacement_ingredient_id=uuid4(),
            quantity_factor="1",
            structural=False,
            provenance=provenance(),
        )
    )
    r = RecipeVersionSnapshot.model_validate(d)
    out = generation.generate_variants(
        request(
            r,
            rule_selections=[dict(rule_ids=[t.id for t in r.variant_rules])],
        )
    )
    assert len(out.candidates) == 1 and out.rejections[0].code == "UNAUTHORIZED_SELECTION"


def test_nonstructural_pair_is_explicit_not_cartesian():
    d = recipe_data()
    for rule in d["variant_rules"]:
        rule["structural"] = False
    r = RecipeVersionSnapshot.model_validate(d)
    targets = tuple(t.replacement_ingredient_id for t in r.variant_rules)
    assert len(generation.generate_variants(request(r, ingredient_targets=targets)).candidates) == 3
    pair = [t.id for t in r.variant_rules]
    out = generation.generate_variants(request(r, rule_selections=[dict(rule_ids=pair)]))
    assert len(out.candidates) == 2 and selected(out, pair)


@pytest.mark.parametrize("duplicate", [True, False])
def test_same_slot_or_repeated_rule_rejected(duplicate):
    d = recipe_data()
    first = d["variant_rules"][0]
    if not duplicate:
        d["variant_rules"].append(first | dict(id=uuid4(), key="alternative-same-slot"))
    r = RecipeVersionSnapshot.model_validate(d)
    ids = [r.variant_rules[0].id, r.variant_rules[0 if duplicate else -1].id]
    out = generation.generate_variants(request(r, rule_selections=[dict(rule_ids=ids)]))
    assert len(out.candidates) == 1 and out.rejections[0].code == "UNAUTHORIZED_SELECTION"


def test_dedup_merges_triggers_but_preserves_distinct_rule_provenance():
    d = recipe_data()
    rule = d["variant_rules"][0]
    d["variant_rules"].append(rule | dict(id=uuid4(), key="another-authorized-path"))
    r = RecipeVersionSnapshot.model_validate(d)
    out = generation.generate_variants(
        request(
            r,
            ingredient_targets=[rule["replacement_ingredient_id"]] * 2,
            rule_selections=[dict(rule_ids=[rule["id"]])] * 2,
        )
    )
    assert len(out.candidates) == 3
    assert selected(out, (rule["id"],)).triggers == ("AUTHORED_SELECTION", "INGREDIENT_TARGET")
    assert len({c.fingerprint for c in out.candidates}) == 3


@pytest.mark.parametrize("bad", ["tier", "rule"])
def test_unknown_tier_or_rule_fails_demand_closed(bad):
    out = generation.generate_variants(
        request(
            **(
                dict(serving_counts=[3])
                if bad == "tier"
                else dict(rule_selections=[dict(rule_ids=[uuid4()])])
            )
        )
    )
    assert out.status == "INVALID_DEMAND" and out.candidates == () and out.attempts == 0


def test_all_explicit_tiers_keep_authored_nonlinear_fixed_discrete_to_taste_quantities():
    r = snapshot()
    out = generation.generate_variants(request(r, serving_counts=[4, 2]))
    assert len(out.candidates) == 2
    for c in out.candidates:
        tier = next(t for t in r.portion_tiers if t.id == c.tier_id)
        assert {q.requirement_id: q.quantity.amount for q in c.resolved_ingredients} == {
            q.requirement_id: q.amount for q in tier.quantities
        }
        assert c.serving_count == tier.servings
        count = next(q for q in c.resolved_ingredients if q.quantity.basis == "COUNT")
        assert count.quantity.item_ref == "garnish.egg"


def test_count_targeted_substitution_rejected_even_from_untrusted_model_copy():
    r = snapshot()
    bad = r.variant_rules[0].model_copy(update=dict(requirement_id=r.ingredients[3].id))
    r = r.model_copy(update=dict(variant_rules=(bad,)))
    q = request().model_copy(update=dict(recipe=r))
    with pytest.raises(ValueError, match="COUNT"):
        generation.generate_variants(q)


@pytest.mark.parametrize("path", ["substitute_only", "base_only", "neither"])
def test_transformation_path_semantics(path):
    d = recipe_data()
    if path == "substitute_only":
        d["transformations"] = d["transformations"][1:]
    elif path == "base_only":
        d["transformations"] = d["transformations"][:1]
    else:
        d["transformations"] = []
    r = RecipeVersionSnapshot.model_validate(d)
    out = generation.generate_variants(
        request(
            r,
            ingredient_targets=[r.variant_rules[0].replacement_ingredient_id],
        )
    )
    assert len(out.candidates) == (1 if path == "base_only" else 2)
    if path == "substitute_only":
        assert selected(out).transformations == ()
        assert len(selected(out, (r.variant_rules[0].id,)).transformations) == 1
    if path == "neither":
        assert all(not c.transformations for c in out.candidates)
    if path == "base_only":
        assert out.rejections[0].code == "UNRESOLVABLE_PATH"


def test_exclusion_filters_resolved_ingredients_but_cannot_prove_global_infeasibility():
    r = snapshot()
    out = generation.generate_variants(
        request(r, excluded_ingredient_ids=[r.ingredients[0].ingredient_id])
    )
    assert out.status == "NO_CANDIDATES" and out.candidates == ()
    out = generation.generate_variants(
        request(
            r,
            excluded_ingredient_ids=[r.ingredients[0].ingredient_id],
            ingredient_targets=[r.variant_rules[0].replacement_ingredient_id],
        )
    )
    assert len(out.candidates) == 1 and out.candidates[0].selected_rule_ids


@pytest.mark.parametrize("limit", ["max_attempts", "max_candidates"])
def test_explosion_limit_returns_no_arbitrary_shortlist(limit):
    r = snapshot()
    limits = dict(max_attempts=128, max_candidates=64) | {limit: 1}
    out = generation.generate_variants(
        request(
            r,
            limits=limits,
            ingredient_targets=[t.replacement_ingredient_id for t in r.variant_rules],
        )
    )
    assert out.status == "LIMIT_EXCEEDED" and not out.candidates
    assert out.rejections[-1].code == "LIMIT_EXCEEDED"


def test_limit_applies_to_tier_cross_selection_and_deduplicates_first():
    r = snapshot()
    selection = dict(rule_ids=[r.variant_rules[0].id])
    out = generation.generate_variants(
        request(
            r,
            serving_counts=[2, 4],
            rule_selections=[selection] * 5,
            limits=dict(max_attempts=4, max_candidates=4),
        )
    )
    assert out.attempts == len(out.candidates) == 4


def test_unordered_source_and_demand_have_identical_result_under_decimal_context_change():
    d = combo_data()
    r = RecipeVersionSnapshot.model_validate(d)
    q = request(
        r,
        serving_counts=[2, 4],
        ingredient_targets=[t.replacement_ingredient_id for t in r.variant_rules],
    )
    first = generation.generate_variants(q)
    for name in (
        "ingredients",
        "portion_tiers",
        "variant_rules",
        "approved_combinations",
        "transformations",
    ):
        d[name].reverse()
    for tier in d["portion_tiers"]:
        tier["quantities"].reverse()
    for combo in d["approved_combinations"]:
        combo["rule_ids"].reverse()
    d["base_servings"] = "2.000000"
    with localcontext() as ctx:
        ctx.prec = 3
        second = generation.generate_variants(
            request(
                RecipeVersionSnapshot.model_validate(d),
                serving_counts=["4.00", "2.000", 2],
                ingredient_targets=tuple(reversed(q.demand.ingredient_targets)),
            )
        )
    assert second == first
    assert first.model_dump_json() == second.model_dump_json()


@pytest.mark.parametrize("change", ["procedure", "provenance", "factor"])
def test_source_primitive_change_changes_candidate_identity(change):
    d = recipe_data()
    before = generation.generate_variants(request(RecipeVersionSnapshot.model_validate(d)))
    if change == "procedure":
        d["procedure"] += "\nAn authored second step."
    elif change == "provenance":
        d["provenance"]["source_version"] = "2"
    else:
        d["transformations"][0]["factor"] = "0.7"
    after = generation.generate_variants(request(RecipeVersionSnapshot.model_validate(d)))
    assert before.recipe_source_hash != after.recipe_source_hash
    assert before.candidates[0].fingerprint != after.candidates[0].fingerprint


def test_candidate_identity_excludes_request_triggers_limits_and_other_demand():
    r = snapshot()
    a = generation.generate_variants(request(r))
    b = generation.generate_variants(request(r, ingredient_targets=[uuid4()]))
    assert a.request_hash != b.request_hash
    assert a.candidates[0].fingerprint == b.candidates[0].fingerprint


@pytest.mark.parametrize("bad", ["float", "nan", "draft", "version", "delta", "reason", "limit"])
def test_contract_rejects_untruthful_or_inexact_inputs(bad):
    q = request().model_dump()
    if bad in {"float", "nan"}:
        q["demand"]["serving_counts"] = [2.5 if bad == "float" else "NaN"]
    elif bad == "draft":
        q["recipe"]["review_status"] = "DRAFT"
    elif bad == "version":
        q["contract_version"] = "culinary-generation-request.v99"
    elif bad == "limit":
        q["limits"]["max_attempts"] = True
    else:
        q["demand"]["adjustment_deltas" if bad == "delta" else "variant_reason"] = {"x": 1}
    with pytest.raises(ValueError):
        VariantGenerationRequest.model_validate(q)


@pytest.mark.parametrize("mutation", ["ingredient", "quantity", "source", "tier", "fingerprint"])
def test_forged_candidate_rejected_even_with_recomputed_fingerprint(mutation):
    r = snapshot()
    c = generation.generate_variants(request(r)).candidates[0]
    data = c.model_dump()
    if mutation == "ingredient":
        data["resolved_ingredients"][0]["ingredient_id"] = uuid4()
    elif mutation == "quantity":
        data["resolved_ingredients"][0]["quantity"]["amount"] += 1
    elif mutation == "source":
        data["recipe_source_hash"] = "f" * 64
    elif mutation == "tier":
        data["tier_id"] = uuid4()
    forged = CulinaryCandidateDraft.model_construct(**data)
    if mutation != "fingerprint":
        # Use parsed nested values before rehashing, without validating the old fingerprint.
        parsed = c.model_copy(
            update={
                "resolved_ingredients": tuple(
                    type(c.resolved_ingredients[0]).model_validate(i)
                    for i in data["resolved_ingredients"]
                ),
                "recipe_source_hash": data["recipe_source_hash"],
                "tier_id": data["tier_id"],
            }
        )
        forged = parsed.model_copy(update=dict(fingerprint=parsed.expected_fingerprint()))
    else:
        forged = c.model_copy(update=dict(fingerprint="f" * 64))
    with pytest.raises(ValueError):
        bind_generated_candidate(candidate=forged, recipe=r, **owner(culinary_source(r)))


def test_independent_validator_catches_self_consistent_forged_selected_binding(monkeypatch):
    r = snapshot()
    c = generation.generate_variants(request(r)).candidates[0]
    s = culinary_source(r)
    b = bind_generated_candidate(candidate=c, recipe=r, **owner(s))
    rows = list(b.requirements)
    rows[0] = rows[0].model_copy(update=dict(ingredient_id=uuid4()))
    b = b.model_copy(update=dict(requirements=tuple(rows)))
    b = b.model_copy(update=dict(fingerprint=b.expected_fingerprint()))
    s = source_with_binding(s, b)

    def forbidden(*a, **kw):
        raise AssertionError("Validator called generator/producer")

    monkeypatch.setattr(generation, "generate_variants", forbidden)
    monkeypatch.setattr(generation, "resolve_culinary_binding", forbidden)
    report = validate_recipe_grounding(s)
    assert not report.culinary_checks_passed and not report.activation_authorized
    assert any(f.code == "CULINARY_RESOLUTION" for f in report.findings)


def test_generator_does_not_swallow_programmer_error(monkeypatch):
    def broken(*a, **kw):
        raise RuntimeError("producer defect")

    monkeypatch.setattr(generation, "resolve_culinary_binding", broken)
    with pytest.raises(RuntimeError, match="producer defect"):
        generation.generate_variants(request())


def test_generator_runtime_has_no_db_clock_random_solver_or_downstream_imports():
    tree = ast.parse(Path(generation.__file__).read_text(encoding="utf-8"))
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imports += [i.name for n in ast.walk(tree) if isinstance(n, ast.Import) for i in n.names]
    assert set(imports) == {"json", "hashlib", "app.modules.recipes.contracts"}


def test_generator_does_not_modify_source_request():
    q = request()
    before = q.model_dump_json()
    assert generation.generate_variants(q) == generation.generate_variants(q)
    assert q.model_dump_json() == before


@pytest.mark.parametrize(
    "target",
    [
        "app.modules.recipes.generation",
        "app.modules.recipes.public",
        "app.modules.planning.culinary",
    ],
)
def test_validator_cannot_import_candidate_producer(target):
    import runpy

    root = Path(__file__).resolve().parents[3]
    check = runpy.run_path(str(root / "tools/check_import_boundaries.py"))["check_source"]
    assert check(f"import {target}", "app.modules.validation.recipe_grounding")


def test_duplicate_approved_sets_have_deterministic_binding_combo_identity():
    d = combo_data()
    d["approved_combinations"].append(
        d["approved_combinations"][0]
        | dict(
            id=uuid4(),
            key="same-authorization-second-source",
            provenance=provenance(),
        )
    )
    r = RecipeVersionSnapshot.model_validate(d)
    targets = tuple(t.replacement_ingredient_id for t in r.variant_rules)
    c = selected(
        generation.generate_variants(request(r, ingredient_targets=targets)),
        tuple(t.id for t in r.variant_rules),
    )
    s = culinary_source(r)
    b = bind_generated_candidate(candidate=c, recipe=r, **owner(s))
    flipped = r.model_copy(update=dict(approved_combinations=r.approved_combinations[::-1]))
    assert b == bind_generated_candidate(candidate=c, recipe=flipped, **owner(s))
    assert b.approved_combination_id == min((x.id for x in r.approved_combinations), key=str)


def test_adjustment_envelopes_are_retained_but_generator_never_samples_them():
    r = snapshot()
    out = generation.generate_variants(request(r, serving_counts=(2, 4)))
    assert r.ingredients[0].adjustment.max_delta == 60
    assert len(out.candidates) == 2
    assert all(i.adjustment_delta == 0 for c in out.candidates for i in c.resolved_ingredients)


def test_many_authored_alternatives_expand_linearly_without_cartesian_product():
    d = recipe_data()
    templates = list(d["variant_rules"])
    d["variant_rules"] = [
        templates[n % 2]
        | dict(
            id=uuid4(),
            key=f"authored-path-{n}",
            replacement_ingredient_id=uuid4(),
            provenance=provenance(),
        )
        for n in range(24)
    ]
    d["transformations"] = []
    r = RecipeVersionSnapshot.model_validate(d)
    out = generation.generate_variants(
        request(
            r,
            ingredient_targets=[t.replacement_ingredient_id for t in r.variant_rules],
            limits=dict(max_attempts=25, max_candidates=25),
        )
    )
    assert out.status == "COMPLETE" and len(out.candidates) == out.attempts == 25
    assert all(len(c.selected_rule_ids) <= 1 for c in out.candidates)
