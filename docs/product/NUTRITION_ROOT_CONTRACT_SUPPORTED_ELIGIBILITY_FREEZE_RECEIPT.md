# Nutrition Root Contract & Supported-Eligibility — structural freeze receipt

**NUTRITION ROOT CONTRACT & SUPPORTED-ELIGIBILITY FOUNDATION — FROZEN**

**STRUCTURAL FREEZE ONLY — PRODUCTION NUTRITION/CLINICAL CONTENT NOT AUTHORIZED**

**PRODUCTION NUTRITION/CLINICAL CONTENT GATE — CLOSED**

## Canonical implementation and freeze gate

- Implementation: [PR #123](https://github.com/thedusk4203/Menuto/pull/123).
- Approved implementation head: `7953e74c64ce0d2db06d802a9213c0b0ad27dd1d`;
  implementation base: `cb66f462f3ea7e8cf6e63a3cbe2d75db0d19a682`.
- [Implementation review 6500572389 — PASS](https://github.com/thedusk4203/Menuto/pull/123#issuecomment-6500572389).
- Actual merge / verified main: `6a77575fcb0ecf7a02493dae935fab88e94d09f1`.
- Actual merged tree: `3b2f7a210ebd75bc8e81555cab3d0e55a8b05ccf`, identical to the
  approved implementation tree. PR #123 contained 51 files and two reviewed commits;
  merge used the exact implementation-head guard with auto-merge OFF.
- Exact post-merge **push** [CI 40931231875](https://github.com/thedusk4203/Menuto/actions/runs/40931231875):
  **SUCCESS** on that merge/main SHA. Python/web and every required workflow step SUCCESS.
  PR CI 40883176488 is historical implementation-head evidence, not the post-merge gate.
- Canonical [freeze comment 6506156639](https://github.com/thedusk4203/Menuto/pull/123#issuecomment-6506156639).

## Verified regression, compatibility and durable scope

- **3,782 passed / 0 skips = 3,638 retained baseline + 144 additive**.
- **NRC01–NRC80** mapped; **66 actual PostgreSQL executions / 32 required obligations**.
- SCRAM/TLS **16/16**; benchmark **22/22**; client **10/10**;
  Ruff, architecture/import/export/OpenAPI/fixtures/contracts/typecheck/build green.
- **447 exports = 403 retained unchanged bodies/hashes + 44 additive definitions**;
  earlier frozen compatibility guards remain intact.
- Migration **0016**; **98 domain tables**, previously 85. Old migrations 0001–0015 unchanged.
- Approved durable addition: **13 source/authority tables + 1 sequence**
  (`nutrition_source_recorded_order`). This is new source persistence, not zero new persistence.
- **60 protected SQL functions = 5 entry points + 55 helpers/triggers**.
  Entry points in `menuto_nutrition`: `register_provider(jsonb)`, `enroll_principal(jsonb)`,
  `change_authority(jsonb)`, `append(jsonb)`, `capture(jsonb)`.
- The [implementation evidence](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_EVIDENCE.md)
  retains the exact durable object inventory and executed acceptance mapping.

Fresh-install verification on disposable real PostgreSQL confirmed all 13 new source tables
empty before TEST_ONLY enrollment/content: **production nutrition/provider/enrollment/seed/default
counts = 0**. This includes guideline providers, production reviewers/publishers/assessors,
guideline publications/numeric content, supported-population definitions, eligibility assertions,
seeded member goals and default nutrition policies. The three infrastructure NOLOGIN roles are
not enrolled source actors or production content. Isolated TEST_ONLY fixtures are not installed
production truth. This records fresh-install state; it does not claim a production deployment audit.

## Frozen semantics and content boundary

Nutrition source authority stays independent of Preferences/prior/hierarchy authority. Privileged
enrollment/admin remains separate from ordinary source operations. Guideline review and publication
require distinct capabilities and different verified humans; hashes, labels and login aliases do
not supply authority. Protected PostgreSQL identity/grant/CAS/idempotency/lifecycle enforcement and
direct-runtime-DML prohibition remain unchanged. Goals/observations remain exact-subject scoped;
household OWNER/EDITOR alone grants no representative authorship.

Eligibility remains `SUPPORTED | UNSUPPORTED | INELIGIBLE | UNKNOWN`; missing evidence never
becomes healthy/default-supported. Roots remain `RANGE | MINIMUM | MAXIMUM | TARGET`, with TARGET
a reference center, not an inferred hard interval. Exact descriptor matching precedes rational
containment arithmetic. No implicit unit/temporal conversion, invented bound or BMR/TDEE safety
default; NutritionPrecision, CostPreference/Budget, KitchenEffort/convenience and TasteFit cannot
mint or weaken root truth.

Capture remains one authenticated, clean, caller-owned read-only REPEATABLE READ/SERIALIZABLE
reader connection, complete/all-or-fail with retained frontiers and absence witnesses. No cut
splicing, favorable truncation, unrelated-member leakage or fake common MVCC across sessions.
Pure replay remains zero-I/O. Fingerprints prove retained identity/tamper self-consistency, not
canonical DB origin, current authorization/publication or scientific correctness. Independent
root validation reconstructs source/eligibility/authorship/containment without using producer
`root_resolution` business logic as its oracle; it is not full MTR-026 or full-plan validation.

The structural freeze grants no approval for real calorie/nutrient values, clinical thresholds,
BMR/TDEE policy, supported-population definitions, exclusion/eligibility protocols, provider
authority, reviewer/assessor qualifications, production guideline editions, member clinical
eligibility, production defaults or seeds. These remain behind a separately authorized
**NUTRITION CONTENT / EVIDENCE / QUALIFICATION AUTHORITY GATE**.

`policy_synthesis=NOT_PERFORMED`; `numeric_goal_protection=NOT_SYNTHESIZED`;
`planner_ready=False`; `activation_ready=False`. Full MTR-006 and MTR-008 remain incomplete.
MTR-040 COMPLETE; MTR-039 OPEN; full MTR-041/MTR-046 PARTIAL; MTR-024/MTR-020B/MTR-021 BLOCKED;
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED; planner activation disabled.

This receipt synchronizes the existing canonical freeze only. Historical design and delivery-stage
evidence grant no production content authority. No dependency review, next-gate selection, design,
implementation, migration 0017, issue closure or downstream authorization is part of this status sync.
