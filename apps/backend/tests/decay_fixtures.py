"""Explicit synthetic bands/multipliers; no production decay defaults."""

from app.modules.learning import contracts as c
from app.modules.learning.public import assess_recipe_cooldown
from cooldown_fixtures import cooldown_input


def band(ordinal, lower, upper, numerator, denominator):
    return dict(
        ordinal=ordinal,
        lower_age_microseconds=lower,
        upper_age_microseconds=upper,
        retention_multiplier=dict(numerator=numerator, denominator=denominator),
    )


def policy_for(assessment, bands=None):
    duration = assessment.subject.policy.duration_microseconds
    return c.RecipeDecayPolicy(
        policy_id="synthetic.decay",
        policy_version="test.v1",
        provenance=assessment.subject.policy.provenance,
        bands=bands
        if bands is not None
        else (band(0, 0, duration // 2, 1, 2), band(1, duration // 2, duration, 0, 1)),
    )


def decay_input(offsets=(-1, -2, -3, -4)):
    subject = cooldown_input(offsets)
    subject = subject.model_copy(
        update={"policy": subject.policy.model_copy(update={"duration_microseconds": 4})}
    )
    assessment = assess_recipe_cooldown(subject)
    return c.RecipeDecayInput(assessment=assessment, policy=policy_for(assessment))
