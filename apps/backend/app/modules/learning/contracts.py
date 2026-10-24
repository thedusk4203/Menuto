"""Immutable proposal-preview primitives; no consumption or learned behavior authority."""

import hashlib
import json
from collections import defaultdict
from datetime import timedelta
from math import gcd
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


class RecipeCooldownPolicy(Contract):
    """Explicit configuration, not an empirical default or a utility weight."""

    contract_version: Literal["recipe-cooldown-policy.v1"] = "recipe-cooldown-policy.v1"
    policy_id: Identifier
    policy_version: Identifier
    provenance: Provenance
    duration_microseconds: Annotated[int, Field(strict=True, gt=0)]
    fingerprint_kind: Literal["RECIPE_ID"] = "RECIPE_ID"
    interval: Literal["START_INCLUSIVE_TARGET_EXCLUSIVE"] = "START_INCLUSIVE_TARGET_EXCLUSIVE"

    def fingerprint(self):
        return _hash(self.model_dump(mode="json"))


class RecipeCooldownQuery(Contract):
    contract_version: Literal["recipe-cooldown-query.v1"] = "recipe-cooldown-query.v1"
    household_id: UUID
    member_id: UUID
    plan_id: UUID
    proposal_id: UUID
    meal_node_id: UUID
    recipe_id: UUID


class RecipeCooldownInput(Contract):
    contract_version: Literal["recipe-cooldown-input.v1"] = "recipe-cooldown-input.v1"
    snapshot: ExposurePreviewSnapshot
    query: RecipeCooldownQuery
    policy: RecipeCooldownPolicy

    @model_validator(mode="after")
    def exact_context(self):
        _cooldown_context(self)
        return self

    def canonical_json(self):
        data = self.model_dump(mode="json")
        data["snapshot"] = json.loads(self.snapshot.canonical_json())
        return _json(data)

    def fingerprint(self):
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


class RecipeCooldownWitness(Contract):
    fact: RecipeExposurePreviewFact
    distance_microseconds: Annotated[int, Field(strict=True, gt=0)]


def _cooldown_context(subject):
    s, q = subject.snapshot, subject.query
    if (q.household_id, q.member_id) != (s.household_id, s.member_id):
        raise ValueError("Cooldown query household/member differs from capture")
    if len(s.sources) != 1 or s.sources[0].proposal is None:
        raise ValueError("Cooldown requires exactly one current selected proposal")
    p = s.sources[0].proposal
    if (q.plan_id, q.proposal_id) != (p.graph.plan_id, p.id):
        raise ValueError("Cooldown query plan/proposal differs from capture")
    if subject.policy.provenance.observed_at > s.captured_at:
        raise ValueError("Cooldown policy was observed after capture")
    meal = next((m for m in p.graph.meals if m.node_id == q.meal_node_id), None)
    if (
        meal is None
        or meal.status != "PLANNED"
        or q.member_id not in {m.member_id for m in meal.participants}
    ):
        raise ValueError("Cooldown target must be a planned participating meal")
    recipes = {r.recipe_version_id: r.recipe_id for r in s.recipes}
    batches = {
        b.node_id: b
        for b in p.graph.batches
        if b.status == "PLANNED" and recipes[b.recipe_version_id] == q.recipe_id
    }
    support = tuple(
        ExposureAllocationSupport(
            allocation_node_id=a.node_id,
            batch_node_id=a.batch_node_id,
            recipe_version_id=batches[a.batch_node_id].recipe_version_id,
        )
        for a in p.graph.allocations
        if a.meal_node_id == meal.node_id
        and a.status == "PLANNED"
        and a.servings > 0
        and a.batch_node_id in batches
    )
    if not support:
        raise ValueError("Target recipe requires a positive planned batch allocation")
    try:
        start = meal.scheduled_at - timedelta(microseconds=subject.policy.duration_microseconds)
    except OverflowError as error:
        raise ValueError("Cooldown lookback is outside representable time") from error
    if not s.policy.window.start <= start < meal.scheduled_at <= s.policy.window.end:
        raise ValueError("Captured window must contain the full cooldown lookback")
    target = RecipeExposurePreviewFact(
        household_id=s.household_id,
        member_id=s.member_id,
        plan_id=q.plan_id,
        proposal_id=p.id,
        proposal_hash=p.graph_hash,
        meal_node_id=meal.node_id,
        recipe_id=q.recipe_id,
        scheduled_at=meal.scheduled_at,
        support=support,
    )
    return target, start


