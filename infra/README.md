# Infrastructure boundary

V1 dùng PostgreSQL và Alembic làm migration runner duy nhất. Chưa có schema/migration hoặc tài nguyên cloud được tạo. MTR-003, MTR-009 và MTR-014 sẽ bổ sung schema thật. Không dựng database demo rồi coi đó là dữ liệu production.

Queue/worker, object storage, deployment và secrets của môi trường vận hành chỉ thêm khi cần theo đặc tả. Chưa có dịch vụ AI, retailer adapter hoặc dữ liệu thật.
