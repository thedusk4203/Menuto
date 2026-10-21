# Ma trận tình huống benchmark

Nguồn chuẩn: đặc tả V1, mục 2.2, 10–11, 18 và 23.

**Trạng thái: thiết kế tình huống; chưa có fixtures, harness, solver hoặc kết quả đo.** Các kỳ vọng dưới đây là điều cần kiểm chứng khi triển khai, không phải kết quả đã quan sát.

## Các chiều dữ liệu phải phủ

| Chiều | Biến thể theo đặc tả |
| --- | --- |
| Horizon và lịch ăn | 1/3/7 ngày; 2 hoặc 3 bữa/ngày |
| Ngân sách | Rộng, chặt, không đặt giới hạn |
| Inventory | Không có, nhiều đồ dùng được, sắp hết hạn |
| Catalog | Nhỏ, vừa, lớn |
| Mục tiêu | High protein, maintain, calorie deficit |
| Ràng buộc/sở thích | Nhiều loại trừ; sở thích và đa dạng |
| Package và shelf-life | Bước mua lớn; thời gian bảo quản ngắn |
| Giá | Fresh, stale, fallback |

Không cần tích Descartes toàn bộ tổ hợp ngay. Bộ fixture đầu tiên phải phủ các chiều trên và các lỗi đã biết; ADR-008 sẽ chốt kích thước tập, môi trường và ngưỡng.

## Những tình huống cần tạo trước

| ID | Tình huống | Điều cần kiểm chứng |
| --- | --- | --- |
| BM-01 | Bài toán nhỏ, dữ liệu đầy đủ | So với nghiệm/tính khả thi tính độc lập |
| BM-02 | Ngân sách chặt nhưng có inventory dùng được | Precheck không loại nhầm nghiệm do bỏ qua inventory |
| BM-03 | Nhiều món rẻ cùng tồn tại món phù hợp nutrition/preference | Shortlist không bị lấp bởi cheapest-first; đối chiếu reference pool |
| BM-04 | Một bữa có nhiều thành phần | Không chấm mỗi thành phần bằng target của toàn bữa |
| BM-05 | Các đơn vị kcal và gram khác thang đo | Objective dùng normalized deviation/basis points |
| BM-06 | Dừng trước khi có nghiệm vì hết thời gian | UNKNOWN_TIME_LIMIT không thành PROVEN_INFEASIBLE |
| BM-07 | Package lớn và budget strict | Số package nguyên; tổng tiền mua thực không vượt budget |
| BM-08 | Inventory hết hạn, giữ chỗ và tiêu thụ | Không dùng quá hạn, không âm kho hoặc giữ chỗ trùng |
| BM-09 | Thiếu nutrition, product mapping hoặc giá usable | Phân biệt DATA_INSUFFICIENT với vô nghiệm toán học |
| BM-10 | Giá stale/fallback và carryover | Ghi rõ nguồn/confidence; không coi mọi carryover là waste |
| BM-11 | Allergy, exclusion và yêu cầu xung đột | Không có hard violation hoặc silent relaxation; advice sau proven infeasible theo policy |
| BM-12 | Swap/regenerate một phần kế hoạch | Revalidate toàn kế hoạch; giữ constraint hoặc trình bày thay đổi cần chấp nhận |

Mỗi fixture cần xác định dữ liệu đầu vào, phiên bản, điều kiện hợp lệ, kỳ vọng và cách kiểm tra độc lập. Các trường hợp timeout cần cách kích hoạt kiểm soát được; không dùng độ chậm ngẫu nhiên làm bằng chứng.

## Đầu ra và điều kiện chấp nhận sau này

Harness cần ghi status, solve time, phase, candidate count; vector objective; nutrition deviation; purchase cost; inventory used; waste/carryover; số món, thời gian nấu, shopping days và products; phiên bản/snapshot liên quan.

Reference dùng candidate pool lớn và thời gian dài hơn. So sánh trên dữ liệu và chính sách tương thích; không diễn giải reference còn best-effort là optimum đã chứng minh. ADR-008 phải chốt timeout, giới hạn quality gap và ngưỡng regression trước khi dùng làm gate CI. Hiện chưa có ngưỡng hoặc điểm benchmark.
