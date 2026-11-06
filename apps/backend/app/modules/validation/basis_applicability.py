"""Independent basis reconstruction; no producer, projection or fixture-registry oracle."""

import json

from app.domain.feature_identity import canonical
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition.resolution_limits import WorkBudget, ingest
from app.modules.validation.nutrition_resolution import check_nutrition_resolution_independently
from app.modules.validation.nutrition_resolution_authority import verify_resolution_rule_sources


class _Invalid(ValueError):
    def __init__(self, code, state="REJECTED"):
        self.code = code
        self.state = "UNSUPPORTED" if code == "UNSUPPORTED_LINEAGE" else state


def _assert(ok, code, state="REJECTED"):
    if not ok:
        raise _Invalid(code, state)


def _identity(kind, model, field):
    data = canonical(model)
    data.pop(field)
    return b.basis_hash(kind, data)


def _original(rows, name):
    matches = []
    for evidence in rows:
        try:
            data = ingest(evidence.body, 16384)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or data.get("schema") != "test-only.measurement-meaning.v1":
            continue
        _assert(
            set(data) == {"schema", "environment", "claims"} and data["environment"] == "TEST_ONLY",
            "ENVIRONMENT_MISMATCH",
        )
        _assert(
            isinstance(data["claims"], list) and len(data["claims"]) <= 128, "RESOURCE_EXCEEDED"
        )
        for item in data["claims"]:
            _assert(set(item) == {"key", "meaning"}, "CONVERSION_NOT_SUPPORTED")
            if item["key"] == name:
                matches.append(json.dumps(item["meaning"], separators=(",", ":"), sort_keys=True))
    _assert(len(matches) <= 1, "ORIGINAL_MEANING_CONTRADICTION")
    return next(iter(matches), None)


