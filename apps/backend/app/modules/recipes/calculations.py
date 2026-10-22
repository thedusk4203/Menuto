"""Deterministic culinary arithmetic, not a generator, optimizer or independent validator."""

from decimal import Inexact, Rounded, localcontext

from app.domain.units import CalculatedQuantity


def cooking_output(transformation, quantity):
    """Recomputable factor with no AP/EP conversion or implicit quantization."""
    if quantity.basis != transformation.source_basis:
        raise ValueError("Cooking transformation requires EP_RAW_G")
    with localcontext() as ctx:
        ctx.prec = 160
        ctx.traps[Inexact] = ctx.traps[Rounded] = True
        amount = quantity.amount * transformation.factor
    return CalculatedQuantity(amount=amount, basis=transformation.target_basis)
