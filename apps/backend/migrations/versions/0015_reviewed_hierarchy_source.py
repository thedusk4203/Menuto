"""Reviewed hierarchy source only; empty, separate authority, no member derivation."""

# ruff: noqa: E501
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

TABLE_SQL = r'''

CREATE TABLE hierarchy_source_principals (
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
	CONSTRAINT pk_hierarchy_source_principals PRIMARY KEY (id),
	CONSTRAINT ck_hierarchy_source_principals_authenticated_actor CHECK (actor_authentication_method='scram-sha-256' AND actor_authenticated_identity=actor_role_name),
	CONSTRAINT ck_hierarchy_source_principals_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT uq_hierarchy_source_principals_database_oid_role_oid_role_name UNIQUE (database_oid, role_oid, role_name),
	CONSTRAINT uq_hierarchy_source_principals_actor_role_oid_idempotency_key UNIQUE (actor_role_oid, idempotency_key),
	CONSTRAINT ck_hierarchy_source_principals_idempotency_key_identifier CHECK (idempotency_key ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_hierarchy_source_principals_oids CHECK (database_oid BETWEEN 1 AND 4294967295 AND role_oid BETWEEN 1 AND 4294967295),
	CONSTRAINT ck_hierarchy_source_principals_database_binding CHECK (database_oid=actor_database_oid AND database_name=actor_database_name),
	CONSTRAINT ck_hierarchy_source_principals_command_hash CHECK (command_hash ~ '^[a-f0-9]{64}$')
)


;

CREATE TABLE hierarchy_source_providers (
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
	CONSTRAINT pk_hierarchy_source_providers PRIMARY KEY (id),
	CONSTRAINT ck_hierarchy_source_providers_authenticated_actor CHECK (actor_authentication_method='scram-sha-256' AND actor_authenticated_identity=actor_role_name),
	CONSTRAINT ck_hierarchy_source_providers_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT uq_hierarchy_source_providers_code_version UNIQUE (code, version),
	CONSTRAINT uq_hierarchy_source_providers_actor_role_oid_idempotency_key UNIQUE (actor_role_oid, idempotency_key),
	CONSTRAINT uq_hierarchy_source_providers_id_source_system UNIQUE (id, source_system),
	CONSTRAINT ck_hierarchy_source_providers_code_identifier CHECK (code ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_hierarchy_source_providers_version_identifier CHECK (version ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_hierarchy_source_providers_source_system_identifier CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_hierarchy_source_providers_idempotency_key_identifier CHECK (idempotency_key ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT ck_hierarchy_source_providers_remit CHECK (length(remit) BETWEEN 1 AND 4000 AND remit ~ '[^[:space:]]'),
	CONSTRAINT ck_hierarchy_source_providers_command_hash CHECK (command_hash ~ '^[a-f0-9]{64}$')
)


;

CREATE TABLE hierarchy_source_authority (
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
	CONSTRAINT pk_hierarchy_source_authority PRIMARY KEY (id),
	CONSTRAINT ck_hierarchy_source_authority_authenticated_actor CHECK (actor_authentication_method='scram-sha-256' AND actor_authenticated_identity=actor_role_name),
	CONSTRAINT ck_hierarchy_source_authority_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT uq_hierarchy_source_authority_provider_id_authority_sequence UNIQUE (provider_id, authority_sequence),
	CONSTRAINT uq_hierarchy_source_authority_provider_id_actor_role_oi_7f90 UNIQUE (provider_id, actor_role_oid, idempotency_key),
	CONSTRAINT uq_hierarchy_source_authority_id_provider_id_mutation_sequence UNIQUE (id, provider_id, mutation_sequence),
	CONSTRAINT ck_hierarchy_source_authority_capability CHECK (capability IN ('REVIEW_PUBLISH','RETRACT','CAPTURE')),
	CONSTRAINT ck_hierarchy_source_authority_action CHECK (action IN ('GRANT','REVOKE')),
	CONSTRAINT ck_hierarchy_source_authority_sequences CHECK (expected_authority_generation>=0 AND authority_sequence=expected_authority_generation+1 AND mutation_sequence>0),
	CONSTRAINT ck_hierarchy_source_authority_reason CHECK (length(reason) BETWEEN 1 AND 4000 AND reason ~ '[^[:space:]]'),
	CONSTRAINT ck_hierarchy_source_authority_hashes CHECK (command_hash ~ '^[a-f0-9]{64}$' AND fact_hash ~ '^[a-f0-9]{64}$'),
	CONSTRAINT ck_hierarchy_source_authority_idempotency_key_identifier CHECK (idempotency_key ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT fk_hierarchy_source_authority_provider_id_hierarchy_sou_ee91 FOREIGN KEY(provider_id) REFERENCES hierarchy_source_providers (id) ON DELETE RESTRICT,
	CONSTRAINT fk_hierarchy_source_authority_principal_id_hierarchy_so_8172 FOREIGN KEY(principal_id) REFERENCES hierarchy_source_principals (id) ON DELETE RESTRICT
)


;

CREATE TABLE hierarchy_source_frontiers (
	provider_id UUID NOT NULL,
	source_generation BIGINT NOT NULL,
	authority_generation BIGINT NOT NULL,
	mutation_generation BIGINT NOT NULL,
	source_head_id UUID,
	authority_head_id UUID,
	mutation_head_hash VARCHAR(64),
	CONSTRAINT pk_hierarchy_source_frontiers PRIMARY KEY (provider_id),
	CONSTRAINT ck_hierarchy_source_frontiers_generations CHECK (source_generation>=0 AND authority_generation>=0 AND mutation_generation>=0 AND mutation_generation=source_generation+authority_generation),
	CONSTRAINT ck_hierarchy_source_frontiers_heads CHECK ((source_generation=0)=(source_head_id IS NULL) AND (authority_generation=0)=(authority_head_id IS NULL) AND (mutation_generation=0)=(mutation_head_hash IS NULL)),
	CONSTRAINT fk_hierarchy_source_frontiers_provider_id_hierarchy_sou_d292 FOREIGN KEY(provider_id) REFERENCES hierarchy_source_providers (id) ON DELETE RESTRICT
)


;

CREATE TABLE hierarchy_source_streams (
	id UUID NOT NULL,
	provider_id UUID NOT NULL,
	kind VARCHAR(20) NOT NULL,
	policy_id UUID NOT NULL,
	identity JSONB NOT NULL,
	stream_key VARCHAR(64) NOT NULL,
	head_id UUID NOT NULL,
	head_revision INTEGER NOT NULL,
	CONSTRAINT pk_hierarchy_source_streams PRIMARY KEY (id),
	CONSTRAINT uq_hierarchy_source_streams_id_provider_id UNIQUE (id, provider_id),
	CONSTRAINT uq_hierarchy_source_streams_provider_id_stream_key UNIQUE (provider_id, stream_key),
	CONSTRAINT ck_hierarchy_source_streams_kind_revision CHECK (kind IN ('POLICY','RELATION') AND head_revision>=0),
	CONSTRAINT fk_hierarchy_source_streams_provider_id_hierarchy_sourc_6ec9 FOREIGN KEY(provider_id) REFERENCES hierarchy_source_providers (id) ON DELETE RESTRICT
)


;

CREATE TABLE hierarchy_source_revisions (
	id UUID NOT NULL,
	stream_id UUID NOT NULL,
	provider_id UUID NOT NULL,
	principal_id UUID NOT NULL,
	grant_event_id UUID NOT NULL,
	operation VARCHAR(10) NOT NULL,
	command JSONB NOT NULL,
	owner_pins JSONB NOT NULL,
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
	CONSTRAINT pk_hierarchy_source_revisions PRIMARY KEY (id),
	CONSTRAINT ck_hierarchy_source_revisions_authenticated_actor CHECK (actor_authentication_method='scram-sha-256' AND actor_authenticated_identity=actor_role_name),
	CONSTRAINT ck_hierarchy_source_revisions_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT fk_hierarchy_source_revisions_stream_id_hierarchy_sourc_c21d FOREIGN KEY(stream_id, provider_id) REFERENCES hierarchy_source_streams (id, provider_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
	CONSTRAINT uq_hierarchy_source_revisions_id_stream_id_provider_id_revision UNIQUE (id, stream_id, provider_id, revision),
	CONSTRAINT uq_hierarchy_source_revisions_id_provider_id_mutation_sequence UNIQUE (id, provider_id, mutation_sequence),
	CONSTRAINT uq_hierarchy_source_revisions_provider_id_source_sequence UNIQUE (provider_id, source_sequence),
	CONSTRAINT uq_hierarchy_source_revisions_stream_id_revision UNIQUE (stream_id, revision),
	CONSTRAINT uq_hierarchy_source_revisions_provider_id_principal_id__264a UNIQUE (provider_id, principal_id, idempotency_key),
	CONSTRAINT ck_hierarchy_source_revisions_sequences CHECK (expected_provider_generation>=0 AND source_sequence=expected_provider_generation+1 AND authority_generation>=0 AND mutation_sequence>0 AND revision>=0 AND revision=expected_revision+1 AND expected_revision>=-1),
	CONSTRAINT ck_hierarchy_source_revisions_predecessor CHECK ((expected_revision=-1)=(predecessor_id IS NULL)),
	CONSTRAINT ck_hierarchy_source_revisions_operation_time CHECK (operation IN ('REPLACE','RETRACT') AND effective_at=recorded_at AND isfinite(effective_at)),
	CONSTRAINT ck_hierarchy_source_revisions_hashes CHECK (command_hash ~ '^[a-f0-9]{64}$' AND fact_hash ~ '^[a-f0-9]{64}$'),
	CONSTRAINT ck_hierarchy_source_revisions_idempotency_key_identifier CHECK (idempotency_key ~ '^[A-Za-z0-9_.:-]+$'),
	CONSTRAINT fk_hierarchy_source_revisions_principal_id_hierarchy_so_9229 FOREIGN KEY(principal_id) REFERENCES hierarchy_source_principals (id) ON DELETE RESTRICT,
	CONSTRAINT fk_hierarchy_source_revisions_grant_event_id_hierarchy__3f25 FOREIGN KEY(grant_event_id) REFERENCES hierarchy_source_authority (id) ON DELETE RESTRICT,
	CONSTRAINT fk_hierarchy_source_revisions_predecessor_id_hierarchy__17bd FOREIGN KEY(predecessor_id) REFERENCES hierarchy_source_revisions (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
)


;

CREATE TABLE hierarchy_source_mutations (
	provider_id UUID NOT NULL,
	mutation_sequence BIGINT NOT NULL,
	kind VARCHAR(20) NOT NULL,
	authority_event_id UUID,
	publication_id UUID,
	child_hash VARCHAR(64) NOT NULL,
	predecessor_hash VARCHAR(64),
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	journal_hash VARCHAR(64) NOT NULL,
	CONSTRAINT pk_hierarchy_source_mutations PRIMARY KEY (provider_id, mutation_sequence),
	CONSTRAINT fk_hierarchy_source_mutations_authority_event_id_hierar_5364 FOREIGN KEY(authority_event_id, provider_id, mutation_sequence) REFERENCES hierarchy_source_authority (id, provider_id, mutation_sequence) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
	CONSTRAINT fk_hierarchy_source_mutations_publication_id_hierarchy__537e FOREIGN KEY(publication_id, provider_id, mutation_sequence) REFERENCES hierarchy_source_revisions (id, provider_id, mutation_sequence) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
	CONSTRAINT ck_hierarchy_source_mutations_sequence_time CHECK (mutation_sequence>0 AND isfinite(recorded_at)),
	CONSTRAINT ck_hierarchy_source_mutations_typed_child CHECK ((kind='AUTHORITY' AND authority_event_id IS NOT NULL AND publication_id IS NULL) OR (kind='PUBLICATION' AND publication_id IS NOT NULL AND authority_event_id IS NULL)),
	CONSTRAINT ck_hierarchy_source_mutations_hashes CHECK (child_hash ~ '^[a-f0-9]{64}$' AND journal_hash ~ '^[a-f0-9]{64}$'),
	CONSTRAINT fk_hierarchy_source_mutations_provider_id_hierarchy_sou_83e8 FOREIGN KEY(provider_id) REFERENCES hierarchy_source_providers (id) ON DELETE RESTRICT
)

;
ALTER TABLE hierarchy_source_streams ADD CONSTRAINT fk_hierarchy_source_stream_head FOREIGN KEY(head_id, id, provider_id, head_revision) REFERENCES hierarchy_source_revisions (id, stream_id, provider_id, revision) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;

'''

