"""Pre-policy metadata only. No policy arithmetic, precision-band choice or Validation calls."""

import json

from app.domain.feature_identity import canonical
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition.resolution_limits import ingest
from app.modules.nutrition.synthesis import nutrition_policy_requirements
from app.modules.nutrition.synthesis_journal import replay_synthesis_sources


def stable_scope(s):
    return b.basis_hash(
        "stable-scope",
        canonical(
            s.scope,
        )
        | {
            "contract_version": "nutrition-resolution-scope-request.v1",
            "requirement_fingerprint": None,
        },
    )


def original_preimage(evidence, key):
    found = []
    for row in evidence:
        try:
            data = ingest(row.body, 16384)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or data.get("schema") != "test-only.measurement-meaning.v1":
            continue
        if set(data) != {"schema", "environment", "claims"} or data["environment"] != "TEST_ONLY":
            raise ValueError("ENVIRONMENT_MISMATCH")
        if not isinstance(data["claims"], list) or len(data["claims"]) > 128:
            raise ValueError("RESOURCE_EXCEEDED")
        for item in data["claims"]:
            if set(item) != {"key", "meaning"}:
                raise ValueError("CONVERSION_NOT_SUPPORTED")
            if item["key"] == key:
                found.append(json.dumps(item["meaning"], sort_keys=True, separators=(",", ":")))
    if len(found) > 1:
        raise ValueError("ORIGINAL_MEANING_CONTRADICTION")
    return found[0] if found else None


def project_basis_anchors(nre):
    """Fresh frozen requirement plus a DISTINCT full root/operation metadata manifest."""
    s = nre.sources
    source, rule, reason = replay_synthesis_sources(s.synthesis_sources)
    if reason or rule is None:
        raise ValueError("SOURCE_INVALID")
    req = nutrition_policy_requirements(source)
    if req != s.requirements:
        raise ValueError("REQUIREMENT_IDENTITY")
    root = source.request.root
    cases = [c for c in rule.cases if c.direction == root.goal_direction]
    if len(cases) != 1:
        raise ValueError("UNSUPPORTED_LINEAGE")
    case, clauses = cases[0], {r.clause.root_key: r.clause for r in root.roots}
    if not clauses:
        raise ValueError("REQUIRED_ANCHOR_MISSING")
    guideline_rows = [
        e.command.body.guideline
        for e in root.sources.sources
        if e.command.body.kind == "DRAFT"
        and e.command.body.guideline.revision_id == root.sources.request.guideline_revision_id
    ]
    if len(guideline_rows) != 1:
        raise ValueError("SOURCE_INVALID")
    guideline = guideline_rows[0]
    records, values = [], {}

    def anchor(key, layer, root_key, desc, evidences, original):
        data = dict(
            key=key,
            layer=layer,
            root_key=root_key,
            descriptor=desc,
            subject=s.scope.subject,
            original_source_fingerprint=original,
            evidence_fingerprint=b.basis_hash("original-evidence", evidences),
            meaning_preimage=original_preimage(evidences, key),
            stable_scope_fingerprint=stable_scope(s),
            root_fingerprint=root.result_fingerprint,
            requirement_fingerprint=req.fingerprint,
            nre_source_fingerprint=s.source_fingerprint,
            nre_result_fingerprint=nre.estimate.result_fingerprint,
        )
        records.append(
            b.BasisClaimAnchorV1(**data, anchor_fingerprint=b.basis_hash("anchor", data))
        )

    for key, clause in sorted(clauses.items()):
        anchor(
            "root:" + key,
            clause.interpretation,
            key,
            clause.descriptor,
            guideline.evidence_manifest,
            root.sources.request.guideline_body_fingerprint,
        )
    for op in case.operations:
        if op.id in values or any(i not in values for i in op.inputs):
            raise ValueError("UNSUPPORTED_LINEAGE")
        args = [values[i] for i in op.inputs]
        if op.kind == "COPY_REFERENCE":
            if op.root_key not in clauses or not hasattr(
                clauses[op.root_key].constraint, op.endpoint
            ):
                raise ValueError("UNSUPPORTED_LINEAGE")
            value = (op.root_key, clauses[op.root_key].descriptor, "ENDPOINT")
        elif op.kind in {"AFFINE_SAME_UNIT", "REVIEWED_PERIOD_PROJECTION", "FINITE_PERIOD_SUM"}:
            key, desc, typ = args[0]
            if typ != "ENDPOINT" or any(x[0] != key or x[2] != typ for x in args):
                raise ValueError("UNSUPPORTED_LINEAGE")
            if op.kind == "AFFINE_SAME_UNIT":
                value = args[0]
            else:
                if any(
                    canonical(x[1]) | {"temporal": None} != canonical(desc) | {"temporal": None}
                    for x in args
                ):
                    raise ValueError("UNSUPPORTED_LINEAGE")
                if op.kind == "FINITE_PERIOD_SUM" and (
                    tuple(x[1].temporal for x in args) != rule.calendar_cells
                    or op.temporal != rule.applicability.temporal
                ):
                    raise ValueError("UNSUPPORTED_LINEAGE")
                if (
                    op.temporal not in rule.calendar_cells
                    and op.temporal != rule.applicability.temporal
                ):
                    raise ValueError("UNSUPPORTED_LINEAGE")
                value = (
                    key,
                    n.NutritionRootDescriptor.model_validate(
                        canonical(desc) | {"temporal": canonical(op.temporal)}
                    ),
                    typ,
                )
        elif op.kind == "MAKE_CONSTRAINT":
            if op.root_key not in clauses:
                raise ValueError("UNSUPPORTED_LINEAGE")
            desc = n.NutritionRootDescriptor.model_validate(
                canonical(clauses[op.root_key].descriptor) | {"temporal": canonical(op.temporal)}
            )
            if any(x != (op.root_key, desc, "ENDPOINT") for x in args):
                raise ValueError("UNSUPPORTED_LINEAGE")
            value = (op.root_key, desc, "CLAIM")
            anchor(
                "rule:" + case.id + ":" + op.id,
                op.layer,
                op.root_key,
                desc,
                rule.evidence,
                s.requirements.rule_body_fingerprint,
            )
        elif op.kind == "SELECT_PRECISION_CASE":
            if any(x != args[0] for x in args) or args[0][2] != "CLAIM":
                raise ValueError("UNSUPPORTED_LINEAGE")
            value = args[0]
        elif op.kind in {"CHECK_SUBSET", "CHECK_DIRECTION"}:
            if args[0][0:2] != args[1][0:2] or args[0][2] != "CLAIM":
                raise ValueError("UNSUPPORTED_LINEAGE")
            if op.kind == "CHECK_SUBSET" and args[1][2] != "CLAIM":
                raise ValueError("UNSUPPORTED_LINEAGE")
            value = (args[0][0], args[0][1], "RELATION")
        else:
            raise ValueError("UNSUPPORTED_LINEAGE")
        values[op.id] = value
    if any(k not in values or values[k][2] != "CLAIM" for k in case.required_claims):
        raise ValueError("REQUIRED_ANCHOR_MISSING")
    if not 1 <= len(records) <= 128:
        raise ValueError("RESOURCE_EXCEEDED")
    return tuple(sorted(records, key=lambda x: x.key))
