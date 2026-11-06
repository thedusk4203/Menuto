"""Server-owned wall-time hosting; no production admission or policy integration."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError

from app.modules.nutrition.basis_applicability import basis_handoff
from app.modules.validation.basis_applicability import check_basis_handoff_independently


def _run_bounded(operation, *, executor_factory=ThreadPoolExecutor):
    executor = None
    try:
        executor = executor_factory(max_workers=1)
        # Host timeout discards the result. Cooperative pure-work limits additionally
        # bound running work; a Python thread is not a hostile-code sandbox.
        return executor.submit(operation).result(timeout=10)
    except TimeoutError as exc:
        raise ValueError("RESOURCE_EXCEEDED: server execution timeout") from exc
    finally:
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)


def reconstruct_test_basis_handoff(retained_sources):
    """Fresh conjunction for diagnostics only; all returned transports stay unverified."""
    handoff = _run_bounded(lambda: basis_handoff(retained_sources))
    report = _run_bounded(lambda: check_basis_handoff_independently(handoff))
    if report.decision != "CONSISTENT":
        raise ValueError("BASIS_INDEPENDENT_RECONSTRUCTION_FAILED")
    return handoff
