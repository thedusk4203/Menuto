"""Canonical byte mechanics only; no culinary truth or persistence ownership."""

import json
from datetime import datetime
from hashlib import sha256


def canonical(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="python")
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [canonical(v) for v in value]
    if isinstance(value, datetime):
        from datetime import UTC

        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, float):
        raise ValueError("Float is not a canonical exact primitive")
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def canonical_bytes(value):
    return json.dumps(
        canonical(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def identity_hash(value):
    return sha256(canonical_bytes(value)).hexdigest()


def unique_sorted(values, key=str):
    if len(set(map(key, values))) != len(values):
        raise ValueError("Duplicate source identity")
    return tuple(sorted(values, key=key))
