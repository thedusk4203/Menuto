"""Exact finite planned-input estimator. Pure replay; no policy integration or origin proof."""

from fractions import Fraction
from itertools import product

from app.domain.feature_identity import canonical
from app.modules.nutrition import resolution_contracts as c
from app.modules.nutrition.resolution_limits import WITNESSES, WorkBudget, ingest
from app.modules.nutrition.synthesis import nutrition_policy_requirements


class _Unavailable(ValueError):
    def __init__(self, state, reason):
        self.state, self.reason = state, reason


def _require(truth, reason, state="REJECTED"):
    if not truth:
        raise _Unavailable(state, reason)


def _ratio(value):
    return Fraction(value)


def _amount(value, signed=False):
    cls = c.NreDelta if signed else c.NreRational
    return cls(numerator=value.numerator, denominator=value.denominator)


def _key(value):
    return c.resolution_hash("temporal", value)


def _source(s):
    q, frame, nps = s.scope, s.frame, s.synthesis_sources
    body = canonical(s)
    body.pop("source_fingerprint")
    _require(c.resolution_hash("sources", body) == s.source_fingerprint, "SOURCE_IDENTITY")
    _require(frame.owner_relations == c.NRE_OWNER_RELATIONS, "OWNER_RELATION_MANIFEST")
    _require(frame.fixture_database_name.startswith("nrc_test_"), "ENVIRONMENT_MISMATCH")
    requirements = nutrition_policy_requirements(nps)
    _require(
        requirements == s.requirements and requirements.fingerprint == q.requirement_fingerprint,
        "REQUIREMENT_IDENTITY",
    )
    root = nps.request.root.sources.request
    _require(
        q.root_request == root
        and q.subject == root.subject == requirements.subject
        and q.selection == nps.request.selection
        and q.precision == nps.request.precision
        and q.actor_user_id == q.precision.actor_user_id,
        "SUBJECT_REQUEST_IDENTITY",
    )
    _require(
        q.environment == root.environment == requirements.environment == "TEST_ONLY",
        "ENVIRONMENT_MISMATCH",
    )
    _require(
        frame.source_frame == nps.frame
        and frame.subject == q.subject
        and frame.actor_user_id == q.actor_user_id,
        "SOURCE_CUT_INCOHERENT",
    )
    witness = nps.frame.reader_subject_witness
    _require(
        (frame.membership_id, frame.membership_role, frame.member_id)
        == (witness.membership_id, witness.role, witness.actor_member_id)
        and witness.subject == q.subject
        and witness.actor_user_id == q.actor_user_id,
        "ACTOR_WITNESS_MISMATCH",
    )
    who = next((p for p in nps.principal_facts if p.id == nps.frame.reader_principal_id), None)
    _require(
        who is not None
        and who.command.verified_human_id is not None
        and who.command.service_id is None
        and who.command.user_id == q.actor_user_id,
        "ENROLLED_ACTOR_MISMATCH",
    )
    _require(
        frame.started_at <= nps.request.root.sources.capture.started_at
        and nps.frame.completed_at <= frame.completed_at
        and frame.completed_at >= frame.started_at,
        "SOURCE_CUT_INCOHERENT",
    )
    _require(
        (frame.fixture_database_oid, frame.fixture_database_name)
        == (nps.frame.session.database_oid, nps.frame.session.database_name),
        "ENVIRONMENT_MISMATCH",
    )
    _require(
        c.resolution_hash("fixture-manifest", frame.fixture_manifest)
        == frame.fixture_food_fingerprint,
        "ENVIRONMENT_MISMATCH",
    )
    fixtures = {(m.owner, m.identity): m for m in frame.fixture_manifest}
    _require(len(fixtures) == len(frame.fixture_manifest), "DUPLICATE_FIXTURE_IDENTITY")
    for owner, rows in (
        ("Recipe", s.recipes),
        ("Ingredient", s.ingredients),
        ("Reference", s.references),
    ):
        _require(len({r.id for r in rows}) == len(rows), "DUPLICATE_SOURCE_IDENTITY")
        for row in rows:
            fixture = fixtures.get((owner, row.id))
            _require(
                fixture is not None
                and fixture.body_fingerprint == c.resolution_hash("fixture", row),
                "ENVIRONMENT_MISMATCH",
            )
            if owner == "Reference":
                _require(fixture.ingredient_id == row.fact.ingredient_id, "ENVIRONMENT_MISMATCH")
                _require(row.fact.provenance.observed_at <= frame.completed_at, "SOURCE_AFTER_CUT")
            if owner == "Recipe":
                _require(row.review_status == "REVIEWED", "UNREVIEWED_RECIPE")
                evidence = (
                    row.provenance,
                    *(r.provenance for r in row.variant_rules),
                    *(r.provenance for r in row.transformations),
                    *(r.provenance for r in row.approved_combinations),
                )
                _require(
                    all(p.observed_at <= frame.completed_at for p in evidence), "SOURCE_AFTER_CUT"
                )
    _require(len(s.references) <= 512 and len(s.recipes) <= 32, "OWNER_COVERAGE")
    recipes = {r.id: r for r in s.recipes}
    _require(set(recipes) <= {r.recipe_version_id for r in q.recipes}, "FOREIGN_RECIPE")
    _require(
        len(s.recipe_seals) == len(recipes)
        and {(x.recipe_version_id, x.body_fingerprint) for x in s.recipe_seals}
        == {(r.id, c.resolution_hash("recipe", r)) for r in s.recipes},
        "RECIPE_SEAL_COVERAGE",
    )
    row_count = (
        3
        + len(s.ingredients)
        + len(s.references)
        + len({r.recipe.id for r in s.recipes})
        + sum(
            2
            + len(r.ingredients)
            + len(r.portion_tiers)
            + sum(len(t.quantities) for t in r.portion_tiers)
            + len(r.variant_rules)
            + len(r.approved_combinations)
            + sum(len(g.rule_ids) for g in r.approved_combinations)
            + len(r.transformations)
            for r in s.recipes
        )
    )
    _require(row_count == frame.owner_row_count, "OWNER_ROW_MANIFEST")
    _require(bool(q.recipes) and bool(q.slots), "EMPTY_UNIVERSE", "UNAVAILABLE")
    expected = set()
    closure = set()
    for selection in q.recipes:
        r = recipes.get(selection.recipe_version_id)
        if r is None:
            expected.add(("Recipes", str(selection.recipe_version_id), "VERSION_MISSING"))
            continue
        for i in set(selection.tier_ids) - {t.id for t in r.portion_tiers}:
            expected.add(("Recipes", str(i), "TIER_MISSING"))
        rules = {v.id: v for v in r.variant_rules}
        for ids in selection.rule_selections:
            replacements = {
                rules[i].requirement_id: rules[i].replacement_ingredient_id
                for i in ids
                if i in rules
            }
            closure.update(replacements.get(v.id, v.ingredient_id) for v in r.ingredients)
            expected.update(("Recipes", str(i), "RULE_MISSING") for i in ids if i not in rules)
    expected.update(
        ("Catalog", str(i), "INGREDIENT_MISSING") for i in closure - {v.id for v in s.ingredients}
    )
    expected.update(
        ("Catalog", str(i), "REFERENCE_MISSING")
        for i in {v.reference_id for v in q.references} - {v.id for v in s.references}
    )
    expected.update(
        ("Catalog", str(i), "REFERENCE_COVERAGE_MISSING")
        for i in {
            m.identity
            for m in frame.fixture_manifest
            if m.owner == "Reference" and m.ingredient_id in closure
        }
        - {v.id for v in s.references}
    )
    actual = {(v.owner, v.identity, v.reason) for v in s.absences}
    _require(expected == actual and len(actual) == len(s.absences), "ABSENCE_MANIFEST")
    _require(not s.absences, "SOURCE_MISSING", "UNAVAILABLE")
    return requirements, recipes


