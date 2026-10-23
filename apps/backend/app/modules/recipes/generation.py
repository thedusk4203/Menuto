"""ADR-005 demand expansion, without Cartesian search, ranking or live source reads."""

import json
from hashlib import sha256

from app.modules.recipes.contracts import (
    CulinaryCandidateDraft,
    CulinaryGenerationRejection,
    RecipeVersionSnapshot,
    VariantGenerationRequest,
    VariantGenerationResult,
    resolve_culinary_binding,
)


def _hash(data):
    return sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def _recipe_content(recipe):
    data = recipe.model_dump(mode="json")
    for name in (
        "ingredients",
        "portion_tiers",
        "variant_rules",
        "approved_combinations",
        "transformations",
    ):
        data[name] = sorted(data[name], key=lambda r: r["id"])
    for tier in data["portion_tiers"]:
        tier["quantities"] = sorted(tier["quantities"], key=lambda q: q["requirement_id"])
    for combo in data["approved_combinations"]:
        combo["rule_ids"] = sorted(combo["rule_ids"])
    return data


def recipe_source_hash(recipe: RecipeVersionSnapshot):
    """Only unordered fact sets sort; authored procedure content retains its order."""
    recipe = RecipeVersionSnapshot.model_validate(recipe.model_dump())
    return _hash(_recipe_content(recipe))


def _request_content(request):
    data = request.model_dump(mode="json")
    data["recipe"] = _recipe_content(request.recipe)
    for key in ("serving_counts", "ingredient_targets", "excluded_ingredient_ids"):
        data["demand"][key] = sorted(set(data["demand"][key]))
    data["demand"]["rule_selections"] = [
        {"rule_ids": list(ids)}
        for ids in sorted({tuple(sorted(s["rule_ids"])) for s in data["demand"]["rule_selections"]})
    ]
    return data


def generate_variants(request: VariantGenerationRequest) -> VariantGenerationResult:
    # Revalidate copies too: a caller's model_copy/model_construct is not trusted authorship.
    request = VariantGenerationRequest.model_validate(request.model_dump())
    recipe, demand, limits = request.recipe, request.demand, request.limits
    source_hash, request_hash = _hash(_recipe_content(recipe)), _hash(_request_content(request))
    rejections, candidates, attempts = [], {}, 0

    def finish(status):
        return VariantGenerationResult(
            status=status,
            request_hash=request_hash,
            recipe_source_hash=source_hash,
            candidates=tuple(candidates[k] for k in sorted(candidates))
            if status == "COMPLETE"
            else (),
            rejections=tuple(
                sorted(
                    rejections,
                    key=lambda r: (
                        r.code,
                        str(r.tier_id or ""),
                        tuple(map(str, r.rule_ids)),
                        r.detail,
                    ),
                )
            ),
            attempts=attempts,
        )

    def reject(code, detail, tier=None, selected=()):
        rejections.append(
            CulinaryGenerationRejection(
                code=code,
                detail=detail,
                tier_id=tier,
                rule_ids=selected,
            )
        )

    tiers = {t.servings: t for t in recipe.portion_tiers}
    servings = set(demand.serving_counts or (recipe.base_servings,))
    rules = {r.id: r for r in recipe.variant_rules}
    if not servings <= tiers.keys() or any(
        r not in rules for selection in demand.rule_selections for r in selection.rule_ids
    ):
        reject("INVALID_DEMAND", "Requested tier or rule is not authored for this RecipeVersion")
        return finish("INVALID_DEMAND")

    selections = {(): {"DEFAULT"}}

    def add(ids, trigger):
        ids = tuple(sorted(ids, key=str))
        selections.setdefault(ids, set()).add(trigger)

    targets = set(demand.ingredient_targets)
    for rule in recipe.variant_rules:
        if rule.replacement_ingredient_id in targets:
            add((rule.id,), "INGREDIENT_TARGET")
    for combo in recipe.approved_combinations:
        if all(rules[r].replacement_ingredient_id in targets for r in combo.rule_ids):
            add(combo.rule_ids, "INGREDIENT_TARGET")
    for selection in demand.rule_selections:
        add(selection.rule_ids, "AUTHORED_SELECTION")
    if len(selections) * len(servings) > limits.max_attempts:
        reject("LIMIT_EXCEEDED", "Demand expansion exceeds max_attempts; no partial output")
        return finish("LIMIT_EXCEEDED")

    exclusions = set(demand.excluded_ingredient_ids)
    approved = {frozenset(c.rule_ids) for c in recipe.approved_combinations}
    for tier in sorted((tiers[n] for n in servings), key=lambda t: str(t.id)):
        for selected, triggers in sorted(selections.items(), key=lambda p: tuple(map(str, p[0]))):
            attempts += 1
            chosen = [rules[r] for r in selected]
            if (
                len(set(selected)) != len(selected)
                or len({r.requirement_id for r in chosen}) != len(chosen)
                or (sum(r.structural for r in chosen) > 1 and frozenset(selected) not in approved)
            ):
                reject(
                    "UNAUTHORIZED_SELECTION",
                    "Rule set lacks exact authored authorization",
                    tier.id,
                    selected,
                )
                continue
            replacements = {r.requirement_id: r.replacement_ingredient_id for r in chosen}
            paths = {(t.requirement_id, t.ingredient_id) for t in recipe.transformations}
            if any(
                (i.id, i.ingredient_id) in paths
                and (i.id, replacements.get(i.id, i.ingredient_id)) not in paths
                for i in recipe.ingredients
            ):
                reject(
                    "UNRESOLVABLE_PATH",
                    "Selected path lacks compatible authored resolution",
                    tier.id,
                    selected,
                )
                continue
            ingredients, transformations, count = resolve_culinary_binding(
                recipe, tier.id, selected, {i.id: 0 for i in recipe.ingredients}
            )
            if any(i.ingredient_id in exclusions for i in ingredients):
                reject(
                    "EXCLUDED_INGREDIENT",
                    "Resolved ingredient excluded by caller demand",
                    tier.id,
                    selected,
                )
                continue
            fields = dict(
                recipe_version_id=recipe.id,
                recipe_source_hash=source_hash,
                tier_id=tier.id,
                serving_count=count,
                selected_rule_ids=selected,
                resolved_ingredients=tuple(
                    sorted(ingredients, key=lambda i: str(i.requirement_id))
                ),
                transformations=tuple(sorted(transformations, key=lambda t: str(t.id))),
                provenance=recipe.provenance,
                triggers=tuple(sorted(triggers)),
            )
            tmp = CulinaryCandidateDraft.model_construct(**fields)
            candidate = CulinaryCandidateDraft(**fields, fingerprint=tmp.expected_fingerprint())
            candidates[candidate.fingerprint] = candidate
            if len(candidates) > limits.max_candidates:
                reject(
                    "LIMIT_EXCEEDED", "Unique candidates exceed max_candidates; no partial output"
                )
                return finish("LIMIT_EXCEEDED")
    return finish("COMPLETE" if candidates else "NO_CANDIDATES")
