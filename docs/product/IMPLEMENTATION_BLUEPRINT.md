# Milestone 0/1 — entry checklist V1.3

Đây là khung chuẩn bị theo §23.5, không phải blueprint đã được phê duyệt hoặc production schema. Baseline hiện chưa đạt toàn bộ entry criteria.

| Điều kiện | Trạng thái | Công việc / bằng chứng cần có |
| --- | --- | --- |
| V1.3 + 11 ADR + 30 invariants cùng phiên bản | Có trong repository | Baseline consistency check; original spec/invariants byte-exact |
| Units/measurement-basis contracts freeze | Chưa có | MTR-003; explicit conversion + provenance, reject incompatible bases |
| Ownership/lifecycle/state diagrams | Draft tài liệu | ARCHITECTURE.md; cần gắn testable domain contracts MTR-004/015/016/017/023 |
| ValidationSubjectSnapshot + planner request/output draft schemas | Chưa có | MTR-025/027; immutable facts, hashes, provenance/revision lock |
| Neutral benchmark format + mutation fixture format freeze | Một phần | synthetic-v2 regression giữ nguyên; mutation fixtures đầy đủ còn thiếu MTR-002/026 |
| CI chặn validation → planner/solver internals | Có static rule + negative tests | Bao gồm public-facade/relative-import và contracts đường vòng; chưa chứng minh runtime isolation |
| Selective Smart Menu reuse strategy | Đã giữ | Spec §22; không fork schema/code/lịch sử hoặc coi nguồn tham khảo là đã port |

## Thứ tự chuẩn bị đề xuất

1. Freeze units/basis/provenance và ownership contracts (MTR-003/004/005).
2. Draft immutable intent/execution/validation subjects và dependency contracts (MTR-015/016/017/023/025/027).
3. Chốt neutral lifecycle + mutation fixture format cho năm seams; tạo fixtures known-valid/known-invalid có kết quả độc lập.
4. Review entry criteria trước khi build policy/solver/consumer workflows.

Numeric examples trong spec/debate không tự trở thành production defaults. Không chốt schema DB, thresholds hoặc thuật toán qua tài liệu khung này.
