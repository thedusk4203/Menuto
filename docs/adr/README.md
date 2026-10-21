# Danh mục quyết định kiến trúc

ADR (Architecture Decision Record) là bản ghi bối cảnh, lựa chọn, lý do và hệ quả của một quyết định kiến trúc.

Nguồn chuẩn: đặc tả V1, mục 24.1. **Hiện mới có danh mục cần hoàn thiện, chưa có ADR riêng được duyệt.** Các nguyên tắc đã chốt trong đặc tả vẫn có hiệu lực; phần cần quyết định bên dưới chưa được coi là hợp đồng triển khai.

| ID | Chủ đề | Nền tảng đã có trong đặc tả | Nội dung cần hoàn thiện |
| --- | --- | --- | --- |
| ADR-001 | Modular Monolith boundaries | Backend modular monolith; 12 domain; PostgreSQL; không microservices V1 | Cấu trúc code, hợp đồng liên module và ranh giới transaction |
| ADR-002 | Ingredient vs RetailProduct separation | Ingredient tách Product, Package, Retailer và PriceObservation | Mapping, đơn vị/quy đổi và quy tắc dữ liệu đủ điều kiện cho planner |
| ADR-003 | Planner trusted boundary and AI role | Engine xác định và validator là nguồn kiểm chứng; AI hiểu ý định/giải thích | Đầu vào/đầu ra AI, kiểm chứng, consent và xử lý lỗi |
| ADR-004 | Hard/soft constraints and relaxation policy | Hard/soft có nguồn; không âm thầm nới; dị ứng và safety không do AI quyết định | Chính sách version hóa, mức được phép đề xuất và luồng người dùng chấp nhận |
| ADR-005 | Planner versioning + reproducibility snapshots | Lưu phiên bản planner/policy/recipe/target và snapshot dữ liệu liên quan | Cấu trúc snapshot, fingerprint, replay và lưu trữ |
| ADR-006 | Inventory ledger/event model | Lot, expiry, reservation và event; không tồn kho âm hoặc giữ chỗ trùng | Ngữ nghĩa sự kiện, transaction, optimistic concurrency và xác nhận mua/tiêu thụ |
| ADR-007 | Retail price freshness/confidence policy | Giá có nguồn, thời điểm và confidence; stale/fallback phải hiển thị | Ngưỡng freshness theo nguồn, fallback và xử lý dữ liệu thiếu |
| ADR-008 | Benchmark/reference-solve acceptance policy | Pool lớn/timeout dài làm reference; đo quality gap và runtime | Fixture, môi trường, timeout, ngưỡng chấp nhận và regression gate |

## Khi viết từng ADR

Dùng tên `NNN-short-title.md` với ID tương ứng, ghi trạng thái Proposed/Accepted/Superseded, ngày, các mục đặc tả liên quan, bối cảnh, lựa chọn được xét, quyết định, hệ quả và cách kiểm chứng.

Chỉ chuyển sang Accepted khi nội dung đã được rà soát và chốt. Không điền ngưỡng giá, timeout hoặc quality gap tùy ý để làm tài liệu trông hoàn chỉnh. Nếu quyết định làm thay đổi yêu cầu đã có, cập nhật đặc tả cùng ADR.
