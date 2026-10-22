# Menuto

Menuto giúp cá nhân/hộ gia đình tối ưu kế hoạch ăn và mua sắm theo ngân sách, dinh dưỡng, tồn kho và khả năng thực hiện.

**Trạng thái:** foundation đã căn chỉnh theo kiến trúc V1.3. Health API, web shell và benchmark synthetic chạy được; chưa có Planner V4 hoặc closed-loop workflow nghiệp vụ. Milestone 0/1 chưa hoàn thành.

## Nguồn chuẩn

- [Development Spec V1.3](docs/MENUTO_DEVELOPMENT_SPEC_V1_3.md).
- [30 Architecture Invariants](docs/ARCHITECTURE_INVARIANTS.md).
- [ADR-001..011](docs/adr/).
- [Glossary](docs/product/GLOSSARY.md), [kiến trúc](docs/product/ARCHITECTURE.md), [trạng thái/bằng chứng](docs/product/FOUNDATION_STATUS.md).
- [Backlog V1.3 MTR-001 → MTR-050](docs/product/BACKLOG.md).
- [Chuyển mã V1.2 → V1.3](docs/product/BASELINE_MIGRATION_V1_3.md), [entry checklist Milestone 0/1](docs/product/IMPLEMENTATION_BLUEPRINT.md).
- [Implementation Blueprint M0/M1](docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md): đã có units/Pydantic contracts và migration đầu tiên cho 9 bảng; các handoff planner/validation vẫn là draft. [Hướng dẫn database/tests](apps/backend/README.md).

V1.3 là baseline duy nhất đang hiệu lực. V1.2 chỉ còn trong lịch sử Git; mã invariant/backlog cũ không được diễn giải theo nghĩa V1.3. Các bản gốc người dùng đặt tại root được giữ ở máy và bỏ qua trong Git; `docs/` là bản chuẩn được quản lý.

Thay đổi mâu thuẫn ADR/invariant đã chấp nhận cần superseding ADR. Những chi tiết chưa khóa phải được phân biệt với quyết định đã có.

## Chạy tại máy

Yêu cầu Python 3.13.14 (uv có thể cài), uv 0.11.28, Node 24.x và npm. Dependencies khóa trong uv.lock và một package-lock.json tại root.

```powershell
uv sync --locked
uv run python tools/check_architecture_baseline.py
uv run python tools/check_import_boundaries.py
uv run pytest
uv run ruff check .
uv run menuto-benchmark --output benchmark/results/latest.json
uv run uvicorn app.main:app --reload
```

Ở terminal khác, từ root:

```powershell
npm ci
npm run contracts:check
npm run test:client
npm run dev --workspace @menuto/web
```

Web: http://127.0.0.1:5173. API docs: http://127.0.0.1:8000/docs. Health chỉ kiểm tra process liveness, không chứng minh database/planner readiness.

## Cấu trúc

```text
apps/backend/app/modules/   16 namespace theo V1.3 §16.4, gồm validation và learning
apps/backend/app/shared/    Technical primitives và health contract
apps/backend/tests/        Health, architecture/import và baseline consistency tests
apps/backend/workers/      Chưa có worker
apps/web/                  React/TypeScript/Vite foundation
packages/contracts/        OpenAPI snapshot từ FastAPI
packages/api-client/       Generated TypeScript client và runtime validator
benchmark/                 CP-SAT micro-model, reference, verifier, fixtures và runner
data/                      Seeds/imports, chưa có dữ liệu thật
docs/                      Spec, 30 invariants, 11 ADR, glossary, backlog và blueprint
infra/                     Chưa provision database/cloud
tools/                     Baseline/import checks, export và fixture generator
graphify-out/              Bản đồ tài liệu/code, không chứng minh feature hoàn tất
```

## Thứ tự phát triển

Theo V1.3 §20: Milestone 0 contracts/units/benchmark → Milestone 1 household/data/execution foundation → Milestone 2 policies/snapshots → Milestone 3 Planner V4/validator → Milestone 4 refinement/repair/horizon bridge → Milestone 5 consumer closed loop → Milestone 6 public readiness.

Execution State Machine, Independent Validator và Behavioral Learning đã có quyết định kiến trúc trong ADR-009..011; implementation vẫn chưa có. Các quyết định còn mở gồm ReferenceFeasibleCost, numeric nutrition/launch gates, retail acquisition/terms, exploration/cooldown, assumption-debt thresholds, receipt-calibrated probability model và chi tiết DB/contracts cho blueprint (§24.3).

## Kiểm tra và giới hạn

Theo [CONTRIBUTING](CONTRIBUTING.md). CI kiểm baseline docs, import boundaries, Python, OpenAPI/fixtures, benchmark, generated client và web build. Main yêu cầu PR + checks python/web, strict up-to-date; cấm force-push/xóa kể cả admin.

22 fixtures hiện tại có provenance synthetic-from-spec-v1.2 và được giữ nguyên để bảo toàn regression evidence; không đổi nhãn thành coverage V1.3. [Ma trận benchmark V1.3](benchmark/V1_3_SCENARIO_MATRIX.md) ghi rõ phần còn thiếu. Không dùng synthetic adapter như Planner V4 production.

Graphify là công cụ phát triển tùy chọn. Chỉ ba output công khai được track; cache/interpreter/manifest giữ local. Smart Menu là reference tại máy, không đưa code/lịch sử cũ vào Menuto.
