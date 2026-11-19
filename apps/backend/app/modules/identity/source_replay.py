"""Pure reconstruction of retained Identity sources; never current/origin admission."""

from collections import defaultdict

from app.modules.identity import source_contracts as c
from app.modules.identity import source_limits as caps
from app.modules.identity.source_native_manifest import NATIVE_SSLINFO_PINS
from app.modules.identity.source_primitives import (
    IdentityResourceError,
    canonical,
    fingerprint,
    parse,
    primitive,
    request_fingerprint,
    strict_load,
    without,
)
from app.modules.identity.source_routine_manifest import LEGACY_ROUTINE_PINS


class _WorkBudget:
    """Per-invocation semantic visits; parsing/hashing have separate byte/node caps."""

    def __init__(self):
        self.remaining = caps.WORK_STEPS

    def take(self, count):
        self.remaining -= count
        if self.remaining < 0:
            raise IdentityResourceError("Semantic work limit")


class IdentityReplayError(ValueError):
    pass


def _require(condition, reason):
    if not condition:
        raise IdentityReplayError(reason)


def _native_members(session):
    names = set(NATIVE_SSLINFO_PINS["public"])
    known_digests = {d for values in NATIVE_SSLINFO_PINS.values() for d in values.values()}
    _require(
        all(
            o.definition_fingerprint not in known_digests
            or o.kind == "FUNCTION"
            and o.schema_name in NATIVE_SSLINFO_PINS
            and NATIVE_SSLINFO_PINS[o.schema_name].get(o.object_name) == o.definition_fingerprint
            for o in session.objects
        ),
        "Substituted native descriptor",
    )
    members = [o for o in session.objects if o.kind == "FUNCTION" and o.object_name in names]
    _require(
        len(members) == 10 and {o.object_name for o in members} == names,
        "Incomplete native catalog",
    )
    namespaces = {o.schema_name for o in members}
    _require(
        len(namespaces) == 1 and next(iter(namespaces)) in NATIVE_SSLINFO_PINS, "Native namespace"
    )
    namespace = next(iter(namespaces))
    schemas = {o.object_name: o.owner_oid for o in session.objects if o.kind == "SCHEMA"}
    expected_readers = {
        "menuto_prior",
        "menuto_hierarchy",
        "menuto_nutrition",
        "menuto_nutrition_synthesis",
    }
    _require(expected_readers <= set(schemas), "Missing native ACL source owners")
    schema_rows = [o for o in session.objects if o.kind == "SCHEMA"]
    _require(len(schema_rows) == len(schemas), "Duplicate schema identity")
    native_schema = next(o for o in schema_rows if o.object_name == namespace)
    _require(
        all(
            a[2] != "CREATE" or a[0] in {native_schema.owner_oid, session.database_owner_oid}
            for a in native_schema.acl or ()
        ),
        "Unreviewed native schema CREATE",
    )
    owner = session.database_owner_oid
    for obj in members:
        acl = [(owner, owner, "EXECUTE", False)]
        if namespace == "public":
            acl.append((0, owner, "EXECUTE", False))
        if obj.object_name == "ssl_is_used":
            acl.extend((schemas[n], owner, "EXECUTE", False) for n in expected_readers)
            acl.append((session.execution_owner_oid, owner, "EXECUTE", False))
        _require(
            obj.owner_oid == owner
            and obj.definition_fingerprint == NATIVE_SSLINFO_PINS[namespace][obj.object_name]
            and obj.acl == tuple(sorted(acl)),
            "UNDETERMINED native semantics/ACL",
        )
    return {o.object_oid for o in members}


