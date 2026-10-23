from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.units import Provenance
from app.modules.catalog.contracts import AffinityFeatureTermFact
from app.modules.preferences.contracts import (
    MemberPreferenceDeclarationFact,
    SetMemberPreferenceCommand,
)

NOW = datetime(2026, 10, 22, tzinfo=UTC)


def provenance(**kw):
    return Provenance(
        **(
            dict(
                kind="USER",
                source_system="synthetic.preferences",
                external_record_id=str(uuid4()),
                source_version="1",
                observed_at=NOW,
            )
            | kw
        )
    )


def command(**kw):
    return SetMemberPreferenceCommand(
        **(
            dict(
                household_id=uuid4(),
                member_id=uuid4(),
                actor_user_id=uuid4(),
                authorship="SELF",
                target=dict(kind="INGREDIENT", ingredient_id=uuid4()),
                expected_revision=-1,
                predecessor_id=None,
                value="LIKE",
                reason="INITIAL",
                occurred_at=NOW,
                provenance=provenance(),
                idempotency_key=uuid4().hex,
            )
            | kw
        )
    )


def term(kind="METHOD", **kw):
    return AffinityFeatureTermFact(
        **(
            dict(
                id=uuid4(),
                kind=kind,
                code="synthetic." + uuid4().hex,
                version=1,
                label="Synthetic term",
                definition="Synthetic authored meaning, no ingredient/recipe classification",
                status="REVIEWED",
                provenance=provenance(kind="REVIEWED_REFERENCE"),
            )
            | kw
        )
    )


def declaration(cmd, *, stream_id=None, sequence=1):
    return MemberPreferenceDeclarationFact(
        id=uuid4(),
        stream_id=stream_id or uuid4(),
        member_sequence=sequence,
        revision_no=cmd.expected_revision + 1,
        recorded_at=NOW + timedelta(seconds=sequence),
        actor_role="OWNER",
        command=cmd,
        command_fingerprint=cmd.fingerprint(),
    )
