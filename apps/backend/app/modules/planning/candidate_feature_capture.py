"""Canonical read-only ingress for one exact candidate's reviewed feature sources."""

from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, NoResultFound

from app.domain.feature_identity import identity_hash
from app.domain.resolution import ResolutionError
from app.modules.catalog.public import (
    affinity_feature_terms,
    ingredient_protein_frontier,
    ingredient_protein_sources,
)
from app.modules.households.public import read_household_actor
from app.modules.planning.candidate_feature_projection import (
    _binding,
    _feature_input,
    _parse_request,
    _require_grounded,
    _source_payload,
    project_candidate_features,
)
from app.modules.planning.contracts import (
    CandidateFeatureProjectionRequest,
    CandidateFeatureProjectionSourceSnapshot,
)
from app.modules.planning.grounding import resolve_captured_candidate
from app.modules.planning.grounding_capture import capture_candidate_sources
from app.modules.recipes.contracts import MainProteinFeatureSources, RecipeFeatureSources
from app.modules.recipes.public import culinary_feature_frontier, culinary_feature_sources


def _clock(session):
    return session.scalar(text("SELECT clock_timestamp()"))


def _read_features(session, candidate, dimensions):
    scopes = culinary_feature_sources(session, candidate.sources.recipe.id, dimensions)
    streams = ()
    extras = {}
    source_type = RecipeFeatureSources
    if "MAIN_PROTEIN" in dimensions:
        ingredients = {
            support.ingredient_id
            for scope in scopes
            for review in scope.reviews
            for support in review.command.supports
        }
        streams = ingredient_protein_sources(session, ingredients)
        source_type = MainProteinFeatureSources
        extras = dict(
            catalog_frontier=ingredient_protein_frontier(session), catalog_streams=streams
        )
    terms = {
        tid
        for scope in scopes
        for review in scope.reviews
        for tid in review.command.covered_term_ids
    } | {
        tid
        for stream in streams
        for review in stream.reviews
        for tid in review.command.covered_term_ids
    }
    return source_type(
        recipe_frontier=culinary_feature_frontier(session),
        scopes=scopes,
        terms=affinity_feature_terms(session, terms),
        **extras,
    )


def capture_candidate_feature_projection_sources(
    session,
    request: CandidateFeatureProjectionRequest,
    *,
    actor_user_id: UUID,
) -> CandidateFeatureProjectionSourceSnapshot:
    """Reconstruct from owner truth; never accept a serialized child as source authority."""
    request = _parse_request(request)
    try:
        if (
            session.new
            or session.dirty
            or session.deleted
            or session.connection().get_isolation_level() not in {"REPEATABLE READ", "SERIALIZABLE"}
            or session.scalar(text("SHOW transaction_read_only")) != "on"
        ):
            raise ResolutionError(
                "CAPTURE_CONTEXT_INVALID",
                "Capture requires clean read-only RR/SERIALIZABLE",
                rejected=True,
            )
        read_household_actor(session, request.grounding_request.household_id, actor_user_id)
        started = _clock(session)
        try:
            sources = capture_candidate_sources(session, request.grounding_request)
        except (LookupError, NoResultFound, ValidationError) as exc:
            raise ResolutionError(
                "CANONICAL_SOURCE_UNAVAILABLE", "Required canonical grounding source is unavailable"
            ) from exc
        except ValueError as exc:
            # Preserve Inventory's existing nonfuture-cutoff requirement at this ingress.
            raise ResolutionError("INVALID_REQUEST", str(exc), rejected=True) from exc
        grounding = resolve_captured_candidate(request.grounding_request, sources)
        candidate = _require_grounded(grounding)
        if candidate.fingerprint != request.expected_grounding_fingerprint:
            raise ResolutionError(
                "EXPECTED_GROUNDING_MISMATCH",
                "Fresh grounding differs from the pinned candidate",
                rejected=True,
            )
        try:
            feature_sources = _read_features(session, candidate, request.requested_dimensions)
        except (ValidationError, ValueError) as exc:
            raise ResolutionError(
                "FEATURE_SOURCE_INVALID", "Frozen owner source validation failed", rejected=True
            ) from exc
        captured = _clock(session)
        evaluation = _feature_input(
            candidate,
            request,
            dict(
                recipe=candidate.sources.recipe,
                requested_dimensions=request.requested_dimensions,
                path=None
                if set(request.requested_dimensions) == {"METHOD"}
                else _binding(candidate).path,
                sources=feature_sources,
                captured_at=captured,
            ),
            started,
            captured,
        )
        fields = dict(
            request=request,
            grounded_candidate=candidate,
            grounding_issues=grounding.issues,
            feature_input=evaluation,
            capture_started_at=started,
            capture_completed_at=_clock(session),
        )
        temporary = CandidateFeatureProjectionSourceSnapshot.model_construct(**fields)
        subject = CandidateFeatureProjectionSourceSnapshot(
            **fields, fingerprint=identity_hash(_source_payload(temporary))
        )
        # The same semantic replay is required at canonical ingress and offline consumption.
        return project_candidate_features(subject).source
    except ResolutionError:
        raise
    except PermissionError as exc:
        raise ResolutionError(
            "CAPTURE_ACCESS_DENIED", "Household read access denied", rejected=True
        ) from exc
    except (LookupError, NoResultFound) as exc:
        raise ResolutionError(
            "CANONICAL_SOURCE_UNAVAILABLE", "Required canonical owner source is unavailable"
        ) from exc
    except (DBAPIError, OSError, TimeoutError, MemoryError) as exc:
        raise ResolutionError("CAPTURE_IO_FAILURE", "Canonical source capture failed") from exc
