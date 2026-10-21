"""Independent arithmetic audit of a returned micro-model solution; not Validator V2."""

from benchmark.schema import Scenario, SolveResult


def verify(scenario: Scenario, result: SolveResult) -> list[str]:
    errors = []
    if result.status not in {"OPTIMAL", "FEASIBLE_BEST_EFFORT"}:
        if result.selected or result.packages or result.lot_use or result.objective is not None:
            errors.append("NON_SOLUTION_HAS_DECISIONS")
        return errors
    choices = {c.id: c for c in scenario.candidates}
    slots = {s.id: s for s in scenario.slots}
    products = {p.ingredient_id: p for p in scenario.products}
    lots = {lot.id: lot for lot in scenario.lots}
    if set(result.selected) != slots.keys():
        return ["SLOT_COVERAGE"]
    picked = []
    for slot, candidate_id in result.selected.items():
        c = choices.get(candidate_id)
        if c is None or c.slot_id != slot:
            return ["INVALID_CANDIDATE"]
        if set(c.ingredients).intersection(scenario.excluded_ingredients):
            errors.append("EXCLUDED_INGREDIENT")
        picked.append(c)
    if set(result.packages) != products.keys():
        return errors + ["PACKAGE_COVERAGE"]
    for count in result.packages.values():
        if type(count) is not int or count < 0:
            return errors + ["INVALID_PACKAGE_COUNT"]
    used = {slot: dict.fromkeys(products, 0) for slot in slots}
    for lot_id, allocations in result.lot_use.items():
        lot = lots.get(lot_id)
        if lot is None:
            return errors + ["UNKNOWN_LOT"]
        if any(type(q) is not int or q < 0 for q in allocations.values()):
            return errors + ["INVALID_LOT_QUANTITY"]
        if sum(allocations.values()) > lot.units:
            errors.append("LOT_OVERDRAW")
        for slot_id, quantity in allocations.items():
            if slot_id not in slots:
                return errors + ["UNKNOWN_STOCK_SLOT"]
            if quantity and slots[slot_id].day > lot.expires_day:
                errors.append("EXPIRED_LOT")
            used[slot_id][lot.ingredient_id] += quantity
    for ingredient, product in products.items():
        purchased_demand = 0
        for c in picked:
            demand = c.ingredients.get(ingredient, 0)
            from_stock = used[c.slot_id][ingredient]
            if from_stock > demand:
                errors.append("STOCK_EXCEEDS_DEMAND")
            purchased_demand += max(0, demand - from_stock)
        if purchased_demand > result.packages[ingredient] * product.pack_units:
            errors.append("INSUFFICIENT_PROCUREMENT")
    loss = 0
    for day in range(scenario.horizon_days):
        daily = [c for c in picked if slots[c.slot_id].day == day]
        for band in scenario.bands:
            amount = sum(c.nutrients[band.nutrient] for c in daily)
            if not band.hard_min <= amount <= band.hard_max:
                errors.append("NUTRIENT_HARD_BOUND")
            distance = 0
            if amount < band.comfort_min:
                distance = band.comfort_min - amount
            elif amount > band.comfort_max:
                distance = amount - band.comfort_max
            loss += (distance * 10_000) // band.normalization_unit
    cost = sum(result.packages[key] * p.price_minor for key, p in products.items())
    if scenario.budget_mode == "SPEND_LIMIT":
        costs = [cost]
        for prices in scenario.stress_prices.values():
            costs.append(sum(result.packages[key] * prices[key] for key in products))
        if any(value > scenario.budget_minor for value in costs):
            errors.append("SPEND_LIMIT_VIOLATION")
    if result.objective != [loss, cost]:
        errors.append("OBJECTIVE_MISMATCH")
    return sorted(set(errors))
