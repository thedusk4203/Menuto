"""Explicit registration at the composition root; cross-context models use database FKs."""

from app.modules.catalog.models import Ingredient, NutritionFact
from app.modules.households.models import Household, HouseholdMember, Membership
from app.modules.identity.models import User
from app.modules.nutrition.models import MemberNutritionProfile, MemberSafetyConstraint
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
from app.shared.db import Base

__all__ = [
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
