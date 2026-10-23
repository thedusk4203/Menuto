"""Named MTR-019A adversarial matrix: independent enforcement, not producer mirroring."""

from decimal import Decimal
from uuid import uuid4

import pytest
from app.domain.units import CalculatedQuantity
from app.modules.planning.contracts import BoundPlanIntentGraph, PlannedCulinaryBinding
from app.modules.recipes.contracts import RecipeVersionSnapshot
from app.modules.validation.contracts import CulinaryValidationInput
from app.modules.validation.recipe_grounding import validate_recipe_grounding
from culinary_fixtures import altered, culinary_source
from recipe_fixtures import recipe_data
from test_architecture import check_source


def check(s):
    return validate_recipe_grounding(s)


def row_change(s, index=0, **kw):
    rows = list(s.proposal.graph.culinary_bindings[0].requirements)
    rows[index] = rows[index].model_copy(update=kw)
    return altered(s, requirements=tuple(rows))


def test_exact_default_roundtrip_determinism_and_immutability():
    s = culinary_source()
    assert check(s).culinary_checks_passed
    assert not check(s).activation_authorized
    assert check(s) == check(s)
    again = CulinaryValidationInput.model_validate_json(s.model_dump_json())
    assert again == s and again.fingerprint == s.fingerprint
    with pytest.raises(ValueError):
        s.activation_ready = True


def test_valid_single_authored_substitution():
    r = RecipeVersionSnapshot.model_validate(recipe_data())
    s = culinary_source(r, selected=(r.variant_rules[0].id,))
    assert check(s).culinary_checks_passed


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_rule",
        "wrong_slot_rule",
        "duplicate_rule",
        "wrong_ingredient",
        "wrong_basis",
        "wrong_item_ref",
        "below_min",
        "above_max",
        "amount",
        "wrong_transform",
        "missing_transform",
        "duplicate_requirement",
        "missing_requirement",
    ],
)
def test_requirement_mutation_matrix(mutation):
    s = culinary_source()
    row = s.proposal.graph.culinary_bindings[0].requirements[0]
    rule = s.recipes[0].variant_rules[0]
    if mutation == "unknown_rule":
        s = row_change(s, selected_rule_id=uuid4())
    if mutation == "wrong_slot_rule":
        s = row_change(s, index=1, selected_rule_id=rule.id)
    if mutation == "duplicate_rule":
        s = row_change(s, selected_rule_id=rule.id)
        s = row_change(s, index=1, selected_rule_id=rule.id)
    if mutation == "wrong_ingredient":
        s = row_change(s, ingredient_id=uuid4())
    if mutation == "wrong_basis":
        s = row_change(s, quantity=CalculatedQuantity(amount=200, basis="COOKED_G"))
    if mutation == "wrong_item_ref":
        s = row_change(
            s, index=3, quantity=CalculatedQuantity(amount=1, basis="COUNT", item_ref="wrong.egg")
        )
    if mutation == "below_min":
        s = row_change(s, adjustment_delta=Decimal(-21))
    if mutation == "above_max":
        s = row_change(s, adjustment_delta=Decimal(61))
    if mutation == "amount":
        s = row_change(s, quantity=CalculatedQuantity(amount=201, basis="EP_RAW_G"))
    if mutation == "wrong_transform":
        s = row_change(s, transformation_id=uuid4())
    if mutation == "missing_transform":
        s = row_change(s, transformation_id=None)
    rows = s.proposal.graph.culinary_bindings[0].requirements
    if mutation == "duplicate_requirement":
        s = altered(s, requirements=(*rows, row))
    if mutation == "missing_requirement":
        s = altered(s, requirements=rows[1:])
    assert not check(s).culinary_checks_passed


@pytest.mark.parametrize(
    "field",
    [
        "household_id",
        "plan_id",
        "proposal_id",
        "batch_node_id",
        "recipe_version_id",
        "tier_id",
        "planned_servings",
        "fingerprint",
    ],
)
def test_binding_owner_tier_serving_fingerprint_mutations(field):
    s = culinary_source()
    value = (
        "a" * 64
        if field == "fingerprint"
        else Decimal(3)
        if field == "planned_servings"
        else uuid4()
    )
    assert not check(altered(s, **{field: value})).culinary_checks_passed


