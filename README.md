# Menuto

Menuto giúp cá nhân/hộ gia đình tối ưu kế hoạch ăn và mua sắm theo ngân sách, dinh dưỡng, tồn kho và khả năng thực hiện.

**Trạng thái:** foundation đã căn chỉnh theo kiến trúc V1.3. Health API, web shell và benchmark synthetic chạy được; chưa có Planner V4 hoặc closed-loop workflow nghiệp vụ. Milestone 0/1 chưa hoàn thành.

## Nguồn chuẩn

- [Development Spec V1.3](docs/MENUTO_DEVELOPMENT_SPEC_V1_3.md).
- [30 Architecture Invariants](docs/ARCHITECTURE_INVARIANTS.md).
- [ADR-001..011](docs/adr/).
- [Glossary](docs/product/GLOSSARY.md), [kiến trúc](docs/product/ARCHITECTURE.md), [trạng thái/bằng chứng](docs/product/FOUNDATION_STATUS.md).
- [Backlog V1.3 MTR-001 → MTR-050](docs/product/BACKLOG.md).
- [Chuyển mã V1.2 → V1.3](docs/product/BASELINE_MIGRATION_V1_3.md), [entry checklist Milestone 0/1](docs/product/IMPLEMENTATION_BLUEPRINT.md).
- [Implementation Blueprint M0/M1](docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md): migration đến `0015`, tổng85 bảng; hierarchy SOURCE đã FROZEN; M1.1 Retail đã freeze, M1.2 bổ sung immutable RecipeVersion, authored rules/tiers/envelopes và net cooking yield theo ingredient path. Handoff planning/validation/grounded culinary input vẫn draft. [Correction evidence M1.2](docs/product/M1_2_CULINARY_BINDING_CORRECTIONS.md), [hướng dẫn database/tests](apps/backend/README.md).

V1.3 là baseline duy nhất đang hiệu lực. V1.2 chỉ còn trong lịch sử Git; mã invariant/backlog cũ không được diễn giải theo nghĩa V1.3. Các bản gốc người dùng đặt tại root được giữ ở máy và bỏ qua trong Git; `docs/` là bản chuẩn được quản lý.

Thay đổi mâu thuẫn ADR/invariant đã chấp nhận cần superseding ADR. Những chi tiết chưa khóa phải được phân biệt với quyết định đã có.

## Chạy tại máy

Yêu cầu Python 3.13.14 (uv có thể cài), uv 0.11.28, Node 24.x và npm. Dependencies khóa trong uv.lock và một package-lock.json tại root.

```powershell
uv sync --locked
uv run python tools/check_architecture_baseline.py
uv run python tools/check_import_boundaries.py
uv run pytest
uv run ruff check .
uv run menuto-benchmark --output benchmark/results/latest.json
uv run uvicorn app.main:app --reload
```

Ở terminal khác, từ root:

```powershell
npm ci
npm run contracts:check
npm run test:client
npm run dev --workspace @menuto/web
```

Web: http://127.0.0.1:5173. API docs: http://127.0.0.1:8000/docs. Health chỉ kiểm tra process liveness, không chứng minh database/planner readiness.

## Cấu trúc

```text
apps/backend/app/modules/   16 namespace theo V1.3 §16.4, gồm validation và learning
apps/backend/app/domain/    Neutral units/provenance và draft handoff contracts
apps/backend/app/persistence/ SQLAlchemy metadata/engine, chưa provision DB ứng dụng
apps/backend/migrations/    Alembic 0001 → 0015, 85 bảng domain; hierarchy SOURCE FROZEN
apps/backend/app/shared/    Technical primitives và health contract
apps/backend/tests/        Health, architecture/import và baseline consistency tests
apps/backend/workers/      Chưa có worker
apps/web/                  React/TypeScript/Vite foundation
packages/contracts/        OpenAPI snapshot từ FastAPI
packages/api-client/       Generated TypeScript client và runtime validator
benchmark/                 CP-SAT micro-model, reference, verifier, fixtures và runner
data/                      Seeds/imports, chưa có dữ liệu thật
docs/                      Spec, 30 invariants, 11 ADR, glossary, backlog và blueprint
infra/                     Chưa provision database/cloud
tools/                     Baseline/import checks, export và fixture generator
graphify-out/              Bản đồ tài liệu/code, không chứng minh feature hoàn tất
```

## Thứ tự phát triển

Theo V1.3 §20: Milestone 0 contracts/units/benchmark → Milestone 1 household/data/execution foundation → Milestone 2 policies/snapshots → Milestone 3 Planner V4/validator → Milestone 4 refinement/repair/horizon bridge → Milestone 5 consumer closed loop → Milestone 6 public readiness.

Execution State Machine, Independent Validator và Behavioral Learning đã có quyết định kiến trúc trong ADR-009..011; implementation vẫn chưa có. Các quyết định còn mở gồm ReferenceFeasibleCost, numeric nutrition/launch gates, retail acquisition/terms, exploration/cooldown, assumption-debt thresholds, receipt-calibrated probability model và chi tiết DB/contracts cho blueprint (§24.3).