def _session(session, mode, *, budget):
    """Reconstruct actual-login safety from retained catalog primitives."""
    s = session
    budget.take(
        1 + len(s.roles) + len(s.edges) + len(s.objects) + sum(len(o.acl or ()) for o in s.objects)
    )
    roles = {r.role_oid: r for r in s.roles}
    _require(len(roles) == len(s.roles), "Duplicate role")
    _require(len({r.role_name for r in s.roles}) == len(s.roles), "Duplicate role name")
    login = roles.get(s.login_role_oid)
    owner = roles.get(s.execution_owner_oid)
    _require(login is not None and owner is not None and login.can_login, "Missing principal")
    _require(login.role_name == s.session_user and s.requested_role == "none", "Role substitution")
    _require(
        s.system_user == "scram-sha-256:" + s.session_user
        and s.authentication_method == "scram-sha-256"
        and s.tls,
        "Invalid authentication",
    )
    _require(login.valid_until is None or s.observed_at < login.valid_until, "Expired password")
    _require(
        owner.role_name == "menuto_identity_source_owner"
        and not any(
            (
                owner.can_login,
                owner.superuser,
                owner.create_role,
                owner.create_db,
                owner.replication,
                owner.bypass_rls,
            )
        ),
        "Unsafe execution owner",
    )
    _require(
        all(
            e.member_oid in roles and e.role_oid in roles and e.member_oid != owner.role_oid
            for e in s.edges
        ),
        "Incomplete role graph",
    )

    def closure(use_set):
        result = {login.role_oid}
        while True:
            budget.take(len(s.edges))
            extra = {
                e.role_oid
                for e in s.edges
                if e.member_oid in result and (e.inherit_option or use_set and e.set_option)
            }
            if extra <= result:
                return result
            result |= extra
            _require(len(result) <= caps.ROLE_FACTS, "Role closure limit")

    _require(
        len({(e.role_oid, e.member_oid, e.grantor_oid) for e in s.edges}) == len(s.edges),
        "Duplicate native role membership",
    )
    inherited, reachable = closure(False), closure(True)
    names = {roles[oid].role_name for oid in inherited}
    infrastructure = [
        r
        for r in s.roles
        if r.role_name
        in {
            "menuto_identity_source_owner",
            "menuto_identity_bootstrap",
            "menuto_identity_issuer",
            "menuto_identity_requester",
        }
    ]
    _require(
        len(infrastructure) == 4
        and all(
            not any(
                (r.can_login, r.superuser, r.create_role, r.create_db, r.replication, r.bypass_rls)
            )
            for r in infrastructure
        )
        and s.execution_owner_oid != s.database_owner_oid,
        "Unsafe infrastructure",
    )
    native_ids = _native_members(s)
    legacy = [
        o
        for o in s.objects
        if o.kind == "FUNCTION" and o.schema_name == "public" and o.object_oid not in native_ids
    ]
    expected_routines = {name: digest for name, _, digest in LEGACY_ROUTINE_PINS}
    _require(
        len(legacy) == len(expected_routines)
        and {o.object_name for o in legacy} == set(expected_routines),
        "Incomplete legacy catalog",
    )
    default_acl = (
        (0, s.database_owner_oid, "EXECUTE", False),
        (s.database_owner_oid, s.database_owner_oid, "EXECUTE", False),
    )
    for routine in legacy:
        _require(
            routine.owner_oid == s.database_owner_oid
            and routine.definition_fingerprint == expected_routines[routine.object_name]
            and routine.acl == default_acl,
            "UNDETERMINED historical routine",
        )
    _require(
        not any(
            o.kind == "FUNCTION"
            and o.schema_name == "menuto_identity_source"
            and any(a[0] == 0 for a in o.acl or ())
            for o in s.objects
        ),
        "PUBLIC protected capability",
    )
    if mode == "BOOTSTRAP":
        _require(
            (login.superuser or login.role_oid == s.database_owner_oid)
            and "menuto_identity_bootstrap" in names,
            "Not bootstrap",
        )
        return
    _require(mode in {"ISSUER", "REQUESTER"}, "Unknown role mode")
    required = "menuto_identity_" + mode.lower()
    forbidden = {
        "menuto_identity_bootstrap",
        "menuto_identity_source_owner",
        "menuto_identity_requester" if mode == "ISSUER" else "menuto_identity_issuer",
    }
    _require(required in names and not names & forbidden, "Wrong entry class")
    _require(
        s.database_owner_oid not in reachable and s.execution_owner_oid not in reachable,
        "Owner reachability",
    )
    _require(
        not any(
            any(
                (
                    roles[i].superuser,
                    roles[i].create_role,
                    roles[i].create_db,
                    roles[i].replication,
                    roles[i].bypass_rls,
                )
            )
            for i in reachable
        ),
        "Elevated role",
    )
    _require(
        not any(roles[i].role_name.startswith("pg_") for i in reachable),
        "Unreviewed predefined PostgreSQL capability",
    )
    _require(not any(e.admin_option for e in s.edges if e.member_oid in reachable), "Admin edge")
    object_keys = {(o.kind, o.object_oid, o.sub_id) for o in s.objects}
    _require(len(object_keys) == len(s.objects), "Duplicate catalog object")
    grants = inherited | {0}
    schemas = {
        o.object_name
        for o in s.objects
        if o.kind == "SCHEMA"
        and (
            o.owner_oid in inherited or any(a[0] in grants and a[2] == "USAGE" for a in o.acl or ())
        )
    }
    allowed = {
        "ISSUER": {"change_binding", "change_operation_grant"},
        "REQUESTER": {"capture_request_source"},
    }[mode]
    for obj in s.objects:
        acl = tuple(a for a in obj.acl or () if a[0] in grants)
        _require(obj.owner_oid not in reachable, "Object ownership")
        if obj.kind == "PARAMETER":
            _require(not acl, "Extra parameter capability")
        elif obj.kind == "DATABASE":
            _require(not any(a[2] == "CREATE" for a in acl), "Database CREATE")
        elif obj.kind == "SCHEMA":
            _require(not any(a[2] == "CREATE" for a in acl), "Schema CREATE")
        elif obj.kind in {"TABLE", "COLUMN", "SEQUENCE"}:
            _require(not acl, "Direct data privilege")
        elif obj.kind == "FUNCTION" and acl:
            usable = obj.schema_name in schemas
            private_grant = any(a[0] != 0 for a in acl)
            valid = (
                obj.schema_name == "menuto_identity_source"
                and obj.object_name in allowed
                or obj.schema_name == "public"
                and obj.object_name in expected_routines
                or obj.object_oid in native_ids
            )
            _require(valid or not usable and not private_grant, "Unrelated function privilege")


