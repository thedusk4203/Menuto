"""MBA013–MBA080: explicit, adversarial expectations for TEST_ONLY source semantics."""

import ast
import hashlib
import json
import pickle
import runpy
import subprocess
import sys
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition.basis_applicability import basis_handoff
from app.modules.nutrition.basis_applicability import resolve_basis_applicability as resolve
from app.modules.nutrition.basis_projection import project_basis_anchors
from app.modules.nutrition.resolution_limits import ingest
from app.modules.planning import basis_capture as capture
from app.modules.validation.basis_applicability import (
    check_basis_applicability_independently as check,
)
from app.modules.validation.basis_applicability import (
    check_basis_handoff_independently as handoff_check,
)
from basis_fixtures import reauthor_meaning, rehash_artifact, rehash_sources, retained

ROOT = Path(__file__).resolve().parents[3]


def changed(mutator, source=None):
    data = canonical(source or retained())
    mutator(data)
    return rehash_sources(data)


def edited_history(mutator, source=None):
    data = canonical(source or retained())
    mutator(data["artifact"]["events"])
    data["artifact"] = canonical(rehash_artifact(data["artifact"]))
    data["frame"]["artifact_fingerprint"] = data["artifact"]["artifact_fingerprint"]
    return rehash_sources(data)


def assertion_edit(mutator):
    def edit(events):
        review = next(e for e in events if e["kind"] == "REVIEW")
        mutator(review["assertion"])
        digest = b.basis_hash("assertion", review["assertion"])
        for event in events:
            if event["kind"] in {"REVIEW", "PUBLISH"}:
                event["assertion_fingerprint"] = digest

    return edited_history(edit)


def no_positive(source, expected=None):
    result = resolve(source)
    assert result.outcome != "APPLICABLE_TEST_ONLY", result
    assert not result.witnesses
    if expected:
        assert expected in result.reasons, result
    assert not result.planner_ready and not result.activation_ready
    return result


def lifecycle(kind, source=None, **changes):
    def append(events):
        pub = next(x for x in events if x["kind"] == "PUBLISH")
        event = dict(
            pub,
            id="TEST_ONLY_lifecycle",
            kind=kind,
            review_id=None,
            predecessor_publication_id=pub["id"],
        )
        event.update(changes)
        events.append(event)

    return edited_history(append, source)


def test_mba013_complete_same_meaning_positive():
    s = retained()
    result = resolve(s)
    assert result.outcome == "APPLICABLE_TEST_ONLY"
    assert len(result.witnesses) == 6
    assert check(s, result).decision == "CONSISTENT"


def test_mba014_token_alone_not_interpretation():
    s = reauthor_meaning(
        retained(),
        lambda d: [x["meaning"].update(interpretation_version="unknown") for x in d["claims"]],
    )
    assert no_positive(s).outcome == "UNSUPPORTED"


@pytest.mark.parametrize(
    "case,token",
    [
        (15, "PLANNED_OFFERED_FOOD_V1"),
        (16, "OBSERVED_OFFERED_FOOD_V1"),
        (17, "OBSERVED_CONSUMED_FOOD_V1"),
        (18, "PHYSIOLOGICAL_INTAKE_V1"),
        (19, "PHYSIOLOGICAL_INTAKE_V1"),
    ],
    ids=lambda x: str(x),
)
def test_mba015_mba019_no_quantity_inference(case, token):
    s = reauthor_meaning(
        retained(), lambda d: [x["meaning"].update(meaning=token) for x in d["claims"]]
    )
    result = no_positive(s, "CONVERSION_NOT_SUPPORTED")
    assert result.outcome == "UNSUPPORTED"
    assert check(s, result).decision == "CONSISTENT"


def test_mba020_unknown_vocabulary_never_fallback():
    data = canonical(retained().artifact.events[-2].assertion.meanings[0])
    data["meaning"] = "UNKNOWN"
    with pytest.raises(ValueError):
        b.MeasurementMeaningV1.model_validate(data)


def test_mba021_missing_original_meaning_legacy_unavailable():
    s = reauthor_meaning(retained(), lambda d: d.update(claims=[]))
    assert no_positive(s, "MEANING_MISSING").outcome == "UNAVAILABLE"


