"""Pure retained Nutrition source replay. No live authorization or scientific certification."""

from fractions import Fraction

from app.domain.feature_identity import canonical, canonical_bytes
from app.modules.nutrition import root_contracts as c
from app.modules.nutrition.root_limits import (
    CAPTURE_BYTES,
    CAPTURE_ROWS,
    HISTORY_DEPTH,
    check_structure,
)


def _fail(condition, message):
    if condition:
        raise ValueError(message)


def _hash(domain, value):
    return c.nutrition_root_hash(domain, value)


def _source_key(identity):
    return _hash("nutrition.source-stream.v1", identity)


def _authority_group(scope):
    values = canonical(scope)
    if values["member_id"] is not None:
        values.update(provider_id=None, family_id=None)
    return values


def _authority_key(scope):
    return _hash("nutrition.authority-stream.v1", _authority_group(scope))


def _scope(identity):
    return c.NutritionAuthorityScope(
        **{
            key: getattr(identity, key)
            for key in ("provider_id", "family_id", "household_id", "member_id")
        }
    )


def _member_identity(q, kind, code):
    return c.NutritionStreamIdentity(
        kind=kind,
        provider_id=q.provider_id if kind == "ASSESSMENT" else None,
        family_id=q.family_id if kind == "ASSESSMENT" else None,
        household_id=q.subject.household_id,
        member_id=q.subject.member_id,
        code=code,
    )


def _reference_identity(q):
    return c.NutritionStreamIdentity(
        kind="GUIDELINE",
        provider_id=q.provider_id,
        family_id=q.family_id,
        household_id=None,
        member_id=None,
        code="FAMILY",
    )


def _timeline(records):
    """Apply explicitly named valid-time replacements; recorded prefixes stay immutable."""
    segments = []
    for record in records:
        b = record.command.body
        lo, hi = b.effective.start, b.effective.end
        overlaps = [s for s in segments if s[0] < hi and s[1] > lo]
        identifiers = {s[2].id for s in overlaps}
        if b.operation == "CREATE":
            _fail(bool(overlaps) or bool(b.replaces), "CREATE overlaps retained state")
        else:
            _fail(
                not overlaps or set(b.replaces) != identifiers,
                "Exact replacement coverage/lineage required",
            )
            cursor = lo
            for a, z, _ in sorted(overlaps, key=lambda s: s[0]):
                _fail(a > cursor, "Replacement invents absent coverage")
                cursor = max(cursor, min(z, hi))
            _fail(cursor < hi, "Incomplete replacement coverage")
            if b.operation in {"REPLACE", "RETRACT"}:
                _fail(hi != max(s[1] for s in segments), "Old state must not resurrect")
        updated = []
        for a, z, old in segments:
            if a < hi and z > lo:
                if a < lo:
                    updated.append((a, lo, old))
                if z > hi:
                    updated.append((hi, z, old))
            else:
                updated.append((a, z, old))
        updated.append((lo, hi, record))
        segments = sorted(updated, key=lambda s: s[0])
        _fail(len(segments) > HISTORY_DEPTH, "Server effective-interval limit")
    return segments


def _cover(segments, span):
    return next((r for a, z, r in segments if a <= span.start and z >= span.end), None)


def _publication_segments(records, drafts):
    segments = []
    for record in records:
        b = record.command.body
        draft = drafts[b.draft_revision_id].command.body.guideline
        lo, hi = b.effective_at, draft.effective.end
        if b.action in {"PUBLISH", "SUPERSEDE"}:
            _fail(not draft.effective.start <= lo < hi, "Publication outside guideline interval")
        updated = []
        found = b.action == "SUPERSEDE" and any(
            old.id == b.prior_publication_id and z == lo for _, z, old, _, _ in segments
        )
        for a, z, old, active, reason in segments:
            if b.action == "PUBLISH":
                _fail(a < hi and z > lo, "Ambiguous overlapping publication")
                updated.append((a, z, old, active, reason))
            elif old.id == b.prior_publication_id and z > lo:
                found = True
                if a < lo:
                    updated.append((a, lo, old, active, reason))
                if b.action in {"RETIRE", "RETRACT"}:
                    _fail(
                        old.command.body.draft_revision_id != b.draft_revision_id,
                        "Withdrawal target differs",
                    )
                    updated.append(
                        (
                            max(a, lo),
                            z,
                            record,
                            False,
                            "SOURCE_RETIRED" if b.action == "RETIRE" else "SOURCE_RETRACTED",
                        )
                    )
                elif z > hi:
                    updated.append((hi, z, record, False, "SOURCE_OUT_OF_EFFECTIVE_RANGE"))
            else:
                _fail(
                    b.action == "SUPERSEDE" and a < hi and z > lo,
                    "Supersession truncates unrelated scheduled publication",
                )
                updated.append((a, z, old, active, reason))
        _fail(b.action != "PUBLISH" and not found, "Missing publication predecessor coverage")
        if b.action in {"PUBLISH", "SUPERSEDE"}:
            updated.append((lo, hi, record, True, None))
        segments = sorted(updated, key=lambda s: s[0])
        _fail(len(segments) > HISTORY_DEPTH, "Server publication interval limit")
    return segments


