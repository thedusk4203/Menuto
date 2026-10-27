"""Zero-IO replay of reviewed hierarchy SOURCE; never a member preference consumer."""

from app.domain.feature_identity import canonical
from app.modules.preferences import hierarchy_contracts as c
from app.modules.preferences.hierarchy_contracts import target_key
from app.modules.recipes.contracts import (
    CulinaryFeatureEvaluationInput,
    FeatureTermQuery,
    MainProteinFeatureSources,
    RecipeFeatureSources,
    discover_feature_input,
    resolve_culinary_binding,
    resolve_feature_input,
    validate_applicability,
)


def policy_identity(policy_id):
    return c.HierarchyStreamIdentity(
        kind="POLICY", policy_id=policy_id, source=None, destination=None, recipe_bindings=()
    )


def check_cycle(publications):
    adjacency = {}
    for publication in publications:
        command = publication.command
        if command.identity.kind != "RELATION" or command.operation == "RETRACT":
            continue
        a, b = target_key(command.identity.source), target_key(command.identity.destination)
        adjacency.setdefault(a, set()).add(b)
    indegree = {node: 0 for node in adjacency}
    for children in adjacency.values():
        for child in children:
            indegree[child] = indegree.get(child, 0) + 1
    ready = [node for node, degree in indegree.items() if degree == 0]
    processed = 0
    while ready:
        node = ready.pop()
        processed += 1
        for child in adjacency.get(node, ()):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if processed != len(indegree):
        raise ValueError("Hierarchy cycle prohibited")


