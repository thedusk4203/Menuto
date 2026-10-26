"""Approved acceptance cases 01–68 through the exact-target pure consumer interface."""

import ast
import json
from copy import deepcopy
from datetime import timedelta
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest
from app.modules.preferences import prior_affinity_contracts as c
from app.modules.preferences.contracts import _profile_hash
from app.modules.preferences.prior_affinity import (
    _blend,
)
from app.modules.preferences.prior_affinity import (
    derive_exact_target_prior_backed_affinity as derive,
)
from prior_shrinkage_fixtures import (
    KINDS,
    consumer_input,
    reference_source,
    shrinkage,
)
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def base():
    return consumer_input()


@pytest.fixture(scope="module")
def draft(base):
    return derive(base)


def amount(value):
    return Fraction(value.amount.numerator, value.amount.denominator)


def policy_data(base):
    return base.compatibility_policy.model_dump()


def rebind(base, data, **shrinkage_kw):
    policy = c.ExactTargetPriorCompatibilityPolicy.model_validate(data)
    weights = shrinkage(policy, **shrinkage_kw).model_dump()
    weights["provenance"] = base.shrinkage_policy.provenance
    return c.ExactTargetPriorBackedAffinityInput.model_validate(
        base.model_dump() | dict(compatibility_policy=policy, shrinkage_policy=weights)
    )


def rehashed_result(draft, mutate):
    data = draft.model_dump()
    mutate(data)
    forged = c.ExactTargetPriorBackedAffinityDraft.model_construct(**data)
    data["fingerprint"] = forged.expected_fingerprint()
    return data


def test_c01_source_fractions_have_no_automatic_conversion(base, draft):
    # Raw explicit LIKE is 3/5, reviewed prior is 1/2; authored outputs are 3/4, 1/4.
    assert amount(draft.mapped_explicit.value) == Fraction(3, 4)
    assert amount(draft.mapped_prior.value) == Fraction(1, 4)
    assert amount(draft.effective.value) == Fraction(1, 2)
    with pytest.raises(ValidationError):
        c.ScopedMemberProfileAffinity.model_validate(
            base.reference_source.publications[0].command.amount
        )


@pytest.mark.parametrize("name,new", [("policy_id", "other"), ("policy_version", "other")])
def test_c02_c03_explicit_policy_identity_version(base, name, new):
    data = base.model_dump()
    data["compatibility_policy"]["explicit_" + name] = new
    with pytest.raises(ValidationError, match="Pinned explicit policy"):
        c.ExactTargetPriorBackedAffinityInput.model_validate(data)


def test_c04_explicit_policy_fingerprint(base):
    data = base.model_dump()
    data["compatibility_policy"]["explicit_policy_fingerprint"] = "f" * 64
    with pytest.raises(ValidationError, match="Pinned explicit policy"):
        derive(data)


def test_c05_all_explicit_amount_bindings(base):
    data = policy_data(base)
    data["explicit_maps"][0]["rows"][0]["expected_explicit_amount"]["numerator"] = -1
    with pytest.raises(ValidationError, match="Expected explicit mapping"):
        rebind(base, data)


@pytest.mark.parametrize("duplicate", [False, True])
def test_c06_missing_duplicate_explicit_mapping(base, duplicate):
    data = policy_data(base)
    rows = list(data["explicit_maps"][0]["rows"])
    data["explicit_maps"][0]["rows"] = rows[:2] if not duplicate else [rows[0]] * 3
    with pytest.raises(ValidationError):
        c.ExactTargetPriorCompatibilityPolicy.model_validate(data)


def test_c07_explicit_mapping_order(base):
    data = policy_data(base)
    data["explicit_maps"][0]["rows"][0]["output_amount"] = dict(numerator=1, denominator=1)
    with pytest.raises(ValidationError, match="Mapped DISLIKE"):
        c.ExactTargetPriorCompatibilityPolicy.model_validate(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("coordinate_id", "MEMBER_PROFILE_AFFINITY"),
        ("coordinate_version", 2),
        ("unit", "POLICY_MEMBER_PROFILE_AFFINITY_UNITS"),
        ("applicability", "MEMBER"),
    ],
)
def test_c08_reference_coordinate_is_closed(base, field, value):
    data = policy_data(base)
    data["reference_coordinate"][field] = value
    with pytest.raises(ValidationError):
        c.ExactTargetPriorCompatibilityPolicy.model_validate(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("provider_id", str(uuid4())),
        ("provider_command_hash", "f" * 64),
    ],
)
def test_c09_provider_immutable_binding(base, field, value):
    data = policy_data(base)
    data[field] = value
    with pytest.raises(ValidationError, match="provider command"):
        rebind(base, data)


