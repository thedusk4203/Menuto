"""Additive NRE transport. Retained consistency never proves database/scientific authority."""

from math import gcd
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, Sha256
from app.domain.feature_identity import canonical, identity_hash
from app.modules.catalog.contracts import IngredientIdentityFact, NutritionReferenceFact
from app.modules.households.contracts import HouseholdMemberIdentity
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition.resolution_limits import BITS, STATES, WORK, ingest, structure
from app.modules.nutrition.synthesis_contracts import (
    NutritionPolicyRequirementSpec,
    NutritionPrecisionSelection,
    NutritionSynthesisSelection,
    NutritionSynthesisSourceSnapshot,
)
from app.modules.recipes.contracts import RecipeVersionSnapshot

NRE_OWNER_RELATIONS = (
    "households",
    "household_members",
    "ingredients",
    "memberships",
    "nutrition_facts",
    "preparation_transformations",
    "recipe_combination_members",
    "recipe_ingredients",
    "recipe_portion_tiers",
    "recipe_rule_combinations",
    "recipe_tier_quantities",
    "recipe_variant_rules",
    "recipe_version_seals",
    "recipe_versions",
    "recipes",
)


def resolution_hash(kind, value):
    structure(value)
    return identity_hash(
        {"domain": "nutrition-resolution." + kind + ".v1", "value": canonical(value)}
    )


def _unique(rows, key):
    result = {}
    for row in rows:
        identity = key(row)
        if identity in result and result[identity] != row:
            raise ValueError("Conflicting duplicate identity")
        result[identity] = row
    return tuple(result[k] for k in sorted(result))


class NreTransport(Contract):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")

    @model_validator(mode="before")
    @classmethod
    def exact(cls, value):
        return canonical(ingest(value))

    @field_validator("planner_ready", "activation_ready", mode="before", check_fields=False)
    @classmethod
    def exact_flags(cls, value):
        if type(value) is not bool:
            raise ValueError("Exact false readiness flag required")
        return value


class NreRational(NreTransport):
    numerator: Annotated[int, Field(strict=True, ge=0, lt=1 << BITS)]
    denominator: Annotated[int, Field(strict=True, gt=0, lt=1 << BITS)]

    @model_validator(mode="after")
    def reduced(self):
        if gcd(self.numerator, self.denominator) != 1:
            raise ValueError("Canonical reduced rational required")
        return self


class NreDelta(NreTransport):
    numerator: Annotated[int, Field(strict=True, gt=-(1 << BITS), lt=1 << BITS)]
    denominator: Annotated[int, Field(strict=True, gt=0, lt=1 << BITS)]

    @model_validator(mode="after")
    def reduced(self):
        if gcd(self.numerator, self.denominator) != 1:
            raise ValueError("Canonical signed reduced rational required")
        return self


class NreResourceProfile(NreTransport):
    version: Literal["NRE_STRUCTURAL_LIMITS_V1"] = "NRE_STRUCTURAL_LIMITS_V1"
    request_bytes: Literal[262144] = 262144
    source_bytes: Literal[16777216] = 16777216
    recipes: Literal[32] = 32
    references: Literal[512] = 512
    owner_rows: Literal[8192] = 8192
    ingredients: Literal[32] = 32
    tiers: Literal[16] = 16
    rule_sets: Literal[16] = 16
    slots: Literal[14] = 14
    alternatives: Literal[64] = 64
    periods: Literal[32] = 32
    deltas: Literal[64] = 64
    states: Literal[16384] = 16384
    witnesses: Literal[65536] = 65536
    work: Literal[1000000] = 1000000
    bits: Literal[256] = 256
    depth: Literal[32] = 32
    string_characters: Literal[100000] = 100000
    statement_seconds: Literal[15] = 15
    operation_seconds: Literal[60] = 60


