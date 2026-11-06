"""Privileged TEST_ONLY fixture authors. No installer runs at application startup."""

import json
from pathlib import Path
from uuid import uuid4

from app.domain.feature_identity import canonical
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition.basis_projection import project_basis_anchors, stable_scope
from nutrition_root_fixtures import authority_interval


def meaning(descriptor, token="PLANNED_INGREDIENT_INPUT_V1"):
    return b.MeasurementMeaningV1(
        meaning=token,
        interpretation_id="NRE_EXACT_PLANNED_INPUT",
        interpretation_version="v1",
        material_bases=("EP_RAW_G",),
        descriptor=descriptor,
    )


def proof(claims):
    body = json.dumps(
        dict(
            schema="test-only.measurement-meaning.v1",
            environment="TEST_ONLY",
            claims=[dict(key=k, meaning=canonical(m)) for k, m in claims],
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    return b.n.NutritionSourceEvidence(
        # Frozen SQL checks canonical order using the database collation. A lowercase
        # suffix after the existing "algebra" ID agrees with Python/C and en_US order.
        evidence_id="TEST_ONLY_zmba_" + uuid4().hex,
        version="TEST_ONLY_v1",
        environment="TEST_ONLY",
        purpose="TEST_ONLY invented same-meaning fixture, NOT scientific evidence",
        body=body,
        body_fingerprint=b.n.nutrition_root_hash("nutrition.evidence-body.v1", body),
    )


def original_guideline(builder):
    def build(*args, **kwargs):
        body = builder(*args, **kwargs)
        evidence = proof([("root:" + r.root_key, meaning(r.descriptor)) for r in body.clauses])
        return type(body).model_validate(
            canonical(body)
            | {
                "evidence_manifest": canonical(
                    tuple(sorted((*body.evidence_manifest, evidence), key=lambda x: x.evidence_id))
                )
            }
        )

    return build


def original_rule(builder):
    def build(*args, **kwargs):
        body = builder(*args, **kwargs)
        clauses = {r.clause.root_key: r.clause for r in args[0].roots}
        claims = []
        for case in body.cases:
            for op in case.operations:
                if op.kind == "MAKE_CONSTRAINT":
                    desc = b.n.NutritionRootDescriptor.model_validate(
                        canonical(clauses[op.root_key].descriptor)
                        | {"temporal": canonical(op.temporal)}
                    )
                    claims.append(("rule:" + case.id + ":" + op.id, meaning(desc)))
        return type(body).model_validate(
            canonical(body)
            | {
                "evidence": canonical(
                    tuple(sorted((*body.evidence, proof(claims)), key=lambda x: x.evidence_id))
                )
            }
        )

    return build


def rehash_event_chain(events):
    previous, result = None, []
    for index, event in enumerate(events, 1):
        body = canonical(event)
        body.pop("event_hash", None)
        body.update(sequence=index, previous_hash=previous)
        body = canonical(b.BasisFixtureEventV1(**body, event_hash="0" * 64))
        body.pop("event_hash")
        item = b.BasisFixtureEventV1(**body, event_hash=b.basis_hash("event", body))
        result.append(item)
        previous = item.event_hash
    return tuple(result)


def rehash_artifact(artifact):
    body = canonical(artifact)
    body.pop("artifact_fingerprint", None)
    body["events"] = rehash_event_chain(body["events"])
    body = canonical(b.BasisFixtureArtifactV1(**body, artifact_fingerprint="0" * 64))
    body.pop("artifact_fingerprint")
    return b.BasisFixtureArtifactV1(**body, artifact_fingerprint=b.basis_hash("artifact", body))


def rehash_sources(value):
    body = canonical(value)
    body.pop("source_fingerprint", None)
    return b.BasisApplicabilitySourcesV1(**body, source_fingerprint=b.basis_hash("sources", body))


def artifact(nre):
    anchors = project_basis_anchors(nre)
    ns = nre.sources
    req, events = ns.scope.root_request, []
    a = b.BasisAssertionV1(
        id="TEST_ONLY_assertion",
        revision="v1",
        subject=req.subject,
        scope_id=req.scope_id,
        scope_version=req.scope_version,
        protocol_fingerprint=req.protocol_fingerprint,
        stable_scope_fingerprint=stable_scope(ns),
        original_sources=tuple(sorted(set(x.original_source_fingerprint for x in anchors))),
        original_evidence=tuple(sorted(set(x.evidence_fingerprint for x in anchors))),
        required_keys=tuple(x.key for x in anchors),
        meanings=tuple(
            b.parse_basis(x.meaning_preimage, b.MeasurementMeaningV1)
            if x.meaning_preimage
            else meaning(x.descriptor)
            for x in anchors
        ),
        material_reference_fingerprint=b.basis_hash(
            "material-references",
            dict(recipes=ns.recipes, references=ns.references, slots=ns.scope.slots),
        ),
        effective=req.temporal.interval,
    )
    for person in ("reviewer", "publisher", "reader"):
        events.append(
            dict(kind="ENROLL", principal=person, principal_subject="TEST_ONLY_" + person)
        )
    for person, capability in (
        ("reviewer", "TEST_BASIS_REVIEW"),
        ("publisher", "TEST_BASIS_PUBLISH"),
        ("publisher", "TEST_BASIS_WITHDRAW"),
        ("reader", "TEST_BASIS_SOURCE_READ"),
    ):
        events.append(dict(kind="GRANT", principal=person, capability=capability))
    for person in ("reviewer", "publisher"):
        events.append(
            dict(
                kind="QUALIFY", principal=person, qualification="SYMBOLIC_TEST_ONLY_NOT_SCIENTIFIC"
            )
        )
    events.append(
        dict(
            id="TEST_ONLY_review",
            kind="REVIEW",
            principal="reviewer",
            assertion=a,
            assertion_fingerprint=b.basis_hash("assertion", a),
            effective=a.effective,
        )
    )
    events.append(
        dict(
            id="TEST_ONLY_publication",
            kind="PUBLISH",
            principal="publisher",
            review_id="TEST_ONLY_review",
            assertion_fingerprint=b.basis_hash("assertion", a),
            effective=a.effective,
        )
    )
    rows = []
    for index, e in enumerate(events):
        fields = dict(
            id="TEST_ONLY_event_" + str(index),
            sequence=1,
            previous_hash=None,
            recorded_at=ns.frame.started_at,
            effective=authority_interval(),
            principal_subject=None,
            capability=None,
            qualification=None,
            assertion=None,
            assertion_fingerprint=None,
            review_id=None,
            predecessor_publication_id=None,
            scope=req.scope_id,
        )
        fields.update(e)
        rows.append(fields)
    return rehash_artifact(
        dict(
            registry_id="TEST_ONLY_registry_" + uuid4().hex,
            revision=1,
            previous_artifact_fingerprint=None,
            deployment="TEST_ONLY_isolated",
            database_oid=ns.frame.fixture_database_oid,
            database_name=ns.frame.fixture_database_name,
            issuer_epoch=uuid4().hex,
            events=rows,
        )
    )


def retained():
    return b.parse_basis(
        Path(__file__).with_name("fixtures").joinpath("basis_retained_TEST_ONLY.json").read_bytes(),
        b.BasisApplicabilitySourcesV1,
    )


def reauthor_meaning(source, change):
    """Coherent synthetic alternative: NOT database/publication authority."""
    from app.modules.nutrition.resolution_contracts import NutritionResolutionHandoffV2
    from app.modules.nutrition.resolution_estimator import estimate_nutrition_resolution
    from app.modules.nutrition.synthesis import nutrition_policy_requirements
    from nutrition_resolution_fixtures import rehash
    from nutrition_synthesis_pure_fixtures import reauthor_root, reauthor_rule

    def evidence_rows(rows):
        for e in rows:
            try:
                data = json.loads(e["body"])
            except ValueError:
                continue
            if isinstance(data, dict) and data.get("schema") == "test-only.measurement-meaning.v1":
                change(data)
                e["body"] = json.dumps(data, sort_keys=True, separators=(",", ":"))
                e["body_fingerprint"] = b.n.nutrition_root_hash(
                    "nutrition.evidence-body.v1", e["body"]
                )

    def root_edit(data):
        guideline = next(
            r["command"]["body"]["guideline"]
            for r in data["sources"]
            if r["command"]["body"]["kind"] == "DRAFT"
        )
        evidence_rows(guideline["evidence_manifest"])
        fingerprint = b.n.nutrition_root_hash("nutrition.guideline-body.v1", guideline)
        evidence_hash = b.n.nutrition_root_hash(
            "nutrition.evidence-manifest.v1", guideline["evidence_manifest"]
        )
        data["request"]["guideline_body_fingerprint"] = fingerprint
        for r in data["sources"]:
            body = r["command"]["body"]
            if body["kind"] in {"REVIEW", "PUBLICATION"}:
                body["body_fingerprint"] = fingerprint
                if body["kind"] == "REVIEW":
                    body["evidence_fingerprint"] = evidence_hash
            if body["kind"] == "ASSESSMENT":
                body["guideline_body_fingerprint"] = fingerprint

    synth = reauthor_root(source.nre.sources.synthesis_sources, root_edit)
    synth = reauthor_rule(synth, lambda rule: evidence_rows(rule["evidence"]))
    req = nutrition_policy_requirements(synth)
    ns = canonical(source.nre.sources)
    ns["synthesis_sources"], ns["requirements"] = canonical(synth), canonical(req)
    ns["scope"].update(
        root_request=canonical(synth.request.root.sources.request),
        selection=canonical(synth.request.selection),
        requirement_fingerprint=req.fingerprint,
    )
    ns = rehash(ns)
    nre = NutritionResolutionHandoffV2(sources=ns, estimate=estimate_nutrition_resolution(ns))
    data = canonical(source)
    data["nre"] = canonical(nre)
    data["anchors"] = canonical(project_basis_anchors(nre))
    data["artifact"] = canonical(artifact(nre))
    data["selectors"]["nre_scope"] = canonical(ns.scope)
    data["selectors"]["nre_scope"].pop("requirement_fingerprint")
    data["selectors"]["nre_scope"]["contract_version"] = "nutrition-resolution-scope-request.v1"
    for name in (
        "registry_id",
        "artifact_fingerprint",
        "deployment",
        "issuer_epoch",
        "database_oid",
        "database_name",
    ):
        data["frame"][name] = data["artifact"][name]
    data["frame"]["registry_revision"] = data["artifact"]["revision"]
    return rehash_sources(data)


def weekly_basis_sources(include_week):
    """Invented retained TEST_ONLY source, no canonical-origin/scientific claim."""
    from datetime import timedelta

    from app.modules.nutrition.resolution_contracts import NutritionResolutionHandoffV2
    from app.modules.nutrition.resolution_estimator import estimate_nutrition_resolution
    from nutrition_resolution_fixtures import rehash, sources
    from nutrition_synthesis_fixtures import instruction
    from nutrition_synthesis_pure_fixtures import reauthor_root, reauthor_rule, weekly_sources

    old = retained()
    synthesis = weekly_sources(old.nre.sources.synthesis_sources)

    def original_root(data):
        guideline = next(
            r["command"]["body"]["guideline"]
            for r in data["sources"]
            if r["command"]["body"]["kind"] == "DRAFT"
        )
        guideline["evidence_manifest"] = [
            canonical(
                proof(
                    [
                        ("root:" + c["root_key"], meaning(c["descriptor"]))
                        for c in guideline["clauses"]
                    ]
                )
            )
        ]
        body_hash = b.n.nutrition_root_hash("nutrition.guideline-body.v1", guideline)
        evidence_hash = b.n.nutrition_root_hash(
            "nutrition.evidence-manifest.v1", guideline["evidence_manifest"]
        )
        data["request"]["guideline_body_fingerprint"] = body_hash
        for record in data["sources"]:
            value = record["command"]["body"]
            if value["kind"] in {"REVIEW", "PUBLICATION"}:
                value["body_fingerprint"] = body_hash
                if value["kind"] == "REVIEW":
                    value["evidence_fingerprint"] = evidence_hash
            if value["kind"] == "ASSESSMENT":
                value["guideline_body_fingerprint"] = body_hash

    synthesis = reauthor_root(synthesis, original_root)
    root = synthesis.request.root
    if include_week:

        def add_week(rule):
            rule["cases"][0]["operations"].append(
                canonical(
                    instruction(
                        "TEST_ONLY_week_comfort",
                        "MAKE_CONSTRAINT",
                        ("lower", "upper"),
                        root_key=root.roots[0].clause.root_key,
                        constraint_kind="RANGE",
                        layer="COMFORT",
                        temporal=root.sources.request.temporal,
                    )
                )
            )

        synthesis = reauthor_rule(synthesis, add_week)

    def rule_meanings(rule):
        original = [x for x in rule["evidence"] if x["evidence_id"] == rule["calendar_evidence_id"]]
        clauses = {r.clause.root_key: r.clause for r in root.roots}
        claims = []
        for case in rule["cases"]:
            for op in case["operations"]:
                if op["kind"] == "MAKE_CONSTRAINT":
                    desc = b.n.NutritionRootDescriptor.model_validate(
                        canonical(clauses[op["root_key"]].descriptor) | {"temporal": op["temporal"]}
                    )
                    claims.append(("rule:" + case["id"] + ":" + op["id"], meaning(desc)))
        evidence = original + [
            canonical(proof(claims[i : i + 8])) for i in range(0, len(claims), 8)
        ]
        rule["evidence"] = sorted(evidence, key=lambda x: x["evidence_id"])

    synthesis = reauthor_rule(synthesis, rule_meanings)
    ns = canonical(sources(synthesis))
    recipe = ns["recipes"][0]
    recipe["ingredients"][0]["adjustment"] = dict(kind="NONE", min_delta="0", max_delta="0")
    tier = recipe["portion_tiers"][0]["id"]
    ns["scope"]["recipes"][0]["tier_ids"] = [tier]
    template = next(x for x in ns["scope"]["slots"][0]["alternatives"] if x["tier_id"] == tier)
    first = root.sources.request.temporal.interval.start
    ns["scope"]["slots"] = [
        dict(
            slot_id=f"TEST_ONLY_day_{i}",
            interval=dict(start=first + timedelta(days=i), end=first + timedelta(days=i + 1)),
            alternatives=[template | {"slot_id": f"TEST_ONLY_day_{i}"}],
        )
        for i in range(7)
    ]
    ns = rehash(ns, food_manifest=True, counts=True)
    nre = NutritionResolutionHandoffV2(sources=ns, estimate=estimate_nutrition_resolution(ns))
    assert nre.estimate.availability == "AVAILABLE", nre.estimate.reasons
    a = artifact(nre)
    selectors = canonical(old.selectors)
    selectors["nre_scope"] = canonical(ns.scope)
    selectors["nre_scope"].pop("requirement_fingerprint")
    selectors["nre_scope"]["contract_version"] = "nutrition-resolution-scope-request.v1"
    frame = canonical(old.frame)
    for key in (
        "registry_id",
        "artifact_fingerprint",
        "deployment",
        "issuer_epoch",
        "database_oid",
        "database_name",
    ):
        frame[key] = getattr(a, key)
    frame["registry_revision"] = a.revision
    return rehash_sources(
        dict(
            contract_version="basis-applicability-sources.v1",
            nre=nre,
            artifact=a,
            selectors=selectors,
            anchors=project_basis_anchors(nre),
            frame=frame,
            absences=(),
        )
    )
