"""Real protected TEST_ONLY DAY/WEEK source authors; no frozen fixture edits."""

from datetime import timedelta

import pytest
from app.domain.feature_identity import canonical
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.resolution_contracts import NutritionResolutionHandoffV2
from app.modules.nutrition.resolution_estimator import estimate_nutrition_resolution
from app.modules.planning.basis_capture import _install_isolated_basis_fixture
from basis_fixtures import artifact, meaning, original_guideline, original_rule, proof
from nutrition_resolution_postgres_fixtures import capture_nre
from nutrition_root_fixtures import amount
from nutrition_synthesis_fixtures import instruction
from nutrition_synthesis_fixtures import rule as day_rule


def week_rule(root, provider, family):
    base = day_rule(root, provider, family)
    span, key = root.sources.request.temporal, root.roots[0].clause.root_key
    cells = tuple(
        b.n.NutritionTemporalScope(
            kind="DAY",
            period_id="TEST_ONLY_day_" + str(i),
            calendar=span.calendar,
            timezone=span.timezone,
            interval=dict(
                start=span.interval.start + timedelta(days=i),
                end=span.interval.start + timedelta(days=i + 1),
            ),
        )
        for i in range(7)
    )
    ops, required = list(base.cases[0].operations[:2]), []
    for ident, layer, kind, args in (
        ("goal", "GOAL_PROTECTION", "RANGE", ("lower", "upper")),
        ("week_goal", "WEEKLY_GOAL", "RANGE", ("lower", "upper")),
        ("week_center", "WEEKLY_CENTER", "TARGET", ("lower",)),
    ):
        ops.append(
            instruction(
                ident,
                "MAKE_CONSTRAINT",
                args,
                root_key=key,
                layer=layer,
                constraint_kind=kind,
                temporal=span,
            )
        )
        required.append(ident)
    ops += [
        instruction("direction", "CHECK_DIRECTION", ("goal", "upper"), comparator="CONTAINS"),
        instruction(
            "week_direction", "CHECK_DIRECTION", ("week_goal", "upper"), comparator="CONTAINS"
        ),
    ]
    for index, cell in enumerate(cells):
        for end in ("lower", "upper"):
            ops.append(
                instruction(
                    end + str(index),
                    "REVIEWED_PERIOD_PROJECTION",
                    (end,),
                    coefficient=dict(numerator=1, denominator=7),
                    offset=dict(numerator=0, denominator=1),
                    temporal=cell,
                )
            )
        for ident, layer in (
            ("daily", "DAILY_PROTECTION"),
            ("relaxed", "COMFORT"),
            ("standard", "COMFORT"),
            ("precise", "COMFORT"),
        ):
            ops.append(
                instruction(
                    ident + str(index),
                    "MAKE_CONSTRAINT",
                    ("lower" + str(index), "upper" + str(index)),
                    root_key=key,
                    layer=layer,
                    constraint_kind="RANGE",
                    temporal=cell,
                )
            )
        ops.append(
            instruction(
                "precision" + str(index),
                "SELECT_PRECISION_CASE",
                tuple(x + str(index) for x in ("relaxed", "standard", "precise")),
            )
        )
        required.extend(("daily" + str(index), "precision" + str(index)))
    for name in ("relaxed", "standard", "precise"):
        ops.append(
            instruction(
                "week_" + name,
                "MAKE_CONSTRAINT",
                ("lower", "upper"),
                root_key=key,
                layer="COMFORT",
                constraint_kind="RANGE",
                temporal=span,
            )
        )
    ops.append(
        instruction(
            "week_precision",
            "SELECT_PRECISION_CASE",
            tuple("week_" + x for x in ("relaxed", "standard", "precise")),
        )
    )
    required.append("week_precision")
    ops.append(
        instruction(
            "sum",
            "FINITE_PERIOD_SUM",
            tuple("lower" + str(i) for i in range(7)),
            coefficients=(dict(numerator=1, denominator=1),) * 7,
            temporal=span,
        )
    )
    case_id = "TEST_ONLY_week_case"
    claims = []
    for op in ops:
        if op.kind == "MAKE_CONSTRAINT":
            desc = b.n.NutritionRootDescriptor.model_validate(
                canonical(root.roots[0].clause.descriptor) | {"temporal": canonical(op.temporal)}
            )
            claims.append(("rule:" + case_id + ":" + op.id, meaning(desc)))
    evidence = tuple(
        sorted(
            (*base.evidence, *(proof(claims[i : i + 8]) for i in range(0, len(claims), 8))),
            key=lambda x: x.evidence_id,
        )
    )
    return c.NutritionSynthesisRuleBody.model_validate(
        canonical(base)
        | dict(
            calendar_cells=canonical(cells),
            evidence=canonical(evidence),
            cases=[
                dict(
                    id=case_id,
                    direction="MAINTAIN",
                    operations=canonical(ops),
                    required_claims=required,
                    daily_root_keys=[key],
                    comfort_root_keys=[key],
                    weekly="REQUIRED",
                )
            ],
        )
    )


