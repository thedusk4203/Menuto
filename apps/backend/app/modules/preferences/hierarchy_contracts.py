"""Reviewed hierarchy SOURCE only; no member data, arithmetic or consumer authority."""

from fractions import Fraction
from math import gcd
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, Sha256
from app.domain.feature_identity import canonical, identity_hash, unique_sorted
from app.domain.units import Provenance
from app.modules.catalog.contracts import (
    AffinityFeatureTermFact,
    IngredientIdentityFact,
    IngredientProteinStreamFact,
)
from app.modules.preferences.contracts import (
    AffinityValue,
    ExplicitAffinityAmount,
    ExplicitTargetAffinityPolicy,
    PreferenceTarget,
    TargetKind,
    _profile_hash,
)
from app.modules.preferences.prior_affinity_contracts import (
    ExactTargetPriorCompatibilityPolicy,
    MemberProfileAffinityCoordinate,
)
from app.modules.recipes.contracts import (
    CulinaryFeatureApplicabilityKey,
    CulinaryFeatureScopeFact,
    FeatureSelectedPath,
    RecipeFact,
    RecipeVersionSnapshot,
)

Counter = Annotated[int, Field(strict=True, ge=0, le=9_223_372_036_854_775_807)]
Sequence = Annotated[int, Field(strict=True, gt=0, le=9_223_372_036_854_775_807)]
Revision = Annotated[int, Field(strict=True, ge=0, le=2_147_483_647)]
ExpectedRevision = Annotated[int, Field(strict=True, ge=-1, le=2_147_483_647)]
Oid = Annotated[int, Field(strict=True, gt=0, le=4_294_967_295)]
Reason = Annotated[str, Field(min_length=1, max_length=4000, pattern=r"\S")]
PgName = Annotated[str, Field(min_length=1, max_length=63, pattern=r"^[^\x00-\x1f\x7f]+$")]
Capability = Literal["REVIEW_PUBLISH", "RETRACT", "CAPTURE"]


class _HierarchyContract(Contract):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True, revalidate_instances="always"
    )

    @model_validator(mode="before")
    @classmethod
    def primitives(cls, value):
        return canonical(value)

    @field_validator(
        "read_only", "planner_ready", "activation_ready", mode="before", check_fields=False
    )
    @classmethod
    def strict_flags(cls, value):
        if type(value) is not bool:
            raise ValueError("Flags require JSON booleans")
        return value


def hierarchy_hash(domain, value):
    return identity_hash({"domain": domain, "value": canonical(value)})


def target_key(target):
    return identity_hash(target)


class HierarchySessionFact(_HierarchyContract):
    database_oid: Oid
    database_name: PgName
    role_oid: Oid
    role_name: PgName
    authentication_method: Literal["scram-sha-256"] = "scram-sha-256"
    authenticated_identity: PgName

    @model_validator(mode="after")
    def authenticated_login(self):
        if self.role_name != self.authenticated_identity:
            raise ValueError("Authentication and session identity differ")
        return self


class HierarchyProviderCommand(_HierarchyContract):
    code: Identifier
    version: Identifier
    source_system: Identifier
    remit: Reason
    idempotency_key: Identifier


class HierarchyPrincipalCommand(_HierarchyContract):
    role_name: PgName
    idempotency_key: Identifier


class HierarchyProviderFact(_HierarchyContract):
    id: UUID
    command: HierarchyProviderCommand
    administrator: HierarchySessionFact
    recorded_at: AwareTime
    command_hash: Sha256

    @model_validator(mode="after")
    def command_identity(self):
        if self.command_hash != hierarchy_hash("hierarchy.provider-command.v1", self.command):
            raise ValueError("Provider registration command hash differs")
        return self


