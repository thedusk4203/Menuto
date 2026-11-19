# Identity shared-public sslinfo: routine classification preflight blocker

**BLOCKED / NO IMPLEMENTATION PR / NO NEW CI / NOT MERGED / NOT FROZEN / PRODUCTION GATE CLOSED**

## Authorization and unchanged baseline

Canonical main was re-fetched at `68fcb688231460f1973077eb20140b8c5db440a2`.
[Owner namespace authorization6937420352](https://github.com/thedusk4203/Menuto/pull/148#issuecomment-6937420352)
was read in full. It permits the namespace-specific substitution of exactly two TLS grants and the
corresponding Identity-local resolver/helper. It explicitly does **not** authorize “loosening routine
classifier”. No source, helper, SQL, grant, contract, historical test or fixture was changed during
this diagnostic. No production database was accessed. No proposed TLS correction was installed.

The earlier raw namespace report `IDENTITY_SHARED_SSLINFO_NAMESPACE_IMPLEMENTATION_BLOCKER.md`
remains unchanged. This is a distinct follow-on preflight finding, not a rewrite of that evidence.

## Actual PostgreSQL diagnostic

A new disposable SCRAM/TLS verify-full loopback cluster running actual PostgreSQL18.4 was created.
Two separate databases used the unchanged frozen migrations through0017:

1. Native `sslinfo` installed by frozen migrations in `menuto_prior`.
2. Native `sslinfo` preinstalled in `public`, then frozen migrations installed through0017.

No catalog mutation, classifier bypass or Identity grants were used. The probe queries actual
`pg_extension`, `pg_namespace`, `pg_proc`, `pg_language`, `pg_roles` and `pg_depend`, retaining raw
function/schema ACLs and extension membership. Both database objects and the cluster were cleaned
up in finally blocks. The two passing diagnostics prove the measured catalog difference; they do
**not** prove dual-layout Identity TLS/security acceptance or a full regression pass.

| Actual fact | menuto_prior layout | public layout |
|---|---:|---:|
| PostgreSQL version |18.4|18.4|
| sslinfo native version |1.2|1.2|
| extension OID |19533|20883|
| extension namespace OID |19532|2200|
| native ssl_is_used() OID |19535|20885|
| extension/function owner OID |10|10|
| public routine count |68|78|
| genuine sslinfo function members |10|10|
| unchanged exact68 public inventory predicate |true|false|

OIDs are environment-specific observations, not globally pinned constants. The native function is
C-language `$libdir/sslinfo`, symbol `ssl_is_used`, zero-argument boolean-returning SECURITY INVOKER;
its actual `deptype=e` pg_depend edge points to the measured extension. Extension and function owners
are the same actual disposable administrator superuser. Native owner and member identity are genuine,
so a spoofed wrapper is not the explanation for the public inventory difference.

The ten additional public routines are:

- `ssl_cipher()`
- `ssl_client_cert_present()`
- `ssl_client_dn()`
- `ssl_client_dn_field(text)`
- `ssl_client_serial()`
- `ssl_extension_info()`
- `ssl_is_used()`
- `ssl_issuer_dn()`
- `ssl_issuer_field(text)`
- `ssl_version()`

All ten have actual native extension membership and PUBLIC EXECUTE in this default native install.
Existing ACLs were observed, not changed or reclassified as safe. A genuine extension member label
alone has not been accepted as a blanket capability safety proof.

## Exact unchanged predicates and inference

The uncommitted Identity migration `0018_identity_principal_user_sources.py` at lines1746–1773
collects **all** pg_proc rows in public and requires count and name set to equal its68-entry
`LEGACY_PINS`. The diagnostic executes the same inventory SQL against both real layouts and proves
the count/name-set predicate false for the public layout. The extra OID set exactly equals the ten
extension-member function OIDs; no unknown additional routine accounts for the difference.

The migration's failure message for this predicate is:

```text
Identity historical routine identity inventory mismatch
```

This message is a **statically identified next failure**, not a claimed observed exception from a
patched migration: the current earlier namespace guard has not been bypassed or patched. Correcting
only that TLS guard would still leave the actual false inventory predicate. The runtime SQL
`_safe_role_v1` (lines761–771) also requires the exact public68 set and rejects unknown rows with42501.
The pure producer replay (`source_replay.py`, lines125–141) independently requires that exact set.
Validation-owned checker (`validation/identity_source.py`, around lines613–625) separately enforces
it as well. Changing only install-time count cannot resolve the full trust boundary.

Therefore completing a successful public-layout Identity installation/capture requires a separately
reviewed classification decision beyond the allowed namespace substitution. Silently filtering the
native functions, treating SECURITY INVOKER as sufficient, changing68 to78, expanding a manifest
without individual capability proof, ignoring PUBLIC EXECUTE, or weakening independent checking
would exceed the current authorization. None was done.

## Execution receipts and limits

The final corrected diagnostic invocation was:

```text
C:/PERSONAL1/Menuto/.venv/Scripts/python.exe .local/run_identity_acceptance.py identity-shared-namespace-preflight-2 .local/test_identity_namespace_preflight.py -o junit_family=xunit1
```

Final diagnostic: **2 passed /0failed /0errors /0skips**. An initial attempt failed because its
probe incorrectly passed PUBLIC as a role name to has_function_privilege (42704); the probe alone
was corrected to inspect aclexplode grantee0, then both cases were rerun. Those attempts are not
added together and do not count as ITR acceptance. No runtime or historical test was corrected.

Full historical reference-prior regression, dual-layout Identity TLS positive/negative, downgrade
ACL restoration, full ITR/full regression and exact-head CI have **not** passed under a namespace
correction; there is no such source correction yet. The previous focused88PG/57pure/16architecture
results and earlier8pass+8setupERROR smoke remain historical partial evidence, not full acceptance.

## Preservation and required decision

Read-only verification confirmed all19 original local file hashes, originalHEAD and status unchanged;
all185 canonical runtime/migration file hashes unchanged; all537 baseline export bodies unchanged;
556 draft exports remain537+19. No frozen pin/fixture, old migration, privilege, role, routine or
persistent source was changed by this task. Existing uncommitted Identity work remains protected.
No commit, push, implementation PR, merge or freeze was performed.

The exact remaining authorization prerequisite is an architecture/security decision for classifying
and independently verifying the native extension routines in the public layout across install SQL,
protected SQL, producer replay and Validation. It must preserve the68 historical pins, raw catalog/ACL
completeness, fail-closed unknown functions, and individual capability/dependency safety proof. This
report does not select or implement that design, request blanket privilege, or reuse a positive trust
label as authority.

Production Nutrition/clinical gate CLOSED; fullMTR006/007/008 INCOMPLETE; issues5/6/7 remainOPEN;
planner_ready=False;activation_ready=False;ExecutionNOTSTARTED;PRECOMMITFAIL-CLOSED.

## Raw local artifacts

These are author-executed local diagnostic artifacts, not independent review receipts or CI:

- `.local/test_identity_namespace_preflight.py` — SHA-256 `893959c2092ccb2948236793f5292bf860e92be3c3a4fb47ac2d07749ab0ef3d`
- `.local/identity-shared-namespace-preflight-2/results.xml` — SHA-256 `7020e90266420e39cf6da8c4d3e9cfcd96f43aea74ea16e1b301cf353e714b5e`
- `.local/identity-shared-namespace-preflight-proof/menuto_prior.json` — SHA-256 `518cd6f1d0d77bd058193f19414e0dc9e78fb2824486297bb7acfbf03cd117d2`
- `.local/identity-shared-namespace-preflight-proof/public.json` — SHA-256 `8f0477d3c670ab6ddf17ec6d683c0a12a5e0dd7ff65f418cbd9088ff42b82a27`
