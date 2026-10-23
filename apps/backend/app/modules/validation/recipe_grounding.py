"""Independent authored-rule verification. Never invokes the culinary producer/resolver."""

import hashlib
import json
from decimal import Decimal, Inexact, Rounded, localcontext

from app.modules.validation.contracts import (
    CulinaryValidationInput,
    RecipeGroundingReport,
    ValidationFinding,
)


def validate_recipe_grounding(source: CulinaryValidationInput, *, phase="PRECOMMIT_VALIDATION"):
    if not isinstance(source, CulinaryValidationInput):
        raise TypeError("Immutable culinary validation input required")
    if phase not in {"PRECOMMIT_VALIDATION", "POSTFACT_VALIDATION"}:
        raise ValueError("Unknown phase")
    findings = []

    def fail(code, ref, detail):
        findings.append(
            ValidationFinding(
                code=code,
                severity="ERROR",
                source_domain="PLAN",
                scope=str(ref),
                proof_refs=(str(ref),),
                detail=detail,
            )
        )

    g, proposal = source.proposal.graph, source.proposal
    if (
        source.contract_version != "culinary-validation-input.v1"
        or g.contract_version != "plan-intent.v3"
    ):
        fail("CULINARY_VERSION", proposal.id, "Unsupported source contract version")
    versions = {v.id: v for v in source.recipes}
    if len(versions) != len(source.recipes):
        fail("CULINARY_RECIPE_AMBIGUOUS", proposal.id, "Duplicate authored version")
    batches = {b.node_id: b for b in g.batches}
    if len({b.batch_node_id for b in g.culinary_bindings}) != len(g.culinary_bindings) or set(
        batches
    ) != {b.batch_node_id for b in g.culinary_bindings}:
        fail("CULINARY_BINDING_COVERAGE", proposal.id, "One binding per exact batch required")
    for binding in sorted(g.culinary_bindings, key=lambda b: str(b.batch_node_id)):
        ref = binding.batch_node_id
        if binding.contract_version != "planned-culinary-binding.v1":
            fail("CULINARY_VERSION", ref, "Unsupported binding schema")
        batch, v = batches.get(ref), versions.get(binding.recipe_version_id)
        if binding.provenance.kind not in {"USER_AUTHORED", "CURATED_REFERENCE"}:
            fail("CULINARY_PROVENANCE", ref, "Unreviewed imported intent is not authoritative")
        if (
            batch is None
            or (binding.household_id, binding.plan_id, binding.proposal_id)
            != (g.household_id, g.plan_id, proposal.id)
            or (binding.recipe_version_id, binding.tier_id, binding.planned_servings)
            != (batch.recipe_version_id, batch.tier_id, batch.planned_servings)
        ):
            fail("CULINARY_OWNER", ref, "Cross household/plan/proposal/batch/version")
            continue
        if v is None or v.review_status != "REVIEWED":
            fail("CULINARY_RECIPE_SOURCE", ref, "Exact reviewed authored version required")
            continue
        tiers = [
            t for t in v.portion_tiers if t.id == binding.tier_id and t.recipe_version_id == v.id
        ]
        if len(tiers) != 1 or tiers[0].servings != binding.planned_servings:
            fail("CULINARY_TIER", ref, "Serving count must be an authored tier")
            continue
        items = {i.id: i for i in v.ingredients}
        rows = {r.requirement_id: r for r in binding.requirements}
        if len(rows) != len(binding.requirements) or set(rows) != set(items):
            fail("CULINARY_REQUIREMENTS", ref, "Exact unique requirement coverage required")
        selected = [r.selected_rule_id for r in binding.requirements if r.selected_rule_id]
        rules = {r.id: r for r in v.variant_rules}
        if len(set(selected)) != len(selected) or any(key not in rules for key in selected):
            fail("CULINARY_RULE", ref, "Unknown/duplicate rule")
        structural = [rules[key] for key in selected if key in rules and rules[key].structural]
        combo = next(
            (c for c in v.approved_combinations if c.id == binding.approved_combination_id), None
        )
        if (
            len(structural) > 1
            and (
                combo is None
                or combo.recipe_version_id != v.id
                or set(combo.rule_ids) != set(selected)
            )
        ) or (len(structural) <= 1 and binding.approved_combination_id is not None):
            fail("CULINARY_COMBINATION", ref, "Exact authored combination required")
        amounts = {q.requirement_id: q.amount for q in tiers[0].quantities}
        try:
            with localcontext() as ctx:
                ctx.prec = 160
                ctx.traps[Inexact] = ctx.traps[Rounded] = True
                for key, row in rows.items():
                    item = items.get(key)
                    if item is None or item.recipe_version_id != v.id or key not in amounts:
                        fail("CULINARY_REQUIREMENT_OWNER", key, "Requirement/tier ownership")
                        continue
                    rule = rules.get(row.selected_rule_id)
                    if row.selected_rule_id and (
                        rule is None
                        or rule.recipe_version_id != v.id
                        or rule.requirement_id != key
                        or item.quantity.basis == "COUNT"
                    ):
                        fail("CULINARY_RULE", key, "Unauthorized rule/slot/COUNT substitution")
                        continue
                    ingredient = rule.replacement_ingredient_id if rule else item.ingredient_id
                    delta, policy = row.adjustment_delta, item.adjustment
                    if not policy.min_delta <= delta <= policy.max_delta or (
                        policy.kind == "DISCRETE" and delta % policy.step != 0
                    ):
                        fail("CULINARY_ADJUSTMENT", key, "Delta outside authored envelope/step")
                    amount = amounts[key] * (rule.quantity_factor if rule else Decimal(1)) + delta
                    if (
                        row.ingredient_id,
                        row.quantity.amount,
                        row.quantity.basis,
                        row.quantity.item_ref,
                    ) != (
                        ingredient,
                        amount,
                        item.quantity.basis,
                        item.quantity.item_ref,
                    ) or amount <= 0:
                        fail(
                            "CULINARY_RESOLUTION",
                            key,
                            "Ingredient, amount or measurement identity mismatch",
                        )
                    scale = item.scaling
                    # Independently check authored tier points, not producer-calculated totals.
                    points = sorted(
                        (
                            t.servings,
                            next(q.amount for q in t.quantities if q.requirement_id == key),
                        )
                        for t in v.portion_tiers
                    )
                    for servings, quantity in points:
                        if (
                            (servings == v.base_servings and quantity != item.quantity.amount)
                            or (
                                scale.kind == "LINEAR"
                                and quantity * v.base_servings != item.quantity.amount * servings
                            )
                            or (scale.kind == "FIXED" and quantity != item.quantity.amount)
                            or (
                                scale.kind == "TO_TASTE"
                                and not scale.minimum <= quantity <= scale.maximum
                            )
                        ):
                            fail("CULINARY_SCALING", key, "Authored tier violates scaling")
                    if scale.kind == "SUBLINEAR" and any(
                        not (q1 < q2 and q2 * s1 < q1 * s2)
                        for (s1, q1), (s2, q2) in zip(points, points[1:])
                    ):
                        fail("CULINARY_SCALING", key, "Sublinear authored points invalid")
                    if scale.kind == "DISCRETE" and (
                        amount % scale.quantum != 0 or any(q % scale.quantum for _, q in points)
                    ):
                        fail("CULINARY_SCALING", key, "Discrete quantity not aligned")
                    path = [
                        t
                        for t in v.transformations
                        if t.requirement_id == key and t.ingredient_id == ingredient
                    ]
                    base_has_path = any(
                        t.requirement_id == key and t.ingredient_id == item.ingredient_id
                        for t in v.transformations
                    )
                    if (
                        len(path) > 1
                        or (base_has_path and not path)
                        or row.transformation_id != (path[0].id if path else None)
                    ):
                        fail(
                            "CULINARY_TRANSFORMATION",
                            key,
                            "Wrong/missing resolved preparation path",
                        )
                    for t in path:
                        if (
                            t.recipe_version_id != v.id
                            or t.method != v.recipe.cooking_method
                            or item.quantity.basis != "EP_RAW_G"
                            or (t.source_basis, t.target_basis) != ("EP_RAW_G", "COOKED_G")
                            or t.factor <= 0
                        ):
                            fail("CULINARY_TRANSFORMATION", key, "Invalid raw/cooked context")
        except (Inexact, Rounded, ArithmeticError, StopIteration):
            fail("CULINARY_ARITHMETIC", ref, "Exact authored arithmetic could not be resolved")
        # Independent serialization implementation, not binding.expected_fingerprint().
        payload = binding.model_dump(mode="json", exclude={"fingerprint"})
        payload["planned_servings"] = format(binding.planned_servings, "f")
        payload["provenance"]["observed_at"] = binding.provenance.observed_at.isoformat(
            timespec="microseconds"
        ).replace("+00:00", "Z")
        for row, fact in zip(payload["requirements"], binding.requirements, strict=True):
            row["quantity"]["amount"] = format(fact.quantity.amount, "f")
            row["adjustment_delta"] = format(fact.adjustment_delta, "f")
        payload["requirements"].sort(key=lambda r: r["requirement_id"])

        def digest(p):
            return hashlib.sha256(
                json.dumps(p, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
            ).hexdigest()

        if digest(payload) != binding.fingerprint:
            fail("CULINARY_FINGERPRINT", ref, "Binding fingerprint differs from primitives")
        payload.pop("proposal_id")
        if digest(payload) != batch.culinary_signature:
            fail("CULINARY_SIGNATURE", ref, "Batch signature differs from primitive intent")
    return RecipeGroundingReport(
        phase=phase,
        subject_hash=source.fingerprint,
        culinary_checks_passed=not findings,
        findings=tuple(sorted(findings, key=lambda f: (f.scope, f.code, f.detail))),
    )