@pytest.mark.parametrize("field", ["providers", "fallback_provider", "provider_weights"])
def test_c10_provider_aggregation_not_in_contract(base, field):
    with pytest.raises(ValidationError):
        rebind(base, policy_data(base) | {field: []})


def test_c11_empty_reference_group_is_explicitly_unmapped_duplicate_rejects(base):
    data = policy_data(base)
    for group in data["reference_maps"]:
        group["rows"] = ()
    result = derive(rebind(base, data))
    assert result.mapped_prior.reason == "PRIOR_VALUE_NOT_MAPPED"
    assert result.effective.mode == "EXPLICIT_ONLY"
    data = policy_data(base)
    rows = list(data["reference_maps"][0]["rows"])
    data["reference_maps"][0]["rows"] = rows + rows[:1]
    with pytest.raises(ValidationError):
        c.ExactTargetPriorCompatibilityPolicy.model_validate(data)


@pytest.mark.parametrize("plateau", [False, True])
def test_c12_reference_mapping_strict_order(base, plateau):
    data = policy_data(base)
    rows = data["reference_maps"][0]["rows"]
    rows[1]["output_amount"] = rows[0 if plateau else -1]["output_amount"]
    with pytest.raises(ValidationError, match="strictly increasing"):
        c.ExactTargetPriorCompatibilityPolicy.model_validate(data)


@pytest.mark.parametrize("unmapped", [(1, 3), (2, 3), (-1, 2)])
def test_c13_no_reference_interpolation(unmapped):
    result = derive(consumer_input(amount=unmapped))
    assert result.mapped_prior.reason == "PRIOR_VALUE_NOT_MAPPED"
    assert result.reviewed_prior.rows[0].status == "AVAILABLE"
    assert result.effective.mode == "EXPLICIT_ONLY"


def test_c14_no_publication_does_not_synthesize_zero():
    result = derive(consumer_input(member="UNDECLARED", prior="NO_PUBLICATION"))
    assert result.mapped_prior.reason == "NO_PUBLICATION"
    assert result.effective.status == "UNAVAILABLE"
    assert not hasattr(result.effective, "value")


def test_c15_prior_retracted_does_not_reuse_amount():
    result = derive(consumer_input(prior="RETRACTED"))
    assert result.reviewed_prior.rows[0].tombstone.command.operation == "RETRACT"
    assert result.mapped_prior.reason == "RETRACTED"
    assert result.effective.mode == "EXPLICIT_ONLY"


def test_c16_real_available_zero():
    result = derive(consumer_input(member="UNDECLARED", amount=(0, 1)))
    assert result.effective.mode == "PRIOR_ONLY_COLD_START"
    assert amount(result.mapped_prior.value) == amount(result.effective.value) == 0


def test_c17_undeclared_distinct_from_neutral():
    undeclared = derive(consumer_input(member="UNDECLARED"))
    neutral = derive(consumer_input(value="NEUTRAL"))
    assert undeclared.mapped_explicit is None
    assert neutral.explicit_profile.rows[0].raw_state.status == "DECLARED"
    assert neutral.mapped_explicit.rule_key[1] == "NEUTRAL"


def test_c18_retracted_distinct_from_undeclared():
    assert derive(consumer_input(member="RETRACTED")).effective.reason == "MEMBER_RETRACTED"
    assert derive(consumer_input(member="UNDECLARED")).effective.status == "AVAILABLE"


@pytest.mark.parametrize("prior", ["AVAILABLE", "NO_PUBLICATION", "RETRACTED"])
def test_c19_member_retraction_blocks_all_prior_branches(prior):
    result = derive(consumer_input(member="RETRACTED", prior=prior))
    assert result.effective.reason == "MEMBER_RETRACTED"
    assert result.mapped_explicit is None
    assert result.explicit_profile.rows[0].evidence_strength.level == "NONE"
    assert result.contributions == () and result.shrinkage == "NOT_APPLIED"


@pytest.mark.parametrize("kind", KINDS)
def test_c20_exact_blend_all_five_kinds(kind):
    result = derive(consumer_input(kind=kind))
    assert result.target_kind == result.target.kind == kind
    assert result.effective.mode == "BLENDED_EXPLICIT_AND_PRIOR"
    assert amount(result.effective.value) == Fraction(1, 2)
    assert [amount(x.value) for x in result.contributions] == [Fraction(3, 8), Fraction(1, 8)]
    assert all(x.value.coordinate == result.coordinate for x in result.contributions)


