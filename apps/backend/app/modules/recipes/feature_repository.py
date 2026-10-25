"""Recipe-owned classification companion writes/reads, no preference or execution truth."""

from uuid import uuid4

from pydantic import TypeAdapter
from sqlalchemy import insert, select, text

from app.modules.recipes import contracts as c
from app.modules.recipes import feature_models as m
from app.modules.recipes.feature_resolution import validate_applicability
from app.modules.recipes.repository import RecipeRepository


def _key(session, aid):
    return TypeAdapter(c.CulinaryFeatureApplicabilityKey).validate_python(
        session.scalar(text("SELECT menuto_feature_key(:a)"), {"a": aid})
    )


def culinary_feature_frontier(session):
    return session.scalar(select(m.CulinaryFeatureFrontier.generation))


def culinary_feature_sources(session, recipe_version_id, dimensions):
    scopes = []
    for row in session.execute(
        select(m.CulinaryFeatureApplicability.__table__)
        .where(
            m.CulinaryFeatureApplicability.recipe_version_id == recipe_version_id,
            m.CulinaryFeatureApplicability.dimension.in_(dimensions),
        )
        .order_by(m.CulinaryFeatureApplicability.id)
    ).mappings():
        reviews = []
        for r in session.execute(
            select(m.CulinaryFeatureReview.__table__)
            .where(m.CulinaryFeatureReview.applicability_id == row["id"])
            .order_by(m.CulinaryFeatureReview.revision_no)
        ).mappings():
            reviews.append(
                c.CulinaryFeatureReviewFact(
                    **{
                        k: r[k]
                        for k in (
                            "id",
                            "applicability_id",
                            "recipe_version_id",
                            "dimension",
                            "revision_no",
                            "predecessor_revision_no",
                            "source_sequence",
                            "reviewer_user_id",
                            "recorded_at",
                            "command_hash",
                        )
                    },
                    command=session.scalar(
                        text("SELECT menuto_feature_review_command(:id,false)"), {"id": r["id"]}
                    ),
                )
            )
        if (
            not reviews
            or reviews[-1].id != row["head_review_id"]
            or reviews[-1].revision_no != row["head_revision_no"]
        ):
            raise ValueError("Incomplete Recipe classification head")
        scopes.append(
            c.CulinaryFeatureScopeFact(
                id=row["id"], key=_key(session, row["id"]), reviews=tuple(reviews)
            )
        )
    return tuple(scopes)