def _stream(rows, kind, root_id, frame, *, budget):
    budget.take(len(rows))
    _require(0 < len(rows) <= caps.STREAM_FACTS, "Missing/long stream")
    first = rows[0]
    prior = None
    intervals = []
    immutable = None
    for number, fact in enumerate(rows, 1):
        command = fact.command
        data = primitive(command)
        _require(
            fact.stream_kind == kind == command.kind
            and fact.root_id == root_id
            and command.root_id == root_id
            and fact.stream_id == first.stream_id,
            "Stream identity",
        )
        stream_id = (
            root_id
            if kind == "ROOT"
            else getattr(
                command,
                {"ISSUER": "issuer_id", "BINDING": "binding_id", "OPERATION_GRANT": "grant_id"}[
                    kind
                ],
            )
        )
        _require(fact.stream_id == stream_id and fact.revision == number, "Revision identity")
        _require(
            command.expected_revision == number - 1
            and command.predecessor_id == (prior.fact_id if prior else None),
            "Authored CAS",
        )
        _require(
            fact.previous_fact_id == (prior.fact_id if prior else None)
            and fact.previous_fact_fingerprint == (prior.fact_fingerprint if prior else None),
            "Predecessor",
        )
        _require(
            fact.recorded_at <= frame.finished_at and fact.author.observed_at == fact.recorded_at,
            "Recorded time",
        )
        _require(
            prior is None
            or (
                fact.recorded_at >= prior.recorded_at
                and fact.recorded_order > prior.recorded_order
                and prior.command.action != "REVOKE"
            ),
            "Append order/tombstone",
        )
        _require(
            fact.command_fingerprint == fingerprint("identity.command.v1", command)
            and fact.fact_fingerprint
            == fingerprint("identity.fact.v1", without(fact, "fact_fingerprint")),
            "Fact fingerprint",
        )
        identity = {
            k: v
            for k, v in data.items()
            if k
            not in {
                "action",
                "effective",
                "idempotency_key",
                "expected_revision",
                "predecessor_id",
                "evidence_id",
                "evidence_version",
                "evidence_preimage",
            }
        }
        if immutable is None:
            immutable = identity
            _require(
                command.action
                == (
                    "INITIALIZE"
                    if kind == "ROOT"
                    else "GRANT"
                    if kind == "OPERATION_GRANT"
                    else "ENROLL"
                ),
                "Initial action",
            )
        else:
            _require(
                identity == immutable and command.action in {"RENEW", "REVOKE"}, "Immutable subject"
            )
        if command.action == "REVOKE":
            _require(
                command.effective is None
                and fact.effective_start is None
                and fact.effective_end is None,
                "Revoke interval",
            )
        else:
            effective = command.effective
            _require(effective is not None, "Missing interval")
            start = fact.recorded_at if effective.mode == "IMMEDIATE" else effective.start
            _require(
                start is not None and (effective.mode == "IMMEDIATE" or start > fact.recorded_at),
                "Backdating",
            )
            _require(
                start == fact.effective_start
                and effective.end == fact.effective_end
                and start < effective.end,
                "Effective mismatch",
            )
            _require(not intervals or intervals[-1][1] <= start, "Overlapping renewal")
            intervals.append((start, effective.end))
        _session(
            fact.author, "BOOTSTRAP" if kind in {"ROOT", "ISSUER"} else "ISSUER", budget=budget
        )
        if kind in {"ROOT", "ISSUER"}:
            _require(fact.author_issuer_fact_id is None, "Unexpected author issuer")
        if kind == "ROOT":
            _require(fact.target_role is None and fact.membership_at_issue is None, "Root fields")
        elif kind in {"ISSUER", "BINDING"}:
            role = fact.target_role
            _require(
                role is not None
                and role.role_name == command.role_name
                and role.can_login
                and not any(
                    (
                        role.superuser,
                        role.create_role,
                        role.create_db,
                        role.replication,
                        role.bypass_rls,
                    )
                ),
                "Target role",
            )
            if prior:
                _require(
                    (role.role_oid, role.role_name)
                    == (first.target_role.role_oid, first.target_role.role_name),
                    "Role replacement",
                )
        prior = fact


