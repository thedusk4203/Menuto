"""Canonical hashes for unordered immutable fact collections; no business enforcement."""

import hashlib
import json

from pydantic import BaseModel


def canonical_value(value):
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        return {k: canonical_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return sorted((canonical_value(v) for v in value), key=canonical_json)
    return value


def canonical_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def canonical_hash(value):
    return hashlib.sha256(canonical_json(canonical_value(value)).encode("utf-8")).hexdigest()
