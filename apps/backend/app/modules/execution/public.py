"""Atomic plan intent orchestration only; no meal/cooking execution state machine."""

import json
from hashlib import sha256
from uuid import uuid4

from app.modules.cooking.public import store_batch_intents
from app.modules.inventory.contracts import (
    PhysicalEvidence,
    ReleaseReservationCommand,
    ReserveInventoryCommand,
)
from app.modules.inventory.public import InventoryService
from app.modules.planning import contracts as c
from app.modules.planning.public import PlanStore
from app.modules.shopping.public import store_shopping_intents


def fingerprint(command):
    payload = command.model_dump()
    if payload.get("graph", {}).get("contract_version") == "plan-intent.v3":
        payload["graph"] = command.graph.content()
    if payload.get("graph", {}).get("contract_version") == "plan-intent.v1":
        payload["graph"].pop("shopping_contributions", None)
    return sha256(
        json.dumps(
            c.canonical_value(payload),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def target_content(graph, intent):
    if intent.batch_node_id:
        return next(b for b in graph.batches if b.node_id == intent.batch_node_id).model_dump()
    meal = next(m for m in graph.meals if m.node_id == intent.meal_node_id)
    allocations = [a for a in graph.allocations if a.meal_node_id == meal.node_id]
    ids = {a.batch_node_id for a in allocations}
    return dict(
        meal=meal.model_dump(),
        allocations=sorted([a.model_dump() for a in allocations], key=lambda x: str(x["node_id"])),
        batches=sorted(
            [b.model_dump() for b in graph.batches if b.node_id in ids],
            key=lambda x: str(x["node_id"]),
        ),
    )


class PlanRevisionService:
    """Caller owns commit/rollback. Nested savepoints keep caught failures atomic.

    Production cannot mint PRECOMMIT authorizations. A full validator/issuer and complete
    subject/source-frontier guard are required before enabling operational activation.
    """

    def __init__(self, session):
        self.session = session
        self.store = PlanStore(session)

    def create_workspace(self, command: c.CreatePlanWorkspaceCommand):
        command = c.CreatePlanWorkspaceCommand.model_validate(command.model_dump())
        return self.store.create_workspace(
            plan_id=command.plan_id,
            household_id=command.household_id,
            tracked_member_id=command.tracked_member_id,
            horizon=command.horizon,
            actor_user_id=command.actor_user_id,
        )

    def current_plan(self, household_id, plan_id):
        self.store.lock(household_id)
        w = self.store.workspace(household_id, plan_id)
        if w.active_revision_no is None:
            raise ValueError("Plan is not activated; use immutable draft proposals")
        revision = self.store.revision(household_id, plan_id, w.active_revision_no)
        snapshot_type = (
            c.BoundActivePlanSnapshot
            if isinstance(revision, c.BoundPlanRevisionSnapshot)
            else c.ActivePlanSnapshot
        )
        return snapshot_type(workspace=w, revision=revision)

    def horizon_handoff(self, household_id, plan_id, cutoff):
        current = self.current_plan(household_id, plan_id)
        if isinstance(current, c.BoundActivePlanSnapshot):
            raise ValueError("V3 horizon projection is deferred; use exact culinary capture")
        return c.HorizonCommitmentsDraft(
            revision=current.revision,
            inventory_frontier=self.store.inventory_frontier(household_id),
            boundary_version=current.workspace.boundary_version,
            cutoff=cutoff,
        )

    def propose(self, command: c.ProposePlanCommand):
        command_type = (
            c.ProposeBoundPlanCommand
            if isinstance(command, c.ProposeBoundPlanCommand)
            else c.ProposePlanCommand
        )
        command = command_type.model_validate(command.model_dump())
        self.store.lock(command.graph.household_id)
        existing = self.store.existing(
            "proposal",
            plan_id=command.graph.plan_id,
            source_system=command.source_system,
            idempotency_key=command.idempotency_key,
            fingerprint=fingerprint(command),
        )
        if existing:
            return self.store.proposal(
                command.graph.household_id, command.graph.plan_id, existing["id"]
            )
        with self.session.begin_nested():
            self.store.begin_proposal(command, fingerprint(command))
            context = dict(
                proposal_id=command.proposal_id,
                household_id=command.graph.household_id,
                plan_id=command.graph.plan_id,
            )
            store_batch_intents(
                self.session,
                **context,
                batches=command.graph.batches,
                allocations=command.graph.allocations,
            )
            self.store.store_reservation_intents(command)
            store_shopping_intents(
                self.session,
                **context,
                requirements=command.graph.shopping,
                contributions=command.graph.shopping_contributions,
            )
            self.store.store_bindings(command.graph)
            self.store.seal(command.proposal_id)
            result = self.store.proposal(
                command.graph.household_id, command.graph.plan_id, command.proposal_id
            )
            if result.graph_hash != command.graph.fingerprint():
                raise ValueError("Persisted graph differs from exact authored command")
            return result

    def publish(self, command: c.PublishPlanRevisionCommand):
        command = c.PublishPlanRevisionCommand.model_validate(command.model_dump())
        self.store.lock(command.household_id)
        existing = self.store.existing(
            "revision",
            plan_id=command.plan_id,
            source_system=command.source_system,
            idempotency_key=command.idempotency_key,
            fingerprint=fingerprint(command),
        )
        if existing:
            return self.store.revision(
                command.household_id, command.plan_id, existing["revision_no"]
            )
        with self.session.begin_nested():
            w = self.store.workspace(command.household_id, command.plan_id)
            p = self.store.proposal(command.household_id, command.plan_id, command.proposal_id)
            old = (
                self.store.revision(command.household_id, command.plan_id, w.active_revision_no)
                if w.active_revision_no is not None
                else None
            )
            links = self.store.reservation_links(
                command.household_id, command.plan_id, w.active_revision_no
            )
            # This header insertion checks the real stored authorization BEFORE physical effects.
            revision_no = self.store.publish_header(command, fingerprint(command))
            inv = InventoryService(self.session)
            snapshot = inv.snapshot(command.household_id)
            releases = {r.reservation_id for r in snapshot.releases}
            positions = {p.lot_id: p for p in snapshot.positions}
            old_intents = {r.node_id: r for r in old.proposal.graph.reservations} if old else {}
            new_intents = {r.node_id: r for r in p.graph.reservations}
            retain = {}
            for link in links:
                key = link["intent_node_id"]
                prior = old_intents[key]
                new = new_intents.get(key)
                if (
                    new is not None
                    and new == prior
                    and link["reservation_id"] not in releases
                    and positions[new.lot_id].lifecycle_state == "ACTIVE"
                    and target_content(old.proposal.graph, prior) == target_content(p.graph, new)
                ):
                    retain[key] = link["reservation_id"]
                elif link["reservation_id"] not in releases:
                    evidence = PhysicalEvidence(
                        kind="USER",
                        source_system="plan.revision",
                        external_record_id=f"{command.plan_id}.{revision_no}.release.{key}",
                        source_version="1",
                        confirmed_by_user_id=command.actor_user_id,
                    )
                    inv.release(
                        ReleaseReservationCommand(
                            household_id=command.household_id,
                            lot_id=link["lot_id"],
                            reservation_id=link["reservation_id"],
                            occurred_at=self.store.clock(),
                            idempotency_key=f"r{command.plan_id}.{revision_no}.{key}",
                            reason="Explicit accepted plan revision releases allocation intent",
                            evidence=evidence,
                        )
                    )
            for r in p.graph.reservations:
                identity = retain.get(r.node_id)
                if identity is None:
                    identity = uuid4()
                    evidence = PhysicalEvidence(
                        kind="USER",
                        source_system="plan.revision",
                        external_record_id=f"{command.plan_id}.{revision_no}.reserve.{r.node_id}",
                        source_version="1",
                        confirmed_by_user_id=command.actor_user_id,
                    )
                    inv.reserve(
                        ReserveInventoryCommand(
                            household_id=command.household_id,
                            lot_id=r.lot_id,
                            quantity=r.quantity,
                            reservation_id=identity,
                            purpose=f"Plan {command.plan_id} revision {revision_no}",
                            occurred_at=self.store.clock(),
                            idempotency_key=f"s{command.plan_id}.{revision_no}.{r.node_id}",
                            reason="Explicit accepted plan revision allocation intent",
                            evidence=evidence,
                        )
                    )
                self.store.bind_reservation(command, revision_no, r, identity)
            self.store.complete()
            return self.store.revision(command.household_id, command.plan_id, revision_no)
