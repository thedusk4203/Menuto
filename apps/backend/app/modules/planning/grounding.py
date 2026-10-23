"""Assemble source-domain resolutions, never redefine their arithmetic or policies."""

from pydantic import ValidationError

from app.domain.resolution import ResolutionError
from app.modules.inventory.public import resolve_inventory_sources
from app.modules.nutrition.public import check_candidate_members, resolve_nutrition, total_nutrition
from app.modules.planning.contracts import (
    CandidateGroundingRequest,
    CandidateGroundingResult,
    CandidateGroundingSources,
    GroundedDishCandidate,
    GroundedIngredientFacts,
    GroundingIssue,
)
from app.modules.recipes.public import resolve_candidate_source
from app.modules.retail.public import resolve_procurement_sources


def resolve_captured_candidate(request, sources):
    """Pure captured-fact entrypoint; its inputs are not an authentication/authority token."""
    request = CandidateGroundingRequest.model_validate(request.model_dump())
    sources = CandidateGroundingSources.model_validate(sources.model_dump())
    issues = []
    try:
        if sources.inventory.household_id != request.household_id:
            raise ResolutionError(
                "INVENTORY_OWNER_MISMATCH", "Physical source crosses household", rejected=True
            )
        if sources.inventory.as_of != request.as_of:
            raise ResolutionError("SOURCE_CUTOFF_MISMATCH", "Physical source cutoff differs")
        rows, transforms = resolve_candidate_source(request.candidate, sources.recipe)
        ingredient_ids = {r.ingredient_id for r in rows}
        if not ingredient_ids <= {i.id for i in sources.ingredients}:
            raise ResolutionError(
                "INGREDIENT_SOURCE_MISSING", "Canonical ingredient identity missing"
            )
        if sources.recipe.provenance.observed_at > request.as_of:
            raise ResolutionError("RECIPE_SOURCE_AFTER_CUTOFF", "Recipe source exceeds cutoff")
        check_candidate_members(
            household_id=request.household_id,
            tracked_member_id=request.tracked_member_id,
            participants=request.participants,
            members=sources.members,
            safety=sources.member_safety,
            ingredient_ids=ingredient_ids,
            as_of=request.as_of,
        )
        selected = {s.requirement_id: s.reference_id for s in request.nutrition_selections}
        if not selected.keys() <= {r.requirement_id for r in rows}:
            raise ResolutionError(
                "NUTRITION_SELECTION_MISMATCH", "Foreign requirement selection", rejected=True
            )
        lines = []
        for row in sorted(rows, key=lambda r: str(r.requirement_id)):
            nutrition = resolve_nutrition(
                ingredient_id=row.ingredient_id,
                quantity=row.quantity,
                references=sources.nutrition_references,
                as_of=request.as_of,
                reference_id=selected.get(row.requirement_id),
            )
            procurement = resolve_procurement_sources(
                ingredient_id=row.ingredient_id,
                quantity=row.quantity,
                sources=sources.procurements,
                statuses=sources.retailer_statuses,
                region_code=request.region_code,
                currency=request.currency,
                as_of=request.as_of,
            )
            inventory = resolve_inventory_sources(
                sources.inventory,
                ingredient_id=row.ingredient_id,
                quantity=row.quantity,
            )
            if not procurement and not inventory:
                raise ResolutionError(
                    "MATERIAL_SOURCE_UNRESOLVED",
                    "No captured procurement or confirmed physical possibility",
                )
            for path in procurement:
                if path.availability == "UNKNOWN":
                    issues.append(
                        GroundingIssue(
                            code="UNKNOWN_RETAIL_AVAILABILITY",
                            severity="WARNING",
                            scope=row.requirement_id,
                            detail="Conditional evidence is not checkout certainty",
                        )
                    )
            lines.append(
                GroundedIngredientFacts(
                    requirement_id=row.requirement_id,
                    nutrition=nutrition,
                    procurement_paths=procurement,
                    inventory_paths=inventory,
                )
            )
        fields = dict(
            request=request,
            sources=sources,
            ingredient_facts=tuple(lines),
            preparation_outputs=transforms,
            input_nutrition=total_nutrition([line.nutrition for line in lines]),
        )
        temporary = GroundedDishCandidate.model_construct(**fields)
        candidate = GroundedDishCandidate(**fields, fingerprint=temporary.expected_fingerprint())
        return CandidateGroundingResult(
            status="GROUNDED", candidate=candidate, issues=tuple(issues)
        )
    except ResolutionError as exc:
        return CandidateGroundingResult(
            status="REJECTED" if exc.rejected else "INCOMPLETE",
            candidate=None,
            issues=(GroundingIssue(code=exc.code, severity="ERROR", detail=exc.detail),),
        )
    except (ArithmeticError, ValidationError):
        return CandidateGroundingResult(
            status="INCOMPLETE",
            candidate=None,
            issues=(
                GroundingIssue(
                    code="SOURCE_RESOLUTION_UNREPRESENTABLE",
                    severity="ERROR",
                    detail="Source arithmetic cannot be represented exactly without a new policy",
                ),
            ),
        )
