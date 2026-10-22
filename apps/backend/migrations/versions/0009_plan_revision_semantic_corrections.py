"""Scoped demand contributions and complete advice cut line; frozen SQL only."""
# ruff: noqa: E501 -- frozen SQL/DDL
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

UPGRADE_SQL = r'''
ALTER TABLE plan_proposals ADD COLUMN graph_version varchar(30) NOT NULL DEFAULT 'plan-intent.v1';
ALTER TABLE plan_proposals ADD CONSTRAINT ck_plan_proposals_graph_version CHECK (graph_version IN ('plan-intent.v1','plan-intent.v2'));

CREATE TABLE shopping_demand_contributions (
	requirement_node_id UUID NOT NULL,
	meal_node_id UUID,
	batch_node_id UUID,
	amount NUMERIC NOT NULL,
	basis VARCHAR(20) NOT NULL,
	item_ref VARCHAR(100),
	status VARCHAR(20) NOT NULL,
	proposal_id UUID NOT NULL,
	node_id UUID NOT NULL,
	household_id UUID NOT NULL,
	plan_id UUID NOT NULL,
	CONSTRAINT pk_shopping_demand_contributions PRIMARY KEY (proposal_id, node_id),
	CONSTRAINT fk_shopping_demand_contributions_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT,
	CONSTRAINT fk_shopping_demand_contributions_proposal_id_shopping_r_2b84 FOREIGN KEY(proposal_id, requirement_node_id) REFERENCES shopping_requirement_intents (proposal_id, node_id) ON DELETE RESTRICT,
	CONSTRAINT fk_shopping_demand_contributions_proposal_id_plan_meal_intents FOREIGN KEY(proposal_id, meal_node_id) REFERENCES plan_meal_intents (proposal_id, node_id) ON DELETE RESTRICT,
	CONSTRAINT fk_shopping_demand_contributions_proposal_id_planned_co_409c FOREIGN KEY(proposal_id, batch_node_id) REFERENCES planned_cooking_batches (proposal_id, node_id) ON DELETE RESTRICT,
	CONSTRAINT ck_shopping_demand_contributions_target CHECK ((meal_node_id IS NULL) <> (batch_node_id IS NULL)),
	CONSTRAINT ck_shopping_demand_contributions_status CHECK (status IN ('PLANNED','RETIRED')),
	CONSTRAINT ck_shopping_demand_contributions_amount CHECK (amount>0 AND amount<1000000000000 AND amount=trunc(amount,6)),
	CONSTRAINT ck_shopping_demand_contributions_basis CHECK ((basis='COUNT' AND item_ref IS NOT NULL AND item_ref ~ '^[A-Za-z0-9_.:-]+$') OR (basis IN ('AP_G','EP_RAW_G','COOKED_G') AND item_ref IS NULL))
)

;
CREATE OR REPLACE FUNCTION menuto_plan_graph(p_id uuid) RETURNS jsonb LANGUAGE sql STABLE AS $$
 SELECT jsonb_build_object('contract_version',p.graph_version,'household_id',w.household_id,
 'plan_id',w.id,'tracked_member_id',w.tracked_member_id,'horizon',jsonb_build_object(
 'start',to_char(w.horizon_start AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
 'end',to_char(w.horizon_end AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')),
'meals',coalesce((SELECT jsonb_agg(jsonb_build_object('scheduled_at',to_char(x.scheduled_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'meal_kind',x.meal_kind,'status',x.status,'node_id',x.node_id,'participants',coalesce((SELECT jsonb_agg(jsonb_build_object('member_id',q.member_id,'portion_factor',trim_scale(q.portion_factor)::text,'nutrition_role',q.nutrition_role) ORDER BY q.member_id) FROM plan_meal_participants q WHERE q.proposal_id=x.proposal_id AND q.meal_node_id=x.node_id),'[]'::jsonb)) ORDER BY x.node_id) FROM plan_meal_intents x WHERE x.proposal_id=p_id),'[]'::jsonb),
'batches',coalesce((SELECT jsonb_agg(jsonb_build_object('recipe_version_id',x.recipe_version_id,'tier_id',x.tier_id,'planned_servings',trim_scale(x.planned_servings)::text,'planned_at',to_char(x.planned_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'status',x.status,'node_id',x.node_id) ORDER BY x.node_id) FROM planned_cooking_batches x WHERE x.proposal_id=p_id),'[]'::jsonb),
'allocations',coalesce((SELECT jsonb_agg(jsonb_build_object('batch_node_id',x.batch_node_id,'meal_node_id',x.meal_node_id,'servings',trim_scale(x.servings)::text,'status',x.status,'node_id',x.node_id) ORDER BY x.node_id) FROM planned_batch_allocations x WHERE x.proposal_id=p_id),'[]'::jsonb),
'shopping',coalesce((SELECT jsonb_agg(jsonb_build_object('ingredient_id',x.ingredient_id,'need_by',to_char(x.need_by AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'status',x.status,'node_id',x.node_id,'quantity',jsonb_build_object('amount',trim_scale(x.amount)::text,'basis',x.basis,'item_ref',x.item_ref)) ORDER BY x.node_id) FROM shopping_requirement_intents x WHERE x.proposal_id=p_id),'[]'::jsonb),
'reservations',coalesce((SELECT jsonb_agg(jsonb_build_object('lot_id',x.lot_id,'meal_node_id',x.meal_node_id,'batch_node_id',x.batch_node_id,'node_id',x.node_id,'quantity',jsonb_build_object('amount',trim_scale(x.amount)::text,'basis',x.basis,'item_ref',x.item_ref)) ORDER BY x.node_id) FROM plan_reservation_intents x WHERE x.proposal_id=p_id),'[]'::jsonb)
) || CASE WHEN p.graph_version='plan-intent.v2' THEN jsonb_build_object('shopping_contributions',coalesce((SELECT jsonb_agg(jsonb_build_object('node_id',c.node_id,'requirement_node_id',c.requirement_node_id,'meal_node_id',c.meal_node_id,'batch_node_id',c.batch_node_id,'quantity',jsonb_build_object('amount',trim_scale(c.amount)::text,'basis',c.basis,'item_ref',c.item_ref),'status',c.status) ORDER BY c.node_id) FROM shopping_demand_contributions c WHERE c.proposal_id=p_id),'[]'::jsonb)) ELSE '{}'::jsonb END FROM plan_proposals p JOIN plan_workspaces w ON w.id=p.plan_id WHERE p.id=p_id
$$;
CREATE FUNCTION menuto_plan_delta_0009(a jsonb,b jsonb,k text)
RETURNS TABLE(prev jsonb,curr jsonb) LANGUAGE sql IMMUTABLE AS $$
 SELECT x.v,y.v FROM jsonb_array_elements(coalesce(a->k,'[]'::jsonb)) x(v)
 FULL JOIN jsonb_array_elements(coalesce(b->k,'[]'::jsonb)) y(v) ON x.v->>'node_id'=y.v->>'node_id'
 WHERE x.v IS DISTINCT FROM y.v
$$;
CREATE FUNCTION menuto_plan_target_meals_0009(a uuid,b uuid,t jsonb) RETURNS SETOF uuid
LANGUAGE sql STABLE AS $$
 SELECT (t->>'meal_node_id')::uuid WHERE t->>'meal_node_id' IS NOT NULL
 UNION SELECT meal_node_id FROM planned_batch_allocations WHERE proposal_id IN(a,b)
 AND batch_node_id=(t->>'batch_node_id')::uuid AND status='PLANNED'
$$;
CREATE FUNCTION menuto_plan_require_local_0009(a uuid,b uuid,t jsonb,m uuid) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
 IF t IS NOT NULL AND (NOT EXISTS(SELECT 1 FROM menuto_plan_target_meals_0009(a,b,t)) OR EXISTS(
 SELECT 1 FROM menuto_plan_target_meals_0009(a,b,t) x(id) WHERE id<>m)) THEN
 RAISE EXCEPTION 'SINGLE_MEAL scope escapes target dependency closure' USING ERRCODE='23514'; END IF;
END $$;
CREATE FUNCTION menuto_plan_contributions_0009(p uuid) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM shopping_demand_contributions c JOIN plan_proposals p0 ON p0.id=c.proposal_id
 JOIN shopping_requirement_intents s ON s.proposal_id=c.proposal_id AND s.node_id=c.requirement_node_id
 LEFT JOIN plan_meal_intents m ON m.proposal_id=c.proposal_id AND m.node_id=c.meal_node_id
 LEFT JOIN planned_cooking_batches b ON b.proposal_id=c.proposal_id AND b.node_id=c.batch_node_id
 WHERE c.proposal_id=p AND (p0.graph_version<>'plan-intent.v2' OR c.basis<>s.basis
 OR c.item_ref IS DISTINCT FROM s.item_ref OR (c.status='PLANNED' AND
 (s.status<>'PLANNED' OR coalesce(m.status,b.status)<>'PLANNED')))) OR EXISTS(
 SELECT 1 FROM shopping_requirement_intents s WHERE s.proposal_id=p AND EXISTS(
 SELECT 1 FROM shopping_demand_contributions c WHERE c.proposal_id=p AND c.requirement_node_id=s.node_id)
 AND (CASE WHEN s.status='PLANNED' THEN s.amount ELSE 0 END)<>(
 SELECT coalesce(sum(c.amount) FILTER (WHERE c.status='PLANNED'),0) FROM shopping_demand_contributions c
 WHERE c.proposal_id=p AND c.requirement_node_id=s.node_id)) THEN
 RAISE EXCEPTION 'invalid contribution ownership/basis/quantity conservation' USING ERRCODE='23514';END IF;
END $$;
CREATE FUNCTION menuto_plan_scope_0009(a uuid,b uuid) RETURNS void LANGUAGE plpgsql AS $$
DECLARE o jsonb:=menuto_plan_graph(a);g jsonb:=menuto_plan_graph(b);s text;ids uuid[];m uuid;r record;t jsonb;
BEGIN
 SELECT scope INTO s FROM plan_proposals WHERE id=b;
 IF EXISTS(SELECT 1 FROM shopping_demand_contributions x JOIN shopping_demand_contributions y
 ON y.proposal_id=b AND y.node_id=x.node_id WHERE x.proposal_id=a
 AND x.requirement_node_id<>y.requirement_node_id) THEN
 RAISE EXCEPTION 'contribution parent identity cannot be retargeted' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT node_id FROM shopping_demand_contributions WHERE proposal_id=a EXCEPT
 SELECT node_id FROM shopping_demand_contributions WHERE proposal_id=b) THEN
 RAISE EXCEPTION 'retire historical contribution, do not erase identity' USING ERRCODE='23514';END IF;
 WITH changed AS (
 SELECT (coalesce(prev,curr)->>'node_id')::uuid id FROM menuto_plan_delta_0009(o,g,'meals')
 UNION SELECT (v->>'meal_node_id')::uuid FROM menuto_plan_delta_0009(o,g,'allocations') d
 CROSS JOIN LATERAL (VALUES(d.prev),(d.curr)) z(v) WHERE v IS NOT NULL
 UNION SELECT id FROM menuto_plan_delta_0009(o,g,'batches') d
 CROSS JOIN LATERAL menuto_plan_target_meals_0009(a,b,jsonb_build_object('batch_node_id',coalesce(prev,curr)->>'node_id')) x(id))
 SELECT array_agg(DISTINCT id) INTO ids FROM changed;
 IF (s='SINGLE_MEAL' AND coalesce(cardinality(ids),0)<>1) OR
 (s='MULTI_MEAL' AND coalesce(cardinality(ids),0)<1) OR (s='PROCUREMENT_ONLY' AND
 (o->'meals'<>g->'meals' OR o->'batches'<>g->'batches' OR o->'allocations'<>g->'allocations')) THEN
 RAISE EXCEPTION 'revision scope does not cover dependency closure' USING ERRCODE='23514';END IF;
 IF s<>'SINGLE_MEAL' THEN RETURN;END IF;m:=ids[1];
 FOR r IN SELECT * FROM menuto_plan_delta_0009(o,g,'batches') LOOP
 PERFORM menuto_plan_require_local_0009(a,b,jsonb_build_object('batch_node_id',coalesce(r.prev,r.curr)->>'node_id'),m);
 END LOOP;
 FOR r IN SELECT * FROM menuto_plan_delta_0009(o,g,'reservations') UNION ALL
 SELECT * FROM menuto_plan_delta_0009(o,g,'shopping_contributions') LOOP
 PERFORM menuto_plan_require_local_0009(a,b,r.prev,m);
 PERFORM menuto_plan_require_local_0009(a,b,r.curr,m);
 END LOOP;
 FOR r IN SELECT * FROM menuto_plan_delta_0009(o,g,'shopping')
 UNION SELECT x.v,y.v FROM jsonb_array_elements(o->'shopping') x(v)
 FULL JOIN jsonb_array_elements(g->'shopping') y(v) ON x.v->>'node_id'=y.v->>'node_id'
 WHERE coalesce(x.v,y.v)->>'node_id' IN (
 SELECT v->>'requirement_node_id' FROM menuto_plan_delta_0009(o,g,'shopping_contributions') d
 CROSS JOIN LATERAL (VALUES(d.prev),(d.curr)) z(v) WHERE v IS NOT NULL) LOOP
 -- Missing ownership cannot be guessed. Both source and replacement need evidence.
 IF (r.prev IS NOT NULL AND NOT EXISTS(SELECT 1 FROM shopping_demand_contributions
 WHERE proposal_id=a AND requirement_node_id=(r.prev->>'node_id')::uuid)) OR
 (r.curr IS NOT NULL AND NOT EXISTS(SELECT 1 FROM shopping_demand_contributions
 WHERE proposal_id=b AND requirement_node_id=(r.curr->>'node_id')::uuid)) THEN
 RAISE EXCEPTION 'SINGLE_MEAL scope requires attributed shopping contributions' USING ERRCODE='23514';END IF;
 -- Amount-only delta can retain other meals' exact shares. Identity/time/status affect all.
 IF (r.prev-ARRAY['quantity']) IS DISTINCT FROM (r.curr-ARRAY['quantity']) OR
 r.prev->'quantity'->'basis' IS DISTINCT FROM r.curr->'quantity'->'basis' OR
 r.prev->'quantity'->'item_ref' IS DISTINCT FROM r.curr->'quantity'->'item_ref' THEN
 FOR t IN SELECT to_jsonb(c) FROM shopping_demand_contributions c
 WHERE (proposal_id=a AND requirement_node_id=(r.prev->>'node_id')::uuid)
 OR (proposal_id=b AND requirement_node_id=(r.curr->>'node_id')::uuid) LOOP
 PERFORM menuto_plan_require_local_0009(a,b,t,m);END LOOP;
 END IF;
 END LOOP;
END $$;
CREATE FUNCTION menuto_plan_anchor_0009(p uuid,t jsonb) RETURNS timestamptz LANGUAGE sql STABLE AS $$
 SELECT coalesce((SELECT scheduled_at FROM plan_meal_intents WHERE proposal_id=p AND node_id=(t->>'meal_node_id')::uuid),
 (SELECT planned_at FROM planned_cooking_batches WHERE proposal_id=p AND node_id=(t->>'batch_node_id')::uuid))
$$;
CREATE FUNCTION menuto_plan_cutline_0009(a uuid,b uuid) RETURNS void LANGUAGE plpgsql AS $$
DECLARE o jsonb:=menuto_plan_graph(a);g jsonb:=menuto_plan_graph(b);cut timestamptz;family text;anchor text;r record;
BEGIN
 SELECT effective_from INTO cut FROM plan_proposals WHERE id=b;
 FOR family,anchor IN VALUES ('meals','scheduled_at'),('batches','planned_at'),('shopping','need_by') LOOP
 FOR r IN SELECT * FROM menuto_plan_delta_0009(o,g,family) LOOP
 IF (r.prev->>anchor)::timestamptz<cut OR (r.curr->>anchor)::timestamptz<cut THEN
 RAISE EXCEPTION 'past advice frozen by own temporal anchor' USING ERRCODE='23514';END IF;
 END LOOP;END LOOP;
 FOR family IN VALUES ('reservations'),('shopping_contributions') LOOP
 FOR r IN SELECT * FROM menuto_plan_delta_0009(o,g,family) LOOP
 IF menuto_plan_anchor_0009(a,r.prev)<cut OR menuto_plan_anchor_0009(b,r.curr)<cut OR
 (family='shopping_contributions' AND (
 EXISTS(SELECT 1 FROM shopping_requirement_intents WHERE proposal_id=a AND node_id=(r.prev->>'requirement_node_id')::uuid AND need_by<cut) OR
 EXISTS(SELECT 1 FROM shopping_requirement_intents WHERE proposal_id=b AND node_id=(r.curr->>'requirement_node_id')::uuid AND need_by<cut))) THEN
 RAISE EXCEPTION 'past advice dependency frozen by temporal anchor' USING ERRCODE='23514';END IF;
 END LOOP;END LOOP;
END $$;

CREATE OR REPLACE FUNCTION menuto_plan_check(p_id uuid) RETURNS void LANGUAGE plpgsql AS $$
DECLARE p plan_proposals%ROWTYPE;w plan_workspaces%ROWTYPE;old_id uuid;g jsonb;o jsonb;

BEGIN
 SELECT * INTO p FROM plan_proposals WHERE id=p_id;
 SELECT * INTO w FROM plan_workspaces WHERE id=p.plan_id AND household_id=p.household_id;
 IF p.expected_revision IS DISTINCT FROM w.active_revision_no THEN
 RAISE EXCEPTION 'STALE_ACTIVE_REVISION' USING ERRCODE='23514'; END IF;
 IF p.effective_from>w.horizon_end THEN RAISE EXCEPTION 'cut line beyond horizon' USING ERRCODE='23514';END IF;
 IF NOT EXISTS(SELECT 1 FROM plan_meal_intents WHERE proposal_id=p_id) OR EXISTS(
 SELECT 1 FROM plan_meal_intents m WHERE m.proposal_id=p_id AND
 (m.scheduled_at<w.horizon_start OR m.scheduled_at>=w.horizon_end OR NOT EXISTS(
 SELECT 1 FROM plan_meal_participants x WHERE x.proposal_id=p_id AND x.meal_node_id=m.node_id))) OR EXISTS(
 SELECT 1 FROM plan_meal_participants x WHERE x.proposal_id=p_id AND
 ((x.member_id=w.tracked_member_id)<>(x.nutrition_role='TRACKED'))) THEN
 RAISE EXCEPTION 'invalid meal horizon or participants' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM planned_cooking_batches b JOIN recipe_portion_tiers t ON t.id=b.tier_id
 WHERE b.proposal_id=p_id AND (b.planned_servings<>t.servings OR b.planned_at>=w.horizon_end)) THEN
 RAISE EXCEPTION 'batch must use exact authored tier servings/context' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM planned_batch_allocations a
 JOIN planned_cooking_batches b ON b.proposal_id=a.proposal_id AND b.node_id=a.batch_node_id
 JOIN plan_meal_intents m ON m.proposal_id=a.proposal_id AND m.node_id=a.meal_node_id
 WHERE a.proposal_id=p_id AND a.status='PLANNED' AND
 (b.status<>'PLANNED' OR m.status<>'PLANNED' OR m.meal_kind<>'HOME' OR b.planned_at>m.scheduled_at)) OR EXISTS(
 SELECT 1 FROM planned_cooking_batches b WHERE b.proposal_id=p_id AND b.planned_servings<(
 SELECT coalesce(sum(servings),0) FROM planned_batch_allocations a WHERE a.proposal_id=p_id
 AND a.batch_node_id=b.node_id AND a.status='PLANNED')) OR EXISTS(
 SELECT 1 FROM plan_meal_intents m WHERE m.proposal_id=p_id AND m.status='PLANNED' AND m.meal_kind='HOME'
 AND NOT EXISTS(SELECT 1 FROM planned_batch_allocations a WHERE a.proposal_id=p_id
 AND a.meal_node_id=m.node_id AND a.status='PLANNED')) THEN
 RAISE EXCEPTION 'invalid batch allocation/production chronology' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM shopping_requirement_intents s WHERE s.proposal_id=p_id AND s.need_by>w.horizon_end)
 OR EXISTS(SELECT 1 FROM plan_reservation_intents r JOIN inventory_lots l ON l.id=r.lot_id
 LEFT JOIN plan_meal_intents m ON m.proposal_id=r.proposal_id AND m.node_id=r.meal_node_id
 LEFT JOIN planned_cooking_batches b ON b.proposal_id=r.proposal_id AND b.node_id=r.batch_node_id
 WHERE r.proposal_id=p_id AND (r.basis<>l.basis OR r.item_ref IS DISTINCT FROM l.item_ref
 OR coalesce(m.status,b.status)<>'PLANNED')) THEN
 RAISE EXCEPTION 'invalid shopping/reservation material context' USING ERRCODE='23514';END IF;
 PERFORM menuto_plan_contributions_0009(p_id);
 IF w.active_revision_no IS NOT NULL THEN
 SELECT proposal_id INTO old_id FROM plan_revisions WHERE plan_id=w.id AND revision_no=w.active_revision_no;
 IF p.effective_from < (SELECT effective_from FROM plan_proposals WHERE id=old_id) THEN
 RAISE EXCEPTION 'revision cut line regressed' USING ERRCODE='23514';END IF;
 ELSE
 SELECT id INTO old_id FROM plan_proposals WHERE plan_id=w.id AND proposal_no=p.expected_generation;
 END IF;
 g:=menuto_plan_graph(p_id);o:=menuto_plan_graph(old_id);
 IF old_id IS NOT NULL THEN
 -- Stable historical nodes remain in full snapshots; retirement is explicit content.
 IF EXISTS(SELECT 1 FROM (
 SELECT node_id FROM plan_meal_intents WHERE proposal_id=old_id EXCEPT
 SELECT node_id FROM plan_meal_intents WHERE proposal_id=p_id) x)
 OR EXISTS(SELECT 1 FROM (
 SELECT node_id FROM planned_cooking_batches WHERE proposal_id=old_id EXCEPT
 SELECT node_id FROM planned_cooking_batches WHERE proposal_id=p_id) x)
 OR EXISTS(SELECT 1 FROM (
 SELECT node_id FROM planned_batch_allocations WHERE proposal_id=old_id EXCEPT
 SELECT node_id FROM planned_batch_allocations WHERE proposal_id=p_id) x)
 OR EXISTS(SELECT 1 FROM (
 SELECT node_id FROM shopping_requirement_intents WHERE proposal_id=old_id EXCEPT
 SELECT node_id FROM shopping_requirement_intents WHERE proposal_id=p_id) x) THEN
 RAISE EXCEPTION 'retire historical intent, do not erase identity' USING ERRCODE='23514';END IF;
 PERFORM menuto_plan_scope_0009(old_id,p_id);
 IF w.active_revision_no IS NOT NULL AND (EXISTS(
 SELECT 1 FROM jsonb_array_elements(o->'meals') x(v) WHERE (v->>'scheduled_at')::timestamptz<p.effective_from
 AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(g->'meals') y(n) WHERE n=v)) OR EXISTS(
 SELECT 1 FROM planned_batch_allocations a JOIN plan_meal_intents m
 ON m.proposal_id=a.proposal_id AND m.node_id=a.meal_node_id
 WHERE a.proposal_id=old_id AND m.scheduled_at<p.effective_from AND NOT EXISTS(
 SELECT 1 FROM planned_batch_allocations n WHERE n.proposal_id=p_id AND n.node_id=a.node_id
 AND (to_jsonb(n)-ARRAY['proposal_id'])=(to_jsonb(a)-ARRAY['proposal_id']))) OR EXISTS(
 SELECT 1 FROM planned_cooking_batches b WHERE b.proposal_id=old_id AND EXISTS(
 SELECT 1 FROM planned_batch_allocations a JOIN plan_meal_intents m ON m.proposal_id=a.proposal_id AND m.node_id=a.meal_node_id
 WHERE a.proposal_id=old_id AND a.batch_node_id=b.node_id AND m.scheduled_at<p.effective_from)
 AND NOT EXISTS(SELECT 1 FROM planned_cooking_batches n WHERE n.proposal_id=p_id AND n.node_id=b.node_id
 AND (to_jsonb(n)-ARRAY['proposal_id'])=(to_jsonb(b)-ARRAY['proposal_id'])))) THEN
 RAISE EXCEPTION 'past advice is frozen; elapsed time is not execution' USING ERRCODE='23514';END IF;
 END IF;
 IF w.active_revision_no IS NOT NULL THEN PERFORM menuto_plan_cutline_0009(old_id,p_id);END IF;
 -- Materialized components pin their exact source version, including late evidence.
 IF EXISTS(SELECT 1 FROM plan_materialization_links l WHERE l.plan_id=w.id AND (
 (l.batch_node_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM planned_cooking_batches s
 JOIN planned_cooking_batches n ON n.proposal_id=p_id AND n.node_id=s.node_id
 WHERE s.proposal_id=l.proposal_id AND s.node_id=l.batch_node_id
 AND (to_jsonb(s)-ARRAY['proposal_id'])=(to_jsonb(n)-ARRAY['proposal_id']))) OR
 (l.meal_node_id IS NOT NULL AND menuto_plan_meal_path(l.proposal_id,l.meal_node_id)
 IS DISTINCT FROM menuto_plan_meal_path(p_id,l.meal_node_id)))) THEN
 RAISE EXCEPTION 'materialized intent cannot be rewritten' USING ERRCODE='23514';END IF;
END $$;
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON shopping_demand_contributions FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON shopping_demand_contributions FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_child BEFORE INSERT ON shopping_demand_contributions FOR EACH ROW EXECUTE FUNCTION menuto_plan_child_insert();
'''
DOWNGRADE_SQL = r'''
LOCK TABLE plan_workspaces,plan_proposals,shopping_demand_contributions IN ACCESS EXCLUSIVE MODE;
DO $$ BEGIN IF EXISTS(SELECT 1 FROM shopping_demand_contributions) OR EXISTS(SELECT 1 FROM plan_proposals WHERE graph_version<>'plan-intent.v1') THEN RAISE EXCEPTION '0009 downgrade would lose intent/contribution/version provenance' USING ERRCODE='23514';END IF;END $$;
CREATE OR REPLACE FUNCTION menuto_plan_check(p_id uuid) RETURNS void LANGUAGE plpgsql AS $$
DECLARE p plan_proposals%ROWTYPE;w plan_workspaces%ROWTYPE;old_id uuid;g jsonb;o jsonb;
 count_changed integer;
BEGIN
 SELECT * INTO p FROM plan_proposals WHERE id=p_id;
 SELECT * INTO w FROM plan_workspaces WHERE id=p.plan_id AND household_id=p.household_id;
 IF p.expected_revision IS DISTINCT FROM w.active_revision_no THEN
 RAISE EXCEPTION 'STALE_ACTIVE_REVISION' USING ERRCODE='23514'; END IF;
 IF p.effective_from>w.horizon_end THEN RAISE EXCEPTION 'cut line beyond horizon' USING ERRCODE='23514';END IF;
 IF NOT EXISTS(SELECT 1 FROM plan_meal_intents WHERE proposal_id=p_id) OR EXISTS(
 SELECT 1 FROM plan_meal_intents m WHERE m.proposal_id=p_id AND
 (m.scheduled_at<w.horizon_start OR m.scheduled_at>=w.horizon_end OR NOT EXISTS(
 SELECT 1 FROM plan_meal_participants x WHERE x.proposal_id=p_id AND x.meal_node_id=m.node_id))) OR EXISTS(
 SELECT 1 FROM plan_meal_participants x WHERE x.proposal_id=p_id AND
 ((x.member_id=w.tracked_member_id)<>(x.nutrition_role='TRACKED'))) THEN
 RAISE EXCEPTION 'invalid meal horizon or participants' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM planned_cooking_batches b JOIN recipe_portion_tiers t ON t.id=b.tier_id
 WHERE b.proposal_id=p_id AND (b.planned_servings<>t.servings OR b.planned_at>=w.horizon_end)) THEN
 RAISE EXCEPTION 'batch must use exact authored tier servings/context' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM planned_batch_allocations a
 JOIN planned_cooking_batches b ON b.proposal_id=a.proposal_id AND b.node_id=a.batch_node_id
 JOIN plan_meal_intents m ON m.proposal_id=a.proposal_id AND m.node_id=a.meal_node_id
 WHERE a.proposal_id=p_id AND a.status='PLANNED' AND
 (b.status<>'PLANNED' OR m.status<>'PLANNED' OR m.meal_kind<>'HOME' OR b.planned_at>m.scheduled_at)) OR EXISTS(
 SELECT 1 FROM planned_cooking_batches b WHERE b.proposal_id=p_id AND b.planned_servings<(
 SELECT coalesce(sum(servings),0) FROM planned_batch_allocations a WHERE a.proposal_id=p_id
 AND a.batch_node_id=b.node_id AND a.status='PLANNED')) OR EXISTS(
 SELECT 1 FROM plan_meal_intents m WHERE m.proposal_id=p_id AND m.status='PLANNED' AND m.meal_kind='HOME'
 AND NOT EXISTS(SELECT 1 FROM planned_batch_allocations a WHERE a.proposal_id=p_id
 AND a.meal_node_id=m.node_id AND a.status='PLANNED')) THEN
 RAISE EXCEPTION 'invalid batch allocation/production chronology' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM shopping_requirement_intents s WHERE s.proposal_id=p_id AND s.need_by>w.horizon_end)
 OR EXISTS(SELECT 1 FROM plan_reservation_intents r JOIN inventory_lots l ON l.id=r.lot_id
 LEFT JOIN plan_meal_intents m ON m.proposal_id=r.proposal_id AND m.node_id=r.meal_node_id
 LEFT JOIN planned_cooking_batches b ON b.proposal_id=r.proposal_id AND b.node_id=r.batch_node_id
 WHERE r.proposal_id=p_id AND (r.basis<>l.basis OR r.item_ref IS DISTINCT FROM l.item_ref
 OR coalesce(m.status,b.status)<>'PLANNED')) THEN
 RAISE EXCEPTION 'invalid shopping/reservation material context' USING ERRCODE='23514';END IF;
 IF w.active_revision_no IS NOT NULL THEN
 SELECT proposal_id INTO old_id FROM plan_revisions WHERE plan_id=w.id AND revision_no=w.active_revision_no;
 IF p.effective_from < (SELECT effective_from FROM plan_proposals WHERE id=old_id) THEN
 RAISE EXCEPTION 'revision cut line regressed' USING ERRCODE='23514';END IF;
 ELSE
 SELECT id INTO old_id FROM plan_proposals WHERE plan_id=w.id AND proposal_no=p.expected_generation;
 END IF;
 g:=menuto_plan_graph(p_id);o:=menuto_plan_graph(old_id);
 IF old_id IS NOT NULL THEN
 -- Stable historical nodes remain in full snapshots; retirement is explicit content.
 IF EXISTS(SELECT 1 FROM (
 SELECT node_id FROM plan_meal_intents WHERE proposal_id=old_id EXCEPT
 SELECT node_id FROM plan_meal_intents WHERE proposal_id=p_id) x)
 OR EXISTS(SELECT 1 FROM (
 SELECT node_id FROM planned_cooking_batches WHERE proposal_id=old_id EXCEPT
 SELECT node_id FROM planned_cooking_batches WHERE proposal_id=p_id) x)
 OR EXISTS(SELECT 1 FROM (
 SELECT node_id FROM planned_batch_allocations WHERE proposal_id=old_id EXCEPT
 SELECT node_id FROM planned_batch_allocations WHERE proposal_id=p_id) x)
 OR EXISTS(SELECT 1 FROM (
 SELECT node_id FROM shopping_requirement_intents WHERE proposal_id=old_id EXCEPT
 SELECT node_id FROM shopping_requirement_intents WHERE proposal_id=p_id) x) THEN
 RAISE EXCEPTION 'retire historical intent, do not erase identity' USING ERRCODE='23514';END IF;
 WITH changed_batch AS (
 SELECT coalesce(a.v->>'node_id',b.v->>'node_id') id FROM jsonb_array_elements(o->'batches') a(v)
 FULL JOIN jsonb_array_elements(g->'batches') b(v) ON a.v->>'node_id'=b.v->>'node_id'
 WHERE a.v IS DISTINCT FROM b.v), changed AS (
 SELECT coalesce(a.v->>'node_id',b.v->>'node_id') id FROM jsonb_array_elements(o->'meals') a(v)
 FULL JOIN jsonb_array_elements(g->'meals') b(v) ON a.v->>'node_id'=b.v->>'node_id'
 WHERE a.v IS DISTINCT FROM b.v
 UNION SELECT v->>'meal_node_id' FROM jsonb_array_elements((o->'allocations')||(g->'allocations')) x(v)
 WHERE v->>'batch_node_id' IN (SELECT id FROM changed_batch)
 UNION SELECT coalesce(a.v->>'meal_node_id',b.v->>'meal_node_id') FROM jsonb_array_elements(o->'allocations') a(v)
 FULL JOIN jsonb_array_elements(g->'allocations') b(v) ON a.v->>'node_id'=b.v->>'node_id'
 WHERE a.v IS DISTINCT FROM b.v) SELECT count(DISTINCT id) INTO count_changed FROM changed;
 IF (p.scope='SINGLE_MEAL' AND count_changed<>1) OR
 (p.scope='MULTI_MEAL' AND count_changed<1) OR (p.scope='PROCUREMENT_ONLY' AND
 (o->'meals'<>g->'meals' OR o->'batches'<>g->'batches' OR o->'allocations'<>g->'allocations')) THEN
 RAISE EXCEPTION 'revision scope does not cover dependency closure' USING ERRCODE='23514';END IF;
 IF w.active_revision_no IS NOT NULL AND (EXISTS(
 SELECT 1 FROM jsonb_array_elements(o->'meals') x(v) WHERE (v->>'scheduled_at')::timestamptz<p.effective_from
 AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(g->'meals') y(n) WHERE n=v)) OR EXISTS(
 SELECT 1 FROM planned_batch_allocations a JOIN plan_meal_intents m
 ON m.proposal_id=a.proposal_id AND m.node_id=a.meal_node_id
 WHERE a.proposal_id=old_id AND m.scheduled_at<p.effective_from AND NOT EXISTS(
 SELECT 1 FROM planned_batch_allocations n WHERE n.proposal_id=p_id AND n.node_id=a.node_id
 AND (to_jsonb(n)-ARRAY['proposal_id'])=(to_jsonb(a)-ARRAY['proposal_id']))) OR EXISTS(
 SELECT 1 FROM planned_cooking_batches b WHERE b.proposal_id=old_id AND EXISTS(
 SELECT 1 FROM planned_batch_allocations a JOIN plan_meal_intents m ON m.proposal_id=a.proposal_id AND m.node_id=a.meal_node_id
 WHERE a.proposal_id=old_id AND a.batch_node_id=b.node_id AND m.scheduled_at<p.effective_from)
 AND NOT EXISTS(SELECT 1 FROM planned_cooking_batches n WHERE n.proposal_id=p_id AND n.node_id=b.node_id
 AND (to_jsonb(n)-ARRAY['proposal_id'])=(to_jsonb(b)-ARRAY['proposal_id'])))) THEN
 RAISE EXCEPTION 'past advice is frozen; elapsed time is not execution' USING ERRCODE='23514';END IF;
 END IF;
 -- Materialized components pin their exact source version, including late evidence.
 IF EXISTS(SELECT 1 FROM plan_materialization_links l WHERE l.plan_id=w.id AND (
 (l.batch_node_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM planned_cooking_batches s
 JOIN planned_cooking_batches n ON n.proposal_id=p_id AND n.node_id=s.node_id
 WHERE s.proposal_id=l.proposal_id AND s.node_id=l.batch_node_id
 AND (to_jsonb(s)-ARRAY['proposal_id'])=(to_jsonb(n)-ARRAY['proposal_id']))) OR
 (l.meal_node_id IS NOT NULL AND menuto_plan_meal_path(l.proposal_id,l.meal_node_id)
 IS DISTINCT FROM menuto_plan_meal_path(p_id,l.meal_node_id)))) THEN
 RAISE EXCEPTION 'materialized intent cannot be rewritten' USING ERRCODE='23514';END IF;
END $$;
CREATE OR REPLACE FUNCTION menuto_plan_graph(p_id uuid) RETURNS jsonb LANGUAGE sql STABLE AS $$
 SELECT jsonb_build_object('contract_version','plan-intent.v1','household_id',w.household_id,
 'plan_id',w.id,'tracked_member_id',w.tracked_member_id,'horizon',jsonb_build_object(
 'start',to_char(w.horizon_start AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
 'end',to_char(w.horizon_end AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')),
'meals',coalesce((SELECT jsonb_agg(jsonb_build_object('scheduled_at',to_char(x.scheduled_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'meal_kind',x.meal_kind,'status',x.status,'node_id',x.node_id,'participants',coalesce((SELECT jsonb_agg(jsonb_build_object('member_id',q.member_id,'portion_factor',trim_scale(q.portion_factor)::text,'nutrition_role',q.nutrition_role) ORDER BY q.member_id) FROM plan_meal_participants q WHERE q.proposal_id=x.proposal_id AND q.meal_node_id=x.node_id),'[]'::jsonb)) ORDER BY x.node_id) FROM plan_meal_intents x WHERE x.proposal_id=p_id),'[]'::jsonb),
'batches',coalesce((SELECT jsonb_agg(jsonb_build_object('recipe_version_id',x.recipe_version_id,'tier_id',x.tier_id,'planned_servings',trim_scale(x.planned_servings)::text,'planned_at',to_char(x.planned_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'status',x.status,'node_id',x.node_id) ORDER BY x.node_id) FROM planned_cooking_batches x WHERE x.proposal_id=p_id),'[]'::jsonb),
'allocations',coalesce((SELECT jsonb_agg(jsonb_build_object('batch_node_id',x.batch_node_id,'meal_node_id',x.meal_node_id,'servings',trim_scale(x.servings)::text,'status',x.status,'node_id',x.node_id) ORDER BY x.node_id) FROM planned_batch_allocations x WHERE x.proposal_id=p_id),'[]'::jsonb),
'shopping',coalesce((SELECT jsonb_agg(jsonb_build_object('ingredient_id',x.ingredient_id,'need_by',to_char(x.need_by AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'status',x.status,'node_id',x.node_id,'quantity',jsonb_build_object('amount',trim_scale(x.amount)::text,'basis',x.basis,'item_ref',x.item_ref)) ORDER BY x.node_id) FROM shopping_requirement_intents x WHERE x.proposal_id=p_id),'[]'::jsonb),
'reservations',coalesce((SELECT jsonb_agg(jsonb_build_object('lot_id',x.lot_id,'meal_node_id',x.meal_node_id,'batch_node_id',x.batch_node_id,'node_id',x.node_id,'quantity',jsonb_build_object('amount',trim_scale(x.amount)::text,'basis',x.basis,'item_ref',x.item_ref)) ORDER BY x.node_id) FROM plan_reservation_intents x WHERE x.proposal_id=p_id),'[]'::jsonb)
) FROM plan_proposals p JOIN plan_workspaces w ON w.id=p.plan_id WHERE p.id=p_id
$$;
DROP FUNCTION menuto_plan_cutline_0009(uuid,uuid);
DROP FUNCTION menuto_plan_scope_0009(uuid,uuid);
DROP FUNCTION menuto_plan_contributions_0009(uuid);
DROP FUNCTION menuto_plan_require_local_0009(uuid,uuid,jsonb,uuid);
DROP FUNCTION menuto_plan_target_meals_0009(uuid,uuid,jsonb);
DROP FUNCTION menuto_plan_anchor_0009(uuid,jsonb);
DROP FUNCTION menuto_plan_delta_0009(jsonb,jsonb,text);
DROP TABLE shopping_demand_contributions;
ALTER TABLE plan_proposals DROP COLUMN graph_version;
'''

def upgrade():
    op.execute(UPGRADE_SQL)

def downgrade():
    op.execute(DOWNGRADE_SQL)
