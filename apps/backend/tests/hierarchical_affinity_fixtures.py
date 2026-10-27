"""Synthetic complete journals for the pure consumer; no canonical-origin claim."""

from datetime import timedelta
from uuid import uuid4

from app.modules.preferences import hierarchy_contracts as h
from app.modules.preferences import prior_affinity_contracts as p
from hierarchy_fixtures import policy
from preference_fixtures import NOW, declaration
from prior_shrinkage_fixtures import compatibility, consumer_input, reference_source, shrinkage
from target_affinity_fixtures import revision


def hierarchy_cut(parent, destination, transfer, *, operations=None, owner=None):
    """Build real frozen contracts/hashes/replay, never mock resolution output."""
    admin = h.HierarchySessionFact(
        database_oid=42,
        database_name="synthetic",
        role_oid=1,
        role_name="admin",
        authenticated_identity="admin",
    )
    session = admin.model_copy(
        update=dict(role_oid=2, role_name="reader", authenticated_identity="reader")
    )
    cmd = h.HierarchyProviderCommand(
        code="synthetic.hierarchy",
        version="1",
        source_system="synthetic.hierarchy",
        remit="Synthetic tests only",
        idempotency_key="provider",
    )
    provider = h.HierarchyProviderFact(
        id=uuid4(),
        command=cmd,
        administrator=admin,
        recorded_at=NOW,
        command_hash=h.hierarchy_hash("hierarchy.provider-command.v1", cmd),
    )
    cmd = h.HierarchyPrincipalCommand(role_name="reader", idempotency_key="reader")
    principal = h.HierarchyPrincipalFact(
        id=uuid4(),
        command=cmd,
        database_oid=42,
        database_name="synthetic",
        role_oid=2,
        role_name="reader",
        administrator=admin,
        recorded_at=NOW,
        command_hash=h.hierarchy_hash("hierarchy.principal-command.v1", cmd),
    )
    terms = tuple(
        i.identity
        for i in (parent, destination)
        if i.target.kind in {"METHOD", "FLAVOR", "PROTEIN"}
    )
    owner = owner or h.HierarchyOwnerManifest(
        identities=(parent, destination),
        catalog_frontier=0,
        catalog_streams=(),
        recipe_frontier=0,
        recipes=(),
        scopes=(),
        terms=terms,
    )
    events, pubs, mutations, heads = [], [], [], {}

    def hashed(cls, fields, name, domain):
        body = {k: v for k, v in fields.items() if k != "owner_source"}
        return cls(**fields, **{name: h.hierarchy_hash(domain, body)})

    def journal(child, kind):
        fields = dict(
            provider_id=provider.id,
            mutation_sequence=len(mutations) + 1,
            kind=kind,
            child_id=child.id,
            child_hash=child.fact_hash,
            recorded_at=child.recorded_at,
            predecessor_hash=mutations[-1].journal_hash if mutations else None,
        )
        mutations.append(
            hashed(h.HierarchyMutationFact, fields, "journal_hash", "hierarchy.mutation.v1")
        )

    for cap in ("CAPTURE", "REVIEW_PUBLISH", "RETRACT"):
        cmd = h.HierarchyAuthorityCommand(
            provider_id=provider.id,
            principal_id=principal.id,
            capability=cap,
            action="GRANT",
            expected_authority_generation=len(events),
            reason="Synthetic grant",
            idempotency_key=cap,
        )
        fields = dict(
            id=uuid4(),
            command=cmd,
            administrator=admin,
            recorded_at=NOW + timedelta(seconds=len(events) + 1),
            authority_sequence=len(events) + 1,
            mutation_sequence=len(mutations) + 1,
            command_hash=h.hierarchy_hash("hierarchy.authority-command.v1", cmd),
        )
        event = hashed(h.HierarchyAuthorityEvent, fields, "fact_hash", "hierarchy.authority.v1")
        events.append(event)
        journal(event, "AUTHORITY")

    policy_identity = h.HierarchyStreamIdentity(
        kind="POLICY",
        policy_id=transfer.policy_id,
        source=None,
        destination=None,
        recipe_bindings=(),
    )
    bindings = tuple(
        dict(
            endpoint=name,
            recipe_version_id=next(
                r.id for r in owner.recipes if r.recipe.id == endpoint.target.recipe_id
            ),
            key=None,
            path=None,
        )
        for name, endpoint in (("SOURCE", parent), ("DESTINATION", destination))
        if endpoint.target.kind == "DIRECT_RECIPE"
    )
    relation_identity = h.HierarchyStreamIdentity(
        kind="RELATION",
        policy_id=transfer.policy_id,
        source=parent.target,
        destination=destination.target,
        recipe_bindings=bindings,
    )
    operations = (
        operations
        if operations is not None
        else [(policy_identity, "REPLACE", transfer), (relation_identity, "REPLACE", None)]
    )
    for identity, operation, payload in operations:
        previous = heads.get(identity.key())
        policy_head = heads.get(policy_identity.key())
        pins = (
            h.HierarchyOwnerManifest(
                identities=(),
                catalog_frontier=0,
                catalog_streams=(),
                recipe_frontier=0,
                recipes=(),
                scopes=(),
                terms=(),
            )
            if identity.kind == "POLICY"
            else owner
        )
        if identity.kind == "RELATION":
            endpoints = (identity.source, identity.destination)
            pins = pins.model_copy(
                update=dict(
                    identities=tuple(i for i in owner.identities if i.target in endpoints),
                    recipes=tuple(
                        r
                        for r in owner.recipes
                        if r.id in {b.recipe_version_id for b in identity.recipe_bindings}
                    ),
                )
            )
        if isinstance(payload, dict) and identity.kind == "RELATION":
            payload = h.HierarchyRelationBody(
                policy_revision_id=policy_head.id,
                policy_fingerprint=policy_head.command.policy.fingerprint(),
                **payload,
            )
        relation = (
            None
            if operation == "RETRACT" or identity.kind == "POLICY"
            else (
                payload
                or h.HierarchyRelationBody(
                    policy_revision_id=policy_head.id,
                    policy_fingerprint=policy_head.command.policy.fingerprint(),
                    support_mode="REVIEWED_EXACT_PAIR",
                    support_review_id=None,
                    catalog_review_ids=(),
                )
            )
        )
        cmd = h.HierarchyPublicationCommand(
            provider_id=provider.id,
            identity=identity,
            operation=operation,
            policy=payload if identity.kind == "POLICY" else None,
            relation=relation,
            provenance=transfer.provenance.model_copy(
                update=dict(source_system=provider.command.source_system)
            ),
            review_rationale="Synthetic review",
            expected_provider_generation=len(pubs),
            expected_mutation_head_hash=mutations[-1].journal_hash,
            expected_revision=previous.revision if previous else -1,
            predecessor_id=previous.id if previous else None,
            idempotency_key=f"pub.{len(pubs)}",
        )
        clock = NOW + timedelta(seconds=10 + len(pubs))
        fields = dict(
            id=uuid4(),
            stream_id=previous.stream_id if previous else uuid4(),
            command=cmd,
            owner_source=pins,
            owner_pins=h.hierarchy_owner_pins(pins),
            principal_id=principal.id,
            session=session,
            grant_event_id=events[2 if operation == "RETRACT" else 1].id,
            authority_generation=3,
            revision=cmd.expected_revision + 1,
            source_sequence=len(pubs) + 1,
            mutation_sequence=len(mutations) + 1,
            recorded_at=clock,
            effective_at=clock,
            command_hash=h.hierarchy_hash("hierarchy.publication-command.v1", cmd),
        )
        pub = hashed(h.HierarchyRevisionFact, fields, "fact_hash", "hierarchy.publication.v1")
        pubs.append(pub)
        heads[identity.key()] = pub
        journal(pub, "PUBLICATION")
    required = {h.target_key(destination.target)} | {
        h.target_key(t)
        for pub in pubs
        for t in (pub.command.identity.source, pub.command.identity.destination)
        if t is not None
    }
    owner = owner.model_copy(
        update=dict(
            identities=tuple(i for i in owner.identities if h.target_key(i.target) in required)
        )
    )
    return h.HierarchySourceSnapshotDraft(
        request=dict(
            provider_id=provider.id,
            policy_id=transfer.policy_id,
            requested_targets=(destination.target,),
        ),
        provider=provider,
        principals=(principal,),
        authority_events=events,
        publications=pubs,
        mutations=mutations,
        streams=tuple(
            h.HierarchyStreamFact(
                id=v.stream_id,
                provider_id=provider.id,
                identity=v.command.identity,
                head_id=v.id,
                head_revision=v.revision,
            )
            for v in heads.values()
        ),
        frontier=dict(
            provider_id=provider.id,
            source_generation=len(pubs),
            authority_generation=3,
            mutation_generation=len(mutations),
            source_head_id=pubs[-1].id if pubs else None,
            authority_head_id=events[-1].id,
            mutation_head_hash=mutations[-1].journal_hash,
        ),
        owner_source=owner,
        reader_principal_id=principal.id,
        reader_session=session,
        reader_grant_id=events[0].id,
        capture_started_at=NOW + timedelta(hours=2),
        capture_completed_at=NOW + timedelta(hours=2, seconds=1),
        isolation="REPEATABLE READ",
    )