class HierarchyPrincipalFact(_HierarchyContract):
    id: UUID
    command: HierarchyPrincipalCommand
    database_oid: Oid
    database_name: PgName
    role_oid: Oid
    role_name: PgName
    administrator: HierarchySessionFact
    recorded_at: AwareTime
    command_hash: Sha256

    @model_validator(mode="after")
    def binding(self):
        if (
            self.role_name != self.command.role_name
            or (self.database_oid, self.database_name)
            != (self.administrator.database_oid, self.administrator.database_name)
            or self.command_hash != hierarchy_hash("hierarchy.principal-command.v1", self.command)
        ):
            raise ValueError("Principal enrollment binding differs")
        return self


class HierarchyAuthorityCommand(_HierarchyContract):
    provider_id: UUID
    principal_id: UUID
    capability: Capability
    action: Literal["GRANT", "REVOKE"]
    expected_authority_generation: Counter
    reason: Reason
    idempotency_key: Identifier


KINDS = {"INGREDIENT", "PROTEIN", "METHOD", "FLAVOR", "DIRECT_RECIPE"}
SupportMode = Literal["REVIEWED_EXACT_PAIR", "CLASSIFICATION_BOUND_PAIR"]


class HierarchyProvenance(Provenance):
    kind: Literal["REVIEWED_REFERENCE"] = "REVIEWED_REFERENCE"
    content_hash: Sha256


class HierarchyPolicyAmount(_HierarchyContract):
    numerator: Annotated[int, Field(strict=True, ge=-2147483647, le=2147483647)]
    denominator: Annotated[int, Field(strict=True, gt=0, le=2147483647)]

    @model_validator(mode="after")
    def canonical_rational(self):
        if (
            abs(self.numerator) > self.denominator
            or gcd(abs(self.numerator), self.denominator) != 1
        ):
            raise ValueError("Canonical exact signed unit rational required")
        return self


class HierarchyTransferMapRow(_HierarchyContract):
    source_descriptor: MemberProfileAffinityCoordinate
    source_affinity_value: AffinityValue
    expected_source_amount: ExplicitAffinityAmount
    output_amount: HierarchyPolicyAmount

    @model_validator(mode="after")
    def semantic_anchor(self):
        n = self.output_amount.numerator
        if self.source_affinity_value == "NEUTRAL" and n != 0:
            raise ValueError("NEUTRAL must map exactly to 0/1")
        if self.source_affinity_value == "DISLIKE" and n > 0:
            raise ValueError("DISLIKE cannot map positive")
        if self.source_affinity_value == "LIKE" and n < 0:
            raise ValueError("LIKE cannot map negative")
        if (
            max(abs(self.expected_source_amount.numerator), self.expected_source_amount.denominator)
            > 2147483647
        ):
            raise ValueError("Authored source rational resource bound")
        return self


class HierarchyDirectionPolicy(_HierarchyContract):
    source_kind: TargetKind
    destination_kind: TargetKind
    enabled: Annotated[bool, Field(strict=True)]
    support_modes: tuple[SupportMode, ...]
    rows: tuple[HierarchyTransferMapRow, ...]
    attenuation: HierarchyPolicyAmount | None

    @model_validator(mode="after")
    def direction(self):
        rows = unique_sorted(self.rows, key=lambda r: r.source_affinity_value)
        modes = unique_sorted(self.support_modes)
        kinds = {self.source_kind, self.destination_kind}
        classification_shape = kinds == {"INGREDIENT", "PROTEIN"} or (
            "DIRECT_RECIPE" in kinds
            and len(kinds) == 2
            and bool(kinds & {"PROTEIN", "METHOD", "FLAVOR"})
        )
        if "CLASSIFICATION_BOUND_PAIR" in modes and not classification_shape:
            raise ValueError("Classification-bound direction shape prohibited")
        if self.enabled:
            if not rows or not modes or self.attenuation is None or self.attenuation.numerator <= 0:
                raise ValueError(
                    "Enabled direction requires explicit map, modes and positive attenuation"
                )
        elif rows or modes or self.attenuation is not None:
            raise ValueError("Denied direction cannot carry transfer data")
        order = {"DISLIKE": 0, "NEUTRAL": 1, "LIKE": 2}
        semantic = sorted(rows, key=lambda r: order[r.source_affinity_value])
        if any(
            Fraction(a.output_amount.numerator, a.output_amount.denominator)
            >= Fraction(b.output_amount.numerator, b.output_amount.denominator)
            for a, b in zip(semantic, semantic[1:])
        ):
            raise ValueError("Transfer map must preserve strict semantic ordering")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "support_modes", modes)
        return self


