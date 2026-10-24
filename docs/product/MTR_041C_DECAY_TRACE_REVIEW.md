# MTR-041C — proposal-local Recipe-ID decay trace

Architecture: **APPROVED by user**, including the horizon, naming and policy-time clarifications.
Baseline: `378cb36615b7f9445b500ce961627669e99cb858`. Implementation: NOT FROZEN.
Schema stays0012 /58 tables; no persistence/migration. Frozen040A/041A/041B unchanged.

## Approved boundary before implementation

Learning consumes a fully revalidated frozen041B assessment plus explicit versioned decay policy.
One proposal/member/target, RECIPE_ID only. Only witnesses eligible under041B are interpreted.
Bands cover (0,D] for **this subset only**, where D is041B cooldown duration. This does not
require a future full decay horizon to equal cooldown. No defaults, gaps, overlaps, tail or
interpolation. Explicit band ordinals preserve ordered policy semantics.

Lower bounds are non-negative integer microseconds; upper bounds positive. Retention multiplier
is an exact rational0..1, canonicalized by GCD to reduced numerator/denominator, including0/1
and1/1. Retention never increases with age. Zero retention keeps the witness visible.

Witness = source evidence; age = derived primitive; multiplier = policy interpretation;
trace = derived diagnostic. No aggregate sum/mean/max, RepeatPenalty, confidence, EvidenceStrength,
probability, preference, novelty, ranking or Stage-2 utility is introduced.

Interpretation is explicitly **AS_OF_CAPTURE**: policy.observed_at <=source snapshot.captured_at.
Retrospective interpretation under a later policy is deferred to a separate explicit semantic;
it is not forbidden for all future designs. Frozen041B's own fields/hashes are not rewritten.

Pure versioned frozen/extra-forbid contracts, deterministic canonical identity containing source,
policy/provenance/bands, full recomputation on result validation, no IO or writes. Output remains
activation_ready=False and confirmed/accepted/global history, consumption, novelty, TasteFit and
RepeatPenalty remain UNAVAILABLE. Full041/024/020B/021 remain blocked; Execution unstarted and
PRECOMMIT fail-closed. [Evidence](MTR_041C_DECAY_TRACE_EVIDENCE.md).

## Implemented model and API

Six new contracts: RetentionMultiplier, RecipeDecayBand, RecipeDecayPolicy, RecipeDecayInput,
RecipeDecayTraceEntry and RecipeDecayTraceDraft. Policy has explicit AS_OF_CAPTURE, RECIPE_ID,
PROPOSAL_PREVIEW and LOWER_EXCLUSIVE_UPPER_INCLUSIVE literals; required bands and provenance.
Bands require ordinals0..N-1 in authored order. Rational input normalizes exactly (2/4→1/2,
0/N→0/1,N/N→1/1); comparisons use integer cross-products. No numeric parameter is seeded.

RecipeDecayInput has before validators that reparse supplied model instances, including a
malformed model_construct/copy, before frozen041B validators run. It fully revalidates the
assessment/source primitives and policy, then checks final upper age equals this input's D and
policy.observed_at <=captured_at. Invalid input rejects, never substitutes a default multiplier.

`learning.public.trace_recipe_decay(subject)` returns one entry per eligible frozen witness,
with its original witness and the selected complete band (ordinal/bounds/retention). The result
recomputes all entries and rejects missing/extra/duplicated/reordered/tampered traces. Zero
multiplier retains the entry. Empty input yields empty scoped entries with no global conclusion.
No total, mean, max, score, rank, probability, EvidenceStrength or portfolio field is exposed.

Canonical input embeds frozen041B canonical bytes plus the complete normalized policy; result
embeds that input and recomputed entries. Unordered entries sort by stable event key. Ordered
policy bands are never generically sorted. Same immutable normalized input has identical hashes;
new captured_at or changed policy/provenance may legitimately change identity. A hash confers no
authority or continuous liveness. Latest source is current at capture; old snapshots can replay.

Interpretation uses as-of capture exclusively. A later policy cannot enter this mode; future
retrospective analysis is a different contract. Also, aligning this subset with041B's eligible
window does not constrain future full decay beyond that window. No frozen source fields change.

The existing Planning public capture facade is reused without a new query/write path. Learning
core stays contracts-only and pure. Domain bundle18 retains186 prior definitions and adds6.
INV-009/012/013/018/021–030 remain protected within this subset; no claim of complete cross-horizon
or independent validation enforcement. AP→EP Retail yield and Recipe cooking yield are untouched.
