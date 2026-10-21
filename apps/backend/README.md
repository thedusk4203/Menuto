# Backend foundation

FastAPI modular monolith theo V1.2 §8, §9 và §16. Có 14 namespace domain, hiện chưa có schema nghiệp vụ hoặc database migration. PostgreSQL/SQLAlchemy/Alembic đã pin dependencies để triển khai MTR-003 và các mốc sau; chưa kết nối dữ liệu.

Từ root repository:

```powershell
uv sync --locked
uv run uvicorn app.main:app --reload
```

`GET /api/v1/health` là process liveness, không phải readiness database/planner. Health luôn khai báo `stage=foundation`, `planner_ready=false`.

Không import benchmark adapter vào backend: micro-model chỉ dùng kiểm tra harness, không được cung cấp như Planner V4. Không dùng `create_all()` để thay migration runner.
