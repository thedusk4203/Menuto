"""Consumer seam delegates real frozen policy/journal/context replay."""

from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.modules.preferences import hierarchical_affinity_contracts as c
from app.modules.preferences import hierarchy_contracts as h
from app.modules.preferences.public import derive_one_hop_hierarchical_member_preference as derive
from hierarchical_affinity_fixtures import (
    catalog_correction,
    classification_input,
    inputs,
    rebuild,
)
from test_hierarchical_affinity import rehashed_root


def identities(subject):
    source = subject["hierarchy_source"]
    return source.publications[0].command.identity, source.publications[1].command.identity


@pytest.mark.parametrize(
    "mode,reason",
    [
        ("missing", "POLICY_MISSING"),
        ("retracted", "POLICY_RETRACTED"),
        ("superseded", "POLICY_SUPERSEDED"),
    ],
)
def test_hc35_policy_states_preserved(mode, reason):
    subject = inputs()
    policy_identity, relation_identity = identities(subject)
    policy = subject["hierarchy_source"].publications[0].command.policy
    operations = (
        []
        if mode == "missing"
        else [(policy_identity, "REPLACE", policy), (relation_identity, "REPLACE", None)]
    )
    if mode != "missing":
        operations.append(
            (policy_identity, "RETRACT", None)
            if mode == "retracted"
            else (policy_identity, "REPLACE", policy.model_copy(update=dict(policy_version=2)))
        )
    result = derive(rebuild(subject, operations=operations) | dict(parent=None))
    assert result.inherited.reason == "HIERARCHY_SOURCE_UNAVAILABLE"
    assert result.inherited.source_reason == reason
    assert result.hierarchy.rows[0].reason == reason


@pytest.mark.parametrize("retracted,reason", [(False, "NO_RELATION"), (True, "RELATION_RETRACTED")])
def test_hc06_hc36_no_relation_and_tombstone_are_distinct(retracted, reason):
    subject = inputs()
    pi, ri = identities(subject)
    policy = subject["hierarchy_source"].publications[0].command.policy
    operations = [(pi, "REPLACE", policy)]
    if retracted:
        operations += [(ri, "REPLACE", None), (ri, "RETRACT", None)]
    result = derive(rebuild(subject, operations=operations) | dict(parent=None))
    assert result.inherited.source_reason == reason and "value" not in result.inherited.model_dump()


def ambiguous(subject, *, diamond=False):
    pi, ri = identities(subject)
    cut = subject["hierarchy_source"]
    owner = cut.owner_source
    target = ri.source.model_copy(update=dict(ingredient_id=uuid4()))
    entry = h.HierarchyTargetIdentity(
        target=target, identity=dict(id=target.ingredient_id, name="Another exact parent")
    )
    second = ri.model_copy(update=dict(source=target))
    operations = [
        (pi, "REPLACE", cut.publications[0].command.policy),
        (ri, "REPLACE", None),
        (second, "REPLACE", None),
    ]
    entries = (*owner.identities, entry)
    if diamond:
        root = ri.source.model_copy(update=dict(ingredient_id=uuid4()))
        entries += (
            h.HierarchyTargetIdentity(
                target=root, identity=dict(id=root.ingredient_id, name="Diamond root")
            ),
        )
        operations += [
            (ri.model_copy(update=dict(source=root, destination=ri.source)), "REPLACE", None),
            (ri.model_copy(update=dict(source=root, destination=target)), "REPLACE", None),
        ]
    return rebuild(
        subject, owner=owner.model_copy(update=dict(identities=entries)), operations=operations
    )


@pytest.mark.parametrize("diamond", [False, True])
def test_hc37_hc39_no_favorable_parent_or_diamond_choice(diamond):
    result = derive(
        ambiguous(inputs(source_kind="INGREDIENT", destination_kind="INGREDIENT"), diamond=diamond)
    )
    assert result.inherited.source_reason == "MULTIPLE_INCOMING_RELATIONS"
    assert result.hierarchy.rows[0].selected_relation is None


