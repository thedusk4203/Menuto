# Identity trust-root — future acceptance and PostgreSQL matrix

Part of the [bounded design](IDENTITY_PRINCIPAL_USER_ENROLLMENT_BOUNDED_DESIGN.md).
**96 future obligations; none implemented or executed by this docs-only PR.**

## Execution rules

ITR001–ITR048 are **48 individually identifiable mandatory real PostgreSQL test items**.
Each runs against disposable PostgreSQL18 with actual protected SQL entry points and distinct
administrator/issuer/requester credentials. Tests of failed authentication use actual attempted
connections. Privilege tests execute as the actual ordinary role, not source owner with a mocked
principal. Parameter expansion may increase actual executions; report item/node IDs and observed
counts separately. Mocks, collection, SQL text matching and labels do not satisfy these48.

ITR049–ITR080 are32 pure/adversarial obligations; ITR081–ITR096 are16 static/compatibility/delivery
obligations. A row can require multiple assertions or parametrized cases; do not invent a future
full-suite count from96. Retain4611 existing tests with zero skips. Temporary admin/issuer/requester
fixtures are explicitly TEST_ONLY, created by authenticated test setup and never production seeds.
Fault injection belongs to controlled disposable test setup, never ordinary runtime permissions.

## Mandatory real PostgreSQL obligations

