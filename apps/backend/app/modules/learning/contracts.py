"""Immutable proposal-preview primitives; no consumption or learned behavior authority."""

import hashlib
import json
from collections import defaultdict
from datetime import timedelta
from math import gcd
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, TypeAdapter, field_validator, model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, Sha256
from app.domain.feature_identity import canonical, canonical_bytes, identity_hash, unique_sorted
from app.domain.snapshots import Horizon
from app.domain.units import Provenance
from app.modules.catalog.contracts import FeatureFrontier
from app.modules.households.contracts import HouseholdMemberIdentity
from app.modules.planning.contracts import (
    BoundPlanProposalSnapshot,
    CulinaryFeatureDiscoveryDraft,
    MealParticipantIntent,
    PlanProposalSnapshot,
    PlanWorkspaceDraft,
)
from app.modules.recipes.contracts import (
    FeatureDimension,
    FeatureDimensionDiscovery,
    FeatureTermQuery,
    FeatureTermResolution,
    RecipeProvenance,
    resolve_feature_input,
)


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


# MTR-041E is additive. The frozen Recipe-ID source/policy algorithms are unchanged.


class FeatureExposurePreviewRequest(Contract):
    contract_version: Literal["feature-exposure-request.v1"] = "feature-exposure-request.v1"
    household_id: UUID
    plan_id: UUID
    proposal_id: UUID
    proposal_hash: Sha256
    selected_member_ids: Annotated[tuple[UUID, ...], Field(min_length=1)]
    requested_dimensions: Annotated[tuple[FeatureDimension, ...], Field(min_length=1)]
    recipe_eligibility_policy: ExposurePreviewPolicy

    @model_validator(mode="after")
    def sets(self):
        for name in ("selected_member_ids", "requested_dimensions"):
            object.__setattr__(self, name, unique_sorted(getattr(self, name)))
        return self


class RecipeExposureFrontier(Contract):
    dimension: Literal["METHOD", "FLAVOR"]
    recipe_frontier: FeatureFrontier


class MainProteinExposureFrontier(Contract):
    dimension: Literal["MAIN_PROTEIN"] = "MAIN_PROTEIN"
    recipe_frontier: FeatureFrontier
    catalog_frontier: FeatureFrontier


def _feature_proposal(proposal):
    return proposal.model_dump(mode="json") | {"graph": proposal.graph.content()}


def _feature_member_source(source, *, audit=True):
    data = json.loads(source.canonical_json())
    if not audit:
        del data["captured_at"]
    return data


def _feature_classification_source(source, *, audit=True):
    data = json.loads(source.subject.canonical_bytes())
    if not audit:
        del data["evaluation"]["captured_at"]
    # Frozen discovery fingerprint includes the audit clock; don't leak it into cut digests.
    result = dict(subject=data, dimensions=canonical(source.dimensions))
    if audit:
        result["fingerprint"] = source.fingerprint
    return result


def _feature_eligible_rows(snapshot):
    """Flatten every allocation support, including versions grouped by frozen041A Recipe ID."""
    for member in snapshot.member_sources:
        proposal = member.sources[0].proposal
        meals = {m.node_id: m for m in proposal.graph.meals}
        for fact in derive_preview_facts(member):
            meal = meals[fact.meal_node_id]
            participant = next(p for p in meal.participants if p.member_id == member.member_id)
            for support in fact.support:
                yield fact, support, participant


