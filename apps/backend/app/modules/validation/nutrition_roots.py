"""Independent Nutrition source/containment checking, never a full-plan validator.

This implementation reconstructs valid-time state on a boundary grid. It does not
import the producer's interval reducer, source resolver or semantic validator.
"""

from fractions import Fraction

from app.domain.feature_identity import canonical, canonical_bytes
from app.modules.nutrition import root_contracts as n


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _digest(domain, body):
    return n.nutrition_root_hash(domain, body)


def _scope_of(identity):
    return n.NutritionAuthorityScope(
        provider_id=identity.provider_id,
        family_id=identity.family_id,
        household_id=identity.household_id,
        member_id=identity.member_id,
    )


def _scope_group(scope):
    value = canonical(scope)
    if value["member_id"] is not None:
        value["provider_id"] = value["family_id"] = None
    return value


def _authority_stream(scope):
    return _digest("nutrition.authority-stream.v1", _scope_group(scope))


def _source_stream(identity):
    return _digest("nutrition.source-stream.v1", identity)


def _identity(request, kind, code):
    member = kind != "GUIDELINE"
    reference = kind in {"GUIDELINE", "ASSESSMENT"}
    return n.NutritionStreamIdentity(
        kind=kind,
        provider_id=request.provider_id if reference else None,
        family_id=request.family_id if reference else None,
        household_id=request.subject.household_id if member else None,
        member_id=request.subject.member_id if member else None,
        code=code,
    )


def _grid(records):
    boundaries = sorted(
        {t for r in records for t in (r.command.body.effective.start, r.command.body.effective.end)}
    )
    cells = [(a, z, None) for a, z in zip(boundaries, boundaries[1:])]
    for record in records:
        body = record.command.body
        lo, hi = body.effective.start, body.effective.end
        selected = [i for i, (a, z, _) in enumerate(cells) if a >= lo and z <= hi]
        previous = [cells[i][2] for i in selected]
        present = {r.id for r in previous if r is not None}
        if body.operation == "CREATE":
            _require(not present and not body.replaces, "Overlapping creation")
        else:
            _require(
                bool(selected)
                and all(r is not None for r in previous)
                and present == set(body.replaces),
                "Replacement proof/coverage differs",
            )
            if body.operation in {"REPLACE", "RETRACT"}:
                end = max(z for _, z, r in cells if r is not None)
                _require(hi == end, "Retraction/replacement resurrects old state")
        for i in selected:
            a, z, _ = cells[i]
            cells[i] = (a, z, record)
    return cells


def _whole(cells, span):
    relevant = [(a, z, r) for a, z, r in cells if a < span.end and z > span.start]
    if not relevant or relevant[0][0] > span.start or relevant[-1][1] < span.end:
        return None
    selected = {r.id for _, _, r in relevant if r is not None}
    if len(selected) != 1 or any(r is None for _, _, r in relevant):
        return None
    return relevant[0][2]


def _publication_grid(publications, drafts):
    if not publications:
        return []
    boundaries = {r.command.body.effective_at for r in publications}
    boundaries |= {
        t
        for r in publications
        for t in (
            drafts[r.command.body.draft_revision_id].command.body.guideline.effective.start,
            drafts[r.command.body.draft_revision_id].command.body.guideline.effective.end,
        )
    }
    points = sorted(boundaries)
    cells = [(a, z, None) for a, z in zip(points, points[1:])]
    for record in publications:
        body = record.command.body
        source = drafts[body.draft_revision_id].command.body.guideline
        lo, hi = body.effective_at, source.effective.end
        if body.action in {"PUBLISH", "SUPERSEDE"}:
            _require(source.effective.start <= lo < hi, "Publication interval mismatch")
        targeted = [
            i
            for i, (a, z, state) in enumerate(cells)
            if state is not None and state[0].id == body.prior_publication_id and z > lo
        ]
        if body.action != "PUBLISH":
            adjacent = body.action == "SUPERSEDE" and any(
                state is not None and state[0].id == body.prior_publication_id and z == lo
                for _, z, state in cells
            )
            _require(bool(targeted) or adjacent, "Explicit publication predecessor unavailable")
        for index, (a, z, state) in enumerate(cells):
            in_new = a >= lo and z <= hi
            if body.action == "PUBLISH":
                _require(not in_new or state is None, "Conflicting publication")
                if in_new:
                    cells[index] = (a, z, (record, True, None))
            elif index in targeted:
                if body.action in {"RETIRE", "RETRACT"}:
                    _require(
                        state[0].command.body.draft_revision_id == body.draft_revision_id,
                        "Wrong publication withdrawn",
                    )
                    cells[index] = (
                        a,
                        z,
                        (
                            record,
                            False,
                            "SOURCE_RETIRED" if body.action == "RETIRE" else "SOURCE_RETRACTED",
                        ),
                    )
                elif in_new:
                    cells[index] = (a, z, (record, True, None))
                elif a >= hi:
                    cells[index] = (a, z, (record, False, "SOURCE_OUT_OF_EFFECTIVE_RANGE"))
            elif body.action == "SUPERSEDE" and in_new:
                _require(state is None, "Supersession truncates another scheduled publication")
                cells[index] = (a, z, (record, True, None))
    return cells


