"""Source catalog reads with exact reference identity/provenance."""

from sqlalchemy import select

from app.domain.units import Provenance, Quantity
from app.modules.catalog.contracts import (
    IngredientIdentityFact,
    NutritionFact,
    NutritionReferenceFact,
    NutritionValues,
)
from app.modules.catalog.models import Ingredient
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
