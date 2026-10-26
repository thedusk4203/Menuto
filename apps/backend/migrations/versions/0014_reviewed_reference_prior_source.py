"""Empty reviewed reference prior source; no production priors or credential secrets."""

# ruff: noqa: E501
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

TABLE_SQL = r"""

CREATE TABLE reference_prior_principals (
	id UUID NOT NULL,
	database_oid BIGINT NOT NULL,
	database_name VARCHAR(63) NOT NULL,
	role_oid BIGINT NOT NULL,
	role_name VARCHAR(63) NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	actor_database_oid BIGINT NOT NULL,
	actor_database_name VARCHAR(63) NOT NULL,
	actor_role_oid BIGINT NOT NULL,
	actor_role_name VARCHAR(63) NOT NULL,
	actor_authentication_method VARCHAR(30) NOT NULL,
	actor_authenticated_identity VARCHAR(63) NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	CONSTRAINT pk_reference_prior_principals PRIMARY KEY (id),
	CONSTRAINT ck_reference_prior_principals_authenticated_actor CHECK (actor_authentication_method='scram-sha-256' AND actor_authenticated_identity=actor_role_name),
	CONSTRAINT ck_reference_prior_principals_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT uq_reference_prior_principals_database_oid_role_oid_role_name UNIQUE (database_oid, role_oid, role_name),
	CONSTRAINT uq_reference_prior_principals_actor_role_oid_idempotency_key UNIQUE (actor_role_oid, idempotency_key),
	CONSTRAINT ck_reference_prior_principals_idempotency_key_identifier CHECK (idempotency_key ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_reference_prior_principals_oids CHECK (database_oid BETWEEN 1 AND 4294967295 AND role_oid BETWEEN 1 AND 4294967295),
	CONSTRAINT ck_reference_prior_principals_database_binding CHECK (database_oid=actor_database_oid AND database_name=actor_database_name),
	CONSTRAINT ck_reference_prior_principals_command_hash CHECK (command_hash ~ '^[a-f0-9]{64}$')
)

;

CREATE TABLE reference_prior_providers (
	id UUID NOT NULL,
	code VARCHAR(100) NOT NULL,
	version VARCHAR(100) NOT NULL,
	source_system VARCHAR(100) NOT NULL,
	remit TEXT NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	actor_database_oid BIGINT NOT NULL,
	actor_database_name VARCHAR(63) NOT NULL,
	actor_role_oid BIGINT NOT NULL,
	actor_role_name VARCHAR(63) NOT NULL,
	actor_authentication_method VARCHAR(30) NOT NULL,
	actor_authenticated_identity VARCHAR(63) NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	CONSTRAINT pk_reference_prior_providers PRIMARY KEY (id),
	CONSTRAINT ck_reference_prior_providers_authenticated_actor CHECK (actor_authentication_method='scram-sha-256' AND actor_authenticated_identity=actor_role_name),
	CONSTRAINT ck_reference_prior_providers_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT uq_reference_prior_providers_code_version UNIQUE (code, version),
	CONSTRAINT uq_reference_prior_providers_actor_role_oid_idempotency_key UNIQUE (actor_role_oid, idempotency_key),
	CONSTRAINT uq_reference_prior_providers_id_source_system UNIQUE (id, source_system),
	CONSTRAINT ck_reference_prior_providers_code_identifier CHECK (code ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_reference_prior_providers_version_identifier CHECK (version ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_reference_prior_providers_source_system_identifier CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_reference_prior_providers_idempotency_key_identifier CHECK (idempotency_key ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_reference_prior_providers_remit CHECK (length(remit) BETWEEN 1 AND 4000 AND remit ~ '[^[:space:]]'),
	CONSTRAINT ck_reference_prior_providers_command_hash CHECK (command_hash ~ '^[a-f0-9]{64}$')
)

;

CREATE TABLE reference_prior_authority (
	id UUID NOT NULL,
	provider_id UUID NOT NULL,
	principal_id UUID NOT NULL,
	capability VARCHAR(30) NOT NULL,
	action VARCHAR(10) NOT NULL,
	expected_authority_generation BIGINT NOT NULL,
	reason TEXT NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	authority_sequence BIGINT NOT NULL,
	mutation_sequence BIGINT NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	fact_hash VARCHAR(64) NOT NULL,
	actor_database_oid BIGINT NOT NULL,
	actor_database_name VARCHAR(63) NOT NULL,
	actor_role_oid BIGINT NOT NULL,
	actor_role_name VARCHAR(63) NOT NULL,
	actor_authentication_method VARCHAR(30) NOT NULL,
	actor_authenticated_identity VARCHAR(63) NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	CONSTRAINT pk_reference_prior_authority PRIMARY KEY (id),
	CONSTRAINT ck_reference_prior_authority_authenticated_actor CHECK (actor_authentication_method='scram-sha-256' AND actor_authenticated_identity=actor_role_name),
	CONSTRAINT ck_reference_prior_authority_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT uq_reference_prior_authority_provider_id_authority_sequence UNIQUE (provider_id, authority_sequence),
	CONSTRAINT uq_reference_prior_authority_provider_id_actor_role_oid_e378 UNIQUE (provider_id, actor_role_oid, idempotency_key),
	CONSTRAINT uq_reference_prior_authority_id_provider_id_mutation_sequence UNIQUE (id, provider_id, mutation_sequence),
	CONSTRAINT ck_reference_prior_authority_capability CHECK (capability IN ('REVIEW_PUBLISH','RETRACT','CAPTURE')),
	CONSTRAINT ck_reference_prior_authority_action CHECK (action IN ('GRANT','REVOKE')),
	CONSTRAINT ck_reference_prior_authority_sequences CHECK (expected_authority_generation>=0 AND authority_sequence=expected_authority_generation+1 AND mutation_sequence>0),
	CONSTRAINT ck_reference_prior_authority_reason CHECK (length(reason) BETWEEN 1 AND 4000 AND reason ~ '[^[:space:]]'),
	CONSTRAINT ck_reference_prior_authority_hashes CHECK (command_hash ~ '^[a-f0-9]{64}$' AND fact_hash ~ '^[a-f0-9]{64}$'),
	CONSTRAINT ck_reference_prior_authority_idempotency_key_identifier CHECK (idempotency_key ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT fk_reference_prior_authority_provider_id_reference_prio_aaa4 FOREIGN KEY(provider_id) REFERENCES reference_prior_providers (id) ON DELETE RESTRICT,
	CONSTRAINT fk_reference_prior_authority_principal_id_reference_pri_7ce8 FOREIGN KEY(principal_id) REFERENCES reference_prior_principals (id) ON DELETE RESTRICT
)

;

CREATE TABLE reference_prior_frontiers (
	provider_id UUID NOT NULL,
	source_generation BIGINT NOT NULL,
	authority_generation BIGINT NOT NULL,
	mutation_generation BIGINT NOT NULL,
	source_head_id UUID,
	authority_head_id UUID,
	mutation_head_hash VARCHAR(64),
	CONSTRAINT pk_reference_prior_frontiers PRIMARY KEY (provider_id),
	CONSTRAINT ck_reference_prior_frontiers_generations CHECK (source_generation>=0 AND authority_generation>=0 AND mutation_generation>=0 AND mutation_generation=source_generation+authority_generation),
	CONSTRAINT ck_reference_prior_frontiers_heads CHECK ((source_generation=0)=(source_head_id IS NULL) AND (authority_generation=0)=(authority_head_id IS NULL) AND (mutation_generation=0)=(mutation_head_hash IS NULL)),
	CONSTRAINT fk_reference_prior_frontiers_provider_id_reference_prio_4463 FOREIGN KEY(provider_id) REFERENCES reference_prior_providers (id) ON DELETE RESTRICT
)

;

CREATE TABLE reference_prior_streams (
	id UUID NOT NULL,
	provider_id UUID NOT NULL,
	target_kind VARCHAR(20) NOT NULL,
	ingredient_id UUID,
	recipe_id UUID,
	feature_term_id UUID,
	head_id UUID NOT NULL,
	head_revision INTEGER NOT NULL,
	CONSTRAINT pk_reference_prior_streams PRIMARY KEY (id),
	CONSTRAINT uq_reference_prior_streams_id_provider_id UNIQUE (id, provider_id),
	CONSTRAINT fk_reference_prior_streams_feature_term_id_affinity_fea_e303 FOREIGN KEY(feature_term_id, target_kind) REFERENCES affinity_feature_terms (id, kind) ON DELETE RESTRICT,
	CONSTRAINT ck_reference_prior_streams_typed_target CHECK ((target_kind='INGREDIENT' AND ingredient_id IS NOT NULL AND recipe_id IS NULL AND feature_term_id IS NULL) OR (target_kind='DIRECT_RECIPE' AND recipe_id IS NOT NULL AND ingredient_id IS NULL AND feature_term_id IS NULL) OR (target_kind IN ('PROTEIN','METHOD','FLAVOR') AND feature_term_id IS NOT NULL AND ingredient_id IS NULL AND recipe_id IS NULL)),
	CONSTRAINT ck_reference_prior_streams_head_revision CHECK (head_revision>=0),
	CONSTRAINT fk_reference_prior_streams_provider_id_reference_prior__f40b FOREIGN KEY(provider_id) REFERENCES reference_prior_providers (id) ON DELETE RESTRICT,
	CONSTRAINT fk_reference_prior_streams_ingredient_id_ingredients FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT,
	CONSTRAINT fk_reference_prior_streams_recipe_id_recipes FOREIGN KEY(recipe_id) REFERENCES recipes (id) ON DELETE RESTRICT
)

;
CREATE UNIQUE INDEX uq_prior_stream_direct_recipe ON reference_prior_streams (provider_id, recipe_id) WHERE target_kind='DIRECT_RECIPE';
CREATE UNIQUE INDEX uq_prior_stream_flavor ON reference_prior_streams (provider_id, feature_term_id) WHERE target_kind='FLAVOR';
CREATE UNIQUE INDEX uq_prior_stream_ingredient ON reference_prior_streams (provider_id, ingredient_id) WHERE target_kind='INGREDIENT';
CREATE UNIQUE INDEX uq_prior_stream_method ON reference_prior_streams (provider_id, feature_term_id) WHERE target_kind='METHOD';
CREATE UNIQUE INDEX uq_prior_stream_protein ON reference_prior_streams (provider_id, feature_term_id) WHERE target_kind='PROTEIN';

CREATE TABLE reference_prior_revisions (
	id UUID NOT NULL,
	stream_id UUID NOT NULL,
	provider_id UUID NOT NULL,
	principal_id UUID NOT NULL,
	grant_event_id UUID NOT NULL,
	operation VARCHAR(10) NOT NULL,
	numerator INTEGER,
	denominator INTEGER,
	source_kind VARCHAR(30) NOT NULL,
	source_system VARCHAR(100) NOT NULL,
	external_record_id VARCHAR(2048) NOT NULL,
	source_version VARCHAR(200) NOT NULL,
	source_uri VARCHAR(2048),
	content_hash VARCHAR(64) NOT NULL,
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
	review_rationale TEXT NOT NULL,
	expected_provider_generation BIGINT NOT NULL,
	expected_revision INTEGER NOT NULL,
	predecessor_id UUID,
	idempotency_key VARCHAR(100) NOT NULL,
	authority_generation BIGINT NOT NULL,
	revision INTEGER NOT NULL,
	source_sequence BIGINT NOT NULL,
	mutation_sequence BIGINT NOT NULL,
	effective_at TIMESTAMP WITH TIME ZONE NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	fact_hash VARCHAR(64) NOT NULL,
	actor_database_oid BIGINT NOT NULL,
	actor_database_name VARCHAR(63) NOT NULL,
	actor_role_oid BIGINT NOT NULL,
	actor_role_name VARCHAR(63) NOT NULL,
	actor_authentication_method VARCHAR(30) NOT NULL,
	actor_authenticated_identity VARCHAR(63) NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	CONSTRAINT pk_reference_prior_revisions PRIMARY KEY (id),
	CONSTRAINT ck_reference_prior_revisions_authenticated_actor CHECK (actor_authentication_method='scram-sha-256' AND actor_authenticated_identity=actor_role_name),
	CONSTRAINT ck_reference_prior_revisions_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT fk_reference_prior_revisions_stream_id_reference_prior_streams FOREIGN KEY(stream_id, provider_id) REFERENCES reference_prior_streams (id, provider_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
	CONSTRAINT fk_reference_prior_revisions_provider_id_reference_prio_9c19 FOREIGN KEY(provider_id, source_system) REFERENCES reference_prior_providers (id, source_system) ON DELETE RESTRICT,
	CONSTRAINT uq_reference_prior_revisions_id_stream_id_provider_id_revision UNIQUE (id, stream_id, provider_id, revision),
	CONSTRAINT uq_reference_prior_revisions_id_provider_id_mutation_sequence UNIQUE (id, provider_id, mutation_sequence),
	CONSTRAINT uq_reference_prior_revisions_provider_id_source_sequence UNIQUE (provider_id, source_sequence),
	CONSTRAINT uq_reference_prior_revisions_stream_id_revision UNIQUE (stream_id, revision),
	CONSTRAINT uq_reference_prior_revisions_provider_id_principal_id_i_653f UNIQUE (provider_id, principal_id, idempotency_key),
	CONSTRAINT ck_reference_prior_revisions_sequences CHECK (expected_provider_generation>=0 AND source_sequence=expected_provider_generation+1 AND authority_generation>=0 AND mutation_sequence>0 AND revision>=0 AND revision=expected_revision+1 AND expected_revision>=-1),
	CONSTRAINT ck_reference_prior_revisions_predecessor CHECK ((expected_revision=-1)=(predecessor_id IS NULL)),
	CONSTRAINT ck_reference_prior_revisions_exact_amount CHECK ((operation='REPLACE' AND numerator IS NOT NULL AND denominator IS NOT NULL AND denominator>0 AND numerator BETWEEN -2147483647 AND 2147483647 AND abs(numerator::bigint)<=denominator AND gcd(abs(numerator::bigint),denominator::bigint)=1) OR (operation='RETRACT' AND numerator IS NULL AND denominator IS NULL AND expected_revision>=0)),
	CONSTRAINT ck_reference_prior_revisions_source_time CHECK (source_kind='REVIEWED_REFERENCE' AND isfinite(observed_at) AND observed_at<=recorded_at AND effective_at=recorded_at),
	CONSTRAINT ck_reference_prior_revisions_reference_identity CHECK (length(trim(external_record_id))>0 AND length(trim(source_version))>0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'),
	CONSTRAINT ck_reference_prior_revisions_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')),
	CONSTRAINT ck_reference_prior_revisions_hashes CHECK (content_hash ~ '^[a-f0-9]{64}$' AND command_hash ~ '^[a-f0-9]{64}$' AND fact_hash ~ '^[a-f0-9]{64}$'),
	CONSTRAINT ck_reference_prior_revisions_rationale CHECK (length(review_rationale) BETWEEN 1 AND 4000 AND review_rationale ~ '[^[:space:]]'),
	CONSTRAINT ck_reference_prior_revisions_idempotency_key_identifier CHECK (idempotency_key ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_reference_prior_revisions_source_system_identifier CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT fk_reference_prior_revisions_principal_id_reference_pri_c516 FOREIGN KEY(principal_id) REFERENCES reference_prior_principals (id) ON DELETE RESTRICT,
	CONSTRAINT fk_reference_prior_revisions_grant_event_id_reference_p_51d6 FOREIGN KEY(grant_event_id) REFERENCES reference_prior_authority (id) ON DELETE RESTRICT,
	CONSTRAINT fk_reference_prior_revisions_predecessor_id_reference_p_894e FOREIGN KEY(predecessor_id) REFERENCES reference_prior_revisions (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
)

;

CREATE TABLE reference_prior_mutations (
	provider_id UUID NOT NULL,
	mutation_sequence BIGINT NOT NULL,
	kind VARCHAR(20) NOT NULL,
	authority_event_id UUID,
	publication_id UUID,
	child_hash VARCHAR(64) NOT NULL,
	predecessor_hash VARCHAR(64),
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	journal_hash VARCHAR(64) NOT NULL,
	CONSTRAINT pk_reference_prior_mutations PRIMARY KEY (provider_id, mutation_sequence),
	CONSTRAINT fk_reference_prior_mutations_authority_event_id_referen_6f03 FOREIGN KEY(authority_event_id, provider_id, mutation_sequence) REFERENCES reference_prior_authority (id, provider_id, mutation_sequence) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
	CONSTRAINT fk_reference_prior_mutations_publication_id_reference_p_d52e FOREIGN KEY(publication_id, provider_id, mutation_sequence) REFERENCES reference_prior_revisions (id, provider_id, mutation_sequence) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
	CONSTRAINT ck_reference_prior_mutations_sequence_time CHECK (mutation_sequence>0 AND isfinite(recorded_at)),
	CONSTRAINT ck_reference_prior_mutations_typed_child CHECK ((kind='AUTHORITY' AND authority_event_id IS NOT NULL AND publication_id IS NULL) OR (kind='PUBLICATION' AND publication_id IS NOT NULL AND authority_event_id IS NULL)),
	CONSTRAINT ck_reference_prior_mutations_hashes CHECK (child_hash ~ '^[a-f0-9]{64}$' AND journal_hash ~ '^[a-f0-9]{64}$'),
	CONSTRAINT fk_reference_prior_mutations_provider_id_reference_prio_bc69 FOREIGN KEY(provider_id) REFERENCES reference_prior_providers (id) ON DELETE RESTRICT
)

;
ALTER TABLE reference_prior_streams ADD CONSTRAINT fk_reference_prior_stream_head FOREIGN KEY(head_id, id, provider_id, head_revision) REFERENCES reference_prior_revisions (id, stream_id, provider_id, revision) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
"""