## Kiểm tra và giới hạn

Theo [CONTRIBUTING](CONTRIBUTING.md). CI kiểm baseline docs, import boundaries, Python, OpenAPI/fixtures, benchmark, generated client và web build. Main yêu cầu PR + checks python/web, strict up-to-date; cấm force-push/xóa kể cả admin.

22 fixtures hiện tại có provenance synthetic-from-spec-v1.2 và được giữ nguyên để bảo toàn regression evidence; không đổi nhãn thành coverage V1.3. [Ma trận benchmark V1.3](benchmark/V1_3_SCENARIO_MATRIX.md) ghi rõ phần còn thiếu. Không dùng synthetic adapter như Planner V4 production.

Graphify là công cụ phát triển tùy chọn. Chỉ ba output công khai được track; cache/interpreter/manifest giữ local. Smart Menu là reference tại máy, không đưa code/lịch sử cũ vào Menuto.


M1.1/M1.2 đã freeze tại 05382b6. M1.3 thêm physical inventory foundation ở migration
0007, tổng 38 bảng. [Review](docs/product/M1_3_INVENTORY_DOMAIN_REVIEW.md) và
[evidence](docs/product/M1_3_INVENTORY_PHYSICAL_LEDGER_EVIDENCE.md) ghi chính xác scope;
không có full execution/Planner/Inventory UX. M1.3 đã **FROZEN** tại `fef6299` (0001–0007, 38 bảng).
Slice tiếp theo giữ tên canonical **F — Plan/revision foundation (MTR-016)**;
[architecture review](docs/product/PLAN_REVISION_FOUNDATION_DOMAIN_REVIEW.md) và
[evidence foundation 0008](docs/product/PLAN_REVISION_FOUNDATION_EVIDENCE.md): 13 bảng mới,
tổng 51 bảng; operational activation vẫn fail-closed, chưa FROZEN.


[Plan/revision correction0009](docs/product/PLAN_REVISION_SEMANTIC_CORRECTIONS.md) bổ sung
shopping contribution ownership và historical advice guards; tổng52 bảng. Chưa FROZEN.


MTR-016 đã user FROZEN tại751a40e. [Validation subject foundation](docs/product/VALIDATION_SUBJECT_FOUNDATION_EVIDENCE.md)
bổ sung immutable input và independent supported checks; chưa full Independent Validator,
production authority hoặc execution. Schema vẫn0009/52 bảng; không có migration mới.


MTR-019A thêm authoritative sealed culinary binding trong plan-intent.v3 và independent
RecipeGroundingValidator; [review A–J](docs/product/MTR_019A_CULINARY_BINDING_REVIEW.md),
[evidence](docs/product/MTR_019A_CULINARY_BINDING_EVIDENCE.md). V1/v2 plan hashes và frozen
MTR-025 giữ nguyên. Chưa có full VariantGenerator, Execution hoặc production authority.

