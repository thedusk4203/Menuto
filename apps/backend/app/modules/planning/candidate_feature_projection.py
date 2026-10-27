"""Replay exact candidate classification facts; no live reads or downstream authority."""

from uuid import UUID

from pydantic import BaseModel, TypeAdapter, ValidationError

from app.domain.contracts import AwareTime
from app.domain.feature_identity import canonical, canonical_bytes, identity_hash
from app.domain.resolution import ResolutionError
from app.modules.planning.contracts import (
    CandidateFeatureBinding,
    CandidateFeatureProjectionDraft,
    CandidateFeatureProjectionRequest,
    CandidateFeatureProjectionSourceSnapshot,
    GroundedDishCandidate,
    grounding_canonical_json,
)
from app.modules.planning.grounding import resolve_captured_candidate
from app.modules.recipes.contracts import (
    CulinaryFeatureEvaluationInput,
    FeatureSelectedPath,
    RecipeVersionSnapshot,
    discover_feature_input,
)

_DIMENSIONS = frozenset({"METHOD", "MAIN_PROTEIN", "FLAVOR"})
_TIME = TypeAdapter(AwareTime)


def _wire(value):
    return (
        value.model_dump(mode="python", warnings=False) if isinstance(value, BaseModel) else value
    )


def _fail(code, detail, *, rejected=True):
    raise ResolutionError(code, detail, rejected=rejected)


def _parse_request(request):
    raw = _wire(request)
    if isinstance(raw, dict):
        dimensions = raw.get("requested_dimensions")
        if isinstance(dimensions, (tuple, list)) and any(
            not isinstance(d, str) or d not in _DIMENSIONS for d in dimensions
        ):
            _fail("UNSUPPORTED_DIMENSION", "Only METHOD, MAIN_PROTEIN and FLAVOR are supported")
    try:
        return CandidateFeatureProjectionRequest.model_validate(raw)
    except (ValidationError, TypeError, ValueError) as exc:
        raise ResolutionError(
            "INVALID_REQUEST", "Invalid candidate feature request", rejected=True
        ) from exc


def _request_payload(request):
    return dict(
        contract_version=request.contract_version,
        grounding_request_json=grounding_canonical_json(
            request.grounding_request.model_dump(mode="json")
        ),
        expected_grounding_fingerprint=request.expected_grounding_fingerprint,
        requested_dimensions=sorted(request.requested_dimensions),
    )


def _source_payload(subject):
    return dict(
        contract_version=subject.contract_version,
        request=_request_payload(subject.request),
        grounded_candidate_json=subject.grounded_candidate.canonical_json(),
        grounding_issues_json=grounding_canonical_json(
            {"issues": [i.model_dump(mode="json") for i in subject.grounding_issues]}
        ),
        feature_input=canonical(subject.feature_input),
        capture_semantics=subject.capture_semantics,
        capture_started_at=subject.capture_started_at,
        capture_completed_at=subject.capture_completed_at,
    )


def _result_payload(result):
    return dict(
        contract_version=result.contract_version,
        source=_source_payload(result.source),
        source_fingerprint=result.source.fingerprint,
        binding=result.binding,
        dimensions=tuple(sorted(result.dimensions, key=lambda d: d.dimension)),
        status=result.status,
        planner_ready=result.planner_ready,
        activation_ready=result.activation_ready,
    )


def _require_grounded(result):
    if result.status != "GROUNDED":
        raise ResolutionError(
            "GROUNDING_REJECTED" if result.status == "REJECTED" else "GROUNDING_INCOMPLETE",
            "; ".join(i.code for i in result.issues),
            rejected=result.status == "REJECTED",
        )
    return result.candidate


def _binding(candidate):
    culinary = candidate.request.candidate
    return CandidateFeatureBinding(
        grounding_fingerprint=candidate.fingerprint,
        culinary_candidate_fingerprint=culinary.fingerprint,
        recipe_id=candidate.sources.recipe.recipe.id,
        recipe_version_id=culinary.recipe_version_id,
        recipe_source_hash=culinary.recipe_source_hash,
        path=FeatureSelectedPath(
            tier_id=culinary.tier_id,
            selected_rule_ids=culinary.selected_rule_ids,
            deltas=tuple(
                (r.requirement_id, r.adjustment_delta) for r in culinary.resolved_ingredients
            ),
        ),
    )


