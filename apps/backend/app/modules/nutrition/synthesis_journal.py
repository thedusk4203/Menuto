"""Pure replay of the retained synthesis journal; no claim of offline database origin."""

from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition import synthesis_contracts as c


def digest(domain, value):
    return n.nutrition_root_hash("nutrition-synthesis." + domain + ".v1", value)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _covers(span, start, end):
    return span.start <= start and end <= span.end


def applicability(root_request):
    q = root_request
    return c.NutritionRuleApplicability(
        root_provider_id=q.provider_id,
        root_family_id=q.family_id,
        guideline_revision_id=q.guideline_revision_id,
        guideline_body_fingerprint=q.guideline_body_fingerprint,
        protocol_fingerprint=q.protocol_fingerprint,
        scope_id=q.scope_id,
        scope_version=q.scope_version,
        temporal=q.temporal,
    )


def _enrollments(s, principals):
    histories, bindings = {}, {}
    for fact in s.principal_facts:
        histories.setdefault(fact.enrollment_root_id, []).append(fact)
        binding = (fact.database_oid, fact.role_oid, fact.command.role_name)
        require(
            binding not in bindings or bindings[binding] == fact.enrollment_root_id,
            "One actual credential cannot mint multiple logical authors",
        )
        bindings[binding] = fact.enrollment_root_id
    heads = []
    for root, history in sorted(histories.items(), key=lambda pair: str(pair[0])):
        history.sort(key=lambda f: f.generation)
        previous = None
        require(len(history) <= 64, "Principal history resource limit")
        for gen, fact in enumerate(history, 1):
            require(
                fact.generation == gen
                and fact.command.expected_generation == gen - 1
                and fact.command.previous_enrollment_id == (previous.id if previous else None),
                "Principal replacement lineage differs",
            )
            require(
                (previous is not None and previous.recorded_order < fact.recorded_order)
                or (previous is None and fact.id == root),
                "Principal recorded enrollment order differs",
            )
            previous = fact
        heads.append(
            c.NutritionSynthesisPrincipalFrontier(
                enrollment_root_id=root,
                revision=previous.generation,
                head_id=previous.id,
                head_hash=digest("principal-fact", previous),
            )
        )
    require(s.principal_frontiers == tuple(heads), "Complete principal enrollment frontier differs")

    def current(who, order=None):
        fact = principals[who]
        known = [
            p
            for p in histories[fact.enrollment_root_id]
            if order is None or p.recorded_order < order
        ]
        require(known and known[-1].id == who, "Exact current enrollment revision required")

    return current


def _publication(segments, record, rule):
    b = record.command.body
    lo, hi = b.effective_at, rule.effective.end
    out = []
    found = False
    for seg in segments:
        a, z = seg["start"], seg["end"]
        if b.action == "PUBLISH":
            require(not (a < hi and z > lo), "Overlapping publication cannot be hidden")
            out.append(seg)
        elif seg["publication_id"] == b.predecessor_publication_id and z > lo:
            found = True
            if a < lo:
                out.append(seg | dict(end=lo))
            if b.action in {"RETIRE", "RETRACT"}:
                require(seg["revision_id"] == b.revision_id, "Withdrawal revision differs")
                out.append(
                    seg
                    | dict(
                        start=max(a, lo),
                        publication_id=record.id,
                        active=False,
                        cause="RULE_WITHDRAWN",
                    )
                )
            elif z > hi:
                out.append(
                    seg
                    | dict(
                        start=hi,
                        publication_id=record.id,
                        active=False,
                        cause="RULE_OUTSIDE_EFFECTIVE_RANGE",
                    )
                )
        else:
            require(
                b.action != "SUPERSEDE" or not (a < hi and z > lo),
                "Unrelated scheduled publication overlaps",
            )
            out.append(seg)
    found = found or (
        b.action == "SUPERSEDE"
        and any(
            x["publication_id"] == b.predecessor_publication_id and x["end"] == lo for x in segments
        )
    )
    require(b.action == "PUBLISH" or found, "Exact applicable publication predecessor required")
    if b.action in {"PUBLISH", "SUPERSEDE"}:
        out.append(
            dict(
                start=lo,
                end=hi,
                publication_id=record.id,
                revision_id=b.revision_id,
                active=True,
                cause=None,
            )
        )
    require(len(out) <= 64, "Publication interval resource limit")
    return sorted(out, key=lambda x: x["start"])