class NreRecipeSelection(NreTransport):
    recipe_version_id: UUID
    tier_ids: tuple[UUID, ...] = Field(max_length=16)
    rule_selections: tuple[tuple[UUID, ...], ...] = Field(max_length=16)

    @model_validator(mode="after")
    def sets(self):
        object.__setattr__(self, "tier_ids", tuple(sorted(set(self.tier_ids), key=str)))
        if any(len(set(r)) != len(r) for r in self.rule_selections):
            raise ValueError("Duplicate selected rule")
        object.__setattr__(
            self,
            "rule_selections",
            tuple(sorted({tuple(sorted(r, key=str)) for r in self.rule_selections}, key=str)),
        )
        return self


class NreReferenceSelection(NreTransport):
    ingredient_id: UUID
    basis: Literal["EP_RAW_G", "COOKED_G", "COUNT"]
    reference_id: UUID


class NreServingDeclaration(NreTransport):
    kind: Literal["WHOLE_TIER_TO_SINGLE_TRACKED_MEMBER_V1"]
    subject: HouseholdMemberIdentity
    actor_user_id: UUID
    slot_id: Identifier
    recipe_version_id: UUID
    tier_id: UUID
    rule_ids: tuple[UUID, ...]
    serving_definition: Identifier
    nutrition_role: Literal["TRACKED"] = "TRACKED"

    @model_validator(mode="after")
    def rules(self):
        if len(set(self.rule_ids)) != len(self.rule_ids):
            raise ValueError("Duplicate selected rule")
        object.__setattr__(self, "rule_ids", tuple(sorted(self.rule_ids, key=str)))
        return self


class NreSlot(NreTransport):
    slot_id: Identifier
    interval: n.NutritionSourceInterval
    alternatives: tuple[NreServingDeclaration, ...] = Field(max_length=64)

    @model_validator(mode="after")
    def sets(self):
        object.__setattr__(
            self,
            "alternatives",
            _unique(
                self.alternatives,
                lambda r: (str(r.recipe_version_id), str(r.tier_id), tuple(map(str, r.rule_ids))),
            ),
        )
        return self


class NutritionResolutionScopeRequestV1(NreTransport):
    """Selection-only ingress. A fresh capture fingerprint cannot be precomputed by a caller."""

    contract_version: Literal["nutrition-resolution-scope-request.v1"] = (
        "nutrition-resolution-scope-request.v1"
    )
    kind: Literal["EXACT_DECLARED_RECIPE_VERSION_SET_V1"]
    subject: HouseholdMemberIdentity
    actor_user_id: UUID
    root_request: n.NutritionRootRequest
    selection: NutritionSynthesisSelection
    precision: NutritionPrecisionSelection
    recipes: tuple[NreRecipeSelection, ...] = Field(max_length=32)
    references: tuple[NreReferenceSelection, ...] = Field(max_length=512)
    slots: tuple[NreSlot, ...] = Field(max_length=14)
    measurement_basis: Literal["PLANNED_INGREDIENT_INPUT_V1"] = "PLANNED_INGREDIENT_INPUT_V1"
    environment: Literal["TEST_ONLY"]
    profile: NreResourceProfile = NreResourceProfile()
    max_work: Annotated[int, Field(strict=True, gt=0, le=WORK)] = WORK
    max_states: Annotated[int, Field(strict=True, gt=0, le=STATES)] = STATES

    @model_validator(mode="after")
    def sets(self):
        for field, key in (
            ("recipes", lambda r: str(r.recipe_version_id)),
            ("references", lambda r: (str(r.ingredient_id), r.basis)),
            ("slots", lambda r: r.slot_id),
        ):
            object.__setattr__(self, field, _unique(getattr(self, field), key))
        return self


class NutritionResolutionScopeV1(NutritionResolutionScopeRequestV1):
    """Capture-bound immutable scope, pinned by the canonical adapter after fresh projection."""

    contract_version: Literal["nutrition-resolution-scope.v1"] = "nutrition-resolution-scope.v1"
    requirement_fingerprint: Sha256


