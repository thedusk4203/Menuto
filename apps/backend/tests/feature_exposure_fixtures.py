"""Synthetic reviewed evidence only; no accepted plan, execution or learned history."""

from datetime import timedelta
from uuid import uuid4

from app.modules.households.contracts import HouseholdMemberIdentity
from app.modules.learning import contracts as c
from app.modules.planning import contracts as p
from app.modules.planning.feature_preview import discover_culinary_feature_assignments
from app.modules.recipes import contracts as r
from feature_fixtures import feature_subject


def source(
    *,
    dimension="FLAVOR",
    coverage="COMPLETE",
    positives=True,
    empty=False,
    batches=2,
    meals=2,
    members=2,
):
    child, terms = feature_subject(
        dimension=dimension,
        coverage=coverage,
        positives=positives,
        empty=empty,
    )
    recipe, proposal = child.evaluation.recipe, child.proposal
    graph = proposal.graph
    mids = (graph.tracked_member_id,) + tuple(uuid4() for _ in range(members - 1))
    data = graph.model_dump()
    batch, binding, meal = graph.batches[0], graph.culinary_bindings[0], graph.meals[0]
    data.update(batches=[], culinary_bindings=[], meals=[], allocations=[])
    for _ in range(batches):
        bid = uuid4()
        bound = binding.model_copy(update={"batch_node_id": bid})
        bound = bound.model_copy(update={"fingerprint": bound.expected_fingerprint()})
        data["culinary_bindings"].append(bound)
        data["batches"].append(
            batch.model_dump()
            | dict(
                node_id=bid,
                culinary_signature=bound.semantic_fingerprint(),
            )
        )
    for n in range(meals):
        mid = uuid4()
        data["meals"].append(
            meal.model_dump()
            | dict(
                node_id=mid,
                scheduled_at=meal.scheduled_at + timedelta(hours=n),
                participants=tuple(
                    dict(
                        member_id=m,
                        portion_factor=1,
                        nutrition_role="TRACKED" if i == 0 else "SHARED",
                    )
                    for i, m in enumerate(mids)
                ),
            )
        )
        for b in data["batches"]:
            data["allocations"].append(
                dict(node_id=uuid4(), batch_node_id=b["node_id"], meal_node_id=mid, servings="0.5")
            )
    graph = p.BoundPlanIntentGraph.model_validate(data)
    proposal = p.BoundPlanProposalSnapshot.model_validate(
        proposal.model_dump()
        | dict(
            graph=graph,
            graph_hash=graph.fingerprint(),
        )
    )
    captured = child.evaluation.captured_at
    policy = c.ExposurePreviewPolicy(
        policy_id="synthetic.feature-source.window",
        policy_version="1",
        window=graph.horizon,
        provenance=dict(
            kind="USER",
            source_system="synthetic-policy",
            external_record_id="policy",
            source_version="1",
            observed_at=proposal.created_at,
        ),
    )
    member_sources = tuple(
        c.ExposurePreviewSnapshot(
            household_id=graph.household_id,
            member_id=m,
            captured_at=captured,
            policy=policy,
            members=tuple(
                HouseholdMemberIdentity(household_id=graph.household_id, member_id=x) for x in mids
            ),
            sources=(c.ProposalExposureSource(workspace=child.workspace, proposal=proposal),),
            recipes=(
                c.RecipeExposureIdentity(
                    recipe_version_id=recipe.id,
                    recipe_id=recipe.recipe.id,
                    version=recipe.version,
                    provenance=recipe.provenance,
                    review_status=recipe.review_status,
                ),
            ),
        )
        for m in mids
    )
    classifications = []
    for b, bound in zip(graph.batches, graph.culinary_bindings, strict=True):
        raw = child.model_dump() | dict(proposal=proposal)
        raw["request"] |= dict(batch_node_id=b.node_id, proposal_hash=proposal.graph_hash)
        if dimension != "METHOD":
            raw["context"] = dict(mode="BOUND_CULINARY_PATH", binding=bound)
        classifications.append(
            discover_culinary_feature_assignments(
                p.CapturedCulinaryFeatureSubjectDraft.model_validate(raw)
            )
        )
    request = c.FeatureExposurePreviewRequest(
        household_id=graph.household_id,
        plan_id=graph.plan_id,
        proposal_id=proposal.id,
        proposal_hash=proposal.graph_hash,
        selected_member_ids=mids,
        requested_dimensions=(dimension,),
        recipe_eligibility_policy=policy,
    )
    return c.FeatureExposureSourceSnapshotDraft(
        request=request,
        capture_completed_at=captured + timedelta(seconds=3),
        member_sources=member_sources,
        classification_sources=tuple(classifications),
        frontiers=(
            c.RecipeExposureFrontier(
                dimension=dimension, recipe_frontier=child.evaluation.sources.recipe_frontier
            ),
        ),
    )


def remap(snapshot, *, graph=None, proposal_id=None, proposal_no=None, revalidate=True):
    """Explicitly rebuild all attached proofs when changing canonical proposal intent."""
    old = snapshot.member_sources[0].sources[0].proposal
    graph = graph or old.graph
    pdata = old.model_dump() | dict(graph=graph, graph_hash=graph.fingerprint())
    if proposal_id is not None:
        pdata["id"] = proposal_id
    if proposal_no is not None:
        pdata["proposal_no"] = proposal_no
    proposal = p.BoundPlanProposalSnapshot.model_validate(pdata)
    workspace = (
        snapshot.member_sources[0]
        .sources[0]
        .workspace.model_copy(update={"latest_proposal_no": proposal.proposal_no})
    )
    data = snapshot.model_dump()
    data["request"] |= dict(proposal_id=proposal.id, proposal_hash=proposal.graph_hash)
    for m in data["member_sources"]:
        m["sources"] = (dict(workspace=workspace, proposal=proposal),)
    for s in data["classification_sources"]:
        s["subject"] |= dict(proposal=proposal, workspace=workspace)
        s["subject"]["request"] |= dict(proposal_id=proposal.id, proposal_hash=proposal.graph_hash)
        if s["subject"]["context"]["mode"] == "BOUND_CULINARY_PATH":
            b = next(
                b
                for b in graph.culinary_bindings
                if b.batch_node_id == s["subject"]["request"]["batch_node_id"]
            )
            s["subject"]["context"]["binding"] = b
            s["subject"]["evaluation"]["path"] = r.FeatureSelectedPath(
                tier_id=b.tier_id,
                selected_rule_ids=tuple(
                    x.selected_rule_id for x in b.requirements if x.selected_rule_id is not None
                ),
                deltas=tuple((x.requirement_id, x.adjustment_delta) for x in b.requirements),
            )
        if revalidate:
            child = p.CapturedCulinaryFeatureSubjectDraft.model_validate(s["subject"])
            s.update(discover_culinary_feature_assignments(child).model_dump())
    return data