| ID | Boundary | Required executed proof |
|---|---|---|
| ITR001 | Fresh install and downgrade | Install proposed forward migration into empty real PostgreSQL; all six tables have zero rows, correct constraints/entry grants; populated-history downgrade refuses loss. |
| ITR002 | Bootstrap root | Actual dedicated SCRAM/TLS administrator initializes exactly one TEST_ONLY root, captures actual DB/role identity and immutable receipt; duplicate active root denied. |
| ITR003 | Administrator/issuer separation | Ordinary issuer/requester cannot initialize root or enroll issuers; bootstrap cannot use ordinary binding/grant/capture paths. |
| ITR004 | Privileged requester rejection | Superuser, database owner and private object owner fail ordinary issuer/requester calls despite otherwise matching UUIDs. |
| ITR005 | Issuer enrollment and exact User | Bootstrap enrolls issuer, issuer enrolls one existing requester User; nonexistent User/unknown role/unsafe target cannot become a binding. |
| ITR006 | Alias and role reservation | Same User under issuer/requester aliases denied; second active requester binding and rebinding reserved role/name to another User denied. |
| ITR007 | Positive scoped capture | Real ordinary requester login, exact positive grant and OWNER/EDITOR linked membership yield complete source at retained cut, fresh independent CONSISTENT check and non-admitting EPI inspection. |
| ITR008 | Actual wrong password | A real new connection with wrong credentials fails authentication; no source snapshot or actor-by-UUID fallback. |
| ITR009 | Actual trust rejection | Disposable trust-authenticated TCP login is rejected by protected entry despite matching session_user/role/User. |
| ITR010 | Actual non-SCRAM rejection | Disposable actual password-method session is rejected; test actual negotiated system_user rather than only HBA file text. |
| ITR011 | Actual TLS requirement | Otherwise valid non-TLS source session is denied, including loopback. |
| ITR012 | Verified endpoint | Trusted client verify-full rejects wrong CA/hostname before protected source use; server TLS flag cannot replace client endpoint verification. |
| ITR013 | SET ROLE spoofing | Ordinary principal under SET ROLE and inherited unsafe membership cannot impersonate a source actor; actual login remains pinned. |
| ITR014 | SET SESSION AUTHORIZATION spoofing | Privileged session adopting requester session authorization cannot pass original authenticated-identity/ordinary-role guards. |
| ITR015 | Role recreation | Drop and recreate same login name, new OID: old binding and all grants fail; no name-only fallback. |
| ITR016 | Role rename | Rename original role and reuse old name with another OID: both fail original binding until separately authorized fresh enrollment. |
| ITR017 | Database/root identity | Clone/restore with wrong actual database OID/name or wrong pinned root/endpoint fails; copied root UUID/hash not enough. |
| ITR018 | Privilege graph closure | Unsafe direct/inherited CREATEROLE/CREATEDB/BYPASSRLS/replication/ownership/owner-SET reachability denied, not hidden by benign immediate role. Extend within this same PG obligation with contract section2.1 catalog cases: actual ownerless parameter rows/default absence, direct/PUBLIC/INHERIT TRUE SET and ALTER SYSTEM grants plus grant options, INHERIT FALSE control, grant/revoke mutation and explicit-login has_parameter_privilege parity; compare producer capture and independent reconstruction, including benign no-extra-rights positive capture. No synthetic parameter owner/OID or inferred zero total SET authority. |
| ITR019 | No direct source access | Ordinary issuer/requester/PUBLIC cannot SELECT/DML history/frontier/receipt/sequence or invoke private helpers; only exact protected entry functions execute. |
| ITR020 | Shadowing resistance | Malicious temp/public objects and overloads cannot change protected lookup or escalate source owner; fixed search_path/qualified base reads hold. |
| ITR021 | Scope issuance authority | Issuer must be active at DB recorded_at and cover complete delegated interval; overlong or retrospective grants and inappropriate operation/wildcards rejected atomically. |
| ITR022 | Foreign scope | Foreign household/target, target outside household and caller-substituted actor/body context never yield a positive source or foreign private facts. |
| ITR023 | Membership eligibility | VIEWER/no membership/unlinked actor member/deleted User fail closed; Membership by itself cannot authenticate an unbound caller. |
| ITR024 | Membership pin change | Changed role/link or deleted/recreated Membership ID invalidates grant; same observed facts may remain valid, without claiming unseen historical changes. |
| ITR025 | Operation isolation | Exact CAPTURE_EXPLICIT_PLAN_INTENT grant does not allow goal/physiology writes, enrollment, another member scope or financial execution. |
| ITR026 | Root revocation | Bootstrap terminal root revoke disables fresh descendant capture; scheduled rows and copied receipts do not resurrect it. |
| ITR027 | Issuer revocation | Bootstrap issuer revoke disables descendant binding/grant freshness without rewriting them; later issuer enrollment cannot repair old unauthorized commands. |
| ITR028 | Binding revocation | Issuer revokes own bound requester stream; fresh capture unavailable, own faithful negative independently consistent, no new positive witness. |
| ITR029 | Grant revocation | Exact grant revoke terminal; future renewal/pinned old result cannot authorize fresh capture, unrelated granted scope unaffected. |
| ITR030 | Expiry without REVOKE | Root/issuer/binding/grant finite expiry denies fresh source use without revoke; each expired ancestor independently exercised. |
| ITR031 | Credential expiry and reset | Already-connected login past rolvaliduntil denied by source check; password reset or extended validuntil does not renew source interval or revive revoked binding. |
| ITR032 | Renewal cannot repair past | Later issuer/binding/grant renewal cannot backdate or validate commands recorded during an authority gap; original intervals and receipts unchanged. |
| ITR033 | Future-effective renewal | Current interval remains until boundary; adjacent renewal begins at boundary, explicit gap unavailable, overlaps rejected, terminal revoke wins scheduled future interval. |
| ITR034 | Concurrent CAS | Two real writer sessions race same revision; exactly one complete event/frontier/receipt transition, deterministic conflict for loser, no duplicate revision. |
| ITR035 | Idempotency | Authorized identical retry returns original receipt; changed body/evidence/CAS under same actual-actor key conflicts, no added event. |
| ITR036 | Revoked issuer retry | Revoke/expiry observed after lock and before receipt lookup blocks old identical command retry; receipt possession does not restore authority. |
| ITR037 | Atomic failure | Constraint/forced test transaction error rolls back event, frontier and receipt together; no hidden commit and no partially usable history. |
| ITR038 | Read-only transaction shape | Capture requires actual clean RR/SERIALIZABLE read-only transaction; READ COMMITTED, writable, begun/dirty mutation transaction rejected. |
| ITR039 | No cache or split capture | Actual facade rejects dirty ORM/autoflush, cached-source injection and split-engine/session capture; cannot claim common MVCC from matching hashes. |
| ITR040 | Coherent cut | Concurrent membership/source mutation during RR capture produces one faithful cut or whole-cut failure; no mixed favorable rows. Include concurrent parameter GRANT/REVOKE and unchanged-catalog control: retain complete cluster-wide enumeration at both boundaries, reject an observed ACL/OID/role-closure change and require fresh post-commit capture to reflect changed privileges; an earlier retained cut never authorizes new work. |
| ITR041 | Fresh versus retained revoke | Revoke committed before first fresh snapshot denies it; earlier RR cut replays only historical authority and cannot be submitted for new live inspection/admission. |
| ITR042 | Complete source and absences | Return contiguous own histories plus complete issuer directory, selected frontiers and protected zero absences; omission/overflow never positive prefix. Parameter catalog enumeration includes all rows, even PUBLIC/other-grantee and unloaded-custom names; missing pg_parameter_acl row is a complete-enumeration default case, not a synthesized owner/OID or dropped unfavorable row. |
| ITR043 | Privacy | Other requester bindings/households/member histories, display names, passwords/verifiers never returned; denied target fields redacted including existence. |
| ITR044 | Server limits | Real byte/row/history/role-closure bounds cause whole error, zero partial snapshot and no caller-raised limits. |
| ITR045 | Timeout and cancellation | Real lock/statement timeout and client cancellation do not leave committed writes or usable partial capture; caller rollback/config restoration and no unsafe reuse verified. |
| ITR046 | Complete request preimage | Real capture binds exact raw request and actor/household/member/revision/horizon; public fingerprints cannot substitute or change principal. |
| ITR047 | Authenticated invalid intent | Actual source-valid request with invalid EPI semantic value retains frozen child non-success; no authenticated-plan or numerical-use claim. |
| ITR048 | Unrelated authority rejected | Only Nutrition/PIV/prior/hierarchy grants without Identity enrollment cannot call Identity source; no PIV lease/purpose extension or production content installation. |

