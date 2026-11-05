"""NRE real PostgreSQL obligations; isolated TEST_ONLY source state only."""

from datetime import timedelta
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.modules.catalog.models import Ingredient, NutritionFact
from app.modules.catalog.public import catalog_facts
from app.modules.households.models import Membership
from app.modules.households.public import read_household_actor
from app.modules.nutrition import resolution_contracts as c
from app.modules.nutrition.resolution_estimator import estimate_nutrition_resolution as estimate
from app.modules.nutrition.synthesis_sources import capture_nutrition_synthesis_sources
from app.modules.planning import nutrition_resolution_capture as capture_module
from app.modules.planning.nutrition_resolution_capture import capture_nutrition_resolution_sources
from app.modules.validation.nutrition_resolution import (
    check_nutrition_resolution_independently as check,
)
from nutrition_resolution_fixtures import rehash, row_count
from nutrition_resolution_postgres_fixtures import (  # noqa: F401
    capture_nre,
    configure_fixture,
    fingerprint_rows,
    nre_case,
)
from nutrition_root_postgres_fixtures import grant, nrc_server, reader  # noqa: F401
from nutrition_synthesis_postgres_fixtures import (
    capture_rules,
    grant_rule,
    publish,
    setup_synthesis,
)
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker
from test_postgres_foundation import postgres_engine as postgres_engine  # noqa: F401

pytestmark = pytest.mark.postgres


READ_RELATIONS = (
    "ingredients",
    "nutrition_facts",
    "households",
    "household_members",
    "memberships",
    "recipes",
    "recipe_versions",
    "recipe_ingredients",
    "recipe_portion_tiers",
    "recipe_tier_quantities",
    "recipe_variant_rules",
    "recipe_rule_combinations",
    "recipe_combination_members",
    "preparation_transformations",
    "recipe_version_seals",
)


def test_nre001_composed_ordinary_reader_preflight(nrc_server):  # noqa: F811
    s = setup_synthesis(nrc_server)
    publish(s)
    request = capture_rules(s).request
    with s["engines"]["root"].connect() as admin:
        for relation in READ_RELATIONS:
            admin.connection.driver_connection.execute(
                sql.SQL("GRANT SELECT ON public.{} TO {}").format(
                    sql.Identifier(relation), sql.Identifier(s["names"]["self"])
                )
            )
        admin.connection.driver_connection.commit()
    with reader(s, "self") as db:
        source = capture_nutrition_synthesis_sources(db, request)
        actor = read_household_actor(db, s["household_id"], s["user_id"])
        assert actor[1] == "OWNER"
        assert catalog_facts(db, ()) == ((), ())
        for relation in READ_RELATIONS:
            count = db.scalar(text('SELECT count(*) FROM public."' + relation + '"'))
            assert count >= 0
        assert source.frame.backend_pid == db.scalar(text("SELECT pg_backend_pid()"))
        assert source.frame.mvcc_snapshot == db.scalar(text("SELECT pg_current_snapshot()::text"))
        assert db.scalar(text("SHOW transaction_read_only")) == "on"


def test_nre001_full_canonical_capture_and_independent_check(nre_case):  # noqa: F811
    from app.modules.nutrition.resolution_estimator import estimate_nutrition_resolution
    from app.modules.validation.nutrition_resolution import check_nutrition_resolution_independently

    sources = capture_nre(nre_case)
    result = estimate_nutrition_resolution(sources)
    assert result.availability == "AVAILABLE", result.reasons
    assert len(result.configurations) == 6
    report = check_nutrition_resolution_independently(sources, result)
    assert report.decision == "CONSISTENT", report


def request_changed(s, change):
    data = canonical(s["nre_scope"])
    change(data)
    return c.NutritionResolutionScopeRequestV1.model_validate(data)


def add_reference(s, count=1, status="DRAFT", observed_at=None):
    """Privileged TEST_ONLY fixture bootstrap, never runtime source permission."""
    first = s["nre_references"][0]
    with Session(s["engines"]["root"]) as db:
        for _ in range(count):
            data = first.fact.provenance.model_dump()
            data["source_kind"] = data.pop("kind")
            data["source_uri"] = str(data["source_uri"]) if data["source_uri"] else None
            data["external_record_id"] = str(uuid4())
            if observed_at is not None:
                data["observed_at"] = observed_at
            db.add(
                NutritionFact(
                    id=uuid4(),
                    ingredient_id=first.fact.ingredient_id,
                    reference_amount=first.fact.reference.amount,
                    basis=first.fact.reference.basis.value,
                    **first.fact.nutrients.model_dump(),
                    status=status,
                    **data,
                )
            )
        db.commit()


