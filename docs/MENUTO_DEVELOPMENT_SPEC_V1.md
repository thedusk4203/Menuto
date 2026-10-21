# Menuto - Tài liệu phát triển sản phẩm V1.0

**Product Strategy · Architecture · Planner V4 · Data Model · UX · Roadmap**

> **Định nghĩa sản phẩm**
>
> Menuto là nền tảng tối ưu quyết định ăn uống cá nhân/hộ gia đình: kết hợp ngân sách, dinh dưỡng, sở thích, inventory, hạn sử dụng, sản phẩm bán lẻ và khả năng thực hiện để tạo một kế hoạch ăn + mua sắm có thể áp dụng trong đời sống thực.

Nguồn thiết kế: Smart Menu hiện tại + rà soát NeatEat, Eat This Much, Samsung Food, Mentu

Ngày chốt tài liệu: 21/10/2026

> **Tệp Markdown chuẩn:** phù hợp để lưu tại `docs/Menuto_DEVELOPMENT_SPEC_V1.md` trong repository Menuto.

# Mục lục

1. Tóm tắt điều hành
2. Kết luận sau khi rà soát lại Smart Menu
3. Định vị Menuto
4. Người dùng mục tiêu và Jobs-to-be-Done
5. Nguyên tắc thiết kế sản phẩm
6. Scope V1 và Non-goals
7. Information Architecture và user journeys
8. Kiến trúc hệ thống
9. Bounded contexts và domain model
10. Planner V4 - đặc tả thuật toán
11. Feasibility, relaxation và explainability
12. Retail, product và pricing architecture
13. Inventory và food lifecycle
14. Recipe, cooking friction và adherence
15. AI / Menuto Assistant
16. API, backend và frontend architecture
17. Security, privacy và safety
18. Testing, benchmark và observability
19. Metrics và feedback loop
20. Roadmap Public V1 → V1.5 → V2
21. Backlog triển khai ưu tiên
22. Smart Menu → Menuto reuse/migration matrix
23. Definition of Done và launch gate
24. Rủi ro và quyết định kiến trúc
25. Nguồn tham chiếu và ghi chú nghiên cứu

# 1. Tóm tắt điều hành

> **Quyết định chính**
>
> Menuto phải là sản phẩm mới về product architecture và data model. Không fork Smart Menu rồi tiếp tục sửa. Chỉ tái sử dụng các domain concept, thuật toán, test scenario và hạ tầng đã được chứng minh có giá trị.

Smart Menu đã có một lõi kỹ thuật mạnh hơn nhiều ứng dụng meal planner thông thường: CP-SAT, inventory theo lot, expiry/storage, purchase increments, nutrition targets, shopping list, regenerate/swap có revalidation và independent constraint checking. Tuy nhiên nó vẫn mang dấu vết của một đồ án tiến hóa dần: model retail chưa đủ thực tế, CandidateSelector có thể làm mất nghiệm tốt, feasibility có thể false-infeasible trong trường hợp có inventory, UX chưa tối giản theo consumer journey, và product loop dừng quá sớm ở “generate plan”.

Menuto vì vậy không nên cạnh tranh bằng nhãn “AI Meal Planner”. Vị trí phù hợp hơn là một Food Planning & Optimization Platform: user cung cấp ngân sách, mục tiêu, sở thích, đồ đang có và nơi mua; Menuto trả một tuần ăn + mua sắm + sử dụng inventory có thể giải thích, có thể điều chỉnh, và được xác minh bằng constraint engine.

| **Trụ cột**              | **Menuto V1 phải đạt**                                                                                                   |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------|
| Trustworthy optimization | Plan hợp lệ, benchmark được, không false-infeasible đã biết, swap/regenerate vẫn giữ constraint.                          |
| Retail reality           | Ingredient tách khỏi retail product; package, retailer, price observation, freshness và availability là first-class data. |
| Simple UX                | User không cần hiểu solver. Onboarding hỏi budget, household, goal, exclusions, store; advanced settings nằm sau.         |
| Execution loop           | Không chỉ plan. Có Today mode, shopping state, inventory consumption và feedback để biết plan có được thực hiện không.    |
| Explainability           | Mỗi plan phải giải thích budget, nutrition fit, inventory usage, waste/carryover và constraint nào đã được nới.           |
| Learning loop            | Accept/swap/skip/cook/waste/actual-price trở thành signals để cải thiện lần lập kế hoạch sau.                             |

# 2. Kết luận sau khi rà soát lại Smart Menu

## 2.1 Những tài sản kỹ thuật nên kế thừa

| **Tài sản Smart Menu**                       | **Giá trị**    | **Cách dùng trong Menuto**                                                                          |
|----------------------------------------------|----------------|------------------------------------------------------------------------------------------------------|
| CP-SAT procurement-aware optimizer           | Cao            | Giữ triết lý joint optimization; viết Planner V4 contract mới.                                       |
| Inventory lots + reservations                | Cao            | Giữ mô hình ledger theo lot, expiry, storage; đổi schema naming và lifecycle cho rõ.                 |
| Nutrition domain                             | Cao            | Giữ formulas/targets; tách health goal preset khỏi raw macro settings.                               |
| Independent constraint checker               | Rất cao        | Bắt buộc ở Menuto; optimizer không tự chứng minh tính đúng của chính nó.                            |
| Regenerate signature / validated swap        | Cao            | Giữ concept, nâng thành controlled alternatives + explain differences.                               |
| Shopping list + public share                 | Trung bình-cao | Port concept; V1 chưa cần household realtime collaboration.                                          |
| AI provider abstraction / structured parsing | Cao            | Giữ boundary: AI hiểu intent và giải thích, deterministic engine quyết định feasibility/cost/safety. |
| Catalog/admin QA concepts                    | Cao            | Chuyển thành data-quality pipeline cho recipe, nutrition, retail product, price và shelf-life.       |

## 2.2 Những điểm yếu không được copy nguyên trạng

