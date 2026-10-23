"""Explicit member declarations; frozen SQL, no mutable ORM imports."""
# ruff: noqa: E501
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

UPGRADE_SQL = r'''

CREATE TABLE affinity_feature_terms (
	kind VARCHAR(20) NOT NULL, 
	code VARCHAR(100) NOT NULL, 
	version INTEGER NOT NULL, 
	label VARCHAR(200) NOT NULL, 
	definition TEXT NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_affinity_feature_terms PRIMARY KEY (id), 
	CONSTRAINT uq_affinity_feature_terms_kind_code_version UNIQUE (kind, code, version), 
	CONSTRAINT uq_affinity_feature_terms_id_kind UNIQUE (id, kind), 
	CONSTRAINT ck_affinity_feature_terms_kind CHECK (kind IN ('PROTEIN','METHOD','FLAVOR')), 
	CONSTRAINT ck_affinity_feature_terms_code CHECK (code ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_affinity_feature_terms_version CHECK (version>0), 
	CONSTRAINT ck_affinity_feature_terms_definition CHECK (length(trim(label))>0 AND length(trim(definition))>0), 
	CONSTRAINT ck_affinity_feature_terms_status CHECK (status IN ('DRAFT','REVIEWED')), 
	CONSTRAINT ck_affinity_feature_terms_source_kind CHECK (source_kind IN ('USER','REVIEWED_REFERENCE')), 
	CONSTRAINT ck_affinity_feature_terms_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_affinity_feature_terms_source_identity CHECK (length(trim(external_record_id))>0 AND length(trim(source_version))>0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_affinity_feature_terms_observed_at CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_affinity_feature_terms_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_affinity_feature_terms_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_affinity_feature_terms_source_system_external_record_d8f0 UNIQUE (source_system, external_record_id, source_version)
)

;

CREATE TABLE member_preference_frontiers (
	household_id UUID NOT NULL, 
	member_id UUID NOT NULL, 
	generation BIGINT NOT NULL, 
	CONSTRAINT pk_member_preference_frontiers PRIMARY KEY (household_id, member_id), 
	CONSTRAINT fk_member_preference_frontiers_household_id_household_members FOREIGN KEY(household_id, member_id) REFERENCES household_members (household_id, id) ON DELETE RESTRICT, 
	CONSTRAINT ck_member_preference_frontiers_generation CHECK (generation>=0)
)

;

CREATE TABLE member_preference_streams (
	household_id UUID NOT NULL, 
	member_id UUID NOT NULL, 
	target_kind VARCHAR(20) NOT NULL, 
	ingredient_id UUID, 
	recipe_id UUID, 
	feature_term_id UUID, 
	head_revision INTEGER DEFAULT -1 NOT NULL, 
	head_id UUID, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_member_preference_streams PRIMARY KEY (id), 
	CONSTRAINT uq_member_preference_streams_id_household_id_member_id UNIQUE (id, household_id, member_id), 
	CONSTRAINT fk_member_preference_streams_household_id_household_members FOREIGN KEY(household_id, member_id) REFERENCES household_members (household_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_member_preference_streams_feature_term_id_affinity_f_d23b FOREIGN KEY(feature_term_id, target_kind) REFERENCES affinity_feature_terms (id, kind) ON DELETE RESTRICT, 
	CONSTRAINT ck_member_preference_streams_target_shape CHECK ((target_kind='INGREDIENT' AND ingredient_id IS NOT NULL AND recipe_id IS NULL AND feature_term_id IS NULL) OR (target_kind='DIRECT_RECIPE' AND recipe_id IS NOT NULL AND ingredient_id IS NULL AND feature_term_id IS NULL) OR (target_kind IN ('PROTEIN','METHOD','FLAVOR') AND feature_term_id IS NOT NULL AND ingredient_id IS NULL AND recipe_id IS NULL)), 
	CONSTRAINT ck_member_preference_streams_head CHECK (head_revision>=-1 AND ((head_revision=-1)=(head_id IS NULL))), 
	CONSTRAINT fk_member_preference_streams_ingredient_id_ingredients FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_member_preference_streams_recipe_id_recipes FOREIGN KEY(recipe_id) REFERENCES recipes (id) ON DELETE RESTRICT
)

;

CREATE TABLE member_preference_declarations (
	id UUID NOT NULL, 
	stream_id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	member_id UUID NOT NULL, 
	revision_no INTEGER NOT NULL, 
	predecessor_id UUID, 
	actor_user_id UUID NOT NULL, 
	authorship VARCHAR(30) NOT NULL, 
	actor_role VARCHAR(20) NOT NULL, 
	action VARCHAR(10) NOT NULL, 
	value VARCHAR(10), 
	reason VARCHAR(30) NOT NULL, 
	source VARCHAR(30) NOT NULL, 
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	member_sequence BIGINT NOT NULL, 
	idempotency_key VARCHAR(100) NOT NULL, 
	command_fingerprint VARCHAR(64) NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_member_preference_declarations PRIMARY KEY (id), 
	CONSTRAINT uq_member_preference_declarations_id_stream_id_househol_e83d UNIQUE (id, stream_id, household_id, member_id), 
	CONSTRAINT uq_member_preference_declarations_stream_id_revision_no UNIQUE (stream_id, revision_no), 
	CONSTRAINT uq_member_preference_declarations_household_id_member_i_e5a4 UNIQUE (household_id, member_id, member_sequence), 
	CONSTRAINT uq_member_preference_declarations_household_id_actor_us_8239 UNIQUE (household_id, actor_user_id, source_system, idempotency_key), 
	CONSTRAINT uq_member_preference_declarations_household_id_source_s_d315 UNIQUE (household_id, source_system, external_record_id, source_version), 
	CONSTRAINT fk_member_preference_declarations_stream_id_member_pref_6bbb FOREIGN KEY(stream_id, household_id, member_id) REFERENCES member_preference_streams (id, household_id, member_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_member_preference_declarations_predecessor_id_member_63a1 FOREIGN KEY(predecessor_id, stream_id, household_id, member_id) REFERENCES member_preference_declarations (id, stream_id, household_id, member_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_member_preference_declarations_sequence CHECK (revision_no>=0 AND member_sequence>0), 
	CONSTRAINT ck_member_preference_declarations_predecessor CHECK ((revision_no=0)=(predecessor_id IS NULL)), 
	CONSTRAINT ck_member_preference_declarations_authorship CHECK (authorship IN ('SELF','AUTHORIZED_REPRESENTATIVE') AND actor_role IN ('OWNER','EDITOR')), 
	CONSTRAINT ck_member_preference_declarations_assertion CHECK ((action='SET' AND value IN ('LIKE','DISLIKE','NEUTRAL') AND value IS NOT NULL AND ((revision_no=0 AND reason='INITIAL') OR (revision_no>0 AND reason IN ('INPUT_CORRECTION','PREFERENCE_CHANGED')))) OR (action='RETRACT' AND value IS NULL AND revision_no>0 AND reason='RETRACTED')), 
	CONSTRAINT ck_member_preference_declarations_times CHECK (isfinite(occurred_at) AND isfinite(recorded_at) AND isfinite(observed_at) AND occurred_at<=observed_at AND observed_at<=recorded_at), 
	CONSTRAINT ck_member_preference_declarations_source CHECK (source_kind='USER' AND source='EXPLICIT_DECLARATION'), 
	CONSTRAINT ck_member_preference_declarations_identifiers CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_member_preference_declarations_source_identity CHECK (length(trim(external_record_id))>0 AND length(trim(source_version))>0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_member_preference_declarations_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_member_preference_declarations_fingerprint CHECK (command_fingerprint ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_member_preference_declarations_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT fk_member_preference_declarations_actor_user_id_users FOREIGN KEY(actor_user_id) REFERENCES users (id) ON DELETE RESTRICT
)

;
CREATE UNIQUE INDEX uq_preference_flavor ON member_preference_streams (household_id, member_id, feature_term_id) WHERE target_kind='FLAVOR';
CREATE UNIQUE INDEX uq_preference_ingredient ON member_preference_streams (household_id, member_id, ingredient_id) WHERE target_kind='INGREDIENT';
CREATE UNIQUE INDEX uq_preference_method ON member_preference_streams (household_id, member_id, feature_term_id) WHERE target_kind='METHOD';
CREATE UNIQUE INDEX uq_preference_protein ON member_preference_streams (household_id, member_id, feature_term_id) WHERE target_kind='PROTEIN';
CREATE UNIQUE INDEX uq_preference_recipe ON member_preference_streams (household_id, member_id, recipe_id) WHERE target_kind='DIRECT_RECIPE';
ALTER TABLE member_preference_streams ADD CONSTRAINT fk_preference_stream_head FOREIGN KEY(head_id, id, household_id, member_id) REFERENCES member_preference_declarations (id, stream_id, household_id, member_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;CREATE FUNCTION menuto_preference_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Immutable preference source fact' USING ERRCODE='23514'; END $$;

CREATE FUNCTION menuto_preference_canonical(j jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE STRICT AS $$
DECLARE result text;
BEGIN
 CASE jsonb_typeof(j)
 WHEN 'object' THEN SELECT '{'||coalesce(string_agg(to_json(k)::text||':'||menuto_preference_canonical(v),',' ORDER BY k),'')||'}' INTO result FROM jsonb_each(j) e(k,v);
 WHEN 'array' THEN SELECT '['||coalesce(string_agg(menuto_preference_canonical(v),',' ORDER BY n),'')||']' INTO result FROM jsonb_array_elements(j) WITH ORDINALITY e(v,n);
 ELSE result:=j::text;
 END CASE;
 RETURN result;
END $$;

CREATE FUNCTION menuto_preference_term_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.observed_at>clock_timestamp() THEN RAISE EXCEPTION 'Future vocabulary source' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION menuto_preference_frontier_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP NOT IN ('INSERT','UPDATE') OR pg_trigger_depth()<>2 THEN RAISE EXCEPTION 'Protected preference frontier' USING ERRCODE='23514'; END IF;
 IF TG_OP='INSERT' THEN
  IF NEW.generation<>0 THEN RAISE EXCEPTION 'Invalid initial frontier' USING ERRCODE='23514'; END IF;
 ELSE
  IF (NEW.household_id,NEW.member_id) IS DISTINCT FROM (OLD.household_id,OLD.member_id) OR NEW.generation<>OLD.generation+1 THEN RAISE EXCEPTION 'Invalid frontier transition' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION menuto_preference_stream_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE term_status text;
BEGIN
 IF TG_OP='INSERT' THEN
  PERFORM pg_advisory_xact_lock(hashtextextended('preference.member:'||NEW.household_id::text||':'||NEW.member_id::text,0));
  IF NEW.head_revision<>-1 OR NEW.head_id IS NOT NULL THEN RAISE EXCEPTION 'Stream must start empty' USING ERRCODE='23514'; END IF;
  IF NEW.feature_term_id IS NOT NULL THEN
   SELECT status INTO term_status FROM affinity_feature_terms WHERE id=NEW.feature_term_id AND kind=NEW.target_kind;
   IF term_status IS DISTINCT FROM 'REVIEWED' THEN RAISE EXCEPTION 'Reviewed typed feature target required' USING ERRCODE='23514'; END IF;
  END IF;
 ELSIF TG_OP='UPDATE' THEN
  IF pg_trigger_depth()<>2 OR (to_jsonb(NEW)-'head_revision'-'head_id') IS DISTINCT FROM (to_jsonb(OLD)-'head_revision'-'head_id') OR NEW.head_revision<>OLD.head_revision+1 OR NEW.head_id IS NULL THEN
   RAISE EXCEPTION 'Protected preference stream/head' USING ERRCODE='23514';
  END IF;
 ELSE RAISE EXCEPTION 'Immutable preference stream identity' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION menuto_preference_complete() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM member_preference_streams s JOIN member_preference_declarations d ON d.id=s.head_id AND d.stream_id=s.id AND d.household_id=s.household_id AND d.member_id=s.member_id AND d.revision_no=s.head_revision WHERE s.id=NEW.id) THEN
  RAISE EXCEPTION 'Incomplete preference stream' USING ERRCODE='23514';
 END IF;
 RETURN NULL;
END $$;

CREATE FUNCTION menuto_preference_append() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE membership_row record; stream_row record; prior_action text; target jsonb; payload jsonb;
BEGIN
 SELECT member_id,role INTO membership_row FROM memberships WHERE household_id=NEW.household_id AND user_id=NEW.actor_user_id FOR SHARE;
 IF NOT FOUND OR membership_row.role NOT IN ('OWNER','EDITOR') THEN RAISE EXCEPTION 'Preference actor cannot write' USING ERRCODE='23514'; END IF;
 IF NEW.authorship='SELF' AND membership_row.member_id IS DISTINCT FROM NEW.member_id THEN RAISE EXCEPTION 'SELF actor differs from subject' USING ERRCODE='23514'; END IF;
 IF NEW.actor_role IS NOT NULL OR NEW.recorded_at IS NOT NULL OR NEW.member_sequence IS NOT NULL OR NEW.command_fingerprint IS NOT NULL THEN RAISE EXCEPTION 'Database-owned audit fields' USING ERRCODE='23514'; END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('preference.retry:'||NEW.household_id::text||':'||NEW.actor_user_id::text||':'||NEW.source_system||':'||NEW.idempotency_key,0));
 PERFORM pg_advisory_xact_lock(hashtextextended('preference.member:'||NEW.household_id::text||':'||NEW.member_id::text,0));
 SELECT * INTO stream_row FROM member_preference_streams WHERE id=NEW.stream_id AND household_id=NEW.household_id AND member_id=NEW.member_id FOR UPDATE;
 IF NOT FOUND OR NEW.revision_no<>stream_row.head_revision+1 OR NEW.predecessor_id IS DISTINCT FROM stream_row.head_id THEN RAISE EXCEPTION 'Stale preference predecessor/revision' USING ERRCODE='23514'; END IF;
 IF NEW.action='RETRACT' THEN
  SELECT action INTO prior_action FROM member_preference_declarations WHERE id=NEW.predecessor_id;
  IF prior_action IS DISTINCT FROM 'SET' THEN RAISE EXCEPTION 'Retraction requires active assertion' USING ERRCODE='23514'; END IF;
 END IF;
 INSERT INTO member_preference_frontiers(household_id,member_id,generation) VALUES(NEW.household_id,NEW.member_id,0) ON CONFLICT DO NOTHING;
 UPDATE member_preference_frontiers SET generation=generation+1 WHERE household_id=NEW.household_id AND member_id=NEW.member_id RETURNING generation INTO NEW.member_sequence;
 NEW.actor_role:=membership_row.role;
 NEW.recorded_at:=clock_timestamp();
 IF stream_row.target_kind='INGREDIENT' THEN target:=jsonb_build_object('kind','INGREDIENT','ingredient_id',stream_row.ingredient_id);
 ELSIF stream_row.target_kind='DIRECT_RECIPE' THEN target:=jsonb_build_object('kind','DIRECT_RECIPE','recipe_id',stream_row.recipe_id);
 ELSE target:=jsonb_build_object('kind',stream_row.target_kind,'feature_term_id',stream_row.feature_term_id); END IF;
 payload:=jsonb_build_object(
  'contract_version','member-preference-write.v1','household_id',NEW.household_id,'member_id',NEW.member_id,
  'actor_user_id',NEW.actor_user_id,'authorship',NEW.authorship,'target',target,'expected_revision',NEW.revision_no-1,
  'predecessor_id',NEW.predecessor_id,'action',NEW.action,'value',NEW.value,'reason',NEW.reason,
  'source',NEW.source,'idempotency_key',NEW.idempotency_key,
  'occurred_at',to_char(NEW.occurred_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'provenance',jsonb_build_object('kind',NEW.source_kind,'source_system',NEW.source_system,
    'external_record_id',NEW.external_record_id,'source_version',NEW.source_version,'source_uri',NEW.source_uri,
    'content_hash',NEW.content_hash,'observed_at',to_char(NEW.observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')));
 NEW.command_fingerprint:=encode(sha256(convert_to(menuto_preference_canonical(payload),'UTF8')),'hex');
 UPDATE member_preference_streams SET head_revision=NEW.revision_no,head_id=NEW.id WHERE id=NEW.stream_id;
 RETURN NEW;
END $$;

CREATE TRIGGER affinity_term_insert BEFORE INSERT ON affinity_feature_terms FOR EACH ROW EXECUTE FUNCTION menuto_preference_term_guard();
CREATE TRIGGER affinity_term_immutable BEFORE UPDATE OR DELETE ON affinity_feature_terms FOR EACH ROW EXECUTE FUNCTION menuto_preference_immutable();
CREATE TRIGGER affinity_term_truncate BEFORE TRUNCATE ON affinity_feature_terms FOR EACH STATEMENT EXECUTE FUNCTION menuto_preference_immutable();
CREATE TRIGGER preference_frontier_guard BEFORE INSERT OR UPDATE OR DELETE ON member_preference_frontiers FOR EACH ROW EXECUTE FUNCTION menuto_preference_frontier_guard();
CREATE TRIGGER preference_frontier_truncate BEFORE TRUNCATE ON member_preference_frontiers FOR EACH STATEMENT EXECUTE FUNCTION menuto_preference_immutable();
CREATE TRIGGER preference_stream_guard BEFORE INSERT OR UPDATE OR DELETE ON member_preference_streams FOR EACH ROW EXECUTE FUNCTION menuto_preference_stream_guard();
CREATE TRIGGER preference_stream_truncate BEFORE TRUNCATE ON member_preference_streams FOR EACH STATEMENT EXECUTE FUNCTION menuto_preference_immutable();
CREATE CONSTRAINT TRIGGER preference_stream_complete AFTER INSERT ON member_preference_streams DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_preference_complete();
CREATE TRIGGER preference_declaration_append BEFORE INSERT ON member_preference_declarations FOR EACH ROW EXECUTE FUNCTION menuto_preference_append();
CREATE TRIGGER preference_declaration_immutable BEFORE UPDATE OR DELETE ON member_preference_declarations FOR EACH ROW EXECUTE FUNCTION menuto_preference_immutable();
CREATE TRIGGER preference_declaration_truncate BEFORE TRUNCATE ON member_preference_declarations FOR EACH STATEMENT EXECUTE FUNCTION menuto_preference_immutable();

'''

