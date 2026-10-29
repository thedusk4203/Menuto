"""SMTF01–36: actual PostgreSQL source paths and independent cohort obligations."""

from fractions import Fraction
from uuid import uuid4

import pytest
from app.domain.feature_identity import canonical
from app.domain.resolution import ResolutionError
from app.modules.identity.models import User
from app.modules.planning import shared_target_tastefit_capture as adapter
from app.modules.planning import shared_target_tastefit_contracts as c
from app.modules.planning.shared_target_tastefit_public import (
    capture_shared_member_target_tastefit_sources as capture_sources,
)
from app.modules.planning.shared_target_tastefit_public import (
    derive_shared_member_target_tastefit as derive,
)
from app.modules.planning.shared_target_tastefit_public import (
    validate_shared_member_target_tastefit as validate,
)
from app.modules.planning.tastefit_contracts import TasteFitInterpretationPolicy
from shared_target_tastefit_fixtures import pack
from shared_target_tastefit_postgres_fixtures import (
    author_for_members,
    child_results,
    declare_for,
    group,
    prepared_group,
    root_request,
    shared_capture,
)
from sqlalchemy import event, inspect, text
from sqlalchemy.orm import Session
from tastefit_fixtures import fit_policy, interpretation, request
from tastefit_postgres_fixtures import (
    capture,
    configure_exact,
    configure_hierarchy,
    prepare,
    publish_prior,
    sessions,
)
from tastefit_postgres_fixtures import hierarchy_server as hierarchy_server
from tastefit_postgres_fixtures import tastefit_server as tastefit_server
from test_postgres_candidate_feature_projection import clear_method
from test_postgres_candidate_member_tastefit import rebind_grounding

pytestmark = pytest.mark.postgres


def fails(operation, code=None):
    with pytest.raises(ResolutionError) as caught:
        operation()
    if code:
        assert caught.value.code == code, caught.value.detail
    return caught.value


def withheld(r):
    assert r.value is r.weight_total is r.weighted_total is None
    assert r.aggregate_availability == "UNAVAILABLE"
    assert all(v.common_operand is v.weighted_contribution is None for v in r.contributions)


def assert_exact(s):
    source = shared_capture(s)
    r = derive(source)
    assert validate(r) == r and r.sources == source
    assert r.coverage.required_count == len(s["ids"])
    assert r.coverage.numeric_coverage == "COMPLETE"
    products = [
        Fraction(v.authored_weight.weight.numerator, v.authored_weight.weight.denominator)
        * Fraction(
            v.selected_bridge.mapped_amount.numerator, v.selected_bridge.mapped_amount.denominator
        )
        for v in r.contributions
    ]
    weights = [
        Fraction(v.weight.numerator, v.weight.denominator)
        for v in source.request.policy.member_weights
    ]
    assert Fraction(r.value.amount.numerator, r.value.amount.denominator) == sum(products) / sum(
        weights
    )
    assert {v.diagnostic.member_id for v in r.contributions} == set(s["ids"])
    return r


def test_smtf01_actual_ingredient_cohort_distinct_member_declarations(tastefit_server):
    r = assert_exact(prepared_group(tastefit_server, kind="INGREDIENT"))
    assert all(v.diagnostic.row.proof.requirement_ids for v in r.contributions)
    assert len({s.declaration_id for s in r.direct_signals}) == 2


def test_smtf02_actual_recipe_version_source_and_path(tastefit_server):
    r = assert_exact(prepared_group(tastefit_server, kind="DIRECT_RECIPE"))
    assert r.coordinate.target.recipe_id == r.coordinate.binding.recipe_id
    assert (
        r.coordinate.binding.recipe_version_id
        == r.sources.children[0].sources.projection.source.feature_input.recipe.id
    )
    assert (
        r.coordinate.binding.recipe_source_hash
        == r.sources.children[
            0
        ].sources.projection.source.grounded_candidate.request.candidate.recipe_source_hash
    )


def test_smtf03_actual_reviewed_main_protein_support(tastefit_server):
    r = assert_exact(prepared_group(tastefit_server))
    for v in r.contributions:
        assert v.diagnostic.row.proof.dimension.dimension == "MAIN_PROTEIN"
        assert v.diagnostic.row.proof.term_resolution.state == "PRESENT"
    assert r.sources.children[0].sources.projection.source.feature_input.sources.catalog_streams


