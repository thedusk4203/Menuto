"""Canonical NRE ingress. No HTTP endpoints, publications, source writes or numeric policy."""

from dataclasses import dataclass
from threading import Timer
from time import monotonic

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.catalog.public import capture_resolution_catalog
from app.modules.households.public import capture_resolution_member
from app.modules.nutrition import root_public
from app.modules.nutrition.resolution_contracts import (
    NreCaptureFrame,
    NreFixtureFact,
    NreOwnerAbsence,
    NreRecipeSeal,
    NutritionResolutionScopeRequestV1,
    NutritionResolutionScopeV1,
    NutritionResolutionSourcesV1,
    resolution_hash,
)
from app.modules.nutrition.resolution_limits import (
    DEADLINE_SECONDS,
    REQUEST_BYTES,
    ingest,
    structure,
)
from app.modules.nutrition.synthesis import nutrition_policy_requirements
from app.modules.nutrition.synthesis_contracts import NutritionSynthesisRequest
from app.modules.nutrition.synthesis_sources import capture_nutrition_synthesis_sources
from app.modules.recipes.public import capture_resolution_recipes

READ_RELATIONS = (
    "households",
    "household_members",
    "ingredients",
    "memberships",
    "nutrition_facts",
    "preparation_transformations",
    "recipe_combination_members",
    "recipe_ingredients",
    "recipe_portion_tiers",
    "recipe_rule_combinations",
    "recipe_tier_quantities",
    "recipe_variant_rules",
    "recipe_version_seals",
    "recipe_versions",
    "recipes",
)
_CONTEXT_SEAL = object()


@dataclass(frozen=True, slots=True, init=False)
class NutritionResolutionCaptureContext:
    """Trusted deployment dependency, never a request/JSON bearer credential.

    Local Python is trusted, not a hostile-code sandbox. Only isolated TEST_ONLY
    deployment setup supplies the manifest; it is not loaded from an ordinary request.
    Actual actor/reader authority is still reconstructed by PostgreSQL, not this context.
    """

    database_oid: int
    database_name: str
    manifest: tuple
    seal: object

    def __init__(self, database_oid, database_name, manifest, *, _seal=None):
        if _seal is not _CONTEXT_SEAL:
            raise TypeError("Server-owned isolated TEST_ONLY context required")
        object.__setattr__(self, "database_oid", database_oid)
        object.__setattr__(self, "database_name", database_name)
        object.__setattr__(self, "manifest", tuple(manifest))
        object.__setattr__(self, "seal", _seal)


def _configure_isolated_test_capture(database_oid, database_name, fixture_manifest):
    """Internal trusted test/deployment bootstrap; no runtime publication or enrollment."""
    if (
        type(database_oid) is not int
        or database_oid <= 0
        or not database_name.startswith("nrc_test_")
    ):
        raise ValueError("ENVIRONMENT_MISMATCH: isolated test database required")
    manifest = tuple(NreFixtureFact.model_validate(ingest(x)) for x in fixture_manifest)
    keys = [(x.owner, str(x.identity)) for x in manifest]
    if keys != sorted(set(keys)):
        raise ValueError("ENVIRONMENT_MISMATCH: complete sorted fixture manifest required")
    return NutritionResolutionCaptureContext(
        database_oid, database_name, manifest, _seal=_CONTEXT_SEAL
    )


