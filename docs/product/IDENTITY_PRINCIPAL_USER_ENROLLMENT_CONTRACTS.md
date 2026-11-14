# Identity principal enrollment — proposed immutable contracts

This appendix is normative within the [bounded design](IDENTITY_PRINCIPAL_USER_ENROLLMENT_BOUNDED_DESIGN.md).
**PROPOSED ONLY / STRUCTURAL / TEST_ONLY / IMPLEMENTATION NOT AUTHORIZED.**
No contract described here exists in the current 537-definition export. The independently authored
future additive manifest is the numbered list below; it must never be inferred from actual exports.

## 1. Common wire rules

Every model is immutable, versioned, strict, closed to unknown fields, and revalidated at each
public boundary, including model-constructed instances. Every field listed is required; nullable
means explicit null, not omitted/defaulted. Tuples serialize as arrays. Duplicate JSON keys at any
depth, non-finite/float numbers, booleans as integers, invalid UTF-8, unpaired surrogates, NUL,
unsupported versions and unknown literals fail before semantic use. No Python hook/object coercion.
UUIDs use canonical lowercase text. Instants are UTC RFC3339 with explicit zone, normalized to
microseconds; intervals are half-open [start,end), finite and nonempty. Effective time and recorded
time are distinct. Identity source commands do not accept caller-authored recorded_at.

Notation: Oid is integer 1..2^32-1; Count is integer 0..2^63-1; Revision is positive Count;
Sha256 is lowercase 64 hexadecimal characters; Key is nonempty ASCII at most64 bytes; RoleName
is the exact case-sensitive PostgreSQL name, at most63 UTF-8 bytes, no normalization or controls.
Ordinary text is at most256 codepoints. Explicit evidence preimages are at most4096 UTF-8 bytes;
raw request is at most49,152 UTF-8 bytes. UUID/string/number emptiness is never a default authority.
Canonical horizons reuse the frozen EPI horizon contract without altering its body.

There are no newly exported enum/helper/base classes. Finite literals, bounded primitive aliases
and fixed tuples are internal schema shapes. Existing shared primitives are reused unchanged.
The four command shapes each include the common fields spelled out below; inheritance does not
add a public definition. These conventions fix the exact 19-name export boundary.

## 2. Exact 19-name manifest and field inventory

1. **IdentityEffectiveRequestV1** — Identity-owned. Fields: version=1; mode=IMMEDIATE|SCHEDULED;
   start: instant|null; end: instant. IMMEDIATE requires start=null and uses actual DB recorded_at;
   SCHEDULED requires explicit start strictly after recorded_at. End must exceed the resolved start.
   REVOKE commands carry effective=null rather than this object. No backdated grant or open interval.
2. **IdentityRoleFactV1** — Identity-owned catalog primitive. Fields: version=1; role_oid: Oid;
   role_name: RoleName; can_login, superuser, create_role, create_db, replication, bypass_rls,
   inherit: strict booleans; valid_until: instant|null. Null valid_until means no password expiry
   recorded by PostgreSQL, not unlimited source authority. Never include password/verifier data.
3. **IdentityRoleEdgeV1** — Identity-owned catalog primitive. Fields: version=1; role_oid,
   member_oid, grantor_oid: Oid; inherit_option, set_option, admin_option: strict booleans.
   Retain complete reachable closure, including unsafe edges; do not filter before verification.
