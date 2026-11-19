# Identity principal-to-User enrollment — implementation evidence

**STRUCTURAL / TEST_ONLY — LOCAL FULL ACCEPTANCE PASS / IMPLEMENTATION REVIEW CANDIDATE / INDEPENDENT REVIEW PENDING / NOT MERGED / NOT FROZEN / PRODUCTION GATE CLOSED**

This is author-executed implementation evidence, not independent security approval, live deployment,
current-authorization admission or a structural freeze. No production migration was run.

## Governing identities and authorizations

- Design PR146 and bounded implementation/preflight PR147.
- Corrected retained-catalog-cut design PR148, main/base `68fcb688231460f1973077eb20140b8c5db440a2`,
  design tree `0855a39561bc194d569ef8b93b6e4db68a49f91b`.
- [PR148 completion6936082046](https://github.com/thedusk4203/Menuto/pull/148#issuecomment-6936082046),
  baseline pushCI43995258973 SUCCESS:4611 tests, not Identity implementation acceptance.
- [Original narrow TLS grant exception6904787639](https://github.com/thedusk4203/Menuto/pull/147#issuecomment-6904787639).
- [Legacy capability classification6906886726](https://github.com/thedusk4203/Menuto/pull/147#issuecomment-6906886726).
- [Retained-cut correction6918157643](https://github.com/thedusk4203/Menuto/pull/147#issuecomment-6918157643).
- [Two-layout TLS variation6937420352](https://github.com/thedusk4203/Menuto/pull/148#issuecomment-6937420352).
- [Exact native10 classification6966766271](https://github.com/thedusk4203/Menuto/pull/148#issuecomment-6966766271).
- [Separate one-line MTR040B exception6969179602](https://github.com/thedusk4203/Menuto/pull/148#issuecomment-6969179602).

The exact submitted implementation head and final exact-head CI belong to the PR verification receipt.
A commit cannot include its own future hash/CI result. This document does not infer CI completion.

## Physical persistence and privilege inventory

Previous canonical migration0017 /108 tables. Draft forward migration0018 adds six typed private
Identity tables, resulting in114 installed domain tables. Existing public Base108 is unchanged.
No0019, no modification of0001–0017, no Nutrition/preference authority reuse.

Tables in `menuto_identity_source`: **`roots`, `issuers`, `principal_bindings`, `operation_grants`, `frontiers`, `command_receipts`**.
One private `recorded_order` sequence; four typed append-only histories, frontiers and atomic
idempotency receipts. Source/CAS locks, auth-before-receipt retry checks, typed FKs and append-only
triggers execute at the protected PostgreSQL boundary. Caller owns commit/rollback.

Four NOLOGIN roles: **`menuto_identity_source_owner`, `menuto_identity_bootstrap`, `menuto_identity_issuer`, `menuto_identity_requester`**. No production login or enrollment is seeded. Owner has no
inherited membership/elevated role capability. Ordinary actors own no protected source objects,
have no direct DML/sequence access and no PUBLIC protected EXECUTE.

Exactly five protected actor entries:

| Entry | Granted group |
|---|---|
| `bootstrap_root(text)` | `menuto_identity_bootstrap` |
| `change_issuer(text)` | `menuto_identity_bootstrap` |
| `change_binding(text)` | `menuto_identity_issuer` |
| `change_operation_grant(text)` | `menuto_identity_issuer` |
| `capture_request_source(text)` | `menuto_identity_requester` |

Twelve private helpers: **`_canonical_hash_v1`, `_parameter_acl_facts_v1`, `_tls_fact_v1`, `_safe_role_v1`, `_session_fact_v1`, `_parse_command_v1`, `_lock_frontiers_v1`, `_authority_at_v1`, `_assert_lifecycle_v1`, `_reject_history_mutation_v1`, `_append_receipt_v1`, `_capture_sources_v1`**. Total17 SQL functions. The private `_tls_fact_v1` is also
SECURITY DEFINER; it is not a sixth actor entry and has no ordinary/PUBLIC EXECUTE.
All17 functions pin `search_path=pg_catalog,menuto_identity_source,pg_temp`.
The owner has the approved SELECT on four canonical public anchors (users, households,
household_members, memberships), plus the selected two-grant TLS pair; no prior/Nutrition/PIV
source-table/function authority, blanket EXECUTE, pg_read_all_stats, new role or extra entry.

## Native TLS and legacy68 boundary

The original actual42501 failure is retained in the TLS blocker report. A hardcoded-private-schema
resolver then blocked the frozen public-extension lifecycle. That historical result is preserved in
[the raw namespace blocker](IDENTITY_SHARED_SSLINFO_NAMESPACE_IMPLEMENTATION_BLOCKER.md), and the
subsequent68-versus78 result in [the raw classifier blocker](IDENTITY_PUBLIC_SSLINFO_ROUTINE_CLASSIFICATION_BLOCKER.md).
These are historical stage records, not the current acceptance verdict.

The correction preserves all68 legacy pins byte-for-value and uses a separate exact ten-function
native manifest. Neither78 count, C language, INVOKER, prefix nor namespace alone establishes safety.
Live installer/protected SQL verifies actual PG18.4, sslinfo1.2, allowed namespace, trusted deployment
owner, function OIDs/owners, full declarations/OUT/SETOF result, symbol/library, ACLs/grant options,
actual extension membership/dependencies and the exact native set. Unknown/changed/eleventh rows
fail closed. All FUNCTION facts remain captured. OIDs are installation-local, never cross-cluster
numeric constants. The bounded supported deployment uses extension/function owner equal to the
trusted superuser database owner; other owner topologies are not silently admitted.

[Narrow before/after draft correction](IDENTITY_NATIVE_SSLINFO_CORRECTION.diff) preserves the uncommitted pre-correction source for inspection.

[Authored native semantic manifest](IDENTITY_NATIVE_SSLINFO_SEMANTIC_MANIFEST.json) retains all ten
reviewed declarations and separate namespace fingerprints. Native body/dependency fingerprint
includes raw-ACL NULL/EXPLICIT state; complete reconstructed ACLs remain separate primitive facts,
with raw installed ACLs pinned by the live SQL gate. Native library/catalog provenance assumes a
trusted PostgreSQL deployment. This is **not cryptographic binary attestation**.

The trusted installer selects exactly one namespace, then grants only USAGE there and EXECUTE on
its native ssl_is_used(). No grants in both namespaces. The parsed SQL BEGIN ATOMIC private helper
has a verified pg_depend edge to the actual native function OID, fixed safe search_path, and
metadata revalidation before evaluating it. The other nine native routines are metadata only;
Identity does not invoke them or promote client-certificate data into Policy authority.

The live gate and pure checker have different proof limits: Validation owns a separate literal
native semantic manifest, reconstructs role closure/ACLs and rejects contradictory facts without
importing/calling the producer classifier. Existing19 contracts contain no pg_depend primitive.
An internally coherent offline forgery cannot prove actual extension/database origin and remains
TEST_ONLY / UNVERIFIED_TRANSPORT / NOT_ADMITTED, as explicitly tested. Matching fingerprints and
CONSISTENT labels cannot authorize current work or numerical use.

Downgrade refuses any retained Identity history. For an empty source it removes Identity objects
and only its added TLS ACL entries. The installation ledger preserves preexisting selected-schema
USAGE/primitive EXECUTE, shared extension/member objects, PUBLIC native defaults and historical
prior-domain ACLs. No DROP EXTENSION, relocation or CASCADE workaround is used.

## Runtime module/API inventory

- Identity `source_contracts`:18 immutable typed contracts; no shape change in this correction.
- `source_models`:separate private six-table metadata; public existing models unchanged.
- `source_limits`, `source_primitives`:server-owned absolute bytes/depth/row/role/edge/integer/work
  caps, duplicate-key/strict parsing and tagged deterministic canonical identity.
- `source_public`:finite protected-command facades; caller transaction, no enrollment bypass.
- `source_capture`:actual authenticated psycopg/SQLAlchemy connection, clean caller-owned read-only
  RR/SERIALIZABLE transaction, pinned deployment/endpoint/database/principal; one actual session.
- `source_replay`:pure retained replay/semantic checking with zero DB/network/filesystem/clock I/O.
- `source_routine_manifest`:unchanged68 legacy semantic pins.
- `source_native_manifest`:separate exact native10 semantics, no exported contract.
- Validation `identity_source`:independent reconstruction; no producer classifier/oracle import.
- Planning `identity_source_inspection`:fresh capture, independent source check, frozen EPI
  producer/checker and a non-admitting inspection; no caller source/report injection.
- Policy `authenticated_intent_contracts`:the nineteenth carrier, not ResolvedPlanPolicy.

No HTTP endpoint, production ingress claim, authenticated planner admission, defaults/override
precedence, numerical policy composition, PIV lease expansion or activation is implemented.

## Accepted cut semantics

One actual read-only RR/SERIALIZABLE cut; observed inconsistent catalog/identity evidence fails the
whole capture. Native GRANT/REVOKE committed after an established cut may remain unobserved. Equal
reads do not prove no concurrent mutation. Fresh unsafe captures reject42501; actual observed
session/catalog disagreement rejects whole source40001. Cross-database parameter ACL behavior and
retained-vs-fresh controls execute in real PG18.4. No new observer session/epoch/lock is introduced
in runtime. AVAILABLE_AT_RETAINED_CUT/CONSISTENT means historical retained consistency only, not
current authorization. Full-source fingerprint binds the complete retained sources/capture frame.

## Executed acceptance and compatibility

One complete fresh regression run executed **4,865 passed /0 failures /0 errors /0 skips**:
**4,611 retained baseline +254 additive Identity executions**. This is one completed run from
collection through its final node; it does not sum partial/focused runs. The
[full local receipt](IDENTITY_LOCAL_FULL_ACCEPTANCE_RECEIPT.json) records actual case identities,
class counts, retained properties, XML digest and verification inventory. Exact-head GitHub CI
is a separate delivery requirement recorded against the submitted head in the PR receipt.

All **ITR001–ITR096**, all **48 mandatory real-PG groups** and **P1–P7** are covered.
The [executed acceptance mapping](IDENTITY_ITR_EXECUTED_ACCEPTANCE.json) includes **150 actual
PostgreSQL executions** (88 original Identity +62 native supplement),57 pure/adversarial,
16 architecture/compatibility and31 new one-line inverse/mutation proofs. The native supplement
and patch36 cases reuse existing obligations; no extra mandatory IDs/groups are invented.
The earlier223 focused executions and128 historical/smoke passes are historical component
receipts, not additional tests added to the4,865 total.

Native positives exercise both `menuto_prior` and `public` layouts, bootstrap/issuer/scoped
capture, actual extension/member OIDs/declarations, parsed helper dependency, NOLOGIN owner TLS,
plaintext rejection, SCRAM and client verify-full. Negatives exercise shadowing, eleventh/member
substitution, binary/symbol, owner/ACL/dependency/role/CREATE mutation, retained primitive tamper
and coherent offline forgery limitations. Empty upgrade/downgrade preserves shared extension
and preexisting ACLs. [Native catalog/execution evidence](IDENTITY_NATIVE_SSLINFO_EXECUTION_EVIDENCE.json)
retains the earlier diagnostics and the final full-suite result separately.

The complete historical reference-prior fixture regression and SCRAM/TLS groups execute in this
full run. Dedicated smoke16/16, benchmark22/22, client10/10, Ruff, architecture/import boundaries,
OpenAPI/domain exports,22 synthetic fixtures, typecheck and web build PASS as repository guards.

Before publication, the new migration was materialized using its exact Git LF bytes and the
new guard's raw digest was aligned with that committed blob. Its full Python AST, including
literal SQL values, is identical to the local full-run copy. No runtime or privilege semantics
changed. The exact canonical migration SHA256 is
`27282e130042a202da2fee1c4e1d05dc97c2512c3dea9f380d4af8696659d7de`.
All 185 old frozen Git blobs and the original target/receipt/35-package blobs were rechecked.
The strict focused guards then passed again:48/48,0errors/failures/skips. This artifact-digest
verification is separate from the4,865-test runtime regression; final exact-head CI is the
complete submitted-tree verification. The guard accepts only the exact LF bytes, not a
permissive newline-normalized equivalent.

### Separately authorized MTR040B one-line exception

The immutable PR147 package remains exactly35 entries and SHA256
`f82f527841e4cc2e2c9097bf6fa36226c19e3d9397531d75c8a30e8d305095d3`.
[Complete existing-file ledger](IDENTITY_EXISTING_FILE_PATCH_LEDGER.json) retains those35 original
entries and one separately authorized36th entry. It does not rewrite the historical preflight.
Only the literal0018 filename is inserted in `test_target_affinity.py`; no other old source line,
receipt, hash, test name or assertion is changed by this exception.

- Historical file preimage SHA256: `4196726aa225684fb294dbe4f7e1cd917f51180c44368c0f943a67be55e47f13`.
- Exact one-line postimage SHA256: `13fb1dee71b83ff6f3789133fe8481e3738458e9a87a9f05a718b9041f65746f`.
- Historical receipt SHA256: `61ccf6b0bb0c10bfc3979e062b7a3dc9563f6f694620bd8c706dab16ac9636b5`.

The Identity-owned helper first requires exact postimage, reverses the single pinned block,
then requires exact historical preimage. The original MTR040B test still runs its AST checks,
237 schema pins,13 original migration hashes and exact filename assertion. Additional guards
pin the exact0018 body/revision/down_revision and every original0001–0017 file. No wildcard,
subset check or permissive source normalization is introduced.

[Patch36 execution evidence](IDENTITY_MIGRATION_ALLOWLIST_EXECUTION_EVIDENCE.json) records
48 focused passes (31 new inverse/mutation +16 architecture + original040B), and all31 new cases
also pass in the full run. Mutations reject each0001–0013 body change, deletion/rename,0019 or
unknown filename,0018 name/body/revision/parent drift, unapproved source edits, duplicate insertion,
wrong preimage/postimage and historical receipt tamper. Original35 inverse/mutation guards
continue to execute. Baseline migration graph has singleton head0017;0018 is its sole additive child.

Earlier incomplete runs are preserved as diagnostics, without adding their counts to the
successful full run:

- A 20-connection local harness stopped at 2,102 passed / 1 setup error. Only the ignored
  harness capacity changed to 100; no historical fixture or privilege changed.
- The next run stopped at 4,572 passed / 1 historical migration-allowlist failure, with 261
  cases unexecuted. The separate owner authorization allowed the one-line exception above.
- A long-lived process crossed from 18 November to 19 November and stopped at 3,062 passed /
  1 failure. The unchanged plan fixture retained its imported NOW, while created_at used live
  database time, producing SQLSTATE 23514 on the historical deadline constraint. The exact
  case passed in a fresh process without a test or runtime change. A temporary test-runner
  keep-awake request is released after cleanup; no machine power policy changed.
- Another run stopped at 2,629 passed / 1 setup error when a bootstrap connection closed
  before source checks. No postmaster crash, slot exhaustion or SQLSTATE was observed; the
  cause remains unproven. Three adjacent cases passed in a fresh control. No source retry
  or privilege change was introduced. The full retry added only ignored connection diagnostics.
- Two later in-progress runs were interrupted for corrections in NEW Identity test fixtures,
  and are not PASS receipts. Both fixtures now pin exact server_version_num 180004, matching
  the runtime/migration, instead of comparing a display string that can include vendor text.
  The new Identity HBA fault helper now uses the exact PostgreSQL-observed client IP plus
  explicit loopback hosts, following the unchanged hierarchy fixture convention for container
  networking. Temporary rules remain exact-database/exact-role/exact-host and restore the
  complete original HBA file. No historical assertion, runtime authorization or production
  HBA changed.

The final complete 4,865-test run began after these new-fixture corrections. The historical
migration blocker report and proposed exception remain unchanged as prior-stage evidence.

Compatibility: **537 old definition bodies retained exactly +19 literal manifest additions =556**.
The503 historical pins,515 legacy definitions,53 frozen files,59 PIV pins and4,611 baseline test
identities remain checked. All185 canonical runtime/migration files are byte-identical; no old
migration or source semantics change. Both original new-contract modules retain their pre-correction
hashes, preserving all19 shapes. Original19 local files, HEAD/status and hashes remain protected.
The preservation fixture is an author-local attestation, not remote proof of worktree access.

## Fresh install and production boundaries

Actual fresh install:0018 /114 domain tables, all six Identity sources empty; provider/enrollment,
qualification/publication/production Nutrition content0. The only nonempty tables are the two
unchanged baseline culinary/protein frontier witnesses, each one row; these are not new content.
Four groups are NOLOGIN; no qualified actor, provider, source enrollment, default or login is seeded.
This gate intentionally adds six durable Identity tables; it is not ZERO NEW PERSISTENCE.

FullMTR-006/007/008 INCOMPLETE;issues#5/#6/#7 OPEN. Frozen Root/NPS/NRE/MBA/PIV/EPI identities and
semantics are preserved. Production Nutrition/clinical gate CLOSED. planner_ready=False;
activation_ready=False;Execution NOT STARTED;PRECOMMIT FAIL-CLOSED. No merge, freeze, deployment,
production scientific content, solver or downstream implementation is authorized by this evidence.

## Exact nineteen additive exported contracts

- `IdentityEffectiveRequestV1`
- `IdentityRoleFactV1`
- `IdentityRoleEdgeV1`
- `IdentityPrivilegeObjectFactV1`
- `IdentitySessionFactV1`
- `IdentityRootCommandV1`
- `IdentityIssuerCommandV1`
- `IdentityBindingCommandV1`
- `IdentityOperationGrantCommandV1`
- `IdentityRecordedFactV1`
- `IdentityCommandReceiptV1`
- `IdentityRequestBindingV1`
- `IdentityMembershipWitnessV1`
- `IdentitySourceFrontierV1`
- `IdentityCaptureFrameV1`
- `IdentitySourceSnapshotV1`
- `IdentityCaptureFailureV1`
- `IdentitySourceCheckV1`
- `AuthenticatedPlanIntentInspectionV1`
