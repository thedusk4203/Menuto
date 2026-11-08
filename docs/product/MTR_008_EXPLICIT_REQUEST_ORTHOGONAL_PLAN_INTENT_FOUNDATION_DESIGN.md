# MTR-008 — Explicit-Request Orthogonal Plan Intent Foundation: Detailed Design

**Status: ARCHITECT-AUTHORED DESIGN CANDIDATE / READY FOR INDEPENDENT REVIEW / NOT APPROVED FOR IMPLEMENTATION**

**Scope:** A first, pure, source-unverified and non-activating structural slice of MTR-008 (**STRUCTURAL / TEST_ONLY**). It is **not** the complete PlanPolicyResolver or ResolvedPlanPolicy of ADR-003.

**Design baseline:** Menuto `main` merge `6df908d4295d2b96260eb633e936e35e49c2285d`; tree `700dbaccbeb2d6cb074cdd5135cdf4ae02f7851f`. PR #140 is merged; post-merge push CI `42449622472` completed SUCCESS (4,369 pytest passed / 0 skips, Python/web successful). Frozen MTR-006 Policy Integration v2 identity remains implementation merge `45bb2677d3eb657dcf36aaf9fc5b9e146e8bf8fa`, tree `19c97149aeaaf108894e7a3d01afd0db4558e9e9`.

**Authority:** Proposed independent-architect design. Publishing this document neither authorizes its implementation nor its merge, downstream MTR-008 activation, clinical use, or a new scientific/nutrition policy source. This decision is separate from the owner-authorized research PR #140.

## 1. Evidence and architectural decision

Read and preserve:

- `docs/product/POST_MTR_006_POLICY_INTEGRATION_V2_DEPENDENCY_REVIEW.md` §§2–9, which selects explicit-request orthogonal interpretation as the smallest candidate and explicitly leaves pure-only vs authenticated capture to architecture.
- `docs/adr/ADR-003-plan-policy-resolution.md`: NutritionPrecision, CostPreference, KitchenEffort/optional DailyAvailability, and BudgetContract are orthogonal; BudgetPressure is system-derived, not preference; defaults/overrides and versioned ResolvedPlanPolicy belong to the **full** resolver.
- `docs/MENUTO_DEVELOPMENT_SPEC_V1_3.md` §§8.1 and 10.9–10.10; `docs/ARCHITECTURE_INVARIANTS.md` INV-001/002/010/028.
- `apps/backend/app/domain/snapshots.py`: existing frozen `PlannerRequestDraft` already carries required `nutrition_precision`, `cost_preference`, `kitchen_effort`, `budget`, actor, household, tracked member, horizon, revision triple and source versions. `BudgetContract` uses `NONE | TARGET | SPEND_LIMIT`, with `Money.amount_minor` and exact currency.
- `apps/backend/app/modules/policy/contracts.py`: currently defines only `ValidationCoveragePolicySnapshot`; do **not** repurpose it into a resolved policy.
- `apps/backend/app/modules/nutrition/synthesis_contracts.py`: `NutritionPrecisionSelection` can carry `REQUEST_EXPLICIT` plus authenticated evidence in frozen Nutrition paths. A mere `PlannerRequestDraft` string is **not** that verified selection.
- `apps/backend/app/modules/nutrition/policy_v2_public.py`: frozen purpose `STRUCTURAL_TEST_ONLY_INSPECTION`, no planner consumer admission. No additional use/lease is granted.
- `apps/backend/app/domain/feature_identity.py`: `identity_hash` preserves list order and rejects float input; avoid `app.domain.canonical.canonical_hash` for request identity because it sorts *all* lists and could erase meal/source order.

**Decision D1 — PURE-ONLY:** First slice accepts **raw UTF-8 JSON bytes representing one full `PlannerRequestDraft`**. It performs bounded strict parsing and a mechanical projection of declared fields. No PostgreSQL connection, transaction, trusted DB capture, role assertion, credential, enrollment lookup, or source admission exists. It is an internal, standalone structural utility rather than a live HTTP endpoint.

