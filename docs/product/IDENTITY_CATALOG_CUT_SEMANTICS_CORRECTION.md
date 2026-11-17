# Identity catalog-cut semantics — targeted architectural correction

**DOCS ONLY / INDEPENDENT ARCHITECTURE AND SECURITY REVIEW PENDING / IMPLEMENTATION PAUSED**

## Authorization, exact baseline and preserved evidence

Owner decision: [6918157643](https://github.com/thedusk4203/Menuto/pull/147#issuecomment-6918157643).
GitHub main was re-fetched at **120d28f62b66720e8631b64e0b2a50cdc57e6c42**, tree
**8cbab048b2ecea6977bca61367a6e0a695dd9109**. This new docs-only branch starts there.
The earlier main push43597887745 is the4,611-test baseline, not Identity implementation acceptance.

The complete [historical blocker report](IDENTITY_CATALOG_CUT_FRESHNESS_IMPLEMENTATION_BLOCKER.md)
is published unchanged from the isolated implementation worktree. Its requirement for an additional
freshness mechanism and its blocked disposition are historical evidence; the selected semantics below
are the owner-authorized proposed clarification, pending independent review. Neither record authorizes
resuming implementation or editing the two failing tests.

[Reproduction source, raw observations, SQLSTATEs and artifact inventory](IDENTITY_CATALOG_CUT_DIAGNOSTIC_EVIDENCE.md)
are published with this correction. The scope/certainty distinctions in that evidence are mandatory.

## Selected bounded V1 semantics

| Concept | Required meaning | Forbidden interpretation |
|---|---|---|
| Snapshot consistency | One actual clean caller-owned read-only RR/SERIALIZABLE transaction retains complete coherent source evidence as of its initial MVCC cut | Several sessions/cuts silently merged; favorable-row or accepted-prefix capture |
| Observed mismatch | Actually unequal DB/login/OID/ACL/role safety observations fail the whole capture; no usable partial source | Choosing the favorable observation; ignoring a real contradiction |
| Unobserved concurrent mutation | A commit after snapshot establishment need not appear in either MVCC catalog read; a complete faithful earlier cut may remain self-consistent | Equal reads/hashes proving no concurrent commit, or SERIALIZABLE proving current-at-return rights |
| Current authorization | A new trusted operation needs a new actual authenticated transaction/capture and fresh independent checking | Retained source/report, CONSISTENT, timestamp, hash or prior inspection used as a bearer capability |

`AVAILABLE_AT_RETAINED_CUT / CONSISTENT` means historical retained evidence only. Permanent
`TEST_ONLY / UNVERIFIED_TRANSPORT / NOT_ADMITTED / planner_ready=False / activation_ready=False`
containment is unchanged. V1 adds no numerical consumer, admission lease or full ResolvedPlanPolicy.

This correction does **not** require separate fresh sessions, locks, epoch tokens, grants or runtime
changes. A new trusted operation may use a new transaction on an appropriately configured authenticated
connection; no extra observer connection is added to the V1 capture. Source identity, complete histories,
current source-authority rules at the selected cut and all existing parsing/resource/privacy rules remain.

[PostgreSQL18 isolation semantics](https://www.postgresql.org/docs/18/transaction-iso.html#XACT-REPEATABLE-READ)
explain why repeating a catalog SELECT in the same snapshot cannot guarantee observing later commits.
[pg_parameter_acl](https://www.postgresql.org/docs/18/catalog-pg-parameter-acl.html) is cluster-wide;
changing the writer database does not make its mutation database-local.

## Exact expectation distinctions

1. **GRANT after an established cut:** the old complete catalog may show no extra actor ACL at both
   boundaries, while a separate new transaction sees the committed extra privilege. A faithful old
   non-admitting result is not rejected merely because wall time advanced. New capture after the
   unsafe grant must reject42501. Any actually observed contradiction still fails whole-cut.
2. **REVOKE after an established cut:** the old cut can retain the earlier grant. If that earlier
   privilege made the requester unsafe, capture must deny it; do not fabricate AVAILABLE or a
   faithful unavailable source where the design permits only a generic failure. Subsequent removal
   of an unsafe SQL privilege cannot repair the old observation or renew Identity authority. A
   benign other-grantee revocation may leave an otherwise valid historical source consistent.
3. **Identity source revocation:** a root/issuer/binding/operation revoke visible at a fresh cut still
   disables that authority. Earlier retained evidence stays historical; it cannot be re-used for new work.
4. **Observed catalog/OID/ACL disagreement:** producer must return whole-capture non-success/null
   payload; independent reconstruction rejects contradictory primitives. No row selection, partial
   source, cached favorable report or matching fingerprint may override the mismatch.
5. **Omission/substitution/forgery:** reject contradictions against complete retained boundaries,
   pinned routines, role closure and authority history, including fully rehashed favorable labels.
   A coordinated internally coherent replacement with no remaining retained contradiction is not
   cryptographically authenticated offline. ITR061's existing UNVERIFIED_TRANSPORT limit remains;
   do not claim that an offline checker can discover missing live facts it was never given.

In particular, the two historical inherited-edge failures are not automatically resolved by the
MVCC clarification. A proposed adversary must carry the complete native edge that makes an
other-grantee ACL effective for the actor before expecting unsafe-right reconstruction. This PR
changes no implementation fixture, test expectation or checker behavior to obtain a passing result.

## Narrow document and acceptance impact

| Document / obligation | Change | Retained boundary |
|---|---|---|
| Bounded design section6 | Four meanings, cut timing and no-current-authority limitation | One actual reader transaction; no bearer/consumer admission |
| Contracts15/16 and section2.1 | Describe frame/source/cut observations precisely | Exactly19 names and existing fields/types/literals; no new fields |
| ITR018 / P5 | Native oracle compared at the identified observation/cut; separate before-cut and invisible-after-cut writes | All direct/PUBLIC/inherited/grant-option negatives, no fabricated owner |
| ITR040 | Separate unchanged, mutation-before-cut, invisible-after-cut and observed-mismatch expectations | All48 real-PG groups; same3 mapped parameter IDs, more explicit assertions |
| ITR041 | Fresh denial versus historical replay; no cached-authority reuse | Actual new authenticated transaction, no admission |
| ITR055 | Reject contradictory omissions/forgeries; distinguish total coherent replacement | Independent checker and ITR061 transport limit |
| ITR066 | Actual observed descriptor mismatch, including cross-database writes, versus invisible commit control | Whole error, no partial positive |
| Acceptance/security preflight | Harmonize the same expectations and oracle timing |96 obligation IDs,48PG/32pure/16static, original names and mapping |

The preflight's143 anticipated items remain a historical proposal, not a measured count. Nothing in
this correction authorizes applying its revised expectations to the paused implementation before
independent PASS and separate owner resumption authorization.

## Stronger freshness alternatives — evaluated, not implemented

| Alternative | Benefit and remaining race | Native/cross-database coverage | Sessions, privilege and compatibility impact |
|---|---|---|---|
| Separate fresh post-cut observation | Can observe a committed change missed by the original cut; writes can still occur after observation/before return or use, and ABA may restore an equal view | Must enumerate relevant native role/object/parameter facts through a demonstrably fresh cut; same-cluster writes from every database matter | New trusted observation/session or transaction and independently bound evidence; cannot silently splice it into the existing single-cut frame; separate contract/security approval |
| Catalog/privilege locking | A proven fence could block conflicting writers until the protected operation ends; acquiring it after snapshot establishment does not repair stale visibility | Must prove conflict with actual PostgreSQL native GRANT/REVOKE, role/ownership/ACL writers and shared catalogs across databases; an application advisory lock alone has no such coverage | Catalog lock permissions, read-only constraints, ordering/deadlock/timeout behavior and native-writer effects need independent review; no broad privilege or system-catalog lock is granted here |
| Authoritative epoch / writer coordination | A trustworthy monotonically changing generation could expose mutation/ABA; checking an epoch without a use-time fence still leaves a race | Every relevant native catalog writer, including privileged tools and second-database sessions, must participate or be blocked; an Identity-only epoch cannot cover arbitrary native GRANT/REVOKE | New durable authority/coordination and lifecycle, trusted writer enforcement and checker inputs; likely source/contract/privilege impact requiring separate approved design |

[PostgreSQL LOCK documentation](https://www.postgresql.org/docs/18/sql-lock.html) explains that a
lock acquired after the first repeatable snapshot does not make earlier reads current, and lock
modes have their own permissions. No alternative is claimed sufficient without a concrete coverage
and race proof. WAL-LSN, matching hashes or check-time timestamps are not substituted as freshness oracles.

If the product requires **every** concurrent catalog mutation to reject a capture, the exact missing
prerequisite is an independently approved **native-catalog writer visibility/fencing authority** that
covers the shared cluster, pins observations/use-time ordering and states residual races. Separate
owner authorization must specify sessions/locks/grants/objects/persistence, contract evidence and
independent validation obligations. That stronger requirement is not satisfied or authorized by V1.

## Evidence accounting and compatibility

- Historical expanded Identity native run: **84 passed /2 failed /0 skipped out of86**. No full
  implementation regression, exact-head Identity CI or ITR acceptance is inferred.
- New diagnostic: **9 native PostgreSQL18.4 cases +7 unchanged-draft offline checker cases**, all
  completed without failure/skip. These are separately scoped design probes, not16 new accepted ITRs.
  No Identity0018 migration/functions were installed by the diagnostic; the fresh42501 guard and
  observed40001 predicate are explicitly test-local native DO statements, not production Identity entries.
- The original actual protected-entry reproduction remains evidence of AVAILABLE_AT_RETAINED_CUT,
  offline CONSISTENT and the subsequent42501 rejection; it is published as historical author-run
  evidence, not independently re-executed by this docs-only PR.
- Docs exact-head CI must run the unchanged4,611-test canonical baseline and all repository guards.
  Its result does not accept the unpublished556-export draft or its two failed tests.
-537 existing exports/bodies,515legacy/503historical hashes,53frozen files,59PIV pins and schema0017/108
  remain unchanged. No0018 in this branch, no persistence/SQL/role/grant/runtime/tooling/test change.
- The original19local files and the entire paused implementation's61tracked/untracked changed-file
  inventory are SHA-256/status/HEAD checked before and after. Neither worktree is committed or published.

## Review and stop

**ITR CATALOG CUT SEMANTICS CORRECTION — READY FOR INDEPENDENT ARCHITECTURE/SECURITY REVIEW**

Implementation remains paused. Independent correction PASS, separate owner merge authorization,
verified merge/main pushCI and a separate instruction reconciling the paused implementation with the
approved correction are required before code/test resumption. No self-approval, merge or freeze.

FullMTR-006/007/008 INCOMPLETE;issues5/6/7OPEN;productionNutrition/clinical gateCLOSED;
planner_ready=False;activation_ready=False;ExecutionNOTSTARTED;PRECOMMITFAIL-CLOSED.
