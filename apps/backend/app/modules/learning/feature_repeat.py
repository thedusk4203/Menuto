"""Pure exact-term public interpretation. Full recursive verification lives in contracts."""

from app.modules.learning import contracts as c


def assess_feature_cooldown(subject):
    subject = c.FeatureCooldownInput.model_validate(c._feature_repeat_wire(subject))
    return c.FeatureCooldownAssessmentDraft(subject=subject, **c.feature_cooldown_values(subject))


def trace_feature_decay(subject):
    subject = c.FeatureDecayInput.model_validate(c._feature_repeat_wire(subject))
    return c.FeatureDecayTraceDraft(subject=subject, **c.feature_decay_values(subject))


def interpret_feature_repeat_penalty(subject):
    subject = c.FeatureRepeatPenaltyInput.model_validate(c._feature_repeat_wire(subject))
    return c.FeatureRepeatPenaltyDraft(subject=subject, **c.feature_penalty_values(subject))
