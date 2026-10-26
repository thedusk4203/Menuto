"""Pure exact-target compatibility/shrinkage. No source capture or current authority."""

from fractions import Fraction

from app.modules.preferences import prior_affinity_contracts as c
from app.modules.preferences.profile_derivation import derive_explicit_target_affinity_profile
from app.modules.preferences.reference_prior_resolution import resolve_reference_priors


def _scoped(coordinate, amount):
    return c.ScopedMemberProfileAffinity(
        coordinate=coordinate,
        amount=c.MemberProfileAffinityAmount(
            numerator=amount.numerator, denominator=amount.denominator
        ),
    )


def _blend(coordinate, explicit, prior, weight):
    """Internal seam: complete descriptors are checked before numeric arithmetic."""
    coordinate = c.MemberProfileAffinityCoordinate.model_validate(coordinate)
    explicit = c.ScopedMemberProfileAffinity.model_validate(explicit)
    prior = c.ScopedMemberProfileAffinity.model_validate(prior)
    weight = c.PriorInfluenceWeight.model_validate(weight)
    if explicit.coordinate != coordinate or prior.coordinate != coordinate:
        raise ValueError("Blend coordinate descriptor mismatch; coercion forbidden")
    p = Fraction(weight.numerator, weight.denominator)
    e = 1 - p
    contributions = tuple(
        c.ExactTargetShrinkageContribution(
            side=side,
            weight_numerator=w.numerator,
            weight_denominator=w.denominator,
            value=_scoped(coordinate, w * c._fraction(value.amount)),
        )
        for side, w, value in (("EXPLICIT", e, explicit), ("PRIOR", p, prior))
    )
    return contributions, _scoped(
        coordinate, sum((c._fraction(x.value.amount) for x in contributions), Fraction(0))
    )


def _derive_fields(subject):
    subject = c.ExactTargetPriorBackedAffinityInput.model_validate(subject)
    explicit = derive_explicit_target_affinity_profile(subject.explicit)
    prior = resolve_reference_priors(subject.reference_source)
    row, reference = explicit.rows[0], prior.rows[0]
    target, policy = row.target, subject.compatibility_policy
    coordinate = policy.coordinate_for(target.kind)
    mapped_explicit = None
    if row.raw_state.status == "DECLARED":
        group = next(g for g in policy.explicit_maps if g.target_kind == target.kind)
        rule = next(r for r in group.rows if r.value == row.raw_state.value)
        mapped_explicit = c.MappedExplicitProfileAffinity(
            rule_key=(target.kind, rule.value),
            value=_scoped(coordinate, c._fraction(rule.output_amount)),
        )
    if reference.status == "UNAVAILABLE":
        mapped_prior = c.UnavailableReferenceCompatibility(reason=reference.reason)
    else:
        group = next(g for g in policy.reference_maps if g.target_kind == target.kind)
        rule = next((r for r in group.rows if r.reference_amount == reference.amount), None)
        mapped_prior = (
            c.MappedReferenceProfileAffinity(
                rule_key=(target.kind, reference.amount),
                value=_scoped(coordinate, c._fraction(rule.output_amount)),
            )
            if rule
            else c.UnavailableReferenceCompatibility(reason="PRIOR_VALUE_NOT_MAPPED")
        )
    contributions = ()
    shrinkage = "NOT_APPLIED"
    if row.raw_state.status == "RETRACTED":
        effective = c.UnavailableExactTargetProfileAffinity(reason="MEMBER_RETRACTED")
    elif mapped_explicit is not None and mapped_prior.status == "AVAILABLE":
        weight = next(
            r.prior_weight
            for r in subject.shrinkage_policy.rules
            if r.level == row.evidence_strength.level
        )
        contributions, value = _blend(coordinate, mapped_explicit.value, mapped_prior.value, weight)
        shrinkage = "APPLIED"
        effective = c.AvailableExactTargetProfileAffinity(
            mode="BLENDED_EXPLICIT_AND_PRIOR", value=value
        )
    elif mapped_explicit is not None:
        effective = c.AvailableExactTargetProfileAffinity(
            mode="EXPLICIT_ONLY", value=mapped_explicit.value
        )
    elif mapped_prior.status == "AVAILABLE":
        effective = c.AvailableExactTargetProfileAffinity(
            mode="PRIOR_ONLY_COLD_START", value=mapped_prior.value
        )
    else:
        effective = c.UnavailableExactTargetProfileAffinity(
            reason="NO_EXPLICIT_OR_COMPATIBLE_PRIOR"
        )
    return dict(
        subject=subject,
        household_id=subject.explicit.source.request.household_id,
        member_id=subject.explicit.source.request.member_id,
        target=target,
        target_kind=target.kind,
        coordinate=coordinate,
        explicit_profile=explicit,
        reviewed_prior=prior,
        mapped_explicit=mapped_explicit,
        mapped_prior=mapped_prior,
        shrinkage=shrinkage,
        contributions=contributions,
        effective=effective,
        compatibility_policy_fingerprint=policy.fingerprint(),
        shrinkage_policy_fingerprint=subject.shrinkage_policy.fingerprint(),
    )


def derive_exact_target_prior_backed_affinity(subject):
    """Reparse primitives, recompute both frozen children, return a validated pure draft."""
    fields = _derive_fields(subject)
    temporary = c.ExactTargetPriorBackedAffinityDraft.model_construct(
        **fields, fingerprint="0" * 64
    )
    return c.ExactTargetPriorBackedAffinityDraft(
        **fields, fingerprint=temporary.expected_fingerprint()
    )
