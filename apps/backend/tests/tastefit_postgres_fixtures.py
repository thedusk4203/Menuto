"""Real same-database owner reads with independent prior/hierarchy SCRAM principals."""

import secrets
import time
from contextlib import ExitStack, contextmanager
from ipaddress import ip_address
from uuid import uuid4

import pytest
from app.modules.catalog.models import Ingredient
from app.modules.planning.tastefit_public import capture_candidate_member_tastefit_sources
from app.modules.preferences.public import PreferenceService
from app.modules.preferences.reference_priors import (
    change_reference_prior_authority,
    enroll_reference_prior_principal,
    register_reference_prior_provider,
)
from hierarchy_postgres_fixtures import hierarchy_server as hierarchy_server
from hierarchy_postgres_fixtures import hierarchy_source as hierarchy_source
from preference_fixtures import command
from sqlalchemy import text
from sqlalchemy.orm import Session
from tastefit_fixtures import fit_policy, interpretation, request
from test_postgres_candidate_feature_projection import prepared


class DisposableSources(dict):
    def __repr__(self):
        return "<disposable PostgreSQL source fixture>"


@pytest.fixture(scope="module")
def tastefit_server(hierarchy_server):
    s = hierarchy_server
    from app.persistence.database import create_database_engine
    from psycopg import sql

    names = {
        k: "tastefit_" + k + "_" + uuid4().hex[:12]
        for k in ("prior_admin", "prior_curator", "prior_reader")
    }
    passwords = {k: secrets.token_urlsafe(32) for k in names}
    engines = dict(s["engines"])
    original = hba_path = None

    def hba(conn, body):
        oid = conn.scalar(text("SELECT lo_from_bytea(0,convert_to(:body,'UTF8'))"), dict(body=body))
        try:
            conn.execute(
                text("SELECT lo_export(CAST(:oid AS oid),:path)"), dict(oid=oid, path=hba_path)
            )
        finally:
            conn.execute(text("SELECT lo_unlink(CAST(:oid AS oid))"), dict(oid=oid))
        conn.execute(text("SELECT pg_reload_conf()"))
        time.sleep(0.15)

    with s["engines"]["root"].connect() as conn:
        conn.execute(text("SELECT 1"))
        cur = conn.connection.driver_connection.cursor()
        cur.execute("SET password_encryption='scram-sha-256'")
        for who, name in names.items():
            cur.execute(
                sql.SQL("CREATE ROLE {} LOGIN INHERIT PASSWORD {}").format(
                    sql.Identifier(name), sql.Literal(passwords[who])
                )
            )
            cur.execute(
                sql.SQL("GRANT {} TO {}").format(
                    sql.Identifier(
                        "menuto_prior_admin" if who == "prior_admin" else "menuto_prior_client"
                    ),
                    sql.Identifier(name),
                )
            )
        cur.close()
        hba_path = conn.scalar(text("SHOW hba_file"))
        original = conn.scalar(text("SELECT pg_read_file(:path)"), dict(path=hba_path))
        addresses = {"127.0.0.1/32", "::1/128"}
        address = conn.scalar(text("SELECT host(inet_client_addr())"))
        if address:
            addresses.add(address + ("/32" if ip_address(address).version == 4 else "/128"))
        rules = [
            f"host {s['dbname']} {name} {address} scram-sha-256"
            for name in names.values()
            for address in sorted(addresses)
        ]
        hba(conn, "\n".join(rules) + "\n" + original)
        conn.commit()
    try:
        for who, name in names.items():
            engines[who] = create_database_engine(
                s["parsed"]
                .set(database=s["dbname"], username=name, password=passwords[who])
                .render_as_string(hide_password=False)
            )
        with Session(engines["prior_admin"]) as db:
            principals = {
                who: enroll_reference_prior_principal(
                    db, dict(role_name=names["prior_" + who], idempotency_key=uuid4().hex)
                )
                for who in ("curator", "reader")
            }
            db.commit()
        yield DisposableSources(
            s, engines=engines, names=s["names"] | names, prior_principals=principals
        )
    finally:
        for who in names:
            if who in engines:
                engines[who].dispose()
        with s["engines"]["root"].connect() as conn:
            conn.execute(text("SELECT 1"))
            hba(conn, original)
            # Disposable enrollment facts are immutable, but roles are independent
            # cluster principals and can be removed after all connections close.
            cur = conn.connection.driver_connection.cursor()
            for name in names.values():
                cur.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))
            cur.close()
            conn.commit()


