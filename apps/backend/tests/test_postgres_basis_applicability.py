"""MBA001–MBA012 actual PostgreSQL protected-reader obligations."""

import json
from pathlib import Path

import pytest
from app.domain.feature_identity import canonical
from app.modules.nutrition.basis_applicability import basis_handoff, resolve_basis_applicability
from app.modules.planning import basis_capture as capture_module
from app.modules.validation.basis_applicability import check_basis_handoff_independently
from basis_postgres_fixtures import capture_basis, mba_case, nre_case  # noqa: F401
from nutrition_root_postgres_fixtures import nrc_server, reader  # noqa: F401
from test_postgres_foundation import postgres_engine  # noqa: F401

pytestmark = pytest.mark.postgres


def test_mba001_complete_ordinary_reader(mba_case):  # noqa: F811
    sources = capture_basis(mba_case)
    result = resolve_basis_applicability(sources)
    assert result.outcome == "APPLICABLE_TEST_ONLY", result.reasons
    assert check_basis_handoff_independently(basis_handoff(sources)).decision == "CONSISTENT"
    assert len(result.witnesses) == len(sources.anchors) == 6
    # An explicitly requested local evidence export, never part of normal test side effects.
    import os

    if os.environ.get("MENUTO_WRITE_MBA_TEST_FIXTURE") == "1":
        Path(__file__).with_name("fixtures").joinpath("basis_retained_TEST_ONLY.json").write_text(
            json.dumps(canonical(sources), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


@pytest.mark.parametrize("field", ["database_oid", "database_name", "deployment"])
def test_mba002_context_database_deployment_binding(mba_case, field):  # noqa: F811
    from basis_fixtures import rehash_artifact

    data = canonical(mba_case["basis_artifact"])
    data[field] = data[field] + 1 if field == "database_oid" else "TEST_ONLY_foreign"
    if field == "deployment":
        with reader(mba_case, "self") as db:
            with pytest.raises(PermissionError, match="FORGED_CONTEXT"):  # noqa: F811
                capture_module.capture_test_basis_sources(data, db, mba_case["basis_selectors"])
    else:
        with pytest.raises((PermissionError, ValueError)):  # noqa: F811
            capture_module._install_isolated_basis_fixture(
                mba_case["nre_context"],
                rehash_artifact(data),
                reader_principal="reader",
                actor_user_id=mba_case["user_id"],
            )


@pytest.mark.parametrize("identity", ["set_role", "wrong_login", "spoof_actor"])
def test_mba003_actual_authentication(mba_case, identity):  # noqa: F811
    from uuid import uuid4

    from app.modules.nutrition.basis_contracts import BasisSelectorsV1
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    s = mba_case
    selectors = s["basis_selectors"]
    if identity == "spoof_actor":
        data = canonical(selectors)
        data["nre_scope"]["actor_user_id"] = str(uuid4())
        selectors = BasisSelectorsV1.model_validate(data)
    with reader(s, "other" if identity == "wrong_login" else "self") as db:
        if identity == "set_role":
            db.execute(text("SET ROLE menuto_nutrition_client"))
        with pytest.raises((PermissionError, DBAPIError)):  # noqa: F811
            capture_module.capture_test_basis_sources(s["basis_context"], db, selectors)


def test_mba004_revoke_reader_fresh_vs_retained(mba_case):  # noqa: F811
    from nutrition_root_postgres_fixtures import grant
    from sqlalchemy.exc import DBAPIError

    old = capture_basis(mba_case)
    grant(mba_case, "self", "ROOT_SOURCE_READ", action="REVOKE")
    with pytest.raises((PermissionError, DBAPIError)):  # noqa: F811
        capture_basis(mba_case)
    assert check_basis_handoff_independently(basis_handoff(old)).decision == "CONSISTENT"


def test_mba005_concurrent_reference_uses_one_cut(mba_case):  # noqa: F811
    from sqlalchemy import text
    from test_postgres_nutrition_resolution import add_reference

    s = mba_case
    with reader(s, "self") as db:
        db.scalar(text("SELECT count(*) FROM nutrition_facts"))
        snapshot = db.scalar(text("SELECT pg_current_snapshot()::text"))
        add_reference(s)
        old = capture_module.capture_test_basis_sources(
            s["basis_context"], db, s["basis_selectors"]
        )
        assert old.nre.sources.frame.source_frame.mvcc_snapshot == snapshot
        assert resolve_basis_applicability(old).outcome == "APPLICABLE_TEST_ONLY"
    with pytest.raises(PermissionError):  # noqa: F811
        capture_basis(s)


@pytest.mark.parametrize("missing", ["reference", "tier", "recipe", "rule", "serving"])
def test_mba006_missing_canonical_not_replaced_by_artifact(mba_case, missing):  # noqa: F811
    from uuid import uuid4

    from app.modules.nutrition.basis_contracts import BasisSelectorsV1

    s = mba_case
    data = canonical(s["basis_selectors"])
    scope = data["nre_scope"]
    if missing == "reference":
        scope["references"][0]["reference_id"] = str(uuid4())
    elif missing == "tier":
        scope["recipes"][0]["tier_ids"] = [str(uuid4())]
    elif missing == "recipe":
        scope["recipes"][0]["recipe_version_id"] = str(uuid4())
    elif missing == "rule":
        scope["recipes"][0]["rule_selections"] = [[str(uuid4())]]
    else:
        scope["slots"][0]["alternatives"] = []
    s["basis_selectors"] = BasisSelectorsV1.model_validate(data)
    try:
        captured = capture_basis(s)
    except (ValueError, PermissionError):  # noqa: F811
        return
    assert resolve_basis_applicability(captured).outcome != "APPLICABLE_TEST_ONLY"


@pytest.mark.parametrize("kind", ["FOREIGN_SUBJECT", "VIEWER"])
def test_mba007_exact_member_membership(mba_case, kind):  # noqa: F811
    from uuid import uuid4

    from app.modules.nutrition.basis_contracts import BasisSelectorsV1
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from sqlalchemy.orm import Session

    s = mba_case
    if kind == "FOREIGN_SUBJECT":
        data = canonical(s["basis_selectors"])
        data["nre_scope"]["subject"]["member_id"] = str(uuid4())
        s["basis_selectors"] = BasisSelectorsV1.model_validate(data)
    else:
        with Session(s["engines"]["root"]) as db:
            db.execute(
                text("UPDATE memberships SET role='VIEWER' WHERE user_id=:u"), {"u": s["user_id"]}
            )
            db.commit()
    with pytest.raises((ValueError, PermissionError, DBAPIError)):  # noqa: F811
        capture_basis(s)


@pytest.mark.parametrize("mode", ["writable", "dirty", "routed", "multiple", "schema"])
def test_mba008_frozen_capture_guards(mba_case, mode):  # noqa: F811
    from app.modules.catalog.models import Ingredient
    from sqlalchemy.orm import Session

    s = mba_case
    with reader(s, "self", readonly=mode != "writable") as db:
        if mode == "dirty":
            db.add(Ingredient(name="TEST_ONLY never flushed"))
        target = [db, db] if mode == "multiple" else db
        if mode == "routed":
            with Session(s["engines"]["self"], binds={Ingredient: s["engines"]["root"]}) as routed:
                with pytest.raises(ValueError):  # noqa: F811
                    capture_module.capture_test_basis_sources(
                        s["basis_context"], routed, s["basis_selectors"]
                    )
            return
        if mode == "schema":
            with Session(
                s["engines"]["self"], execution_options={"schema_translate_map": {None: "pg_temp"}}
            ) as translated:
                with pytest.raises(ValueError):  # noqa: F811
                    capture_module.capture_test_basis_sources(
                        s["basis_context"], translated, s["basis_selectors"]
                    )
            return
        with pytest.raises((ValueError, AttributeError)):  # noqa: F811
            capture_module.capture_test_basis_sources(
                s["basis_context"], target, s["basis_selectors"]
            )


def test_mba009_republished_rule_not_old_assertion(mba_case):  # noqa: F811
    from uuid import uuid4

    from app.modules.nutrition.basis_contracts import BasisSelectorsV1
    from app.modules.nutrition.synthesis_contracts import NutritionSynthesisRuleBody
    from app.modules.nutrition.synthesis_journal import digest
    from nutrition_synthesis_postgres_fixtures import append, capture_rules, command

    s = mba_case
    s["rule"] = NutritionSynthesisRuleBody.model_validate(
        canonical(s["rule"]) | {"revision_id": str(uuid4())}
    )
    body = s["rule"]
    append(s, "reviewer", command(s, dict(kind="DRAFT", rule=body)))
    review = append(
        s,
        "reviewer",
        command(
            s,
            dict(
                kind="REVIEW",
                revision_id=body.revision_id,
                body_fingerprint=digest("rule", body),
                evidence_fingerprint=digest("evidence-manifest", body.evidence),
                decision="APPROVE",
                prior_review_id=None,
            ),
        ),
    )
    s["rule_publication"] = append(
        s,
        "publisher",
        command(
            s,
            dict(
                kind="PUBLICATION",
                revision_id=body.revision_id,
                body_fingerprint=digest("rule", body),
                action="SUPERSEDE",
                review_id=review.id,
                predecessor_publication_id=s["rule_publication"].id,
                effective_at=body.effective.start,
            ),
        ),
    )
    rules = capture_rules(s)
    data = canonical(s["basis_selectors"])
    data["nre_scope"]["selection"] = canonical(rules.request.selection)
    s["basis_selectors"] = BasisSelectorsV1.model_validate(data)
    assert resolve_basis_applicability(capture_basis(s)).outcome == "REJECTED"


@pytest.mark.parametrize("change", ["frontier", "reader"])
def test_mba010_registry_change_during_actual_capture(mba_case, monkeypatch, change):  # noqa: F811
    from basis_fixtures import rehash_artifact

    s = mba_case
    frozen = capture_module.capture_nutrition_resolution_sources

    def changed(*args):  # noqa: F811
        result = frozen(*args)
        if change == "reader":
            capture_module._revoke_isolated_basis_context(s["basis_context"])
        else:
            data = canonical(s["basis_artifact"])
            data.update(
                revision=2, previous_artifact_fingerprint=s["basis_artifact"].artifact_fingerprint
            )
            data["events"].append(
                data["events"][6] | {"id": "TEST_ONLY_read_revoke", "kind": "REVOKE"}
            )
            capture_module._advance_isolated_basis_fixture(
                s["basis_context"], rehash_artifact(data)
            )
        return result

    monkeypatch.setattr(capture_module, "capture_nutrition_resolution_sources", changed)
    with pytest.raises(PermissionError, match="REGISTRY_FRONTIER_CHANGED"):  # noqa: F811
        capture_basis(s)


def test_mba011_fresh_install_no_basis_objects_or_content(postgres_engine):  # noqa: F811
    from sqlalchemy import inspect, text
    from sqlalchemy.orm import Session

    with Session(postgres_engine) as db:
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
        tables = inspect(db.connection()).get_table_names()
        assert len(tables) == 109 and not any("basis" in t for t in tables)
        for name in tables:
            if name.startswith("nutrition_"):
                assert db.scalar(text('SELECT count(*) FROM public."' + name + '"')) == 0, name
        # Each other case uses a distinct synthetic provider; a separate fresh DB has no rows.
        assert (
            db.scalar(
                text(
                    "SELECT count(*) FROM nutrition_source_providers "
                    "WHERE environment='REVIEWED_PRODUCTION'"
                )
            )
            == 0
        )


def test_mba012_forged_positive_report_not_admission(mba_case):  # noqa: F811
    from app.modules.nutrition import basis_contracts as b
    from basis_fixtures import rehash_sources

    sources = capture_basis(mba_case)
    handoff = basis_handoff(sources)
    data = canonical(sources)
    data["anchors"] = data["anchors"][:-1]
    bad = rehash_sources(data)
    forged = canonical(handoff.result)
    forged["source_fingerprint"] = bad.source_fingerprint
    forged.pop("result_fingerprint")
    forged["result_fingerprint"] = b.basis_hash("result", forged)
    report = b.BasisApplicabilityCheckV1(
        decision="CONSISTENT",
        findings=(),
        reconstructed_result_fingerprint=forged["result_fingerprint"],
    )
    assert report.decision == "CONSISTENT"  # Wire data, never accepted as an argument/proof.
    assert (
        check_basis_handoff_independently(dict(sources=canonical(bad), result=forged)).decision
        == "INCONSISTENT"
    )
