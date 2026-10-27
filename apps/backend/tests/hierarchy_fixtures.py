"""Explicit synthetic hierarchy policies, never production defaults or source claims."""

from uuid import uuid4

from app.modules.preferences import hierarchy_contracts as h
from preference_fixtures import provenance
from prior_shrinkage_fixtures import consumer_input


def policy(
    *, source_kind="INGREDIENT", destination_kind="PROTEIN", states=("DISLIKE", "NEUTRAL", "LIKE")
):
    subject = consumer_input(kind=source_kind)
    explicit, compatibility = subject.explicit.policy, subject.compatibility_policy
    group = next(g for g in explicit.target_policies if g.target_kind == source_kind)
    rows = [
        h.HierarchyTransferMapRow(
            source_descriptor=compatibility.coordinate_for(source_kind),
            source_affinity_value=r.value,
            expected_source_amount=r.amount,
            output_amount=h.HierarchyPolicyAmount(
                numerator={"DISLIKE": -1, "NEUTRAL": 0, "LIKE": 1}[r.value], denominator=1
            ),
        )
        for r in group.affinity_rules
        if r.value in states
    ]
    return h.HierarchyTransferPolicy(
        policy_id=uuid4(),
        policy_version=1,
        explicit_policy=explicit,
        compatibility_policy=compatibility,
        provenance=h.HierarchyProvenance(
            **(provenance(kind="REVIEWED_REFERENCE").model_dump() | {"content_hash": "a" * 64})
        ),
        directions=[
            dict(
                source_kind=a,
                destination_kind=b,
                enabled=(a, b) == (source_kind, destination_kind),
                support_modes=(
                    ["REVIEWED_EXACT_PAIR", "CLASSIFICATION_BOUND_PAIR"]
                    if (
                        {a, b} == {"INGREDIENT", "PROTEIN"}
                        or (
                            "DIRECT_RECIPE" in {a, b}
                            and len({a, b}) == 2
                            and bool({a, b} & {"PROTEIN", "METHOD", "FLAVOR"})
                        )
                    )
                    else ["REVIEWED_EXACT_PAIR"]
                )
                if (a, b) == (source_kind, destination_kind)
                else [],
                rows=rows if (a, b) == (source_kind, destination_kind) else [],
                attenuation=dict(numerator=1, denominator=2)
                if (a, b) == (source_kind, destination_kind)
                else None,
            )
            for a in sorted(h.KINDS)
            for b in sorted(h.KINDS)
        ],
    )


def enable_direction(original, source_kind, destination_kind):
    body = original.model_dump(mode="json")
    template = policy(source_kind=source_kind, destination_kind=destination_kind)
    cell = next(d for d in template.directions if d.enabled).model_dump(mode="json")
    for row in cell["rows"]:
        row["source_descriptor"] = original.compatibility_policy.coordinate_for(
            source_kind
        ).model_dump(mode="json")
        group = next(
            g for g in original.explicit_policy.target_policies if g.target_kind == source_kind
        )
        row["expected_source_amount"] = next(
            r.amount for r in group.affinity_rules if r.value == row["source_affinity_value"]
        ).model_dump(mode="json")
    body["directions"] = [
        cell if (d["source_kind"], d["destination_kind"]) == (source_kind, destination_kind) else d
        for d in body["directions"]
    ]
    return h.HierarchyTransferPolicy.model_validate(body)
