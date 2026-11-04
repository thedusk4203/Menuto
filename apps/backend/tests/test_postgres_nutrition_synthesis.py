"""NPS real PostgreSQL protected source obligations. All values are TEST_ONLY."""

import pytest
from app.modules.nutrition.synthesis import (
    nutrition_policy_requirements,
    synthesize_nutrition_policy,
)
from app.modules.nutrition.synthesis_contracts import NutritionPolicyValidationInput
from app.modules.validation.nutrition_policy import validate_nutrition_policy_independently
from nutrition_root_postgres_fixtures import nrc_server  # noqa: F401
from nutrition_synthesis_fixtures import resolution
from nutrition_synthesis_postgres_fixtures import capture_rules, publish, setup_synthesis

pytestmark = pytest.mark.postgres


def test_nps023_one_actual_execute_only_root_and_rule_reader(nrc_server):  # noqa: F811
    s = setup_synthesis(nrc_server)
    publish(s)
    sources = capture_rules(s)
    requirements = nutrition_policy_requirements(sources)
    result = synthesize_nutrition_policy(sources, resolution(requirements, sources.request.root))
    assert result.outcome == "AVAILABLE"
    assert not result.planner_ready and not result.activation_ready
    report = validate_nutrition_policy_independently(
        NutritionPolicyValidationInput(
            policy=result, coverage="SYNTHESIS_SOURCE_AND_POLICY_SEMANTICS"
        )
    )
    assert report.decision == "CONSISTENT"
    assert sources.frame.backend_pid == sources.request.root.sources.capture.backend_pid
