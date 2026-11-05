"""Independent finite-relation checker. No producer business implementation is imported.

An internally consistent retained cut is not proof of its database origin, current
authorization, scientific validity, or a feasible/activatable plan.
"""

import json
from fractions import Fraction

from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition import synthesis_contracts as c
from app.modules.validation.nutrition_roots import validate_nutrition_root_independently


def _hash(kind, value):
    return n.nutrition_root_hash("nutrition-synthesis." + kind + ".v1", value)


def _check(truth, reason):
    if not truth:
        raise ValueError(reason)


def _fraction(value):
    return Fraction(value.numerator, value.denominator)


def _bounds(value):
    if value.kind == "TARGET":
        return _fraction(value.center), _fraction(value.center)
    return (
        _fraction(value.lower) if hasattr(value, "lower") else None,
        _fraction(value.upper) if hasattr(value, "upper") else None,
    )


def _inside(value, protection):
    low, high = _bounds(value)
    left, right = _bounds(protection)
    return (left is None or (low is not None and left <= low)) and (
        right is None or (high is not None and high <= right)
    )


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


def _source(policy):
    s, root = policy.inputs, policy.inputs.request.root
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


def _relations(policy, rule, case):
    root = policy.inputs.request.root
    clauses = {x.clause.root_key: x.clause for x in root.roots}
    traces = policy.trace
    _check(
        tuple(t.operation_id for t in traces) == tuple(o.id for o in case.operations),
        "COMPLETE_TRACE",
    )
    values = {}
    selected = set()
    direction = set()
    for op, t in zip(case.operations, traces, strict=True):
        args = [values[key] for key in op.inputs]
        if op.kind == "COPY_REFERENCE":
            source = clauses[op.root_key]
            _check(
                t.descriptor == source.descriptor
                and t.amount
                == c.SynthesisRational.model_validate(
                    canonical(getattr(source.constraint, op.endpoint))
                )
                and t.claim is None
                and t.passed is None,
                "COPY_REFERENCE_RELATION",
            )
        elif op.kind in {"AFFINE_SAME_UNIT", "REVIEWED_PERIOD_PROJECTION", "FINITE_PERIOD_SUM"}:
            descriptor = canonical(args[0].descriptor)
            if op.temporal:
                _check(
                    op.temporal in rule.calendar_cells
                    or op.temporal == root.sources.request.temporal,
                    "TEMPORAL_AUTHORITY",
                )
                _check(
                    root.sources.request.temporal.kind != "DAY"
                    or op.temporal == root.sources.request.temporal,
                    "UNCOVERED_DAY",
                )
                descriptor["temporal"] = canonical(op.temporal)
            for a in args:
                _check(
                    (canonical(a.descriptor) | {"temporal": None})
                    == (descriptor | {"temporal": None}),
                    "MEASUREMENT_IDENTITY",
                )
            if op.kind == "FINITE_PERIOD_SUM":
                _check(
                    tuple(a.descriptor.temporal for a in args) == rule.calendar_cells
                    and op.temporal == rule.applicability.temporal,
                    "PERIOD_SUM_PARTITION",
                )
                expected = sum(
                    (
                        _fraction(a.amount) * _fraction(co)
                        for a, co in zip(args, op.coefficients, strict=True)
                    ),
                    Fraction(),
                )
            else:
                expected = _fraction(args[0].amount) * _fraction(op.coefficient) + _fraction(
                    op.offset
                )
            _check(
                canonical(t.descriptor) == descriptor
                and t.amount is not None
                and _fraction(t.amount) == expected
                and t.claim is None
                and t.passed is None,
                "FINITE_ARITHMETIC_RELATION",
            )
        elif op.kind == "MAKE_CONSTRAINT":
            claim = t.claim
            _check(claim is not None and t.amount is None and t.passed is None, "CONSTRAINT_TRACE")
            d = canonical(clauses[op.root_key].descriptor) | {"temporal": canonical(op.temporal)}
            _check(
                canonical(claim.descriptor) == d == canonical(t.descriptor)
                and all(canonical(a.descriptor) == d for a in args),
                "CONSTRAINT_DESCRIPTOR",
            )
            _check(
                claim.id == op.id
                and claim.subject == root.sources.request.subject
                and claim.root_key == op.root_key
                and claim.layer == op.layer
                and claim.rule_revision_id == rule.revision_id
                and claim.evidence_id == op.evidence_id,
                "CONSTRAINT_SCOPE",
            )
            endpoints = {
                "RANGE": ("lower", "upper"),
                "MINIMUM": ("lower",),
                "MAXIMUM": ("upper",),
                "TARGET": ("center",),
            }[op.constraint_kind]
            _check(
                claim.constraint.kind == op.constraint_kind
                and all(
                    _fraction(getattr(claim.constraint, name)) == _fraction(arg.amount)
                    for name, arg in zip(endpoints, args, strict=True)
                ),
                "EXACT_CONSTRAINT_RELATION",
            )
        elif op.kind == "SELECT_PRECISION_CASE":
            _check(
                all(a.claim is not None and a.claim.layer == "COMFORT" for a in args),
                "THREE_COMFORT_CASES",
            )
            _check(
                args[0].descriptor == args[1].descriptor == args[2].descriptor
                and _inside(args[2].claim.constraint, args[1].claim.constraint)
                and _inside(args[1].claim.constraint, args[0].claim.constraint),
                "PRECISION_NESTING",
            )
            chosen = args[
                {"RELAXED": 0, "STANDARD": 1, "PRECISION": 2}[policy.inputs.request.precision.value]
            ]
            _check(
                t.descriptor == chosen.descriptor
                and t.amount == chosen.amount
                and t.claim == chosen.claim
                and t.passed is None,
                "PRECISION_SELECTION",
            )
            selected.add(t.claim.id)
        else:
            _check(
                t.descriptor is None and t.amount is None and t.claim is None and t.passed is True,
                "CHECK_TRACE",
            )
            if op.kind == "CHECK_SUBSET":
                _check(
                    args[0].descriptor == args[1].descriptor
                    and _inside(args[0].claim.constraint, args[1].claim.constraint),
                    "AUTHORED_SUBSET",
                )
            else:
                goal, reference = args
                _check(
                    goal.claim.layer in {"GOAL_PROTECTION", "WEEKLY_GOAL"}
                    and goal.descriptor.metric == "ENERGY"
                    and goal.descriptor == reference.descriptor,
                    "DIRECTION_SCOPE",
                )
                low, high = _bounds(goal.claim.constraint)
                center = _fraction(reference.amount)
                predicate = {
                    "UPPER_LT": high is not None and high < center,
                    "UPPER_LE": high is not None and high <= center,
                    "LOWER_GT": low is not None and low > center,
                    "LOWER_GE": low is not None and low >= center,
                    "CONTAINS": (low is None or low <= center) and (high is None or center <= high),
                }[op.comparator]
                _check(predicate, "GOAL_DIRECTION")
                direction.add(goal.claim.id)
        values[op.id] = t
    expected = tuple(
        t.claim
        for t in traces
        if t.claim is not None
        and t.operation_id == t.claim.id
        and (t.claim.layer != "COMFORT" or t.claim.id in selected)
    )
    goals = {x.id for x in expected if x.layer in {"GOAL_PROTECTION", "WEEKLY_GOAL"}}
    _check(
        policy.claims == expected and goals and goals <= direction, "COMPLETE_CLAIMS_AND_DIRECTION"
    )
    _check(set(case.required_claims) <= set(values), "REQUIRED_CLAIMS")


