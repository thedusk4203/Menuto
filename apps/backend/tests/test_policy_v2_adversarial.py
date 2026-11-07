"""Additional PIV joint, resource and worker controls. Synthetic TEST_ONLY only."""

import json
import multiprocessing
import os
import re
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from threading import Event, Timer
from time import monotonic, sleep

import pytest
from app.domain.feature_identity import canonical, canonical_bytes
from app.modules.nutrition import policy_v2_contracts as v
from app.modules.nutrition.policy_v2 import derive_policy_v2
from app.modules.nutrition.policy_v2_limits import PolicyWork
from app.modules.nutrition.resolution_limits import ingest, structure
from app.modules.planning import policy_v2_capture as host
from basis_fixtures import rehash_sources, retained, weekly_basis_sources
from policy_v2_fixtures import author_root, author_rule, compose, input_for
from test_policy_v2 import assert_negative, assert_positive


def replace_synthesis(source, synthesis):
    from nutrition_resolution_fixtures import rehash

    data = canonical(source)
    ns = data["nre"]["sources"]
    ns["synthesis_sources"] = canonical(synthesis)
    ns["frame"]["source_frame"] = canonical(synthesis.frame)
    data["nre"]["sources"] = canonical(rehash(ns))
    return rehash_sources(data)


def add_clause(body, metric, constraint, interpretation="GUIDELINE_HARD"):
    clause = deepcopy(body["clauses"][0])
    clause.update(
        root_key="TEST_ONLY_" + metric.lower(), constraint=constraint, interpretation=interpretation
    )
    clause["descriptor"].update(metric=metric, unit="G")
    body["clauses"].append(clause)
    body["clauses"].sort(key=lambda c: c["root_key"])
    body["mandatory_hard_roots"] = sorted(
        c["root_key"] for c in body["clauses"] if c["interpretation"] == "GUIDELINE_HARD"
    )


@pytest.mark.parametrize("lower,positive", [(20, True), (43, False)])
def test_piv_d12_marginals_do_not_prove_correlated_support(lower, positive):
    source = author_root(
        retained(),
        lambda body: add_clause(
            body, "PROTEIN", dict(kind="MINIMUM", lower=dict(numerator=lower, denominator=1))
        ),
    )
    estimate = source.nre.estimate
    vectors = estimate.periods[0].vectors
    # Each marginal is reachable. With the stronger protein bound no SAME tuple
    # satisfies the retained energy root. An extrema or gap test would lie.
    assert any(
        7 <= Fraction(x.nutrients[0].numerator, x.nutrients[0].denominator) <= 13 for x in vectors
    )
    assert any(
        Fraction(x.nutrients[1].numerator, x.nutrients[1].denominator) >= lower for x in vectors
    )
    i = input_for(source)
    if positive:
        result = assert_positive(i)
        assert any(x.hard_violations for x in result.payload.support.assignments)
    else:
        assert_negative(i, "RESOLUTION_INSUFFICIENT", "NO_PROTECTED_JOINT_WITNESS")


def test_piv_d10_one_sided_roots_and_reference_target_are_not_invented_intervals():
    def edit(body):
        add_clause(body, "PROTEIN", dict(kind="MINIMUM", lower=dict(numerator=0, denominator=1)))
        add_clause(body, "FAT", dict(kind="MAXIMUM", upper=dict(numerator=100, denominator=1)))
        add_clause(
            body,
            "CARBOHYDRATE",
            dict(kind="TARGET", center=dict(numerator=0, denominator=1)),
            "REFERENCE_CENTER",
        )

    i = input_for(author_root(retained(), edit))
    result = assert_positive(i)
    clauses = {
        x.clause.descriptor.metric: x.clause.constraint for x in result.payload.retained_roots
    }
    assert not hasattr(clauses["PROTEIN"], "upper")
    assert not hasattr(clauses["FAT"], "lower")
    assert clauses["CARBOHYDRATE"].kind == "TARGET"
    assert all(x.nutrients[3].numerator != 0 for x in i.basis_sources.nre.estimate.configurations)


