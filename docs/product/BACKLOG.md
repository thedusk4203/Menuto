# MTR-001 → MTR-014

Nguồn chuẩn: Development Spec V1.2 §21. GitHub issues là nơi theo dõi execution; bảng dưới đây được tạo cùng lần khởi tạo, trạng thái mới nhất xem trên GitHub.

| Issue | Nội dung | Phụ thuộc ban đầu | Trạng thái khi khởi tạo |
| --- | --- | --- | --- |
| [MTR-001](https://github.com/thedusk4203/Menuto/issues/1) | Domain glossary + invariants | — | Mở |
| [MTR-002](https://github.com/thedusk4203/Menuto/issues/2) | Benchmark harness | MTR-001 | Mở |
| [MTR-003](https://github.com/thedusk4203/Menuto/issues/3) | Household-first schema | MTR-001 | Mở |
| [MTR-004](https://github.com/thedusk4203/Menuto/issues/4) | MealParticipants model | MTR-003 | Mở |
| [MTR-005](https://github.com/thedusk4203/Menuto/issues/5) | NutritionPolicyEngine | MTR-001, MTR-003 | Mở |
| [MTR-006](https://github.com/thedusk4203/Menuto/issues/6) | NutritionResolutionEstimator | MTR-005 | Mở |
| [MTR-007](https://github.com/thedusk4203/Menuto/issues/7) | PlanPolicyResolver | MTR-005 | Mở |
| [MTR-008](https://github.com/thedusk4203/Menuto/issues/8) | Budget baseline/pressure | MTR-007 | Mở |
| [MTR-009](https://github.com/thedusk4203/Menuto/issues/9) | Retail evidence schema | MTR-001 | Mở |
| [MTR-010](https://github.com/thedusk4203/Menuto/issues/10) | ProcurementClass builder | MTR-009, MTR-013 | Mở |
| [MTR-011](https://github.com/thedusk4203/Menuto/issues/11) | PlanningPriceQuote + calibration | MTR-009, MTR-010 | Mở |
| [MTR-012](https://github.com/thedusk4203/Menuto/issues/12) | SPEND_LIMIT stress scenarios | MTR-007, MTR-010, MTR-011 | Mở |
| [MTR-013](https://github.com/thedusk4203/Menuto/issues/13) | AP→EP mapping | MTR-009 | Mở |
| [MTR-014](https://github.com/thedusk4203/Menuto/issues/14) | Inventory ledger + policy | MTR-003, MTR-009 | Mở |

Dependencies là thứ tự triển khai đề xuất, không thay đổi acceptance criteria trong đặc tả. Một số issue cần phối hợp phần ngoài nhóm này, ví dụ grounded recipe schemas MTR-015/016 hoặc Validator MTR-022; chưa tạo các issue đó trong đợt này.

Namespace scaffold không đồng nghĩa nghiệp vụ hoàn tất. MTR-001/002 đã có nền ban đầu nhưng vẫn mở; MTR-003..014 chưa có implementation production. Các numeric constants và launch thresholds vẫn theo open questions §24.3.
