# MTR-041F — Proposal-local Reviewed Feature Repeat Policy Foundation

Status: **IMPLEMENTED / NOT FROZEN — architecture/freeze review pending**.
The user approved [the design](MTR_041F_FEATURE_REPEAT_POLICY_DESIGN.md) and implementation from
canonical main `9e9dfc0f9cf234a8e0c32082652318becce38bfd` (design PR #92; exact post-merge
[CI40223523693](https://github.com/thedusk4203/Menuto/actions/runs/40223523693) SUCCESS).
This implementation does not self-freeze041F or authorize any later milestone.

## Delivered scope

Additive pure Learning public functions:

- `assess_feature_cooldown(FeatureCooldownInput)`;
- `trace_feature_decay(FeatureDecayInput)`;
- `interpret_feature_repeat_penalty(FeatureRepeatPenaltyInput)`.

`learning/feature_repeat.py` exposes these three functions. The repository prohibits contracts
from importing implementation modules, so recursive immutable verification and derivation live
in `learning/contracts.py`, like the frozen Recipe-ID chain. They import only immutable owner
contracts and neutral arithmetic/canonical primitives; the new pure module has a strict import
allowlist. No new HTTP endpoint, capture adapter, source matcher, transaction, cache or store.

The20 additive exported contracts are:

```text
FeatureRepeatQuery, FeatureRetentionMultiplier, FeatureRepeatPenaltyAmount,
FeatureCooldownPolicy, FeatureDecayBand, FeatureDecayPolicy, FeatureRepeatPenaltyPolicy,
FeatureCooldownInput, FeatureTermCoverageCell, FeatureMealTermOccurrence,
FeatureCooldownWitness, FeatureCooldownAssessmentDraft,
FeatureDecayInput, FeatureDecayTraceEntry, FeatureDecayTraceDraft,
FeatureRepeatPenaltyInput, FeatureRepeatPenaltyContribution,
AvailableProposalLocalFeaturePenalty, UnavailableProposalLocalFeaturePenalty,
FeatureRepeatPenaltyDraft
```

One atomic query is one household/member/plan/selected proposal/target meal/dimension/exact term.
Only METHOD, MAIN_PROTEIN and FLAVOR are accepted. Policies independently bind exact dimension,
term, ID, version and USER/REVIEWED_REFERENCE provenance. The operator and positive rational unit
penalty must be explicitly supplied; no policy defaults, fallback terms, recipe weights or implicit
dimension ordering. Test values are synthetic, not production recommendations.

Every stage recursively reparses the **full** frozen041E preview/source, reconstructs its exact
diagnostic manifest, then independently recomputes prior stages. It accepts no caller event array,
coverage flag, cached count, witness list, subtotal or previously claimed penalty as input authority.
Term resolution calls unchanged Recipes046A `resolve_feature_input`; no second matcher is copied.

The target must have a real041E positive event. Prior participating meals use exact integer
microsecond ages and `[t-D,t)`, with the complete interval and target contained in both the captured
eligibility window and **canonical graph.horizon**; the target is strictly before each end.
No clamp, float, truncated interval or borrowed horizon. The policy cutoff is the minimum queried
member041A clock plus actually consumed queried-dimension046A clocks for target/lookback cells.
Other members/dimensions/unconsumed future meals do not tighten that cutoff. All three policy
observed times must be no later than it, rather than merely before outer capture completion.

Per-meal exact-term resolution is existential: any PRESENT cell proves exactly one occurrence,
even with unresolved sibling batches; all positive supports and all diagnostics stay attached.
All required cells REVIEWED_ABSENT prove finite queried-term absence; otherwise the meal remains
UNRESOLVED. Different versions/batches/allocation/MAIN_PROTEIN slot cardinality never adds events.
The original owner reasons remain available in diagnostics and term resolution. In particular,
frozen046A may resolve an uncaptured term as TERM_NOT_CAPTURED while its discovery says NO_SOURCE;
041F retains both rather than substituting an absence or overriding owner reason precedence.

Decay covers exactly(0,D], lower-exclusive/upper-inclusive, with authored contiguous ordinals,
non-increasing exact rational retention and no interpolation. Zero-retention witnesses stay.
Each known contribution is explicit unit penalty × retention, with integer products/sums/GCD only.

| Actual occurrence set | Penalty availability |
| --- | --- |
| Any unresolved potential prior occurrence | UNAVAILABLE / UNRESOLVED_TERM_OCCURRENCES, even in a zero band; known per-occurrence contributions retained, no subtotal/lower-bound/total |
| Fully resolved and no witnesses | UNAVAILABLE / NO_MATCH_IN_SELECTED_PROPOSAL, no numeric zero; NO_ELIGIBLE_PRIOR_MEALS remains distinct from finite reviewed absence |
| Fully resolved and nonempty trace | AVAILABLE exact sum, including AVAILABLE0/1 for explicitly zero retention with nonempty contributions |

## Determinism, compatibility and limits

Frozen041E preview fingerprint remains full audit/capture identity; its queried-dimension
evidence-cut digest is retained unchanged. Neither authenticates database origin, proves liveness,
authorizes activation nor acts as a PRECOMMIT token. An internally coherent offline capture is
replayable after replacement; consistency alone does not prove that it came from the database.
METHOD/FLAVOR keep Recipes-only source dependencies. MAIN_PROTEIN keeps relevant Recipes+Catalog
association dependencies; a fresh stale support remains unresolved. Full mixed-source audit
identity may change while METHOD/FLAVOR dimension cuts and numerical interpretations stay equal.

Declared unordered sets canonicalize by typed keys and reject duplicate identities; semantic band
ordinals and source lineage order are preserved. Constructed/copied/rehashed cached results still
fail independent recomputation. Equivalent rational spellings serialize identically.

`feature_repeat_compatibility.json` pins the256 old exported definition structures, old frozen
algorithm ASTs and all13 released migrations at the canonical base. The export is additive:
**276 definitions =256 retained +20 new**. No migration, **Alembic0013 /71 domain tables**.
The existing export bundle ID `urn:menuto:domain:foundation:20` is also retained; new wire
aggregates carry their own explicit feature v1 versions. No old compatibility test was weakened.
No frozen040A/B,041A/B/C/D/E or046A shape, algorithm, hash or recipe policy is widened/genericized.
Frozen041E attached feature_cooldown/feature_decay/repeat_penalty remain UNAVAILABLE; only041F's
new outer contracts describe the scoped feature interpretation.

All results retain:

```text
coverage = ONE_SELECTED_PROPOSAL_EXACT_FEATURE_TERM_ONLY
source_kind = PROPOSAL_PREVIEW
interpretation_mode = AS_OF_CAPTURE
accepted_schedule / confirmed_exposure / consumption_history = UNAVAILABLE
durable_history / cross_horizon_history / global_repeat_penalty = UNAVAILABLE
novelty / taste_fit = UNAVAILABLE
member_behavior_profile = NOT_MODIFIED
cross_dimension_aggregation = NOT_PERFORMED
planner_ready = False
activation_ready = False
```

No cross-term/dimension/member/candidate or recipe+feature aggregation, normalization, cap, mean,
max, portion/participant division, learned evidence, TasteFit, prior/shrinkage, inferred preference
or planner weight.040C design NOT READY/NOT AUTHORIZED,040B prior/shrinkage UNAVAILABLE,
024/020B/021 BLOCKED, Execution NOT STARTED, PRECOMMIT FAIL-CLOSED. No next milestone authorized.

## Approved44-case acceptance mapping

`U` = `apps/backend/tests/test_feature_repeat.py` (test names start with the listed case number).
`PG` = `apps/backend/tests/test_postgres_feature_repeat.py`, real PostgreSQL18.4 transactions.
Existing785 PG tests remain untouched; mocks do not replace concurrency/frontier evidence.
Interleaving hooks only schedule real concurrent owner transactions between member/classification
reads; they call the real original capture implementation and never return fabricated DB results.

| Approved case | Actual test/evidence |
| --- | --- |
|1 distinct dimension policies | U case01, all3 dimensions with deliberately distinct explicit rational units |
|2 missing/mismatched policies | U case02, every stage; missing/dimension/term/recipe/list inputs |
|3 multi-batch/version/allocations | U case03 all3 dimensions, two RecipeVersions in one meal; PG cases03_36_41 |
|4 multiple prior meals | U case04, exact retained-occurrence sum |
|5 equal target/future timestamps | U case05, strictly prior only |
|6 start/ageD/age0/microseconds | U case06, exact integer distances |
|7 capture/horizon containment, exclusive end | U case07, explicit LOOKBACK_NOT_CAPTURED / TARGET_OUTSIDE_CAPTURE |
|8 huge duration/underflow/overflow | U case08, strict duration and representability failures |
|9 foreign identities | U case09, household/member/plan/proposal/hash/meal; existing real-PG access gates retained |
|10 nonpositive/wrong target | U case10, reviewed absence/no-source/retraction/random term/wrong dimension |
|11 complete finite absence | U case11, unavailable empty penalty with retained reviewed absence |
|12 outside universe/not captured | U case12, exact frozen resolver reasons retained |
|13 ASSIGNED/PARTIAL | U case13, positive proof and unresolved unlisted term distinguished |
|14 separate unknown meal | U case14, known witnesses retained but no aggregate amount |
|15 positive + unknown sibling | U case15, exactly one decidable occurrence with all cells |
|16 all cells absent | U case16, scoped no-match, no never-exposed conclusion |
|17 no eligible prior meals | U case17, NO_ELIGIBLE_PRIOR_MEALS / unavailable no-match |
|18 missing/duplicate/extra/forged cells | U case18, full041E primitive/result reconstruction |
|19 source/retraction/no-scope/stale reasons | U cases19/21; PG cases37_38 association fresh stale; owner NO_SOURCE diagnostic preserved alongside TERM_NOT_CAPTURED |
|20 same code/new ID | U case20, no alias reconciliation or inference |
|21 path/tier/rule/delta | U case21, all3 dimensions; METHOD invariant, FLAVOR/MAIN_PROTEIN exact path |
|22 multiple MAIN_PROTEIN support slots | U case22, one occurrence, two reviewed slots |
|23 invalid decay bands | U case23, gaps/overlaps/ordinals/reordering/increase/coverage |
|24 exact band boundaries | U case24, exact edge assignment and zero entries retained |
|25 rational validation | U case25, bool/float/nonfinite/string/negative/zero denominator and equivalent GCD forms |
|26 explicit zero retention | U case26, nonempty AVAILABLE0/1 |
|27 empty/unknown/zero distinction | U cases11/17/26/27_28 |
|28 unknown zero-band occurrence | U cases27_28, still unavailable; no fabricated decay entry |
|29 large exact arithmetic | U case29,150-digit integer product/sum, no cap/probability bound |
|30 explicit positive unit/operator | U case30, no zero/default or alternate mean/max/cap/normalization/unit |
|31 minimum consumed-child cutoff | U case31 across all stages/member-or-classification clocks, other member/future child excluded; PG cases31_39 excludes unrelated dimensions |
|32 scheduled time/UTC offsets | U case32, equal canonical source identity and exact ages |
|33 policy identity changes | U case33, derived fingerprint changes while source fingerprint stays equal |
|34 unordered permutations | U case34, equal canonical bytes/fingerprints, bands never silently reordered |
|35 forged/rehashed nested results | U case35 wire/copy/construct and next-stage recursive rejection |
|36 retries/overlap | U case36, single-source-only input; PG cases03_36_41 exact replay |
|37 concurrent proposal replacement | PG cases37_38 proposal, RR and SERIALIZABLE, owner write between actual source reads, old replay/fresh rebind |
|38 concurrent classification/association | PG cases37_38 classification and association, both isolations, old coherent/fresh changed or stale |
|39 unrelated Catalog source | PG cases31_39, METHOD/FLAVOR unchanged cuts and amounts, MAIN stale, full audit may change |
|40 unauthorized evidence/source | U cases40_43 closed ingress and fixed boundaries |
|41 zero IO/write | U case41 file/network traps and import negatives; PG cases03_36_41 SQL trap and persisted-row counts unchanged |
|42 frozen compatibility/schema | U case42 pins256 definitions/algorithms/0001–0013; PG cases03_36_41 checks0013 /71; existing drift/direct SQL/migration suites retained |
|43 no cross-scope total | U cases40_43 closed fields and operation; one query/policy coordinate only |
|44 hashes do not grant authority | U cases40_43_44/case44, deterministic offline replay and fixed non-authority literals |

## Verification receipts

Local final verification on2026-10-26:

| Gate | Actual result |
| --- | --- |
| Full Python suite with PostgreSQL18.4 | **2237 passed**,0 failure/error/skip,349.63s; one existing Starlette/httpx deprecation warning |
| Previous regression identities | **2015/2015 retained**,0 removed; compared exact JUnit classname/name identities with canonical design-base receipt |
| Additive tests | **222 =209 pure +13 real-PG**; full44-case mapping above |
| PostgreSQL-real total | **798 =785 retained +13 new**, all included/passed |
| Frozen compatibility |165 pinned prior algorithm definitions,256 old exported structures and all13 migration files unchanged; existing frozen tests untouched |
| Schema/export | **0013 /71 tables;276 definitions =256 old +20 new**; foundation:20 bundle ID retained; no migration |
| Ruff / architecture / imports | PASS;30 invariants,11 ADRs,50 linked tasks,16 contexts |
| OpenAPI/domain exports / synthetic fixtures | PASS; HTTP snapshot/client unchanged,22 fixtures verified |
| Synthetic benchmark | **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client/typecheck/web build | PASS; **10/10** client tests |
| Diff scope / whitespace |20 explicit files; no persistence/HTTP/migration/existing-test change; PASS |

Exact implementation PR/post-merge CI receipts are recorded in the PR delivery receipt.
Commands follow `.github/workflows/ci.yml`; local full test run uses loopback PostgreSQL18.4,
`.venv/Scripts/python -m pytest --basetemp=.local/041f-full-final --junitxml=.local/041f-full-final.xml`.
Ignored `.local/041f-*` logs, manifests and XML retain local receipts; they are not committed data.

Implementation head, PR head, merge SHA and exact PR/post-merge CI runs are published in the
implementation PR's delivery receipt once GitHub finishes them; this file does not predict a
self-referential commit hash or claim a future CI result.

## Changed files

```text
README.md
apps/backend/app/modules/learning/README.md
apps/backend/app/modules/learning/contracts.py
apps/backend/app/modules/learning/feature_repeat.py
apps/backend/app/modules/learning/public.py
apps/backend/tests/feature_repeat_compatibility.json
apps/backend/tests/feature_repeat_fixtures.py
apps/backend/tests/test_feature_repeat.py
apps/backend/tests/test_postgres_feature_repeat.py
docs/product/BACKLOG.md
docs/product/FOUNDATION_STATUS.md
docs/product/GLOSSARY.md
docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md
docs/product/INVARIANT_COVERAGE.md
docs/product/MTR_041F_FEATURE_REPEAT_POLICY_DESIGN.md
docs/product/MTR_041F_FEATURE_REPEAT_POLICY_EVIDENCE.md
docs/product/POST_MTR_041E_DEPENDENCY_REVIEW.md
packages/contracts/domain.schema.json
tools/check_import_boundaries.py
tools/export_domain_contracts.py
```

**READY FOR MTR-041F ARCHITECTURE/FREEZE REVIEW** — implementation only, NOT FROZEN.
