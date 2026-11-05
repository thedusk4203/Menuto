"""MTR-040B pure contracts, head algebra, hostile inputs and exact canonical identities."""

import json
from datetime import timedelta
from uuid import uuid4

import pytest
from app.modules.preferences import contracts as c
from app.modules.preferences.profile_derivation import (
    derive_explicit_target_affinity_profile as derive,
)
from preference_fixtures import command, declaration, provenance, term
from target_affinity_fixtures import KINDS, entry, policy, revision, subject


def reparse(result):
    return c.ExplicitTargetAffinityProfileDraft.model_validate(result)


@pytest.mark.parametrize("value,n,d", [("LIKE", 3, 5), ("DISLIKE", -2, 3), ("NEUTRAL", 0, 1)])
def test_active_value_is_separate_from_policy_strength(value, n, d):
    first = declaration(command(value=value))
    result = derive(subject((first,)))
    row = result.rows[0]
    assert (row.affinity.amount.numerator, row.affinity.amount.denominator) == (n, d)
    assert row.affinity.status == "AVAILABLE" and row.evidence_strength.level == "LOW"
    assert row.current_declaration == first and row.prior.status == "UNAVAILABLE"
    assert row.shrunk_affinity.status == "UNAVAILABLE"
    assert not result.activation_ready and not result.planner_ready


@pytest.mark.parametrize("case", ["correct", "change", "retract", "restore"])
def test_latest_head_only_correction_change_retraction_restore(case):
    first = declaration(command())
    second = revision(
        first,
        value="NEUTRAL" if case == "change" else "DISLIKE",
        reason="PREFERENCE_CHANGED" if case == "change" else "INPUT_CORRECTION",
        retract=case in {"retract", "restore"},
    )
    rows = (first, second)
    if case == "restore":
        rows += (revision(second, value="LIKE"),)
    result = derive(subject(rows))
    row = result.rows[0]
    assert result.subject.source.preferences.declarations == rows
    assert row.current_declaration == rows[-1]
    if case == "retract":
        assert row.raw_state.status == "RETRACTED"
        assert row.affinity.reason == "RETRACTED" and row.evidence_strength.level == "NONE"
        assert row.evidence_strength.active_declaration_id is None
    else:
        assert row.raw_state.value == rows[-1].command.value
        assert row.evidence_strength.level == "LOW"
        assert row.affinity.declaration_id == rows[-1].id


def test_hundred_replacements_are_one_current_assertion():
    first = declaration(command())
    rows = [first]
    for _ in range(100):
        rows.append(revision(rows[-1], value="LIKE"))
    result = derive(subject(tuple(rows)))
    assert len(result.subject.source.preferences.declarations) == 101
    assert result.rows[0].evidence_strength.level == "LOW"
    assert result.rows[0].affinity.amount == derive(subject((first,))).rows[0].affinity.amount


@pytest.mark.parametrize("scope", ["empty", "subset", "never_declared"])
def test_exact_requested_scope_preserves_full_raw_history(scope):
    first = declaration(command())
    other = command().target
    targets = (
        () if scope == "empty" else (first.command.target, other) if scope == "subset" else (other,)
    )
    s = subject((first,), targets=targets)
    result = derive(s)
    assert len(result.rows) == len(targets)
    assert result.subject.source.preferences.declarations == (first,)
    assert result.subject.source.preferences.fingerprint() == s.source.preferences.fingerprint()
    for row in result.rows:
        if row.target == other:
            assert row.raw_state.status == "UNDECLARED" and row.affinity.reason == "UNDECLARED"
            assert row.current_declaration is None and row.evidence_strength.level == "NONE"
    assert result.coverage == "EXPLICIT_SOURCE_TARGETS_ONLY"
    assert result.absence_semantics == "NO_TARGET_ROWS_IS_NOT_GLOBAL_PREFERENCE_NEUTRALITY"