def _possibilities(s, recipes, budget):
    q = s.scope
    options, ingredient_ids, closure, total = {}, set(), set(), 0
    for selection in q.recipes:
        r = recipes.get(selection.recipe_version_id)
        _require(r is not None, "SOURCE_MISSING", "UNAVAILABLE")
        _require(len(r.ingredients) <= 32, "INGREDIENT_LIMIT", "RESOURCE_EXCEEDED")
        _require(
            bool(selection.tier_ids) and bool(selection.rule_selections),
            "EMPTY_UNIVERSE",
            "UNAVAILABLE",
        )
        tiers, rules = {t.id: t for t in r.portion_tiers}, {x.id: x for x in r.variant_rules}
        for tier, ids in product(selection.tier_ids, selection.rule_selections):
            _require(
                tier in tiers and all(i in rules for i in ids), "SELECTION_MISSING", "UNAVAILABLE"
            )
            chosen = [rules[i] for i in ids]
            _require(len({x.requirement_id for x in chosen}) == len(chosen), "RULE_SLOT_CONFLICT")
            _require(
                sum(x.structural for x in chosen) <= 1
                or any(set(x.rule_ids) == set(ids) for x in r.approved_combinations),
                "UNAUTHORIZED_RULE_COMBINATION",
            )
            alternatives = []
            amounts = {v.requirement_id: _ratio(v.amount) for v in tiers[tier].quantities}
            for item in sorted(r.ingredients, key=lambda x: str(x.id)):
                b, a = item.quantity.basis.value, item.adjustment
                _require(
                    item.scaling.kind != "TO_TASTE" and a.kind in {"NONE", "DISCRETE"},
                    "CONTINUOUS_ENVELOPE",
                    "UNSUPPORTED",
                )
                _require(b != "COUNT", "COUNT_NUTRITION_SOURCE_UNAVAILABLE", "UNSUPPORTED")
                rule = next((x for x in chosen if x.requirement_id == item.id), None)
                ingredient = rule.replacement_ingredient_id if rule else item.ingredient_id
                paths = {t.ingredient_id for t in r.transformations if t.requirement_id == item.id}
                _require(
                    item.ingredient_id not in paths or ingredient in paths, "TRANSFORM_PATH_MISSING"
                )
                base = budget.number(
                    amounts[item.id] * (_ratio(rule.quantity_factor) if rule else 1)
                )
                if a.kind == "NONE":
                    deltas = (Fraction(0),)
                else:
                    step = _ratio(a.step)
                    low, high = _ratio(a.min_delta) / step, _ratio(a.max_delta) / step
                    _require(low.denominator == high.denominator == 1, "DELTA_ALIGNMENT")
                    _require(high - low + 1 <= 64, "DELTA_LIMIT", "RESOURCE_EXCEEDED")
                    deltas = tuple(budget.number(k * step) for k in range(int(low), int(high) + 1))
                choices = []
                for delta in deltas:
                    amount = budget.number(base + delta)
                    _require(amount > 0, "NONPOSITIVE_QUANTITY")
                    if item.scaling.kind == "DISCRETE":
                        _require(
                            (amount / _ratio(item.scaling.quantum)).denominator == 1,
                            "QUANTUM_ALIGNMENT",
                        )
                    choices.append((item, ingredient, amount, delta))
                alternatives.append(tuple(choices))
                ingredient_ids.add(ingredient)
                closure.add((ingredient, b))
            count = budget.product([len(a) for a in alternatives], q.max_states)
            total += count
            _require(total <= q.max_states, "CONFIGURATION_LIMIT", "RESOURCE_EXCEEDED")
            options[(r.id, tier, ids)] = (r, alternatives)
    _require({i.id for i in s.ingredients} == ingredient_ids, "INGREDIENT_COVERAGE", "UNAVAILABLE")
    actual_refs = {r.id for r in s.references}
    expected_refs = {
        m.identity
        for m in s.frame.fixture_manifest
        if m.owner == "Reference" and m.ingredient_id in ingredient_ids
    }
    _require(actual_refs == expected_refs, "REFERENCE_COVERAGE", "UNAVAILABLE")
    _require(
        {(p.ingredient_id, p.basis) for p in q.references} == closure,
        "REFERENCE_SELECTION_COVERAGE",
        "UNAVAILABLE",
    )
    return options


