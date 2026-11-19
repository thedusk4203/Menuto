"""ITR049–080 retained-input/adversarial checks, independent expected outcomes."""

import copy
import hashlib
import inspect
import json
from uuid import uuid4

import pytest
from app.modules.identity import source_contracts as c
from app.modules.identity.source_primitives import parse
from app.modules.identity.source_replay import (
    reconstruct_identity_source_v1,
    validate_identity_source_v1,
)
from app.modules.planning.identity_source_inspection import (
    inspect_authenticated_explicit_plan_intent_v1,
)
from app.modules.policy.explicit_intent_public import resolve_explicit_plan_intent_v1
from app.modules.validation.identity_source import check_identity_source_v1
from identity_source_fixtures import available_source, instant, rehash, uid
from pydantic import ValidationError


def _deny(source):
    rehash(source)
    report = check_identity_source_v1(source, source["binding"])
    assert report.decision == "INCONSISTENT" and report.reconstructed_outcome is None
    assert report.numerical_use == "NOT_ADMITTED"
    with pytest.raises((ValueError, TypeError)):
        validate_identity_source_v1(source, source["binding"])
    return report


def _sessions(source):
    return [source["frame"]["session_start"], source["frame"]["session_end"]] + [
        row["author"]
        for key in ("root_history", "issuer_history", "binding_history", "grant_history")
        for row in source[key]
    ]


def _expired():
    s = available_source()
    row = s["grant_history"][0]
    row["command"]["effective"]["end"] = row["effective_end"] = instant(5)
    s.update(outcome="UNAVAILABLE", reason="GRANT_EXPIRED", membership=None)
    return rehash(s)


@pytest.mark.parametrize(
    "variant",
    (
        "bool_int",
        "float",
        "extra_key",
        "missing_key",
        "invalid_uuid",
        "invalid_oid",
        "invalid_time",
        "invalid_utf8",
        "duplicate_key",
        "unsupported_version",
    ),
)
def test_itr049_strict_parsing(variant):
    s = available_source()
    value = copy.deepcopy(s["frame"]["session_start"])
    if variant == "bool_int":
        value["database_oid"] = True
    elif variant == "float":
        value["database_oid"] = 10.0
    elif variant == "extra_key":
        value["asserted_authority"] = True
    elif variant == "missing_key":
        del value["tls"]
    elif variant == "invalid_oid":
        value["database_oid"] = 0
    elif variant == "invalid_time":
        value["observed_at"] = "2026-01-01T00:00:00.0000001Z"
    elif variant == "unsupported_version":
        value["version"] = 2
    elif variant == "invalid_utf8":
        value = b"\xff"
    elif variant == "duplicate_key":
        value = b'{"version":1,"version":1}'
    else:
        value = dict(s["binding"], actor_user_id="NOT-A-UUID")
        with pytest.raises(ValueError):
            parse(c.IdentityRequestBindingV1, value)
        return
    with pytest.raises((ValueError, TypeError)):
        parse(c.IdentitySessionFactV1, value)


def test_itr050_raw_versus_semantic_identity():
    a = available_source()["binding"]
    b = dict(a, request_utf8=json.dumps(json.loads(a["request_utf8"]), indent=2))
    assert (
        hashlib.sha256(a["request_utf8"].encode()).digest()
        != hashlib.sha256(b["request_utf8"].encode()).digest()
    )
    assert (
        resolve_explicit_plan_intent_v1(a["request_utf8"].encode()).payload.semantic_fingerprint
        == resolve_explicit_plan_intent_v1(b["request_utf8"].encode()).payload.semantic_fingerprint
    )


