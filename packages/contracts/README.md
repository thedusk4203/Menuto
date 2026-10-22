# Contracts

Nguồn hợp đồng HTTP: OpenAPI sinh từ FastAPI. Chỉ có health endpoint, chưa có PlanRequest hoặc Planner API.

`uv run python tools/export_openapi.py` cập nhật openapi.json; `npm run contracts:generate` sinh type TypeScript, JSON Schema và standalone response validator trong packages/api-client. Không chỉnh tay các file generated.

CI kiểm tra hai chiều: schema snapshot phải khớp backend, generated client phải khớp snapshot. Client tests kiểm tra runtime payload/HTTP/cancellation; typecheck kiểm tra đường dẫn/phương thức theo hợp đồng. HealthResponse serialization schema yêu cầu đủ các field backend luôn gửi; wire response không đổi.

Không đưa PlanningMode vào hợp đồng mới. Business contracts được chốt theo đặc tả trước khi thêm endpoint nghiệp vụ.

## Domain foundation contracts

`domain.schema.json` là bundle `$defs` riêng từ Pydantic, không quảng bá HTTP endpoint. Chọn definition cụ thể để validate; không dùng cả bundle như root schema của một request. Sinh/kiểm bằng `uv run python tools/export_domain_contracts.py [--check]`.

Units/basis, money, provenance và household/catalog/member source contracts đã có implementation. Planner request/output, validation subject/report và mutation fixtures dùng các version `m0-draft.2`; chưa đủ để solve/validate/activate plan. Python validators kiểm thêm quan hệ giữa fields; JSON Schema không biểu diễn hết các guard này. Chưa sinh TypeScript client cho domain drafts.

Bundle hiện có ID `urn:menuto:domain:foundation:9`. Retail facts dùng **retail-v2** (breaking wire change): quote chỉ có `reference_price_pair`, CALIBRATED_REFERENCE = reference + calibration; không nhận calibration cho observation. Option không nhận promotion/single-source booleans; snapshot derive coverage. ProductVersion yêu cầu canonical_ingredient_id; Retailer status là fact riêng. `RetailSourcedAPAssetDraft` chuyển sang `inventory-retail-origin.m1-draft.2`, vẫn không phải physical ledger hoặc validator-ready asset. Callers phải nâng version tường minh, không alias payload v1. [Domain review M1.1](../../docs/product/M1_1_RETAIL_DOMAIN_REVIEW.md).

Recipe facts dùng **recipe-v1**: immutable authored snapshot, contextual rules, serving tiers,
scaling/adjustment policies và preparation transformations EP_RAW_G→COOKED_G.
`GroundedRecipeVariantDraft` chỉ là culinary input, bắt buộc DRAFT/activation_ready=False;
chưa có nutrition/safety/retail/inventory resolution. Không dùng như solver-ready candidate.
[Domain review A–H](../../docs/product/M1_2_RECIPE_DOMAIN_REVIEW.md).

Correction 0006 giữ nguyên wire shape recipe-v1 nhưng siết semantic validation: cấm mọi
substitution nhắm COUNT; COUNT chưa thay thế vẫn giữ item_ref. Transformation được chọn
đúng resolved ingredient path, là net yield trong Recipe context. VariantReason vẫn chỉ
là draft explanation của caller, chưa phải evidence downstream đã xác minh.


M1.3 bundle ID `urn:menuto:domain:foundation:7` thêm inventory-v1 confirmed physical facts
và command contracts; không đổi recipe-v1/retail-v2 wire shapes. PhysicalInventorySnapshot
và BatchFlowLinkDraft vẫn DRAFT/activation_ready=False hoặc execution_ready=False. Legacy
RetailSourcedAPAssetDraft giữ nguyên là draft, không được dùng như physical acquisition.
Actual acquisition dùng AcquireInventoryCommand có explicit evidence; retail origin map FK
không tự là purchase fact. Snapshot giữ full immutable mapping primitives khi có nguồn AP.


F / plan-intent.v1 thêm frozen workspace/proposal/revision snapshots, meal participants,
shopping/batch/allocation/reservation intents và command contracts. ActivePlanSnapshot chỉ
đọc được sau accepted revision; proposals không activation-ready. Production PRECOMMIT
authority chưa installed nên publish fail-closed. HorizonCommitmentsDraft chưa phải
HorizonBridgeResolver hoặc ValidationSubjectSnapshot. Không thêm HTTP business API.


Correction0009 adds plan-intent.v2 with typed ShoppingDemandContributionIntent. Root
commands/snapshots still use their v1 envelopes; the embedded graph version is explicit.
Legacy plan-intent.v1 reads preserve graph and command fingerprints: new empty fields are
excluded from v1 canonical payload. V1 cannot carry contributions. Unattributed legacy
demand is not guessed into ownership and cannot be edited under SINGLE_MEAL.
