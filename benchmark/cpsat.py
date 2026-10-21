"""Actual CP-SAT micro-model. Deliberately excludes full V4 policy and batch semantics."""

from ortools.sat.python import cp_model

from benchmark.schema import Scenario, SolveConfig, SolveResult


def purchasable(product) -> bool:
    """Solver-only evidence decision; reference and auditor must not call this."""
    return product.price_minor is not None and product.price_state in {"fresh", "fallback"}


class SyntheticCpSatAdapter:
    version = "synthetic-cpsat-v2"

    def solve(self, scenario: Scenario, config: SolveConfig) -> SolveResult:
        products = {p.ingredient_id: p for p in scenario.products}
        permitted = [
            c
            for c in scenario.candidates
            if not set(c.ingredients).intersection(scenario.excluded_ingredients)
        ]
        relevant = {key for c in permitted for key, value in c.ingredients.items() if value}
        unknown_mapping = {
            c.id
            for c in permitted
            if any(quantity and key not in products for key, quantity in c.ingredients.items())
        }
        missing_evidence = bool(unknown_mapping) or any(
            key in relevant and not purchasable(product) for key, product in products.items()
        )
        model = cp_model.CpModel()
        choices = {c.id: model.new_bool_var(c.id) for c in scenario.candidates}
        for slot in scenario.slots:
            model.add_exactly_one(
                choices[c.id] for c in scenario.candidates if c.slot_id == slot.id
            )
        for c in scenario.candidates:
            if c.id in unknown_mapping or set(c.ingredients) & set(scenario.excluded_ingredients):
                model.add(choices[c.id] == 0)
        penalties = []
        for day in range(scenario.horizon_days):
            ids = {s.id for s in scenario.slots if s.day == day}
            for band in scenario.bands:
                total = sum(
                    c.nutrients[band.nutrient] * choices[c.id]
                    for c in scenario.candidates
                    if c.slot_id in ids
                )
                model.add(total >= band.hard_min)
                model.add(total <= band.hard_max)
                deviation = model.new_int_var(0, 1_000_000, f"deviation_{day}_{band.nutrient}")
                model.add_max_equality(
                    deviation, [band.comfort_min - total, total - band.comfort_max, 0]
                )
                normalized = model.new_int_var(
                    0, 10_000_000_000, f"normalized_{day}_{band.nutrient}"
                )
                model.add_division_equality(normalized, deviation * 10_000, band.normalization_unit)
                penalties.append(normalized)
        lots = {}
        for lot in scenario.lots:
            eligible = {}
            for slot in scenario.slots:
                if slot.day <= lot.expires_day:
                    eligible[slot.id] = model.new_int_var(0, lot.units, f"lot_{lot.id}_{slot.id}")
            model.add(sum(eligible.values()) <= lot.units)
            lots[lot.id] = eligible
        packages = {}
        for product in scenario.products:
            ingredient = product.ingredient_id
            maximum = sum(c.ingredients.get(ingredient, 0) for c in scenario.candidates)
            pack_bound = (maximum + product.pack_units - 1) // product.pack_units
            if not purchasable(product):
                pack_bound = 0
            packages[ingredient] = model.new_int_var(0, pack_bound, f"packs_{ingredient}")
            purchased_use = []
            for slot in scenario.slots:
                demand = sum(
                    c.ingredients.get(ingredient, 0) * choices[c.id]
                    for c in scenario.candidates
                    if c.slot_id == slot.id
                )
                stock = sum(
                    lots[lot.id][slot.id]
                    for lot in scenario.lots
                    if lot.ingredient_id == ingredient and slot.id in lots[lot.id]
                )
                bought = model.new_int_var(0, maximum, f"bought_{ingredient}_{slot.id}")
                model.add(stock + bought == demand)
                purchased_use.append(bought)
            model.add(sum(purchased_use) <= packages[ingredient] * product.pack_units)
        cost = sum(packages[p.ingredient_id] * (p.price_minor or 0) for p in scenario.products)
        if scenario.budget_mode == "SPEND_LIMIT":
            model.add(cost <= scenario.budget_minor)
            for name in scenario.stress_policy.required_scenarios:
                if name == "BASE":
                    continue
                prices = scenario.stress_prices[name]
                model.add(
                    sum(packages[key] * price for key, price in prices.items())
                    <= scenario.budget_minor
                )
        nutrition_loss = sum(penalties)
        model.minimize(nutrition_loss)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = config.time_limit_seconds
        solver.parameters.num_search_workers = config.workers
        solver.parameters.random_seed = config.seed

        def capture(status: str, phases: int) -> SolveResult:
            return SolveResult(
                status=status,
                selected={
                    s.id: next(
                        c.id
                        for c in scenario.candidates
                        if c.slot_id == s.id and solver.value(choices[c.id])
                    )
                    for s in scenario.slots
                },
                packages={key: solver.value(value) for key, value in packages.items()},
                lot_use={
                    key: {slot: solver.value(value) for slot, value in uses.items()}
                    for key, uses in lots.items()
                },
                objective=[solver.value(nutrition_loss), solver.value(cost)],
                phases_completed=phases,
                reason="OPTIMAL_WITHIN_TRUSTED_EVIDENCE" if missing_evidence else None,
            )

        status = solver.solve(model)
        if status == cp_model.INFEASIBLE:
            return SolveResult(
                status="DATA_INSUFFICIENT" if missing_evidence else "PROVEN_INFEASIBLE",
                reason="NO_TRUSTED_SOLUTION_WITH_INCOMPLETE_DATA" if missing_evidence else None,
            )
        if status == cp_model.UNKNOWN:
            return SolveResult(status="UNKNOWN_TIME_LIMIT", reason="NO_INCUMBENT_BEFORE_LIMIT")
        if status == cp_model.MODEL_INVALID:
            return SolveResult(status="ERROR", reason=solver.solution_info())
        first = capture("FEASIBLE_BEST_EFFORT", 1)
        if status != cp_model.OPTIMAL:
            return first
        model.add(nutrition_loss == first.objective[0])
        model.minimize(cost)
        status = solver.solve(model)
        if status == cp_model.MODEL_INVALID:
            return SolveResult(status="ERROR", reason=solver.solution_info())
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return first.model_copy(update={"reason": "ECONOMIC_PHASE_DID_NOT_COMPLETE"})
        return capture("OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE_BEST_EFFORT", 2)
