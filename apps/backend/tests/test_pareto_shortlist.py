"""Conservative coverage only: no missing policy, cost, safety or material truth invented."""

from dataclasses import FrozenInstanceError
from decimal import Decimal
from itertools import permutations
from uuid import uuid4

import pytest
from app.modules.planning.contracts import (
    ParetoShortlistDraft,
    ShortlistPolicyDraft,
)
from app.modules.planning.grounding import resolve_captured_candidate
from app.modules.planning.shortlist import (
    CapturedShortlistPool,
    _captured_pool,
    shortlist_grounded_pool,
)
from app.modules.recipes.contracts import CulinaryGenerationTrigger
from app.modules.retail.contracts import ProcurementSnapshotDraft
from grounding_fixtures import empty_inventory, retail_for, setup
from test_architecture import check_source


def policy(**updates):
    return ShortlistPolicyDraft(
        **(
            dict(policy_id="synthetic.coverage", policy_version="1", max_inputs=20, max_frontier=20)
            | updates
        )
    )


def entries():
    q, s, _ = setup()
    f = retail_for(s.recipe.ingredients[0].ingredient_id)
    extra = ProcurementSnapshotDraft(
        procurement_class=f["cls"], members=(f["member"],), options=(f["option"],)
    )
    both = s.model_copy(
        update=dict(
            procurements=(*s.procurements, extra),
            retailer_statuses=(*s.retailer_statuses, f["retailer_status"]),
        )
    )
    # Real capture returns statuses for the requested classes only, in the same RR snapshot.
    a = (q, resolve_captured_candidate(q, s))
    qb = q.model_copy(update=dict(procurement_class_ids=(*q.procurement_class_ids, f["cls"].id)))
    b = (qb, resolve_captured_candidate(qb, both))
    qc = q.model_copy(update=dict(procurement_class_ids=(f["cls"].id,)))
    sc = s.model_copy(update=dict(procurements=(extra,), retailer_statuses=(f["retailer_status"],)))
    c = (qc, resolve_captured_candidate(qc, sc))
    assert all(r.status == "GROUNDED" for _, r in (a, b, c))
    return a, b, c


def run(items, **limits):
    # Synthetic trusted-adapter mint for pure tests, never an untrusted production ingress.
    return shortlist_grounded_pool(_captured_pool(items), policy(**limits))


def test_strict_coverage_dominance_retains_every_primitive_and_records_witness():
    a, b, _ = entries()
    before = b[1].candidate.canonical_json()
    out = run((a, b))
    assert out.status == "COMPLETE"
    assert out.candidates == (b[1].candidate,)
    assert out.candidates[0].canonical_json() == before
    assert out.dominance[0].removed_fingerprint == a[1].candidate.fingerprint
    assert out.dominance[0].retained_fingerprint == b[1].candidate.fingerprint
    assert out.frontier_count == 1 and out.unique_candidate_count == 2
    assert not out.activation_ready and not out.candidates[0].activation_ready


def test_input_order_and_exact_duplicates_do_not_change_frontier_or_identity():
    items = entries()
    expected = run(items)
    for order in permutations(items):
        assert run(order) == expected
    assert run((*items, items[0])) == expected


def test_semantic_duplicate_tuple_order_has_canonical_wire_and_stable_representative():
    _, b, _ = entries()
    q = b[0].model_copy(update=dict(procurement_class_ids=b[0].procurement_class_ids[::-1]))
    permuted = (q, resolve_captured_candidate(q, b[1].candidate.sources))
    assert permuted[1].candidate.fingerprint == b[1].candidate.fingerprint
    x = run((b, permuted))
    y = run((permuted, b))
    assert x == y and x.model_dump_json() == y.model_dump_json()
    assert run((b,)).canonical_json() == run((permuted,)).canonical_json()


def test_incomparable_package_paths_preserved_even_with_equal_counts():
    a, _, c = entries()
    out = run((a, c))
    assert len(out.candidates) == 2 and not out.dominance


@pytest.mark.parametrize("difference", ["cutoff", "nutrition", "culinary_trigger", "inventory"])
def test_material_context_differences_preserved(difference):
    a, b, _ = entries()
    q, s = b[0], b[1].candidate.sources
    if difference == "cutoff":
        from datetime import timedelta

        q = q.model_copy(update=dict(as_of=q.as_of + timedelta(seconds=1)))
        s = s.model_copy(update=dict(inventory=s.inventory.model_copy(update=dict(as_of=q.as_of))))
    elif difference == "nutrition":
        ref = s.nutrition_references[0]
        nutrients = ref.fact.nutrients.model_copy(update=dict(protein_g=Decimal(21)))
        fact = ref.fact.model_copy(update=dict(nutrients=nutrients))
        s = s.model_copy(
            update=dict(nutrition_references=(ref.model_copy(update=dict(fact=fact)),))
        )
    elif difference == "culinary_trigger":
        q = q.model_copy(
            update=dict(
                candidate=q.candidate.model_copy(
                    update=dict(triggers=(CulinaryGenerationTrigger.AUTHORED_SELECTION,))
                )
            )
        )
    else:
        s = empty_inventory(s)
    changed = (q, resolve_captured_candidate(q, s))
    assert changed[1].status == "GROUNDED"
    out = run((a, changed))
    assert len(out.candidates) == 2


def test_equal_coverage_different_provenance_not_tie_broken_away():
    a, _, _ = entries()
    q = a[0]
    s = a[1].candidate.sources
    # Additional unused canonical catalog evidence changes provenance, not resolved nutrition.
    identity = s.ingredients[0].model_copy(update=dict(id=uuid4()))
    s = s.model_copy(update=dict(ingredients=(*s.ingredients, identity)))
    b = (q, resolve_captured_candidate(q, s))
    out = run((a, b))
    assert len(out.candidates) == 2 and not out.dominance
    assert out == run((b, a))