def test_smtf04_actual_method_version_wide_child_and_outer_path(tastefit_server):
    r = assert_exact(prepared_group(tastefit_server, kind="METHOD", dimensions=("METHOD",)))
    assert all(ch.sources.projection.source.feature_input.path is None for ch in r.sources.children)
    assert r.coordinate.binding.path.tier_id is not None


def test_smtf05_actual_flavor_exact_path_finite_coverage(tastefit_server):
    r = assert_exact(prepared_group(tastefit_server, kind="FLAVOR"))
    assert r.contributions[0].diagnostic.row.proof.term_resolution.state == "PRESENT"
    assert all(
        ch.sources.projection.source.feature_input.path == r.coordinate.binding.path
        for ch in r.sources.children
    )


def test_smtf06_tracked_and_multiple_shared_never_copy_preferences(tastefit_server):
    s = prepared_group(tastefit_server, states=("LIKE", "UNDECLARED", "DISLIKE"))
    r = derive(shared_capture(s))
    withheld(r)
    assert r.coverage.captured_count == 3 and r.coverage.available_count == 2
    assert {v.direct_signal for v in r.direct_signals} == {
        "DECLARED_LIKE",
        "NONE",
        "DECLARED_DISLIKE",
    }


def test_smtf07_single_actual_member_not_scope_copy(tastefit_server):
    r = assert_exact(prepared_group(tastefit_server, states=("LIKE",)))
    assert r.value.coordinate != r.contributions[0].original_value.coordinate
    assert r.weight_total.numerator == 2 and r.value.amount.numerator == 2


def test_smtf08_denied_actor_before_preference_reads(tastefit_server):
    s = prepared_group(tastefit_server)
    seen = []

    def observe(conn, cursor, sql, *args):
        seen.append(sql)

    engine = s["engines"]["root"]
    event.listen(engine, "before_cursor_execute", observe)
    try:
        with sessions(s) as cuts:
            fails(
                lambda: capture_sources(cuts, root_request(s), actor_user_id=uuid4()),
                "CAPTURE_ACCESS_DENIED",
            )
    finally:
        event.remove(engine, "before_cursor_execute", observe)
    assert not any("member_preference_declarations" in sql for sql in seen)


def test_smtf09_foreign_member_not_local_participant(tastefit_server):
    a, b = prepared_group(tastefit_server), prepared_group(tastefit_server)
    raw = canonical(root_request(a))
    raw["members"][0]["member_id"] = str(b["ids"][0])
    with sessions(a) as cuts:
        fails(
            lambda: capture_sources(cuts, raw, actor_user_id=a["actor"]), "PARTICIPANT_SET_MISMATCH"
        )


def test_smtf10_nonexistent_member_cannot_be_empty_preference(tastefit_server):
    s = prepared_group(tastefit_server)
    raw = canonical(root_request(s))
    old, new = raw["members"][0]["member_id"], str(uuid4())
    for member in raw["members"]:
        if member["member_id"] == old:
            member["member_id"] = new
    for p in raw["projection_request"]["grounding_request"]["participants"]["participants"]:
        if p["member_id"] == old:
            p["member_id"] = new
    for w in raw["policy"]["member_weights"]:
        if w["member_id"] == old:
            w["member_id"] = new
    p = c.SharedMemberTargetTasteFitPolicy.model_validate(raw["policy"])
    raw["expected_policy_fingerprint"] = p.fingerprint()
    with sessions(s) as cuts:
        fails(
            lambda: capture_sources(cuts, raw, actor_user_id=s["actor"]),
            "MEMBER_SOURCE_UNAVAILABLE",
        )


@pytest.mark.parametrize("mode", ["dirty", "writable", "read_committed"])
def test_smtf11_invalid_caller_transaction_rejected_unchanged(tastefit_server, mode):
    s = prepared_group(tastefit_server)
    with sessions(
        s,
        readonly=mode != "writable",
        isolation="READ COMMITTED" if mode == "read_committed" else "REPEATABLE READ",
    ) as cuts:
        if mode == "dirty":
            cuts["member"].add(User(display_name="Unflushed caller test object"))
        fails(
            lambda: capture_sources(cuts, root_request(s), actor_user_id=s["actor"]),
            "MEMBER_SOURCE_UNAVAILABLE",
        )
        assert bool(cuts["member"].new) == (mode == "dirty")


