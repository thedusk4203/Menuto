"""Real PostgreSQL identities, protected paths and isolated TEST_ONLY source fixtures."""

import os
import secrets
import time
from contextlib import contextmanager
from ipaddress import ip_address
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as c
from app.modules.nutrition.root_admin import (
    change_nutrition_authority,
    enroll_nutrition_principal,
    register_nutrition_provider,
)
from app.modules.nutrition.root_models import NUTRITION_ROOT_TABLES
from app.modules.nutrition.root_sources import (
    append_nutrition_source,
    capture_nutrition_root_sources,
)
from app.persistence.database import create_database_engine
from nutrition_root_fixtures import (
    amount,
    authority_interval,
    evidence,
    guideline,
    interval,
    member_identity,
    reference_identity,
    root_request,
)
from psycopg import sql
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from test_postgres_foundation import seed_household

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def nrc_server():
    url = os.environ.get("MENUTO_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set MENUTO_TEST_POSTGRES_URL for actual Nutrition protected-path tests")
    parsed = make_url(url)
    assert parsed.host in {"localhost", "127.0.0.1", "::1"} and parsed.database == "postgres"
    maintenance = create_database_engine(url).execution_options(isolation_level="AUTOCOMMIT")
    dbname = "nrc_test_" + uuid4().hex
    engines = {}
    names = {}
    passwords = {}
    original_hba = hba_path = None
    created = False
    fixture_roles = []

    def write_hba(db, body):
        oid = db.scalar(text("SELECT lo_from_bytea(0,convert_to(:body,'UTF8'))"), {"body": body})
        try:
            db.execute(
                text("SELECT lo_export(CAST(:oid AS oid),:path)"), {"oid": oid, "path": hba_path}
            )
        finally:
            db.execute(text("SELECT lo_unlink(CAST(:oid AS oid))"), {"oid": oid})
        db.execute(text("SELECT pg_reload_conf()"))
        time.sleep(0.15)

    def create_role(key, group="menuto_nutrition_client", authentication="scram-sha-256"):
        nonlocal original_hba
        name = "nrc_" + key + "_" + uuid4().hex[:12]
        password = secrets.token_urlsafe(32)
        with maintenance.connect() as db:
            with db.connection.driver_connection.cursor() as cur:
                cur.execute("SET password_encryption='scram-sha-256'")
                cur.execute(
                    sql.SQL("CREATE ROLE {} LOGIN INHERIT PASSWORD {}").format(
                        sql.Identifier(name), sql.Literal(password)
                    )
                )
                cur.execute(
                    sql.SQL("GRANT {} TO {}").format(sql.Identifier(group), sql.Identifier(name))
                )
            actual = db.scalar(text("SELECT host(inet_client_addr())"))
            addresses = {"127.0.0.1/32", "::1/128"}
            if actual:
                addresses.add(actual + ("/32" if ip_address(actual).version == 4 else "/128"))
            current = db.scalar(text("SELECT pg_read_file(:path)"), {"path": hba_path})
            rules = "\n".join(
                f"host {dbname} {name} {addr} {authentication}" for addr in sorted(addresses)
            )
            write_hba(db, rules + "\n" + current)
            assert not db.scalar(
                text("SELECT count(*) FROM pg_hba_file_rules WHERE error IS NOT NULL")
            )
        names[key] = name
        passwords[key] = password
        fixture_roles.append(name)
        engines[key] = create_database_engine(
            parsed.set(database=dbname, username=name, password=password).render_as_string(
                hide_password=False
            )
        )
        return engines[key]

    try:
        with maintenance.connect() as db:
            db.execute(text(f'CREATE DATABASE "{dbname}"'))
            created = True
            hba_path = db.scalar(text("SHOW hba_file"))
            original_hba = db.scalar(text("SELECT pg_read_file(:path)"), {"path": hba_path})
        engines["root"] = create_database_engine(
            parsed.set(database=dbname).render_as_string(hide_password=False)
        )
        config = Config(str(ROOT / "alembic.ini"))
        with engines["root"].connect() as db:
            config.attributes["connection"] = db
            command.upgrade(config, "head")
            assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0016"
            assert len(set(inspect(db).get_table_names()) - {"alembic_version"}) == 98
            empty = {
                t.name: db.scalar(text('SELECT count(*) FROM "' + t.name + '"'))
                for t in NUTRITION_ROOT_TABLES
            }
            assert not any(empty.values())
            command.check(config)
            db.commit()
            command.downgrade(config, "0015")
            db.commit()
            command.upgrade(config, "head")
            db.commit()
        create_role("admin", "menuto_nutrition_admin")
        for key in ("reviewer", "publisher", "assessor", "reader", "validator", "other", "alias"):
            create_role(key)
        create_role("trust", authentication="trust")
        human = uuid4()
        principals = {}
        with Session(engines["admin"]) as db:
            for key in (
                "reviewer",
                "publisher",
                "assessor",
                "reader",
                "validator",
                "other",
                "alias",
                "trust",
            ):
                service = key in {"reader", "validator", "other", "trust"}
                principals[key] = enroll_nutrition_principal(
                    db,
                    dict(
                        role_name=names[key],
                        verified_human_id=None
                        if service
                        else human
                        if key in {"reviewer", "alias"}
                        else uuid4(),
                        user_id=None,
                        service_id="TEST_ONLY_" + key if service else None,
                        delegation_registrar=False,
                        identity_evidence=evidence("TEST_ONLY enrollment " + key),
                        idempotency_key=uuid4().hex,
                    ),
                )
            db.commit()
        yield dict(
            engines=engines,
            names=names,
            passwords=passwords,
            principals=principals,
            parsed=parsed,
            dbname=dbname,
            config=config,
            empty_install=empty,
            create_role=create_role,
            maintenance=maintenance,
            write_hba=write_hba,
            hba_path=hba_path,
        )
    finally:
        for engine in engines.values():
            engine.dispose()
        with maintenance.connect() as db:
            if original_hba is not None:
                write_hba(db, original_hba)
                assert (
                    db.scalar(text("SELECT pg_read_file(:path)"), {"path": hba_path})
                    == original_hba
                )
            if created:
                db.execute(text(f'DROP DATABASE "{dbname}" WITH (FORCE)'))
            with db.connection.driver_connection.cursor() as cur:
                for name in fixture_roles:
                    cur.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(name)))
        maintenance.dispose()


