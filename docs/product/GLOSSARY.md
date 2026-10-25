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
Phiên bản sản phẩm bán lẻ cụ thể. V1 gắn mỗi phiên bản với một canonical ingredient cho procurement; composite/mixed products chưa được hỗ trợ.

**Package / Offer / PriceObservation**:
Quy cách bán, đề nghị bán và bằng chứng giá/availability ở thời điểm quan sát.

**ProcurementClass**:
Nhóm cách mua tương đương hợp lý, có granularity và bằng chứng thay thế.

**PlanningPriceQuote**:
Cặp tiền và lượng AP tham chiếu dùng lập kế hoạch, có nguồn và policy rõ; chưa phải chi phí mua package hoặc checkout guarantee.

**AP → EP**:
Chuyển lượng mua về sang phần nguyên liệu sống sử dụng được qua edible yield thuộc Product→Ingredient mapping của Retail.

**IngredientProductMap**:
Bằng chứng có phiên bản nối một retail product với ingredient và edible yield AP→EP cụ thể. Review và nguồn của mapping phải được giữ khi chuyển thành tài sản AP của household.

**RetailPackage**:
Cách mua một phiên bản product: pack cố định, pack có cân nặng biến thiên, hoặc hàng cân rời theo minimum/step. Package không tự là phép đổi count/ml sang gram.

**ReferencePriceBook**:
Nguồn giá proxy có phiên bản, dùng fallback khi thiếu evidence phù hợp. Reference baseline không phải giá hoặc bằng chứng còn hàng của retailer.

**RetailPriceCalibration**:
Bằng chứng điều chỉnh reference baseline theo retailer, store/region và category khi thiếu direct retail evidence. Không nhân hệ số này vào giá retailer đã quan sát; mức tin cậy dạng LOW/MEDIUM/HIGH không tự là xác suất.

**RetailerStatusFact**:
Bằng chứng trạng thái ACTIVE/INACTIVE của cùng một retailer tại thời điểm hiệu lực; thay trạng thái không tạo retailer identity mới.

**Source coverage**:
Số đường mua, retailer và provider được thể hiện bởi direct observations chưa UNAVAILABLE. Nhiều giá reference không tự tạo thêm evidence rằng retailer có hàng.

**Primary / Backup procurement option**:
Đường mua được ưu tiên và những đường mua thay thế trong procurement class. Quote lại cùng product/package/store không tạo thêm backup coverage.

**Cooking yield**:
Thay đổi lượng do phương pháp/quá trình nấu, thuộc Recipe/Preparation; khác edible yield.

**Recipe**:
Danh tính ổn định của một món và phương pháp nấu. Đổi phương pháp làm thay đổi món tạo Recipe khác.

**RecipeVersion**:
Phiên bản tác giả bất biến của Recipe, gồm quy trình, serving, nguyên liệu, phép biến đổi và các giới hạn linh hoạt. Sửa nội dung tạo phiên bản mới.

**Recipe ingredient slot**:
Vai trò nguyên liệu bắt buộc trong một phiên bản công thức, có identity, lượng và measurement basis rõ ràng.

**Portion tier**:
Quy mô sản xuất được tác giả khai báo với số serving và lượng nguyên liệu cụ thể. Số serving không được suy ra từ tổng gram.

**Scaling policy**:
Quy tắc thay đổi lượng nguyên liệu khi chọn quy mô sản xuất khác; có thể tuyến tính, dưới tuyến tính, cố định, rời rạc hoặc theo khẩu vị trong giới hạn đã khai báo.

**Quantity adjustment envelope**:
Giới hạn điều chỉnh nhỏ cho nguyên liệu sau khi chọn quy mô và substitution. Điều chỉnh này thay thành phần trên mỗi serving, không tự đổi serving count.

**Authored substitution rule**:
Quyền thay một ingredient slot trong đúng RecipeVersion bằng nguyên liệu và tỷ lệ đã khai báo. Không phải quan hệ thay thế toàn cục giữa các ingredient.

