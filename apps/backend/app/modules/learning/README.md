# Behavioral learning — namespace V1.3

ADR-011, INV-022..030. Chưa có router, profile store hoặc learning engine.

Evidence classification DIRECT/CONTEXTUAL/INFERRED/PASSIVE route sang taste, kitchen context, exposure, retail calibration hoặc NoLearn. AUTOPILOT_ASSUMED không tạo durable learning; USER_CONFIRMED_COOKED không đồng nghĩa thích món. FORCED_CONFLICT_RESOLUTION bị quarantine; explicit preference vẫn thuộc member được actor chỉ định.

Learning đọc immutable event/domain contracts, không gọi planner/execution mutation facades. Preferences giữ declared/member-owned preference; learning giữ attribution và learned observations. Numeric exploration/cooldown/shrinkage defaults vẫn cần evidence/versioned policy.


MTR-041A implements only pure recipe-level **PROPOSAL_PREVIEW** contracts/replay/deduplication.
Read-only canonical capture is Planning orchestration; Learning core has no DB/Execution/solver
IO. Latest proposal advice remains PROVISIONAL, not accepted schedule or confirmed consumption.
No durable exposure history, learned profile, attribution router, repeat score or novelty.
Exposure source coverage is explicitly selected plans, never complete member consumption history.