def prepare(
    s,
    *,
    dimensions=("METHOD", "MAIN_PROTEIN", "FLAVOR"),
    empty=False,
    coverage="COMPLETE",
    positives=True,
):
    engine = s["engines"]["root"]
    actor, projection, publications, terms = prepared(
        engine, dimensions, empty=empty, coverage=coverage, positives=positives
    )
    mp = interpretation()
    q = request(projection, mp, fit_policy(mp))
    return dict(s, actor=actor, request=q, publications=publications, terms=terms)


@contextmanager
def sessions(
    s, *, prior=False, hierarchy=False, who="reader", isolation="REPEATABLE READ", readonly=True
):
    with ExitStack() as stack:
        ordinary = stack.enter_context(
            Session(
                s["engines"]["root"].execution_options(
                    isolation_level=isolation, postgresql_readonly=readonly
                )
            )
        )
        values = {"member": ordinary}
        if prior:
            values["prior"] = stack.enter_context(
                Session(
                    s["engines"]["prior_reader"].execution_options(
                        isolation_level="REPEATABLE READ", postgresql_readonly=True
                    )
                )
            )
        if hierarchy:
            values["hierarchy"] = stack.enter_context(
                Session(
                    s["engines"][who].execution_options(
                        isolation_level="REPEATABLE READ", postgresql_readonly=True
                    )
                )
            )
        yield values


def capture(s, *, q=None, actor=None, prior=False, hierarchy=False, **kw):
    with sessions(s, prior=prior, hierarchy=hierarchy, **kw) as cuts:
        return capture_candidate_member_tastefit_sources(
            cuts, q or s["request"], actor_user_id=actor or s["actor"]
        )


def declare(s, target, *, value="LIKE", old=None, retract=False, key=None, authorship="SELF"):
    from app.modules.preferences.contracts import RetractMemberPreferenceCommand

    q = command(
        household_id=s["request"].household_id,
        member_id=s["request"].member_id,
        actor_user_id=s["actor"],
        target=target,
        value=value,
        authorship=authorship,
        expected_revision=old.revision_no if old else -1,
        predecessor_id=old.id if old else None,
        idempotency_key=key or uuid4().hex,
        reason="INPUT_CORRECTION" if old else "INITIAL",
    )
    if retract:
        q = RetractMemberPreferenceCommand.model_validate(
            q.model_dump(exclude={"contract_version", "action", "value", "reason"})
        )
    with Session(s["engines"]["root"]) as db:
        receipt = PreferenceService(db, actor_user_id=s["actor"]).write(q)
        db.commit()
    return receipt


def prior_provider(s):
    with Session(s["engines"]["prior_admin"]) as db:
        provider = register_reference_prior_provider(
            db,
            dict(
                code="tastefit." + uuid4().hex,
                version="1",
                source_system="tastefit.test",
                remit="Disposable test-only source",
                idempotency_key=uuid4().hex,
            ),
        )
        generation = 0
        for who, caps in (
            ("curator", ("REVIEW_PUBLISH", "RETRACT", "CAPTURE")),
            ("reader", ("CAPTURE",)),
        ):
            for cap in caps:
                change_reference_prior_authority(
                    db,
                    dict(
                        provider_id=provider.id,
                        principal_id=s["prior_principals"][who].id,
                        capability=cap,
                        action="GRANT",
                        expected_authority_generation=generation,
                        reason="Disposable acceptance grant",
                        idempotency_key=uuid4().hex,
                    ),
                )
                generation += 1
        db.commit()
    return provider


def add_parent(s):
    with Session(s["engines"]["root"]) as db:
        ingredient = Ingredient(name="Disposable parent outside candidate")
        db.add(ingredient)
        db.commit()
        return dict(kind="INGREDIENT", ingredient_id=ingredient.id)


