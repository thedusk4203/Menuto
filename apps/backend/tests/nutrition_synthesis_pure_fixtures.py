"""Synthetic retained-cut mutation helpers. They do NOT establish canonical DB origin."""

import json
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition import root_public
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.synthesis import (
    nutrition_policy_requirements,
    synthesize_nutrition_policy,
)
from app.modules.nutrition.synthesis_journal import applicability, digest
from nutrition_root_fixtures import rebuild_test_journals
from nutrition_synthesis_fixtures import instruction, resolution


def retained():
    return c.NutritionPolicy.model_validate(
        json.loads(
            (
                Path(__file__).parent / "fixtures/nutrition_synthesis_retained_TEST_ONLY.json"
            ).read_text()
        )
    )


def hash_sources(value):
    data = canonical(
        c.NutritionSynthesisSourceSnapshot.model_validate(
            canonical(value) | dict(source_fingerprint="0" * 64)
        )
    )
    data.pop("source_fingerprint", None)
    data["source_fingerprint"] = digest("sources", data)
    return c.NutritionSynthesisSourceSnapshot.model_validate(data)


def hash_policy(value):
    data = canonical(
        c.NutritionPolicy.model_validate(canonical(value) | dict(result_fingerprint="0" * 64))
    )
    data.pop("result_fingerprint", None)
    data["result_fingerprint"] = digest("policy", data)
    return c.NutritionPolicy.model_validate(data)


def reauthor_rule(sources, mutate):
    data = deepcopy(canonical(sources))
    draft = next(r for r in data["records"] if r["command"]["body"]["kind"] == "DRAFT")
    body = draft["command"]["body"]["rule"]
    mutate(body)
    body = canonical(c.NutritionSynthesisRuleBody.model_validate(body))
    draft["command"]["body"]["rule"] = body
    fingerprint = digest("rule", body)
    manifest = digest("evidence-manifest", body["evidence"])
    data["request"]["selection"].update(body_fingerprint=fingerprint, evidence_fingerprint=manifest)
    for record in data["records"]:
        b = record["command"]["body"]
        if b["kind"] in {"REVIEW", "PUBLICATION"}:
            b["body_fingerprint"] = fingerprint
            if b["kind"] == "REVIEW":
                b["evidence_fingerprint"] = manifest
    previous = None
    for record in data["records"]:
        record["command"] = canonical(c.NutritionSynthesisCommand.model_validate(record["command"]))
        record["previous_hash"] = previous
        record["command_hash"] = digest("command", record["command"])
        record["event_hash"] = digest(
            "event", {k: v for k, v in record.items() if k != "event_hash"}
        )
        previous = record["event_hash"]
    data["frontier_hash"] = previous
    return hash_sources(data)


def reauthor_root(sources, mutate):
    data = canonical(sources)
    primitive = canonical(sources.request.root.sources)
    mutate(primitive)
    root = root_public.resolve_nutrition_root(rebuild_test_journals(primitive))
    data["request"]["root"] = canonical(root)
    app = canonical(applicability(root.sources.request))
    for grant in data["grant_facts"]:
        grant["command"]["applicability"] = app
        grant["command_hash"] = digest("grant-command", grant["command"])
    for frontier in data["authority_frontiers"]:
        history = [
            g
            for g in data["grant_facts"]
            if g["command"]["principal_id"] == frontier["principal_id"]
            and g["command"]["capability"] == frontier["capability"]
        ]
        if history:
            head = max(history, key=lambda g: g["generation"])
            frontier["head_hash"] = digest("grant-fact", head)
    return reauthor_rule(hash_sources(data), lambda rule: rule.update(applicability=app))


def derive(sources, *, provide_resolution=True):
    try:
        requirement = nutrition_policy_requirements(sources)
    except ValueError:
        return synthesize_nutrition_policy(sources)
    return synthesize_nutrition_policy(
        sources, resolution(requirement, sources.request.root) if provide_resolution else None
    )


def remove_root_records(sources, kind):
    def mutate(value):
        value["sources"] = [r for r in value["sources"] if r["command"]["body"]["kind"] != kind]

    return reauthor_root(sources, mutate)