def test_explicit_zero_is_available_distinct_from_absence_and_retraction():
    first = declaration(command(value="NEUTRAL"))
    zero = derive(subject((first,))).rows[0]
    absent = derive(subject((), targets=(first.command.target,))).rows[0]
    retracted = derive(subject((first, revision(first, retract=True)))).rows[0]
    assert zero.affinity.amount.numerator == 0 and zero.evidence_strength.level == "LOW"
    assert {r.raw_state.status for r in (zero, absent, retracted)} == {
        "DECLARED",
        "UNDECLARED",
        "RETRACTED",
    }


@pytest.mark.parametrize("levels", [("LOW", "HIGH"), ("HIGH", "LOW"), ("MEDIUM", "MEDIUM")])
def test_self_proxy_authorship_is_preserved_without_implicit_order(levels):
    p = policy(self_level=levels[0], proxy_level=levels[1])
    for index, mode in enumerate(("SELF", "AUTHORIZED_REPRESENTATIVE")):
        first = declaration(command(authorship=mode))
        row = derive(subject((first,), interpretation=p)).rows[0]
        assert row.evidence_strength.level == levels[index]
        assert row.current_declaration.command.authorship == mode
        assert row.affinity.amount.numerator == 3


@pytest.mark.parametrize("kind", ["PROTEIN", "METHOD", "FLAVOR"])
def test_same_feature_code_new_term_id_is_separate(kind):
    a = term(kind)
    b = term(kind, code=a.code, version=2)
    first = declaration(command(target=dict(kind=kind, feature_term_id=a.id)))
    other = c.FeaturePreferenceTarget(kind=kind, feature_term_id=b.id)
    result = derive(
        subject(
            (first,),
            targets=(first.command.target, other),
            terms=(a,),
            entries=(entry(first.command.target, identity=a), entry(other, identity=b)),
        )
    )
    by_id = {r.target.feature_term_id: r for r in result.rows}
    assert by_id[a.id].raw_state.status == "DECLARED"
    assert by_id[b.id].raw_state.status == "UNDECLARED"


@pytest.mark.parametrize("source_kind", ["DIRECT_RECIPE", "INGREDIENT"])
def test_no_recipe_feature_or_ingredient_protein_transfer(source_kind):
    field = "recipe_id" if source_kind == "DIRECT_RECIPE" else "ingredient_id"
    first = declaration(command(target=dict(kind=source_kind, **{field: uuid4()})))
    features = tuple(
        c.FeaturePreferenceTarget(kind=k, feature_term_id=uuid4())
        for k in ("PROTEIN", "METHOD", "FLAVOR")
    )
    result = derive(subject((first,), targets=(first.command.target, *features)))
    assert sum(r.raw_state.status == "DECLARED" for r in result.rows) == 1
    assert all(r.evidence_strength.level == "NONE" for r in result.rows if r.target in features)


@pytest.mark.parametrize("change", ["version", "provenance", "coordinates", "strength"])
def test_policy_replay_changes_derived_identity_only(change):
    s = subject()
    before = derive(s)
    data = s.policy.model_dump()
    if change == "version":
        data["policy_version"] = "2"
    if change == "provenance":
        data["provenance"] = provenance(
            observed_at=s.source.capture_completed_at + timedelta(days=9)
        )
    if change == "coordinates":
        for p in data["target_policies"]:
            next(r for r in p["affinity_rules"] if r["value"] == "LIKE")["amount"] = dict(
                numerator=1, denominator=4
            )
    if change == "strength":
        data = policy(self_level="HIGH").model_dump()
    result = derive(s.model_copy(update=dict(policy=c.ExplicitTargetAffinityPolicy(**data))))
    assert result.fingerprint != before.fingerprint
    assert result.policy_fingerprint != before.policy_fingerprint
    assert result.source_fingerprint == before.source_fingerprint
    assert (
        result.subject.source.preferences.canonical_json() == s.source.preferences.canonical_json()
    )
    if change == "coordinates":
        assert result.rows[0].evidence_strength == before.rows[0].evidence_strength


