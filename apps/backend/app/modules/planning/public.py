"""Planning-owned persistence facade; no inventory, shopping or cooking mutation calls."""

from uuid import uuid4

from sqlalchemy import insert, select, text

from app.domain.snapshots import Horizon
from app.modules.planning import binding_models as bm
from app.modules.planning import contracts as c
from app.modules.planning import models as m


class PlanStore:
    def __init__(self, session):
        self.session = session

    def lock(self, household_id):
        self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
            {"key": "inventory.household:" + str(household_id)},
        )

    def clock(self):
        return self.session.scalar(text("SELECT clock_timestamp()"))

    def inventory_frontier(self, household_id):
        return self.session.scalar(
            text("SELECT menuto_plan_inventory_frontier(:h)"), {"h": household_id}
        )

    def workspace(self, household_id, plan_id):
        row = (
            self.session.execute(
                select(m.PlanWorkspace.__table__).where(
                    m.PlanWorkspace.id == plan_id, m.PlanWorkspace.household_id == household_id
                )
            )
            .mappings()
            .one()
        )
        return c.PlanWorkspaceDraft(
            id=row["id"],
            household_id=row["household_id"],
            tracked_member_id=row["tracked_member_id"],
            created_by_user_id=row["created_by_user_id"],
            horizon=Horizon(start=row["horizon_start"], end=row["horizon_end"]),
            state=row["state"],
            latest_proposal_no=row["latest_proposal_no"],
            active_revision_no=row["active_revision_no"],
            boundary_version=row["boundary_version"],
        )

    def create_workspace(self, *, plan_id, household_id, tracked_member_id, horizon, actor_user_id):
        self.lock(household_id)
        row = (
            self.session.execute(
                select(m.PlanWorkspace.__table__).where(m.PlanWorkspace.id == plan_id)
            )
            .mappings()
            .first()
        )
        if row is not None:
            if (
                row["household_id"],
                row["tracked_member_id"],
                row["horizon_start"],
                row["horizon_end"],
                row["created_by_user_id"],
            ) != (household_id, tracked_member_id, horizon.start, horizon.end, actor_user_id):
                raise ValueError("Stable workspace identity already has different context")
        else:
            self.session.execute(
                insert(m.PlanWorkspace.__table__).values(
                    id=plan_id,
                    household_id=household_id,
                    tracked_member_id=tracked_member_id,
                    horizon_start=horizon.start,
                    horizon_end=horizon.end,
                    created_by_user_id=actor_user_id,
                )
            )
        return self.workspace(household_id, plan_id)

    def existing(self, model_kind, *, plan_id, source_system, idempotency_key, fingerprint):
        model = m.PlanProposal if model_kind == "proposal" else m.PlanRevision
        row = (
            self.session.execute(
                select(model.__table__).where(
                    model.plan_id == plan_id,
                    model.source_system == source_system,
                    model.idempotency_key == idempotency_key,
                )
            )
            .mappings()
            .first()
        )
        if row is not None and row["command_fingerprint"] != fingerprint:
            raise ValueError("Idempotency key reused with different command content")
        return dict(row) if row is not None else None

    def begin_proposal(self, command, fingerprint):
        g = command.graph
        w = self.workspace(g.household_id, g.plan_id)
        if (w.tracked_member_id, w.horizon) != (g.tracked_member_id, g.horizon):
            raise ValueError("Graph disagrees with immutable workspace context")
        self.session.execute(
            insert(m.PlanProposal.__table__).values(
                id=command.proposal_id,
                household_id=g.household_id,
                plan_id=g.plan_id,
                proposal_no=command.expected_generation + 1,
                expected_generation=command.expected_generation,
                expected_revision=command.expected_revision,
                scope=command.scope,
                effective_from=command.effective_from,
                actor_user_id=command.actor_user_id,
                source_system=command.source_system,
                idempotency_key=command.idempotency_key,
                command_fingerprint=fingerprint,
                reason=command.reason,
                graph_version=g.contract_version,
            )
        )
        context = dict(
            proposal_id=command.proposal_id, household_id=g.household_id, plan_id=g.plan_id
        )
        for meal in g.meals:
            self.session.execute(
                insert(m.PlanMealIntent.__table__).values(
                    **context, **meal.model_dump(exclude={"participants"})
                )
            )
            for p in meal.participants:
                self.session.execute(
                    insert(m.PlanMealParticipant.__table__).values(
                        **context, meal_node_id=meal.node_id, **p.model_dump()
                    )
                )

    def store_reservation_intents(self, command):
        g = command.graph
        context = dict(
            proposal_id=command.proposal_id, household_id=g.household_id, plan_id=g.plan_id
        )
        for r in g.reservations:
            fields = r.model_dump(exclude={"quantity"})
            fields.update(
                amount=r.quantity.amount, basis=r.quantity.basis, item_ref=r.quantity.item_ref
            )
            self.session.execute(
                insert(m.PlanReservationIntent.__table__).values(**context, **fields)
            )

    def seal(self, proposal_id):
        self.session.execute(insert(m.PlanProposalSeal.__table__).values(proposal_id=proposal_id))

    def proposal(self, household_id, plan_id, proposal_id):
        row = (
            self.session.execute(
                select(m.PlanProposal.__table__).where(
                    m.PlanProposal.id == proposal_id,
                    m.PlanProposal.household_id == household_id,
                    m.PlanProposal.plan_id == plan_id,
                )
            )
            .mappings()
            .one()
        )
        raw = self.session.scalar(text("SELECT menuto_plan_graph(:p)"), {"p": proposal_id})
        graph_type = (
            c.BoundPlanIntentGraph
            if raw["contract_version"] == "plan-intent.v3"
            else c.PlanIntentGraph
        )
        graph = graph_type.model_validate(raw)
        graph_hash = self.session.scalar(
            select(m.PlanProposalSeal.graph_hash).where(
                m.PlanProposalSeal.proposal_id == proposal_id
            )
        )
        snapshot_type = (
            c.BoundPlanProposalSnapshot
            if isinstance(graph, c.BoundPlanIntentGraph)
            else c.PlanProposalSnapshot
        )
        return snapshot_type(
            id=row["id"],
            proposal_no=row["proposal_no"],
            graph=graph,
            graph_hash=graph_hash,
            expected_revision=row["expected_revision"],
            scope=row["scope"],
            effective_from=row["effective_from"],
            actor_user_id=row["actor_user_id"],
            source_system=row["source_system"],
            idempotency_key=row["idempotency_key"],
            reason=row["reason"],
            created_at=row["created_at"],
        )

    def revision(self, household_id, plan_id, revision_no):
        row = (
            self.session.execute(
                select(m.PlanRevision.__table__).where(
                    m.PlanRevision.household_id == household_id,
                    m.PlanRevision.plan_id == plan_id,
                    m.PlanRevision.revision_no == revision_no,
                )
            )
            .mappings()
            .one()
        )
        parent_hash = None
        if row["parent_revision_no"] is not None:
            parent_proposal = self.session.scalar(
                select(m.PlanRevision.proposal_id).where(
                    m.PlanRevision.plan_id == plan_id,
                    m.PlanRevision.revision_no == row["parent_revision_no"],
                )
            )
            parent_hash = self.session.scalar(
                select(m.PlanProposalSeal.graph_hash).where(
                    m.PlanProposalSeal.proposal_id == parent_proposal
                )
            )
        proposal = self.proposal(household_id, plan_id, row["proposal_id"])
        snapshot_type = (
            c.BoundPlanRevisionSnapshot
            if isinstance(proposal, c.BoundPlanProposalSnapshot)
            else c.PlanRevisionSnapshot
        )
        return snapshot_type(
            household_id=household_id,
            plan_id=plan_id,
            revision_no=revision_no,
            parent_revision_no=row["parent_revision_no"],
            parent_graph_hash=parent_hash,
            reason_kind=("INITIAL_ACTIVATED_BASELINE" if revision_no == 0 else "PLAN_REVISION"),
            proposal=proposal,
            authorization_id=row["authorization_id"],
            created_at=row["created_at"],
        )

    def reservation_links(self, household_id, plan_id, revision_no):
        return tuple(
            dict(r)
            for r in self.session.execute(
                select(m.PlanRevisionReservation.__table__).where(
                    m.PlanRevisionReservation.household_id == household_id,
                    m.PlanRevisionReservation.plan_id == plan_id,
                    m.PlanRevisionReservation.revision_no == revision_no,
                )
            ).mappings()
        )

    def publish_header(self, command, fingerprint):
        self.session.execute(
            insert(m.PlanRevision.__table__).values(
                id=uuid4(),
                household_id=command.household_id,
                plan_id=command.plan_id,
                proposal_id=command.proposal_id,
                authorization_id=command.authorization_id,
                actor_user_id=command.actor_user_id,
                source_system=command.source_system,
                idempotency_key=command.idempotency_key,
                command_fingerprint=fingerprint,
                revision_no=0,
            )
        )
        return self.workspace(command.household_id, command.plan_id).active_revision_no

    def bind_reservation(self, command, revision_no, intent, reservation_id):
        self.session.execute(
            insert(m.PlanRevisionReservation.__table__).values(
                plan_id=command.plan_id,
                household_id=command.household_id,
                revision_no=revision_no,
                proposal_id=command.proposal_id,
                intent_node_id=intent.node_id,
                lot_id=intent.lot_id,
                reservation_id=reservation_id,
            )
        )

    def complete(self):
        self.session.execute(text("SET CONSTRAINTS plan_revision_complete IMMEDIATE"))
        self.session.execute(text("SET CONSTRAINTS plan_revision_complete DEFERRED"))

    def link_materialization(
        self,
        *,
        household_id,
        plan_id,
        source_revision_no,
        lot_id,
        movement_id,
        actor_user_id,
        meal_node_id=None,
        batch_node_id=None,
        shopping_node_id=None,
    ):
        self.lock(household_id)
        source = self.revision(household_id, plan_id, source_revision_no)
        self.session.execute(
            insert(m.PlanMaterializationLink.__table__).values(
                id=uuid4(),
                household_id=household_id,
                plan_id=plan_id,
                source_revision_no=source_revision_no,
                proposal_id=source.proposal.id,
                lot_id=lot_id,
                movement_id=movement_id,
                actor_user_id=actor_user_id,
                meal_node_id=meal_node_id,
                batch_node_id=batch_node_id,
                shopping_node_id=shopping_node_id,
            )
        )

    def store_bindings(self, graph):
        for binding in getattr(graph, "culinary_bindings", ()):
            data = binding.model_dump(exclude={"requirements", "provenance"})
            data.update(binding.provenance.model_dump(exclude={"kind"}))
            data["source_kind"] = binding.provenance.kind
            if data["source_uri"] is not None:
                data["source_uri"] = str(data["source_uri"])
            self.session.execute(insert(bm.PlannedCulinaryBinding.__table__).values(**data))
            for row in binding.requirements:
                fields = row.model_dump(exclude={"quantity"})
                fields.update(
                    amount=row.quantity.amount,
                    basis=row.quantity.basis,
                    item_ref=row.quantity.item_ref,
                )
                self.session.execute(
                    insert(bm.CulinaryRequirementBinding.__table__).values(
                        proposal_id=binding.proposal_id,
                        batch_node_id=binding.batch_node_id,
                        recipe_version_id=binding.recipe_version_id,
                        **fields,
                    )
                )
