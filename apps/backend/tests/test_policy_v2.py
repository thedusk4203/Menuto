"""PIV-D pure/adversarial obligations. All quantities are invented TEST_ONLY algebra."""

import hashlib
import json
import pickle
import runpy
from copy import copy, deepcopy
from pathlib import Path
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition import policy_v2_contracts as v
from app.modules.nutrition.policy_v2 import derive_policy_v2 as derive
from app.modules.nutrition.policy_v2_limits import PolicyWork
from app.modules.nutrition.policy_v2_public import admit_production_policy_v2, policy_v2_handoff
from app.modules.nutrition.resolution_limits import ingest, structure
from app.modules.planning import policy_v2_capture as host
from app.modules.validation.nutrition_policy_v2 import check_policy_handoff_v2, check_policy_v2
from basis_fixtures import reauthor_meaning, rehash_artifact, rehash_sources, retained
from nutrition_synthesis_fixtures import instruction
from policy_v2_fixtures import (
    author_root,
    author_rule,
    forged,
    input_for,
    positive_week,
    rehash_input,
)

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def day():
    i = input_for()
    return i, derive(i)


@pytest.fixture(scope="module")
def week():
    i = input_for(positive_week())
    return i, derive(i)


def assert_positive(i, r=None):
    r = derive(i) if r is None else r
    assert r.outcome == "AVAILABLE_TEST_ONLY", r.diagnostics
    report = check_policy_v2(i, r)
    assert report.decision == "CONSISTENT" and report.numerical_use == "AVAILABLE_RETAINED_ONLY"
    assert r.validation_authority == report.validation_authority == "UNVERIFIED_TRANSPORT"
    assert r.production_admission == "CLOSED" and not r.planner_ready and not r.activation_ready
    return r


def assert_negative(i, outcome, reason, consistent=True):
    r = derive(i)
    assert r.outcome == outcome and r.payload is None, r
    assert r.diagnostics[0].code == reason, r.diagnostics
    report = check_policy_v2(i, r)
    assert report.numerical_use == "NOT_ADMITTED"
    assert report.decision == ("CONSISTENT" if consistent else "INCONSISTENT"), report
    return r


def comfort(source, low, high, branch=None):
    def edit(rule):
        ops = rule["cases"][0]["operations"]
        extra = [
            canonical(
                instruction(
                    "TEST_ONLY_soft_" + key,
                    "AFFINE_SAME_UNIT",
                    ("lower",),
                    coefficient=dict(numerator=0, denominator=1),
                    offset=dict(numerator=value, denominator=1),
                )
            )
            for key, value in (("lo", low), ("hi", high))
        ]
        rule["cases"][0]["operations"] = ops[:2] + extra + ops[2:]
        for op in ops:
            if (
                op["kind"] == "MAKE_CONSTRAINT"
                and op["layer"] == "COMFORT"
                and (branch is None or op["id"] == branch)
            ):
                op["inputs"] = ["TEST_ONLY_soft_lo", "TEST_ONLY_soft_hi"]

    return author_rule(source, edit)


@pytest.mark.parametrize("name", ["day", "week"])
def test_piv_d01_full_joint_policy(name, request):
    i, r = request.getfixturevalue(name)
    r = assert_positive(i, r)
    assert (
        r.payload.retained_roots == i.basis_sources.nre.sources.synthesis_sources.request.root.roots
    )
    assert len(r.payload.coverage) == len(i.basis_sources.anchors)
    assert {x.disposition for x in r.payload.coverage} == {
        "RETAINED_ROOT",
        "ACTIVE_CLAIM",
        "UNSELECTED_PRECISION_BRANCH",
    }