def _cooldown_values(subject):
    target, start = _cooldown_context(subject)
    witnesses = []
    for fact in derive_preview_facts(subject.snapshot):
        if (
            fact.meal_node_id != target.meal_node_id
            and fact.recipe_id == target.recipe_id
            and start <= fact.scheduled_at < target.scheduled_at
        ):
            distance = target.scheduled_at - fact.scheduled_at
            # No float total_seconds() or rounding, including sub-second distances.
            micros = (distance.days * 86400 + distance.seconds) * 1000000 + distance.microseconds
            witnesses.append(RecipeCooldownWitness(fact=fact, distance_microseconds=micros))
    # This is an unordered witness set, not ordered execution history.
    witnesses = tuple(sorted(witnesses, key=lambda w: w.fact.event_key()))
    return dict(
        target=target,
        lookback_start=start,
        witnesses=witnesses,
        outcome="MATCH_IN_SELECTED_PROPOSAL" if witnesses else "NO_MATCH_IN_SELECTED_PROPOSAL",
    )


class RecipeCooldownAssessmentDraft(Contract):
    contract_version: Literal["recipe-cooldown-assessment.v1-draft"] = (
        "recipe-cooldown-assessment.v1-draft"
    )
    activation_ready: Literal[False] = False
    coverage: Literal["ONE_SELECTED_PROPOSAL_ONLY"] = "ONE_SELECTED_PROPOSAL_ONLY"
    absence_semantics: Literal["NOT_GLOBAL_COOLDOWN_SAFETY_OR_NEVER_EXPOSED"] = (
        "NOT_GLOBAL_COOLDOWN_SAFETY_OR_NEVER_EXPOSED"
    )
    accepted_schedule: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    confirmed_exposure: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    consumption_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    decay: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    novelty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    taste_fit: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    repeat_penalty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    subject: RecipeCooldownInput
    target: RecipeExposurePreviewFact
    lookback_start: AwareTime
    witnesses: tuple[RecipeCooldownWitness, ...]
    outcome: Literal["MATCH_IN_SELECTED_PROPOSAL", "NO_MATCH_IN_SELECTED_PROPOSAL"]

    @model_validator(mode="after")
    def recompute_cooldown(self):
        subject = RecipeCooldownInput.model_validate(self.subject.model_dump())
        for name, value in _cooldown_values(subject).items():
            if getattr(self, name) != value:
                raise ValueError("Cooldown result differs from captured primitives/policy")
        return self

    def canonical_json(self):
        data = self.model_dump(mode="json")
        data["subject"] = json.loads(self.subject.canonical_json())
        return _json(data)

    def fingerprint(self):
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