| **Vấn đề**                                  | **Bằng chứng trong Smart Menu**                                                                                      | **Quyết định Menuto**                                                                  |
|---------------------------------------------|----------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| Candidate pruning thiên về cheapest         | Khi có budget, shortlist có thể lấp phần lớn cap bằng món rẻ nhất trước khi preference/nutrition diversity tham gia. | Candidate generation đa tín hiệu + Pareto shortlist + benchmark against reference pool. |
| Dish nutrition score sai abstraction        | Từng dish được so với target của cả meal trong khi lunch/dinner là meal composition nhiều dish.                      | Score ở component/meal level; không dùng whole-meal target cho từng component.          |
| Budget precheck bỏ qua giá trị inventory    | minimum_required_budget dựa trên estimated dish cost, trước khi procurement optimizer dùng inventory.                | Feasibility V2 phải inventory-aware; hard reject chỉ khi lower bound đáng tin cậy.      |
| Nutrition objective chưa normalize          | Calories, gram protein/fat/carb cộng với trọng số trên đơn vị khác nhau.                                             | Dùng normalized deviation / basis points; policy được version hóa và benchmark.         |
| Timeout vs infeasible chưa tách sạch        | Diversity tier có phase time rất ngắn; UNKNOWN có thể dẫn tới relax.                                                 | Explicit solver outcome: PROVEN_INFEASIBLE / TIME_LIMIT / FEASIBLE / OPTIMAL.           |
| Retail source là string                     | price_snapshots có source + price_per_default_unit nhưng chưa có retailer/product/package identity.                  | Retailer / StoreRegion / Product / Package / PriceObservation là entities riêng.        |
| Product flow dừng ở generate/save           | Có result, shopping list, inventory, nhưng execution loop chưa phải core.                                            | Today / Shop / Cook / Consume / Feedback là first-class workflow.                       |
| Quality policy có nguy cơ drift/dead fields | Policy chứa các tham số không phải lúc nào cũng điều khiển solver trực tiếp.                                         | Policy schema có version, tests chứng minh mỗi field tác động objective/constraint.     |

## 2.3 Kết luận kiến trúc

> **Không fork codebase**
>
> Tạo repo Menuto sạch. Port từng capability sau khi đã có contract V1. Ưu tiên tái sử dụng test cases, fixtures và domain knowledge trước; chỉ copy code nếu module độc lập, đã test tốt và phù hợp data model mới.

# 3. Định vị Menuto

## 3.1 Product promise

> **Menuto**
>
> “Cho Menuto biết ngân sách, mục tiêu và đồ bạn đang có - Menuto tối ưu cả tuần ăn và mua sắm cho bạn.”

Không định vị Menuto là chatbot. AI là lớp giao tiếp; sản phẩm cốt lõi là một decision engine có khả năng giải thích và kiểm chứng.

## 3.2 Competitive position

| **Sản phẩm**  | **Điểm mạnh công khai**                                                                 | **Khoảng Menuto cần sở hữu**                                                                   |
|---------------|-----------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| NeatEat       | Budget-first weekly grid, automatic grocery list, ingredient reuse, simple consumer UX. | Budget + nutrition + inventory + retail package + waste/carryover trong cùng optimization loop. |
| Eat This Much | Automatic meal planner mạnh về calories/macros, preferences, budget và schedule.        | Procurement/inventory/expiry/retail reality + execution loop.                                   |
| Samsung Food  | Recipe ecosystem, import từ web, community, meal plan + shopping list.                  | Global constraint optimization + retailer/package + measurable plan quality.                    |
| Mentu         | Family weekly plan, shopping list, macros, allergens, cooking mode.                     | Optimization sâu hơn, actual price/inventory và constraint-relaxation advisor.                  |
| Menuto       | Mục tiêu                                                                                | Food decision optimization: Plan → Shop → Cook → Consume → Learn.                               |

## 3.3 USP

- **USP 1 - Joint optimization:** tối ưu đồng thời nutrition, budget, inventory, retail package, waste, diversity và adherence.
- **USP 2 - Explainable constraints:** user biết vì sao plan này được chọn và điều kiện nào gây khó.
- **USP 3 - Constraint Relaxation Advisor:** khi không khả thi, hệ thống đưa các thay đổi tối thiểu để có nghiệm.
- **USP 4 - Execution-aware:** kế hoạch không chỉ “đẹp trên giấy”; có cooking friction, Today mode và behavioral feedback.
- **USP 5 - Retail-realistic:** mua sản phẩm/package thực tế, không chỉ nhân giá nguyên liệu theo gram.

# 4. Người dùng mục tiêu và Jobs-to-be-Done

## 4.1 Persona ưu tiên V1

| **Persona**                   | **Nhu cầu chính**                                            | **Không nên bắt họ làm**                                   |
|-------------------------------|--------------------------------------------------------------|------------------------------------------------------------|
| Budget-conscious individual   | Ăn ổn trong ngân sách tuần, giảm quyết định, tránh mua thừa. | Nhập macro chi tiết, tự tính package, quản lý spreadsheet. |
| Fitness-oriented user         | Đạt calorie/protein mục tiêu mà chi phí vẫn hợp lý.          | Tự phối món để đạt macro hoặc kiểm tra toàn tuần bằng tay. |
| Busy couple / small household | Một plan dễ nấu, reuse nguyên liệu, ít chuyến mua sắm.       | Quản lý từng món như project phức tạp.                     |
| Inventory-heavy user          | Dùng đồ sắp hết hạn trước, tránh lãng phí.                   | Tự nhớ lot/hạn dùng và ghép recipe bằng tay.               |

## 4.2 Core JTBD

1. Khi bắt đầu một tuần mới, tôi muốn biết ăn gì và mua gì để không vượt ngân sách.
2. Khi có mục tiêu dinh dưỡng, tôi muốn plan tự cân bằng mà không phải tính macro từng món.
3. Khi trong bếp đã có thực phẩm, tôi muốn hệ thống ưu tiên dùng chúng đúng lúc trước khi hỏng.
4. Khi không thích một món, tôi muốn đổi món nhưng vẫn giữ budget/nutrition/constraints.
5. Khi các yêu cầu xung đột, tôi muốn biết thay đổi nhỏ nhất nào giúp plan khả thi.
6. Khi đi mua hàng, tôi muốn list phản ánh package/sản phẩm thực tế và tổng giá dự kiến.
7. Khi tuần kết thúc, tôi muốn Menuto học từ những món tôi thực sự nấu, bỏ qua hoặc thay thế.

# 5. Nguyên tắc thiết kế sản phẩm