def test_mba022_external_cannot_override_original():
    s = assertion_edit(lambda a: a["meanings"][0].update(meaning="PHYSIOLOGICAL_INTAKE_V1"))
    no_positive(s, "ORIGINAL_MEANING_CONTRADICTION")
    original = reauthor_meaning(
        retained(),
        lambda body: [
            x["meaning"].update(meaning="PHYSIOLOGICAL_INTAKE_V1") for x in body["claims"]
        ],
    )

    def override(events):
        review = next(e for e in events if e["kind"] == "REVIEW")
        for row in review["assertion"]["meanings"]:
            row["meaning"] = "PLANNED_INGREDIENT_INPUT_V1"
        fingerprint = b.basis_hash("assertion", review["assertion"])
        for event in events:
            if event["kind"] in {"REVIEW", "PUBLISH"}:
                event["assertion_fingerprint"] = fingerprint

    contradictory = edited_history(override, original)
    no_positive(contradictory, "ORIGINAL_MEANING_CONTRADICTION")
    assert check(contradictory, resolve(retained())).decision == "INCONSISTENT"


def test_mba023_guideline_evidence_revision_exact():
    no_positive(
        assertion_edit(lambda a: a.update(original_sources=["0" * 64])), "ORIGINAL_SOURCE_MISMATCH"
    )


def test_mba024_rule_revision_case_operation_exact():
    no_positive(
        assertion_edit(lambda a: a["required_keys"].__setitem__(1, "rule:other:operation")),
        "ORIGINAL_SOURCE_MISMATCH",
    )


def test_mba025_exact_subject_not_household_aggregate():
    no_positive(
        assertion_edit(lambda a: a["subject"].update(member_id=str(uuid4()))),
        "SUBJECT_SCOPE_MISMATCH",
    )


def test_mba026_different_supported_population_not_applicable():
    s = assertion_edit(lambda a: a.update(scope_version="other"))
    assert no_positive(s).outcome == "NOT_APPLICABLE"


def test_mba027_qualification_required():
    s = edited_history(lambda es: es.__setitem__(8, es[8] | {"kind": "DISQUALIFY"}))
    assert no_positive(s).outcome == "UNAVAILABLE"


def test_mba028_scoped_capability_required():
    s = edited_history(lambda es: es.__setitem__(3, es[3] | {"kind": "REVOKE"}))
    no_positive(s, "CAPABILITY_UNAVAILABLE")


def test_mba029_alias_logins_not_distinct_subjects():
    s = edited_history(lambda es: es[1].update(principal_subject=es[0]["principal_subject"]))
    no_positive(s, "REVIEW_BINDING")


def test_mba030_review_binding_exact_body():
    no_positive(
        edited_history(lambda es: es[-1].update(assertion_fingerprint="0" * 64)), "REVIEW_BINDING"
    )


def test_mba031_unrelated_grants_not_basis_capability():
    s = canonical(retained().artifact.events[3])
    s["capability"] = "ROOT_SOURCE_READ"
    with pytest.raises(ValueError):
        b.BasisFixtureEventV1.model_validate(s)


def test_mba032_hash_reviewer_label_not_enrollment():
    no_positive(
        edited_history(lambda es: es[-1].update(principal="REVIEWED_REFERENCE")),
        "PRINCIPAL_NOT_ENROLLED",
    )


@pytest.mark.parametrize("mutation", ["duplicate", "reorder", "missing", "edited"])
def test_mba033_journal_identity(mutation):
    def edit(d):
        es = d["artifact"]["events"]
        if mutation == "duplicate":
            es[1] = deepcopy(es[0])
        elif mutation == "reorder":
            es[3], es[4] = es[4], es[3]
        elif mutation == "missing":
            es.pop(4)
        else:
            es[0]["principal_subject"] = "changed"

    no_positive(changed(edit))


def test_mba034_retained_replay_deterministic():
    s = retained()
    assert resolve(s) == resolve(canonical(s)) == resolve(json.dumps(canonical(s)))


