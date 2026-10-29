"""NRC01–32: executed PostgreSQL source authority, lifecycle and coherent capture."""

import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as c
from app.modules.nutrition.root_models import NUTRITION_ROOT_TABLES
from app.modules.nutrition.root_resolution import resolve_nutrition_root, validate_nutrition_root
from app.modules.nutrition.root_sources import (
    append_nutrition_source,
    capture_nutrition_root_sources,
)
from app.persistence.database import create_database_engine
from nutrition_root_fixtures import (
    amount,
    evidence,
    guideline,
    interval,
    member_identity,
    reference_identity,
    root_request,
)
from nutrition_root_postgres_fixtures import (
    append,
    assessment_command,
    capture,
    delegation_command,
    grant,
    prepare_nrc,
    publish_revision,
    reader,
    revised_member_command,
    source_command,
)
from nutrition_root_postgres_fixtures import nrc_server as nrc_server
from psycopg import sql
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session

pytestmark = pytest.mark.postgres


def test_nrc01_empty_installation_and_real_schema(nrc_server):
    assert not any(nrc_server["empty_install"].values())
    assert len(nrc_server["empty_install"]) == 13
    with nrc_server["engines"]["root"].connect() as db:
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0016"
        assert len(set(inspect(db).get_table_names()) - {"alembic_version"}) == 98
        assert all(t.name in inspect(db).get_table_names() for t in NUTRITION_ROOT_TABLES)


@pytest.mark.parametrize(
    "outcome,state",
    [
        ("ADMITTED", "SUPPORTED"),
        ("OUT_OF_SCOPE", "UNSUPPORTED"),
        ("EXCLUDED", "INELIGIBLE"),
        ("UNDETERMINED", "UNKNOWN"),
    ],
)
def test_nrc25_actual_supported_assertion_capture_and_replay(nrc_server, outcome, state):
    s = prepare_nrc(nrc_server)
    if outcome != "ADMITTED":
        append(
            s,
            "assessor",
            assessment_command(
                s, outcome=outcome, operation="CORRECT", replaces=(s["assessment"].id,)
            ),
        )
    source = capture(s)
    result = resolve_nutrition_root(source)
    assert result.availability == ("AVAILABLE" if state == "SUPPORTED" else "UNAVAILABLE")
    assert result.eligibility == state
    assert result.goal_direction == "MAINTAIN" and result.goal_state == "PRESENT"
    assert result.policy_synthesis == "NOT_PERFORMED" and not result.planner_ready
    assert validate_nutrition_root(result) == result


def raw_append(s, who, command_):
    with Session(s["engines"][who]) as db:
        result = db.scalar(
            text("SELECT menuto_nutrition.append(CAST(:c AS jsonb))"),
            {"c": json.dumps(canonical(command_))},
        )
        db.commit()
        return result


@pytest.mark.parametrize("credential", ["wrong", "missing", "trust"])
def test_nrc02_actual_scram_credential_and_trust_denial(nrc_server, credential):
    s = prepare_nrc(nrc_server, complete=False)
    if credential == "trust":
        with reader(s, "trust") as db, pytest.raises(DBAPIError, match="SCRAM"):
            capture_nutrition_root_sources(db, root_request(s))
    else:
        url = s["engines"]["reader"].url._replace(
            password="TEST_ONLY_wrong" if credential == "wrong" else None
        )
        engine = create_database_engine(url.render_as_string(hide_password=False))
        try:
            with pytest.raises(OperationalError), engine.connect() as db:
                db.execute(text("SELECT 1"))
        finally:
            engine.dispose()


def test_nrc03_actual_session_db_role_binding_and_set_role_spoof(nrc_server):
    s = prepare_nrc(nrc_server)
    snap = capture(s)
    with s["engines"]["reader"].connect() as db:
        oid = db.scalar(text("SELECT oid::bigint FROM pg_roles WHERE rolname=session_user"))
        db_oid = db.scalar(
            text("SELECT oid::bigint FROM pg_database WHERE datname=current_database()")
        )
    assert (snap.capture.session.role_oid, snap.capture.session.database_oid) == (oid, db_oid)
    with reader(s) as db:
        db.execute(text("SET ROLE menuto_nutrition_client"))
        with pytest.raises(DBAPIError, match="SET ROLE"):
            capture_nutrition_root_sources(db, root_request(s))
    forged = canonical(s["goal"].command)
    forged["actor_user_id"] = str(uuid4())
    with pytest.raises(DBAPIError):
        raw_append(s, "self", forged)