DOWNGRADE_SQL = r'''

LOCK TABLE affinity_feature_terms,member_preference_frontiers,member_preference_streams,member_preference_declarations IN ACCESS EXCLUSIVE MODE;
DO $$ BEGIN
IF EXISTS(SELECT 1 FROM affinity_feature_terms) OR EXISTS(SELECT 1 FROM member_preference_frontiers) OR EXISTS(SELECT 1 FROM member_preference_streams) OR EXISTS(SELECT 1 FROM member_preference_declarations) THEN RAISE EXCEPTION 'Lossy preference downgrade refused' USING ERRCODE='23514'; END IF;
END $$;
ALTER TABLE member_preference_streams DROP CONSTRAINT fk_preference_stream_head;
DROP TABLE member_preference_declarations;
DROP TABLE member_preference_streams;
DROP TABLE member_preference_frontiers;
DROP TABLE affinity_feature_terms;
DROP FUNCTION menuto_preference_append();
DROP FUNCTION menuto_preference_complete();
DROP FUNCTION menuto_preference_stream_guard();
DROP FUNCTION menuto_preference_frontier_guard();
DROP FUNCTION menuto_preference_term_guard();
DROP FUNCTION menuto_preference_canonical(jsonb);
DROP FUNCTION menuto_preference_immutable();

'''

def upgrade():
    op.execute(UPGRADE_SQL)

def downgrade():
    op.execute(DOWNGRADE_SQL)
