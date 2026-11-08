"""Independent retained-declaration reconstruction. Never imports a Policy evaluator."""

import json
import re
from datetime import datetime, timezone
from uuid import UUID

from app.domain.canonical import canonical_hash
from app.domain.snapshots import Horizon
from app.domain.units import Money
from app.modules.policy.explicit_intent_contracts import (
    ExplicitPlanIntentBudgetV1,
    ExplicitPlanIntentContextV1,
    ExplicitPlanIntentRequestV1,
    ExplicitPlanIntentValuesV1,
    PlanIntentAxisEvidenceV1,
    PlanIntentCheckV1,
    PlanIntentDiagnosticV1,
    PlanIntentResolutionV1,
    ResolvedExplicitPlanIntentV1,
)

_MODELS = (
    ExplicitPlanIntentBudgetV1,
    ExplicitPlanIntentContextV1,
    ExplicitPlanIntentRequestV1,
    ExplicitPlanIntentValuesV1,
    PlanIntentAxisEvidenceV1,
    PlanIntentCheckV1,
    PlanIntentDiagnosticV1,
    PlanIntentResolutionV1,
    ResolvedExplicitPlanIntentV1,
    Money,
    Horizon,
)


class _Problem(Exception):
    def __init__(self, code, path="$", outcome="INVALID_INPUT", unsafe=False):
        self.code, self.path, self.outcome, self.unsafe = code, path, outcome, unsafe