class HierarchyTransferPolicy(_HierarchyContract):
    contract_version: Literal["hierarchy-transfer-policy.v1"] = "hierarchy-transfer-policy.v1"
    policy_id: UUID
    policy_version: Annotated[int, Field(strict=True, gt=0, le=2147483647)]
    explicit_policy: ExplicitTargetAffinityPolicy
    compatibility_policy: ExactTargetPriorCompatibilityPolicy
    directions: Annotated[tuple[HierarchyDirectionPolicy, ...], Field(min_length=25, max_length=25)]
    provenance: HierarchyProvenance
    traversal: Literal["ONE_HOP_NO_INHERITED_PARENTS"] = "ONE_HOP_NO_INHERITED_PARENTS"
    multiple_parents: Literal["UNAVAILABLE_NO_AGGREGATION"] = "UNAVAILABLE_NO_AGGREGATION"
    precedence: Literal["DIRECT_DECLARATION_WINS_RETRACTION_SUPPRESSES"] = (
        "DIRECT_DECLARATION_WINS_RETRACTION_SUPPRESSES"
    )
    source_values: Literal["CURRENT_MAPPED_EXPLICIT_ONLY"] = "CURRENT_MAPPED_EXPLICIT_ONLY"
    policy_ownership: Literal["HIERARCHY_COMPATIBILITY_REPLAY_ONLY"] = (
        "HIERARCHY_COMPATIBILITY_REPLAY_ONLY"
    )

    @model_validator(mode="after")
    def pinned_semantics(self):
        e, c = self.explicit_policy, self.compatibility_policy
        if (c.explicit_policy_id, c.explicit_policy_version, c.explicit_policy_fingerprint) != (
            e.policy_id,
            e.policy_version,
            _profile_hash(e),
        ):
            raise ValueError("Frozen explicit policy binding differs")
        directions = unique_sorted(
            self.directions, key=lambda d: (d.source_kind, d.destination_kind)
        )
        if {(d.source_kind, d.destination_kind) for d in directions} != {
            (a, b) for a in KINDS for b in KINDS
        }:
            raise ValueError("Closed full 5x5 matrix required")
        for group in c.explicit_maps:
            rules = next(
                g.affinity_rules for g in e.target_policies if g.target_kind == group.target_kind
            )
            for rule in group.rows:
                expected = next(r.amount for r in rules if r.value == rule.value)
                if rule.expected_explicit_amount != expected:
                    raise ValueError(
                        "Frozen compatibility explicit semantic/amount binding differs"
                    )
        for direction in directions:
            frozen = next(g for g in e.target_policies if g.target_kind == direction.source_kind)
            for row in direction.rows:
                expected = next(
                    r.amount for r in frozen.affinity_rules if r.value == row.source_affinity_value
                )
                if (
                    row.expected_source_amount != expected
                    or row.source_descriptor != c.coordinate_for(direction.source_kind)
                ):
                    raise ValueError(
                        "Transfer semantic state/expected frozen amount or descriptor differs"
                    )
        object.__setattr__(self, "directions", directions)
        return self

    @model_validator(mode="before")
    @classmethod
    def raw_authored_resources(cls, value):
        def check(item):
            if isinstance(item, dict):
                if "numerator" in item and "denominator" in item:
                    n, d = item["numerator"], item["denominator"]
                    if type(n) is not int or type(d) is not int or max(abs(n), abs(d)) > 2147483647:
                        raise ValueError("Strict bounded authored rational components required")
                for child in item.values():
                    check(child)
            elif isinstance(item, (list, tuple)):
                for child in item:
                    check(child)

        value = canonical(value)
        check(value)
        return value

    def fingerprint(self):
        return hierarchy_hash("hierarchy.transfer-policy.v1", self)


