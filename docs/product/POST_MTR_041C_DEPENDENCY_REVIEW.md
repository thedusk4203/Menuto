# Post-MTR-041C dependency review

Status: **ARCHITECTURE APPROVED** by user after PR #80. Historical dependency review.
Implementation is tracked in [041D review](MTR_041D_REPEAT_PENALTY_REVIEW.md) and
[evidence](MTR_041D_REPEAT_PENALTY_EVIDENCE.md);041D is now user FROZEN at091daa81.
The [post041D review](POST_MTR_041D_DEPENDENCY_REVIEW.md) supersedes the next-slice recommendation.

Reviewed fetched `main` /`origin/main`: **`338566c84197196dae12bbefd9e1ef0c96958f2f`**.
User-frozen040A and041A/B/C remain untouched. Current schema **0012 /58 domain tables**;
migrations0001–0012 immutable. No correction to041C is required. Full040/041 incomplete;
024/020B/021 BLOCKED; Execution NOT STARTED; PRECOMMIT fail-closed.

## 1. Decision

**Recommend MTR-041D — proposal-local Recipe-ID RepeatPenalty interpretation policy.**
This is a proposed sub-slice under canonical MTR-041, not a new backlog numbering scheme.
**READY for a bounded policy interpretation; BLOCKED for global/production RecentExposureModel.**
User approval is now recorded; the historical proposal below remains the design rationale.

Existing source truth can answer: under an explicit policy, what repeat-penalty amount is
assigned to this member/target/Recipe ID's eligible proposed repetitions **within this one
current-at-capture proposal**? Frozen041C already provides revalidated witnesses, exact ages
and explicit per-witness decay interpretation. No new actual behavior is needed for that
limited question. The missing aggregation/unit policy belongs inside this slice; it is not
a missing upstream producer. No default policy value or empirical claim follows from readiness.

The critical distinction is **one behavioral dimension vs a composite score**. Spec§14.10
lists repeat_penalty separately from taste_fit/time_fit/equipment_fit/novelty_value. ADR-011
Decision4 and INV-027 defer *cross-dimension composition* to Stage2; they do not ban an explicit
repeat-only interpretation. Thus summing eligible contributions under a named repeat policy
need not create RecipeScore, AdherenceScore, TasteFit or planner utility. It must remain scoped,
provenance-bearing and unusable as a claim of global history, safety, optimality or authority.

## 2. Current boundary and inspected evidence