def test_micro_adjustment_preserves_explicit_servings():
    r = RecipeVersionSnapshot.model_validate(recipe_data())
    deltas = {i.id: 60 if n == 0 else 0 for n, i in enumerate(r.ingredients)}
    s = culinary_source(r, deltas=deltas)
    assert check(s).culinary_checks_passed
    assert s.proposal.graph.culinary_bindings[0].planned_servings == 2


def test_wrong_version_rule_and_count_substitution_fail_independently():
    s = culinary_source()
    foreign = s.recipes[0].variant_rules[0].model_copy(update={"recipe_version_id": uuid4()})
    v = s.recipes[0].model_copy(update={"variant_rules": (foreign,)})
    assert not check(
        row_change(s.model_copy(update={"recipes": (v,)}), selected_rule_id=foreign.id)
    ).culinary_checks_passed
    count = s.recipes[0].ingredients[3]
    count_rule = foreign.model_copy(
        update={"recipe_version_id": s.recipes[0].id, "requirement_id": count.id}
    )
    v = s.recipes[0].model_copy(update={"variant_rules": (count_rule,)})
    assert not check(
        row_change(s.model_copy(update={"recipes": (v,)}), index=3, selected_rule_id=count_rule.id)
    ).culinary_checks_passed


def test_structural_combination_exact_approval():
    d = recipe_data()
    extra = dict(
        d["variant_rules"][0],
        id=uuid4(),
        key="second",
        requirement_id=d["ingredients"][1]["id"],
        replacement_ingredient_id=uuid4(),
    )
    d["variant_rules"] = [d["variant_rules"][0], extra]
    ids = tuple(r["id"] for r in d["variant_rules"])
    from recipe_fixtures import provenance

    d["approved_combinations"] = [
        dict(
            id=uuid4(), recipe_version_id=d["id"], key="both", rule_ids=ids, provenance=provenance()
        )
    ]
    r = RecipeVersionSnapshot.model_validate(d)
    s = culinary_source(r, selected=ids)
    assert check(s).culinary_checks_passed
    assert not check(altered(s, approved_combination_id=None)).culinary_checks_passed
    assert not check(altered(s, approved_combination_id=uuid4())).culinary_checks_passed


def test_raw_base_when_only_substitute_has_preparation_path():
    d = recipe_data()
    d["transformations"] = [
        t
        for t in d["transformations"]
        if t["ingredient_id"] == d["variant_rules"][0]["replacement_ingredient_id"]
    ]
    r = RecipeVersionSnapshot.model_validate(d)
    assert check(culinary_source(r)).culinary_checks_passed
    assert check(culinary_source(r, selected=(r.variant_rules[0].id,))).culinary_checks_passed


def test_discrete_step_rejected_and_scaling_recomputed():
    d = recipe_data()
    d["ingredients"][0]["adjustment"] = dict(kind="DISCRETE", min_delta=-20, max_delta=60, step=2)
    s = culinary_source(RecipeVersionSnapshot.model_validate(d))
    assert not check(row_change(s, adjustment_delta=Decimal(1))).culinary_checks_passed
    v = s.recipes[0]
    tier = v.portion_tiers[-1]
    points = list(tier.quantities)
    points[0] = points[0].model_copy(update={"amount": Decimal(999)})
    altered_tier = tier.model_copy(update={"quantities": tuple(points)})
    v = v.model_copy(update={"portion_tiers": (*v.portion_tiers[:-1], altered_tier)})
    assert not check(s.model_copy(update={"recipes": (v,)})).culinary_checks_passed