def test_piv_d12_equal_vectors_retain_every_configuration_witness():
    source = author_root(
        retained(),
        lambda body: body["clauses"][0]["constraint"].update(
            lower=dict(numerator=5, denominator=1), upper=dict(numerator=13, denominator=1)
        ),
    )

    # A TEST_ONLY zero-composition adjustable ingredient produces distinct exact
    # configuration IDs with equal vectors. They must all survive the projection.
    def equal_vectors(ns):
        ingredient = ns["recipes"][0]["ingredients"][0]["ingredient_id"]
        for row in ns["references"]:
            if row["fact"]["ingredient_id"] == ingredient:
                row["fact"]["nutrients"] = dict(
                    energy_kcal="0", protein_g="0", fat_g="0", carbohydrate_g="0"
                )

    same = compose(source.nre.sources.synthesis_sources, source, equal_vectors)
    result = assert_positive(input_for(same))
    nre = same.nre.estimate
    assert any(len(vec.configurations) > 1 for p in nre.periods for vec in p.vectors)
    assert len(result.payload.support.assignments) == len(nre.configurations)
    assert len({x.configuration_ids for x in result.payload.support.assignments}) == len(
        nre.configurations
    )


def test_piv_d13_singleton_null_gap_does_not_mean_missing_resolution():
    source = retained()

    def one_food(ns):
        recipe = ns["recipes"][0]
        recipe["ingredients"][0]["adjustment"] = dict(kind="NONE", min_delta="0", max_delta="0")
        tier = recipe["portion_tiers"][0]["id"]
        ns["scope"]["recipes"][0]["tier_ids"] = [tier]
        ns["scope"]["slots"][0]["alternatives"] = [
            x for x in ns["scope"]["slots"][0]["alternatives"] if x["tier_id"] == tier
        ]

    singleton = compose(source.nre.sources.synthesis_sources, source, one_food)
    result = assert_positive(input_for(singleton))
    assert len(result.payload.support.assignments) == 1
    assert singleton.nre.estimate.measurements[0].maximum_gap is None
    assert singleton.nre.estimate.measurements[0].step_state == "NO_ADJACENT_STEP"


@pytest.mark.parametrize("which", ["root", "unselected"])
def test_piv_d01_d07_missing_full_anchor_not_hidden_by_comfort_requirements(which):
    data = canonical(retained())
    if which == "root":
        data["anchors"] = [x for x in data["anchors"] if not x["key"].startswith("root:")]
    else:
        data["anchors"] = [x for x in data["anchors"] if not x["key"].endswith(":precise")]
    assert_negative(
        input_for(rehash_sources(data)), "SOURCE_UNAVAILABLE", "ANCHOR_COVERAGE_MISSING"
    )


def test_piv_d14_d27_missing_retained_week_period_is_not_manufactured():
    assert_negative(
        input_for(weekly_basis_sources(False)), "SOURCE_UNAVAILABLE", "PERIOD_COVERAGE_MISSING"
    )


def test_piv_d06_faithful_unavailable_nre_is_consistent_but_not_admitted():
    source = retained()
    unavailable = compose(
        source.nre.sources.synthesis_sources,
        source,
        lambda ns: ns["references"][0]["fact"].update(status="DRAFT"),
    )
    assert unavailable.nre.estimate.availability == "UNAVAILABLE"
    result = assert_negative(input_for(unavailable), "SOURCE_UNAVAILABLE", "NRE_UNAVAILABLE")
    assert result.diagnostics[0].child_outcome == "UNAVAILABLE"
    assert result.diagnostics[0].child_reason == "NRE_UNAVAILABLE"


@pytest.mark.parametrize("boundary", ["before", "inside", "after"])
def test_piv_d23_d25_rule_withdrawal_time_is_not_early_or_rewritten(boundary):
    from datetime import timedelta

    from nutrition_synthesis_pure_fixtures import withdraw

    source = retained()
    span = source.nre.sources.scope.root_request.temporal.interval
    source = author_rule(
        source, lambda rule: rule["effective"].update(end=span.end + timedelta(days=2))
    )
    effective = {
        "before": span.start,
        "inside": span.start + timedelta(hours=12),
        "after": span.end,
    }[boundary]
    changed = replace_synthesis(
        source, withdraw(source.nre.sources.synthesis_sources, effective_at=effective)
    )
    if boundary == "after":
        changed = compose(changed.nre.sources.synthesis_sources, source)
        assert_positive(input_for(changed))
    else:
        assert_negative(
            input_for(changed),
            "SOURCE_UNAVAILABLE",
            "SOURCE_WITHDRAWN" if boundary == "before" else "SOURCE_UNAUTHORIZED",
        )
    assert_positive(input_for(source))


