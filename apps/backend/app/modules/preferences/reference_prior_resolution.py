"""Zero-IO replay; source self-consistency does not authenticate database origin."""

from app.domain.feature_identity import canonical
from app.modules.preferences.reference_prior_contracts import (
    ReferencePriorSourceSnapshotDraft,
    ReviewedReferencePriorDraft,
    prior_hash,
    reference_rows,
)


def resolve_reference_priors(source):
    source = ReferencePriorSourceSnapshotDraft.model_validate(canonical(source))
    rows = reference_rows(source)
    return ReviewedReferencePriorDraft(
        source=source,
        rows=rows,
        source_fingerprint=source.fingerprint(),
        result_fingerprint=prior_hash(
            "reviewed-reference-prior.v1", dict(source=source, rows=rows)
        ),
    )
