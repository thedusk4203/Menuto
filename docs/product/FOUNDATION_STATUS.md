# Trạng thái foundation V1.3 và bằng chứng

## MTR-008 explicit-request plan-intent — DETAILED DESIGN / REVIEW PENDING

The owner authorized the [bounded detailed design](MTR_008_EXPLICIT_REQUEST_PLAN_INTENT_BOUNDED_DESIGN.md)
after [PR #140 completion](https://github.com/thedusk4203/Menuto/pull/140#issuecomment-6718064942).
Exact design base: `6df908d4295d2b96260eb633e936e35e49c2285d`; merged-main
[CI 42449622472](https://github.com/thedusk4203/Menuto/actions/runs/42449622472) SUCCESS, 4,369 tests / 0 skips.
The earlier dependency review is architecture/scope PASS and merged; its research-stage wording
below is historical. Scope is **pure-only fully explicit four-axis interpretation and independent
checking, STRUCTURAL / TEST_ONLY**. Authenticated capture, defaults/week/override precedence,
numerical policy composition and consumer admission are excluded. No implementation authorized.

Frozen PIV identity remains merge `45bb2677d3eb657dcf36aaf9fc5b9e146e8bf8fa` /
tree `19c97149aeaaf108894e7a3d01afd0db4558e9e9`; all earlier frozen semantics remain intact.
Current exports 528; 503 historical hashes / 53 historical frozen files (59 full PIV pins);
schema 0017/108, no 0018, no new persistence/privileges. Full MTR-006/007/008 INCOMPLETE;
issues #5/#6/#7 OPEN; production gate CLOSED; planner_ready=False; activation_ready=False;
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED. Design PR must remain OPEN / auto-merge OFF.

## Post-MTR-006 v2 dependency/readiness review — INDEPENDENT REVIEW PENDING

The [post-freeze capability and dependency review](POST_MTR_006_POLICY_INTEGRATION_V2_DEPENDENCY_REVIEW.md)
examines exact main 4b1decc67124eafddb1626dfc6e796a8a77de943. Recommended candidate:
**MTR-008 explicit-request orthogonal plan-intent resolution (STRUCTURAL / TEST_ONLY)**.
This is a research recommendation only. The independent architect selects the next scope and
finalizes its design; no new contract, precedence rule, design execution or implementation is authorized.

Frozen Root/MTR-006 v1/MTR-007/MBA/MTR-006 v2 identities and semantics remain unchanged.
Full MTR-006/007/008 INCOMPLETE; issues #5/#6/#7 OPEN; production Nutrition/clinical gate CLOSED.
528 exports, 503 historical hashes, 53 historical frozen files (59 complete v2 pins), schema0017/108,
no0018. planner_ready=False; activation_ready=False; Execution NOT STARTED; PRECOMMIT FAIL-CLOSED.

## MTR-006 Policy Integration v2 — STRUCTURALLY FROZEN / TEST_ONLY

[Approved design PR #136](https://github.com/thedusk4203/Menuto/pull/136), reviewed head
`570098480335dbf7c731fcf0954dd4601a2ccb9d`, and
[PIV-R136-01 corrigendum PR #137](https://github.com/thedusk4203/Menuto/pull/137), reviewed head
`dcab0f41a8605bb82c4d6b85ce01d176dcbc1bee`, established the corrected bounded detailed design retained at
baseline `5b9441d1c10e5ad010a10f9e1af415c1ef50bd5a`.
The separately authorized bounded implementation adds a structural, source-bound, independently
verified NutritionPolicy v2 integration seam over frozen Root/rule, NRE and MBA primitives, with
authenticated Policy-owned REQUEST_EXPLICIT precision.

**MTR-006 POLICY INTEGRATION V2 — STRUCTURALLY FROZEN / TEST_ONLY.**
The [canonical freeze receipt](MTR_006_POLICY_INTEGRATION_V2_FREEZE_RECEIPT.md) and
[formal freeze 6710492789](https://github.com/thedusk4203/Menuto/pull/138#issuecomment-6710492789)
pin implementation [PR #138](https://github.com/thedusk4203/Menuto/pull/138), reviewed head
`1e9000cf5122964393cd1cb1343719d378a7f936`, to actual merge
`45bb2677d3eb657dcf36aaf9fc5b9e146e8bf8fa` and frozen tree
`19c97149aeaaf108894e7a3d01afd0db4558e9e9`, identical to reviewed-head tree.
Exact post-merge **push** [CI 42389669892 — SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/42389669892):
Python/web and all guards SUCCESS; **4,369 passed / 0 skips = 4,183 retained + 186 additive**.
All **32 PIV-D families (PIV-D01–PIV-D32)** and **10 PIV-PG obligations (PIV-PG01–PIV-PG10)**
execute, including **45 real PostgreSQL executions**; dedicated SCRAM/TLS 16/16, benchmark 22/22,
client 10/10. PIV-R138-01 was closed at the reviewed head by
[independent PASS 6709092185](https://github.com/thedusk4203/Menuto/pull/138#issuecomment-6709092185).
Terminal carriers remain **UNVERIFIED_TRANSPORT**; no scientific or production acceptance.

The [implementation evidence](MTR_006_POLICY_INTEGRATION_V2_IMPLEMENTATION_EVIDENCE.md) and
approved designs remain unchanged historical records. Their candidate/NOT FROZEN wording describes
historical review stages and is superseded only as to current status. Documentation-sync commits
do not replace the frozen implementation merge/tree.

Exports: **528 = 515 unchanged legacy definitions + exactly 13 additive v2 names**. All 503 historical
definition hashes and 53 historical frozen files remain intact (59 total in v2 compatibility manifest,
including 6 MBA companions). Schema remains **0017 / 108**, no 0018, zero new persistence,
SQL objects, roles or runtime privileges. Fresh-install production Nutrition/clinical content,
providers, qualifications, publications, seeds and defaults remain **0**.
Nutrition Root, MTR-006 v1 synthesis, MTR-007 estimator, MBA applicability and MTR-006 v2 policy integration
foundations remain **FROZEN**. Full MTR-006/007/008 remain **INCOMPLETE**, issues #5/#6/#7 OPEN.
The **PRODUCTION NUTRITION/CLINICAL CONTENT GATE remains CLOSED**; planner_ready=False,
activation_ready=False; Execution NOT STARTED; PRECOMMIT FAIL-CLOSED.
MTR-008 remains a separate unauthorized downstream gate. No scientific conversion or downstream work is introduced.

## Measurement-basis applicability — STRUCTURALLY FROZEN / TEST_ONLY

[Approved design PR #132](https://github.com/thedusk4203/Menuto/pull/132), reviewed head
`803f83791bd7f41acda614268098f35b72eaa729`, merged at
`83025f158306e8cebc6357ac6d13fc3caac57809`; exact main push
[42174230677 — SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/42174230677).
[Architecture PASS](https://github.com/thedusk4203/Menuto/pull/132#issuecomment-6678583194)
and [design completion](https://github.com/thedusk4203/Menuto/pull/132#issuecomment-6679271731)
remain the governing reviewed design records.

The separately authorized bounded implementation adds a **STRUCTURAL / TEST_ONLY**
companion, private harness-issued immutable fixture registry, complete pre-policy anchor
projection, one-session Planning capture, pure Nutrition producer and independently
reconstructing Validation checker. Only original source-authored same-meaning planned-input
fixtures may be positive. There is no conversion, physiological inference or production authority.

**SOURCE-BOUND MEASUREMENT-BASIS APPLICABILITY & INDEPENDENT EVIDENCE CONTAINMENT —
STRUCTURALLY FROZEN / TEST_ONLY.**
The [canonical freeze receipt](MEASUREMENT_BASIS_APPLICABILITY_INDEPENDENT_EVIDENCE_CONTAINMENT_FREEZE_RECEIPT.md)
and [formal freeze 6688245300](https://github.com/thedusk4203/Menuto/pull/133#issuecomment-6688245300)
pin [implementation PR #133](https://github.com/thedusk4203/Menuto/pull/133), reviewed head
`a22d3c37697f7ac7d73ed29acbaa1d0b26c50b49`, to actual merge
`9d3b580ce2a2d111223b37814612a4072dbfe6a2` and frozen tree
`3a68035f9c33de152b3899a083d534a537c647e1`, identical to reviewed-head tree.
Exact post-merge **push** [CI 42230659936 — SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/42230659936):
Python/web and all guards SUCCESS; **4,183 passed /0 skips =4,047 retained +136 additive**.
MBA001–MBA080; **110 pure +26 real PostgreSQL executions /12 mandatory PG obligations**;
SCRAM/TLS16/16; benchmark22/22; client10/10. MBA-R133-01 is closed at the corrected head
by [independent PASS 6685642216](https://github.com/thedusk4203/Menuto/pull/133#issuecomment-6685642216).
Terminal carriers remain **UNVERIFIED_TRANSPORT**; no scientific or production acceptance.

The [implementation evidence](MEASUREMENT_BASIS_APPLICABILITY_INDEPENDENT_EVIDENCE_CONTAINMENT_EVIDENCE.md)
and approved design remain unchanged historical records. Their candidate/NOT FROZEN wording
is superseded only as to current status, not rewritten. Documentation-sync commits do not
replace the frozen implementation merge/tree. This freeze grants no downstream authorization.

All 4,047 baseline tests and 503 frozen exported-definition hashes are retained. The bundle
adds 12 definitions (515 total); all53 frozen source/migration files remain unchanged.
Schema remains **0017 / 108**, no0018, zero new persistence,
SQL objects, roles or grants. No production provider, qualification, publication, seed or default.
Nutrition Root, MTR-006 synthesis, MTR-007 estimator and MBA applicability foundations remain **FROZEN**.
Full MTR-006/007/008 remain **INCOMPLETE**, issues #5/#6/#7 OPEN. The **PRODUCTION
NUTRITION/CLINICAL CONTENT GATE remains CLOSED**; planner_ready=False,
activation_ready=False; Execution NOT STARTED; PRECOMMIT FAIL-CLOSED.
MTR-006 policy-integration v2 is structurally frozen; MTR-008 remains a separate unauthorized downstream gate.
No scientific conversion, new clinical measurement source or downstream work is introduced.

## MTR-040 — COMPLETE; issue #41 — CLOSED / COMPLETED

The separately approved closure gate has passed. [PR #108](https://github.com/thedusk4203/Menuto/pull/108)
merged reviewed head `d30f9f610af937f2e59fb4eea5962478037ff414` at
`959e7fa3488e0c379ab37044c25da74292c2d76b`; its tree exactly equals that head.
Exact post-merge push [CI 40486320021](https://github.com/thedusk4203/Menuto/actions/runs/40486320021)
SUCCESS, python/web SUCCESS; 2,978 tests; 358 exported definitions; schema **0015 / 85 domain tables**.
[Issue #41](https://github.com/thedusk4203/Menuto/issues/41) is CLOSED with state_reason=completed.
The [accepted parent review and closure receipt](POST_MTR_040C_PARENT_MTR_040_COMPLETION_REVIEW.md#12-approved-closure-receipt)
record canonical acceptance satisfied and the exact scope of completion.

Frozen 040A/B/C, reviewed prior source, PR #100 and hierarchy SOURCE semantics remain unchanged.
040C remains frozen at `69241affc2d85ee534ca682a0ff9a4d23a7c7862` (PR #107);
no new aggregate, persistence, migration 0016, source policy or production rows/defaults are added.
Member-owned typed sources and pure derived views satisfy this acceptance. MTR-039 remains a
separate requirement for broader attributed learning; no such event consumer is claimed complete.

Full 041/046 remain PARTIAL; 039 OPEN; 024/020B/021 BLOCKED; Execution NOT STARTED;
PRECOMMIT FAIL-CLOSED; planner_ready=False, activation_ready=False. The separately authorized
bounded candidate projection below grants no other downstream implementation.
Earlier delivery/review-stage statements are historical;
this closure receipt supersedes current-status wording only, never frozen behavior.

## Candidate-bound reviewed feature projection — FROZEN

[Design PR #111](https://github.com/thedusk4203/Menuto/pull/111) is APPROVED at
`04dbbb012041be80fc86914b582777812ed32e59` and merged at
`3efcd8c9594cbc0ae154d5bcac4e6315bf09d8f8`; exact post-merge push
[CI 40507097863](https://github.com/thedusk4203/Menuto/actions/runs/40507097863) SUCCESS, python/web green.
The separately reviewed [implementation PR #112](https://github.com/thedusk4203/Menuto/pull/112)
is **FROZEN** at `8fffd634cd6a9be809defa7e41c911c6dd1c254c`, exactly the reviewed head's tree.
Exact post-merge push [CI 40517159039](https://github.com/thedusk4203/Menuto/actions/runs/40517159039)
SUCCESS; python/web SUCCESS; **3,104 passed, 0 skips**; CFP01–CFP60 covered.
The [canonical freeze receipt](CANDIDATE_BOUND_REVIEWED_CULINARY_FEATURE_PROJECTION_FREEZE_RECEIPT.md)
binds design, implementation, review and verification identities; exports **362 = 358 + 4**,
schema **0015 / 85**, zero new persistence; planner_ready=False, activation_ready=False.
This bounded freeze does not complete full MTR-046. No new MTR suffix assigned. MTR-040 remains COMPLETE /
issue #41 CLOSED — COMPLETED; 039 OPEN; full 041/046 PARTIAL; 020B/021/024 BLOCKED;
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED. That projection freeze authorizes no other downstream implementation.

## Candidate × Member TasteFit — FROZEN

The [approved design](CANDIDATE_MEMBER_TASTEFIT_FOUNDATION_DESIGN.md), PR #115 head
`676ff2aca51cf4c4870c15d830a2f8e9048d9f42`, remains unchanged. The separately reviewed
[implementation PR #116](https://github.com/thedusk4203/Menuto/pull/116) is **FROZEN**:
reviewed head `152dbe8a365790956d2f7bac1b40a09b7dbd9134`, actual merge / verified main
`7ac0547b3df621fb19c614c27edaca268a901169`; the merged tree exactly equals the reviewed head.
Exact post-merge push [CI40659094576](https://github.com/thedusk4203/Menuto/actions/runs/40659094576)
**SUCCESS**, python/web SUCCESS; **3,396 passed, 0 skips** = 3,104 retained +292 additive.
**TF01–TF132 covered**; **42 real PostgreSQL cases cover all35 required PG obligations**.
SCRAM/TLS16/16; benchmark22/22; client10/10; guards/contracts/typecheck/build green.
Exports **384 =362 retained unchanged +22 additive**; schema **0015 /85**, no0016;
**ZERO NEW PERSISTENCE**, no production seed/default coefficients or policy publication/selection authority.
The [canonical freeze receipt](CANDIDATE_MEMBER_TASTEFIT_FOUNDATION_FREEZE_RECEIPT.md)
binds the review, exact merge and push-CI identities; the
[implementation evidence](CANDIDATE_MEMBER_TASTEFIT_FOUNDATION_EVIDENCE.md) retains all acceptance mappings.
One canonical candidate × one participating member; structured exact-target fit under a required,
explicit versioned/body-pinned conditional interpretation policy. No aggregate, comparison/ranking,
shared-member reducer or global/current/default/production policy publication/selection authority.
Frozen 040A/B/C, prior/shrinkage, hierarchy SOURCE,041A–F,046A and candidate projection remain unchanged.
planner_ready=False; activation_ready=False. No MTR suffix assigned; MTR-040 COMPLETE /issue41 CLOSED — COMPLETED;
039 OPEN;full041/046 PARTIAL;024/020B/021 BLOCKED;Execution NOT STARTED;PRECOMMIT FAIL-CLOSED.
This freeze itself grants no downstream implementation authority. The separately authorized design gate follows.

## Shared-member exact-target TasteFit — FROZEN; Planner Convergence review

The [canonical freeze receipt](CANDIDATE_SHARED_MEMBER_EXACT_TARGET_TASTEFIT_AGGREGATION_FREEZE_RECEIPT.md)
records reviewed implementation head `ea77d0476ce95db1c349c652312de9883ec00824`,
actual PR #120 merge/main `dc7a964c4acecb0ee8995f1705f176b164e50221` (same reviewed tree),
and exact post-merge push [CI40800756796](https://github.com/thedusk4203/Menuto/actions/runs/40800756796)
**SUCCESS**, Python/web and all required guards SUCCESS; **3,638 passed /0 skips**
=3,396 retained +242 additive; SMTF01–SMTF120;44 actual PG executions /36 required obligations.
SCRAM/TLS16/16;benchmark22/22;client10/10. **403 exports =384 unchanged +19 additive**;
**schema0015 /85;no0016;ZERO NEW PERSISTENCE**. Formal freeze comment
[6485815770](https://github.com/thedusk4203/Menuto/pull/120#issuecomment-6485815770).

One canonical candidate × one exact typed target × entire canonical participant set.
Compatibility and complete numeric coverage precede EXACT_POSITIVE_WEIGHTED_MEAN with authored
positive exact rational weights; incomplete coverage withholds every new arithmetic field.
Direct dislike stays independently observable, without hard veto. Policy authority remains
EXPLICIT_INTERPRETATION_INPUT_ONLY; no production/default policy authority or rows.
Frozen child TasteFit/040/041/046 semantics remain unchanged; planner_ready=False;activation_ready=False.

This ends the current preference-abstraction branch. The
[Planner Convergence dependency review](POST_PR_120_PLANNER_CONVERGENCE_REVIEW.md) is APPROVED
at head `fb81de8942cc681f8efa4ab358d8528749c3465b`, formal review6487151566;
PR #121 merged at `d4167537a7347b686b1edc273b5ac9d4f5145d62` (same reviewed tree).
Exact post-merge push [CI40812998898](https://github.com/thedusk4203/Menuto/actions/runs/40812998898)
SUCCESS, Python/web/all guards green;3,638 passed /0 skips;403 exports;0015 /85;no0016.
The [Nutrition Root Contract & Supported-Eligibility design](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_DESIGN.md)
is **APPROVED** at `e090bf788bd6a257d7bba0f3e88d6b5fec12bc44`, review6491096716.
PR #122 merged at `cb66f462f3ea7e8cf6e63a3cbe2d75db0d19a682`, exactly the reviewed tree;
exact post-merge push [CI40839789573](https://github.com/thedusk4203/Menuto/actions/runs/40839789573)
SUCCESS, Python/web/all guards green;3,638 passed /0 skips;403 exports;0015 /85.
**NUTRITION ROOT CONTRACT & SUPPORTED-ELIGIBILITY FOUNDATION — FROZEN**;
[canonical repository freeze receipt](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_FREEZE_RECEIPT.md)
and [implementation evidence](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_EVIDENCE.md).
PR #123 reviewed head `7953e74c64ce0d2db06d802a9213c0b0ad27dd1d`, review6500572389;
actual merge/main `6a77575fcb0ecf7a02493dae935fab88e94d09f1`, identical reviewed tree.
Exact post-merge push [CI40931231875](https://github.com/thedusk4203/Menuto/actions/runs/40931231875)
SUCCESS, Python/web/all guards green; canonical [freeze6506156639](https://github.com/thedusk4203/Menuto/pull/123#issuecomment-6506156639).
3,782 passed /0 skips =3,638 retained +144 additive; NRC01–NRC80;
66 actual PostgreSQL executions /32 obligations;SCRAM/TLS16/16;benchmark22/22;client10/10.
Schema0016 /98 domain tables;13 source/authority tables +1 sequence;
60 protected SQL functions =5 entry points +55 helpers/triggers.
447 exported definitions =403 retained unchanged +44 additive; earlier frozen semantics unchanged.
Fresh-install production nutrition/provider/enrollment/seed/default counts remain0.
**STRUCTURAL FREEZE ONLY — PRODUCTION NUTRITION/CLINICAL CONTENT NOT AUTHORIZED**.
**PRODUCTION NUTRITION/CLINICAL CONTENT GATE — CLOSED**: no real calorie/nutrient values,
clinical thresholds, BMR/TDEE policy, supported populations, exclusion/eligibility protocols,
provider authority, reviewer/assessor qualifications, guideline editions, member clinical eligibility,
production defaults or seeds approved. Isolated TEST_ONLY fixtures are not content approval.
Provider/publication authority stays independent; physiology/goals remain member-owned;
eligibility requires exact qualified attestation. Root availability is complete applicable source input,
not safety certification, policy synthesis or independent full-plan validation.
`policy_synthesis=NOT_PERFORMED`;`planner_ready=False`;`activation_ready=False`;
full MTR-006 and MTR-008 remain incomplete. The bounded020A all-survivor preview option is unchanged.
No new dependency gate, next-gate selection, design, implementation or downstream authorization.
MTR040 COMPLETE /issue41 CLOSED—COMPLETED;039 OPEN;full041/046 PARTIAL;
024/020B/021 remain BLOCKED;Execution NOT STARTED;PRECOMMIT FAIL-CLOSED.
Historical implementation-stage NOT FROZEN/open-PR wording is superseded only as to status.

The [post-Nutrition-root dependency review](POST_NUTRITION_ROOT_PLANNER_CONVERGENCE_REVIEW.md)
was approved in [review 6630817744](https://github.com/thedusk4203/Menuto/pull/125#issuecomment-6630817744).
PR #125 merged at `4a7ddac883a777270cfd1d2460f9b953332b6673`; exact post-merge push
[CI 41831629205](https://github.com/thedusk4203/Menuto/actions/runs/41831629205) SUCCESS;
[completion 6631661206](https://github.com/thedusk4203/Menuto/pull/125#issuecomment-6631661206).
The [bounded MTR-006 detailed design](MTR_006_SOURCE_BOUND_NUTRITION_POLICY_SYNTHESIS_CONTAINMENT_DESIGN.md)
was approved in [review 6633481532](https://github.com/thedusk4203/Menuto/pull/126#issuecomment-6633481532).
PR #126 merged at `4a39e8fbbf4b91ef02f39d210eeff89970ab2bb9`; exact push
[CI 41852571668](https://github.com/thedusk4203/Menuto/actions/runs/41852571668) SUCCESS;
[completion 6635044106](https://github.com/thedusk4203/Menuto/pull/126#issuecomment-6635044106).
The separately authorized [structural implementation candidate](MTR_006_SOURCE_BOUND_NUTRITION_POLICY_SYNTHESIS_CONTAINMENT_EVIDENCE.md)
adds dedicated rule-source authority, deterministic synthesis and independent policy semantics.
**IMPLEMENTATION READY FOR REVIEW / FREEZE CANDIDATE — NOT FROZEN.**
Its candidate tree has 3,902 tests (3,782 retained + 120 additive), all 120 NPS cases
and 32/32 new real PostgreSQL obligations passed locally, 0017 / 108 domain tables and
480 exports (447 retained + 33 additive). Full exact-head Actions evidence belongs to
its implementation PR and is mandatory before delivery.
The ten durable source tables install empty; no policy/profile cache or production content is added.
Nutrition Root remains structurally FROZEN; production nutrition/evidence/qualification content
gate remains CLOSED. MTR-006/007/008 remain incomplete; no parent issue is closed.
Canonical implementation base remains 3,782 tests / 0 skips, 447 exports, 0016 / 98 tables;
the new candidate is not a merge or freeze receipt.
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED; planner_ready=False; activation_ready=False.





## Historical PR #100 freeze receipt

**Exact-target Prior Compatibility & Shrinkage Foundation FROZEN / APPROVED** tại
`5728411ac12555f583f8df72ac71861998978aa4`; [freeze receipt](EXACT_TARGET_PRIOR_SHRINKAGE_FREEZE_RECEIPT.md).
Push CI40351934792 SUCCESS trên đúng SHA; python/web xanh;2597 tests;318 exports;0014 /78 bảng;
không0015, persistence hoặc production/default policy values.040B cũ vẫn giữ prior/shrinkage UNAVAILABLE;
PR #100 là consumer cộng thêm, planner_ready=False, activation_ready=False.


## Đã có

- Canonical V1.3 spec, 30 invariants, 11 accepted ADR; bảng chuyển mã cũ/mới.
- 16 namespace theo §16.4; validation và learning hiện chỉ có namespace/ranh giới.
- Health API, web shell, OpenAPI và generated TypeScript client + runtime validation.
- 22 synthetic-v2 fixtures, CP-SAT micro-model, exhaustive reference, independent arithmetic/evidence verifier và fault-injection tests.
- Static dependency checks cho contract/public surfaces, validator independence; baseline consistency checks.
- Toolchain lock, CI và main protection. CI configuration không mặc định chứng minh mọi commit đều xanh.
- Backlog canonical MTR-001..050; mã MTR không đồng nghĩa số issue GitHub. Xem BACKLOG.md.

## Bằng chứng theo invariant

[INVARIANT_COVERAGE.md](INVARIANT_COVERAGE.md) ghi đủ INV-001..030, phân biệt micro-model evidence với production tests còn thiếu. Baseline checker chỉ xác minh cấu trúc/link/numbering, không chứng minh thực thi cả 30 quy tắc.

## Chưa hoàn thành

MTR-001 có glossary/mapping nhưng chưa đủ business tests. MTR-002 có harness/regressions nhưng chưa có production mutation corpus, V4 adapter/large-pool reference hoặc numeric launch gates. MTR-003..050 chưa được coi hoàn tất qua việc tạo tài liệu/namespace/issue.

Đợt Foundation đầu có units/basis/provenance, household/catalog/member source contracts và migration đến `0002` cho 8 bảng; xem [Implementation Blueprint M0/M1](IMPLEMENTATION_BLUEPRINT_M0_M1.md). PostgreSQL tests kiểm migration trên schema rỗng và dữ liệu legacy, rollback khi mâu thuẫn, ownership, finite numeric constraints, append-only catalog facts và stale profile writes. [Sáu sửa đổi foundation](FOUNDATION_CORRECTIONS.md) tách calculation/storage, chuẩn hóa account/member và provenance, mở draft assets raw/prepared. Planner/validation/mutation handoffs vẫn là draft, chưa đủ input để validate plan.

Chưa có auth production, NutritionPolicyEngine, PlanPolicyResolver, retail live, production Independent Validator, learning router hoặc consumer closed loop. Retail/inventory/plan foundation được cập nhật riêng bên dưới; operational plan activation vẫn fail-closed. Entry checklist chưa hoàn thành toàn bộ; không gọi phần nền tảng đầu tiên là đạt cả Milestone 0/1.

## M1.1 Retail / Procurement Foundation

Tại freeze M1.1, schema tới **0004**, tổng **23 bảng domain**. Mapping Product→Ingredient sở hữu edible yield; mỗi ProductVersion có một canonical ingredient và nhiều phiên bản mapping cho ingredient đó. Retailer giữ identity ổn định, status chuyển sang history append-only. Fixed/catch/loose vẫn tách riêng. Quote reference_price_pair chưa phải purchase cost; CALIBRATED_REFERENCE chỉ derive từ reference + calibration, availability UNKNOWN. Promotion và source coverage được derive từ evidence; toàn bộ planning handoffs vẫn DRAFT. M1.1 không có cooking yield, InventoryLot persistence hoặc workflow mới; cooking yield bổ sung riêng ở M1.2 bên dưới.

[Evidence corrections 0004](M1_1_RETAIL_CORRECTIONS_EVIDENCE.md) là nguồn nghiệm thu hiện hành. [Evidence 0003](M1_1_RETAIL_PROCUREMENT_EVIDENCE.md) giữ kết quả lịch sử 368 tests/CI của PR #55 đã merge; chính các tests đó từng encode calibration sai nên không đủ làm freeze gate. M1.1 corrected semantics đã được user review và **APPROVED TO FREEZE** trước M1.2.

Correction đã đạt **398 local tests (157 PostgreSQL thật)** và **GitHub CI PASS** riêng: [run #17](https://github.com/thedusk4203/Menuto/actions/runs/39763499529), Python/PostgreSQL 18.4 + web. [PR #56](https://github.com/thedusk4203/Menuto/pull/56) đã merge tại `f49e9b1`; [CI sau merge](https://github.com/thedusk4203/Menuto/actions/runs/39764143827) pass cả Python và web.

## M1.2 Recipe / Preparation Foundation

Schema mới `0005` bổ sung 10 bảng, tổng 33 bảng domain. Recipe identity tách immutable
RecipeVersion; aggregate có seal và ràng buộc giao dịch lắp ráp, chặn cả thêm child sau
commit. Recipe giữ culinary truth, chỉ tham chiếu Ingredient, không có Retail SKU/quote
hoặc household inventory. Cooking transformations có context/version/provenance và chỉ
EP_RAW_G→COOKED_G; M1.1 AP→EP giữ nguyên.

Năm scaling policies được kiểm trên các tier tác giả khai báo; adjustment envelope riêng
không đổi serving count. Contextual substitution và exact approved combinations chuẩn bị
giới hạn một structural substitution. `GroundedRecipeVariantDraft` là culinary input
**DRAFT/activation_ready=False**, chưa có nutrition/safety/retail/inventory resolution.
Không có generator, Planner V4, ledger, CookingBatch execution hoặc full Validator.

[Review A–H](M1_2_RECIPE_DOMAIN_REVIEW.md) và
[evidence kiểm thử/CI](M1_2_RECIPE_PREPARATION_EVIDENCE.md) ghi phạm vi và kết quả thực chạy.
Không suy từ slice này thành toàn bộ M0/M1 hoàn tất. Tại thời điểm M1.2, M1.3 chưa triển khai; trạng thái M1.3 cập nhật bên dưới.

Review PR #57 yêu cầu hai correction trước freeze: path-specific transformation selection
và cấm COUNT-targeted substitutions. `0006` bổ sung seal policy guard, không đổi 33 bảng,
seal/version functions hoặc `0005`. [Correction evidence](M1_2_CULINARY_BINDING_CORRECTIONS.md)
là nguồn nghiệm thu mới; 559 tests/CI của 0005 vẫn là evidence lịch sử, không tự chứng minh
hai counterexamples đã được sửa. User đã APPROVED TO FREEZE M1.2 tại commit `05382b6425a072433e38db99a1de101b577804a0` (0001–0006, 33 bảng).

## Quyết định còn mở

Theo §24.3: ReferenceFeasibleCost; numeric nutrition/launch defaults; retail terms; exploration/cooldown; assumption-debt thresholds; receipt-calibrated probability model; chi tiết database/contracts của blueprint. Ba subsystem Execution/Validation/Learning đã chốt kiến trúc, không còn liệt kê là architecture open decisions.


## M1.3 Inventory Physical Ledger Foundation

Migration 0007 thêm **5 bảng**, tổng **38 bảng domain**. M1.1/M1.2 giữ nguyên boundary;
0001–0006 không đổi. [Review A–J](M1_3_INVENTORY_DOMAIN_REVIEW.md) và
[evidence thực chạy](M1_3_INVENTORY_PHYSICAL_LEDGER_EVIDENCE.md) là phạm vi nghiệm thu.

Physical lots/movements có household ownership, explicit evidence/basis, append-only
corrections, DB-controlled balance và chronological ordering. Reservations/releases là
intent riêng, không movement. Prepared dish dùng contextual servings; prepared component
dùng COOKED_G. Retail mapping giữ FK exact immutable evidence; không sở hữu yield.

Service acquire/consume/discard/reconcile/reserve/release/snapshot và expiry foundation
đã có; không có HTTP business endpoints/UX, fulfillment/import, CookingBatch execution,
ActivePlan, projections, replan hoặc Independent Validator đầy đủ. Handoff snapshot và
batch flow vẫn DRAFT. M1.3 đã **APPROVED/FROZEN** ngày 2026-10-23 tại
`fef629965dd7401e27c98b5a0c523998a27017c4`, migrations0001–0007, 38 bảng;
688 Python / 313 PostgreSQL-real tests, benchmark22/22 và postmerge CI SUCCESS.
Không suy thành full M0/M1 hoặc execution readiness.


## F — Plan/revision foundation (MTR-016, FROZEN)

[Review A–J](PLAN_REVISION_FOUNDATION_DOMAIN_REVIEW.md) ghi ownership, immutable full
revision graph, mutable head view, reservation/fulfillment/batch seams và adversarial traces.
Repo chưa đặt số M1.4 cho slice này; giữ tên F và business identifier MTR-016.
Foundation implementation tại `0008` thêm 13 bảng, tổng 51 bảng; có sealed relational proposals,
immutable accepted revisions, atomic head/reservation orchestration và physical boundary links.
[Evidence F](PLAN_REVISION_FOUNDATION_EVIDENCE.md) ghi test/CI thực chạy và giới hạn.
Operational activation/revision bị chặn tới khi có real PRECOMMIT gate và full subject;
draft authoring không được gọi là ActivePlan operational hoặc PlanRevision0.
Trạng thái review: **READY FOR ARCHITECTURE/FREEZE REVIEW**, chưa FROZEN.


Correction MTR-016 `0009`: [scope/cut-line evidence](PLAN_REVISION_SEMANTIC_CORRECTIONS.md).
Thêm typed quantitative shopping contributions, enforce SINGLE_MEAL dependency closure
và freeze advice theo scheduled_at/planned_at/need_by. Schema hiện0009, **52 bảng**;
0001–0008 giữ nguyên. Legacy v1 giữ hash, graph v2 explicit; PRECOMMIT vẫn fail-closed.
Trạng thái **READY FOR ARCHITECTURE/FREEZE REVIEW**, chưa tự FROZEN hoặc đóng MTR-016.


## Current freeze and validation foundation

MTR-016 đã user APPROVED/FROZEN tại `751a40e847dd2e664a6fe3667c272bc740a44e49`,
head0009,52 bảng. Các submission/evidence READY trước đó là lịch sử; freeze foundation
không mở production PRECOMMIT hoặc cooking execution. Không sửa migrations0001–0009.

Slice tiếp theo: **MTR-025 ValidationSubject v1 foundation + supported subset MTR-026**.
[Review A–G](VALIDATION_SUBJECT_FOUNDATION_REVIEW.md), [evidence](VALIDATION_SUBJECT_FOUNDATION_EVIDENCE.md).
Implemented: immutable policy/source-aware snapshot, read-only coherent capture, independent
source-supported root/exclusion/nutrition/yield/physical replay checks. Structurally supported:
future source/validator handoff. Deferred: full clinical/root policy, grounding/scenario,
planned material/batch/revision/assumption/bridge validation and production authority.
Subject/report remain FOUNDATION_ONLY and non-authorizing; no migration/new tables. Domain
bundle10 is independent of DB head0009. Full MTR-025/026 production acceptance is PARTIAL.


## MTR-019A — Explicit culinary binding / independent grounding

[Review A–J](MTR_019A_CULINARY_BINDING_REVIEW.md), [evidence and matrix](MTR_019A_CULINARY_BINDING_EVIDENCE.md).
Migration0010 adds two proposal-owned relational binding tables (54 domain tables). Plan-intent.v3
includes exact selected culinary facts and batch signature; v1/v2/frozen MTR-025 hashes stay unchanged.
Independent RecipeGroundingValidator verifies primitive authored choices; companion input is
culinary-validation-input.v1. No production authority, full MTR-019/026 completion or Execution.
MTR-025 remains user FROZEN at219b556. MTR-019A is user **FROZEN / APPROVED** at
`4a6207ac52bc5ba0ce95de2df54c0c949f36066e`, migration0010 /54 domain tables.
RecipeGroundingValidator is an accepted completed sub-capability of MTR-026;
neither full MTR-019 nor full MTR-026 is complete.

## MTR-019B — Demand-driven culinary candidate generation

[Focused review](MTR_019B_VARIANT_GENERATOR_REVIEW.md),
[evidence](MTR_019B_VARIANT_GENERATOR_EVIDENCE.md).
Implemented: deterministic finite demand expansion from reviewed authored rules, exact tiers,
approved structural combinations and explicit zero adjustments; canonical source/candidate
identities, exclusion filters, fail-closed resource budgets and selected-binding handoff.
Candidates remain culinary DRAFT, not fully grounded solver-facing DishCandidates.
Frozen MTR-019A wire/hash/seal/validator semantics and migrations0001–0010 unchanged.
No new persistence: schema remains0010 /54 tables. MTR-019B is user **FROZEN / APPROVED** at
`23dd0b3bc3245ac9c7ef5493968f8ab120242f00`.
Deferred: downstream evidence-backed reasons, nutrition/retail/inventory grounding, shortlist,
solver, MTR-030 refinement, Execution and production PRECOMMIT/TOCTOU authorization.

## MTR-019C — Candidate Grounding

[Review A–J](MTR_019C_CANDIDATE_GROUNDING_REVIEW.md),
[evidence](MTR_019C_CANDIDATE_GROUNDING_EVIDENCE.md).
Planning assembles immutable nested domain resolutions from canonical read-only capture:
Recipe culinary/preparation, compatible Nutrition references, Retail supply coefficients/evidence,
Inventory confirmed possibilities and canonical member restrictions. No caller nutrient/price summaries.
Supported complete primitive inputs produce GroundedDishCandidate; missing facts return INCOMPLETE,
forbidden/forged choices REJECTED. Candidate activation remains False; no physical/reservation writes.
No migration/new tables;0010 /54 remains current. Frozen A/B/validator hashes/semantics unchanged.
COUNT nutrition and allergen/diet classification unavailable; policy/scenarios/basket cost, global
allocation/feasibility, MTR-020 and Execution deferred. MTR-019/026 remain PARTIAL.
MTR-019C is user **FROZEN / APPROVED** at `ffaa009031d8def0e32a654266a871cced44d35e`.

## MTR-020A — Conservative Pareto Shortlist Foundation

[Dependency/architecture review](MTR_020A_PARETO_SHORTLIST_REVIEW.md),
[verification evidence](MTR_020A_PARETO_SHORTLIST_EVIDENCE.md).
Implemented: canonical capture-only ingress; pure exact coverage frontier; exact duplicate
handling; dominance witnesses; explicit fail-closed resource limits. Different culinary,
nutrition, inventory, member/cutoff and non-contained supply provenance choices survive.
No synthetic cost/nutrition-fit/effort/preference scores. Serialized candidates/ready flags
cannot establish canonical ingress. No source re-grounding/DB IO in shortlist core.
No tables/migration;0010 /54 and frozen A/B/C semantics unchanged; domain bundle14 additive.
Full MTR-019/020/026 remain PARTIAL. Role/utility portfolio, evidence-backed reasons, COUNT
nutrition, classification, global feasibility, solver, Execution and PRECOMMIT remain deferred.
MTR-020A is user **FROZEN / APPROVED** at `87278ed1ea79771f80b09b161ff711ff066556a8`,
head0010 /54 tables. Full MTR-019/020/026 remain NOT COMPLETE; MTR-021/Execution NOT STARTED;
PRECOMMIT fail-closed. [Post-freeze dependency review](POST_MTR_020A_DEPENDENCY_REVIEW.md)
finds MTR-020B BLOCKED. User approved it with an ordering correction: **MTR-040A → MTR-041
→ MTR-024 → MTR-020B → MTR-021**. MTR-019D is optional support later/in parallel, not next.
[MTR-040A explicit preference design](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_REVIEW.md) was approved
with required correction: raw declarations have no EvidenceStrength; it belongs to later derived
MemberBehaviorProfile. The correction was applied before implementation.

## MTR-040A — Explicit Member Preference Foundation

[Actual implementation evidence](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_EVIDENCE.md).
Forward0011 adds four tables (58 total): reviewed affinity vocabulary, member source frontier,
stable typed preference streams and immutable declaration facts. Explicit source only; all five
targets, actor/subject ownership, replacement/retraction, CAS/idempotency and coherent snapshot.
No raw EvidenceStrength/assertion_confidence/TasteFit; no inferred feature assignment or shared
preference copying. MemberBehaviorProfile derivation/learning and full MTR-040 remain incomplete.
Frozen A/B/C/020A,0001–0010 unchanged; production gate fail-closed. MTR-041 not started;
MTR-020B/021 blocked. Submit040A **READY FOR ARCHITECTURE/FREEZE REVIEW**, not self-FROZEN.


MTR-040A remains **NOT FROZEN** after review of PR #71 (`f451d7f`).
[Authorship correction](MTR_040A_AUTHORSHIP_CORRECTION_EVIDENCE.md): forward `0012` replaces only
`menuto_preference_append()` and adds the inverse application guard. SELF iff canonical linked
member equals subject; representative iff different (including NULL); OWNER/EDITOR only.
Wrong modes reject, never normalize. No historical row/hash rewrite or new table; current schema
`0012` / **58 tables**, migrations0001–0011 unchanged. No MTR-041 work started.


## User freeze040A and MTR-041A preview-source subset

User **FROZEN / APPROVED MTR-040A** at `06dc1dcbf38d474b90f7bfb74f04651e884285e4`
(0012 /58 tables). Earlier NOT FROZEN entries above are historical review stages. Full040
remains incomplete; no declaration/schema semantics change in041A.

[MTR-041A review](MTR_041A_RECENT_EXPOSURE_DOMAIN_REVIEW.md) selects current sealed proposal
previews only. [Evidence](MTR_041A_RECENT_EXPOSURE_EVIDENCE.md) distinguishes capture/replay from
durable confirmed exposure: no such producer exists. Recipe-level per-member facts stay
PROVISIONAL/PROPOSAL_PREVIEW; consumption history UNAVAILABLE, empty is not never-exposed.
No migration/new tables:0012 /58. No cooldown/novelty/taste scores, learning router, assumption
graph, HorizonBridgeResolver, MTR-020B/021, Execution or PRECOMMIT authorization. Full041 remains
PARTIAL and cannot yet supply complete production portfolio novelty/exposure.
User has **FROZEN / APPROVED MTR-041A** at `774405ebe51f126fec10ce61c4dd41b9d229230a` (PR #73), scope
**proposal-preview subset only**. [Post-merge CI](https://github.com/thedusk4203/Menuto/actions/runs/40020836511)
is SUCCESS for Python/web against that commit. Evidence:1403 Python /630 PostgreSQL-real,
1350/1350 prior regressions retained,53 new tests, benchmark22/22, client10/10;172 old domain
schema definitions unchanged and9 additive. Schema0012 /58 tables, no migration.

Full040/041 and MTR-017 remain incomplete; MTR-038/039 are not implemented; MTR-046 lacks the
required feature mappings. MTR-024/020B/021 remain BLOCKED. **Do not start MTR-024**:041A supplies
proposed scheduled exposure only, not accepted commitment, cooking/consumption/taste evidence
or durable history. Execution not started; PRECOMMIT fail-closed. No following slice is authorized
by this freeze record.

## Post-MTR-041A dependency review — awaiting approval

[Review and capability/source/fingerprint matrices](POST_MTR_041A_DEPENDENCY_REVIEW.md)
propose **MTR-041B recipe-level, single-proposal cooldown-policy assessment** as the smallest
next slice. Existing provisional source truth can support a target-relative predicate with
self-exclusion and an explicit versioned policy, without fabricating consumption/novelty or
accepted-schedule evidence. This is a recommendation only; no041B implementation starts here.
Full041 is not completable now;024/020B/021 remain BLOCKED. No migration, frozen040A/041A
runtime change, Execution or PRECOMMIT authority. Approval is required before implementation.

## MTR-041B — proposal-local cooldown subset / FROZEN

User approved the dependency review and authorized only this subset from391a53e.
[Contract decisions](MTR_041B_RECIPE_COOLDOWN_REVIEW.md) /[evidence](MTR_041B_RECIPE_COOLDOWN_EVIDENCE.md).
Pure RECIPE_ID predicate on one current captured proposal, explicit versioned cooldown policy,
exact microsecond witnesses, target-relative interval and whole-target-meal exclusion.
No-match is scoped absence, not global safety/novelty/history. No DB IO, new persistence or
migration:0012 /58 tables. Frozen040A/041A semantics/hashes unchanged. Full040/041 remain
incomplete;024/020B/021 blocked, Execution unstarted, PRECOMMIT fail-closed.
User **FROZEN / APPROVED MTR-041B** at `43192c7303e42c7bac321728edecaa8421a58e9a` (PR #77).
Post-merge CI40073675503 SUCCESS;1453 Python /635 PostgreSQL-real,1403 prior regressions retained,
50 new tests, benchmark22/22, client10/10;181 prior schema definitions unchanged +5 additive.
Schema0012 /58 tables; migrations0001–0012 immutable. No correction PR is needed.

## Post-MTR-041B dependency review — recommendation only

[Remaining capability matrix and next-slice proposal](POST_MTR_041B_DEPENDENCY_REVIEW.md)
recommend **MTR-041C — proposal-local Recipe-ID decay-policy evidence** as a narrowly scoped
next step: apply an explicit versioned age policy to frozen041B's exact witnesses, without
inventing confirmed history, a global penalty or novelty. This is a proposed sub-slice, not
an implemented capability or permission to implement. No migration expected; full040/041,
MTR-024/020B/021 remain incomplete/blocked. Execution unstarted; PRECOMMIT fail-closed.

## MTR-041C — as-of-capture proposal-local decay trace / FROZEN

User approved the next subset with reduced rational, non-negative lower-bound and explicit
policy-time/horizon clarifications. [Review](MTR_041C_DECAY_TRACE_REVIEW.md) /
[evidence](MTR_041C_DECAY_TRACE_EVIDENCE.md). Six additive contracts; pure per-witness trace over
fully revalidated frozen041B. Explicit ordered policy bands, exact reduced retention multiplier,
zero retention keeps source witness, no aggregates/RepeatPenalty/novelty/utility. AS_OF_CAPTURE
only; future retrospective mode and full-decay horizon are separate semantics. No persistence/
migration:0012 /58 tables. Frozen040A/041A/041B unchanged. Full041/024/020B/021 blocked, Execution
unstarted, PRECOMMIT fail-closed.
User **FROZEN / APPROVED MTR-041C** at `338566c84197196dae12bbefd9e1ef0c96958f2f` (PR #79).
Post-merge CI40076805477 SUCCESS;1540 Python /640 PostgreSQL-real,1453 prior regressions retained,
87 new tests, benchmark22/22, client10/10;186 previous definitions unchanged +6 additive.
Schema0012 /58 tables, no migration;0001–0012 immutable. No correction PR required.

## Post-MTR-041C dependency review — historical recommendation (now approved)

[Review](POST_MTR_041C_DEPENDENCY_REVIEW.md) proposes **MTR-041D — proposal-local Recipe-ID
RepeatPenalty interpretation policy**. Current source truth supports a separately approved,
explicit exact-rational policy for this one dimension; it does not support global history,
novelty or final utility. Source/classification branches remain prerequisites for their wider
capabilities. The user subsequently approved041D implementation, tracked below. Full040/041
incomplete,024/020B/021 BLOCKED; Execution unstarted, PRECOMMIT fail-closed. No migration.


## MTR-041D — proposal-local RepeatPenalty interpretation / FROZEN

User-approved implementation after PR #80, baseline59cc0a48b52addc5c7d612fae6b81b0681e90a00.
[Review](MTR_041D_REPEAT_PENALTY_REVIEW.md) / [evidence](MTR_041D_REPEAT_PENALTY_EVIDENCE.md).
Pure Learning interpretation fully reparses frozen041C/source/041B. Explicit versioned policy,
SUM_RETAINED_OCCURRENCES only; positive explicit unit penalty, exact reduced nonnegative
rational contributions/total in POLICY_REPEAT_PENALTY_UNITS, unbounded above. Empty evidence
returns scoped NO_MATCH/None; zero-retained witnesses yield explicit0 with provenance retained.
No production parameter default. AS_OF_CAPTURE only; activation_ready=False. Global history,
RepeatPenalty, novelty, TasteFit, authority and final utility remain unavailable.
Five additive contracts (bundle19);192 old definitions unchanged. No persistence/migration:
0012 /58 tables;0001–0012 unchanged. Frozen040A/041A/B/C unchanged. Full040/041 incomplete,
024/020B/021 BLOCKED; Execution NOT STARTED; PRECOMMIT fail-closed. User freeze recorded below.


## User freeze decision — MTR-041D

User **FROZEN / APPROVED MTR-041D** at `091daa81ae9bc67b536fec4956ba1f52780fe9c9`
(PR #81). Exact post-merge [CI40088853692](https://github.com/thedusk4203/Menuto/actions/runs/40088853692)
SUCCESS, Python and web;1626 Python /645 PostgreSQL-real,1540 prior regressions retained,
86 additive tests, benchmark22/22, client10/10. Schema0012 /58; no migration,0001–0012 unchanged.
Acceptance is only proposal-local Recipe-ID RepeatPenalty interpretation. Full040/041 remain
incomplete;024/020B/021 BLOCKED, Execution NOT STARTED, PRECOMMIT fail-closed. No correction PR.
[Post041D dependency review](POST_MTR_041D_DEPENDENCY_REVIEW.md) recommends a separately
approved046A reviewed culinary feature assignment source design, not an041E arithmetic wrapper.
No next implementation is authorized or started by recording this freeze.


## MTR-046A — Reviewed Culinary Feature Assignment / FROZEN

User authorized implementation from `c1dcf48907fa4dcb1acc210acd15ceba670345f0` after approving
PR #84's corrected [design](MTR_046A_CULINARY_FEATURE_ASSIGNMENT_DESIGN.md).
[Implementation evidence](MTR_046A_IMPLEMENTATION_EVIDENCE.md) records actual gates and limits.
Forward migration **0013** adds **13 relational tables**, actual metadata total **71**;
released0001–0012 remain unchanged. Catalog owns Ingredient→PROTEIN; Recipes owns invariant
METHOD cooking contexts and authored FLAVOR/MAIN_PROTEIN path scopes. Review coverage is separate
from positive assignment. Append-only replacements/retractions preserve complete lineage,
provider identity, reviewer/provenance, CAS/idempotency, database-protected heads/frontiers and
transactional aggregate closure. No Recipe seals are redesigned.

Dimension-only Planning capture is coherent read-only RR/SERIALIZABLE. Pure discovery needs no
term IDs; optional pure term queries reuse the same subject. METHOD/FLAVOR neither read/lock/hash
nor CAS the Catalog association generation. MAIN_PROTEIN pins current Catalog support; later
association changes make fresh results STALE_ASSOCIATION, preserving old captured replay.
SQL/Python key/command identity parity and direct SQL/concurrency/migration tests cover this seam.
Captured outputs remain PROPOSAL_PREVIEW / activation_ready=False.

User **FROZEN / APPROVED MTR-046A** at `428b992892ac2aeebdbedb8bb3fd5e436e76415c`
(PR #85). Exact post-merge [CI40172577535](https://github.com/thedusk4203/Menuto/actions/runs/40172577535)
SUCCESS, Python and web. Schema0013 /71 tables;0001–0013 are now immutable.
Full040/041/046 are incomplete;
024/020B/021 remain BLOCKED. No multi-fingerprint exposure integration, profile derivation,
TasteFit, novelty, safety inference, Execution or PRECOMMIT authority. PRECOMMIT stays fail-closed.

## Post-MTR-046A feature exposure source design — subsequently approved

[Dependency/design review](POST_MTR_046A_DEPENDENCY_REVIEW.md) proposes a coherent read-only
join of frozen041A proposal/member/meal allocation evidence and046A reviewed classification.
One selected proposal, METHOD/MAIN_PROTEIN/FLAVOR, distinct member×meal×dimension×term events,
full support witnesses and coverage diagnostics; no defaulting unknowns to zero/absence.
The user subsequently approved the name/design and authorized implementation from c609d3bf.
The original review was documentation only; see the implementation status below.

## MTR-041E — Proposal-local Reviewed Feature Exposure Sources / FROZEN

[Evidence](MTR_041E_FEATURE_EXPOSURE_EVIDENCE.md). Eleven additive definitions and one pure
Learning API join exact batch/context/path reviewed sources to member/meal/allocation facts.
Planning captures one current proposal in one clean read-only RR/SERIALIZABLE transaction.
Multiple batches/versions supporting one term in a member's meal give one event and multiple
witnesses. ASSIGNED, finite REVIEWED_NONE and UNRESOLVED remain distinct; empty output has
machine-readable scoped absence. All digests/events/diagnostics are recomputed from attached
primitives. Evidence-cut digest is diagnostic only, never liveness/PRECOMMIT authority.
No persistence/migration;0013 /71 tables. Frozen040A/041A–D/046A algorithms and226 old definitions
unchanged. No feature B/C/D policy or profile/utility/Execution work. Full040/041/046 incomplete;
024/020B/021 BLOCKED, PRECOMMIT fail-closed. User freeze is recorded below.

User **FROZEN / APPROVED MTR-041E** at `146c7cee9915c91593c4ec7518615e065d7abf53` (PR #87),
without a correction PR. Exact [post-merge CI40183397009](https://github.com/thedusk4203/Menuto/actions/runs/40183397009)
SUCCESS, Python/web;1860 Python /755 real-PG,1758 prior identities retained,102 additive tests,
benchmark22/22, client10/10. Schema0013 /71, no migration;040A/041A–E/046A FROZEN.
The implementation was accepted without reopening its source or identity semantics.

## Post-MTR-041E historical dependency review — superseded by040B freeze below

This paragraph records the earlier dependency-review stage; current040B status is FROZEN below.

[Dependency matrix](POST_MTR_041E_DEPENDENCY_REVIEW.md) recommends detailed design of remaining040
explicit-source target affinity/derived-strength/prior-availability semantics. Suggested040B suffix
and scope require review; not implementation-ready or authorized here. Frozen040A already provides
coherent read-only capture. A profile policy/contract and production prior sources do not yet exist.
Feature-aware041 policies are independently designable but not prerequisites before this design.
Full040/041/046 remain incomplete;024/020B/021 BLOCKED; Execution NOT STARTED; PRECOMMIT fail-closed.

## MTR-040B — Explicit-source Target Affinity Profile / FROZEN

User architecture/freeze review **APPROVED**, freeze requested2026-10-26.
[Implementation/freeze evidence](MTR_040B_EXPLICIT_TARGET_AFFINITY_EVIDENCE.md),
[approved design](MTR_040B_EXPLICIT_TARGET_AFFINITY_DESIGN.md): Preferences owns exact-target
explicit preference interpretation, canonical target identity capture, a complete versioned
explicit interpretation policy, rational explicit affinity, explicit evidence strength and
deterministic replay/fingerprints. Canonical implementation PR #90 head
`6ef6b8f9d64a6b1c45fce570857d3cd0568385c6`, merge
`08ddeb87604b8913175ae3852a32ce6f4b8d1273`;
[post-merge CI40215578850](https://github.com/thedusk4203/Menuto/actions/runs/40215578850) SUCCESS,
2015 tests /785 real-PG, benchmark22/22, client10/10. Schema0013 /71; no migration.

Only the current explicit declaration head determines affinity/strength. UNDECLARED and RETRACTED
are distinct from NEUTRAL; explicit zero may be AVAILABLE. Retries/history do not strengthen
assertions. No cross-target transfer. Affinity is a policy coordinate, not probability/calibrated
utility; EvidenceStrength is explicit-evidence policy metadata, not statistical confidence.
Offline consistency does not prove canonical database origin. Full-source fingerprint includes
complete captured source/frontier and capture identity, not merely visible target rows.

Prior/shrinkage and learned/contextual/passive evidence remain UNAVAILABLE. Cross-target inference
and candidate aggregation remain NOT_PERFORMED; planner_ready=False and activation_ready=False.
No default prior, inferred preference, planner weight, TasteFit or planner/PRECOMMIT authority.
Full040/041/046 remain incomplete;024/020B/021 BLOCKED; Execution NOT STARTED. No MTR-040C or
next-milestone implementation is started or authorized. Earlier design-only entries are history.

**MTR-040B FROZEN — READY FOR NEXT-MILESTONE ARCHITECTURE REVIEW, NOT IMPLEMENTATION.**

## MTR-041F — Proposal-local Reviewed Feature Repeat Policy / FROZEN / APPROVED

The user approved the [041F design](MTR_041F_FEATURE_REPEAT_POLICY_DESIGN.md) after design PR #92
merged at `9e9dfc0f9cf234a8e0c32082652318becce38bfd`. The additive implementation provides pure
cooldown, exact decay and proposal-local feature penalty for one member/target/dimension/term.
Full041E source/preview is revalidated each stage; frozen046A resolves finite term coverage.
Explicit versioned policies, contained lookback and minimum consumed-child cutoff are enforced.
Unresolved potential occurrences keep the aggregate unavailable; scoped empty is not zero;
complete nonempty explicit-zero traces remain AVAILABLE0/1. All44 acceptance cases and current
receipts are recorded in [implementation evidence](MTR_041F_FEATURE_REPEAT_POLICY_EVIDENCE.md).
Frozen040A/B,041A–E,046A remain unchanged.256 old definitions retained plus20 additive=276;
schema0013 /71, no migration or new source/persistence/HTTP endpoint. Full041 stays PARTIAL.
040C design NOT READY/NOT AUTHORIZED,040B prior/shrinkage UNAVAILABLE;024/020B/021 BLOCKED.
No learned profile, novelty, TasteFit, accepted/confirmed/consumed/cross-horizon/family history,
Execution or PRECOMMIT authority. User FROZEN / APPROVED at exact canonical main
`63e6b9f7dff3f061657fa96680a69cfc6fd1ae06`; exact push
[CI40257089579](https://github.com/thedusk4203/Menuto/actions/runs/40257089579) SUCCESS,
python/web SUCCESS. PR #93 supplied implementation, PR #94 corrected a new test's UUID-order
assumption; frozen runtime semantics were unchanged by that correction.

## Post-MTR-041F dependency review — design only

[Independent dependency review](POST_MTR_041F_DEPENDENCY_REVIEW.md) finds no additional proposal-local
041 prerequisite for remaining profile work.040B already derives explicit exact-target affinity and
strength; full040 is PARTIAL, while prior-backed/hierarchical/learned derivation is still blocked.
Proposed next implementation target: canonical reviewed exact-target preference-prior source,
pending dedicated source design/authority/coordinate approval; no milestone suffix assigned.
Future source persistence is expected to require a forward migration; none is made here.
Full040/041/046 remain incomplete;024/020B/021 BLOCKED, Execution NOT STARTED, PRECOMMIT FAIL-CLOSED.
No 040C or other implementation is authorized by this review or its merge.

## Reviewed exact-target preference-prior source — implemented, not frozen

The user APPROVED PR #95's dependency selection at exact main
`0a6abb4b004e9a1fa82e3aac8905a2a0fc9d3e47`, push
[CI40263357354](https://github.com/thedusk4203/Menuto/actions/runs/40263357354) SUCCESS.
The user subsequently APPROVED the [dedicated source design](PREFERENCE_PRIOR_SOURCE_FOUNDATION_DESIGN.md)
and AUTHORIZED source implementation from main577f32a (PR #96). The additive
[implementation](PREFERENCE_PRIOR_SOURCE_FOUNDATION_EVIDENCE.md) is **IMPLEMENTED / NOT FROZEN**:
dedicated SCRAM/provider authority, immutable exact-target reference revisions, coherent capture
and pure replay. Preferences semantics remain separate from member authorship/publication authority.
Migration0014 adds7 tables:0014 /78 domain tables;276 old definitions unchanged,23 additive,299 total.
No providers, principals, provider capability grants or prior values are seeded. No milestone number
assigned.040B prior/shrinkage stay UNAVAILABLE. Production content, coordinate mapping, shrinkage
and MTR-040C remain unauthorized; full040/041/046 incomplete,024/020B/021 BLOCKED, Execution NOT STARTED,
PRECOMMIT FAIL-CLOSED. Architecture/freeze review of this implementation is still required.