def _anchors(s):
    """Independent finite lineage walk, retaining ALL constraint branches and original roots."""
    ns = s.nre.sources
    rule = verify_resolution_rule_sources(ns.synthesis_sources)
    root = ns.synthesis_sources.request.root
    clauses = {r.clause.root_key: r.clause for r in root.roots}
    cases = [c for c in rule.cases if c.direction == root.goal_direction]
    _assert(len(cases) == 1 and bool(clauses), "UNSUPPORTED_LINEAGE")
    case = cases[0]
    originals = [
        x.command.body.guideline
        for x in root.sources.sources
        if x.command.body.kind == "DRAFT"
        and x.command.body.guideline.revision_id == root.sources.request.guideline_revision_id
    ]
    _assert(len(originals) == 1, "SOURCE_INVALID")
    stable = canonical(ns.scope)
    stable.update(
        contract_version="nutrition-resolution-scope-request.v1", requirement_fingerprint=None
    )
    scope_hash = b.basis_hash("stable-scope", stable)
    rows, nodes = [], {}

    def record(name, layer, key, descriptor, evidence, source_hash):
        data = dict(
            key=name,
            layer=layer,
            root_key=key,
            descriptor=descriptor,
            subject=ns.scope.subject,
            original_source_fingerprint=source_hash,
            evidence_fingerprint=b.basis_hash("original-evidence", evidence),
            meaning_preimage=_original(evidence, name),
            stable_scope_fingerprint=scope_hash,
            root_fingerprint=root.result_fingerprint,
            requirement_fingerprint=ns.requirements.fingerprint,
            nre_source_fingerprint=ns.source_fingerprint,
            nre_result_fingerprint=s.nre.estimate.result_fingerprint,
        )
        rows.append(b.BasisClaimAnchorV1(**data, anchor_fingerprint=b.basis_hash("anchor", data)))

    for key in sorted(clauses):
        clause = clauses[key]
        record(
            "root:" + key,
            clause.interpretation,
            key,
            clause.descriptor,
            originals[0].evidence_manifest,
            root.sources.request.guideline_body_fingerprint,
        )
    for instruction in case.operations:
        _assert(
            instruction.id not in nodes and all(k in nodes for k in instruction.inputs),
            "UNSUPPORTED_LINEAGE",
        )
        operands = [nodes[k] for k in instruction.inputs]
        kind = instruction.kind
        if kind == "COPY_REFERENCE":
            clause = clauses.get(instruction.root_key)
            _assert(
                clause is not None and hasattr(clause.constraint, instruction.endpoint),
                "UNSUPPORTED_LINEAGE",
            )
            metadata = dict(key=instruction.root_key, descriptor=clause.descriptor, form="ENDPOINT")
        elif kind == "MAKE_CONSTRAINT":
            _assert(instruction.root_key in clauses, "UNSUPPORTED_LINEAGE")
            desc = n.NutritionRootDescriptor.model_validate(
                canonical(clauses[instruction.root_key].descriptor)
                | {"temporal": canonical(instruction.temporal)}
            )
            _assert(
                all(
                    x == dict(key=instruction.root_key, descriptor=desc, form="ENDPOINT")
                    for x in operands
                ),
                "UNSUPPORTED_LINEAGE",
            )
            metadata = dict(key=instruction.root_key, descriptor=desc, form="CLAIM")
            record(
                "rule:" + case.id + ":" + instruction.id,
                instruction.layer,
                instruction.root_key,
                desc,
                rule.evidence,
                ns.requirements.rule_body_fingerprint,
            )
        elif kind == "SELECT_PRECISION_CASE":
            _assert(
                all(x == operands[0] for x in operands) and operands[0]["form"] == "CLAIM",
                "UNSUPPORTED_LINEAGE",
            )
            metadata = operands[0]
        elif kind in {"CHECK_SUBSET", "CHECK_DIRECTION"}:
            first, second = operands
            _assert(
                first["key"] == second["key"]
                and first["descriptor"] == second["descriptor"]
                and first["form"] == "CLAIM"
                and (kind != "CHECK_SUBSET" or second["form"] == "CLAIM"),
                "UNSUPPORTED_LINEAGE",
            )
            metadata = first | {"form": "RELATION"}
        else:
            _assert(
                kind in {"AFFINE_SAME_UNIT", "FINITE_PERIOD_SUM", "REVIEWED_PERIOD_PROJECTION"},
                "UNSUPPORTED_LINEAGE",
            )
            first = operands[0]
            _assert(
                first["form"] == "ENDPOINT"
                and all(x["key"] == first["key"] and x["form"] == "ENDPOINT" for x in operands),
                "UNSUPPORTED_LINEAGE",
            )
            metadata = first
            if kind != "AFFINE_SAME_UNIT":
                _assert(
                    all(
                        (canonical(x["descriptor"]) | {"temporal": None})
                        == (canonical(first["descriptor"]) | {"temporal": None})
                        for x in operands
                    ),
                    "UNSUPPORTED_LINEAGE",
                )
                _assert(
                    instruction.temporal in rule.calendar_cells
                    or instruction.temporal == rule.applicability.temporal,
                    "UNSUPPORTED_LINEAGE",
                )
                if kind == "FINITE_PERIOD_SUM":
                    _assert(
                        tuple(x["descriptor"].temporal for x in operands) == rule.calendar_cells
                        and instruction.temporal == rule.applicability.temporal,
                        "UNSUPPORTED_LINEAGE",
                    )
                metadata = first | {
                    "descriptor": n.NutritionRootDescriptor.model_validate(
                        canonical(first["descriptor"])
                        | {"temporal": canonical(instruction.temporal)}
                    )
                }
        nodes[instruction.id] = metadata
    _assert(
        all(k in nodes and nodes[k]["form"] == "CLAIM" for k in case.required_claims),
        "REQUIRED_ANCHOR_MISSING",
    )
    _assert(1 <= len(rows) <= 128, "RESOURCE_EXCEEDED")
    return tuple(sorted(rows, key=lambda r: r.key)), scope_hash