| **Nguyên tắc**                  | **Quy tắc triển khai**                                                                               |
|---------------------------------|------------------------------------------------------------------------------------------------------|
| Deterministic before generative | LLM không được là nguồn quyết định cuối cho allergy, budget, nutrition compliance hoặc feasibility.  |
| Hard vs soft explicit           | Mọi preference/constraint phải khai báo rõ hard/soft và có provenance.                               |
| Progressive disclosure          | Default UX đơn giản; macro, shopping frequency, solver preferences ở Advanced.                       |
| No silent relaxation            | Constraint bị nới phải hiển thị và lưu vào plan metadata.                                            |
| Reference data has provenance   | Nutrition, shelf life, retail price và product mapping phải có source + updated_at + quality status. |
| Optimize for adherence          | Một plan khó nấu là plan chất lượng thấp dù nutrition/cost đẹp.                                      |
| Measure actual behavior         | North Star không phải số plan generate; phải đo planned → cooked/consumed.                           |
| Version everything important    | Planner policy, data snapshot, price snapshot, nutrition target và recipe revision phải trace được.  |

# 6. Scope V1 và Non-goals

## 6.1 Must-have V1

| **Capability**                       | **V1**                                           |
|--------------------------------------|--------------------------------------------------|
| Auth + profile + household size      | Có                                               |
| Nutrition target + presets           | Có                                               |
| Allergy/exclusion                    | Có                                               |
| Preferences / meal style presets     | Có                                               |
| Recipe catalog                       | Có                                               |
| Ingredient catalog + nutrition       | Có                                               |
| Retailer/product/package/price model | Có - tối thiểu 1 market/retailer adapter         |
| Inventory ledger                     | Có                                               |
| Planner V4 + validator               | Có                                               |
| Benchmark harness                    | Có                                               |
| Shopping list                        | Có                                               |
| Regenerate + validated swap          | Có                                               |
| Plan quality summary                 | Có                                               |
| Today mode cơ bản                    | Có                                               |
| AI intent parsing + explanation      | Có, nhưng không nằm trong trusted computing base |

## 6.2 Explicit non-goals V1

- Native iOS + Android cùng lúc.
- Social feed/community.
- Full household realtime collaboration.
- Fridge vision nhận diện tự động hoàn chỉnh.
- Receipt OCR production-grade.
- Multi-retailer split-basket optimization.
- Recipe import từ mọi website/social platform.
- Medical nutrition / clinical decision support.
- Price forecasting hoặc promotion prediction.

# 7. Information Architecture và user journeys

## 7.1 Navigation đề xuất

```text
Home / Today
Plan
Shop
Kitchen
Recipes
Profile / Settings
```

Không tách module theo cách backend vào navigation. Navigation phản ánh jobs của người dùng, không phản ánh database.

## 7.2 Primary onboarding

```text
Create account
→ Household size
→ Goal preset
→ Budget
→ Allergies / foods to avoid
→ Preferred style / cooking effort
→ Default store / region
→ Optional: "What is already in your kitchen?"
→ Generate first week
```

## 7.3 Generate plan flow

```text
User intent
→ Resolve profile & constraints
→ Snapshot inventory + retail data
→ Candidate generation
→ Feasibility
→ CP-SAT solve
→ Independent validation
→ Quality metrics
→ Explain / present plan
```

## 7.4 Result screen

- Budget used / limit + confidence of prices.
- Nutrition fit score và chỉ số lệch chính.
- Inventory used + items saved from expiry.
- Estimated carryover / waste.
- Shopping trips / package count.
- Diversity + cooking effort summary.
- Nút Swap từng dish; Regenerate có kiểm soát; Save/Activate plan.

## 7.5 Today mode

- Bữa tiếp theo và thời gian/prep cần thiết.
- Các item cần lấy khỏi fridge/freezer.
- Nguyên liệu sắp hết hạn cần ưu tiên.
- Mark cooked / skipped / swapped.
- Auto-adjust inventory sau khi user xác nhận thực hiện.

# 8. Kiến trúc hệ thống

> **Architecture style**
>
> Modular monolith + PostgreSQL + CP-SAT worker path. Không dùng microservices ở V1.

```text
Web/PWA (React/Next.js)
|
v
API (FastAPI)
|
+-- Identity / Household
+-- Nutrition
+-- Catalog / Recipes
+-- Retail / Pricing
+-- Inventory
+-- Planning
+-- Shopping / Execution
+-- Preferences
+-- Assistant
|
+-→ PostgreSQL
+-→ Redis / job queue (khi cần async solve/import)
+-→ OR-Tools CP-SAT
+-→ Object storage (images/imports)
+-→ External AI providers (structured, bounded)
```

## 8.1 Vì sao modular monolith

- Planner cần transaction/read-consistency xuyên nhiều domain; microservices làm complexity tăng sớm.
- Product còn đang tìm PMF; đổi boundary và data model sẽ diễn ra thường xuyên.
- Có thể tách Retail ingestion, AI jobs hoặc optimization worker sau khi profiling chứng minh cần scale độc lập.

# 9. Bounded contexts và domain model

| **Context** | **Entities chính**                                        | **Trách nhiệm**                                             |
|-------------|-----------------------------------------------------------|-------------------------------------------------------------|
| Identity    | User, Session, Consent                                    | Auth, account lifecycle, privacy consent.                   |
| Household   | Household, Member, ServingProfile                         | Quy mô và nhu cầu người ăn; V1 có thể chỉ 1 household/user. |
| Nutrition   | NutritionProfile, NutritionTarget, GoalPreset             | TDEE/targets, macro envelope, safety bounds.                |
| Catalog     | Ingredient, FoodGroup, UnitConversion                     | Nguyên liệu chuẩn hóa, units, nutrition identity.           |
| Recipes     | Recipe, RecipeVersion, RecipeIngredient, RecipeTag        | Cách nấu, serving, nutrition, cooking friction.             |
| Retail      | Retailer, StoreRegion, Product, Package, PriceObservation | Sản phẩm thực tế, package, price, availability.             |
| Inventory   | InventoryLot, InventoryEvent, Reservation                 | Đồ đang có, expiry, consumption, waste.                     |
| Planning    | PlanRequest, Plan, PlanDay, PlanMeal, PlannerRun          | Constraints, solve, quality metrics, provenance.            |
| Shopping    | ShoppingList, ShoppingItem, PurchaseEvent                 | Mua gì, package gì, planned vs actual.                      |
| Execution   | MealExecution, RecipeExecution                            | Cook/skip/swap, actual servings.                            |
| Preferences | PreferenceSignal, PreferenceProfile                       | Declared + behavioral preferences.                          |
| Assistant   | Conversation, IntentParse, Explanation                    | Natural-language interface có boundary rõ.                  |