def _publication_for(segments, span):
    return next((s for s in segments if s[0] <= span.start and s[1] >= span.end), None)


def _normalize_sources(value):
    check_structure(value)
    parsed = c.NutritionRootSourceSnapshot.model_validate(canonical(value))
    data = canonical(parsed)
    data["provider_enrollments"].sort(key=lambda x: (x["command"]["provider_id"], x["generation"]))
    data["principals"].sort(key=lambda x: x["id"])
    for name in ("authority", "sources"):
        data[name].sort(key=lambda x: (x["stream_key"], x["sequence"]))
    data["streams"].sort(key=lambda x: x["stream_key"])
    data["capture"]["absence_stream_keys"].sort()
    _fail(len(canonical_bytes(data)) > CAPTURE_BYTES, "Source capture byte limit")
    _fail(
        data["source_fingerprint"]
        != _hash(
            "nutrition.sources.v1", {k: v for k, v in data.items() if k != "source_fingerprint"}
        ),
        "Full-source fingerprint mismatch",
    )
    return c.NutritionRootSourceSnapshot.model_validate(data)


def _verify_evidence_identity(value):
    seen = {}
    stack = [canonical(value)]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if "evidence_id" in item:
                key = (item["environment"], item["evidence_id"], item["version"])
                _fail(key in seen and seen[key] != item, "Conflicting immutable evidence identity")
                seen[key] = item
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)


def _principal_session(p, session):
    return (p.database_oid, p.database_name, p.role_oid, p.command.role_name) == (
        session.database_oid,
        session.database_name,
        session.role_oid,
        session.role_name,
    )


def _permission(
    authority, principal_id, scope, capability, at, *, protocol=None, fact=None, ceiling=None
):
    matches = [
        a
        for a in authority
        if a.command.principal_id == principal_id
        and a.command.scope == scope
        and a.command.capability == capability
        and a.command.protocol_fingerprint == protocol
        and a.command.fact_key == fact
        and a.command.effective.start <= at
        and (ceiling is None or a.sequence <= ceiling)
    ]
    if not matches:
        return None
    head = max(matches, key=lambda a: a.sequence)
    return head if head.command.action == "GRANT" and at < head.command.effective.end else None


def _required_capability(record):
    b = record.command.body
    if b.kind in {"DRAFT", "REVIEW"}:
        return "GUIDELINE_REVIEW", None, None
    if b.kind == "PUBLICATION":
        return (
            ("GUIDELINE_PUBLISH" if b.action in {"PUBLISH", "SUPERSEDE"} else "GUIDELINE_WITHDRAW"),
            None,
            None,
        )
    if b.kind == "ASSESSMENT":
        return "ELIGIBILITY_ATTEST", b.protocol_fingerprint, None
    if b.kind == "OBSERVATION":
        return "MEMBER_OBSERVATION_WRITE", None, b.fact_key
    if b.kind == "DELEGATION" and b.operation_scope != "MEMBER_GOAL_WRITE":
        return (
            "MEMBER_OBSERVATION_WRITE",
            None,
            ("BODY_MASS" if b.operation_scope == "BODY_MASS_WRITE" else "HEIGHT"),
        )
    return "MEMBER_GOAL_WRITE", None, None


