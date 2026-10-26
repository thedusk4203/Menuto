"""Canonical owner support and explicit stable recipe/version context; no preference consumer."""

from uuid import uuid4

import pytest
from app.modules.catalog.models import Ingredient
from app.modules.catalog.public import (
    IngredientProteinService,
    add_affinity_feature_term,
    ingredient_protein_frontier,
)
from app.modules.identity.models import User
from app.modules.preferences.hierarchy_resolution import resolve_hierarchy_sources
from app.modules.recipes.contracts import FeatureSelectedPath
from app.modules.recipes.public import CulinaryFeatureService, culinary_feature_frontier
from feature_fixtures import review_command
from hierarchy_fixtures import policy as authored_policy
from hierarchy_postgres_fixtures import capture, publication, publish
from hierarchy_postgres_fixtures import hierarchy_server as hierarchy_server
from hierarchy_postgres_fixtures import hierarchy_source as hierarchy_source
from preference_fixtures import term
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_postgres_culinary_features import catq, nextq
from test_postgres_culinary_features import seed as seed_culinary

pytestmark = pytest.mark.postgres


def test_g02_unresolved_parent_is_diagnostic_not_silently_dropped(hierarchy_source):
    from app.modules.catalog.contracts import IngredientProteinReviewCommand
    from preference_fixtures import provenance

    s, q, receipt, actor, identity, relation = ingredient_support(hierarchy_source)
    publish(s, publication(s, identity=identity, relation=relation))
    with Session(s["engines"]["root"]) as root:
        other = Ingredient(name="Second reviewed parent")
        root.add(other)
        root.flush()
        second = IngredientProteinReviewCommand.model_validate(
            q.model_dump()
            | dict(
                ingredient_id=other.id,
                expected_catalog_frontier=ingredient_protein_frontier(root),
                idempotency_key=uuid4().hex,
                provenance=provenance().model_dump(),
            )
        )
        second_receipt = IngredientProteinService(root, actor_user_id=actor).write(second)
        other_target = dict(kind="INGREDIENT", ingredient_id=str(other.id))
        root.commit()
    second_identity = dict(identity, source=other_target)
    second_relation = dict(relation, support_review_id=second_receipt.review_id)
    publish(s, publication(s, identity=second_identity, relation=second_relation))
    with Session(s["engines"]["root"]) as root:
        retired = nextq(
            second, second_receipt, frontier=ingredient_protein_frontier(root), action="RETRACT"
        )
        IngredientProteinService(root, actor_user_id=actor).write(retired)
        root.commit()
    row = resolve_hierarchy_sources(capture(s, [s["destination"]])).rows[0]
    assert row.reason == "MULTIPLE_INCOMING_RELATIONS" and row.selected_relation is None
    assert len(row.diagnostics) == 2
    assert {d.support_status for d in row.diagnostics} == {None, "SUPPORT_RETRACTED"}


def test_i04_reviewed_scope_uses_exact_nonzero_authored_path(hierarchy_source):
    from app.modules.recipes.contracts import CulinaryFeaturePathKey
    from feature_fixtures import path_key

    s = hierarchy_source
    with Session(s["engines"]["root"]) as root:
        recipe, actor, terms = seed_culinary(root, "FLAVOR")
        key = path_key(recipe).model_dump()
        slot = next(x for x in key["slots"] if x["requirement_id"] == recipe.ingredients[0].id)
        slot["adjustment"] = "AUTHORED_ENVELOPE"
        key["scope"] = "REVIEWED_SCOPE"
        key = CulinaryFeaturePathKey.model_validate(key)
        q = review_command(
            recipe,
            terms,
            dimension="FLAVOR",
            key=key,
            expected_recipe_frontier=culinary_feature_frontier(root),
        )
        receipt = CulinaryFeatureService(root, actor_user_id=actor).write(q)
        root.commit()
    s = dict(
        s,
        policy=authored_policy(source_kind="DIRECT_RECIPE", destination_kind="FLAVOR"),
        target=dict(kind="DIRECT_RECIPE", recipe_id=str(recipe.recipe.id)),
        destination=dict(kind="FLAVOR", feature_term_id=str(terms[0].id)),
    )
    p = publish(s, publication(s))
    path = FeatureSelectedPath(
        tier_id=recipe.portion_tiers[0].id,
        selected_rule_ids=(),
        deltas=tuple((i.id, 10 if n == 0 else 0) for n, i in enumerate(recipe.ingredients)),
    )
    identity = dict(
        kind="RELATION",
        policy_id=s["policy"].policy_id,
        source=s["target"],
        destination=s["destination"],
        recipe_bindings=[dict(endpoint="SOURCE", recipe_version_id=recipe.id, key=key, path=path)],
    )
    relation = dict(
        policy_revision_id=p.publication.id,
        policy_fingerprint=s["policy"].fingerprint(),
        support_mode="CLASSIFICATION_BOUND_PAIR",
        support_review_id=receipt.review_id,
        catalog_review_ids=[],
    )
    publish(s, publication(s, identity=identity, relation=relation))
    assert (
        resolve_hierarchy_sources(capture(s, [s["destination"]])).rows[0].status
        == "ELIGIBLE_RELATION"
    )


