# M1.1 — Canonical semantic corrections (0004)

Ngày: 2026-10-22, Asia/Saigon. Sửa findings sau review của `main` tại `7fe02d5`/PR #55. Không triển khai M1.2, Planner V4, physical inventory, Execution hoặc AI. [Domain review A–G hiện hành](M1_1_RETAIL_DOMAIN_REVIEW.md). Canonical ADR-006/V1.3 không đổi; implementation cũ dùng calibration sai nghĩa được thay bằng reference fallback.

## Quyết định đã triển khai

| Finding | Quyết định và guard |
| --- | --- |
| P0 calibration ngược nghĩa | RETAIL_OBSERVED = observation; REFERENCE_BASELINE = reference; CALIBRATED_REFERENCE = reference + calibration. Factory/contracts/SQL reject observation + calibration. 60.000/1.000g baseline × 1,1 = 66.000/1.000g; observation 50.000 giữ nguyên. |
| Availability | Hai reference origins luôn UNKNOWN, không tạo retail availability. Raw CONFIRMED vẫn chỉ là evidence ở observed_at. |
| Promotion primitive nói dối | Bỏ input/DB column depends_on_promotion. Property đọc từ quote.observation.is_promotion; reference origins không nhận promotion truth giả. |
| Single-source nhập tay | Bỏ input/DB column ở option. Snapshot derive coverage trực tiếp: paths, retailers, providers chưa UNAVAILABLE. Single-source=true nếu một trong ba coverage trực tiếp <2; reference không tăng direct counts. Đây là structural heuristic, không claim statistical independence/probability. |
| Package brittleness | Giữ assessed value nhưng yêu cầu brittleness_policy_version và option provenance. Rows cũ có marker explicit legacy-unversioned.0003, không giả đã được policy đánh giá. |
| Retailer lifecycle | Stable Retailer bỏ status. RetailerStatusFact append-only với effective_at/provenance; đọc latest effective_at≤as_of; không fact = unknown. Không đổi retailer ID để deactivate. |
| Product multiplicity | ProductVersion bắt buộc canonical_ingredient_id; composite FK khóa mọi mapping vào ingredient đó. Cho phép nhiều mapping/yield versions của cùng ingredient; mixed/composite decomposition defer. |
| Quote price ambiguity | ReferencePricePair giữ money_for_reference_quantity + priced_ap_g + AP_G/REFERENCE_WEIGHT_RATE. Root quote không còn .price/.priced_ap_g; SQL dùng reference_amount_minor/reference_ap_g. Cặp 60.000/1.000g không là giá pack 500g. ProcurementCostEvaluator chưa implement và bắt buộc trước Planner. |

Contracts đổi sang **retail-v2**, inventory-origin draft.2, schema bundle 4. Đây là breaking wire change; không alias CALIBRATED v1 sang CALIBRATED_REFERENCE hoặc tự nhận payload cũ.

## Migration và bảo toàn dữ liệu

- Thêm **0004_correct_retail_semantics.py**; không sửa 0001/0002/0003. DDL/functions đóng trong file revision; không import ORM metadata lúc migrate.
- Giữ 13 bảng Retail cũ; thêm retailer_status_facts và retail_legacy_option_assessments, tổng 23 domain tables.
- Upgrade khóa các bảng Retail trước preflight. Có CALIBRATED cũ thì dừng: observation không có reference baseline để tự suy ra provenance mới. Product không có mapping hoặc có nhiều ingredient khác nhau cũng dừng, cần canonical binding được giải quyết tường minh trước migration.
- Trường hợp không mơ hồ: thêm canonical binding từ mapping hiện có; giữ nguyên source observation/mapping và pair tiền/lượng. Rename quote columns không scale/round hoặc thay giá.
- Status cũ chuyển thành fact với kind LEGACY_STATE, source menuto.migration.0004/retailer-status.0003; không giả reviewed reference hoặc người dùng đã ghi event mới. Effective time giữ created_at của immutable legacy identity.
- Hai cờ authored cũ được copy nguyên vào audit archive trước khi bỏ columns; audit không tham gia fragility. Archive đóng với INSERT/UPDATE/DELETE/TRUNCATE sau migration.
- Status và source facts vẫn chặn UPDATE/DELETE/TRUNCATE. Downgrade khóa cả bảng mới/cũ và từ chối nếu có bất kỳ Retail rows nào; không bỏ audit/provenance hoặc tái diễn giải semantics corrected sang 0003.

