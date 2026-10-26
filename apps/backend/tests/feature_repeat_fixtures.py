"""Explicit synthetic policies and reviewed sources; never production defaults."""

from datetime import timedelta
from uuid import uuid4

from app.modules.catalog import contracts as cat
from app.modules.learning import contracts as c
from app.modules.learning.public import (
    assess_feature_cooldown,
    interpret_feature_repeat_penalty,
    preview_feature_exposure,
    trace_feature_decay,
)
from app.modules.planning import contracts as p
from app.modules.planning.culinary import author_binding
from app.modules.planning.feature_preview import discover_culinary_feature_assignments as discover
from app.modules.recipes import contracts as r
from feature_exposure_fixtures import remap, source
from feature_fixtures import review_command, scope
from plan_fixtures import NOW
from preference_fixtures import provenance, term

HOUR = 3_600_000_000


def policies(query, *, duration=2 * HOUR, observed=None, unit=(7, 3), bands=None):
    common = dict(
        policy_id="synthetic.feature-policy",
        policy_version="test.1",
        provenance=provenance(**({} if observed is None else dict(observed_at=observed))),
        dimension=query.dimension,
        feature_term_id=query.feature_term_id,
    )
    return (
        c.FeatureCooldownPolicy(**common, duration_microseconds=duration),
        c.FeatureDecayPolicy(
            **common,
            bands=bands
            if bands is not None
            else (
                c.FeatureDecayBand(
                    ordinal=0,
                    lower_age_microseconds=0,
                    upper_age_microseconds=duration,
                    retention_multiplier=dict(numerator=1, denominator=2),
                ),
            ),
        ),
        c.FeatureRepeatPenaltyPolicy(
            **common,
            operator="SUM_RETAINED_TERM_OCCURRENCES",
            unit_penalty=dict(numerator=unit[0], denominator=unit[1]),
        ),
    )


def query_for(preview, *, target=None, dimension=None, term_id=None):
    e = max(preview.events, key=lambda e: e.scheduled_at) if target is None else target
    return c.FeatureRepeatQuery(
        household_id=e.household_id,
        member_id=e.member_id,
        plan_id=e.plan_id,
        proposal_id=e.proposal_id,
        proposal_hash=e.proposal_hash,
        meal_node_id=e.meal_node_id,
        dimension=dimension or e.dimension,
        feature_term_id=term_id or e.feature_term_id,
    )


def stages(preview, *, query=None, duration=2 * HOUR, observed=None, unit=(7, 3), bands=None):
    query = query or query_for(preview)
    cool, decay, penalty = policies(
        query, duration=duration, observed=observed, unit=unit, bands=bands
    )
    assessment = assess_feature_cooldown(
        c.FeatureCooldownInput(
            preview=preview,
            query=query,
            policy=cool,
        )
    )
    trace = trace_feature_decay(c.FeatureDecayInput(assessment=assessment, policy=decay))
    result = interpret_feature_repeat_penalty(
        c.FeatureRepeatPenaltyInput(trace=trace, policy=penalty)
    )
    return assessment, trace, result