def rehash_rule_records(data):
    previous = None
    for record in data["records"]:
        record["command"] = canonical(c.NutritionSynthesisCommand.model_validate(record["command"]))
        record["previous_hash"] = previous
        record["command_hash"] = digest("command", record["command"])
        record["event_hash"] = digest(
            "event", {k: v for k, v in record.items() if k != "event_hash"}
        )
        previous = record["event_hash"]
    last = data["records"][-1] if data["records"] else None
    data.update(
        frontier_revision=len(data["records"]),
        frontier_id=last["id"] if last else None,
        frontier_hash=previous,
    )
    data["frame"]["row_count"] = sum(
        len(data[k])
        for k in (
            "records",
            "principal_facts",
            "provider_facts",
            "grant_facts",
            "authority_frontiers",
            "principal_frontiers",
        )
    )
    return hash_sources(data)


def withdraw(sources, *, effective_at=None):
    data = canonical(sources)
    previous = data["records"][-1]
    record = deepcopy(previous)
    identity = str(uuid4())
    record.update(id=identity, sequence=previous["sequence"] + 1)
    record["recorded_order"] = (
        max(
            f["recorded_order"]
            for group in ("records", "principal_facts", "provider_facts", "grant_facts")
            for f in data[group]
        )
        + 1
    )
    command = record["command"]
    command.update(
        event_id=identity,
        expected_revision=previous["sequence"],
        predecessor_id=previous["id"],
        idempotency_key="TEST_ONLY_withdraw_" + identity,
    )
    command["body"].update(
        action="RETRACT", review_id=None, predecessor_publication_id=previous["id"]
    )
    if effective_at is not None:
        command["body"]["effective_at"] = effective_at
    record["grant_id"] = next(
        g["id"]
        for g in data["grant_facts"]
        if g["command"]["capability"] == "SYNTHESIS_RULE_WITHDRAW"
        and g["command"]["principal_id"] == record["principal_id"]
    )
    data["records"].append(record)
    return rehash_rule_records(data)


def retract_goal(sources):
    def mutate(primitive):
        prior = next(r for r in primitive["sources"] if r["command"]["body"]["kind"] == "GOAL")
        tombstone = deepcopy(prior)
        identity = str(uuid4())
        tombstone["id"] = tombstone["command"]["revision_id"] = identity
        tombstone["sequence"] = 2
        tombstone["recorded_order"] = (
            max(r["recorded_order"] for r in primitive["authority"] + primitive["sources"]) + 1
        )
        authority = next(r for r in primitive["authority"] if r["id"] == prior["grant_event_id"])
        tombstone["authority_generation"] = max(
            r["sequence"]
            for r in primitive["authority"]
            if r["stream_key"] == authority["stream_key"]
        )
        tombstone["recorded_at"] = max(
            r["recorded_at"] for r in primitive["authority"] + primitive["sources"]
        )
        tombstone["command"].update(
            expected_revision=1,
            predecessor_id=prior["id"],
            idempotency_key="TEST_ONLY_retract_" + identity,
        )
        tombstone["command"]["body"].update(
            operation="RETRACT", direction=None, replaces=[prior["id"]]
        )
        primitive["sources"].append(tombstone)

    return reauthor_root(sources, mutate)


