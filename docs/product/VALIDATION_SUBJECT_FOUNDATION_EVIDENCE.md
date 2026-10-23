# MTR-025 ValidationSubject / MTR-026 independent foundation evidence

2026-10-23. **READY FOR ARCHITECTURE/FREEZE REVIEW — foundation subset only.**
This does not complete the production Independent Validator or enable execution/activation.

## Decision and frozen baseline

[Review A–G](VALIDATION_SUBJECT_FOUNDATION_REVIEW.md) was written before implementation.
Selected dependency: canonical source facts → stable immutable ValidationSubject → independent
source-supported checks → later complete policy/grounding/scenario suite → PRECOMMIT authority
→ later execution. Blueprint G remains a completion audit; no milestone numbering is invented.

MTR-016 is user **APPROVED/FROZEN**, canonical main
`751a40e847dd2e664a6fe3667c272bc740a44e49`, migration0009,52 domain tables.
No concrete contradiction was found; its semantics/guards remain unchanged.
Published migrations0001–0009 have no diff. **No new table or migration is needed.**
Implementation commit: `fb298dd177197d1c22fbd0644ad4535e3b10b0b7`. PR/CI results are recorded below after remote execution.

## Implemented

- Versioned frozen/extra-forbid subject/report, exact source contracts and coverage policy.
  Subject status FOUNDATION_ONLY, validation_ready=False; report activation_authorized=False.
- Canonical serialization/hash of unordered fact collections, including explicit policy
  identity/provenance, selected proposal graph, current revision/frontier and source primitives.
  Decimal normalization/UTC/source IDs are preserved; no generated clock/UUID in validation.
- Read-only source capture in execution application orchestration using source public facades.
  Requires actual PostgreSQL read-only REPEATABLE READ/SERIALIZABLE. Captures immutable recipe
  versions, canonical household/member safety rows, catalog identities/nutrition references,
  proposal/parent revision and inventory full recorded history up to effective cutoff.
- Independent root identity/safety guards: participating member × authored default ingredient
  identities; canonical exclusions bypass summaries. Missing/foreign/ambiguous sources fail.
  Allergen/diet classification is unavailable in the current catalog: reported as unsupported,
  never inferred safe from missing tags or replaced with a global substitution rule.
- Default authored RecipeVersion/tier inputs and compatible reviewed nutrition-reference
  arithmetic recomputed without Recipe binder/candidate/Inventory calculator calls. Exactly
  one compatible reviewed reference is needed; no arbitrary provider selection or COUNT/AP
  mass conversion. These are batch INPUT nutrients, not final cooked/member meal totals.
- Exact contextual Retail AP→EP and Recipe EP_RAW→COOKED estimates from supplied source facts.
  Estimates remain distinct from physical movements/output and retain mapping/transformation IDs.
- Separate whole-history conservation and imperative chronological replay of current physical
  lots/movements/reservations/releases. Opening is ACQUIRE once, not acquisition plus lot quantity.
  Checks chronology, stock/reservation deficits, resolved expiry, owner/basis/asset identity,
  event phase/order, acquisition/correction/release references and cached closing positions.
- Deterministic structured findings (FATAL/ERROR/WARNING/INFO; DATA/POLICY/PLAN/EXECUTION),
  source proof refs, independent derived facts, policy/subject hashes. PRECOMMIT blocked or
  rejected; POSTFACT diagnostic, with zero repair/persistence side effects.

## Numeric and trust boundaries

All source quantities retain frozen Foundation storage semantics; derived nutrition uses
calculation Decimal72/36. Arithmetic contexts trap rounding/inexact results. A nonterminating
ratio or out-of-range calculation is reported unresolved, never silently quantized. No floats.
Material signed accounting amounts are calculation values, not negative physical quantities.
Incompatible bases cannot produce a derived closing quantity; raw/prepared assets stay separate.

