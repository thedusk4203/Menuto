"""SMTF37–119: public-interface replay, exact bridges and fail-closed coverage."""

from copy import deepcopy
from datetime import timedelta
from fractions import Fraction
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.domain.resolution import ResolutionError
from app.modules.planning import shared_target_tastefit as core
from app.modules.planning import shared_target_tastefit_contracts as c
from app.modules.planning import tastefit_contracts as child
from app.modules.planning.shared_target_tastefit_public import (
    derive_shared_member_target_tastefit as derive,
)
from app.modules.planning.shared_target_tastefit_public import (
    validate_shared_member_target_tastefit as validate,
)
from app.modules.planning.tastefit_public import derive_candidate_member_tastefit as child_derive
from candidate_feature_fixtures import seal_source as seal_projection_source
from preference_fixtures import command, declaration
from shared_target_tastefit_fixtures import (
    authored_policy,
    make_cohort,
    pack,
    replace_policy,
)
from tastefit_fixtures import seal, with_member_modes, with_policy


@pytest.fixture(scope="module")
def source():
    return make_cohort()


def bad(value, operation=derive, code=None):
    with pytest.raises(ResolutionError) as caught:
        operation(value)
    if code:
        assert caught.value.code == code, caught.value.detail
    return caught.value


def withheld(result):
    assert result.aggregate_availability == "UNAVAILABLE"
    assert result.value is result.weight_total is result.weighted_total is None
    assert all(v.common_operand is v.weighted_contribution is None for v in result.contributions)


def policy_body(source):
    return canonical(source.request.policy)


def policy_source(source, **changes):
    return replace_policy(
        source, c.SharedMemberTargetTasteFitPolicy.model_validate(policy_body(source) | changes)
    )


def reseal_wire(body):
    body["children"].sort(key=lambda ch: ch["subject"]["member_id"])
    body["owner_frames"].sort(key=lambda pair: pair[0])
    body["fingerprint"] = c.shared_tastefit_hash(
        "shared-target.sources.v1", {k: v for k, v in body.items() if k != "fingerprint"}
    )
    return body


def target_row(ch, source):
    return next(r for r in ch.targets if r.proof.target == source.request.target)


def test_smtf37_full_sources_and_numeric_coverage_separate(source):
    r = validate(derive(source))
    assert r.coverage.source_coverage == r.coverage.numeric_coverage == "COMPLETE"
    assert r.coverage.required_member_ids == r.coverage.captured_member_ids
    assert len(r.contributions) == r.coverage.required_count == 2
    assert r.sources.children == source.children


def test_smtf38_duplicate_input_rejected_before_dictionary_collapse(source):
    raw = canonical(source)
    raw["request"]["members"].append(deepcopy(raw["request"]["members"][0]))
    bad(raw)


@pytest.mark.parametrize("field", ["members", "children"])
def test_smtf39_missing_required_input_or_child(source, field):
    raw = canonical(source)
    (raw["request"] if field == "members" else raw)[field].pop()
    bad(reseal_wire(raw))


def test_smtf40_extra_favorable_child_rejects(source):
    raw = canonical(source)
    raw["children"].append(canonical(make_cohort(states=("LIKE",)).children[0]))
    bad(reseal_wire(raw), code="SOURCE_COVERAGE_INCOMPLETE")


def test_smtf41_member_slot_request_subject_binding(source):
    raw = canonical(source)
    raw["children"][0]["subject"]["member_id"] = raw["children"][1]["subject"]["member_id"]
    bad(reseal_wire(raw))


def test_smtf42_empty_participants_never_zero(source):
    raw = canonical(source)
    raw["request"]["projection_request"]["grounding_request"]["participants"]["participants"] = []
    bad(raw)


def test_smtf43_tracked_only_substitution_rejects(source):
    raw = canonical(source)
    g = raw["request"]["projection_request"]["grounding_request"]
    raw["request"]["members"] = [
        m for m in raw["request"]["members"] if m["member_id"] == g["tracked_member_id"]
    ]
    bad(raw, code="PARTICIPANT_SET_MISMATCH")


@pytest.mark.parametrize("field,value", [("portion_factor", "4"), ("nutrition_role", "SHARED")])
def test_smtf44_context_tamper_not_coherent_candidate(source, field, value):
    raw = canonical(source)
    raw["request"]["projection_request"]["grounding_request"]["participants"]["participants"][0][
        field
    ] = value
    bad(raw)


def test_smtf45_other_candidate_same_amount_rejects(source):
    other = make_cohort()
    raw = canonical(source)
    raw["children"][0] = canonical(other.children[0])
    bad(reseal_wire(raw))


@pytest.mark.parametrize("field", ["recipe_version_id", "recipe_id", "tier_id"])
def test_smtf46_version_source_path_binding_before_arithmetic(source, field):
    raw = canonical(source)
    binding = raw["children"][0]["subject"]["binding"]
    (binding["path"] if field == "tier_id" else binding)[field] = str(uuid4())
    bad(reseal_wire(raw))


