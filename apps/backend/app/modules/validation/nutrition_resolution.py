"""Fresh independent NRE verification. No estimator, producer or live-source calls."""

from fractions import Fraction
from itertools import product

from app.domain.feature_identity import canonical
from app.modules.nutrition import resolution_contracts as c
from app.modules.nutrition import root_contracts as n
from app.modules.nutrition import synthesis_contracts as p
from app.modules.nutrition.resolution_limits import WITNESSES, WorkBudget, ingest
from app.modules.validation.nutrition_resolution_authority import verify_resolution_rule_sources
from app.modules.validation.nutrition_roots import validate_nutrition_root_independently


class _Failure(ValueError):
    def __init__(self, code, state="REJECTED"):
        self.code, self.state = code, state


def _check(ok, code, state="REJECTED"):
    if not ok:
        raise _Failure(code, state)


def _q(v):
    return Fraction(v.numerator, v.denominator)


def _r(v, signed=False):
    return (c.NreDelta if signed else c.NreRational)(
        numerator=v.numerator, denominator=v.denominator
    )


def _requirements(s):
    source, root = s.synthesis_sources, s.synthesis_sources.request.root
    result = validate_nutrition_root_independently(
        n.NutritionRootValidationInput(
            root=root, coverage="ROOT_SOURCE_CONSISTENCY_ONLY", derived_claims=()
        )
    )
    _check(
        result.decision == "CONSISTENT"
        and root.availability == "AVAILABLE"
        and root.eligibility == "SUPPORTED"
        and root.goal_state == "PRESENT",
        "SOURCE_INVALID",
    )
    rule = verify_resolution_rule_sources(source)
    cases = [r for r in rule.cases if r.direction == root.goal_direction]
    _check(len(cases) == 1, "SOURCE_INVALID")
    case = cases[0]
    clauses = {r.clause.root_key: r.clause for r in root.roots}
    measures = {}
    for op in case.operations:
        if op.kind != "MAKE_CONSTRAINT" or op.layer != "COMFORT":
            continue
        _check(op.root_key in clauses and op.root_key in case.comfort_root_keys, "SOURCE_INVALID")
        desc = n.NutritionRootDescriptor.model_validate(
            canonical(clauses[op.root_key].descriptor) | {"temporal": canonical(op.temporal)}
        )
        row = p.NutritionResolutionRequirement(root_key=op.root_key, descriptor=desc)
        key = n.nutrition_root_hash("nutrition-synthesis.measurement.v1", row)
        measures[key] = row
    _check(bool(measures), "SOURCE_INVALID")
    fields = dict(
        subject=root.sources.request.subject,
        root_fingerprint=root.result_fingerprint,
        rule_body_fingerprint=n.nutrition_root_hash("nutrition-synthesis.rule.v1", rule),
        case_id=case.id,
        temporal=root.sources.request.temporal,
        root_keys=case.comfort_root_keys,
        measurements=tuple(measures[k] for k in sorted(measures)),
        environment=root.sources.request.environment,
    )
    req = p.NutritionPolicyRequirementSpec(
        **fields, fingerprint=n.nutrition_root_hash("nutrition-synthesis.requirements.v1", fields)
    )
    _check(
        req == s.requirements and req.fingerprint == s.scope.requirement_fingerprint,
        "REQUIREMENT_IDENTITY",
    )
    return req


