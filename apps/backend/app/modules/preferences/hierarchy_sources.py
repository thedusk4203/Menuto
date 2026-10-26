"""Internal hierarchy source interface. Caller owns transaction and credentials."""

import json

from sqlalchemy import text

from app.domain.feature_identity import canonical
from app.modules.preferences import hierarchy_contracts as c


def _call(session, function, command, output):
    url = session.get_bind().url
    if (
        url.host not in {"localhost", "127.0.0.1", "::1"}
        and url.query.get("sslmode") != "verify-full"
    ):
        raise ValueError("Remote hierarchy source requires sslmode=verify-full")
    result = session.scalar(
        text(f"SELECT menuto_hierarchy.{function}(CAST(:command AS jsonb))"),
        {"command": json.dumps(canonical(command), ensure_ascii=False)},
    )
    return output.model_validate(result)


def register_hierarchy_provider(session, command):
    command = c.HierarchyProviderCommand.model_validate(canonical(command))
    return _call(session, "register_provider", command, c.HierarchyProviderFact)


def enroll_hierarchy_principal(session, command):
    command = c.HierarchyPrincipalCommand.model_validate(canonical(command))
    return _call(session, "enroll_principal", command, c.HierarchyPrincipalFact)


def change_hierarchy_authority(session, command):
    command = c.HierarchyAuthorityCommand.model_validate(canonical(command))
    return _call(session, "change_authority", command, c.HierarchyAuthorityEvent)


def publish_hierarchy_source(session, command):
    command = c.HierarchyPublicationCommand.model_validate(canonical(command))
    return _call(session, "publish", command, c.HierarchyWriteReceipt)


def capture_hierarchy_sources(session, request):
    if session.new or session.dirty or session.deleted:
        raise ValueError("Clean read-only RR/SERIALIZABLE hierarchy capture required")
    request = c.HierarchyCaptureRequest.model_validate(canonical(request))
    return _call(session, "capture", request, c.HierarchySourceSnapshotDraft)
