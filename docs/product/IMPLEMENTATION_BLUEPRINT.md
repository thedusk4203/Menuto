# Milestone 0/1 — entry checklist V1.3

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
PRECOMMIT FAIL-CLOSED; planner_ready=False, activation_ready=False. No downstream design or
implementation is authorized. Earlier delivery/review-stage status statements below are historical;
this closure receipt supersedes current-status wording only, never frozen behavior.

## Post-MTR-040 next-gate review — recommendation only

The [next-milestone dependency review](POST_MTR_040_NEXT_MILESTONE_DEPENDENCY_REVIEW.md)
recommends **Candidate-bound Reviewed Culinary Feature Projection Foundation** as **READY FOR
DETAILED DESIGN**: an additive 019B/C + 046A candidate-input integration, with no MTR suffix assigned.
This is a review recommendation, not detailed-design approval or implementation authorization.
MTR-040 remains COMPLETE / issue #41 CLOSED — COMPLETED. Full 041/046 remain PARTIAL;
020B/021/024 remain BLOCKED. No downstream work starts; the review PR must not auto-merge.



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
