"""Pure captured classification consumer. No DB, scoring or behavioral interpretation."""

from app.domain.feature_identity import identity_hash, unique_sorted
from app.modules.planning import contracts as c
from app.modules.recipes.contracts import (
    discover_feature_input,
    resolve_feature_input,
)


def discover_culinary_feature_assignments(subject):
    subject = c.CapturedCulinaryFeatureSubjectDraft.model_validate(subject.model_dump())
    rows = discover_feature_input(subject.evaluation)
    return c.CulinaryFeatureDiscoveryDraft(
        subject=subject,
        dimensions=rows,
        fingerprint=identity_hash(dict(subject_hash=subject.fingerprint, dimensions=rows)),
    )


def resolve_feature_terms(subject, queries):
    subject = c.CapturedCulinaryFeatureSubjectDraft.model_validate(subject.model_dump())
    queries = unique_sorted(
        tuple(c.FeatureTermQuery.model_validate(q.model_dump()) for q in queries),
        key=lambda q: q.dimension,
    )
    if not queries:
        raise ValueError("Nonempty query set required")
    terms = resolve_feature_input(subject.evaluation, queries)
    count = sum(t.state != "UNRESOLVED" for t in terms)
    status = "RESOLVED" if count == len(terms) else ("PARTIAL" if count else "UNRESOLVED")
    return c.CulinaryFeatureResolutionDraft(
        subject=subject,
        queries=queries,
        terms=terms,
        status=status,
        fingerprint=identity_hash(
            dict(subject_hash=subject.fingerprint, queries=queries, terms=terms, status=status)
        ),
    )
