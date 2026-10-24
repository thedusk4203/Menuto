"""Synthetic explicit policy amounts; no production penalty defaults."""

from app.modules.learning import contracts as c
from app.modules.learning.public import trace_recipe_decay
from decay_fixtures import decay_input


def penalty_input(trace=None):
    trace = trace if trace is not None else trace_recipe_decay(decay_input())
    return c.RecipeRepeatPenaltyInput(
        trace=trace,
        policy=c.RecipeRepeatPenaltyPolicy(
            policy_id="synthetic.repeat",
            policy_version="test.v1",
            provenance=trace.subject.policy.provenance,
            operator="SUM_RETAINED_OCCURRENCES",
            unit_penalty=c.RepeatPenaltyAmount(numerator=3, denominator=1),
        ),
    )
