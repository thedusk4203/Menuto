# Benchmark harness — synthetic foundation

MTR-002, đặc tả V1.2 §10.12, §18. Đây là harness chạy thật cho micro-model, **không phải Planner V4**. Fixtures tổng hợp mới từ tình huống trong đặc tả; chưa port fixtures Smart Menu vì source cũ không còn trong workspace.

```powershell
uv sync --locked
uv run menuto-benchmark --output benchmark/results/latest.json
uv run pytest benchmark/tests
```

## Cách kiểm chứng

1. Adapter CP-SAT chọn một candidate mỗi slot, giữ hard nutrition bands và exclusions, dùng inventory lot còn hạn, mua số package nguyên; SPEND_LIMIT kiểm tra các scenario giá được cung cấp.
2. Tối ưu lexicographic hai phase của micro-model: normalized comfort violation, rồi chi phí mua. Seed 42, một worker, timeout mặc định 5 giây **mỗi phase**.
3. Reference độc lập không import OR-Tools: vét cạn lựa chọn, phân bổ FEFO bằng số học và làm tròn package. Reference bị chặn theo số tổ hợp để không chạy vô hạn.
4. Verifier kiểm tra riêng slot, nutrition, stock, expiry, procurement, scenarios và objective. Một bài toán có optimum [0, 600] được tính tay trong test.
5. JSON ghi runtime thực, status, vector objective, phase, candidate count, versions/config/fingerprint, reference và delta. CLI trả mã khác 0 khi sai kỳ vọng, sai nghiệm, chưa chứng nhận reference hoặc lỗi dữ liệu.

UNKNOWN_TIME_LIMIT không bị gọi là infeasible. Nếu phase sau hết giờ mà đã có incumbent phase trước, giữ FEASIBLE_BEST_EFFORT. DATA_INSUFFICIENT tách khỏi vô nghiệm. OPTIMAL chỉ đúng trong micro-model và candidate set đã cung cấp.

## Phạm vi của fixture

Các trường hợp phủ 1/3/7 ngày, 2/3 bữa, budget NONE/TARGET/SPEND_LIMIT, có/không có/sắp hết hạn inventory, package lớn, exclusions, giá fresh/stale/fallback, thiếu mapping, stress price và catalog nhỏ/vừa/lớn ở quy mô synthetic. Nhãn mục tiêu không phải preset dinh dưỡng production.

Mọi con số về nutrition, giá, package và scenario stress chỉ là hằng số fixture; **không phải khuyến cáo dinh dưỡng hoặc policy đã duyệt**. Giá stale bị chặn theo gate bảo thủ của micro-model, không phải freshness policy production.

## Giới hạn và mở rộng

- Mỗi ingredient có một sản phẩm; mọi hàng mua sẵn từ đầu và bảo quản được cả horizon; đơn vị nguyên synthetic, không phải gram hoặc tiền thật.
- Không có participant physiology, NutritionPolicyEngine, ProcurementClass đầy đủ, calibration, cooking batch, waste objective, Stage 2 utility, quantity refinement hoặc Validator V2.
- Reference dùng cùng candidate pool và vét cạn; chưa có reference pool lớn hơn hoặc quality-gap gate production.
- `BenchmarkAdapter` là điểm gắn adapter V4 sau này; không dùng adapter synthetic trong backend.
- Ngưỡng runtime/quality gap phát hành và policy constants vẫn mở theo §24.3. Gate exact equality hiện chỉ kiểm tra những bài toán nhỏ biết optimum.
- Results là artifact local/CI, không đưa runtime theo máy vào Git. CI lưu JSON làm artifact, không tuyên bố launch-ready.