@pytest.mark.parametrize("fake", [None, {}, "570098480335dbf7c731fcf0954dd4601a2ccb9d", uuid4()])
def test_piv_d02_serialized_origin_cannot_issue_lease(day, fake):
    i, r = day
    assert_positive(i, r)
    denied = host.consume_test_policy_v2(fake, host.expected_policy_v2_use(i))
    assert denied.diagnostics[0].code == "ORIGIN_NOT_ESTABLISHED"
    assert not hasattr(denied, "payload")


@pytest.mark.parametrize("field", ["configurations", "periods", "measurements"])
def test_piv_d03_fully_rehashed_nre_forgery(day, field):
    i, _ = day
    data = canonical(i.basis_sources)
    e = data["nre"]["estimate"]
    if field == "configurations":
        e[field][0]["nutrients"][0]["numerator"] += 1
    elif field == "periods":
        e[field][0]["vectors"][0]["nutrients"][0]["numerator"] += 1
    else:
        e[field][0]["values"][0]["numerator"] += 1
    body = dict(e)
    body.pop("result_fingerprint")
    from app.modules.nutrition.resolution_contracts import resolution_hash

    e["result_fingerprint"] = resolution_hash("estimate", body)
    mutated = input_for(rehash_sources(data))
    assert_negative(mutated, "REJECTED", "NRE_INCONSISTENT", consistent=False)


@pytest.mark.parametrize("seam", ["assertion", "qualification", "reader"])
def test_piv_d04_rehashed_mba_authority_forgery(day, seam):
    i, _ = day
    data = canonical(i.basis_sources)
    events = data["artifact"]["events"]
    if seam == "assertion":
        review = next(e for e in events if e["kind"] == "REVIEW")
        review["assertion"]["material_reference_fingerprint"] = "f" * 64
        fp = b.basis_hash("assertion", review["assertion"])
        for e in events:
            if e["kind"] in {"REVIEW", "PUBLISH"}:
                e["assertion_fingerprint"] = fp
    elif seam == "qualification":
        next(e for e in events if e["kind"] == "QUALIFY")["principal_subject"] = "forged"
    else:
        next(e for e in events if e["capability"] == "TEST_BASIS_SOURCE_READ")["principal"] = (
            "forged"
        )
    data["artifact"] = canonical(rehash_artifact(data["artifact"]))
    data["frame"]["artifact_fingerprint"] = data["artifact"]["artifact_fingerprint"]
    assert_negative(
        input_for(rehash_sources(data)), "REJECTED", "MBA_INCONSISTENT", consistent=False
    )


@pytest.mark.parametrize(
    "seam", ["claim", "trace", "roots", "coverage", "assignment", "representative"]
)
def test_piv_d05_whole_policy_rehashed_positive_forgery(day, seam):
    i, r = day

    def edit(data):
        p = data["payload"]
        if seam == "claim":
            p["claims"][0]["constraint"]["upper"]["numerator"] += 1
        elif seam == "trace":
            p["trace"][0]["amount"]["numerator"] += 1
        elif seam == "roots":
            p["retained_roots"][0]["clause"]["constraint"]["lower"]["numerator"] -= 1
        elif seam == "coverage":
            p["coverage"] = p["coverage"][:-1]
        elif seam == "assignment":
            p["support"]["assignments"][0]["hard_violations"] = []
            p["support"]["protected_assignment_ids"] = [
                x["assignment_fingerprint"] for x in p["support"]["assignments"]
            ]
        else:
            p["support"]["representative_comfort_assignment_id"] = "f" * 64
        support = dict(p["support"])
        support.pop("support_fingerprint")
        p["support"]["support_fingerprint"] = v.policy_v2_hash("support", support)

    bad = forged(r, edit)
    report = check_policy_v2(i, bad)
    assert report.decision == "INCONSISTENT"
    assert report.findings == ("POLICY_SEMANTICS_INCONSISTENT",)


