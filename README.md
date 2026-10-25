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
- [Implementation Blueprint M0/M1](docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md): migration đến `0010`, tổng 54 bảng; M1.1 Retail đã freeze, M1.2 bổ sung immutable RecipeVersion, authored rules/tiers/envelopes và net cooking yield theo ingredient path. Handoff planning/validation/grounded culinary input vẫn draft. [Correction evidence M1.2](docs/product/M1_2_CULINARY_BINDING_CORRECTIONS.md), [hướng dẫn database/tests](apps/backend/README.md).

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
apps/backend/migrations/    Alembic 0001 → 0010, hiện có 54 bảng domain
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

MTR-041F hiện chỉ ở bước [architecture/design](docs/product/MTR_041F_FEATURE_REPEAT_POLICY_DESIGN.md):
policy cooldown -> decay -> proposal-local feature RepeatPenalty cho METHOD/MAIN_PROTEIN/FLAVOR,
giữ riêng từng dimension/term và xử lý coverage chưa xác định. Chưa triển khai, chưa freeze;
PR tài liệu sẽ dừng để review. MTR-040C chưa sẵn sàng và chưa được phép thiết kế; không mở novelty,
TasteFit,024 composition, accepted/confirmed/history, Execution hay PRECOMMIT authority.