@pytest.mark.parametrize("state", ["absent", "retracted"])
def test_piv_d06_d16_goal_missing_does_not_default_to_maintain(state):
    from nutrition_synthesis_pure_fixtures import remove_root_records, retract_goal

    source = retained()
    ss = source.nre.sources.synthesis_sources
    changed = remove_root_records(ss, "GOAL") if state == "absent" else retract_goal(ss)
    assert changed.request.root.goal_state != "PRESENT"
    assert_negative(
        input_for(replace_synthesis(source, changed)),
        "SOURCE_UNAVAILABLE",
        "GOAL_SOURCE_UNAVAILABLE",
    )


@pytest.mark.parametrize("precision", ["RELAXED", "STANDARD", "PRECISION"])
def test_piv_d19_d21_every_explicit_precision_value_is_source_bound(precision):
    from nutrition_synthesis_pure_fixtures import hash_sources

    source = retained()
    data = canonical(source.nre.sources.synthesis_sources)
    data["request"]["precision"]["value"] = precision
    s = compose(hash_sources(data), source)
    result = assert_positive(input_for(s))
    selected = [x.id for x in result.payload.claims if x.layer == "COMFORT"]
    assert selected == [
        {"RELAXED": "relaxed", "STANDARD": "standard", "PRECISION": "precise"}[precision]
    ]


@pytest.mark.parametrize(
    "axis", ["CostPreference", "BudgetContract", "KitchenEffort", "convenience", "TasteFit"]
)
def test_piv_d21_non_nutrition_axes_cannot_become_policy_operands(axis):
    data = canonical(input_for())
    data[axis] = "TEST_ONLY_override"
    with pytest.raises(ValueError, match="Extra inputs"):
        derive_policy_v2(data)


@pytest.mark.parametrize("kind", ["GRANT", "QUALIFY", "journal", "publisher"])
def test_piv_d04_d24_actual_rejected_history_is_not_honest_unavailable(kind):
    from app.modules.nutrition.basis_applicability import resolve_basis_applicability
    from basis_fixtures import rehash_artifact

    data = canonical(retained())
    events = data["artifact"]["events"]
    if kind == "GRANT":
        row = next(x for x in events if x["kind"] == "GRANT")
        row["scope"] = "TEST_ONLY_foreign_scope"
    elif kind == "QUALIFY":
        next(x for x in events if x["kind"] == "QUALIFY")["principal_subject"] = (
            "TEST_ONLY_forged_human"
        )
    elif kind == "journal":
        events[1]["previous_hash"] = "f" * 64
    else:
        pub = next(x for x in events if x["kind"] == "PUBLISH")
        grant = next(
            x for x in events if x["kind"] == "GRANT" and x["capability"] == "TEST_BASIS_PUBLISH"
        )
        grant["effective"]["end"] = pub["recorded_at"]
    if kind != "journal":
        data["artifact"] = canonical(rehash_artifact(data["artifact"]))
    data["frame"]["artifact_fingerprint"] = data["artifact"]["artifact_fingerprint"]
    s = rehash_sources(data)
    child = resolve_basis_applicability(s)
    assert child.outcome == "REJECTED", child
    result = assert_negative(input_for(s), "REJECTED", "MBA_INCONSISTENT", consistent=False)
    assert result.diagnostics[0].child_outcome == "REJECTED"
    assert result.diagnostics[0].child_reason == child.reasons[0]


