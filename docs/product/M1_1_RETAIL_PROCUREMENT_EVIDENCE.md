# M1.1 — Retail / Procurement evidence

Ngày kiểm chứng: **2026-10-22**, timezone Asia/Saigon. Kết quả: **slice foundation M1.1 đạt kiểm chứng local**; planning/procurement handoffs vẫn DRAFT. Không tuyên bố M0/M1 hoặc production planning hoàn tất. [Domain review và quyết định A–G](M1_1_RETAIL_DOMAIN_REVIEW.md).

## Những gì đã triển khai

- 13 SQLAlchemy 2 tables, đưa domain schema từ 8 lên 21 bảng. Registration tại `app/persistence/models.py`, ownership tại Retail.
- Migration mới `0003_retail_procurement_foundation.py`; giữ nguyên 0001/0002. DDL/trigger SQL đóng trong revision, không import ORM metadata.
- Frozen/extra-forbid/versioned `retail-v1` facts, quote/option/snapshot DRAFT; inventory origin seam `inventory-retail-origin.m1-draft.1` chưa tạo physical stock.
- Product→Ingredient mapping có edible yield, basis, review, version và provenance; exact AP→EP calculation, explicit storage quantization.
- Package fixed/catch/loose có riêng dữ liệu và purchase intent semantics. PriceObservation khác PlanningPriceQuote; calibrated/reference origins giữ nguồn.
- Repository contract↔row roundtrip, caller-owned transactions, nested evidence identity checks. Không có business HTTP endpoints mới.
- PostgreSQL composite FK/CHECK/unique + semantic triggers; mọi bảng M1.1 chặn UPDATE/DELETE/TRUNCATE. Downgrade khóa bảng rồi reject nếu bất kỳ bảng M1.1 có dữ liệu.
- Domain schema export cập nhật `urn:menuto:domain:foundation:3`. HTTP OpenAPI/client giữ nguyên.

## Tests thực chạy

Môi trường: Windows 11, Python **3.13.14**, Node **24.17.0**, PostgreSQL **18.4**, SQLAlchemy/Alembic/Pydantic theo `uv.lock`. Dùng PostgreSQL cluster test tạm trên loopback; harness tạo và drop đúng database ngẫu nhiên `menuto_test_<uuid>`. Không test trên database ứng dụng, không reset dữ liệu người dùng.

```powershell
# Admin URL loopback của PostgreSQL test, maintenance DB postgres; không dùng production URL.
$env:MENUTO_TEST_POSTGRES_URL = 'postgresql+psycopg://menuto_test@127.0.0.1:55440/postgres'
uv run pytest --basetemp=.local/pytest-m11-final --tb=short --junitxml=.local/m11-final-tests.xml
```

Lượt thực chạy dùng `.venv/Scripts/python.exe -m pytest` tương đương trong environment đã cài theo lock. **368 passed, 0 failed, 0 skipped, 16.99s.** Một warning có sẵn từ Starlette về httpx TestClient; không thay dependency ngoài scope.

| Nhóm | Kết quả |
| --- | --- |
| Retail unit/contracts | 68 passed |
| Retail real PostgreSQL + M1.1 migrations | 106 passed |
| Existing foundation PostgreSQL | 24 passed |
| Existing 0001→0002 migration/data safety tests, nay đi qua head 0003 | 8 passed |
| Architecture boundaries | 38 passed |
| Baseline | 3 passed |
| Existing domain contracts + precision + health | 53 passed |
| Existing synthetic benchmark regressions/harness | 68 passed |
| **Tổng PostgreSQL thật** | **138 passed** |
| **Tổng Python** | **368 passed** |

JUnit local: `.local/m11-final-tests.xml` (ignored build evidence). Tóm tắt kiểm chứng được lưu cùng tài liệu trong [M1_1_TEST_RESULTS.json](M1_1_TEST_RESULTS.json).

## Coverage theo yêu cầu nghiệm thu