def test_smtf12_actual_serializable_read_only_capture(tastefit_server):
    s = prepared_group(tastefit_server)
    r = derive(shared_capture(s, isolation="SERIALIZABLE"))
    assert r.value is not None
    assert {f.isolation for _, frames in r.sources.owner_frames for f in frames} == {"SERIALIZABLE"}


def test_smtf13_primary_rr_cut_during_actual_concurrent_correction(tastefit_server, monkeypatch):
    s = prepared_group(tastefit_server, states=("LIKE", "UNDECLARED"))
    original, calls = adapter.capture_candidate_member_tastefit_sources, []

    def capture_then_correct(cuts, q, **kw):
        result = original(cuts, q, **kw)
        calls.append(q.member_id)
        if len(calls) == 1:
            declare_for(s, s["ids"][1], s["target"], value="LIKE")
        return result

    monkeypatch.setattr(adapter, "capture_candidate_member_tastefit_sources", capture_then_correct)
    old = shared_capture(s)
    monkeypatch.setattr(adapter, "capture_candidate_member_tastefit_sources", original)
    withheld(derive(old))
    assert derive(shared_capture(s)).value is not None
    assert validate(derive(old)).sources == old


def test_smtf14_actual_wrong_database_oid_not_same_label(tastefit_server):
    import psycopg
    from sqlalchemy import create_engine

    s = author_for_members(
        group(configure_exact(prepare(tastefit_server)), states=("LIKE", "LIKE"))
    )
    maintenance = s["engines"]["root"].execution_options(isolation_level="AUTOCOMMIT")
    name, wrong = "shared_wrong_" + uuid4().hex, None
    try:
        with maintenance.connect() as db:
            db.execute(text('CREATE DATABASE "' + name + '"'))
        # Same configured URL/name labels, but an actual connection to another DB.
        actual = s["parsed"].set(database=name, drivername="postgresql")
        wrong = create_engine(
            s["engines"]["root"].url,
            creator=lambda: psycopg.connect(actual.render_as_string(hide_password=False)),
        )
        assert wrong.url.database == s["engines"]["root"].url.database
        with (
            sessions(s, prior=True) as cuts,
            Session(
                wrong.execution_options(isolation_level="REPEATABLE READ", postgresql_readonly=True)
            ) as other,
        ):
            assert other.scalar(text("SELECT current_database()")) == name
            other_oid = other.scalar(
                text("SELECT oid FROM pg_database WHERE datname=current_database()")
            )
            with s["engines"]["root"].connect() as db:
                assert other_oid != db.scalar(
                    text("SELECT oid FROM pg_database WHERE datname=current_database()")
                )
            observed = []

            def observe(conn, cursor, sql, *args):
                observed.append(sql)

            event.listen(wrong, "before_cursor_execute", observe)
            cuts["prior"] = other
            try:
                fails(
                    lambda: capture_sources(cuts, root_request(s), actor_user_id=s["actor"]),
                    "MEMBER_SOURCE_UNAVAILABLE",
                )
            finally:
                event.remove(wrong, "before_cursor_execute", observe)
            assert not any("menuto_prior." in sql for sql in observed)
    finally:
        if wrong:
            wrong.dispose()
        with maintenance.connect() as db:
            db.execute(text('DROP DATABASE "' + name + '" WITH (FORCE)'))


def test_smtf15_actual_denied_prior_reader_aborts(tastefit_server):
    s = author_for_members(
        group(configure_exact(prepare(tastefit_server)), states=("LIKE", "LIKE"))
    )
    with (
        sessions(s, prior=True) as cuts,
        Session(
            s["engines"]["reader"].execution_options(
                isolation_level="REPEATABLE READ", postgresql_readonly=True
            )
        ) as other,
    ):
        cuts["prior"] = other
        error = fails(
            lambda: capture_sources(cuts, root_request(s), actor_user_id=s["actor"]),
            "MEMBER_SOURCE_UNAVAILABLE",
        )
        assert "MEMBER_CHILD_CAPTURE" in error.detail


def test_smtf16_prior_cannot_supply_hierarchy_capability(tastefit_server):
    s = author_for_members(
        group(configure_hierarchy(prepare(tastefit_server)), states=("LIKE", "LIKE"))
    )
    with sessions(s, prior=True, hierarchy=True) as cuts:
        cuts["hierarchy"] = cuts["prior"]
        fails(
            lambda: capture_sources(cuts, root_request(s), actor_user_id=s["actor"]),
            "MEMBER_SOURCE_UNAVAILABLE",
        )


