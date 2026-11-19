# Identity implementation — historical migration allowlist stop

**NATIVE SSLINFO CLASSIFICATION VERIFIED / BOTH LAYOUTS PASS / FULL ACCEPTANCE BLOCKED / NO IMPLEMENTATION PR / NOT MERGED / NOT FROZEN / PRODUCTION GATE CLOSED**

Canonical main remains68fcb688231460f1973077eb20140b8c5db440a2. The native classification exception
[#6966766271](https://github.com/thedusk4203/Menuto/pull/148#issuecomment-6966766271) was implemented
without changing19 contract shapes,68 legacy pins, old migrations or frozen source semantics.
223 focused Identity tests passed, including150actualPG executions and all96IDs/48mandatoryPGgroups.
Historical reference-prior112 and separate SCRAM/TLS16 passed. External guards, benchmark22/22,
client10/10 and web passed. These are component results, not full acceptance.

## Actual full regression result

The final full attempt (100-connection disposable harness) executed4573cases:
**4572passed /1failed /0errors /0skips**, stopping at the historical guard below. All223Identity
cases, including150actualPG executions, passed in this same run. From the4834-node collection,
261cases remain unexecuted. There is no completed full-suite PASS and no exact-head implementation CI.
The earlier20-connection setup error is separate historical evidence and was not counted as a pass.

Failure at `apps/backend/tests/test_target_affinity.py:515`, test:
`test_all_frozen_040a_041abcde_046a_definitions_and_migrations_retained`.

```text
Extra items in the left set:
'apps/backend/migrations/versions/0018_identity_principal_user_sources.py'
```

The guard first passed its frozen definition checks,237pinned schema definition hashes and13released
migration hashes. It then requires the exact migration filename set to equal0001–0013 plus the four
explicit additions0014–0017. The independently approved new0018 is therefore rejected by metadata.
An isolated rerun of that one test reproduced the same failure. No guard was changed or suppressed.

## Exact pending exception — proposal only

The file is not in the approved35 metadata package and remains byte-identical to its baseline:
`4196726aa225684fb294dbe4f7e1cd917f51180c44368c0f943a67be55e47f13`.
Owner authority is required before adding the single filename to this exact-set assertion.
No subset/inequality replacement, fixture rewrite, old hash change, test rename/skip/xfail or
migration modification is proposed.

```diff
--- a/apps/backend/tests/test_target_affinity.py
+++ b/apps/backend/tests/test_target_affinity.py
@@ -516,8 +516,9 @@
         "apps/backend/migrations/versions/0014_reviewed_reference_prior_source.py",
         "apps/backend/migrations/versions/0015_reviewed_hierarchy_source.py",
         "apps/backend/migrations/versions/0016_nutrition_root_sources.py",
         "apps/backend/migrations/versions/0017_nutrition_synthesis_sources.py",
+        "apps/backend/migrations/versions/0018_identity_principal_user_sources.py",
     }
 
 
 @pytest.mark.parametrize(

```

Proposed postimage SHA256:
`13fb1dee71b83ff6f3789133fe8481e3738458e9a87a9f05a718b9041f65746f`.
The full [machine-readable proposal](IDENTITY_MIGRATION_ALLOWLIST_EXCEPTION_PROPOSAL.json) is
**NOT AUTHORIZED / NOT APPLIED**.

If owner approves this one-file/one-block exception, the new Identity-owned compatibility helper
and its adversarial tests also need a separately pinned exact inverse/preimage proof for this
exception. Preserve the original approved35-file package/hash, all174baseline preimages and all
historical fixtures unchanged; do not silently add an unapproved path or relax exact-set checks.
This follow-up is proposed, not executed.

Read-only inspection found no second unmodified Python migration-allowlist candidate from the
explicit0017-filename search. The other unmodified Python match, nutrition synthesis acceptance,
loads the fixed0017 migration for its own semantics and is not an enumeration guard; historical
JSON matches remain frozen fixtures. This limited inspection is not proof that the261unexecuted
cases pass.

## Preserved and stopped

537previous export bodies +19additive =556;503/515historical pins,53frozen files,59PIVpins and185
canonical runtime/migration bytes remain checked. The19original local files/HEAD/status are
unchanged. Draft0018/114 adds only the approved six Identity tables/four NOLOGIN roles/17functions/
five protected entries and exactly one selected namespace-specific two-grant TLS pair.
Production Nutrition/provider/enrollment/qualification/publication/default content remains0 on
fresh install; no production deployment occurred. Canonical main remains0017/108 and537exports.

No commit/push/implementation PR, CI, merge or freeze was performed. Do not continue implementation
or apply this metadata proposal without separate owner authorization. FullMTR006/007/008 INCOMPLETE;
issues5/6/7OPEN;productiongateCLOSED;planner_ready=False;activation_ready=False;
ExecutionNOTSTARTED;PRECOMMITFAIL-CLOSED.

Local receipts: `.local/identity-full-regression-final-2/results.xml` and
`.local/identity-migration-allowlist-red.xml`. The full failed JUnit/log is not published because
tracebacks may contain disposable fixture credentials; the exact sanitized finding is above.