def _immutable_records(*roots):
    """Only the same typed owner record is comparable; sharing a UUID is insufficient."""
    seen = {}

    def visit(value):
        if isinstance(value, BaseModel):
            record_id = getattr(value, "id", None)
            if isinstance(record_id, UUID):
                key = (type(value), record_id)
                payload = canonical_bytes(value)
                if key in seen and seen[key] != payload:
                    _fail("SOURCE_CUT_INCOHERENT", "Conflicting repeated immutable source record")
                seen[key] = payload
            for field in type(value).model_fields:
                visit(getattr(value, field))
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                visit(item)

    for root in roots:
        visit(root)


def _check_frontiers(raw, captured_at):
    """Cross-cut time/frontier checks precede the unchanged owner source validator."""
    sources = _wire(raw.get("sources"))
    if not isinstance(sources, dict):
        return  # Frozen validation reports malformed source shape.
    for collection, frontier_name in (
        ("scopes", "recipe_frontier"),
        ("catalog_streams", "catalog_frontier"),
    ):
        frontier = sources.get(frontier_name)
        for item in sources.get(collection, ()):
            for review in _wire(item).get("reviews", ()):
                review = _wire(review)
                sequence = review.get("source_sequence")
                if type(sequence) is int and type(frontier) is int and sequence > frontier:
                    _fail("SOURCE_CUT_INCOHERENT", "Review exceeds retained owner frontier")
                try:
                    recorded = _TIME.validate_python(review.get("recorded_at"))
                except (ValueError, TypeError):
                    continue  # Frozen validation reports malformed review time.
                if recorded > captured_at:
                    _fail("SOURCE_CUT_INCOHERENT", "Review exceeds feature capture time")
                command = _wire(review.get("command"))
                if isinstance(command, dict):
                    audit = command.get("expected_catalog_frontier")
                    catalog = sources.get("catalog_frontier")
                    if type(audit) is int and type(catalog) is int and audit > catalog:
                        _fail("SOURCE_CUT_INCOHERENT", "Publication audit exceeds Catalog cut")


def _feature_input(candidate, request, raw, started, completed):
    raw = _wire(raw)
    try:
        if not isinstance(raw, dict):
            raise ValueError("Feature input is not a mapping")
        captured = _TIME.validate_python(raw.get("captured_at"))
        if not started <= captured <= completed:
            _fail("CAPTURE_CONTEXT_INVALID", "Feature clock is outside the capture interval")
        recipe = RecipeVersionSnapshot.model_validate(_wire(raw.get("recipe")))
        if recipe.id != candidate.sources.recipe.id:
            _fail("RECIPE_VERSION_MISMATCH", "Feature RecipeVersion differs from grounding")
        if canonical_bytes(recipe) != canonical_bytes(candidate.sources.recipe):
            _fail("SOURCE_CUT_INCOHERENT", "Immutable RecipeVersion payload differs across cuts")
        dimensions = raw.get("requested_dimensions", ())
        if sorted(dimensions) != list(request.requested_dimensions):
            _fail("SOURCE_CUT_INCOHERENT", "Feature dimensions differ from the request")
        expected_path = None if set(dimensions) == {"METHOD"} else _binding(candidate).path
        path = raw.get("path")
        try:
            path = None if path is None else FeatureSelectedPath.model_validate(_wire(path))
        except (ValueError, TypeError) as exc:
            raise ResolutionError("PATH_MISMATCH", "Invalid retained path", rejected=True) from exc
        if path != expected_path:
            _fail("PATH_MISMATCH", "Feature path differs from the exact grounded candidate")
        _check_frontiers(raw, captured)
        feature = CulinaryFeatureEvaluationInput.model_validate(raw)
        _immutable_records(candidate, feature)
        return feature
    except ResolutionError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ResolutionError(
            "FEATURE_SOURCE_INVALID", "Frozen feature source validation failed", rejected=True
        ) from exc