@pytest.mark.parametrize("state", ["DECLARED", "RETRACTED"])
def test_hc22_direct_suppression_keeps_ambiguous_source_diagnostics(state):
    subject = ambiguous(
        inputs(source_kind="INGREDIENT", destination_kind="INGREDIENT", destination_state=state)
    )
    result = derive(subject | dict(parent=None))
    assert result.inherited.status == "SUPPRESSED"
    assert result.hierarchy.rows[0].reason == "MULTIPLE_INCOMING_RELATIONS"
    assert len(result.hierarchy.rows[0].diagnostics) == 2


@pytest.mark.parametrize("mutation", ["grant", "journal", "reader", "owner"])
def test_hc23_hc73_invalid_source_not_masked_by_suppression(mutation):
    data = canonical(inputs(destination_state="DECLARED"))
    source = data["hierarchy_source"]
    if mutation == "grant":
        source["authority_events"].pop()
    elif mutation == "journal":
        source["mutations"].pop(0)
    elif mutation == "reader":
        source["reader_grant_id"] = str(uuid4())
    else:
        source["owner_source"]["identities"].pop()
    with pytest.raises(ValueError):
        derive(data)


def test_hc40_cycle_rejected_without_traversal_or_inverse_inference():
    subject = inputs(source_kind="INGREDIENT", destination_kind="INGREDIENT")
    pi, ri = identities(subject)
    with pytest.raises(ValueError, match="cycle"):
        rebuild(
            subject,
            operations=[
                (pi, "REPLACE", subject["hierarchy_source"].publications[0].command.policy),
                (ri, "REPLACE", None),
                (
                    ri.model_copy(update=dict(source=ri.destination, destination=ri.source)),
                    "REPLACE",
                    None,
                ),
            ],
        )
    source = subject["hierarchy_source"]
    # A valid cut requesting the source endpoint does not reverse the authored edge.
    inverse = source.model_copy(
        update=dict(request=source.request.model_copy(update=dict(requested_targets=(ri.source,))))
    )
    # Use the same parent/destination ledger but reverse only the exact input children.
    result = derive(
        dict(destination=subject["parent"], parent=subject["destination"], hierarchy_source=inverse)
    )
    assert result.inherited.status == "SUPPRESSED"
    assert result.hierarchy.rows[0].reason == "NO_RELATION"


@pytest.mark.parametrize(
    "mode,reason",
    [
        ("RETRACT", "SUPPORT_RETRACTED"),
        ("NONE", "SUPPORT_REVIEWED_NONE"),
        ("ABSENT", "SUPPORT_REVIEWED_ABSENT"),
        ("UNRESOLVED", "SUPPORT_UNRESOLVED"),
        ("REPLACE", "SUPPORT_SUPERSEDED"),
    ],
)
def test_hc41_hc44_catalog_partial_positive_and_fresh_correction(mode, reason):
    subject = classification_input()
    old = derive(subject)
    assert old.inherited.status == "AVAILABLE"
    source, owner = subject["hierarchy_source"], subject["hierarchy_source"].owner_source
    stream, extra = catalog_correction(owner.catalog_streams[0], mode=mode)
    fresh_owner = owner.model_copy(
        update=dict(
            catalog_frontier=2,
            catalog_streams=(stream,),
            terms=(*owner.terms, extra) if extra else owner.terms,
        )
    )
    fresh = derive(
        subject | dict(hierarchy_source=source.model_copy(update=dict(owner_source=fresh_owner)))
    )
    assert fresh.inherited.source_reason == reason
    assert fresh.fingerprint != old.fingerprint
    assert derive(subject) == old


