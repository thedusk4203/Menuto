"""Bounded explicit declarations only; no authentication, numerical policy or admission."""

import json
import re
from datetime import datetime, timezone
from uuid import UUID

from pydantic import ValidationError

from app.domain.canonical import canonical_hash
from app.domain.snapshots import Horizon
from app.domain.units import Money
from app.modules.policy import explicit_intent_contracts as c

_AXES = ("nutrition_precision", "cost_preference", "kitchen_effort", "budget")
_HEADER = ("contract_version", "source", "environment")
_ROOT = (*_HEADER, "context", *_AXES)
_CONTEXT = (
    "request_id",
    "request_revision",
    "household_id",
    "actor_user_id",
    "tracked_member_id",
    "horizon",
    "declared_at",
)
_TIME = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-]\d\d:\d\d)\Z")


class _Fault(Exception):
    def __init__(self, code, path="$", outcome="INVALID_INPUT"):
        self.code, self.path, self.outcome = code, path, outcome


class _Reader:
    """Limits precede canonicalization and arbitrary object serialization."""

    def __init__(self):
        self.nodes = self.work = self.size = 0
        self.active = set()

    def charge(self, amount=1):
        self.work += amount
        if self.work > 4096:
            raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")

    def visit(self, depth):
        self.charge()
        self.nodes += 1
        if depth > 8 or self.nodes > 2048:
            raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")

    def string(self, value, key=False):
        if len(value) > 256 or len(value.encode("utf-8")) > 1024:
            raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        if key and (not value.isascii() or len(value) > 64):
            raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        return value

    def integer(self, value):
        if value.bit_length() > 63:
            raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        return value

    def walk(self, value, depth=1):
        self.visit(depth)
        kind = type(value)
        if kind in (str, int, bool) or value is None:
            if kind is str:
                self.string(value)
            if kind is int:
                self.integer(value)
            self.size += len(json.dumps(value, ensure_ascii=False).encode("utf-8"))
            result = value
        elif kind is UUID:
            result = self.string(str(value))
            self.size += len(result) + 2
        elif kind is datetime:
            if type(value.tzinfo) is not timezone:
                raise _Fault("MALFORMED_SHAPE")
            result = value.isoformat()
            self.size += len(result) + 2
        else:
            if id(value) in self.active:
                raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
            self.active.add(id(value))
            try:
                if kind in (
                    c.ExplicitPlanIntentRequestV1,
                    c.ExplicitPlanIntentContextV1,
                    c.ExplicitPlanIntentBudgetV1,
                    Money,
                    Horizon,
                ):
                    stored = object.__getattribute__(value, "__dict__")
                    extra = object.__getattribute__(value, "__pydantic_extra__")
                    private = object.__getattribute__(value, "__pydantic_private__")
                    if type(stored) is not dict or extra or private:
                        raise _Fault("MALFORMED_SHAPE")
                    result = self.mapping(stored, depth)
                elif kind is dict:
                    result = self.mapping(value, depth)
                elif kind in (list, tuple):
                    if len(value) > 32:
                        raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
                    self.size += len(value) + 2
                    result = [self.walk(v, depth + 1) for v in value]
                else:
                    raise _Fault("MALFORMED_SHAPE")
            finally:
                self.active.remove(id(value))
        if self.size > 49152:
            raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        return result

    def mapping(self, value, depth):
        if len(value) > 32:
            raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        self.size += len(value) * 2 + 2
        out = {}
        for key, item in value.items():
            if type(key) is not str:
                raise _Fault("MALFORMED_SHAPE")
            self.string(key, True)
            self.size += len(json.dumps(key).encode())
            out[key] = self.walk(item, depth + 1)
        return out

    def decode(self, source):
        if type(source) is not bytes:
            return self.walk(source)
        if len(source) > 49152:
            raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        try:
            text = source.decode("utf-8")
        except UnicodeDecodeError as error:
            raise _Fault("MALFORMED_ENCODING") from error
        self.preflight(text)
        self.text, self.pos = text, 0
        value = self.value(1)
        self.space()
        if self.pos != len(text):
            raise _Fault("MALFORMED_SHAPE")
        return value

    def preflight(self, text):
        # A full lexical resource pass precedes syntax failures/duplicate-key detection.
        # It never recursively decodes a document and never constructs integers >19 digits.
        position, nodes, containers = 0, 0, []
        while position < len(text):
            char = text[position]
            if char in "[{":
                containers.append(1)
                nodes += 1
                if len(containers) > 8:
                    raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
            elif char in "]}":
                if containers:
                    containers.pop()
            elif char == "," and containers:
                containers[-1] += 1
                if containers[-1] > 32:
                    raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
            elif char == '"':
                start, position, escape = position, position + 1, False
                while position < len(text):
                    if position - start > 6144:
                        raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
                    current = text[position]
                    if current == '"' and not escape:
                        break
                    escape = current == "\\" and not escape
                    position += 1
                if position >= len(text):
                    raise _Fault("MALFORMED_SHAPE")
                end = position + 1
                while end < len(text) and text[end] in " \t\r\n":
                    end += 1
                key = end < len(text) and text[end] == ":"
                self.string(json.loads(text[start : position + 1]), key)
                nodes += not key
            elif char in "-0123456789":
                token = re.match(r"-?[0-9]+", text[position:])
                if token:
                    raw = token.group()
                    if len(raw.lstrip("-")) > 19:
                        raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
                    self.integer(int(raw))
                    position += len(raw) - 1
                    nodes += 1
            elif text.startswith(("true", "false", "null"), position):
                token = next(t for t in ("true", "false", "null") if text.startswith(t, position))
                position += len(token) - 1
                nodes += 1
            if nodes > 2048:
                raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
            position += 1

    def space(self):
        while self.pos < len(self.text) and self.text[self.pos] in " \t\r\n":
            self.pos += 1

    def quoted(self, key=False):
        start = self.pos
        self.pos += 1
        escaped = False
        while self.pos < len(self.text):
            char = self.text[self.pos]
            self.pos += 1
            if self.pos - start > 6146:
                raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
            if char == '"' and not escaped:
                try:
                    return self.string(json.loads(self.text[start : self.pos]), key)
                except (ValueError, UnicodeError) as error:
                    raise _Fault("MALFORMED_SHAPE") from error
            escaped = char == "\\" and not escaped
        raise _Fault("MALFORMED_SHAPE")

    def value(self, depth):
        self.visit(depth)
        self.space()
        if self.pos >= len(self.text):
            raise _Fault("MALFORMED_SHAPE")
        char = self.text[self.pos]
        if char == '"':
            return self.quoted()
        if char in "[{":
            obj = char == "{"
            closing, out = ("}", {}) if obj else ("]", [])
            self.pos += 1
            self.space()
            if self.pos < len(self.text) and self.text[self.pos] == closing:
                self.pos += 1
                return out
            while True:
                if len(out) >= 32:
                    raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
                self.space()
                if obj:
                    if self.pos >= len(self.text) or self.text[self.pos] != '"':
                        raise _Fault("MALFORMED_SHAPE")
                    key = self.quoted(True)
                    if key in out:
                        raise _Fault("DUPLICATE_KEY")
                    self.space()
                    if self.pos >= len(self.text) or self.text[self.pos] != ":":
                        raise _Fault("MALFORMED_SHAPE")
                    self.pos += 1
                    out[key] = self.value(depth + 1)
                else:
                    out.append(self.value(depth + 1))
                self.space()
                if self.pos >= len(self.text):
                    raise _Fault("MALFORMED_SHAPE")
                end = self.text[self.pos]
                self.pos += 1
                if end == closing:
                    return out
                if end != ",":
                    raise _Fault("MALFORMED_SHAPE")
        for token, value in (("true", True), ("false", False), ("null", None)):
            if self.text.startswith(token, self.pos):
                self.pos += len(token)
                return value
        match = re.match(r"-?(?:0|[1-9][0-9]*)", self.text[self.pos :])
        if not match:
            raise _Fault("MALFORMED_SHAPE")
        token = match.group()
        if len(token.lstrip("-")) > 19:
            raise _Fault("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        self.pos += len(token)
        if self.pos < len(self.text) and self.text[self.pos] in ".eE":
            raise _Fault("MALFORMED_SHAPE")
        return self.integer(int(token))


def _hash(kind, body):
    return canonical_hash({"domain": f"menuto.explicit-intent.{kind}.v1", "body": body})


def _closed():
    return dict(
        environment="TEST_ONLY",
        source_authority="UNAUTHENTICATED_DECLARATION",
        validation_authority="UNVERIFIED_TRANSPORT",
        numerical_use="NOT_ADMITTED",
        production_admission="CLOSED",
        resolved_plan_policy_ready=False,
        planner_ready=False,
        activation_ready=False,
    )


def _shape(value, keys, path):
    if type(value) is not dict:
        raise _Fault("MALFORMED_SHAPE", path)
    unknown = sorted(set(value) - set(keys))
    if unknown:
        raise _Fault("UNKNOWN_FIELD", path)


def _interpret(value, reader):
    reader.charge()
    _shape(value, _ROOT, "$")
    for name in _HEADER:
        if name in value and type(value[name]) is not str:
            raise _Fault("MALFORMED_SHAPE", "$." + name)
    nested = []
    if "context" in value:
        context = value["context"]
        _shape(context, _CONTEXT, "$.context")
        nested.append((context, _CONTEXT, "$.context"))
        if "horizon" in context:
            _shape(context["horizon"], ("start", "end"), "$.context.horizon")
            nested.append((context["horizon"], ("start", "end"), "$.context.horizon"))
    if value.get("budget") is not None:
        budget = value["budget"]
        _shape(budget, ("constraint", "amount"), "$.budget")
        nested.append((budget, ("constraint", "amount"), "$.budget"))
        if budget.get("amount") is not None:
            _shape(budget["amount"], ("amount_minor", "currency"), "$.budget.amount")
            nested.append((budget["amount"], ("amount_minor", "currency"), "$.budget.amount"))
    for key, expected, code in (
        ("contract_version", "explicit-plan-intent-request.v1", "VERSION_UNSUPPORTED"),
        ("source", "REQUEST_EXPLICIT", "SOURCE_UNSUPPORTED"),
        ("environment", "TEST_ONLY", "ENVIRONMENT_UNSUPPORTED"),
    ):
        if key in value and value[key] != expected:
            raise _Fault(code, "$." + key, "UNSUPPORTED")
    for record, keys, path in ((value, _ROOT, "$"), *nested):
        for key in keys:
            reader.charge()
            if key not in record:
                raise _Fault("MISSING_FIELD", path + "." + key, "MISSING_INPUT")
    context = value["context"]
    try:
        for key in ("request_id", "household_id", "actor_user_id", "tracked_member_id"):
            raw = context[key]
            if type(raw) is not str or str(UUID(raw)) != raw:
                raise ValueError("UUID")
        for raw in (context["declared_at"], *context["horizon"].values()):
            if type(raw) is not str or not _TIME.fullmatch(raw):
                raise ValueError("time")
        normalized = c.ExplicitPlanIntentContextV1.model_validate(context).model_dump(mode="json")
    except (ValueError, TypeError) as error:
        raise _Fault("CONTEXT_INVALID", "$.context") from error
    for key, allowed in zip(
        _AXES[:3],
        (
            ("RELAXED", "STANDARD", "PRECISION"),
            ("LOW", "NORMAL", "HIGH"),
            ("MINIMAL", "NORMAL", "FLEXIBLE"),
        ),
        strict=True,
    ):
        if value[key] is not None and (type(value[key]) is not str or value[key] not in allowed):
            raise _Fault("AXIS_INVALID", "$." + key)
    budget = value["budget"]
    if budget is not None:
        kind, amount = budget["constraint"], budget["amount"]
        valid = type(kind) is str and kind in ("NONE", "TARGET", "SPEND_LIMIT")
        valid = valid and ((kind == "NONE") == (amount is None))
        if amount is not None:
            valid = valid and type(amount["amount_minor"]) is int and amount["amount_minor"] >= 0
            valid = valid and type(amount["currency"]) is str
            valid = valid and re.fullmatch(r"[A-Z]{3}", amount["currency"]) is not None
        if not valid:
            raise _Fault("BUDGET_INVALID", "$.budget")
    request = dict(value, context=normalized)
    fingerprint = _hash("input", request)
    for key in _AXES:
        if value[key] is None:
            return (
                "MISSING_INPUT",
                None,
                fingerprint,
                [dict(code="AXIS_UNDECLARED", path="$." + key)],
            )
    values = {key: request[key] for key in _AXES}
    evidence = []
    for key in _AXES:
        reader.charge()
        evidence.append(
            dict(
                axis=key.upper(),
                source="REQUEST_EXPLICIT",
                input_fingerprint=fingerprint,
                context_fingerprint=_hash("context", normalized),
                value_fingerprint=canonical_hash(
                    dict(
                        domain="menuto.explicit-intent.axis.v1", axis=key.upper(), value=values[key]
                    )
                ),
                interpretation_version="EXPLICIT_IDENTITY_V1",
            )
        )
    payload = dict(
        contract_version="resolved-explicit-plan-intent.v1",
        context=normalized,
        values=values,
        axis_evidence=evidence,
        environment="TEST_ONLY",
        semantic_fingerprint=canonical_hash(
            dict(
                domain="menuto.explicit-intent.semantic.v1",
                interpretation_version="EXPLICIT_IDENTITY_V1",
                values=values,
            )
        ),
    )
    return "AVAILABLE_TEST_ONLY", payload, fingerprint, []


def resolve_explicit_plan_intent_v1(source):
    """Interpret one retained declaration. No consumer accepts this as authorization."""
    reader = _Reader()
    try:
        outcome, payload, fingerprint, diagnostics = _interpret(reader.decode(source), reader)
    except _Fault as failure:
        outcome, payload, fingerprint = failure.outcome, None, None
        diagnostics = [dict(code=failure.code, path=failure.path)]
    except (ValueError, TypeError, OverflowError, UnicodeError, ValidationError):
        outcome, payload, fingerprint = "INVALID_INPUT", None, None
        diagnostics = [dict(code="MALFORMED_SHAPE", path="$")]
    body = dict(
        contract_version="plan-intent-resolution.v1",
        interpretation_version="EXPLICIT_IDENTITY_V1",
        outcome=outcome,
        payload=payload,
        input_fingerprint=fingerprint,
        diagnostics=diagnostics,
        **_closed(),
    )
    return c.PlanIntentResolutionV1(**body, result_fingerprint=_hash("result", body))