def inputs(
    *,
    source_kind="INGREDIENT",
    destination_kind="PROTEIN",
    parent_state="DECLARED",
    destination_state="UNDECLARED",
    value="LIKE",
    destination_value="LIKE",
    prior="NO_PUBLICATION",
    destination_prior="NO_PUBLICATION",
    transfer=None,
):
    parent = consumer_input(kind=source_kind, member=parent_state, value=value, prior=prior)
    dest = consumer_input(
        kind=destination_kind,
        member=destination_state,
        value=destination_value,
        prior=destination_prior,
    )
    # Author one complete member history, then independently capture the two exact targets.
    ledger = list(parent.explicit.source.preferences.declarations)
    for row in dest.explicit.source.preferences.declarations:
        cmd = row.command.model_copy(
            update=dict(
                household_id=parent.explicit.source.request.household_id,
                member_id=parent.explicit.source.request.member_id,
            )
        )
        if row.revision_no == 0:
            fresh = declaration(cmd, sequence=len(ledger) + 1)
        else:
            fresh = revision(ledger[-1], retract=True).model_copy(
                update=dict(member_sequence=len(ledger) + 1)
            )
        ledger.append(fresh)
    terms = tuple(
        i.identity
        for s in (parent, dest)
        for i in s.explicit.source.manifest.entries
        if i.kind in {"METHOD", "FLAVOR", "PROTEIN"}
        and any(
            d.command.target.feature_term_id == i.identity.id
            for d in ledger
            if d.command.target.kind in {"METHOD", "FLAVOR", "PROTEIN"}
        )
    )
    common = parent.explicit.source.preferences.model_copy(
        update=dict(declarations=tuple(ledger), frontier=len(ledger), feature_terms=terms)
    )
    for name, child in (("parent", parent), ("destination", dest)):
        body = child.model_dump()
        body["explicit"]["source"]["preferences"] = common
        for field in ("request", "manifest"):
            body["explicit"]["source"][field].update(
                household_id=common.household_id, member_id=common.member_id
            )
        child = p.ExactTargetPriorBackedAffinityInput.model_validate(body)
        if name == "parent":
            parent = child
        else:
            dest = child
    transfer = transfer or policy(source_kind=source_kind, destination_kind=destination_kind)
    # Bind the authored hierarchy to the complete actual parent policy, not its scalar.
    if transfer.explicit_policy != parent.explicit.policy:
        parent = rebind(parent, explicit_policy=transfer.explicit_policy)
        dest = dest.model_copy(
            update=dict(
                explicit=dest.explicit.model_copy(
                    update=dict(
                        source=dest.explicit.source.model_copy(
                            update=dict(preferences=parent.explicit.source.preferences)
                        )
                    )
                )
            )
        )
    transfer = repin_transfer(transfer, parent)
    subject = dict(destination=dest, parent=parent)
    return rebuild(subject, transfer=transfer)


