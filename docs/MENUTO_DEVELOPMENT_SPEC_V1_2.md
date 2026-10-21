# MENUTO - Tài liệu phát triển sản phẩm V1.2

**Product Strategy · Architecture · Planner V4 · Data Model · UX · Roadmap**

> **Phiên bản:** V1.2 — Canonical Architecture Baseline
>
> **Ngày cập nhật:** 21/10/2026
>
> **Mục tiêu của revision này:** đóng băng baseline kiến trúc đã được tranh luận và chốt qua các vòng Planner, Nutrition, Policy, Household, Recipe, Retail và Budget. V1.2 là canonical spec để triển khai; các abstraction cũ bị thay thế trực tiếp, không tồn tại song song.

> **Định nghĩa sản phẩm**
>
> Menuto là nền tảng tối ưu quyết định ăn uống cho cá nhân/hộ gia đình: kết hợp ngân sách, dinh dưỡng, sở thích, inventory, hạn sử dụng, sản phẩm bán lẻ và khả năng thực hiện để tạo một kế hoạch ăn + mua sắm có thể áp dụng trong đời sống thực.

Nguồn thiết kế: Smart Menu hiện tại + rà soát sản phẩm cạnh tranh + các vòng architecture debate về Planner, Nutrition Policy, Household và Recipe Model.

> **Tệp Markdown chuẩn:** `docs/MENUTO_DEVELOPMENT_SPEC_V1_2.md`

## Revision highlights từ V1.0

1. Loại bỏ `PlanningMode`; thay bằng `PlanPolicyResolver` và các policy axis độc lập.
2. Thay point-target nutrition bằng **Guideline/Goal/Comfort + Weekly Centering**.
3. Thay nhiều phase lexicographic bằng **2-stage Band-First global solve + bounded local refinement**.
4. Candidate generation trở thành **role-aware Pareto grounding**.
5. Household là ownership boundary ngay từ V1; Solver V1 chỉ có một `TrackedMember` về individualized nutrition.
6. `MealParticipants` là source of truth; `AttendanceScale` chỉ là derived coefficient; `ConsumptionDemand != BatchProduction`.
7. Recipe dùng **authored flexibility → pre-solve grounded immutable candidates**; global solver không tự sáng tác món.
8. Package-fit dùng **portion tiers → global solve → bounded CulinaryAdjustmentPass**.
9. Inventory có policy, confidence và **One-tap Reconcile**.
10. Relaxation Advisor dùng **conflict → elastic estimate → verification** và tuân thủ `No silent relaxation`.
11. Retail được chuẩn hóa thành **Retail evidence → ProcurementClass → Planning Quote → concrete primary/backups**.
12. `RetailProduct/SKU` không phải đơn vị tối ưu hóa mặc định; `FIXED_PACK`, `CATCH_WEIGHT`, `LOOSE_SCALE` được mô hình hóa riêng.
13. Reference fallback dùng **RetailPriceCalibration theo retailer × region × category**, không dùng một store multiplier mù.
14. `SPEND_LIMIT` được kiểm tra bằng **deterministic robust stress scenarios**, không giả lập P90 khi chưa có dữ liệu calibrated.
15. Risk score không được trình bày như probability; checkout certainty không được hứa nếu Menuto không khóa giá/tồn kho.
16. Bộ **8 ADR canonical + Architecture Invariants** được xuất bản cùng V1.2 và trở thành guardrail cho implementation.

# Mục lục

1. Tóm tắt điều hành
2. Kết luận sau khi rà soát lại Smart Menu
3. Định vị Menuto
4. Người dùng mục tiêu và Jobs-to-be-Done
5. Nguyên tắc thiết kế và architecture invariants
6. Scope V1 và Non-goals
7. Information Architecture và user journeys
8. Kiến trúc hệ thống
9. Bounded contexts và domain model
10. Planner V4 - Band-First Optimization Architecture
11. Feasibility, relaxation và explainability
12. Retail, product và pricing architecture
13. Inventory và food lifecycle
14. Recipe architecture, cooking batch và adherence
15. AI / Menuto Assistant
16. API, backend và frontend architecture
17. Security, privacy và safety
18. Testing, benchmark và observability
19. Metrics và feedback loop
20. Roadmap Public V1 → V1.5 → V2
21. Backlog triển khai ưu tiên
22. Smart Menu → Menuto reuse/migration matrix
23. Definition of Done và launch gate
24. ADR registry, risks và open decisions
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

# 5. Nguyên tắc thiết kế và architecture invariants

## 5.1 Product/engineering principles

| Nguyên tắc | Quy tắc triển khai |
|---|---|
| Deterministic before generative | LLM không là nguồn quyết định cuối cho allergy, budget, nutrition compliance, feasibility hoặc authoritative price. |
| Hard vs soft explicit | Mọi constraint/preference phải khai báo loại, provenance, scope và policy version. |
| Progressive disclosure | User trả lời câu hỏi đời sống; solver terminology không lộ ra onboarding mặc định. |
| No silent relaxation | Bất kỳ constraint nào bị nới đều phải có reason code, user-visible explanation và plan metadata. |
| Reference data has provenance | Nutrition, shelf-life, retail price, product mapping và recipe revision phải trace được nguồn/version. |
| Optimize for adherence | Plan khó mua/nấu/thực hiện là plan chất lượng thấp dù macro và cost đẹp. |
| Measure actual behavior | North Star là completed planned meals, không phải số plan generated. |
| Version important decisions | Planner policy, price snapshot, recipe version, nutrition policy và resolver output phải reproducible. |

## 5.2 Architecture invariants đã khóa

Canonical list được mirror tại `docs/ARCHITECTURE_INVARIANTS.md`.

### INV-001 — Planning preference must never masquerade as physiology

`CostPreference`, `KitchenEffort` hoặc “tuần này bận/tiết kiệm” không được ngầm thay đổi guideline/physiological constraints.

### INV-002 — Observed constraint must never masquerade as user preference

`BudgetPressure` cao không đồng nghĩa user muốn rẻ nhất có thể. System pressure, explicit budget contract và subjective preference là ba dữ kiện độc lập.

### INV-003 — Shared resource != shared physiology

Inventory, shopping, kitchen, batch và plan thuộc Household; nutrition/allergy/diet/body/goal thuộc HouseholdMember.

### INV-004 — Aggregate demand must never erase individual safety constraints

Một aggregate attendance coefficient không được làm mất allergy/diet constraints của participants tạo ra coefficient đó.

### INV-005 — Recipe flexibility must be authored, not inferred

Substitution, quantity envelope và compatibility phải được catalog author/curated rule cho phép; không tự suy từ cost/nutrition similarity.

### INV-006 — Global optimization may choose among culinary possibilities; it may not create culinary possibilities

Global CP-SAT chỉ chọn grounded immutable candidates; không free-form substitute, mutate recipe ratio hoặc đổi cooking method.

### INV-007 — Attendance != production

Meal consumption demand và cooking batch production/allocation là hai khái niệm khác nhau.

### INV-008 — Retail observations are evidence, not guarantees

Offer/price/availability là observations có provenance và freshness, không phải lời hứa rằng cùng SKU sẽ còn tại `T_shop`.

### INV-009 — The planner optimizes procurement resilience, not merely observed price

Một basket rẻ nhưng phụ thuộc promo/single-source SKU có thể kém hơn basket đắt hơn một chút nhưng robust.

### INV-010 — Mathematical budget feasibility must not be presented as checkout certainty

`SPEND_LIMIT` là feasibility dưới procurement-risk policy của Menuto, không phải guarantee hóa đơn nếu chưa có locked cart/price/stock.

### INV-011 — A risk score is not a probability unless it has been calibrated as one

Không dùng heuristic reserve, score hoặc confidence để claim `P90`, `90%` hay xác suất tương tự khi chưa backtest/calibrate bằng actual outcomes.

### INV-012 — A hard user constraint may produce a relaxed alternative, but the alternative must never inherit the hard-feasible label without explicit user acceptance

Relaxation Advisor có thể đề xuất phương án gần khả thi; phương án đó phải mang status riêng và chỉ trở thành active plan sau explicit acceptance.

## 5.3 Trusted boundary

```text
User intent / AI parse
        ↓
Policy resolvers + data resolvers
        ↓
Grounded candidates
        ↓
Deterministic optimizer
        ↓
Independent validator
        ↓
Verified plan metrics
        ↓
AI explanation / UI
```

# 6. Scope V1 và Non-goals

