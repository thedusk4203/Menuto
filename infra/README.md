# Infrastructure boundary

V1 dùng PostgreSQL và Alembic làm migration runner duy nhất. Migration `0001` đã có schema đầu tiên cho household/member/catalog, được kiểm trên PostgreSQL 18.4 riêng. Chưa provision database ứng dụng hoặc tài nguyên cloud. Xem [hướng dẫn database/tests](../apps/backend/README.md) và [blueprint M0/M1](../docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md).

Queue/worker, object storage, deployment và secrets của môi trường vận hành chỉ thêm khi cần theo đặc tả. Chưa có dịch vụ AI, retailer adapter hoặc dữ liệu thật.