def support_status(identity, relation, owner, captured_at):
    """Recompute frozen food truth; classification never creates transfer permission."""
    owner = c.HierarchyOwnerManifest.model_validate(canonical(owner))
    targets = {target_key(i.target): i for i in owner.identities}
    if any(target_key(t) not in targets for t in (identity.source, identity.destination)):
        raise ValueError("Incomplete canonical endpoint manifest")
    recipes = {r.id: r for r in owner.recipes}
    for binding in identity.recipe_bindings:
        target = identity.source if binding.endpoint == "SOURCE" else identity.destination
        recipe = recipes.get(binding.recipe_version_id)
        if (
            recipe is None
            or recipe.recipe.id != target.recipe_id
            or recipe.review_status != "REVIEWED"
        ):
            raise ValueError("Exact reviewed RecipeVersion binding required")
        if binding.key is not None:
            validate_applicability(recipe, binding.key)
        if binding.path is not None:
            resolve_culinary_binding(
                recipe,
                binding.path.tier_id,
                binding.path.selected_rule_ids,
                dict(binding.path.deltas),
            )
    if relation.support_mode == "REVIEWED_EXACT_PAIR":
        return None, None
    a, b = identity.source, identity.destination
    if {a.kind, b.kind} == {"INGREDIENT", "PROTEIN"}:
        ingredient = a if a.kind == "INGREDIENT" else b
        term = b if a.kind == "INGREDIENT" else a
        stream = next(
            (s for s in owner.catalog_streams if s.ingredient_id == ingredient.ingredient_id), None
        )
        if relation.catalog_review_ids:
            raise ValueError("Ingredient pair support does not carry recipe support IDs")
        if stream is None:
            return "SUPPORT_UNRESOLVED", "NO_SOURCE"
        head = stream.reviews[-1]
        if head.command.command_kind == "RETRACT":
            return "SUPPORT_RETRACTED", "RETRACTED"
        if not head.command.positive_term_ids and head.command.coverage == "COMPLETE":
            return "SUPPORT_REVIEWED_NONE", "REVIEWED_NONE"
        if term.feature_term_id in head.command.positive_term_ids:
            if head.id != relation.support_review_id:
                return "SUPPORT_SUPERSEDED", "REVIEW_HEAD_CHANGED"
            return None, None
        if term.feature_term_id not in head.command.covered_term_ids:
            return "SUPPORT_UNRESOLVED", "OUTSIDE_REVIEWED_UNIVERSE"
        return (
            ("SUPPORT_REVIEWED_ABSENT", "REVIEWED_ABSENT")
            if head.command.coverage == "COMPLETE"
            else ("SUPPORT_UNRESOLVED", "PARTIAL_COVERAGE")
        )
    if "DIRECT_RECIPE" not in {a.kind, b.kind}:
        raise ValueError("Classification-bound relation shape prohibited")
    term = b if a.kind == "DIRECT_RECIPE" else a
    if term.kind not in {"METHOD", "FLAVOR", "PROTEIN"} or len(identity.recipe_bindings) != 1:
        raise ValueError("Classification-bound recipe/feature shape required")
    binding = identity.recipe_bindings[0]
    dimension = "MAIN_PROTEIN" if term.kind == "PROTEIN" else term.kind
    if binding.key is None or binding.key.dimension != dimension:
        raise ValueError("Explicit classification context dimension required")
    scopes = tuple(
        s
        for s in owner.scopes
        if s.key.recipe_version_id == binding.recipe_version_id and s.key.dimension == dimension
    )
    source_type = MainProteinFeatureSources if dimension == "MAIN_PROTEIN" else RecipeFeatureSources
    streams = ()
    if dimension == "MAIN_PROTEIN":
        required = {
            p.ingredient_id for scope in scopes for r in scope.reviews for p in r.command.supports
        }
        streams = tuple(s for s in owner.catalog_streams if s.ingredient_id in required)
    tids = {t for scope in scopes for r in scope.reviews for t in r.command.covered_term_ids}
    tids |= {t for stream in streams for r in stream.reviews for t in r.command.covered_term_ids}
    fields = dict(
        recipe_frontier=owner.recipe_frontier,
        scopes=scopes,
        terms=tuple(t for t in owner.terms if t.id in tids),
    )
    if dimension == "MAIN_PROTEIN":
        fields.update(catalog_frontier=owner.catalog_frontier, catalog_streams=streams)
    try:
        subject = CulinaryFeatureEvaluationInput(
            recipe=recipes[binding.recipe_version_id],
            requested_dimensions=(dimension,),
            path=binding.path,
            sources=source_type(**fields),
            captured_at=captured_at,
        )
        discovery = discover_feature_input(subject)[0]
        result = resolve_feature_input(
            subject, (FeatureTermQuery(dimension=dimension, term_ids=(term.feature_term_id,)),)
        )[0]
    except ValueError as exc:
        if "SOURCE_CONFLICT" in str(exc):
            return "SUPPORT_UNRESOLVED", "SOURCE_CONFLICT"
        raise
    if discovery.state == "REVIEWED_NONE":
        return "SUPPORT_REVIEWED_NONE", "REVIEWED_NONE"
    if discovery.reason == "RETRACTED":
        return "SUPPORT_RETRACTED", "RETRACTED"
    if discovery.reason == "STALE_ASSOCIATION":
        return "SUPPORT_SUPERSEDED", "STALE_ASSOCIATION"
    if result.state == "REVIEWED_ABSENT":
        return "SUPPORT_REVIEWED_ABSENT", "REVIEWED_ABSENT"
    if result.state == "UNRESOLVED":
        return "SUPPORT_UNRESOLVED", result.reason
    if discovery.review_id != relation.support_review_id:
        return "SUPPORT_SUPERSEDED", "REVIEW_HEAD_CHANGED"
    scope = next((s for s in scopes if s.id == discovery.applicability_id), None)
    if scope is None or scope.key != binding.key:
        return "SUPPORT_UNRESOLVED", "EXACT_CONTEXT_NOT_MATCHED"
    expected = {p.catalog_review_id for p in scope.reviews[-1].command.supports}
    if set(relation.catalog_review_ids) != expected:
        return "SUPPORT_SUPERSEDED", "CATALOG_SUPPORT_PIN_CHANGED"
    if result.state == "PRESENT":
        return None, None
    return "SUPPORT_UNRESOLVED", result.reason