@pytest.mark.parametrize(
    "prior,reason",
    [
        ("NO_PUBLICATION", "NO_PUBLICATION"),
        ("RETRACTED", "RETRACTED"),
        ("UNMAPPED", "PRIOR_VALUE_NOT_MAPPED"),
    ],
)
def test_c21_c22_c23_observable_explicit_only(prior, reason):
    result = derive(
        consumer_input(
            prior="AVAILABLE" if prior == "UNMAPPED" else prior,
            amount=(1, 3) if prior == "UNMAPPED" else (1, 2),
        )
    )
    assert result.effective.mode == "EXPLICIT_ONLY"
    assert result.mapped_prior.reason == reason
    assert result.effective.value == result.mapped_explicit.value
    assert result.contributions == () and result.shrinkage == "NOT_APPLIED"


def test_c24_cold_start_does_not_mint_strength():
    result = derive(consumer_input(member="UNDECLARED"))
    assert result.effective.mode == "PRIOR_ONLY_COLD_START"
    assert result.explicit_profile.rows[0].evidence_strength.level == "NONE"
    assert result.mapped_explicit is None
    assert result.effective.value == result.mapped_prior.value
    assert result.contributions == ()


@pytest.mark.parametrize(
    "prior,amount_input",
    [
        ("NO_PUBLICATION", (1, 2)),
        ("RETRACTED", (1, 2)),
        ("AVAILABLE", (1, 3)),
    ],
)
def test_c25_no_explicit_or_compatible_prior(prior, amount_input):
    result = derive(consumer_input(member="UNDECLARED", prior=prior, amount=amount_input))
    assert result.effective.reason == "NO_EXPLICIT_OR_COMPATIBLE_PRIOR"
    assert not hasattr(result.effective, "value")
    assert (
        result.coordinate.compatibility_policy_fingerprint
        == result.compatibility_policy_fingerprint
    )


def test_c26_neutral_mapping_need_not_be_zero():
    result = derive(consumer_input(value="NEUTRAL", prior="NO_PUBLICATION"))
    assert amount(result.effective.value) == Fraction(1, 4)


@pytest.mark.parametrize("invalid", [0.5, "0.9", dict(probability="0.9")])
def test_c27_strength_is_ordinal_not_probability(base, invalid):
    data = base.shrinkage_policy.model_dump()
    data["rules"][0]["level"] = invalid
    with pytest.raises(ValidationError):
        c.ExactTargetShrinkagePolicy.model_validate(data)


@pytest.mark.parametrize("duplicate", [False, True])
def test_c28_strength_rules_complete(base, duplicate):
    data = base.shrinkage_policy.model_dump()
    rows = data["rules"]
    data["rules"] = rows[:2] if not duplicate else (rows[0],) * 3
    with pytest.raises(ValidationError):
        c.ExactTargetShrinkagePolicy.model_validate(data)


@pytest.mark.parametrize(
    "n,d",
    [
        (True, 2),
        (1.0, 2),
        ("1", 2),
        (1, "2"),
        (1, True),
        (1, 0),
        (1, -2),
        (-1, 2),
        (2, 4),
        (0, 2),
        (2**31, 2**31 + 1),
    ],
)
def test_c29_malformed_weights(n, d):
    with pytest.raises(ValidationError):
        c.PriorInfluenceWeight(numerator=n, denominator=d)


def test_c30_active_weight_one_rejects():
    with pytest.raises(ValidationError):
        c.PriorInfluenceWeight(numerator=1, denominator=1)


@pytest.mark.parametrize("weights", [((0, 1), (1, 3), (0, 1)), ((1, 2), (0, 1), (1, 3))])
def test_c31_nonmonotonic_weights(base, weights):
    with pytest.raises(ValidationError, match="monotonic"):
        shrinkage(base.compatibility_policy, weights=weights)


def test_c32_zero_weight_preserves_prior_trace(base):
    result = derive(rebind(base, policy_data(base), weights=((0, 1),) * 3))
    assert result.mapped_prior.status == "AVAILABLE" and result.shrinkage == "APPLIED"
    assert amount(result.contributions[1].value) == 0
    assert result.effective.value == result.mapped_explicit.value


