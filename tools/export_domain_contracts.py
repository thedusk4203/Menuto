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
from app.modules.cooking.contracts import PlannedBatchAllocationIntent, PlannedCookingBatchIntent
from app.modules.households.contracts import HouseholdCreate, HouseholdCreated, MealParticipants
from app.modules.inventory.contracts import (
    AcquireInventoryCommand,
    BatchFlowLinkDraft,
    ConsumeInventoryCommand,
    DiscardInventoryCommand,
    ExpireInventoryCommand,
    InventoryLot,
    InventoryMovement,
    InventoryPosition,
    InventoryReservation,
    InventoryReservationRelease,
    PhysicalEvidence,
    PhysicalInventorySnapshot,
    ReconcileInventoryCommand,
    ReleaseReservationCommand,
    ReserveInventoryCommand,
    RetailSourcedAPAssetDraft,
)
from app.modules.nutrition.contracts import MemberNutritionProfileWrite, MemberSafetyConstraint
from app.modules.planning.contracts import (
    ActivePlanSnapshot,
    CreatePlanWorkspaceCommand,
    HorizonCommitmentsDraft,
    MealIntent,
    PlanIntentGraph,
    PlanProposalSnapshot,
    PlanRevisionSnapshot,
    PlanWorkspaceDraft,
    ProposePlanCommand,
    PublishPlanRevisionCommand,
    ReservationIntent,
)
from app.modules.recipes.contracts import (
    GroundedRecipeVariantDraft,
    PreparationTransformationFact,
    QuantityAdjustmentPolicy,
    RecipeFact,
    RecipeIngredientFact,
    RecipePortionTierFact,
    RecipeProvenance,
    RecipeRuleCombinationFact,
    RecipeVariantRuleFact,
    RecipeVersionSnapshot,
    ResolvedRecipeIngredient,
    ScalingPolicy,
)
from app.modules.retail.contracts import (
    IngredientProductMapFact,
    PackageFact,
    PlanningPriceQuoteDraft,
    PlanningProcurementOptionDraft,
    PriceEvidenceAssessmentDraft,
    PriceObservationFact,
    ProcurementClassFact,
    ProcurementClassMemberFact,
    ProcurementSnapshotDraft,
    ProductIngredientConversionFact,
    PurchaseIntent,
    ReferencePriceBookFact,
    ReferencePriceEntryFact,
    ReferencePricePair,
    RetailerFact,
    RetailerStatusFact,
    RetailPriceCalibrationFact,
    RetailProductFact,
    SourceCoverageDraft,
    StoreRegionFact,
)
from app.modules.shopping.contracts import (
    ObservedAcquisitionCoverageDraft,
    ShoppingDemandContributionIntent,
    ShoppingRequirementIntent,
)
from pydantic.json_schema import models_json_schema

CONTRACTS = (
    PlanIntentGraph,
    MealIntent,
    ReservationIntent,
    PlanWorkspaceDraft,
    ProposePlanCommand,
    PlanProposalSnapshot,
    PublishPlanRevisionCommand,
    PlanRevisionSnapshot,
    HorizonCommitmentsDraft,
    CreatePlanWorkspaceCommand,
    ActivePlanSnapshot,
    ShoppingRequirementIntent,
    ShoppingDemandContributionIntent,
    ObservedAcquisitionCoverageDraft,
    PlannedCookingBatchIntent,
    PlannedBatchAllocationIntent,
    AcquireInventoryCommand,
    BatchFlowLinkDraft,
    ConsumeInventoryCommand,
    DiscardInventoryCommand,
    ExpireInventoryCommand,
    InventoryLot,
    InventoryMovement,
    InventoryPosition,
    InventoryReservation,
    InventoryReservationRelease,
    PhysicalEvidence,
    PhysicalInventorySnapshot,
    ReconcileInventoryCommand,
    ReleaseReservationCommand,
    ReserveInventoryCommand,
    RecipeFact,
    RecipeVersionSnapshot,
    RecipeIngredientFact,
    RecipePortionTierFact,
    RecipeVariantRuleFact,
    RecipeRuleCombinationFact,
    PreparationTransformationFact,
    ScalingPolicy,
    QuantityAdjustmentPolicy,
    RecipeProvenance,
    ResolvedRecipeIngredient,
    GroundedRecipeVariantDraft,
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
    RetailerFact,
    RetailerStatusFact,
    ReferencePricePair,
    SourceCoverageDraft,
    StoreRegionFact,
    RetailProductFact,
    PackageFact,
    PurchaseIntent,
    IngredientProductMapFact,
    ProductIngredientConversionFact,
    PriceObservationFact,
    ReferencePriceBookFact,
    ReferencePriceEntryFact,
    RetailPriceCalibrationFact,
    ProcurementClassFact,
    ProcurementClassMemberFact,
    PlanningPriceQuoteDraft,
    PlanningProcurementOptionDraft,
    ProcurementSnapshotDraft,
    PriceEvidenceAssessmentDraft,
    RetailSourcedAPAssetDraft,
)


def export() -> str:
    _, schema = models_json_schema(
        [(model, "validation") for model in CONTRACTS],
        title="Menuto M0 domain contracts — draft handoffs, no business HTTP endpoints",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "urn:menuto:domain:foundation:9"
    schema["description"] = (
        "Bundle of named definitions; select a $defs reference to validate a document. "
        "Planner, validation and mutation handoffs are m0 drafts. "
        "Retail facts use retail-v2; reference calibration and price pairs remain DRAFT. "
        "Recipe authored snapshots use recipe-v1; culinary grounded inputs remain DRAFT. "
        "V1 substitutions are mass-only; preparation yield is net and path-specific. "
        "Plan intent v1 legacy/v2 contribution graphs, guarded scope/cut-line revision seams; "
        "PRECOMMIT authority not installed. "
        "No production activation or full independent validation is provided. "
        "Inventory-v1 physical commands/facts are explicit confirmation only; no projections. "
        "Physical snapshot and batch-flow handoffs remain DRAFT, not activation-ready. "
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
