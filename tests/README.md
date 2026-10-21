# Chiến lược kiểm thử

Nguồn chuẩn: đặc tả V1, mục 18 và 23. **Chưa có mã kiểm thử, runner hoặc CI; tài liệu này là hướng dẫn cho các đợt triển khai tiếp theo.**

| Lớp kiểm tra | Hành vi cần chứng minh khi có code |
| --- | --- |
| Domain unit | Công thức dinh dưỡng, quy đổi đơn vị, hạn dùng, giá và phép tính package |
| Planner model | Bài toán nhỏ có tính khả thi/nghiệm tối ưu biết trước |
| Property-based | Không tồn kho âm, không vượt ngân sách cứng, không chọn nguyên liệu bị loại |
| Integration | Generate → validate → save → shopping → inventory reservation |
| Golden scenarios | Kế hoạch 1/3/7 ngày với dữ liệu có nguồn và kết quả được rà soát |
| Benchmark | Chất lượng và runtime V4 so với reference; V3 chỉ khi có adapter và điều kiện so sánh phù hợp |
| Frontend | Onboarding, generate, swap, Shop, Today; bàn phím và responsive |
| Data quality | Nutrition, giá, shelf-life và product mapping đủ điều kiện |

## Quy tắc bằng chứng

- Validator phải kiểm tra đầu ra theo đường triển khai độc lập; test solver tự so với chính logic của nó không đủ chứng minh đúng.
- Phân biệt OPTIMAL, FEASIBLE_BEST_EFFORT, PROVEN_INFEASIBLE, UNKNOWN_TIME_LIMIT và DATA_INSUFFICIENT.
- Mô tả đúng kiểm tra đã chạy, môi trường, phiên bản dữ liệu/policy và giới hạn; không gọi tài liệu hay file giữ chỗ là test đã pass.
- Không lấy dữ liệu cá nhân từ đồ án làm fixture. Tình huống lấy ý tưởng từ Smart Menu cần được viết lại theo domain mới và kiểm tra độc lập.
- Chọn runner, lệnh chạy và CI khi bắt đầu có code; ghi hướng dẫn có thể chạy lại ở thời điểm đó.

Xem [ma trận benchmark](benchmark/README.md). Thư mục integration hiện chỉ có file giữ chỗ.
