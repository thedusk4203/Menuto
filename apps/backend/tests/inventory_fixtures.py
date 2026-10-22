"""Synthetic explicit-confirmation ledger fixtures, never inferred stock."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.units import Quantity
from app.modules.inventory import contracts as c

NOW = datetime.now(UTC) - timedelta(days=2)


def evidence(actor=None, **kw):
    return c.PhysicalEvidence(
        **(
            dict(
                kind="USER",
                source_system="manual",
                external_record_id=str(uuid4()),
                source_version="1",
                confirmed_by_user_id=actor or uuid4(),
            )
            | kw
        )
    )


def acquire(household=None, actor=None, ingredient=None, **kw):
    return c.AcquireInventoryCommand(
        **(
            dict(
                household_id=household or uuid4(),
                lot_id=uuid4(),
                ingredient_id=ingredient or uuid4(),
                asset_type="RAW_INGREDIENT",
                quantity=Quantity(amount="500", basis="EP_RAW_G"),
                occurred_at=NOW,
                idempotency_key=str(uuid4()),
                evidence=evidence(actor),
                reason="Explicit kitchen observation",
            )
            | kw
        )
    )


def command(cls, acq, amount="100", seconds=1, **kw):
    fields = dict(
        household_id=acq.household_id,
        lot_id=acq.lot_id,
        occurred_at=NOW + timedelta(seconds=seconds),
        idempotency_key=str(uuid4()),
        evidence=evidence(acq.evidence.confirmed_by_user_id),
        reason="Explicit confirmed action",
    )
    if issubclass(cls, c.LotCommand):
        fields["quantity"] = Quantity(
            amount=amount, basis=acq.quantity.basis, item_ref=acq.quantity.item_ref
        )
    return cls(**(fields | kw))
