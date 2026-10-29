"""Dedicated SCRAM root/household/owner identity adversaries, never impersonated sessions."""

import json

import pytest
from app.domain.feature_identity import canonical
from app.modules.households.models import Membership
from app.modules.preferences.reference_priors import (
    capture_reference_prior_sources,
    enroll_reference_prior_principal,
    publish_reference_prior,
    register_reference_prior_provider,
)
from psycopg import sql
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_postgres_foundation import seed_household
from test_postgres_recipes import seed
from test_postgres_reference_priors import publication, reader
from test_postgres_reference_priors import source as source
from test_postgres_reference_priors import source_server as source_server

pytestmark = [pytest.mark.postgres, pytest.mark.reference_prior_auth]


def test_a04_scram_superuser_and_database_owner_denied_even_with_execute(source):
    s = source
    with (
        Session(s["engines"]["super"]) as session,
        pytest.raises(DBAPIError, match="Unsafe source login"),
    ):
        publish_reference_prior(session, publication(s))
    with s["engines"]["root"].connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        original = conn.scalar(
            text("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()")
        )
        with conn.connection.driver_connection.cursor() as cur:
            cur.execute(
                sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                    sql.Identifier(s["dbname"]), sql.Identifier(s["names"]["dbowner"])
                )
            )
        try:
            with (
                Session(s["engines"]["dbowner"]) as session,
                pytest.raises(DBAPIError, match="Unsafe source login"),
            ):
                publish_reference_prior(session, publication(s))
        finally:
            with conn.connection.driver_connection.cursor() as cur:
                cur.execute(
                    sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                        sql.Identifier(s["dbname"]), sql.Identifier(original)
                    )
                )


@pytest.mark.parametrize("role", ["OWNER", "EDITOR"])
def test_a01_real_household_membership_cannot_mint_reference_authority(source, role):
    s = source
    with Session(s["engines"]["root"]) as session:
        user, result = seed_household(session)
        membership = session.scalar(select(Membership).where(Membership.user_id == user.id))
        membership.role = role
        session.commit()
        c = canonical(publication(s))
        c.update(
            actor_user_id=str(user.id), household_id=str(result.household_id), authorship="SELF"
        )
    with Session(s["engines"]["other"]) as session, pytest.raises(DBAPIError):
        session.scalar(text("SELECT menuto_prior.publish(CAST(:c AS jsonb))"), {"c": json.dumps(c)})
    with (
        Session(s["engines"]["other"]) as session,
        pytest.raises(DBAPIError, match="capability denied"),
    ):
        publish_reference_prior(session, publication(s))


def test_t01_recipe_version_id_cannot_stand_in_for_stable_recipe(source):
    s = source
    with Session(s["engines"]["root"]) as session:
        version, _ = seed(session)
        session.commit()
    with reader(s) as session, pytest.raises(DBAPIError, match="TARGET_IDENTITY_UNRESOLVED"):
        capture_reference_prior_sources(
            session,
            dict(
                provider_id=s["provider"].id,
                requested_targets=[dict(kind="DIRECT_RECIPE", recipe_id=version.id)],
            ),
        )


def test_a08_provider_and_enrollment_idempotency(source):
    s = source
    with Session(s["engines"]["admin"]) as session:
        assert register_reference_prior_provider(session, s["provider"].command) == s["provider"]
        assert (
            enroll_reference_prior_principal(session, s["principals"]["curator"].command)
            == s["principals"]["curator"]
        )
        session.commit()
    c = canonical(s["provider"].command)
    c["version"] = "different-version"
    with Session(s["engines"]["admin"]) as session, pytest.raises(DBAPIError, match="Idempotency"):
        register_reference_prior_provider(session, c)


@pytest.mark.parametrize("unsafe", ["admin-client", "direct-write"])
def test_a04_unsafe_effective_privileges_fail_closed_on_scram_sessions(source, unsafe):
    s = source
    who = "admin" if unsafe == "admin-client" else "other"
    name = sql.Identifier(s["names"][who])
    grant = (
        sql.SQL("GRANT menuto_prior_client TO {}")
        if unsafe == "admin-client"
        else sql.SQL("GRANT UPDATE ON reference_prior_frontiers TO {}")
    )
    revoke = (
        sql.SQL("REVOKE menuto_prior_client FROM {}")
        if unsafe == "admin-client"
        else sql.SQL("REVOKE UPDATE ON reference_prior_frontiers FROM {}")
    )
    with s["engines"]["root"].connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        with conn.connection.driver_connection.cursor() as cur:
            cur.execute(grant.format(name))
        try:
            with (
                Session(s["engines"][who]) as session,
                pytest.raises(DBAPIError, match="Unsafe source login|direct mutation privileges"),
            ):
                publish_reference_prior(session, publication(s))
        finally:
            with conn.connection.driver_connection.cursor() as cur:
                cur.execute(revoke.format(name))
    with Session(s["engines"][who]) as session, pytest.raises(DBAPIError):
        session.scalar(text("SELECT menuto_prior.backend_tls()"))


def test_m01_populated_downgrade_refuses_registry_and_audit_loss(source_server):
    from alembic import command

    s = source_server
    with s["engines"]["root"].connect() as conn:
        config = s["config"]
        config.attributes["connection"] = conn
        assert conn.scalar(text("SELECT count(*) FROM reference_prior_revisions")) == 0
        before = conn.scalar(text("SELECT count(*) FROM reference_prior_principals"))
        assert before > 0
        conn.commit()
        with pytest.raises(DBAPIError, match="Refusing destructive"):
            command.downgrade(config, "0013")
        conn.rollback()
        assert conn.scalar(text("SELECT count(*) FROM reference_prior_principals")) == before
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0016"
