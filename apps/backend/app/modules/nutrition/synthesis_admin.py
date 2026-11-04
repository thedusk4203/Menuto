"""Dedicated privileged registrar. Ordinary source commands cannot dispatch here."""

from app.domain.feature_identity import canonical
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.synthesis_sources import _call


def register_nutrition_synthesis_provider(session, command):
    value = c.NutritionSynthesisProviderEnrollment.model_validate(canonical(command))
    return c.NutritionSynthesisProviderFact.model_validate(
        _call(session, "register_provider", value)
    )


def enroll_nutrition_synthesis_principal(session, command):
    value = c.NutritionSynthesisPrincipalEnrollment.model_validate(canonical(command))
    return c.NutritionSynthesisPrincipalFact.model_validate(
        _call(session, "enroll_principal", value)
    )


def change_nutrition_synthesis_authority(session, command):
    value = c.NutritionSynthesisGrant.model_validate(canonical(command))
    return c.NutritionSynthesisGrantFact.model_validate(_call(session, "change_authority", value))