def _configurations(s, options, budget):
    q, scope_hash = s.scope, c.resolution_hash("scope", s.scope)
    references = {r.id: r for r in s.references}
    pins = {(r.ingredient_id, r.basis): r.reference_id for r in q.references}
    configs, per_slot, seen, count = [], {}, set(), 0
    for slot in q.slots:
        _require(bool(slot.alternatives), "EMPTY_UNIVERSE", "UNAVAILABLE")
        per_slot[slot.slot_id] = []
        for serving in slot.alternatives:
            _require(
                serving.subject == q.subject
                and serving.actor_user_id == q.actor_user_id
                and serving.slot_id == slot.slot_id,
                "SERVING_IDENTITY",
            )
            k = (serving.recipe_version_id, serving.tier_id, serving.rule_ids)
            _require(k in options, "SERVING_SELECTION_MISMATCH")
            recipe, alternatives = options[k]
            _require(serving.serving_definition == recipe.serving_definition, "SERVING_DEFINITION")
            seen.add(k)
            count += budget.product([len(a) for a in alternatives], q.max_states)
            _require(count <= q.max_states, "CONFIGURATION_LIMIT", "RESOURCE_EXCEEDED")
            for selection in product(*alternatives):
                lines, vector = [], [Fraction(0)] * 4
                for item, ingredient, quantity, delta in selection:
                    ref = references.get(pins[(ingredient, item.quantity.basis.value)])
                    _require(ref is not None, "REFERENCE_MISSING", "UNAVAILABLE")
                    f = ref.fact
                    _require(f.status == "REVIEWED", "REFERENCE_UNREVIEWED", "UNAVAILABLE")
                    _require(
                        f.ingredient_id == ingredient and f.reference.basis == item.quantity.basis,
                        "REFERENCE_BASIS_MISMATCH",
                        "UNSUPPORTED",
                    )
                    values = []
                    for index, nutrient in enumerate(
                        (
                            f.nutrients.energy_kcal,
                            f.nutrients.protein_g,
                            f.nutrients.fat_g,
                            f.nutrients.carbohydrate_g,
                        )
                    ):
                        value = budget.number(
                            budget.number(quantity * _ratio(nutrient)) / _ratio(f.reference.amount)
                        )
                        values.append(_amount(value))
                        vector[index] = budget.number(vector[index] + value)
                    lines.append(
                        c.NreIngredientContribution(
                            requirement_id=item.id,
                            ingredient_id=ingredient,
                            reference_id=ref.id,
                            basis=item.quantity.basis.value,
                            amount=_amount(quantity),
                            delta=_amount(delta, True),
                            nutrients=tuple(values),
                        )
                    )
                data = dict(
                    scope_fingerprint=scope_hash,
                    serving=serving,
                    recipe_fingerprint=c.resolution_hash("recipe", recipe),
                    ingredients=tuple(lines),
                    nutrients=tuple(map(_amount, vector)),
                )
                result = c.ResolutionConfigurationV1(
                    **data, configuration_id=c.resolution_hash("configuration", data)
                )
                configs.append(result)
                per_slot[slot.slot_id].append(result)
    _require(seen == set(options), "DECLARED_UNIVERSE_OMISSION")
    return tuple(sorted(configs, key=lambda x: x.configuration_id)), per_slot


