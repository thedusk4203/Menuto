# Candidate × Member TasteFit Foundation — Freeze Receipt

Status: **CANDIDATE × MEMBER TASTEFIT FOUNDATION — FROZEN**.
Recorded on 2026-10-28 after the separately authorized exact-head merge and successful exact
post-merge push CI. This is a bounded foundation freeze, not planner activation or a new MTR suffix.

## Canonical identities and verification

| Receipt | Verified value |
| --- | --- |
| Repository | `thedusk4203/Menuto` |
| Approved design | [PR #115](https://github.com/thedusk4203/Menuto/pull/115), head `676ff2aca51cf4c4870c15d830a2f8e9048d9f42` |
| Design merge / implementation base | `89320203d1f64c274585cbcee0d5cef9045eacd1` |
| Implementation | [PR #116](https://github.com/thedusk4203/Menuto/pull/116), 26 reviewed files /3 commits |
| Reviewed implementation head | `152dbe8a365790956d2f7bac1b40a09b7dbd9134` |
| Formal implementation review | [6464492744](https://github.com/thedusk4203/Menuto/pull/116#issuecomment-6464492744), PASS / FREEZE CANDIDATE |
| Exact-head CI | [40654562525](https://github.com/thedusk4203/Menuto/actions/runs/40654562525), SUCCESS on the reviewed head |
| Actual implementation merge / verified main | `7ac0547b3df621fb19c614c27edaca268a901169` |
| Merged / reviewed tree | `3732449fd8fd19e68c873636c0fe851d3c6ffb14`, identical trees |
| Exact post-merge push CI | [40659094576](https://github.com/thedusk4203/Menuto/actions/runs/40659094576), event=push / exact merge SHA above; SUCCESS |
| Required jobs and repository guards | python/web SUCCESS; lint, architecture/import, OpenAPI/domain exports, fixtures, contracts/typecheck/build green |
| Full pytest | **3,396 passed /0 skips** =3,104 retained +292 additive |
| Acceptance | **TF01–TF132 covered**;188 pure +62 architecture/compatibility +42 real PostgreSQL cases |
| PostgreSQL obligations | **42 real PostgreSQL cases cover all35 required PG obligations**;1,143 total real PostgreSQL cases |
| Real SCRAM/TLS | **16/16 passed** |
| Benchmark / client | **22/22 /10/10 passed** |
| Exports | **384 =362 prior definitions unchanged +22 additive** |
| Schema | **0015 /85 domain tables**;86 with alembic_version; no migration0016 |
| Persistence | **ZERO NEW PERSISTENCE**; no TasteFit table/cache/materialized profile, production seed/default, coefficients or new policy authority |
| Canonical freeze decision | [Formal post-merge receipt](https://github.com/thedusk4203/Menuto/pull/116#issuecomment-6468012284) |

Immediately before merge the PR was OPEN /MERGEABLE /CLEAN at the exact authorized head,
with the same26 files and3 commits, exact-head CI SUCCESS and no unresolved review threads or
technical blockers. The formal review receipt records PASS; the quota-only Copilot comment is
not a technical finding. Merge used an exact-head guard; auto-merge was not enabled.

The actual merge commit was fetched after merge, independently matched to main, and checked for
the approved base/head parents. Its entire tree equals the reviewed head. No synthetic pre-merge
merge_commit_sha is used as canonical evidence. Main was re-fetched after the successful push run
and remained the verified implementation merge SHA. The run's logs, not a local or prior-head run,
provide the post-merge test/guard receipt.

Independent checks reconfirm384 exported definitions,85 registered domain tables, migration files
0001–0015 and all132 stable TF cases with35 PG obligations. Frozen retention checks pin128 existing
runtime/migration files and all362 prior export definitions. The real PostgreSQL TF129/TF132 test
checks85 domain tables plus Alembic, head0015, unchanged row counts/frontiers and SELECT/SHOW-only
capture statements; it verifies no TasteFit table or production/default rows were introduced.
This is repository/disposable-test evidence, not a claim to have queried a production deployment.

## Frozen scope and invariants

The [approved design](CANDIDATE_MEMBER_TASTEFIT_FOUNDATION_DESIGN.md) and
[implementation evidence /TF01–TF132 mapping](CANDIDATE_MEMBER_TASTEFIT_FOUNDATION_EVIDENCE.md)
retain the exact interface and acceptance boundary. No runtime, contract, test, migration or
existing frozen semantic change is made by this freeze/status synchronization.

- Planning owns the additive candidate/member join and conditional interpretation. Preferences
  owns member source capture/replay; narrow companion imports do not expose frozen private APIs.
- One exact canonical candidate, one household and one explicitly participating member, including
  SHARED subjects. Other participants/portions remain context, never subject replacement or weights.
- Canonical target proofs bind recipe/version/path and selected ingredients/reviewed positive
  features before policy filtering. MAIN_PROTEIN proves PROTEIN; it is not a sixth preference kind.
- Raw040B explicit, exact-target prior/shrinkage and040C one-hop views remain distinct. Retraction
  suppresses fit; direct precedence and authored categorical branch selection remain unchanged.
  Unavailable selected evidence never falls back; no sum/max/average/strongest/favorable-parent rule.
- One-hop inheritance uses mapped explicit only, never a blended/prior-only/inherited parent,
  recursion or multi-parent aggregation. Valid destination-context mismatch remains diagnostic.
- EvidenceStrength is ordinal lineage only, never probability/confidence, a multiplier, threshold
  or inherited strength. Direct dislike stays soft evidence; prior/inherited signs do not mint it.
- Required explicit versioned/body-pinned policy drives finite exact lookup. No production/current/
  default/shared policy selector, registry, publication authority, numeric defaults or coefficients.
  Available zero differs from absent/unresolved/reviewed-none/retracted/no-evidence states.
- Scoped fit retains full household/member/candidate/typed-target/policy identity. Numeric equality
  under the same descriptor grants no cross-target/member/candidate comparison, aggregation or utility.
- Owner capture uses clean authenticated read-only RR/SERIALIZABLE sessions with separate prior and
  hierarchy trust roots. Independent clocks/cuts remain explicit; common MVCC is NOT_CLAIMED.
- Pure replay/semantic validation recursively reparses/recomputes retained primitives and every
  selected/unselected child with zero I/O. Fingerprints cover complete retained sources; hashes,
  cached results and offline self-consistency grant no canonical origin or publication authority.
- Invalid required capture aborts the whole bundle. Authored resource budgets reject rather than
  truncate. No hidden learning/history/safety/procurement source substitutes for missing fit evidence.
- `planner_ready=False`; `activation_ready=False`; no aggregate fit, ranking, shared reducer,
  planner utility, hard-safety/feasibility authority, persistence or durable behavioral learning.

## Unchanged statuses and stop boundary

| Work | Status |
| --- | --- |
| MTR-040 /issue #41 | COMPLETE /CLOSED — COMPLETED; frozen semantics unchanged |
| MTR-039 | OPEN |
| Full MTR-041 /MTR-046 | PARTIAL /PARTIAL; frozen slices unchanged |
| MTR-024 /MTR-020B /MTR-021 | BLOCKED |
| Execution | NOT STARTED |
| PRECOMMIT | FAIL-CLOSED |
| Planner activation, ranking, shared-member reducer, learning loop | NOT AUTHORIZED |

The linked formal post-merge comment records the authorized freeze decision. This docs-only
synchronization persists that receipt and current status; earlier review-pending delivery wording
is historical and superseded only for this foundation's status. No parent issue is closed and no
next gate is selected, reviewed, designed, implemented or authorized. The documentation PR remains
OPEN for review; this authorization merges PR #116 only and does not authorize another PR merge.
