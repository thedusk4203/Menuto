"""Global reviewed reference source, separate from member declarations and learned evidence."""

from math import gcd
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.domain.contracts import AwareTime, Contract, Identifier, Sha256
from app.domain.feature_identity import canonical, identity_hash, unique_sorted
from app.domain.units import Provenance
from app.modules.catalog.contracts import AffinityFeatureTermFact, IngredientIdentityFact
from app.modules.preferences.contracts import PreferenceTarget
from app.modules.recipes.contracts import RecipeFact

Counter = Annotated[int, Field(strict=True, ge=0, le=9_223_372_036_854_775_807)]
Sequence = Annotated[int, Field(strict=True, gt=0, le=9_223_372_036_854_775_807)]
Revision = Annotated[int, Field(strict=True, ge=0, le=2_147_483_647)]
ExpectedRevision = Annotated[int, Field(strict=True, ge=-1, le=2_147_483_647)]
Oid = Annotated[int, Field(strict=True, gt=0, le=4_294_967_295)]
Reason = Annotated[str, Field(min_length=1, max_length=4000, pattern=r"\S")]
PgName = Annotated[str, Field(min_length=1, max_length=63, pattern=r"^[^\x00-\x1f\x7f]+$")]
Capability = Literal["REVIEW_PUBLISH", "RETRACT", "CAPTURE"]


class _ReferenceContract(Contract):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True, revalidate_instances="always"
    )

    @field_validator(
        "read_only", "planner_ready", "activation_ready", mode="before", check_fields=False
    )
    @classmethod
    def strict_flags(cls, value):
        if type(value) is not bool:
            raise ValueError("Flags require JSON booleans")
        return value


def prior_hash(domain, value):
    return identity_hash({"domain": domain, "value": value})


def target_key(target):
    return identity_hash(target)


class ReferencePriorCoordinate(_ReferenceContract):
    coordinate_id: Literal["CURATED_REFERENCE_PREFERENCE"] = "CURATED_REFERENCE_PREFERENCE"
    coordinate_version: Literal[1] = 1
    unit: Literal["REVIEWED_REFERENCE_ANCHOR_UNITS"] = "REVIEWED_REFERENCE_ANCHOR_UNITS"
    applicability: Literal["GLOBAL_REFERENCE_ONLY"] = "GLOBAL_REFERENCE_ONLY"

    @field_validator("coordinate_version", mode="before")
    @classmethod
    def integer_version(cls, value):
        if type(value) is not int:
            raise ValueError("Coordinate version must be an integer")
        return value


class ReferencePriorAmount(_ReferenceContract):
    numerator: Annotated[int, Field(strict=True, ge=-2_147_483_647, le=2_147_483_647)]
    denominator: Annotated[int, Field(strict=True, gt=0, le=2_147_483_647)]
    unit: Literal["REVIEWED_REFERENCE_ANCHOR_UNITS"] = "REVIEWED_REFERENCE_ANCHOR_UNITS"

    @model_validator(mode="after")
    def exact_reference(self):
        if (
            abs(self.numerator) > self.denominator
            or gcd(abs(self.numerator), self.denominator) != 1
        ):
            raise ValueError("Reference prior must be a reduced exact rational in [-1,1]")
        return self


class ReferencePriorProvenance(Provenance):
    kind: Literal["REVIEWED_REFERENCE"] = "REVIEWED_REFERENCE"
    content_hash: Sha256


class ReferencePriorSessionFact(_ReferenceContract):
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


class ReferencePriorProviderCommand(_ReferenceContract):
    code: Identifier
    version: Identifier
    source_system: Identifier
    remit: Reason
    coordinate: ReferencePriorCoordinate = ReferencePriorCoordinate()
    idempotency_key: Identifier


class ReferencePriorPrincipalCommand(_ReferenceContract):
    role_name: PgName
    idempotency_key: Identifier


class ReferencePriorProviderFact(_ReferenceContract):
    id: UUID
    command: ReferencePriorProviderCommand
    administrator: ReferencePriorSessionFact
    recorded_at: AwareTime
    command_hash: Sha256

    @model_validator(mode="after")
    def command_identity(self):
        if self.command_hash != prior_hash("prior.provider-command.v1", self.command):
            raise ValueError("Provider registration command hash differs")
        return self


