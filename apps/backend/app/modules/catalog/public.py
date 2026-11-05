"""Source catalog reads with exact reference identity/provenance."""

from sqlalchemy import select

from app.domain.units import Provenance, Quantity
from app.modules.catalog.contracts import (
    AffinityFeatureTermFact,
    IngredientIdentityFact,
    NutritionFact,
    NutritionReferenceFact,
    NutritionValues,
)
from app.modules.catalog.models import AffinityFeatureTerm, Ingredient
from app.modules.catalog.models import NutritionFact as NutritionRow


def catalog_facts(session, ingredient_ids):
    identities = tuple(
        IngredientIdentityFact(id=r.id, name=r.name)
        for r in session.scalars(
            select(Ingredient).where(Ingredient.id.in_(ingredient_ids)).order_by(Ingredient.id)
        )
    )
    nutrients = tuple(
        NutritionReferenceFact(
            id=r.id,
            fact=NutritionFact(
                ingredient_id=r.ingredient_id,
                reference=Quantity(amount=r.reference_amount, basis=r.basis),
                nutrients=NutritionValues(
                    energy_kcal=r.energy_kcal,
                    protein_g=r.protein_g,
                    fat_g=r.fat_g,
                    carbohydrate_g=r.carbohydrate_g,
                ),
                status=r.status,
                provenance=Provenance(
                    kind=r.source_kind,
                    source_system=r.source_system,
                    external_record_id=r.external_record_id,
                    source_version=r.source_version,
                    source_uri=r.source_uri,
                    content_hash=r.content_hash,
                    observed_at=r.observed_at,
                ),
            ),
        )
        for r in session.scalars(
            select(NutritionRow)
            .where(NutritionRow.ingredient_id.in_(ingredient_ids))
            .order_by(NutritionRow.id)
        )
    )
    return identities, nutrients


def capture_resolution_catalog(session, ingredient_ids, *, row_budget=8192):
    """NRE owner read: bound the complete selected closure before materializing rows."""
    from sqlalchemy import func

    if type(row_budget) is not int or not 0 <= row_budget <= 8192:
        raise ValueError("RESOURCE_EXCEEDED: owner row budget")
    ids = tuple(sorted(set(ingredient_ids), key=str))
    if len(ids) > 1024:
        raise ValueError("RESOURCE_EXCEEDED: ingredient closure")
    count = session.scalar(
        select(func.count()).select_from(NutritionRow).where(NutritionRow.ingredient_id.in_(ids))
    )
    identity_count = session.scalar(
        select(func.count()).select_from(Ingredient).where(Ingredient.id.in_(ids))
    )
    if count > 512 or count + identity_count > row_budget:
        raise ValueError("RESOURCE_EXCEEDED: nutrition reference rows")
    # All statuses/versions, including unselected references, are retained.
    return catalog_facts(session, ids)


def add_affinity_feature_term(session, fact):
    """Internal curated-source write, not an unreviewed import or public HTTP endpoint."""
    fact = AffinityFeatureTermFact.model_validate(fact.model_dump())
    fields = fact.model_dump(exclude={"provenance", "contract_version"})
    fields.update(fact.provenance.model_dump(exclude={"kind", "source_uri"}))
    fields.update(
        source_kind=fact.provenance.kind,
        source_uri=str(fact.provenance.source_uri) if fact.provenance.source_uri else None,
    )
    session.add(AffinityFeatureTerm(**fields))
    session.flush()
    return fact


def affinity_feature_terms(session, ids):
    return tuple(
        AffinityFeatureTermFact(
            **{
                k: getattr(row, k)
                for k in ("id", "kind", "code", "version", "label", "definition", "status")
            },
            provenance=Provenance(
                kind=row.source_kind,
                **{
                    k: getattr(row, k)
                    for k in (
                        "source_system",
                        "external_record_id",
                        "source_version",
                        "source_uri",
                        "content_hash",
                        "observed_at",
                    )
                },
            ),
        )
        for row in session.scalars(
            select(AffinityFeatureTerm).where(AffinityFeatureTerm.id.in_(ids))
        )
    )

# Additive curated association source surface. No Recipe dependency.
from app.modules.catalog.feature_repository import (  # noqa: E402,F401  # noqa: E402,F401
    IngredientProteinService,
    ingredient_protein_frontier,
    ingredient_protein_sources,
    lock_ingredient_protein_frontier,
)


def ingredient_identities(session, ingredient_ids):
    """Identity-only canonical owner read; no nutrition or inferred feature evidence."""
    return tuple(
        IngredientIdentityFact(id=row.id, name=row.name)
        for row in session.execute(
            select(Ingredient.id, Ingredient.name)
            .where(Ingredient.id.in_(ingredient_ids)).order_by(Ingredient.id)
        )
    )


def reviewed_affinity_feature_terms(session, ids):
    """Exact vocabulary identities; never silently filter an existing DRAFT term."""
    terms = affinity_feature_terms(session, ids)
    if any(t.status != "REVIEWED" for t in terms):
        raise ValueError("TARGET_NOT_REVIEWED: reviewed vocabulary identity required")
    return terms