@pytest.mark.parametrize(
    "unsafe", ["admin", "source-owner", "superuser", "db-owner", "direct-write"]
)
def test_nrc04_unsafe_graph_rechecked_before_old_receipt(nrc_server, unsafe):
    s = prepare_nrc(nrc_server)
    role = s["names"]["self"]
    engine = s["engines"]["root"].execution_options(isolation_level="AUTOCOMMIT")
    with engine.connect() as root:
        owner = root.scalar(
            text("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()")
        )

        def execute(template, *names):
            with root.connection.driver_connection.cursor() as cur:
                cur.execute(sql.SQL(template).format(*map(sql.Identifier, names)))

        if unsafe in {"admin", "source-owner"}:
            group = "menuto_nutrition_admin" if unsafe == "admin" else "menuto_nutrition_owner"
            execute("GRANT {} TO {}", group, role)
        elif unsafe == "superuser":
            execute("ALTER ROLE {} SUPERUSER", role)
        elif unsafe == "db-owner":
            execute("ALTER DATABASE {} OWNER TO {}", s["dbname"], role)
        else:
            execute("GRANT SELECT,INSERT ON public.nutrition_goal_revisions TO {}", role)
        try:
            with pytest.raises(DBAPIError, match="Unsafe|mutation privileges"):
                append(s, "self", s["goal"].command)
            if unsafe == "direct-write":
                with (
                    Session(s["engines"]["self"]) as db,
                    pytest.raises(DBAPIError, match="Direct Nutrition"),
                ):
                    db.execute(
                        text(
                            "INSERT INTO nutrition_goal_revisions "
                            "SELECT * FROM nutrition_goal_revisions"
                        )
                    )
        finally:
            if unsafe in {"admin", "source-owner"}:
                execute("REVOKE {} FROM {}", group, role)
            elif unsafe == "superuser":
                execute("ALTER ROLE {} NOSUPERUSER", role)
            elif unsafe == "db-owner":
                execute("ALTER DATABASE {} OWNER TO {}", s["dbname"], owner)
            else:
                execute("REVOKE SELECT,INSERT ON public.nutrition_goal_revisions FROM {}", role)
    assert append(s, "self", s["goal"].command).id == s["goal"].id


def test_nrc05_provider_household_and_foreign_source_grants_do_not_transfer(nrc_server):
    a = prepare_nrc(nrc_server)
    b = prepare_nrc(nrc_server)
    grant(b, "reviewer", "GUIDELINE_REVIEW", action="REVOKE")
    assert append(a, "reviewer", a["draft"].command).id == a["draft"].id
    with pytest.raises(DBAPIError, match="capability"):
        append(b, "reviewer", b["draft"].command)
    with pytest.raises(DBAPIError, match="capability"):
        append(a, "self", a["draft"].command)
    # Real independent source group membership is not a Nutrition domain grant.
    with a["engines"]["root"].begin() as root:
        with root.connection.driver_connection.cursor() as cur:
            cur.execute(
                sql.SQL("GRANT menuto_prior_client,menuto_hierarchy_client TO {}").format(
                    sql.Identifier(a["names"]["alias"])
                )
            )
    try:
        with pytest.raises(DBAPIError, match="capability"):
            append(a, "alias", a["draft"].command)
    finally:
        with a["engines"]["root"].begin() as root:
            with root.connection.driver_connection.cursor() as cur:
                cur.execute(
                    sql.SQL("REVOKE menuto_prior_client,menuto_hierarchy_client FROM {}").format(
                        sql.Identifier(a["names"]["alias"])
                    )
                )


def test_nrc06_review_binds_actual_full_evidence_body(nrc_server):
    s = prepare_nrc(nrc_server)
    b = canonical(s["review"].command.body)
    b["evidence_fingerprint"] = "f" * 64
    cmd = source_command(s, s["review"].command.identity, b)
    with pytest.raises(DBAPIError, match="evidence|review binding"):
        raw_append(s, "reviewer", cmd)
    assert capture(s).sources


def test_nrc07_publisher_and_complete_active_review_are_required(nrc_server):
    s = prepare_nrc(nrc_server)
    b = canonical(s["publication"].command.body)
    b.update(
        action="SUPERSEDE",
        prior_publication_id=str(s["publication"].id),
        review_event_id=str(uuid4()),
    )
    cmd = source_command(s, s["publication"].command.identity, b)
    with pytest.raises(DBAPIError, match="review"):
        raw_append(s, "publisher", cmd)
    with pytest.raises(DBAPIError, match="capability"):
        raw_append(s, "reviewer", s["publication"].command)


def test_nrc08_same_verified_human_two_logins_cannot_publish_own_review(nrc_server):
    s = prepare_nrc(nrc_server)
    grant(s, "alias", "GUIDELINE_PUBLISH")
    b = canonical(s["publication"].command.body)
    b.update(action="SUPERSEDE", prior_publication_id=str(s["publication"].id))
    cmd = source_command(s, s["publication"].command.identity, b)
    with pytest.raises(DBAPIError, match="different verified humans"):
        raw_append(s, "alias", cmd)


@pytest.mark.parametrize("change", ["body", "unit", "applicability", "evidence", "protocol"])
def test_nrc09_any_reviewed_semantic_change_requires_fresh_review(nrc_server, change):
    s = prepare_nrc(nrc_server)
    body = canonical(s["guideline"])
    body["revision_id"] = str(uuid4())
    if change == "body":
        body["clauses"][0]["constraint"]["upper"]["numerator"] = 14
    elif change == "unit":
        body["clauses"][0]["descriptor"].update(metric="PROTEIN", unit="G")
    elif change == "evidence":
        body["evidence_manifest"] = [canonical(evidence("TEST_ONLY changed reviewed evidence"))]
    else:
        body["protocol"]["version"] = "TEST_ONLY_v2"
        if change == "applicability":
            body["protocol"]["scope_id"] = "TEST_ONLY_changed_scope"
        else:
            body["protocol"]["meaning"] = canonical(evidence("TEST_ONLY changed protocol meaning"))
        fp = c.nutrition_root_hash("nutrition.protocol.v1", body["protocol"])
        body["clauses"][0]["descriptor"].update(
            protocol_fingerprint=fp, scope_id=body["protocol"]["scope_id"]
        )
    body = c.NutritionGuidelineBody.model_validate(body)
    identity = reference_identity(s["provider_id"], s["family_id"])
    append(
        s,
        "reviewer",
        source_command(
            s, identity, dict(kind="DRAFT", guideline=body), revision_id=body.revision_id
        ),
    )
    b = canonical(s["publication"].command.body)
    b.update(
        action="SUPERSEDE",
        prior_publication_id=str(s["publication"].id),
        draft_revision_id=str(body.revision_id),
        body_fingerprint=c.nutrition_root_hash("nutrition.guideline-body.v1", body),
    )
    with pytest.raises(DBAPIError, match="review"):
        raw_append(s, "publisher", source_command(s, identity, b))


