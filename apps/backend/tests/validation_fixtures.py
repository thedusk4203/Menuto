"""Synthetic partial source subjects, never production authorization/clinical policy."""

from datetime import timedelta
from uuid import uuid4

from app.domain.units import Provenance, Quantity
from app.modules.catalog.contracts import (
    IngredientIdentityFact,
    NutritionFact,
    NutritionReferenceFact,
    NutritionValues,
)
from app.modules.households.contracts import HouseholdMemberIdentity
from app.modules.inventory.contracts import (
    InventoryLot,
    InventoryMovement,
    InventoryPosition,
    InventoryReservation,
)
from app.modules.nutrition.contracts import CanonicalMemberSafetySnapshot
from app.modules.planning.contracts import PlanIntentGraph, PlanProposalSnapshot
from app.modules.policy.contracts import ValidationCoveragePolicySnapshot
from app.modules.recipes.contracts import RecipeVersionSnapshot
from app.modules.validation.contracts import (
    InventoryValidationFacts,
    ValidationSourceFrontier,
    ValidationSubjectSnapshot,
)
from inventory_fixtures import evidence
from plan_fixtures import NOW, graph_data
from recipe_fixtures import recipe_data


def simple_recipe_data():
    data = recipe_data()
    data["ingredients"] = data["ingredients"][:1]
    data["variant_rules"] = []
    data["transformations"] = data["transformations"][:1]
    for tier in data["portion_tiers"]:
        tier["quantities"] = tier["quantities"][:1]
    return data


def coverage_policy(**changes):
    return ValidationCoveragePolicySnapshot(
        **(
            dict(
                policy_version="1",
                provenance=Provenance(
                    kind="USER",
                    source_system="synthetic.coverage",
                    external_record_id="fixture.definition",
                    source_version="1",
                    observed_at=NOW - timedelta(days=1),
                ),
            )
            | changes
        )
    )


def subject():
    actor, lot_id = uuid4(), uuid4()
    r = RecipeVersionSnapshot.model_validate(simple_recipe_data())
    ingredient = r.ingredients[0].ingredient_id
    d = graph_data()
    household = d["household_id"]
    member = d["tracked_member_id"]
    batch = uuid4()
    d["meals"][0]["meal_kind"] = "HOME"
    d["batches"] = [
        dict(
            node_id=batch,
            recipe_version_id=r.id,
            tier_id=r.portion_tiers[0].id,
            planned_servings="2",
            planned_at=NOW + timedelta(hours=1),
        )
    ]
    d["allocations"] = [
        dict(
            node_id=uuid4(),
            batch_node_id=batch,
            meal_node_id=d["meals"][0]["node_id"],
            servings="2",
        )
    ]
    g = PlanIntentGraph.model_validate(d)
    proposal = PlanProposalSnapshot(
        id=uuid4(),
        proposal_no=0,
        graph=g,
        graph_hash=g.fingerprint(),
        expected_revision=None,
        scope="REMAINING_HORIZON",
        effective_from=NOW,
        actor_user_id=actor,
        source_system="synthetic",
        idempotency_key=str(uuid4()),
        reason="Fixture only",
        created_at=NOW,
    )
    acquired = NOW - timedelta(hours=2)
    lot = InventoryLot(
        id=lot_id,
        household_id=household,
        asset_type="RAW_INGREDIENT",
        ingredient_id=ingredient,
        acquired_quantity=Quantity(amount="500", basis="EP_RAW_G"),
        acquired_at=acquired,
        created_at=acquired,
        usable_until=NOW + timedelta(days=3),
        observation_confidence="CONFIRMED",
        serving_definition=None,
    )

    def ledger(seq, **changes):
        return dict(
            id=uuid4(),
            household_id=household,
            lot_id=lot_id,
            occurred_at=acquired + timedelta(seconds=seq - 1),
            recorded_at=acquired + timedelta(seconds=seq),
            ledger_sequence=seq,
            idempotency_key=str(uuid4()),
            command_fingerprint="a" * 64,
            evidence=evidence(actor),
            reason="Explicit synthetic confirmation",
            **changes,
        )

    opening = InventoryMovement(
        **ledger(1, phase=10, movement_type="ACQUIRE", quantity=lot.acquired_quantity)
    )
    reserve = InventoryReservation(
        **ledger(
            2,
            phase=20,
            purpose="Meal allocation intent",
            quantity=Quantity(amount="200", basis="EP_RAW_G"),
        )
    )
    consume = InventoryMovement(
        **ledger(
            3, phase=30, movement_type="CONSUME", quantity=Quantity(amount="100", basis="EP_RAW_G")
        )
    )
    inventory = InventoryValidationFacts(
        household_id=household,
        as_of=NOW,
        lots=(lot,),
        movements=(opening, consume),
        reservations=(reserve,),
        releases=(),
        positions=(
            InventoryPosition(
                lot_id=lot_id,
                remaining=Quantity(amount="400", basis="EP_RAW_G"),
                reserved=reserve.quantity,
                lifecycle_state="ACTIVE",
            ),
        ),
    )
    nutrition = NutritionReferenceFact(
        id=uuid4(),
        fact=NutritionFact(
            ingredient_id=ingredient,
            reference=Quantity(amount="100", basis="EP_RAW_G"),
            nutrients=NutritionValues(
                energy_kcal="200", protein_g="20", fat_g="5", carbohydrate_g="10"
            ),
            provenance=Provenance(
                kind="REVIEWED_REFERENCE",
                source_system="synthetic.nutrition",
                external_record_id="fixture.reference",
                source_version="1",
                observed_at=acquired,
            ),
            status="REVIEWED",
        ),
    )
    return ValidationSubjectSnapshot(
        household_id=household,
        proposal=proposal,
        parent_revision=None,
        source_frontier=ValidationSourceFrontier(
            current_revision_no=None,
            inventory_ledger_sequence=3,
            materialization_boundary_version=0,
            capture_consistency="EXPLICIT_INPUT",
        ),
        members=(HouseholdMemberIdentity(household_id=household, member_id=member),),
        member_safety=(
            CanonicalMemberSafetySnapshot(household_id=household, member_id=member, constraints=()),
        ),
        ingredients=(IngredientIdentityFact(id=ingredient, name="Fixture chicken"),),
        nutrition_references=(nutrition,),
        recipes=(r,),
        inventory=inventory,
        policy=coverage_policy(),
    )
