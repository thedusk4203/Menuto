# M1.1 — Retail / Procurement domain review

Ngày: 2026-10-22. Phần A–G đã được trình bày trước khi thay code; tài liệu này ghi lại quyết định đã triển khai. Nguồn chuẩn: [V1.3 §12](../MENUTO_DEVELOPMENT_SPEC_V1_3.md), [ADR-006](../adr/ADR-006-retail-procurement-abstraction.md), [ADR-010](../adr/ADR-010-independent-validator.md), [blueprint](IMPLEMENTATION_BLUEPRINT_M0_M1.md). Không thay canonical Foundation, ADR hoặc invariant.

## A. Entities và bảng

| Bảng | Ý nghĩa và quan hệ chính |
| --- | --- |
| retailers | Retailer identity, country/currency/status |
| store_regions | Một store hoặc region scope; thuộc retailer, có region_code và scope_code |
| retail_products | Phiên bản SKU của retailer, category/brand và source provenance |
| retail_packages | Phiên bản purchase behavior của product; AP gram trong M1.1 |
| ingredient_product_maps | Phiên bản Product→Ingredient, edible yield, AP_G→EP_RAW_G, review/confidence/provenance |
| price_observations | RetailOffer là observation có thời điểm, không tạo bảng offer mutable song song |
| procurement_classes | Abstraction versioned theo ingredient và granularity, chỉ DRAFT |
| procurement_class_members | Product mapping được chấp nhận, equivalence/rationale/provenance |
| reference_price_books | Reference version theo region; không có retailer_id |
| reference_price_entries | Giá proxy AP gram theo ingredient, currency và confidence; provenance từ book |
| retail_price_calibrations | Retailer × store/region × category; factor, evidence_count, ordinal confidence, method/source version |
| planning_price_quotes | Derived draft với FK về mapping/package/class và nguồn giá; không phải observation |
| planning_procurement_options | Rank 0 primary, rank >0 backup, quote, substitution_group và fragility assessment primitives |

M1.1 thêm 13 bảng vào 8 bảng Foundation: **21 bảng domain**, ngoài `alembic_version`. Không dùng JSONB, không có RecipeVersion/cooking/physical inventory/ActivePlan tables.

## B. Ownership và lịch sử

- Catalog sở hữu Ingredient; Retail chỉ tham chiếu bằng FK.
- Retail sở hữu các facts/catalog mua hàng dùng chung. Không gắn household giả vào retailer/product/quote. Household sẽ sở hữu tài sản/giao dịch thực tế ở slice riêng.
- Product là identity phiên bản SKU trong retailer. Package và mapping có identity/version riêng, không suy chuyển đổi từ SKU name hoặc package label.
- Toàn bộ rows M1.1 append-only; PostgreSQL chặn UPDATE, DELETE và TRUNCATE. Sửa source/review/calibration bằng identity/version mới, không sửa nguồn đã được quote tham chiếu.
- Các cột context lặp lại phục vụ composite FK, không phải hai nguồn truth độc lập: retailer/store/product/package, class/ingredient/granularity và mapping/product/ingredient đều được ràng buộc.
- Repository không commit, không tự tạo nested source. Khi nhận snapshot lồng nhau, repository đối chiếu primitive facts với identity bất biến đã lưu. Caller sở hữu transaction.

## C. Evidence gốc và dữ liệu dẫn xuất

`PriceObservationFact` có product/package, retailer/store/region ID, Money, lượng AP được báo giá, promotion, source quality, availability và Provenance. Provenance giữ source_system, external_record_id, source_version, observed_at, source_uri/content_hash tùy chọn. Unique source identity được scope theo provider và fact table; external_record_id không bị ép thành Identifier nội bộ.

`PlanningPriceQuoteDraft` lưu riêng với ba origin:

| Origin | Nguồn bắt buộc | Availability |
| --- | --- | --- |
| RETAIL_OBSERVED | observation | Đọc evidence ở observation, kể cả CONFIRMED vẫn chỉ tại observed_at |
| CALIBRATED | observation + calibration đúng retailer/store-region/category | Vẫn đọc observation, calibration không nâng availability |
| REFERENCE_BASELINE | reference entry + book | UNKNOWN; không tạo retail observation giả |

`derive_price_quote` chỉ nhận lựa chọn nguồn tường minh và policy_version. Không tự fallback, không tự chọn giá thấp nhất, không tự chứng nhận freshness/eligibility. DB trigger kiểm lại source money/currency/reference quantity/time; composite FK kiểm ownership/context. Quote không có cột availability riêng để drift khỏi source.

Calibration là factor do nguồn bên ngoài cung cấp, không phải thuật toán học trong slice này. Phép nhân exact phải ra integer minor units; nếu có phần lẻ thì reject, không tự làm tròn hoặc gắn probability/P90. Reference AP price là proxy fallback trên basis AP_G đã khai báo, không phải nutrition price EP hoặc giá cửa hàng thật. Chưa có calibrated-reference/shrinkage resolver; không ngầm dùng observation calibration cho reference.