def test_mba035_withdrawn_blocks_fresh_retained_old_unchanged():
    old = retained()
    new = lifecycle(
        "WITHDRAW", effective={"start": "2020-01-01T00:00:00Z", "end": "2100-01-01T00:00:00Z"}
    )
    assert no_positive(new).outcome == "UNAVAILABLE"
    assert resolve(old).outcome == "APPLICABLE_TEST_ONLY"


def test_mba036_retired_blocks_retrospective_admission():
    new = lifecycle(
        "RETIRE", effective={"start": "2020-01-01T00:00:00Z", "end": "2100-01-01T00:00:00Z"}
    )
    no_positive(new, "PUBLICATION_RETIRED")


def test_mba037_future_replacement_not_early():
    s = retained()
    future = (s.frame.completed_at + timedelta(days=1)).isoformat()
    es = canonical(s.artifact.events)
    pub = es[-1]
    replacement = dict(
        pub,
        id="TEST_ONLY_future",
        kind="SUPERSEDE",
        predecessor_publication_id=pub["id"],
        effective={"start": future, "end": "2100-01-01T00:00:00Z"},
    )
    # Different reviewed effective content cannot reuse the old review, even future-effective.
    no_positive(edited_history(lambda es: es.append(replacement)), "REVIEW_BINDING")
    future_retire = lifecycle("RETIRE", effective={"start": future, "end": "2100-01-01T00:00:00Z"})
    assert resolve(future_retire).outcome == "APPLICABLE_TEST_ONLY"


def test_mba038_cross_version_not_stitched():
    no_positive(assertion_edit(lambda a: a["effective"].update(end="2026-09-01T12:00:00Z")))


def test_mba039_retro_correction_not_mutate_retained():
    old = retained()
    identity = old.source_fingerprint
    no_positive(assertion_edit(lambda a: a.update(revision="corrected")))
    assert (
        retained().source_fingerprint == identity and resolve(old).outcome == "APPLICABLE_TEST_ONLY"
    )


def test_mba040_revocation_blocks_subsequent_action_not_old_publication():
    s = retained()
    revoke = canonical(s.artifact.events[4]) | dict(id="TEST_ONLY_pub_revoke", kind="REVOKE")
    good = edited_history(lambda es: es.append(revoke))
    assert resolve(good).outcome == "APPLICABLE_TEST_ONLY"

    def edit(es):
        pub = es.pop()
        es.append(revoke)
        es.append(pub)

    no_positive(edited_history(edit), "CAPABILITY_UNAVAILABLE")


def test_mba041_qualification_withdrawal_blocks_fresh_use():
    e = canonical(retained().artifact.events[7]) | dict(
        id="TEST_ONLY_disqualify", kind="DISQUALIFY"
    )
    no_positive(edited_history(lambda es: es.append(e)), "SOURCE_UNQUALIFIED")


def test_mba042_selection_explicit_no_latest():
    no_positive(
        changed(lambda d: d["selectors"].update(publication_id="missing")), "PUBLICATION_MISSING"
    )


@pytest.mark.parametrize(
    "case,field,value",
    [(43, "period_id", "foreign"), (44, "kind", "WEEK"), (45, "metric", "PROTEIN")],
)
def test_mba043_mba045_exact_descriptor(case, field, value):
    def edit(a):
        d = a["meanings"][0]["descriptor"]
        if field == "metric":
            d.update(metric=value, unit="G")
        else:
            d["temporal"][field] = value

    no_positive(assertion_edit(edit), "ORIGINAL_MEANING_CONTRADICTION")


def test_mba046_material_basis_not_identity_bridge():
    s = reauthor_meaning(
        retained(),
        lambda d: [x["meaning"].update(material_bases=["COOKED_G"]) for x in d["claims"]],
    )
    no_positive(s, "MATERIAL_BASIS_MISMATCH")


def test_mba047_converter_fields_forbidden():
    data = canonical(retained().artifact.events[-2].assertion.meanings[0])
    data["retention_coefficient"] = 1
    with pytest.raises(ValueError):
        b.MeasurementMeaningV1.model_validate(data)