## Pure, replay and adversarial obligations

| ID | Boundary | Required proof |
|---|---|---|
| ITR049 | Strict parsing | Booleans-as-int, float, extra/missing keys, invalid UUID/OID/time/UTF-8, duplicate keys and unsupported versions fail deterministically before semantic use. PARAMETER requires owner_oid=null; all genuinely owned kinds require non-null real OID. Reject owner0, fabricated parameter owner, non-PARAMETER null owner/ACL and PARAMETER privilege outside SET/ALTER SYSTEM. |
| ITR050 | Raw versus semantic identity | Whitespace/key-order changes alter raw preimage identity; frozen EPI semantic hashes remain their own protocol, no equality-based source shortcut. |
| ITR051 | Golden vectors | Exact Unicode/escaping/time/ordered-array fingerprint vectors match independently authored PostgreSQL/Python expectations; full-source not visible-row hash. Include ownerless parameter ACL explicit/empty/NULL and absent-row vectors; raw ACL grantor/PUBLIC/bit/grant-option distinctions must remain bound, not normalized into an imaginary owner or identical preimage. |
| ITR052 | Replay determinism | Same complete retained source plus binding yields same report without DB/network/filesystem/clock/environment/producer callbacks. |
| ITR053 | Historical author interval | Expired issuer at recorded_at or failure to cover entire delegated interval rejected, including fully rehashed later renewal history. |
| ITR054 | Terminal lifecycle | Future renewal, gap, ancestor expiry and terminal revoke independently reconstructed; no prior-state resurrection or latest-row-only logic. |
| ITR055 | Role graph reconstruction | Forged omitted privilege edge/default ACL/owner privilege detected from retained complete primitives; unsupported catalog shape fails closed. Independently replay ownerless parameter NULL/default/explicit cases and PUBLIC/inherited SET/ALTER SYSTEM plus grant options against ITR018 actual-catalog vectors. Fully rehashed fabricated owner, removed grant, forged absent row relative to retained boundary facts or omitted inherited edge cannot yield a safe positive; preserve fully coherent replacement/non-origin limitation. |
| ITR056 | Principal substitution | Rehashed role OID/name/database/User/issuer alias substitutions relative to primitive observations produce INCONSISTENT, not positive witness. |
| ITR057 | Complete directory | Missing issuer/stream row, conflicting head/count, duplicate revision, broken predecessor or omission of revoked issuer fails completeness. |
| ITR058 | Absence witness | Zero frontier distinct from empty favorable subset, missing head or truncated source; no authority from caller-declared absence. |
| ITR059 | Faithful negatives | Faithful expired/revoked/absent-scope source yields CONSISTENT with reconstructed UNAVAILABLE/NOT_ADMITTED, not positive payload. |
| ITR060 | Forged positives | Same unavailable primitives plus fully rehashed positive source/inspection/witness/report are INCONSISTENT and NOT_ADMITTED. |
| ITR061 | Coherent total forgery | Self-consistent replacement of all source primitives may be offline consistent but remains UNVERIFIED_TRANSPORT; live inspection takes no source/report argument. |
| ITR062 | Bare reports | Forged CONSISTENT label/matching hashes or bare CaptureFailure without primitives NOT_CHECKABLE or INCONSISTENT, never origin/admission. |
| ITR063 | Request subject | Actor/household/member/request ID/revision/horizon tampering or cross-member copy relative to retained source rejected after rehash. |
| ITR064 | Context versus axis ownership | Identity binds structural context only; invalid precision/cost/effort/budget remains EPI semantic failure and cannot be hidden by valid authentication. |
| ITR065 | Authority time | Caller declared_at/request_revision cannot set recorded time/frontier/CAS or extend source validity; retained cut not current-time authorization. |
| ITR066 | Catalog changes | Start/end login/database/privilege descriptor differences fail incoherent cut; no partial success or retained catalog-origin overclaim. Include parameter-row creation/deletion, ACL mutation, NULL/empty changes and inherited permission changes, even when only another database in the cluster issued the parameter GRANT/REVOKE. |
| ITR067 | Mutable Membership limits | Observed role/link/ID mismatch denied; unchanged observed row does not prove no intervening change, explicit Identity revocation remains terminal. |
| ITR068 | No role-name heuristic | Name prefix, UUID convention, fixture label or matching root hash without authoritative primitive history insufficient. |
| ITR069 | Operation bounds | Wildcard/cross-household/goal/physiology operation and altered grant Membership pins rejected independently. |
| ITR070 | Non-success ordering | Fixed precedence and redacted codes stable; access failure not clinical conflict, hard-policy infeasibility or safe/unrestricted default. |
| ITR071 | Bounds before work | Byte/depth/integer/history/node limits apply before expensive parse/hash/graph replay, all-or-error with fixed work counter. |
| ITR072 | Cancellation replay boundary | Interrupted work produces no reusable positive result or silently restored authority; retained complete result not transferable admission. |
| ITR073 | Strict TEST_ONLY | Taint stripping/PRODUCTION label, fabricated production root or unqualified source cannot be admitted; no numerical/clinical authority. |
| ITR074 | No EPI upgrade | All frozen child source/transport/readiness literals retained exactly; authenticated companion does not mutate or reinterpret them. |
| ITR075 | Money independence | Retained frozen money/currency/explicit-zero/NONE/TARGET/SPEND_LIMIT/orthogonal axes regression remains unchanged under inspection. |
| ITR076 | No bearer lifecycle | Inspection report cannot be used as token/lease, consume/reissue PIV purpose, grant source reads or authorize fresh operation. |
| ITR077 | Independent checker | Identity producer wrong-result fault injection detected by independently reconstructed checker, no shared authority-state evaluator. |
| ITR078 | Immutable complete contracts | All19 future types strict/frozen/versioned, model-constructed/tampered nested instances revalidated; no naked author_session override. |
| ITR079 | Source privacy shaping | Negative access witness redacts target even existence; only own source plus issuer authority metadata allowed, secrets rejected. |
| ITR080 | Historical versus current claim | Valid old cut plus newer revocation stays historical-only; cannot be relabeled fresh by timestamp/fingerprint/report replacement. |

