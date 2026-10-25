"""Reviewed culinary assignment companions. Frozen PostgreSQL DDL, no ORM imports."""
# ruff: noqa: E501
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

UPGRADE_SQL = r'''

CREATE TABLE culinary_feature_frontier (
	source VARCHAR(20) NOT NULL,
	generation BIGINT NOT NULL,
	CONSTRAINT pk_culinary_feature_frontier PRIMARY KEY (source),
	CONSTRAINT ck_culinary_feature_frontier_singleton CHECK (source='RECIPES' AND generation>=0)
)

;

CREATE TABLE ingredient_protein_frontier (
	source VARCHAR(20) NOT NULL,
	generation BIGINT NOT NULL,
	CONSTRAINT pk_ingredient_protein_frontier PRIMARY KEY (source),
	CONSTRAINT ck_ingredient_protein_frontier_singleton CHECK (source='CATALOG' AND generation>=0)
)

;

CREATE TABLE ingredient_protein_streams (
	id UUID NOT NULL,
	ingredient_id UUID NOT NULL,
	head_revision_no INTEGER DEFAULT -1 NOT NULL,
	head_review_id UUID,
	assembly_xid VARCHAR(30) NOT NULL,
	CONSTRAINT pk_ingredient_protein_streams PRIMARY KEY (id),
	CONSTRAINT uq_ingredient_protein_streams_ingredient_id UNIQUE (ingredient_id),
	CONSTRAINT uq_ingredient_protein_streams_id_ingredient_id UNIQUE (id, ingredient_id),
	CONSTRAINT ck_ingredient_protein_streams_head CHECK ((head_revision_no=-1 AND head_review_id IS NULL) OR (head_revision_no>=0 AND head_review_id IS NOT NULL)),
	CONSTRAINT fk_ingredient_protein_streams_ingredient_id_ingredients FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT
)

;

CREATE TABLE culinary_feature_applicabilities (
	id UUID NOT NULL,
	recipe_version_id UUID NOT NULL,
	dimension VARCHAR(20) NOT NULL,
	scope VARCHAR(30) NOT NULL,
	key_hash VARCHAR(64) NOT NULL,
	assembly_xid VARCHAR(30) NOT NULL,
	declared_tier_count INTEGER NOT NULL,
	head_revision_no INTEGER DEFAULT -1 NOT NULL,
	head_review_id UUID,
	CONSTRAINT pk_culinary_feature_applicabilities PRIMARY KEY (id),
	CONSTRAINT uq_culinary_feature_applicabilities_recipe_version_id_d_cd8e UNIQUE (recipe_version_id, dimension, key_hash),
	CONSTRAINT uq_culinary_feature_applicabilities_id_recipe_version_i_c23d UNIQUE (id, recipe_version_id, dimension),
	CONSTRAINT uq_culinary_feature_applicabilities_id_recipe_version_id UNIQUE (id, recipe_version_id),
	CONSTRAINT ck_culinary_feature_applicabilities_scope CHECK (dimension IN ('METHOD','FLAVOR','MAIN_PROTEIN') AND scope IN ('RECIPE_COOKING_CONTEXT','EXACT_PATH','REVIEWED_SCOPE') AND ((dimension='METHOD' AND scope='RECIPE_COOKING_CONTEXT' AND declared_tier_count=0) OR (dimension!='METHOD' AND scope!='RECIPE_COOKING_CONTEXT' AND declared_tier_count>0))),
	CONSTRAINT ck_culinary_feature_applicabilities_hash CHECK (key_hash ~ '^[a-f0-9]{64}$'),
	CONSTRAINT ck_culinary_feature_applicabilities_head CHECK ((head_revision_no=-1 AND head_review_id IS NULL) OR (head_revision_no>=0 AND head_review_id IS NOT NULL)),
	CONSTRAINT fk_culinary_feature_applicabilities_recipe_version_id_r_2f9d FOREIGN KEY(recipe_version_id) REFERENCES recipe_versions (id) ON DELETE RESTRICT
)

;

CREATE TABLE ingredient_protein_reviews (
	id UUID NOT NULL,
	revision_no INTEGER NOT NULL,
	predecessor_id UUID,
	predecessor_revision_no INTEGER,
	source_sequence BIGINT NOT NULL,
	action VARCHAR(20) NOT NULL,
	command_kind VARCHAR(20) NOT NULL,
	coverage VARCHAR(20),
	reviewer_user_id UUID NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	assembly_xid VARCHAR(30) NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	correction_reason VARCHAR(200),
	declared_covered_count INTEGER NOT NULL,
	declared_assigned_count INTEGER NOT NULL,
	source_kind VARCHAR(30) NOT NULL,
	source_system VARCHAR(100) NOT NULL,
	external_record_id VARCHAR(2048) NOT NULL,
	source_version VARCHAR(200) NOT NULL,
	source_uri VARCHAR(2048),
	content_hash VARCHAR(64),
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
	stream_id UUID NOT NULL,
	ingredient_id UUID NOT NULL,
	CONSTRAINT pk_ingredient_protein_reviews PRIMARY KEY (id),
	CONSTRAINT ck_ingredient_protein_reviews_source_kind CHECK (source_kind IN ('USER','REVIEWED_REFERENCE')),
	CONSTRAINT ck_ingredient_protein_reviews_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_ingredient_protein_reviews_source_identity CHECK (length(trim(external_record_id))>0 AND length(trim(source_version))>0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'),
	CONSTRAINT ck_ingredient_protein_reviews_time CHECK (isfinite(observed_at) AND isfinite(recorded_at) AND observed_at<=recorded_at),
	CONSTRAINT ck_ingredient_protein_reviews_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'),
	CONSTRAINT ck_ingredient_protein_reviews_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')),
	CONSTRAINT uq_ingredient_protein_reviews_source_system_external_re_c774 UNIQUE (source_system, external_record_id, source_version),
	CONSTRAINT uq_ingredient_protein_reviews_source_system_idempotency_key UNIQUE (source_system, idempotency_key),
	CONSTRAINT uq_ingredient_protein_reviews_source_sequence UNIQUE (source_sequence),
	CONSTRAINT ck_ingredient_protein_reviews_sequence CHECK (revision_no>=0 AND source_sequence>0),
	CONSTRAINT ck_ingredient_protein_reviews_predecessor CHECK ((revision_no=0 AND predecessor_id IS NULL AND predecessor_revision_no IS NULL AND action='REPLACE') OR (revision_no>0 AND predecessor_id IS NOT NULL AND predecessor_revision_no=revision_no-1 AND correction_reason IS NOT NULL AND length(trim(correction_reason))>0)),
	CONSTRAINT ck_ingredient_protein_reviews_shape CHECK (action IN ('REPLACE','RETRACT') AND ((action='REPLACE' AND coverage IS NOT NULL AND coverage IN ('PARTIAL','COMPLETE') AND declared_covered_count>0) OR (action='RETRACT' AND coverage IS NULL AND declared_covered_count=0 AND declared_assigned_count=0))),
	CONSTRAINT ck_ingredient_protein_reviews_counts CHECK (declared_assigned_count>=0 AND declared_assigned_count<=declared_covered_count),
	CONSTRAINT ck_ingredient_protein_reviews_command_identity CHECK (command_hash ~ '^[a-f0-9]{64}$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_ingredient_protein_reviews_command_kind CHECK (command_kind=action),
	CONSTRAINT uq_ingredient_protein_reviews_stream_id_revision_no UNIQUE (stream_id, revision_no),
	CONSTRAINT uq_ingredient_protein_reviews_id_stream_id_revision_no UNIQUE (id, stream_id, revision_no),
	CONSTRAINT uq_ingredient_protein_reviews_id_ingredient_id UNIQUE (id, ingredient_id),
	CONSTRAINT fk_ingredient_protein_reviews_stream_id_ingredient_prot_23e9 FOREIGN KEY(stream_id, ingredient_id) REFERENCES ingredient_protein_streams (id, ingredient_id) ON DELETE RESTRICT,
	CONSTRAINT fk_ingredient_protein_reviews_predecessor_id_ingredient_ac81 FOREIGN KEY(predecessor_id, stream_id, predecessor_revision_no) REFERENCES ingredient_protein_reviews (id, stream_id, revision_no) ON DELETE RESTRICT,
	CONSTRAINT fk_ingredient_protein_reviews_reviewer_user_id_users FOREIGN KEY(reviewer_user_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

CREATE TABLE culinary_feature_applicability_tiers (
	applicability_id UUID NOT NULL,
	recipe_version_id UUID NOT NULL,
	tier_id UUID NOT NULL,
	CONSTRAINT pk_culinary_feature_applicability_tiers PRIMARY KEY (applicability_id, tier_id),
	CONSTRAINT fk_culinary_feature_applicability_tiers_applicability_i_9643 FOREIGN KEY(applicability_id, recipe_version_id) REFERENCES culinary_feature_applicabilities (id, recipe_version_id) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_feature_applicability_tiers_tier_id_recipe__b82a FOREIGN KEY(tier_id, recipe_version_id) REFERENCES recipe_portion_tiers (id, recipe_version_id) ON DELETE RESTRICT
)

;

CREATE TABLE culinary_feature_reviews (
	id UUID NOT NULL,
	revision_no INTEGER NOT NULL,
	predecessor_id UUID,
	predecessor_revision_no INTEGER,
	source_sequence BIGINT NOT NULL,
	action VARCHAR(20) NOT NULL,
	command_kind VARCHAR(20) NOT NULL,
	coverage VARCHAR(20),
	reviewer_user_id UUID NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	assembly_xid VARCHAR(30) NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	correction_reason VARCHAR(200),
	declared_covered_count INTEGER NOT NULL,
	declared_assigned_count INTEGER NOT NULL,
	source_kind VARCHAR(30) NOT NULL,
	source_system VARCHAR(100) NOT NULL,
	external_record_id VARCHAR(2048) NOT NULL,
	source_version VARCHAR(200) NOT NULL,
	source_uri VARCHAR(2048),
	content_hash VARCHAR(64),
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
	applicability_id UUID NOT NULL,
	recipe_version_id UUID NOT NULL,
	dimension VARCHAR(20) NOT NULL,
	declared_support_count INTEGER NOT NULL,
	catalog_frontier_at_write BIGINT,
	CONSTRAINT pk_culinary_feature_reviews PRIMARY KEY (id),
	CONSTRAINT ck_culinary_feature_reviews_source_kind CHECK (source_kind IN ('USER','REVIEWED_REFERENCE')),
	CONSTRAINT ck_culinary_feature_reviews_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_culinary_feature_reviews_source_identity CHECK (length(trim(external_record_id))>0 AND length(trim(source_version))>0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'),
	CONSTRAINT ck_culinary_feature_reviews_time CHECK (isfinite(observed_at) AND isfinite(recorded_at) AND observed_at<=recorded_at),
	CONSTRAINT ck_culinary_feature_reviews_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'),
	CONSTRAINT ck_culinary_feature_reviews_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')),
	CONSTRAINT uq_culinary_feature_reviews_source_system_external_reco_9f00 UNIQUE (source_system, external_record_id, source_version),
	CONSTRAINT uq_culinary_feature_reviews_source_system_idempotency_key UNIQUE (source_system, idempotency_key),
	CONSTRAINT uq_culinary_feature_reviews_source_sequence UNIQUE (source_sequence),
	CONSTRAINT ck_culinary_feature_reviews_sequence CHECK (revision_no>=0 AND source_sequence>0),
	CONSTRAINT ck_culinary_feature_reviews_predecessor CHECK ((revision_no=0 AND predecessor_id IS NULL AND predecessor_revision_no IS NULL AND action='REPLACE') OR (revision_no>0 AND predecessor_id IS NOT NULL AND predecessor_revision_no=revision_no-1 AND correction_reason IS NOT NULL AND length(trim(correction_reason))>0)),
	CONSTRAINT ck_culinary_feature_reviews_shape CHECK (action IN ('REPLACE','RETRACT') AND ((action='REPLACE' AND coverage IS NOT NULL AND coverage IN ('PARTIAL','COMPLETE') AND declared_covered_count>0) OR (action='RETRACT' AND coverage IS NULL AND declared_covered_count=0 AND declared_assigned_count=0))),
	CONSTRAINT ck_culinary_feature_reviews_counts CHECK (declared_assigned_count>=0 AND declared_assigned_count<=declared_covered_count),
	CONSTRAINT ck_culinary_feature_reviews_command_identity CHECK (command_hash ~ '^[a-f0-9]{64}$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_culinary_feature_reviews_command_kind CHECK ((revision_no=0 AND command_kind='REGISTER' AND action='REPLACE') OR (revision_no>0 AND command_kind=action)),
	CONSTRAINT ck_culinary_feature_reviews_dependency CHECK (declared_support_count>=0 AND ((dimension='MAIN_PROTEIN' AND catalog_frontier_at_write IS NOT NULL AND catalog_frontier_at_write>=0) OR (dimension IN ('METHOD','FLAVOR') AND catalog_frontier_at_write IS NULL AND declared_support_count=0)) AND (action!='RETRACT' OR declared_support_count=0)),
	CONSTRAINT uq_culinary_feature_reviews_applicability_id_revision_no UNIQUE (applicability_id, revision_no),
	CONSTRAINT uq_culinary_feature_reviews_id_applicability_id_revision_no UNIQUE (id, applicability_id, revision_no),
	CONSTRAINT uq_culinary_feature_reviews_id_applicability_id_recipe__772f UNIQUE (id, applicability_id, recipe_version_id, dimension),
	CONSTRAINT fk_culinary_feature_reviews_applicability_id_culinary_f_3428 FOREIGN KEY(applicability_id, recipe_version_id, dimension) REFERENCES culinary_feature_applicabilities (id, recipe_version_id, dimension) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_feature_reviews_predecessor_id_culinary_fea_57a4 FOREIGN KEY(predecessor_id, applicability_id, predecessor_revision_no) REFERENCES culinary_feature_reviews (id, applicability_id, revision_no) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_feature_reviews_reviewer_user_id_users FOREIGN KEY(reviewer_user_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

CREATE TABLE ingredient_protein_review_terms (
	review_id UUID NOT NULL,
	ingredient_id UUID NOT NULL,
	term_id UUID NOT NULL,
	term_kind VARCHAR(20) NOT NULL,
	CONSTRAINT pk_ingredient_protein_review_terms PRIMARY KEY (review_id, term_id),
	CONSTRAINT ck_ingredient_protein_review_terms_kind CHECK (term_kind='PROTEIN'),
	CONSTRAINT uq_ingredient_protein_review_terms_review_id_ingredient_4d34 UNIQUE (review_id, ingredient_id, term_id),
	CONSTRAINT fk_ingredient_protein_review_terms_review_id_ingredient_231d FOREIGN KEY(review_id, ingredient_id) REFERENCES ingredient_protein_reviews (id, ingredient_id) ON DELETE RESTRICT,
	CONSTRAINT fk_ingredient_protein_review_terms_term_id_affinity_fea_4ef9 FOREIGN KEY(term_id, term_kind) REFERENCES affinity_feature_terms (id, kind) ON DELETE RESTRICT
)

;

CREATE TABLE culinary_feature_applicability_slots (
	applicability_id UUID NOT NULL,
	recipe_version_id UUID NOT NULL,
	requirement_id UUID NOT NULL,
	choice VARCHAR(30) NOT NULL,
	selected_rule_id UUID,
	preparation VARCHAR(30) NOT NULL,
	transformation_id UUID,
	adjustment VARCHAR(30) NOT NULL,
	CONSTRAINT pk_culinary_feature_applicability_slots PRIMARY KEY (applicability_id, requirement_id),
	CONSTRAINT uq_culinary_feature_applicability_slots_applicability_i_9c7d UNIQUE (applicability_id, recipe_version_id, requirement_id),
	CONSTRAINT fk_culinary_feature_applicability_slots_applicability_i_8c6f FOREIGN KEY(applicability_id, recipe_version_id) REFERENCES culinary_feature_applicabilities (id, recipe_version_id) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_feature_applicability_slots_requirement_id__d886 FOREIGN KEY(requirement_id, recipe_version_id) REFERENCES recipe_ingredients (id, recipe_version_id) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_feature_applicability_slots_selected_rule_i_1e8b FOREIGN KEY(selected_rule_id, recipe_version_id) REFERENCES recipe_variant_rules (id, recipe_version_id) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_feature_applicability_slots_transformation__8d4f FOREIGN KEY(transformation_id, recipe_version_id) REFERENCES preparation_transformations (id, recipe_version_id) ON DELETE RESTRICT,
	CONSTRAINT ck_culinary_feature_applicability_slots_choice CHECK (choice IN ('BASE','RULE','ANY_AUTHORED_CHOICE') AND ((choice='RULE' AND selected_rule_id IS NOT NULL) OR (choice!='RULE' AND selected_rule_id IS NULL))),
	CONSTRAINT ck_culinary_feature_applicability_slots_preparation CHECK (preparation IN ('NONE','TRANSFORMATION','ANY_AUTHORED_PATH_CONTEXT') AND ((preparation='TRANSFORMATION' AND transformation_id IS NOT NULL) OR (preparation!='TRANSFORMATION' AND transformation_id IS NULL))),
	CONSTRAINT ck_culinary_feature_applicability_slots_adjustment CHECK (adjustment IN ('ZERO_ONLY','AUTHORED_ENVELOPE'))
)

;

CREATE TABLE culinary_feature_review_terms (
	review_id UUID NOT NULL,
	applicability_id UUID NOT NULL,
	recipe_version_id UUID NOT NULL,
	dimension VARCHAR(20) NOT NULL,
	term_id UUID NOT NULL,
	term_kind VARCHAR(20) NOT NULL,
	CONSTRAINT pk_culinary_feature_review_terms PRIMARY KEY (review_id, term_id),
	CONSTRAINT uq_culinary_feature_review_terms_review_id_applicabilit_e295 UNIQUE (review_id, applicability_id, recipe_version_id, dimension, term_id),
	CONSTRAINT fk_culinary_feature_review_terms_review_id_culinary_fea_563e FOREIGN KEY(review_id, applicability_id, recipe_version_id, dimension) REFERENCES culinary_feature_reviews (id, applicability_id, recipe_version_id, dimension) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_feature_review_terms_term_id_affinity_feature_terms FOREIGN KEY(term_id, term_kind) REFERENCES affinity_feature_terms (id, kind) ON DELETE RESTRICT,
	CONSTRAINT ck_culinary_feature_review_terms_kind CHECK ((dimension='MAIN_PROTEIN' AND term_kind='PROTEIN') OR (dimension IN ('METHOD','FLAVOR') AND term_kind=dimension))
)

;

CREATE TABLE ingredient_protein_assignments (
	review_id UUID NOT NULL,
	ingredient_id UUID NOT NULL,
	term_id UUID NOT NULL,
	term_kind VARCHAR(20) NOT NULL,
	CONSTRAINT pk_ingredient_protein_assignments PRIMARY KEY (review_id, term_id),
	CONSTRAINT ck_ingredient_protein_assignments_kind CHECK (term_kind='PROTEIN'),
	CONSTRAINT uq_ingredient_protein_assignments_review_id_ingredient__6a3c UNIQUE (review_id, ingredient_id, term_id),
	CONSTRAINT fk_ingredient_protein_assignments_review_id_ingredient__7ebc FOREIGN KEY(review_id, ingredient_id, term_id) REFERENCES ingredient_protein_review_terms (review_id, ingredient_id, term_id) ON DELETE RESTRICT
)

;

CREATE TABLE culinary_feature_assignments (
	review_id UUID NOT NULL,
	applicability_id UUID NOT NULL,
	recipe_version_id UUID NOT NULL,
	dimension VARCHAR(20) NOT NULL,
	term_id UUID NOT NULL,
	term_kind VARCHAR(20) NOT NULL,
	CONSTRAINT pk_culinary_feature_assignments PRIMARY KEY (review_id, term_id),
	CONSTRAINT uq_culinary_feature_assignments_review_id_applicability_16b4 UNIQUE (review_id, applicability_id, recipe_version_id, dimension, term_id),
	CONSTRAINT fk_culinary_feature_assignments_review_id_culinary_feat_04a7 FOREIGN KEY(review_id, applicability_id, recipe_version_id, dimension, term_id) REFERENCES culinary_feature_review_terms (review_id, applicability_id, recipe_version_id, dimension, term_id) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_feature_assignments_term_id_affinity_feature_terms FOREIGN KEY(term_id, term_kind) REFERENCES affinity_feature_terms (id, kind) ON DELETE RESTRICT,
	CONSTRAINT ck_culinary_feature_assignments_kind CHECK ((dimension='MAIN_PROTEIN' AND term_kind='PROTEIN') OR (dimension IN ('METHOD','FLAVOR') AND term_kind=dimension))
)

;

CREATE TABLE culinary_feature_main_protein_support (
	review_id UUID NOT NULL,
	applicability_id UUID NOT NULL,
	recipe_version_id UUID NOT NULL,
	dimension VARCHAR(20) NOT NULL,
	term_id UUID NOT NULL,
	requirement_id UUID NOT NULL,
	ingredient_id UUID NOT NULL,
	catalog_review_id UUID NOT NULL,
	CONSTRAINT pk_culinary_feature_main_protein_support PRIMARY KEY (review_id, term_id, requirement_id),
	CONSTRAINT ck_culinary_feature_main_protein_support_dimension CHECK (dimension='MAIN_PROTEIN'),
	CONSTRAINT fk_culinary_feature_main_protein_support_review_id_culi_3bd0 FOREIGN KEY(review_id, applicability_id, recipe_version_id, dimension, term_id) REFERENCES culinary_feature_assignments (review_id, applicability_id, recipe_version_id, dimension, term_id) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_feature_main_protein_support_applicability__f2ab FOREIGN KEY(applicability_id, recipe_version_id, requirement_id) REFERENCES culinary_feature_applicability_slots (applicability_id, recipe_version_id, requirement_id) ON DELETE RESTRICT,
	CONSTRAINT fk_culinary_feature_main_protein_support_catalog_review_7da8 FOREIGN KEY(catalog_review_id, ingredient_id, term_id) REFERENCES ingredient_protein_assignments (review_id, ingredient_id, term_id) ON DELETE RESTRICT
)

;
ALTER TABLE ingredient_protein_streams ADD CONSTRAINT fk_ingredient_protein_reviews_head FOREIGN KEY(head_review_id, id, head_revision_no) REFERENCES ingredient_protein_reviews (id, stream_id, revision_no) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
CREATE UNIQUE INDEX uq_culinary_method_context ON culinary_feature_applicabilities (recipe_version_id) WHERE dimension='METHOD';
ALTER TABLE culinary_feature_applicabilities ADD CONSTRAINT fk_culinary_feature_reviews_head FOREIGN KEY(head_review_id, id, head_revision_no) REFERENCES culinary_feature_reviews (id, applicability_id, revision_no) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
INSERT INTO ingredient_protein_frontier VALUES ('CATALOG',0);
INSERT INTO culinary_feature_frontier VALUES ('RECIPES',0);
CREATE FUNCTION menuto_feature_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Immutable culinary feature source' USING ERRCODE='23514'; END $$;

CREATE FUNCTION menuto_feature_canonical(j jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE STRICT AS $$
DECLARE result text;
BEGIN
 CASE jsonb_typeof(j)
 WHEN 'object' THEN SELECT '{'||coalesce(string_agg(to_json(k)::text||':'||menuto_feature_canonical(v),',' ORDER BY k COLLATE "C"),'')||'}' INTO result FROM jsonb_each(j) e(k,v);
 WHEN 'array' THEN SELECT '['||coalesce(string_agg(menuto_feature_canonical(v),',' ORDER BY n),'')||']' INTO result FROM jsonb_array_elements(j) WITH ORDINALITY e(v,n);
 ELSE result:=j::text;
 END CASE; RETURN result;
END $$;

CREATE FUNCTION menuto_feature_key(aid uuid) RETURNS jsonb LANGUAGE plpgsql STABLE AS $$
DECLARE a record; result jsonb;
BEGIN
 SELECT * INTO STRICT a FROM culinary_feature_applicabilities WHERE id=aid;
 result:=jsonb_build_object('contract_version','culinary-feature-applicability.v1',
   'recipe_version_id',a.recipe_version_id,'dimension',a.dimension,'scope',a.scope);
 IF a.dimension<>'METHOD' THEN
  result:=result||jsonb_build_object('tier_ids',(SELECT coalesce(jsonb_agg(tier_id ORDER BY tier_id),'[]') FROM culinary_feature_applicability_tiers WHERE applicability_id=aid),
   'slots',(SELECT coalesce(jsonb_agg(jsonb_build_object('requirement_id',requirement_id,
     'choice',choice,'selected_rule_id',selected_rule_id,'preparation',preparation,
     'transformation_id',transformation_id,'adjustment',adjustment) ORDER BY requirement_id),'[]') FROM culinary_feature_applicability_slots WHERE applicability_id=aid));
 END IF; RETURN result;
END $$;

CREATE FUNCTION menuto_feature_key_hash(aid uuid) RETURNS text LANGUAGE plpgsql STABLE AS $$
DECLARE a record; b text; v text;
BEGIN
 SELECT * INTO STRICT a FROM culinary_feature_applicabilities WHERE id=aid;
 b:=E'menuto.culinary-feature-key.v1\nversion='||a.recipe_version_id||E'\ndimension='||a.dimension||E'\nscope='||a.scope||E'\n';
 IF a.dimension<>'METHOD' THEN
  SELECT string_agg(tier_id::text,',' ORDER BY tier_id) INTO v FROM culinary_feature_applicability_tiers WHERE applicability_id=aid;
  b:=b||'tiers='||coalesce(v,'')||E'\n';
  SELECT string_agg('slot='||requirement_id||'|'||choice||'|'||coalesce(selected_rule_id::text,'-')||'|'||preparation||'|'||coalesce(transformation_id::text,'-')||'|'||adjustment||E'\n','' ORDER BY requirement_id) INTO v FROM culinary_feature_applicability_slots WHERE applicability_id=aid;
  b:=b||coalesce(v,'');
 END IF;
 RETURN encode(sha256(convert_to(b,'UTF8')),'hex');
END $$;

CREATE FUNCTION menuto_feature_options(aid uuid,rid uuid)
RETURNS TABLE(rule_id uuid,ingredient_id uuid,transformation_id uuid,structural boolean,factor numeric)
LANGUAGE sql STABLE AS $$
 WITH choices AS (
 SELECT NULL::uuid AS rule_id,i.ingredient_id,false AS structural,1::numeric AS factor
 FROM recipe_ingredients i JOIN culinary_feature_applicability_slots s ON s.requirement_id=i.id
 WHERE s.applicability_id=aid AND i.id=rid AND s.choice IN ('BASE','ANY_AUTHORED_CHOICE')
 UNION ALL
 SELECT r.id,r.replacement_ingredient_id,r.structural,r.quantity_factor
 FROM recipe_variant_rules r JOIN culinary_feature_applicability_slots s ON s.requirement_id=r.requirement_id
 JOIN recipe_ingredients i ON i.id=r.requirement_id
 WHERE s.applicability_id=aid AND r.requirement_id=rid AND i.basis<>'COUNT'
 AND (s.choice='ANY_AUTHORED_CHOICE' OR (s.choice='RULE' AND s.selected_rule_id=r.id))
 )
 SELECT c.rule_id,c.ingredient_id,t.id,c.structural,c.factor FROM choices c
 JOIN culinary_feature_applicability_slots s ON s.applicability_id=aid AND s.requirement_id=rid
 JOIN recipe_ingredients i ON i.id=rid
 LEFT JOIN preparation_transformations t ON t.requirement_id=rid AND t.ingredient_id=c.ingredient_id
 WHERE (s.preparation='ANY_AUTHORED_PATH_CONTEXT' OR (s.preparation='NONE' AND t.id IS NULL)
   OR (s.preparation='TRANSFORMATION' AND t.id=s.transformation_id))
 AND (t.id IS NOT NULL OR NOT EXISTS (SELECT 1 FROM preparation_transformations b WHERE b.requirement_id=rid AND b.ingredient_id=i.ingredient_id));
$$;

CREATE FUNCTION menuto_feature_fence() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP<>'UPDATE' OR pg_trigger_depth()<>2 OR NEW.source<>OLD.source OR NEW.generation<>OLD.generation+1 THEN
  RAISE EXCEPTION 'Protected feature frontier' USING ERRCODE='23514';
 END IF; RETURN NEW;
END $$;

CREATE FUNCTION menuto_feature_registry() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE gen bigint;
BEGIN
 IF TG_OP='UPDATE' THEN
  IF pg_trigger_depth()<>2 OR NEW.head_revision_no<>OLD.head_revision_no+1 OR NEW.head_review_id IS NULL
   OR (to_jsonb(NEW)-'head_revision_no'-'head_review_id') IS DISTINCT FROM (to_jsonb(OLD)-'head_revision_no'-'head_review_id') THEN
   RAISE EXCEPTION 'Protected feature head/identity' USING ERRCODE='23514';
  END IF; RETURN NEW;
 ELSIF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Immutable registry' USING ERRCODE='23514'; END IF;
 IF current_setting('transaction_isolation')<>'read committed' THEN RAISE EXCEPTION 'Feature writes require READ COMMITTED' USING ERRCODE='23514'; END IF;
 IF NEW.assembly_xid IS NOT NULL OR NEW.head_revision_no<>-1 OR NEW.head_review_id IS NOT NULL THEN
  RAISE EXCEPTION 'Database-owned registry assembly/head' USING ERRCODE='23514'; END IF;
 IF TG_TABLE_NAME='ingredient_protein_streams' THEN
  SELECT generation INTO gen FROM ingredient_protein_frontier FOR UPDATE;
 ELSE
  IF NEW.dimension='MAIN_PROTEIN' THEN SELECT generation INTO gen FROM ingredient_protein_frontier FOR UPDATE; END IF;
  SELECT generation INTO gen FROM culinary_feature_frontier FOR UPDATE;
  IF NOT EXISTS (SELECT 1 FROM recipe_versions v JOIN recipe_version_seals z ON z.recipe_version_id=v.id WHERE v.id=NEW.recipe_version_id AND v.review_status='REVIEWED') THEN
   RAISE EXCEPTION 'Classification requires sealed reviewed recipe' USING ERRCODE='23514'; END IF;
 END IF;
 NEW.assembly_xid:=pg_current_xact_id()::text; RETURN NEW;
END $$;

CREATE FUNCTION menuto_feature_append() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE owner record; gen bigint; cat bigint; prior text;
BEGIN
 IF current_setting('transaction_isolation')<>'read committed' THEN RAISE EXCEPTION 'Feature writes require READ COMMITTED' USING ERRCODE='23514'; END IF;
 IF NEW.assembly_xid IS NOT NULL OR NEW.recorded_at IS NOT NULL THEN RAISE EXCEPTION 'Database-owned review audit' USING ERRCODE='23514'; END IF;
 IF TG_TABLE_NAME='ingredient_protein_reviews' THEN
  SELECT generation INTO gen FROM ingredient_protein_frontier FOR UPDATE;
  SELECT * INTO STRICT owner FROM ingredient_protein_streams WHERE id=NEW.stream_id FOR UPDATE;
  IF NEW.ingredient_id<>owner.ingredient_id THEN RAISE EXCEPTION 'Catalog owner mismatch' USING ERRCODE='23514'; END IF;
  IF NEW.predecessor_id IS NOT NULL THEN SELECT action INTO prior FROM ingredient_protein_reviews WHERE id=NEW.predecessor_id; END IF;
 ELSE
  IF NEW.dimension='MAIN_PROTEIN' THEN
   SELECT generation INTO cat FROM ingredient_protein_frontier FOR UPDATE;
   IF NEW.catalog_frontier_at_write IS DISTINCT FROM cat THEN RAISE EXCEPTION 'Stale Catalog frontier' USING ERRCODE='23514'; END IF;
  END IF;
  SELECT generation INTO gen FROM culinary_feature_frontier FOR UPDATE;
  SELECT * INTO STRICT owner FROM culinary_feature_applicabilities WHERE id=NEW.applicability_id FOR UPDATE;
  IF NEW.recipe_version_id<>owner.recipe_version_id OR NEW.dimension<>owner.dimension THEN RAISE EXCEPTION 'Recipe owner mismatch' USING ERRCODE='23514'; END IF;
  IF NEW.predecessor_id IS NOT NULL THEN SELECT action INTO prior FROM culinary_feature_reviews WHERE id=NEW.predecessor_id; END IF;
 END IF;
 IF NEW.source_sequence<>gen+1 OR NEW.revision_no<>owner.head_revision_no+1 OR NEW.predecessor_id IS DISTINCT FROM owner.head_review_id THEN
  RAISE EXCEPTION 'Stale source frontier/head/predecessor' USING ERRCODE='23514'; END IF;
 IF NEW.action='RETRACT' AND prior IS DISTINCT FROM 'REPLACE' THEN RAISE EXCEPTION 'Retraction requires active review' USING ERRCODE='23514'; END IF;
 NEW.assembly_xid:=pg_current_xact_id()::text; NEW.recorded_at:=clock_timestamp();
 IF TG_TABLE_NAME='ingredient_protein_reviews' THEN
  UPDATE ingredient_protein_frontier SET generation=gen+1;
  UPDATE ingredient_protein_streams SET head_revision_no=NEW.revision_no,head_review_id=NEW.id WHERE id=NEW.stream_id;
 ELSE
  UPDATE culinary_feature_frontier SET generation=gen+1;
  UPDATE culinary_feature_applicabilities SET head_revision_no=NEW.revision_no,head_review_id=NEW.id WHERE id=NEW.applicability_id;
 END IF; RETURN NEW;
END $$;

CREATE FUNCTION menuto_feature_child() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE p record; n integer; limit_n integer; t record;
BEGIN
 IF current_setting('transaction_isolation')<>'read committed' THEN RAISE EXCEPTION 'Feature writes require READ COMMITTED' USING ERRCODE='23514'; END IF;
 IF TG_TABLE_NAME LIKE 'culinary_feature_applicability_%' THEN
  SELECT * INTO STRICT p FROM culinary_feature_applicabilities WHERE id=NEW.applicability_id;
  IF p.dimension='METHOD' THEN RAISE EXCEPTION 'METHOD forbids path children' USING ERRCODE='23514'; END IF;
  IF TG_TABLE_NAME='culinary_feature_applicability_tiers' THEN limit_n:=p.declared_tier_count;
  ELSE SELECT count(*) INTO limit_n FROM recipe_ingredients WHERE recipe_version_id=p.recipe_version_id; END IF;
  EXECUTE format('SELECT count(*) FROM %I WHERE applicability_id=$1',TG_TABLE_NAME) INTO n USING p.id;
 ELSE
  IF TG_TABLE_NAME LIKE 'ingredient_protein_%' THEN
   SELECT * INTO STRICT p FROM ingredient_protein_reviews WHERE id=NEW.review_id;
  ELSE SELECT * INTO STRICT p FROM culinary_feature_reviews WHERE id=NEW.review_id; END IF;
  IF TG_TABLE_NAME LIKE '%review_terms' THEN limit_n:=p.declared_covered_count;
  ELSIF TG_TABLE_NAME LIKE '%assignments' THEN limit_n:=p.declared_assigned_count;
  ELSE limit_n:=p.declared_support_count; END IF;
  EXECUTE format('SELECT count(*) FROM %I WHERE review_id=$1',TG_TABLE_NAME) INTO n USING p.id;
  IF TG_TABLE_NAME LIKE '%review_terms' THEN
   SELECT * INTO STRICT t FROM affinity_feature_terms WHERE id=NEW.term_id;
   IF t.status<>'REVIEWED' OR t.observed_at>p.recorded_at THEN RAISE EXCEPTION 'Unreviewed/future term' USING ERRCODE='23514'; END IF;
  END IF;
 END IF;
 IF p.assembly_xid<>pg_current_xact_id()::text OR n>=limit_n THEN RAISE EXCEPTION 'Closed source assembly/child limit' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION menuto_feature_check_scope(aid uuid) RETURNS void LANGUAGE plpgsql AS $$
DECLARE a record; n integer; exact boolean; feasible boolean; other record;
BEGIN
 SELECT * INTO STRICT a FROM culinary_feature_applicabilities WHERE id=aid;
 IF a.head_revision_no<0 THEN RAISE EXCEPTION 'Empty feature registry' USING ERRCODE='23514'; END IF;
 IF a.key_hash<>menuto_feature_key_hash(aid) THEN RAISE EXCEPTION 'Applicability key hash mismatch' USING ERRCODE='23514'; END IF;
 IF (SELECT count(*) FROM culinary_feature_applicability_tiers WHERE applicability_id=aid)<>a.declared_tier_count THEN RAISE EXCEPTION 'Incomplete scope tiers' USING ERRCODE='23514'; END IF;
 SELECT count(*) INTO n FROM culinary_feature_applicability_slots WHERE applicability_id=aid;
 IF a.dimension='METHOD' THEN
  IF n<>0 THEN RAISE EXCEPTION 'METHOD has path children' USING ERRCODE='23514'; END IF;
  RETURN;
 END IF;
 IF n<>(SELECT count(*) FROM recipe_ingredients WHERE recipe_version_id=a.recipe_version_id) THEN RAISE EXCEPTION 'Incomplete scope slots' USING ERRCODE='23514'; END IF;
 SELECT a.declared_tier_count=1 AND bool_and(choice<>'ANY_AUTHORED_CHOICE' AND preparation<>'ANY_AUTHORED_PATH_CONTEXT' AND adjustment='ZERO_ONLY') INTO exact FROM culinary_feature_applicability_slots WHERE applicability_id=aid;
 IF (a.scope='EXACT_PATH')<>exact THEN RAISE EXCEPTION 'Scope exactness mismatch' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM culinary_feature_applicability_slots s WHERE s.applicability_id=aid AND NOT EXISTS (SELECT 1 FROM menuto_feature_options(aid,s.requirement_id))) THEN RAISE EXCEPTION 'Impossible authored slot path' USING ERRCODE='23514'; END IF;
 -- Minimize structural choices independently. At most one forced structural slot is legal.
 SELECT count(*)<=1 INTO feasible FROM culinary_feature_applicability_slots s WHERE s.applicability_id=aid AND NOT EXISTS (SELECT 1 FROM menuto_feature_options(aid,s.requirement_id) o WHERE NOT o.structural);
 IF NOT feasible THEN
  SELECT EXISTS (SELECT 1 FROM recipe_rule_combinations c WHERE c.recipe_version_id=a.recipe_version_id
   AND NOT EXISTS (SELECT 1 FROM culinary_feature_applicability_slots s WHERE s.applicability_id=aid AND NOT EXISTS (
     SELECT 1 FROM menuto_feature_options(aid,s.requirement_id) o WHERE
      (o.rule_id IS NULL AND NOT EXISTS (SELECT 1 FROM recipe_combination_members cm JOIN recipe_variant_rules r ON r.id=cm.rule_id WHERE cm.combination_id=c.id AND r.requirement_id=s.requirement_id))
      OR o.rule_id IN (SELECT rule_id FROM recipe_combination_members WHERE combination_id=c.id)))) INTO feasible;
 END IF;
 IF NOT feasible THEN RAISE EXCEPTION 'Scope has no approved structural path' USING ERRCODE='23514'; END IF;
 -- Conservative intersection; cannot choose a preferred overlapping source.
 IF (SELECT action FROM culinary_feature_reviews WHERE id=a.head_review_id)='REPLACE' THEN
  FOR other IN SELECT b.id FROM culinary_feature_applicabilities b JOIN culinary_feature_reviews h ON h.id=b.head_review_id
   WHERE b.id<>aid AND b.recipe_version_id=a.recipe_version_id AND b.dimension=a.dimension AND h.action='REPLACE'
  LOOP
   IF EXISTS (SELECT 1 FROM culinary_feature_applicability_tiers x JOIN culinary_feature_applicability_tiers y ON y.tier_id=x.tier_id WHERE x.applicability_id=aid AND y.applicability_id=other.id)
    AND NOT EXISTS (SELECT 1 FROM culinary_feature_applicability_slots s WHERE s.applicability_id=aid AND NOT EXISTS (
      SELECT 1 FROM menuto_feature_options(aid,s.requirement_id) x JOIN menuto_feature_options(other.id,s.requirement_id) y ON x.rule_id IS NOT DISTINCT FROM y.rule_id AND x.transformation_id IS NOT DISTINCT FROM y.transformation_id)) THEN
    RAISE EXCEPTION 'Overlapping active feature scopes' USING ERRCODE='23514';
   END IF;
  END LOOP;
 END IF;
END $$;

CREATE FUNCTION menuto_feature_review_command(rid uuid, catalog boolean) RETURNS jsonb LANGUAGE plpgsql STABLE AS $$
DECLARE r record; result jsonb; covered jsonb; assigned jsonb; supports jsonb; p jsonb;
BEGIN
 IF catalog THEN
  SELECT * INTO STRICT r FROM ingredient_protein_reviews WHERE id=rid;
  SELECT coalesce(jsonb_agg(term_id ORDER BY term_id),'[]') INTO covered FROM ingredient_protein_review_terms WHERE review_id=rid;
  SELECT coalesce(jsonb_agg(term_id ORDER BY term_id),'[]') INTO assigned FROM ingredient_protein_assignments WHERE review_id=rid;
 ELSE
  SELECT * INTO STRICT r FROM culinary_feature_reviews WHERE id=rid;
  SELECT coalesce(jsonb_agg(term_id ORDER BY term_id),'[]') INTO covered FROM culinary_feature_review_terms WHERE review_id=rid;
  SELECT coalesce(jsonb_agg(term_id ORDER BY term_id),'[]') INTO assigned FROM culinary_feature_assignments WHERE review_id=rid;
  SELECT coalesce(jsonb_agg(jsonb_build_object('term_id',term_id,'requirement_id',requirement_id,'ingredient_id',ingredient_id,'catalog_review_id',catalog_review_id) ORDER BY term_id,requirement_id),'[]') INTO supports FROM culinary_feature_main_protein_support WHERE review_id=rid;
 END IF;
 p:=jsonb_build_object('kind',r.source_kind,'source_system',r.source_system,'external_record_id',r.external_record_id,'source_version',r.source_version,'source_uri',r.source_uri,'content_hash',r.content_hash,'observed_at',to_char(r.observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'));
 result:=jsonb_build_object('command_kind',r.command_kind,'expected_revision_no',r.revision_no-1,'predecessor_id',r.predecessor_id,'coverage',r.coverage,'covered_term_ids',covered,'positive_term_ids',assigned,'provenance',p,'correction_reason',r.correction_reason,'idempotency_key',r.idempotency_key);
 IF catalog THEN
  result:=result||jsonb_build_object('contract_version',CASE WHEN r.action='RETRACT' THEN 'ingredient-protein-retract.v1' ELSE 'ingredient-protein-write.v1' END,'ingredient_id',r.ingredient_id,'expected_catalog_frontier',r.source_sequence-1);
 ELSE
  result:=result||jsonb_build_object('contract_version',CASE r.command_kind WHEN 'REGISTER' THEN 'culinary-feature-register.v1' WHEN 'RETRACT' THEN 'culinary-feature-retract.v1' ELSE 'culinary-feature-write.v1' END,'recipe_version_id',r.recipe_version_id,'dimension',r.dimension,'applicability_id',CASE WHEN r.command_kind='REGISTER' THEN NULL ELSE r.applicability_id END,'key',CASE WHEN r.command_kind='REGISTER' THEN menuto_feature_key(r.applicability_id) ELSE NULL END,'expected_recipe_frontier',r.source_sequence-1,'supports',supports);
  IF r.dimension='MAIN_PROTEIN' THEN result:=result||jsonb_build_object('expected_catalog_frontier',r.catalog_frontier_at_write); END IF;
 END IF;
 RETURN result;
END $$;

CREATE FUNCTION menuto_feature_check_review(rid uuid,catalog boolean) RETURNS void LANGUAGE plpgsql AS $$
DECLARE r record; c integer; a integer; s integer; digest text;
BEGIN
 IF catalog THEN
  SELECT * INTO STRICT r FROM ingredient_protein_reviews WHERE id=rid;
  SELECT count(*) INTO c FROM ingredient_protein_review_terms WHERE review_id=rid;
  SELECT count(*) INTO a FROM ingredient_protein_assignments WHERE review_id=rid;
 ELSE
  SELECT * INTO STRICT r FROM culinary_feature_reviews WHERE id=rid;
  SELECT count(*) INTO c FROM culinary_feature_review_terms WHERE review_id=rid;
  SELECT count(*) INTO a FROM culinary_feature_assignments WHERE review_id=rid;
  SELECT count(*) INTO s FROM culinary_feature_main_protein_support WHERE review_id=rid;
  IF s<>r.declared_support_count THEN RAISE EXCEPTION 'Incomplete support assembly' USING ERRCODE='23514'; END IF;
  PERFORM menuto_feature_check_scope(r.applicability_id);
  IF r.dimension='MAIN_PROTEIN' AND r.action='REPLACE' THEN
   IF EXISTS (SELECT 1 FROM culinary_feature_assignments x WHERE x.review_id=rid AND NOT EXISTS (SELECT 1 FROM culinary_feature_main_protein_support p WHERE p.review_id=rid AND p.term_id=x.term_id)) THEN RAISE EXCEPTION 'Unsupported main-protein designation' USING ERRCODE='23514'; END IF;
   IF EXISTS (SELECT 1 FROM culinary_feature_main_protein_support p JOIN culinary_feature_applicability_slots k ON k.applicability_id=p.applicability_id AND k.requirement_id=p.requirement_id
    JOIN ingredient_protein_streams cs ON cs.ingredient_id=p.ingredient_id
    WHERE p.review_id=rid AND (k.choice='ANY_AUTHORED_CHOICE' OR cs.head_review_id<>p.catalog_review_id OR NOT EXISTS (SELECT 1 FROM menuto_feature_options(p.applicability_id,p.requirement_id) o WHERE o.ingredient_id=p.ingredient_id)
     OR EXISTS (SELECT 1 FROM culinary_feature_applicability_tiers t JOIN recipe_tier_quantities q ON q.tier_id=t.tier_id AND q.requirement_id=p.requirement_id
       JOIN recipe_ingredients i ON i.id=p.requirement_id CROSS JOIN LATERAL menuto_feature_options(p.applicability_id,p.requirement_id) o
       WHERE t.applicability_id=p.applicability_id AND q.amount*o.factor+CASE WHEN k.adjustment='ZERO_ONLY' THEN 0 ELSE i.min_delta END<=0))) THEN
    RAISE EXCEPTION 'Stale/invalid/nonpositive main-protein slot support' USING ERRCODE='23514';
   END IF;
  END IF;
 END IF;
 IF c<>r.declared_covered_count OR a<>r.declared_assigned_count THEN RAISE EXCEPTION 'Incomplete immutable review assembly' USING ERRCODE='23514'; END IF;
 digest:=encode(sha256(convert_to(menuto_feature_canonical(jsonb_build_object('command',menuto_feature_review_command(rid,catalog),'actor_user_id',r.reviewer_user_id)),'UTF8')),'hex');
 IF digest<>r.command_hash THEN RAISE EXCEPTION 'Review command hash mismatch' USING ERRCODE='23514'; END IF;
END $$;

CREATE FUNCTION menuto_feature_complete() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE r record;
BEGIN
 IF TG_TABLE_NAME='ingredient_protein_streams' THEN
  IF NOT EXISTS (SELECT 1 FROM ingredient_protein_streams WHERE id=NEW.id AND head_revision_no>=0) THEN RAISE EXCEPTION 'Empty Catalog stream' USING ERRCODE='23514'; END IF;
 ELSIF TG_TABLE_NAME='culinary_feature_applicabilities' THEN PERFORM menuto_feature_check_scope(NEW.id);
 ELSIF TG_TABLE_NAME='ingredient_protein_reviews' THEN PERFORM menuto_feature_check_review(NEW.id,true);
 ELSIF TG_TABLE_NAME='culinary_feature_reviews' THEN PERFORM menuto_feature_check_review(NEW.id,false);
 ELSIF TG_TABLE_NAME LIKE 'culinary_feature_applicability_%' THEN PERFORM menuto_feature_check_scope(NEW.applicability_id);
 ELSE PERFORM menuto_feature_check_review(NEW.review_id,TG_TABLE_NAME LIKE 'ingredient_protein_%'); END IF;
 RETURN NULL;
END $$;

CREATE TRIGGER feature_registry_guard BEFORE INSERT OR UPDATE OR DELETE ON culinary_feature_applicabilities FOR EACH ROW EXECUTE FUNCTION menuto_feature_registry();
CREATE CONSTRAINT TRIGGER feature_complete AFTER INSERT ON culinary_feature_applicabilities DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_feature_complete();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON culinary_feature_applicabilities FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_insert BEFORE INSERT ON culinary_feature_applicability_slots FOR EACH ROW EXECUTE FUNCTION menuto_feature_child();
CREATE TRIGGER feature_immutable BEFORE UPDATE OR DELETE ON culinary_feature_applicability_slots FOR EACH ROW EXECUTE FUNCTION menuto_feature_immutable();
CREATE CONSTRAINT TRIGGER feature_complete AFTER INSERT ON culinary_feature_applicability_slots DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_feature_complete();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON culinary_feature_applicability_slots FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_insert BEFORE INSERT ON culinary_feature_applicability_tiers FOR EACH ROW EXECUTE FUNCTION menuto_feature_child();
CREATE TRIGGER feature_immutable BEFORE UPDATE OR DELETE ON culinary_feature_applicability_tiers FOR EACH ROW EXECUTE FUNCTION menuto_feature_immutable();
CREATE CONSTRAINT TRIGGER feature_complete AFTER INSERT ON culinary_feature_applicability_tiers DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_feature_complete();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON culinary_feature_applicability_tiers FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_insert BEFORE INSERT ON culinary_feature_assignments FOR EACH ROW EXECUTE FUNCTION menuto_feature_child();
CREATE TRIGGER feature_immutable BEFORE UPDATE OR DELETE ON culinary_feature_assignments FOR EACH ROW EXECUTE FUNCTION menuto_feature_immutable();
CREATE CONSTRAINT TRIGGER feature_complete AFTER INSERT ON culinary_feature_assignments DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_feature_complete();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON culinary_feature_assignments FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_frontier_guard BEFORE INSERT OR UPDATE OR DELETE ON culinary_feature_frontier FOR EACH ROW EXECUTE FUNCTION menuto_feature_fence();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON culinary_feature_frontier FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_insert BEFORE INSERT ON culinary_feature_main_protein_support FOR EACH ROW EXECUTE FUNCTION menuto_feature_child();
CREATE TRIGGER feature_immutable BEFORE UPDATE OR DELETE ON culinary_feature_main_protein_support FOR EACH ROW EXECUTE FUNCTION menuto_feature_immutable();
CREATE CONSTRAINT TRIGGER feature_complete AFTER INSERT ON culinary_feature_main_protein_support DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_feature_complete();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON culinary_feature_main_protein_support FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_insert BEFORE INSERT ON culinary_feature_review_terms FOR EACH ROW EXECUTE FUNCTION menuto_feature_child();
CREATE TRIGGER feature_immutable BEFORE UPDATE OR DELETE ON culinary_feature_review_terms FOR EACH ROW EXECUTE FUNCTION menuto_feature_immutable();
CREATE CONSTRAINT TRIGGER feature_complete AFTER INSERT ON culinary_feature_review_terms DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_feature_complete();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON culinary_feature_review_terms FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_insert BEFORE INSERT ON culinary_feature_reviews FOR EACH ROW EXECUTE FUNCTION menuto_feature_append();
CREATE TRIGGER feature_immutable BEFORE UPDATE OR DELETE ON culinary_feature_reviews FOR EACH ROW EXECUTE FUNCTION menuto_feature_immutable();
CREATE CONSTRAINT TRIGGER feature_complete AFTER INSERT ON culinary_feature_reviews DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_feature_complete();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON culinary_feature_reviews FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_insert BEFORE INSERT ON ingredient_protein_assignments FOR EACH ROW EXECUTE FUNCTION menuto_feature_child();
CREATE TRIGGER feature_immutable BEFORE UPDATE OR DELETE ON ingredient_protein_assignments FOR EACH ROW EXECUTE FUNCTION menuto_feature_immutable();
CREATE CONSTRAINT TRIGGER feature_complete AFTER INSERT ON ingredient_protein_assignments DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_feature_complete();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON ingredient_protein_assignments FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_frontier_guard BEFORE INSERT OR UPDATE OR DELETE ON ingredient_protein_frontier FOR EACH ROW EXECUTE FUNCTION menuto_feature_fence();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON ingredient_protein_frontier FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_insert BEFORE INSERT ON ingredient_protein_review_terms FOR EACH ROW EXECUTE FUNCTION menuto_feature_child();
CREATE TRIGGER feature_immutable BEFORE UPDATE OR DELETE ON ingredient_protein_review_terms FOR EACH ROW EXECUTE FUNCTION menuto_feature_immutable();
CREATE CONSTRAINT TRIGGER feature_complete AFTER INSERT ON ingredient_protein_review_terms DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_feature_complete();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON ingredient_protein_review_terms FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_insert BEFORE INSERT ON ingredient_protein_reviews FOR EACH ROW EXECUTE FUNCTION menuto_feature_append();
CREATE TRIGGER feature_immutable BEFORE UPDATE OR DELETE ON ingredient_protein_reviews FOR EACH ROW EXECUTE FUNCTION menuto_feature_immutable();
CREATE CONSTRAINT TRIGGER feature_complete AFTER INSERT ON ingredient_protein_reviews DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_feature_complete();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON ingredient_protein_reviews FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
CREATE TRIGGER feature_registry_guard BEFORE INSERT OR UPDATE OR DELETE ON ingredient_protein_streams FOR EACH ROW EXECUTE FUNCTION menuto_feature_registry();
CREATE CONSTRAINT TRIGGER feature_complete AFTER INSERT ON ingredient_protein_streams DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_feature_complete();
CREATE TRIGGER feature_truncate BEFORE TRUNCATE ON ingredient_protein_streams FOR EACH STATEMENT EXECUTE FUNCTION menuto_feature_immutable();
'''

