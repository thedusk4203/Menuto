# MTR-006 Source-Bound NutritionPolicy Synthesis & Containment — implementation evidence

**IMPLEMENTATION READY FOR REVIEW / FREEZE CANDIDATE. NOT FROZEN.**

This is the bounded structural slice approved by PR #126. Full MTR-006/007/008
remain incomplete. Nutrition Root remains FROZEN. The **PRODUCTION
NUTRITION/CLINICAL CONTENT GATE remains CLOSED**. No production numerical rules,
guidelines, supported populations, qualifications, providers, publications,
enrollments, seeds or defaults are supplied. No parent issue is closed.

## Authorization and baseline

- Approved design head: `26ac499a23a13525157ee732931cd76d52b7fa4f`.
- Architecture approval: [6633481532](https://github.com/thedusk4203/Menuto/pull/126#issuecomment-6633481532).
- Design completion: [6635044106](https://github.com/thedusk4203/Menuto/pull/126#issuecomment-6635044106).
- Exact design merge / implementation base: `4a39e8fbbf4b91ef02f39d210eeff89970ab2bb9`.
- Exact baseline push CI: [41852571668 — SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/41852571668).
- Retained baseline: **3,782 tests; 447 exported definitions; 0016 / 98 domain tables**.

The next legal migration was determined from the actual repository chain, not reserved
by design. Migration **0017** is additive; migrations 0001–0016 remain byte-for-byte
unchanged. No existing frozen export definition is edited.

## Durable source inventory and empty installation

Schema becomes **0017 / 108 domain tables**, adding **10 tables** and one
`nutrition_synthesis_recorded_order` sequence. This intentionally adds durable source
authority/history. It is **not ZERO NEW PERSISTENCE**. No derived policy/profile cache,
planner state or member aggregate is persisted.

The disposable PostgreSQL fresh-install check upgraded the actual complete migration
chain, ran Alembic metadata-drift checking, downgraded the empty new source, and upgraded
again. The new tables below all contained zero rows. Separate loss-refusal tests prove
that populated source history cannot be silently downgraded.

| New durable table | Responsibility | Fresh-install rows |
| --- | --- | --- |
| `nutrition_synthesis_providers` | Append-only provider enrollment/replacement lineage | 0 |
| `nutrition_synthesis_principals` | Append-only actual credential/human/service enrollment revisions | 0 |
| `nutrition_synthesis_principal_frontiers` | Current enrollment head plus serialization token | 0 |
| `nutrition_synthesis_grants` | Exact enrollment-revision/family/remit capability grant/revoke journal | 0 |
| `nutrition_synthesis_streams` | Provider lock anchor and family CAS frontier | 0 |
| `nutrition_synthesis_receipts` | Immutable authenticated commands, ordinal order and idempotency receipts | 0 |
| `nutrition_synthesis_drafts` | Immutable complete typed rule revisions | 0 |
| `nutrition_synthesis_reviews` | Exact body/evidence review and cancellation receipts | 0 |
| `nutrition_synthesis_publications` | Append-only effective-time publication transitions | 0 |
| `nutrition_synthesis_evidence` | Immutable evidence preimages with conflicting-ID refusal | 0 |

The frontier tables are mutable serialization state; source facts, reviews, publications,
evidence and receipts are append-only. Principal replacement needs a frontier so a stale
RR writer cannot keep using an old credential enrollment. A new credential revision does
not inherit grants or old review authority. The canonical logical enrollment identity and
all old revisions remain retained. No generic event table replaces distinct authorities.

## PostgreSQL authority and lifecycle

Three separate infrastructure roles are installed, all NOLOGIN:
`menuto_nutrition_synthesis_owner`, `menuto_nutrition_synthesis_admin`, and
`menuto_nutrition_synthesis_client`. These are not qualified production actors.
No Nutrition Root, Preferences, prior or hierarchy capability is reused.

Finite capabilities are `SYNTHESIS_RULE_REVIEW`, `SYNTHESIS_RULE_PUBLISH`,
`SYNTHESIS_RULE_WITHDRAW`, `SYNTHESIS_SOURCE_READ`, and `SYNTHESIS_VALIDATOR_READ`.
Only the separately privileged registrar may enroll providers/principals or change grants.
Household membership and member goal authorship grant no publication authority.

The protected paths reconstruct actual database/login OID and name, SCRAM identity and
TLS status. They reject SET ROLE authorship, trust connections, unsafe inherited rights,
ordinary use of owner/db-owner/superuser credentials, writable protected schemas,
and direct source-table/sequence rights. Fixed search paths and qualified table/function
references defeat temp/schema shadowing. PUBLIC has no execute on protected helpers.
Clients have no source DML/SELECT/ownership.

Provider/frontier locks precede current authorization. Principal frontier locks are acquired
in a fixed global order. Exact reviewer qualification, enrolled human separation,
review cancellation, complete body/evidence/applicability and current grant identity are
checked **before an old idempotency receipt is returned**. Renewed/revoked qualification
requires fresh review; receipts cannot mint present authority. CAS and atomic typed
event/frontier/receipt commit prevent partial races. Different logins for one verified human
do not satisfy reviewer/publisher separation.

Database-issued recorded order is distinct from effective time and from the frozen root's
independent sequence. Grant/enrollment authorization is replayed by recorded order, never
by assuming a monotonic wall clock. PUBLISH/SUPERSEDE/RETIRE/RETRACT operate on exact named
publication intervals. Future changes preserve earlier coverage; retrospective correction
does not rewrite old retained cuts. Withdrawal never implicitly resurrects a predecessor.
Historical publication truth is not a claim of a publisher's present permission.

## Protected SQL inventory

There are **32 functions** in `menuto_nutrition_synthesis`: five execute-only entry points
(`register_provider`, `enroll_principal`, `change_authority`, `append`, `capture`) and
27 private helpers/triggers. All are frozen directly into migration 0017; historical
installation imports no mutable application models or live schemas.

`append`, `apply_publication`, `bounds`, `canonical`, `capture`, `change_authority`, `check_command`, `check_rule`, `check_tree`, `coherent`, `covers`, `deadline`, `enroll_principal`, `evidence`, `fact`, `hash`, `immutable`, `interval_ok`, `lock_provider`, `permission`, `principal`, `publication_timeline`, `record_fact`, `register_provider`, `retain_evidence`, `safe_role`, `session_fact`, `touch_principals`, `utc`, `uuid`, `validate_json`, `write_guard`.

## Module and interface inventory

| Module | Boundary |
| --- | --- |
| `nutrition/synthesis_contracts.py` | Immutable closed transport, typed finite instructions and scoped policy/validation/handoff carriers |
| `nutrition/synthesis_models.py` | Only additive source metadata |
| `nutrition/synthesis_admin.py` | Separate privileged registrar interface |
| `nutrition/synthesis_sources.py` | Authenticated append/capture adapter; one actual caller-owned connection |
| `nutrition/synthesis_journal.py` | Pure enrollment/grant/review/publication replay and exact selection |
| `nutrition/synthesis.py` | Acyclic requirements, exact synthesis, self-consistency and closed production admission |
| `nutrition/synthesis_public.py` | Bounded consumer facade; no registrar dispatch or planner authority |
| `validation/nutrition_policy.py` | Independent source and policy-semantic companion |

The root child is always reconstructed through the unchanged frozen public root interface.
Source capture calls frozen root capture and new rule capture on the same clean read-only
REPEATABLE READ/SERIALIZABLE session. Actual endpoint/database/login/backend/MVCC/isolation
frames agree. Enrollment and grant frontiers include complete histories and explicit absence.
No favorable prefix, source truncation, unrelated member history or multi-session MVCC fiction
is returned. Missing or failed capture returns no partial successful synthesis input.

Pure resolution/validation performs no DB/network/filesystem/wall-clock/environment lookup.
Every fingerprint binds retained semantic identity, not canonical DB origin, present
authorization, scientific correctness or production eligibility. Fully forged but internally
consistent offline material cannot establish any of those authorities.

## Finite numeric and layer semantics

Only the approved finite typed operations are interpreted: COPY_REFERENCE, AFFINE_SAME_UNIT,
MAKE_CONSTRAINT, CHECK_SUBSET, FINITE_PERIOD_SUM, REVIEWED_PERIOD_PROJECTION,
CHECK_DIRECTION and SELECT_PRECISION_CASE. IDs are unique, references backward-only and
operand types checked in both transport and SQL. Scalars/predicates cannot masquerade as
required constraint claims. There are no scripts, callbacks, metabolic models or inferred
coefficients. All arithmetic is reduced exact rational arithmetic with bounded integers.

The exact hard/reference root clauses survive unchanged. TARGET is a reference center,
never a hard interval. Missing opposite bounds and missing numeric inputs are not zero.
Each goal envelope needs its authored reference/direction check. All three comfort cases
are nested and contained, including unselected cases. Precision changes comfort only.
Cost, budget, effort, convenience and TasteFit cannot enter nutrition arithmetic.

Daily protection and weekly goal/centering have separate reviewed authority. Retained UTC
calendar cells are ordered, disjoint and gap-free. Finite sum coefficients are explicitly
positive. Joint reachable daily/aggregate interval consistency is checked without requiring
every daily combination to satisfy a weekly envelope, widening a bound, or claiming that a
catalog/meal plan is feasible. Cross-version stitching and coupled/rolling period systems
are unsupported. Original aggregate roots remain conjuncts.

Resolution insufficiency returns UNAVAILABLE with RESOLUTION_INSUFFICIENT, not a widened
comfort band, a physiological violation or solver infeasibility. Non-AVAILABLE results expose
no consumable policy claims/trace fallback. Retained hard roots remain source facts.

MTR-007 is only an acyclic typed requirements/resolution handoff. The sole interpreted
estimator fixture protocol is explicitly TEST_ONLY, retains primitive preimages plus
independent expected results, and is version-pinned. No production estimator/capture/verifier
or canonical candidate-pool scan is claimed. MTR-008 receives a full pinned policy/report/
precision reference only; no defaults/week precedence or ResolvedPlanPolicy is fabricated.

## Independent Validation

SYNTHESIS_SOURCE_AND_POLICY_SEMANTICS is an additive companion. It uses the unchanged
Validation-owned root checker and explicitly requires AVAILABLE/SUPPORTED/PRESENT admission.
It does not import/call the producer's source replay, selector, finite evaluator,
self-consistency validator, NutritionPolicyEngine, PlanPolicyResolver or solver.

The checker independently reconstructs enrollment/grant/review/publication state, uses a
boundary-grid publication replay rather than the producer's segment reducer, verifies each
finite relation, required purpose/coverage, root/direction/containment, precision/resolution,
calendar/aggregate constraints and the complete trace/result identity. A root containment
report alone cannot satisfy the companion. Existing MTR-025/026 contracts/coverage stay frozen.
Reports retain NOT_CERTIFIED / NOT_PROVED_OFFLINE / NOT_CLAIMED and false readiness flags.

## Resource limits and production stop

Server-owned bounds: 131,072 command bytes; 4,194,304 capture bytes; 4,096 serialized
source/frontier rows; 64 records per family/history stream; 512 retained principal facts;
127-bit integer magnitude; 32 evidence entries; 64 temporal cells/intervals; depth 32;
15,000 ms operation budget and 1-second protected lock timeout. The adapter also installs
the server-authored statement timeout. Direct SQL structure/history/deadline checks are
all-or-error; no truncation or favorable result is allowed. These controls do not replace
future server-owned public HTTP ingress limits. No public planner endpoint is introduced.

Production admission remains unconditionally closed, including for relabeled TEST_ONLY
material. Empty install has zero providers, enrolled reviewers/publishers/assessors,
qualifications, publications, production rules, numeric policy, seeds and defaults.
No real scientific/clinical content is provided by fixtures or migrations.

## Compatibility and test evidence

**480 exports = 447 retained byte-equivalent definitions + 33 additive definitions.**
The compatibility receipt retains all 447 body hashes, the older 130 runtime/migration pins,
24 additional frozen root/migration pins, and all 3,782 baseline test identities.
Only current-head migration/table/export receipts in older tests are mechanically advanced;
no test is removed, renamed, skipped or deprived of its frozen business assertions.
The persistence model registry receives an append-only import; its old byte prefix remains
pinned. Earlier TasteFit export slices still check their original exact sets after excluding
the explicitly inventoried later additive definitions.

New exported definitions (the exact delta):

`NutritionPolicy`, `NutritionPolicyClaim`, `NutritionPolicyReference`, `NutritionPolicyRequirementSpec`, `NutritionPolicyTrace`, `NutritionPolicyValidationInput`, `NutritionPolicyValidationReport`, `NutritionPrecisionSelection`, `NutritionResolutionFact`, `NutritionResolutionInput`, `NutritionResolutionRequirement`, `NutritionRuleApplicability`, `NutritionRuleCase`, `NutritionSynthesisAuthorityFrontier`, `NutritionSynthesisCaptureCommand`, `NutritionSynthesisCommand`, `NutritionSynthesisDraft`, `NutritionSynthesisGrant`, `NutritionSynthesisGrantFact`, `NutritionSynthesisOperation`, `NutritionSynthesisPrincipalEnrollment`, `NutritionSynthesisPrincipalFact`, `NutritionSynthesisPrincipalFrontier`, `NutritionSynthesisProviderEnrollment`, `NutritionSynthesisProviderFact`, `NutritionSynthesisPublication`, `NutritionSynthesisRecorded`, `NutritionSynthesisRequest`, `NutritionSynthesisReview`, `NutritionSynthesisRuleBody`, `NutritionSynthesisSelection`, `NutritionSynthesisSourceSnapshot`, `SynthesisRational`.

Executed acceptance map below is **NPS001–NPS120**. NPS001–032 are real PostgreSQL protected
path obligations, not mocks or collection-only checks. The one-time local retained-fixture
construction is not included in the acceptance/regression test count. Final verification
totals and exact-head CI are recorded in the implementation PR receipt after execution;
this evidence file does not substitute a previous-head or baseline CI run.

| Case | Layer | Executed pytest node | Required assertion |
| --- | --- | --- | --- |
| NPS001 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS001]` | Fresh migration installs empty rule authority/content; baseline 0016 objects unchanged |
| NPS002 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS002]` | Provider enrollment requires separate privileged registrar |
| NPS003 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS003]` | Ordinary command cannot become provider/principal/admin enrollment |
| NPS004 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS004]` | Actual database and login OID/name binding rejects spoof/recreated identity |
| NPS005 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS005]` | Trust/shared-login actor spoofing and SET ROLE cannot author |
| NPS006 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS006]` | Superuser, db-owner, source-owner and unsafe inherited privilege actors reject |
| NPS007 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS007]` | Direct SELECT/DML/ownership and PUBLIC execute paths cannot bypass protected scope |
| NPS008 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS008]` | Fixed search_path defeats writable schema/temp shadowing |
| NPS009 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS009]` | Frozen root grants do not authorize synthesis rule operations |
| NPS010 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS010]` | Preference/prior/hierarchy and household/member grants do not authorize rule publication |
| NPS011 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS011]` | Exact rule-local remit/capability/environment grants enforced |
| NPS012 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS012]` | Review cannot publish; publish cannot manufacture a review |
| NPS013 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS013]` | Different logins for the same verified human fail separation of duties |
| NPS014 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS014]` | Changed coefficient/body/evidence/calendar/requiredness needs fresh exact review |
| NPS015 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS015]` | Qualification/enrollment labels alone cannot bypass required retained review evidence |
| NPS016 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS016]` | Revoked authority is checked before old-command idempotency receipt lookup |
| NPS017 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS017]` | CAS races produce one committed event/frontier/receipt without partial writes |
| NPS018 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS018]` | Same key/body/actor retry is stable; changed command/actor/scope rejects |
| NPS019 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS019]` | PUBLISH/SUPERSEDE/RETIRE/RETRACT remain append-only; predecessor does not resurrect |
| NPS020 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS020]` | Future-effective replacement preserves current state; correction retains old cuts |
| NPS021 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS021]` | Overlapping applicable publication/case ambiguity cannot be hidden by a pin |
| NPS022 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS022]` | Two concurrent publishers/withdrawal serialize through authority/frontier locks |
| NPS023 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis.py::test_nps023_one_actual_execute_only_root_and_rule_reader` | One independently enrolled execute-only reader captures root and rules under frozen guards |
| NPS024 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS024]` | READ COMMITTED, writable/dirty transaction and mixed connection cuts reject |
| NPS025 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS025]` | Endpoint/role/backend/MVCC/frame mismatch rejects even when body hashes match |
| NPS026 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS026]` | Full history/frontier/absence capture; no favorable row selection or truncation |
| NPS027 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS027]` | Capture is exact-subject scoped; unrelated member data is not returned |
| NPS028 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS028]` | Server-owned bytes/rows/depth/integer/time limits fail all-or-error for direct SQL callers |
| NPS029 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS029]` | Concurrent revocation/publication cut yields coherent old or new state, never a splice |
| NPS030 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS030]` | Duplicate evidence identity with conflicting body rejects |
| NPS031 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS031]` | TEST_ONLY fixtures/enrollment do not survive as production install seeds/defaults |
| NPS032 | PG | `apps/backend/tests/test_postgres_nutrition_synthesis_authority.py::test_real_synthesis_authority_obligation[NPS032]` | Loss-refusal downgrade and transaction rollback preserve reviewed source history |
| NPS033 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS033]` | Unchanged AVAILABLE/SUPPORTED/PRESENT root admits structurally valid input |
| NPS034 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS034]` | Root UNAVAILABLE cannot become usable numeric policy |
| NPS035 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS035]` | UNKNOWN, UNSUPPORTED and INELIGIBLE remain distinct reasons |
| NPS036 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS036]` | Absent goal does not become MAINTAIN |
| NPS037 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS037]` | Retracted goal does not resurrect prior goal |
| NPS038 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS038]` | Ambiguous/foreign member goal fails exact-subject binding |
| NPS039 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS039]` | Cached/model-constructed root replays from primitive sources and tampering rejects |
| NPS040 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS040]` | Frozen root non-synthesis/non-activation literals remain unchanged |
| NPS041 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS041]` | Exact rule provider/revision/body/evidence and language pins required |
| NPS042 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS042]` | No rule/provider/version fallback or latest selector |
| NPS043 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS043]` | Missing and ambiguous rule cases fail distinctly |
| NPS044 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS044]` | Wrong guideline/protocol/scope/environment/subject rule applicability rejects |
| NPS045 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS045]` | Retired/retracted/out-of-effective-range rule blocks fresh applicability |
| NPS046 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS046]` | Historical replay preserves retained authority/publication knowledge |
| NPS047 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS047]` | Rule and source full-history fingerprints cover absence/frontiers/evidence |
| NPS048 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS048]` | Fingerprint/REVIEWED_PRODUCTION alone cannot mint publication or qualification |
| NPS049 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS049]` | Unknown language/operator/nonlinear/metabolic model is UNSUPPORTED |
| NPS050 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS050]` | Duplicate IDs, forward references, recursion and scripts reject |
| NPS051 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS051]` | Reduced exact rationals only; no float/bool/string coercion |
| NPS052 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS052]` | Zero is an explicit value; missing coefficient/offset is not identity/zero |
| NPS053 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS053]` | Oversized integers/denominator zero/negative final amount fail before unsafe work |
| NPS054 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS054]` | Descriptor/unit/basis/subject mismatch rejects before arithmetic |
| NPS055 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS055]` | Untouched complete hard-root manifest and clause identities survive synthesis |
| NPS056 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS056]` | RANGE both bounds, including equal-endpoint range, retain exact closed semantics |
| NPS057 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS057]` | MINIMUM has no invented upper; MAXIMUM has no invented lower |
| NPS058 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS058]` | TARGET stays reference; cannot become a hard safety interval |
| NPS059 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS059]` | Duplicate frozen metric/temporal/role or second guideline remains unsupported |
| NPS060 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS060]` | Protected RANGE stays within matching hard RANGE |
| NPS061 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS061]` | One-sided protection never weakens root endpoint |
| NPS062 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS062]` | Empty/conflicting constraints fail; no averaging/clipping/automatic intersection repair |
| NPS063 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS063]` | Missing authorized maintenance/reference role blocks goal synthesis |
| NPS064 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS064]` | CUT case requires exact reviewed comparator/reference evidence |
| NPS065 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS065]` | MAINTAIN case does not infer a center from absent content |
| NPS066 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS066]` | GAIN case cannot choose another direction's mapping |
| NPS067 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS067]` | Numeric direction relation inconsistent with published case fails |
| NPS068 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS068]` | Goal envelope outside hard protection fails without direction-preserving fallback |
| NPS069 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS069]` | No cross-member physiology/reference/goal aggregation or transfer |
| NPS070 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS070]` | Physiological observations do not implicitly select BMR/TDEE or safety formula |
| NPS071 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS071]` | Exact root temporal frame is retained; no claim root already has mixed DAY/WEEK clauses |
| NPS072 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS072]` | Wider-period daily derived protection needs separately reviewed transformation authority |
| NPS073 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS073]` | WEEK-only source with no required daily authority fails; no default floor |
| NPS074 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS074]` | DAY root cannot be repeated outside its exact covered interval |
| NPS075 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS075]` | Weekly centering never overrides daily hard protection |
| NPS076 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS076]` | No implicit day count, scaling, averaging or partial-week extension |
| NPS077 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS077]` | Period cells have exact ordered/disjoint/gap-free horizon coverage |
| NPS078 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS078]` | Calendar/timezone/version/DST mismatch or absent retained mapping rejects |
| NPS079 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS079]` | Cross-publication/root-cut/horizon stitching remains unsupported |
| NPS080 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS080]` | Contradictory daily/weekly interval sums conflict; no fake meal-plan feasibility |
| NPS081 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS081]` | Explicit precision case selected; missing explicit selection is unavailable |
| NPS082 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS082]` | PRECISION ⊆ STANDARD ⊆ RELAXED for comparable authored cases |
| NPS083 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS083]` | Every comfort set remains within hard and goal protection |
| NPS084 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS084]` | Coarse resolution returns insufficiency, never widen-until-feasible |
| NPS085 | Pure | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS085]` | Package size and DataConfidence cannot inflate bands or mint granularity |
| NPS086 | Handoff | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS086]` | Requirement-spec projection does not need final comfort output; no MTR-007 cycle |
| NPS087 | Handoff | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS087]` | Resolution pins complete pool/portion primitives, requirement identity and estimator version |
| NPS088 | Handoff | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS088]` | Cached/caller-authored resolution number without primitive authority rejects |
| NPS089 | Handoff | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS089]` | Missing required estimator coverage blocks; TEST_ONLY fixture not MTR-007 completion |
| NPS090 | Handoff | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS090]` | MTR-008 pins full policy/root/rule/report/precision identity; no consumer band edits |
| NPS091 | Handoff | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS091]` | Unapproved default/week precedence cannot fabricate STANDARD or a default receipt |
| NPS092 | Handoff | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS092]` | CostPreference cannot weaken or enter physiological/goal arithmetic |
| NPS093 | Handoff | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS093]` | BudgetContract/BudgetPressure cannot weaken or enter root synthesis |
| NPS094 | Handoff | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS094]` | KitchenEffort/convenience cannot weaken root/goal protection |
| NPS095 | Handoff | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS095]` | TasteFit/shared aggregation cannot supply utility-as-nutrition or physiology |
| NPS096 | Handoff | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS096]` | NutritionPrecision changes comfort only; new selection changes policy identity |
| NPS097 | Validation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS097]` | Independent root reconstruction required; CONSISTENT unavailable root cannot admit |
| NPS098 | Validation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS098]` | No import/call to producer selector/evaluator/validator, policy resolver or solver |
| NPS099 | Validation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS099]` | Rule authority/selection and complete mandatory manifest independently recomputed |
| NPS100 | Validation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS100]` | Omitted required goal/comfort/daily/weekly/resolution claim never passes vacuously |
| NPS101 | Validation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS101]` | Forged optional/not-applicable downgrade is rejected |
| NPS102 | Validation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS102]` | Rehashed mutated bounds/coefficients/reference/direction caught against retained publication |
| NPS103 | Validation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS103]` | Rehashed temporal cell, calendar, unit or subject mutation caught independently |
| NPS104 | Validation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS104]` | Full expected trace/policy identity checked, not just final numeric equality |
| NPS105 | Validation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS105]` | Root containment alone cannot stand in for complete policy-semantic coverage |
| NPS106 | Validation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS106]` | Offline all-forged self-consistency is not claimed as DB/scientific/current-authority proof |
| NPS107 | Isolation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS107]` | TEST_ONLY taint propagates to policy/ResolvedPlanPolicy/preview/report contracts |
| NPS108 | Isolation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS108]` | Mixed environment substitution rejects; production admission rejects TEST_ONLY |
| NPS109 | Isolation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS109]` | No environment lookup, global registry, DB/network/filesystem/wall-clock in replay |
| NPS110 | Compatibility | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS110]` | All 447 export bodies/hashes retained; new exports additive only |
| NPS111 | Compatibility | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS111]` | All frozen source/runtime/migration pins and 3,782 baseline test identities retained |
| NPS112 | Compatibility | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS112]` | NRC01–NRC80 and 66/32 real-PG evidence remain valid; no frozen root weakening |
| NPS113 | Compatibility | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS113]` | No changes to frozen 040/TasteFit/041A–F/046A/grounding/inventory semantics |
| NPS114 | Compatibility | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS114]` | Frozen MTR-025/026 and no-clinical-policy definition retain literals/hashes |
| NPS115 | Isolation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS115]` | No production clinical values, formulas, populations, protocols or qualification fixtures |
| NPS116 | Isolation | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS116]` | No enrolled production provider/default policy/seed or content gate auto-opening |
| NPS117 | Interface | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS117]` | Canonical ordering/replay produces deterministic fingerprints and scoped equality |
| NPS118 | Interface | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS118]` | Non-AVAILABLE result carries no consumable numeric fallback; diagnostics stay labeled |
| NPS119 | Interface | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS119]` | Resource overflow/time budget is all-or-error; no truncated favorable result |
| NPS120 | Governance | `apps/backend/tests/test_nutrition_synthesis_acceptance.py::test_source_bound_nutrition_acceptance[NPS120]` | No planner/API/activation/Execution/PRECOMMIT or parent completion authority |

