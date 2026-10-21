# Thuật ngữ Menuto V1.2

Nguồn chuẩn: Development Spec V1.2 §8–14 và ADR-001..008. Đây là nghĩa nghiệp vụ; không phải bằng chứng những chức năng đã triển khai.

| Thuật ngữ | Nghĩa |
| --- | --- |
| Household | Chủ sở hữu tài nguyên chung như inventory, ngân sách, kế hoạch và mua sắm |
| HouseholdMember | Người ăn, có thông tin sinh lý, dị ứng/diet và sở thích riêng |
| Membership | Quan hệ người dùng với household và quyền tham gia |
| Tracked member | Member duy nhất được V1 bảo đảm mục tiêu dinh dưỡng cá nhân |
| Shared diner | Người cùng ăn làm thay đổi nhu cầu và hard compatibility, không được V1 bảo đảm macro cá nhân |
| MealParticipants | Danh sách member, portion factor và nutrition role cho một bữa |
| Portion factor | Ước lượng sức ăn; không tự là tỷ lệ nutrition target của mọi món |
| ConsumptionDemand | Nhu cầu ăn ở một bữa/thời điểm |
| CookingBatch / BatchAllocation | Lượng thực phẩm được nấu một lần và phân bổ cho các nhu cầu ăn; khác attendance |
| Ingredient | Danh tính nguyên liệu chuẩn hóa |
| RetailProduct | Sản phẩm bán lẻ cụ thể, không đồng nghĩa ingredient |
| Package / Offer / PriceObservation | Quy cách bán, đề nghị bán và bằng chứng giá/availability ở thời điểm quan sát |
| ProcurementClass | Nhóm cách mua tương đương hợp lý, có granularity và bằng chứng thay thế |
| PlanningPriceQuote | Giá dùng lập kế hoạch đã xử lý evidence/policy, không phải checkout guarantee |
| AP → EP | Chuyển lượng mua về sang phần nguyên liệu sống sử dụng được qua edible yield |
| Cooking yield | Thay đổi lượng do phương pháp/quá trình nấu; khác edible yield |
| Recipe / RecipeVersion | Công thức và phiên bản nội dung có thể truy vết |
| GroundedRecipeVariant | Biến thể đã resolve từ authored rules với bindings/quantities/nutrition bất biến |
| DishCandidate | Lựa chọn đã chuẩn bị cho một vai trò/bữa trong planner |
| NutritionPolicy | Guideline/goal/comfort/temporal rules có version cho tracked member |
| NutritionPrecision | Sở thích về độ sát dinh dưỡng; không được làm yếu physiological guardrails |
| CostPreference | Mức ưu tiên tiết kiệm được người dùng khai báo |
| BudgetConstraint | Hợp đồng ngân sách SPEND_LIMIT, TARGET hoặc NONE |
| BudgetPressure | Chỉ số áp lực ngân sách do hệ thống suy ra; không phải sở thích |
| SPEND_LIMIT | Chỉ gắn hard-feasible sau khi vượt qua required stress scenarios trong cap |
| TARGET | Mục tiêu chi tiêu mềm, có penalty/tolerance; khác hard spending cap |
| InventoryLot | Lô tồn kho có ownership, lượng, thời gian dùng được, expiry/storage và confidence |
| Inventory projection | Dự kiến lượng tồn, chưa phải confirmed inventory truth |
| Hard constraint | Điều kiện bắt buộc trong policy/request hiện tại |
| Soft preference | Mục tiêu có thể cân nhắc khi tối ưu; không thay quyền của hard constraints |
| Verified relaxation | Phương án nới điều kiện đã được kiểm chứng, gắn nhãn riêng và cần chấp nhận trước activation |
| OPTIMAL | Chứng minh optimum trong model/candidate set đang xét; không tự là optimum ngoài thực tế |
| UNKNOWN_TIME_LIMIT | Chưa có kết luận trong thời gian cho phép; không phải proven infeasible |
| Synthetic benchmark | Bài toán tổng hợp để kiểm tra harness/thuật toán nhỏ, không đại diện đầy đủ sản phẩm |