def _assert_frontiers(s):
    all_records = [*s.authority, *s.sources]
    _fail(len({r.id for r in all_records}) != len(all_records), "Duplicate immutable receipt ID")
    _fail(
        len({r.recorded_order for r in all_records}) != len(all_records),
        "Duplicate DB-recorded order",
    )
    manifests = {m.stream_key: m for m in s.streams}
    _fail(len(manifests) != len(s.streams), "Duplicate stream manifest")
    groups = {}
    for record in all_records:
        groups.setdefault(record.stream_key, []).append(record)
    _fail(set(groups) - set(manifests), "Source stream omitted from complete manifest")
    for key, manifest in manifests.items():
        records = sorted(groups.get(key, ()), key=lambda r: r.sequence)
        expected_key = (
            _source_key(manifest.source_identity)
            if manifest.source_identity
            else _authority_key(manifest.authority_scope)
        )
        _fail(key != expected_key, "Forged typed stream key")
        _fail(
            len(records) != manifest.revision or len(records) > HISTORY_DEPTH,
            "Incomplete source history/frontier",
        )
        previous = None
        for index, record in enumerate(records, 1):
            _fail(
                record.sequence != index
                or record.previous_hash != (previous.fact_hash if previous else None),
                "Broken contiguous journal prefix",
            )
            _fail(
                previous is not None and previous.recorded_at > record.recorded_at,
                "Recorded source clock regression",
            )
            _fail(
                previous is not None and previous.recorded_order >= record.recorded_order,
                "Recorded transaction/frontier order regressed",
            )
            expected_previous = previous.id if previous else None
            if isinstance(record, c.NutritionAuthorityFact):
                _fail(
                    manifest.authority_scope is None
                    or _authority_group(record.command.scope) != canonical(manifest.authority_scope)
                    or record.command.expected_generation != index - 1
                    or record.command.predecessor_id != expected_previous,
                    "Authority lineage/scope mismatch",
                )
                domain, command_domain = "nutrition.authority.v1", "nutrition.authority-command.v1"
            else:
                _fail(
                    manifest.source_identity != record.command.identity
                    or record.command.expected_revision != index - 1
                    or record.command.predecessor_id != expected_previous
                    or record.id != record.command.revision_id,
                    "Source lineage/identity mismatch",
                )
                domain, command_domain = "nutrition.record.v1", "nutrition.source-command.v1"
            _fail(
                record.command_hash != _hash(command_domain, record.command),
                "Command fingerprint differs",
            )
            data = canonical(record)
            _fail(
                record.fact_hash
                != _hash(domain, {k: v for k, v in data.items() if k != "fact_hash"}),
                "Immutable source fact fingerprint differs",
            )
            _fail(record.recorded_at > s.capture.completed_at, "Record outside retained cut")
            previous = record
        _fail(
            manifest.head_id != (previous.id if previous else None)
            or manifest.head_hash != (previous.fact_hash if previous else None),
            "Head/absence witness mismatch",
        )
    empty = tuple(sorted(m.stream_key for m in s.streams if m.revision == 0))
    _fail(tuple(s.capture.absence_stream_keys) != empty, "Protected absence manifest differs")
    q = s.request
    required = [
        _reference_identity(q),
        _member_identity(q, "GOAL", "ENERGY_DIRECTION"),
        _member_identity(q, "OBSERVATION", "BODY_MASS"),
        _member_identity(q, "OBSERVATION", "HEIGHT"),
        _member_identity(q, "ASSESSMENT", q.protocol_fingerprint),
    ]
    required_keys = {_source_key(i) for i in required}
    required_keys |= {
        _authority_key(_scope(_reference_identity(q))),
        _authority_key(_scope(_member_identity(q, "GOAL", "ENERGY_DIRECTION"))),
    }
    _fail(required_keys - set(manifests), "Required stream/absence witness missing")
    for manifest in s.streams:
        if manifest.source_identity is not None:
            i = manifest.source_identity
            if i.kind == "GUIDELINE":
                _fail(i != _reference_identity(q), "Foreign guideline family captured")
            else:
                _fail(
                    (i.household_id, i.member_id) != (q.subject.household_id, q.subject.member_id),
                    "Unrelated member history captured",
                )
                _fail(
                    i.kind == "ASSESSMENT"
                    and i != _member_identity(q, "ASSESSMENT", q.protocol_fingerprint),
                    "Unrequested assessment scope captured",
                )
        else:
            _fail(manifest.stream_key not in required_keys, "Unrelated authority history captured")
    return manifests, groups


def _verify_enrollments(s):
    principals = {p.id: p for p in s.principals}
    _fail(len(principals) != len(s.principals), "Duplicate principal enrollment ID")
    bindings = set()
    for p in principals.values():
        _fail(
            p.command_hash != _hash("nutrition.principal-command.v1", p.command)
            or (p.database_oid, p.database_name)
            != (p.administrator.database_oid, p.administrator.database_name),
            "Principal enrollment identity differs",
        )
        key = p.database_oid, p.role_oid, p.command.role_name
        _fail(
            key in bindings or p.recorded_at > s.capture.completed_at,
            "Duplicate/stale principal enrollment",
        )
        bindings.add(key)
    providers, by_id = {}, {}
    for p in s.provider_enrollments:
        _fail(p.id in by_id, "Duplicate provider enrollment ID")
        by_id[p.id] = p
        providers.setdefault(p.command.provider_id, []).append(p)
    for _, history in providers.items():
        previous = None
        for index, p in enumerate(sorted(history, key=lambda p: p.generation), 1):
            _fail(
                p.generation != index
                or p.command.expected_generation != index - 1
                or p.command.previous_enrollment_id != (previous.id if previous else None)
                or p.command_hash != _hash("nutrition.provider-command.v1", p.command)
                or (index == 1 and p.id != p.command.provider_id),
                "Provider enrollment prefix differs",
            )
            if previous:
                _fail(
                    (p.command.code, p.command.version, p.command.remit, p.command.environment)
                    != (
                        previous.command.code,
                        previous.command.version,
                        previous.command.remit,
                        previous.command.environment,
                    )
                    or p.recorded_at < previous.recorded_at,
                    "Immutable provider identity changed",
                )
            _fail(p.recorded_at > s.capture.completed_at, "Provider outside cut")
            previous = p
    _fail(s.request.provider_id not in providers, "Explicit provider enrollment absent")
    selected = max(providers[s.request.provider_id], key=lambda p: p.generation)
    _fail(
        selected.id != s.capture.provider_enrollment_id
        or (selected.administrator.database_oid, selected.administrator.database_name)
        != (s.capture.session.database_oid, s.capture.session.database_name)
        or selected.command.environment != s.request.environment,
        "Actual capture/provider binding or environment differs",
    )
    return principals, by_id