**GroundedRecipeVariant**:
Biến thể đã resolve từ authored rules với bindings/quantities/nutrition bất biến.

**Culinary grounded input draft**:
Bản gắn lựa chọn culinary vào RecipeVersion, tier và lượng cụ thể để tiếp tục resolve. Chưa phải GroundedRecipeVariant hoàn chỉnh khi thiếu nutrition, safety và retail/inventory resolution.

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


**Physical InventoryLot**:
Một tài sản vật chất đã được xác nhận của household. Lot sống, component chín và món đã nấu
có danh tính riêng; dự kiến mua và giả định vận hành không phải stock.

**InventoryMovement**:
Bằng chứng bất biến về vật chất vào/ra lot hoặc xác nhận hết hạn. Sửa sai giữ sự kiện cũ và
thêm sự kiện bù; thời gian trôi qua không chứng minh đã tiêu thụ.

**InventoryReservation / release**:
Ý định giữ một phần vật chất cho mục đích cụ thể và bằng chứng thôi giữ phần đó.
Giữ chỗ không tiêu thụ hoặc làm biến mất vật chất.

**Physical remaining / allocatable**:
Physical remaining là lượng vật chất còn được ghi nhận, kể cả phần đã hết hạn.
Allocatable là phần còn sử dụng được sau khi trừ giữ chỗ; lot không còn usable có allocatable bằng không.

**Ledger sequence**:
Số thứ tự xác định giữa các sự kiện cùng thời điểm và cùng phase vật chất; không lấy thứ tự từ UUID.

**Observation confidence**:
Mức chắc chắn của quan sát số lượng, tách biệt lifecycle và nguồn xác nhận của sự kiện vật chất.


**Current Working Graph**:
Khuyến nghị hiện hành của một plan, được xác định bởi head đang chọn. Thay head qua một
revision được chấp nhận làm đổi future intent; lịch sử revision và physical facts không đổi.

**PlanProposalDraft**:
Đề xuất intent chưa được activation/revision gate chấp nhận. Lịch sử đề xuất không phải
PlanRevision0; proposal không chứng minh feasibility hoặc tạo confirmed reality.

**ShoppingRequirement**:
Nhu cầu mua có lượng và basis rõ theo một phiên bản intent. Không tự là bằng chứng đã mua.

**PurchaseFulfillment**:
Bằng chứng mua thực tế với actual quantity và actual price, có thể đáp ứng một phần nhu cầu.
Thay khuyến nghị về sau không xóa purchase hoặc tài sản household đã nhận.

**PlannedCookingBatch**:
Ý định sản xuất với recipe version, composition và planned servings rõ. Khác batch thực sự
đã nấu và khác prepared food đã thuộc household.

**Materialization boundary**:
Ranh giới một phần intent đã có confirmed execution/physical evidence. Nó giữ liên kết với
khuyến nghị nguồn mà không biến thời gian trôi qua thành bằng chứng thực thi.


**Proposal generation**:
Thứ tự các đề xuất intent đã lưu, kể cả đề xuất chưa được chấp nhận. Khác số revision
vận hành đã được chấp nhận.
_Avoid_: Draft revision0

**Observed acquisition coverage (draft)**:
Lượng nhu cầu có thể đối chiếu với acquisition đã được xác nhận, cùng ingredient và
measurement identity. Chưa chứng minh giá mua thực tế hoặc toàn bộ PurchaseFulfillment.

**Accepted revision head**:
Phiên bản khuyến nghị được chấp nhận hiện hành của cùng một plan. Đổi head không đổi
quyền sở hữu hay lịch sử vật chất của household.


**ShoppingDemandContribution**:
Phần nhu cầu định lượng đóng góp vào một ShoppingRequirement, thuộc về đúng một meal
hoặc planned batch. Các phần đang có hiệu lực giữ đúng tổng lượng và measurement identity.