@pytest.mark.parametrize(
    "variant", ("absent_parameter", "null_parameter", "empty_parameter", "explicit_parameter")
)
def test_itr051_golden_vectors(variant):
    value = (
        []
        if variant == "absent_parameter"
        else [
            dict(
                version=1,
                kind="PARAMETER",
                object_oid=9000,
                sub_id=0,
                schema_name=None,
                object_name="TEST_ONLY.θ",
                owner_oid=None,
                definition_fingerprint=None,
                acl=None
                if variant == "null_parameter"
                else []
                if variant == "empty_parameter"
                else [[30, 10, "SET", False]],
            )
        ]
    )
    expected = hashlib.sha256(
        b"identity.source.v1\x00"
        + json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    from app.modules.identity.source_primitives import fingerprint

    assert fingerprint("identity.source.v1", value) == expected
    if value:
        assert parse(c.IdentityPrivilegeObjectFactV1, value[0]).owner_oid is None
        for owner in (0, 10):
            with pytest.raises(ValueError):
                parse(c.IdentityPrivilegeObjectFactV1, dict(value[0], owner_oid=owner))


def test_itr052_replay_determinism():
    s = available_source()
    assert check_identity_source_v1(s, s["binding"]) == check_identity_source_v1(s, s["binding"])
    assert validate_identity_source_v1(s, s["binding"]) == validate_identity_source_v1(
        s, s["binding"]
    )


def test_itr053_historical_author_interval():
    s = available_source()
    row = s["issuer_history"][0]
    row["effective_end"] = row["command"]["effective"]["end"] = instant(3)
    _deny(s)


def test_itr054_terminal_lifecycle():
    s = available_source()
    row = copy.deepcopy(s["grant_history"][0])
    row.update(
        fact_id=uid(991),
        revision=2,
        recorded_order=5,
        recorded_at=instant(5),
        previous_fact_id=row["fact_id"],
        previous_fact_fingerprint=row["fact_fingerprint"],
        effective_start=None,
        effective_end=None,
    )
    row["author"]["observed_at"] = instant(5)
    row["command"].update(
        action="REVOKE",
        effective=None,
        expected_revision=1,
        predecessor_id=s["grant_history"][0]["fact_id"],
        idempotency_key=uid(992),
    )
    s["grant_history"].append(row)
    s.update(outcome="UNAVAILABLE", reason="GRANT_REVOKED", membership=None)
    rehash(s)
    r = check_identity_source_v1(s, s["binding"])
    assert r.decision == "CONSISTENT" and r.reconstructed_outcome == "UNAVAILABLE"
    forged = copy.deepcopy(s)
    forged.update(outcome="AVAILABLE_AT_RETAINED_CUT", reason="SOURCE_AVAILABLE")
    _deny(forged)


@pytest.mark.parametrize(
    "variant",
    (
        "fabricated_owner",
        "removed_grant",
        "omitted_inherited_edge",
        "public_grant_option",
        "alter_system_bit",
        "forged_absence",
        "unsupported_catalog",
        "benign_default_control",
    ),
)
def test_itr055_role_graph_reconstruction(variant):
    s = available_source()
    if variant == "benign_default_control":
        assert check_identity_source_v1(s, s["binding"]).decision == "CONSISTENT"
        return
    for session in _sessions(s):
        routine = next(
            o
            for o in session["objects"]
            if o["kind"] == "FUNCTION" and o["schema_name"] == "public"
        )
        if variant == "fabricated_owner":
            routine["owner_oid"] = session["login_role_oid"]
        elif variant == "removed_grant":
            routine["acl"] = []
        elif variant == "public_grant_option":
            routine["acl"][0][3] = True
        elif variant == "omitted_inherited_edge":
            session["edges"] = []
        elif variant == "unsupported_catalog":
            routine["kind"] = "PROCEDURE"
        elif variant == "forged_absence":
            session["objects"].remove(routine)
        else:
            session["objects"].append(
                dict(
                    version=1,
                    kind="PARAMETER",
                    object_oid=9000,
                    sub_id=0,
                    schema_name=None,
                    object_name="TEST_ONLY.parameter",
                    owner_oid=None,
                    acl=[[0, 10, "ALTER SYSTEM", False]],
                    definition_fingerprint=None,
                )
            )
    _deny(s)


def test_itr056_principal_substitution():
    s = available_source()
    s["frame"]["session_start"]["login_role_oid"] = 30
    s["frame"]["session_end"]["login_role_oid"] = 30
    _deny(s)


def test_itr057_complete_directory():
    s = available_source()
    s["issuer_history"] = []
    _deny(s)


def test_itr058_absence_witness():
    s = available_source()
    s["grant_history"] = []
    s.update(outcome="UNAVAILABLE", reason="GRANT_ABSENT", membership=None)
    # A favorable empty list without a protected zero frontier/absence is not complete source.
    _deny(s)


def test_itr059_faithful_negatives():
    s = _expired()
    r = check_identity_source_v1(s, s["binding"])
    assert r.decision == "CONSISTENT" and r.reconstructed_outcome == "UNAVAILABLE"
    assert r.numerical_use == "NOT_ADMITTED"
    assert validate_identity_source_v1(s, s["binding"]).reason == "GRANT_EXPIRED"


def test_itr060_forged_positives():
    s = _expired()
    s.update(outcome="AVAILABLE_AT_RETAINED_CUT", reason="SOURCE_AVAILABLE")
    _deny(s)


def test_itr061_coherent_total_forgery():
    s = available_source()
    r = check_identity_source_v1(s, s["binding"])
    assert r.decision == "CONSISTENT" and r.transport == "UNVERIFIED_TRANSPORT"
    assert r.numerical_use == "NOT_ADMITTED" and not r.planner_ready


def test_itr062_bare_reports():
    s = available_source()
    claim = check_identity_source_v1(s, s["binding"])
    r = check_identity_source_v1(claim, s["binding"])
    assert r.decision != "CONSISTENT" and r.numerical_use == "NOT_ADMITTED"


def test_itr063_request_subject():
    s = available_source()
    expected = dict(s["binding"], tracked_member_id=uid(999))
    assert check_identity_source_v1(s, expected).decision == "INCONSISTENT"


def test_itr064_context_versus_axis_ownership():
    s = available_source()
    child = json.loads(s["binding"]["request_utf8"])
    child["nutrition_precision"] = 1.5
    raw = json.dumps(child, separators=(",", ":"))
    s["binding"].update(
        request_utf8=raw,
        request_preimage_fingerprint=hashlib.sha256(
            b"identity.request-preimage.v1\x00" + raw.encode()
        ).hexdigest(),
    )
    rehash(s)
    assert validate_identity_source_v1(s, s["binding"]).outcome == "AVAILABLE_AT_RETAINED_CUT"
    assert check_identity_source_v1(s, s["binding"]).decision == "CONSISTENT"
    assert resolve_explicit_plan_intent_v1(raw.encode()).payload is None


def test_itr065_authority_time():
    s = _expired()
    child = json.loads(s["binding"]["request_utf8"])
    child["context"]["declared_at"] = instant(1)
    raw = json.dumps(child, separators=(",", ":"))
    s["binding"].update(
        request_utf8=raw,
        request_preimage_fingerprint=hashlib.sha256(
            b"identity.request-preimage.v1\x00" + raw.encode()
        ).hexdigest(),
    )
    rehash(s)
    r = check_identity_source_v1(s, s["binding"])
    assert r.decision == "CONSISTENT" and r.reconstructed_outcome == "UNAVAILABLE"


def test_itr066_catalog_changes():
    s = available_source()
    session = s["frame"]["session_end"]
    session["objects"] = session["objects"][:-1]
    _deny(s)


def test_itr067_mutable_membership_limits():
    s = available_source()
    s["membership"]["role"] = "VIEWER"
    s["membership"].update(
        target_member_id=None, target_member_household_id=None, target_member_exists=None
    )
    s.update(outcome="UNAVAILABLE", reason="AUTHORIZATION_DENIED")
    rehash(s)
    assert check_identity_source_v1(s, s["binding"]).decision == "CONSISTENT"
    s.update(outcome="AVAILABLE_AT_RETAINED_CUT", reason="SOURCE_AVAILABLE")
    _deny(s)


def test_itr068_no_role_name_heuristic():
    s = available_source()
    for session in _sessions(s):
        session["system_user"] = session["session_user"]
    _deny(s)


def test_itr069_operation_bounds():
    s = available_source()
    s["grant_history"][0]["command"]["operation"] = "*"
    _deny(s)


def test_itr070_non_success_ordering():
    s = _expired()
    r = reconstruct_identity_source_v1(s, s["binding"])
    assert r.reason == "GRANT_EXPIRED" and r.outcome == "UNAVAILABLE"
    assert not any(word in r.reason for word in ("SAFE", "INFEASIBLE", "CLINICAL"))


def test_itr071_bounds_before_work():
    with pytest.raises(ValueError):
        parse(c.IdentityRequestBindingV1, b"{" * 20)
    with pytest.raises(ValueError):
        parse(c.IdentitySessionFactV1, b'{"database_oid":9999999999999999999999999}')
    with pytest.raises(ValueError):
        parse(c.IdentitySourceSnapshotV1, b" " * 8_388_609)


def test_itr072_cancellation_replay_boundary():
    s = available_source()
    s["grant_history"] = []
    _deny(s)
    assert (
        "source" not in inspect.signature(inspect_authenticated_explicit_plan_intent_v1).parameters
    )


def test_itr073_strict_test_only():
    s = available_source()
    s["binding"]["environment"] = "PRODUCTION"
    _deny(s)


def test_itr074_no_epi_upgrade():
    s = available_source()
    result = resolve_explicit_plan_intent_v1(s["binding"]["request_utf8"].encode())
    assert result.source_authority == "UNAUTHENTICATED_DECLARATION"
    assert result.validation_authority == "UNVERIFIED_TRANSPORT"
    assert result.numerical_use == "NOT_ADMITTED" and not result.planner_ready


def test_itr075_money_independence():
    child = json.loads(available_source()["binding"]["request_utf8"])
    child["budget"] = dict(constraint="SPEND_LIMIT", amount=dict(amount_minor=0, currency="VND"))
    result = resolve_explicit_plan_intent_v1(json.dumps(child).encode())
    assert (
        result.outcome == "AVAILABLE_TEST_ONLY"
        and result.payload.values.budget.amount.amount_minor == 0
    )
    assert result.payload.values.nutrition_precision == "STANDARD"


def test_itr076_no_bearer_lifecycle():
    with pytest.raises(TypeError):
        inspect_authenticated_explicit_plan_intent_v1(
            None, None, context=None, report={"decision": "CONSISTENT"}
        )


def test_itr077_independent_checker(monkeypatch):
    from app.modules.identity import source_replay

    def wrong(*args, **kwargs):
        raise AssertionError("Producer is not an independent oracle")

    monkeypatch.setattr(source_replay, "validate_identity_source_v1", wrong)
    monkeypatch.setattr(source_replay, "reconstruct_identity_source_v1", wrong)
    s = available_source()
    assert check_identity_source_v1(s, s["binding"]).decision == "CONSISTENT"


def test_itr078_immutable_complete_contracts():
    s = available_source()
    m = parse(c.IdentityRequestBindingV1, s["binding"])
    with pytest.raises(ValidationError):
        m.actor_user_id = uuid4()
    forged = c.IdentityRequestBindingV1.model_construct(**dict(m.__dict__, request_revision=True))
    with pytest.raises(ValueError):
        parse(c.IdentityRequestBindingV1, forged)


def test_itr079_source_privacy_shaping():
    s = _expired()
    s["membership"] = copy.deepcopy(s["grant_history"][0]["membership_at_issue"])
    _deny(s)


def test_itr080_historical_versus_current_claim():
    s = available_source()
    r = check_identity_source_v1(s, s["binding"])
    assert r.decision == "CONSISTENT" and r.transport == "UNVERIFIED_TRANSPORT"
    assert r.numerical_use == "NOT_ADMITTED" and not r.activation_ready


@pytest.mark.parametrize("name", ("pg_read_all_data", "pg_write_all_data", "pg_read_all_stats"))
def test_itr055_predefined_capability_is_denied_without_granting_it(name):
    # Retained-input adversary only. No database role, grant, membership or privilege is changed.
    s = available_source()
    for session in (s["frame"]["session_start"], s["frame"]["session_end"]):
        session["roles"].append(
            dict(
                version=1,
                role_oid=9001,
                role_name=name,
                can_login=False,
                superuser=False,
                create_role=False,
                create_db=False,
                replication=False,
                bypass_rls=False,
                inherit=True,
                valid_until=None,
            )
        )
        session["edges"].append(
            dict(
                version=1,
                role_oid=9001,
                member_oid=session["login_role_oid"],
                grantor_oid=10,
                inherit_option=True,
                set_option=False,
                admin_option=False,
            )
        )
    _deny(s)


def test_itr071_semantic_work_exhaustion_is_local_and_non_authorizing(monkeypatch):
    from app.modules.identity import source_limits, source_replay
    from app.modules.validation import identity_source as independent

    source = available_source()
    budget = source_replay._WorkBudget()
    budget.take(500_000)
    with pytest.raises(ValueError, match="Semantic work limit"):
        budget.take(1)
    checker_budget = independent._ReplayWork()
    checker_budget.take(500_000)
    with pytest.raises(ValueError):
        checker_budget.take(1)
    monkeypatch.setattr(source_limits, "WORK_STEPS", 10)
    with pytest.raises(ValueError, match="Semantic work limit"):
        source_replay.validate_identity_source_v1(source, source["binding"])
    # Independent accounting does not import/trust the producer's counter.
    assert check_identity_source_v1(source, source["binding"]).decision == "CONSISTENT"

    def low(self):
        self.left = 10

    monkeypatch.setattr(independent._ReplayWork, "__init__", low)
    report = check_identity_source_v1(source, source["binding"])
    assert report.decision == "INCONSISTENT" and report.reconstructed_outcome is None
    assert report.numerical_use == "NOT_ADMITTED"


def test_itr055_duplicate_native_edge_is_not_a_catalog_fact():
    source = available_source()
    for session in (source["frame"]["session_start"], source["frame"]["session_end"]):
        session["edges"].append(copy.deepcopy(session["edges"][0]))
    _deny(source)


def test_itr057_cross_kind_stream_collision_is_rejected():
    source = available_source()
    grant = source["grant_history"][0]
    old = grant["stream_id"]
    new = source["issuer_history"][0]["stream_id"]
    grant["stream_id"] = grant["command"]["grant_id"] = new
    for frontier in source["frame"]["frontiers"]:
        if frontier["kind"] == "OPERATION_GRANT" and frontier["stream_id"] == old:
            frontier["stream_id"] = new
    _deny(source)