DOWNGRADE_SQL = r'''
LOCK TABLE culinary_feature_applicabilities,culinary_feature_applicability_slots,culinary_feature_applicability_tiers,culinary_feature_assignments,culinary_feature_frontier,culinary_feature_main_protein_support,culinary_feature_review_terms,culinary_feature_reviews,ingredient_protein_assignments,ingredient_protein_frontier,ingredient_protein_review_terms,ingredient_protein_reviews,ingredient_protein_streams IN ACCESS EXCLUSIVE MODE;
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM culinary_feature_applicabilities WHERE true) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM culinary_feature_applicability_slots WHERE true) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM culinary_feature_applicability_tiers WHERE true) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM culinary_feature_assignments WHERE true) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM culinary_feature_frontier WHERE generation<>0) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM culinary_feature_main_protein_support WHERE true) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM culinary_feature_review_terms WHERE true) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM culinary_feature_reviews WHERE true) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM ingredient_protein_assignments WHERE true) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM ingredient_protein_frontier WHERE generation<>0) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM ingredient_protein_review_terms WHERE true) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM ingredient_protein_reviews WHERE true) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM ingredient_protein_streams WHERE true) THEN RAISE EXCEPTION 'Downgrade would lose culinary classification history' USING ERRCODE='23514'; END IF;
END $$;
ALTER TABLE ingredient_protein_streams DROP CONSTRAINT fk_ingredient_protein_reviews_head;
ALTER TABLE culinary_feature_applicabilities DROP CONSTRAINT fk_culinary_feature_reviews_head;
DROP TABLE culinary_feature_main_protein_support;
DROP TABLE culinary_feature_assignments;
DROP TABLE ingredient_protein_assignments;
DROP TABLE culinary_feature_review_terms;
DROP TABLE culinary_feature_applicability_slots;
DROP TABLE ingredient_protein_review_terms;
DROP TABLE culinary_feature_reviews;
DROP TABLE culinary_feature_applicability_tiers;
DROP TABLE ingredient_protein_reviews;
DROP TABLE culinary_feature_applicabilities;
DROP TABLE ingredient_protein_streams;
DROP TABLE ingredient_protein_frontier;
DROP TABLE culinary_feature_frontier;
DROP FUNCTION menuto_feature_complete();
DROP FUNCTION menuto_feature_check_review(uuid,boolean);
DROP FUNCTION menuto_feature_review_command(uuid,boolean);
DROP FUNCTION menuto_feature_check_scope(uuid);
DROP FUNCTION menuto_feature_child();
DROP FUNCTION menuto_feature_append();
DROP FUNCTION menuto_feature_registry();
DROP FUNCTION menuto_feature_fence();
DROP FUNCTION menuto_feature_options(uuid,uuid);
DROP FUNCTION menuto_feature_key_hash(uuid);
DROP FUNCTION menuto_feature_key(uuid);
DROP FUNCTION menuto_feature_canonical(jsonb);
DROP FUNCTION menuto_feature_immutable();
'''

def upgrade():
    op.execute(UPGRADE_SQL)

def downgrade():
    op.execute(DOWNGRADE_SQL)
