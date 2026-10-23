"""Authoritative sealed culinary intent; frozen SQL only."""
# ruff: noqa: E501
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

UPGRADE_SQL = r'''
ALTER TABLE preparation_transformations ADD CONSTRAINT uq_preparation_transformations_id_recipe_version_id UNIQUE(id,recipe_version_id);
ALTER TABLE plan_proposals DROP CONSTRAINT ck_plan_proposals_graph_version;
ALTER TABLE plan_proposals ADD CONSTRAINT ck_plan_proposals_graph_version CHECK(graph_version IN ('plan-intent.v1','plan-intent.v2','plan-intent.v3'));

CREATE TABLE planned_culinary_bindings (
	proposal_id UUID NOT NULL,
	batch_node_id UUID NOT NULL,
	household_id UUID NOT NULL,
	plan_id UUID NOT NULL,
	recipe_version_id UUID NOT NULL,
	tier_id UUID NOT NULL,
	planned_servings NUMERIC NOT NULL,
	approved_combination_id UUID,
	contract_version VARCHAR(50) NOT NULL,
	fingerprint VARCHAR(64) NOT NULL,
	source_kind VARCHAR(30) NOT NULL,
	source_system VARCHAR(100) NOT NULL,
	external_record_id VARCHAR(2048) NOT NULL,
	source_version VARCHAR(200) NOT NULL,
	source_uri VARCHAR(2048),
	content_hash VARCHAR(64),
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
	CONSTRAINT pk_planned_culinary_bindings PRIMARY KEY (proposal_id, batch_node_id),
	CONSTRAINT fk_planned_culinary_bindings_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT,
	CONSTRAINT fk_planned_culinary_bindings_proposal_id_planned_cookin_39af FOREIGN KEY(proposal_id, batch_node_id) REFERENCES planned_cooking_batches (proposal_id, node_id) ON DELETE RESTRICT,
	CONSTRAINT fk_planned_culinary_bindings_tier_id_recipe_portion_tiers FOREIGN KEY(tier_id, recipe_version_id) REFERENCES recipe_portion_tiers (id, recipe_version_id) ON DELETE RESTRICT,
	CONSTRAINT fk_planned_culinary_bindings_approved_combination_id_re_831d FOREIGN KEY(approved_combination_id, recipe_version_id) REFERENCES recipe_rule_combinations (id, recipe_version_id) ON DELETE RESTRICT,
	CONSTRAINT uq_planned_culinary_bindings_proposal_id_batch_node_id__0560 UNIQUE (proposal_id, batch_node_id, recipe_version_id),
	CONSTRAINT ck_planned_culinary_bindings_version CHECK (contract_version='planned-culinary-binding.v1'),
	CONSTRAINT ck_planned_culinary_bindings_fingerprint CHECK (fingerprint ~ '^[a-f0-9]{64}$'),
	CONSTRAINT ck_planned_culinary_bindings_servings CHECK (planned_servings>0 AND planned_servings<1000000000000 AND planned_servings=trunc(planned_servings,6)),
	CONSTRAINT ck_planned_culinary_bindings_source_kind CHECK (source_kind IN ('USER_AUTHORED','CURATED_REFERENCE')),
	CONSTRAINT ck_planned_culinary_bindings_source_identity CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$' AND length(trim(external_record_id))>0 AND length(trim(source_version))>0 AND isfinite(observed_at)),
	CONSTRAINT ck_planned_culinary_bindings_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$')
)

;

CREATE TABLE culinary_requirement_bindings (
	proposal_id UUID NOT NULL,
	batch_node_id UUID NOT NULL,
	requirement_id UUID NOT NULL,
	recipe_version_id UUID NOT NULL,
	selected_rule_id UUID,
	ingredient_id UUID NOT NULL,
	amount NUMERIC NOT NULL,
	basis VARCHAR(20) NOT NULL,
	item_ref VARCHAR(100),
	adjustment_delta NUMERIC NOT NULL,
	transformation_id UUID,
	CONSTRAINT pk_culinary_requirement_bindings PRIMARY KEY (proposal_id, batch_node_id, requirement_id),
	CONSTRAINT fk_culinary_requirement_bindings_proposal_id_planned_cu_7c76 FOREIGN KEY(proposal_id, batch_node_id, recipe_version_id) REFERENCES planned_culinary_bindings (proposal_id, batch_node_id, recipe_version_id) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_requirement_bindings_requirement_id_recipe__2126 FOREIGN KEY(requirement_id, recipe_version_id) REFERENCES recipe_ingredients (id, recipe_version_id) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_requirement_bindings_selected_rule_id_recip_a941 FOREIGN KEY(selected_rule_id, recipe_version_id) REFERENCES recipe_variant_rules (id, recipe_version_id) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_requirement_bindings_transformation_id_prep_db65 FOREIGN KEY(transformation_id, recipe_version_id) REFERENCES preparation_transformations (id, recipe_version_id) ON DELETE RESTRICT,
	CONSTRAINT ck_culinary_requirement_bindings_calculation CHECK (amount>0 AND amount<1e36::numeric AND amount=trunc(amount,36)),
	CONSTRAINT ck_culinary_requirement_bindings_adjustment CHECK (abs(adjustment_delta)<1000000000000 AND adjustment_delta=trunc(adjustment_delta,6)),
	CONSTRAINT ck_culinary_requirement_bindings_basis CHECK ((basis IN ('EP_RAW_G','COOKED_G') AND item_ref IS NULL) OR (basis='COUNT' AND item_ref IS NOT NULL AND item_ref ~ '^[A-Za-z0-9_.:-]+$' AND selected_rule_id IS NULL)),
	CONSTRAINT fk_culinary_requirement_bindings_ingredient_id_ingredients FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT
)

;

CREATE FUNCTION menuto_culinary_json(p uuid,b uuid) RETURNS jsonb LANGUAGE sql STABLE AS $$
 SELECT jsonb_build_object('contract_version',h.contract_version,'household_id',h.household_id,
 'plan_id',h.plan_id,'proposal_id',h.proposal_id,'batch_node_id',h.batch_node_id,
 'recipe_version_id',h.recipe_version_id,'tier_id',h.tier_id,
 'planned_servings',trim_scale(h.planned_servings)::text,'approved_combination_id',h.approved_combination_id,
 'fingerprint',h.fingerprint,'provenance',jsonb_build_object('kind',h.source_kind,'source_system',h.source_system,
 'external_record_id',h.external_record_id,'source_version',h.source_version,'source_uri',h.source_uri,
 'content_hash',h.content_hash,'observed_at',to_char(h.observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')),
 'requirements',coalesce((SELECT jsonb_agg(jsonb_build_object('requirement_id',r.requirement_id,
 'selected_rule_id',r.selected_rule_id,'ingredient_id',r.ingredient_id,'adjustment_delta',trim_scale(r.adjustment_delta)::text,
 'quantity',jsonb_build_object('amount',trim_scale(r.amount)::text,'basis',r.basis,'item_ref',r.item_ref),
 'transformation_id',r.transformation_id) ORDER BY r.requirement_id) FROM culinary_requirement_bindings r
 WHERE r.proposal_id=p AND r.batch_node_id=b),'[]'::jsonb))
 FROM planned_culinary_bindings h WHERE h.proposal_id=p AND h.batch_node_id=b
$$;
CREATE FUNCTION menuto_culinary_signature(p uuid,b uuid) RETURNS text LANGUAGE sql STABLE AS $$
 SELECT encode(sha256(convert_to(menuto_plan_canonical(menuto_culinary_json(p,b)-ARRAY['proposal_id','fingerprint']),'UTF8')),'hex')
$$;
CREATE FUNCTION menuto_culinary_child() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM planned_culinary_bindings h JOIN plan_proposals p ON p.id=h.proposal_id
 WHERE h.proposal_id=NEW.proposal_id AND h.batch_node_id=NEW.batch_node_id
 AND p.authored_transaction=pg_current_xact_id()::text) OR EXISTS(
 SELECT 1 FROM plan_proposal_seals WHERE proposal_id=NEW.proposal_id) THEN
 RAISE EXCEPTION 'culinary proposal assembly is closed' USING ERRCODE='23514'; END IF; RETURN NEW;
END $$;
CREATE FUNCTION menuto_culinary_check(p uuid) RETURNS void LANGUAGE plpgsql AS $$
DECLARE h planned_culinary_bindings%ROWTYPE;n integer;
BEGIN
 IF (SELECT graph_version FROM plan_proposals WHERE id=p)<>'plan-intent.v3' THEN
 IF EXISTS(SELECT 1 FROM plan_proposals newer JOIN plan_proposals cur ON cur.id=p AND newer.plan_id=cur.plan_id WHERE newer.graph_version='plan-intent.v3' AND newer.proposal_no<cur.proposal_no) THEN RAISE EXCEPTION 'cannot erase bound culinary intent by legacy downgrade' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM planned_culinary_bindings WHERE proposal_id=p) THEN
 RAISE EXCEPTION 'legacy graph cannot hide culinary intent' USING ERRCODE='23514';END IF;RETURN;END IF;
 IF EXISTS(SELECT 1 FROM planned_cooking_batches b WHERE b.proposal_id=p AND NOT EXISTS(
 SELECT 1 FROM planned_culinary_bindings hdr WHERE hdr.proposal_id=p AND hdr.batch_node_id=b.node_id)) THEN
 RAISE EXCEPTION 'every batch requires exact culinary binding' USING ERRCODE='23514';END IF;
 FOR h IN SELECT * FROM planned_culinary_bindings WHERE proposal_id=p LOOP
 IF NOT EXISTS(SELECT 1 FROM planned_cooking_batches b JOIN recipe_portion_tiers t ON t.id=h.tier_id
 JOIN recipe_versions v ON v.id=h.recipe_version_id JOIN recipe_version_seals z ON z.recipe_version_id=v.id
 WHERE b.proposal_id=p AND b.node_id=h.batch_node_id AND b.household_id=h.household_id AND b.plan_id=h.plan_id
 AND (b.recipe_version_id,b.tier_id,b.planned_servings)=(h.recipe_version_id,h.tier_id,h.planned_servings)
 AND t.servings=h.planned_servings AND v.review_status='REVIEWED') THEN
 RAISE EXCEPTION 'culinary batch recipe/tier/ownership mismatch' USING ERRCODE='23514';END IF;
 IF (SELECT count(*) FROM culinary_requirement_bindings WHERE proposal_id=p AND batch_node_id=h.batch_node_id)
 <> (SELECT count(*) FROM recipe_ingredients WHERE recipe_version_id=h.recipe_version_id) THEN
 RAISE EXCEPTION 'culinary requirement coverage incomplete' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM culinary_requirement_bindings r JOIN recipe_ingredients i ON i.id=r.requirement_id
 JOIN recipe_tier_quantities q ON q.tier_id=h.tier_id AND q.requirement_id=i.id
 LEFT JOIN recipe_variant_rules v ON v.id=r.selected_rule_id
 LEFT JOIN preparation_transformations t ON t.recipe_version_id=h.recipe_version_id AND t.requirement_id=i.id
 AND t.ingredient_id=r.ingredient_id
 WHERE r.proposal_id=p AND r.batch_node_id=h.batch_node_id AND (
 (v.id IS NOT NULL AND (v.requirement_id<>i.id OR i.basis='COUNT')) OR
 r.ingredient_id<>coalesce(v.replacement_ingredient_id,i.ingredient_id) OR
 r.basis<>i.basis OR r.item_ref IS DISTINCT FROM i.item_ref OR
 r.adjustment_delta<i.min_delta OR r.adjustment_delta>i.max_delta OR
 (i.adjustment_kind='DISCRETE' AND mod(r.adjustment_delta,i.adjustment_step)<>0) OR
 r.amount<>q.amount*coalesce(v.quantity_factor,1)+r.adjustment_delta OR
 (i.scaling_kind='DISCRETE' AND mod(r.amount,i.scaling_quantum)<>0) OR
 r.transformation_id IS DISTINCT FROM t.id OR (t.id IS NULL AND EXISTS(
 SELECT 1 FROM preparation_transformations orig WHERE orig.recipe_version_id=h.recipe_version_id
 AND orig.requirement_id=i.id AND orig.ingredient_id=i.ingredient_id)))) THEN
 RAISE EXCEPTION 'culinary rule/quantity/basis/transformation mismatch' USING ERRCODE='23514';END IF;
 SELECT count(*) INTO n FROM culinary_requirement_bindings r JOIN recipe_variant_rules v ON v.id=r.selected_rule_id
 WHERE r.proposal_id=p AND r.batch_node_id=h.batch_node_id AND v.structural;
 IF (n<=1 AND h.approved_combination_id IS NOT NULL) OR (n>1 AND (h.approved_combination_id IS NULL OR EXISTS(
 (SELECT rule_id FROM recipe_combination_members WHERE combination_id=h.approved_combination_id EXCEPT
 SELECT selected_rule_id FROM culinary_requirement_bindings WHERE proposal_id=p AND batch_node_id=h.batch_node_id AND selected_rule_id IS NOT NULL)
 UNION ALL (SELECT selected_rule_id FROM culinary_requirement_bindings WHERE proposal_id=p AND batch_node_id=h.batch_node_id AND selected_rule_id IS NOT NULL EXCEPT
 SELECT rule_id FROM recipe_combination_members WHERE combination_id=h.approved_combination_id)))) THEN
 RAISE EXCEPTION 'culinary structural combination not approved' USING ERRCODE='23514';END IF;
 IF h.fingerprint<>encode(sha256(convert_to(menuto_plan_canonical(menuto_culinary_json(p,h.batch_node_id)-'fingerprint'),'UTF8')),'hex') THEN
 RAISE EXCEPTION 'culinary fingerprint mismatch' USING ERRCODE='23514';END IF;
 END LOOP;
END $$;
ALTER FUNCTION menuto_plan_graph(uuid) RENAME TO menuto_plan_graph_pre_culinary_0010;
CREATE FUNCTION menuto_plan_graph(p uuid) RETURNS jsonb LANGUAGE plpgsql STABLE AS $$
DECLARE g jsonb:=menuto_plan_graph_pre_culinary_0010(p);
BEGIN
 IF g->>'contract_version'<>'plan-intent.v3' THEN RETURN g;END IF;
 RETURN g || jsonb_build_object('culinary_bindings',coalesce((SELECT jsonb_agg(menuto_culinary_json(p,b.batch_node_id) ORDER BY b.batch_node_id)
 FROM planned_culinary_bindings b WHERE b.proposal_id=p),'[]'::jsonb),
 'batches',coalesce((SELECT jsonb_agg(v || jsonb_build_object('culinary_signature',menuto_culinary_signature(p,(v->>'node_id')::uuid)) ORDER BY v->>'node_id')
 FROM jsonb_array_elements(g->'batches') x(v)),'[]'::jsonb),
 'shopping_contributions',coalesce((SELECT jsonb_agg(jsonb_build_object('node_id',c.node_id,'requirement_node_id',c.requirement_node_id,
 'meal_node_id',c.meal_node_id,'batch_node_id',c.batch_node_id,'quantity',jsonb_build_object('amount',trim_scale(c.amount)::text,'basis',c.basis,'item_ref',c.item_ref),'status',c.status)
 ORDER BY c.node_id) FROM shopping_demand_contributions c WHERE c.proposal_id=p),'[]'::jsonb));
END $$;
ALTER FUNCTION menuto_plan_check(uuid) RENAME TO menuto_plan_check_pre_culinary_0010;
CREATE FUNCTION menuto_plan_check(p_id uuid) RETURNS void LANGUAGE plpgsql AS $$
DECLARE h uuid;
BEGIN
 PERFORM menuto_culinary_check(p_id);
 PERFORM menuto_plan_check_pre_culinary_0010(p_id);
 SELECT household_id INTO h FROM plan_proposals WHERE id=p_id;
 IF EXISTS(SELECT 1 FROM plan_materialization_links l WHERE l.plan_id=(SELECT plan_id FROM plan_proposals WHERE id=p_id)
 AND l.batch_node_id IS NOT NULL AND menuto_culinary_signature(l.proposal_id,l.batch_node_id)
 IS DISTINCT FROM menuto_culinary_signature(p_id,l.batch_node_id)) THEN
 RAISE EXCEPTION 'materialized culinary binding cannot be rewritten' USING ERRCODE='23514';END IF;
END $$;
CREATE OR REPLACE FUNCTION menuto_plan_contributions_0009(p uuid) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM shopping_demand_contributions c JOIN plan_proposals p0 ON p0.id=c.proposal_id
 JOIN shopping_requirement_intents s ON s.proposal_id=c.proposal_id AND s.node_id=c.requirement_node_id
 LEFT JOIN plan_meal_intents m ON m.proposal_id=c.proposal_id AND m.node_id=c.meal_node_id
 LEFT JOIN planned_cooking_batches b ON b.proposal_id=c.proposal_id AND b.node_id=c.batch_node_id
 WHERE c.proposal_id=p AND (p0.graph_version NOT IN ('plan-intent.v2','plan-intent.v3') OR c.basis<>s.basis
 OR c.item_ref IS DISTINCT FROM s.item_ref OR (c.status='PLANNED' AND
 (s.status<>'PLANNED' OR coalesce(m.status,b.status)<>'PLANNED')))) OR EXISTS(
 SELECT 1 FROM shopping_requirement_intents s WHERE s.proposal_id=p AND EXISTS(
 SELECT 1 FROM shopping_demand_contributions c WHERE c.proposal_id=p AND c.requirement_node_id=s.node_id)
 AND (CASE WHEN s.status='PLANNED' THEN s.amount ELSE 0 END)<>(
 SELECT coalesce(sum(c.amount) FILTER (WHERE c.status='PLANNED'),0) FROM shopping_demand_contributions c
 WHERE c.proposal_id=p AND c.requirement_node_id=s.node_id)) THEN
 RAISE EXCEPTION 'invalid contribution ownership/basis/quantity conservation' USING ERRCODE='23514';END IF;
END $$;
CREATE TRIGGER culinary_immutable BEFORE UPDATE OR DELETE ON planned_culinary_bindings FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER culinary_truncate BEFORE TRUNCATE ON planned_culinary_bindings FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER culinary_immutable BEFORE UPDATE OR DELETE ON culinary_requirement_bindings FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER culinary_truncate BEFORE TRUNCATE ON culinary_requirement_bindings FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER culinary_child BEFORE INSERT ON planned_culinary_bindings FOR EACH ROW EXECUTE FUNCTION menuto_plan_child_insert();
CREATE TRIGGER culinary_child BEFORE INSERT ON culinary_requirement_bindings FOR EACH ROW EXECUTE FUNCTION menuto_culinary_child();
'''
DOWNGRADE_SQL = r'''
LOCK TABLE plan_proposals,planned_culinary_bindings,culinary_requirement_bindings IN ACCESS EXCLUSIVE MODE;
DO $$ BEGIN IF EXISTS(SELECT 1 FROM plan_proposals WHERE graph_version='plan-intent.v3') OR EXISTS(SELECT 1 FROM planned_culinary_bindings) THEN RAISE EXCEPTION '0010 downgrade would lose culinary binding history' USING ERRCODE='23514';END IF;END $$;
DROP FUNCTION menuto_plan_check(uuid);
ALTER FUNCTION menuto_plan_check_pre_culinary_0010(uuid) RENAME TO menuto_plan_check;
DROP FUNCTION menuto_plan_graph(uuid);
ALTER FUNCTION menuto_plan_graph_pre_culinary_0010(uuid) RENAME TO menuto_plan_graph;
CREATE OR REPLACE FUNCTION menuto_plan_contributions_0009(p uuid) RETURNS void LANGUAGE plpgsql AS $$
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
DROP TABLE culinary_requirement_bindings;
DROP TABLE planned_culinary_bindings;
ALTER TABLE preparation_transformations DROP CONSTRAINT uq_preparation_transformations_id_recipe_version_id;
DROP FUNCTION menuto_culinary_check(uuid);
DROP FUNCTION menuto_culinary_child();
DROP FUNCTION menuto_culinary_signature(uuid,uuid);
DROP FUNCTION menuto_culinary_json(uuid,uuid);
ALTER TABLE plan_proposals DROP CONSTRAINT ck_plan_proposals_graph_version;
ALTER TABLE plan_proposals ADD CONSTRAINT ck_plan_proposals_graph_version CHECK(graph_version IN ('plan-intent.v1','plan-intent.v2'));
'''

def upgrade():
    op.execute(UPGRADE_SQL)

def downgrade():
    op.execute(DOWNGRADE_SQL)
