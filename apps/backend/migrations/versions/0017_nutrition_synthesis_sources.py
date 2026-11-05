"""Dedicated source-bound synthesis rule authority. Empty installation, no content."""
# Frozen SQL: never resolve live application code during historical migration.
# ruff: noqa: E501
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None

TABLE_SQL = r'''
CREATE SEQUENCE nutrition_synthesis_recorded_order;

CREATE TABLE nutrition_synthesis_providers (
	id UUID NOT NULL,
	command JSONB NOT NULL,
	administrator JSONB NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	recorded_order BIGINT NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	actor_role_oid BIGINT NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	provider_id UUID NOT NULL,
	generation BIGINT NOT NULL,
	previous_id UUID,
	CONSTRAINT pk_nutrition_synthesis_providers PRIMARY KEY (id),
	CONSTRAINT uq_nutrition_synthesis_providers_actor_role_oid_idempotency_key UNIQUE (actor_role_oid, idempotency_key),
	CONSTRAINT ck_nutrition_synthesis_providers_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT ck_nutrition_synthesis_providers_recorded_order CHECK (recorded_order>0),
	CONSTRAINT uq_nutrition_synthesis_providers_provider_id_generation UNIQUE (provider_id, generation),
	CONSTRAINT ck_nutrition_synthesis_providers_generation CHECK (generation>0 AND (generation=1)=(previous_id IS NULL)),
	CONSTRAINT uq_nutrition_synthesis_providers_recorded_order UNIQUE (recorded_order)
)

;

CREATE TABLE nutrition_synthesis_principals (
	id UUID NOT NULL,
	command JSONB NOT NULL,
	administrator JSONB NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	recorded_order BIGINT NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	actor_role_oid BIGINT NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	database_oid BIGINT NOT NULL,
	database_name VARCHAR(63) NOT NULL,
	role_oid BIGINT NOT NULL,
	role_name VARCHAR(63) NOT NULL,
	verified_human_id UUID,
	user_id UUID,
	service_id VARCHAR(100),
	enrollment_root_id UUID NOT NULL,
	generation BIGINT NOT NULL,
	previous_id UUID,
	CONSTRAINT pk_nutrition_synthesis_principals PRIMARY KEY (id),
	CONSTRAINT uq_nutrition_synthesis_principals_actor_role_oid_idempo_caee UNIQUE (actor_role_oid, idempotency_key),
	CONSTRAINT ck_nutrition_synthesis_principals_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT ck_nutrition_synthesis_principals_recorded_order CHECK (recorded_order>0),
	CONSTRAINT uq_nutrition_synthesis_principals_enrollment_root_id_generation UNIQUE (enrollment_root_id, generation),
	CONSTRAINT ck_nutrition_synthesis_principals_generation CHECK (generation>0 AND (generation=1)=(previous_id IS NULL)),
	CONSTRAINT ck_nutrition_synthesis_principals_identity_class CHECK ((verified_human_id IS NULL)<>(service_id IS NULL)),
	CONSTRAINT ck_nutrition_synthesis_principals_service_not_user CHECK (service_id IS NULL OR user_id IS NULL),
	CONSTRAINT uq_nutrition_synthesis_principals_recorded_order UNIQUE (recorded_order)
)

;

CREATE TABLE nutrition_synthesis_principal_frontiers (
	enrollment_root_id UUID NOT NULL,
	revision BIGINT NOT NULL,
	head_id UUID NOT NULL,
	head_hash VARCHAR(64) NOT NULL,
	lock_version BIGINT NOT NULL,
	CONSTRAINT pk_nutrition_synthesis_principal_frontiers PRIMARY KEY (enrollment_root_id),
	CONSTRAINT ck_nutrition_synthesis_principal_frontiers_frontier CHECK (revision>0 AND lock_version>=0)
)

;

CREATE TABLE nutrition_synthesis_grants (
	id UUID NOT NULL,
	command JSONB NOT NULL,
	administrator JSONB NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	recorded_order BIGINT NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	actor_role_oid BIGINT NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	provider_id UUID NOT NULL,
	family_id VARCHAR(100) NOT NULL,
	principal_id UUID NOT NULL,
	capability VARCHAR(40) NOT NULL,
	generation BIGINT NOT NULL,
	previous_id UUID,
	CONSTRAINT pk_nutrition_synthesis_grants PRIMARY KEY (id),
	CONSTRAINT uq_nutrition_synthesis_grants_actor_role_oid_idempotency_key UNIQUE (actor_role_oid, idempotency_key),
	CONSTRAINT ck_nutrition_synthesis_grants_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT ck_nutrition_synthesis_grants_recorded_order CHECK (recorded_order>0),
	CONSTRAINT uq_nutrition_synthesis_grants_provider_id_family_id_pri_da88 UNIQUE (provider_id, family_id, principal_id, capability, generation),
	CONSTRAINT ck_nutrition_synthesis_grants_generation CHECK (generation>0 AND (generation=1)=(previous_id IS NULL)),
	CONSTRAINT uq_nutrition_synthesis_grants_recorded_order UNIQUE (recorded_order)
)

;

CREATE TABLE nutrition_synthesis_streams (
	provider_id UUID NOT NULL,
	family_id VARCHAR(100) NOT NULL,
	revision BIGINT NOT NULL,
	head_id UUID,
	head_hash VARCHAR(64),
	CONSTRAINT pk_nutrition_synthesis_streams PRIMARY KEY (provider_id, family_id),
	CONSTRAINT ck_nutrition_synthesis_streams_frontier CHECK (revision>=0 AND (family_id='__AUTHORITY_LOCK__' OR ((revision=0)=(head_id IS NULL) AND (head_id IS NULL)=(head_hash IS NULL))))
)

;

CREATE TABLE nutrition_synthesis_receipts (
	id UUID NOT NULL,
	provider_id UUID NOT NULL,
	family_id VARCHAR(100) NOT NULL,
	sequence BIGINT NOT NULL,
	principal_id UUID NOT NULL,
	grant_id UUID NOT NULL,
	actor JSONB NOT NULL,
	command JSONB NOT NULL,
	previous_id UUID,
	previous_hash VARCHAR(64),
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	recorded_order BIGINT NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	event_hash VARCHAR(64) NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	CONSTRAINT pk_nutrition_synthesis_receipts PRIMARY KEY (id),
	CONSTRAINT uq_nutrition_synthesis_receipts_principal_id_idempotency_key UNIQUE (principal_id, idempotency_key),
	CONSTRAINT uq_nutrition_synthesis_receipts_provider_id_family_id_sequence UNIQUE (provider_id, family_id, sequence),
	CONSTRAINT ck_nutrition_synthesis_receipts_lineage CHECK (sequence>0 AND (sequence=1)=(previous_id IS NULL) AND (previous_id IS NULL)=(previous_hash IS NULL)),
	CONSTRAINT ck_nutrition_synthesis_receipts_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT ck_nutrition_synthesis_receipts_recorded_order CHECK (recorded_order>0),
	CONSTRAINT uq_nutrition_synthesis_receipts_recorded_order UNIQUE (recorded_order)
)

;

CREATE TABLE nutrition_synthesis_drafts (
	id UUID NOT NULL,
	revision_id UUID NOT NULL,
	body_fingerprint VARCHAR(64) NOT NULL,
	evidence_fingerprint VARCHAR(64) NOT NULL,
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_synthesis_drafts PRIMARY KEY (id),
	CONSTRAINT uq_nutrition_synthesis_drafts_revision_id UNIQUE (revision_id)
)

;

CREATE TABLE nutrition_synthesis_reviews (
	id UUID NOT NULL,
	revision_id UUID NOT NULL,
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_synthesis_reviews PRIMARY KEY (id)
)

;

CREATE TABLE nutrition_synthesis_publications (
	id UUID NOT NULL,
	revision_id UUID NOT NULL,
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_synthesis_publications PRIMARY KEY (id)
)

;

CREATE TABLE nutrition_synthesis_evidence (
	evidence_id VARCHAR(100) NOT NULL,
	body JSONB NOT NULL,
	fingerprint VARCHAR(64) NOT NULL,
	CONSTRAINT pk_nutrition_synthesis_evidence PRIMARY KEY (evidence_id)
)

;
ALTER TABLE nutrition_synthesis_principals ADD CONSTRAINT fk_nutrition_synthesis_principals_enrollment_root_id_nu_5087 FOREIGN KEY(enrollment_root_id) REFERENCES nutrition_synthesis_principals (id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_synthesis_principals ADD CONSTRAINT fk_nutrition_synthesis_principals_previous_id_nutrition_583d FOREIGN KEY(previous_id) REFERENCES nutrition_synthesis_principals (id);
ALTER TABLE nutrition_synthesis_principals ADD CONSTRAINT fk_nutrition_synthesis_principals_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT;
ALTER TABLE nutrition_synthesis_principal_frontiers ADD CONSTRAINT fk_nutrition_synthesis_principal_frontiers_enrollment_r_00f6 FOREIGN KEY(enrollment_root_id) REFERENCES nutrition_synthesis_principals (id);
ALTER TABLE nutrition_synthesis_principal_frontiers ADD CONSTRAINT fk_nutrition_synthesis_principal_frontiers_head_id_nutr_ad15 FOREIGN KEY(head_id) REFERENCES nutrition_synthesis_principals (id);
ALTER TABLE nutrition_synthesis_grants ADD CONSTRAINT fk_nutrition_synthesis_grants_principal_id_nutrition_sy_a072 FOREIGN KEY(principal_id) REFERENCES nutrition_synthesis_principals (id);
ALTER TABLE nutrition_synthesis_receipts ADD CONSTRAINT fk_nutrition_synthesis_receipts_grant_id_nutrition_synt_67d7 FOREIGN KEY(grant_id) REFERENCES nutrition_synthesis_grants (id);
ALTER TABLE nutrition_synthesis_receipts ADD CONSTRAINT fk_nutrition_synthesis_receipts_principal_id_nutrition__5e4d FOREIGN KEY(principal_id) REFERENCES nutrition_synthesis_principals (id);
ALTER TABLE nutrition_synthesis_drafts ADD CONSTRAINT fk_nutrition_synthesis_drafts_id_nutrition_synthesis_receipts FOREIGN KEY(id) REFERENCES nutrition_synthesis_receipts (id);
ALTER TABLE nutrition_synthesis_reviews ADD CONSTRAINT fk_nutrition_synthesis_reviews_id_nutrition_synthesis_receipts FOREIGN KEY(id) REFERENCES nutrition_synthesis_receipts (id);
ALTER TABLE nutrition_synthesis_reviews ADD CONSTRAINT fk_nutrition_synthesis_reviews_revision_id_nutrition_sy_d754 FOREIGN KEY(revision_id) REFERENCES nutrition_synthesis_drafts (revision_id);
ALTER TABLE nutrition_synthesis_publications ADD CONSTRAINT fk_nutrition_synthesis_publications_id_nutrition_synthe_5dc5 FOREIGN KEY(id) REFERENCES nutrition_synthesis_receipts (id);
ALTER TABLE nutrition_synthesis_publications ADD CONSTRAINT fk_nutrition_synthesis_publications_revision_id_nutriti_826b FOREIGN KEY(revision_id) REFERENCES nutrition_synthesis_drafts (revision_id);
'''