def _published_whole(cells, span):
    selected = [(a, z, state) for a, z, state in cells if a < span.end and z > span.start]
    if (
        not selected
        or selected[0][0] > span.start
        or selected[-1][1] < span.end
        or any(state is None for _, _, state in selected)
    ):
        return None
    states = {state[0].id for _, _, state in selected}
    return selected[0][2] if len(states) == 1 else None


def _grant(s, principal, scope, cap, at, *, protocol=None, fact=None, before=None):
    admitted = [
        a
        for a in s.authority
        if a.command.principal_id == principal
        and a.command.scope == scope
        and a.command.capability == cap
        and a.command.protocol_fingerprint == protocol
        and a.command.fact_key == fact
        and a.command.effective.start <= at
        and (before is None or a.recorded_order < before)
    ]
    if not admitted:
        return None
    last = max(admitted, key=lambda a: a.recorded_order)
    return last if last.command.action == "GRANT" and last.command.effective.end > at else None


def _canonical_sources(value):
    s = n.NutritionRootSourceSnapshot.model_validate(canonical(value))
    body = canonical(s)
    body["provider_enrollments"].sort(key=lambda p: (p["command"]["provider_id"], p["generation"]))
    body["principals"].sort(key=lambda p: p["id"])
    body["authority"].sort(key=lambda a: (a["stream_key"], a["sequence"]))
    body["sources"].sort(key=lambda a: (a["stream_key"], a["sequence"]))
    body["streams"].sort(key=lambda a: a["stream_key"])
    body["capture"]["absence_stream_keys"].sort()
    supplied = body.pop("source_fingerprint")
    _require(supplied == _digest("nutrition.sources.v1", body), "Whole-source fingerprint differs")
    _require(len(canonical_bytes(body)) <= 4194304, "Capture absolute byte limit")
    return n.NutritionRootSourceSnapshot(**dict(body, source_fingerprint=supplied))


