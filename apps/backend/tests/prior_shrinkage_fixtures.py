"""Authored synthetic policies and self-consistent source cuts, never canonical DB claims."""

from datetime import timedelta
from uuid import uuid4

from app.modules.preferences import contracts as old
from app.modules.preferences import prior_affinity_contracts as c
from app.modules.preferences import reference_prior_contracts as r
from preference_fixtures import NOW, command, declaration, provenance
from target_affinity_fixtures import KINDS, entry, revision, subject


def _hashed(model, fields, field, domain):
    return model(**fields, **{field: r.prior_hash(domain, fields)})


def reference_source(target, identity, *, state="AVAILABLE", amount=(1, 2), provider=None):
    admin = r.ReferencePriorSessionFact(
        database_oid=42,
        database_name="synthetic",
        role_oid=1,
        role_name="synthetic_admin",
        authenticated_identity="synthetic_admin",
    )
    session = admin.model_copy(
        update=dict(
            role_oid=2, role_name="synthetic_reader", authenticated_identity="synthetic_reader"
        )
    )
    provider_command = r.ReferencePriorProviderCommand(
        code="synthetic.prior",
        version="1",
        source_system="synthetic.reference",
        remit="Synthetic test only",
        idempotency_key="provider",
    )
    provider = provider or r.ReferencePriorProviderFact(
        id=uuid4(),
        command=provider_command,
        administrator=admin,
        recorded_at=NOW,
        command_hash=r.prior_hash("prior.provider-command.v1", provider_command),
    )
    cmd = r.ReferencePriorPrincipalCommand(role_name=session.role_name, idempotency_key="reader")
    principal = r.ReferencePriorPrincipalFact(
        id=uuid4(),
        command=cmd,
        database_oid=42,
        database_name="synthetic",
        role_oid=2,
        role_name=session.role_name,
        administrator=admin,
        recorded_at=NOW,
        command_hash=r.prior_hash("prior.principal-command.v1", cmd),
    )
    events, mutations, publications = [], [], []

    def journal(child, kind):
        fields = dict(
            provider_id=provider.id,
            mutation_sequence=len(mutations) + 1,
            kind=kind,
            child_id=child.id,
            child_hash=child.fact_hash,
            predecessor_hash=mutations[-1].journal_hash if mutations else None,
            recorded_at=child.recorded_at,
        )
        mutations.append(
            _hashed(r.ReferencePriorMutationFact, fields, "journal_hash", "prior.mutation.v1")
        )

    for capability in ("CAPTURE", "REVIEW_PUBLISH", "RETRACT"):
        cmd = r.ReferencePriorAuthorityCommand(
            provider_id=provider.id,
            principal_id=principal.id,
            capability=capability,
            action="GRANT",
            expected_authority_generation=len(events),
            reason="Synthetic test authority",
            idempotency_key=capability,
        )
        fields = dict(
            id=uuid4(),
            command=cmd,
            administrator=admin,
            recorded_at=NOW + timedelta(seconds=len(events) + 1),
            authority_sequence=len(events) + 1,
            mutation_sequence=len(events) + 1,
            command_hash=r.prior_hash("prior.authority-command.v1", cmd),
        )
        event = _hashed(r.ReferencePriorAuthorityEvent, fields, "fact_hash", "prior.authority.v1")
        events.append(event)
        journal(event, "AUTHORITY")
    stream_id = uuid4()
    count = 0 if state == "NO_PUBLICATION" else 2 if state == "RETRACTED" else 1
    for index in range(count):
        fields = dict(
            provider_id=provider.id,
            target=target,
            provenance=r.ReferencePriorProvenance(
                source_system="synthetic.reference",
                external_record_id="review",
                source_version="1",
                content_hash="a" * 64,
                observed_at=NOW,
            ),
            review_rationale="Synthetic reviewed anchor",
            expected_provider_generation=index,
            expected_revision=index - 1,
            predecessor_id=publications[-1].id if publications else None,
            idempotency_key=f"publication.{index}",
        )
        cmd = (
            r.ReferencePriorRetractCommand(**fields)
            if index
            else r.ReferencePriorPublishCommand(
                **fields, amount=dict(numerator=amount[0], denominator=amount[1])
            )
        )
        clock = NOW + timedelta(seconds=10 + index)
        fields = dict(
            id=uuid4(),
            stream_id=stream_id,
            command=cmd,
            principal_id=principal.id,
            session=session,
            grant_event_id=events[2 if index else 1].id,
            authority_generation=3,
            revision=index,
            source_sequence=index + 1,
            mutation_sequence=len(mutations) + 1,
            recorded_at=clock,
            effective_at=clock,
            command_hash=r.prior_hash("prior.publication-command.v1", cmd),
        )
        fact = _hashed(r.ReferencePriorRevisionFact, fields, "fact_hash", "prior.publication.v1")
        publications.append(fact)
        journal(fact, "PUBLICATION")
    return r.ReferencePriorSourceSnapshotDraft(
        request=r.ReferencePriorCaptureRequest(
            provider_id=provider.id, requested_targets=(target,)
        ),
        provider=provider,
        principals=(principal,),
        authority_events=events,
        publications=publications,
        mutations=mutations,
        streams=(
            r.ReferencePriorStreamFact(
                id=stream_id,
                provider_id=provider.id,
                target=target,
                head_id=publications[-1].id,
                head_revision=count - 1,
            ),
        )
        if count
        else (),
        frontier=r.ReferencePriorFrontier(
            provider_id=provider.id,
            source_generation=count,
            authority_generation=3,
            mutation_generation=3 + count,
            source_head_id=publications[-1].id if count else None,
            authority_head_id=events[-1].id,
            mutation_head_hash=mutations[-1].journal_hash,
        ),
        identities=(r.ReferencePriorTargetIdentity(target=target, identity=identity),),
        reader_principal_id=principal.id,
        reader_session=session,
        reader_grant_id=events[0].id,
        capture_started_at=NOW + timedelta(hours=1),
        capture_completed_at=NOW + timedelta(hours=1, seconds=1),
        isolation="REPEATABLE READ",
    )