## 9.1 Những distinction bắt buộc

- **Ingredient != Retail Product:** “ức gà” là ingredient; “CP ức gà khay 500g” là product/package.
- **Recipe != Dish Candidate:** recipe là nội dung/cách nấu; planner candidate là phiên bản recipe đã resolve serving + availability + nutrition + cost.
- **Planned cost != Actual cost:** price snapshot tạo planned cost; receipt/purchase event tạo actual cost.
- **Inventory quantity != Shopping carryover:** carryover trở thành inventory lot khi plan được execute/purchase xác nhận.
- **Preference != Constraint:** không ăn do allergy là hard; “thích món cay” là soft signal.

# 10. Planner V4 - đặc tả thuật toán

## 10.1 Planner responsibilities

Planner V4 phải trả lời: “Trong tập recipe/product/inventory hiện tại, kế hoạch tuần nào đáp ứng hard constraints và tối ưu các mục tiêu theo thứ tự ưu tiên đã công bố?”

## 10.2 Pipeline

```text
1. Resolve request
2. Hard eligibility filter
3. Retail & inventory resolution
4. Candidate generation
5. Pareto shortlist
6. Fast feasibility bounds
7. CP-SAT model build
8. Lexicographic solve
9. Independent validation
10. Quality scoring
11. Sensitivity / relaxation advice (if infeasible)
12. Materialize plan + provenance
```

## 10.3 Candidate generation V4

Không đặt cap 8-12 và lấp cap tuần tự theo cheapest như V3. Mỗi candidate được đánh giá trên nhiều signal; shortlist là union của các frontier/buckets và luôn có diversity reserve.

| **Signal**             | **Ý nghĩa**                                 | **Ví dụ normalization** |
|------------------------|---------------------------------------------|-------------------------|
| Nutrition fit          | Khớp target của meal composition/role.      | 0..1 error ratio        |
| Purchase cost          | Chi phí biên thực sự sau inventory/package. | marginal VND / serving  |
| Inventory utilization  | Dùng nguyên liệu đang có/sắp hết hạn.       | value/qty saved         |
| Ingredient overlap     | Reuse nguyên liệu giữa các bữa.             | shared ingredient score |
| Preference             | Tag + behavioral affinity.                  | 0..1                    |
| Adherence              | Thời gian, khó, thiết bị, số ingredients.   | friction score          |
| Retail availability    | Có package/price usable không.              | hard/soft confidence    |
| Diversity contribution | Cooking method/protein/style diversity.     | coverage gain           |

> **Rule**
>
> Reference solve dùng candidate pool lớn + timeout dài phải tồn tại trong benchmark. V4 shortlist chỉ được chấp nhận nếu quality gap so với reference nằm trong threshold đã đặt.

## 10.4 Hard constraints V1

- Allergy/excluded ingredients.
- Meal slot composition.
- Retail/product availability nếu request yêu cầu store-specific plan.
- Budget upper bound khi user đánh dấu budget là strict.
- Inventory availability windows và expiry.
- Package quantization/purchase increment.
- Daily calorie safety envelope.
- Horizon calorie/protein minimum.
- No negative stock / double reservation.
- Hard recipe dietary rules.
- User-defined hard exclusions.

## 10.5 Lexicographic objectives đề xuất

| **Priority** | **Objective**                  | **Ghi chú**                                                                        |
|--------------|--------------------------------|------------------------------------------------------------------------------------|
| P0           | Hard feasibility               | Không đánh đổi.                                                                    |
| P1           | Normalized nutrition deviation | Calories/protein/macros dùng tỷ lệ/basis points; không cộng raw kcal với raw gram. |
| P2           | Purchase cost                  | Chi phí package thực tế sau inventory.                                             |
| P3           | Expiry/waste risk              | Ưu tiên tiêu thụ lot sắp hết hạn; penalty waste có value + quantity.               |
| P4           | Ending carryover               | Không coi mọi carryover là waste; phân biệt useful carryover vs awkward remainder. |
| P5           | Shopping effort                | Trips, unique products/packages.                                                   |
| P6           | Adherence / cooking friction   | Giảm plan quá khó, quá nhiều prep.                                                 |
| P7           | Diversity + preferences        | Không lặp, style preference, behavioral score.                                     |

## 10.6 Nutrition normalization

```text
calorie_error_bp = abs(calories - target) / target * 10_000
protein_shortage_bp = max(target - protein, 0) / target * 10_000
fat_error_bp = abs(fat - target) / target * 10_000
carb_error_bp = abs(carbs - target) / target * 10_000
nutrition_score = weighted_sum(basis_points)
```

Protein overage policy phải configurable; V1 có thể chỉ penalize shortage nhưng phải có upper safety guard nếu domain yêu cầu.

## 10.7 Meal-level distribution

Daily total tốt chưa đủ. Planner nên có soft envelopes theo meal slot (ví dụ breakfast/lunch/dinner ratios) hoặc per-slot target derived từ user schedule. Đây là soft constraint mặc định, có thể harden cho use case cụ thể.

## 10.8 Solver state semantics

| **State**            | **Ý nghĩa UI/API**                                             |
|----------------------|----------------------------------------------------------------|
| OPTIMAL              | Đã chứng minh optimum trong model/candidate set.               |
| FEASIBLE_BEST_EFFORT | Có nghiệm hợp lệ nhưng chưa chứng minh optimum do time limit.  |
| PROVEN_INFEASIBLE    | Model đã chứng minh không có nghiệm.                           |
| UNKNOWN_TIME_LIMIT   | Không được diễn giải là infeasible; có thể retry/relax/expand. |
| DATA_INSUFFICIENT    | Thiếu catalog/price/procurement data để model đáng tin cậy.    |

# 11. Feasibility, relaxation và explainability

## 11.1 Feasibility V2

