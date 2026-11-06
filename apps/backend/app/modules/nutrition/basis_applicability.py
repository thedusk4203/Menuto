"""Provisional pure same-meaning producer. No Validation import or scientific bridge."""

from app.domain.feature_identity import canonical
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition.basis_projection import project_basis_anchors, stable_scope
from app.modules.nutrition.resolution_estimator import estimate_nutrition_resolution
from app.modules.nutrition.resolution_limits import WorkBudget


class _BasisFailure(ValueError):
    def __init__(self, reason, state="REJECTED"):
        self.reason, self.state = reason, state


def _need(ok, reason, state="REJECTED"):
    if not ok:
        raise _BasisFailure(reason, state)


def _covers(span, wanted):
    return span.start <= wanted.start < wanted.end <= span.end


def replay_basis_artifact(artifact, selection, at, interval, budget):
    """Reconstruct every synthetic event, not just a selected positive publication."""
    a = artifact
    data = canonical(a)
    data.pop("artifact_fingerprint")
    _need(b.basis_hash("artifact", data) == a.artifact_fingerprint, "ARTIFACT_IDENTITY")
    _need(a.database_name.startswith("nrc_test_"), "ENVIRONMENT_MISMATCH")
    _need((a.revision == 1) == (a.previous_artifact_fingerprint is None), "ARTIFACT_LINEAGE")
    people, grants, qualified, reviews, publications = {}, {}, {}, {}, {}
    previous, ids, last_time = None, set(), None

    def head(history, key, moment):
        eligible = [x for x in history.get(key, ()) if x.effective.start <= moment]
        return eligible[-1] if eligible else None

    for index, e in enumerate(a.events, 1):
        budget.charge()
        body = canonical(e)
        body.pop("event_hash")
        _need(
            e.sequence == index
            and e.previous_hash == previous
            and e.id not in ids
            and b.basis_hash("event", body) == e.event_hash
            and (last_time is None or last_time <= e.recorded_at)
            and e.recorded_at <= at,
            "JOURNAL_IDENTITY",
        )
        previous, last_time = e.event_hash, e.recorded_at
        ids.add(e.id)
        if e.kind == "ENROLL":
            _need(
                e.principal not in people
                and e.principal_subject is not None
                and e.capability is None
                and e.qualification is None
                and e.assertion is None
                and e.assertion_fingerprint is None
                and e.review_id is None
                and e.predecessor_publication_id is None,
                "ENROLLMENT_INVALID",
            )
            people[e.principal] = e.principal_subject
            continue
        _need(e.principal in people and e.principal_subject is None, "PRINCIPAL_NOT_ENROLLED")
        if e.kind in {"GRANT", "REVOKE"}:
            _need(
                e.capability is not None
                and e.qualification is None
                and e.assertion is None
                and e.assertion_fingerprint is None
                and e.review_id is None
                and e.predecessor_publication_id is None,
                "CAPABILITY_INVALID",
            )
            grants.setdefault((e.principal, e.scope, e.capability), []).append(e)
            continue
        if e.kind in {"QUALIFY", "DISQUALIFY"}:
            _need(
                e.qualification == "SYMBOLIC_TEST_ONLY_NOT_SCIENTIFIC"
                and e.capability is None
                and e.assertion is None
                and e.review_id is None
                and e.assertion_fingerprint is None
                and e.predecessor_publication_id is None,
                "QUALIFICATION_INVALID",
            )
            qualified.setdefault((e.principal, e.scope), []).append(e)
            continue

        def capable(principal, capability, period):
            g = head(grants, (principal, e.scope, capability), e.recorded_at)
            return g is not None and g.kind == "GRANT" and _covers(g.effective, period)

        def qualification(principal, period):
            q = head(qualified, (principal, e.scope), e.recorded_at)
            return q is not None and q.kind == "QUALIFY" and _covers(q.effective, period)

        _need(e.capability is None and e.qualification is None, "EVENT_SHAPE")
        cap = (
            "TEST_BASIS_REVIEW"
            if e.kind == "REVIEW"
            else (
                "TEST_BASIS_PUBLISH"
                if e.kind in {"PUBLISH", "SUPERSEDE"}
                else "TEST_BASIS_WITHDRAW"
            )
        )
        _need(capable(e.principal, cap, e.effective), "CAPABILITY_UNAVAILABLE")
        g = head(grants, (e.principal, e.scope, cap), e.recorded_at)
        _need(g.effective.start <= e.recorded_at < g.effective.end, "CAPABILITY_UNAVAILABLE")
        if e.kind in {"REVIEW", "PUBLISH", "SUPERSEDE"}:
            _need(qualification(e.principal, e.effective), "SOURCE_UNQUALIFIED", "UNAVAILABLE")
            q = head(qualified, (e.principal, e.scope), e.recorded_at)
            _need(
                q.effective.start <= e.recorded_at < q.effective.end,
                "SOURCE_UNQUALIFIED",
                "UNAVAILABLE",
            )
        if e.kind == "REVIEW":
            _need(
                e.assertion is not None
                and e.assertion_fingerprint == b.basis_hash("assertion", e.assertion)
                and e.scope == e.assertion.scope_id
                and e.effective == e.assertion.effective
                and e.review_id is None
                and e.predecessor_publication_id is None,
                "REVIEW_BINDING",
            )
            reviews[e.id] = e
        elif e.kind in {"PUBLISH", "SUPERSEDE"}:
            r = reviews.get(e.review_id)
            _need(
                r is not None
                and e.assertion is None
                and r.scope == e.scope
                and e.assertion_fingerprint == r.assertion_fingerprint
                and e.effective == r.effective
                and people[e.principal] != people[r.principal],
                "REVIEW_BINDING",
            )
            _need(
                capable(r.principal, "TEST_BASIS_REVIEW", e.effective)
                and qualification(r.principal, e.effective),
                "SOURCE_UNQUALIFIED",
                "UNAVAILABLE",
            )
            _need(
                (e.kind == "PUBLISH") == (e.predecessor_publication_id is None),
                "PUBLICATION_LINEAGE",
            )
            if e.kind == "SUPERSEDE":
                old = publications.get(e.predecessor_publication_id)
                _need(old is not None and old[0].scope == e.scope, "PUBLICATION_LINEAGE")
            publications[e.id] = (e, r.assertion, r.principal)
        else:
            _need(
                e.assertion is None
                and e.review_id is None
                and e.predecessor_publication_id in publications,
                "PUBLICATION_LINEAGE",
            )
            old = publications[e.predecessor_publication_id]
            _need(
                old[0].scope == e.scope and e.assertion_fingerprint == old[0].assertion_fingerprint,
                "PUBLICATION_LINEAGE",
            )
    selected = publications.get(selection.publication_id)
    _need(selected is not None, "PUBLICATION_MISSING", "UNAVAILABLE")
    pub, assertion, reviewer = selected
    for identity, (other, alternative, _) in publications.items():
        if (
            identity != pub.id
            and other.predecessor_publication_id != pub.id
            and pub.predecessor_publication_id != identity
            and alternative.subject == assertion.subject
            and alternative.stable_scope_fingerprint == assertion.stable_scope_fingerprint
            and set(alternative.required_keys) & set(assertion.required_keys)
            and other.effective.start < pub.effective.end
            and pub.effective.start < other.effective.end
        ):
            raise _BasisFailure("PUBLICATION_AMBIGUOUS")
    _need(
        (assertion.id, assertion.revision)
        == (selection.assertion_id, selection.assertion_revision),
        "ASSERTION_SELECTION",
    )
    _need(_covers(pub.effective, interval), "TEMPORAL_COVERAGE_MISSING", "UNSUPPORTED")
    for e in a.events:
        if e.predecessor_publication_id == pub.id:
            if e.kind == "WITHDRAW":
                raise _BasisFailure("PUBLICATION_WITHDRAWN", "UNAVAILABLE")
            cutoff = e.effective.start
            _need(at < cutoff, "PUBLICATION_RETIRED", "UNAVAILABLE")
            _need(
                not interval.start < cutoff < interval.end, "CROSS_VERSION_INTERVAL", "UNSUPPORTED"
            )
    for person in (pub.principal, reviewer):
        q = head(qualified, (person, pub.scope), at)
        _need(
            q is not None
            and q.kind == "QUALIFY"
            and _covers(q.effective, interval)
            and q.effective.start <= at < q.effective.end,
            "SOURCE_UNQUALIFIED",
            "UNAVAILABLE",
        )
    reader = head(grants, (selection.reader_principal, pub.scope, "TEST_BASIS_SOURCE_READ"), at)
    _need(
        reader is not None
        and reader.kind == "GRANT"
        and _covers(reader.effective, interval)
        and reader.effective.start <= at < reader.effective.end,
        "READER_REVOKED",
        "UNAVAILABLE",
    )
    return assertion


