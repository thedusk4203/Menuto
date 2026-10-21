# Menuto

Menuto giúp cá nhân/hộ gia đình tối ưu kế hoạch ăn và mua sắm theo ngân sách, dinh dưỡng, tồn kho và khả năng thực hiện.

**Trạng thái:** scaffold kiến trúc V1.2 + benchmark harness synthetic chạy được. Chưa có Planner V4 hoặc workflow nghiệp vụ hoàn chỉnh.

## Nguồn chuẩn

- [Development Spec V1.2](docs/MENUTO_DEVELOPMENT_SPEC_V1_2.md).
- [Architecture Invariants](docs/ARCHITECTURE_INVARIANTS.md).
- [ADR-001..008](docs/adr/).
- [Glossary](docs/product/GLOSSARY.md), [kiến trúc scaffold](docs/product/ARCHITECTURE.md), [trạng thái/giới hạn](docs/product/FOUNDATION_STATUS.md).
- [MTR-001 → MTR-014](docs/product/BACKLOG.md): issue đã tạo trên GitHub, vẫn mở cho phần chưa đạt acceptance criteria.

Implementation có thể bổ sung chi tiết chưa khóa. Thay đổi mâu thuẫn ADR/invariant đã chấp nhận phải có superseding ADR; không âm thầm đi lệch trong code.

## Chạy tại máy

Yêu cầu Python 3.13.14 (uv có thể cài), uv 0.11.28, Node 24.x và npm. Dependencies được khóa trong uv.lock và một package-lock.json tại root cho npm workspace.

```powershell
uv sync --locked
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

Web: http://127.0.0.1:5173. API docs: http://127.0.0.1:8000/docs. Web chỉ có trang foundation gọi health API; health không kiểm chứng DB/planner readiness.

## Cấu trúc

```text
apps/backend/app/modules/   14 namespace theo V1.2 §9
apps/backend/app/shared/    Technical primitives và health contract
apps/backend/tests/        Health/API tests
apps/backend/workers/      Đường mở rộng, chưa có worker
apps/web/                  React/TypeScript/Vite foundation
packages/contracts/        OpenAPI snapshot từ FastAPI
packages/api-client/       Generated TypeScript contracts và standalone runtime validator
benchmark/                 CP-SAT micro-model, reference độc lập, verifier, fixtures, runner
data/                      Seeds/imports, chưa có dữ liệu thật
docs/                      Spec, invariants, ADR, glossary, architecture, backlog
infra/                     Ranh giới hạ tầng; chưa provision database/cloud
tools/                     Export contracts và tái sinh synthetic fixtures
graphify-out/              Bản đồ quan hệ và báo cáo Graphify sinh từ corpus
```

Không dùng adapter trong benchmark như Planner V4 production. Không có policy dinh dưỡng lâm sàng, retailer thật, auth, migration hoặc inventory ledger hoàn chỉnh. [Benchmark README](benchmark/README.md) nêu rõ model hỗ trợ và giới hạn.

## Kiểm tra trước khi commit

Theo [CONTRIBUTING](CONTRIBUTING.md). CI chạy Python tests/lint, import boundaries, OpenAPI/fixtures, benchmark, generated client drift/typecheck/tests và frontend build; JSON runtime là artifact, không phải dữ liệu production.

Main được bảo vệ bằng PR, check python/web của GitHub Actions và cấm force-push/xóa nhánh (kể cả admin). Cấu hình mong muốn được lưu trong .github/branch-protection.main.json.

Graphify là công cụ phát triển tùy chọn, không phải runtime của sản phẩm. Chỉ ba output công khai của graph được quản lý trên Git; interpreter, cache và sidecars tại máy bị bỏ qua. Graph là bản đồ tài liệu/code, không chứng minh feature đã hoàn thành.

## Intentionally open after V1.2

1. Execution State Machine.
2. Independent Validator V2 scope/independence.
3. Behavioral Learning / cold-start / anti-filter-bubble.
4. ReferenceFeasibleCost implementation.
5. Numeric benchmark and nutrition policy constants.
6. Retail acquisition/terms and future receipt-calibrated probability model.

Các phần còn mở không được chốt bằng các con số trong synthetic fixtures.
