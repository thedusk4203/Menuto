"""Owned MTR-046A relational sources; cache writes are database-controlled."""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
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


class CulinaryFeatureFrontier(Base):
    __table__ = Table(
        "culinary_feature_frontier",
        Base.metadata,
        Column("source", String(20), primary_key=True),
        Column("generation", BigInteger, nullable=False),
        check("source='RECIPES' AND generation>=0", "singleton"),
    )


class CulinaryFeatureApplicability(Base):
    __table__ = Table(
        "culinary_feature_applicabilities",
        Base.metadata,
        uid("id", primary=True),
        Column(
            "recipe_version_id",
            Uuid,
            ForeignKey("recipe_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        word("dimension", 20),
        word("scope", 30),
        word("key_hash", 64),
        word("assembly_xid", 30),
        count("declared_tier_count"),
        Column("head_revision_no", Integer, nullable=False, server_default=text("-1")),
        uid("head_review_id", nullable=True),
        UniqueConstraint("recipe_version_id", "dimension", "key_hash"),
        UniqueConstraint("id", "recipe_version_id", "dimension"),
        UniqueConstraint("id", "recipe_version_id"),
        fk(
            ["head_review_id", "id", "head_revision_no"],
            "culinary_feature_reviews",
            ["id", "applicability_id", "revision_no"],
        ),
        check(
            "dimension IN ('METHOD','FLAVOR','MAIN_PROTEIN') AND "
            "scope IN ('RECIPE_COOKING_CONTEXT','EXACT_PATH','REVIEWED_SCOPE') AND "
            "((dimension='METHOD' AND scope='RECIPE_COOKING_CONTEXT' AND declared_tier_count=0) "
            "OR (dimension!='METHOD' AND scope!='RECIPE_COOKING_CONTEXT' "
            "AND declared_tier_count>0))",
            "scope",
        ),
        check("key_hash ~ '^[a-f0-9]{64}$'", "hash"),
        check(
            "(head_revision_no=-1 AND head_review_id IS NULL) OR "
            "(head_revision_no>=0 AND head_review_id IS NOT NULL)",
            "head",
        ),
    )


Index(
    "uq_culinary_method_context",
    CulinaryFeatureApplicability.recipe_version_id,
    unique=True,
    postgresql_where=text("dimension='METHOD'"),
)


class CulinaryFeatureApplicabilitySlot(Base):
    __table__ = Table(
        "culinary_feature_applicability_slots",
        Base.metadata,
        uid("applicability_id", primary=True),
        uid("recipe_version_id"),
        uid("requirement_id", primary=True),
        word("choice", 30),
        uid("selected_rule_id", nullable=True),
        word("preparation", 30),
        uid("transformation_id", nullable=True),
        word("adjustment", 30),
        UniqueConstraint("applicability_id", "recipe_version_id", "requirement_id"),
        fk(
            ["applicability_id", "recipe_version_id"],
            "culinary_feature_applicabilities",
            ["id", "recipe_version_id"],
        ),
        fk(
            ["requirement_id", "recipe_version_id"],
            "recipe_ingredients",
            ["id", "recipe_version_id"],
        ),
        fk(
            ["selected_rule_id", "recipe_version_id"],
            "recipe_variant_rules",
            ["id", "recipe_version_id"],
        ),
        fk(
            ["transformation_id", "recipe_version_id"],
            "preparation_transformations",
            ["id", "recipe_version_id"],
        ),
        check(
            "choice IN ('BASE','RULE','ANY_AUTHORED_CHOICE') AND "
            "((choice='RULE' AND selected_rule_id IS NOT NULL) OR "
            "(choice!='RULE' AND selected_rule_id IS NULL))",
            "choice",
        ),
        check(
            "preparation IN ('NONE','TRANSFORMATION','ANY_AUTHORED_PATH_CONTEXT') AND "
            "((preparation='TRANSFORMATION' AND transformation_id IS NOT NULL) OR "
            "(preparation!='TRANSFORMATION' AND transformation_id IS NULL))",
            "preparation",
        ),
        check("adjustment IN ('ZERO_ONLY','AUTHORED_ENVELOPE')", "adjustment"),
    )


class CulinaryFeatureApplicabilityTier(Base):
    __table__ = Table(
        "culinary_feature_applicability_tiers",
        Base.metadata,
        uid("applicability_id", primary=True),
        uid("recipe_version_id"),
        uid("tier_id", primary=True),
        fk(
            ["applicability_id", "recipe_version_id"],
            "culinary_feature_applicabilities",
            ["id", "recipe_version_id"],
        ),
        fk(["tier_id", "recipe_version_id"], "recipe_portion_tiers", ["id", "recipe_version_id"]),
    )


class CulinaryFeatureReview(Base):
    __table__ = Table(
        "culinary_feature_reviews",
        Base.metadata,
        *review_columns(),
        uid("applicability_id"),
        uid("recipe_version_id"),
        word("dimension", 20),
        count("declared_support_count"),
        Column("catalog_frontier_at_write", BigInteger, nullable=True),
        *review_checks(),
        check(
            "(revision_no=0 AND command_kind='REGISTER' AND action='REPLACE') OR "
            "(revision_no>0 AND command_kind=action)",
            "command_kind",
        ),
        check(
            "declared_support_count>=0 AND ((dimension='MAIN_PROTEIN' "
            "AND catalog_frontier_at_write IS NOT NULL AND catalog_frontier_at_write>=0) OR "
            "(dimension IN ('METHOD','FLAVOR') AND catalog_frontier_at_write IS NULL "
            "AND declared_support_count=0)) AND "
            "(action!='RETRACT' OR declared_support_count=0)",
            "dependency",
        ),
        UniqueConstraint("applicability_id", "revision_no"),
        UniqueConstraint("id", "applicability_id", "revision_no"),
        UniqueConstraint("id", "applicability_id", "recipe_version_id", "dimension"),
        fk(
            ["applicability_id", "recipe_version_id", "dimension"],
            "culinary_feature_applicabilities",
            ["id", "recipe_version_id", "dimension"],
        ),
        fk(
            ["predecessor_id", "applicability_id", "predecessor_revision_no"],
            "culinary_feature_reviews",
            ["id", "applicability_id", "revision_no"],
        ),
    )


class CulinaryFeatureReviewTerm(Base):
    __table__ = Table(
        "culinary_feature_review_terms",
        Base.metadata,
        uid("review_id", primary=True),
        uid("applicability_id"),
        uid("recipe_version_id"),
        word("dimension", 20),
        uid("term_id", primary=True),
        word("term_kind", 20),
        UniqueConstraint(
            "review_id", "applicability_id", "recipe_version_id", "dimension", "term_id"
        ),
        fk(
            ["review_id", "applicability_id", "recipe_version_id", "dimension"],
            "culinary_feature_reviews",
            ["id", "applicability_id", "recipe_version_id", "dimension"],
        ),
        fk(["term_id", "term_kind"], "affinity_feature_terms", ["id", "kind"]),
        check(
            "(dimension='MAIN_PROTEIN' AND term_kind='PROTEIN') OR "
            "(dimension IN ('METHOD','FLAVOR') AND term_kind=dimension)",
            "kind",
        ),
    )


class CulinaryFeatureAssignment(Base):
    __table__ = Table(
        "culinary_feature_assignments",
        Base.metadata,
        uid("review_id", primary=True),
        uid("applicability_id"),
        uid("recipe_version_id"),
        word("dimension", 20),
        uid("term_id", primary=True),
        word("term_kind", 20),
        UniqueConstraint(
            "review_id", "applicability_id", "recipe_version_id", "dimension", "term_id"
        ),
        fk(
            ["review_id", "applicability_id", "recipe_version_id", "dimension", "term_id"],
            "culinary_feature_review_terms",
            ["review_id", "applicability_id", "recipe_version_id", "dimension", "term_id"],
        ),
        fk(["term_id", "term_kind"], "affinity_feature_terms", ["id", "kind"]),
        check(
            "(dimension='MAIN_PROTEIN' AND term_kind='PROTEIN') OR "
            "(dimension IN ('METHOD','FLAVOR') AND term_kind=dimension)",
            "kind",
        ),
    )


class CulinaryFeatureMainProteinSupport(Base):
    __table__ = Table(
        "culinary_feature_main_protein_support",
        Base.metadata,
        uid("review_id", primary=True),
        uid("applicability_id"),
        uid("recipe_version_id"),
        word("dimension", 20),
        uid("term_id", primary=True),
        uid("requirement_id", primary=True),
        uid("ingredient_id"),
        uid("catalog_review_id"),
        check("dimension='MAIN_PROTEIN'", "dimension"),
        fk(
            ["review_id", "applicability_id", "recipe_version_id", "dimension", "term_id"],
            "culinary_feature_assignments",
            ["review_id", "applicability_id", "recipe_version_id", "dimension", "term_id"],
        ),
        fk(
            ["applicability_id", "recipe_version_id", "requirement_id"],
            "culinary_feature_applicability_slots",
            ["applicability_id", "recipe_version_id", "requirement_id"],
        ),
        fk(
            ["catalog_review_id", "ingredient_id", "term_id"],
            "ingredient_protein_assignments",
            ["review_id", "ingredient_id", "term_id"],
        ),
    )