## Verification receipt

The candidate retains **3,782 baseline tests** and adds **120 NPS cases**, for **3,902**
complete-suite cases. The local full invocation executed all 3,902 with **0 skips**:
3,901 passed and one old migration allowlist still omitted the new 0017 filename.
That inventory-only receipt was corrected; its complete Target Affinity test file and
all 22 Nutrition Root architecture cases then passed. No behavior or hash assertion was
weakened. Full SUCCESS on the exact implementation head is additionally mandatory in
GitHub Actions before delivery; that final run/result is recorded in the PR receipt.

All **NPS001–NPS120 passed in the full invocation**. It executed **1,285 real PostgreSQL
cases**, including **32 new protected-path executions / all 32 NPS obligations** and all
**66 retained Nutrition Root PostgreSQL executions**. The JUnit receipt maps each NPS ID
to a successful executed case, with no collection-only substitution.

The separate real SCRAM/TLS smoke completed **16/16**. Ruff, architecture and import guards,
OpenAPI/domain exports, all 22 synthetic fixtures and **22/22 benchmark scenarios** passed.
Client contract checks, typecheck, **10/10 client tests** and web production build passed.
Fresh installation verified **0017 / 108**, all ten new source tables and thirteen retained
Nutrition Root tables empty, metadata parity, empty downgrade/re-upgrade and zero production
providers, qualifications, publications, nutrition content, seeds or defaults. The populated
source downgrade-refusal obligation also executed successfully.

All **447 old export-definition hashes** and frozen runtime/migration pins passed; **33 new
exports** bring the total to **480**. The only old test edits are current-head inventory
receipts, not behavioral assertions or coverage removal.

Delivery additionally requires SUCCESS from GitHub Actions on the exact implementation
head. Its run ID, head SHA and job/guard results are recorded in the implementation PR
verification receipt after completion, without changing the tested head. No PR CI is
claimed as post-merge evidence. No freeze, architecture approval, merge or downstream
authorization is claimed by this file.

## Explicit non-authorizations

Nutrition Root stays FROZEN. Production nutrition/clinical content remains CLOSED.
MTR-006/007/008 remain incomplete; MTR-020B/021/024 remain BLOCKED. No MTR-039 work,
planner/optimizer/API activation, Execution or PRECOMMIT work is started.
`planner_ready=False`, `activation_ready=False`, Execution NOT STARTED and PRECOMMIT
FAIL-CLOSED remain unchanged. No parent issue closure or self-freeze is performed.