class HierarchyMappingLookup(_HierarchyContract):
    status: Literal["AVAILABLE", "SOURCE_VALUE_NOT_MAPPED", "DIRECTION_DENIED"]
    row: HierarchyTransferMapRow | None


def lookup_hierarchy_policy_row(policy, source_kind, destination_kind, semantic_state):
    """Authored policy lookup only: no member input, arithmetic or derived affinity."""
    policy = HierarchyTransferPolicy.model_validate(canonical(policy))
    if (
        source_kind not in KINDS
        or destination_kind not in KINDS
        or semantic_state not in {"LIKE", "NEUTRAL", "DISLIKE"}
    ):
        raise ValueError("Unknown kind/semantic state")
    direction = next(
        d
        for d in policy.directions
        if (d.source_kind, d.destination_kind) == (source_kind, destination_kind)
    )
    row = next((r for r in direction.rows if r.source_affinity_value == semantic_state), None)
    return HierarchyMappingLookup(
        status="DIRECTION_DENIED"
        if not direction.enabled
        else "AVAILABLE"
        if row
        else "SOURCE_VALUE_NOT_MAPPED",
        row=row,
    )


class HierarchyRecipeBinding(_HierarchyContract):
    endpoint: Literal["SOURCE", "DESTINATION"]
    recipe_version_id: UUID
    key: CulinaryFeatureApplicabilityKey | None
    path: FeatureSelectedPath | None

    @model_validator(mode="after")
    def exact_context(self):
        if self.key is not None and self.key.recipe_version_id != self.recipe_version_id:
            raise ValueError("Recipe context/version mismatch")
        if self.key is None and self.path is not None:
            raise ValueError("No implicit recipe path")
        if self.key is not None and ((self.key.dimension == "METHOD") != (self.path is None)):
            raise ValueError("METHOD forbids path; FLAVOR/MAIN_PROTEIN requires explicit path")
        return self


class HierarchyStreamIdentity(_HierarchyContract):
    kind: Literal["POLICY", "RELATION"]
    policy_id: UUID
    source: PreferenceTarget | None
    destination: PreferenceTarget | None
    recipe_bindings: tuple[HierarchyRecipeBinding, ...]

    @model_validator(mode="after")
    def exact_endpoints(self):
        bindings = unique_sorted(self.recipe_bindings, key=lambda b: b.endpoint)
        if self.kind == "POLICY":
            if self.source is not None or self.destination is not None or bindings:
                raise ValueError("Policy stream has no endpoints")
        else:
            if self.source is None or self.destination is None or self.source == self.destination:
                raise ValueError("Exact distinct relation endpoints required; no self-edge")
            expected = {
                name
                for name, t in (("SOURCE", self.source), ("DESTINATION", self.destination))
                if t.kind == "DIRECT_RECIPE"
            }
            if {b.endpoint for b in bindings} != expected:
                raise ValueError("Every DIRECT_RECIPE endpoint requires explicit version binding")
        object.__setattr__(self, "recipe_bindings", bindings)
        return self

    def key(self):
        return hierarchy_hash("hierarchy.stream.v1", self)


class HierarchyRelationBody(_HierarchyContract):
    policy_revision_id: UUID
    policy_fingerprint: Sha256
    support_mode: SupportMode
    support_review_id: UUID | None
    catalog_review_ids: tuple[UUID, ...]

    @model_validator(mode="after")
    def support(self):
        object.__setattr__(self, "catalog_review_ids", unique_sorted(self.catalog_review_ids))
        if self.support_mode == "REVIEWED_EXACT_PAIR" and (
            self.support_review_id is not None or self.catalog_review_ids
        ):
            raise ValueError("Exact pair makes no classification claim")
        if self.support_mode == "CLASSIFICATION_BOUND_PAIR" and self.support_review_id is None:
            raise ValueError("Classification-bound relation requires exact support review")
        return self