def test_smtf17_actual_declared_and_prior_only_modes(tastefit_server):
    s = group(
        configure_exact(prepare(tastefit_server), declared="RAW_EXPLICIT"),
        states=("LIKE", "UNDECLARED"),
    )
    publish_prior(s)
    s = author_for_members(s)
    r = assert_exact(s)
    assert {v.diagnostic.row.selected_mode for v in r.contributions} == {
        "RAW_EXPLICIT",
        "PRIOR_ONLY",
    }
    assert sum(signal.direct_signal == "NONE" for signal in r.direct_signals) == 1


def test_smtf18_actual_one_hop_mapped_explicit_no_strength_propagation(tastefit_server):
    s = group(configure_hierarchy(prepare(tastefit_server)))
    for mid in s["ids"]:
        declare_for(s, mid, s["parent_target"], value="LIKE")
    s = author_for_members(s)
    r = assert_exact(s)
    assert all(v.diagnostic.row.selected_mode == "ONE_HOP_INHERITED" for v in r.contributions)
    assert all(v.diagnostic.row.evidence_strength.level == "NONE" for v in r.contributions)
    assert not r.direct_dislikes


def test_smtf19_full_protected_journal_retains_hidden_publications(tastefit_server):
    s = group(configure_exact(prepare(tastefit_server)))
    publication = publish_prior(s)
    s = author_for_members(s)
    before = shared_capture(s)
    # Another exact target publication is retained even when not numerically selected.
    ingredient = next(
        e.target
        for e in capture(s, prior=True).member_sources.entries
        if e.target.kind == "INGREDIENT"
    )
    hidden = publish_prior(s, target=ingredient)
    s = author_for_members(s)
    r = derive(shared_capture(s))
    for ch in r.sources.children:
        entry = next(e for e in ch.sources.member_sources.entries if e.exact_target)
        ids = {p.id for p in entry.exact_target.reference_source.publications}
        assert publication.publication.id in ids and hidden.publication.id in ids
    assert r.coordinate.retained_cohort_fingerprint == r.sources.fingerprint
    assert derive(before).value.amount == r.value.amount
    assert before.fingerprint != r.sources.fingerprint
    # Identical visible target values cannot license spliced protected journals.
    mixed = pack((before.children[0], r.sources.children[1]), s["target"], r.sources.request.policy)
    fails(lambda: derive(mixed), "SOURCE_CUT_INCOHERENT")


def test_smtf20_actual_pre_post_review_cuts_cannot_splice(tastefit_server):
    s = prepared_group(tastefit_server, kind="METHOD")
    before = child_results(s)
    clear_method(s["engines"]["root"], s["actor"], s["publications"]["METHOD"])
    after = child_results(s)
    mixed = pack((before[0], after[1]), s["target"], root_request(s).policy)
    fails(lambda: derive(mixed), "SOURCE_CUT_INCOHERENT")


def kill_after_first(s, monkeypatch, owner):
    original, captured = adapter.capture_candidate_member_tastefit_sources, []

    def actual_capture_then_fault(cuts, q, **kw):
        source = original(cuts, q, **kw)
        captured.append(source)
        if len(captured) == 1:
            pid = cuts[owner].scalar(text("SELECT pg_backend_pid()"))
            with (
                s["engines"]["root"].connect().execution_options(isolation_level="AUTOCOMMIT") as db
            ):
                assert db.scalar(text("SELECT pg_terminate_backend(:pid)"), dict(pid=pid))
        return source

    monkeypatch.setattr(
        adapter, "capture_candidate_member_tastefit_sources", actual_capture_then_fault
    )
    return original, captured


def test_smtf21_actual_later_member_connection_failure_aborts_whole_capture(
    tastefit_server, monkeypatch
):
    s = prepared_group(tastefit_server)
    _, captured = kill_after_first(s, monkeypatch, "member")
    error = fails(lambda: shared_capture(s), "MEMBER_SOURCE_UNAVAILABLE")
    assert len(captured) == 1 and "MEMBER_CHILD_CAPTURE" in error.detail
    assert str(sorted(s["ids"], key=str)[1]) in error.detail


