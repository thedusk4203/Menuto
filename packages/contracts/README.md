# Contracts

Nguồn hợp đồng HTTP hiện tại: OpenAPI sinh từ app FastAPI. Chỉ có health endpoint, chưa có PlanRequest hoặc Planner API.

`openapi.json` là snapshot được sinh lại bằng `uv run python tools/export_openapi.py`; CI kiểm tra snapshot khớp với API. Web dùng typed health client tối thiểu; hợp đồng nghiệp vụ sẽ được chốt trước khi triển khai. Không đưa PlanningMode vào hợp đồng mới.