def test_piv_d06_consistent_negative_no_numeric_use(day):
    s = reauthor_meaning(
        retained(),
        lambda data: [x["meaning"].update(material_bases=["COOKED_G"]) for x in data["claims"]],
    )
    r = assert_negative(input_for(s), "UNSUPPORTED", "UNIT_OR_SCOPE_MISMATCH")
    assert r.diagnostics[0].child_outcome == "NOT_APPLICABLE"


@pytest.mark.parametrize(
    "field",
    [
        "root_source_fingerprint",
        "root_result_fingerprint",
        "requirement_fingerprint",
        "anchor_manifest_fingerprint",
        "original_meaning_manifest_fingerprint",
        "rule_case_id",
    ],
)
def test_piv_d07_complete_identity_pins(day, field):
    i, _ = day
    data = canonical(i)
    data["identity"][field] = "forged" if field == "rule_case_id" else "f" * 64
    assert_negative(rehash_input(data), "REJECTED", "SOURCE_IDENTITY_MISMATCH", consistent=False)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "contradictory"])
def test_piv_d08_original_source_meaning_not_wrapper_authority(mutation):
    def edit(data):
        if mutation == "missing":
            data["claims"] = []
        elif mutation == "duplicate":
            data["claims"].append(deepcopy(data["claims"][0]))
        else:
            extra = deepcopy(data["claims"][0])
            extra["meaning"]["interpretation_version"] = "incompatible"
            data["claims"].append(extra)

    if mutation == "missing":
        assert_negative(
            input_for(reauthor_meaning(retained(), edit)), "SOURCE_UNAVAILABLE", "MBA_UNAVAILABLE"
        )
    else:
        # Canonical full original manifest construction itself refuses contradictory evidence.
        with pytest.raises(ValueError, match="ORIGINAL_MEANING_CONTRADICTION"):
            reauthor_meaning(retained(), edit)


@pytest.mark.parametrize(
    "token",
    [
        "PLANNED_OFFERED_FOOD_V1",
        "OBSERVED_OFFERED_FOOD_V1",
        "OBSERVED_CONSUMED_FOOD_V1",
        "PHYSIOLOGICAL_INTAKE_V1",
    ],
)
def test_piv_d09_no_clinical_identity_bridge(token):
    s = reauthor_meaning(
        retained(), lambda d: [x["meaning"].update(meaning=token) for x in d["claims"]]
    )
    assert_negative(input_for(s), "UNSUPPORTED", "MEANING_MISMATCH")


@pytest.mark.parametrize("field", ["subject", "actor_user_id", "database_oid", "database_name"])
def test_piv_d10_exact_subject_and_descriptor_identity(day, field):
    i, _ = day
    data = canonical(i)
    if field == "subject":
        data["identity"][field]["member_id"] = str(uuid4())
    elif field == "actor_user_id":
        data["identity"][field] = str(uuid4())
    elif field == "database_oid":
        data["identity"][field] += 1
    else:
        data["identity"][field] = "nrc_test_foreign"
    assert_negative(rehash_input(data), "REJECTED", "SOURCE_IDENTITY_MISMATCH", consistent=False)


@pytest.mark.parametrize("seam", ["recipe", "reference", "seal"])
def test_piv_d11_favorable_only_source_is_not_complete(day, seam):
    i, _ = day
    data = canonical(i.basis_sources)
    ns = data["nre"]["sources"]
    key = {"recipe": "recipes", "reference": "references", "seal": "recipe_seals"}[seam]
    ns[key] = ns[key][:-1]
    from nutrition_resolution_fixtures import rehash

    ns = rehash(ns)
    data["nre"]["sources"] = canonical(ns)
    # Full parent pins are re-authored; unchanged estimate cannot hide missing primitive rows.
    assert_negative(
        input_for(rehash_sources(data)), "REJECTED", "NRE_INCONSISTENT", consistent=False
    )