def _coverage(policy, rule, case):
    root = policy.inputs.request.root
    q = root.sources.request
    _check(policy.hard_roots == root.roots, "UNCHANGED_HARD_ROOTS")
    _check(any(x.clause.descriptor.metric == "ENERGY" for x in root.roots), "ENERGY_PURPOSE")
    _check(
        any(
            x.layer == "GOAL_PROTECTION" and x.descriptor.metric == "ENERGY" for x in policy.claims
        ),
        "GOAL_REQUIRED",
    )
    for key in case.daily_root_keys:
        for cell in rule.calendar_cells:
            _check(
                any(
                    x.root_key == key
                    and x.layer == "DAILY_PROTECTION"
                    and x.descriptor.temporal == cell
                    for x in policy.claims
                ),
                "DAILY_REQUIRED",
            )
    for key in case.comfort_root_keys:
        _check(
            any(x.root_key == key and x.layer == "COMFORT" for x in policy.claims),
            "COMFORT_REQUIRED",
        )
    if q.temporal.kind == "DAY":
        _check(
            case.weekly == "NOT_APPLICABLE" and rule.calendar_cells == (q.temporal,), "DAY_PROFILE"
        )
    else:
        _check(
            case.weekly == "REQUIRED"
            and {"WEEKLY_GOAL", "WEEKLY_CENTER"} <= {x.layer for x in policy.claims},
            "WEEKLY_REQUIRED",
        )
    next_start = q.temporal.interval.start
    for cell in rule.calendar_cells:
        _check(
            cell.interval.start == next_start
            and cell.calendar == q.temporal.calendar
            and cell.timezone == q.temporal.timezone,
            "CALENDAR_PARTITION",
        )
        next_start = cell.interval.end
    _check(next_start == q.temporal.interval.end, "TEMPORAL_COVERAGE")
    protections = [x.clause for x in root.roots if x.clause.interpretation == "GUIDELINE_HARD"]
    protections += [
        x
        for x in policy.claims
        if x.layer in {"GOAL_PROTECTION", "DAILY_PROTECTION", "WEEKLY_GOAL"}
    ]
    authored = {t.claim.id: t.claim for t in policy.trace if t.claim is not None}
    for claim in authored.values():
        for protected in protections:
            if protected.descriptor == claim.descriptor:
                if claim.layer in {"COMFORT", "WEEKLY_CENTER"} or protected in [
                    x.clause for x in root.roots
                ]:
                    _check(_inside(claim.constraint, protected.constraint), "CONTAINMENT")
    buckets = {}
    for protected in protections:
        bucket = buckets.setdefault(_hash("descriptor", protected.descriptor), [[], []])
        lo, hi = _bounds(protected.constraint)
        if lo is not None:
            bucket[0].append(lo)
        if hi is not None:
            bucket[1].append(hi)
    for lows, highs in buckets.values():
        _check(not lows or not highs or max(lows) <= min(highs), "HARD_POLICY_CONFLICT")
    req = policy.requirements
    measurement_map = {}
    clauses = {r.clause.root_key: r.clause for r in root.roots}
    for op in case.operations:
        if op.kind == "MAKE_CONSTRAINT" and op.layer == "COMFORT":
            _check(op.root_key in case.comfort_root_keys, "COMFORT_MANIFEST")
            descriptor = n.NutritionRootDescriptor.model_validate(
                canonical(clauses[op.root_key].descriptor) | {"temporal": canonical(op.temporal)}
            )
            measurement = c.NutritionResolutionRequirement(
                root_key=op.root_key, descriptor=descriptor
            )
            measurement_map[_hash("measurement", measurement)] = measurement
    _check(
        req is not None
        and req.subject == q.subject
        and req.root_fingerprint == root.result_fingerprint
        and req.rule_body_fingerprint == _hash("rule", rule)
        and req.case_id == case.id
        and req.temporal == q.temporal
        and req.root_keys == case.comfort_root_keys
        and req.measurements == tuple(item for key, item in sorted(measurement_map.items()))
        and req.environment == q.environment,
        "ACYCLIC_REQUIREMENTS",
    )
    data = canonical(req)
    data.pop("fingerprint")
    _check(req.fingerprint == _hash("requirements", data), "REQUIREMENTS_IDENTITY")
    r = policy.resolution
    _check(
        r is not None
        and r.availability == "AVAILABLE"
        and r.environment == q.environment == "TEST_ONLY"
        and r.requirements_fingerprint == req.fingerprint
        and r.evidence.environment == "TEST_ONLY",
        "RESOLUTION_ADMISSION",
    )
    source = json.loads(r.evidence.body)
    _check(
        source.get("kind") == "TEST_ONLY_RESOLUTION_FIXTURE_V1"
        and source.get("estimator_version") == r.estimator_version == "TEST_ONLY_fixture_v1"
        and source.get("facts") == canonical(r.facts)
        and r.pool_fingerprint == _hash("pool", r.facts),
        "RESOLUTION_PRIMITIVES",
    )
    _check(
        {(f.root_key, _hash("descriptor", f.descriptor)) for f in r.facts}
        == {(m.root_key, _hash("descriptor", m.descriptor)) for m in req.measurements},
        "COMPLETE_RESOLUTION",
    )
    for fact in r.facts:
        preimage = canonical(fact)
        preimage.pop("primitive_fingerprint")
        _check(
            _hash("resolution-primitive", preimage) == fact.primitive_fingerprint
            and fact.portion_step == fact.expected_step
            and _fraction(fact.portion_step) > 0,
            "RESOLUTION_EXPECTATION",
        )
        for claim in policy.claims:
            if (
                claim.layer == "COMFORT"
                and claim.root_key == fact.root_key
                and claim.descriptor == fact.descriptor
            ):
                lo, hi = _bounds(claim.constraint)
                _check(
                    fact.descriptor == claim.descriptor
                    and lo is not None
                    and hi is not None
                    and _fraction(fact.portion_step) <= hi - lo,
                    "RESOLUTION_INSUFFICIENT",
                )