def _replay_source(subject):
    raw = _wire(subject)
    if not isinstance(raw, dict):
        _fail("REPLAY_MISMATCH", "Complete retained source envelope required")
    request = _parse_request(raw.get("request"))
    try:
        candidate = GroundedDishCandidate.model_validate(_wire(raw.get("grounded_candidate")))
    except (ValueError, TypeError) as exc:
        raise ResolutionError("REPLAY_MISMATCH", "Invalid grounding child", rejected=True) from exc
    if grounding_canonical_json(request.grounding_request.model_dump(mode="json")) != (
        grounding_canonical_json(candidate.request.model_dump(mode="json"))
    ):
        _fail("REPLAY_MISMATCH", "Outer grounding request differs from the retained candidate")
    try:
        grounding = resolve_captured_candidate(candidate.request, candidate.sources)
    except (ValueError, TypeError) as exc:
        raise ResolutionError(
            "REPLAY_MISMATCH", "Invalid grounding primitives", rejected=True
        ) from exc
    fresh = _require_grounded(grounding)
    if fresh.canonical_json() != candidate.canonical_json():
        _fail("REPLAY_MISMATCH", "Cached grounding differs from primitive replay")
    if fresh.fingerprint != request.expected_grounding_fingerprint:
        _fail("EXPECTED_GROUNDING_MISMATCH", "Grounding identity differs from the pinned candidate")
    try:
        started = _TIME.validate_python(raw.get("capture_started_at"))
        completed = _TIME.validate_python(raw.get("capture_completed_at"))
    except (ValueError, TypeError) as exc:
        raise ResolutionError(
            "CAPTURE_CONTEXT_INVALID", "Invalid capture interval", rejected=True
        ) from exc
    feature = _feature_input(fresh, request, raw.get("feature_input"), started, completed)
    try:
        parsed = CandidateFeatureProjectionSourceSnapshot.model_validate(
            raw | dict(request=request, grounded_candidate=fresh, feature_input=feature)
        )
    except (ValueError, TypeError) as exc:
        raise ResolutionError(
            "REPLAY_MISMATCH", "Invalid retained source envelope", rejected=True
        ) from exc
    if grounding_canonical_json(
        {"issues": [i.model_dump(mode="json") for i in parsed.grounding_issues]}
    ) != grounding_canonical_json(
        {"issues": [i.model_dump(mode="json") for i in grounding.issues]}
    ):
        _fail("REPLAY_MISMATCH", "Grounding diagnostics differ from primitive replay")
    if parsed.fingerprint != identity_hash(_source_payload(parsed)):
        _fail("REPLAY_MISMATCH", "Full-source fingerprint differs")
    return parsed


def project_candidate_features(
    subject: CandidateFeatureProjectionSourceSnapshot,
) -> CandidateFeatureProjectionDraft:
    """Recompute frozen grounding and classification from a retained cut, with zero I/O."""
    source = _replay_source(subject)
    dimensions = discover_feature_input(source.feature_input)
    fields = dict(source=source, binding=_binding(source.grounded_candidate), dimensions=dimensions)
    temporary = CandidateFeatureProjectionDraft.model_construct(**fields)
    return CandidateFeatureProjectionDraft(
        **fields, fingerprint=identity_hash(_result_payload(temporary))
    )


def validate_candidate_feature_projection(
    result: CandidateFeatureProjectionDraft,
) -> CandidateFeatureProjectionDraft:
    """Return a freshly derived result, never a serialized validation/origin attestation."""
    raw = _wire(result)
    if not isinstance(raw, dict):
        _fail("REPLAY_MISMATCH", "Complete projection result required")
    fresh = project_candidate_features(raw.get("source"))
    try:
        parsed = CandidateFeatureProjectionDraft.model_validate(raw)
    except (ValueError, TypeError) as exc:
        raise ResolutionError("REPLAY_MISMATCH", "Invalid projection shape", rejected=True) from exc
    if parsed.binding.path != fresh.binding.path:
        _fail("PATH_MISMATCH", "Cached result path differs from primitive replay")
    if canonical_bytes(_result_payload(parsed)) != canonical_bytes(_result_payload(fresh)) or (
        parsed.fingerprint != fresh.fingerprint
    ):
        _fail("REPLAY_MISMATCH", "Projection differs from full semantic replay")
    return fresh