class _Bounds:
    def __init__(self):
        self.work = 0

    def spend(self):
        self.work += 1
        if self.work > 4096:
            raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")

    def text(self, value, key=False):
        if len(value) > 256 or len(value.encode("utf-8")) > 1024:
            raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        if key and (not value.isascii() or len(value) > 64):
            raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        return value

    def integer(self, text):
        if len(text.lstrip("-")) > 19:
            raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        value = int(text)
        if not -9_223_372_036_854_775_807 <= value <= 9_223_372_036_854_775_807:
            raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        return value

    def pairs(self, entries):
        if len(entries) > 32:
            raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        result = {}
        for key, value in entries:
            self.text(key, True)
            if key in result:
                raise _Problem("DUPLICATE_KEY")
            result[key] = value
        return result

    def bad_number(self, _text):
        raise _Problem("MALFORMED_SHAPE")

    def bytes(self, value):
        if len(value) > 49152:
            raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
        try:
            text = value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise _Problem("MALFORMED_ENCODING") from error
        # Bound nesting and individual strings before the standard recursive JSON decoder.
        depth, pos, nodes, entries = 0, 0, 0, []
        while pos < len(text):
            char = text[pos]
            if char in "[{":
                depth += 1
                nodes += 1
                entries.append(1)
                if depth > 8:
                    raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
            elif char in "]}":
                depth = max(0, depth - 1)
                if entries:
                    entries.pop()
            elif char == "," and entries:
                entries[-1] += 1
                if entries[-1] > 32:
                    raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
            elif char == '"':
                start, escaped = pos, False
                pos += 1
                while pos < len(text):
                    current = text[pos]
                    if pos - start > 6144:
                        raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
                    if current == '"' and not escaped:
                        look = pos + 1
                        while look < len(text) and text[look] in " \t\r\n":
                            look += 1
                        key = look < len(text) and text[look] == ":"
                        self.text(json.loads(text[start : pos + 1]), key)
                        nodes += not key
                        break
                    escaped = current == "\\" and not escaped
                    pos += 1
            elif char in "-0123456789":
                token = re.match(r"-?[0-9]+", text[pos:])
                if token:
                    self.integer(token.group())
                    pos += len(token.group()) - 1
                    nodes += 1
            elif text.startswith(("true", "false", "null"), pos):
                word = next(w for w in ("true", "false", "null") if text.startswith(w, pos))
                pos += len(word) - 1
                nodes += 1
            if nodes > 2048:
                raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
            pos += 1
        return json.loads(
            text,
            parse_int=self.integer,
            parse_float=self.bad_number,
            parse_constant=self.bad_number,
            object_pairs_hook=self.pairs,
        )

    def retain(self, source):
        if type(source) is bytes:
            source = self.bytes(source)
        active, count, encoded = set(), 0, 0

        def copy(value, level):
            nonlocal count, encoded
            self.spend()
            count += 1
            if count > 2048 or level > 8:
                raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
            kind = type(value)
            if kind is str:
                result = self.text(value)
                encoded += len(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            elif kind is int:
                if value.bit_length() > 63:
                    raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
                result = self.integer(str(value))
                encoded += len(str(result))
            elif value is None or kind is bool:
                result = value
                encoded += 5
            elif kind is float:
                # A known invalid primitive can be faithfully classified without hooks.
                raise _Problem("MALFORMED_SHAPE")
            elif kind is UUID:
                result = str(value)
                encoded += len(result) + 2
            elif kind is datetime:
                if type(value.tzinfo) is not timezone:
                    raise _Problem("MALFORMED_SHAPE", unsafe=True)
                result = value.isoformat()
                encoded += len(result) + 2
            else:
                if id(value) in active:
                    raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
                active.add(id(value))
                try:
                    if kind in _MODELS:
                        if object.__getattribute__(
                            value, "__pydantic_extra__"
                        ) or object.__getattribute__(value, "__pydantic_private__"):
                            raise _Problem("MALFORMED_SHAPE", unsafe=True)
                        stored = object.__getattribute__(value, "__dict__")
                        if type(stored) is not dict:
                            raise _Problem("MALFORMED_SHAPE", unsafe=True)
                        result = record(stored, level)
                    elif kind is dict:
                        result = record(value, level)
                    elif kind in (list, tuple):
                        if len(value) > 32:
                            raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
                        encoded += len(value) + 2
                        result = [copy(item, level + 1) for item in value]
                    else:
                        raise _Problem("MALFORMED_SHAPE", unsafe=True)
                finally:
                    active.remove(id(value))
            if encoded > 49152:
                raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
            return result

        def record(value, level):
            nonlocal encoded
            if len(value) > 32:
                raise _Problem("STRUCTURE_LIMIT", outcome="RESOURCE_EXCEEDED")
            encoded += len(value) * 2 + 2
            result = {}
            for key, item in value.items():
                if type(key) is not str:
                    raise _Problem("MALFORMED_SHAPE", unsafe=True)
                self.text(key, True)
                encoded += len(json.dumps(key).encode())
                result[key] = copy(item, level + 1)
            return result

        return copy(source, 1)


def _digest(kind, body):
    return canonical_hash({"domain": "menuto.explicit-intent." + kind + ".v1", "body": body})


def _non_authority():
    return {
        "environment": "TEST_ONLY",
        "source_authority": "UNAUTHENTICATED_DECLARATION",
        "validation_authority": "UNVERIFIED_TRANSPORT",
        "numerical_use": "NOT_ADMITTED",
        "production_admission": "CLOSED",
        "resolved_plan_policy_ready": False,
        "planner_ready": False,
        "activation_ready": False,
    }


def _reconstruct(source, budget):
    """Independent, finite semantic reconstruction from retained primitive declarations."""
    header = ("contract_version", "source", "environment")
    axes = ("nutrition_precision", "cost_preference", "kitchen_effort", "budget")
    root_keys = header + ("context",) + axes
    context_keys = (
        "request_id",
        "request_revision",
        "household_id",
        "actor_user_id",
        "tracked_member_id",
        "horizon",
        "declared_at",
    )
    records = [(source, root_keys, "$")]
    if type(source) is dict:
        if "context" in source:
            records.append((source["context"], context_keys, "$.context"))
            if type(source["context"]) is dict and "horizon" in source["context"]:
                records.append(
                    (source["context"]["horizon"], ("start", "end"), "$.context.horizon")
                )
        if source.get("budget") is not None:
            records.append((source["budget"], ("constraint", "amount"), "$.budget"))
            if type(source["budget"]) is dict and source["budget"].get("amount") is not None:
                records.append(
                    (source["budget"]["amount"], ("amount_minor", "currency"), "$.budget.amount")
                )
    for record, keys, path in records:
        if type(record) is not dict:
            raise _Problem("MALFORMED_SHAPE", path)
        if set(record).difference(keys):
            raise _Problem("UNKNOWN_FIELD", path)
        if path == "$":
            for key in header:
                if key in record and type(record[key]) is not str:
                    raise _Problem("MALFORMED_SHAPE", "$." + key)
    accepted_headers = ("explicit-plan-intent-request.v1", "REQUEST_EXPLICIT", "TEST_ONLY")
    for key, expected, code in zip(
        header,
        accepted_headers,
        ("VERSION_UNSUPPORTED", "SOURCE_UNSUPPORTED", "ENVIRONMENT_UNSUPPORTED"),
        strict=True,
    ):
        if key in source and source[key] != expected:
            raise _Problem(code, "$." + key, "UNSUPPORTED")
    for record, keys, path in records:
        for key in keys:
            budget.spend()
            if key not in record:
                raise _Problem("MISSING_FIELD", path + "." + key, "MISSING_INPUT")
    context = source["context"]
    try:
        for key in ("request_id", "household_id", "actor_user_id", "tracked_member_id"):
            raw = context[key]
            if type(raw) is not str or raw != str(UUID(raw)):
                raise ValueError("identity")
        times = [context["declared_at"], context["horizon"]["start"], context["horizon"]["end"]]
        for value in times:
            if type(value) is not str or not re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
                r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})",
                value,
            ):
                raise ValueError("time")
        context = ExplicitPlanIntentContextV1.model_validate(context).model_dump(mode="json")
    except (ValueError, TypeError) as error:
        raise _Problem("CONTEXT_INVALID", "$.context") from error
    choices = {
        "nutrition_precision": {"RELAXED", "STANDARD", "PRECISION"},
        "cost_preference": {"LOW", "NORMAL", "HIGH"},
        "kitchen_effort": {"MINIMAL", "NORMAL", "FLEXIBLE"},
    }
    for key in axes[:3]:
        value = source[key]
        if value is not None and (type(value) is not str or value not in choices[key]):
            raise _Problem("AXIS_INVALID", "$." + key)
    declared_budget = source["budget"]
    if declared_budget is not None:
        kind, amount = declared_budget["constraint"], declared_budget["amount"]
        if type(kind) is not str or kind not in {"NONE", "TARGET", "SPEND_LIMIT"}:
            raise _Problem("BUDGET_INVALID", "$.budget")
        if kind == "NONE":
            valid = amount is None
        else:
            valid = amount is not None
        if amount is not None:
            valid = (
                valid
                and type(amount["amount_minor"]) is int
                and amount["amount_minor"] >= 0
                and type(amount["currency"]) is str
                and re.fullmatch("[A-Z]{3}", amount["currency"]) is not None
            )
        if not valid:
            raise _Problem("BUDGET_INVALID", "$.budget")
    normalized_source = {**source, "context": context}
    input_hash = _digest("input", normalized_source)
    values = {axis: source[axis] for axis in axes}
    for axis in axes:
        if values[axis] is None:
            return _resolution(
                "MISSING_INPUT",
                None,
                input_hash,
                [{"code": "AXIS_UNDECLARED", "path": "$." + axis}],
            )
    evidence = []
    for axis in axes:
        budget.spend()
        evidence.append(
            {
                "axis": axis.upper(),
                "source": "REQUEST_EXPLICIT",
                "input_fingerprint": input_hash,
                "context_fingerprint": _digest("context", context),
                "value_fingerprint": canonical_hash(
                    {
                        "domain": "menuto.explicit-intent.axis.v1",
                        "axis": axis.upper(),
                        "value": values[axis],
                    }
                ),
                "interpretation_version": "EXPLICIT_IDENTITY_V1",
            }
        )
    payload = {
        "contract_version": "resolved-explicit-plan-intent.v1",
        "context": context,
        "values": values,
        "axis_evidence": evidence,
        "environment": "TEST_ONLY",
        "semantic_fingerprint": canonical_hash(
            {
                "domain": "menuto.explicit-intent.semantic.v1",
                "interpretation_version": "EXPLICIT_IDENTITY_V1",
                "values": values,
            }
        ),
    }
    return _resolution("AVAILABLE_TEST_ONLY", payload, input_hash, [])


