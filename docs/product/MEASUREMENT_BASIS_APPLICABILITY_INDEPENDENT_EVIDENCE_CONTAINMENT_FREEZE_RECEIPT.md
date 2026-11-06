# Measurement-Basis Applicability & Independent Evidence Containment — structural freeze receipt

**SOURCE-BOUND MEASUREMENT-BASIS APPLICABILITY & INDEPENDENT EVIDENCE CONTAINMENT — STRUCTURALLY FROZEN / TEST_ONLY**

**PRODUCTION NUTRITION/CLINICAL CONTENT GATE — CLOSED**

This records the separately authorized structural freeze. It is not scientific approval,
production acceptance, a complete NutritionPolicy integration or full-MTR completion.

## Canonical design and frozen implementation

- Approved design: [PR #132](https://github.com/thedusk4203/Menuto/pull/132), reviewed head
  `803f83791bd7f41acda614268098f35b72eaa729`, merged at
  `83025f158306e8cebc6357ac6d13fc3caac57809`.
- [Architecture PASS 6678583194](https://github.com/thedusk4203/Menuto/pull/132#issuecomment-6678583194)
  and [design completion 6679271731](https://github.com/thedusk4203/Menuto/pull/132#issuecomment-6679271731).
- Implementation: [PR #133](https://github.com/thedusk4203/Menuto/pull/133), five commits /27 files;
  implementation base `83025f158306e8cebc6357ac6d13fc3caac57809`.
- Reviewed implementation head: `a22d3c37697f7ac7d73ed29acbaa1d0b26c50b49`.
- **Frozen implementation merge:** `9d3b580ce2a2d111223b37814612a4072dbfe6a2`.
- **Frozen implementation tree:** `3a68035f9c33de152b3899a083d534a537c647e1`, identical to
  the reviewed-head tree. The merge's two parents are exactly the implementation base and head.
- Merge used `merge` with the exact implementation-head SHA guard, ordinary branch protection
  enforcement and auto-merge OFF; no squash/rebase/force-push or bypass.
- Canonical [formal structural freeze 6688245300](https://github.com/thedusk4203/Menuto/pull/133#issuecomment-6688245300).

Freeze is pinned to this implementation merge/tree, not to a later documentation commit.
The docs-only synchronization branch starts at the frozen merge. Its CI verifies the status-sync
tree separately; it never substitutes for the implementation's post-merge verification.

## Review history and publication-time correction

The historical implementation head `37cb08db0e97a590f656f71a92cb438cba4dd5d9` passed its
CI but received [CHANGES REQUIRED 6682831199](https://github.com/thedusk4203/Menuto/pull/133#issuecomment-6682831199)
for MBA-R133-01: an expired original-reviewer grant/qualification could be accepted for a
retrospective publication whose assertion interval was earlier than publication time.

Correction `a22d3c37697f7ac7d73ed29acbaa1d0b26c50b49` changes exactly four files:
Nutrition replay, independent Validation replay, regression tests and implementation evidence.
Both implementations now require the original reviewer's exact scoped `TEST_BASIS_REVIEW` grant
and `SYMBOLIC_TEST_ONLY_NOT_SCIENTIFIC` qualification to be valid at every PUBLISH/SUPERSEDE
`recorded_at`, using `effective.start <= recorded_at < effective.end`, and to cover the complete
assertion effective interval. Publisher capability/qualification checks remain intact.
Each implementation folds retained immutable journal prefixes independently. Later renewal or
requalification, including backdated valid time, cannot repair an unauthorized publication.

[Corrected-head CI 42205518787](https://github.com/thedusk4203/Menuto/actions/runs/42205518787)
passed; [independent correction PASS 6685642216](https://github.com/thedusk4203/Menuto/pull/133#issuecomment-6685642216)
closed MBA-R133-01 at that exact head. The original finding is retained as history, not deleted.
The 18 executed additions cover eight producer negatives, eight independent-checker/handoff
negatives with fully rehashed positive claims, and two authorized retrospective controls.
Grant and qualification expiry are each covered for PUBLISH/SUPERSEDE, with and without later
backdated renewal, without requiring REVOKE/DISQUALIFY. Invalid evidence yields no favorable
partial witnesses. Existing future-effective succession, withdrawal, retirement and replay remain.

The [post-merge completion receipt 6687858924](https://github.com/thedusk4203/Menuto/pull/133#issuecomment-6687858924)
records the separately completed merge gate. Its freeze-pending disposition was accurate then;
the later authorized formal freeze supersedes only that status. A technical PASS comment is not
itself GitHub APPROVED, maintainer merge authorization or structural-freeze authorization.

## Exact post-merge execution evidence

[GitHub Actions push CI 42230659936](https://github.com/thedusk4203/Menuto/actions/runs/42230659936),
attempt1, ran on exact merge SHA `9d3b580ce2a2d111223b37814612a4072dbfe6a2` and completed
**SUCCESS**. Python/web and every workflow step passed; completed direct logs were inspected.
PR CI is historical head evidence, not a substitute for this merged-main push gate.

| Executed requirement | Result |
|---|---:|
| Full pytest | **4,183 passed /0 skips** |
| Retained baseline | **4,047** |
| Additive MBA cases | **136 =110 pure +26 real PostgreSQL** |
| Mandatory acceptance mapping | **MBA001–MBA080** |
| Mandatory PostgreSQL obligations | **12/12**, covered by 26 executions |
| MBA-R133-01 regression additions | **18 =8 producer +8 checker/handoff +2 controls** |
| Separate SCRAM/TLS smoke | **16/16** |
| Benchmark | **22/22** |
| Client | **10/10** |

Ruff, architecture/import boundaries, OpenAPI/domain exports, synthetic fixtures, client contracts,
typecheck and web build passed. All MBA cases, including real protected PostgreSQL paths, are part
of the unfiltered no-skip full suite. Collection reconciles inventory; it is not counted as execution.
The full log retains six non-blocking warnings: one Starlette/httpx deprecation, two import-time
`~bool` deprecations and three Pydantic serializer warnings in tests. No suppression or implementation
change was introduced for freeze. Dependency maintenance remains separately scoped work.

## Frozen compatibility and persistence boundary

- **503 prior exported definition bodies/hashes unchanged +12 additive =515 total definitions**.
- **53 frozen source/migration files byte-identical** to the implementation base.
- Schema **0017 /108 domain tables**; no0018.
- **ZERO NEW PERSISTENCE**; no new SQL tables, protected functions, roles or privileges.
- Frozen Root/MTR-006 v1/MTR-007 source contracts, runtime semantics and historical migrations unchanged.
- [Implementation evidence](MEASUREMENT_BASIS_APPLICABILITY_INDEPENDENT_EVIDENCE_CONTAINMENT_EVIDENCE.md)
  retains MBA001–MBA080 mappings; the compatibility fixture retains frozen definition/file pins.

Fresh-install MBA011 checks the migrated empty PostgreSQL database has no basis DB objects and
zero Nutrition source-table rows before isolated TEST_ONLY setup. No production provider,
qualification, publication, seed or default is installed. This is fresh-install evidence, not an
audit of a live production deployment.

## Exact bounded frozen semantics

1. Original source-authored same-meaning measurement preimages retained inside exact reviewed
   guideline/rule sources; a hash, label or downstream assertion cannot replace original evidence.
2. Complete pre-policy original and derived anchors: roots, hard/goal/comfort and temporal/weekly
   descriptors, including every required MAKE_CONSTRAINT branch. Missing/conflicting original
   meaning or required period evidence withholds favorable applicability; no synthetic weekly sum.
3. Synthetic TEST_ONLY fixture registry with private issued context identity, actor/reader/database
   binding, append-only revisions/frontiers and finite authority/publication history. Privileged
   test-harness bootstrap is not a production enrollment or hostile-code security boundary.
4. Exact subject/scope/temporal identity and reviewer/publisher principal-subject separation;
   independently reconstructed capability and symbolic qualification lifecycle.
5. PUBLISH/SUPERSEDE/withdrawal/retirement replay, publication-time correction MBA-R133-01,
   retrospective authorized publication and future-effective succession without early activation.
6. One-session canonical NRE capture composition through the unchanged ordinary reader, pinned
   before/after against immutable fixture registry state. No common MVCC is claimed between
   PostgreSQL and the in-memory fixture registry; no partial/truncated successful capture.
7. Pure Nutrition producer and independently reconstructed Validation; no shared producer business
   predicate as checker oracle, no trust in supplied positive results/reports or matching hashes.
8. No-positive-on-invalid containment, no implicit latest/provider/substitute fallback and no
   cross-version stitching. Expected unavailable/unsupported evidence remains distinct from a
   malformed/inconsistent favorable claim.
9. Terminal **UNVERIFIED_TRANSPORT** semantics. Fingerprints establish retained replay identity,
   not canonical database origin, current authorization/publication or scientific correctness.

This freeze does not authorize physiological intake, consumed-food interpretation, nutrient
conversion, clinical measurement equivalence, retention coefficients, a clinical measurement
bridge, scientific validity or production readiness. Structural TEST_ONLY applicability is not
permission to synthesize a production nutrition policy or validate/activate a full plan.

## Preserved closed gates and historical records

**PRODUCTION NUTRITION/CLINICAL CONTENT GATE — CLOSED**. No production numerical values,
clinical protocols, supported-population declarations, qualified actors, providers, publications,
conversion rules, seeds or defaults are authorized.

`planner_ready=False`; `activation_ready=False`; **Execution NOT STARTED; PRECOMMIT FAIL-CLOSED**.
Full **MTR-006/007/008 INCOMPLETE**; parent issues **#5/#6/#7 OPEN**. Nutrition Root, MTR-006 v1
structural synthesis and MTR-007 bounded estimator retain their prior freezes and semantics.
No MTR-006 policy-integration v2, MTR-008 implementation, solver activation, scientific conversion,
parent issue closure, next-gate selection or downstream implementation is part of this freeze/sync.

The [approved design](MEASUREMENT_BASIS_APPLICABILITY_INDEPENDENT_EVIDENCE_CONTAINMENT_DESIGN.md),
historical implementation evidence and GitHub review/merge receipts remain unchanged. Their
NOT FROZEN/candidate/future-test wording describes the respective historical stages; this receipt
supersedes current freeze status only. Documentation synchronization changes no implementation
body, contract, test, export, tooling, migration or data. The initial docs-only sync PR remains OPEN
pending separate review and merge authorization.
