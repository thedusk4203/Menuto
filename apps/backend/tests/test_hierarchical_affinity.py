import builtins
import socket
from datetime import timedelta
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.modules.preferences import hierarchical_affinity_contracts as c
from app.modules.preferences import hierarchy_contracts as h
from app.modules.preferences import prior_affinity_contracts as p
from app.modules.preferences.public import derive_one_hop_hierarchical_member_preference as derive
from hierarchical_affinity_fixtures import inputs, rebind, rebuild
from prior_shrinkage_fixtures import shrinkage
from target_affinity_fixtures import KINDS
from test_hierarchy_policy import positive_neutral_policy


def test_hc25_hc48_mapping_then_attenuation():
    result = derive(inputs())
    assert result.inherited.status == "AVAILABLE"
    assert result.inherited.value.amount.numerator == 1
    assert result.inherited.value.amount.denominator == 2
    assert result.parent_exact_target.mapped_explicit.value.amount.numerator == 3
    assert result.parent_exact_target.explicit_profile.rows[0].affinity.amount.numerator == 3


@pytest.mark.parametrize("source", KINDS)
@pytest.mark.parametrize("destination", KINDS)
def test_hc01_hc42_hc69_all25_exact_typed_directions(source, destination):
    result = derive(inputs(source_kind=source, destination_kind=destination))
    assert result.inherited.status == "AVAILABLE"
    trace = result.inherited.trace
    assert trace.relation_identity.source == result.parent_target
    assert trace.relation_identity.destination == result.destination_target
    assert trace.product.coordinate.destination_target_kind == destination
    assert {b.endpoint for b in trace.relation_identity.recipe_bindings} == {
        k for k, v in (("SOURCE", source), ("DESTINATION", destination)) if v == "DIRECT_RECIPE"
    }
    with pytest.raises(ValueError):
        c.InheritedMemberPreferenceCoordinate(
            destination_target_kind="MAIN_PROTEIN", transfer_policy_semantic_fingerprint="a" * 64
        )


@pytest.mark.parametrize("where", ["explicit", "reference"])
@pytest.mark.parametrize("mutation", ["empty", "batch", "different"])
def test_hc02_exact_target_child_rule(where, mutation):
    data = canonical(inputs())
    request = (
        data["destination"]["explicit"]["source"]["request"]
        if where == "explicit"
        else (data["destination"]["reference_source"]["request"])
    )
    target = dict(request["requested_targets"][0], feature_term_id=str(uuid4()))
    request["requested_targets"] = (
        []
        if mutation == "empty"
        else ([request["requested_targets"][0], target] if mutation == "batch" else [target])
    )
    with pytest.raises(ValueError):
        derive(data)


@pytest.mark.parametrize("mutation", ["id", "kind", "batch", "empty"])
def test_hc03_exact_hierarchy_destination_request(mutation):
    data = canonical(inputs())
    request = data["hierarchy_source"]["request"]
    other = data["parent"]["explicit"]["source"]["request"]["requested_targets"][0]
    if mutation == "id":
        request["requested_targets"][0]["feature_term_id"] = str(uuid4())
    else:
        request["requested_targets"] = (
            []
            if mutation == "empty"
            else [other]
            if mutation == "kind"
            else (request["requested_targets"] + [other])
        )
    with pytest.raises(ValueError):
        derive(data)


@pytest.mark.parametrize("field", ["household_id", "member_id"])
def test_hc04_foreign_member_rejected(field):
    subject = inputs(parent_state="UNDECLARED")
    data = canonical(subject)
    child = data["parent"]["explicit"]["source"]
    for name in ("request", "manifest", "preferences"):
        child[name][field] = str(uuid4()) if name == "request" else child["request"][field]
    with pytest.raises(ValueError, match="MEMBER_OWNER_MISMATCH"):
        derive(data)


def test_hc05_missing_required_parent_fails():
    with pytest.raises(ValueError, match="MISSING_REQUIRED_PARENT_INPUT"):
        derive(inputs() | dict(parent=None))
    subject = inputs()
    del subject["parent"]
    with pytest.raises(ValueError, match="MISSING_REQUIRED_PARENT_INPUT"):
        derive(subject)


