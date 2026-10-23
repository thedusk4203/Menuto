from datetime import timedelta
from uuid import uuid4

import pytest
from app.modules.preferences import contracts as c
from preference_fixtures import NOW, command, declaration, term
from test_architecture import check_source


def snapshot(rows=(), **kw):
    return c.ExplicitMemberPreferenceSnapshot(
        **(
            dict(
                household_id=rows[0].command.household_id if rows else uuid4(),
                member_id=rows[0].command.member_id if rows else uuid4(),
                frontier=len(rows),
                captured_at=NOW + timedelta(days=1),
                declarations=rows,
            )
            | kw
        )
    )


@pytest.mark.parametrize("kind", ["INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"])
def test_five_typed_targets(kind):
    field = {"INGREDIENT": "ingredient_id", "DIRECT_RECIPE": "recipe_id"}.get(
        kind, "feature_term_id"
    )
    q = command(target=dict(kind=kind, **{field: uuid4()}))
    assert q.target.kind == kind
    with pytest.raises(ValueError):
        command(target=dict(kind=kind, target_id=uuid4()))


@pytest.mark.parametrize(
    "field",
    [
        "evidence_strength",
        "strength_basis",
        "assertion_confidence",
        "taste_fit",
        "score",
        "affinity_score",
        "is_safe",
    ],
)
def test_raw_declaration_cannot_accept_derived_or_confidence_fields(field):
    q = command()
    with pytest.raises(ValueError):
        c.PreferenceWriteCommand.model_validate(q.model_dump() | {field: "HIGH"})
    r = declaration(q)
    with pytest.raises(ValueError):
        c.MemberPreferenceDeclarationFact.model_validate(r.model_dump() | {field: "HIGH"})


@pytest.mark.parametrize("value", ["LIKE", "DISLIKE", "NEUTRAL"])
def test_explicit_values_are_assertions_not_safety_or_scalar(value):
    r = declaration(command(value=value))
    s = snapshot((r,))
    assert s.state_for(r.command.target).status == "DECLARED"
    assert s.state_for(r.command.target).value == value
    assert not hasattr(s, "evidence_strength") and s.profile_derivation == "NOT_IMPLEMENTED"


def test_undeclared_neutral_retracted_distinct_and_immutable():
    q = command(value="NEUTRAL")
    a = declaration(q)
    bq = c.RetractMemberPreferenceCommand(
        **(
            q.model_dump(exclude={"action", "value", "reason"})
            | dict(expected_revision=0, predecessor_id=a.id)
        )
    )
    b = declaration(bq, stream_id=a.stream_id, sequence=2)
    empty = snapshot((), household_id=q.household_id, member_id=q.member_id)
    assert empty.state_for(q.target).status == "UNDECLARED"
    assert snapshot((a,)).state_for(q.target).value == "NEUTRAL"
    assert snapshot((a, b)).state_for(q.target).status == "RETRACTED"
    assert snapshot((a, b)).state_for(q.target).value is None
    with pytest.raises(ValueError):
        a.command.value = "DISLIKE"


@pytest.mark.parametrize(
    "case",
    [
        "predecessor",
        "sequence",
        "revision",
        "owner",
        "target",
        "fingerprint",
        "future_record",
        "duplicate_id",
        "duplicate_target",
    ],
)
def test_primitive_replay_rejects_corruption(case):
    q = command()
    a = declaration(q)
    bq = command(
        **(
            q.model_dump(exclude={"action", "contract_version"})
            | dict(
                expected_revision=0, predecessor_id=a.id, reason="INPUT_CORRECTION", value="DISLIKE"
            )
        )
    )
    b = declaration(bq, stream_id=a.stream_id, sequence=2)
    d = b.model_dump()
    if case == "predecessor":
        d["command"]["predecessor_id"] = uuid4()
    if case == "sequence":
        d["member_sequence"] = 3
    if case == "revision":
        d["revision_no"] = 3
    if case == "owner":
        d["command"]["member_id"] = uuid4()
    if case == "target":
        d["command"]["target"]["ingredient_id"] = uuid4()
    if case == "fingerprint":
        d["command_fingerprint"] = "f" * 64
    if case == "future_record":
        d["recorded_at"] = NOW + timedelta(days=2)
    if case == "duplicate_id":
        d["id"] = a.id
    if case == "duplicate_target":
        d = declaration(q, sequence=2).model_dump()
    if case in {"predecessor", "owner", "target"}:
        d["command_fingerprint"] = c.PreferenceWriteCommand.model_validate(
            d["command"]
        ).fingerprint()
    with pytest.raises(ValueError):
        snapshot((a, d))


def test_feature_vocabulary_review_kind_and_binding_required():
    t = term()
    q = command(target=dict(kind=t.kind, feature_term_id=t.id))
    a = declaration(q)
    for terms in (
        (),
        (t.model_copy(update=dict(status="DRAFT")),),
        (t.model_copy(update=dict(kind="FLAVOR")),),
    ):
        with pytest.raises(ValueError):
            snapshot((a,), feature_terms=terms)
    assert snapshot((a,), feature_terms=(t,)).feature_terms == (t,)


def test_snapshot_order_hash_roundtrip_and_primitive_change():
    a = declaration(command())
    q = command(household_id=a.command.household_id, member_id=a.command.member_id)
    b = declaration(q, sequence=2)
    x, y = snapshot((a, b)), snapshot((b, a))
    assert x.canonical_json() == y.canonical_json() and x.fingerprint() == y.fingerprint()
    assert c.ExplicitMemberPreferenceSnapshot.model_validate_json(x.canonical_json()) == x
    changed = snapshot((a, b), captured_at=x.captured_at + timedelta(seconds=1))
    assert changed.fingerprint() != x.fingerprint()


@pytest.mark.parametrize(
    "changes",
    [
        dict(value=None),
        dict(expected_revision=0),
        dict(provenance={}),
        dict(source="INFERRED"),
        dict(reason="RETRACTED"),
        dict(value=0.5),
    ],
)
def test_invalid_explicit_inputs_fail_closed(changes):
    with pytest.raises(ValueError):
        c.PreferenceWriteCommand.model_validate(command().model_dump() | changes)


def test_empty_snapshot_huge_frontier_rejected_without_allocating_a_range():
    with pytest.raises(ValueError):
        snapshot(frontier=9_223_372_036_854_775_807)


def test_lookup_validates_typed_target_and_explicit_neutral():
    q = command(value="NEUTRAL")
    s = snapshot((declaration(q),))
    assert s.state_for(q.target.model_dump()).value == "NEUTRAL"
    with pytest.raises(ValueError):
        s.state_for({"kind": "METHOD", "target_id": str(uuid4())})


@pytest.mark.parametrize(
    "target",
    [
        "planning.contracts",
        "execution.contracts",
        "learning.contracts",
        "inventory.public",
        "retail.public",
        "validation.public",
        "policy.contracts",
    ],
)
def test_preference_core_has_no_planner_learning_execution_dependencies(target):
    assert check_source(f"import app.modules.{target}", "app.modules.preferences.public")


def test_catalog_vocabulary_cannot_import_preference_implementation():
    assert check_source("import app.modules.preferences.models", "app.modules.catalog.models")
