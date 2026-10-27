"""Explicit member source commands and coherent capture; no learning or utility."""

from uuid import uuid4

from sqlalchemy import insert, select, text

from app.domain.units import Provenance
from app.modules.catalog.public import affinity_feature_terms
from app.modules.households.public import lock_household_actor, member_identities
from app.modules.preferences import contracts as c
from app.modules.preferences import models as m


def _target(row):
    kind = row["target_kind"]
    field = {"INGREDIENT": "ingredient_id", "DIRECT_RECIPE": "recipe_id"}.get(
        kind, "feature_term_id"
    )
    return {"kind": kind, field: row[field]}


def _fact(row, stream):
    fields = {
        k: row[k]
        for k in (
            "household_id",
            "member_id",
            "actor_user_id",
            "authorship",
            "action",
            "value",
            "reason",
            "occurred_at",
            "idempotency_key",
            "source",
            "predecessor_id",
        )
    }
    fields.update(
        expected_revision=row["revision_no"] - 1,
        target=_target(stream),
        provenance=Provenance(
            kind=row["source_kind"],
            **{
                k: row[k]
                for k in (
                    "source_system",
                    "external_record_id",
                    "source_version",
                    "source_uri",
                    "content_hash",
                    "observed_at",
                )
            },
        ),
    )
    return c.MemberPreferenceDeclarationFact(
        command=fields,
        **{
            k: row[k]
            for k in (
                "id",
                "stream_id",
                "revision_no",
                "member_sequence",
                "recorded_at",
                "actor_role",
                "command_fingerprint",
            )
        },
    )