class NreOwnerAbsence(NreTransport):
    owner: Literal["Recipes", "Catalog", "Households"]
    identity: str
    reason: Identifier


class NreRecipeSeal(NreTransport):
    recipe_version_id: UUID
    sealed: Literal[True]
    body_fingerprint: Sha256


class NreCaptureFrame(NreTransport):
    source_frame: n.NutritionCaptureFrame
    actor_user_id: UUID
    subject: HouseholdMemberIdentity
    membership_id: UUID
    membership_role: Literal["OWNER", "EDITOR"]
    member_id: UUID | None
    started_at: AwareTime
    completed_at: AwareTime
    owner_row_count: Annotated[int, Field(strict=True, ge=0, le=8192)]
    owner_relations: tuple[str, ...]
    owner_frontiers: Literal["NO_NATIVE_FRONTIER"] = "NO_NATIVE_FRONTIER"
    environment: Literal["TEST_ONLY"] = "TEST_ONLY"
    fixture_database_oid: n.NrcOid
    fixture_database_name: str
    fixture_food_fingerprint: Sha256
    fixture_manifest: tuple["NreFixtureFact", ...] = Field(max_length=1568)
    fixture_manifest_authority: Literal["SERVER_OWNED_ISOLATED_TEST_ONLY_CONTEXT"] = (
        "SERVER_OWNED_ISOLATED_TEST_ONLY_CONTEXT"
    )


class NreFixtureFact(NreTransport):
    owner: Literal["Recipe", "Ingredient", "Reference"]
    identity: UUID
    ingredient_id: UUID | None
    body_fingerprint: Sha256


class NutritionResolutionSourcesV1(NreTransport):
    contract_version: Literal["nutrition-resolution-sources.v1"] = "nutrition-resolution-sources.v1"
    scope: NutritionResolutionScopeV1
    synthesis_sources: NutritionSynthesisSourceSnapshot
    requirements: NutritionPolicyRequirementSpec
    recipes: tuple[RecipeVersionSnapshot, ...] = Field(max_length=32)
    recipe_seals: tuple[NreRecipeSeal, ...] = Field(max_length=32)
    ingredients: tuple[IngredientIdentityFact, ...] = Field(max_length=1024)
    references: tuple[NutritionReferenceFact, ...] = Field(max_length=512)
    absences: tuple[NreOwnerAbsence, ...]
    frame: NreCaptureFrame
    source_fingerprint: Sha256


class NreIngredientContribution(NreTransport):
    requirement_id: UUID
    ingredient_id: UUID
    reference_id: UUID
    basis: Literal["EP_RAW_G", "COOKED_G"]
    amount: NreRational
    delta: NreDelta
    nutrients: tuple[NreRational, NreRational, NreRational, NreRational]


class ResolutionConfigurationV1(NreTransport):
    configuration_id: Sha256
    scope_fingerprint: Sha256
    serving: NreServingDeclaration
    recipe_fingerprint: Sha256
    ingredients: tuple[NreIngredientContribution, ...] = Field(min_length=1, max_length=32)
    nutrients: tuple[NreRational, NreRational, NreRational, NreRational]


class NreReachableVector(NreTransport):
    nutrients: tuple[NreRational, NreRational, NreRational, NreRational]
    configurations: tuple[tuple[Sha256, ...], ...] = Field(max_length=65536)


class NrePeriodVectors(NreTransport):
    temporal: n.NutritionTemporalScope
    slot_ids: tuple[Identifier, ...]
    vectors: tuple[NreReachableVector, ...] = Field(max_length=16384)


class NreResolutionGap(NreTransport):
    lower: NreRational
    upper: NreRational
    amount: NreRational
    lower_witnesses: tuple[tuple[Sha256, ...], ...]
    upper_witnesses: tuple[tuple[Sha256, ...], ...]


