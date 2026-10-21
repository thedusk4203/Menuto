# ADR-005 — Authored Recipe Flexibility and Pre-Solve Grounding

**Status:** ACCEPTED  
**Date:** 2026-10-21

## Context
Pure static recipes waste inventory and package-fit opportunities; fully parameterized solver recipes can create culinarily invalid “Frankenstein” dishes and explode the decision space.

## Decision
Recipe identity and procedure are stable. Flexibility is authored through contextual `RecipeVariantRule`, quantity/scaling policies and compatibility rules.

Global planning pipeline:

`RecipeVersion → demand-driven VariantGenerator → culinary validation → nutrition/retail resolution → immutable DishCandidate → Pareto shortlist → CP-SAT`.

V1 runtime variants activate at most one structural substitution unless a specific combination is explicitly approved. Cooking method changes create a different recipe, not a runtime variant.

Package-fit uses three levels:

1. grounded substitution/portion tiers before global solve;
2. immutable quantities during global solve;
3. bounded local `CulinaryAdjustmentPass` after selection, followed by independent revalidation.

## Consequences
- Global solver never invents substitutions or cooking methods.
- Candidate fingerprint/reason/provenance are explainable and cacheable.
- Recipe versions are snapshotted for reproducibility.

## Invariants
INV-005, INV-006.