@pytest.mark.parametrize(
    "who,cap",
    [
        ("reviewer", "GUIDELINE_REVIEW"),
        ("publisher", "GUIDELINE_PUBLISH"),
        ("self", "MEMBER_GOAL_WRITE"),
    ],
)
def test_nrc10_revocation_precedes_idempotency_receipt_lookup(nrc_server, who, cap):
    s = prepare_nrc(nrc_server)
    command_ = s["publication"].command if who in {"reviewer", "publisher"} else s["goal"].command
    actor = "publisher" if who == "reviewer" else who
    before = capture(s)
    grant(s, who, cap, action="REVOKE")
    with pytest.raises(DBAPIError, match="capability|review"):
        append(s, actor, command_)
    # Retained pre-revocation input is still historical, not current authorization.
    assert resolve_nutrition_root(before).availability == "AVAILABLE"


@pytest.mark.parametrize(
    "bad", ["root_type", "unit", "interval", "manifest", "float", "denominator"]
)
def test_nrc11_raw_sql_cannot_bypass_structural_root_semantics(nrc_server, bad):
    s = prepare_nrc(nrc_server)
    raw = canonical(s["draft"].command)
    raw["idempotency_key"] = uuid4().hex
    root = raw["body"]["guideline"]["clauses"][0]
    if bad == "root_type":
        root["constraint"]["kind"] = "TEST_ONLY_UNKNOWN"
    elif bad == "unit":
        root["descriptor"]["unit"] = "G"
    elif bad == "interval":
        root["descriptor"]["temporal"]["interval"]["end"] = root["descriptor"]["temporal"][
            "interval"
        ]["start"]
    elif bad == "manifest":
        raw["body"]["guideline"]["mandatory_hard_roots"] = []
    elif bad == "float":
        root["constraint"]["lower"]["numerator"] = 1.5
    else:
        root["constraint"]["lower"]["denominator"] = 0
    # json.dumps is deliberately used here rather than the exact Python adapter.
    with Session(s["engines"]["reviewer"]) as db, pytest.raises(DBAPIError):
        db.scalar(text("SELECT menuto_nutrition.append(CAST(:c AS jsonb))"), {"c": json.dumps(raw)})


def test_nrc12_concurrent_publication_cas_is_atomic(nrc_server):
    s = prepare_nrc(nrc_server)
    body = canonical(s["publication"].command.body)
    body.update(action="SUPERSEDE", prior_publication_id=str(s["publication"].id))
    commands = [source_command(s, s["publication"].command.identity, body) for _ in range(2)]

    def attempt(command_):
        try:
            return append(s, "publisher", command_)
        except DBAPIError as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, commands))
    assert sum(isinstance(r, c.NutritionRecordedSource) for r in results) == 1
    assert sum(isinstance(r, DBAPIError) for r in results) == 1
    result = resolve_nutrition_root(capture(s))
    assert result.availability == "AVAILABLE"
    assert len([r for r in result.sources.sources if r.command.body.kind == "PUBLICATION"]) == 2
    # Different newly allocated UUIDs cannot race to enroll one canonical provider identity.
    commands = []
    code = "TEST_ONLY_provider_race_" + uuid4().hex
    for _ in range(2):
        command_ = canonical(s["provider"].command)
        command_.update(provider_id=str(uuid4()), code=code, idempotency_key=uuid4().hex)
        commands.append(command_)

    def enroll(command_):
        from app.modules.nutrition.root_admin import register_nutrition_provider

        try:
            with Session(s["engines"]["admin"]) as db:
                result = register_nutrition_provider(db, command_)
                db.commit()
                return result
        except DBAPIError as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(enroll, commands))
    assert sum(isinstance(r, c.NutritionProviderFact) for r in results) == 1
    assert sum(isinstance(r, DBAPIError) for r in results) == 1


def test_nrc13_exact_retry_only_changed_same_key_rejected(nrc_server):
    s = prepare_nrc(nrc_server)
    assert append(s, "self", s["goal"].command) == s["goal"]
    changed = canonical(s["goal"].command)
    changed["body"]["direction"] = "GAIN"
    with pytest.raises(DBAPIError, match="idempotency"):
        raw_append(s, "self", changed)


