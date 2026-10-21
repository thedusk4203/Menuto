# Hướng dẫn đóng góp

## Phạm vi và nguồn chuẩn

Đọc [đặc tả V1](docs/MENUTO_DEVELOPMENT_SPEC_V1.md) trước khi thay đổi. Mỗi phần triển khai cần gắn với milestone hoặc mục backlog MTR tương ứng; không mở rộng sang non-goals V1 khi chưa có quyết định cập nhật đặc tả.

Nếu thay đổi sản phẩm hoặc kiến trúc đã chốt, cập nhật nguồn chuẩn và ADR liên quan cùng thay đổi. Không tự diễn giải nội dung chưa chốt thành yêu cầu đã được duyệt. Repository hiện chỉ có khung và tài liệu; chưa có hợp đồng API hay schema để cam kết tương thích.

Smart Menu chỉ là nguồn tham khảo. Không copy toàn bộ code, cấu hình, dữ liệu cá nhân hoặc secrets. Với phần định tái sử dụng, ghi rõ nguồn, lý do phù hợp với model mới và bằng chứng kiểm thử.

## Quy trình và commit

- Tách thay đổi theo mục đích; đọc diff và trạng thái Git trước khi stage.
- Commit theo dạng `type(scope): mô tả ngắn`; dùng `docs`, `chore`, `feat`, `fix`, `test` hoặc `refactor` phù hợp. Ví dụ: `docs(domain): làm rõ Ingredient và Product`.
- Với thay đổi sau lần khởi tạo, dùng nhánh làm việc và pull request để phần triển khai có thể được review.
- Mô tả thay đổi bằng vấn đề, hành vi sau sửa, kiểm tra đã chạy và giới hạn còn lại. Không ghi “đã hoàn tất” khi mới có khung hoặc kiểm tra tĩnh.
- Không force-push để ghi đè công việc chưa được phối hợp.

## Quy ước nội dung và code

Tài liệu hướng dẫn viết bằng tiếng Việt; giữ tên entity và thuật ngữ kỹ thuật thống nhất với đặc tả. Dùng UTF-8 và quy tắc xuống dòng trong `.editorconfig`/`.gitattributes`; không đổi toàn bộ định dạng của file không liên quan.

Định hướng stack từ mục 16 là Python 3.13+, FastAPI/Pydantic v2, SQLAlchemy 2/PostgreSQL, migration có một nguồn chuẩn và OR-Tools CP-SAT; frontend React/TypeScript. Chưa chốt phiên bản phụ thuộc, công cụ quản lý gói, Vite/Next.js hay công cụ test. Chốt và ghi lại khi tạo ứng dụng, dựa trên tương thích thực tế; không coi mô tả này là bộ cài đã tồn tại.

Giữ ranh giới 12 domain; đưa quy tắc nghiệp vụ về domain sở hữu, tránh truy cập hoặc sửa dữ liệu domain khác tùy tiện. Chi tiết giao tiếp giữa module sẽ được chốt trong ADR-001.

## Kiểm thử và CI

Theo [chiến lược kiểm thử](tests/README.md). Khi có code, bổ sung bằng chứng phù hợp với hành vi thay đổi; kiểm thử thuật toán phải có trường hợp biết trước tính khả thi hoặc nghiệm tối ưu và validator độc lập.

Chưa có test runner hoặc workflow CI. Trước mỗi thay đổi tài liệu, kiểm tra liên kết nội bộ, đường dẫn, nội dung bám đặc tả và danh sách file được stage. Chỉ tạo CI chạy kiểm tra thực khi có công cụ và mã tương ứng; không tạo build giả.

## Cấu hình, dữ liệu và secrets

- Chưa có biến môi trường bắt buộc hoặc `.env.example`. Khi ứng dụng có cấu hình, thêm mẫu chỉ chứa tên biến và giá trị giả an toàn, cùng hướng dẫn sử dụng.
- Giữ `.env`, token, khóa riêng, chuỗi kết nối thật và bản sao cơ sở dữ liệu ngoài Git. Không đưa dữ liệu cá nhân/sức khỏe vào fixtures hay log.
- `data/imports/` dành cho dữ liệu nhập tại máy và mặc định bị bỏ qua, ngoài file giữ chỗ. Chỉ đưa dữ liệu tổng hợp hoặc được phép sử dụng vào `data/seeds/` sau khi rà soát nguồn và chất lượng.
- Dữ liệu dùng cho planner phải có nguồn, thời điểm cập nhật và trạng thái chất lượng theo đặc tả. Không dùng giá hoặc dữ liệu dinh dưỡng giả như dữ liệu thực.