## Static, compatibility and final-delivery obligations

| ID | Boundary | Required proof |
|---|---|---|
| ITR081 | 537-body baseline | Verify every existing537 exported definition body/hash identical to approved base; no removals/renames/replacements. |
| ITR082 | Exact19-name manifest | Exact set difference equals separately authored19-name manifest, proposed total556; never derive expected names from actual exports. |
| ITR083 | Historical pins | Retain515 legacy and503 historical definition hashes,53 frozen source/migration files,59 complete PIV pins byte-identical. |
| ITR084 | Baseline test identities | All4611 retained test identities and EPI001–EPI064 remain; no skip/xfail/delete, no summed focused runs as full pass. |
| ITR085 | Identity ownership | Identity public/source modules import no Nutrition/PIV capability or Policy business evaluator; Household anchors accessed through proposed exact protected path. |
| ITR086 | Validation independence | Validation imports immutable contracts/primitives only, not Identity producer/replay, source command helper or capture as correctness oracle. |
| ITR087 | Planning integration | Only approved live inspection facade orchestrates capture/checks; no report/source injection parameter, hidden bearer state or numerical consumer. |
| ITR088 | SQL inventory | Only six proposed source tables/five protected entries/private helpers/indexes/triggers; no broad source grants, unrelated old SQL edits or role provisioning function. |
| ITR089 | Migration safety | Old migrations unchanged; actual next revision determined at implementation; loss-refusing downgrade and fresh empty source state tested. |
| ITR090 | Production isolation | No clinical values/providers/qualifications/default supported population, policy defaults/coefficients or production authority/content seeds. |
| ITR091 | No source secrets | No password/verifier/credential URL/logging or unrelated household/private facts in API/schema/log fields. |
| ITR092 | Public surface | No HTTP/auth/login endpoint or full PlanPolicyResolver/consumer admission; root directory metadata not a cross-member reader. |
| ITR093 | Readiness gates | Full006/007/008 incomplete, parent issues open, planner/activation false, Execution not started, PRECOMMIT fail-closed. |
| ITR094 | Compatibility approval | Before implementation guard edits, exact affected file/block/preimage inventory and separate owner authorization; no inherited historical exception. |
| ITR095 | Original worktree preservation | HEAD/status/file SHA-256 inventory of original19 files unchanged before/after isolated work; no reset/discard/accidental staging. |
| ITR096 | Full execution evidence | One final exact-head full CI pass, zero skips, actual real-PG item mapping, SCRAM/TLS16,benchmark22,client10,all architecture/import/export/web guards; report measured totals. |

