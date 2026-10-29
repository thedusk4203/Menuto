"""Server-owned structural bounds, never nutritional or clinical policy values."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

COMMAND_BYTES = 131_072
CAPTURE_BYTES = 4_194_304
CAPTURE_ROWS = 4096
HISTORY_DEPTH = 64
STRUCTURE_DEPTH = 32
INTEGER_MAX = (1 << 127) - 1
MANIFEST_ENTRIES = 32
INTERVAL_COUNT = 64
OPERATION_MILLISECONDS = 15_000


def check_structure(value, *, byte_limit=CAPTURE_BYTES):
    """Bound traversal before recursive canonicalization or model validation."""
    pending = [(value, 0)]
    size = nodes = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if depth > STRUCTURE_DEPTH or nodes > CAPTURE_ROWS * 128:
            raise ValueError("Nutrition source structural limit; no truncation")
        if isinstance(item, BaseModel):
            item = {k: getattr(item, k) for k in type(item).model_fields if hasattr(item, k)}
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ValueError("String object keys required")
                size += len(key.encode("utf-8")) + 4
                pending.append((child, depth + 1))
        elif isinstance(item, (tuple, list)):
            if len(item) > CAPTURE_ROWS:
                raise ValueError("Nutrition source row limit; no truncation")
            pending.extend((child, depth + 1) for child in item)
            size += len(item) + 2
        elif type(item) is int:
            if abs(item) > INTEGER_MAX:
                raise ValueError("Nutrition source integer size limit")
            size += len(str(item))
        elif isinstance(item, str):
            size += len(item.encode("utf-8")) + 2
        elif isinstance(item, datetime):
            if item.tzinfo is None or item.utcoffset() is None:
                raise ValueError("Aware source time required")
            size += 32
        elif isinstance(item, UUID):
            size += 38
        elif item is None or type(item) is bool:
            size += 5
        else:
            raise ValueError("Exact source primitives required; no float/coercion")
        if size > byte_limit:
            raise ValueError("Nutrition source byte limit; all-or-error")
