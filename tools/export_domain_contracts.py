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
from app.modules.catalog.contracts import (
    AffinityFeatureTermFact,
    IngredientCreate,
    IngredientIdentityFact,
    NutritionFact,
    NutritionReferenceFact,
)
from app.modules.cooking.contracts import PlannedBatchAllocationIntent, PlannedCookingBatchIntent
from app.modules.households.contracts import (
    HouseholdCreate,
    HouseholdCreated,
    HouseholdMemberIdentity,
    MealParticipants,
)
from app.modules.inventory.contracts import (
    AcquireInventoryCommand,
    BatchFlowLinkDraft,
    ConsumeInventoryCommand,
    DiscardInventoryCommand,
    ExpireInventoryCommand,
    InventoryCandidateLot,
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
from app.modules.learning.contracts import (
    ExposureAllocationSupport,
    ExposurePreviewPolicy,
    ExposurePreviewRequest,
    ExposurePreviewSnapshot,
    ProposalExposureSource,
    RecipeCooldownAssessmentDraft,
    RecipeCooldownInput,
    RecipeCooldownPolicy,
    RecipeCooldownQuery,
    RecipeCooldownWitness,
    RecipeDecayBand,
    RecipeDecayInput,
    RecipeDecayPolicy,
    RecipeDecayTraceDraft,
    RecipeDecayTraceEntry,
    RecipeExposureIdentity,
    RecipeExposurePreviewDraft,
    RecipeExposurePreviewFact,
    RecipeRepeatEvidenceDraft,
    RetentionMultiplier,
)
from app.modules.nutrition.contracts import (
    CanonicalMemberSafetySnapshot,
    MemberNutritionProfileWrite,
    MemberSafetyConstraint,
    MemberSafetySourceFact,
    ResolvedNutrients,
    ResolvedNutritionPortion,
)
from app.modules.planning.contracts import (
    ActivePlanSnapshot,
    BoundActivePlanSnapshot,
    BoundCookingBatchIntent,
    BoundPlanIntentGraph,
    BoundPlanProposalSnapshot,
    BoundPlanRevisionSnapshot,
    CandidateGroundingRequest,
    CandidateGroundingResult,
    CandidateGroundingSources,
    CreatePlanWorkspaceCommand,
    CulinaryRequirementBinding,
    GroundedDishCandidate,
    GroundedIngredientFacts,
    GroundingIssue,
    GroundingNutritionSelection,
    HorizonCommitmentsDraft,
    MealIntent,
    ParetoShortlistDraft,
    PlanIntentGraph,
    PlannedCulinaryBinding,
    PlanProposalSnapshot,
    PlanRevisionSnapshot,
    PlanWorkspaceDraft,
    ProposeBoundPlanCommand,
    ProposePlanCommand,
    PublishPlanRevisionCommand,
    ReservationIntent,
    ShortlistDominanceWitness,
    ShortlistInputFailure,
    ShortlistPolicyDraft,
)
from app.modules.policy.contracts import ValidationCoveragePolicySnapshot
from app.modules.preferences.contracts import (
    ExplicitMemberPreferenceSnapshot,
    FeaturePreferenceTarget,
    IngredientPreferenceTarget,
    MemberPreferenceDeclarationFact,
    MemberPreferenceState,
    PreferenceWriteCommand,
    RecipePreferenceTarget,
    RetractMemberPreferenceCommand,
    SetMemberPreferenceCommand,
)
from app.modules.recipes.contracts import (
    CulinaryCandidateDraft,
    CulinaryDemand,
    CulinaryGenerationLimits,
    CulinaryGenerationRejection,
    CulinaryRuleSelection,
    GroundedRecipeVariantDraft,
    PreparationOutputEstimate,
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
    VariantGenerationRequest,
    VariantGenerationResult,
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
    ProcurementSupplyPath,
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
from app.modules.validation.contracts import (
    CalculatedNutrition,
    CulinaryValidationInput,
    DefaultBatchInputDerivation,
    InventoryValidationFacts,
    MaterialBalanceDerivation,
    RecipeGroundingReport,
    ValidationReport,
    ValidationSourceFrontier,
    ValidationSubjectSnapshot,
    YieldEstimate,
)
from pydantic.json_schema import models_json_schema

CONTRACTS = (
    RetentionMultiplier,
    RecipeDecayBand,
    RecipeDecayPolicy,
    RecipeDecayInput,
    RecipeDecayTraceEntry,
    RecipeDecayTraceDraft,
    RecipeCooldownPolicy,
    RecipeCooldownQuery,
    RecipeCooldownInput,
    RecipeCooldownWitness,
    RecipeCooldownAssessmentDraft,
    ExposureAllocationSupport,
    ExposurePreviewPolicy,
    ExposurePreviewRequest,
    ExposurePreviewSnapshot,
    ProposalExposureSource,
    RecipeExposureIdentity,
    RecipeExposurePreviewDraft,
    RecipeExposurePreviewFact,
    RecipeRepeatEvidenceDraft,
    AffinityFeatureTermFact,
    ExplicitMemberPreferenceSnapshot,
    FeaturePreferenceTarget,
    IngredientPreferenceTarget,
    MemberPreferenceDeclarationFact,
    MemberPreferenceState,
    PreferenceWriteCommand,
    RecipePreferenceTarget,
    RetractMemberPreferenceCommand,
    SetMemberPreferenceCommand,
    ParetoShortlistDraft,
    ShortlistDominanceWitness,
    ShortlistInputFailure,
    ShortlistPolicyDraft,
    CandidateGroundingRequest,
    CandidateGroundingResult,
    CandidateGroundingSources,
    GroundedDishCandidate,
    GroundedIngredientFacts,
    GroundingIssue,
    GroundingNutritionSelection,
    ResolvedNutrients,
    ResolvedNutritionPortion,
    PreparationOutputEstimate,
    ProcurementSupplyPath,
    InventoryCandidateLot,
    VariantGenerationRequest,
    VariantGenerationResult,
    CulinaryCandidateDraft,
    CulinaryDemand,
    CulinaryGenerationLimits,
    CulinaryRuleSelection,
    CulinaryGenerationRejection,
    PlannedCulinaryBinding,
    CulinaryRequirementBinding,
    BoundCookingBatchIntent,
    BoundPlanIntentGraph,
    ProposeBoundPlanCommand,
    BoundPlanProposalSnapshot,
    BoundPlanRevisionSnapshot,
    BoundActivePlanSnapshot,
    CulinaryValidationInput,
    RecipeGroundingReport,
    ValidationSubjectSnapshot,
    ValidationReport,
    InventoryValidationFacts,
    ValidationSourceFrontier,
    DefaultBatchInputDerivation,
    CalculatedNutrition,
    MaterialBalanceDerivation,
    YieldEstimate,
    ValidationCoveragePolicySnapshot,
    IngredientIdentityFact,
    NutritionReferenceFact,
    CanonicalMemberSafetySnapshot,
    MemberSafetySourceFact,
    HouseholdMemberIdentity,
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
    schema["$id"] = "urn:menuto:domain:foundation:18"
    schema["description"] = (
        "Bundle of named definitions; select a $defs reference to validate a document. "
        "Validation subject/report v1-foundation are partial self-contained inputs/diagnostics; "
        "production authority is absent and reports cannot authorize activation. "
        "Planner, validation and mutation handoffs are m0 drafts. "
        "Retail facts use retail-v2; reference calibration and price pairs remain DRAFT. "
        "Recipe authored snapshots use recipe-v1; culinary grounded inputs remain DRAFT. "
        "V1 substitutions are mass-only; preparation yield is net and path-specific. "
        "Plan intent v1/v2 unchanged; v3 sealed authoritative culinary intent; "
        "independent grounding companion; "
        "culinary generation v1 expands authored demand only, no downstream grounding/ranking; "
        "candidate grounding v1 resolves supported primitives, not feasibility/authority; "
        "Pareto shortlist v1-draft compares exact optional supply coverage only, "
        "not full portfolio/ranking or global feasibility; "
        "explicit preferences v1 record raw member assertions, no EvidenceStrength or utility; "
        "exposure preview v1 captures selected current proposals only, not consumption history; "
        "recipe cooldown v1-draft assesses one proposal using explicit policy, not global safety; "
        "decay trace v1-draft interprets eligible witnesses AS_OF_CAPTURE, no aggregate utility; "
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
