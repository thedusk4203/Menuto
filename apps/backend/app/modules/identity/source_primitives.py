"""Bounded canonical primitives only; no source-state or authorization business evaluator."""

import hashlib
import json
from datetime import UTC, datetime, timezone
from uuid import UUID

from pydantic import BaseModel

from app.domain.snapshots import Horizon
from app.modules.identity import source_contracts as c
from app.modules.identity import source_limits as limits


class IdentityStructureError(ValueError):
    pass


class IdentityResourceError(ValueError):
    pass


def primitive(value, *, depth=0, budget=None):
    budget = [limits.SOURCE_NODES] if budget is None else budget
    budget[0] -= 1
    if budget[0] < 0:
        raise IdentityResourceError("Node limit")
    kind = type(value)
    if kind is datetime:
        if type(value.tzinfo) is not timezone:
            raise IdentityStructureError("Concrete zoned time required")
        return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if kind is UUID:
        return str(value)
    if isinstance(value, BaseModel):
        allowed = (
            kind.__module__ == c.__name__
            and kind.__name__.startswith("Identity")
            or kind is Horizon
        )
        if not allowed or set(value.__dict__) != set(kind.model_fields):
            raise IdentityStructureError("Unexpected or incomplete model")
        value = value.__dict__
        kind = dict
    if kind in (dict, list, tuple):
        if depth > limits.JSON_DEPTH:
            raise IdentityResourceError("Depth limit")
        if kind is dict:
            if any(type(key) is not str for key in value):
                raise IdentityStructureError("String keys required")
            for key in value:
                if len(key.encode("utf-8", "strict")) > 64:
                    raise IdentityResourceError("Key limit")
            return {
                key: primitive(item, depth=depth + 1, budget=budget) for key, item in value.items()
            }
        return [primitive(item, depth=depth + 1, budget=budget) for item in value]
    if kind is int:
        if not -(1 << 63) < value <= limits.INTEGER_MAX:
            raise IdentityResourceError("Integer limit")
        return value
    if kind is str:
        if "\x00" in value or any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            raise IdentityStructureError("Invalid string")
        value.encode("utf-8", "strict")
        return value
    if value is None or kind is bool:
        return value
    raise IdentityStructureError("Unsupported primitive")


def canonical(value):
    return json.dumps(
        primitive(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def fingerprint(tag, value):
    return hashlib.sha256(tag.encode("ascii") + b"\x00" + canonical(value)).hexdigest()


def request_fingerprint(raw):
    if type(raw) is not str or len(raw.encode("utf-8", "strict")) > limits.REQUEST_BYTES:
        raise IdentityResourceError("Request byte limit")
    return hashlib.sha256(
        b"identity.request-preimage.v1\x00" + raw.encode("utf-8", "strict")
    ).hexdigest()


class _OpaqueNumber:
    """Uninterpreted child-axis token, never a value in an Identity contract/hash."""


def strict_load(raw, *, maximum=limits.SOURCE_BYTES, _context_only=False):
    if type(raw) is str:
        if len(raw) > maximum:
            raise IdentityResourceError("Byte limit")
        raw = raw.encode("utf-8", "strict")
    if type(raw) is not bytes:
        raise IdentityStructureError("Exact bytes or string required")
    if len(raw) > maximum:
        raise IdentityResourceError("Byte limit")
    text = raw.decode("utf-8", "strict")
    # Bound containers, lexeme size and work before allocating decoded JSON structures.
    depth, quoted, escaped, integer_digits, tokens = 0, False, False, 0, 0
    for char in text:
        if not quoted and char in "[{: ," and char != " ":
            tokens += 1
            if tokens > limits.SOURCE_NODES:
                raise IdentityResourceError("Lexical node limit")
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            integer_digits = 0
        elif char in "[{":
            depth += 1
            if depth > limits.JSON_DEPTH + 1:
                raise IdentityResourceError("Depth limit")
        elif char in "]}":
            depth -= 1
        elif char.isdecimal():
            integer_digits += 1
            if integer_digits > 19:
                raise IdentityResourceError("Integer limit")
        else:
            integer_digits = 0

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise IdentityStructureError("Duplicate key")
            result[key] = value
        return result

    def noninteger(_):
        raise IdentityStructureError("No float or non-finite numbers")

    result = json.loads(
        text,
        object_pairs_hook=pairs,
        parse_float=(lambda _: _OpaqueNumber()) if _context_only else noninteger,
        parse_constant=noninteger,
    )
    if not _context_only:
        return primitive(result)
    # Identity binds exact raw bytes/context; frozen EPI alone interprets axis values.
    remaining = [limits.SOURCE_NODES]

    def bounded(value, level=0):
        remaining[0] -= 1
        if remaining[0] < 0 or level > limits.JSON_DEPTH + 1:
            raise IdentityResourceError("Child structure limit")
        if type(value) is dict:
            for key, item in value.items():
                primitive(key)
                if len(key.encode("utf-8")) > 64:
                    raise IdentityResourceError("Child key limit")
                bounded(item, level + 1)
        elif type(value) is list:
            for item in value:
                bounded(item, level + 1)
        elif type(value) is not _OpaqueNumber:
            primitive(value)

    bounded(result)
    return result


def parse(model, value, *, maximum=limits.SOURCE_BYTES):
    if type(value) in (bytes, str):
        value = strict_load(value, maximum=maximum)
    else:
        value = primitive(value)
        if len(canonical(value)) > maximum:
            raise IdentityResourceError("Byte limit")
    return model.model_validate_json(canonical(value))


def without(value, field):
    data = primitive(value)
    if field not in data:
        raise IdentityStructureError("Missing fingerprint field")
    return {key: item for key, item in data.items() if key != field}