class FeatureExposureSourceSnapshotDraft(Contract):
    contract_version: Literal["feature-exposure-source.v1-draft"] = (
        "feature-exposure-source.v1-draft"
    )
    activation_ready: Literal[False] = False
    request: FeatureExposurePreviewRequest
    capture_completed_at: AwareTime
    member_sources: Annotated[tuple[ExposurePreviewSnapshot, ...], Field(min_length=1)]
    classification_sources: tuple[CulinaryFeatureDiscoveryDraft, ...]
    frontiers: tuple[
        Annotated[
            RecipeExposureFrontier | MainProteinExposureFrontier, Field(discriminator="dimension")
        ],
        ...,
    ]

    @model_validator(mode="after")
    def coherent_primitives(self):
        # Reparse recursively: constructed/copied nested objects are not trusted.
        q = FeatureExposurePreviewRequest.model_validate(self.request.model_dump())
        members = unique_sorted(
            tuple(
                ExposurePreviewSnapshot.model_validate(m.model_dump()) for m in self.member_sources
            ),
            key=lambda m: str(m.member_id),
        )
        sources = unique_sorted(
            tuple(
                CulinaryFeatureDiscoveryDraft.model_validate(s.model_dump())
                for s in self.classification_sources
            ),
            key=lambda s: (
                str(s.subject.request.batch_node_id),
                s.subject.request.requested_dimensions,
            ),
        )
        frontiers = unique_sorted(self.frontiers, key=lambda f: f.dimension)
        if (
            {m.member_id for m in members} != set(q.selected_member_ids)
            or {f.dimension for f in frontiers} != set(q.requested_dimensions)
            or len({f.recipe_frontier for f in frontiers}) != 1
        ):
            raise ValueError("Feature member/dimension/frontier manifest mismatch")
        object.__setattr__(self, "request", q)
        object.__setattr__(self, "member_sources", members)
        object.__setattr__(self, "classification_sources", sources)
        object.__setattr__(self, "frontiers", frontiers)
        first = members[0]
        reference = _feature_member_source(first, audit=False)
        reference.pop("member_id")
        for m in members:
            common = _feature_member_source(m, audit=False)
            common.pop("member_id")
            if (
                common != reference
                or m.household_id != q.household_id
                or m.policy != q.recipe_eligibility_policy
                or len(m.sources) != 1
                or m.captured_at > self.capture_completed_at
            ):
                raise ValueError("Conflicting feature member source cut")
        owner = first.sources[0]
        p = owner.proposal
        if p is None or (owner.workspace.id, p.id, p.graph_hash) != (
            q.plan_id,
            q.proposal_id,
            q.proposal_hash,
        ):
            raise ValueError("Selected current proposal required")
        expected = {
            (s.batch_node_id, d)
            for _, s, _ in _feature_eligible_rows(self)
            for d in q.requested_dimensions
        }
        actual = {
            (s.subject.request.batch_node_id, s.subject.request.requested_dimensions[0])
            for s in sources
            if len(s.subject.request.requested_dimensions) == 1
        }
        if len(actual) != len(sources) or actual != expected:
            raise ValueError("Exact eligible batch/singleton-dimension manifest required")
        identities = {r.recipe_version_id: r for r in first.recipes}
        cuts = {f.dimension: f for f in frontiers}
        seen = {}

        def consistent(key, value):
            encoded = canonical_bytes(value)
            if key in seen and seen[key] != encoded:
                raise ValueError("Conflicting classification primitive/source cut")
            seen[key] = encoded

        for s in sources:
            child, e = s.subject, s.subject.evaluation
            d = child.request.requested_dimensions[0]
            frontier = cuts[d]
            recipe = e.recipe
            identity = RecipeExposureIdentity(
                recipe_version_id=recipe.id,
                recipe_id=recipe.recipe.id,
                version=recipe.version,
                review_status=recipe.review_status,
                provenance=recipe.provenance,
            )
            if (
                child.workspace != owner.workspace
                or _feature_proposal(child.proposal) != _feature_proposal(p)
                or e.captured_at > self.capture_completed_at
                or identity != identities.get(recipe.id)
                or e.sources.recipe_frontier != frontier.recipe_frontier
                or (d == "MAIN_PROTEIN" and e.sources.catalog_frontier != frontier.catalog_frontier)
            ):
                raise ValueError("Conflicting classification owner/recipe/frontier/cutoff")
            consistent(("recipe", recipe.id), recipe)
            consistent(("scopes", recipe.id, d), e.sources.scopes)
            for t in e.sources.terms:
                consistent(("term", t.id), t)
            for scope in e.sources.scopes:
                consistent(("scope", scope.id), scope)
                for review in scope.reviews:
                    consistent(("recipe_sequence", review.source_sequence), review)
            for stream in getattr(e.sources, "catalog_streams", ()):
                consistent(("ingredient", stream.ingredient_id), stream)
                for review in stream.reviews:
                    consistent(("catalog_sequence", review.source_sequence), review)
        return self

    def content(self, *, dimension=None):
        """An explicit diagnostic projection; only capture clocks/other dimensions are excluded."""
        audit = dimension is None
        data = canonical(self)
        data["member_sources"] = [
            _feature_member_source(m, audit=audit) for m in self.member_sources
        ]
        sources = self.classification_sources
        if not audit:
            if dimension not in self.request.requested_dimensions:
                raise ValueError("Uncaptured feature dimension")
            data.pop("capture_completed_at")
            data["contract_version"] = "feature-exposure-evidence-cut.v1-diagnostic"
            data["request"]["requested_dimensions"] = [dimension]
            sources = tuple(
                s for s in sources if s.subject.request.requested_dimensions == (dimension,)
            )
            data["frontiers"] = [canonical(f) for f in self.frontiers if f.dimension == dimension]
        data["classification_sources"] = [
            _feature_classification_source(s, audit=audit) for s in sources
        ]
        return data

    def canonical_json(self):
        return canonical_bytes(self.content()).decode()

    def fingerprint(self):
        return identity_hash(self.content())


class FeatureExposureSourceKey(Contract):
    batch_node_id: UUID
    dimension: FeatureDimension


class FeatureExposureAssignmentRef(Contract):
    review_id: UUID
    term_id: UUID


class FeatureExposureSupportWitness(Contract):
    participant: MealParticipantIntent
    recipe_event_key: Sha256
    allocation_node_id: UUID
    batch_node_id: UUID
    recipe_id: UUID
    recipe_version_id: UUID
    classification_source: FeatureExposureSourceKey
    subject_hash: Sha256
    discovery_hash: Sha256
    applicability_id: UUID
    assignment: FeatureExposureAssignmentRef