def test_piv_d12_same_assignment_not_marginals(day):
    i, r = day
    support = assert_positive(i, r).payload.support
    assert len(support.assignments) == 6
    assert len(support.protected_assignment_ids) < len(support.assignments)
    assert set(support.comfort_assignment_ids) <= set(support.protected_assignment_ids)
    assert all(row.configuration_ids for row in support.assignments)


def test_piv_d13_inclusive_single_value_band_despite_large_gap():
    i = input_for(comfort(retained(), 10, 10))
    r = assert_positive(i)
    assert i.basis_sources.nre.estimate.measurements[0].maximum_gap.numerator > 0
    assert len(r.payload.support.comfort_assignment_ids) == 1


def test_piv_d14_joint_day_week_coherence(week):
    i, r = week
    support = assert_positive(i, r).payload.support
    assert len(support.slot_ids) == 7
    assert all(len(x.period_vector_fingerprints) == 8 for x in support.assignments)
    assert len(r.payload.support.center_deltas) == len(support.assignments)


def test_piv_d15_authored_hard_widening_is_conflict():
    def edit(rule):
        ops = rule["cases"][0]["operations"]
        ops.insert(
            2,
            canonical(
                instruction(
                    "TEST_ONLY_widen",
                    "AFFINE_SAME_UNIT",
                    ("upper",),
                    coefficient=dict(numerator=1, denominator=1),
                    offset=dict(numerator=1, denominator=1),
                )
            ),
        )
        next(x for x in ops if x["id"] == "daily")["inputs"] = ["lower", "TEST_ONLY_widen"]

    assert_negative(
        input_for(author_rule(retained(), edit)), "POLICY_CONFLICT", "HARD_CONTAINMENT_FAILED"
    )


@pytest.mark.parametrize("comparator", ["UPPER_LT", "LOWER_GT"])
def test_piv_d16_goal_direction_comes_from_authored_instruction(comparator):
    def edit(rule):
        next(x for x in rule["cases"][0]["operations"] if x["kind"] == "CHECK_DIRECTION")[
            "comparator"
        ] = comparator

    assert_negative(
        input_for(author_rule(retained(), edit)), "POLICY_CONFLICT", "GOAL_DIRECTION_CONFLICT"
    )


def test_piv_d17_daily_claim_cannot_be_dropped():
    def edit(rule):
        case = rule["cases"][0]
        case["operations"] = [x for x in case["operations"] if x["id"] != "daily"]
        case["required_claims"].remove("daily")

    assert_negative(
        input_for(author_rule(retained(), edit)), "SOURCE_UNAVAILABLE", "DAILY_PROTECTION_MISSING"
    )


def test_piv_d18_weekly_target_is_soft_delta_not_equality(week):
    i, r = week
    r = assert_positive(i, r)
    assert any(x.amount_minus_center.numerator != 0 for x in r.payload.support.center_deltas)
    assert r.solver_infeasibility == "NOT_PROVEN"


def test_piv_d19_missing_authenticated_precision_witness(day):
    i, _ = day
    data = canonical(i)
    data["basis_sources"]["nre"]["sources"]["synthesis_sources"]["precision_witness"] = None
    assert_negative(rehash_input(data), "SOURCE_UNAVAILABLE", "PRECISION_UNAUTHORIZED")


@pytest.mark.parametrize("field", ["version", "actor_user_id", "evidence"])
def test_piv_d20_equal_precision_enum_different_identity(day, field):
    i, _ = day
    data = canonical(i)
    p = data["identity"]["precision"]
    if field == "evidence":
        p[field]["purpose"] += " forged"
    else:
        p[field] = str(uuid4())
    assert_negative(rehash_input(data), "REJECTED", "PRECISION_IDENTITY_MISMATCH", consistent=False)


def test_piv_d21_unselected_precision_branch_remains_checked():
    assert_negative(
        input_for(comfort(retained(), 6, 14, "precise")),
        "POLICY_CONFLICT",
        "PRECISION_NESTING_FAILED",
    )


