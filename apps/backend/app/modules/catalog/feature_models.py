"""Owned MTR-046A relational sources; cache writes are database-controlled."""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Table,
    UniqueConstraint,
    Uuid,
    text,
)

from app.shared.db import Base


def fk(cols, table, targets):
    return ForeignKeyConstraint(
        cols,
        [f"{table}.{x}" for x in targets],
        ondelete="RESTRICT",
        **(
            dict(
                deferrable=True, initially="DEFERRED", use_alter=True, name="fk_" + table + "_head"
            )
            if cols[0] == "head_review_id"
            else {}
        ),
    )


def uid(name, *, primary=False, nullable=False):
    return Column(name, Uuid, primary_key=primary, nullable=nullable)


def count(name):
    return Column(name, Integer, nullable=False)


def word(name, length=100, *, nullable=False):
    return Column(name, String(length), nullable=nullable)


def check(sql, name):
    return CheckConstraint(sql, name=name)


def source_columns():
    return [
        word("source_kind", 30),
        word("source_system"),
        word("external_record_id", 2048),
        word("source_version", 200),
        word("source_uri", 2048, nullable=True),
        word("content_hash", 64, nullable=True),
        Column("observed_at", DateTime(timezone=True), nullable=False),
    ]


def source_checks():
    return [
        check("source_kind IN ('USER','REVIEWED_REFERENCE')", "source_kind"),
        check("source_system ~ '^[A-Za-z0-9_.:-]+$'", "source_system"),
        check(
            "length(trim(external_record_id))>0 AND length(trim(source_version))>0 "
            "AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'",
            "source_identity",
        ),
        check(
            "isfinite(observed_at) AND isfinite(recorded_at) AND observed_at<=recorded_at", "time"
        ),
        check("content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'", "content_hash"),
        check(
            "source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' "
            "AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')",
            "uri",
        ),
        UniqueConstraint("source_system", "external_record_id", "source_version"),
        UniqueConstraint("source_system", "idempotency_key"),
        UniqueConstraint("source_sequence"),
    ]


def review_columns():
    return [
        uid("id", primary=True),
        count("revision_no"),
        uid("predecessor_id", nullable=True),
        Column("predecessor_revision_no", Integer, nullable=True),
        Column("source_sequence", BigInteger, nullable=False),
        word("action", 20),
        word("command_kind", 20),
        word("coverage", 20, nullable=True),
        Column(
            "reviewer_user_id", Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        word("idempotency_key"),
        word("command_hash", 64),
        word("assembly_xid", 30),
        Column("recorded_at", DateTime(timezone=True), nullable=False),
        word("correction_reason", 200, nullable=True),
        count("declared_covered_count"),
        count("declared_assigned_count"),
        *source_columns(),
    ]


def review_checks():
    return [
        *source_checks(),
        check("revision_no>=0 AND source_sequence>0", "sequence"),
        check(
            "(revision_no=0 AND predecessor_id IS NULL AND predecessor_revision_no IS NULL "
            "AND action='REPLACE') OR (revision_no>0 AND predecessor_id IS NOT NULL "
            "AND predecessor_revision_no=revision_no-1 AND correction_reason IS NOT NULL "
            "AND length(trim(correction_reason))>0)",
            "predecessor",
        ),
        check(
            "action IN ('REPLACE','RETRACT') AND ((action='REPLACE' "
            "AND coverage IS NOT NULL AND coverage IN ('PARTIAL','COMPLETE') "
            "AND declared_covered_count>0) OR (action='RETRACT' AND coverage IS NULL "
            "AND declared_covered_count=0 AND declared_assigned_count=0))",
            "shape",
        ),
        check(
            "declared_assigned_count>=0 AND declared_assigned_count<=declared_covered_count",
            "counts",
        ),
        check(
            "command_hash ~ '^[a-f0-9]{64}$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$'",
            "command_identity",
        ),
    ]


class IngredientProteinFrontier(Base):
    __table__ = Table(
        "ingredient_protein_frontier",
        Base.metadata,
        Column("source", String(20), primary_key=True),
        Column("generation", BigInteger, nullable=False),
        check("source='CATALOG' AND generation>=0", "singleton"),
    )


class IngredientProteinStream(Base):
    __table__ = Table(
        "ingredient_protein_streams",
        Base.metadata,
        uid("id", primary=True),
        Column(
            "ingredient_id", Uuid, ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False
        ),
        Column("head_revision_no", Integer, nullable=False, server_default=text("-1")),
        uid("head_review_id", nullable=True),
        word("assembly_xid", 30),
        UniqueConstraint("ingredient_id"),
        UniqueConstraint("id", "ingredient_id"),
        fk(
            ["head_review_id", "id", "head_revision_no"],
            "ingredient_protein_reviews",
            ["id", "stream_id", "revision_no"],
        ),
        check(
            "(head_revision_no=-1 AND head_review_id IS NULL) OR "
            "(head_revision_no>=0 AND head_review_id IS NOT NULL)",
            "head",
        ),
    )


class IngredientProteinReview(Base):
    __table__ = Table(
        "ingredient_protein_reviews",
        Base.metadata,
        *review_columns(),
        uid("stream_id"),
        uid("ingredient_id"),
        *review_checks(),
        check("command_kind=action", "command_kind"),
        UniqueConstraint("stream_id", "revision_no"),
        UniqueConstraint("id", "stream_id", "revision_no"),
        UniqueConstraint("id", "ingredient_id"),
        fk(["stream_id", "ingredient_id"], "ingredient_protein_streams", ["id", "ingredient_id"]),
        fk(
            ["predecessor_id", "stream_id", "predecessor_revision_no"],
            "ingredient_protein_reviews",
            ["id", "stream_id", "revision_no"],
        ),
    )


class IngredientProteinReviewTerm(Base):
    __table__ = Table(
        "ingredient_protein_review_terms",
        Base.metadata,
        uid("review_id", primary=True),
        uid("ingredient_id"),
        uid("term_id", primary=True),
        word("term_kind", 20),
        check("term_kind='PROTEIN'", "kind"),
        UniqueConstraint("review_id", "ingredient_id", "term_id"),
        fk(["review_id", "ingredient_id"], "ingredient_protein_reviews", ["id", "ingredient_id"]),
        fk(["term_id", "term_kind"], "affinity_feature_terms", ["id", "kind"]),
    )


class IngredientProteinAssignment(Base):
    __table__ = Table(
        "ingredient_protein_assignments",
        Base.metadata,
        uid("review_id", primary=True),
        uid("ingredient_id"),
        uid("term_id", primary=True),
        word("term_kind", 20),
        check("term_kind='PROTEIN'", "kind"),
        UniqueConstraint("review_id", "ingredient_id", "term_id"),
        fk(
            ["review_id", "ingredient_id", "term_id"],
            "ingredient_protein_review_terms",
            ["review_id", "ingredient_id", "term_id"],
        ),
    )