def _resolve(s, budget):
    f, a, nre = s.frame, s.artifact, s.nre
    data = canonical(s)
    data.pop("source_fingerprint")
    _need(b.basis_hash("sources", data) == s.source_fingerprint, "SOURCE_IDENTITY")
    _need(
        (
            f.registry_id,
            f.registry_revision,
            f.artifact_fingerprint,
            f.deployment,
            f.issuer_epoch,
            f.database_oid,
            f.database_name,
        )
        == (
            a.registry_id,
            a.revision,
            a.artifact_fingerprint,
            a.deployment,
            a.issuer_epoch,
            a.database_oid,
            a.database_name,
        ),
        "SOURCE_CUT_INCOHERENT",
    )
    nf = nre.sources.frame
    _need(
        (a.database_oid, a.database_name) == (nf.fixture_database_oid, nf.fixture_database_name)
        and f.started_at <= nf.started_at <= nf.completed_at <= f.completed_at,
        "SOURCE_CUT_INCOHERENT",
    )
    from_scope = canonical(nre.sources.scope)
    from_scope.pop("requirement_fingerprint")
    from_scope["contract_version"] = "nutrition-resolution-scope-request.v1"
    _need(from_scope == canonical(s.selectors.nre_scope), "SCOPE_IDENTITY")
    fresh = estimate_nutrition_resolution(nre.sources)
    _need(fresh == nre.estimate, "NRE_RESULT_FORGED")
    _need(fresh.availability == "AVAILABLE", "NRE_UNAVAILABLE", "UNAVAILABLE")
    try:
        anchors = project_basis_anchors(nre)
    except ValueError as exc:
        if str(exc) in {"UNSUPPORTED_LINEAGE", "CONVERSION_NOT_SUPPORTED"}:
            raise _BasisFailure(str(exc), "UNSUPPORTED") from exc
        raise
    _need(anchors == s.anchors and not s.absences, "REQUIRED_ANCHOR_MISSING")
    req = nre.sources.scope.root_request
    assertion = replay_basis_artifact(a, s.selectors, f.completed_at, req.temporal.interval, budget)
    _need(
        assertion.subject == req.subject
        and assertion.stable_scope_fingerprint == stable_scope(nre.sources),
        "SUBJECT_SCOPE_MISMATCH",
    )
    _need(
        (assertion.scope_id, assertion.scope_version, assertion.protocol_fingerprint)
        == (req.scope_id, req.scope_version, req.protocol_fingerprint),
        "POPULATION_SCOPE_MISMATCH",
        "NOT_APPLICABLE",
    )
    _need(
        assertion.required_keys == tuple(x.key for x in anchors)
        and assertion.original_sources
        == tuple(sorted({x.original_source_fingerprint for x in anchors}))
        and assertion.original_evidence == tuple(sorted({x.evidence_fingerprint for x in anchors})),
        "ORIGINAL_SOURCE_MISMATCH",
    )
    materials = b.basis_hash(
        "material-references",
        dict(
            recipes=nre.sources.recipes,
            references=nre.sources.references,
            slots=nre.sources.scope.slots,
        ),
    )
    _need(assertion.material_reference_fingerprint == materials, "MATERIAL_BASIS_MISMATCH")
    _need(len(assertion.meanings) == len(anchors), "REQUIRED_ANCHOR_MISSING")
    witnesses = []
    for anchor, meaning in zip(anchors, assertion.meanings, strict=True):
        budget.charge()
        _need(anchor.meaning_preimage is not None, "MEANING_MISSING", "UNAVAILABLE")
        try:
            original = b.parse_basis(anchor.meaning_preimage, b.MeasurementMeaningV1, 16384)
        except ValueError as exc:
            raise _BasisFailure("CONVERSION_NOT_SUPPORTED", "UNSUPPORTED") from exc
        _need(original == meaning, "ORIGINAL_MEANING_CONTRADICTION")
        _need(original.meaning != "UNSPECIFIED_V1", "MEANING_MISSING", "UNAVAILABLE")
        _need(
            original.meaning == "PLANNED_INGREDIENT_INPUT_V1",
            "CONVERSION_NOT_SUPPORTED",
            "UNSUPPORTED",
        )
        _need(
            original.interpretation_id == "NRE_EXACT_PLANNED_INPUT"
            and original.interpretation_version == "v1",
            "MEANING_VERSION",
            "UNSUPPORTED",
        )
        _need(original.descriptor == anchor.descriptor, "UNIT_TEMPORAL_MISMATCH")
        bases = tuple(sorted({x.basis for v in fresh.configurations for x in v.ingredients}))
        _need(original.material_bases == bases, "MATERIAL_BASIS_MISMATCH", "NOT_APPLICABLE")
        periods = [p for p in fresh.periods if p.temporal == anchor.descriptor.temporal]
        _need(len(periods) == 1 and periods[0].vectors, "TEMPORAL_COVERAGE_MISSING", "UNAVAILABLE")
        witnesses.append(
            b.BasisComparisonWitnessV1(
                anchor_fingerprint=anchor.anchor_fingerprint,
                period_fingerprint=b.basis_hash("period", periods[0]),
                component=anchor.descriptor.metric,
                assertion_fingerprint=b.basis_hash("assertion", assertion),
                original_meaning_fingerprint=b.basis_hash("meaning", original),
            )
        )
    return tuple(witnesses)