@pytest.mark.parametrize(
    "n,d",
    [
        (1, 0),
        (1, -2),
        (2, 1),
        (-2, 1),
        (True, 2),
        (1, False),
        (0.5, 1),
        (1, 2.0),
        (float("nan"), 1),
        (float("inf"), 1),
        ("1", 2),
        (1, "2"),
    ],
)
def test_invalid_rational_rejected(n, d):
    with pytest.raises(ValueError):
        c.ExplicitAffinityAmount(numerator=n, denominator=d)


def test_equivalent_rationals_and_zero_canonicalize_identically():
    a = c.ExplicitAffinityAmount(numerator=1, denominator=2)
    assert a == c.ExplicitAffinityAmount(numerator=2, denominator=4)
    assert (
        a.canonical_json()
        == c.ExplicitAffinityAmount(numerator=999, denominator=1998).canonical_json()
    )
    assert c.ExplicitAffinityAmount(numerator=0, denominator=91).denominator == 1
    s = subject()
    data = s.model_dump()
    for p in data["policy"]["target_policies"]:
        for r in p["affinity_rules"]:
            r["amount"]["numerator"] *= 2
            r["amount"]["denominator"] *= 2
    assert derive(data).canonical_json() == derive(s).canonical_json()


@pytest.mark.parametrize(
    "case",
    [
        "missing_kind",
        "duplicate_kind",
        "missing_value",
        "duplicate_value",
        "missing_authorship",
        "duplicate_authorship",
        "none_active",
        "missing_none",
        "disordered",
        "provenance",
        "empty_policy",
    ],
)
def test_policy_matrix_is_explicit_complete_and_ordered(case):
    data = policy().model_dump()
    p = data["target_policies"][0]
    if case == "missing_kind":
        data["target_policies"] = data["target_policies"][1:]
    if case == "duplicate_kind":
        data["target_policies"] += (p,)
    if case == "missing_value":
        p["affinity_rules"] = p["affinity_rules"][1:]
    if case == "duplicate_value":
        p["affinity_rules"] += (p["affinity_rules"][0],)
    if case == "missing_authorship":
        p["strength_rules"] = p["strength_rules"][:1]
    if case == "duplicate_authorship":
        p["strength_rules"] += (p["strength_rules"][0],)
    if case == "none_active":
        p["strength_rules"][0]["level"] = "NONE"
    if case == "missing_none":
        del p["undeclared_strength"]
    if case == "disordered":
        for r in p["affinity_rules"]:
            r["amount"] = dict(numerator=1, denominator=2)
    if case == "provenance":
        data["provenance"]["kind"] = "RECEIPT"
    if case == "empty_policy":
        del data["target_policies"]
    with pytest.raises(ValueError):
        c.ExplicitTargetAffinityPolicy(**data)


@pytest.mark.parametrize(
    "field",
    [
        "affinity",
        "strength",
        "prior",
        "shrinkage",
        "head",
        "state",
        "rows",
        "source_fingerprint",
        "manifest_fingerprint",
        "policy_fingerprint",
        "fingerprint",
        "scope",
        "activation",
    ],
)
@pytest.mark.parametrize("form", ["dict", "copy", "construct"])
def test_forged_derived_claims_rejected_by_recomputation(field, form):
    result = derive(subject())
    data = result.model_dump()
    row = data["rows"][0]
    if field == "affinity":
        row["affinity"]["amount"] = dict(numerator=1, denominator=9)
    if field == "strength":
        row["evidence_strength"]["level"] = "HIGH"
    if field == "prior":
        row["prior"]["value"] = 0
    if field == "shrinkage":
        row["shrunk_affinity"]["amount"] = dict(numerator=0, denominator=1)
    if field == "head":
        row["current_declaration"] = None
    if field == "state":
        row["raw_state"]["status"] = "RETRACTED"
    if field == "rows":
        data["rows"] = ()
    if field.endswith("fingerprint"):
        data[field] = "f" * 64
    if field == "scope":
        data["learned_evidence"] = "AVAILABLE"
    if field == "activation":
        data["activation_ready"] = True
    # Rehashing a forged summary cannot turn it into a valid derived result.
    if field not in {"fingerprint", "activation", "scope"}:
        temp = c.ExplicitTargetAffinityProfileDraft.model_construct(**data)
        data["fingerprint"] = temp.expected_fingerprint()
    untrusted = (
        data
        if form == "dict"
        else result.model_copy(update=data)
        if form == "copy"
        else (c.ExplicitTargetAffinityProfileDraft.model_construct(**data))
    )
    with pytest.raises(ValueError):
        reparse(untrusted)