def test_nrc14_publication_future_supersession_retire_retract_append_only(nrc_server):
    s = prepare_nrc(nrc_server, guideline_effective=interval(end="2026-09-03T00:00:00Z"))
    old = capture(s)
    future = guideline(
        s["provider_id"],
        s["family_id"],
        proto=s["guideline"].protocol,
        span=interval("2026-09-02T00:00:00Z", "2026-09-03T00:00:00Z"),
    )
    publish_revision(s, future, prior=s["publication"].id)
    after = capture(s)
    assert resolve_nutrition_root(after).roots == resolve_nutrition_root(old).roots
    assert after.source_fingerprint != old.source_fingerprint
    body = canonical(s["publication"].command.body)
    body.update(
        action="RETIRE", review_event_id=None, prior_publication_id=str(s["publication"].id)
    )
    retired = append(s, "publisher", source_command(s, s["publication"].command.identity, body))
    assert "SOURCE_RETIRED" in resolve_nutrition_root(capture(s)).reasons
    body.update(action="RETRACT", prior_publication_id=str(retired.id))
    append(s, "publisher", source_command(s, s["publication"].command.identity, body))
    assert "SOURCE_RETRACTED" in resolve_nutrition_root(capture(s)).reasons
    assert resolve_nutrition_root(old).availability == "AVAILABLE"
    with Session(s["engines"]["publisher"]) as db, pytest.raises(DBAPIError):
        db.execute(text("DELETE FROM nutrition_guideline_publications"))


def test_nrc15_member_self_is_actual_authenticated_account_to_subject(nrc_server):
    s = prepare_nrc(nrc_server)
    actual = s["goal"]
    assert actual.subject_witness.actor_user_id == s["user_id"]
    assert actual.subject_witness.actor_member_id == s["member_id"]
    assert actual.principal_id == s["principals"]["self"].id
    assert actual.author.role_oid == s["principals"]["self"].role_oid
    assert actual.delegation_event_id is None
    forged = canonical(actual.command)
    forged["body"]["authorship"] = "SELF"
    with pytest.raises(DBAPIError):
        raw_append(s, "representative", forged)


def test_nrc16_representative_needs_exact_operation_delegation(nrc_server):
    s = prepare_nrc(nrc_server)
    cmd = revised_member_command(s, s["goal"], direction="GAIN")
    with pytest.raises(DBAPIError, match="delegation"):
        append(s, "representative", cmd)
    permission = append(s, "self", delegation_command(s))
    result = append(s, "representative", cmd)
    assert result.delegation_event_id == permission.id
    assert result.subject_witness.actor_user_id == s["representative_user_id"]
    physiology = revised_member_command(s, s["observations"]["BODY_MASS"])
    with pytest.raises(DBAPIError, match="delegation"):
        append(s, "representative", physiology)
    assert resolve_nutrition_root(capture(s)).goal_direction == "GAIN"


def test_nrc17_delegation_expiry_revoke_and_retry_order(nrc_server):
    s = prepare_nrc(nrc_server)
    append(
        s,
        "self",
        delegation_command(s, span=interval("2000-01-01T00:00:00Z", "2001-01-01T00:00:00Z")),
    )
    cmd = revised_member_command(s, s["goal"], direction="GAIN")
    with pytest.raises(DBAPIError, match="delegation"):
        append(s, "representative", cmd)
    current = append(s, "self", delegation_command(s))
    changed = append(s, "representative", cmd)
    assert changed.delegation_event_id == current.id
    revoke = delegation_command(s, action="REVOKE", previous=current.id)
    # Caller-owned uncommitted revoke holds the real member frontier lock.
    with Session(s["engines"]["self"]) as revoker:
        append_nutrition_source(revoker, revoke)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(append, s, "representative", cmd)
            revoker.commit()
            with pytest.raises(DBAPIError, match="delegation"):
                future.result(timeout=10)
    assert resolve_nutrition_root(capture(s)).goal_direction == "GAIN"


def test_nrc18_cross_member_goal_copy_and_service_authorship_denied(nrc_server):
    a = prepare_nrc(nrc_server)
    b = prepare_nrc(nrc_server)
    command_ = revised_member_command(b, b["goal"], goal_id=a["goal"].command.body.goal_id)
    with pytest.raises(DBAPIError, match="another member"):
        append(b, "self", command_)
    grant(a, "reader", "MEMBER_GOAL_WRITE")
    with pytest.raises(DBAPIError, match="member-author"):
        append(a, "reader", revised_member_command(a, a["goal"], direction="GAIN"))


def test_nrc19_goal_valid_time_future_correction_retraction_history(nrc_server):
    s = prepare_nrc(nrc_server, complete=False)
    first_id = uuid4()
    i = member_identity(s, "GOAL", "ENERGY_DIRECTION")
    first = append(
        s,
        "self",
        source_command(
            s,
            i,
            dict(
                kind="GOAL",
                operation="CREATE",
                goal_id=first_id,
                goal_type="ENERGY_DIRECTION",
                direction="MAINTAIN",
                effective=interval(end="2026-09-03T00:00:00Z"),
                replaces=(),
                provenance=evidence("TEST_ONLY explicit initial goal"),
            ),
            revision_id=first_id,
        ),
    )
    original = capture(s)
    second = append(
        s,
        "self",
        revised_member_command(
            s,
            first,
            operation="REPLACE",
            direction="GAIN",
            span=interval("2026-09-02T00:00:00Z", "2026-09-03T00:00:00Z"),
        ),
    )
    assert resolve_nutrition_root(capture(s)).goal_direction == "MAINTAIN"
    corrected = append(
        s, "self", revised_member_command(s, first, direction="CUT", span=interval())
    )
    assert resolve_nutrition_root(capture(s)).goal_direction == "CUT"
    assert resolve_nutrition_root(original).goal_direction == "MAINTAIN"
    body = canonical(corrected.command.body)
    body.update(
        operation="RETRACT",
        direction=None,
        effective=canonical(interval(end="2026-09-03T00:00:00Z")),
        replaces=sorted([str(corrected.id), str(second.id)]),
    )
    append(s, "self", source_command(s, i, body))
    root = resolve_nutrition_root(capture(s))
    assert root.goal_state == "RETRACTED" and root.goal_direction is None
    assert len([r for r in root.sources.sources if r.command.body.kind == "GOAL"]) == 4


