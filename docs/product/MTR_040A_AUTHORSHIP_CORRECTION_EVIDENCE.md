# MTR-040A authorship correction — evidence

Status: **NOT FROZEN — correction submitted for freeze review**.
Reviewed baseline: PR #71, `f451d7fb86170ca5326692929b13be7dfb864173`.
Implementation commit, correction PR and CI links are recorded after actual verification.

## Defect and exact rule

0011 guarded SELF → linked subject, but not the inverse. Four focused PostgreSQL regression
cases reproduced the defect before the fix: self-linked OWNER/EDITOR declarations marked
AUTHORIZED_REPRESENTATIVE were accepted through both service and direct SQL (4 failures,
20 deselected). The initial sandbox connection failure was environmental, not a reproduced bug;
the recorded four failures used a ready PostgreSQL18.4 test server outside the network sandbox.

At write time, canonical authenticated Membership is locked FOR SHARE:

- SELF iff its member_id equals the subject member_id.
- AUTHORIZED_REPRESENTATIVE iff its member_id differs from the subject. NULL is distinct from
  a non-null subject and may represent them.
- OWNER/EDITOR may write; VIEWER may not. Existing household/subject/principal checks remain.
- Incorrect caller mode is rejected, never normalized. No preference fan-out.

The application guard in PreferenceService._access() and authoritative PostgreSQL
menuto_preference_append() independently enforce that relation. The existing membership lock,
revision CAS, idempotency, member frontier and transaction boundaries are unchanged.

## Forward migration and compatibility

`0012_preference_authorship_semantics.py` uses frozen CREATE OR REPLACE FUNCTION SQL;
upgrade adds only the inverse representative guard. Downgrade restores the exact previous
0011 function body and acceptance behavior. No import of mutable ORM/old migrations, data
backfill, table/column/constraint/trigger changes or lossy downgrade. Head **0012**, **58 tables**.
Migration0001–0011 files are byte-for-byte unchanged from the reviewed baseline.

Tests compare all preference table rows (including audit hashes/frontiers/heads), other preference
function definitions and append function identity across empty/populated 0011→0012→0011→0012.
A historically mislabeled declaration is deliberately inserted via frozen0011 SQL: its record,
hash and snapshot primitive remain unchanged throughout. No retroactive claim that its historical
label was truthful; repairing such history would require an explicit new corrective declaration.
The corrected service can append a valid SELF replacement on that stream.

No wire schema/hash changes, new source primitive or raw EvidenceStrength. Frozen MTR-019A/B/C
and MTR-020A semantics remain unchanged. Learning, Execution, TasteFit, profile derivation,
MTR-041 and PRECOMMIT authority are not implemented by this correction.

## Tests executed

26 focused real-PostgreSQL tests pass: 12 canonical membership/mode/role cases each through
service and raw SQL, plus empty and populated migration roundtrips. Rejected application writes
must raise PermissionError; a database-only rejection cannot conceal a missing application guard.
Positive cases assert the original mode is preserved. Negative cases assert no appended row.

Full regression, migration/drift, architecture/exports, benchmark and client/web results are
recorded below after execution. Current-head assertions alone advance0011→0012 in four existing
test files; historical0011 migration targets and all previous business/hash checks remain.

## Verification results

Local verification on Python 3.13 / PostgreSQL 18.4:

| Check | Actual result |
| --- | --- |
| Full Python suite | **1350 passed**, 0 failures/errors/skips, 169.04s |
| PostgreSQL-real included in that run | **615** (589 prior +26 new), independently marker-collected |
| Prior regression identities | **1324/1324 retained**, including all prior MTR-040A tests |
| Focused authorship/migration tests | **26 passed**, 10.94s |
| Migration/drift | Empty/populated 0011→0012→0011→0012; head→base→head; metadata drift PASS |
| Frozen migrations | All 11 files unchanged against baseline; downgrade body matches0011 |
| Architecture/imports/Ruff | PASS:30 invariants,11 ADRs,50 tasks,16 contexts |
| Contract/OpenAPI exports | PASS, no schema changes |
| Synthetic fixtures / benchmark | **22 fixtures /22 of22 scenarios PASS**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client | **10/10**, generated contract check and typecheck PASS |
| Web | TypeScript/Vite build PASS |

One existing Starlette/httpx deprecation warning remains. No tests were removed or weakened.
Ignored local artifacts: `.local/authorship-red.log`, `authorship-focused.xml/log`,
`authorship-full.xml/log`, `authorship-postgres-collection.log`, `authorship-benchmark.json`.
Remote PR/head and post-merge evidence are recorded after actual CI completion.

**READY FOR MTR-040A FREEZE REVIEW** is the delivery gate; MTR-040A is not self-frozen.
