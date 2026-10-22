# Menuto Architecture Invariants — Canonical V1.3 Baseline

> **System rule:** Every domain service, solver model, validator, state transition and API endpoint must uphold these 30 invariants. No code change may violate an invariant without an approved superseding ADR.
>
> **Renumbering note:** invariant numbers from V1.2/debate transcripts are superseded by this V1.3 list.

## I. Policy, physiology & intent

- **INV-001 — Planning preference must never masquerade as physiology.** Convenience/thrift preferences cannot lower physiological/guideline safety floors or erase goal direction.
- **INV-002 — Observed constraint must never masquerade as user preference.** `BudgetPressure`, `CostPreference` and explicit `BudgetConstraint` are independent signals.

## II. Household & participant safety

- **INV-003 — Shared resource != shared physiology.** Shared physical/financial assets belong to Household; biological profiles, allergies and preferences belong to HouseholdMember.
- **INV-004 — Aggregate demand must never erase individual safety constraints.** Every participating member's hard constraints survive attendance aggregation.

## III. Culinary & recipe grounding

- **INV-005 — Recipe flexibility must be authored, not inferred.** Substitution, portion and quantity flexibility comes from curated `RecipeVersion` rules.
- **INV-006 — Global optimization may choose among culinary possibilities; it may not create culinary possibilities.** Global solve selects grounded immutable candidates; micro-adjustment preserves recipe identity and serving-count semantics unless an explicit portion-tier revision says otherwise.

## IV. Retail, pricing & spend limits

- **INV-007 — Retail observations are evidence, not guarantees.** Retail offers/availability are time-bound evidence, not future checkout promises.
- **INV-008 — The planner optimizes procurement resilience, not merely observed price.** Fragility must be considered alongside spend/waste/carryover.
- **INV-009 — A risk score is not a probability unless it has been calibrated as one.** Heuristics/stress scores must not be presented as P90/probability without empirical calibration.
- **INV-010 — A hard user constraint may produce a relaxed alternative, but that alternative must never inherit the hard-feasible label without explicit user acceptance.**

## V. Execution state machine & inventory truth

- **INV-011 — Planned acquisition is not owned inventory.** Unconfirmed shopping cannot become physical stock.
- **INV-012 — Elapsed time is not evidence of consumption.** Time may create reversible operational assumptions, never confirmed consumption.
- **INV-013 — Inference may update a projection; only evidence may update confirmed reality.**
- **INV-014 — Execution drift should be repaired locally before globally.** Local adjustment/substitution/reschedule precede remaining-week global replan.

## VI. Independent validation

- **INV-015 — Validation verifies correctness, not optimality.**
- **INV-016 — Policy definitions may be shared; correctness enforcement must be independently evaluated.**
- **INV-017 — Critical validation derives from resolved primitive facts, not planner-computed summaries.**
- **INV-018 — Primitive facts must carry explicit measurement basis and provenance before independent recomputation.**
- **INV-019 — Material feasibility must hold globally and at every causal point in time.** Conservation and chronological replay both pass.
- **INV-020 — Root contract validation must not trust planner-resolved safety summaries.** Canonical member safety/root goal contracts are checked directly.
- **INV-021 — Validation of intent is gating; validation of reality is diagnostic.** Validation observes; repair acts.

## VII. Behavioral learning & preference integrity

- **INV-022 — Passive execution assumptions must not create durable behavioral learning.**
- **INV-023 — Operational or retail friction must never penalize culinary taste affinity.**
- **INV-024 — Execution success must not masquerade as taste preference.**
- **INV-025 — Unattributed rejection is weak evidence, not confirmed dislike.**
- **INV-026 — Shared meals may aggregate preferences; they must not erase member-level preference ownership.**
- **INV-027 — Behavioral dimensions remain separable until planner utility composition.**
- **INV-028 — Learned observations may influence soft ranking, but may not silently rewrite explicit user policy.**
- **INV-029 — Forced trade-offs are evidence of constraint resolution, not voluntary preference.**
- **INV-030 — Future commitments must be honored when projecting inventory and exposure across planning horizons.**

## Enforcement expectations

- Unit tests and property tests should reference invariant IDs when practical.
- PRs that alter behavior governed by an invariant should reference the corresponding ADR.
- A deliberate invariant break requires a superseding ADR and migration/compatibility plan.
- AI/LLM layers never override these invariants; they may only parse intent or explain verified deterministic facts.