def test_mba048_no_fractional_shared_serving():
    d = canonical(retained())
    d["nre"]["sources"]["scope"]["slots"][0]["alternatives"][0]["kind"] = "SHARED"
    with pytest.raises(ValueError):
        b.BasisApplicabilitySourcesV1.model_validate(d)


def test_mba049_pins_recomputed_not_public_hashes():
    no_positive(
        changed(lambda d: d["anchors"][0].update(requirement_fingerprint="0" * 64)),
        "REQUIRED_ANCHOR_MISSING",
    )


def test_mba050_comfort_manifest_not_all_claims():
    s = retained()
    assert len(s.nre.sources.requirements.measurements) == 1
    assert {x.layer for x in project_basis_anchors(s.nre)} == {
        "GUIDELINE_HARD",
        "GOAL_PROTECTION",
        "DAILY_PROTECTION",
        "COMFORT",
    }
    no_positive(
        changed(lambda d: d.update(anchors=[x for x in d["anchors"] if x["layer"] == "COMFORT"])),
        "REQUIRED_ANCHOR_MISSING",
    )


def test_mba051_ambiguous_lineage_not_favorable_selection():
    no_positive(
        changed(
            lambda d: d["nre"]["sources"]["synthesis_sources"]["request"]["selection"].update(
                language_version="FINITE_EXACT_V1", body_fingerprint="0" * 64
            )
        )
    )


def test_mba052_completed_policy_not_source_input():
    d = canonical(retained())
    d["nutrition_policy"] = {}
    with pytest.raises(ValueError):
        b.BasisApplicabilitySourcesV1.model_validate(d)


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "subset"])
def test_mba053_whole_manifest_required(mutation):
    def edit(d):
        if mutation == "missing":
            d["anchors"].pop()
        elif mutation == "extra":
            d["anchors"].append(d["anchors"][0] | {"key": "extra"})
        elif mutation == "duplicate":
            d["anchors"].append(d["anchors"][0])
        else:
            d["anchors"] = d["anchors"][:1]

    no_positive(changed(edit), "REQUIRED_ANCHOR_MISSING")


def test_mba054_missing_period_slot_not_zero():
    no_positive(changed(lambda d: d["nre"]["estimate"].update(periods=[])), "NRE_RESULT_FORGED")


def test_mba055_nre_available_and_independent_check_required():
    no_positive(
        changed(
            lambda d: d["nre"]["estimate"]["configurations"][0]["nutrients"][0].update(
                numerator=999
            )
        ),
        "NRE_RESULT_FORGED",
    )


def test_mba056_forged_nre_consistent_report_no_input():
    d = canonical(retained())
    d["nre"]["report"] = {
        "decision": "CONSISTENT",
        "source_fingerprint": d["nre"]["sources"]["source_fingerprint"],
    }
    assert (
        handoff_check({"sources": d, "result": canonical(resolve(retained()))}).decision
        == "INCONSISTENT"
    )


def test_mba057_forged_basis_positive_consistent_no_admission():
    s = changed(lambda d: d["anchors"].pop())
    r = canonical(resolve(retained()))
    r.update(source_fingerprint=s.source_fingerprint)
    assert check(s, r).decision == "INCONSISTENT"


def test_mba058_rehashed_meaning_mutation_detected_independently():
    s = assertion_edit(lambda a: a["meanings"][0].update(meaning="PHYSIOLOGICAL_INTAKE_V1"))
    r = resolve(retained()).model_copy(update={"source_fingerprint": s.source_fingerprint})
    assert check(s, r).decision == "INCONSISTENT"


def test_mba059_offline_consistency_not_origin():
    s = edited_history(lambda es: es[0].update(principal_subject="TEST_ONLY_alternative_human"))
    assert check(s, resolve(s)).decision == "CONSISTENT"
    assert resolve(s).source_origin == "NOT_PROVED_OFFLINE"
    with pytest.raises(PermissionError):
        capture.capture_test_basis_sources(canonical(s), None, s.selectors)