def _verify_member_author(record, principal, records):
    i, b, witness = record.command.identity, record.command.body, record.subject_witness
    _fail(
        witness is None
        or witness.subject.household_id != i.household_id
        or witness.subject.member_id != i.member_id
        or witness.actor_user_id != principal.command.user_id,
        "Canonical subject/actor witness differs",
    )
    if b.kind == "ASSESSMENT":
        _fail(principal.command.verified_human_id is None, "Qualified human assessor required")
        return
    is_self = (
        principal.command.user_id is not None
        and witness.membership_id is not None
        and witness.role in {"OWNER", "EDITOR"}
        and witness.actor_member_id == i.member_id
    )
    if b.kind == "DELEGATION":
        _fail(
            record.delegation_event_id is not None
            or not (
                is_self
                or (
                    principal.command.verified_human_id is not None
                    and principal.command.delegation_registrar
                )
            ),
            "Delegation issuer not subject or explicitly enrolled registrar",
        )
        return
    _fail(
        principal.command.user_id is None
        or witness.membership_id is None
        or witness.role not in {"OWNER", "EDITOR"},
        "Member author needs canonical household access",
    )
    if is_self:
        _fail(record.delegation_event_id is not None, "Self authorship cannot borrow a delegation")
        return
    operation = (
        "MEMBER_GOAL_WRITE"
        if b.kind == "GOAL"
        else "BODY_MASS_WRITE"
        if b.fact_key == "BODY_MASS"
        else "HEIGHT_WRITE"
    )
    delegated = [
        r
        for r in records
        if r.command.body.kind == "DELEGATION"
        and r.command.identity.member_id == i.member_id
        and r.command.body.grantee_principal_id == principal.id
        and r.command.body.operation_scope == operation
        and r.command.body.effective.start <= record.recorded_at
        and r.recorded_order < record.recorded_order
    ]
    head = max(delegated, key=lambda r: r.sequence) if delegated else None
    _fail(
        head is None
        or head.id != record.delegation_event_id
        or head.command.body.action != "GRANT"
        or head.command.body.effective.end <= record.recorded_at
        or not (
            head.command.body.effective.start <= b.effective.start
            and b.effective.end <= head.command.body.effective.end
        ),
        "Exact active subject/operation delegation required",
    )