class ReferencePriorPrincipalFact(_ReferenceContract):
    id: UUID
    command: ReferencePriorPrincipalCommand
    database_oid: Oid
    database_name: PgName
    role_oid: Oid
    role_name: PgName
    administrator: ReferencePriorSessionFact
    recorded_at: AwareTime
    command_hash: Sha256

    @model_validator(mode="after")
    def binding(self):
        if (
            self.role_name != self.command.role_name
            or (self.database_oid, self.database_name)
            != (self.administrator.database_oid, self.administrator.database_name)
            or self.command_hash != prior_hash("prior.principal-command.v1", self.command)
        ):
            raise ValueError("Principal enrollment binding differs")
        return self


class ReferencePriorAuthorityCommand(_ReferenceContract):
    provider_id: UUID
    principal_id: UUID
    capability: Capability
    action: Literal["GRANT", "REVOKE"]
    expected_authority_generation: Counter
    reason: Reason
    idempotency_key: Identifier


class ReferencePriorPublishCommand(_ReferenceContract):
    operation: Literal["REPLACE"] = "REPLACE"
    provider_id: UUID
    target: PreferenceTarget
    coordinate: ReferencePriorCoordinate = ReferencePriorCoordinate()
    amount: ReferencePriorAmount
    provenance: ReferencePriorProvenance
    review_rationale: Reason
    expected_provider_generation: Counter
    expected_revision: ExpectedRevision
    predecessor_id: UUID | None
    idempotency_key: Identifier

    @model_validator(mode="after")
    def initial_head(self):
        if (self.expected_revision == -1) != (self.predecessor_id is None):
            raise ValueError("Exact predecessor required; initial publication uses revision -1")
        return self


class ReferencePriorRetractCommand(_ReferenceContract):
    operation: Literal["RETRACT"] = "RETRACT"
    provider_id: UUID
    target: PreferenceTarget
    coordinate: ReferencePriorCoordinate = ReferencePriorCoordinate()
    provenance: ReferencePriorProvenance
    review_rationale: Reason
    expected_provider_generation: Counter
    expected_revision: Revision
    predecessor_id: UUID
    idempotency_key: Identifier


PublicationCommand = Annotated[
    ReferencePriorPublishCommand | ReferencePriorRetractCommand, Field(discriminator="operation")
]


class ReferencePriorAuthorityEvent(_ReferenceContract):
    id: UUID
    command: ReferencePriorAuthorityCommand
    administrator: ReferencePriorSessionFact
    recorded_at: AwareTime
    authority_sequence: Sequence
    mutation_sequence: Sequence
    command_hash: Sha256
    fact_hash: Sha256

    def expected_hash(self):
        return prior_hash("prior.authority.v1", self.model_dump(exclude={"fact_hash"}))

    @model_validator(mode="after")
    def hashes(self):
        if (
            self.command_hash != prior_hash("prior.authority-command.v1", self.command)
            or self.fact_hash != self.expected_hash()
        ):
            raise ValueError("Authority content hash differs")
        return self


class ReferencePriorRevisionFact(_ReferenceContract):
    id: UUID
    stream_id: UUID
    command: PublicationCommand
    principal_id: UUID
    session: ReferencePriorSessionFact
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
        return prior_hash("prior.publication.v1", self.model_dump(exclude={"fact_hash"}))

    @model_validator(mode="after")
    def hashes(self):
        if (
            self.recorded_at != self.effective_at
            or self.command.provenance.observed_at > self.recorded_at
            or self.revision != self.command.expected_revision + 1
            or self.command_hash != prior_hash("prior.publication-command.v1", self.command)
            or self.fact_hash != self.expected_hash()
        ):
            raise ValueError("Publication identity/time/hash differs")
        return self


class ReferencePriorMutationFact(_ReferenceContract):
    provider_id: UUID
    mutation_sequence: Sequence
    kind: Literal["AUTHORITY", "PUBLICATION"]
    child_id: UUID
    child_hash: Sha256
    predecessor_hash: Sha256 | None
    recorded_at: AwareTime
    journal_hash: Sha256

    def expected_hash(self):
        return prior_hash("prior.mutation.v1", self.model_dump(exclude={"journal_hash"}))

    @model_validator(mode="after")
    def journal_identity(self):
        if self.journal_hash != self.expected_hash():
            raise ValueError("Mutation hash differs")
        return self


class ReferencePriorStreamFact(_ReferenceContract):
    id: UUID
    provider_id: UUID
    target: PreferenceTarget
    head_id: UUID
    head_revision: Revision