**Decision D2 — Truth boundary:** “Explicit” means the field was **present in the retained raw request document**, not that it was genuinely authored or approved by an authenticated user. `actor_user_id`, `sources`, fingerprints, and labels are *unverified claims* from that document. A downstream planner must not consume this projection as user authorization, authenticated Policy-owned NutritionPrecisionSelection, source truth, clinical policy, numerical policy, or activation proof.

**Decision D3 — No defaults:** No source reads or derivations. No `STANDARD`, `NORMAL`, `MAINTAIN`, budget `0`, unlimited spend, time allowance, weight, tolerance, `BudgetPressure`, precision provenance, or current-week context is fabricated. If a caller omits a required field, reject it rather than rebuilding an apparently valid request.

**Decision D4 — Non-upgradeable seam:** This design emits a versioned **`ExplicitPlanIntentProjectionV1`** and **`ExplicitPlanIntentCheckV1`**, not `ResolvedPlanPolicy`, positive `ValidationReport`, plan feasibility, or `PolicyV2Use`. A future authorized MTR-008 step must introduce authenticated source capture and independently validated composition as separate versioned contracts, not reinterpret this one.

## 2. Exact bounded scope

**In scope:** Read full raw request; enforce syntax and structural limits; validate using the existing `PlannerRequestDraft` without changing it; retain exact declared axis values; preserve whole-request/actor/subject/horizon/version/source/revision identity; calculate domain-separated canonical hashes; rederive independently in Validation; produce deterministic explicit non-success; add focused pure and adversarial tests.

**Out of scope:** Defaults/profile/week context/overrides; merge precedence; server-authenticated intent or user approval; new policy tables; inference from behavioral data; economic tolerance/pressure/scenarios; kitchen prep durations and per-day envelopes; Nutrition Root/NRE/MBA/PIV numerical evaluation; clinical inputs; complete `ResolvedPlanPolicy`; planner/solver/API/scheduler/UI; relaxation; preview/activation and PRECOMMIT. Shared meal participant semantics are retained only through the input hash, not reinterpreted as allocation or safety validation.

**Persistence and public surface:** No migration 0018, no new persistence, no SQL objects, no new API route or registered public/exported domain schema definitions. Preserve exactly **528 existing exports** and all historical pins. The proposed internal types are *not* added to `tools/export_domain_contracts.py`, `packages/contracts/domain.schema.json` or OpenAPI; exposing them later needs an independent additive export authorization.

## 3. Proposed module and dependency boundaries

Implementation target files, only after review/owner authorization:

| Path | Responsibility |
| --- | --- |
| `apps/backend/app/modules/policy/explicit_intent_contracts.py` | New immutable, internal-only Pydantic carriers and no-authority literals |
| `apps/backend/app/modules/policy/explicit_intent.py` | Bounded raw input parsing, required-field checks, mechanical projection, deterministic fingerprint/result |
| `apps/backend/app/modules/validation/explicit_plan_intent.py` | Independent source-based reconstruction; never imports producer implementation |
| `apps/backend/tests/test_explicit_plan_intent.py` | Normal, orthogonality, budget, identity and resource-bounds proofs |
| `apps/backend/tests/test_explicit_plan_intent_adversarial.py` | Forgeries, negative/consistency controls, no-authority regression |

Policy implementation may import `app.domain.snapshots`, `app.domain.contracts`, `app.domain.units`, `app.domain.feature_identity` and **its own** new contracts. Validation may import those shared immutable domain and Policy contract definitions, but **must not import `policy.explicit_intent` or call its parser/projection function**. No cross-context service calls, DB dependencies or network dependencies.

If import-boundary tooling needs an additive registration for the new modules, it must be minimal and independently reviewed, without broadening existing import permissions. Ordinary module imports consistent with existing context constraints are preferred.