@pytest.mark.parametrize(
    "case",
    [
        "source_owner",
        "manifest_owner",
        "missing",
        "extra",
        "duplicate",
        "future",
        "term_conflict",
        "draft",
        "wrong_kind",
        "history",
    ],
)
def test_source_manifest_and_recursive_frozen_child_validation(case):
    t = term()
    first = declaration(command(target=dict(kind=t.kind, feature_term_id=t.id)))
    s = subject((first,), terms=(t,), entries=(entry(first.command.target, identity=t),))
    data = s.model_dump()
    src = data["source"]
    if case == "source_owner":
        src["preferences"]["member_id"] = uuid4()
    if case == "manifest_owner":
        src["manifest"]["household_id"] = uuid4()
    if case == "missing":
        src["manifest"]["entries"] = ()
    if case == "extra":
        src["request"]["requested_targets"] = ()
    if case == "duplicate":
        src["manifest"]["entries"] *= 2
    if case == "future":
        src["capture_completed_at"] = first.recorded_at
    if case == "term_conflict":
        src["manifest"]["entries"][0]["identity"]["definition"] = "Different immutable meaning"
    if case == "draft":
        src["manifest"]["entries"][0]["identity"]["status"] = "DRAFT"
    if case == "wrong_kind":
        src["manifest"]["entries"][0]["identity"]["kind"] = "FLAVOR"
    if case == "history":
        # Frozen instances otherwise bypass Pydantic nested-instance validation.
        src["preferences"] = s.source.preferences.model_copy(update=dict(frontier=99))
    with pytest.raises(ValueError):
        derive(c.ExplicitTargetAffinityInput.model_construct(**data))


def test_shuffled_unordered_sets_and_roundtrip_are_canonical():
    terms = tuple(term(k) for k in ("METHOD", "PROTEIN", "FLAVOR"))
    first = declaration(command())
    rows = [first]
    entries = [entry(first.command.target)]
    for i, t in enumerate(terms, 2):
        q = command(
            household_id=first.command.household_id,
            member_id=first.command.member_id,
            target=dict(kind=t.kind, feature_term_id=t.id),
        )
        rows.append(declaration(q, sequence=i))
        entries.append(entry(q.target, identity=t))
    s = subject(tuple(rows), terms=terms, entries=tuple(entries))
    before = derive(s)
    data = s.model_dump()
    source = data["source"]
    source["request"]["requested_targets"] = source["request"]["requested_targets"][::-1]
    source["manifest"]["entries"] = source["manifest"]["entries"][::-1]
    source["preferences"]["feature_terms"] = source["preferences"]["feature_terms"][::-1]
    source["preferences"]["declarations"] = source["preferences"]["declarations"][::-1]
    data["policy"]["target_policies"] = data["policy"]["target_policies"][::-1]
    for p in data["policy"]["target_policies"]:
        p["affinity_rules"] = p["affinity_rules"][::-1]
        p["strength_rules"] = p["strength_rules"][::-1]
    after = derive(data)
    assert before.canonical_json() == after.canonical_json()
    assert (
        c.ExplicitTargetAffinityProfileDraft.model_validate_json(
            before.canonical_json()
        ).canonical_json()
        == before.canonical_json()
    )
    data = before.model_dump()
    data["rows"] = data["rows"][::-1]
    assert reparse(data).canonical_json() == before.canonical_json()
    assert json.loads(before.canonical_json())["subject"]["source"]["preferences"] == json.loads(
        s.source.preferences.canonical_json()
    )