@pytest.mark.parametrize(
    "strength,expected",
    [
        ("LOW", Fraction(1, 2)),
        ("MEDIUM", Fraction(7, 12)),
        ("HIGH", Fraction(3, 4)),
    ],
)
def test_c33_ordinal_policy_chooses_exact_authored_weight(strength, expected):
    result = derive(consumer_input(strength=strength))
    assert amount(result.effective.value) == expected
    assert result.explicit_profile.rows[0].evidence_strength.level == strength


def test_c34_exact_rational_canonical_reduction(base):
    result = derive(rebind(base, policy_data(base), weights=((2, 7), (1, 7), (0, 1))))
    assert amount(result.effective.value) == Fraction(17, 28)
    assert (result.effective.value.amount.numerator, result.effective.value.amount.denominator) == (
        17,
        28,
    )


@pytest.mark.parametrize("n,d", [(2, 1), (-2, 1), (0, 2), (2, 4), (1.0, 2), (True, 1)])
def test_c35_no_clipping_or_noncanonical_output(n, d):
    with pytest.raises(ValidationError):
        c.MemberProfileAffinityAmount(numerator=n, denominator=d)


@pytest.mark.parametrize("targets", [(), "multiple"])
def test_c36_exactly_one_requested_target(base, targets):
    from target_affinity_fixtures import subject

    values = (
        ()
        if targets == ()
        else (
            base.explicit.source.request.requested_targets[0],
            type(base.explicit.source.request.requested_targets[0])(ingredient_id=uuid4()),
        )
    )
    explicit = subject((), targets=values, interpretation=base.explicit.policy)
    with pytest.raises(ValidationError, match="one identical typed target"):
        derive(base.model_dump() | dict(explicit=explicit))


@pytest.mark.parametrize("kind", ["INGREDIENT", "FLAVOR"])
def test_c37_c38_mismatched_identity_or_kind(base, kind):
    other = consumer_input(kind=kind)
    data = base.model_dump() | dict(reference_source=other.reference_source)
    with pytest.raises(ValidationError, match="one identical typed target"):
        derive(data)


def test_c39_new_feature_version_identity_independent():
    from app.modules.preferences.contracts import FeaturePreferenceTarget

    a = consumer_input(kind="METHOD")
    old_term = a.reference_source.identities[0].identity
    new_term = old_term.model_copy(update=dict(id=uuid4(), version=old_term.version + 1))
    new_target = FeaturePreferenceTarget(kind="METHOD", feature_term_id=new_term.id)
    source = reference_source(new_target, new_term, provider=a.reference_source.provider)
    assert new_term.code == old_term.code and new_term.id != old_term.id
    with pytest.raises(ValidationError, match="one identical typed target"):
        derive(a.model_dump() | dict(reference_source=source))


def test_c38_identical_uuid_different_typed_kind_rejects(base):
    from app.modules.preferences.contracts import FeaturePreferenceTarget
    from preference_fixtures import term

    identity = base.explicit.source.request.requested_targets[0].ingredient_id
    target = FeaturePreferenceTarget(kind="FLAVOR", feature_term_id=identity)
    source = reference_source(
        target, term("FLAVOR", id=identity), provider=base.reference_source.provider
    )
    with pytest.raises(ValidationError, match="one identical typed target"):
        derive(base.model_dump() | dict(reference_source=source))


@pytest.mark.parametrize(
    "child,field",
    [
        ("explicit_profile", "affinity"),
        ("explicit_profile", "evidence_strength"),
        ("reviewed_prior", "amount"),
    ],
)
def test_c40_c41_cached_children_not_input_authority(base, draft, child, field):
    # Convenience/cached results are not input fields, regardless of plausible child hashes.
    with pytest.raises(ValidationError):
        derive(base.model_dump() | {child: getattr(draft, child)})
    data = draft.model_dump()
    if field == "evidence_strength":
        data[child]["rows"][0][field]["level"] = "HIGH"
    else:
        row = data[child]["rows"][0]
        target = row[field]["amount"] if field == "affinity" else row[field]
        target["numerator"] = 0
        target["denominator"] = 1
    forged = c.ExactTargetPriorBackedAffinityDraft.model_construct(**data)
    data["fingerprint"] = forged.expected_fingerprint()
    with pytest.raises(ValidationError):
        c.ExactTargetPriorBackedAffinityDraft.model_validate(data)


