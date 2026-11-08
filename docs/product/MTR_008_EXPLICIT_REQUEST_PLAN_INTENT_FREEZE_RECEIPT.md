# MTR-008 explicit-request orthogonal plan-intent resolution — bounded structural freeze receipt

**MTR-008 PURE-ONLY EXPLICIT-REQUEST ORTHOGONAL PLAN-INTENT RESOLUTION — STRUCTURALLY FROZEN / TEST_ONLY**

**PRODUCTION NUTRITION/CLINICAL CONTENT GATE — CLOSED**

This records the owner's conditional bounded structural freeze after exact post-merge verification.
It is documentation synchronization, not a new freeze decision, full MTR-008 completion,
authenticated request authority, numerical policy admission or planner readiness.

## Canonical design, implementation and decisions

| Record | Canonical identity |
|---|---|
| Approved bounded design | [PR #142](https://github.com/thedusk4203/Menuto/pull/142), reviewed head `584ef315ce46bf9304d85de724c2fbdf85575c90` |
| Independent design PASS | [6719067953](https://github.com/thedusk4203/Menuto/pull/142#issuecomment-6719067953) |
| Verified design merge / implementation base | `b7992898698a8a8a3493b3c260939325cc494063` |
| Design merge completion | [6719670106](https://github.com/thedusk4203/Menuto/pull/142#issuecomment-6719670106) |
| Implementation | [PR #143](https://github.com/thedusk4203/Menuto/pull/143), 3 commits / 28 approved files |
| Reviewed implementation head | `24a868a601b5c7060ac76af952fe5b33ca6f636f` |
| Independent implementation technical PASS | [6722974021](https://github.com/thedusk4203/Menuto/pull/143#issuecomment-6722974021) |
| Frozen implementation merge | **`40875d95f81390f3985cc0e2ad4600b1e494dacb`** |
| Frozen implementation tree | **`a6f53925857898ce0d63c30f4da5b55890e7d374`** |
| Verified post-merge completion | [6724098947](https://github.com/thedusk4203/Menuto/pull/143#issuecomment-6724098947) |
| Formal owner-authorized bounded structural freeze | [6724106966](https://github.com/thedusk4203/Menuto/pull/143#issuecomment-6724106966) |

The owner's “PR #143 Merge, Verification & Conditional Structural Freeze” authorization required
complete Phase 2 verification before freeze. Both completion and freeze comments were read back
and matched to the submitted bodies. The freeze applies only to this pure-only structural slice.
The separate docs-sync PR is authorized for review, not automatic merge.

Merge parents, in order, are exactly the approved base
`b7992898698a8a8a3493b3c260939325cc494063` and reviewed head
`24a868a601b5c7060ac76af952fe5b33ca6f636f`. Resulting tree equals reviewed-head tree;
the approved 28-file implementation delta contains no source divergence.
Merge used the exact-head SHA guard and merge-commit method under required branch protections,
with auto-merge OFF and no bypass, squash, rebase or force-push.

**Later documentation commits do not replace this implementation merge/tree.**

## Exact merged-main execution evidence

[Foundation checks push CI 42495459642](https://github.com/thedusk4203/Menuto/actions/runs/42495459642)
ran on exact merge `40875d95f81390f3985cc0e2ad4600b1e494dacb`, attempt 1, and completed **SUCCESS**.
Python job `128776721364`, web job `128776721589` and every listed workflow step succeeded.
Direct completed logs were inspected; pre-merge PR CI was not substituted for this run.

| Executed requirement | Result |
|---|---:|
| One complete pytest run | **4,611 passed / 0 skips**, six retained warnings, 3541.07 seconds |
| Retained regression baseline | **4,369** |
| Additive pure/architecture/adversarial tests | **242** |
| Acceptance mapping | **EPI001–EPI064: 64/64** |
| New EPI-specific PostgreSQL authority obligations | **0**; retained real PostgreSQL corpus still executes |
| Dedicated SCRAM/TLS smoke | **16/16** |
| Benchmark | **22/22** |
| Client | **10/10** |

Ruff, architecture/import boundaries, OpenAPI/domain exports, synthetic fixtures, client contracts,
typecheck and web build passed. The acceptance manifest maps every EPI identifier to executed
named tests/parameters; test totals are not sums of separately executed runs.

[Implementation evidence](MTR_008_EXPLICIT_REQUEST_PLAN_INTENT_IMPLEMENTATION_EVIDENCE.md),
[execution receipt](MTR_008_EXPLICIT_INTENT_EXECUTION_RECEIPT.json) and
[authorized compatibility diff](MTR_008_EXPLICIT_INTENT_AUTHORIZED_COMPATIBILITY.diff)
remain historical stage records. Their pre-submission `exact_head_ci: PENDING` snapshot is
superseded as current CI evidence by the completed runs and receipts here, without rewriting history.
The first PR run failed the new EPI028 subprocess import-path test; the final reviewed correction
only made that new test's subprocess paths explicit. Final-head
[PR CI 42480721695](https://github.com/thedusk4203/Menuto/actions/runs/42480721695) and the separate
merged-main push run above both succeeded. No historical behavior test or runtime workaround was used.
The separately reported 700-case byte-mutation diagnostic is not added to pytest totals.

## Exact bounded semantics and nine contracts

The frozen implementation consists of Policy-owned immutable contracts and pure interpretation,
a minimal pure public facade, and Validation-owned independent checking.

| Exported immutable versioned contract | Bounded role |
|---|---|
| `ExplicitPlanIntentContextV1` | Declared request context/correlation; no authenticated origin |
| `ExplicitPlanIntentBudgetV1` | Exact NONE / TARGET / SPEND_LIMIT intent |
| `ExplicitPlanIntentRequestV1` | Fully explicit four-axis input |
| `ExplicitPlanIntentValuesV1` | Independently retained axis values |
| `PlanIntentAxisEvidenceV1` | Axis-local retained interpretation evidence |
| `ResolvedExplicitPlanIntentV1` | TEST_ONLY resolved values and evidence |
| `PlanIntentDiagnosticV1` | Deterministic failure detail |
| `PlanIntentResolutionV1` | Producer outcome and optional payload |
| `PlanIntentCheckV1` | Independent reconstruction/check result |

These are exactly the nine names in the committed additive manifest, not a new registration request.
NutritionPrecision, CostPreference, KitchenEffort and BudgetContract are independent axes.
All request keys remain required. Missing intent never silently becomes a default, precedence
rule, BudgetPressure, economics weight, clinical limit or kitchen-time coefficient.
Money retains strict exact minor units and currency identity; explicit zero is a real value.
No foreign-exchange, currency-exponent or numerical budget-policy derivation is introduced.

The producer and checker have strict bounded parsing, deterministic fingerprints and non-success
semantics. The checker reconstructs from retained primitive input using its own parsing and
interpretation, without importing the producer resolver/public facade/helpers as an oracle.
Complete claims and ordered evidence are checked, not merely a matching fingerprint or report label.
Negative/adversarial cases cover malformed and missing inputs, forged claims, tampering, invalid
types, boundary overflows, resource exhaustion and independent reconstruction differences.

Fingerprints establish retained semantic identity, not authenticated origin, member authorship,
source authority or admission. A coherently replaced source and claim may be offline-consistent
while remaining unauthenticated. Serialized CONSISTENT labels do not grant numerical authority.

All outputs preserve **TEST_ONLY**, **UNAUTHENTICATED_DECLARATION**, **UNVERIFIED_TRANSPORT**,
numerical use **NOT_ADMITTED**, production admission **CLOSED**,
`resolved_plan_policy_ready=False`, `planner_ready=False`, `activation_ready=False`.
There is no adapter to frozen NutritionPrecision selection, PIV leases or planner consumer admission.

## Immutable compatibility and source boundary

- **537 exports = 528 unchanged definition bodies + exactly nine additive names**.
- All **515 legacy definition hashes** and **503 historical pinned hashes** remain checked.
- All **53 historical frozen files** and **59 complete PIV file pins** match their byte hashes.
- Exactly authorized metadata changes in eight historical test files / 17 blocks preserve
  historical integrity assertions. PIV-D31 retains its old exact-set/hash/preimage comparisons;
  the new bounded normalization and exact nine-name set do not replace historical expected digests.
- The exact named-contract import allowance permits only the nine immutable contracts from
  `policy.explicit_intent_contracts` to `validation.explicit_plan_intent`. It grants no generic
  Validation-to-Policy, wildcard, producer/public/helper or transitive implementation access.
- Schema remains **0017 / 108 domain tables**, no **0018**.
- **ZERO NEW PERSISTENCE**; no new SQL objects, roles, DB privileges or production endpoints.
- The committed fresh-install execution evidence records zero rows in all 23 canonical Nutrition
  Root/synthesis tables, including production content/providers/enrollments/qualifications/
  publications/seeds/defaults. The implementation delta has no source/data installation change.
- Root/NPS/NRE/MBA/PIV frozen contracts, accepted behavior and historical migrations remain intact.

The PIV frozen identity remains merge `45bb2677d3eb657dcf36aaf9fc5b9e146e8bf8fa` /
tree `19c97149aeaaf108894e7a3d01afd0db4558e9e9`; MBA remains merge
`9d3b580ce2a2d111223b37814612a4072dbfe6a2` /
tree `3a68035f9c33de152b3899a083d534a537c647e1`.

The original worktree's HEAD, full modified/untracked inventory and SHA-256 of all **19 original
local files** matched the protected pre-implementation snapshot after post-merge CI. None of
those local changes were reset, discarded, overwritten, committed or published by this gate.

## Documentation synchronization and preserved gates

This docs-only branch starts from the frozen implementation merge. It updates only this receipt
and the current-status sections in BACKLOG, FOUNDATION_STATUS and both implementation blueprints.
Earlier design/research/implementation evidence is retained as historical context. The docs PR's
own exact-head CI checks its tree separately; it cannot substitute for the implementation push CI.
The PR remains **OPEN / auto-merge OFF** for independent documentation review.

This freeze excludes authenticated capture, defaults/week context/override precedence, source
lifecycle, numerical policy composition, economic/kitchen numerical policies, full
ResolvedPlanPolicy, PIV lease expansion, planner consumer admission, solver and activation.
No downstream design or implementation is started or authorized by this synchronization.

- Full **MTR-006/007/008 INCOMPLETE**; issues **#5/#6/#7 OPEN**.
- **Production Nutrition/clinical content gate CLOSED**; no clinical values, qualified actors,
  providers, publications, defaults or seeds authorized.
- `planner_ready=False`; `activation_ready=False`.
- Execution **NOT STARTED**; PRECOMMIT **FAIL-CLOSED**.

**MTR-008 PURE-ONLY STRUCTURALLY FROZEN / TEST_ONLY / PRODUCTION GATE CLOSED.**