def grant(s, who, capability, *, scope=None, protocol=None, fact=None, action="GRANT", key=None):
    if scope is None:
        reference = capability.startswith("GUIDELINE_")
        member = capability.startswith("MEMBER_")
        scope = dict(
            provider_id=None if member else s["provider_id"],
            family_id=None if member else s["family_id"],
            household_id=None if reference else s["household_id"],
            member_id=None if reference else s["member_id"],
        )
    group = dict(scope)
    if group["member_id"] is not None:
        group.update(provider_id=None, family_id=None)
    stream_key = c.nutrition_root_hash("nutrition.authority-stream.v1", group)
    with s["engines"]["root"].connect() as root:
        row = root.execute(
            text("SELECT revision,head_id FROM nutrition_source_streams WHERE stream_key=:key"),
            {"key": stream_key},
        ).first()
    with Session(s["engines"]["admin"]) as db:
        result = change_nutrition_authority(
            db,
            dict(
                principal_id=s["principals"][who].id,
                scope=scope,
                capability=capability,
                protocol_fingerprint=protocol,
                fact_key=fact,
                action=action,
                effective=authority_interval(),
                qualification_evidence=evidence("TEST_ONLY exact scope grant " + capability),
                expected_generation=row[0] if row else 0,
                predecessor_id=row[1] if row else None,
                idempotency_key=key or uuid4().hex,
            ),
        )
        db.commit()
        return result


