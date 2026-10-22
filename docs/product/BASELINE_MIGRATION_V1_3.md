# Chuyển baseline V1.2 → V1.3 — 22/10/2026

V1.3 là canonical source duy nhất đang hiệu lực. Bản V1.2 được giữ trong lịch sử Git, không tiếp tục làm baseline song song. Root spec/invariants/adr do người dùng cung cấp được giữ nguyên tại máy và bỏ qua trong Git.

## Invariant migration

| ID V1.2 | Nghĩa / đích V1.3 |
| --- | --- |
| INV-001..006 | Giữ ID; INV-006 được làm rõ serving-count semantics |
| INV-007 Attendance != production | Không chuyển một-một; giữ domain distinction tại §9.4 và ADR-004, thêm seam serving count trong INV-006 |
| INV-008 Retail observations | INV-007 |
| INV-009 Procurement resilience | INV-008 |
| INV-010 Budget feasibility != checkout certainty | Không chuyển một-một; giữ nguyên tắc tại §10.9/ADR-007 và INV-007/009 |
| INV-011 Uncalibrated risk != probability | INV-009 |
| INV-012 Hard constraint relaxation | INV-010 |

INV-011..030 của V1.3 là execution/validation/learning/horizon contracts; không được gán nghĩa từ ID trùng số của V1.2. Historical PR/commit/issue phải đọc cùng version gốc.

Các bản ADR-001..008 được cung cấp vẫn dẫn ID V1.2. Bản canonical trong docs/adr được normalize invariant links sang V1.3 và thêm alignment note từ spec §8.4. ADR-009..011 và spec/invariant mirrors giữ nguyên nội dung nguồn. Không tạo quyết định kiến trúc mới để thay đổi baseline người dùng đã chốt.

## Backlog migration

Giữ issue GitHub theo nội dung công việc để không chuyển lịch sử Household sang Units. Mã MTR là business identifier; số issue # là định danh GitHub độc lập.

| Mã V1.2 | Mã V1.3 | Nội dung / issue giữ nguyên |
| --- | --- | --- |
| MTR-001 | MTR-001 | Glossary/invariants — #1 |
| MTR-002 | MTR-002 | Benchmark/mutation harness — #2 |
| MTR-003 | MTR-004 | Household — #3 |
| MTR-004 | MTR-005 | MealParticipants — #4 |
| MTR-005 | MTR-006 | NutritionPolicyEngine — #5 |
| MTR-006 | MTR-007 | NutritionResolutionEstimator — #6 |
| MTR-007 | MTR-008 | PlanPolicyResolver — #7 |
| MTR-008 | MTR-009 | Budget baseline/pressure — #8 |
| MTR-009 | MTR-010 | Retail evidence — #9 |
| MTR-010 | MTR-011 | ProcurementClass — #10 |
| MTR-011 | MTR-012 | PlanningPriceQuote/calibration — #11 |
| MTR-012 | MTR-013 | SPEND_LIMIT stress — #12 |
| MTR-013 | MTR-014 | AP→EP/cooking yield — #13 |
| MTR-014 | MTR-015 | Inventory ledger — #14 |

MTR-003 mới (Units) và MTR-016..050 là các work items bổ sung. BACKLOG.md ghi canonical acceptance criteria và issue tương ứng. Issue cũ được giữ historical V1.2 body trong phần migration; dependencies/reference IDs trong active criteria dùng V1.3. Không đóng issue dựa trên việc tạo scaffold.

## Compatibility và phạm vi

- Giữ nguyên health API và generated client contract; đây vẫn là foundation.
- Giữ schema synthetic-v2 và 22 fixture provenance V1.2; chưa nâng thành production execution/validation contracts.
- 14 namespace cũ mở rộng thành 16 theo §16.4; validation/learning chỉ có namespace/import policy.
- Chưa có units/snapshot/lifecycle schemas freeze; entry criteria Milestone 0/1 vẫn partial.
- Shortcut cá nhân, raw imports, secrets, dependencies và Smart Menu không thuộc commit.
