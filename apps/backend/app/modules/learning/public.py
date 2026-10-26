"""Pure proposal preview; no attribution, IO, history writes or utility scoring."""

from app.modules.learning.contracts import (
    ExposurePreviewSnapshot,
    FeatureExposurePreviewDraft,
    FeatureExposureSourceSnapshotDraft,
    RecipeCooldownAssessmentDraft,
    RecipeCooldownInput,
    RecipeDecayInput,
    RecipeDecayTraceDraft,
    RecipeExposurePreviewDraft,
    RecipeExposurePreviewFact,
    RecipeRepeatPenaltyDraft,
    RecipeRepeatPenaltyInput,
    _cooldown_values,
    _decay_entries,
    _feature_exposure_values,
    _repeat_penalty_values,
    derive_preview_facts,
)
from app.modules.learning.feature_repeat import (
    assess_feature_cooldown as assess_feature_cooldown,
)
from app.modules.learning.feature_repeat import (
    interpret_feature_repeat_penalty as interpret_feature_repeat_penalty,
)
from app.modules.learning.feature_repeat import (
    trace_feature_decay as trace_feature_decay,
)


def preview_recent_exposure(snapshot):
    snapshot = ExposurePreviewSnapshot.model_validate(snapshot.model_dump())
    return RecipeExposurePreviewDraft(snapshot=snapshot, facts=derive_preview_facts(snapshot))


def deduplicate_preview_facts(facts):
    """Set union for overlapping captures; conflicting revisions require explicit recapture."""
    unique = {}
    versions = {}
    for value in facts:
        fact = RecipeExposurePreviewFact.model_validate(value.model_dump())
        owner = (fact.household_id, fact.member_id, fact.plan_id)
        version = (fact.proposal_id, fact.proposal_hash)
        if owner in versions and versions[owner] != version:
            raise ValueError("Conflicting preview revisions; recapture current sources")
        versions[owner] = version
        key = fact.event_key()
        if key in unique and unique[key] != fact:
            raise ValueError("Conflicting preview revisions; recapture current sources")
        unique[key] = fact
    return tuple(unique[k] for k in sorted(unique))


def assess_recipe_cooldown(subject):
    """Assess only captured proposed repetition; invalid/unsupported inputs fail closed."""
    subject = RecipeCooldownInput.model_validate(subject.model_dump())
    return RecipeCooldownAssessmentDraft(subject=subject, **_cooldown_values(subject))


def trace_recipe_decay(subject):
    """AS_OF_CAPTURE interpretation only; no retrospective mode or aggregate utility."""
    subject = RecipeDecayInput.model_validate(subject.model_dump())
    return RecipeDecayTraceDraft(subject=subject, entries=_decay_entries(subject))


def interpret_recipe_repeat_penalty(subject):
    """Interpret captured proposal repetitions only; no global history or utility claim."""
    subject = RecipeRepeatPenaltyInput.model_validate(subject.model_dump())
    return RecipeRepeatPenaltyDraft(subject=subject, **_repeat_penalty_values(subject))


def preview_feature_exposure(snapshot):
    """Pure reviewed source join only; no feature policy interpretation or history authority."""
    snapshot = FeatureExposureSourceSnapshotDraft.model_validate(snapshot.model_dump())
    return FeatureExposurePreviewDraft(snapshot=snapshot, **_feature_exposure_values(snapshot))