def _verify_sources(s):
    _verify_evidence_identity(s)
    manifests, groups = _assert_frontiers(s)
    principals, providers = _verify_enrollments(s)
    frame, q = s.capture, s.request
    _fail(
        frame.completed_at < frame.started_at or s.current_legacy_anchor.subject != q.subject,
        "Incoherent capture interval/legacy subject",
    )
    _fail(
        frame.row_count
        != (
            len(s.provider_enrollments)
            + len(s.principals)
            + len(s.authority)
            + len(s.sources)
            + len(s.streams)
        )
        or frame.row_count > CAPTURE_ROWS,
        "Complete capture row count/limit differs",
    )
    for a in s.authority:
        p = principals.get(a.command.principal_id)
        _fail(
            p is None
            or p.recorded_at > a.recorded_at
            or (p.database_oid, p.database_name)
            != (a.administrator.database_oid, a.administrator.database_name),
            "Authority enrollment/actual database binding differs",
        )
        _fail(
            (
                a.command.capability.startswith("GUIDELINE_")
                or a.command.capability == "ELIGIBILITY_ATTEST"
            )
            and p.command.verified_human_id is None,
            "Reference/assessor grant requires verified human",
        )
        _fail(
            a.command.action == "GRANT"
            and p.command.identity_evidence.environment
            != (a.command.qualification_evidence.environment),
            "Principal/grant environment differs",
        )
    reader = principals.get(frame.reader_principal_id)
    _fail(
        reader is None or not _principal_session(reader, frame.session),
        "Actual captured reader differs from enrollment",
    )
    witness = frame.reader_subject_witness
    _fail(
        witness.subject != q.subject or witness.actor_user_id != reader.command.user_id,
        "Captured canonical reader/subject access differs",
    )
    if reader.command.user_id is not None:
        _fail(
            witness.membership_id is None or witness.role is None,
            "Human reader lacks canonical household access",
        )
    else:
        _fail(reader.command.service_id is None, "Explicit source reader service binding required")
    read_scope = c.NutritionAuthorityScope(
        provider_id=q.provider_id,
        family_id=q.family_id,
        household_id=q.subject.household_id,
        member_id=q.subject.member_id,
    )
    cap = "ROOT_SOURCE_READ" if q.purpose == "ROOT" else "VALIDATOR_SOURCE_READ"
    for at in (frame.started_at, frame.completed_at):
        grant = _permission(s.authority, reader.id, read_scope, cap, at)
        _fail(
            grant is None or grant.id != frame.reader_grant_id,
            "Captured read authority unavailable",
        )
    sources = {r.id: r for r in s.sources}
    for record in s.sources:
        p = principals.get(record.principal_id)
        _fail(
            p is None
            or not _principal_session(p, record.author)
            or p.recorded_at > record.recorded_at,
            "Canonical authenticated source author differs",
        )
        cap, protocol, fact = _required_capability(record)
        sc = _scope(record.command.identity)
        group_key = _authority_key(sc)
        earlier = [
            a.sequence
            for a in s.authority
            if a.stream_key == group_key and a.recorded_order < record.recorded_order
        ]
        _fail(
            record.authority_generation != max(earlier, default=0),
            "Recorded authorization generation differs from serialized history",
        )
        grant = _permission(
            s.authority,
            p.id,
            sc,
            cap,
            record.recorded_at,
            protocol=protocol,
            fact=fact,
            ceiling=record.authority_generation,
        )
        _fail(
            grant is None or grant.id != record.grant_event_id,
            "Exact capability must precede source receipt",
        )
        if record.command.identity.provider_id is not None:
            provider = providers.get(record.provider_enrollment_id)
            _fail(
                provider is None
                or provider.command.provider_id != sc.provider_id
                or (provider.administrator.database_oid, provider.administrator.database_name)
                != (record.author.database_oid, record.author.database_name),
                "Actual provider enrollment/author database differs",
            )
        else:
            _fail(
                record.provider_enrollment_id is not None,
                "Member truth cannot borrow provider authority",
            )
        if record.command.identity.kind == "GUIDELINE":
            _fail(
                p.command.verified_human_id is None
                or record.subject_witness is not None
                or record.delegation_event_id is not None
                or record.legacy_anchor is not None,
                "Global reference authority is not member authorship",
            )
        else:
            _verify_member_author(record, p, s.sources)
        b = record.command.body
        _fail(
            p.command.identity_evidence.environment != q.environment,
            "Captured source environment mismatch",
        )
        if b.kind in {"OBSERVATION", "GOAL"}:
            _fail(
                b.provenance.environment != p.command.identity_evidence.environment,
                "Member provenance environment mismatch",
            )
        if b.kind == "DELEGATION":
            _fail(
                b.authorization_evidence.environment != p.command.identity_evidence.environment,
                "Delegation evidence environment mismatch",
            )
        if b.kind == "OBSERVATION":
            _fail(b.observed_at > record.recorded_at, "Observation is not yet measured")
        if b.kind == "DELEGATION":
            grantee = principals.get(b.grantee_principal_id)
            _fail(
                grantee is None
                or grantee.command.verified_human_id is None
                or grantee.command.user_id is None,
                "Delegation cannot mint service authorship",
            )
            if b.action == "REVOKE":
                old = sources.get(b.previous_grant_id)
                _fail(
                    old is None
                    or old.command.body.kind != "DELEGATION"
                    or old.command.body.action != "GRANT"
                    or old.command.identity != record.command.identity
                    or old.recorded_order >= record.recorded_order,
                    "Delegation revoke exact grant lineage differs",
                )
        if b.kind in {"OBSERVATION", "ASSESSMENT"}:
            _fail(
                record.legacy_anchor is None
                or record.legacy_anchor.subject != record.subject_witness.subject,
                "Observation/assessment requires full canonical legacy anchor",
            )
            profile = record.legacy_anchor.profile
            legacy = (
                None
                if profile is None or b.kind != "OBSERVATION"
                else (profile.body_mass_kg if b.fact_key == "BODY_MASS" else profile.height_cm)
            )
            if legacy is not None and b.kind == "OBSERVATION" and b.value is not None:
                _fail(
                    Fraction(legacy) != Fraction(b.value.numerator, b.value.denominator),
                    "Explicit legacy reconciliation and new attestation required",
                )
        else:
            _fail(record.legacy_anchor is not None, "Legacy anchor belongs to observation source")
        if b.kind == "GOAL":
            anchor = sources.get(b.goal_id)
            _fail(
                anchor is None
                or anchor.command.body.kind != "GOAL"
                or anchor.command.body.goal_id != anchor.id
                or anchor.command.identity != record.command.identity,
                "Goal identity cannot be copied between members",
            )
    return principals, groups


