# Identity physical database and privilege authorization inventory

**PROPOSED INVENTORY ONLY. No SQL, migration, role or grant is executed by this package.**
Baseline/source semantics are the [approved design](IDENTITY_PRINCIPAL_USER_ENROLLMENT_BOUNDED_DESIGN.md).

## Physical representation and common history columns

Exactly six tables in schema menuto_identity_source. Separate IdentitySourceBase metadata owns these
six; public shared Base and its108 existing tables remain byte-identical. Actual installed domain
count would be114 across public/Identity schemas. No foreign key to pg_authid, User/Household/Member
or Membership: these are retained observed anchors, and their existing deletion semantics must not
be changed. Protected SQL reconstructs their actual truth at each required operation.

The four typed history tables share these **explicit proposed columns**, not a generic event table:

| Column | PostgreSQL type / invariant |
|---|---|
| id | UUID PK, DB-generated fact identity |
| root_id, stream_id | UUID NOT NULL; immutable source identities |
| revision | BIGINT NOT NULL >0, UNIQUE(root_id,stream_id,revision) |
| recorded_order | BIGINT NOT NULL >0, DB-owned shared sequence, unique per table; gaps allowed |
| recorded_at | TIMESTAMPTZ NOT NULL, finite, actual DB time after authority/frontier locks |
| previous_id, previous_fingerprint | UUID / CHAR(64), both null iff revision1; otherwise same-table/same-root/same-stream predecessor FK |
| action | TEXT NOT NULL, table-specific finite action check |
| effective_start, effective_end | TIMESTAMPTZ nullable; both null iff REVOKE, otherwise finite start<end |
| actor_database_oid, actor_role_oid | BIGINT NOT NULL, CHECK1..4294967295, observed OIDs, never client facts |
| actor_database_name, actor_role_name | VARCHAR(63) NOT NULL, actual case/UTF-8-byte limits |
| author_session | JSONB NOT NULL, complete strict observed IdentitySessionFactV1, secrets forbidden |
| command_body | JSONB NOT NULL, complete strict authored typed command including evidence/CAS; normalized fields must agree |
| command_fingerprint, fact_fingerprint | CHAR(64) NOT NULL, lowercase hex, recomputed protected preimages |
| idempotency_key | UUID NOT NULL; cross-table uniqueness enforced by atomic receipt key |
| environment | TEXT NOT NULL CHECK='TEST_ONLY', no default production value |

Every history table has UNIQUE(id,root_id,stream_id) for composite predecessor FKs, and
UNIQUE(id,root_id) for typed cross-source FKs. Predecessor revision+1, fingerprint, non-overlap,
authority containment and immutable subject consistency are checked under source locks, not by a
caller-provided JSON label. All source FKs RESTRICT/NO ACTION, never cascading history deletion.
Retained JSON stores complete typed preimages; it does not replace normalized identities/constraints.

## Six-table exact delta

