"""Pure proposal preview; no attribution, IO, history writes or utility scoring."""

from app.modules.learning.contracts import (
    ExposurePreviewSnapshot,
    RecipeCooldownAssessmentDraft,
    RecipeCooldownInput,
    RecipeDecayInput,
    RecipeDecayTraceDraft,
    RecipeExposurePreviewDraft,
    RecipeExposurePreviewFact,
    _cooldown_values,
    _decay_entries,
    derive_preview_facts,
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