## 4. Input contract and canonical semantics

Public-within-process entry points (exact proposed callable names):

```python
def interpret_explicit_plan_intent(request_document: bytes) -> ExplicitIntentInterpretationV1: ...

def check_explicit_plan_intent_independently(
    request_document: bytes,
    claimed: ExplicitIntentInterpretationV1 | bytes,
) -> ExplicitPlanIntentCheckV1: ...
```

1. The sole authoritative *comparison input within this test-only exercise* is `request_document`; the resulting projection is a claim to be checked. Raw bytes are not authenticated database evidence. The checker must have the **retained source bytes**; a detached projection/hash alone is never admissible.
2. Accept only strict UTF-8 JSON top-level object. Reject duplicate JSON keys at *every nesting level* (including duplicated budget or identity), NaN/Infinity, invalid UTF-8, unexpected model fields, unrepresentable Unicode, and malformed/non-object input. Parse JSON numbers as exact primitives (no binary float representation); existing strict `Money.amount_minor` integer and `PositiveDecimal` bounds remain decisive.
3. Before creating `PlannerRequestDraft`, ensure raw top-level keys `household_id`, `actor_user_id`, `tracked_member_id`, `horizon`, `nutrition_precision`, `cost_preference`, `kitchen_effort`, `budget`, `meals`, `sources`, `planner_version`, and `policy_version` are present. `budget.constraint` must be present. For TARGET/SPEND_LIMIT require explicit `budget.amount` with `amount_minor` and `currency`; for NONE require amount absent or null. A decimal/string zero is not an allowed substitute for the strictly typed integer zero. The three revision fields must satisfy the existing all-or-none invariant.
4. Validate via unmodified `PlannerRequestDraft`. Preserve its existing enum sets, all source/participant/meal invariants, timezone-normalized horizon, exact budget currency and revision rules. No acceptance beyond what it declares is implied. Do not reclassify a domain validation failure as a physiological hard conflict, infeasibility or user-policy relaxation.
5. Declare structural budgets: source `request_document` **<= 256 KiB**; decoded tree **<= 10,000 nodes** and **<= 32 levels deep**; `meals` **<= 128**; `participants` **<= 32 per meal**; `sources` **<= 128**; result/check serialized bytes **<= 64 KiB**. Oversize/over-depth must return an explicit bounded non-success with no partial projection. A hostile nested JSON parser recursion/Unicode failure cannot bubble as success. These are computational limits, not implicit planning-horizon or meal-frequency rules. Never truncate a source list or meal list to fit.
6. Compute `request_fingerprint` as `identity_hash({"domain": "menuto.mtr008.explicit-request.v1", "request": validated_draft})` using canonical exact `feature_identity` mechanics, preserving ordered request collections. Compute source-manifest fingerprint as `identity_hash({"domain": "menuto.mtr008.source-manifest.v1", "sources": validated_draft.sources})`. Field order, legitimate UTC-equivalent timestamps and equivalent accepted exact decimal representations have canonical semantics; changes to list order do not collapse silently.
7. No authority arises because the request contains a plausible actor ID, a source fingerprint, a `policy_version`, or a `planner_version`. All such values remain `REQUEST_DECLARED_UNVERIFIED`.

## 5. Immutable internal carrier schema

Use Pydantic `Contract` (`frozen=True`, `extra="forbid"`) and existing primitive enum types. Proposed class fields and versions:

