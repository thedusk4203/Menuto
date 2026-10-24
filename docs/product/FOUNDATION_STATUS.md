# Trạng thái foundation V1.3 và bằng chứng

## Đã có

- Canonical V1.3 spec, 30 invariants, 11 accepted ADR; bảng chuyển mã cũ/mới.
- 16 namespace theo §16.4; validation và learning hiện chỉ có namespace/ranh giới.
- Health API, web shell, OpenAPI và generated TypeScript client + runtime validation.
- 22 synthetic-v2 fixtures, CP-SAT micro-model, exhaustive reference, independent arithmetic/evidence verifier và fault-injection tests.
- Static dependency checks cho contract/public surfaces, validator independence; baseline consistency checks.
- Toolchain lock, CI và main protection. CI configuration không mặc định chứng minh mọi commit đều xanh.
- Backlog canonical MTR-001..050; mã MTR không đồng nghĩa số issue GitHub. Xem BACKLOG.md.

## Bằng chứng theo invariant

[INVARIANT_COVERAGE.md](INVARIANT_COVERAGE.md) ghi đủ INV-001..030, phân biệt micro-model evidence với production tests còn thiếu. Baseline checker chỉ xác minh cấu trúc/link/numbering, không chứng minh thực thi cả 30 quy tắc.

## Chưa hoàn thành

MTR-001 có glossary/mapping nhưng chưa đủ business tests. MTR-002 có harness/regressions nhưng chưa có production mutation corpus, V4 adapter/large-pool reference hoặc numeric launch gates. MTR-003..050 chưa được coi hoàn tất qua việc tạo tài liệu/namespace/issue.

Đợt Foundation đầu có units/basis/provenance, household/catalog/member source contracts và migration đến `0002` cho 8 bảng; xem [Implementation Blueprint M0/M1](IMPLEMENTATION_BLUEPRINT_M0_M1.md). PostgreSQL tests kiểm migration trên schema rỗng và dữ liệu legacy, rollback khi mâu thuẫn, ownership, finite numeric constraints, append-only catalog facts và stale profile writes. [Sáu sửa đổi foundation](FOUNDATION_CORRECTIONS.md) tách calculation/storage, chuẩn hóa account/member và provenance, mở draft assets raw/prepared. Planner/validation/mutation handoffs vẫn là draft, chưa đủ input để validate plan.

Chưa có auth production, NutritionPolicyEngine, PlanPolicyResolver, retail live, production Independent Validator, learning router hoặc consumer closed loop. Retail/inventory/plan foundation được cập nhật riêng bên dưới; operational plan activation vẫn fail-closed. Entry checklist chưa hoàn thành toàn bộ; không gọi phần nền tảng đầu tiên là đạt cả Milestone 0/1.

## M1.1 Retail / Procurement Foundation

Tại freeze M1.1, schema tới **0004**, tổng **23 bảng domain**. Mapping Product→Ingredient sở hữu edible yield; mỗi ProductVersion có một canonical ingredient và nhiều phiên bản mapping cho ingredient đó. Retailer giữ identity ổn định, status chuyển sang history append-only. Fixed/catch/loose vẫn tách riêng. Quote reference_price_pair chưa phải purchase cost; CALIBRATED_REFERENCE chỉ derive từ reference + calibration, availability UNKNOWN. Promotion và source coverage được derive từ evidence; toàn bộ planning handoffs vẫn DRAFT. M1.1 không có cooking yield, InventoryLot persistence hoặc workflow mới; cooking yield bổ sung riêng ở M1.2 bên dưới.

[Evidence corrections 0004](M1_1_RETAIL_CORRECTIONS_EVIDENCE.md) là nguồn nghiệm thu hiện hành. [Evidence 0003](M1_1_RETAIL_PROCUREMENT_EVIDENCE.md) giữ kết quả lịch sử 368 tests/CI của PR #55 đã merge; chính các tests đó từng encode calibration sai nên không đủ làm freeze gate. M1.1 corrected semantics đã được user review và **APPROVED TO FREEZE** trước M1.2.

