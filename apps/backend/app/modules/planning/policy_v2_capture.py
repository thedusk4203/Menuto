"""Cut-scoped TEST_ONLY capture and atomic one-shot use. No transferable authority."""

import multiprocessing
import os
from dataclasses import dataclass
from threading import Event, RLock, Thread, Timer
from time import monotonic
from weakref import WeakKeyDictionary

from sqlalchemy import text

from app.domain.feature_identity import canonical_bytes
from app.modules.nutrition import policy_v2_contracts as v
from app.modules.nutrition.policy_v2_public import prepare_policy_v2_input
from app.modules.planning import basis_capture as mba
from app.modules.planning.policy_v2_worker import execute

_SEAL = object()
_LOCK = RLock()
_SPAWN_LOCK = RLock()
_ACTIVE = WeakKeyDictionary()
_TERMINAL = WeakKeyDictionary()
_SESSIONS = WeakKeyDictionary()
_PURE_SECONDS = 15.0


class _Lease:
    __slots__ = ("__weakref__",)

    def __init__(self, seal=None):
        if seal is not _SEAL:
            raise TypeError("Private capture issuance required")

    def __reduce__(self):
        raise TypeError("Lease cannot be serialized")

    def __copy__(self):
        raise TypeError("Lease cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Lease cannot be copied")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        with _LOCK:
            _burn(self, "ABORTED")


@dataclass
class _Entry:
    state: str
    session: object
    connection: object
    transaction: object
    context: object
    registration: object
    cut: tuple
    input: v.NutritionPolicyIntegrationInputV2
    result: v.NutritionPolicyResultV2
    use: v.PolicyV2Use
    deadline: float
    timer: object
    session_owner: object


@dataclass
class _Reservation:
    state: str
    cancelled: object


def _burn(lease, state):
    entry = _ACTIVE.pop(lease, None)
    if entry is not None:
        entry.state = state
        entry.session_owner.state = state
        entry.session_owner.cancelled.set()
        if _SESSIONS.get(entry.session) is entry.session_owner:
            _SESSIONS.pop(entry.session, None)
        if entry.timer:
            entry.timer.cancel()
        _TERMINAL[lease] = state


def _expire(lease):
    with _LOCK:
        _burn(lease, "ABORTED")


def _failure(code, outcome="ADMISSION_REJECTED", fingerprint=None):
    return v.PolicyV2CaptureFailure(
        contract_version="nutrition-policy-capture-failure.v2",
        outcome=outcome,
        diagnostics=(
            v.PolicyDiagnosticV2(
                stage="CONSUMER",
                code=code,
                subject_path=None,
                child_outcome=None,
                child_reason=None,
                hard_support="NOT_EVALUATED",
                soft_support="NOT_EVALUATED",
                environment="TEST_ONLY",
            ),
        ),
        input_fingerprint=fingerprint,
        environment="TEST_ONLY",
        production_admission="CLOSED",
        planner_ready=False,
        activation_ready=False,
    )


def _cut(session, deadline):
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise TimeoutError("HOST_TIMEOUT")
    timer = Timer(remaining, session.connection().connection.driver_connection.cancel)
    timer.daemon = True
    timer.start()
    try:
        return tuple(
            session.execute(
                text(
                    "SELECT pg_catalog.current_database(), (SELECT oid FROM pg_catalog.pg_database "
                    "WHERE datname=pg_catalog.current_database()), session_user, current_user, "
                    "(SELECT oid FROM pg_catalog.pg_roles WHERE rolname=session_user), "
                    "(SELECT oid FROM pg_catalog.pg_roles WHERE rolname=current_user), "
                    "pg_catalog.pg_backend_pid(), pg_catalog.pg_current_snapshot()::text, "
                    "pg_catalog.current_setting('transaction_isolation'), "
                    "pg_catalog.current_setting('transaction_read_only')"
                )
            ).one()
        )
    finally:
        timer.cancel()
        timer.join()


