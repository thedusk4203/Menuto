# Ranh giới domain Menuto

Nguồn chuẩn: đặc tả V1, mục 5, 8–13 và 15–17. Tài liệu này tóm tắt trách nhiệm để chuẩn bị triển khai; chưa tạo model, bảng dữ liệu hoặc API.

## Mười hai domain

Domain là vùng trách nhiệm nghiệp vụ. Chúng nằm trong một backend chia module (modular monolith); không phải 12 dịch vụ độc lập.

| Domain | Entity theo đặc tả | Trách nhiệm |
| --- | --- | --- |
| Identity | User, Session, Consent | Tài khoản, phiên đăng nhập, đồng ý và vòng đời tài khoản |
| Household | Household, Member, ServingProfile | Quy mô hộ, người ăn và nhu cầu khẩu phần |
| Nutrition | NutritionProfile, NutritionTarget, GoalPreset | Mục tiêu năng lượng/dinh dưỡng và giới hạn an toàn |
| Catalog | Ingredient, FoodGroup, UnitConversion | Danh tính nguyên liệu, nhóm thực phẩm và quy đổi đơn vị |
| Recipes | Recipe, RecipeVersion, RecipeIngredient, RecipeTag | Công thức, phiên bản, nguyên liệu và công sức nấu |
| Retail | Retailer, StoreRegion, Product, Package, PriceObservation | Cửa hàng, sản phẩm, quy cách, giá và khả năng mua |
| Inventory | InventoryLot, InventoryEvent, Reservation | Tồn kho theo lô, hạn dùng, sự kiện và giữ chỗ |
| Planning | PlanRequest, Plan, PlanDay, PlanMeal, PlannerRun | Yêu cầu, tối ưu, xác minh, chất lượng và nguồn dữ liệu kế hoạch |
| Shopping | ShoppingList, ShoppingItem, PurchaseEvent | Danh sách mua, package và chi phí dự kiến/thực tế |
| Execution | MealExecution, RecipeExecution | Nấu, bỏ qua, đổi món và khẩu phần thực hiện |
| Preferences | PreferenceSignal, PreferenceProfile | Sở thích khai báo và tín hiệu hành vi |
| Assistant | Conversation, IntentParse, Explanation | Hiểu ý định và giải thích trên dữ liệu được xác minh |

Tên module vật lý và hợp đồng giao tiếp sẽ được chốt ở ADR-001 khi tạo backend; khung hiện tại chưa cấp phát code theo domain.

## Những khái niệm không được nhập làm một

- **Ingredient và Retail Product:** “ức gà” là nguyên liệu; “ức gà khay 500g của một nhãn hàng” là sản phẩm/quy cách bán lẻ.
- **Recipe và Dish Candidate:** công thức mô tả cách nấu; candidate là lựa chọn đã xử lý khẩu phần, dinh dưỡng, tồn kho và khả năng mua để đưa vào planner.
- **Planned cost và Actual cost:** chi phí dự kiến dựa trên snapshot giá; chi phí thực dựa trên giao dịch mua đã ghi nhận.
- **Inventory và Shopping carryover:** lượng còn lại dự kiến sau mua chưa tự trở thành tồn kho; phải có xác nhận mua/thực hiện.
- **Preference và Constraint:** thích món cay là tín hiệu mềm; tránh thành phần gây dị ứng là ràng buộc cứng.

## Nguyên tắc đã có trong đặc tả

- V1 dùng modular monolith, PostgreSQL và đường xử lý CP-SAT; chỉ thêm queue/worker khi cần xử lý bất đồng bộ.
- AI phân tích ý định và giải thích, không quyết định cuối về dị ứng, ngân sách, dinh dưỡng hoặc tính khả thi.
- Ràng buộc cứng/mềm phải rõ và có nguồn gốc. Thay đổi ràng buộc phải được trình bày, lưu lại và được người dùng chấp nhận khi áp dụng cho yêu cầu họ đã khai báo.
- Validator kiểm tra đầu ra độc lập với optimizer; không dùng lời giải thích AI để chứng minh kế hoạch đúng.
- Recipe, policy, target và snapshot dữ liệu/giá quan trọng phải truy vết được theo phiên bản.
- Timeout, thiếu dữ liệu và chứng minh vô nghiệm là các kết quả khác nhau; không đánh đồng chúng.

## Việc còn phải quyết định

Danh mục [ADR](../adr/README.md) quản lý các quyết định còn mở: giao tiếp và giao dịch giữa module, chính sách ràng buộc chi tiết, cấu trúc snapshot/ledger, ngưỡng giá cũ và ngưỡng benchmark. Chưa có schema hoặc hợp đồng tích hợp được duyệt từ tài liệu tóm tắt này.
