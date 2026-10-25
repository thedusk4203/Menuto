"""Synthetic policies are explicit test inputs, never production defaults."""

from datetime import timedelta
from uuid import uuid4

from app.modules.preferences import contracts as c
from preference_fixtures import command, declaration, provenance, term
from test_explicit_preferences import snapshot

KINDS = ("INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR")


def policy(*, self_level="LOW", proxy_level="HIGH", **kw):
    return c.ExplicitTargetAffinityPolicy(
        **(
            dict(
                policy_id="synthetic.040b",
                policy_version="1",
                provenance=provenance(),
                target_policies=tuple(
                    dict(
                        target_kind=kind,
                        affinity_rules=tuple(
                            dict(value=value, amount=dict(numerator=n, denominator=d))
                            for value, n, d in (
                                ("DISLIKE", -2, 3),
                                ("NEUTRAL", 0, 7),
                                ("LIKE", 3, 5),
                            )
                        ),
                        strength_rules=(
                            dict(authorship="SELF", level=self_level),
                            dict(authorship="AUTHORIZED_REPRESENTATIVE", level=proxy_level),
                        ),
                        undeclared_strength="NONE",
                        retracted_strength="NONE",
                    )
                    for kind in KINDS
                ),
            )
            | kw
        )
    )


def entry(target, *, identity=None):
    if target.kind == "INGREDIENT":
        return c.IngredientTargetManifestEntry(
            identity=identity or dict(id=target.ingredient_id, name="Synthetic ingredient")
        )
    if target.kind == "DIRECT_RECIPE":
        return c.RecipeTargetManifestEntry(
            identity=identity
            or dict(id=target.recipe_id, name="Synthetic recipe", cooking_method="synthetic")
        )
    return c.FeatureTargetManifestEntry(
        kind=target.kind, identity=identity or term(target.kind, id=target.feature_term_id)
    )


def subject(rows=None, *, targets=None, entries=None, terms=(), interpretation=None):
    if rows is None:
        rows = (declaration(command()),)
    source = snapshot(rows, feature_terms=terms)
    if targets is None:
        targets = tuple(
            {c.preference_target_key(d.command.target): d.command.target for d in rows}.values()
        )
    request = c.ExplicitTargetAffinityCaptureRequest(
        household_id=source.household_id,
        member_id=source.member_id,
        requested_targets=targets,
    )
    manifest = c.CanonicalPreferenceTargetManifest(
        household_id=source.household_id,
        member_id=source.member_id,
        entries=tuple(entry(t) for t in targets) if entries is None else entries,
    )
    return c.ExplicitTargetAffinityInput(
        source=c.ExplicitTargetAffinitySourceSnapshotDraft(
            request=request,
            preferences=source,
            manifest=manifest,
            capture_completed_at=source.captured_at + timedelta(seconds=1),
        ),
        policy=interpretation or policy(),
    )


def revision(first, *, value="DISLIKE", reason="INPUT_CORRECTION", retract=False):
    fields = first.command.model_dump(exclude={"action", "contract_version", "value", "reason"})
    fields.update(
        expected_revision=first.revision_no, predecessor_id=first.id, idempotency_key=uuid4().hex
    )
    q = (
        c.RetractMemberPreferenceCommand(**fields)
        if retract
        else c.SetMemberPreferenceCommand(**fields, value=value, reason=reason)
    )
    return declaration(q, stream_id=first.stream_id, sequence=first.member_sequence + 1)
