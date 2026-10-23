"""Captured synthetic primitives, not production nutrition/price calibration."""

from app.modules.households.contracts import MealParticipants
from app.modules.inventory.contracts import PhysicalInventorySnapshot
from app.modules.planning.contracts import CandidateGroundingRequest, CandidateGroundingSources
from app.modules.recipes.contracts import VariantGenerationRequest
from app.modules.recipes.public import generate_variants
from app.modules.retail.contracts import Availability, ProcurementSnapshotDraft
from app.modules.retail.public import derive_price_quote
from retail_fixtures import chain
from validation_fixtures import subject


def retail_for(
    ingredient_id, granularity="FIXED_PACK", origin="RETAIL_OBSERVED", availability="LIKELY"
):
    f = chain(granularity)
    f["product"] = f["product"].model_copy(update=dict(canonical_ingredient_id=ingredient_id))
    f["mapping"] = f["mapping"].model_copy(update=dict(ingredient_id=ingredient_id))
    f["cls"] = f["cls"].model_copy(update=dict(ingredient_id=ingredient_id))
    f["member"] = f["member"].model_copy(update=dict(mapping=f["mapping"]))
    f["reference"] = f["reference"].model_copy(update=dict(ingredient_id=ingredient_id))
    f["observation"] = f["observation"].model_copy(
        update=dict(availability=Availability(availability))
    )
    f["quote"] = derive_price_quote(
        **(
            f["quote_inputs"]
            | dict(
                mapping=f["mapping"],
                observation=f["observation"] if origin == "RETAIL_OBSERVED" else None,
                reference=f["reference"] if origin != "RETAIL_OBSERVED" else None,
                calibration=f["calibration"] if origin == "CALIBRATED_REFERENCE" else None,
            )
        )
    )
    f["option"] = f["option"].model_copy(update=dict(quote=f["quote"]))
    return f


def setup(granularity="FIXED_PACK", origin="RETAIL_OBSERVED", availability="LIKELY"):
    s = subject()
    recipe = s.recipes[0]
    candidate = generate_variants(
        VariantGenerationRequest(
            recipe=recipe,
            demand={},
            limits=dict(max_attempts=1, max_candidates=1),
        )
    ).candidates[0]
    f = retail_for(recipe.ingredients[0].ingredient_id, granularity, origin, availability)
    procurement = ProcurementSnapshotDraft(
        procurement_class=f["cls"], members=(f["member"],), options=(f["option"],)
    )
    request = CandidateGroundingRequest(
        candidate=candidate,
        household_id=s.household_id,
        tracked_member_id=s.proposal.graph.tracked_member_id,
        participants=MealParticipants(
            participants=tuple(p.model_dump() for p in s.proposal.graph.meals[0].participants)
        ),
        region_code=f["region"].region_code,
        currency="VND",
        as_of=s.inventory.as_of,
        procurement_class_ids=(f["cls"].id,),
    )
    physical = PhysicalInventorySnapshot.model_validate(
        s.inventory.model_dump(exclude={"contract_version"})
    )
    sources = CandidateGroundingSources(
        recipe=recipe,
        ingredients=s.ingredients,
        nutrition_references=s.nutrition_references,
        procurements=(procurement,),
        retailer_statuses=(f["retailer_status"],),
        members=s.members,
        member_safety=s.member_safety,
        inventory=physical,
    )
    return request, sources, f


def empty_inventory(sources):
    return sources.model_copy(
        update=dict(
            inventory=sources.inventory.model_copy(
                update=dict(
                    lots=(),
                    movements=(),
                    reservations=(),
                    releases=(),
                    positions=(),
                )
            )
        )
    )
