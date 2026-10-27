"""Reviewed source policy semantics, including the PR103 neutral-anchor correction."""

from fractions import Fraction
from uuid import uuid4

import pytest
from app.modules.preferences import hierarchy_contracts as h
from app.modules.preferences.contracts import ExplicitTargetAffinityPolicy, _profile_hash
from app.modules.preferences.hierarchy_contracts import HierarchyTransferPolicy
from app.modules.preferences.prior_affinity_contracts import ExactTargetPriorCompatibilityPolicy
from hierarchy_fixtures import policy


def test_h01_neutral_nonzero_rejected():
    body = policy().model_dump(mode="json")
    cell = next(c for c in body["directions"] if c["enabled"])
    row = next(r for r in cell["rows"] if r["source_affinity_value"] == "NEUTRAL")
    row["output_amount"] = {"numerator": 1, "denominator": 2}
    with pytest.raises(ValueError, match="NEUTRAL"):
        HierarchyTransferPolicy.model_validate(body)


def enabled(body):
    return next(c for c in body["directions"] if c["enabled"])


@pytest.mark.parametrize("state,numerator", [("DISLIKE", 1), ("LIKE", -1)])
def test_h02_h03_anti_correlation_rejected(state, numerator):
    body = policy().model_dump(mode="json")
    next(r for r in enabled(body)["rows"] if r["source_affinity_value"] == state)[
        "output_amount"
    ] = dict(numerator=numerator, denominator=2)
    with pytest.raises(ValueError, match=state):
        HierarchyTransferPolicy.model_validate(body)


def positive_neutral_policy():
    body = policy().model_dump(mode="json")
    for group in body["explicit_policy"]["target_policies"]:
        for row in group["affinity_rules"]:
            row["amount"].update(
                numerator={"DISLIKE": 1, "NEUTRAL": 2, "LIKE": 3}[row["value"]], denominator=4
            )
    explicit = ExplicitTargetAffinityPolicy.model_validate(body["explicit_policy"])
    body["compatibility_policy"]["explicit_policy_fingerprint"] = _profile_hash(explicit)
    for group in body["compatibility_policy"]["explicit_maps"]:
        for row in group["rows"]:
            row["expected_explicit_amount"].update(
                numerator={"DISLIKE": 1, "NEUTRAL": 2, "LIKE": 3}[row["value"]], denominator=4
            )
    compatibility = ExactTargetPriorCompatibilityPolicy.model_validate(body["compatibility_policy"])
    for row in enabled(body)["rows"]:
        row["source_descriptor"] = compatibility.coordinate_for("INGREDIENT").model_dump(
            mode="json"
        )
        row["expected_source_amount"].update(
            numerator={"DISLIKE": 1, "NEUTRAL": 2, "LIKE": 3}[row["source_affinity_value"]],
            denominator=4,
        )
    return HierarchyTransferPolicy.model_validate(body)


def test_h04_h07_positive_source_neutral_is_available_exact_zero():
    p = positive_neutral_policy()
    lookup = h.lookup_hierarchy_policy_row(p, "INGREDIENT", "PROTEIN", "NEUTRAL")
    assert lookup.status == "AVAILABLE"
    assert lookup.row.expected_source_amount.numerator == 1
    assert lookup.row.expected_source_amount.denominator == 2
    assert lookup.row.output_amount == h.HierarchyPolicyAmount(numerator=0, denominator=1)
    direction = next(d for d in p.directions if d.enabled)
    assert Fraction(0, 1) * Fraction(
        direction.attenuation.numerator, direction.attenuation.denominator
    ) == Fraction(0, 1)


@pytest.mark.parametrize("state", ["DISLIKE", "NEUTRAL", "LIKE"])
def test_h05_h06_rehashed_forged_semantic_amount_pair_rejected(state):
    body = policy().model_dump(mode="json")
    row = next(r for r in enabled(body)["rows"] if r["source_affinity_value"] == state)
    other = next(r for r in enabled(body)["rows"] if r["source_affinity_value"] != state)
    row["expected_source_amount"] = other["expected_source_amount"]
    assert len(h.hierarchy_hash("hierarchy.transfer-policy.v1", body)) == 64
    with pytest.raises(ValueError, match="expected frozen amount"):
        HierarchyTransferPolicy.model_validate(body)


