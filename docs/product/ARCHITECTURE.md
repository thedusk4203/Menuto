# Scaffold kiến trúc V1.2

Nguồn chuẩn: §8, §9, §16 của đặc tả; ADR-001..008 giữ nguyên. Repo hiện là modular monolith foundation; chưa có service nghiệp vụ hay DB được provision.

## Ranh giới

Web React/TypeScript gọi HTTP API FastAPI. OpenAPI được sinh và kiểm tra từ API thật. `shared` chỉ giữ primitive kỹ thuật, không chuyển business policy vào một shared god module.

| Namespace backend | Trách nhiệm định hướng |
| --- | --- |
| identity | Identity and consent |
| households | Household ownership and membership |
| nutrition | Member nutrition policies |
| catalog | Canonical ingredient and nutrition facts |
| recipes | Authored and versioned culinary variants |
| retail | Retail evidence and procurement |
| inventory | Household inventory ledger |
| policy | Orthogonal resolved plan policies |
| planning | Planner orchestration and immutable snapshots |
| cooking | Batch production and allocations |
| shopping | Shopping requirements and purchases |
| execution | Meal execution and consumption |
| preferences | Declared and behavioral preferences |
| assistant | Bounded intent parsing and explanation |

Các namespace chưa export model/schema nghiệp vụ. Luật import đã được enforce bằng tools/check_import_boundaries.py và architecture tests; transaction/giao tiếp nghiệp vụ vẫn bổ sung cùng implementation; không coi sự tồn tại của thư mục là đã có module hoàn chỉnh.

## Benchmark nằm ngoài trusted production path

`benchmark.protocol.BenchmarkAdapter` là điểm nối runner/adapters. Hiện có SyntheticCpSatAdapter và exhaustive reference độc lập. Cả hai dùng neutral scenario format, không phải production PlanRequest.

Verifier kiểm tra micro-model bằng số học riêng, không import optimizer. Nó chưa chốt kiến trúc Independent Validator V2 đang mở ở §24.3. Backend không import hoặc expose synthetic solve endpoint.

## Dữ liệu và toolchain

Python 3.13.14 và OR-Tools 9.15.6755 đã được kiểm thử cùng toolchain lock. PostgreSQL/SQLAlchemy/Alembic là hướng persistence; chưa có schema/migration nên không chạy create_all khi startup. Queue/worker là optional path sau đo latency.

Frontend scaffold chỉ có trang trạng thái và health request thật. Khi phát triển UI nghiệp vụ cần query cache, schema validation, accessibility và progressive disclosure theo đặc tả.

## Điều cần giữ khi mở rộng

- Household ownership tách actor; tracked physiology tách shared resources.
- Recipe flexibility do authored rules, solver chỉ chọn grounded candidates.
- Policy axes độc lập; không tái tạo PlanningMode.
- Numeric constants, launch thresholds và execution lifecycle chưa khóa cần quyết định/evidence riêng.


## Import policy được kiểm tra tự động

Cross-context imports chỉ được đi qua namespace contracts hoặc public và theo allowlist trong tools/check_import_boundaries.py. Các hướng chính: recipes/retail → catalog; inventory → households/catalog/retail; policy → households/nutrition/preferences; planning → các domain nguồn; shopping/execution → planning và các domain execution liên quan. Không có cạnh recipes → planning hoặc retail → shopping.

Assistant có thể gọi planning.public/contracts, không import repository/model nội bộ của planning. Shared không import domain; toàn bộ backend không import synthetic benchmark. Relative imports được resolve; context mới và dynamic import/eval/exec trong domain phải được review thay vì âm thầm bypass.

Đây là static import enforcement, không phải sandbox bảo mật hoặc bằng chứng mọi SQL/runtime side effect được phân tách. Public facades và contracts phải giữ trách nhiệm domain; một tên thư mục public không tự chứng minh interface tốt.
