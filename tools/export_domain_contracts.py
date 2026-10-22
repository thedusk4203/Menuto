"""Export draft domain contracts separately from the live HTTP OpenAPI document."""

import argparse
import json
from pathlib import Path

from app.domain.snapshots import (
    MutationFixtureDraft,
    PlannerOutputDraft,
    PlannerRequestDraft,
    PreparedFoodAssetFact,
    RawIngredientAssetFact,
    ValidationReportDraft,
    ValidationSubjectDraft,
    WriteCommand,
)
from app.domain.units import (
    CalculatedQuantity,
    Money,
    Provenance,
    Quantity,
    QuantizationPolicy,
    QuantizationResult,
    YieldConversion,
)
from app.modules.catalog.contracts import IngredientCreate, NutritionFact
from app.modules.households.contracts import HouseholdCreate, HouseholdCreated, MealParticipants
from app.modules.nutrition.contracts import MemberNutritionProfileWrite, MemberSafetyConstraint
from pydantic.json_schema import models_json_schema

CONTRACTS = (
    Quantity,
    CalculatedQuantity,
    QuantizationPolicy,
    QuantizationResult,
    Provenance,
    RawIngredientAssetFact,
    PreparedFoodAssetFact,
    Money,
    YieldConversion,
    IngredientCreate,
    NutritionFact,
    HouseholdCreate,
    HouseholdCreated,
    MealParticipants,
    PlannerRequestDraft,
    PlannerOutputDraft,
    ValidationSubjectDraft,
    ValidationReportDraft,
    MutationFixtureDraft,
    WriteCommand,
    MemberNutritionProfileWrite,
    MemberSafetyConstraint,
)


def export() -> str:
    _, schema = models_json_schema(
        [(model, "validation") for model in CONTRACTS],
        title="Menuto M0 domain contracts — draft handoffs, no business HTTP endpoints",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "urn:menuto:domain:foundation:2"
    schema["description"] = (
        "Bundle of named definitions; select a $defs reference to validate a document. "
        "Planner, validation and mutation handoffs are m0 drafts. "
        "Cross-field semantic guards run in Python, not JSON Schema alone."
    )
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = Path(__file__).resolve().parents[1] / "packages/contracts/domain.schema.json"
    content = export()
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            raise SystemExit("Domain contract drift; run tools/export_domain_contracts.py")
        print("Domain contract schema matches.")
    else:
        target.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