@pytest.mark.parametrize("owner", ["prior", "hierarchy"])
def test_smtf22_actual_required_protected_db_failure_after_partial_read(
    tastefit_server, monkeypatch, owner
):
    s = author_for_members(
        group(configure_hierarchy(prepare(tastefit_server)), states=("LIKE", "LIKE"))
    )
    _, captured = kill_after_first(s, monkeypatch, owner)
    fails(lambda: shared_capture(s), "MEMBER_SOURCE_UNAVAILABLE")
    assert len(captured) == 1


def test_smtf23_correction_fresh_trace_old_cohort_historical_replay(tastefit_server):
    s = group(prepare(tastefit_server))
    old = declare_for(s, s["ids"][0], s["target"], value="LIKE")
    declare_for(s, s["ids"][1], s["target"], value="LIKE")
    before = shared_capture(s)
    declare_for(s, s["ids"][0], s["target"], value="DISLIKE", old=old)
    after = shared_capture(s)
    assert derive(before).value.amount != derive(after).value.amount
    assert before.fingerprint != after.fingerprint
    assert validate(derive(before)).sources == before
    assert derive(after).direct_dislikes[0].member_id == s["ids"][0]


def test_smtf24_current_retraction_withholds_no_resurrection(tastefit_server):
    s = group(prepare(tastefit_server))
    old = declare_for(s, s["ids"][0], s["target"], value="LIKE")
    declare_for(s, s["ids"][1], s["target"], value="LIKE")
    declare_for(s, s["ids"][0], s["target"], old=old, retract=True)
    r = derive(shared_capture(s))
    withheld(r)
    assert "MEMBER_RETRACTED" in r.reasons and not r.direct_dislikes


def different_policy(s, *, unmapped=False):
    q = s["requests"][1]
    body = q.policy.model_dump()
    body["policy_id"] = "synthetic.other.member"
    for kind_policy in body["kind_policies"]:
        if kind_policy["target_kind"] == s["target"].kind:
            if unmapped:
                kind_policy["mappings"] = [
                    r for r in kind_policy["mappings"] if r["semantic_state"] != "DISLIKE"
                ]
            else:
                for row in kind_policy["mappings"]:
                    if row["semantic_state"] == "DISLIKE":
                        row["fit_amount"] = dict(numerator=-1, denominator=4)
    policy = TasteFitInterpretationPolicy.model_validate(body)
    changed = request(
        q.projection_request,
        q.member_interpretation,
        policy,
        member_id=q.member_id,
        probes=q.diagnostic_targets,
    )
    return dict(s, requests=(s["requests"][0], changed))


def test_smtf25_actual_unmapped_dislike_remains_visible(tastefit_server):
    r = derive(shared_capture(different_policy(prepared_group(tastefit_server), unmapped=True)))
    withheld(r)
    assert len(r.direct_dislikes) == 1 and "CHILD_FIT_UNMAPPED" in r.reasons


def test_smtf26_real_neutral_available_zero(tastefit_server):
    r = assert_exact(prepared_group(tastefit_server, states=("NEUTRAL", "NEUTRAL")))
    assert (r.value.amount.numerator, r.value.amount.denominator) == (0, 1)
    assert {s.direct_signal for s in r.direct_signals} == {"DECLARED_NEUTRAL"}


def test_smtf27_undeclared_diner_not_omitted_or_zero(tastefit_server):
    r = derive(shared_capture(prepared_group(tastefit_server, states=("LIKE", "UNDECLARED"))))
    withheld(r)
    assert r.coverage.required_count == 2 and r.coverage.available_count == 1
    assert "MEMBER_UNDECLARED" in r.reasons


def test_smtf28_actual_known_absence_and_nonexistent_target(tastefit_server):
    from app.modules.preferences.contracts import IngredientPreferenceTarget
    from tastefit_postgres_fixtures import add_parent

    s = prepared_group(tastefit_server, kind="INGREDIENT")
    target = IngredientPreferenceTarget.model_validate(add_parent(s))
    s = dict(s, target=target)
    r = derive(shared_capture(s))
    withheld(r)
    assert "CANDIDATE_TARGET_ABSENT" in r.reasons
    assert all(v.diagnostic.row.proof.role == "DIAGNOSTIC_ONLY" for v in r.contributions)
    s = dict(s, target=target.model_copy(update=dict(ingredient_id=uuid4())))
    fails(lambda: shared_capture(s), "MEMBER_SOURCE_UNAVAILABLE")