FUNCTION_SQL = r'''
DO $$ BEGIN
 IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='menuto_nutrition_synthesis_owner') THEN CREATE ROLE menuto_nutrition_synthesis_owner NOLOGIN; END IF;
 IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='menuto_nutrition_synthesis_admin') THEN CREATE ROLE menuto_nutrition_synthesis_admin NOLOGIN; END IF;
 IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='menuto_nutrition_synthesis_client') THEN CREATE ROLE menuto_nutrition_synthesis_client NOLOGIN; END IF;
END $$;
DO $$ DECLARE n text; BEGIN
 FOREACH n IN ARRAY ARRAY['menuto_nutrition_synthesis_owner','menuto_nutrition_synthesis_admin','menuto_nutrition_synthesis_client'] LOOP
  IF EXISTS(SELECT FROM pg_roles WHERE rolname=n AND(rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN RAISE EXCEPTION 'Unsafe existing synthesis infrastructure role'; END IF;
 END LOOP;
 IF EXISTS(SELECT FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member WHERE r.rolname='menuto_nutrition_synthesis_owner') THEN RAISE EXCEPTION 'Synthesis owner must not inherit roles'; END IF;
END $$;
CREATE SCHEMA menuto_nutrition_synthesis AUTHORIZATION menuto_nutrition_synthesis_owner;
REVOKE ALL ON SCHEMA menuto_nutrition_synthesis FROM PUBLIC;
GRANT USAGE ON SCHEMA menuto_nutrition_synthesis TO menuto_nutrition_synthesis_admin,menuto_nutrition_synthesis_client;
GRANT USAGE ON SCHEMA public TO menuto_nutrition_synthesis_owner;
GRANT SELECT ON public.users,public.households,public.household_members,public.memberships TO menuto_nutrition_synthesis_owner;
DO $$ DECLARE ns name; BEGIN
 IF NOT EXISTS (SELECT FROM pg_catalog.pg_extension WHERE extname='sslinfo') THEN
  CREATE EXTENSION sslinfo WITH SCHEMA menuto_nutrition_synthesis;
 END IF;
 SELECT n.nspname INTO STRICT ns FROM pg_catalog.pg_extension e JOIN pg_catalog.pg_namespace n ON n.oid=e.extnamespace WHERE e.extname='sslinfo';
 EXECUTE format('GRANT USAGE ON SCHEMA %I TO menuto_nutrition_synthesis_owner',ns);
 EXECUTE format('GRANT EXECUTE ON FUNCTION %I.ssl_is_used() TO menuto_nutrition_synthesis_owner',ns);
 EXECUTE format('CREATE FUNCTION menuto_nutrition_synthesis.backend_tls() RETURNS boolean LANGUAGE sql STABLE SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp BEGIN ATOMIC SELECT %I.ssl_is_used(); END',ns);
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.utc(t timestamptz) RETURNS text LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
 SELECT to_char(t AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
$$;
CREATE FUNCTION menuto_nutrition_synthesis.canonical(j jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE r text; BEGIN
 CASE jsonb_typeof(j)
 WHEN 'object' THEN SELECT '{'||coalesce(string_agg(to_jsonb(key)::text||':'||menuto_nutrition_synthesis.canonical(value),',' ORDER BY key COLLATE "C"),'')||'}' INTO r FROM jsonb_each(j);
 WHEN 'array' THEN SELECT '['||coalesce(string_agg(menuto_nutrition_synthesis.canonical(value),',' ORDER BY ord),'')||']' INTO r FROM jsonb_array_elements(j) WITH ORDINALITY a(value,ord);
 WHEN 'number' THEN
  IF j::text !~ '^-?(0|[1-9][0-9]*)$' THEN RAISE EXCEPTION 'Exact integer required'; END IF; r:=j::text;
 ELSE r:=j::text;
 END CASE; RETURN r;
END $$;
CREATE FUNCTION menuto_nutrition_synthesis.hash(domain text,j jsonb) RETURNS text LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
 SELECT encode(sha256(convert_to(menuto_nutrition_synthesis.canonical(jsonb_build_object('domain',domain,'value',j)),'UTF8')),'hex')
$$;
CREATE FUNCTION menuto_nutrition_synthesis.uuid(j jsonb) RETURNS uuid LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE v uuid; BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'UUID string required'; END IF;
 v:=(j#>>'{}')::uuid;
 IF v::text<>(j#>>'{}') THEN RAISE EXCEPTION 'Canonical UUID required'; END IF; RETURN v;
END $$;
CREATE FUNCTION menuto_nutrition_synthesis.bounds(j jsonb, maxbytes integer, depth integer DEFAULT 0) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE x jsonb; BEGIN
 IF depth>32 OR octet_length(j::text)>maxbytes THEN RAISE EXCEPTION 'Nutrition source structural/byte limit; all-or-error'; END IF;
 CASE jsonb_typeof(j)
 WHEN 'number' THEN
  IF length(j::text)>40 OR j::text !~ '^-?(0|[1-9][0-9]*)$' OR abs(j::text::numeric)>170141183460469231731687303715884105727 THEN
   RAISE EXCEPTION 'Nutrition source exact integer size limit';
  END IF;
 WHEN 'array' THEN
  IF jsonb_array_length(j)>4096 THEN RAISE EXCEPTION 'Nutrition source row limit'; END IF;
  FOR x IN SELECT value FROM jsonb_array_elements(j) LOOP PERFORM menuto_nutrition_synthesis.bounds(x,maxbytes,depth+1); END LOOP;
 WHEN 'object' THEN
  FOR x IN SELECT value FROM jsonb_each(j) LOOP PERFORM menuto_nutrition_synthesis.bounds(x,maxbytes,depth+1); END LOOP;
 ELSE NULL;
 END CASE;
END $$;
CREATE FUNCTION menuto_nutrition_synthesis.deadline(t timestamptz) RETURNS void LANGUAGE plpgsql VOLATILE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$ BEGIN
 IF clock_timestamp()-t>interval '15 seconds' THEN RAISE EXCEPTION 'Nutrition source operation budget exceeded' USING ERRCODE='57014'; END IF;
END $$;
CREATE FUNCTION menuto_nutrition_synthesis.interval_ok(j jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$ BEGIN
 IF (j->>'start')::timestamptz >= (j->>'end')::timestamptz THEN RAISE EXCEPTION 'Nonempty effective interval required'; END IF;
END $$;
CREATE FUNCTION menuto_nutrition_synthesis.covers(outer_interval jsonb,inner_interval jsonb) RETURNS boolean LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
 SELECT (outer_interval->>'start')::timestamptz<=(inner_interval->>'start')::timestamptz
    AND (outer_interval->>'end')::timestamptz>=(inner_interval->>'end')::timestamptz
$$;
CREATE FUNCTION menuto_nutrition_synthesis.evidence(j jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$ BEGIN
 IF j->>'body_fingerprint'<>menuto_nutrition_synthesis.hash('nutrition.evidence-body.v1',j->'body') THEN RAISE EXCEPTION 'Retained evidence body differs'; END IF;
END $$;
CREATE FUNCTION menuto_nutrition_synthesis.validate_json(j jsonb,s jsonb,root jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE t text; x record; option jsonb; ok boolean:=false; n numeric; BEGIN
 IF s ? '$ref' THEN PERFORM menuto_nutrition_synthesis.validate_json(j,root->'$defs'->split_part(s->>'$ref','/',3),root); RETURN; END IF;
 IF s ? 'anyOf' THEN
  FOR option IN SELECT value FROM jsonb_array_elements(s->'anyOf') LOOP
   BEGIN PERFORM menuto_nutrition_synthesis.validate_json(j,option,root); ok:=true; EXCEPTION WHEN raise_exception THEN NULL; END;
   EXIT WHEN ok;
  END LOOP;
  IF NOT ok THEN RAISE EXCEPTION 'Closed union contract mismatch'; END IF; RETURN;
 END IF;
 IF s ? 'oneOf' THEN
  FOR option IN SELECT value FROM jsonb_array_elements(s->'oneOf') LOOP
   BEGIN PERFORM menuto_nutrition_synthesis.validate_json(j,option,root); ok:=true; EXCEPTION WHEN raise_exception THEN NULL; END;
   EXIT WHEN ok;
  END LOOP;
  IF NOT ok THEN RAISE EXCEPTION 'Closed discriminated contract mismatch'; END IF; RETURN;
 END IF;
 IF s ? 'const' AND j IS DISTINCT FROM s->'const' THEN RAISE EXCEPTION 'Closed constant mismatch'; END IF;
 IF s ? 'enum' AND NOT (s->'enum' @> jsonb_build_array(j)) THEN RAISE EXCEPTION 'Closed enum mismatch'; END IF;
 t:=s->>'type';
 IF t='integer' THEN
  IF jsonb_typeof(j) IS DISTINCT FROM 'number' OR j::text !~ '^-?(0|[1-9][0-9]*)$' THEN RAISE EXCEPTION 'Strict integer required'; END IF;
  n:=j::text::numeric;
  IF (s ? 'minimum' AND n<(s->>'minimum')::numeric) OR (s ? 'maximum' AND n>(s->>'maximum')::numeric) OR (s ? 'exclusiveMinimum' AND n<=(s->>'exclusiveMinimum')::numeric) THEN RAISE EXCEPTION 'Integer bound'; END IF;
 ELSIF t IS NOT NULL AND jsonb_typeof(j) IS DISTINCT FROM t THEN RAISE EXCEPTION 'Strict contract type mismatch';
 END IF;
 IF t='object' THEN
  IF (SELECT array_agg(k ORDER BY k) FROM jsonb_object_keys(j) k) IS DISTINCT FROM (SELECT array_agg(k ORDER BY k) FROM jsonb_object_keys(s->'properties') k) THEN RAISE EXCEPTION 'Complete closed canonical fields required'; END IF;
  FOR x IN SELECT key,value FROM jsonb_each(j) LOOP PERFORM menuto_nutrition_synthesis.validate_json(x.value,s->'properties'->x.key,root); END LOOP;
 ELSIF t='array' THEN
  IF (s ? 'minItems' AND jsonb_array_length(j)<(s->>'minItems')::int) OR (s ? 'maxItems' AND jsonb_array_length(j)>(s->>'maxItems')::int) THEN RAISE EXCEPTION 'Array bound'; END IF;
  FOR x IN SELECT value,ordinality FROM jsonb_array_elements(j) WITH ORDINALITY LOOP
   PERFORM menuto_nutrition_synthesis.validate_json(x.value,coalesce(s->'prefixItems'->(x.ordinality::int-1),s->'items'),root);
  END LOOP;
 ELSIF t='string' THEN
  IF (s ? 'minLength' AND length(j#>>'{}')<(s->>'minLength')::int) OR (s ? 'maxLength' AND length(j#>>'{}')>(s->>'maxLength')::int) OR (s ? 'pattern' AND (j#>>'{}') !~ (s->>'pattern')) THEN RAISE EXCEPTION 'String contract bound'; END IF;
  IF s->>'format'='uuid' THEN PERFORM menuto_nutrition_synthesis.uuid(j); END IF;
  IF s->>'format'='date-time' THEN
   IF NOT isfinite((j#>>'{}')::timestamptz) OR menuto_nutrition_synthesis.utc((j#>>'{}')::timestamptz)<>j#>>'{}' THEN RAISE EXCEPTION 'Canonical finite UTC time required'; END IF;
  END IF;
 END IF;
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.safe_role(login name,admin_mode boolean) RETURNS void LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE r record; db_owner oid; t record; BEGIN
 SELECT * INTO r FROM pg_roles WHERE rolname=login;
 SELECT datdba INTO db_owner FROM pg_database WHERE datname=current_database();
 IF r.oid IS NULL OR NOT r.rolcanlogin OR r.oid=db_owner OR EXISTS(
  SELECT FROM pg_roles p WHERE pg_has_role(r.oid,p.oid,'MEMBER') AND
  (p.rolsuper OR p.rolcreaterole OR p.rolcreatedb OR p.rolreplication OR p.rolbypassrls OR p.oid=db_owner
   OR p.rolname IN ('pg_read_all_data','pg_write_all_data','pg_read_server_files','pg_write_server_files',
    'pg_execute_server_program','pg_signal_backend','pg_maintain','pg_checkpoint','pg_create_subscription')
   OR p.rolname ~ '^menuto_.*_owner$'
   OR (p.rolname ~ '^menuto_.*_admin$' AND NOT(admin_mode AND p.rolname='menuto_nutrition_synthesis_admin'))))
 THEN RAISE EXCEPTION 'Unsafe synthesis source principal' USING ERRCODE='42501'; END IF;
 IF has_schema_privilege(r.oid,'menuto_nutrition_synthesis','CREATE') THEN RAISE EXCEPTION 'Writable protected schema' USING ERRCODE='42501'; END IF;
 IF has_sequence_privilege(r.oid,'public.nutrition_synthesis_recorded_order','USAGE,SELECT,UPDATE') THEN RAISE EXCEPTION 'Direct source order rights forbidden' USING ERRCODE='42501'; END IF;
 FOR t IN SELECT c.oid,c.relowner FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='public' AND c.relkind='r' AND c.relname LIKE 'nutrition_synthesis_%' LOOP
  IF t.relowner=r.oid OR has_table_privilege(r.oid,t.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') THEN
   RAISE EXCEPTION 'Direct source rights forbidden' USING ERRCODE='42501'; END IF;
 END LOOP;
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.session_fact(admin_mode boolean) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE r record; d record; BEGIN
 IF system_user IS DISTINCT FROM ('scram-sha-256:'||session_user) OR current_setting('role')<>'none'
  OR inet_client_addr() IS NULL THEN RAISE EXCEPTION 'Authenticated un-switched SCRAM login required' USING ERRCODE='28000'; END IF;
 IF inet_client_addr() NOT IN ('127.0.0.1'::inet,'::1'::inet) AND NOT menuto_nutrition_synthesis.backend_tls() THEN RAISE EXCEPTION 'Remote TLS required' USING ERRCODE='28000'; END IF;
 PERFORM menuto_nutrition_synthesis.safe_role(session_user,admin_mode);
 IF admin_mode AND NOT pg_has_role(session_user,'menuto_nutrition_synthesis_admin','MEMBER') THEN
  RAISE EXCEPTION 'Separate synthesis registrar required' USING ERRCODE='42501'; END IF;
 SELECT oid,rolname INTO STRICT r FROM pg_roles WHERE rolname=session_user;
 SELECT oid,datname INTO STRICT d FROM pg_database WHERE datname=current_database();
 RETURN jsonb_build_object('database_oid',d.oid::bigint,'database_name',d.datname,'role_oid',r.oid::bigint,'role_name',r.rolname,
  'authentication_method','scram-sha-256','authenticated_identity',r.rolname);
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.check_command(n text,c jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE schemas jsonb:='{"NutritionSynthesisCaptureCommand": {"$defs": {"HouseholdMemberIdentity": {"additionalProperties": false, "properties": {"contract_version": {"const": "household-member-identity.v1", "default": "household-member-identity.v1", "title": "Contract Version", "type": "string"}, "household_id": {"format": "uuid", "title": "Household Id", "type": "string"}, "member_id": {"format": "uuid", "title": "Member Id", "type": "string"}}, "required": ["household_id", "member_id"], "title": "HouseholdMemberIdentity", "type": "object"}, "NutritionCaptureFrame": {"additionalProperties": false, "properties": {"absence_stream_keys": {"items": {"pattern": "^[a-f0-9]{64}$", "type": "string"}, "title": "Absence Stream Keys", "type": "array"}, "backend_pid": {"maximum": 9223372036854775807, "minimum": 0, "title": "Backend Pid", "type": "integer"}, "completed_at": {"format": "date-time", "title": "Completed At", "type": "string"}, "endpoint": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Endpoint", "type": "string"}, "isolation": {"enum": ["REPEATABLE READ", "SERIALIZABLE"], "title": "Isolation", "type": "string"}, "mvcc_snapshot": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Mvcc Snapshot", "type": "string"}, "provider_enrollment_id": {"format": "uuid", "title": "Provider Enrollment Id", "type": "string"}, "read_only": {"const": true, "title": "Read Only", "type": "boolean"}, "reader_grant_id": {"format": "uuid", "title": "Reader Grant Id", "type": "string"}, "reader_principal_id": {"format": "uuid", "title": "Reader Principal Id", "type": "string"}, "reader_subject_witness": {"$ref": "#/$defs/NutritionSubjectWitness"}, "row_count": {"maximum": 9223372036854775807, "minimum": 0, "title": "Row Count", "type": "integer"}, "session": {"$ref": "#/$defs/NutritionSourceSession"}, "started_at": {"format": "date-time", "title": "Started At", "type": "string"}, "transaction_id": {"const": "UNASSIGNED_READ_ONLY", "title": "Transaction Id", "type": "string"}}, "required": ["session", "reader_principal_id", "reader_subject_witness", "reader_grant_id", "endpoint", "backend_pid", "mvcc_snapshot", "transaction_id", "isolation", "read_only", "started_at", "completed_at", "provider_enrollment_id", "row_count", "absence_stream_keys"], "title": "NutritionCaptureFrame", "type": "object"}, "NutritionPrecisionSelection": {"additionalProperties": false, "properties": {"actor_user_id": {"format": "uuid", "title": "Actor User Id", "type": "string"}, "evidence": {"$ref": "#/$defs/NutritionSourceEvidence"}, "source": {"const": "REQUEST_EXPLICIT", "title": "Source", "type": "string"}, "subject": {"$ref": "#/$defs/HouseholdMemberIdentity"}, "value": {"enum": ["RELAXED", "STANDARD", "PRECISION"], "title": "Value", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["value", "source", "version", "actor_user_id", "subject", "evidence"], "title": "NutritionPrecisionSelection", "type": "object"}, "NutritionRootRequest": {"additionalProperties": false, "properties": {"contract_version": {"const": "nutrition-root-request.v1", "default": "nutrition-root-request.v1", "title": "Contract Version", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "family_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Family Id", "type": "string"}, "goal_type": {"const": "ENERGY_DIRECTION", "title": "Goal Type", "type": "string"}, "guideline_body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Guideline Body Fingerprint", "type": "string"}, "guideline_revision_id": {"format": "uuid", "title": "Guideline Revision Id", "type": "string"}, "protocol_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Protocol Fingerprint", "type": "string"}, "provider_id": {"format": "uuid", "title": "Provider Id", "type": "string"}, "purpose": {"enum": ["ROOT", "VALIDATOR"], "title": "Purpose", "type": "string"}, "scope_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Id", "type": "string"}, "scope_version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Version", "type": "string"}, "subject": {"$ref": "#/$defs/HouseholdMemberIdentity"}, "temporal": {"$ref": "#/$defs/NutritionTemporalScope"}}, "required": ["subject", "provider_id", "family_id", "guideline_revision_id", "guideline_body_fingerprint", "protocol_fingerprint", "scope_id", "scope_version", "temporal", "environment", "purpose", "goal_type"], "title": "NutritionRootRequest", "type": "object"}, "NutritionSourceEvidence": {"additionalProperties": false, "properties": {"body": {"maxLength": 16384, "minLength": 1, "title": "Body", "type": "string"}, "body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Evidence Id", "type": "string"}, "purpose": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Purpose", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["evidence_id", "version", "environment", "purpose", "body", "body_fingerprint"], "title": "NutritionSourceEvidence", "type": "object"}, "NutritionSourceInterval": {"additionalProperties": false, "properties": {"end": {"format": "date-time", "title": "End", "type": "string"}, "start": {"format": "date-time", "title": "Start", "type": "string"}}, "required": ["start", "end"], "title": "NutritionSourceInterval", "type": "object"}, "NutritionSourceSession": {"additionalProperties": false, "properties": {"authenticated_identity": {"maxLength": 63, "minLength": 1, "pattern": "^[^\\x00-\\x1f\\x7f]+$", "title": "Authenticated Identity", "type": "string"}, "authentication_method": {"const": "scram-sha-256", "title": "Authentication Method", "type": "string"}, "database_name": {"maxLength": 63, "minLength": 1, "pattern": "^[^\\x00-\\x1f\\x7f]+$", "title": "Database Name", "type": "string"}, "database_oid": {"exclusiveMinimum": 0, "maximum": 4294967295, "title": "Database Oid", "type": "integer"}, "role_name": {"maxLength": 63, "minLength": 1, "pattern": "^[^\\x00-\\x1f\\x7f]+$", "title": "Role Name", "type": "string"}, "role_oid": {"exclusiveMinimum": 0, "maximum": 4294967295, "title": "Role Oid", "type": "integer"}}, "required": ["database_oid", "database_name", "role_oid", "role_name", "authentication_method", "authenticated_identity"], "title": "NutritionSourceSession", "type": "object"}, "NutritionSubjectWitness": {"additionalProperties": false, "properties": {"actor_member_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Actor Member Id"}, "actor_user_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Actor User Id"}, "membership_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Membership Id"}, "role": {"anyOf": [{"enum": ["OWNER", "EDITOR", "VIEWER"], "type": "string"}, {"type": "null"}], "title": "Role"}, "subject": {"$ref": "#/$defs/HouseholdMemberIdentity"}}, "required": ["subject", "actor_user_id", "membership_id", "actor_member_id", "role"], "title": "NutritionSubjectWitness", "type": "object"}, "NutritionSynthesisSelection": {"additionalProperties": false, "properties": {"body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "evidence_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Evidence Fingerprint", "type": "string"}, "family_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Family Id", "type": "string"}, "language_version": {"const": "FINITE_EXACT_V1", "title": "Language Version", "type": "string"}, "provider_id": {"format": "uuid", "title": "Provider Id", "type": "string"}, "publication_id": {"format": "uuid", "title": "Publication Id", "type": "string"}, "revision_id": {"format": "uuid", "title": "Revision Id", "type": "string"}, "selection_version": {"const": "EXACT_SINGLE_CASE_V1", "title": "Selection Version", "type": "string"}}, "required": ["provider_id", "family_id", "revision_id", "publication_id", "body_fingerprint", "evidence_fingerprint", "selection_version", "language_version"], "title": "NutritionSynthesisSelection", "type": "object"}, "NutritionTemporalScope": {"additionalProperties": false, "properties": {"calendar": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Calendar", "type": "string"}, "interval": {"$ref": "#/$defs/NutritionSourceInterval"}, "kind": {"enum": ["EXACT_INTERVAL", "DAY", "WEEK"], "title": "Kind", "type": "string"}, "period_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Period Id", "type": "string"}, "timezone": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Timezone", "type": "string"}}, "required": ["kind", "period_id", "calendar", "timezone", "interval"], "title": "NutritionTemporalScope", "type": "object"}}, "additionalProperties": false, "properties": {"precision": {"anyOf": [{"$ref": "#/$defs/NutritionPrecisionSelection"}, {"type": "null"}]}, "root_frame": {"$ref": "#/$defs/NutritionCaptureFrame"}, "root_request": {"$ref": "#/$defs/NutritionRootRequest"}, "selection": {"$ref": "#/$defs/NutritionSynthesisSelection"}}, "required": ["root_request", "root_frame", "selection", "precision"], "title": "NutritionSynthesisCaptureCommand", "type": "object"}, "NutritionSynthesisCommand": {"$defs": {"NutritionRuleApplicability": {"additionalProperties": false, "properties": {"guideline_body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Guideline Body Fingerprint", "type": "string"}, "guideline_revision_id": {"format": "uuid", "title": "Guideline Revision Id", "type": "string"}, "protocol_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Protocol Fingerprint", "type": "string"}, "root_family_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Root Family Id", "type": "string"}, "root_provider_id": {"format": "uuid", "title": "Root Provider Id", "type": "string"}, "scope_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Id", "type": "string"}, "scope_version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Version", "type": "string"}, "temporal": {"$ref": "#/$defs/NutritionTemporalScope"}}, "required": ["root_provider_id", "root_family_id", "guideline_revision_id", "guideline_body_fingerprint", "protocol_fingerprint", "scope_id", "scope_version", "temporal"], "title": "NutritionRuleApplicability", "type": "object"}, "NutritionRuleCase": {"additionalProperties": false, "properties": {"comfort_root_keys": {"items": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, "maxItems": 16, "minItems": 1, "title": "Comfort Root Keys", "type": "array"}, "daily_root_keys": {"items": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, "maxItems": 16, "minItems": 1, "title": "Daily Root Keys", "type": "array"}, "direction": {"enum": ["CUT", "MAINTAIN", "GAIN"], "title": "Direction", "type": "string"}, "id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Id", "type": "string"}, "operations": {"items": {"$ref": "#/$defs/NutritionSynthesisOperation"}, "maxItems": 256, "minItems": 1, "title": "Operations", "type": "array"}, "required_claims": {"items": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, "maxItems": 64, "minItems": 1, "title": "Required Claims", "type": "array"}, "weekly": {"enum": ["REQUIRED", "NOT_APPLICABLE"], "title": "Weekly", "type": "string"}}, "required": ["id", "direction", "operations", "required_claims", "daily_root_keys", "comfort_root_keys", "weekly"], "title": "NutritionRuleCase", "type": "object"}, "NutritionSourceEvidence": {"additionalProperties": false, "properties": {"body": {"maxLength": 16384, "minLength": 1, "title": "Body", "type": "string"}, "body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Evidence Id", "type": "string"}, "purpose": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Purpose", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["evidence_id", "version", "environment", "purpose", "body", "body_fingerprint"], "title": "NutritionSourceEvidence", "type": "object"}, "NutritionSourceInterval": {"additionalProperties": false, "properties": {"end": {"format": "date-time", "title": "End", "type": "string"}, "start": {"format": "date-time", "title": "Start", "type": "string"}}, "required": ["start", "end"], "title": "NutritionSourceInterval", "type": "object"}, "NutritionSynthesisDraft": {"additionalProperties": false, "properties": {"kind": {"const": "DRAFT", "title": "Kind", "type": "string"}, "rule": {"$ref": "#/$defs/NutritionSynthesisRuleBody"}}, "required": ["kind", "rule"], "title": "NutritionSynthesisDraft", "type": "object"}, "NutritionSynthesisOperation": {"additionalProperties": false, "description": "Closed instruction record. Inapplicable fields must be explicitly null/empty.", "properties": {"coefficient": {"anyOf": [{"$ref": "#/$defs/SynthesisRational"}, {"type": "null"}]}, "coefficients": {"items": {"$ref": "#/$defs/SynthesisRational"}, "maxItems": 64, "title": "Coefficients", "type": "array"}, "comparator": {"anyOf": [{"enum": ["UPPER_LT", "UPPER_LE", "LOWER_GT", "LOWER_GE", "CONTAINS"], "type": "string"}, {"type": "null"}], "title": "Comparator"}, "constraint_kind": {"anyOf": [{"enum": ["RANGE", "MINIMUM", "MAXIMUM", "TARGET"], "type": "string"}, {"type": "null"}], "title": "Constraint Kind"}, "endpoint": {"anyOf": [{"enum": ["lower", "upper", "center"], "type": "string"}, {"type": "null"}], "title": "Endpoint"}, "evidence_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Evidence Id", "type": "string"}, "id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Id", "type": "string"}, "inputs": {"items": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, "maxItems": 64, "title": "Inputs", "type": "array"}, "kind": {"enum": ["COPY_REFERENCE", "AFFINE_SAME_UNIT", "MAKE_CONSTRAINT", "CHECK_SUBSET", "FINITE_PERIOD_SUM", "REVIEWED_PERIOD_PROJECTION", "CHECK_DIRECTION", "SELECT_PRECISION_CASE"], "title": "Kind", "type": "string"}, "layer": {"anyOf": [{"enum": ["GOAL_PROTECTION", "DAILY_PROTECTION", "COMFORT", "WEEKLY_GOAL", "WEEKLY_CENTER"], "type": "string"}, {"type": "null"}], "title": "Layer"}, "offset": {"anyOf": [{"$ref": "#/$defs/SynthesisRational"}, {"type": "null"}]}, "reference_role": {"anyOf": [{"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, {"type": "null"}], "title": "Reference Role"}, "root_key": {"anyOf": [{"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, {"type": "null"}], "title": "Root Key"}, "temporal": {"anyOf": [{"$ref": "#/$defs/NutritionTemporalScope"}, {"type": "null"}]}}, "required": ["id", "kind", "inputs", "root_key", "endpoint", "reference_role", "coefficient", "offset", "constraint_kind", "layer", "temporal", "coefficients", "comparator", "evidence_id"], "title": "NutritionSynthesisOperation", "type": "object"}, "NutritionSynthesisPublication": {"additionalProperties": false, "properties": {"action": {"enum": ["PUBLISH", "SUPERSEDE", "RETIRE", "RETRACT"], "title": "Action", "type": "string"}, "body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "effective_at": {"format": "date-time", "title": "Effective At", "type": "string"}, "kind": {"const": "PUBLICATION", "title": "Kind", "type": "string"}, "predecessor_publication_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Predecessor Publication Id"}, "review_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Review Id"}, "revision_id": {"format": "uuid", "title": "Revision Id", "type": "string"}}, "required": ["kind", "revision_id", "body_fingerprint", "action", "review_id", "predecessor_publication_id", "effective_at"], "title": "NutritionSynthesisPublication", "type": "object"}, "NutritionSynthesisReview": {"additionalProperties": false, "properties": {"body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "decision": {"enum": ["APPROVE", "CANCEL"], "title": "Decision", "type": "string"}, "evidence_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Evidence Fingerprint", "type": "string"}, "kind": {"const": "REVIEW", "title": "Kind", "type": "string"}, "prior_review_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Prior Review Id"}, "revision_id": {"format": "uuid", "title": "Revision Id", "type": "string"}}, "required": ["kind", "revision_id", "body_fingerprint", "evidence_fingerprint", "decision", "prior_review_id"], "title": "NutritionSynthesisReview", "type": "object"}, "NutritionSynthesisRuleBody": {"additionalProperties": false, "properties": {"applicability": {"$ref": "#/$defs/NutritionRuleApplicability"}, "authored_version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Authored Version", "type": "string"}, "calendar_cells": {"items": {"$ref": "#/$defs/NutritionTemporalScope"}, "maxItems": 64, "minItems": 1, "title": "Calendar Cells", "type": "array"}, "calendar_evidence_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Calendar Evidence Id", "type": "string"}, "cases": {"items": {"$ref": "#/$defs/NutritionRuleCase"}, "maxItems": 16, "minItems": 1, "title": "Cases", "type": "array"}, "contract_version": {"const": "nutrition-synthesis-rule.v1", "default": "nutrition-synthesis-rule.v1", "title": "Contract Version", "type": "string"}, "effective": {"$ref": "#/$defs/NutritionSourceInterval"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence": {"items": {"$ref": "#/$defs/NutritionSourceEvidence"}, "maxItems": 32, "minItems": 1, "title": "Evidence", "type": "array"}, "family_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Family Id", "type": "string"}, "language_version": {"const": "FINITE_EXACT_V1", "title": "Language Version", "type": "string"}, "provider_id": {"format": "uuid", "title": "Provider Id", "type": "string"}, "purpose": {"const": "BOUNDED_COMPLETE_POLICY_V1", "title": "Purpose", "type": "string"}, "revision_id": {"format": "uuid", "title": "Revision Id", "type": "string"}}, "required": ["revision_id", "provider_id", "family_id", "authored_version", "language_version", "purpose", "environment", "effective", "applicability", "evidence", "calendar_evidence_id", "calendar_cells", "cases"], "title": "NutritionSynthesisRuleBody", "type": "object"}, "NutritionTemporalScope": {"additionalProperties": false, "properties": {"calendar": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Calendar", "type": "string"}, "interval": {"$ref": "#/$defs/NutritionSourceInterval"}, "kind": {"enum": ["EXACT_INTERVAL", "DAY", "WEEK"], "title": "Kind", "type": "string"}, "period_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Period Id", "type": "string"}, "timezone": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Timezone", "type": "string"}}, "required": ["kind", "period_id", "calendar", "timezone", "interval"], "title": "NutritionTemporalScope", "type": "object"}, "SynthesisRational": {"additionalProperties": false, "properties": {"denominator": {"exclusiveMinimum": 0, "maximum": 170141183460469231731687303715884105727, "title": "Denominator", "type": "integer"}, "numerator": {"maximum": 170141183460469231731687303715884105727, "minimum": -170141183460469231731687303715884105727, "title": "Numerator", "type": "integer"}}, "required": ["numerator", "denominator"], "title": "SynthesisRational", "type": "object"}}, "additionalProperties": false, "properties": {"body": {"discriminator": {"mapping": {"DRAFT": "#/$defs/NutritionSynthesisDraft", "PUBLICATION": "#/$defs/NutritionSynthesisPublication", "REVIEW": "#/$defs/NutritionSynthesisReview"}, "propertyName": "kind"}, "oneOf": [{"$ref": "#/$defs/NutritionSynthesisDraft"}, {"$ref": "#/$defs/NutritionSynthesisReview"}, {"$ref": "#/$defs/NutritionSynthesisPublication"}], "title": "Body"}, "event_id": {"format": "uuid", "title": "Event Id", "type": "string"}, "expected_revision": {"maximum": 9223372036854775807, "minimum": 0, "title": "Expected Revision", "type": "integer"}, "family_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Family Id", "type": "string"}, "idempotency_key": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Idempotency Key", "type": "string"}, "predecessor_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Predecessor Id"}, "provider_id": {"format": "uuid", "title": "Provider Id", "type": "string"}}, "required": ["provider_id", "family_id", "event_id", "expected_revision", "predecessor_id", "idempotency_key", "body"], "title": "NutritionSynthesisCommand", "type": "object"}, "NutritionSynthesisGrant": {"$defs": {"NutritionRuleApplicability": {"additionalProperties": false, "properties": {"guideline_body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Guideline Body Fingerprint", "type": "string"}, "guideline_revision_id": {"format": "uuid", "title": "Guideline Revision Id", "type": "string"}, "protocol_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Protocol Fingerprint", "type": "string"}, "root_family_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Root Family Id", "type": "string"}, "root_provider_id": {"format": "uuid", "title": "Root Provider Id", "type": "string"}, "scope_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Id", "type": "string"}, "scope_version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Version", "type": "string"}, "temporal": {"$ref": "#/$defs/NutritionTemporalScope"}}, "required": ["root_provider_id", "root_family_id", "guideline_revision_id", "guideline_body_fingerprint", "protocol_fingerprint", "scope_id", "scope_version", "temporal"], "title": "NutritionRuleApplicability", "type": "object"}, "NutritionSourceEvidence": {"additionalProperties": false, "properties": {"body": {"maxLength": 16384, "minLength": 1, "title": "Body", "type": "string"}, "body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Evidence Id", "type": "string"}, "purpose": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Purpose", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["evidence_id", "version", "environment", "purpose", "body", "body_fingerprint"], "title": "NutritionSourceEvidence", "type": "object"}, "NutritionSourceInterval": {"additionalProperties": false, "properties": {"end": {"format": "date-time", "title": "End", "type": "string"}, "start": {"format": "date-time", "title": "Start", "type": "string"}}, "required": ["start", "end"], "title": "NutritionSourceInterval", "type": "object"}, "NutritionTemporalScope": {"additionalProperties": false, "properties": {"calendar": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Calendar", "type": "string"}, "interval": {"$ref": "#/$defs/NutritionSourceInterval"}, "kind": {"enum": ["EXACT_INTERVAL", "DAY", "WEEK"], "title": "Kind", "type": "string"}, "period_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Period Id", "type": "string"}, "timezone": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Timezone", "type": "string"}}, "required": ["kind", "period_id", "calendar", "timezone", "interval"], "title": "NutritionTemporalScope", "type": "object"}}, "additionalProperties": false, "properties": {"action": {"enum": ["GRANT", "REVOKE"], "title": "Action", "type": "string"}, "applicability": {"$ref": "#/$defs/NutritionRuleApplicability"}, "capability": {"enum": ["SYNTHESIS_RULE_REVIEW", "SYNTHESIS_RULE_PUBLISH", "SYNTHESIS_RULE_WITHDRAW", "SYNTHESIS_SOURCE_READ", "SYNTHESIS_VALIDATOR_READ"], "title": "Capability", "type": "string"}, "effective": {"$ref": "#/$defs/NutritionSourceInterval"}, "evidence": {"$ref": "#/$defs/NutritionSourceEvidence"}, "expected_generation": {"maximum": 9223372036854775807, "minimum": 0, "title": "Expected Generation", "type": "integer"}, "family_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Family Id", "type": "string"}, "idempotency_key": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Idempotency Key", "type": "string"}, "predecessor_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Predecessor Id"}, "principal_id": {"format": "uuid", "title": "Principal Id", "type": "string"}, "provider_id": {"format": "uuid", "title": "Provider Id", "type": "string"}}, "required": ["provider_id", "family_id", "principal_id", "capability", "action", "applicability", "effective", "evidence", "expected_generation", "predecessor_id", "idempotency_key"], "title": "NutritionSynthesisGrant", "type": "object"}, "NutritionSynthesisPrincipalEnrollment": {"$defs": {"NutritionSourceEvidence": {"additionalProperties": false, "properties": {"body": {"maxLength": 16384, "minLength": 1, "title": "Body", "type": "string"}, "body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Evidence Id", "type": "string"}, "purpose": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Purpose", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["evidence_id", "version", "environment", "purpose", "body", "body_fingerprint"], "title": "NutritionSourceEvidence", "type": "object"}}, "additionalProperties": false, "properties": {"evidence": {"$ref": "#/$defs/NutritionSourceEvidence"}, "expected_generation": {"default": 0, "maximum": 9223372036854775807, "minimum": 0, "title": "Expected Generation", "type": "integer"}, "idempotency_key": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Idempotency Key", "type": "string"}, "previous_enrollment_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "default": null, "title": "Previous Enrollment Id"}, "role_name": {"maxLength": 63, "minLength": 1, "pattern": "^[^\\x00-\\x1f\\x7f]+$", "title": "Role Name", "type": "string"}, "service_id": {"anyOf": [{"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, {"type": "null"}], "title": "Service Id"}, "user_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "User Id"}, "verified_human_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Verified Human Id"}}, "required": ["role_name", "verified_human_id", "user_id", "service_id", "evidence", "idempotency_key"], "title": "NutritionSynthesisPrincipalEnrollment", "type": "object"}, "NutritionSynthesisProviderEnrollment": {"$defs": {"NutritionSourceEvidence": {"additionalProperties": false, "properties": {"body": {"maxLength": 16384, "minLength": 1, "title": "Body", "type": "string"}, "body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Evidence Id", "type": "string"}, "purpose": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Purpose", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["evidence_id", "version", "environment", "purpose", "body", "body_fingerprint"], "title": "NutritionSourceEvidence", "type": "object"}}, "additionalProperties": false, "properties": {"code": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Code", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence": {"$ref": "#/$defs/NutritionSourceEvidence"}, "expected_generation": {"maximum": 9223372036854775807, "minimum": 0, "title": "Expected Generation", "type": "integer"}, "idempotency_key": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Idempotency Key", "type": "string"}, "predecessor_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Predecessor Id"}, "provider_id": {"format": "uuid", "title": "Provider Id", "type": "string"}, "remit": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Remit", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["provider_id", "code", "version", "remit", "environment", "evidence", "expected_generation", "predecessor_id", "idempotency_key"], "title": "NutritionSynthesisProviderEnrollment", "type": "object"}}'::jsonb; BEGIN
 PERFORM menuto_nutrition_synthesis.bounds(c,131072);
 IF NOT schemas ? n THEN RAISE EXCEPTION 'Unknown command type'; END IF;
 PERFORM menuto_nutrition_synthesis.validate_json(c,schemas->n,schemas->n);
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.check_tree(c jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE x jsonb; n numeric; d numeric; BEGIN
 IF jsonb_typeof(c)='object' THEN
  IF c ? 'evidence_id' AND c ? 'body_fingerprint' THEN
   PERFORM menuto_nutrition_synthesis.evidence(c);
   IF c->>'environment'<>'TEST_ONLY' THEN RAISE EXCEPTION 'Production nutrition content gate CLOSED'; END IF;
  END IF;
  IF c ? 'numerator' AND c ? 'denominator' THEN
   n:=(c->>'numerator')::numeric; d:=(c->>'denominator')::numeric;
   IF d<=0 OR gcd(n,d)<>1 THEN RAISE EXCEPTION 'Reduced exact rational required'; END IF;
  END IF;
  IF (SELECT array_agg(key ORDER BY key) FROM jsonb_each(c))=ARRAY['end','start'] THEN PERFORM menuto_nutrition_synthesis.interval_ok(c); END IF;
  FOR x IN SELECT value FROM jsonb_each(c) LOOP PERFORM menuto_nutrition_synthesis.check_tree(x); END LOOP;
 ELSIF jsonb_typeof(c)='array' THEN
  FOR x IN SELECT value FROM jsonb_array_elements(c) LOOP PERFORM menuto_nutrition_synthesis.check_tree(x); END LOOP;
 END IF;
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.fact(kind text,j jsonb) RETURNS jsonb LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE f jsonb; BEGIN
 f:=jsonb_build_object('id',j->'id','command',j->'command','administrator',j->'administrator',
  'recorded_at',menuto_nutrition_synthesis.utc((j->>'recorded_at')::timestamptz),'recorded_order',j->'recorded_order','command_hash',j->'command_hash');
 IF kind='PRINCIPAL' THEN RETURN f||jsonb_build_object('database_oid',j->'database_oid','database_name',j->'database_name','role_oid',j->'role_oid','enrollment_root_id',j->'enrollment_root_id','generation',j->'generation'); END IF;
 RETURN f||jsonb_build_object('generation',j->'generation');
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.principal(s jsonb) RETURNS public.nutrition_synthesis_principals LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE p public.nutrition_synthesis_principals; BEGIN
 SELECT x.* INTO p FROM public.nutrition_synthesis_principals x JOIN public.nutrition_synthesis_principal_frontiers f ON f.head_id=x.id
  WHERE database_oid=(s->>'database_oid')::bigint AND database_name=s->>'database_name' AND role_oid=(s->>'role_oid')::bigint AND role_name=s->>'role_name';
 IF NOT FOUND THEN RAISE EXCEPTION 'Independently enrolled synthesis principal required' USING ERRCODE='42501'; END IF;
 RETURN p;
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.touch_principals(who uuid[]) RETURNS void LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE root uuid; BEGIN
 FOR root IN SELECT DISTINCT enrollment_root_id FROM public.nutrition_synthesis_principals WHERE id=ANY(who) ORDER BY enrollment_root_id LOOP
  UPDATE public.nutrition_synthesis_principal_frontiers SET lock_version=lock_version+1 WHERE enrollment_root_id=root;
  IF NOT FOUND THEN RAISE EXCEPTION 'Principal enrollment frontier missing'; END IF;
 END LOOP;
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.lock_provider(p uuid,f text) RETURNS public.nutrition_synthesis_streams LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE st public.nutrition_synthesis_streams; BEGIN
 -- Actual versioned lock row: stale RR writers fail serialization after revocation.
 UPDATE public.nutrition_synthesis_streams SET revision=revision+1 WHERE provider_id=p AND family_id='__AUTHORITY_LOCK__';
 IF NOT FOUND THEN RAISE EXCEPTION 'Provider lock anchor unavailable'; END IF;
 INSERT INTO public.nutrition_synthesis_streams VALUES(p,f,0,NULL,NULL) ON CONFLICT DO NOTHING;
 SELECT * INTO STRICT st FROM public.nutrition_synthesis_streams WHERE provider_id=p AND family_id=f FOR UPDATE;
 RETURN st;
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.permission(p uuid,f text,who uuid,cap text,at_time timestamptz) RETURNS public.nutrition_synthesis_grants LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE g public.nutrition_synthesis_grants; cp public.nutrition_synthesis_principals; BEGIN
 SELECT * INTO STRICT cp FROM public.nutrition_synthesis_principals WHERE id=who;
 IF NOT EXISTS(SELECT FROM public.nutrition_synthesis_principal_frontiers WHERE head_id=who) THEN RAISE EXCEPTION 'Principal enrollment replaced; exact new grants/review required' USING ERRCODE='42501'; END IF;
 IF cp.database_oid<>(SELECT oid::bigint FROM pg_database WHERE datname=current_database()) OR cp.database_name<>current_database()
  OR NOT EXISTS(SELECT FROM pg_roles WHERE oid=cp.role_oid AND rolname=cp.role_name) THEN RAISE EXCEPTION 'Current principal database/login identity stale' USING ERRCODE='42501'; END IF;
 PERFORM menuto_nutrition_synthesis.safe_role(cp.role_name,false);
 IF NOT EXISTS(SELECT FROM public.nutrition_synthesis_providers pr WHERE pr.provider_id=p AND (pr.administrator->>'database_oid')::oid=(SELECT oid FROM pg_database WHERE datname=current_database()) AND pr.administrator->>'database_name'=current_database()) THEN RAISE EXCEPTION 'Provider database identity unavailable'; END IF;
 SELECT * INTO g FROM public.nutrition_synthesis_grants WHERE provider_id=p AND family_id=f AND principal_id=who AND capability=cap ORDER BY generation DESC LIMIT 1;
 IF g.id IS NULL OR g.command->>'action'<>'GRANT' OR NOT ((g.command#>>'{effective,start}')::timestamptz<=at_time AND at_time<(g.command#>>'{effective,end}')::timestamptz) THEN
  RAISE EXCEPTION 'Current exact synthesis capability required' USING ERRCODE='42501'; END IF;
 RETURN g;
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.register_provider(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp SET lock_timeout='1s' AS $$
DECLARE s jsonb:=menuto_nutrition_synthesis.session_fact(true); r public.nutrition_synthesis_providers; old public.nutrition_synthesis_providers; h text; p uuid; BEGIN
 PERFORM menuto_nutrition_synthesis.check_command('NutritionSynthesisProviderEnrollment',c); PERFORM menuto_nutrition_synthesis.check_tree(c);
 IF c->>'environment'<>'TEST_ONLY' THEN RAISE EXCEPTION 'Production content gate CLOSED'; END IF;
 p:=(c->>'provider_id')::uuid;
 PERFORM pg_advisory_xact_lock(hashtextextended('nutrition-synthesis-provider:'||p::text,0));
 IF EXISTS(SELECT FROM public.nutrition_synthesis_providers WHERE provider_id=p) THEN PERFORM menuto_nutrition_synthesis.lock_provider(p,'__ENROLLMENT__'); END IF;
 s:=menuto_nutrition_synthesis.session_fact(true); h:=menuto_nutrition_synthesis.hash('nutrition-synthesis.provider-command.v1',c);
 SELECT * INTO r FROM public.nutrition_synthesis_providers WHERE actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF FOUND THEN IF r.command_hash<>h THEN RAISE EXCEPTION 'Provider idempotency conflict'; END IF; RETURN menuto_nutrition_synthesis.fact('PROVIDER',to_jsonb(r)); END IF;
 SELECT * INTO old FROM public.nutrition_synthesis_providers WHERE provider_id=p ORDER BY generation DESC LIMIT 1;
 IF coalesce(old.generation,0)<>(c->>'expected_generation')::bigint OR old.id IS DISTINCT FROM (c->>'predecessor_id')::uuid THEN RAISE EXCEPTION 'Provider CAS conflict' USING ERRCODE='40001'; END IF;
 IF coalesce(old.generation,0)>=64 THEN RAISE EXCEPTION 'Server provider history depth limit'; END IF;
 PERFORM menuto_nutrition_synthesis.retain_evidence(c->'evidence');
 INSERT INTO public.nutrition_synthesis_providers VALUES(gen_random_uuid(),c,s,clock_timestamp(),nextval('public.nutrition_synthesis_recorded_order'),h,(s->>'role_oid')::bigint,c->>'idempotency_key',p,coalesce(old.generation,0)+1,old.id) RETURNING * INTO r;
 INSERT INTO public.nutrition_synthesis_streams VALUES(p,'__AUTHORITY_LOCK__',0,NULL,NULL) ON CONFLICT DO NOTHING;
 RETURN menuto_nutrition_synthesis.fact('PROVIDER',to_jsonb(r));
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.enroll_principal(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp SET lock_timeout='1s' AS $$
DECLARE started timestamptz:=clock_timestamp(); s jsonb:=menuto_nutrition_synthesis.session_fact(true); r public.nutrition_synthesis_principals; old public.nutrition_synthesis_principals; login record; h text; new_id uuid:=gen_random_uuid(); root uuid; generation bigint; BEGIN
 PERFORM menuto_nutrition_synthesis.check_command('NutritionSynthesisPrincipalEnrollment',c); PERFORM menuto_nutrition_synthesis.check_tree(c);
 IF ((c->>'verified_human_id') IS NULL)=((c->>'service_id') IS NULL) OR ((c->>'service_id') IS NOT NULL AND (c->>'user_id') IS NOT NULL) THEN RAISE EXCEPTION 'Exact human/service binding required'; END IF;
 SELECT oid,rolname INTO STRICT login FROM pg_roles WHERE rolname=c->>'role_name';
 PERFORM menuto_nutrition_synthesis.safe_role(login.rolname,false);
 PERFORM pg_advisory_xact_lock(hashtextextended('nutrition-synthesis-principal:'||login.oid::text,0));
 IF c->>'previous_enrollment_id' IS NOT NULL THEN
  SELECT * INTO STRICT old FROM public.nutrition_synthesis_principals WHERE id=(c->>'previous_enrollment_id')::uuid;
  PERFORM menuto_nutrition_synthesis.touch_principals(ARRAY[old.id]);
 END IF;
 s:=menuto_nutrition_synthesis.session_fact(true); h:=menuto_nutrition_synthesis.hash('nutrition-synthesis.principal-command.v1',c);
 SELECT * INTO r FROM public.nutrition_synthesis_principals WHERE actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF FOUND THEN IF r.command_hash<>h THEN RAISE EXCEPTION 'Principal idempotency conflict'; END IF; RETURN menuto_nutrition_synthesis.fact('PRINCIPAL',to_jsonb(r)); END IF;
 IF old.id IS NULL THEN
  IF (c->>'expected_generation')::bigint<>0 THEN RAISE EXCEPTION 'Principal enrollment CAS conflict' USING ERRCODE='40001'; END IF;
  root:=new_id; generation:=1;
 ELSE
  IF (c->>'expected_generation')::bigint<>old.generation OR NOT EXISTS(SELECT FROM public.nutrition_synthesis_principal_frontiers WHERE head_id=old.id) THEN RAISE EXCEPTION 'Principal replacement CAS conflict' USING ERRCODE='40001'; END IF;
  root:=old.enrollment_root_id; generation:=old.generation+1;
  IF generation>64 THEN RAISE EXCEPTION 'Server principal history depth limit'; END IF;
 END IF;
 IF EXISTS(SELECT FROM public.nutrition_synthesis_principals WHERE database_oid=(s->>'database_oid')::bigint AND role_oid=login.oid AND role_name=login.rolname AND enrollment_root_id<>root) THEN RAISE EXCEPTION 'Actual credential cannot mint another logical author'; END IF;
 PERFORM menuto_nutrition_synthesis.retain_evidence(c->'evidence');
 INSERT INTO public.nutrition_synthesis_principals VALUES(new_id,c,s,clock_timestamp(),nextval('public.nutrition_synthesis_recorded_order'),h,(s->>'role_oid')::bigint,c->>'idempotency_key',
  (s->>'database_oid')::bigint,s->>'database_name',login.oid,login.rolname,(c->>'verified_human_id')::uuid,(c->>'user_id')::uuid,c->>'service_id',root,generation,old.id) RETURNING * INTO r;
 IF old.id IS NULL THEN
  INSERT INTO public.nutrition_synthesis_principal_frontiers VALUES(root,generation,r.id,menuto_nutrition_synthesis.hash('nutrition-synthesis.principal-fact.v1',menuto_nutrition_synthesis.fact('PRINCIPAL',to_jsonb(r))),0);
 ELSE UPDATE public.nutrition_synthesis_principal_frontiers SET revision=generation,head_id=r.id,head_hash=menuto_nutrition_synthesis.hash('nutrition-synthesis.principal-fact.v1',menuto_nutrition_synthesis.fact('PRINCIPAL',to_jsonb(r))) WHERE enrollment_root_id=root; END IF;
 PERFORM menuto_nutrition_synthesis.deadline(started);
 RETURN menuto_nutrition_synthesis.fact('PRINCIPAL',to_jsonb(r));
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.change_authority(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp SET lock_timeout='1s' AS $$
DECLARE s jsonb:=menuto_nutrition_synthesis.session_fact(true); r public.nutrition_synthesis_grants; old public.nutrition_synthesis_grants; cp public.nutrition_synthesis_principals; p uuid; f text; who uuid; cap text; h text; BEGIN
 PERFORM menuto_nutrition_synthesis.check_command('NutritionSynthesisGrant',c); PERFORM menuto_nutrition_synthesis.check_tree(c);
 p:=(c->>'provider_id')::uuid; f:=c->>'family_id'; who:=(c->>'principal_id')::uuid; cap:=c->>'capability';
 IF f LIKE '\_\_%' THEN RAISE EXCEPTION 'Reserved family identity'; END IF;
 PERFORM menuto_nutrition_synthesis.lock_provider(p,f); s:=menuto_nutrition_synthesis.session_fact(true);
 PERFORM menuto_nutrition_synthesis.touch_principals(ARRAY[who]);
 IF c->>'action'='GRANT' THEN
  SELECT * INTO STRICT cp FROM public.nutrition_synthesis_principals WHERE id=who;
  IF NOT EXISTS(SELECT FROM public.nutrition_synthesis_principal_frontiers WHERE head_id=who) THEN RAISE EXCEPTION 'Exact current principal enrollment required'; END IF;
  IF cp.database_oid<>(s->>'database_oid')::bigint OR cp.database_name<>s->>'database_name'
    OR NOT EXISTS(SELECT FROM pg_roles WHERE oid=cp.role_oid AND rolname=cp.role_name)
    OR (cap LIKE 'SYNTHESIS_RULE_%' AND cp.verified_human_id IS NULL) THEN RAISE EXCEPTION 'Current exact qualified target enrollment required' USING ERRCODE='42501'; END IF;
  PERFORM menuto_nutrition_synthesis.safe_role(cp.role_name,false);
 END IF;
 h:=menuto_nutrition_synthesis.hash('nutrition-synthesis.grant-command.v1',c);
 SELECT * INTO r FROM public.nutrition_synthesis_grants WHERE actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF FOUND THEN IF r.command_hash<>h THEN RAISE EXCEPTION 'Authority idempotency conflict'; END IF; RETURN menuto_nutrition_synthesis.fact('GRANT',to_jsonb(r)); END IF;
 SELECT * INTO old FROM public.nutrition_synthesis_grants WHERE provider_id=p AND family_id=f AND principal_id=who AND capability=cap ORDER BY generation DESC LIMIT 1;
 IF coalesce(old.generation,0)<>(c->>'expected_generation')::bigint OR old.id IS DISTINCT FROM (c->>'predecessor_id')::uuid THEN RAISE EXCEPTION 'Authority CAS conflict' USING ERRCODE='40001'; END IF;
 IF coalesce(old.generation,0)>=64 THEN RAISE EXCEPTION 'Server authority history depth limit'; END IF;
 PERFORM menuto_nutrition_synthesis.retain_evidence(c->'evidence');
 INSERT INTO public.nutrition_synthesis_grants VALUES(gen_random_uuid(),c,s,clock_timestamp(),nextval('public.nutrition_synthesis_recorded_order'),h,(s->>'role_oid')::bigint,c->>'idempotency_key',p,f,who,cap,coalesce(old.generation,0)+1,old.id) RETURNING * INTO r;
 RETURN menuto_nutrition_synthesis.fact('GRANT',to_jsonb(r));
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.check_rule(b jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE cs jsonb; o jsonb; seen text[]; refs text[]; ids text[]; k text; fields text[]; expected text[]; arity int; cell jsonb; end_at timestamptz; interval_body jsonb; types jsonb; expected_type text; ref text; ref_index int; BEGIN
 PERFORM menuto_nutrition_synthesis.check_tree(b);
 IF b->>'environment'<>'TEST_ONLY' THEN RAISE EXCEPTION 'Production content gate CLOSED'; END IF;
 SELECT array_agg(e->>'evidence_id' ORDER BY ord) INTO ids FROM jsonb_array_elements(b->'evidence') WITH ORDINALITY x(e,ord);
 IF ids IS DISTINCT FROM (SELECT array_agg(DISTINCT id ORDER BY id) FROM unnest(ids) id) OR NOT b->>'calendar_evidence_id'=ANY(ids) THEN RAISE EXCEPTION 'Canonical evidence manifest required'; END IF;
 interval_body:=b#>'{applicability,temporal,interval}'; end_at:=(interval_body->>'start')::timestamptz;
 FOR cell IN SELECT value FROM jsonb_array_elements(b->'calendar_cells') LOOP
  IF (cell#>>'{interval,start}')::timestamptz<>end_at OR cell->>'calendar'<>b#>>'{applicability,temporal,calendar}' OR cell->>'timezone'<>b#>>'{applicability,temporal,timezone}' THEN RAISE EXCEPTION 'Calendar cells must cover exact retained mapping'; END IF;
  end_at:=(cell#>>'{interval,end}')::timestamptz;
 END LOOP;
 IF end_at<>(interval_body->>'end')::timestamptz THEN RAISE EXCEPTION 'Incomplete calendar coverage'; END IF;
 IF (SELECT count(*) FROM jsonb_array_elements(b->'cases'))<>(SELECT count(DISTINCT v->>'id') FROM jsonb_array_elements(b->'cases') v) THEN RAISE EXCEPTION 'Duplicate rule case'; END IF;
 FOR cs IN SELECT value FROM jsonb_array_elements(b->'cases') LOOP
  seen:=ARRAY[]::text[];
  types:='{}'::jsonb;
  FOR k IN SELECT unnest(ARRAY['daily_root_keys','comfort_root_keys','required_claims']) LOOP
   IF (SELECT count(*) FROM jsonb_array_elements(cs->k))<>(SELECT count(DISTINCT value) FROM jsonb_array_elements(cs->k)) THEN RAISE EXCEPTION 'Duplicate required manifest'; END IF;
  END LOOP;
  FOR o IN SELECT value FROM jsonb_array_elements(cs->'operations') LOOP
   IF o->>'id'=ANY(seen) OR NOT o->>'evidence_id'=ANY(ids) THEN RAISE EXCEPTION 'Duplicate operation or missing evidence'; END IF;
   SELECT coalesce(array_agg(value),ARRAY[]::text[]) INTO refs FROM jsonb_array_elements_text(o->'inputs');
   IF NOT refs<@seen THEN RAISE EXCEPTION 'Forward reference/recursion forbidden'; END IF;
   seen:=array_append(seen,o->>'id'); arity:=cardinality(refs);
   SELECT coalesce(array_agg(key ORDER BY key),ARRAY[]::text[]) INTO fields FROM jsonb_each(o) WHERE value<>'null'::jsonb AND key IN('root_key','endpoint','reference_role','coefficient','offset','constraint_kind','layer','temporal','comparator');
   CASE o->>'kind'
    WHEN 'COPY_REFERENCE' THEN expected:=ARRAY['endpoint','reference_role','root_key']; IF arity<>0 THEN RAISE EXCEPTION 'Operand arity'; END IF;
    WHEN 'AFFINE_SAME_UNIT' THEN expected:=ARRAY['coefficient','offset']; IF arity<>1 THEN RAISE EXCEPTION 'Operand arity'; END IF;
    WHEN 'MAKE_CONSTRAINT' THEN expected:=ARRAY['constraint_kind','layer','root_key','temporal']; IF arity<>(CASE WHEN o->>'constraint_kind'='RANGE' THEN 2 ELSE 1 END) THEN RAISE EXCEPTION 'Operand arity'; END IF;
     IF (o->>'constraint_kind'='TARGET')<>(o->>'layer'='WEEKLY_CENTER') OR (o->>'layer'='COMFORT' AND o->>'constraint_kind'<>'RANGE') THEN RAISE EXCEPTION 'TARGET remains a soft center; comfort requires explicit band'; END IF;
    WHEN 'CHECK_SUBSET' THEN expected:=ARRAY[]::text[]; IF arity<>2 THEN RAISE EXCEPTION 'Operand arity'; END IF;
    WHEN 'FINITE_PERIOD_SUM' THEN expected:=ARRAY['temporal']; IF arity<1 OR arity<>jsonb_array_length(o->'coefficients') OR EXISTS(SELECT FROM jsonb_array_elements(o->'coefficients') x WHERE (x->>'numerator')::numeric<=0) THEN RAISE EXCEPTION 'Positive exact period coefficients required'; END IF;
    WHEN 'REVIEWED_PERIOD_PROJECTION' THEN expected:=ARRAY['coefficient','offset','temporal']; IF arity<>1 THEN RAISE EXCEPTION 'Operand arity'; END IF;
    WHEN 'CHECK_DIRECTION' THEN expected:=ARRAY['comparator']; IF arity<>2 THEN RAISE EXCEPTION 'Operand arity'; END IF;
    WHEN 'SELECT_PRECISION_CASE' THEN expected:=ARRAY[]::text[]; IF arity<>3 THEN RAISE EXCEPTION 'Operand arity'; END IF;
    ELSE RAISE EXCEPTION 'Unsupported finite language';
   END CASE;
   IF fields<>expected OR (o->>'kind'<>'FINITE_PERIOD_SUM' AND jsonb_array_length(o->'coefficients')<>0) THEN RAISE EXCEPTION 'Closed instruction shape required'; END IF;
   ref_index:=0;
   FOREACH ref IN ARRAY refs LOOP
    ref_index:=ref_index+1;
    expected_type:=CASE WHEN o->>'kind' IN('CHECK_SUBSET','SELECT_PRECISION_CASE') OR (o->>'kind'='CHECK_DIRECTION' AND ref_index=1) THEN 'CONSTRAINT' ELSE 'NUMBER' END;
    IF (types->>ref) IS DISTINCT FROM expected_type THEN RAISE EXCEPTION 'Finite operand type mismatch'; END IF;
   END LOOP;
   types:=types||jsonb_build_object(o->>'id',CASE WHEN o->>'kind' IN('CHECK_SUBSET','CHECK_DIRECTION') THEN 'BOOLEAN' WHEN o->>'kind' IN('MAKE_CONSTRAINT','SELECT_PRECISION_CASE') THEN 'CONSTRAINT' ELSE 'NUMBER' END);
  END LOOP;
  IF EXISTS(SELECT FROM jsonb_array_elements_text(cs->'required_claims') x WHERE NOT x=ANY(seen)) THEN RAISE EXCEPTION 'Unknown mandatory claim'; END IF;
  IF EXISTS(SELECT FROM jsonb_array_elements_text(cs->'required_claims') x WHERE (types->>x) IS DISTINCT FROM 'CONSTRAINT') THEN RAISE EXCEPTION 'Mandatory claim is not a constraint'; END IF;
 END LOOP;
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.retain_evidence(e jsonb) RETURNS void LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE old public.nutrition_synthesis_evidence; BEGIN
 PERFORM menuto_nutrition_synthesis.evidence(e);
 INSERT INTO public.nutrition_synthesis_evidence VALUES(e->>'evidence_id',e,e->>'body_fingerprint') ON CONFLICT DO NOTHING;
 SELECT * INTO STRICT old FROM public.nutrition_synthesis_evidence WHERE evidence_id=e->>'evidence_id';
 IF old.body<>e THEN RAISE EXCEPTION 'Conflicting retained evidence identity'; END IF;
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.record_fact(r public.nutrition_synthesis_receipts) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
 SELECT jsonb_build_object('id',r.id,'command',r.command,'principal_id',r.principal_id,'grant_id',r.grant_id,'session',r.actor,
  'sequence',r.sequence,'previous_hash',r.previous_hash,'recorded_at',menuto_nutrition_synthesis.utc(r.recorded_at),'recorded_order',r.recorded_order,'command_hash',r.command_hash,'event_hash',r.event_hash)
$$;

CREATE FUNCTION menuto_nutrition_synthesis.apply_publication(segments jsonb,id uuid,b jsonb,rule jsonb) RETURNS jsonb LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE lo timestamptz:=(b->>'effective_at')::timestamptz; hi timestamptz:=(rule#>>'{effective,end}')::timestamptz;
 seg jsonb; a timestamptz; z timestamptz; out jsonb:='[]'; prior text:=b->>'predecessor_publication_id'; found_target boolean:=false;
 action text:=b->>'action'; BEGIN
 IF (action='PUBLISH')<>(prior IS NULL) THEN RAISE EXCEPTION 'Exact publication predecessor required'; END IF;
 IF action IN('PUBLISH','SUPERSEDE') AND (lo<(rule#>>'{effective,start}')::timestamptz OR lo>=hi) THEN RAISE EXCEPTION 'Publication outside reviewed interval'; END IF;
 FOR seg IN SELECT value FROM jsonb_array_elements(segments) LOOP
  a:=(seg->>'start')::timestamptz; z:=(seg->>'end')::timestamptz;
  IF action='PUBLISH' THEN
   IF a<hi AND z>lo THEN RAISE EXCEPTION 'PUBLISH cannot hide overlapping history'; END IF;
   out:=out||jsonb_build_array(seg);
  ELSIF seg->>'publication_id'=prior AND z>lo THEN
   found_target:=true;
   IF a<lo THEN out:=out||jsonb_build_array(seg||jsonb_build_object('end',menuto_nutrition_synthesis.utc(lo))); END IF;
   IF action IN('RETIRE','RETRACT') THEN
    IF seg->>'revision_id'<>b->>'revision_id' THEN RAISE EXCEPTION 'Withdrawal revision mismatch'; END IF;
    out:=out||jsonb_build_array(seg||jsonb_build_object('start',menuto_nutrition_synthesis.utc(greatest(a,lo)),
      'publication_id',id,'active',false,'cause','RULE_WITHDRAWN'));
   ELSIF z>hi THEN
    out:=out||jsonb_build_array(seg||jsonb_build_object('start',menuto_nutrition_synthesis.utc(hi),
      'publication_id',id,'active',false,'cause','RULE_OUTSIDE_EFFECTIVE_RANGE'));
   END IF;
  ELSE
   IF action='SUPERSEDE' AND a<hi AND z>lo THEN RAISE EXCEPTION 'Unrelated scheduled publication overlaps'; END IF;
   out:=out||jsonb_build_array(seg);
  END IF;
 END LOOP;
 IF action='SUPERSEDE' AND EXISTS(SELECT FROM jsonb_array_elements(segments) s WHERE s->>'publication_id'=prior AND (s->>'end')::timestamptz=lo) THEN found_target:=true; END IF;
 IF action<>'PUBLISH' AND NOT found_target THEN RAISE EXCEPTION 'Exact applicable publication predecessor required'; END IF;
 IF action IN('PUBLISH','SUPERSEDE') THEN
  out:=out||jsonb_build_array(jsonb_build_object('start',menuto_nutrition_synthesis.utc(lo),'end',menuto_nutrition_synthesis.utc(hi),
   'publication_id',id,'revision_id',b->'revision_id','active',true,'cause',NULL));
 END IF;
 IF jsonb_array_length(out)>64 THEN RAISE EXCEPTION 'Server publication interval limit; no truncation'; END IF;
 SELECT coalesce(jsonb_agg(s ORDER BY (s->>'start')::timestamptz),'[]') INTO out FROM jsonb_array_elements(out) s;
 RETURN out;
END $$;
CREATE FUNCTION menuto_nutrition_synthesis.publication_timeline(p uuid,f text) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE segments jsonb:='[]'; r record; BEGIN
 FOR r IN SELECT x.id,v.body,d.body rule FROM public.nutrition_synthesis_receipts x
  JOIN public.nutrition_synthesis_publications v ON v.id=x.id JOIN public.nutrition_synthesis_drafts d ON d.revision_id=v.revision_id
  WHERE x.provider_id=p AND x.family_id=f ORDER BY x.sequence LOOP
  segments:=menuto_nutrition_synthesis.apply_publication(segments,r.id,r.body,r.rule);
 END LOOP;
 RETURN segments;
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.append(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp SET lock_timeout='1s' AS $$
DECLARE started timestamptz:=clock_timestamp(); s jsonb:=menuto_nutrition_synthesis.session_fact(false);
 p public.nutrition_synthesis_principals; st public.nutrition_synthesis_streams;
 g public.nutrition_synthesis_grants; r public.nutrition_synthesis_receipts;
 d public.nutrition_synthesis_drafts; rv public.nutrition_synthesis_reviews;
 previous public.nutrition_synthesis_publications; reviewer public.nutrition_synthesis_principals;
 reviewer_id uuid; reviewer_grant public.nutrition_synthesis_grants; reviewed_grant uuid; b jsonb:=c->'body'; cap text; h text; e jsonb; at_time timestamptz; BEGIN
 PERFORM menuto_nutrition_synthesis.check_command('NutritionSynthesisCommand',c);
 PERFORM menuto_nutrition_synthesis.check_tree(c);
 IF c->>'family_id' LIKE '\_\_%' THEN RAISE EXCEPTION 'Reserved family identity'; END IF;
 st:=menuto_nutrition_synthesis.lock_provider((c->>'provider_id')::uuid,c->>'family_id');
 p:=menuto_nutrition_synthesis.principal(s);
 IF b->>'kind'='PUBLICATION' AND b->>'action' IN('PUBLISH','SUPERSEDE') THEN
  SELECT x.principal_id INTO reviewer_id FROM public.nutrition_synthesis_receipts x
   JOIN public.nutrition_synthesis_reviews v ON v.id=x.id WHERE v.id=(b->>'review_id')::uuid;
 END IF;
 -- Actor-frontier locks are globally ordered after the provider lock. Enrollment
 -- replacement and stale RR writers therefore serialize with publication/retries.
 PERFORM menuto_nutrition_synthesis.touch_principals(ARRAY[p.id,reviewer_id]);
 s:=menuto_nutrition_synthesis.session_fact(false);
 p:=menuto_nutrition_synthesis.principal(s); at_time:=clock_timestamp();
 cap:=CASE WHEN b->>'kind' IN('DRAFT','REVIEW') THEN 'SYNTHESIS_RULE_REVIEW'
  WHEN b->>'action' IN('RETIRE','RETRACT') THEN 'SYNTHESIS_RULE_WITHDRAW' ELSE 'SYNTHESIS_RULE_PUBLISH' END;
 g:=menuto_nutrition_synthesis.permission(st.provider_id,st.family_id,p.id,cap,at_time);
 IF p.verified_human_id IS NULL THEN RAISE EXCEPTION 'Verified human author required' USING ERRCODE='42501'; END IF;
 IF b->>'kind'='DRAFT' THEN
  PERFORM menuto_nutrition_synthesis.check_rule(b->'rule');
  IF b#>>'{rule,provider_id}'<>c->>'provider_id' OR b#>>'{rule,family_id}'<>c->>'family_id'
    OR b#>'{rule,applicability}'<>g.command->'applicability' THEN RAISE EXCEPTION 'Exact rule-local remit required'; END IF;
 ELSE
  SELECT * INTO STRICT d FROM public.nutrition_synthesis_drafts WHERE revision_id=(b->>'revision_id')::uuid;
  IF d.body_fingerprint<>b->>'body_fingerprint' OR d.body->>'provider_id'<>c->>'provider_id'
    OR d.body->>'family_id'<>c->>'family_id' OR d.body->'applicability'<>g.command->'applicability' THEN
   RAISE EXCEPTION 'Exact immutable body/remit required'; END IF;
  IF b->>'kind'='REVIEW' THEN
   IF d.evidence_fingerprint<>b->>'evidence_fingerprint' THEN RAISE EXCEPTION 'Exact review evidence required'; END IF;
   IF b->>'decision'='CANCEL' AND NOT EXISTS(SELECT FROM public.nutrition_synthesis_reviews v
    JOIN public.nutrition_synthesis_receipts x ON x.id=v.id WHERE v.id=(b->>'prior_review_id')::uuid
    AND v.revision_id=d.revision_id AND x.principal_id=p.id AND v.body->>'decision'='APPROVE') THEN RAISE EXCEPTION 'Exact own prior review required'; END IF;
   IF b->>'decision'='APPROVE' AND b->>'prior_review_id' IS NOT NULL THEN RAISE EXCEPTION 'Unexpected prior review'; END IF;
  ELSIF b->>'action' IN('PUBLISH','SUPERSEDE') THEN
   SELECT * INTO STRICT rv FROM public.nutrition_synthesis_reviews WHERE id=(b->>'review_id')::uuid
    AND revision_id=d.revision_id AND body->>'decision'='APPROVE';
   IF EXISTS(SELECT FROM public.nutrition_synthesis_reviews WHERE body->>'prior_review_id'=rv.id::text AND body->>'decision'='CANCEL') THEN RAISE EXCEPTION 'Cancelled review'; END IF;
   SELECT q.* INTO STRICT reviewer FROM public.nutrition_synthesis_principals q
    JOIN public.nutrition_synthesis_receipts x ON x.principal_id=q.id WHERE x.id=rv.id;
   reviewer_grant:=menuto_nutrition_synthesis.permission(st.provider_id,st.family_id,reviewer.id,'SYNTHESIS_RULE_REVIEW',at_time);
   SELECT grant_id INTO STRICT reviewed_grant FROM public.nutrition_synthesis_receipts WHERE id=rv.id;
   IF reviewer_grant.id<>reviewed_grant THEN RAISE EXCEPTION 'Review qualification changed; fresh review required'; END IF;
   IF reviewer.verified_human_id IS NULL OR reviewer.verified_human_id=p.verified_human_id THEN RAISE EXCEPTION 'Different verified reviewer/publisher humans required'; END IF;
   IF (b->>'effective_at')::timestamptz<(d.body#>>'{effective,start}')::timestamptz OR (b->>'effective_at')::timestamptz>=(d.body#>>'{effective,end}')::timestamptz THEN RAISE EXCEPTION 'Publication outside reviewed interval'; END IF;
  ELSIF b->>'review_id' IS NOT NULL THEN RAISE EXCEPTION 'Withdrawal does not manufacture review authority'; END IF;
 END IF;
 h:=menuto_nutrition_synthesis.hash('nutrition-synthesis.command.v1',c);
 -- ALL current identity, remit, qualification, review and separation checks above
 -- precede an old receipt. Historical receipts never mint present authority.
 SELECT * INTO r FROM public.nutrition_synthesis_receipts WHERE principal_id=p.id AND idempotency_key=c->>'idempotency_key';
 IF FOUND THEN IF r.command_hash<>h THEN RAISE EXCEPTION 'Idempotency body/actor/scope conflict'; END IF;
  PERFORM menuto_nutrition_synthesis.deadline(started); RETURN menuto_nutrition_synthesis.record_fact(r); END IF;
 IF st.revision>=64 THEN RAISE EXCEPTION 'Server history depth limit; all-or-error'; END IF;
 IF st.revision<>(c->>'expected_revision')::bigint OR st.head_id IS DISTINCT FROM (c->>'predecessor_id')::uuid THEN RAISE EXCEPTION 'Source CAS conflict' USING ERRCODE='40001'; END IF;
 IF b->>'kind'='DRAFT' THEN
  FOR e IN SELECT value FROM jsonb_array_elements(b#>'{rule,evidence}') LOOP PERFORM menuto_nutrition_synthesis.retain_evidence(e); END LOOP;
 ELSIF b->>'kind'='PUBLICATION' THEN
  PERFORM menuto_nutrition_synthesis.apply_publication(menuto_nutrition_synthesis.publication_timeline(st.provider_id,st.family_id),(c->>'event_id')::uuid,b,d.body);
 END IF;
 r.id:=(c->>'event_id')::uuid; r.provider_id:=st.provider_id; r.family_id:=st.family_id; r.sequence:=st.revision+1;
 r.principal_id:=p.id; r.grant_id:=g.id; r.actor:=s; r.command:=c; r.previous_id:=st.head_id; r.previous_hash:=st.head_hash;
 r.recorded_at:=at_time; r.recorded_order:=nextval('public.nutrition_synthesis_recorded_order');
 r.command_hash:=h; r.idempotency_key:=c->>'idempotency_key';
 r.event_hash:=menuto_nutrition_synthesis.hash('nutrition-synthesis.event.v1',menuto_nutrition_synthesis.record_fact(r)-'event_hash');
 INSERT INTO public.nutrition_synthesis_receipts SELECT r.*;
 CASE b->>'kind'
  WHEN 'DRAFT' THEN INSERT INTO public.nutrition_synthesis_drafts VALUES(r.id,(b#>>'{rule,revision_id}')::uuid,
   menuto_nutrition_synthesis.hash('nutrition-synthesis.rule.v1',b->'rule'),
   menuto_nutrition_synthesis.hash('nutrition-synthesis.evidence-manifest.v1',b#>'{rule,evidence}'),b->'rule');
  WHEN 'REVIEW' THEN INSERT INTO public.nutrition_synthesis_reviews VALUES(r.id,(b->>'revision_id')::uuid,b);
  WHEN 'PUBLICATION' THEN INSERT INTO public.nutrition_synthesis_publications VALUES(r.id,(b->>'revision_id')::uuid,b);
 END CASE;
 UPDATE public.nutrition_synthesis_streams SET revision=r.sequence,head_id=r.id,head_hash=r.event_hash WHERE provider_id=st.provider_id AND family_id=st.family_id;
 PERFORM menuto_nutrition_synthesis.deadline(started);
 RETURN menuto_nutrition_synthesis.record_fact(r);
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.capture(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp SET lock_timeout='1s' AS $$
DECLARE started timestamptz:=clock_timestamp(); s jsonb:=menuto_nutrition_synthesis.session_fact(false); p public.nutrition_synthesis_principals;
 g public.nutrition_synthesis_grants; pr public.nutrition_synthesis_providers; st public.nutrition_synthesis_streams;
 rq jsonb:=c->'root_request'; fr jsonb:=c->'root_frame'; rr jsonb; pp jsonb; gg jsonb; principals jsonb; principal_heads jsonb; frontiers jsonb; frame jsonb; witness jsonb:=NULL; result jsonb; n bigint; at_time timestamptz:=clock_timestamp(); BEGIN
 PERFORM menuto_nutrition_synthesis.check_command('NutritionSynthesisCaptureCommand',c);
 IF current_setting('transaction_isolation') NOT IN('repeatable read','serializable') OR current_setting('transaction_read_only')<>'on' OR txid_current_if_assigned() IS NOT NULL THEN RAISE EXCEPTION 'Clean caller-owned read-only repeatable cut required'; END IF;
 p:=menuto_nutrition_synthesis.principal(s);
 g:=menuto_nutrition_synthesis.permission((c#>>'{selection,provider_id}')::uuid,c#>>'{selection,family_id}',p.id,
  CASE WHEN rq->>'purpose'='VALIDATOR' THEN 'SYNTHESIS_VALIDATOR_READ' ELSE 'SYNTHESIS_SOURCE_READ' END,at_time);
 IF g.command->'applicability' IS DISTINCT FROM jsonb_build_object('root_provider_id',rq->'provider_id','root_family_id',rq->'family_id','guideline_revision_id',rq->'guideline_revision_id','guideline_body_fingerprint',rq->'guideline_body_fingerprint','protocol_fingerprint',rq->'protocol_fingerprint','scope_id',rq->'scope_id','scope_version',rq->'scope_version','temporal',rq->'temporal') THEN RAISE EXCEPTION 'Reader exact applicability required'; END IF;
 IF fr->'session'<>s OR fr->>'backend_pid'<>pg_backend_pid()::text OR fr->>'mvcc_snapshot'<>pg_current_snapshot()::text OR fr->>'isolation'<>upper(current_setting('transaction_isolation')) OR fr->>'endpoint'<>(host(inet_server_addr())||':'||inet_server_port()::text) THEN RAISE EXCEPTION 'Actual root/rule capture frame mismatch'; END IF;
 -- The frozen root path has independently authorized this exact-subject read.
 -- Precision is household planning intent, never member-goal authorship authority.
 IF c->'precision'<>'null'::jsonb THEN
  IF p.user_id IS NULL OR c#>>'{precision,actor_user_id}'<>p.user_id::text OR c#>'{precision,subject}'<>rq->'subject' OR NOT EXISTS(
   SELECT FROM public.memberships m WHERE m.user_id=p.user_id AND m.household_id=(rq#>>'{subject,household_id}')::uuid AND m.role IN('OWNER','EDITOR')) THEN RAISE EXCEPTION 'Authenticated exact-household precision actor required'; END IF;
  SELECT jsonb_build_object('subject',rq->'subject','actor_user_id',p.user_id,'membership_id',m.id,'actor_member_id',m.member_id,'role',m.role) INTO witness
   FROM public.memberships m
   WHERE m.user_id=p.user_id AND m.household_id=(rq#>>'{subject,household_id}')::uuid;
 END IF;
 SELECT * INTO STRICT pr FROM public.nutrition_synthesis_providers WHERE provider_id=(c#>>'{selection,provider_id}')::uuid ORDER BY generation DESC LIMIT 1;
 SELECT * INTO st FROM public.nutrition_synthesis_streams WHERE provider_id=pr.provider_id AND family_id=c#>>'{selection,family_id}';
 SELECT coalesce(jsonb_agg(menuto_nutrition_synthesis.record_fact(x) ORDER BY sequence),'[]') INTO rr FROM public.nutrition_synthesis_receipts x WHERE provider_id=pr.provider_id AND family_id=c#>>'{selection,family_id}';
 SELECT coalesce(jsonb_agg(menuto_nutrition_synthesis.fact('PROVIDER',to_jsonb(x)) ORDER BY generation),'[]') INTO pp FROM public.nutrition_synthesis_providers x WHERE provider_id=pr.provider_id;
 SELECT coalesce(jsonb_agg(menuto_nutrition_synthesis.fact('GRANT',to_jsonb(x)) ORDER BY recorded_order),'[]') INTO gg FROM public.nutrition_synthesis_grants x WHERE provider_id=pr.provider_id AND family_id=c#>>'{selection,family_id}';
 SELECT coalesce(jsonb_agg(menuto_nutrition_synthesis.fact('PRINCIPAL',to_jsonb(x)) ORDER BY recorded_order),'[]') INTO principals FROM public.nutrition_synthesis_principals x WHERE enrollment_root_id IN(
  SELECT enrollment_root_id FROM public.nutrition_synthesis_principals WHERE id=p.id OR id IN(SELECT (v#>>'{command,principal_id}')::uuid FROM jsonb_array_elements(gg) v));
 SELECT jsonb_agg(jsonb_build_object('enrollment_root_id',enrollment_root_id,'revision',revision,'head_id',head_id,'head_hash',head_hash) ORDER BY enrollment_root_id)
 INTO principal_heads FROM public.nutrition_synthesis_principal_frontiers WHERE enrollment_root_id IN(SELECT (v->>'enrollment_root_id')::uuid FROM jsonb_array_elements(principals) v);
 SELECT jsonb_agg(jsonb_build_object('principal_id',who,'capability',cap,'revision',coalesce(frontier_grant.generation,0),'head_id',frontier_grant.id,
   'head_hash',CASE WHEN frontier_grant.id IS NULL THEN NULL ELSE menuto_nutrition_synthesis.hash('nutrition-synthesis.grant-fact.v1',menuto_nutrition_synthesis.fact('GRANT',to_jsonb(frontier_grant))) END) ORDER BY who,cap)
 INTO frontiers FROM (SELECT (v->>'id')::uuid who FROM jsonb_array_elements(principals) v) people
 CROSS JOIN unnest(ARRAY['SYNTHESIS_RULE_REVIEW','SYNTHESIS_RULE_PUBLISH','SYNTHESIS_RULE_WITHDRAW','SYNTHESIS_SOURCE_READ','SYNTHESIS_VALIDATOR_READ']) cap
 LEFT JOIN LATERAL(SELECT x.* FROM public.nutrition_synthesis_grants x WHERE x.provider_id=pr.provider_id
  AND x.family_id=c#>>'{selection,family_id}' AND x.principal_id=who AND x.capability=cap ORDER BY x.generation DESC LIMIT 1) frontier_grant ON true;
 n:=jsonb_array_length(rr)+jsonb_array_length(pp)+jsonb_array_length(gg)+jsonb_array_length(principals)+jsonb_array_length(frontiers)+jsonb_array_length(principal_heads);
 IF n>4096 OR jsonb_array_length(rr)>64 OR jsonb_array_length(pp)>64 OR jsonb_array_length(principals)>512 OR jsonb_array_length(gg)>4096 THEN RAISE EXCEPTION 'Server capture/history limit; no truncation'; END IF;
 frame:=jsonb_build_object('session',s,'reader_principal_id',p.id,'reader_subject_witness',fr->'reader_subject_witness','reader_grant_id',g.id,'endpoint',fr->'endpoint',
  'backend_pid',pg_backend_pid(),'mvcc_snapshot',pg_current_snapshot()::text,'transaction_id','UNASSIGNED_READ_ONLY',
  'isolation',upper(current_setting('transaction_isolation')),'read_only',true,'started_at',menuto_nutrition_synthesis.utc(started),'completed_at',menuto_nutrition_synthesis.utc(clock_timestamp()),
  'provider_enrollment_id',pr.id,'row_count',n,'absence_stream_keys',CASE WHEN st.head_id IS NULL THEN jsonb_build_array(menuto_nutrition_synthesis.hash('nutrition-synthesis.absence.v1',c->'selection')) ELSE '[]'::jsonb END);
 result:=jsonb_build_object('provider_facts',pp,'principal_facts',principals,'principal_frontiers',principal_heads,'grant_facts',gg,'authority_frontiers',frontiers,'records',rr,'frame',frame,
  'frontier_revision',coalesce(st.revision,0),'frontier_id',st.head_id,'frontier_hash',st.head_hash,'precision_witness',witness);
 PERFORM menuto_nutrition_synthesis.bounds(result,4194304); PERFORM menuto_nutrition_synthesis.deadline(started); RETURN result;
END $$;

CREATE FUNCTION menuto_nutrition_synthesis.write_guard() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$ BEGIN
 IF current_user<>'menuto_nutrition_synthesis_owner' THEN RAISE EXCEPTION 'Protected synthesis path only' USING ERRCODE='42501'; END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION menuto_nutrition_synthesis.immutable() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$ BEGIN RAISE EXCEPTION 'Append-only synthesis history'; END $$;
CREATE FUNCTION menuto_nutrition_synthesis.coherent() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition_synthesis,pg_temp AS $$
DECLARE p uuid; f text; st public.nutrition_synthesis_streams; r public.nutrition_synthesis_receipts; prev public.nutrition_synthesis_receipts; children int;
 pf public.nutrition_synthesis_principal_frontiers; cp public.nutrition_synthesis_principals; prior_cp public.nutrition_synthesis_principals; BEGIN
 IF TG_TABLE_NAME IN('nutrition_synthesis_principals','nutrition_synthesis_principal_frontiers') THEN
  SELECT * INTO STRICT pf FROM public.nutrition_synthesis_principal_frontiers WHERE enrollment_root_id=NEW.enrollment_root_id;
  SELECT * INTO STRICT cp FROM public.nutrition_synthesis_principals WHERE enrollment_root_id=NEW.enrollment_root_id ORDER BY generation DESC LIMIT 1;
  IF cp.id<>pf.head_id OR cp.generation<>pf.revision OR pf.head_hash<>menuto_nutrition_synthesis.hash('nutrition-synthesis.principal-fact.v1',menuto_nutrition_synthesis.fact('PRINCIPAL',to_jsonb(cp))) THEN RAISE EXCEPTION 'Atomic principal enrollment/frontier invariant'; END IF;
  IF TG_TABLE_NAME='nutrition_synthesis_principals' THEN
   IF (NEW.command->>'expected_generation')::bigint<>NEW.generation-1 OR NEW.previous_id IS DISTINCT FROM (NEW.command->>'previous_enrollment_id')::uuid THEN RAISE EXCEPTION 'Principal command/CAS lineage mismatch'; END IF;
   IF NEW.generation=1 THEN IF NEW.enrollment_root_id<>NEW.id THEN RAISE EXCEPTION 'Canonical enrollment genesis identity'; END IF;
   ELSE SELECT * INTO STRICT prior_cp FROM public.nutrition_synthesis_principals WHERE id=NEW.previous_id;
    IF prior_cp.enrollment_root_id<>NEW.enrollment_root_id OR prior_cp.generation<>NEW.generation-1 OR prior_cp.recorded_order>=NEW.recorded_order THEN RAISE EXCEPTION 'Principal replacement lineage mismatch'; END IF;
   END IF;
  END IF;
  RETURN NULL;
 END IF;
 IF TG_TABLE_NAME='nutrition_synthesis_streams' THEN p:=NEW.provider_id; f:=NEW.family_id;
 ELSE SELECT * INTO STRICT r FROM public.nutrition_synthesis_receipts WHERE id=NEW.id; p:=r.provider_id; f:=r.family_id;
  SELECT count(*) INTO children FROM(SELECT id FROM public.nutrition_synthesis_drafts WHERE id=r.id UNION ALL SELECT id FROM public.nutrition_synthesis_reviews WHERE id=r.id UNION ALL SELECT id FROM public.nutrition_synthesis_publications WHERE id=r.id) x;
  IF children<>1 OR r.command_hash<>menuto_nutrition_synthesis.hash('nutrition-synthesis.command.v1',r.command) OR r.event_hash<>menuto_nutrition_synthesis.hash('nutrition-synthesis.event.v1',menuto_nutrition_synthesis.record_fact(r)-'event_hash') THEN RAISE EXCEPTION 'Atomic typed receipt/hash invariant'; END IF;
  IF r.previous_id IS NOT NULL THEN SELECT * INTO STRICT prev FROM public.nutrition_synthesis_receipts WHERE id=r.previous_id;
   IF prev.provider_id<>p OR prev.family_id<>f OR prev.sequence<>r.sequence-1 OR prev.event_hash<>r.previous_hash OR prev.recorded_order>=r.recorded_order THEN RAISE EXCEPTION 'Contiguous history required'; END IF;
  END IF;
 END IF;
 IF f='__AUTHORITY_LOCK__' THEN RETURN NULL; END IF;
 SELECT * INTO STRICT st FROM public.nutrition_synthesis_streams WHERE provider_id=p AND family_id=f;
 SELECT * INTO r FROM public.nutrition_synthesis_receipts WHERE provider_id=p AND family_id=f ORDER BY sequence DESC LIMIT 1;
 IF st.revision<>(SELECT count(*) FROM public.nutrition_synthesis_receipts WHERE provider_id=p AND family_id=f) OR st.head_id IS DISTINCT FROM r.id OR st.head_hash IS DISTINCT FROM r.event_hash THEN RAISE EXCEPTION 'Atomic event/frontier mismatch'; END IF;
 RETURN NULL;
END $$;
DO $$ DECLARE t text; fn record; BEGIN
 FOREACH t IN ARRAY ARRAY['nutrition_synthesis_providers','nutrition_synthesis_principals','nutrition_synthesis_principal_frontiers','nutrition_synthesis_grants','nutrition_synthesis_streams',
 'nutrition_synthesis_receipts','nutrition_synthesis_drafts','nutrition_synthesis_reviews','nutrition_synthesis_publications','nutrition_synthesis_evidence'] LOOP
  EXECUTE format('ALTER TABLE public.%I OWNER TO menuto_nutrition_synthesis_owner',t);
  EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC,menuto_nutrition_synthesis_admin,menuto_nutrition_synthesis_client',t);
  EXECUTE format('CREATE TRIGGER nps_insert BEFORE INSERT ON public.%I FOR EACH ROW EXECUTE FUNCTION menuto_nutrition_synthesis.write_guard()',t);
  EXECUTE format('CREATE TRIGGER nps_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION menuto_nutrition_synthesis.immutable()',t);
  IF t IN('nutrition_synthesis_streams','nutrition_synthesis_principal_frontiers') THEN
   EXECUTE format('CREATE TRIGGER nps_frontier BEFORE UPDATE ON public.%I FOR EACH ROW EXECUTE FUNCTION menuto_nutrition_synthesis.write_guard()',t);
   EXECUTE format('CREATE TRIGGER nps_delete BEFORE DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION menuto_nutrition_synthesis.immutable()',t);
  ELSE EXECUTE format('CREATE TRIGGER nps_immutable BEFORE UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION menuto_nutrition_synthesis.immutable()',t); END IF;
  IF t IN('nutrition_synthesis_principals','nutrition_synthesis_principal_frontiers','nutrition_synthesis_streams','nutrition_synthesis_receipts','nutrition_synthesis_drafts','nutrition_synthesis_reviews','nutrition_synthesis_publications') THEN
   EXECUTE format('CREATE CONSTRAINT TRIGGER nps_coherent AFTER INSERT OR UPDATE ON public.%I DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_nutrition_synthesis.coherent()',t);
  END IF;
 END LOOP;
 ALTER SEQUENCE public.nutrition_synthesis_recorded_order OWNER TO menuto_nutrition_synthesis_owner;
 REVOKE ALL ON SEQUENCE public.nutrition_synthesis_recorded_order FROM PUBLIC,menuto_nutrition_synthesis_admin,menuto_nutrition_synthesis_client;
 FOR fn IN SELECT p.oid::regprocedure sig FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='menuto_nutrition_synthesis' LOOP
  EXECUTE format('ALTER FUNCTION %s OWNER TO menuto_nutrition_synthesis_owner',fn.sig);
  EXECUTE format('REVOKE ALL ON FUNCTION %s FROM PUBLIC,menuto_nutrition_synthesis_admin,menuto_nutrition_synthesis_client',fn.sig);
 END LOOP;
END $$;
GRANT EXECUTE ON FUNCTION menuto_nutrition_synthesis.register_provider(jsonb),menuto_nutrition_synthesis.enroll_principal(jsonb),menuto_nutrition_synthesis.change_authority(jsonb) TO menuto_nutrition_synthesis_admin;
GRANT EXECUTE ON FUNCTION menuto_nutrition_synthesis.append(jsonb),menuto_nutrition_synthesis.capture(jsonb) TO menuto_nutrition_synthesis_client;

'''

