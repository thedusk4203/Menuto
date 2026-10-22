# Backend foundation

FastAPI modular monolith theo V1.3 §8, §9 và §16. Có 16 namespace domain, hiện chưa có schema nghiệp vụ hoặc database migration. PostgreSQL/SQLAlchemy/Alembic đã pin dependencies để triển khai MTR-004 và các mốc sau; chưa kết nối dữ liệu.

Từ root repository:

```powershell
uv sync --locked
uv run uvicorn app.main:app --reload
```

`GET /api/v1/health` là process liveness, không phải readiness database/planner. Health luôn khai báo `stage=foundation`, `planner_ready=false`.

Không import benchmark adapter vào backend: micro-model chỉ dùng kiểm tra harness, không được cung cấp như Planner V4. Không dùng `create_all()` để thay migration runner.

`validation` và `learning` được tách theo ADR-010/011, hiện chỉ namespace. Chưa có production validator/learning engine, state projections hoặc DB migration.