## 6.1 Must-have V1

| Capability | V1 boundary |
|---|---|
| Auth + default Household | Có; đăng ký tạo household mặc định + primary member. |
| Household members | Có ở schema; UI tối thiểu hỗ trợ shared diners/portion factor. |
| Tracked nutrition member | Có đúng 1 member/plan được enforce đầy đủ nutrition policy. |
| Nutrition policy | Safety/guideline + goal envelope + comfort band + weekly centering. |
| Budget policy | amount + SPEND_LIMIT/TARGET/NONE + explicit cost preference. |
| Kitchen policy | default effort + weekday/weekend cook-time envelope + batching preference. |
| Allergy/dietary constraints | Per-member; shared meal dùng intersection hard constraints của participants. |
| Recipe catalog | Versioned recipe + bounded variant rules + culinary roles. |
| Retail model | Ingredient != RetailProduct; RetailOffer/PriceObservation + ProcurementClass + PlanningPriceQuote are first-class. |
| ReferencePriceBook | Có làm fallback có provenance, không giả làm retailer. |
| Inventory ledger | Household-scoped lots + events + policy + reconcile state. |
| Planner V4 | Role-aware grounded candidates + 2-stage Band-First solve + validator. |
| CookingBatch | Model production/allocation tối thiểu cho shared leftovers/batch cook. |
| Benchmark harness | Có reference runs + regression thresholds. |
| Shopping list | ProcurementClass-aware ShoppingRequirement with primary + backup offers. |
| Local swap | Freeze other meals; revalidate whole plan/procurement. |
| Regenerate remaining plan | Có controlled difference và preserved constraints. |
| Plan Quality Summary | Budget, nutrition zone, inventory, waste/carryover, kitchen effort, confidence. |
| Today mode cơ bản | Next meal, prep, batch/leftover note, expiry prompts, execution feedback. |
| AI intent/explanation | Có nhưng ngoài trusted computing base. |

## 6.2 Explicit non-goals V1

- Full individualized nutrition optimization cho nhiều household members trong cùng một meal.
- Personalized component allocation kiểu “A ăn 185g thịt, B ăn 115g” do solver quyết định.
- Solver tự tạo recipe bằng free-form substitution hoặc free-form ingredient ratios.
- Native iOS + Android cùng lúc.
- Social feed/community.
- Full realtime household collaboration.
- Fridge vision/receipt OCR production-grade.
- Multi-retailer split-basket optimization.
- General web/social recipe import production-grade.
- Clinical/medical nutrition decision support.
- Price forecasting hoặc promotion prediction.

## 6.3 V1 wellness eligibility boundary

V1 chỉ định vị cho general wellness planning. Các nhóm cần therapeutic/clinical nutrition, pregnancy/breastfeeding, pediatric planning hoặc disease-specific macro restrictions không được solver tự xử lý như use case mặc định. Khi profile/request nằm ngoài phạm vi supported, Menuto phải trả explicit unsupported/clinician-guided state thay vì bịa safety policy.

# 7. Information Architecture và user journeys

## 7.1 Navigation đề xuất

```text
Home / Today
Plan
Shop
Kitchen
Recipes
Household / Profile
Settings
```

Navigation phản ánh jobs của user, không phản ánh bounded contexts backend.

## 7.2 Onboarding: hỏi về đời sống, không hỏi về solver

```text
Create account
→ Auto-create default Household
→ Household / người thường ăn cùng
→ Tracked member + goal
→ Weekly budget + "mức tối đa hay linh hoạt?"
→ Allergies / foods to avoid của các member liên quan
→ Ngày thường muốn dành bao lâu cho việc bếp?
→ Có theo dõi macro nghiêm túc không?
→ Default region / retailer (nếu hỗ trợ)
→ Optional inventory bootstrap
→ Generate first week
```

Không có màn hình chọn `BALANCED | BUDGET_FIRST | CONVENIENCE_FIRST | STRICT_NUTRITION`.

## 7.3 Policy defaults và situational overrides

Stable defaults được lưu ở profile/household. Mỗi plan có thể có temporary overrides mà không sửa profile gốc.

Ví dụ summary trước Generate:

```text
Tuần này
🎯 Bám khá sát mục tiêu
💰 Không vượt 700.000đ
⚡ ≤20 phút ngày thường, ưu tiên nấu gộp
👥 Tối ăn 2 người; sáng/trưa 1 người
```

User chạm từng chip để sửa đúng một chiều. Chip “Tiết kiệm hơn” không được tự thay đổi budget amount; chip “Bận hơn” không được làm nutrition safety yếu đi.

## 7.4 One-tap Inventory Reconcile trước plan

```text
Menuto đang nghĩ bạn còn:
✓ 4 trứng
✓ 250g ức gà
✓ 1/2 bắp cải
✓ 300g gạo

[ Đúng ]  [ Chỉnh nhanh ]
```

Reconcile cập nhật confidence/truth state của inventory trước khi planner snapshot.

## 7.5 Meal participation UX

Không bắt user nhập 21 ô. V1 hỏi default pattern:

```text
Weekday:
Breakfast  1 người
Lunch      1 người
Dinner     2 người

Weekend:
Breakfast  2 người
Lunch      2 người
Dinner     2 người
```

Calendar có exception như `OUTSIDE`, `SKIP`, `LEFTOVER`, thêm guest/participant sau này.

## 7.6 Generate flow

```text
Intent + Plan overrides
→ PlanPolicyResolver
→ MealParticipants resolver
→ Inventory reconcile snapshot
→ Retail/reference price snapshot
→ Recipe eligibility + grounded variants
→ Role-aware Pareto shortlist
→ Feasibility
→ Stage 1 Band/Economic solve
→ Stage 2 Human-utility solve
→ Local CulinaryAdjustmentPass
→ Independent validation
→ Quality metrics + provenance
→ Present plan
```

## 7.7 Result screen

- Budget amount/constraint + planned spend + `BudgetPressure` explanation.
- Nutrition: hiển thị zone/range và weekly centering, tránh fake precision.
- Inventory used + expiring value saved.
- Package/carryover/waste summary; phân biệt good carryover và risky carryover.
- Cooking batches, cooking events, weekday prep time.
- Shopping trips/product packages.
- Price confidence/fallback source.
- Local Swap, Re-optimize remaining week, Activate plan.

## 7.8 Today mode

- Meal tiếp theo + participants + portion guidance.
- “Nấu 2.8 servings: 1.8 dùng tối nay, 1.0 để trưa mai.”
- Item cần thaw/prep.
- Ingredient sắp hết hạn.
- Mark cooked/skipped/outside/swapped.
- Confirm actual servings để materialize inventory consumption.

# 8. Kiến trúc hệ thống

> **Architecture style:** Modular Monolith + PostgreSQL + OR-Tools CP-SAT. Worker path chỉ dùng khi latency/import workload cần. Không microservices ở V1.

```text
Web/PWA
  ↓
FastAPI Modular Monolith
  │
  ├── Identity
  ├── Households
  ├── Nutrition
  ├── Catalog
  ├── Recipes
  ├── Retail
  ├── Inventory
  ├── Policy Resolution
  ├── Planning
  ├── Shopping
  ├── Execution
  ├── Preferences
  └── Assistant
  │
  ├── PostgreSQL
  ├── OR-Tools CP-SAT
  ├── Redis/worker (optional path)
  ├── Object storage
  └── External AI providers (bounded)
```

## 8.1 Plan policy synthesis

`PlanningMode` enum bị loại khỏi canonical domain.

```text
UserPolicyDefaults
        +
CurrentWeekContext
        +
Explicit Budget Contract
        ↓
PlanPolicyResolver
   ├── NutritionPolicyEngine
   ├── EconomicPolicyResolver
   └── KitchenPolicyResolver
        ↓
ResolvedPlanPolicy (versioned snapshot)
```

### Canonical policy inputs

- `NutritionPrecision`: RELAXED / STANDARD / PRECISION.
- `CostPreference`: LOW / NORMAL / HIGH.
- `KitchenEffort`: MINIMAL / NORMAL / FLEXIBLE.
- `BudgetConstraint`: amount + SPEND_LIMIT / TARGET / NONE.
- `BudgetPressure`: system-derived metric; không phải preference.
- `DailyAvailability`: optional per-day/weekday/weekend cook envelope.

## 8.2 Vì sao modular monolith

