# MENUTO - Tài liệu phát triển sản phẩm V1.3

**Product Strategy · Architecture · Planner V4 · Data Model · UX · Roadmap**

> **Phiên bản:** V1.3 — Closed-Loop Canonical Architecture Baseline
>
> **Ngày cập nhật:** 22/10/2026
>
> **Mục tiêu của revision này:** đóng băng vòng kiến trúc khép kín `Policy → Planner → Validator → Execution → Learning → Planner`, tích hợp ADR-009/010/011, 5 seam handoff contracts và bộ 30 architecture invariants. V1.3 là canonical spec để bước vào Implementation Blueprint Milestone 0/1; các quyết định superseded không tồn tại song song.

> **Định nghĩa sản phẩm**
>
> Menuto là nền tảng tối ưu quyết định ăn uống cho cá nhân/hộ gia đình: kết hợp ngân sách, dinh dưỡng, sở thích, inventory, hạn sử dụng, sản phẩm bán lẻ và khả năng thực hiện để tạo một kế hoạch ăn + mua sắm có thể áp dụng trong đời sống thực.

Nguồn thiết kế: Smart Menu hiện tại + rà soát sản phẩm cạnh tranh + các vòng architecture debate về Planner, Nutrition Policy, Household và Recipe Model.

> **Tệp Markdown chuẩn:** `docs/MENUTO_DEVELOPMENT_SPEC_V1_3.md`

## Revision highlights từ V1.2

1. Khóa **ADR-009 Execution State Machine**: một `ActivePlan` có `plan_id` ổn định, immutable revision snapshots, future intent revisable và execution facts tách khỏi plan intent.
2. Thêm ba state views: `ConfirmedState`, `OperationalState`, `PlanningState`; elapsed time chỉ được tạo reversible operational assumptions, không sửa confirmed reality.
3. `CookingBatch` trở thành physical transformation `Raw Inventory → PreparedFoodLot`; leftovers là household assets, không chỉ là repeat marker.
4. Khóa **ADR-010 Independent Validator** với ba lớp độc lập: semantic root-contract guards, arithmetic primitive recomputation và algorithmic chronological replay.
5. Validator dùng `ValidationSubjectSnapshot`, measurement-basis provenance, global conservation + chronological causality; `PRECOMMIT` gating tách khỏi `POSTFACT` diagnostics.
6. Khóa **ADR-011 Behavioral Learning**: attribution-routed multi-signal learning, member-owned preferences, `RecentExposureModel`, bounded exploration và không dùng scalar `recipe_score/adherence_score` làm truth.
7. Passive/autopilot execution không tạo durable taste hoặc exposure learning; `USER_CONFIRMED_COOKED` chứng minh execution fit chứ không chứng minh taste affinity.
8. Final seam audit khóa 5 handoff contracts: batch composition after micro-adjustment, sunk actual spend in mid-week revisions, cross-horizon inventory/exposure handoff, shared-meal utility attribution và forced-trade-off quarantine.
9. `HorizonBridgeResolver` project state đến đầu horizon mới bằng chronological commitments thay vì cộng/trừ thủ công dễ double-count.
10. `SPEND_LIMIT` revision validation dùng **actual sunk spend + future stress-tested spend**; uncertainty biến mất cho purchase đã fulfilled.
11. Bộ invariant canonical được renumber thành **INV-001 → INV-030**. Numbering tạm trong V1.2/debate bị supersede; implementation chỉ dùng numbering V1.3.
12. Roadmap/backlog/DoD được nâng để Milestone 0/1 bắt đầu từ domain contracts, units/measurement basis, execution/validation snapshots và benchmark harness.

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

> **Renumbering note:** các số invariant tạm xuất hiện trong V1.2 và các transcript tranh luận bị supersede bởi numbering V1.3 dưới đây. Code, test và PR từ V1.3 trở đi chỉ tham chiếu `INV-001` → `INV-030` theo danh mục này.

### I. Policy, physiology & intent

**INV-001 — Planning preference must never masquerade as physiology.** Convenience hoặc thrift preference không được hạ physiological/guideline safety floors hay phá goal direction.

**INV-002 — Observed constraint must never masquerade as user preference.** `BudgetPressure`, `CostPreference` và explicit `BudgetConstraint` là ba dữ kiện độc lập.

### II. Household & participant safety

**INV-003 — Shared resource != shared physiology.** Inventory/shopping/batch/plan thuộc Household; biology, allergy, diet và preference thuộc HouseholdMember.

**INV-004 — Aggregate demand must never erase individual safety constraints.** Effective allowed set của shared meal phải giữ mọi hard constraint của từng `MealParticipant`; attendance aggregation không được xóa identity safety.

### III. Culinary & recipe grounding

**INV-005 — Recipe flexibility must be authored, not inferred.** Substitution, portion tier và quantity envelope chỉ đến từ `RecipeVersion` rules được author/curate.

**INV-006 — Global optimization may choose among culinary possibilities; it may not create culinary possibilities.** Global CP-SAT chỉ chọn grounded immutable candidates; bounded micro-adjustment không được đổi recipe identity hoặc batch serving count nếu không có explicit portion-tier revision.

### IV. Retail, pricing & spend limits

**INV-007 — Retail observations are evidence, not guarantees.** Point-in-time offers được compile thành planning evidence; transient SKU/promo không phải checkout promise.

**INV-008 — The planner optimizes procurement resilience, not merely observed price.** `ProcurementFragility` phải tham gia economic quality cùng spend/waste/carryover.

**INV-009 — A risk score is not a probability unless it has been calibrated as one.** Stress scenarios, confidence classes, exploration bonuses hoặc heuristic reserves không được gọi là P90/xác suất nếu chưa empirical calibration.

**INV-010 — A hard user constraint may produce a relaxed alternative, but that alternative must never inherit the hard-feasible label without explicit user acceptance.**

### V. Execution state machine & inventory truth

**INV-011 — Planned acquisition is not owned inventory.** Planned/unconfirmed shopping không được materialize thành physical `InventoryLot`.

**INV-012 — Elapsed time is not evidence of consumption.** Time passage chỉ có thể tạo reversible `AUTOPILOT_ASSUMED` operational projection, không sửa `ConfirmedState`.