def capture_nutrition_resolution_sources(session, authenticated_context, scope):
    """All-or-error owner reads on one actual caller-owned read-only transaction."""
    started = monotonic()
    ctx = authenticated_context
    if type(ctx) is not NutritionResolutionCaptureContext or ctx.seal is not _CONTEXT_SEAL:
        raise PermissionError("ENVIRONMENT_MISMATCH: trusted capture context required")
    # A clean identity map is necessary: ORM get()/relationship reads can otherwise
    # reuse objects from a previous transaction. One Session also need not mean one
    # connection when mapper binds/custom routing are configured. This V1 adapter
    # supports only the ordinary, single-Engine Session shape proved by PG tests.
    # Pinned SQLAlchemy 2.1 exposes the mapper-bind map; unsupported shapes fail closed.
    if (
        not isinstance(session, Session)
        or getattr(session.get_bind, "__func__", None) is not Session.get_bind
        or getattr(session, "binds", None) != {}
        or not hasattr(session.bind, "url")
        or session.identity_map
        or session.new
        or session.dirty
        or session.deleted
    ):
        raise ValueError("SOURCE_CUT_UNSUPPORTED: one clean actual Session required")
    request_scope = NutritionResolutionScopeRequestV1.model_validate(ingest(scope, REQUEST_BYTES))
    scope = request_scope
    if (
        scope.subject != scope.root_request.subject
        or scope.subject != scope.precision.subject
        or scope.actor_user_id != scope.precision.actor_user_id
    ):
        raise PermissionError("AUTHORIZATION_DENIED: subject/request binding")
    for slot in scope.slots:
        for declaration in slot.alternatives:
            if (
                declaration.subject != scope.subject
                or declaration.actor_user_id != scope.actor_user_id
                or declaration.slot_id != slot.slot_id
            ):
                raise PermissionError("AUTHORIZATION_DENIED: serving subject/slot binding")
    connection = session.connection()
    if (
        connection.dialect.name != "postgresql"
        or connection.get_isolation_level() not in {"REPEATABLE READ", "SERIALIZABLE"}
        or session.scalar(text("SHOW transaction_read_only")) != "on"
    ):
        raise ValueError("SOURCE_CUT_UNSUPPORTED: read-only repeatable snapshot required")
    database = session.execute(
        text("SELECT oid,datname FROM pg_catalog.pg_database WHERE datname=current_database()")
    ).one()
    if (database.oid, database.datname) != (ctx.database_oid, ctx.database_name):
        raise PermissionError("ENVIRONMENT_MISMATCH: fixture endpoint/database binding")
    began = session.scalar(text("SELECT clock_timestamp()"))
    old_path = session.scalar(text("SHOW search_path"))
    old_timeout = session.scalar(text("SHOW statement_timeout"))
    watchdog = Timer(DEADLINE_SECONDS, connection.connection.driver_connection.cancel)
    watchdog.daemon = True
    watchdog.start()
    try:
        if monotonic() - started > DEADLINE_SECONDS:
            raise ValueError("RESOURCE_EXCEEDED: capture deadline")
        session.execute(
            text("SELECT pg_catalog.set_config('search_path',:p,true)"),
            {"p": "pg_catalog,public,pg_temp"},
        )
        session.execute(text("SELECT pg_catalog.set_config('statement_timeout','15000',true)"))
        if session.scalar(text("SELECT has_schema_privilege(session_user,'public','CREATE')")):
            raise PermissionError("AUTHORIZATION_DENIED: writable owner schema")
        # Frozen SQL reconstructs SCRAM/login/database/OIDs and verifies privilege graphs.
        root_sources = root_public.capture_nutrition_root_sources(session, scope.root_request)
        root = root_public.resolve_nutrition_root(root_sources)
        request = NutritionSynthesisRequest(
            root=root,
            selection=scope.selection,
            precision=scope.precision,
            purpose="BOUNDED_COMPLETE_POLICY_V1",
            required_claims=(),
        )
        synthesis = capture_nutrition_synthesis_sources(session, request)
        principal = next(
            p for p in synthesis.principal_facts if p.id == synthesis.frame.reader_principal_id
        )
        if (
            principal.command.verified_human_id is None
            or principal.command.service_id is not None
            or principal.command.user_id != scope.actor_user_id
        ):
            raise PermissionError("AUTHORIZATION_DENIED: exact enrolled human request actor")
        witness = capture_resolution_member(
            session, scope.subject.household_id, scope.subject.member_id, scope.actor_user_id
        )
        requirements = nutrition_policy_requirements(synthesis)
        # Root/result identity includes capture identity. Pin the fresh requirement
        # here, never ask a caller to predict a future capture's fingerprint.
        scope = NutritionResolutionScopeV1.model_validate(
            request_scope.model_dump()
            | {
                "contract_version": "nutrition-resolution-scope.v1",
                "requirement_fingerprint": requirements.fingerprint,
            }
        )
        recipes, seals, missing, row_count = capture_resolution_recipes(
            session, tuple(x.recipe_version_id for x in scope.recipes), row_budget=8192 - 3
        )
        for slot in scope.slots:
            for declaration in slot.alternatives:
                recipe = next((r for r in recipes if r.id == declaration.recipe_version_id), None)
                if (
                    recipe is not None
                    and declaration.serving_definition != recipe.serving_definition
                ):
                    raise ValueError(
                        "SERVING_MAPPING_UNSUPPORTED: exact authored serving definition"
                    )
        ingredient_ids = set()
        for selection in scope.recipes:
            recipe = next((r for r in recipes if r.id == selection.recipe_version_id), None)
            if recipe is None:
                continue
            rules = {r.id: r for r in recipe.variant_rules}
            for selected in selection.rule_selections:
                replacements = {
                    rules[r].requirement_id: rules[r].replacement_ingredient_id
                    for r in selected
                    if r in rules
                }
                ingredient_ids.update(
                    replacements.get(i.id, i.ingredient_id) for i in recipe.ingredients
                )
        ingredients, references = capture_resolution_catalog(
            session, ingredient_ids, row_budget=8192 - row_count - 3
        )
        row_count += len(ingredients) + len(references) + 3
        absences = [
            NreOwnerAbsence(owner="Recipes", identity=str(i), reason="VERSION_MISSING")
            for i in missing
        ]
        for selection in scope.recipes:
            recipe = next((r for r in recipes if r.id == selection.recipe_version_id), None)
            if recipe is not None:
                for identity in set(selection.tier_ids) - {t.id for t in recipe.portion_tiers}:
                    absences.append(
                        NreOwnerAbsence(
                            owner="Recipes", identity=str(identity), reason="TIER_MISSING"
                        )
                    )
                for identity in {i for ids in selection.rule_selections for i in ids} - {
                    r.id for r in recipe.variant_rules
                }:
                    absences.append(
                        NreOwnerAbsence(
                            owner="Recipes", identity=str(identity), reason="RULE_MISSING"
                        )
                    )
        absences += [
            NreOwnerAbsence(owner="Catalog", identity=str(i), reason="INGREDIENT_MISSING")
            for i in sorted(ingredient_ids - {i.id for i in ingredients}, key=str)
        ]
        for identity in {r.reference_id for r in scope.references} - {r.id for r in references}:
            absences.append(
                NreOwnerAbsence(owner="Catalog", identity=str(identity), reason="REFERENCE_MISSING")
            )
        for identity in {
            m.identity
            for m in ctx.manifest
            if m.owner == "Reference" and m.ingredient_id in ingredient_ids
        } - {r.id for r in references}:
            absences.append(
                NreOwnerAbsence(
                    owner="Catalog", identity=str(identity), reason="REFERENCE_COVERAGE_MISSING"
                )
            )
        if not witness[3]:
            absences.append(
                NreOwnerAbsence(
                    owner="Households",
                    identity=str(scope.subject.member_id),
                    reason="MEMBER_MISSING",
                )
            )
        expected = {(m.owner, m.identity): m for m in ctx.manifest}
        for owner, rows in (
            ("Recipe", recipes),
            ("Ingredient", ingredients),
            ("Reference", references),
        ):
            for item in rows:
                fixture = expected.get((owner, item.id))
                if fixture is None or fixture.body_fingerprint != resolution_hash("fixture", item):
                    raise PermissionError("ENVIRONMENT_MISMATCH: unclassified/changed fixture row")
        if monotonic() - started > DEADLINE_SECONDS:
            raise ValueError("RESOURCE_EXCEEDED: capture deadline")
        frame = NreCaptureFrame(
            source_frame=synthesis.frame,
            actor_user_id=scope.actor_user_id,
            subject=scope.subject,
            membership_id=witness[0],
            member_id=witness[1],
            membership_role=witness[2],
            started_at=began,
            completed_at=session.scalar(text("SELECT clock_timestamp()")),
            owner_row_count=row_count,
            owner_relations=READ_RELATIONS,
            fixture_database_oid=ctx.database_oid,
            fixture_database_name=ctx.database_name,
            fixture_food_fingerprint=resolution_hash("fixture-manifest", ctx.manifest),
            fixture_manifest=ctx.manifest,
        )
        data = dict(
            scope=scope,
            synthesis_sources=synthesis,
            requirements=requirements,
            recipes=recipes,
            recipe_seals=tuple(
                NreRecipeSeal(
                    recipe_version_id=i, sealed=True, body_fingerprint=resolution_hash("recipe", r)
                )
                for i in seals
                for r in recipes
                if r.id == i
            ),
            ingredients=ingredients,
            references=references,
            absences=tuple(sorted(absences, key=lambda x: (x.owner, x.identity, x.reason))),
            frame=frame,
        )
        data["contract_version"] = "nutrition-resolution-sources.v1"
        structure(data)
        return NutritionResolutionSourcesV1(
            **data, source_fingerprint=resolution_hash("sources", data)
        )
    finally:
        watchdog.cancel()
        watchdog.join()
        # Never commit/rollback or change isolation. A failed statement leaves transaction
        # recovery with its owner; don't mask it by issuing SQL in an aborted transaction.
        raw = connection.connection.driver_connection
        if raw.info.transaction_status.name != "INERROR":
            session.execute(
                text("SELECT pg_catalog.set_config('search_path',:p,true)"), {"p": old_path}
            )
            session.execute(
                text("SELECT pg_catalog.set_config('statement_timeout',:p,true)"),
                {"p": old_timeout},
            )
