"""Separate privileged enrollment interface; never dispatched by ordinary source commands."""

from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as c
from app.modules.nutrition.root_limits import COMMAND_BYTES, check_structure
from app.modules.nutrition.root_sources import _call


def register_nutrition_provider(session, command):
    check_structure(command, byte_limit=COMMAND_BYTES)
    command = c.NutritionProviderEnrollment.model_validate(canonical(command))
    return _call(session, "register_provider", command, c.NutritionProviderFact)


def enroll_nutrition_principal(session, command):
    check_structure(command, byte_limit=COMMAND_BYTES)
    command = c.NutritionPrincipalEnrollment.model_validate(canonical(command))
    return _call(session, "enroll_principal", command, c.NutritionPrincipalFact)


def change_nutrition_authority(session, command):
    check_structure(command, byte_limit=COMMAND_BYTES)
    command = c.NutritionAuthorityCommand.model_validate(canonical(command))
    return _call(session, "change_authority", command, c.NutritionAuthorityFact)
