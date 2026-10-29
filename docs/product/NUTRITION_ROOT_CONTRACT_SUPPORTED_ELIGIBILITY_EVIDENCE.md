# Nutrition Root Contract & Supported-Eligibility — implementation evidence

NUTRITION ROOT CONTRACT & SUPPORTED-ELIGIBILITY FOUNDATION

IMPLEMENTATION READY FOR REVIEW / FREEZE CANDIDATE — NOT FROZEN

## 1. Approved design and verified entry gate

The [approved design](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_DESIGN.md) is immutable at
PR #122 reviewed head `e090bf788bd6a257d7bba0f3e88d6b5fec12bc44`, base
`d4167537a7347b686b1edc273b5ac9d4f5145d62`; architecture receipt
[6491096716](https://github.com/thedusk4203/Menuto/pull/122#issuecomment-6491096716).
Exact design-head [CI40818736250](https://github.com/thedusk4203/Menuto/actions/runs/40818736250) SUCCESS.
The OPEN/MERGEABLE PR had one commit, five Markdown files, no unresolved technical thread,
and auto-merge OFF immediately before exact-head-guarded merge.

Actual design merge and implementation entry main:
`cb66f462f3ea7e8cf6e63a3cbe2d75db0d19a682`.
Its tree `ffec4fcd51e38ec1b553dcad2411dd902bbfd741` exactly equals the approved design head.
Exact post-merge **push** [CI40839789573](https://github.com/thedusk4203/Menuto/actions/runs/40839789573)
**SUCCESS**; Python/web/every required guard SUCCESS; **3,638 passed /0 skips**;
SCRAM/TLS16/16;benchmark22/22;client10/10;403 exported definitions;schema0015 /85.
No design migration or implementation drift; PR #120 remains FROZEN.
Only after this gate did the separate structural implementation branch begin.

This receipt approves no production nutrition/clinical content, numerical references, supported
population definitions, qualification records or actual member eligibility assertions.
Implementation remains a separate OPEN review candidate. No self-freeze or implementation merge.

## 2. Durable physical schema

Alembic reported a single current head0015 at verified implementation entry. The actual legal
forward revision selected from that graph is **0016**, with `down_revision=0015`.
Old0001–0015 migration bytes remain unchanged. **85→98 domain tables (+13)**;
99 physical public tables including Alembic's revision table. One additional operational sequence
`nutrition_source_recorded_order` records causal cross-stream order; rolled-back sequence gaps
are valid and are not presented as contiguous global transaction history.

| New domain table | Exact durable responsibility |
| --- | --- |
| nutrition_source_providers | Immutable provider identity/remit/environment enrollment generations and explicit rebind lineage |
| nutrition_source_principals | Actual database/role OID+name, verified human or service identity, account binding and enrollment evidence |
| nutrition_source_streams | Typed SOURCE/AUTHORITY frontiers and separate operational LOCK rows; exact CAS heads |
| nutrition_source_receipts | Immutable command hash/actor/order/idempotency/audit envelope, exactly one typed child per receipt |
| nutrition_source_authority | Source-local capability grant/revoke history, scope, qualification, generation and effective interval |
| nutrition_guideline_drafts | Complete immutable guideline/version/revision/evidence/protocol/applicability body |
| nutrition_guideline_reviews | Exact-body content-review receipt or explicit cancellation |
| nutrition_guideline_publications | PUBLISH/SUPERSEDE/RETIRE/RETRACT, exact review and predecessor |
| nutrition_member_delegations | Exact subject/actor/operation grant/revoke with retained authorization evidence |
| nutrition_physiology_revisions | BODY_MASS/KG or HEIGHT/CM observation, provenance, effective time and correction lineage |
| nutrition_eligibility_revisions | Qualified exact protocol/member/observation assessment and complete missingness manifest |
| nutrition_goal_revisions | Member-owned ENERGY_DIRECTION intent and append-only lifecycle |
| nutrition_source_evidence_artifacts | Environment+evidence ID+version immutable full-body identity registry; grants no authority |

This is **NEW PERSISTENCE for source authority/history**, not a root cache or materialized profile.
The shared receipt/frontier envelope does not collapse distinct authorities into a generic event
body table: source bodies reside in their typed tables, with foreign keys, physical constraints,
protected command validation and deferred atomic coherence triggers. The evidence registry
prevents reuse of the same immutable ID/version for a different preimage.

Fresh migration/install was executed against real disposable PostgreSQL18. **Every new table has
0 rows**: provider0;principal0;grants0;reviewer/publisher/assessor enrollments0;guideline content0;
observations0;eligibility assertions0;goals0;delegations0;receipts/frontiers/evidence0.
**Production nutrition-content row count0; numeric policy/default rows0; seed rows0.**
Three infrastructure NOLOGIN roles and the protected functions are permissions, not enrolled people,
providers or reviewed content. Existing historical culinary policy/frontier records are unaffected.
Empty downgrade/re-upgrade succeeds; any populated new source table makes downgrade refuse data loss.

## 3. Authority and protected PostgreSQL interface

Independent NOLOGIN infrastructure roles: `menuto_nutrition_owner`, `menuto_nutrition_admin`,
`menuto_nutrition_client`. Deployment provisioning remains privileged. Runtime logins are separately
created with real SCRAM credentials and explicitly enrolled against actual database/role OID+name.
A human's verified identity is independent of login aliases; service identity cannot act as self.
Concurrent first enrollment of the same provider code/version is rejected by a physical unique
index, even when competing commands allocate different UUIDs. No Preferences/prior/hierarchy credential or household OWNER/EDITOR role supplies Nutrition rights.

| Protected entry point in menuto_nutrition | Execute permission |
| --- | --- |
| register_provider(jsonb) | Nutrition admin only; complete evidence/remit/environment, CAS enrollment generations |
| enroll_principal(jsonb) | Nutrition admin only; canonical actual role/database and verified identity evidence |
| change_authority(jsonb) | Nutrition admin only; exact scope/capability/protocol qualification grant/revoke |
| append(jsonb) | Nutrition client only; authenticated author+current capability+typed body+CAS |
| capture(jsonb) | Nutrition client only; exact current ROOT_SOURCE_READ or VALIDATOR_SOURCE_READ, subject and purpose |

All60 functions use a fixed trusted `search_path=pg_catalog,menuto_nutrition,pg_temp`.
Every function revokes PUBLIC execution; runtime/admin entry grants are explicit. Helpers have no
ordinary execute grant. Runtime actors own no tables and receive no direct DML. Owner-only insert/
frontier triggers, immutable UPDATE/DELETE/TRUNCATE guards and deferred coherence enforce atomic
one-receipt/one-typed-child/frontier state, even if an unsafe direct grant is attempted later.
Nutrition owner receives only the specifically required legacy member/profile SELECT access.

`system_user` reconstructs SCRAM-authenticated identity from the actual session. The path rejects
trust/missing/wrong credentials, SET ROLE as authorship, shared-login actor claims, superuser,
database/source owner, admin-as-runtime, unsafe role membership/ownership/direct-DML/unscoped-SELECT graphs, privileged global data/server-file/program roles and
writable-schema/temp-shadow escalation. Remote adapters require verify-full TLS; actual certificate
verification, password rotation and drop/recreated-role OID isolation are integration-tested.

Mutation order: provider lock, exact member/frontier lock, current principal/privilege graph and
capability/delegation/review checks, then idempotency lookup, then exact CAS and atomic append.
Operational LOCK row versions make stale RR/SERIALIZABLE writers fail on concurrent revoke instead
of using an old authorization snapshot. Exact retries need current permission; changed same-key
commands fail. No ordinary command can select an administration/enrollment dispatcher.

Capabilities remain exactly GUIDELINE_REVIEW, GUIDELINE_PUBLISH, GUIDELINE_WITHDRAW,
ELIGIBILITY_ATTEST, MEMBER_OBSERVATION_WRITE, MEMBER_GOAL_WRITE, ROOT_SOURCE_READ,
VALIDATOR_SOURCE_READ. Assessment qualification pins an already-reviewed published protocol.
Review and publish need different verified humans; two logins for one human fail. Semantic changes
in body/evidence/protocol/unit/applicability require fresh review. Revocation does not rewrite
past publication truth; explicit withdrawal does. All capabilities and delegations remain finite,
subject/provider scoped and effective-time bounded.

## 4. Source semantics, capture and replay

Physiological source revisions retain exact fact/unit/rational/provenance, observed/effective time,
author/delegation, lineage/frontier and full protected legacy profile anchor or absence witness.
A conflicting non-null legacy value rejects the observation until explicitly reconciled through
the existing profile path and newly attested. Legacy values are never backfilled as historical
verified observations. A relevant profile/observation change invalidates fresh dependent assessment;
old retained cuts still replay their own knowledge.

Goals support only ENERGY_DIRECTION: CUT/MAINTAIN/GAIN intent, no numeric target/rate/prescription.
Self comes from actual account↔member binding; representative needs exact-operation delegation,
not household role. Replace/correct/retract/future transitions preserve prior history. Absent goal
never becomes MAINTAIN; tombstones never resurrect earlier goals; no cross-member copying.

Eligibility is a qualified reviewed assertion, not inference from body measurements or absence
of diagnosis/restrictions. ADMITTED→SUPPORTED only with complete coherent required evidence;
OUT_OF_SCOPE→UNSUPPORTED; EXCLUDED→INELIGIBLE; UNDETERMINED/missing/stale/incoherent→UNKNOWN.
Proven negative evidence keeps its distinct meaning beside unrelated missing diagnostics.
No roots are returned for non-SUPPORTED state or incomplete source/goal/applicability.

One explicit provider/family/revision/body/protocol/scope/temporal pin; no latest/provider fallback.
RANGE/MINIMUM/MAXIMUM use exact reduced rationals; TARGET is only a reference center. Supported
finite metric/unit pairs provide structural measurement algebra, not scientific approval of values.
No float coercion, implicit conversion, daily↔weekly scaling, invented opposite bound or version
stitching. Same-source/metric/unit/applicability/period descriptors precede arithmetic.

Capture uses **one actual Nutrition reader connection**, caller-owned clean read-only RR or
SERIALIZABLE transaction with no assigned write transaction. No cross-owner multi-session cut is
claimed. Wrong session/isolation or unresolved authority fails entirely. It retains actual endpoint/
database/role/service identity, MVCC frame, capture interval, provider/grant generations, exact scoped
full histories/frontiers/tombstones and protected absence witnesses. No unrelated member history,
partial success, favorable-row selection or truncation. Reader permission is checked through the
capture interval; snapshot semantics remain explicit, without pretending offline current authority.

Producer replay has zero DB/network/filesystem/wall-clock/environment/global policy I/O. It
reconstructs every retained source, grant, review, lifecycle, dependency and effective interval.
Semantic validation recomputes the complete result rather than trusting cached/model-constructed
children. Fingerprints bind the full retained capture, including hidden/history/frame identity;
they prove tamper/self-consistency, **not canonical DB origin, present authorization/publication
or scientific correctness**.

## 5. Independent Validation companion

`validation.nutrition_roots` imports only immutable Nutrition contracts and primitive canonical/
measurement support. It never calls/imports producer root_resolution, producer semantic validation,
NutritionPolicyEngine, PlanPolicyResolver or planner objective code as a correctness oracle.
The producer uses interval-splitting replay; Validation independently reconstructs boundary-grid
state, publication/review/current-at-command authority, member authorship/delegation, observation/
legacy dependencies, eligibility, effective-time/frontier identity and complete root result.
Rehashed wrong producer results fail independently. Frozen025/026 contracts/bodies are unchanged.

ROOT_SOURCE_CONSISTENCY_ONLY proves this named source/root self-consistency only.
ROOT_AND_DERIVED_CONTAINMENT requires complete typed derived claim carriers for every protected
root and checks exact RANGE, MINIMUM/MAXIMUM and reference-center inequalities independently.
Missing required claims are UNSUPPORTED, not vacuous success. Goal protection requires exact goal
and retained baseline provenance; this slice supplies no production synthesis. Cost/budget,
KitchenEffort/convenience, TasteFit or NutritionPrecision cannot widen/mint a root. Descriptor
mismatch is rejected before Fraction/arithmetic. Neither scope certifies future policy business
correctness, medical truth, full-plan validation or activation.

## 6. Server-owned bounds

| Absolute bound | Value / behavior |
| --- | --- |
| Command JSON bytes | 131,072; preflight before model/canonical recursion and protected SQL validation |
| Complete capture bytes | 4,194,304; all-or-error |
| Journal/whole capture rows | 4,096; no truncated successful prefix |
| Source history/effective interval depth | 64; overflow rejects atomically |
| Structure nesting | 32; bounded iterative preflight |
| Rational integer | nonnegative numerator / positive denominator, each ≤2^127−1; canonical gcd1 |
| Evidence manifest | 32 entries; complete immutable bodies |
| Operation | adapter-owned15,000ms statement budget, SQL deadline and1s lock timeout |

These are server-owned structural limits, not caller-authored policy values. Direct SQL checks
also bound body/history/manifest/integer/lock/work paths. Overflow leaves no partial event/frontier/
receipt. Public production HTTP ingress limits remain the separate Planner API gate.

## 7. Module/API and SQL inventory

| Module | Responsibility |
| --- | --- |
| nutrition.root_contracts | Immutable finite source/measurement/root/validation transport;44 additive definitions |
| nutrition.root_limits | Server structural preflight and absolute limits |
| nutrition.root_models |13 normalized source tables plus causal order sequence |
| nutrition.root_admin | Separate privileged provider/principal/grant adapter |
| nutrition.root_sources | Concrete one-session authenticated append/capture adapter; caller transaction ownership |
| nutrition.root_resolution | Pure retained-source resolver plus full producer semantic recomputation |
| nutrition.root_public | Bounded append/capture/resolve/validate facade, no admin or HTTP endpoint |
| validation.nutrition_roots | Independent source/root/containment checker |
| migration0016 | Self-contained frozen DDL+SQL; no importing live runtime schemas or external SQL at migration time |

Protected SQL inventory: five callable entry points above, plus55 private helpers/triggers.

`backend_tls`, `utc`, `canonical`, `hash`, `uuid`, `bounds`, `deadline`, `safe_role`, `session_fact`, `interval_ok`, `covers`, `amount`, `evidence`, `strict_sets`, `authority_group`, `authority_key`, `source_key`, `subject`, `legacy_anchor`, `subject_witness`, `ensure_stream`, `lock_sources`, `principal`, `provider`, `permission`, `validate_json`, `command_schema`, `check_command`, `provider_fact`, `principal_fact`, `record_body`, `record_fact`, `receipt`, `check_evidence_tree`, `check_authority`, `retain_evidence`, `check_bundle`, `check_source_command`, `apply_timeline`, `timeline`, `covering_revision`, `apply_publication`, `publication_timeline`, `published_revision`, `check_review`, `check_publication`, `touch_sources`, `check_assessor_qualification`, `member_auth`, `check_observation`, `check_assessment`, `source_in_request`, `write_guard`, `immutable`, `coherent`.


## 8. Executed acceptance matrix — NRC01–NRC80

The machine-readable [acceptance map](../../apps/backend/tests/fixtures/nutrition_root_acceptance.json)
pins all80 cases to parameter-expanded test IDs. **144 additive executions**: PG66, pure replay31,
independent Validation25, architecture/compatibility22. **All32 mandatory real PG obligations** run
against actual protected PostgreSQL paths with real SCRAM actors, committed/concurrent mutation,
recapture, certificate checks and physical migration/restore; no mocked or collection-only PG proof.
The retained TEST_ONLY snapshot was produced through real capture; its offline reuse proves only
retained semantic consistency, not a currently trusted database or live credentials.

| Case | Layer | Executed tests | Obligation / executable proof |
| --- | --- | --- | --- |
| NRC01 | PG | 1 | Empty enrollment/source installation grants nobody publication or default content; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC02 | PG | 3 | Real SCRAM success; missing/wrong credential and trust authentication denied; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC03 | PG | 1 | Actual database/role identity binding; SET ROLE, forged actor/session data rejected; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC04 | PG | 6 | Unsafe/elevated/direct-DML privilege graphs rejected and rechecked after enrollment; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC05 | PG | 1 | Guideline provider/remit capability isolation; prior/hierarchy/household grants do not transfer; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC06 | PG | 1 | Actual guideline REVIEW with scientific evidence body/version pin; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC07 | PG | 1 | PUBLISH requires current publisher plus exact active content-review receipt; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC08 | PG | 1 | Same verified human using multiple logins cannot self-review/publish; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC09 | PG | 5 | Changed body/unit/applicability/evidence/protocol requires fresh review; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC10 | PG | 3 | Reviewer/publisher revocation and retry ordering before idempotency lookup; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC11 | PG | 6 | Direct SQL bypass cannot forge review, root type/unit/interval or mandatory keys; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC12 | PG | 1 | Concurrent guideline publication CAS; one successor, atomic history/frontier/receipt; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC13 | PG | 1 | Exact retry succeeds only while authorized; changed same-key command rejected; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC14 | PG | 1 | Scheduled supersession, retirement and retraction preserve exact historical publication; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC15 | PG | 1 | Member self actor derives from authenticated account-to-member binding; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC16 | PG | 1 | Representative requires exact goal-specific authorization; household role alone denied; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC17 | PG | 1 | Delegation issuance evidence, scope, expiry/revoke and concurrent retry behavior; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC18 | PG | 1 | Another member/household cannot copy or author a goal; service reader cannot become self; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC19 | PG | 1 | Goal replace/retract/correct lifecycle and future-effective transitions are append-only; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC20 | PG | 1 | Concurrent member goal CAS and cross-subject idempotency isolation; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC21 | PG | 1 | Physiology observation ownership, unit/provenance/time, legacy anchor agreement/absence and explicit re-attestation; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC22 | PG | 1 | Observation or legacy profile change/correction/retraction invalidates dependent assessment in fresh capture; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC23 | PG | 1 | Assessor needs exact reviewed scope/protocol qualification grant, separate from publisher; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC24 | PG | 4 | Assessment binds exact member/observations and complete required evidence; partial/forged inputs denied; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC25 | PG | 5 | Real sources yield distinct supported/out-of-scope/excluded/undetermined outcomes with their evidence; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC26 | PG | 1 | Reader and validator-reader scope isolation; unauthorized capture discloses no partial member/source data; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC27 | PG | 5 | Clean same-session read-only RR/SERIALIZABLE coherent capture; wrong DB/session/isolation denied; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC28 | PG | 1 | Concurrent correction/revoke/new publication cannot splice cuts; old retained cut still replays; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC29 | PG | 1 | Full journal/frontier and absence witnesses include hidden/tombstoned revisions; no cherry-picked omission; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC30 | PG | 1 | Remote TLS/server verification obligations and credential rotation/recreated-role isolation; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC31 | PG | 6 | Protected SQL/Python parity for finite types, exact rationals, applicability and lifecycle; no rounding; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC32 | PG | 1 | Append-only/no row drift on reads/replay; actual future migration/restore/downgrade loss-refusal and empty-production-content guarantees; [test_postgres_nutrition_root_source.py](../../apps/backend/tests/test_postgres_nutrition_root_source.py) |
| NRC33 | P | 1 | Guideline identity/version/body and provider/family pins exact; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC34 | P | 1 | Review label, reviewer UUID or hash without canonical authority evidence is insufficient; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC35 | P | 1 | Same typed immutable ID with different full body is rejected across the snapshot; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC36 | P | 1 | Guideline unavailable differs from not applicable; no latest/provider fallback; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC37 | P | 1 | Missing assessment/required observation produces UNKNOWN, not unsupported or safe; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC38 | P | 3 | Positive OUT_OF_SCOPE and EXCLUDED retain distinct UNSUPPORTED/INELIGIBLE meanings; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC39 | P | 1 | Mass/height, guessed age, absent diagnosis/restrictions never infer healthy adult/SUPPORTED; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC40 | P | 1 | Assessment scope/protocol, observation/version or required-coverage mismatch withholds roots; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC41 | P | 1 | Source edition/jurisdiction/applicability missing or contradictory is unresolved; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC42 | P | 1 | Unit/metric mismatch rejects before amount comparisons; no food-basis conversion; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC43 | P | 2 | Unsupported nutrient/root/goal/contract version rejected; finite operators only; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC44 | P | 5 | RANGE/MINIMUM/MAXIMUM union shape and exact canonical rational validation; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC45 | P | 1 | TARGET is reference center, never an inferred hard safety interval; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC46 | P | 1 | Guideline/assessment/goal/physiology expiry and exact effective intersection; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC47 | P | 1 | Daily/weekly/calendar/interval identity mismatch; no implicit temporal scaling; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC48 | P | 1 | Goal ABSENT versus RETRACTED versus invalid/ambiguous; no MAINTAIN default; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC49 | P | 1 | Current tombstone does not resurrect older goal; full reason/proof set retained; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC50 | P | 1 | Future transition and retrospective correction distinguish valid time from recorded frontier; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC51 | P | 1 | Deterministic order/canonicalization/fingerprints with exact rational normalization; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC52 | P | 1 | Full histories/frames/unused publication bodies affect source identity; visible bounds hash alone insufficient; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC53 | P | 1 | Field, nested body, model_construct/copy and forged-cache tampering detected by full recomputation; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC54 | P | 1 | Old retained input replays after current permission/content changes without claiming current authorization; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC55 | P | 1 | Read/access failure is not a successful empty source; absence requires frontier witness; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC56 | P | 1 | Server source resource overflow is all-or-error; no truncated favorable prefix; [test_nutrition_root_replay.py](../../apps/backend/tests/test_nutrition_root_replay.py) |
| NRC57 | V | 1 | Independent root identity/publication/applicability reconstruction without producer business code; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC58 | V | 1 | Independent eligibility, observation dependency and member goal authorship verification; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC59 | V | 1 | Independent effective-time/source-frontier integrity and immutable ID conflict detection; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC60 | V | 4 | Derived RANGE containment, including boundary equality, against exact hard roots; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC61 | V | 8 | MINIMUM/MAXIMUM one-sided protection and target-center containment; no invented opposite bound; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC62 | V | 1 | Goal direction alone cannot prove numeric protection or weaken hard roots; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC63 | V | 2 | CostPreference/budget cannot widen a protected root; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC64 | V | 2 | KitchenEffort/convenience cannot widen a protected root; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC65 | V | 1 | TasteFit input/score cannot create, weaken or replace root truth; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC66 | V | 1 | NutritionPrecision cannot mint safety truth; derived comfort remains contained where required; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC67 | V | 1 | Weekly/temporal claims require exact root/policy/period source binding and interval coverage; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC68 | V | 1 | Missing baseline/derived claims or descriptor mismatch fails required containment scope; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC69 | V | 1 | Rehashed wrong producer result caught independently; ROOT_SOURCE_ONLY does not claim policy validation; [test_nutrition_root_independent_validation.py](../../apps/backend/tests/test_nutrition_root_independent_validation.py) |
| NRC70 | A | 7 | Pure resolver/semantic validation has zero DB/network/filesystem/clock/global/environment I/O; [test_nutrition_root_architecture.py](../../apps/backend/tests/test_nutrition_root_architecture.py) |
| NRC71 | A | 5 | Independent Validation imports contracts/primitives only, not producer/engine/planner logic; [test_nutrition_root_architecture.py](../../apps/backend/tests/test_nutrition_root_architecture.py) |
| NRC72 | A | 1 | No actual production numeric constants, datasets, seeds or default provider/policy/eligibility; [test_nutrition_root_architecture.py](../../apps/backend/tests/test_nutrition_root_architecture.py) |
| NRC73 | A | 1 | No environment numeric authority, BMR/TDEE universal floor or clinical inference engine; [test_nutrition_root_architecture.py](../../apps/backend/tests/test_nutrition_root_architecture.py) |
| NRC74 | A | 1 | No Preferences/TasteFit/Learning dependency or source-capability reuse; [test_nutrition_root_architecture.py](../../apps/backend/tests/test_nutrition_root_architecture.py) |
| NRC75 | A | 1 | No planner/activation/PRECOMMIT authority, endpoint or MTR006/008 completion claim; [test_nutrition_root_architecture.py](../../apps/backend/tests/test_nutrition_root_architecture.py) |
| NRC76 | A | 1 | Frozen preference/prior/hierarchy/feature/TasteFit/041/046 contracts/semantics remain unchanged; [test_nutrition_root_architecture.py](../../apps/backend/tests/test_nutrition_root_architecture.py) |
| NRC77 | A | 1 | Frozen inventory/recipes/grounding/025/026 subject/hash semantics and old migration bytes retained; [test_nutrition_root_architecture.py](../../apps/backend/tests/test_nutrition_root_architecture.py) |
| NRC78 | A | 2 | All existing403 definition bodies and3,638 baseline test identities retained at future implementation entry; additive exports only; [test_nutrition_root_architecture.py](../../apps/backend/tests/test_nutrition_root_architecture.py) |
| NRC79 | A | 1 | Content/qualification approval is separate from structural schema/permission approval and TEST_ONLY fixtures; [test_nutrition_root_architecture.py](../../apps/backend/tests/test_nutrition_root_architecture.py) |
| NRC80 | A | 1 | All-survivor020A policy remains finite/complete/system-bounded; no020B, solver, Execution or activation work in this slice; [test_nutrition_root_architecture.py](../../apps/backend/tests/test_nutrition_root_architecture.py) |


## 9. Verification receipts and frozen compatibility

The complete local corpus executed **3,781 tests, 0 skips**:3,775 initially passed and six
legacy current-head metadata/append-only composition assertions failed. Those six were corrected
mechanically (new bundle/migration/table/export inventory and exact old composition prefix), then
**all six passed**. A subsequent103-test compatibility/architecture/SCRAM-TLS gate passed.
The final single-run combined regression gate is the **exact implementation-head Foundation CI**;
its run ID/result/full3,782 count must be pinned in the implementation PR verification receipt
before this candidate is presented as ready. A final real PG privilege-graph regression adds one
execution after that initial corpus:144 additive cases,3,782 combined. Global read/write, server-file,
server-program and maintenance roles, plus direct unscoped source SELECT, are rejected before an
old receipt or capture can be returned. No different-SHA or pre-final CI is substituted.

The acceptance run passed144/144 with66 real PG executions and zero skips. Frozen baseline
identity guard retains all3,638 test IDs. Existing test edits only synchronize current migration/
table/export totals; old test identities/assertions about frozen feature semantics remain.
Source definition pins retain **all403 old bodies/hashes** and add44: **447 total exports**.
The compatibility manifest also pins130 frozen runtime/domain/old-migration files. Old preference,
prior, hierarchy, feature projection, both TasteFit foundations,041A–F,046A, inventory, recipes,
validation025/026 and all0001–0015 migrations retain their bytes. Only the authorized persistence
composition appends new table registration after its byte-exact old prefix; an exact suffix/prefix
manifest prevents any other edit at this seam. Import guards add an exact immutable-contract exception
for the new Validation companion; no general module-boundary relaxation.

Ruff, architecture/import guards, OpenAPI/domain exports,22 synthetic fixtures,22/22 benchmark,
client10/10,typecheck and web build are required alongside full pytest and16/16 SCRAM/TLS smoke.
No workflow/CI coverage reduction or two-level gate implementation occurs here.

## 10. Production-content stop and downstream status

**PRODUCTION NUMERICAL/CLINICAL CONTENT GATE: CLOSED / NOT AUTHORIZED.**
All structural fixtures/evidence are unmistakably TEST_ONLY in disposable sources. TEST_ONLY
provider/principal/evidence environments cannot become production source state through selection.
No thresholds, percentages, BMR/TDEE safety authority, clinical cutoffs, goal rates, population/
exclusion protocols, qualification records or actual provider/member assertions ship in migration.
Before any such production content is enrolled/published, separately review its evidence, exact
source edition/applicability/protocol/value content and qualified-human authority. Hashes, labels,
structural permissions and these test results cannot replace that independent content gate.

AVAILABLE means complete applicable authoritative retained inputs resolved; policy_synthesis=
NOT_PERFORMED;numeric_goal_protection=NOT_SYNTHESIZED;planner_ready=False;activation_ready=False.
It is not full NutritionPolicy, a safe plan, general medical eligibility or independent full-plan
validation. MTR006 synthesis and MTR008 resolution remain incomplete and are not implemented here.
MTR040 COMPLETE/issue41 CLOSED;039 OPEN;full041/046 PARTIAL;024/020B/021 BLOCKED;
Execution NOT STARTED;PRECOMMIT FAIL-CLOSED;planner activation disabled.
No downstream work, issue closure, implementation merge or self-freeze is authorized by this receipt.

NUTRITION ROOT CONTRACT & SUPPORTED-ELIGIBILITY FOUNDATION

IMPLEMENTATION READY FOR REVIEW / FREEZE CANDIDATE