class HierarchyPublicationCommand(_HierarchyContract):
    provider_id: UUID
    identity: HierarchyStreamIdentity
    operation: Literal["REPLACE", "RETRACT"]
    policy: HierarchyTransferPolicy | None
    relation: HierarchyRelationBody | None
    provenance: HierarchyProvenance
    review_rationale: Reason
    expected_provider_generation: Counter
    expected_mutation_head_hash: Sha256 | None
    expected_revision: ExpectedRevision
    predecessor_id: UUID | None
    idempotency_key: Identifier

    @model_validator(mode="after")
    def publication_shape(self):
        if (self.expected_revision == -1) != (self.predecessor_id is None):
            raise ValueError("Exact expected revision/predecessor required")
        if self.operation == "RETRACT":
            if self.policy is not None or self.relation is not None or self.expected_revision < 0:
                raise ValueError("Retraction is a payload-free tombstone")
        elif self.identity.kind == "POLICY":
            if (
                self.policy is None
                or self.relation is not None
                or self.policy.policy_id != self.identity.policy_id
            ):
                raise ValueError("Complete policy publication required")
        elif self.relation is None or self.policy is not None:
            raise ValueError("Complete exact relation publication required")
        return self


class HierarchyTargetIdentity(_HierarchyContract):
    target: PreferenceTarget
    identity: IngredientIdentityFact | RecipeFact | AffinityFeatureTermFact

    @model_validator(mode="after")
    def owner_identity(self):
        t, i = self.target, self.identity
        valid = (
            (
                isinstance(i, IngredientIdentityFact)
                and t.kind == "INGREDIENT"
                and i.id == t.ingredient_id
            )
            or (isinstance(i, RecipeFact) and t.kind == "DIRECT_RECIPE" and i.id == t.recipe_id)
            or (
                isinstance(i, AffinityFeatureTermFact)
                and t.kind == i.kind
                and i.id == t.feature_term_id
                and i.status == "REVIEWED"
            )
        )
        if not valid:
            raise ValueError("TARGET_IDENTITY_UNRESOLVED / TARGET_NOT_REVIEWED")
        return self


class HierarchyOwnerManifest(_HierarchyContract):
    identities: tuple[HierarchyTargetIdentity, ...]
    catalog_frontier: Counter
    catalog_streams: tuple[IngredientProteinStreamFact, ...]
    recipe_frontier: Counter
    recipes: tuple[RecipeVersionSnapshot, ...]
    scopes: tuple[CulinaryFeatureScopeFact, ...]
    terms: tuple[AffinityFeatureTermFact, ...]

    @model_validator(mode="after")
    def source_sets(self):
        for field, key in (
            ("identities", lambda i: target_key(i.target)),
            ("catalog_streams", lambda i: str(i.ingredient_id)),
            ("recipes", lambda i: str(i.id)),
            ("scopes", lambda i: str(i.id)),
            ("terms", lambda i: str(i.id)),
        ):
            object.__setattr__(self, field, unique_sorted(getattr(self, field), key=key))
        if any(
            r.source_sequence > self.catalog_frontier
            for s in self.catalog_streams
            for r in s.reviews
        ):
            raise ValueError("Catalog review outside captured frontier")
        if any(r.source_sequence > self.recipe_frontier for s in self.scopes for r in s.reviews):
            raise ValueError("Recipe review outside captured frontier")
        reviews = [r for stream in self.catalog_streams for r in stream.reviews]
        if len(reviews) != self.catalog_frontier or {r.source_sequence for r in reviews} != set(
            range(1, len(reviews) + 1)
        ):
            raise ValueError("Incomplete complete Catalog source frontier")
        terms = {t.id: t for t in self.terms}
        for review in reviews:
            for term_id in review.command.covered_term_ids:
                term = terms.get(term_id)
                if (
                    term is None
                    or term.kind != "PROTEIN"
                    or term.status != "REVIEWED"
                    or term.provenance.observed_at > review.recorded_at
                ):
                    raise ValueError("Catalog support vocabulary manifest differs")
        for entry in self.identities:
            if (
                entry.target.kind in {"PROTEIN", "METHOD", "FLAVOR"}
                and terms.get(entry.identity.id) != entry.identity
            ):
                raise ValueError("Endpoint vocabulary differs from source manifest")
        return self


