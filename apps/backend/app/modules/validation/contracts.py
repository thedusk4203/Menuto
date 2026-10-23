"""Immutable primitive input/report; FOUNDATION_ONLY is never commit authority."""

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from app.domain.canonical import canonical_hash, canonical_json, canonical_value
from app.domain.contracts import (
    AwareTime,
    CalculationDecimal,
    Contract,
    Identifier,
    NonNegativeCalculationDecimal,
    Sha256,
)
from app.domain.units import CalculatedQuantity, QuantityIdentity
from app.modules.catalog.contracts import IngredientIdentityFact, NutritionReferenceFact
from app.modules.households.contracts import HouseholdMemberIdentity
from app.modules.inventory.contracts import (
    InventoryLot,
    InventoryMovement,
    InventoryPosition,
    InventoryReservation,
    InventoryReservationRelease,
)
from app.modules.nutrition.contracts import CanonicalMemberSafetySnapshot
from app.modules.planning.contracts import (
    BoundPlanProposalSnapshot,
    PlanProposalSnapshot,
    PlanRevisionSnapshot,
)
from app.modules.policy.contracts import ValidationCoveragePolicySnapshot
from app.modules.recipes.contracts import RecipeVersionSnapshot


class DeferredCapability(StrEnum):
    ROOT_NUTRITION_POLICY = "ROOT_NUTRITION_POLICY"
    ALLERGEN_DIET_CLASSIFICATION = "ALLERGEN_DIET_CLASSIFICATION"
    EXACT_GROUNDED_BINDING = "EXACT_GROUNDED_BINDING"
    PROCUREMENT_SCENARIOS = "PROCUREMENT_SCENARIOS"
    PLANNED_MATERIAL_ALLOCATION = "PLANNED_MATERIAL_ALLOCATION"
    BATCH_FLOW_EXECUTION = "BATCH_FLOW_EXECUTION"
    ASSUMPTION_GRAPH = "ASSUMPTION_GRAPH"
    HORIZON_BRIDGE = "HORIZON_BRIDGE"
    PRODUCTION_AUTHORITY = "PRODUCTION_AUTHORITY"
    REVISION_MATERIALIZATION_REPLAY = "REVISION_MATERIALIZATION_REPLAY"


DEFERRED_CAPABILITIES = tuple(DeferredCapability)


class InventoryValidationFacts(Contract):
    """Primitive arrays, intentionally no aggregate replay validator before POSTFACT checks."""

    contract_version: Literal["inventory-validation-facts.v1"] = "inventory-validation-facts.v1"

    household_id: UUID
    as_of: AwareTime
    lots: tuple[InventoryLot, ...]
    movements: tuple[InventoryMovement, ...]
    reservations: tuple[InventoryReservation, ...]
    releases: tuple[InventoryReservationRelease, ...]
    positions: tuple[InventoryPosition, ...]


class ValidationSourceFrontier(Contract):
    current_revision_no: Annotated[int, Field(strict=True, ge=0)] | None
    inventory_ledger_sequence: Annotated[int, Field(strict=True, ge=0)]
    materialization_boundary_version: Annotated[int, Field(strict=True, ge=0)]
    capture_consistency: Literal["REPEATABLE_READ", "SERIALIZABLE", "EXPLICIT_INPUT"]