The coverage policy is immutable metadata identifying supported foundation checks, explicitly
NO_CLINICAL_POLICY. It is not a second NutritionPolicyEngine and contains no invented clinical
constants. The full subject hash fingerprints mutable safety content, not a fabricated source
row-version. Inventory ledger_sequence is a household event frontier, not a global inventory
revision counter. Capture consistency is not cryptographic source attestation or a commit permit.

Validator consumes frozen source contracts only. It imports no runtime source facades, ORM,
DB client, solver, objectives, candidate generator or benchmark code. Source capture reads DB
outside the validator. Import checks also reject SQLite/network/file-IO backdoors. Existing
household bootstrap remains intact; new public functions add read-only source capabilities.

## Executed verification

Local full suite: **928 passed**, **445 PostgreSQL-real**; **68 new tests**
(59 unit/adversarial +9 PostgreSQL), **860 prior regression tests retained**.
Zero skipped/errors/failures. One existing Starlette/httpx deprecation warning.
Command: `python -m pytest --junitxml=.local/validation-tests.xml --tb=short`,
PYTHONPATH=apps/backend and MENUTO_TEST_POSTGRES_URL set to isolated real PostgreSQL18.4.
Run duration85.39s. Ruff/architecture/import/schema/OpenAPI/fixture drift checks pass.
Benchmark22/22; client10/10/typecheck/generated contracts and web build pass.

New unit/adversarial tests cover canonical hash/roundtrip/permutation, policy/material hash
changes, unsupported policy, primitive shared-member exclusions, forged safe summaries,
missing/cross-household sources, reviewed/default tier identities, missing/ambiguous/basis-
incompatible nutrition references, recurring ratio/no rounding, provenance and yield precision,
conservation vs consume-before-buy, expiry/negative/double consumption, causal sequence,
reservation-only allocation/release, raw/prepared coexistence, POSTFACT immutability,
ambient Decimal independence, IO prohibition and import-boundary violations.

Real PostgreSQL18.4 tests cover read-only RR/SERIALIZABLE capture, refusal of READ COMMITTED/
writable capture, canonical unsafe-source rejection, concurrent mid-capture safety mutation,
zero queries/writes by validation, unchanged52-table schema/head0009 and direct SQL inability
to mint authorization/publish from a partial report. Existing PostgreSQL migration up/down,
populated loss guards, SQL negative/concurrency and metadata-drift checks are retained.

Required checks: Ruff; architecture/import boundaries; domain/OpenAPI/fixture exports;
full prior regression; real PostgreSQL; benchmark22/22 (HARNESS_SMOKE_NOT_PLANNER_V4 only);
client10/10 + typecheck; web build; PR and postmerge CI. Exact executed results are recorded below.
No new persistence means no artificial0010 migration or separate migration corpus is added.
Domain contract bundle10 is an export version, **not** database migration0010.

## Structurally supported / deferred

The source snapshot can carry exact supported authored/default recipe facts and physical
ledger primitives into future validators. Current planned batches still lack exact grounded
rule/quantity binding and actual produced facts. No cooking execution is claimed.

Always deferred, typed and non-authorizing: root nutrition/goal/guideline policy; allergen/diet
classification; exact grounded binding; procurement scenario/package cost resolution; planned
material allocation feasibility; full batch-flow, revision materialization and assumption replay;
horizon bridge and production authorization/security/commit-source recheck. Report scope makes
these gaps explicit even if every implemented check passes. There is no full semantic PASS.

No NutritionPolicyEngine synthesis, optimizer/optimality proof, repair/replan, CookingBatchExecution,
MealExecution, import/receipt workflow, assumptions/autopilot, behavioral learning, AI or UX.
MTR-025 production coverage and the ten-validator MTR-026 suite remain **PARTIAL**.
Stop at architecture/freeze review of this foundation; do not start the next slice automatically.


POSTFACT in this foundation diagnoses the supplied physical history and default planned
exposure. It does not certify actual meal composition/member consumption allocations:
MealExecution/batch-flow source contracts and their independent checks remain deferred.
