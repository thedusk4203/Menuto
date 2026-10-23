"""ADR-010 pure independent foundation. No DB, solver, runtime source or repair calls."""

from decimal import Decimal, Inexact, Rounded, localcontext

from pydantic import ValidationError

from app.domain.units import CalculatedQuantity
from app.modules.validation.contracts import (
    DEFERRED_CAPABILITIES,
    CalculatedNutrition,
    DefaultBatchInputDerivation,
    ValidationFinding,
    ValidationReport,
    ValidationSubjectSnapshot,
    YieldEstimate,
)
from app.modules.validation.material import check_material


def validate_subject(
    subject: ValidationSubjectSnapshot, *, phase="PRECOMMIT_VALIDATION"
) -> ValidationReport:
    if phase not in {"PRECOMMIT_VALIDATION", "POSTFACT_VALIDATION"}:
        raise ValueError("Unknown validation phase")
    # Canonical order also makes findings deterministic for duplicate/ambiguous input facts.
    s = ValidationSubjectSnapshot.model_validate_json(subject.canonical_json())
    findings, derived, yields = [], [], []

    def emit(code, severity, domain, scope, detail, *proof):
        findings.append(
            ValidationFinding(
                code=code,
                severity=severity,
                source_domain=domain,
                scope=str(scope),
                detail=detail,
                proof_refs=tuple(str(x) for x in proof),
            )
        )

    g = s.proposal.graph
    if s.household_id != g.household_id or s.inventory.household_id != s.household_id:
        emit("SUBJECT_HOUSEHOLD_MISMATCH", "ERROR", "DATA", "subject", "Source ownership differs")
    groups = (
        (s.members, "member_id"),
        (s.member_safety, "member_id"),
        (s.ingredients, "id"),
        (s.recipes, "id"),
        (s.nutrition_references, "id"),
    )
    for values, key in groups:
        if len({getattr(v, key) for v in values}) != len(values):
            emit("DUPLICATE_CANONICAL_FACT", "ERROR", "DATA", key, "Source identity is ambiguous")
    members = {m.member_id: m for m in s.members}
    safety = {m.member_id: m for m in s.member_safety}
    ingredients = {i.id: i for i in s.ingredients}
    recipes = {r.id: r for r in s.recipes}
    for m in (*s.members, *s.member_safety):
        if m.household_id != s.household_id:
            emit(
                "MEMBER_HOUSEHOLD_MISMATCH",
                "ERROR",
                "DATA",
                m.member_id,
                "Member/source is not owned by subject household",
            )
    for m in s.member_safety:
        if m.member_id not in members:
            emit(
                "CANONICAL_MEMBER_SOURCE_MISSING",
                "ERROR",
                "DATA",
                m.member_id,
                "Restriction source has no canonical member identity",
            )
        keys = [v.id for v in m.constraints]
        if len(keys) != len(set(keys)):
            emit(
                "DUPLICATE_SAFETY_FACT",
                "ERROR",
                "DATA",
                m.member_id,
                "Repeated source constraint identity",
            )
        for source in m.constraints:
            c = source.constraint
            if (c.household_id, c.member_id) != (s.household_id, m.member_id):
                emit(
                    "SAFETY_SOURCE_OWNER_MISMATCH",
                    "ERROR",
                    "DATA",
                    source.id,
                    "Restriction source identity crosses member/household",
                )
            if c.kind != "EXCLUDED_INGREDIENT":
                emit(
                    "SAFETY_CLASSIFICATION_UNAVAILABLE",
                    "ERROR",
                    "DATA",
                    source.id,
                    "Allergen/diet classification unavailable; unknown is not safe",
                    c.kind,
                    c.code,
                )
    required_members = {p.member_id for m in g.meals for p in m.participants}
    for identity in sorted(required_members | {g.tracked_member_id}, key=str):
        if identity not in members or identity not in safety:
            emit(
                "CANONICAL_MEMBER_SOURCE_MISSING",
                "ERROR",
                "DATA",
                identity,
                "Participant canonical identity/safety source missing",
            )
    frontier = s.source_frontier.current_revision_no
    if frontier != s.proposal.expected_revision:
        emit(
            "STALE_PLAN_REVISION",
            "ERROR",
            "PLAN",
            g.plan_id,
            "Proposal expectation differs from captured current head",
        )
    if (frontier is None) != (s.parent_revision is None) or (
        s.parent_revision is not None
        and (
            (
                s.parent_revision.household_id,
                s.parent_revision.plan_id,
                s.parent_revision.revision_no,
            )
            != (s.household_id, g.plan_id, frontier)
        )
    ):
        emit(
            "REVISION_SOURCE_MISMATCH",
            "ERROR",
            "PLAN",
            g.plan_id,
            "Parent revision does not bind captured stable plan identity",
        )
    if s.policy.policy_version != "1":
        emit(
            "UNSUPPORTED_VALIDATION_POLICY",
            "FATAL",
            "POLICY",
            s.policy.policy_version,
            "Coverage policy version is not implemented",
        )

    # Default authored inputs are reconstructed directly, not by calling the Recipe binder.
    batches = {}
    for b in g.batches:
        if b.status != "PLANNED":
            continue
        r = recipes.get(b.recipe_version_id)
        if r is None:
            emit(
                "RECIPE_SOURCE_MISSING",
                "ERROR",
                "DATA",
                b.node_id,
                "Exact immutable RecipeVersion required",
            )
            continue
        tier = next((t for t in r.portion_tiers if t.id == b.tier_id), None)
        if tier is None or tier.recipe_version_id != r.id or tier.servings != b.planned_servings:
            emit(
                "AUTHORED_TIER_MISMATCH",
                "ERROR",
                "PLAN",
                b.node_id,
                "Tier and planned serving count must bind exact authored version",
            )
            continue
        if r.review_status != "REVIEWED":
            emit(
                "UNREVIEWED_RECIPE",
                "ERROR",
                "DATA",
                r.id,
                "Draft authorship is not reviewed culinary evidence",
            )
        quantities = {q.requirement_id: q.amount for q in tier.quantities}
        batches[b.node_id] = (r, quantities)
        totals = dict.fromkeys(("energy_kcal", "protein_g", "fat_g", "carbohydrate_g"), Decimal(0))
        refs, complete = [], True
        with localcontext() as ctx:
            ctx.prec = 160
            ctx.traps[Inexact] = ctx.traps[Rounded] = True
            for item in r.ingredients:
                if item.ingredient_id not in ingredients:
                    emit(
                        "UNKNOWN_INGREDIENT_SOURCE",
                        "ERROR",
                        "DATA",
                        item.id,
                        "Canonical ingredient identity missing",
                        item.ingredient_id,
                    )
                    complete = False
                candidates = [
                    n
                    for n in s.nutrition_references
                    if n.fact.ingredient_id == item.ingredient_id
                    and n.fact.reference.basis == item.quantity.basis
                    and n.fact.status == "REVIEWED"
                ]
                if len(candidates) != 1:
                    emit(
                        "NUTRITION_SOURCE_UNRESOLVED",
                        "ERROR",
                        "DATA",
                        item.id,
                        "One compatible reviewed reference required; no implicit conversion",
                        item.quantity.basis,
                    )
                    complete = False
                    continue
                n = candidates[0]
                refs.append(n.id)
                try:
                    for name in totals:
                        totals[name] += (
                            quantities[item.id]
                            * getattr(n.fact.nutrients, name)
                            / n.fact.reference.amount
                        )
                    CalculatedNutrition(**totals)
                except (ArithmeticError, ValidationError):
                    emit(
                        "NUTRITION_ARITHMETIC_UNRESOLVED",
                        "ERROR",
                        "DATA",
                        item.id,
                        "Exact calculation exceeds supported resolution; rounding is forbidden",
                    )
                    complete = False
            derived.append(
                DefaultBatchInputDerivation(
                    batch_node_id=b.node_id,
                    recipe_version_id=r.id,
                    tier_id=tier.id,
                    requirement_ids=tuple(sorted(quantities, key=str)),
                    nutrition_reference_ids=tuple(sorted(refs, key=str)),
                    input_nutrition=CalculatedNutrition(**totals) if complete else None,
                )
            )
            for t in r.transformations:
                item = next(
                    (
                        i
                        for i in r.ingredients
                        if i.id == t.requirement_id and i.ingredient_id == t.ingredient_id
                    ),
                    None,
                )
                if item is None:  # A transformation authored only for a substitute is not default.
                    continue
                if (
                    t.recipe_version_id,
                    t.method,
                    t.source_basis,
                    t.target_basis,
                    item.quantity.basis,
                ) != (r.id, r.recipe.cooking_method, "EP_RAW_G", "COOKED_G", "EP_RAW_G"):
                    emit(
                        "PREPARATION_CONTEXT_MISMATCH",
                        "ERROR",
                        "DATA",
                        t.id,
                        "Cooking yield needs its exact authored ingredient/method/bases",
                    )
                    continue
                try:
                    yields.append(
                        YieldEstimate(
                            owner="RECIPE_PREPARATION",
                            owner_id=t.id,
                            context_id=b.node_id,
                            input=CalculatedQuantity(amount=quantities[item.id], basis="EP_RAW_G"),
                            output=CalculatedQuantity(
                                amount=quantities[item.id] * t.factor, basis="COOKED_G"
                            ),
                        )
                    )
                except (ArithmeticError, ValidationError):
                    emit(
                        "YIELD_ARITHMETIC_UNRESOLVED",
                        "ERROR",
                        "DATA",
                        t.id,
                        "Cannot represent exact derived cooking yield",
                    )
    # Safety always traverses actual participants × authored default ingredient identities.
    meal_map = {m.node_id: m for m in g.meals}
    for allocation in g.allocations:
        meal = meal_map[allocation.meal_node_id]
        if (
            allocation.status != "PLANNED"
            or meal.status != "PLANNED"
            or allocation.batch_node_id not in batches
        ):
            continue
        r, _ = batches[allocation.batch_node_id]
        actual = {i.ingredient_id for i in r.ingredients}
        for p in meal.participants:
            source = safety.get(p.member_id)
            if source:
                for fact in source.constraints:
                    c = fact.constraint
                    if c.kind == "EXCLUDED_INGREDIENT" and c.ingredient_id in actual:
                        emit(
                            "FORBIDDEN_INGREDIENT",
                            "ERROR",
                            "PLAN",
                            meal.node_id,
                            "Canonical restriction contradicts primitive ingredient exposure",
                            p.member_id,
                            c.ingredient_id,
                            fact.id,
                            r.id,
                        )
    with localcontext() as ctx:
        ctx.prec = 160
        ctx.traps[Inexact] = ctx.traps[Rounded] = True
        for lot in s.inventory.lots:
            mapping = lot.retail_mapping
            if mapping is not None:
                if (
                    mapping.ingredient_id != lot.ingredient_id
                    or mapping.status != "REVIEWED"
                    or lot.acquired_quantity.basis != "AP_G"
                ):
                    emit(
                        "RETAIL_MAPPING_CONTEXT_MISMATCH",
                        "ERROR",
                        "DATA",
                        lot.id,
                        "AP yield requires exact reviewed product/ingredient origin",
                    )
                    continue
                try:
                    yields.append(
                        YieldEstimate(
                            owner="RETAIL_MAPPING",
                            owner_id=mapping.id,
                            context_id=lot.id,
                            input=CalculatedQuantity(
                                amount=lot.acquired_quantity.amount, basis="AP_G"
                            ),
                            output=CalculatedQuantity(
                                amount=lot.acquired_quantity.amount * mapping.edible_yield,
                                basis="EP_RAW_G",
                            ),
                        )
                    )
                except (ArithmeticError, ValidationError):
                    emit(
                        "YIELD_ARITHMETIC_UNRESOLVED",
                        "ERROR",
                        "DATA",
                        lot.id,
                        "Cannot represent exact derived edible yield",
                    )
    balances = check_material(s, emit)
    semantic_error = any(f.severity in {"ERROR", "FATAL"} for f in findings)
    for gap in DEFERRED_CAPABILITIES:
        emit(
            "REQUIRED_CAPABILITY_UNAVAILABLE",
            "ERROR" if phase == "PRECOMMIT_VALIDATION" else "INFO",
            "POLICY",
            gap,
            "Foundation coverage cannot authorize production intent",
        )
    findings.sort(key=lambda f: (f.code, f.source_domain, f.scope, f.proof_refs, f.detail))
    return ValidationReport(
        phase=phase,
        decision=(
            "DIAGNOSTIC"
            if phase == "POSTFACT_VALIDATION"
            else ("REJECTED" if semantic_error else "BLOCKED_UNSUPPORTED")
        ),
        subject_hash=s.fingerprint,
        policy_hash=s.policy.fingerprint,
        expected_revision=s.proposal.expected_revision,
        findings=tuple(findings),
        default_batch_inputs=tuple(sorted(derived, key=lambda d: str(d.batch_node_id))),
        material_balances=balances,
        yield_estimates=tuple(
            sorted(yields, key=lambda y: (y.owner, str(y.context_id), str(y.owner_id)))
        ),
        deferred_capabilities=DEFERRED_CAPABILITIES,
    )
