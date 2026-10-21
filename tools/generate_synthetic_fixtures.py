"""Generate deterministic synthetic fixtures; none are clinical or real retail data."""

import argparse
import copy
import json
from pathlib import Path


def base(identifier: str, days: int = 1, meals: int = 2, options: int = 2) -> dict:
    slots = [{"id": f"s{i}", "day": i // meals} for i in range(days * meals)]
    candidates = []
    for index, slot in enumerate(slots):
        for choice in range(options if index < 2 else 1):
            quantity, calories, protein = (
                (4, 500, 25)
                if choice == 0
                else (3, 450, 20)
                if choice == 1
                else (choice + 3, 450 + choice * 50, 20 + choice * 5)
            )
            candidates.append(
                {
                    "id": f"{slot['id']}_c{choice}",
                    "slot_id": slot["id"],
                    "ingredients": {"food": quantity},
                    "nutrients": {"calories": calories, "protein": protein},
                }
            )
    return {
        "schema_version": "synthetic-v1",
        "id": identifier,
        "provenance": "synthetic-from-spec-v1.2",
        "horizon_days": days,
        "tags": [
            f"{days}-day",
            f"{meals}-meals",
            "maintain",
            "small-catalog",
            "fresh-price",
            "no-inventory",
            "no-budget",
        ],
        "slots": slots,
        "candidates": candidates,
        "products": [
            {
                "ingredient_id": "food",
                "pack_units": 5,
                "price_minor": 300,
                "price_state": "fresh",
                "valid_for_full_horizon": True,
            }
        ],
        "bands": [
            {
                "nutrient": "calories",
                "hard_min": 400 * meals,
                "hard_max": 600 * meals,
                "comfort_min": 450 * meals,
                "comfort_max": 500 * meals,
                "normalization_unit": 500 * meals,
            },
            {
                "nutrient": "protein",
                "hard_min": 20 * meals,
                "hard_max": 35 * meals,
                "comfort_min": 22 * meals,
                "comfort_max": 27 * meals,
                "normalization_unit": 25 * meals,
            },
        ],
        "lots": [],
        "excluded_ingredients": [],
        "budget_mode": "NONE",
        "budget_minor": None,
        "stress_prices": {},
        "expected_status": "OPTIMAL",
    }


def fixtures() -> dict[str, dict]:
    result = {}

    def add(filename, scenario, *tags):
        scenario["tags"] = list(dict.fromkeys(scenario["tags"] + list(tags)))
        result[filename + ".json"] = scenario

    add("01-baseline", base("baseline"))
    add("02-three-meals", base("three-meals", meals=3))
    add("03-three-day", base("three-day", days=3, options=3), "medium-catalog")
    add("04-seven-day", base("seven-day", days=7, meals=3, options=4), "large-catalog")
    tight = base("strict-tight")
    tight.update(budget_mode="SPEND_LIMIT", budget_minor=600)
    add("05-tight-budget", tight, "tight-budget")
    loose = base("strict-loose")
    loose.update(budget_mode="SPEND_LIMIT", budget_minor=10000)
    add("06-loose-budget", loose, "loose-budget")
    target = base("target-not-limit")
    target.update(budget_mode="TARGET", budget_minor=1)
    add("07-target-budget", target, "target-budget")
    rich = base("inventory-no-purchase")
    rich.update(
        budget_mode="SPEND_LIMIT",
        budget_minor=0,
        lots=[{"id": "stock", "ingredient_id": "food", "units": 8, "expires_day": 0}],
    )
    add("08-rich-inventory", rich, "rich-inventory")
    expiry = base("expiry-cannot-fund-later", days=3)
    expiry.update(
        budget_mode="SPEND_LIMIT",
        budget_minor=0,
        lots=[{"id": "stock", "ingredient_id": "food", "units": 24, "expires_day": 0}],
        expected_status="PROVEN_INFEASIBLE",
    )
    add("09-expiry", expiry, "expiring-inventory")
    excluded = base("hard-exclusion")
    excluded.update(excluded_ingredients=["food"], expected_status="PROVEN_INFEASIBLE")
    add("10-exclusion", excluded, "hard-exclusion")
    package = base("large-package")
    package["products"][0].update(pack_units=50, price_minor=1500)
    package.update(
        budget_mode="SPEND_LIMIT", budget_minor=1000, expected_status="PROVEN_INFEASIBLE"
    )
    add("11-large-package", package, "large-package")
    stale = base("stale-price")
    stale["products"][0]["price_state"] = "stale"
    stale["expected_status"] = "DATA_INSUFFICIENT"
    add("12-stale-price", stale, "stale-price")
    fallback = base("fallback-price")
    fallback["products"][0].update(price_state="fallback", price_minor=350)
    add("13-fallback-price", fallback, "fallback-price")
    missing = base("missing-mapping")
    missing["candidates"][0]["ingredients"] = {"unmapped": 4}
    missing["expected_status"] = "DATA_INSUFFICIENT"
    add("14-missing-mapping", missing, "missing-product-map")
    stress = base("stress-exceeds-spend-limit")
    stress.update(
        budget_mode="SPEND_LIMIT",
        budget_minor=1000,
        stress_prices={
            "ADVERSE_WEIGHT": {"food": 700},
            "BACKUP": {"food": 600},
            "CATEGORY_STRESS": {"food": 650},
        },
        expected_status="PROVEN_INFEASIBLE",
    )
    add("15-stress-scenarios", stress, "budget-stress")
    protein = copy.deepcopy(base("high-protein"))
    protein["bands"][1].update(hard_min=50, comfort_min=50)
    add("16-high-protein", protein, "high-protein")
    deficit = base("calorie-deficit")
    deficit["bands"][0].update(hard_min=800, comfort_min=850, comfort_max=950, hard_max=1000)
    add("17-calorie-deficit", deficit, "calorie-deficit")
    missing_price = base("missing-price")
    missing_price["products"][0].update(price_minor=None, price_state="missing")
    missing_price["expected_status"] = "DATA_INSUFFICIENT"
    add("18-missing-price", missing_price, "missing-price")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = Path(__file__).resolve().parents[1] / "benchmark/scenarios"
    target.mkdir(parents=True, exist_ok=True)
    for name, data in fixtures().items():
        content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        path = target / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Fixture differs: {name}")
        else:
            path.write_text(content, encoding="utf-8")
    print(f"{len(fixtures())} synthetic fixtures {'verified' if args.check else 'generated'}.")


if __name__ == "__main__":
    main()