def test_noncontained_source_fact_prevents_coverage_dominance():
    a, b, _ = entries()
    q, s = b[0], b[1].candidate.sources
    p = s.procurements[0]
    # Authored assessment provenance is not erased just because paths compare equally.
    p = p.model_copy(
        update=dict(
            members=(
                p.members[0].model_copy(
                    update=dict(rationale="Different authored equivalence rationale")
                ),
            )
        )
    )
    s = s.model_copy(update=dict(procurements=(p, *s.procurements[1:])))
    b = (q, resolve_captured_candidate(q, s))
    assert b[1].status == "GROUNDED"
    assert len(run((a, b)).candidates) == 2


@pytest.mark.parametrize("failure", ["INCOMPLETE", "REJECTED"])
def test_failed_grounding_makes_no_shortlist_eligible(failure):
    a, _, _ = entries()
    q, s = a[0], a[1].candidate.sources
    if failure == "INCOMPLETE":
        s = s.model_copy(update=dict(nutrition_references=()))
    else:
        q = q.model_copy(update=dict(tracked_member_id=uuid4()))
    failed = (q, resolve_captured_candidate(q, s))
    assert failed[1].status == failure
    out = run((a, failed))
    assert out.status == "GROUNDING_FAILED" and out.candidates == ()
    assert out.failures[0].status == failure
    assert out.frontier_count is None


def test_empty_is_not_infeasible():
    out = run(())
    assert out.status == "EMPTY" and not out.activation_ready


def test_frontier_overflow_never_truncates_incomparable_options():
    a, _, c = entries()
    out = run((a, c), max_frontier=1)
    assert out.status == "FRONTIER_LIMIT_EXCEEDED" and out.candidates == ()
    assert out.frontier_count == 2 and out.dominance == ()


def test_input_limit_never_selects_arbitrary_prefix():
    a, b, c = entries()
    out = run((a, b, c), max_inputs=2)
    assert out.status == "INPUT_LIMIT_EXCEEDED" and not out.candidates
    assert out.unique_candidate_count is None and out.frontier_count is None


@pytest.mark.parametrize("field", ["max_inputs", "max_frontier"])
@pytest.mark.parametrize("value", [0, -1, True, 1.0, "2"])
def test_explicit_resource_policy_requires_positive_integers(field, value):
    with pytest.raises(ValueError):
        policy(**{field: value})


def test_policy_identity_changes_result_identity():
    a, _, _ = entries()
    pool = _captured_pool((a,))
    p = policy()
    x = shortlist_grounded_pool(pool, p)
    y = shortlist_grounded_pool(pool, p.model_copy(update=dict(policy_version="2")))
    assert x.candidates == y.candidates and x.fingerprint != y.fingerprint


def test_wire_roundtrip_is_immutable_but_not_capture_authority():
    a, _, _ = entries()
    out = run((a,))
    copy = ParetoShortlistDraft.model_validate_json(out.model_dump_json())
    assert copy == out
    with pytest.raises(ValueError):
        out.activation_ready = True
    with pytest.raises(TypeError):
        shortlist_grounded_pool(copy, policy())
    with pytest.raises(ValueError):
        ParetoShortlistDraft.model_validate(out.model_dump() | dict(is_safe=True))


@pytest.mark.parametrize("kind", ["candidate", "result", "dict", "tuple"])
def test_self_consistent_hash_or_ready_flag_cannot_mint_ingress(kind):
    a, _, _ = entries()
    candidate = a[1].candidate
    raw = {
        "candidate": candidate,
        "result": a[1],
        "dict": candidate.model_dump(),
        "tuple": (candidate,),
    }[kind]
    with pytest.raises(TypeError):
        shortlist_grounded_pool(raw, policy())
    with pytest.raises(TypeError):
        CapturedShortlistPool((a,))


def test_pool_is_immutable_and_request_mismatch_rejected():
    a, _, _ = entries()
    pool = _captured_pool((a,))
    with pytest.raises(FrozenInstanceError):
        pool._entries = ()
    with pytest.raises(ValueError, match="different request"):
        _captured_pool(((a[0].model_copy(update=dict(currency="USD")), a[1]),))


@pytest.mark.parametrize(
    "target",
    [
        "ortools.sat.python.cp_model",
        "sqlalchemy",
        "socket",
        "pathlib",
        "os",
        "app.modules.execution.contracts",
        "app.modules.inventory.public",
        "app.modules.recipes.public",
        "app.modules.planning.grounding",
        "app.modules.planning.optimizer",
        "app.modules.planning.public",
        "app.modules.learning.contracts",
        "app.modules.validation.contracts",
    ],
)
def test_shortlist_cannot_reach_io_grounding_execution_or_optimizer(target):
    assert any(
        "SHORTLIST_NARROW_BOUNDARY" in e
        for e in check_source(f"import {target}", "app.modules.planning.shortlist")
    )


@pytest.mark.parametrize(
    "origin", ["RETAIL_OBSERVED", "REFERENCE_BASELINE", "CALIBRATED_REFERENCE"]
)
def test_unknown_conditional_supply_is_preserved_without_quality_or_cost_claim(origin):
    q, s, _ = setup(origin=origin, availability="UNKNOWN")
    out = run(((q, resolve_captured_candidate(q, s)),))
    path = out.candidates[0].ingredient_facts[0].procurement_paths[0]
    assert path.interpretation == "CONDITIONAL_EVIDENCE"
    assert path.availability == "UNKNOWN" and path.freshness_assessment == "NOT_IMPLEMENTED"
    assert not hasattr(out, "purchase_cost") and not out.activation_ready