def _retained(s):
    """Independent manifest, scope and absence reconstruction, not an origin oracle."""
    v, f = s.scope, s.frame
    body = canonical(s)
    body.pop("source_fingerprint")
    _check(c.resolution_hash("sources", body) == s.source_fingerprint, "SOURCE_IDENTITY")
    _check(f.owner_relations == c.NRE_OWNER_RELATIONS, "OWNER_RELATION_MANIFEST")
    _check(f.fixture_database_name.startswith("nrc_test_"), "ENVIRONMENT_MISMATCH")
    req = _requirements(s)
    a = s.synthesis_sources
    _check(
        v.subject == v.root_request.subject == req.subject
        and v.root_request == a.request.root.sources.request
        and v.selection == a.request.selection
        and v.precision == a.request.precision
        and v.actor_user_id == v.precision.actor_user_id,
        "SUBJECT_REQUEST_IDENTITY",
    )
    _check(
        v.environment == req.environment == v.root_request.environment == "TEST_ONLY",
        "ENVIRONMENT_MISMATCH",
    )
    _check(
        f.source_frame == a.frame and f.actor_user_id == v.actor_user_id and f.subject == v.subject,
        "SOURCE_CUT_INCOHERENT",
    )
    w = a.frame.reader_subject_witness
    _check(
        (f.membership_id, f.membership_role, f.member_id)
        == (w.membership_id, w.role, w.actor_member_id)
        and w.subject == v.subject
        and w.actor_user_id == v.actor_user_id,
        "ACTOR_WITNESS_MISMATCH",
    )
    people = [x for x in a.principal_facts if x.id == a.frame.reader_principal_id]
    _check(
        len(people) == 1
        and people[0].command.user_id == v.actor_user_id
        and people[0].command.verified_human_id is not None
        and people[0].command.service_id is None,
        "ENROLLED_ACTOR_MISMATCH",
    )
    _check(
        f.started_at
        <= a.request.root.sources.capture.started_at
        <= a.frame.completed_at
        <= f.completed_at,
        "SOURCE_CUT_INCOHERENT",
    )
    _check(
        (f.fixture_database_oid, f.fixture_database_name)
        == (a.frame.session.database_oid, a.frame.session.database_name)
        and f.fixture_food_fingerprint == c.resolution_hash("fixture-manifest", f.fixture_manifest),
        "ENVIRONMENT_MISMATCH",
    )
    fixtures = {}
    for entry in f.fixture_manifest:
        _check((entry.owner, entry.identity) not in fixtures, "DUPLICATE_FIXTURE_IDENTITY")
        fixtures[entry.owner, entry.identity] = entry
    recipes, items, references = {}, {}, {}
    for owner, rows, index in (
        ("Recipe", s.recipes, recipes),
        ("Ingredient", s.ingredients, items),
        ("Reference", s.references, references),
    ):
        for row in rows:
            _check(row.id not in index, "DUPLICATE_SOURCE_IDENTITY")
            index[row.id] = row
            proof = fixtures.get((owner, row.id))
            _check(
                proof is not None and proof.body_fingerprint == c.resolution_hash("fixture", row),
                "ENVIRONMENT_MISMATCH",
            )
            if owner == "Reference":
                _check(proof.ingredient_id == row.fact.ingredient_id, "ENVIRONMENT_MISMATCH")
                _check(row.fact.provenance.observed_at <= f.completed_at, "SOURCE_AFTER_CUT")
            if owner == "Recipe":
                _check(row.review_status == "REVIEWED", "UNREVIEWED_RECIPE")
                proofs = [row.provenance] + [
                    x.provenance
                    for x in (*row.variant_rules, *row.approved_combinations, *row.transformations)
                ]
                _check(all(x.observed_at <= f.completed_at for x in proofs), "SOURCE_AFTER_CUT")
    _check(set(recipes) <= {x.recipe_version_id for x in v.recipes}, "FOREIGN_RECIPE")
    seals = {(x.recipe_version_id, x.body_fingerprint) for x in s.recipe_seals}
    _check(
        len(seals) == len(s.recipe_seals) == len(recipes)
        and seals == {(r.id, c.resolution_hash("recipe", r)) for r in recipes.values()},
        "RECIPE_SEAL_COVERAGE",
    )
    counts = 3 + len(items) + len(references) + len({r.recipe.id for r in recipes.values()})
    for r in recipes.values():
        counts += 2 + len(r.ingredients) + len(r.portion_tiers) + len(r.variant_rules)
        counts += sum(len(x.quantities) for x in r.portion_tiers)
        counts += len(r.approved_combinations) + sum(
            len(x.rule_ids) for x in r.approved_combinations
        )
        counts += len(r.transformations)
    _check(counts == f.owner_row_count, "OWNER_ROW_MANIFEST")
    _check(bool(v.recipes) and bool(v.slots), "EMPTY_UNIVERSE", "UNAVAILABLE")
    needed, absent = set(), set()
    for select in v.recipes:
        r = recipes.get(select.recipe_version_id)
        if r is None:
            absent.add(("Recipes", str(select.recipe_version_id), "VERSION_MISSING"))
            continue
        for tier in set(select.tier_ids) - {t.id for t in r.portion_tiers}:
            absent.add(("Recipes", str(tier), "TIER_MISSING"))
        rulemap = {rule.id: rule for rule in r.variant_rules}
        for selected in select.rule_selections:
            replace = {}
            for identity in selected:
                if identity not in rulemap:
                    absent.add(("Recipes", str(identity), "RULE_MISSING"))
                else:
                    rule = rulemap[identity]
                    replace[rule.requirement_id] = rule.replacement_ingredient_id
            needed |= {replace.get(i.id, i.ingredient_id) for i in r.ingredients}
    absent |= {("Catalog", str(i), "INGREDIENT_MISSING") for i in needed - set(items)}
    absent |= {
        ("Catalog", str(i), "REFERENCE_MISSING")
        for i in {x.reference_id for x in v.references} - set(references)
    }
    fixture_refs = {
        x.identity
        for x in f.fixture_manifest
        if x.owner == "Reference" and x.ingredient_id in needed
    }
    absent |= {
        ("Catalog", str(i), "REFERENCE_COVERAGE_MISSING") for i in fixture_refs - set(references)
    }
    recorded = {(x.owner, x.identity, x.reason) for x in s.absences}
    _check(recorded == absent and len(recorded) == len(s.absences), "ABSENCE_MANIFEST")
    _check(not absent, "SOURCE_MISSING", "UNAVAILABLE")
    return recipes, references, needed, fixture_refs


