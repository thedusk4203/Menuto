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
DB IO, global history, member aggregation, ranking or cross-dimension utility. NOT FROZEN.
