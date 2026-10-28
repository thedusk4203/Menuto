"""Fresh candidate/member coordinator; never opens or commits caller transactions."""

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.domain.resolution import ResolutionError
from app.modules.planning.candidate_feature_capture import (
    capture_candidate_feature_projection_sources,
)
from app.modules.planning.candidate_feature_projection import project_candidate_features
from app.modules.planning.tastefit import (
    _budget,
    _parse_request,
    candidate_target_set,
    derive_candidate_member_tastefit,
    member_capture_plan,
)
from app.modules.planning.tastefit_contracts import CandidateMemberTasteFitSources
from app.modules.preferences.tastefit_contracts import TasteFitCaptureFrame
from app.modules.preferences.tastefit_public import capture_tastefit_member_sources


def _clock(session):
    return session.scalar(text("SELECT clock_timestamp()"))


def capture_candidate_member_tastefit_sources(sessions, request, *, actor_user_id):
    request = _parse_request(request)
    try:
        session = sessions["member"]
        if session is None or session.new or session.dirty or session.deleted:
            raise ValueError("Clean read-only session required")
        isolation = session.connection().get_isolation_level()
        if isolation not in {"REPEATABLE READ", "SERIALIZABLE"} or (
            session.scalar(text("SHOW transaction_read_only")) != "on"
        ):
            raise ValueError("Read-only RR/SERIALIZABLE required")
        started = _clock(session)
        projection_source = capture_candidate_feature_projection_sources(
            session, request.projection_request, actor_user_id=actor_user_id
        )
        projection = project_candidate_features(projection_source)
        plan = member_capture_plan(request, projection)
        if len(plan.targets) > request.policy.max_targets:
            raise ResolutionError(
                "RESOURCE_LIMIT", "Candidate target budget exceeded", rejected=True
            )
        _, targets = candidate_target_set(projection, request.diagnostic_targets)
        url = session.get_bind().engine.url
        identity = (
            session.execute(
                text(
                    "SELECT current_database() AS database_name, "
                    "(SELECT oid::bigint FROM pg_database "
                    "WHERE datname=current_database()) AS database_oid, "
                    "host(inet_server_addr()) AS server_address, "
                    "inet_server_port() AS server_port, "
                    "session_user AS session_user"
                )
            )
            .mappings()
            .one()
        )
        frame = TasteFitCaptureFrame(
            owner="CANDIDATE",
            actor_user_id=actor_user_id,
            targets=tuple(targets.values()),
            configured_host=url.host or "",
            configured_port=url.port or 5432,
            **identity,
            isolation=isolation,
            read_only=True,
            started_at=started,
            completed_at=_clock(session),
        )
        bundle = capture_tastefit_member_sources(sessions, plan, actor_user_id=actor_user_id)
        fields = dict(
            request=request,
            projection=projection,
            member_sources=bundle,
            candidate_frame=frame,
            capture_started_at=started,
            capture_completed_at=_clock(session),
        )
        temporary = CandidateMemberTasteFitSources.model_construct(**fields, fingerprint="0" * 64)
        source = CandidateMemberTasteFitSources(
            **fields, fingerprint=temporary.expected_fingerprint()
        )
        _budget(source, source=True)
        return derive_candidate_member_tastefit(source).sources
    except ResolutionError:
        raise
    except PermissionError as exc:
        raise ResolutionError(
            "CAPTURE_ACCESS_DENIED", "Household read access denied", rejected=True
        ) from exc
    except LookupError as exc:
        raise ResolutionError(
            "CANONICAL_TARGET_UNAVAILABLE", "Required owner identity missing", rejected=True
        ) from exc
    except (DBAPIError, OSError, TimeoutError, ValueError, TypeError, AttributeError) as exc:
        raise ResolutionError(
            "SOURCE_CAPTURE_FAILED", "Required owner capture failed", rejected=True
        ) from exc
