"""F/MTR-016 relational intent and guarded revision foundation; frozen PostgreSQL SQL."""
# ruff: noqa: E501 -- frozen DDL and trigger SQL
from alembic import op

revision="0008"
down_revision="0007"
branch_labels=None
depends_on=None
UPGRADE_SQL=r'''

CREATE TABLE plan_workspaces (
	id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	tracked_member_id UUID NOT NULL, 
	created_by_user_id UUID NOT NULL, 
	horizon_start TIMESTAMP WITH TIME ZONE NOT NULL, 
	horizon_end TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT clock_timestamp() NOT NULL, 
	state VARCHAR(20) DEFAULT 'DRAFT' NOT NULL, 
	active_revision_no INTEGER, 
	latest_proposal_no INTEGER DEFAULT '-1' NOT NULL, 
	boundary_version BIGINT DEFAULT '0' NOT NULL, 
	CONSTRAINT pk_plan_workspaces PRIMARY KEY (id), 
	CONSTRAINT uq_plan_workspaces_id_household_id UNIQUE (id, household_id), 
	CONSTRAINT ck_plan_workspaces_state CHECK ((state='DRAFT' AND active_revision_no IS NULL) OR (state='ACTIVE' AND active_revision_no>=0)), 
	CONSTRAINT ck_plan_workspaces_counters CHECK (latest_proposal_no>=-1 AND boundary_version>=0), 
	CONSTRAINT ck_plan_workspaces_horizon CHECK (isfinite(horizon_start) AND isfinite(horizon_end) AND horizon_start<horizon_end)
)

;

CREATE TABLE plan_proposals (
	id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	proposal_no INTEGER NOT NULL, 
	expected_generation INTEGER NOT NULL, 
	expected_revision INTEGER, 
	scope VARCHAR(30) NOT NULL, 
	effective_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	actor_user_id UUID NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	idempotency_key VARCHAR(100) NOT NULL, 
	command_fingerprint VARCHAR(64) NOT NULL, 
	reason VARCHAR(200) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT clock_timestamp() NOT NULL, 
	authored_transaction VARCHAR(100) DEFAULT '' NOT NULL, 
	CONSTRAINT pk_plan_proposals PRIMARY KEY (id), 
	CONSTRAINT uq_plan_proposals_id_household_id_plan_id UNIQUE (id, household_id, plan_id), 
	CONSTRAINT uq_plan_proposals_plan_id_proposal_no UNIQUE (plan_id, proposal_no), 
	CONSTRAINT uq_plan_proposals_plan_id_source_system_idempotency_key UNIQUE (plan_id, source_system, idempotency_key), 
	CONSTRAINT ck_plan_proposals_scope CHECK (scope IN ('SINGLE_MEAL','MULTI_MEAL','REMAINING_HORIZON','PROCUREMENT_ONLY')), 
	CONSTRAINT ck_plan_proposals_versions CHECK (proposal_no>=0 AND expected_generation>=-1 AND (expected_revision IS NULL OR expected_revision>=0)), 
	CONSTRAINT ck_plan_proposals_effective_time CHECK (isfinite(effective_from)), 
	CONSTRAINT ck_plan_proposals_source CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$' AND command_fingerprint ~ '^[a-f0-9]{64}$' AND length(trim(reason))>0)
)

;

CREATE TABLE plan_proposal_seals (
	proposal_id UUID NOT NULL, 
	graph_hash VARCHAR(64) DEFAULT '' NOT NULL, 
	CONSTRAINT pk_plan_proposal_seals PRIMARY KEY (proposal_id), 
	CONSTRAINT ck_plan_proposal_seals_hash CHECK (graph_hash ~ '^[a-f0-9]{64}$')
)

;

CREATE TABLE plan_meal_intents (
	scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	meal_kind VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	proposal_id UUID NOT NULL, 
	node_id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	CONSTRAINT pk_plan_meal_intents PRIMARY KEY (proposal_id, node_id), 
	CONSTRAINT ck_plan_meal_intents_kind CHECK (meal_kind IN ('HOME','OUTSIDE','SKIP')), 
	CONSTRAINT ck_plan_meal_intents_status CHECK (status IN ('PLANNED','RETIRED')), 
	CONSTRAINT ck_plan_meal_intents_time CHECK (isfinite(scheduled_at))
)

;

CREATE TABLE plan_meal_participants (
	proposal_id UUID NOT NULL, 
	meal_node_id UUID NOT NULL, 
	member_id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	portion_factor NUMERIC NOT NULL, 
	nutrition_role VARCHAR(20) NOT NULL, 
	CONSTRAINT pk_plan_meal_participants PRIMARY KEY (proposal_id, meal_node_id, member_id), 
	CONSTRAINT ck_plan_meal_participants_role CHECK (nutrition_role IN ('TRACKED','SHARED')), 
	CONSTRAINT ck_plan_meal_participants_portion CHECK (portion_factor>0 AND portion_factor<1000000000000 AND portion_factor=trunc(portion_factor,6))
)

;

CREATE TABLE plan_reservation_intents (
	lot_id UUID NOT NULL, 
	meal_node_id UUID, 
	batch_node_id UUID, 
	amount NUMERIC NOT NULL, 
	basis VARCHAR(20) NOT NULL, 
	item_ref VARCHAR(100), 
	proposal_id UUID NOT NULL, 
	node_id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	CONSTRAINT pk_plan_reservation_intents PRIMARY KEY (proposal_id, node_id), 
	CONSTRAINT ck_plan_reservation_intents_target CHECK ((meal_node_id IS NULL) <> (batch_node_id IS NULL)), 
	CONSTRAINT ck_plan_reservation_intents_amount CHECK (amount>0 AND amount<1000000000000 AND amount=trunc(amount,6)), 
	CONSTRAINT ck_plan_reservation_intents_identity CHECK ((basis IN ('COUNT','SERVING') AND item_ref IS NOT NULL AND item_ref ~ '^[A-Za-z0-9_.:-]+$') OR (basis IN ('AP_G','EP_RAW_G','COOKED_G') AND item_ref IS NULL))
)

;

CREATE TABLE plan_validation_authorizations (
	id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	proposal_id UUID NOT NULL, 
	graph_hash VARCHAR(64) NOT NULL, 
	subject_hash VARCHAR(64) NOT NULL, 
	report_digest VARCHAR(64) NOT NULL, 
	validator_version VARCHAR(100) NOT NULL, 
	inventory_frontier BIGINT NOT NULL, 
	boundary_version BIGINT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT clock_timestamp() NOT NULL, 
	valid_until TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_plan_validation_authorizations PRIMARY KEY (id), 
	CONSTRAINT uq_plan_validation_authorizations_id_household_id_plan__00fd UNIQUE (id, household_id, plan_id, proposal_id), 
	CONSTRAINT ck_plan_validation_authorizations_hashes CHECK (graph_hash ~ '^[a-f0-9]{64}$' AND subject_hash ~ '^[a-f0-9]{64}$' AND report_digest ~ '^[a-f0-9]{64}$' AND validator_version ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_plan_validation_authorizations_frontier CHECK (inventory_frontier>=0 AND boundary_version>=0), 
	CONSTRAINT ck_plan_validation_authorizations_deadline CHECK (isfinite(valid_until) AND valid_until>created_at)
)

;

CREATE TABLE plan_revisions (
	id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	proposal_id UUID NOT NULL, 
	revision_no INTEGER NOT NULL, 
	parent_revision_no INTEGER, 
	authorization_id UUID NOT NULL, 
	actor_user_id UUID NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	idempotency_key VARCHAR(100) NOT NULL, 
	command_fingerprint VARCHAR(64) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT clock_timestamp() NOT NULL, 
	authored_transaction VARCHAR(100) DEFAULT '' NOT NULL, 
	CONSTRAINT pk_plan_revisions PRIMARY KEY (id), 
	CONSTRAINT uq_plan_revisions_plan_id_revision_no UNIQUE (plan_id, revision_no), 
	CONSTRAINT uq_plan_revisions_plan_id_household_id_revision_no UNIQUE (plan_id, household_id, revision_no), 
	CONSTRAINT uq_plan_revisions_plan_id_source_system_idempotency_key UNIQUE (plan_id, source_system, idempotency_key), 
	CONSTRAINT uq_plan_revisions_authorization_id UNIQUE (authorization_id), 
	CONSTRAINT ck_plan_revisions_chain CHECK ((revision_no=0 AND parent_revision_no IS NULL) OR (revision_no>0 AND parent_revision_no=revision_no-1)), 
	CONSTRAINT ck_plan_revisions_source CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$' AND command_fingerprint ~ '^[a-f0-9]{64}$')
)

;

CREATE TABLE plan_revision_reservations (
	plan_id UUID NOT NULL, 
	revision_no INTEGER NOT NULL, 
	intent_node_id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	proposal_id UUID NOT NULL, 
	lot_id UUID NOT NULL, 
	reservation_id UUID NOT NULL, 
	CONSTRAINT pk_plan_revision_reservations PRIMARY KEY (plan_id, revision_no, intent_node_id)
)

;

CREATE TABLE plan_materialization_links (
	id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	proposal_id UUID NOT NULL, 
	source_revision_no INTEGER NOT NULL, 
	meal_node_id UUID, 
	batch_node_id UUID, 
	shopping_node_id UUID, 
	lot_id UUID NOT NULL, 
	movement_id UUID NOT NULL, 
	actor_user_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT clock_timestamp() NOT NULL, 
	CONSTRAINT pk_plan_materialization_links PRIMARY KEY (id), 
	CONSTRAINT uq_plan_materialization_links_movement_id UNIQUE (movement_id), 
	CONSTRAINT ck_plan_materialization_links_target CHECK (num_nonnulls(meal_node_id,batch_node_id,shopping_node_id)=1)
)

;

CREATE TABLE planned_cooking_batches (
	recipe_version_id UUID NOT NULL, 
	tier_id UUID NOT NULL, 
	planned_servings NUMERIC NOT NULL, 
	planned_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	proposal_id UUID NOT NULL, 
	node_id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	CONSTRAINT pk_planned_cooking_batches PRIMARY KEY (proposal_id, node_id), 
	CONSTRAINT ck_planned_cooking_batches_status CHECK (status IN ('PLANNED','RETIRED')), 
	CONSTRAINT ck_planned_cooking_batches_time CHECK (isfinite(planned_at)), 
	CONSTRAINT ck_planned_cooking_batches_servings CHECK (planned_servings>0 AND planned_servings<1000000000000 AND planned_servings=trunc(planned_servings,6))
)

;

CREATE TABLE planned_batch_allocations (
	batch_node_id UUID NOT NULL, 
	meal_node_id UUID NOT NULL, 
	servings NUMERIC NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	proposal_id UUID NOT NULL, 
	node_id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	CONSTRAINT pk_planned_batch_allocations PRIMARY KEY (proposal_id, node_id), 
	CONSTRAINT ck_planned_batch_allocations_status CHECK (status IN ('PLANNED','RETIRED')), 
	CONSTRAINT ck_planned_batch_allocations_servings CHECK (servings>0 AND servings<1000000000000 AND servings=trunc(servings,6))
)

;

CREATE TABLE shopping_requirement_intents (
	ingredient_id UUID NOT NULL, 
	amount NUMERIC NOT NULL, 
	basis VARCHAR(20) NOT NULL, 
	item_ref VARCHAR(100), 
	need_by TIMESTAMP WITH TIME ZONE NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	proposal_id UUID NOT NULL, 
	node_id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	CONSTRAINT pk_shopping_requirement_intents PRIMARY KEY (proposal_id, node_id), 
	CONSTRAINT ck_shopping_requirement_intents_status CHECK (status IN ('PLANNED','RETIRED')), 
	CONSTRAINT ck_shopping_requirement_intents_time CHECK (isfinite(need_by)), 
	CONSTRAINT ck_shopping_requirement_intents_amount CHECK (amount>0 AND amount<1000000000000 AND amount=trunc(amount,6)), 
	CONSTRAINT ck_shopping_requirement_intents_basis CHECK ((basis='COUNT' AND item_ref IS NOT NULL AND item_ref ~ '^[A-Za-z0-9_.:-]+$') OR (basis IN ('AP_G','EP_RAW_G','COOKED_G') AND item_ref IS NULL))
)

;
ALTER TABLE plan_workspaces ADD CONSTRAINT fk_plan_workspaces_household_id_household_members FOREIGN KEY(household_id, tracked_member_id) REFERENCES household_members (household_id, id) ON DELETE RESTRICT;
ALTER TABLE plan_workspaces ADD CONSTRAINT fk_plan_workspaces_household_id_households FOREIGN KEY(household_id) REFERENCES households (id) ON DELETE RESTRICT;
ALTER TABLE plan_workspaces ADD CONSTRAINT fk_plan_workspaces_household_id_memberships FOREIGN KEY(household_id, created_by_user_id) REFERENCES memberships (household_id, user_id) ON DELETE RESTRICT;
ALTER TABLE plan_workspaces ADD CONSTRAINT fk_plan_workspaces_id_plan_revisions FOREIGN KEY(id, household_id, active_revision_no) REFERENCES plan_revisions (plan_id, household_id, revision_no) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE plan_proposals ADD CONSTRAINT fk_plan_proposal_requires_seal FOREIGN KEY(id) REFERENCES plan_proposal_seals (proposal_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE plan_proposals ADD CONSTRAINT fk_plan_proposals_household_id_memberships FOREIGN KEY(household_id, actor_user_id) REFERENCES memberships (household_id, user_id) ON DELETE RESTRICT;
ALTER TABLE plan_proposals ADD CONSTRAINT fk_plan_proposals_plan_id_plan_workspaces FOREIGN KEY(plan_id, household_id) REFERENCES plan_workspaces (id, household_id) ON DELETE RESTRICT;
ALTER TABLE plan_proposal_seals ADD CONSTRAINT fk_plan_proposal_seals_proposal_id_plan_proposals FOREIGN KEY(proposal_id) REFERENCES plan_proposals (id) ON DELETE RESTRICT;
ALTER TABLE plan_meal_intents ADD CONSTRAINT fk_plan_meal_intents_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT;
ALTER TABLE plan_meal_participants ADD CONSTRAINT fk_plan_meal_participants_household_id_household_members FOREIGN KEY(household_id, member_id) REFERENCES household_members (household_id, id) ON DELETE RESTRICT;
ALTER TABLE plan_meal_participants ADD CONSTRAINT fk_plan_meal_participants_proposal_id_plan_meal_intents FOREIGN KEY(proposal_id, meal_node_id) REFERENCES plan_meal_intents (proposal_id, node_id) ON DELETE RESTRICT;
ALTER TABLE plan_meal_participants ADD CONSTRAINT fk_plan_meal_participants_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT;
ALTER TABLE plan_reservation_intents ADD CONSTRAINT fk_plan_reservation_intents_household_id_inventory_lots FOREIGN KEY(household_id, lot_id) REFERENCES inventory_lots (household_id, id) ON DELETE RESTRICT;
ALTER TABLE plan_reservation_intents ADD CONSTRAINT fk_plan_reservation_intents_proposal_id_plan_meal_intents FOREIGN KEY(proposal_id, meal_node_id) REFERENCES plan_meal_intents (proposal_id, node_id) ON DELETE RESTRICT;
ALTER TABLE plan_reservation_intents ADD CONSTRAINT fk_plan_reservation_intents_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT;
ALTER TABLE plan_reservation_intents ADD CONSTRAINT fk_plan_reservation_intents_proposal_id_planned_cooking_batches FOREIGN KEY(proposal_id, batch_node_id) REFERENCES planned_cooking_batches (proposal_id, node_id) ON DELETE RESTRICT;
ALTER TABLE plan_validation_authorizations ADD CONSTRAINT fk_plan_validation_authorizations_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT;
ALTER TABLE plan_revisions ADD CONSTRAINT fk_plan_revisions_authorization_id_plan_validation_auth_6c78 FOREIGN KEY(authorization_id, household_id, plan_id, proposal_id) REFERENCES plan_validation_authorizations (id, household_id, plan_id, proposal_id) ON DELETE RESTRICT;
ALTER TABLE plan_revisions ADD CONSTRAINT fk_plan_revisions_household_id_memberships FOREIGN KEY(household_id, actor_user_id) REFERENCES memberships (household_id, user_id) ON DELETE RESTRICT;
ALTER TABLE plan_revisions ADD CONSTRAINT fk_plan_revisions_plan_id_plan_revisions FOREIGN KEY(plan_id, household_id, parent_revision_no) REFERENCES plan_revisions (plan_id, household_id, revision_no) ON DELETE RESTRICT;
ALTER TABLE plan_revisions ADD CONSTRAINT fk_plan_revisions_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT;
ALTER TABLE plan_revision_reservations ADD CONSTRAINT fk_plan_revision_reservations_household_id_inventory_re_a837 FOREIGN KEY(household_id, lot_id, reservation_id) REFERENCES inventory_reservations (household_id, lot_id, id) ON DELETE RESTRICT;
ALTER TABLE plan_revision_reservations ADD CONSTRAINT fk_plan_revision_reservations_plan_id_plan_revisions FOREIGN KEY(plan_id, household_id, revision_no) REFERENCES plan_revisions (plan_id, household_id, revision_no) ON DELETE RESTRICT;
ALTER TABLE plan_revision_reservations ADD CONSTRAINT fk_plan_revision_reservations_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT;
ALTER TABLE plan_revision_reservations ADD CONSTRAINT fk_plan_revision_reservations_proposal_id_plan_reservat_00c6 FOREIGN KEY(proposal_id, intent_node_id) REFERENCES plan_reservation_intents (proposal_id, node_id) ON DELETE RESTRICT;
ALTER TABLE plan_materialization_links ADD CONSTRAINT fk_plan_materialization_links_household_id_inventory_movements FOREIGN KEY(household_id, lot_id, movement_id) REFERENCES inventory_movements (household_id, lot_id, id) ON DELETE RESTRICT;
ALTER TABLE plan_materialization_links ADD CONSTRAINT fk_plan_materialization_links_household_id_memberships FOREIGN KEY(household_id, actor_user_id) REFERENCES memberships (household_id, user_id) ON DELETE RESTRICT;
ALTER TABLE plan_materialization_links ADD CONSTRAINT fk_plan_materialization_links_plan_id_plan_revisions FOREIGN KEY(plan_id, household_id, source_revision_no) REFERENCES plan_revisions (plan_id, household_id, revision_no) ON DELETE RESTRICT;
ALTER TABLE plan_materialization_links ADD CONSTRAINT fk_plan_materialization_links_proposal_id_plan_meal_intents FOREIGN KEY(proposal_id, meal_node_id) REFERENCES plan_meal_intents (proposal_id, node_id) ON DELETE RESTRICT;
ALTER TABLE plan_materialization_links ADD CONSTRAINT fk_plan_materialization_links_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT;
ALTER TABLE plan_materialization_links ADD CONSTRAINT fk_plan_materialization_links_proposal_id_planned_cooki_37ab FOREIGN KEY(proposal_id, batch_node_id) REFERENCES planned_cooking_batches (proposal_id, node_id) ON DELETE RESTRICT;
ALTER TABLE plan_materialization_links ADD CONSTRAINT fk_plan_materialization_links_proposal_id_shopping_requ_f4d2 FOREIGN KEY(proposal_id, shopping_node_id) REFERENCES shopping_requirement_intents (proposal_id, node_id) ON DELETE RESTRICT;
ALTER TABLE planned_cooking_batches ADD CONSTRAINT fk_planned_cooking_batches_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT;
ALTER TABLE planned_cooking_batches ADD CONSTRAINT fk_planned_cooking_batches_recipe_version_id_recipe_versions FOREIGN KEY(recipe_version_id) REFERENCES recipe_versions (id) ON DELETE RESTRICT;
ALTER TABLE planned_cooking_batches ADD CONSTRAINT fk_planned_cooking_batches_tier_id_recipe_portion_tiers FOREIGN KEY(tier_id, recipe_version_id) REFERENCES recipe_portion_tiers (id, recipe_version_id) ON DELETE RESTRICT;
ALTER TABLE planned_batch_allocations ADD CONSTRAINT fk_planned_batch_allocations_proposal_id_plan_meal_intents FOREIGN KEY(proposal_id, meal_node_id) REFERENCES plan_meal_intents (proposal_id, node_id) ON DELETE RESTRICT;
ALTER TABLE planned_batch_allocations ADD CONSTRAINT fk_planned_batch_allocations_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT;
ALTER TABLE planned_batch_allocations ADD CONSTRAINT fk_planned_batch_allocations_proposal_id_planned_cookin_ca12 FOREIGN KEY(proposal_id, batch_node_id) REFERENCES planned_cooking_batches (proposal_id, node_id) ON DELETE RESTRICT;
ALTER TABLE shopping_requirement_intents ADD CONSTRAINT fk_shopping_requirement_intents_ingredient_id_ingredients FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT;
ALTER TABLE shopping_requirement_intents ADD CONSTRAINT fk_shopping_requirement_intents_proposal_id_plan_proposals FOREIGN KEY(proposal_id, household_id, plan_id) REFERENCES plan_proposals (id, household_id, plan_id) ON DELETE RESTRICT;
CREATE FUNCTION menuto_plan_graph(p_id uuid) RETURNS jsonb LANGUAGE sql STABLE AS $$
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

CREATE FUNCTION menuto_plan_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'plan history is immutable' USING ERRCODE='23514'; END $$;
CREATE FUNCTION menuto_plan_no_authority() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'PRECOMMIT authority not installed' USING ERRCODE='23514'; END $$;
CREATE FUNCTION menuto_plan_workspace_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='TRUNCATE' OR TG_OP='DELETE' OR pg_trigger_depth()<>2 OR
 (to_jsonb(NEW)-ARRAY['state','active_revision_no','latest_proposal_no','boundary_version']) IS DISTINCT FROM
 (to_jsonb(OLD)-ARRAY['state','active_revision_no','latest_proposal_no','boundary_version']) THEN
 RAISE EXCEPTION 'plan workspace is transaction-controlled' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION menuto_plan_actor(h uuid,a uuid) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM memberships WHERE household_id=h AND user_id=a
 AND role IN ('OWNER','EDITOR')) THEN
 RAISE EXCEPTION 'plan requires household editor' USING ERRCODE='23514'; END IF;
END $$;
CREATE FUNCTION menuto_plan_begin_workspace() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 PERFORM pg_advisory_xact_lock(hashtextextended('inventory.household:'||NEW.household_id::text,0));
 PERFORM menuto_plan_actor(NEW.household_id,NEW.created_by_user_id);
 NEW.state:='DRAFT'; NEW.active_revision_no:=NULL;NEW.latest_proposal_no:=-1;NEW.boundary_version:=0;
 NEW.created_at:=clock_timestamp(); RETURN NEW;
END $$;
CREATE FUNCTION menuto_plan_begin_proposal() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE w plan_workspaces%ROWTYPE;
BEGIN
 PERFORM pg_advisory_xact_lock(hashtextextended('inventory.household:'||NEW.household_id::text,0));
 SELECT * INTO w FROM plan_workspaces WHERE id=NEW.plan_id AND household_id=NEW.household_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'plan household mismatch' USING ERRCODE='23503';END IF;
 PERFORM menuto_plan_actor(NEW.household_id,NEW.actor_user_id);
 IF NEW.expected_generation<>w.latest_proposal_no OR
 NEW.expected_revision IS DISTINCT FROM w.active_revision_no THEN
 RAISE EXCEPTION 'STALE_PLAN_GENERATION_OR_REVISION' USING ERRCODE='23514';END IF;
 NEW.proposal_no:=w.latest_proposal_no+1;
 NEW.authored_transaction:=pg_current_xact_id()::text;NEW.created_at:=clock_timestamp();
 UPDATE plan_workspaces SET latest_proposal_no=NEW.proposal_no WHERE id=w.id;
 RETURN NEW;
END $$;
CREATE FUNCTION menuto_plan_child_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE tx text;
BEGIN
 SELECT authored_transaction INTO tx FROM plan_proposals WHERE id=NEW.proposal_id
 AND household_id=NEW.household_id AND plan_id=NEW.plan_id;
 IF tx IS NULL OR tx<>pg_current_xact_id()::text OR EXISTS(
 SELECT 1 FROM plan_proposal_seals WHERE proposal_id=NEW.proposal_id) THEN
 RAISE EXCEPTION 'plan proposal assembly is closed' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION menuto_plan_canonical(j jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE STRICT AS $$
DECLARE result text;
BEGIN
 CASE jsonb_typeof(j)
 WHEN 'object' THEN SELECT '{'||coalesce(string_agg(to_json(k)::text||':'||menuto_plan_canonical(v),
 ',' ORDER BY k COLLATE "C"),'')||'}' INTO result FROM jsonb_each(j) x(k,v);
 WHEN 'array' THEN SELECT '['||coalesce(string_agg(menuto_plan_canonical(v),',' ORDER BY n),'')||']'
 INTO result FROM jsonb_array_elements(j) WITH ORDINALITY x(v,n);
 ELSE result:=j::text;
 END CASE; RETURN result;
END $$;
CREATE FUNCTION menuto_plan_inventory_frontier(h uuid) RETURNS bigint LANGUAGE sql STABLE AS $$
 SELECT coalesce(max(n),0) FROM (
 SELECT ledger_sequence n FROM inventory_movements WHERE household_id=h
 UNION ALL SELECT ledger_sequence FROM inventory_reservations WHERE household_id=h
 UNION ALL SELECT ledger_sequence FROM inventory_reservation_releases WHERE household_id=h) x
$$;
CREATE FUNCTION menuto_plan_meal_path(p uuid,n uuid) RETURNS jsonb LANGUAGE sql STABLE AS $$
 SELECT jsonb_build_object('meal',(SELECT v FROM jsonb_array_elements(menuto_plan_graph(p)->'meals') x(v)
 WHERE v->>'node_id'=n::text),'allocations',coalesce((SELECT jsonb_agg(v ORDER BY v->>'node_id')
 FROM jsonb_array_elements(menuto_plan_graph(p)->'allocations') x(v) WHERE v->>'meal_node_id'=n::text),'[]'::jsonb),
 'batches',coalesce((SELECT jsonb_agg(v ORDER BY v->>'node_id') FROM jsonb_array_elements(menuto_plan_graph(p)->'batches') x(v)
 WHERE v->>'node_id' IN(SELECT a.batch_node_id::text FROM planned_batch_allocations a
 WHERE a.proposal_id=p AND a.meal_node_id=n)),'[]'::jsonb))
$$;
CREATE FUNCTION menuto_plan_check(p_id uuid) RETURNS void LANGUAGE plpgsql AS $$
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
CREATE FUNCTION menuto_plan_seal() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE p plan_proposals%ROWTYPE;
BEGIN
 SELECT * INTO p FROM plan_proposals WHERE id=NEW.proposal_id;
 IF p.authored_transaction<>pg_current_xact_id()::text THEN
 RAISE EXCEPTION 'plan proposal assembly is closed' USING ERRCODE='23514';END IF;
 PERFORM menuto_plan_check(NEW.proposal_id);
 NEW.graph_hash:=encode(sha256(convert_to(menuto_plan_canonical(menuto_plan_graph(NEW.proposal_id)),'UTF8')),'hex');
 RETURN NEW;
END $$;
CREATE FUNCTION menuto_plan_revision() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE w plan_workspaces%ROWTYPE;p plan_proposals%ROWTYPE;a plan_validation_authorizations%ROWTYPE;
BEGIN
 PERFORM pg_advisory_xact_lock(hashtextextended('inventory.household:'||NEW.household_id::text,0));
 SELECT * INTO w FROM plan_workspaces WHERE id=NEW.plan_id AND household_id=NEW.household_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'plan household mismatch' USING ERRCODE='23503';END IF;
 PERFORM menuto_plan_actor(NEW.household_id,NEW.actor_user_id);
 SELECT * INTO p FROM plan_proposals WHERE id=NEW.proposal_id AND household_id=NEW.household_id AND plan_id=w.id;
 IF NOT FOUND OR NOT EXISTS(SELECT 1 FROM plan_proposal_seals WHERE proposal_id=p.id) THEN
 RAISE EXCEPTION 'revision requires sealed exact proposal' USING ERRCODE='23514';END IF;
 PERFORM menuto_plan_check(p.id);
 SELECT * INTO a FROM plan_validation_authorizations WHERE id=NEW.authorization_id
 AND household_id=NEW.household_id AND plan_id=w.id AND proposal_id=p.id;
 IF NOT FOUND OR a.graph_hash<>(SELECT graph_hash FROM plan_proposal_seals WHERE proposal_id=p.id)
 OR a.inventory_frontier<>menuto_plan_inventory_frontier(w.household_id)
 OR a.boundary_version<>w.boundary_version OR a.valid_until<=clock_timestamp() THEN
 RAISE EXCEPTION 'PRECOMMIT authorization absent/stale/wrong subject frontier' USING ERRCODE='23514';END IF;
 NEW.revision_no:=coalesce(w.active_revision_no+1,0);NEW.parent_revision_no:=w.active_revision_no;
 NEW.created_at:=clock_timestamp();NEW.authored_transaction:=pg_current_xact_id()::text;
 UPDATE plan_workspaces SET state='ACTIVE',active_revision_no=NEW.revision_no WHERE id=w.id;
 RETURN NEW;
END $$;
CREATE FUNCTION menuto_plan_reservation_target(p uuid,n uuid) RETURNS jsonb LANGUAGE sql STABLE AS $$
 SELECT CASE WHEN i.batch_node_id IS NOT NULL THEN
 (SELECT v FROM jsonb_array_elements(menuto_plan_graph(p)->'batches') x(v) WHERE v->>'node_id'=i.batch_node_id::text)
 ELSE jsonb_build_object('meal',(SELECT v FROM jsonb_array_elements(menuto_plan_graph(p)->'meals') x(v)
 WHERE v->>'node_id'=i.meal_node_id::text),'allocations',coalesce((SELECT jsonb_agg(v ORDER BY v->>'node_id')
 FROM jsonb_array_elements(menuto_plan_graph(p)->'allocations') x(v) WHERE v->>'meal_node_id'=i.meal_node_id::text),'[]'::jsonb),
 'batches',coalesce((SELECT jsonb_agg(v ORDER BY v->>'node_id') FROM jsonb_array_elements(menuto_plan_graph(p)->'batches') x(v)
 WHERE v->>'node_id' IN(SELECT a.batch_node_id::text FROM planned_batch_allocations a
 WHERE a.proposal_id=p AND a.meal_node_id=i.meal_node_id)),'[]'::jsonb)) END
 FROM plan_reservation_intents i WHERE i.proposal_id=p AND i.node_id=n
$$;
CREATE FUNCTION menuto_plan_revision_reservation() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE r plan_revisions%ROWTYPE;i plan_reservation_intents%ROWTYPE;s inventory_reservations%ROWTYPE;
BEGIN
 SELECT * INTO r FROM plan_revisions WHERE plan_id=NEW.plan_id AND household_id=NEW.household_id
 AND revision_no=NEW.revision_no;
 IF NOT FOUND OR r.authored_transaction<>pg_current_xact_id()::text OR r.proposal_id<>NEW.proposal_id THEN
 RAISE EXCEPTION 'revision reservation assembly is closed' USING ERRCODE='23514';END IF;
 SELECT * INTO i FROM plan_reservation_intents WHERE proposal_id=NEW.proposal_id AND node_id=NEW.intent_node_id;
 SELECT * INTO s FROM inventory_reservations WHERE id=NEW.reservation_id AND household_id=NEW.household_id AND lot_id=NEW.lot_id;
 IF i.lot_id IS DISTINCT FROM s.lot_id OR i.amount IS DISTINCT FROM s.amount
 OR i.basis IS DISTINCT FROM s.basis OR i.item_ref IS DISTINCT FROM s.item_ref OR EXISTS(
 SELECT 1 FROM inventory_reservation_releases WHERE reservation_id=s.id) THEN
 RAISE EXCEPTION 'reservation evidence disagrees with intent' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM plan_revision_reservations previous_link JOIN plan_reservation_intents oi
 ON oi.proposal_id=previous_link.proposal_id AND oi.node_id=previous_link.intent_node_id
 WHERE previous_link.reservation_id=s.id AND (previous_link.plan_id<>NEW.plan_id OR
 (to_jsonb(oi)-ARRAY['proposal_id']) IS DISTINCT FROM (to_jsonb(i)-ARRAY['proposal_id']) OR
 menuto_plan_reservation_target(oi.proposal_id,oi.node_id) IS DISTINCT FROM
 menuto_plan_reservation_target(i.proposal_id,i.node_id))) THEN
 RAISE EXCEPTION 'cannot retarget physical reservation' USING ERRCODE='23514';END IF;
 IF NOT EXISTS(SELECT 1 FROM plan_revision_reservations previous_link WHERE previous_link.reservation_id=s.id)
 AND (s.recorded_at<r.created_at OR s.source_system<>'plan.revision') THEN
 RAISE EXCEPTION 'cannot commandeer unlinked manual reservation' USING ERRCODE='23514';END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION menuto_plan_revision_complete() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.parent_revision_no IS NOT NULL AND EXISTS(
 SELECT 1 FROM plan_revision_reservations previous_link WHERE previous_link.plan_id=NEW.plan_id
 AND previous_link.revision_no=NEW.parent_revision_no AND NOT EXISTS(
 SELECT 1 FROM inventory_reservation_releases r WHERE r.reservation_id=previous_link.reservation_id)
 AND NOT EXISTS(SELECT 1 FROM plan_revision_reservations n WHERE n.plan_id=NEW.plan_id
 AND n.revision_no=NEW.revision_no AND n.reservation_id=previous_link.reservation_id)) THEN
 RAISE EXCEPTION 'revision must release or retain all prior plan reservations' USING ERRCODE='23514';END IF;
 IF EXISTS(SELECT 1 FROM plan_reservation_intents i WHERE i.proposal_id=NEW.proposal_id
 AND NOT EXISTS(SELECT 1 FROM plan_revision_reservations r WHERE r.plan_id=NEW.plan_id
 AND r.revision_no=NEW.revision_no AND r.intent_node_id=i.node_id)) OR EXISTS(
 SELECT 1 FROM plan_revision_reservations r WHERE r.plan_id=NEW.plan_id AND r.revision_no=NEW.revision_no
 AND NOT EXISTS(SELECT 1 FROM plan_reservation_intents i WHERE i.proposal_id=NEW.proposal_id AND i.node_id=r.intent_node_id)) THEN
 RAISE EXCEPTION 'incomplete atomic revision reservation effects' USING ERRCODE='23514';END IF;
 RETURN NULL;
END $$;
CREATE FUNCTION menuto_plan_materialization() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE r plan_revisions%ROWTYPE;m inventory_movements%ROWTYPE;l inventory_lots%ROWTYPE;
BEGIN
 PERFORM pg_advisory_xact_lock(hashtextextended('inventory.household:'||NEW.household_id::text,0));
 PERFORM 1 FROM plan_workspaces WHERE id=NEW.plan_id AND household_id=NEW.household_id FOR UPDATE;
 PERFORM menuto_plan_actor(NEW.household_id,NEW.actor_user_id);
 SELECT * INTO r FROM plan_revisions WHERE plan_id=NEW.plan_id AND household_id=NEW.household_id
 AND revision_no=NEW.source_revision_no;
 IF NOT FOUND OR r.proposal_id<>NEW.proposal_id THEN
 RAISE EXCEPTION 'materialization source revision mismatch' USING ERRCODE='23514';END IF;
 SELECT * INTO m FROM inventory_movements WHERE id=NEW.movement_id AND household_id=NEW.household_id AND lot_id=NEW.lot_id;
 SELECT * INTO l FROM inventory_lots WHERE id=NEW.lot_id AND household_id=NEW.household_id;
 IF m.id IS NULL OR (NEW.meal_node_id IS NOT NULL AND m.movement_type<>'CONSUME')
 OR (NEW.batch_node_id IS NOT NULL AND (m.movement_type<>'ACQUIRE' OR l.asset_type='RAW_INGREDIENT'))
 OR (NEW.shopping_node_id IS NOT NULL AND (m.movement_type<>'ACQUIRE' OR NOT EXISTS(
 SELECT 1 FROM shopping_requirement_intents s WHERE s.proposal_id=NEW.proposal_id AND s.node_id=NEW.shopping_node_id
 AND s.ingredient_id=l.ingredient_id AND s.basis=m.basis AND s.item_ref IS NOT DISTINCT FROM m.item_ref))) THEN
 RAISE EXCEPTION 'materialization needs exact compatible confirmed inventory evidence' USING ERRCODE='23514';END IF;
 UPDATE plan_workspaces SET boundary_version=boundary_version+1 WHERE id=NEW.plan_id;
 NEW.created_at:=clock_timestamp();RETURN NEW;
END $$;

CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON plan_workspaces FOR EACH ROW EXECUTE FUNCTION menuto_plan_workspace_guard();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON plan_workspaces FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON plan_proposals FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON plan_proposals FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON plan_proposal_seals FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON plan_proposal_seals FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON plan_meal_intents FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON plan_meal_intents FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON plan_meal_participants FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON plan_meal_participants FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON plan_reservation_intents FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON plan_reservation_intents FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON plan_validation_authorizations FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON plan_validation_authorizations FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON plan_revisions FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON plan_revisions FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON plan_revision_reservations FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON plan_revision_reservations FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON plan_materialization_links FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON plan_materialization_links FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON planned_cooking_batches FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON planned_cooking_batches FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON planned_batch_allocations FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON planned_batch_allocations FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_guard BEFORE UPDATE OR DELETE ON shopping_requirement_intents FOR EACH ROW EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_truncate BEFORE TRUNCATE ON shopping_requirement_intents FOR EACH STATEMENT EXECUTE FUNCTION menuto_plan_immutable();
CREATE TRIGGER plan_child BEFORE INSERT ON plan_meal_intents FOR EACH ROW EXECUTE FUNCTION menuto_plan_child_insert();
CREATE TRIGGER plan_child BEFORE INSERT ON plan_meal_participants FOR EACH ROW EXECUTE FUNCTION menuto_plan_child_insert();
CREATE TRIGGER plan_child BEFORE INSERT ON planned_cooking_batches FOR EACH ROW EXECUTE FUNCTION menuto_plan_child_insert();
CREATE TRIGGER plan_child BEFORE INSERT ON planned_batch_allocations FOR EACH ROW EXECUTE FUNCTION menuto_plan_child_insert();
CREATE TRIGGER plan_child BEFORE INSERT ON shopping_requirement_intents FOR EACH ROW EXECUTE FUNCTION menuto_plan_child_insert();
CREATE TRIGGER plan_child BEFORE INSERT ON plan_reservation_intents FOR EACH ROW EXECUTE FUNCTION menuto_plan_child_insert();
CREATE TRIGGER plan_insert BEFORE INSERT ON plan_workspaces FOR EACH ROW EXECUTE FUNCTION menuto_plan_begin_workspace();
CREATE TRIGGER plan_insert BEFORE INSERT ON plan_proposals FOR EACH ROW EXECUTE FUNCTION menuto_plan_begin_proposal();
CREATE TRIGGER plan_insert BEFORE INSERT ON plan_proposal_seals FOR EACH ROW EXECUTE FUNCTION menuto_plan_seal();
CREATE TRIGGER plan_insert BEFORE INSERT ON plan_validation_authorizations FOR EACH ROW EXECUTE FUNCTION menuto_plan_no_authority();
CREATE TRIGGER plan_insert BEFORE INSERT ON plan_revisions FOR EACH ROW EXECUTE FUNCTION menuto_plan_revision();
CREATE TRIGGER plan_insert BEFORE INSERT ON plan_revision_reservations FOR EACH ROW EXECUTE FUNCTION menuto_plan_revision_reservation();
CREATE TRIGGER plan_insert BEFORE INSERT ON plan_materialization_links FOR EACH ROW EXECUTE FUNCTION menuto_plan_materialization();
CREATE CONSTRAINT TRIGGER plan_revision_complete AFTER INSERT ON plan_revisions DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_plan_revision_complete();
'''
DOWNGRADE_SQL=r'''
LOCK TABLE plan_workspaces,plan_proposals,plan_proposal_seals,plan_meal_intents,plan_meal_participants,plan_reservation_intents,plan_validation_authorizations,plan_revisions,plan_revision_reservations,plan_materialization_links,planned_cooking_batches,planned_batch_allocations,shopping_requirement_intents IN ACCESS EXCLUSIVE MODE;
DO $$ BEGIN
IF EXISTS(SELECT 1 FROM plan_workspaces) OR EXISTS(SELECT 1 FROM plan_proposals) OR EXISTS(SELECT 1 FROM plan_proposal_seals) OR EXISTS(SELECT 1 FROM plan_meal_intents) OR EXISTS(SELECT 1 FROM plan_meal_participants) OR EXISTS(SELECT 1 FROM plan_reservation_intents) OR EXISTS(SELECT 1 FROM plan_validation_authorizations) OR EXISTS(SELECT 1 FROM plan_revisions) OR EXISTS(SELECT 1 FROM plan_revision_reservations) OR EXISTS(SELECT 1 FROM plan_materialization_links) OR EXISTS(SELECT 1 FROM planned_cooking_batches) OR EXISTS(SELECT 1 FROM planned_batch_allocations) OR EXISTS(SELECT 1 FROM shopping_requirement_intents) THEN RAISE EXCEPTION '0008 downgrade would lose intent/revision history' USING ERRCODE='23514';END IF;END $$;
ALTER TABLE plan_workspaces DROP CONSTRAINT fk_plan_workspaces_household_id_household_members;
ALTER TABLE plan_workspaces DROP CONSTRAINT fk_plan_workspaces_household_id_households;
ALTER TABLE plan_workspaces DROP CONSTRAINT fk_plan_workspaces_household_id_memberships;
ALTER TABLE plan_workspaces DROP CONSTRAINT fk_plan_workspaces_id_plan_revisions;
ALTER TABLE plan_proposals DROP CONSTRAINT fk_plan_proposal_requires_seal;
ALTER TABLE plan_proposals DROP CONSTRAINT fk_plan_proposals_household_id_memberships;
ALTER TABLE plan_proposals DROP CONSTRAINT fk_plan_proposals_plan_id_plan_workspaces;
ALTER TABLE plan_proposal_seals DROP CONSTRAINT fk_plan_proposal_seals_proposal_id_plan_proposals;
ALTER TABLE plan_meal_intents DROP CONSTRAINT fk_plan_meal_intents_proposal_id_plan_proposals;
ALTER TABLE plan_meal_participants DROP CONSTRAINT fk_plan_meal_participants_household_id_household_members;
ALTER TABLE plan_meal_participants DROP CONSTRAINT fk_plan_meal_participants_proposal_id_plan_meal_intents;
ALTER TABLE plan_meal_participants DROP CONSTRAINT fk_plan_meal_participants_proposal_id_plan_proposals;
ALTER TABLE plan_reservation_intents DROP CONSTRAINT fk_plan_reservation_intents_household_id_inventory_lots;
ALTER TABLE plan_reservation_intents DROP CONSTRAINT fk_plan_reservation_intents_proposal_id_plan_meal_intents;
ALTER TABLE plan_reservation_intents DROP CONSTRAINT fk_plan_reservation_intents_proposal_id_plan_proposals;
ALTER TABLE plan_reservation_intents DROP CONSTRAINT fk_plan_reservation_intents_proposal_id_planned_cooking_batches;
ALTER TABLE plan_validation_authorizations DROP CONSTRAINT fk_plan_validation_authorizations_proposal_id_plan_proposals;
ALTER TABLE plan_revisions DROP CONSTRAINT fk_plan_revisions_authorization_id_plan_validation_auth_6c78;
ALTER TABLE plan_revisions DROP CONSTRAINT fk_plan_revisions_household_id_memberships;
ALTER TABLE plan_revisions DROP CONSTRAINT fk_plan_revisions_plan_id_plan_revisions;
ALTER TABLE plan_revisions DROP CONSTRAINT fk_plan_revisions_proposal_id_plan_proposals;
ALTER TABLE plan_revision_reservations DROP CONSTRAINT fk_plan_revision_reservations_household_id_inventory_re_a837;
ALTER TABLE plan_revision_reservations DROP CONSTRAINT fk_plan_revision_reservations_plan_id_plan_revisions;
ALTER TABLE plan_revision_reservations DROP CONSTRAINT fk_plan_revision_reservations_proposal_id_plan_proposals;
ALTER TABLE plan_revision_reservations DROP CONSTRAINT fk_plan_revision_reservations_proposal_id_plan_reservat_00c6;
ALTER TABLE plan_materialization_links DROP CONSTRAINT fk_plan_materialization_links_household_id_inventory_movements;
ALTER TABLE plan_materialization_links DROP CONSTRAINT fk_plan_materialization_links_household_id_memberships;
ALTER TABLE plan_materialization_links DROP CONSTRAINT fk_plan_materialization_links_plan_id_plan_revisions;
ALTER TABLE plan_materialization_links DROP CONSTRAINT fk_plan_materialization_links_proposal_id_plan_meal_intents;
ALTER TABLE plan_materialization_links DROP CONSTRAINT fk_plan_materialization_links_proposal_id_plan_proposals;
ALTER TABLE plan_materialization_links DROP CONSTRAINT fk_plan_materialization_links_proposal_id_planned_cooki_37ab;
ALTER TABLE plan_materialization_links DROP CONSTRAINT fk_plan_materialization_links_proposal_id_shopping_requ_f4d2;
ALTER TABLE planned_cooking_batches DROP CONSTRAINT fk_planned_cooking_batches_proposal_id_plan_proposals;
ALTER TABLE planned_cooking_batches DROP CONSTRAINT fk_planned_cooking_batches_recipe_version_id_recipe_versions;
ALTER TABLE planned_cooking_batches DROP CONSTRAINT fk_planned_cooking_batches_tier_id_recipe_portion_tiers;
ALTER TABLE planned_batch_allocations DROP CONSTRAINT fk_planned_batch_allocations_proposal_id_plan_meal_intents;
ALTER TABLE planned_batch_allocations DROP CONSTRAINT fk_planned_batch_allocations_proposal_id_plan_proposals;
ALTER TABLE planned_batch_allocations DROP CONSTRAINT fk_planned_batch_allocations_proposal_id_planned_cookin_ca12;
ALTER TABLE shopping_requirement_intents DROP CONSTRAINT fk_shopping_requirement_intents_ingredient_id_ingredients;
ALTER TABLE shopping_requirement_intents DROP CONSTRAINT fk_shopping_requirement_intents_proposal_id_plan_proposals;
DROP TABLE shopping_requirement_intents;
DROP TABLE planned_batch_allocations;
DROP TABLE planned_cooking_batches;
DROP TABLE plan_materialization_links;
DROP TABLE plan_revision_reservations;
DROP TABLE plan_revisions;
DROP TABLE plan_validation_authorizations;
DROP TABLE plan_reservation_intents;
DROP TABLE plan_meal_participants;
DROP TABLE plan_meal_intents;
DROP TABLE plan_proposal_seals;
DROP TABLE plan_proposals;
DROP TABLE plan_workspaces;
DROP FUNCTION menuto_plan_reservation_target(uuid,uuid);
DROP FUNCTION menuto_plan_revision_complete();
DROP FUNCTION menuto_plan_materialization();
DROP FUNCTION menuto_plan_revision_reservation();
DROP FUNCTION menuto_plan_revision();
DROP FUNCTION menuto_plan_seal();
DROP FUNCTION menuto_plan_check(uuid);
DROP FUNCTION menuto_plan_meal_path(uuid,uuid);
DROP FUNCTION menuto_plan_inventory_frontier(uuid);
DROP FUNCTION menuto_plan_canonical(jsonb);
DROP FUNCTION menuto_plan_child_insert();
DROP FUNCTION menuto_plan_begin_proposal();
DROP FUNCTION menuto_plan_begin_workspace();
DROP FUNCTION menuto_plan_actor(uuid,uuid);
DROP FUNCTION menuto_plan_workspace_guard();
DROP FUNCTION menuto_plan_no_authority();
DROP FUNCTION menuto_plan_immutable();
DROP FUNCTION menuto_plan_graph(uuid);
'''
def upgrade():
    op.execute(UPGRADE_SQL)
def downgrade():
    op.execute(DOWNGRADE_SQL)