@pytest.mark.parametrize(
    "state,reason",
    [("DECLARED", "DESTINATION_DIRECT_DECLARATION"), ("RETRACTED", "MEMBER_RETRACTED")],
)
def test_hc06_hc21_optional_parent_for_suppression(state, reason):
    result = derive(
        inputs(destination_state=state, destination_prior="AVAILABLE") | dict(parent=None)
    )
    assert result.inherited.status == "SUPPRESSED" and result.inherited.reason == reason
    assert result.parent_target is None and result.parent_exact_target is None
    assert "value" not in result.inherited.model_dump()
    subject = inputs(destination_state=state)
    del subject["parent"]
    assert derive(subject).inherited.reason == reason


def test_hc07_malformed_optional_parent_fails_before_suppression():
    data = canonical(inputs(destination_state="DECLARED"))
    data["parent"]["compatibility_policy"]["explicit_policy_fingerprint"] = "f" * 64
    with pytest.raises(ValueError):
        derive(data)


@pytest.mark.parametrize("state", ["UNDECLARED", "DECLARED", "RETRACTED"])
def test_hc08_parent_exact_target_checked_before_suppression(state):
    subject = inputs(
        source_kind="INGREDIENT", destination_kind="INGREDIENT", destination_state=state
    )
    # Both exact inputs share the same ledger; choosing the destination as parent
    # must fail even if its kind/coordinate/label happens to agree.
    with pytest.raises(ValueError, match="PARENT_TARGET_MISMATCH"):
        derive(subject | dict(parent=subject["destination"]))


@pytest.mark.parametrize(
    "name",
    [
        "eligibility",
        "selected_relation",
        "mapping_row",
        "attenuation",
        "parent_selector",
        "actor",
        "evidence_strength",
        "amount",
    ],
)
def test_hc09_untrusted_input_extras_rejected(name):
    with pytest.raises(ValueError):
        derive(inputs() | {name: "fake"})


def test_hc10_constructed_and_dictionary_inputs_revalidate():
    data = inputs()
    parsed = c.OneHopHierarchicalMemberPreferenceInput(**data)
    assert (
        derive(parsed)
        == derive(canonical(parsed))
        == derive(c.OneHopHierarchicalMemberPreferenceInput.model_construct(**data))
    )
    bad = p.ExactTargetPriorBackedAffinityInput.model_construct(**data["parent"].__dict__)
    object.__setattr__(
        bad,
        "compatibility_policy",
        bad.compatibility_policy.model_copy(update=dict(explicit_policy_fingerprint="f" * 64)),
    )
    with pytest.raises(ValueError):
        derive(
            c.OneHopHierarchicalMemberPreferenceInput.model_construct(**(data | dict(parent=bad)))
        )


def test_hc11_hc14_incoherent_member_frontiers_fail():
    subject = inputs(destination_state="DECLARED")
    data = canonical(subject)
    ledger = data["destination"]["explicit"]["source"]["preferences"]
    ledger["declarations"] = ledger["declarations"][:1]
    ledger["frontier"] = 1
    ledger["feature_terms"] = []
    # The old destination looks undeclared while the parent sees its declaration.
    with pytest.raises(ValueError, match="INCOHERENT_MEMBER_HISTORY"):
        derive(data)


@pytest.mark.parametrize(
    "field", ["id", "stream_id", "recorded_at", "actor", "authorship", "predecessor"]
)
def test_hc12_same_frontier_changed_ledger_fails(field):
    from app.modules.preferences.contracts import MemberPreferenceDeclarationFact

    data = canonical(inputs())
    row = data["parent"]["explicit"]["source"]["preferences"]["declarations"][0]
    if field in {"id", "stream_id"}:
        row[field] = str(uuid4())
    elif field == "recorded_at":
        row[field] = "2026-10-22T00:00:04Z"
    elif field == "predecessor":
        row["command"]["predecessor_id"] = str(uuid4())
    else:
        row["command"]["actor_user_id" if field == "actor" else "authorship"] = (
            str(uuid4()) if field == "actor" else "AUTHORIZED_REPRESENTATIVE"
        )
        from app.modules.preferences.contracts import PreferenceWriteCommand

        row["command_fingerprint"] = PreferenceWriteCommand.model_validate(
            row["command"]
        ).fingerprint()
    # Invalid lineage is rejected by the frozen child; internally valid alternative
    # ledger bodies are rejected by the new common-history gate.
    with pytest.raises(ValueError):
        MemberPreferenceDeclarationFact.model_validate(row)
        derive(data)