def rebuild(subject, *, transfer=None, operations=None, owner=None):
    parent, dest = subject["parent"], subject["destination"]
    if transfer is None:
        transfer = subject["hierarchy_source"].publications[0].command.policy
    endpoints = (
        h.HierarchyTargetIdentity(
            target=parent.explicit.source.request.requested_targets[0],
            identity=parent.explicit.source.manifest.entries[0].identity,
        ),
        h.HierarchyTargetIdentity(
            target=dest.explicit.source.request.requested_targets[0],
            identity=dest.explicit.source.manifest.entries[0].identity,
        ),
    )
    if owner is None:
        from app.modules.recipes.contracts import RecipeVersionSnapshot
        from recipe_fixtures import recipe_data

        recipes = []
        for endpoint in endpoints:
            if endpoint.target.kind == "DIRECT_RECIPE":
                data = recipe_data()
                data["recipe"] = endpoint.identity.model_dump()
                for transformation in data["transformations"]:
                    transformation["method"] = endpoint.identity.cooking_method
                recipes.append(RecipeVersionSnapshot.model_validate(data))
        owner = h.HierarchyOwnerManifest(
            identities=endpoints,
            catalog_frontier=0,
            catalog_streams=(),
            recipe_frontier=0,
            recipes=recipes,
            scopes=(),
            terms=tuple(
                e.identity for e in endpoints if e.target.kind in {"PROTEIN", "METHOD", "FLAVOR"}
            ),
        )
    return dict(
        subject,
        hierarchy_source=hierarchy_cut(*endpoints, transfer, operations=operations, owner=owner),
    )