def _audit(s):
    q = s.request
    principals = {p.id: p for p in s.principals}
    _require(len(principals) == len(s.principals), "Principal immutable identity collision")
    role_bindings = set()
    for p in principals.values():
        _require(
            p.command_hash == _digest("nutrition.principal-command.v1", p.command)
            and (p.database_oid, p.database_name)
            == (p.administrator.database_oid, p.administrator.database_name),
            "Principal enrollment source identity differs",
        )
        binding = p.database_oid, p.role_oid, p.command.role_name
        _require(
            binding not in role_bindings and p.recorded_at <= s.capture.completed_at,
            "Duplicate/out-of-cut principal binding",
        )
        role_bindings.add(binding)
    providers = {}
    provider_ids = set()
    for p in s.provider_enrollments:
        _require(p.id not in provider_ids, "Provider immutable ID collision")
        provider_ids.add(p.id)
        providers.setdefault(p.command.provider_id, []).append(p)
    for history in providers.values():
        previous = None
        for index, p in enumerate(sorted(history, key=lambda p: p.generation), 1):
            _require(
                p.command_hash == _digest("nutrition.provider-command.v1", p.command)
                and p.generation == index
                and p.command.expected_generation == index - 1
                and p.command.previous_enrollment_id == (previous.id if previous else None)
                and p.recorded_at <= s.capture.completed_at,
                "Provider enrollment prefix differs",
            )
            if previous is None:
                _require(p.id == p.command.provider_id, "Provider initial identity differs")
            else:
                a, b = previous.command, p.command
                _require(
                    (a.code, a.version, a.remit, a.environment)
                    == (b.code, b.version, b.remit, b.environment)
                    and previous.recorded_at <= p.recorded_at,
                    "Provider identity changed",
                )
            previous = p
    _require(q.provider_id in providers, "Requested provider absent")
    selected_provider = max(providers[q.provider_id], key=lambda p: p.generation)
    _require(
        selected_provider.id == s.capture.provider_enrollment_id
        and selected_provider.command.environment == q.environment
        and (
            selected_provider.administrator.database_oid,
            selected_provider.administrator.database_name,
        )
        == (s.capture.session.database_oid, s.capture.session.database_name),
        "Actual provider/capture binding differs",
    )
    evidence = {}
    pending = [canonical(s)]
    while pending:
        v = pending.pop()
        if isinstance(v, dict):
            if "evidence_id" in v:
                key = v["environment"], v["evidence_id"], v["version"]
                _require(
                    key not in evidence or evidence[key] == v, "Immutable evidence ID conflict"
                )
                evidence[key] = v
            pending.extend(v.values())
        elif isinstance(v, list):
            pending.extend(v)
    records = [*s.authority, *s.sources]
    _require(
        len({r.id for r in records}) == len(records)
        and len({r.recorded_order for r in records}) == len(records),
        "Receipt ID/order collision",
    )
    manifests = {m.stream_key: m for m in s.streams}
    _require(len(manifests) == len(s.streams), "Duplicate manifest")
    by_stream = {}
    for r in records:
        by_stream.setdefault(r.stream_key, []).append(r)
    _require(set(by_stream) <= set(manifests), "Omitted source stream")
    for key, m in manifests.items():
        actual = (
            _source_stream(m.source_identity)
            if m.source_identity
            else _authority_stream(m.authority_scope)
        )
        _require(key == actual, "Forged stream identity")
        history = sorted(by_stream.get(key, ()), key=lambda r: r.sequence)
        _require(len(history) == m.revision and len(history) <= 64, "Incomplete retained frontier")
        previous = None
        for index, r in enumerate(history, 1):
            _require(
                r.sequence == index
                and r.previous_hash == (previous.fact_hash if previous else None)
                and r.recorded_at <= s.capture.completed_at,
                "Journal prefix/knowledge cut differs",
            )
            if previous:
                _require(
                    previous.recorded_order < r.recorded_order
                    and previous.recorded_at <= r.recorded_at,
                    "Recorded order regressed",
                )
            data = canonical(r)
            supplied = data.pop("fact_hash")
            authority = isinstance(r, n.NutritionAuthorityFact)
            _require(
                supplied
                == _digest("nutrition.authority.v1" if authority else "nutrition.record.v1", data),
                "Immutable receipt preimage differs",
            )
            _require(
                r.command_hash
                == _digest(
                    "nutrition.authority-command.v1"
                    if authority
                    else "nutrition.source-command.v1",
                    r.command,
                ),
                "Command identity differs",
            )
            if authority:
                _require(
                    m.authority_scope is not None
                    and canonical(m.authority_scope) == _scope_group(r.command.scope)
                    and r.command.expected_generation == index - 1
                    and r.command.predecessor_id == (previous.id if previous else None),
                    "Authority lineage differs",
                )
                p = principals.get(r.command.principal_id)
                _require(
                    p is not None
                    and p.recorded_at <= r.recorded_at
                    and (p.database_oid, p.database_name)
                    == (r.administrator.database_oid, r.administrator.database_name),
                    "Grant target enrollment differs",
                )
                if (
                    r.command.capability.startswith("GUIDELINE_")
                    or r.command.capability == "ELIGIBILITY_ATTEST"
                ):
                    _require(p.command.verified_human_id is not None, "Human qualification missing")
                if r.command.action == "GRANT":
                    _require(
                        p.command.identity_evidence.environment
                        == (r.command.qualification_evidence.environment),
                        "Principal/grant source environments differ",
                    )
            else:
                _require(
                    m.source_identity == r.command.identity
                    and r.command.revision_id == r.id
                    and r.command.expected_revision == index - 1
                    and r.command.predecessor_id == (previous.id if previous else None),
                    "Source lineage differs",
                )
            previous = r
        _require(
            m.head_id == (previous.id if previous else None)
            and m.head_hash == (previous.fact_hash if previous else None),
            "Head/absence witness differs",
        )
    expected_absence = tuple(sorted(m.stream_key for m in s.streams if not m.revision))
    _require(s.capture.absence_stream_keys == expected_absence, "Absence manifest differs")
    reference = _identity(q, "GUIDELINE", "FAMILY")
    goal_id = _identity(q, "GOAL", "ENERGY_DIRECTION")
    required = {
        _source_stream(i)
        for i in (
            reference,
            goal_id,
            _identity(q, "OBSERVATION", "BODY_MASS"),
            _identity(q, "OBSERVATION", "HEIGHT"),
            _identity(q, "ASSESSMENT", q.protocol_fingerprint),
        )
    }
    required |= {_authority_stream(_scope_of(reference)), _authority_stream(_scope_of(goal_id))}
    _require(required <= set(manifests), "Required absent stream not proved")
    for m in s.streams:
        i = m.source_identity
        if i is None:
            _require(m.stream_key in required, "Foreign authority history")
        elif i.kind == "GUIDELINE":
            _require(i == reference, "Foreign provider/family history")
        else:
            _require(
                (i.household_id, i.member_id) == (q.subject.household_id, q.subject.member_id),
                "Unrelated member history",
            )
            if i.kind == "ASSESSMENT":
                _require(
                    i == _identity(q, "ASSESSMENT", q.protocol_fingerprint),
                    "Wrong assessment protocol captured",
                )
    count = len(s.principals) + len(s.provider_enrollments) + len(records) + len(s.streams)
    _require(
        count == s.capture.row_count
        and count <= 4096
        and s.capture.started_at <= s.capture.completed_at
        and s.current_legacy_anchor.subject == q.subject,
        "Capture cut/count/context differs",
    )
    reader = principals.get(s.capture.reader_principal_id)
    session = s.capture.session
    _require(
        reader is not None
        and (reader.database_oid, reader.database_name, reader.role_oid, reader.command.role_name)
        == (session.database_oid, session.database_name, session.role_oid, session.role_name),
        "Reader actual identity differs",
    )
    witness = s.capture.reader_subject_witness
    _require(
        witness.subject == q.subject and witness.actor_user_id == reader.command.user_id,
        "Reader member-source binding differs",
    )
    _require(
        (
            reader.command.user_id is not None
            and witness.membership_id is not None
            and witness.role is not None
        )
        or (reader.command.user_id is None and reader.command.service_id is not None),
        "Reader household/service authority missing",
    )
    read_scope = n.NutritionAuthorityScope(
        provider_id=q.provider_id,
        family_id=q.family_id,
        household_id=q.subject.household_id,
        member_id=q.subject.member_id,
    )
    for at in (s.capture.started_at, s.capture.completed_at):
        g = _grant(
            s,
            reader.id,
            read_scope,
            "ROOT_SOURCE_READ" if q.purpose == "ROOT" else "VALIDATOR_SOURCE_READ",
            at,
        )
        _require(
            g is not None and g.id == s.capture.reader_grant_id, "Retained reader grant differs"
        )
    sources = {r.id: r for r in s.sources}
    enrollment_by_id = {p.id: p for p in s.provider_enrollments}
    for r in s.sources:
        i, b = r.command.identity, r.command.body
        if b.kind == "OBSERVATION":
            _require(b.observed_at <= r.recorded_at, "Future observation asserted as measured")
        if b.kind == "DELEGATION":
            target = principals.get(b.grantee_principal_id)
            _require(
                target is not None
                and target.command.verified_human_id is not None
                and target.command.user_id is not None,
                "Service cannot receive member authorship",
            )
            if b.action == "REVOKE":
                previous = sources.get(b.previous_grant_id)
                _require(
                    previous is not None
                    and previous.command.body.kind == "DELEGATION"
                    and previous.command.body.action == "GRANT"
                    and previous.command.identity == i
                    and previous.recorded_order < r.recorded_order,
                    "Delegation exact grant lineage differs",
                )
        p = principals.get(r.principal_id)
        _require(
            p is not None
            and (p.database_oid, p.database_name, p.role_oid, p.command.role_name)
            == (
                r.author.database_oid,
                r.author.database_name,
                r.author.role_oid,
                r.author.role_name,
            )
            and p.recorded_at <= r.recorded_at,
            "Actual enrolled author differs",
        )
        _require(
            p.command.identity_evidence.environment == q.environment,
            "Captured source environment differs",
        )
        if b.kind in {"OBSERVATION", "GOAL"}:
            _require(
                b.provenance.environment == p.command.identity_evidence.environment,
                "Member source provenance environment differs",
            )
        if b.kind == "DELEGATION":
            _require(
                b.authorization_evidence.environment == p.command.identity_evidence.environment,
                "Delegation source environment differs",
            )
        if b.kind in {"DRAFT", "REVIEW"}:
            cap, protocol, fact = "GUIDELINE_REVIEW", None, None
        elif b.kind == "PUBLICATION":
            cap, protocol, fact = (
                (
                    "GUIDELINE_PUBLISH"
                    if b.action in {"PUBLISH", "SUPERSEDE"}
                    else "GUIDELINE_WITHDRAW"
                ),
                None,
                None,
            )
        elif b.kind == "ASSESSMENT":
            cap, protocol, fact = "ELIGIBILITY_ATTEST", b.protocol_fingerprint, None
        elif b.kind == "OBSERVATION":
            cap, protocol, fact = "MEMBER_OBSERVATION_WRITE", None, b.fact_key
        elif b.kind == "DELEGATION" and b.operation_scope != "MEMBER_GOAL_WRITE":
            cap, protocol, fact = (
                "MEMBER_OBSERVATION_WRITE",
                None,
                ("BODY_MASS" if b.operation_scope == "BODY_MASS_WRITE" else "HEIGHT"),
            )
        else:
            cap, protocol, fact = "MEMBER_GOAL_WRITE", None, None
        scope = _scope_of(i)
        generation = max(
            (
                a.sequence
                for a in s.authority
                if a.stream_key == _authority_stream(scope) and a.recorded_order < r.recorded_order
            ),
            default=0,
        )
        g = _grant(
            s,
            p.id,
            scope,
            cap,
            r.recorded_at,
            protocol=protocol,
            fact=fact,
            before=r.recorded_order,
        )
        _require(
            g is not None and g.id == r.grant_event_id and generation == r.authority_generation,
            "Author capability/generation differs",
        )
        if i.provider_id is not None:
            enrollment = enrollment_by_id.get(r.provider_enrollment_id)
            _require(
                enrollment is not None
                and enrollment.command.provider_id == i.provider_id
                and (enrollment.administrator.database_oid, enrollment.administrator.database_name)
                == (r.author.database_oid, r.author.database_name),
                "Provider binding differs",
            )
        else:
            _require(
                r.provider_enrollment_id is None, "Member author borrows global reference authority"
            )
        if i.kind == "GUIDELINE":
            _require(
                p.command.verified_human_id is not None
                and r.subject_witness is None
                and r.delegation_event_id is None
                and r.legacy_anchor is None,
                "Reference/member authorities conflated",
            )
        else:
            w = r.subject_witness
            _require(
                w is not None and w.subject == q.subject and w.actor_user_id == p.command.user_id,
                "Canonical member author witness differs",
            )
            own = (
                p.command.user_id is not None
                and w.membership_id is not None
                and w.role in {"OWNER", "EDITOR"}
                and w.actor_member_id == i.member_id
            )
            if b.kind == "ASSESSMENT":
                _require(
                    p.command.verified_human_id is not None, "Assessor human qualification missing"
                )
            elif b.kind == "DELEGATION":
                _require(
                    r.delegation_event_id is None
                    and (
                        own
                        or (
                            p.command.verified_human_id is not None
                            and p.command.delegation_registrar
                        )
                    ),
                    "Delegation issuer lacks exact authority",
                )
            else:
                _require(
                    p.command.user_id is not None
                    and w.membership_id is not None
                    and w.role in {"OWNER", "EDITOR"},
                    "Member household authorship missing",
                )
                if own:
                    _require(r.delegation_event_id is None, "Self borrows representative authority")
                else:
                    op = (
                        "MEMBER_GOAL_WRITE"
                        if b.kind == "GOAL"
                        else "BODY_MASS_WRITE"
                        if b.fact_key == "BODY_MASS"
                        else "HEIGHT_WRITE"
                    )
                    candidates = [
                        d
                        for d in s.sources
                        if d.command.body.kind == "DELEGATION"
                        and d.command.body.grantee_principal_id == p.id
                        and d.command.body.operation_scope == op
                        and d.command.body.effective.start <= r.recorded_at
                        and d.recorded_order < r.recorded_order
                    ]
                    delegation = (
                        max(candidates, key=lambda d: d.recorded_order) if candidates else None
                    )
                    _require(
                        delegation is not None
                        and delegation.id == r.delegation_event_id
                        and delegation.command.body.action == "GRANT"
                        and delegation.command.body.effective.end > r.recorded_at
                        and delegation.command.body.effective.start <= b.effective.start
                        and b.effective.end <= delegation.command.body.effective.end,
                        "Exact representative delegation missing",
                    )
        if b.kind in {"OBSERVATION", "ASSESSMENT"}:
            _require(
                r.legacy_anchor is not None and r.legacy_anchor.subject == q.subject,
                "Legacy anchor missing",
            )
            if (
                b.kind == "OBSERVATION"
                and b.value is not None
                and r.legacy_anchor.profile is not None
            ):
                profile = r.legacy_anchor.profile
                original = profile.body_mass_kg if b.fact_key == "BODY_MASS" else profile.height_cm
                if original is not None:
                    _require(
                        Fraction(original) == Fraction(b.value.numerator, b.value.denominator),
                        "Legacy conflict was not reconciled",
                    )
        else:
            _require(r.legacy_anchor is None, "Unexpected legacy-source substitution")
        if b.kind == "GOAL":
            owner = sources.get(b.goal_id)
            _require(
                owner is not None
                and owner.command.body.kind == "GOAL"
                and owner.command.body.goal_id == owner.id
                and owner.command.identity == i,
                "Cross-member goal identity copy",
            )
    return principals, by_stream