def validate_hierarchy_publication(publication, heads):
    command, identity = publication.command, publication.command.identity
    if any(
        r.recorded_at > publication.recorded_at
        for stream in publication.owner_source.catalog_streams
        for r in stream.reviews
    ) or any(
        r.recorded_at > publication.recorded_at
        for scope in publication.owner_source.scopes
        for r in scope.reviews
    ):
        raise ValueError("Owner support postdates publication cut")
    if command.operation == "RETRACT":
        return
    if identity.kind == "POLICY":
        return
    selected = heads.get(policy_identity(identity.policy_id).key())
    relation = command.relation
    if (
        selected is None
        or selected.command.operation != "REPLACE"
        or selected.id != relation.policy_revision_id
        or selected.command.policy.fingerprint() != relation.policy_fingerprint
    ):
        raise ValueError("Exact current active policy pin required")
    policy = selected.command.policy
    direction = next(
        d
        for d in policy.directions
        if (d.source_kind, d.destination_kind) == (identity.source.kind, identity.destination.kind)
    )
    if not direction.enabled or relation.support_mode not in direction.support_modes:
        raise ValueError("Direction/support mode denied")
    reason, detail = support_status(
        identity, relation, publication.owner_source, publication.recorded_at
    )
    if reason:
        raise ValueError(f"Publication support not eligible: {reason}/{detail}")
    prospective = dict(heads)
    prospective[identity.key()] = publication
    check_cycle(
        p for p in prospective.values() if p.command.identity.policy_id == identity.policy_id
    )


def relation_diagnostic(source, publication, policy):
    retracted = publication.command.operation == "RETRACT"
    policy_reason = None
    support = detail = None
    if policy is None:
        policy_reason = "POLICY_MISSING"
    elif policy.command.operation == "RETRACT":
        policy_reason = "POLICY_RETRACTED"
    elif not retracted:
        relation, identity = publication.command.relation, publication.command.identity
        if (
            relation.policy_revision_id != policy.id
            or relation.policy_fingerprint != policy.command.policy.fingerprint()
        ):
            policy_reason = "POLICY_SUPERSEDED"
        else:
            direction = next(
                d
                for d in policy.command.policy.directions
                if (d.source_kind, d.destination_kind)
                == (identity.source.kind, identity.destination.kind)
            )
            if not direction.enabled or relation.support_mode not in direction.support_modes:
                policy_reason = "DIRECTION_DENIED"
    if not retracted:
        support, detail = support_status(
            publication.command.identity,
            publication.command.relation,
            source.owner_source,
            source.capture_started_at,
        )
    return c.HierarchyRelationDiagnostic(
        publication_id=publication.id,
        retracted=retracted,
        policy_reason=policy_reason,
        support_status=support,
        support_reason=detail,
    )


def hierarchy_rows(source):
    heads = {s.identity.key(): s for s in source.streams}
    publications = {p.id: p for p in source.publications}
    policy_head = heads.get(policy_identity(source.request.policy_id).key())
    policy = publications[policy_head.head_id] if policy_head else None
    rows = []
    for target in source.request.requested_targets:
        relations = tuple(
            sorted(
                (
                    publications[s.head_id]
                    for s in source.streams
                    if s.identity.kind == "RELATION"
                    and s.identity.policy_id == source.request.policy_id
                    and s.identity.destination == target
                ),
                key=lambda r: r.command.identity.key(),
            )
        )
        active = tuple(p for p in relations if p.command.operation != "RETRACT")
        diagnostics = tuple(relation_diagnostic(source, p, policy) for p in relations)
        reason, detail, selected = None, None, None
        if policy is None:
            reason = "POLICY_MISSING"
        elif policy.command.operation == "RETRACT":
            reason = "POLICY_RETRACTED"
        elif len(active) > 1:
            reason = "MULTIPLE_INCOMING_RELATIONS"
        elif not active:
            reason = "RELATION_RETRACTED" if relations else "NO_RELATION"
        else:
            selected = active[0]
            diagnostic = next(d for d in diagnostics if d.publication_id == selected.id)
            reason = diagnostic.policy_reason or diagnostic.support_status
            detail = diagnostic.support_reason
        rows.append(
            c.HierarchyDestinationSource(
                target=target,
                status="UNAVAILABLE" if reason else "ELIGIBLE_RELATION",
                reason=reason,
                policy=policy,
                relations=relations,
                selected_relation=selected,
                support_reason=detail,
                diagnostics=diagnostics,
            )
        )
    return tuple(rows)