## ITR018 parameter-catalog expansion (same obligation, future execution)

These are mandatory subcases within existing ITR018, with ITR040/ITR042 integration and ITR055
pure mutation coverage; they do not add acceptance IDs or change the48 real-PG obligation count.
Future evidence must report each executed node/parameter and actual expansion count separately.

| Subcase | Actual catalog/operation setup in disposable PostgreSQL | Required proof |
|---|---|---|
| P1 default positive | Fresh ordinary safe login; confirm no pg_parameter_acl row for work_mem and no extra parameter ACL privilege | Capture may succeed with no invented owner/row/OID. Explicit-role has_parameter_privilege SET/ALTER SYSTEM false, while native session SET work_mem may succeed; neither is Identity authority. |
| P2 real row | Test administrator grants SET on a controlled parameter; inspect actual oid/parname/paracl and information_schema.columns for pg_parameter_acl | Only the three actual catalog columns exist; fact owner=null, real row OID, all ACL entries retained. Owned TABLE/FUNCTION controls still require their real owners. |
| P3 direct grants | Separate SET and ALTER SYSTEM grants to the actual ordinary login; test each WITH GRANT OPTION variant | Effective ACL bit/option agrees with explicit-login PostgreSQL oracle; ordinary safe-role gate denies, no positive source/inspection. Do not execute ALTER SYSTEM against shared configuration. |
| P4 PUBLIC/inheritance | Grant to PUBLIC and to a role reached through INHERIT TRUE; compare an otherwise equivalent INHERIT FALSE path | PUBLIC and inheritable paths deny safe capture, non-inherited path alone adds no current ACL right; SET-role/admin reachability still checked separately. PUBLIC grant-option fabrication rejected. |
| P5 revoke/mutation | Retain complete before/after catalog cuts across GRANT, REVOKE and inherited-edge changes, including mutation from a second database | Fresh capture tracks effective rights; observed within-capture descriptor changes fail whole-cut; faithful old cuts stay historical-only. Rehashed deleted grant/owner forgery rejected against retained primitives. |
| P6 default shape controls | Exercise absent-row and existing empty ACL observations through real supported catalog operations; require present-NULL default parity via a rollback-only trusted fixture if normal commands do not yield NULL | Keep no-row, raw NULL and empty ACL distinct. No privileged fault-injection capability in runtime; no manufactured owner or all-user grant. Superuser bypass is recognized independently and forbidden for ordinary actors. |
| P7 completeness/negative | Real grant on an unloaded custom parameter and other-grantee rows; exhaust the existing bounded catalog capacity in disposable fixtures | Enumeration cannot be restricted to pg_settings, actor-favorable rows or known built-ins. Overflow/unsupported shape produces whole error, no truncated successful source. |