def _verify_reference_history(s, principals, groups):
    q = s.request
    records = sorted(groups.get(_source_key(_reference_identity(q)), ()), key=lambda r: r.sequence)
    drafts, reviews, publications, protocol_versions = {}, {}, [], {}
    provider = next(p for p in s.provider_enrollments if p.id == s.capture.provider_enrollment_id)
    for record in records:
        b = record.command.body
        if b.kind == "DRAFT":
            body = b.guideline
            _fail(
                body.environment != provider.command.environment,
                "Guideline/provider environment differs",
            )
            key = body.protocol.protocol_id, body.protocol.version
            ph = _hash("nutrition.protocol.v1", body.protocol)
            _fail(
                key in protocol_versions and protocol_versions[key] != ph,
                "Conflicting immutable protocol identity/version",
            )
            protocol_versions[key] = ph
            drafts[record.id] = record
        elif b.kind == "REVIEW":
            draft = drafts.get(b.draft_revision_id)
            _fail(draft is None, "Review references unavailable draft")
            body = draft.command.body.guideline
            _fail(
                b.body_fingerprint != _hash("nutrition.guideline-body.v1", body)
                or b.evidence_fingerprint
                != _hash("nutrition.evidence-manifest.v1", body.evidence_manifest)
                or b.protocol_fingerprint != _hash("nutrition.protocol.v1", body.protocol),
                "Review does not bind complete body/evidence/protocol",
            )
            if b.decision == "CANCEL":
                old = reviews.get(b.prior_review_id)
                _fail(
                    old is None
                    or old.command.body.decision != "APPROVE"
                    or old.command.body.draft_revision_id != b.draft_revision_id
                    or principals[old.principal_id].command.verified_human_id
                    != (principals[record.principal_id].command.verified_human_id)
                    or any(r.command.body.prior_review_id == old.id for r in reviews.values()),
                    "Review cancellation identity/authority differs",
                )
            reviews[record.id] = record
        elif b.kind == "PUBLICATION":
            draft = drafts.get(b.draft_revision_id)
            _fail(
                draft is None
                or b.body_fingerprint
                != _hash(
                    "nutrition.guideline-body.v1", draft.command.body.guideline if draft else None
                ),
                "Publication exact draft identity differs",
            )
            if b.action in {"PUBLISH", "SUPERSEDE"}:
                review = reviews.get(b.review_event_id)
                _fail(
                    review is None
                    or review.command.body.decision != "APPROVE"
                    or review.command.body.draft_revision_id != b.draft_revision_id
                    or any(r.command.body.prior_review_id == review.id for r in reviews.values()),
                    "Publication requires a complete active review",
                )
                grant = _permission(
                    s.authority,
                    review.principal_id,
                    _scope(record.command.identity),
                    "GUIDELINE_REVIEW",
                    record.recorded_at,
                    ceiling=record.authority_generation,
                )
                _fail(
                    grant is None or grant.id != review.grant_event_id,
                    "Reviewer authority changed before publication",
                )
                _fail(
                    principals[review.principal_id].command.verified_human_id
                    == (principals[record.principal_id].command.verified_human_id),
                    "Different logins do not establish different verified humans",
                )
            if b.prior_publication_id is not None:
                previous = next((r for r in publications if r.id == b.prior_publication_id), None)
                _fail(previous is None, "Explicit prior publication not retained")
                if b.action in {"RETIRE", "RETRACT"}:
                    _fail(
                        previous.command.body.draft_revision_id != b.draft_revision_id,
                        "Withdrawal exact revision differs",
                    )
            publications.append(record)
        else:
            raise ValueError("Unexpected reference-source kind")
    return drafts, _publication_segments(publications, drafts)