def _known(rows, order, *, budget):
    budget.take(3 * len(rows))
    return [r for r in rows if r.recorded_order < order]


def _active(rows, at, order=9_223_372_036_854_775_808, *, budget):
    known = _known(rows, order, budget=budget)
    if any(r.command.action == "REVOKE" and r.recorded_at <= at for r in known):
        return None
    available = [
        r
        for r in known
        if r.command.action != "REVOKE" and r.effective_start <= at < r.effective_end
    ]
    _require(len(available) <= 1, "Ambiguous effective state")
    return available[0] if available else None


def _covers(rows, start, end, order, *, budget):
    known = _known(rows, order, budget=budget)
    revoke = [r.recorded_at for r in known if r.command.action == "REVOKE"]
    if revoke and (start >= min(revoke) or end > min(revoke)):
        return False
    cursor = start
    for row in known:
        if row.command.action == "REVOKE":
            continue
        a, b = row.effective_start, row.effective_end
        if a <= cursor < b:
            cursor = max(cursor, b)
            if cursor >= end:
                return True
    return False


def _require_authority(rows, fact, *, budget):
    _require(
        _active(rows, fact.recorded_at, fact.recorded_order, budget=budget) is not None,
        "Author expired",
    )
    if fact.command.action != "REVOKE":
        _require(
            _covers(
                rows, fact.effective_start, fact.effective_end, fact.recorded_order, budget=budget
            ),
            "Delegation exceeds authority",
        )


def _failure(rows, prefix, at, *, budget):
    budget.take(len(rows))
    if any(r.command.action == "REVOKE" and r.recorded_at <= at for r in rows):
        return prefix + "_REVOKED"
    return prefix + "_EXPIRED"


