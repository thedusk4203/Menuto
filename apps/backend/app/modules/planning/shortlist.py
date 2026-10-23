"""Pure conservative coverage frontier. No source resolution, ranking or authority."""

import json
from dataclasses import dataclass
from hashlib import sha256

from app.modules.planning.contracts import (
    CandidateGroundingRequest,
    CandidateGroundingResult,
    ParetoShortlistDraft,
    ShortlistDominanceWitness,
    ShortlistInputFailure,
    ShortlistPolicyDraft,
    grounding_canonical_json,
)

_CAPTURE_SEAL = object()


def _digest(value):
    return sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True, slots=True, init=False)
class CapturedShortlistPool:
    """Server-local source provenance, not a wire token or PRECOMMIT capability.

    Only the capture adapter mints this value. Python internals are trusted code, not a
    hostile-code security sandbox. JSON/Pydantic result ingestion cannot mint a pool.
    """

    _entries: tuple
    _seal: object

    def __init__(self, entries, *, _seal=None):
        if _seal is not _CAPTURE_SEAL:
            raise TypeError(
                "Use canonical shortlist capture; serialized candidates are not ingress"
            )
        object.__setattr__(self, "_entries", tuple(entries))
        object.__setattr__(self, "_seal", _seal)


def _captured_pool(entries):
    """Trusted adapter-only mint after canonical grounding; not exported by public facade."""
    checked = []
    for request, result in entries:
        request = CandidateGroundingRequest.model_validate(request.model_dump())
        result = CandidateGroundingResult.model_validate(result.model_dump())
        if result.candidate is not None and result.candidate.request != request:
            raise ValueError("Captured candidate belongs to a different request")
        checked.append((request, result))
    return CapturedShortlistPool(checked, _seal=_CAPTURE_SEAL)


def _comparison(candidate):
    data = candidate.model_dump(mode="json")
    data["request"].pop("procurement_class_ids")
    sources = data["sources"]
    procurements = sources.pop("procurements")
    statuses = sources.pop("retailer_statuses")
    paths = set()
    for line in data["ingredient_facts"]:
        for path in line.pop("procurement_paths"):
            paths.add((line["requirement_id"], grounding_canonical_json(path)))
    data.pop("fingerprint")
    partition = sha256(grounding_canonical_json(data).encode()).hexdigest()
    return partition, (
        frozenset(paths),
        frozenset(grounding_canonical_json(p) for p in procurements),
        frozenset(grounding_canonical_json(s) for s in statuses),
    )


def _dominates(a, b):
    return a[0] > b[0] and a[1] >= b[1] and a[2] >= b[2]


def _result(
    *, policy, identity, status, unique=None, count=None, candidates=(), witnesses=(), failures=()
):
    fields = dict(
        policy=policy,
        input_fingerprint=identity,
        status=status,
        unique_candidate_count=unique,
        frontier_count=count,
        candidates=candidates,
        dominance=witnesses,
        failures=failures,
    )
    temporary = ParetoShortlistDraft.model_construct(**fields)
    return ParetoShortlistDraft(**fields, fingerprint=temporary.expected_fingerprint())


def shortlist_grounded_pool(pool, policy):
    """Reduce captured possibilities only; never authenticate hashes or re-ground sources."""
    if type(pool) is not CapturedShortlistPool or pool._seal is not _CAPTURE_SEAL:
        raise TypeError("Canonical captured pool required, not candidate JSON/ready flags")
    policy = ShortlistPolicyDraft.model_validate(policy.model_dump())
    identity = _digest(
        sorted(
            {
                grounding_canonical_json(
                    dict(request=q.model_dump(mode="json"), result=r.model_dump(mode="json"))
                )
                for q, r in pool._entries
            }
        )
    )
    if len(pool._entries) > policy.max_inputs:
        return _result(policy=policy, identity=identity, status="INPUT_LIMIT_EXCEEDED")
    candidates = {}
    failures = {}
    for request, result in pool._entries:
        if result.candidate is None:
            key = sha256(grounding_canonical_json(request.model_dump(mode="json")).encode())
            failure = ShortlistInputFailure(
                request_fingerprint=key.hexdigest(),
                status=result.status,
                issues=tuple(
                    sorted(
                        result.issues,
                        key=lambda i: grounding_canonical_json(i.model_dump(mode="json")),
                    )
                ),
            )
            failures[grounding_canonical_json(failure.model_dump(mode="json"))] = failure
        else:
            candidate = result.candidate
            previous = candidates.get(candidate.fingerprint)
            # Identical semantic hashes may carry differently ordered fact tuples.
            # Preserve an original value, but choose it independently of arrival order.
            if previous is None or candidate.model_dump_json() < previous.model_dump_json():
                candidates[candidate.fingerprint] = candidate
    if failures:
        return _result(
            policy=policy,
            identity=identity,
            status="GROUNDING_FAILED",
            unique=len(candidates),
            failures=tuple(failures[k] for k in sorted(failures)),
        )
    if not candidates:
        return _result(policy=policy, identity=identity, status="EMPTY", unique=0, count=0)
    partitions = {}
    comparisons = {}
    for key in sorted(candidates):
        partition, coverage = _comparison(candidates[key])
        comparisons[key] = (partition, coverage)
        partitions.setdefault(partition, []).append(key)
    frontier = []
    for keys in partitions.values():
        frontier.extend(
            k
            for k in keys
            if not any(_dominates(comparisons[j][1], comparisons[k][1]) for j in keys if j != k)
        )
    frontier.sort()
    if len(frontier) > policy.max_frontier:
        return _result(
            policy=policy,
            identity=identity,
            status="FRONTIER_LIMIT_EXCEEDED",
            unique=len(candidates),
            count=len(frontier),
        )
    witnesses = []
    for key in sorted(candidates.keys() - set(frontier)):
        partition, coverage = comparisons[key]
        winner = next(
            k
            for k in frontier
            if comparisons[k][0] == partition and _dominates(comparisons[k][1], coverage)
        )
        witnesses.append(
            ShortlistDominanceWitness(
                removed_fingerprint=key,
                retained_fingerprint=winner,
                partition_fingerprint=partition,
            )
        )
    return _result(
        policy=policy,
        identity=identity,
        status="COMPLETE",
        unique=len(candidates),
        count=len(frontier),
        candidates=tuple(candidates[k] for k in frontier),
        witnesses=tuple(witnesses),
    )
