"""NPS001–032 adversarial checks execute protected PostgreSQL functions, never mocks."""

import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from alembic import command as alembic
from alembic.config import Config
from app.domain.feature_identity import canonical
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.synthesis_admin import enroll_nutrition_synthesis_principal
from app.modules.nutrition.synthesis_journal import digest, replay_synthesis_sources
from app.modules.nutrition.synthesis_sources import capture_nutrition_synthesis_sources
from nutrition_root_fixtures import evidence
from nutrition_root_postgres_fixtures import nrc_server, reader  # noqa: F401
from nutrition_synthesis_postgres_fixtures import (
    append,
    capture_rules,
    command,
    grant_rule,
    publish,
    setup_synthesis,
)
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

pytestmark = pytest.mark.postgres


def protected(s, who, operation, body):
    with Session(s["engines"][who]) as db:
        result = db.scalar(
            text(f"SELECT menuto_nutrition_synthesis.{operation}(CAST(:c AS jsonb))"),
            {"c": json.dumps(canonical(body))},
        )
        db.commit()
        return result


def rejected(s, who, operation, body, match=None):
    with pytest.raises(DBAPIError, match=match):
        protected(s, who, operation, body)


def review_command(s):
    b = s["rule"]
    return command(
        s,
        dict(
            kind="REVIEW",
            revision_id=b.revision_id,
            body_fingerprint=digest("rule", b),
            evidence_fingerprint=digest("evidence-manifest", b.evidence),
            decision="APPROVE",
            prior_review_id=None,
        ),
    )


def publication_command(s, action="SUPERSEDE", **changes):
    b = s["rule"]
    body = dict(
        kind="PUBLICATION",
        revision_id=b.revision_id,
        body_fingerprint=digest("rule", b),
        action=action,
        review_id=s["rule_review"].id if action == "SUPERSEDE" else None,
        predecessor_publication_id=s["rule_publication"].id,
        effective_at=b.effective.start,
    )
    body.update(changes)
    return command(s, body)


def row_counts(s):
    with Session(s["engines"]["root"]) as db:
        return tuple(
            db.execute(
                text(
                    "SELECT revision,head_id,head_hash FROM nutrition_synthesis_streams "
                    "WHERE provider_id=:p AND family_id=:f"
                ),
                dict(p=s["rule_provider_id"], f=s["rule_family_id"]),
            ).one()
        )