@pytest.mark.parametrize(
    "path",
    [
        ("mapped_explicit", "value", "amount", "numerator"),
        ("mapped_prior", "value", "amount", "numerator"),
        ("contributions", 0, "value", "amount", "numerator"),
        ("contributions", 0, "weight_numerator"),
        ("effective", "value", "amount", "numerator"),
        ("compatibility_policy_fingerprint",),
        ("shrinkage_policy_fingerprint",),
    ],
)
def test_c42_rehashed_derived_forgery_rejects(draft, path):
    def mutate(data):
        for key in path[:-1]:
            data = data[key]
        data[path[-1]] = "f" * 64 if "fingerprint" in str(path[-1]) else 0

    data = rehashed_result(draft, mutate)
    with pytest.raises(ValidationError):
        c.ExactTargetPriorBackedAffinityDraft.model_validate(data)


def test_c43_old_cuts_replay_byte_deterministically(base, draft):
    assert derive(base).canonical_json() == draft.canonical_json()
    assert derive(json.loads(base.canonical_json())) == draft
    assert (
        c.ExactTargetPriorBackedAffinityDraft.model_validate_json(draft.canonical_json()) == draft
    )


def test_c44_fresh_prior_changes_only_fresh_result(base, draft):
    identity = base.reference_source.identities[0]
    fresh = reference_source(
        identity.target, identity.identity, amount=(1, 1), provider=base.reference_source.provider
    )
    new = derive(base.model_dump() | dict(reference_source=fresh))
    assert amount(new.effective.value) == Fraction(7, 8)
    assert new.fingerprint != draft.fingerprint
    assert derive(base) == draft


def test_c45_separate_capture_cuts_are_retained(draft):
    assert (
        draft.explicit_profile.subject.source.capture_completed_at
        != draft.reviewed_prior.source.capture_completed_at
    )
    assert draft.interpretation_mode == "VERSIONED_CONSUMER_POLICY_REPLAY"
    assert "simultaneous_liveness" not in type(draft).model_fields


def test_c46_new_mapping_version_does_not_mutate_old_replay(base, draft):
    data = policy_data(base)
    data["policy_version"] = "2"
    for group in data["explicit_maps"]:
        for row in group["rows"]:
            if row["value"] == "LIKE":
                row["output_amount"] = dict(numerator=1, denominator=1)
    new = derive(rebind(base, data))
    assert new.coordinate != draft.coordinate
    assert amount(new.effective.value) == Fraction(5, 8)
    assert derive(base) == draft


def test_c47_later_policy_is_replay_not_as_of_capture(base):
    data = policy_data(base)
    data["provenance"]["observed_at"] += timedelta(days=100)
    result = derive(rebind(base, data))
    assert result.interpretation_mode == "VERSIONED_CONSUMER_POLICY_REPLAY"
    assert result.subject.compatibility_policy.provenance.observed_at > (
        result.subject.reference_source.capture_completed_at
    )


@pytest.mark.parametrize(
    "field",
    [
        "recipe_repeat",
        "feature_repeat",
        "cooked",
        "out_of_stock",
        "too_expensive",
        "no_time",
        "no_equipment",
        "forced_conflict_resolution",
        "inferred_preference",
    ],
)
def test_c48_c49_c50_unrelated_evidence_cannot_enter(base, field):
    with pytest.raises(ValidationError):
        derive(base.model_dump() | {field: []})


@pytest.mark.parametrize("field", ["hierarchy", "cross_target_mapping", "parent_preference"])
def test_c51_no_hierarchy_or_cross_target_policy(base, field):
    with pytest.raises(ValidationError):
        rebind(base, policy_data(base) | {field: {}})


def test_c52_no_cross_member_fanout(draft):
    data = rehashed_result(draft, lambda d: d.update(member_id=uuid4()))
    with pytest.raises(ValidationError, match="primitive replay: member_id"):
        c.ExactTargetPriorBackedAffinityDraft.model_validate(data)
    with pytest.raises(ValidationError):
        c.ExactTargetPriorBackedAffinityInput.model_validate(
            draft.subject.model_dump() | {"members": [draft.member_id]}
        )


