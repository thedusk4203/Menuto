# Backend foundation

FastAPI modular monolith theo V1.3 §8, §9 và §16. Có 16 namespace domain, migration `0001` → `0010`, hiện có 54 bảng domain;0010 bổ sung hai bảng authoritative culinary intent. Xem [Implementation Blueprint M0/M1](../../docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md) và [correction evidence M1.2](../../docs/product/M1_2_CULINARY_BINDING_CORRECTIONS.md) để phân biệt phần đã triển khai và schema đích.

Từ root repository:

```powershell
uv sync --locked
uv run uvicorn app.main:app --reload
```

`GET /api/v1/health` là process liveness, không phải readiness database/planner. Health luôn khai báo `stage=foundation`, `planner_ready=false`.

Không import benchmark adapter vào backend: micro-model chỉ dùng kiểm tra harness, không được cung cấp như Planner V4. Không dùng `create_all()` để thay migration runner.

`validation` và `learning` được tách theo ADR-010/011, hiện chỉ namespace. Chưa có production validator/learning engine hoặc state projections.

## Persistence và tests

Đặt `MENUTO_DATABASE_URL` với driver `postgresql+psycopg` rồi chạy `uv run alembic upgrade head`. Database đích phải được tạo trước. Không tự kết nối hoặc chạy migration lúc API startup. Credentials không ghi vào repository.

```powershell
$env:MENUTO_DATABASE_URL = 'postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/menuto'
uv run alembic upgrade head
uv run python tools/export_domain_contracts.py --check
```

Integration tests cần `MENUTO_TEST_POSTGRES_URL` trỏ vào maintenance database `postgres` trên loopback. Test tự tạo database tên ngẫu nhiên `menuto_test_<uuid>`, chạy migration up/down/up, rồi xóa đúng database đó. Cần user có quyền CREATEDB; không dùng URL dữ liệu ứng dụng. Khi không có URL, tests PostgreSQL được ghi rõ skipped; CI có PostgreSQL service và chạy thật.

```powershell
$env:MENUTO_TEST_POSTGRES_URL = 'postgresql+psycopg://TEST_USER:TEST_PASSWORD@127.0.0.1:5432/postgres'
uv run pytest
```

Bootstrap household là service nội bộ nhận user đã tồn tại và không tự commit. Profile concurrency dùng ORM version counter; authorization, idempotent command execution và bulk-SQL CAS chưa có business service trong đợt này. Nutrition source facts append-only; correction tạo source version mới. Bảng yield chung đã được gỡ; M1.1 đã lưu edible yield ở Retail Product→Ingredient mapping, còn cooking yield thuộc Recipe/Preparation ở M1.2. Xem [sáu sửa đổi foundation](../../docs/product/FOUNDATION_CORRECTIONS.md).

Retail repository trả frozen `retail-v2` contracts và không tự commit. Tất cả facts Retail append-only; retailer status nằm ở history riêng. `0004` từ chối legacy CALIBRATED quotes và product có canonical ingredient mơ hồ; downgrade từ chối khi có Retail data. Quote chỉ expose reference_price_pair, chưa phải purchase cost. Calibration chỉ áp reference; promotion/coverage được derive. Quote/snapshot vẫn DRAFT, chưa có production eligibility/freshness/scoring policy hoặc ProcurementCostEvaluator. `RetailSourcedAPAssetDraft` draft.2 giữ mapping origin, không tạo lot. [Domain review A–G](../../docs/product/M1_1_RETAIL_DOMAIN_REVIEW.md) mô tả đầy đủ.