def _frontier(frontier, rows, *, budget):
    budget.take(1)
    _require(
        frontier.revision == len(rows)
        and frontier.fact_count == len(rows)
        and frontier.head_id == (rows[-1].fact_id if rows else None)
        and frontier.head_fingerprint == (rows[-1].fact_fingerprint if rows else None),
        "Frontier mismatch",
    )


def reconstruct_identity_source_v1(value, expected_binding):
    """Fresh derivation from primitives; any returned availability is retained-cut only."""
    budget = _WorkBudget()
    source = parse(c.IdentitySourceSnapshotV1, value)
    expected = parse(c.IdentityRequestBindingV1, expected_binding, maximum=caps.ENVELOPE_BYTES)
    _require(canonical(source.binding) == canonical(expected), "Request substitution")
    binding = source.binding
    _require(
        binding.request_preimage_fingerprint == request_fingerprint(binding.request_utf8),
        "Raw request fingerprint",
    )
    document = strict_load(binding.request_utf8, maximum=caps.REQUEST_BYTES, _context_only=True)
    _require(
        type(document) is dict
        and type(document.get("context")) is dict
        and document.get("environment") == "TEST_ONLY",
        "Request structure",
    )
    context = document["context"]
    for key in (
        "request_id",
        "request_revision",
        "household_id",
        "actor_user_id",
        "tracked_member_id",
    ):
        _require(
            type(context.get(key)) is type(primitive(getattr(binding, key)))
            and context[key] == primitive(getattr(binding, key)),
            "Request context",
        )
    horizon = context.get("horizon")
    _require(type(horizon) is dict and set(horizon) == {"start", "end"}, "Request horizon")
    _require(
        canonical(c.Horizon.model_validate(horizon)) == canonical(binding.horizon),
        "Horizon substitution",
    )
    frame = source.frame
    _require(
        frame.started_at
        <= frame.session_start.observed_at
        <= frame.session_end.observed_at
        <= frame.finished_at
        and frame.transaction_started_at <= frame.started_at
        and (frame.finished_at - frame.started_at).total_seconds() <= caps.INSPECTION_SECONDS,
        "Capture timing",
    )
    before, after = primitive(frame.session_start), primitive(frame.session_end)
    before.pop("observed_at")
    after.pop("observed_at")
    _require(before == after, "Catalog changed")
    _require(
        frame.session_start.read_only
        and frame.session_start.isolation in {"REPEATABLE_READ", "SERIALIZABLE"},
        "Capture transaction",
    )
    _session(frame.session_start, "REQUESTER", budget=budget)
    _session(frame.session_end, "REQUESTER", budget=budget)
    root = list(source.root_history)
    bound = list(source.binding_history)
    _require(root and bound, "Missing original binding")
    issuers, grants = defaultdict(list), defaultdict(list)
    for fact in source.issuer_history:
        issuers[fact.stream_id].append(fact)
    for fact in source.grant_history:
        grants[fact.stream_id].append(fact)
    if len(issuers) > caps.ISSUER_STREAMS:
        raise IdentityResourceError("Issuer limit")
    all_rows = root + list(source.issuer_history) + bound + list(source.grant_history)
    _require(
        len(all_rows) == frame.total_fact_count
        and len(all_rows) <= caps.TOTAL_FACTS
        and len({r.fact_id for r in all_rows}) == len(all_rows)
        and len({r.recorded_order for r in all_rows}) == len(all_rows),
        "Global frontier",
    )
    groups = [("ROOT", root), ("BINDING", bound)]
    groups += [("ISSUER", rows) for rows in issuers.values()]
    groups += [("OPERATION_GRANT", rows) for rows in grants.values()]
    _require(
        len({rows[0].stream_id for _, rows in groups}) == len(groups), "Cross-kind stream identity"
    )
    for kind, rows in groups:
        _stream(rows, kind, frame.root_id, frame, budget=budget)
    root_session = root[0].author
    _require(
        all(
            r.author.database_oid == root_session.database_oid
            and r.author.database_name == root_session.database_name
            and r.author.execution_owner_oid == root_session.execution_owner_oid
            for r in all_rows
        ),
        "Cross-database source",
    )
    _require(
        frame.session_start.database_oid == root_session.database_oid
        and frame.session_start.database_name == root_session.database_name
        and frame.session_start.execution_owner_oid == root_session.execution_owner_oid,
        "Captured database mismatch",
    )
    original = bound[0]
    user = original.command.user_id
    _require(
        user == binding.actor_user_id
        and original.target_role.role_oid == frame.session_start.login_role_oid
        and original.target_role.role_name == frame.session_start.session_user,
        "Principal substitution",
    )
    issuer_id = original.command.issuer_id
    _require(
        issuer_id in issuers
        and user not in {r.command.user_id for rows in issuers.values() for r in rows},
        "Issuer/requester alias",
    )
    for rows in issuers.values():
        for fact in rows:
            _require_authority(root, fact, budget=budget)
    for fact in bound + list(source.grant_history):
        _require_authority(root, fact, budget=budget)
        _require(fact.command.issuer_id == issuer_id, "Wrong enrolling issuer")
        parents = issuers[issuer_id]
        _require_authority(parents, fact, budget=budget)
        parent = _active(parents, fact.recorded_at, fact.recorded_order, budget=budget)
        _require(
            parent.fact_id == fact.author_issuer_fact_id
            and parent.target_role.role_oid == fact.author.login_role_oid
            and parent.target_role.role_name == fact.author.session_user,
            "Actual issuer",
        )
        if fact.stream_kind == "OPERATION_GRANT":
            _require(
                fact.command.binding_id == original.stream_id
                and fact.command.household_id == binding.household_id
                and fact.command.tracked_member_id == binding.tracked_member_id,
                "Foreign operation scope",
            )
            _require_authority(bound, fact, budget=budget)
            witness = fact.membership_at_issue
            _require(witness is not None and _membership(witness, binding), "Grant Membership")
    frontiers = {(f.kind, f.stream_id): f for f in frame.frontiers}
    _require(len(frontiers) == len(frame.frontiers), "Duplicate frontier")
    for kind, rows in [("ROOT", root), ("BINDING", bound)]:
        _require((kind, rows[0].stream_id) in frontiers, "Missing frontier")
        _frontier(frontiers[kind, rows[0].stream_id], rows, budget=budget)
    issuer_rows = sorted(source.issuer_history, key=lambda r: r.recorded_order)
    entries = [
        [str(key), len(rows), str(rows[-1].fact_id), rows[-1].fact_fingerprint, len(rows)]
        for key, rows in sorted(issuers.items(), key=lambda pair: str(pair[0]))
    ]
    directory = frontiers.get(("ISSUER_DIRECTORY", frame.root_id))
    _require(
        directory is not None
        and primitive(directory.directory_entries) == entries
        and directory.directory_fingerprint
        == fingerprint("identity.source.v1", {"issuer_directory": entries}),
        "Issuer directory",
    )
    _frontier(directory, issuer_rows, budget=budget)
    for stream, rows in grants.items():
        _require(("OPERATION_GRANT", stream) in frontiers, "Missing grant frontier")
        _frontier(frontiers["OPERATION_GRANT", stream], rows, budget=budget)
    expected_keys = {
        ("ROOT", frame.root_id),
        ("ISSUER_DIRECTORY", frame.root_id),
        ("BINDING", original.stream_id),
    }
    expected_keys |= {("OPERATION_GRANT", stream) for stream in grants}
    if not grants:
        expected_keys.add(("OPERATION_GRANT", binding.tracked_member_id))
        _require(
            ("OPERATION_GRANT", binding.tracked_member_id) in frontiers,
            "Missing zero grant frontier",
        )
        _frontier(frontiers["OPERATION_GRANT", binding.tracked_member_id], [], budget=budget)
    _require(
        set(frontiers) == expected_keys
        and all(f.root_id == frame.root_id for f in frame.frontiers),
        "Foreign frontier",
    )
    expected_absences = []
    if not grants:
        expected_absences.append(["OPERATION_GRANT", str(binding.tracked_member_id)])
    if source.membership is not None and source.membership.membership_id is None:
        expected_absences.append(["MEMBERSHIP", str(binding.actor_user_id)])
    _require(primitive(source.absences) == sorted(expected_absences), "Absence completeness")
    for frontier in frame.frontiers:
        if frontier.kind != "ISSUER_DIRECTORY":
            _require(
                not frontier.directory_entries and frontier.directory_fingerprint is None,
                "Unexpected directory claim",
            )

    def protected(session):
        return sorted(
            (o.object_oid, o.object_name, o.definition_fingerprint)
            for o in session.objects
            if o.kind == "FUNCTION"
            and (
                o.schema_name in {"menuto_identity_source", "public"}
                or o.object_name in NATIVE_SSLINFO_PINS["public"]
            )
        )

    baseline_functions = protected(root_session)
    _require(
        baseline_functions
        and all(protected(r.author) == baseline_functions for r in all_rows)
        and protected(frame.session_start) == baseline_functions
        and protected(frame.session_end) == baseline_functions,
        "Source function changed",
    )
    at = frame.session_end.observed_at
    reason = "SOURCE_AVAILABLE"
    for rows, prefix in [(root, "ROOT"), (issuers[issuer_id], "ISSUER"), (bound, "BINDING")]:
        if _active(rows, at, budget=budget) is None:
            reason = _failure(rows, prefix, at, budget=budget)
            break
    active_grants = [
        row for rows in grants.values() if (row := _active(rows, at, budget=budget)) is not None
    ]
    _require(len(active_grants) <= 1, "Ambiguous grant")
    if reason == "SOURCE_AVAILABLE":
        if not active_grants:
            reason = (
                "GRANT_REVOKED"
                if any(r.command.action == "REVOKE" for r in source.grant_history)
                else "GRANT_EXPIRED"
                if grants
                else "GRANT_ABSENT"
            )
        else:
            witness = source.membership
            issued = active_grants[0].membership_at_issue
            if (
                witness is None
                or not _membership(witness, binding)
                or any(
                    getattr(witness, key) != getattr(issued, key)
                    for key in ("membership_id", "actor_member_id", "role")
                )
            ):
                reason = "AUTHORIZATION_DENIED"
    if reason != "SOURCE_AVAILABLE" and source.membership is not None:
        _require(
            all(
                getattr(source.membership, key) is None
                for key in (
                    "target_member_id",
                    "target_member_household_id",
                    "target_member_exists",
                )
            ),
            "Negative privacy leak",
        )
    data = primitive(source)
    data["outcome"] = "AVAILABLE_AT_RETAINED_CUT" if reason == "SOURCE_AVAILABLE" else "UNAVAILABLE"
    data["reason"] = reason
    data["source_fingerprint"] = fingerprint(
        "identity.source.v1", {k: v for k, v in data.items() if k != "source_fingerprint"}
    )
    return parse(c.IdentitySourceSnapshotV1, data)


def _membership(witness, request):
    return (
        witness.user_exists
        and witness.user_id == request.actor_user_id
        and witness.household_id == request.household_id
        and witness.membership_id is not None
        and witness.membership_user_id == request.actor_user_id
        and witness.membership_household_id == request.household_id
        and witness.actor_member_id is not None
        and witness.role in {"OWNER", "EDITOR"}
        and witness.actor_member_household_id == request.household_id
        and witness.target_member_id == request.tracked_member_id
        and witness.target_member_household_id == request.household_id
        and witness.target_member_exists is True
    )


def validate_identity_source_v1(value, expected_binding):
    original = parse(c.IdentitySourceSnapshotV1, value)
    reconstructed = reconstruct_identity_source_v1(original, expected_binding)
    _require(canonical(original) == canonical(reconstructed), "Source claim mismatch")
    return reconstructed
