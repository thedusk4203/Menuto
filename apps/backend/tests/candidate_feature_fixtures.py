"""Synthetic retained cuts; independent normative envelope hashing for tamper tests."""

from datetime import timedelta
from uuid import uuid4

from app.domain.feature_identity import canonical, identity_hash
from app.modules.catalog import contracts as cat
from app.modules.planning import contracts as p
from app.modules.planning.grounding import resolve_captured_candidate
from app.modules.recipes import contracts as r
from feature_fixtures import review_command
from grounding_fixtures import setup
from preference_fixtures import provenance, term


def source_payload(source):
    q = source.request
    return dict(
        contract_version=source.contract_version,
        request=dict(
            contract_version=q.contract_version,
            grounding_request_json=p.grounding_canonical_json(
                q.grounding_request.model_dump(mode="json")
            ),
            expected_grounding_fingerprint=q.expected_grounding_fingerprint,
            requested_dimensions=sorted(q.requested_dimensions),
        ),
        grounded_candidate_json=source.grounded_candidate.canonical_json(),
        grounding_issues_json=p.grounding_canonical_json(
            {"issues": [i.model_dump(mode="json") for i in source.grounding_issues]}
        ),
        feature_input=canonical(source.feature_input),
        capture_semantics=source.capture_semantics,
        capture_started_at=source.capture_started_at,
        capture_completed_at=source.capture_completed_at,
    )


def seal_source(source):
    return source.model_copy(update=dict(fingerprint=identity_hash(source_payload(source))))


def seal_result(result):
    payload = dict(
        contract_version=result.contract_version,
        source=source_payload(result.source),
        source_fingerprint=result.source.fingerprint,
        binding=result.binding,
        dimensions=tuple(sorted(result.dimensions, key=lambda d: d.dimension)),
        status=result.status,
        planner_ready=result.planner_ready,
        activation_ready=result.activation_ready,
    )
    return result.model_copy(update=dict(fingerprint=identity_hash(payload)))


def seal_ground(candidate):
    return candidate.model_copy(update=dict(fingerprint=candidate.expected_fingerprint()))


def make_subject(
    dimensions=("METHOD", "MAIN_PROTEIN", "FLAVOR"),
    *,
    empty=False,
    coverage="COMPLETE",
    positives=True,
    grounding=None,
    availability="LIKELY",
):
    if grounding is None:
        q, sources, _ = setup(availability=availability)
    else:
        q, sources = grounding
    result = resolve_captured_candidate(q, sources)
    assert result.status == "GROUNDED", result
    candidate = result.candidate
    request = p.CandidateFeatureProjectionRequest(
        grounding_request=q,
        expected_grounding_fingerprint=candidate.fingerprint,
        requested_dimensions=dimensions,
    )
    recipe = sources.recipe
    scopes, terms, streams = [], [], ()
    for index, dimension in enumerate(() if empty else request.requested_dimensions):
        vocabulary = tuple(
            term("PROTEIN" if dimension == "MAIN_PROTEIN" else dimension) for _ in range(2)
        )
        terms.extend(vocabulary)
        extra = {}
        if dimension == "MAIN_PROTEIN":
            ingredient = recipe.ingredients[0].ingredient_id
            cq = cat.IngredientProteinReviewCommand(
                command_kind="REPLACE",
                ingredient_id=ingredient,
                expected_revision_no=-1,
                predecessor_id=None,
                expected_catalog_frontier=0,
                coverage="COMPLETE",
                covered_term_ids=tuple(t.id for t in vocabulary),
                positive_term_ids=(vocabulary[0].id,),
                provenance=provenance().model_dump(),
                correction_reason=None,
                idempotency_key=uuid4().hex,
            )
            actor, stream_id = uuid4(), uuid4()
            cr = cat.IngredientProteinReviewFact(
                id=uuid4(),
                stream_id=stream_id,
                ingredient_id=ingredient,
                revision_no=0,
                predecessor_revision_no=None,
                source_sequence=1,
                reviewer_user_id=actor,
                recorded_at=q.as_of + timedelta(microseconds=1),
                command=cq,
                command_hash=cq.fingerprint(actor),
            )
            streams = (
                cat.IngredientProteinStreamFact(
                    id=stream_id,
                    ingredient_id=ingredient,
                    reviews=(cr,),
                ),
            )
            extra = dict(
                expected_catalog_frontier=1,
                supports=(
                    dict(
                        term_id=vocabulary[0].id,
                        requirement_id=recipe.ingredients[0].id,
                        ingredient_id=ingredient,
                        catalog_review_id=cr.id,
                    ),
                )
                if positives
                else (),
            )
        command = review_command(
            recipe,
            vocabulary,
            dimension=dimension,
            expected_recipe_frontier=index,
            coverage=coverage,
            positive_term_ids=(vocabulary[0].id,) if positives else (),
            **extra,
        )
        actor, aid = uuid4(), uuid4()
        review = r.CulinaryFeatureReviewFact(
            id=uuid4(),
            applicability_id=aid,
            recipe_version_id=recipe.id,
            dimension=dimension,
            revision_no=0,
            predecessor_revision_no=None,
            source_sequence=index + 1,
            reviewer_user_id=actor,
            recorded_at=q.as_of + timedelta(seconds=1),
            command=command,
            command_hash=command.fingerprint(actor),
        )
        scopes.append(r.CulinaryFeatureScopeFact(id=aid, key=command.key, reviews=(review,)))
    source_type, extra = r.RecipeFeatureSources, {}
    if "MAIN_PROTEIN" in dimensions:
        source_type = r.MainProteinFeatureSources
        extra = dict(catalog_frontier=1 if streams else 0, catalog_streams=streams)
    feature = r.CulinaryFeatureEvaluationInput(
        recipe=recipe,
        requested_dimensions=dimensions,
        path=None
        if set(dimensions) == {"METHOD"}
        else r.FeatureSelectedPath(
            tier_id=q.candidate.tier_id,
            selected_rule_ids=q.candidate.selected_rule_ids,
            deltas=tuple(
                (row.requirement_id, row.adjustment_delta)
                for row in q.candidate.resolved_ingredients
            ),
        ),
        sources=source_type(
            recipe_frontier=len(scopes), scopes=tuple(scopes), terms=tuple(terms), **extra
        ),
        captured_at=q.as_of + timedelta(hours=1),
    )
    source = p.CandidateFeatureProjectionSourceSnapshot(
        request=request,
        grounded_candidate=candidate,
        grounding_issues=result.issues,
        feature_input=feature,
        capture_started_at=feature.captured_at - timedelta(minutes=1),
        capture_completed_at=feature.captured_at + timedelta(seconds=1),
        fingerprint="0" * 64,
    )
    return seal_source(source)


