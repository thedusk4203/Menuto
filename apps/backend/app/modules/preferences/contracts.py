"""Raw explicit assertions. EvidenceStrength belongs to later profile derivation."""

import json
from hashlib import sha256
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, TypeAdapter, model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, Sha256
from app.domain.units import Provenance
from app.modules.catalog.contracts import AffinityFeatureTermFact


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
