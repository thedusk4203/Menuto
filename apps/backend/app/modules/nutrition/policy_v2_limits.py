"""Server-owned structural limits; no nutrition constants or authority."""

from app.domain.feature_identity import canonical, canonical_bytes
from app.modules.nutrition.resolution_limits import ingest, structure

INPUT_BYTES = 32 * 1024 * 1024
RESULT_BYTES = 8 * 1024 * 1024
HANDOFF_BYTES = 48 * 1024 * 1024
CHECK_BYTES = 256 * 1024


class PolicyWork:
    def __init__(self):
        self.used = 0
        self.control = 0

    def reserve_control(self):
        # Count bounded error serialization in the same absolute budget. Exhausting
        # arithmetic work must still allow one small all-or-error diagnostic.
        self.charge(512)
        self.control = 512

    def charge(self, count=1):
        if type(count) is not int or count < 0 or self.used > 2_000_000 - count:
            raise ValueError("RESOURCE_EXCEEDED: policy work")
        self.used += count

    def tree(self, value):
        pending = [canonical(ingest(value, INPUT_BYTES))]
        while pending:
            item = pending.pop()
            self.charge()
            if isinstance(item, dict):
                pending.extend(item.values())
            elif isinstance(item, (list, tuple)):
                pending.extend(item)

    def number(self, value):
        self.charge()
        if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > 256:
            raise ValueError("RESOURCE_EXCEEDED: policy rational")
        return value

    def multiply(self, left, right):
        self.charge()
        if (
            abs(left.numerator).bit_length() + abs(right.numerator).bit_length() > 1024
            or left.denominator.bit_length() + right.denominator.bit_length() > 1024
        ):
            raise ValueError("RESOURCE_EXCEEDED: temporary product")
        return left * right

    def add(self, left, right):
        self.charge()
        numerator_bits = (
            max(
                abs(left.numerator).bit_length() + right.denominator.bit_length(),
                abs(right.numerator).bit_length() + left.denominator.bit_length(),
            )
            + 1
        )
        if (
            numerator_bits > 1024
            or left.denominator.bit_length() + right.denominator.bit_length() > 1024
        ):
            raise ValueError("RESOURCE_EXCEEDED: temporary sum")
        return left + right

    def output(self, value, limit):
        structure(value, limit)
        if len(canonical_bytes(value)) > limit:
            raise ValueError("RESOURCE_EXCEEDED: output bytes")
        self.tree(value)

    def failure_output(self, value, limit):
        structure(value, limit)
        pending = [canonical(value)]
        while pending:
            item = pending.pop()
            if self.control <= 0:
                raise ValueError("RESOURCE_EXCEEDED: control output")
            self.control -= 1
            if isinstance(item, dict):
                pending.extend(item.values())
            elif isinstance(item, (list, tuple)):
                pending.extend(item)
        if len(canonical_bytes(value)) > limit:
            raise ValueError("RESOURCE_EXCEEDED: output bytes")
