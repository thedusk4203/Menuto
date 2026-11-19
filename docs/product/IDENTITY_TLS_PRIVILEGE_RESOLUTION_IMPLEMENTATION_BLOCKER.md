# Identity TLS exception resolution and implementation blocker

Status: TLS PRIVILEGE BLOCKER RESOLVED / IMPLEMENTATION BLOCKED ON REAL-PG FUNCTION-PRIVILEGE CLASSIFICATION / NOT SUBMITTED / PRODUCTION GATE CLOSED.

## Canonical baseline and scope

GitHub main was re-read and remains `120d28f62b66720e8631b64e0b2a50cdc57e6c42`.
Implementation worktree/branch: `codex/identity-source-implementation`, based on that exact commit.
No commit, push, implementation PR, merge, freeze or production deployment has occurred.
This is local diagnostic evidence, not full implementation acceptance or independent approval.
Owner authorization: https://github.com/thedusk4203/Menuto/pull/147#issuecomment-6904787639.

## Exact authorized native TLS grants

```sql
GRANT USAGE ON SCHEMA menuto_prior TO menuto_identity_source_owner;
GRANT EXECUTE ON FUNCTION menuto_prior.ssl_is_used() TO menuto_identity_source_owner;
```

The local additive migration draft is `0018_identity_principal_user_sources.py`, down-revision `0017` after verifying the singleton migration DAG. It installs six private Identity tables, one sequence, seventeen functions (five protected entries and twelve private helpers), and four NOLOGIN infrastructure roles. Fresh disposable installation has108 public domain tables plus6 private Identity tables =114, excluding Alembic metadata. Canonical main is still0017/108; the draft is not merged or installed outside disposable tests.

No third native TLS privilege was granted. The four separately approved anchor-table SELECT grants and Identity infrastructure/entry grants are distinct from this two-grant native exception.

## Executed TLS evidence

`.local/identity-tls-authorized-proof-3/evidence.json` records the completed native PostgreSQL18.4 TLS proof:

- Native `sslinfo` extension membership, namespace and owner verified through pg_extension/pg_proc/pg_depend/pg_language.
- Proof-cluster extension OID19533, namespace19532, native function19535, owner10. These are observed disposable identities, not deployment constants.
- C language, `$libdir/sslinfo`, `ssl_is_used`, bool return, zero arguments; source-owner NOLOGIN/no elevated attributes/no inherited memberships.
- Original missing-native-access failure SQLSTATE42501. Effective `(schema USAGE,function EXECUTE,pg_read_all_stats)` changed `(false,false,false)` to `(true,true,false)` using exactly the two grants.
- SQL BEGIN ATOMIC directly binds the schema-qualified primitive by OID; no `menuto_prior.backend_tls()` or another domain's private helper.
- TLS true/false observed; plaintext requester denied42501 including loopback; actual `system_user` SCRAM principal checked; SET ROLE, wrong password, wrong CA and wrong hostname rejected.
- All35 protected prior functions and all7 prior-owned source tables remain inaccessible to the Identity owner; actual denied calls/SELECT/INSERT/DELETE recorded. Actual prior-owned sequence count is0.
- Exact two REVOKEs restored original native ACLs; extension/function identities retained.

`.local/identity-migration-proof-1/evidence.json` additionally proves the ACTUAL new migration helper (not only a test wrapper):

- Six empty tables /114 domain tables; no actor/source/content seeds.
- Actual SECURITY DEFINER helper under NOLOGIN owner returns TLS true and false on encrypted/plaintext sessions.
- All35 prior protected functions and7 prior source tables still denied.
- Empty downgrade to0017 succeeds, removes only new Identity objects/roles created by that install and retains the shared sslinfo extension/native function OIDs.

The actual bootstrap entry also appended a root/receipt successfully in `.local/identity-install-proof-5.log`. Every disposable cluster was stopped.

## New real-PostgreSQL blocker

Reproduction: `.local/identity-callability-proof-final.py`, output `.local/identity-callability-proof-final.log`, observed catalog `.local/identity-callability-proof-final/public_function_catalog.json`.