def test_hc38_unusable_competing_support_is_still_ambiguous():
    subject = classification_input()
    source = subject["hierarchy_source"]
    pi, ri = identities(subject)
    # A second exact pair remains active even when classification support for the
    # first relation is retracted. Caller supplying only the usable parent cannot filter it.
    target = ri.source.model_copy(update=dict(ingredient_id=uuid4()))
    entry = h.HierarchyTargetIdentity(
        target=target, identity=dict(id=target.ingredient_id, name="Other")
    )
    owner = source.owner_source.model_copy(
        update=dict(identities=(*source.owner_source.identities, entry))
    )
    relation = source.publications[1].command.relation.model_dump(
        exclude={"policy_revision_id", "policy_fingerprint"}
    )
    built = rebuild(
        subject,
        owner=owner,
        operations=[
            (pi, "REPLACE", source.publications[0].command.policy),
            (ri, "REPLACE", relation),
            (ri.model_copy(update=dict(source=target)), "REPLACE", None),
        ],
    )
    stream, _ = catalog_correction(owner.catalog_streams[0])
    fresh = built["hierarchy_source"].model_copy(
        update=dict(
            owner_source=owner.model_copy(
                update=dict(catalog_frontier=2, catalog_streams=(stream,))
            )
        )
    )
    result = derive(built | dict(hierarchy_source=fresh))
    assert result.inherited.source_reason == "MULTIPLE_INCOMING_RELATIONS"
    assert {d.support_status for d in result.hierarchy.rows[0].diagnostics} == {
        None,
        "SUPPORT_RETRACTED",
    }


@pytest.mark.parametrize("dimension", ["METHOD", "FLAVOR", "MAIN_PROTEIN"])
def test_hc42_hc43_exact_recipe_classification_context(dimension):
    subject = classification_input(dimension=dimension)
    result = derive(subject)
    assert result.inherited.status == "AVAILABLE"
    binding = result.inherited.trace.relation_identity.recipe_bindings[0]
    assert binding.key.dimension == dimension
    assert binding.recipe_version_id == subject["hierarchy_source"].owner_source.recipes[0].id
    assert (binding.path is None) == (dimension == "METHOD")
    data = canonical(subject)
    data["hierarchy_source"]["publications"][1]["command"]["identity"]["recipe_bindings"][0][
        "recipe_version_id"
    ] = str(uuid4())
    with pytest.raises(ValueError):
        derive(data)


def test_hc39_same_source_different_recipe_contexts_not_deduplicated():
    subject = inputs(source_kind="DIRECT_RECIPE")
    source = subject["hierarchy_source"]
    pi, ri = identities(subject)
    recipe = source.owner_source.recipes[0]
    newer = recipe.model_copy(update=dict(id=uuid4(), version=2))
    # RecipeVersion children are version-bound; use another complete authored version.
    from app.modules.recipes.contracts import RecipeVersionSnapshot
    from recipe_fixtures import recipe_data

    body = recipe_data()
    body["recipe"] = recipe.recipe.model_dump()
    body["version"] = 2
    for transformation in body["transformations"]:
        transformation["method"] = recipe.recipe.cooking_method
    newer = RecipeVersionSnapshot.model_validate(body)
    second = ri.model_copy(
        update=dict(
            recipe_bindings=(
                ri.recipe_bindings[0].model_copy(update=dict(recipe_version_id=newer.id)),
            )
        )
    )
    owner = source.owner_source.model_copy(update=dict(recipes=(recipe, newer)))
    result = derive(
        rebuild(
            subject,
            owner=owner,
            operations=[
                (pi, "REPLACE", source.publications[0].command.policy),
                (ri, "REPLACE", None),
                (second, "REPLACE", None),
            ],
        )
    )
    assert result.inherited.source_reason == "MULTIPLE_INCOMING_RELATIONS"