def configure_exact(
    s, *, kind="PROTEIN", declared="EXACT_TARGET_EFFECTIVE", undeclared="PRIOR_ONLY"
):
    from app.modules.preferences.reference_priors import capture_reference_prior_sources
    from prior_shrinkage_fixtures import compatibility, shrinkage

    initial = capture(s)
    selected = next(e for e in initial.member_sources.entries if e.target.kind == kind)
    provider = prior_provider(s)
    with sessions(s, prior=True) as cuts:
        ref = capture_reference_prior_sources(
            cuts["prior"], dict(provider_id=provider.id, requested_targets=(selected.target,))
        )
    comp = compatibility(selected.explicit, ref)
    mp = interpretation(s["request"].member_interpretation.explicit_policy, comp, shrinkage(comp))
    fit = fit_policy(
        mp,
        kinds=(kind,),
        mode="EXACT_TARGET",
        declared=declared,
        undeclared=undeclared,
        mappings={},
    )
    q = request(s["request"].projection_request, mp, fit, member_id=s["request"].member_id)
    return dict(s, request=q, prior_provider=provider, selected_target=selected.target)


def publish_prior(s, *, amount=(1, 2), old=None, retract=False, target=None):
    from datetime import UTC, datetime, timedelta

    from app.modules.preferences.reference_prior_contracts import (
        ReferencePriorPublishCommand,
        ReferencePriorRetractCommand,
    )
    from app.modules.preferences.reference_priors import (
        capture_reference_prior_sources,
        publish_reference_prior,
        retract_reference_prior,
    )

    target = target or s["selected_target"]
    with sessions(s, prior=True) as cuts:
        cut = capture_reference_prior_sources(
            cuts["prior"], dict(provider_id=s["prior_provider"].id, requested_targets=(target,))
        )
    fields = dict(
        provider_id=s["prior_provider"].id,
        target=target,
        provenance=dict(
            source_system="tastefit.test",
            external_record_id=uuid4().hex,
            source_version="1",
            content_hash="a" * 64,
            observed_at=datetime.now(UTC) - timedelta(days=1),
        ),
        review_rationale="Disposable reviewed test anchor",
        expected_provider_generation=cut.frontier.source_generation,
        expected_revision=old.publication.revision if old else -1,
        predecessor_id=old.publication.id if old else None,
        idempotency_key=uuid4().hex,
    )
    q = (
        ReferencePriorRetractCommand(**fields)
        if retract
        else ReferencePriorPublishCommand(
            **fields, amount=dict(numerator=amount[0], denominator=amount[1])
        )
    )
    with Session(s["engines"]["prior_curator"]) as db:
        receipt = retract_reference_prior(db, q) if retract else publish_reference_prior(db, q)
        db.commit()
    return receipt


def author_current_mapping(s, *, prior=False, hierarchy=False):
    from app.modules.planning import tastefit_contracts as c
    from app.modules.planning.tastefit_public import derive_candidate_member_tastefit

    source = capture(s, prior=prior, hierarchy=hierarchy)
    result = derive_candidate_member_tastefit(source)
    fit_body = s["request"].policy.model_dump()
    for group in fit_body["kind_policies"]:
        mappings = []
        for row in result.targets:
            if row.proof.target.kind != group["target_kind"] or row.source_amount is None:
                continue
            mappings.append(
                c.TasteFitMappingRow(
                    target_kind=group["target_kind"],
                    source_mode=row.selected_mode,
                    semantic_state=row.semantic_state,
                    source_coordinate=row.source_coordinate,
                    source_amount=row.source_amount,
                    fit_amount=dict(
                        numerator={"LIKE": 1, "DISLIKE": -1, "NEUTRAL": 0, "NO_DECLARATION": 1}[
                            row.semantic_state
                        ],
                        denominator=3,
                    ),
                )
            )
        group["mappings"] = mappings
    fit = c.TasteFitInterpretationPolicy.model_validate(fit_body)
    q = request(
        s["request"].projection_request,
        s["request"].member_interpretation,
        fit,
        member_id=s["request"].member_id,
        probes=s["request"].diagnostic_targets,
    )
    return dict(s, request=q)