def _reference(s, principals, by_stream):
    records = sorted(
        by_stream.get(_source_stream(_identity(s.request, "GUIDELINE", "FAMILY")), ()),
        key=lambda r: r.sequence,
    )
    drafts, reviews, publications, protocol_ids = {}, {}, [], {}
    for r in records:
        b = r.command.body
        if b.kind == "DRAFT":
            g = b.guideline
            _require(g.environment == s.request.environment, "Guideline environment differs")
            key = g.protocol.protocol_id, g.protocol.version
            h = _digest("nutrition.protocol.v1", g.protocol)
            _require(
                key not in protocol_ids or protocol_ids[key] == h,
                "Immutable protocol version conflict",
            )
            protocol_ids[key] = h
            drafts[r.id] = r
        elif b.kind == "REVIEW":
            draft = drafts.get(b.draft_revision_id)
            _require(draft is not None, "Review draft missing")
            g = draft.command.body.guideline
            _require(
                b.body_fingerprint == _digest("nutrition.guideline-body.v1", g)
                and b.evidence_fingerprint
                == _digest("nutrition.evidence-manifest.v1", g.evidence_manifest)
                and b.protocol_fingerprint == _digest("nutrition.protocol.v1", g.protocol),
                "Review exact body binding differs",
            )
            if b.decision == "CANCEL":
                prior = reviews.get(b.prior_review_id)
                _require(
                    prior is not None
                    and prior.command.body.decision == "APPROVE"
                    and prior.command.body.draft_revision_id == b.draft_revision_id
                    and principals[prior.principal_id].command.verified_human_id
                    == principals[r.principal_id].command.verified_human_id
                    and not any(
                        a.command.body.prior_review_id == prior.id for a in reviews.values()
                    ),
                    "Review cancellation differs",
                )
            reviews[r.id] = r
        else:
            _require(b.kind == "PUBLICATION", "Reference class differs")
            draft = drafts.get(b.draft_revision_id)
            _require(
                draft is not None
                and b.body_fingerprint
                == _digest("nutrition.guideline-body.v1", draft.command.body.guideline),
                "Publication body identity differs",
            )
            if b.action in {"PUBLISH", "SUPERSEDE"}:
                review = reviews.get(b.review_event_id)
                _require(
                    review is not None
                    and review.command.body.decision == "APPROVE"
                    and review.command.body.draft_revision_id == b.draft_revision_id
                    and not any(
                        a.command.body.prior_review_id == review.id for a in reviews.values()
                    ),
                    "Active complete review missing",
                )
                grant = _grant(
                    s,
                    review.principal_id,
                    _scope_of(r.command.identity),
                    "GUIDELINE_REVIEW",
                    r.recorded_at,
                    before=r.recorded_order,
                )
                _require(
                    grant is not None and grant.id == review.grant_event_id,
                    "Reviewer grant changed",
                )
                _require(
                    principals[review.principal_id].command.verified_human_id
                    != principals[r.principal_id].command.verified_human_id,
                    "Same verified human self-published",
                )
            if b.prior_publication_id is not None:
                predecessor = next(
                    (p for p in publications if p.id == b.prior_publication_id), None
                )
                _require(predecessor is not None, "Publication predecessor missing")
                if b.action in {"RETIRE", "RETRACT"}:
                    _require(
                        predecessor.command.body.draft_revision_id == b.draft_revision_id,
                        "Wrong version withdrawn",
                    )
            publications.append(r)
    return drafts, publications, _publication_grid(publications, drafts)