class RetentionMultiplier(Contract):
    """Exact reduced rational policy interpretation; never confidence or probability."""

    numerator: Annotated[int, Field(strict=True, ge=0)]
    denominator: Annotated[int, Field(strict=True, gt=0)]

    @model_validator(mode="after")
    def reduced_rational(self):
        if self.numerator > self.denominator:
            raise ValueError("Retention multiplier must be between zero and one")
        divisor = gcd(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", self.numerator // divisor)
        object.__setattr__(self, "denominator", self.denominator // divisor)
        return self


class RecipeDecayBand(Contract):
    ordinal: Annotated[int, Field(strict=True, ge=0)]
    lower_age_microseconds: Annotated[int, Field(strict=True, ge=0)]
    upper_age_microseconds: Annotated[int, Field(strict=True, gt=0)]
    retention_multiplier: RetentionMultiplier

    @model_validator(mode="after")
    def positive_span(self):
        if self.lower_age_microseconds >= self.upper_age_microseconds:
            raise ValueError("Decay band requires lower age below upper age")
        return self


class RecipeDecayPolicy(Contract):
    contract_version: Literal["recipe-decay-policy.v1"] = "recipe-decay-policy.v1"
    policy_id: Identifier
    policy_version: Identifier
    provenance: Provenance
    interpretation_mode: Literal["AS_OF_CAPTURE"] = "AS_OF_CAPTURE"
    fingerprint_kind: Literal["RECIPE_ID"] = "RECIPE_ID"
    source_kind: Literal["PROPOSAL_PREVIEW"] = "PROPOSAL_PREVIEW"
    band_interval: Literal["LOWER_EXCLUSIVE_UPPER_INCLUSIVE"] = "LOWER_EXCLUSIVE_UPPER_INCLUSIVE"
    bands: tuple[RecipeDecayBand, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_contiguous_decay(self):
        upper, prior = 0, None
        for ordinal, band in enumerate(self.bands):
            if band.ordinal != ordinal or band.lower_age_microseconds != upper:
                raise ValueError("Decay bands require explicit ordinal order and exact adjacency")
            current = band.retention_multiplier
            if prior is not None and (
                current.numerator * prior.denominator > prior.numerator * current.denominator
            ):
                raise ValueError("Retention must not increase with age")
            upper, prior = band.upper_age_microseconds, current
        return self

    def fingerprint(self):
        return _hash(self.model_dump(mode="json"))


class RecipeDecayInput(Contract):
    contract_version: Literal["recipe-decay-input.v1"] = "recipe-decay-input.v1"
    assessment: RecipeCooldownAssessmentDraft
    policy: RecipeDecayPolicy

    @field_validator("assessment", mode="before")
    @classmethod
    def reparse_assessment_instance(cls, value):
        # Reparse before frozen041B's own after-validator sees an untrusted instance.
        return value.model_dump() if isinstance(value, RecipeCooldownAssessmentDraft) else value

    @field_validator("policy", mode="before")
    @classmethod
    def reparse_policy_instance(cls, value):
        return value.model_dump() if isinstance(value, RecipeDecayPolicy) else value

    @model_validator(mode="after")
    def revalidated_as_of_capture(self):
        # Do not trust even a caller's model_copy/model_construct instance or witness list.
        assessment = RecipeCooldownAssessmentDraft.model_validate(self.assessment.model_dump())
        policy = RecipeDecayPolicy.model_validate(self.policy.model_dump())
        if policy.bands[-1].upper_age_microseconds != (
            assessment.subject.policy.duration_microseconds
        ):
            raise ValueError("This decay subset must exactly cover the frozen cooldown witnesses")
        if policy.provenance.observed_at > assessment.subject.snapshot.captured_at:
            raise ValueError("AS_OF_CAPTURE decay policy was observed after capture")
        object.__setattr__(self, "assessment", assessment)
        object.__setattr__(self, "policy", policy)
        return self

    def canonical_json(self):
        data = self.model_dump(mode="json")
        data["assessment"] = json.loads(self.assessment.canonical_json())
        return _json(data)

    def fingerprint(self):
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


class RecipeDecayTraceEntry(Contract):
    witness: RecipeCooldownWitness
    band: RecipeDecayBand


def _decay_entries(subject):
    entries = []
    for witness in subject.assessment.witnesses:
        age = witness.distance_microseconds
        band = next(
            (
                b
                for b in subject.policy.bands
                if b.lower_age_microseconds < age <= b.upper_age_microseconds
            ),
            None,
        )
        if band is None:
            raise ValueError("No explicit decay band for eligible witness age")
        entries.append(RecipeDecayTraceEntry(witness=witness, band=band))
    # Only unordered witness traces sort; policy bands retain authored ordinal order.
    return tuple(sorted(entries, key=lambda e: e.witness.fact.event_key()))


class RecipeDecayTraceDraft(Contract):
    contract_version: Literal["recipe-decay-trace.v1-draft"] = "recipe-decay-trace.v1-draft"
    activation_ready: Literal[False] = False
    interpretation_mode: Literal["AS_OF_CAPTURE"] = "AS_OF_CAPTURE"
    coverage: Literal["ONE_SELECTED_PROPOSAL_ONLY"] = "ONE_SELECTED_PROPOSAL_ONLY"
    absence_semantics: Literal["NO_GLOBAL_PENALTY_OR_NOVELTY_CONCLUSION"] = (
        "NO_GLOBAL_PENALTY_OR_NOVELTY_CONCLUSION"
    )
    repeat_penalty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    novelty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    taste_fit: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    confirmed_exposure: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    consumption_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    accepted_schedule: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    global_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    subject: RecipeDecayInput
    entries: tuple[RecipeDecayTraceEntry, ...]

    @model_validator(mode="after")
    def recompute_trace(self):
        subject = RecipeDecayInput.model_validate(self.subject.model_dump())
        if self.entries != _decay_entries(subject):
            raise ValueError("Decay trace differs from revalidated source witnesses/policy")
        object.__setattr__(self, "subject", subject)
        return self

    def canonical_json(self):
        data = self.model_dump(mode="json")
        data["subject"] = json.loads(self.subject.canonical_json())
        return _json(data)

    def fingerprint(self):
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


class RepeatPenaltyAmount(Contract):
    """Exact policy units, unbounded above; neither material nor probability."""

    numerator: Annotated[int, Field(strict=True, ge=0)]
    denominator: Annotated[int, Field(strict=True, gt=0)]
    unit: Literal["POLICY_REPEAT_PENALTY_UNITS"] = "POLICY_REPEAT_PENALTY_UNITS"

    @model_validator(mode="after")
    def reduced_amount(self):
        divisor = gcd(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", self.numerator // divisor)
        object.__setattr__(self, "denominator", self.denominator // divisor)
        return self


class RecipeRepeatPenaltyPolicy(Contract):
    contract_version: Literal["recipe-repeat-penalty-policy.v1"] = "recipe-repeat-penalty-policy.v1"
    policy_id: Identifier
    policy_version: Identifier
    provenance: Provenance
    operator: Literal["SUM_RETAINED_OCCURRENCES"]
    unit_penalty: RepeatPenaltyAmount
    interpretation_mode: Literal["AS_OF_CAPTURE"] = "AS_OF_CAPTURE"
    fingerprint_kind: Literal["RECIPE_ID"] = "RECIPE_ID"
    source_kind: Literal["PROPOSAL_PREVIEW"] = "PROPOSAL_PREVIEW"

    @model_validator(mode="after")
    def positive_unit_penalty(self):
        if self.unit_penalty.numerator == 0:
            raise ValueError("Explicit unit penalty must be positive")
        return self

    def fingerprint(self):
        return _hash(self.model_dump(mode="json"))


class RecipeRepeatPenaltyInput(Contract):
    contract_version: Literal["recipe-repeat-penalty-input.v1"] = "recipe-repeat-penalty-input.v1"
    trace: RecipeDecayTraceDraft
    policy: RecipeRepeatPenaltyPolicy

    @field_validator("trace", "policy", mode="before")
    @classmethod
    def reparse_instances(cls, value):
        if isinstance(value, (RecipeDecayTraceDraft, RecipeRepeatPenaltyPolicy)):
            return value.model_dump()
        return value

    @model_validator(mode="after")
    def revalidated_as_of_capture(self):
        trace = RecipeDecayTraceDraft.model_validate(self.trace.model_dump())
        policy = RecipeRepeatPenaltyPolicy.model_validate(self.policy.model_dump())
        if policy.provenance.observed_at > trace.subject.assessment.subject.snapshot.captured_at:
            raise ValueError("AS_OF_CAPTURE repeat penalty policy was observed after capture")
        object.__setattr__(self, "trace", trace)
        object.__setattr__(self, "policy", policy)
        return self

    def canonical_json(self):
        data = self.model_dump(mode="json")
        data["trace"] = json.loads(self.trace.canonical_json())
        return _json(data)

    def fingerprint(self):
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


class RecipeRepeatPenaltyContribution(Contract):
    source: RecipeDecayTraceEntry
    unit_penalty: RepeatPenaltyAmount
    contribution: RepeatPenaltyAmount


def _repeat_penalty_values(subject):
    unit = subject.policy.unit_penalty
    entries = []
    total_n, total_d = 0, 1
    for source in subject.trace.entries:
        retention = source.band.retention_multiplier
        amount = RepeatPenaltyAmount(
            numerator=unit.numerator * retention.numerator,
            denominator=unit.denominator * retention.denominator,
        )
        entries.append(
            RecipeRepeatPenaltyContribution(
                source=source, unit_penalty=unit, contribution=amount
            )
        )
        total_n, total_d = (
            total_n * amount.denominator + amount.numerator * total_d,
            total_d * amount.denominator,
        )
        divisor = gcd(total_n, total_d)
        total_n, total_d = total_n // divisor, total_d // divisor
    return dict(
        contributions=tuple(entries),
        outcome="INTERPRETED_IN_SELECTED_PROPOSAL" if entries else "NO_MATCH_IN_SELECTED_PROPOSAL",
        proposal_local_repeat_penalty=(
            RepeatPenaltyAmount(numerator=total_n, denominator=total_d) if entries else None
        ),
    )


class RecipeRepeatPenaltyDraft(Contract):
    contract_version: Literal["recipe-repeat-penalty.v1-draft"] = "recipe-repeat-penalty.v1-draft"
    activation_ready: Literal[False] = False
    interpretation_mode: Literal["AS_OF_CAPTURE"] = "AS_OF_CAPTURE"
    coverage: Literal["ONE_SELECTED_PROPOSAL_ONLY"] = "ONE_SELECTED_PROPOSAL_ONLY"
    absence_semantics: Literal["NO_GLOBAL_PENALTY_OR_NOVELTY_CONCLUSION"] = (
        "NO_GLOBAL_PENALTY_OR_NOVELTY_CONCLUSION"
    )
    repeat_penalty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    novelty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    taste_fit: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    confirmed_exposure: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    consumption_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    accepted_schedule: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    global_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    subject: RecipeRepeatPenaltyInput
    contributions: tuple[RecipeRepeatPenaltyContribution, ...]
    outcome: Literal["INTERPRETED_IN_SELECTED_PROPOSAL", "NO_MATCH_IN_SELECTED_PROPOSAL"]
    proposal_local_repeat_penalty: RepeatPenaltyAmount | None

    @field_validator("subject", mode="before")
    @classmethod
    def reparse_subject_instance(cls, value):
        return value.model_dump() if isinstance(value, RecipeRepeatPenaltyInput) else value

    @model_validator(mode="after")
    def recompute_interpretation(self):
        subject = RecipeRepeatPenaltyInput.model_validate(self.subject.model_dump())
        for name, value in _repeat_penalty_values(subject).items():
            if getattr(self, name) != value:
                raise ValueError("Repeat penalty differs from revalidated source/policy")
        object.__setattr__(self, "subject", subject)
        return self

    def canonical_json(self):
        data = self.model_dump(mode="json")
        data["subject"] = json.loads(self.subject.canonical_json())
        return _json(data)

    def fingerprint(self):
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()
