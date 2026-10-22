"""Atomic authored aggregates. Caller owns transaction; reads return frozen contracts."""

from sqlalchemy import insert, select

from app.domain.units import Quantity
from app.modules.recipes import contracts as c
from app.modules.recipes import models as m


def source_fields(provenance):
    fields = provenance.model_dump()
    fields["source_kind"] = fields.pop("kind")
    if fields["source_uri"] is not None:
        fields["source_uri"] = str(fields["source_uri"])
    return fields


def source_contract(fields):
    source = {
        key: fields.pop(key)
        for key in (
            "source_kind",
            "source_system",
            "external_record_id",
            "source_version",
            "source_uri",
            "content_hash",
            "observed_at",
        )
    }
    source["kind"] = source.pop("source_kind")
    return c.RecipeProvenance(**source)


def plain(fields):
    fields = dict(fields)
    fields.pop("created_at", None)
    fields.pop("ordinal", None)
    fields.pop("authored_transaction", None)
    return fields


class RecipeRepository:
    def __init__(self, session):
        self.session = session

    def _insert(self, model, fields):
        self.session.execute(insert(model.__table__).values(**fields))

    def add_recipe(self, fact: c.RecipeFact):
        self._insert(m.Recipe, fact.model_dump(exclude={"contract_version"}))

    def recipe(self, identity):
        row = (
            self.session.execute(select(m.Recipe.__table__).where(m.Recipe.id == identity))
            .mappings()
            .one()
        )
        return c.RecipeFact(**plain(row))

    def add_version(self, snapshot: c.RecipeVersionSnapshot):
        # Revalidate even if a caller used Pydantic model_copy/model_construct.
        snapshot = c.RecipeVersionSnapshot.model_validate(snapshot.model_dump())
        if self.recipe(snapshot.recipe.id) != snapshot.recipe:
            raise ValueError("Recipe identity disagrees with persisted fact")
        # A failed aggregate write rolls back completely, even if caller catches the error.
        with self.session.begin_nested():
            fields = snapshot.model_dump(
                exclude={
                    "contract_version",
                    "recipe",
                    "ingredients",
                    "portion_tiers",
                    "variant_rules",
                    "approved_combinations",
                    "transformations",
                    "provenance",
                }
            )
            fields.update(recipe_id=snapshot.recipe.id, **source_fields(snapshot.provenance))
            self._insert(m.RecipeVersion, fields)
            for ordinal, fact in enumerate(snapshot.ingredients):
                fields = fact.model_dump(
                    exclude={"contract_version", "quantity", "scaling", "adjustment"}
                )
                fields.update(
                    ordinal=ordinal,
                    amount=fact.quantity.amount,
                    basis=fact.quantity.basis,
                    item_ref=fact.quantity.item_ref,
                    scaling_kind=fact.scaling.kind,
                    scaling_quantum=fact.scaling.quantum,
                    scaling_minimum=fact.scaling.minimum,
                    scaling_maximum=fact.scaling.maximum,
                    adjustment_kind=fact.adjustment.kind,
                    min_delta=fact.adjustment.min_delta,
                    max_delta=fact.adjustment.max_delta,
                    adjustment_step=fact.adjustment.step,
                )
                self._insert(m.RecipeIngredient, fields)
            for ordinal, tier in enumerate(snapshot.portion_tiers):
                self._insert(
                    m.RecipePortionTier,
                    {
                        **tier.model_dump(exclude={"contract_version", "quantities"}),
                        "ordinal": ordinal,
                    },
                )
                for index, quantity in enumerate(tier.quantities):
                    self._insert(
                        m.RecipeTierQuantity,
                        dict(
                            tier_id=tier.id,
                            recipe_version_id=snapshot.id,
                            ordinal=index,
                            requirement_id=quantity.requirement_id,
                            amount=quantity.amount,
                        ),
                    )
            for ordinal, rule in enumerate(snapshot.variant_rules):
                self._insert(
                    m.RecipeVariantRule,
                    {
                        **rule.model_dump(exclude={"contract_version", "provenance"}),
                        "ordinal": ordinal,
                        **source_fields(rule.provenance),
                    },
                )
            for ordinal, combo in enumerate(snapshot.approved_combinations):
                self._insert(
                    m.RecipeRuleCombination,
                    {
                        **combo.model_dump(exclude={"contract_version", "provenance", "rule_ids"}),
                        "ordinal": ordinal,
                        **source_fields(combo.provenance),
                    },
                )
                for index, rule_id in enumerate(combo.rule_ids):
                    self._insert(
                        m.RecipeCombinationMember,
                        dict(
                            combination_id=combo.id,
                            recipe_version_id=snapshot.id,
                            rule_id=rule_id,
                            ordinal=index,
                        ),
                    )
            for ordinal, transformation in enumerate(snapshot.transformations):
                self._insert(
                    m.PreparationTransformation,
                    {
                        **transformation.model_dump(exclude={"contract_version", "provenance"}),
                        "ordinal": ordinal,
                        **source_fields(transformation.provenance),
                    },
                )
            self._insert(m.RecipeVersionSeal, {"recipe_version_id": snapshot.id})

    def version(self, identity):
        table = m.RecipeVersion.__table__
        fields = plain(
            self.session.execute(select(table).where(table.c.id == identity)).mappings().one()
        )
        fields["recipe"] = self.recipe(fields.pop("recipe_id"))
        fields["provenance"] = source_contract(fields)

        def children(model):
            table = model.__table__
            return [
                plain(row)
                for row in self.session.execute(
                    select(table)
                    .where(table.c.recipe_version_id == identity)
                    .order_by(table.c.ordinal)
                ).mappings()
            ]

        ingredients = []
        for row in children(m.RecipeIngredient):
            row["quantity"] = Quantity(
                amount=row.pop("amount"), basis=row.pop("basis"), item_ref=row.pop("item_ref")
            )
            row["scaling"] = c.ScalingPolicy(
                kind=row.pop("scaling_kind"),
                quantum=row.pop("scaling_quantum"),
                minimum=row.pop("scaling_minimum"),
                maximum=row.pop("scaling_maximum"),
            )
            row["adjustment"] = c.QuantityAdjustmentPolicy(
                kind=row.pop("adjustment_kind"),
                min_delta=row.pop("min_delta"),
                max_delta=row.pop("max_delta"),
                step=row.pop("adjustment_step"),
            )
            ingredients.append(c.RecipeIngredientFact(**row))
        fields["ingredients"] = tuple(ingredients)
        quantities = children(m.RecipeTierQuantity)
        tiers = children(m.RecipePortionTier)
        for tier in tiers:
            tier["quantities"] = tuple(
                c.TierQuantity(requirement_id=q["requirement_id"], amount=q["amount"])
                for q in quantities
                if q["tier_id"] == tier["id"]
            )
        fields["portion_tiers"] = tuple(c.RecipePortionTierFact(**t) for t in tiers)
        for field, model, contract in (
            ("variant_rules", m.RecipeVariantRule, c.RecipeVariantRuleFact),
            ("transformations", m.PreparationTransformation, c.PreparationTransformationFact),
        ):
            rows = children(model)
            for row in rows:
                row["provenance"] = source_contract(row)
            fields[field] = tuple(contract(**r) for r in rows)
        members = children(m.RecipeCombinationMember)
        combinations = children(m.RecipeRuleCombination)
        for row in combinations:
            row["provenance"] = source_contract(row)
            row["rule_ids"] = tuple(
                r["rule_id"] for r in members if r["combination_id"] == row["id"]
            )
        fields["approved_combinations"] = tuple(
            c.RecipeRuleCombinationFact(**r) for r in combinations
        )
        return c.RecipeVersionSnapshot(**fields)
