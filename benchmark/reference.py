"""Independent exhaustive reference: enumerates choices and uses FEFO arithmetic, no OR-Tools."""

import itertools
import math

from benchmark.schema import Scenario, SolveResult


def solve_reference(scenario: Scenario, max_combinations: int) -> tuple[SolveResult | None, str]:
    options = [
        [
            c
            for c in scenario.candidates
            if c.slot_id == slot.id
            and not set(c.ingredients).intersection(scenario.excluded_ingredients)
        ]
        for slot in scenario.slots
    ]
    count = math.prod(map(len, options))
    if count > max_combinations:
        return None, "COMBINATION_LIMIT"
    best = None
    products = {p.ingredient_id: p for p in scenario.products}
    # Conservative uncertainty classification is independently expressed here.
    incomplete = False
    for candidates in options:
        for candidate in candidates:
            for ingredient, quantity in candidate.ingredients.items():
                if quantity <= 0:
                    continue
                product = products.get(ingredient)
                if product is None or product.price_minor is None:
                    incomplete = True
                elif product.price_state != "fresh" and product.price_state != "fallback":
                    incomplete = True
    for assignment in itertools.product(*options):
        loss = 0
        valid = True
        for day in range(scenario.horizon_days):
            day_slots = {s.id for s in scenario.slots if s.day == day}
            for band in scenario.bands:
                amount = sum(
                    c.nutrients[band.nutrient] for c in assignment if c.slot_id in day_slots
                )
                if amount < band.hard_min or amount > band.hard_max:
                    valid = False
                    break
                loss += (
                    max(band.comfort_min - amount, amount - band.comfort_max, 0)
                    * (10_000)
                    // band.normalization_unit
                )
        if not valid:
            continue
        if any(
            quantity and ingredient not in products
            for candidate in assignment
            for ingredient, quantity in candidate.ingredients.items()
        ):
            incomplete = True
            continue
        stock = {lot.id: lot.units for lot in scenario.lots}
        use = {lot.id: {} for lot in scenario.lots}
        needs = dict.fromkeys(products, 0)
        by_slot = {c.slot_id: c for c in assignment}
        for slot in sorted(scenario.slots, key=lambda s: (s.day, s.id)):
            for ingredient, quantity in by_slot[slot.id].ingredients.items():
                need = quantity
                eligible = sorted(
                    (
                        lot
                        for lot in scenario.lots
                        if lot.ingredient_id == ingredient and lot.expires_day >= slot.day
                    ),
                    key=lambda lot: (lot.expires_day, lot.id),
                )
                for lot in eligible:
                    taken = min(need, stock[lot.id])
                    use[lot.id][slot.id] = taken
                    stock[lot.id] -= taken
                    need -= taken
                needs[ingredient] += need
        packs = {
            ingredient: (quantity + products[ingredient].pack_units - 1)
            // products[ingredient].pack_units
            for ingredient, quantity in needs.items()
        }
        # This decision is deliberately implemented independently of cpsat.purchasable.
        if any(
            packs[key] > 0
            and (product.price_minor is None or product.price_state not in ("fresh", "fallback"))
            for key, product in products.items()
        ):
            incomplete = True
            continue
        cost = sum(packs[key] * (product.price_minor or 0) for key, product in products.items())
        if scenario.budget_mode == "SPEND_LIMIT":
            scenario_costs = [cost] + [
                sum(packs[key] * prices[key] for key in products)
                for name, prices in scenario.stress_prices.items()
                if name in scenario.stress_policy.required_scenarios
            ]
            if max(scenario_costs) > scenario.budget_minor:
                continue
        objective = [loss, cost]
        if best is None or objective < best.objective:
            best = SolveResult(
                status="OPTIMAL",
                selected={c.slot_id: c.id for c in assignment},
                packages=packs,
                lot_use=use,
                objective=objective,
                phases_completed=2,
            )
    if best is not None:
        return best, "EXHAUSTIVE_TRUSTED_EVIDENCE"
    return SolveResult(
        status="DATA_INSUFFICIENT" if incomplete else "PROVEN_INFEASIBLE",
        reason="NO_TRUSTED_SOLUTION_WITH_INCOMPLETE_DATA" if incomplete else None,
    ), "EXHAUSTIVE_CERTIFIED"