def configure_hierarchy(
    s,
    *,
    source_kind="INGREDIENT",
    destination_kind="PROTEIN",
    declared="RAW_EXPLICIT",
    undeclared="ONE_HOP_INHERITED",
    publish_policy=True,
    publish_relation=True,
    recipe_bindings=(),
):
    from app.modules.preferences import hierarchy_contracts as h
    from app.modules.preferences.hierarchy_sources import (
        change_hierarchy_authority,
        register_hierarchy_provider,
    )
    from hierarchy_fixtures import policy as transfer
    from hierarchy_postgres_fixtures import publication, publish

    s = configure_exact(s, kind=destination_kind, declared=declared, undeclared="NO_EVIDENCE")
    mp = s["request"].member_interpretation
    body = transfer(source_kind=source_kind, destination_kind=destination_kind).model_dump()
    body.update(explicit_policy=mp.explicit_policy, compatibility_policy=mp.compatibility_policy)
    for d in body["directions"]:
        for r in d["rows"]:
            r["source_descriptor"] = mp.compatibility_policy.coordinate_for(
                d["source_kind"]
            ).model_dump()
    policy = h.HierarchyTransferPolicy.model_validate(body)
    with Session(s["engines"]["admin"]) as db:
        provider = register_hierarchy_provider(
            db,
            dict(
                code="tastefit.h." + uuid4().hex,
                version="1",
                source_system="hierarchy.test",
                remit="Disposable test source",
                idempotency_key=uuid4().hex,
            ),
        )
        gen = 0
        for who, caps in (
            ("curator", ("REVIEW_PUBLISH", "RETRACT", "CAPTURE")),
            ("reader", ("CAPTURE",)),
        ):
            for cap in caps:
                change_hierarchy_authority(
                    db,
                    dict(
                        provider_id=provider.id,
                        principal_id=s["principals"][who].id,
                        capability=cap,
                        action="GRANT",
                        expected_authority_generation=gen,
                        reason="Disposable grant",
                        idempotency_key=uuid4().hex,
                    ),
                )
                gen += 1
        db.commit()
    parent = add_parent(s)
    mp = interpretation(
        mp.explicit_policy, mp.compatibility_policy, mp.shrinkage_policy, policy, provider
    )
    fit = fit_policy(
        mp,
        kinds=(destination_kind,),
        mode="EXACT_TARGET_AND_ONE_HOP",
        declared=declared,
        undeclared=undeclared,
        mappings={},
    )
    q = request(s["request"].projection_request, mp, fit, member_id=s["request"].member_id)
    hs = dict(s, provider=provider, policy=policy, target=parent)
    policy_receipt = publish(hs, publication(hs)) if publish_policy else None
    relation_receipt = None
    if publish_relation:
        identity = dict(
            kind="RELATION",
            policy_id=policy.policy_id,
            source=parent,
            destination=s["selected_target"],
            recipe_bindings=recipe_bindings,
        )
        relation = dict(
            policy_revision_id=policy_receipt.publication.id,
            policy_fingerprint=policy.fingerprint(),
            support_mode="REVIEWED_EXACT_PAIR",
            support_review_id=None,
            catalog_review_ids=(),
        )
        relation_receipt = publish(hs, publication(hs, identity=identity, relation=relation))
    return dict(
        s,
        request=q,
        hierarchy=hs,
        parent_target=parent,
        policy_receipt=policy_receipt,
        relation_receipt=relation_receipt,
    )


def clone_recipe_version(s, *, substitution=False):
    """Publish a genuinely distinct sealed authored version, with fresh child IDs."""
    from app.modules.recipes.contracts import RecipeVersionSnapshot
    from app.modules.recipes.repository import RecipeRepository

    current = capture(s).projection.source.grounded_candidate.sources.recipe
    body = current.model_dump()
    body["provenance"]["source_version"] = str(current.version + 1)
    version_id = uuid4()
    requirement_id = uuid4()
    first = body["ingredients"][0]
    selected_ingredient = first["ingredient_id"]
    first.update(id=requirement_id, recipe_version_id=version_id)
    body.update(
        id=version_id,
        version=current.version + 1,
        transformations=[],
        variant_rules=[],
        approved_combinations=[],
    )
    for tier in body["portion_tiers"]:
        tier.update(id=uuid4(), recipe_version_id=version_id)
        for quantity in tier["quantities"]:
            quantity["requirement_id"] = requirement_id
    with Session(s["engines"]["root"]) as db:
        if substitution:
            original = Ingredient(name="Disposable substituted-away original")
            db.add(original)
            db.flush()
            first["ingredient_id"] = original.id
            body["variant_rules"] = [
                dict(
                    id=uuid4(),
                    recipe_version_id=version_id,
                    key="selected-substitution",
                    version=1,
                    requirement_id=requirement_id,
                    replacement_ingredient_id=selected_ingredient,
                    quantity_factor="1",
                    structural=True,
                    provenance=current.provenance,
                )
            ]
        new = RecipeVersionSnapshot.model_validate(body)
        RecipeRepository(db).add_version(new)
        db.commit()
    return new
