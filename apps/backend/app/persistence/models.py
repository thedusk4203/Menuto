"""Explicit registration at the composition root; cross-context models use database FKs."""

from app.modules.catalog.models import Ingredient, NutritionFact, UnitConversion
from app.modules.households.models import Household, HouseholdMember, Membership
from app.modules.identity.models import User
from app.modules.nutrition.models import MemberNutritionProfile, MemberSafetyConstraint
from app.shared.db import Base

__all__ = [
    "Base",
    "Household",
    "HouseholdMember",
    "Ingredient",
    "MemberNutritionProfile",
    "MemberSafetyConstraint",
    "Membership",
    "NutritionFact",
    "UnitConversion",
    "User",
]