class ValidationSubjectSnapshot(Contract):
    contract_version: Literal["validation-subject.v1-foundation"] = (
        "validation-subject.v1-foundation"
    )
    coverage: Literal["FOUNDATION_ONLY"] = "FOUNDATION_ONLY"
    validation_ready: Literal[False] = False
    household_id: UUID
    proposal: PlanProposalSnapshot
    parent_revision: PlanRevisionSnapshot | None
    source_frontier: ValidationSourceFrontier
    members: tuple[HouseholdMemberIdentity, ...]
    member_safety: tuple[CanonicalMemberSafetySnapshot, ...]
    ingredients: tuple[IngredientIdentityFact, ...]
    nutrition_references: tuple[NutritionReferenceFact, ...]
    recipes: tuple[RecipeVersionSnapshot, ...]
    inventory: InventoryValidationFacts
    policy: ValidationCoveragePolicySnapshot
    root_nutrition_policy: Literal["DEFERRED"] = "DEFERRED"
    procurement_resolution: Literal["DEFERRED"] = "DEFERRED"
    exact_grounded_binding: Literal["DEFERRED"] = "DEFERRED"
    bridge_assumptions_batch_flow: Literal["DEFERRED"] = "DEFERRED"

    @property
    def fingerprint(self):
        return canonical_hash(self)

    def canonical_json(self):
        return canonical_json(canonical_value(self))


class ValidationFinding(Contract):
    code: Identifier
    severity: Literal["FATAL", "ERROR", "WARNING", "INFO"]
    source_domain: Literal["DATA", "POLICY", "PLAN", "EXECUTION"]
    scope: str
    proof_refs: tuple[str, ...]
    detail: str


class CalculatedNutrition(Contract):
    energy_kcal: NonNegativeCalculationDecimal
    protein_g: NonNegativeCalculationDecimal
    fat_g: NonNegativeCalculationDecimal
    carbohydrate_g: NonNegativeCalculationDecimal


class DefaultBatchInputDerivation(Contract):
    """Authored default input only, not fully grounded meal/member nutrient allocation."""

    batch_node_id: UUID
    recipe_version_id: UUID
    tier_id: UUID
    requirement_ids: tuple[UUID, ...]
    nutrition_reference_ids: tuple[UUID, ...]
    input_nutrition: CalculatedNutrition | None


class MaterialBalanceDerivation(Contract):
    lot_id: UUID
    quantity_identity: QuantityIdentity
    signed_closing_amount: CalculationDecimal
    signed_reserved_amount: CalculationDecimal


class YieldEstimate(Contract):
    owner: Literal["RETAIL_MAPPING", "RECIPE_PREPARATION"]
    owner_id: UUID
    context_id: UUID
    input: CalculatedQuantity
    output: CalculatedQuantity


class ValidationReport(Contract):
    contract_version: Literal["validation-report.v1-foundation"] = "validation-report.v1-foundation"
    evaluator_version: Literal["independent-foundation.1"] = "independent-foundation.1"
    phase: Literal["PRECOMMIT_VALIDATION", "POSTFACT_VALIDATION"]
    decision: Literal["REJECTED", "BLOCKED_UNSUPPORTED", "DIAGNOSTIC"]
    activation_authorized: Literal[False] = False
    subject_hash: Sha256
    policy_hash: Sha256
    expected_revision: int | None
    findings: tuple[ValidationFinding, ...]
    default_batch_inputs: tuple[DefaultBatchInputDerivation, ...]
    material_balances: tuple[MaterialBalanceDerivation, ...]
    yield_estimates: tuple[YieldEstimate, ...]
    deferred_capabilities: tuple[DeferredCapability, ...]


class CulinaryValidationInput(Contract):
    contract_version: Literal["culinary-validation-input.v1"] = "culinary-validation-input.v1"
    activation_ready: Literal[False] = False
    proposal: BoundPlanProposalSnapshot
    recipes: tuple[RecipeVersionSnapshot, ...]

    @property
    def fingerprint(self):
        from app.domain.canonical import canonical_hash

        # Proposal/binding have explicit relationship IDs. Recipe facts are unordered;
        # procedure text retains its own order. No GroundedVariantDraft is embedded.
        return canonical_hash(self)


class RecipeGroundingReport(Contract):
    contract_version: Literal["recipe-grounding-report.v1"] = "recipe-grounding-report.v1"
    phase: Literal["PRECOMMIT_VALIDATION", "POSTFACT_VALIDATION"]
    subject_hash: Sha256
    activation_authorized: Literal[False] = False
    culinary_checks_passed: bool
    findings: tuple[ValidationFinding, ...]
