"""Real isolated TEST_ONLY PostgreSQL source setup; no production seed artifacts."""

from uuid import uuid4

from app.domain.feature_identity import canonical
from app.modules.nutrition import root_public
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.synthesis_admin import (
    change_nutrition_synthesis_authority,
    enroll_nutrition_synthesis_principal,
    register_nutrition_synthesis_provider,
)
from app.modules.nutrition.synthesis_journal import applicability, digest
from app.modules.nutrition.synthesis_sources import (
    append_nutrition_synthesis_rule,
    capture_nutrition_synthesis_sources,
)
from nutrition_root_fixtures import authority_interval, evidence
from nutrition_root_postgres_fixtures import capture, grant, prepare_nrc, reader
from nutrition_synthesis_fixtures import rule
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.orm import Session


def grant_rule(s, who, capability, action="GRANT", **changes):
    with Session(s["engines"]["root"]) as db:
        old = db.execute(
            text(
                "SELECT id,generation FROM nutrition_synthesis_grants WHERE "
                "provider_id=:p AND family_id=:f AND principal_id=:who AND capability=:cap "
                "ORDER BY generation DESC LIMIT 1"
            ),
            dict(
                p=s["rule_provider_id"],
                f=s["rule_family_id"],
                who=s["rule_principals"][who].id,
                cap=capability,
            ),
        ).first()
    command = dict(
        provider_id=s["rule_provider_id"],
        family_id=s["rule_family_id"],
        principal_id=s["rule_principals"][who].id,
        capability=capability,
        action=action,
        applicability=applicability(s["root"].sources.request),
        effective=authority_interval(),
        evidence=evidence("TEST_ONLY synthesis authority, no production qualifications"),
        expected_generation=old.generation if old else 0,
        predecessor_id=old.id if old else None,
        idempotency_key=uuid4().hex,
    )
    command.update(changes)
    with Session(s["engines"]["synthesis_admin"]) as db:
        result = change_nutrition_synthesis_authority(db, command)
        db.commit()
    return result


def command(s, body, **changes):
    with Session(s["engines"]["root"]) as db:
        st = db.execute(
            text(
                "SELECT revision,head_id FROM nutrition_synthesis_streams "
                "WHERE provider_id=:p AND family_id=:f"
            ),
            dict(p=s["rule_provider_id"], f=s["rule_family_id"]),
        ).first()
    data = dict(
        provider_id=s["rule_provider_id"],
        family_id=s["rule_family_id"],
        event_id=uuid4(),
        expected_revision=st.revision if st else 0,
        predecessor_id=st.head_id if st else None,
        idempotency_key=uuid4().hex,
        body=body,
    )
    data.update(changes)
    return c.NutritionSynthesisCommand(**data)


def append(s, who, value):
    with Session(s["engines"][who]) as db:
        result = append_nutrition_synthesis_rule(db, value)
        db.commit()
    return result


def setup_synthesis(server):
    s = prepare_nrc(server)
    grant(s, "self", "ROOT_SOURCE_READ")
    s["root"] = root_public.resolve_nutrition_root(capture(s, who="self"))
    server["create_role"]("synthesis_admin", group="menuto_nutrition_synthesis_admin")
    s["engines"] = dict(s["engines"], synthesis_admin=server["engines"]["synthesis_admin"])
    s["rule_provider_id"], s["rule_family_id"] = uuid4(), "TEST_ONLY_rules_" + uuid4().hex[:10]
    s["rule_principals"] = {}
    cached_principals = server.setdefault("synthesis_principals", {})
    for who in ("reviewer", "publisher", "alias", "reader", "self"):
        with server["maintenance"].connect() as db:
            db.connection.driver_connection.execute(
                sql.SQL("GRANT menuto_nutrition_synthesis_client TO {}").format(
                    sql.Identifier(s["names"][who])
                )
            )
        prior = s["principals"][who]
        if s["names"][who] in cached_principals:
            s["rule_principals"][who] = cached_principals[s["names"][who]]
            continue
        with Session(s["engines"]["synthesis_admin"]) as db:
            result = enroll_nutrition_synthesis_principal(
                db,
                dict(
                    role_name=s["names"][who],
                    verified_human_id=prior.command.verified_human_id,
                    user_id=prior.command.user_id,
                    service_id=prior.command.service_id,
                    evidence=evidence("TEST_ONLY independent synthesis enrollment"),
                    idempotency_key=uuid4().hex,
                ),
            )
            db.commit()
        s["rule_principals"][who] = result
        cached_principals[s["names"][who]] = result
    with Session(s["engines"]["synthesis_admin"]) as db:
        s["rule_provider"] = register_nutrition_synthesis_provider(
            db,
            dict(
                provider_id=s["rule_provider_id"],
                code="TEST_ONLY_" + uuid4().hex,
                version="TEST_ONLY_v1",
                remit="TEST_ONLY finite algebra, no clinical content",
                environment="TEST_ONLY",
                evidence=evidence("TEST_ONLY synthesis provider"),
                expected_generation=0,
                predecessor_id=None,
                idempotency_key=uuid4().hex,
            ),
        )
        db.commit()
    for who, capability in (
        ("reviewer", "SYNTHESIS_RULE_REVIEW"),
        ("publisher", "SYNTHESIS_RULE_PUBLISH"),
        ("publisher", "SYNTHESIS_RULE_WITHDRAW"),
        ("self", "SYNTHESIS_SOURCE_READ"),
        ("reader", "SYNTHESIS_SOURCE_READ"),
    ):
        grant_rule(s, who, capability)
    s["rule"] = rule(s["root"], s["rule_provider_id"], s["rule_family_id"])
    return s


def publish(s):
    b = s["rule"]
    draft = append(s, "reviewer", command(s, dict(kind="DRAFT", rule=b)))
    review = append(
        s,
        "reviewer",
        command(
            s,
            dict(
                kind="REVIEW",
                revision_id=b.revision_id,
                body_fingerprint=digest("rule", b),
                evidence_fingerprint=digest("evidence-manifest", b.evidence),
                decision="APPROVE",
                prior_review_id=None,
            ),
        ),
    )
    publication = append(
        s,
        "publisher",
        command(
            s,
            dict(
                kind="PUBLICATION",
                revision_id=b.revision_id,
                body_fingerprint=digest("rule", b),
                action="PUBLISH",
                review_id=review.id,
                predecessor_publication_id=None,
                effective_at=b.effective.start,
            ),
        ),
    )
    s.update(rule_draft=draft, rule_review=review, rule_publication=publication)
    return publication


def capture_rules(s, *, who="self", **changes):
    b = s["rule"]
    request = c.NutritionSynthesisRequest(
        root=s["root"],
        selection=dict(
            provider_id=b.provider_id,
            family_id=b.family_id,
            revision_id=b.revision_id,
            publication_id=s["rule_publication"].id,
            body_fingerprint=digest("rule", b),
            evidence_fingerprint=digest("evidence-manifest", b.evidence),
            selection_version="EXACT_SINGLE_CASE_V1",
            language_version="FINITE_EXACT_V1",
        ),
        precision=dict(
            value="STANDARD",
            source="REQUEST_EXPLICIT",
            version="TEST_ONLY_v1",
            actor_user_id=s["user_id"],
            subject=s["root"].sources.request.subject,
            evidence=evidence("TEST_ONLY explicit planning precision"),
        ),
        purpose="BOUNDED_COMPLETE_POLICY_V1",
        required_claims=(),
    )
    request = c.NutritionSynthesisRequest.model_validate(canonical(request) | changes)
    with reader(s, who) as db:
        return capture_nutrition_synthesis_sources(db, request)