def test_mba060_reconstructed_or_serialized_context_rejected():
    fake = object.__new__(capture._HarnessContext)
    with pytest.raises(PermissionError):
        capture.capture_test_basis_sources(fake, None, retained().selectors)
    with pytest.raises(TypeError):
        pickle.dumps(fake)
    with pytest.raises(PermissionError):
        capture._HarnessContext()


def test_mba061_all_cached_fields_recomputed():
    r = resolve(retained()).model_copy(
        update={"planner_ready": True, "scientific_correctness": "CERTIFIED"}
    )
    assert check(retained(), r).decision == "INCONSISTENT"


def test_mba062_independence_enforced():
    guard = runpy.run_path(str(ROOT / "tools/check_import_boundaries.py"))["check_source"]
    assert guard(
        "from app.modules.nutrition.basis_applicability import resolve_basis_applicability",
        "app.modules.validation.basis_applicability",
    )
    assert guard(
        "from app.modules.validation.basis_applicability import check_basis_handoff_independently",
        "app.modules.nutrition.basis_applicability",
    )
    assert guard(
        "from app.modules.nutrition.basis_projection import project_basis_anchors",
        "app.modules.validation.basis_applicability",
    )


def test_mba063_qualification_symbolic_not_scientific():
    assert {e.qualification for e in retained().artifact.events if e.kind == "QUALIFY"} == {
        "SYMBOLIC_TEST_ONLY_NOT_SCIENTIFIC"
    }
    assert resolve(retained()).scientific_correctness == "NOT_CERTIFIED"


def test_mba064_no_production_relabel():
    d = canonical(retained())
    d["artifact"]["environment"] = "REVIEWED_PRODUCTION"
    with pytest.raises(ValueError):
        b.BasisApplicabilitySourcesV1.model_validate(d)


def test_mba065_no_default_registry_or_request_installer():
    assert not hasattr(capture, "install_fixture")
    with pytest.raises(PermissionError):
        capture.capture_test_basis_sources(None, None, retained().selectors)


def test_mba066_full_history_absences_affect_identity():
    s = retained()
    new = changed(lambda d: d.update(absences=["missing"]))
    assert new.source_fingerprint != s.source_fingerprint
    no_positive(new)


@pytest.mark.parametrize(
    "payload",
    [b'{"x":1,"x":2}', b" " * (65536 + 1), b"[" * 33 + b"]" * 33],
    ids=["duplicate-key", "bytes", "depth"],
)
def test_mba067_ingress_bounds_before_parse(payload):
    with pytest.raises(ValueError):
        b.parse_basis(payload, b.BasisSelectorsV1, 65536)


@pytest.mark.parametrize(
    "payload",
    [{"x": 1 << 256}, {"x": "a" * 100001}, {"x": 1.5}],
    ids=["integer", "string", "float"],
)
def test_mba068_absolute_structure_limits(payload):
    with pytest.raises(ValueError):
        ingest(payload)


def test_mba069_work_overflow_all_or_error():
    s = changed(lambda d: d["selectors"].update(max_work=1))
    assert no_positive(s).outcome == "RESOURCE_EXCEEDED"
    assert check(s, resolve(s)).decision == "CONSISTENT"


def test_mba070_host_timeout_no_success():
    from concurrent.futures import TimeoutError

    from app.modules.planning.basis_host import _run_bounded

    calls = []

    class TimeoutExecutor:
        def __init__(self, *, max_workers):
            assert max_workers == 1

        def submit(self, operation):
            return self

        def result(self, *, timeout):
            assert timeout == 10
            raise TimeoutError()

        def shutdown(self, **kwargs):
            calls.append(kwargs)

    with pytest.raises(ValueError, match="RESOURCE_EXCEEDED"):
        _run_bounded(lambda: None, executor_factory=TimeoutExecutor)
    assert calls == [{"wait": False, "cancel_futures": True}]


