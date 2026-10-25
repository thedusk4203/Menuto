# MTR-041F — Proposal-local Reviewed Feature Repeat Policy Foundation

Status: **DESIGN ONLY — architecture review pending; implementation NOT AUTHORIZED; NOT FROZEN**.
The user authorized a docs-only architecture/design PR, then a stop for review before any code.
Canonical design base: `ce03e1b925c80771d20863277963fac8db711c66` (main, freeze PR #91).
[Exact base CI40218477245](https://github.com/thedusk4203/Menuto/actions/runs/40218477245)
SUCCESS, python/web, independently rechecked. Schema **0013 /71 domain tables**,256 exported
contract definitions. This PR changes documentation only: no runtime, contracts, tests, exports,
schema or migration; no new HTTP endpoint, persistence, cache or durable frontier is proposed.

```text
frozen041E reviewed proposal-local feature exposure + full captured source/coverage
  -> exact dimension/term cooldown witnesses + unresolved-occurrence diagnostics
  -> exact decay trace over those witnesses
  -> proposal-local feature RepeatPenalty, only where occurrence enumeration is decidable
```

Supported dimensions are exactly **METHOD / MAIN_PROTEIN / FLAVOR**. One atomic interpretation
belongs to one HouseholdMember and one target meal in one selected proposal, for one exact
(dimension, term ID). No cross-term, cross-dimension, member/shared or recipe-plus-feature total
is defined. All model/API names below are **proposals**, not existing exports or tested features.

## 1. Decision, dependencies and frozen basis

040A,040B,041A/B/C/D/E and046A are user FROZEN.041F is the next **design-only** branch.
MTR-040C design is **NOT READY / NOT AUTHORIZED**: canonical onboarding/catalog preference priors
and broader observation sources do not exist;040B keeps prior/shrinkage UNAVAILABLE.041F needs
neither a fabricated prior nor039 attribution/Execution. It interprets041E's already typed
PROPOSAL_PREVIEW source only. It does not change or complete MemberBehaviorProfile.

References: [ADR-011](../adr/ADR-011-behavioral-learning-loop.md),
[invariants](../ARCHITECTURE_INVARIANTS.md),
[041E source design](POST_MTR_046A_DEPENDENCY_REVIEW.md),
[041E frozen evidence](MTR_041E_FEATURE_EXPOSURE_EVIDENCE.md),
[041B](MTR_041B_RECIPE_COOLDOWN_REVIEW.md), [041C](MTR_041C_DECAY_TRACE_REVIEW.md),
[041D](MTR_041D_REPEAT_PENALTY_REVIEW.md),
[post041E dependency matrix](POST_MTR_041E_DEPENDENCY_REVIEW.md),
[040B freeze receipt](MTR_040B_EXPLICIT_TARGET_AFFINITY_EVIDENCE.md).
The older dependency matrix identified feature policies as separately designable once041E existed;
the user's current decision selects that branch after040B freeze. It does not authorize code.

Direct inspection at the base confirms:

| Existing source | Reused fact / constraint |
| --- | --- |
| `learning.contracts.FeatureExposureSourceSnapshotDraft` | Full immutable041A member snapshots +046A classification subjects, exact selected proposal, source-owned frontiers and all eligible batch/dimension sources |
| `FeatureExposurePreviewDraft`, `preview_feature_exposure()` | Recomputed positive member/meal/dimension/term events, allocation-level support, coverage diagnostics and dimension evidence-cut digests; no feature policy interpretation |
| `FeatureExposureCoverageDiagnostic` | Per member/meal/batch/dimension discovery, exact covered/positive finite term IDs, review/applicability and allocation support; no global classification completeness |
| `recipes.contracts.resolve_feature_input()` | Existing pure term-specific PRESENT / REVIEWED_ABSENT / UNRESOLVED semantics over a captured046A evaluation, including TERM_NOT_CAPTURED and OUTSIDE_REVIEWED_UNIVERSE |
| `planning.public.capture_feature_exposure_preview()` | Existing authenticated clean read-only RR/SERIALIZABLE coordinated capture; returns the041E source snapshot, not a policy result; no commit/new connection |
| Frozen041B/C/D | RECIPE_ID-specific query/witness, exact age-band and retained-occurrence patterns; no feature query/coverage/time/weight policy exists |
| ORM, migrations and exports |0013 /71 and256 definitions; no feature-policy result store or new canonical history source |

Graphify's existing index was orientation only; current contracts/adapters above determine the
design. No frozen contradiction requiring a correction or genericization was found.

## 2. Ownership, ingress and trust

Learning owns the new pure proposal-local interpretation. Recipes/Catalog retain classification,
term identity, covered universes, reviewed support and frontier ownership. Planning retains
proposal selection and canonical capture. No second source matcher, preference store or generic
behavior engine is added. Shared Policy-module extraction is outside this slice.

Proposed new immutable contracts/helpers are additive to `learning/contracts.py`; pure enforcement
may live in `learning/feature_repeat.py`, exposed by additive Learning public functions:

- `assess_feature_cooldown(FeatureCooldownInput)`;
- `trace_feature_decay(FeatureDecayInput)`;
- `interpret_feature_repeat_penalty(FeatureRepeatPenaltyInput)`.

The pure call path imports only immutable Learning/Recipes contracts and neutral canonical/numeric
primitives. It has zero DB/network/file IO, zero writes and no runtime dependency on Preferences,
Planning facades, Execution, attribution, ranking or optimizer. It may call the existing pure
Recipes **contract** term resolver; it must not copy/reimplement its source matching rules.

Canonical application flow, only after future implementation approval:

1. Authenticated caller supplies the existing041E capture request with exact current proposal ID/
   hash, selected member(s), dimensions and explicit recipe eligibility window/policy.
2. Reuse the existing public Planning capture in one caller-owned clean read-only REPEATABLE READ
   or SERIALIZABLE transaction. Preserve each frozen child clock and the full041E source.
3. Existing pure041E preview recomputes events/diagnostics from that source. New041F input accepts
   the **full frozen preview**, query and explicit policy, never standalone caller event arrays,
   claimed completeness, confidence or cached penalty.
4. New pure APIs recursively reparse all nested source/preview/policy/result models, including
   model_construct/model_copy instances; independently recompute041E and every041F stage.

Capture errors remain whole-capture failures; no silent dimension drop, partial retry or fake
UNRESOLVED source is manufactured. Retry serialization failures as a whole capture transaction.
Offline self-consistency verifies internal replay, not canonical database origin/currentness.
An old coherent source can replay after replacement; a fresh source/query must bind its new exact
proposal and reviewed sources. None of these hashes or drafts authorizes PRECOMMIT.

## 3. Atomic target and occurrence identity

Proposed `FeatureRepeatQuery` / `feature-repeat-query.v1` fields:

```text
household_id, member_id, plan_id, proposal_id, proposal_hash,
meal_node_id, dimension:METHOD|MAIN_PROTEIN|FLAVOR, feature_term_id
```

No caller-supplied timestamp, Recipe-ID fallback, raw PreferenceTarget, term code alias, feature
weight or target assignment is accepted. MAIN_PROTEIN refers to the046A contextual assignment;
its vocabulary kind is PROTEIN under the existing owner resolver. This is not an inferred
ingredient preference, protein-gram calculation or040B preference target conversion.

Resolve exactly one041E event for that owner/target meal/dimension/term and exact proposal hash.
The target must be a PLANNED participating meal with the eligible allocation/source support
already proven by041E and a real positive reviewed target event. Its scheduled_at and exact term
fact/version/provenance come from attached source. Target lacking a positive event fails with a
specific target error: TARGET_NOT_CAPTURED / TARGET_NOT_PRESENT / TARGET_FEATURE_UNRESOLVED as
appropriate to recomputed diagnostics. Missing member/dimension, wrong term kind, random UUID,
REVIEWED_NONE or unresolved target cannot become a successful no-repeat/zero assessment. The
original041E diagnostics remain available; rejection does not rewrite them.

Reuse the unchanged041E event key: household/member/plan/meal/dimension/term. Proposal identity/
hash and full support remain attached. One event may have multiple batches, RecipeVersions,
allocations, review IDs and supports: those are proof, **not independent occurrences**. Repeated
captures do not add occurrences. No union of proposals, plans or captures is accepted.
Same code/new term ID is a separate identity. No term/family/version reconciliation is defined.

## 4. Proposed additive contracts and explicit policies

All proposed models are frozen, extra-forbid, tuple-based, with closed literal/discriminator
unions. Wire aggregates have explicit versions. Static scope tags may default; **numeric policy
values, term/dimension selection and operators must be explicitly supplied**, with no constructor
fallbacks or production seeds. The following table specifies future shape, not code in this PR.

| Proposed contract | Required content / rule |
| --- | --- |
| `FeatureRetentionMultiplier` | strict integer numerator>=0, denominator>0, numerator<=denominator; GCD reduced;0/x->0/1, x/x->1/1; dimensionless policy retention, not probability |
| `FeatureRepeatPenaltyAmount` | strict integer numerator>=0, denominator>0, canonical GCD reduction, unbounded above; unit=POLICY_FEATURE_REPEAT_PENALTY_UNITS; separate from money/quantity/affinity |
| `FeatureCooldownPolicy` / `feature-cooldown-policy.v1` | policy_id/version, authored/reviewed Provenance, exact dimension and term_id, required positive integer duration_microseconds; fingerprint_kind=REVIEWED_FEATURE_TERM_ID, source_kind=PROPOSAL_PREVIEW, interpretation_mode=AS_OF_CAPTURE, interval=START_INCLUSIVE_TARGET_EXCLUSIVE |
| `FeatureDecayBand` | explicit contiguous ordinal, lower_age_microseconds>=0, upper_age_microseconds>lower; complete FeatureRetentionMultiplier |
| `FeatureDecayPolicy` / `feature-decay-policy.v1` | policy_id/version/provenance, exact dimension/term_id, AS_OF_CAPTURE/PROPOSAL_PREVIEW, LOWER_EXCLUSIVE_UPPER_INCLUSIVE, required nonempty authored-order bands |
| `FeatureRepeatPenaltyPolicy` / `feature-repeat-penalty-policy.v1` | policy_id/version/provenance, exact dimension/term_id; required operator=SUM_RETAINED_TERM_OCCURRENCES; required positive FeatureRepeatPenaltyAmount unit_penalty; AS_OF_CAPTURE/PROPOSAL_PREVIEW |
| `FeatureCooldownInput` / `feature-cooldown-input.v1` | full frozen FeatureExposurePreviewDraft, FeatureRepeatQuery, FeatureCooldownPolicy; reparse/recompute full041E source/result, validate exact owner/proposal/target/policy/time/window |
| `FeatureTermCoverageCell` | full frozen coverage diagnostic + recomputed FeatureTermResolution for the query term; immutable source key and exact resolution retained; no caller-authored coverage flag |
| `FeatureMealTermOccurrence` | meal_node_id, resolved scheduled_at, exact query dimension/term, all applicable cells, state=PRESENT/REVIEWED_ABSENT/UNRESOLVED, exact041E event or None; prove the term-specific existential/count decision in section6 |
| `FeatureCooldownWitness` | full041E positive event and exact positive distance_microseconds; one per eligible prior event key |
| `FeatureCooldownAssessmentDraft` / `feature-cooldown-assessment.v1-draft` | full input, target event, derived lookback_start/policy_cutoff, ordered-by-key witness tuple, per-meal term occurrences, unresolved_meal_ids, outcome and occurrence-resolution enum (section7); dimension evidence-cut identity and fixed non-authority boundary |
| `FeatureDecayInput` / `feature-decay-input.v1` | full revalidated FeatureCooldownAssessmentDraft + exact matching FeatureDecayPolicy; bands exactly cover this assessment's(0,D], no gaps/overlap/increasing retention |
| `FeatureDecayTraceEntry` | full witness, derived age and entire selected band including ordinal/bounds/retention; no dropped zero entries |
| `FeatureDecayTraceDraft` / `feature-decay-trace.v1-draft` | full input, exactly one entry per known eligible witness, unchanged unresolved occurrences and resolution outcome; trace does not certify exhaustive history when unknowns exist |
| `FeatureRepeatPenaltyInput` / `feature-repeat-penalty-input.v1` | full revalidated FeatureDecayTraceDraft + matching FeatureRepeatPenaltyPolicy; no caller contributions, totals or stage-switch flags |
| `FeatureRepeatPenaltyContribution` | full trace entry + explicit unit_penalty + exactly recomputed contribution; dimension/term matches its input |
| `AvailableProposalLocalFeaturePenalty` | status=AVAILABLE; amount:FeatureRepeatPenaltyAmount; legal only for a nonempty trace with no unresolved prior meal occurrence |
| `UnavailableProposalLocalFeaturePenalty` | status=UNAVAILABLE; reason=UNRESOLVED_TERM_OCCURRENCES / NO_MATCH_IN_SELECTED_PROPOSAL; no numeric amount or default baseline |
| `FeatureRepeatPenaltyDraft` / `feature-repeat-penalty.v1-draft` | full input, exact contributions, discriminated proposal_local_feature_repeat_penalty availability, scoped outcome/unknowns, fixed boundaries and independently recomputed fingerprint |

Provenance must be USER or REVIEWED_REFERENCE, with source_system, external identity/version and
observed_at. No curator service or durable policy repository is installed. Every stage's dimension
and term ID must exactly equal the query; policy IDs/versions are explicit and independently
retained in the chain. Missing stages and dimension/term mismatches reject; lists in place of
singular policies or extra policy fields are outside the closed input shape.

The atomic API takes exactly one explicit policy at each stage; no policy matrix is implicitly
created for unrequested terms/dimensions. A later caller evaluating several terms must supply a
complete explicit triple **for each** atomic query; no default/fallback to another term/dimension,
recipe policy, shared unit weight, inherited duration or guessed decay band. No batched aggregator
is specified here. An explicit zero multiplier is legal; a zero **unit penalty** is rejected in
this v1 design. Disabled/omitted dimensions are separate caller requests, not hidden zero weights.

Feature penalties are expected by ADR-011 to be lighter/different from exact recipe/family
repetition. This is a **curated policy decision**, not a universal ratio, constant or inequality
the engine can infer. No recipe reference weight is consumed; no cross-scale comparison,
normalization or automatic METHOD<MAIN_PROTEIN<FLAVOR order is defined. The shared unit label
alone does not authorize addition/comparison across dimension or policy coordinate systems. A reviewed policy may
choose different values; production values and calibration remain unsupplied. Examples and later
synthetic fixtures are not defaults, learned statistics, probabilities or planner coefficients.

Do not modify, subclass to widen, rename or genericize frozen RecipeCooldown*, RecipeDecay*,
RecipeRepeatPenalty*, RetentionMultiplier or RepeatPenaltyAmount. New feature numeric/stage
contracts are additive. Any future shared arithmetic extraction needs a separate compatibility
review; this design reuses the mathematical pattern, not Recipe-ID policy semantics or weights.

## 5. Time, eligibility and exact cooldown interval

Let t be the scheduled_at resolved from the target event, and D the explicitly supplied positive
integer cooldown duration. Derive start=t-D without float conversion. Eligible prior meals have
start <= scheduled_at < t; exclude the target meal and all simultaneous/future meals, independent
of UUID or graph-array order. Age uses integer timedelta days/seconds/microseconds only, so
0<age<=D. Overflow or underflow fails explicitly; no clamp/truncated interval.

For this first subset require the complete[start,t] decision context inside both the captured041E
recipe eligibility window and the selected proposal horizon; t must lie **strictly before** each
end, because041E events are emitted on[start,end). Reject LOOKBACK_NOT_CAPTURED / TARGET_OUTSIDE_CAPTURE
when this cannot be proven. Do not extrapolate absence outside the selected proposal, widen the
source window silently or borrow a preceding horizon. This is an intentional narrow041F choice;
it neither changes041B's target-boundary rules nor defines future global-history policy.

Source eligibility remains exactly041E's PLANNED member participation/batch/allocation rules.
041F does not reinterpret servings, rerun inventory, create additional supports or alter recipe
eligibility policy's frozen RECIPE_ID tag; that tag controls source extraction, not feature weights.

AS_OF_CAPTURE: derive policy_cutoff as the minimum of the queried member's041A captured_at and
all queried-dimension046A evaluation captured_at clocks actually used for target/lookback cells.
Target positive proof ensures this set is nonempty. All three policy provenances must be observed
no later than that cutoff (and therefore no later than041E capture completion). Preserve each
child clock, observed_at and recorded_at; no caller cutoff/now, clock replacement or retrospective
policy replay. Later-policy retrospective interpretation requires a separately reviewed mode.
An old source replay stays deterministic; a fresh source can satisfy a later policy only under
its own captured cutoff. This choice is stricter than using outer completion alone and needs review.

## 6. Coverage: decide exact term occurrences, never global absence

Recompute the full frozen041E preview first. From its exact selected proposal graph, enumerate all
eligible prior participating meals with eligible allocation supports in[start,t). Require the
full matching diagnostic-cell manifest for each meal/batch/queried dimension, including cells
without positive events. A caller cannot omit an unresolved batch/meal to obtain a lower penalty.
The target positive event supplies canonical term identity; classification for another cell uses
that cell's own captured term universe, not a union that fabricates reviewed coverage.

For each cell invoke the existing pure Recipes contract resolver on its attached046A evaluation
and an exact FeatureTermQuery(dimension, term_ids=(query.feature_term_id,)). Keep its actual result:

| Resolution | Count meaning in this one cell |
| --- | --- |
| PRESENT | Exact reviewed query term is present; corresponding041E event/support must agree |
| REVIEWED_ABSENT | This query term is in that reviewed finite universe and COMPLETE coverage excludes it; not global/never-exposed absence |
| UNRESOLVED | Preserve NO_SOURCE / NO_MATCHING_SCOPE / RETRACTED / STALE_ASSOCIATION / PARTIAL_COVERAGE / OUTSIDE_REVIEWED_UNIVERSE / TERM_NOT_CAPTURED; absence cannot be inferred |

REVIEWED_NONE alone is insufficient: a term outside its finite covered universe or not captured
for that evaluation remains UNRESOLVED. ASSIGNED/PARTIAL can prove its actual positive term, but
unlisted terms remain unresolved. Do not invent term facts, expand a reviewed universe, reconcile
new term IDs by code, treat ingredient association as contextual MAIN_PROTEIN, or replace the
owner's stale/retracted/no-scope reasons with zero.

Determine one **term-specific occurrence per meal**, using the fixed041E event cardinality:

1. Any cell PRESENT -> that exact term occurrence is PRESENT; require the exact041E event with all
   positive supports, count it once and retain every cell diagnostic. An unresolved sibling
   batch cannot add a second event with the same key. This proves the existence/count of **this
   term** only; it does not make the meal/dimension globally complete or resolve sibling features.
2. No PRESENT and every required cell REVIEWED_ABSENT -> occurrence REVIEWED_ABSENT, scoped to
   this member/meal/dimension/term and its attached finite reviewed sources.
3. Otherwise -> occurrence UNRESOLVED; keep the meal as an unresolved potential occurrence.

A meal with no eligible supports is excluded by the source rules, not recast as REVIEWED_NONE.
A missing expected cell is corrupted/incomplete input and rejects, not a successful absence.
Known-positive witnesses remain valid when other meals are unresolved. Never infer their number
is the full count; do not mint witnesses or missing contribution placeholders for unresolved meals.
Even an unknown meal's applicable age band having zero retention does **not** turn unknown source
into an observed zero occurrence or permit an aggregate total in this v1 conservative design.

## 7. Cooldown outcome, decay and penalty availability

Cooldown separates positive evidence from enumeration decidability:

| Known witnesses | Unresolved potential-occurrence meals | Cooldown outcome / occurrence resolution |
| --- | --- | --- |
| Nonempty | None | MATCH_IN_SELECTED_PROPOSAL / ALL_QUERIED_TERM_OCCURRENCES_DECIDABLE |
| Nonempty | Present | MATCH_IN_SELECTED_PROPOSAL / HAS_UNRESOLVED_MEALS; positive proof only |
| Empty | Present | UNRESOLVED_IN_SELECTED_PROPOSAL / HAS_UNRESOLVED_MEALS |
| Empty | None, some eligible meals | NO_MATCH_IN_SELECTED_PROPOSAL / ALL_QUERIED_TERM_OCCURRENCES_DECIDABLE |
| Empty | None, no eligible prior meals | NO_MATCH_IN_SELECTED_PROPOSAL / NO_ELIGIBLE_PRIOR_MEALS |

No outcome means safe, novel, never exposed, accepted, eaten or liked. Cooldown is a diagnostic
repeat witness assessment, not a hard ban, planner rule, feasibility gate or preference update.

Decay uses required contiguous bands covering exactly(0,D] **for this subset**: lower-exclusive,
upper-inclusive, ordinals0..N-1 in authored order; no gaps, overlap, tail, interpolation or omitted
band. Retention cannot increase with age, checked by exact integer cross-products. Future wider
decay horizons need their own design; this does not make cooldown=full-decay a universal rule.
Retain every positive witness even at zero retention. Trace partial known evidence when unknown
meals exist, with those unknowns and the original assessment still attached. Do not invent a decay
entry for an unresolved occurrence, a calibrated confidence or a default multiplier.

Let U be this exact dimension/term's explicit positive rational unit penalty; r_i its selected
band retention. Each known contribution c_i=U*r_i. A nonempty fully decidable occurrence set yields
proposal_local_feature_repeat_penalty=sum(c_i), in POLICY_FEATURE_REPEAT_PENALTY_UNITS, with the
query dimension/term attached. No division by portions, meals, participants or target count; no
mean/max, cap, probability mapping, normalization, cross-term sum or Recipe-ID weight reuse.
Use strict integer product/sum/GCD reduction only; no float, Decimal rounding or quantization.

| Source/trace state | Penalty branch |
| --- | --- |
| Any unresolved potential-occurrence meal | UNAVAILABLE / UNRESOLVED_TERM_OCCURRENCES; retain known contributions but expose no subtotal, lower-bound score or total |
| No unresolved meals, no witnesses | UNAVAILABLE / NO_MATCH_IN_SELECTED_PROPOSAL; no numeric zero, following the explicit scoped-empty discipline of041D |
| No unresolved meals, nonempty trace | AVAILABLE exact sum; if all retentions are explicitly zero, AVAILABLE0/1 with the nonempty zero contributions retained |

These rules distinguish unavailable/absence from a real policy-interpreted zero. Empty source or
REVIEWED_NONE does not by itself become zero RepeatPenalty. The only supported aggregation is
known retained occurrences of **one term, one dimension, one member and one target meal** inside
one proposal. It is not recipe/candidate utility composition, a member behavior score or taste fit.

## 8. Canonical identity, tamper rejection and dimension separability

New wire encodings use UTF-8, sorted object keys, compact separators, canonical UUIDs, UTC
microseconds and normalized strict rational integers. Preserve nested frozen041E and all child
canonical encodings verbatim via their canonical serializers. Do not rewrite frozen fields:
041E's feature_cooldown/feature_decay/repeat_penalty remain UNAVAILABLE in the attached source;
only the additive041F outer contract describes this new scoped interpretation.

- Retain full041E preview fingerprint (including full attached source, support, clocks and other
  requested member/dimension branches) as the audit capture identity. It is not a hash of only
  visible matching event rows, a liveness token or origin signature.
- Retain the queried dimension's unchanged041E evidence-cut digest as **diagnostic** identity.
  METHOD/FLAVOR evidence cuts must not gain Catalog association frontier dependencies. MAIN_PROTEIN
  retains its actual Recipes+Catalog frontiers; vocabulary identity remains source-owned.
- Policy fingerprint includes version tags, exact dimension/term, ID/version/provenance, time/
  interval/mode, every explicit numeric field and operator; no map/default row is implicit.
- Each input/result fingerprint hashes its complete canonical payload including prior-stage
  canonical bytes, query, policy, recomputed witness/cell/occurrence/availability/contribution
  fields. If a fingerprint is a stored field, exclude only that result's own fingerprint field.
- Unordered source/support/event/cell/meal/witness/contribution sets sort by their typed stable
  keys (041E event_key for witnesses/contributions; member/meal/batch/dimension/term for cells;
  member/meal/dimension/term for occurrences); duplicates/conflicts reject before sorting. Policy bands and source revision/sequence
  lineage retain authored order; do not generically sort every list.

Result validators independently rebuild the entire source->coverage->cooldown->decay->penalty
chain and compare every cached field/hash. Forged witness/age/coverage/unknown list/total/result,
including internally rehashed cached results and constructed/copied nested models, rejects.
Identical captured primitives/policies or shuffled unordered sets yield identical canonical
bytes. Changed capture clocks can change full audit identity with equal numeric interpretation.
An unrelated Catalog-only edit cannot change METHOD/FLAVOR term outcomes or their041E dimension
cuts; a fresh mixed-dimension capture's full audit hash may change. Do not falsely promise global
fingerprint stability while retaining mixed source truth. Other dimensions' policies/results are
never consulted for an atomic query. No giant scalar behavior score or cross-dimension total.

## 9. Fixed result boundaries and invariants

Every new draft retains these semantics (scope literals may be shared by the new draft models):

```text
coverage              = ONE_SELECTED_PROPOSAL_EXACT_FEATURE_TERM_ONLY
source_kind           = PROPOSAL_PREVIEW
interpretation_mode   = AS_OF_CAPTURE
absence_semantics     = NO_GLOBAL_REPEAT_NOVELTY_OR_NEVER_EXPOSED_CONCLUSION
accepted_schedule     = UNAVAILABLE
confirmed_exposure    = UNAVAILABLE
consumption_history   = UNAVAILABLE
durable_history       = UNAVAILABLE
cross_horizon_history = UNAVAILABLE
global_repeat_penalty = UNAVAILABLE
novelty               = UNAVAILABLE
taste_fit             = UNAVAILABLE
member_behavior_profile = NOT_MODIFIED
cross_dimension_aggregation = NOT_PERFORMED
planner_ready         = False
activation_ready      = False
```

Cooldown/trace stages do not expose a final penalty; the final stage exposes only the explicitly
named proposal-local feature availability union. This does not redefine041D's global-repeat flag.
Prior/shrinkage remain040B UNAVAILABLE;041F does not add profile or learned evidence fields/sources.
Proposal preview !=accepted exposure; proposal preview !=confirmed exposure;
REVIEWED_NONE !=never exposed; UNRESOLVED !=zero repeat. No elapsed time, cook/skip/out-of-stock,
forced trade-off or raw preference assertion is accepted as new exposure/taste evidence here.

INV-012/013 preserve proposed versus confirmed reality;018 preserves exact primitives/provenance;
021 keeps diagnostic evidence separate from authority. INV-022–029 preserve no passive learning,
no friction/cooked-to-taste inference, member ownership, separable behavior dimensions, explicit
policy and no forced-choice preference claims. INV-030 remains incomplete: no cross-horizon bridge
is designed here. No full invariant or production-readiness completion is claimed by these docs.

## 10. Concurrency, persistence and frozen compatibility

No new capture adapter, SQL read/write path, source generation, table, migration or profile/history
persistence is needed. Reuse frozen041E capture plus existing canonical source review services.
0013 /71 remains unchanged;0001–0013 remain immutable. New pure contracts/APIs/exports/tests, if
subsequently approved, must be additive and retain all256 existing definitions byte-for-byte.
041B/C/D remain RECIPE_ID-specific, unchanged, with all existing hashes/semantics/test receipts.
040A/B,041A–E and046A remain frozen; no fields, source encodings or import-boundary widening here.

Future real PostgreSQL tests must establish actual old/fresh RR/SERIALIZABLE behavior during
proposal replacement and reviewed classification/association updates, using owner append/CAS
services and real concurrent transactions. A fresh stale MAIN_PROTEIN support remains unresolved;
old captures replay coherently. METHOD/FLAVOR remain independent of association generation.
No per-target retry or snapshot union hides mixed sources. Future currentness/authorization
rechecks belong to a separately approved production commit flow; PRECOMMIT remains fail-closed.

## 11. Proposed adversarial acceptance plan — not tests implemented by this PR

U=pure contract/derivation; PG=real PostgreSQL; C=frozen compatibility/import/export/schema.
Every dimension must be exercised, with deliberately distinct explicit policy fixtures.

| # | Proposed acceptance case | Required result / layer |
| --- | --- | --- |
| 1 | METHOD / MAIN_PROTEIN / FLAVOR explicit different policies | Exact dimension/term selection; no implicit recipe/shared weights; separate results. U |
| 2 | Missing dimension/term/stage policy or mismatched triple | Reject; no fallback/default map or dimension drop. U |
| 3 | Same term in2 batches/versions/allocations in1 meal | One occurrence/witness with full support; not multiplied by support cardinality. U/PG |
| 4 | Same term in2 earlier meals | Two witnesses; exact sum of retained occurrences. U |
| 5 | Same-timestamp meal, target meal, future meal | Excluded from prior witnesses, no UUID/array-order tie-break. U |
| 6 | Exact start / just-before start / ageD / age0 | Start included, earlier excluded, ageD included, age0 excluded; exact microseconds. U |
| 7 | Lookback outside eligibility window/proposal horizon; target at exclusive end | Reject explicit context error; no truncated success or borrowed horizon. U/PG |
| 8 | Huge duration or datetime under/overflow | Fail cleanly without float, clamp or unbounded range allocation. U |
| 9 | Missing/nonparticipating/foreign member or foreign household/plan/proposal/hash | Reject; memberA cannot produce memberB result. U/PG |
| 10 | Target lacks positive event (reviewed-none/unresolved/random UUID/wrong kind) | Specific target rejection, never valid zero/no-repeat output. U/PG |
| 11 | REVIEWED_NONE with query term inside COMPLETE finite universe | Term-specific absence only; empty penalty UNAVAILABLE, not never-exposed/zero. U |
| 12 | REVIEWED_NONE but query term outside universe/not captured | Preserve UNRESOLVED reason; no false absence. U |
| 13 | ASSIGNED/PARTIAL includes query term | Positive witness valid; unlisted terms remain unresolved. U |
| 14 | One prior meal has no positive and an unresolved cell | Occurrence unresolved; scalar penalty UNAVAILABLE, even with known witnesses elsewhere. U/PG |
| 15 | Same meal has a PRESENT cell plus unresolved sibling batch | One proven term occurrence; retain all diagnostics, no global completeness claim. U |
| 16 | Every cell explicitly REVIEWED_ABSENT for query term | Scoped NO_MATCH, no numeric penalty or global safety conclusion. U |
| 17 | No eligible prior meals / filtered allocations | Scoped empty result, no fabricated REVIEWED_NONE or zero penalty. U/PG |
| 18 | Remove/duplicate expected diagnostic/meal/support cell | Full primitive reconstruction rejects; cannot hide unknowns. U |
| 19 | RETRACTED / NO_SOURCE / NO_MATCHING_SCOPE / STALE_ASSOCIATION | Actual owner reasons preserved; no default event or zero. U/PG |
| 20 | New term ID/version with same code | Separate identity; no reconciliation, transfer or summed alias. U/PG |
| 21 | Exact path/tier/substitution changes | METHOD context invariant; FLAVOR/MAIN_PROTEIN use correct bound path; no source matcher copied. U/PG |
| 22 | Term present in multiple MAIN_PROTEIN slot supports | Exact041E event count only; no ingredient/grams/quantity or association-only inference. U |
| 23 | Decay bands missing/gapped/overlapping/reordered/ordinal-invalid/increasing | Reject; exactly(0,D], authored order retained, no interpolation. U |
| 24 | Boundary ages on each band | Exact lower-exclusive/upper-inclusive selection; no rounding. U |
| 25 | Negative, float, bool, zero-denominator or nonfinite rational | Reject; equivalents and0/x normalize identically. U |
| 26 | Nonempty witnesses all explicit retention0 | Keep all entries/contributions; AVAILABLE0/1 only with resolved occurrence set. U |
| 27 | Empty trace vs unresolved potential events vs explicit zero | Three distinct availability/basis states; no missing-as-zero. U |
| 28 | Unknown meal would fall in a zero-retention band | Remains unresolved; no invented zero occurrence/aggregate total. U |
| 29 | Large rational products/sums, amount>1 | Exact GCD canonical arithmetic; not probability, confidence, cap or quantity. U |
| 30 | Zero unit penalty / unknown operator/unit / hidden recipe policy field | Reject under this explicit v1 policy; no implicit disable/fallback. U |
| 31 | Later-than-cutoff policy (between child captures and completion included) | Reject AS_OF_CAPTURE; preserve child clocks and no retrospective mode. U/PG |
| 32 | Earlier source schedules with future target, equal/offset UTC times | Correct scheduled-time age only; no time-now, source review age or timezone rounding. U |
| 33 | Policy ID/version/provenance/numeric rule change | Derived identity changes, immutable source/review history unchanged. U |
| 34 | Shuffle explicitly unordered inputs | Identical canonical bytes/results; ordered bands/lineage untouched. U |
| 35 | Forge cached witness/age/coverage/unknowns/retention/contribution/total/hash | Recursive primitive and result recomputation rejects, including rehashed construct/copy. U |
| 36 | Repeated capture/retry or overlapping snapshots | No count inflation; single captured subject only, source unions rejected. U/PG |
| 37 | Concurrent proposal replacement between source reads | Old coherent RR/SERIALIZABLE capture replays; fresh exact query must rebind. PG |
| 38 | Concurrent classification/association correction/retraction | Old proof coherent; fresh cut reflects source/head/frontier/unresolved changes. PG |
| 39 | Unrelated Catalog association edit | METHOD/FLAVOR semantics/evidence-cut unchanged; MAIN retains real dependency; audit hash may change. U/PG |
| 40 | Cooked/skip/out-of-stock/passive/preference/accepted/global/family inputs | Closed inputs reject; no new source/attribution/history semantics. U/C |
| 41 | Pure API attempts database/network/file IO or writes | IO traps/import checks; no row/physical/preference/source mutations or commits. U/PG/C |
| 42 | Frozen contracts/hashes/migrations/schema drift | All256 old definitions, all frozen algorithm receipts and0001–0013 unchanged;0013 /71. C/PG |
| 43 | Consumer tries cross-term/dimension/member/candidate or recipe+feature total | No field/operator/API supports it; no giant behavior score or planner weight. U/C |
| 44 | Unknown source claimed as current authority by hash | Replay consistency only; origin/currentness/authorization claims remain unavailable. U/C |

These are implementation acceptance requirements for later review/authorization, not executed041F
coverage. Mocks cannot substitute for the stated PG snapshot/frontier/concurrency behavior.

## 12. Explicit exclusions and review decisions

Do not implement or design-expand into novelty, TasteFit, MemberBehaviorProfile/040C changes,
MTR-024 utility composition, accepted-plan exposure, confirmed/consumed exposure, cross-horizon
history, variant-family exposure, Execution,039 attribution or PRECOMMIT authority. No portfolio,
optimizer, ranking, shared-member aggregation, profile persistence or production default weights.
No new prior/shrinkage source, placeholder, neutral/zero prior or learned evidence is introduced.

Reviewer decisions requested before any implementation:

1. Atomic exact dimension/term/member/meal scope and the explicit per-stage/per-term policy triple.
2. Use of frozen046A term resolution and existential term-occurrence counting, including a known
   positive with unresolved sibling batch versus an unresolved uncounted meal.
3. Conservative unavailable aggregate for any unresolved potential occurrence, even zero-band age;
   scoped empty trace unavailable, nonempty zero-retention trace AVAILABLE0.
4. Contained lookback/target window and the minimum-consumed-child-clock AS_OF_CAPTURE policy cutoff.
5. Exact rational retained-occurrence arithmetic, positive-only unit penalties, separate
   dimensions and no production mappings.
6. Full audit/source identity versus unchanged dimension evidence-cut diagnostics; no liveness or
   origin authentication and no modification of frozen041B/C/D/E/046A.

MTR-040C remains NOT READY/NOT AUTHORIZED for design. MTR-024,020B,021 remain BLOCKED;
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED.041F itself is DESIGN ONLY, NOT FROZEN and
implementation NOT AUTHORIZED. Creating or merging documentation is not implementation approval.
This task will leave the design PR open for architecture review; no implementation begins.

## 13. Verification of this documentation PR

Existing gates validate regression/documentation integrity only, not the proposed041F algorithms
or44 future acceptance cases. Fresh local verification and the exact design PR head/CI receipt
are recorded after checks finish. No new runtime/contract/export/schema/test is added by this PR.

Local verification on2026-10-26:

| Gate | Actual result |
| --- | --- |
| Full Python with real PostgreSQL18.4 | **2015 passed**,0 failures/errors/skips,218.59s; one existing Starlette/httpx warning |
| Regression retention | **2015/2015 exact identities retained**,0 new/removed; compared with canonical040B freeze XML |
| PostgreSQL-real | All785 existing marked tests included/passed; no database behavior tests mocked or replaced |
| Migration/drift/direct SQL/frozen compatibility | Existing full real-PG suite PASS;0013 /71; no migration or runtime change |
| Ruff / architecture / imports | PASS;30 invariants,11 ADRs,50 linked tasks,16 contexts |
| Domain/OpenAPI exports | PASS; all256 definitions and HTTP snapshot unchanged |
| Synthetic fixtures / benchmark |22 verified; **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client contracts/typecheck/tests / web build | PASS; **10/10** client tests |
| Diff scope/whitespace | PASS;8 Markdown documents only; no code/contracts/tests/exports/schema/migrations modified |

Full command: `.venv/Scripts/python -m pytest --basetemp=.local/041f-design-full
--junitxml=.local/041f-design-full.xml`, loopback PostgreSQL enabled. Other checks follow
`.github/workflows/ci.yml`. Ignored `.local/041f-design-*` logs/XML are verification artifacts.
These passing regressions do not prove the proposed041F algorithm or its44 planned cases.
The design PR remains open for architecture review; no merge or implementation is authorized.

Changed documents:

- `docs/product/MTR_041F_FEATURE_REPEAT_POLICY_DESIGN.md` (this design)
- `README.md`
- `docs/product/BACKLOG.md`
- `docs/product/FOUNDATION_STATUS.md`
- `docs/product/GLOSSARY.md`
- `docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md`
- `docs/product/INVARIANT_COVERAGE.md`
- `docs/product/POST_MTR_041E_DEPENDENCY_REVIEW.md`


**READY FOR MTR-041F ARCHITECTURE/DESIGN REVIEW — IMPLEMENTATION NOT AUTHORIZED.**