- Lower-bound budget phải trừ inventory usable và tính package lower bound hợp lý.
- Nutrition range phải dựa trên valid meal compositions, không chỉ min/max riêng từng dish role nếu correlation làm bound quá lỏng.
- Precheck chỉ hard-reject khi bound bảo thủ và chứng minh được; nếu không, trả warning và cho solver quyết định.
- Data-quality failures phải phân biệt với mathematical infeasibility.

## 11.2 Constraint Relaxation Advisor

Khi PROVEN_INFEASIBLE, Menuto chạy một lớp sensitivity analysis để tìm thay đổi nhỏ nhất theo preference của user.

| **Relaxation candidate** | **Ví dụ**                                      |
|--------------------------|------------------------------------------------|
| Budget                   | +80.000đ để đạt target hiện tại.               |
| Protein target           | 150g → 132g/ngày.                              |
| Diet/exclusion           | Cho phép chicken 2 bữa/tuần.                   |
| Diversity                | Cho phép 1 món lặp thêm 1 lần.                 |
| Shopping trips           | 2 → 3 chuyến.                                  |
| Planning horizon         | 7 → 6 ngày nếu user muốn giữ budget tuyệt đối. |

> **UX rule**
>
> Không tự động nới hard constraint mà không báo. User phải nhìn thấy thay đổi và chọn/accept nếu đó là constraint họ khai báo.

## 11.3 Plan explanation

- Vì sao plan này fit budget.
- Nguồn calorie/protein targets.
- Inventory lot nào được ưu tiên vì expiry.
- Package nào tạo carryover.
- Món nào được chọn vì preference/adherence.
- Solver có timed out không.
- Constraint nào relaxed và mức độ.

# 12. Retail, product và pricing architecture

## 12.1 Core schema

| **Entity**           | **Fields tối thiểu**                                                                   |
|----------------------|----------------------------------------------------------------------------------------|
| Retailer             | id, name, country, currency, status                                                    |
| StoreRegion          | retailer_id, region_code, fulfillment_mode                                             |
| RetailProduct        | retailer_sku, name, brand, ingredient_mapping_status                                   |
| Package              | product_id, quantity, unit, pack_count, normalized_quantity                            |
| PriceObservation     | package_id, amount, currency, observed_at, source, promotion, availability, confidence |
| IngredientProductMap | ingredient_id, product_id, conversion/yield, confidence, reviewed_at                   |

## 12.2 Price selection policy

1. Chỉ dùng observation chưa stale theo retailer policy.
2. Ưu tiên exact store/region, sau đó region-level fallback nếu user cho phép.
3. Mọi fallback phải ghi confidence/provenance.
4. Promotion price có validity window; không coi promotion cũ là current.
5. Planner snapshot price IDs vào plan để historical reproducibility.

## 12.3 Package optimization

Optimizer chọn số package integer thay vì cost = grams \* normalized unit price. Normalized unit price chỉ là ranking/heuristic; budget constraint cuối phải dựa trên package purchase cost.

# 13. Inventory và food lifecycle

## 13.1 Inventory lot

| **Field**                  | **Mục đích**                                                       |
|----------------------------|--------------------------------------------------------------------|
| ingredient_id / product_id | Trace nguyên liệu và nguồn retail nếu biết.                        |
| quantity_remaining + unit  | Tồn thực tế.                                                       |
| available_from             | Có thể là future delivery/purchase.                                |
| expires_on / best_before   | Expiry scheduling.                                                 |
| storage_mode               | room / fridge / freezer / same_day.                                |
| cost_basis                 | Đo waste value, planned vs actual.                                 |
| source                     | manual / purchase / carryover / receipt import.                    |
| status                     | projected / available / reserved / consumed / expired / discarded. |

## 13.2 Event-sourced-ish inventory ledger

Không cần full event sourcing framework, nhưng inventory nên có immutable events cho purchase, consume, adjust, waste, transfer-storage. quantity_remaining có thể là materialized state.

## 13.3 Input UX

V1: manual + quick-add. V1.5: barcode/receipt/photo là input accelerators. Tất cả đều normalize về cùng InventoryLot contract.

# 14. Recipe, cooking friction và adherence

## 14.1 Recipe model

| **Nhóm**    | **Fields**                                                       |
|-------------|------------------------------------------------------------------|
| Identity    | title, cuisine, tags, source, version                            |
| Serving     | base_servings, portion unit, yield                               |
| Ingredients | ingredient_id, qty/unit, optional/substitute rules               |
| Cooking     | prep_minutes, cook_minutes, total_minutes, equipment, difficulty |
| Batch       | batchable, leftover_days, reheating suitability                  |
| Nutrition   | calculated snapshot + provenance                                 |
| Planner     | meal roles, seasonality, suitability tags                        |
| Safety      | allergen derivation / manual review flags                        |

## 14.2 Adherence score

```text
adherence_score =
time_fit
+ equipment_fit
+ complexity_fit
+ ingredient_count_fit
+ batch_fit
+ weekday_fit
+ behavioral_acceptance
- recent_rejection_penalty
```

Không cần ML ở V1. Score heuristic + configurable policy đủ để thu data. Chỉ chuyển sang learned ranking khi có đủ event volume và offline evaluation.

# 15. AI / Menuto Assistant

## 15.1 AI làm gì

- Parse natural-language request thành structured intent.
- Giải thích plan dựa trên metrics đã xác minh.
- Hỗ trợ recipe normalization/import.
- Hiểu yêu cầu swap (“nhanh hơn”, “ít cay”, “rẻ hơn”).
- Tạo conversational interface cho relaxation options.

## 15.2 AI không được làm gì

- Tự tuyên bố plan feasible.
- Tự tính authoritative purchase cost.
- Tự bỏ allergy constraint.
- Tự sửa nutrition target mà không có domain rule/user consent.
- Tạo ingredient/price facts không có provenance rồi đưa vào trusted catalog.

## 15.3 Trusted computing boundary

```text
LLM → structured intent / candidate suggestions
→ schema validation
→ deterministic services
→ optimizer / validator
→ verified metrics
LLM ← verified metrics for explanation
```

# 16. API, backend và frontend architecture

## 16.1 Backend stack đề xuất

