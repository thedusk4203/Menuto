# Independent validation foundation

ADR-010 / INV-015..021. MTR-025 subject foundation and source-supported MTR-026 subset.

`public.validate_subject` is pure and consumes immutable v1-foundation source snapshots.
It independently checks canonical identity/exclusion, default authored recipe input and
compatible nutrition/yield arithmetic, conservation and physical chronological replay.
It never calls DB/source facades, Inventory replay helpers, Recipe binder or solver.

All reports are non-authorizing: PRECOMMIT REJECTED/BLOCKED_UNSUPPORTED, POSTFACT DIAGNOSTIC.
Missing full policy/grounding/scenario/material/batch/revision/assumption/bridge coverage
is explicit; this is not a complete Independent Validator. No clinical policy synthesis.

Read-only coherent capture lives in execution/validation_capture.py and requires a real
read-only REPEATABLE READ/SERIALIZABLE transaction. After capture, validation has no live
reads or repair effects. Production Plan authorization insertion guard remains unchanged.

See docs/product/VALIDATION_SUBJECT_FOUNDATION_REVIEW.md and
docs/product/VALIDATION_SUBJECT_FOUNDATION_EVIDENCE.md for exact scope.


MTR-019A adds `recipe_grounding.validate_recipe_grounding` over versioned
`CulinaryValidationInput`: exact sealed proposal bindings + authored RecipeVersion primitives.
Independent rule/quantity/scaling/tier/transformation/hash enforcement; no producer resolver,
DB/source queries or repair. Read-only capture is execution/culinary_capture.py. This is not full
Independent Validator completion or production authorization. Frozen v1 input remains unchanged.
