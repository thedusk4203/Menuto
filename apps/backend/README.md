# Backend foundation

FastAPI modular monolith theo V1.3 §8, §9 và §16. Có 16 namespace domain và migration `0001` → `0002` → `0003`, hiện có 21 bảng: 8 bảng Foundation và 13 bảng M1.1 Retail/Procurement. Xem [Implementation Blueprint M0/M1](../../docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md) và [evidence M1.1](../../docs/product/M1_1_RETAIL_PROCUREMENT_EVIDENCE.md) để phân biệt phần đã triển khai và schema đích.

Từ root repository:

```powershell
uv sync --locked
uv run uvicorn app.main:app --reload
```

`GET /api/v1/health` là process liveness, không phải readiness database/planner. Health luôn khai báo `stage=foundation`, `planner_ready=false`.

Không import benchmark adapter vào backend: micro-model chỉ dùng kiểm tra harness, không được cung cấp như Planner V4. Không dùng `create_all()` để thay migration runner.

`validation` và `learning` được tách theo ADR-010/011, hiện chỉ namespace. Chưa có production validator/learning engine hoặc state projections.

## Persistence và tests

Đặt `MENUTO_DATABASE_URL` với driver `postgresql+psycopg` rồi chạy `uv run alembic upgrade head`. Database đích phải được tạo trước. Không tự kết nối hoặc chạy migration lúc API startup. Credentials không ghi vào repository.

```powershell
$env:MENUTO_DATABASE_URL = 'postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/menuto'
uv run alembic upgrade head
uv run python tools/export_domain_contracts.py --check
```

Integration tests cần `MENUTO_TEST_POSTGRES_URL` trỏ vào maintenance database `postgres` trên loopback. Test tự tạo database tên ngẫu nhiên `menuto_test_<uuid>`, chạy migration up/down/up, rồi xóa đúng database đó. Cần user có quyền CREATEDB; không dùng URL dữ liệu ứng dụng. Khi không có URL, tests PostgreSQL được ghi rõ skipped; CI có PostgreSQL service và chạy thật.

```powershell
$env:MENUTO_TEST_POSTGRES_URL = 'postgresql+psycopg://TEST_USER:TEST_PASSWORD@127.0.0.1:5432/postgres'
uv run pytest
```

Bootstrap household là service nội bộ nhận user đã tồn tại và không tự commit. Profile concurrency dùng ORM version counter; authorization, idempotent command execution và bulk-SQL CAS chưa có business service trong đợt này. Nutrition source facts append-only; correction tạo source version mới. Bảng yield chung đã được gỡ; M1.1 đã lưu edible yield ở Retail Product→Ingredient mapping, còn cooking yield thuộc Recipe/Preparation ở M1.2. Xem [sáu sửa đổi foundation](../../docs/product/FOUNDATION_CORRECTIONS.md).

Retail repository trả frozen contracts và không tự commit. Tất cả 13 bảng Retail append-only; downgrade `0003` dừng nếu có dữ liệu. Quote/snapshot chỉ DRAFT; `derive_price_quote` chưa có production eligibility/freshness/scoring policy. `RetailSourcedAPAssetDraft` chỉ là contract giữ mapping origin cho Inventory sau này, không tạo lot. Không có retailer scraper hoặc API nghiệp vụ Retail trong slice này. [Domain review A–G](../../docs/product/M1_1_RETAIL_DOMAIN_REVIEW.md) mô tả schema và các giới hạn.