Correction đã đạt **398 local tests (157 PostgreSQL thật)** và **GitHub CI PASS** riêng: [run #17](https://github.com/thedusk4203/Menuto/actions/runs/39763499529), Python/PostgreSQL 18.4 + web. [PR #56](https://github.com/thedusk4203/Menuto/pull/56) đã merge tại `f49e9b1`; [CI sau merge](https://github.com/thedusk4203/Menuto/actions/runs/39764143827) pass cả Python và web.

## M1.2 Recipe / Preparation Foundation

Schema mới `0005` bổ sung 10 bảng, tổng 33 bảng domain. Recipe identity tách immutable
RecipeVersion; aggregate có seal và ràng buộc giao dịch lắp ráp, chặn cả thêm child sau
commit. Recipe giữ culinary truth, chỉ tham chiếu Ingredient, không có Retail SKU/quote
hoặc household inventory. Cooking transformations có context/version/provenance và chỉ
EP_RAW_G→COOKED_G; M1.1 AP→EP giữ nguyên.

Năm scaling policies được kiểm trên các tier tác giả khai báo; adjustment envelope riêng
không đổi serving count. Contextual substitution và exact approved combinations chuẩn bị
giới hạn một structural substitution. `GroundedRecipeVariantDraft` là culinary input
**DRAFT/activation_ready=False**, chưa có nutrition/safety/retail/inventory resolution.
Không có generator, Planner V4, ledger, CookingBatch execution hoặc full Validator.

[Review A–H](M1_2_RECIPE_DOMAIN_REVIEW.md) và
[evidence kiểm thử/CI](M1_2_RECIPE_PREPARATION_EVIDENCE.md) ghi phạm vi và kết quả thực chạy.
Không suy từ slice này thành toàn bộ M0/M1 hoàn tất. Tại thời điểm M1.2, M1.3 chưa triển khai; trạng thái M1.3 cập nhật bên dưới.

Review PR #57 yêu cầu hai correction trước freeze: path-specific transformation selection
và cấm COUNT-targeted substitutions. `0006` bổ sung seal policy guard, không đổi 33 bảng,
seal/version functions hoặc `0005`. [Correction evidence](M1_2_CULINARY_BINDING_CORRECTIONS.md)
là nguồn nghiệm thu mới; 559 tests/CI của 0005 vẫn là evidence lịch sử, không tự chứng minh
hai counterexamples đã được sửa. User đã APPROVED TO FREEZE M1.2 tại commit `05382b6425a072433e38db99a1de101b577804a0` (0001–0006, 33 bảng).

## Quyết định còn mở

Theo §24.3: ReferenceFeasibleCost; numeric nutrition/launch defaults; retail terms; exploration/cooldown; assumption-debt thresholds; receipt-calibrated probability model; chi tiết database/contracts của blueprint. Ba subsystem Execution/Validation/Learning đã chốt kiến trúc, không còn liệt kê là architecture open decisions.


## M1.3 Inventory Physical Ledger Foundation

Migration 0007 thêm **5 bảng**, tổng **38 bảng domain**. M1.1/M1.2 giữ nguyên boundary;
0001–0006 không đổi. [Review A–J](M1_3_INVENTORY_DOMAIN_REVIEW.md) và
[evidence thực chạy](M1_3_INVENTORY_PHYSICAL_LEDGER_EVIDENCE.md) là phạm vi nghiệm thu.

Physical lots/movements có household ownership, explicit evidence/basis, append-only
corrections, DB-controlled balance và chronological ordering. Reservations/releases là
intent riêng, không movement. Prepared dish dùng contextual servings; prepared component
dùng COOKED_G. Retail mapping giữ FK exact immutable evidence; không sở hữu yield.

Service acquire/consume/discard/reconcile/reserve/release/snapshot và expiry foundation
đã có; không có HTTP business endpoints/UX, fulfillment/import, CookingBatch execution,
ActivePlan, projections, replan hoặc Independent Validator đầy đủ. Handoff snapshot và
batch flow vẫn DRAFT. M1.3 đã **APPROVED/FROZEN** ngày 2026-10-23 tại
`fef629965dd7401e27c98b5a0c523998a27017c4`, migrations0001–0007, 38 bảng;
688 Python / 313 PostgreSQL-real tests, benchmark22/22 và postmerge CI SUCCESS.
Không suy thành full M0/M1 hoặc execution readiness.


## F — Plan/revision foundation (MTR-016, FROZEN)

[Review A–J](PLAN_REVISION_FOUNDATION_DOMAIN_REVIEW.md) ghi ownership, immutable full
revision graph, mutable head view, reservation/fulfillment/batch seams và adversarial traces.
Repo chưa đặt số M1.4 cho slice này; giữ tên F và business identifier MTR-016.
Foundation implementation tại `0008` thêm 13 bảng, tổng 51 bảng; có sealed relational proposals,
immutable accepted revisions, atomic head/reservation orchestration và physical boundary links.
[Evidence F](PLAN_REVISION_FOUNDATION_EVIDENCE.md) ghi test/CI thực chạy và giới hạn.
Operational activation/revision bị chặn tới khi có real PRECOMMIT gate và full subject;
draft authoring không được gọi là ActivePlan operational hoặc PlanRevision0.
Trạng thái review: **READY FOR ARCHITECTURE/FREEZE REVIEW**, chưa FROZEN.


Correction MTR-016 `0009`: [scope/cut-line evidence](PLAN_REVISION_SEMANTIC_CORRECTIONS.md).
Thêm typed quantitative shopping contributions, enforce SINGLE_MEAL dependency closure
và freeze advice theo scheduled_at/planned_at/need_by. Schema hiện0009, **52 bảng**;
0001–0008 giữ nguyên. Legacy v1 giữ hash, graph v2 explicit; PRECOMMIT vẫn fail-closed.
Trạng thái **READY FOR ARCHITECTURE/FREEZE REVIEW**, chưa tự FROZEN hoặc đóng MTR-016.


## Current freeze and validation foundation

MTR-016 đã user APPROVED/FROZEN tại `751a40e847dd2e664a6fe3667c272bc740a44e49`,
head0009,52 bảng. Các submission/evidence READY trước đó là lịch sử; freeze foundation
không mở production PRECOMMIT hoặc cooking execution. Không sửa migrations0001–0009.

Slice tiếp theo: **MTR-025 ValidationSubject v1 foundation + supported subset MTR-026**.
[Review A–G](VALIDATION_SUBJECT_FOUNDATION_REVIEW.md), [evidence](VALIDATION_SUBJECT_FOUNDATION_EVIDENCE.md).
Implemented: immutable policy/source-aware snapshot, read-only coherent capture, independent
source-supported root/exclusion/nutrition/yield/physical replay checks. Structurally supported:
future source/validator handoff. Deferred: full clinical/root policy, grounding/scenario,
planned material/batch/revision/assumption/bridge validation and production authority.
Subject/report remain FOUNDATION_ONLY and non-authorizing; no migration/new tables. Domain
bundle10 is independent of DB head0009. Full MTR-025/026 production acceptance is PARTIAL.


## MTR-019A — Explicit culinary binding / independent grounding

[Review A–J](MTR_019A_CULINARY_BINDING_REVIEW.md), [evidence and matrix](MTR_019A_CULINARY_BINDING_EVIDENCE.md).
Migration0010 adds two proposal-owned relational binding tables (54 domain tables). Plan-intent.v3
includes exact selected culinary facts and batch signature; v1/v2/frozen MTR-025 hashes stay unchanged.
Independent RecipeGroundingValidator verifies primitive authored choices; companion input is
culinary-validation-input.v1. No production authority, full MTR-019/026 completion or Execution.
MTR-025 remains user FROZEN at219b556. MTR-019A is user **FROZEN / APPROVED** at
`4a6207ac52bc5ba0ce95de2df54c0c949f36066e`, migration0010 /54 domain tables.
RecipeGroundingValidator is an accepted completed sub-capability of MTR-026;
neither full MTR-019 nor full MTR-026 is complete.

## MTR-019B — Demand-driven culinary candidate generation

[Focused review](MTR_019B_VARIANT_GENERATOR_REVIEW.md),
[evidence](MTR_019B_VARIANT_GENERATOR_EVIDENCE.md).
Implemented: deterministic finite demand expansion from reviewed authored rules, exact tiers,
approved structural combinations and explicit zero adjustments; canonical source/candidate
identities, exclusion filters, fail-closed resource budgets and selected-binding handoff.
Candidates remain culinary DRAFT, not fully grounded solver-facing DishCandidates.
Frozen MTR-019A wire/hash/seal/validator semantics and migrations0001–0010 unchanged.
No new persistence: schema remains0010 /54 tables. MTR-019B is user **FROZEN / APPROVED** at
`23dd0b3bc3245ac9c7ef5493968f8ab120242f00`.
Deferred: downstream evidence-backed reasons, nutrition/retail/inventory grounding, shortlist,
solver, MTR-030 refinement, Execution and production PRECOMMIT/TOCTOU authorization.

## MTR-019C — Candidate Grounding

[Review A–J](MTR_019C_CANDIDATE_GROUNDING_REVIEW.md),
[evidence](MTR_019C_CANDIDATE_GROUNDING_EVIDENCE.md).
Planning assembles immutable nested domain resolutions from canonical read-only capture:
Recipe culinary/preparation, compatible Nutrition references, Retail supply coefficients/evidence,
Inventory confirmed possibilities and canonical member restrictions. No caller nutrient/price summaries.
Supported complete primitive inputs produce GroundedDishCandidate; missing facts return INCOMPLETE,
forbidden/forged choices REJECTED. Candidate activation remains False; no physical/reservation writes.
No migration/new tables;0010 /54 remains current. Frozen A/B/validator hashes/semantics unchanged.
COUNT nutrition and allergen/diet classification unavailable; policy/scenarios/basket cost, global
allocation/feasibility, MTR-020 and Execution deferred. MTR-019/026 remain PARTIAL.
MTR-019C is user **FROZEN / APPROVED** at `ffaa009031d8def0e32a654266a871cced44d35e`.

## MTR-020A — Conservative Pareto Shortlist Foundation

[Dependency/architecture review](MTR_020A_PARETO_SHORTLIST_REVIEW.md),
[verification evidence](MTR_020A_PARETO_SHORTLIST_EVIDENCE.md).
Implemented: canonical capture-only ingress; pure exact coverage frontier; exact duplicate
handling; dominance witnesses; explicit fail-closed resource limits. Different culinary,
nutrition, inventory, member/cutoff and non-contained supply provenance choices survive.
No synthetic cost/nutrition-fit/effort/preference scores. Serialized candidates/ready flags
cannot establish canonical ingress. No source re-grounding/DB IO in shortlist core.
No tables/migration;0010 /54 and frozen A/B/C semantics unchanged; domain bundle14 additive.
Full MTR-019/020/026 remain PARTIAL. Role/utility portfolio, evidence-backed reasons, COUNT
nutrition, classification, global feasibility, solver, Execution and PRECOMMIT remain deferred.
MTR-020A is user **FROZEN / APPROVED** at `87278ed1ea79771f80b09b161ff711ff066556a8`,
head0010 /54 tables. Full MTR-019/020/026 remain NOT COMPLETE; MTR-021/Execution NOT STARTED;
PRECOMMIT fail-closed. [Post-freeze dependency review](POST_MTR_020A_DEPENDENCY_REVIEW.md)
finds MTR-020B BLOCKED. User approved it with an ordering correction: **MTR-040A → MTR-041
→ MTR-024 → MTR-020B → MTR-021**. MTR-019D is optional support later/in parallel, not next.
[MTR-040A explicit preference design](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_REVIEW.md) was approved
with required correction: raw declarations have no EvidenceStrength; it belongs to later derived
MemberBehaviorProfile. The correction was applied before implementation.

## MTR-040A — Explicit Member Preference Foundation

[Actual implementation evidence](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_EVIDENCE.md).
Forward0011 adds four tables (58 total): reviewed affinity vocabulary, member source frontier,
stable typed preference streams and immutable declaration facts. Explicit source only; all five
targets, actor/subject ownership, replacement/retraction, CAS/idempotency and coherent snapshot.
No raw EvidenceStrength/assertion_confidence/TasteFit; no inferred feature assignment or shared
preference copying. MemberBehaviorProfile derivation/learning and full MTR-040 remain incomplete.
Frozen A/B/C/020A,0001–0010 unchanged; production gate fail-closed. MTR-041 not started;
MTR-020B/021 blocked. Submit040A **READY FOR ARCHITECTURE/FREEZE REVIEW**, not self-FROZEN.


MTR-040A remains **NOT FROZEN** after review of PR #71 (`f451d7f`).
[Authorship correction](MTR_040A_AUTHORSHIP_CORRECTION_EVIDENCE.md): forward `0012` replaces only
`menuto_preference_append()` and adds the inverse application guard. SELF iff canonical linked
member equals subject; representative iff different (including NULL); OWNER/EDITOR only.
Wrong modes reject, never normalize. No historical row/hash rewrite or new table; current schema
`0012` / **58 tables**, migrations0001–0011 unchanged. No MTR-041 work started.


## User freeze040A and MTR-041A preview-source subset

User **FROZEN / APPROVED MTR-040A** at `06dc1dcbf38d474b90f7bfb74f04651e884285e4`
(0012 /58 tables). Earlier NOT FROZEN entries above are historical review stages. Full040
remains incomplete; no declaration/schema semantics change in041A.

[MTR-041A review](MTR_041A_RECENT_EXPOSURE_DOMAIN_REVIEW.md) selects current sealed proposal
previews only. [Evidence](MTR_041A_RECENT_EXPOSURE_EVIDENCE.md) distinguishes capture/replay from
durable confirmed exposure: no such producer exists. Recipe-level per-member facts stay
PROVISIONAL/PROPOSAL_PREVIEW; consumption history UNAVAILABLE, empty is not never-exposed.
No migration/new tables:0012 /58. No cooldown/novelty/taste scores, learning router, assumption
graph, HorizonBridgeResolver, MTR-020B/021, Execution or PRECOMMIT authorization. Full041 remains
PARTIAL and cannot yet supply complete production portfolio novelty/exposure.
User has **FROZEN / APPROVED MTR-041A** at `774405ebe51f126fec10ce61c4dd41b9d229230a` (PR #73), scope
**proposal-preview subset only**. [Post-merge CI](https://github.com/thedusk4203/Menuto/actions/runs/40020836511)
is SUCCESS for Python/web against that commit. Evidence:1403 Python /630 PostgreSQL-real,
1350/1350 prior regressions retained,53 new tests, benchmark22/22, client10/10;172 old domain
schema definitions unchanged and9 additive. Schema0012 /58 tables, no migration.

Full040/041 and MTR-017 remain incomplete; MTR-038/039 are not implemented; MTR-046 lacks the
required feature mappings. MTR-024/020B/021 remain BLOCKED. **Do not start MTR-024**:041A supplies
proposed scheduled exposure only, not accepted commitment, cooking/consumption/taste evidence
or durable history. Execution not started; PRECOMMIT fail-closed. No following slice is authorized
by this freeze record.

## Post-MTR-041A dependency review — awaiting approval

[Review and capability/source/fingerprint matrices](POST_MTR_041A_DEPENDENCY_REVIEW.md)
propose **MTR-041B recipe-level, single-proposal cooldown-policy assessment** as the smallest
next slice. Existing provisional source truth can support a target-relative predicate with
self-exclusion and an explicit versioned policy, without fabricating consumption/novelty or
accepted-schedule evidence. This is a recommendation only; no041B implementation starts here.
Full041 is not completable now;024/020B/021 remain BLOCKED. No migration, frozen040A/041A
runtime change, Execution or PRECOMMIT authority. Approval is required before implementation.

## MTR-041B — proposal-local cooldown subset / FROZEN

User approved the dependency review and authorized only this subset from391a53e.
[Contract decisions](MTR_041B_RECIPE_COOLDOWN_REVIEW.md) /[evidence](MTR_041B_RECIPE_COOLDOWN_EVIDENCE.md).
Pure RECIPE_ID predicate on one current captured proposal, explicit versioned cooldown policy,
exact microsecond witnesses, target-relative interval and whole-target-meal exclusion.
No-match is scoped absence, not global safety/novelty/history. No DB IO, new persistence or
migration:0012 /58 tables. Frozen040A/041A semantics/hashes unchanged. Full040/041 remain
incomplete;024/020B/021 blocked, Execution unstarted, PRECOMMIT fail-closed.
User **FROZEN / APPROVED MTR-041B** at `43192c7303e42c7bac321728edecaa8421a58e9a` (PR #77).
Post-merge CI40073675503 SUCCESS;1453 Python /635 PostgreSQL-real,1403 prior regressions retained,
50 new tests, benchmark22/22, client10/10;181 prior schema definitions unchanged +5 additive.
Schema0012 /58 tables; migrations0001–0012 immutable. No correction PR is needed.

## Post-MTR-041B dependency review — recommendation only

[Remaining capability matrix and next-slice proposal](POST_MTR_041B_DEPENDENCY_REVIEW.md)
recommend **MTR-041C — proposal-local Recipe-ID decay-policy evidence** as a narrowly scoped
next step: apply an explicit versioned age policy to frozen041B's exact witnesses, without
inventing confirmed history, a global penalty or novelty. This is a proposed sub-slice, not
an implemented capability or permission to implement. No migration expected; full040/041,
MTR-024/020B/021 remain incomplete/blocked. Execution unstarted; PRECOMMIT fail-closed.

## MTR-041C — as-of-capture proposal-local decay trace / NOT FROZEN

User approved the next subset with reduced rational, non-negative lower-bound and explicit
policy-time/horizon clarifications. [Review](MTR_041C_DECAY_TRACE_REVIEW.md) /
[evidence](MTR_041C_DECAY_TRACE_EVIDENCE.md). Six additive contracts; pure per-witness trace over
fully revalidated frozen041B. Explicit ordered policy bands, exact reduced retention multiplier,
zero retention keeps source witness, no aggregates/RepeatPenalty/novelty/utility. AS_OF_CAPTURE
only; future retrospective mode and full-decay horizon are separate semantics. No persistence/
migration:0012 /58 tables. Frozen040A/041A/041B unchanged. Full041/024/020B/021 blocked, Execution
unstarted, PRECOMMIT fail-closed. Submit for review; no automatic next milestone or freeze.
