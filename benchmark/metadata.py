"""Descriptive tags derived from final synthetic data, never accumulated through mutations."""

from collections import Counter
from collections.abc import Mapping
from typing import Any


def derive_tags(scenario: Mapping[str, Any]) -> list[str]:
    days = scenario["horizon_days"]
    daily_meals = Counter(slot["day"] for slot in scenario["slots"])
    goal = scenario.get("goal_preset", "maintain")
    count = len(scenario["candidates"])
    catalog = "small" if count <= 4 else "medium" if count <= 12 else "large"
    tags = [
        f"{days}-day",
        *(f"{n}-meals" for n in sorted(set(daily_meals.values()))),
        goal,
        f"{catalog}-catalog",
        f"candidate-count-{count}",
    ]
    mode = scenario["budget_mode"]
    tags.append(
        {"NONE": "no-budget", "TARGET": "target-budget", "SPEND_LIMIT": "spend-limit"}[mode]
    )
    if scenario["budget_minor"] is not None:
        tags.append(f"budget-cap-{scenario['budget_minor']}")
    lots = [lot for lot in scenario["lots"] if lot["units"] > 0]
    if lots:
        tags.append("has-inventory")
        tags.append(
            "expiring-inventory"
            if any(lot["expires_day"] < days - 1 for lot in lots)
            else "within-horizon-inventory"
        )
    else:
        tags.append("no-inventory")
    states = {
        p["price_state"] if p["price_minor"] is not None else "missing"
        for p in scenario["products"]
    }
    tags.append(f"{next(iter(states))}-price" if len(states) == 1 else "mixed-price-evidence")
    tags.extend(f"pack-step-{n}" for n in sorted({p["pack_units"] for p in scenario["products"]}))
    known = {p["ingredient_id"] for p in scenario["products"]}
    if any(
        quantity and ingredient not in known
        for c in scenario["candidates"]
        for ingredient, quantity in c["ingredients"].items()
    ):
        tags.append("missing-product-map")
    if scenario["excluded_ingredients"]:
        tags.append("hard-exclusion")
    policy = scenario.get("stress_policy")
    if policy:
        tags.append(
            "budget-stress" if set(policy["required_scenarios"]) - {"BASE"} else "base-only-policy"
        )
    return tags
