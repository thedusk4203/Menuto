# Milestone 0/1 — entry checklist V1.3

Đây là checklist theo §23.5. [Blueprint M0/M1 và phần nền tảng đã triển khai](IMPLEMENTATION_BLUEPRINT_M0_M1.md) là tài liệu chi tiết; checklist chưa đạt toàn bộ tiêu chí cho các workflow ở milestones sau.

| Điều kiện | Trạng thái | Công việc / bằng chứng cần có |
| --- | --- | --- |
| V1.3 + 11 ADR + 30 invariants cùng phiên bản | Có trong repository | Baseline consistency check; original spec/invariants byte-exact |
| Units/measurement-basis contracts freeze | Đã có primitives + schema snapshot kiểm drift | MTR-003; calculation tách storage + explicit quantization/provenance; tests từ chối incompatible bases, float và số không hữu hạn |
| Ownership/lifecycle/state diagrams | Draft tài liệu | ARCHITECTURE.md; cần gắn testable domain contracts MTR-004/015/016/017/023 |
| ValidationSubjectSnapshot + planner request/output draft schemas | Đã có `m0-draft.2`, chưa validation-ready | MTR-025/027; typed immutable source facts, hashes/revision lock; liệt kê rõ primitive contracts còn thiếu |
| Neutral benchmark format + mutation fixture format freeze | Một phần | synthetic-v2 regression giữ nguyên; mutation fixtures đầy đủ còn thiếu MTR-002/026 |
| CI chặn validation → planner/solver internals | Có static rule + negative tests | Bao gồm public-facade/relative-import và contracts đường vòng; chưa chứng minh runtime isolation |
| Selective Smart Menu reuse strategy | Đã giữ | Spec §22; không fork schema/code/lịch sử hoặc coi nguồn tham khảo là đã port |
| M1.1 Retail/Procurement foundation | Local checks đạt; remote CI chưa chạy | [Evidence](M1_1_RETAIL_PROCUREMENT_EVIDENCE.md); 0003/21 domain tables, mapping AP→EP, granularity/evidence/quote/procurement draft; không chứng nhận toàn bộ M0/M1 |

## Thứ tự chuẩn bị đề xuất

1. Freeze units/basis/provenance và ownership contracts (MTR-003/004/005).
2. Draft immutable intent/execution/validation subjects và dependency contracts (MTR-015/016/017/023/025/027).
3. Chốt neutral lifecycle + mutation fixture format cho năm seams; tạo fixtures known-valid/known-invalid có kết quả độc lập.
4. Review entry criteria trước khi build policy/solver/consumer workflows.

Numeric examples trong spec/debate không tự trở thành production defaults. Không chốt schema DB, thresholds hoặc thuật toán qua tài liệu khung này.
