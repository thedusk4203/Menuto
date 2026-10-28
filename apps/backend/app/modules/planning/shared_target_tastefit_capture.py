"""All-or-fail fresh cohort capture on caller-owned read-only owner sessions."""

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.domain.resolution import ResolutionError
from app.modules.planning.candidate_feature_capture import (
    capture_candidate_feature_projection_sources,
)
from app.modules.planning.candidate_feature_projection import project_candidate_features
from app.modules.planning.shared_target_tastefit import (
    _child_request,
    _parse_request,
    _participants,
    derive_shared_member_target_tastefit,
)
from app.modules.planning.shared_target_tastefit_contracts import SharedMemberTargetTasteFitSources
from app.modules.planning.tastefit_public import (
    capture_candidate_member_tastefit_sources,
    derive_candidate_member_tastefit,
)


def capture_shared_member_target_tastefit_sources(sessions, request, *, actor_user_id):
    request = _parse_request(request)
    stage, member_id = "CANDIDATE_PREFLIGHT", None
    try:
        # Retain the caller's exact Session objects for this entire cohort.
        # Later changes to its mapping cannot select another owner transaction.
        sessions = dict(sessions)
        session = sessions["member"]
        # The frozen preflight proves access, canonical grounding/pin and transaction
        # cleanliness before the first preference read, including all participant IDs.
        projection = project_candidate_features(
            capture_candidate_feature_projection_sources(
                session, request.projection_request, actor_user_id=actor_user_id
            )
        )
        _participants(request, projection)
        started = projection.source.capture_started_at
        children = []
        for member in request.members:
            member_id, stage = member.member_id, "MEMBER_CHILD_CAPTURE"
            source = capture_candidate_member_tastefit_sources(
                sessions, _child_request(request, member), actor_user_id=actor_user_id
            )
            stage = "MEMBER_CHILD_REPLAY"
            children.append(derive_candidate_member_tastefit(source))
        fields = dict(
            request=request,
            children=tuple(children),
            owner_frames=tuple(
                (
                    ch.subject.member_id,
                    (ch.sources.candidate_frame,) + ch.sources.member_sources.frames,
                )
                for ch in children
            ),
            capture_started_at=started,
            capture_completed_at=session.scalar(text("SELECT clock_timestamp()")),
        )
        stage, member_id = "COHORT_VALIDATION", None
        temporary = SharedMemberTargetTasteFitSources.model_construct(
            **fields, fingerprint="0" * 64
        )
        source = SharedMemberTargetTasteFitSources(
            **fields, fingerprint=temporary.expected_fingerprint()
        )
        return derive_shared_member_target_tastefit(source).sources
    except ResolutionError as exc:
        if stage == "COHORT_VALIDATION":
            raise
        code = (
            "CAPTURE_ACCESS_DENIED"
            if exc.code == "CAPTURE_ACCESS_DENIED"
            else ("MEMBER_SOURCE_UNAVAILABLE")
        )
        raise ResolutionError(
            code,
            f"member={member_id}; stage={stage}; cause={exc.code}; full cohort retry required",
            rejected=True,
        ) from exc
    except (
        DBAPIError,
        OSError,
        TimeoutError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
    ) as exc:
        raise ResolutionError(
            "MEMBER_SOURCE_UNAVAILABLE",
            f"member={member_id}; stage={stage}; required owner read failed; "
            "full cohort retry required",
            rejected=True,
        ) from exc
