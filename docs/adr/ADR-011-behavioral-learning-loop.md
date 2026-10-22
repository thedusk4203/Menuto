# ADR-011: Attribution-Routed Behavioral Learning, Recent Exposure & Bounded Exploration

- **Status:** Accepted — 2026-10-22
- **Supersedes:** V1.2 scalar adherence/preference open decision

## Context

Naive `recipe_score += event` conflates taste with time/retail friction, confuses recent repetition with permanent dislike and lets passive execution assumptions self-reinforce early catalog accidents. Household shared meals also require preference aggregation without losing member ownership.

## Decision

### 1. Evidence classification + attribution routing

Events are classified `DIRECT | CONTEXTUAL | INFERRED | PASSIVE` and routed to `TasteAffinity`, `KitchenContextFit`, `RecentExposureModel`, `RetailCalibration` or `NoLearn`.

- `AUTOPILOT_ASSUMED`: no durable taste/exposure learning; only reversible provisional exposure.
- `USER_CONFIRMED_COOKED`: execution/context fit + confirmed exposure; TasteAffinity unchanged.
- `NO_TIME`, `OUT_OF_STOCK`, `TOO_EXPENSIVE`, `NO_EQUIPMENT`: never penalize taste.
- Unattributed swap/skip: weak evidence only.
- `FORCED_CONFLICT_RESOLUTION`: quarantined from voluntary preference learning.

### 2. Member-owned hierarchical preference

`MemberBehaviorProfile` belongs to `HouseholdMember` and keeps ingredient/protein/method/flavor/direct-recipe affinity plus `EvidenceStrength`. Planner uses shrunk affinity toward onboarding/catalog priors when evidence is weak.

Shared meal utility aggregates participant-owned preferences only after hard safety resolution. Direct avoid/dislike can create strong soft veto-like penalty; low affinity is ordinary weighted utility, not veto.

### 3. RecentExposureModel

Cross-week exposure uses multiple fingerprints (`recipe_id`, `variant_family_id`, main protein, method, flavor) with stronger same-recipe/family penalties and lighter feature penalties. Decay/cooldown defaults are versioned/configurable rather than universal constants. Scheduled meals bridging a horizon contribute provisional exposure; passive assumptions never become durable history without confirmation/reconcile.

### 4. Separable behavior vector

Taste, time fit, equipment fit, complexity, repeat penalty and novelty remain separate until Stage 2 utility composition. No persisted scalar `AdherenceScore`/`RecipeScore` becomes canonical truth.

### 5. Bounded exploration

Role-aware shortlist reserves configurable capacity across `EXPLOIT`, `STRUCTURAL_CHAMPION` and `EXPLORE`. V1 uses deterministic novelty/feature-fit/exposure rules; it does not claim UCB/statistical confidence unless such model is actually implemented and calibrated.

### 6. Explainable/resettable learned observations

Learned patterns may softly affect ranking but do not rewrite explicit user policy. User can confirm/promote, invalidate or reset observations; explicit correction should prevent immediate re-inference without new evidence.

## Alternatives considered

- Scalar recipe/adherence score — rejected.
- Cooked = liked — rejected.
- Passive autopilot = confirmed satiation/taste — rejected.
- Fixed exploitation/exploration percentages as architecture constants — rejected.
- Black-box online ML in V1 — rejected.

## Consequences

Cold-start is handled by explicit/onboarding priors; long-term personalization remains causal and explainable; filter-bubble risk is bounded without treating assumptions as preference facts.

## Invariants

`INV-022` through `INV-029`, plus `INV-030` for cross-horizon scheduled exposure.

## V1 boundary

Deterministic rules, evidence classes, hierarchical shrinkage, recent-exposure history and versioned shortlist portfolio. No online neural recommender required.