- Planner cần consistent snapshot xuyên household, inventory, retail, recipes và policy.
- Domain boundary còn được tinh chỉnh; microservices tạo migration/contract cost quá sớm.
- Retail ingestion, image/OCR jobs hoặc optimizer worker có thể tách khi profiling chứng minh bottleneck.

## 8.3 Snapshot/reproducibility rule

Mỗi activated plan snapshot tối thiểu:

- planner_version + policy_version;
- resolved nutrition/economic/kitchen policy;
- tracked_member_id;
- participant schedule/portion factors;
- recipe_version + grounded bindings/quantities;
- selected price/package observation IDs hoặc ReferencePriceBook version;
- inventory lot snapshot/fingerprint;
- solver statuses/tolerance/relaxations.

# 9. Bounded contexts và domain model

| Context | Entities chính | Trách nhiệm |
|---|---|---|
| Identity | User, Session, Consent | Auth, account lifecycle, privacy. |
| Household | Household, HouseholdMember, Membership, PortionProfile | Ownership boundary, participants, shared defaults. |
| Nutrition | MemberNutritionProfile, NutritionPolicy, GoalPolicy | Guideline/goal/comfort rules cho tracked member. |
| Catalog | Ingredient, UnitConversion, NutritionFact | Canonical food identity/data. |
| Recipes | Recipe, RecipeVersion, RecipeIngredient, VariantRule | Culinary identity, versioning, authored flexibility. |
| Retail | Retailer, StoreRegion, RetailProduct, Package, Offer, PriceObservation, ReferencePriceBook | Retail truth/fallback/provenance. |
| Inventory | InventoryLot, InventoryEvent, InventoryPolicy, Reservation | Household stock, expiry, confidence, lifecycle. |
| Policy | UserPolicyDefaults, PlanIntentOverride, ResolvedPlanPolicy | Compile human intent thành deterministic planner policy. |
| Planning | PlanRequest, MealSchedule, PlannerRun, GroundedVariant, Plan | Solve, metrics, provenance, versioning. |
| Cooking | CookingBatch, BatchAllocation | Sản xuất batch và phân bổ sang consumption demand. |
| Shopping | ShoppingList, ShoppingItem, PurchaseEvent | Planned products/packages vs actual purchases. |
| Execution | MealExecution, ConsumptionEvent | Cook/skip/outside/actual servings. |
| Preferences | PreferenceSignal, PreferenceProfile | Declared + behavioral preference. |
| Assistant | Conversation, IntentParse, Explanation | NL interface ngoài trusted truth. |

## 9.1 Ownership rules

### Household-owned resources

- InventoryLots/InventoryEvents.
- Shopping lists/purchases.
- Plans and CookingBatches.
- Kitchen defaults.
- Budget defaults.

### Member-owned physiology/preferences

- Nutrition profile/body/goal.
- Allergy.
- Dietary restrictions.
- Personal preference signals.

Plan lưu `household_id` và `created_by_user_id`; ownership và actor không phải cùng khái niệm.

## 9.2 Household V1 boundary

V1 là **Household-First data model + Single Tracked Nutrition Member**.

```text
Plan
├── household_id
├── tracked_member_id
├── meal_schedule
├── policy_snapshot
└── participants per meal
```

Các shared diners ảnh hưởng ingredient demand, package, inventory và hard dietary compatibility nhưng không được optimizer bảo đảm individual macro targets.

## 9.3 MealParticipants là source of truth

```yaml
dinner:
  participants:
    - member_id: 1
      portion_factor: 1.0
      nutrition_role: TRACKED
    - member_id: 2
      portion_factor: 0.8
      nutrition_role: SHARED
```

Resolver tạo:

```text
attendance_scale = 1.8
participant_hard_constraints = intersection/union theo policy
```

`portion_factor` là estimate hành vi/sức ăn; nutrition target chỉ có thể gợi ý initial value, không tự động là ratio của mọi món.

## 9.4 ConsumptionDemand != CookingBatchProduction

```text
Monday dinner demand = 1.8 servings
Tuesday lunch demand = 1.0 serving

Monday batch production = 2.8 servings
  ├── allocate 1.8 → Monday dinner
  └── allocate 1.0 → Tuesday lunch
```

Attendance scaling bản thân là coefficient đã resolve; batch production/allocation vẫn là decision variables nếu planner tối ưu batch.

## 9.5 Shared meal compatibility V1

Nếu participant constraints xung đột, V1 shared meal chỉ dùng món thỏa tất cả hard constraints tương thích. V1 không tự tạo hai protein/starch allocation riêng cho từng member. Trường hợp cần individualized decomposition thuộc V2.

## 9.6 Core distinctions bắt buộc

- Ingredient != RetailProduct.
- RetailProduct != Package/Offer.
- Recipe != GroundedRecipeVariant != DishCandidate.
- Preference != Constraint.
- BudgetPressure != CostPreference != BudgetConstraint.
- Inventory projection != confirmed inventory truth.
- ConsumptionDemand != BatchProduction.
- Household ownership != member physiology.
- Planned cost != actual purchase cost.

# 10. Planner V4 - Band-First Optimization Architecture

## 10.1 Planner responsibility

Planner V4 không tìm “macro chính xác nhất”. Nó tìm một plan **an toàn/goal-compatible**, nằm trong vùng nutrition đáng tin cậy nếu có thể, rồi tối ưu economics và khả năng thực hiện mà không đánh đổi hard constraints.

## 10.2 Pipeline

```text
1. Resolve Household/TrackedMember/Participants
2. Resolve Plan Policy
3. Hard recipe/member eligibility
4. Inventory + retail/reference snapshot
5. Recipe Variant Grounding
6. Role-aware Pareto shortlist
7. Feasibility/diagnostics
8. Stage 1: Band + Structural Economics
9. Stage 2: Human Utility within tolerances
10. Local CulinaryAdjustmentPass
11. Independent validation
12. Materialize plan/provenance/explanation facts
```

## 10.3 NutritionPolicyEngine: 4-layer synthesis

Không dùng một công thức `target ± x%` cho mọi nutrient.

```text
1. Guideline / Eligibility policy
        ↓
2. Goal policy / goal-direction protection
        ↓
3. Resolution + temporal policy
        ↓
4. NutritionPrecision preference
        ↓
Resolved NutritionPolicy
```

### Policy types per nutrient

- `RANGE`: calories/fat/carbs khi phù hợp.
- `MINIMUM`: protein/fiber hoặc nutrient floor.
- `MAXIMUM`: khi có justified policy.
- `TARGET`: chỉ cho trường hợp thực sự cần point-like center; vẫn có comfort semantics.

### Energy layers

- Hard daily reasonableness/supported envelope.
- Daily Comfort Band: cho phép package/batch flexibility.
- Weekly Goal Envelope/Centering: bảo vệ hướng cut/maintain/gain và ngăn systematic edge-hugging.
- Stage-2 center drift/stability penalty: chọn nghiệm tự nhiên hơn khi economics tương đương.

Không dùng BMR như universal “minimum safe calorie intake”. Clinical/unsupported cases bị chặn bởi eligibility boundary.

## 10.4 NutritionResolutionEstimator

Comfort band không được hẹp vô lý so với granularity của serving/recipe catalog. Resolver ước lượng resolution từ:

- portion steps;
- discrete ingredient units;
- grounded candidate composition.

Package size không trực tiếp quyết định nutrition resolution.

Nếu catalog quá thô để đáp ứng comfort band, hệ thống không âm thầm nới goal-protection vô hạn; trả warning/data-resolution state hoặc advisor option.

## 10.5 Role-aware candidate generation

Smart Menu V3 score từng component với whole-meal target; Menuto không làm vậy.

Các role ví dụ:

```text
BREAKFAST_MAIN
STARCH_BASE
MAIN_PROTEIN
VEGETABLE
SOUP
SINGLE_DISH_MEAL
SUPPLEMENT
```

Mỗi role có scoring envelope riêng. Ví dụ `MAIN_PROTEIN` quan tâm protein/cost/fat; `VEGETABLE` không bị phạt vì thiếu protein của whole meal.

Candidate signals:

| Signal | Ý nghĩa |
|---|---|
| Role-aware nutrition contribution | Fit đúng vai trò trong meal composition. |
| Economic contribution | Marginal package/purchase impact. |
| Inventory/expiry rescue | Dùng đồ đang có, đặc biệt near-expiry. |
| Ingredient overlap | Reuse giữa meals/batches. |
| Preference | Declared + behavior signals. |
| Adherence | Prep/cook/equipment/ingredient complexity. |
| Retail confidence | Offer/package usable/fresh. |
| Diversity contribution | Protein/method/flavor/family coverage. |