```python
class ExplicitPlanIntentIdentityV1(Contract):
    contract_version: Literal["explicit-plan-intent-identity.v1"]
    household_id: UUID
    actor_user_id: UUID
    tracked_member_id: UUID
    horizon: Horizon
    planner_version: Identifier
    policy_version: Identifier
    plan_id: UUID | None
    expected_revision: Version | None
    baseline_hash: Sha256 | None
    request_fingerprint: Sha256
    sources_fingerprint: Sha256

class ExplicitPlanIntentAxesV1(Contract):
    contract_version: Literal["explicit-plan-intent-axes.v1"]
    nutrition_precision: Literal["RELAXED", "STANDARD", "PRECISION"]
    cost_preference: Literal["LOW", "NORMAL", "HIGH"]
    kitchen_effort: Literal["MINIMAL", "NORMAL", "FLEXIBLE"]
    budget: BudgetContract
    provenance: Literal["REQUEST_DECLARED_UNVERIFIED"]

class ExplicitPlanIntentProjectionV1(Contract):
    contract_version: Literal["explicit-plan-intent-projection.v1"]
    identity: ExplicitPlanIntentIdentityV1
    axes: ExplicitPlanIntentAxesV1
    environment: Literal["TEST_ONLY"]
    authority: Literal["UNVERIFIED_TRANSPORT"]
    policy_compilation: Literal["NOT_PERFORMED"]
    clinical_admission: Literal["CLOSED"]
    planner_ready: Literal[False]
    activation_ready: Literal[False]

class ExplicitIntentInterpretationV1(Contract):
    contract_version: Literal["explicit-plan-intent-interpretation.v1"]
    outcome: Literal["PROJECTED_TEST_ONLY", "INVALID_REQUEST", "RESOURCE_EXCEEDED"]
    projection: ExplicitPlanIntentProjectionV1 | None
    diagnostics: tuple[Identifier, ...]       # bounded: <= 8
    result_fingerprint: Sha256
    authority: Literal["UNVERIFIED_TRANSPORT"]
    planner_ready: Literal[False]
    activation_ready: Literal[False]

class ExplicitPlanIntentCheckV1(Contract):
    contract_version: Literal["explicit-plan-intent-check.v1"]
    decision: Literal["CONSISTENT", "INCONSISTENT", "RESOURCE_EXCEEDED"]
    reconstructed_outcome: Literal[
        "PROJECTED_TEST_ONLY", "INVALID_REQUEST", "RESOURCE_EXCEEDED"
    ] | None
    findings: tuple[Identifier, ...]           # bounded: <= 8
    numerical_use: Literal["NOT_ADMITTED"]
    source_origin: Literal["NOT_PROVED_OFFLINE"]
    current_authorization: Literal["NOT_CLAIMED"]
    planner_ready: Literal[False]
    activation_ready: Literal[False]
```

The interpretation requires **projection iff `outcome == PROJECTED_TEST_ONLY`**; all failures carry `projection=None`. Enforce this with model validation, including hostile directly constructed carrier objects. A success has no diagnostics. Use a domain-separated `result_fingerprint` over every interpretation field **except itself**; it is a consistency checksum, never a signature or admission credential.

Diagnostics are restricted to `MISSING_EXPLICIT_FIELD`, `INVALID_STRUCTURE`, `INVALID_VALUE`, `INVALID_BUDGET`, `RESOURCE_LIMIT`, `INVALID_CLAIM`, and `CLAIM_MISMATCH`; deterministic one-primary-code reporting is preferable to leaking exception internals. No body, source locator, credential, clinical fact, actor secret or raw user content is included in a diagnostic. For non-success results the checksum still covers the exact outcome and diagnostic.

No `DailyAvailability`, `BudgetPressure`, source proof, clinical numeric restriction, policy range, preparation duration, feasible flag, `ResolvedPlanPolicy` or consumer lease appears in these carriers.

## 6. Interpretation algorithm and independent checker

**Interpreter**:

1. Bounded bytes decode/parse with duplicate-key rejection and structural work limits; on limit return `RESOURCE_EXCEEDED`, on invalid request return `INVALID_REQUEST`.
2. Require explicit raw keys and exact `BudgetContract` meaning; validate the existing `PlannerRequestDraft`, fail closed.
3. Derive identity from the **validated request**, including exact request/source fingerprints. Copy the four axes unchanged and mark provenance unverified. Neither request hash nor policy version is source authenticity.
4. Assemble one immutable `ExplicitPlanIntentProjectionV1`; enforce output byte bound; wrap in `PROJECTED_TEST_ONLY` with domain-separated result checksum. Do not evaluate Nutrition, budget feasibility or kitchen effort into numbers.