**Advice temporal anchor**:
Thời điểm advice dự kiến diễn ra: giờ meal, giờ planned batch hoặc hạn shopping. Khác
thời điểm có bằng chứng xác nhận vật chất đã được mua, nấu hoặc tiêu thụ.


**ValidationSubject foundation**:
Bộ facts bất biến và self-contained để kiểm độc lập các phần đã có nguồn, kèm policy và
identity của đầu vào. Phạm vi foundation còn thiếu capability nên không cấp quyền activation.

**Validation coverage policy**:
Định nghĩa có phiên bản về phạm vi kiểm định đang hỗ trợ và cách từ chối facts quan trọng
chưa giải được. Khác policy dinh dưỡng/goal do NutritionPolicyEngine tổng hợp.

**POSTFACT diagnostic**:
Kết quả giải thích lỗi hoặc mâu thuẫn của thực tế đã được ghi nhận. Không tự sửa/xóa lịch
sử vật chất, không tự tạo plan revision hoặc repair.


### Planned Culinary Binding

Exact authored culinary choices for one planned cooking batch: selected ingredients, quantities,
adjustments and preparation paths. It records what is intended, not what was cooked or consumed.

### Culinary Semantic Signature

Identity of unchanged culinary intent across proposal copies. A change of culinary facts changes
this signature; merely recording the same intent in a new proposal does not.

**Culinary Candidate**:
Một khả năng culinary cụ thể từ RecipeVersion đã được tác giả cho phép, có ingredient,
lượng và serving tier xác định. Chưa phải DishCandidate hoàn chỉnh khi thiếu grounding downstream.
_Avoid_: safe meal, fully grounded candidate

**Culinary Demand**:
Yêu cầu chọn khả năng culinary theo serving tier, ingredient mong muốn, rule set và exclusions.
Đây là đầu vào lựa chọn, không tự chứng minh giá, inventory hay an toàn cho thành viên.

**Generation Trigger**:
Lý do cơ học khiến một khả năng được xét, như default, ingredient target hoặc rule set được yêu cầu.
Khác lý do đã được chứng minh bằng bằng chứng như price advantage hay expiry rescue.

**Grounded Dish Candidate**:
Một khả năng culinary kèm đủ primitive facts được hỗ trợ cho đầu vào shortlist: composition,
nguồn dinh dưỡng, các đường procurement/stock và context thành viên. Chưa khẳng định global feasibility hay activation.

**Procurement Supply Path**:
Một đường cung ứng nguyên liệu với package/granularity, edible yield và price evidence rõ ràng.
Khác số lượng đã mua, chi phí checkout hoặc stock đã sở hữu.

**Ingredient Input Composition**:
Lượng chất dinh dưỡng tính từ ingredient quantities và nutrition references tương thích basis.
Không tự khẳng định nutrient retention sau nấu hay lượng thực tế một thành viên đã ăn.

**Supply Coverage Frontier**:
Tập ứng viên giữ mọi lựa chọn cung ứng khác biệt; chỉ bỏ một ứng viên khi ứng viên cùng
culinary/context giữ nguyên toàn bộ bằng chứng của nó và có thêm đường cung ứng.
_Avoid_: cheapest dishes, guaranteed feasible shortlist

**Explicit Preference Declaration**:
Phát biểu được ghi rõ cho một HouseholdMember về việc thích, không thích hoặc trung lập với
một đối tượng cụ thể; khác preference suy ra từ hành vi hay hard safety restriction.

**Preference Retraction**:
Rút lại phát biểu sở thích đang có, vẫn giữ lịch sử phát biểu và việc rút lại.
Không đồng nghĩa với việc thành viên đã tuyên bố trung lập.

**EvidenceStrength**:
Mức bằng chứng của affinity trong MemberBehaviorProfile được suy ra theo policy/version và
evidence provenance. Không phải trường do caller gắn lên raw explicit preference declaration.


