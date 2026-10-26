"""Raw SQL cannot bypass semantic anchors, finite mapping or frozen policy pins."""

import json

import pytest
from app.domain.feature_identity import canonical
from hierarchy_fixtures import policy
from hierarchy_postgres_fixtures import capture, publication, publish
from hierarchy_postgres_fixtures import hierarchy_server as hierarchy_server
from hierarchy_postgres_fixtures import hierarchy_source as hierarchy_source
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_hierarchy_policy import enabled, positive_neutral_policy

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize(
    "case",
    [
        "H01",
        "H02",
        "H03",
        "H05",
        "H06",
        "DESCRIPTOR",
        "MISSING_CELL",
        "UNKNOWN_KIND",
        "DUPLICATE_CELL",
        "ZERO_ATTENUATION",
        "NEGATIVE_ATTENUATION",
        "DUPLICATE_SEMANTIC",
        "FROZEN_POLICY_PIN",
    ],
)
def test_h01_h06_raw_sql_semantic_and_coordinate_guard(hierarchy_source, case):
    s = hierarchy_source
    body = canonical(s["policy"])
    direction = enabled(body)
    rows = {r["source_affinity_value"]: r for r in direction["rows"]}
    if case == "H01":
        rows["NEUTRAL"]["output_amount"] = dict(numerator=1, denominator=2)
    elif case == "H02":
        rows["DISLIKE"]["output_amount"] = dict(numerator=1, denominator=2)
    elif case == "H03":
        rows["LIKE"]["output_amount"] = dict(numerator=-1, denominator=2)
    elif case in {"H05", "H06"}:
        rows["NEUTRAL"]["expected_source_amount"] = rows["LIKE"]["expected_source_amount"]
    elif case == "DESCRIPTOR":
        rows["LIKE"]["source_descriptor"]["target_kind"] = "METHOD"
    elif case == "MISSING_CELL":
        body["directions"].pop()
    elif case == "UNKNOWN_KIND":
        body["directions"][0]["source_kind"] = "MAIN_PROTEIN"
    elif case == "DUPLICATE_CELL":
        body["directions"][-1] = body["directions"][0]
    elif case == "ZERO_ATTENUATION":
        direction["attenuation"] = dict(numerator=0, denominator=1)
    elif case == "NEGATIVE_ATTENUATION":
        direction["attenuation"] = dict(numerator=-1, denominator=2)
    elif case == "DUPLICATE_SEMANTIC":
        direction["rows"][1] = direction["rows"][0]
    else:
        body["compatibility_policy"]["explicit_policy_fingerprint"] = "f" * 64
    command = canonical(publication(s))
    command["policy"] = body
    with Session(
        s["engines"]["curator"].execution_options(isolation_level="SERIALIZABLE")
    ) as session:
        with pytest.raises(DBAPIError):
            session.scalar(
                text("SELECT menuto_hierarchy.publish(CAST(:c AS jsonb))"),
                {"c": json.dumps(command)},
            )
    assert capture(s).frontier.source_generation == 0


def test_h04_h07_h09_positive_source_neutral_publishes_zero_without_global_ownership(
    hierarchy_source,
):
    s = dict(hierarchy_source, policy=positive_neutral_policy())
    receipt = publish(s, publication(s))
    body = receipt.publication.command.policy
    row = next(
        r
        for d in body.directions
        if d.enabled
        for r in d.rows
        if r.source_affinity_value == "NEUTRAL"
    )
    assert row.expected_source_amount.numerator > 0 and row.output_amount.numerator == 0
    assert body.policy_ownership == "HIERARCHY_COMPATIBILITY_REPLAY_ONLY"
    with s["engines"]["root"].connect() as root:
        assert root.scalar(text("SELECT count(*) FROM reference_prior_providers")) == 0
        assert root.scalar(text("SELECT count(*) FROM member_preference_declarations")) == 0


def test_h08_partial_finite_semantic_map_is_published_without_filling_rows(hierarchy_source):
    s = dict(
        hierarchy_source,
        policy=policy(source_kind="INGREDIENT", destination_kind="INGREDIENT", states=("LIKE",)),
    )
    receipt = publish(s, publication(s))
    assert [
        r.source_affinity_value
        for d in receipt.publication.command.policy.directions
        if d.enabled
        for r in d.rows
    ] == ["LIKE"]


def test_c02_exact_nearby_rationals_use_cross_products_not_rounded_division(hierarchy_source):
    # These distinct fractions differ by less than 1e-18 around 1/2.
    from app.modules.preferences.hierarchy_contracts import HierarchyTransferPolicy

    body = canonical(hierarchy_source["policy"])
    reference = body["compatibility_policy"]["reference_maps"][0]
    reference["rows"][0]["reference_amount"].update(numerator=1073741822, denominator=2147483645)
    reference["rows"][1]["reference_amount"].update(numerator=1073741823, denominator=2147483647)
    reference["rows"] = reference["rows"][:2]
    compatibility = body["compatibility_policy"]
    from app.modules.preferences.prior_affinity_contracts import ExactTargetPriorCompatibilityPolicy

    cp = ExactTargetPriorCompatibilityPolicy.model_validate(compatibility)
    for d in body["directions"]:
        for row in d["rows"]:
            row["source_descriptor"] = canonical(cp.coordinate_for(d["source_kind"]))
    s = dict(hierarchy_source, policy=HierarchyTransferPolicy.model_validate(body))
    receipt = publish(s, publication(s))
    assert receipt.publication.command.policy == s["policy"]