@pytest.mark.parametrize(
    "model,field",
    [
        (v.PolicyAssignmentEvaluationV2, "configuration_ids"),
        (v.JointPolicySupportV2, "assignments"),
        (v.JointPolicySupportV2, "center_deltas"),
        (v.NutritionPolicyBodyV2, "coverage"),
        (v.NutritionPolicyBodyV2, "claims"),
    ],
)
def test_piv_d30_collection_limit_and_overflow(model, field):
    # CoreSchema validates length before accepting the constructed record; use
    # real positive rows so overflow is not masked by unrelated malformed data.
    positive = assert_positive(input_for())
    if model is v.PolicyAssignmentEvaluationV2:
        obj = positive.payload.support.assignments[0]
    elif model is v.JointPolicySupportV2:
        obj = positive.payload.support
    else:
        obj = positive.payload
    max_length = next(
        x.max_length for x in model.model_fields[field].metadata if hasattr(x, "max_length")
    )
    sample = (
        canonical(obj)[field][0]
        if canonical(obj)[field]
        else canonical(positive.payload.support.assignments[0])
    )
    data = canonical(obj)
    # For an empty DAY center list use a genuine imported delta carrier.
    if field == "center_deltas":
        from policy_v2_fixtures import positive_week

        sample = canonical(
            assert_positive(input_for(positive_week())).payload.support.center_deltas[0]
        )
    data[field] = [sample] * max_length
    # The 8MiB result cap may reject a structurally allowed high-cardinality record;
    # field length itself still has its exact declared cap.
    try:
        model.model_validate(data)
    except ValueError as exc:
        assert "RESOURCE_EXCEEDED" in str(exc)
    data[field].append(sample)
    with pytest.raises(ValueError):
        model.model_validate(data)


@pytest.mark.parametrize(
    "limit",
    [
        64 * 1024,
        256 * 1024,
        2 * 1024 * 1024,
        8 * 1024 * 1024,
        16 * 1024 * 1024,
        32 * 1024 * 1024,
        48 * 1024 * 1024,
    ],
)
def test_piv_d30_encoded_bytes_exact_boundary_and_plus_one(limit):
    # JSON whitespace counts at ingress and does not consume structure nodes.
    encoded = b"0" + b" " * (limit - 1)
    assert ingest(encoded, limit) == 0
    with pytest.raises(ValueError, match="encoded bytes"):
        ingest(encoded + b" ", limit)


def test_piv_d30_structure_integer_and_reserved_failure_output_boundaries():
    structure({"x": "x" * 100_000})
    with pytest.raises(ValueError, match="string"):
        structure({"x": "x" * 100_001})
    structure([0] * 65536)
    with pytest.raises(ValueError, match="collection"):
        structure([0] * 65537)
    nested = 0
    for _ in range(32):
        nested = [nested]
    structure(nested)
    with pytest.raises(ValueError, match="structure"):
        structure([nested])
    work = PolicyWork()
    work.reserve_control()
    work.charge(2_000_000 - work.used)
    with pytest.raises(ValueError, match="policy work"):
        work.charge()
    work.failure_output(dict(outcome="RESOURCE_EXCEEDED", payload=None), 256 * 1024)
    assert work.used == 2_000_000
    assert work.control < 512


def test_piv_d30_exact_structure_node_cap_and_plus_one():
    # 1 root + 16 list nodes + 999,983 scalar nodes = 1,000,000.
    value = [[0] * 62500 for _ in range(15)] + [[0] * 62483]
    structure(value, 32 * 1024 * 1024)
    value[-1].append(0)
    with pytest.raises(ValueError, match="structure"):
        structure(value, 32 * 1024 * 1024)


def test_piv_d30_frozen_history_and_anchor_caps_cannot_be_raised():
    from app.modules.nutrition import basis_contracts as b

    source = retained()
    artifact = canonical(source.artifact)
    artifact["events"] = [artifact["events"][0]] * 256
    b.BasisFixtureArtifactV1.model_validate(artifact)
    artifact["events"].append(artifact["events"][0])
    with pytest.raises(ValueError):
        b.BasisFixtureArtifactV1.model_validate(artifact)
    body = canonical(source)
    body["anchors"] = [body["anchors"][0]] * 128
    b.BasisApplicabilitySourcesV1.model_validate(body)
    body["anchors"].append(body["anchors"][0])
    with pytest.raises(ValueError):
        b.BasisApplicabilitySourcesV1.model_validate(body)


def test_piv_d30_canonical_rational_output_and_temporary_bit_boundaries():
    work = PolicyWork()
    assert work.number(Fraction(2**256 - 1, 1)).numerator.bit_length() == 256
    with pytest.raises(ValueError, match="policy rational"):
        work.number(Fraction(2**256, 1))
    # Endpoint-language operands remain 127-bit and each operation materializes a
    # bounded endpoint; a product of two of them cannot exceed 254 temporary bits.
    from app.modules.nutrition.synthesis_contracts import SynthesisRational

    SynthesisRational(numerator=2**127 - 1, denominator=1)
    with pytest.raises(ValueError):
        SynthesisRational(numerator=2**127, denominator=1)
    assert work.multiply(Fraction(2**511), Fraction(2**511)) == 2**1022
    with pytest.raises(ValueError, match="temporary product"):
        work.multiply(Fraction(2**512), Fraction(2**512))
    assert work.add(Fraction(2**1021), Fraction(2**1021)) == 2**1022
    with pytest.raises(ValueError, match="temporary sum"):
        work.add(Fraction(2**1023), Fraction(1))