With actual SCRAM/verify-full TLS logins and exact entry-group edges `(INHERIT TRUE,SET FALSE,ADMIN FALSE)`, actual root initialization succeeds. Bootstrap issuer enrollment then fails:

```text
SQLSTATE 42501: Identity unsafe privilege
_safe_role_v1(oid,text) -> _append_receipt_v1(text,jsonb,jsonb) -> change_issuer(text)
```

Directly verified facts:

- Existing frozen migrations expose68 functions in public through PUBLIC EXECUTE, all SECURITY INVOKER (`prosecdef=false`).
-41 return trigger. Actual ordinary call of `public.menuto_recipe_begin_version()` is rejected by PostgreSQL with0A000: trigger functions can only be called as triggers.
-27 have other return types. Actual ordinary call of `public.menuto_preference_canonical('{}'::jsonb)` succeeds and returns `{}`; PUBLIC EXECUTE is therefore not merely theoretical.
- Current NEW Identity SQL classifier treats any accessible non-Identity function EXECUTE as unsafe. The new pure producer and independent checker use the same conservative classification rule independently. This prevents ordinary issuer enrollment on the genuine baseline.

Assessment (not an established defect in a frozen source): the current implementation classifier is too broad to distinguish harmless inherited baseline invoker/trigger execution from a function permission that actually conveys unsafe authority. This is NOT another missing sslinfo permission and NOT evidence that these68 frozen functions are vulnerabilities.

The approved retained `IdentityPrivilegeObjectFactV1` carries OID/name/owner/raw ACL/definition fingerprint, but does not carry the definition preimage, return kind or SECURITY DEFINER/invoker mode. A fingerprint alone cannot let an independent replay checker reconstruct that distinction.

The decision requiring review is the exact safe-function classification and its independently checkable retained evidence. Do not silently exempt all PUBLIC functions, trust an unproved hash/label, filter away unfavorable ACLs, introduce an implicit name allowlist, revoke legacy PUBLIC rights, or modify frozen migrations. Any necessary contract/trust-boundary correction needs explicit review before changing the approved source semantics. No additional privilege has been requested or applied.

## Compatibility and unfinished work

Read-only/in-memory checks at stop:

-537 existing registered exported definition bodies retained exactly; adding the proposed19 models in memory produces exactly556 with the independently authored19-name manifest. Generated exports/registration have NOT been changed.
-515 legacy and503 historical definition hashes checked;53 frozen files and59 PIV pins checked byte-for-byte against unchanged fixtures.
-All17 old migration files match their baseline SHA-256.
-Original checkout HEAD remains1679d6035dd6685118df6c95fa37628384cc961c; exactly19 original local modified/untracked files, every file SHA-256 unchanged.
-No tracked baseline file has been edited in the isolated worktree; all implementation changes remain new, uncommitted drafts. The35 historical compatibility patches have not been applied.

`.local/identity-blocker-compatibility-evidence.json` retains the exact implementation file hashes and preservation inventory.

NO claim is made that ITR001–ITR096,48 PG groups/P1–P7, full regression, SCRAM smoke suite, benchmarks, client/web or exact-head implementation CI have passed. The standalone native/migration diagnostic runs are not counted as completed ITR obligations. The last approved4611-test main baseline remains historical evidence, not a new implementation full-suite pass.

19 contracts, source replay/checker, migration and capture/inspection code exist as unfinished drafts. Additional implementation/testing remains; they are not review-ready. No implementation PR has been opened while the real-PG path is blocked.

## Preserved governance

Frozen Root/NPS/NRE/MBA/PIV/EPI semantics and identities remain unchanged. Full MTR-006/007/008 INCOMPLETE; issues5/6/7 not modified. Production Nutrition/clinical gate CLOSED; planner_ready=False; activation_ready=False; Execution NOT STARTED; PRECOMMIT FAIL-CLOSED. No content, scientific conversion, solver, downstream work, merge or freeze.
