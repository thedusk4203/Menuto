# Lộ trình phát triển

Nguồn chuẩn: đặc tả V1, mục 20–24. Đây là thứ tự công việc, không phải cam kết lịch phát hành.

## Hiện tại: khởi tạo repository

Đã có khung thư mục, đặc tả chuẩn, hướng dẫn đóng góp, ranh giới domain, danh mục ADR và ma trận benchmark. Chưa có ứng dụng, dữ liệu thật, test suite hoặc kết quả benchmark.

**Milestone 0 chưa hoàn tất.** Danh mục ADR chưa phải tám ADR đã được duyệt; ma trận benchmark chưa phải fixtures hoặc harness chạy được.

## Các milestone

| Mốc | Nội dung cần thực hiện | Điều còn thiếu để hoàn thành |
| --- | --- | --- |
| 0 — Foundation / decisions | Repo sạch; ADR; glossary và semantics hard/soft; quy ước code/test/CI; fixtures ban đầu từ tình huống Smart Menu | Hoàn thiện và duyệt tám ADR; chốt chi tiết thuật ngữ/ràng buộc; chọn công cụ và dựng kiểm tra thực khi có code; tạo và kiểm tra fixtures |
| 1 — Core data platform | Identity/profile/household; ingredient/nutrition/recipe; retail/product/package/price; inventory lot/event; quản trị chất lượng | Chưa triển khai |
| 2 — Planner V4 | Candidate đa tín hiệu/Pareto; feasibility inventory-aware; nutrition chuẩn hóa; package procurement; validator; benchmark/reference solve; reason codes | Chưa triển khai |
| 3 — Consumer V1 | Onboarding; generate/result; swap/regenerate; shopping; Today; inventory quick-add; AI parse/explain có giới hạn | Chưa triển khai |
| 4 — Public readiness | Security/privacy; provenance/freshness; observability; hiệu năng; accessibility; chất lượng catalog; launch/rollback | Chưa triển khai |

## Bắt đầu công việc tiếp theo

Ưu tiên MTR-001 (glossary và ADR baseline) rồi MTR-002 (benchmark harness), phối hợp nền dữ liệu MTR-003 theo đặc tả. Chọn công cụ, phiên bản và hợp đồng khi bắt đầu phần code tương ứng; không chuyển nguyên đồ án Smart Menu sang làm Menuto.

Các mục MTR-004 đến MTR-019 thuộc việc xây engine và trải nghiệm V1. MTR-020 đến MTR-022 cùng các mở rộng V1.5/V2 được giữ trong đặc tả, không kéo vào lần khởi tạo này.

Trước khi tuyên bố sẵn sàng phát hành, đối chiếu đầy đủ các điều kiện Planner DoD, Data DoD và Consumer launch gate ở mục 23; việc push code hoặc CI xanh riêng lẻ không chứng minh đã đạt.