def _run(stage, data, deadline, cancelled=None):
    """Explicit spawn, bounded byte transport and kill/join on every timeout path."""
    stage_deadline = min(deadline, monotonic() + _PURE_SECONDS)
    remaining = stage_deadline - monotonic()
    if remaining <= 0:
        raise TimeoutError("HOST_TIMEOUT")
    body = canonical_bytes(data)
    if len(body) > (32 if stage == "derive" else 48) * 1024 * 1024:
        raise ValueError("RESOURCE_EXCEEDED: worker input")
    ctx = multiprocessing.get_context("spawn")
    parent, child = ctx.Pipe(duplex=False)
    process = ctx.Process(target=execute, args=(stage, body, child), daemon=True)
    process_started = False
    finished, watcher = Event(), None

    def stop_at_boundary():
        while not finished.wait(0.02):
            if monotonic() >= stage_deadline or (cancelled is not None and cancelled.is_set()):
                if process.is_alive():
                    process.kill()
                return

    try:
        # Spawn only primitive bytes and the dedicated IPC endpoint. Environment
        # is scrubbed before the fresh interpreter starts, not inside it afterwards.
        with _SPAWN_LOCK:
            if monotonic() >= stage_deadline or (cancelled is not None and cancelled.is_set()):
                raise TimeoutError("HOST_TIMEOUT")
            secret = {
                k: val
                for k, val in os.environ.items()
                if k.upper().startswith("PG")
                or any(
                    word in k.upper()
                    for word in (
                        "DATABASE",
                        "POSTGRES",
                        "PGPASS",
                        "PGUSER",
                        "PASSWORD",
                        "TOKEN",
                        "SECRET",
                        "CREDENTIAL",
                        "DSN",
                    )
                )
                or "postgres://" in val.lower()
                or "postgresql" in val.lower()
            }
            try:
                for key in secret:
                    os.environ.pop(key, None)
                process.start()
                process_started = True
            finally:
                os.environ.update(secret)
        child.close()
        remaining = stage_deadline - monotonic()
        if remaining <= 0:
            raise TimeoutError("HOST_TIMEOUT")
        watcher = Thread(target=stop_at_boundary, daemon=True)
        watcher.start()
        limit = 8 * 1024 * 1024 if stage == "derive" else 256 * 1024
        if not parent.poll(remaining):
            raise TimeoutError("HOST_TIMEOUT")
        try:
            result = parent.recv_bytes(maxlength=limit)
        except EOFError as exc:
            if monotonic() >= stage_deadline or (cancelled is not None and cancelled.is_set()):
                raise TimeoutError("HOST_TIMEOUT") from exc
            raise ValueError("Pure worker failed") from exc
        process.join(max(0, stage_deadline - monotonic()))
        if process.is_alive():
            raise TimeoutError("HOST_TIMEOUT")
        if cancelled is not None and cancelled.is_set():
            raise TimeoutError("HOST_TIMEOUT")
        if monotonic() >= stage_deadline:
            raise TimeoutError("HOST_TIMEOUT")
        if process.exitcode != 0:
            raise ValueError("Pure worker failed")
        return result
    finally:
        finished.set()
        if watcher is not None:
            watcher.join()
        if process_started:
            if process.is_alive():
                process.kill()
            process.join()
            process.close()
        child.close()
        parent.close()


def expected_policy_v2_use(retained_input):
    """Unverified use selector. Equality to this shape never supplies a lease."""
    i = v.parse_policy_v2(retained_input, v.NutritionPolicyIntegrationInputV2)
    return v.PolicyV2Use(
        purpose="STRUCTURAL_TEST_ONLY_INSPECTION",
        subject=i.identity.subject,
        actor_user_id=i.identity.actor_user_id,
        selector_fingerprint=v.policy_v2_hash("selectors", i.basis_sources.selectors),
        precision_fingerprint=v.policy_v2_hash("precision", i.identity.precision),
        environment="TEST_ONLY",
    )


def capture_test_policy_v2(session, issued_basis_context, selectors):
    began, lease = monotonic(), _Lease(_SEAL)
    owner, issued, reserved = _Reservation("CAPTURING", Event()), False, False
    try:
        with mba._LOCK:
            reg = mba._ISSUED.get(issued_basis_context)
        if reg is None or type(issued_basis_context) is not mba._HarnessContext:
            return _failure("ORIGIN_NOT_ESTABLISHED", "CAPTURE_REJECTED")
        with _LOCK:
            if session in _SESSIONS:
                return _failure("SOURCE_CUT_INCOHERENT", "CAPTURE_REJECTED")
            _SESSIONS[session] = owner
            reserved = True
        connection, transaction = session.connection(), session.get_transaction()
        sources = mba.capture_test_basis_sources(issued_basis_context, session, selectors)
        if monotonic() - began > 60:
            return _failure("HOST_TIMEOUT", "RESOURCE_EXCEEDED")
        i = prepare_policy_v2_input(sources)
        if (
            session.connection() is not connection
            or session.get_transaction() is not transaction
            or connection.closed
            or not transaction.is_active
        ):
            return _failure("SOURCE_CUT_INCOHERENT", "CAPTURE_REJECTED")
        cut = _cut(session, began + 90)
        frame = sources.nre.sources.frame.source_frame
        if (
            cut[0:3]
            != (frame.session.database_name, frame.session.database_oid, frame.session.role_name)
            or cut[2] != cut[3]
            or cut[4] != cut[5]
            or cut[4] != frame.session.role_oid
            or cut[6] != frame.backend_pid
            or cut[7] != frame.mvcc_snapshot
            or cut[8].upper() != frame.isolation
            or cut[9] != "on"
        ):
            return _failure("SOURCE_CUT_INCOHERENT", "CAPTURE_REJECTED")
        result = v.parse_policy_v2(
            _run("derive", i, began + 90, owner.cancelled),
            v.NutritionPolicyResultV2,
            8 * 1024 * 1024,
        )
        # The registry is never locked while source capture/pure derivation executes.
        with _LOCK:
            with mba._LOCK:
                if mba._ISSUED.get(issued_basis_context) is not reg:
                    return _failure("REGISTRY_CHANGED", "CAPTURE_REJECTED")
                timer = Timer(max(0, began + 90 - monotonic()), _expire, args=(lease,))
                timer.daemon = True
                _ACTIVE[lease] = _Entry(
                    "READY",
                    session,
                    connection,
                    transaction,
                    issued_basis_context,
                    reg,
                    cut,
                    i,
                    result,
                    expected_policy_v2_use(i),
                    began + 90,
                    timer,
                    owner,
                )
                owner.state = "READY"
                issued = True
                timer.start()
        return lease
    except TimeoutError:
        return _failure("HOST_TIMEOUT", "RESOURCE_EXCEEDED")
    except Exception as exc:
        return _failure(
            "RESOURCE_LIMIT" if str(exc).startswith("RESOURCE_EXCEEDED") else "CAPTURE_FAILED",
            "RESOURCE_EXCEEDED" if str(exc).startswith("RESOURCE_EXCEEDED") else "CAPTURE_REJECTED",
        )

    finally:
        if reserved and not issued:
            with _LOCK:
                if _SESSIONS.get(session) is owner:
                    _SESSIONS.pop(session, None)
                owner.state = "ABORTED"
                owner.cancelled.set()