**Proposal Exposure Preview**:
Dấu vết tạm theo từng thành viên và món ăn được đề xuất trong một meal intent; không chứng minh
commitment đã được chấp nhận, món đã nấu hay thành viên đã ăn.
_Avoid_: confirmed consumption, taste evidence

**Proposal-local Recipe Cooldown Assessment**:
Kiểm tra trong một proposal xem cùng thành viên có được đề xuất cùng Recipe ID ở bữa khác
trước bữa mục tiêu, trong khoảng thời gian do policy có phiên bản quy định hay không.
Không tính chính bữa mục tiêu. Không có match chỉ nói về proposal đang xét, không chứng minh
chưa từng ăn, an toàn về cooldown toàn cục, novelty hay sở thích.

**Proposal-local Decay Trace (AS_OF_CAPTURE)**:
Diễn giải từng cooldown witness theo policy age bands có phiên bản tại thời điểm capture.
Witness là bằng chứng nguồn; tuổi là primitive được tính; retention multiplier là diễn giải
policy bằng rational chính xác, không phải confidence/probability/EvidenceStrength hay sở thích.
Hệ số0 vẫn giữ witness. Trace là diagnostic, chưa có RepeatPenalty hay tổng điểm utility.


**Proposal-local RepeatPenalty**:
Mức penalty theo policy cho các lần cùng thành viên được đề xuất cùng Recipe ID trong một
proposal và lookback đang xét. Đây là một dimension riêng, không phải sở thích hay utility.
Không có witness thì chưa có giá trị; witness có retention0 vẫn cho giá trị0 kèm nguồn chứng cứ.

**Policy Repeat Penalty Units**:
Đơn vị diễn giải do policy RepeatPenalty định nghĩa, dùng rational chính xác và có thể lớn hơn1.
Không phải xác suất, confidence, EvidenceStrength, tiền hay lượng vật chất; các policy khác nhau
không mặc nhiên cho giá trị có thể so sánh trực tiếp.

**Culinary Feature Assignment**:
Phát biểu đã review rằng một culinary source trong phạm vi cụ thể mang một term METHOD,
FLAVOR hoặc MAIN_PROTEIN. Định nghĩa term và việc gán term là hai loại sự thật khác nhau.

**Culinary Feature Applicability**:
Phạm vi culinary đã được reviewer xét cho một loại feature. METHOD gắn với cooking context của
RecipeVersion và giữ nguyên qua các variant hợp lệ. FLAVOR/MAIN_PROTEIN có thể xét lựa chọn
ingredient, preparation, tier và quantity-adjustment theo path được nêu rõ. Không đồng nghĩa với
exact candidate identity.

**Culinary Feature Capture / Term Query**:
Capture lấy các assignment dương, coverage và nguồn chứng cứ theo dimensions được yêu cầu,
không cần biết trước term IDs. Term query là câu hỏi riêng chạy trên snapshot đã capture;
term ngoài manifest đã capture vẫn UNRESOLVED, không tự trở thành REVIEWED_ABSENT.

**Feature Coverage**:
Phát biểu phạm vi review đã bao phủ đầy đủ hay một phần một tập term có danh tính rõ ràng.
Không có assignment chỉ chứng minh feature vắng mặt khi có coverage đầy đủ cho term đang hỏi.

**Contextual Main Protein**:
Protein category được reviewer chỉ định là chính cho một culinary path, có ingredient-slot support.
Không tự suy ra từ protein grams, ingredient order, lượng nguyên liệu hay ingredient association.


**Ingredient Protein Association**:
Phát biểu đã review rằng một ingredient gắn với một protein term cụ thể. Đây là nguồn chứng cứ
có thể tái dùng; chưa đủ để kết luận protein đó là chính trong một món ăn.

**Stale Main-Protein Support**:
Một designation MAIN_PROTEIN còn giữ chứng cứ đã pin, nhưng association nguồn đã được thay thế
hoặc rút lại. Capture mới trả về chưa xác định cho tới khi được review lại; lịch sử cũ vẫn giữ nguyên.