@pytest.mark.parametrize("case", ["hard_empty", "soft_empty", "soft_violation"])
def test_piv_d22_separate_hard_and_soft_support(case):
    if case == "hard_empty":
        s = author_root(
            retained(),
            lambda g: g["clauses"][0]["constraint"].update(
                lower=dict(numerator=100, denominator=1), upper=dict(numerator=101, denominator=1)
            ),
        )
        assert_negative(input_for(s), "RESOLUTION_INSUFFICIENT", "NO_PROTECTED_JOINT_WITNESS")
    elif case == "soft_empty":
        r = assert_negative(
            input_for(comfort(retained(), 8, 9)),
            "RESOLUTION_INSUFFICIENT",
            "NO_JOINT_COMFORT_SUPPORT",
        )
        assert (r.diagnostics[0].hard_support, r.diagnostics[0].soft_support) == (
            "PRESENT",
            "SOFT_UNSUPPORTED",
        )
    else:
        r = assert_positive(input_for(comfort(retained(), 10, 10)))
        assert set(r.payload.support.protected_assignment_ids) - set(
            r.payload.support.comfort_assignment_ids
        )


@pytest.mark.parametrize("field", ["rule_selection", "registry_revision", "issuer_epoch"])
def test_piv_d23_exact_publication_and_cut_identity(day, field):
    i, _ = day
    data = canonical(i)
    if field == "rule_selection":
        data["identity"][field]["publication_id"] = str(uuid4())
    elif field == "registry_revision":
        data["identity"][field] += 1
    else:
        data["identity"][field] = "foreign_epoch"
    assert_negative(rehash_input(data), "REJECTED", "SOURCE_IDENTITY_MISMATCH", consistent=False)


@pytest.mark.parametrize("kind", ["PUBLISH", "SUPERSEDE"])
@pytest.mark.parametrize("expired", ["GRANT", "QUALIFY"])
@pytest.mark.parametrize("renewed", [False, True])
def test_piv_d24_honest_negative_and_forged_positive(kind, expired, renewed):
    from app.modules.nutrition.basis_applicability import resolve_basis_applicability
    from app.modules.validation.basis_applicability import check_basis_applicability_independently
    from test_basis_applicability import retrospective_publication

    source = retrospective_publication(kind, expired, renewed)
    child = resolve_basis_applicability(source)
    assert (child.outcome, child.reasons, child.witnesses) == (
        "UNAVAILABLE",
        ("SOURCE_UNQUALIFIED",),
        (),
    )
    assert check_basis_applicability_independently(source, child).decision == "CONSISTENT"
    i = input_for(source)
    negative = assert_negative(i, "SOURCE_UNAVAILABLE", "SOURCE_UNAUTHORIZED")
    assert negative.diagnostics[0].child_outcome == "UNAVAILABLE"
    assert negative.diagnostics[0].child_reason == "SOURCE_UNQUALIFIED"
    use = host.expected_policy_v2_use(i)
    valid_i = input_for(retrospective_publication(kind))
    positive = assert_positive(valid_i)
    for seam in ("child", "witness", "parent", "report"):
        data = canonical(positive)
        data["input_fingerprint"] = i.source_fingerprint
        data["identity_fingerprint"] = v.policy_v2_hash("identity", i.identity)
        ch = data["payload"]["reconstructed_basis_result"]
        ch["source_fingerprint"] = source.source_fingerprint
        if seam == "witness":
            ch["witnesses"][0]["assertion_fingerprint"] = "f" * 64
        if seam == "parent":
            data["payload"]["claims"][0]["constraint"]["upper"]["numerator"] += 1
        ch.pop("result_fingerprint")
        ch["result_fingerprint"] = b.basis_hash("result", ch)
        data.pop("result_fingerprint")
        forged_positive = v.NutritionPolicyResultV2(
            **data, result_fingerprint=v.policy_v2_hash("result", data)
        )
        assert check_policy_v2(i, forged_positive).decision == "INCONSISTENT"
        claimed_check = canonical(check_policy_v2(valid_i, positive))
        claimed_check.update(
            input_fingerprint=i.source_fingerprint,
            reconstructed_result_fingerprint=negative.result_fingerprint,
        )
        handoff = v.NutritionPolicyHandoffV2(
            contract_version="nutrition-policy-handoff.v2",
            input=i,
            result=negative if seam == "report" else forged_positive,
            retained_check=v.NutritionPolicyCheckV2.model_validate(claimed_check),
            environment="TEST_ONLY",
            validation_authority="UNVERIFIED_TRANSPORT",
            production_admission="CLOSED",
            planner_ready=False,
            activation_ready=False,
        )
        report = check_policy_handoff_v2(handoff, use)
        assert report.decision == "INCONSISTENT" and report.numerical_use == "NOT_ADMITTED"
        assert (
            host.consume_test_policy_v2(canonical(handoff), use).diagnostics[0].code
            == "ORIGIN_NOT_ESTABLISHED"
        )


