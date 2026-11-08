"""Pure explicit-intent interface; no report-proof, transport adapter or admission."""

from app.modules.policy.explicit_intent import resolve_explicit_plan_intent_v1

__all__ = ("resolve_explicit_plan_intent_v1",)
