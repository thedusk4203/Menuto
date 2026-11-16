# Identity catalog-cut freshness blocker — local implementation evidence

Status: **BLOCKED / CLASSIFICATION ACCEPTANCE INCOMPLETE / IMPLEMENTATION NOT SUBMITTED / PRODUCTION GATE CLOSED**.

This is measured local diagnostic evidence, not implementation acceptance, a freeze or a change to approved architecture. GitHub main was fetched again and is still `120d28f62b66720e8631b64e0b2a50cdc57e6c42`.

Owner authorization: [conditional routine classification correction](https://github.com/thedusk4203/Menuto/pull/147#issuecomment-6906886726).

## Work preserved and classification progress

The isolated `codex/identity-source-implementation` draft retains the 19 approved additive contracts, six private tables/five protected entries/twelve private helpers and exactly the approved native TLS grants. No legacy PUBLIC EXECUTE privilege or migration0001–0017 was changed. No commit, push, PR, merge, freeze or production deployment occurred.

`IDENTITY_LEGACY_ROUTINE_MANIFEST.json` records individual semantic preimages, signatures, owner rules, ACL/body/dependency fingerprints and conditional execution-context reasoning. The SQL classifier binds installed routine OIDs and exact preimages. The independent checker owns its own literal pins and reconstructs effective privileges; it does not import the producer classifier. These are draft checks, not a blanket approval of68 functions or a declaration that classification acceptance is complete.

A prior focused native run executed16 cases successfully (issuer/capture, trigger non-callability, denied protected access, routine substitution/body/owner/signature/ACL/dependency and temp-object attacks). Its result is not added to the later run's totals.

## Reproduced failure: a committed catalog mutation between capture boundaries

The dedicated diagnostic uses real PostgreSQL18.4, authenticated SCRAM/verify-full connections and the actual protected capture entry. It does not replace source functions or use a mocked catalog.

1. Provision a TEST_ONLY root, issuer, binding and exact operation grant; normal capture succeeds.
2. In a separate disposable administrator transaction, lock `public.memberships` in ACCESS EXCLUSIVE mode solely as a test synchronization barrier.
3. Start the ordinary requester capture in REPEATABLE READ / READ ONLY.
4. Confirm through `pg_locks` that this exact backend is waiting on the membership relation, after its first catalog observation and before its final observation.
5. A second administrator connection commits `GRANT ALTER SYSTEM ON PARAMETER <random TEST_ONLY custom name> TO <this requester>`; verify native `has_parameter_privilege` becomes true.
6. Release the barrier and let the unchanged protected capture complete. No actual ALTER SYSTEM is executed.
7. Independently check its retained result, then try a new capture.

Measured result:

```json
{
  "mutation": "committed GRANT ALTER SYSTEM between catalog boundaries",
  "result": "AVAILABLE_AT_RETAINED_CUT",
  "reason": "SOURCE_AVAILABLE",
  "sqlstate": null,
  "start_contains_parameter": false,
  "end_contains_parameter": false,
  "independent_decision": "CONSISTENT",
  "next_fresh_capture": "42501"
}
```

The mandatory expectation was whole-capture failure. The diagnostic assertion therefore **FAILS**. The parameter grant is revoked in `finally`; all disposable clusters have been stopped.

This is not evidence that the independent checker should invent live catalog truth. The two retained inventories faithfully describe the earlier snapshot. `CONSISTENT` remains a retained self-consistency result, `UNVERIFIED_TRANSPORT` remains explicit, and numerical use remains `NOT_ADMITTED`. Nevertheless, this does not satisfy the newly required guarantee that any committed privilege mutation between the two boundaries rejects the whole capture.

## Why the current repeated-read mechanism is insufficient

Both SQL catalog enumerations use the same repeatable snapshot. A newly committed parameter row can be absent from both. Repeating the query or comparing the two retained hashes cannot expose that absent row. A new transaction observes the new privilege and rejects42501, as the control above proves.

This agrees with [PostgreSQL18 Repeatable Read semantics](https://www.postgresql.org/docs/18/transaction-iso.html#XACT-REPEATABLE-READ). [pg_parameter_acl](https://www.postgresql.org/docs/18/catalog-pg-parameter-acl.html) is cluster-wide; an absent row is not an owner or invented ACL. This report does not claim that every native catalog/cache accessor uses an identical visibility mechanism, or that an independent future design cannot solve freshness.

**Required architecture decision:** establish how the strict concurrent catalog-mutation rejection guarantee is to be provided alongside one coherent read-only source snapshot. The currently approved repeated-catalog-read mechanism has a concrete counterexample. A separate live observation, mutation-generation authority or locking/permission strategy has not been approved or implemented here. Do not silently weaken the guarantee, add a connection/privilege/object, or label an old-cut equality check as live freshness.

## Actual test state — not full acceptance

The second expanded native Identity module run executed86 tests: **84 passed /2 failed /0 skipped**,425.224seconds. Both remaining failures are:

- `test_itr018_privilege_graph_closure[p4_inherit_true_set]`
- `test_itr018_privilege_graph_closure[p4_inherit_true_alter_system]`

The native unsafe capture rejects as expected; the later handcrafted retained-forgery assertion expected INCONSISTENT but observed CONSISTENT. Its injected parameter fact does not yet supply the newly granted inherited-role edge from the live catalog. This is an additional unresolved adversarial-test construction/checking issue, not authority to accept a favorable classifier label. It must be corrected and rerun after the architecture blocker is settled; no pass is claimed.

The dedicated cut diagnostic separately executed1 failing test. It is not included in the86-test total. No final full-regression or exact-head CI pass exists for this uncommitted draft. ITR001–ITR096 and all48PG obligation groups are **not accepted as completed**.

## Compatibility and local preservation

Read-only comparison after the diagnostic confirms:

- All537 existing exported definition bodies unchanged; exact19-name additive manifest yields556 in the generated draft schema.
-515legacy and503historical definition hashes unchanged.
-53frozen files and59PIV pinned files unchanged.
- SHA-256 of all19 original modified/untracked files remains exactly equal to the protected inventory.
- Canonical main remains0017/108. The authorized local0018/114 draft exists only in the isolated worktree and disposable test installations; it is not merged/deployed.
- No additional migration/grant/role/SQL entry was introduced to work around the cut failure.

Machine-readable local evidence and artifact SHA-256 values: `.local/identity-catalog-cut-blocker.json`. Compatibility proof: `.local/identity-catalog-cut-compatibility.json`. Reproducer: `.local/identity_cut_probe.py`, native runner `.local/identity-cut-probe-1.py`, JUnit `.local/identity-cut-probe-1/results.xml`. Expanded run: `.local/identity-itr-all-2/results.xml`.

## Stop disposition

**IDENTITY IMPLEMENTATION BLOCKED / CONCURRENT CATALOG-MUTATION GUARANTEE UNPROVEN / NO PR SUBMITTED / PRODUCTION GATE CLOSED**.

No further implementation, new trust machinery or permissions are inferred. FullMTR-006/007/008 remain incomplete;issues5/6/7open;planner_ready=False;activation_ready=False;ExecutionNOTSTARTED;PRECOMMITFAIL-CLOSED. Original local work is preserved. This report does not request or authorize merge/freeze/activation.