def test_hc13_hc16_hc74_different_observation_clocks_preserved():
    subject = inputs()
    first = derive(subject)
    data = canonical(subject)
    data["parent"]["explicit"]["source"]["preferences"]["captured_at"] = "2026-10-22T05:00:00Z"
    second = derive(data)
    assert first.member_ledger_fingerprint == second.member_ledger_fingerprint
    assert first.inherited == second.inherited
    assert first.fingerprint != second.fingerprint
    assert first.parent_exact_target.fingerprint != second.parent_exact_target.fingerprint
    assert second.interpretation_mode == "VERSIONED_CONSUMER_POLICY_REPLAY"
    assert (
        c.OneHopHierarchicalMemberPreferenceDraft.model_validate_json(second.model_dump_json())
        == second
    )


def test_hc15_member_ledger_order_is_canonical_only_for_equivalence():
    subject = inputs(destination_state="DECLARED")
    data = canonical(subject)
    data["parent"]["explicit"]["source"]["preferences"]["declarations"].reverse()
    result = derive(data)
    assert result.member_ledger_fingerprint == derive(subject).member_ledger_fingerprint
    assert result.parent_exact_target.subject != result.destination_exact_target.subject


@pytest.mark.parametrize("value", ["LIKE", "DISLIKE", "NEUTRAL"])
def test_hc17_hc18_hc19_destination_declaration_wins(value):
    result = derive(inputs(destination_state="DECLARED", destination_value=value, value="DISLIKE"))
    assert result.inherited.reason == "DESTINATION_DIRECT_DECLARATION"
    assert "trace" not in result.inherited.model_dump()


@pytest.mark.parametrize("value", ["LIKE", "NEUTRAL"])
def test_hc19_hc20_nonzero_neutral_and_explicit_zero_suppress(value):
    subject = inputs(destination_state="DECLARED", destination_value=value)
    policy = positive_neutral_policy().explicit_policy.model_dump()
    if value == "LIKE":
        for group in policy["target_policies"]:
            for row in group["affinity_rules"]:
                row["amount"] = dict(
                    numerator={"DISLIKE": -1, "NEUTRAL": -1, "LIKE": 0}[row["value"]],
                    denominator=2 if row["value"] == "NEUTRAL" else 1,
                )
    from app.modules.preferences.contracts import ExplicitTargetAffinityPolicy

    subject["destination"] = rebind(
        subject["destination"], explicit_policy=ExplicitTargetAffinityPolicy.model_validate(policy)
    )
    result = derive(subject)
    assert result.inherited.reason == "DESTINATION_DIRECT_DECLARATION"
    assert result.destination_exact_target.explicit_profile.rows[0].raw_state.value == value
    assert result.destination_exact_target.explicit_profile.rows[0].affinity.amount.numerator == (
        0 if value == "LIKE" else 1
    )


def test_hc24_destination_prior_keeps_separate_component():
    result = derive(inputs(destination_prior="AVAILABLE"))
    assert result.destination_exact_target.effective.mode == "PRIOR_ONLY_COLD_START"
    assert result.inherited.status == "AVAILABLE"
    assert (
        result.destination_exact_target.effective.value.coordinate.coordinate_id
        == "MEMBER_PROFILE_AFFINITY"
    )
    assert result.inherited.value.coordinate.coordinate_id == "INHERITED_MEMBER_PREFERENCE"
    assert not hasattr(result, "effective")


@pytest.mark.parametrize(
    "state,prior,reason",
    [
        ("UNDECLARED", "AVAILABLE", "PARENT_PRIOR_ONLY_COLD_START"),
        ("UNDECLARED", "NO_PUBLICATION", "PARENT_UNDECLARED"),
        ("RETRACTED", "AVAILABLE", "PARENT_MEMBER_RETRACTED"),
    ],
)
def test_hc27_hc28_hc29_parent_no_explicit_fallback(state, prior, reason):
    result = derive(inputs(parent_state=state, prior=prior))
    assert result.inherited.status == "UNAVAILABLE" and result.inherited.reason == reason
    assert "value" not in result.inherited.model_dump()


def test_hc30_inherited_result_is_not_parent_input():
    subject = inputs()
    with pytest.raises(ValueError):
        derive(subject | dict(parent=derive(subject)))


