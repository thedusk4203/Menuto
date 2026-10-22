"""Draft retail-to-inventory seam only; no InventoryLot persistence or workflow."""

from typing import Literal

from pydantic import model_validator

from app.domain.snapshots import RawIngredientAssetFact
from app.modules.retail.contracts import IngredientProductMapFact


class RetailSourcedAPAssetDraft(RawIngredientAssetFact):
    """Inventory owns this future handoff. AP source evidence must not be discarded.

    The old neutral m0 RawIngredientAssetFact is still an incomplete validator draft,
    not an accepted retail acquisition handoff. This contract grants no physical stock.
    """

    contract_version: Literal["inventory-retail-origin.m1-draft.2"] = (
        "inventory-retail-origin.m1-draft.2"
    )
    validation_ready: Literal[False] = False
    retail_mapping: IngredientProductMapFact

    @model_validator(mode="after")
    def preserve_product_mapping(self):
        if self.quantity.basis != "AP_G":
            raise ValueError("Retail AP asset handoff requires AP_G")
        if self.ingredient_id != self.retail_mapping.ingredient_id:
            raise ValueError("Inventory ingredient and product mapping must agree")
        if self.retail_mapping.status != "REVIEWED":
            raise ValueError("Retail origin requires reviewed mapping evidence")
        return self
