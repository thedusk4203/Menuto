"""MTR-026 review evidence; characterize frozen hashing without changing its semantics."""

from datetime import timedelta

import pytest
from app.domain.canonical import canonical_hash
from app.modules.recipes.contracts import RecipeVersionSnapshot
from app.modules.validation.contracts import ValidationSubjectSnapshot
from app.modules.validation.public import validate_subject
from recipe_fixtures import recipe_data
from validation_fixtures import coverage_policy, subject


def reverse_collections(value):
    if isinstance(value, dict):
        return {key: reverse_collections(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(reverse_collections(item) for item in reversed(value))
    return value


def test_all_current_subject_fact_collections_are_permutation_invariant():
    original = subject()
    reordered = ValidationSubjectSnapshot.model_validate(reverse_collections(original.model_dump()))
    assert reordered.canonical_json() == original.canonical_json()
    assert reordered.fingerprint == original.fingerprint
    assert validate_subject(reordered) == validate_subject(original)


def test_authored_recipe_fact_order_does_not_replace_procedure_order():
    original = RecipeVersionSnapshot.model_validate(recipe_data())
    reordered = RecipeVersionSnapshot.model_validate(reverse_collections(original.model_dump()))
    assert original.procedure == reordered.procedure
    assert canonical_hash(original) == canonical_hash(reordered)
    changed = original.model_dump() | {"procedure": original.procedure + " Then rest."}
    assert canonical_hash(RecipeVersionSnapshot.model_validate(changed)) != canonical_hash(original)


@pytest.mark.parametrize("field", ["ledger_sequence", "phase", "occurred_at"])
def test_explicit_causal_fields_survive_collection_sorting(field):
    original = subject()
    data = original.model_dump()
    event = data["inventory"]["movements"][1]
    if field == "ledger_sequence":
        event[field] += 100
    elif field == "phase":
        event[field] = 60
    else:
        event[field] -= timedelta(seconds=1)
    changed = ValidationSubjectSnapshot.model_validate(data)
    assert changed.fingerprint != original.fingerprint


def test_unordered_hash_is_not_a_safe_encoding_for_future_implicit_sequences():
    # Counterexample only: these are NOT fields accepted by the frozen subject.
    first = {"steps": ["boil", "drain"]}
    second = {"steps": ["drain", "boil"]}
    assert first != second
    assert canonical_hash(first) == canonical_hash(second)
    with pytest.raises(ValueError):
        ValidationSubjectSnapshot.model_validate(subject().model_dump() | first)


def test_explicit_ordinals_preserve_a_future_ordered_process():
    first = {"steps": [{"ordinal": 1, "action": "boil"}, {"ordinal": 2, "action": "drain"}]}
    second = {"steps": [{"ordinal": 2, "action": "boil"}, {"ordinal": 1, "action": "drain"}]}
    assert canonical_hash(first) != canonical_hash(second)
    assert canonical_hash(first) == canonical_hash(reverse_collections(first))


def test_future_parallel_arrays_must_be_replaced_by_explicit_relationship_records():
    # BatchFlowLinkDraft is outside the current subject. Its parallel arrays must not
    # be inserted into this generic recursive sorter with positional pairing implied.
    first = {"lot_ids": ["lot-a", "lot-b"], "movement_ids": ["move-a", "move-b"]}
    second = first | {"movement_ids": ["move-b", "move-a"]}
    assert canonical_hash(first) == canonical_hash(second)
    pairs = [{"lot_id": "lot-a", "movement_id": "move-a"},
             {"lot_id": "lot-b", "movement_id": "move-b"}]
    swapped = [{"lot_id": "lot-a", "movement_id": "move-b"},
               {"lot_id": "lot-b", "movement_id": "move-a"}]
    assert canonical_hash(pairs) != canonical_hash(swapped)


def test_policy_content_can_change_without_changing_existing_source_frontier():
    original = subject()
    changed = ValidationSubjectSnapshot.model_validate(
        original.model_dump() | {"policy": coverage_policy(policy_version="2")}
    )
    assert changed.source_frontier == original.source_frontier
    assert changed.policy.fingerprint != original.policy.fingerprint
    assert changed.fingerprint != original.fingerprint
    # A commit guard comparing only today's frontier fields would miss this change.
    # This does not implement or simulate production authorization.
    assert not validate_subject(original).activation_authorized
    assert not validate_subject(changed).activation_authorized