Recipe repository ghi aggregate nguyên tử và trả frozen `recipe-v1` snapshots. Trong cùng
giao dịch: tạo Recipe nếu chưa có, thêm version cùng toàn bộ child facts, rồi seal.
Không thêm child hoặc sửa/xóa nội dung cũ; correction tạo version mới. `0005` từ chối
downgrade khi có Recipe data. SQL guards kiểm cả completeness, tier arithmetic và
preparation context. Culinary binder chỉ chọn authored tier/rules và delta trong envelope;
không thực hiện generation, household safety hoặc Independent Validator.
[Review M1.2](../../docs/product/M1_2_RECIPE_DOMAIN_REVIEW.md) và
[evidence](../../docs/product/M1_2_RECIPE_PREPARATION_EVIDENCE.md).

`0006` cấm COUNT-targeted substitutions tại seal và từ chối upgrade nếu dữ liệu 0005 có
rule dạng này; cần xử lý/archival tường minh, không rewrite facts bất biến. Downgrade
0006 chỉ gỡ guard, không mất dữ liệu; protection của 0005 giữ nguyên. Binder chọn net
transformation đúng ingredient path; raw base không bị ép transform bởi alternate path.


## M1.3 physical inventory

0007 thêm 5 bảng (38 tổng). `InventoryService` ở `modules/inventory/public.py` nhận frozen
inventory-v1 commands; caller sở hữu transaction/commit. Important: rollback transaction
khi command lỗi; retry toàn transaction khi SQLSTATE 40001/deadlock, giữ nguyên idempotency
key và payload. Acquire cần caller-stable lot_id, explicit evidence và household editor.
Idempotency scope là household × source_system × key **trong từng family** movement,
reservation hoặc release; fingerprint phân biệt concrete command. External source identity
cũng unique trong từng family/household/provider. Không dùng key mới khi retry.

Snapshot khóa shared household fence; mọi DB inventory writer lấy exclusive fence trước lot
balance lock/update. Serializes writes per household (trade-off V1); balances dùng revision
để stale RR writers không tính trên snapshot cũ. Physical truth là immutable history, không
cache. Commands không nhận calculated quantity: caller phải quantize explicit trước storage.
Read snapshot là effective-time cutoff trong recorded facts, không future projection.

Reservations active tới explicit full release. Release + consume có thể cùng transaction,
nhưng phải giữ nondecreasing occurred_at/phase. Expiry không xóa vật chất hoặc auto-release
intent; `position.allocatable` bằng zero nếu unusable. Confidence trên lot là initial observation,
không phải confidence inference sau thời gian. CONFIRMED không là probability.

[M1.3 review](../../docs/product/M1_3_INVENTORY_DOMAIN_REVIEW.md),
[evidence](../../docs/product/M1_3_INVENTORY_PHYSICAL_LEDGER_EVIDENCE.md).


F / MTR-016 có PlanRevisionService trong execution/public (orchestration), PlanStore trong
planning/public và context-local shopping/cooking writers. Caller owns transaction.
create_workspace → propose tạo sealed immutable intent, không stock/reservation effects.
publish đòi stored PRECOMMIT authorization; production issuer chưa installed, không có
mint/bypass API. Successful transaction tests seed synthetic receipts bằng isolated
test DB-owner fixture. Không dùng fixture này để mở production activation.

Household inventory fence → plan row lock → inventory commands giữ lock order M1.3;
expected_generation và expected_revision kiểm cả authoring và acceptance. Idempotent
retry trả đúng immutable prior result; changed body cùng key bị reject. Khi 40001/deadlock,
retry toàn outer transaction. current_plan đọc exact head, horizon_handoff vẫn DRAFT.


MTR-019A: planning owns sealed culinary bindings; independent validation consumes the
read-only culinary-validation-input.v1 companion. [Review/evidence](../../docs/product/MTR_019A_CULINARY_BINDING_EVIDENCE.md).
No production PRECOMMIT issuer or cooking/meal execution. Database head0010; old migrations unchanged.

## Reviewed reference prior source (0014, historical implementation notes)