4. **IdentityPrivilegeObjectFactV1** — Identity-owned catalog primitive. Fields: version=1;
   kind=DATABASE|SCHEMA|TABLE|COLUMN|SEQUENCE|FUNCTION|PARAMETER; object_oid: Oid;
   sub_id: Count; schema_name: text|null; object_name: text; owner_oid: Oid|null;
   acl: ordered tuple of fixed (grantee_oid, grantor_oid, privilege, grantable) entries|null;
   definition_fingerprint: Sha256|null. **owner_oid is null iff kind=PARAMETER**. Every other kind
   requires its actual catalog owner OID (COLUMN uses its owning relation's real owner); no invented
   owner, owner0 or nullable-owner fallback for DATABASE/SCHEMA/TABLE/COLUMN/SEQUENCE/FUNCTION.
   PARAMETER facts represent actual pg_parameter_acl rows only: object_oid=row.oid,
   object_name=row.parname, sub_id=0, schema_name=null, definition_fingerprint=null. For these facts,
   acl=null means observed paracl IS NULL; otherwise retain all expanded raw ACL entries, including
   an explicitly empty tuple. Non-PARAMETER keeps the required non-null ACL tuple and existing
   real-owner/default reconstruction. Grantee0 explicitly means PUBLIC, never owner0. Privilege
   literals must match kind; PARAMETER permits only SET/ALTER SYSTEM plus the separate grantable
   boolean. Protected function fingerprints still bind exact signature/body/search_path/security
   mode. Parameter defaults, complete enumeration and effective permissions follow section2.1.
5. **IdentitySessionFactV1** — Identity-owned. Fields: version=1; database_oid, database_owner_oid,
   login_role_oid, execution_owner_oid: Oid; database_name, endpoint_id, client_address: text;
   server_address: text; server_port, backend_pid: positive Count; session_user: RoleName;
   system_user: text; requested_role: text; authentication_method: text; tls: bool;
   isolation=READ_COMMITTED|REPEATABLE_READ|SERIALIZABLE; read_only: bool; observed_at: instant;
   roles: tuple[IdentityRoleFactV1]; edges: tuple[IdentityRoleEdgeV1];
   objects: tuple[IdentityPrivilegeObjectFactV1]. Endpoint ID is server-engine configuration identity,
   not a URL/secret. session_user/login_oid are actor identity, execution_owner is SECURITY DEFINER
   context. A command may retain a read-write READ_COMMITTED session; capture requires read-only
   repeatable isolation. Method/role/TLS fields are observations to check, not positive assertions.
6. **IdentityRootCommandV1** — Identity-owned. Common command fields: version=1; root_id: UUID;
   idempotency_key: UUID; expected_revision: Count; predecessor_id: UUID|null;
   evidence_id: Key; evidence_version: Key; evidence_preimage: text[4096 bytes];
   environment=TEST_ONLY. Own fields: kind=ROOT; action=INITIALIZE|RENEW|REVOKE;
   effective: IdentityEffectiveRequestV1|null. INITIALIZE starts revision1 with expected_revision0
   and predecessor=null. Bootstrap may initialize only the one selected root in this database;
   no second active root or implicit reset. RENEW retains the same selected root and appends a non-overlapping future/immediate interval;
   only bootstrap may perform it and it cannot repair an earlier gap. REVOKE is terminal and needs
   the current predecessor. A revoked root cannot be renewed or reset.
7. **IdentityIssuerCommandV1** — Identity-owned. Same common command fields. Own fields:
   kind=ISSUER; issuer_id: UUID; role_name: RoleName; user_id: UUID;
   capability=BINDINGS_AND_SCOPE_GRANTS; action=ENROLL|RENEW|REVOKE;
   effective: IdentityEffectiveRequestV1|null. Actual role OID and User existence are server reads,
   never inferred from role_name. Subject/root/role/User/capability cannot change on renewal.
8. **IdentityBindingCommandV1** — Identity-owned. Same common command fields. Own fields:
   kind=BINDING; binding_id, issuer_id, user_id: UUID; role_name: RoleName;
   action=ENROLL|RENEW|REVOKE; effective: IdentityEffectiveRequestV1|null.
   Issuer_id must identify the actual authenticated active issuer, not a caller-selected author.
   User/role/root are immutable; revoke and new dedicated role are required for replacement.
9. **IdentityOperationGrantCommandV1** — Identity-owned. Same common command fields. Own fields:
   kind=OPERATION_GRANT; grant_id, binding_id, issuer_id, household_id, tracked_member_id: UUID;
   operation=CAPTURE_EXPLICIT_PLAN_INTENT; action=GRANT|RENEW|REVOKE;
   effective: IdentityEffectiveRequestV1|null. No wildcard or alternate operation. Server reconstructs
   exact issuance Membership/actor-member/target-member; caller cannot supply that witness.
10. **IdentityRecordedFactV1** — Identity-owned immutable transport for one typed persisted row.
    Fields: version=1; fact_id, root_id, stream_id: UUID;
    stream_kind=ROOT|ISSUER|BINDING|OPERATION_GRANT; revision: Revision; recorded_order: Revision;
    recorded_at: instant; previous_fact_id: UUID|null; previous_fact_fingerprint: Sha256|null;
    command: union of exactly the four command models; command_fingerprint: Sha256;
    effective_start, effective_end: instant|null; author: IdentitySessionFactV1;
    author_issuer_fact_id: UUID|null; target_role: IdentityRoleFactV1|null;
    membership_at_issue: IdentityMembershipWitnessV1|null; fact_fingerprint: Sha256.
    Root/issuer rows have bootstrap authors and no author issuer; binding/grant rows bind the exact
    issuer fact. Root has no target role; issuer/binding require it. Grant requires issuance Membership
    and refers to its binding's reserved role. REVOKE retains both effective fields null. All other
    rows retain resolved nonempty intervals. Union discriminator must match stream kind. Physical
    storage remains the four distinct normalized tables; this transport is not a generic event store.
11. **IdentityCommandReceiptV1** — Identity-owned. Fields: version=1; root_id, fact_id, stream_id,
    idempotency_key: UUID; author_role_oid: Oid; revision: Revision; command_fingerprint,
    fact_fingerprint: Sha256; recorded_at: instant; result=APPENDED. An authorized identical retry
    returns this original receipt unchanged; no second row or replacement timestamp. Receipt keys
    are root + actual author role OID + idempotency key; hash includes the complete authored command.
12. **IdentityRequestBindingV1** — Identity-owned source binding. Fields: version=1;
    operation=CAPTURE_EXPLICIT_PLAN_INTENT; actor_user_id, household_id, tracked_member_id,
    request_id: UUID; request_revision: Count; horizon: frozen EPI horizon;
    request_utf8: text[49,152 bytes]; request_preimage_fingerprint: Sha256;
    environment=TEST_ONLY. Request revision0 remains valid exactly as in frozen EPI. The complete raw document must
    structurally contain the same context,
    revision, horizon and explicit TEST_ONLY environment. It may contain invalid axis values; those
    are EPI's decision. Duplicate keys/invalid document shape are rejected before authentication.
    The actual actor is reconstructed from session/enrollment and compared with actor_user_id.
13. **IdentityMembershipWitnessV1** — Identity-owned retained Household primitive. Fields:
    version=1; user_id, household_id: UUID; user_exists: bool; membership_id: UUID|null;
    membership_user_id, membership_household_id, actor_member_id: UUID|null;
    role=OWNER|EDITOR|VIEWER|null; actor_member_household_id: UUID|null;
    target_member_id, target_member_household_id: UUID|null; target_member_exists: bool|null.
    Exact observed fields, no display names, no claim of clinical/representative authority. Missing
    membership retains null row fields. Failed access redacts all target fields to null, including
    existence (not false). Grant issuance requires complete successful witness. Current witness must
    match the grant's pinned Membership ID/link/role, and both members must be in the same household.
14. **IdentitySourceFrontierV1** — Identity-owned. Fields: version=1; root_id, stream_id: UUID;
    kind=ROOT|ISSUER_DIRECTORY|BINDING|OPERATION_GRANT; revision: Count;
    head_id: UUID|null; head_fingerprint: Sha256|null; fact_count: Count;
    directory_fingerprint: Sha256|null;
    directory_entries: ordered tuple[(issuer_id UUID, revision Count, head_id UUID,
    head_fingerprint Sha256, fact_count Count)]. Directory entries must be empty except for
    ISSUER_DIRECTORY. Zero ordinary frontier has null head and zero count, witnessed by protected
    capture, not asserted by caller. Directory revision is the append counter for all issuer events;
    its head/hash refer to the last issuer event; directory_fingerprint separately binds the ordered
    entire directory (null for other kinds).
    Each issuer's full contiguous history must match its entry. Directory is complete for the root,
    including revoked issuers; no omitted favorable subset.
15. **IdentityCaptureFrameV1** — Identity-owned. Fields: version=1; root_id: UUID;
    deployment_context_id: Key; started_at, finished_at, transaction_started_at: instant;
    snapshot_id: text; session_start, session_end: IdentitySessionFactV1;
    frontiers: tuple[IdentitySourceFrontierV1]; total_fact_count: Count;
    environment=TEST_ONLY; transport=UNVERIFIED_TRANSPORT. Snapshot ID is actual retained MVCC
    descriptor, not a claim that replay has a live transaction. Start/end safety descriptors must
    agree; changes fail the whole capture. No password/token or unrelated source rows.
16. **IdentitySourceSnapshotV1** — Identity-owned. Fields: version=1;
    binding: IdentityRequestBindingV1; frame: IdentityCaptureFrameV1;
    root_history, issuer_history, binding_history, grant_history: tuple[IdentityRecordedFactV1];
    membership: IdentityMembershipWitnessV1|null;
    absences: ordered tuple[(kind ROOT|ISSUER|BINDING|OPERATION_GRANT|MEMBERSHIP,
    subject_id UUID)]; outcome=AVAILABLE_AT_RETAINED_CUT|UNAVAILABLE;
    reason=SOURCE_AVAILABLE|ROOT_EXPIRED|ROOT_REVOKED|ISSUER_EXPIRED|ISSUER_REVOKED|
    BINDING_EXPIRED|BINDING_REVOKED|GRANT_ABSENT|GRANT_EXPIRED|GRANT_REVOKED|
    AUTHORIZATION_DENIED; source_fingerprint: Sha256. AVAILABLE requires SOURCE_AVAILABLE and full
    witness; unavailable has no positive access witness or policy payload. Known original binding
    permits inspection of own history after revocation; unsafe/unbound/recreated principals get no
    snapshot. All histories include every selected stream row at the retained cut, including scheduled
    and revoked rows; issuer_history includes the complete issuer directory. No payload-owned limits.
17. **IdentityCaptureFailureV1** — Identity-owned. Fields: version=1; request_id: UUID|null;
    outcome=INVALID_INPUT|UNSUPPORTED|CAPTURE_REJECTED|SOURCE_CUT_INCOHERENT|RESOURCE_EXCEEDED;
    reason=INVALID_STRUCTURE|UNSUPPORTED_VERSION|UNSUPPORTED_DEPLOYMENT|AUTHENTICATION_FAILED|
    AUTHORIZATION_DENIED|WRONG_ROOT|INVALID_TRANSACTION|INCOMPLETE_SOURCE|CATALOG_CHANGED|
    LIMIT_EXCEEDED|CANCELLED; payload=null; environment=TEST_ONLY;
    transport=UNVERIFIED_TRANSPORT; numerical_use=NOT_ADMITTED;
    planner_ready=False; activation_ready=False. Fixed errors only, no raw source/SQL/credential leak.
    Missing evidence is not proof of a faithful negative source; a bare failure is NOT_CHECKABLE.
18. **IdentitySourceCheckV1** — Identity-owned immutable report, constructed by Validation.
    Fields: version=1; decision=CONSISTENT|INCONSISTENT|NOT_CHECKABLE;
    reconstructed_outcome=AVAILABLE_AT_RETAINED_CUT|UNAVAILABLE|null;
    reason=SOURCE_AVAILABLE|FAITHFUL_NEGATIVE|INVALID_AUTHORITY_HISTORY|INVALID_AUTHENTICATION|
    SUBJECT_MISMATCH|INCOMPLETE_SOURCE|FINGERPRINT_MISMATCH|INVALID_CLAIM|NO_SOURCE;
    checked_source_fingerprint: Sha256|null; checked_request_fingerprint: Sha256|null;
    check_fingerprint: Sha256; environment=TEST_ONLY; transport=UNVERIFIED_TRANSPORT;
    numerical_use=NOT_ADMITTED; planner_ready=False; activation_ready=False. Matching public hashes
    or a deserialized CONSISTENT report are never accepted instead of independent reconstruction.
19. **AuthenticatedPlanIntentInspectionV1** — **Policy-owned**, Planning-produced inspection carrier.
    Fields: version=1; source: IdentitySourceSnapshotV1|null; source_failure:
    IdentityCaptureFailureV1|null; source_check: IdentitySourceCheckV1|null;
    intent_result: frozen PlanIntentResolutionV1|null; intent_check:
    frozen PlanIntentCheckV1|null; outcome=SOURCE_AND_INTENT_CONSISTENT|UNAVAILABLE|REJECTED;
    reason=INSPECTION_COMPLETE|SOURCE_NON_SUCCESS|INTENT_NON_SUCCESS|INDEPENDENT_INCONSISTENCY;
    inspection_fingerprint: Sha256; environment=TEST_ONLY; transport=UNVERIFIED_TRANSPORT;
    numerical_use=NOT_ADMITTED; resolved_plan_policy_ready=False; planner_ready=False;
    activation_ready=False. Exactly source XOR source_failure; source requires a fresh source check;
    intent outputs exist only after source-consistent availability. An EPI invalid result is retained
    with its exact frozen checker result and yields INTENT_NON_SUCCESS. Positive inspection does not
    upgrade any frozen child's source-authority or transport flags, or admit any policy consumer.

The frozen PlanIntentResolutionV1 and PlanIntentCheckV1 types in item19 are the actual existing
registered classes; reference those identities without rename, replacement or duplicate re-export.
The additive manifest consists solely of the19 names in bold above.

## 2.1. Ownerless parameter ACL capture and reconstruction (ITR-D146-01)

This corrects contract4 only; it adds no contract name, SQL entry or authority. PostgreSQL's
[pg_parameter_acl catalog](https://www.postgresql.org/docs/18/catalog-pg-parameter-acl.html)
is cluster-wide and contains row OID, parameter name and ACL, without an owner. It omits parameters
using default privileges. An absent row therefore produces **no synthetic object fact or OID**.
Absence is meaningful only within the protected complete enumeration, never from an arbitrary
empty caller list. An actual ACL grantor OID, database owner or source owner is not a parameter owner.

**Enumeration.** At capture start and end retain the complete ordered pg_parameter_acl relation,
without filtering by actor, grantee, privilege or pg_settings visibility. Include rows for unloaded/
custom parameters as well. Order by canonical parname then row OID; expand each non-null paracl
with PostgreSQL's aclexplode into all (grantee,grantor,privilege,grantable) entries, ordered by those
four fields. Keep raw NULL distinct from an empty ACL and from no row. Names are PostgreSQL's
canonical stored names; no Python Unicode case folding or caller-selected alias determines identity.
The objects arrays include all these facts, and both boundary enumerations must match. Use the
existing catalog4096-object, source-byte/node/work/time bounds before accepting/expanding a complete
result; overflow, duplicate identities, unsupported ACL bits or inconsistent enumeration fails the
whole capture. Do not truncate, filter irrelevant-looking rows or load extensions to make rows vanish.

**Defaults, not ownership.** Pin reconstruction to the supported PostgreSQL18 semantics. In the
[18.4 parameter ACL evaluator](https://github.com/postgres/postgres/blob/REL_18_4/src/backend/catalog/aclchk.c#L3224),
no row gives ordinary roles no additional parameter ACL rights; superuser bypass is a separate role
attribute. A present row with paracl=NULL uses the built-in parameter default ACL; a present explicit
ACL uses its entries. The bootstrap-superuser identity used internally for this evaluation is **not**
an observed owner and must never populate owner_oid. Its default entry grants no PUBLIC parameter
ACL rights; inspect default generation independently in
[18.4 acldefault](https://github.com/postgres/postgres/blob/REL_18_4/src/backend/utils/adt/acl.c#L822).
No pg_default_acl/table-owner/creator-default fallback is applied to PARAMETER. The existing unsafe
superuser/bootstrap-role reachability checks still reject ordinary actors that could obtain those
intrinsic privileges; absence does not exempt them.

**Effective grants.** Reconstruct each SET and ALTER SYSTEM bit and its grant option separately from
the actual login role, PUBLIC (grantee0) and the complete inheritance-enabled role closure. A path
with INHERIT FALSE does not provide the current actor that ACL privilege. Separately retain/check
SET-role/admin escalation paths under the existing safe-role rules. PUBLIC WITH GRANT OPTION is
invalid, not synthesized. Preserve grantor OIDs and revocation effects; no owner-grant options are
invented for a parameter. PostgreSQL's
[GRANT rules](https://www.postgresql.org/docs/18/sql-grant.html) distinguish inherited permissions,
PUBLIC and grant options. V1 ordinary Identity actors must have no extra parameter ACL SET or
ALTER SYSTEM capability, directly, through PUBLIC or inheritance, including grant options. A real
new grant makes fresh capture fail the safe-role gate; revoking it removes that ACL capability but
does not renew any Identity enrollment. No grants are installed by this design correction.

**ACL rights are not all SET behavior.** User-context settings such as work_mem may be set by an
ordinary session without a parameter ACL grant. Backend/context and restart restrictions also
matter; ALTER SYSTEM permission alone is not proof that every value/change is operationally allowed.
[pg_settings context semantics](https://www.postgresql.org/docs/18/view-pg-settings.html) remain
separate from the ACL check. Default session-setting behavior is not a manufactured ACL entry,
Identity operation grant or source-authority proof, and the protected path still enforces its own
session/timeout/search-path requirements. This slice does not promise arbitrary configuration control.

**Independent proof.** Validation reconstructs ownerlessness, NULL/default/explicit ACL treatment
and effective role closure from retained primitives, not producer booleans or matching fingerprints.
Real-PG ITR018 compares replay to has_parameter_privilege(actual_login_oid, parname, privilege),
including WITH GRANT OPTION variants; never use the implicit current_user overload in SECURITY
DEFINER, where it would check the source owner. That SQL function is an independent test oracle,
not a substitute for the pure checker. Capture cannot prove origin after serialization: coordinated
replacement of a complete catalog and all hashes retains the existing UNVERIFIED_TRANSPORT limit.

## 3. Source selection, verification and invariants

Selection is explicit root + actual principal's binding + exact operation/household/member grant.
No latest-root/provider fallback or current-member inference. At most one applicable binding and
grant may be active at the cut; conflicting streams fail closed, not aggregated. Writes prevent
ambiguous overlapping authority while retaining all history. Root/issuer/binding/grant validity is
required at cut time, and at each historical authoring time/entire delegated interval. A scheduled
renewal cannot repair a past gap; a terminal revocation wins over future rows. Role OID/name must
match the original immutable binding, not only its most recent renewal. Revalidate User existence
and active Membership pins on capture; deletion of anchors never silently transfers authority.

Bootstrap root and issuer commands retain actual administrative author evidence. Ordinary issuer
commands retain complete root/issuer authority and exact new target role/subject facts. Offline
Validation checks those observations as retained evidence, not as an actual new DB login. It cannot
prove a wholly fabricated but internally coherent database history is canonical. An ordinary login
cannot supply a fake author_session to SQL: observed fields and recorded_at are generated inside
the protected path, with no command override parameter.

## 4. Canonical fingerprints and APIs

New command/fact/source/check/inspection hashes use:
H(tag,value) = SHA256(UTF8(tag) || NUL || canonical-JSON(value)).
Tags are respectively identity.command.v1, identity.fact.v1, identity.source.v1,
identity.check.v1 and policy.identity-inspection.v1. Canonical JSON sorts object keys by their UTF-8
byte order, emits UTF-8 without ASCII escaping, no whitespace/NaN/float, and preserves array order.
Normalize UUID/time only through the strict typed boundary. Exclude only the object's own fingerprint
field, not other claims. Command hash includes CAS, idempotency key and complete evidence preimage.
Fact hash binds complete authored and server-observed preimages and prior link. Source hash binds
frame, complete histories, raw request and absences. The separate request-preimage fingerprint is
SHA256(UTF8('identity.request-preimage.v1') || NUL || exact original request UTF-8 bytes); it does not
replace frozen EPI's canonical semantic fingerprints. Full golden vectors for PostgreSQL/Python
Unicode, escaping, arrays and timestamps are mandatory before implementation acceptance.

Proposed interfaces (not implemented):

- Identity SQL entry functions named in the main design accept only typed authored commands or the
  request binding. Actual session/role/DB facts are reconstructed internally. No source injection.
- Identity capture facade takes a caller-owned actual clean read-only connection, server-owned
  deployment context and complete request binding. Returns Snapshot OR CaptureFailure atomically.
- Validation check_identity_source_v1(snapshot_or_failure, expected_binding) is pure; reconstructs
  source/result from primitives and does not call Identity's evaluator. A failure alone produces
  NOT_CHECKABLE, not authenticated absence. Expected binding is compared, not treated as authority.
- Planning inspect_explicit_request_source(connection, deployment_context, request_binding) always
  captures anew, independently checks Identity and frozen EPI, and returns the Policy carrier above.
  It accepts no supplied source, report, token or checker callback. No consumer/admission API.

The server-owned deployment context pins endpoint/TLS/root/database and absolute limits; it is
configuration of the trusted engine, not an exported credential/bearer contract or caller override.
No mutable environment lookup changes authority during pure replay. Replay uses only retained inputs.

## 5. Compatibility and review stop

Future additive target: **556 =537 retained +19 proposed**. Current export remains537. Add a full
537-body/hash fixture from the approved implementation base and the literal19-name manifest before
new registration. Preserve all older515/503 hashes,53 frozen files,59 PIV pins and baseline4611 tests.
Existing count/name/import guards need a separately approved exact patch inventory, not a weakened
subset comparison. No fixtures, runtime or SQL are changed by this design.

All proposed outputs remain TEST_ONLY/UNVERIFIED_TRANSPORT/NOT_ADMITTED. They do not authorize
clinical content, plan activation, PIV numerical use, defaults/override precedence, another member's
goal, generic login endpoints or full ResolvedPlanPolicy. Independent security review must approve
the19 contracts and their source disclosure/privacy semantics before implementation authorization.
