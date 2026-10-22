# Contracts

Nguồn hợp đồng HTTP: OpenAPI sinh từ FastAPI. Chỉ có health endpoint, chưa có PlanRequest hoặc Planner API.

`uv run python tools/export_openapi.py` cập nhật openapi.json; `npm run contracts:generate` sinh type TypeScript, JSON Schema và standalone response validator trong packages/api-client. Không chỉnh tay các file generated.

CI kiểm tra hai chiều: schema snapshot phải khớp backend, generated client phải khớp snapshot. Client tests kiểm tra runtime payload/HTTP/cancellation; typecheck kiểm tra đường dẫn/phương thức theo hợp đồng. HealthResponse serialization schema yêu cầu đủ các field backend luôn gửi; wire response không đổi.

Không đưa PlanningMode vào hợp đồng mới. Business contracts được chốt theo đặc tả trước khi thêm endpoint nghiệp vụ.

## Domain foundation contracts

`domain.schema.json` là bundle `$defs` riêng từ Pydantic, không quảng bá HTTP endpoint. Chọn definition cụ thể để validate; không dùng cả bundle như root schema của một request. Sinh/kiểm bằng `uv run python tools/export_domain_contracts.py [--check]`.

Units/basis, money, provenance và household/catalog/member source contracts đã có implementation. Planner request/output, validation subject/report và mutation fixtures mang version `m0-draft.1`; chưa đủ để solve/validate/activate plan. Python validators kiểm thêm quan hệ giữa fields; JSON Schema không biểu diễn hết các guard này. Chưa sinh TypeScript client cho domain drafts.
