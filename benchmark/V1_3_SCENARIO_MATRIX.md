# Benchmark/mutation matrix V1.3

Theo spec §18.7–18.9 và §8.4; đây là ma trận triển khai, không là kết quả benchmark giả. 22 fixtures hiện có vẫn là synthetic-v2, provenance V1.2. Production adapter chưa có; tất cả dòng PARTIAL/PENDING không chứng minh launch readiness.

| Nhóm | Bằng chứng hiện có | Phần phải bổ sung | Trạng thái |
| --- | --- | --- | --- |
| 1/3/7 ngày; 2/3 bữa | Fixtures 01–04 | Household schedule thực | PARTIAL |
| Loose/tight/no budget, TARGET | 05–07 + baseline | TARGET utility đầy đủ; actual sunk spend revision | PARTIAL |
| Inventory no/rich/expiring | 08–09, 20 | Confirmed/Operational/Planning views và reconcile | PARTIAL |
| Small/medium/large catalog | Candidate-count metadata | Large-pool reference/grounded variant pressure | PARTIAL |
| Goal presets | 16–17 + maintain | Root goal/nutrition policies; safety contract mutation | PARTIAL |
| Exclusions/preferences/participants | 10 exclusion micro-test | Member safety vs aggregate summaries; actor attribution | PARTIAL |
| Package/catch-weight/shelf-life | 11 fixed packs + expiry | CATCH_WEIGHT/LOOSE_SCALE và actual timing | PARTIAL |
| Fresh/stale/fallback/missing | 12–14, 18–22 + evidence fault injection | ProcurementClass fragility/calibration | PARTIAL |
| Required stress scenarios | 15 + required/optional policy tests | Partial purchase → sunk actual + future stress only | PARTIAL |
| Seam 1 batch micro-adjustment | Chưa có | Ingredient allocation recompute; reject implicit serving inflation | PENDING |
| Seam 2 sunk spend revision | Chưa có | Không stress lại fulfilled purchase; không bỏ qua actual overspend | PENDING |
| Seam 3 horizon bridge | Chưa có | Raw reservation/prepared output không double-count; scheduled exposure | PENDING |
| Seam 4 shared meal attribution | Chưa có | Hard safety từng participant; direct preference đúng actor/member | PENDING |
| Seam 5 forced choice quarantine | Chưa có | FORCED_CONFLICT_RESOLUTION không update voluntary taste/context | PENDING |
| Mutation: bad units/yield | Chưa có | AP/EP/cooked/serving basis mismatch + omitted/double yield | PENDING |
| Mutation: temporal causality | Chưa có | Consume-before-acquire; expiry; double reservation; negative intermediate stock | PENDING |
| Mutation: snapshots/revisions | Chưa có | Stale subject hash; modified materialized past; broken assumption parent | PENDING |
| Mutation: learning integrity | Chưa có | Cooked != liked; passive != durable; retail friction != taste penalty | PENDING |

Hiện có corrupted-output tests (missing procurement, wrong objective, expiry/overdraw, stale price gate) trong benchmark/tests. Chúng không thay mutation corpus của ADR-010. Không tạo lifecycle fixture/schema tạm để né việc freeze contracts MTR-003/025/026.

Metrics mới cần thêm sau khi model hỗ trợ: findings severity/code + validation_ms/hash retry; actual_sunk_spend/remaining scenario spend; intermediate stock violations; assumption debt/correction; exposure/exploration mix. Hiện runner chỉ xuất các metric micro-model đã tính thật. Numeric launch gates vẫn mở §24.3.