@pytest.mark.parametrize(
    "field,value", [("kind", "METHOD"), ("feature_term_id", str(uuid4()))], ids=["kind", "identity"]
)
def test_smtf47_exact_target_identity_not_uuid_only(source, field, value):
    raw = canonical(source)
    raw["request"]["target"][field] = value
    bad(raw)


@pytest.mark.parametrize("kind", ["INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"])
def test_smtf48_five_independent_kinds(kind):
    r = derive(make_cohort(kind=kind))
    assert r.coordinate.target.kind == kind and r.value is not None


def test_smtf48_no_sixth_main_protein_kind(source):
    raw = canonical(source)
    raw["request"]["target"]["kind"] = "MAIN_PROTEIN"
    bad(raw)


def test_smtf49_diagnostic_probe_cannot_mint_presence(source):
    raw = canonical(source)
    chosen = next(
        t for t in raw["children"][0]["targets"] if t["proof"]["target"] == raw["request"]["target"]
    )
    chosen["proof"]["role"] = "DIAGNOSTIC_ONLY"
    bad(reseal_wire(raw))
    assert all(len(ch.targets) == 5 for ch in source.children)


def test_smtf50_child_dimensions_must_equal_root_construction(source):
    raw = canonical(source)
    raw["children"][0]["sources"]["request"]["projection_request"]["requested_dimensions"] = [
        "METHOD"
    ]
    bad(reseal_wire(raw))


@pytest.mark.parametrize(
    "field", ["expected_policy_fingerprint", "expected_explicit_policy_fingerprint"]
)
def test_smtf51_child_configuration_revalidated(source, field):
    raw = canonical(source)
    q = raw["children"][0]["sources"]["request"]
    (q if field == "expected_policy_fingerprint" else q["member_interpretation"])[field] = "0" * 64
    bad(reseal_wire(raw))


def test_smtf52_no_missing_policy_fallback(source):
    raw = canonical(source)
    raw["request"].pop("policy")
    bad(raw, code="POLICY_MISSING")


@pytest.mark.parametrize("field", ["expected_policy_id", "expected_policy_version"])
def test_smtf53_exact_root_policy_pins(source, field):
    raw = canonical(source)
    raw["request"][field] = "other"
    bad(raw, code="POLICY_VERSION_MISMATCH")


def test_smtf54_changed_body_requires_independent_pin(source):
    raw = canonical(source)
    raw["request"]["policy"]["member_weights"][0]["weight"]["numerator"] += 1
    bad(raw, code="POLICY_FINGERPRINT_MISMATCH")


def test_smtf55_new_coherent_authored_policy_conditional_only(source):
    changed = policy_source(source, policy_version="2")
    r = derive(changed)
    assert r.policy_authority == "EXPLICIT_INTERPRETATION_INPUT_ONLY"
    assert r.value.amount == derive(source).value.amount
    assert r.coordinate != derive(source).coordinate


@pytest.mark.parametrize("location", ["request", "policy", "child"])
def test_smtf56_unknown_contract_versions(source, location):
    raw = canonical(source)
    body = (
        raw["request"]
        if location == "request"
        else raw["request"]["policy"]
        if location == "policy"
        else raw["children"][0]
    )
    body["contract_version"] = "future.v2"
    bad(raw)


def unadmitted(source):
    ch = source.children[0]
    p = ch.sources.request.policy.model_copy(update=dict(policy_version="unadmitted"))
    new = child_derive(with_policy(ch.sources, p))
    return pack((new,) + source.children[1:], source.request.target, source.request.policy)


def test_smtf57_valid_unadmitted_policy_is_not_forgery(source):
    r = derive(unadmitted(source))
    withheld(r)
    assert r.compatibility.status == "INCOMPATIBLE" and "POLICY_INCOMPATIBLE" in r.reasons


def test_smtf58_equal_numeric_amount_different_policy_not_compatible(source):
    new = unadmitted(source)
    assert (
        target_row(new.children[0], new).value.amount
        == target_row(source.children[0], source).value.amount
    )
    withheld(derive(new))


def test_smtf58_same_policy_id_version_different_full_body_not_compatible(source):
    ch = source.children[0]
    p = ch.sources.request.policy
    p = p.model_copy(
        update=dict(provenance=p.provenance.model_copy(update=dict(external_record_id=uuid4().hex)))
    )
    changed = child_derive(with_policy(ch.sources, p))
    assert (p.policy_id, p.policy_version) == (
        ch.sources.request.policy.policy_id,
        ch.sources.request.policy.policy_version,
    )
    assert target_row(changed, source).value.amount == target_row(ch, source).value.amount
    r = derive(pack((changed,) + source.children[1:], source.request.target, source.request.policy))
    withheld(r)
    assert "POLICY_INCOMPATIBLE" in r.reasons


