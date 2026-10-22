# Invariant coverage — V1.3

Mỗi ID dưới đây dùng nghĩa trong canonical V1.3. SCAFFOLD_ONLY là ranh giới/tài liệu; MICRO_MODEL_ONLY là bằng chứng cho mô hình tổng hợp; PARTIAL_FOUNDATION là đã có primitive/schema tests nhưng chưa đầy đủ workflow; NOT_IMPLEMENTED là chưa có implementation tương ứng. Không dòng nào tuyên bố toàn bộ invariant đã được thực thi trong production.

| Invariant | Mức bằng chứng | Công việc | Bằng chứng hiện tại / gap |
| --- | --- | --- | --- |
| INV-001 | SCAFFOLD_ONLY | MTR-006, MTR-008 | Chưa có policy/physiology business tests |
| INV-002 | NOT_IMPLEMENTED | MTR-008, MTR-009 | Chưa có BudgetPressure hoặc intent resolver |
| INV-003 | PARTIAL_FOUNDATION | MTR-004 | Household/member schema + composite FK/PostgreSQL tests; authorization và các shared assets còn thiếu |
| INV-004 | PARTIAL_FOUNDATION | MTR-005, MTR-026 | Participant identity/portion và canonical safety draft tests; shared-meal hard-safety enforcement chưa có |
| INV-005 | SCAFFOLD_ONLY | MTR-018, MTR-019 | Chưa có authored rule/grounding service |
| INV-006 | MICRO_MODEL_ONLY | MTR-019, MTR-023, MTR-030 | Candidate quantities cố định; chưa có serving-count seam |
| INV-007 | PARTIAL_FOUNDATION | MTR-010, MTR-012 | M1.1 raw observation/derived quote tách bảng; provenance/origin/availability và SQL guards; chưa production eligibility/live integration |
| INV-008 | PARTIAL_FOUNDATION | MTR-011, MTR-022 | M1.1 class/member/primary/backup/package/substitution/source/promo primitives; chống backup giả; chưa fragility scoring/economic optimizer |
| INV-009 | PARTIAL_FOUNDATION | MTR-012, MTR-047 | M1.1 ordinal confidence, category calibration evidence và explicit reference origin; không probability/P90, chưa empirical calibration/backtest |
| INV-010 | MICRO_MODEL_ONLY | MTR-013, MTR-031 | Timeout/stress policy tests; chưa có acceptance/activation |
| INV-011 | NOT_IMPLEMENTED | MTR-015, MTR-034 | Chưa có quantitative fulfillment hoặc physical ledger |
| INV-012 | NOT_IMPLEMENTED | MTR-017, MTR-036 | Chưa có confirmed/operational assumptions |
| INV-013 | NOT_IMPLEMENTED | MTR-017, MTR-036 | Chưa có evidence→confirmed state implementation |
| INV-014 | NOT_IMPLEMENTED | MTR-037 | Chưa có local-first repair escalation |
| INV-015 | MICRO_MODEL_ONLY | MTR-026 | Micro verifier kiểm arithmetic; chưa có production orchestrator |
| INV-016 | SCAFFOLD_ONLY | MTR-026 | test_architecture.py chặn solver/facade/contract backdoor; chưa chứng minh full semantic independence |
| INV-017 | PARTIAL_FOUNDATION | MTR-025, MTR-026 | M1.1 mapping/package/source primitive chain và quote recomputation guards; micro-model arithmetic còn giữ; chưa production Independent Validator/nutrition path |
| INV-018 | PARTIAL_FOUNDATION | MTR-003, MTR-014, MTR-025 | Exact units/provenance; M1.1 Product→Ingredient mapping version/review/basis, AP→EP precision và inventory-origin draft; full validation chain chưa có |
| INV-019 | MICRO_MODEL_ONLY | MTR-015, MTR-026 | Expiry/overdraw kiểm trong micro-model; chưa có chronological acquisition/raw/prepared replay |
| INV-020 | NOT_IMPLEMENTED | MTR-006, MTR-026 | Chưa có root-contract guards bỏ qua planner summaries |
| INV-021 | NOT_IMPLEMENTED | MTR-025, MTR-026 | Chưa có PRECOMMIT/POSTFACT gate/hash lock |
| INV-022 | NOT_IMPLEMENTED | MTR-039, MTR-041 | Chưa có passive evidence quarantine/provisional exposure |
| INV-023 | NOT_IMPLEMENTED | MTR-039 | Chưa có attribution retail/context ≠ taste |
| INV-024 | NOT_IMPLEMENTED | MTR-039, MTR-040 | Chưa có cooked→context/exposure routing |
| INV-025 | NOT_IMPLEMENTED | MTR-039, MTR-040 | Chưa có unattributed rejection evidence handling |
| INV-026 | NOT_IMPLEMENTED | MTR-005, MTR-040 | Chưa có member actor-scoped preference write |
| INV-027 | NOT_IMPLEMENTED | MTR-024, MTR-040 | Chưa có separable behavioral vector |
| INV-028 | NOT_IMPLEMENTED | MTR-008, MTR-042 | Chưa có learned observation promotion/reset UX |
| INV-029 | NOT_IMPLEMENTED | MTR-031, MTR-039 | Chưa có forced-trade-off quarantine |
| INV-030 | NOT_IMPLEMENTED | MTR-038, MTR-041 | Chưa có horizon bridge commitments/exposure |

Bằng chứng micro-model: benchmark/tests/test_harness.py và test_foundation_regressions.py. Bằng chứng static: apps/backend/tests/test_architecture.py. Baseline consistency test kiểm numbering/coverage/link, không thay business tests. Full correctness/mutation corpus phải theo ADR-010 và benchmark/V1_3_SCENARIO_MATRIX.md.

[Evidence M1.1](M1_1_RETAIL_PROCUREMENT_EVIDENCE.md) bổ sung 68 unit/contracts và 106 real-PostgreSQL tests cho Retail/migration. INV-003/011/013 giữ ranh giới ownership/intents, chưa thay trạng thái physical lifecycle. Không hàng nào được nâng thành full production compliance; remote CI cho working tree chưa chạy.