def _resolution(outcome, payload, source_hash, diagnostics):
    result = {
        "contract_version": "plan-intent-resolution.v1",
        "interpretation_version": "EXPLICIT_IDENTITY_V1",
        "outcome": outcome,
        "payload": payload,
        "input_fingerprint": source_hash,
        "diagnostics": diagnostics,
        **_non_authority(),
    }
    return {**result, "result_fingerprint": _digest("result", result)}


def check_explicit_plan_intent_v1(source, claimed_resolution):
    """Reports consistency only. The complete primitive source is always required."""
    bounds = _Bounds()
    reconstructed = claim_hash = None
    source_error = None
    try:
        retained = bounds.retain(source)
    except _Problem as failure:
        source_error = failure
    except (ValueError, TypeError, OverflowError, UnicodeError):
        source_error = _Problem("MALFORMED_SHAPE")
    try:
        claim = bounds.retain(claimed_resolution)
    except _Problem as failure:
        if failure.outcome == "RESOURCE_EXCEEDED":
            return _report("NOT_CHECKABLE", None, None, "CHECK_RESOURCE_LIMIT")
        claim = None
    except (ValueError, TypeError, OverflowError, UnicodeError):
        claim = None
    if source is None or (
        source_error and (source_error.unsafe or source_error.outcome == "RESOURCE_EXCEEDED")
    ):
        return _report("NOT_CHECKABLE", None, None, "SOURCE_NOT_CHECKABLE")
    try:
        if source_error:
            raise source_error
        reconstructed = _reconstruct(retained, bounds)
    except _Problem as failure:
        if failure.outcome == "RESOURCE_EXCEEDED":
            return _report("NOT_CHECKABLE", None, None, "CHECK_RESOURCE_LIMIT")
        reconstructed = _resolution(
            failure.outcome, None, None, [{"code": failure.code, "path": failure.path}]
        )
    try:
        if type(claim) is not dict:
            raise ValueError("claim")
        for key in ("resolved_plan_policy_ready", "planner_ready", "activation_ready"):
            if type(claim.get(key)) is not bool:
                raise ValueError("strict flag")
        if type(claim.get("payload")) is dict:
            context = claim["payload"].get("context")
            if type(context) is not dict or type(context.get("horizon")) is not dict:
                raise ValueError("claim context")
            for key in ("request_id", "household_id", "actor_user_id", "tracked_member_id"):
                raw = context.get(key)
                if type(raw) is not str or str(UUID(raw)) != raw:
                    raise ValueError("strict claim UUID")
            for raw in (context.get("declared_at"), *context["horizon"].values()):
                if type(raw) is not str or not re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
                    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})",
                    raw,
                ):
                    raise ValueError("strict claim timestamp")
        parsed = PlanIntentResolutionV1.model_validate(claim).model_dump(mode="json")
        claim_hash = _digest("claim", parsed)
    except (ValueError, TypeError):
        return _report("INCONSISTENT", reconstructed, None, "CLAIM_INVALID")
    if parsed != reconstructed:
        return _report("INCONSISTENT", reconstructed, claim_hash, "CLAIM_MISMATCH")
    return _report("CONSISTENT", reconstructed, claim_hash, None)


def _report(decision, reconstructed, claim_hash, code):
    body = {
        "contract_version": "plan-intent-check.v1",
        "decision": decision,
        "reconstructed_outcome": reconstructed["outcome"] if reconstructed else None,
        "source_fingerprint": reconstructed["input_fingerprint"] if reconstructed else None,
        "claim_fingerprint": claim_hash,
        "diagnostics": [{"code": code, "path": "$"}] if code else [],
        **_non_authority(),
    }
    return PlanIntentCheckV1(**body, check_fingerprint=_digest("check", body))
