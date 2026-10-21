# Đóng góp vào Menuto

Nguồn chuẩn: đặc tả V1.2, Architecture Invariants và ADR-001..008. Skill/tool chỉ hỗ trợ cách làm; không thay thế các quyết định đã khóa. Thay đổi mâu thuẫn ADR/invariant phải có ADR superseding được chốt trước.

- Làm từng phần nhỏ gắn với issue MTR; không mặc định đã hoàn thành cả issue chỉ vì tạo namespace.
- Tách domain theo V1.2 §9; backend không import benchmark synthetic model.
- Thay đổi API phải cập nhật hợp đồng OpenAPI và kiểm tra consumer.
- Python 3.13.14, uv.lock và OR-Tools exact version được quản lý trên Git. Frontend dùng Node 24, npm workspace và một package-lock.json tại root. Generator/client dùng TypeScript 5.9.3 theo peer requirement; web giữ TypeScript 7.0.2, cả hai được kiểm tra riêng.
- Chạy `uv run python tools/check_import_boundaries.py`, `npm run contracts:check`, `npm run typecheck:client`, `npm run test:client`, `npm run build:web` và `uv run ruff check .`, `uv run pytest`, `uv run python tools/export_openapi.py --check`, `uv run menuto-benchmark --output benchmark/results/latest.json`, và frontend build khi liên quan.
- Dùng fixture tổng hợp có nguồn và expected độc lập; không coi test coverage là bằng chứng đủ cho thuật toán.
- Không đưa secrets, dữ liệu cá nhân/sức khỏe hoặc raw imports lên Git. Không gọi heuristic confidence là xác suất khi chưa calibration.
- Commit theo `type(scope): mô tả`; nêu thay đổi, kiểm tra đã chạy, phần còn thiếu. Giữ issue chưa hoàn tất ở trạng thái mở.
- Không cài hook tự commit/push hoặc thực hiện gửi dữ liệu đến AI/retailer ngoài phạm vi công việc đã được yêu cầu.

- Main yêu cầu PR + required checks python/web, strict up-to-date; không direct push hoặc force-push kể cả admin. Repo solo yêu cầu 0 approvals để không tự khóa người sở hữu; việc qua PR/CI vẫn bắt buộc.
- Cross-context imports chỉ qua contracts/public và đúng hướng trong tools/check_import_boundaries.py; assistant không import repository nội bộ của planning. Shared không import domain; backend không import benchmark synthetic.
