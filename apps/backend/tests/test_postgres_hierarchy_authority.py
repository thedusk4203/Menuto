"""Database privilege, provider grants and source authority isolation."""

import json
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.modules.preferences.hierarchy_sources import (
    change_hierarchy_authority,
    publish_hierarchy_source,
)
from hierarchy_postgres_fixtures import capture, publication, publish
from hierarchy_postgres_fixtures import hierarchy_server as hierarchy_server
from hierarchy_postgres_fixtures import hierarchy_source as hierarchy_source
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize(
    "table",
    ["providers", "principals", "authority", "frontiers", "streams", "revisions", "mutations"],
)
@pytest.mark.parametrize("verb", ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"])
def test_a03_no_direct_source_table_bypass(hierarchy_source, table, verb):
    s = hierarchy_source
    name = "hierarchy_source_" + table
    query = {
        "SELECT": f"SELECT * FROM {name}",
        "INSERT": f"INSERT INTO {name} DEFAULT VALUES",
        "UPDATE": f"UPDATE {name} SET "
        + ("id=id" if table not in {"frontiers", "mutations"} else "provider_id=provider_id"),
        "DELETE": f"DELETE FROM {name}",
        "TRUNCATE": f"TRUNCATE {name}",
    }[verb]
    with (
        Session(s["engines"]["curator"]) as session,
        pytest.raises(DBAPIError, match="permission denied"),
    ):
        session.execute(text(query))


@pytest.mark.parametrize(
    "statement",
    [
        "SET ROLE menuto_hierarchy_owner",
        "SET ROLE menuto_hierarchy_admin",
        "SET ROLE menuto_hierarchy_catalog_owner",
        "SET ROLE menuto_hierarchy_recipes_owner",
        "SELECT menuto_hierarchy.session_fact(true)",
        "SELECT menuto_hierarchy.command_schema()",
        "SELECT menuto_hierarchy.register_provider('{}'::jsonb)",
        "SELECT menuto_hierarchy.catalog_read('[]'::jsonb)",
        "CREATE FUNCTION menuto_hierarchy.shadow() RETURNS int LANGUAGE sql AS 'SELECT 1'",
        "TRUNCATE ingredient_protein_reviews",
        "TRUNCATE culinary_feature_reviews",
    ],
)
def test_a03_function_role_search_path_and_classification_escalation_denied(
    hierarchy_source, statement
):
    with Session(hierarchy_source["engines"]["curator"]) as session, pytest.raises(DBAPIError):
        session.execute(text(statement))


def test_a02_no_provider_or_principal_fallback(hierarchy_source):
    s = hierarchy_source
    command = publication(s)
    with pytest.raises(DBAPIError, match="capability denied"):
        publish(s, command, who="other")
    with pytest.raises(DBAPIError, match="capability denied"):
        publish(s, command, who="reader")
    assert capture(s).frontier.source_generation == 0


def test_a04_revoke_precedes_idempotent_receipt_and_old_replay_stays_stable(hierarchy_source):
    s = hierarchy_source
    command = publication(s)
    receipt = publish(s, command)
    old_cut = capture(s)
    with Session(s["engines"]["admin"]) as session:
        change_hierarchy_authority(
            session,
            dict(
                provider_id=s["provider"].id,
                principal_id=s["principals"]["curator"].id,
                capability="REVIEW_PUBLISH",
                action="REVOKE",
                expected_authority_generation=4,
                reason="Explicit revoke",
                idempotency_key=uuid4().hex,
            ),
        )
        session.commit()
    with pytest.raises(DBAPIError, match="capability denied"):
        publish(s, command)
    new_cut = capture(s)
    assert old_cut.publications == new_cut.publications == (receipt.publication,)
    assert old_cut.fingerprint() != new_cut.fingerprint()


@pytest.mark.parametrize(
    "field,value",
    [
        ("actor_user_id", str(uuid4())),
        ("reviewer_user_id", str(uuid4())),
        ("support_present", True),
        ("status", "REVIEWED"),
    ],
)
def test_a02_raw_sql_claimed_authority_fields_rejected(hierarchy_source, field, value):
    s = hierarchy_source
    command = canonical(publication(s)) | {field: value}
    with Session(
        s["engines"]["curator"].execution_options(isolation_level="SERIALIZABLE")
    ) as session:
        with pytest.raises(DBAPIError):
            session.scalar(
                text("SELECT menuto_hierarchy.publish(CAST(:c AS jsonb))"),
                {"c": json.dumps(command)},
            )


def test_a02_guc_and_temp_shadow_cannot_mint_or_change_actor(hierarchy_source):
    s = hierarchy_source
    with Session(
        s["engines"]["other"].execution_options(isolation_level="SERIALIZABLE")
    ) as session:
        session.execute(
            text("SELECT set_config('menuto.actor_user_id',:id,true)"),
            {"id": str(s["principals"]["curator"].id)},
        )
        session.execute(text("CREATE TEMP TABLE hierarchy_source_authority (action text)"))
        with pytest.raises(DBAPIError, match="capability denied"):
            publish_hierarchy_source(session, publication(s))


def test_a02_prior_credentials_and_grants_not_hierarchy_authority(hierarchy_source):
    s = hierarchy_source
    login = s["names"]["other"]
    with s["engines"]["root"].begin() as root:
        root.execute(text(f'GRANT menuto_prior_client TO "{login}"'))
    try:
        with pytest.raises(DBAPIError, match="Unsafe source login"):
            publish(s, publication(s), who="other")
    finally:
        with s["engines"]["root"].begin() as root:
            root.execute(text(f'REVOKE menuto_prior_client FROM "{login}"'))


@pytest.mark.parametrize("role", ["OWNER", "EDITOR"])
def test_a02_real_household_roles_and_self_authorship_do_not_authorize_source(
    hierarchy_source, role
):
    from app.modules.households.models import Membership
    from sqlalchemy import select
    from test_postgres_foundation import seed_household

    s = hierarchy_source
    with Session(s["engines"]["root"]) as session:
        user, household = seed_household(session)
        session.scalar(select(Membership).where(Membership.user_id == user.id)).role = role
        actor_id = user.id
        session.commit()
    with Session(
        s["engines"]["other"].execution_options(isolation_level="SERIALIZABLE")
    ) as session:
        session.execute(
            text("SELECT set_config('menuto.actor_user_id',:id,true)"), {"id": str(actor_id)}
        )
        with pytest.raises(DBAPIError, match="capability denied"):
            publish_hierarchy_source(session, publication(s))


@pytest.mark.parametrize(
    "group",
    [
        "menuto_hierarchy_owner",
        "menuto_hierarchy_catalog_owner",
        "menuto_hierarchy_recipes_owner",
        "menuto_hierarchy_admin",
    ],
)
def test_a03_current_unsafe_membership_denied_after_enrollment(hierarchy_source, group):
    s = hierarchy_source
    login = s["names"]["curator"]
    with s["engines"]["root"].begin() as root:
        root.execute(text(f'GRANT {group} TO "{login}"'))
    try:
        with pytest.raises(DBAPIError, match="Unsafe source login"):
            publish(s, publication(s))
    finally:
        with s["engines"]["root"].begin() as root:
            root.execute(text(f'REVOKE {group} FROM "{login}"'))


def test_a04_renamed_login_does_not_inherit_old_binding(hierarchy_source):
    from app.modules.preferences.hierarchy_sources import capture_hierarchy_sources

    s = hierarchy_source
    old = s["names"]["reader"]
    renamed = old + "_r"
    live = Session(
        s["engines"]["reader"].execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        )
    )
    assert live.scalar(text("SELECT system_user")) == "scram-sha-256:" + old
    with s["engines"]["root"].begin() as root:
        root.execute(text(f'ALTER ROLE "{old}" RENAME TO "{renamed}"'))
    try:
        with pytest.raises(DBAPIError, match="SCRAM|enrolled"):
            capture_hierarchy_sources(
                live,
                dict(
                    provider_id=s["provider"].id,
                    policy_id=s["policy"].policy_id,
                    requested_targets=[],
                ),
            )
        live.rollback()
        with Session(s["engines"]["admin"]) as admin:
            from app.modules.preferences.hierarchy_sources import enroll_hierarchy_principal

            enrolled = enroll_hierarchy_principal(
                admin, dict(role_name=renamed, idempotency_key=uuid4().hex)
            )
            admin.commit()
        assert enrolled.role_oid == s["principals"]["reader"].role_oid
        assert enrolled.id != s["principals"]["reader"].id
    finally:
        live.close()
        with s["engines"]["root"].begin() as root:
            root.execute(text(f'ALTER ROLE "{renamed}" RENAME TO "{old}"'))