**Validation-owned checker**:

1. Independently parse the **same retained raw input** and re-evaluate presence, duplicate keys, limits and existing `PlannerRequestDraft` constraints. Shared primitive Pydantic types and canonical hashing are permitted; importing/calling the interpreter, its business parser or a cached asserted report is prohibited.
2. Independently reconstruct every identity field, both fingerprints and every axis, plus the no-authority constants and iff-state rules. Deep-compare the **entire exact structured claim**, then verify the result checksum from the observed claim; merely checking a checksum or claimed `CONSISTENT` field is insufficient.
3. A faithful negative and its exact diagnostics can be `CONSISTENT`, but numerical use remains `NOT_ADMITTED`. A favorable rehash of a missing/invalid request, changed budget/currency/precision/actor/source/temporal/revision or altered TEST_ONLY constant is `INCONSISTENT`.
4. Parse errors in a submitted claimed document produce a bounded inconsistent/no-admission check; source-resource exhaustion yields `RESOURCE_EXCEEDED`/no-admission. Never emit a positive projection from source failure.
5. A `CONSISTENT` result means **only** retained source-document semantic consistency; not verified user authorship, current database authorization, clinical applicability, MTR-006 v2 admission, hard feasibility, planner readiness, or activation.

No caller-provided checker result may be replayed as an authority token. Source and claim must be rechecked together each time.

## 7. Mandatory acceptance/test matrix

Each ID denotes at least one independent test or explicit parametrized subcase; test assertions, not merely test names, must establish the stated property.

| ID | Mandatory proof |
| --- | --- |
| PI01 | Full valid explicit request projects exactly four axes; producer and independent checker agree; no authority |
| PI02 | Change only NutritionPrecision; all other projected axes identical, request checksum changes |
| PI03 | Change only CostPreference; other axes stay unchanged, no derived numerical cost/pressure |
| PI04 | Change only KitchenEffort; no inferred minutes or daily availability |
| PI05 | Budget NONE with null/absent amount retained as NONE, not unlimited numerical policy |
| PI06 | TARGET amount_minor=0 with explicit currency survives exactly |
| PI07 | SPEND_LIMIT amount_minor=0 with explicit currency survives exactly, not feasible/unlimited |
| PI08 | TARGET/SPEND_LIMIT without amount; NONE with amount; malformed amount/currency reject |
| PI09 | Required axis omitted, invalid enum, malformed actor/household/subject reject without defaults |
| PI10 | Valid timezone-equivalent horizon inputs canonicalize; changed instant or interval rejects a prior claim |
| PI11 | Same actor/subject but changed source version/fingerprint or source order invalidates previous claim |
| PI12 | Revision triple absent, complete, partially supplied; respect existing all-or-none invariant |
| PI13 | Two requests differing in meals/participants cannot share the full request binding |
| PI14 | Nested duplicate JSON key, invalid UTF-8, float-derived invalid money, NaN/Infinity and invalid top-level type fail closed |
| PI15 | Input bytes/tree depth/tree node/source count/meal count/participant count/output budget reject explicitly, never truncate |
| PI16 | Tamper any axis and rehash claimed result: independent checker detects mismatch |
| PI17 | Tamper actor, household, tracked member, horizon, policy/planner versions or revision; fully rehashed check rejects |
| PI18 | Forged positive result for missing/invalid request, including rehashed checksum, cannot be admitted |
| PI19 | Faithful invalid input has exact bounded negative result and `CONSISTENT / NOT_ADMITTED` independent check |
| PI20 | Directly constructed malformed Pydantic success/failure carriers cannot violate payload-iff-success or TEST_ONLY/no-authority literals |
| PI21 | No import/call into Nutrition producer, PIV lease/capture, DB, HTTP, solver, PRECOMMIT or live Validation report |
| PI22 | Determinism for identical retained source bytes and accepted canonical-equivalent field/key ordering, without treating unverified source hashes as authority |
| PI23 | Existing exports remain 528, frozen hashes/files unchanged; no new schemas, migrations, roles, tooling shortcuts or public routes |
| PI24 | All existing 4,369 baseline tests remain passing with 0 skips; required real-PG, SCRAM/TLS, web/client, benchmark and architectural guards stay green |