def change_feature(source, **changes):
    return source.model_copy(
        update=dict(feature_input=source.feature_input.model_copy(update=changes))
    )


def alternate_grounding(source):
    """Select another actually authored tier, not a fabricated resolved row."""
    from app.modules.recipes.public import generate_variants

    q = source.request.grounding_request
    recipe = source.grounded_candidate.sources.recipe
    alternative = generate_variants(
        r.VariantGenerationRequest(
            recipe=recipe,
            demand=dict(serving_counts=(recipe.portion_tiers[1].servings,)),
            limits=dict(max_attempts=20, max_candidates=20),
        )
    ).candidates[-1]
    assert alternative.tier_id != q.candidate.tier_id
    q = q.model_copy(update=dict(candidate=alternative))
    return q, source.grounded_candidate.sources


def replace_review(source, *, retract=False):
    scope = source.feature_input.sources.scopes[0]
    old = scope.reviews[-1]
    changes = dict(
        contract_version="culinary-feature-retract.v1" if retract else "culinary-feature-write.v1",
        command_kind="RETRACT" if retract else "REPLACE",
        key=None,
        applicability_id=scope.id,
        expected_revision_no=old.revision_no,
        predecessor_id=old.id,
        expected_recipe_frontier=source.feature_input.sources.recipe_frontier,
        correction_reason="Synthetic correction",
        idempotency_key=uuid4().hex,
        provenance=provenance().model_dump(),
    )
    if retract:
        changes.update(coverage=None, covered_term_ids=(), positive_term_ids=(), supports=())
    command = type(old.command).model_validate(old.command.model_dump() | changes)
    review = r.CulinaryFeatureReviewFact(
        **(
            old.model_dump()
            | dict(
                id=uuid4(),
                revision_no=old.revision_no + 1,
                predecessor_revision_no=old.revision_no,
                source_sequence=command.expected_recipe_frontier + 1,
                command=command,
                recorded_at=old.recorded_at + timedelta(seconds=1),
                command_hash=command.fingerprint(old.reviewer_user_id),
            )
        )
    )
    scopes = (
        scope.model_copy(update=dict(reviews=(*scope.reviews, review))),
        *source.feature_input.sources.scopes[1:],
    )
    sources = source.feature_input.sources.model_copy(
        update=dict(scopes=scopes, recipe_frontier=review.source_sequence)
    )
    return seal_source(change_feature(source, sources=sources))


def advance_catalog(source):
    sources = source.feature_input.sources
    stream = sources.catalog_streams[0]
    old = stream.reviews[-1]
    command = cat.IngredientProteinReviewCommand.model_validate(
        old.command.model_dump()
        | dict(
            expected_revision_no=old.revision_no,
            predecessor_id=old.id,
            expected_catalog_frontier=sources.catalog_frontier,
            correction_reason="Synthetic association correction",
            idempotency_key=uuid4().hex,
            provenance=provenance().model_dump(),
        )
    )
    review = cat.IngredientProteinReviewFact(
        **(
            old.model_dump()
            | dict(
                id=uuid4(),
                revision_no=old.revision_no + 1,
                predecessor_revision_no=old.revision_no,
                source_sequence=sources.catalog_frontier + 1,
                recorded_at=old.recorded_at + timedelta(microseconds=1),
                command=command,
                command_hash=command.fingerprint(old.reviewer_user_id),
            )
        )
    )
    sources = sources.model_copy(
        update=dict(
            catalog_frontier=review.source_sequence,
            catalog_streams=(stream.model_copy(update=dict(reviews=(*stream.reviews, review))),),
        )
    )
    return seal_source(change_feature(source, sources=sources))