P6 trusted setup is a future isolated test fixture, not permission to modify a live catalog here.
The normative absence/default rules are grounded in PostgreSQL18.4 source and require these future
actual-catalog checks; the current docs-only CI executes the existing4611 tests, not new ITR cases.

## Earlier A01–A16 research proposal coverage

These earlier research labels remain proposals; this design specializes them into executable
future obligations without claiming completed source tests. Frozen EPI evidence remains historical.

| Research proposal | New mandatory obligations |
|---|---|
| A01 subject/body binding | ITR007, ITR022, ITR046, ITR063 |
| A02 operation/role matrix | ITR003–ITR007, ITR021–ITR025, ITR069 |
| A03 actual principal authentication | ITR008–ITR018, ITR056 |
| A04 coherent transaction | ITR038–ITR041, ITR066 |
| A05 fresh revocation versus replay | ITR026–ITR033, ITR041, ITR067, ITR080 |
| A06 request time versus source sequence | ITR021, ITR032–ITR036, ITR065 |
| A07 completeness/privacy | ITR042–ITR044, ITR057–ITR058, ITR079 |
| A08 faithful negative versus forgery | ITR028–ITR030, ITR047, ITR059–ITR062, ITR070 |
| A09 rehashed substitution/report | ITR017, ITR046, ITR056, ITR060–ITR063 |
| A10 independent primitive reconstruction | ITR052–ITR062, ITR077, ITR086–ITR087 |
| A11 frozen orthogonal EPI | ITR047, ITR064, ITR074–ITR075 |
| A12 bounds/cancellation | ITR044–ITR045, ITR071–ITR072 |
| A13 TEST_ONLY/no admission | ITR048, ITR073–ITR076, ITR090–ITR093 |
| A14 least privilege | ITR003–ITR004, ITR018–ITR021, ITR048, ITR088 |
| A15 exact compatibility | ITR078, ITR081–ITR086, ITR089, ITR094–ITR095 |
| A16 final full execution | ITR084, ITR096 |

## Design PR versus future implementation evidence

This PR runs only existing repository checks and existing4611-test CI, plus documentation/link/
matrix/compatibility validation. It creates no new source test, protected SQL, enrollment, grant
or migration. Future implementation must attach a case-to-executed-node manifest and actual PG
execution receipt for all48 items, not present this design table as an executed result.

Stop implementation for an unsupported actual authentication/session identity, an independent
checker that needs a producer oracle, a frozen-source change, unapproved permission expansion,
new contracts beyond the exact19, or a required guard edit without separate narrow authorization.
No clinical/production approval is inferred from engineering tests. Production gate remains CLOSED.
