"""Internal dedicated-credential source boundary; caller owns every transaction."""

import json

from sqlalchemy import text

from app.domain.feature_identity import canonical
from app.modules.catalog.public import ingredient_identities, reviewed_affinity_feature_terms
from app.modules.preferences.reference_prior_contracts import (
    ReferencePriorAuthorityCommand,
    ReferencePriorAuthorityEvent,
    ReferencePriorCaptureRequest,
    ReferencePriorPrincipalCommand,
    ReferencePriorPrincipalFact,
    ReferencePriorProviderCommand,
    ReferencePriorProviderFact,
    ReferencePriorPublishCommand,
    ReferencePriorRetractCommand,
    ReferencePriorSourceSnapshotDraft,
    ReferencePriorTargetIdentity,
    ReferencePriorWriteReceipt,
    target_key,
)
from app.modules.recipes.public import recipe_identities


def _call(session, function, command, contract):
    # Function names are private fixed literals, never request data.
    url = session.get_bind().url
    if (
        url.host not in {"localhost", "127.0.0.1", "::1"}
        and url.query.get("sslmode") != "verify-full"
    ):
        raise ValueError("Remote reference connection requires sslmode=verify-full")
    value = session.scalar(
        text(f"SELECT menuto_prior.{function}(CAST(:command AS jsonb))"),
        {"command": json.dumps(canonical(command), ensure_ascii=False)},
    )
    return contract.model_validate(value)


def register_reference_prior_provider(session, command):
    command = ReferencePriorProviderCommand.model_validate(canonical(command))
    return _call(session, "register_provider", command, ReferencePriorProviderFact)


def enroll_reference_prior_principal(session, command):
    command = ReferencePriorPrincipalCommand.model_validate(canonical(command))
    return _call(session, "enroll_principal", command, ReferencePriorPrincipalFact)


def change_reference_prior_authority(session, command):
    command = ReferencePriorAuthorityCommand.model_validate(canonical(command))
    return _call(session, "change_authority", command, ReferencePriorAuthorityEvent)


def publish_reference_prior(session, command):
    command = ReferencePriorPublishCommand.model_validate(canonical(command))
    return _call(session, "publish", command, ReferencePriorWriteReceipt)


def retract_reference_prior(session, command):
    command = ReferencePriorRetractCommand.model_validate(canonical(command))
    return _call(session, "publish", command, ReferencePriorWriteReceipt)


def capture_reference_prior_sources(session, request):
    if session.new or session.dirty or session.deleted:
        raise ValueError("Clean caller-owned read-only capture transaction required")
    request = ReferencePriorCaptureRequest.model_validate(canonical(request))

    # Validate the complete snapshot only after canonical owner reads finish on this same session.
    class _Parts:
        @staticmethod
        def model_validate(value):
            return value

    parts = _call(session, "capture", request, _Parts)
    targets = {target_key(t): t for t in request.requested_targets}
    for stream in parts["streams"]:
        from pydantic import TypeAdapter

        from app.modules.preferences.contracts import PreferenceTarget

        t = TypeAdapter(PreferenceTarget).validate_python(stream["target"])
        targets[target_key(t)] = t
    ingredients = {
        i.id: i
        for i in ingredient_identities(
            session, [t.ingredient_id for t in targets.values() if t.kind == "INGREDIENT"]
        )
    }
    recipes = {
        i.id: i
        for i in recipe_identities(
            session, [t.recipe_id for t in targets.values() if t.kind == "DIRECT_RECIPE"]
        )
    }
    terms = {
        i.id: i
        for i in reviewed_affinity_feature_terms(
            session,
            [
                t.feature_term_id
                for t in targets.values()
                if t.kind in {"PROTEIN", "METHOD", "FLAVOR"}
            ],
        )
    }
    identities = []
    for t in targets.values():
        if t.kind == "INGREDIENT":
            identity = ingredients.get(t.ingredient_id)
        elif t.kind == "DIRECT_RECIPE":
            identity = recipes.get(t.recipe_id)
        else:
            identity = terms.get(t.feature_term_id)
        if identity is None:
            raise ValueError("TARGET_IDENTITY_UNRESOLVED")
        identities.append(ReferencePriorTargetIdentity(target=t, identity=identity))
    parts["identities"] = identities
    parts["capture_completed_at"] = session.scalar(text("SELECT menuto_prior.capture_complete()"))
    return ReferencePriorSourceSnapshotDraft.model_validate(canonical(parts))