| **Layer**      | **Lựa chọn V1**                                            |
|----------------|------------------------------------------------------------|
| Language       | Python 3.13+                                               |
| API            | FastAPI + Pydantic v2                                      |
| Persistence    | SQLAlchemy 2 + PostgreSQL                                  |
| Migrations     | Alembic hoặc migration runner chuẩn hóa; một nguồn sự thật |
| Optimizer      | OR-Tools CP-SAT                                            |
| Async jobs     | Redis + worker khi solve/import vượt interactive budget    |
| Object storage | S3-compatible                                              |
| Observability  | OpenTelemetry-compatible logs/traces + error tracking      |
| AI             | Provider abstraction + structured outputs                  |

## 16.2 Frontend stack đề xuất

| **Layer**     | **Lựa chọn**                                                                                     |
|---------------|--------------------------------------------------------------------------------------------------|
| Web/PWA       | React + TypeScript; Next.js nếu cần SSR/marketing và unified app shell.                          |
| Data fetching | Typed API client + query cache; không fetch rải rác trong components.                            |
| Forms         | Schema-driven validation; advanced settings progressive disclosure.                              |
| Design system | Tokens + reusable form/card/list/metric components.                                              |
| Mobile        | Không bắt buộc V1; API contract thiết kế mobile-ready. React Native/Expo sau product validation. |

## 16.3 API principles

- Idempotency cho generate/save/purchase mutation thích hợp.
- Explicit planner_version + policy_version + source_snapshot IDs.
- Structured error codes; không chỉ text.
- Long-running solve có run_id/status nếu chuyển sang async.
- Pagination/filtering chuẩn cho catalog/retail.
- Optimistic concurrency cho inventory mutation.

## 16.4 Repository layout gợi ý

```text
Menuto/
apps/
web/
api/
backend/
modules/
identity/
households/
nutrition/
catalog/
recipes/
retail/
inventory/
planning/
shopping/
execution/
preferences/
assistant/
shared/
data/
seeds/
imports/
tests/
benchmark/
integration/
docs/
adr/
product/
api/
```

# 17. Security, privacy và safety

| **Area**            | **Requirement V1**                                                                                |
|---------------------|---------------------------------------------------------------------------------------------------|
| Auth                | Modern password hashing/OAuth; rotateable secrets; session revocation.                            |
| Authorization       | Household/user ownership enforced backend-side; public share token scope + expiry.                |
| PII                 | Minimize; clear retention policy; export/delete workflow.                                         |
| Health-related data | Treat nutrition/profile as sensitive application data; do not overclaim medical advice.           |
| AI                  | Consent + provider data policy; no raw secrets in prompts/logs; bounded retention.                |
| Retail imports      | Source compliance; provenance and rate-limit discipline.                                          |
| Audit               | Admin/catalog/price changes auditable.                                                            |
| Safety copy         | Nutrition planning is informational/wellness; escalate clinical needs to qualified professionals. |

# 18. Testing, benchmark và observability

## 18.1 Test pyramid

| **Layer**        | **Tests**                                                                     |
|------------------|-------------------------------------------------------------------------------|
| Domain unit      | Nutrition formulas, unit conversions, shelf-life, price/package math.         |
| Planner model    | Small deterministic instances với known optimum/feasibility.                  |
| Property-based   | No negative stock, budget never exceeded, excluded ingredient never selected. |
| Integration      | Generate → validate → save → shopping → inventory reservation.                |
| Golden scenarios | Curated 1/3/7-day real-world plans.                                           |
| Benchmark        | V3/V4/reference pool comparison; quality + runtime regression.                |
| Frontend         | Critical onboarding/generate/swap/shop/today flows.                           |
| Data quality     | Missing nutrition/price/shelf-life/product-map thresholds.                    |

## 18.2 Benchmark dimensions

- 1/3/7 days; 2 vs 3 meals/day.
- Loose/tight/no budget.
- No inventory vs rich inventory vs expiring inventory.
- Small/medium/large recipe catalog.
- High protein, maintain, calorie deficit presets.
- Many exclusions/preferences.
- Large package increments and short shelf-life.
- Price data fresh vs stale/fallback.

## 18.3 Metrics per run

| **Category** | **Metrics**                                                               |
|--------------|---------------------------------------------------------------------------|
| Solver       | status, solve_ms, phases completed, optimal/best-effort, candidate_count. |
| Nutrition    | calorie_error_pct, protein_shortage_pct, macro deviations.                |
| Budget       | purchase_cost, budget_utilization, actual-vs-planned later.               |
| Inventory    | inventory_value_used, expiring_value_saved, ending stock.                 |
| Waste        | expired_waste_value, awkward_carryover_value.                             |
| Experience   | unique_dishes, repeats, cooking_minutes, shopping_days, unique_products.  |
| Quality gap  | difference vs reference solve on comparable objective vector.             |

## 18.4 Observability

- Planner run trace có request fingerprint nhưng tránh PII/raw sensitive detail trong logs.
- Catalog data version + policy version + price snapshot IDs.
- Reason codes cho infeasible/data insufficient/time limit.
- Dashboard nội bộ theo fail rate, timeout rate, swap rate, plan quality distribution.

# 19. Metrics và feedback loop

> **North Star Metric**
>
> Completed planned meals per active household per week.

| **Metric**            | **Ý nghĩa**                                     |
|-----------------------|-------------------------------------------------|
| Plan acceptance rate  | Plan generate xong có được activate/save không. |
| Swap rate             | Proxy cho candidate/preference quality.         |
| Planned → cooked rate | Adherence thực tế.                              |
| Budget deviation      | Planned vs actual spend.                        |
| Inventory utilization | Giá trị/khối lượng đồ sẵn có được dùng.         |
| Waste rate            | Discarded/expired inventory.                    |
| Weekly retention      | Menuto có trở thành routine không.             |
| Relaxation acceptance | Advisor có đưa lựa chọn hữu ích không.          |

## 19.1 Behavioral events

```text
plan_generated
plan_activated
dish_shown
dish_swapped
dish_skipped
dish_cooked
recipe_favorited
shopping_item_purchased
actual_price_recorded
inventory_consumed
inventory_discarded
relaxation_offered
relaxation_accepted
```

# 20. Roadmap Public V1 → V1.5 → V2

## 20.1 Milestone 0 - Foundation / decisions