def test_nrc20_member_goal_concurrency_and_cross_subject_idempotency(nrc_server):
    s = prepare_nrc(nrc_server)
    commands = [
        revised_member_command(s, s["goal"], direction=direction) for direction in ("CUT", "GAIN")
    ]

    def attempt(cmd):
        try:
            return append(s, "self", cmd)
        except DBAPIError as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, commands))
    assert sum(isinstance(r, c.NutritionRecordedSource) for r in results) == 1
    assert sum(isinstance(r, DBAPIError) for r in results) == 1
    other = prepare_nrc(nrc_server)
    with pytest.raises(DBAPIError, match="capability"):
        append(other, "self", s["goal"].command)


def set_legacy_profile(s, mass):
    from decimal import Decimal

    from app.modules.nutrition.models import MemberNutritionProfile
    from sqlalchemy import select

    with Session(s["engines"]["root"]) as db:
        profile = db.scalar(
            select(MemberNutritionProfile).where(MemberNutritionProfile.member_id == s["member_id"])
        )
        if profile is None:
            profile = MemberNutritionProfile(
                household_id=s["household_id"],
                member_id=s["member_id"],
                created_by_user_id=s["user_id"],
                body_mass_kg=Decimal(mass),
            )
            db.add(profile)
        else:
            profile.body_mass_kg = Decimal(mass)
        db.commit()
        return profile.row_version


def test_nrc21_observation_legacy_conflict_requires_explicit_reconciliation(nrc_server):
    s = prepare_nrc(nrc_server)
    old = s["observations"]["BODY_MASS"]
    assert old.legacy_anchor.profile is None
    set_legacy_profile(s, "4")
    conflict = revised_member_command(s, old)
    with pytest.raises(DBAPIError, match="reconcile"):
        append(s, "self", conflict)
    agreed = append(s, "self", revised_member_command(s, old, value=amount(4)))
    assert agreed.legacy_anchor.profile.body_mass_kg == "4.000000"
    assert agreed.legacy_anchor.profile.row_version == 1
    set_legacy_profile(s, "3.5")
    with pytest.raises(DBAPIError, match="reconcile"):
        append(s, "self", revised_member_command(s, agreed, value=amount(4)))
    fresh = append(s, "self", revised_member_command(s, agreed, value=amount(7, 2)))
    assert fresh.legacy_anchor.profile.row_version == 2


def test_nrc22_legacy_and_observation_changes_require_new_assessment(nrc_server):
    s = prepare_nrc(nrc_server)
    retained = capture(s)
    set_legacy_profile(s, "4")
    stale = resolve_nutrition_root(capture(s))
    assert stale.eligibility == "UNKNOWN" and "PHYSIOLOGICAL_SOURCE_CHANGED" in stale.reasons
    for fact in ("BODY_MASS", "HEIGHT"):
        old = s["observations"][fact]
        s["observations"][fact] = append(
            s,
            "self",
            revised_member_command(
                s, old, value=amount(4) if fact == "BODY_MASS" else old.command.body.value
            ),
        )
    assert resolve_nutrition_root(capture(s)).eligibility == "UNKNOWN"
    append(
        s, "assessor", assessment_command(s, operation="CORRECT", replaces=(s["assessment"].id,))
    )
    assert resolve_nutrition_root(capture(s)).availability == "AVAILABLE"
    assert resolve_nutrition_root(retained).availability == "AVAILABLE"


def test_nrc23_exact_assessor_protocol_capability_separate_from_publisher(nrc_server):
    s = prepare_nrc(nrc_server)
    command_ = assessment_command(s, operation="CORRECT", replaces=(s["assessment"].id,))
    with pytest.raises(DBAPIError, match="capability"):
        append(s, "publisher", command_)
    forged = canonical(command_)
    forged["identity"]["code"] = forged["body"]["protocol_fingerprint"] = "f" * 64
    with pytest.raises(DBAPIError, match="capability"):
        raw_append(s, "assessor", forged)
    with pytest.raises(DBAPIError, match="reviewed published protocol"):
        grant(s, "assessor", "ELIGIBILITY_ATTEST", protocol="f" * 64)


@pytest.mark.parametrize("bad", ["partial", "value", "revision", "legacy_anchor"])
def test_nrc24_assessment_requires_complete_canonical_observations(nrc_server, bad):
    s = prepare_nrc(nrc_server)
    raw = canonical(assessment_command(s, operation="CORRECT", replaces=(s["assessment"].id,)))
    b = raw["body"]
    if bad == "partial":
        b["observations"] = b["observations"][:1]
        b["missing_observations"] = ["HEIGHT"]
    elif bad == "value":
        b["observations"][0]["value"] = {"numerator": 9, "denominator": 1}
    elif bad == "revision":
        b["observations"][0]["revision_id"] = str(uuid4())
    else:
        b["observations"][0]["legacy_anchor_fingerprint"] = "f" * 64
    with pytest.raises(DBAPIError):
        raw_append(s, "assessor", raw)


