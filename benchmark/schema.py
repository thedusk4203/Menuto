"""Versioned neutral fixtures. All quantities and nutrition values are synthetic integers."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Quantity = Annotated[int, Field(ge=0, le=1_000_000, strict=True)]
Positive = Annotated[int, Field(gt=0, le=1_000_000, strict=True)]
Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Slot(Record):
    id: Identifier
    day: Annotated[int, Field(ge=0, le=6)]


class Product(Record):
    ingredient_id: Identifier
    pack_units: Positive
    price_minor: Quantity | None
    price_state: Literal["fresh", "stale", "fallback", "missing"] = "fresh"
    valid_for_full_horizon: Literal[True] = True


class Lot(Record):
    id: Identifier
    ingredient_id: Identifier
    units: Quantity
    expires_day: Annotated[int, Field(ge=0, le=6)]


class Candidate(Record):
    id: Identifier
    slot_id: Identifier
    ingredients: dict[Identifier, Quantity]
    nutrients: dict[Identifier, Quantity]


class Band(Record):
    nutrient: Identifier
    hard_min: Quantity
    hard_max: Quantity
    comfort_min: Quantity
    comfort_max: Quantity
    normalization_unit: Positive

    @model_validator(mode="after")
    def ordered_bounds(self):
        if not self.hard_min <= self.comfort_min <= self.comfort_max <= self.hard_max:
            raise ValueError("hard/comfort bands are not nested")
        return self


class StressScenarioPolicy(Record):
    version: Identifier
    required_scenarios: list[Identifier] = Field(min_length=1)
    base_only_justification: str | None = None

    @model_validator(mode="after")
    def explicit_required_set(self):
        names = self.required_scenarios
        if len(names) != len(set(names)) or "BASE" not in names:
            raise ValueError("stress policy needs unique scenarios including BASE")
        if names == ["BASE"] and not (
            self.base_only_justification and self.base_only_justification.strip()
        ):
            raise ValueError("BASE-only policy requires an explicit justification")
        return self


class Scenario(Record):
    schema_version: Literal["synthetic-v2"] = "synthetic-v2"
    id: Identifier
    provenance: Literal["synthetic-from-spec-v1.2"] = "synthetic-from-spec-v1.2"
    horizon_days: Annotated[int, Field(ge=1, le=7)]
    tags: list[str]
    goal_preset: Literal["maintain", "high-protein", "calorie-deficit"] = "maintain"
    slots: list[Slot] = Field(min_length=1, max_length=21)
    products: list[Product] = Field(min_length=1, max_length=8)
    candidates: list[Candidate] = Field(min_length=1, max_length=84)
    lots: list[Lot] = Field(default_factory=list, max_length=12)
    bands: list[Band] = Field(min_length=1, max_length=4)
    excluded_ingredients: list[Identifier] = Field(default_factory=list)
    budget_mode: Literal["NONE", "TARGET", "SPEND_LIMIT"] = "NONE"
    budget_minor: Quantity | None = None
    stress_prices: dict[Identifier, dict[Identifier, Quantity]] = Field(default_factory=dict)
    stress_policy: StressScenarioPolicy | None = None
    expected_status: Literal["OPTIMAL", "PROVEN_INFEASIBLE", "DATA_INSUFFICIENT"]

    @model_validator(mode="after")
    def consistent_references(self):
        for values in (
            [s.id for s in self.slots],
            [p.ingredient_id for p in self.products],
            [c.id for c in self.candidates],
            [lot.id for lot in self.lots],
            [band.nutrient for band in self.bands],
        ):
            if len(values) != len(set(values)):
                raise ValueError("duplicate identifier")
        slot_ids = {s.id for s in self.slots}
        ingredients = {p.ingredient_id for p in self.products}
        if any(c.slot_id not in slot_ids for c in self.candidates):
            raise ValueError("candidate refers to unknown slot")
        if any(lot.ingredient_id not in ingredients for lot in self.lots):
            raise ValueError("lot refers to unknown product")
        if {s.day for s in self.slots} != set(range(self.horizon_days)):
            raise ValueError("each day in the horizon must have slots")
        if self.budget_mode == "NONE" and self.budget_minor is not None:
            raise ValueError("NONE has no budget amount")
        if self.budget_mode != "NONE" and self.budget_minor is None:
            raise ValueError("budget contract needs an amount")
        if "BASE" in self.stress_prices:
            raise ValueError("BASE is derived from product prices, not a competing override")
        if self.budget_mode == "SPEND_LIMIT":
            if self.stress_policy is None:
                raise ValueError("SPEND_LIMIT requires an explicit stress policy")
            missing = (
                set(self.stress_policy.required_scenarios) - {"BASE"} - self.stress_prices.keys()
            )
            if missing:
                raise ValueError(f"missing required stress coefficients: {sorted(missing)}")
        elif self.stress_policy is not None or self.stress_prices:
            raise ValueError(
                "stress policy/scenarios only apply to SPEND_LIMIT in this micro-model"
            )
        if any(set(prices) != ingredients for prices in self.stress_prices.values()):
            raise ValueError("stress prices must cover every product")
        if any(not {b.nutrient for b in self.bands} <= c.nutrients.keys() for c in self.candidates):
            raise ValueError("candidate lacks required nutrient data")
        return self


class SolveConfig(Record):
    time_limit_seconds: float = Field(default=5.0, ge=0, le=300)
    seed: int = Field(default=42, ge=0)
    workers: Literal[1] = 1


class SolveResult(Record):
    status: Literal[
        "OPTIMAL",
        "FEASIBLE_BEST_EFFORT",
        "PROVEN_INFEASIBLE",
        "UNKNOWN_TIME_LIMIT",
        "DATA_INSUFFICIENT",
        "ERROR",
    ]
    selected: dict[str, str] = Field(default_factory=dict)
    packages: dict[str, int] = Field(default_factory=dict)
    lot_use: dict[str, dict[str, int]] = Field(default_factory=dict)
    objective: list[int] | None = None
    reason: str | None = None
    phases_completed: int = 0