@pytest.mark.parametrize("state", ["DISLIKE", "NEUTRAL", "LIKE"])
def test_h08_missing_semantic_row_has_no_zero_fallback(state):
    p = policy(states=tuple(s for s in ("DISLIKE", "NEUTRAL", "LIKE") if s != state))
    lookup = h.lookup_hierarchy_policy_row(p, "INGREDIENT", "PROTEIN", state)
    assert lookup.status == "SOURCE_VALUE_NOT_MAPPED" and lookup.row is None


def test_h09_policy_pin_is_replay_only_no_global_ownership():
    p = policy()
    assert p.policy_ownership == "HIERARCHY_COMPATIBILITY_REPLAY_ONLY"
    assert "global_owner" not in type(p).model_fields
    with pytest.raises(ValueError):
        HierarchyTransferPolicy.model_validate(
            p.model_dump() | dict(policy_ownership="GLOBAL_OWNER")
        )


@pytest.mark.parametrize("source", sorted(h.KINDS))
@pytest.mark.parametrize("destination", sorted(h.KINDS))
def test_i02_complete_closed25_cells_no_automatic_relation(source, destination):
    p = policy(source_kind=source, destination_kind=destination)
    assert len(p.directions) == 25
    assert sum(d.enabled for d in p.directions) == 1
    assert not hasattr(p, "relations")


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown"])
def test_i02_invalid_matrix_never_wildcard(mutation):
    body = policy().model_dump(mode="json")
    if mutation == "missing":
        body["directions"].pop()
    elif mutation == "duplicate":
        body["directions"][-1] = body["directions"][0]
    else:
        body["directions"][-1]["source_kind"] = "MAIN_PROTEIN"
    with pytest.raises(ValueError):
        HierarchyTransferPolicy.model_validate(body)


@pytest.mark.parametrize("value", [True, "1", 0.5, 2147483648])
def test_c02_strict_authored_components_before_reduction(value):
    body = policy().model_dump(mode="json")
    enabled(body)["rows"][0]["expected_source_amount"]["numerator"] = value
    with pytest.raises(ValueError):
        HierarchyTransferPolicy.model_validate(body)


@pytest.mark.parametrize("value", [(0, 1), (-1, 2), (2, 1), (2, 4), (True, 2)])
def test_c02_no_default_zero_negative_amplifying_or_noncanonical_attenuation(value):
    body = policy().model_dump(mode="json")
    enabled(body)["attenuation"] = dict(numerator=value[0], denominator=value[1])
    with pytest.raises(ValueError):
        HierarchyTransferPolicy.model_validate(body)


@pytest.mark.parametrize("field", ["target_kind", "compatibility_policy_fingerprint"])
def test_c01_forged_descriptor_rejected(field):
    body = policy().model_dump(mode="json")
    enabled(body)["rows"][0]["source_descriptor"][field] = (
        "FLAVOR" if field == "target_kind" else "f" * 64
    )
    with pytest.raises(ValueError, match="descriptor"):
        HierarchyTransferPolicy.model_validate(body)


@pytest.mark.parametrize("kind", sorted(h.KINDS))
def test_i01_self_edge_same_kind_exact_identity_rejected(kind):
    key = (
        "ingredient_id"
        if kind == "INGREDIENT"
        else "recipe_id"
        if kind == "DIRECT_RECIPE"
        else "feature_term_id"
    )
    target = dict(kind=kind, **{key: uuid4()})
    with pytest.raises(ValueError, match="self-edge"):
        h.HierarchyStreamIdentity(
            kind="RELATION",
            policy_id=uuid4(),
            source=target,
            destination=target,
            recipe_bindings=[],
        )


def test_i04_recipe_version_binding_is_explicit():
    with pytest.raises(ValueError, match="version binding"):
        h.HierarchyStreamIdentity(
            kind="RELATION",
            policy_id=uuid4(),
            source=dict(kind="DIRECT_RECIPE", recipe_id=uuid4()),
            destination=dict(kind="METHOD", feature_term_id=uuid4()),
            recipe_bindings=[],
        )
