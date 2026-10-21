# Trạng thái foundation và bằng chứng

## Có trong scaffold

- 14 namespace domain, FastAPI process-liveness endpoint, React/TypeScript health shell và OpenAPI snapshot.
- Benchmark runner, CP-SAT micro-model, exhaustive reference độc lập, số học kiểm chứng, 18 fixtures synthetic có thể tái sinh và tests.
- Toolchain lock, CI checks và issue MTR-001..014. Đây là CI configuration; kết quả chạy thực được báo theo từng commit, không mặc định luôn xanh.
- Graphify phân tích AST + nội dung tài liệu để tạo bản đồ quan hệ, không thay validator hay test.

## Mapping invariant → công việc còn lại

| Invariant | Bằng chứng hiện tại / còn thiếu |
| --- | --- |
| INV-001 | Chưa có NutritionPolicyEngine; MTR-005/007 phải kiểm chứng preference không giảm guardrails |
| INV-002 | Chưa có BudgetPressure; MTR-008 phải tách system pressure khỏi user preference |
| INV-003 | Namespace households/nutrition; chưa có ownership/authorization schema/test |
| INV-004 | Micro-model test loại ingredient bị exclude; chưa có participant hard-constraint resolution |
| INV-005 | Fixtures candidate cố định; chưa có authored RecipeVersion/VariantRule production |
| INV-006 | CP-SAT micro-model chỉ chọn candidate có sẵn; không tạo biến thể món mới |
| INV-007 | Cooking namespace có sẵn; chưa có demand/batch/allocation model |
| INV-008 | Synthetic gate phân biệt fresh/stale/fallback; chưa có retail evidence pipeline |
| INV-009 | Chưa có ProcurementFragility/Stage 1 structural economics production |
| INV-010 | Micro-model kiểm tra budget/stress coefficients; chưa có budget outcome UX hoặc receipt guarantee |
| INV-011 | Không có probabilistic model hoặc P90 claim; calibration thực chưa triển khai |
| INV-012 | Tests phân biệt timeout/vô nghiệm; chưa có advisor/acceptance/activation lifecycle production |

## Chưa hoàn thành

MTR-001 có glossary nhưng chưa mirror toàn bộ invariants trong business tests. MTR-002 có foundation harness nhưng chưa có adapter Planner V4, large-pool reference hoặc numeric launch gates; do đó cả hai issue vẫn mở. MTR-003..014 chỉ có module boundary và acceptance criteria.

Chưa có auth, persistence/schema/migration, NutritionPolicyEngine, PlanPolicyResolver, retailer thật, inventory ledger, Planner V4, user workflow hoặc release readiness.
