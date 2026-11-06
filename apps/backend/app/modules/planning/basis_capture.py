"""Trusted disposable-harness composition; no production registry, writes or new DB grants."""

from dataclasses import dataclass
from threading import RLock, Timer
from time import monotonic
from weakref import WeakKeyDictionary

from sqlalchemy import text

from app.domain.feature_identity import canonical
from app.modules.nutrition import basis_contracts as b
from app.modules.nutrition.basis_applicability import replay_basis_artifact
from app.modules.nutrition.basis_projection import project_basis_anchors
from app.modules.nutrition.resolution_contracts import NutritionResolutionHandoffV2
from app.modules.nutrition.resolution_estimator import estimate_nutrition_resolution
from app.modules.nutrition.resolution_limits import WorkBudget
from app.modules.planning.nutrition_resolution_capture import capture_nutrition_resolution_sources

_INSTALLER = object()
_ISSUED = WeakKeyDictionary()
_LOCK = RLock()


class _HarnessContext:
    __slots__ = ("__weakref__",)

    def __init__(self, seal=None):
        if seal is not _INSTALLER:
            raise PermissionError("Private harness issuance required")

    def __reduce__(self):
        raise TypeError("Harness context cannot be serialized")


@dataclass(frozen=True)
class _Registration:
    artifact: b.BasisFixtureArtifactV1
    nre_context: object
    reader_principal: str
    actor_user_id: object


def _artifact(value):
    a = b.parse_basis(value, b.BasisFixtureArtifactV1, 2 * 1024 * 1024)
    body = canonical(a)
    body.pop("artifact_fingerprint")
    if b.basis_hash("artifact", body) != a.artifact_fingerprint or not a.database_name.startswith(
        "nrc_test_"
    ):
        raise ValueError("ENVIRONMENT_MISMATCH")
    return a


def _install_isolated_basis_fixture(nre_context, artifact, *, reader_principal, actor_user_id):
    """Private test bootstrap only. Trusted Python installer is outside the hostile-data model."""
    a = _artifact(artifact)
    if (a.database_oid, a.database_name) != (nre_context.database_oid, nre_context.database_name):
        raise PermissionError("ENVIRONMENT_MISMATCH")
    handle = _HarnessContext(_INSTALLER)
    with _LOCK:
        _ISSUED[handle] = _Registration(a, nre_context, reader_principal, actor_user_id)
    return handle


def _advance_isolated_basis_fixture(handle, artifact):
    """Atomic append-only registry frontier replacement by privileged test setup."""
    a = _artifact(artifact)
    with _LOCK:
        old = _ISSUED.get(handle)
        if old is None:
            raise PermissionError("FORGED_CONTEXT")
        p = old.artifact
        if (
            (a.registry_id, a.deployment, a.database_oid, a.database_name, a.issuer_epoch)
            != (p.registry_id, p.deployment, p.database_oid, p.database_name, p.issuer_epoch)
            or a.revision != p.revision + 1
            or a.previous_artifact_fingerprint != p.artifact_fingerprint
        ):
            raise ValueError("REGISTRY_FRONTIER")
        if a.events[: len(p.events)] != p.events or len(a.events) <= len(p.events):
            raise ValueError("HISTORY_REWRITTEN")
        _ISSUED[handle] = _Registration(a, old.nre_context, old.reader_principal, old.actor_user_id)


def _revoke_isolated_basis_context(handle):
    with _LOCK:
        _ISSUED.pop(handle, None)


def capture_test_basis_sources(trusted_context, caller_owned_nre_session, exact_selectors):
    """One frozen ordinary reader; artifact revision is pinned around the actual DB capture."""
    began = monotonic()
    if type(trusted_context) is not _HarnessContext:
        raise PermissionError("FORGED_CONTEXT")
    with _LOCK:
        reg = _ISSUED.get(trusted_context)
    if reg is None:
        raise PermissionError("FORGED_CONTEXT")
    selection = b.parse_basis(exact_selectors, b.BasisSelectorsV1, 64 * 1024)
    if (
        selection.reader_principal != reg.reader_principal
        or selection.nre_scope.actor_user_id != reg.actor_user_id
    ):
        raise PermissionError("READER_BINDING_MISMATCH")
    session = caller_owned_nre_session
    # Frozen adapter itself checks session shape/cleanliness/identity/privileges before reads.
    # Do not perform a preliminary ORM/query read here that could dirty its identity map.
    connection = session.connection()
    timer = Timer(60, connection.connection.driver_connection.cancel)
    timer.daemon = True
    timer.start()
    try:
        nre_sources = capture_nutrition_resolution_sources(
            session, reg.nre_context, selection.nre_scope
        )
        a = reg.artifact
        actual = nre_sources.frame
        if (a.database_oid, a.database_name) != (
            actual.fixture_database_oid,
            actual.fixture_database_name,
        ):
            raise PermissionError("ENVIRONMENT_MISMATCH")
        estimate = estimate_nutrition_resolution(nre_sources)
        nre = NutritionResolutionHandoffV2(sources=nre_sources, estimate=estimate)
        anchors = project_basis_anchors(nre)
        completed = session.scalar(text("SELECT clock_timestamp()"))
        # Reader admission is reconstructed, not a boolean supplied by the caller.
        replay_basis_artifact(
            a, selection, completed, nre_sources.scope.root_request.temporal.interval, WorkBudget()
        )
        if monotonic() - began > 60:
            raise ValueError("RESOURCE_EXCEEDED: combined capture watchdog")
        frame = b.BasisCaptureFrameV1(
            registry_id=a.registry_id,
            registry_revision=a.revision,
            artifact_fingerprint=a.artifact_fingerprint,
            deployment=a.deployment,
            issuer_epoch=a.issuer_epoch,
            database_oid=a.database_oid,
            database_name=a.database_name,
            started_at=actual.started_at,
            completed_at=completed,
        )
        body = dict(
            nre=nre, artifact=a, selectors=selection, anchors=anchors, frame=frame, absences=()
        )
        model = b.BasisApplicabilitySourcesV1(**body, source_fingerprint="0" * 64)
        fields = canonical(model)
        fields.pop("source_fingerprint")
        result = b.BasisApplicabilitySourcesV1(
            **fields, source_fingerprint=b.basis_hash("sources", fields)
        )
        if monotonic() - began > 60:
            raise ValueError("RESOURCE_EXCEEDED: combined capture watchdog")
        with _LOCK:
            if _ISSUED.get(trusted_context) is not reg:
                raise PermissionError("REGISTRY_FRONTIER_CHANGED")
            return result
    finally:
        timer.cancel()