Shortlist là union/Pareto frontier + diversity reserve; không cheapest-first fill cap.

## 10.6 Stage 0 — Hard feasibility

Hard constraints V1 gồm:

- participant allergies/exclusions/dietary constraints;
- supported nutrition/goal envelope;
- `SPEND_LIMIT` theo required deterministic procurement stress scenarios;
- inventory availability/expiry;
- package integer constraints;
- no negative/double-reserved stock;
- meal composition;
- planning availability/procurement evidence đáp ứng policy của request;
- recipe hard safety/compatibility rules.

## 10.7 Stage 1 — Comfort Band + Structural Economics

Decision model bao gồm cùng lúc:

- meal/candidate selection;
- package purchases;
- inventory allocations;
- batch production/allocation;
- shopping-day variables;
- carryover/waste classification.

Primary semantics:

1. Minimize normalized `ComfortBandViolation`.
2. Trong mức violation tốt nhất, minimize structural economic loss.

Economic loss concept:

```text
cash purchase
+ expired waste
+ risky/awkward carryover
+ procurement fragility penalty
+ optional shopping friction terms
```

Carryover không mặc định là xấu. Carryover penalty phụ thuộc value, expiry risk, likely reuse/consumption uncertainty và handling awkwardness. Gạo còn lại khác hoàn toàn 60g thịt tươi sắp hỏng.

### Big-M policy

Nếu benchmark chọn single-solve lexicographic scaling, hệ số M phải được suy ra từ mathematical upper bound của normalized economic score; không dùng arbitrary huge constant. Alternative implementation phải benchmark: hard comfort band → elastic fallback vs derived-M single solve.

## 10.8 Stage 2 — Human Utility Polish

Lock:

- band violation ở best/tolerance đã phê duyệt;
- economic score <= best + policy-derived economic tolerance.

Optimize:

- cooking effort/events;
- batching quality;
- diversity;
- preference;
- schedule fit;
- equipment/ingredient friction;
- center drift/daily stability;
- learned behavior signals khi có đủ data.

`EconomicTolerance` được compile từ BudgetConstraint + CostPreference + BudgetPressure, không chỉ từ một mode.

## 10.9 Budget semantics — `SPEND_LIMIT`, `TARGET`, `NONE`

Canonical budget contract:

```text
BudgetPolicy
├── amount
├── constraint_type: SPEND_LIMIT | TARGET | NONE
└── cost_preference: LOW | NORMAL | HIGH
```

System-derived `BudgetPressure` vẫn độc lập với contract/preference:

```text
BudgetPressure ≈ ReferenceFeasibleCost / UserBudget
```

### `SPEND_LIMIT`

Ý nghĩa: Menuto chỉ gắn nhãn **hard-feasible** khi basket vượt qua procurement-risk policy đã version hóa dưới mức user đặt. V1 không claim checkout guarantee.

Menuto không giả lập xác suất bằng `γ × spread`. Retail resolver tạo các **deterministic stress scenarios** có provenance, ví dụ:

```text
BASE
ADVERSE_WEIGHT
BACKUP
CATEGORY_STRESS
```

Global planner yêu cầu:

```text
for each required scenario s:
    BasketCost(s) <= Budget
```

Scenario set phụ thuộc purchase granularity, source confidence, fallback coverage và policy version. Các scenario phải là linear coefficients trước khi build CP-SAT.

Nếu `BASE <= Budget` nhưng một required stress scenario vượt budget:

```text
status = RELAXATION_AVAILABLE
```

Không được gắn nhãn `SPEND_LIMIT` feasible. Advisor có thể đề xuất:

- tăng cap tối thiểu đã verify;
- chấp nhận expected-only alternative;
- đổi retailer/procurement substitutions;
- đổi meal candidates để hạ fragility/cost.

User phải explicit accept nếu chọn alternative đã relax.

### `TARGET`

Menuto tối ưu expected/planning spend quanh amount với soft penalty/tolerance. Actual shopping có thể dao động; UI không dùng ngôn ngữ guarantee.

### `NONE`

Không có budget constraint; cost vẫn là objective/quality signal nếu policy yêu cầu.

### Budget outcome states

- `WITHIN_LIMIT_ROBUST`: mọi required stress scenario đều nằm trong `SPEND_LIMIT`.
- `EXPECTED_WITHIN_LIMIT_ONLY`: chỉ `BASE`/expected nằm trong limit; đây là relaxation candidate, không phải hard-feasible plan.
- `EXPECTED_OVER_LIMIT`: base/expected cũng vượt limit.
- `DATA_INSUFFICIENT_FOR_LIMIT`: evidence không đủ để áp policy đáng tin cậy.

### UI rule

Consumer UI có thể hiển thị:

> **Chi phí dự kiến: ~660.000đ / giới hạn 700.000đ**  
> Menuto đã chừa một biên mua sắm cho chênh lệch giá/khối lượng theo dữ liệu hiện có.

Không hiển thị `P90`, `σ`, `Γ` hoặc probability jargon nếu chưa có calibrated model.

## 10.10 Kitchen policy

`KitchenEffort` là default, không phải toàn bộ schedule.

Support:

- weekday/weekend max-prep envelope;
- optional per-day availability;
- batch preference;
- ingredient/equipment friction;
- cooking-event penalty.

V1 UI có thể chỉ hỏi weekday/weekend; domain giữ room cho daily overrides.

## 10.11 Solver outcome semantics

Mọi solve/run/phase phải tách rõ:

- OPTIMAL;
- FEASIBLE_BEST_EFFORT;
- TIME_LIMIT_WITH_INCUMBENT;
- PROVEN_INFEASIBLE;
- UNKNOWN/ERROR.

Không được dùng timeout/UNKNOWN làm bằng chứng để relax constraint.

## 10.12 Reference benchmark

Reference configuration dùng candidate pool lớn hơn + timeout dài hơn để ước lượng quality gap. V1 shortlist/2-stage policy chỉ được accept khi runtime/quality regression nằm trong threshold định nghĩa trước.

# 11. Feasibility, relaxation và explainability

## 11.1 Feasibility V2

Feasibility precheck phải conservative: chỉ hard-reject khi lower/upper bound đáng tin cậy. Không lặp lỗi Smart Menu V3 tính minimum budget mà bỏ qua inventory/package reality.

Precheck nhóm:

- candidate/role coverage;
- participant hard compatibility;
- nutrition reachability/band reachability;
- budget/package lower bound có xét inventory;
- retail/reference-data sufficiency;
- inventory window/expiry impossibility;
- catalog granularity/resolution issue.

## 11.2 Constraint Relaxation Advisor — 3 bước

Không coi một weighted slack result là “chính xác cần thêm đúng X đồng”.

```text
A. Conflict identification
        ↓
B. Elastic estimate
        ↓
C. Verify each proposed relaxation
        ↓
User-visible options
```

### A. Conflict identification

Nhóm negotiable constraints dùng assumptions/reason groups khi implementation/library version cho phép đáng tin cậy. Kết quả là “sufficient conflict set”, không mặc định là minimal unsat core.

Ví dụ:

```text
conflict candidates:
- budget hard cap
- protein goal floor
- no-chicken constraint
```

### B. Elastic estimate

Chỉ soften nhóm liên quan để tìm candidate relaxation:

- +budget;
- reduced goal floor;
- allow one excluded preference (never allergy);
- reduce strict diversity;
- relax kitchen time.

### C. Verification

Mỗi suggestion phải được chạy lại với **một thay đổi được đề xuất + các constraint gốc còn lại**. Chỉ suggestion verified feasible mới hiển thị như action.

Ví dụ UI:

```text
Không thể tạo plan trong 700k với cấu hình hiện tại.

Có thể thử:
[ Tăng trần lên 775k ]
[ Giữ 700k, giảm protein goal xuống X ]
[ Giữ nutrition, cho phép thêm 1 bữa gà ]
```

## 11.3 Explainability facts

Explanation chỉ dùng verified data:

- plan nằm trong/ngoài Comfort Band ở đâu;
- weekly goal centering;
- budget constraint và price confidence;
- packages được chọn và tại sao có carryover;
- inventory near-expiry đã cứu;
- batch production/allocation;
- constraint/tolerance nào đã được user chấp nhận nới.

LLM có thể diễn đạt, không tạo facts mới.

# 12. Retail, product và pricing architecture

