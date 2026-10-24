# Backlog canonical V1.3 — MTR-001 → MTR-050

Nguồn chuẩn: Development Spec V1.3 §21. Mã MTR là business identifier; số issue GitHub độc lập. Tất cả work items được giữ mở đến khi có implementation/kiểm chứng đủ; đây không phải bảng tuyên bố tiến độ hoàn thành.

14 issue cũ được giữ theo chủ đề, cập nhật mã và criteria V1.3; tạo 36 issue còn thiếu. [Migration](BASELINE_MIGRATION_V1_3.md) ghi bảng chuyển mã và cách đọc lịch sử. GitHub là nguồn trạng thái thực tế.

| ID | Priority | Nội dung | Acceptance criteria canonical | Trạng thái baseline |
| --- | --- | --- | --- | --- |
| [MTR-001](https://github.com/thedusk4203/Menuto/issues/1) | P0 | Domain glossary + invariants | V1.3 canonical distinctions + INV-001..030 mirrored in docs/tests; renumber migration note present. | PARTIAL — vẫn mở |
| [MTR-002](https://github.com/thedusk4203/Menuto/issues/2) | P0 | Benchmark + mutation harness | Scenario matrix, objective vector, runtime/status, reference config + deliberately corrupted validator fixtures. | PARTIAL — vẫn mở |
| [MTR-003](https://github.com/thedusk4203/Menuto/issues/16) | P0 | Units & measurement basis | AP/EP/raw/cooked/serving/money/discrete contracts; incompatible bases rejected. | OPEN — chưa chứng nhận |
| [MTR-004](https://github.com/thedusk4203/Menuto/issues/3) | P0 | Household-first schema | Default household/member; household-owned resources; actor fields. | OPEN — chưa chứng nhận |
| [MTR-005](https://github.com/thedusk4203/Menuto/issues/4) | P0 | MealParticipants model | Participant IDs + portion factors + canonical hard-constraint resolution + derived attendance scale. | OPEN — chưa chứng nhận |
| [MTR-006](https://github.com/thedusk4203/Menuto/issues/5) | P0 | NutritionPolicyEngine | Guideline/goal/comfort/weekly policy; root contracts versioned. | OPEN — chưa chứng nhận |
| [MTR-007](https://github.com/thedusk4203/Menuto/issues/6) | P0 | NutritionResolutionEstimator | Catalog/portion resolution reporting; no silent unbounded widening. | OPEN — chưa chứng nhận |
| [MTR-008](https://github.com/thedusk4203/Menuto/issues/7) | P0 | PlanPolicyResolver | NutritionPrecision, CostPreference, KitchenEffort, BudgetContract compiled independently. | OPEN — chưa chứng nhận |
| [MTR-009](https://github.com/thedusk4203/Menuto/issues/8) | P0 | Budget baseline/pressure | ReferenceFeasibleCost pressure distinct from preference/contract. | OPEN — chưa chứng nhận |
| [MTR-010](https://github.com/thedusk4203/Menuto/issues/9) | P0 | Retail evidence schema | RetailProduct/Offer/provenance/source-quality/availability evidence. | OPEN — chưa chứng nhận |
| [MTR-011](https://github.com/thedusk4203/Menuto/issues/10) | P0 | ProcurementClass builder | FIXED_PACK/CATCH_WEIGHT/LOOSE_SCALE + coverage/fragility metadata. | OPEN — chưa chứng nhận |
| [MTR-012](https://github.com/thedusk4203/Menuto/issues/11) | P0 | PlanningPriceQuote + calibration | Retailer×region×category calibration with confidence/shrinkage. | OPEN — chưa chứng nhận |
| [MTR-013](https://github.com/thedusk4203/Menuto/issues/12) | P0 | SPEND_LIMIT stress scenarios | BASE/ADVERSE_WEIGHT/BACKUP/CATEGORY_STRESS snapshot + revision sunk-spend semantics. | OPEN — chưa chứng nhận |
| [MTR-014](https://github.com/thedusk4203/Menuto/issues/13) | P0 | AP→EP + cooking-yield chain | Product AP→EP explicit; cooking yield/prepared output separate. | OPEN — chưa chứng nhận |
| [MTR-015](https://github.com/thedusk4203/Menuto/issues/14) | P0 | Inventory physical ledger | Household lots/movements/reservations/policy/reconcile; planned acquisition never physical stock. | OPEN — chưa chứng nhận |
| [MTR-016](https://github.com/thedusk4203/Menuto/issues/17) | P0 | ActivePlan + PlanRevision schema | Stable plan_id, immutable revision snapshots/diffs, locked materialized past, optimistic revision locking. | FROZEN foundation — user approved 2026-10-23 |
| [MTR-017](https://github.com/thedusk4203/Menuto/issues/18) | P0 | Execution state projections | Confirmed/Operational/Planning views + provisional assumption provenance. | OPEN — chưa chứng nhận |
| [MTR-018](https://github.com/thedusk4203/Menuto/issues/19) | P0 | Recipe version/variant schema | Contextual substitution + quantity/scaling/adjustment policies. | OPEN — chưa chứng nhận |
| [MTR-019](https://github.com/thedusk4203/Menuto/issues/20) | P0 | Grounded Variant Generator | Demand-driven immutable candidates; reason/fingerprint; explicit bases. | PARTIAL — A/B/C user FROZEN; C at ffaa009; broader coverage/reasons deferred |
| [MTR-020](https://github.com/thedusk4203/Menuto/issues/21) | P0 | Role-aware portfolio shortlist | Pareto + EXPLOIT/STRUCTURAL_CHAMPION/EXPLORE capacity; no cheapest starvation. | PARTIAL — MTR-020A user FROZEN at87278ed; MTR-020B BLOCKED pending source/policy prerequisites |
| [MTR-021](https://github.com/thedusk4203/Menuto/issues/22) | P0 | Feasibility V2 | Inventory/procurement/participant aware; data insufficiency != infeasible. | BLOCKED — MTR-020B/source-policy prerequisites; NOT STARTED |
| [MTR-022](https://github.com/thedusk4203/Menuto/issues/23) | P0 | Stage 1 global optimizer | Comfort violation + structural economics + fragility + package/inventory/batch. | OPEN — chưa chứng nhận |
| [MTR-023](https://github.com/thedusk4203/Menuto/issues/24) | P0 | CookingBatch/PreparedFood model | Planned production/allocation + execution transformation + leftovers; serving-count seam rule. | OPEN — chưa chứng nhận |
| [MTR-024](https://github.com/thedusk4203/Menuto/issues/25) | P0 | Stage 2 human utility | Separable behavioral vector compiled by versioned utility policy. | BLOCKED — remaining source/policy prerequisites;041A preview alone is insufficient; NOT STARTED |
| [MTR-025](https://github.com/thedusk4203/Menuto/issues/26) | P0 | ValidationSubjectSnapshot | Immutable facts/policy/scenario/revision hash; no mid-validation DB drift. | OPEN — chưa chứng nhận |
| [MTR-026](https://github.com/thedusk4203/Menuto/issues/27) | P0 | Independent validator suite | Root safety, primitive nutrition/cost/yield, conservation, chronological replay, batch/revision/assumption checks. | OPEN — chưa chứng nhận |
| [MTR-027](https://github.com/thedusk4203/Menuto/issues/28) | P0 | Planner API v1 | Versioned policy/source/scenario/validation snapshots + structured statuses/reasons. | OPEN — chưa chứng nhận |
| [MTR-028](https://github.com/thedusk4203/Menuto/issues/29) | P0 | Consumer onboarding | Life questions; budget wording; household defaults; cold-start feature priors. | OPEN — chưa chứng nhận |
| [MTR-029](https://github.com/thedusk4203/Menuto/issues/30) | P0 | Plan Quality Summary | Nutrition zone, spend status, provenance, inventory, waste, batch, fragility. | OPEN — chưa chứng nhận |
| [MTR-030](https://github.com/thedusk4203/Menuto/issues/31) | P1 | CulinaryAdjustmentPass | Freeze structure; bounded quantity refinement; preserve serving count unless explicit tier; revalidate/fallback. | OPEN — chưa chứng nhận |
| [MTR-031](https://github.com/thedusk4203/Menuto/issues/32) | P1 | Relaxation Advisor | Conflict → elastic estimate → verified proposals; forced-context quarantine. | OPEN — chưa chứng nhận |
| [MTR-032](https://github.com/thedusk4203/Menuto/issues/33) | P1 | Local Swap revision | Proposed graph built/validated before atomic commit; preserve physical facts. | OPEN — chưa chứng nhận |
| [MTR-033](https://github.com/thedusk4203/Menuto/issues/34) | P1 | Remaining-week replan | Freeze executed/materialized past; use current actual/operational/planning state correctly. | OPEN — chưa chứng nhận |
| [MTR-034](https://github.com/thedusk4203/Menuto/issues/35) | P1 | Shopping fulfillment resolver | Partial actual qty/price, sunk spend, primary/backups, household inventory materialization. | OPEN — chưa chứng nhận |
| [MTR-035](https://github.com/thedusk4203/Menuto/issues/36) | P1 | Today/execution mode | Batch/leftover guidance, skip/eat-out/swap, non-blocking assumption correction. | OPEN — chưa chứng nhận |
| [MTR-036](https://github.com/thedusk4203/Menuto/issues/37) | P1 | Assumption graph + compensation | Dependency chains, compensating reversals, execution conflicts, assumption-debt tracking. | OPEN — chưa chứng nhận |
| [MTR-037](https://github.com/thedusk4203/Menuto/issues/38) | P1 | ExecutionImpactAnalyzer | NONE/LOCAL_REPAIR/REPLAN_RECOMMENDED/REPLAN_REQUIRED with local-first escalation. | OPEN — chưa chứng nhận |
| [MTR-038](https://github.com/thedusk4203/Menuto/issues/39) | P1 | HorizonBridgeResolver | Chronological projection of future commitments + scheduled exposure to next horizon without double-count. | OPEN — chưa chứng nhận |
| [MTR-039](https://github.com/thedusk4203/Menuto/issues/40) | P1 | SignalAttributionRouter | DIRECT/CONTEXTUAL/INFERRED/PASSIVE → taste/context/exposure/retail/no-learn. | OPEN — chưa chứng nhận |
| [MTR-040](https://github.com/thedusk4203/Menuto/issues/41) | P1 | MemberBehaviorProfile | Hierarchical feature/direct affinity + evidence strength + explicit ownership. | PARTIAL — MTR-040A user FROZEN at06dc1dc; derived profile/learning NOT COMPLETE |
| [MTR-041](https://github.com/thedusk4203/Menuto/issues/42) | P1 | RecentExposureModel | Cross-week multi-fingerprint repeat penalty; provisional vs confirmed exposure semantics. | PARTIAL —041A/B/C FROZEN; proposed041D local RepeatPenalty policy awaits approval; full041/history NOT COMPLETE |
| [MTR-042](https://github.com/thedusk4203/Menuto/issues/43) | P1 | Learned observations UX | Show/reset/invalidate/promote learned rules; never silent policy mutation. | OPEN — chưa chứng nhận |
| [MTR-043](https://github.com/thedusk4203/Menuto/issues/44) | P1 | Price/provenance UX | Retail vs calibrated reference vs baseline clearly distinguished. | OPEN — chưa chứng nhận |
| [MTR-044](https://github.com/thedusk4203/Menuto/issues/45) | P1 | AI intent/explanation | Structured intent + verified metrics only. | OPEN — chưa chứng nhận |
| [MTR-045](https://github.com/thedusk4203/Menuto/issues/46) | P1 | Telemetry/feedback | Execution/learning/relaxation events with attribution reason/context and privacy review. | OPEN — chưa chứng nhận |
| [MTR-046](https://github.com/thedusk4203/Menuto/issues/47) | P1 | Catalog coverage matrix | Role/protein/style/quick/high-protein coverage + planner-ready completeness. | OPEN — chưa chứng nhận |
| [MTR-047](https://github.com/thedusk4203/Menuto/issues/48) | P1 | Receipt-vs-plan calibration dataset | Planned quotes/scenarios vs actual checkout, with retailer/category/context. | OPEN — chưa chứng nhận |
| [MTR-048](https://github.com/thedusk4203/Menuto/issues/49) | P2 | Barcode/receipt import | Reviewable mapping to fulfillment/inventory/actual-price. | OPEN — chưa chứng nhận |
| [MTR-049](https://github.com/thedusk4203/Menuto/issues/50) | P2 | Household-lite collaboration | Shared household UI/permissions, no individualized solver yet. | OPEN — chưa chứng nhận |
| [MTR-050](https://github.com/thedusk4203/Menuto/issues/51) | P2 | Recipe import | Reviewable RecipeVersion draft; no auto-trust facts. | OPEN — chưa chứng nhận |

Dependencies/contracts chi tiết cần freeze trong [Milestone 0/1 blueprint](IMPLEMENTATION_BLUEPRINT.md); thứ tự mã không phải DAG đã khóa. MTR-001/002 có foundation evidence, chưa đạt toàn bộ production criteria. Units, execution, independent validation và learning không được coi hoàn thành qua namespace.


## Review evidence sau baseline

M1.3 đã user APPROVED/FROZEN tại `fef629965dd7401e27c98b5a0c523998a27017c4`
(head0007, 38 bảng). [Evidence](M1_3_INVENTORY_PHYSICAL_LEDGER_EVIDENCE.md).
MTR-015 bao gồm policy/workflow rộng hơn ledger foundation; freeze slice không tự đóng
GitHub issue hoặc tuyên bố toàn bộ acceptance criteria đã xong.

Slice tiếp theo: **F — Plan/revision foundation / MTR-016**, theo blueprint.
[Review A–J](PLAN_REVISION_FOUNDATION_DOMAIN_REVIEW.md) và [evidence F](PLAN_REVISION_FOUNDATION_EVIDENCE.md)
ghi foundation implementation `0008`: sealed proposals, revision/head và atomic reservations.
Production activation fail-closed; full execution/validation chưa có. MTR-016/023/025 vẫn
OPEN, không auto-close hoặc tự FROZEN bởi việc merge foundation.


Correction MTR-016 `0009`: [scope/cut-line evidence](PLAN_REVISION_SEMANTIC_CORRECTIONS.md).
Thêm typed quantitative shopping contributions, enforce SINGLE_MEAL dependency closure
và freeze advice theo scheduled_at/planned_at/need_by. Schema hiện0009, **52 bảng**;
0001–0008 giữ nguyên. Legacy v1 giữ hash, graph v2 explicit; PRECOMMIT vẫn fail-closed.
Trạng thái **READY FOR ARCHITECTURE/FREEZE REVIEW**, chưa tự FROZEN hoặc đóng MTR-016.


User freeze decision: MTR-016 foundation is APPROVED/FROZEN at751a40e,0009/52 tables.
This records architecture acceptance; it does not silently close unrelated execution/gating work.
Next dependency-safe work is [MTR-025 subject foundation / partial MTR-026](VALIDATION_SUBJECT_FOUNDATION_REVIEW.md),
with [implementation evidence](VALIDATION_SUBJECT_FOUNDATION_EVIDENCE.md). Full production
MTR-025/026 remain PARTIAL and authorization stays fail-closed. No invented M1.4 numbering.


## MTR-019A approved implementation scope

[Explicit culinary ownership](MTR_019A_CULINARY_BINDING_REVIEW.md) is a narrow sub-slice under
MTR-019 plus independent RecipeGroundingValidator under MTR-026. [Evidence](MTR_019A_CULINARY_BINDING_EVIDENCE.md).
Durable sealed plan intent, forward0010, version3 graph/companion input; no demand-driven
generator or production authorization. Both parent work items remain incomplete. Freeze approval
of MTR-025 at219b556 concerns its foundation semantics; they remain untouched.

## MTR-019A freeze / MTR-019B implementation scope

MTR-019A user **FROZEN / APPROVED** at4a6207a,0010 /54 domain tables. Accepted
RecipeGroundingValidator completes only that MTR-026 sub-capability; both parent MTRs remain open.
[MTR-019B](MTR_019B_VARIANT_GENERATOR_REVIEW.md) adds deterministic demand-driven authored
culinary candidates and handoff to frozen binding, with [evidence](MTR_019B_VARIANT_GENERATOR_EVIDENCE.md).
No new migration, ranking, grounding downstream, Execution or PRECOMMIT authority.
MTR-019B awaits architecture/freeze review; no automatic next milestone.

## MTR-019B freeze / MTR-019C scope

MTR-019B is user FROZEN at23dd0b3. [MTR-019C](MTR_019C_CANDIDATE_GROUNDING_REVIEW.md)
adds supported canonical primitive grounding before any Pareto shortlist. [Evidence](MTR_019C_CANDIDATE_GROUNDING_EVIDENCE.md).
MTR-019/026 remain incomplete; no MTR-020 implementation or new milestone numbering. MTR-019C
awaits architecture/freeze review, not self-FROZEN. Prior submission notes above are historical.