def test_forged_producer_output_caught_without_using_producer(monkeypatch):
    s = culinary_source()
    import app.modules.recipes.contracts as recipe_contracts

    forged = row_change(s, ingredient_id=uuid4())
    b = forged.proposal.graph.culinary_bindings[0]
    b = b.model_copy(update={"fingerprint": b.expected_fingerprint()})
    g = forged.proposal.graph.model_copy(
        update={
            "culinary_bindings": (b,),
            "batches": (
                forged.proposal.graph.batches[0].model_copy(
                    update={"culinary_signature": b.semantic_fingerprint()}
                ),
            ),
        }
    )
    forged = forged.model_copy(
        update={
            "proposal": forged.proposal.model_copy(
                update={"graph": g, "graph_hash": g.fingerprint()}
            )
        }
    )

    def forbidden(*a, **kw):
        raise AssertionError("Producer enforcement called")

    monkeypatch.setattr(recipe_contracts, "resolve_culinary_binding", forbidden)
    monkeypatch.setattr(PlannedCulinaryBinding, "expected_fingerprint", forbidden)
    assert check(s).culinary_checks_passed
    result = check(forged)
    assert not result.culinary_checks_passed
    codes = {f.code for f in result.findings}
    assert "CULINARY_RESOLUTION" in codes
    assert not codes & {"CULINARY_FINGERPRINT", "CULINARY_SIGNATURE"}


def test_binding_copy_keeps_semantic_signature_but_changes_proposal_hash():
    s = culinary_source()
    b = s.proposal.graph.culinary_bindings[0]
    copy = b.model_copy(update={"proposal_id": uuid4()})
    assert copy.semantic_fingerprint() == b.semantic_fingerprint()
    assert copy.expected_fingerprint() != b.fingerprint
    data = s.proposal.graph.model_dump() | {
        "culinary_bindings": (copy.model_copy(update={"fingerprint": copy.expected_fingerprint()}),)
    }
    assert BoundPlanIntentGraph.model_validate(data).fingerprint() != s.proposal.graph.fingerprint()


def test_postfact_is_diagnostic_and_does_not_repair():
    s = row_change(culinary_source(), ingredient_id=uuid4())
    before = s.model_dump_json()
    r = validate_recipe_grounding(s, phase="POSTFACT_VALIDATION")
    assert r.findings and not r.activation_authorized
    assert before == s.model_dump_json()


def test_unreviewed_binding_provenance_is_not_accepted():
    s = culinary_source()
    b = s.proposal.graph.culinary_bindings[0]
    assert not check(
        altered(s, provenance=b.provenance.model_copy(update={"kind": "IMPORTED_DRAFT"}))
    ).culinary_checks_passed


def test_v3_request_retry_does_not_depend_on_requirement_tuple_order():
    from app.modules.execution.public import fingerprint
    from app.modules.planning.contracts import ProposeBoundPlanCommand

    s = culinary_source()
    b = s.proposal.graph.culinary_bindings[0]
    g = s.proposal.graph.model_copy(
        update={
            "culinary_bindings": (
                b.model_copy(update={"requirements": tuple(reversed(b.requirements))}),
            )
        }
    )
    cmd = ProposeBoundPlanCommand(
        proposal_id=s.proposal.id,
        graph=s.proposal.graph,
        expected_generation=-1,
        scope=s.proposal.scope,
        effective_from=s.proposal.effective_from,
        actor_user_id=s.proposal.actor_user_id,
        source_system="manual",
        idempotency_key="same.retry",
        reason="Exact request",
    )
    assert fingerprint(cmd) == fingerprint(cmd.model_copy(update={"graph": g}))


@pytest.mark.parametrize("scope", ["input", "binding", "graph"])
def test_unknown_contract_versions_fail_closed(scope):
    s = culinary_source()
    if scope == "input":
        s = s.model_copy(update={"contract_version": "future.unknown"})
    if scope == "binding":
        s = altered(s, contract_version="future.unknown")
    if scope == "graph":
        s = s.model_copy(
            update={
                "proposal": s.proposal.model_copy(
                    update={
                        "graph": s.proposal.graph.model_copy(
                            update={"contract_version": "future.unknown"}
                        )
                    }
                )
            }
        )
    assert not check(s).culinary_checks_passed


@pytest.mark.parametrize(
    "target",
    [
        "ortools.sat.python.cp_model",
        "app.modules.planning.culinary",
        "app.modules.recipes.contracts.resolve_culinary_binding",
        "app.modules.recipes.public",
        "app.modules.planning.optimizer",
        "benchmark.schema",
    ],
)
def test_independent_grounding_import_boundary(target):
    assert check_source(f"import {target}", "app.modules.validation.recipe_grounding")