class FeatureExposurePreviewFact(Contract):
    contract_version: Literal["feature-exposure-fact.v1-draft"] = "feature-exposure-fact.v1-draft"
    activation_ready: Literal[False] = False
    status: Literal["PROVISIONAL"] = "PROVISIONAL"
    source_kind: Literal["PROPOSAL_PREVIEW"] = "PROPOSAL_PREVIEW"
    household_id: UUID
    member_id: UUID
    plan_id: UUID
    meal_node_id: UUID
    dimension: FeatureDimension
    feature_term_id: UUID
    proposal_id: UUID
    proposal_hash: Sha256
    scheduled_at: AwareTime
    support: Annotated[tuple[FeatureExposureSupportWitness, ...], Field(min_length=1)]

    @field_validator("support")
    @classmethod
    def witnesses(cls, values):
        return unique_sorted(values, key=lambda w: str(w.allocation_node_id))

    @model_validator(mode="after")
    def support_owners(self):
        if any(
            w.participant.member_id != self.member_id
            or w.classification_source.batch_node_id != w.batch_node_id
            or w.classification_source.dimension != self.dimension
            or w.assignment.term_id != self.feature_term_id
            for w in self.support
        ):
            raise ValueError("Feature support participant/batch/dimension/assignment mismatch")
        return self

    def event_key(self):
        return identity_hash(
            dict(
                contract_version="feature-exposure-event-key.v1",
                **{
                    k: getattr(self, k)
                    for k in (
                        "household_id",
                        "member_id",
                        "plan_id",
                        "meal_node_id",
                        "dimension",
                        "feature_term_id",
                    )
                },
            )
        )


class FeatureExposureCoverageDiagnostic(Contract):
    household_id: UUID
    member_id: UUID
    plan_id: UUID
    meal_node_id: UUID
    classification_source: FeatureExposureSourceKey
    allocation_node_ids: Annotated[tuple[UUID, ...], Field(min_length=1)]
    discovery: FeatureDimensionDiscovery


class FeatureExposureEvidenceCut(Contract):
    contract_version: Literal["feature-exposure-cut.v1-diagnostic"] = (
        "feature-exposure-cut.v1-diagnostic"
    )
    dimension: FeatureDimension
    digest: Sha256
    authority: Literal["DIAGNOSTIC_ONLY_NOT_LIVENESS_OR_AUTHORIZATION"] = (
        "DIAGNOSTIC_ONLY_NOT_LIVENESS_OR_AUTHORIZATION"
    )


def _feature_exposure_values(snapshot):
    sources = {
        (s.subject.request.batch_node_id, s.subject.request.requested_dimensions[0]): s
        for s in snapshot.classification_sources
    }
    grouped, diagnostics = {}, {}
    for fact, support, participant in _feature_eligible_rows(snapshot):
        for dimension in snapshot.request.requested_dimensions:
            source = sources[support.batch_node_id, dimension]
            discovery = source.dimensions[0]
            key = FeatureExposureSourceKey(batch_node_id=support.batch_node_id, dimension=dimension)
            dk = (fact.member_id, fact.meal_node_id, support.batch_node_id, dimension)
            if dk not in diagnostics:
                diagnostics[dk] = dict(
                    household_id=fact.household_id,
                    member_id=fact.member_id,
                    plan_id=fact.plan_id,
                    meal_node_id=fact.meal_node_id,
                    classification_source=key,
                    discovery=discovery,
                    allocation_node_ids=set(),
                )
            diagnostics[dk]["allocation_node_ids"].add(support.allocation_node_id)
            for term in discovery.positive_term_ids:
                if discovery.state != "ASSIGNED":
                    raise ValueError("Positive exposure requires reviewed assignment")
                ek = (fact.member_id, fact.meal_node_id, dimension, term)
                if ek not in grouped:
                    grouped[ek] = dict(
                        household_id=fact.household_id,
                        member_id=fact.member_id,
                        plan_id=fact.plan_id,
                        meal_node_id=fact.meal_node_id,
                        dimension=dimension,
                        feature_term_id=term,
                        proposal_id=fact.proposal_id,
                        proposal_hash=fact.proposal_hash,
                        scheduled_at=fact.scheduled_at,
                        support=[],
                    )
                grouped[ek]["support"].append(
                    FeatureExposureSupportWitness(
                        participant=participant,
                        recipe_event_key=fact.event_key(),
                        allocation_node_id=support.allocation_node_id,
                        batch_node_id=support.batch_node_id,
                        recipe_id=fact.recipe_id,
                        recipe_version_id=support.recipe_version_id,
                        classification_source=key,
                        subject_hash=source.subject.fingerprint,
                        discovery_hash=source.fingerprint,
                        applicability_id=discovery.applicability_id,
                        assignment=FeatureExposureAssignmentRef(
                            review_id=discovery.review_id, term_id=term
                        ),
                    )
                )
    events = tuple(
        sorted(
            (FeatureExposurePreviewFact(**v) for v in grouped.values()), key=lambda f: f.event_key()
        )
    )
    rows = tuple(
        FeatureExposureCoverageDiagnostic(
            **(v | {"allocation_node_ids": tuple(sorted(v["allocation_node_ids"], key=str))})
        )
        for _, v in sorted(diagnostics.items(), key=lambda kv: tuple(map(str, kv[0])))
    )
    cuts = tuple(
        FeatureExposureEvidenceCut(dimension=d, digest=identity_hash(snapshot.content(dimension=d)))
        for d in snapshot.request.requested_dimensions
    )
    return dict(events=events, diagnostics=rows, evidence_cuts=cuts)