def inventory(s):
    with s["engines"]["root"].connect() as db:
        return {
            t.name: db.scalar(text('SELECT count(*) FROM "' + t.name + '"'))
            for t in NUTRITION_ROOT_TABLES
        }


def test_nrc26_reader_validator_scopes_are_distinct_no_partial_capture(nrc_server):
    s = prepare_nrc(nrc_server)
    before = inventory(s)
    for who, purpose in (("other", "ROOT"), ("reader", "VALIDATOR"), ("validator", "ROOT")):
        with reader(s, who) as db, pytest.raises(DBAPIError, match="capability"):
            capture_nutrition_root_sources(db, root_request(s, purpose=purpose))
    assert capture(s, who="validator").request.purpose == "VALIDATOR"
    other = prepare_nrc(nrc_server)
    grant(other, "reader", "ROOT_SOURCE_READ", action="REVOKE")
    with reader(s) as db, pytest.raises(DBAPIError, match="capability"):
        capture_nutrition_root_sources(db, root_request(other))
    assert capture(s).request.subject.member_id == s["member_id"]
    # Failed reads never create source state; unrelated explicit fixture writes are excluded.
    assert all(inventory(s)[name] >= count for name, count in before.items())


@pytest.mark.parametrize(
    "isolation,readonly,assigned,success",
    [
        ("REPEATABLE READ", True, False, True),
        ("SERIALIZABLE", True, False, True),
        ("READ COMMITTED", True, False, False),
        ("REPEATABLE READ", False, False, False),
        ("REPEATABLE READ", True, True, False),
    ],
)
def test_nrc27_actual_same_session_clean_readonly_capture(
    nrc_server, isolation, readonly, assigned, success
):
    s = prepare_nrc(nrc_server)
    before = inventory(s)
    with reader(s, isolation=isolation, readonly=readonly) as db:
        if assigned:
            db.scalar(text("SELECT pg_current_xact_id()"))
        if success:
            pid = db.scalar(text("SELECT pg_backend_pid()"))
            result = capture_nutrition_root_sources(db, root_request(s))
            assert result.capture.backend_pid == pid and result.capture.isolation == isolation
            assert result.capture.transaction_id == "UNASSIGNED_READ_ONLY" and db.in_transaction()
        else:
            with pytest.raises(DBAPIError, match="Clean"):
                capture_nutrition_root_sources(db, root_request(s))
    assert inventory(s) == before


def test_nrc28_mvcc_cut_does_not_splice_concurrent_correction_or_revoke(nrc_server):
    s = prepare_nrc(nrc_server)
    with reader(s) as db:
        old = capture_nutrition_root_sources(db, root_request(s))
        append(
            s, "self", revised_member_command(s, s["observations"]["BODY_MASS"], value=amount(4))
        )
        grant(s, "reader", "ROOT_SOURCE_READ", action="REVOKE")
        retained = capture_nutrition_root_sources(db, root_request(s))
        assert retained.sources == old.sources and retained.streams == old.streams
        assert retained.authority == old.authority
    with reader(s) as db, pytest.raises(DBAPIError, match="capability"):
        capture_nutrition_root_sources(db, root_request(s))
    assert resolve_nutrition_root(old).availability == "AVAILABLE"
    # A stale write snapshot must not resurrect a revoked capability through retry.
    with Session(
        s["engines"]["self"].execution_options(isolation_level="REPEATABLE READ")
    ) as writer:
        writer.scalar(text("SELECT pg_current_snapshot()"))
        grant(s, "self", "MEMBER_GOAL_WRITE", action="REVOKE")
        with pytest.raises(DBAPIError, match="serializ|capability"):
            append_nutrition_source(writer, s["goal"].command)


def test_nrc29_full_source_tombstones_frontiers_and_absence_witnesses(nrc_server):
    s = prepare_nrc(nrc_server)
    old = s["goal"]
    changed = append(s, "self", revised_member_command(s, old, direction="GAIN"))
    append(s, "self", revised_member_command(s, changed, operation="RETRACT", direction=None))
    snap = capture(s)
    goals = [r for r in snap.sources if r.command.body.kind == "GOAL"]
    assert len(goals) == 3 and goals[-1].command.body.operation == "RETRACT"
    assert resolve_nutrition_root(snap).goal_state == "RETRACTED"
    from nutrition_root_fixtures import rehash_sources

    forged = canonical(snap)
    forged["sources"] = [r for r in forged["sources"] if r["id"] != str(changed.id)]
    with pytest.raises(ValueError, match="history|frontier"):
        resolve_nutrition_root(rehash_sources(forged))
    empty = prepare_nrc(nrc_server, complete=False)
    absent = capture(empty)
    assert len(absent.capture.absence_stream_keys) >= 4
    assert resolve_nutrition_root(absent).goal_state == "ABSENT"