def _periods(s, per_slot, budget):
    q, requirements = s.scope, s.requirements
    temporal = {
        _key(r.descriptor.temporal): r.descriptor.temporal for r in requirements.measurements
    }
    _require(len(temporal) <= 32, "PERIOD_LIMIT", "RESOURCE_EXCEEDED")
    horizon = q.root_request.temporal
    rule = next(
        x.command.body.rule
        for x in s.synthesis_sources.records
        if x.command.body.kind == "DRAFT"
        and x.command.body.rule.revision_id == q.selection.revision_id
    )
    for value in tuple(temporal.values()):
        _require(
            value == horizon or value in rule.calendar_cells,
            "REVIEWED_CALENDAR_CELL_MISSING",
            "UNSUPPORTED",
        )
        if value.kind == "WEEK":
            children = sorted(
                (
                    c
                    for c in rule.calendar_cells
                    if c.kind == "DAY"
                    and value.interval.start <= c.interval.start
                    and c.interval.end <= value.interval.end
                ),
                key=lambda c: c.interval.start,
            )
            cursor = value.interval.start
            for child in children:
                _require(
                    child.calendar == value.calendar
                    and child.timezone == value.timezone
                    and child.interval.start == cursor,
                    "PARENT_DAY_COVERAGE_MISSING",
                    "UNSUPPORTED",
                )
                cursor = child.interval.end
                temporal[_key(child)] = child
            _require(
                bool(children) and cursor == value.interval.end,
                "PARENT_DAY_COVERAGE_MISSING",
                "UNSUPPORTED",
            )
    _require(len(temporal) <= 32, "PERIOD_LIMIT", "RESOURCE_EXCEEDED")
    for value in temporal.values():
        _require(
            (value.calendar, value.timezone) == (horizon.calendar, horizon.timezone)
            and horizon.interval.start
            <= value.interval.start
            < value.interval.end
            <= horizon.interval.end,
            "TEMPORAL_MAPPING_UNSUPPORTED",
            "UNSUPPORTED",
        )
    for x, y in product(temporal.values(), repeat=2):
        if x == y:
            continue
        a, b = x.interval, y.interval
        overlap = a.start < b.end and b.start < a.end
        nested = (
            a.start <= b.start and b.end <= a.end and x.kind == "WEEK" and y.kind == "DAY"
        ) or (b.start <= a.start and a.end <= b.end and y.kind == "WEEK" and x.kind == "DAY")
        _require(not overlap or nested, "UNRELATED_PERIOD_OVERLAP", "UNSUPPORTED")
    slots = {k: [] for k in temporal}
    for slot in q.slots:
        assigned = False
        for k, value in temporal.items():
            a, b = slot.interval, value.interval
            if a.start < b.end and b.start < a.end:
                _require(
                    b.start <= a.start and a.end <= b.end,
                    "TEMPORAL_MAPPING_UNSUPPORTED",
                    "UNSUPPORTED",
                )
                slots[k].append(slot.slot_id)
                assigned = True
        _require(assigned, "UNASSIGNED_SLOT", "UNSUPPORTED")
    outputs, witness_count, vector_count = [], 0, 0
    for k, value in sorted(temporal.items()):
        names = tuple(sorted(slots[k]))
        _require(bool(names), "TEMPORAL_COVERAGE_MISSING", "UNAVAILABLE")
        budget.product([len(per_slot[n]) for n in names], q.max_states)
        vectors = {}
        for choices in product(*(per_slot[n] for n in names)):
            totals = [Fraction(0)] * 4
            for choice in choices:
                for i, v in enumerate(choice.nutrients):
                    totals[i] = budget.number(totals[i] + Fraction(v.numerator, v.denominator))
            vectors.setdefault(tuple(totals), []).append(tuple(v.configuration_id for v in choices))
            witness_count += 1
            _require(witness_count <= WITNESSES, "WITNESS_LIMIT", "RESOURCE_EXCEEDED")
        vector_count += len(vectors)
        _require(vector_count <= q.max_states, "VECTOR_LIMIT", "RESOURCE_EXCEEDED")
        outputs.append(
            c.NrePeriodVectors(
                temporal=value,
                slot_ids=names,
                vectors=tuple(
                    c.NreReachableVector(
                        nutrients=tuple(map(_amount, v)), configurations=tuple(sorted(w))
                    )
                    for v, w in sorted(vectors.items())
                ),
            )
        )
    return tuple(outputs)


