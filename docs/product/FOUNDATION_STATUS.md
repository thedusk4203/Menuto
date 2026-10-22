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
Không suy từ slice này thành toàn bộ M0/M1 hoàn tất. M1.3 chưa triển khai.

## Quyết định còn mở

Theo §24.3: ReferenceFeasibleCost; numeric nutrition/launch defaults; retail terms; exploration/cooldown; assumption-debt thresholds; receipt-calibrated probability model; chi tiết database/contracts của blueprint. Ba subsystem Execution/Validation/Learning đã chốt kiến trúc, không còn liệt kê là architecture open decisions.