@pytest.mark.parametrize(
    "mutation", ["label", "amount", "descriptor", "anchor", "matrix", "denied"]
)
def test_hc49_hc50_hc55_hc56_forged_published_policy_fails_after_rehash(mutation):
    subject = inputs()
    source = subject["hierarchy_source"]
    body = canonical(source.publications[0].command.policy)
    direction = next(d for d in body["directions"] if d["enabled"])
    like = next(r for r in direction["rows"] if r["source_affinity_value"] == "LIKE")
    if mutation == "label":
        like["source_affinity_value"] = "NEUTRAL"
    elif mutation == "amount":
        like["expected_source_amount"] = dict(numerator=1, denominator=2)
    elif mutation == "descriptor":
        like["source_descriptor"]["compatibility_policy_fingerprint"] = "f" * 64
    elif mutation == "anchor":
        like["output_amount"] = dict(numerator=-1, denominator=2)
    elif mutation == "matrix":
        body["directions"].pop()
    else:
        next(d for d in body["directions"] if not d["enabled"])["attenuation"] = dict(
            numerator=1, denominator=2
        )
    # Rehashed forged publication cannot skip recursive policy validation.
    forged = h.HierarchyTransferPolicy.model_construct(
        **(body | dict(provenance=source.publications[0].command.policy.provenance))
    )
    pi, ri = identities(subject)
    with pytest.warns(UserWarning, match="Pydantic serializer warnings"):
        with pytest.raises(ValueError):
            derive(
                rebuild(
                    subject,
                    transfer=forged,
                    operations=[(pi, "REPLACE", forged), (ri, "REPLACE", None)],
                )
            )


@pytest.mark.parametrize(
    "amount",
    [
        dict(numerator=0, denominator=1),
        dict(numerator=-1, denominator=2),
        dict(numerator=2, denominator=1),
        dict(numerator=True, denominator=2),
        dict(numerator="1", denominator=2),
        dict(numerator=0.5, denominator=1),
        dict(numerator=2, denominator=4),
    ],
)
def test_hc62_invalid_authored_attenuation_rejected(amount):
    data = canonical(inputs())
    body = data["hierarchy_source"]["publications"][0]["command"]["policy"]
    next(d for d in body["directions"] if d["enabled"])["attenuation"] = amount
    with pytest.raises(ValueError):
        derive(data)


def test_hc44_hc66_policy_replacement_requires_fresh_relation_pin():
    subject = inputs()
    old = derive(subject)
    source = subject["hierarchy_source"]
    pi, ri = identities(subject)
    policy = source.publications[0].command.policy
    replacement = policy.model_copy(update=dict(policy_version=2))
    fresh = rebuild(
        subject,
        operations=[
            (pi, "REPLACE", policy),
            (ri, "REPLACE", None),
            (pi, "REPLACE", replacement),
            (ri, "REPLACE", None),
        ],
    )
    new = derive(fresh)
    assert new.inherited.value.amount == old.inherited.value.amount
    assert new.inherited.value.coordinate != old.inherited.value.coordinate
    assert (
        new.inherited.value.coordinate.transfer_policy_semantic_fingerprint
        == replacement.fingerprint()
    )
    assert derive(subject) == old


def test_hc68_review_history_does_not_amplify_or_mint_strength():
    subject = inputs()
    old = derive(subject)
    source = subject["hierarchy_source"]
    pi, ri = identities(subject)
    fresh = rebuild(
        subject,
        operations=[
            (pi, "REPLACE", source.publications[0].command.policy),
            (ri, "REPLACE", None),
            (ri, "REPLACE", None),
            (ri, "REPLACE", None),
        ],
    )
    result = derive(fresh)
    assert result.inherited.value == old.inherited.value
    assert result.inherited.trace.attenuation == old.inherited.trace.attenuation
    assert result.evidence_strength == "NOT_DERIVED"
    assert result.fingerprint != old.fingerprint


@pytest.mark.parametrize("field", ["eligibility", "selection", "diagnostics"])
def test_hc71_edited_cached_hierarchy_rejects_even_rehashed(field):
    result = derive(inputs())

    def edit(d):
        row = d["hierarchy"]["rows"][0]
        if field == "eligibility":
            row["status"] = "UNAVAILABLE"
        elif field == "selection":
            row["selected_relation"] = None
        else:
            row["diagnostics"] = []

    with pytest.raises(ValueError):
        c.OneHopHierarchicalMemberPreferenceDraft.model_validate(rehashed_root(result, edit))