def _enumerate(s, recipes, refs, needed, fixture_refs, work):
    """Independently expand ingredient choices then assemble entire-slot vectors."""
    scope_hash = c.resolution_hash("scope", s.scope)
    v = s.scope
    admitted, closure, state_count = {}, set(), 0
    for selector in v.recipes:
        r = recipes.get(selector.recipe_version_id)
        _check(r is not None, "SOURCE_MISSING", "UNAVAILABLE")
        _check(len(r.ingredients) <= 32, "INGREDIENT_LIMIT", "RESOURCE_EXCEEDED")
        _check(
            bool(selector.tier_ids) and bool(selector.rule_selections),
            "EMPTY_UNIVERSE",
            "UNAVAILABLE",
        )
        for tier_id in selector.tier_ids:
            tier = next((t for t in r.portion_tiers if t.id == tier_id), None)
            for rule_ids in selector.rule_selections:
                selected = [rule for rule in r.variant_rules if rule.id in rule_ids]
                _check(
                    tier is not None and len(selected) == len(rule_ids),
                    "SELECTION_MISSING",
                    "UNAVAILABLE",
                )
                _check(
                    len({x.requirement_id for x in selected}) == len(selected), "RULE_SLOT_CONFLICT"
                )
                _check(
                    sum(x.structural for x in selected) <= 1
                    or any(set(x.rule_ids) == set(rule_ids) for x in r.approved_combinations),
                    "UNAUTHORIZED_RULE_COMBINATION",
                )
                rows = []
                for i in sorted(r.ingredients, key=lambda x: str(x.id)):
                    _check(
                        i.adjustment.kind in {"NONE", "DISCRETE"} and i.scaling.kind != "TO_TASTE",
                        "CONTINUOUS_ENVELOPE",
                        "UNSUPPORTED",
                    )
                    _check(
                        i.quantity.basis != "COUNT",
                        "COUNT_NUTRITION_SOURCE_UNAVAILABLE",
                        "UNSUPPORTED",
                    )
                    replacement = next((x for x in selected if x.requirement_id == i.id), None)
                    ingredient = (
                        replacement.replacement_ingredient_id if replacement else i.ingredient_id
                    )
                    paths = [x.ingredient_id for x in r.transformations if x.requirement_id == i.id]
                    _check(
                        i.ingredient_id not in paths or ingredient in paths,
                        "TRANSFORM_PATH_MISSING",
                    )
                    base = Fraction(
                        next(x.amount for x in tier.quantities if x.requirement_id == i.id)
                    )
                    if replacement is not None:
                        base = work.number(base * Fraction(replacement.quantity_factor))
                    else:
                        base = work.number(base)
                    if i.adjustment.kind == "NONE":
                        changes = [Fraction(0)]
                    else:
                        step = Fraction(i.adjustment.step)
                        left, right = (
                            Fraction(i.adjustment.min_delta) / step,
                            Fraction(i.adjustment.max_delta) / step,
                        )
                        _check(left.denominator == right.denominator == 1, "DELTA_ALIGNMENT")
                        _check(right - left + 1 <= 64, "DELTA_LIMIT", "RESOURCE_EXCEEDED")
                        changes = [
                            work.number(step * k)
                            for k in range(left.numerator, right.numerator + 1)
                        ]
                    row = []
                    for delta in changes:
                        quantity = work.number(delta + base)
                        _check(quantity > 0, "NONPOSITIVE_QUANTITY")
                        _check(
                            i.scaling.kind != "DISCRETE"
                            or (quantity / Fraction(i.scaling.quantum)).denominator == 1,
                            "QUANTUM_ALIGNMENT",
                        )
                        row.append((i, ingredient, quantity, delta))
                    rows.append(row)
                    closure.add((ingredient, i.quantity.basis.value))
                state_count += work.product([len(x) for x in rows], v.max_states)
                _check(state_count <= v.max_states, "CONFIGURATION_LIMIT", "RESOURCE_EXCEEDED")
                admitted[r.id, tier_id, rule_ids] = (r, rows)
    _check({x.id for x in s.ingredients} == needed, "INGREDIENT_COVERAGE", "UNAVAILABLE")
    _check(set(refs) == fixture_refs, "REFERENCE_COVERAGE", "UNAVAILABLE")
    _check(
        {(x.ingredient_id, x.basis) for x in v.references} == closure,
        "REFERENCE_SELECTION_COVERAGE",
        "UNAVAILABLE",
    )
    pins = {(x.ingredient_id, x.basis): x.reference_id for x in v.references}
    configurations, slot_values, covered, count = [], {}, set(), 0
    for slot in v.slots:
        _check(bool(slot.alternatives), "EMPTY_UNIVERSE", "UNAVAILABLE")
        slot_values[slot.slot_id] = []
        for declaration in slot.alternatives:
            _check(
                declaration.subject == v.subject
                and declaration.actor_user_id == v.actor_user_id
                and declaration.slot_id == slot.slot_id,
                "SERVING_IDENTITY",
            )
            identity = declaration.recipe_version_id, declaration.tier_id, declaration.rule_ids
            _check(identity in admitted, "SERVING_SELECTION_MISMATCH")
            recipe, choices = admitted[identity]
            _check(
                declaration.serving_definition == recipe.serving_definition, "SERVING_DEFINITION"
            )
            covered.add(identity)
            count += work.product([len(x) for x in choices], v.max_states)
            _check(count <= v.max_states, "CONFIGURATION_LIMIT", "RESOURCE_EXCEEDED")
            # Independent iterative fold, not the producer's ingredient Cartesian traversal.
            folded = [([], (Fraction(0),) * 4)]
            for ingredient_choices in choices:
                next_rows = []
                for i, ingredient, quantity, delta in ingredient_choices:
                    ref = refs.get(pins[ingredient, i.quantity.basis.value])
                    _check(ref is not None, "REFERENCE_MISSING", "UNAVAILABLE")
                    f = ref.fact
                    _check(f.status == "REVIEWED", "REFERENCE_UNREVIEWED", "UNAVAILABLE")
                    _check(
                        f.ingredient_id == ingredient and f.reference.basis == i.quantity.basis,
                        "REFERENCE_BASIS_MISMATCH",
                        "UNSUPPORTED",
                    )
                    values = tuple(
                        work.number(
                            work.number(Fraction(x) * quantity) / Fraction(f.reference.amount)
                        )
                        for x in (
                            f.nutrients.energy_kcal,
                            f.nutrients.protein_g,
                            f.nutrients.fat_g,
                            f.nutrients.carbohydrate_g,
                        )
                    )
                    line = c.NreIngredientContribution(
                        requirement_id=i.id,
                        ingredient_id=ingredient,
                        reference_id=ref.id,
                        basis=i.quantity.basis.value,
                        amount=_r(quantity),
                        delta=_r(delta, True),
                        nutrients=tuple(map(_r, values)),
                    )
                    for lines, old in folded:
                        new = tuple(work.number(x + y) for x, y in zip(old, values))
                        next_rows.append((lines + [line], new))
                folded = next_rows
            for lines, total in folded:
                fields = dict(
                    scope_fingerprint=scope_hash,
                    serving=declaration,
                    recipe_fingerprint=c.resolution_hash("recipe", recipe),
                    ingredients=tuple(lines),
                    nutrients=tuple(map(_r, total)),
                )
                row = c.ResolutionConfigurationV1(
                    **fields, configuration_id=c.resolution_hash("configuration", fields)
                )
                configurations.append(row)
                slot_values[slot.slot_id].append(row)
    _check(covered == set(admitted), "DECLARED_UNIVERSE_OMISSION")
    return tuple(sorted(configurations, key=lambda x: x.configuration_id)), slot_values


