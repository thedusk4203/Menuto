"""MTR-026 review: current frontier is intentionally not production freshness authority."""


import pytest
from app.modules.nutrition.models import MemberSafetyConstraint
from app.modules.validation.public import validate_subject
from sqlalchemy.orm import Session
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_validation import capture, seed_source

pytestmark = pytest.mark.postgres


def test_new_safety_fact_changes_subject_without_advancing_existing_frontier(postgres_engine):
    keys, actor, ingredient = seed_source(postgres_engine)
    before = capture(postgres_engine, keys)
    member_id = before.proposal.graph.tracked_member_id
    with Session(postgres_engine) as writer:
        writer.add(
            MemberSafetyConstraint(
                household_id=keys["household_id"],
                member_id=member_id,
                kind="EXCLUDED_INGREDIENT",
                code="review.new.exclusion",
                ingredient_id=ingredient,
                created_by_user_id=actor,
            )
        )
        writer.commit()
    after = capture(postgres_engine, keys)
    assert before.source_frontier == after.source_frontier
    assert before.fingerprint != after.fingerprint
    assert before.member_safety[0].constraints == ()
    assert after.member_safety[0].constraints
    assert any(f.code == "FORBIDDEN_INGREDIENT" for f in validate_subject(after).findings)
    assert not validate_subject(before).activation_authorized
    assert not validate_subject(after).activation_authorized