FUNCTION_SQL = r'''

-- Structural roles have no credentials or provider capabilities.
DO $$ DECLARE n text; BEGIN
 FOREACH n IN ARRAY ARRAY['menuto_hierarchy_owner','menuto_hierarchy_admin','menuto_hierarchy_client'] LOOP
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname=n) THEN
   EXECUTE pg_catalog.format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS',n);
  END IF;
  IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname=n AND
    (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN
   RAISE EXCEPTION 'Unsafe existing reference infrastructure role';
  END IF;
 END LOOP;
 IF EXISTS (SELECT FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid=m.member WHERE r.rolname='menuto_hierarchy_owner') THEN RAISE EXCEPTION 'Source owner must not inherit external roles'; END IF;
END $$;
CREATE SCHEMA menuto_hierarchy AUTHORIZATION menuto_hierarchy_owner;
REVOKE ALL ON SCHEMA menuto_hierarchy FROM PUBLIC;
GRANT USAGE ON SCHEMA menuto_hierarchy TO menuto_hierarchy_admin, menuto_hierarchy_client;
GRANT USAGE ON SCHEMA public TO menuto_hierarchy_owner;

-- Backend-local TLS primitive, not pg_stat_ssl's role-filtered cross-session statistics.
-- Reuse a pre-existing deployment extension; newly installed objects belong to this schema.
DO $$ DECLARE ns name; BEGIN
 IF NOT EXISTS (SELECT FROM pg_catalog.pg_extension WHERE extname='sslinfo') THEN
  CREATE EXTENSION sslinfo WITH SCHEMA menuto_hierarchy;
 END IF;
 SELECT n.nspname INTO STRICT ns FROM pg_catalog.pg_extension e JOIN pg_catalog.pg_namespace n ON n.oid=e.extnamespace WHERE e.extname='sslinfo';
 EXECUTE format('GRANT USAGE ON SCHEMA %I TO menuto_hierarchy_owner',ns);
 EXECUTE format('GRANT EXECUTE ON FUNCTION %I.ssl_is_used() TO menuto_hierarchy_owner',ns);
 -- Parsed SQL body records an OID dependency. Dropping/replacing extension objects cannot
 -- silently redirect this helper to a caller-created shadow function.
 EXECUTE format('CREATE FUNCTION menuto_hierarchy.backend_tls() RETURNS boolean LANGUAGE sql STABLE SET search_path=pg_catalog,menuto_hierarchy,pg_temp BEGIN ATOMIC SELECT %I.ssl_is_used(); END',ns);
END $$;

CREATE FUNCTION menuto_hierarchy.utc(t timestamptz) RETURNS text LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
 SELECT to_char(t AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
$$;
CREATE FUNCTION menuto_hierarchy.canonical(j jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE r text; BEGIN
 CASE jsonb_typeof(j)
 WHEN 'object' THEN SELECT '{'||coalesce(string_agg(to_jsonb(key)::text||':'||menuto_hierarchy.canonical(value),',' ORDER BY key COLLATE "C"),'')||'}' INTO r FROM jsonb_each(j);
 WHEN 'array' THEN SELECT '['||coalesce(string_agg(menuto_hierarchy.canonical(value),',' ORDER BY ord),'')||']' INTO r FROM jsonb_array_elements(j) WITH ORDINALITY a(value,ord);
 WHEN 'number' THEN
  IF j::text !~ '^-?(0|[1-9][0-9]*)$' THEN RAISE EXCEPTION 'Exact integer required'; END IF; r:=j::text;
 ELSE r:=j::text;
 END CASE; RETURN r;
END $$;
CREATE FUNCTION menuto_hierarchy.hash(domain text,j jsonb) RETURNS text LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
 SELECT encode(sha256(convert_to(menuto_hierarchy.canonical(jsonb_build_object('domain',domain,'value',j)),'UTF8')),'hex')
$$;
CREATE FUNCTION menuto_hierarchy.keys(j jsonb, names text[]) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'object' OR
  (SELECT array_agg(k ORDER BY k) FROM jsonb_object_keys(j) k) IS DISTINCT FROM
  (SELECT array_agg(k ORDER BY k) FROM unnest(names) k) THEN
  RAISE EXCEPTION 'Closed command fields required';
 END IF;
END $$;
CREATE FUNCTION menuto_hierarchy.integer(j jsonb, lo bigint, hi bigint) RETURNS bigint LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE v bigint; BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'number' OR j::text !~ '^-?(0|[1-9][0-9]*)$' THEN RAISE EXCEPTION 'Strict integer required'; END IF;
 v:=j::text::bigint; IF v<lo OR v>hi THEN RAISE EXCEPTION 'Integer outside bounds'; END IF; RETURN v;
END $$;
CREATE FUNCTION menuto_hierarchy.identifier(j jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'string' OR length(j#>>'{}') NOT BETWEEN 1 AND 100 OR (j#>>'{}') !~ '^[A-Za-z0-9_.:-]+$' THEN RAISE EXCEPTION 'Invalid identifier'; END IF;
 RETURN j#>>'{}';
END $$;
CREATE FUNCTION menuto_hierarchy.uuid(j jsonb) RETURNS uuid LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE v uuid; BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'UUID string required'; END IF;
 v:=(j#>>'{}')::uuid;
 IF v::text<>(j#>>'{}') THEN RAISE EXCEPTION 'Canonical UUID required'; END IF; RETURN v;
END $$;
CREATE FUNCTION menuto_hierarchy.nonblank(t text) RETURNS boolean LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
 SELECT length(btrim(t, chr(9)||chr(10)||chr(11)||chr(12)||chr(13)||' '||U&'\0085\00A0\1680\2000\2001\2002\2003\2004\2005\2006\2007\2008\2009\200A\2028\2029\202F\205F\3000'))>0
$$;
CREATE FUNCTION menuto_hierarchy.reason(j jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'string' OR length(j#>>'{}') NOT BETWEEN 1 AND 4000 OR NOT menuto_hierarchy.nonblank(j#>>'{}') THEN RAISE EXCEPTION 'Review rationale required'; END IF; RETURN j#>>'{}';
END $$;
CREATE FUNCTION menuto_hierarchy.safe_role(login name, admin_mode boolean) RETURNS void LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE r record; dbowner oid; BEGIN
 SELECT * INTO r FROM pg_catalog.pg_roles WHERE rolname=login;
 SELECT datdba INTO dbowner FROM pg_catalog.pg_database WHERE datname=current_database();
 IF r.oid IS NULL OR NOT r.rolcanlogin OR r.oid=dbowner OR
  EXISTS (SELECT FROM pg_catalog.pg_roles x WHERE
    (x.rolsuper OR x.rolcreaterole OR x.rolcreatedb OR x.rolreplication OR x.rolbypassrls OR x.oid=dbowner OR x.rolname IN ('menuto_hierarchy_owner','menuto_hierarchy_catalog_owner','menuto_hierarchy_recipes_owner','menuto_prior_owner','menuto_prior_admin','menuto_prior_client')
      OR (NOT admin_mode AND x.rolname='menuto_hierarchy_admin'))
    AND pg_catalog.pg_has_role(r.oid,x.oid,'MEMBER')) OR
  has_schema_privilege(login,'menuto_hierarchy','CREATE') THEN
  RAISE EXCEPTION 'Unsafe source login' USING ERRCODE='42501';
 END IF;
 IF EXISTS (SELECT FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relname LIKE 'hierarchy_source_%' AND c.relkind='r'
   AND (has_table_privilege(login,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') OR c.relowner=r.oid)) THEN
  RAISE EXCEPTION 'Source login has direct mutation privileges' USING ERRCODE='42501';
 END IF;
END $$;
CREATE FUNCTION menuto_hierarchy.session_fact(admin_mode boolean) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE r record; d record; addr inet; BEGIN
 IF system_user IS DISTINCT FROM ('scram-sha-256:'||session_user) THEN
  RAISE EXCEPTION 'SCRAM authenticated original session required' USING ERRCODE='28000';
 END IF;
 PERFORM menuto_hierarchy.safe_role(session_user,admin_mode);
 IF admin_mode AND NOT pg_catalog.pg_has_role(session_user,'menuto_hierarchy_admin','MEMBER') THEN
  RAISE EXCEPTION 'Enrollment administrator required' USING ERRCODE='42501';
 END IF;
 addr:=inet_client_addr();
 IF addr IS NULL OR (addr NOT IN ('127.0.0.1'::inet,'::1'::inet) AND NOT menuto_hierarchy.backend_tls()) THEN
  RAISE EXCEPTION 'Remote reference sessions require TLS' USING ERRCODE='28000';
 END IF;
 SELECT oid,rolname INTO r FROM pg_catalog.pg_roles WHERE rolname=session_user;
 SELECT oid,datname INTO d FROM pg_catalog.pg_database WHERE datname=current_database();
 RETURN jsonb_build_object('database_oid',d.oid::bigint,'database_name',d.datname,'role_oid',r.oid::bigint,'role_name',r.rolname,'authentication_method','scram-sha-256','authenticated_identity',r.rolname);
END $$;
CREATE FUNCTION menuto_hierarchy.audit(s jsonb,t timestamptz) RETURNS jsonb LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
 SELECT jsonb_build_object('actor_database_oid',s->'database_oid','actor_database_name',s->'database_name','actor_role_oid',s->'role_oid','actor_role_name',s->'role_name','actor_authentication_method',s->'authentication_method','actor_authenticated_identity',s->'authenticated_identity','recorded_at',menuto_hierarchy.utc(t))
$$;
CREATE FUNCTION menuto_hierarchy.actor(d jsonb) RETURNS jsonb LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
 SELECT jsonb_build_object('database_oid',d->'actor_database_oid','database_name',d->'actor_database_name','role_oid',d->'actor_role_oid','role_name',d->'actor_role_name','authentication_method',d->'actor_authentication_method','authenticated_identity',d->'actor_authenticated_identity')
$$;

CREATE FUNCTION menuto_hierarchy.provider_fact(d jsonb) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
 SELECT jsonb_build_object('id',d->'id','command',jsonb_build_object('code',d->'code','version',d->'version','source_system',d->'source_system','remit',d->'remit','idempotency_key',d->'idempotency_key'),'administrator',menuto_hierarchy.actor(d),'recorded_at',menuto_hierarchy.utc((d->>'recorded_at')::timestamptz),'command_hash',d->'command_hash')
$$;
CREATE FUNCTION menuto_hierarchy.principal_fact(d jsonb) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
 SELECT jsonb_build_object('id',d->'id','command',jsonb_build_object('role_name',d->'role_name','idempotency_key',d->'idempotency_key'),'database_oid',d->'database_oid','database_name',d->'database_name','role_oid',d->'role_oid','role_name',d->'role_name','administrator',menuto_hierarchy.actor(d),'recorded_at',menuto_hierarchy.utc((d->>'recorded_at')::timestamptz),'command_hash',d->'command_hash')
$$;
CREATE FUNCTION menuto_hierarchy.authority_fact(d jsonb) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
 SELECT jsonb_build_object('id',d->'id','command',jsonb_build_object('provider_id',d->'provider_id','principal_id',d->'principal_id','capability',d->'capability','action',d->'action','expected_authority_generation',d->'expected_authority_generation','reason',d->'reason','idempotency_key',d->'idempotency_key'),'administrator',menuto_hierarchy.actor(d),'recorded_at',menuto_hierarchy.utc((d->>'recorded_at')::timestamptz),'authority_sequence',d->'authority_sequence','mutation_sequence',d->'mutation_sequence','command_hash',d->'command_hash','fact_hash',d->'fact_hash')
$$;

CREATE FUNCTION menuto_hierarchy.mutation_fact(d jsonb) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
 SELECT jsonb_build_object('provider_id',d->'provider_id','mutation_sequence',d->'mutation_sequence','kind',d->'kind','child_id',coalesce(nullif(d->'authority_event_id','null'::jsonb),d->'publication_id'),'child_hash',d->'child_hash','predecessor_hash',d->'predecessor_hash','recorded_at',menuto_hierarchy.utc((d->>'recorded_at')::timestamptz),'journal_hash',d->'journal_hash')
$$;
CREATE FUNCTION menuto_hierarchy.append_mutation(p uuid, seq bigint, k text, child uuid, h text, t timestamptz, prev text) RETURNS jsonb LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE d jsonb; f jsonb; BEGIN
 IF EXISTS (SELECT FROM public.hierarchy_source_mutations WHERE provider_id=p AND recorded_at>t) OR EXISTS (SELECT FROM public.hierarchy_source_providers WHERE id=p AND recorded_at>t) OR EXISTS (SELECT FROM public.hierarchy_source_principals x JOIN public.hierarchy_source_authority a ON a.principal_id=x.id WHERE a.provider_id=p AND x.recorded_at>t) THEN RAISE EXCEPTION 'Source clock regression'; END IF;
 d:=jsonb_build_object('provider_id',p,'mutation_sequence',seq,'kind',k,'authority_event_id',CASE WHEN k='AUTHORITY' THEN child END,'publication_id',CASE WHEN k='PUBLICATION' THEN child END,'child_hash',h,'predecessor_hash',prev,'recorded_at',menuto_hierarchy.utc(t));
 f:=menuto_hierarchy.mutation_fact(d);
 d:=d||jsonb_build_object('journal_hash',menuto_hierarchy.hash('hierarchy.mutation.v1',f-'journal_hash'));
 INSERT INTO public.hierarchy_source_mutations SELECT * FROM jsonb_populate_record(NULL::public.hierarchy_source_mutations,d);
 RETURN menuto_hierarchy.mutation_fact(d);
END $$;
CREATE FUNCTION menuto_hierarchy.principal(s jsonb) RETURNS uuid LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE id uuid; BEGIN
 SELECT p.id INTO id FROM public.hierarchy_source_principals p WHERE p.database_oid=(s->>'database_oid')::bigint AND p.database_name=s->>'database_name' AND p.role_oid=(s->>'role_oid')::bigint AND p.role_name=s->>'role_name';
 IF id IS NULL THEN RAISE EXCEPTION 'Login is not enrolled' USING ERRCODE='42501'; END IF; RETURN id;
END $$;
CREATE FUNCTION menuto_hierarchy.permission(p uuid, who uuid, cap text) RETURNS uuid LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE a record; BEGIN
 SELECT id,action INTO a FROM public.hierarchy_source_authority WHERE provider_id=p AND principal_id=who AND capability=cap ORDER BY authority_sequence DESC LIMIT 1;
 IF a.id IS NULL OR a.action<>'GRANT' THEN RAISE EXCEPTION 'Provider capability denied' USING ERRCODE='42501'; END IF; RETURN a.id;
END $$;

CREATE FUNCTION menuto_hierarchy.register_provider(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE s jsonb:=menuto_hierarchy.session_fact(true); d jsonb; h text; t timestamptz:=clock_timestamp(); old record; BEGIN
 PERFORM menuto_hierarchy.keys(c,ARRAY['code','version','source_system','remit','idempotency_key']);
 PERFORM menuto_hierarchy.identifier(c->'code'); PERFORM menuto_hierarchy.identifier(c->'version'); PERFORM menuto_hierarchy.identifier(c->'source_system'); PERFORM menuto_hierarchy.identifier(c->'idempotency_key'); PERFORM menuto_hierarchy.reason(c->'remit');
 -- Registry creation has no provider frontier yet; serialize administrative enrollment globally.
 PERFORM pg_advisory_xact_lock(140015,1);
 h:=menuto_hierarchy.hash('hierarchy.provider-command.v1',c);
 SELECT * INTO old FROM public.hierarchy_source_providers WHERE actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF old.id IS NOT NULL THEN
  IF old.command_hash<>h THEN RAISE EXCEPTION 'Idempotency conflict'; END IF;
  RETURN menuto_hierarchy.provider_fact(to_jsonb(old));
 END IF;
 d:= c||menuto_hierarchy.audit(s,t)||jsonb_build_object('id',gen_random_uuid(),'command_hash',h);
 INSERT INTO public.hierarchy_source_providers SELECT * FROM jsonb_populate_record(NULL::public.hierarchy_source_providers,d);
 INSERT INTO public.hierarchy_source_frontiers VALUES ((d->>'id')::uuid,0,0,0,NULL,NULL,NULL);
 RETURN menuto_hierarchy.provider_fact(d);
END $$;
CREATE FUNCTION menuto_hierarchy.enroll_principal(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE s jsonb:=menuto_hierarchy.session_fact(true); d jsonb; h text; r record; old record; BEGIN
 PERFORM menuto_hierarchy.keys(c,ARRAY['role_name','idempotency_key']);
 IF jsonb_typeof(c->'role_name') IS DISTINCT FROM 'string' OR length(c->>'role_name') NOT BETWEEN 1 AND 63 OR (c->>'role_name') ~ '[[:cntrl:]]' THEN RAISE EXCEPTION 'Invalid role name'; END IF;
 PERFORM menuto_hierarchy.identifier(c->'idempotency_key');
 PERFORM pg_advisory_xact_lock(140015,1);
 PERFORM menuto_hierarchy.safe_role((c->>'role_name')::name,false);
 SELECT oid,rolname INTO r FROM pg_catalog.pg_roles WHERE rolname=c->>'role_name';
 h:=menuto_hierarchy.hash('hierarchy.principal-command.v1',c);
 SELECT * INTO old FROM public.hierarchy_source_principals WHERE actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF old.id IS NOT NULL THEN
  IF old.command_hash<>h OR old.role_oid<>r.oid::bigint THEN RAISE EXCEPTION 'Idempotency or immutable binding conflict'; END IF;
  RETURN menuto_hierarchy.principal_fact(to_jsonb(old));
 END IF;
 d:=c||menuto_hierarchy.audit(s,clock_timestamp())||jsonb_build_object('id',gen_random_uuid(),'command_hash',h,'database_oid',s->'database_oid','database_name',s->'database_name','role_oid',r.oid::bigint);
 INSERT INTO public.hierarchy_source_principals SELECT * FROM jsonb_populate_record(NULL::public.hierarchy_source_principals,d);
 RETURN menuto_hierarchy.principal_fact(d);
END $$;
CREATE FUNCTION menuto_hierarchy.change_authority(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE s jsonb:=menuto_hierarchy.session_fact(true); p uuid; who uuid; f record; old record; last_action text; h text; d jsonb; fact jsonb; m jsonb; t timestamptz; BEGIN
 PERFORM menuto_hierarchy.keys(c,ARRAY['provider_id','principal_id','capability','action','expected_authority_generation','reason','idempotency_key']);
 p:=menuto_hierarchy.uuid(c->'provider_id'); who:=menuto_hierarchy.uuid(c->'principal_id');
 PERFORM menuto_hierarchy.integer(c->'expected_authority_generation',0,9223372036854775807);
 PERFORM menuto_hierarchy.reason(c->'reason'); PERFORM menuto_hierarchy.identifier(c->'idempotency_key');
 IF c->>'capability' NOT IN ('REVIEW_PUBLISH','RETRACT','CAPTURE') OR c->>'action' NOT IN ('GRANT','REVOKE') THEN RAISE EXCEPTION 'Invalid authority mutation'; END IF;
 SELECT * INTO f FROM public.hierarchy_source_frontiers WHERE provider_id=p FOR UPDATE;
 IF f.provider_id IS NULL THEN RAISE EXCEPTION 'Unknown provider'; END IF;
 PERFORM menuto_hierarchy.check_provider_binding(p,s);
 IF NOT EXISTS (SELECT FROM public.hierarchy_source_principals WHERE id=who) THEN RAISE EXCEPTION 'Unknown principal'; END IF;
 h:=menuto_hierarchy.hash('hierarchy.authority-command.v1',c);
 SELECT * INTO old FROM public.hierarchy_source_authority WHERE provider_id=p AND actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF old.id IS NOT NULL THEN
  IF old.command_hash<>h THEN RAISE EXCEPTION 'Idempotency conflict'; END IF; RETURN menuto_hierarchy.authority_fact(to_jsonb(old));
 END IF;
 IF f.authority_generation<>(c->>'expected_authority_generation')::bigint THEN RAISE EXCEPTION 'Authority CAS conflict' USING ERRCODE='40001'; END IF;
 SELECT action INTO last_action FROM public.hierarchy_source_authority WHERE provider_id=p AND principal_id=who AND capability=c->>'capability' ORDER BY authority_sequence DESC LIMIT 1;
 IF last_action=c->>'action' OR (last_action IS NULL AND c->>'action'='REVOKE') THEN RAISE EXCEPTION 'Authority no-op'; END IF;
 t:=clock_timestamp();
 d:=c||menuto_hierarchy.audit(s,t)||jsonb_build_object('id',gen_random_uuid(),'authority_sequence',f.authority_generation+1,'mutation_sequence',f.mutation_generation+1,'command_hash',h);
 fact:=menuto_hierarchy.authority_fact(d);
 d:=d||jsonb_build_object('fact_hash',menuto_hierarchy.hash('hierarchy.authority.v1',fact-'fact_hash'));
 INSERT INTO public.hierarchy_source_authority SELECT * FROM jsonb_populate_record(NULL::public.hierarchy_source_authority,d);
 m:=menuto_hierarchy.append_mutation(p,f.mutation_generation+1,'AUTHORITY',(d->>'id')::uuid,d->>'fact_hash',t,f.mutation_head_hash);
 UPDATE public.hierarchy_source_frontiers SET authority_generation=f.authority_generation+1,mutation_generation=f.mutation_generation+1,authority_head_id=(d->>'id')::uuid,mutation_head_hash=m->>'journal_hash' WHERE provider_id=p;
 RETURN menuto_hierarchy.authority_fact(d);
END $$;

-- Canonical literal locators form a conservative ASCII HTTP(S) subset. This prevents
-- a raw SQL caller from storing a URL that the contract parser would rewrite.
CREATE FUNCTION menuto_hierarchy.check_uri(j jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
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


CREATE FUNCTION menuto_hierarchy.command_schema() RETURNS jsonb LANGUAGE sql IMMUTABLE SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $schema$ SELECT '{"$defs": {"CulinaryFeaturePathKey": {"additionalProperties": false, "properties": {"contract_version": {"const": "culinary-feature-applicability.v1", "default": "culinary-feature-applicability.v1", "title": "Contract Version", "type": "string"}, "dimension": {"enum": ["FLAVOR", "MAIN_PROTEIN"], "title": "Dimension", "type": "string"}, "recipe_version_id": {"format": "uuid", "title": "Recipe Version Id", "type": "string"}, "scope": {"enum": ["EXACT_PATH", "REVIEWED_SCOPE"], "title": "Scope", "type": "string"}, "slots": {"items": {"$ref": "#/$defs/FeatureSlotApplicability"}, "minItems": 1, "title": "Slots", "type": "array"}, "tier_ids": {"items": {"format": "uuid", "type": "string"}, "minItems": 1, "title": "Tier Ids", "type": "array"}}, "required": ["recipe_version_id", "dimension", "scope", "tier_ids", "slots"], "title": "CulinaryFeaturePathKey", "type": "object"}, "EvidenceKind": {"enum": ["USER", "REVIEWED_REFERENCE", "RETAIL_OBSERVATION", "RECEIPT"], "title": "EvidenceKind", "type": "string"}, "ExactTargetPriorCompatibilityPolicy": {"additionalProperties": false, "properties": {"contract_version": {"const": "exact-target-prior-compatibility-policy.v1", "default": "exact-target-prior-compatibility-policy.v1", "title": "Contract Version", "type": "string"}, "coordinate_id": {"const": "MEMBER_PROFILE_AFFINITY", "default": "MEMBER_PROFILE_AFFINITY", "title": "Coordinate Id", "type": "string"}, "coordinate_version": {"const": 1, "default": 1, "title": "Coordinate Version", "type": "integer"}, "explicit_maps": {"items": {"$ref": "#/$defs/ExplicitTargetKindCompatibilityMap"}, "maxItems": 5, "minItems": 5, "title": "Explicit Maps", "type": "array"}, "explicit_policy_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Explicit Policy Fingerprint", "type": "string"}, "explicit_policy_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Explicit Policy Id", "type": "string"}, "explicit_policy_version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Explicit Policy Version", "type": "string"}, "interpretation_mode": {"const": "VERSIONED_CONSUMER_POLICY_REPLAY", "default": "VERSIONED_CONSUMER_POLICY_REPLAY", "title": "Interpretation Mode", "type": "string"}, "policy_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Policy Id", "type": "string"}, "policy_version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Policy Version", "type": "string"}, "provenance": {"$ref": "#/$defs/Provenance"}, "provider_command_hash": {"pattern": "^[a-f0-9]{64}$", "title": "Provider Command Hash", "type": "string"}, "provider_id": {"format": "uuid", "title": "Provider Id", "type": "string"}, "reference_coordinate": {"$ref": "#/$defs/ReferencePriorCoordinate"}, "reference_mapping_mode": {"const": "FINITE_EXACT_LOOKUP", "default": "FINITE_EXACT_LOOKUP", "title": "Reference Mapping Mode", "type": "string"}, "reference_maps": {"items": {"$ref": "#/$defs/ReferenceTargetKindCompatibilityMap"}, "maxItems": 5, "minItems": 5, "title": "Reference Maps", "type": "array"}, "scope": {"const": "ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY", "default": "ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY", "title": "Scope", "type": "string"}, "unit": {"const": "POLICY_MEMBER_PROFILE_AFFINITY_UNITS", "default": "POLICY_MEMBER_PROFILE_AFFINITY_UNITS", "title": "Unit", "type": "string"}}, "required": ["policy_id", "policy_version", "provenance", "explicit_policy_id", "explicit_policy_version", "explicit_policy_fingerprint", "provider_id", "provider_command_hash", "reference_coordinate", "explicit_maps", "reference_maps"], "title": "ExactTargetPriorCompatibilityPolicy", "type": "object"}, "ExplicitAffinityAmount": {"additionalProperties": false, "properties": {"contract_version": {"const": "explicit-affinity-amount.v1", "default": "explicit-affinity-amount.v1", "title": "Contract Version", "type": "string"}, "denominator": {"exclusiveMinimum": 0, "title": "Denominator", "type": "integer"}, "numerator": {"title": "Numerator", "type": "integer"}, "unit": {"const": "POLICY_EXPLICIT_AFFINITY_UNITS", "default": "POLICY_EXPLICIT_AFFINITY_UNITS", "title": "Unit", "type": "string"}}, "required": ["numerator", "denominator"], "title": "ExplicitAffinityAmount", "type": "object"}, "ExplicitAffinityValueRule": {"additionalProperties": false, "properties": {"amount": {"$ref": "#/$defs/ExplicitAffinityAmount"}, "value": {"enum": ["LIKE", "DISLIKE", "NEUTRAL"], "title": "Value", "type": "string"}}, "required": ["value", "amount"], "title": "ExplicitAffinityValueRule", "type": "object"}, "ExplicitAuthorshipStrengthRule": {"additionalProperties": false, "properties": {"authorship": {"enum": ["SELF", "AUTHORIZED_REPRESENTATIVE"], "title": "Authorship", "type": "string"}, "level": {"enum": ["LOW", "MEDIUM", "HIGH"], "title": "Level", "type": "string"}}, "required": ["authorship", "level"], "title": "ExplicitAuthorshipStrengthRule", "type": "object"}, "ExplicitProfileMappingRule": {"additionalProperties": false, "properties": {"expected_explicit_amount": {"$ref": "#/$defs/ExplicitAffinityAmount"}, "output_amount": {"$ref": "#/$defs/MemberProfileAffinityAmount"}, "value": {"enum": ["LIKE", "DISLIKE", "NEUTRAL"], "title": "Value", "type": "string"}}, "required": ["value", "expected_explicit_amount", "output_amount"], "title": "ExplicitProfileMappingRule", "type": "object"}, "ExplicitTargetAffinityPolicy": {"additionalProperties": false, "properties": {"contract_version": {"const": "explicit-target-affinity-policy.v1", "default": "explicit-target-affinity-policy.v1", "title": "Contract Version", "type": "string"}, "evidence_basis": {"const": "LATEST_ACTIVE_EXPLICIT_DECLARATION_ONLY", "default": "LATEST_ACTIVE_EXPLICIT_DECLARATION_ONLY", "title": "Evidence Basis", "type": "string"}, "interpretation_mode": {"const": "EXPLICIT_POLICY_VERSION_REPLAY", "default": "EXPLICIT_POLICY_VERSION_REPLAY", "title": "Interpretation Mode", "type": "string"}, "policy_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Policy Id", "type": "string"}, "policy_version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Policy Version", "type": "string"}, "prior_mode": {"const": "UNAVAILABLE_ONLY", "default": "UNAVAILABLE_ONLY", "title": "Prior Mode", "type": "string"}, "provenance": {"$ref": "#/$defs/Provenance"}, "shrinkage_mode": {"const": "UNAVAILABLE_ONLY", "default": "UNAVAILABLE_ONLY", "title": "Shrinkage Mode", "type": "string"}, "target_policies": {"items": {"$ref": "#/$defs/ExplicitTargetKindPolicy"}, "title": "Target Policies", "type": "array"}}, "required": ["policy_id", "policy_version", "provenance", "target_policies"], "title": "ExplicitTargetAffinityPolicy", "type": "object"}, "ExplicitTargetKindCompatibilityMap": {"additionalProperties": false, "properties": {"rows": {"items": {"$ref": "#/$defs/ExplicitProfileMappingRule"}, "maxItems": 3, "minItems": 3, "title": "Rows", "type": "array"}, "target_kind": {"enum": ["INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"], "title": "Target Kind", "type": "string"}}, "required": ["target_kind", "rows"], "title": "ExplicitTargetKindCompatibilityMap", "type": "object"}, "ExplicitTargetKindPolicy": {"additionalProperties": false, "properties": {"affinity_rules": {"items": {"$ref": "#/$defs/ExplicitAffinityValueRule"}, "title": "Affinity Rules", "type": "array"}, "retracted_strength": {"const": "NONE", "title": "Retracted Strength", "type": "string"}, "strength_rules": {"items": {"$ref": "#/$defs/ExplicitAuthorshipStrengthRule"}, "title": "Strength Rules", "type": "array"}, "target_kind": {"enum": ["INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"], "title": "Target Kind", "type": "string"}, "undeclared_strength": {"const": "NONE", "title": "Undeclared Strength", "type": "string"}}, "required": ["target_kind", "affinity_rules", "strength_rules", "undeclared_strength", "retracted_strength"], "title": "ExplicitTargetKindPolicy", "type": "object"}, "FeaturePreferenceTarget": {"additionalProperties": false, "properties": {"feature_term_id": {"format": "uuid", "title": "Feature Term Id", "type": "string"}, "kind": {"enum": ["PROTEIN", "METHOD", "FLAVOR"], "title": "Kind", "type": "string"}}, "required": ["kind", "feature_term_id"], "title": "FeaturePreferenceTarget", "type": "object"}, "FeatureSelectedPath": {"additionalProperties": false, "properties": {"deltas": {"items": {"maxItems": 2, "minItems": 2, "prefixItems": [{"format": "uuid", "type": "string"}, {"anyOf": [{"type": "number"}, {"type": "string"}], "decimal_places": 6, "max_digits": 18}], "type": "array"}, "title": "Deltas", "type": "array"}, "selected_rule_ids": {"items": {"format": "uuid", "type": "string"}, "title": "Selected Rule Ids", "type": "array"}, "tier_id": {"format": "uuid", "title": "Tier Id", "type": "string"}}, "required": ["tier_id", "selected_rule_ids", "deltas"], "title": "FeatureSelectedPath", "type": "object"}, "FeatureSlotApplicability": {"additionalProperties": false, "properties": {"adjustment": {"enum": ["ZERO_ONLY", "AUTHORED_ENVELOPE"], "title": "Adjustment", "type": "string"}, "choice": {"enum": ["BASE", "RULE", "ANY_AUTHORED_CHOICE"], "title": "Choice", "type": "string"}, "preparation": {"enum": ["NONE", "TRANSFORMATION", "ANY_AUTHORED_PATH_CONTEXT"], "title": "Preparation", "type": "string"}, "requirement_id": {"format": "uuid", "title": "Requirement Id", "type": "string"}, "selected_rule_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Selected Rule Id"}, "transformation_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Transformation Id"}}, "required": ["requirement_id", "choice", "selected_rule_id", "preparation", "transformation_id", "adjustment"], "title": "FeatureSlotApplicability", "type": "object"}, "HierarchyDirectionPolicy": {"additionalProperties": false, "properties": {"attenuation": {"anyOf": [{"$ref": "#/$defs/HierarchyPolicyAmount"}, {"type": "null"}]}, "destination_kind": {"enum": ["INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"], "title": "Destination Kind", "type": "string"}, "enabled": {"title": "Enabled", "type": "boolean"}, "rows": {"items": {"$ref": "#/$defs/HierarchyTransferMapRow"}, "title": "Rows", "type": "array"}, "source_kind": {"enum": ["INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"], "title": "Source Kind", "type": "string"}, "support_modes": {"items": {"enum": ["REVIEWED_EXACT_PAIR", "CLASSIFICATION_BOUND_PAIR"], "type": "string"}, "title": "Support Modes", "type": "array"}}, "required": ["source_kind", "destination_kind", "enabled", "support_modes", "rows", "attenuation"], "title": "HierarchyDirectionPolicy", "type": "object"}, "HierarchyPolicyAmount": {"additionalProperties": false, "properties": {"denominator": {"exclusiveMinimum": 0, "maximum": 2147483647, "title": "Denominator", "type": "integer"}, "numerator": {"maximum": 2147483647, "minimum": -2147483647, "title": "Numerator", "type": "integer"}}, "required": ["numerator", "denominator"], "title": "HierarchyPolicyAmount", "type": "object"}, "HierarchyProvenance": {"additionalProperties": false, "properties": {"content_hash": {"pattern": "^[a-f0-9]{64}$", "title": "Content Hash", "type": "string"}, "external_record_id": {"maxLength": 2048, "minLength": 1, "title": "External Record Id", "type": "string"}, "kind": {"const": "REVIEWED_REFERENCE", "default": "REVIEWED_REFERENCE", "title": "Kind", "type": "string"}, "observed_at": {"format": "date-time", "title": "Observed At", "type": "string"}, "source_system": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Source System", "type": "string"}, "source_uri": {"anyOf": [{"format": "uri", "maxLength": 2048, "minLength": 1, "type": "string"}, {"type": "null"}], "default": null, "title": "Source Uri"}, "source_version": {"maxLength": 200, "minLength": 1, "title": "Source Version", "type": "string"}}, "required": ["source_system", "external_record_id", "source_version", "content_hash", "observed_at"], "title": "HierarchyProvenance", "type": "object"}, "HierarchyRecipeBinding": {"additionalProperties": false, "properties": {"endpoint": {"enum": ["SOURCE", "DESTINATION"], "title": "Endpoint", "type": "string"}, "key": {"anyOf": [{"discriminator": {"mapping": {"FLAVOR": "#/$defs/CulinaryFeaturePathKey", "MAIN_PROTEIN": "#/$defs/CulinaryFeaturePathKey", "METHOD": "#/$defs/RecipeMethodContextKey"}, "propertyName": "dimension"}, "oneOf": [{"$ref": "#/$defs/RecipeMethodContextKey"}, {"$ref": "#/$defs/CulinaryFeaturePathKey"}]}, {"type": "null"}], "title": "Key"}, "path": {"anyOf": [{"$ref": "#/$defs/FeatureSelectedPath"}, {"type": "null"}]}, "recipe_version_id": {"format": "uuid", "title": "Recipe Version Id", "type": "string"}}, "required": ["endpoint", "recipe_version_id", "key", "path"], "title": "HierarchyRecipeBinding", "type": "object"}, "HierarchyRelationBody": {"additionalProperties": false, "properties": {"catalog_review_ids": {"items": {"format": "uuid", "type": "string"}, "title": "Catalog Review Ids", "type": "array"}, "policy_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Policy Fingerprint", "type": "string"}, "policy_revision_id": {"format": "uuid", "title": "Policy Revision Id", "type": "string"}, "support_mode": {"enum": ["REVIEWED_EXACT_PAIR", "CLASSIFICATION_BOUND_PAIR"], "title": "Support Mode", "type": "string"}, "support_review_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Support Review Id"}}, "required": ["policy_revision_id", "policy_fingerprint", "support_mode", "support_review_id", "catalog_review_ids"], "title": "HierarchyRelationBody", "type": "object"}, "HierarchyStreamIdentity": {"additionalProperties": false, "properties": {"destination": {"anyOf": [{"discriminator": {"mapping": {"DIRECT_RECIPE": "#/$defs/RecipePreferenceTarget", "FLAVOR": "#/$defs/FeaturePreferenceTarget", "INGREDIENT": "#/$defs/IngredientPreferenceTarget", "METHOD": "#/$defs/FeaturePreferenceTarget", "PROTEIN": "#/$defs/FeaturePreferenceTarget"}, "propertyName": "kind"}, "oneOf": [{"$ref": "#/$defs/IngredientPreferenceTarget"}, {"$ref": "#/$defs/RecipePreferenceTarget"}, {"$ref": "#/$defs/FeaturePreferenceTarget"}]}, {"type": "null"}], "title": "Destination"}, "kind": {"enum": ["POLICY", "RELATION"], "title": "Kind", "type": "string"}, "policy_id": {"format": "uuid", "title": "Policy Id", "type": "string"}, "recipe_bindings": {"items": {"$ref": "#/$defs/HierarchyRecipeBinding"}, "title": "Recipe Bindings", "type": "array"}, "source": {"anyOf": [{"discriminator": {"mapping": {"DIRECT_RECIPE": "#/$defs/RecipePreferenceTarget", "FLAVOR": "#/$defs/FeaturePreferenceTarget", "INGREDIENT": "#/$defs/IngredientPreferenceTarget", "METHOD": "#/$defs/FeaturePreferenceTarget", "PROTEIN": "#/$defs/FeaturePreferenceTarget"}, "propertyName": "kind"}, "oneOf": [{"$ref": "#/$defs/IngredientPreferenceTarget"}, {"$ref": "#/$defs/RecipePreferenceTarget"}, {"$ref": "#/$defs/FeaturePreferenceTarget"}]}, {"type": "null"}], "title": "Source"}}, "required": ["kind", "policy_id", "source", "destination", "recipe_bindings"], "title": "HierarchyStreamIdentity", "type": "object"}, "HierarchyTransferMapRow": {"additionalProperties": false, "properties": {"expected_source_amount": {"$ref": "#/$defs/ExplicitAffinityAmount"}, "output_amount": {"$ref": "#/$defs/HierarchyPolicyAmount"}, "source_affinity_value": {"enum": ["LIKE", "DISLIKE", "NEUTRAL"], "title": "Source Affinity Value", "type": "string"}, "source_descriptor": {"$ref": "#/$defs/MemberProfileAffinityCoordinate"}}, "required": ["source_descriptor", "source_affinity_value", "expected_source_amount", "output_amount"], "title": "HierarchyTransferMapRow", "type": "object"}, "HierarchyTransferPolicy": {"additionalProperties": false, "properties": {"compatibility_policy": {"$ref": "#/$defs/ExactTargetPriorCompatibilityPolicy"}, "contract_version": {"const": "hierarchy-transfer-policy.v1", "default": "hierarchy-transfer-policy.v1", "title": "Contract Version", "type": "string"}, "directions": {"items": {"$ref": "#/$defs/HierarchyDirectionPolicy"}, "maxItems": 25, "minItems": 25, "title": "Directions", "type": "array"}, "explicit_policy": {"$ref": "#/$defs/ExplicitTargetAffinityPolicy"}, "multiple_parents": {"const": "UNAVAILABLE_NO_AGGREGATION", "default": "UNAVAILABLE_NO_AGGREGATION", "title": "Multiple Parents", "type": "string"}, "policy_id": {"format": "uuid", "title": "Policy Id", "type": "string"}, "policy_ownership": {"const": "HIERARCHY_COMPATIBILITY_REPLAY_ONLY", "default": "HIERARCHY_COMPATIBILITY_REPLAY_ONLY", "title": "Policy Ownership", "type": "string"}, "policy_version": {"exclusiveMinimum": 0, "maximum": 2147483647, "title": "Policy Version", "type": "integer"}, "precedence": {"const": "DIRECT_DECLARATION_WINS_RETRACTION_SUPPRESSES", "default": "DIRECT_DECLARATION_WINS_RETRACTION_SUPPRESSES", "title": "Precedence", "type": "string"}, "provenance": {"$ref": "#/$defs/HierarchyProvenance"}, "source_values": {"const": "CURRENT_MAPPED_EXPLICIT_ONLY", "default": "CURRENT_MAPPED_EXPLICIT_ONLY", "title": "Source Values", "type": "string"}, "traversal": {"const": "ONE_HOP_NO_INHERITED_PARENTS", "default": "ONE_HOP_NO_INHERITED_PARENTS", "title": "Traversal", "type": "string"}}, "required": ["policy_id", "policy_version", "explicit_policy", "compatibility_policy", "directions", "provenance"], "title": "HierarchyTransferPolicy", "type": "object"}, "IngredientPreferenceTarget": {"additionalProperties": false, "properties": {"ingredient_id": {"format": "uuid", "title": "Ingredient Id", "type": "string"}, "kind": {"const": "INGREDIENT", "default": "INGREDIENT", "title": "Kind", "type": "string"}}, "required": ["ingredient_id"], "title": "IngredientPreferenceTarget", "type": "object"}, "MemberProfileAffinityAmount": {"additionalProperties": false, "description": "Numeric component only. Consumer operations require ScopedMemberProfileAffinity.", "properties": {"denominator": {"exclusiveMinimum": 0, "maximum": 340282366920938463463374607431768211455, "title": "Denominator", "type": "integer"}, "numerator": {"maximum": 340282366920938463463374607431768211455, "minimum": -340282366920938463463374607431768211455, "title": "Numerator", "type": "integer"}}, "required": ["numerator", "denominator"], "title": "MemberProfileAffinityAmount", "type": "object"}, "MemberProfileAffinityCoordinate": {"additionalProperties": false, "properties": {"compatibility_policy_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Compatibility Policy Fingerprint", "type": "string"}, "coordinate_id": {"const": "MEMBER_PROFILE_AFFINITY", "default": "MEMBER_PROFILE_AFFINITY", "title": "Coordinate Id", "type": "string"}, "coordinate_version": {"const": 1, "default": 1, "title": "Coordinate Version", "type": "integer"}, "scope": {"const": "ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY", "default": "ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY", "title": "Scope", "type": "string"}, "target_kind": {"enum": ["INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"], "title": "Target Kind", "type": "string"}, "unit": {"const": "POLICY_MEMBER_PROFILE_AFFINITY_UNITS", "default": "POLICY_MEMBER_PROFILE_AFFINITY_UNITS", "title": "Unit", "type": "string"}}, "required": ["target_kind", "compatibility_policy_fingerprint"], "title": "MemberProfileAffinityCoordinate", "type": "object"}, "Provenance": {"additionalProperties": false, "properties": {"content_hash": {"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null, "title": "Content Hash"}, "external_record_id": {"maxLength": 2048, "minLength": 1, "title": "External Record Id", "type": "string"}, "kind": {"$ref": "#/$defs/EvidenceKind"}, "observed_at": {"format": "date-time", "title": "Observed At", "type": "string"}, "source_system": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Source System", "type": "string"}, "source_uri": {"anyOf": [{"format": "uri", "maxLength": 2048, "minLength": 1, "type": "string"}, {"type": "null"}], "default": null, "title": "Source Uri"}, "source_version": {"maxLength": 200, "minLength": 1, "title": "Source Version", "type": "string"}}, "required": ["kind", "source_system", "external_record_id", "source_version", "observed_at"], "title": "Provenance", "type": "object"}, "RecipeMethodContextKey": {"additionalProperties": false, "properties": {"contract_version": {"const": "culinary-feature-applicability.v1", "default": "culinary-feature-applicability.v1", "title": "Contract Version", "type": "string"}, "dimension": {"const": "METHOD", "default": "METHOD", "title": "Dimension", "type": "string"}, "recipe_version_id": {"format": "uuid", "title": "Recipe Version Id", "type": "string"}, "scope": {"const": "RECIPE_COOKING_CONTEXT", "default": "RECIPE_COOKING_CONTEXT", "title": "Scope", "type": "string"}}, "required": ["recipe_version_id"], "title": "RecipeMethodContextKey", "type": "object"}, "RecipePreferenceTarget": {"additionalProperties": false, "properties": {"kind": {"const": "DIRECT_RECIPE", "default": "DIRECT_RECIPE", "title": "Kind", "type": "string"}, "recipe_id": {"format": "uuid", "title": "Recipe Id", "type": "string"}}, "required": ["recipe_id"], "title": "RecipePreferenceTarget", "type": "object"}, "ReferencePriorAmount": {"additionalProperties": false, "properties": {"denominator": {"exclusiveMinimum": 0, "maximum": 2147483647, "title": "Denominator", "type": "integer"}, "numerator": {"maximum": 2147483647, "minimum": -2147483647, "title": "Numerator", "type": "integer"}, "unit": {"const": "REVIEWED_REFERENCE_ANCHOR_UNITS", "default": "REVIEWED_REFERENCE_ANCHOR_UNITS", "title": "Unit", "type": "string"}}, "required": ["numerator", "denominator"], "title": "ReferencePriorAmount", "type": "object"}, "ReferencePriorCoordinate": {"additionalProperties": false, "properties": {"applicability": {"const": "GLOBAL_REFERENCE_ONLY", "default": "GLOBAL_REFERENCE_ONLY", "title": "Applicability", "type": "string"}, "coordinate_id": {"const": "CURATED_REFERENCE_PREFERENCE", "default": "CURATED_REFERENCE_PREFERENCE", "title": "Coordinate Id", "type": "string"}, "coordinate_version": {"const": 1, "default": 1, "title": "Coordinate Version", "type": "integer"}, "unit": {"const": "REVIEWED_REFERENCE_ANCHOR_UNITS", "default": "REVIEWED_REFERENCE_ANCHOR_UNITS", "title": "Unit", "type": "string"}}, "title": "ReferencePriorCoordinate", "type": "object"}, "ReferenceProfileMappingRule": {"additionalProperties": false, "properties": {"output_amount": {"$ref": "#/$defs/MemberProfileAffinityAmount"}, "reference_amount": {"$ref": "#/$defs/ReferencePriorAmount"}}, "required": ["reference_amount", "output_amount"], "title": "ReferenceProfileMappingRule", "type": "object"}, "ReferenceTargetKindCompatibilityMap": {"additionalProperties": false, "properties": {"rows": {"items": {"$ref": "#/$defs/ReferenceProfileMappingRule"}, "title": "Rows", "type": "array"}, "target_kind": {"enum": ["INGREDIENT", "DIRECT_RECIPE", "PROTEIN", "METHOD", "FLAVOR"], "title": "Target Kind", "type": "string"}}, "required": ["target_kind", "rows"], "title": "ReferenceTargetKindCompatibilityMap", "type": "object"}}, "additionalProperties": false, "properties": {"expected_mutation_head_hash": {"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "title": "Expected Mutation Head Hash"}, "expected_provider_generation": {"maximum": 9223372036854775807, "minimum": 0, "title": "Expected Provider Generation", "type": "integer"}, "expected_revision": {"maximum": 2147483647, "minimum": -1, "title": "Expected Revision", "type": "integer"}, "idempotency_key": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Idempotency Key", "type": "string"}, "identity": {"$ref": "#/$defs/HierarchyStreamIdentity"}, "operation": {"enum": ["REPLACE", "RETRACT"], "title": "Operation", "type": "string"}, "policy": {"anyOf": [{"$ref": "#/$defs/HierarchyTransferPolicy"}, {"type": "null"}]}, "predecessor_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Predecessor Id"}, "provenance": {"$ref": "#/$defs/HierarchyProvenance"}, "provider_id": {"format": "uuid", "title": "Provider Id", "type": "string"}, "relation": {"anyOf": [{"$ref": "#/$defs/HierarchyRelationBody"}, {"type": "null"}]}, "review_rationale": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Review Rationale", "type": "string"}}, "required": ["provider_id", "identity", "operation", "policy", "relation", "provenance", "review_rationale", "expected_provider_generation", "expected_mutation_head_hash", "expected_revision", "predecessor_id", "idempotency_key"], "title": "HierarchyPublicationCommand", "type": "object"}'::jsonb $schema$;

-- Closed schema validation is a private input guard, not a mutable policy/expression engine.
CREATE FUNCTION menuto_hierarchy.check_provider_binding(p uuid,s jsonb) RETURNS void LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$ BEGIN
 IF NOT EXISTS (SELECT FROM public.hierarchy_source_providers x WHERE x.id=p AND x.actor_database_oid=(s->>'database_oid')::bigint AND x.actor_database_name=s->>'database_name') THEN RAISE EXCEPTION 'Hierarchy provider database binding differs; verified deployment enrollment required'; END IF;
END $$;
CREATE FUNCTION menuto_hierarchy.validate_json(j jsonb,s jsonb,root jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE t text; x record; option jsonb; ok boolean:=false; n numeric; BEGIN
 IF s ? '$ref' THEN PERFORM menuto_hierarchy.validate_json(j,root->'$defs'->split_part(s->>'$ref','/',3),root); RETURN; END IF;
 IF s ? 'anyOf' THEN
  FOR option IN SELECT value FROM jsonb_array_elements(s->'anyOf') LOOP
   BEGIN PERFORM menuto_hierarchy.validate_json(j,option,root); ok:=true; EXCEPTION WHEN raise_exception THEN NULL; END;
   EXIT WHEN ok;
  END LOOP;
  IF NOT ok THEN RAISE EXCEPTION 'Closed union contract mismatch'; END IF; RETURN;
 END IF;
 IF s ? 'oneOf' THEN
  FOR option IN SELECT value FROM jsonb_array_elements(s->'oneOf') LOOP
   BEGIN PERFORM menuto_hierarchy.validate_json(j,option,root); ok:=true; EXCEPTION WHEN raise_exception THEN NULL; END;
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
  FOR x IN SELECT key,value FROM jsonb_each(j) LOOP PERFORM menuto_hierarchy.validate_json(x.value,s->'properties'->x.key,root); END LOOP;
 ELSIF t='array' THEN
  IF (s ? 'minItems' AND jsonb_array_length(j)<(s->>'minItems')::int) OR (s ? 'maxItems' AND jsonb_array_length(j)>(s->>'maxItems')::int) THEN RAISE EXCEPTION 'Array bound'; END IF;
  FOR x IN SELECT value,ordinality FROM jsonb_array_elements(j) WITH ORDINALITY LOOP
   PERFORM menuto_hierarchy.validate_json(x.value,coalesce(s->'prefixItems'->(x.ordinality::int-1),s->'items'),root);
  END LOOP;
 ELSIF t='string' THEN
  IF (s ? 'minLength' AND length(j#>>'{}')<(s->>'minLength')::int) OR (s ? 'maxLength' AND length(j#>>'{}')>(s->>'maxLength')::int) OR (s ? 'pattern' AND (j#>>'{}') !~ (s->>'pattern')) THEN RAISE EXCEPTION 'String contract bound'; END IF;
  IF s->>'format'='uuid' THEN PERFORM menuto_hierarchy.uuid(j); END IF;
  IF s->>'format'='date-time' THEN
   IF NOT isfinite((j#>>'{}')::timestamptz) OR menuto_hierarchy.utc((j#>>'{}')::timestamptz)<>j#>>'{}' THEN RAISE EXCEPTION 'Canonical finite UTC time required'; END IF;
  END IF;
  IF s->>'format'='uri' THEN PERFORM menuto_hierarchy.check_uri(j); END IF;
 END IF;
END $$;

CREATE FUNCTION menuto_hierarchy.revision_fact(d jsonb) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
BEGIN RETURN jsonb_build_object('id',d->'id','stream_id',d->'stream_id','command',d->'command','owner_pins',d->'owner_pins','owner_source',menuto_hierarchy.owner_at(d->'owner_pins'),'principal_id',d->'principal_id','session',menuto_hierarchy.actor(d),'grant_event_id',d->'grant_event_id','authority_generation',d->'authority_generation','revision',d->'revision','source_sequence',d->'source_sequence','mutation_sequence',d->'mutation_sequence','recorded_at',menuto_hierarchy.utc((d->>'recorded_at')::timestamptz),'effective_at',menuto_hierarchy.utc((d->>'effective_at')::timestamptz),'command_hash',d->'command_hash','fact_hash',d->'fact_hash'); END
$$;
CREATE FUNCTION menuto_hierarchy.receipt(id uuid) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
 SELECT jsonb_build_object('publication',menuto_hierarchy.revision_fact(to_jsonb(r)),'mutation',menuto_hierarchy.mutation_fact(to_jsonb(m)),'frontier',jsonb_build_object('provider_id',r.provider_id,'source_generation',r.source_sequence,'authority_generation',r.authority_generation,'mutation_generation',m.mutation_sequence,'source_head_id',r.id,'authority_head_id',(SELECT id FROM public.hierarchy_source_authority WHERE provider_id=r.provider_id AND authority_sequence=r.authority_generation),'mutation_head_hash',m.journal_hash),'commit_status','CALLER_TRANSACTION_NOT_CERTIFIED') FROM public.hierarchy_source_revisions r JOIN public.hierarchy_source_mutations m ON m.provider_id=r.provider_id AND m.mutation_sequence=r.mutation_sequence WHERE r.id=$1
$$;

CREATE FUNCTION menuto_hierarchy.path_matches(recipe jsonb,k jsonb,p jsonb) RETURNS boolean LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE item jsonb; slot jsonb; rule jsonb; tier jsonb; chosen jsonb; transform jsonb; delta numeric; base numeric; factor numeric; selected uuid[]; structural uuid[]:=ARRAY[]::uuid[]; allids uuid[]:=ARRAY[]::uuid[]; n int; combo jsonb; BEGIN
 IF k->>'dimension'='METHOD' THEN RETURN p='null'::jsonb; END IF;
 IF p IS NULL OR p='null'::jsonb THEN RETURN false; END IF;
 SELECT value INTO tier FROM jsonb_array_elements(recipe->'portion_tiers') WHERE value->>'id'=p->>'tier_id';
 IF tier IS NULL THEN RAISE EXCEPTION 'Foreign recipe path tier'; END IF;
 SELECT coalesce(array_agg((v#>>'{}')::uuid ORDER BY v#>>'{}'),ARRAY[]::uuid[]) INTO selected FROM jsonb_array_elements(p->'selected_rule_ids') v;
 IF cardinality(selected)<>(SELECT count(DISTINCT v) FROM unnest(selected) v) THEN RAISE EXCEPTION 'Duplicate selected rule'; END IF;
 IF jsonb_array_length(p->'deltas')<>jsonb_array_length(recipe->'ingredients') THEN RAISE EXCEPTION 'Complete exact delta set required'; END IF;
 FOR item IN SELECT value FROM jsonb_array_elements(recipe->'ingredients') LOOP
  SELECT count(*),min((v->>1)::numeric) INTO n,delta FROM jsonb_array_elements(p->'deltas') v WHERE v->>0=item->>'id';
  IF n<>1 OR delta<(item#>>'{adjustment,min_delta}')::numeric OR delta>(item#>>'{adjustment,max_delta}')::numeric THEN RAISE EXCEPTION 'Invalid authored path delta'; END IF;
  IF item#>>'{adjustment,kind}'='DISCRETE' AND mod(delta,(item#>>'{adjustment,step}')::numeric)<>0 THEN RAISE EXCEPTION 'Delta step mismatch'; END IF;
  SELECT count(*) INTO n FROM jsonb_array_elements(recipe->'variant_rules') r WHERE (r->>'id')::uuid=ANY(selected) AND r->>'requirement_id'=item->>'id';
  IF n>1 THEN RAISE EXCEPTION 'Multiple rules for requirement'; END IF;
  SELECT r INTO rule FROM jsonb_array_elements(recipe->'variant_rules') r WHERE (r->>'id')::uuid=ANY(selected) AND r->>'requirement_id'=item->>'id';
  factor:=1; chosen:=item->'ingredient_id';
  IF rule IS NOT NULL THEN
   IF item#>>'{quantity,basis}'='COUNT' THEN RAISE EXCEPTION 'COUNT substitutions forbidden'; END IF;
   allids:=array_append(allids,(rule->>'id')::uuid); chosen:=rule->'replacement_ingredient_id'; factor:=(rule->>'quantity_factor')::numeric;
   IF rule->'structural'='true'::jsonb THEN structural:=array_append(structural,(rule->>'id')::uuid); END IF;
  END IF;
  SELECT (q->>'amount')::numeric INTO base FROM jsonb_array_elements(tier->'quantities') q WHERE q->>'requirement_id'=item->>'id';
  IF base*factor+delta<=0 THEN RAISE EXCEPTION 'Nonpositive authored path quantity'; END IF;
  SELECT t INTO transform FROM jsonb_array_elements(recipe->'transformations') t WHERE t->>'requirement_id'=item->>'id' AND t->'ingredient_id'=chosen;
  IF transform IS NULL AND EXISTS (SELECT FROM jsonb_array_elements(recipe->'transformations') t WHERE t->>'requirement_id'=item->>'id' AND t->'ingredient_id'=item->'ingredient_id') THEN RAISE EXCEPTION 'Missing required preparation path'; END IF;
  SELECT s INTO slot FROM jsonb_array_elements(k->'slots') s WHERE s->>'requirement_id'=item->>'id';
  IF slot IS NULL THEN RETURN false; END IF;
  IF (slot->>'choice'='BASE' AND rule IS NOT NULL) OR (slot->>'choice'='RULE' AND slot->>'selected_rule_id' IS DISTINCT FROM rule->>'id') OR (slot->>'preparation'='NONE' AND transform IS NOT NULL) OR (slot->>'preparation'='TRANSFORMATION' AND slot->>'transformation_id' IS DISTINCT FROM transform->>'id') OR (slot->>'adjustment'='ZERO_ONLY' AND delta<>0) THEN RETURN false; END IF;
 END LOOP;
 IF cardinality(allids)<>cardinality(selected) THEN RAISE EXCEPTION 'Unknown selected recipe rule'; END IF;
 IF cardinality(structural)>1 AND NOT EXISTS (SELECT FROM jsonb_array_elements(recipe->'approved_combinations') a WHERE (SELECT array_agg(x#>>'{}' ORDER BY x#>>'{}') FROM jsonb_array_elements(a->'rule_ids') x)=(SELECT array_agg(x::text ORDER BY x::text) FROM unnest(selected) x)) THEN RAISE EXCEPTION 'Unapproved structural combination'; END IF;
 RETURN (k->'tier_ids') @> jsonb_build_array(p->'tier_id');
END $$;

CREATE FUNCTION menuto_hierarchy.check_binding(recipe jsonb,k jsonb,p jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE sorted jsonb; item jsonb; previous text; exact_scope boolean; BEGIN
 IF k='null'::jsonb THEN IF p<>'null'::jsonb THEN RAISE EXCEPTION 'No implicit recipe path'; END IF; RETURN; END IF;
 IF k->>'recipe_version_id'<>recipe->>'id' THEN RAISE EXCEPTION 'Recipe version context mismatch'; END IF;
 IF k->>'dimension'='METHOD' THEN IF p<>'null'::jsonb THEN RAISE EXCEPTION 'METHOD forbids path'; END IF; RETURN; END IF;
 IF p='null'::jsonb THEN RAISE EXCEPTION 'Path-sensitive context requires explicit path'; END IF;
 SELECT coalesce(jsonb_agg(v ORDER BY v#>>'{}'),'[]') INTO sorted FROM (SELECT DISTINCT value v FROM jsonb_array_elements(k->'tier_ids')) q;
 IF sorted<>k->'tier_ids' OR EXISTS (SELECT FROM jsonb_array_elements(k->'tier_ids') t WHERE NOT EXISTS (SELECT FROM jsonb_array_elements(recipe->'portion_tiers') r WHERE r->'id'=t)) THEN RAISE EXCEPTION 'Exact sorted authored tiers required'; END IF;
 IF jsonb_array_length(k->'slots')<>jsonb_array_length(recipe->'ingredients') THEN RAISE EXCEPTION 'Complete exact context slots required'; END IF;
 previous:=NULL;
 FOR item IN SELECT value FROM jsonb_array_elements(k->'slots') LOOP
  IF (previous IS NOT NULL AND previous>=item->>'requirement_id' COLLATE "C") OR NOT EXISTS (SELECT FROM jsonb_array_elements(recipe->'ingredients') r WHERE r->'id'=item->'requirement_id') THEN RAISE EXCEPTION 'Unique sorted exact context slots'; END IF; previous:=item->>'requirement_id';
  IF (item->>'choice'='RULE') IS DISTINCT FROM (item->'selected_rule_id'<>'null'::jsonb) OR (item->>'preparation'='TRANSFORMATION') IS DISTINCT FROM (item->'transformation_id'<>'null'::jsonb) THEN RAISE EXCEPTION 'Conditional context selectors invalid'; END IF;
 END LOOP;
 exact_scope:=jsonb_array_length(k->'tier_ids')=1 AND NOT EXISTS (SELECT FROM jsonb_array_elements(k->'slots') r WHERE r->>'choice'='ANY_AUTHORED_CHOICE' OR r->>'preparation'='ANY_AUTHORED_PATH_CONTEXT' OR r->>'adjustment'<>'ZERO_ONLY');
 IF (k->>'scope'='EXACT_PATH') IS DISTINCT FROM exact_scope THEN RAISE EXCEPTION 'Exact versus reviewed scope mismatch'; END IF;
 SELECT coalesce(jsonb_agg(v ORDER BY v#>>'{}'),'[]') INTO sorted FROM (SELECT DISTINCT value v FROM jsonb_array_elements(p->'selected_rule_ids')) q;
 IF sorted<>p->'selected_rule_ids' THEN RAISE EXCEPTION 'Canonical sorted selected rules'; END IF;
 previous:=NULL;
 FOR item IN SELECT value FROM jsonb_array_elements(p->'deltas') LOOP
  IF (previous IS NOT NULL AND previous>=(item->>0) COLLATE "C") OR jsonb_typeof(item->1)<>'string' OR menuto_hierarchy.decimal_text(item->>1)<>item->>1 OR abs((item->>1)::numeric)>=1000000000000 OR scale(trim_scale((item->>1)::numeric))>6 THEN RAISE EXCEPTION 'Canonical sorted exact path deltas'; END IF; previous:=item->>0;
 END LOOP;
END $$;

CREATE FUNCTION menuto_hierarchy.check_relation(c jsonb,policy jsonb,owner jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE i jsonb:=c->'identity'; r jsonb:=c->'relation'; a jsonb:=i->'source'; b jsonb:=i->'destination'; binding jsonb; recipe jsonb; term jsonb; ingredient jsonb; stream jsonb; head jsonb; scope jsonb; active jsonb; cell jsonb; dimension text; modes text[]; req jsonb; ids jsonb; matches int:=0; expected int; prior text; BEGIN
 IF a=b OR a='null'::jsonb OR b='null'::jsonb THEN RAISE EXCEPTION 'Exact distinct endpoints required; no self-edge'; END IF;
 SELECT value INTO cell FROM jsonb_array_elements(policy->'directions') WHERE value->>'source_kind'=a->>'kind' AND value->>'destination_kind'=b->>'kind';
 IF cell->'enabled' IS DISTINCT FROM 'true'::jsonb OR NOT (cell->'support_modes' @> jsonb_build_array(r->'support_mode')) THEN RAISE EXCEPTION 'Direction/support mode denied'; END IF;
 expected:=(CASE WHEN a->>'kind'='DIRECT_RECIPE' THEN 1 ELSE 0 END)+(CASE WHEN b->>'kind'='DIRECT_RECIPE' THEN 1 ELSE 0 END);
 IF jsonb_array_length(i->'recipe_bindings')<>expected THEN RAISE EXCEPTION 'Explicit recipe endpoint bindings required'; END IF;
 prior:=NULL;
 FOR binding IN SELECT value FROM jsonb_array_elements(i->'recipe_bindings') LOOP
  IF prior IS NOT NULL AND prior>=binding->>'endpoint' COLLATE "C" THEN RAISE EXCEPTION 'Unique sorted recipe endpoint bindings'; END IF; prior:=binding->>'endpoint';
  term:=CASE WHEN binding->>'endpoint'='SOURCE' THEN a ELSE b END;
  SELECT value INTO recipe FROM jsonb_array_elements(owner->'recipes') WHERE value->>'id'=binding->>'recipe_version_id';
  IF term->>'kind'<>'DIRECT_RECIPE' OR recipe#>>'{recipe,id}' IS DISTINCT FROM term->>'recipe_id' OR recipe->>'review_status'<>'REVIEWED' THEN RAISE EXCEPTION 'Exact reviewed RecipeVersion binding required'; END IF;
  PERFORM menuto_hierarchy.check_binding(recipe,binding->'key',binding->'path');
  IF binding->'key'='null'::jsonb THEN
   IF binding->'path'<>'null'::jsonb THEN RAISE EXCEPTION 'No implicit recipe path'; END IF;
  ELSIF binding#>>'{key,recipe_version_id}'<>binding->>'recipe_version_id' OR NOT menuto_hierarchy.path_matches(recipe,binding->'key',binding->'path') THEN RAISE EXCEPTION 'Recipe context/path mismatch'; END IF;
 END LOOP;
 IF r->>'support_mode'='REVIEWED_EXACT_PAIR' THEN
  IF r->'support_review_id'<>'null'::jsonb OR jsonb_array_length(r->'catalog_review_ids')<>0 THEN RAISE EXCEPTION 'Exact pair cannot claim classification'; END IF; RETURN;
 END IF;
 IF (a->>'kind'='INGREDIENT' AND b->>'kind'='PROTEIN') OR (b->>'kind'='INGREDIENT' AND a->>'kind'='PROTEIN') THEN
  ingredient:=CASE WHEN a->>'kind'='INGREDIENT' THEN a ELSE b END; term:=CASE WHEN a->>'kind'='INGREDIENT' THEN b ELSE a END;
  SELECT value INTO stream FROM jsonb_array_elements(owner->'catalog_streams') WHERE value->>'ingredient_id'=ingredient->>'ingredient_id'; head:=stream->'reviews'->-1;
  IF head->>'id' IS DISTINCT FROM r->>'support_review_id' OR head#>>'{command,command_kind}'='RETRACT' OR NOT (head#>'{command,positive_term_ids}' @> jsonb_build_array(term->'feature_term_id')) OR jsonb_array_length(r->'catalog_review_ids')<>0 THEN RAISE EXCEPTION 'Canonical positive Catalog support required'; END IF; RETURN;
 END IF;
 IF a->>'kind'='DIRECT_RECIPE' THEN term:=b; ELSIF b->>'kind'='DIRECT_RECIPE' THEN term:=a; ELSE RAISE EXCEPTION 'Classification relation shape prohibited'; END IF;
 IF term->>'kind' NOT IN ('METHOD','FLAVOR','PROTEIN') OR expected<>1 THEN RAISE EXCEPTION 'Classification recipe/feature shape required'; END IF;
 dimension:=CASE WHEN term->>'kind'='PROTEIN' THEN 'MAIN_PROTEIN' ELSE term->>'kind' END;
 binding:=i->'recipe_bindings'->0;
 IF binding->'key'='null'::jsonb OR binding#>>'{key,dimension}'<>dimension THEN RAISE EXCEPTION 'Exact explicit feature context required'; END IF;
 FOR scope IN SELECT value FROM jsonb_array_elements(owner->'scopes') WHERE value#>>'{key,recipe_version_id}'=binding->>'recipe_version_id' AND value#>>'{key,dimension}'=dimension LOOP
  head:=scope->'reviews'->-1;
  IF head#>>'{command,command_kind}'<>'RETRACT' AND menuto_hierarchy.path_matches(recipe,scope->'key',binding->'path') THEN matches:=matches+1; active:=scope; END IF;
 END LOOP;
 head:=active->'reviews'->-1;
 IF matches<>1 OR active->'key' IS DISTINCT FROM binding->'key' OR head->>'id' IS DISTINCT FROM r->>'support_review_id' OR NOT (head#>'{command,positive_term_ids}' @> jsonb_build_array(term->'feature_term_id')) THEN RAISE EXCEPTION 'Canonical exact positive nonconflicting Recipe support required'; END IF;
 SELECT coalesce(jsonb_agg(x ORDER BY x#>>'{}'),'[]') INTO ids FROM (SELECT DISTINCT value->'catalog_review_id' x FROM jsonb_array_elements(head#>'{command,supports}')) q;
 IF ids IS DISTINCT FROM r->'catalog_review_ids' THEN RAISE EXCEPTION 'Exact Catalog support pins required'; END IF;
 FOR req IN SELECT value FROM jsonb_array_elements(head#>'{command,supports}') LOOP
  SELECT value INTO stream FROM jsonb_array_elements(owner->'catalog_streams') WHERE value->>'ingredient_id'=req->>'ingredient_id';
  IF stream#>>'{reviews,-1,id}' IS DISTINCT FROM req->>'catalog_review_id' OR stream#>>'{reviews,-1,command,command_kind}'='RETRACT' OR NOT (stream#>'{reviews,-1,command,positive_term_ids}' @> jsonb_build_array(req->'term_id')) THEN RAISE EXCEPTION 'Stale MAIN_PROTEIN Catalog support'; END IF;
 END LOOP;
END $$;

CREATE FUNCTION menuto_hierarchy.rational(j jsonb) RETURNS numeric LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE n bigint; d bigint; BEGIN
 n:=menuto_hierarchy.integer(j->'numerator',-2147483647,2147483647);
 d:=menuto_hierarchy.integer(j->'denominator',1,2147483647);
 IF abs(n)>d OR gcd(abs(n),d)<>1 THEN RAISE EXCEPTION 'Canonical rational required'; END IF;
 RETURN n::numeric/d::numeric;
END $$;
CREATE FUNCTION menuto_hierarchy.raw_hash(j jsonb) RETURNS text LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$ SELECT encode(sha256(convert_to(menuto_hierarchy.canonical(j),'UTF8')),'hex') $$;

CREATE FUNCTION menuto_hierarchy.less(a jsonb,b jsonb) RETURNS boolean LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$ SELECT (a->>'numerator')::numeric*(b->>'denominator')::numeric < (b->>'numerator')::numeric*(a->>'denominator')::numeric $$;
CREATE FUNCTION menuto_hierarchy.check_policy(p jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE e jsonb:=p->'explicit_policy'; c jsonb:=p->'compatibility_policy'; g jsonb; r jsonb; x jsonb; cell jsonb; frozen jsonb; prev text; prevrow text; k text; state text; val jsonb; d jsonb; n jsonb; l jsonb; lastval jsonb; hash text; seen text[]:=ARRAY[]::text[]; modes text[]; BEGIN
 IF e#>>'{provenance,kind}' NOT IN ('USER','REVIEWED_REFERENCE') OR c#>>'{provenance,kind}'<>'REVIEWED_REFERENCE' OR c->>'explicit_policy_id'<>e->>'policy_id' OR c->>'explicit_policy_version'<>e->>'policy_version' OR c->>'explicit_policy_fingerprint'<>menuto_hierarchy.raw_hash(e) THEN RAISE EXCEPTION 'Frozen explicit policy binding differs'; END IF;
 IF jsonb_array_length(e->'target_policies')<>5 THEN RAISE EXCEPTION 'Five explicit kinds required'; END IF;
 prev:=NULL;
 FOR g IN SELECT value FROM jsonb_array_elements(e->'target_policies') LOOP
  k:=g->>'target_kind';
  IF k NOT IN ('INGREDIENT','PROTEIN','METHOD','FLAVOR','DIRECT_RECIPE') OR (prev IS NOT NULL AND prev>=k COLLATE "C") THEN RAISE EXCEPTION 'Closed sorted five kinds'; END IF; prev:=k;
  IF jsonb_array_length(g->'affinity_rules')<>3 OR jsonb_array_length(g->'strength_rules')<>2 THEN RAISE EXCEPTION 'Complete explicit mappings'; END IF;
  prevrow:=NULL;
  FOR r IN SELECT value FROM jsonb_array_elements(g->'affinity_rules') LOOP
   IF prevrow IS NOT NULL AND prevrow>=r->>'value' COLLATE "C" THEN RAISE EXCEPTION 'Sorted distinct semantic states'; END IF; prevrow:=r->>'value';
   PERFORM menuto_hierarchy.rational(r->'amount'); val:=r->'amount';
   CASE r->>'value' WHEN 'DISLIKE' THEN d:=val; WHEN 'NEUTRAL' THEN n:=val; WHEN 'LIKE' THEN l:=val; ELSE RAISE EXCEPTION 'Unknown semantic state'; END CASE;
  END LOOP;
  IF NOT menuto_hierarchy.less(d,n) OR NOT menuto_hierarchy.less(n,l) THEN RAISE EXCEPTION 'Explicit strict ordering'; END IF;
  IF (g#>>'{strength_rules,0,authorship}',g#>>'{strength_rules,1,authorship}') IS DISTINCT FROM ('AUTHORIZED_REPRESENTATIVE','SELF') THEN RAISE EXCEPTION 'Complete authorship strength rules'; END IF;
 END LOOP;
 FOREACH k IN ARRAY ARRAY['explicit_maps','reference_maps'] LOOP
  IF jsonb_array_length(c->k)<>5 THEN RAISE EXCEPTION 'Complete compatibility groups'; END IF;
  prev:=NULL;
  FOR g IN SELECT value FROM jsonb_array_elements(c->k) LOOP
   IF (prev IS NOT NULL AND prev>=g->>'target_kind' COLLATE "C") OR NOT EXISTS (SELECT FROM jsonb_array_elements(e->'target_policies') a WHERE a->>'target_kind'=g->>'target_kind') THEN RAISE EXCEPTION 'Compatibility group identity'; END IF; prev:=g->>'target_kind';
   lastval:=NULL; prevrow:=NULL; d:=NULL;
   IF k='explicit_maps' AND jsonb_array_length(g->'rows')<>3 THEN RAISE EXCEPTION 'Complete explicit compatibility rows'; END IF;
   FOR r IN SELECT value FROM jsonb_array_elements(g->'rows') LOOP
    PERFORM menuto_hierarchy.rational(r->'output_amount'); val:=r->'output_amount';
    IF k='explicit_maps' THEN
     IF prevrow IS NOT NULL AND prevrow>=r->>'value' COLLATE "C" THEN RAISE EXCEPTION 'Sorted compatibility semantics'; END IF; prevrow:=r->>'value';
     SELECT a INTO frozen FROM jsonb_array_elements(e->'target_policies') a WHERE a->>'target_kind'=g->>'target_kind';
     SELECT a->'amount' INTO x FROM jsonb_array_elements(frozen->'affinity_rules') a WHERE a->>'value'=r->>'value';
     PERFORM menuto_hierarchy.rational(r->'expected_explicit_amount');
     IF x IS DISTINCT FROM r->'expected_explicit_amount' THEN RAISE EXCEPTION 'Frozen compatibility semantic/amount mismatch'; END IF;
    ELSE
     PERFORM menuto_hierarchy.rational(r->'reference_amount'); n:=r->'reference_amount';
     IF d IS NOT NULL AND NOT menuto_hierarchy.less(d,n) THEN RAISE EXCEPTION 'Sorted finite reference lookup'; END IF; d:=n;
     IF lastval IS NOT NULL AND NOT menuto_hierarchy.less(lastval,val) THEN RAISE EXCEPTION 'Monotonic reference map'; END IF; lastval:=val;
    END IF;
   END LOOP;
   IF k='explicit_maps' THEN
    SELECT a->'output_amount' INTO d FROM jsonb_array_elements(g->'rows') a WHERE a->>'value'='DISLIKE';
    SELECT a->'output_amount' INTO n FROM jsonb_array_elements(g->'rows') a WHERE a->>'value'='NEUTRAL';
    SELECT a->'output_amount' INTO l FROM jsonb_array_elements(g->'rows') a WHERE a->>'value'='LIKE';
    IF d IS NULL OR n IS NULL OR l IS NULL OR NOT menuto_hierarchy.less(d,n) OR NOT menuto_hierarchy.less(n,l) THEN RAISE EXCEPTION 'Monotonic explicit compatibility map'; END IF;
   END IF;
  END LOOP;
 END LOOP;
 hash:=menuto_hierarchy.hash('exact-target-prior-compatibility-policy.v1',c);
 IF jsonb_array_length(p->'directions')<>25 THEN RAISE EXCEPTION 'Full25-cell matrix required'; END IF;
 prev:=NULL;
 FOR cell IN SELECT value FROM jsonb_array_elements(p->'directions') LOOP
  k:=(cell->>'source_kind')||':'||(cell->>'destination_kind');
  IF k=ANY(seen) OR (prev IS NOT NULL AND prev>=k COLLATE "C") THEN RAISE EXCEPTION 'Unique sorted25-cell matrix'; END IF; seen:=array_append(seen,k); prev:=k;
  SELECT array_agg(v#>>'{}' ORDER BY v#>>'{}' COLLATE "C") INTO modes FROM jsonb_array_elements(cell->'support_modes') v;
  IF (SELECT count(*) FROM unnest(modes))<>(SELECT count(DISTINCT v) FROM unnest(modes) v) OR to_jsonb(coalesce(modes,ARRAY[]::text[]))<>cell->'support_modes' THEN RAISE EXCEPTION 'Unique sorted support modes'; END IF;
  IF cell->'enabled'='false'::jsonb THEN
   IF jsonb_array_length(cell->'rows')<>0 OR jsonb_array_length(cell->'support_modes')<>0 OR cell->'attenuation'<>'null'::jsonb THEN RAISE EXCEPTION 'Denied direction payload'; END IF;
   CONTINUE;
  END IF;
  IF cell->'support_modes' @> '["CLASSIFICATION_BOUND_PAIR"]'::jsonb AND NOT (
   (cell->>'source_kind'='INGREDIENT' AND cell->>'destination_kind'='PROTEIN') OR (cell->>'destination_kind'='INGREDIENT' AND cell->>'source_kind'='PROTEIN') OR
   (cell->>'source_kind'='DIRECT_RECIPE' AND cell->>'destination_kind' IN ('PROTEIN','METHOD','FLAVOR')) OR (cell->>'destination_kind'='DIRECT_RECIPE' AND cell->>'source_kind' IN ('PROTEIN','METHOD','FLAVOR'))
  ) THEN RAISE EXCEPTION 'Classification-bound direction shape prohibited'; END IF;
  IF jsonb_array_length(cell->'rows')=0 OR jsonb_array_length(cell->'support_modes')=0 OR cell->'attenuation'='null'::jsonb OR menuto_hierarchy.rational(cell->'attenuation')<=0 THEN RAISE EXCEPTION 'Enabled direction requires authored map/modes/attenuation'; END IF;
  prevrow:=NULL; d:=NULL; n:=NULL; l:=NULL;
  FOR r IN SELECT value FROM jsonb_array_elements(cell->'rows') LOOP
   state:=r->>'source_affinity_value';
   IF prevrow IS NOT NULL AND prevrow>=state COLLATE "C" THEN RAISE EXCEPTION 'Unique sorted transfer semantic rows'; END IF; prevrow:=state;
   SELECT a INTO frozen FROM jsonb_array_elements(e->'target_policies') a WHERE a->>'target_kind'=cell->>'source_kind';
   SELECT a->'amount' INTO x FROM jsonb_array_elements(frozen->'affinity_rules') a WHERE a->>'value'=state;
   IF x IS DISTINCT FROM r->'expected_source_amount' THEN RAISE EXCEPTION 'Transfer semantic/expected frozen amount mismatch'; END IF;
   PERFORM menuto_hierarchy.rational(r->'expected_source_amount');
   x:=jsonb_build_object('coordinate_id','MEMBER_PROFILE_AFFINITY','coordinate_version',1,'target_kind',cell->>'source_kind','compatibility_policy_fingerprint',hash,'unit','POLICY_MEMBER_PROFILE_AFFINITY_UNITS','scope','ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY');
   IF x IS DISTINCT FROM r->'source_descriptor' THEN RAISE EXCEPTION 'Transfer source descriptor mismatch'; END IF;
   PERFORM menuto_hierarchy.rational(r->'output_amount'); val:=r->'output_amount';
   CASE state WHEN 'NEUTRAL' THEN IF (val->>'numerator')::bigint<>0 THEN RAISE EXCEPTION 'NEUTRAL requires zero'; END IF; n:=val;
    WHEN 'DISLIKE' THEN IF (val->>'numerator')::bigint>0 THEN RAISE EXCEPTION 'DISLIKE cannot map positive'; END IF; d:=val;
    WHEN 'LIKE' THEN IF (val->>'numerator')::bigint<0 THEN RAISE EXCEPTION 'LIKE cannot map negative'; END IF; l:=val;
    ELSE RAISE EXCEPTION 'Unknown semantic state'; END CASE;
  END LOOP;
  IF (d IS NOT NULL AND n IS NOT NULL AND NOT menuto_hierarchy.less(d,n)) OR (n IS NOT NULL AND l IS NOT NULL AND NOT menuto_hierarchy.less(n,l)) OR (d IS NOT NULL AND l IS NOT NULL AND NOT menuto_hierarchy.less(d,l)) THEN RAISE EXCEPTION 'Transfer strict semantic ordering'; END IF;
 END LOOP;
END $$;

-- Independently owned, SELECT-only Catalog/Recipes read adapters. No curation writes.
DO $$ DECLARE n text; BEGIN
 FOREACH n IN ARRAY ARRAY['menuto_hierarchy_catalog_owner','menuto_hierarchy_recipes_owner'] LOOP
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname=n) THEN EXECUTE format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS',n); END IF;
  IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname=n AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) OR EXISTS (SELECT FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid=m.member WHERE r.rolname=n) THEN RAISE EXCEPTION 'Unsafe hierarchy read-adapter owner'; END IF;
 END LOOP;
END $$;
DO $$ BEGIN
 IF EXISTS (SELECT FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid=m.roleid WHERE r.rolname IN ('menuto_hierarchy_owner','menuto_hierarchy_catalog_owner','menuto_hierarchy_recipes_owner')) THEN RAISE EXCEPTION 'Protected hierarchy owners must have no inbound role membership'; END IF;
END $$;
GRANT USAGE ON SCHEMA menuto_hierarchy,public TO menuto_hierarchy_catalog_owner,menuto_hierarchy_recipes_owner;
GRANT SELECT ON public.ingredients,public.affinity_feature_terms,public.ingredient_protein_frontier,public.ingredient_protein_streams,public.ingredient_protein_reviews,public.ingredient_protein_review_terms,public.ingredient_protein_assignments TO menuto_hierarchy_catalog_owner;
GRANT SELECT ON public.recipes,public.recipe_versions,public.recipe_version_seals,public.recipe_ingredients,public.recipe_portion_tiers,public.recipe_tier_quantities,public.recipe_variant_rules,public.recipe_rule_combinations,public.recipe_combination_members,public.preparation_transformations,public.culinary_feature_frontier,public.culinary_feature_applicabilities,public.culinary_feature_applicability_tiers,public.culinary_feature_applicability_slots,public.culinary_feature_reviews,public.culinary_feature_review_terms,public.culinary_feature_assignments,public.culinary_feature_main_protein_support TO menuto_hierarchy_recipes_owner;
DO $$ DECLARE owner_name text; allowed text[]; BEGIN
 FOREACH owner_name IN ARRAY ARRAY['menuto_hierarchy_owner','menuto_hierarchy_catalog_owner','menuto_hierarchy_recipes_owner'] LOOP
  allowed:=CASE owner_name WHEN 'menuto_hierarchy_catalog_owner' THEN ARRAY['ingredients','affinity_feature_terms','ingredient_protein_frontier','ingredient_protein_streams','ingredient_protein_reviews','ingredient_protein_review_terms','ingredient_protein_assignments'] WHEN 'menuto_hierarchy_recipes_owner' THEN ARRAY['recipes','recipe_versions','recipe_version_seals','recipe_ingredients','recipe_portion_tiers','recipe_tier_quantities','recipe_variant_rules','recipe_rule_combinations','recipe_combination_members','preparation_transformations','culinary_feature_frontier','culinary_feature_applicabilities','culinary_feature_applicability_tiers','culinary_feature_applicability_slots','culinary_feature_reviews','culinary_feature_review_terms','culinary_feature_assignments','culinary_feature_main_protein_support'] ELSE ARRAY[]::text[] END;
  IF has_schema_privilege(owner_name,'public','CREATE') OR EXISTS (SELECT FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r' AND c.relname NOT LIKE 'hierarchy_source_%' AND (has_table_privilege(owner_name,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') OR (NOT c.relname=ANY(allowed) AND has_table_privilege(owner_name,c.oid,'SELECT')))) THEN RAISE EXCEPTION 'Hierarchy function owner has privileges outside its source/read remit'; END IF;
 END LOOP;
END $$;

CREATE FUNCTION menuto_hierarchy.provenance(j jsonb) RETURNS jsonb LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$ SELECT jsonb_build_object('kind',j->'source_kind','source_system',j->'source_system','external_record_id',j->'external_record_id','source_version',j->'source_version','source_uri',j->'source_uri','content_hash',j->'content_hash','observed_at',menuto_hierarchy.utc((j->>'observed_at')::timestamptz)) $$;
CREATE FUNCTION menuto_hierarchy.decimal_text(v text) RETURNS text LANGUAGE plpgsql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE n numeric:=v::numeric; spelling text; digits text; frac text; exponent int; adjusted int; zeros int; sign text:=''; BEGIN
 IF n=0 THEN RETURN '0'; END IF;
 IF n<0 THEN sign:='-'; END IF;
 spelling:=trim_scale(abs(n))::text; frac:=split_part(spelling,'.',2);
 digits:=ltrim(replace(spelling,'.',''),'0'); exponent:=-length(frac);
 zeros:=length(digits)-length(rtrim(digits,'0')); digits:=rtrim(digits,'0'); exponent:=exponent+zeros;
 adjusted:=exponent+length(digits)-1;
 IF exponent>0 OR adjusted < -6 THEN RETURN sign||left(digits,1)||(CASE WHEN length(digits)>1 THEN '.'||substr(digits,2) ELSE '' END)||'E'||(CASE WHEN adjusted>=0 THEN '+' ELSE '' END)||adjusted::text; END IF;
 RETURN sign||spelling;
END $$;
CREATE FUNCTION menuto_hierarchy.recipe_leaf(j jsonb, decimals text[]) RETURNS jsonb LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$ DECLARE out jsonb; k text; BEGIN
 out:=j-ARRAY['created_at','ordinal','authored_transaction'];
 IF j ? 'source_kind' THEN out:=(out-ARRAY['source_kind','source_system','external_record_id','source_version','source_uri','content_hash','observed_at'])||jsonb_build_object('provenance',menuto_hierarchy.provenance(j)); END IF;
 FOREACH k IN ARRAY decimals LOOP IF out ? k AND out->k<>'null'::jsonb THEN out:=jsonb_set(out,ARRAY[k],to_jsonb(menuto_hierarchy.decimal_text(out->>k))); END IF; END LOOP;
 RETURN out||jsonb_build_object('contract_version','recipe-v1');
END $$;
CREATE FUNCTION menuto_hierarchy.catalog_term(j jsonb) RETURNS jsonb LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$ SELECT (j-ARRAY['created_at','source_kind','source_system','external_record_id','source_version','source_uri','content_hash','observed_at'])||jsonb_build_object('contract_version','affinity-feature-term.v1','provenance',menuto_hierarchy.provenance(j)) $$;

CREATE FUNCTION menuto_hierarchy.catalog_read(targets jsonb) RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path=pg_catalog,public,menuto_hierarchy,pg_temp AS $$
DECLARE identities jsonb:='[]'; t jsonb; i jsonb; streams jsonb; terms jsonb; BEGIN
 FOR t IN SELECT value FROM jsonb_array_elements(targets) LOOP
  IF t->>'kind'='INGREDIENT' THEN
   SELECT jsonb_build_object('contract_version','ingredient-identity.v1','id',id,'name',name) INTO i FROM public.ingredients WHERE id=(t->>'ingredient_id')::uuid;
  ELSIF t->>'kind' IN ('PROTEIN','METHOD','FLAVOR') THEN
   SELECT menuto_hierarchy.catalog_term(to_jsonb(f)) INTO i FROM public.affinity_feature_terms f WHERE id=(t->>'feature_term_id')::uuid AND kind=t->>'kind' AND status='REVIEWED';
  ELSE CONTINUE; END IF;
  IF i IS NULL THEN RAISE EXCEPTION 'TARGET_IDENTITY_UNRESOLVED / TARGET_NOT_REVIEWED'; END IF;
  identities:=identities||jsonb_build_array(jsonb_build_object('target',t,'identity',i));
 END LOOP;
 -- Complete canonical Catalog review source, including negative and withdrawn reviews.
 SELECT coalesce(jsonb_agg(jsonb_build_object('contract_version','ingredient-protein-stream.v1','id',s.id,'ingredient_id',s.ingredient_id,'reviews',
   (SELECT coalesce(jsonb_agg(jsonb_build_object('contract_version','ingredient-protein-review.v1','id',r.id,'stream_id',r.stream_id,'ingredient_id',r.ingredient_id,'revision_no',r.revision_no,'predecessor_revision_no',r.predecessor_revision_no,'source_sequence',r.source_sequence,'reviewer_user_id',r.reviewer_user_id,'recorded_at',menuto_hierarchy.utc(r.recorded_at),'command',public.menuto_feature_review_command(r.id,true),'command_hash',r.command_hash) ORDER BY r.revision_no),'[]') FROM public.ingredient_protein_reviews r WHERE r.stream_id=s.id)) ORDER BY s.ingredient_id),'[]') INTO streams FROM public.ingredient_protein_streams s;
 SELECT coalesce(jsonb_agg(menuto_hierarchy.catalog_term(to_jsonb(ft)) ORDER BY ft.id),'[]') INTO terms FROM public.affinity_feature_terms ft WHERE ft.status='REVIEWED';
 RETURN jsonb_build_object('identities',identities,'catalog_frontier',(SELECT generation FROM public.ingredient_protein_frontier),'catalog_streams',streams,'terms',terms);
END $$;

CREATE FUNCTION menuto_hierarchy.recipe_snapshot(v uuid) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,public,menuto_hierarchy,pg_temp AS $$
DECLARE body jsonb; ingredients jsonb; tiers jsonb; rules jsonb; combinations jsonb; transforms jsonb; BEGIN
 SELECT (menuto_hierarchy.recipe_leaf(to_jsonb(r),ARRAY['base_servings'])-'recipe_id')||jsonb_build_object('recipe',menuto_hierarchy.recipe_leaf(to_jsonb(p),ARRAY[]::text[])) INTO body FROM public.recipe_versions r JOIN public.recipes p ON p.id=r.recipe_id JOIN public.recipe_version_seals s ON s.recipe_version_id=r.id WHERE r.id=v AND r.review_status='REVIEWED';
 IF body IS NULL THEN RAISE EXCEPTION 'Exact reviewed RecipeVersion required'; END IF;
 SELECT coalesce(jsonb_agg((menuto_hierarchy.recipe_leaf(to_jsonb(r),ARRAY[]::text[])-ARRAY['amount','basis','item_ref','scaling_kind','scaling_quantum','scaling_minimum','scaling_maximum','adjustment_kind','min_delta','max_delta','adjustment_step'])||jsonb_build_object(
  'quantity',jsonb_build_object('amount',menuto_hierarchy.decimal_text(r.amount::text),'basis',r.basis,'item_ref',r.item_ref),
  'scaling',jsonb_build_object('contract_version','recipe-v1','kind',r.scaling_kind,'quantum',menuto_hierarchy.decimal_text(r.scaling_quantum::text),'minimum',menuto_hierarchy.decimal_text(r.scaling_minimum::text),'maximum',menuto_hierarchy.decimal_text(r.scaling_maximum::text)),
  'adjustment',jsonb_build_object('contract_version','recipe-v1','kind',r.adjustment_kind,'min_delta',menuto_hierarchy.decimal_text(r.min_delta::text),'max_delta',menuto_hierarchy.decimal_text(r.max_delta::text),'step',menuto_hierarchy.decimal_text(r.adjustment_step::text))) ORDER BY r.ordinal),'[]') INTO ingredients FROM public.recipe_ingredients r WHERE recipe_version_id=v;
 SELECT coalesce(jsonb_agg(menuto_hierarchy.recipe_leaf(to_jsonb(t),ARRAY['servings'])||jsonb_build_object('quantities',
  (SELECT coalesce(jsonb_agg(jsonb_build_object('contract_version','recipe-v1','requirement_id',q.requirement_id,'amount',menuto_hierarchy.decimal_text(q.amount::text)) ORDER BY q.ordinal),'[]') FROM public.recipe_tier_quantities q WHERE q.tier_id=t.id)) ORDER BY t.ordinal),'[]') INTO tiers FROM public.recipe_portion_tiers t WHERE recipe_version_id=v;
 SELECT coalesce(jsonb_agg(menuto_hierarchy.recipe_leaf(to_jsonb(r),ARRAY['quantity_factor']) ORDER BY r.ordinal),'[]') INTO rules FROM public.recipe_variant_rules r WHERE recipe_version_id=v;
 SELECT coalesce(jsonb_agg(menuto_hierarchy.recipe_leaf(to_jsonb(r),ARRAY[]::text[])||jsonb_build_object('rule_ids',(SELECT coalesce(jsonb_agg(m.rule_id ORDER BY m.ordinal),'[]') FROM public.recipe_combination_members m WHERE m.combination_id=r.id)) ORDER BY r.ordinal),'[]') INTO combinations FROM public.recipe_rule_combinations r WHERE recipe_version_id=v;
 SELECT coalesce(jsonb_agg(menuto_hierarchy.recipe_leaf(to_jsonb(r),ARRAY['factor']) ORDER BY r.ordinal),'[]') INTO transforms FROM public.preparation_transformations r WHERE recipe_version_id=v;
 RETURN body||jsonb_build_object('ingredients',ingredients,'portion_tiers',tiers,'variant_rules',rules,'approved_combinations',combinations,'transformations',transforms);
END $$;

CREATE FUNCTION menuto_hierarchy.recipes_read(targets jsonb, bindings jsonb) RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path=pg_catalog,public,menuto_hierarchy,pg_temp AS $$
DECLARE t jsonb; identities jsonb:='[]'; i jsonb; recipes jsonb:='[]'; scopes jsonb; v uuid; vids uuid[]; BEGIN
 FOR t IN SELECT value FROM jsonb_array_elements(targets) WHERE value->>'kind'='DIRECT_RECIPE' LOOP
  SELECT menuto_hierarchy.recipe_leaf(to_jsonb(r),ARRAY[]::text[]) INTO i FROM public.recipes r WHERE r.id=(t->>'recipe_id')::uuid;
  IF i IS NULL THEN RAISE EXCEPTION 'TARGET_IDENTITY_UNRESOLVED'; END IF;
  identities:=identities||jsonb_build_array(jsonb_build_object('target',t,'identity',i));
 END LOOP;
 SELECT coalesce(array_agg(DISTINCT (value->>'recipe_version_id')::uuid ORDER BY (value->>'recipe_version_id')::uuid),ARRAY[]::uuid[]) INTO vids FROM jsonb_array_elements(bindings);
 FOREACH v IN ARRAY vids LOOP recipes:=recipes||jsonb_build_array(menuto_hierarchy.recipe_snapshot(v)); END LOOP;
 SELECT coalesce(jsonb_agg(jsonb_build_object('contract_version','culinary-feature-scope.v1','id',s.id,'key',public.menuto_feature_key(s.id),'reviews',
  (SELECT coalesce(jsonb_agg(jsonb_build_object('contract_version','culinary-feature-review.v1','id',r.id,'applicability_id',r.applicability_id,'recipe_version_id',r.recipe_version_id,'dimension',r.dimension,'revision_no',r.revision_no,'predecessor_revision_no',r.predecessor_revision_no,'source_sequence',r.source_sequence,'reviewer_user_id',r.reviewer_user_id,'recorded_at',menuto_hierarchy.utc(r.recorded_at),'command',public.menuto_feature_review_command(r.id,false),'command_hash',r.command_hash) ORDER BY r.revision_no),'[]') FROM public.culinary_feature_reviews r WHERE r.applicability_id=s.id)) ORDER BY s.id),'[]') INTO scopes FROM public.culinary_feature_applicabilities s WHERE s.recipe_version_id=ANY(vids);
 RETURN jsonb_build_object('identities',identities,'recipe_frontier',(SELECT generation FROM public.culinary_feature_frontier),'recipes',recipes,'scopes',scopes);
END $$;

CREATE FUNCTION menuto_hierarchy.owner_source(targets jsonb,bindings jsonb) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE a jsonb; b jsonb; ids jsonb; BEGIN
 a:=menuto_hierarchy.catalog_read(targets); b:=menuto_hierarchy.recipes_read(targets,bindings);
 SELECT coalesce(jsonb_agg(value ORDER BY menuto_hierarchy.raw_hash(value->'target')),'[]') INTO ids FROM jsonb_array_elements((a->'identities')||(b->'identities'));
 RETURN (a-'identities')||(b-'identities')||jsonb_build_object('identities',ids);
END $$;

-- Durable publications pin owner identities/fingerprints/frontiers, not capture snapshots.
CREATE FUNCTION menuto_hierarchy.owner_pins(owner jsonb) RETURNS jsonb LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE facts jsonb; targets jsonb; BEGIN
 SELECT coalesce(jsonb_agg(jsonb_build_object('kind',k,'id',v->'id','fingerprint',menuto_hierarchy.raw_hash(v)) ORDER BY k COLLATE "C",v->>'id'),'[]') INTO facts FROM (
  SELECT 'CATALOG_STREAM' k,value v FROM jsonb_array_elements(owner->'catalog_streams') UNION ALL
  SELECT 'RECIPE_VERSION',value FROM jsonb_array_elements(owner->'recipes') UNION ALL
  SELECT 'RECIPE_SCOPE',value FROM jsonb_array_elements(owner->'scopes') UNION ALL
  SELECT 'FEATURE_TERM',value FROM jsonb_array_elements(owner->'terms')
 ) q;
 SELECT coalesce(jsonb_agg(value->'target' ORDER BY menuto_hierarchy.raw_hash(value->'target')),'[]') INTO targets FROM jsonb_array_elements(owner->'identities');
 RETURN jsonb_build_object('catalog_frontier',owner->'catalog_frontier','recipe_frontier',owner->'recipe_frontier','targets',targets,'facts',facts);
END $$;

CREATE FUNCTION menuto_hierarchy.owner_at(pins jsonb) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE owner jsonb; bindings jsonb; streams jsonb; scopes jsonb; terms jsonb; BEGIN
 SELECT coalesce(jsonb_agg(jsonb_build_object('recipe_version_id',value->'id')),'[]') INTO bindings FROM jsonb_array_elements(pins->'facts') WHERE value->>'kind'='RECIPE_VERSION';
 owner:=menuto_hierarchy.owner_source(pins->'targets',bindings);
 SELECT coalesce(jsonb_agg(s||jsonb_build_object('reviews',(SELECT coalesce(jsonb_agg(r ORDER BY (r->>'revision_no')::int),'[]') FROM jsonb_array_elements(s->'reviews') r WHERE (r->>'source_sequence')::bigint<=(pins->>'catalog_frontier')::bigint)) ORDER BY s->>'ingredient_id'),'[]') INTO streams FROM jsonb_array_elements(owner->'catalog_streams') s WHERE EXISTS (SELECT FROM jsonb_array_elements(pins->'facts') p WHERE p->>'kind'='CATALOG_STREAM' AND p->'id'=s->'id');
 SELECT coalesce(jsonb_agg(s||jsonb_build_object('reviews',(SELECT coalesce(jsonb_agg(r ORDER BY (r->>'revision_no')::int),'[]') FROM jsonb_array_elements(s->'reviews') r WHERE (r->>'source_sequence')::bigint<=(pins->>'recipe_frontier')::bigint)) ORDER BY s->>'id'),'[]') INTO scopes FROM jsonb_array_elements(owner->'scopes') s WHERE EXISTS (SELECT FROM jsonb_array_elements(pins->'facts') p WHERE p->>'kind'='RECIPE_SCOPE' AND p->'id'=s->'id');
 SELECT coalesce(jsonb_agg(t ORDER BY t->>'id'),'[]') INTO terms FROM jsonb_array_elements(owner->'terms') t WHERE EXISTS (SELECT FROM jsonb_array_elements(pins->'facts') p WHERE p->>'kind'='FEATURE_TERM' AND p->'id'=t->'id');
 owner:=owner||jsonb_build_object('catalog_frontier',pins->'catalog_frontier','recipe_frontier',pins->'recipe_frontier','catalog_streams',streams,'scopes',scopes,'terms',terms);
 IF menuto_hierarchy.owner_pins(owner) IS DISTINCT FROM pins THEN RAISE EXCEPTION 'Canonical owner facts differ from publication pins'; END IF;
 RETURN owner;
END $$;

CREATE FUNCTION menuto_hierarchy.publish(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE s jsonb:=menuto_hierarchy.session_fact(false); p uuid; who uuid; grant_id uuid; f record; old record; stream record; policy record; key text; h text; d jsonb; fact jsonb; m jsonb; t timestamptz; owner jsonb; targets jsonb; bindings jsonb; body jsonb; cycle boolean; BEGIN
 IF current_setting('transaction_isolation')<>'serializable' OR current_setting('transaction_read_only')<>'off' THEN RAISE EXCEPTION 'Hierarchy writes require caller-owned read-write SERIALIZABLE'; END IF;
 p:=menuto_hierarchy.uuid(c->'provider_id'); who:=menuto_hierarchy.principal(s);
 SELECT * INTO f FROM public.hierarchy_source_frontiers WHERE provider_id=p FOR UPDATE;
 IF f.provider_id IS NULL THEN RAISE EXCEPTION 'Unknown hierarchy provider'; END IF;
 PERFORM menuto_hierarchy.check_provider_binding(p,s);
 grant_id:=menuto_hierarchy.permission(p,who,CASE WHEN c->>'operation'='REPLACE' THEN 'REVIEW_PUBLISH' ELSE 'RETRACT' END);
 -- Authorization precedes even a byte-identical idempotent retry.
 PERFORM menuto_hierarchy.validate_json(c,menuto_hierarchy.command_schema(),menuto_hierarchy.command_schema());
 IF pg_column_size(c)>2097152 THEN RAISE EXCEPTION 'Complete hierarchy command resource limit'; END IF;
 h:=menuto_hierarchy.hash('hierarchy.publication-command.v1',c);
 SELECT * INTO old FROM public.hierarchy_source_revisions WHERE provider_id=p AND principal_id=who AND idempotency_key=c->>'idempotency_key';
 IF old.id IS NOT NULL THEN
  IF old.command_hash<>h THEN RAISE EXCEPTION 'Idempotency conflict'; END IF; RETURN menuto_hierarchy.receipt(old.id);
 END IF;
 IF (c->>'expected_provider_generation')::bigint<>f.source_generation OR c->>'expected_mutation_head_hash' IS DISTINCT FROM f.mutation_head_hash THEN RAISE EXCEPTION 'Provider frontier CAS conflict' USING ERRCODE='40001'; END IF;
 IF (c#>>'{provenance,source_system}') IS DISTINCT FROM (SELECT source_system FROM public.hierarchy_source_providers WHERE id=p) THEN RAISE EXCEPTION 'Provider provenance mismatch'; END IF;
 IF ((c->>'expected_revision')::int=-1) IS DISTINCT FROM (c->'predecessor_id'='null'::jsonb) THEN RAISE EXCEPTION 'Exact predecessor required'; END IF;
 key:=menuto_hierarchy.hash('hierarchy.stream.v1',c->'identity');
 SELECT * INTO stream FROM public.hierarchy_source_streams WHERE provider_id=p AND stream_key=key FOR UPDATE;
 IF coalesce(stream.head_revision,-1)<>(c->>'expected_revision')::int OR stream.head_id IS DISTINCT FROM (c->>'predecessor_id')::uuid THEN RAISE EXCEPTION 'Stream head CAS conflict' USING ERRCODE='40001'; END IF;
 IF c->>'operation'='RETRACT' THEN
  IF c->'policy'<>'null'::jsonb OR c->'relation'<>'null'::jsonb OR stream.id IS NULL OR NOT EXISTS (SELECT FROM public.hierarchy_source_revisions WHERE id=stream.head_id AND operation='REPLACE') THEN RAISE EXCEPTION 'Retraction requires active predecessor and no payload'; END IF;
 ELSIF c#>>'{identity,kind}'='POLICY' THEN
  IF c->'policy'='null'::jsonb OR c->'relation'<>'null'::jsonb OR c#>>'{policy,policy_id}'<>c#>>'{identity,policy_id}' OR c#>'{identity,source}'<>'null'::jsonb OR c#>'{identity,destination}'<>'null'::jsonb OR jsonb_array_length(c#>'{identity,recipe_bindings}')<>0 THEN RAISE EXCEPTION 'Policy stream identity/payload mismatch'; END IF;
  PERFORM menuto_hierarchy.check_policy(c->'policy');
  IF EXISTS (SELECT FROM public.hierarchy_source_revisions r WHERE r.provider_id=p AND r.command#>>'{identity,kind}'='POLICY' AND r.command#>>'{identity,policy_id}'=c#>>'{identity,policy_id}' AND (r.command#>>'{policy,policy_version}')::int>=(c#>>'{policy,policy_version}')::int) THEN RAISE EXCEPTION 'Policy version must increase'; END IF;
 ELSE
  IF c->'relation'='null'::jsonb OR c->'policy'<>'null'::jsonb THEN RAISE EXCEPTION 'Relation payload required'; END IF;
 END IF;
 SELECT coalesce(jsonb_agg(v ORDER BY menuto_hierarchy.raw_hash(v)),'[]') INTO targets FROM (SELECT DISTINCT value v FROM jsonb_array_elements(jsonb_build_array(c#>'{identity,source}',c#>'{identity,destination}')) WHERE value<>'null'::jsonb) a;
 bindings:=c#>'{identity,recipe_bindings}';
 owner:=menuto_hierarchy.owner_source(targets,bindings);
 IF c->>'operation'='REPLACE' AND c#>>'{identity,kind}'='RELATION' THEN
  SELECT r.* INTO policy FROM public.hierarchy_source_streams st JOIN public.hierarchy_source_revisions r ON r.id=st.head_id WHERE st.provider_id=p AND st.kind='POLICY' AND st.policy_id=(c#>>'{identity,policy_id}')::uuid;
  IF policy.id IS NULL OR policy.operation<>'REPLACE' OR policy.id::text<>c#>>'{relation,policy_revision_id}' OR menuto_hierarchy.hash('hierarchy.transfer-policy.v1',policy.command->'policy')<>c#>>'{relation,policy_fingerprint}' THEN RAISE EXCEPTION 'Exact current active policy pin required'; END IF;
  PERFORM menuto_hierarchy.check_relation(c,policy.command->'policy',owner);
  WITH RECURSIVE edges(a,b) AS (
   SELECT menuto_hierarchy.raw_hash(r.command#>'{identity,source}'),menuto_hierarchy.raw_hash(r.command#>'{identity,destination}') FROM public.hierarchy_source_streams st JOIN public.hierarchy_source_revisions r ON r.id=st.head_id WHERE st.provider_id=p AND st.kind='RELATION' AND st.policy_id=(c#>>'{identity,policy_id}')::uuid AND st.stream_key<>key AND r.operation='REPLACE'
   UNION SELECT menuto_hierarchy.raw_hash(c#>'{identity,source}'),menuto_hierarchy.raw_hash(c#>'{identity,destination}')
  ), walk(a,b) AS (SELECT a,b FROM edges UNION SELECT w.a,e.b FROM walk w JOIN edges e ON w.b=e.a)
  SELECT EXISTS (SELECT FROM walk WHERE a=b) INTO cycle;
  IF cycle THEN RAISE EXCEPTION 'Hierarchy cycle prohibited'; END IF;
 END IF;
 t:=clock_timestamp();
 IF EXISTS (SELECT FROM jsonb_array_elements(owner->'catalog_streams') st CROSS JOIN LATERAL jsonb_array_elements(st->'reviews') rv WHERE (rv->>'recorded_at')::timestamptz>t) OR EXISTS (SELECT FROM jsonb_array_elements(owner->'scopes') st CROSS JOIN LATERAL jsonb_array_elements(st->'reviews') rv WHERE (rv->>'recorded_at')::timestamptz>t) THEN RAISE EXCEPTION 'Owner support clock exceeds publication cut'; END IF;
 IF NOT isfinite((c#>>'{provenance,observed_at}')::timestamptz) OR (c#>>'{provenance,observed_at}')::timestamptz>t THEN RAISE EXCEPTION 'Publication source time invalid'; END IF;
 IF stream.id IS NULL THEN
  stream.id:=gen_random_uuid();
  INSERT INTO public.hierarchy_source_streams VALUES (stream.id,p,c#>>'{identity,kind}',(c#>>'{identity,policy_id}')::uuid,c->'identity',key,gen_random_uuid(),0);
 END IF;
 d:=menuto_hierarchy.audit(s,t)||jsonb_build_object('id',gen_random_uuid(),'stream_id',stream.id,'provider_id',p,'principal_id',who,'grant_event_id',grant_id,'operation',c->'operation','command',c,'owner_pins',menuto_hierarchy.owner_pins(owner),'expected_provider_generation',c->'expected_provider_generation','expected_revision',c->'expected_revision','predecessor_id',c->'predecessor_id','idempotency_key',c->'idempotency_key','authority_generation',f.authority_generation,'revision',(c->>'expected_revision')::int+1,'source_sequence',f.source_generation+1,'mutation_sequence',f.mutation_generation+1,'effective_at',menuto_hierarchy.utc(t),'command_hash',h);
 fact:=menuto_hierarchy.revision_fact(d);
 d:=d||jsonb_build_object('fact_hash',menuto_hierarchy.hash('hierarchy.publication.v1',fact-ARRAY['fact_hash','owner_source']));
 INSERT INTO public.hierarchy_source_revisions SELECT * FROM jsonb_populate_record(NULL::public.hierarchy_source_revisions,d);
 m:=menuto_hierarchy.append_mutation(p,f.mutation_generation+1,'PUBLICATION',(d->>'id')::uuid,d->>'fact_hash',t,f.mutation_head_hash);
 UPDATE public.hierarchy_source_streams SET head_id=(d->>'id')::uuid,head_revision=(d->>'revision')::int WHERE id=stream.id;
 UPDATE public.hierarchy_source_frontiers SET source_generation=f.source_generation+1,mutation_generation=f.mutation_generation+1,source_head_id=(d->>'id')::uuid,mutation_head_hash=m->>'journal_hash' WHERE provider_id=p;
 RETURN menuto_hierarchy.receipt((d->>'id')::uuid);
END $$;

CREATE FUNCTION menuto_hierarchy.capture(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE s jsonb:=menuto_hierarchy.session_fact(false); p uuid; who uuid; grant_id uuid; result jsonb; targets jsonb; bindings jsonb; t timestamptz:=clock_timestamp(); item jsonb; ids uuid[]; BEGIN
 IF current_setting('transaction_read_only')<>'on' OR current_setting('transaction_isolation') NOT IN ('repeatable read','serializable') THEN RAISE EXCEPTION 'Clean read-only RR/SERIALIZABLE capture required'; END IF;
 PERFORM menuto_hierarchy.keys(c,ARRAY['provider_id','policy_id','requested_targets']);
 p:=menuto_hierarchy.uuid(c->'provider_id'); PERFORM menuto_hierarchy.uuid(c->'policy_id'); who:=menuto_hierarchy.principal(s); PERFORM menuto_hierarchy.check_provider_binding(p,s); grant_id:=menuto_hierarchy.permission(p,who,'CAPTURE');
 IF jsonb_typeof(c->'requested_targets') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'Exact targets required'; END IF;
 SELECT coalesce(jsonb_agg(v ORDER BY menuto_hierarchy.raw_hash(v)),'[]') INTO targets FROM (
  SELECT DISTINCT value v FROM jsonb_array_elements(c->'requested_targets') UNION SELECT DISTINCT q.v FROM public.hierarchy_source_revisions r CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(r.command#>'{identity,source}',r.command#>'{identity,destination}')) q(v) WHERE r.provider_id=p AND q.v<>'null'::jsonb
 ) a;
 -- Validate the frozen typed identity union using its immutable command schema definition.
 FOR item IN SELECT value FROM jsonb_array_elements(targets) LOOP
  PERFORM menuto_hierarchy.validate_json(item,menuto_hierarchy.command_schema()#>'{$defs,HierarchyStreamIdentity,properties,source}',menuto_hierarchy.command_schema());
 END LOOP;
 SELECT coalesce(jsonb_agg(v ORDER BY v::text),'[]') INTO bindings FROM (SELECT DISTINCT q.v FROM public.hierarchy_source_revisions r CROSS JOIN LATERAL jsonb_array_elements(r.command#>'{identity,recipe_bindings}') q(v) WHERE r.provider_id=p) a;
 SELECT array_agg(DISTINCT id) INTO ids FROM (
  SELECT who id UNION SELECT principal_id FROM public.hierarchy_source_authority WHERE provider_id=p UNION SELECT principal_id FROM public.hierarchy_source_revisions WHERE provider_id=p
 ) q;
 SELECT jsonb_build_object('contract_version','hierarchy-source.v1-draft','request',c,'provider',menuto_hierarchy.provider_fact(to_jsonb(pr)),
  'principals',(SELECT coalesce(jsonb_agg(menuto_hierarchy.principal_fact(to_jsonb(x)) ORDER BY x.id),'[]') FROM public.hierarchy_source_principals x WHERE x.id=ANY(ids)),
  'authority_events',(SELECT coalesce(jsonb_agg(menuto_hierarchy.authority_fact(to_jsonb(x)) ORDER BY x.authority_sequence),'[]') FROM public.hierarchy_source_authority x WHERE x.provider_id=p),
  'publications',(SELECT coalesce(jsonb_agg(menuto_hierarchy.revision_fact(to_jsonb(x)) ORDER BY x.source_sequence),'[]') FROM public.hierarchy_source_revisions x WHERE x.provider_id=p),
  'mutations',(SELECT coalesce(jsonb_agg(menuto_hierarchy.mutation_fact(to_jsonb(x)) ORDER BY x.mutation_sequence),'[]') FROM public.hierarchy_source_mutations x WHERE x.provider_id=p),
  'streams',(SELECT coalesce(jsonb_agg(jsonb_build_object('id',x.id,'provider_id',x.provider_id,'identity',x.identity,'head_id',x.head_id,'head_revision',x.head_revision) ORDER BY x.stream_key),'[]') FROM public.hierarchy_source_streams x WHERE x.provider_id=p),
  'frontier',(SELECT to_jsonb(f) FROM public.hierarchy_source_frontiers f WHERE f.provider_id=p),
  'owner_source',menuto_hierarchy.owner_source(targets,bindings),'reader_principal_id',who,'reader_session',s,'reader_grant_id',grant_id,'capture_started_at',menuto_hierarchy.utc(t),'capture_completed_at',menuto_hierarchy.utc(clock_timestamp()),'isolation',upper(current_setting('transaction_isolation')),'read_only',true)
 INTO result FROM public.hierarchy_source_providers pr WHERE pr.id=p;
 IF result IS NULL THEN RAISE EXCEPTION 'Unknown provider'; END IF;
 IF pg_column_size(result)>16777216 THEN RAISE EXCEPTION 'Complete source capture resource limit; no truncation'; END IF;
 RETURN result;
END $$;

CREATE FUNCTION menuto_hierarchy.immutable() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$ BEGIN RAISE EXCEPTION 'Immutable reviewed hierarchy source'; END $$;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['providers','principals','authority','revisions','mutations'] LOOP
  EXECUTE format('CREATE TRIGGER hierarchy_immutable BEFORE UPDATE OR DELETE ON public.hierarchy_source_%I FOR EACH ROW EXECUTE FUNCTION menuto_hierarchy.immutable()',t);
 END LOOP;
 FOREACH t IN ARRAY ARRAY['providers','principals','frontiers','streams','authority','revisions','mutations'] LOOP
  EXECUTE format('CREATE TRIGGER hierarchy_no_truncate BEFORE TRUNCATE ON public.hierarchy_source_%I FOR EACH STATEMENT EXECUTE FUNCTION menuto_hierarchy.immutable()',t);
 END LOOP;
END $$;

CREATE FUNCTION menuto_hierarchy.coherent() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_hierarchy,pg_temp AS $$
DECLARE p uuid:=NEW.provider_id; f record; ns bigint; na bigint; nm bigint; h record; BEGIN
 SELECT * INTO STRICT f FROM public.hierarchy_source_frontiers WHERE provider_id=p;
 SELECT count(*) INTO ns FROM public.hierarchy_source_revisions WHERE provider_id=p;
 SELECT count(*) INTO na FROM public.hierarchy_source_authority WHERE provider_id=p;
 SELECT count(*) INTO nm FROM public.hierarchy_source_mutations WHERE provider_id=p;
 SELECT * INTO h FROM public.hierarchy_source_mutations WHERE provider_id=p ORDER BY mutation_sequence DESC LIMIT 1;
 IF (ns,na,nm) IS DISTINCT FROM (f.source_generation,f.authority_generation,f.mutation_generation) OR h.mutation_sequence IS DISTINCT FROM nullif(nm,0) OR h.journal_hash IS DISTINCT FROM f.mutation_head_hash OR
 f.source_head_id IS DISTINCT FROM (SELECT id FROM public.hierarchy_source_revisions WHERE provider_id=p ORDER BY source_sequence DESC LIMIT 1) OR
 f.authority_head_id IS DISTINCT FROM (SELECT id FROM public.hierarchy_source_authority WHERE provider_id=p ORDER BY authority_sequence DESC LIMIT 1) OR
 EXISTS (SELECT FROM public.hierarchy_source_mutations m WHERE m.provider_id=p AND (m.predecessor_hash IS DISTINCT FROM (SELECT journal_hash FROM public.hierarchy_source_mutations WHERE provider_id=p AND mutation_sequence=m.mutation_sequence-1) OR m.journal_hash<>menuto_hierarchy.hash('hierarchy.mutation.v1',menuto_hierarchy.mutation_fact(to_jsonb(m))-'journal_hash'))) OR
 EXISTS (SELECT FROM public.hierarchy_source_streams s WHERE s.provider_id=p AND (s.head_id IS DISTINCT FROM (SELECT id FROM public.hierarchy_source_revisions WHERE stream_id=s.id ORDER BY revision DESC LIMIT 1) OR s.identity IS DISTINCT FROM (SELECT command->'identity' FROM public.hierarchy_source_revisions WHERE id=s.head_id) OR s.stream_key<>menuto_hierarchy.hash('hierarchy.stream.v1',s.identity))) OR
 EXISTS (SELECT FROM public.hierarchy_source_revisions r WHERE r.provider_id=p AND (r.fact_hash<>menuto_hierarchy.hash('hierarchy.publication.v1',menuto_hierarchy.revision_fact(to_jsonb(r))-ARRAY['fact_hash','owner_source']) OR r.command_hash<>menuto_hierarchy.hash('hierarchy.publication-command.v1',r.command))) THEN RAISE EXCEPTION 'Incoherent reviewed hierarchy source'; END IF;
 RETURN NULL;
END $$;
DO $$ DECLARE t text; f record; BEGIN
 FOREACH t IN ARRAY ARRAY['frontiers','streams','authority','revisions','mutations'] LOOP EXECUTE format('CREATE CONSTRAINT TRIGGER hierarchy_coherent AFTER INSERT OR UPDATE ON public.hierarchy_source_%I DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_hierarchy.coherent()',t); END LOOP;
 FOREACH t IN ARRAY ARRAY['providers','principals','frontiers','streams','authority','revisions','mutations'] LOOP
  EXECUTE format('ALTER TABLE public.hierarchy_source_%I OWNER TO menuto_hierarchy_owner',t);
  EXECUTE format('REVOKE ALL ON public.hierarchy_source_%I FROM PUBLIC,menuto_hierarchy_admin,menuto_hierarchy_client',t);
 END LOOP;
 FOR f IN SELECT p.oid::regprocedure sig,p.proname FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='menuto_hierarchy' LOOP
  IF f.proname IN ('recipes_read','recipe_snapshot') THEN EXECUTE format('ALTER FUNCTION %s OWNER TO menuto_hierarchy_recipes_owner',f.sig);
  ELSIF f.proname='catalog_read' THEN EXECUTE format('ALTER FUNCTION %s OWNER TO menuto_hierarchy_catalog_owner',f.sig);
  ELSE EXECUTE format('ALTER FUNCTION %s OWNER TO menuto_hierarchy_owner',f.sig); END IF;
  EXECUTE format('REVOKE ALL ON FUNCTION %s FROM PUBLIC',f.sig);
 END LOOP;
END $$;
GRANT EXECUTE ON FUNCTION menuto_hierarchy.utc(timestamptz),menuto_hierarchy.provenance(jsonb),menuto_hierarchy.recipe_leaf(jsonb,text[]),menuto_hierarchy.catalog_term(jsonb),menuto_hierarchy.decimal_text(text) TO menuto_hierarchy_catalog_owner,menuto_hierarchy_recipes_owner;
GRANT EXECUTE ON FUNCTION menuto_hierarchy.catalog_read(jsonb),menuto_hierarchy.recipes_read(jsonb,jsonb) TO menuto_hierarchy_owner;
GRANT EXECUTE ON FUNCTION menuto_hierarchy.register_provider(jsonb),menuto_hierarchy.enroll_principal(jsonb),menuto_hierarchy.change_authority(jsonb) TO menuto_hierarchy_admin;
GRANT EXECUTE ON FUNCTION menuto_hierarchy.publish(jsonb),menuto_hierarchy.capture(jsonb) TO menuto_hierarchy_client;

'''