def resolve_hierarchy_sources(source):
    source = c.HierarchySourceSnapshotDraft.model_validate(canonical(source))
    rows = hierarchy_rows(source)
    return c.ReviewedHierarchySourceDraft(
        source=source,
        rows=rows,
        source_fingerprint=source.fingerprint(),
        result_fingerprint=c.hierarchy_hash(
            "hierarchy.resolution.v1", dict(source=source, rows=rows)
        ),
    )


def validate_owner_references(source):
    current = source.owner_source
    recipes = {r.id: r for r in current.recipes}
    terms = {r.id: r for r in current.terms}
    catalog = {r.id: r for r in current.catalog_streams}
    scopes = {r.id: r for r in current.scopes}
    for publication in source.publications:
        owner = publication.owner_source
        if (
            owner.catalog_frontier > current.catalog_frontier
            or owner.recipe_frontier > current.recipe_frontier
        ):
            raise ValueError("Owner source frontier regressed")
        for recipe in owner.recipes:
            if recipes.get(recipe.id) != recipe:
                raise ValueError("Immutable RecipeVersion differs across owner cuts")
        for term in owner.terms:
            if terms.get(term.id) != term:
                raise ValueError("Immutable vocabulary differs across owner cuts")
        for stream in owner.catalog_streams:
            fresh = catalog.get(stream.id)
            if (
                fresh is None
                or fresh.ingredient_id != stream.ingredient_id
                or fresh.reviews[: len(stream.reviews)] != stream.reviews
            ):
                raise ValueError("Catalog pinned history differs across owner cuts")
        for scope in owner.scopes:
            fresh = scopes.get(scope.id)
            if (
                fresh is None
                or fresh.key != scope.key
                or fresh.reviews[: len(scope.reviews)] != scope.reviews
            ):
                raise ValueError("Recipe pinned history differs across owner cuts")


def validate_hierarchy_source(source):
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
    validate_owner_references(source)
    if any(
        r.recorded_at > source.capture_started_at
        for stream in source.owner_source.catalog_streams
        for r in stream.reviews
    ) or any(
        r.recorded_at > source.capture_started_at
        for scope in source.owner_source.scopes
        for r in scope.reviews
    ):
        raise ValueError("Owner support postdates capture cut")
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
    policy_versions = {}
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
                c.provenance.source_system == provider.command.source_system,
                "Provider coordinate or provenance differs",
            )
            k = c.identity.key()
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
            if c.policy is not None:
                previous_version = policy_versions.get(c.identity.policy_id, 0)
                require(
                    c.policy.policy_version > previous_version, "Policy version did not increase"
                )
                policy_versions[c.identity.policy_id] = c.policy.policy_version
            validate_hierarchy_publication(child, heads)
            require(c.expected_mutation_head_hash == previous_hash, "Mutation frontier CAS differs")
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
        h = heads.get(s.identity.key())
        require(
            h is not None
            and s.provider_id == provider.id
            and (s.id, s.head_id, s.head_revision) == (h.stream_id, h.id, h.revision),
            "Stream cache differs from history",
        )
    required_targets = {target_key(t) for t in source.request.requested_targets}
    for publication in source.publications:
        required_targets.update(
            target_key(t)
            for t in (publication.command.identity.source, publication.command.identity.destination)
            if t is not None
        )
    require(
        {target_key(i.target) for i in source.owner_source.identities} == required_targets,
        "Incomplete canonical target identity union",
    )