class ResolutionMeasurementV1(NreTransport):
    subject: HouseholdMemberIdentity
    scope_fingerprint: Sha256
    root_key: Identifier
    descriptor: n.NutritionRootDescriptor
    basis: Literal["PLANNED_INGREDIENT_INPUT_V1"] = "PLANNED_INGREDIENT_INPUT_V1"
    values: tuple[NreRational, ...]
    gaps: tuple[NreResolutionGap, ...]
    maximum_gap: NreRational | None
    step_state: Literal["EXACT_FINITE_GAPS", "NO_ADJACENT_STEP"]


class NutritionResolutionEstimateV1(NreTransport):
    contract_version: Literal["nutrition-resolution-estimate.v1"] = (
        "nutrition-resolution-estimate.v1"
    )
    estimator_version: Literal["EXACT_FINITE_RESOLUTION_V1"] = "EXACT_FINITE_RESOLUTION_V1"
    source_fingerprint: Sha256
    scope_fingerprint: Sha256
    requirements_fingerprint: Sha256
    availability: Literal[
        "AVAILABLE", "UNAVAILABLE", "UNSUPPORTED", "REJECTED", "RESOURCE_EXCEEDED"
    ]
    reasons: tuple[Identifier, ...]
    configurations: tuple[ResolutionConfigurationV1, ...] = Field(max_length=16384)
    periods: tuple[NrePeriodVectors, ...] = Field(max_length=32)
    measurements: tuple[ResolutionMeasurementV1, ...] = Field(max_length=64)
    work_used: Annotated[int, Field(strict=True, ge=0, le=WORK)]
    environment: Literal["TEST_ONLY"] = "TEST_ONLY"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False
    policy_synthesis: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    hard_policy_feasibility: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"
    solver_infeasibility: Literal["NOT_PROVEN"] = "NOT_PROVEN"
    consumption: Literal["NOT_ASSERTED"] = "NOT_ASSERTED"
    measurement_basis: Literal["PLANNED_INGREDIENT_INPUT_V1"] = "PLANNED_INGREDIENT_INPUT_V1"
    result_fingerprint: Sha256

    @model_validator(mode="after")
    def no_partial_value(self):
        if self.availability != "AVAILABLE" and (
            self.configurations or self.periods or self.measurements
        ):
            raise ValueError("Non-success cannot expose partial numerical evidence")
        return self


class NutritionResolutionCheckV1(NreTransport):
    checker_version: Literal["INDEPENDENT_FINITE_RESOLUTION_V1"] = (
        "INDEPENDENT_FINITE_RESOLUTION_V1"
    )
    decision: Literal["CONSISTENT", "INCONSISTENT"]
    numerical_use: Literal["AVAILABLE_RETAINED_ONLY", "NOT_ADMITTED"]
    findings: tuple[Identifier, ...]
    source_fingerprint: Sha256
    reconstructed_result_fingerprint: Sha256 | None
    source_origin: Literal["RETAINED_CONSISTENCY_NOT_DATABASE_PROOF"] = (
        "RETAINED_CONSISTENCY_NOT_DATABASE_PROOF"
    )
    validation_authority: Literal["UNVERIFIED_TRANSPORT"] = "UNVERIFIED_TRANSPORT"
    current_authorization: Literal["NOT_CLAIMED"] = "NOT_CLAIMED"
    scientific_correctness: Literal["NOT_CERTIFIED"] = "NOT_CERTIFIED"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False


class NutritionResolutionHandoffV2(NreTransport):
    contract_version: Literal["nutrition-resolution-handoff.v2"] = "nutrition-resolution-handoff.v2"
    protocol: Literal["CANONICAL_FINITE_RESOLUTION_V2"] = "CANONICAL_FINITE_RESOLUTION_V2"
    sources: NutritionResolutionSourcesV1
    estimate: NutritionResolutionEstimateV1
    validation_authority: Literal["UNVERIFIED_TRANSPORT"] = "UNVERIFIED_TRANSPORT"
    policy_integration: Literal["NOT_AUTHORIZED"] = "NOT_AUTHORIZED"
    production_admission: Literal["CLOSED"] = "CLOSED"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False
