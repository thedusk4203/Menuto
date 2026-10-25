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
