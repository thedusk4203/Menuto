"""Independent retained NPS source-authority replay for NRE; no producer imports."""

from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition import synthesis_contracts as c


def _hash(kind, value):
    return n.nutrition_root_hash("nutrition-synthesis." + kind + ".v1", value)


def _check(truth, reason):
    if not truth:
        raise ValueError(reason)


def _principal_history(snapshot, people):
    groups, bindings = {}, {}
    for fact in people.values():
        groups.setdefault(fact.enrollment_root_id, []).append(fact)
        key = (fact.database_oid, fact.role_oid, fact.command.role_name)
        _check(
            key not in bindings or bindings[key] == fact.enrollment_root_id, "ONE_CREDENTIAL_AUTHOR"
        )
        bindings[key] = fact.enrollment_root_id
    expected = []
    for identity, versions in sorted(groups.items(), key=lambda p: str(p[0])):
        versions.sort(key=lambda f: f.generation)
        _check(len(versions) <= 64, "ENROLLMENT_HISTORY_LIMIT")
        last = None
        for i, fact in enumerate(versions):
            _check(
                fact.generation == i + 1
                and fact.command.expected_generation == i
                and fact.command.previous_enrollment_id == (last.id if last else None),
                "ENROLLMENT_LINEAGE",
            )
            _check(
                last.recorded_order < fact.recorded_order if last else fact.id == identity,
                "ENROLLMENT_ORDER",
            )
            last = fact
        expected.append(
            c.NutritionSynthesisPrincipalFrontier(
                enrollment_root_id=identity,
                revision=last.generation,
                head_id=last.id,
                head_hash=_hash("principal-fact", last),
            )
        )
    _check(snapshot.principal_frontiers == tuple(expected), "ENROLLMENT_MANIFEST")

    def active(who, before=None):
        eligible = [
            p
            for p in groups[people[who].enrollment_root_id]
            if before is None or p.recorded_order < before
        ]
        _check(eligible and eligible[-1].id == who, "ENROLLMENT_REPLACED")

    return active


def _publication_cells(records, drafts, interval):
    # Independent boundary-grid replay; never calls the producer's segment reducer.
    points = {interval.start, interval.end}
    for record in records:
        b = record.command.body
        points.update((b.effective_at, drafts[b.revision_id].effective.end))
    grid = sorted(points)
    cells = {(a, b): None for a, b in zip(grid, grid[1:])}
    for record in records:
        b = record.command.body
        lo, hi = b.effective_at, drafts[b.revision_id].effective.end
        target = False
        old = dict(cells)
        for (left, right), value in old.items():
            if b.action == "PUBLISH":
                _check(not (left < hi and right > lo and value is not None), "PUBLICATION_OVERLAP")
            elif value is not None and value[0] == b.predecessor_publication_id and right > lo:
                target = True
                if b.action in {"RETIRE", "RETRACT"}:
                    _check(value[1] == b.revision_id, "WITHDRAW_REVISION")
                    cells[left, right] = (record.id, value[1], False)
                elif right > hi:
                    cells[left, right] = (record.id, value[1], False)
                else:
                    cells[left, right] = None
            elif b.action == "SUPERSEDE" and left < hi and right > lo:
                _check(value is None, "UNRELATED_SCHEDULED_VERSION")
        if b.action == "SUPERSEDE":
            target = target or any(
                value is not None and value[0] == b.predecessor_publication_id and right == lo
                for (left, right), value in old.items()
            )
        _check(b.action == "PUBLISH" or target, "PUBLICATION_PREDECESSOR")
        if b.action in {"PUBLISH", "SUPERSEDE"}:
            for left, right in cells:
                if lo <= left and right <= hi:
                    cells[left, right] = (record.id, b.revision_id, True)
    values = [
        value
        for (left, right), value in cells.items()
        if interval.start <= left and right <= interval.end
    ]
    _check(
        values and all(value is not None and value[2] for value in values), "PUBLICATION_COVERAGE"
    )
    _check(len(set(values)) == 1, "CROSS_VERSION_STITCHING")
    return values[0][0]