class PreferenceService:
    """Caller owns transaction; actor comes from authenticated application context."""

    def __init__(self, session, *, actor_user_id):
        self.session = session
        self.actor_user_id = actor_user_id

    def _access(self, household_id, member_id, *, write=False, authorship=None):
        if member_id not in {i.member_id for i in member_identities(self.session, household_id)}:
            raise LookupError("Unknown household member")
        linked, role = lock_household_actor(
            self.session, household_id, self.actor_user_id, write=write
        )
        if write and authorship == "SELF" and linked != member_id:
            raise PermissionError("SELF actor differs from subject")
        if write and authorship == "AUTHORIZED_REPRESENTATIVE" and linked == member_id:
            raise PermissionError("AUTHORIZED_REPRESENTATIVE actor equals subject; use SELF")
        return role

    def write(self, command):
        command = c.PreferenceWriteCommand.model_validate(command.model_dump())
        if command.actor_user_id != self.actor_user_id:
            raise PermissionError("Command actor differs from authenticated principal")
        self._access(
            command.household_id, command.member_id, write=True, authorship=command.authorship
        )
        s = self.session
        for key in (
            f"preference.retry:{command.household_id}:{command.actor_user_id}:"
            f"{command.provenance.source_system}:{command.idempotency_key}",
            f"preference.member:{command.household_id}:{command.member_id}",
        ):
            s.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"), {"key": key})
        table = m.MemberPreferenceDeclaration.__table__
        streams = m.MemberPreferenceStream.__table__
        existing = (
            s.execute(
                select(table).where(
                    table.c.household_id == command.household_id,
                    table.c.actor_user_id == command.actor_user_id,
                    table.c.source_system == command.provenance.source_system,
                    table.c.idempotency_key == command.idempotency_key,
                )
            )
            .mappings()
            .one_or_none()
        )
        if existing:
            stream = (
                s.execute(select(streams).where(streams.c.id == existing["stream_id"]))
                .mappings()
                .one()
            )
            receipt = _fact(existing, stream)
            if receipt.command.fingerprint() != command.fingerprint():
                raise ValueError("Idempotency key reused with different command")
            return receipt
        target = command.target.model_dump()
        kind = target.pop("kind")
        stream = (
            s.execute(
                select(streams)
                .where(
                    streams.c.household_id == command.household_id,
                    streams.c.member_id == command.member_id,
                    streams.c.target_kind == kind,
                    *(streams.c[k] == v for k, v in target.items()),
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if stream is None:
            if command.expected_revision != -1:
                raise ValueError("Stale preference revision")
            stream = (
                s.execute(
                    insert(streams)
                    .values(
                        id=uuid4(),
                        household_id=command.household_id,
                        member_id=command.member_id,
                        target_kind=kind,
                        **target,
                    )
                    .returning(streams)
                )
                .mappings()
                .one()
            )
        if (stream["head_revision"], stream["head_id"]) != (
            command.expected_revision,
            command.predecessor_id,
        ):
            raise ValueError("Stale preference revision/predecessor")
        fields = command.model_dump(
            exclude={
                "contract_version",
                "target",
                "expected_revision",
                "provenance",
            }
        )
        fields.update(command.provenance.model_dump(exclude={"kind", "source_uri"}))
        fields.update(
            source_kind="USER",
            source_uri=str(command.provenance.source_uri)
            if command.provenance.source_uri
            else None,
            id=uuid4(),
            stream_id=stream["id"],
            revision_no=command.expected_revision + 1,
        )
        row = s.execute(insert(table).values(**fields).returning(table)).mappings().one()
        return _fact(row, stream)

    def snapshot(self, household_id, member_id):
        s = self.session
        if (
            s.connection().get_isolation_level() not in {"REPEATABLE READ", "SERIALIZABLE"}
            or s.scalar(text("SHOW transaction_read_only")) != "on"
            or s.new
            or s.dirty
            or s.deleted
        ):
            raise ValueError("Preference capture requires clean read-only RR/SERIALIZABLE")
        # Read-only capture cannot take row locks; canonical membership read is coherent in RR.
        identities = {i.member_id for i in member_identities(s, household_id)}
        if member_id not in identities:
            raise LookupError("Unknown household member")
        access = s.execute(
            text("SELECT role FROM memberships WHERE household_id=:h AND user_id=:a"),
            {"h": household_id, "a": self.actor_user_id},
        ).scalar_one_or_none()
        if access is None:
            raise PermissionError("Household actor access denied")
        frontier = s.scalar(
            select(m.MemberPreferenceFrontier.generation).where(
                m.MemberPreferenceFrontier.household_id == household_id,
                m.MemberPreferenceFrontier.member_id == member_id,
            )
        )
        streams = {
            r["id"]: r
            for r in s.execute(
                select(m.MemberPreferenceStream.__table__).where(
                    m.MemberPreferenceStream.household_id == household_id,
                    m.MemberPreferenceStream.member_id == member_id,
                )
            ).mappings()
        }
        rows = tuple(
            _fact(r, streams[r["stream_id"]])
            for r in s.execute(
                select(m.MemberPreferenceDeclaration.__table__)
                .where(
                    m.MemberPreferenceDeclaration.household_id == household_id,
                    m.MemberPreferenceDeclaration.member_id == member_id,
                )
                .order_by(m.MemberPreferenceDeclaration.member_sequence)
            ).mappings()
        )
        if set(streams) != {r.stream_id for r in rows}:
            raise ValueError("Incomplete preference streams")
        ids = {
            r.command.target.feature_term_id
            for r in rows
            if isinstance(r.command.target, c.FeaturePreferenceTarget)
        }
        return c.ExplicitMemberPreferenceSnapshot(
            household_id=household_id,
            member_id=member_id,
            frontier=frontier or 0,
            captured_at=s.scalar(text("SELECT clock_timestamp()")),
            declarations=rows,
            feature_terms=affinity_feature_terms(s, ids),
        )


def capture_explicit_target_affinity_sources(session, request, *, actor_user_id):
    """Additive lazy capture facade; caller owns the read-only RR/SERIALIZABLE transaction."""
    from app.modules.preferences.profile_capture import capture_explicit_target_affinity_sources

    return capture_explicit_target_affinity_sources(session, request, actor_user_id=actor_user_id)


def derive_explicit_target_affinity_profile(subject):
    """Additive facade; the derivation core itself has no IO dependency."""
    from app.modules.preferences.profile_derivation import derive_explicit_target_affinity_profile

    return derive_explicit_target_affinity_profile(subject)


def derive_exact_target_prior_backed_affinity(subject):
    """Additive zero-IO exact-target compatibility/shrinkage facade; no planner authority."""
    from app.modules.preferences.prior_affinity import derive_exact_target_prior_backed_affinity

    return derive_exact_target_prior_backed_affinity(subject)


# Additive internal global source; no member preference or hierarchy consumer authority.
from app.modules.preferences.hierarchy_sources import (  # noqa: E402,F401
    capture_hierarchy_sources,
    change_hierarchy_authority,
    enroll_hierarchy_principal,
    publish_hierarchy_source,
    register_hierarchy_provider,
)


def resolve_hierarchy_sources(source):
    from app.modules.preferences.hierarchy_resolution import resolve_hierarchy_sources

    return resolve_hierarchy_sources(source)


def derive_one_hop_hierarchical_member_preference(subject):
    """Additive lazy pure consumer; no durable learning or planner authority."""
    from app.modules.preferences.hierarchical_affinity import (
        derive_one_hop_hierarchical_member_preference,
    )

    return derive_one_hop_hierarchical_member_preference(subject)
