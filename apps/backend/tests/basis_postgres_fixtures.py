"""Real frozen reader composition; meanings are authored before original publication."""

import pytest
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition.resolution_contracts import NutritionResolutionHandoffV2
from app.modules.nutrition.resolution_estimator import estimate_nutrition_resolution
from app.modules.planning.basis_capture import (
    _install_isolated_basis_fixture,
    capture_test_basis_sources,
)
from basis_fixtures import artifact, original_guideline, original_rule
from nutrition_resolution_postgres_fixtures import capture_nre, nre_case  # noqa: F401
from nutrition_root_postgres_fixtures import reader


@pytest.fixture
def mba_case(request, monkeypatch):
    import nutrition_root_postgres_fixtures as root_setup
    import nutrition_synthesis_postgres_fixtures as rule_setup

    monkeypatch.setattr(root_setup, "guideline", original_guideline(root_setup.guideline))
    monkeypatch.setattr(rule_setup, "rule", original_rule(rule_setup.rule))
    s = request.getfixturevalue("nre_case")
    ns = capture_nre(s)
    nre = NutritionResolutionHandoffV2(sources=ns, estimate=estimate_nutrition_resolution(ns))
    a = artifact(nre)
    handle = _install_isolated_basis_fixture(
        s["nre_context"], a, reader_principal="reader", actor_user_id=s["user_id"]
    )
    s.update(
        basis_artifact=a,
        basis_context=handle,
        basis_selectors=b.BasisSelectorsV1(
            nre_scope=s["nre_scope"],
            publication_id="TEST_ONLY_publication",
            assertion_id="TEST_ONLY_assertion",
            assertion_revision="v1",
            reader_principal="reader",
        ),
    )
    return s


def capture_basis(s, **reader_options):
    with reader(s, "self", **reader_options) as db:
        return capture_test_basis_sources(s["basis_context"], db, s["basis_selectors"])