class CulinaryFeatureService:
    def __init__(self, session, *, actor_user_id):
        self.session, self.actor_user_id = session, actor_user_id

    def _lock(self, dimension):
        if self.session.connection().get_isolation_level() != "READ COMMITTED":
            raise ValueError("Feature writes require READ COMMITTED")
        if dimension == "MAIN_PROTEIN":
            # Coordinate exclusively through Catalog's public source fence.
            from app.modules.catalog.public import lock_ingredient_protein_frontier

            lock_ingredient_protein_frontier(self.session)
        self.session.execute(select(m.CulinaryFeatureFrontier).with_for_update()).all()

    def _retry(self, q):
        old = (
            self.session.execute(
                select(m.CulinaryFeatureReview.__table__).where(
                    m.CulinaryFeatureReview.source_system == q.provenance.source_system,
                    m.CulinaryFeatureReview.idempotency_key == q.idempotency_key,
                )
            )
            .mappings()
            .one_or_none()
        )
        if old and old["command_hash"] != q.fingerprint(self.actor_user_id):
            raise ValueError("IDEMPOTENCY_CONFLICT")
        return self._receipt(old, True) if old else None

    def write(self, command):
        q = TypeAdapter(c.CulinaryFeatureWriteCommand).validate_python(command.model_dump())
        with self.session.begin_nested():
            self._lock(q.dimension)
            prior = self._retry(q)
            return prior if prior else self._append(q)

    def rekey(self, retract, register):
        """Atomic same-version/path-dimension retire+register, exact pair retry only."""
        adapter = TypeAdapter(c.CulinaryFeatureWriteCommand)
        a, b = (adapter.validate_python(q.model_dump()) for q in (retract, register))
        if (
            a.command_kind != "RETRACT"
            or b.command_kind != "REGISTER"
            or a.dimension == "METHOD"
            or a.dimension != b.dimension
            or a.recipe_version_id != b.recipe_version_id
            or a.idempotency_key == b.idempotency_key
            or b.expected_recipe_frontier != a.expected_recipe_frontier + 1
        ):
            raise ValueError("Invalid atomic scope rekey pair")
        with self.session.begin_nested():
            self._lock(a.dimension)
            x, y = self._retry(a), self._retry(b)
            if bool(x) != bool(y):
                raise ValueError("Conflicting partial rekey retry")
            if x:
                return x, y
            return self._append(a), self._append(b)

    def _append(self, q):
        s = self.session
        if culinary_feature_frontier(s) != q.expected_recipe_frontier:
            raise ValueError("Stale Recipes frontier")
        if q.dimension == "MAIN_PROTEIN":
            from app.modules.catalog.public import ingredient_protein_frontier

            if ingredient_protein_frontier(s) != q.expected_catalog_frontier:
                raise ValueError("Stale Catalog frontier")
        if q.command_kind == "REGISTER":
            validate_applicability(RecipeRepository(s).version(q.recipe_version_id), q.key)
            aid = uuid4()
            s.execute(
                insert(m.CulinaryFeatureApplicability).values(
                    id=aid,
                    recipe_version_id=q.recipe_version_id,
                    dimension=q.dimension,
                    scope=q.key.scope,
                    key_hash=q.key.fingerprint(),
                    declared_tier_count=len(getattr(q.key, "tier_ids", ())),
                )
            )
            for tid in getattr(q.key, "tier_ids", ()):
                s.execute(
                    insert(m.CulinaryFeatureApplicabilityTier).values(
                        applicability_id=aid, recipe_version_id=q.recipe_version_id, tier_id=tid
                    )
                )
            for slot in getattr(q.key, "slots", ()):
                s.execute(
                    insert(m.CulinaryFeatureApplicabilitySlot).values(
                        applicability_id=aid,
                        recipe_version_id=q.recipe_version_id,
                        **slot.model_dump(),
                    )
                )
        else:
            aid = q.applicability_id
        provenance = q.provenance.model_dump(exclude={"kind", "source_uri"})
        row = (
            s.execute(
                insert(m.CulinaryFeatureReview)
                .values(
                    id=uuid4(),
                    applicability_id=aid,
                    recipe_version_id=q.recipe_version_id,
                    dimension=q.dimension,
                    revision_no=q.expected_revision_no + 1,
                    predecessor_revision_no=q.expected_revision_no
                    if q.expected_revision_no >= 0
                    else None,
                    predecessor_id=q.predecessor_id,
                    source_sequence=q.expected_recipe_frontier + 1,
                    action="RETRACT" if q.command_kind == "RETRACT" else "REPLACE",
                    command_kind=q.command_kind,
                    coverage=q.coverage,
                    reviewer_user_id=self.actor_user_id,
                    idempotency_key=q.idempotency_key,
                    command_hash=q.fingerprint(self.actor_user_id),
                    correction_reason=q.correction_reason,
                    declared_covered_count=len(q.covered_term_ids),
                    declared_assigned_count=len(q.positive_term_ids),
                    declared_support_count=len(q.supports),
                    catalog_frontier_at_write=getattr(q, "expected_catalog_frontier", None),
                    source_kind=q.provenance.kind,
                    source_uri=str(q.provenance.source_uri) if q.provenance.source_uri else None,
                    **provenance,
                )
                .returning(m.CulinaryFeatureReview.__table__)
            )
            .mappings()
            .one()
        )
        ctx = dict(
            review_id=row["id"],
            applicability_id=aid,
            recipe_version_id=q.recipe_version_id,
            dimension=q.dimension,
        )
        kind = "PROTEIN" if q.dimension == "MAIN_PROTEIN" else q.dimension
        for model, ids in [
            (m.CulinaryFeatureReviewTerm, q.covered_term_ids),
            (m.CulinaryFeatureAssignment, q.positive_term_ids),
        ]:
            for tid in ids:
                s.execute(insert(model).values(**ctx, term_id=tid, term_kind=kind))
        for support in q.supports:
            s.execute(
                insert(m.CulinaryFeatureMainProteinSupport).values(**ctx, **support.model_dump())
            )
        s.execute(text("SELECT menuto_feature_check_review(:id,false)"), {"id": row["id"]})
        return self._receipt(row, False)

    def _receipt(self, row, replayed):
        return c.CulinaryFeatureWriteReceipt(
            **{
                k: row[k]
                for k in (
                    "recipe_version_id",
                    "applicability_id",
                    "dimension",
                    "source_sequence",
                    "command_hash",
                )
            },
            review_id=row["id"],
            replayed=replayed,
        )