def test_nre002_payload_actor_uuid_cannot_spoof_database_author(nre_case):  # noqa: F811
    def spoof(d):
        identity = str(uuid4())
        d["actor_user_id"] = d["precision"]["actor_user_id"] = identity
        for slot in d["slots"]:
            for declaration in slot["alternatives"]:
                declaration["actor_user_id"] = identity

    request = request_changed(nre_case, spoof)
    with pytest.raises((PermissionError, DBAPIError), match="binding|actor|author"):
        capture_nre(nre_case, scope_value=request)


@pytest.mark.parametrize("access", ["VIEWER", "NO_MEMBERSHIP", "FOREIGN_HOUSEHOLD"])
def test_nre003_viewer_and_foreign_household_no_planning_authorship(nre_case, access):  # noqa: F811
    s = nre_case
    if access == "FOREIGN_HOUSEHOLD":

        def foreign(d):
            subject = d["subject"] | {"household_id": str(uuid4()), "member_id": str(uuid4())}
            d["subject"] = d["root_request"]["subject"] = d["precision"]["subject"] = subject
            for slot in d["slots"]:
                for declaration in slot["alternatives"]:
                    declaration["subject"] = subject

        with pytest.raises((PermissionError, DBAPIError)):
            capture_nre(s, scope_value=request_changed(s, foreign))
        return
    with Session(s["engines"]["root"]) as db:
        db.execute(
            text(
                (
                    "UPDATE memberships SET role='VIEWER'"
                    if access == "VIEWER"
                    else "DELETE FROM memberships"
                )
                + " WHERE user_id=:u AND household_id=:h"
            ),
            dict(u=s["user_id"], h=s["household_id"]),
        )
        db.commit()
    with pytest.raises((PermissionError, DBAPIError)):
        capture_nre(s)


@pytest.mark.parametrize("domain", ["ROOT", "SYNTHESIS"])
def test_nre004_independent_reader_grants_required(nre_case, domain):  # noqa: F811
    s = nre_case
    if domain == "ROOT":
        grant(s, "self", "ROOT_SOURCE_READ", action="REVOKE")
    else:
        grant_rule(s, "self", "SYNTHESIS_SOURCE_READ", action="REVOKE")
    with pytest.raises((PermissionError, DBAPIError)):
        capture_nre(s)


@pytest.mark.parametrize("identity", ["superuser", "set_role", "source_owner"])
def test_nre005_unsafe_actual_postgres_identity_rejected(nre_case, identity):  # noqa: F811
    s = nre_case
    if identity == "superuser":
        with pytest.raises((PermissionError, DBAPIError)):
            capture_nre(s, who="root")
        return
    if identity == "source_owner":
        with s["engines"]["root"].begin() as admin:
            admin.connection.driver_connection.execute(
                sql.SQL("GRANT menuto_nutrition_owner TO {}").format(
                    sql.Identifier(s["names"]["self"])
                )
            )
    with reader(s, "self") as db:
        if identity == "set_role":
            db.execute(text("SET ROLE menuto_nutrition_client"))
        with pytest.raises((PermissionError, DBAPIError)):
            capture_nutrition_resolution_sources(db, s["nre_context"], s["nre_scope"])


@pytest.mark.parametrize(
    "isolation,readonly", [("READ COMMITTED", True), ("REPEATABLE READ", False)]
)
def test_nre006_actual_transaction_mode_must_be_read_only_repeatable(nre_case, isolation, readonly):  # noqa: F811
    with pytest.raises(ValueError, match="SOURCE_CUT_UNSUPPORTED"):
        capture_nre(nre_case, isolation=isolation, readonly=readonly)


