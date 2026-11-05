# Milestone 0/1 — entry checklist V1.3

## Post-MTR-007 structural freeze — proposed measurement-basis / policy-v2 dependency gate

**MTR-007 source-bound estimator structural foundation: FROZEN**, following [PR #130](https://github.com/thedusk4203/Menuto/pull/130)
and [formal freeze receipt 6662354375](https://github.com/thedusk4203/Menuto/pull/130#issuecomment-6662354375).
Actual merged main `82b4a7c631acbc04ffbd522702bf3529d7e2e2d2` passed exact
[post-merge push CI 42050943839](https://github.com/thedusk4203/Menuto/actions/runs/42050943839):
**4,047 passed /0 skips**, 36 real PostgreSQL NRE executions /20 obligations,
SCRAM/TLS 16/16, benchmark 22/22, client 10/10; 503 frozen exported definitions
(480 retained +23 new), migration 0017 /108 domain tables, no 0018 or new persistence.
The complete [implementation evidence](MTR_007_SOURCE_BOUND_NUTRITION_RESOLUTION_ESTIMATOR_EVIDENCE.md)
is part of that already frozen scope.

The [post-freeze dependency review](POST_MTR_007_MEASUREMENT_BASIS_POLICY_V2_DEPENDENCY_REVIEW.md) is **a docs-only proposal awaiting
independent architecture review**. It recommends **source-bound measurement-basis applicability
and independent evidence containment — BOUNDED DETAILED DESIGN** before successful numerical
MTR-006 policy-integration v2. `PLANNED_INGREDIENT_INPUT_V1` is not automatically
physiological intake or a reviewed clinical comparison basis; the frozen MTR-006 v1
resolution interface stays fixture-only. Basis/content approval and integration v2 are
separately gated. This PR does not authorize design, implementation, production clinical
evidence/publication, policy v2, MTR-008, a new migration, or parent issue closure.

Nutrition Root, MTR-006 synthesis, MTR-007 estimator: **FROZEN STRUCTURAL FOUNDATIONS**.
Full MTR-006/007/008 remain OPEN/INCOMPLETE. Production Nutrition/clinical content gate
**CLOSED**; planner_ready=False, activation_ready=False; Execution NOT STARTED;
PRECOMMIT FAIL-CLOSED. Historical older `IMPLEMENTATION CANDIDATE` notices are
superseded for current status only; their original receipts remain historical evidence.

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
The separately authorized [bounded MTR-006 detailed-design proposal](MTR_006_SOURCE_BOUND_NUTRITION_POLICY_SYNTHESIS_CONTAINMENT_DESIGN.md)
is now **READY FOR ARCHITECTURE REVIEW — NOT APPROVED / NOT IMPLEMENTED**.
It proposes explicit rule-source authority, pure synthesis and independent containment; it adds
no runtime, contract, test, migration, tooling or data. Any future durable rule source requires
separate design approval and implementation authorization; no migration number is reserved.
Nutrition Root remains structurally FROZEN; production nutrition/evidence/qualification content
gate remains CLOSED. MTR-006/007/008 remain incomplete; no parent issue is closed.
Baseline: 3,782 tests / 0 skips, 447 exports, 0016 / 98 tables; no 0017.
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED; planner_ready=False; activation_ready=False.





Đây là checklist theo §23.5. [Blueprint M0/M1 và phần nền tảng đã triển khai](IMPLEMENTATION_BLUEPRINT_M0_M1.md) là tài liệu chi tiết; checklist chưa đạt toàn bộ tiêu chí cho các workflow ở milestones sau.

| Điều kiện | Trạng thái | Công việc / bằng chứng cần có |
| --- | --- | --- |
| V1.3 + 11 ADR + 30 invariants cùng phiên bản | Có trong repository | Baseline consistency check; original spec/invariants byte-exact |
| Units/measurement-basis contracts freeze | Đã có primitives + schema snapshot kiểm drift | MTR-003; calculation tách storage + explicit quantization/provenance; tests từ chối incompatible bases, float và số không hữu hạn |
| Ownership/lifecycle/state diagrams | Draft tài liệu | ARCHITECTURE.md; cần gắn testable domain contracts MTR-004/015/016/017/023 |
| ValidationSubjectSnapshot + planner request/output draft schemas | Đã có `m0-draft.2`, chưa validation-ready | MTR-025/027; typed immutable source facts, hashes/revision lock; liệt kê rõ primitive contracts còn thiếu |
| Neutral benchmark format + mutation fixture format freeze | Một phần | synthetic-v2 regression giữ nguyên; mutation fixtures đầy đủ còn thiếu MTR-002/026 |
| CI chặn validation → planner/solver internals | Có static rule + negative tests | Bao gồm public-facade/relative-import và contracts đường vòng; chưa chứng minh runtime isolation |
| Selective Smart Menu reuse strategy | Đã giữ | Spec §22; không fork schema/code/lịch sử hoặc coi nguồn tham khảo là đã port |
| M1.1 Retail/Procurement foundation | APPROVED TO FREEZE; PR #56 merged, post-merge CI pass | [Correction evidence](M1_1_RETAIL_CORRECTIONS_EVIDENCE.md); 23 domain tables ở 0004; M1.1 ownership/semantics giữ nguyên trong M1.2 |
| M1.2 Recipe/Preparation foundation | Authored schema/contracts + tests; nghiệm thu theo evidence | [Review A–H](M1_2_RECIPE_DOMAIN_REVIEW.md), [evidence](M1_2_RECIPE_PREPARATION_EVIDENCE.md); 0005 thêm 10 bảng, culinary grounded input vẫn DRAFT; không triển khai M1.3 |

## Thứ tự chuẩn bị đề xuất

1. Freeze units/basis/provenance và ownership contracts (MTR-003/004/005).
2. Draft immutable intent/execution/validation subjects và dependency contracts (MTR-015/016/017/023/025/027).
3. Chốt neutral lifecycle + mutation fixture format cho năm seams; tạo fixtures known-valid/known-invalid có kết quả độc lập.
4. Review entry criteria trước khi build policy/solver/consumer workflows.

Numeric examples trong spec/debate không tự trở thành production defaults. Không chốt schema DB, thresholds hoặc thuật toán qua tài liệu khung này.

Current canonical slice: [Exact-target Prior Compatibility & Shrinkage](EXACT_TARGET_PRIOR_SHRINKAGE_FREEZE_RECEIPT.md)
is **FROZEN / APPROVED** at5728411 (PR #100, exact push CI40351934792 SUCCESS;2597 tests).
Historical [implementation evidence](EXACT_TARGET_PRIOR_COMPATIBILITY_SHRINKAGE_EVIDENCE.md) starts
from12048de; this is not MTR-040C. Pure member-owned compatibility/shrinkage retains kind/
mapping-policy coordinate descriptors; no IO, persistence, migration0015 or production numeric defaults.
0014 /78 remains unchanged;299 old definitions +19 additive =318. Full040/041/046 incomplete;
024/020B/021 BLOCKED; Execution NOT STARTED; PRECOMMIT FAIL-CLOSED.
[Post-freeze review](POST_EXACT_TARGET_PRIOR_SHRINKAGE_DEPENDENCY_REVIEW.md) is APPROVED at73b3b0b
(PR #101; exact push CI40365344734 SUCCESS). Authorized dedicated DESIGN is now narrowed to
[Canonical Reviewed Hierarchical Preference Relation & Transfer-Policy Source Foundation](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_DESIGN.md),
DESIGN PROPOSAL / READY FOR ARCHITECTURE REVIEW. Separate verified publication/capture authority,
exact endpoints/context, versioned mappings and lifecycle come before a pure hierarchy consumer;
consumer is only a downstream seam. No source/consumer runtime,039/040C implementation or downstream
authority is authorized; no migration0015, physical table or permission enum is reserved. Documentation
merge is not architecture approval; no production direction/coefficient is introduced.


M1.3 đã APPROVED/FROZEN tại `fef629965dd7401e27c98b5a0c523998a27017c4`
(head0007, 38 bảng). [Evidence](M1_3_INVENTORY_PHYSICAL_LEDGER_EVIDENCE.md).
Review tiếp theo giữ tên canonical **F — Plan/revision foundation / MTR-016**:
[review A–J](PLAN_REVISION_FOUNDATION_DOMAIN_REVIEW.md). Chưa có operational activation;
PRECOMMIT capability/source resolution vẫn là dependency bắt buộc. Không đổi numbering.