def _aggregate_relations(policy, rule, case):
    """Independent interval image check for a disjoint, single aggregate map."""
    if policy.inputs.request.root.sources.request.temporal.kind == "DAY":
        return
    ancestry, maps = {}, {}
    for op in case.operations:
        key = op.root_key if op.root_key else (ancestry[op.inputs[0]] if op.inputs else None)
        ancestry[op.id] = key
        if op.kind == "FINITE_PERIOD_SUM":
            _check(all(ancestry[x] == key for x in op.inputs), "CROSS_ROOT_AGGREGATE")
            vector = tuple(_fraction(x) for x in op.coefficients)
            _check(key not in maps or maps[key] == vector, "COUPLED_SYSTEM_UNSUPPORTED")
            maps[key] = vector
    for key in case.daily_root_keys:
        _check(key in maps, "EXPLICIT_SUM_MAP_REQUIRED")
        interval_lows, interval_highs = [], []
        for period in rule.calendar_cells:
            limits = [
                _bounds(x.constraint)
                for x in policy.claims
                if x.root_key == key
                and x.descriptor.temporal == period
                and x.layer in {"DAILY_PROTECTION", "GOAL_PROTECTION"}
            ]
            lowers = [x[0] for x in limits if x[0] is not None]
            uppers = [x[1] for x in limits if x[1] is not None]
            interval_lows.append(max(lowers) if lowers else None)
            interval_highs.append(min(uppers) if uppers else None)
        required = [
            _bounds(x.constraint)
            for x in policy.claims
            if x.root_key == key
            and x.layer in {"WEEKLY_GOAL", "GOAL_PROTECTION"}
            and x.descriptor.temporal == rule.applicability.temporal
        ]
        required += [
            _bounds(x.clause.constraint)
            for x in policy.hard_roots
            if x.clause.root_key == key and x.clause.interpretation == "GUIDELINE_HARD"
        ]
        lows = [a for a, b in required if a is not None]
        highs = [b for a, b in required if b is not None]
        if all(x is not None for x in interval_lows):
            lows.append(
                sum((a * b for a, b in zip(maps[key], interval_lows, strict=True)), Fraction())
            )
        if all(x is not None for x in interval_highs):
            highs.append(
                sum((a * b for a, b in zip(maps[key], interval_highs, strict=True)), Fraction())
            )
        _check(not lows or not highs or max(lows) <= min(highs), "AGGREGATE_PROTECTION_CONFLICT")


