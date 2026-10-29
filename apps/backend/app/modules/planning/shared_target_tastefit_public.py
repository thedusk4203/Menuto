"""Three additive operations; no endpoint, policy selector or planner authority."""


def capture_shared_member_target_tastefit_sources(sessions, request, *, actor_user_id):
    from app.modules.planning.shared_target_tastefit_capture import (
        capture_shared_member_target_tastefit_sources,
    )

    return capture_shared_member_target_tastefit_sources(
        sessions, request, actor_user_id=actor_user_id
    )


def derive_shared_member_target_tastefit(sources):
    from app.modules.planning.shared_target_tastefit import derive_shared_member_target_tastefit

    return derive_shared_member_target_tastefit(sources)


def validate_shared_member_target_tastefit(result):
    from app.modules.planning.shared_target_tastefit import validate_shared_member_target_tastefit

    return validate_shared_member_target_tastefit(result)
