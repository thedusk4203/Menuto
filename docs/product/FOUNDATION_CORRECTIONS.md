# Sáu sửa đổi foundation sau review

Ngày: 2026-10-22. Chuẩn vẫn là V1.3, 30 invariants và 11 ADR đã chấp nhận. Đây là sửa implementation để khớp baseline; chưa mở rộng thành Retail, Recipe, Inventory hoặc Independent Validator.

| Vấn đề | Thay đổi | Kiểm chứng |
| --- | --- | --- |
| Phép nhân yield hợp lệ bị scale 6 chặn | CalculatedQuantity 72/36 tách Quantity/StoredQuantity NUMERIC(18,6). Nhân/cộng dùng exact Decimal với context riêng và trap rounding; vượt giới hạn thì từ chối | Chuỗi 123.456789 × 0.876543 × 1.234567 = 133.598895312768560109, kể cả caller đặt precision 3 |
| Yield persistence sai owner | Bỏ catalog UnitConversion và bảng generic unit_conversions; giữ neutral YieldConversion để tính | Metadata drift check và kiểm bảng absent; migration từ chối xóa bảng có rows |
| Hai nguồn account/member | Chỉ Membership giữ user_id + optional member_id; bỏ HouseholdMember.user_id | DB uniqueness, composite household FK; safe backfill, reject conflicting/orphan/ambiguous legacy links |
| Exclusion uniqueness theo nhãn | Partial unique ingredient_id cho EXCLUDED_INGREDIENT; kind/code cho ALLERGEN và DIET_RULE | Cùng ingredient/khác nhãn bị chặn, khác ingredient/cùng nhãn được phép |
| Draft material chỉ có raw ingredient | MaterialAssetFact là discriminated union raw/prepared; prepared phải có serving definition, lot/batch/recipe version | Roundtrip cả hai loại, sai basis/identity/tag/household và duplicate physical asset bị chặn |
| Provenance locator quá hẹp | source_system tách external_record_id/version; thêm optional source_uri/content_hash | Unicode/path/opaque locator, dài >100 ký tự, provider identity và duplicate-source checks |

## Precision và ranh giới lưu trữ

Không làm tròn sau mỗi bước yield. Caller phải gọi `CalculatedQuantity.to_stored(QuantizationPolicy(...))` khi cần giá trị lưu trữ; chọn rõ version và FLOOR/CEILING/HALF_EVEN. Kết quả trả cả original_amount, stored và signed residual (= original − stored). Không có rounding direction mặc định. ORM bind guard từ chối scale quá 6 trước khi PostgreSQL tự ép kiểu; raw SQL client vẫn phải tuân thủ ranh giới này vì NUMERIC có thể làm tròn ngay khi cast.

Giới hạn 72/36, 18/6 và context tính toán 160 digits là giới hạn kỹ thuật, không phải clinical thresholds. Chưa triển khai phép chia/phân bổ batch, residual ledger hoặc tolerance policy của Inventory/Validator; các lát sau phải định nghĩa conservation và nơi lưu rounding evidence. QuantizationResult chưa tự được persist vào bảng riêng.

## Yield ownership

Edible yield AP→EP sẽ nằm trên Product→Ingredient mapping của Retail. Cooking yield EP→Cooked sẽ thuộc RecipeVersion/PreparationTransformation. Chưa tạo các owner tables đó trong đợt này. Neutral context_ref của YieldConversion chỉ là nguồn tính toán; không thay FK hoặc canonical persistence tương lai.

## Tương thích contracts

Bundle domain schema chuyển sang `urn:menuto:domain:foundation:2`; tất cả planner/validation/mutation drafts chuyển từ `m0-draft.1` sang `m0-draft.2`. MaterialFact cũ được thay bằng typed MaterialAssetFact; Provenance bỏ source_ref, yêu cầu source_system + external_record_id. Không âm thầm nhận payload .1 hay tự đoán provider. Health/OpenAPI/generated HTTP client không đổi. Các cờ activation_ready, validation_ready và activation_authorized vẫn chỉ được false; HORIZON_BRIDGE và các primitive contracts còn thiếu vẫn được khai báo rõ.

## Migration 0001 → 0002

Giữ nguyên DDL đã phát hành ở 0001. Migration 0002 chạy trong transaction PostgreSQL và lock các bảng liên quan trước preflight:

- Nếu bảng generic yield có dữ liệu: dừng; cần export và migration theo owner Retail/Recipe cụ thể trước, không xóa evidence.
- Nếu account/member trùng, orphan hoặc mâu thuẫn: dừng; cần xác minh mapping, không tự gán quyền hay người ăn.
- Nếu một member có nhiều nhãn loại trừ cho cùng ingredient: dừng; cần giải quyết canonical identity có chủ đích.
- Mapping cũ hợp lệ với member_id còn trống được backfill. source_ref giữ nguyên thành external_record_id; source_system nhận nhãn migration `legacy.m0`, không giả định đó là provider thật. Không để default này cho insert mới.

Downgrade 0002→0001 chỉ thực hiện khi không mất thông tin: dừng nếu có modern provenance không biểu diễn được bằng schema cũ hoặc safety identities xung đột với unique code cũ. Khi hợp lệ, khôi phục field/mapping cũ và bảng yield rỗng. Đây là rollback kỹ thuật đã test trên database tạm, không phải lệnh nên tự chạy với dữ liệu người dùng.

Trước khi migrate database ứng dụng: backup/restore theo quy trình vận hành, kiểm tra preflight và chuẩn bị resolution cho dữ liệu cũ. Tests chỉ tạo/xóa database ngẫu nhiên riêng trên loopback; không provision hoặc migrate database ứng dụng trong đợt sửa này.

[Bằng chứng chạy kiểm tra](M0_M1_FOUNDATION_EVIDENCE.md) ghi kết quả và giới hạn thực tế.