- Create clean repo + ADRs.
- Freeze domain glossary and hard/soft constraint semantics.
- Set coding/testing/CI conventions.
- Create initial benchmark fixtures from Smart Menu scenarios.

## 20.2 Milestone 1 - Core data platform

- Identity/profile/household minimal.
- Ingredient + nutrition + recipe schemas.
- Retailer/product/package/price schemas.
- Inventory lot/event model.
- Admin/data-quality workflows.

## 20.3 Milestone 2 - Planner V4

- Candidate generator + Pareto shortlist.
- Inventory-aware feasibility.
- Normalized nutrition objective.
- Package-aware procurement model.
- Independent validator.
- Benchmark/reference solver.
- Structured reason codes.

## 20.4 Milestone 3 - Consumer V1

- Onboarding.
- Generate/result quality summary.
- Swap/regenerate.
- Shopping list.
- Today mode basic.
- Inventory quick-add.
- AI parse/explain bounded by deterministic data.

## 20.5 Milestone 4 - Public readiness

- Security/privacy review.
- Data provenance/freshness thresholds.
- Observability + error tracking.
- Performance/load tests.
- Accessibility/responsive QA.
- Seed/catalog quality gate.
- Launch checklist and rollback strategy.

## 20.6 V1.5

- Barcode/receipt-assisted inventory.
- Cooking friction tuning.
- Household-lite sharing.
- More retailer adapters.
- Leftover execution workflow.
- Behavioral preference scoring.
- Recipe import limited/bounded.

## 20.7 V2

- Multi-retailer basket optimization.
- Full household individual nutrition + shared dishes/portion optimization.
- Native mobile if web/PWA retention validates need.
- Camera inventory assistant.
- Long-horizon carryover planning.
- Learned ranking/personalization after sufficient offline evaluation data.

# 21. Backlog triển khai ưu tiên

| **ID**  | **Priority** | **Epic / Issue**               | **Acceptance criteria tóm tắt**                                                                   |
|---------|--------------|--------------------------------|---------------------------------------------------------------------------------------------------|
| MTR-001 | P0           | Domain glossary + ADR baseline | Ingredient/Product/Recipe/Candidate/Inventory/Constraint semantics documented; no ambiguous term. |
| MTR-002 | P0           | Benchmark harness              | Runs scenario matrix; emits objective vector, runtime, status; CI regression threshold.           |
| MTR-003 | P0           | Retail schema                  | Retailer/Product/Package/PriceObservation + provenance + freshness.                               |
| MTR-004 | P0           | Planner V4 candidate generator | Multi-signal shortlist; no cheapest-first cap starvation; reference-gap test.                     |
| MTR-005 | P0           | Feasibility V2                 | Inventory-aware; distinguishes data insufficiency/time limit/proven infeasible.                   |
| MTR-006 | P0           | Normalized nutrition objective | Basis-point deviations; policy versioned and unit-tested.                                         |
| MTR-007 | P0           | Package-aware procurement      | Integer package decisions; inventory allocation; budget constraint authoritative.                 |
| MTR-008 | P0           | Independent validator          | Rejects any invalid optimizer output; separate implementation path.                               |
| MTR-009 | P0           | Generate API v1                | Planner/version/source snapshot in response; structured reasons/warnings.                         |
| MTR-010 | P0           | Consumer onboarding            | Default flow ≤ key decisions; advanced settings hidden by default.                                |
| MTR-011 | P0           | Plan Quality Summary           | Budget/nutrition/inventory/waste/trips/status visible.                                            |
| MTR-012 | P1           | Validated swap                 | Re-plan/validate whole plan; show impact delta.                                                   |
| MTR-013 | P1           | Regenerate alternatives        | Material difference threshold + preserved constraints.                                            |
| MTR-014 | P1           | Constraint Relaxation Advisor  | Returns ranked minimal relaxations after proven infeasible.                                       |
| MTR-015 | P1           | Today mode                     | Next meal + prep + expiry prompts + cooked/skip action.                                           |
| MTR-016 | P1           | Inventory ledger UI            | Quick-add, adjust, consume, discard; optimistic concurrency.                                      |
| MTR-017 | P1           | Price freshness/confidence     | Stale/fallback shown; plan snapshots selected price IDs.                                          |
| MTR-018 | P1           | AI intent/explanation          | Structured schema + verified metrics only; no safety/feasibility authority.                       |
| MTR-019 | P1           | Telemetry/feedback events      | Plan/swaps/cook/purchase/waste events with privacy review.                                        |
| MTR-020 | P2           | Barcode/receipt import         | Normalize to InventoryLot; manual confirmation before commit.                                     |
| MTR-021 | P2           | Household-lite                 | Shared plan/list/inventory scope after V1 stability.                                              |
| MTR-022 | P2           | Recipe import                  | Importer produces reviewable draft; never auto-trust nutrition/allergy facts.                     |

# 22. Smart Menu → Menuto reuse/migration matrix

| **Smart Menu capability**     | **Action**                   | **Lý do**                                                              |
|-------------------------------|------------------------------|------------------------------------------------------------------------|
| Nutrition calculator/domain   | PORT WITH TESTS              | Domain tương đối độc lập; giữ formulas, đổi API/schema naming.         |
| CandidateSelector V3          | REWRITE                      | Có starvation/abstraction issues.                                      |
| Optimizer V3                  | REFERENCE + EXTRACT          | Giữ ideas/procurement modeling; viết V4 model trên contract mới.       |
| Feasibility V3                | REWRITE                      | Budget lower bound cần inventory/package-aware.                        |
| Procurement checker/validator | PORT CONCEPT, DUAL IMPLEMENT | Giữ independent validation, tránh share quá nhiều logic với optimizer. |
| Inventory schema              | REDESIGN, PORT CONCEPTS      | Lot model tốt nhưng cần events/product identity/lifecycle rõ hơn.      |
| price_snapshots               | REPLACE                      | Thiếu retailer/product/package identity.                               |
| Shopping list                 | PORT                         | Concept/UX hữu ích; update sang product/package items.                 |
| Public share token            | PORT LATER V1/P1             | Đã là consumer-friendly capability.                                    |
| CreateMenu UI                 | REDESIGN                     | Form-driven; Menuto cần onboarding/progressive disclosure.            |
| MenuResult explain/swap       | PORT UX CONCEPTS             | Giữ explain + whole-plan validation; redesign quality header.          |
| AI provider abstraction       | PORT                         | Boundary phù hợp nếu giữ structured outputs/consent.                   |
| Admin catalog quality         | EXPAND                       | Menuto cần data QA mạnh hơn cho retail/product mapping/provenance.    |
| Tests/fixtures                | PORT AGGRESSIVELY            | Tài sản an toàn nhất để giữ bài học mà không mang coupling.            |

