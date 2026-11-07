# MTR-006 Policy Integration v2 — structural freeze receipt

**MTR-006 POLICY INTEGRATION V2 — STRUCTURALLY FROZEN / TEST_ONLY**

**PRODUCTION NUTRITION/CLINICAL CONTENT GATE — CLOSED**

This records the separately authorized structural freeze of the bounded, source-bound, independently verified NutritionPolicy v2 integration. It is not scientific approval, clinical authority, production acceptance, or full MTR-006/007/008 completion.

## Canonical design and frozen implementation

- Approved design: [PR #136](https://github.com/thedusk4203/Menuto/pull/136), reviewed head
  `570098480335dbf7c731fcf0954dd4601a2ccb9d`, merged at
  `1679d6023253b34293f773dc164cff054fc21c32`.
- [Architecture PASS 6701198539](https://github.com/thedusk4203/Menuto/pull/136#issuecomment-6701198539)
  and [design completion 6701887643](https://github.com/thedusk4203/Menuto/pull/136#issuecomment-6701887643).
- Corrected design: [PR #137](https://github.com/thedusk4203/Menuto/pull/137) (PIV-R136-01), reviewed head
  `dcab0f41a8605bb82c4d6b85ce01d176dcbc1bee`, merged at
  `5b9441d1c10e5ad010a10f9e1af415c1ef50bd5a`.
- [Corrigendum PASS 6703079507](https://github.com/thedusk4203/Menuto/pull/137#issuecomment-6703079507)
  and [verified merge receipt 6703597433](https://github.com/thedusk4203/Menuto/pull/137#issuecomment-6703597433).
- Implementation: [PR #138](https://github.com/thedusk4203/Menuto/pull/138), implementation base
  `5b9441d1c10e5ad010a10f9e1af415c1ef50bd5a`.
- Reviewed implementation head: `1e9000cf5122964393cd1cb1343719d378a7f936`.
- Independent implementation PASS: [6709092185](https://github.com/thedusk4203/Menuto/pull/138#issuecomment-6709092185).
- Verified post-merge completion: [6710291961](https://github.com/thedusk4203/Menuto/pull/138#issuecomment-6710291961).
- **Frozen implementation merge:** `45bb2677d3eb657dcf36aaf9fc5b9e146e8bf8fa`.
- **Frozen implementation tree:** `19c97149aeaaf108894e7a3d01afd0db4558e9e9`, identical to
  the reviewed-head tree. The merge's two parents are exactly the implementation base and head.
- Merge used standard GitHub merge with the exact implementation-head SHA guard, branch protection
  enforcement and auto-merge OFF; no squash/rebase/force-push or bypass.
- Canonical [formal structural freeze 6710492789](https://github.com/thedusk4203/Menuto/pull/138#issuecomment-6710492789).

Freeze is pinned to this implementation merge/tree, not to a later documentation commit.
The docs-only synchronization branch starts at the frozen merge. Its CI verifies the status-sync
tree separately; it never substitutes for the implementation's post-merge verification.

## Review history and differential resolution

The historical implementation head `4b148213898bd4bacdb7ecc442e91aa2fdaeb48d` passed its
CI but received [CHANGES REQUIRED 6706823011](https://github.com/thedusk4203/Menuto/pull/138#issuecomment-6706823011)
for PIV-R138-01: independent WEEK period-map reconstruction was incomplete.

Correction `1e9000cf5122964393cd1cb1343719d378a7f936` updated:
`apps/backend/app/modules/validation/nutrition_policy_v2_rules.py`,
`apps/backend/tests/test_policy_v2.py`, and
`docs/product/MTR_006_POLICY_INTEGRATION_V2_IMPLEMENTATION_EVIDENCE.md`.
The independent checker enforces complete exact coefficient vectors per original root without importing
the producer evaluator. Nine source-authored TEST_ONLY WEEK regressions cover:
- Two conflicting-map negatives: producer `UNSUPPORTED/UNSUPPORTED_TEMPORAL_MAP`, null payload; checker `CONSISTENT/NOT_ADMITTED`.
- Two fully rehashed favorable forgeries on those same unsupported retained sources: checker `INCONSISTENT/NOT_ADMITTED`.
- Three equal-vector positives, including permitted non-unit non-daily coefficients.
- Two non-unit daily rejections, retaining all daily unit protection.

[Corrected-head CI 42385311029](https://github.com/thedusk4203/Menuto/actions/runs/42385311029) passed;
[independent re-review PASS 6709092185](https://github.com/thedusk4203/Menuto/pull/138#issuecomment-6709092185) closed
PIV-R138-01 at that exact head. Both PIV-R136-01 and PIV-R138-01 are resolved in the reviewed/frozen implementation.

The [post-merge completion receipt 6710291961](https://github.com/thedusk4203/Menuto/pull/138#issuecomment-6710291961)
records the completed merge gate. The formal freeze supersedes only its freeze-pending disposition.

## Exact post-merge execution evidence

[GitHub Actions push CI 42389669892](https://github.com/thedusk4203/Menuto/actions/runs/42389669892),
attempt 1, ran on exact merge SHA `45bb2677d3eb657dcf36aaf9fc5b9e146e8bf8fa` and completed
**SUCCESS**. Python/web and every workflow step passed; completed direct logs were inspected.

| Executed requirement | Result |
|---|---:|
| Full pytest | **4,369 passed / 0 skips** |
| Retained baseline | **4,183** |
| Additive v2 cases | **186 = 141 pure + 45 real PostgreSQL** |
| Mandatory acceptance mapping | **32 PIV-D families (PIV-D01–PIV-D32)** |
| Mandatory PostgreSQL obligations | **10/10 (PIV-PG01–PIV-PG10)**, covered by 45 executions |
| PIV-R138-01 regression additions | **9 differential cases** |
| Separate SCRAM/TLS smoke | **16/16** |
| Benchmark | **22/22** |
| Client | **10/10** |

Ruff, architecture/import boundaries, OpenAPI/domain exports, synthetic fixtures, client contracts,
typecheck and web build passed. All v2 cases, including real protected PostgreSQL paths, are part
of the unfiltered no-skip full suite. The full log retains six non-blocking warnings from existing dependencies.

## Frozen compatibility and persistence boundary

- **528 exports = 515 unchanged legacy definitions + exactly 13 additive v2 names**.
- All **503 historical definition hashes** individually match their historical pins.
- All **53 historical frozen source/migration files** are byte-identical and match their SHA-256 pins.
  All **59** pins in the complete v2 compatibility manifest match, including six MBA companions.
- Schema **0017 / 108 domain tables**; no migration **0018**.
- **ZERO NEW PERSISTENCE**; no new SQL tables, protected functions, roles or DB privileges.
- Frozen Root, MTR-006 v1, MTR-007 and MBA source contracts, runtime semantics and historical migrations unchanged.
- [Implementation evidence](MTR_006_POLICY_INTEGRATION_V2_IMPLEMENTATION_EVIDENCE.md) retains
  PIV-D01–PIV-D32 and PIV-PG01–PIV-PG10 mappings.

Fresh-install guard checks that the migrated empty PostgreSQL database has schema revision 0017,
empty Nutrition source tables, and zero v2 SQL objects or roles before isolated TEST_ONLY setup.
Fresh-install production Nutrition/clinical content, providers, qualifications, publications, seeds,
and defaults remain **0**.

## Exact bounded frozen semantics

1. One-session canonical Planning capture over existing authenticated sources, bound to a private
   one-shot lease and MBA registry registration; freshly checked before atomic consumption.
2. Complete source/precision/temporal/original-meaning IDL coverage; frozen v1 fixture-only inputs
   and child NOT_AUTHORIZED literals remain unchanged.
3. Retention of horizon/all-anchor periods and authored unit required period sums for DAY/WEEK profiles;
   source-authored bound projection remains distinct from nutrient conversion.
4. Protected hard constraints H and soft comfort constraints C derived from full joint assignments;
   absent joint support produces RESOLUTION_INSUFFICIENT, distinct from policy conflict, soft violations,
   and solver infeasibility.
5. Independent Validation-owned whole-policy reconstruction with no Nutrition evaluator oracle.
6. MBA error mapping preserves (outcome, reason) pairs; integrity rejections are not downgraded to unavailability.
7. Authenticated explicit NutritionPrecision with full source/actor/version/evidence identity.
8. Exact per-original-root complete coefficient-vector consistency for every FINITE_PERIOD_SUM.
9. Authored finite operator semantics, resource bounds, overflow failure, cancellation/kill/join,
   transaction/capture lifetime, registry checks, single-use consumption, and deterministic non-success.
10. TEST_ONLY taint, closed production admission, and UNVERIFIED_TRANSPORT non-authority boundaries.
    Fingerprints establish retained semantic identity, not canonical DB origin, present authorization,
    scientific correctness, planner readiness, or clinical authority.

## Preserved closed gates and historical records

**PRODUCTION NUTRITION/CLINICAL CONTENT GATE — CLOSED**. No production numerical values,
clinical protocols, supported-population declarations, qualified actors, providers, publications,
conversion rules, seeds, or defaults are authorized.

`planner_ready=False`; `activation_ready=False`; **Execution NOT STARTED; PRECOMMIT FAIL-CLOSED**.
Full **MTR-006/007/008 INCOMPLETE**; parent issues **#5/#6/#7 OPEN**. Nutrition Root, MTR-006 v1
structural synthesis, MTR-007 bounded estimator, and MBA applicability retain their prior freezes and semantics.
No MTR-008 implementation, solver activation, scientific conversion, parent issue closure, or downstream
implementation is part of this freeze/sync.

The approved designs, historical implementation evidence, and GitHub review/merge receipts remain unchanged.
Their candidate/NOT FROZEN wording describes the respective historical stages; this receipt supersedes
current freeze status only. Documentation synchronization changes no implementation body, contract,
test, export, tooling, migration, or data. The docs-only sync PR remains OPEN pending separate review.
