"""Raw explicit assertions. EvidenceStrength belongs to later profile derivation."""

import json
from hashlib import sha256
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, TypeAdapter, model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, Sha256
from app.domain.units import Provenance
from app.modules.catalog.contracts import AffinityFeatureTermFact, IngredientIdentityFact
from app.modules.recipes.contracts import RecipeFact


class IngredientPreferenceTarget(Contract):
    kind: Literal["INGREDIENT"] = "INGREDIENT"
    ingredient_id: UUID


class RecipePreferenceTarget(Contract):
    kind: Literal["DIRECT_RECIPE"] = "DIRECT_RECIPE"
    recipe_id: UUID


class FeaturePreferenceTarget(Contract):
    kind: Literal["PROTEIN", "METHOD", "FLAVOR"]
    feature_term_id: UUID


PreferenceTarget = Annotated[
    IngredientPreferenceTarget | RecipePreferenceTarget | FeaturePreferenceTarget,
    Field(discriminator="kind"),
]
AffinityValue = Literal["LIKE", "DISLIKE", "NEUTRAL"]


def preference_json(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def preference_time(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


class PreferenceWriteCommand(Contract):
    contract_version: Literal["member-preference-write.v1"] = "member-preference-write.v1"
    household_id: UUID
    member_id: UUID
    actor_user_id: UUID
    authorship: Literal["SELF", "AUTHORIZED_REPRESENTATIVE"]
    target: PreferenceTarget
    expected_revision: Annotated[int, Field(strict=True, ge=-1, le=2_147_483_646)]
    predecessor_id: UUID | None
    action: Literal["SET", "RETRACT"]
    value: AffinityValue | None
    reason: Literal["INITIAL", "INPUT_CORRECTION", "PREFERENCE_CHANGED", "RETRACTED"]
    occurred_at: AwareTime
    provenance: Provenance
    idempotency_key: Identifier
    source: Literal["EXPLICIT_DECLARATION"] = "EXPLICIT_DECLARATION"

    @model_validator(mode="after")
    def explicit_shape(self):
        if self.provenance.kind != "USER" or self.occurred_at > self.provenance.observed_at:
            raise ValueError("Explicit assertion requires USER provenance after occurrence")
        if (self.expected_revision == -1) != (self.predecessor_id is None):
            raise ValueError("Expected head and predecessor differ")
        if self.action == "SET":
            if (
                self.value is None
                or ((self.expected_revision == -1) != (self.reason == "INITIAL"))
                or self.reason == "RETRACTED"
            ):
                raise ValueError("SET requires value and correct initial/replacement reason")
        elif self.value is not None or self.reason != "RETRACTED" or self.expected_revision < 0:
            raise ValueError("RETRACT requires active predecessor and no value")
        return self

    def fingerprint(self):
        data = self.model_dump(mode="json")
        data["occurred_at"] = preference_time(self.occurred_at)
        data["provenance"]["observed_at"] = preference_time(self.provenance.observed_at)
        return sha256(preference_json(data).encode()).hexdigest()


class SetMemberPreferenceCommand(PreferenceWriteCommand):
    action: Literal["SET"] = "SET"
    value: AffinityValue


class RetractMemberPreferenceCommand(PreferenceWriteCommand):
    action: Literal["RETRACT"] = "RETRACT"
    value: None = None
    reason: Literal["RETRACTED"] = "RETRACTED"


class MemberPreferenceDeclarationFact(Contract):
    contract_version: Literal["member-preference-declaration.v1"] = (
        "member-preference-declaration.v1"
    )
    id: UUID
    stream_id: UUID
    revision_no: Annotated[int, Field(strict=True, ge=0)]
    member_sequence: Annotated[int, Field(strict=True, gt=0)]
    recorded_at: AwareTime
    actor_role: Literal["OWNER", "EDITOR"]
    command: Annotated[
        SetMemberPreferenceCommand | RetractMemberPreferenceCommand,
        Field(discriminator="action"),
    ]
    command_fingerprint: Sha256

    @model_validator(mode="after")
    def source_identity(self):
        if (
            self.revision_no != self.command.expected_revision + 1
            or self.command.provenance.observed_at > self.recorded_at
            or self.command_fingerprint != self.command.fingerprint()
        ):
            raise ValueError("Declaration revision/time/primitive fingerprint differs")
        return self


class MemberPreferenceState(Contract):
    target: PreferenceTarget
    status: Literal["UNDECLARED", "DECLARED", "RETRACTED"]
    value: AffinityValue | None
    declaration_id: UUID | None

    @model_validator(mode="after")
    def no_fake_neutral(self):
        if (self.status == "DECLARED") != (self.value is not None) or (
            (self.status == "UNDECLARED") != (self.declaration_id is None)
        ):
            raise ValueError("Undeclared/retracted is not a neutral assertion")
        return self


class ExplicitMemberPreferenceSnapshot(Contract):
    contract_version: Literal["explicit-member-preferences.v1"] = "explicit-member-preferences.v1"
    coverage: Literal["EXPLICIT_DECLARATIONS_ONLY"] = "EXPLICIT_DECLARATIONS_ONLY"
    profile_derivation: Literal["NOT_IMPLEMENTED"] = "NOT_IMPLEMENTED"
    household_id: UUID
    member_id: UUID
    frontier: Annotated[int, Field(strict=True, ge=0)]
    captured_at: AwareTime
    declarations: tuple[MemberPreferenceDeclarationFact, ...]
    feature_terms: tuple[AffinityFeatureTermFact, ...] = ()

    @model_validator(mode="after")
    def replay(self):
        rows = sorted(self.declarations, key=lambda r: r.member_sequence)
        if len(rows) != self.frontier or any(r.member_sequence != n for n, r in enumerate(rows, 1)):
            raise ValueError("Incomplete member preference history/frontier")
        if len({r.id for r in rows}) != len(rows):
            raise ValueError("Duplicate declaration identity")
        terms = {t.id: t for t in self.feature_terms}
        if len(terms) != len(self.feature_terms):
            raise ValueError("Duplicate feature term")
        heads, owners = {}, {}
        used_terms = set()
        for r in rows:
            c = r.command
            if (c.household_id, c.member_id) != (self.household_id, self.member_id) or (
                r.recorded_at > self.captured_at
            ):
                raise ValueError("Foreign owner or future declaration")
            key = preference_json(c.target.model_dump(mode="json"))
            if key in owners and owners[key] != r.stream_id:
                raise ValueError("Duplicate target streams")
            owners[key] = r.stream_id
            old = heads.get(r.stream_id)
            if old is None:
                if r.revision_no != 0 or c.predecessor_id is not None:
                    raise ValueError("Missing initial declaration")
            elif (
                c.target != old.command.target
                or c.predecessor_id != old.id
                or r.revision_no != old.revision_no + 1
                or r.recorded_at < old.recorded_at
                or (c.action == "RETRACT" and old.command.action == "RETRACT")
            ):
                raise ValueError("Broken preference lineage")
            if isinstance(c.target, FeaturePreferenceTarget):
                term = terms.get(c.target.feature_term_id)
                if (
                    term is None
                    or term.kind != c.target.kind
                    or term.status != "REVIEWED"
                    or term.provenance.observed_at > r.recorded_at
                ):
                    raise ValueError("Unresolved reviewed feature target")
                used_terms.add(term.id)
            heads[r.stream_id] = r
        if set(terms) != used_terms:
            raise ValueError("Unbound feature vocabulary")
        return self

    def state_for(self, target: PreferenceTarget):
        target = TypeAdapter(PreferenceTarget).validate_python(
            target.model_dump() if isinstance(target, Contract) else target
        )
        rows = [r for r in self.declarations if r.command.target == target]
        latest = max(rows, key=lambda r: r.member_sequence) if rows else None
        return MemberPreferenceState(
            target=target,
            status=(
                "UNDECLARED"
                if latest is None
                else "RETRACTED"
                if latest.command.action == "RETRACT"
                else "DECLARED"
            ),
            value=latest.command.value if latest else None,
            declaration_id=latest.id if latest else None,
        )

    def canonical_json(self):
        data = self.model_dump(mode="json")
        data["declarations"] = sorted(data["declarations"], key=lambda r: r["member_sequence"])
        data["feature_terms"] = sorted(data["feature_terms"], key=lambda t: t["id"])
        return preference_json(data)

    def fingerprint(self):
        return sha256(self.canonical_json().encode()).hexdigest()


# Additive MTR-040B. Frozen raw declarations and their canonical bytes above stay unchanged.
from math import gcd  # noqa: E402

from pydantic import BaseModel, ConfigDict  # noqa: E402

from app.domain.feature_identity import canonical, canonical_bytes, unique_sorted  # noqa: E402

TargetKind = Literal["INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"]
EvidenceStrength = Literal["NONE", "LOW", "MEDIUM", "HIGH"]


def _profile_primitives(value):
    """Reparse even constructed/copied nested frozen source instances, without IO."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="python")
    if isinstance(value, dict):
        return {k: _profile_primitives(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_profile_primitives(v) for v in value)
    return value


def _profile_content(value):
    if isinstance(value, ExplicitMemberPreferenceSnapshot):
        # This child has its own frozen encoding, including its original clocks.
        return json.loads(value.canonical_json())
    if isinstance(value, BaseModel):
        return {k: _profile_content(getattr(value, k)) for k in type(value).model_fields}
    if isinstance(value, dict):
        return {k: _profile_content(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_profile_content(v) for v in value]
    return canonical(value)


def _profile_hash(value):
    return sha256(canonical_bytes(_profile_content(value))).hexdigest()


def preference_target_key(target):
    """Typed exact identity, never a feature code or a guessed recipe version."""
    identity = target.model_dump(exclude={"kind"})
    return target.kind, str(next(iter(identity.values())))


class _AffinityContract(Contract):
    model_config = ConfigDict(revalidate_instances="always")

    @model_validator(mode="before")
    @classmethod
    def reparse_primitives(cls, value):
        return _profile_primitives(value)

    def canonical_json(self):
        return canonical_bytes(_profile_content(self)).decode("utf-8")


class ExplicitTargetAffinityCaptureRequest(_AffinityContract):
    contract_version: Literal["explicit-target-affinity-capture.v1"] = (
        "explicit-target-affinity-capture.v1"
    )
    household_id: UUID
    member_id: UUID
    requested_targets: tuple[PreferenceTarget, ...]

    @model_validator(mode="after")
    def canonical_targets(self):
        object.__setattr__(
            self,
            "requested_targets",
            unique_sorted(self.requested_targets, key=preference_target_key),
        )
        return self


class IngredientTargetManifestEntry(_AffinityContract):
    kind: Literal["INGREDIENT"] = "INGREDIENT"
    identity: IngredientIdentityFact

    def target(self):
        return IngredientPreferenceTarget(ingredient_id=self.identity.id)


class RecipeTargetManifestEntry(_AffinityContract):
    kind: Literal["DIRECT_RECIPE"] = "DIRECT_RECIPE"
    identity: RecipeFact

    def target(self):
        return RecipePreferenceTarget(recipe_id=self.identity.id)


class FeatureTargetManifestEntry(_AffinityContract):
    kind: Literal["PROTEIN", "METHOD", "FLAVOR"]
    identity: AffinityFeatureTermFact

    @model_validator(mode="after")
    def reviewed_exact_kind(self):
        if self.kind != self.identity.kind or self.identity.status != "REVIEWED":
            raise ValueError("TARGET_NOT_REVIEWED: exact reviewed feature kind required")
        return self

    def target(self):
        return FeaturePreferenceTarget(kind=self.kind, feature_term_id=self.identity.id)


TargetManifestEntry = Annotated[
    IngredientTargetManifestEntry | RecipeTargetManifestEntry | FeatureTargetManifestEntry,
    Field(discriminator="kind"),
]


class CanonicalPreferenceTargetManifest(_AffinityContract):
    contract_version: Literal["preference-target-manifest.v1"] = "preference-target-manifest.v1"
    household_id: UUID
    member_id: UUID
    coverage: Literal["REQUESTED_CANONICAL_TARGETS_ONLY"] = "REQUESTED_CANONICAL_TARGETS_ONLY"
    entries: tuple[TargetManifestEntry, ...]

    @model_validator(mode="after")
    def canonical_entries(self):
        object.__setattr__(
            self,
            "entries",
            unique_sorted(self.entries, key=lambda e: preference_target_key(e.target())),
        )
        return self


class ExplicitTargetAffinitySourceSnapshotDraft(_AffinityContract):
    contract_version: Literal["explicit-target-affinity-source.v1-draft"] = (
        "explicit-target-affinity-source.v1-draft"
    )
    activation_ready: Literal[False] = False
    request: ExplicitTargetAffinityCaptureRequest
    preferences: ExplicitMemberPreferenceSnapshot
    manifest: CanonicalPreferenceTargetManifest
    capture_completed_at: AwareTime

    @model_validator(mode="after")
    def exact_capture(self):
        owner = self.request.household_id, self.request.member_id
        if any((v.household_id, v.member_id) != owner for v in (self.preferences, self.manifest)):
            raise ValueError("Foreign profile source/manifest owner")
        if tuple(e.target() for e in self.manifest.entries) != self.request.requested_targets:
            raise ValueError("TARGET_IDENTITY_UNRESOLVED: exact requested manifest required")
        if self.preferences.captured_at > self.capture_completed_at:
            raise ValueError("Source capture follows completion")
        terms = {t.id: t for t in self.preferences.feature_terms}
        for entry in self.manifest.entries:
            if isinstance(entry, FeatureTargetManifestEntry):
                t = entry.identity
                if t.provenance.observed_at > self.capture_completed_at:
                    raise ValueError("Future feature provenance")
                if t.id in terms and terms[t.id] != t:
                    raise ValueError("Manifest/source immutable term conflict")
        return self


class ExplicitAffinityAmount(_AffinityContract):
    contract_version: Literal["explicit-affinity-amount.v1"] = "explicit-affinity-amount.v1"
    numerator: Annotated[int, Field(strict=True)]
    denominator: Annotated[int, Field(strict=True, gt=0)]
    unit: Literal["POLICY_EXPLICIT_AFFINITY_UNITS"] = "POLICY_EXPLICIT_AFFINITY_UNITS"

    @model_validator(mode="after")
    def reduce_exact(self):
        if not -self.denominator <= self.numerator <= self.denominator:
            raise ValueError("Affinity outside signed unit coordinate range")
        divisor = gcd(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", self.numerator // divisor)
        object.__setattr__(self, "denominator", self.denominator // divisor)
        return self


class ExplicitAffinityValueRule(_AffinityContract):
    value: AffinityValue
    amount: ExplicitAffinityAmount


class ExplicitAuthorshipStrengthRule(_AffinityContract):
    authorship: Literal["SELF", "AUTHORIZED_REPRESENTATIVE"]
    level: Literal["LOW", "MEDIUM", "HIGH"]


class ExplicitTargetKindPolicy(_AffinityContract):
    target_kind: TargetKind
    affinity_rules: tuple[ExplicitAffinityValueRule, ...]
    strength_rules: tuple[ExplicitAuthorshipStrengthRule, ...]
    undeclared_strength: Literal["NONE"]
    retracted_strength: Literal["NONE"]

    @model_validator(mode="after")
    def complete_mappings(self):
        affinities = unique_sorted(self.affinity_rules, key=lambda r: r.value)
        strengths = unique_sorted(self.strength_rules, key=lambda r: r.authorship)
        if {r.value for r in affinities} != {"LIKE", "DISLIKE", "NEUTRAL"} or {
            r.authorship for r in strengths
        } != {"SELF", "AUTHORIZED_REPRESENTATIVE"}:
            raise ValueError("Complete explicit value/authorship mappings required")
        amounts = {r.value: r.amount for r in affinities}
        for a, b in (("DISLIKE", "NEUTRAL"), ("NEUTRAL", "LIKE")):
            x, y = amounts[a], amounts[b]
            if x.numerator * y.denominator >= y.numerator * x.denominator:
                raise ValueError("Policy requires exact DISLIKE < NEUTRAL < LIKE")
        object.__setattr__(self, "affinity_rules", affinities)
        object.__setattr__(self, "strength_rules", strengths)
        return self


class ExplicitTargetAffinityPolicy(_AffinityContract):
    contract_version: Literal["explicit-target-affinity-policy.v1"] = (
        "explicit-target-affinity-policy.v1"
    )
    policy_id: Identifier
    policy_version: Identifier
    provenance: Provenance
    interpretation_mode: Literal["EXPLICIT_POLICY_VERSION_REPLAY"] = (
        "EXPLICIT_POLICY_VERSION_REPLAY"
    )
    evidence_basis: Literal["LATEST_ACTIVE_EXPLICIT_DECLARATION_ONLY"] = (
        "LATEST_ACTIVE_EXPLICIT_DECLARATION_ONLY"
    )
    target_policies: tuple[ExplicitTargetKindPolicy, ...]
    prior_mode: Literal["UNAVAILABLE_ONLY"] = "UNAVAILABLE_ONLY"
    shrinkage_mode: Literal["UNAVAILABLE_ONLY"] = "UNAVAILABLE_ONLY"

    @model_validator(mode="after")
    def complete_policy(self):
        if self.provenance.kind not in {"USER", "REVIEWED_REFERENCE"}:
            raise ValueError("Explicit authored/reviewed policy provenance required")
        rows = unique_sorted(self.target_policies, key=lambda p: p.target_kind)
        if {r.target_kind for r in rows} != {
            "INGREDIENT",
            "DIRECT_RECIPE",
            "PROTEIN",
            "METHOD",
            "FLAVOR",
        }:
            raise ValueError("Complete five-kind policy required")
        object.__setattr__(self, "target_policies", rows)
        return self


class ExplicitTargetAffinityInput(_AffinityContract):
    contract_version: Literal["explicit-target-affinity-input.v1"] = (
        "explicit-target-affinity-input.v1"
    )
    source: ExplicitTargetAffinitySourceSnapshotDraft
    policy: ExplicitTargetAffinityPolicy


class AvailableExplicitAffinity(_AffinityContract):
    status: Literal["AVAILABLE"] = "AVAILABLE"
    amount: ExplicitAffinityAmount
    policy_rule_key: tuple[TargetKind, AffinityValue]
    declaration_id: UUID


class UnavailableExplicitAffinity(_AffinityContract):
    status: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    reason: Literal["UNDECLARED", "RETRACTED"]


class DerivedExplicitEvidenceStrength(_AffinityContract):
    contract_version: Literal["explicit-evidence-strength.v1"] = "explicit-evidence-strength.v1"
    scope: Literal["CURRENT_EXPLICIT_TARGET_ONLY"] = "CURRENT_EXPLICIT_TARGET_ONLY"
    level: EvidenceStrength
    basis: Literal["NO_ACTIVE_DECLARATION", "SINGLE_CURRENT_EXPLICIT_DECLARATION"]
    active_declaration_id: UUID | None
    rule_key: tuple[TargetKind, Literal["SELF", "AUTHORIZED_REPRESENTATIVE"]] | None

    @model_validator(mode="after")
    def active_basis(self):
        if self.level == "NONE":
            if self.basis != "NO_ACTIVE_DECLARATION" or (
                self.active_declaration_id is not None or self.rule_key is not None
            ):
                raise ValueError("NONE requires no active explicit declaration")
        elif self.basis != "SINGLE_CURRENT_EXPLICIT_DECLARATION" or (
            self.active_declaration_id is None or self.rule_key is None
        ):
            raise ValueError("Active strength requires exact declaration and policy rule")
        return self


class UnavailablePreferencePrior(_AffinityContract):
    contract_version: Literal["preference-prior-availability.v1"] = (
        "preference-prior-availability.v1"
    )
    status: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    reason: Literal["NO_CANONICAL_PREFERENCE_PRIOR_SOURCE"] = "NO_CANONICAL_PREFERENCE_PRIOR_SOURCE"


class UnavailableShrunkAffinity(_AffinityContract):
    contract_version: Literal["shrunk-affinity-availability.v1"] = "shrunk-affinity-availability.v1"
    status: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    reason: Literal["PRIOR_UNAVAILABLE"] = "PRIOR_UNAVAILABLE"


class DerivedTargetAffinity(_AffinityContract):
    contract_version: Literal["derived-explicit-target-affinity.v1"] = (
        "derived-explicit-target-affinity.v1"
    )
    target: PreferenceTarget
    raw_state: MemberPreferenceState
    current_declaration: MemberPreferenceDeclarationFact | None
    affinity: Annotated[
        AvailableExplicitAffinity | UnavailableExplicitAffinity, Field(discriminator="status")
    ]
    evidence_strength: DerivedExplicitEvidenceStrength
    prior: UnavailablePreferencePrior
    shrunk_affinity: UnavailableShrunkAffinity

    @model_validator(mode="after")
    def head_consistency(self):
        head, state, strength = self.current_declaration, self.raw_state, self.evidence_strength
        if state.target != self.target or state.declaration_id != (head.id if head else None):
            raise ValueError("Target/state/current declaration mismatch")
        if head is not None and head.command.target != self.target:
            raise ValueError("Foreign current head")
        if state.status == "DECLARED":
            if head is None or head.command.action != "SET" or head.command.value != state.value:
                raise ValueError("Active head/value mismatch")
            if not isinstance(self.affinity, AvailableExplicitAffinity) or (
                self.affinity.declaration_id != head.id
                or self.affinity.policy_rule_key != (self.target.kind, state.value)
                or strength.level == "NONE"
                or strength.active_declaration_id != head.id
                or strength.rule_key != (self.target.kind, head.command.authorship)
            ):
                raise ValueError("Active affinity/strength head mismatch")
        else:
            if (state.status == "RETRACTED") != (head is not None):
                raise ValueError("Retraction requires retained head")
            if head is not None and head.command.action != "RETRACT":
                raise ValueError("Retraction head must retract")
            if not isinstance(self.affinity, UnavailableExplicitAffinity) or (
                self.affinity.reason != state.status or strength.level != "NONE"
            ):
                raise ValueError("No active assertion: affinity unavailable and strength NONE")
        return self


def _explicit_target_affinity_rows(subject):
    """Contract enforcement recomputes each value from complete primitives + explicit policy."""
    source = subject.source.preferences
    policies = {p.target_kind: p for p in subject.policy.target_policies}
    heads = {}
    for declaration in sorted(source.declarations, key=lambda d: d.member_sequence):
        heads[preference_target_key(declaration.command.target)] = declaration
    rows = []
    for entry in subject.source.manifest.entries:
        target = entry.target()
        state = source.state_for(target)
        head = heads.get(preference_target_key(target))
        policy = policies[target.kind]
        if state.status == "DECLARED":
            affinity = AvailableExplicitAffinity(
                amount=next(r.amount for r in policy.affinity_rules if r.value == state.value),
                policy_rule_key=(target.kind, state.value),
                declaration_id=head.id,
            )
            strength = DerivedExplicitEvidenceStrength(
                level=next(
                    r.level
                    for r in policy.strength_rules
                    if r.authorship == head.command.authorship
                ),
                basis="SINGLE_CURRENT_EXPLICIT_DECLARATION",
                active_declaration_id=head.id,
                rule_key=(target.kind, head.command.authorship),
            )
        else:
            affinity = UnavailableExplicitAffinity(reason=state.status)
            strength = DerivedExplicitEvidenceStrength(
                level=policy.undeclared_strength
                if state.status == "UNDECLARED"
                else policy.retracted_strength,
                basis="NO_ACTIVE_DECLARATION",
                active_declaration_id=None,
                rule_key=None,
            )
        rows.append(
            DerivedTargetAffinity(
                target=target,
                raw_state=state,
                current_declaration=head,
                affinity=affinity,
                evidence_strength=strength,
                prior=UnavailablePreferencePrior(),
                shrunk_affinity=UnavailableShrunkAffinity(),
            )
        )
    return tuple(rows)


class ExplicitTargetAffinityProfileDraft(_AffinityContract):
    contract_version: Literal["explicit-target-affinity-profile.v1-draft"] = (
        "explicit-target-affinity-profile.v1-draft"
    )
    coverage: Literal["EXPLICIT_SOURCE_TARGETS_ONLY"] = "EXPLICIT_SOURCE_TARGETS_ONLY"
    absence_semantics: Literal["NO_TARGET_ROWS_IS_NOT_GLOBAL_PREFERENCE_NEUTRALITY"] = (
        "NO_TARGET_ROWS_IS_NOT_GLOBAL_PREFERENCE_NEUTRALITY"
    )
    learned_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    contextual_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    passive_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    cross_target_inference: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    candidate_aggregation: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False
    subject: ExplicitTargetAffinityInput
    rows: tuple[DerivedTargetAffinity, ...]
    source_fingerprint: Sha256
    manifest_fingerprint: Sha256
    policy_fingerprint: Sha256
    fingerprint: Sha256

    def expected_fingerprint(self):
        data = _profile_content(self)
        del data["fingerprint"]
        return _profile_hash(data)

    @model_validator(mode="after")
    def recompute(self):
        subject = ExplicitTargetAffinityInput.model_validate(self.subject)
        rows = unique_sorted(self.rows, key=lambda r: preference_target_key(r.target))
        if rows != _explicit_target_affinity_rows(subject):
            raise ValueError("Derived rows differ from captured primitives and policy")
        for name, value in (
            ("source_fingerprint", subject.source),
            ("manifest_fingerprint", subject.source.manifest),
            ("policy_fingerprint", subject.policy),
        ):
            if getattr(self, name) != _profile_hash(value):
                raise ValueError("Derived fingerprint differs from primitives: " + name)
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "rows", rows)
        if self.fingerprint != self.expected_fingerprint():
            raise ValueError("Derived result fingerprint differs from primitives")
        return self