class ReferencePriorFrontier(_ReferenceContract):
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


class ReferencePriorWriteReceipt(_ReferenceContract):
    publication: ReferencePriorRevisionFact
    mutation: ReferencePriorMutationFact
    frontier: ReferencePriorFrontier
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


class ReferencePriorCaptureRequest(_ReferenceContract):
    provider_id: UUID
    requested_targets: tuple[PreferenceTarget, ...]
    coordinate: ReferencePriorCoordinate = ReferencePriorCoordinate()

    @field_validator("requested_targets")
    @classmethod
    def targets(cls, values):
        return unique_sorted(values, key=target_key)


class ReferencePriorTargetIdentity(_ReferenceContract):
    target: PreferenceTarget
    identity: IngredientIdentityFact | RecipeFact | AffinityFeatureTermFact

    @model_validator(mode="after")
    def exact_owner(self):
        t, i = self.target, self.identity
        if t.kind == "INGREDIENT":
            valid = isinstance(i, IngredientIdentityFact) and t.ingredient_id == i.id
        elif t.kind == "DIRECT_RECIPE":
            valid = isinstance(i, RecipeFact) and t.recipe_id == i.id
        else:
            valid = (
                isinstance(i, AffinityFeatureTermFact)
                and t.feature_term_id == i.id
                and t.kind == i.kind
                and i.status == "REVIEWED"
            )
        if not valid:
            raise ValueError("TARGET_IDENTITY_UNRESOLVED or TARGET_NOT_REVIEWED")
        return self


class ReferencePriorSourceSnapshotDraft(_ReferenceContract):
    contract_version: Literal["reference-prior-source.v1-draft"] = "reference-prior-source.v1-draft"
    request: ReferencePriorCaptureRequest
    provider: ReferencePriorProviderFact
    principals: tuple[ReferencePriorPrincipalFact, ...]
    authority_events: tuple[ReferencePriorAuthorityEvent, ...]
    publications: tuple[ReferencePriorRevisionFact, ...]
    mutations: tuple[ReferencePriorMutationFact, ...]
    streams: tuple[ReferencePriorStreamFact, ...]
    frontier: ReferencePriorFrontier
    identities: tuple[ReferencePriorTargetIdentity, ...]
    reader_principal_id: UUID
    reader_session: ReferencePriorSessionFact
    reader_grant_id: UUID
    capture_started_at: AwareTime
    capture_completed_at: AwareTime
    isolation: Literal["REPEATABLE READ", "SERIALIZABLE"]
    read_only: Literal[True] = True

    @model_validator(mode="before")
    @classmethod
    def recursive_primitives(cls, value):
        return canonical(value)

    @model_validator(mode="after")
    def validate_source(self):
        for field, key in (
            ("principals", lambda v: str(v.id)),
            ("authority_events", lambda v: v.authority_sequence),
            ("publications", lambda v: v.source_sequence),
            ("mutations", lambda v: v.mutation_sequence),
            ("streams", lambda v: target_key(v.target)),
            ("identities", lambda v: target_key(v.target)),
        ):
            object.__setattr__(self, field, unique_sorted(getattr(self, field), key=key))
        validate_reference_source(self)
        return self

    def fingerprint(self):
        return prior_hash("preference-prior-source.v1", self)


class AvailableReviewedReferencePrior(_ReferenceContract):
    status: Literal["AVAILABLE"] = "AVAILABLE"
    target: PreferenceTarget
    provider_id: UUID
    coordinate: ReferencePriorCoordinate
    publication: ReferencePriorRevisionFact
    amount: ReferencePriorAmount


class UnavailableReviewedReferencePrior(_ReferenceContract):
    status: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    reason: Literal["NO_PUBLICATION", "RETRACTED"]
    target: PreferenceTarget
    provider_id: UUID
    tombstone: ReferencePriorRevisionFact | None


PriorRow = Annotated[
    AvailableReviewedReferencePrior | UnavailableReviewedReferencePrior,
    Field(discriminator="status"),
]