| Table | Additional columns | Keys / authority constraints |
|---|---|---|
| roots | database_oid BIGINT, database_name VARCHAR(63), deployment_context_id VARCHAR(64), all NOT NULL | stream_id=root_id; action INITIALIZE/RENEW/REVOKE; one INITIALIZE per deployment via unique constant partial index; later same root only, no reset/replacement by second root |
| issuers | root_initial_fact_id UUID, issuer_user_id UUID, issuer_role_oid BIGINT, issuer_role_name VARCHAR(63), target_role JSONB, capability TEXT, all NOT NULL | FK root initializer (id,root_id); capability BINDINGS_AND_SCOPE_GRANTS; action ENROLL/RENEW/REVOKE; issuer ID=stream_id; subject/DB/role/User immutable; bootstrap author only |
| principal_bindings | root_initial_fact_id UUID, enrolling_issuer_id UUID, author_issuer_fact_id UUID, user_id UUID, role_oid BIGINT, role_name VARCHAR(63), target_role JSONB, all NOT NULL | FKs root initializer and actual issuer fact (id,root_id); binding ID=stream_id; ENROLL/RENEW/REVOKE; permanent root+role OID and root+role name reservation on ENROLL; no issuer-User/requester-User alias overlap |
| operation_grants | root_initial_fact_id UUID, binding_initial_fact_id UUID, binding_id UUID, author_issuer_fact_id UUID, operation TEXT, household_id UUID, tracked_member_id UUID, membership_id UUID, actor_member_id UUID, membership_role TEXT, membership_at_issue JSONB, all NOT NULL | Typed FKs root/binding/issuer facts within same root; operation CAPTURE_EXPLICIT_PLAN_INTENT; role OWNER/EDITOR; GRANT/RENEW/REVOKE; exact immutable household/member scope; current and complete delegated interval authorization required |
| frontiers | root_id UUID NOT NULL, root_initial_fact_id UUID NOT NULL, kind TEXT NOT NULL, stream_id UUID NOT NULL, revision BIGINT NOT NULL, fact_count BIGINT NOT NULL, head_id UUID nullable, head_fingerprint CHAR(64) nullable, directory_entries JSONB NOT NULL, directory_fingerprint CHAR(64) nullable | PK(root_id,kind,stream_id); FK(root_initial_fact_id,root_id) to roots(id,root_id), initializer action checked; kind ROOT/ISSUER_DIRECTORY/BINDING/OPERATION_GRANT; revision/count>=0; zero implies null head and zero count; issuer-directory JSON only for its kind, complete issuer heads/counts, not authority itself |
| command_receipts | id UUID PK, root_id UUID, actor_role_oid BIGINT, idempotency_key UUID, kind TEXT, stream_id UUID, revision BIGINT, recorded_at TIMESTAMPTZ, command_fingerprint CHAR(64), fact_fingerprint CHAR(64), root_fact_id/issuer_fact_id/binding_fact_id/grant_fact_id UUID nullable | UNIQUE(root_id,actor_role_oid,idempotency_key); exactly one typed fact FK non-null according to kind; typed event/receipt stream and fingerprints agree; immutable original APPENDED result |

For frontiers, directory_entries is [] except for ISSUER_DIRECTORY. There is one directory frontier
per root; each issuer's latest row is protected by that lock and its complete directory entry. No
extra per-issuer table is needed. Global sequence is private, owned by object owner; only protected
code allocates values. Uniqueness across all typed events follows protected nextval allocation and
root serialization; no ordinary SETVAL/sequence access. Source-owner/superuser tampering is TCB.

No static EXCLUDE constraint over authored intervals pretends to understand later revocation. Under
the root lock, bounded complete replay enforces at most one effective binding per User and one
applicable exact operation grant, non-overlapping renewals and terminal revocation. A revoked
binding may be replaced only by a fresh dedicated role/new enrollment; old role reservations remain.
Issuer source histories retain role/User reservations; a requester User cannot become an issuer
alias under another login. Reject before insertion if any applicable-state ambiguity exists.

## Indexes, triggers, locks and atomicity

For each history: PK and composite unique keys above; unique recorded_order; index
(root_id,stream_id,revision DESC); index(root_id,recorded_order). Issuers add root+issuer_user_id
lookup; bindings add partial unique ENROLL indexes(root_id,role_oid) and(root_id,role_name), and
(root_id,user_id,stream_id) lookup; grants add(root_id,binding_id,operation,household_id,
tracked_member_id,revision DESC). Receipts use the exact author/idempotency unique key and typed
fact lookup indexes. Frontiers use its PK only. No btree_gist/new extension is required.

Append-only BEFORE UPDATE/DELETE triggers always reject on the four histories and receipts.
Frontier mutation is possible only to the NOLOGIN owner through protected entry code; no caller GUC
or client-supplied internal flag authorizes writes. Strict row checks validate typed discriminators,
field agreement and predecessor links; semantic source-state guards revalidate under locks. Normal
actors have no direct table/sequence rights. A privileged TCB administrator can bypass controls;
this is explicitly not protection against a compromised administrator.

First initialization uses an Identity-specific per-database advisory transaction lock before root
frontier exists. Other writes lock root frontier -> issuer directory -> binding -> operation frontier,
in stable key order. Initial absence/CAS revision0 is protected by the root lock. Writes require
caller-owned READ COMMITTED read-write transaction; after locks recheck actual session/authority,
then idempotency receipt, then CAS/predecessor. Append one typed fact, matching receipt and frontier
update in the same transaction. No hidden commit/rollback. Identical retry returns original receipt
only if still authorized; changed payload conflicts. Revoke is immediate/terminal, including scheduled
renewals. DB time, not client declared_at, drives authorization. Cancellation/timeout must leave no
partially committed event/frontier/receipt and requires caller rollback before reuse.

## Five protected SQL entries and private helper inventory