## 12.1 Four-layer retail truth model

```text
Ingredient
   ↓ mapping / AP→EP
RetailProduct
   ↓ observed at retailer/region/time
RetailOffer / PriceObservation
   ↓ normalization + evidence evaluation
ProcurementClass / PlanningProcurementOption
   ↓
Global Planner
   ↓
Concrete Primary + Backup Offers
```

`RetailProduct` là product/SKU identity. `RetailOffer` là observation có thời gian/retailer/store/region. `ProcurementClass` là planning abstraction ổn định hơn mà solver sử dụng mặc định.

## 12.2 Core entities

| Entity | Fields tối thiểu |
|---|---|
| Retailer | id, name, country, currency, status |
| StoreRegion | retailer_id, region_code, fulfillment/store scope |
| RetailProduct | sku/barcode, name, brand, category, declared pack metadata, mapping status |
| RetailOffer / PriceObservation | product/package, retailer/store scope, observed price, promo, observed_at, availability evidence, source quality |
| IngredientProductMap | ingredient_id, product_id, AP→EP edible_yield/conversion, confidence, reviewed_at |
| ProcurementClass | ingredient, granularity_type, nominal/low/high quantity or min/step, eligible offer set, resilience metadata |
| PlanningPriceQuote | procurement_class, planning price, range/evidence, confidence, policy_version, provenance |
| PlanningAvailability | CONFIRMED/LIKELY/UNKNOWN/UNAVAILABLE + provenance |
| ReferencePriceBook | region/category/ingredient proxy, version, amount/range, confidence, updated_at |
| RetailPriceCalibration | retailer × region × category index, evidence_count, confidence, version |

## 12.3 Purchase granularity types

### `FIXED_PACK`

Industrial/fixed package: 10 eggs, tofu 300g, milk 1L. Package quantity can be treated as exact within declared data quality.

### `CATCH_WEIGHT`

Fresh trays/items with variable weight. Model:

```text
expected_qty
qty_low
qty_high
price_per_weight / quote
```

Shortage protection uses plausible lower usable quantity where relevant; carryover/waste evaluation uses plausible upper quantity. Catch-weight uncertainty is not silently reduced to a fixed 500g package.

### `LOOSE_SCALE`

Items purchased by weight/count with `min_purchase_qty` and `step_qty`/count step. Do not invent a fake fixed pack when the retailer permits variable purchase.

## 12.4 AP→EP and cooking yield

- `edible_yield_factor` belongs to Product→Ingredient mapping: as-purchased quantity → usable raw ingredient.
- `cooking_yield_factor` belongs near recipe/preparation transformation because it depends on cooking method/process.

## 12.5 ProcurementClass policy

Global Planner does **not** optimize directly over isolated brand SKU by default. Exact SKU remains evidence/fulfillment data.

A `ProcurementClass` groups reasonably equivalent purchasing options and exposes solver-ready coefficients:

```yaml
ingredient: chicken_breast
granularity: CATCH_WEIGHT
qty_expected_g: 500
qty_low_g: 450
qty_high_g: 550
planning_price: 50000
availability: LIKELY
price_confidence: HIGH
substitution_coverage: HIGH
fragility: LOW
```

Exception: an exact SKU may become a fixed/committed input when the user already bought it, reserved it, or a retailer cart locks price/stock.

## 12.6 Price evidence and planning quote

Raw observation is not the same thing as planning price.

```text
PriceObservation
      ↓
Offer Normalizer
      ↓
PriceEvidenceScore
      ↓
PlanningPriceQuote
```

Evidence evaluation must consider more than freshness:

- source quality;
- age/freshness;
- sample/offer coverage;
- price dispersion;
- promo/outlier status;
- availability confidence;
- mapping/equivalence quality.

Flash sale/outlier price may be shown as possible upside but must not become the foundation of a `SPEND_LIMIT` plan unless policy explicitly justifies it.

## 12.7 ReferencePriceBook fallback and calibration

No fake “Menuto Market”. Reference data is explicit fallback evidence.

Price provenance examples:

```text
LIVE_RETAIL
RECENT_RETAIL
CALIBRATED_REFERENCE
REFERENCE_BASELINE
USER_RECORDED
RECEIPT_ACTUAL
```

When retailer-specific data is missing, baseline may be adjusted using hierarchical `RetailPriceCalibration`:

```text
retailer × region × category
    ↓ if weak sample
retailer × region
    ↓
regional reference baseline
```

Category calibration with little evidence must shrink/blend toward broader index rather than overfit a noisy multiplier.

## 12.8 Procurement resilience / fragility

A cheapest basket is not automatically the best basket. `ProcurementFragility` may depend on:

- single-source SKU dependence;
- promotion dependence;
- substitution coverage;
- availability confidence;
- evidence quality;
- package-size brittleness.

Stage 1 structural economics may include `FragilityPenalty` in addition to purchase/waste/carryover cost.

## 12.9 Stress-scenario builder for `SPEND_LIMIT`

V1 uses deterministic stress scenarios rather than pretending a heuristic score is a calibrated probability.

Scenario families can include:

- `BASE`: planning quote + expected/nominal quantities;
- `ADVERSE_WEIGHT`: plausible unfavorable catch-weight quantities/prices;
- `BACKUP`: primary offer unavailable, common backup used;
- `CATEGORY_STRESS`: policy-defined correlated uplift for a category/store exposure.

Only scenario sets justified by evidence/policy are required. Every scenario and coefficient is snapshot/versioned for reproducibility.

## 12.10 ShoppingRequirement: primary + backups

Shopping output is structured, not a frozen text SKU:

```text
ShoppingRequirement
├── ingredient / required usable quantity
├── accepted ProcurementClass
├── primary_offer
├── backup_offers[]
├── price/provenance facts
├── max acceptable price guidance (when derived)
└── substitution rules
```

UI example:

> **Ức gà phi lê — 1 khay khoảng 450–550g**  
> Gợi ý chính: offer phổ biến phù hợp hiện tại.  
> Có thể chọn nhãn tương đương trong class; Menuto hiển thị provenance và mức giá tham chiếu thay vì giả vờ SKU luôn còn hàng.

## 12.11 Actual checkout learning

`RECEIPT_ACTUAL`/user-confirmed purchase events are valuable for:

- planned vs actual cost;
- retailer/category calibration;
- fallback bias;
- empirical coverage of future risk policies.

Menuto chỉ được dùng language kiểu `P90/~90%` sau khi model đã được calibrated/backtested trên actual outcomes đủ tin cậy.

# 13. Inventory và food lifecycle

## 13.1 Household-scoped InventoryLot

| Field | Mục đích |
|---|---|
| household_id | Ownership boundary. |
| ingredient_id / product_id | Canonical ingredient + retail provenance nếu biết. |
| quantity_remaining + unit | Tồn materialized. |
| available_from | Current/future delivery/purchase. |
| expires_on / best_before | Expiry scheduling. |
| storage_mode | room / fridge / freezer / same_day. |
| cost_basis | Waste/carryover valuation. |
| source | manual / purchase / carryover / receipt. |
| status | projected / available / reserved / consumed / expired / discarded. |
| confidence | CONFIRMED / PROJECTED / STALE / UNKNOWN. |

## 13.2 InventoryPolicy

Không bắt user track mọi gia vị như database admin.

```text
TRACK_EXACT
ASSUME_AVAILABLE
OPTIONAL_TRACK
PURCHASE_ALWAYS
```

Ví dụ salt/fish sauce có thể `ASSUME_AVAILABLE`, chicken/eggs `TRACK_EXACT`.

Policy là household/user configurable và phải được snapshot nếu ảnh hưởng plan.

## 13.3 Ledger/events

Không cần full event-sourcing framework, nhưng mutation tạo immutable audit/event records:

- PURCHASE;
- CONSUME;
- ADJUST;
- DISCARD/EXPIRE;
- STORAGE_TRANSFER;
- RECONCILE.

`quantity_remaining` là materialized state có optimistic concurrency.

## 13.4 One-tap Reconcile

Trước generate, projected/stale inventory phải được user confirm nhanh. Reconcile làm tăng confidence và sửa projected reality trước snapshot.

## 13.5 Good carryover vs bad carryover

Không phạt mọi ending inventory.

Carryover quality xét:

- shelf-life/expiry risk;
- quantity/value;
- future consumption likelihood;
- storage practicality;
- awkwardness.

Long-life staple carryover có thể gần như neutral; 60g fresh meat gần hết hạn có penalty cao.