def test_hc26_hc31_hc32_hc65_prior_and_shrinkage_do_not_enter_transfer():
    subject = inputs(prior="AVAILABLE")
    first = derive(subject)
    assert first.parent_exact_target.effective.mode == "BLENDED_EXPLICIT_AND_PRIOR"
    assert first.parent_exact_target.effective.value.amount.model_dump() == dict(
        numerator=1, denominator=2
    )
    assert first.parent_exact_target.mapped_explicit.value.amount.model_dump() == dict(
        numerator=3, denominator=4
    )
    parent = rebind(subject["parent"], prior_state="AVAILABLE", prior_amount=(-1, 1))
    second = derive(subject | dict(parent=parent))
    assert first.inherited == second.inherited and first.fingerprint != second.fingerprint
    parent = parent.model_copy(
        update=dict(
            shrinkage_policy=shrinkage(
                parent.compatibility_policy, version="2", weights=((1, 3), (1, 4), (0, 1))
            )
        )
    )
    third = derive(subject | dict(parent=parent))
    assert second.inherited == third.inherited and second.fingerprint != third.fingerprint
    assert third.parent_exact_target.effective.value != second.parent_exact_target.effective.value


def test_hc33_prior_cannot_mint_explicit_eligibility():
    subject = inputs(parent_state="UNDECLARED", prior="AVAILABLE")
    first = derive(subject)
    subject["parent"] = rebind(subject["parent"], prior_state="AVAILABLE", prior_amount=(1, 1))
    assert derive(subject).inherited == first.inherited
    assert derive(inputs(prior="AVAILABLE")).inherited.status == "AVAILABLE"


def test_hc34_hc80_non_authority_flags_and_member_lineage():
    result = derive(inputs())
    assert result.parent_exact_target.explicit_profile.rows[0].evidence_strength.level == "LOW"
    assert result.member_owner == "PRESERVED" and result.evidence_strength == "NOT_DERIVED"
    assert not result.planner_ready and not result.activation_ready
    assert (
        result.learned_evidence
        == result.contextual_evidence
        == result.passive_evidence
        == "UNAVAILABLE"
    )
    assert (
        result.recursive_transfer
        == result.parent_aggregation
        == result.candidate_aggregation
        == "NOT_PERFORMED"
    )
    assert result.taste_fit == "UNAVAILABLE"
    assert "evidence_strength" not in result.inherited.model_dump()


@pytest.mark.parametrize(
    "field,value", [("target_kind", "FLAVOR"), ("compatibility_policy_fingerprint", "f" * 64)]
)
def test_hc45_forged_published_parent_descriptor_rejected(field, value):
    data = canonical(inputs())
    policy = data["hierarchy_source"]["publications"][0]["command"]["policy"]
    next(d for d in policy["directions"] if d["enabled"])["rows"][0]["source_descriptor"][field] = (
        value
    )
    with pytest.raises(ValueError):
        derive(data)


@pytest.mark.parametrize(
    "which", ["explicit", "compatibility", "inactive_explicit", "inactive_compatibility"]
)
def test_hc46_hc47_valid_but_different_full_parent_policy_unavailable(which):
    subject = inputs()
    parent = subject["parent"]
    if "explicit" in which:
        body = parent.explicit.policy.model_dump()
        if which == "explicit":
            body["policy_version"] = "2"
        else:
            body["target_policies"][0]["strength_rules"][0]["level"] = "MEDIUM"
        from app.modules.preferences.contracts import ExplicitTargetAffinityPolicy

        parent = rebind(parent, explicit_policy=ExplicitTargetAffinityPolicy.model_validate(body))
    else:
        body = parent.compatibility_policy.model_dump()
        if which == "compatibility":
            body["policy_version"] = "2"
        else:
            next(r for r in body["explicit_maps"][0]["rows"] if r["value"] == "LIKE")[
                "output_amount"
            ] = dict(numerator=4, denominator=5)
        mapping = p.ExactTargetPriorCompatibilityPolicy.model_validate(body)
        parent = parent.model_copy(
            update=dict(compatibility_policy=mapping, shrinkage_policy=shrinkage(mapping))
        )
    result = derive(subject | dict(parent=parent))
    assert result.inherited.reason == "INCOMPATIBLE_COORDINATE"


@pytest.mark.parametrize("value,numerator", [("DISLIKE", -1), ("NEUTRAL", 0), ("LIKE", 1)])
def test_hc51_hc52_hc53_semantics_not_raw_sign(value, numerator):
    result = derive(inputs(value=value, transfer=positive_neutral_policy()))
    assert result.inherited.status == "AVAILABLE"
    assert result.inherited.trace.semantic_state == value
    assert result.parent_exact_target.explicit_profile.rows[0].affinity.amount.numerator > 0
    assert result.inherited.value.amount.model_dump() == dict(
        numerator=numerator, denominator=1 if numerator == 0 else 2
    )


