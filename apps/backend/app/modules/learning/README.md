# Behavioral learning — namespace V1.3

ADR-011, INV-022..030. Chưa có router, profile store hoặc learning engine.

Evidence classification DIRECT/CONTEXTUAL/INFERRED/PASSIVE route sang taste, kitchen context, exposure, retail calibration hoặc NoLearn. AUTOPILOT_ASSUMED không tạo durable learning; USER_CONFIRMED_COOKED không đồng nghĩa thích món. FORCED_CONFLICT_RESOLUTION bị quarantine; explicit preference vẫn thuộc member được actor chỉ định.

Learning đọc immutable event/domain contracts, không gọi planner/execution mutation facades. Preferences giữ declared/member-owned preference; learning giữ attribution và learned observations. Numeric exploration/cooldown/shrinkage defaults vẫn cần evidence/versioned policy.


MTR-041A implements only pure recipe-level **PROPOSAL_PREVIEW** contracts/replay/deduplication.
Read-only canonical capture is Planning orchestration; Learning core has no DB/Execution/solver
IO. Latest proposal advice remains PROVISIONAL, not accepted schedule or confirmed consumption.
No durable exposure history, learned profile, attribution router, repeat score or novelty.
Exposure source coverage is explicitly selected plans, never complete member consumption history.

Frozen041B adds proposal-local Recipe-ID cooldown assessment.041C adds pure AS_OF_CAPTURE
decay trace over fully revalidated041B witnesses, with explicit policy bands and exact reduced
rational retention. Multiplier is policy interpretation, never behavioral evidence/confidence.
Zero retention preserves the source witness; no aggregate utility, RepeatPenalty, novelty,
history/authority or new source workflow. Future full decay horizon/retrospective policy mode
are separate semantics, not silently added here.


MTR-041D adds interpret_recipe_repeat_penalty: fully revalidated041C→exact per-witness
contributions and proposal_local_repeat_penalty, explicit versioned SUM_RETAINED_OCCURRENCES
policy only. None for empty; exact0 for zero retention with witnesses retained. No numeric defaults,
DB IO, global history, member aggregation, ranking or cross-dimension utility.041D is user FROZEN.


MTR-041F implements additive assess_feature_cooldown -> trace_feature_decay ->
interpret_feature_repeat_penalty for one exact reviewed term/member/target in one proposal.
Full frozen041E preview/source is reconstructed every stage; frozen046A resolves finite coverage.
Explicit versioned per-term policies only; no Recipe-ID weight reuse or default numeric values.
Unknown meals withhold totals, scoped empty is unavailable, complete nonempty zero retention is
AVAILABLE0/1. No IO/persistence, profile mutation, global history, novelty, TasteFit or planner authority.
041F is user FROZEN / APPROVED at `63e6b9f7dff3f061657fa96680a69cfc6fd1ae06`.
Frozen041B/C/D remain separate. The
[post-041F dependency review](../../../../../docs/product/POST_MTR_041F_DEPENDENCY_REVIEW.md)
does not authorize another implementation or turn proposal-local repeat into member history.