class HierarchyOwnerPin(_HierarchyContract):
    kind: Literal["CATALOG_STREAM", "RECIPE_VERSION", "RECIPE_SCOPE", "FEATURE_TERM"]
    id: UUID
    fingerprint: Sha256


class HierarchyOwnerPins(_HierarchyContract):
    catalog_frontier: Counter
    recipe_frontier: Counter
    targets: tuple[PreferenceTarget, ...]
    facts: tuple[HierarchyOwnerPin, ...]

    @model_validator(mode="after")
    def canonical_pins(self):
        object.__setattr__(self, "targets", unique_sorted(self.targets, key=target_key))
        object.__setattr__(
            self, "facts", unique_sorted(self.facts, key=lambda p: (p.kind, str(p.id)))
        )
        return self


def hierarchy_owner_pins(owner):
    owner = HierarchyOwnerManifest.model_validate(canonical(owner))
    facts = []
    for kind, rows in (
        ("CATALOG_STREAM", owner.catalog_streams),
        ("RECIPE_VERSION", owner.recipes),
        ("RECIPE_SCOPE", owner.scopes),
        ("FEATURE_TERM", owner.terms),
    ):
        facts.extend(
            HierarchyOwnerPin(kind=kind, id=r.id, fingerprint=identity_hash(r)) for r in rows
        )
    return HierarchyOwnerPins(
        catalog_frontier=owner.catalog_frontier,
        recipe_frontier=owner.recipe_frontier,
        targets=tuple(i.target for i in owner.identities),
        facts=tuple(facts),
    )


class HierarchyAuthorityEvent(_HierarchyContract):
    id: UUID
    command: HierarchyAuthorityCommand
    administrator: HierarchySessionFact
    recorded_at: AwareTime
    authority_sequence: Sequence
    mutation_sequence: Sequence
    command_hash: Sha256
    fact_hash: Sha256

    def expected_hash(self):
        return hierarchy_hash("hierarchy.authority.v1", self.model_dump(exclude={"fact_hash"}))

    @model_validator(mode="after")
    def hashes(self):
        if (
            self.command_hash != hierarchy_hash("hierarchy.authority-command.v1", self.command)
            or self.fact_hash != self.expected_hash()
        ):
            raise ValueError("Authority content hash differs")
        return self


class HierarchyRevisionFact(_HierarchyContract):
    id: UUID
    stream_id: UUID
    command: HierarchyPublicationCommand
    owner_source: HierarchyOwnerManifest
    owner_pins: HierarchyOwnerPins
    principal_id: UUID
    session: HierarchySessionFact
    grant_event_id: UUID
    authority_generation: Counter
    revision: Revision
    source_sequence: Sequence
    mutation_sequence: Sequence
    recorded_at: AwareTime
    effective_at: AwareTime
    command_hash: Sha256
    fact_hash: Sha256

    def expected_hash(self):
        return hierarchy_hash(
            "hierarchy.publication.v1", self.model_dump(exclude={"fact_hash", "owner_source"})
        )

    @model_validator(mode="after")
    def hashes(self):
        if (
            self.owner_pins != hierarchy_owner_pins(self.owner_source)
            or self.recorded_at != self.effective_at
            or self.command.provenance.observed_at > self.recorded_at
            or self.revision != self.command.expected_revision + 1
            or self.command_hash != hierarchy_hash("hierarchy.publication-command.v1", self.command)
            or self.fact_hash != self.expected_hash()
        ):
            raise ValueError("Publication identity/time/hash differs")
        required_targets = {
            target_key(t)
            for t in (self.command.identity.source, self.command.identity.destination)
            if t is not None
        }
        if {target_key(t) for t in self.owner_pins.targets} != required_targets or {
            r.id for r in self.owner_source.recipes
        } != {b.recipe_version_id for b in self.command.identity.recipe_bindings}:
            raise ValueError("Publication owner pins differ from exact endpoints/context")
        return self