| # | Yêu cầu | Bằng chứng thực chạy |
| --- | --- | --- |
| 1 | FIXED_PACK valid/invalid | Contract roundtrip, strict package count, SQL field exclusivity/positive/scale và price-one-package |
| 2 | CATCH_WEIGHT bounds | Unit + SQL low/expected/high, non-degenerate bounds, không fake exact checkout weight |
| 3 | LOOSE_SCALE | Unit minimum+k×step, reject package count; SQL minimum/step và field exclusivity |
| 4 | Edible yield đúng owner | Retail mapping FK/columns, Catalog không có edible_yield |
| 5 | AP→EP precision | `123.456789 × 0.876543 = 108.215184200427`; explicit quantization/residual, wire roundtrip |
| 6 | Không generic cooking persistence | Metadata không unit_conversions/cooking_yield; Retail không import Recipe |
| 7 | Cross-product/ingredient integrity | SQL gắn member sai product/ingredient bị FK reject; quote mapping/package/class composite FKs |
| 8 | Money/currency | Unit int/float/nonfinite/negative/mixed currencies; SQL price constraints và retailer-currency FK |
| 9 | Observation/provenance roundtrip | Repository roundtrip source URI/hash/version/time, complete procurement snapshot |
| 10 | Different providers | Cùng external record được lưu với source_system khác nhau |
| 11 | Duplicate source identity | Cùng provider/record/version bị unique reject |
| 12 | Invalid availability | Unit + SQL reject GUARANTEED |
| 13 | Numeric invalid | Unit + SQL NaN/Infinity/negative/excess scale; ORM rejects float và implicit rounding |
| 14 | Reference fallback | Origin riêng, UNKNOWN availability, không retail source giả; region/ingredient/currency/source guards |
| 15 | Raw != derived | Hai contract/bảng riêng; exclusive FK origin và exact source-price derivation guard |
| 16 | Migration cycle | 0002→0003→0002→0003, base→head→base→head và legacy populated upgrade |
| 17 | Metadata drift | Alembic `command.check` trong PG harness và dedicated M1.1 cycle |
| 18 | Direct SQL constraints | Package/mapping/observation/quote/option negative tests; actual existing cross-retailer/store context |
| 19 | Foundation regression | Existing domain/precision/household/catalog/migration tests pass; hai head-revision assertions cập nhật 0003 |
| 20 | Import boundaries | 38 architecture tests + checker; validator chỉ đọc Retail contracts; Retail không import Recipes/Inventory/Planning/Execution |
| + | Append-only | UPDATE/DELETE/TRUNCATE SQL trên cả 13 bảng đều reject |
| + | Fake backup và snapshot identity | Same purchase path không được clone thành backup; nested facts sai dưới cùng ID bị repository reject |

## Các kiểm tra ngoài pytest

| Check | Kết quả |
| --- | --- |
| Ruff toàn repository | PASS |
| `check_architecture_baseline.py` | PASS: 30 invariants, 11 ADR, 50 linked tasks |
| `check_import_boundaries.py` | PASS: 16 contexts |
| `export_domain_contracts.py --check` | PASS |
| `export_openapi.py --check` | PASS |
| `generate_synthetic_fixtures.py --check` | PASS: 22 fixtures |
| Standalone benchmark runner | PASS: 22/22; harness smoke, không Planner V4 |
| `npm run contracts:check` | PASS |
| `npm run typecheck:client` | PASS |
| `npm run test:client` | PASS: 10 tests |
| `npm run build:web` | PASS |

## CI và giới hạn bằng chứng

**GitHub CI cho thay đổi này: chưa chạy; chờ quyền công bố nhánh.** GitHub CLI ngoài sandbox đã xác nhận có đăng nhập và quyền repository, nhưng automatic approval review từ chối lệnh push vì mã nguồn/tài liệu là sensitive egress và chưa có user authorization rõ cho payload/đích đến. Không thực hiện push qua công cụ khác để vượt qua từ chối. Nhánh dự kiến `thedusk4203/m1-1-retail-procurement-foundation` tại `thedusk4203/Menuto`; cần user cho phép push và mở draft PR trước khi chạy remote CI.

Workflow hiện có chạy toàn bộ pytest với PostgreSQL service 18.4 và các checks nêu trên; các bước chức năng tương ứng đã pass local. Không dùng trạng thái CI của commit cũ để chứng nhận thay đổi hiện tại. CI Linux vẫn cần chạy sau khi đưa thay đổi lên PR.

Không có real retailer prices, live integration, calibrated launch constants, auth, production eligibility/scoring, shopping basket optimization, physical inventory, RecipeVersion/Preparation persistence, ActivePlan/Execution, Independent Validator hoặc AI. Không sinh CP-SAT model mới. Không claim P90/probability, checkout certainty hoặc production activation readiness.

## Thay đổi invariant coverage và bước tiếp theo

INV-007/008/009 nay có Retail foundation evidence; INV-017/018 có mapping/price primitive chain, provenance và SQL constraints. Đây vẫn là **PARTIAL_FOUNDATION**, không phải full invariant certification. INV-003/011/013 giữ ranh giới ownership/intents, chưa có physical lifecycle. Xem [INVARIANT_COVERAGE.md](INVARIANT_COVERAGE.md).

**Đủ nền tảng kỹ thuật để review và bắt đầu M1.2 Recipe/Preparation.** Điều kiện phát hành/merge M1.1 còn lại là CI trên commit/PR thực. M1.2 phải giữ cooking yield thuộc Recipe/Preparation và không sửa mapping Retail. Slice này dừng ở M1.1; không tự triển khai M1.2/M1.3.