@pytest.fixture
def piv_case(request, monkeypatch):
    import nutrition_resolution_postgres_fixtures as nre_setup
    import nutrition_root_postgres_fixtures as root_setup
    import nutrition_synthesis_postgres_fixtures as rule_setup

    mode = getattr(request, "param", "DAY")
    week = mode == "WEEK"
    if week:
        original_interval, guideline = root_setup.interval, root_setup.guideline
        span = original_interval("2026-09-01T00:00:00Z", "2026-09-08T00:00:00Z")
        monkeypatch.setattr(root_setup, "interval", lambda: span)

        def weekly_guideline(*args, **kwargs):
            body = canonical(guideline(*args, **kwargs))
            body["effective"] = canonical(span)
            for clause in body["clauses"]:
                clause["descriptor"]["temporal"].update(
                    kind="WEEK", period_id="TEST_ONLY_week", interval=canonical(span)
                )
                clause["constraint"].update(
                    lower=canonical(amount(49)), upper=canonical(amount(91))
                )
            return b.n.NutritionGuidelineBody.model_validate(body)

        monkeypatch.setattr(root_setup, "guideline", original_guideline(weekly_guideline))
        monkeypatch.setattr(rule_setup, "rule", week_rule)
        food, scope = nre_setup.food, nre_setup.scope

        def weekly_food(*args, **kwargs):
            recipe, identities, refs = food(*args, **kwargs)
            data = canonical(recipe)
            data["ingredients"][0]["adjustment"] = dict(kind="NONE", min_delta="0", max_delta="0")
            return type(recipe).model_validate(data), identities, refs

        def weekly_scope(synthesis, recipe, refs):
            q = canonical(scope(synthesis, recipe, refs))
            # UUID ordering is unrelated to authored serving amounts. Select the
            # exact TEST_ONLY one-serving tier, not a random first UUID.
            tier = str(next(t.id for t in recipe.portion_tiers if t.key == "TEST_ONLY_1"))
            q["recipes"][0]["tier_ids"] = [tier]
            alternative = next(x for x in q["slots"][0]["alternatives"] if x["tier_id"] == tier)
            first = synthesis.request.root.sources.request.temporal.interval.start
            q["slots"] = [
                dict(
                    slot_id="TEST_ONLY_day_" + str(i),
                    interval=dict(
                        start=first + timedelta(days=i), end=first + timedelta(days=i + 1)
                    ),
                    alternatives=[alternative | dict(slot_id="TEST_ONLY_day_" + str(i))],
                )
                for i in range(7)
            ]
            return type(scope(synthesis, recipe, refs)).model_validate(q)

        monkeypatch.setattr(nre_setup, "food", weekly_food)
        monkeypatch.setattr(nre_setup, "scope", weekly_scope)
    else:
        guideline = root_setup.guideline
        if mode == "H_EMPTY":

            def absent_support_guideline(*args, **kwargs):
                body = canonical(guideline(*args, **kwargs))
                body["clauses"][0]["constraint"].update(
                    lower=canonical(amount(100)), upper=canonical(amount(101))
                )
                return b.n.NutritionGuidelineBody.model_validate(body)

            monkeypatch.setattr(
                root_setup, "guideline", original_guideline(absent_support_guideline)
            )
        else:
            monkeypatch.setattr(root_setup, "guideline", original_guideline(guideline))
        monkeypatch.setattr(rule_setup, "rule", original_rule(rule_setup.rule))
    s = request.getfixturevalue("nre_case")
    ns = capture_nre(s)
    nre = NutritionResolutionHandoffV2(sources=ns, estimate=estimate_nutrition_resolution(ns))
    a = artifact(nre)
    s.update(
        basis_artifact=a,
        basis_context=_install_isolated_basis_fixture(
            s["nre_context"], a, reader_principal="reader", actor_user_id=s["user_id"]
        ),
        basis_selectors=b.BasisSelectorsV1(
            nre_scope=s["nre_scope"],
            publication_id="TEST_ONLY_publication",
            assertion_id="TEST_ONLY_assertion",
            assertion_revision="v1",
            reader_principal="reader",
        ),
    )
    return s
