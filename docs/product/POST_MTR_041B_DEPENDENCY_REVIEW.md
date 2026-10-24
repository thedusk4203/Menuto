# Post-MTR-041B dependency review

Status: **APPROVED by user;041C implementation authorized separately**. This document records
the original documentation-only review. [Implemented review](MTR_041C_DECAY_TRACE_REVIEW.md) /
[evidence](MTR_041C_DECAY_TRACE_EVIDENCE.md);041C is now user FROZEN at338566c.
The subsequent [post041C review](POST_MTR_041C_DEPENDENCY_REVIEW.md) governs next-slice recommendations.

Reviewed fetched `main` /`origin/main`: **`43192c7303e42c7bac321728edecaa8421a58e9a`**.
User froze MTR-041B at that exact commit (PR #77). Frozen040A/041A/041B remain unchanged.
Schema **0012 /58 domain tables**; migrations0001–0012 immutable. No correction is required.
Full040/041 incomplete;024/020B/021 BLOCKED; Execution NOT STARTED; PRECOMMIT fail-closed.

## 1. Recommendation

The single smallest useful next slice is **MTR-041C — proposal-local Recipe-ID decay-policy
evidence**. This is a proposed sub-slice under existing MTR-041, not a new canonical backlog
number, approved algorithm or implementation authorization.

**Readiness: READY for the bounded policy evaluator, BLOCKED for a full RecentExposureModel.**
Existing canonical truth can supply immutable provisional witnesses with exact age relative to
the target. A separately authored/versioned policy can define how their influence attenuates
with age. This needs no confirmed-history producer, inferred feature mapping or numeric default.
No persistence/migration is expected. Stop for architecture approval before writing code.

This recommendation advances a requirement *owned by041 itself*: spec§19.4 and ADR-011 Decision3
require configurable/versioned decay. It is not a reason to declare024 ready or bypass source
coverage. A useful sub-slice need not complete all parent dependencies at once.

## 2. Current frozen boundary and actual evidence

[041B review](MTR_041B_RECIPE_COOLDOWN_REVIEW.md) /[evidence](MTR_041B_RECIPE_COOLDOWN_EVIDENCE.md)
prove a target-relative predicate within one current captured proposal. The target is PLANNED,
member-scoped, Recipe-ID resolved from positive planned allocation. Lookback is [T-D,T), whole
target excluded, equal time not earlier. Full capture window is required. window.end ==T is valid
because graph resolution identifies the target independently from the filtered preview window.

041B intentionally stops at positive witnesses, exact integer microsecond distances and a scoped
match/no-match result. It does not implement decay, RepeatPenalty, novelty, accepted schedule,
confirmed/member consumption, attribution, history completeness or source liveness authorization.
No-match never means globally safe or never-exposed. A snapshot hash does not grant authority.

Inspected canonical sources: spec [§13.14,§14.10,§19.1–19.8,§21,§24.3](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[ADR-009](../adr/ADR-009-execution-state-machine.md),
[ADR-010](../adr/ADR-010-independent-validator.md),
[ADR-011](../adr/ADR-011-behavioral-learning-loop.md),
[invariants](../ARCHITECTURE_INVARIANTS.md), [backlog](BACKLOG.md),
[blueprint](IMPLEMENTATION_BLUEPRINT_M0_M1.md), [status](FOUNDATION_STATUS.md),
[post041A review](POST_MTR_041A_DEPENDENCY_REVIEW.md), and
[MTR-026 dependency review](MTR_026_DEPENDENCY_REVIEW.md).

| Current code (relative to apps/backend/) | What it establishes |
| --- | --- |
| `app/modules/learning/contracts.py`: RecipeCooldownPolicy/Input/Witness/AssessmentDraft; _cooldown_context/_cooldown_values | Required explicit duration; exact target and ages; revalidated, hashed policy/provenance/input; recomputed result; decay/novelty/RepeatPenalty UNAVAILABLE. |
| `learning/public.py`: assess_recipe_cooldown; preview_recent_exposure; deduplicate_preview_facts | Pure revalidation/replay; no DB IO, ranking, Preferences runtime or optimizer. Conflicting source revisions require recapture. |
| `planning/exposure_capture.py`; `planning/public.py`: latest_proposal_source | Canonical current selected-proposal ingress in clean read-only RR/SERIALIZABLE. Current at capture, not continuously current. |
| `execution/public.py`: PlanRevisionService.publish/horizon_handoff; frozen0008 menuto_plan_no_authority | No production accepted-publication issuer; v3 horizon handoff explicitly deferred; namespace does not implement MealExecution. |
| `validation/public.py`, `validation/contracts.py` | Required source/enforcement gaps and non-authorizing reports; POSTFACT diagnostic. No production026 completion. |
| `catalog/contracts.py`: AffinityFeatureTermFact; `preferences/contracts.py` | Reviewed feature vocabulary and explicit member assertions exist. Vocabulary does not assign features to recipes/selected ingredient paths. |
| `tests/test_recipe_cooldown.py`, `test_postgres_recipe_cooldown.py` | Boundary precision, whole-target exclusion, policy identity, unsupported inputs, immutable source, zero-IO and concurrent source replacement. |

Graphify was consulted for ADR-011/INV-030 relationships using existing vocabulary
exposure/horizon/learning/policy/recipe. Its graph predates current implementations; actual
current contracts/tests, not old namespace labels, determine readiness. No concrete contradiction
or isolated defect justifies changing frozen code or migrations.

## 3. Remaining capability/dependency matrix

READY means the explicitly bounded operation has all necessary *source truth*. Defining its
new policy contract is part of that slice, not pretending a policy/default already exists.
PARTIALLY READY means some facts/identities exist but interpretation/capture is missing.
BLOCKED identifies a missing upstream domain source. Order is dependency priority, not MTR number
or permission to implement: N=next proposed subset; S=source/feature branch; L=later integration.

| Capability | Existing primitives | Missing primitive / owner | Status | Prerequisite MTR | Order |
| --- | --- | --- | --- | --- | --- |
| Recipe-level proposal preview/cooldown | Frozen041A/B, exact member/recipe/time/source | None for frozen scope | READY / FROZEN | None | Preserve |
| Age-dependent provisional decay evidence |041B exact positive witness ages and captured policy/source | Explicit versioned attenuation policy and exact per-witness result; Learning-owned, not new behavioral truth | READY for new bounded evaluator | Proposed041C using frozen041B | **N** |
| Production decay defaults | Versioned-policy pattern | Reviewed/tuned parameter set, applicability and supporting evidence | BLOCKED for a default claim |041 policy curation/benchmark work under§24.3 | Separate from N; no seeded defaults |
| RepeatPenalty dimension | Identity, scoped cooldown witnesses; future decay coefficients | Explicit aggregation, source-kind weighting and availability semantics; Learning derivation,024 composition separate | PARTIALLY READY |After041C, separately review041 penalty-policy subset; wider sources below | Later041 policy, not N |
| Novelty | Recipe identity; scoped absence semantics | Covered history/source completeness and explicit novelty definition; missing evidence ≠novel | BLOCKED for production novelty |Remaining041 sources/coverage;046 for feature novelty;024 composition | After relevant S |
| Accepted-schedule exposure |016 graph/revision/publication structures | Production validator coverage/issuer, TOCTOU/source recheck and accepted-source capture | BLOCKED |026 upstream primitives/independent checks →026 authority with016/027 →041 capture | S, broader than N |
| Confirmed exposure/consumption | ADR event semantics; member/recipe IDs; physical ledger | Actual member-attributed confirmed event, correction lineage and complete source stream | BLOCKED |023/035 confirmed source →039 routing;017 capture →041 history | L; do not start Execution |
| USER_CONFIRMED_COOKED exposure | ADR-011 distinguishes cooking from liking/eating | Real cooking confirmation with explicitly attributed subject and correction lineage | BLOCKED |023/035 producer +039;017 confirmed view | L |
| Reversible assumed exposure | ADR semantics only | Assumption identities, causal parents/reversal/conflict contracts and operational view | BLOCKED |017/036 +039 →041 provisional extension | L; never durable history |
| Cross-horizon canonical replay | Source timestamps/IDs, overlap set union and draft handoff | Resolved017 views;038 contribution/commitment identity linking confirmed/provisional and asset transformations | BLOCKED |017 +023 planned flow →038;036 if assumptions;026 for accepted source | S/L |
| Member-owned durable history/frontier | Per-member previews; immutable proposal lineage | Confirmed semantic source stream, completeness frontier and replay/correction contract | PARTIALLY READY |023/035 +039 +017 →041 history | L |
| METHOD/PROTEIN/FLAVOR fingerprint | Stable IDs, exact bindings and reviewed term vocabulary | Authored recipe/selected-path→feature assignment, applicability/version/frontier | BLOCKED |046 reviewed assignment source design, coordinated with018/019 | S before those fingerprints |
| Variant/family repeat identity | Exact candidate/binding hashes | Authored family identity and version/path membership; hashes are not semantic families | BLOCKED |046 with018/019 authored mapping →041 | S before family |
| Cold-start/prior semantics | Explicit040A UNDECLARED/NEUTRAL/RETRACTED;041 scoped absence | Explicit priors/profile policy and coverage-aware interpretations | PARTIALLY READY |Remaining040 +028 priors;041 broader history/novelty | S; no inference from emptiness |
| MTR-024 source readiness | Raw040A assertions and bounded041A/B facts | Profile affinity, supported repeat/novelty and other separable source/policy inputs | BLOCKED |Remaining040/041,039/046 where applicable;006/007/008 contextual policy branches | Not unlocked by N |

Full041 cannot complete from proposal previews alone. A/B/C do not certify the required history,
multi-fingerprint or causal cross-horizon source chains. MTR-020B and021 remain blocked as before.

## 4. Why decay evidence is the smallest next step

Two earlier proposed meals can both satisfy041B's cooldown while having different ages.041B
reports those ages but defines no attenuation. An explicit age policy would let a later consumer
tell how each witness is interpreted *under that named policy*, preserving the original source.
That is a new, reproducible policy interpretation, not renaming occurrence_count or match=true.

Do not turn this into a new utility scalar. The proposed next result is a **per-witness decay
trace**, not total RepeatPenalty, novelty, TasteFit, EvidenceStrength, RecipeScore or ranking.
It provides a required primitive for a later independently reviewed penalty policy. Formula or
default choice does not become canonical merely because synthetic tests demonstrate arithmetic.

Alternatives reviewed:

| Candidate next slice | Why not select it first |
| --- | --- |
|046 reviewed feature assignments | Useful required branch for full multi-fingerprint041. Needs a new durable mapping design and curation/frontier semantics; no missing mapping prevents Recipe-ID age interpretation. It cannot supply decay or history by itself. |
|039 router | Needed when enabling behavioral source kinds. A router cannot manufacture confirmed source events; no router needed to retain041B's fixed PROPOSAL_PREVIEW classification. |
|017/038 projection/bridge | Required later for canonical commitments, assets and cross-horizon reconciliation. Not equivalent to same-proposal age evaluation and has broader upstream flow/lineage needs. |
|026/accepted-schedule source | Missing complete validation authority and authoritative TOCTOU frontier recheck, not just a SELECT adapter. Cannot safely unlock accepted data by a narrow Learning change. |
| Confirmed exposure source /Execution | Producing physical/execution facts solely for learning would invert the approved dependency chain. No new execution workflow is authorized. |
| RepeatPenalty aggregation now | Requires its own explicit aggregation/applicability policy; skip neither age semantics nor source availability. Age evidence can be derived without inventing an aggregate utility interpretation. |
| Novelty now | Empty selected proposal scope cannot prove unexposed or complete history. A novelty wrapper would fabricate evidence. |

This is a recommended topological order, not a claim that the DAG admits only one order.
It advances041's own mandatory policy work; it does not move optional inventory-match work ahead
of the behavioral critical path.046/017/038/039/026 remain real dependencies for their named
branches and must not be silently removed from the full041 completion criteria.

## 5. Proposed041C boundary for separate approval

### Inputs and ownership

Learning consumes an immutable, fully revalidated **041B assessment** (including its complete
subject/source primitives) plus a new explicit versioned decay policy. Still exactly one
current-at-capture proposal, one member, target and Recipe ID. No arbitrary witness list or
caller-authored event may replace source reconstruction. No DB calls during evaluation.

The policy should define explicit age bands and exact attenuation multipliers. A minimal
reviewable representation is a bounded piecewise-constant policy over the same lookback D:
ordered adjacent bands **(lower_age_us, upper_age_us]**, covering (0,D] exactly. Non-negative
integer lower bounds and positive upper bounds; first lower bound0; last upper bound equals041B duration. No gaps, overlaps or
implicit tail/default. This matches041B's [T-D,T), including age D and excluding age0.

Propose exact rational numerator/denominator multipliers in [0,1], denominator positive,
canonical exact representation and non-increasing retention as age increases. These bounds
define attenuation, not a calibrated probability. No sample bands/multipliers are production
defaults. This is a proposed minimal policy shape for approval, not an already accepted ADR
constant or implemented contract. Another exact representation may be approved before coding.

Policy provenance/version and applicable fixed source kind must enter result identity. Policy
observation after capture must reject, as in041B; otherwise a new coherent capture is required.
User approval clarifies this is AS_OF_CAPTURE only, not a ban on future separately designed
retrospective evaluation. The equality to D bounds this subset's already-eligible witnesses;
it is not an architecture invariant requiring full decay horizon to equal cooldown.
Learning owns interpretation. Immutable policy definitions may stay alongside041B's Learning
policy contracts; moving them into shared Policy is not a prerequisite and must not redesign B.

### Outputs and failure semantics

New independently versioned DRAFT output, activation_ready=False, with original source/query/
041B identity, decay policy identity, exact witness ages, selected band identity/bounds and exact
retention multiplier per witness. Recompute all traces from source and policy on deserialization.
Order witness sets deterministically; keep band ordinal/boundary semantics explicit. A multiplier
of0 is only allowed when explicitly authored; retain that witness/provenance rather than erase it.

Empty witnesses produce an empty **scoped trace**, never a global zero penalty or novelty claim.
Reject missing/malformed policy, incomplete/ambiguous bands, unsupported source/fingerprint,
foreign query, tampered witness/distance, retention increasing with age, or incompatible lookback.
No silent interpolation, exponential curve, rounding, source blending, default parameter or
normalization into a probability. Rational exactness must not quantize into stored quantities.

Keep accepted schedule, confirmed/member consumption, global history, novelty, TasteFit,
EvidenceStrength and final RepeatPenalty UNAVAILABLE. Do not mutate041B's frozen decay field:
its nested result remains exactly as frozen; any new interpretation belongs to041C's new contract.
There is no output aggregate sum/average/max, portfolio role, final objective or activation gate.

### What adds genuine semantics and what stays deferred

041B answers interval membership;041C would answer the age-to-retention mapping under an
explicit policy for each eligible proposed witness. Numeric values describe the selected
configuration, not measured behavioral truth.024 still owns final separable utility composition;
later041 work must separately define how repeat evidence becomes a RepeatPenalty dimension.
Neither that dimension nor Stage-2 weights should be smuggled into this trace evaluator.

No table, exposure store, new migration, recipe feature assignment, assumption graph, safety
policy, chronology replay, accepted-source producer, Execution, optimizer or AI is needed.
Migration expectation: **NONE**. Frozen schema stays0012 /58. No alteration of A/B hashes.

## 6. Adversarial approval criteria

These are required **future** tests, not tests added or claimed implemented by this review:

1. Two eligible witnesses of different ages select their explicitly authored bands; this changes
   interpretation without changing whether either witness matched041B's cooldown predicate.
2. Boundary age D is covered; age0 is not eligible. Shared band endpoint belongs to exactly one
   band under (lower,upper]; no generic tuple sorting may decide time precedence.
3. Missing band, overlap, nonpositive denominator, float/NaN/Inf, increasing age-retention,
   mismatched lookback or missing policy rejects; no default/zero fallback.
4. Explicit zero multiplier retains its original witness. No witnesses preserve unavailable
   global history/novelty/penalty and never mean never-exposed.
5. Cached coefficient/band/age or original041B outcome tampering rejects via recomputation.
6. Changing policy identity/version/provenance changes result identity; identical normalized
   immutable inputs yield identical bytes. New captured_at may legitimately change identity.
7. Mixed/foreign combinations or an old query against a fresh proposal capture still reject;
   unchanged immutable old snapshots remain replayable. Fresh proposal needs coherent recapture.
8. Policy age attenuation cannot promote scheduled evidence to confirmed eating or taste,
   or copy one member's preference/exposure to another. No DB/IO or mutation occurs in core.
9. All frozen A/B tests/hashes/schema definitions and previous regressions remain unchanged.

Applicable invariants: INV-012/013 evidence vs time/inference;018 provenance/explicit exact
primitives;021 no authority;022–029 no passive durable learning, friction/execution→taste,
member fan-out, scalar collapse, explicit-policy rewrite or forced preference evidence;
030 future bridge remains incomplete;009 no unsupported probability.005/006 culinary authorship
and007 Retail evidence remain untouched. Reservation/material AP→EP/cooking ownership unchanged.

## 7. Final dependency decision and stop boundary

```text
040A FROZEN
041A FROZEN →041B FROZEN
               ↓
      proposed041C explicit proposal-local decay trace (review next, not implemented)
               ↓
      later041 penalty-policy interpretation +remaining sources/classifications/history
               ↓
      024 (still BLOCKED; also needs remaining040 and other approved input domains)
               ↓
      020B BLOCKED →021 BLOCKED
```

Is full041 completable now? **NO**. Are024/020B/021 allowed to start? **NO**.
Is Execution required for this next policy subset? **NO**; do not open it to create learning
truth. Does the proposed041C need migration? **NO**. Does041C itself finish041 or unlock024?
**NO**. One smallest next slice: **041C proposal-local Recipe-ID decay-policy evidence**,
subject to architecture approval. No capability implementation is authorized by this document.

## 8. Review verification

Head/table count checked from fetched main, Alembic graph and registered ORM metadata; not a
live-production database claim. Runtime/contracts/export/migrations and tests remain unchanged
from user-frozen43192c7. Local checks: **245 existing tests passed** across exposure/cooldown,
explicit preferences, validation foundation/canonical review, architecture and baseline.
Architecture30 invariants/11 ADRs/50 tasks,16-context import boundaries, domain/OpenAPI drift,
document links and whitespace all PASS. No local PostgreSQL rerun is claimed for documentation
changes; full PostgreSQL-backed PR/merge CI is verified at delivery.
This review adds no test or production capability and records no new invariant
certification. Frozen baseline evidence remains1453 Python /635 real-PG,22/22 benchmark,
client10/10 and post-merge CI40073675503 SUCCESS.

**READY FOR ARCHITECTURE REVIEW**