def test_hc54_missing_semantic_row_has_no_implicit_zero():
    from hierarchy_fixtures import policy

    result = derive(inputs(value="NEUTRAL", transfer=policy(states=("DISLIKE", "LIKE"))))
    assert result.inherited.reason == "SOURCE_VALUE_NOT_MAPPED"
    assert "value" not in result.inherited.model_dump()


def test_hc59_hc60_hc67_coordinate_full_policy_and_scoped_equality():
    first = derive(inputs())
    coordinate = first.inherited.value.coordinate
    assert coordinate.transfer_policy_semantic_fingerprint == (
        first.hierarchy.rows[0].policy.command.policy.fingerprint()
    )
    assert (
        c.ScopedInheritedMemberPreference.model_validate(first.inherited.value)
        == first.inherited.value
    )
    assert not hasattr(first.inherited.value, "target_id") and not hasattr(
        first.inherited.value, "rank"
    )
    with pytest.raises(TypeError):
        _ = first.inherited.value + first.inherited.value
    with pytest.raises(TypeError):
        _ = first.inherited.value < first.inherited.value


@pytest.mark.parametrize(
    "mapped,attenuation,expected",
    [
        ((2, 3), (3, 5), (2, 5)),
        ((-2, 3), (3, 5), (-2, 5)),
        (
            (2147483646, 2147483647),
            (2147483645, 2147483647),
            (4611686007689969670, 4611686014132420609),
        ),
    ],
)
def test_hc61_hc63_hc64_exact_product_near_authored_bound(mapped, attenuation, expected):
    subject = inputs(value="DISLIKE" if mapped[0] < 0 else "LIKE")
    transfer = subject["hierarchy_source"].publications[0].command.policy.model_dump()
    direction = next(d for d in transfer["directions"] if d["enabled"])
    direction["attenuation"] = dict(numerator=attenuation[0], denominator=attenuation[1])
    row = next(
        r
        for r in direction["rows"]
        if r["source_affinity_value"] == ("DISLIKE" if mapped[0] < 0 else "LIKE")
    )
    row["output_amount"] = dict(numerator=mapped[0], denominator=mapped[1])
    result = derive(rebuild(subject, transfer=h.HierarchyTransferPolicy.model_validate(transfer)))
    assert result.inherited.value.amount.model_dump() == dict(
        numerator=expected[0], denominator=expected[1]
    )


@pytest.mark.parametrize(
    "amount",
    [
        dict(numerator=True, denominator=1),
        dict(numerator="1", denominator=2),
        dict(numerator=0.5, denominator=1),
        dict(numerator=2, denominator=4),
        dict(numerator=0, denominator=2),
        dict(numerator=1, denominator=0),
        dict(numerator=2, denominator=1),
        dict(numerator=1, denominator=1 << 128),
    ],
)
def test_hc62_hc63_hc64_noncanonical_or_oversized_derived_amount_rejected(amount):
    with pytest.raises(ValueError):
        c.InheritedMemberPreferenceAmount.model_validate(amount)


def rehashed_root(result, edit):
    data = canonical(result)
    edit(data)
    data["fingerprint"] = h.hierarchy_hash(
        "member-preference.one-hop-result.v1", {k: v for k, v in data.items() if k != "fingerprint"}
    )
    return data


@pytest.mark.parametrize(
    "field,value",
    [
        ("destination_target_kind", "FLAVOR"),
        ("transfer_policy_semantic_fingerprint", "a" * 64),
        ("coordinate_id", "MEMBER_PROFILE_AFFINITY"),
        ("coordinate_version", True),
        ("coordinate_version", "1"),
    ],
)
def test_hc57_hc58_forged_descriptor_rejects_before_transfer_math(monkeypatch, field, value):
    result = derive(inputs())
    data = rehashed_root(
        result, lambda d: d["inherited"]["value"]["coordinate"].update({field: value})
    )
    import app.modules.preferences.hierarchical_affinity as runtime

    def fail(*args, **kw):
        pytest.fail("forged coordinate reached transfer arithmetic")

    monkeypatch.setattr(runtime, "Fraction", fail)
    # Cached descriptor is parsed before root replay and must fail without math.
    with pytest.raises(ValueError):
        c.OneHopHierarchicalMemberPreferenceDraft.model_validate(data)


