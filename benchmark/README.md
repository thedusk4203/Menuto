# Benchmark harness — synthetic foundation

MTR-002, đặc tả V1.3 §10.12, §18. Đây là harness chạy thật cho micro-model, **không phải Planner V4**. Fixtures tổng hợp mới từ tình huống trong đặc tả; chưa port fixtures Smart Menu. Thư mục tham khảo Smart Menu đã được bổ sung lại tại máy nhưng không tự đưa vào Git hoặc coi là fixture đã port.

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

Mọi con số về nutrition, giá, package và scenario stress chỉ là hằng số fixture; **không phải khuyến cáo dinh dưỡng hoặc policy đã duyệt**. Micro-model chỉ cho mua khi giá fresh/fallback có amount. Product không dùng đến không chặn nghiệm; inventory đã có vẫn dùng được khi thiếu purchase price. Khi không có nghiệm trong tập bằng chứng tin cậy nhưng còn dữ liệu thiếu, trả DATA_INSUFFICIENT, không khẳng định vô nghiệm. OPTIMAL chỉ trong tập evidence tin cậy, không phải tối ưu qua các giá chưa biết.

## Giới hạn và mở rộng

- Mỗi ingredient có một sản phẩm; mọi hàng mua sẵn từ đầu và bảo quản được cả horizon; đơn vị nguyên synthetic, không phải gram hoặc tiền thật.
- Không có participant physiology, NutritionPolicyEngine, ProcurementClass đầy đủ, calibration, cooking batch, waste objective, Stage 2 utility, quantity refinement hoặc Independent Validator theo ADR-010.
- Reference dùng cùng candidate pool và vét cạn; chưa có reference pool lớn hơn hoặc quality-gap gate production.
- `BenchmarkAdapter` là điểm gắn adapter V4 sau này; không dùng adapter synthetic trong backend.
- Ngưỡng runtime/quality gap phát hành và policy constants vẫn mở theo §24.3. Gate exact equality hiện chỉ kiểm tra những bài toán nhỏ biết optimum.
- Results là artifact local/CI, không đưa runtime theo máy vào Git. CI lưu JSON làm artifact, không tuyên bố launch-ready.


## Synthetic format v2 và các gate độc lập

Có 22 fixtures. Tags được derive từ dữ liệu cuối: ngày/bữa, goal metadata, budget contract/amount, tồn kho, trạng thái giá và candidate count. Catalog buckets small ≤4 / medium ≤12 / large >12 chỉ là mô tả kích thước fixture; không là threshold production.

SPEND_LIMIT bắt buộc stress_policy có version và required_scenarios, gồm BASE; thiếu coefficients required là lỗi input. BASE luôn lấy từ product prices. Policy chỉ BASE phải có base_only_justification; các fixed-pack fixture exact-price không bị ép thêm stress thiếu cơ sở. Optional sensitivity scenarios không tự trở thành hard constraints.

TARGET trong micro-model chỉ kiểm tra khác biệt với hard cap; chưa có soft target-distance objective production. Stress infeasibility là solver outcome của micro-model, không thay thế budget outcome/Advisor V4.

CP-SAT, exhaustive reference và independent_data_check có ba cách kiểm tra evidence riêng. Reference/auditor không gọi solver eligibility helper. Mutation test cố tình làm solver chấp nhận giá stale và xác nhận reference cùng auditor phát hiện sai. Neutral shapes vẫn dùng chung schema; độc lập không có nghĩa toàn bộ parsing/type definitions được viết lại.

Schema/report version đổi thành synthetic-v2 / synthetic-benchmark-v2. Fixture input v1 phải tái sinh hoặc migrate rõ, không silently nhận thiếu stress policy.

## Baseline V1.3

22 fixture inputs giữ provenance `synthetic-from-spec-v1.2`; không relabel lịch sử hoặc coi là coverage cho execution/learning V1.3. Xem [scenario matrix](V1_3_SCENARIO_MATRIX.md) cho coverage/gaps của §18.8 và năm seams. synthetic-v2 format không đổi trong lần căn chỉnh baseline này.