def test_nrc30_actual_tls_verification_password_rotation_and_role_recreation(nrc_server, tmp_path):
    s = prepare_nrc(nrc_server)
    with s["engines"]["root"].connect() as root:
        assert root.scalar(text("SHOW ssl")) == "on"
        certificate = root.scalar(text("SELECT pg_read_file(current_setting('ssl_cert_file'))"))
    ca = tmp_path / "TEST_ONLY_nrc_ca.crt"
    ca.write_text(certificate)
    verified = create_database_engine(
        s["engines"]["reader"]
        .url.update_query_dict(dict(sslmode="verify-full", sslrootcert=str(ca)))
        .render_as_string(hide_password=False)
    )
    try:
        with Session(
            verified.execution_options(isolation_level="REPEATABLE READ", postgresql_readonly=True)
        ) as db:
            assert db.scalar(text("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")) is True
            assert (
                capture_nutrition_root_sources(
                    db, root_request(s)
                ).capture.session.authentication_method
                == "scram-sha-256"
            )
    finally:
        verified.dispose()
    bad = tmp_path / "TEST_ONLY_invalid_ca.crt"
    bad.write_text("TEST_ONLY invalid root certificate")
    wrong = create_database_engine(
        s["engines"]["reader"]
        .url.update_query_dict(dict(sslmode="verify-full", sslrootcert=str(bad)))
        .render_as_string(hide_password=False)
    )
    try:
        with pytest.raises(OperationalError), wrong.connect():
            pass
    finally:
        wrong.dispose()
    role = s["names"]["self"]
    original = s["engines"]["self"].url.password
    rotated = "TEST_ONLY_rotated_" + uuid4().hex

    def root_statement(statement, *values):
        with s["engines"]["root"].begin() as db:
            with db.connection.driver_connection.cursor() as cur:
                cur.execute(sql.SQL(statement).format(*values))

    root_statement("ALTER ROLE {} PASSWORD {}", sql.Identifier(role), sql.Literal(rotated))
    s["engines"]["self"].dispose()
    with pytest.raises(OperationalError):
        append(s, "self", s["goal"].command)
    rotated_engine = create_database_engine(
        s["engines"]["self"].url.set(password=rotated).render_as_string(hide_password=False)
    )
    try:
        with Session(rotated_engine) as db:
            assert append_nutrition_source(db, s["goal"].command).id == s["goal"].id
    finally:
        rotated_engine.dispose()
        root_statement("ALTER ROLE {} PASSWORD {}", sql.Identifier(role), sql.Literal(original))
    # A new role with the same name/password still has a different actual OID.
    s["engines"]["self"].dispose()
    root_statement("DROP ROLE {}", sql.Identifier(role))
    root_statement("CREATE ROLE {} LOGIN PASSWORD {}", sql.Identifier(role), sql.Literal(original))
    root_statement("GRANT menuto_nutrition_client TO {}", sql.Identifier(role))
    with pytest.raises(DBAPIError, match="not enrolled"):
        append(s, "self", s["goal"].command)
    assert resolve_nutrition_root(capture(s)).goal_state == "PRESENT"


def test_nrc31_raw_sql_exact_nearby_rationals_no_rounding(nrc_server):
    from fractions import Fraction

    s = prepare_nrc(nrc_server, complete=False)
    lower = amount((1 << 100) - 1, (1 << 101) - 1)
    upper = amount(1 << 100, (1 << 101) + 1)
    assert Fraction(lower.numerator, lower.denominator) < Fraction(
        upper.numerator, upper.denominator
    )
    body = canonical(s["guideline"])
    revision = uuid4()
    body["revision_id"] = str(revision)
    body["clauses"][0]["constraint"] = {
        "kind": "RANGE",
        "lower": canonical(lower),
        "upper": canonical(upper),
    }
    cmd = source_command(
        s,
        reference_identity(s["provider_id"], s["family_id"]),
        dict(kind="DRAFT", guideline=body),
        revision_id=revision,
    )
    result = raw_append(s, "reviewer", cmd)
    stored = result["command"]["body"]["guideline"]["clauses"][0]["constraint"]
    assert stored["lower"] == canonical(lower) and stored["upper"] == canonical(upper)
    bad = canonical(cmd)
    bad["idempotency_key"] = uuid4().hex
    bad["body"]["guideline"]["clauses"][0]["constraint"].update(
        lower=canonical(upper), upper=canonical(lower)
    )
    with pytest.raises(DBAPIError, match="range"):
        raw_append(s, "reviewer", bad)


@pytest.mark.parametrize("limit", ["bytes", "integer", "evidence_manifest", "environment"])
def test_nrc31_server_owned_command_limits_and_content_environment(nrc_server, limit):
    s = prepare_nrc(nrc_server)
    before = inventory(s)
    raw = canonical(s["draft"].command)
    raw["idempotency_key"] = uuid4().hex
    body = raw["body"]["guideline"]
    if limit == "bytes":
        body["edition"] = "TEST_ONLY" * 20000
    elif limit == "integer":
        body["clauses"][0]["constraint"]["upper"]["numerator"] = 1 << 128
    elif limit == "evidence_manifest":
        body["evidence_manifest"] *= 33
    else:
        raw = canonical(revised_member_command(s, s["goal"], direction="GAIN"))
        raw["body"]["provenance"]["environment"] = "REVIEWED_PRODUCTION"
    with (
        Session(s["engines"]["self" if limit == "environment" else "reviewer"]) as db,
        pytest.raises(DBAPIError),
    ):
        db.scalar(text("SELECT menuto_nutrition.append(CAST(:c AS jsonb))"), {"c": json.dumps(raw)})
    assert inventory(s) == before