FUNCTION_SQL = r'''
-- Structural roles have no credentials or provider capabilities.
DO $$ DECLARE n text; BEGIN
 FOREACH n IN ARRAY ARRAY['menuto_prior_owner','menuto_prior_admin','menuto_prior_client'] LOOP
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname=n) THEN
   EXECUTE pg_catalog.format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS',n);
  END IF;
  IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname=n AND
    (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN
   RAISE EXCEPTION 'Unsafe existing reference infrastructure role';
  END IF;
 END LOOP;
 IF EXISTS (SELECT FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid=m.member WHERE r.rolname='menuto_prior_owner') THEN RAISE EXCEPTION 'Source owner must not inherit external roles'; END IF;
END $$;
CREATE SCHEMA menuto_prior AUTHORIZATION menuto_prior_owner;
REVOKE ALL ON SCHEMA menuto_prior FROM PUBLIC;
GRANT USAGE ON SCHEMA menuto_prior TO menuto_prior_admin, menuto_prior_client;
GRANT USAGE ON SCHEMA public TO menuto_prior_owner;
GRANT SELECT ON public.ingredients, public.recipes, public.affinity_feature_terms TO menuto_prior_owner;
DO $$ BEGIN
 IF has_schema_privilege('menuto_prior_owner','public','CREATE') OR EXISTS (
  SELECT FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='public' AND c.relkind='r' AND c.relname NOT LIKE 'reference_prior_%'
  AND (has_table_privilege('menuto_prior_owner',c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') OR
       (c.relname NOT IN ('ingredients','recipes','affinity_feature_terms') AND has_table_privilege('menuto_prior_owner',c.oid,'SELECT')))
 ) THEN RAISE EXCEPTION 'Reference owner has privileges outside source and identity reads'; END IF;
END $$;


CREATE FUNCTION menuto_prior.coordinate() RETURNS jsonb LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
 SELECT '{"coordinate_id":"CURATED_REFERENCE_PREFERENCE","coordinate_version": 1,"unit":"REVIEWED_REFERENCE_ANCHOR_UNITS","applicability":"GLOBAL_REFERENCE_ONLY"}'::jsonb
$$;
CREATE FUNCTION menuto_prior.utc(t timestamptz) RETURNS text LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
 SELECT to_char(t AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
$$;
CREATE FUNCTION menuto_prior.canonical(j jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE r text; BEGIN
 CASE jsonb_typeof(j)
 WHEN 'object' THEN SELECT '{'||coalesce(string_agg(to_jsonb(key)::text||':'||menuto_prior.canonical(value),',' ORDER BY key COLLATE "C"),'')||'}' INTO r FROM jsonb_each(j);
 WHEN 'array' THEN SELECT '['||coalesce(string_agg(menuto_prior.canonical(value),',' ORDER BY ord),'')||']' INTO r FROM jsonb_array_elements(j) WITH ORDINALITY a(value,ord);
 WHEN 'number' THEN
  IF j::text !~ '^-?(0|[1-9][0-9]*)$' THEN RAISE EXCEPTION 'Exact integer required'; END IF; r:=j::text;
 ELSE r:=j::text;
 END CASE; RETURN r;
END $$;
CREATE FUNCTION menuto_prior.hash(domain text,j jsonb) RETURNS text LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
 SELECT encode(sha256(convert_to(menuto_prior.canonical(jsonb_build_object('domain',domain,'value',j)),'UTF8')),'hex')
$$;
CREATE FUNCTION menuto_prior.keys(j jsonb, names text[]) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'object' OR
  (SELECT array_agg(k ORDER BY k) FROM jsonb_object_keys(j) k) IS DISTINCT FROM
  (SELECT array_agg(k ORDER BY k) FROM unnest(names) k) THEN
  RAISE EXCEPTION 'Closed command fields required';
 END IF;
END $$;
CREATE FUNCTION menuto_prior.integer(j jsonb, lo bigint, hi bigint) RETURNS bigint LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE v bigint; BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'number' OR j::text !~ '^-?(0|[1-9][0-9]*)$' THEN RAISE EXCEPTION 'Strict integer required'; END IF;
 v:=j::text::bigint; IF v<lo OR v>hi THEN RAISE EXCEPTION 'Integer outside bounds'; END IF; RETURN v;
END $$;
CREATE FUNCTION menuto_prior.identifier(j jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'string' OR length(j#>>'{}') NOT BETWEEN 1 AND 100 OR (j#>>'{}') !~ '^[A-Za-z0-9_.:-]+$' THEN RAISE EXCEPTION 'Invalid identifier'; END IF;
 RETURN j#>>'{}';
END $$;
CREATE FUNCTION menuto_prior.uuid(j jsonb) RETURNS uuid LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE v uuid; BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'UUID string required'; END IF;
 v:=(j#>>'{}')::uuid;
 IF v::text<>(j#>>'{}') THEN RAISE EXCEPTION 'Canonical UUID required'; END IF; RETURN v;
END $$;
CREATE FUNCTION menuto_prior.reason(j jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'string' OR length(j#>>'{}') NOT BETWEEN 1 AND 4000 OR (j#>>'{}') !~ '[^[:space:]]' THEN RAISE EXCEPTION 'Review rationale required'; END IF; RETURN j#>>'{}';
END $$;
CREATE FUNCTION menuto_prior.safe_role(login name, admin_mode boolean) RETURNS void LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE r record; dbowner oid; BEGIN
 SELECT * INTO r FROM pg_catalog.pg_roles WHERE rolname=login;
 SELECT datdba INTO dbowner FROM pg_catalog.pg_database WHERE datname=current_database();
 IF r.oid IS NULL OR NOT r.rolcanlogin OR r.oid=dbowner OR
  EXISTS (SELECT FROM pg_catalog.pg_roles x WHERE
    (x.rolsuper OR x.rolcreaterole OR x.rolcreatedb OR x.rolreplication OR x.rolbypassrls OR x.oid=dbowner OR x.rolname='menuto_prior_owner'
      OR (NOT admin_mode AND x.rolname='menuto_prior_admin'))
    AND pg_catalog.pg_has_role(r.oid,x.oid,'MEMBER')) OR
  has_schema_privilege(login,'menuto_prior','CREATE') THEN
  RAISE EXCEPTION 'Unsafe source login' USING ERRCODE='42501';
 END IF;
 IF EXISTS (SELECT FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relname LIKE 'reference_prior_%' AND c.relkind='r'
   AND (has_table_privilege(login,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') OR c.relowner=r.oid)) THEN
  RAISE EXCEPTION 'Source login has direct mutation privileges' USING ERRCODE='42501';
 END IF;
END $$;
CREATE FUNCTION menuto_prior.session_fact(admin_mode boolean) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE r record; d record; addr inet; BEGIN
 IF system_user IS DISTINCT FROM ('scram-sha-256:'||session_user) THEN
  RAISE EXCEPTION 'SCRAM authenticated original session required' USING ERRCODE='28000';
 END IF;
 PERFORM menuto_prior.safe_role(session_user,admin_mode);
 IF admin_mode AND NOT pg_catalog.pg_has_role(session_user,'menuto_prior_admin','MEMBER') THEN
  RAISE EXCEPTION 'Enrollment administrator required' USING ERRCODE='42501';
 END IF;
 addr:=inet_client_addr();
 IF addr IS NULL OR (addr NOT IN ('127.0.0.1'::inet,'::1'::inet) AND NOT coalesce((SELECT ssl FROM pg_catalog.pg_stat_ssl WHERE pid=pg_backend_pid()),false)) THEN
  RAISE EXCEPTION 'Remote reference sessions require TLS' USING ERRCODE='28000';
 END IF;
 SELECT oid,rolname INTO r FROM pg_catalog.pg_roles WHERE rolname=session_user;
 SELECT oid,datname INTO d FROM pg_catalog.pg_database WHERE datname=current_database();
 RETURN jsonb_build_object('database_oid',d.oid::bigint,'database_name',d.datname,'role_oid',r.oid::bigint,'role_name',r.rolname,'authentication_method','scram-sha-256','authenticated_identity',r.rolname);
END $$;
CREATE FUNCTION menuto_prior.audit(s jsonb,t timestamptz) RETURNS jsonb LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
 SELECT jsonb_build_object('actor_database_oid',s->'database_oid','actor_database_name',s->'database_name','actor_role_oid',s->'role_oid','actor_role_name',s->'role_name','actor_authentication_method',s->'authentication_method','actor_authenticated_identity',s->'authenticated_identity','recorded_at',menuto_prior.utc(t))
$$;
CREATE FUNCTION menuto_prior.actor(d jsonb) RETURNS jsonb LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
 SELECT jsonb_build_object('database_oid',d->'actor_database_oid','database_name',d->'actor_database_name','role_oid',d->'actor_role_oid','role_name',d->'actor_role_name','authentication_method',d->'actor_authentication_method','authenticated_identity',d->'actor_authenticated_identity')
$$;
CREATE FUNCTION menuto_prior.target(d jsonb) RETURNS jsonb LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE k text:=d->>'target_kind'; BEGIN
 RETURN jsonb_build_object('kind',k,CASE k WHEN 'INGREDIENT' THEN 'ingredient_id' WHEN 'DIRECT_RECIPE' THEN 'recipe_id' ELSE 'feature_term_id' END,
 d->CASE k WHEN 'INGREDIENT' THEN 'ingredient_id' WHEN 'DIRECT_RECIPE' THEN 'recipe_id' ELSE 'feature_term_id' END);
END $$;
CREATE FUNCTION menuto_prior.check_target(t jsonb) RETURNS void LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE k text:=t->>'kind'; v_id uuid; BEGIN
 IF k='INGREDIENT' THEN
  PERFORM menuto_prior.keys(t,ARRAY['kind','ingredient_id']); v_id:=menuto_prior.uuid(t->'ingredient_id');
  IF NOT EXISTS (SELECT FROM public.ingredients WHERE ingredients.id=v_id) THEN RAISE EXCEPTION 'TARGET_IDENTITY_UNRESOLVED'; END IF;
 ELSIF k='DIRECT_RECIPE' THEN
  PERFORM menuto_prior.keys(t,ARRAY['kind','recipe_id']); v_id:=menuto_prior.uuid(t->'recipe_id');
  IF NOT EXISTS (SELECT FROM public.recipes WHERE recipes.id=v_id) THEN RAISE EXCEPTION 'TARGET_IDENTITY_UNRESOLVED'; END IF;
 ELSIF k IN ('PROTEIN','METHOD','FLAVOR') THEN
  PERFORM menuto_prior.keys(t,ARRAY['kind','feature_term_id']); v_id:=menuto_prior.uuid(t->'feature_term_id');
  IF NOT EXISTS (SELECT FROM public.affinity_feature_terms f WHERE f.id=v_id AND f.kind=k AND f.status='REVIEWED') THEN RAISE EXCEPTION 'TARGET_NOT_REVIEWED'; END IF;
 ELSE RAISE EXCEPTION 'Invalid exact target kind'; END IF;
END $$;
CREATE FUNCTION menuto_prior.provider_fact(d jsonb) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
 SELECT jsonb_build_object('id',d->'id','command',jsonb_build_object('code',d->'code','version',d->'version','source_system',d->'source_system','remit',d->'remit','coordinate',menuto_prior.coordinate(),'idempotency_key',d->'idempotency_key'),'administrator',menuto_prior.actor(d),'recorded_at',menuto_prior.utc((d->>'recorded_at')::timestamptz),'command_hash',d->'command_hash')
$$;
CREATE FUNCTION menuto_prior.principal_fact(d jsonb) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
 SELECT jsonb_build_object('id',d->'id','command',jsonb_build_object('role_name',d->'role_name','idempotency_key',d->'idempotency_key'),'database_oid',d->'database_oid','database_name',d->'database_name','role_oid',d->'role_oid','role_name',d->'role_name','administrator',menuto_prior.actor(d),'recorded_at',menuto_prior.utc((d->>'recorded_at')::timestamptz),'command_hash',d->'command_hash')
$$;
CREATE FUNCTION menuto_prior.authority_fact(d jsonb) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
 SELECT jsonb_build_object('id',d->'id','command',jsonb_build_object('provider_id',d->'provider_id','principal_id',d->'principal_id','capability',d->'capability','action',d->'action','expected_authority_generation',d->'expected_authority_generation','reason',d->'reason','idempotency_key',d->'idempotency_key'),'administrator',menuto_prior.actor(d),'recorded_at',menuto_prior.utc((d->>'recorded_at')::timestamptz),'authority_sequence',d->'authority_sequence','mutation_sequence',d->'mutation_sequence','command_hash',d->'command_hash','fact_hash',d->'fact_hash')
$$;
CREATE FUNCTION menuto_prior.revision_fact(d jsonb) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE c jsonb; t jsonb; BEGIN
 SELECT menuto_prior.target(to_jsonb(s)) INTO t FROM public.reference_prior_streams s WHERE s.id=(d->>'stream_id')::uuid;
 c:=jsonb_build_object('operation',d->'operation','provider_id',d->'provider_id','target',t,'coordinate',menuto_prior.coordinate(),
 'provenance',jsonb_build_object('kind',d->'source_kind','source_system',d->'source_system','external_record_id',d->'external_record_id','source_version',d->'source_version','source_uri',d->'source_uri','content_hash',d->'content_hash','observed_at',menuto_prior.utc((d->>'observed_at')::timestamptz)),
 'review_rationale',d->'review_rationale','expected_provider_generation',d->'expected_provider_generation','expected_revision',d->'expected_revision','predecessor_id',d->'predecessor_id','idempotency_key',d->'idempotency_key');
 IF d->>'operation'='REPLACE' THEN c:=c||jsonb_build_object('amount',jsonb_build_object('numerator',d->'numerator','denominator',d->'denominator','unit','REVIEWED_REFERENCE_ANCHOR_UNITS')); END IF;
 RETURN jsonb_build_object('id',d->'id','stream_id',d->'stream_id','command',c,'principal_id',d->'principal_id','session',menuto_prior.actor(d),'grant_event_id',d->'grant_event_id','authority_generation',d->'authority_generation','revision',d->'revision','source_sequence',d->'source_sequence','mutation_sequence',d->'mutation_sequence','recorded_at',menuto_prior.utc((d->>'recorded_at')::timestamptz),'effective_at',menuto_prior.utc((d->>'effective_at')::timestamptz),'command_hash',d->'command_hash','fact_hash',d->'fact_hash');
END $$;
CREATE FUNCTION menuto_prior.mutation_fact(d jsonb) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
 SELECT jsonb_build_object('provider_id',d->'provider_id','mutation_sequence',d->'mutation_sequence','kind',d->'kind','child_id',coalesce(nullif(d->'authority_event_id','null'::jsonb),d->'publication_id'),'child_hash',d->'child_hash','predecessor_hash',d->'predecessor_hash','recorded_at',menuto_prior.utc((d->>'recorded_at')::timestamptz),'journal_hash',d->'journal_hash')
$$;
CREATE FUNCTION menuto_prior.append_mutation(p uuid, seq bigint, k text, child uuid, h text, t timestamptz, prev text) RETURNS jsonb LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE d jsonb; f jsonb; BEGIN
 IF EXISTS (SELECT FROM public.reference_prior_mutations WHERE provider_id=p AND recorded_at>t) OR EXISTS (SELECT FROM public.reference_prior_providers WHERE id=p AND recorded_at>t) OR EXISTS (SELECT FROM public.reference_prior_principals x JOIN public.reference_prior_authority a ON a.principal_id=x.id WHERE a.provider_id=p AND x.recorded_at>t) THEN RAISE EXCEPTION 'Source clock regression'; END IF;
 d:=jsonb_build_object('provider_id',p,'mutation_sequence',seq,'kind',k,'authority_event_id',CASE WHEN k='AUTHORITY' THEN child END,'publication_id',CASE WHEN k='PUBLICATION' THEN child END,'child_hash',h,'predecessor_hash',prev,'recorded_at',menuto_prior.utc(t));
 f:=menuto_prior.mutation_fact(d);
 d:=d||jsonb_build_object('journal_hash',menuto_prior.hash('prior.mutation.v1',f-'journal_hash'));
 INSERT INTO public.reference_prior_mutations SELECT * FROM jsonb_populate_record(NULL::public.reference_prior_mutations,d);
 RETURN menuto_prior.mutation_fact(d);
END $$;
CREATE FUNCTION menuto_prior.principal(s jsonb) RETURNS uuid LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE id uuid; BEGIN
 SELECT p.id INTO id FROM public.reference_prior_principals p WHERE p.database_oid=(s->>'database_oid')::bigint AND p.database_name=s->>'database_name' AND p.role_oid=(s->>'role_oid')::bigint AND p.role_name=s->>'role_name';
 IF id IS NULL THEN RAISE EXCEPTION 'Login is not enrolled' USING ERRCODE='42501'; END IF; RETURN id;
END $$;
CREATE FUNCTION menuto_prior.permission(p uuid, who uuid, cap text) RETURNS uuid LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE a record; BEGIN
 SELECT id,action INTO a FROM public.reference_prior_authority WHERE provider_id=p AND principal_id=who AND capability=cap ORDER BY authority_sequence DESC LIMIT 1;
 IF a.id IS NULL OR a.action<>'GRANT' THEN RAISE EXCEPTION 'Provider capability denied' USING ERRCODE='42501'; END IF; RETURN a.id;
END $$;

CREATE FUNCTION menuto_prior.register_provider(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE s jsonb:=menuto_prior.session_fact(true); d jsonb; h text; t timestamptz:=clock_timestamp(); old record; BEGIN
 PERFORM menuto_prior.keys(c,ARRAY['code','version','source_system','remit','coordinate','idempotency_key']);
 PERFORM menuto_prior.identifier(c->'code'); PERFORM menuto_prior.identifier(c->'version'); PERFORM menuto_prior.identifier(c->'source_system'); PERFORM menuto_prior.identifier(c->'idempotency_key'); PERFORM menuto_prior.reason(c->'remit');
 IF c->'coordinate' IS DISTINCT FROM menuto_prior.coordinate() THEN RAISE EXCEPTION 'Unsupported coordinate'; END IF;
 -- Registry creation has no provider frontier yet; serialize administrative enrollment globally.
 PERFORM pg_advisory_xact_lock(140014,1);
 h:=menuto_prior.hash('prior.provider-command.v1',c);
 SELECT * INTO old FROM public.reference_prior_providers WHERE actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF old.id IS NOT NULL THEN
  IF old.command_hash<>h THEN RAISE EXCEPTION 'Idempotency conflict'; END IF;
  RETURN menuto_prior.provider_fact(to_jsonb(old));
 END IF;
 d:= (c-'coordinate')||menuto_prior.audit(s,t)||jsonb_build_object('id',gen_random_uuid(),'command_hash',h);
 INSERT INTO public.reference_prior_providers SELECT * FROM jsonb_populate_record(NULL::public.reference_prior_providers,d);
 INSERT INTO public.reference_prior_frontiers VALUES ((d->>'id')::uuid,0,0,0,NULL,NULL,NULL);
 RETURN menuto_prior.provider_fact(d);
END $$;
CREATE FUNCTION menuto_prior.enroll_principal(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE s jsonb:=menuto_prior.session_fact(true); d jsonb; h text; r record; old record; BEGIN
 PERFORM menuto_prior.keys(c,ARRAY['role_name','idempotency_key']);
 IF jsonb_typeof(c->'role_name') IS DISTINCT FROM 'string' OR length(c->>'role_name') NOT BETWEEN 1 AND 63 OR (c->>'role_name') ~ '[[:cntrl:]]' THEN RAISE EXCEPTION 'Invalid role name'; END IF;
 PERFORM menuto_prior.identifier(c->'idempotency_key');
 PERFORM pg_advisory_xact_lock(140014,1);
 PERFORM menuto_prior.safe_role((c->>'role_name')::name,false);
 SELECT oid,rolname INTO r FROM pg_catalog.pg_roles WHERE rolname=c->>'role_name';
 h:=menuto_prior.hash('prior.principal-command.v1',c);
 SELECT * INTO old FROM public.reference_prior_principals WHERE actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF old.id IS NOT NULL THEN
  IF old.command_hash<>h OR old.role_oid<>r.oid::bigint THEN RAISE EXCEPTION 'Idempotency or immutable binding conflict'; END IF;
  RETURN menuto_prior.principal_fact(to_jsonb(old));
 END IF;
 d:=c||menuto_prior.audit(s,clock_timestamp())||jsonb_build_object('id',gen_random_uuid(),'command_hash',h,'database_oid',s->'database_oid','database_name',s->'database_name','role_oid',r.oid::bigint);
 INSERT INTO public.reference_prior_principals SELECT * FROM jsonb_populate_record(NULL::public.reference_prior_principals,d);
 RETURN menuto_prior.principal_fact(d);
END $$;
CREATE FUNCTION menuto_prior.change_authority(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE s jsonb:=menuto_prior.session_fact(true); p uuid; who uuid; f record; old record; last_action text; h text; d jsonb; fact jsonb; m jsonb; t timestamptz; BEGIN
 PERFORM menuto_prior.keys(c,ARRAY['provider_id','principal_id','capability','action','expected_authority_generation','reason','idempotency_key']);
 p:=menuto_prior.uuid(c->'provider_id'); who:=menuto_prior.uuid(c->'principal_id');
 PERFORM menuto_prior.integer(c->'expected_authority_generation',0,9223372036854775807);
 PERFORM menuto_prior.reason(c->'reason'); PERFORM menuto_prior.identifier(c->'idempotency_key');
 IF c->>'capability' NOT IN ('REVIEW_PUBLISH','RETRACT','CAPTURE') OR c->>'action' NOT IN ('GRANT','REVOKE') THEN RAISE EXCEPTION 'Invalid authority mutation'; END IF;
 SELECT * INTO f FROM public.reference_prior_frontiers WHERE provider_id=p FOR UPDATE;
 IF f.provider_id IS NULL THEN RAISE EXCEPTION 'Unknown provider'; END IF;
 IF NOT EXISTS (SELECT FROM public.reference_prior_principals WHERE id=who) THEN RAISE EXCEPTION 'Unknown principal'; END IF;
 h:=menuto_prior.hash('prior.authority-command.v1',c);
 SELECT * INTO old FROM public.reference_prior_authority WHERE provider_id=p AND actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF old.id IS NOT NULL THEN
  IF old.command_hash<>h THEN RAISE EXCEPTION 'Idempotency conflict'; END IF; RETURN menuto_prior.authority_fact(to_jsonb(old));
 END IF;
 IF f.authority_generation<>(c->>'expected_authority_generation')::bigint THEN RAISE EXCEPTION 'Authority CAS conflict' USING ERRCODE='40001'; END IF;
 SELECT action INTO last_action FROM public.reference_prior_authority WHERE provider_id=p AND principal_id=who AND capability=c->>'capability' ORDER BY authority_sequence DESC LIMIT 1;
 IF last_action=c->>'action' OR (last_action IS NULL AND c->>'action'='REVOKE') THEN RAISE EXCEPTION 'Authority no-op'; END IF;
 t:=clock_timestamp();
 d:=c||menuto_prior.audit(s,t)||jsonb_build_object('id',gen_random_uuid(),'authority_sequence',f.authority_generation+1,'mutation_sequence',f.mutation_generation+1,'command_hash',h);
 fact:=menuto_prior.authority_fact(d);
 d:=d||jsonb_build_object('fact_hash',menuto_prior.hash('prior.authority.v1',fact-'fact_hash'));
 INSERT INTO public.reference_prior_authority SELECT * FROM jsonb_populate_record(NULL::public.reference_prior_authority,d);
 m:=menuto_prior.append_mutation(p,f.mutation_generation+1,'AUTHORITY',(d->>'id')::uuid,d->>'fact_hash',t,f.mutation_head_hash);
 UPDATE public.reference_prior_frontiers SET authority_generation=f.authority_generation+1,mutation_generation=f.mutation_generation+1,authority_head_id=(d->>'id')::uuid,mutation_head_hash=m->>'journal_hash' WHERE provider_id=p;
 RETURN menuto_prior.authority_fact(d);
END $$;
-- Canonical literal locators form a conservative ASCII HTTP(S) subset. This prevents
-- a raw SQL caller from storing a URL that the contract parser would rewrite.
CREATE FUNCTION menuto_prior.check_uri(j jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE u text; authority text; hostname text; port text; label text; BEGIN
 IF j='null'::jsonb THEN RETURN; END IF;
 IF jsonb_typeof(j) IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'HTTP artifact locator required'; END IF;
 u:=j#>>'{}';
 IF length(u)>2048 OR u !~ '^https?://[a-z0-9][a-z0-9.-]*(:[1-9][0-9]{0,4})?/[A-Za-z0-9._~!$&''()*+,;=:@%/?#-]*$' OR u ~ '(^|/)(\.|\.\.)(/|[?#]|$)' OR u ~* '%2e' THEN
  RAISE EXCEPTION 'Canonical ASCII HTTP artifact locator required';
 END IF;
 authority:=substring(u from '^https?://([^/]+)');
 hostname:=split_part(authority,':',1); port:=nullif(split_part(authority,':',2),'');
 IF length(hostname)>253 OR (port IS NOT NULL AND (port::int>65535 OR
   (left(u,7)='http://' AND port='80') OR (left(u,8)='https://' AND port='443'))) THEN RAISE EXCEPTION 'Noncanonical artifact authority'; END IF;
 FOREACH label IN ARRAY string_to_array(hostname,'.') LOOP
  IF length(label) NOT BETWEEN 1 AND 63 OR label !~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$' THEN RAISE EXCEPTION 'Invalid artifact hostname'; END IF;
 END LOOP;
 IF hostname ~ '(^|\.)([0-9]+|0x[0-9a-f]+)$' AND hostname IS DISTINCT FROM host(hostname::inet) THEN RAISE EXCEPTION 'Noncanonical IPv4 artifact hostname'; END IF;
END $$;

CREATE FUNCTION menuto_prior.receipt(id uuid) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE r public.reference_prior_revisions; m public.reference_prior_mutations; ah uuid; BEGIN
 SELECT * INTO STRICT r FROM public.reference_prior_revisions WHERE reference_prior_revisions.id=receipt.id;
 SELECT * INTO STRICT m FROM public.reference_prior_mutations WHERE provider_id=r.provider_id AND mutation_sequence=r.mutation_sequence;
 SELECT a.id INTO ah FROM public.reference_prior_authority a WHERE a.provider_id=r.provider_id AND a.authority_sequence=r.authority_generation;
 RETURN jsonb_build_object('publication',menuto_prior.revision_fact(to_jsonb(r)),
 'mutation',menuto_prior.mutation_fact(to_jsonb(m)),'frontier',jsonb_build_object('provider_id',r.provider_id,'source_generation',r.source_sequence,'authority_generation',r.authority_generation,'mutation_generation',r.mutation_sequence,'source_head_id',r.id,'authority_head_id',ah,'mutation_head_hash',m.journal_hash),'commit_status','CALLER_TRANSACTION_NOT_CERTIFIED');
END $$;
CREATE FUNCTION menuto_prior.publish(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE s jsonb:=menuto_prior.session_fact(false); p uuid; who uuid; grant_id uuid; f public.reference_prior_frontiers;
 st public.reference_prior_streams; old public.reference_prior_revisions; d jsonb; h text; m jsonb; fact jsonb;
 t timestamptz; prov jsonb; op text:=c->>'operation'; k text; tid uuid; n bigint; den bigint; rev bigint; BEGIN
 IF op='REPLACE' THEN
  PERFORM menuto_prior.keys(c,ARRAY['operation','provider_id','target','coordinate','amount','provenance','review_rationale','expected_provider_generation','expected_revision','predecessor_id','idempotency_key']);
 ELSIF op='RETRACT' THEN
  PERFORM menuto_prior.keys(c,ARRAY['operation','provider_id','target','coordinate','provenance','review_rationale','expected_provider_generation','expected_revision','predecessor_id','idempotency_key']);
 ELSE RAISE EXCEPTION 'Unsupported publication operation'; END IF;
 p:=menuto_prior.uuid(c->'provider_id'); who:=menuto_prior.principal(s);
 SELECT * INTO f FROM public.reference_prior_frontiers WHERE provider_id=p FOR UPDATE;
 IF f.provider_id IS NULL THEN RAISE EXCEPTION 'Unknown provider'; END IF;
 -- Authority lookup deliberately follows the shared frontier lock, before receipt replay.
 grant_id:=menuto_prior.permission(p,who,CASE op WHEN 'REPLACE' THEN 'REVIEW_PUBLISH' ELSE 'RETRACT' END);
 PERFORM menuto_prior.identifier(c->'idempotency_key'); PERFORM menuto_prior.reason(c->'review_rationale');
 PERFORM menuto_prior.integer(c->'expected_provider_generation',0,9223372036854775807);
 rev:=menuto_prior.integer(c->'expected_revision',-1,2147483647);
 IF (rev=-1) IS DISTINCT FROM (c->'predecessor_id'='null'::jsonb) OR (op='RETRACT' AND rev<0) THEN RAISE EXCEPTION 'Exact predecessor required'; END IF;
 IF rev>=0 THEN PERFORM menuto_prior.uuid(c->'predecessor_id'); END IF;
 IF c->'coordinate' IS DISTINCT FROM menuto_prior.coordinate() THEN RAISE EXCEPTION 'Unsupported coordinate'; END IF;
 PERFORM menuto_prior.check_target(c->'target');
 IF op='REPLACE' THEN
  PERFORM menuto_prior.keys(c->'amount',ARRAY['numerator','denominator','unit']);
  n:=menuto_prior.integer(c->'amount'->'numerator',-2147483647,2147483647); den:=menuto_prior.integer(c->'amount'->'denominator',1,2147483647);
  IF abs(n)>den OR gcd(abs(n),den)<>1 OR c->'amount'->>'unit' IS DISTINCT FROM 'REVIEWED_REFERENCE_ANCHOR_UNITS' THEN RAISE EXCEPTION 'Noncanonical reference amount'; END IF;
 END IF;
 prov:=c->'provenance';
 PERFORM menuto_prior.keys(prov,ARRAY['kind','source_system','external_record_id','source_version','source_uri','content_hash','observed_at']);
 PERFORM menuto_prior.identifier(prov->'source_system');
 IF prov->>'kind' IS DISTINCT FROM 'REVIEWED_REFERENCE' OR prov->>'source_system' IS DISTINCT FROM (SELECT source_system FROM public.reference_prior_providers WHERE id=p) THEN RAISE EXCEPTION 'Provider provenance mismatch'; END IF;
 IF jsonb_typeof(prov->'external_record_id') IS DISTINCT FROM 'string' OR jsonb_typeof(prov->'source_version') IS DISTINCT FROM 'string' OR
  jsonb_typeof(prov->'content_hash') IS DISTINCT FROM 'string' OR jsonb_typeof(prov->'observed_at') IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'Reviewed provenance required'; END IF;
 IF prov->>'observed_at' IS DISTINCT FROM menuto_prior.utc((prov->>'observed_at')::timestamptz) OR NOT isfinite((prov->>'observed_at')::timestamptz) THEN RAISE EXCEPTION 'Canonical finite observed time required'; END IF;
 PERFORM menuto_prior.check_uri(prov->'source_uri');
 h:=menuto_prior.hash('prior.publication-command.v1',c);
 SELECT * INTO old FROM public.reference_prior_revisions WHERE provider_id=p AND principal_id=who AND idempotency_key=c->>'idempotency_key';
 IF old.id IS NOT NULL THEN
  IF old.command_hash<>h THEN RAISE EXCEPTION 'Idempotency conflict'; END IF;
  RETURN menuto_prior.receipt(old.id);
 END IF;
 IF f.source_generation<>(c->>'expected_provider_generation')::bigint THEN RAISE EXCEPTION 'Provider CAS conflict' USING ERRCODE='40001'; END IF;
 k:=c->'target'->>'kind'; tid:=coalesce(c->'target'->>'ingredient_id',c->'target'->>'recipe_id',c->'target'->>'feature_term_id')::uuid;
 SELECT * INTO st FROM public.reference_prior_streams WHERE provider_id=p AND target_kind=k AND
  CASE k WHEN 'INGREDIENT' THEN ingredient_id WHEN 'DIRECT_RECIPE' THEN recipe_id ELSE feature_term_id END=tid FOR UPDATE;
 IF rev<>coalesce(st.head_revision,-1) OR (c->>'predecessor_id')::uuid IS DISTINCT FROM st.head_id THEN RAISE EXCEPTION 'Stream CAS conflict' USING ERRCODE='40001'; END IF;
 IF op='RETRACT' AND (SELECT operation FROM public.reference_prior_revisions WHERE id=st.head_id) IS DISTINCT FROM 'REPLACE' THEN RAISE EXCEPTION 'No active publication to retract'; END IF;
 t:=clock_timestamp();
 d:=jsonb_build_object('id',gen_random_uuid(),'stream_id',coalesce(st.id,gen_random_uuid()),'provider_id',p,'principal_id',who,'grant_event_id',grant_id,'operation',op,'numerator',n,'denominator',den,
 'source_kind',prov->'kind','source_system',prov->'source_system','external_record_id',prov->'external_record_id','source_version',prov->'source_version','source_uri',prov->'source_uri','content_hash',prov->'content_hash','observed_at',prov->'observed_at','review_rationale',c->'review_rationale',
 'expected_provider_generation',c->'expected_provider_generation','expected_revision',c->'expected_revision','predecessor_id',c->'predecessor_id','idempotency_key',c->'idempotency_key','authority_generation',f.authority_generation,'revision',rev+1,'source_sequence',f.source_generation+1,'mutation_sequence',f.mutation_generation+1,'effective_at',menuto_prior.utc(t),'command_hash',h)||menuto_prior.audit(s,t);
 IF st.id IS NULL THEN
  INSERT INTO public.reference_prior_streams VALUES ((d->>'stream_id')::uuid,p,k,CASE WHEN k='INGREDIENT' THEN tid END,CASE WHEN k='DIRECT_RECIPE' THEN tid END,CASE WHEN k IN ('PROTEIN','METHOD','FLAVOR') THEN tid END,(d->>'id')::uuid,0);
 ELSE UPDATE public.reference_prior_streams SET head_id=(d->>'id')::uuid,head_revision=rev+1 WHERE id=st.id; END IF;
 fact:=menuto_prior.revision_fact(d);
 -- Reconstructed typed command must match the exact canonical caller command.
 IF fact->'command'<>c THEN RAISE EXCEPTION 'Command reconstruction differs'; END IF;
 d:=d||jsonb_build_object('fact_hash',menuto_prior.hash('prior.publication.v1',fact-'fact_hash'));
 INSERT INTO public.reference_prior_revisions SELECT * FROM jsonb_populate_record(NULL::public.reference_prior_revisions,d);
 m:=menuto_prior.append_mutation(p,f.mutation_generation+1,'PUBLICATION',(d->>'id')::uuid,d->>'fact_hash',t,f.mutation_head_hash);
 UPDATE public.reference_prior_frontiers SET source_generation=f.source_generation+1,mutation_generation=f.mutation_generation+1,source_head_id=(d->>'id')::uuid,mutation_head_hash=m->>'journal_hash' WHERE provider_id=p;
 RETURN menuto_prior.receipt((d->>'id')::uuid);
END $$;
CREATE FUNCTION menuto_prior.capture(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE s jsonb:=menuto_prior.session_fact(false); p uuid; who uuid; grant_id uuid; f record; result jsonb; t timestamptz:=clock_timestamp(); target jsonb; BEGIN
 IF pg_current_xact_id_if_assigned() IS NOT NULL OR current_setting('transaction_read_only')<>'on' OR current_setting('transaction_isolation') NOT IN ('repeatable read','serializable') THEN RAISE EXCEPTION 'Clean read-only RR/SERIALIZABLE capture required'; END IF;
 PERFORM menuto_prior.keys(c,ARRAY['provider_id','requested_targets','coordinate']); p:=menuto_prior.uuid(c->'provider_id'); who:=menuto_prior.principal(s);
 IF c->'coordinate' IS DISTINCT FROM menuto_prior.coordinate() OR jsonb_typeof(c->'requested_targets') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'Invalid capture selector'; END IF;
 FOR target IN SELECT * FROM jsonb_array_elements(c->'requested_targets') LOOP PERFORM menuto_prior.check_target(target); END LOOP;
 IF (SELECT count(*) FROM jsonb_array_elements(c->'requested_targets'))<>(SELECT count(DISTINCT value) FROM jsonb_array_elements(c->'requested_targets')) THEN RAISE EXCEPTION 'Duplicate requested target'; END IF;
 SELECT * INTO f FROM public.reference_prior_frontiers WHERE provider_id=p;
 IF f.provider_id IS NULL THEN RAISE EXCEPTION 'Unknown provider'; END IF;
 grant_id:=menuto_prior.permission(p,who,'CAPTURE');
 SELECT jsonb_build_object('request',c,'provider',menuto_prior.provider_fact(to_jsonb(pr)),
 'frontier',to_jsonb(f),'reader_principal_id',who,'reader_session',s,'reader_grant_id',grant_id,
 'principals',coalesce((SELECT jsonb_agg(menuto_prior.principal_fact(to_jsonb(x))) FROM public.reference_prior_principals x WHERE x.id=who OR x.id IN (SELECT principal_id FROM public.reference_prior_authority WHERE provider_id=p) OR x.id IN (SELECT principal_id FROM public.reference_prior_revisions WHERE provider_id=p)),'[]'::jsonb),
 'authority_events',coalesce((SELECT jsonb_agg(menuto_prior.authority_fact(to_jsonb(x))) FROM public.reference_prior_authority x WHERE provider_id=p),'[]'::jsonb),
 'publications',coalesce((SELECT jsonb_agg(menuto_prior.revision_fact(to_jsonb(x))) FROM public.reference_prior_revisions x WHERE provider_id=p),'[]'::jsonb),
 'mutations',coalesce((SELECT jsonb_agg(menuto_prior.mutation_fact(to_jsonb(x))) FROM public.reference_prior_mutations x WHERE provider_id=p),'[]'::jsonb),
 'streams',coalesce((SELECT jsonb_agg(jsonb_build_object('id',x.id,'provider_id',x.provider_id,'target',menuto_prior.target(to_jsonb(x)),'head_id',x.head_id,'head_revision',x.head_revision)) FROM public.reference_prior_streams x WHERE provider_id=p),'[]'::jsonb),
 'capture_started_at',menuto_prior.utc(t),'isolation',upper(current_setting('transaction_isolation')),'read_only',true)
 INTO result FROM public.reference_prior_providers pr WHERE pr.id=p;
 RETURN result;
END $$;
CREATE FUNCTION menuto_prior.capture_complete() RETURNS text LANGUAGE sql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$ SELECT menuto_prior.utc(clock_timestamp()) $$;

CREATE FUNCTION menuto_prior.immutable() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$ BEGIN RAISE EXCEPTION 'Immutable reviewed reference source'; END $$;
-- Even a source owner cannot accidentally rewrite publication or authority history.
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['providers','principals','authority','revisions','mutations'] LOOP
  EXECUTE format('CREATE TRIGGER prior_immutable BEFORE UPDATE OR DELETE ON public.reference_prior_%I FOR EACH ROW EXECUTE FUNCTION menuto_prior.immutable()',t);
 END LOOP;
 FOREACH t IN ARRAY ARRAY['providers','principals','frontiers','streams','authority','revisions','mutations'] LOOP
  EXECUTE format('CREATE TRIGGER prior_no_truncate BEFORE TRUNCATE ON public.reference_prior_%I FOR EACH STATEMENT EXECUTE FUNCTION menuto_prior.immutable()',t);
 END LOOP;
END $$;

-- Deferred integrity covers typed child/journal completeness and all cached heads.
CREATE FUNCTION menuto_prior.coherent() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_prior,pg_temp AS $$
DECLARE p uuid; f record; ns bigint; na bigint; nm bigint; h record; BEGIN
 p:=NEW.provider_id;
 SELECT * INTO STRICT f FROM public.reference_prior_frontiers WHERE provider_id=p;
 SELECT count(*) INTO ns FROM public.reference_prior_revisions WHERE provider_id=p;
 SELECT count(*) INTO na FROM public.reference_prior_authority WHERE provider_id=p;
 SELECT count(*) INTO nm FROM public.reference_prior_mutations WHERE provider_id=p;
 SELECT * INTO h FROM public.reference_prior_mutations WHERE provider_id=p ORDER BY mutation_sequence DESC LIMIT 1;
 IF (ns,na,nm) IS DISTINCT FROM (f.source_generation,f.authority_generation,f.mutation_generation) OR
  h.mutation_sequence IS DISTINCT FROM nullif(nm,0) OR h.journal_hash IS DISTINCT FROM f.mutation_head_hash OR
  f.source_head_id IS DISTINCT FROM (SELECT id FROM public.reference_prior_revisions WHERE provider_id=p ORDER BY source_sequence DESC LIMIT 1) OR
  f.authority_head_id IS DISTINCT FROM (SELECT id FROM public.reference_prior_authority WHERE provider_id=p ORDER BY authority_sequence DESC LIMIT 1) OR
  EXISTS (SELECT FROM public.reference_prior_mutations m WHERE m.provider_id=p AND
    (m.predecessor_hash IS DISTINCT FROM (SELECT journal_hash FROM public.reference_prior_mutations WHERE provider_id=p AND mutation_sequence=m.mutation_sequence-1) OR
     m.journal_hash<>menuto_prior.hash('prior.mutation.v1',menuto_prior.mutation_fact(to_jsonb(m))-'journal_hash'))) OR
  EXISTS (SELECT FROM public.reference_prior_streams s WHERE s.provider_id=p AND s.head_id IS DISTINCT FROM (SELECT id FROM public.reference_prior_revisions WHERE stream_id=s.id ORDER BY revision DESC LIMIT 1)) THEN
  RAISE EXCEPTION 'Incoherent reviewed reference source';
 END IF; RETURN NULL;
END $$;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['frontiers','streams','authority','revisions','mutations'] LOOP
  EXECUTE format('CREATE CONSTRAINT TRIGGER prior_coherent AFTER INSERT OR UPDATE ON public.reference_prior_%I DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_prior.coherent()',t);
 END LOOP;
END $$;

DO $$ DECLARE t text; f record; BEGIN
 FOREACH t IN ARRAY ARRAY['providers','principals','frontiers','streams','authority','revisions','mutations'] LOOP
  EXECUTE format('ALTER TABLE public.reference_prior_%I OWNER TO menuto_prior_owner',t);
  EXECUTE format('REVOKE ALL ON public.reference_prior_%I FROM PUBLIC, menuto_prior_admin, menuto_prior_client',t);
 END LOOP;
 FOR f IN SELECT p.oid::regprocedure sig FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='menuto_prior' LOOP
  EXECUTE format('ALTER FUNCTION %s OWNER TO menuto_prior_owner',f.sig);
  EXECUTE format('REVOKE ALL ON FUNCTION %s FROM PUBLIC',f.sig);
 END LOOP;
END $$;
GRANT EXECUTE ON FUNCTION menuto_prior.register_provider(jsonb),menuto_prior.enroll_principal(jsonb),menuto_prior.change_authority(jsonb) TO menuto_prior_admin;
GRANT EXECUTE ON FUNCTION menuto_prior.publish(jsonb),menuto_prior.capture(jsonb),menuto_prior.capture_complete() TO menuto_prior_client;
-- Owner API reads in the same caller-owned capture transaction, limited to identity owners.
GRANT SELECT ON public.ingredients,public.recipes,public.affinity_feature_terms TO menuto_prior_client;


'''


