"""Catalog-owned reviewed association streams; trusted curation, caller owns transaction."""

from uuid import uuid4

from sqlalchemy import insert, select, text

from app.modules.catalog import contracts as c
from app.modules.catalog import feature_models as m


def _source(provenance):
    fields = provenance.model_dump(exclude={"kind", "source_uri"})
    return fields | dict(
        source_kind=provenance.kind,
        source_uri=str(provenance.source_uri) if provenance.source_uri else None,
    )


def _review(session, row):
    command = session.scalar(
        text("SELECT menuto_feature_review_command(:id,true)"), {"id": row["id"]}
    )
    return c.IngredientProteinReviewFact(
        **{
            k: row[k]
            for k in (
                "id",
                "stream_id",
                "ingredient_id",
                "revision_no",
                "predecessor_revision_no",
                "source_sequence",
                "reviewer_user_id",
                "recorded_at",
                "command_hash",
            )
        },
        command=command,
    )


def ingredient_protein_sources(session, ingredient_ids):
    streams = []
    for row in session.execute(
        select(m.IngredientProteinStream.__table__)
        .where(m.IngredientProteinStream.ingredient_id.in_(ingredient_ids))
        .order_by(m.IngredientProteinStream.ingredient_id)
    ).mappings():
        reviews = tuple(
            _review(session, r)
            for r in session.execute(
                select(m.IngredientProteinReview.__table__)
                .where(m.IngredientProteinReview.stream_id == row["id"])
                .order_by(m.IngredientProteinReview.revision_no)
            ).mappings()
        )
        if (
            not reviews
            or reviews[-1].id != row["head_review_id"]
            or reviews[-1].revision_no != row["head_revision_no"]
        ):
            raise ValueError("Incomplete Catalog source head")
        streams.append(
            c.IngredientProteinStreamFact(
                id=row["id"], ingredient_id=row["ingredient_id"], reviews=reviews
            )
        )
    return tuple(streams)


def ingredient_protein_frontier(session):
    return session.scalar(select(m.IngredientProteinFrontier.generation))


class IngredientProteinService:
    def __init__(self, session, *, actor_user_id):
        self.session, self.actor_user_id = session, actor_user_id

    def write(self, command):
        q = c.IngredientProteinReviewCommand.model_validate(command.model_dump())
        s = self.session
        if s.connection().get_isolation_level() != "READ COMMITTED":
            raise ValueError("Feature writes require READ COMMITTED")
        with s.begin_nested():
            s.execute(select(m.IngredientProteinFrontier).with_for_update()).all()
            old = (
                s.execute(
                    select(m.IngredientProteinReview.__table__).where(
                        m.IngredientProteinReview.source_system == q.provenance.source_system,
                        m.IngredientProteinReview.idempotency_key == q.idempotency_key,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if old:
                if old["command_hash"] != q.fingerprint(self.actor_user_id):
                    raise ValueError("IDEMPOTENCY_CONFLICT")
                return self._receipt(old, True)
            if ingredient_protein_frontier(s) != q.expected_catalog_frontier:
                raise ValueError("Stale Catalog frontier")
            stream = (
                s.execute(
                    select(m.IngredientProteinStream.__table__).where(
                        m.IngredientProteinStream.ingredient_id == q.ingredient_id
                    )
                )
                .mappings()
                .one_or_none()
            )
            if stream is None:
                if q.expected_revision_no != -1:
                    raise ValueError("Stale Catalog revision")
                stream = (
                    s.execute(
                        insert(m.IngredientProteinStream)
                        .values(id=uuid4(), ingredient_id=q.ingredient_id)
                        .returning(m.IngredientProteinStream.__table__)
                    )
                    .mappings()
                    .one()
                )
            if (stream["head_revision_no"], stream["head_review_id"]) != (
                q.expected_revision_no,
                q.predecessor_id,
            ):
                raise ValueError("Stale Catalog revision/predecessor")
            row = (
                s.execute(
                    insert(m.IngredientProteinReview)
                    .values(
                        id=uuid4(),
                        stream_id=stream["id"],
                        ingredient_id=q.ingredient_id,
                        revision_no=q.expected_revision_no + 1,
                        predecessor_revision_no=q.expected_revision_no
                        if q.expected_revision_no >= 0
                        else None,
                        predecessor_id=q.predecessor_id,
                        source_sequence=q.expected_catalog_frontier + 1,
                        action=q.command_kind,
                        command_kind=q.command_kind,
                        coverage=q.coverage,
                        reviewer_user_id=self.actor_user_id,
                        idempotency_key=q.idempotency_key,
                        command_hash=q.fingerprint(self.actor_user_id),
                        correction_reason=q.correction_reason,
                        declared_covered_count=len(q.covered_term_ids),
                        declared_assigned_count=len(q.positive_term_ids),
                        **_source(q.provenance),
                    )
                    .returning(m.IngredientProteinReview.__table__)
                )
                .mappings()
                .one()
            )
            for model, ids in [
                (m.IngredientProteinReviewTerm, q.covered_term_ids),
                (m.IngredientProteinAssignment, q.positive_term_ids),
            ]:
                for tid in ids:
                    s.execute(
                        insert(model).values(
                            review_id=row["id"],
                            ingredient_id=q.ingredient_id,
                            term_id=tid,
                            term_kind="PROTEIN",
                        )
                    )
            s.execute(text("SELECT menuto_feature_check_review(:id,true)"), {"id": row["id"]})
            _review(s, row)
            return self._receipt(row, False)

    def _receipt(self, row, replayed):
        return c.IngredientProteinWriteReceipt(
            **{
                k: row[k] for k in ("ingredient_id", "stream_id", "source_sequence", "command_hash")
            },
            review_id=row["id"],
            replayed=replayed,
        )


def lock_ingredient_protein_frontier(session):
    """Catalog-before-Recipes fence for explicit MAIN_PROTEIN publication only."""
    return session.scalar(select(m.IngredientProteinFrontier.generation).with_for_update())