## Kiểm chứng

Môi trường local: Windows, Python 3.13.14, PostgreSQL **18.4** riêng trên loopback. Harness tạo/drop database `menuto_test_<uuid>`; không dùng database ứng dụng. Chạy bằng Python trong `.venv` đã cài theo lock.

```powershell
$env:MENUTO_TEST_POSTGRES_URL = 'postgresql+psycopg://menuto_test@127.0.0.1:55441/postgres'
.venv/Scripts/python.exe -m pytest --basetemp=.local/pytest-0004-final-complete --tb=short --junitxml=.local/0004-final-tests.xml
```

**Kết quả cuối: 398 passed, 0 failed, 0 skipped, 33.93s; gồm 157 tests PostgreSQL thật.** Một warning có sẵn từ Starlette/httpx, không thay dependencies ngoài scope. [Machine-readable summary](M1_1_RETAIL_CORRECTIONS_TEST_RESULTS.json) giữ group counts, timestamp, JUnit hash và source hashes; SHA-256 các migration 0001–0003 đối chiếu với base main xác nhận không đổi.

| Nhóm | Kết quả local |
| --- | --- |
| Existing + corrected Retail unit/contracts | 68 + 11 = 79 passed |
| Retail SQL/migration tests đã cập nhật + correction cases | 109 + 16 = 125 passed |
| Existing Foundation PostgreSQL/migration | 24 + 8 = 32 passed |
| Architecture/baseline | 38 + 3 passed |
| Domain/precision/health | 42 + 8 + 3 passed |
| Existing synthetic benchmark tests | 68 passed |
| Ruff, baseline/import, domain/OpenAPI schema drift | PASS |
| Standalone fixtures/benchmark | 22/22 và 22/22 PASS |
| Client generated contracts, typecheck, tests, web build | PASS; 10 client tests |

Lượt chạy ngay trước kết quả cuối có một baseline link failure trong lúc tài liệu mới đang được tạo; đã hoàn tất tài liệu, baseline check và full suite đều chạy lại xanh. Không tính lượt đó là PASS.

Tests mới kiểm riêng canonical example và regression: reject observation calibration, keep direct price, UNKNOWN fallback availability, reject calibration sai retailer/store/category, pair ≠ package cost, reject authored booleans, derive structural coverage với hai retailer/provider hoặc fallback/unavailable, stable identity/effective history, canonical mapping FK với các yield revisions, populated 0003 upgrade giữ source/audit, malformed legacy fail/rollback, empty upgrade/downgrade/upgrade và Alembic drift. Existing Foundation, import boundaries và benchmark tiếp tục được chạy.

## CI và phần chưa implement

**Remote CI correction: chưa chạy; chờ user authorization cho payload/nhánh mới.** Implementation local commit `748ae81c6dd4a2b2a391e0b5f93bae325cbb0a3d`, nhánh `thedusk4203/m1-1-retail-canonical-fixes`, đích `thedusk4203/Menuto`. Automatic approval review từ chối push vì correction là payload/branch khác với PR #55 đã được cho phép trước đó. Không công bố qua công cụ khác để vượt từ chối. Cần user cho phép push và mở draft PR để có CI riêng. CI xanh của PR #55 chỉ là lịch sử của implementation cũ; không merge hoặc gọi freeze chỉ dựa trên green cũ.

Chưa có ProcurementCostEvaluator/rounding policy cho purchase cost, observation normalization/eligibility, hierarchy/shrinkage estimator, fragility optimizer score, mixed-product decomposition, retailer ingestion hoặc activation-ready planning. Retailer status history chưa là production eligibility policy. Không freeze freshness/calibration constants.

INV-007/008/009/018 được bổ sung semantic guards; coverage vẫn PARTIAL_FOUNDATION. Sau corrected tests/CI và review, có thể freeze M1.1 để chuyển M1.2; chưa tự bắt đầu M1.2.