def ingredient_support(s, *, coverage="COMPLETE", positives=True):
    with Session(s["engines"]["root"]) as session:
        actor = User(display_name="Synthetic classification curator")
        ingredient = Ingredient(name="Exact classification support target")
        session.add_all([actor, ingredient])
        session.flush()
        terms = (term("PROTEIN"), term("PROTEIN"))
        for t in terms:
            add_affinity_feature_term(session, t)
        q = catq(
            session,
            ingredient.id,
            terms,
            coverage=coverage,
            positive_term_ids=(terms[0].id,) if positives else (),
        )
        receipt = IngredientProteinService(session, actor_user_id=actor.id).write(q)
        session.commit()
        source = dict(kind="INGREDIENT", ingredient_id=str(ingredient.id))
        actor_id = actor.id
    s = dict(
        s,
        target=source,
        policy=authored_policy(source_kind="INGREDIENT", destination_kind="PROTEIN"),
        destination=dict(kind="PROTEIN", feature_term_id=str(terms[0].id)),
    )
    p = publish(s, publication(s))
    identity = dict(
        kind="RELATION",
        policy_id=s["policy"].policy_id,
        source=s["target"],
        destination=s["destination"],
        recipe_bindings=[],
    )
    relation = dict(
        policy_revision_id=p.publication.id,
        policy_fingerprint=s["policy"].fingerprint(),
        support_mode="CLASSIFICATION_BOUND_PAIR",
        support_review_id=receipt.review_id,
        catalog_review_ids=[],
    )
    return s, q, receipt, actor_id, identity, relation


@pytest.mark.parametrize("coverage", ["PARTIAL", "COMPLETE"])
def test_i03_canonical_ingredient_positive_support_partial_or_complete(hierarchy_source, coverage):
    s, q, receipt, actor, identity, relation = ingredient_support(
        hierarchy_source, coverage=coverage
    )
    publish(s, publication(s, identity=identity, relation=relation))
    result = resolve_hierarchy_sources(capture(s, [s["destination"]]))
    assert result.rows[0].status == "ELIGIBLE_RELATION"
    assert result.rows[0].selected_relation.command.relation.support_review_id == receipt.review_id


@pytest.mark.parametrize("coverage", ["PARTIAL", "COMPLETE"])
def test_i03_no_absence_unresolved_or_reviewed_none_can_publish_relation(
    hierarchy_source, coverage
):
    s, q, receipt, actor, identity, relation = ingredient_support(
        hierarchy_source, coverage=coverage, positives=False
    )
    with pytest.raises(DBAPIError, match="positive Catalog support"):
        publish(s, publication(s, identity=identity, relation=relation))


@pytest.mark.parametrize("mode", ["NONE", "ABSENT", "RETRACTED", "REPLACED"])
def test_r02_catalog_correction_changes_fresh_support_but_old_cut_replays(hierarchy_source, mode):
    s, q, receipt, actor, identity, relation = ingredient_support(hierarchy_source)
    publish(s, publication(s, identity=identity, relation=relation))
    old = capture(s, [s["destination"]])
    with Session(s["engines"]["root"]) as session:
        changes = dict(positive_term_ids=() if mode in {"NONE", "ABSENT"} else q.positive_term_ids)
        if mode == "ABSENT":
            changes["positive_term_ids"] = (
                next(t for t in q.covered_term_ids if t not in q.positive_term_ids),
            )
        updated = nextq(
            q,
            receipt,
            frontier=ingredient_protein_frontier(session),
            action="RETRACT" if mode == "RETRACTED" else "REPLACE",
            **({} if mode == "RETRACTED" else changes),
        )
        IngredientProteinService(session, actor_user_id=actor).write(updated)
        session.commit()
    result = resolve_hierarchy_sources(capture(s, [s["destination"]]))
    expected = {
        "NONE": "SUPPORT_REVIEWED_NONE",
        "ABSENT": "SUPPORT_REVIEWED_ABSENT",
        "RETRACTED": "SUPPORT_RETRACTED",
        "REPLACED": "SUPPORT_SUPERSEDED",
    }[mode]
    assert result.rows[0].reason == expected
    assert resolve_hierarchy_sources(old).rows[0].status == "ELIGIBLE_RELATION"