@pytest.mark.parametrize(
    "field",
    [
        "exposures",
        "cooked",
        "skipped",
        "out_of_stock",
        "learned",
        "contextual",
        "passive",
        "candidate",
        "taste_fit",
    ],
)
def test_nonexplicit_inputs_cannot_enter_profile(field):
    s = subject()
    with pytest.raises(ValueError):
        derive(s.model_dump() | {field: [dict(value="LIKE")] * 100})


def test_pure_derivation_uses_zero_database_network_file_io(monkeypatch):
    import builtins
    import socket

    from sqlalchemy.engine import Connection, Engine
    from sqlalchemy.orm import Session

    s = subject()

    def forbidden(*a, **kw):
        pytest.fail("Pure derivation attempted IO")

    for owner, method in (
        (Engine, "connect"),
        (Connection, "execute"),
        (Session, "execute"),
        (Session, "flush"),
        (Session, "commit"),
        (socket, "socket"),
        (socket, "create_connection"),
        (builtins, "open"),
    ):
        monkeypatch.setattr(owner, method, forbidden)
    assert derive(s).canonical_json() == derive(s).canonical_json()


def test_missing_defaults_and_kind_specific_policy_selection():
    p = policy().model_dump()
    for index, row in enumerate(p["target_policies"], 5):
        next(r for r in row["affinity_rules"] if r["value"] == "LIKE")["amount"] = dict(
            numerator=1, denominator=index
        )
    p = c.ExplicitTargetAffinityPolicy(**p)
    for kind in KINDS:
        field = {"INGREDIENT": "ingredient_id", "DIRECT_RECIPE": "recipe_id"}.get(
            kind, "feature_term_id"
        )
        q = command(target=dict(kind=kind, **{field: uuid4()}))
        t = (
            term(kind, id=q.target.feature_term_id)
            if kind in {"PROTEIN", "METHOD", "FLAVOR"}
            else None
        )
        row = derive(
            subject(
                (declaration(q),),
                terms=(t,) if t else (),
                entries=(entry(q.target, identity=t),),
                interpretation=p,
            )
        ).rows[0]
        rule = next(r for r in p.target_policies if r.target_kind == kind)
        assert row.affinity.amount == next(
            r.amount for r in rule.affinity_rules if r.value == "LIKE"
        )


