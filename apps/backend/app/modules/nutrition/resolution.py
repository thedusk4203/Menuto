"""Nutrition-owned exact source resolution. Not a second NutritionPolicyEngine."""

from decimal import Decimal, Inexact, Rounded, localcontext

from pydantic import ValidationError

from app.domain.resolution import ResolutionError
from app.modules.nutrition.contracts import ResolvedNutrients, ResolvedNutritionPortion


def resolve_nutrition(*, ingredient_id, quantity, references, as_of, reference_id=None):
    matches = [
        r
        for r in references
        if r.fact.ingredient_id == ingredient_id
        and r.fact.reference.basis == quantity.basis
        and r.fact.status == "REVIEWED"
        and r.fact.provenance.observed_at <= as_of
    ]
    if reference_id is not None:
        matches = [r for r in matches if r.id == reference_id]
    if len(matches) != 1:
        raise ResolutionError(
            "NUTRITION_REFERENCE_UNRESOLVED",
            "One compatible reviewed canonical reference is required",
        )
    r = matches[0]
    try:
        with localcontext() as ctx:
            ctx.prec = 160
            ctx.traps[Inexact] = ctx.traps[Rounded] = True
            values = {
                k: quantity.amount * v / r.fact.reference.amount
                for k, v in r.fact.nutrients.model_dump().items()
            }
            result = ResolvedNutrients(**values)
    except (ArithmeticError, ValidationError) as exc:
        raise ResolutionError(
            "NUTRITION_PRECISION_UNRESOLVED",
            "Exact nutrient result cannot be represented without rounding",
        ) from exc
    return ResolvedNutritionPortion(
        ingredient_id=ingredient_id, quantity=quantity, reference=r, nutrients=result
    )


def total_nutrition(portions):
    try:
        with localcontext() as ctx:
            ctx.prec = 160
            ctx.traps[Inexact] = ctx.traps[Rounded] = True
            return ResolvedNutrients(
                **{
                    k: sum((getattr(p.nutrients, k) for p in portions), Decimal(0))
                    for k in ResolvedNutrients.model_fields
                }
            )
    except (ArithmeticError, ValidationError) as exc:
        raise ResolutionError(
            "NUTRITION_PRECISION_UNRESOLVED",
            "Exact batch nutrient total exceeds supported precision",
        ) from exc


def check_candidate_members(
    *, household_id, tracked_member_id, participants, members, safety, ingredient_ids, as_of
):
    ids = {m.member_id for m in members if m.household_id == household_id}
    required = {p.member_id for p in participants.participants}
    tracked = [p.member_id for p in participants.participants if p.nutrition_role == "TRACKED"]
    if tracked != [tracked_member_id] or not required <= ids:
        raise ResolutionError(
            "PARTICIPANT_OWNER_MISMATCH",
            "All participants and the single tracked member must belong to household",
            rejected=True,
        )
    facts = {s.member_id: s for s in safety}
    if (
        len(facts) != len(safety)
        or len(ids) != len(members)
        or any(s.household_id != household_id for s in safety)
    ):
        raise ResolutionError(
            "SAFETY_OWNER_MISMATCH", "Canonical source ownership is ambiguous", rejected=True
        )
    unsupported = False
    for member in sorted(required, key=str):
        s = facts.get(member)
        if s is None or s.household_id != household_id:
            raise ResolutionError("SAFETY_SOURCE_UNRESOLVED", "Canonical member safety is missing")
        for source in s.constraints:
            c = source.constraint
            if (c.household_id, c.member_id) != (household_id, member):
                raise ResolutionError(
                    "SAFETY_OWNER_MISMATCH", "Restriction owner differs", rejected=True
                )
            if source.recorded_at > as_of:
                raise ResolutionError("SAFETY_SOURCE_AFTER_CUTOFF", "Safety source exceeds cutoff")
            if c.kind == "EXCLUDED_INGREDIENT" and c.ingredient_id in ingredient_ids:
                raise ResolutionError(
                    "FORBIDDEN_INGREDIENT",
                    "Participant excludes resolved ingredient",
                    rejected=True,
                )
            if c.kind != "EXCLUDED_INGREDIENT":
                unsupported = True
    if unsupported:
        raise ResolutionError(
            "SAFETY_CLASSIFICATION_UNAVAILABLE",
            "Allergen/diet classification source is not implemented",
        )