def test_nrc31_server_history_depth_rejects_overflow_without_truncation(nrc_server):
    s = prepare_nrc(nrc_server)
    goal = s["goal"]
    for index in range(63):
        goal = append(
            s,
            "self",
            revised_member_command(s, goal, direction=("CUT", "GAIN", "MAINTAIN")[index % 3]),
        )
    before = inventory(s)
    with pytest.raises(DBAPIError, match="history-depth"):
        append(s, "self", revised_member_command(s, goal, direction="GAIN"))
    assert inventory(s) == before
    captured = capture(s)
    assert len([r for r in captured.sources if r.command.body.kind == "GOAL"]) == 64
    assert resolve_nutrition_root(captured).goal_revision_id == goal.id


def test_nrc25_proven_exclusion_keeps_unrelated_missing_evidence_observable(nrc_server):
    s = prepare_nrc(nrc_server)
    protocol = s["guideline"].protocol
    cmd = assessment_command(
        s,
        outcome="EXCLUDED",
        operation="CORRECT",
        replaces=(s["assessment"].id,),
        observations={"BODY_MASS": s["observations"]["BODY_MASS"]},
        slots=protocol.excluded.evidence_slots,
    )
    append(s, "assessor", cmd)
    result = resolve_nutrition_root(capture(s))
    assert result.eligibility == "INELIGIBLE" and not result.roots
    assert "PHYSIOLOGICAL_INPUT_MISSING" in result.reasons
    assert "INSUFFICIENT_EVIDENCE" in result.reasons


def test_nrc32_loss_refusal_no_read_drift_and_restored_db_binding(nrc_server):
    from alembic import command
    from alembic.config import Config
    from app.persistence.models import Base
    from sqlalchemy import select

    s = prepare_nrc(nrc_server)
    before = inventory(s)
    retained = capture(s)
    assert resolve_nutrition_root(retained).availability == "AVAILABLE"
    assert inventory(s) == before
    config = Config(str(nrc_server["config"].config_file_name))
    with s["engines"]["root"].connect() as db:
        config.attributes["connection"] = db
        with pytest.raises(DBAPIError, match="Refusing destructive downgrade"):
            command.downgrade(config, "0015")
        db.rollback()
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0016"
        assert (
            db.scalar(
                text(
                    "SELECT count(*) FROM nutrition_source_providers "
                    "WHERE environment='REVIEWED_PRODUCTION'"
                )
            )
            == 0
        )
        assert (
            db.scalar(
                text(
                    "SELECT count(*) FROM nutrition_source_evidence_artifacts "
                    "WHERE environment='REVIEWED_PRODUCTION'"
                )
            )
            == 0
        )
    restored = "nrc_restore_" + uuid4().hex
    maintenance = s["maintenance"]
    restore_engine = None
    reader_engine = None
    saved_hba = None
    try:
        with maintenance.connect() as db:
            db.execute(text(f'CREATE DATABASE "{restored}"'))
        restore_engine = create_database_engine(
            s["parsed"].set(database=restored).render_as_string(hide_password=False)
        )
        with restore_engine.connect() as dest:
            cfg = Config(str(config.config_file_name))
            cfg.attributes["connection"] = dest
            command.upgrade(cfg, "head")
            dest.commit()
        with s["engines"]["root"].connect() as original, restore_engine.begin() as dest:
            dest.execute(text("SET LOCAL session_replication_role=replica"))
            # Replace this disposable destination's structural baseline rows with
            # the actual retained database image; no production instance is used.
            dest.execute(
                text(
                    "TRUNCATE TABLE "
                    + ",".join('"' + t.name + '"' for t in Base.metadata.tables.values())
                )
            )
            for table in Base.metadata.sorted_tables:
                rows = [dict(r) for r in original.execute(select(table)).mappings()]
                if rows:
                    dest.execute(table.insert(), rows)
        with maintenance.connect() as db:
            saved_hba = db.scalar(text("SELECT pg_read_file(:p)"), {"p": s["hba_path"]})
            address = db.scalar(text("SELECT host(inet_client_addr())"))
            from ipaddress import ip_address

            networks = {"127.0.0.1/32", "::1/128"}
            if address:
                networks.add(address + ("/32" if ip_address(address).version == 4 else "/128"))
            rules = "\n".join(
                f"host {restored} {s['names']['reader']} {network} scram-sha-256"
                for network in sorted(networks)
            )
            s["write_hba"](db, rules + "\n" + saved_hba)
        reader_engine = create_database_engine(
            s["engines"]["reader"].url.set(database=restored).render_as_string(hide_password=False)
        )
        with Session(
            reader_engine.execution_options(
                isolation_level="REPEATABLE READ", postgresql_readonly=True
            )
        ) as db:
            with pytest.raises(DBAPIError, match="not enrolled|database binding"):
                capture_nutrition_root_sources(db, root_request(s))
        assert resolve_nutrition_root(retained).availability == "AVAILABLE"
    finally:
        if reader_engine is not None:
            reader_engine.dispose()
        if restore_engine is not None:
            restore_engine.dispose()
        with maintenance.connect() as db:
            if saved_hba is not None:
                s["write_hba"](db, saved_hba)
            db.execute(text(f'DROP DATABASE IF EXISTS "{restored}" WITH (FORCE)'))
    assert inventory(s) == before