def test_all_frozen_040a_041abcde_046a_definitions_and_migrations_retained():
    import ast
    from hashlib import sha256
    from pathlib import Path

    receipt = json.loads(
        Path(__file__).with_name("target_affinity_compatibility.json").read_text(encoding="utf-8")
    )

    def digest(value):
        return sha256(value.encode("utf-8")).hexdigest()

    for path, definitions in receipt["definitions"].items():
        current = {
            n.name: digest(ast.dump(n, include_attributes=False))
            for n in ast.parse(Path(path).read_text(encoding="utf-8")).body
            if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert all(current.get(k) == v for k, v in definitions.items()), path
    schema = json.loads(Path("packages/contracts/domain.schema.json").read_text(encoding="utf-8"))
    assert len(receipt["schema_definitions"]) == 237
    for name, expected in receipt["schema_definitions"].items():
        assert (
            digest(
                json.dumps(
                    schema["$defs"][name], sort_keys=True, separators=(",", ":"), ensure_ascii=False
                )
            )
            == expected
        ), name
    assert len(receipt["released_migrations"]) == 13
    for path, expected in receipt["released_migrations"].items():
        assert digest(Path(path).read_text(encoding="utf-8")) == expected, path
    directory = Path(next(iter(receipt["released_migrations"]))).parent
    assert {p.as_posix() for p in directory.glob("*.py")} == set(receipt["released_migrations"]) | {
        "apps/backend/migrations/versions/0014_reviewed_reference_prior_source.py",
        "apps/backend/migrations/versions/0015_reviewed_hierarchy_source.py",
        "apps/backend/migrations/versions/0016_nutrition_root_sources.py",
        "apps/backend/migrations/versions/0017_nutrition_synthesis_sources.py",
    }


@pytest.mark.parametrize(
    "module",
    [
        "socket",
        "httpx",
        "sqlalchemy",
        "app.modules.learning.contracts",
        "app.modules.preferences.public",
        "app.persistence.database",
        "app.modules.catalog.public",
        "app.modules.planning.contracts",
    ],
)
def test_pure_core_import_boundary_rejects_runtime_and_other_sources(module):
    from test_architecture import check_source

    assert any(
        "EXPLICIT_AFFINITY_PURE_CORE" in error
        for error in check_source(f"import {module}", "app.modules.preferences.profile_derivation")
    )


def test_unordered_duplicates_in_request_and_result_rejected():
    s = subject()
    request = s.source.request
    with pytest.raises(ValueError):
        c.ExplicitTargetAffinityCaptureRequest.model_validate(
            request.model_copy(update=dict(requested_targets=request.requested_targets * 2))
        )
    result = derive(s)
    with pytest.raises(ValueError):
        reparse(result.model_copy(update=dict(rows=result.rows * 2)))


@pytest.mark.parametrize("case", ["command", "declaration", "term", "amount"])
def test_deep_constructed_children_are_reparsed(case):
    s = subject()
    if case in {"command", "declaration"}:
        old = s.source.preferences.declarations[0]
        forged = old.model_copy(
            update=dict(command=old.command.model_copy(update=dict(value="DISLIKE")))
        )
        if case == "declaration":
            forged = old.model_copy(update=dict(command_fingerprint="0" * 64))
        source = s.source.model_copy(
            update=dict(
                preferences=s.source.preferences.model_copy(update=dict(declarations=(forged,)))
            )
        )
        s = s.model_copy(update=dict(source=source))
    if case == "term":
        t = term()
        first = declaration(command(target=dict(kind=t.kind, feature_term_id=t.id)))
        s = subject((first,), terms=(t,), entries=(entry(first.command.target, identity=t),))
        source = s.source.model_copy(
            update=dict(
                preferences=s.source.preferences.model_copy(
                    update=dict(feature_terms=(t.model_copy(update=dict(status="DRAFT")),))
                )
            )
        )
        s = s.model_copy(update=dict(source=source))
    if case == "amount":
        p = s.policy.target_policies[0]
        rule = p.affinity_rules[0]
        bad = rule.model_copy(
            update=dict(amount=rule.amount.model_copy(update=dict(denominator=True)))
        )
        p = p.model_copy(update=dict(affinity_rules=(bad, *p.affinity_rules[1:])))
        s = s.model_copy(
            update=dict(
                policy=s.policy.model_copy(
                    update=dict(target_policies=(p, *s.policy.target_policies[1:]))
                )
            )
        )
    with pytest.raises(ValueError):
        derive(s)


def test_nonzero_neutral_asymmetric_coordinates_are_not_replaced_by_defaults():
    data = policy().model_dump()
    for p in data["target_policies"]:
        for r in p["affinity_rules"]:
            r["amount"] = dict(
                numerator={"DISLIKE": -1, "NEUTRAL": 1, "LIKE": 2}[r["value"]], denominator=3
            )
    p = c.ExplicitTargetAffinityPolicy(**data)
    row = derive(subject((declaration(command(value="NEUTRAL")),), interpretation=p)).rows[0]
    assert (row.affinity.amount.numerator, row.affinity.amount.denominator) == (1, 3)
    assert row.evidence_strength.level == "LOW"


def test_requested_feature_provenance_must_precede_capture_completion():
    t = term()
    target = c.FeaturePreferenceTarget(kind=t.kind, feature_term_id=t.id)
    s = subject((), targets=(target,), entries=(entry(target, identity=t),))
    future = t.model_copy(
        update=dict(
            provenance=t.provenance.model_copy(
                update=dict(observed_at=s.source.capture_completed_at + timedelta(seconds=1))
            )
        )
    )
    forged = s.source.manifest.model_copy(
        update=dict(entries=(c.FeatureTargetManifestEntry(kind=t.kind, identity=future),))
    )
    with pytest.raises(ValueError, match="Future feature"):
        derive(s.model_copy(update=dict(source=s.source.model_copy(update=dict(manifest=forged)))))
