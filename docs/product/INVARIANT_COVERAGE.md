# Invariant coverage — V1.3

Mỗi ID dưới đây dùng nghĩa trong canonical V1.3. SCAFFOLD_ONLY là ranh giới/tài liệu; MICRO_MODEL_ONLY là bằng chứng cho mô hình tổng hợp; PARTIAL_FOUNDATION là đã có primitive/schema tests nhưng chưa đầy đủ workflow; NOT_IMPLEMENTED là chưa có implementation tương ứng. Không dòng nào tuyên bố toàn bộ invariant đã được thực thi trong production.

| Invariant | Mức bằng chứng | Công việc | Bằng chứng hiện tại / gap |
| --- | --- | --- | --- |
| INV-001 | SCAFFOLD_ONLY | MTR-006, MTR-008 | Chưa có policy/physiology business tests |
| INV-002 | NOT_IMPLEMENTED | MTR-008, MTR-009 | Chưa có BudgetPressure hoặc intent resolver |
| INV-003 | PARTIAL_FOUNDATION | MTR-004 | Household/member schema + composite FK/PostgreSQL tests; authorization và các shared assets còn thiếu |
| INV-004 | PARTIAL_FOUNDATION | MTR-005, MTR-026 | Participant identity/portion và canonical safety draft tests; shared-meal hard-safety enforcement chưa có |
| INV-005 | PARTIAL_FOUNDATION | MTR-018, MTR-019 | M1.2 immutable version/rule/combo/tier, mass-only substitution (0006 COUNT guard), path-specific culinary binding; chưa production VariantGenerator |
| INV-006 | PARTIAL_FOUNDATION | MTR-019, MTR-023, MTR-030 | M1.2 authored tiers/adjustment envelopes, structural limit và serving-count preservation tests; chưa production solver/adjustment pass/batch execution |
| INV-007 | PARTIAL_FOUNDATION | MTR-010, MTR-012 | M1.1 raw observation/derived quote tách bảng; provenance/origin/availability và SQL guards; chưa production eligibility/live integration |
| INV-008 | PARTIAL_FOUNDATION | MTR-011, MTR-022 | M1.1 class/member/primary/backup/package/substitution/source/promo primitives; chống backup giả; chưa fragility scoring/economic optimizer |
| INV-009 | PARTIAL_FOUNDATION | MTR-012, MTR-047 | M1.1 ordinal confidence, category calibration evidence và explicit reference origin; không probability/P90, chưa empirical calibration/backtest |
| INV-010 | MICRO_MODEL_ONLY | MTR-013, MTR-031 | Timeout/stress policy tests; chưa có acceptance/activation |
| INV-011 | PARTIAL_FOUNDATION | MTR-015, MTR-034 | M1.3 physical commands/SQL evidence guard cấm planned acquisition; chưa full quantitative fulfillment |
| INV-012 | PARTIAL_FOUNDATION | MTR-017, MTR-036 | M1.3 chỉ explicit consumption, elapsed time không ghi movement; chưa operational assumptions |
| INV-013 | PARTIAL_FOUNDATION | MTR-017, MTR-036 | M1.3 explicit USER/RECEIPT/BARCODE/EXECUTION + household actor guards; không SYSTEM inference; chưa projection |
| INV-014 | NOT_IMPLEMENTED | MTR-037 | Chưa có local-first repair escalation |
| INV-015 | PARTIAL_FOUNDATION | MTR-026 | Independent foundation checks correctness primitives only; no optimality/search; full validator suite deferred |
| INV-016 | PARTIAL_FOUNDATION | MTR-026 | Static independence plus zero DB/IO tests; independently implemented default-input arithmetic and physical replay; full suite deferred |
| INV-017 | PARTIAL_FOUNDATION | MTR-025, MTR-026 | M1.1 mapping/quote primitives; M1.2 recomputable culinary primitives + DB seal; M1.3 exact quantities, timestamps/sequence and movement history; chưa production Independent Validator/nutrition path |
| INV-018 | PARTIAL_FOUNDATION | MTR-003, MTR-014, MTR-025 | Exact units/provenance; M1.1 AP→EP mapping giữ nguyên; M1.2 contextual EP_RAW→COOKED factors/version/provenance; M1.3 explicit asset basis, immutable mapping FK + primitive ledger replay; full validation chain chưa có |
| INV-019 | PARTIAL_FOUNDATION | MTR-015, MTR-026 | M1.3 exact event order, nonnegative/reservation/expiry SQL + snapshot replay và competing writer tests; chưa batch flow validator |
| INV-020 | PARTIAL_FOUNDATION | MTR-006, MTR-026 | Canonical participant/exclusion guards bypass planner summaries; unsupported allergen/diet/root goal policy fail closed |
| INV-021 | PARTIAL_FOUNDATION | MTR-025, MTR-026 | F sealed graph hash + guarded receipt/frontier/CAS seam; production authority absent, publish fail-closed; chưa full PRECOMMIT/POSTFACT independent validation |
| INV-022 | NOT_IMPLEMENTED | MTR-039, MTR-041 | Chưa có passive evidence quarantine/provisional exposure |
| INV-023 | NOT_IMPLEMENTED | MTR-039 | Chưa có attribution retail/context ≠ taste |
| INV-024 | NOT_IMPLEMENTED | MTR-039, MTR-040 | Chưa có cooked→context/exposure routing |
| INV-025 | NOT_IMPLEMENTED | MTR-039, MTR-040 | Chưa có unattributed rejection evidence handling |
| INV-026 | NOT_IMPLEMENTED | MTR-005, MTR-040 | Chưa có member actor-scoped preference write |
| INV-027 | NOT_IMPLEMENTED | MTR-024, MTR-040 | Chưa có separable behavioral vector |
| INV-028 | NOT_IMPLEMENTED | MTR-008, MTR-042 | Chưa có learned observation promotion/reset UX |
| INV-029 | NOT_IMPLEMENTED | MTR-031, MTR-039 | Chưa có forced-trade-off quarantine |
| INV-030 | NOT_IMPLEMENTED | MTR-038, MTR-041 | Chưa có horizon bridge commitments/exposure |