def repin_transfer(transfer, parent):
    body = transfer.model_dump()
    body.update(
        explicit_policy=parent.explicit.policy, compatibility_policy=parent.compatibility_policy
    )
    for direction in body["directions"]:
        group = next(
            g
            for g in parent.explicit.policy.target_policies
            if g.target_kind == direction["source_kind"]
        )
        for row in direction["rows"]:
            row["source_descriptor"] = parent.compatibility_policy.coordinate_for(
                direction["source_kind"]
            )
            row["expected_source_amount"] = next(
                r.amount for r in group.affinity_rules if r.value == row["source_affinity_value"]
            )
    return h.HierarchyTransferPolicy.model_validate(body)


def rebind(child, *, explicit_policy=None, prior_state=None, prior_amount=(1, 2)):
    explicit = child.explicit.model_copy(
        update=dict(policy=explicit_policy or child.explicit.policy)
    )
    source = child.reference_source
    if prior_state is not None:
        source = reference_source(
            source.request.requested_targets[0],
            source.identities[0].identity,
            state=prior_state,
            amount=prior_amount,
            provider=source.provider,
        )
    mapping = (
        child.compatibility_policy
        if explicit.policy == child.explicit.policy
        else (compatibility(explicit, source))
    )
    return p.ExactTargetPriorBackedAffinityInput(
        explicit=explicit,
        reference_source=source,
        compatibility_policy=mapping,
        shrinkage_policy=child.shrinkage_policy
        if (mapping == child.compatibility_policy)
        else shrinkage(mapping),
    )


def catalog_stream(ingredient_id, term, *, coverage="PARTIAL", positive=True):
    from app.modules.catalog.contracts import (
        IngredientProteinReviewFact,
        IngredientProteinStreamFact,
        ReplaceIngredientProteinReviewCommand,
    )
    from preference_fixtures import provenance

    cmd = ReplaceIngredientProteinReviewCommand(
        ingredient_id=ingredient_id,
        expected_revision_no=-1,
        expected_catalog_frontier=0,
        predecessor_id=None,
        coverage=coverage,
        covered_term_ids=(term.id,),
        positive_term_ids=(term.id,) if positive else (),
        provenance=provenance().model_dump(),
        correction_reason=None,
        idempotency_key="classification",
    )
    actor, stream_id = uuid4(), uuid4()
    fact = IngredientProteinReviewFact(
        id=uuid4(),
        stream_id=stream_id,
        ingredient_id=ingredient_id,
        revision_no=0,
        predecessor_revision_no=None,
        source_sequence=1,
        reviewer_user_id=actor,
        recorded_at=NOW + timedelta(seconds=4),
        command=cmd,
        command_hash=cmd.fingerprint(actor),
    )
    return IngredientProteinStreamFact(id=stream_id, ingredient_id=ingredient_id, reviews=(fact,))