Exactly these future SQL entries, all in menuto_identity_source, SECURITY DEFINER, owned by the
private NOLOGIN owner, fixed search_path=pg_catalog,menuto_identity_source,pg_temp:

| Function | Proposed transport signature | Only executable group |
|---|---|---|
| bootstrap_root | (command_text TEXT) RETURNS JSONB | menuto_identity_bootstrap |
| change_issuer | (command_text TEXT) RETURNS JSONB | menuto_identity_bootstrap |
| change_binding | (command_text TEXT) RETURNS JSONB | menuto_identity_issuer |
| change_operation_grant | (command_text TEXT) RETURNS JSONB | menuto_identity_issuer |
| capture_request_source | (request_binding_text TEXT) RETURNS JSONB | menuto_identity_requester |

TEXT is intentional: JSONB input would discard duplicate keys before protected validation. Bound
bytes/lexemes/depth before casting to JSONB; reject duplicate keys at every nesting level. SQL output
is strict contract JSON; hashes use the approved canonical protocol, not PostgreSQL display text.

Private helper inventory (no PUBLIC/actor EXECUTE): _session_fact_v1, _safe_role_v1,
_parameter_acl_facts_v1, _tls_fact_v1, _parse_command_v1, _canonical_hash_v1,
_lock_frontiers_v1, _authority_at_v1, _assert_lifecycle_v1, _append_receipt_v1,
_capture_sources_v1, _reject_history_mutation_v1. Existing PostgreSQL sslinfo primitive may be used
by the Identity-local TLS helper; never call Nutrition/PIV private functions or grant pg_read_all_stats.
No dynamic identifier/role SQL, arbitrary query function, role provisioning or unbounded source reader.
Private helpers are implementation inventory, not extra public entry points or exported contracts.
Proposed exact private signatures (all EXECUTE revoked from PUBLIC and actor groups):

| Helper | Arguments | Return |
|---|---|---|
| _session_fact_v1 | mode TEXT | JSONB |
| _safe_role_v1 | actor_oid OID, mode TEXT | JSONB |
| _parameter_acl_facts_v1 | actor_oid OID | JSONB |
| _tls_fact_v1 | none | JSONB |
| _parse_command_v1 | raw_text TEXT, kind TEXT | JSONB |
| _canonical_hash_v1 | tag TEXT, typed_preimage JSONB | TEXT |
| _lock_frontiers_v1 | root_id UUID, binding_id UUID, grant_id UUID | VOID |
| _authority_at_v1 | root_id UUID, stream_id UUID, recorded_at TIMESTAMPTZ, effective_start TIMESTAMPTZ, effective_end TIMESTAMPTZ | JSONB |
| _assert_lifecycle_v1 | previous_fact JSONB, next_fact JSONB | VOID |
| _append_receipt_v1 | kind TEXT, fact JSONB, command JSONB | JSONB |
| _capture_sources_v1 | request_binding JSONB, observed_session JSONB | JSONB |
| _reject_history_mutation_v1 | none | TRIGGER |

These signatures specialize the approved five-entry scope; they are proposals requiring implementation
authorization. Mode/kind values are finite internal discriminators, not caller-selected SQL or bypass
flags. Private arguments are never accepted as externally authoritative session facts. Hash helper
must implement approved UTF-8 sorted-key canonicalization, not JSONB display ordering/escaping.
No helper publishes a sixth entry or grants any extra source access.

## Exact role, grant and revoke matrix

Four proposed Identity-specific NOLOGIN roles, all NOSUPERUSER/NOCREATEDB/NOCREATEROLE/
NOREPLICATION/NOBYPASSRLS: menuto_identity_source_owner, menuto_identity_bootstrap,
menuto_identity_issuer, menuto_identity_requester. Issuer/requester groups own no SQL objects.

