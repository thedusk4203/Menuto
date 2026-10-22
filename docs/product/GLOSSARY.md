# Thuật ngữ Menuto V1.3

Nghĩa nghiệp vụ theo spec V1.3 và ADR-001..011. Thuật ngữ không phải bằng chứng đã có implementation.

## Ngôn ngữ canonical

**Household**:
Chủ sở hữu tài nguyên chung như inventory, ngân sách, kế hoạch và mua sắm.

**HouseholdMember**:
Người ăn, có thông tin sinh lý, dị ứng/diet và sở thích riêng.

**Membership**:
Quan hệ người dùng với household và quyền tham gia. Trong foundation, đây là nơi duy nhất lưu liên kết `user_id` → `member_id` (tùy chọn); HouseholdMember không chứa user_id.

**Tracked member**:
Member duy nhất được V1 bảo đảm mục tiêu dinh dưỡng cá nhân.

**Shared diner**:
Người cùng ăn làm thay đổi nhu cầu và hard compatibility, không được V1 bảo đảm macro cá nhân.

**MealParticipants**:
Danh sách member, portion factor và nutrition role cho một bữa.

**Portion factor**:
Ước lượng sức ăn; không tự là tỷ lệ nutrition target của mọi món.

**ConsumptionDemand**:
Nhu cầu ăn ở một bữa/thời điểm.

**CookingBatch / BatchAllocation**:
Lượng thực phẩm được nấu một lần và phân bổ cho các nhu cầu ăn; khác attendance.

**Ingredient**:
Danh tính nguyên liệu chuẩn hóa.

**RetailProduct**:
Sản phẩm bán lẻ cụ thể, không đồng nghĩa ingredient.

**Package / Offer / PriceObservation**:
Quy cách bán, đề nghị bán và bằng chứng giá/availability ở thời điểm quan sát.

**ProcurementClass**:
Nhóm cách mua tương đương hợp lý, có granularity và bằng chứng thay thế.

**PlanningPriceQuote**:
Giá dùng lập kế hoạch đã xử lý evidence/policy, không phải checkout guarantee.

**AP → EP**:
Chuyển lượng mua về sang phần nguyên liệu sống sử dụng được qua edible yield thuộc Product→Ingredient mapping của Retail.

**IngredientProductMap**:
Bằng chứng có phiên bản nối một retail product với ingredient và edible yield AP→EP cụ thể. Review và nguồn của mapping phải được giữ khi chuyển thành tài sản AP của household.

**RetailPackage**:
Cách mua một phiên bản product: pack cố định, pack có cân nặng biến thiên, hoặc hàng cân rời theo minimum/step. Package không tự là phép đổi count/ml sang gram.

**ReferencePriceBook**:
Nguồn giá proxy có phiên bản, dùng fallback khi thiếu evidence phù hợp. Reference baseline không phải giá hoặc bằng chứng còn hàng của retailer.

**RetailPriceCalibration**:
Bằng chứng điều chỉnh giá theo retailer, store/region và category, có phương pháp và phiên bản riêng. Mức tin cậy dạng LOW/MEDIUM/HIGH không tự là xác suất.

**Primary / Backup procurement option**:
Đường mua được ưu tiên và những đường mua thay thế trong procurement class. Quote lại cùng product/package/store không tạo thêm backup coverage.

**Cooking yield**:
Thay đổi lượng do phương pháp/quá trình nấu, thuộc Recipe/Preparation; khác edible yield.

**Recipe / RecipeVersion**:
Công thức và phiên bản nội dung có thể truy vết.

**GroundedRecipeVariant**:
Biến thể đã resolve từ authored rules với bindings/quantities/nutrition bất biến.

**DishCandidate**:
Lựa chọn đã chuẩn bị cho một vai trò/bữa trong planner.

**NutritionPolicy**:
Guideline/goal/comfort/temporal rules có version cho tracked member.

**NutritionPrecision**:
Sở thích về độ sát dinh dưỡng; không được làm yếu physiological guardrails.

**CostPreference**:
Mức ưu tiên tiết kiệm được người dùng khai báo.

**BudgetConstraint**:
Hợp đồng ngân sách SPEND_LIMIT, TARGET hoặc NONE.

**BudgetPressure**:
Chỉ số áp lực ngân sách do hệ thống suy ra; không phải sở thích.

**SPEND_LIMIT**:
Chỉ gắn hard-feasible sau khi vượt qua required stress scenarios trong cap.

**TARGET**:
Mục tiêu chi tiêu mềm, có penalty/tolerance; khác hard spending cap.

**InventoryLot**:
Lô tồn kho có ownership, lượng, thời gian dùng được, expiry/storage và confidence.

**Inventory projection**:
Dự kiến lượng tồn, chưa phải confirmed inventory truth.

**Hard constraint**:
Điều kiện bắt buộc trong policy/request hiện tại.

**Soft preference**:
Mục tiêu có thể cân nhắc khi tối ưu; không thay quyền của hard constraints.