def validate_nutrition_policy_independently(value):
    request = c.NutritionPolicyValidationInput.model_validate(canonical(value))
    policy = request.policy
    findings = []
    decision = "CONSISTENT"
    try:
        root = policy.inputs.request.root
        report = validate_nutrition_root_independently(
            n.NutritionRootValidationInput(
                root=root, coverage="ROOT_SOURCE_CONSISTENCY_ONLY", derived_claims=()
            )
        )
        _check(report.decision == "CONSISTENT", "INDEPENDENT_ROOT_RECONSTRUCTION")
        if (
            policy.outcome != "AVAILABLE"
            or root.availability != "AVAILABLE"
            or root.eligibility != "SUPPORTED"
            or root.goal_state != "PRESENT"
        ):
            return c.NutritionPolicyValidationReport(
                decision="UNSUPPORTED",
                coverage=request.coverage,
                findings=("COMPLETE_POLICY_UNAVAILABLE",),
                policy_fingerprint=policy.result_fingerprint,
                source_fingerprint=policy.inputs.source_fingerprint,
            )
        _check(policy.environment == root.sources.request.environment, "ENVIRONMENT")
        _check(not policy.reasons, "AVAILABLE_MISSINGNESS")
        body = canonical(policy)
        body.pop("result_fingerprint")
        _check(_hash("policy", body) == policy.result_fingerprint, "POLICY_IDENTITY")
        rule = _source(policy)
        matches = [case for case in rule.cases if case.direction == root.goal_direction]
        _check(len(matches) == 1, "EXACT_RULE_CASE")
        case = matches[0]
        _check(
            not policy.inputs.request.required_claims
            or set(policy.inputs.request.required_claims) == set(case.required_claims),
            "REQUIREDNESS_SUBSTITUTION",
        )
        _relations(policy, rule, case)
        _coverage(policy, rule, case)
        _aggregate_relations(policy, rule, case)
    except (ValueError, KeyError, TypeError, AttributeError, IndexError, ArithmeticError):
        decision = "INCONSISTENT"
        findings.append("POLICY_SEMANTICS_INCONSISTENT")
    return c.NutritionPolicyValidationReport(
        decision=decision,
        coverage=request.coverage,
        findings=tuple(findings),
        policy_fingerprint=policy.result_fingerprint,
        source_fingerprint=policy.inputs.source_fingerprint,
    )