def upgrade():
    op.execute(TABLE_SQL)
    op.execute(FUNCTION_SQL)


def downgrade():
    op.execute(r"""
    DO $$ BEGIN
      IF EXISTS (SELECT FROM public.hierarchy_source_providers) OR EXISTS (SELECT FROM public.hierarchy_source_principals) THEN
        RAISE EXCEPTION 'Refusing destructive downgrade of populated reviewed hierarchy history';
      END IF;
    END $$;
    REVOKE SELECT ON public.ingredients,public.affinity_feature_terms,public.ingredient_protein_frontier,public.ingredient_protein_streams,public.ingredient_protein_reviews,public.ingredient_protein_review_terms,public.ingredient_protein_assignments FROM menuto_hierarchy_catalog_owner;
    REVOKE SELECT ON public.recipes,public.recipe_versions,public.recipe_version_seals,public.recipe_ingredients,public.recipe_portion_tiers,public.recipe_tier_quantities,public.recipe_variant_rules,public.recipe_rule_combinations,public.recipe_combination_members,public.preparation_transformations,public.culinary_feature_frontier,public.culinary_feature_applicabilities,public.culinary_feature_applicability_tiers,public.culinary_feature_applicability_slots,public.culinary_feature_reviews,public.culinary_feature_review_terms,public.culinary_feature_assignments,public.culinary_feature_main_protein_support FROM menuto_hierarchy_recipes_owner;
    DO $$ DECLARE ns name; BEGIN
      SELECT n.nspname INTO ns FROM pg_catalog.pg_extension e JOIN pg_catalog.pg_namespace n ON n.oid=e.extnamespace WHERE e.extname='sslinfo';
      IF ns IS NOT NULL THEN EXECUTE format('REVOKE EXECUTE ON FUNCTION %I.ssl_is_used() FROM menuto_hierarchy_owner',ns); END IF;
    END $$;
    DROP SCHEMA menuto_hierarchy CASCADE;
    ALTER TABLE public.hierarchy_source_streams DROP CONSTRAINT fk_hierarchy_source_stream_head;
    DROP TABLE public.hierarchy_source_mutations;
    DROP TABLE public.hierarchy_source_revisions;
    DROP TABLE public.hierarchy_source_authority;
    DROP TABLE public.hierarchy_source_streams;
    DROP TABLE public.hierarchy_source_frontiers;
    DROP TABLE public.hierarchy_source_principals;
    DROP TABLE public.hierarchy_source_providers;
    -- Structural cluster roles/credentials are outside database migration lifecycle.
    """)