class HierarchyMutationFact(_HierarchyContract):
    provider_id: UUID
    mutation_sequence: Sequence
    kind: Literal["AUTHORITY", "PUBLICATION"]
    child_id: UUID
    child_hash: Sha256
    predecessor_hash: Sha256 | None
    recorded_at: AwareTime
    journal_hash: Sha256

    def expected_hash(self):
        return hierarchy_hash("hierarchy.mutation.v1", self.model_dump(exclude={"journal_hash"}))

    @model_validator(mode="after")
    def journal_identity(self):
        if self.journal_hash != self.expected_hash():
            raise ValueError("Mutation hash differs")
        return self


class HierarchyStreamFact(_HierarchyContract):
    id: UUID
    provider_id: UUID
    identity: HierarchyStreamIdentity
    head_id: UUID
    head_revision: Revision


class HierarchyFrontier(_HierarchyContract):
    provider_id: UUID
    source_generation: Counter
    authority_generation: Counter
    mutation_generation: Counter
    source_head_id: UUID | None
    authority_head_id: UUID | None
    mutation_head_hash: Sha256 | None

    @model_validator(mode="after")
    def generations_and_heads(self):
        if (
            self.mutation_generation != self.source_generation + self.authority_generation
            or (self.source_generation == 0) != (self.source_head_id is None)
            or (self.authority_generation == 0) != (self.authority_head_id is None)
            or (self.mutation_generation == 0) != (self.mutation_head_hash is None)
        ):
            raise ValueError("Frontier generation/head identity differs")
        return self


class HierarchyWriteReceipt(_HierarchyContract):
    publication: HierarchyRevisionFact
    mutation: HierarchyMutationFact
    frontier: HierarchyFrontier
    commit_status: Literal["CALLER_TRANSACTION_NOT_CERTIFIED"] = "CALLER_TRANSACTION_NOT_CERTIFIED"

    @model_validator(mode="after")
    def child_journal_frontier(self):
        p, m, f = self.publication, self.mutation, self.frontier
        if (
            m.kind != "PUBLICATION"
            or m.child_id != p.id
            or m.child_hash != p.fact_hash
            or m.recorded_at != p.recorded_at
            or m.mutation_sequence != p.mutation_sequence
            or m.provider_id != p.command.provider_id
            or f.provider_id != m.provider_id
            or f.source_head_id != p.id
            or f.source_generation != p.source_sequence
            or f.authority_generation != p.authority_generation
            or f.mutation_generation != m.mutation_sequence
            or f.mutation_head_hash != m.journal_hash
        ):
            raise ValueError("Write receipt child/journal/frontier differs")
        return self


class HierarchyCaptureRequest(_HierarchyContract):
    provider_id: UUID
    policy_id: UUID
    requested_targets: tuple[PreferenceTarget, ...]

    @field_validator("requested_targets")
    @classmethod
    def exact_targets(cls, values):
        return unique_sorted(values, key=target_key)