@pytest.mark.parametrize("dimension", ["METHOD", "FLAVOR", "MAIN_PROTEIN"])
def test_i04_frozen_recipe_classification_full_support_and_exact_context(
    hierarchy_source, dimension
):
    s = hierarchy_source
    with Session(s["engines"]["root"]) as session:
        recipe, actor, terms = seed_culinary(
            session, "PROTEIN" if dimension == "MAIN_PROTEIN" else dimension
        )
        extra = {}
        supports = []
        if dimension == "MAIN_PROTEIN":
            ingredient = recipe.ingredients[0]
            assoc = IngredientProteinService(session, actor_user_id=actor).write(
                catq(session, ingredient.ingredient_id, terms)
            )
            supports = [
                dict(
                    term_id=terms[0].id,
                    requirement_id=ingredient.id,
                    ingredient_id=ingredient.ingredient_id,
                    catalog_review_id=assoc.review_id,
                )
            ]
            extra["expected_catalog_frontier"] = ingredient_protein_frontier(session)
        q = review_command(
            recipe,
            terms,
            dimension=dimension,
            expected_recipe_frontier=culinary_feature_frontier(session),
            supports=supports,
            **extra,
        )
        receipt = CulinaryFeatureService(session, actor_user_id=actor).write(q)
        session.commit()
    kind = "PROTEIN" if dimension == "MAIN_PROTEIN" else dimension
    s = dict(
        s,
        policy=authored_policy(source_kind="DIRECT_RECIPE", destination_kind=kind),
        target=dict(kind="DIRECT_RECIPE", recipe_id=str(recipe.recipe.id)),
        destination=dict(kind=kind, feature_term_id=str(terms[0].id)),
    )
    p = publish(s, publication(s))
    path = (
        None
        if dimension == "METHOD"
        else FeatureSelectedPath(
            tier_id=recipe.portion_tiers[0].id,
            selected_rule_ids=(),
            deltas=tuple((i.id, 0) for i in recipe.ingredients),
        )
    )
    identity = dict(
        kind="RELATION",
        policy_id=s["policy"].policy_id,
        source=s["target"],
        destination=s["destination"],
        recipe_bindings=[
            dict(endpoint="SOURCE", recipe_version_id=recipe.id, key=q.key, path=path)
        ],
    )
    relation = dict(
        policy_revision_id=p.publication.id,
        policy_fingerprint=s["policy"].fingerprint(),
        support_mode="CLASSIFICATION_BOUND_PAIR",
        support_review_id=receipt.review_id,
        catalog_review_ids=[x["catalog_review_id"] for x in supports],
    )
    publish(s, publication(s, identity=identity, relation=relation))
    cut = capture(s, [s["destination"]])
    result = resolve_hierarchy_sources(cut)
    assert result.rows[0].status == "ELIGIBLE_RELATION"
    assert (
        result.rows[0].selected_relation.command.identity.recipe_bindings[0].recipe_version_id
        == recipe.id
    )
    captured = next(r for r in cut.owner_source.recipes if r.id == recipe.id)
    assert captured == recipe
    from app.domain.feature_identity import canonical
    from app.modules.preferences.hierarchy_contracts import HierarchySourceSnapshotDraft

    forged = canonical(cut)
    forged["owner_source"]["recipes"][0]["procedure"] = "Forged body under an immutable version ID"
    with pytest.raises(ValueError, match="Immutable RecipeVersion"):
        HierarchySourceSnapshotDraft.model_validate(forged)
    # A later version of the same stable Recipe cannot retarget this relation.
    from app.modules.recipes.contracts import RecipeVersionSnapshot
    from app.modules.recipes.repository import RecipeRepository
    from recipe_fixtures import recipe_data

    data = recipe_data()
    data["recipe"] = recipe.recipe.model_dump()
    data["version"] = 2
    newer = RecipeVersionSnapshot.model_validate(data)
    with Session(s["engines"]["root"]) as session:
        ids = {i.ingredient_id for i in newer.ingredients} | {
            r.replacement_ingredient_id for r in newer.variant_rules
        }
        session.add_all([Ingredient(id=i, name="New version ingredient") for i in ids])
        session.flush()
        RecipeRepository(session).add_version(newer)
        session.commit()
    fresh = capture(s, [s["destination"]])
    assert {r.id for r in fresh.owner_source.recipes} == {recipe.id}
    assert resolve_hierarchy_sources(fresh).rows[0].status == "ELIGIBLE_RELATION"
    with Session(s["engines"]["root"]) as session:
        revoked = nextq(
            q, receipt, frontier=culinary_feature_frontier(session), action="RETRACT", supports=()
        )
        CulinaryFeatureService(session, actor_user_id=actor).write(revoked)
        session.commit()
    assert (
        resolve_hierarchy_sources(capture(s, [s["destination"]])).rows[0].reason
        == "SUPPORT_RETRACTED"
    )
    assert resolve_hierarchy_sources(cut).rows[0].status == "ELIGIBLE_RELATION"