def _journal(s, work):
    """Independent history fold, separation of duties and lifecycle over the full artifact."""
    artifact, selectors, now = s.artifact, s.selectors, s.frame.completed_at
    requested = s.nre.sources.scope.root_request.temporal.interval
    _assert(
        _identity("artifact", artifact, "artifact_fingerprint") == artifact.artifact_fingerprint,
        "ARTIFACT_IDENTITY",
    )
    _assert(artifact.database_name.startswith("nrc_test_"), "ENVIRONMENT_MISMATCH")
    _assert(
        (artifact.revision == 1) == (artifact.previous_artifact_fingerprint is None),
        "ARTIFACT_LINEAGE",
    )
    identities, permissions, qualifications, review_events, published = {}, {}, {}, {}, {}
    seen, preceding, recorded = set(), None, None

    def authority_at(journal, identity, time):
        result = None
        for row in journal.get(identity, ()):
            if row.effective.start <= time:
                result = row
        return result

    def covers(a, z):
        return a.start <= z.start < z.end <= a.end

    for pos, event in enumerate(artifact.events):
        work.charge()
        _assert(
            event.sequence == pos + 1
            and event.previous_hash == preceding
            and event.id not in seen
            and _identity("event", event, "event_hash") == event.event_hash
            and (recorded is None or event.recorded_at >= recorded)
            and event.recorded_at <= now,
            "JOURNAL_IDENTITY",
        )
        seen.add(event.id)
        preceding, recorded = event.event_hash, event.recorded_at
        if event.kind == "ENROLL":
            _assert(
                event.principal not in identities
                and event.principal_subject is not None
                and all(
                    x is None
                    for x in (
                        event.capability,
                        event.qualification,
                        event.assertion,
                        event.assertion_fingerprint,
                        event.review_id,
                        event.predecessor_publication_id,
                    )
                ),
                "ENROLLMENT_INVALID",
            )
            identities[event.principal] = event.principal_subject
            continue
        _assert(
            event.principal in identities and event.principal_subject is None,
            "PRINCIPAL_NOT_ENROLLED",
        )
        key = event.principal, event.scope
        if event.kind in {"GRANT", "REVOKE"}:
            _assert(
                event.capability is not None
                and all(
                    x is None
                    for x in (
                        event.qualification,
                        event.assertion,
                        event.assertion_fingerprint,
                        event.review_id,
                        event.predecessor_publication_id,
                    )
                ),
                "CAPABILITY_INVALID",
            )
            permissions.setdefault(key + (event.capability,), []).append(event)
            continue
        if event.kind in {"QUALIFY", "DISQUALIFY"}:
            _assert(
                event.qualification == "SYMBOLIC_TEST_ONLY_NOT_SCIENTIFIC"
                and all(
                    x is None
                    for x in (
                        event.capability,
                        event.assertion,
                        event.assertion_fingerprint,
                        event.review_id,
                        event.predecessor_publication_id,
                    )
                ),
                "QUALIFICATION_INVALID",
            )
            qualifications.setdefault(key, []).append(event)
            continue
        _assert(event.capability is None and event.qualification is None, "EVENT_SHAPE")
        cap = {
            "REVIEW": "TEST_BASIS_REVIEW",
            "PUBLISH": "TEST_BASIS_PUBLISH",
            "SUPERSEDE": "TEST_BASIS_PUBLISH",
            "WITHDRAW": "TEST_BASIS_WITHDRAW",
            "RETIRE": "TEST_BASIS_WITHDRAW",
        }[event.kind]
        grant = authority_at(permissions, key + (cap,), event.recorded_at)
        _assert(
            grant is not None
            and grant.kind == "GRANT"
            and covers(grant.effective, event.effective)
            and grant.effective.start <= event.recorded_at < grant.effective.end,
            "CAPABILITY_UNAVAILABLE",
        )
        if event.kind in {"REVIEW", "PUBLISH", "SUPERSEDE"}:
            qualification = authority_at(qualifications, key, event.recorded_at)
            _assert(
                qualification is not None
                and qualification.kind == "QUALIFY"
                and covers(qualification.effective, event.effective)
                and qualification.effective.start
                <= event.recorded_at
                < qualification.effective.end,
                "SOURCE_UNQUALIFIED",
                "UNAVAILABLE",
            )
        if event.kind == "REVIEW":
            _assert(
                event.assertion is not None
                and event.assertion_fingerprint == b.basis_hash("assertion", event.assertion)
                and event.scope == event.assertion.scope_id
                and event.effective == event.assertion.effective
                and event.review_id is None
                and event.predecessor_publication_id is None,
                "REVIEW_BINDING",
            )
            review_events[event.id] = event
        elif event.kind in {"PUBLISH", "SUPERSEDE"}:
            review = review_events.get(event.review_id)
            _assert(
                review is not None
                and event.assertion is None
                and review.scope == event.scope
                and review.assertion_fingerprint == event.assertion_fingerprint
                and review.effective == event.effective
                and identities[review.principal] != identities[event.principal],
                "REVIEW_BINDING",
            )
            review_grant = authority_at(
                permissions, (review.principal, event.scope, "TEST_BASIS_REVIEW"), event.recorded_at
            )
            review_qual = authority_at(
                qualifications, (review.principal, event.scope), event.recorded_at
            )
            _assert(
                review_grant is not None
                and review_grant.kind == "GRANT"
                and covers(review_grant.effective, event.effective)
                and review_qual is not None
                and review_qual.kind == "QUALIFY"
                and covers(review_qual.effective, event.effective),
                "SOURCE_UNQUALIFIED",
                "UNAVAILABLE",
            )
            _assert(
                (event.kind == "PUBLISH") == (event.predecessor_publication_id is None),
                "PUBLICATION_LINEAGE",
            )
            if event.kind == "SUPERSEDE":
                prior = published.get(event.predecessor_publication_id)
                _assert(prior is not None and prior[0].scope == event.scope, "PUBLICATION_LINEAGE")
            published[event.id] = event, review.assertion, review.principal
        else:
            _assert(
                event.assertion is None
                and event.review_id is None
                and event.predecessor_publication_id in published,
                "PUBLICATION_LINEAGE",
            )
            prior = published[event.predecessor_publication_id][0]
            _assert(
                prior.scope == event.scope
                and prior.assertion_fingerprint == event.assertion_fingerprint,
                "PUBLICATION_LINEAGE",
            )
    _assert(selectors.publication_id in published, "PUBLICATION_MISSING", "UNAVAILABLE")
    chosen, assertion, reviewer = published[selectors.publication_id]
    for identity, (other, alternative, _) in published.items():
        if (
            identity != chosen.id
            and other.predecessor_publication_id != chosen.id
            and chosen.predecessor_publication_id != identity
            and alternative.subject == assertion.subject
            and alternative.stable_scope_fingerprint == assertion.stable_scope_fingerprint
            and set(alternative.required_keys) & set(assertion.required_keys)
            and other.effective.start < chosen.effective.end
            and chosen.effective.start < other.effective.end
        ):
            raise _Invalid("PUBLICATION_AMBIGUOUS")
    _assert(
        (assertion.id, assertion.revision)
        == (selectors.assertion_id, selectors.assertion_revision),
        "ASSERTION_SELECTION",
    )
    _assert(covers(chosen.effective, requested), "TEMPORAL_COVERAGE_MISSING", "UNSUPPORTED")
    for event in artifact.events:
        if event.predecessor_publication_id == chosen.id:
            _assert(event.kind != "WITHDRAW", "PUBLICATION_WITHDRAWN", "UNAVAILABLE")
            _assert(now < event.effective.start, "PUBLICATION_RETIRED", "UNAVAILABLE")
            _assert(
                not requested.start < event.effective.start < requested.end,
                "CROSS_VERSION_INTERVAL",
                "UNSUPPORTED",
            )
    for name in (chosen.principal, reviewer):
        q = authority_at(qualifications, (name, chosen.scope), now)
        _assert(
            q is not None
            and q.kind == "QUALIFY"
            and covers(q.effective, requested)
            and q.effective.start <= now < q.effective.end,
            "SOURCE_UNQUALIFIED",
            "UNAVAILABLE",
        )
    g = authority_at(
        permissions, (selectors.reader_principal, chosen.scope, "TEST_BASIS_SOURCE_READ"), now
    )
    _assert(
        g is not None
        and g.kind == "GRANT"
        and covers(g.effective, requested)
        and g.effective.start <= now < g.effective.end,
        "READER_REVOKED",
        "UNAVAILABLE",
    )
    return assertion


