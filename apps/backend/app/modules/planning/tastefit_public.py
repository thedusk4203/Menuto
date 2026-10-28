"""Three bounded additive TasteFit operations, no endpoint or activation authority."""


def capture_candidate_member_tastefit_sources(sessions, request, *, actor_user_id):
    from app.modules.planning.tastefit_capture import capture_candidate_member_tastefit_sources

    return capture_candidate_member_tastefit_sources(sessions, request, actor_user_id=actor_user_id)


def derive_candidate_member_tastefit(sources):
    from app.modules.planning.tastefit import derive_candidate_member_tastefit

    return derive_candidate_member_tastefit(sources)


def validate_candidate_member_tastefit(result):
    from app.modules.planning.tastefit import validate_candidate_member_tastefit

    return validate_candidate_member_tastefit(result)
