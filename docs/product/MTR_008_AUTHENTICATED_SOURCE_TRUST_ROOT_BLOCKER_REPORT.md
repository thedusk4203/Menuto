# MTR-008 authenticated explicit-request source — trust-root blocker report

**DESIGN BLOCKED / PREREQUISITE DECISION REQUIRED**

This is a local prerequisite report, not an implementation-ready detailed design, approved new
source authority, exported contract or migration proposal. No detailed-design PR was created.
It follows the owner's critical blocker rule after successful PR #145 merge verification.

## 1. Completed Phase 1 / exact assessment baseline

- PR #145 reviewed head: `2c98315276457610b4329a331a24c9c7f8a444c8`.
- Actual merge/current main: **`cd8cbe175cf60e77e05a95cb30b0571d95819759`**.
- Resulting tree: **`f1d43e9ea30a7873119465a341ec005906b5b660`**, identical to reviewed tree.
- Ordered parents: `fddb1a665f438ad2cc8ccf04521a93b8172af16d`,
  `2c98315276457610b4329a331a24c9c7f8a444c8`; exactly five approved Markdown files.
- [Post-merge push CI 42567336877](https://github.com/thedusk4203/Menuto/actions/runs/42567336877):
  exact merge SHA, SUCCESS; Python/web/every step green; **4,611 passed / 0 skips**, six retained
  warnings, 2665.10s; SCRAM/TLS16/16, benchmark22/22, client10/10.
- [Completion receipt 6733574997](https://github.com/thedusk4203/Menuto/pull/145#issuecomment-6733574997)
  was posted and read back exactly. No branch-protection bypass or auto-merge.
- Phase2 investigation uses a separate worktree/branch at this exact main. No main drift found.

Frozen EPI remains implementation merge `40875d95f81390f3985cc0e2ad4600b1e494dacb` /
tree `a6f53925857898ce0d63c30f4da5b55890e7d374`. The research merge does not replace that identity.

## 2. Exact missing prerequisite

**An owner-approved, independently owned Identity/Policy requester trust source that binds an actual
authenticated principal to an existing Menuto User, including who may issue/change/revoke that
binding and what Policy request operation it authorizes.**

Actual PostgreSQL credential authentication and TLS can prove the connection's login and endpoint.
They do not, by themselves, prove which application User that login represents or authorize all-axis
plan intent. A Membership row can answer what an already authenticated User may access; it does not
prove who authenticated the caller. The missing binding cannot be supplied by the request UUID itself.

No suitable general Identity/Policy source or verified external issuer was found in the inspected
canonical application/contracts/migrations. Nutrition has a real narrower principal enrollment source;
its existence is not evidence of generic Policy authority.

## 3. Direct source evidence

All links pin the exact assessment baseline; these are verified source facts, not future proposals.

| Evidence | What it proves / cannot prove |
|---|---|
| [Identity models](https://github.com/thedusk4203/Menuto/blob/cd8cbe175cf60e77e05a95cb30b0571d95819759/apps/backend/app/modules/identity/models.py#L1) | Explicit identity-anchor-only implementation; User has display_name plus id/created_at, no credential/session or principal binding |
| [Original users DDL](https://github.com/thedusk4203/Menuto/blob/cd8cbe175cf60e77e05a95cb30b0571d95819759/apps/backend/migrations/versions/0001_household_member_safety_and_measured_.py#L32) | Canonical User row is an identity anchor, not a DB-login credential record; no later general requester binding source was found |
| [Household access](https://github.com/thedusk4203/Menuto/blob/cd8cbe175cf60e77e05a95cb30b0571d95819759/apps/backend/app/modules/households/public.py#L50) | Caller supplies actor_user_id; access functions explicitly assume an authenticated internal caller and query membership |
| [Household models](https://github.com/thedusk4203/Menuto/blob/cd8cbe175cf60e77e05a95cb30b0571d95819759/apps/backend/app/modules/households/models.py#L25) | User/household/member/role relationship; not append-only credential, grant-expiry or authorization history |
| [NRE actor capture](https://github.com/thedusk4203/Menuto/blob/cd8cbe175cf60e77e05a95cb30b0571d95819759/apps/backend/app/modules/planning/nutrition_resolution_capture.py#L172) | Actor derives from actual Nutrition synthesis principal enrollment before bounded member access; no general Policy requester authenticator |
| [Synthesis principal storage](https://github.com/thedusk4203/Menuto/blob/cd8cbe175cf60e77e05a95cb30b0571d95819759/apps/backend/app/modules/nutrition/synthesis_models.py#L51) | Real database/role OID/name to user/human binding exists, but is owned by the Nutrition authority source |
| [Protected synthesis capture](https://github.com/thedusk4203/Menuto/blob/cd8cbe175cf60e77e05a95cb30b0571d95819759/apps/backend/migrations/versions/0017_nutrition_synthesis_sources.py#L729) | Requires Nutrition provider/family/applicability and its read grant; precision witness is bounded to that path, not a generic authenticated-user interface |
| [Finite synthesis capabilities](https://github.com/thedusk4203/Menuto/blob/cd8cbe175cf60e77e05a95cb30b0571d95819759/apps/backend/app/modules/nutrition/synthesis_contracts.py#L12) | Nutrition review/publish/withdraw/read capabilities; no general Policy request submission capability |
| [PIV use selector](https://github.com/thedusk4203/Menuto/blob/cd8cbe175cf60e77e05a95cb30b0571d95819759/apps/backend/app/modules/planning/policy_v2_capture.py#L236) | Unverified selector and inspection-only purpose; a lease or matching selector does not supply general request authentication |
| [Frozen EPI outputs](https://github.com/thedusk4203/Menuto/blob/cd8cbe175cf60e77e05a95cb30b0571d95819759/apps/backend/app/modules/policy/explicit_intent_contracts.py#L101) | Source stays UNAUTHENTICATED_DECLARATION, transport UNVERIFIED, numerical use NOT_ADMITTED and readiness False |
| [Application entrypoint](https://github.com/thedusk4203/Menuto/blob/cd8cbe175cf60e77e05a95cb30b0571d95819759/apps/backend/app/main.py#L1) | Health only; no implemented public credential/session/authenticated request ingress |

Inspected Identity/Households/Policy/shared sources, relevant source-principal models, the frozen NRE/
Nutrition/PIV capture interfaces, original User DDL and later source migrations. Searches for generic
credential/session/JWT/OIDC/verified-request interfaces did not reveal an alternate approved source.
Preference service similarly assumes an authenticated application actor; hierarchy principal records
are their own source authority and do not supply a User binding for Policy. The existing graph query
returned only scaffold-era navigation and was not used as authentication evidence; no graph rebuild.

## 4. Why detailed design cannot be finalized under the present authority decision

**Verified fact:** the existing appropriate general binding source is missing.
**Assessment:** selecting a new issuer, registrar/enrollment source, role namespace or canonical
configuration authority would establish a new trust source; selecting new protected read/enrollment
functions or grants would establish a new privilege surface. These are not consequences that can be
inferred from the approved research or from a read-only capture interface.

The owner explicitly requires identifying new authority/persistence rather than unilaterally deciding
migration0018, SQL grants, roles or tables. A viable new source can be designed, but its authority
scope/issuer choice must first be approved or explicitly included in an expanded design authorization.
This report does not claim that authentication is technically impossible, that a full public login
product is mandatory, or that every valid source must use a new table. It identifies the missing
source decision before contracts can honestly claim authenticated requester evidence.

A server-owned map/role-name convention or versioned artifact could only be evaluated as a **new
explicitly approved issuing authority**, with actual credential binding and lifecycle. Calling an
unapproved map a TEST_ONLY fixture, a private context or a trusted configuration does not solve this.

Therefore exact positive authority contracts, permission matrix, grant lifecycle and source-specific
PG execution counts are not fabricated or marked DESIGN READY. Frozen EPI child semantics remain
unchanged. No independent checker can reconstruct missing authoritative primitive facts from a hash.

## 5. Alternatives and required impact decision

| Alternative | Authority required | Source/schema/privilege impact | Disposition |
|---|---|---|---|
| A. Bounded Identity-owned DB-principal-to-User enrollment source, with Policy-specific operation authorization | Explicit registrar/issuer authority separate from ordinary requester; actual dedicated credential and DB/login OID/name binding; exact User identity and revocation/expiry semantics | Durable enrollment/binding and operation authorization truth may require protected source objects and restricted admin/read interfaces; normalized physical schema, roles/grants and legal migration revision require separate review, none chosen here | **Recommended prerequisite direction** for a small internal STRUCTURAL/TEST_ONLY path; no public login product or clinical qualification is inherently required |
| B. Approved external or existing organizational identity issuer | Concrete issuer/trust anchors, credential verification, subject-to-User mapping, audience/lifetime/revocation and authenticated server request binding | New Identity verifier/configuration and possibly durable mapping/session truth; sharing a DB service login still requires verified actor evidence, not an arbitrary actor UUID | Viable only after actual source/issuer is supplied and scope approved; no such implementation/approved source found here |
| C. Reuse Nutrition enrollment/grants or PIV lease as Policy authority | Would silently transfer a different domain's authority | Frozen semantic/permission expansion, unrelated provider/applicability dependency or direct protected-source access | **Rejected under current authorization**; real credentials in another source are not all-axis Policy permission |
| D. UUID + membership, shared login, fixture/test label, digest/report or naming convention without an issuer | No authoritative credential-to-User source | Hides the missing source instead of establishing one | **Rejected**; cannot label this authenticated source capture |

A versioned repository/deployment artifact is not ruled out in principle, but would belong to A/B's
new authority/source decision: who publishes it, why its User binding is trusted, actual credential
verification, immutability, invalidation/revocation and capture/replay must be settled. Hashing an
artifact or treating its test values as authority is insufficient.

No migration number/table count, new SQL function, role, grant or production actor is reserved.
This report adds zero persistence and grants. A future schema-backed option would require an
approved forward migration after the then-current schema; it does not assume that revision is0018.

## 6. Prerequisite decision needed before design resumes

1. Select the Identity/Policy issuing authority and credential mode: bounded DB enrollment, an actual
   external issuer, or an independently justified artifact-backed source. Identify the trusted
   administrative issuer and exact principal-to-User truth it owns.
2. Approve whether that source authority is a separate prerequisite design or explicitly expanded
   scope of this source-capture design. Do not grant implementation or production content by inference.
3. Authorize the source/persistence/privilege impact for design review; future physical objects and
   runtime grants remain subject to separate implementation authorization.
4. Then finalize the source capture contracts/operation matrix, exact subject scope, publication or
   enrollment lifecycle, fresh-versus-retained verification, one-snapshot restrictions and exact
   named real-PG obligations. No preselected export count or fabricated User/role binding is carried forward.

The preceding research A01–A16 remain **proposals**, not implemented tests. EPI001–EPI064 remain
frozen and executed. Source-authentication implementation will need actual PostgreSQL cases for
principal spoofing/shared-login/SET ROLE/OID recreation, scoped grants and membership isolation,
revocation/expiry without explicit REVOKE, coherent read-only snapshots, shadowing/least privileges,
resource cancellation and independent forged-positive rejection. Concrete source-specific counts
cannot be honestly finalized before the source choice; mocks are not substituted for those executions.

This engineering authority gap is **separate from the production scientific/clinical gate**. Resolving
it need not publish Nutrition content or qualify clinical actors; resolving it would not authorize any
such content, physiological conversion, numerical policy or consumer admission.

## 7. Local report / preserved state

Only this local Markdown blocker report is added in the isolated design worktree. No commit, push,
detailed-design PR, source/test/contract/migration/tooling/CI/data change, role creation or grant.
No complete design or implementation readiness is claimed. No new exact-head design CI exists,
because the blocked outcome has no submitted design PR. The completed Phase1 push CI is accurately
identified above; it is not presented as testing a new authentication source or design.

Preserved: 537 exports, 515 legacy hashes, 503 historical hashes, 53 frozen files and59 PIV pins;
schema0017/108, no0018; frozen Root/NPS/NRE/MBA/PIV/EPI identities. Original19 local files remain
untouched by full status/HEAD/SHA-256 comparison. Full MTR-006/007/008 INCOMPLETE, #5/#6/#7 OPEN,
production Nutrition/clinical gate CLOSED; planner_ready=False, activation_ready=False;
Execution NOT STARTED, PRECOMMIT FAIL-CLOSED.

**PR #145 MERGED & VERIFIED / TRUST-ROOT BLOCKER IDENTIFIED / PREREQUISITE DECISION REQUIRED / NO IMPLEMENTATION AUTHORIZED / PRODUCTION GATE CLOSED**