def compatibility(explicit, source):
    maps = []
    for group in explicit.policy.target_policies:
        maps.append(
            dict(
                target_kind=group.target_kind,
                rows=[
                    dict(
                        value=row.value,
                        expected_explicit_amount=row.amount,
                        output_amount=dict(
                            numerator={"DISLIKE": -3, "NEUTRAL": 1, "LIKE": 3}[row.value],
                            denominator=4,
                        ),
                    )
                    for row in group.affinity_rules
                ],
            )
        )
    return c.ExactTargetPriorCompatibilityPolicy(
        policy_id="synthetic.compatibility",
        policy_version="1",
        provenance=provenance(kind="REVIEWED_REFERENCE"),
        explicit_policy_id=explicit.policy.policy_id,
        explicit_policy_version=explicit.policy.policy_version,
        explicit_policy_fingerprint=old._profile_hash(explicit.policy),
        provider_id=source.provider.id,
        provider_command_hash=source.provider.command_hash,
        reference_coordinate=source.request.coordinate,
        explicit_maps=maps,
        reference_maps=[
            dict(
                target_kind=kind,
                rows=[
                    dict(
                        reference_amount=dict(numerator=n, denominator=d),
                        output_amount=dict(numerator=x, denominator=y),
                    )
                    for n, d, x, y in ((-1, 1, -1, 1), (0, 1, 0, 1), (1, 2, 1, 4), (1, 1, 1, 1))
                ],
            )
            for kind in KINDS
        ],
    )


def shrinkage(policy, *, weights=((1, 2), (1, 3), (0, 1)), version="1"):
    return c.ExactTargetShrinkagePolicy(
        policy_id="synthetic.shrinkage",
        policy_version=version,
        provenance=provenance(kind="REVIEWED_REFERENCE"),
        compatibility_policy_fingerprint=policy.fingerprint(),
        rules=[
            dict(level=level, prior_weight=dict(numerator=n, denominator=d))
            for level, (n, d) in zip(("LOW", "MEDIUM", "HIGH"), weights)
        ],
    )


def consumer_input(
    *,
    kind="INGREDIENT",
    member="DECLARED",
    prior="AVAILABLE",
    amount=(1, 2),
    value="LIKE",
    strength="LOW",
):
    field = {"INGREDIENT": "ingredient_id", "DIRECT_RECIPE": "recipe_id"}.get(
        kind, "feature_term_id"
    )
    cmd = command(target=dict(kind=kind, **{field: uuid4()}), value=value)
    first = declaration(cmd)
    rows = () if member == "UNDECLARED" else (first,)
    if member == "RETRACTED":
        rows += (revision(first, retract=True),)
    identity = entry(cmd.target)
    from target_affinity_fixtures import policy

    explicit = subject(
        rows,
        targets=(cmd.target,),
        entries=(identity,),
        terms=(identity.identity,) if kind in {"PROTEIN", "METHOD", "FLAVOR"} and rows else (),
        interpretation=policy(self_level=strength),
    )
    source = reference_source(cmd.target, identity.identity, state=prior, amount=amount)
    mapping = compatibility(explicit, source)
    return c.ExactTargetPriorBackedAffinityInput(
        explicit=explicit,
        reference_source=source,
        compatibility_policy=mapping,
        shrinkage_policy=shrinkage(mapping),
    )
