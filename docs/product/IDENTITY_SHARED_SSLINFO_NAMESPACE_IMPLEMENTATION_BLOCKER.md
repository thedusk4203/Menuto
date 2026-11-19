# Identity shared sslinfo namespace — implementation compatibility blocker

**IMPLEMENTATION BLOCKED / NOT COMMITTED / NO IMPLEMENTATION PR / NOT MERGED / NOT FROZEN / PRODUCTION GATE CLOSED**

## Verified design merge and bounded resumption

PR148 merged with exact-head protection: reviewed062e1c0c3eecb7210180ae342ab8f8ff2d781431;
actual main68fcb688231460f1973077eb20140b8c5db440a2;
tree0855a39561bc194d569ef8b93b6e4db68a49f91b; ordered parents120d28f62b66720e8631b64e0b2a50cdc57e6c42 and062e1c0c3eecb7210180ae342ab8f8ff2d781431.
Exactly eight reviewed Markdown files. Separate pushCI43995258973 SUCCESS:4611 tests/0skips,
smoke16/16,benchmark22/22,client10/10 and all guards.
[Verified completion receipt6936082046](https://github.com/thedusk4203/Menuto/pull/148#issuecomment-6936082046).

The preserved isolated implementation worktree fast-forwarded without reset/discard. The identical
untracked blocker report was retained in an ignored backup before becoming tracked from PR148.
Original19 local file hashes/HEAD/status and all61 pre-resumption implementation preimages were preserved.

## Exact new blocker

The existing frozen reference-prior fixture `apps/backend/tests/test_postgres_reference_priors.py`
(lines113–116 in this worktree) explicitly tests a **pre-existing shared deployment sslinfo extension
in schema public**. It downgrades to0013, successfully executes:

```sql
CREATE EXTENSION sslinfo WITH SCHEMA public;
```

and calls `command.upgrade(config, "head")` again. This behavior is part of the retained baseline;
the authorized35 metadata patches do not authorize rewriting that fixture's lifecycle or semantics.

Identity migration0018 (`0018_identity_principal_user_sources.py`, lines1654–1670) requires the actual
native C primitive to be an sslinfo extension member whose **extension and function namespace are
menuto_prior**. The executed shared-public fixture therefore fails its Python installation guard:

```text
RuntimeError: Identity sslinfo catalog trust root mismatch
```

This is a Python pre-install guard, **not a42501 SQLSTATE failure**. It occurs before the Identity
roles/DDL and before the exactly authorized TLS grants. The successful CREATE EXTENSION public and
subsequent guard failure are observed in the completed real PostgreSQL18.4 smoke run, not a mock.
No separate live catalog OID query for the already-cleaned failed database is claimed.

The current namespace pin is intentional under the owner's narrow TLS prerequisite. The frozen prior
shared-extension case is also intentional. **Both requirements cannot be satisfied by the current
implementation unchanged.** Silently relaxing the pin, moving the shared extension, adding a wrapper,
granting access in another namespace, expanding the vetted public routine manifest or changing the
historical fixture would exceed current authority. No such workaround was applied.

## Measured execution, without summing runs into a full pass

- Red reproduction: the two ITR018 inherited-TRUE cases failed only the incomplete offline fixture;
  actual unsafe protected capture already rejected42501. The fixture now retains real native role
  membership before the unsafe parameter ACL. Four TRUE/FALSE controls subsequently passed, without
  changing the expected rejection or importing a producer classifier into Validation.
- Complete focused Identity native run: **88 passed /0failed /0errors /0skips**, all48PG obligation
  groups, P1–P7, exactly3mapped ITR040 IDs. It includes RR/SERIALIZABLE, same/other-database native
  GRANT/REVOKE, fresh42501 denial and native observed login-descriptor disagreement. The actual
  public capture boundary returns SOURCE_CUT_INCOHERENT/CATALOG_CHANGED with null payload.
- Pure/adversarial component run: **57 passed /0skips**; architecture component: **16 passed /0skips**.
  These are focused component evidence, **not** a full retained-baseline regression pass.
- Required separate16-case SCRAM/TLS regression: **8 passed /8setup errors /0failed /0skips**.
  All8errors share the reference-prior fixture's shared-public extension installation blocker.
- Full-suite execution was stopped at the proven scope blocker, around42% progress. It is
  **INCOMPLETE / NOT PASS**. There is no valid completed full-suite total and no implementation CI.
  Only the dedicated pytest child was stopped; its harness finally stopped the disposable cluster.
- Ruff, architecture/import, OpenAPI/domain export and synthetic fixture guards passed. Client10/10,
  typecheck/build and benchmark22/22 passed separately.
- Collection inventory (not execution): **4772 nodes =4611 retained +161 additive Identity nodes**.
  The expected143 proposal was not used as an executed count. No diagnostic run is counted twice.

Local receipts: `.local/identity-resume-red-1/results.xml`, `identity-resume-green-1/results.xml`,
`identity-resume-cut-2/results.xml`, `identity-resume-all-1/results.xml`,
`identity-pure-final-draft.xml`, `identity-architecture-2.xml`,
`identity-resume-install-inventory-1/results.xml`, `identity-tls-smoke-final-1/results.xml`.
These ignored artifacts are author-run evidence, not independently reviewed GitHub receipts.

## Preserved compatibility and source inventory

537 previous definition bodies/hashes remain exact;19 literal additive names yield556 exports.
All35 metadata patches retain exact approved postimages and inverse preimages. The185-file canonical
runtime/migration snapshot is byte-identical, including503/515historical hashes,53frozen files and59PIVpins.
Original19 local files retain exact bytes, HEAD1679d6035dd6685118df6c95fa37628384cc961c and status.

The draft0018 installs six Identity tables (108public+6private=114), five protected entries plus12
private helpers, four NOLOGIN groups and only the two authorized native TLS grants. The private TLS
helper is also SECURITY DEFINER but has no PUBLIC/ordinary EXECUTE; it is not a sixth entry point.
Fresh-install evidence in the supported menuto_prior-extension layout confirms all six Identity
sources and Nutrition/provider/qualification/publication content empty. The two retained baseline
rows are public.culinary_feature_frontier and public.ingredient_protein_frontier structural witnesses,
not newly seeded content. Schema on canonical GitHub main remains0017/108;0018 is an uncommitted draft
executed only in disposable tests. No production migration, role, grant or content was deployed.

## Required owner/architecture decision — no implementation selected

Reconcile the supported shared-extension namespace model with the narrow TLS prerequisite, exact
source-owner privileges, independently pinned routine identities and preserved migration compatibility.
If an unsupported Identity deployment may still install inert structural objects, that install/failure
boundary requires separate explicit design approval; it is not assumed here. If another native namespace
is supported, authority must explicitly settle the schema-qualified primitive, OID/extension/owner
validation, grants and classification impact. Existing PUBLIC rights are not used as an implicit exception.
No historical fixture exemption or scientific/nutrition authority is requested by this report.

Implementation submission remains gated on a full successful retained regression and exact-head CI.
No commit/push/implementation PR was created because that prerequisite failed. No new grants,
namespace relocation, wrapper, frozen fixture edit, merge or freeze was performed to bypass the blocker.

FullMTR-006/007/008 INCOMPLETE;issues5/6/7OPEN;productionNutrition/clinical gateCLOSED;
planner_ready=False;activation_ready=False;ExecutionNOTSTARTED;PRECOMMITFAIL-CLOSED.

**PR148 MERGED / POST-MERGE VERIFIED / IDENTITY IMPLEMENTATION BLOCKED AT SHARED-SSLINFO NAMESPACE COMPATIBILITY / OWNER ARCHITECTURE DECISION REQUIRED / PRODUCTION GATE CLOSED**