@pytest.mark.parametrize("state", ["partial", "reviewed_none", "uncaptured"])
def test_smtf29_actual_finite_feature_missingness_not_fit(tastefit_server, state):
    s = prepared_group(
        tastefit_server,
        kind="METHOD",
        dimensions=("METHOD", "FLAVOR"),
        positives=state == "uncaptured",
        coverage="PARTIAL" if state == "partial" else "COMPLETE",
    )
    if state == "uncaptured":
        requests = tuple(
            q.model_copy(
                update=dict(
                    projection_request=q.projection_request.model_copy(
                        update=dict(requested_dimensions=("FLAVOR",))
                    )
                )
            )
            for q in s["requests"]
        )
        s = dict(s, requests=requests)
    r = derive(shared_capture(s))
    withheld(r)
    if state == "reviewed_none":
        assert all(v.diagnostic.row.proof.candidate_state == "ABSENT" for v in r.contributions)
    else:
        assert all(v.diagnostic.row.proof.candidate_state == "UNRESOLVED" for v in r.contributions)


def test_smtf30_different_actual_policies_require_own_bridges(tastefit_server):
    s = different_policy(prepared_group(tastefit_server))
    r = assert_exact(s)
    assert len(r.sources.request.policy.policy_admissions) == 2
    assert len({v.original_value.coordinate.policy_fingerprint for v in r.contributions}) == 2
    assert {v.original_value.amount.denominator for v in r.contributions} == {2, 4}


def test_smtf31_actual_unadmitted_policy_no_arithmetic(tastefit_server):
    s = prepared_group(tastefit_server)
    old_policy = root_request(s).policy
    s = different_policy(s)
    r = derive(shared_capture(s, q=root_request(s, old_policy)))
    withheld(r)
    assert "POLICY_INCOMPATIBLE" in r.reasons


def test_smtf32_full_retry_recaptures_every_actual_member(tastefit_server, monkeypatch):
    s = prepared_group(tastefit_server)
    original, captured = kill_after_first(s, monkeypatch, "member")
    fails(lambda: shared_capture(s), "MEMBER_SOURCE_UNAVAILABLE")
    old = captured[0]
    seen = []

    def count_actual(cuts, q, **kw):
        seen.append(q.member_id)
        return original(cuts, q, **kw)

    monkeypatch.setattr(adapter, "capture_candidate_member_tastefit_sources", count_actual)
    source = shared_capture(s)
    assert tuple(seen) == tuple(sorted(s["ids"], key=str))
    assert all(ch.sources.fingerprint != old.fingerprint for ch in source.children)
    assert validate(derive(source)).sources == source


def inventory(s):
    with s["engines"]["root"].connect() as db:
        names = inspect(db).get_table_names()
        return {name: db.scalar(text('SELECT count(*) FROM "' + name + '"')) for name in names}


def test_smtf33_actual_sql_read_only_no_transactions_connections_or_row_drift(
    tastefit_server, monkeypatch
):
    s = prepared_group(tastefit_server)
    before, statements, changes = inventory(s), [], []
    engine = s["engines"]["root"]

    def observe(conn, cursor, sql, *args):
        statements.append(sql.strip().split()[0].upper())

    def mutation(*args):
        changes.append(True)

    with sessions(s) as cuts:
        cuts["member"].scalar(text("SELECT 1"))
        session_ids = []
        original = adapter.capture_candidate_member_tastefit_sources

        def same_actual_session(mapping, q, **kw):
            session_ids.append(id(mapping["member"]))
            assert mapping["member"] is cuts["member"]
            return original(mapping, q, **kw)

        monkeypatch.setattr(
            adapter, "capture_candidate_member_tastefit_sources", same_actual_session
        )
        event.listen(engine, "before_cursor_execute", observe)
        for name in ("commit", "rollback", "connect"):
            event.listen(engine, name, mutation)
        try:
            source = capture_sources(cuts, root_request(s), actor_user_id=s["actor"])
        finally:
            event.remove(engine, "before_cursor_execute", observe)
            for name in ("commit", "rollback", "connect"):
                event.remove(engine, name, mutation)
        assert cuts["member"].in_transaction()
    assert statements and set(statements) <= {"SELECT", "SHOW"} and not changes
    assert len(session_ids) == len(s["ids"]) and len(set(session_ids)) == 1
    assert inventory(s) == before and derive(source).value is not None


