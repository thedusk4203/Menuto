# MTR-041E — Proposal-local Reviewed Feature Exposure Sources

Status: **IMPLEMENTED; NOT FROZEN — awaiting architecture/freeze review**.

Authorized implementation baseline: `c609d3bf25768bc571a33c8c9ca1c21c7cbeece3` (PR #86).
The user approved the name and [source integration design](POST_MTR_046A_DEPENDENCY_REVIEW.md),
with two additional freeze criteria: machine-readable scoped empty-preview semantics and fully
recomputed diagnostic evidence-cut digests. No design correction PR was required.
Verification date:2026-10-25, Asia/Saigon. Exact implementation/test/export commit:
**`1e3ddb9a1b084534abe67958a0b9e5b37e398652`**. The following documentation commit does
not change that runtime. Remote PR/exact-merge CI is reported in the delivery receipt after it
runs, never inferred from local success.

## Actual implementation and ownership

Learning owns11 additive immutable/extra-forbid definitions: feature request, two closed frontier
shapes, source snapshot, source key, assignment reference, support witness, exposure fact,
coverage diagnostic, evidence-cut diagnostic and preview result. Existing226 definitions are
unchanged. The domain export adds these definitions without changing existing wire versions or
the aggregate bundle identifier. No HTTP endpoint or UI is added; OpenAPI stays unchanged.

Planning's new `capture_feature_exposure_preview()` coordinates the two frozen capture adapters
inside the caller's one clean read-only RR/SERIALIZABLE transaction. It captures041A once per
selected member, flattens all eligible individual allocation supports and captures046A once per
eligible batch/requested singleton dimension. It neither commits nor opens another connection.
The exact source manifest and shared proposal/member/recipe/policy/frontier facts are verified.
Each frozen child's own capture clock is retained. Completion bounds the child clocks.

Learning's pure `preview_feature_exposure()` recursively reparses attached primitives, validates
coherence and derives all events/diagnostics/digests. No database/network/store/Execution/
Preferences runtime, attribution or utility is called. Cross-domain imports are contracts only.
The existing frozen discovery contract recomputes classification; Learning adds no second matcher.

The new event key is household/member/plan/meal/dimension/term, with an explicit v1 identity tag.
Proposal, recipe/version, allocation, batch, review and support cardinality are evidence, not extra
occurrences. Every positive witness retains participant, frozen recipe-event key, allocation,
batch, recipe/version, source key and hashes, applicability and actual (review_id, term_id).
Full nested source proofs retain finite covered universe, lineage, provenance and Catalog support.
No generic assignment UUID, classification by names/mass, term-code version reconciliation or
bare unsupported context reference is introduced.

METHOD remains RecipeVersion cooking-context invariant. FLAVOR/MAIN_PROTEIN use the exact bound
path; MAIN_PROTEIN additionally requires contextual slot review and pinned ingredient association.
Catalog-owned immutable vocabulary terms are retained for all dimensions, but Catalog **association
generation/support** is present only for MAIN_PROTEIN. All existing quantity bases and AP/EP/cooked/
COUNT ownership remain unchanged; no conversion or serving-count inference is added.

## Coverage, failures and identity

Positive ASSIGNED terms produce events; PARTIAL remains partial. REVIEWED_NONE remains a finite
reviewed-universe statement, not global absence. UNRESOLVED keeps its exact reason. A meal can
retain positive evidence alongside unresolved support without a global completeness boolean.

Even events=()/diagnostics=() carries explicit literals:

```text
coverage = SELECTED_PROPOSAL_FEATURE_PREVIEW_ONLY
absence_semantics = NOT_EVIDENCE_OF_NEVER_EXPOSED_OR_GLOBAL_FEATURE_ABSENCE
activation_ready = False
```

Missing exact binding, required unreviewed recipe, corrupt source or independent grounding failure
fails the entire requested capture. A valid046A UNRESOLVED result remains data. There is no silent
METHOD-only downgrade; the caller must issue an explicit new request. Frozen046A still validates
the whole bound proposal, without trimming unsupported batches outside the exposure window.

Three identities stay distinct: semantic event key, exact timestamp-sensitive snapshot/result
fingerprint and per-dimension diagnostic evidence-cut digest. The last excludes capture audit
clocks and other dimension branches only, preserving source observed/recorded times, policy,
proposal/member/recipe identities, reviewed primitives and applicable frontiers. It is always
recomputed from the attached source during result validation; forged digest/cache is rejected.
Its authority literal is DIAGNOSTIC_ONLY_NOT_LIVENESS_OR_AUTHORIZATION. It is not a live-source
proof, validation receipt, PRECOMMIT token or substitute for a future authoritative frontier recheck.

Fresh capture replaces the entire selected preview. Old immutable captures replay; no cross-cut
merge API combines old/new proposal or review evidence. Explicitly unordered fact sets have typed
canonical ordering; source lineage and authored ordinal semantics retain their frozen encoding.
Equal timestamps create no artificial chronology. No generic recursive sequence sorting is used.

## Adversarial acceptance mapping

The28 approved cases are mapped to executed tests, not represented as28 new business capabilities:

| Approved cases | Implementation evidence |
| --- | --- |
|1–5 multi-batch/term/meal/member and absent participant | Pure multi-owner fixtures, two-term case and explicit participant removal; real-PG selected members share one batch/dimension capture. |
|6 METHOD vs exact path | Unit matrix tier/rule/delta ×METHOD/FLAVOR; MAIN_PROTEIN real source/pinned-support capture; frozen binding/discovery guards retained. |
|7–8 reviewed-none/unresolved | Dimension×coverage×positive matrix; positive and unmatched substitution paths coexist as separate diagnostics. |
|9–10 Catalog replacement / conditional identity | Real-PG combined singleton capture: old replay, fresh MAIN_PROTEIN STALE_ASSOCIATION, METHOD/FLAVOR cut digests unchanged. |
|11 RR proposal replacement | Actual concurrent proposal write; old RR cut coherent, stale fresh request rejected, explicit current request captures replacement. |
|12–13 duplicate support / multiple versions | Duplicate cached support rejected; same stable Recipe ID with two exact versions yields one feature event and two version-specific witnesses. |
|14–15 equal timestamps / permutation | Distinct same-time meals preserved; shuffled unordered sources/members/graph/terms preserve canonical bytes/output. |
|16 forged caches | Reparse constructed/copy inputs; forged digest/term/coverage/support/proposal/recipe/frontier fail; independently valid conflicting children fail aggregate coherence. |
|17–18 pure/no side effects | Engine query trap during replay; SQL capture limited to SELECT/SHOW; physical/preference/plan/source row counts unchanged; writable/dirty/READ COMMITTED rejected. |
|19–20 no inference / frozen compatibility | Unreviewed/no-source classifications rejected or unresolved; checked-in receipt pins all226 definitions, old function/class ASTs and0001–0013 migration contents. |
|21 whole-request failure | Real canonical legacy proposal has no binding: FLAVOR, MAIN_PROTEIN and mixed METHOD+FLAVOR fail; explicit METHOD retry succeeds. |
|22 conflicting cuts | Member/policy/recipe/proposal/frontier mismatches and valid child scope/term/recipe conflicts reject without trusting claimed frontier numbers. |
|23 batch reuse | Multi-meal/member pure fixture and real selected-member capture preserve per-event ownership with shared classification source. |
|24 empty window | Each dimension captures actual source frontier with no eligible sources, explicit scoped absence and no fabricated history. |
|25 clock differences | Different valid frozen child capture times change audit fingerprint, not evidence-cut digest or event identity. |
|26 classification replacement | Actual concurrent review replacement retains coherent old RR source, fresh reviewed-none result, unchanged old replay and no event union. |
|27 closed manifest/dimensions | Missing/extra/duplicate source, foreign ownership, caller term/weight/safety fields, unsupported/empty dimensions and nonpositive quantity fail. |
|28 whole-proposal grounding | Frozen046A whole-proposal grounding algorithm and contract ASTs are pinned unchanged; new coordinator passes the canonical full proposal through that capture, never a trimmed graph. No claim that malformed unsealable SQL can become canonical. |

Tests live in `test_feature_exposure.py`, `test_postgres_feature_exposure.py` and supporting
`feature_exposure_fixtures.py`; `feature_exposure_compatibility.json` is a checked-in baseline
compatibility receipt, not live authority. Existing test files are not weakened or deleted.
Initial focused failures were test-fixture issues (unordered canonical roundtrip, tuple updates,
global sequence/source agreement, detached ORM fixture identity and forbidden legacy downgrade).
Fixes corrected the new fixtures/expectations; database guards and frozen semantics were preserved.

## Verification ledger

| Gate | Actual local result |
| --- | --- |
| Full Python suite | **1860 passed**,0 failures/errors/skipped;180.09s; one existing FastAPI/Starlette httpx deprecation warning |
| PostgreSQL-real | **755 marked tests**, all executed/passed within full run; includes8 migration tests; new focused real-PG module separately **27/27** |
| Prior regressions | **1758/1758 identities retained**,0 missing, XML compared to reviewed baseline run |
| Additive tests | **102 =75 unit/adversarial +27 PostgreSQL-real** |
| Migration/drift | Existing real-PG empty up/down/up, populated lossless roundtrip, fail-closed lossy downgrade, schema/ORM parity and direct SQL guards remain green |
| Capture/concurrency | Read-only RR/SERIALIZABLE, real proposal/classification concurrent replacement, per-member ownership and conditional Catalog dependency PASS |
| Frozen compatibility | All226 old schema definitions and pinned old algorithm ASTs retained; **11 additive** definitions;0001–0013 migration contents unchanged |
| Ruff / architecture / imports | PASS;30 invariants,11 ADRs,50 linked tasks;16 registered contexts |
| OpenAPI / domain exports | PASS; OpenAPI unchanged; domain export237 definitions with old226 identical |
| Synthetic fixtures / benchmark |22 fixtures verified; **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client contract check / typecheck / tests | PASS, **10/10** |
| Web typecheck/build | PASS |
| Git diff whitespace | PASS |
| PR and exact post-merge CI | Exact head/merge SHAs and run links reported in final delivery after remote gates complete; no advance PASS claim |

Full command: `.venv/Scripts/python -m pytest --basetemp=.local/041e-full
--junitxml=.local/041e-full.xml` with MENUTO_TEST_POSTGRES_URL targeting loopback PostgreSQL18
and random isolated test databases. Marker collection independently confirms755 real-PG identities;
all1860 executed tests passed, so that subset had no skips. Local logs/XML remain under ignored
`.local/041e-*`; no production data is committed. Other gates match `.github/workflows/ci.yml`.
No migration is added. Schema remains **0013 /71 domain tables**; all0001–0013 immutable.

## Explicitly deferred / no completion claim

No feature cooldown, decay, RepeatPenalty policy/weight, novelty, TasteFit, MemberBehaviorProfile,
EvidenceStrength, priors/shrinkage, utility, shortlist/rank/portfolio/optimizer, accepted/confirmed/
consumed exposure, durable member history, cross-horizon bridge, family mapping, allergen/diet
classification, Execution, production permission/UI or PRECOMMIT authority is implemented.
No planned stock/reservation becomes physical movement. No preference is copied or inferred.

Full040/041/046 and026 remain incomplete;024/020B/021 BLOCKED; Execution NOT STARTED;
PRECOMMIT fail-closed; POSTFACT diagnostic. This slice does not self-freeze or authorize another
slice. Stop for architecture/freeze review.

**READY FOR MTR-041E ARCHITECTURE/FREEZE REVIEW**. Remote gate identities are included in delivery.