| Principal | Granted rights | Explicit exclusions / verification |
|---|---|---|
| Trusted installer | Out-of-band schema/role/function installation under actual deployment admin | No credential or actor seed; name collision with unsafe/pre-existing unrelated role refuses install |
| Bootstrap LOGIN | Actual database owner or superuser AND dedicated bootstrap membership; USAGE schema, EXECUTE first two entries | Separate from ordinary issuer/requester; SCRAM/TLS, DB/OID/name, no SET ROLE/SESSION AUTH spoof; never accepted as ordinary source actor |
| NOLOGIN source owner | Own private schema,six tables,sequence,functions; SELECT only public.users/public.households/public.household_members/public.memberships | No ordinary membership/SET/admin path into owner; no broad base-table write grants; no password/login or human identity |
| Operational issuer LOGIN | Existing bootstrap-enrolled User; issuer group membership; USAGE schema + EXECUTE change_binding/change_operation_grant only | No CREATEROLE/DB/super/BYPASS/replication/db or object ownership; no direct source reads/DML, sequence or base DML; cannot enroll issuers or act as requester |
| Dedicated requester LOGIN | Existing issuer-bound User and exact operation grant; requester group; USAGE + EXECUTE capture only | Same unsafe-role exclusions; must satisfy exact Membership/member grant; cannot author goals, physiology, grants or publish anything |
| Independent Validation | Pure retained immutable inputs only; no new DB role/grant | No validator backdoor reader, producer oracle, current-authorization claim or Nutrition/PIV source-read capability |
| PUBLIC / ordinary roles | No private schema/table/sequence/helper rights | Explicit REVOKE ALL on schema,all tables,sequence,functions; revoke PUBLIC function EXECUTE in installation transaction; default future function EXECUTE revoked for source owner |

Exact entry-group grants from a trusted admin use INHERIT TRUE,SET FALSE,ADMIN FALSE. Verify complete
role graph and actual authenticated login, including grant options/ownership and unsafe direct
privileges. Existing independent enrollments in other domains do not count as Identity permission.
No actor receives CREATE on private/public schemas or ownership of trusted code. Source owner gets
only the four canonical anchor-table SELECT grants above; no blanket database reader role. The four exact anchor names were verified against the pinned Identity/Households model declarations;
recheck their OIDs/owners/grants before any future DDL.

## Ownerless PARAMETER ACL proof preserved

The approved correction is normative: owner_oid=null iff PARAMETER; all owned object kinds require
actual catalog owners. Capture complete pg_parameter_acl across the cluster, including all grantees
and unloaded/custom names. Real row OID only; missing row produces no fake object/OID. Distinguish
raw paracl=NULL, explicit empty ACL and absence. No table-owner/default-creator ACL fallback.
PostgreSQL18.4's parameter evaluator/defaults and native user-context SET are distinct: an ordinary
role can SET work_mem without an extra ACL grant. Reconstruct SET/ALTER SYSTEM/grant options for
actual login/PUBLIC/inheritable roles, separately check SET-role escalation; deny ordinary extra
parameter ACL capability. Use has_parameter_privilege with explicit actor OID as test oracle, not
current_user inside SECURITY DEFINER. Validate from retained primitives, not owner booleans/report
hashes. Bounded full capture or error; fully coherent offline forgery remains unverified transport.
ITR018 P1–P7/ITR055 are future actual-catalog and mutation proofs, not current executed tests.

## Installation, source capture and downgrade

Actual current migration DAG has sole head0017/down0016 and seventeen existing revisions. No new
revision/file is reserved. At implementation authorization re-fetch the DAG, select/approve the next
legal revision and exact filename, then pin it in the new test-only migration manifest. No changes
to0001–0017; no importing live application SQL into a historical migration. Six source tables,one
sequence,listed indexes/triggers/functions/four NOLOGIN roles install atomically with PUBLIC revokes.
Empty installation: zero root/issuer/binding/grant/frontier/receipt rows; zero LOGIN roles/passwords,
clinical content,providers,qualifications,seeds/defaults. NOLOGIN groups are infrastructure, not
qualified actors. First enrollment is a separate authenticated deployment action, not a seed.

Capture requires one actual clean read-only RR/SERIALIZABLE ordinary connection, full request bytes,
actual authenticated session/OIDs/TLS, complete selected histories and private-source frontiers,
required own Membership facts and redacted negative scope evidence. Server engine pins endpoint/
CA/root/database and absolute bounds. No dirty ORM, autoflush, cached report, multiple owner sessions,
caller-controlled resource limits or current-origin claim from serialized retained data.

Failed upgrade rolls back all transactional source DDL/privileges; it must not leave PUBLIC execution
windows. Downgrade first refuses if any six-table row/source receipt/history exists. If empty, remove
only owned functions/triggers/indexes/sequence/tables/schema and exact infrastructure grants. Remove
only roles created by this migration and only if they have no unrelated memberships/dependencies;
otherwise refuse and require administrative resolution. Never CASCADE unrelated grants/history,
delete actor accounts, drop clinical data or silently lose source truth. Forward repair needs review;
no runtime reset/automatic root replacement or unreviewed production rollback.
