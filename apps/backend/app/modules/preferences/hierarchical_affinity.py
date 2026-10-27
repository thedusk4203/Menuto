"""Pure one-hop interpretation; no capture, ambient state or new evidence event."""

from fractions import Fraction

from pydantic import BaseModel

from app.domain.feature_identity import canonical
from app.modules.catalog.contracts import AffinityFeatureTermFact
from app.modules.preferences import hierarchical_affinity_contracts as c
from app.modules.preferences.hierarchy_contracts import hierarchy_hash, lookup_hierarchy_policy_row
from app.modules.preferences.hierarchy_resolution import resolve_hierarchy_sources
from app.modules.preferences.prior_affinity import derive_exact_target_prior_backed_affinity
from app.modules.recipes.contracts import RecipeFact, RecipeVersionSnapshot


def _ledger(snapshot):
    body = canonical(snapshot)
    del body["captured_at"]
    body["declarations"].sort(key=lambda d: d["member_sequence"])
    body["feature_terms"].sort(key=lambda t: t["id"])
    return body


def _immutable_facts(subject):
    """Compare typed immutable owner facts at every depth, including prior identities.

    Models are already reparsed at this seam. Walking actual model types avoids
    confusing policies, mutable ingredient labels or UUIDs from different owners.
    RecipeVersion is immutable too; frozen source replay validates its internal
    support, while this check also reconciles repeated bodies across all children.
    """
    seen = {}

    def visit(value):
        if isinstance(value, (AffinityFeatureTermFact, RecipeFact, RecipeVersionSnapshot)):
            key = (type(value), value.id)
            body = canonical(value)
            if key in seen and seen[key] != body:
                raise ValueError("CONFLICTING_IMMUTABLE_OWNER_FACT: " + type(value).__name__)
            seen[key] = body
        if isinstance(value, BaseModel):
            for name in type(value).model_fields:
                visit(getattr(value, name))
        elif isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, (tuple, list)):
            for child in value:
                visit(child)

    visit(subject)


def _inherited(destination, parent, row, claimed=None):
    raw_dest = destination.explicit_profile.rows[0].raw_state
    if raw_dest.status == "RETRACTED":
        return c.SuppressedInheritedMemberPreference(reason="MEMBER_RETRACTED")
    if raw_dest.status == "DECLARED":
        return c.SuppressedInheritedMemberPreference(reason="DESTINATION_DIRECT_DECLARATION")
    if row.status == "UNAVAILABLE":
        return c.UnavailableInheritedMemberPreference(
            reason="HIERARCHY_SOURCE_UNAVAILABLE", source_reason=row.reason
        )
    if parent is None:
        raise ValueError("MISSING_REQUIRED_PARENT_INPUT")
    raw = parent.explicit_profile.rows[0]
    if raw.raw_state.status == "RETRACTED":
        return c.UnavailableInheritedMemberPreference(reason="PARENT_MEMBER_RETRACTED")
    if raw.raw_state.status == "UNDECLARED":
        reason = (
            "PARENT_PRIOR_ONLY_COLD_START"
            if (
                parent.effective.status == "AVAILABLE"
                and parent.effective.mode == "PRIOR_ONLY_COLD_START"
            )
            else "PARENT_UNDECLARED"
        )
        return c.UnavailableInheritedMemberPreference(reason=reason)
    policy = row.policy.command.policy
    mapped = parent.mapped_explicit
    if (
        parent.subject.explicit.policy != policy.explicit_policy
        or parent.subject.compatibility_policy != policy.compatibility_policy
        or mapped.value.coordinate != policy.compatibility_policy.coordinate_for(parent.target_kind)
    ):
        return c.UnavailableInheritedMemberPreference(reason="INCOMPATIBLE_COORDINATE")
    if (
        parent.effective.status != "AVAILABLE"
        or parent.effective.mode not in {"EXPLICIT_ONLY", "BLENDED_EXPLICIT_AND_PRIOR"}
        or mapped.rule_key != (parent.target_kind, raw.raw_state.value)
    ):
        raise ValueError("Recomputed explicit lineage differs")
    identity = row.selected_relation.command.identity
    lookup = lookup_hierarchy_policy_row(
        policy, parent.target_kind, destination.target_kind, raw.raw_state.value
    )
    if lookup.status == "SOURCE_VALUE_NOT_MAPPED":
        return c.UnavailableInheritedMemberPreference(reason="SOURCE_VALUE_NOT_MAPPED")
    direction = next(
        d
        for d in policy.directions
        if (d.source_kind, d.destination_kind) == (parent.target_kind, destination.target_kind)
    )
    mapping = lookup.row
    # Distinct raw and mapped coordinates: never compare their scalar amounts.
    if (
        lookup.status != "AVAILABLE"
        or mapping not in direction.rows
        or mapping.expected_source_amount != raw.affinity.amount
        or mapping.source_descriptor != mapped.value.coordinate
        or identity.source != parent.target
        or identity.destination != destination.target
    ):
        raise ValueError("Published semantic/operand/relation binding differs")
    coordinate = c.InheritedMemberPreferenceCoordinate(
        destination_target_kind=destination.target_kind,
        transfer_policy_semantic_fingerprint=policy.fingerprint(),
    )
    if claimed is not None and claimed.status == "AVAILABLE":
        if any(
            descriptor != coordinate
            for descriptor in (
                claimed.value.coordinate,
                claimed.trace.mapped_inherited.coordinate,
                claimed.trace.product.coordinate,
            )
        ):
            raise ValueError("Inherited descriptor differs from complete published policy")
    mapped_value = c.ScopedInheritedMemberPreference(
        coordinate=coordinate, amount=mapping.output_amount.model_dump()
    )
    # All complete policy, identity, semantic and descriptor gates precede new
    # transfer arithmetic. Frozen child shrinkage has its own earlier math gates.
    product = Fraction(
        mapping.output_amount.numerator, mapping.output_amount.denominator
    ) * Fraction(direction.attenuation.numerator, direction.attenuation.denominator)
    value = c.ScopedInheritedMemberPreference(
        coordinate=coordinate,
        amount=dict(numerator=product.numerator, denominator=product.denominator),
    )
    return c.AvailableInheritedMemberPreference(
        value=value,
        trace=c.InheritedPreferenceTrace(
            provider_id=row.selected_relation.command.provider_id,
            policy_stream_id=row.policy.stream_id,
            policy_revision_id=row.policy.id,
            relation_stream_id=row.selected_relation.stream_id,
            relation_revision_id=row.selected_relation.id,
            relation_identity=identity,
            semantic_state=raw.raw_state.value,
            mapped_explicit=mapped.value,
            mapping_row=mapping,
            mapped_inherited=mapped_value,
            attenuation=direction.attenuation,
            product=value,
        ),
    )