def missing_bridge(source):
    rules = [r for r in source.request.policy.bridge_rules if r.direct_signal != "DECLARED_DISLIKE"]
    return policy_source(source, bridge_rules=rules)


def test_smtf59_same_child_policy_body_still_needs_bridge(source):
    r = derive(missing_bridge(source))
    withheld(r)
    assert "BRIDGE_RULE_NOT_FOUND" in r.reasons


@pytest.mark.parametrize(
    "change", ["source_coordinate", "source_amount", "source_mode", "semantic_state"]
)
def test_smtf60_smtf61_smtf62_smtf63_complete_mapping_identity(source, change):
    raw = canonical(source)
    row = next(
        r for r in raw["children"][0]["targets"] if r["proof"]["target"] == raw["request"]["target"]
    )
    if change == "source_coordinate":
        row["mapping"][change]["explicit_policy_fingerprint"] = "f" * 64
    elif change == "source_amount":
        row["mapping"][change]["numerator"] = 0
    elif change == "source_mode":
        row["mapping"][change] = "EXACT_TARGET_EFFECTIVE"
    else:
        row["mapping"][change] = "NO_DECLARATION"
    bad(reseal_wire(raw))


def test_smtf64_direct_signal_is_exact_bridge_key(source):
    body = policy_body(source)
    body["bridge_rules"][0]["direct_signal"] = "NONE"
    with pytest.raises(ValueError, match="BRIDGE_DIRECT_SIGNAL_MISMATCH"):
        c.SharedMemberTargetTasteFitPolicy.model_validate(body)


def test_smtf65_detached_mapping_rejected(source):
    body = policy_body(source)
    body["bridge_rules"][0]["mapping"]["source_amount"]["numerator"] += 11
    with pytest.raises(ValueError):
        c.SharedMemberTargetTasteFitPolicy.model_validate(body)


@pytest.mark.parametrize("alter", [False, True])
def test_smtf66_duplicate_or_contradictory_admission(source, alter):
    body = policy_body(source)
    row = deepcopy(body["policy_admissions"][0])
    if alter:
        row["expected_policy_fingerprint"] = "0" * 64
    body["policy_admissions"].append(row)
    with pytest.raises(ValueError):
        c.SharedMemberTargetTasteFitPolicy.model_validate(body)


def test_smtf67_equivalent_fraction_duplicate_key(source):
    body = policy_body(source)
    rule = deepcopy(body["bridge_rules"][0])
    rule["rule_id"] = "another"
    for field in ("source_amount", "fit_amount"):
        for part in ("numerator", "denominator"):
            rule["mapping"][field][part] *= 2
    body["bridge_rules"].append(rule)
    with pytest.raises(ValueError, match="Duplicate"):
        c.SharedMemberTargetTasteFitPolicy.model_validate(body)


