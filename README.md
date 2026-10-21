# Menuto V1.2 Architecture Release

This bundle is the canonical architecture baseline after the design debates completed on 2026-10-21.

## Contents

- `docs/MENUTO_DEVELOPMENT_SPEC_V1_2.md` — canonical product/architecture spec.
- `docs/ARCHITECTURE_INVARIANTS.md` — non-negotiable cross-domain guardrails.
- `docs/adr/ADR-001..ADR-008` — accepted architecture decisions.

## Change rule

Implementation may refine details that are not locked. A change that contradicts an accepted ADR or invariant requires a superseding ADR; do not silently diverge in code.

## Intentionally open after V1.2

1. Execution State Machine.
2. Independent Validator V2 scope/independence.
3. Behavioral Learning / cold-start / anti-filter-bubble.
4. Numeric benchmark and nutrition policy constants.
5. Retail acquisition/terms and future receipt-calibrated probability model.
