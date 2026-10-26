# Reviewed exact-target preference-prior source — implementation review

Status: **IMPLEMENTED / NOT FROZEN — architecture/freeze review required**.
The user approved the [dedicated design](PREFERENCE_PRIOR_SOURCE_FOUNDATION_DESIGN.md)
and separately authorized this implementation from exact canonical main
`577f32a302cca56c7b6ac9dfb65ce2d663ae8a30` (design PR #96;
[exact post-merge CI 40279844244](https://github.com/thedusk4203/Menuto/actions/runs/40279844244)
SUCCESS). No milestone number is assigned. This source is not MTR-040C.

## Delivered boundary

Preferences owns global reviewed reference semantics and lifecycle. A reference prior is
not member preference data. Household membership, SELF/AUTHORIZED_REPRESENTATIVE, actor GUCs,
reviewer IDs, hashes and REVIEWED_REFERENCE provenance grant no publication authority.

The additive source implements:

```text
dedicated authenticated enrollment administration
  -> provider-scoped GRANT/REVOKE ledger
  -> reviewed exact-target publication/replacement/retraction
  -> coherent complete-provider capture
  -> pure exact-target reference resolution
```

The coordinate is closed: CURATED_REFERENCE_PREFERENCE / version 1 /
REVIEWED_REFERENCE_ANCHOR_UNITS / GLOBAL_REFERENCE_ONLY. Its reduced signed rational in
[-1,1] is neither a probability, utility, EvidenceStrength, pseudo-count nor a member preference.
Equal fractions do not convert it into frozen040B ExplicitAffinityAmount.

One explicit provider and one exact typed identity determine a stream: Ingredient ID,
stable Recipe ID, or a reviewed PROTEIN/METHOD/FLAVOR AffinityFeatureTerm ID. There is no
provider fallback, averaging, alias resolution or transfer across targets. NO_PUBLICATION,
RETRACTED and AVAILABLE0/1 remain distinct. Invalid identities/providers fail the request.

## Code and persistence ownership

| Component | Responsibility |
| --- | --- |
| `preferences/reference_prior_contracts.py` | Additive immutable contracts and independent primitive replay validation |
| `preferences/reference_priors.py` | Internal dedicated-connection administration, write and capture boundary |
| `preferences/reference_prior_resolution.py` | Zero-IO resolver; guarded import boundary |
| `preferences/reference_prior_models.py` | Seven new typed source relations |
| `migrations/versions/0014_reviewed_reference_prior_source.py` | Frozen forward DDL, protected SQL, ACLs, append-only/deferred guards and loss-refusing downgrade |

Migration **0014** adds seven domain tables: reference_prior_providers, principals,
frontiers, streams, authority, revisions and mutations. New head **0014 /78 domain tables**
(79 including Alembic). No persisted snapshot, member profile or materialized score is added.
Migrations0001–0013 remain byte-identical. All276 prior exported definitions are unchanged;
23 additive definitions bring the bundle to299. The frozen bundle identifier is retained.

Migration creates no providers, enrolled principals, provider capability grants, prior amounts,
default zero/neutral priors, credentials or production policy values. Three NOLOGIN structural
roles are privilege infrastructure only: menuto_prior_owner, menuto_prior_admin and
menuto_prior_client. They are not provider permission records.

## Publication authority and deployment

The non-login owner owns only the new source relations/functions and receives the required
Catalog/Recipes identity reads. Migration rejects unsafe pre-existing infrastructure roles or
broader owner privileges. Protected functions live in the inaccessible-to-CREATE menuto_prior
schema; relations are explicitly qualified in public and have private ACLs. Default PUBLIC
function execution is revoked. Only the administration group can execute enrollment/provider/
authority functions; only the client group can execute publication/capture functions.

Deployment must provision separate real PostgreSQL LOGIN credentials for administrators,
curators and readers, require SCRAM-SHA-256 in HBA, and grant the appropriate structural group.
Do not grant owner membership, database ownership, superuser/role-creation/bypass privileges,
direct source DML/TRUNCATE/TRIGGER rights or schema CREATE. Enrollment administrator membership
is rejected on ordinary source interfaces. Application/household logins are not enrolled by
default. No HTTP publishing endpoint or consumer auth workflow is installed.

Each protected entry derives original session_user and server system_user, requires the exact
SCRAM identity, verifies the real database and role OID/name, rejects unsafe privilege graphs,
and resolves an immutable principal binding. SET ROLE never changes publication identity.
Rename/drop/recreate/rotation cannot silently reuse the old binding or grants. Rotation needs
a new binding, explicit old revocation and new grants. Provider-specific REVIEW_PUBLISH,
RETRACT and CAPTURE are independently checked. A missing ledger event denies access.

Remote connections require TLS at the server boundary; the Python boundary additionally
requires sslmode=verify-full. PostgreSQL cannot certify that an arbitrary client verified the
server hostname. Loopback test connections are explicitly permitted. DBAs/database owners
remain trusted roots; this implementation does not claim protection from DBA compromise.

Curator attestation is a single authenticated review claim with rationale and actual artifact
provenance. It does not prove a second human approval or the quality of the prior content.
Optional artifact URIs use canonical ASCII HTTP(S) locators: lowercase DNS/canonical IPv4,
an explicit slash path, canonical optional port, no credentials/dot-segment rewrites. Omit
the URI when the external record/version/hash identifies the artifact sufficiently. Raw SQL
rejects locators that would be rewritten by contract parsing; no artifact is fetched.

## Transaction, lifecycle and replay

All writes serialize on provider frontier before stream. Grant/revoke shares that frontier.
Permission is checked after locking and before idempotent receipt replay. An authorized exact
retry returns its original receipt/frontier even after unrelated writes; changed payload
conflicts, and a revoked retry is denied. Caller owns commit/rollback; receipts explicitly
say CALLER_TRANSACTION_NOT_CERTIFIED. No hidden connection, commit or retry is used.

Source and authority generations advance separately. The contiguous typed mutation journal
interleaves both, so replay reconstructs the actual authority state immediately before each
publication. A revoked publication cannot pin an earlier valid grant. Initial revision is0
with expected-1/no predecessor; corrective replacement/retraction binds the current head.
Retraction carries no amount; replacement after a tombstone is explicit.

DB-owned recorded_at equals effective_at. Observed future evidence and clock regression fail;
equal timestamps use sequence order. There are no schedules, backdating, expiration defaults
or current-table historical as_of filtering. Hashes are acyclic: typed child -> journal ->
frontier/receipt. Old snapshots support historical replay without current database access.

Capture requires a clean caller-owned read-only REPEATABLE READ/SERIALIZABLE transaction.
Pending ORM writes, writable/READ COMMITTED sessions and already assigned write transaction
IDs are rejected. The same session captures the complete named provider's publications,
streams, authority events, mutations, frontiers, consumed enrollment facts and canonical owner
identities for all source plus requested targets. No successful partial/truncated capture or
snapshot cache exists. Full-source fingerprints identify capture/replay, not just visible rows.

Pure replay recursively reparses primitives, verifies command/child/journal hashes, actual
authority cuts, lineage, canonical identities, complete frontiers and result rows. Permutations
are canonicalized by semantic identity/sequence. Rehashed contradictions fail. An entirely
self-consistent forged offline artifact still does not authenticate canonical database origin.

## Acceptance coverage

The new real-PG module uses random isolated databases and separate real login connections.
Ephemeral secrets are generated during tests. HBA additions affect only random test logins;
the exact original HBA bytes are restored, including Windows CRLF. Existing trust-authenticated
fixtures remain unchanged and are not counted as SCRAM proof.
CI provisions a one-day disposable server certificate and verifies TLS with verify-full;
Docker bridge connections receive no runtime TLS exemption. Test HBA rules name only the
random database/logins and the exact observed client address. Canonical SQL validation also
rejects Unicode-only whitespace and oversized artifact references before storing source facts.

| Design category | Concrete coverage |
| --- | --- |
| A01–A02 | Unenrolled/household-style application sessions denied; forged command authority fields rejected; real actor, grant and time stamped by SQL |
| A03 | GUC/SET ROLE cannot impersonate; dropped/recreated role denied, explicit rotation binds a new OID/principal |
| A04 | Real reader/curator direct INSERT/UPDATE/DELETE/TRUNCATE, function/schema alteration, owner/admin role switch and enrollment/grant attempts denied |
| A05 | Capture-only, retract-only distinctions, cross-provider denial and revoked idempotent retry |
| A06 | Real publish/retract versus revoke ordering and stale RR/SERIALIZABLE whole-transaction aborts |
| A07 | Reviewed rationale/provenance required; canonical locator roundtrip and poisoning rejection; single attestation only |
| A08 | Administration CAS/idempotency/no-op rejection, rollback and competing administrators in all three isolation levels |
| A09 | Separate SCRAM logins, wrong/missing passwords, trust and password-auth rejection, unsafe root/admin rejection |
| C01–C03 | Closed distinct coordinate, exact rational rejection in Python and SQL, missing/retracted/available zero distinctions |
| T01–T03 | All five owner identity kinds, DRAFT/wrong-kind/unknown rejection, provider mismatch and independent conflicting provider amounts |
| L01–L03 | Full lifecycle/tombstone revival, real concurrent initial/corrective writes, stale CAS, rollback, exact and conflicting retries |
| L04–L05 | DB-owned immediate times, future observation, clock-regression refusal, equal-time sequence order and old snapshot replay |
| S01–S02 | Clean RO RR/SERIALIZABLE capture and complete unrequested source/identity history |
| S03–S04 | Dropped/duplicate/rehashed primitive, cache, lineage/binding and stale-grant forgeries; source identity versus offline origin boundary |
| S05–S06 | Distinct missingness, empty requested scope and deterministic set permutations |
| F01–F02 | Byte pins for13 frozen migrations, structural pins for276 definitions, old tests retained, fixed semantic flags and forged result rejection |
| M01 | Empty upgrade/downgrade/upgrade/drift; populated registry/audit downgrade refusal; real privilege and credential rotation coverage |
| R01 | Full existing required CI, reported below after completion |

Populated downgrade refuses before deleting even registry/enrollment/audit data. Empty downgrade
removes only the new database objects/ACLs. Structural cluster roles and all credential secrets
remain outside the downgrade lifecycle. There is no authorized destructive export/preservation
bypass.

## Remaining gates

This delivery requires architecture/freeze review; **it does not self-freeze**. Production
provider enrollment, capability grants and prior content still require explicit authorized
publication and are absent from migrations. Approved coordinate compatibility/mapping and
shrinkage/profile policies are still missing. Source capability does not authorize those policies.

Frozen040A/B,041A–F and046A are unchanged.040B prior/shrunk_affinity stay UNAVAILABLE; undeclared
and retracted remain distinct from neutral, explicit zero remains meaningful, and declaration
history/retries do not increase EvidenceStrength.041F stays proposal-local, not global history.
Full040/041/046 remain PARTIAL;024/020B/021 BLOCKED; Execution NOT STARTED; PRECOMMIT FAIL-CLOSED.

No learned/contextual/passive evidence, inference, coordinate conversion, candidate aggregation,
TasteFit, planner utility, hard-safety authority or next milestone is authorized. Every result
fixes planner_ready=False and activation_ready=False.

## Verified implementation regression receipt

Local verification on2026-10-26, with isolated PostgreSQL18.4:

| Gate | Actual result |
| --- | --- |
| Full Python + real PostgreSQL | **2377 passed**,0 failures/errors/skips,370.69s; one existing Starlette/httpx deprecation warning |
| Existing test identities | **2237/2237 retained**,0 removed;140 additive tests |
| Real PostgreSQL | **918 passed**:798 existing +120 new SCRAM/source acceptance cases |
| Explicit authority/authentication cases | **73** of the120 new real-PG cases; remaining47 cover source arithmetic/identity/lifecycle/replay/migration under those real sessions |
| Final source hardening | All140 new tests rechecked PASS after Unicode/bounded-reference hardening and enrollment-only downgrade isolation; GRANT versus REVOKE passes RC/RR/SERIALIZABLE |
| Frozen compatibility |13 migration byte pins and all276 prior structural definition pins PASS;23 additive definitions,299 total |
| Migration/deployment | Empty upgrade/downgrade/upgrade and ORM drift PASS; populated registry/audit downgrade refusal PASS; no source production rows seeded |
| Privilege/direct SQL | Real curator/reader DML, TRUNCATE, heads/frontiers, function/schema changes, owner/admin role switches and enrollment/grant attempts denied; real SCRAM superuser/database-owner and unsafe effective privilege cases denied |
| Authentication | Separate SCRAM logins PASS; missing/wrong password, trust and unsupported password authentication rejected; immutable binding rotation checked |
| Ruff / architecture / imports | PASS;30 invariants,11 ADRs,50 linked tasks,16 contexts |
| OpenAPI / domain exports / fixtures | PASS; HTTP OpenAPI unchanged;22 synthetic fixtures verified |
| Synthetic benchmark | **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client contracts/typecheck/tests / web build | PASS; client **10/10** |

Ignored local receipts: `.local/prior-source-final.xml`, `.local/prior-final-full.log`,
`.local/prior-implementation-receipt.json`, `.local/prior-implementation-benchmark.json`.
The earlier full pass was followed by focused source hardening and CI TLS provisioning;
exact GitHub PR and post-merge CI run the complete final tree again. Merge/head/CI receipts are reported in
the PR delivery record, without predicting hashes or successful checks in advance.

Files changed are limited to the five additive Preferences implementation modules/migration,
model registration, three new test modules plus frozen compatibility pins, mechanical schema
head/table/migration enumeration updates in ten existing tests, additive domain export/import
guards and pytest marker, disposable CI TLS provisioning, and source/status/deployment documentation. No frozen algorithms,
old migrations, old schema definitions, HTTP endpoints, production source records or downstream
milestone implementations change.

**READY FOR PREFERENCE-PRIOR SOURCE ARCHITECTURE/FREEZE REVIEW**