def nutrition_policy_reference(value):
    """Assemble a pin only after a fresh independent policy pass at this boundary.

    No caller-supplied report is accepted. The returned transport is not a transferable
    attestation; another consumer must call validate_nutrition_policy_reference_independently.
    """
    policy = c.NutritionPolicy.model_validate(canonical(value))
    report = validate_nutrition_policy_independently(
        c.NutritionPolicyValidationInput(
            policy=policy, coverage="SYNTHESIS_SOURCE_AND_POLICY_SEMANTICS"
        )
    )
    if report.decision != "CONSISTENT" or policy.inputs.request.precision is None:
        raise ValueError("Fresh independent validation of a complete policy is required")
    return c.NutritionPolicyReference(
        policy=policy,
        validation=report,
        environment=policy.environment,
        precision=policy.inputs.request.precision,
    )


def validate_nutrition_policy_reference_independently(value):
    """Revalidate serialized handoffs; attached reports never bypass fresh checking.

    This is the required admission boundary for a future MTR-008 consumer. It proves
    retained semantic consistency only, with the same offline/scientific non-authority.
    """
    claimed = c.NutritionPolicyReference.model_validate(canonical(value))
    fresh = nutrition_policy_reference(claimed.policy)
    if canonical(claimed) != canonical(fresh):
        raise ValueError("Reference pins or attached report disagree with fresh validation")
    return fresh
