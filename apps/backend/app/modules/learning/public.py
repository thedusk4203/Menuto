"""Pure proposal preview; no attribution, IO, history writes or utility scoring."""

from app.modules.learning.contracts import (
    ExposurePreviewSnapshot,
    RecipeExposurePreviewDraft,
    RecipeExposurePreviewFact,
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