## 13.6 V1 input UX

- manual quick-add;
- purchase-derived lots;
- carryover-derived projected lots;
- reconcile.

V1.5+: barcode/receipt/photo chỉ là input accelerator, tất cả normalize về cùng ledger contract.

# 14. Recipe architecture, cooking batch và adherence

## 14.1 Recipe identity vs grounded candidate

```text
Recipe
  ↓ version
RecipeVersion
  ↓ authored flexibility
RecipeVariantRule / RecipeIngredient
  ↓ runtime grounding
GroundedRecipeVariant
  ↓ planner contract
DishCandidate
```

Recipe là identity/procedure; GroundedVariant là một binding cụ thể đã resolve ingredients/quantities/nutrition/cost/yield; DishCandidate là planner-facing immutable candidate.

## 14.2 Bounded Culinary Template

Recipe không static 100%, nhưng flexibility phải curated:

- fixed ingredients;
- contextual substitution slots;
- portion/quantity envelopes;
- scaling policy;
- adjustment policy;
- compatibility rules.

Không tồn tại global substitute table kiểu “chicken ↔ pork ↔ tofu” áp vô hướng cho mọi recipe.

## 14.3 CookingMethod rule

Đổi kỹ thuật nấu tạo Recipe khác. Boiled chicken, pan-fried chicken và braised chicken không phải variants của cùng một Recipe vì instructions, equipment, oil, time, yield và texture thay đổi.

## 14.4 Pre-Solve Grounding invariant

Global planner chỉ nhận candidate đã grounded:

```text
RecipeVersion
+ Inventory snapshot
+ Retail/reference offers
+ Exclusions
+ Nutrition role needs
        ↓
VariantGenerator
        ↓
CulinaryValidator
        ↓
Nutrition/Cost/Yield resolver
        ↓
Grounded DishCandidate
```

Mỗi candidate có `variant_reason`:

```text
DEFAULT
INVENTORY_MATCH
EXPIRY_RESCUE
PRICE_ADVANTAGE
NUTRITION_FIT
PACKAGE_FIT
```

Explainability có thể dùng reason trực tiếp mà không cần LLM suy đoán.

## 14.5 Demand-driven variant generation

Không materialize Cartesian product.

Một recipe runtime chỉ spawn vài variants dựa trên signals:

- default;
- near-expiry inventory match;
- strong price advantage;
- nutrition/portion tier;
- explicit package-fit tier.

Template có thể định nghĩa nhiều rules nhưng V1 mỗi generated variant chỉ activate tối đa một **structural substitution** trừ khi combination được explicitly approved.

## 14.6 Quantity policies

`RecipeIngredient` hỗ trợ:

```text
ScalingPolicy:
LINEAR
SUBLINEAR
FIXED
DISCRETE
TO_TASTE

QuantityAdjustmentPolicy:
NONE
SMALL
PORTIONABLE
DISCRETE
```

Kèm min/max/step hoặc absolute delta. Không dùng một `±15%` global cho mọi ingredient.

## 14.7 Package-fit strategy

Không cho free-form `CulinaryAbsorptionSlack` trong global solver.

### Level 1 — Grounded portion tiers

Các tier có ý nghĩa sản phẩm, ví dụ `STANDARD`, `HIGH_PROTEIN`, `SMALL`, được materialize trước solve khi signal cần.

### Level 2 — Global solve

Recipes/quantities của candidate immutable. Solver chọn meal structure, packages, inventory, batch.

### Level 3 — CulinaryAdjustmentPass

Sau global solve, freeze meal structure và dùng bounded local refinement để hấp thụ **awkward residuals** nếu recipe envelopes cho phép.

Ví dụ:

```text
2 × 220g chicken selected = 440g
package = 500g
residual = 60g
```

Local pass có thể điều chỉnh +30g/+30g nếu nằm trong authored envelope; sau đó recompute nutrition/batch và independent validator chạy lại.

Không phải mọi remainder cần absorb. `RemainderDisposition` có thể là:

```text
KEEP
USE_NEXT_WEEK
ABSORB
REPURPOSE
WASTE_RISK
```

## 14.8 Recipe versioning

Plan snapshot:

- recipe_version_id;
- resolved bindings;
- resolved quantities;
- grounded fingerprint;
- instructions/version.

Catalog edit sau này không được làm thay đổi plan lịch sử.

## 14.9 CookingBatch

CookingBatch là production entity, không chỉ repeat dish marker.

```text
CookingBatch
├── recipe/grounded variant
├── produced_quantity
├── production_time
└── BatchAllocation[] → meal consumption demands
```

`CookingEffort` khác `MealRepetition`: nấu một lần ăn hai bữa có thể desirable dù recipe xuất hiện hai lần.

## 14.10 Adherence score

```text
adherence_score =
  time_fit
+ equipment_fit
+ complexity_fit
+ ingredient_count_fit
+ batch_fit
+ schedule_fit
+ behavioral_acceptance
- recent_rejection_penalty
```

V1 dùng heuristic/versioned policy. Learned ranking chỉ sau khi có đủ event volume + offline evaluation.

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

| Layer | V1 |
|---|---|
| Language | Python 3.13.x, pin minor/runtime image |
| API | FastAPI + Pydantic v2 |
| Persistence | SQLAlchemy 2 + PostgreSQL |
| Migrations | Alembic hoặc một migration runner duy nhất |
| Optimizer | OR-Tools CP-SAT **pin exact tested version** |
| Async jobs | Redis + worker khi interactive budget không đủ |
| Object storage | S3-compatible |
| Observability | Structured logs/traces/error tracking |
| AI | Provider abstraction + structured outputs |

Không dùng loose dependency kiểu `ortools>=9`; optimizer/version phải reproducible và benchmarked trước upgrade.

## 16.2 Frontend stack đề xuất

| Layer | Lựa chọn |
|---|---|
| Web/PWA | React + TypeScript; Next.js nếu cần SSR/marketing/unified shell |
| Data fetching | Typed API client + query cache |
| Forms | Schema-driven + progressive disclosure |
| Design system | Reusable tokens/components |
| Mobile | Chưa bắt buộc V1; API mobile-ready |

## 16.3 API principles

- Household ownership + actor identity explicit.
- `PlanRequest` không nhận raw “PlanningMode”.
- Canonical participant input là IDs/portion factors/schedule; attendance scale là resolved field.
- Explicit planner_version/policy_version/source_snapshot IDs.
- Structured reason/error codes.
- Long solve có run_id/status khi async.
- Optimistic concurrency cho inventory.
- Activated plan immutable về critical snapshots; changes tạo revision/new run.

## 16.4 Repository layout

