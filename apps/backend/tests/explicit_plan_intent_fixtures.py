"""Unambiguously TEST_ONLY explicit declarations, never production source content."""

from copy import deepcopy

from app.domain.canonical import canonical_hash


def source():
    return {
        "contract_version": "explicit-plan-intent-request.v1",
        "source": "REQUEST_EXPLICIT",
        "environment": "TEST_ONLY",
        "context": {
            "request_id": "00000000-0000-0000-0000-000000000001",
            "request_revision": 0,
            "household_id": "00000000-0000-0000-0000-000000000002",
            "actor_user_id": "00000000-0000-0000-0000-000000000003",
            "tracked_member_id": "00000000-0000-0000-0000-000000000004",
            "horizon": {"start": "2026-01-01T00:00:00Z", "end": "2026-01-08T00:00:00Z"},
            "declared_at": "2025-12-31T00:00:00Z",
        },
        "nutrition_precision": "STANDARD",
        "cost_preference": "NORMAL",
        "kitchen_effort": "NORMAL",
        "budget": {"constraint": "NONE", "amount": None},
    }


def money(kind="TARGET", amount=0, currency="VND"):
    return {"constraint": kind, "amount": {"amount_minor": amount, "currency": currency}}


def wire(result):
    return deepcopy(result.model_dump(mode="json"))


def rehash(result):
    body = deepcopy(result)
    body.pop("result_fingerprint", None)
    return {
        **body,
        "result_fingerprint": canonical_hash(
            {
                "domain": "menuto.explicit-intent.result.v1",
                "body": body,
            }
        ),
    }