def _assessments(s, by_stream, drafts, publications):
    records = by_stream.get(
        _source_stream(_identity(s.request, "ASSESSMENT", s.request.protocol_fingerprint)), ()
    )
    obs = {r.id: r for r in s.sources if r.command.body.kind == "OBSERVATION"}
    for r in records:
        b = r.command.body
        draft = drafts.get(b.guideline_revision_id)
        _require(
            draft is not None
            and b.guideline_body_fingerprint
            == _digest("nutrition.guideline-body.v1", draft.command.body.guideline),
            "Assessment guideline pin differs",
        )
        protocol = draft.command.body.guideline.protocol
        _require(
            b.protocol_fingerprint == _digest("nutrition.protocol.v1", protocol),
            "Assessment protocol differs",
        )
        if b.operation == "RETRACT":
            _require(b.outcome == "UNDETERMINED", "Assessment tombstone asserts admission")
            continue
        grant = next(a for a in s.authority if a.id == r.grant_event_id)
        _require(
            grant.command.effective.start <= b.effective.start
            and b.effective.end <= grant.command.effective.end,
            "Assessor qualification interval differs",
        )
        earlier = [p for p in publications if p.recorded_order < r.recorded_order]
        state = _published_whole(_publication_grid(earlier, drafts), b.effective)
        _require(
            state is not None
            and state[1]
            and state[0].command.body.draft_revision_id == b.guideline_revision_id,
            "Assessed publication not applicable at retained knowledge cut",
        )
        for ref in b.observations:
            observed = obs.get(ref.revision_id)
            _require(
                observed is not None
                and observed.recorded_order < r.recorded_order
                and observed.fact_hash == ref.fact_hash
                and observed.command.body.fact_key == ref.fact_key
                and observed.command.body.value == ref.value
                and observed.command.body.unit == ref.unit
                and observed.legacy_anchor.body_fingerprint == ref.legacy_anchor_fingerprint
                and observed.legacy_anchor == r.legacy_anchor,
                "Assessment observation/legacy binding differs",
            )
            history = sorted(
                (
                    o
                    for o in obs.values()
                    if o.command.identity == observed.command.identity
                    and o.recorded_order < r.recorded_order
                ),
                key=lambda o: o.sequence,
            )
            current = _whole(_grid(history), b.effective)
            _require(
                current is not None
                and current.id == observed.id
                and current.command.body.operation != "RETRACT",
                "Assessment observation prefix/interval differs",
            )
        reqs = (protocol.admitted, protocol.excluded, protocol.out_of_scope)
        all_facts = {f for req in reqs for f in req.observations}
        all_slots = {v for req in reqs for v in req.evidence_slots}
        supplied_facts = {o.fact_key for o in b.observations}
        supplied_slots = {e.evidence_id for e in b.evidence}
        _require(
            supplied_facts <= all_facts
            and supplied_slots <= all_slots
            and set(b.missing_observations) == all_facts - supplied_facts
            and set(b.missing_evidence_slots) == all_slots - supplied_slots,
            "Assessment completeness manifest differs",
        )
        _require(
            all(e.environment == protocol.environment for e in b.evidence),
            "Assessment content environment differs",
        )
        required = {
            "ADMITTED": protocol.admitted,
            "EXCLUDED": protocol.excluded,
            "OUT_OF_SCOPE": protocol.out_of_scope,
        }.get(b.outcome)
        if required:
            _require(
                set(required.observations) <= supplied_facts
                and set(required.evidence_slots) <= supplied_slots,
                "Outcome-specific assessment evidence incomplete",
            )