```text
menuto/
├── apps/
│   ├── web/
│   └── backend/
│       ├── app/
│       │   ├── modules/
│       │   │   ├── identity/
│       │   │   ├── households/
│       │   │   ├── nutrition/
│       │   │   ├── catalog/
│       │   │   ├── recipes/
│       │   │   ├── retail/
│       │   │   ├── inventory/
│       │   │   ├── policy/
│       │   │   ├── planning/
│       │   │   ├── cooking/
│       │   │   ├── shopping/
│       │   │   ├── execution/
│       │   │   ├── preferences/
│       │   │   └── assistant/
│       │   └── shared/
│       ├── tests/
│       └── workers/
├── packages/
│   └── contracts/
├── benchmark/
├── data/
│   ├── seeds/
│   └── imports/
├── docs/
│   ├── adr/
│   ├── product/
│   └── api/
└── infra/
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

## 20.1 Milestone 0 — Architecture lock + benchmark foundation

- Repo sạch + coding/CI conventions.
- Domain glossary và invariants V1.2.
- Publish canonical ADR-001..ADR-008 + Architecture Invariants.
- Smart Menu benchmark fixtures port sang neutral scenario format.
- Pin Python/OR-Tools toolchain và reproducibility policy.

## 20.2 Milestone 1 — Household/Data foundation

- Identity + default household/member creation.
- Member nutrition/diet/allergy profile schema.
- MealParticipants/meal schedule defaults.
- Ingredient + nutrition catalog.
- RecipeVersion + RecipeIngredient + VariantRule.
- RetailProduct/Offer + ProcurementClass + PlanningPriceQuote + ReferencePriceBook + RetailPriceCalibration.
- Household inventory lot/events/policy/reconcile.

## 20.3 Milestone 2 — Policy engines

- NutritionPolicyEngine 4-layer synthesis.
- NutritionResolutionEstimator.
- BudgetPolicy/CostPreference/BudgetPressure resolver + `SPEND_LIMIT` contract.
- KitchenPolicy resolver + weekday/weekend availability.
- ResolvedPlanPolicy version/snapshot tests.

## 20.4 Milestone 3 — Planner V4 global core

- Grounded Variant Generator.
- Role-aware Pareto shortlist.
- Conservative Feasibility V2.
- Stage 1 Band + Structural Economics.
- Package/procurement/inventory/batch model + deterministic budget stress scenarios.
- Stage 2 Human Utility.
- Independent validator.
- Reference benchmark/quality-gap report.

## 20.5 Milestone 4 — Refinement + advisor

- CulinaryAdjustmentPass.
- Constraint conflict/elastic/verification advisor.
- Local Swap vs Re-optimize Remaining Week separated.
- Explainability facts/provenance.

## 20.6 Milestone 5 — Consumer V1

- Onboarding without PlanningMode.
- Situational plan chips.
- One-tap inventory reconcile.
- Household meal participation defaults.
- Result Quality Summary.
- Shopping list/product packages.
- Today mode + batch/leftover execution.
- AI parse/explain bounded by deterministic facts.

## 20.7 Milestone 6 — Public readiness

- Security/privacy/eligibility review.
- Retail evidence/provenance, ProcurementClass, calibration and stress-scenario policy.
- Data-quality coverage matrix.
- Performance/load/timeout behavior.
- Accessibility/responsive QA.
- Backup/restore/migration rollback.
- Launch feature flags/rollback.

## 20.8 V1.5

- Barcode/receipt-assisted inventory.
- Better per-day schedule context.
- Household-lite sharing/collaboration.
- More retailer adapters.
- Leftover execution refinement.
- Behavioral preference ranking.
- Limited/bounded recipe import drafts.

## 20.9 V2

- Full multi-member individual nutrition + component allocation.
- Multi-retailer split-basket optimization.
- Native mobile if retention supports it.
- Camera inventory assistant.
- Long-horizon carryover planning.
- Robust nutrition optimization only when uncertainty metadata is sufficient.
- Learned ranking/personalization after offline evaluation maturity.

# 21. Backlog triển khai ưu tiên

| ID | Priority | Epic / Issue | Acceptance criteria tóm tắt |
|---|---|---|---|
| MTR-001 | P0 | Domain glossary + invariants | Canonical V1.2 distinctions/invariants mirrored in tests/docs. |
| MTR-002 | P0 | Benchmark harness | Scenario matrix + objective vector + runtime/status + reference config. |
| MTR-003 | P0 | Household-first schema | Default household/member; household-owned resources; actor fields. |
| MTR-004 | P0 | MealParticipants model | Participant IDs + portion factors + hard constraint resolution + derived scale. |
| MTR-005 | P0 | NutritionPolicyEngine | Guideline/goal/comfort/weekly policy; no BMR-as-safety shortcut. |
| MTR-006 | P0 | NutritionResolutionEstimator | Catalog/portion granularity reporting; no silent unbounded widening. |
| MTR-007 | P0 | PlanPolicyResolver | NutritionPrecision, CostPreference, KitchenEffort, BudgetContract compiled independently. |
| MTR-008 | P0 | Budget baseline/pressure | ReferenceFeasibleCost pressure distinct from preference/contract. |
| MTR-009 | P0 | Retail evidence schema | RetailProduct/Offer/provenance/source-quality/availability evidence. |
| MTR-010 | P0 | ProcurementClass builder | FIXED_PACK/CATCH_WEIGHT/LOOSE_SCALE + coverage/fragility metadata. |
| MTR-011 | P0 | PlanningPriceQuote + calibration | RetailPriceCalibration retailer×region×category with confidence/shrinkage. |
| MTR-012 | P0 | SPEND_LIMIT stress scenarios | BASE/ADVERSE_WEIGHT/BACKUP/CATEGORY_STRESS snapshot + linear constraints. |
| MTR-013 | P0 | AP→EP mapping | Edible yield at Product→Ingredient; cooking yield in recipe layer. |
| MTR-014 | P0 | Inventory ledger + policy | Household lots/events/policy/confidence/reconcile. |
| MTR-015 | P0 | Recipe version/variant schema | Contextual substitution + quantity/scaling/adjustment policies. |
| MTR-016 | P0 | Grounded Variant Generator | Demand-driven variants; immutable nutrition/cost/yield; reason/fingerprint. |
| MTR-017 | P0 | Role-aware Pareto shortlist | No cheapest starvation; per-role scoring; reference-gap test. |
| MTR-018 | P0 | Feasibility V2 | Inventory/procurement/participant aware; data insufficiency != infeasible. |
| MTR-019 | P0 | Stage 1 global optimizer | Comfort violation + structural economics + fragility + package/inventory/batch. |
| MTR-020 | P0 | CookingBatch model | Production/allocation separate from attendance/meal demand. |
| MTR-021 | P0 | Stage 2 human utility | Economic tolerance + adherence/diversity/schedule/center drift. |
| MTR-022 | P0 | Independent validator | Separate validation path for nutrition/budget scenarios/inventory/batch/recipe snapshots. |
| MTR-023 | P0 | Planner API v1 | Versioned policy/source/scenario snapshots + structured statuses/reasons. |
| MTR-024 | P0 | Consumer onboarding | No PlanningMode; life questions; budget contract wording; household defaults. |
| MTR-025 | P0 | Plan Quality Summary | Nutrition zone, budget status, provenance, inventory, waste, batch, fragility. |
| MTR-026 | P1 | CulinaryAdjustmentPass | Freeze meal structure; bounded quantity refinement; revalidate. |
| MTR-027 | P1 | Relaxation Advisor | Conflict → elastic estimate → verified proposals; no silent hard relaxation. |
| MTR-028 | P1 | Local Swap | Freeze unaffected meals; recompute procurement/nutrition/scenarios/validator. |
| MTR-029 | P1 | Re-optimize remaining week | Freeze executed/past state; use current inventory/purchases. |
| MTR-030 | P1 | Shopping requirement resolver | Primary + backups + price/provenance + accepted procurement class. |
| MTR-031 | P1 | Today mode | Participants, batch/leftover guidance, prep/expiry, execution actions. |
| MTR-032 | P1 | Inventory reconcile UI | Confirm/edit stale/projected inventory in seconds. |
| MTR-033 | P1 | Price/provenance UX | Retail vs calibrated reference vs baseline clearly distinguished. |
| MTR-034 | P1 | AI intent/explanation | Structured intent + verified metrics only. |
| MTR-035 | P1 | Telemetry/feedback | plan/swap/cook/purchase/waste/reconcile/actual-price events with privacy review. |
| MTR-036 | P1 | Catalog coverage matrix | Role/protein/style/quick/high-protein coverage + planner-ready completeness. |
| MTR-037 | P1 | Receipt-vs-plan calibration dataset | Store planned quote/scenario outcomes vs actual checkout for later risk calibration. |
| MTR-038 | P2 | Barcode/receipt import | Reviewable mapping to InventoryLot/PurchaseEvent/RECEIPT_ACTUAL. |
| MTR-039 | P2 | Household-lite collaboration | Shared household UI/permissions, no individualized solver yet. |
| MTR-040 | P2 | Recipe import | Reviewable RecipeVersion draft; no auto-trust facts. |

# 22. Smart Menu → Menuto reuse/migration matrix

| Smart Menu capability | Action | Menuto decision |
|---|---|---|
| Nutrition calculator/domain | PORT FORMULAS/TESTS SELECTIVELY | Do not port old objective semantics; feed NutritionPolicyEngine instead. |
| CandidateSelector V3 | REWRITE | Replace cheapest-first/per-dish whole-meal scoring with role-aware grounded Pareto generation. |
| Optimizer V3 | REFERENCE + EXTRACT IDEAS | Keep procurement/inventory modeling lessons; write new 2-stage model/contracts. |
| Feasibility V3 | REWRITE | Conservative, inventory/package/participant-aware. |
| Procurement checker/validator | PORT CONCEPT, DUAL IMPLEMENT | Independent validation remains mandatory. |
| Inventory lots/reservations | PORT DOMAIN CONCEPTS | Move ownership to household; add policy/confidence/events/reconcile. |
| price_snapshots | REPLACE | RetailProduct/Offer evidence + ProcurementClass + PlanningPriceQuote + ReferencePriceBook. |
| Shopping list | PORT UX/CONCEPT | Product/package-aware and household-owned. |
| Share token | PORT LATER | Useful but not core V1 architecture. |
| CreateMenu UI | REDESIGN | No PlanningMode; policy inferred from life questions + situational chips. |
| MenuResult explain/swap | PORT UX CONCEPTS | Split Local Swap vs Re-optimize remaining week; richer verified facts. |
| AI provider abstraction | PORT | Keep structured/bounded boundary. |
| Admin catalog QA | EXPAND | RecipeVersion/variant QA + retail provenance + coverage matrix. |
| QualityPolicy enum/weights | REPLACE | Explicit versioned Nutrition/Economic/Kitchen policies. |
| Planner tests/fixtures | PORT AGGRESSIVELY | Convert to neutral benchmark scenarios; add household/package/band cases. |

# 23. Definition of Done và launch gate

## 23.1 Planner DoD

- Independent validator không có hard violation.
- Timeout/UNKNOWN không bao giờ bị trình bày như proven infeasible.
- Comfort/goal policy semantics được snapshot/versioned.
- Weekly centering/goal direction được giữ theo policy.
- `SPEND_LIMIT` hard-feasible status chỉ khi mọi required deterministic stress scenario pass.
- Participant allergy/diet hard constraints được giữ sau aggregation.
- CookingBatch production/allocation cân bằng với consumption demand.
- Grounded candidate không bị global solver mutate ingredient identity/quantity.
- CulinaryAdjustmentPass chỉ dùng authored envelope và phải revalidate.
- Shortlist/global plan quality gap vs reference nằm trong threshold phê duyệt.

## 23.2 Data DoD

- Planner-ready ingredient có nutrition provenance/status.
- Planner-ready recipe có RecipeVersion + ingredient quantities + roles + instructions.
- Mọi variant rule contextual và QA-able; không global substitution mù.
- Retail market hỗ trợ có RetailProduct/Offer evidence và ProcurementClass/PlanningPriceQuote hoặc explicit ReferencePriceBook fallback.
- Price/reference source có timestamp/version/provenance/source quality; planning quote/scenario policy được snapshot.
- Shelf-life thiếu không bị silent-assume khi ảnh hưởng procurement/waste.
- Household/member ownership constraints có integration tests.

## 23.3 Catalog launch gate

Không dùng “>=200 recipes” làm metric duy nhất. Dùng coverage matrix theo:

- breakfast/main protein/vegetable/soup/starch/single-dish roles;
- protein families;
- quick weekday recipes;
- high-protein options;
- dietary coverage của target market;
- complete nutrition/quantity/procurement readiness.

Recipe count là kết quả của coverage, không phải mục tiêu độc lập.

## 23.4 Consumer launch gate

- Onboarding/generate/shop/today responsive + accessible.
- Inventory reconcile nhanh, rõ projected vs confirmed.
- Result không hiển thị fake precision (ví dụ 1,987 kcal như exact truth nếu policy/data không justify).
- Retail offer vs calibrated reference vs baseline provenance dễ phân biệt; không fake checkout certainty.
- Unsupported health/clinical request trả bounded message, không tự tính therapeutic plan.
- Structured errors/reasons có copy user-friendly.
- Privacy export/delete workflow.
- Operational dashboards cho error/timeout/infeasible/data-quality.
- No critical/high security findings mở.
- Backup/restore + migration rollback đã test.

# 24. ADR registry, risks và open decisions

## 24.1 Canonical ADRs published with V1.2

| ADR | Status | Canonical decision |
|---|---|---|
| ADR-001 Band-First Planner | ACCEPTED | Stage 0 hard feasibility; Stage 1 comfort/structural economics; Stage 2 human utility; bounded local refinement. |
| ADR-002 Nutrition Policy Engine | ACCEPTED | Guideline → Goal → Resolution/Temporal → NutritionPrecision; no universal point-target/BMR safety shortcut. |
| ADR-003 Plan Policy Resolution | ACCEPTED | No canonical PlanningMode; orthogonal nutrition/cost/kitchen policy + explicit budget contract. |
| ADR-004 Household-First Model | ACCEPTED | Household owns shared resources; member owns physiology; one TrackedMember in V1; participants source-of-truth. |
| ADR-005 Grounded Recipe Variants | ACCEPTED | Authored flexibility → grounded immutable candidates; local adjustment only after global selection. |
| ADR-006 Retail Procurement Abstraction | ACCEPTED | Retail evidence → ProcurementClass → PlanningQuote → concrete primary/backups; SKU-direct is not default. |
| ADR-007 SPEND_LIMIT Robustness | ACCEPTED | Deterministic stress scenarios; no uncalibrated P90; relaxed alternatives require explicit acceptance. |
| ADR-008 No Silent Relaxation | ACCEPTED | Hard constraint relaxations are separately labeled, verified and user-accepted before activation. |

Published files live under `docs/adr/`. The implementation must reference the ADR ID in PRs that alter a canonical decision.

## 24.2 Core risks

| Risk | Impact | Mitigation |
|---|---|---|
| Retail data stale/unavailable | Very high | Provenance, ProcurementClass, calibration, reference fallback, stress scenarios, explicit UX. |
| False checkout certainty | Very high | `SPEND_LIMIT` semantics + invariant INV-010/011; no probability claim before calibration. |
| Solver model growth | High | Grounded candidate caps, Pareto shortlist, 2-stage solve, local refinement, benchmark. |
| Recipe variant explosion | High | Demand-driven grounding, one structural substitution/variant V1, compatibility rules. |
| “Mathematically optimal, culinarily weird” | Very high | Authored flexibility + culinary validator + immutable candidates. |
| Inventory diverges from kitchen reality | High | Confidence state + one-tap reconcile + execution events. |
| Household aggregation hides allergy | Critical | Participants source-of-truth + member hard constraint resolution. |
| Nutrition overclaims precision | High | Band-based UI, eligibility boundary, provenance, no fake medical certainty. |
| Budget inference overrides user intent | Medium-high | Separate Pressure/Preference/Contract. |
| V1 grows into multi-member macro solver | High | Explicit non-goal + schema prepared for V2. |
| Build too much before PMF | High | V1 gates, non-goals, milestone sequencing. |

## 24.3 Open architecture questions after V1.2

The following are intentionally **not** locked by V1.2:

1. **Execution State Machine:** shopping partially completed, actual quantities/prices, skips/eat-out, expiry drift, projected→confirmed inventory and remaining-week adaptation.
2. **Independent Validator V2 architecture:** how far validator extends beyond generated plan to local refinement, swaps, activated/executed plan and stress-scenario replay while staying implementation-independent.
3. **Behavioral Learning:** causal event taxonomy, cold-start preference and anti-filter-bubble strategy.
4. **ReferenceFeasibleCost implementation:** fast lower-bound model vs small reference optimization for BudgetPressure.
5. **Numeric NutritionPolicy constants:** architecture locked; values require evidence/product safety review and benchmark.
6. **Retail acquisition/legal terms:** specific retailer adapters, terms and ingestion method need separate review.
7. **Benchmark launch thresholds:** runtime, reference-gap and stress coverage numeric gates remain to be set empirically.
8. **Receipt-calibrated stochastic/quantile model:** only after sufficient actual checkout history; not a V1 assumption.

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

## 25.4 Architecture debate consolidation notes (V1.2)

Revision V1.2 hợp nhất các vòng phản biện sau:

- Objective architecture: point-target/epsilon → Band-First 2-stage hierarchy.
- Nutrition band synthesis: safety/guideline, goal protection, resolution/temporal, user precision separated.
- PlanningMode removal: orthogonal policy dimensions + situational overrides.
- Household-first data ownership with single tracked nutrition member in V1.
- MealParticipants source-of-truth and explicit attendance/production separation.
- Recipe bounded templates, contextual substitutions and Pre-Solve Grounding.
- Package-fit micro-adjustment moved to local refinement after global meal/package selection.
- Inventory tracking policy + confidence + reconcile.
- Relaxation advice requires verification before user-facing action.

Các numeric policy constants chưa được coi là “fact” chỉ vì xuất hiện trong debate examples. Chúng phải được chốt riêng bằng evidence, product eligibility scope và benchmark/safety review.



---

## V1.2 release baseline

This document, `docs/ARCHITECTURE_INVARIANTS.md`, and ADR-001..ADR-008 form one canonical architecture baseline. If a future implementation intentionally violates an accepted ADR/invariant, the change requires a superseding ADR rather than an undocumented code deviation.