def repeat_preview(
    *, dimension="FLAVOR", rows=(("positive",), ("positive",)), times=None, main_slots=1
):
    """Independent reviewed RecipeVersions per cell; only requested meal allocations exist."""
    total = sum(map(len, rows))
    base = source(
        dimension="FLAVOR" if dimension == "MAIN_PROTEIN" else dimension,
        batches=total,
        meals=len(rows),
        members=1,
    )
    old = base.member_sources[0].sources[0].proposal
    graph = old.graph
    prototype = base.classification_sources[0].subject
    terms = (
        term("PROTEIN" if dimension == "MAIN_PROTEIN" else dimension),
        term("PROTEIN" if dimension == "MAIN_PROTEIN" else dimension),
    )
    # Pin the same immutable Catalog association sources across all MAIN_PROTEIN cells.
    streams = []
    actor = uuid4()
    for n, item in enumerate(prototype.evaluation.recipe.ingredients[:main_slots]):
        cmd = cat.IngredientProteinReviewCommand(
            command_kind="REPLACE",
            ingredient_id=item.ingredient_id,
            expected_revision_no=-1,
            expected_catalog_frontier=n,
            predecessor_id=None,
            coverage="COMPLETE",
            covered_term_ids=tuple(t.id for t in terms),
            positive_term_ids=(terms[0].id,),
            provenance=provenance().model_dump(),
            correction_reason=None,
            idempotency_key=uuid4().hex,
        )
        sid = uuid4()
        review = cat.IngredientProteinReviewFact(
            id=uuid4(),
            stream_id=sid,
            ingredient_id=item.ingredient_id,
            revision_no=0,
            predecessor_revision_no=None,
            source_sequence=n + 1,
            reviewer_user_id=actor,
            recorded_at=NOW + timedelta(seconds=1),
            command=cmd,
            command_hash=cmd.fingerprint(actor),
        )
        streams.append(
            cat.IngredientProteinStreamFact(
                id=sid, ingredient_id=item.ingredient_id, reviews=(review,)
            )
        )
    gd = graph.model_dump()
    gd["culinary_bindings"] = list(gd["culinary_bindings"])
    if times is not None:
        for m, time in zip(gd["meals"], times, strict=True):
            m["scheduled_at"] = time
    allocations, identities, specs = [], [], []
    index = 0
    for meal_index, states in enumerate(rows):
        for state in states:
            b = gd["batches"][index]
            original_recipe = prototype.evaluation.recipe
            rid = uuid4()

            def owners(value):
                if isinstance(value, dict):
                    return {
                        k: rid if k == "recipe_version_id" else owners(v) for k, v in value.items()
                    }
                if isinstance(value, (tuple, list)):
                    return tuple(owners(v) for v in value)
                return value

            recipe = r.RecipeVersionSnapshot.model_validate(
                owners(original_recipe.model_dump()) | dict(id=rid, version=index + 1)
            )
            binding = author_binding(
                recipe=recipe,
                tier_id=recipe.portion_tiers[0].id,
                selected_rule_ids=(),
                deltas={i.id: 0 for i in recipe.ingredients},
                provenance=graph.culinary_bindings[0].provenance,
                household_id=graph.household_id,
                plan_id=graph.plan_id,
                proposal_id=old.id,
                batch_node_id=b["node_id"],
            )
            gd["culinary_bindings"][index] = binding.model_dump()
            b.update(recipe_version_id=rid, culinary_signature=binding.semantic_fingerprint())
            allocations.extend(
                a
                for a in gd["allocations"]
                if a["batch_node_id"] == b["node_id"]
                and a["meal_node_id"] == gd["meals"][meal_index]["node_id"]
            )
            identities.append(
                c.RecipeExposureIdentity(
                    recipe_version_id=rid,
                    recipe_id=recipe.recipe.id,
                    version=recipe.version,
                    provenance=recipe.provenance,
                    review_status=recipe.review_status,
                )
            )
            specs.append((state, recipe, binding))
            index += 1
    gd["allocations"] = allocations
    graph = p.BoundPlanIntentGraph.model_validate(gd)
    data = remap(base, graph=graph, revalidate=False)
    data["request"]["requested_dimensions"] = (dimension,)
    for member in data["member_sources"]:
        member["recipes"] = tuple(identities)
    children = []
    for n, (state, recipe, binding) in enumerate(specs):
        positive = (terms[0].id,) if state in {"positive", "partial", "stale"} else ()
        universe = terms[1:] if state in {"outside", "not_captured"} else terms
        cmd_kw = dict(
            dimension=dimension,
            expected_recipe_frontier=n,
            positive_term_ids=positive,
            coverage="PARTIAL" if state in {"partial", "partial_absent"} else "COMPLETE",
        )
        if dimension == "MAIN_PROTEIN":
            cmd_kw.update(
                expected_catalog_frontier=len(streams),
                supports=tuple(
                    dict(
                        term_id=terms[0].id,
                        requirement_id=item.id,
                        ingredient_id=item.ingredient_id,
                        catalog_review_id=stream.reviews[0].id,
                    )
                    for item, stream in zip(recipe.ingredients[:main_slots], streams, strict=True)
                )
                if positive
                else (),
            )
        cmd = review_command(recipe, universe, **cmd_kw)
        sc = scope(cmd.model_copy(update={"expected_recipe_frontier": 0}), actor=actor)
        review = sc.reviews[0].model_copy(
            update={
                "source_sequence": n + 1,
                "command": cmd,
                "command_hash": cmd.fingerprint(actor),
            }
        )
        sc = sc.model_copy(update={"reviews": (review,)})
        if state == "outside":
            initial = review_command(
                recipe, terms, dimension=dimension, expected_recipe_frontier=n, positive_term_ids=()
            )
            review = review.model_copy(
                update={"command": initial, "command_hash": initial.fingerprint(actor)}
            )
            replacement = r.RecipeOnlyFeatureCommand.model_validate(
                cmd.model_dump()
                | dict(
                    contract_version="culinary-feature-write.v1",
                    command_kind="REPLACE",
                    key=None,
                    applicability_id=sc.id,
                    expected_revision_no=0,
                    predecessor_id=review.id,
                    expected_recipe_frontier=total + n,
                    correction_reason="Synthetic finite universe",
                    idempotency_key=uuid4().hex,
                )
            )
            tail = r.CulinaryFeatureReviewFact(
                id=uuid4(),
                applicability_id=sc.id,
                recipe_version_id=recipe.id,
                dimension=dimension,
                revision_no=1,
                predecessor_revision_no=0,
                source_sequence=total + n + 1,
                reviewer_user_id=actor,
                recorded_at=NOW + timedelta(seconds=2),
                command=replacement,
                command_hash=replacement.fingerprint(actor),
            )
            sc = sc.model_copy(update={"reviews": (review, tail)})
        if state == "retracted":
            retract = r.RecipeOnlyFeatureCommand.model_validate(
                cmd.model_dump()
                | dict(
                    contract_version="culinary-feature-retract.v1",
                    command_kind="RETRACT",
                    key=None,
                    applicability_id=sc.id,
                    expected_revision_no=0,
                    predecessor_id=review.id,
                    expected_recipe_frontier=total + n,
                    coverage=None,
                    covered_term_ids=(),
                    positive_term_ids=(),
                    supports=(),
                    correction_reason="Synthetic retraction",
                    idempotency_key=uuid4().hex,
                )
            )
            tail = r.CulinaryFeatureReviewFact(
                id=uuid4(),
                applicability_id=sc.id,
                recipe_version_id=recipe.id,
                dimension=dimension,
                revision_no=1,
                predecessor_revision_no=0,
                source_sequence=total + n + 1,
                reviewer_user_id=actor,
                recorded_at=NOW + timedelta(seconds=2),
                command=retract,
                command_hash=retract.fingerprint(actor),
            )
            sc = sc.model_copy(update={"reviews": (review, tail)})
        scopes = () if state == "no_source" else (sc,)
        source_data = dict(
            recipe_frontier=2 * total,
            scopes=scopes,
            terms=() if not scopes else terms if state == "outside" else universe,
        )
        if dimension == "MAIN_PROTEIN":
            source_data.update(
                catalog_frontier=len(streams), catalog_streams=tuple(streams) if positive else ()
            )
        evaluation = r.CulinaryFeatureEvaluationInput(
            recipe=recipe,
            requested_dimensions=(dimension,),
            path=None
            if dimension == "METHOD"
            else r.FeatureSelectedPath(
                tier_id=binding.tier_id,
                selected_rule_ids=(),
                deltas=tuple((i.id, 0) for i in recipe.ingredients),
            ),
            sources=source_data,
            captured_at=prototype.evaluation.captured_at,
        )
        child = next(
            v["subject"]
            for v in data["classification_sources"]
            if v["subject"]["request"]["batch_node_id"] == binding.batch_node_id
        )
        child["request"]["requested_dimensions"] = (dimension,)
        child["evaluation"] = evaluation
        child["context"] = (
            p.RecipeCookingFeatureContext()
            if dimension == "METHOD"
            else p.BoundCulinaryFeatureContext(binding=binding)
        )
        children.append(discover(p.CapturedCulinaryFeatureSubjectDraft.model_validate(child)))
    data["classification_sources"] = tuple(children)
    data["frontiers"] = (
        dict(dimension=dimension, recipe_frontier=2 * total)
        | (dict(catalog_frontier=len(streams)) if dimension == "MAIN_PROTEIN" else {}),
    )
    return preview_feature_exposure(c.FeatureExposureSourceSnapshotDraft.model_validate(data))
