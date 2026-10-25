"""Primitive nutrition references carry their own measurement basis and evidence."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, Label, NonNegativeDecimal, Sha256
from app.domain.feature_identity import identity_hash, unique_sorted
from app.domain.units import MeasurementBasis, Provenance, Quantity


class IngredientCreate(Contract):
    name: Label


class IngredientIdentityFact(Contract):
    contract_version: Literal["ingredient-identity.v1"] = "ingredient-identity.v1"
    id: UUID
    name: Label


class NutritionValues(Contract):
    energy_kcal: NonNegativeDecimal
    protein_g: NonNegativeDecimal
    fat_g: NonNegativeDecimal
    carbohydrate_g: NonNegativeDecimal


class NutritionFact(Contract):
    ingredient_id: UUID
    reference: Quantity
    nutrients: NutritionValues
    provenance: Provenance
    status: Literal["DRAFT", "REVIEWED"]

    @model_validator(mode="after")
    def usable_reference(self):
        if self.reference.amount <= 0:
            raise ValueError("Nutrition reference amount must be positive")
        if self.reference.basis not in {MeasurementBasis.EP_RAW_G, MeasurementBasis.COOKED_G}:
            raise ValueError("Nutrition reference must use edible raw or cooked mass")
        return self


class NutritionReferenceFact(Contract):
    contract_version: Literal["nutrition-reference-source.v1"] = "nutrition-reference-source.v1"
    id: UUID
    fact: NutritionFact


class AffinityFeatureTermFact(Contract):
    """Reviewed vocabulary meaning only, never inferred recipe/ingredient classification."""

    contract_version: Literal["affinity-feature-term.v1"] = "affinity-feature-term.v1"
    id: UUID
    kind: Literal["PROTEIN", "METHOD", "FLAVOR"]
    code: Identifier
    version: Annotated[int, Field(strict=True, gt=0, le=2_147_483_647)]
    label: Label
    definition: Annotated[str, Field(min_length=1, max_length=4000, pattern=r"\S")]
    status: Literal["DRAFT", "REVIEWED"]
    provenance: Provenance

    @model_validator(mode="after")
    def authored_source(self):
        if self.provenance.kind not in {"USER", "REVIEWED_REFERENCE"}:
            raise ValueError("Feature vocabulary requires authored/curated source")
        return self


# Additive MTR-046A source contracts. Existing vocabulary contracts remain unchanged.


FeatureRevision = Annotated[int, Field(strict=True, ge=0, le=2_147_483_647)]
FeatureExpectedRevision = Annotated[int, Field(strict=True, ge=-1, le=2_147_483_647)]
FeatureFrontier = Annotated[int, Field(strict=True, ge=0, le=9_223_372_036_854_775_807)]
FeatureSequence = Annotated[int, Field(strict=True, gt=0, le=9_223_372_036_854_775_807)]


class FeatureReviewSource(Provenance):
    kind: Literal["USER", "REVIEWED_REFERENCE"]


class IngredientProteinReviewCommand(Contract):
    contract_version: Literal["ingredient-protein-write.v1", "ingredient-protein-retract.v1"] = (
        "ingredient-protein-write.v1"
    )
    command_kind: Literal["REPLACE", "RETRACT"]
    ingredient_id: UUID
    expected_revision_no: FeatureExpectedRevision
    expected_catalog_frontier: FeatureFrontier
    predecessor_id: UUID | None
    coverage: Literal["PARTIAL", "COMPLETE"] | None
    covered_term_ids: tuple[UUID, ...]
    positive_term_ids: tuple[UUID, ...]
    provenance: FeatureReviewSource
    correction_reason: Label | None
    idempotency_key: Identifier

    @model_validator(mode="after")
    def review_shape(self):
        expected_version = (
            "ingredient-protein-retract.v1"
            if self.command_kind == "RETRACT"
            else "ingredient-protein-write.v1"
        )
        if self.contract_version != expected_version:
            raise ValueError("Command kind/version mismatch")
        object.__setattr__(self, "covered_term_ids", unique_sorted(self.covered_term_ids))
        object.__setattr__(self, "positive_term_ids", unique_sorted(self.positive_term_ids))
        if (self.expected_revision_no == -1) != (self.predecessor_id is None):
            raise ValueError("Predecessor/revision mismatch")
        if self.expected_revision_no >= 0 and self.correction_reason is None:
            raise ValueError("Correction reason required")
        if self.command_kind == "RETRACT":
            if (
                self.expected_revision_no < 0
                or self.coverage is not None
                or self.covered_term_ids
                or self.positive_term_ids
            ):
                raise ValueError("Retraction requires prior review and no coverage/children")
        elif (
            self.coverage is None
            or not self.covered_term_ids
            or not set(self.positive_term_ids) <= set(self.covered_term_ids)
        ):
            raise ValueError("Replacement requires covered universe and positive subset")
        return self

    def fingerprint(self, actor_user_id):
        return identity_hash(dict(command=self, actor_user_id=actor_user_id))


class ReplaceIngredientProteinReviewCommand(IngredientProteinReviewCommand):
    contract_version: Literal["ingredient-protein-write.v1"] = "ingredient-protein-write.v1"
    command_kind: Literal["REPLACE"] = "REPLACE"


class RetractIngredientProteinReviewCommand(IngredientProteinReviewCommand):
    contract_version: Literal["ingredient-protein-retract.v1"] = "ingredient-protein-retract.v1"
    command_kind: Literal["RETRACT"] = "RETRACT"


class IngredientProteinReviewFact(Contract):
    contract_version: Literal["ingredient-protein-review.v1"] = "ingredient-protein-review.v1"
    id: UUID
    stream_id: UUID
    ingredient_id: UUID
    revision_no: FeatureRevision
    predecessor_revision_no: FeatureRevision | None
    source_sequence: FeatureSequence
    reviewer_user_id: UUID
    recorded_at: AwareTime
    command: IngredientProteinReviewCommand
    command_hash: Sha256

    @model_validator(mode="after")
    def lineage(self):
        if (
            self.ingredient_id != self.command.ingredient_id
            or self.revision_no != self.command.expected_revision_no + 1
            or self.predecessor_revision_no != (self.revision_no - 1 if self.revision_no else None)
            or self.command_hash != self.command.fingerprint(self.reviewer_user_id)
            or self.command.provenance.observed_at > self.recorded_at
            or self.source_sequence != self.command.expected_catalog_frontier + 1
        ):
            raise ValueError("Catalog review ownership/lineage/hash/time mismatch")
        return self


class IngredientProteinStreamFact(Contract):
    contract_version: Literal["ingredient-protein-stream.v1"] = "ingredient-protein-stream.v1"
    id: UUID
    ingredient_id: UUID
    reviews: Annotated[tuple[IngredientProteinReviewFact, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def complete_history(self):
        unique_sorted(self.reviews, key=lambda r: r.id)
        rows = unique_sorted(self.reviews, key=lambda r: r.revision_no)
        object.__setattr__(self, "reviews", rows)
        for n, r in enumerate(rows):
            if (
                r.revision_no != n
                or r.stream_id != self.id
                or r.ingredient_id != self.ingredient_id
                or r.command.predecessor_id != (rows[n - 1].id if n else None)
                or (
                    n
                    and (
                        r.source_sequence <= rows[n - 1].source_sequence
                        or r.recorded_at < rows[n - 1].recorded_at
                    )
                )
                or (
                    r.command.command_kind == "RETRACT"
                    and (not n or rows[n - 1].command.command_kind != "REPLACE")
                )
            ):
                raise ValueError("Incomplete/conflicting Catalog history")
        return self


class IngredientProteinWriteReceipt(Contract):
    contract_version: Literal["ingredient-protein-write-receipt.v1"] = (
        "ingredient-protein-write-receipt.v1"
    )
    ingredient_id: UUID
    stream_id: UUID
    review_id: UUID
    source_sequence: FeatureSequence
    command_hash: Sha256
    replayed: Annotated[bool, Field(strict=True)]