def source_command(s, identity, body, *, revision_id=None, key=None):
    stream_key = c.nutrition_root_hash("nutrition.source-stream.v1", identity)
    with s["engines"]["root"].connect() as root:
        row = root.execute(
            text("SELECT revision,head_id FROM nutrition_source_streams WHERE stream_key=:key"),
            {"key": stream_key},
        ).first()
    return c.NutritionSourceCommand(
        revision_id=revision_id or uuid4(),
        identity=identity,
        body=body,
        expected_revision=row[0] if row else 0,
        predecessor_id=row[1] if row else None,
        idempotency_key=key or uuid4().hex,
    )


def append(s, who, command_):
    with Session(s["engines"][who]) as db:
        result = append_nutrition_source(db, command_)
        db.commit()
        return result


@contextmanager
def reader(s, who="reader", *, isolation="REPEATABLE READ", readonly=True):
    with Session(
        s["engines"][who].execution_options(isolation_level=isolation, postgresql_readonly=readonly)
    ) as db:
        yield db


def capture(s, *, who="reader", request=None):
    with reader(s, who) as db:
        return capture_nutrition_root_sources(
            db, request or root_request(s, purpose="VALIDATOR" if who == "validator" else "ROOT")
        )


def prepare_nrc(server, *, complete=True, root_kind="RANGE", guideline_effective=None):
    s = dict(server, principals=dict(server["principals"]))
    with Session(s["engines"]["root"]) as db:
        user, subject = seed_household(db)
        representative, rep_subject = seed_household(db)
        # Representative is explicitly a household editor but not the subject.
        from app.modules.households.models import Membership

        db.add(
            Membership(
                household_id=subject.household_id,
                user_id=representative.id,
                member_id=None,
                role="EDITOR",
            )
        )
        db.commit()
        s.update(
            household_id=subject.household_id,
            member_id=subject.member_id,
            user_id=user.id,
            representative_user_id=representative.id,
        )
    token = uuid4().hex[:10]
    for key, user_id in (
        ("self_" + token, s["user_id"]),
        ("rep_" + token, s["representative_user_id"]),
    ):
        server["create_role"](key)
        with Session(s["engines"]["admin"]) as db:
            p = enroll_nutrition_principal(
                db,
                dict(
                    role_name=server["names"][key],
                    verified_human_id=uuid4(),
                    user_id=user_id,
                    service_id=None,
                    delegation_registrar=False,
                    identity_evidence=evidence("TEST_ONLY canonical member actor"),
                    idempotency_key=uuid4().hex,
                ),
            )
            db.commit()
        label = "self" if key.startswith("self_") else "representative"
        s["principals"][label] = p
        # Each fixture retains its own engine; global cleanup still disposes the concrete one.
        s["engines"] = dict(s["engines"], **{label: server["engines"][key]})
        s["names"] = dict(s["names"], **{label: server["names"][key]})
    s.update(provider_id=uuid4(), family_id="TEST_ONLY_family_" + uuid4().hex[:12])
    with Session(s["engines"]["admin"]) as db:
        s["provider"] = register_nutrition_provider(
            db,
            dict(
                provider_id=s["provider_id"],
                code="TEST_ONLY_" + uuid4().hex,
                version="TEST_ONLY_v1",
                remit="TEST_ONLY structural source",
                environment="TEST_ONLY",
                authority_evidence=evidence("TEST_ONLY provider enrollment"),
                expected_generation=0,
                previous_enrollment_id=None,
                idempotency_key=uuid4().hex,
            ),
        )
        db.commit()
    grant(s, "reviewer", "GUIDELINE_REVIEW")
    grant(s, "publisher", "GUIDELINE_PUBLISH")
    grant(s, "publisher", "GUIDELINE_WITHDRAW")
    grant(s, "reader", "ROOT_SOURCE_READ")
    grant(s, "validator", "VALIDATOR_SOURCE_READ")
    for who in ("self", "representative"):
        grant(s, who, "MEMBER_GOAL_WRITE")
        for fact in ("BODY_MASS", "HEIGHT"):
            grant(s, who, "MEMBER_OBSERVATION_WRITE", fact=fact)
    body = guideline(s["provider_id"], s["family_id"], root_kind=root_kind)
    if guideline_effective is not None:
        body = c.NutritionGuidelineBody.model_validate(
            dict(canonical(body), effective=canonical(guideline_effective))
        )
    s["guideline"] = body
    identity = reference_identity(s["provider_id"], s["family_id"])
    s["draft"] = append(
        s,
        "reviewer",
        source_command(
            s, identity, dict(kind="DRAFT", guideline=body), revision_id=body.revision_id
        ),
    )
    s["review"] = append(
        s,
        "reviewer",
        source_command(
            s,
            identity,
            dict(
                kind="REVIEW",
                draft_revision_id=body.revision_id,
                body_fingerprint=c.nutrition_root_hash("nutrition.guideline-body.v1", body),
                evidence_fingerprint=c.nutrition_root_hash(
                    "nutrition.evidence-manifest.v1", body.evidence_manifest
                ),
                protocol_fingerprint=c.nutrition_root_hash("nutrition.protocol.v1", body.protocol),
                decision="APPROVE",
                prior_review_id=None,
                rationale="TEST_ONLY reviewed synthetic structure",
            ),
        ),
    )
    s["publication"] = append(
        s,
        "publisher",
        source_command(
            s,
            identity,
            dict(
                kind="PUBLICATION",
                action="PUBLISH",
                draft_revision_id=body.revision_id,
                body_fingerprint=c.nutrition_root_hash("nutrition.guideline-body.v1", body),
                review_event_id=s["review"].id,
                prior_publication_id=None,
                effective_at=body.effective.start,
                rationale="TEST_ONLY publication; NO PRODUCTION NUTRITION CONTENT",
            ),
        ),
    )
    grant(
        s,
        "assessor",
        "ELIGIBILITY_ATTEST",
        protocol=c.nutrition_root_hash("nutrition.protocol.v1", body.protocol),
    )
    s["observations"] = {}
    if complete:
        for fact, unit, value in (("BODY_MASS", "KG", amount(7, 2)), ("HEIGHT", "CM", amount(19))):
            obs = append(
                s,
                "self",
                source_command(
                    s,
                    member_identity(s, "OBSERVATION", fact),
                    dict(
                        kind="OBSERVATION",
                        operation="CREATE",
                        fact_key=fact,
                        value=value,
                        unit=unit,
                        observed_at="2026-08-01T00:00:00Z",
                        provenance=evidence("TEST_ONLY physiological observation " + fact),
                        effective=interval(),
                        replaces=(),
                    ),
                ),
            )
            s["observations"][fact] = obs
        goal_id = uuid4()
        s["goal"] = append(
            s,
            "self",
            source_command(
                s,
                member_identity(s, "GOAL", "ENERGY_DIRECTION"),
                dict(
                    kind="GOAL",
                    operation="CREATE",
                    goal_id=goal_id,
                    goal_type="ENERGY_DIRECTION",
                    direction="MAINTAIN",
                    effective=interval(),
                    replaces=(),
                    provenance=evidence("TEST_ONLY member intent"),
                ),
                revision_id=goal_id,
            ),
        )
        s["assessment"] = append(s, "assessor", assessment_command(s))
    return s