@pytest.mark.parametrize("pending", ["new", "dirty", "deleted", "cached"])
def test_nre007_dirty_session_never_flushed(nre_case, pending):  # noqa: F811
    s = nre_case
    before = fingerprint_rows(s)
    with reader(s, "self") as db:
        if pending == "new":
            db.add(Ingredient(name="TEST_ONLY never flushed"))
        elif pending == "cached":
            record = db.get(Ingredient, s["nre_references"][0].fact.ingredient_id)
            assert record is not None and db.identity_map
        else:
            record = (
                db.query(Membership)
                .filter_by(user_id=s["user_id"], household_id=s["household_id"])
                .one()
            )
            if pending == "dirty":
                record.role = "EDITOR"
            else:
                db.delete(record)
        with pytest.raises(ValueError, match="clean"):
            capture_nutrition_resolution_sources(db, s["nre_context"], s["nre_scope"])
    assert fingerprint_rows(s) == before


def test_nre008_concurrent_catalog_commit_cannot_mix_snapshot(nre_case):  # noqa: F811
    s = nre_case
    with reader(s, "self") as db:
        assert (
            db.scalar(
                text("SELECT count(*) FROM nutrition_facts WHERE ingredient_id=:i"),
                {"i": s["nre_references"][0].fact.ingredient_id},
            )
            == 1
        )
        old_cut = db.scalar(text("SELECT pg_current_snapshot()::text"))
        add_reference(s)  # A second real connection commits while this snapshot stays open.
        source = capture_nutrition_resolution_sources(db, s["nre_context"], s["nre_scope"])
        assert len(source.references) == 2
        assert source.frame.source_frame.mvcc_snapshot == old_cut
        assert estimate(source).availability == "AVAILABLE"
    with pytest.raises(PermissionError, match="fixture"):
        capture_nre(s)
    context, _, _ = configure_fixture(s, s["nre_recipe"].id)
    s["nre_context"] = context
    assert len(capture_nre(s).references) == 3


def test_nre009_concurrent_rule_revoke_respects_retained_knowledge_cut(nre_case):  # noqa: F811
    s = nre_case
    with reader(s, "self") as db:
        db.scalar(text("SELECT count(*) FROM memberships"))
        grant_rule(s, "self", "SYNTHESIS_SOURCE_READ", action="REVOKE")
        old = capture_nutrition_resolution_sources(db, s["nre_context"], s["nre_scope"])
        result = estimate(old)
        assert check(old, result).decision == "CONSISTENT"
    with pytest.raises(DBAPIError):
        capture_nre(s)
    assert check(old, result).current_authorization == "NOT_CLAIMED"


def test_nre010_multiple_sessions_and_foreign_endpoint_not_one_cut(nre_case):  # noqa: F811
    s = nre_case
    with reader(s, "self") as a, reader(s, "self") as b:
        with pytest.raises(ValueError, match="SOURCE_CUT_UNSUPPORTED"):
            capture_nutrition_resolution_sources([a, b], s["nre_context"], s["nre_scope"])
        ctx = capture_module._configure_isolated_test_capture(
            s["nre_context"].database_oid, "nrc_test_foreign", s["nre_context"].manifest
        )
        with pytest.raises(PermissionError, match="database"):
            capture_nutrition_resolution_sources(a, ctx, s["nre_scope"])
    with Session(
        s["engines"]["self"].execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ),
        binds={Ingredient: s["engines"]["root"]},
    ) as routed:
        with pytest.raises(ValueError, match="SOURCE_CUT_UNSUPPORTED"):
            capture_nutrition_resolution_sources(routed, s["nre_context"], s["nre_scope"])

    class CustomRoutingSession(Session):
        def get_bind(self, *args, **kwargs):
            return s["engines"]["root"]

    with CustomRoutingSession(s["engines"]["self"]) as routed:
        with pytest.raises(ValueError, match="SOURCE_CUT_UNSUPPORTED"):
            capture_nutrition_resolution_sources(routed, s["nre_context"], s["nre_scope"])
    ordinary_factory = sessionmaker(
        s["engines"]["self"].execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        )
    )
    with ordinary_factory() as ordinary:
        assert (
            estimate(
                capture_nutrition_resolution_sources(ordinary, s["nre_context"], s["nre_scope"])
            ).availability
            == "AVAILABLE"
        )


