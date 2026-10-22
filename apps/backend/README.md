# Backend foundation

FastAPI modular monolith theo V1.3 §8, §9 và §16. Có 16 namespace domain và migration `0001` → `0002` → `0003` → `0004` → `0005` → `0006` → `0007`, hiện có 38 bảng: 8 bảng Foundation, 15 bảng Retail, 10 bảng Recipe/Preparation và 5 bảng Inventory. Xem [Implementation Blueprint M0/M1](../../docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md) và [correction evidence M1.2](../../docs/product/M1_2_CULINARY_BINDING_CORRECTIONS.md) để phân biệt phần đã triển khai và schema đích.

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

Retail repository trả frozen `retail-v2` contracts và không tự commit. Tất cả facts Retail append-only; retailer status nằm ở history riêng. `0004` từ chối legacy CALIBRATED quotes và product có canonical ingredient mơ hồ; downgrade từ chối khi có Retail data. Quote chỉ expose reference_price_pair, chưa phải purchase cost. Calibration chỉ áp reference; promotion/coverage được derive. Quote/snapshot vẫn DRAFT, chưa có production eligibility/freshness/scoring policy hoặc ProcurementCostEvaluator. `RetailSourcedAPAssetDraft` draft.2 giữ mapping origin, không tạo lot. [Domain review A–G](../../docs/product/M1_1_RETAIL_DOMAIN_REVIEW.md) mô tả đầy đủ.

Recipe repository ghi aggregate nguyên tử và trả frozen `recipe-v1` snapshots. Trong cùng
giao dịch: tạo Recipe nếu chưa có, thêm version cùng toàn bộ child facts, rồi seal.
Không thêm child hoặc sửa/xóa nội dung cũ; correction tạo version mới. `0005` từ chối
downgrade khi có Recipe data. SQL guards kiểm cả completeness, tier arithmetic và
preparation context. Culinary binder chỉ chọn authored tier/rules và delta trong envelope;
không thực hiện generation, household safety hoặc Independent Validator.
[Review M1.2](../../docs/product/M1_2_RECIPE_DOMAIN_REVIEW.md) và
[evidence](../../docs/product/M1_2_RECIPE_PREPARATION_EVIDENCE.md).

`0006` cấm COUNT-targeted substitutions tại seal và từ chối upgrade nếu dữ liệu 0005 có
rule dạng này; cần xử lý/archival tường minh, không rewrite facts bất biến. Downgrade
0006 chỉ gỡ guard, không mất dữ liệu; protection của 0005 giữ nguyên. Binder chọn net
transformation đúng ingredient path; raw base không bị ép transform bởi alternate path.


## M1.3 physical inventory

0007 thêm 5 bảng (38 tổng). `InventoryService` ở `modules/inventory/public.py` nhận frozen
inventory-v1 commands; caller sở hữu transaction/commit. Important: rollback transaction
khi command lỗi; retry toàn transaction khi SQLSTATE 40001/deadlock, giữ nguyên idempotency
key và payload. Acquire cần caller-stable lot_id, explicit evidence và household editor.
Idempotency scope là household × source_system × key **trong từng family** movement,
reservation hoặc release; fingerprint phân biệt concrete command. External source identity
cũng unique trong từng family/household/provider. Không dùng key mới khi retry.

Snapshot khóa shared household fence; mọi DB inventory writer lấy exclusive fence trước lot
balance lock/update. Serializes writes per household (trade-off V1); balances dùng revision
để stale RR writers không tính trên snapshot cũ. Physical truth là immutable history, không
cache. Commands không nhận calculated quantity: caller phải quantize explicit trước storage.
Read snapshot là effective-time cutoff trong recorded facts, không future projection.

Reservations active tới explicit full release. Release + consume có thể cùng transaction,
nhưng phải giữ nondecreasing occurred_at/phase. Expiry không xóa vật chất hoặc auto-release
intent; `position.allocatable` bằng zero nếu unusable. Confidence trên lot là initial observation,
không phải confidence inference sau thời gian. CONFIRMED không là probability.

[M1.3 review](../../docs/product/M1_3_INVENTORY_DOMAIN_REVIEW.md),
[evidence](../../docs/product/M1_3_INVENTORY_PHYSICAL_LEDGER_EVIDENCE.md).
