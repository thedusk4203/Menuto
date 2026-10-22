# Trạng thái foundation V1.3 và bằng chứng

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

Chưa có auth, NutritionPolicyEngine, PlanPolicyResolver, retail thật, inventory ledger, ActivePlan revision engine, production Independent Validator, learning router hoặc consumer closed loop. Entry checklist chưa hoàn thành toàn bộ; không gọi phần nền tảng đầu tiên là đạt cả Milestone 0/1.

## M1.1 Retail / Procurement Foundation

Đã triển khai và kiểm chứng local/CI: 13 bảng Retail mới qua migration `0003`, tổng **21 bảng domain**. Mapping Product→Ingredient sở hữu edible yield và review/provenance; fixed/catch/loose có semantics riêng; raw observation tách derived quote; reference fallback rõ nguồn. Cooking yield chưa triển khai ở Retail. Các quote/class/option/snapshot vẫn **DRAFT**, chưa activation-ready. Inventory chỉ thêm handoff draft giữ mapping, chưa có persistence/workflow.

[Evidence M1.1](M1_1_RETAIL_PROCUREMENT_EVIDENCE.md): **368 Python tests pass, gồm 138 PostgreSQL thật**, import/baseline/schema checks pass, 22/22 benchmark smoke, 10 client tests và web build pass. **GitHub CI PASS** cho implementation `ed11639`: [Foundation checks #14](https://github.com/thedusk4203/Menuto/actions/runs/39744442973), cả Python/PostgreSQL 18.4 và web; [PR #55](https://github.com/thedusk4203/Menuto/pull/55) vẫn draft. [Domain review A–G](M1_1_RETAIL_DOMAIN_REVIEW.md) ghi quyết định và giới hạn. Có thể bắt đầu review M1.2 Recipe/Preparation; chưa tự triển khai M1.2 hoặc M1.3.

## Quyết định còn mở

Theo §24.3: ReferenceFeasibleCost; numeric nutrition/launch defaults; retail terms; exploration/cooldown; assumption-debt thresholds; receipt-calibrated probability model; chi tiết database/contracts của blueprint. Ba subsystem Execution/Validation/Learning đã chốt kiến trúc, không còn liệt kê là architecture open decisions.
