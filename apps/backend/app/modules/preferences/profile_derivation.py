"""Zero-IO exact-target explicit interpretation. No persistence or runtime source imports."""

from app.modules.preferences.contracts import (
    ExplicitTargetAffinityInput,
    ExplicitTargetAffinityProfileDraft,
    _explicit_target_affinity_rows,
    _profile_hash,
)


def derive_explicit_target_affinity_profile(subject):
    subject = ExplicitTargetAffinityInput.model_validate(subject)
    fields = dict(
        subject=subject,
        rows=_explicit_target_affinity_rows(subject),
        source_fingerprint=_profile_hash(subject.source),
        manifest_fingerprint=_profile_hash(subject.source.manifest),
        policy_fingerprint=_profile_hash(subject.policy),
    )
    # Temporary object only computes the non-self-referential hash; never returned.
    temporary = ExplicitTargetAffinityProfileDraft.model_construct(**fields, fingerprint="0" * 64)
    return ExplicitTargetAffinityProfileDraft(
        **fields, fingerprint=temporary.expected_fingerprint()
    )