class FeatureExposurePreviewDraft(Contract):
    contract_version: Literal["feature-exposure-preview.v1-draft"] = (
        "feature-exposure-preview.v1-draft"
    )
    activation_ready: Literal[False] = False
    coverage: Literal["SELECTED_PROPOSAL_FEATURE_PREVIEW_ONLY"] = (
        "SELECTED_PROPOSAL_FEATURE_PREVIEW_ONLY"
    )
    absence_semantics: Literal["NOT_EVIDENCE_OF_NEVER_EXPOSED_OR_GLOBAL_FEATURE_ABSENCE"] = (
        "NOT_EVIDENCE_OF_NEVER_EXPOSED_OR_GLOBAL_FEATURE_ABSENCE"
    )
    accepted_schedule: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    confirmed_exposure: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    consumption_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    durable_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    cross_horizon_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    feature_cooldown: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    feature_decay: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    repeat_penalty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    novelty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    taste_fit: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    snapshot: FeatureExposureSourceSnapshotDraft
    events: tuple[FeatureExposurePreviewFact, ...]
    diagnostics: tuple[FeatureExposureCoverageDiagnostic, ...]
    evidence_cuts: tuple[FeatureExposureEvidenceCut, ...]

    @model_validator(mode="after")
    def recompute(self):
        snapshot = FeatureExposureSourceSnapshotDraft.model_validate(self.snapshot.model_dump())
        expected = _feature_exposure_values(snapshot)
        for name, value in expected.items():
            if getattr(self, name) != value:
                raise ValueError("Feature exposure differs from revalidated source primitives")
        object.__setattr__(self, "snapshot", snapshot)
        return self

    def canonical_json(self):
        data = canonical(self)
        data["snapshot"] = self.snapshot.content()
        return canonical_bytes(data).decode()

    def fingerprint(self):
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


