"""Validate evidence actually used by a proposed solution. No optimizer imports."""

from benchmark.schema import Scenario, SolveResult


def audit_solution_data(scenario: Scenario, result: SolveResult) -> list[str]:
    errors = []
    by_id = {c.id: c for c in scenario.candidates}
    products = {p.ingredient_id: p for p in scenario.products}
    for candidate_id in result.selected.values():
        candidate = by_id.get(candidate_id)
        if candidate is not None:
            for ingredient, quantity in candidate.ingredients.items():
                if quantity > 0 and ingredient not in products:
                    errors.append("SELECTED_PRODUCT_MAPPING_MISSING")
    for ingredient, count in result.packages.items():
        if count <= 0:
            continue
        product = products.get(ingredient)
        if product is None or product.price_minor is None:
            errors.append("PURCHASE_PRICE_MISSING")
        elif product.price_state not in {"fresh", "fallback"}:
            errors.append("PURCHASE_EVIDENCE_UNUSABLE")
    return sorted(set(errors))