def slow_test_worker(stage, body, channel):
    sleep(30)


def environment_test_worker(stage, body, channel):
    channel.send_bytes(
        canonical_bytes(
            dict(
                secret=os.getenv("TEST_ONLY_DATABASE_SECRET"),
                pg=os.getenv("PGPASSWORD"),
                marker=os.getenv("PIV_SAFE_MARKER"),
            )
        )
    )
    channel.close()


@pytest.mark.parametrize("boundary", ["deadline", "cancelled"])
def test_piv_d30_spawned_worker_is_killed_joined_and_output_discarded(monkeypatch, boundary):
    monkeypatch.setattr(host, "execute", slow_test_worker)
    monkeypatch.setattr(host, "_PURE_SECONDS", 0.5 if boundary == "deadline" else 5.0)
    cancel = Event()
    timer = Timer(0.5, cancel.set) if boundary == "cancelled" else None
    old = {c.pid for c in multiprocessing.active_children()}
    started = monotonic()
    if timer:
        timer.start()
    try:
        with pytest.raises(TimeoutError):
            host._run("derive", {}, monotonic() + 90, cancel)
    finally:
        if timer:
            timer.cancel()
            timer.join()
    assert monotonic() - started < 8
    assert {c.pid for c in multiprocessing.active_children()} <= old


def test_piv_d30_spawn_environment_scrubbed_before_interpreter_start(monkeypatch):
    monkeypatch.setattr(host, "execute", environment_test_worker)
    monkeypatch.setenv("TEST_ONLY_DATABASE_SECRET", "TEST_ONLY_not_a_real_credential")
    monkeypatch.setenv("PGPASSWORD", "TEST_ONLY_not_a_real_credential")
    monkeypatch.setenv("PIV_SAFE_MARKER", "TEST_ONLY_visible")
    result = json.loads(host._run("derive", {}, monotonic() + 90))
    assert result == dict(secret=None, pg=None, marker="TEST_ONLY_visible")
    assert os.environ["PGPASSWORD"] == "TEST_ONLY_not_a_real_credential"


def test_piv_d31_collected_baseline_ids_remain_exactly_available(request):
    expected = json.loads(
        (Path(__file__).parent / "fixtures/policy_v2_compatibility.json").read_text()
    )["baseline_tests"]
    # When the complete suite is collected, require every original node ID. A
    # targeted test invocation checks the retained fixture's exact inventory only.
    collected = {x.nodeid for x in request.session.items}
    if len(collected) >= 4183:
        wanted = Counter(stable_baseline_id(x) for x in expected)
        actual = Counter(stable_baseline_id(x) for x in collected)
        assert wanted <= actual
    assert len(expected) == len(set(expected)) == 4183


def stable_baseline_id(node):
    # These FOUR frozen parameters call uuid4() during collection. Preserve their
    # exact function/field identity and cardinality; normalize only the generated
    # label, never a test body, assertion, parameter value or execution.
    prefixes = (
        "apps/backend/tests/test_postgres_hierarchy_authority.py::"
        "test_a02_raw_sql_claimed_authority_fields_rejected[actor_user_id-",
        "apps/backend/tests/test_postgres_hierarchy_authority.py::"
        "test_a02_raw_sql_claimed_authority_fields_rejected[reviewer_user_id-",
        "apps/backend/tests/test_postgres_reference_priors.py::"
        "test_a01_a02_l04_raw_sql_rejects_claimed_authority[grant_event_id-",
        "apps/backend/tests/test_prior_shrinkage.py::"
        "test_c09_provider_immutable_binding[provider_id-",
    )
    for prefix in prefixes:
        if node.startswith(prefix) and re.fullmatch(r"[0-9a-f-]{36}\]", node[len(prefix) :]):
            return prefix + "<GENERATED_UUID>]"
    return node