class ReviewedReferencePriorDraft(_ReferenceContract):
    contract_version: Literal["reviewed-reference-prior.v1-draft"] = (
        "reviewed-reference-prior.v1-draft"
    )
    source: ReferencePriorSourceSnapshotDraft
    rows: tuple[PriorRow, ...]
    source_fingerprint: Sha256
    result_fingerprint: Sha256
    scope: Literal["ONE_EXPLICIT_PROVIDER_EXACT_TARGET_REFERENCE_ONLY"] = (
        "ONE_EXPLICIT_PROVIDER_EXACT_TARGET_REFERENCE_ONLY"
    )
    interpretation_mode: Literal["AS_OF_CAPTURE"] = "AS_OF_CAPTURE"
    member_preference_data: Literal["NOT_MODIFIED"] = "NOT_MODIFIED"
    evidence_strength: Literal["NOT_DERIVED"] = "NOT_DERIVED"
    learned_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    contextual_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    passive_evidence: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    cross_target_inference: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    provider_aggregation: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    coordinate_conversion: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    shrinkage: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    candidate_aggregation: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    taste_fit: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    planner_ready: Literal[False] = False
    activation_ready: Literal[False] = False

    @model_validator(mode="before")
    @classmethod
    def recursive_primitives(cls, value):
        return canonical(value)

    @model_validator(mode="after")
    def recompute(self):
        if (
            self.rows != reference_rows(self.source)
            or self.source_fingerprint != self.source.fingerprint()
            or self.result_fingerprint
            != prior_hash("reviewed-reference-prior.v1", dict(source=self.source, rows=self.rows))
        ):
            raise ValueError("Reference result differs from source replay")
        return self