**INV-013 — Inference may update a projection; only evidence may update confirmed reality.**

**INV-014 — Execution drift should be repaired locally before globally.** Escalate qua local adjustment/substitution/reschedule trước remaining-week global replan.

### VI. Independent validation

**INV-015 — Validation verifies correctness, not optimality.** Validator không ranking objective hoặc chứng minh plan tốt nhất.

**INV-016 — Policy definitions may be shared; correctness enforcement must be independently evaluated.**

**INV-017 — Critical validation derives from resolved primitive facts, not planner-computed summaries.**

**INV-018 — Primitive facts must carry explicit measurement basis and provenance before independent recomputation.** `AP`, `EP_RAW`, `COOKED_G`, `SERVING`, money và discrete units không được nhập nhằng.

**INV-019 — Material feasibility must hold globally and at every causal point in time.** End-of-horizon conservation và chronological replay đều phải pass.

**INV-020 — Root contract validation must not trust planner-resolved safety summaries.** Participant allergies/hard dietary contracts và root goal direction phải được kiểm từ canonical contracts.

**INV-021 — Validation of intent is gating; validation of reality is diagnostic.** `PRECOMMIT` có thể reject proposed intent; `POSTFACT` ghi nhận reality rồi diagnostic. Validation observes; repair acts.

### VII. Behavioral learning & preference integrity

**INV-022 — Passive execution assumptions must not create durable behavioral learning.** `AUTOPILOT_ASSUMED` chỉ tạo reversible/provisional exposure trong operational horizon cho đến khi confirmed/reconciled.

**INV-023 — Operational or retail friction must never penalize culinary taste affinity.** `NO_TIME`, `OUT_OF_STOCK`, `TOO_EXPENSIVE`, `NO_EQUIPMENT` route sang đúng domain khác.

**INV-024 — Execution success must not masquerade as taste preference.** `USER_CONFIRMED_COOKED` cập nhật execution/context fit và confirmed exposure, không tự tăng taste affinity.

**INV-025 — Unattributed rejection is weak evidence, not confirmed dislike.**

**INV-026 — Shared meals may aggregate preferences; they must not erase member-level preference ownership.**

**INV-027 — Behavioral dimensions remain separable until planner utility composition.** Không persist một scalar truth trộn taste/time/equipment/complexity/repeat/novelty.

**INV-028 — Learned observations may influence soft ranking, but may not silently rewrite explicit user policy.** User-confirmed policy vẫn là contract.

**INV-029 — Forced trade-offs are evidence of constraint resolution, not voluntary preference.** Choices từ Relaxation Advisor hoặc forced execution repair bị quarantine khỏi taste/context learning trừ khi user đưa direct preference signal riêng.

**INV-030 — Future commitments must be honored when projecting inventory and exposure across planning horizons.** Reservations, scheduled transformations, carryovers và scheduled recent exposure trước `T_start` phải được handoff vào horizon mới.

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
- solver statuses/tolerance/relaxations;
- active revision number + baseline revision hash when activated;
- validation subject/report hashes for precommit gate;
- horizon bridge snapshot when a future horizon overlaps an active plan.

## 8.4 Closed-loop architecture and seam handoff contracts

V1.3 coi Menuto là một closed loop thay vì pipeline chỉ dừng ở plan:

```text
Policy
  ↓
Planner V4
  ↓
Independent Validator
  ↓
ActivePlan / Execution
  ↓
Attribution-Routed Learning
  └──────────────→ next Planner request
```

Năm seam dưới đây là canonical handoff contracts.

### Seam 1 — CulinaryAdjustment ↔ CookingBatch ↔ Validator

- `CulinaryAdjustmentPass` có thể thay đổi `batch_resolved_ingredients` trong authored envelope nhưng không tự thay `planned_servings`/`produced_servings`.
- Ingredient adjustment thay **composition per serving**, không suy tuyến tính thành “4.36 servings”.
- Allocation của ingredient `i` từ batch `b` cho meal dùng `k` servings được validator derive từ resolved batch composition và serving allocation.
- Chỉ explicit portion-tier/plan revision mới được đổi serving count.

### Seam 2 — Fulfilled purchase ↔ SPEND_LIMIT revision

Khi mid-week revision xảy ra, uncertainty của purchase đã fulfilled sụp về sunk historical fact:

```text
RevisionCost_s(t)
  = ConfirmedActualSpend(t)
  + StressScenarioSpend_s(RemainingUnfulfilled(t))
```

Không stress-test lại giá của món đã mua; cũng không bỏ qua actual overspend đã xảy ra.

### Seam 3 — Active horizon ↔ next-horizon planning

`HorizonBridgeResolver` project `PlanningState(t_now)` qua tất cả future commitments đến `T_start` bằng chronological transformation. Output là `ProjectedOpeningAssets(T_start)` và `ProvisionalRecentExposure(T_start)`.

Không implement opening stock bằng phép cộng/trừ rời rạc dễ double-count raw ingredients và future prepared carryover. Scheduled meals trước `T_start` được bridge như provisional exposure để tránh Sunday→Monday repetition dù chưa confirmed eaten.

### Seam 4 — Shared meal ↔ member-owned behavior

- Hard safety không nằm trong utility aggregation; nó được enforce cho từng participant trước.
- `DIRECT DISLIKE/EXPLICIT_AVOID` tạo strong shared-meal penalty; `LOW_AFFINITY` chỉ là ordinary weighted utility; `UNKNOWN` dùng prior/neutral.
- `FAVORITE`/`DISLIKE` mặc định update member tương ứng `actor_user_id` hoặc member user explicitly selected; không copy preference sang household members khác.

### Seam 5 — Relaxation/repair ↔ learning

Mọi accepted alternative từ `ConstraintRelaxationAdvisor` hoặc forced local repair mang `context = FORCED_CONFLICT_RESOLUTION`. Event này dùng cho trade-off analytics nhưng bị quarantine khỏi voluntary taste/context learning theo `INV-029`.

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
| lifecycle_state | ACTIVE / DEPLETED / EXPIRED / DISCARDED; reservation is modeled separately. |
| observation_confidence | CONFIRMED / STALE / UNKNOWN; projected quantities live in Operational/Planning projections, not as physical lots. |

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
- carryover-derived projections in `OperationalState`/`PlanningState` (không materialize thành physical lot cho tới khi evidence/reconcile xác nhận);
- reconcile.