def _period_projection(s, choices, work):
    periods = {
        c.resolution_hash("temporal", x.descriptor.temporal): x.descriptor.temporal
        for x in s.requirements.measurements
    }
    _check(len(periods) <= 32, "PERIOD_LIMIT", "RESOURCE_EXCEEDED")
    frame = s.scope.root_request.temporal
    selected_rule = next(
        record.command.body.rule
        for record in s.synthesis_sources.records
        if record.command.body.kind == "DRAFT"
        and record.command.body.rule.revision_id == s.scope.selection.revision_id
    )
    for required in list(periods.values()):
        _check(
            required == frame or required in selected_rule.calendar_cells,
            "REVIEWED_CALENDAR_CELL_MISSING",
            "UNSUPPORTED",
        )
        if required.kind != "WEEK":
            continue
        cells = sorted(
            [
                cell
                for cell in selected_rule.calendar_cells
                if cell.kind == "DAY"
                and cell.interval.start >= required.interval.start
                and cell.interval.end <= required.interval.end
            ],
            key=lambda cell: cell.interval.start,
        )
        edges = [required.interval.start] + [cell.interval.end for cell in cells]
        _check(
            bool(cells)
            and edges[-1] == required.interval.end
            and all(
                cell.interval.start == edges[index]
                and (cell.calendar, cell.timezone) == (required.calendar, required.timezone)
                for index, cell in enumerate(cells)
            ),
            "PARENT_DAY_COVERAGE_MISSING",
            "UNSUPPORTED",
        )
        for cell in cells:
            periods[c.resolution_hash("temporal", cell)] = cell
    _check(len(periods) <= 32, "PERIOD_LIMIT", "RESOURCE_EXCEEDED")
    for period in periods.values():
        _check(
            period.calendar == frame.calendar
            and period.timezone == frame.timezone
            and frame.interval.start
            <= period.interval.start
            < period.interval.end
            <= frame.interval.end,
            "TEMPORAL_MAPPING_UNSUPPORTED",
            "UNSUPPORTED",
        )
    for x, y in product(periods.values(), repeat=2):
        if x == y:
            continue
        a, b = x.interval, y.interval
        disjoint = a.end <= b.start or b.end <= a.start
        nesting = x.kind == "WEEK" and y.kind == "DAY" and a.start <= b.start and b.end <= a.end
        nesting |= y.kind == "WEEK" and x.kind == "DAY" and b.start <= a.start and a.end <= b.end
        _check(disjoint or nesting, "UNRELATED_PERIOD_OVERLAP", "UNSUPPORTED")
    assignment = {key: [] for key in periods}
    for slot in s.scope.slots:
        matches = []
        for key, period in periods.items():
            a, b = slot.interval, period.interval
            if a.start < b.end and b.start < a.end:
                _check(
                    b.start <= a.start and a.end <= b.end,
                    "TEMPORAL_MAPPING_UNSUPPORTED",
                    "UNSUPPORTED",
                )
                matches.append(key)
        _check(bool(matches), "UNASSIGNED_SLOT", "UNSUPPORTED")
        for key in matches:
            assignment[key].append(slot.slot_id)
    outputs, count, vectors_count = [], 0, 0
    for key in sorted(periods):
        names = tuple(sorted(assignment[key]))
        _check(bool(names), "TEMPORAL_COVERAGE_MISSING", "UNAVAILABLE")
        work.product([len(choices[name]) for name in names], s.scope.max_states)
        # Independent incremental sumset carrying complete configuration witnesses.
        sums = {(Fraction(0),) * 4: [()]}
        for name in names:
            next_sums = {}
            for old, witnesses in sums.items():
                for configuration in choices[name]:
                    total = tuple(
                        work.number(old[i] + _q(configuration.nutrients[i])) for i in range(4)
                    )
                    next_sums.setdefault(total, []).extend(
                        w + (configuration.configuration_id,) for w in witnesses
                    )
            sums = next_sums
        count += sum(len(w) for w in sums.values())
        vectors_count += len(sums)
        _check(count <= WITNESSES, "WITNESS_LIMIT", "RESOURCE_EXCEEDED")
        _check(vectors_count <= s.scope.max_states, "VECTOR_LIMIT", "RESOURCE_EXCEEDED")
        outputs.append(
            c.NrePeriodVectors(
                temporal=periods[key],
                slot_ids=names,
                vectors=tuple(
                    c.NreReachableVector(
                        nutrients=tuple(map(_r, vector)), configurations=tuple(sorted(w))
                    )
                    for vector, w in sorted(sums.items())
                ),
            )
        )
    projections = []
    for requirement in s.requirements.measurements:
        period = next(p for p in outputs if p.temporal == requirement.descriptor.temporal)
        index = ("ENERGY", "PROTEIN", "FAT", "CARBOHYDRATE").index(requirement.descriptor.metric)
        scalars = {}
        for vector in period.vectors:
            scalars.setdefault(_q(vector.nutrients[index]), []).extend(vector.configurations)
        ordered = sorted(scalars)
        differences = []
        for i in range(1, len(ordered)):
            lo, hi = ordered[i - 1], ordered[i]
            differences.append(
                c.NreResolutionGap(
                    lower=_r(lo),
                    upper=_r(hi),
                    amount=_r(hi - lo),
                    lower_witnesses=tuple(sorted(scalars[lo])),
                    upper_witnesses=tuple(sorted(scalars[hi])),
                )
            )
        projections.append(
            c.ResolutionMeasurementV1(
                subject=s.scope.subject,
                scope_fingerprint=c.resolution_hash("scope", s.scope),
                root_key=requirement.root_key,
                descriptor=requirement.descriptor,
                values=tuple(map(_r, ordered)),
                gaps=tuple(differences),
                maximum_gap=_r(max(_q(d.amount) for d in differences)) if differences else None,
                step_state="EXACT_FINITE_GAPS" if differences else "NO_ADJACENT_STEP",
            )
        )
    return tuple(outputs), tuple(projections)