@pytest.mark.parametrize("missing", ["version", "tier", "reference"])
def test_nre011_missing_declared_source_captured_as_absence_not_partial_success(nre_case, missing):  # noqa: F811
    s = nre_case

    def absent(d):
        identity = str(uuid4())
        if missing == "version":
            d["recipes"][0]["recipe_version_id"] = identity
            for a in d["slots"][0]["alternatives"]:
                a["recipe_version_id"] = identity
        elif missing == "tier":
            original = d["recipes"][0]["tier_ids"][0]
            d["recipes"][0]["tier_ids"][0] = identity
            for a in d["slots"][0]["alternatives"]:
                if a["tier_id"] == original:
                    a["tier_id"] = identity
        else:
            d["references"][0]["reference_id"] = identity

    source = capture_nre(s, scope_value=request_changed(s, absent))
    assert source.absences
    result = estimate(source)
    assert result.availability == "UNAVAILABLE" and not result.configurations
    assert check(source, result).decision == "CONSISTENT"


def test_nre012_capture_retains_unselected_draft_reference_rows(nre_case):  # noqa: F811
    s = nre_case
    add_reference(s)
    s["nre_context"], _, _ = configure_fixture(s, s["nre_recipe"].id)
    source = capture_nre(s)
    assert len(source.references) == 3 and any(r.fact.status == "DRAFT" for r in source.references)
    result = estimate(source)
    assert result.availability == "AVAILABLE"
    assert check(source, result).decision == "CONSISTENT"
    data = canonical(source)
    data["references"] = [r for r in data["references"] if r["fact"]["status"] != "DRAFT"]
    data["frame"]["owner_row_count"] -= 1
    assert estimate(rehash(data)).availability != "AVAILABLE"


def test_nre013_owner_recipe_seal_and_complete_children_reconstructed(nre_case):  # noqa: F811
    s = nre_case
    source = capture_nre(s)
    assert source.recipes == (s["nre_recipe"],)
    assert source.recipe_seals[0].body_fingerprint == c.resolution_hash("recipe", source.recipes[0])
    assert source.frame.owner_row_count == row_count(
        source.recipes, source.ingredients, source.references
    )
    assert sum(len(t.quantities) for t in source.recipes[0].portion_tiers) == 4


@pytest.mark.parametrize("binding", ["subject", "slot", "serving_definition"])
def test_nre014_serving_authority_cannot_move_between_subject_slot_or_definition(nre_case, binding):  # noqa: F811
    s = nre_case

    def change(d):
        item = d["slots"][0]["alternatives"][0]
        if binding == "subject":
            item["subject"]["member_id"] = str(uuid4())
        elif binding == "slot":
            item["slot_id"] = "TEST_ONLY_foreign"
        else:
            item["serving_definition"] = "TEST_ONLY_foreign"

    with pytest.raises((PermissionError, ValueError)):
        capture_nre(s, scope_value=request_changed(s, change))


def test_nre015_revocation_blocks_fresh_capture_not_historical_replay(nre_case):  # noqa: F811
    s = nre_case
    old = capture_nre(s)
    with Session(s["engines"]["root"]) as db:
        db.execute(
            text("UPDATE memberships SET role='VIEWER' WHERE household_id=:h AND user_id=:u"),
            dict(h=s["household_id"], u=s["user_id"]),
        )
        db.commit()
    with pytest.raises((PermissionError, DBAPIError)):
        capture_nre(s)
    report = check(old, estimate(old))
    assert report.decision == "CONSISTENT" and report.current_authorization == "NOT_CLAIMED"


def test_nre016_actual_oid_role_frame_and_session_settings_retained(nre_case):  # noqa: F811
    s = nre_case
    with reader(s, "self") as db:
        original_path = db.scalar(text("SHOW search_path"))
        original_timeout = db.scalar(text("SHOW statement_timeout"))
        source = capture_nutrition_resolution_sources(db, s["nre_context"], s["nre_scope"])
        actual = db.execute(
            text("SELECT session_user,pg_backend_pid(),pg_current_snapshot()::text")
        ).one()
        frame = source.frame.source_frame
        assert (frame.session.role_name, frame.backend_pid, frame.mvcc_snapshot) == tuple(actual)
        assert (
            source.synthesis_sources.frontier_hash and source.synthesis_sources.authority_frontiers
        )
        assert source.synthesis_sources.request.root.sources.streams
        assert db.scalar(text("SHOW search_path")) == original_path
        assert db.scalar(text("SHOW statement_timeout")) == original_timeout