def _expected_root(s):
    principals, streams = _audit(s)
    drafts, publications, pub_grid = _reference(s, principals, streams)
    _assessments(s, streams, drafts, publications)
    q = s.request
    findings = set()
    span = q.temporal.interval
    publication = _published_whole(pub_grid, span)
    draft = drafts.get(q.guideline_revision_id)
    if draft is None:
        findings.add("GUIDELINE_UNAVAILABLE")
    elif publication is None:
        findings.add("SOURCE_OUT_OF_EFFECTIVE_RANGE" if pub_grid else "GUIDELINE_UNAVAILABLE")
    elif not publication[1]:
        findings.add(publication[2])
    elif publication[0].command.body.draft_revision_id != q.guideline_revision_id:
        findings.add("GUIDELINE_NOT_APPLICABLE")
    if draft:
        body = draft.command.body.guideline
        if _digest("nutrition.guideline-body.v1", body) != q.guideline_body_fingerprint:
            findings.add("VERSION_MISMATCH")
        if (
            _digest("nutrition.protocol.v1", body.protocol),
            body.protocol.scope_id,
            body.protocol.scope_version,
            body.environment,
        ) != (q.protocol_fingerprint, q.scope_id, q.scope_version, q.environment):
            findings.add("GUIDELINE_NOT_APPLICABLE")
        if any(c.descriptor.temporal != q.temporal for c in body.clauses):
            findings.add("TEMPORAL_SCOPE_MISMATCH")
    goal_cells = _grid(
        sorted(
            streams.get(_source_stream(_identity(q, "GOAL", "ENERGY_DIRECTION")), ()),
            key=lambda r: r.sequence,
        )
    )
    goal = _whole(goal_cells, span)
    if goal is None:
        overlap = any(a < span.end and z > span.start and r is not None for a, z, r in goal_cells)
        goal_state = "AMBIGUOUS" if overlap else "ABSENT"
        findings.add("GOAL_AMBIGUOUS" if overlap else "GOAL_ABSENT")
    elif goal.command.body.operation == "RETRACT":
        goal_state = "RETRACTED"
        findings.add("GOAL_RETRACTED")
    else:
        goal_state = "PRESENT"
    assessments = sorted(
        streams.get(_source_stream(_identity(q, "ASSESSMENT", q.protocol_fingerprint)), ()),
        key=lambda r: r.sequence,
    )
    assessment = _whole(_grid(assessments), span)
    eligibility = "UNKNOWN"
    if assessment is None or assessment.command.body.operation == "RETRACT":
        findings.add("ELIGIBILITY_UNKNOWN")
    else:
        b = assessment.command.body
        changed = (
            assessment.legacy_anchor.body_fingerprint != s.current_legacy_anchor.body_fingerprint
        )
        for ref in b.observations:
            observations = sorted(
                streams.get(_source_stream(_identity(q, "OBSERVATION", ref.fact_key)), ()),
                key=lambda r: r.sequence,
            )
            current = _whole(_grid(observations), span)
            changed |= (
                current is None
                or current.id != ref.revision_id
                or current.command.body.operation == "RETRACT"
                or current.legacy_anchor.body_fingerprint
                != s.current_legacy_anchor.body_fingerprint
            )
        if b.missing_observations:
            findings.add("PHYSIOLOGICAL_INPUT_MISSING")
        if b.missing_evidence_slots:
            findings.add("INSUFFICIENT_EVIDENCE")
        if (b.guideline_revision_id, b.guideline_body_fingerprint, b.protocol_fingerprint) != (
            q.guideline_revision_id,
            q.guideline_body_fingerprint,
            q.protocol_fingerprint,
        ):
            findings.add("VERSION_MISMATCH")
            changed = True
        if changed:
            findings.add("PHYSIOLOGICAL_SOURCE_CHANGED")
        else:
            eligibility = {
                "ADMITTED": "SUPPORTED",
                "EXCLUDED": "INELIGIBLE",
                "OUT_OF_SCOPE": "UNSUPPORTED",
                "UNDETERMINED": "UNKNOWN",
            }[b.outcome]
            if eligibility == "SUPPORTED" and (b.missing_observations or b.missing_evidence_slots):
                eligibility = "UNKNOWN"
        if eligibility != "SUPPORTED":
            findings.add(
                {
                    "UNKNOWN": "ELIGIBILITY_UNKNOWN",
                    "INELIGIBLE": "MEMBER_INELIGIBLE",
                    "UNSUPPORTED": "MEMBER_UNSUPPORTED",
                }[eligibility]
            )
    roots = ()
    if eligibility == "SUPPORTED" and goal_state == "PRESENT" and not findings:
        roots = tuple(
            n.NutritionResolvedRoot(
                publication_event_id=publication[0].id,
                guideline_revision_id=q.guideline_revision_id,
                guideline_body_fingerprint=q.guideline_body_fingerprint,
                clause=clause,
            )
            for clause in draft.command.body.guideline.clauses
        )
    result = n.NutritionRootContract(
        sources=s,
        availability="AVAILABLE" if roots else "UNAVAILABLE",
        eligibility=eligibility,
        goal_state=goal_state,
        goal_revision_id=goal.id if goal_state == "PRESENT" else None,
        goal_direction=goal.command.body.direction if goal_state == "PRESENT" else None,
        roots=roots,
        reasons=tuple(sorted(findings)),
        source_fingerprint=s.source_fingerprint,
        result_fingerprint="0" * 64,
    )
    payload = canonical(result)
    payload.pop("result_fingerprint")
    return n.NutritionRootContract(
        **dict(canonical(result), result_fingerprint=_digest("nutrition.root-result.v1", payload))
    )