class HierarchySourceSnapshotDraft(_HierarchyContract):
    contract_version: Literal["hierarchy-source.v1-draft"] = "hierarchy-source.v1-draft"
    request: HierarchyCaptureRequest
    provider: HierarchyProviderFact
    principals: tuple[HierarchyPrincipalFact, ...]
    authority_events: tuple[HierarchyAuthorityEvent, ...]
    publications: tuple[HierarchyRevisionFact, ...]
    mutations: tuple[HierarchyMutationFact, ...]
    streams: tuple[HierarchyStreamFact, ...]
    frontier: HierarchyFrontier
    owner_source: HierarchyOwnerManifest
    reader_principal_id: UUID
    reader_session: HierarchySessionFact
    reader_grant_id: UUID
    capture_started_at: AwareTime
    capture_completed_at: AwareTime
    isolation: Literal["REPEATABLE READ", "SERIALIZABLE"]
    read_only: Literal[True] = True

    @model_validator(mode="after")
    def coherent_source(self):
        from app.modules.preferences.hierarchy_resolution import validate_hierarchy_source

        for field, key in (
            ("principals", lambda p: str(p.id)),
            ("authority_events", lambda p: p.authority_sequence),
            ("publications", lambda p: p.source_sequence),
            ("mutations", lambda p: p.mutation_sequence),
            ("streams", lambda p: p.identity.key()),
        ):
            object.__setattr__(self, field, unique_sorted(getattr(self, field), key=key))
        validate_hierarchy_source(self)
        return self

    def fingerprint(self):
        return hierarchy_hash("hierarchy.source.v1", self)


HierarchySourceReason = Literal[
    "NO_RELATION",
    "RELATION_RETRACTED",
    "DIRECTION_DENIED",
    "POLICY_MISSING",
    "POLICY_RETRACTED",
    "POLICY_SUPERSEDED",
    "MULTIPLE_INCOMING_RELATIONS",
    "SUPPORT_UNRESOLVED",
    "SUPPORT_SUPERSEDED",
    "SUPPORT_RETRACTED",
    "SUPPORT_REVIEWED_NONE",
    "SUPPORT_REVIEWED_ABSENT",
]


class HierarchyRelationDiagnostic(_HierarchyContract):
    publication_id: UUID
    retracted: Annotated[bool, Field(strict=True)]
    policy_reason: (
        Literal["POLICY_MISSING", "POLICY_RETRACTED", "POLICY_SUPERSEDED", "DIRECTION_DENIED"]
        | None
    )
    support_status: (
        Literal[
            "SUPPORT_UNRESOLVED",
            "SUPPORT_SUPERSEDED",
            "SUPPORT_RETRACTED",
            "SUPPORT_REVIEWED_NONE",
            "SUPPORT_REVIEWED_ABSENT",
        ]
        | None
    )
    support_reason: str | None


class HierarchyDestinationSource(_HierarchyContract):
    target: PreferenceTarget
    status: Literal["ELIGIBLE_RELATION", "UNAVAILABLE"]
    reason: HierarchySourceReason | None
    policy: HierarchyRevisionFact | None
    relations: tuple[HierarchyRevisionFact, ...]
    selected_relation: HierarchyRevisionFact | None
    support_reason: str | None
    diagnostics: tuple[HierarchyRelationDiagnostic, ...]


class ReviewedHierarchySourceDraft(_HierarchyContract):
    contract_version: Literal["reviewed-hierarchy-source.v1-draft"] = (
        "reviewed-hierarchy-source.v1-draft"
    )
    source: HierarchySourceSnapshotDraft
    rows: tuple[HierarchyDestinationSource, ...]
    source_fingerprint: Sha256
    result_fingerprint: Sha256
    scope: Literal["ONE_PROVIDER_ONE_POLICY_EXACT_RELATIONS_ONLY"] = (
        "ONE_PROVIDER_ONE_POLICY_EXACT_RELATIONS_ONLY"
    )
    member_affinity: Literal["NOT_DERIVED"] = "NOT_DERIVED"
    evidence_strength: Literal["NOT_DERIVED"] = "NOT_DERIVED"
    member_preference_data: Literal["NOT_MODIFIED"] = "NOT_MODIFIED"
    learned_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    recursive_transfer: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    parent_aggregation: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False

    @model_validator(mode="after")
    def primitive_replay(self):
        from app.modules.preferences.hierarchy_resolution import hierarchy_rows

        if (
            self.rows != hierarchy_rows(self.source)
            or self.source_fingerprint != self.source.fingerprint()
            or self.result_fingerprint
            != hierarchy_hash("hierarchy.resolution.v1", dict(source=self.source, rows=self.rows))
        ):
            raise ValueError("Hierarchy result differs from primitive replay")
        return self
