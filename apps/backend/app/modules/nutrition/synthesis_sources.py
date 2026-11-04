"""Authenticated same-connection capture. Enrollment is a separate privileged interface."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.feature_identity import canonical, canonical_bytes
from app.modules.nutrition import root_public
from app.modules.nutrition import synthesis_contracts as c
from app.modules.nutrition.root_limits import COMMAND_BYTES, OPERATION_MILLISECONDS, check_structure


def _call(session, operation, value):
    if operation not in {
        "register_provider",
        "enroll_principal",
        "change_authority",
        "append",
        "capture",
    }:
        raise ValueError("Unknown protected synthesis operation")
    check_structure(value, byte_limit=COMMAND_BYTES)
    body = canonical_bytes(value)
    url = session.get_bind().url
    if (
        url.host not in {"localhost", "127.0.0.1", "::1"}
        and url.query.get("sslmode") != "verify-full"
    ):
        raise ValueError("Remote synthesis source requires verified TLS")
    timeout = session.scalar(text("SHOW statement_timeout"))
    session.execute(
        text("SELECT set_config('statement_timeout',:t,true)"), {"t": str(OPERATION_MILLISECONDS)}
    )
    result = session.scalar(
        text(f"SELECT menuto_nutrition_synthesis.{operation}(CAST(:body AS jsonb))"),
        {"body": body.decode("utf-8")},
    )
    session.execute(text("SELECT set_config('statement_timeout',:t,true)"), {"t": timeout})
    return result


def append_nutrition_synthesis_rule(session, value):
    command = c.NutritionSynthesisCommand.model_validate(canonical(value))
    return c.NutritionSynthesisRecorded.model_validate(_call(session, "append", command))


def capture_nutrition_synthesis_sources(session, value):
    if not isinstance(session, Session) or session.new or session.dirty or session.deleted:
        raise ValueError("One clean caller-owned Nutrition source reader transaction required")
    request = c.NutritionSynthesisRequest.model_validate(canonical(value))
    # Always recapture/rederive the child on this exact connection; a supplied cached
    # result is never a source authority or a shortcut around the frozen root path.
    sources = root_public.capture_nutrition_root_sources(session, request.root.sources.request)
    root = root_public.resolve_nutrition_root(sources)
    request = c.NutritionSynthesisRequest.model_validate(
        dict(canonical(request), root=canonical(root))
    )
    command = c.NutritionSynthesisCaptureCommand(
        root_request=sources.request,
        root_frame=sources.capture,
        selection=request.selection,
        precision=request.precision,
    )
    body = dict(
        _call(session, "capture", command),
        request=request,
        contract_version="nutrition-synthesis-sources.v1",
    )
    body["source_fingerprint"] = c.n.nutrition_root_hash("nutrition-synthesis.sources.v1", body)
    result = c.NutritionSynthesisSourceSnapshot.model_validate(body)
    from app.modules.nutrition.synthesis_journal import replay_synthesis_sources

    replay_synthesis_sources(result)
    return result
