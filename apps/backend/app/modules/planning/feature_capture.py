"""Read-only Planning orchestration of owner sources; no classification inference."""

from sqlalchemy import text

from app.modules.catalog.public import (
    affinity_feature_terms,
    ingredient_protein_frontier,
    ingredient_protein_sources,
)
from app.modules.households.public import read_household_actor
from app.modules.planning import contracts as c
from app.modules.planning.public import PlanStore
from app.modules.recipes.contracts import (
    CulinaryFeatureEvaluationInput,
    FeatureSelectedPath,
    MainProteinFeatureSources,
    RecipeFeatureSources,
)
from app.modules.recipes.public import (
    authored_version,
    culinary_feature_frontier,
    culinary_feature_sources,
)


def capture_culinary_feature_subject(session, request, *, actor_user_id):
    if (
        session.new
        or session.dirty
        or session.deleted
        or session.connection().get_isolation_level() not in {"REPEATABLE READ", "SERIALIZABLE"}
        or session.scalar(text("SHOW transaction_read_only")) != "on"
    ):
        raise ValueError("Feature capture requires clean read-only RR/SERIALIZABLE")
    q = c.CulinaryFeatureCaptureRequest.model_validate(request.model_dump())
    read_household_actor(session, q.household_id, actor_user_id)
    store = PlanStore(session)
    workspace, proposal = store.latest_proposal_source(q.household_id, q.plan_id)
    if proposal is None or (proposal.id, proposal.graph_hash) != (q.proposal_id, q.proposal_hash):
        raise ValueError("Stale current proposal capture")
    batch = next((b for b in proposal.graph.batches if b.node_id == q.batch_node_id), None)
    if batch is None or batch.status != "PLANNED":
        raise ValueError("Canonical planned batch required")
    recipe = authored_version(session, batch.recipe_version_id)
    context = c.RecipeCookingFeatureContext()
    path = None
    if set(q.requested_dimensions) != {"METHOD"}:
        binding = next(
            (
                b
                for b in getattr(proposal.graph, "culinary_bindings", ())
                if b.batch_node_id == q.batch_node_id
            ),
            None,
        )
        if binding is None:
            raise ValueError("CULINARY_BINDING_UNAVAILABLE")
        from app.modules.validation.contracts import CulinaryValidationInput
        from app.modules.validation.public import validate_culinary_grounding

        recipes = tuple(
            authored_version(session, rid)
            for rid in sorted({b.recipe_version_id for b in proposal.graph.batches}, key=str)
        )
        report = validate_culinary_grounding(
            CulinaryValidationInput(proposal=proposal, recipes=recipes)
        )
        if not report.culinary_checks_passed:
            raise ValueError("Independent recipe grounding rejected captured binding")
        context = c.BoundCulinaryFeatureContext(binding=binding)
        path = FeatureSelectedPath(
            tier_id=binding.tier_id,
            selected_rule_ids=tuple(
                r.selected_rule_id for r in binding.requirements if r.selected_rule_id is not None
            ),
            deltas=tuple((r.requirement_id, r.adjustment_delta) for r in binding.requirements),
        )
    scopes = culinary_feature_sources(session, recipe.id, q.requested_dimensions)
    catalog_streams = ()
    extras = {}
    source_type = RecipeFeatureSources
    if "MAIN_PROTEIN" in q.requested_dimensions:
        ids = {
            p.ingredient_id for scope in scopes for r in scope.reviews for p in r.command.supports
        }
        catalog_streams = ingredient_protein_sources(session, ids)
        source_type = MainProteinFeatureSources
        extras = dict(
            catalog_frontier=ingredient_protein_frontier(session), catalog_streams=catalog_streams
        )
    tids = {tid for scope in scopes for r in scope.reviews for tid in r.command.covered_term_ids}
    tids |= {
        tid
        for stream in catalog_streams
        for r in stream.reviews
        for tid in r.command.covered_term_ids
    }
    sources = source_type(
        recipe_frontier=culinary_feature_frontier(session),
        scopes=scopes,
        terms=affinity_feature_terms(session, tids),
        **extras,
    )
    return c.CapturedCulinaryFeatureSubjectDraft(
        request=q,
        workspace=workspace,
        proposal=proposal,
        context=context,
        evaluation=CulinaryFeatureEvaluationInput(
            recipe=recipe,
            requested_dimensions=q.requested_dimensions,
            path=path,
            sources=sources,
            captured_at=store.clock(),
        ),
    )
