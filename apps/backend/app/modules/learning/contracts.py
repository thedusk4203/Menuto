"""Immutable proposal-preview primitives; no consumption or learned behavior authority."""

import hashlib
import json
from collections import defaultdict
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, TypeAdapter, field_validator, model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, Sha256
from app.domain.snapshots import Horizon
from app.domain.units import Provenance
from app.modules.households.contracts import HouseholdMemberIdentity
from app.modules.planning.contracts import (
    BoundPlanProposalSnapshot,
    PlanProposalSnapshot,
    PlanWorkspaceDraft,
)
from app.modules.recipes.contracts import RecipeProvenance


def _json(value):
    # Lists are NOT generically sorted: only explicitly unordered collections below are sorted.
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _hash(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


class ExposurePreviewPolicy(Contract):
    contract_version: Literal["exposure-preview-policy.v1"] = "exposure-preview-policy.v1"
    policy_id: Identifier
    policy_version: Identifier
    provenance: Provenance
    window: Horizon
    fingerprint_kind: Literal["RECIPE_ID"] = "RECIPE_ID"


class ExposurePreviewRequest(Contract):
    contract_version: Literal["exposure-preview-request.v1"] = "exposure-preview-request.v1"
    household_id: UUID
    member_id: UUID
    plan_ids: tuple[UUID, ...]
    policy: ExposurePreviewPolicy

    @model_validator(mode="after")
    def unique_plans(self):
        if len(set(self.plan_ids)) != len(self.plan_ids):
            raise ValueError("Duplicate plan source")
        return self


class RecipeExposureIdentity(Contract):
    recipe_version_id: UUID
    recipe_id: UUID
    version: Annotated[int, Field(strict=True, gt=0)]
    review_status: Literal["DRAFT", "REVIEWED"]
    provenance: RecipeProvenance


class ProposalExposureSource(Contract):
    workspace: PlanWorkspaceDraft
    proposal: (
        Annotated[
            PlanProposalSnapshot | BoundPlanProposalSnapshot,
            Field(discriminator="contract_version"),
        ]
        | None
    )

    @model_validator(mode="after")
    def current_proposal(self):
        w, p = self.workspace, self.proposal
        if p is None:
            if w.latest_proposal_no != -1:
                raise ValueError("Missing current proposal is not an empty workspace")
        elif (p.graph.household_id, p.graph.plan_id, p.proposal_no) != (
            w.household_id,
            w.id,
            w.latest_proposal_no,
        ):
            raise ValueError("Proposal owner/frontier mismatch")
        return self


class ExposurePreviewSnapshot(Contract):
    contract_version: Literal["exposure-preview-source.v1"] = "exposure-preview-source.v1"
    coverage: Literal["SELECTED_PLAN_PROPOSAL_PREVIEWS_ONLY"] = (
        "SELECTED_PLAN_PROPOSAL_PREVIEWS_ONLY"
    )
    consumption_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    household_id: UUID
    member_id: UUID
    captured_at: AwareTime
    policy: ExposurePreviewPolicy
    members: tuple[HouseholdMemberIdentity, ...]
    sources: tuple[ProposalExposureSource, ...]
    recipes: tuple[RecipeExposureIdentity, ...]

    @model_validator(mode="after")
    def primitive_context(self):
        members = {m.member_id for m in self.members}
        recipes = {r.recipe_version_id for r in self.recipes}
        if (
            len(members) != len(self.members)
            or self.member_id not in members
            or any(m.household_id != self.household_id for m in self.members)
            or len({s.workspace.id for s in self.sources}) != len(self.sources)
            or len(recipes) != len(self.recipes)
            or self.policy.provenance.observed_at > self.captured_at
            or any(r.provenance.observed_at > self.captured_at for r in self.recipes)
        ):
            raise ValueError("Exposure source owner/identity/cutoff mismatch")
        used = set()
        for source in self.sources:
            if source.workspace.household_id != self.household_id:
                raise ValueError("Cross-household source")
            if source.proposal is None:
                continue
            p = source.proposal
            if p.created_at > self.captured_at:
                raise ValueError("Proposal was created after capture")
            if any(x.member_id not in members for meal in p.graph.meals for x in meal.participants):
                raise ValueError("Unknown participant")
            used.update(b.recipe_version_id for b in p.graph.batches)
        if used != recipes:
            raise ValueError("Recipe identity source coverage must be exact")
        return self

    def canonical_json(self):
        value = self.model_dump(mode="json")
        value["members"].sort(key=lambda m: m["member_id"])
        value["recipes"].sort(key=lambda r: r["recipe_version_id"])
        value["sources"].sort(key=lambda s: s["workspace"]["id"])
        for source, fact in zip(
            value["sources"], sorted(self.sources, key=lambda s: str(s.workspace.id)), strict=True
        ):
            if fact.proposal is not None:
                # Existing graph content() explicitly canonicalizes its unordered fact sets.
                source["proposal"]["graph"] = fact.proposal.graph.content()
        return _json(value)

    def fingerprint(self):
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()

    def frontier_hash(self):
        return _hash(
            {
                "household_id": str(self.household_id),
                "member_id": str(self.member_id),
                "selected_sources": [
                    {
                        "workspace": s.workspace.model_dump(mode="json"),
                        "proposal_id": str(s.proposal.id) if s.proposal else None,
                        "proposal_hash": s.proposal.graph_hash if s.proposal else None,
                    }
                    for s in sorted(self.sources, key=lambda s: str(s.workspace.id))
                ],
            }
        )


class ExposureAllocationSupport(Contract):
    allocation_node_id: UUID
    batch_node_id: UUID
    recipe_version_id: UUID


class RecipeExposurePreviewFact(Contract):
    status: Literal["PROVISIONAL"] = "PROVISIONAL"
    source_kind: Literal["PROPOSAL_PREVIEW"] = "PROPOSAL_PREVIEW"
    household_id: UUID
    member_id: UUID
    plan_id: UUID
    proposal_id: UUID
    proposal_hash: Sha256
    meal_node_id: UUID
    recipe_id: UUID
    scheduled_at: AwareTime
    support: tuple[ExposureAllocationSupport, ...] = Field(min_length=1)

    @field_validator("support")
    @classmethod
    def unique_support(cls, values):
        if len({v.allocation_node_id for v in values}) != len(values):
            raise ValueError("Duplicate allocation support")
        return tuple(sorted(values, key=lambda v: str(v.allocation_node_id)))

    def event_key(self):
        return _hash(
            {
                k: str(getattr(self, k))
                for k in ("household_id", "member_id", "plan_id", "meal_node_id", "recipe_id")
            }
        )


def derive_preview_facts(snapshot):
    identities = {r.recipe_version_id: r.recipe_id for r in snapshot.recipes}
    facts = []
    for source in snapshot.sources:
        if source.proposal is None:
            continue
        p = source.proposal
        batches = {b.node_id: b for b in p.graph.batches if b.status == "PLANNED"}
        for meal in p.graph.meals:
            if (
                meal.status != "PLANNED"
                or snapshot.member_id not in {x.member_id for x in meal.participants}
                or not snapshot.policy.window.start
                <= meal.scheduled_at
                < snapshot.policy.window.end
            ):
                continue
            grouped = defaultdict(list)
            for allocation in p.graph.allocations:
                batch = batches.get(allocation.batch_node_id)
                if (
                    allocation.status == "PLANNED"
                    and allocation.meal_node_id == meal.node_id
                    and batch is not None
                ):
                    grouped[identities[batch.recipe_version_id]].append(
                        ExposureAllocationSupport(
                            allocation_node_id=allocation.node_id,
                            batch_node_id=batch.node_id,
                            recipe_version_id=batch.recipe_version_id,
                        )
                    )
            for recipe_id, support in grouped.items():
                facts.append(
                    RecipeExposurePreviewFact(
                        household_id=snapshot.household_id,
                        member_id=snapshot.member_id,
                        plan_id=p.graph.plan_id,
                        proposal_id=p.id,
                        proposal_hash=p.graph_hash,
                        meal_node_id=meal.node_id,
                        recipe_id=recipe_id,
                        scheduled_at=meal.scheduled_at,
                        support=tuple(sorted(support, key=lambda s: str(s.allocation_node_id))),
                    )
                )
    return tuple(sorted(facts, key=lambda f: f.event_key()))


class RecipeRepeatEvidenceDraft(Contract):
    contract_version: Literal["recipe-repeat-evidence.v1-draft"] = "recipe-repeat-evidence.v1-draft"
    activation_ready: Literal[False] = False
    coverage: Literal["SELECTED_PLAN_PROPOSAL_PREVIEWS_ONLY"] = (
        "SELECTED_PLAN_PROPOSAL_PREVIEWS_ONLY"
    )
    consumption_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    absence_semantics: Literal["NOT_EVIDENCE_OF_NEVER_EXPOSED"] = "NOT_EVIDENCE_OF_NEVER_EXPOSED"
    source_hash: Sha256
    recipe_id: UUID
    facts: tuple[RecipeExposurePreviewFact, ...]

    @property
    def occurrence_count(self):
        return len(self.facts)

    @model_validator(mode="after")
    def exact_recipe(self):
        if any(f.recipe_id != self.recipe_id for f in self.facts) or len(
            {f.event_key() for f in self.facts}
        ) != len(self.facts):
            raise ValueError("Repeat evidence recipe/identity mismatch")
        return self


class RecipeExposurePreviewDraft(Contract):
    contract_version: Literal["recipe-exposure-preview.v1-draft"] = (
        "recipe-exposure-preview.v1-draft"
    )
    activation_ready: Literal[False] = False
    snapshot: ExposurePreviewSnapshot
    facts: tuple[RecipeExposurePreviewFact, ...]

    @model_validator(mode="after")
    def recompute(self):
        if self.facts != derive_preview_facts(self.snapshot):
            raise ValueError("Preview differs from captured primitives")
        return self

    def evidence_for(self, recipe_id: UUID, *, fingerprint_kind="RECIPE_ID"):
        if fingerprint_kind != "RECIPE_ID":
            raise ValueError("Unsupported exposure fingerprint")
        recipe_id = TypeAdapter(UUID).validate_python(recipe_id)
        return RecipeRepeatEvidenceDraft(
            source_hash=self.snapshot.fingerprint(),
            recipe_id=recipe_id,
            facts=tuple(f for f in self.facts if f.recipe_id == recipe_id),
        )

    def canonical_json(self):
        return _json(
            {
                "contract_version": self.contract_version,
                "activation_ready": False,
                "snapshot": json.loads(self.snapshot.canonical_json()),
                "facts": [f.model_dump(mode="json") for f in self.facts],
            }
        )