@pytest.mark.parametrize("kind", ["WITHDRAW", "RETIRE"])
def test_piv_d25_withdrawal_is_distinct_from_historical_replay(day, kind):
    i, good = day
    data = canonical(i.basis_sources)
    pub = next(e for e in data["artifact"]["events"] if e["kind"] == "PUBLISH")
    data["artifact"]["events"].append(
        dict(
            pub,
            id="TEST_ONLY_withdraw",
            kind=kind,
            review_id=None,
            predecessor_publication_id=pub["id"],
        )
    )
    data["artifact"] = canonical(rehash_artifact(data["artifact"]))
    data["frame"]["artifact_fingerprint"] = data["artifact"]["artifact_fingerprint"]
    assert_negative(input_for(rehash_sources(data)), "SOURCE_UNAVAILABLE", "SOURCE_WITHDRAWN")
    assert check_policy_v2(i, good).decision == "CONSISTENT"


def test_piv_d26_lease_private_noncopyable_and_unissued_rejected(day):
    i, _ = day
    with pytest.raises(TypeError):
        host._Lease()
    handle = object.__new__(host._Lease)
    for copier in (copy, deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            copier(handle)
    assert (
        host.consume_test_policy_v2(handle, host.expected_policy_v2_use(i)).diagnostics[0].code
        == "ORIGIN_NOT_ESTABLISHED"
    )


def test_piv_d27_nonunit_required_period_sum_is_not_food_conversion():
    def edit(rule):
        next(x for x in rule["cases"][0]["operations"] if x["kind"] == "FINITE_PERIOD_SUM")[
            "coefficients"
        ][0] = dict(numerator=2, denominator=1)

    assert_negative(
        input_for(author_rule(positive_week(), edit)), "UNSUPPORTED", "UNSUPPORTED_TEMPORAL_MAP"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("environment", "PRODUCTION"),
        ("planner_ready", True),
        ("activation_ready", True),
        ("production_admission", "OPEN"),
    ],
)
def test_piv_d28_taint_closed_flags_reject_retagging(day, field, value):
    _, r = day
    data = canonical(r)
    data[field] = value
    with pytest.raises(ValueError):
        v.NutritionPolicyResultV2.model_validate(data)


@pytest.mark.parametrize(
    "module,target",
    [
        ("app.modules.validation.nutrition_policy_v2", "app.modules.nutrition.policy_v2"),
        ("app.modules.validation.nutrition_policy_v2", "app.modules.nutrition.synthesis"),
        (
            "app.modules.validation.nutrition_policy_v2_rules",
            "app.modules.validation.nutrition_policy",
        ),
        ("app.modules.nutrition.policy_v2", "app.modules.validation.nutrition_policy_v2"),
    ],
)
def test_piv_d29_independent_import_boundaries(module, target):
    checker = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]
    assert any(
        "POLICY_V2_PURE_OR_INDEPENDENT_BOUNDARY" in e for e in checker("import " + target, module)
    )
    for path in (ROOT / "apps/backend/app/modules/validation").glob("nutrition_policy_v2*.py"):
        assert not checker(path.read_text(), "app.modules.validation." + path.stem)