def _measurements(s, periods):
    indexes = {"ENERGY": 0, "PROTEIN": 1, "FAT": 2, "CARBOHYDRATE": 3}
    results = []
    for measurement in s.requirements.measurements:
        period = next(p for p in periods if p.temporal == measurement.descriptor.temporal)
        index, projection = indexes[measurement.descriptor.metric], {}
        for vector in period.vectors:
            v = vector.nutrients[index]
            projection.setdefault(Fraction(v.numerator, v.denominator), []).extend(
                vector.configurations
            )
        numbers = sorted(projection)
        gaps = tuple(
            c.NreResolutionGap(
                lower=_amount(a),
                upper=_amount(b),
                amount=_amount(b - a),
                lower_witnesses=tuple(sorted(projection[a])),
                upper_witnesses=tuple(sorted(projection[b])),
            )
            for a, b in zip(numbers, numbers[1:])
        )
        results.append(
            c.ResolutionMeasurementV1(
                subject=s.scope.subject,
                scope_fingerprint=c.resolution_hash("scope", s.scope),
                root_key=measurement.root_key,
                descriptor=measurement.descriptor,
                values=tuple(map(_amount, numbers)),
                gaps=gaps,
                maximum_gap=_amount(max(b - a for a, b in zip(numbers, numbers[1:])))
                if gaps
                else None,
                step_state="EXACT_FINITE_GAPS" if gaps else "NO_ADJACENT_STEP",
            )
        )
    return tuple(results)