def test_i04_missing_or_forged_recipe_context_never_selects_latest(hierarchy_source):
    s = hierarchy_source
    with Session(s["engines"]["root"]) as session:
        recipe, actor, terms = seed_culinary(session, "METHOD")
        session.commit()
    s = dict(
        s,
        policy=authored_policy(source_kind="DIRECT_RECIPE", destination_kind="METHOD"),
        target=dict(kind="DIRECT_RECIPE", recipe_id=str(recipe.recipe.id)),
        destination=dict(kind="METHOD", feature_term_id=str(terms[0].id)),
    )
    p = publish(s, publication(s))
    identity = dict(
        kind="RELATION",
        policy_id=s["policy"].policy_id,
        source=s["target"],
        destination=s["destination"],
        recipe_bindings=[dict(endpoint="SOURCE", recipe_version_id=uuid4(), key=None, path=None)],
    )
    relation = dict(
        policy_revision_id=p.publication.id,
        policy_fingerprint=s["policy"].fingerprint(),
        support_mode="REVIEWED_EXACT_PAIR",
        support_review_id=None,
        catalog_review_ids=[],
    )
    with pytest.raises(DBAPIError, match="reviewed RecipeVersion"):
        publish(s, publication(s, identity=identity, relation=relation))


def test_i03_hierarchy_curator_cannot_publish_classification_fact(hierarchy_source):
    with Session(hierarchy_source["engines"]["curator"]) as session:
        with pytest.raises(DBAPIError, match="permission denied"):
            session.execute(text("UPDATE ingredient_protein_frontier SET generation=generation+1"))


def test_i03_reviewed_reverse_direction_requires_its_own_policy_and_relation(hierarchy_source):
    s, q, receipt, actor, identity, relation = ingredient_support(hierarchy_source)
    s = dict(
        s,
        policy=authored_policy(source_kind="PROTEIN", destination_kind="INGREDIENT"),
        target=s["destination"],
        destination=s["target"],
    )
    p = publish(s, publication(s))
    reverse = dict(
        kind="RELATION",
        policy_id=s["policy"].policy_id,
        source=s["target"],
        destination=s["destination"],
        recipe_bindings=[],
    )
    relation.update(
        policy_revision_id=p.publication.id, policy_fingerprint=s["policy"].fingerprint()
    )
    publish(s, publication(s, identity=reverse, relation=relation))
    assert (
        resolve_hierarchy_sources(capture(s, [s["destination"]])).rows[0].status
        == "ELIGIBLE_RELATION"
    )


def test_i04_reviewed_exact_recipe_pair_needs_version_but_no_classification_claim(hierarchy_source):
    s = hierarchy_source
    with Session(s["engines"]["root"]) as session:
        recipe, actor, terms = seed_culinary(session, "METHOD")
        session.commit()
    s = dict(
        s,
        policy=authored_policy(source_kind="DIRECT_RECIPE", destination_kind="METHOD"),
        target=dict(kind="DIRECT_RECIPE", recipe_id=str(recipe.recipe.id)),
        destination=dict(kind="METHOD", feature_term_id=str(terms[0].id)),
    )
    p = publish(s, publication(s))
    identity = dict(
        kind="RELATION",
        policy_id=s["policy"].policy_id,
        source=s["target"],
        destination=s["destination"],
        recipe_bindings=[dict(endpoint="SOURCE", recipe_version_id=recipe.id, key=None, path=None)],
    )
    relation = dict(
        policy_revision_id=p.publication.id,
        policy_fingerprint=s["policy"].fingerprint(),
        support_mode="REVIEWED_EXACT_PAIR",
        support_review_id=None,
        catalog_review_ids=[],
    )
    publish(s, publication(s, identity=identity, relation=relation))
    assert (
        resolve_hierarchy_sources(capture(s, [s["destination"]])).rows[0].status
        == "ELIGIBLE_RELATION"
    )