def weekly_sources(sources):
    """One invented seven-cell TEST_ONLY interval, not a production calendar/policy."""

    def extend(primitive):
        temporal = primitive["request"]["temporal"]
        temporal.update(kind="WEEK", period_id="TEST_ONLY_week")
        temporal["interval"]["end"] = "2026-09-08T00:00:00.000000Z"
        for record in primitive["sources"]:
            body = record["command"]["body"]
            if body["kind"] == "DRAFT":
                guideline = body["guideline"]
                guideline["effective"] = deepcopy(temporal["interval"])
                for clause in guideline["clauses"]:
                    clause["descriptor"]["temporal"] = deepcopy(temporal)
                fp = n.nutrition_root_hash("nutrition.guideline-body.v1", guideline)
            if body["kind"] in {"OBSERVATION", "GOAL", "ASSESSMENT"}:
                body["effective"] = deepcopy(temporal["interval"])
        primitive["request"]["guideline_body_fingerprint"] = fp
        for record in primitive["sources"]:
            body = record["command"]["body"]
            if body["kind"] in {"REVIEW", "PUBLICATION"}:
                body["body_fingerprint"] = fp
            if body["kind"] == "ASSESSMENT":
                body["guideline_body_fingerprint"] = fp
        first = rebuild_test_journals(primitive)
        observations = {
            r["id"]: r for r in first["sources"] if r["command"]["body"]["kind"] == "OBSERVATION"
        }
        for record in first["sources"]:
            if record["command"]["body"]["kind"] == "ASSESSMENT":
                for ref in record["command"]["body"]["observations"]:
                    ref["fact_hash"] = observations[ref["revision_id"]]["fact_hash"]
        primitive.clear()
        primitive.update(first)

    wider = reauthor_root(sources, extend)
    root = wider.request.root
    assert root.availability == "AVAILABLE"
    span = root.sources.request.temporal
    cells = []
    for i in range(7):
        cells.append(
            n.NutritionTemporalScope(
                kind="DAY",
                period_id="TEST_ONLY_cell_" + str(i),
                calendar=span.calendar,
                timezone=span.timezone,
                interval=dict(
                    start=span.interval.start + timedelta(days=i),
                    end=span.interval.start + timedelta(days=i + 1),
                ),
            )
        )
    key = root.roots[0].clause.root_key
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
    required = []
    for identity, layer, kind, inputs in (
        ("goal", "GOAL_PROTECTION", "RANGE", ("lower", "upper")),
        ("week_goal", "WEEKLY_GOAL", "RANGE", ("lower", "upper")),
        ("week_center", "WEEKLY_CENTER", "TARGET", ("lower",)),
    ):
        operations.append(
            instruction(
                identity,
                "MAKE_CONSTRAINT",
                inputs,
                root_key=key,
                constraint_kind=kind,
                layer=layer,
                temporal=span,
            )
        )
        required.append(identity)
    operations.append(
        instruction("direction", "CHECK_DIRECTION", ("goal", "upper"), comparator="CONTAINS")
    )
    operations.append(
        instruction(
            "week_direction", "CHECK_DIRECTION", ("week_goal", "upper"), comparator="CONTAINS"
        )
    )
    for i, cell in enumerate(cells):
        for endpoint in ("lower", "upper"):
            operations.append(
                instruction(
                    f"{endpoint}{i}",
                    "REVIEWED_PERIOD_PROJECTION",
                    (endpoint,),
                    coefficient=dict(numerator=1, denominator=7),
                    offset=dict(numerator=0, denominator=1),
                    temporal=cell,
                )
            )
        inputs = (f"lower{i}", f"upper{i}")
        for identity, layer in (
            (f"daily{i}", "DAILY_PROTECTION"),
            (f"relaxed{i}", "COMFORT"),
            (f"standard{i}", "COMFORT"),
            (f"precise{i}", "COMFORT"),
        ):
            operations.append(
                instruction(
                    identity,
                    "MAKE_CONSTRAINT",
                    inputs,
                    root_key=key,
                    constraint_kind="RANGE",
                    layer=layer,
                    temporal=cell,
                )
            )
        operations.append(
            instruction(
                f"precision{i}",
                "SELECT_PRECISION_CASE",
                (f"relaxed{i}", f"standard{i}", f"precise{i}"),
            )
        )
        required.extend((f"daily{i}", f"precision{i}"))
    operations.append(
        instruction(
            "sum",
            "FINITE_PERIOD_SUM",
            tuple(f"lower{i}" for i in range(7)),
            coefficients=(dict(numerator=1, denominator=1),) * 7,
            temporal=span,
        )
    )

    def author(body):
        body["effective"] = canonical(span.interval)
        body["calendar_cells"] = canonical(cells)
        body["cases"] = [
            dict(
                id="TEST_ONLY_week_case",
                direction="MAINTAIN",
                operations=canonical(operations),
                required_claims=required,
                daily_root_keys=[key],
                comfort_root_keys=[key],
                weekly="REQUIRED",
            )
        ]

    return reauthor_rule(wider, author)