def _verify_assessments(s, groups, drafts, pub_segments):
    q = s.request
    assessment_records = groups.get(
        _source_key(_member_identity(q, "ASSESSMENT", q.protocol_fingerprint)), ()
    )
    observations = {r.id: r for r in s.sources if r.command.body.kind == "OBSERVATION"}
    for record in assessment_records:
        b = record.command.body
        draft = drafts.get(b.guideline_revision_id)
        _fail(
            draft is None
            or b.guideline_body_fingerprint
            != _hash(
                "nutrition.guideline-body.v1", draft.command.body.guideline if draft else None
            ),
            "Assessment guideline identity differs",
        )
        protocol = draft.command.body.guideline.protocol
        _fail(
            b.protocol_fingerprint != _hash("nutrition.protocol.v1", protocol),
            "Assessment exact reviewed protocol differs",
        )
        if b.operation == "RETRACT":
            _fail(b.outcome != "UNDETERMINED", "Assessment tombstone is not SUPPORTED")
            continue
        grant = next(a for a in s.authority if a.id == record.grant_event_id)
        _fail(
            not (
                grant.command.effective.start <= b.effective.start
                and b.effective.end <= grant.command.effective.end
            ),
            "Assessment outside exact assessor qualification interval",
        )
        # Publication/observation validity at assertion time is replayed against its
        # recorded prefix; later source changes only invalidate fresh use, not history.
        prior_refs = [r for r in s.sources if r.recorded_order < record.recorded_order]
        prior_drafts = {r.id: r for r in prior_refs if r.command.body.kind == "DRAFT"}
        prior_pubs = sorted(
            (r for r in prior_refs if r.command.body.kind == "PUBLICATION"),
            key=lambda r: r.sequence,
        )
        then = _publication_for(_publication_segments(prior_pubs, prior_drafts), b.effective)
        _fail(
            then is None
            or not then[3]
            or then[2].command.body.draft_revision_id != b.guideline_revision_id,
            "Assessment not bound to applicable published protocol",
        )
        for ref in b.observations:
            obs = observations.get(ref.revision_id)
            _fail(
                obs is None
                or obs.recorded_order >= record.recorded_order
                or obs.fact_hash != ref.fact_hash
                or obs.command.body.fact_key != ref.fact_key
                or obs.command.body.value != ref.value
                or obs.command.body.unit != ref.unit
                or obs.legacy_anchor.body_fingerprint != ref.legacy_anchor_fingerprint
                or obs.legacy_anchor != record.legacy_anchor,
                "Assessment observation identity/value/anchor differs",
            )
            history = sorted(
                (r for r in prior_refs if r.command.identity == obs.command.identity),
                key=lambda r: r.sequence,
            )
            current = _cover(_timeline(history), b.effective)
            _fail(
                current is None
                or current.id != obs.id
                or current.command.body.operation == "RETRACT",
                "Assessment observation prefix/interval stale",
            )
        all_requirements = (protocol.admitted, protocol.excluded, protocol.out_of_scope)
        all_facts = {f for req in all_requirements for f in req.observations}
        all_slots = {e for req in all_requirements for e in req.evidence_slots}
        facts, slots = {r.fact_key for r in b.observations}, {e.evidence_id for e in b.evidence}
        _fail(
            facts - all_facts
            or slots - all_slots
            or set(b.missing_observations) != all_facts - facts
            or set(b.missing_evidence_slots) != all_slots - slots,
            "Assessment evidence completeness manifest differs",
        )
        _fail(
            any(e.environment != draft.command.body.guideline.environment for e in b.evidence),
            "Assessment evidence environment differs",
        )
        own = {
            "ADMITTED": protocol.admitted,
            "EXCLUDED": protocol.excluded,
            "OUT_OF_SCOPE": protocol.out_of_scope,
        }.get(b.outcome)
        if own:
            _fail(
                set(own.observations) - facts or set(own.evidence_slots) - slots,
                "Outcome-specific assessment proof incomplete",
            )