def test_nre017_future_observed_source_or_outside_root_interval_cannot_admit(nre_case):  # noqa: F811
    s = nre_case
    add_reference(
        s, observed_at=s["nre_references"][0].fact.provenance.observed_at + timedelta(days=2)
    )
    s["nre_context"], _, _ = configure_fixture(s, s["nre_recipe"].id)
    source = capture_nre(s)
    assert estimate(source).reasons == ("SOURCE_AFTER_CUT",)

    def outside(d):
        d["root_request"]["temporal"]["interval"]["end"] = s[
            "nre_scope"
        ].root_request.temporal.interval.end + timedelta(days=1)

    with pytest.raises((ValueError, DBAPIError)):
        capture_nre(s, scope_value=request_changed(s, outside))


def test_nre018_server_reference_limit_checks_real_sql_count_before_materialization(nre_case):  # noqa: F811
    s = nre_case
    add_reference(s, count=511)
    s["nre_context"], _, _ = configure_fixture(s, s["nre_recipe"].id)
    with pytest.raises(ValueError, match="RESOURCE_EXCEEDED"):
        capture_nre(s)


def test_nre018_real_postgres_blocked_read_is_cancelled_without_partial_capture(
    nre_case,  # noqa: F811
    monkeypatch,
):
    s = nre_case
    before = fingerprint_rows(s)
    with Session(s["engines"]["root"]) as blocker:
        blocker.execute(text("LOCK TABLE public.nutrition_facts IN ACCESS EXCLUSIVE MODE"))
        # Tighten the server-owned deadline for this test; SQL really blocks on
        # another connection and psycopg cancellation must abort the capture.
        monkeypatch.setattr(capture_module, "DEADLINE_SECONDS", 0.25)
        with pytest.raises((ValueError, DBAPIError)):
            capture_nre(s)
        blocker.rollback()
    monkeypatch.undo()
    assert fingerprint_rows(s) == before
    assert estimate(capture_nre(s)).availability == "AVAILABLE"


def test_nre019_capture_has_no_writes_frontier_or_durable_cache(nre_case):  # noqa: F811
    s = nre_case
    before = fingerprint_rows(s)
    source = capture_nre(s)
    assert source.frame.source_frame.transaction_id == "UNASSIGNED_READ_ONLY"
    assert fingerprint_rows(s) == before


def test_nre020_fresh_install_0017_108_all_content_rows_zero(postgres_engine):  # noqa: F811
    import app.persistence.models  # noqa: F401
    from app.shared.db import Base

    with postgres_engine.connect() as db:
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
        assert len(Base.metadata.tables) == 108
        counts = {
            name: db.scalar(text('SELECT count(*) FROM public."' + name + '"'))
            for name in Base.metadata.tables
        }
        # Frozen 0013 installs two empty structural frontier sentinels, not
        # providers, publications, nutrition content or production defaults.
        assert {name: count for name, count in counts.items() if count} == {
            "ingredient_protein_frontier": 1,
            "culinary_feature_frontier": 1,
        }
        for relation in ("ingredient_protein_frontier", "culinary_feature_frontier"):
            assert db.scalar(text("SELECT generation FROM public." + relation)) == 0


def test_nre005_nre016_temp_shadowing_does_not_change_canonical_owner_reads(nre_case):  # noqa: F811
    s = nre_case
    with Session(s["engines"]["self"]) as db:
        # A previous transaction may leave a temp relation on this connection.
        # Creating it inside the later read-only transaction is prohibited.
        db.execute(text("CREATE TEMP TABLE ingredients(id uuid, name varchar(200))"))
        db.execute(
            text("INSERT INTO pg_temp.ingredients VALUES (:i,'TEST_ONLY forged')"), dict(i=uuid4())
        )
        db.commit()
        db.connection(
            execution_options={
                "isolation_level": "REPEATABLE READ",
                "postgresql_readonly": True,
            }
        )
        source = capture_nutrition_resolution_sources(db, s["nre_context"], s["nre_scope"])
        assert {i.id for i in source.ingredients} == {
            i.ingredient_id for i in source.recipes[0].ingredients
        }
        assert all(i.name != "TEST_ONLY forged" for i in source.ingredients)
        assert estimate(source).availability == "AVAILABLE"