V1.5+: barcode/receipt/photo chỉ là input accelerator, tất cả normalize về cùng ledger contract.

## 13.7 Single ActivePlan + immutable revision history

Sau activation, một tuần đang chạy giữ **một `plan_id` ổn định**. Current working graph được phép revise chỉ ở future/unexecuted nodes; lịch sử được đóng băng bằng `PlanRevisionSnapshot #0..N`.

```text
ActivePlan(plan_id stable)
├── Current Working Graph        # future intent mutable by validated revision
├── PlanRevision #0              # INITIAL_ACTIVATED_BASELINE immutable
├── PlanRevision #1..N           # immutable diff/snapshot
└── ExecutionLedger              # what actually happened
```

`PlanRevisionHistory != ExecutionLedger`: revision trả lời “Menuto đã thay đổi lời khuyên thế nào”; ledger trả lời “ngoài đời đã xảy ra gì”. Local Swap, remaining-week replan và intent-changing culinary adjustment đều tạo atomic plan revision với `revision_scope`; execution deviation sau khi nấu không tự động trở thành plan revision.

Khi intent đã materialize thành physical fact (`PurchaseFulfillment → InventoryLot`, `CookingBatchExecution → PreparedFoodLot`), revision sau không được rewrite/xóa fact đó.

## 13.8 ConfirmedState, OperationalState, PlanningState

- `ConfirmedState`: chỉ evidence trực tiếp (`USER`, receipt/barcode, explicit correction, reconcile).
- `OperationalState`: confirmed facts + reversible `AUTOPILOT_ASSUMED`; Today/Expiry/ExecutionImpactAnalyzer đọc view này.
- `PlanningState`: state đã resolve/reconcile để feed optimizer; trước next plan có thể yêu cầu targeted reconcile nếu assumption debt cao.

Operational assumption không được masquerade thành confirmed inventory hoặc durable behavioral memory.

## 13.9 Inventory as material ledger + reservations

`InventoryLot` không dùng mega-enum `projected/available/reserved/consumed` làm source of truth. Physical quantity được giữ bằng lots + movements; reservations là allocation intent riêng:

```text
InventoryLot
├── acquired_qty
├── remaining_qty
├── usable_until
└── provenance/confidence

InventoryReservation
├── lot_id
├── target meal/batch
└── qty
```

Reservation không làm thay đổi conservation quantity; rule `reserved(t) <= physical_available(t)` được validator kiểm riêng.

Planned procurement chỉ là future inflow trong precommit replay; chỉ confirmed fulfillment mới tạo household `InventoryLot`.

## 13.10 Shopping fulfillment is quantitative

Không dùng `purchased=true/false` làm truth. `ShoppingRequirement(required_qty)` có một hoặc nhiều `PurchaseFulfillment(actual_qty, actual_price, product/procurement provenance)`; derived shortfall/overage quyết định repair/replan.

Mid-week budget revision dùng sunk `actual_price` của fulfilled purchases + stress quotes cho remaining unfulfilled requirements.

## 13.11 CookingBatch physical transformation and PreparedFoodLot

Batch execution là transaction vật lý:

```text
Raw InventoryLot
  ↓ consume resolved ingredients
CookingBatchExecution
  ↓ produce
PreparedFoodLot(servings, usable_until)
  ↓ allocate/consume/discard
MealConsumption / leftover
```

Raw inventory dùng grams/units; prepared food V1 được track theo servings để giảm UX friction. `COOKED != CONSUMED`; production, allocation và consumption là events riêng.

`CulinaryAdjustmentPass` giữ serving count trừ khi explicit portion-tier revision thay đổi nó; adjusted ingredient grams thay composition/nutrition per serving.

## 13.12 Reversible optimistic autopilot

Happy path cần zero-tap, nhưng assumption không được biến thành fact.

Autopilot chỉ chạy qua gate:

- plan/slot còn active và chưa bị revision invalidate;
- meal là home meal;
- required inputs available trong OperationalState;
- không có unresolved shopping shortfall hoặc execution conflict.

Allowed effects: provisional consume, provisional prepared lot, provisional leftover allocation, operational projection. Forbidden effects: purchase fulfillment, actual price, discard, allergy-sensitive substitution, hard-constraint relaxation acceptance, durable preference learning hoặc irreversible replan.

Corrections dùng compensating entries (`AUTOPILOT_REVERSAL`) thay vì delete history. Provisional events có dependency chain; reverse parent cascade assumptions phụ thuộc, còn conflict với confirmed child tạo `EXECUTION_CONFLICT` cần reconcile.

## 13.13 ExecutionImpactAnalyzer and local-first repair

Mỗi drift event được đánh giá theo nutrition/inventory/expiry/shopping/batch impact và trả một trong:

```text
NONE
LOCAL_REPAIR
REPLAN_RECOMMENDED
REPLAN_REQUIRED
```

Escalation mặc định: quantity adjustment → substitute → reschedule/leftover → local swap → remaining-week replan. `REPLAN_REQUIRED` nghĩa current remaining intent không còn safe/feasible; user vẫn cần xác nhận revision.

## 13.14 HorizonBridgeResolver

Khi tạo plan cho horizon mới trước khi active horizon kết thúc, resolver replay future commitments từ `t_now` đến `T_start` để tạo:

- `ProjectedOpeningAssets(T_start)`;
- remaining committed reservations transformed correctly;
- scheduled prepared carryovers;
- `ProvisionalRecentExposure` cho meals scheduled trước `T_start`.

