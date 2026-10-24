# MTR-041B — proposal-local Recipe-ID cooldown assessment

Architecture: **APPROVED by user** after [dependency review](POST_MTR_041A_DEPENDENCY_REVIEW.md).
Implementation baseline: `391a53e80e841252cc9fd7389e7d566a5d77907b`.
Implementation status: **FROZEN / APPROVED by user**.
Canonical freeze commit: **`43192c7303e42c7bac321728edecaa8421a58e9a`**
([PR #77](https://github.com/thedusk4203/Menuto/pull/77)).
Schema **0012 /58 domain tables**, no persistence or migration. [Evidence](MTR_041B_RECIPE_COOLDOWN_EVIDENCE.md).

## Scope and ownership

Learning owns pure assessment of one member's proposed repetition within **one current selected
proposal**. Planning's existing041A read-only RR/SERIALIZABLE capture owns authoritative ingress.
Recipe identity comes from captured exact RecipeVersion→Recipe facts. No new source truth,
Execution workflow, preference mutation, physical movement, scoring, candidate generation or IO.

The question is: before this target meal, has the same member been proposed this Recipe ID in
another meal within an explicitly configured interval? A positive witness proves only proposed
repetition. A negative answer is local to the selected proposal, not global cooldown safety,
novelty, consumption history or never-exposed evidence. Frozen041A remains unchanged.

## Exact implemented contracts

All inherit frozen/extra-forbid Contract. Domain bundle17 adds five definitions;181 old
definitions remain structurally identical. Major contracts have explicit schema versions.

- **RecipeCooldownPolicy**: policy_id/version, Provenance, required positive strict integer
  duration_microseconds; RECIPE_ID only; interval START_INCLUSIVE_TARGET_EXCLUSIVE. No default.
- **RecipeCooldownQuery**: household/member/plan/proposal/meal/recipe identities. Caller supplies
  identities, not a target timestamp or cached exposure assertion. They must resolve together.
- **RecipeCooldownInput**: captured041A snapshot +query +policy. Exactly one nonempty current
  selected source; exact owner/proposal/member context; policy observed no later than capture.
- **RecipeCooldownWitness**: original provisional preview fact +positive exact distance in
  integer microseconds. Support retains allocation/batch/RecipeVersion provenance.
- **RecipeCooldownAssessmentDraft**: full immutable input, resolved target, lookback_start,
  witnesses and scoped MATCH_IN_SELECTED_PROPOSAL /NO_MATCH_IN_SELECTED_PROPOSAL outcome.
  activation_ready=False; accepted schedule, confirmed exposure, consumption history, decay,
  novelty, TasteFit and RepeatPenalty are all explicitly UNAVAILABLE.

Policy definitions are explicit immutable inputs, never fitted constants. Learning applies the
predicate. This small policy is in Learning contracts alongside frozen041A's preview policy;
it introduces no second utility/policy engine or runtime dependency. Future shared Policy
definitions can be reviewed separately without changing these versioned wire contracts.

## Resolution and failure semantics

`learning.public.assess_recipe_cooldown(input)` revalidates primitives, then resolves the target
from the captured graph. Target must be PLANNED, the member must explicitly participate, and
Recipe ID must have positive PLANNED allocation(s) from PLANNED batches. The whole target meal
is excluded even when multiple batches/versions supply the recipe. Existing graph/seal contracts
continue to protect quantities, ownership and plan structure; no new culinary validity is claimed.

For target time T and explicit duration D, select other member/Recipe-ID preview facts satisfying
**T-D <= scheduled_at < T**. Equal timestamps are never earlier; no UUID ordering. Require the
captured window to contain the full lookback. A window ending exactly at T is valid: target
resolution uses the graph, so the target need not occur inside the half-open preview window.
Multiple allocations/versions for a prior recipe meal produce one witness with full support.

Missing policy/duration, invalid duration, unrepresentable time, insufficient capture window,
unknown/nonparticipating/retired target, absent positive allocation, unsupported fingerprint,
cross-owner/plan/proposal input, zero/empty/multiple sources or future-dated policy fail with
validation error. They never become NO_MATCH or neutral utility. The approved review permitted
explicit unavailable outcomes or rejection; this implementation chooses rejection for invalid
inputs, keeping the successful result closed to two scoped outcomes.

Integer timedelta arithmetic preserves microseconds; no float total_seconds, rounding or money/
quantity conversion. Duration has no universal numeric default. Synthetic test values are not
production recommendations or calibration.

## Determinism, capture and compatibility

Input canonical serialization embeds frozen snapshot.canonical_json(), query identities and
full policy/provenance. Policy, input and result fingerprints are SHA256 over canonical bytes.
Result validation recomputes target/start/witnesses/outcome from the input instead of trusting
cached summaries. Unordered witnesses sort by stable event key; this is not event chronology.
Future ordered event/assumption histories still require explicit sequence/ordinal semantics.

Same immutable input produces identical bytes/hash. A new capture may have a different captured_at
and therefore a different identity even when frontier/witnesses are unchanged. This is expected
provenance, not nondeterminism. A changed policy or material identity changes result identity.

Capture uses the existing public Planning facade without new SQL paths. Latest-source selection
is current **at capture**; pure replay deliberately does not check liveness against a database.
Concurrent replacement remains coherent under RR. A fresh capture has a new proposal identity;
an old query must reject until rebound explicitly. Old immutable snapshots remain reproducible.
No currentness/PRECOMMIT authority is conferred by a hash. No old/new or cross-plan source union.

Old041A classes/functions retain identical ASTs, schema definitions and canonical algorithms.
Only additive classes/helper functions and a new public assessment function are introduced.
Migration0001–0012 and frozen040A source/write/authorship semantics are unchanged.

## Invariants and deferred work

INV-012/013: elapsed time cannot confirm eating; output stays provisional. INV-022..029:
no durable learning, friction→taste, execution→taste, member fan-out, scalar collapse, silent
policy rewrite or forced-choice taste evidence. INV-018 retains primitive provenance;INV-030
allows scoped scheduled repetition without claiming complete cross-horizon replay. INV-005/006
remain untouched: assessment creates no culinary possibilities. Reservations are not movements;
Retail AP→EP and Recipe cooking yields retain their owners.

Full041 remains BLOCKED: accepted publication requires026 authority/TOCTOU; confirmed attributed
events need later Execution/039; operational/cross-horizon reconciliation needs017/038 (036 for
assumptions); METHOD/PROTEIN/FLAVOR/family need046 mappings. Full040 profile derivation remains
incomplete. No decay, novelty, RepeatPenalty, Stage-2 utility, MTR-024/020B/021, production
authorization or Execution implementation. User freeze closes only this subset. No following
implementation is authorized by the freeze. See the [post041B dependency review](POST_MTR_041B_DEPENDENCY_REVIEW.md).