def test_a01_actual_scram_database_owner_denied(hierarchy_source):
    from app.modules.preferences.hierarchy_sources import capture_hierarchy_sources
    from psycopg import sql

    s = hierarchy_source
    with s["engines"]["root"].connect().execution_options(isolation_level="AUTOCOMMIT") as root:
        original = root.scalar(
            text("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()")
        )
        with root.connection.driver_connection.cursor() as cur:
            cur.execute(
                sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                    sql.Identifier(s["dbname"]), sql.Identifier(s["names"]["dbowner"])
                )
            )
        try:
            with Session(
                s["engines"]["dbowner"].execution_options(
                    isolation_level="REPEATABLE READ", postgresql_readonly=True
                )
            ) as session:
                with pytest.raises(DBAPIError, match="Unsafe source login"):
                    capture_hierarchy_sources(
                        session,
                        dict(
                            provider_id=s["provider"].id,
                            policy_id=s["policy"].policy_id,
                            requested_targets=[],
                        ),
                    )
        finally:
            with root.connection.driver_connection.cursor() as cur:
                cur.execute(
                    sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                        sql.Identifier(s["dbname"]), sql.Identifier(original)
                    )
                )


def test_a04_registry_idempotency_does_not_grant_other_provider_access(hierarchy_source):
    from app.modules.preferences.hierarchy_sources import (
        capture_hierarchy_sources,
        register_hierarchy_provider,
    )

    s = hierarchy_source
    command = dict(
        code="synthetic." + uuid4().hex,
        version="1",
        source_system="hierarchy.test",
        remit="Reviewed registry",
        idempotency_key=uuid4().hex,
    )
    with Session(s["engines"]["admin"]) as admin:
        provider = register_hierarchy_provider(admin, command)
        admin.commit()
        assert register_hierarchy_provider(admin, command) == provider
        admin.commit()
        with pytest.raises(DBAPIError, match="Idempotency conflict"):
            register_hierarchy_provider(admin, command | dict(remit="Changed registry command"))
        admin.rollback()
    with Session(
        s["engines"]["reader"].execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        )
    ) as reader:
        with pytest.raises(DBAPIError, match="capability denied"):
            capture_hierarchy_sources(
                reader,
                dict(
                    provider_id=provider.id, policy_id=s["policy"].policy_id, requested_targets=[]
                ),
            )


def test_a04_grant_retry_is_history_not_regrant_and_fresh_noop_rejected(hierarchy_source):
    s = hierarchy_source
    cmd = dict(
        provider_id=s["provider"].id,
        principal_id=s["principals"]["other"].id,
        capability="CAPTURE",
        action="GRANT",
        expected_authority_generation=4,
        reason="Explicit grant",
        idempotency_key=uuid4().hex,
    )
    with Session(s["engines"]["admin"]) as admin:
        grant = change_hierarchy_authority(admin, cmd)
        admin.commit()
        assert change_hierarchy_authority(admin, cmd) == grant
        admin.commit()
        with pytest.raises(DBAPIError, match="no-op"):
            change_hierarchy_authority(
                admin, cmd | dict(expected_authority_generation=5, idempotency_key=uuid4().hex)
            )
        admin.rollback()
        change_hierarchy_authority(
            admin,
            cmd
            | dict(action="REVOKE", expected_authority_generation=5, idempotency_key=uuid4().hex),
        )
        admin.commit()
        assert change_hierarchy_authority(admin, cmd) == grant
        admin.commit()
    with pytest.raises(DBAPIError, match="capability denied"):
        capture(s, who="other")
    assert capture(s).frontier.authority_generation == 6