def _reconstruct(s, budget):
    _assert(
        _identity("sources", s, "source_fingerprint") == s.source_fingerprint, "SOURCE_IDENTITY"
    )
    artifact, frame, nf = s.artifact, s.frame, s.nre.sources.frame
    for attr in (
        "registry_id",
        "deployment",
        "issuer_epoch",
        "database_oid",
        "database_name",
        "artifact_fingerprint",
    ):
        _assert(getattr(artifact, attr) == getattr(frame, attr), "SOURCE_CUT_INCOHERENT")
    _assert(
        frame.registry_revision == artifact.revision
        and (artifact.database_oid, artifact.database_name)
        == (nf.fixture_database_oid, nf.fixture_database_name)
        and frame.started_at <= nf.started_at <= nf.completed_at <= frame.completed_at,
        "SOURCE_CUT_INCOHERENT",
    )
    scope = canonical(s.nre.sources.scope)
    scope.pop("requirement_fingerprint")
    scope["contract_version"] = "nutrition-resolution-scope-request.v1"
    _assert(scope == canonical(s.selectors.nre_scope), "SCOPE_IDENTITY")
    report = check_nutrition_resolution_independently(s.nre.sources, s.nre.estimate)
    _assert(report.decision == "CONSISTENT", "NRE_RESULT_FORGED")
    _assert(s.nre.estimate.availability == "AVAILABLE", "NRE_UNAVAILABLE", "UNAVAILABLE")
    anchors, scope_hash = _anchors(s)
    _assert(anchors == s.anchors and not s.absences, "REQUIRED_ANCHOR_MISSING")
    assertion = _journal(s, budget)
    req = s.nre.sources.scope.root_request
    _assert(
        assertion.subject == req.subject and assertion.stable_scope_fingerprint == scope_hash,
        "SUBJECT_SCOPE_MISMATCH",
    )
    _assert(
        (assertion.scope_id, assertion.scope_version, assertion.protocol_fingerprint)
        == (req.scope_id, req.scope_version, req.protocol_fingerprint),
        "POPULATION_SCOPE_MISMATCH",
        "NOT_APPLICABLE",
    )
    _assert(
        assertion.required_keys == tuple(x.key for x in anchors)
        and assertion.original_sources
        == tuple(sorted(set(x.original_source_fingerprint for x in anchors)))
        and assertion.original_evidence
        == tuple(sorted(set(x.evidence_fingerprint for x in anchors))),
        "ORIGINAL_SOURCE_MISMATCH",
    )
    food = dict(
        recipes=s.nre.sources.recipes,
        references=s.nre.sources.references,
        slots=s.nre.sources.scope.slots,
    )
    _assert(
        assertion.material_reference_fingerprint == b.basis_hash("material-references", food),
        "MATERIAL_BASIS_MISMATCH",
    )
    _assert(len(assertion.meanings) == len(anchors), "REQUIRED_ANCHOR_MISSING")
    witnesses = []
    for index, anchor in enumerate(anchors):
        budget.charge()
        _assert(anchor.meaning_preimage is not None, "MEANING_MISSING", "UNAVAILABLE")
        try:
            meaning = b.parse_basis(anchor.meaning_preimage, b.MeasurementMeaningV1, 16384)
        except ValueError as exc:
            raise _Invalid("CONVERSION_NOT_SUPPORTED", "UNSUPPORTED") from exc
        _assert(meaning == assertion.meanings[index], "ORIGINAL_MEANING_CONTRADICTION")
        _assert(meaning.meaning != "UNSPECIFIED_V1", "MEANING_MISSING", "UNAVAILABLE")
        _assert(
            meaning.meaning == "PLANNED_INGREDIENT_INPUT_V1",
            "CONVERSION_NOT_SUPPORTED",
            "UNSUPPORTED",
        )
        _assert(
            (meaning.interpretation_id, meaning.interpretation_version)
            == ("NRE_EXACT_PLANNED_INPUT", "v1"),
            "MEANING_VERSION",
            "UNSUPPORTED",
        )
        _assert(meaning.descriptor == anchor.descriptor, "UNIT_TEMPORAL_MISMATCH")
        bases = sorted(
            set(
                ingredient.basis
                for config in s.nre.estimate.configurations
                for ingredient in config.ingredients
            )
        )
        _assert(list(meaning.material_bases) == bases, "MATERIAL_BASIS_MISMATCH", "NOT_APPLICABLE")
        periods = [x for x in s.nre.estimate.periods if x.temporal == anchor.descriptor.temporal]
        _assert(
            len(periods) == 1 and bool(periods[0].vectors),
            "TEMPORAL_COVERAGE_MISSING",
            "UNAVAILABLE",
        )
        witnesses.append(
            b.BasisComparisonWitnessV1(
                anchor_fingerprint=anchor.anchor_fingerprint,
                period_fingerprint=b.basis_hash("period", periods[0]),
                component=anchor.descriptor.metric,
                assertion_fingerprint=b.basis_hash("assertion", assertion),
                original_meaning_fingerprint=b.basis_hash("meaning", meaning),
            )
        )
    return tuple(witnesses)