def validate_reference_source(source):
    """Rebuild the complete authority cut, journal, stream heads and consumed identities."""

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    if (
        source.request.provider_id != source.provider.id
        or source.frontier.provider_id != source.provider.id
    ):
        raise ValueError("Provider source owner differs")
    provider = source.provider
    db = (provider.administrator.database_oid, provider.administrator.database_name)
    principals = {p.id: p for p in source.principals}
    require(len(principals) == len(source.principals), "Duplicate principal")
    require(
        len({(p.database_oid, p.role_oid, p.role_name) for p in source.principals})
        == len(principals),
        "Duplicate principal binding",
    )
    for p in principals.values():
        require((p.database_oid, p.database_name) == db, "Foreign database binding")
        require(p.recorded_at <= source.capture_started_at, "Enrollment after capture")

    def binding(pid, session):
        p = principals.get(pid)
        require(p is not None, "Missing principal")
        require(
            (p.database_oid, p.database_name, p.role_oid, p.role_name)
            == (session.database_oid, session.database_name, session.role_oid, session.role_name),
            "Session is not enrolled binding",
        )
        return p

    binding(source.reader_principal_id, source.reader_session)
    require(
        provider.recorded_at <= source.capture_started_at <= source.capture_completed_at,
        "Incoherent capture clocks",
    )
    events = {e.id: e for e in source.authority_events}
    pubs = {p.id: p for p in source.publications}
    require(
        len(events) == len(source.authority_events)
        and len(pubs) == len(source.publications)
        and not events.keys() & pubs.keys(),
        "Duplicate mutation child",
    )
    require(len(source.mutations) == len(events) + len(pubs), "Incomplete mutation children")
    permissions, heads, stream_ids, used = {}, {}, {}, {source.reader_principal_id}
    source_seq = auth_seq = 0
    previous_hash = source_head = auth_head = None
    previous_time = provider.recorded_at
    seen, operations, admin_operations = set(), set(), set()
    for seq, m in enumerate(source.mutations, 1):
        require(
            m.provider_id == provider.id
            and m.mutation_sequence == seq
            and m.predecessor_hash == previous_hash,
            "Mutation gap or predecessor differs",
        )
        require(
            previous_time <= m.recorded_at <= source.capture_started_at,
            "Mutation clock regression or future mutation",
        )
        child = events.get(m.child_id) if m.kind == "AUTHORITY" else pubs.get(m.child_id)
        require(child is not None and m.child_id not in seen, "Missing or repeated typed child")
        seen.add(m.child_id)
        require(
            child.command.provider_id == provider.id
            and child.mutation_sequence == seq
            and child.recorded_at == m.recorded_at
            and child.fact_hash == m.child_hash,
            "Mutation child binding differs",
        )
        if m.kind == "AUTHORITY":
            auth_seq += 1
            require(
                child.authority_sequence == auth_seq
                and child.command.expected_authority_generation == auth_seq - 1,
                "Authority gap or CAS differs",
            )
            require(
                (child.administrator.database_oid, child.administrator.database_name) == db,
                "Administrator database differs",
            )
            p = principals.get(child.command.principal_id)
            require(p is not None and p.recorded_at <= child.recorded_at, "Missing enrollment")
            used.add(p.id)
            k = (p.id, child.command.capability)
            old = permissions.get(k)
            require(
                (old is None and child.command.action == "GRANT")
                or (old is not None and old.command.action != child.command.action),
                "Authority no-op",
            )
            op = (child.administrator.role_oid, child.command.idempotency_key)
            require(op not in admin_operations, "Duplicate authority operation")
            admin_operations.add(op)
            permissions[k] = child
            auth_head = child.id
        else:
            source_seq += 1
            c = child.command
            p = binding(child.principal_id, child.session)
            used.add(p.id)
            require(p.recorded_at <= child.recorded_at, "Publication predates enrollment")
            cap = "REVIEW_PUBLISH" if c.operation == "REPLACE" else "RETRACT"
            grant = permissions.get((p.id, cap))
            require(
                grant is not None
                and grant.command.action == "GRANT"
                and grant.id == child.grant_event_id
                and child.authority_generation == auth_seq,
                "Publication unauthorized at mutation cut",
            )
            require(
                child.source_sequence == source_seq
                and c.expected_provider_generation == source_seq - 1,
                "Source gap or CAS differs",
            )
            require(
                c.coordinate == provider.command.coordinate
                and c.provenance.source_system == provider.command.source_system,
                "Provider coordinate or provenance differs",
            )
            k = target_key(c.target)
            old = heads.get(k)
            require(
                c.predecessor_id == (old.id if old else None)
                and c.expected_revision == (old.revision if old else -1),
                "Stream lineage differs",
            )
            require(old is None or old.stream_id == child.stream_id, "Stream identity changed")
            require(
                c.operation != "RETRACT"
                or (old is not None and old.command.operation == "REPLACE"),
                "Retraction has no active predecessor",
            )
            require(
                child.stream_id not in stream_ids or stream_ids[child.stream_id] == k,
                "Stream reused for another target",
            )
            stream_ids[child.stream_id] = k
            op = (p.id, c.idempotency_key)
            require(op not in operations, "Duplicate publication operation")
            operations.add(op)
            heads[k] = child
            source_head = child.id
        previous_hash, previous_time = m.journal_hash, m.recorded_at
    require(seen == events.keys() | pubs.keys(), "Unjournaled child")
    require(used == principals.keys(), "Missing or unconsumed enrollment fact")
    grant = permissions.get((source.reader_principal_id, "CAPTURE"))
    require(
        grant is not None
        and grant.command.action == "GRANT"
        and grant.id == source.reader_grant_id,
        "Capture unauthorized at frontier",
    )
    f = source.frontier
    require(
        (
            f.source_generation,
            f.authority_generation,
            f.mutation_generation,
            f.source_head_id,
            f.authority_head_id,
            f.mutation_head_hash,
        )
        == (source_seq, auth_seq, source_seq + auth_seq, source_head, auth_head, previous_hash),
        "Incomplete source frontier",
    )
    require(len(source.streams) == len(heads), "Missing or excess stream cache")
    for s in source.streams:
        h = heads.get(target_key(s.target))
        require(
            h is not None
            and s.provider_id == provider.id
            and (s.id, s.head_id, s.head_revision) == (h.stream_id, h.id, h.revision),
            "Stream cache differs from history",
        )
    required_targets = set(heads) | {target_key(t) for t in source.request.requested_targets}
    require(
        {target_key(i.target) for i in source.identities} == required_targets,
        "Incomplete canonical target identity union",
    )


def reference_rows(source):
    heads = {target_key(s.target): s for s in source.streams}
    revisions = {p.id: p for p in source.publications}
    rows = []
    for t in source.request.requested_targets:
        head = heads.get(target_key(t))
        publication = revisions[head.head_id] if head else None
        if publication and publication.command.operation == "REPLACE":
            rows.append(
                AvailableReviewedReferencePrior(
                    target=t,
                    provider_id=source.provider.id,
                    coordinate=source.request.coordinate,
                    publication=publication,
                    amount=publication.command.amount,
                )
            )
        else:
            rows.append(
                UnavailableReviewedReferencePrior(
                    target=t,
                    provider_id=source.provider.id,
                    reason="RETRACTED" if publication else "NO_PUBLICATION",
                    tombstone=publication,
                )
            )
    return tuple(rows)