# 23. Definition of Done và launch gate

## 23.1 Planner DoD

- Không có hard violation trong independent validator.
- Không có known false-infeasible scenario trong benchmark suite.
- Time-limit không bị map thành infeasible.
- V1 shortlist quality gap so với reference nằm trong threshold đã phê duyệt.
- Price/package/inventory provenance snapshot được lưu cùng plan.
- Regenerate và swap giữ constraint hoặc báo rõ relaxation.

## 23.2 Data DoD

- Mọi ingredient planner-ready có nutrition provenance.
- Mọi regular purchasable ingredient có ít nhất một valid product/package mapping trong market hỗ trợ.
- Price có observed_at/source/confidence; stale policy được enforce.
- Shelf-life data thiếu không được silent-assume nếu ảnh hưởng plan.

## 23.3 Consumer launch gate

- Onboarding/generate/shop/today responsive và keyboard usable.
- Structured errors có copy user-friendly.
- Privacy policy/data deletion/export path.
- Operational dashboards cho generate error/timeout/infeasible/data-quality.
- Seed catalog đủ diversity cho target market.
- No critical/high security findings mở.
- Backup/restore và migration rollback đã test.

# 24. Rủi ro và quyết định kiến trúc

| **Rủi ro**                                           | **Tác động** | **Mitigation**                                                                       |
|------------------------------------------------------|--------------|--------------------------------------------------------------------------------------|
| Retail data acquisition khó/không ổn định            | Cao          | Adapter architecture; start one market; provenance/freshness; manual/admin fallback. |
| Solver model phình khi catalog/package tăng          | Cao          | Pareto shortlist, staged solve, benchmark, async worker path.                        |
| Data quality làm optimizer “đúng toán nhưng sai đời” | Rất cao      | Quality gates, source provenance, admin review, confidence.                          |
| UX quá nhiều setting                                 | Cao          | Goal presets + progressive disclosure + smart defaults.                              |
| Nutrition bị hiểu là medical advice                  | Cao          | Wellness positioning, bounded claims, safety copy, exclude clinical use cases V1.    |
| AI hallucination xâm nhập trusted data               | Cao          | Schema validation + review state + deterministic truth sources.                      |
| Build too much before PMF                            | Cao          | Strict V1 non-goals; metric-driven V1.5/V2 gates.                                    |
| Tên Menuto conflict/trademark                       | Trung bình   | Trademark/domain/App Store search trước branding investment lớn.                     |

## 24.1 ADRs cần viết ngay

1. ADR-001 Modular Monolith boundaries.
2. ADR-002 Ingredient vs RetailProduct separation.
3. ADR-003 Planner trusted boundary and AI role.
4. ADR-004 Hard/soft constraints and relaxation policy.
5. ADR-005 Planner versioning + reproducibility snapshots.
6. ADR-006 Inventory ledger/event model.
7. ADR-007 Retail price freshness/confidence policy.
8. ADR-008 Benchmark/reference-solve acceptance policy.

# 25. Nguồn tham chiếu và ghi chú nghiên cứu

## 25.1 Smart Menu files đã rà soát

- backend/app/modules/meal_planning/candidate_selector.py - shortlist + per-dish nutrition ranking.
- backend/app/modules/meal_planning/domain.py - PlanRequest, DishCandidate, QualityPolicy, metrics.
- backend/app/modules/meal_planning/feasibility.py - budget/nutrition precheck.
- backend/app/modules/meal_planning/optimizer_v3.py - procurement-aware CP-SAT, diversity tiers, lexicographic phases.
- data/migrations/20260720_v3_ledger_inventory.sql - inventory lots/reservations.
- data/init_db.sql - nutrition, price snapshots, exclusions.
- frontend/src/pages/meal-planning/CreateMenu.tsx - current generate UX + AI parse request.
- frontend/src/pages/meal-planning/MenuResult.tsx - regenerate, AI explanation, validated swap UX.
- docs/code/frontend.md, docs/code/database.md, docs/code/architecture.md - current module/route/data contracts.

## 25.2 External market references checked 21/10/2026

| **Source**               | **Key signal**                                                                                                                                                                                   |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| NeatEat official website | Budget-first weekly grid, automatic grocery list, reuse ingredients; explicitly not nutrition/health tracking.                                                                                   |
| NeatEat App Store        | Active consumer product with premium SKUs; rapid iteration.                                                                                                                                      |
| Eat This Much official   | Automatic meal planning based on preferences, budget, schedule, calories/macros.                                                                                                                 |
| Samsung Food official    | Large recipe/import ecosystem, meal planner, nutrition and shopping list.                                                                                                                        |
| Mentu App Store          | Family meal planning, shopping lists, cooking mode, calories/macros and allergens.                                                                                                               |
| Mealime official/support | Classic Plan → Shop → Cook UX and strong personalization; public site announced shutdown on 21/10/2026, a reminder that UX alone is not sufficient without sustainable execution/business model. |

External product claims are used only to frame positioning. They do not prove competitors’ private algorithms or backend implementations.

## 25.3 Final recommendation

> **Build order**
>
> 1) Domain/ADR + benchmark → 2) Core data + retail foundation → 3) Planner V4 + validator → 4) consumer generate/shop/today loop → 5) public-readiness → 6) only then expand camera/import/household/native mobile.

Menuto có cơ hội rõ nhất nếu giữ độ sâu tối ưu của Smart Menu nhưng thay đổi cách sản phẩm được đóng gói: từ “meal planner có nhiều module” thành “decision system cho cả vòng đời ăn uống trong tuần”. Điều quan trọng nhất không phải thêm nhiều feature hơn đối thủ, mà là làm cho engine đáng tin cậy, dữ liệu gần thực tế, UX đơn giản, và feedback loop đo được việc user có thực sự làm theo plan hay không.
