# MTR-041D — proposal-local Recipe-ID RepeatPenalty interpretation

Architecture approved by the user after PR #80. Implementation baseline:
`59cc0a48b52addc5c7d612fae6b81b0681e90a00`. NOT FROZEN.
Schema remains0012 /58 domain tables; no persistence or migration is required.

## Ownership and input/output

Learning owns a pure interpretation of a fully revalidated frozen041C trace.
The trace contains one selected proposal/member/target, RECIPE_ID only, with
PROPOSAL_PREVIEW evidence and AS_OF_CAPTURE policy semantics. Reparse the complete
source→041B→041C chain, including untrusted constructed/copied model instances.
No caller-authored witness list or cached contribution may mint evidence.

Five new contracts: RepeatPenaltyAmount, RecipeRepeatPenaltyPolicy,
RecipeRepeatPenaltyInput, RecipeRepeatPenaltyContribution and
RecipeRepeatPenaltyDraft. All frozen, extra-forbid, with independently versioned
wire aggregates. The only operator is SUM_RETAINED_OCCURRENCES. Policy requires
an explicit positive unit_penalty, policy ID/version/provenance and named
POLICY_REPEAT_PENALTY_UNITS. There is no production numeric default.

## Exact calculation and identity

Each contribution = unit_penalty × frozen entry retention; nonempty total = exact
sum. Amount is a nonnegative reduced integer rational with positive denominator,
unbounded above. It is separate from bounded RetentionMultiplier, Money and
material Quantity. Use integer products/addition/GCD only, no float, Decimal
context rounding, quantization, cap or normalization. Equivalent rational forms
have identical bytes. Policy metadata/unit/operator/source enter identity.

Each contribution retains its entire source trace entry, unit penalty and exact
amount. The result independently rebuilds contributions/outcome/total, rejecting
tampering. Witness sets use frozen canonical event keys; policy bands preserve
explicit authored ordinal order. Canonical input serialization nests the frozen
trace's canonical serialization; do not rewrite frozen hashes or definitions.

## Absence, time and counterexamples

Empty trace → NO_MATCH_IN_SELECTED_PROPOSAL and None, never numeric zero.
Present witnesses with zero retention → INTERPRETED_IN_SELECTED_PROPOSAL and
exact0, retaining each zero contribution. Two half-retained occurrences at a
unit penalty3 produce3, a valid amount greater than1, not a probability.
Policy observed_at must be <= captured_at: this slice is AS_OF_CAPTURE only.
Later retrospective interpretation is deferred, not universally forbidden.
Old coherent snapshots remain replayable after proposal replacement; fresh
capture requires its own current proposal query. Replay confers no authority.

## Boundaries and invariant mapping

INV-009: no probability claim. INV-012/013: proposed schedule is never consumption
or confirmed reality. INV-018: exact typed interpretation and complete provenance.
INV-021: activation_ready=False, PRECOMMIT fail-closed. INV-022–029: no durable
learning, taste attribution, member fan-out, inferred dislike, policy mutation or
cross-dimension utility composition. Full INV-030 bridge remains deferred.
Frozen040A/041A/B/C remain unchanged. Retail edible and recipe cooking yields,
physical ledger and reservations remain untouched.

No global RepeatPenalty, novelty, TasteFit, accepted/confirmed/consumption history,
member/shared aggregation, ranking, portfolio role, Stage-2 weight, optimizer,
Execution, DB IO, learning mutation or production default parameters. Full041,
024/020B/021 remain incomplete/blocked. No next milestone starts in this slice.

## Verification plan

Adversarial tests cover exact large rational arithmetic, canonical equivalents,
empty-vs-zero, forged nested inputs/results, unsupported fields/units/operators,
policy time/provenance, deterministic hashes, frozen compatibility, pure boundaries,
real-PG read-only capture/immutability/concurrent source replacement. Full Python,
real PostgreSQL/migration/drift, architecture/export, benchmark, client and web
gates plus PR and post-merge CI are recorded in the implementation evidence.