def delegation_command(
    s, *, operation_scope="MEMBER_GOAL_WRITE", action="GRANT", previous=None, span=None
):
    grantee = s["principals"]["representative"].id
    identity = member_identity(s, "DELEGATION", operation_scope + ":" + str(grantee))
    return source_command(
        s,
        identity,
        dict(
            kind="DELEGATION",
            action=action,
            grantee_principal_id=grantee,
            operation_scope=operation_scope,
            effective=span or authority_interval(),
            authorization_evidence=evidence(
                "TEST_ONLY explicit subject/actor/operation authorization"
            ),
            previous_grant_id=previous,
        ),
    )


def revised_member_command(s, old, *, operation="CORRECT", span=None, **changes):
    body = canonical(old.command.body)
    body.update(operation=operation, replaces=(old.id,), **changes)
    if span is not None:
        body["effective"] = span
    if "provenance" in body:
        body["provenance"] = evidence("TEST_ONLY explicit source revision " + operation)
    return source_command(s, old.command.identity, body)


def publish_revision(s, body, *, prior=None):
    i = reference_identity(s["provider_id"], s["family_id"])
    draft = append(
        s,
        "reviewer",
        source_command(s, i, dict(kind="DRAFT", guideline=body), revision_id=body.revision_id),
    )
    review = append(
        s,
        "reviewer",
        source_command(
            s,
            i,
            dict(
                kind="REVIEW",
                draft_revision_id=body.revision_id,
                body_fingerprint=c.nutrition_root_hash("nutrition.guideline-body.v1", body),
                evidence_fingerprint=c.nutrition_root_hash(
                    "nutrition.evidence-manifest.v1", body.evidence_manifest
                ),
                protocol_fingerprint=c.nutrition_root_hash("nutrition.protocol.v1", body.protocol),
                decision="APPROVE",
                prior_review_id=None,
                rationale="TEST_ONLY fresh reviewed revision",
            ),
        ),
    )
    publication = append(
        s,
        "publisher",
        source_command(
            s,
            i,
            dict(
                kind="PUBLICATION",
                action="PUBLISH" if prior is None else "SUPERSEDE",
                draft_revision_id=body.revision_id,
                body_fingerprint=c.nutrition_root_hash("nutrition.guideline-body.v1", body),
                review_event_id=review.id,
                prior_publication_id=prior,
                effective_at=body.effective.start,
                rationale="TEST_ONLY structural publication",
            ),
        ),
    )
    return draft, review, publication