def catalog_correction(stream, *, mode="RETRACT"):
    from app.modules.catalog.contracts import (
        IngredientProteinReviewCommand,
        IngredientProteinReviewFact,
    )

    first = stream.reviews[-1]
    body = first.command.model_dump()
    body.update(
        expected_revision_no=first.revision_no,
        predecessor_id=first.id,
        expected_catalog_frontier=len(stream.reviews),
        correction_reason="Reviewed correction",
        idempotency_key=uuid4().hex,
    )
    if mode == "RETRACT":
        body.update(
            contract_version="ingredient-protein-retract.v1",
            command_kind="RETRACT",
            coverage=None,
            covered_term_ids=(),
            positive_term_ids=(),
        )
    elif mode == "NONE":
        body.update(coverage="COMPLETE", positive_term_ids=())
    elif mode == "ABSENT":
        # Another reviewed positive keeps the classification from REVIEWED_NONE.
        from preference_fixtures import term

        extra = term("PROTEIN")
        body.update(
            coverage="COMPLETE",
            covered_term_ids=(*body["covered_term_ids"], extra.id),
            positive_term_ids=(extra.id,),
        )
    elif mode == "UNRESOLVED":
        body.update(coverage="PARTIAL", positive_term_ids=())
    cmd = IngredientProteinReviewCommand.model_validate(body)
    fact = IngredientProteinReviewFact(
        id=uuid4(),
        stream_id=stream.id,
        ingredient_id=stream.ingredient_id,
        revision_no=first.revision_no + 1,
        predecessor_revision_no=first.revision_no,
        source_sequence=first.source_sequence + 1,
        reviewer_user_id=first.reviewer_user_id,
        recorded_at=NOW + timedelta(seconds=30),
        command=cmd,
        command_hash=cmd.fingerprint(first.reviewer_user_id),
    )
    return stream.model_copy(update=dict(reviews=(*stream.reviews, fact))), (
        extra if mode == "ABSENT" else None
    )


def classification_input(*, dimension=None):
    """Actual frozen positive support; no mock source eligibility."""
    subject = inputs(
        source_kind="DIRECT_RECIPE" if dimension else "INGREDIENT",
        destination_kind="PROTEIN" if dimension in {None, "MAIN_PROTEIN"} else dimension,
    )
    old = subject["hierarchy_source"]
    owner = old.owner_source
    term = subject["destination"].explicit.source.manifest.entries[0].identity
    extras, streams, scopes, recipes = {}, (), (), owner.recipes
    if dimension is None:
        ingredient_id = subject["parent"].explicit.source.request.requested_targets[0].ingredient_id
        stream = catalog_stream(ingredient_id, term)
        streams = (stream,)
        review_id = stream.reviews[0].id
    else:
        from app.modules.recipes.contracts import FeatureSelectedPath
        from feature_fixtures import review_command, scope

        recipe = recipes[0]
        path = (
            None
            if dimension == "METHOD"
            else FeatureSelectedPath(
                tier_id=recipe.portion_tiers[0].id,
                selected_rule_ids=(),
                deltas=tuple((i.id, 0) for i in recipe.ingredients),
            )
        )
        supports = ()
        if dimension == "MAIN_PROTEIN":
            ingredient = recipe.ingredients[0]
            stream = catalog_stream(ingredient.ingredient_id, term)
            streams = (stream,)
            supports = (
                dict(
                    term_id=term.id,
                    requirement_id=ingredient.id,
                    ingredient_id=ingredient.ingredient_id,
                    catalog_review_id=stream.reviews[0].id,
                ),
            )
            extras["expected_catalog_frontier"] = 1
        cmd = review_command(recipe, (term,), dimension=dimension, supports=supports, **extras)
        sc = scope(cmd)
        # Publication clocks in this synthetic source are seconds after NOW.
        sc = sc.model_copy(
            update=dict(
                reviews=(
                    sc.reviews[0].model_copy(update=dict(recorded_at=NOW + timedelta(seconds=5))),
                )
            )
        )
        scopes, review_id = (sc,), sc.reviews[0].id
    owner = owner.model_copy(
        update=dict(
            catalog_frontier=len(streams),
            catalog_streams=streams,
            recipe_frontier=len(scopes),
            scopes=scopes,
        )
    )
    policy_identity = old.publications[0].command.identity
    relation_identity = old.publications[1].command.identity
    if dimension:
        relation_identity = relation_identity.model_copy(
            update=dict(
                recipe_bindings=(
                    h.HierarchyRecipeBinding(
                        endpoint="SOURCE", recipe_version_id=recipes[0].id, key=cmd.key, path=path
                    ),
                )
            )
        )
    # The builder pins the actual freshly published policy revision.
    # Rebuild the full journal with classification payload; policy revision IDs
    # are allocated inside hierarchy_cut, so a callback supplies that exact pin.
    relation = dict(
        support_mode="CLASSIFICATION_BOUND_PAIR",
        support_review_id=review_id,
        catalog_review_ids=tuple(s.reviews[0].id for s in streams) if dimension else (),
    )
    return rebuild(
        subject,
        owner=owner,
        operations=[
            (policy_identity, "REPLACE", old.publications[0].command.policy),
            (relation_identity, "REPLACE", relation),
        ],
    )