Current prior-source status is [FROZEN](../../docs/product/PREFERENCE_PRIOR_SOURCE_FREEZE_RECEIPT.md).
The original source-only boundaries below remain unchanged; the later pure exact-target consumer
has its own [freeze receipt](../../docs/product/EXACT_TARGET_PRIOR_SHRINKAGE_FREEZE_RECEIPT.md).
Current hierarchy SOURCE is separately frozen; see its canonical receipt and design-only next gate below.

The [approved design](../../docs/product/PREFERENCE_PRIOR_SOURCE_FOUNDATION_DESIGN.md) now has an
[additive implementation](../../docs/product/PREFERENCE_PRIOR_SOURCE_FOUNDATION_EVIDENCE.md).
Head0014 has78 domain tables.0001–0013 and frozen semantics remain unchanged. The migration
creates empty source storage and NOLOGIN privilege infrastructure; no providers, enrolled
principals, provider grants, prior values, credentials or policy defaults are seeded.

Provision separate SCRAM-authenticated administrator/curator/reader logins out of band.
Grant the administrator the menuto_prior_admin structural group, ordinary source clients
menuto_prior_client, and neither owner membership nor direct source mutation privileges.
Use the dedicated administration boundary to register a provider, enroll immutable role
bindings and append provider-scoped capability grants. Household roles are irrelevant here.
Remote source engines require TLS with sslmode=verify-full; do not reuse ordinary pooled
application credentials or assert request actors. No source HTTP endpoint is exposed.
The server needs PostgreSQL's standard `sslinfo` contrib extension files.0014 installs the
extension privately when absent or reuses an existing deployment extension. Only the private
backend-local TLS primitive is delegated to the source owner; no global statistics/monitoring
privilege is granted. Empty downgrade removes the new private extension, while preserving an
existing shared extension. Publishers/readers cannot execute the private helper directly.

The internal facade is `preferences/reference_priors.py`: register_reference_prior_provider,
enroll_reference_prior_principal, change_reference_prior_authority, publish_reference_prior,
retract_reference_prior and capture_reference_prior_sources. Caller owns commit/rollback.
After any rejected SQL operation, roll back; on serialization failure retry the complete
transaction explicitly. Idempotent receipt replay still checks current permission first.

Capture uses the same clean SQLAlchemy Session on an engine configured with
`isolation_level="REPEATABLE READ", postgresql_readonly=True` (or SERIALIZABLE).
It makes no hidden connection or commit. `reference_prior_resolution.resolve_reference_priors`
then replays without IO. Empty provider source has no default numeric prior.040B continues
to expose prior/shrunk_affinity UNAVAILABLE. No shrinkage/040C or next milestone is authorized.

New real-PG acceptance requires the same explicitly configured loopback maintenance test URL.
Its fixture provisions random separate SCRAM logins and temporarily prepends only their own
HBA rules using the isolated test server's privileged maintenance connection. Original HBA
bytes are restored and random databases/logins are removed afterward. These tests must never
target a production server. They do not use SET SESSION AUTHORIZATION to claim real login proof.
CI uses `tools/configure_ci_postgres_tls.py` to provision a disposable certificate in the
ephemeral PostgreSQL service and verify it with verify-full. Docker bridge traffic receives
no exception from the runtime TLS check. HBA changes are limited to exact test logins and
the observed client address; existing regression roles/rules stay unchanged.
Empty downgrade is supported; populated registry/enrollment/authority/source downgrade refuses
data loss. Credential secrets and structural cluster-role lifecycle are not downgrade-managed.

## Reviewed hierarchy relation/policy source (0015, FROZEN)

The user froze the SOURCE at `ee8a4de1b1c71ccbd56ea565e111718660711fa8` after approved
PR #104 and successful exact post-merge CI40432057006 (python/web;2807 tests).
[Canonical freeze receipt](../../docs/product/HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_FREEZE_RECEIPT.md)
supersedes historical pre-merge status in the implementation evidence. Head0015 has85 domain
tables and349 definitions; all frozen semantics remain unchanged. No production provider, login
enrollment, grant, relation, enabled direction or numeric coefficient is seeded.