def replay_synthesis_sources(value):
    """Return the exact selected rule, or a finite missingness reason. Invalid history raises."""
    s = c.NutritionSynthesisSourceSnapshot.model_validate(canonical(value))
    body = canonical(s)
    body.pop("source_fingerprint")
    require(s.source_fingerprint == digest("sources", body), "Synthesis source fingerprint differs")
    root = s.request.root
    q, pin = root.sources.request, s.request.selection
    root_frame, frame = root.sources.capture, s.frame
    fields = (
        "session",
        "endpoint",
        "backend_pid",
        "mvcc_snapshot",
        "transaction_id",
        "isolation",
        "read_only",
    )
    require(
        all(getattr(root_frame, k) == getattr(frame, k) for k in fields),
        "Root/rule cut incoherence",
    )
    require(
        root_frame.completed_at <= frame.started_at <= frame.completed_at,
        "Capture interval incoherent",
    )
    require(
        frame.reader_subject_witness == root_frame.reader_subject_witness,
        "Exact-subject reader witness differs",
    )
    require(frame.session.database_oid == root_frame.session.database_oid, "Database differs")
    principal = {p.id: p for p in s.principal_facts}
    require(len(principal) == len(s.principal_facts), "Duplicate principal")
    for p in s.principal_facts:
        require(
            p.command_hash == digest("principal-command", p.command), "Principal command differs"
        )
        require(
            p.database_oid == frame.session.database_oid
            and p.database_name == frame.session.database_name,
            "Enrolled principal database mismatch",
        )
    reader = principal.get(frame.reader_principal_id)
    immutable = (*s.provider_facts, *s.principal_facts, *s.grant_facts, *s.records)
    require(
        len({f.recorded_order for f in immutable}) == len(immutable),
        "Duplicate recorded transaction order",
    )
    require(len({r.id for r in s.records}) == len(s.records), "Duplicate immutable event ID")
    require(
        len({(r.principal_id, r.command.idempotency_key) for r in s.records}) == len(s.records),
        "Duplicate actor/idempotency receipt",
    )
    current_enrollment = _enrollments(s, principal)
    require(
        len({p.id for p in s.provider_facts}) == len(s.provider_facts),
        "Duplicate provider enrollment ID",
    )
    require(
        reader is not None
        and reader.role_oid == frame.session.role_oid
        and reader.command.role_name == frame.session.role_name,
        "Actual enrolled reader mismatch",
    )
    current_enrollment(reader.id)
    previous = None
    for generation, provider in enumerate(s.provider_facts, 1):
        command = provider.command
        require(
            provider.generation == generation
            and command.expected_generation == generation - 1
            and command.predecessor_id == previous
            and command.provider_id == pin.provider_id,
            "Provider enrollment frontier differs",
        )
        require(
            provider.command_hash == digest("provider-command", command), "Provider command differs"
        )
        require(
            provider.administrator.database_oid == frame.session.database_oid
            and provider.administrator.database_name == frame.session.database_name,
            "Provider database binding differs",
        )
        require(
            command.environment == q.environment == command.evidence.environment,
            "Provider environment differs",
        )
        previous = provider.id
    require(
        previous is not None and previous == frame.provider_enrollment_id,
        "Complete provider enrollment history required",
    )
    grants = {}
    for grant in s.grant_facts:
        command = grant.command
        key = (command.principal_id, command.capability)
        prior = grants.get(key)
        require(
            command.provider_id == pin.provider_id and command.family_id == pin.family_id,
            "Foreign authority remit",
        )
        require(command.principal_id in principal, "Authority principal unavailable")
        require(
            principal[command.principal_id].recorded_order < grant.recorded_order,
            "Authority predates principal enrollment",
        )
        if command.action == "GRANT":
            current_enrollment(command.principal_id, grant.recorded_order)
        require(grant.command_hash == digest("grant-command", command), "Grant command differs")
        require(
            grant.generation == (prior.generation + 1 if prior else 1)
            and command.expected_generation == grant.generation - 1
            and command.predecessor_id == (prior.id if prior else None),
            "Grant frontier differs",
        )
        grants[key] = grant
    require(len({g.id for g in s.grant_facts}) == len(s.grant_facts), "Duplicate authority fact")
    capabilities = (
        "SYNTHESIS_RULE_PUBLISH",
        "SYNTHESIS_RULE_REVIEW",
        "SYNTHESIS_RULE_WITHDRAW",
        "SYNTHESIS_SOURCE_READ",
        "SYNTHESIS_VALIDATOR_READ",
    )
    expected_frontiers = []
    for who in sorted(principal, key=str):
        for cap in capabilities:
            head = grants.get((who, cap))
            expected_frontiers.append(
                c.NutritionSynthesisAuthorityFrontier(
                    principal_id=who,
                    capability=cap,
                    revision=head.generation if head else 0,
                    head_id=head.id if head else None,
                    head_hash=digest("grant-fact", head) if head else None,
                )
            )
    require(
        s.authority_frontiers == tuple(expected_frontiers),
        "Complete authority frontier/absence manifest differs",
    )

    def permission(who, cap, when, expected=None, app=None, order=None):
        current_enrollment(who, order)
        history = [
            g
            for g in s.grant_facts
            if g.command.principal_id == who
            and g.command.capability == cap
            and (order is None or g.recorded_order < order)
        ]
        g = max(history, key=lambda x: x.generation, default=None)
        require(
            g is not None
            and g.command.action == "GRANT"
            and g.command.effective.start <= when < g.command.effective.end,
            "Retained exact capability unavailable",
        )
        require(app is None or g.command.applicability == app, "Authority applicability mismatch")
        require(expected is None or g.id == expected, "Author grant identity mismatch")
        return g

    permission(
        reader.id,
        "SYNTHESIS_VALIDATOR_READ" if q.purpose == "VALIDATOR" else "SYNTHESIS_SOURCE_READ",
        frame.started_at,
        frame.reader_grant_id,
        applicability(q),
    )
    if s.request.precision:
        selection, witness = s.request.precision, s.precision_witness
        require(
            witness is not None
            and witness.subject == selection.subject == q.subject
            and witness.actor_user_id == selection.actor_user_id == reader.command.user_id
            and witness.membership_id is not None
            and witness.role in {"OWNER", "EDITOR"},
            "Authenticated explicit precision witness unavailable",
        )
        require(selection.evidence.environment == q.environment, "Precision environment mismatch")
    else:
        require(s.precision_witness is None, "Unexpected precision witness")
    drafts, reviews, evidence, publications = {}, {}, {}, []
    segments = []
    for fact in (*s.provider_facts, *s.principal_facts, *s.grant_facts):
        item = fact.command.evidence
        require(item.environment == q.environment, "Authority evidence environment differs")
        require(
            item.evidence_id not in evidence or evidence[item.evidence_id] == item,
            "Conflicting authority evidence identity",
        )
        evidence[item.evidence_id] = item
    previous_id, previous_hash = None, None
    previous_order = None
    for seq, record in enumerate(s.records, 1):
        command, b = record.command, record.command.body
        require(
            record.id == command.event_id
            and record.sequence == seq
            and command.expected_revision == seq - 1
            and command.predecessor_id == previous_id
            and record.previous_hash == previous_hash,
            "Source lineage differs",
        )
        require(
            previous_order is None or previous_order < record.recorded_order,
            "Recorded transaction order reversed",
        )
        require(
            command.provider_id == pin.provider_id and command.family_id == pin.family_id,
            "Foreign rule stream",
        )
        require(record.command_hash == digest("command", command), "Command fingerprint differs")
        data = canonical(record)
        data.pop("event_hash")
        require(record.event_hash == digest("event", data), "Event fingerprint differs")
        actor = principal.get(record.principal_id)
        require(
            actor is not None and actor.recorded_order < record.recorded_order,
            "Principal enrollment unavailable before authoring",
        )
        require(
            actor is not None
            and actor.role_oid == record.session.role_oid
            and actor.command.role_name == record.session.role_name
            and actor.database_oid == record.session.database_oid
            and actor.database_name == record.session.database_name
            and actor.command.verified_human_id is not None,
            "Verified rule author binding differs",
        )
        cap = (
            "SYNTHESIS_RULE_REVIEW"
            if b.kind in {"DRAFT", "REVIEW"}
            else "SYNTHESIS_RULE_WITHDRAW"
            if b.action in {"RETIRE", "RETRACT"}
            else "SYNTHESIS_RULE_PUBLISH"
        )
        record_rule = b.rule if b.kind == "DRAFT" else drafts.get(b.revision_id)
        require(record_rule is not None, "Referenced rule revision unavailable")
        permission(
            actor.id,
            cap,
            record.recorded_at,
            record.grant_id,
            record_rule.applicability,
            record.recorded_order,
        )
        if b.kind == "DRAFT":
            rule = b.rule
            require(
                rule.revision_id not in drafts
                and rule.provider_id == pin.provider_id
                and rule.family_id == pin.family_id,
                "Exact immutable rule applicability differs",
            )
            require(rule.environment == q.environment, "Mixed source environment")
            drafts[rule.revision_id] = rule
            for item in rule.evidence:
                require(
                    item.evidence_id not in evidence or evidence[item.evidence_id] == item,
                    "Conflicting evidence identity",
                )
                evidence[item.evidence_id] = item
        else:
            rule = drafts.get(b.revision_id)
            require(
                rule is not None and digest("rule", rule) == b.body_fingerprint,
                "Exact immutable reviewed rule unavailable",
            )
            if b.kind == "REVIEW":
                require(
                    b.evidence_fingerprint == digest("evidence-manifest", rule.evidence),
                    "Review evidence binding differs",
                )
                if b.decision == "CANCEL":
                    prior = reviews.get(b.prior_review_id)
                    require(
                        prior is not None
                        and prior.principal_id == actor.id
                        and prior.command.body.decision == "APPROVE",
                        "Invalid review cancellation",
                    )
                else:
                    require(b.prior_review_id is None, "Unexpected prior review")
                reviews[record.id] = record
            else:
                if b.action in {"PUBLISH", "SUPERSEDE"}:
                    review = reviews.get(b.review_id)
                    require(
                        review is not None
                        and review.command.body.decision == "APPROVE"
                        and review.command.body.revision_id == b.revision_id,
                        "Exact approved review unavailable",
                    )
                    require(
                        not any(
                            v.command.body.prior_review_id == review.id for v in reviews.values()
                        ),
                        "Review cancelled",
                    )
                    reviewer = principal[review.principal_id]
                    require(
                        reviewer.command.verified_human_id != actor.command.verified_human_id,
                        "Reviewer/publisher same verified human",
                    )
                    permission(
                        reviewer.id,
                        "SYNTHESIS_RULE_REVIEW",
                        record.recorded_at,
                        expected=review.grant_id,
                        app=rule.applicability,
                        order=record.recorded_order,
                    )
                    require(
                        rule.effective.start <= b.effective_at < rule.effective.end,
                        "Publication outside reviewed interval",
                    )
                else:
                    require(b.review_id is None, "Withdrawal does not manufacture review")
                segments = _publication(segments, record, rule)
                publications.append(record)
        previous_id, previous_hash, previous_order = (
            record.id,
            record.event_hash,
            record.recorded_order,
        )
    require(
        (len(s.records), previous_id, previous_hash)
        == (s.frontier_revision, s.frontier_id, s.frontier_hash),
        "Complete source frontier differs",
    )
    require(
        frame.row_count
        == len(s.records)
        + len(s.provider_facts)
        + len(s.principal_facts)
        + len(s.grant_facts)
        + len(s.authority_frontiers)
        + len(s.principal_frontiers),
        # Enrollment and grant generations are distinct from the frozen root's
        # generations; the shared MVCC frame, not those counters, proves the cut.
        "Capture row manifest differs",
    )
    absence = (digest("absence", pin),) if not s.records else ()
    require(frame.absence_stream_keys == absence, "Absence witness differs")
    span = q.temporal.interval
    applicable = [x for x in segments if x["start"] < span.end and x["end"] > span.start]
    if not applicable:
        return s, None, "RULE_OUTSIDE_EFFECTIVE_RANGE" if publications else "RULE_UNAVAILABLE"
    if len(applicable) != 1:
        return s, None, "CROSS_PUBLICATION_HORIZON_UNSUPPORTED"
    segment = applicable[0]
    if not (segment["start"] <= span.start and span.end <= segment["end"]):
        return s, None, "CROSS_PUBLICATION_HORIZON_UNSUPPORTED"
    if not segment["active"]:
        return s, None, segment["cause"]
    selected = next(r for r in publications if r.id == segment["publication_id"])
    b = selected.command.body
    rule = drafts[b.revision_id]
    require(rule.applicability == applicability(q), "Selected rule applicability mismatch")
    if not _covers(rule.effective, span.start, span.end):
        return s, None, "RULE_OUTSIDE_EFFECTIVE_RANGE"
    require(
        selected.id == pin.publication_id
        and b.revision_id == pin.revision_id
        and b.body_fingerprint == pin.body_fingerprint
        and digest("evidence-manifest", rule.evidence) == pin.evidence_fingerprint,
        "Exact selected publication pins differ",
    )
    return s, rule, None