@pytest.mark.parametrize("component", ["destination_exact_target", "parent_exact_target"])
def test_hc70_edited_cached_children_rejected_even_outer_rehashed(component):
    result = derive(inputs(prior="AVAILABLE", destination_prior="AVAILABLE"))
    data = rehashed_root(result, lambda d: d[component].update(fingerprint="a" * 64))
    with pytest.raises(ValueError):
        c.OneHopHierarchicalMemberPreferenceDraft.model_validate(data)


@pytest.mark.parametrize(
    "field", ["mapped", "coefficient", "product", "row", "relation", "provider"]
)
def test_hc72_rehashed_trace_tampering_rejects(field):
    result = derive(inputs())

    def edit(d):
        trace = d["inherited"]["trace"]
        if field == "mapped":
            trace["mapped_inherited"]["amount"] = dict(numerator=1, denominator=3)
        elif field == "coefficient":
            trace["attenuation"] = dict(numerator=1, denominator=3)
        elif field == "product":
            trace["product"]["amount"] = dict(numerator=1, denominator=3)
            d["inherited"]["value"]["amount"] = trace["product"]["amount"]
        elif field == "row":
            trace["mapping_row"]["expected_source_amount"] = dict(numerator=1, denominator=3)
        elif field == "relation":
            trace["relation_revision_id"] = str(uuid4())
        else:
            trace["provider_id"] = str(uuid4())

    with pytest.raises(ValueError):
        c.OneHopHierarchicalMemberPreferenceDraft.model_validate(rehashed_root(result, edit))


def test_hc58_stripping_descriptor_or_naked_number_never_available():
    result = derive(inputs())
    data = rehashed_root(
        result, lambda d: d["inherited"].update(value=dict(numerator=1, denominator=2))
    )
    with pytest.raises(ValueError):
        c.OneHopHierarchicalMemberPreferenceDraft.model_validate(data)


def test_hc74_hc75_hc76_full_input_replay_not_visible_amount_hash():
    subject = inputs()
    first = derive(subject)
    source = subject["hierarchy_source"]
    second = derive(
        subject
        | dict(
            hierarchy_source=source.model_copy(
                update=dict(capture_completed_at=source.capture_completed_at + timedelta(seconds=1))
            )
        )
    )
    assert first.inherited == second.inherited and first.fingerprint != second.fingerprint
    assert derive(subject).model_dump_json() == first.model_dump_json()
    assert first.interpretation_mode == "VERSIONED_CONSUMER_POLICY_REPLAY"
    assert first.destination_exact_target.interpretation_mode == "VERSIONED_CONSUMER_POLICY_REPLAY"


def test_hc77_pure_entry_and_replay_without_io_clock_randomness(monkeypatch):
    subject = inputs()
    # Import facade/dependencies before sealing IO; no child resolver is mocked.
    result = derive(subject)
    import random
    import time
    import uuid
    from pathlib import Path

    import sqlalchemy
    import sqlalchemy.orm
    from app.persistence import database

    def fail(*a, **kw):
        pytest.fail("pure consumer attempted IO/clock/randomness")

    with monkeypatch.context() as m:
        for owner, name in (
            (builtins, "open"),
            (Path, "open"),
            (socket, "socket"),
            (socket, "create_connection"),
            (sqlalchemy, "create_engine"),
            (sqlalchemy.orm.Session, "execute"),
            (database, "create_database_engine"),
            (time, "time"),
            (time, "monotonic"),
            (random, "random"),
            (uuid, "uuid4"),
        ):
            m.setattr(owner, name, fail)
        assert derive(subject) == result
        assert c.OneHopHierarchicalMemberPreferenceDraft.model_validate(canonical(result)) == result


