"""Synthetic proposal previews; never accepted commitments or consumption history."""

from datetime import timedelta

from app.domain.units import Provenance
from app.modules.households.contracts import HouseholdMemberIdentity
from app.modules.learning import contracts as c
from app.modules.planning.contracts import PlanWorkspaceDraft
from culinary_fixtures import culinary_source


def snapshot():
    source = culinary_source()
    p, recipe = source.proposal, source.recipes[0]
    g = p.graph
    return c.ExposurePreviewSnapshot(
        household_id=g.household_id,
        member_id=g.tracked_member_id,
        captured_at=p.created_at + timedelta(days=20),
        policy=c.ExposurePreviewPolicy(
            policy_id="preview.explicit-window",
            policy_version="test.v1",
            window=g.horizon,
            provenance=Provenance(
                kind="USER",
                source_system="synthetic-policy",
                external_record_id="fixture",
                source_version="1",
                observed_at=p.created_at,
            ),
        ),
        members=(
            HouseholdMemberIdentity(
                household_id=g.household_id,
                member_id=g.tracked_member_id,
            ),
        ),
        sources=(
            c.ProposalExposureSource(
                workspace=PlanWorkspaceDraft(
                    id=g.plan_id,
                    household_id=g.household_id,
                    tracked_member_id=g.tracked_member_id,
                    created_by_user_id=p.actor_user_id,
                    horizon=g.horizon,
                    state="DRAFT",
                    latest_proposal_no=p.proposal_no,
                    active_revision_no=None,
                    boundary_version=0,
                ),
                proposal=p,
            ),
        ),
        recipes=(
            c.RecipeExposureIdentity(
                recipe_version_id=recipe.id,
                recipe_id=recipe.recipe.id,
                version=recipe.version,
                review_status=recipe.review_status,
                provenance=recipe.provenance,
            ),
        ),
    )
