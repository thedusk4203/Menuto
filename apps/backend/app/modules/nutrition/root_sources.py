"""One PostgreSQL Adapter. Caller owns credentials, transaction and rollback."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.feature_identity import canonical, canonical_bytes
from app.modules.nutrition import root_contracts as c
from app.modules.nutrition.root_limits import COMMAND_BYTES, OPERATION_MILLISECONDS, check_structure


def _call(session, function, command, output):
    if function not in {
        "register_provider",
        "enroll_principal",
        "change_authority",
        "append",
        "capture",
    }:
        raise ValueError("Unknown protected Nutrition operation")
    check_structure(command, byte_limit=COMMAND_BYTES)
    payload = canonical_bytes(command)
    if len(payload) > COMMAND_BYTES:
        raise ValueError("Nutrition command byte limit; all-or-error")
    url = session.get_bind().url
    if (
        url.host not in {"localhost", "127.0.0.1", "::1"}
        and url.query.get("sslmode") != "verify-full"
    ):
        raise ValueError("Remote Nutrition source requires sslmode=verify-full")
    # Server-authored adapter budget precedes the query; the protected path also
    # enforces absolute lock/structure/history/deadline bounds for direct SQL callers.
    previous_timeout = session.scalar(text("SHOW statement_timeout"))
    session.execute(
        text("SELECT pg_catalog.set_config('statement_timeout',:timeout,true)"),
        {"timeout": str(OPERATION_MILLISECONDS)},
    )
    result = session.scalar(
        text(f"SELECT menuto_nutrition.{function}(CAST(:command AS jsonb))"),
        {"command": payload.decode("utf-8")},
    )
    session.execute(
        text("SELECT pg_catalog.set_config('statement_timeout',:timeout,true)"),
        {"timeout": previous_timeout},
    )
    return output.model_validate(result)


def append_nutrition_source(session, command):
    check_structure(command, byte_limit=COMMAND_BYTES)
    command = c.NutritionSourceCommand.model_validate(canonical(command))
    return _call(session, "append", command, c.NutritionRecordedSource)


def capture_nutrition_root_sources(session, request):
    if not isinstance(session, Session):
        raise ValueError("UNSUPPORTED: one actual caller-owned Nutrition reader session required")
    if session.new or session.dirty or session.deleted:
        raise ValueError("Clean read-only Nutrition source transaction required")
    check_structure(request, byte_limit=COMMAND_BYTES)
    request = c.NutritionRootRequest.model_validate(canonical(request))
    result = _call(session, "capture", request, c.NutritionRootSourceSnapshot)
    # Full semantic reconstruction also verifies the captured immutable manifest.
    from app.modules.nutrition.root_resolution import resolve_nutrition_root

    resolve_nutrition_root(result)
    return result