Canonical references: [spec§14.10,§19.1–19.8,§21,§24.3](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[ADR-011](../adr/ADR-011-behavioral-learning-loop.md),
[ADR-009](../adr/ADR-009-execution-state-machine.md),
[ADR-010](../adr/ADR-010-independent-validator.md),
[invariants](../ARCHITECTURE_INVARIANTS.md), [backlog](BACKLOG.md),
[blueprint](IMPLEMENTATION_BLUEPRINT_M0_M1.md), [status](FOUNDATION_STATUS.md),
[post041B review](POST_MTR_041B_DEPENDENCY_REVIEW.md),
[041C review](MTR_041C_DECAY_TRACE_REVIEW.md)/[evidence](MTR_041C_DECAY_TRACE_EVIDENCE.md),
and [026 dependency review](MTR_026_DEPENDENCY_REVIEW.md).

Frozen041A supplies selected-proposal evidence;041B resolves exact target/member/Recipe ID,
positive planned allocations and [T-D,T) witnesses;041C applies ordered explicit decay bands
to those witnesses using reduced exact rational multipliers. Zero retention retains evidence.
None exposes an aggregate. Nested041B/041C repeat_penalty remains UNAVAILABLE, and their
activation_ready flags remain false. No older contract field should be changed to add041D.

Code inspected at reviewed commit (paths relative to `apps/backend/`):

| Source | Evidence |
| --- | --- |
| `app/modules/learning/contracts.py`: RecipeDecayInput/TraceDraft, _decay_entries | Fully reparses frozen041B, exact band selection and source trace; no aggregation, penalty unit or policy. |
| `learning/public.py`: trace_recipe_decay/assess_recipe_cooldown | Pure replay, no DB/optimizer/Preferences/Execution runtime; no RepeatPenalty public API. |
| `planning/exposure_capture.py`, `planning/public.py`: latest_proposal_source | Canonical RO RR/SERIALIZABLE capture of latest selected sealed proposal; bounded source manifest, not complete behavioral history. |
| `execution/public.py`, frozen0008 menuto_plan_no_authority | Production accepted publication blocked; namespace is intent orchestration, not a member-eating source. |
| `validation/contracts.py`, `validation/public.py` | Required capability gaps, non-authorizing reports; POSTFACT diagnostic. |
| `catalog/contracts.py`, frozen040A Preferences contracts | Reviewed feature vocabulary and explicit member declarations, not recipe/path classifications or inferred behavior. |
| `tests/test_recipe_decay.py`, `test_postgres_recipe_decay.py` | Exact rational and ordered topology, nested tamper rejection, source concurrency, pure replay and unavailable output boundaries. |

Graphify orientation used existing tokens exposure/learning/policy/utility, pointing to ADR-011
and INV-027/030. Its older graph is not evidence of current runtime capability; actual current
code/tests control this review. No concrete architecture contradiction or frozen-code defect found.

## 3. Remaining dependency matrix

READY refers only to the named supported scope. PARTIALLY READY means existing primitives need
new policy/capture semantics. BLOCKED identifies missing upstream source truth. N=next proposed
slice; S=source branch before enabling that capability; L=later integration. No order here
authorizes code or permits bypassing a blocked source.

| Capability | Existing primitives | Missing primitive / owner | Status | Exact prerequisite | Order |
| --- | --- | --- | --- | --- | --- |
| Proposal-local Recipe-ID evidence/cooldown/decay | Frozen041A/B/C | None within frozen scope | READY / FROZEN | None | Preserve |
| Local RepeatPenalty interpretation | Exact revalidated041C trace; one member/target/proposal; per-witness retention | Explicit repeat-only aggregation, scale/unit and availability policy; Learning owns derivation | READY for bounded new policy subset | Proposed041D, architecture approval first | **N** |
| Global/cross-source RepeatPenalty | Bounded provisional facts only | Covered history, authoritative source-set completeness, correction/reconciliation and source-kind applicability | BLOCKED |Remaining041 sources;017/038 for bridge,023/035 +039 for actual events;026 for accepted source | S/L |
| Production numeric defaults | Explicit-policy pattern | Reviewed parameter values and applicability with supporting evidence | BLOCKED as a default claim |041 policy curation /benchmark evidence per§24.3 | Separate, no seeded constants |
| Novelty | Recipe IDs and scoped absence marker | Covered history and a novelty definition; absent facts are not never-exposed | BLOCKED |Remaining041 history/coverage;046 for feature novelty;024 composition | After relevant S |
| METHOD/PROTEIN/FLAVOR repeat | Reviewed terms and exact culinary IDs | Authored recipe/selected-path feature assignments and source coverage/frontier | BLOCKED |046 reviewed mapping source design with018/019 authored paths | S, not needed for Recipe-ID-only N |
| Variant/family repeat | Exact candidate/binding signatures | Authored family IDs/membership across versions/paths | BLOCKED |046 with018/019 authored family mapping →041 | S |
| Accepted-schedule exposure |016 immutable revision/publication structures | Complete production026 checks/issuer and all-source TOCTOU recheck; accepted-source capture | BLOCKED |026 source prerequisites →026 authority with016/027 seam →041 accepted capture | S |
| Confirmed exposure /consumption | ADR event semantics, Recipe/member identity, physical inventory ledger | Explicit attributed semantic events, correction history and complete source stream | BLOCKED |023/035 confirmed producers →039 routing;017 confirmed capture →041 history | L; do not start Execution |
| USER_CONFIRMED_COOKED exposure | ADR exposure≠taste/eating rule | Real cooking confirmation, explicit attributed subjects and corrections | BLOCKED |023/035 +039;017 source view | L |
| AUTOPILOT_ASSUMED provisional exposure | ADR rule only | Reversible assumptions, causal dependencies/reversals and operational view | BLOCKED |017/036 +039 →041 provisional extension | L; never durable history |
| Cross-horizon exposure reconciliation | Source IDs/times and overlap union | Resolved views, commitment/flow lineage, unique cross-source contribution identity | BLOCKED |017 +023 planned flow →038;036 if assumptions;026 for accepted producers | S/L |
| Member-owned durable history/frontier | Scoped per-member previews and immutable proposal history | Confirmed semantic event stream, completeness frontier and correction replay | PARTIALLY READY |023/035 +039 +017 →041 history | L |
| Shared-meal preference/penalty aggregation | Participant IDs; explicit040A declarations; per-member previews | Derived profile, approved member aggregation/availability and safety ordering | PARTIALLY READY |Remaining040/041 +024; hard safety sources005/006/046 as applicable | Later; no cross-member sum in N |
| MTR-024 separable utility inputs | Raw040A assertions and bounded041A/B/C sources | Remaining profile affinity, covered repeat/novelty/context inputs and composition policy | BLOCKED |Remaining040/041,039/046 and006/007/008 where applicable | Not unlocked by N |

## 4. Why not an upstream source/classification slice first?

046 is genuinely necessary for multi-fingerprint semantics, but a term assignment cannot define
how Recipe-ID repetition becomes a penalty.017/038 cannot supply a penalty scale and also need
broader resolved flow/commitment contracts.039 cannot fabricate a confirmed event stream.
026/accepted capture cannot be unlocked by adding a Learning reader: authority and complete
source-frontier rechecks remain missing. None blocks a deliberately provisional, Recipe-ID-only
policy interpretation of source facts already captured and independently revalidated.

Conversely,041D would not replace those prerequisites. No amount of proposal-local arithmetic
completes full041 history, feature classification or cross-horizon replay. This is a recommended
dependency order, not the only possible topological order; source branches may proceed only
under their own separately approved designs. Do not open Execution merely to make learning easier.

This next slice adds a missing *041-owned interpretation*, unlike optional inventory-match signals
that cannot unblock the behavioral path. It remains a real new semantic step only if it defines
unit, aggregation, applicability and absence semantics; renaming sum(retention) as a ready global
RepeatPenalty or returning a cached scalar without its primitive proof would not qualify.

## 5. Minimal proposed041D design for approval

### Inputs and ownership

Consume a fully revalidated **frozen041C trace** (including all frozen041B/source facts) and a
new explicit versioned repeat-interpretation policy. No free witness/contribution list. Scope
remains one proposal/member/target/Recipe ID and fixed PROPOSAL_PREVIEW source kind.

Learning owns the derived **proposal-local repeat dimension**. Explicit immutable policy is
normative configuration, not learned behavioral truth. Proposed minimal policy fields:

- policy_id/version/provenance; fixed AS_OF_CAPTURE /RECIPE_ID /PROPOSAL_PREVIEW applicability;
- an explicitly supplied operator **SUM_RETAINED_OCCURRENCES**, no default or expression DSL;
- an explicitly supplied **positive exact rational unit_penalty**, with a distinct typed unit
  **POLICY_REPEAT_PENALTY_UNITS**. No production default value, cap, normalization or empirical label.

The operator above is a proposed initial profile to approve, not an ADR-mandated universal
formula. MAX/MEAN, caps, saturation and source blending remain deferred; do not implement a
generic multi-operator framework. Changing interpretation requires a new explicit policy identity.

Policy time is **AS_OF_CAPTURE**, consistent with C: observed_at <=captured_at. Retrospective
evaluation remains a separate possible future semantic. Source is current at capture only;
replay does not query DB or mint authorization. Newer policy may require new coherent capture
for this mode, rather than silently changing an old result's interpretation.

### Arithmetic and types

For each eligible trace entry i, proposed contribution is:

`contribution_i = unit_penalty × entry_i.retention_multiplier`

For a nonempty eligible trace, proposed local amount is the exact sum of those contributions.
Use canonical reduced rational arithmetic with explicit numerator/denominator, positive
denominators and no float, Decimal-context rounding or implicit quantization. Preserve every
entry, including explicit zero retention/contribution, and recompute all contributions/total.

**Do not reuse RetentionMultiplier for a penalty amount.** Retention is bounded0..1 and belongs
to decay-policy interpretation. Penalty amounts are non-negative, potentially greater than1,
with their own policy-defined unit. A new exact rational penalty value object would be required;
this is not Money, physical Quantity, EvidenceStrength, probability, confidence or TasteFit.
No persistence is proposed, so no storage quantization or generic conversion table is needed.

Only this one dimension is aggregated. No taste/time/equipment/nutrition/cost mixing, member
aggregation, candidate ranking, portfolio role or Stage-2 objective weight enters the formula.
024 remains owner of eventual composition; no optimizer/solver/candidate generator import.

### Outcomes and absence semantics

Propose a new independently versioned DRAFT result with activation_ready=False, exact source/
query/C-trace/policy identity, per-witness contribution trace and explicit coverage.

| Source case | Proposed local outcome | Local amount | Meaning |
| --- | --- | --- | --- |
| Nonempty valid eligible trace | INTERPRETED_IN_SELECTED_PROPOSAL | Exact derived rational | Configured interpretation of this member's proposed repetitions only |
| Nonempty trace with all explicit retention0 | INTERPRETED_IN_SELECTED_PROPOSAL | Computed0 in named unit | Policy-derived zero with witnesses retained, not missing data |
| Valid frozen NO_MATCH /empty trace | NO_MATCH_IN_SELECTED_PROPOSAL | **UNAVAILABLE /None** | Preserve scoped absence; do not manufacture a global zero or never-exposed fact |
| Missing/malformed policy, unsupported source, invalid/cross-owner/tampered input | Reject | No result | Do not fall back to zero, neutral preference or an arbitrary policy |

Empty-sum0 is mathematically possible inside a closed scope. The conservative proposed wire
contract deliberately avoids emitting a numeric penalty for an empty evidence trace; callers
must preserve the absence state, never coalesce None to0. This is a design choice for approval,
not a claim that arithmetic cannot sum an empty set. Explicit zero with witnesses stays distinct.

Use an explicit name such as **proposal_local_repeat_penalty**, not an unqualified production
repeat_penalty field. Global RepeatPenalty/history, novelty, TasteFit, confirmed consumption/
exposure and accepted schedule remain UNAVAILABLE. Existing frozen B/C fields remain exactly
UNAVAILABLE; the new dimension lives only in the new contract. No source witness is modified.

Policy metadata, exact unit/scale/operator and every contribution enter deterministic identity.
Identical normalized immutable inputs yield identical bytes; policy/provenance/source changes
change identity. No live liveness/TOCTOU claim. Policy amounts from different policies/scopes
are not automatically comparable or rankable. No probability/P90 interpretation or calibration.

## 6. Adversarial approval criteria

These are required **future** tests, not tests added by this review:

1. Two eligible source witnesses yield two retained contribution traces and the exact configured
   local sum; no duplicate counting of one meal's multiple batches/versions.
2. A summed amount greater than1 is valid in policy penalty units, never coerced into a probability
   or the bounded RetentionMultiplier type. Equivalent rational spellings canonicalize identically.
3. Explicit zero retention preserves witnesses and zero contributions; empty valid trace returns
   the explicit no-match/None state. Missing source/policy never defaults to numeric0.
4. Forged model_construct/copy input, cached C coefficient, contribution, total, unit or outcome
   must reject after full source/policy recomputation; no trusted witness array.
5. Require unit_penalty/operator/provenance/version; reject floats, nonpositive denominator,
   missing parameters, unknown operator/fingerprint/source, cap/ranking/utility fields.
6. Policy observation cutoff is as-of capture. Later/retrospective mode rejects without declaring
   all future retrospective interpretation forbidden. Policy changes change identity.
7. Same normalized input gives identical bytes; ordered policy facts keep ordinals, unordered
   witness/contribution sets sort only by explicit stable keys, not invented chronology.
8. Foreign member/target/proposal or mixed revisions reject; old immutable snapshots remain
   replayable; fresh canonical capture must bind its own current query. Core performs zero IO.
9. No preference mutation, member fan-out, consumption/confirmed/accepted promotion, global
   safety/novelty claim, physical movement, optimization or PRECOMMIT authority.
10. Preserve frozen040A/041A/B/C hashes/schema definitions and all previous tests; real-PG capture,
    concurrency, immutable-source, migration/drift and full client/benchmark/CI gates remain green.

Applicable invariants: INV-012/013 retain scheduled/provisional truth;018 explicit provenance and
exact values;021 gating remains fail-closed;022–029 forbid passive durable learning, operational/
execution→taste, member fan-out, cross-dimension scalar collapse, policy rewrite and forced
preference evidence;009 no probability claim;030 full bridge remains incomplete.005/006 culinary
authorship and007 retail evidence are untouched. Reservations remain intent, not physical stock;
Retail AP→EP and Recipe cooking yield ownership remain separate.

## 7. Final answers and implementation stop

```text
040A FROZEN;041A/B/C FROZEN
    ↓
proposed041D local RepeatPenalty interpretation policy (next review, no code here)
    ↓
remaining041 source/classification/history/bridge branches +remaining040 profile inputs
    ↓
024 BLOCKED →020B BLOCKED →021 BLOCKED
```

Smallest next slice: **041D bounded proposal-local RepeatPenalty policy**, subject to architecture
approval. Does an upstream source/classification prerequisite have to precede this scope? **NO**.
Do full/global041 capabilities still require upstream work? **YES**, as the matrix records.
Can full041 complete now, or can024/020B/021 start? **NO**. Execution required for the proposed
policy step? **NO**. New migration required for this pure transient slice? **NONE expected**.
The documentation merge itself did not authorize implementation or self-freeze. Subsequent
explicit user approval authorized implementation; the later user freeze at091daa81 closes that gate.

## 8. Verification and evidence

Reviewed commit/head/table count verified from fetched main, Alembic revision graph and
registered ORM metadata (not a live-production DB claim). No runtime/contracts/test/export/
migration change from frozen338566c. Local verification: **327 existing tests passed** across
exposure/cooldown/decay, explicit preferences, validation foundation/canonical review, architecture
and baseline;30 invariants/11 ADRs/50 tasks,16-context import boundaries, domain/OpenAPI drift,
document links and whitespace PASS. No local PostgreSQL rerun is claimed for documentation-only
changes; full PostgreSQL-backed PR/merge CI is verified at delivery.
Frozen baseline evidence remains1540 Python /640 real-PG,
1453 prior regressions retained,87 new tests, benchmark22/22, client10/10 and exact-merge
CI40076805477 SUCCESS. This document adds no validator or new invariant enforcement.

**READY FOR ARCHITECTURE REVIEW**