@pytest.mark.parametrize(
    "value",
    ['{"x":1,"x":2}', '{"x":0.5}', '{"x":NaN}', "[" * 33 + "]" * 33, '{"x":' + str(2**256) + "}"],
)
def test_piv_d30_parser_limits_before_arithmetic(value):
    with pytest.raises(ValueError):
        ingest(value, 32 * 1024 * 1024)


def test_piv_d30_exact_work_and_integer_boundaries():
    w = PolicyWork()
    w.charge(2_000_000)
    with pytest.raises(ValueError, match="RESOURCE_EXCEEDED"):
        w.charge()
    structure({"x": 2**256 - 1})
    with pytest.raises(ValueError, match="RESOURCE_EXCEEDED"):
        structure({"x": 2**256})


def test_piv_d31_all_frozen_definition_bodies_files_and_schema():
    proof = json.loads(
        (ROOT / "apps/backend/tests/fixtures/policy_v2_compatibility.json").read_text()
    )
    defs = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
    assert proof["base"] == "5b9441d1c10e5ad010a10f9e1af415c1ef50bd5a"
    assert len(proof["definitions"]) == 515 and len(proof["baseline_tests"]) == 4183
    additions = {
        "PolicyIntegrationIdentityV2",
        "NutritionPolicyIntegrationInputV2",
        "PolicyClaimCoverageV2",
        "PolicyAssignmentEvaluationV2",
        "PolicyCenterDeltaV2",
        "JointPolicySupportV2",
        "NutritionPolicyBodyV2",
        "PolicyDiagnosticV2",
        "NutritionPolicyResultV2",
        "NutritionPolicyCheckV2",
        "NutritionPolicyHandoffV2",
        "PolicyV2Use",
        "PolicyV2CaptureFailure",
    }
    manifest = json.loads(
        (ROOT / "apps/backend/tests/fixtures/policy_v2_export_names.json").read_text()
    )
    assert len(manifest) == 13 and set(manifest) == additions
    assert len(additions) == 13 and len(defs) == 528
    assert set(proof["definitions"]) <= set(defs)
    assert set(defs) - set(proof["definitions"]) == additions
    for name, expected in proof["definitions"].items():
        assert (
            hashlib.sha256(
                json.dumps(defs[name], sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            == expected
        ), name
    for path, expected in proof["frozen_files"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    for path, expected in proof["baseline_test_files"].items():
        assert hashlib.sha256(historical_test_preimage(path)).hexdigest() == expected, path
    assert not list((ROOT / "apps/backend/migrations/versions").glob("0018*"))


def historical_test_preimage(path):
    """Retain original hashes; allow only the owner's SEVEN exact export-metadata edits."""
    exceptions = {
        "apps/backend/tests/test_candidate_feature_projection.py": [
            (
                "    assert len(definitions) == 515  # 503 retained +12 additive MBA.",
                "    assert len(definitions) == 528  # 515 retained +13 additive policy v2.",
            )
        ],
        "apps/backend/tests/test_hierarchical_affinity_compatibility.py": [
            (
                "    assert "
                'len(pins["definitions"]) '
                "== 349 and len(schema) "
                "== 515  # 503 retained "
                "+12 additive MBA.",
                "    assert "
                'len(pins["definitions"]) '
                "== 349 and len(schema) "
                "== 528  # 515 retained "
                "+13 policy v2.",
            )
        ],
        "apps/backend/tests/test_hierarchy_compatibility.py": [
            (
                "    assert len(schema) == 515  # 503 retained +12 additive MBA definitions.",
                "    assert len(schema) == 528  # 515 retained +13 additive policy v2 definitions.",
            )
        ],
        "apps/backend/tests/test_nutrition_resolution.py": [
            (
                "    assert set(schema) == "
                '(set(proof["baseline_definitions"]) | '
                'set(proof["new_definitions"])\n'
                "                           | "
                'set(basis["new_definitions"]))',
                "    policy_v2 = "
                "json.loads((COMPAT.parent / "
                '"policy_v2_export_names.json").read_text())\n'
                "    assert set(schema) == "
                '(set(proof["baseline_definitions"]) | '
                'set(proof["new_definitions"])\n'
                "                           | "
                'set(basis["new_definitions"]) | '
                "set(policy_v2))",
            )
        ],
        "apps/backend/tests/test_nutrition_root_architecture.py": [
            (
                '    assert len(schema) == 503 + len(basis["new_definitions"])',
                "    policy_v2 = "
                "json.loads((FIXTURES / "
                '"policy_v2_export_names.json").read_text())\n'
                "    assert len(schema) == 528  "
                "# 515 retained +13 additive "
                "policy v2 definitions.",
            ),
            (
                '    ) | set(resolution["new_definitions"]) | set(basis["new_definitions"])',
                "    ) | "
                'set(resolution["new_definitions"]) '
                '| set(basis["new_definitions"]) '
                "| set(policy_v2)",
            ),
        ],
        "apps/backend/tests/test_shared_target_tastefit_architecture.py": [
            (
                "    later = "
                '(set(nutrition["new_definitions"]) '
                "| "
                'set(synthesis["new_definitions"])\n'
                "             | "
                'set(resolution["new_definitions"]) '
                "| "
                'set(basis["new_definitions"]))',
                "    policy_v2 = "
                "json.loads((FIXTURES / "
                '"policy_v2_export_names.json").read_text())\n'
                "    later = "
                '(set(nutrition["new_definitions"]) '
                "| "
                'set(synthesis["new_definitions"])\n'
                "             | "
                'set(resolution["new_definitions"]) '
                "| "
                'set(basis["new_definitions"]) '
                "| set(policy_v2))",
            )
        ],
        "apps/backend/tests/test_tastefit_architecture.py": [
            (
                "    assert len(defs) == (\n        384",
                "    policy_v2 = json.loads((FIXTURES "
                "/ "
                '"policy_v2_export_names.json").read_text())\n'
                "    assert len(defs) == 528  # 515 "
                "retained +13 additive policy v2 "
                "definitions.\n"
                "    assert len(defs) == (\n"
                "        384",
            ),
            (
                '        + len(basis["new_definitions"])\n    )',
                '        + len(basis["new_definitions"])\n        + len(policy_v2)\n    )',
            ),
            (
                '        + basis["new_definitions"]\n    )',
                '        + basis["new_definitions"]\n        + policy_v2\n    )',
            ),
        ],
    }
    body = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
    if path in exceptions:
        for old_text, permitted_text in exceptions[path]:
            old, permitted = old_text.encode(), permitted_text.encode()
            assert body.count(permitted + b"\n") == 1, path
            body = body.replace(permitted + b"\n", old + b"\n", 1)
    return body


def test_piv_d32_no_production_admission_no_authority_factory(day):
    i, r = day
    assert_positive(i, r)
    with pytest.raises(PermissionError, match="PRODUCTION_GATE_CLOSED"):
        admit_production_policy_v2(r)
    h = policy_v2_handoff(i)
    assert h.validation_authority == "UNVERIFIED_TRANSPORT" and h.retained_check is None
    report = check_policy_handoff_v2(h, host.expected_policy_v2_use(i))
    assert report.decision == "CONSISTENT"
    assert (
        host.consume_test_policy_v2(canonical(h), host.expected_policy_v2_use(i)).outcome
        == "ADMISSION_REJECTED"
    )
