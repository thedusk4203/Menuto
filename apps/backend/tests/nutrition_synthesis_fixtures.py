"""TEST_ONLY symbolic algebra. These invented values have NO nutritional meaning."""

import json
from uuid import uuid4

from app.domain.feature_identity import canonical
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.synthesis_journal import applicability, digest
from nutrition_root_fixtures import amount, evidence


def instruction(identity, kind, inputs=(), **fields):
    body = dict(
        id=identity,
        kind=kind,
        inputs=inputs,
        root_key=None,
        endpoint=None,
        reference_role=None,
        coefficient=None,
        offset=None,
        constraint_kind=None,
        layer=None,
        temporal=None,
        coefficients=(),
        comparator=None,
        evidence_id="TEST_ONLY_algebra",
    )
    return c.NutritionSynthesisOperation(**(body | fields))


def rule(root, provider_id, family_id):
    clause = root.roots[0].clause
    key, temporal = clause.root_key, clause.descriptor.temporal
    proof = evidence("TEST_ONLY finite algebra", evidence_id="TEST_ONLY_algebra")
    operations = [
        instruction(
            "lower",
            "COPY_REFERENCE",
            root_key=key,
            endpoint="lower",
            reference_role="TEST_ONLY_endpoint",
        ),
        instruction(
            "upper",
            "COPY_REFERENCE",
            root_key=key,
            endpoint="upper",
            reference_role="TEST_ONLY_reference",
        ),
    ]
    for identity, layer in (
        ("goal", "GOAL_PROTECTION"),
        ("daily", "DAILY_PROTECTION"),
        ("relaxed", "COMFORT"),
        ("standard", "COMFORT"),
        ("precise", "COMFORT"),
    ):
        operations.append(
            instruction(
                identity,
                "MAKE_CONSTRAINT",
                ("lower", "upper"),
                root_key=key,
                constraint_kind="RANGE",
                layer=layer,
                temporal=temporal,
            )
        )
    operations.extend(
        (
            instruction("direction", "CHECK_DIRECTION", ("goal", "upper"), comparator="CONTAINS"),
            instruction("precision", "SELECT_PRECISION_CASE", ("relaxed", "standard", "precise")),
        )
    )
    return c.NutritionSynthesisRuleBody(
        revision_id=uuid4(),
        provider_id=provider_id,
        family_id=family_id,
        authored_version="TEST_ONLY_v1",
        language_version="FINITE_EXACT_V1",
        purpose="BOUNDED_COMPLETE_POLICY_V1",
        environment="TEST_ONLY",
        effective=temporal.interval,
        applicability=applicability(root.sources.request),
        evidence=(proof,),
        calendar_evidence_id=proof.evidence_id,
        calendar_cells=(temporal,),
        cases=(
            dict(
                id="TEST_ONLY_maintain",
                direction="MAINTAIN",
                operations=tuple(operations),
                required_claims=("goal", "daily", "precision"),
                daily_root_keys=(key,),
                comfort_root_keys=(key,),
                weekly="NOT_APPLICABLE",
            ),
        ),
    )


def resolution(requirements, root, *, step=None):
    step = step or amount(1)
    facts = []
    recipe_version_id = str(uuid4())
    for measurement in requirements.measurements:
        body = dict(
            root_key=measurement.root_key,
            descriptor=canonical(measurement.descriptor),
            candidate_id="TEST_ONLY_complete_candidate",
            recipe_version_id=recipe_version_id,
            portion_step=canonical(step),
            discrete_unit="TEST_ONLY_discrete_unit",
            ingredient_amounts=[canonical(amount(1))],
            source_nutrients=[canonical(amount(1))],
            expected_step=canonical(step),
        )
        facts.append(
            c.NutritionResolutionFact(
                **body, primitive_fingerprint=digest("resolution-primitive", body)
            )
        )
    facts = tuple(facts)
    preimage = json.dumps(
        dict(
            kind="TEST_ONLY_RESOLUTION_FIXTURE_V1",
            estimator_version="TEST_ONLY_fixture_v1",
            facts=canonical(facts),
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    proof = c.n.NutritionSourceEvidence(
        evidence_id="TEST_ONLY_resolution_fixture",
        version="TEST_ONLY_v1",
        environment="TEST_ONLY",
        purpose="TEST_ONLY interface fixture, NOT MTR-007 or scientific evidence",
        body=preimage,
        body_fingerprint=c.n.nutrition_root_hash("nutrition.evidence-body.v1", preimage),
    )
    return c.NutritionResolutionInput(
        requirements_fingerprint=requirements.fingerprint,
        pool_fingerprint=digest("pool", facts),
        complete_pool=True,
        estimator_version="TEST_ONLY_fixture_v1",
        environment="TEST_ONLY",
        evidence=proof,
        availability="AVAILABLE",
        facts=facts,
    )