MTR-040B đã **FROZEN** theo phê duyệt architecture/freeze của người dùng ngày2026-10-26;
profile vẫn là draft cho các target được yêu cầu và xác minh từ nguồn chuẩn:
[evidence](docs/product/MTR_040B_EXPLICIT_TARGET_AFFINITY_EVIDENCE.md). Affinity dùng phân số chính xác,
EvidenceStrength theo policy riêng; prior/shrinkage chưa có nguồn nên vẫn UNAVAILABLE.
Canonical PR #90: head `6ef6b8f9d64a6b1c45fce570857d3cd0568385c6`, merge
`08ddeb87604b8913175ae3852a32ce6f4b8d1273`;
[CI sau merge40215578850](https://github.com/thedusk4203/Menuto/actions/runs/40215578850) SUCCESS,
2015 tests. Schema0013 /71 bảng, không migration hay lưu profile. Learned/contextual/passive evidence
vẫn UNAVAILABLE; cross-target inference/candidate aggregation NOT_PERFORMED; planner_ready=False,
activation_ready=False. Chưa hoàn tất MemberBehaviorProfile, TasteFit, Planner hoặc quyền kích hoạt.
Không bắt đầu MTR-040C hay cho phép triển khai milestone tiếp theo.

MTR-041F đã triển khai theo [thiết kế được duyệt](docs/product/MTR_041F_FEATURE_REPEAT_POLICY_DESIGN.md),
trạng thái **FROZEN / APPROVED** tại `63e6b9f7dff3f061657fa96680a69cfc6fd1ae06`;
xem [bằng chứng](docs/product/MTR_041F_FEATURE_REPEAT_POLICY_EVIDENCE.md).
Ba API thuần diễn giải cooldown -> decay -> proposal-local feature RepeatPenalty, giữ riêng
METHOD/MAIN_PROTEIN/FLAVOR và từng exact term. Không migration, schema0013 /71 bảng.
MTR-040C chưa sẵn sàng/chưa được phép thiết kế. Không mở novelty, TasteFit,024 composition,
accepted/confirmed/history, Execution hay PRECOMMIT authority.
[Đánh giá phụ thuộc sau041F](docs/product/POST_MTR_041F_DEPENDENCY_REVIEW.md) đề xuất nguồn prior
chuẩn cho exact target làm hướng tiếp theo; cần duyệt thiết kế nguồn trước khi triển khai.

Người dùng đã duyệt [thiết kế nguồn prior](docs/product/PREFERENCE_PRIOR_SOURCE_FOUNDATION_DESIGN.md)
và cho phép triển khai từ main `577f32a302cca56c7b6ac9dfb65ce2d663ae8a30` (PR #96).
[Nguồn đã triển khai](docs/product/PREFERENCE_PRIOR_SOURCE_FOUNDATION_EVIDENCE.md), **IMPLEMENTED / NOT FROZEN**:
quyền SCRAM riêng theo provider, lịch sử bất biến, capture đầy đủ và replay thuần.
Migration `0014` thêm 7 bảng, tổng 78; 276 định nghĩa cũ giữ nguyên, thêm 23, tổng 299.
Không seed provider, principal, capability grants hay prior values. Chưa gán số milestone;
production content, mapping, shrinkage và MTR-040C vẫn chưa được phép. Chờ architecture/freeze review.

Cập nhật hiện tại: nguồn prior đã [FROZEN](docs/product/PREFERENCE_PRIOR_SOURCE_FREEZE_RECEIPT.md).
Sau khi PR #99 được duyệt/merge, người dùng cấp quyền riêng cho **Exact-target Prior Compatibility
& Shrinkage Foundation** từ `12048deeffd8c0b30368df0684de1d971a2c4b9c`.
[Slice đã FROZEN / APPROVED](docs/product/EXACT_TARGET_PRIOR_SHRINKAGE_FREEZE_RECEIPT.md)
tại `5728411ac12555f583f8df72ac71861998978aa4` (PR #100),
[push CI40351934792](https://github.com/thedusk4203/Menuto/actions/runs/40351934792) SUCCESS, python/web xanh,
2.597 test đạt. [Evidence triển khai](docs/product/EXACT_TARGET_PRIOR_COMPATIBILITY_SHRINKAGE_EVIDENCE.md) giữ trạng thái lịch sử:
API thuần, không IO/lưu trữ, descriptor gắn với target kind và full mapping-policy fingerprint;
299 định nghĩa giữ nguyên +19 mới =318. Schema vẫn0014 /78, không0015 hay production policy values.
MTR-040C chưa được gán/cho phép; full040/041/046 chưa hoàn tất;024/020B/021 vẫn BLOCKED,
Execution NOT STARTED, PRECOMMIT FAIL-CLOSED. Scoped numeric equality không cấp quyền truyền/gộp/xếp hạng
sở thích giữa hai exact targets, kể cả cùng kind và cùng policy.
[Dependency review sau PR #100](docs/product/POST_EXACT_TARGET_PRIOR_SHRINKAGE_DEPENDENCY_REVIEW.md)
đã được APPROVED tại canonical `73b3b0b3bbe6571ca5e70c09442d394701c5adf8` (PR #101).
Hierarchy SOURCE đã **FROZEN / APPROVED** tại
`ee8a4de1b1c71ccbd56ea565e111718660711fa8` (PR #104; implementation head4263bf5;
[push CI40432057006](https://github.com/thedusk4203/Menuto/actions/runs/40432057006) SUCCESS,
python/web xanh;2.807 tests). [Freeze receipt](docs/product/HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_FREEZE_RECEIPT.md)
ghi schema0015 /85 bảng,349 definitions và7 bảng nguồn rỗng sau migration test; không seed production.
[Evidence triển khai](docs/product/HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_IMPLEMENTATION_EVIDENCE.md)
giữ receipt lịch sử; runtime/contracts/frozen semantics không đổi.

**MTR-040 — COMPLETE; issue #41 — CLOSED / COMPLETED.**
[Completion review và closure receipt](docs/product/POST_MTR_040C_PARENT_MTR_040_COMPLETION_REVIEW.md#12-approved-closure-receipt)
đã được duyệt; PR #108 merge đúng head `d30f9f610af937f2e59fb4eea5962478037ff414` tại
`959e7fa3488e0c379ab37044c25da74292c2d76b`, tree khớp head đã review.
[Push CI 40486320021](https://github.com/thedusk4203/Menuto/actions/runs/40486320021) SUCCESS trên đúng SHA,
python/web xanh; 2.978 tests; 358 definitions; schema **0015 / 85 bảng**.
Issue #41 đã đóng với lý do completed. Frozen 040A/B/C và các nguồn/policy giữ nguyên;
040C vẫn frozen tại `69241affc2d85ee534ca682a0ff9a4d23a7c7862` (PR #107).
Không thêm runtime, aggregate, persistence, migration 0016 hay production rows/defaults.
Full 041/046 PARTIAL; 039 OPEN; 024/020B/021 BLOCKED; Execution NOT STARTED;
PRECOMMIT FAIL-CLOSED; planner_ready=False, activation_ready=False. Không bắt đầu downstream milestone.
