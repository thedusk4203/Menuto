"""Synthetic retained alternatives; no scientific truth, installation or origin authority."""

import json
from functools import lru_cache

from app.domain.feature_identity import canonical
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition import policy_v2_contracts as v
from app.modules.nutrition.basis_projection import project_basis_anchors
from app.modules.nutrition.policy_v2_public import prepare_policy_v2_input
from app.modules.nutrition.resolution_contracts import NutritionResolutionHandoffV2
from app.modules.nutrition.resolution_estimator import estimate_nutrition_resolution
from app.modules.nutrition.synthesis import nutrition_policy_requirements
from basis_fixtures import artifact, meaning, proof, rehash_sources, retained, weekly_basis_sources
from nutrition_resolution_fixtures import rehash
from nutrition_synthesis_pure_fixtures import reauthor_root, reauthor_rule


def compose(synth, source, food_change=None):
    ns = canonical(source.nre.sources)
    req = nutrition_policy_requirements(synth)
    ns.update(synthesis_sources=canonical(synth), requirements=canonical(req))
    ns["frame"]["source_frame"] = canonical(synth.frame)
    ns["scope"].update(
        root_request=canonical(synth.request.root.sources.request),
        selection=canonical(synth.request.selection),
        precision=canonical(synth.request.precision),
        requirement_fingerprint=req.fingerprint,
    )
    if food_change:
        food_change(ns)
    ns = rehash(ns, food_manifest=True, counts=True)
    nre = NutritionResolutionHandoffV2(sources=ns, estimate=estimate_nutrition_resolution(ns))
    a = artifact(nre)
    data = canonical(source)
    data.update(
        nre=canonical(nre), anchors=canonical(project_basis_anchors(nre)), artifact=canonical(a)
    )
    scope = canonical(ns.scope)
    scope.pop("requirement_fingerprint")
    scope["contract_version"] = "nutrition-resolution-scope-request.v1"
    data["selectors"]["nre_scope"] = scope
    for key in (
        "registry_id",
        "artifact_fingerprint",
        "deployment",
        "issuer_epoch",
        "database_oid",
        "database_name",
    ):
        data["frame"][key] = getattr(a, key)
    data["frame"]["registry_revision"] = a.revision
    return rehash_sources(data)


def author_rule(source, mutate):
    root = source.nre.sources.synthesis_sources.request.root

    def edit(rule):
        mutate(rule)
        # Re-author original-source meaning for the complete changed instruction tree.
        keep = []
        for e in rule["evidence"]:
            try:
                body = json.loads(e["body"])
            except ValueError:
                body = None
            if (
                not isinstance(body, dict)
                or body.get("schema") != "test-only.measurement-meaning.v1"
            ):
                keep.append(e)
        clauses = {r.clause.root_key: r.clause for r in root.roots}
        pairs = []
        for case in rule["cases"]:
            for op in case["operations"]:
                if op["kind"] == "MAKE_CONSTRAINT":
                    desc = b.n.NutritionRootDescriptor.model_validate(
                        canonical(clauses[op["root_key"]].descriptor) | {"temporal": op["temporal"]}
                    )
                    pairs.append(("rule:" + case["id"] + ":" + op["id"], meaning(desc)))
        keep += [canonical(proof(pairs[i : i + 8])) for i in range(0, len(pairs), 8)]
        rule["evidence"] = sorted(keep, key=lambda x: x["evidence_id"])

    return compose(reauthor_rule(source.nre.sources.synthesis_sources, edit), source)


def author_root(source, mutate):
    def edit(data):
        body = next(
            x["command"]["body"]["guideline"]
            for x in data["sources"]
            if x["command"]["body"]["kind"] == "DRAFT"
        )
        mutate(body)
        # New test roots need their own original-source meaning, not a wrapper assertion.
        body["evidence_manifest"] = [
            canonical(
                proof(
                    [("root:" + c["root_key"], meaning(c["descriptor"])) for c in body["clauses"]]
                )
            )
        ]
        fp = b.n.nutrition_root_hash("nutrition.guideline-body.v1", body)
        data["request"]["guideline_body_fingerprint"] = fp
        for row in data["sources"]:
            command = row["command"]["body"]
            if command["kind"] in {"REVIEW", "PUBLICATION"}:
                command["body_fingerprint"] = fp
            if command["kind"] == "REVIEW":
                command["evidence_fingerprint"] = b.n.nutrition_root_hash(
                    "nutrition.evidence-manifest.v1", body["evidence_manifest"]
                )
            if command["kind"] == "ASSESSMENT":
                command["guideline_body_fingerprint"] = fp

    return compose(reauthor_root(source.nre.sources.synthesis_sources, edit), source)


@lru_cache
def positive_week():
    s = weekly_basis_sources(True)
    return author_root(
        s,
        lambda body: body["clauses"][0]["constraint"].update(
            lower=dict(numerator=49, denominator=1), upper=dict(numerator=91, denominator=1)
        ),
    )


def input_for(source=None):
    return prepare_policy_v2_input(source or retained())


def rehash_input(data):
    d = canonical(data)
    d.pop("source_fingerprint", None)
    return v.NutritionPolicyIntegrationInputV2(**d, source_fingerprint=v.policy_v2_hash("input", d))


def forged(result, mutate):
    data = canonical(result)
    mutate(data)
    data.pop("result_fingerprint")
    return v.NutritionPolicyResultV2(**data, result_fingerprint=v.policy_v2_hash("result", data))