def verify_resolution_rule_sources(s):
    root = s.request.root
    source_body = canonical(s)
    source_body.pop("source_fingerprint")
    _check(_hash("sources", source_body) == s.source_fingerprint, "SOURCE_IDENTITY")
    q, pin = root.sources.request, s.request.selection
    frame, rootframe = s.frame, root.sources.capture
    for name in ("session", "backend_pid", "mvcc_snapshot", "endpoint", "isolation", "read_only"):
        _check(getattr(frame, name) == getattr(rootframe, name), "COMMON_CUT")
    _check(rootframe.completed_at <= frame.started_at <= frame.completed_at, "CAPTURE_TIME")
    _check(frame.reader_subject_witness == rootframe.reader_subject_witness, "READER_SUBJECT")
    principals = {x.id: x for x in s.principal_facts}
    facts = (*s.provider_facts, *s.principal_facts, *s.grant_facts, *s.records)
    _check(len({f.recorded_order for f in facts}) == len(facts), "UNIQUE_DATABASE_ORDER")
    _check(len({r.id for r in s.records}) == len(s.records), "UNIQUE_RECEIPT_IDENTITY")
    _check(
        len({(r.principal_id, r.command.idempotency_key) for r in s.records}) == len(s.records),
        "UNIQUE_IDEMPOTENCY_RECEIPT",
    )
    enrolled = _principal_history(s, principals)
    _check(len(principals) == len(s.principal_facts), "DUPLICATE_PRINCIPAL")
    for principal in principals.values():
        _check(
            principal.command_hash == _hash("principal-command", principal.command),
            "PRINCIPAL_BODY",
        )
        _check(
            (principal.database_oid, principal.database_name)
            == (frame.session.database_oid, frame.session.database_name),
            "PRINCIPAL_DATABASE",
        )
    reader = principals[frame.reader_principal_id]
    enrolled(reader.id)
    _check(
        (reader.role_oid, reader.command.role_name)
        == (frame.session.role_oid, frame.session.role_name),
        "READER_IDENTITY",
    )
    last = None
    for i, provider in enumerate(s.provider_facts):
        _check(
            provider.generation == i + 1
            and provider.command.expected_generation == i
            and provider.command.predecessor_id == last
            and provider.command.provider_id == pin.provider_id,
            "PROVIDER_HISTORY",
        )
        _check(
            provider.command_hash == _hash("provider-command", provider.command)
            and provider.command.environment == q.environment,
            "PROVIDER_AUTHORITY",
        )
        _check(
            provider.administrator.database_oid == frame.session.database_oid
            and provider.administrator.database_name == frame.session.database_name,
            "PROVIDER_DATABASE",
        )
        last = provider.id
    _check(last == frame.provider_enrollment_id and last is not None, "PROVIDER_FRONTIER")
    histories = {}
    for fact in s.grant_facts:
        cmd = fact.command
        _check(
            fact.command_hash == _hash("grant-command", cmd)
            and cmd.provider_id == pin.provider_id
            and cmd.family_id == pin.family_id
            and cmd.principal_id in principals,
            "GRANT_IDENTITY",
        )
        group = histories.setdefault((cmd.principal_id, cmd.capability), [])
        _check(
            principals[cmd.principal_id].recorded_order < fact.recorded_order,
            "AUTHORITY_ENROLLMENT_ORDER",
        )
        if cmd.action == "GRANT":
            enrolled(cmd.principal_id, fact.recorded_order)
        _check(
            fact.generation == len(group) + 1
            and cmd.expected_generation == len(group)
            and cmd.predecessor_id == (group[-1].id if group else None),
            "GRANT_FRONTIER",
        )
        group.append(fact)
    _check(len({x.id for x in s.grant_facts}) == len(s.grant_facts), "UNIQUE_GRANT_EVENT")
    expected = []
    for who in sorted(principals, key=str):
        for cap in (
            "SYNTHESIS_RULE_PUBLISH",
            "SYNTHESIS_RULE_REVIEW",
            "SYNTHESIS_RULE_WITHDRAW",
            "SYNTHESIS_SOURCE_READ",
            "SYNTHESIS_VALIDATOR_READ",
        ):
            journal = histories.get((who, cap), ())
            head = journal[-1] if journal else None
            expected.append(
                c.NutritionSynthesisAuthorityFrontier(
                    principal_id=who,
                    capability=cap,
                    revision=head.generation if head else 0,
                    head_id=head.id if head else None,
                    head_hash=_hash("grant-fact", head) if head else None,
                )
            )
    _check(s.authority_frontiers == tuple(expected), "COMPLETE_AUTHORITY_MANIFEST")

    def authorize(who, cap, when, grant_id=None, app=None, before=None):
        enrolled(who, before)
        eligible = [
            x for x in histories.get((who, cap), ()) if before is None or x.recorded_order < before
        ]
        _check(bool(eligible), "AUTHORITY_ABSENT")
        grant = eligible[-1]
        _check(
            grant.command.action == "GRANT"
            and grant.command.effective.start <= when < grant.command.effective.end,
            "AUTHORITY_REVOKED_OR_EXPIRED",
        )
        _check(grant_id is None or grant.id == grant_id, "AUTHORITY_IDENTITY")
        _check(app is None or grant.command.applicability == app, "AUTHORITY_REMIT")

    expected_app = c.NutritionRuleApplicability(
        root_provider_id=q.provider_id,
        root_family_id=q.family_id,
        guideline_revision_id=q.guideline_revision_id,
        guideline_body_fingerprint=q.guideline_body_fingerprint,
        protocol_fingerprint=q.protocol_fingerprint,
        scope_id=q.scope_id,
        scope_version=q.scope_version,
        temporal=q.temporal,
    )
    authorize(
        reader.id,
        "SYNTHESIS_VALIDATOR_READ" if q.purpose == "VALIDATOR" else "SYNTHESIS_SOURCE_READ",
        frame.started_at,
        frame.reader_grant_id,
        expected_app,
    )
    precision = s.request.precision
    _check(precision is not None and s.precision_witness is not None, "PRECISION_WITNESS")
    witness = s.precision_witness
    _check(
        precision.subject == witness.subject == q.subject
        and precision.actor_user_id == witness.actor_user_id == reader.command.user_id
        and witness.membership_id is not None
        and witness.role in {"OWNER", "EDITOR"}
        and precision.evidence.environment == q.environment,
        "PRECISION_AUTHORIZATION",
    )
    draft, review, publications, evidence = {}, {}, [], {}
    for fact in (*s.provider_facts, *s.principal_facts, *s.grant_facts):
        item = fact.command.evidence
        _check(item.environment == q.environment, "AUTHORITY_EVIDENCE_ENVIRONMENT")
        _check(
            item.evidence_id not in evidence or evidence[item.evidence_id] == item,
            "AUTHORITY_EVIDENCE_COLLISION",
        )
        evidence[item.evidence_id] = item
    previous_id = previous_hash = None
    previous_order = None
    for index, record in enumerate(s.records):
        cmd, body = record.command, record.command.body
        _check(
            cmd.provider_id == pin.provider_id
            and cmd.family_id == pin.family_id
            and record.id == cmd.event_id
            and record.sequence == index + 1
            and cmd.expected_revision == index
            and cmd.predecessor_id == previous_id
            and record.previous_hash == previous_hash,
            "RECEIPT_LINEAGE",
        )
        _check(previous_order is None or previous_order < record.recorded_order, "RECORDED_ORDER")
        preimage = canonical(record)
        preimage.pop("event_hash")
        _check(
            _hash("event", preimage) == record.event_hash
            and _hash("command", cmd) == record.command_hash,
            "RECEIPT_BODY",
        )
        author = principals[record.principal_id]
        _check(author.recorded_order < record.recorded_order, "ENROLLMENT_PRECEDES_AUTHORING")
        _check(
            author.command.verified_human_id is not None
            and (
                author.database_oid,
                author.database_name,
                author.role_oid,
                author.command.role_name,
            )
            == (
                record.session.database_oid,
                record.session.database_name,
                record.session.role_oid,
                record.session.role_name,
            ),
            "AUTHOR_IDENTITY",
        )
        cap = (
            "SYNTHESIS_RULE_REVIEW"
            if body.kind in {"DRAFT", "REVIEW"}
            else "SYNTHESIS_RULE_WITHDRAW"
            if body.action in {"RETIRE", "RETRACT"}
            else "SYNTHESIS_RULE_PUBLISH"
        )
        if body.kind == "DRAFT":
            rule = body.rule
            _check(
                rule.revision_id not in draft
                and rule.provider_id == pin.provider_id
                and rule.family_id == pin.family_id
                and rule.environment == q.environment,
                "DRAFT_IDENTITY",
            )
            draft[rule.revision_id] = rule
            for item in rule.evidence:
                _check(
                    item.evidence_id not in evidence or evidence[item.evidence_id] == item,
                    "EVIDENCE_COLLISION",
                )
                evidence[item.evidence_id] = item
        else:
            rule = draft[body.revision_id]
            _check(_hash("rule", rule) == body.body_fingerprint, "REVIEWED_BODY")
            if body.kind == "REVIEW":
                _check(
                    _hash("evidence-manifest", rule.evidence) == body.evidence_fingerprint,
                    "REVIEWED_EVIDENCE",
                )
                if body.decision == "CANCEL":
                    prior = review[body.prior_review_id]
                    _check(
                        prior.principal_id == record.principal_id
                        and prior.command.body.decision == "APPROVE",
                        "REVIEW_CANCEL",
                    )
                else:
                    _check(body.prior_review_id is None, "REVIEW_PREDECESSOR")
                review[record.id] = record
            else:
                if body.action in {"PUBLISH", "SUPERSEDE"}:
                    receipt = review[body.review_id]
                    _check(
                        receipt.command.body.decision == "APPROVE"
                        and receipt.command.body.revision_id == body.revision_id
                        and not any(
                            x.command.body.prior_review_id == receipt.id for x in review.values()
                        ),
                        "COMPLETE_REVIEW",
                    )
                    _check(
                        principals[receipt.principal_id].command.verified_human_id
                        != author.command.verified_human_id,
                        "HUMAN_SEPARATION",
                    )
                    authorize(
                        receipt.principal_id,
                        "SYNTHESIS_RULE_REVIEW",
                        record.recorded_at,
                        grant_id=receipt.grant_id,
                        app=rule.applicability,
                        before=record.recorded_order,
                    )
                    _check(
                        rule.effective.start <= body.effective_at < rule.effective.end,
                        "PUBLICATION_EFFECTIVE_RANGE",
                    )
                else:
                    _check(body.review_id is None, "WITHDRAWAL_REVIEW")
                publications.append(record)
        authorize(
            author.id,
            cap,
            record.recorded_at,
            record.grant_id,
            rule.applicability,
            before=record.recorded_order,
        )
        previous_id, previous_hash, previous_order = (
            record.id,
            record.event_hash,
            record.recorded_order,
        )
    _check(
        (s.frontier_revision, s.frontier_id, s.frontier_hash)
        == (len(s.records), previous_id, previous_hash),
        "SOURCE_FRONTIER",
    )
    _check(
        frame.row_count
        == len(s.records)
        + len(s.provider_facts)
        + len(s.principal_facts)
        + len(s.grant_facts)
        + len(s.authority_frontiers)
        + len(s.principal_frontiers),
        "ROW_MANIFEST",
    )
    _check(frame.absence_stream_keys == (), "AVAILABLE_HISTORY_ABSENCE")
    interval = q.temporal.interval
    selected_id = _publication_cells(publications, draft, interval)
    selected = next(r for r in publications if r.id == selected_id)
    _check(
        selected.id == pin.publication_id
        and selected.command.body.revision_id == pin.revision_id
        and selected.command.body.action in {"PUBLISH", "SUPERSEDE"},
        "EXACT_SELECTED_PUBLICATION",
    )
    rule = draft[pin.revision_id]
    _check(
        rule.applicability == expected_app
        and rule.effective.start <= interval.start
        and interval.end <= rule.effective.end
        and _hash("rule", rule) == pin.body_fingerprint
        and _hash("evidence-manifest", rule.evidence) == pin.evidence_fingerprint,
        "EXACT_RULE_SELECTION",
    )
    return rule
