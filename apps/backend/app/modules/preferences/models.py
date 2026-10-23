"""Member-owned raw declarations; mutable heads are database-maintained caches only."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base, IdentityMixin, ProvenanceMixin


class MemberPreferenceFrontier(Base):
    __tablename__ = "member_preference_frontiers"
    __table_args__ = (
        ForeignKeyConstraint(
            ["household_id", "member_id"],
            ["household_members.household_id", "household_members.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("generation>=0", name="generation"),
    )
    household_id: Mapped[UUID] = mapped_column(primary_key=True)
    member_id: Mapped[UUID] = mapped_column(primary_key=True)
    generation: Mapped[int] = mapped_column(BigInteger)


class MemberPreferenceStream(IdentityMixin, Base):
    __tablename__ = "member_preference_streams"
    __table_args__ = (
        UniqueConstraint("id", "household_id", "member_id"),
        ForeignKeyConstraint(
            ["household_id", "member_id"],
            ["household_members.household_id", "household_members.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["feature_term_id", "target_kind"],
            ["affinity_feature_terms.id", "affinity_feature_terms.kind"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["head_id", "id", "household_id", "member_id"],
            [
                "member_preference_declarations.id",
                "member_preference_declarations.stream_id",
                "member_preference_declarations.household_id",
                "member_preference_declarations.member_id",
            ],
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
            name="fk_preference_stream_head",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "(target_kind='INGREDIENT' AND ingredient_id IS NOT NULL AND recipe_id IS NULL "
            "AND feature_term_id IS NULL) OR "
            "(target_kind='DIRECT_RECIPE' AND recipe_id IS NOT NULL "
            "AND ingredient_id IS NULL AND feature_term_id IS NULL) OR "
            "(target_kind IN ('PROTEIN','METHOD','FLAVOR') AND feature_term_id IS NOT NULL "
            "AND ingredient_id IS NULL AND recipe_id IS NULL)",
            name="target_shape",
        ),
        CheckConstraint(
            "head_revision>=-1 AND ((head_revision=-1)=(head_id IS NULL))", name="head"
        ),
        Index(
            "uq_preference_ingredient",
            "household_id",
            "member_id",
            "ingredient_id",
            unique=True,
            postgresql_where=text("target_kind='INGREDIENT'"),
        ),
        Index(
            "uq_preference_recipe",
            "household_id",
            "member_id",
            "recipe_id",
            unique=True,
            postgresql_where=text("target_kind='DIRECT_RECIPE'"),
        ),
        *[
            Index(
                "uq_preference_" + kind.lower(),
                "household_id",
                "member_id",
                "feature_term_id",
                unique=True,
                postgresql_where=text("target_kind='" + kind + "'"),
            )
            for kind in ("PROTEIN", "METHOD", "FLAVOR")
        ],
    )
    household_id: Mapped[UUID]
    member_id: Mapped[UUID]
    target_kind: Mapped[str] = mapped_column(String(20))
    ingredient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT")
    )
    recipe_id: Mapped[UUID | None] = mapped_column(ForeignKey("recipes.id", ondelete="RESTRICT"))
    feature_term_id: Mapped[UUID | None]
    head_revision: Mapped[int] = mapped_column(server_default=text("-1"))
    head_id: Mapped[UUID | None]


class MemberPreferenceDeclaration(ProvenanceMixin, Base):
    __tablename__ = "member_preference_declarations"
    __table_args__ = (
        UniqueConstraint("id", "stream_id", "household_id", "member_id"),
        UniqueConstraint("stream_id", "revision_no"),
        UniqueConstraint("household_id", "member_id", "member_sequence"),
        UniqueConstraint("household_id", "actor_user_id", "source_system", "idempotency_key"),
        UniqueConstraint("household_id", "source_system", "external_record_id", "source_version"),
        ForeignKeyConstraint(
            ["stream_id", "household_id", "member_id"],
            [
                "member_preference_streams.id",
                "member_preference_streams.household_id",
                "member_preference_streams.member_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["predecessor_id", "stream_id", "household_id", "member_id"],
            [
                "member_preference_declarations.id",
                "member_preference_declarations.stream_id",
                "member_preference_declarations.household_id",
                "member_preference_declarations.member_id",
            ],
            ondelete="RESTRICT",
        ),
        CheckConstraint("revision_no>=0 AND member_sequence>0", name="sequence"),
        CheckConstraint("(revision_no=0)=(predecessor_id IS NULL)", name="predecessor"),
        CheckConstraint(
            "authorship IN ('SELF','AUTHORIZED_REPRESENTATIVE') "
            "AND actor_role IN ('OWNER','EDITOR')",
            name="authorship",
        ),
        CheckConstraint(
            "(action='SET' AND value IN ('LIKE','DISLIKE','NEUTRAL') AND value IS NOT NULL "
            "AND ((revision_no=0 AND reason='INITIAL') OR (revision_no>0 AND "
            "reason IN ('INPUT_CORRECTION','PREFERENCE_CHANGED')))) OR "
            "(action='RETRACT' AND value IS NULL AND revision_no>0 AND reason='RETRACTED')",
            name="assertion",
        ),
        CheckConstraint(
            "isfinite(occurred_at) AND isfinite(recorded_at) AND "
            "isfinite(observed_at) AND occurred_at<=observed_at "
            "AND observed_at<=recorded_at",
            name="times",
        ),
        CheckConstraint("source_kind='USER' AND source='EXPLICIT_DECLARATION'", name="source"),
        CheckConstraint(
            "source_system ~ '^[A-Za-z0-9_.:-]+$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$'",
            name="identifiers",
        ),
        CheckConstraint(
            "length(trim(external_record_id))>0 AND length(trim(source_version))>0 "
            "AND external_record_id !~ '[[:cntrl:]]' "
            "AND source_version !~ '[[:cntrl:]]'",
            name="source_identity",
        ),
        CheckConstraint("content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'", name="hash"),
        CheckConstraint("command_fingerprint ~ '^[a-f0-9]{64}$'", name="fingerprint"),
        CheckConstraint(
            "source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' "
            "AND source_uri !~ '^https?://[^/]*@' "
            "AND source_uri !~ '[[:cntrl:]]')",
            name="uri",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    stream_id: Mapped[UUID]
    household_id: Mapped[UUID]
    member_id: Mapped[UUID]
    revision_no: Mapped[int]
    predecessor_id: Mapped[UUID | None]
    actor_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    authorship: Mapped[str] = mapped_column(String(30))
    actor_role: Mapped[str] = mapped_column(String(20))
    action: Mapped[str] = mapped_column(String(10))
    value: Mapped[str | None] = mapped_column(String(10))
    reason: Mapped[str] = mapped_column(String(30))
    source: Mapped[str] = mapped_column(String(30))
    occurred_at: Mapped[datetime]
    recorded_at: Mapped[datetime]
    member_sequence: Mapped[int] = mapped_column(BigInteger)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    command_fingerprint: Mapped[str] = mapped_column(String(64))