def check_nutrition_resolution_independently(sources, claimed_estimate):
    source_hash, reconstructed = "0" * 64, None
    try:
        s = c.NutritionResolutionSourcesV1.model_validate(ingest(sources))
        claimed = c.NutritionResolutionEstimateV1.model_validate(ingest(claimed_estimate))
        source_hash = s.source_fingerprint
        state, codes, configs, periods, measurements = "AVAILABLE", (), (), (), ()
        try:
            recipes, refs, needed, fixture_refs = _retained(s)
            work = WorkBudget()
            configs, choices = _enumerate(s, recipes, refs, needed, fixture_refs, work)
            periods, measurements = _period_projection(s, choices, work)
        except _Failure as exc:
            state, codes, configs, periods, measurements = exc.state, (exc.code,), (), (), ()
        except (
            ValueError,
            ArithmeticError,
            KeyError,
            TypeError,
            AttributeError,
            IndexError,
        ) as exc:
            state = "RESOURCE_EXCEEDED" if str(exc).startswith("RESOURCE_EXCEEDED") else "REJECTED"
            codes = ("RESOURCE_LIMIT" if state == "RESOURCE_EXCEEDED" else "SOURCE_INVALID",)
            configs, periods, measurements = (), (), ()
        footprint = sum(1 + 14 * len(x.ingredients) for x in configs)
        footprint += sum(4 * len(w) for p in periods for v in p.vectors for w in v.configurations)
        footprint += sum(len(x.values) + len(x.gaps) for x in measurements)
        if footprint > s.scope.max_work:
            state, codes, configs, periods, measurements, footprint = (
                "RESOURCE_EXCEEDED",
                ("WORK_LIMIT",),
                (),
                (),
                (),
                0,
            )
        expected = c.NutritionResolutionEstimateV1(
            source_fingerprint=s.source_fingerprint,
            scope_fingerprint=c.resolution_hash("scope", s.scope),
            requirements_fingerprint=s.requirements.fingerprint,
            availability=state,
            reasons=codes,
            configurations=configs,
            periods=periods,
            measurements=measurements,
            work_used=footprint,
            result_fingerprint="0" * 64,
        )
        # Faithful missing/unsupported evidence may be consistent. Corrupted or
        # unauthorized primitives are not certified consistent even if the producer
        # correctly returned REJECTED; neither case admits numerical use.
        _check(state != "REJECTED", "SOURCE_INVALID")
        preimage = canonical(expected)
        preimage.pop("result_fingerprint")
        reconstructed = c.resolution_hash("estimate", preimage)
        _check(
            canonical(claimed) == preimage | {"result_fingerprint": reconstructed},
            "RESOLUTION_SEMANTICS_INCONSISTENT",
        )
        return c.NutritionResolutionCheckV1(
            decision="CONSISTENT",
            numerical_use="AVAILABLE_RETAINED_ONLY" if state == "AVAILABLE" else "NOT_ADMITTED",
            findings=(),
            source_fingerprint=source_hash,
            reconstructed_result_fingerprint=reconstructed,
        )
    except (ValueError, ArithmeticError, KeyError, TypeError, AttributeError, IndexError):
        return c.NutritionResolutionCheckV1(
            decision="INCONSISTENT",
            numerical_use="NOT_ADMITTED",
            findings=("RESOLUTION_SEMANTICS_INCONSISTENT",),
            source_fingerprint=source_hash,
            reconstructed_result_fingerprint=reconstructed,
        )


def check_nutrition_resolution_handoff_independently(handoff):
    try:
        value = c.NutritionResolutionHandoffV2.model_validate(ingest(handoff))
        return check_nutrition_resolution_independently(value.sources, value.estimate)
    except (ValueError, ArithmeticError, KeyError, TypeError, AttributeError):
        return c.NutritionResolutionCheckV1(
            decision="INCONSISTENT",
            numerical_use="NOT_ADMITTED",
            findings=("HANDOFF_INVALID",),
            source_fingerprint="0" * 64,
            reconstructed_result_fingerprint=None,
        )
