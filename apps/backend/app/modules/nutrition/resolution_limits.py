"""NRE server-owned structural budgets. No scientific or nutrition policy values."""

import json
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

REQUEST_BYTES = 256 * 1024
SOURCE_BYTES = 16 * 1024 * 1024
OWNER_ROWS = 8192
STATES = 16384
WITNESSES = 65536
WORK = 1_000_000
BITS = 256
DEADLINE_SECONDS = 60


def structure(value, byte_limit=SOURCE_BYTES):
    """Bound untrusted structures before canonicalization, hashing or arithmetic."""
    pending, size, nodes = [(value, 0)], 0, 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if depth > 32 or nodes > WORK:
            raise ValueError("RESOURCE_EXCEEDED: structure")
        if isinstance(item, BaseModel):
            item = {k: getattr(item, k) for k in type(item).model_fields if hasattr(item, k)}
        if isinstance(item, dict):
            size += 2
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ValueError("INVALID_SCOPE: string object keys required")
                size += len(json.dumps(key, ensure_ascii=False).encode()) + 2
                pending.append((child, depth + 1))
        elif isinstance(item, (tuple, list)):
            if len(item) > WITNESSES:
                raise ValueError("RESOURCE_EXCEEDED: collection")
            size += len(item) + 2
            pending.extend((child, depth + 1) for child in item)
        elif type(item) is int:
            if abs(item).bit_length() > BITS:
                raise ValueError("RESOURCE_EXCEEDED: integer")
            size += len(str(item))
        elif isinstance(item, str):
            if len(item) > 100_000:
                raise ValueError("RESOURCE_EXCEEDED: string")
            size += len(json.dumps(item, ensure_ascii=False).encode())
        elif isinstance(item, Decimal):
            if not item.is_finite() or len(str(item)) > 100_000:
                raise ValueError("INVALID_SCOPE: finite exact decimal required")
            if abs(item.as_tuple().exponent) > 77 or len(item.as_tuple().digits) > 78:
                raise ValueError("RESOURCE_EXCEEDED: decimal exponent/integer")
            size += len(str(item)) + 2
        elif isinstance(item, (UUID, datetime)):
            size += 40
        elif item is None or type(item) is bool:
            size += 5
        elif type(item).__module__.startswith("pydantic.networks"):
            size += len(str(item)) + 2
        else:
            raise ValueError("INVALID_SCOPE: exact primitives required, no float")
        if size > byte_limit:
            raise ValueError("RESOURCE_EXCEEDED: encoded bytes")


def ingest(value, byte_limit=SOURCE_BYTES):
    if isinstance(value, (str, bytes)):
        if len(value.encode() if isinstance(value, str) else value) > byte_limit:
            raise ValueError("RESOURCE_EXCEEDED: encoded bytes")

        def integer(token):
            if len(token.lstrip("-")) > 78:
                raise ValueError("RESOURCE_EXCEEDED: integer")
            number = int(token)
            if abs(number).bit_length() > BITS:
                raise ValueError("RESOURCE_EXCEEDED: integer")
            return number

        def no_float(token):
            raise ValueError("INVALID_SCOPE: no float or non-finite number")

        # Prevent deeply nested JSON before the decoder constructs its tree.
        depth, quoted, escaped = 0, False, False
        for ch in value.decode() if isinstance(value, bytes) else value:
            if escaped:
                escaped = False
            elif ch == "\\" and quoted:
                escaped = True
            elif ch == '"':
                quoted = not quoted
            elif not quoted and ch in "[{":
                depth += 1
                if depth > 32:
                    raise ValueError("RESOURCE_EXCEEDED: nesting")
            elif not quoted and ch in "]}":
                depth -= 1

        def unique_object(pairs):
            result = {}
            for key, child in pairs:
                if key in result:
                    raise ValueError("INVALID_SCOPE: duplicate JSON field")
                result[key] = child
            return result

        value = json.loads(
            value,
            parse_int=integer,
            parse_float=no_float,
            parse_constant=no_float,
            object_pairs_hook=unique_object,
        )
    structure(value, byte_limit)
    return value


class WorkBudget:
    def __init__(self, limit=WORK):
        if type(limit) is not int or not 0 < limit <= WORK:
            raise ValueError("RESOURCE_EXCEEDED: caller cannot raise work budget")
        self.limit, self.used = limit, 0

    def charge(self, amount=1):
        self.used += amount
        if self.used > self.limit:
            raise ValueError("RESOURCE_EXCEEDED: arithmetic work")

    def number(self, value):
        self.charge()
        if value.numerator.bit_length() > BITS or value.denominator.bit_length() > BITS:
            raise ValueError("RESOURCE_EXCEEDED: rational")
        return value

    def product(self, sizes, limit=STATES):
        total = 1
        for size in sizes:
            self.charge()
            if size < 0 or total > limit // max(size, 1):
                raise ValueError("RESOURCE_EXCEEDED: Cartesian product")
            total *= size
        return total