@pytest.mark.parametrize("kind", ["METHOD", "DIRECT_RECIPE"])
@pytest.mark.parametrize("cut", ["parent_reference", "destination_reference", "hierarchy"])
def test_hc81_all_nested_identity_manifests_checked(kind, cut):
    subject = inputs(source_kind=kind, destination_kind=kind)
    data = canonical(subject)
    if cut == "hierarchy":
        # Alter the destination explicit/reference together to remain internally valid;
        # they now contradict the separate hierarchy owner/context cut.
        child = data["destination"]
        fact = child["explicit"]["source"]["manifest"]["entries"][0]["identity"]
        fact["label" if kind == "METHOD" else "name"] = "Conflicting immutable owner body"
        child["reference_source"]["identities"][0]["identity"] = fact
    else:
        child = data["parent" if cut == "parent_reference" else "destination"]
        fact = child["reference_source"]["identities"][0]["identity"]
        fact["label" if kind == "METHOD" else "name"] = "Conflicting immutable owner body"
    with pytest.raises(ValueError, match="CONFLICTING_IMMUTABLE_OWNER_FACT"):
        derive(data)


def test_hc81_mutable_ingredient_names_do_not_alias_or_grant_transfer():
    subject = inputs(source_kind="INGREDIENT", destination_kind="INGREDIENT")
    data = canonical(subject)
    data["parent"]["reference_source"]["identities"][0]["identity"]["name"] = (
        "Changed display label"
    )
    assert derive(data).inherited.status == "AVAILABLE"
    # Identical display labels do not make these two exact targets interchangeable.
    with pytest.raises(ValueError, match="PARENT_TARGET_MISMATCH"):
        derive(data | dict(parent=data["destination"]))


def test_hc57_all_cached_descriptors_forged_reject_before_transfer_math(monkeypatch):
    result = derive(inputs())

    def edit(data):
        for value in (
            data["inherited"]["value"],
            data["inherited"]["trace"]["mapped_inherited"],
            data["inherited"]["trace"]["product"],
        ):
            value["coordinate"]["transfer_policy_semantic_fingerprint"] = "f" * 64

    data = rehashed_root(result, edit)
    import app.modules.preferences.hierarchical_affinity as runtime

    def fail(*args, **kw):
        pytest.fail("forged descriptor reached new transfer arithmetic")

    monkeypatch.setattr(runtime, "Fraction", fail)
    with pytest.raises(ValueError, match="Inherited descriptor differs"):
        c.OneHopHierarchicalMemberPreferenceDraft.model_validate(data)


def test_hc70_valid_replayed_child_cannot_be_transplanted():
    subject = inputs(prior="AVAILABLE")
    original = derive(subject)
    other = derive(
        subject
        | dict(parent=rebind(subject["parent"], prior_state="AVAILABLE", prior_amount=(-1, 1)))
    )
    data = rehashed_root(
        original, lambda d: d.update(parent_exact_target=canonical(other.parent_exact_target))
    )
    with pytest.raises(ValueError, match="parent_exact_target"):
        c.OneHopHierarchicalMemberPreferenceDraft.model_validate(data)


def test_hc68_repeated_member_history_does_not_increase_strength_or_magnitude():
    from target_affinity_fixtures import revision

    subject = inputs()
    original = derive(subject)
    data = canonical(subject)
    rows = list(subject["parent"].explicit.source.preferences.declarations)
    for _ in range(3):
        rows.append(revision(rows[-1], value="LIKE"))
    for which in ("destination", "parent"):
        ledger = data[which]["explicit"]["source"]["preferences"]
        ledger.update(frontier=len(rows), declarations=canonical(rows))
    result = derive(data)
    assert result.inherited == original.inherited
    assert result.parent_exact_target.explicit_profile.rows[0].evidence_strength.level == "LOW"
    assert result.fingerprint != original.fingerprint


def test_hc60_hc69_equal_scoped_numbers_do_not_imply_equal_exact_targets():
    subject = inputs()
    first = derive(subject)
    child = canonical(subject["destination"])
    identifier = str(uuid4())
    source = child["explicit"]["source"]
    source["request"]["requested_targets"][0]["feature_term_id"] = identifier
    source["manifest"]["entries"][0]["identity"]["id"] = identifier
    reference = child["reference_source"]
    reference["request"]["requested_targets"][0]["feature_term_id"] = identifier
    reference["identities"][0]["target"]["feature_term_id"] = identifier
    reference["identities"][0]["identity"]["id"] = identifier
    destination = p.ExactTargetPriorBackedAffinityInput.model_validate(child)
    second = derive(rebuild(subject | dict(destination=destination)))
    assert first.inherited.value == second.inherited.value
    assert first.destination_target != second.destination_target
    assert first.inherited.trace.relation_revision_id != second.inherited.trace.relation_revision_id
    assert first.fingerprint != second.fingerprint