def assessment_command(
    s,
    *,
    outcome="ADMITTED",
    operation="CREATE",
    replaces=(),
    span=None,
    observations=None,
    slots=None,
):
    body = s["guideline"]
    protocol = body.protocol
    requirements = (protocol.admitted, protocol.excluded, protocol.out_of_scope)
    all_facts = {f for req in requirements for f in req.observations}
    all_slots = {f for req in requirements for f in req.evidence_slots}
    obs = s["observations"] if observations is None else observations
    refs = [
        dict(
            fact_key=fact,
            revision_id=r.id,
            fact_hash=r.fact_hash,
            value=r.command.body.value,
            unit=r.command.body.unit,
            legacy_anchor_fingerprint=r.legacy_anchor.body_fingerprint,
        )
        for fact, r in sorted(obs.items())
    ]
    slots = all_slots if slots is None else set(slots)
    return source_command(
        s,
        member_identity(s, "ASSESSMENT", c.nutrition_root_hash("nutrition.protocol.v1", protocol)),
        dict(
            kind="ASSESSMENT",
            operation=operation,
            guideline_revision_id=body.revision_id,
            guideline_body_fingerprint=c.nutrition_root_hash("nutrition.guideline-body.v1", body),
            protocol_fingerprint=c.nutrition_root_hash("nutrition.protocol.v1", protocol),
            outcome=outcome,
            observations=refs,
            evidence=tuple(
                evidence("TEST_ONLY assessment proof " + slot, evidence_id=slot)
                for slot in sorted(slots)
            ),
            missing_observations=tuple(sorted(all_facts - set(obs))),
            missing_evidence_slots=tuple(sorted(all_slots - slots)),
            effective=span or interval(),
            replaces=replaces,
        ),
    )