def _alive(entry):
    s = entry.session
    if entry.state not in {"READY", "CONSUMING"} or _SESSIONS.get(s) is not entry.session_owner:
        return False
    if (
        monotonic() >= entry.deadline
        or not s.in_transaction()
        or s.get_transaction() is not entry.transaction
        or not entry.transaction.is_active
        or entry.connection.closed
        or s.connection() is not entry.connection
    ):
        return False
    return _cut(s, entry.deadline) == entry.cut


def consume_test_policy_v2(private_lease, expected_use):
    entry = None
    with _LOCK:
        if type(private_lease) is not _Lease:
            return _failure("ORIGIN_NOT_ESTABLISHED")
        entry = _ACTIVE.get(private_lease)
        if entry is None:
            return _failure(
                "CONSUME_REPLAY" if private_lease in _TERMINAL else "ORIGIN_NOT_ESTABLISHED"
            )
        if entry.state != "READY":
            return _failure("CONSUME_REPLAY")
        entry.state = "CONSUMING"
        entry.session_owner.state = "CONSUMING"
    try:
        use = v.parse_policy_v2(expected_use, v.PolicyV2Use, 64 * 1024)
        if use != entry.use:
            return _failure("SOURCE_IDENTITY_MISMATCH")
        if not _alive(entry):
            return _failure("CAPTURE_EXPIRED")
        with _LOCK:
            with mba._LOCK:
                if mba._ISSUED.get(entry.context) is not entry.registration:
                    return _failure("REGISTRY_CHANGED")
        handoff = v.NutritionPolicyHandoffV2(
            contract_version="nutrition-policy-handoff.v2",
            input=entry.input,
            result=entry.result,
            retained_check=None,
            environment="TEST_ONLY",
            validation_authority="UNVERIFIED_TRANSPORT",
            production_admission="CLOSED",
            planner_ready=False,
            activation_ready=False,
        )
        report = v.parse_policy_v2(
            _run(
                "check",
                dict(handoff=handoff, use=use),
                entry.deadline,
                entry.session_owner.cancelled,
            ),
            v.NutritionPolicyCheckV2,
            256 * 1024,
        )
        if not _alive(entry):
            return _failure("CAPTURE_EXPIRED")
        with _LOCK:
            with mba._LOCK:
                if mba._ISSUED.get(entry.context) is not entry.registration:
                    return _failure("REGISTRY_CHANGED")
                if _ACTIVE.get(private_lease) is not entry or monotonic() >= entry.deadline:
                    return _failure("CAPTURE_EXPIRED")
                if report.decision != "CONSISTENT":
                    return _failure("POLICY_SEMANTICS_INCONSISTENT")
                if entry.result.outcome != "AVAILABLE_TEST_ONLY":
                    return _failure(entry.result.diagnostics[0].code)
                if report.numerical_use != "AVAILABLE_RETAINED_ONLY":
                    return _failure("REPORT_NOT_AUTHORITY")
                _burn(private_lease, "CONSUMED")
        # This serialized handoff is retained audit evidence, not a reusable admission fact.
        return v.parse_policy_v2(
            handoff.model_copy(update={"retained_check": report}),
            v.NutritionPolicyHandoffV2,
            48 * 1024 * 1024,
        )
    except TimeoutError:
        return _failure("HOST_TIMEOUT", "RESOURCE_EXCEEDED")
    except Exception:
        return _failure("CAPTURE_FAILED")
    finally:
        with _LOCK:
            if _ACTIVE.get(private_lease) is entry:
                _burn(private_lease, "ABORTED")