def _derive_fields(subject, *, claimed=None):
    subject = c.OneHopHierarchicalMemberPreferenceInput.model_validate(subject)
    destination = derive_exact_target_prior_backed_affinity(subject.destination)
    parent = derive_exact_target_prior_backed_affinity(subject.parent) if subject.parent else None
    hierarchy = resolve_hierarchy_sources(subject.hierarchy_source)
    if subject.hierarchy_source.request.requested_targets != (destination.target,):
        raise ValueError("EXACT_DESTINATION_REQUEST_REQUIRED")
    ledger = _ledger(subject.destination.explicit.source.preferences)
    if parent is not None:
        if (parent.household_id, parent.member_id) != (
            destination.household_id,
            destination.member_id,
        ):
            raise ValueError("MEMBER_OWNER_MISMATCH")
        if ledger != _ledger(subject.parent.explicit.source.preferences):
            raise ValueError("INCOHERENT_MEMBER_HISTORY")
    _immutable_facts(subject)
    row = hierarchy.rows[0]
    if parent is not None and row.status == "ELIGIBLE_RELATION":
        if parent.target != row.selected_relation.command.identity.source:
            raise ValueError("PARENT_TARGET_MISMATCH")
    return dict(
        subject=subject,
        household_id=destination.household_id,
        member_id=destination.member_id,
        destination_target=destination.target,
        parent_target=parent.target if parent else None,
        destination_exact_target=destination,
        parent_exact_target=parent,
        hierarchy=hierarchy,
        member_ledger_fingerprint=hierarchy_hash("member-preference.one-hop-ledger.v1", ledger),
        inherited=_inherited(destination, parent, row, claimed),
    )


def derive_one_hop_hierarchical_member_preference(subject):
    """Recompute frozen children and interpret exactly one reviewed relation, without IO."""
    fields = _derive_fields(subject)
    temporary = c.OneHopHierarchicalMemberPreferenceDraft.model_construct(
        **fields, fingerprint="0" * 64
    )
    return c.OneHopHierarchicalMemberPreferenceDraft(
        **fields, fingerprint=temporary.expected_fingerprint()
    )