def resolve_nutrition_root(value):
    s = _normalize_sources(value)
    principals, groups = _verify_sources(s)
    drafts, pub_segments = _verify_reference_history(s, principals, groups)
    _verify_assessments(s, groups, drafts, pub_segments)
    q, reasons, roots = s.request, set(), ()
    span = q.temporal.interval
    selected = _publication_for(pub_segments, span)
    draft = drafts.get(q.guideline_revision_id)
    if draft is None:
        reasons.add("GUIDELINE_UNAVAILABLE")
    elif selected is None:
        reasons.add("SOURCE_OUT_OF_EFFECTIVE_RANGE" if pub_segments else "GUIDELINE_UNAVAILABLE")
    elif not selected[3]:
        reasons.add(selected[4])
    elif selected[2].command.body.draft_revision_id != q.guideline_revision_id:
        reasons.add("GUIDELINE_NOT_APPLICABLE")
    if draft is not None:
        body = draft.command.body.guideline
        if _hash("nutrition.guideline-body.v1", body) != q.guideline_body_fingerprint:
            reasons.add("VERSION_MISMATCH")
        if (
            _hash("nutrition.protocol.v1", body.protocol),
            body.protocol.scope_id,
            body.protocol.scope_version,
            body.environment,
        ) != (q.protocol_fingerprint, q.scope_id, q.scope_version, q.environment):
            reasons.add("GUIDELINE_NOT_APPLICABLE")
        if any(clause.descriptor.temporal != q.temporal for clause in body.clauses):
            reasons.add("TEMPORAL_SCOPE_MISMATCH")
    goal_history = sorted(
        groups.get(_source_key(_member_identity(q, "GOAL", "ENERGY_DIRECTION")), ()),
        key=lambda r: r.sequence,
    )
    goal_segments = _timeline(goal_history)
    goal = _cover(goal_segments, span)
    if goal is None:
        overlapping = any(a < span.end and z > span.start for a, z, _ in goal_segments)
        goal_state = "AMBIGUOUS" if overlapping else "ABSENT"
        reasons.add("GOAL_AMBIGUOUS" if overlapping else "GOAL_ABSENT")
    elif goal.command.body.operation == "RETRACT":
        goal_state = "RETRACTED"
        reasons.add("GOAL_RETRACTED")
    else:
        goal_state = "PRESENT"
    ah = sorted(
        groups.get(_source_key(_member_identity(q, "ASSESSMENT", q.protocol_fingerprint)), ()),
        key=lambda r: r.sequence,
    )
    assessment = _cover(_timeline(ah), span)
    eligibility = "UNKNOWN"
    if assessment is None or assessment.command.body.operation == "RETRACT":
        reasons.add("ELIGIBILITY_UNKNOWN")
    else:
        b = assessment.command.body
        stale = assessment.legacy_anchor.body_fingerprint != (
            s.current_legacy_anchor.body_fingerprint
        )
        for ref in b.observations:
            history = sorted(
                groups.get(_source_key(_member_identity(q, "OBSERVATION", ref.fact_key)), ()),
                key=lambda r: r.sequence,
            )
            observation = _cover(_timeline(history), span)
            if (
                observation is None
                or observation.id != ref.revision_id
                or observation.command.body.operation == "RETRACT"
                or observation.legacy_anchor.body_fingerprint
                != (s.current_legacy_anchor.body_fingerprint)
            ):
                stale = True
        if b.missing_observations:
            reasons.add("PHYSIOLOGICAL_INPUT_MISSING")
        if b.missing_evidence_slots:
            reasons.add("INSUFFICIENT_EVIDENCE")
        if (
            b.guideline_revision_id != q.guideline_revision_id
            or b.guideline_body_fingerprint != q.guideline_body_fingerprint
            or b.protocol_fingerprint != q.protocol_fingerprint
        ):
            reasons.add("VERSION_MISMATCH")
            stale = True
        if stale:
            reasons.add("PHYSIOLOGICAL_SOURCE_CHANGED")
        else:
            eligibility = {
                "ADMITTED": "SUPPORTED",
                "OUT_OF_SCOPE": "UNSUPPORTED",
                "EXCLUDED": "INELIGIBLE",
                "UNDETERMINED": "UNKNOWN",
            }[b.outcome]
            if eligibility == "SUPPORTED" and (b.missing_observations or b.missing_evidence_slots):
                eligibility = "UNKNOWN"
        if eligibility != "SUPPORTED":
            reasons.add(
                {
                    "UNKNOWN": "ELIGIBILITY_UNKNOWN",
                    "UNSUPPORTED": "MEMBER_UNSUPPORTED",
                    "INELIGIBLE": "MEMBER_INELIGIBLE",
                }[eligibility]
            )
    # Unrelated missing admission slots remain diagnostics beside proven negative
    # assessment evidence. They never turn a negative result into SUPPORTED.
    if eligibility == "SUPPORTED" and goal_state == "PRESENT" and not reasons:
        roots = tuple(
            c.NutritionResolvedRoot(
                publication_event_id=selected[2].id,
                guideline_revision_id=q.guideline_revision_id,
                guideline_body_fingerprint=q.guideline_body_fingerprint,
                clause=clause,
            )
            for clause in draft.command.body.guideline.clauses
        )
    data = dict(
        sources=s,
        availability="AVAILABLE" if roots else "UNAVAILABLE",
        eligibility=eligibility,
        goal_state=goal_state,
        goal_revision_id=goal.id if goal_state == "PRESENT" else None,
        goal_direction=goal.command.body.direction if goal_state == "PRESENT" else None,
        roots=roots,
        reasons=tuple(sorted(reasons)),
        source_fingerprint=s.source_fingerprint,
        result_fingerprint="0" * 64,
    )
    provisional = c.NutritionRootContract(**data)
    payload = canonical(provisional)
    payload.pop("result_fingerprint")
    return c.NutritionRootContract(
        **dict(data, result_fingerprint=_hash("nutrition.root-result.v1", payload))
    )


def validate_nutrition_root(value):
    check_structure(value)
    parsed = c.NutritionRootContract.model_validate(canonical(value))
    expected = resolve_nutrition_root(parsed.sources)
    _fail(canonical(parsed) != canonical(expected), "Nutrition root semantic recomputation differs")
    return expected