def test_c53_zero_io_closed_imports_and_runtime_guards(base, monkeypatch):
    import builtins
    import socket

    def forbidden(*args, **kw):
        raise AssertionError("Pure derivation attempted IO")

    # Validate the complete import closure of new modules and frozen child derivation modules.
    modules = (
        "prior_affinity.py",
        "prior_affinity_contracts.py",
        "profile_derivation.py",
        "reference_prior_resolution.py",
    )
    allowed = {
        "fractions",
        "math",
        "typing",
        "uuid",
        "pydantic",
        "hashlib",
        "app.domain.contracts",
        "app.domain.feature_identity",
        "app.domain.units",
        "app.modules.preferences",
        "app.modules.preferences.contracts",
        "app.modules.preferences.prior_affinity",
        "app.modules.preferences.prior_affinity_contracts",
        "app.modules.preferences.profile_derivation",
        "app.modules.preferences.reference_prior_contracts",
        "app.modules.preferences.reference_prior_resolution",
    }
    for name in modules:
        tree = ast.parse((ROOT / "apps/backend/app/modules/preferences" / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module in allowed, (name, node.module)
            elif isinstance(node, ast.Import):
                assert all(alias.name in allowed for alias in node.names), name
    with monkeypatch.context() as guard:
        guard.setattr(builtins, "open", forbidden)
        guard.setattr(socket, "socket", forbidden)
        guard.setattr(Path, "open", forbidden)
        from sqlalchemy.orm import Session

        guard.setattr(Session, "execute", forbidden)
        result = derive(base)
    assert result.effective.status == "AVAILABLE"


def test_c54_c55_c56_frozen_files_migrations_and_299_definitions():
    pins = json.loads(
        (Path(__file__).parent / "fixtures/prior_shrinkage_compatibility.json").read_text()
    )
    assert pins["baseline"] == "12048deeffd8c0b30368df0684de1d971a2c4b9c"
    assert len(pins["definitions"]) == 299
    schema = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
    for name, expected in pins["definitions"].items():
        data = json.dumps(schema[name], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        assert sha256(data.encode()).hexdigest() == expected, name
    for name, expected in pins["frozen_files"].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    migrations = sorted((ROOT / "apps/backend/migrations/versions").glob("*.py"))
    assert len(migrations) == 14 and migrations[-1].name.startswith("0014_")


def test_c57_no_production_policy_values_and_retained_test_baseline():
    pins = json.loads(
        (Path(__file__).parent / "fixtures/prior_shrinkage_baseline_tests.json").read_text()
    )
    assert len(pins["nodeids"]) == 2377
    source = (ROOT / "apps/backend/app/modules/preferences/prior_affinity_contracts.py").read_text()
    for name in ("explicit_maps", "reference_maps", "rules", "prior_weight"):
        assert c.ExactTargetPriorCompatibilityPolicy.model_fields.get(name) is None or (
            c.ExactTargetPriorCompatibilityPolicy.model_fields[name].is_required()
        )
    assert "synthetic" not in source


@pytest.mark.parametrize(
    "field,value",
    [
        ("planner_ready", True),
        ("activation_ready", True),
        ("planner_ready", 0),
        ("activation_ready", 0),
        ("learned_evidence", "AVAILABLE"),
    ],
)
def test_c58_fixed_scope_flags_reject_widening(draft, field, value):
    data = rehashed_result(draft, lambda d: d.update({field: value}))
    with pytest.raises(ValidationError):
        c.ExactTargetPriorBackedAffinityDraft.model_validate(data)


@pytest.mark.parametrize(
    "field", ["is_safe", "precommit", "validator_authority", "planner_utility"]
)
def test_c59_cannot_mint_authority(draft, field):
    with pytest.raises(ValidationError):
        c.ExactTargetPriorBackedAffinityDraft.model_validate(draft.model_dump() | {field: True})


def test_c60_unordered_policy_shuffle_same_fingerprint_and_result(base, draft):
    data = policy_data(base)
    for name in ("explicit_maps", "reference_maps"):
        data[name] = list(reversed(data[name]))
        for group in data[name]:
            group["rows"] = list(reversed(group["rows"]))
    assert derive(rebind(base, data)).canonical_json() == draft.canonical_json()
    weights = base.shrinkage_policy.model_dump()
    weights["rules"] = list(reversed(weights["rules"]))
    assert derive(base.model_dump() | dict(shrinkage_policy=weights)) == draft


def test_c61_same_fraction_different_kind_no_comparison_or_aggregation(base):
    a, b = [
        c.ScopedMemberProfileAffinity(
            coordinate=base.compatibility_policy.coordinate_for(kind),
            amount=dict(numerator=1, denominator=2),
        )
        for kind in ("INGREDIENT", "FLAVOR")
    ]
    assert a != b
    for operation in (lambda: a < b, lambda: a + b, lambda: sum((a, b))):
        with pytest.raises(TypeError):
            operation()


def test_c62_same_fraction_different_mapping_policy_no_comparison(base):
    other = c.ExactTargetPriorCompatibilityPolicy.model_validate(
        policy_data(base) | dict(policy_version="2")
    )
    a, b = [
        c.ScopedMemberProfileAffinity(
            coordinate=p.coordinate_for("INGREDIENT"), amount=dict(numerator=1, denominator=2)
        )
        for p in (base.compatibility_policy, other)
    ]
    assert a != b
    with pytest.raises(TypeError):
        _ = a < b
    with pytest.raises(TypeError):
        _ = a + b


@pytest.mark.parametrize(
    "field,new",
    [
        ("target_kind", "FLAVOR"),
        ("compatibility_policy_fingerprint", "f" * 64),
    ],
)
def test_c63_mismatched_descriptor_rejects_before_arithmetic(draft, field, new, monkeypatch):
    other = draft.mapped_prior.value.model_dump()
    other["coordinate"][field] = new

    def no_arithmetic(*args):
        raise AssertionError("Arithmetic ran before descriptor validation")

    monkeypatch.setattr("app.modules.preferences.prior_affinity.Fraction", no_arithmetic)
    with pytest.raises(ValueError, match="descriptor mismatch"):
        _blend(
            draft.coordinate,
            draft.mapped_explicit.value,
            other,
            c.PriorInfluenceWeight(numerator=1, denominator=2),
        )


@pytest.mark.parametrize(
    "field,new",
    [
        ("target_kind", "FLAVOR"),
        ("compatibility_policy_fingerprint", "f" * 64),
    ],
)
@pytest.mark.parametrize("branch", ["mapped_explicit", "mapped_prior", "effective", "contribution"])
def test_c64_c65_correct_numeric_wrong_descriptor_rehashed(draft, field, new, branch):
    def mutate(data):
        value = (
            data["contributions"][0]["value"] if branch == "contribution" else data[branch]["value"]
        )
        value["coordinate"][field] = new

    with pytest.raises(ValidationError, match="primitive replay"):
        c.ExactTargetPriorBackedAffinityDraft.model_validate(rehashed_result(draft, mutate))


def test_c66_equal_descriptor_equal_fraction_deterministic_equality(draft):
    value = draft.effective.value
    clone = c.ScopedMemberProfileAffinity.model_validate_json(value.canonical_json())
    assert value == clone
    assert value.canonical_json() == clone.canonical_json()
    with pytest.raises(TypeError):
        _ = value < clone


def test_c67_shrinkage_version_changes_provenance_not_coordinate(base, draft):
    new_policy = base.shrinkage_policy.model_dump() | dict(policy_version="2")
    same = derive(base.model_dump() | dict(shrinkage_policy=new_policy))
    assert same.coordinate == draft.coordinate
    assert same.effective.value == draft.effective.value
    assert same.fingerprint != draft.fingerprint
    assert same.shrinkage_policy_fingerprint != draft.shrinkage_policy_fingerprint
    changed = derive(
        base.model_dump()
        | dict(
            shrinkage_policy=shrinkage(
                base.compatibility_policy, version="3", weights=((0, 1),) * 3
            )
        )
    )
    assert changed.coordinate == draft.coordinate
    assert changed.effective.value != draft.effective.value


def test_c68_descriptor_stripping_naked_downstream_value_rejects(draft):
    naked = draft.effective.value.amount
    with pytest.raises(ValidationError):
        c.ScopedMemberProfileAffinity.model_validate(naked)
    with pytest.raises(ValidationError):
        c.AvailableExactTargetProfileAffinity(mode="EXPLICIT_ONLY", value=naked)
    data = rehashed_result(draft, lambda d: d["effective"].update(value=naked.model_dump()))
    with pytest.raises(ValidationError):
        c.ExactTargetPriorBackedAffinityDraft.model_validate(data)
    assert "shrinkage_policy_fingerprint" not in type(draft.coordinate).model_fields


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("member", ["DECLARED", "UNDECLARED", "RETRACTED"])
@pytest.mark.parametrize(
    "prior,anchor",
    [
        ("AVAILABLE", (1, 2)),
        ("AVAILABLE", (0, 1)),
        ("AVAILABLE", (1, 3)),
        ("NO_PUBLICATION", (1, 2)),
        ("RETRACTED", (1, 2)),
    ],
)
def test_c14_to_c25_exhaustive_missingness_by_kind(kind, member, prior, anchor):
    result = derive(consumer_input(kind=kind, member=member, prior=prior, amount=anchor))
    compatible = prior == "AVAILABLE" and anchor != (1, 3)
    if member == "RETRACTED":
        assert result.effective.reason == "MEMBER_RETRACTED"
    elif member == "UNDECLARED" and not compatible:
        assert result.effective.reason == "NO_EXPLICIT_OR_COMPATIBLE_PRIOR"
    else:
        expected = (
            "PRIOR_ONLY_COLD_START"
            if member == "UNDECLARED"
            else ("BLENDED_EXPLICIT_AND_PRIOR" if compatible else "EXPLICIT_ONLY")
        )
        assert result.effective.mode == expected
        assert result.effective.value.coordinate == result.coordinate
    assert result.planner_ready is result.activation_ready is False
    assert result.explicit_profile.rows[0].prior.status == "UNAVAILABLE"


@pytest.mark.parametrize("component", ["explicit_maps", "reference_maps"])
def test_all_five_groups_required_and_no_hidden_defaults(base, component):
    data = policy_data(base)
    data[component] = data[component][:4]
    with pytest.raises(ValidationError):
        c.ExactTargetPriorCompatibilityPolicy.model_validate(data)


@pytest.mark.parametrize("kind", ["compatibility", "shrinkage"])
def test_reviewed_provenance_required(base, kind):
    policy = base.compatibility_policy if kind == "compatibility" else base.shrinkage_policy
    data = policy.model_dump()
    data["provenance"]["kind"] = "USER"
    with pytest.raises(ValidationError):
        type(policy).model_validate(data)


def test_authored_resource_bounds_and_derived_exact_growth(base):
    data = policy_data(base)
    data["explicit_maps"][0]["rows"][0]["output_amount"] = dict(
        numerator=-(2**31), denominator=2**31 + 1
    )
    with pytest.raises(ValidationError, match="31-bit"):
        c.ExactTargetPriorCompatibilityPolicy.model_validate(data)
    data = policy_data(base)
    expected = data["explicit_maps"][0]["rows"][0]["expected_explicit_amount"]
    expected["numerator"] *= 10**100
    expected["denominator"] *= 10**100
    with pytest.raises(ValidationError, match="31-bit"):
        c.ExactTargetPriorCompatibilityPolicy.model_validate(data)
    result = derive(rebind(base, policy_data(base), weights=((1, 2147483647),) * 3))
    assert amount(result.effective.value) == Fraction(3, 4) - Fraction(1, 2 * 2147483647)
    assert result.effective.value.amount.denominator > 2147483647


def test_constructed_and_copied_nested_inputs_are_recursively_reparsed(base):
    bad = base.compatibility_policy.model_copy(update=dict(provider_command_hash="f" * 64))
    forged = base.model_copy(update=dict(compatibility_policy=bad))
    with pytest.raises(ValidationError):
        derive(forged)
    malformed = base.reference_source.model_copy(update=dict(publications=()))
    with pytest.raises(ValidationError):
        derive(base.model_copy(update=dict(reference_source=malformed)))


def test_current_declaration_only_and_retries_do_not_increase_strength(base):
    from target_affinity_fixtures import revision, subject

    first = base.explicit.source.preferences.declarations[0]
    second = revision(first, value="LIKE")
    explicit = subject((first, second), interpretation=base.explicit.policy)
    result = derive(base.model_dump() | dict(explicit=explicit))
    assert result.explicit_profile.rows[0].evidence_strength.level == "LOW"
    assert result.explicit_profile.rows[0].current_declaration == second
    assert result.effective.value == derive(base).effective.value


def test_authored_fingerprint_contains_no_derived_self_reference(base):
    body = base.compatibility_policy.model_dump()
    assert "compatibility_policy_fingerprint" not in body
    assert "coordinate" not in body
    assert base.compatibility_policy.coordinate_for("METHOD").compatibility_policy_fingerprint == (
        base.compatibility_policy.fingerprint()
    )
    changed = deepcopy(body)
    changed["reference_maps"][0]["rows"] = ()
    assert c.ExactTargetPriorCompatibilityPolicy.model_validate(changed).fingerprint() != (
        base.compatibility_policy.fingerprint()
    )


def test_explicit_policy_content_changed_without_repin_rejects(base):
    data = base.model_dump()
    data["explicit"]["policy"]["provenance"]["external_record_id"] = "different"
    assert _profile_hash(data["explicit"]["policy"]) != (
        base.compatibility_policy.explicit_policy_fingerprint
    )
    with pytest.raises(ValidationError, match="Pinned explicit policy"):
        derive(data)