Bằng chứng micro-model: benchmark/tests/test_harness.py và test_foundation_regressions.py. Bằng chứng static: apps/backend/tests/test_architecture.py. Baseline consistency test kiểm numbering/coverage/link, không thay business tests. Full correctness/mutation corpus phải theo ADR-010 và benchmark/V1_3_SCENARIO_MATRIX.md.

[Evidence M1.1 lịch sử](M1_1_RETAIL_PROCUREMENT_EVIDENCE.md) ghi 68 unit/contracts và 106 real-PostgreSQL tests ở 0003. INV-003/011/013 giữ ranh giới ownership/intents, chưa thay trạng thái physical lifecycle. Implementation `ed11639` đã pass [GitHub CI #14](https://github.com/thedusk4203/Menuto/actions/runs/39744442973); PR #55 đã merge. Bằng chứng này không bao phủ corrected semantics 0004.

**Corrections 0004:** [evidence hiện hành](M1_1_RETAIL_CORRECTIONS_EVIDENCE.md) thay thế semantic freeze của 0003 cho INV-007/008/009/018. Calibration chỉ reference; availability UNKNOWN; promotion/source coverage derive; ProductVersion có một canonical ingredient. Status history giữ retailer identity; quote pair không là purchase cost. Mức PARTIAL_FOUNDATION không đổi. PR #55 nêu trên đã merge; CI lịch sử không chứng nhận corrected implementation.


Review F — Plan/revision foundation: [mapping A–J và adversarial matrix](PLAN_REVISION_FOUNDATION_DOMAIN_REVIEW.md).
[Evidence F](PLAN_REVISION_FOUNDATION_EVIDENCE.md) bổ sung runtime foundation tests cho stable
plan identity, immutable graph/history, scope/cutline/materialization pins, CAS, idempotency,
atomic reservation replacement và no physical rewrite. INV-003/004/006/011/012/017/019 vẫn
PARTIAL; INV-021 chỉ partial guard seam. Tests thành công dùng synthetic authority fixture,
không chứng nhận production activation hoặc Independent Validator. INV-030 chưa implemented:
HorizonCommitmentsDraft chỉ handoff, chưa bridge resolution/exposure accounting.
M1.3 ledger đã user FROZEN tại fef629965dd7401e27c98b5a0c523998a27017c4; các mức PARTIAL
và gaps ngoài phạm vi physical foundation vẫn giữ nguyên.


Correction MTR-016 `0009`: [scope/cut-line evidence](PLAN_REVISION_SEMANTIC_CORRECTIONS.md).
Thêm typed quantitative shopping contributions, enforce SINGLE_MEAL dependency closure
và freeze advice theo scheduled_at/planned_at/need_by. Schema hiện0009, **52 bảng**;
0001–0008 giữ nguyên. Legacy v1 giữ hash, graph v2 explicit; PRECOMMIT vẫn fail-closed.
Trạng thái **READY FOR ARCHITECTURE/FREEZE REVIEW**, chưa tự FROZEN hoặc đóng MTR-016.


MTR-016 foundation is user FROZEN; [validation foundation evidence](VALIDATION_SUBJECT_FOUNDATION_EVIDENCE.md)
adds partial runtime coverage for INV-003/004/013/015–021: primitive member exclusion,
exact source-aware hashing/nutrition/yield estimates, conservation and causal physical replay,
zero-IO independent enforcement, non-authorizing PRECOMMIT and immutable POSTFACT diagnostics.
No invariant is certified fully production-enforced. Root nutrition/goal/safety classification,
scenario/planned material/batch/revision/assumption/bridge coverage and real authority remain
unimplemented; synthetic benchmark remains separate evidence, not this production suite.


MTR-019A [review](MTR_019A_CULINARY_BINDING_REVIEW.md) / [evidence](MTR_019A_CULINARY_BINDING_EVIDENCE.md):
INV-005/006 gain authoritative sealed authored choices and an independent grounding algorithm.
INV-017/018 gain exact binding provenance/bases plus SQL independently checking recipe primitives.
INV-015/016/021 gain pure companion checks, import/query traps and diagnostic/no-authority results.
INV-011/013 remain protected: no physical stock created. Own-anchor/closure/materialization
boundaries see binding-only changes. All remain PARTIAL_FOUNDATION; this does not certify
full MTR-019/026, nutrition safety, material feasibility or Execution. Canonical invariant wording unchanged.

MTR-019A is now user FROZEN at4a6207a. [MTR-019B review](MTR_019B_VARIANT_GENERATOR_REVIEW.md)
and [evidence](MTR_019B_VARIANT_GENERATOR_EVIDENCE.md) add INV-005/006 generation coverage:
no invented substitutions/methods/tiers, no Cartesian expansion, exact combination authorization,
zero refinement and unambiguous COUNT paths. INV-018 gains source/candidate fingerprints with
primitive provenance/bases. INV-015–017/021 stay independently checked by the unchanged
RecipeGroundingValidator; candidate hashes/triggers never grant validation authority.
INV-011/013 remain unchanged: generated possibilities and selected intent create no physical stock.
These additions do not certify downstream nutrition, procurement, material feasibility or full MTR-026.

MTR-019B is user FROZEN at23dd0b3. [MTR-019C](MTR_019C_CANDIDATE_GROUNDING_REVIEW.md)
adds source-supported grounding: INV-005/006 culinary claims recomputed without new possibilities;
INV-003/004 member identities/restrictions preserved (unknown classification blocks eligibility);
INV-007/009 conditional price/availability, no checkout/probability claim; INV-011/013 read-only
physical context, no procurement-as-stock; INV-018 compatible-basis nutrition references, exact
arithmetic/provenance and separate edible/cooking yield. INV-015–017/020/021 remain independent
validation requirements; producer grounding never grants validation authority. Full clinical policy,
scenarios/global material/chronology/assumptions and MTR-026 remain deferred, not certified.

MTR-019C is user FROZEN atffaa009. [MTR-020A review](MTR_020A_PARETO_SHORTLIST_REVIEW.md)
adds conservative coverage pruning without new culinary choices (INV-005/006), erasing member
restrictions (INV-003/004), inventing price/probability/quality metrics (INV-007–009), or physical
mutations (INV-011/013). Every retained alternative keeps full basis/provenance (INV-018).
Canonical capture-only ingress and narrow zero-IO core protect the data boundary, not validation
authority (INV-015–017/020/021). Global/causal feasibility (INV-019), full role/behavior portfolio,
root policy and production PRECOMMIT remain deferred. No canonical invariant wording changes.

MTR-040A [evidence](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_EVIDENCE.md) adds raw explicit member-owned
source coverage for INV-003/004/018/026: typed targets, actor/proxy scope and immutable provenance.
INV-022–025/027–029 are protected by excluding inferred/execution/utility events, scalar TasteFit
and caller EvidenceStrength; hard safety is unchanged. DB CAS/frontier/idempotency, direct SQL and
concurrency checks protect source history; no learned profile or full invariant certification.
PRECOMMIT remains fail-closed (INV-021); exposure/horizon/solver/Execution remain deferred.


MTR-040A authorship correction (`0012`,58 tables) closes the inverse actor/subject check
for INV-003/004/018/026 source provenance: SELF iff linked subject, representative iff distinct
(NULL supported); OWNER/EDITOR only. Service and direct SQL matrix plus historical/data-bearing
roundtrip tests are recorded in [correction evidence](MTR_040A_AUTHORSHIP_CORRECTION_EVIDENCE.md).
No invariant wording, frozen culinary/shortlist contract, raw EvidenceStrength or validation
authority changes. MTR-040A is NOT FROZEN; MTR-041 remains not started.


MTR-041A [review/evidence](MTR_041A_RECENT_EXPOSURE_EVIDENCE.md): selected-proposal preview only.
INV-022 excludes passive assumptions and durable inferred history;023–025/028/029 prevent
friction/cooking/rejection/forced-choice→taste mutation. INV-026 filters explicit participants
without member fan-out;027 retains separate evidence, no scalar score. INV-030 supports stable
meal/member/recipe dedup across explicit windows, not complete horizon/asset replay.013/018/021
retain provisional provenance, no physical/confirmed truth or authority from previews. Source
capture RO/RR/concurrency and pure-core boundaries have focused tests; no claim of full invariant
certification.040A is user FROZEN; full041 remains PARTIAL; no migration/schema change.


User froze **MTR-041A** at `774405ebe51f126fec10ce61c4dd41b9d229230a` (0012 /58 tables, PR #73).
Acceptance covers proposal-preview source/replay evidence only; the tests above do not certify
accepted commitments, confirmed cooking/consumption, durable behavior, complete INV-030 horizon
replay or full MTR-041. INV-022..030 wording and frozen implementation remain unchanged.
MTR-024/020B/021 remain blocked; Execution not started; PRECOMMIT fail-closed.

MTR-041B [evidence](MTR_041B_RECIPE_COOLDOWN_EVIDENCE.md): target-relative, proposal-local
RECIPE_ID cooldown witnesses under explicit policy. INV-012/013 retain provisional truth;
022/024/027 forbid confirmed/taste/utility claims;026 enforces explicit member participation;
018 preserves exact temporal distance/provenance;030 supports same-proposal scheduled repetition,
not canonical cross-horizon reconciliation. Negative tests cover missing/invalid policy,
insufficient lookback, unsupported identity, retired/nonparticipating targets and cached-output
tampering. Real-PG capture/concurrent replacement/read-only/immutable-source checks preserve the
frozen source boundary. No broadened invariant certification, migration or new authority.