def resolve_basis_applicability(retained_sources):
    s = b.parse_basis(retained_sources, b.BasisApplicabilitySourcesV1)
    try:
        witnesses = _resolve(s, WorkBudget(s.selectors.max_work))
        state, reasons = "APPLICABLE_TEST_ONLY", ()
    except _BasisFailure as exc:
        state, reasons, witnesses = exc.state, (exc.reason,), ()
    except (ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
        state = "RESOURCE_EXCEEDED" if str(exc).startswith("RESOURCE_EXCEEDED") else "REJECTED"
        reasons, witnesses = (
            ("RESOURCE_LIMIT" if state == "RESOURCE_EXCEEDED" else "SOURCE_INVALID",),
            (),
        )
    body = dict(
        outcome=state,
        reasons=reasons,
        witnesses=witnesses,
        required_anchor_fingerprints=tuple(x.anchor_fingerprint for x in s.anchors),
        source_fingerprint=s.source_fingerprint,
    )
    model = b.BasisApplicabilityResultV1(**body, result_fingerprint="0" * 64)
    data = canonical(model)
    data.pop("result_fingerprint")
    return b.BasisApplicabilityResultV1(**data, result_fingerprint=b.basis_hash("result", data))


def basis_handoff(sources):
    """Unverified terminal transport. Never a validation/admission certificate."""
    s = b.parse_basis(sources, b.BasisApplicabilitySourcesV1)
    return b.BasisApplicabilityHandoffV1(sources=s, result=resolve_basis_applicability(s))
