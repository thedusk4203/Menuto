"""Independently authored TEST_ONLY primitive fixtures; no deployed source or human authority."""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.modules.validation.identity_source import LEGACY_ROUTINE_PINS


def uid(number):
    return str(UUID(int=number))


def instant(offset=0):
    return (datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=offset)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


def h(tag, data):
    return hashlib.sha256(
        tag.encode("ascii")
        + b"\x00"
        + json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def role(oid, name, *, login=False, superuser=False):
    return dict(
        version=1,
        role_oid=oid,
        role_name=name,
        can_login=login,
        superuser=superuser,
        create_role=False,
        create_db=False,
        replication=False,
        bypass_rls=False,
        inherit=True,
        valid_until=None,
    )


def objects():
    names = (
        "bootstrap_root",
        "change_issuer",
        "change_binding",
        "change_operation_grant",
        "capture_request_source",
        "_session_fact_v1",
        "_safe_role_v1",
        "_parameter_acl_facts_v1",
        "_tls_fact_v1",
        "_parse_command_v1",
        "_canonical_hash_v1",
        "_lock_frontiers_v1",
        "_authority_at_v1",
        "_assert_lifecycle_v1",
        "_append_receipt_v1",
        "_capture_sources_v1",
        "_reject_history_mutation_v1",
    )
    result = [
        dict(
            version=1,
            kind="DATABASE",
            object_oid=1000,
            sub_id=0,
            schema_name=None,
            object_name="TEST_ONLY_identity",
            owner_oid=10,
            acl=[],
            definition_fingerprint=None,
        ),
        dict(
            version=1,
            kind="SCHEMA",
            object_oid=1001,
            sub_id=0,
            schema_name=None,
            object_name="menuto_identity_source",
            owner_oid=21,
            acl=[[20, 21, "USAGE", False], [22, 21, "USAGE", False], [23, 21, "USAGE", False]],
            definition_fingerprint=None,
        ),
    ]
    for index, name in enumerate(names):
        grantee = (
            20
            if name in {"bootstrap_root", "change_issuer"}
            else (
                22
                if name in {"change_binding", "change_operation_grant"}
                else 23
                if name == "capture_request_source"
                else 21
            )
        )
        result.append(
            dict(
                version=1,
                kind="FUNCTION",
                object_oid=1100 + index,
                sub_id=0,
                schema_name="menuto_identity_source",
                object_name=name,
                owner_oid=21,
                acl=[[grantee, 21, "EXECUTE", False]],
                definition_fingerprint=hashlib.sha256(
                    ("TEST_ONLY authored body " + name).encode()
                ).hexdigest(),
            )
        )
    result.append(
        dict(
            version=1,
            kind="SCHEMA",
            object_oid=1002,
            sub_id=0,
            schema_name=None,
            object_name="public",
            owner_oid=10,
            acl=[[0, 10, "USAGE", False]],
            definition_fingerprint=None,
        )
    )
    for index, (name, signature, digest) in enumerate(LEGACY_ROUTINE_PINS):
        result.append(
            dict(
                version=1,
                kind="FUNCTION",
                object_oid=3000 + index,
                sub_id=0,
                schema_name="public",
                object_name=name,
                owner_oid=10,
                acl=[[0, 10, "EXECUTE", False], [10, 10, "EXECUTE", False]],
                definition_fingerprint=digest,
            )
        )
    from app.modules.validation.identity_source import NATIVE_SSLINFO_PINS

    for index, name in enumerate(
        ("menuto_prior", "menuto_hierarchy", "menuto_nutrition", "menuto_nutrition_synthesis")
    ):
        result.append(
            dict(
                version=1,
                kind="SCHEMA",
                object_oid=1010 + index,
                sub_id=0,
                schema_name=None,
                object_name=name,
                owner_oid=50 + index,
                acl=[[50 + index, 50 + index, "USAGE", False]],
                definition_fingerprint=None,
            )
        )
    for index, (name, digest) in enumerate(NATIVE_SSLINFO_PINS["menuto_prior"].items()):
        acl = [[10, 10, "EXECUTE", False]]
        if name == "ssl_is_used":
            acl += [[21, 10, "EXECUTE", False]] + [[50 + i, 10, "EXECUTE", False] for i in range(4)]
        result.append(
            dict(
                version=1,
                kind="FUNCTION",
                object_oid=3500 + index,
                sub_id=0,
                schema_name="menuto_prior",
                object_name=name,
                owner_oid=10,
                acl=sorted(acl),
                definition_fingerprint=digest,
            )
        )
    return sorted(result, key=lambda o: (o["kind"], o["object_oid"], o["sub_id"]))


def session(mode, when, *, read_only=False):
    groups = [
        role(10, "TEST_ONLY_bootstrap", login=True, superuser=True),
        role(20, "menuto_identity_bootstrap"),
        role(21, "menuto_identity_source_owner"),
        role(22, "menuto_identity_issuer"),
        role(23, "menuto_identity_requester"),
    ]
    oid, name, group = {
        "BOOTSTRAP": (10, "TEST_ONLY_bootstrap", 20),
        "ISSUER": (30, "TEST_ONLY_issuer", 22),
        "REQUESTER": (40, "TEST_ONLY_requester", 23),
    }[mode]
    if mode != "BOOTSTRAP":
        groups.append(role(oid, name, login=True))
    return dict(
        version=1,
        database_oid=1000,
        database_owner_oid=10,
        login_role_oid=oid,
        execution_owner_oid=21,
        database_name="TEST_ONLY_identity",
        endpoint_id="TEST_ONLY_ENDPOINT",
        client_address="127.0.0.1",
        server_address="127.0.0.1",
        server_port=5432,
        backend_pid=9999,
        session_user=name,
        system_user="scram-sha-256:" + name,
        requested_role="none",
        authentication_method="scram-sha-256",
        tls=True,
        isolation="REPEATABLE_READ" if read_only else "READ_COMMITTED",
        read_only=read_only,
        observed_at=instant(when),
        roles=sorted(groups, key=lambda r: r["role_oid"]),
        edges=[
            dict(
                version=1,
                role_oid=group,
                member_oid=oid,
                grantor_oid=10,
                inherit_option=True,
                set_option=False,
                admin_option=False,
            )
        ],
        objects=objects(),
    )


def member():
    return dict(
        version=1,
        user_id=uid(300),
        household_id=uid(400),
        user_exists=True,
        membership_id=uid(500),
        membership_user_id=uid(300),
        membership_household_id=uid(400),
        actor_member_id=uid(600),
        role="OWNER",
        actor_member_household_id=uid(400),
        target_member_id=uid(700),
        target_member_household_id=uid(400),
        target_member_exists=True,
    )


def authored(kind, number, *, action=None, previous=None, when=None):
    second = number if when is None else when
    first = "INITIALIZE" if kind == "ROOT" else "GRANT" if kind == "OPERATION_GRANT" else "ENROLL"
    command = dict(
        version=1,
        root_id=uid(100),
        idempotency_key=uid(800 + number),
        expected_revision=previous["revision"] if previous else 0,
        predecessor_id=previous["fact_id"] if previous else None,
        evidence_id="TEST_ONLY_EVIDENCE",
        evidence_version="TEST_ONLY_V1",
        evidence_preimage="TEST_ONLY source attestation",
        environment="TEST_ONLY",
        kind=kind,
        action=action or first,
        effective=None
        if action == "REVOKE"
        else dict(version=1, mode="IMMEDIATE", start=None, end=instant(86400 * 30)),
    )
    if kind == "ISSUER":
        command.update(
            issuer_id=uid(200),
            role_name="TEST_ONLY_issuer",
            user_id=uid(201),
            capability="BINDINGS_AND_SCOPE_GRANTS",
        )
    elif kind == "BINDING":
        command.update(
            binding_id=uid(301),
            issuer_id=uid(200),
            user_id=uid(300),
            role_name="TEST_ONLY_requester",
        )
    elif kind == "OPERATION_GRANT":
        command.update(
            grant_id=uid(401),
            binding_id=uid(301),
            issuer_id=uid(200),
            household_id=uid(400),
            tracked_member_id=uid(700),
            operation="CAPTURE_EXPLICIT_PLAN_INTENT",
        )
    fact = dict(
        version=1,
        fact_id=uid(900 + number),
        root_id=uid(100),
        stream_id=uid({"ROOT": 100, "ISSUER": 200, "BINDING": 301, "OPERATION_GRANT": 401}[kind]),
        stream_kind=kind,
        revision=previous["revision"] + 1 if previous else 1,
        recorded_order=number,
        recorded_at=instant(second),
        previous_fact_id=previous["fact_id"] if previous else None,
        previous_fact_fingerprint=previous["fact_fingerprint"] if previous else None,
        command=command,
        command_fingerprint=h("identity.command.v1", command),
        effective_start=None if action == "REVOKE" else instant(second),
        effective_end=None if action == "REVOKE" else instant(86400 * 30),
        author=session("BOOTSTRAP" if kind in {"ROOT", "ISSUER"} else "ISSUER", second),
        author_issuer_fact_id=None if kind in {"ROOT", "ISSUER"} else uid(902),
        target_role=role(30, "TEST_ONLY_issuer", login=True)
        if kind == "ISSUER"
        else role(40, "TEST_ONLY_requester", login=True)
        if kind == "BINDING"
        else None,
        membership_at_issue=member() if kind == "OPERATION_GRANT" else None,
    )
    fact["fact_fingerprint"] = h("identity.fact.v1", fact)
    return fact


def request():
    context = dict(
        request_id=uid(750),
        request_revision=0,
        household_id=uid(400),
        actor_user_id=uid(300),
        tracked_member_id=uid(700),
        horizon=dict(start=instant(100), end=instant(86400)),
        declared_at=instant(5),
    )
    raw = json.dumps(
        dict(
            contract_version="explicit-plan-intent-request.v1",
            source="REQUEST_EXPLICIT",
            environment="TEST_ONLY",
            context=context,
            nutrition_precision="STANDARD",
            cost_preference="NORMAL",
            kitchen_effort="NORMAL",
            budget=dict(constraint="NONE", amount=None),
        ),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return dict(
        version=1,
        operation="CAPTURE_EXPLICIT_PLAN_INTENT",
        **{k: v for k, v in context.items() if k != "declared_at"},
        request_utf8=raw,
        request_preimage_fingerprint=hashlib.sha256(
            b"identity.request-preimage.v1\x00" + raw.encode()
        ).hexdigest(),
        environment="TEST_ONLY",
    )


def rehash(source):
    for key in ("root_history", "issuer_history", "binding_history", "grant_history"):
        for fact in source[key]:
            fact["command_fingerprint"] = h("identity.command.v1", fact["command"])
            fact["fact_fingerprint"] = h(
                "identity.fact.v1", {k: v for k, v in fact.items() if k != "fact_fingerprint"}
            )
    entries = []
    for key in ("root_history", "binding_history", "grant_history"):
        rows = source[key]
        if rows:
            frontier = next(
                f for f in source["frame"]["frontiers"] if f["kind"] == rows[0]["stream_kind"]
            )
            frontier.update(
                revision=len(rows),
                fact_count=len(rows),
                head_id=rows[-1]["fact_id"],
                head_fingerprint=rows[-1]["fact_fingerprint"],
            )
    issuers = source["issuer_history"]
    if issuers:
        frontier = next(f for f in source["frame"]["frontiers"] if f["kind"] == "ISSUER_DIRECTORY")
        entries = [
            [
                issuers[0]["stream_id"],
                len(issuers),
                issuers[-1]["fact_id"],
                issuers[-1]["fact_fingerprint"],
                len(issuers),
            ]
        ]
        frontier.update(
            revision=len(issuers),
            fact_count=len(issuers),
            head_id=issuers[-1]["fact_id"],
            head_fingerprint=issuers[-1]["fact_fingerprint"],
            directory_entries=entries,
            directory_fingerprint=h("identity.source.v1", {"issuer_directory": entries}),
        )
    source["frame"]["total_fact_count"] = sum(
        len(source[k])
        for k in ("root_history", "issuer_history", "binding_history", "grant_history")
    )
    source["source_fingerprint"] = h(
        "identity.source.v1", {k: v for k, v in source.items() if k != "source_fingerprint"}
    )
    return source


def available_source():
    facts = [
        authored(kind, number)
        for number, kind in enumerate(("ROOT", "ISSUER", "BINDING", "OPERATION_GRANT"), 1)
    ]
    frontiers = []
    for kind, fact in zip(("ROOT", "ISSUER_DIRECTORY", "BINDING", "OPERATION_GRANT"), facts):
        frontiers.append(
            dict(
                version=1,
                root_id=uid(100),
                stream_id=uid(100) if kind == "ISSUER_DIRECTORY" else fact["stream_id"],
                kind=kind,
                revision=1,
                fact_count=1,
                head_id=fact["fact_id"],
                head_fingerprint=fact["fact_fingerprint"],
                directory_entries=[],
                directory_fingerprint=None,
            )
        )
    source = dict(
        version=1,
        binding=request(),
        frame=dict(
            version=1,
            root_id=uid(100),
            deployment_context_id=uid(100),
            started_at=instant(5),
            finished_at=instant(6),
            transaction_started_at=instant(5),
            snapshot_id="TEST_ONLY:1:2:",
            session_start=session("REQUESTER", 5, read_only=True),
            session_end=session("REQUESTER", 6, read_only=True),
            frontiers=frontiers,
            total_fact_count=4,
            environment="TEST_ONLY",
            transport="UNVERIFIED_TRANSPORT",
        ),
        root_history=[facts[0]],
        issuer_history=[facts[1]],
        binding_history=[facts[2]],
        grant_history=[facts[3]],
        membership=member(),
        absences=[],
        outcome="AVAILABLE_AT_RETAINED_CUT",
        reason="SOURCE_AVAILABLE",
    )
    return rehash(source)