Structural hierarchy roles are independent: `menuto_hierarchy_admin` and `menuto_hierarchy_client`.
Protected source/read-adapter owners are non-login roles; clients must never receive owner/admin
membership or direct source/owner-table mutation privileges. Credential provisioning remains out
of band. The normal interface requires an actual SCRAM login with immutable database/login OID/name
enrollment; prior-source grants, household roles, GUCs and actor UUIDs grant no hierarchy authority.
Remote connections require verify-full TLS with trusted server identity. Deployment administrators
are privileged trust roots, not application actors. The SOURCE is frozen; the consumer is not implemented.

Use the internal Preferences public facade: `register_hierarchy_provider`,
`enroll_hierarchy_principal`, `change_hierarchy_authority`, `publish_hierarchy_source`,
`capture_hierarchy_sources`, `resolve_hierarchy_sources`. Registration/enrollment/grants require
separate hierarchy administration. Publication/retraction requires the current provider capability,
checked after the frontier lock and before any idempotent receipt. Writes require caller-owned
read-write SERIALIZABLE transactions; callers handle serialization failures explicitly and own
commit/rollback. A write receipt is not commit certification.

Capture requires separate CAPTURE permission in a clean read-only RR/SERIALIZABLE transaction.
The captured complete provider journal and canonical owner cuts are transient replay inputs;
publication storage holds only owner IDs/fingerprints/frontier pins. Resolution has zero IO,
returns exact source eligibility/diagnostics, and derives no member value. A snapshot/hash is
not proof of canonical origin or a live authorization token.

The closed25-cell policy and finite semantic mappings are explicitly reviewed. NEUTRAL→0/1
is authored AVAILABLE zero; a missing semantic row stays SOURCE_VALUE_NOT_MAPPED. Catalog/Recipes
classification cannot create a relation or publication permission. DIRECT_RECIPE always requires
explicit RecipeVersion context. No automatic latest/default path, repinning, fallback, recursive
propagation, parent aggregation or production content is introduced.

Real-PG hierarchy tests use the same disposable SCRAM/TLS harness discipline above. CI runs the
eight hierarchy authentication tests alongside the retained eight prior-source smoke tests, then
the complete suite. Empty downgrade→0014 is supported; any populated source registry/enrollment/
history refuses destructive downgrade. Structural cluster roles/credentials remain deployment-owned.
### MTR-040C pure one-hop consumer — implemented, not frozen

The [approved design](../../docs/product/MTR_040C_ONE_HOP_HIERARCHICAL_MEMBER_PREFERENCE_CONSUMER_DESIGN.md)
is implemented through `derive_one_hop_hierarchical_member_preference(subject)` in Preferences.
[Implementation evidence](../../docs/product/MTR_040C_ONE_HOP_HIERARCHICAL_MEMBER_PREFERENCE_CONSUMER_EVIDENCE.md)
maps HC01–HC81 to real frozen child/source replay. It adds nine exports (349 →358), no persistence,
IO, capture helper, migration or production defaults; schema remains0015 /85 domain tables.
Parent/destination must share the complete member ledger (only its observation clock may differ).
All repeated immutable typed owner facts across explicit/prior/hierarchy manifests must agree.
Only mapped explicit lineage can transfer; raw semantic state determines the finite map, then
exact authored attenuation applies in a separate inherited coordinate. Direct/retracted destination
suppresses inheritance; destination prior output stays separate. Multiple incoming relations remain
unavailable without aggregation. No EvidenceStrength is derived and no planner authority is granted.
**ARCHITECTURE APPROVED; IMPLEMENTATION REVIEW / FREEZE REQUIRED. Implementation PR stays unmerged.**
Issue #41 remains OPEN/full040 PARTIAL. No039,024/020B/021,Execution/PRECOMMIT implementation
is authorized. Source freeze supplies no production taste coverage.