def test_smtf34_real_schema_0015_85_zero_persistence(tastefit_server):
    s = prepared_group(tastefit_server)
    before = inventory(s)
    with s["engines"]["root"].connect() as db:
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0016"
        names = inspect(db).get_table_names()
        assert len(set(names) - {"alembic_version"}) == 98
        assert not any("shared_target_tastefit" in name for name in names)
    validate(derive(shared_capture(s)))
    assert before == inventory(s)


def test_smtf35_independent_real_frames_and_replay_after_revoke(tastefit_server):
    from app.modules.preferences.hierarchy_sources import change_hierarchy_authority

    s = author_for_members(
        group(configure_hierarchy(prepare(tastefit_server)), states=("LIKE", "LIKE"))
    )
    source = shared_capture(s)
    entry = next(e for e in source.children[0].sources.member_sources.entries if e.one_hop)
    cut = entry.one_hop.hierarchy_source
    with Session(s["engines"]["admin"]) as db:
        change_hierarchy_authority(
            db,
            dict(
                provider_id=s["hierarchy"]["provider"].id,
                principal_id=s["principals"]["reader"].id,
                capability="CAPTURE",
                action="REVOKE",
                expected_authority_generation=cut.frontier.authority_generation,
                reason="Disposable shared capture revoke",
                idempotency_key=uuid4().hex,
            ),
        )
        db.commit()
    fails(lambda: shared_capture(s), "MEMBER_SOURCE_UNAVAILABLE")
    r = validate(derive(source))
    assert (
        r.common_mvcc == "NOT_CLAIMED"
        and r.source_origin == "RETAINED_EVIDENCE_NOT_OFFLINE_ORIGIN_PROOF"
    )
    assert len({f.started_at for _, frames in source.owner_frames for f in frames}) > 2


@pytest.mark.parametrize("variation", ["history", "portion", "role", "strength"])
def test_smtf36_actual_metadata_not_extra_member_weight(tastefit_server, variation):
    from app.modules.households.contracts import MealParticipants
    from target_affinity_fixtures import policy as explicit_policy

    s = group(prepare(tastefit_server))
    first = declare_for(s, s["ids"][0], s["target"], value="LIKE")
    declare_for(s, s["ids"][1], s["target"], value="DISLIKE")
    before = derive(shared_capture(s))
    if variation == "history":
        from app.modules.preferences.public import PreferenceService

        with Session(s["engines"]["root"]) as db:
            assert PreferenceService(db, actor_user_id=s["actor"]).write(first.command) == first
            db.commit()
        corrected = declare_for(s, s["ids"][0], s["target"], value="DISLIKE", old=first)
        declare_for(s, s["ids"][0], s["target"], value="LIKE", old=corrected)
    elif variation in {"portion", "role"}:
        g = s["request"].projection_request.grounding_request
        participants = tuple(
            type(p).model_validate(
                p.model_dump()
                | (
                    dict(portion_factor="3")
                    if variation == "portion"
                    else dict(nutrition_role="SHARED" if i == 0 else "TRACKED")
                )
            )
            for i, p in enumerate(g.participants.participants)
        )
        g = g.model_copy(
            update=dict(
                participants=MealParticipants(participants=participants),
                tracked_member_id=s["ids"][1] if variation == "role" else s["ids"][0],
            )
        )
        q = rebind_grounding(s, g)
        s = dict(
            s,
            requests=tuple(
                old.model_copy(update=dict(projection_request=q.projection_request))
                for old in s["requests"]
            ),
        )
    else:
        mp = interpretation(explicit_policy(self_level="HIGH", proxy_level="LOW"))
        p = fit_policy(mp)
        s = dict(
            s,
            requests=tuple(
                request(
                    q.projection_request, mp, p, member_id=q.member_id, probes=q.diagnostic_targets
                )
                for q in s["requests"]
            ),
        )
    after = derive(shared_capture(s))
    assert after.value.amount == before.value.amount
    assert (after.weight_total.numerator, after.weight_total.denominator) == (
        before.weight_total.numerator,
        before.weight_total.denominator,
    )
    assert (after.weighted_total.numerator, after.weighted_total.denominator) == (
        before.weighted_total.numerator,
        before.weighted_total.denominator,
    )
    assert [(v.member_id, v.weight) for v in after.sources.request.policy.member_weights] == [
        (v.member_id, v.weight) for v in before.sources.request.policy.member_weights
    ]
    assert after.coordinate != before.coordinate