Resolver phải tránh double-count raw ingredients đã reserved cho batch và output prepared food của chính batch đó. Đây là implementation contract của `INV-030`.

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
PlannedCookingBatch
├── grounded recipe/variant
├── planned_servings
├── batch_resolved_ingredients
├── production_time
└── BatchAllocation[] → meal consumption demand
```

Khi thực thi, `CookingBatchExecution` materialize thành `PreparedFoodLot`. `CookingEffort` khác `MealRepetition`: nấu một lần ăn nhiều bữa có thể desirable dù cùng family xuất hiện lặp.

**Batch Density Adjustment Rule:** bounded micro-adjustment thay ingredient composition nhưng không tự đổi `planned_servings`/`produced_servings`. Nutrition cho allocated servings được derive từ batch composition sau adjustment. Explicit portion-tier revision mới được đổi serving count.

## 14.10 Behavioral candidate vector, not persisted AdherenceScore

V1.3 không persist một scalar `adherence_score` làm domain truth. Candidate giữ dimensions riêng:

```text
taste_fit
time_fit
equipment_fit
complexity_fit
ingredient_count_fit
batch_fit
schedule_fit
repeat_penalty
novelty_value
```

Stage 2 compile vector này thành utility bằng versioned policy. Taste, context fit, repeat exposure và novelty được cung cấp bởi ADR-011 learning components; chúng không được collapse sớm thành một historical scalar khó giải thích.

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
- Activated week giữ stable `plan_id`; `PlanRevisionSnapshot` immutable, future working graph chỉ đổi qua validated atomic revision.
- Execution facts/materialized household assets không bị rewrite bởi plan revision.
- State-changing commands dùng optimistic concurrency/idempotency keys; precommit validation report phải match subject/revision hash.

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
│       │   │   ├── validation/
│       │   │   ├── learning/
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

# 18. Independent validation, testing, benchmark và observability

## 18.1 Validator responsibility and independence boundary

`Independent Validator` là deterministic, side-effect-free semantic verifier. Nó kiểm correctness, không search/optimize/repair và không dùng LLM.

```text
ValidationSubjectSnapshot
  ↓
Root Contract Guards
+ Primitive Fact Calculators
+ Chronological Replay
  ↓
Domain Validators
  ↓