def check_basis_applicability_independently(retained_sources, claimed_result):
    reconstructed = None
    try:
        s = b.parse_basis(retained_sources, b.BasisApplicabilitySourcesV1)
        claimed = b.parse_basis(claimed_result, b.BasisApplicabilityResultV1)
        try:
            witnesses = _reconstruct(s, WorkBudget(s.selectors.max_work))
            outcome, reasons = "APPLICABLE_TEST_ONLY", ()
        except _Invalid as exc:
            outcome, reasons, witnesses = exc.state, (exc.code,), ()
        except (ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
            outcome = (
                "RESOURCE_EXCEEDED" if str(exc).startswith("RESOURCE_EXCEEDED") else "REJECTED"
            )
            reasons, witnesses = (
                ("RESOURCE_LIMIT" if outcome == "RESOURCE_EXCEEDED" else "SOURCE_INVALID",),
                (),
            )
        expected = b.BasisApplicabilityResultV1(
            outcome=outcome,
            reasons=reasons,
            witnesses=witnesses,
            required_anchor_fingerprints=tuple(x.anchor_fingerprint for x in s.anchors),
            source_fingerprint=s.source_fingerprint,
            result_fingerprint="0" * 64,
        )
        reconstructed = _identity("result", expected, "result_fingerprint")
        _assert(
            outcome != "REJECTED"
            and canonical(claimed) == (canonical(expected) | {"result_fingerprint": reconstructed}),
            "BASIS_SEMANTICS_INCONSISTENT",
        )
        return b.BasisApplicabilityCheckV1(
            decision="CONSISTENT", findings=(), reconstructed_result_fingerprint=reconstructed
        )
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        return b.BasisApplicabilityCheckV1(
            decision="INCONSISTENT",
            findings=("BASIS_SEMANTICS_INCONSISTENT",),
            reconstructed_result_fingerprint=reconstructed,
        )


def check_basis_handoff_independently(untrusted_handoff):
    try:
        value = b.parse_basis(untrusted_handoff, b.BasisApplicabilityHandoffV1)
        return check_basis_applicability_independently(value.sources, value.result)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        return b.BasisApplicabilityCheckV1(
            decision="INCONSISTENT",
            findings=("HANDOFF_INVALID",),
            reconstructed_result_fingerprint=None,
        )