def _finish(s, availability, reasons, configurations=(), periods=(), measurements=()):
    # Protocol output-work footprint is independently reproducible, not a clock,
    # probability, calibrated complexity or a claim about VM instruction counts.
    work = (
        sum(1 + 14 * len(v.ingredients) for v in configurations)
        + sum(4 * len(w) for p in periods for v in p.vectors for w in v.configurations)
        + sum(len(m.values) + len(m.gaps) for m in measurements)
    )
    if work > s.scope.max_work:
        availability, reasons, configurations, periods, measurements, work = (
            "RESOURCE_EXCEEDED",
            ("WORK_LIMIT",),
            (),
            (),
            (),
            0,
        )
    data = dict(
        source_fingerprint=s.source_fingerprint,
        scope_fingerprint=c.resolution_hash("scope", s.scope),
        requirements_fingerprint=s.requirements.fingerprint,
        availability=availability,
        reasons=reasons,
        configurations=configurations,
        periods=periods,
        measurements=measurements,
        work_used=work,
    )
    model = c.NutritionResolutionEstimateV1(**data, result_fingerprint="0" * 64)
    preimage = canonical(model)
    preimage.pop("result_fingerprint")
    return c.NutritionResolutionEstimateV1(
        **preimage, result_fingerprint=c.resolution_hash("estimate", preimage)
    )


def estimate_nutrition_resolution(sources):
    s = c.NutritionResolutionSourcesV1.model_validate(ingest(sources))
    try:
        _, recipes = _source(s)
        budget = WorkBudget()
        options = _possibilities(s, recipes, budget)
        configurations, slots = _configurations(s, options, budget)
        periods = _periods(s, slots, budget)
        measurements = _measurements(s, periods)
        return _finish(s, "AVAILABLE", (), configurations, periods, measurements)
    except _Unavailable as exc:
        return _finish(s, exc.state, (exc.reason,))
    except (ValueError, ArithmeticError, KeyError, TypeError, AttributeError, IndexError) as exc:
        state = "RESOURCE_EXCEEDED" if str(exc).startswith("RESOURCE_EXCEEDED") else "REJECTED"
        return _finish(
            s, state, ("RESOURCE_LIMIT" if state == "RESOURCE_EXCEEDED" else "SOURCE_INVALID",)
        )
