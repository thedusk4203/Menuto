# Bằng chứng — blueprint và data/contracts foundation

Ngày kiểm: 2026-10-22. Môi trường: Windows, Python 3.13.14, PostgreSQL 18.4, SQLAlchemy 2.1.5, Pydantic 2.14.1, Alembic 1.20.0.

Phạm vi được thực hiện: [blueprint M0/M1](IMPLEMENTATION_BLUEPRINT_M0_M1.md), neutral units/provenance/contracts, draft planner/validation handoffs, migration đầu tiên và household bootstrap nội bộ. Không phải completion report cho toàn bộ Milestone 0/1.

| Kiểm tra thực chạy | Kết quả |
| --- | --- |
| Python suite với `MENUTO_TEST_POSTGRES_URL` | 162 passed; 1 Starlette/httpx deprecation warning có từ dependency hiện tại |
| Real PostgreSQL tests trong suite | 18 passed; mỗi run tự tạo và xóa database ngẫu nhiên riêng |
| Migration | Upgrade → metadata drift check → downgrade → upgrade thành công trên PostgreSQL thật |
| Household integrity | Composite FK từ chối membership/profile/safety member thuộc household khác, gồm kiểm SQLSTATE foreign-key violation |
| Numeric/basis/provenance | Primitive tests từ chối float, NaN/Infinity, negative quantity, excess precision, mixed bases/currencies; PostgreSQL CHECK chặn invalid basis/nonfinite nutrients |
| Persistence semantics | Caller rollback hoàn tác bootstrap; source fact SQL UPDATE/DELETE bị chặn; hai session profile stale write gây StaleDataError |
| Synthetic benchmark | 22/22 scenarios passed; giữ nguyên micro-model/fixture provenance |
| Python lint + import/baseline checks | Passed; 16 contexts, canonical docs 30 invariants/11 ADR/50 task links |
| OpenAPI + domain schema export checks | Passed; OpenAPI vẫn chỉ có health, domain drafts ở bundle riêng |
| Generated API client | Schema drift check + TypeScript typecheck passed, 10 tests passed |
| Web build | Passed |

API test và PostgreSQL cần loopback; sandbox tại máy chặn socket nên lần chạy trong sandbox bị chờ. Kết quả thành công phía trên là lần chạy ngoài sandbox trên cùng source. Không thay runtime logic để né lỗi môi trường.

GitHub Actions được cấu hình thêm PostgreSQL service và domain-schema drift check. Trạng thái remote CI được đối chiếu theo commit/PR; bảng trên là bằng chứng chạy tại máy. Dữ liệu test là synthetic, không có household/health/retailer thật. Không provision database ứng dụng hoặc triển khai endpoint nghiệp vụ.

Chưa kiểm chứng/triển khai: authorization/consent, idempotent business command executor, inventory/reservation transactions, recipe/retail persistence, ActivePlan/revisions/execution, primitive recomputation/chronological validation, planner/learning hoặc consumer workflow. Hash ở draft không tự là activation gate; draft output/report buộc quyền activation bằng false.

Graphify hiện lưu snapshot baseline V1.3 trước phần units/persistence mới; không dùng graph đó làm bằng chứng mọi contract/schema M0/M1 đã được lập bản đồ.