## D. AP→EP

```text
RetailProduct + Ingredient
    → IngredientProductMap(id, version, AP_G, EP_RAW_G, factor, review, provenance)
    → ProductIngredientConversionFact(mapping, input AP, calculated EP)
```

Chỉ mapping REVIEWED được áp dụng. Factor trong `(0,1]`, storage 6 decimal places, calculation giữ precision Foundation; storage kết quả cần QuantizationPolicy và signed residual. Không silent rounding sau phép nhân.

`RetailSourcedAPAssetDraft` nằm ở `inventory/contracts.py`, chỉ là interface draft cho tương lai: household asset giữ full mapping snapshot; ingredient phải khớp mapping và basis phải AP_G. Contract này không tạo lot hoặc confirmed stock. Neutral `RawIngredientAssetFact` m0 cũ vẫn là validator draft chưa đủ dữ liệu, không được dùng như retail acquisition handoff hoàn chỉnh. Không sửa Foundation để import ngược Retail vào neutral domain.

Cooking yield EP_RAW_G→COOKED_G tiếp tục thuộc Recipe/Preparation cho M1.2. `YieldConversion` neutral hiện có chỉ được reuse như calculation value object; không có persistence generic cho hai loại yield.

## E. Package/granularity

| Granularity | Primitive facts | Purchase intent |
| --- | --- | --- |
| FIXED_PACK | fixed_ap_g; các trường catch/loose phải NULL | Số package nguyên dương; observation định giá đúng một package |
| CATCH_WEIGHT | low <= expected <= high, low < high; không có fixed/min/step | Số package nguyên dương; expected/bounds không phải exact checkout weight |
| LOOSE_SCALE | minimum_ap_g >0, step_ap_g >0; không có fixed/catch fields | AP weight = minimum + k × step, k nguyên không âm; không có package count |

Price là integer minor units cho `priced_ap_g` của evidence. Với catch/loose đây là giá cho trọng lượng tham chiếu, không phải tổng tiền checkout. Quote luôn giữ reference quantity và PackageFact. Class khóa granularity; mỗi option giữ package version riêng nên primary/backup khác cỡ pack vẫn thể hiện được.

Chưa có purchase persistence nên discrete package_count và loose requested quantity nằm trong typed PurchaseIntent, kiểm bằng PackageFact.validate_purchase. DB bảo vệ package facts, bounds/basis và observation price semantics; không tạo bảng shopping chỉ để lưu intent trong slice này.

RetailNumeric sử dụng NUMERIC không ép scale, kèm CHECK `value = trunc(value,6)`, giới hạn magnitude và positive/finite. Miền giá trị bằng StoredQuantity, nhưng SQL trực tiếp không được lợi dụng rounding của NUMERIC(18,6). ORM bind vẫn dùng Foundation PersistedDecimal validator. Money là BIGINT + currency, không float.

## F. Invariant coverage

- INV-007: raw evidence/derived quote tách bảng, origin rõ, không checkout guarantee.
- INV-008: accepted products, primary/backup, distinct purchase paths, package behavior, promotion/single-source dependence, mapping/source quality, substitution groups. Chưa có ProcurementFragility score hoặc optimizer.
- INV-009: ordinal evidence quality không phải probability; không có P90 hoặc statistical confidence claim.
- INV-017/018: primitive mapping/package/source chain có identity/basis/provenance; conversion có thể tính lại. Chưa triển khai Independent Validator.
- INV-003/011/013: dùng chung retail facts khác household physical assets; quote/purchase intent không tạo inventory hay confirmed reality.

Collection contract/repository yêu cầu đúng một primary, ranks/quotes/purchase paths khác nhau, accepted reviewed mappings, granularity và currency thống nhất. DB cho phép draft class chưa đủ option để xây dần; nó chưa activation-ready. Unique rank và trigger serialized theo class chặn clone quote của cùng product/package/store thành backup giả.

## G. Các quyết định giữ draft/configurable

- Không có numeric freshness thresholds, outlier policy, fragility weights, default calibration factors hoặc sample thresholds.
- Chưa có multi-source evidence normalization/eligibility, hierarchy/shrinkage hoặc reference calibration resolver. PriceEvidenceAssessmentDraft là input hình thức cho policy tương lai, chưa có evaluation engine/persistence riêng.
- M1.1 chỉ mass AP_G. COUNT/ml cần primitive conversion evidence và contract riêng trước khi hỗ trợ; không có package→gram conversion magic.
- Accepted products được liệt kê tường minh qua mapping. Chưa có product-family taxonomy/resolver.
- Không có retailer ingestion/scraper/live availability, shopping/checkout workflow, physical ledger, recipe persistence, planner, validator, AI hoặc final scoring.
- M1.2 được phép phát triển Recipe/Preparation theo canonical ownership; contract draft ở đây không cấp quyền activation hoặc chứng nhận toàn bộ M0/M1.

Không phát hiện contradiction cần superseding ADR. Các lựa chọn trên cụ thể hóa ADR-006 và giữ nguyên INV-001..030.