def upgrade():
    op.execute(TABLE_SQL)
    op.execute(FUNCTION_SQL)


def downgrade():
    op.execute(r'''
    DO $$ BEGIN
      IF EXISTS (SELECT FROM public.reference_prior_providers) OR
         EXISTS (SELECT FROM public.reference_prior_principals) OR
         EXISTS (SELECT FROM public.reference_prior_authority) OR
         EXISTS (SELECT FROM public.reference_prior_revisions) OR
         EXISTS (SELECT FROM public.reference_prior_mutations) OR
         EXISTS (SELECT FROM public.reference_prior_streams) OR
         EXISTS (SELECT FROM public.reference_prior_frontiers) THEN
        RAISE EXCEPTION 'Refusing destructive downgrade of populated reviewed reference source';
      END IF;
    END $$;
    REVOKE SELECT ON public.ingredients,public.recipes,public.affinity_feature_terms FROM menuto_prior_client,menuto_prior_owner;
    DROP SCHEMA menuto_prior CASCADE;
    ALTER TABLE public.reference_prior_streams DROP CONSTRAINT fk_reference_prior_stream_head;
    DROP TABLE public.reference_prior_mutations;
    DROP TABLE public.reference_prior_revisions;
    DROP TABLE public.reference_prior_authority;
    DROP TABLE public.reference_prior_streams;
    DROP TABLE public.reference_prior_frontiers;
    DROP TABLE public.reference_prior_principals;
    DROP TABLE public.reference_prior_providers;
    -- Leave structural cluster roles and all credentials outside database downgrade lifecycle.
    ''')
