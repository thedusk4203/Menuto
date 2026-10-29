"""Explicit registration at the composition root; cross-context models use database FKs."""

from app.modules.catalog.models import AffinityFeatureTerm, Ingredient, NutritionFact
from app.modules.cooking.models import PlannedBatchAllocation, PlannedCookingBatch
from app.modules.households.models import Household, HouseholdMember, Membership
from app.modules.identity.models import User
from app.modules.inventory.models import (
    InventoryLot,
    InventoryLotBalance,
    InventoryMovement,
    InventoryReservation,
    InventoryReservationRelease,
)
from app.modules.nutrition.models import MemberNutritionProfile, MemberSafetyConstraint
from app.modules.planning.binding_models import CulinaryRequirementBinding, PlannedCulinaryBinding
from app.modules.planning.models import (
    PlanMaterializationLink,
    PlanMealIntent,
    PlanMealParticipant,
    PlanProposal,
    PlanProposalSeal,
    PlanReservationIntent,
    PlanRevision,
    PlanRevisionReservation,
    PlanValidationAuthorization,
    PlanWorkspace,
)
from app.modules.preferences.hierarchy_models import (  # noqa: F401
    HierarchyAuthority,
    HierarchyMutation,
    HierarchyPrincipal,
    HierarchyProvider,
    HierarchyProviderFrontier,
    HierarchyRevision,
    HierarchyStream,
)
from app.modules.preferences.models import (
    MemberPreferenceDeclaration,
    MemberPreferenceFrontier,
    MemberPreferenceStream,
)
from app.modules.preferences.reference_prior_models import (  # noqa: F401
    ReferencePriorAuthority,
    ReferencePriorMutation,
    ReferencePriorPrincipal,
    ReferencePriorProvider,
    ReferencePriorProviderFrontier,
    ReferencePriorRevision,
    ReferencePriorStream,
)
from app.modules.recipes.models import (
    PreparationTransformation,
    Recipe,
    RecipeCombinationMember,
    RecipeIngredient,
    RecipePortionTier,
    RecipeRuleCombination,
    RecipeTierQuantity,
    RecipeVariantRule,
    RecipeVersion,
    RecipeVersionSeal,
)
from app.modules.retail.models import (
    IngredientProductMap,
    LegacyOptionAssessment,
    PlanningPriceQuote,
    PlanningProcurementOption,
    PriceObservation,
    ProcurementClass,
    ProcurementClassMember,
    ReferencePriceBook,
    ReferencePriceEntry,
    Retailer,
    RetailerStatusFact,
    RetailPackage,
    RetailPriceCalibration,
    RetailProduct,
    StoreRegion,
)
from app.modules.shopping.models import ShoppingDemandContribution, ShoppingRequirementIntent
from app.shared.db import Base

__all__ = [
    "AffinityFeatureTerm",
    "MemberPreferenceDeclaration",
    "MemberPreferenceFrontier",
    "MemberPreferenceStream",
    "CulinaryRequirementBinding",
    "PlannedCulinaryBinding",
    "PlanWorkspace",
    "PlanProposal",
    "PlanProposalSeal",
    "PlanMealIntent",
    "PlanMealParticipant",
    "PlanReservationIntent",
    "PlanValidationAuthorization",
    "PlanRevision",
    "PlanRevisionReservation",
    "PlanMaterializationLink",
    "PlannedCookingBatch",
    "PlannedBatchAllocation",
    "ShoppingRequirementIntent",
    "ShoppingDemandContribution",
    "InventoryLot",
    "InventoryLotBalance",
    "InventoryMovement",
    "InventoryReservation",
    "InventoryReservationRelease",
    "PreparationTransformation",
    "Recipe",
    "RecipeCombinationMember",
    "RecipeIngredient",
    "RecipePortionTier",
    "RecipeRuleCombination",
    "RecipeTierQuantity",
    "RecipeVariantRule",
    "RecipeVersion",
    "RecipeVersionSeal",
    "Base",
    "Household",
    "HouseholdMember",
    "Ingredient",
    "MemberNutritionProfile",
    "MemberSafetyConstraint",
    "Membership",
    "NutritionFact",
    "User",
    "IngredientProductMap",
    "LegacyOptionAssessment",
    "PlanningPriceQuote",
    "PlanningProcurementOption",
    "PriceObservation",
    "ProcurementClass",
    "ProcurementClassMember",
    "ReferencePriceBook",
    "ReferencePriceEntry",
    "Retailer",
    "RetailerStatusFact",
    "RetailPackage",
    "RetailPriceCalibration",
    "RetailProduct",
    "StoreRegion",
]

# Source-owned companion facts, independently versioned from frozen Recipe aggregates.
from app.modules.catalog.feature_models import (  # noqa: E402,F401
    IngredientProteinAssignment,
    IngredientProteinFrontier,
    IngredientProteinReview,
    IngredientProteinReviewTerm,
    IngredientProteinStream,
)
from app.modules.recipes.feature_models import (  # noqa: E402,F401
    CulinaryFeatureApplicability,
    CulinaryFeatureApplicabilitySlot,
    CulinaryFeatureApplicabilityTier,
    CulinaryFeatureAssignment,
    CulinaryFeatureFrontier,
    CulinaryFeatureMainProteinSupport,
    CulinaryFeatureReview,
    CulinaryFeatureReviewTerm,
)

# isort: split
# Independently versioned Nutrition source metadata; no legacy model changes.
from app.modules.nutrition.root_models import NUTRITION_ROOT_TABLES  # noqa: E402,F401
