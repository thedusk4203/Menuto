# ADR-010: Independent Semantic Validator, Primitive Recomputation & Chronological Replay

- **Status:** Accepted — 2026-10-22
- **Supersedes:** V1.2 generic independent-checker/open Validator V2 decision

## Context

An optimizer cannot be the sole judge of its own model correctness. A second CP-SAT formulation risks duplicating declarative bugs; trusting candidate/policy summaries misses unit-scaling, AP→EP, policy-synthesis and temporal-causality failures.

## Decision

Implement a deterministic, side-effect-free `ValidationOrchestrator` over immutable `ValidationSubjectSnapshot`.

### 1. Semantic independence

`RootContractValidator` and `HouseholdSafetyValidator` check canonical member constraints/root contracts directly. They do not trust planner-resolved allergen summaries and do not reimplement the full policy synthesis formula; guards focus on identity, safety, direction and containment.

### 2. Arithmetic independence

Correctness-critical values are recomputed from resolved primitive facts with explicit measurement basis/provenance:

- ingredient allocation × compatible nutrition reference;
- AP→EP edible yield and cooking/prepared transformation separately;
- package/procurement quantities × deterministic scenario quotes;
- authored recipe envelopes;
- participant × grounded ingredient safety.

Planner summaries may be compared after recomputation but cannot serve as validation truth.

### 3. Algorithmic independence

Use both global conservation and imperative chronological event replay. Canonical order at equal effective time: acquisition → transfer/reconcile → raw consumption → prepared production → meal consumption → expiry/discard. Replay raw and prepared asset ledgers and verify stock/non-expiry at every causal point.

### 4. Validation modes

- `PRECOMMIT_VALIDATION`: gates activation, local refinement and revisions; `0 FATAL`, `0 ERROR`; subject hash/revision must still match at commit.
- `POSTFACT_VALIDATION`: diagnoses real-world execution; reality is recorded rather than rejected.

Validation has no repair side effects. Repair/advisor services consume structured findings.

### 5. Core validator suite

`RootContractValidator`, `HouseholdSafetyValidator`, `RecipeGroundingValidator`, `NutritionPrimitiveValidator`, `ProcurementScenarioValidator`, `MaterialYieldValidator`, `ChronologicalInventoryValidator`, `BatchFlowValidator`, `RevisionBoundaryValidator`, `AssumptionGraphValidator`.

### 6. Testing discipline

Mutation corpus must prove known-invalid plans are caught: forbidden ingredient, unit/basis mismatch, yield omission, consume-before-buy, expiry violation, spend scenario breach, broken assumption parent, illegal revision of materialized past.

## Alternatives considered

- Trusting `DishCandidate` cached totals — rejected.
- Shared planner constraint-builder as validator — rejected.
- Second optimizer as validator — rejected.
- End-of-horizon balance only — rejected.

## Consequences

Validator is inexpensive relative to search but introduces an explicit second evaluation path for correctness-critical arithmetic and temporal semantics. Module dependency CI must prevent imports from planner/solver internals into validation.

## Invariants

`INV-015` through `INV-021`.

## V1 boundary

Ten core validators, structured findings/proof traces, precommit gating and postfact diagnostics. No formal theorem prover required.