def _contained(source, claim):
    # Source identity, period, metric and unit agree before constructing Fractions.
    _require(canonical(source) == canonical(claim.root), "CONTAINMENT_DESCRIPTOR_MISMATCH")
    hard, derived = source.clause.constraint, claim.constraint

    def ratio(value):
        return Fraction(value.numerator, value.denominator)

    if hard.kind == "RANGE":
        if derived.kind == "RANGE":
            return ratio(derived.lower) >= ratio(hard.lower) and ratio(derived.upper) <= ratio(
                hard.upper
            )
        if derived.kind == "TARGET":
            return ratio(hard.lower) <= ratio(derived.center) <= ratio(hard.upper)
    if hard.kind == "MINIMUM" and derived.kind in {"MINIMUM", "RANGE"}:
        return ratio(derived.lower) >= ratio(hard.lower)
    if hard.kind == "MAXIMUM" and derived.kind in {"MAXIMUM", "RANGE"}:
        return ratio(derived.upper) <= ratio(hard.upper)
    return False


def validate_nutrition_root_independently(value):
    """Check only the named coverage. CONSISTENT never authorizes policy or a plan."""
    value = n.NutritionRootValidationInput.model_validate(canonical(value))
    claimed = value.root
    findings = set()
    expected = None
    try:
        sources = _canonical_sources(claimed.sources)
        expected = _expected_root(sources)
        if canonical(claimed) != canonical(expected):
            findings.add("ROOT_SOURCE_RECONSTRUCTION_MISMATCH")
    except (ValueError, KeyError, TypeError, StopIteration):
        findings.add("ROOT_SOURCE_INCONSISTENT")
    checked = False
    decision = "INCONSISTENT" if findings else "CONSISTENT"
    if value.coverage == "ROOT_AND_DERIVED_CONTAINMENT" and not findings:
        if expected.availability != "AVAILABLE" or not value.derived_claims:
            findings.add("REQUIRED_DERIVED_CLAIMS_UNAVAILABLE")
            decision = "UNSUPPORTED"
        else:
            required = {
                r.clause.root_key: r
                for r in expected.roots
                if r.clause.interpretation == "GUIDELINE_HARD"
            }
            covered = set()
            for claim in value.derived_claims:
                key = claim.root.clause.root_key
                if key not in required:
                    findings.add("CONTAINMENT_ROOT_UNSUPPORTED")
                    continue
                if claim.policy_evidence.environment != expected.sources.request.environment:
                    findings.add("DERIVATION_PROVENANCE_ENVIRONMENT_MISMATCH")
                    continue
                if claim.claim_kind == "GOAL_PROTECTION" and (
                    claim.goal_revision_id != expected.goal_revision_id
                    or claim.baseline_evidence is None
                ):
                    findings.add("GOAL_PROTECTION_BASELINE_PROVENANCE_UNAVAILABLE")
                    continue
                try:
                    if not _contained(required[key], claim):
                        findings.add("HARD_ROOT_CONTAINMENT_FAILED")
                except ValueError:
                    findings.add("CONTAINMENT_DESCRIPTOR_MISMATCH")
                covered.add(key)
            if covered != set(required):
                findings.add("REQUIRED_DERIVED_CLAIMS_UNAVAILABLE")
            checked = True
            if findings:
                decision = "INCONSISTENT"
    return n.NutritionRootValidationReport(
        coverage=value.coverage,
        decision=decision,
        findings=tuple(sorted(findings)),
        source_fingerprint=claimed.source_fingerprint,
        root_fingerprint=claimed.result_fingerprint,
        containment_checked=checked,
    )