@pytest.mark.parametrize("duplicate", ["id", "key"])
def test_smtf68_no_first_or_last_rule_wins(source, duplicate):
    body = policy_body(source)
    if duplicate == "id":
        body["bridge_rules"][1]["rule_id"] = body["bridge_rules"][0]["rule_id"]
    else:
        body["bridge_rules"].append(deepcopy(body["bridge_rules"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        c.SharedMemberTargetTasteFitPolicy.model_validate(body)


def test_smtf69_policy_mapping_kind_exact(source):
    body = policy_body(source)
    body["bridge_rules"][0]["target_kind"] = "METHOD"
    with pytest.raises(ValueError):
        c.SharedMemberTargetTasteFitPolicy.model_validate(body)


@pytest.mark.parametrize(
    "signal,number", [("DECLARED_LIKE", -1), ("DECLARED_DISLIKE", 1), ("DECLARED_NEUTRAL", 1)]
)
def test_smtf70_smtf71_smtf72_fit_sign_and_zero_preserved(source, signal, number):
    body = policy_body(source)
    rule = next(r for r in body["bridge_rules"] if r["direct_signal"] == signal)
    rule["mapped_amount"] = dict(numerator=number, denominator=2)
    with pytest.raises(ValueError, match="BRIDGE_FIT_SIGN_MISMATCH"):
        c.SharedMemberTargetTasteFitPolicy.model_validate(body)


def test_smtf73_no_interpolation_identity_or_zero_fallback(source):
    r = derive(missing_bridge(source))
    withheld(r)
    assert r.coverage.available_count == 2 and r.coverage.compatible_count == 1


def test_smtf74_independent_exact_rational_reference(source):
    r = derive(source)
    expected = sum(
        (
            Fraction(v.authored_weight.weight.numerator, v.authored_weight.weight.denominator)
            * Fraction(
                v.selected_bridge.mapped_amount.numerator,
                v.selected_bridge.mapped_amount.denominator,
            )
            for v in r.contributions
        ),
        Fraction(0),
    )
    total = sum(
        (
            Fraction(w.weight.numerator, w.weight.denominator)
            for w in source.request.policy.member_weights
        ),
        Fraction(0),
    )
    assert Fraction(r.value.amount.numerator, r.value.amount.denominator) == expected / total
    assert Fraction(r.weighted_total.numerator, r.weighted_total.denominator) == expected


def test_smtf74_weighted_products_unbounded_but_final_fit_bounded(source):
    weights = {ch.subject.member_id: 100 for ch in source.children}
    r = derive(
        replace_policy(
            source, authored_policy(source.children, source.request.target, weights=weights)
        )
    )
    assert r.weight_total.numerator == 200
    assert all(
        abs(v.weighted_contribution.numerator) > v.weighted_contribution.denominator
        for v in r.contributions
    )
    assert abs(r.value.amount.numerator) <= r.value.amount.denominator
    assert all(v.weighted_contribution.coordinate == r.coordinate for v in r.contributions)


def test_smtf75_single_member_has_new_descriptor_and_bridge():
    s = make_cohort(states=("LIKE",))
    r = derive(s)
    assert r.value.amount == c.SharedTargetTasteFitAmount(numerator=2, denominator=3)
    assert r.value.coordinate != r.contributions[0].original_value.coordinate
    assert r.weight_total.numerator == 2


def test_smtf76_missing_weight_rejected_even_unavailable():
    s = make_cohort(states=("LIKE", "UNDECLARED"))
    raw = canonical(s)
    raw["request"]["policy"]["member_weights"].pop()
    bad(raw)


@pytest.mark.parametrize("mode", ["duplicate", "extra"])
def test_smtf77_duplicate_extra_weights_reject(source, mode):
    body = policy_body(source)
    weight = deepcopy(body["member_weights"][0])
    if mode == "extra":
        weight["member_id"] = uuid4()
    body["member_weights"].append(weight)
    with pytest.raises(ValueError):
        replace_policy(source, c.SharedMemberTargetTasteFitPolicy.model_validate(body))


@pytest.mark.parametrize(
    "n,d",
    [
        (0, 1),
        (-1, 1),
        (True, 1),
        (1.0, 1),
        (1, False),
        (1, 0),
        (1, -1),
        (1, 0.5),
        (float("inf"), 1),
    ],
)
def test_smtf78_strict_authored_rationals(n, d):
    with pytest.raises(ValueError):
        c.SharedTasteFitWeight(numerator=n, denominator=d)


@pytest.mark.parametrize(
    "n,d", [(True, 1), (0.1, 1), (1, False), (1, 0), (2, 1), (float("inf"), 1)]
)
def test_smtf78_amounts_strict_and_bounded(n, d):
    with pytest.raises(ValueError):
        c.SharedTargetTasteFitAmount(numerator=n, denominator=d)


def test_smtf79_smtf80_portions_and_roles_not_weights(source):
    r = derive(source)
    members = source.request.projection_request.grounding_request.participants.participants
    assert {p.nutrition_role for p in members} == {"TRACKED", "SHARED"}
    assert all(v.authored_weight in source.request.policy.member_weights for v in r.contributions)
    assert [v.weight.numerator for v in source.request.policy.member_weights] == [2, 1]
    assert {str(p.portion_factor) for p in members} == {"1", "0.5"}


def test_smtf81_ordinal_strength_retained_not_multiplier(source):
    r = derive(source)
    assert all(v.diagnostic.row.evidence_strength.level == "LOW" for v in r.contributions)
    test_smtf74_independent_exact_rational_reference(source)


def add_hidden_history(ch):
    body = canonical(ch.sources)
    ledger = body["member_sources"]["entries"][0]["explicit"]["source"]["preferences"]
    cmd = command(
        household_id=ch.subject.household_id,
        member_id=ch.subject.member_id,
        actor_user_id=ch.sources.candidate_frame.actor_user_id,
    )
    fact = declaration(cmd, sequence=ledger["frontier"] + 1)
    ledger["declarations"].append(canonical(fact))
    ledger["frontier"] += 1
    for entry in body["member_sources"]["entries"]:
        entry["explicit"]["source"]["preferences"] = deepcopy(ledger)
    return child_derive(seal(child.CandidateMemberTasteFitSources.model_validate(body)))


def test_smtf82_smtf105_history_changes_identity_not_member_influence(source):
    children = (add_hidden_history(source.children[0]),) + source.children[1:]
    new = pack(children, source.request.target, source.request.policy)
    a, b = derive(source), derive(new)
    assert a.value.amount == b.value.amount and a.weight_total.numerator == b.weight_total.numerator
    assert a.fingerprint != b.fingerprint and a.coordinate != b.coordinate


def test_smtf83_smtf107_new_set_order_normalizes_frozen_order_preserved(source):
    raw = canonical(source)
    raw["children"].reverse()
    raw["owner_frames"].reverse()
    raw["request"]["members"].reverse()
    for key in ("member_weights", "bridge_rules", "policy_admissions"):
        raw["request"]["policy"][key].reverse()
    assert validate(derive(raw)) == derive(source)
    assert (
        derive(raw).cohort.participants
        == source.request.projection_request.grounding_request.participants
    )


def test_smtf84_rescaled_weights_same_amount_different_scope(source):
    body = policy_body(source)
    for w in body["member_weights"]:
        w["weight"]["numerator"] *= 7
    a, b = (
        derive(source),
        derive(replace_policy(source, c.SharedMemberTargetTasteFitPolicy.model_validate(body))),
    )
    assert a.value.amount == b.value.amount
    with pytest.raises(ValueError, match="descriptor"):
        a.value.scoped_numeric_equal(b.value)
    assert abs(b.weighted_total.numerator) > 1 or b.weighted_total.numerator == 0


def test_smtf85_cancellation_is_not_neutral_declaration(source):
    weights = {
        ch.subject.member_id: 2 if target_row(ch, source).direct_signal == "DECLARED_DISLIKE" else 1
        for ch in source.children
    }
    r = derive(
        replace_policy(
            source, authored_policy(source.children, source.request.target, weights=weights)
        )
    )
    assert r.value.amount.numerator == 0 and r.aggregate_availability == "AVAILABLE"
    assert {s.direct_signal for s in r.direct_signals} == {"DECLARED_LIKE", "DECLARED_DISLIKE"}


def test_smtf86_available_zero_unavailable_none_wire_distinct():
    zero, missing = (
        derive(make_cohort(states=("NEUTRAL",))),
        derive(make_cohort(states=("UNDECLARED",))),
    )
    assert validate(canonical(zero)).value.amount.numerator == 0
    assert validate(canonical(missing)).value is None


def test_smtf87_all_zero_keeps_every_weight():
    r = derive(make_cohort(states=("NEUTRAL", "NEUTRAL")))
    assert r.value.amount.numerator == 0 and r.value.amount.denominator == 1
    assert len(r.contributions) == 2 and r.weight_total.numerator == 3


def test_smtf88_unavailable_member_no_new_subtotal():
    r = derive(make_cohort(states=("LIKE", "UNDECLARED")))
    withheld(r)
    assert r.coverage.required_count == 2 and r.coverage.available_count == 1


def test_smtf89_smtf95_retraction_suppresses_not_neutral():
    r = derive(make_cohort(states=("LIKE", "RETRACTED")))
    withheld(r)
    assert "MEMBER_RETRACTED" in r.reasons and "SUPPRESSED" in r.reasons
    assert len([s for s in r.direct_signals if s.direct_signal == "NONE"]) == 1


def test_smtf90_child_unmapped_is_distinct_from_bridge_unmapped(source):
    ch = source.children[0]
    body = ch.sources.request.policy.model_dump()
    for group in body["kind_policies"]:
        group["mappings"] = [m for m in group["mappings"] if m["semantic_state"] == "NEUTRAL"]
    p = child.TasteFitInterpretationPolicy.model_validate(body)
    children = tuple(child_derive(with_policy(ch.sources, p)) for ch in source.children)
    s = pack(children, source.request.target)
    r = derive(s)
    withheld(r)
    assert "CHILD_FIT_UNMAPPED" in r.reasons and "BRIDGE_RULE_NOT_FOUND" not in r.reasons
    assert "BRIDGE_RULE_NOT_FOUND" in derive(missing_bridge(source)).reasons


def test_smtf91_all_required_ids_reasons_retained():
    r = derive(make_cohort(states=("LIKE", "UNDECLARED", "RETRACTED")))
    withheld(r)
    assert r.coverage.required_count == r.coverage.captured_count == 3
    assert {"PARTICIPANT_COVERAGE_INCOMPLETE", "MEMBER_UNDECLARED", "MEMBER_RETRACTED"} <= set(
        r.reasons
    )


@pytest.mark.parametrize("outcome", ["positive", "zero", "unavailable"])
def test_smtf92_dislike_survives_every_aggregate_outcome(source, outcome):
    weights = {
        ch.subject.member_id: (2 if outcome == "zero" else 1)
        if target_row(ch, source).direct_signal == "DECLARED_DISLIKE"
        else (1 if outcome == "zero" else 10)
        for ch in source.children
    }
    s = replace_policy(
        source, authored_policy(source.children, source.request.target, weights=weights)
    )
    r = derive(missing_bridge(s) if outcome == "unavailable" else s)
    assert len(r.direct_dislikes) == 1 and r.direct_dislikes[0].declaration_id is not None
    if outcome == "positive":
        assert r.value.amount.numerator > 0
    elif outcome == "zero":
        assert r.value.amount.numerator == 0
    else:
        withheld(r)


@pytest.mark.parametrize("inherited", [False, True])
def test_smtf93_smtf94_unfavorable_prior_inheritance_not_direct_dislike(inherited):
    s = make_cohort(states=("UNDECLARED",))
    source = with_member_modes(
        s.children[0].sources,
        prior_amount=(-1, 1),
        hierarchy=inherited,
        undeclared="ONE_HOP_INHERITED" if inherited else "PRIOR_ONLY",
        parent_value="DISLIKE",
    )
    r = derive(pack((child_derive(source),), s.request.target))
    assert r.value.amount.numerator < 0 and not r.direct_dislikes
    assert r.contributions[0].diagnostic.row.evidence_strength.level == "NONE"


def test_smtf96_grounding_safety_cannot_be_favorable_fit_rescue(source):
    raw = canonical(source)
    raw["children"][0]["sources"]["projection"]["source"]["grounded_candidate"]["sources"][
        "member_safety"
    ][0]["constraints"] = [dict(kind="ALLERGEN", code="fiction")]
    bad(raw)


def test_smtf97_only_current_direct_heads_retained(source):
    r = derive(source)
    for signal in r.direct_signals:
        raw = signal.row.member_views.explicit.raw_state
        assert (signal.direct_signal, signal.declaration_id) == (
            "DECLARED_" + raw.value,
            raw.declaration_id,
        )


@pytest.mark.parametrize("field", ["reason", "direct_signal", "evidence_strength", "value"])
def test_smtf98_full_unselected_child_replay_not_only_outer_row(source, field):
    raw = canonical(source)
    row = next(r for r in raw["children"][0]["targets"] if r["proof"]["target"]["kind"] == "METHOD")
    if field == "value":
        row[field]["amount"]["numerator"] = 0
    elif field == "evidence_strength":
        row[field]["level"] = "HIGH"
    else:
        row[field] = "forged"
    bad(reseal_wire(raw))


def test_smtf99_construct_copy_are_untrusted(source):
    bad(source.model_copy(update=dict(fingerprint="0" * 64)))
    request = source.request.model_copy(update=dict(expected_policy_fingerprint="0" * 64))
    forged = c.SharedMemberTargetTasteFitSources.model_construct(
        **(source.model_dump() | dict(request=request))
    )
    with pytest.warns(UserWarning, match="serializer warnings"):
        bad(forged)


@pytest.mark.parametrize(
    "field,value",
    [
        ("common_mvcc", "CLAIMED"),
        ("source_origin", "CANONICAL_DATABASE"),
        ("policy_authority", "GLOBAL"),
    ],
)
def test_smtf100_rehashed_fiction_no_authority(source, field, value):
    raw = canonical(derive(source))
    raw[field] = value
    bad(raw, validate)


def test_smtf100_candidate_and_member_frame_require_same_owner_session(source):
    children = []
    for ch in source.children:
        s = ch.sources
        frame = s.candidate_frame.model_copy(update=dict(session_user="different.root.session"))
        # Frozen child validity is not proof that the enclosing owner cut agrees.
        children.append(child_derive(seal(s.model_copy(update=dict(candidate_frame=frame)))))
    bad(pack(children, source.request.target, source.request.policy), code="SOURCE_CUT_INCOHERENT")


def test_smtf101_overlapping_owner_reader_conflict_rejects():
    s = make_cohort(states=("UNDECLARED",))
    ch = child_derive(with_member_modes(s.children[0].sources))
    # Frozen child independently validates protected reader/frame agreements.
    raw = canonical(pack((ch,), s.request.target))
    entry = next(
        e for e in raw["children"][0]["sources"]["member_sources"]["entries"] if e["exact_target"]
    )
    entry["exact_target"]["reference_source"]["reader_grant_id"] = str(uuid4())
    bad(reseal_wire(raw))


def test_smtf102_global_typed_identity_registry_ignores_mutable_ingredient_labels(source):
    from app.modules.catalog.contracts import IngredientIdentityFact
    from app.modules.recipes.contracts import RecipeFact

    recipe = source.children[0].sources.projection.source.feature_input.recipe.recipe
    changed = recipe.model_copy(update=dict(name="Conflicting immutable owner name"))
    with pytest.raises(ResolutionError, match="Conflicting"):
        core._owner_identities((recipe, changed))
    # Same UUID in another owner type is not the same immutable typed identity.
    ingredient = IngredientIdentityFact(id=recipe.id, name="Mutable")
    core._owner_identities((recipe, ingredient, ingredient.model_copy(update=dict(name="Renamed"))))
    assert isinstance(recipe, RecipeFact)


def test_smtf102_individually_valid_children_conflicting_unselected_typed_term(source):
    from preference_fixtures import term

    fact = term("METHOD")
    children = []
    for i, ch in enumerate(source.children):
        body = canonical(ch.sources)
        ledger = body["member_sources"]["entries"][0]["explicit"]["source"]["preferences"]
        different = (
            fact if i == 0 else fact.model_copy(update=dict(label="Conflicting immutable term"))
        )
        cmd = command(
            household_id=ch.subject.household_id,
            member_id=ch.subject.member_id,
            actor_user_id=ch.sources.candidate_frame.actor_user_id,
            target=dict(kind="METHOD", feature_term_id=fact.id),
        )
        ledger["declarations"].append(canonical(declaration(cmd, sequence=ledger["frontier"] + 1)))
        ledger["frontier"] += 1
        ledger["feature_terms"].append(canonical(different))
        for entry in body["member_sources"]["entries"]:
            entry["explicit"]["source"]["preferences"] = deepcopy(ledger)
        children.append(
            child_derive(seal(child.CandidateMemberTasteFitSources.model_validate(body)))
        )
    # Both complete frozen children are valid; the enclosing cohort must reject.
    bad(pack(children, source.request.target, source.request.policy), code="SOURCE_CUT_INCOHERENT")


def shift_read_clocks(ch):
    p = ch.sources.projection.source
    delta = timedelta(microseconds=1)
    p = seal_projection_source(
        p.model_copy(
            update=dict(
                capture_started_at=p.capture_started_at + delta,
                capture_completed_at=p.capture_completed_at + delta,
                feature_input=p.feature_input.model_copy(
                    update=dict(captured_at=p.feature_input.captured_at + delta)
                ),
            )
        )
    )
    from app.modules.planning.candidate_feature_projection import project_candidate_features

    return child_derive(
        seal(ch.sources.model_copy(update=dict(projection=project_candidate_features(p))))
    )


def test_smtf103_smtf104_exact_read_clock_allowlist_changes_full_identity(source):
    changed = shift_read_clocks(source.children[0])
    s = pack((changed,) + source.children[1:], source.request.target, source.request.policy)
    a, b = derive(source), derive(s)
    assert a.cohort.integrity_projection_fingerprint == b.cohort.integrity_projection_fingerprint
    assert a.value.amount == b.value.amount and a.coordinate != b.coordinate
    assert a.sources.fingerprint != b.sources.fingerprint


def test_smtf103_review_source_clock_cannot_be_normalized_away(source):
    ch = source.children[0]
    projection = ch.sources.projection.source
    feature = projection.feature_input
    scopes = list(feature.sources.scopes)
    review = scopes[0].reviews[0]
    scopes[0] = scopes[0].model_copy(
        update=dict(
            reviews=(
                review.model_copy(
                    update=dict(recorded_at=review.recorded_at + timedelta(microseconds=1))
                ),
            )
        )
    )
    feature = feature.model_copy(
        update=dict(sources=feature.sources.model_copy(update=dict(scopes=tuple(scopes))))
    )
    projection = seal_projection_source(projection.model_copy(update=dict(feature_input=feature)))
    from app.modules.planning.candidate_feature_projection import project_candidate_features

    changed = child_derive(
        seal(ch.sources.model_copy(update=dict(projection=project_candidate_features(projection))))
    )
    bad(
        pack((changed,) + source.children[1:], source.request.target, source.request.policy),
        code="SOURCE_CUT_INCOHERENT",
    )


def test_smtf106_unavailable_states_and_policy_full_identity():
    a = make_cohort(states=("UNDECLARED",))
    b = policy_source(a, policy_version="2")
    x, y = derive(a), derive(b)
    withheld(x)
    withheld(y)
    assert x.fingerprint != y.fingerprint and x.sources.fingerprint != y.sources.fingerprint


@pytest.mark.parametrize(
    "field",
    [
        "value",
        "weight_total",
        "weighted_total",
        "coverage",
        "compatibility",
        "direct_signals",
        "coordinate",
        "reasons",
    ],
)
def test_smtf108_complete_semantic_validation_returns_fresh(source, field):
    r = derive(source)
    assert validate(r) == r and validate(r) is not r
    raw = canonical(r)
    if field in {"value", "weight_total", "weighted_total"}:
        target = raw[field]["amount"] if field == "value" else raw[field]
        target["numerator"] += 1
    elif field == "coverage":
        raw[field]["available_count"] = 0
    elif field == "compatibility":
        raw[field]["reasons"] = ["fiction"]
    elif field == "direct_signals":
        raw[field] = []
    elif field == "coordinate":
        raw[field]["retained_cohort_fingerprint"] = "f" * 64
    else:
        raw[field] = ["fiction"]
    raw["fingerprint"] = c.shared_tastefit_hash(
        "shared-target.result.v1", {k: v for k, v in raw.items() if k != "fingerprint"}
    )
    bad(raw, validate)


def test_smtf109_actual_public_interface_zero_io(source, monkeypatch):
    import builtins
    import socket

    from sqlalchemy.orm import Session

    def forbidden(*a, **kw):
        raise AssertionError("Pure replay attempted I/O")

    with monkeypatch.context() as m:
        m.setattr(builtins, "open", forbidden)
        m.setattr(socket, "socket", forbidden)
        m.setattr(Session, "execute", forbidden)
        assert validate(derive(source)).sources == source


def test_smtf110_no_environment_policy_or_mutable_cache(source, monkeypatch):
    monkeypatch.setenv("MENUTO_SHARED_TASTEFIT_DEFAULT_POLICY", "fiction")
    assert derive(source).sources.request.policy == source.request.policy
    raw = canonical(source)
    raw["request"]["policy"] = None
    bad(raw, code="POLICY_MISSING")


@pytest.mark.parametrize("mismatch", ["coverage", "policy", "bridge", "context"])
def test_smtf111_mismatch_before_new_reduction(source, monkeypatch, mismatch):
    def forbidden(*a, **kw):
        raise AssertionError("New arithmetic entered before global compatibility gate")

    monkeypatch.setattr(core, "_reduce", forbidden)
    if mismatch == "coverage":
        s = make_cohort(states=("LIKE", "UNDECLARED"))
    elif mismatch == "policy":
        s = unadmitted(source)
    elif mismatch == "bridge":
        s = missing_bridge(source)
    else:
        raw = canonical(source)
        raw["request"]["projection_request"]["expected_grounding_fingerprint"] = "f" * 64
        bad(raw)
        return
    withheld(derive(s))


@pytest.mark.parametrize(
    "field", ["max_members", "max_policy_bytes", "max_source_bytes", "max_result_bytes"]
)
def test_smtf112_complete_authored_resource_budgets(source, field):
    raw = canonical(source)
    raw["request"]["policy"][field] = 1
    p = raw["request"]["policy"]
    raw["request"]["expected_policy_fingerprint"] = c.shared_tastefit_hash(
        "shared-target.policy.v1", p
    )
    bad(reseal_wire(raw), code="RESOURCE_LIMIT")


def test_smtf113_integer_and_intermediate_budget_no_truncation(source):
    raw = canonical(source)
    raw["request"]["policy"]["member_weights"][0]["weight"]["numerator"] = 1 << 300
    bad(raw, code="RESOURCE_LIMIT")
    with pytest.raises(ResolutionError, match="product budget"):
        core._multiply(Fraction((1 << 40) - 1, 1), Fraction((1 << 39) - 1, (1 << 40) - 3), 64)


@pytest.mark.parametrize(
    "field", ["target", "retained_cohort_fingerprint", "aggregation_policy_fingerprint"]
)
def test_smtf114_stripped_or_forged_descriptors_fail(source, field):
    r = derive(source)
    raw = canonical(r)
    coord = raw["contributions"][0]["common_operand"]["coordinate"]
    if field == "target":
        coord["target"]["feature_term_id"] = str(uuid4())
    else:
        coord[field] = "f" * 64
    bad(raw, validate)
    with pytest.raises(ValueError):
        c.ScopedSharedMemberTargetTasteFit.model_validate(dict(amount=r.value.amount))


@pytest.mark.parametrize(
    "field", ["targets", "overall_fit", "shared_meal_utility", "candidate_rank"]
)
def test_smtf115_no_cross_target_kind_or_whole_candidate_scalar(source, field):
    raw = canonical(source)
    raw["request"][field] = []
    bad(raw)


@pytest.mark.parametrize(
    "field",
    [
        "household_id",
        "participant_context_fingerprint",
        "retained_cohort_fingerprint",
        "aggregation_policy_fingerprint",
    ],
)
def test_smtf116_equality_requires_complete_scope(source, field):
    v = derive(source).value
    assert v.scoped_numeric_equal(canonical(v))
    new = v.model_copy(
        update=dict(
            coordinate=v.coordinate.model_copy(
                update={field: uuid4() if field == "household_id" else "f" * 64}
            )
        )
    )
    with pytest.raises(ValueError, match="descriptor"):
        v.scoped_numeric_equal(new)
    assert not hasattr(v, "rank")


@pytest.mark.parametrize(
    "field",
    [
        "learned_events",
        "cooked",
        "passive_assumptions",
        "forced_tradeoff",
        "operational_friction",
        "contextual_evidence",
    ],
)
def test_smtf117_no_mtr039_behavioral_operands(source, field):
    raw = canonical(source)
    raw["request"][field] = []
    bad(raw)


@pytest.mark.parametrize(
    "field", ["repeat_penalty", "novelty", "exposure_history", "recency_multiplier"]
)
def test_smtf118_history_and_novelty_never_operands(source, field):
    raw = canonical(source)
    raw["request"][field] = 1
    bad(raw)


@pytest.mark.parametrize(
    "field,value",
    [
        ("planner_ready", True),
        ("activation_ready", True),
        ("planner_ready", 0),
        ("policy_authority", "PRODUCTION"),
        ("common_mvcc", "CLAIMED"),
    ],
)
def test_smtf119_non_authority_literals_cannot_promote(source, field, value):
    raw = canonical(derive(source))
    raw[field] = value
    bad(raw, validate)