def test_mba071_pure_modules_no_io_or_clock():
    modules = [
        "nutrition/basis_applicability.py",
        "nutrition/basis_projection.py",
        "validation/basis_applicability.py",
    ]
    for path in modules:
        tree = ast.parse((ROOT / "apps/backend/app/modules" / path).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(
                    n.name.split(".")[0] not in {"os", "time", "sqlalchemy", "pathlib", "socket"}
                    for n in node.names
                )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__"}


def test_mba072_no_numeric_conversion_or_amount_output():
    fields = b.BasisApplicabilityResultV1.model_fields
    assert not {"amount", "coefficient", "target", "nutrients", "conversion"} & fields.keys()


def test_mba073_original_hard_root_untouched():
    s = retained()
    before = canonical(s.nre.sources.synthesis_sources.request.root)
    resolve(s)
    assert canonical(s.nre.sources.synthesis_sources.request.root) == before


@pytest.mark.parametrize(
    "axis", ["CostPreference", "Budget", "KitchenEffort", "TasteFit", "NutritionPrecision"]
)
def test_mba074_preferences_cannot_mint_meaning(axis):
    d = canonical(retained())
    d[axis] = "RELAXED"
    with pytest.raises(ValueError):
        b.BasisApplicabilitySourcesV1.model_validate(d)


def test_mba075_gaps_not_safety_or_solver_feasibility():
    result = resolve(retained())
    assert (
        result.hard_policy_feasibility == "NOT_EVALUATED"
        and result.solver_infeasibility == "NOT_PROVEN"
    )


def test_mba076_handoff_unverified_detached_report_not_credential():
    h = basis_handoff(retained())
    assert h.validation_authority == "UNVERIFIED_TRANSPORT"
    data = canonical(h)
    data["report"] = canonical(handoff_check(h))
    assert handoff_check(data).decision == "INCONSISTENT"


def test_mba077_frozen_files_and_baseline_identity_retained():
    proof = json.loads((Path(__file__).parent / "fixtures/basis_compatibility.json").read_text())
    for name, digest in proof["frozen_files"].items():
        assert hashlib.sha256((ROOT / name).read_text().encode()).hexdigest() == digest, name
    collected = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-o", "addopts="],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    ).stdout
    import re
    from collections import Counter

    def normalize(s):
        return re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<UUID>", s)

    current = Counter(normalize(line) for line in collected.splitlines() if "::" in line)
    assert not Counter(map(normalize, proof["baseline_tests"])) - current
    assert len(proof["baseline_tests"]) == 4047


def test_mba078_all_503_definitions_unchanged():
    proof = json.loads((Path(__file__).parent / "fixtures/basis_compatibility.json").read_text())
    defs = json.loads((ROOT / "packages/contracts/domain.schema.json").read_text())["$defs"]
    assert len(proof["definitions"]) == 503
    for name, digest in proof["definitions"].items():
        assert (
            hashlib.sha256(
                json.dumps(defs[name], sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            == digest
        ), name


def test_mba079_no_new_persistence_or_source_permissions():
    import app.persistence.models  # noqa:F401
    from app.persistence.models import Base

    assert len(Base.metadata.tables) == 108
    assert not list((ROOT / "apps/backend/migrations/versions").glob("0018*"))
    assert not any("basis" in t for t in Base.metadata.tables)


def test_mba080_no_activation_or_parent_completion():
    r = resolve(retained())
    assert (r.planner_ready, r.activation_ready, r.production_admission, r.policy_integration) == (
        False,
        False,
        "CLOSED",
        "NOT_AUTHORIZED",
    )


def test_mba037_valid_future_supersession_preserves_old_cut():
    s = retained()
    boundary = (s.frame.completed_at + timedelta(days=1)).isoformat()

    def edit(events):
        prior = deepcopy(events[-2])
        published = deepcopy(events[-1])
        prior["id"] = "TEST_ONLY_new_review"
        prior["assertion"]["revision"] = "v2"
        prior["assertion"]["effective"] = {"start": boundary, "end": "2100-01-01T00:00:00Z"}
        prior["effective"] = prior["assertion"]["effective"]
        prior["assertion"] = canonical(b.BasisAssertionV1.model_validate(prior["assertion"]))
        prior["assertion_fingerprint"] = b.basis_hash("assertion", prior["assertion"])
        published.update(
            id="TEST_ONLY_next_publication",
            kind="SUPERSEDE",
            assertion_fingerprint=prior["assertion_fingerprint"],
            review_id=prior["id"],
            predecessor_publication_id=published["id"],
            effective=prior["effective"],
        )
        events.extend([prior, published])

    new = edited_history(edit)
    assert resolve(new).outcome == "APPLICABLE_TEST_ONLY"
    assert check(new, resolve(new)).decision == "CONSISTENT"
    assert resolve(s).outcome == "APPLICABLE_TEST_ONLY"


def test_mba042_competing_explicit_publications_rejected():
    def edit(es):
        es.append(es[-1] | {"id": "TEST_ONLY_competing_publication"})

    no_positive(edited_history(edit), "PUBLICATION_AMBIGUOUS")


def test_mba067_duplicate_original_json_not_authority():
    from app.modules.nutrition.basis_projection import original_preimage
    from app.modules.nutrition.root_contracts import NutritionSourceEvidence, nutrition_root_hash

    body = (
        '{"schema":"test-only.measurement-meaning.v1",'
        '"environment":"TEST_ONLY","claims":[],"claims":[]}'
    )
    evidence = NutritionSourceEvidence(
        evidence_id="TEST_ONLY_duplicates",
        version="v1",
        environment="TEST_ONLY",
        purpose="TEST_ONLY",
        body=body,
        body_fingerprint=nutrition_root_hash("nutrition.evidence-body.v1", body),
    )
    with pytest.raises(ValueError, match="duplicate"):
        original_preimage((evidence,), "root:x")


def test_mba060_append_only_registry_rejects_history_edit():
    from types import SimpleNamespace

    s = retained()
    context = capture._install_isolated_basis_fixture(
        SimpleNamespace(
            database_oid=s.artifact.database_oid, database_name=s.artifact.database_name
        ),
        s.artifact,
        reader_principal="reader",
        actor_user_id=s.nre.sources.scope.actor_user_id,
    )
    data = canonical(s.artifact)
    data.update(revision=2, previous_artifact_fingerprint=s.artifact.artifact_fingerprint)
    data["events"][0]["principal_subject"] = "changed"
    data["events"].append(data["events"][6] | {"id": "TEST_ONLY_revoke", "kind": "REVOKE"})
    with pytest.raises(ValueError, match="HISTORY_REWRITTEN"):
        capture._advance_isolated_basis_fixture(context, rehash_artifact(data))
    capture._revoke_isolated_basis_context(context)


def test_mba070_actual_host_reconstructs_not_detached_report():
    from app.modules.planning.basis_host import reconstruct_test_basis_handoff

    h = reconstruct_test_basis_handoff(retained())
    assert (
        h.result.outcome == "APPLICABLE_TEST_ONLY"
        and h.validation_authority == "UNVERIFIED_TRANSPORT"
    )


@pytest.mark.parametrize("kind", ["REVOKE", "DISQUALIFY"])
def test_mba037_future_authority_change_not_early(kind):
    s = retained()
    boundary = (s.frame.completed_at + timedelta(days=1)).isoformat()
    old = canonical(s.artifact.events[6 if kind == "REVOKE" else 7])
    old.update(
        id="TEST_ONLY_future_authority",
        kind=kind,
        effective={"start": boundary, "end": "2100-01-01T00:00:00Z"},
    )
    future = edited_history(lambda es: es.append(old))
    assert resolve(future).outcome == "APPLICABLE_TEST_ONLY"
    assert check(future, resolve(future)).decision == "CONSISTENT"


@pytest.mark.parametrize("complete_week", [False, True], ids=["missing-week", "retained-week"])
def test_mba050_full_week_anchors_need_original_period(complete_week):
    from basis_fixtures import weekly_basis_sources

    s = weekly_basis_sources(complete_week)
    r = resolve(s)
    assert "WEEKLY_GOAL" in {a.layer for a in s.anchors}
    if complete_week:
        assert r.outcome == "APPLICABLE_TEST_ONLY", r.reasons
        assert len(r.witnesses) == len(s.anchors) > 30
    else:
        assert r.outcome == "UNAVAILABLE" and r.reasons == ("TEMPORAL_COVERAGE_MISSING",), r
        assert not r.witnesses
    assert check(s, r).decision == "CONSISTENT"