ValidationReport(findings, derived_facts, trace, hashes)
```

Allowed shared dependencies: domain primitives, units, contracts, immutable policy/scenario snapshots. `validation` không import planner constraint builders, candidate generation, solver expressions hoặc objective helpers.

## 18.2 Root Contract Guards

Validator không viết lại full Policy Engine, nhưng kiểm root invariants từ canonical contracts:

- participant identity + canonical member allergy/diet constraints;
- goal direction/containment contract;
- safety floor không bị resolver làm yếu hơn applicable guideline contract;
- hard budget contract/relaxation status không bị relabel.

Participant safety bypass planner-resolved exclusion summaries.

## 18.3 Primitive recomputation

Correctness-critical values được derive từ resolved primitive facts có explicit measurement basis/provenance:

- nutrition từ resolved ingredient allocations + compatible nutrition basis;
- AP→EP edible yield rồi cooking/prepared transformation riêng;
- procurement cost từ package/procurement quantity × scenario quote, không prorate recipe grams tùy tiện;
- recipe quantities so với authored envelopes;
- household safety từ actual participants × grounded ingredient identities.

Planner summaries có thể được cross-check sau recomputation để phát hiện `DERIVED_SUMMARY_MISMATCH`, nhưng không phải source of truth cho validation.

## 18.4 Global conservation + chronological domain-event replay

Hai checks đều bắt buộc:

1. **Global conservation:** `Opening + Inflows - Outflows = Closing`.
2. **Temporal causality replay:** imperative replay qua acquisition, reconcile/transfer, raw consumption, prepared production, meal consumption, expiry/discard với deterministic ordering/sequence.

Replay kiểm `Stock(t) >= 0`, reservations không vượt physical stock, asset chưa được consume trước acquire, và event không dùng lot sau `usable_until`. Raw và prepared asset ledgers được replay riêng, batch event nối hai ledgers.

## 18.5 PRECOMMIT vs POSTFACT

- `PRECOMMIT_VALIDATION`: gate plan activation, local refinement, swap và revision; yêu cầu `0 FATAL`, `0 ERROR` và matching subject hash/revision lock.
- `POSTFACT_VALIDATION`: diagnostic reality đã xảy ra; không reject lịch sử mà tạo findings/repair recommendations.

Local `CulinaryAdjustmentPass` nếu fail revalidation thì tự discard refinement và fallback về globally validated plan.

## 18.6 Core validators V1

```text
RootContractValidator
HouseholdSafetyValidator
RecipeGroundingValidator
NutritionPrimitiveValidator
ProcurementScenarioValidator
MaterialYieldValidator
ChronologicalInventoryValidator
BatchFlowValidator
RevisionBoundaryValidator
AssumptionGraphValidator
```

Findings có structured `code`, `severity`, `source_domain`, `scope`, expected/actual và proof trace. Severity: `FATAL`, `ERROR`, `WARNING`, `INFO`.

## 18.7 Test pyramid

| Layer | Tests |
|---|---|
| Domain unit | Units/basis, nutrition formulas, yield, shelf-life, procurement/package math. |
| Planner model | Small deterministic instances với known feasibility/optimum. |
| Validator mutation corpus | Start từ valid fixture rồi cố tình inject allergen, AP→EP omission, short protein, budget breach, consume-before-buy, broken assumption dependency. |
| Property-based | No negative stock, conservation, participant safety, locked past unchanged. |
| Integration | Generate → validate → activate → shopping fulfillment → execution/revision → reconcile. |
| Golden scenarios | Curated 1/3/7-day household plans incl. partial shopping, batch leftovers và cross-horizon bridge. |
| Benchmark | Planner/reference comparison; quality + runtime + validation regression. |
| Frontend | Onboarding/generate/swap/shop/today/undo/reconcile flows. |
| Data quality | Missing basis/nutrition/price/shelf-life/product-map thresholds. |

## 18.8 Benchmark dimensions

- 1/3/7 days; 2 vs 3 meals/day.
- Loose/tight/no budget; SPEND_LIMIT revision after partial actual spend.
- No/rich/expiring inventory; planned vs confirmed vs assumed execution state.
- Small/medium/large recipe catalog and grounded variant pressure.
- High protein, maintain, calorie deficit presets.
- Many exclusions/preferences; multi-participant shared meals.
- Large package increments, catch-weight and short shelf-life.
- Price data fresh/stale/fallback; procurement fragility.
- Cross-week horizon generated before current horizon ends.

## 18.9 Metrics per run

| Category | Metrics |
|---|---|
| Solver | status, solve_ms, phases completed, optimal/best-effort, candidate_count. |
| Validation | findings_by_severity/code, validation_ms, stale_report_retry, summary mismatch count. |
| Nutrition | comfort violations, goal/safety violations, validator-recomputed totals. |
| Budget | expected/scenario spend, actual_sunk_spend, remaining stress spend, budget status. |
| Inventory | inventory_value_used, expiring_value_saved, negative/intermediate violations=0. |
| Waste | expired_waste_value, awkward_carryover_value. |
| Execution | assumed vs confirmed events, correction rate, assumption debt, local-repair/replan rate. |
| Experience | unique dishes, repeats, cooking_minutes, shopping_days, exploration/exploit mix. |
| Quality gap | difference vs reference solve on comparable objective vector. |

## 18.10 Observability

- Planner/validator run trace dùng fingerprints, tránh PII/raw sensitive logs.
- Catalog/policy/price/recipe/revision/validation subject hashes.
- Reason codes cho infeasible/data insufficient/time limit/validation failure/execution conflict.
- Dashboard fail/timeout/swap/replan/assumption correction/actual-vs-planned price.

# 19. Metrics và Behavioral Learning Loop

> **North Star Metric**
>
> Completed planned meals per active household per week.

| Metric | Ý nghĩa |
|---|---|
| Plan acceptance rate | Plan generate xong có activate/save không. |
| Swap rate + reason | Candidate quality vs context friction. |
| Planned → confirmed cooked | Execution fit; không đồng nghĩa taste. |
| Budget deviation | Planned/scenario vs actual spend. |
| Inventory utilization | Physical assets được dùng trước expiry. |
| Waste rate | Discarded/expired inventory. |
| Weekly retention | Menuto trở thành routine không. |
| Relaxation acceptance | Advisor usefulness, không phải preference label. |
| Correction rate | Bao nhiêu autopilot assumptions bị user sửa. |
| Exploration acceptance | Món under-explored được giữ/swapped/favorited ra sao. |

## 19.1 Event semantics

Các event phải mang reason/context/provenance đủ để attribution, ví dụ:

```text
plan_generated
plan_activated
plan_revised
shopping_item_fulfilled
actual_price_recorded
user_confirmed_cooked
autopilot_assumed
meal_swapped(reason)
meal_skipped(reason)
meal_ate_out
recipe_favorited
explicit_dislike
inventory_consumed
inventory_discarded
reconcile_confirmed
relaxation_offered
relaxation_accepted(context=FORCED_CONFLICT_RESOLUTION)
```

## 19.2 EvidenceClassifier + SignalAttributionRouter

Mỗi signal được classify `DIRECT | CONTEXTUAL | INFERRED | PASSIVE`, rồi route sang:

```text
TasteAffinity
KitchenContextFit
RecentExposureModel
RetailCalibration
NoLearn
```

`AUTOPILOT_ASSUMED` không tạo durable learning. `USER_CONFIRMED_COOKED` update execution/context fit + confirmed exposure nhưng TasteAffinity = 0. `NO_TIME`/`OUT_OF_STOCK`/`TOO_EXPENSIVE` không phạt taste. Unattributed rejection chỉ weak evidence.

## 19.3 Member-owned hierarchical preference

`MemberBehaviorProfile` thuộc `HouseholdMember` và có feature-level + direct recipe evidence:

- IngredientAffinity;
- ProteinAffinity;
- CookingMethodAffinity;
- FlavorProfileAffinity;
- DirectRecipeAffinity;
- EvidenceStrength `NONE | LOW | MEDIUM | HIGH`.

Planner dùng shrunk affinity: khi evidence thấp thì gần onboarding/catalog prior; evidence trực tiếp tăng dần influence member-specific score. Favorite/rating có thể generalize yếu sang feature, nhưng direct recipe signal mạnh hơn generalization.

## 19.4 RecentExposureModel / RepeatCooldown

Exposure history xuyên weekly boundary và có multi-level fingerprints:

```text
recipe_id          strong repeat penalty
variant_family_id  medium
main_protein       light
cooking_method     light
flavor_profile     light
```

Confirmed/reconciled exposure có full weight theo policy; autopilot chỉ tạo reversible provisional exposure trong operational horizon. Decay/default cooldown được version/configure theo family/category và benchmark; không hard-code universal 7–14 ngày hay exponential curve vào ADR.

## 19.5 Shared meal utility and actor-scoped learning

Hard safety được resolve trước utility. Shared meal TasteFit/RepeatPenalty aggregate member-owned profiles; explicit avoid/direct dislike có strong veto-like soft penalty, low affinity chỉ weighted utility.

Execution→Learning mặc định update actor/member được chỉ định, không copy preference sang mọi participant.

## 19.6 Bounded exploration

Role-aware shortlist bảo vệ configurable capacity cho ba nguồn:

```text
EXPLOIT
STRUCTURAL_CHAMPION   # economics/inventory/nutrition/waste
EXPLORE
```

Quota là versioned `ShortlistPortfolioPolicy`, không phải fixed 50/30/20 architecture constant. V1 dùng deterministic novelty/exposure/feature-fit score, không gọi là UCB/statistical confidence nếu không implement/calibrate đúng.

## 19.7 Learned observation != explicit policy

Repeated context behavior có thể tạo semantic observation (*“Bạn thường chọn món nhanh vào tối ngày thường”*) và soft ranking influence, nhưng không tự rewrite `KitchenEffort`/budget/nutrition policy. User có thể confirm/promote, invalidate hoặc reset learned rule; explicit correction phải ngăn engine re-infer y hệt mà không evidence mới.

## 19.8 Forced trade-off quarantine

Signals từ accepted Relaxation Advisor hoặc forced repair có `FORCED_CONFLICT_RESOLUTION`; chỉ dùng trade-off analytics, không update voluntary taste/context preference theo `INV-029`.

# 20. Roadmap Public V1 → V1.5 → V2

## 20.1 Milestone 0 — Canonical contracts + benchmark foundation

- Publish V1.3 canonical spec, ADR-001..ADR-011 và INV-001..INV-030.
- Domain glossary + ownership/lifecycle/state diagrams.
- Unit/measurement-basis primitives (`AP_G`, `EP_RAW_G`, `COOKED_G`, `SERVING`, money/discrete units).
- Neutral benchmark fixture format + mutation-test fixture format.
- Pin Python/OR-Tools/toolchain and reproducibility policy.
- Architecture dependency checks: validation cannot import planning/solver internals.

## 20.2 Milestone 1 — Household/Data/Execution foundation

- Identity + default household/member creation.
- Member nutrition/diet/allergy + behavior profile schema.
- MealParticipants/meal schedule defaults.
- Ingredient/nutrition catalog with explicit measurement basis/provenance.
- RecipeVersion + RecipeIngredient + VariantRule.
- RetailProduct/Offer + ProcurementClass + PlanningPriceQuote + ReferencePriceBook + RetailPriceCalibration.
- Household inventory lots/movements/reservations/policy/reconcile.
- Stable `ActivePlan` + `PlanRevisionSnapshot` + execution-event schema.
- PreparedFoodLot + CookingBatchExecution data model.

## 20.3 Milestone 2 — Policy engines + snapshots

- NutritionPolicyEngine 4-layer synthesis.
- NutritionResolutionEstimator.
- Economic/Budget resolver + `SPEND_LIMIT` contract.
- KitchenPolicy resolver + daily availability.
- ResolvedPlanPolicy + StressScenario + ValidationSubject snapshot contracts.
- Root contract invariant tests.

## 20.4 Milestone 3 — Planner V4 global core + validator

- Grounded Variant Generator.
- Role-aware Pareto/portfolio shortlist with bounded exploration hooks.
- Conservative Feasibility V2.
- Stage 1 Band + Structural Economics + deterministic spend stress scenarios.
- Package/procurement/inventory/batch model.
- Stage 2 Human Utility vector composition.
- Independent Validator: primitive recomputation + conservation + chronological replay.
- Reference benchmark/quality-gap/mutation corpus.

## 20.5 Milestone 4 — Refinement + execution repair

- CulinaryAdjustmentPass + mandatory revalidation/fallback.
- Constraint conflict/elastic/verification advisor.
- Local Swap / remaining-week replan as atomic plan revisions.
- ExecutionImpactAnalyzer local-first escalation.
- HorizonBridgeResolver for overlapping planning horizons.
- Explainability facts/provenance.

## 20.6 Milestone 5 — Consumer V1 closed loop

- Onboarding without PlanningMode + cold-start feature priors.
- Situational plan chips.
- One-tap inventory reconcile.
- Household meal participation defaults.
- Result Quality Summary.
- Shopping fulfillment actual qty/price + primary/backups.
- Today mode + batch/leftover execution + exception-only autopilot correction UX.
- Learned observations UI/reset/promotion to policy.
- AI parse/explain bounded by deterministic facts.

## 20.7 Milestone 6 — Public readiness

- Security/privacy/wellness eligibility review.
- Retail provenance/calibration/stress-scenario QA.
- Data/catalog coverage matrix.
- Planner + validator + execution performance/load tests.
- Accessibility/responsive QA.
- Backup/restore/migration rollback.
- Launch feature flags/rollback + operational dashboards.

## 20.8 V1.5

- Barcode/receipt-assisted inventory and richer actual-cost calibration.
- Better per-day schedule/context inference with user-confirmable learned rules.
- Household-lite collaboration.
- More retailer adapters.
- Leftover/execution UX refinement.
- Better deterministic learning/portfolio tuning.
- Limited/bounded recipe import drafts.

## 20.9 V2

- Full multi-member individual nutrition + component allocation.
- Multi-retailer split-basket optimization.
- Native mobile if retention supports it.
- Camera inventory assistant.
- Long-horizon carryover planning.
- Robust/stochastic nutrition or checkout models only when uncertainty metadata and empirical calibration are sufficient.
- More advanced personalization after offline evaluation maturity.

# 21. Backlog triển khai ưu tiên

| ID | Priority | Epic / Issue | Acceptance criteria tóm tắt |
|---|---|---|---|
| MTR-001 | P0 | Domain glossary + invariants | V1.3 canonical distinctions + INV-001..030 mirrored in docs/tests; renumber migration note present. |
| MTR-002 | P0 | Benchmark + mutation harness | Scenario matrix, objective vector, runtime/status, reference config + deliberately corrupted validator fixtures. |
| MTR-003 | P0 | Units & measurement basis | AP/EP/raw/cooked/serving/money/discrete contracts; incompatible bases rejected. |
| MTR-004 | P0 | Household-first schema | Default household/member; household-owned resources; actor fields. |
| MTR-005 | P0 | MealParticipants model | Participant IDs + portion factors + canonical hard-constraint resolution + derived attendance scale. |
| MTR-006 | P0 | NutritionPolicyEngine | Guideline/goal/comfort/weekly policy; root contracts versioned. |
| MTR-007 | P0 | NutritionResolutionEstimator | Catalog/portion resolution reporting; no silent unbounded widening. |
| MTR-008 | P0 | PlanPolicyResolver | NutritionPrecision, CostPreference, KitchenEffort, BudgetContract compiled independently. |
| MTR-009 | P0 | Budget baseline/pressure | ReferenceFeasibleCost pressure distinct from preference/contract. |
| MTR-010 | P0 | Retail evidence schema | RetailProduct/Offer/provenance/source-quality/availability evidence. |
| MTR-011 | P0 | ProcurementClass builder | FIXED_PACK/CATCH_WEIGHT/LOOSE_SCALE + coverage/fragility metadata. |
| MTR-012 | P0 | PlanningPriceQuote + calibration | Retailer×region×category calibration with confidence/shrinkage. |
| MTR-013 | P0 | SPEND_LIMIT stress scenarios | BASE/ADVERSE_WEIGHT/BACKUP/CATEGORY_STRESS snapshot + revision sunk-spend semantics. |
| MTR-014 | P0 | AP→EP + cooking-yield chain | Product AP→EP explicit; cooking yield/prepared output separate. |
| MTR-015 | P0 | Inventory physical ledger | Household lots/movements/reservations/policy/reconcile; planned acquisition never physical stock. |
| MTR-016 | P0 | ActivePlan + PlanRevision schema | Stable plan_id, immutable revision snapshots/diffs, locked materialized past, optimistic revision locking. |
| MTR-017 | P0 | Execution state projections | Confirmed/Operational/Planning views + provisional assumption provenance. |
| MTR-018 | P0 | Recipe version/variant schema | Contextual substitution + quantity/scaling/adjustment policies. |
| MTR-019 | P0 | Grounded Variant Generator | Demand-driven immutable candidates; reason/fingerprint; explicit bases. |
| MTR-020 | P0 | Role-aware portfolio shortlist | Pareto + EXPLOIT/STRUCTURAL_CHAMPION/EXPLORE capacity; no cheapest starvation. |
| MTR-021 | P0 | Feasibility V2 | Inventory/procurement/participant aware; data insufficiency != infeasible. |
| MTR-022 | P0 | Stage 1 global optimizer | Comfort violation + structural economics + fragility + package/inventory/batch. |
| MTR-023 | P0 | CookingBatch/PreparedFood model | Planned production/allocation + execution transformation + leftovers; serving-count seam rule. |
| MTR-024 | P0 | Stage 2 human utility | Separable behavioral vector compiled by versioned utility policy. |
| MTR-025 | P0 | ValidationSubjectSnapshot | Immutable facts/policy/scenario/revision hash; no mid-validation DB drift. |
| MTR-026 | P0 | Independent validator suite | Root safety, primitive nutrition/cost/yield, conservation, chronological replay, batch/revision/assumption checks. |
| MTR-027 | P0 | Planner API v1 | Versioned policy/source/scenario/validation snapshots + structured statuses/reasons. |
| MTR-028 | P0 | Consumer onboarding | Life questions; budget wording; household defaults; cold-start feature priors. |
| MTR-029 | P0 | Plan Quality Summary | Nutrition zone, spend status, provenance, inventory, waste, batch, fragility. |
| MTR-030 | P1 | CulinaryAdjustmentPass | Freeze structure; bounded quantity refinement; preserve serving count unless explicit tier; revalidate/fallback. |
| MTR-031 | P1 | Relaxation Advisor | Conflict → elastic estimate → verified proposals; forced-context quarantine. |
| MTR-032 | P1 | Local Swap revision | Proposed graph built/validated before atomic commit; preserve physical facts. |
| MTR-033 | P1 | Remaining-week replan | Freeze executed/materialized past; use current actual/operational/planning state correctly. |
| MTR-034 | P1 | Shopping fulfillment resolver | Partial actual qty/price, sunk spend, primary/backups, household inventory materialization. |
| MTR-035 | P1 | Today/execution mode | Batch/leftover guidance, skip/eat-out/swap, non-blocking assumption correction. |
| MTR-036 | P1 | Assumption graph + compensation | Dependency chains, compensating reversals, execution conflicts, assumption-debt tracking. |
| MTR-037 | P1 | ExecutionImpactAnalyzer | NONE/LOCAL_REPAIR/REPLAN_RECOMMENDED/REPLAN_REQUIRED with local-first escalation. |
| MTR-038 | P1 | HorizonBridgeResolver | Chronological projection of future commitments + scheduled exposure to next horizon without double-count. |
| MTR-039 | P1 | SignalAttributionRouter | DIRECT/CONTEXTUAL/INFERRED/PASSIVE → taste/context/exposure/retail/no-learn. |
| MTR-040 | P1 | MemberBehaviorProfile | Hierarchical feature/direct affinity + evidence strength + explicit ownership. |
| MTR-041 | P1 | RecentExposureModel | Cross-week multi-fingerprint repeat penalty; provisional vs confirmed exposure semantics. |
| MTR-042 | P1 | Learned observations UX | Show/reset/invalidate/promote learned rules; never silent policy mutation. |
| MTR-043 | P1 | Price/provenance UX | Retail vs calibrated reference vs baseline clearly distinguished. |
| MTR-044 | P1 | AI intent/explanation | Structured intent + verified metrics only. |
| MTR-045 | P1 | Telemetry/feedback | Execution/learning/relaxation events with attribution reason/context and privacy review. |
| MTR-046 | P1 | Catalog coverage matrix | Role/protein/style/quick/high-protein coverage + planner-ready completeness. |
| MTR-047 | P1 | Receipt-vs-plan calibration dataset | Planned quotes/scenarios vs actual checkout, with retailer/category/context. |
| MTR-048 | P2 | Barcode/receipt import | Reviewable mapping to fulfillment/inventory/actual-price. |
| MTR-049 | P2 | Household-lite collaboration | Shared household UI/permissions, no individualized solver yet. |
| MTR-050 | P2 | Recipe import | Reviewable RecipeVersion draft; no auto-trust facts. |

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
- Inventory reconcile nhanh, rõ Confirmed vs Operational assumption; no blocking confirmation for every meal.
- Result không hiển thị fake precision (ví dụ 1,987 kcal như exact truth nếu policy/data không justify).
- Retail offer vs calibrated reference vs baseline provenance dễ phân biệt; không fake checkout certainty.
- Unsupported health/clinical request trả bounded message, không tự tính therapeutic plan.
- Structured errors/reasons có copy user-friendly.
- Privacy export/delete workflow.
- Operational dashboards cho error/timeout/infeasible/data-quality.
- No critical/high security findings mở.
- Backup/restore + migration rollback đã test.

## 23.5 Milestone 0/1 implementation entry criteria

Implementation blueprint chỉ bắt đầu khi:

- `MENUTO_DEVELOPMENT_SPEC_V1_3.md`, ADR-001..011 và INV-001..030 cùng commit/version;
- canonical units/measurement-basis enum/contracts được freeze;
- ownership/lifecycle diagram cho Household, ActivePlan, InventoryLot, PreparedFoodLot, ProcurementClass có testable semantics;
- ValidationSubjectSnapshot và Planner request/output contracts có draft schema;
- benchmark + mutation fixture format được freeze;
- architectural dependency CI rule chặn `validation → planning/solver internals`;
- migration strategy từ Smart Menu được coi là selective reuse, không schema fork trực tiếp.

# 24. ADR registry, risks và open decisions

## 24.1 Canonical ADRs published with V1.3

| ADR | Status | Canonical decision |
|---|---|---|
| ADR-001 Band-First Planner | ACCEPTED | Stage 0 hard safety; Stage 1 comfort/structural economics; Stage 2 human utility; bounded local refinement. |
| ADR-002 Nutrition Policy Engine | ACCEPTED | Guideline → Goal → Resolution/Temporal → NutritionPrecision; no universal point-target/BMR shortcut. |
| ADR-003 Plan Policy Resolution | ACCEPTED | No canonical PlanningMode; orthogonal nutrition/cost/kitchen policy + explicit budget contract. |
| ADR-004 Household-First Model | ACCEPTED | Household owns shared resources; member owns physiology; one TrackedMember V1; participants source-of-truth. |
| ADR-005 Grounded Recipe Variants | ACCEPTED | Authored flexibility → grounded immutable candidates; local adjustment after global selection. |
| ADR-006 Retail Procurement Abstraction | ACCEPTED | Retail evidence → ProcurementClass → PlanningQuote → concrete primary/backups; SKU-direct not default. |
| ADR-007 SPEND_LIMIT Robustness | ACCEPTED | Deterministic stress scenarios; no uncalibrated P90; actual sunk spend collapses uncertainty after fulfillment. |
| ADR-008 No Silent Relaxation | ACCEPTED | Hard relaxations separately labeled, verified and user-accepted before activation. |
| ADR-009 Execution State Machine | ACCEPTED | Single ActivePlan graph, immutable revisions, three state views, reversible operational assumptions, prepared-food lifecycle. |
| ADR-010 Independent Validator | ACCEPTED | Root contract guards + primitive recomputation + global conservation + chronological replay; precommit gating/postfact diagnostics. |
| ADR-011 Behavioral Learning Loop | ACCEPTED | Attribution-routed member-owned multi-signal learning, recent exposure, bounded exploration, no passive/forced preference contamination. |

Implementation PRs thay canonical decision phải reference ADR; intentional invariant violation requires superseding ADR.

## 24.2 Core risks

| Risk | Impact | Mitigation |
|---|---|---|
| Retail data stale/unavailable | Very high | Provenance, ProcurementClass, calibration, reference fallback, stress scenarios. |
| False checkout certainty | Very high | SPEND_LIMIT semantics, deterministic stress, no probability claim before calibration. |
| Solver/candidate growth | High | Demand-driven grounding, role portfolio shortlist, local refinement, benchmark. |
| Culinarily weird math | Very high | Authored flexibility, grounded candidates, validator, serving-count seam rule. |
| Inventory diverges from kitchen reality | High | Operational assumptions + exception-only correction + targeted reconcile/assumption debt. |
| Assumption becomes false memory | High | Confirmed/Operational split, no durable learning from passive events, compensating reversals. |
| Household aggregation hides allergy/preference owner | Critical/High | Root member safety validation + member-owned behavior + actor-scoped attribution. |
| Validation shares planner bug | Critical | Root guards, primitive recomputation, imperative replay, module dependency boundary. |
| Cross-horizon double-count | High | HorizonBridgeResolver chronological transformation + INV-030. |
| Learning filter bubble | High | Separable dimensions, shrunk priors, bounded exploration, no autopilot endorsement. |
| Numeric nutrition overclaim | High | Band/policy provenance, wellness eligibility, no fake precision. |
| V1 grows into family macro solver/ML platform | High | Explicit boundaries + deterministic learning V1. |

## 24.3 Remaining open decisions after V1.3

Core architecture loop is closed. Các mục còn mở chủ yếu là implementation/calibration, không phải subsystem ownership:

1. `ReferenceFeasibleCost` implementation: analytical lower bound vs small reference optimization.
2. Numeric NutritionPolicy defaults: require evidence/safety/product benchmark; examples trong debate không phải constants.
3. Retail acquisition/legal/commercial terms for specific adapters.
4. Benchmark launch thresholds: latency, quality gap, validation budget và catalog coverage numeric gates.
5. Exact default shortlist exploration quotas/cooldown configurations; must be empirically tuned/versioned.
6. AssumptionDebt thresholds and when targeted reconcile becomes mandatory.
7. Receipt-calibrated stochastic/quantile model only after sufficient actual checkout history.
8. Database/contract implementation choices to be locked in Milestone 0/1 blueprint.

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

## 25.4 Architecture debate consolidation notes (V1.3)

V1.3 giữ toàn bộ V1.2 decisions và bổ sung/khóa:

- Execution: stable ActivePlan working graph + immutable revisions; physical facts detach from later intent revisions.
- Three state views and reversible optimistic autopilot with compensating entries/dependency graph.
- PreparedFoodLot and raw→prepared physical transformation.
- Validator: semantic/arithmetic/algorithmic independence; explicit basis; global conservation + chronological replay.
- Learning: attribution routing, member-owned preference, no `cooked = liked`, no passive durable learning, recent exposure and bounded exploration.
- Seam 1: micro-adjustment changes batch composition, not implicit serving count.
- Seam 2: fulfilled purchase becomes sunk actual cost in revision budget checks.
- Seam 3: chronological horizon bridge for inventory + exposure; avoid double-count.
- Seam 4: participant utility aggregation with actor-scoped preference attribution.
- Seam 5: forced conflict resolution quarantined from voluntary preference learning.
- Canonical invariants renumbered to INV-001..INV-030; V1.2/debate numbering is superseded.

Numeric examples from debate remain examples unless separately adopted by versioned policy/benchmark evidence.

---

## V1.3 release baseline

This document, `docs/ARCHITECTURE_INVARIANTS.md`, and ADR-001..ADR-011 form one canonical architecture baseline. The closed-loop architecture is now considered ready for Milestone 0/1 Implementation Blueprint. Any future implementation that intentionally violates an accepted ADR/invariant requires a superseding ADR rather than undocumented code drift.