def upgrade():
    op.execute(TABLE_SQL)
    op.execute(FUNCTION_SQL)


def downgrade():
    op.execute(r"""
    DO $$ DECLARE t text; present boolean; BEGIN
      FOREACH t IN ARRAY ARRAY['nutrition_synthesis_providers','nutrition_synthesis_principals','nutrition_synthesis_principal_frontiers','nutrition_synthesis_grants',
        'nutrition_synthesis_streams','nutrition_synthesis_receipts','nutrition_synthesis_drafts','nutrition_synthesis_reviews',
        'nutrition_synthesis_publications','nutrition_synthesis_evidence'] LOOP
        EXECUTE format('SELECT EXISTS(SELECT FROM public.%I)',t) INTO present;
        IF present THEN RAISE EXCEPTION 'Refusing destructive downgrade of retained synthesis source history'; END IF;
      END LOOP;
    END $$;
    REVOKE SELECT ON public.users,public.households,public.household_members,public.memberships FROM menuto_nutrition_synthesis_owner;
    DROP SCHEMA menuto_nutrition_synthesis CASCADE;
    DROP TABLE public.nutrition_synthesis_providers,public.nutrition_synthesis_principals,public.nutrition_synthesis_principal_frontiers,public.nutrition_synthesis_grants,
      public.nutrition_synthesis_streams,public.nutrition_synthesis_receipts,public.nutrition_synthesis_drafts,
      public.nutrition_synthesis_reviews,public.nutrition_synthesis_publications,public.nutrition_synthesis_evidence;
    DROP SEQUENCE public.nutrition_synthesis_recorded_order;
    -- Infrastructure NOLOGIN roles have a cluster lifecycle; there are no source/content seeds.
    """)
