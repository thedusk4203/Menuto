from datetime import timedelta
from uuid import uuid4

from app.modules.planning import contracts as p
from app.modules.recipes import contracts as r
from culinary_fixtures import culinary_source
from plan_fixtures import NOW
from preference_fixtures import provenance, term


def path_key(recipe, dimension="FLAVOR", **changes):
    from app.modules.recipes.contracts import resolve_culinary_binding

    _, ts, _ = resolve_culinary_binding(
        recipe, recipe.portion_tiers[0].id, (), {i.id: 0 for i in recipe.ingredients}
    )
    paths = {t.requirement_id: t.id for t in ts}
    return r.CulinaryFeaturePathKey(
        **(
            dict(
                recipe_version_id=recipe.id,
                dimension=dimension,
                scope="EXACT_PATH",
                tier_ids=(recipe.portion_tiers[0].id,),
                slots=tuple(
                    dict(
                        requirement_id=i.id,
                        choice="BASE",
                        selected_rule_id=None,
                        preparation="TRANSFORMATION" if i.id in paths else "NONE",
                        transformation_id=paths.get(i.id),
                        adjustment="ZERO_ONLY",
                    )
                    for i in recipe.ingredients
                ),
            )
            | changes
        )
    )


def review_command(recipe, terms, *, dimension="METHOD", key=None, **kw):
    if key is None:
        key = (
            r.RecipeMethodContextKey(recipe_version_id=recipe.id)
            if dimension == "METHOD"
            else path_key(recipe, dimension)
        )
    typ = r.MainProteinFeatureCommand if dimension == "MAIN_PROTEIN" else r.RecipeOnlyFeatureCommand
    return typ(
        **(
            dict(
                contract_version="culinary-feature-register.v1",
                command_kind="REGISTER",
                dimension=dimension,
                recipe_version_id=recipe.id,
                applicability_id=None,
                key=key,
                expected_revision_no=-1,
                predecessor_id=None,
                expected_recipe_frontier=0,
                coverage="COMPLETE",
                covered_term_ids=tuple(t.id for t in terms),
                positive_term_ids=tuple(t.id for t in terms[:1]),
                supports=(),
                provenance=provenance().model_dump(),
                correction_reason=None,
                idempotency_key=uuid4().hex,
            )
            | kw
        )
    )


def scope(command, *, actor=None, aid=None, rid=None):
    actor = actor or uuid4()
    aid = aid or uuid4()
    fact = r.CulinaryFeatureReviewFact(
        id=rid or uuid4(),
        applicability_id=aid,
        recipe_version_id=command.recipe_version_id,
        dimension=command.dimension,
        revision_no=0,
        predecessor_revision_no=None,
        source_sequence=1,
        reviewer_user_id=actor,
        recorded_at=NOW + timedelta(seconds=1),
        command=command,
        command_hash=command.fingerprint(actor),
    )
    return r.CulinaryFeatureScopeFact(id=aid, key=command.key, reviews=(fact,))


def feature_subject(*, dimension="METHOD", coverage="COMPLETE", positives=True, empty=False):
    culinary = culinary_source()
    recipe = culinary.recipes[0]
    terms = (
        term(kind="PROTEIN" if dimension == "MAIN_PROTEIN" else dimension),
        term(kind="PROTEIN" if dimension == "MAIN_PROTEIN" else dimension),
    )
    q = review_command(
        recipe,
        terms,
        dimension=dimension,
        coverage=coverage,
        positive_term_ids=(terms[0].id,) if positives else (),
    )
    sc = scope(q)
    proposal = culinary.proposal
    g = proposal.graph
    batch = g.batches[0]
    request = p.CulinaryFeatureCaptureRequest(
        household_id=g.household_id,
        plan_id=g.plan_id,
        proposal_id=proposal.id,
        proposal_hash=proposal.graph_hash,
        batch_node_id=batch.node_id,
        requested_dimensions=(dimension,),
    )
    workspace = p.PlanWorkspaceDraft(
        id=g.plan_id,
        household_id=g.household_id,
        tracked_member_id=g.tracked_member_id,
        horizon=g.horizon,
        created_by_user_id=proposal.actor_user_id,
        state="DRAFT",
        latest_proposal_no=0,
        active_revision_no=None,
        boundary_version=0,
    )
    context = p.RecipeCookingFeatureContext()
    path = None
    if dimension != "METHOD":
        binding = g.culinary_bindings[0]
        context = p.BoundCulinaryFeatureContext(binding=binding)
        path = r.FeatureSelectedPath(
            tier_id=binding.tier_id,
            selected_rule_ids=(),
            deltas=tuple((i.id, 0) for i in recipe.ingredients),
        )
    sources = r.RecipeFeatureSources(
        recipe_frontier=0 if empty else 1,
        scopes=() if empty else (sc,),
        terms=() if empty else terms,
    )
    evaluation = r.CulinaryFeatureEvaluationInput(
        recipe=recipe,
        requested_dimensions=(dimension,),
        path=path,
        sources=sources,
        captured_at=NOW + timedelta(hours=1),
    )
    return p.CapturedCulinaryFeatureSubjectDraft(
        request=request,
        workspace=workspace,
        proposal=proposal,
        context=context,
        evaluation=evaluation,
    ), terms