@pytest.mark.parametrize("case", [f"NPS{i:03d}" for i in range(1, 33) if i != 23])
def test_real_synthesis_authority_obligation(case, nrc_server):  # noqa: F811
    if case == "NPS001":
        with Session(nrc_server["engines"]["root"]) as db:
            tables = (
                db.execute(
                    text(
                        "SELECT tablename FROM pg_tables WHERE schemaname='public' "
                        "AND tablename LIKE 'nutrition_synthesis_%' ORDER BY 1"
                    )
                )
                .scalars()
                .all()
            )
            assert len(tables) == 10
            assert all(db.scalar(text("SELECT count(*) FROM public." + t)) == 0 for t in tables)
            assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
        return
    s = setup_synthesis(nrc_server)
    b = s["rule"]
    draft = command(s, dict(kind="DRAFT", rule=b))
    if case == "NPS002":
        body = canonical(s["rule_provider"].command)
        body.update(provider_id=str(uuid4()), idempotency_key=uuid4().hex)
        rejected(s, "reviewer", "register_provider", body)
        return
    if case == "NPS003":
        raw = canonical(draft)
        raw["body"] = {"kind": "ENROLLMENT", "verified_human_id": str(uuid4())}
        rejected(s, "reviewer", "append", raw)
        return
    if case == "NPS004":
        principal = s["rule_principals"]["alias"]
        with s["engines"]["root"].connect() as db:
            assert (
                db.scalar(
                    text("SELECT oid::bigint FROM pg_roles WHERE rolname=:n"),
                    dict(n=s["names"]["alias"]),
                )
                == principal.role_oid
            )
        original = s["names"]["alias"]
        renamed = "TEST_ONLY_renamed_" + uuid4().hex[:12]
        try:
            with s["maintenance"].connect() as db:
                db.connection.driver_connection.execute(
                    sql.SQL("ALTER ROLE {} RENAME TO {}").format(
                        sql.Identifier(original), sql.Identifier(renamed)
                    )
                )
            rejected(s, "alias", "append", draft)
        finally:
            with s["maintenance"].connect() as db:
                db.connection.driver_connection.execute(
                    sql.SQL("ALTER ROLE {} RENAME TO {}").format(
                        sql.Identifier(renamed), sql.Identifier(original)
                    )
                )
        grant_rule(s, "alias", "SYNTHESIS_RULE_REVIEW")
        old_record = append(s, "alias", draft)
        old = s["rule_principals"]["alias"]
        replacement_command = canonical(old.command) | dict(
            expected_generation=old.generation,
            previous_enrollment_id=str(old.id),
            idempotency_key=uuid4().hex,
            evidence=canonical(evidence("TEST_ONLY explicit credential replacement")),
        )
        with Session(s["engines"]["synthesis_admin"]) as db:
            replacement = enroll_nutrition_synthesis_principal(db, replacement_command)
            db.commit()
        assert replacement.enrollment_root_id == old.enrollment_root_id
        assert replacement.generation == old.generation + 1 and replacement.id != old.id
        nrc_server["synthesis_principals"][s["names"]["alias"]] = replacement
        rejected(s, "alias", "append", old_record.command)
        return
    if case == "NPS005":
        raw = canonical(draft) | {"actor_user_id": str(s["user_id"])}
        rejected(s, "reviewer", "append", raw)
        # A trust-authenticated source role cannot acquire a source identity.
        with s["maintenance"].connect() as db:
            db.connection.driver_connection.execute(
                sql.SQL("GRANT menuto_nutrition_synthesis_client TO {}").format(
                    sql.Identifier(s["names"]["trust"])
                )
            )
        rejected(s, "trust", "append", draft)
        with Session(s["engines"]["reviewer"]) as db:
            db.execute(text("SET ROLE menuto_nutrition_synthesis_client"))
            with pytest.raises(DBAPIError):
                db.scalar(
                    text("SELECT menuto_nutrition_synthesis.append(CAST(:c AS jsonb))"),
                    dict(c=json.dumps(canonical(draft))),
                )
        return
    if case == "NPS006":
        rejected(s, "root", "append", draft)
        for unsafe_group in ("menuto_nutrition_synthesis_owner", "pg_read_all_data"):
            with s["maintenance"].connect() as db:
                db.connection.driver_connection.execute(
                    sql.SQL("GRANT {} TO {}").format(
                        sql.Identifier(unsafe_group), sql.Identifier(s["names"]["alias"])
                    )
                )
            try:
                rejected(s, "alias", "append", draft)
            finally:
                with s["maintenance"].connect() as db:
                    db.connection.driver_connection.execute(
                        sql.SQL("REVOKE {} FROM {}").format(
                            sql.Identifier(unsafe_group), sql.Identifier(s["names"]["alias"])
                        )
                    )
        return
    if case == "NPS007":
        for statement in (
            "SELECT * FROM nutrition_synthesis_drafts",
            "INSERT INTO nutrition_synthesis_drafts DEFAULT VALUES",
            "DELETE FROM nutrition_synthesis_drafts",
            "UPDATE nutrition_synthesis_streams SET revision=0",
            "TRUNCATE nutrition_synthesis_receipts",
            "SELECT menuto_nutrition_synthesis.permission(NULL,NULL,NULL,NULL,now())",
        ):
            with Session(s["engines"]["reviewer"]) as db, pytest.raises(DBAPIError):
                db.execute(text(statement))
        with s["engines"]["root"].connect() as db:
            assert not db.scalar(
                text(
                    "SELECT bool_or(has_function_privilege('public',p.oid,'EXECUTE')) "
                    "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                    "WHERE n.nspname='menuto_nutrition_synthesis'"
                )
            )
        return
    if case == "NPS008":
        with Session(s["engines"]["reviewer"]) as db:
            db.execute(text("CREATE TEMP TABLE nutrition_synthesis_grants (forged text)"))
            record = db.scalar(
                text("SELECT menuto_nutrition_synthesis.append(CAST(:c AS jsonb))"),
                dict(c=json.dumps(canonical(draft))),
            )
            db.commit()
        assert record["principal_id"] == str(s["rule_principals"]["reviewer"].id)
        return
    if case in {"NPS009", "NPS010"}:
        if case == "NPS009":
            grant_rule(s, "reviewer", "SYNTHESIS_RULE_REVIEW", action="REVOKE")
            rejected(s, "reviewer", "append", draft)
        else:
            rejected(s, "self", "append", draft)
            raw = canonical(draft)
            raw["capability"] = "SYNTHESIS_RULE_PUBLISH"
            rejected(s, "self", "append", raw)
        return
    if case == "NPS011":
        rejected(s, "publisher", "append", draft)
        wrong = canonical(draft)
        wrong["body"]["rule"]["applicability"]["scope_version"] = "TEST_ONLY_foreign"
        rejected(s, "reviewer", "append", wrong)
        wrong = canonical(draft)
        wrong["body"]["rule"]["environment"] = "REVIEWED_PRODUCTION"
        rejected(s, "reviewer", "append", wrong)
        return
    if case == "NPS012":
        append(s, "reviewer", draft)
        raw = command(
            s,
            dict(
                kind="PUBLICATION",
                revision_id=b.revision_id,
                body_fingerprint=digest("rule", b),
                action="PUBLISH",
                review_id=uuid4(),
                predecessor_publication_id=None,
                effective_at=b.effective.start,
            ),
        )
        rejected(s, "reviewer", "append", raw)
        rejected(s, "publisher", "append", raw)
        return
    publish(s)
    if case == "NPS013":
        grant_rule(s, "alias", "SYNTHESIS_RULE_PUBLISH")
        rejected(s, "alias", "append", publication_command(s))
    elif case == "NPS014":
        raw = canonical(publication_command(s))
        raw["body"]["body_fingerprint"] = "0" * 64
        rejected(s, "publisher", "append", raw)
        raw = canonical(review_command(s))
        raw["body"]["evidence_fingerprint"] = "1" * 64
        rejected(s, "reviewer", "append", raw)
    elif case == "NPS015":
        raw = canonical(publication_command(s))
        raw["body"]["review_id"] = str(s["rule_provider"].id)
        rejected(s, "publisher", "append", raw)
    elif case == "NPS016":
        old = s["rule_draft"]
        # Renewed qualification cannot resurrect an old review, even for an old
        # publication's identical command/receipt.
        grant_rule(s, "reviewer", "SYNTHESIS_RULE_REVIEW")
        rejected(s, "publisher", "append", s["rule_publication"].command)
        grant_rule(s, "reviewer", "SYNTHESIS_RULE_REVIEW", action="REVOKE")
        rejected(s, "reviewer", "append", old.command)
        rejected(s, "publisher", "append", s["rule_publication"].command)
    elif case in {"NPS017", "NPS022"}:
        first = review_command(s) if case == "NPS017" else publication_command(s)
        second = (
            c.NutritionSynthesisCommand.model_validate(
                canonical(first) | dict(event_id=str(uuid4()), idempotency_key=uuid4().hex)
            )
            if case == "NPS017"
            else publication_command(s, action="RETIRE")
        )
        who = "reviewer" if case == "NPS017" else "publisher"
        before = row_counts(s)[0]

        def attempt(cmd):
            try:
                append(s, who, cmd)
                return True
            except DBAPIError:
                return False

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(attempt, (first, second)))
        assert sum(outcomes) == 1
        assert row_counts(s)[0] == before + 1
    elif case == "NPS018":
        previous = s["rule_draft"]
        assert append(s, "reviewer", previous.command) == previous
        raw = canonical(previous.command) | dict(family_id="TEST_ONLY_other")
        rejected(s, "reviewer", "append", raw)
        grant_rule(s, "alias", "SYNTHESIS_RULE_REVIEW")
        rejected(s, "alias", "append", previous.command)
    elif case == "NPS019":
        before = capture_rules(s)
        append(s, "publisher", publication_command(s, action="RETRACT"))
        after = capture_rules(s)
        assert replay_synthesis_sources(before)[2] is None
        assert replay_synthesis_sources(after)[2] == "RULE_WITHDRAWN"
        assert len(after.records) == len(before.records) + 1
        with Session(s["engines"]["publisher"]) as db, pytest.raises(DBAPIError):
            db.execute(text("DELETE FROM nutrition_synthesis_publications"))
    elif case == "NPS020":
        retained = capture_rules(s)
        future = c.NutritionSynthesisRuleBody.model_validate(
            canonical(b)
            | dict(
                revision_id=str(uuid4()),
                authored_version="TEST_ONLY_future",
                effective=dict(start=canonical(b.effective)["start"], end="2026-09-03T00:00:00Z"),
            )
        )
        append(s, "reviewer", command(s, dict(kind="DRAFT", rule=future)))
        review = append(
            s,
            "reviewer",
            command(
                s,
                dict(
                    kind="REVIEW",
                    revision_id=future.revision_id,
                    body_fingerprint=digest("rule", future),
                    evidence_fingerprint=digest("evidence-manifest", future.evidence),
                    decision="APPROVE",
                    prior_review_id=None,
                ),
            ),
        )
        append(
            s,
            "publisher",
            command(
                s,
                dict(
                    kind="PUBLICATION",
                    revision_id=future.revision_id,
                    body_fingerprint=digest("rule", future),
                    action="SUPERSEDE",
                    review_id=review.id,
                    predecessor_publication_id=s["rule_publication"].id,
                    effective_at=b.effective.end,
                ),
            ),
        )
        current = capture_rules(s)
        assert replay_synthesis_sources(current)[2] is None
        assert replay_synthesis_sources(retained)[0] == retained
        assert current.source_fingerprint != retained.source_fingerprint
    elif case == "NPS021":
        from app.modules.nutrition.synthesis import synthesize_nutrition_policy

        # The protected source retains the complete approved body. A numeric
        # consumer cannot hide two applicable cases by pinning only one case.
        extra = canonical(b.cases[0]) | dict(id="TEST_ONLY_same_direction")
        ambiguous = c.NutritionSynthesisRuleBody.model_validate(
            canonical(b) | dict(revision_id=str(uuid4()), cases=[canonical(b.cases[0]), extra])
        )
        append(s, "reviewer", command(s, dict(kind="DRAFT", rule=ambiguous)))
        rv = append(
            s,
            "reviewer",
            command(
                s,
                dict(
                    kind="REVIEW",
                    revision_id=ambiguous.revision_id,
                    body_fingerprint=digest("rule", ambiguous),
                    evidence_fingerprint=digest("evidence-manifest", ambiguous.evidence),
                    decision="APPROVE",
                    prior_review_id=None,
                ),
            ),
        )
        pub = append(
            s,
            "publisher",
            command(
                s,
                dict(
                    kind="PUBLICATION",
                    revision_id=ambiguous.revision_id,
                    body_fingerprint=digest("rule", ambiguous),
                    action="SUPERSEDE",
                    review_id=rv.id,
                    predecessor_publication_id=s["rule_publication"].id,
                    effective_at=b.effective.start,
                ),
            ),
        )
        s.update(rule=ambiguous, rule_publication=pub)
        assert synthesize_nutrition_policy(capture_rules(s)).outcome == "CONFLICT"
    elif case == "NPS024":
        retained = capture_rules(s)
        for isolation, readonly in (("READ COMMITTED", True), ("REPEATABLE READ", False)):
            with (
                reader(s, "self", isolation=isolation, readonly=readonly) as db,
                pytest.raises((DBAPIError, ValueError)),
            ):
                capture_nutrition_synthesis_sources(db, retained.request)
        with reader(s, "self", readonly=False) as db:
            db.execute(text("CREATE TEMP TABLE nps_dirty(v int)"))
            with pytest.raises((DBAPIError, ValueError)):
                capture_nutrition_synthesis_sources(db, retained.request)
    elif case == "NPS025":
        request = capture_rules(s).request
        # Hold the first backend while acquiring another: a pool can otherwise
        # legitimately reuse the same backend and unchanged MVCC cut.
        with reader(s, "self") as first:
            retained = capture_nutrition_synthesis_sources(first, request)
            cmd = c.NutritionSynthesisCaptureCommand(
                root_request=retained.request.root.sources.request,
                root_frame=retained.request.root.sources.capture,
                selection=retained.request.selection,
                precision=retained.request.precision,
            )
            with reader(s, "self") as second, pytest.raises(DBAPIError):
                second.scalar(
                    text("SELECT menuto_nutrition_synthesis.capture(CAST(:c AS jsonb))"),
                    dict(c=json.dumps(canonical(cmd))),
                )
    elif case == "NPS026":
        retained = capture_rules(s)
        assert retained.frontier_revision == 3 and len(retained.records) == 3
        assert retained.frame.row_count == len(retained.records) + len(
            retained.provider_facts
        ) + len(retained.principal_facts) + len(retained.grant_facts) + len(
            retained.authority_frontiers
        ) + len(retained.principal_frontiers)
        with s["engines"]["root"].connect() as db:
            assert db.scalar(
                text(
                    "SELECT count(*) FROM nutrition_synthesis_receipts "
                    "WHERE provider_id=:p AND family_id=:f"
                ),
                dict(p=b.provider_id, f=b.family_id),
            ) == len(retained.records)
    elif case == "NPS027":
        retained = capture_rules(s)
        subject = retained.request.root.sources.request.subject
        assert all(
            x.command.identity.member_id in {None, subject.member_id}
            for x in retained.request.root.sources.sources
        )
        assert retained.precision_witness.subject == subject
    elif case == "NPS028":
        before = row_counts(s)
        variants = [
            canonical(review_command(s)) | dict(idempotency_key="x" * 140000),
            canonical(review_command(s)) | dict(expected_revision=2**200),
        ]
        nested = "TEST_ONLY"
        for _ in range(40):
            nested = [nested]
        variants.append(canonical(review_command(s)) | dict(forbidden_nested_payload=nested))
        for raw in variants:
            rejected(s, "reviewer", "append", raw)
        assert row_counts(s) == before
    elif case == "NPS029":
        request = capture_rules(s).request
        with reader(s, "self") as db:
            db.scalar(text("SELECT pg_current_snapshot()"))
            grant_rule(s, "self", "SYNTHESIS_SOURCE_READ", action="REVOKE")
            old = capture_nutrition_synthesis_sources(db, request)
            assert replay_synthesis_sources(old)[2] is None
        with pytest.raises(DBAPIError):
            capture_rules(s)
    elif case == "NPS030":
        raw = canonical(b)
        raw["revision_id"] = str(uuid4())
        item = canonical(
            evidence(
                "TEST_ONLY conflicting same evidence identity", evidence_id="TEST_ONLY_algebra"
            )
        )
        raw["evidence"] = [item]
        rejected(s, "reviewer", "append", command(s, dict(kind="DRAFT", rule=raw)))
    elif case == "NPS031":
        raw = canonical(s["rule_provider"].command) | dict(
            provider_id=str(uuid4()), environment="REVIEWED_PRODUCTION", idempotency_key=uuid4().hex
        )
        rejected(s, "synthesis_admin", "register_provider", raw)
        with s["engines"]["root"].connect() as db:
            assert (
                db.scalar(
                    text(
                        "SELECT count(*) FROM nutrition_synthesis_providers "
                        "WHERE command->>'environment'='REVIEWED_PRODUCTION'"
                    )
                )
                == 0
            )
    elif case == "NPS032":
        before = row_counts(s)
        config = Config(str(s["config"].config_file_name))
        with s["engines"]["root"].connect() as db:
            config.attributes["connection"] = db
            with pytest.raises(DBAPIError, match="Refusing destructive downgrade"):
                alembic.downgrade(config, "0016")
            db.rollback()
            assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
        assert row_counts(s) == before
    else:
        raise AssertionError("Unimplemented PG obligation " + case)