For identity and source sensitivity, include positive controls (an unchanged valid claim) and **fully rehashed hostile controls**; never infer checker independence from a self-roundtrip. Report test counts separately; do not sum an additional focused suite into the full-suite total.

## 8. Work packages and review gates

**WP0 — Baseline and governance:** Prove exact main/tree; new isolated implementation worktree, preserve original 19 local changes; archive current manifest and test baseline; identify exact diff allowlist.

**WP1 — Internal immutable contracts:** Implement five internal carriers and validation invariants in `policy/explicit_intent_contracts.py`; no public export registration and no authenticated/clinical claim fields beyond closed literals.

**WP2 — Bounded interpreter:** Implement `interpret_explicit_plan_intent` in `policy/explicit_intent.py`; strict JSON and explicit raw presence; existing `PlannerRequestDraft` validation; domain-separated hashes; typed negative outcomes and resource bounds.

**WP3 — Independent checker:** Implement `check_explicit_plan_intent_independently` in `validation/explicit_plan_intent.py`; independent source reconstruction, not producer oracle; reject fully rehashed favorable tampering and no raw-source replay.

**WP4 — Proof/test harness:** PI01–PI24 positive, negative, metamorphic, resource and forgery tests. No mocks for source authority because source authority is deliberately **not** asserted. Preserve real-PG regression evidence for unchanged existing paths.

**WP5 — Verification:** `ruff`, architecture/import guards, export snapshots, full no-skip pytest, real SCRAM/TLS smoke, web/client, synthetic fixture and benchmark; report exact HEAD and all run IDs. Code implementation must be a separate PR, not this design PR.

**Design review gate:** This detailed design is reviewable on its own without running code. Before implementation, an independent reviewer must confirm:
- strict raw-document input is sufficient to prove **presence only**, not user consent or membership;
- `feature_identity.identity_hash` domain separation and order retention are correct;
- existing `PlannerRequestDraft`, `BudgetContract`, `Money` and frozen Nutrition precision contracts are unmodified;
- no import-boundary expansion or positive unverified authority is smuggled into `Validation`;
- budget semantics, rejection rules and adversarial independence are complete;
- precise acceptance IDs PI01–PI24 are implementable without adding new persistence or numerical policy.

An independent **DESIGN PASS** and separate **owner implementation authorization** are required to begin the WP0–WP5 code PR. No self-approval or auto-merge. If an irreconcilable code-level incompatibility is discovered, document the exact source and stop for architecture correction; do not silently widen this scope.

## 9. Absolute governance invariants

MTR-006 v1 / MTR-007 / MBA / MTR-006 v2 and their source/Validation semantics are frozen. No mutation to their versioned contracts, published origin, lease purpose or earlier historical files. No production Nutrition/clinical content, providers, qualifications, publications, seeds, conversions, thresholds, or defaults. Keep **MTR-006/007/008 parent issues #5/#6/#7 OPEN**, 0017/108 tables, no 0018, 528 existing exports and compatibility pins, `planner_ready=False`, `activation_ready=False`, **Execution NOT STARTED**, **PRECOMMIT FAIL-CLOSED**, **PRODUCTION NUTRITION/CLINICAL CONTENT GATE CLOSED**.

**Final disposition: DETAILED DESIGN CANDIDATE / IMPLEMENTATION NOT AUTHORIZED / STRUCTURAL TEST_ONLY / PRODUCTION GATE CLOSED.**