# MTR-041F: separate feature contracts; frozen Recipe-ID and 041E shapes stay unchanged.
def _feature_repeat_wire(value):
    if isinstance(value, Contract):
        value = value.model_dump()
    if isinstance(value, dict):
        return {k: _feature_repeat_wire(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_feature_repeat_wire(v) for v in value)
    return value


class _FeatureRepeatContract(Contract):
    model_config = ConfigDict(revalidate_instances="always")

    @model_validator(mode="before")
    @classmethod
    def recursive_wire(cls, value):
        return _feature_repeat_wire(value)

    def canonical_json(self):
        return canonical_bytes(feature_repeat_content(self)).decode()

    def fingerprint(self):
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


class FeatureRepeatQuery(_FeatureRepeatContract):
    contract_version: Literal["feature-repeat-query.v1"] = "feature-repeat-query.v1"
    household_id: UUID
    member_id: UUID
    plan_id: UUID
    proposal_id: UUID
    proposal_hash: Sha256
    meal_node_id: UUID
    dimension: FeatureDimension
    feature_term_id: UUID


class FeatureRetentionMultiplier(_FeatureRepeatContract):
    """Exact policy retention, not probability or statistical confidence."""

    numerator: Annotated[int, Field(strict=True, ge=0)]
    denominator: Annotated[int, Field(strict=True, gt=0)]

    @model_validator(mode="after")
    def reduced(self):
        if self.numerator > self.denominator:
            raise ValueError("Feature retention must be in [0,1]")
        divisor = gcd(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", self.numerator // divisor)
        object.__setattr__(self, "denominator", self.denominator // divisor)
        return self


class FeatureRepeatPenaltyAmount(_FeatureRepeatContract):
    numerator: Annotated[int, Field(strict=True, ge=0)]
    denominator: Annotated[int, Field(strict=True, gt=0)]
    unit: Literal["POLICY_FEATURE_REPEAT_PENALTY_UNITS"] = "POLICY_FEATURE_REPEAT_PENALTY_UNITS"

    @model_validator(mode="after")
    def reduced(self):
        divisor = gcd(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", self.numerator // divisor)
        object.__setattr__(self, "denominator", self.denominator // divisor)
        return self


class _FeatureTermPolicy(_FeatureRepeatContract):
    policy_id: Identifier
    policy_version: Identifier
    provenance: Provenance
    dimension: FeatureDimension
    feature_term_id: UUID
    fingerprint_kind: Literal["REVIEWED_FEATURE_TERM_ID"] = "REVIEWED_FEATURE_TERM_ID"
    source_kind: Literal["PROPOSAL_PREVIEW"] = "PROPOSAL_PREVIEW"
    interpretation_mode: Literal["AS_OF_CAPTURE"] = "AS_OF_CAPTURE"

    @model_validator(mode="after")
    def reviewed_policy(self):
        if self.provenance.kind not in {"USER", "REVIEWED_REFERENCE"}:
            raise ValueError("Feature policy requires USER or REVIEWED_REFERENCE provenance")
        return self


class FeatureCooldownPolicy(_FeatureTermPolicy):
    contract_version: Literal["feature-cooldown-policy.v1"] = "feature-cooldown-policy.v1"
    duration_microseconds: Annotated[int, Field(strict=True, gt=0)]
    interval: Literal["START_INCLUSIVE_TARGET_EXCLUSIVE"] = "START_INCLUSIVE_TARGET_EXCLUSIVE"


class FeatureDecayBand(_FeatureRepeatContract):
    ordinal: Annotated[int, Field(strict=True, ge=0)]
    lower_age_microseconds: Annotated[int, Field(strict=True, ge=0)]
    upper_age_microseconds: Annotated[int, Field(strict=True, gt=0)]
    retention_multiplier: FeatureRetentionMultiplier

    @model_validator(mode="after")
    def positive_span(self):
        if self.lower_age_microseconds >= self.upper_age_microseconds:
            raise ValueError("Feature decay band requires a positive span")
        return self


class FeatureDecayPolicy(_FeatureTermPolicy):
    contract_version: Literal["feature-decay-policy.v1"] = "feature-decay-policy.v1"
    band_interval: Literal["LOWER_EXCLUSIVE_UPPER_INCLUSIVE"] = "LOWER_EXCLUSIVE_UPPER_INCLUSIVE"
    bands: Annotated[tuple[FeatureDecayBand, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def contiguous_monotone(self):
        upper, previous = 0, None
        for ordinal, band in enumerate(self.bands):
            if band.ordinal != ordinal or band.lower_age_microseconds != upper:
                raise ValueError("Feature decay requires authored ordinals and contiguous bands")
            current = band.retention_multiplier
            if previous is not None and (
                current.numerator * previous.denominator
                > previous.numerator * current.denominator
            ):
                raise ValueError("Feature retention must not increase with age")
            upper, previous = band.upper_age_microseconds, current
        return self


class FeatureRepeatPenaltyPolicy(_FeatureTermPolicy):
    contract_version: Literal["feature-repeat-penalty-policy.v1"] = (
        "feature-repeat-penalty-policy.v1"
    )
    operator: Literal["SUM_RETAINED_TERM_OCCURRENCES"]
    unit_penalty: FeatureRepeatPenaltyAmount

    @model_validator(mode="after")
    def positive_unit(self):
        if self.unit_penalty.numerator == 0:
            raise ValueError("Feature unit penalty must be explicitly positive")
        return self


class FeatureCooldownInput(_FeatureRepeatContract):
    contract_version: Literal["feature-cooldown-input.v1"] = "feature-cooldown-input.v1"
    preview: FeatureExposurePreviewDraft
    query: FeatureRepeatQuery
    policy: FeatureCooldownPolicy

    @field_validator("preview", mode="before")
    @classmethod
    def canonical_preview(cls, value):
        return reparse_feature_preview(value)

    @model_validator(mode="after")
    def captured_context(self):
        feature_cooldown_context(self)
        return self


class FeatureTermCoverageCell(_FeatureRepeatContract):
    diagnostic: FeatureExposureCoverageDiagnostic
    resolution: FeatureTermResolution

    @field_validator("diagnostic", mode="before")
    @classmethod
    def canonical_diagnostic(cls, value):
        return _feature_repeat_diagnostic(value)

    @model_validator(mode="after")
    def dimension_matches(self):
        if self.diagnostic.classification_source.dimension != self.resolution.dimension:
            raise ValueError("Feature cell dimension mismatch")
        return self


class FeatureMealTermOccurrence(_FeatureRepeatContract):
    meal_node_id: UUID
    scheduled_at: AwareTime
    dimension: FeatureDimension
    feature_term_id: UUID
    cells: Annotated[tuple[FeatureTermCoverageCell, ...], Field(min_length=1)]
    state: Literal["PRESENT", "REVIEWED_ABSENT", "UNRESOLVED"]
    event: FeatureExposurePreviewFact | None

    @field_validator("cells")
    @classmethod
    def unordered_cells(cls, values):
        return unique_sorted(
            values, key=lambda c: str(c.diagnostic.classification_source.batch_node_id)
        )


class FeatureCooldownWitness(_FeatureRepeatContract):
    fact: FeatureExposurePreviewFact
    distance_microseconds: Annotated[int, Field(strict=True, gt=0)]


class _FeatureRepeatResult(_FeatureRepeatContract):
    coverage: Literal["ONE_SELECTED_PROPOSAL_EXACT_FEATURE_TERM_ONLY"] = (
        "ONE_SELECTED_PROPOSAL_EXACT_FEATURE_TERM_ONLY"
    )
    source_kind: Literal["PROPOSAL_PREVIEW"] = "PROPOSAL_PREVIEW"
    interpretation_mode: Literal["AS_OF_CAPTURE"] = "AS_OF_CAPTURE"
    absence_semantics: Literal["NO_GLOBAL_REPEAT_NOVELTY_OR_NEVER_EXPOSED_CONCLUSION"] = (
        "NO_GLOBAL_REPEAT_NOVELTY_OR_NEVER_EXPOSED_CONCLUSION"
    )
    accepted_schedule: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    confirmed_exposure: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    consumption_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    durable_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    cross_horizon_history: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    global_repeat_penalty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    novelty: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    taste_fit: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    member_behavior_profile: Literal["NOT_MODIFIED"] = "NOT_MODIFIED"
    cross_dimension_aggregation: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False
    source_preview_fingerprint: Sha256
    dimension_evidence_cut_digest: Sha256
    outcome: Literal[
        "MATCH_IN_SELECTED_PROPOSAL",
        "UNRESOLVED_IN_SELECTED_PROPOSAL",
        "NO_MATCH_IN_SELECTED_PROPOSAL",
    ]
    occurrence_resolution: Literal[
        "ALL_QUERIED_TERM_OCCURRENCES_DECIDABLE", "HAS_UNRESOLVED_MEALS", "NO_ELIGIBLE_PRIOR_MEALS"
    ]
    unresolved_meal_ids: tuple[UUID, ...]

    @field_validator("unresolved_meal_ids")
    @classmethod
    def unordered_unknowns(cls, values):
        return unique_sorted(values)


class FeatureCooldownAssessmentDraft(_FeatureRepeatResult):
    contract_version: Literal["feature-cooldown-assessment.v1-draft"] = (
        "feature-cooldown-assessment.v1-draft"
    )
    subject: FeatureCooldownInput
    target: FeatureExposurePreviewFact
    lookback_start: AwareTime
    policy_cutoff: AwareTime
    occurrences: tuple[FeatureMealTermOccurrence, ...]
    witnesses: tuple[FeatureCooldownWitness, ...]

    @field_validator("occurrences")
    @classmethod
    def unordered_occurrences(cls, values):
        return unique_sorted(values, key=lambda o: str(o.meal_node_id))

    @field_validator("witnesses")
    @classmethod
    def unordered_witnesses(cls, values):
        return unique_sorted(values, key=lambda w: w.fact.event_key())

    @model_validator(mode="after")
    def recompute(self):
        verify_feature_result(self, feature_cooldown_values(self.subject))
        return self


class FeatureDecayInput(_FeatureRepeatContract):
    contract_version: Literal["feature-decay-input.v1"] = "feature-decay-input.v1"
    assessment: FeatureCooldownAssessmentDraft
    policy: FeatureDecayPolicy

    @model_validator(mode="after")
    def matching_policy(self):
        verify_feature_policy(
            self.policy, self.assessment.subject.query, self.assessment.policy_cutoff
        )
        if self.policy.bands[-1].upper_age_microseconds != (
            self.assessment.subject.policy.duration_microseconds
        ):
            raise ValueError("Feature decay must cover exactly (0,D]")
        return self


class FeatureDecayTraceEntry(_FeatureRepeatContract):
    witness: FeatureCooldownWitness
    age_microseconds: Annotated[int, Field(strict=True, gt=0)]
    band: FeatureDecayBand


class FeatureDecayTraceDraft(_FeatureRepeatResult):
    contract_version: Literal["feature-decay-trace.v1-draft"] = "feature-decay-trace.v1-draft"
    subject: FeatureDecayInput
    entries: tuple[FeatureDecayTraceEntry, ...]

    @field_validator("entries")
    @classmethod
    def unordered_entries(cls, values):
        return unique_sorted(values, key=lambda e: e.witness.fact.event_key())

    @model_validator(mode="after")
    def recompute(self):
        verify_feature_result(self, feature_decay_values(self.subject))
        return self


class FeatureRepeatPenaltyInput(_FeatureRepeatContract):
    contract_version: Literal["feature-repeat-penalty-input.v1"] = "feature-repeat-penalty-input.v1"
    trace: FeatureDecayTraceDraft
    policy: FeatureRepeatPenaltyPolicy

    @model_validator(mode="after")
    def matching_policy(self):
        assessment = self.trace.subject.assessment
        verify_feature_policy(self.policy, assessment.subject.query, assessment.policy_cutoff)
        return self


class FeatureRepeatPenaltyContribution(_FeatureRepeatContract):
    entry: FeatureDecayTraceEntry
    unit_penalty: FeatureRepeatPenaltyAmount
    contribution: FeatureRepeatPenaltyAmount


class AvailableProposalLocalFeaturePenalty(_FeatureRepeatContract):
    status: Literal["AVAILABLE"] = "AVAILABLE"
    amount: FeatureRepeatPenaltyAmount


class UnavailableProposalLocalFeaturePenalty(_FeatureRepeatContract):
    status: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    reason: Literal["UNRESOLVED_TERM_OCCURRENCES", "NO_MATCH_IN_SELECTED_PROPOSAL"]


class FeatureRepeatPenaltyDraft(_FeatureRepeatResult):
    contract_version: Literal["feature-repeat-penalty.v1-draft"] = "feature-repeat-penalty.v1-draft"
    subject: FeatureRepeatPenaltyInput
    contributions: tuple[FeatureRepeatPenaltyContribution, ...]
    proposal_local_feature_repeat_penalty: Annotated[
        AvailableProposalLocalFeaturePenalty | UnavailableProposalLocalFeaturePenalty,
        Field(discriminator="status"),
    ]

    @field_validator("contributions")
    @classmethod
    def unordered_contributions(cls, values):
        return unique_sorted(values, key=lambda c: c.entry.witness.fact.event_key())

    @model_validator(mode="after")
    def recompute(self):
        verify_feature_result(self, feature_penalty_values(self.subject))
        return self


def feature_repeat_content(value):
    """Respect frozen nested encodings, including unordered graph content and child clocks."""
    if isinstance(value, FeatureExposurePreviewDraft):
        return json.loads(value.canonical_json())
    if isinstance(value, Contract):
        return {
            name: feature_repeat_content(getattr(value, name)) for name in type(value).model_fields
        }
    if isinstance(value, dict):
        return {k: feature_repeat_content(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(feature_repeat_content(v) for v in value)
    return value


def reparse_feature_preview(value):
    """Normalize only declared sets, then let frozen 041E reconstruct its full manifest."""
    data = _feature_repeat_wire(value)
    if not isinstance(data, dict):
        raise ValueError("A full FeatureExposurePreviewDraft is required")
    data = dict(data)
    if "events" in data:
        data["events"] = unique_sorted(
            tuple(FeatureExposurePreviewFact.model_validate(e) for e in data["events"]),
            key=lambda e: e.event_key(),
        )
    if "diagnostics" in data:
        rows = [_feature_repeat_diagnostic(raw) for raw in data["diagnostics"]]
        data["diagnostics"] = unique_sorted(
            rows,
            key=lambda d: (
                str(d.member_id),
                str(d.meal_node_id),
                str(d.classification_source.batch_node_id),
                d.classification_source.dimension,
            ),
        )
    if "evidence_cuts" in data:
        data["evidence_cuts"] = unique_sorted(
            tuple(FeatureExposureEvidenceCut.model_validate(e) for e in data["evidence_cuts"]),
            key=lambda e: e.dimension,
        )
    return FeatureExposurePreviewDraft.model_validate(data)


def _feature_repeat_diagnostic(value):
    row = FeatureExposureCoverageDiagnostic.model_validate(_feature_repeat_wire(value))
    return row.model_copy(update={"allocation_node_ids": unique_sorted(row.allocation_node_ids)})


def verify_feature_policy(policy, query, cutoff):
    if (policy.dimension, policy.feature_term_id) != (query.dimension, query.feature_term_id):
        raise ValueError("FEATURE_POLICY_TERM_MISMATCH")
    if policy.provenance.observed_at > cutoff:
        raise ValueError("AS_OF_CAPTURE policy observed after minimum consumed child capture")


def feature_cooldown_context(subject):
    preview, query = subject.preview, subject.query
    source, request = preview.snapshot, preview.snapshot.request
    if (
        (query.household_id, query.plan_id, query.proposal_id, query.proposal_hash)
        != (request.household_id, request.plan_id, request.proposal_id, request.proposal_hash)
        or query.member_id not in request.selected_member_ids
        or query.dimension not in request.requested_dimensions
    ):
        raise ValueError("FEATURE_QUERY_OWNER_OR_DIMENSION_MISMATCH")
    member = next(m for m in source.member_sources if m.member_id == query.member_id)
    graph = member.sources[0].proposal.graph
    meal = next((m for m in graph.meals if m.node_id == query.meal_node_id), None)
    if meal is None:
        raise ValueError("TARGET_NOT_CAPTURED")
    time = meal.scheduled_at
    window = request.recipe_eligibility_policy.window
    if not (window.start <= time < window.end and graph.horizon.start <= time < graph.horizon.end):
        raise ValueError("TARGET_OUTSIDE_CAPTURE")
    try:
        start = time - timedelta(microseconds=subject.policy.duration_microseconds)
    except OverflowError as error:
        raise ValueError("LOOKBACK_NOT_CAPTURED: outside representable time") from error
    if not (window.start <= start and graph.horizon.start <= start):
        raise ValueError("LOOKBACK_NOT_CAPTURED")
    target = next(
        (
            e
            for e in preview.events
            if e.member_id == query.member_id
            and e.meal_node_id == query.meal_node_id
            and e.dimension == query.dimension
            and e.feature_term_id == query.feature_term_id
        ),
        None,
    )
    relevant = tuple(
        d
        for d in preview.diagnostics
        if d.member_id == query.member_id and d.classification_source.dimension == query.dimension
    )
    if target is None:
        unresolved = any(
            d.meal_node_id == query.meal_node_id and d.discovery.state == "UNRESOLVED"
            for d in relevant
        )
        raise ValueError("TARGET_FEATURE_UNRESOLVED" if unresolved else "TARGET_NOT_PRESENT")
    meals = {m.node_id: m for m in graph.meals}
    cells = tuple(
        d
        for d in relevant
        if d.meal_node_id == query.meal_node_id
        or start <= meals[d.meal_node_id].scheduled_at < time
    )
    consumed_batches = {d.classification_source.batch_node_id for d in cells}
    classifications = {
        s.subject.request.batch_node_id: s.subject.evaluation
        for s in source.classification_sources
        if s.subject.request.requested_dimensions == (query.dimension,)
        and s.subject.request.batch_node_id in consumed_batches
    }
    cutoff = min(member.captured_at, *(s.captured_at for s in classifications.values()))
    verify_feature_policy(subject.policy, query, cutoff)
    return target, start, cutoff, cells, classifications, meals


def feature_cooldown_values(subject):
    target, start, cutoff, diagnostics, classifications, meals = feature_cooldown_context(subject)
    query = subject.query
    grouped = {}
    term_query = FeatureTermQuery(dimension=query.dimension, term_ids=(query.feature_term_id,))
    # Resolve once per consumed source; one batch may support several participating meals.
    resolutions = {
        bid: resolve_feature_input(evaluation, (term_query,))[0]
        for bid, evaluation in classifications.items()
    }
    for diagnostic in diagnostics:
        if diagnostic.meal_node_id == query.meal_node_id:
            continue
        cell = FeatureTermCoverageCell(
            diagnostic=diagnostic,
            resolution=resolutions[diagnostic.classification_source.batch_node_id],
        )
        grouped.setdefault(diagnostic.meal_node_id, []).append(cell)
    events = {
        e.meal_node_id: e
        for e in subject.preview.events
        if e.member_id == query.member_id
        and e.dimension == query.dimension
        and e.feature_term_id == query.feature_term_id
    }
    occurrences, witnesses, unknowns = [], [], []
    for meal_id, cells in sorted(grouped.items(), key=lambda kv: str(kv[0])):
        states = {cell.resolution.state for cell in cells}
        state = (
            "PRESENT"
            if "PRESENT" in states
            else "REVIEWED_ABSENT"
            if states == {"REVIEWED_ABSENT"}
            else "UNRESOLVED"
        )
        event = events.get(meal_id)
        positive_allocations = {
            aid
            for cell in cells
            if cell.resolution.state == "PRESENT"
            for aid in cell.diagnostic.allocation_node_ids
        }
        if (event is not None) != (state == "PRESENT") or (
            event is not None
            and {w.allocation_node_id for w in event.support} != positive_allocations
        ):
            raise ValueError("Feature occurrence and frozen 041E positive support disagree")
        occurrences.append(
            FeatureMealTermOccurrence(
                meal_node_id=meal_id,
                scheduled_at=meals[meal_id].scheduled_at,
                dimension=query.dimension,
                feature_term_id=query.feature_term_id,
                cells=tuple(cells),
                state=state,
                event=event,
            )
        )
        if state == "UNRESOLVED":
            unknowns.append(meal_id)
        if event is not None:
            distance = target.scheduled_at - event.scheduled_at
            age = (distance.days * 86400 + distance.seconds) * 1000000 + distance.microseconds
            witnesses.append(FeatureCooldownWitness(fact=event, distance_microseconds=age))
    return dict(
        target=target,
        lookback_start=start,
        policy_cutoff=cutoff,
        occurrences=tuple(occurrences),
        witnesses=tuple(sorted(witnesses, key=lambda w: w.fact.event_key())),
        unresolved_meal_ids=tuple(sorted(unknowns, key=str)),
        outcome=(
            "MATCH_IN_SELECTED_PROPOSAL"
            if witnesses
            else "UNRESOLVED_IN_SELECTED_PROPOSAL"
            if unknowns
            else "NO_MATCH_IN_SELECTED_PROPOSAL"
        ),
        occurrence_resolution=(
            "HAS_UNRESOLVED_MEALS"
            if unknowns
            else "ALL_QUERIED_TERM_OCCURRENCES_DECIDABLE"
            if occurrences
            else "NO_ELIGIBLE_PRIOR_MEALS"
        ),
        source_preview_fingerprint=subject.preview.fingerprint(),
        dimension_evidence_cut_digest=next(
            e.digest for e in subject.preview.evidence_cuts if e.dimension == query.dimension
        ),
    )


def _inherited_result(assessment):
    return {
        name: getattr(assessment, name)
        for name in (
            "outcome",
            "occurrence_resolution",
            "unresolved_meal_ids",
            "source_preview_fingerprint",
            "dimension_evidence_cut_digest",
        )
    }


def feature_decay_values(subject):
    entries = []
    for witness in subject.assessment.witnesses:
        age = witness.distance_microseconds
        band = next(
            b
            for b in subject.policy.bands
            if b.lower_age_microseconds < age <= b.upper_age_microseconds
        )
        entries.append(FeatureDecayTraceEntry(witness=witness, age_microseconds=age, band=band))
    return _inherited_result(subject.assessment) | dict(entries=tuple(entries))


def feature_penalty_values(subject):
    contributions = []
    total_n, total_d = 0, 1
    unit = subject.policy.unit_penalty
    for entry in subject.trace.entries:
        retention = entry.band.retention_multiplier
        amount = FeatureRepeatPenaltyAmount(
            numerator=unit.numerator * retention.numerator,
            denominator=unit.denominator * retention.denominator,
        )
        contributions.append(
            FeatureRepeatPenaltyContribution(
                entry=entry,
                unit_penalty=unit,
                contribution=amount,
            )
        )
        total_n = total_n * amount.denominator + amount.numerator * total_d
        total_d *= amount.denominator
        divisor = gcd(total_n, total_d)
        total_n, total_d = total_n // divisor, total_d // divisor
    if subject.trace.unresolved_meal_ids:
        result = UnavailableProposalLocalFeaturePenalty(reason="UNRESOLVED_TERM_OCCURRENCES")
    elif not contributions:
        result = UnavailableProposalLocalFeaturePenalty(reason="NO_MATCH_IN_SELECTED_PROPOSAL")
    else:
        result = AvailableProposalLocalFeaturePenalty(
            amount=FeatureRepeatPenaltyAmount(numerator=total_n, denominator=total_d)
        )
    return _inherited_result(subject.trace) | dict(
        contributions=tuple(contributions),
        proposal_local_feature_repeat_penalty=result,
    )


def verify_feature_result(result, expected):
    for name, value in expected.items():
        if getattr(result, name) != value:
            raise ValueError(f"Feature repeat result differs from recomputed primitives: {name}")