**Verified relaxation**:
Phương án nới điều kiện đã được kiểm chứng, gắn nhãn riêng và cần chấp nhận trước activation.

**ActivePlan**:
Kế hoạch đang hoạt động cho một horizon, giữ plan_id ổn định qua các lần sửa future intent.

**PlanRevisionSnapshot / PlanRevisionHistory**:
Bản khuyến nghị bất biến tại một revision và lịch sử những thay đổi của khuyến nghị; khác sự kiện thực tế.

**ExecutionLedger**:
Lịch sử evidence về điều đã xảy ra và các compensating entries; không phải lịch sử planner đổi ý.

**ConfirmedState**:
Trạng thái thực tế chỉ gồm facts có bằng chứng xác nhận.

**OperationalState**:
Confirmed facts cộng các giả định vận hành có thể đảo ngược phục vụ hoạt động hiện tại.

**PlanningState**:
Ảnh trạng thái đã resolve/reconcile dùng làm đầu vào cho lần lập kế hoạch.

**AUTOPILOT_ASSUMED**:
Giả định vận hành provisional dựa trên lịch/điều kiện, không phải confirmed consumption hoặc durable preference evidence.

**AssumptionDebt**:
Mức chưa chắc chắn tích lũy từ các giả định chưa được xác nhận hoặc reconcile.

**PreparedFoodLot**:
Tài sản thực phẩm đã chuẩn bị/nấu thuộc household, được theo dõi theo servings và thời hạn dùng.

**CookingBatchExecution**:
Biến đổi vật lý từ raw inventory sang prepared food; nấu xong không đồng nghĩa đã ăn.

**Measurement basis**:
Cơ sở diễn giải lượng: AP_G, EP_RAW_G, COOKED_G, SERVING, money hoặc discrete count; không tự hoán đổi khi thiếu conversion/provenance.

**ValidationSubjectSnapshot**:
Tập primitive facts, root contracts và policy/scenario/revision snapshots bất biến được xác minh như một subject có danh tính/hash.

**PRECOMMIT_VALIDATION**:
Kiểm chứng proposed intent trước activation/revision; report phải khớp subject và revision hiện hành.

**POSTFACT_VALIDATION**:
Kiểm chứng mang tính chẩn đoán reality đã xảy ra; không từ chối ghi nhận sự thật.

**HorizonBridgeResolver**:
Phép chiếu chronological commitments đến đầu horizon mới, tạo opening assets và provisional recent exposure không double-count.

**MemberBehaviorProfile**:
Sở thích và learned evidence thuộc từng member, giữ taste và context/exposure thành các chiều riêng.

**TasteAffinity**:
Mức ưa thích món/đặc tính ẩm thực; không bị suy ra chỉ từ nấu thành công hoặc gặp khó khi mua/nấu.

**KitchenContextFit**:
Mức phù hợp với thời gian, thiết bị và độ phức tạp của hoàn cảnh nấu.

**RecentExposureModel**:
Lịch sử/phép chiếu mức gặp lại món và đặc tính qua các horizon, phân biệt provisional và confirmed exposure.

**EvidenceClass**:
Phân loại DIRECT, CONTEXTUAL, INFERRED hoặc PASSIVE để diễn giải mức chứng cứ hành vi.

**FORCED_CONFLICT_RESOLUTION**:
Ngữ cảnh chọn phương án do ràng buộc ép buộc; bị cách ly khỏi voluntary taste/context learning nếu không có direct preference signal riêng.

## Primitives đã triển khai và draft handoffs

**CalculatedQuantity / CalculationDecimal**:
Lượng dùng trong phép tính chính xác, giới hạn kỹ thuật 72 chữ số/36 chữ số thập phân; không mang scale của database vào chuỗi yield.

**Quantity / StoredQuantity / PersistedDecimal**:
Lượng nguồn/lưu trữ NUMERIC(18,6). Hai tên Quantity và StoredQuantity cùng một contract. Giá trị vượt giới hạn bị từ chối, không tự làm tròn.

**QuantizationPolicy / QuantizationResult**:
Chính sách có version do caller chọn rõ FLOOR, CEILING hoặc HALF_EVEN tại ranh giới lưu trữ. Kết quả giữ original_amount, stored và residual có dấu (= original − stored); đây chưa phải chính sách bảo toàn inventory hay nutrition tolerance.

**Provenance**:
Nguồn gồm source_system nội bộ, external_record_id và source_version giữ định danh bên ngoài dạng opaque, observed_at có timezone, tùy chọn source_uri HTTP(S) không credentials và content_hash SHA-256. Không ép locator bên ngoài theo regex Identifier nội bộ.

**MaterialAssetFact (draft)**:
Union phân biệt RAW_INGREDIENT (inventory_lot_id + ingredient_id, lượng AP/EP raw/count) và PREPARED_FOOD (prepared_food_lot_id + cooking_batch_id + recipe_version_id, lượng SERVING gắn serving_definition_ref). Đây là đầu vào nguồn draft, chưa phải conservation/replay validator.
