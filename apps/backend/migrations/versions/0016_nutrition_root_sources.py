"""Independent Nutrition root source authority; empty installation, no content seeds."""

# SQL is frozen in this migration; keep complete statements visible for authority review.
# ruff: noqa: E501

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

TABLE_SQL = r"""
CREATE SEQUENCE nutrition_source_recorded_order;

CREATE TABLE nutrition_source_providers (
	id UUID NOT NULL,
	provider_id UUID NOT NULL,
	previous_id UUID,
	generation BIGINT NOT NULL,
	database_oid BIGINT NOT NULL,
	database_name VARCHAR(63) NOT NULL,
	actor_role_oid BIGINT NOT NULL,
	code VARCHAR(100) NOT NULL,
	version VARCHAR(100) NOT NULL,
	environment VARCHAR(30) NOT NULL,
	command JSONB NOT NULL,
	administrator JSONB NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	CONSTRAINT pk_nutrition_source_providers PRIMARY KEY (id),
	CONSTRAINT uq_nutrition_source_providers_provider_id_generation UNIQUE (provider_id, generation),
	CONSTRAINT uq_nutrition_source_providers_database_oid_actor_role_o_5199 UNIQUE (database_oid, actor_role_oid, idempotency_key),
	CONSTRAINT ck_nutrition_source_providers_generation CHECK (generation>0 AND (generation=1)=(previous_id IS NULL)),
	CONSTRAINT ck_nutrition_source_providers_recorded_time CHECK (isfinite(recorded_at)),
	CONSTRAINT ck_nutrition_source_providers_environment CHECK (environment IN ('TEST_ONLY','REVIEWED_PRODUCTION'))
)

;

CREATE TABLE nutrition_source_principals (
	id UUID NOT NULL,
	database_oid BIGINT NOT NULL,
	database_name VARCHAR(63) NOT NULL,
	role_oid BIGINT NOT NULL,
	role_name VARCHAR(63) NOT NULL,
	verified_human_id UUID,
	user_id UUID,
	service_id VARCHAR(100),
	delegation_registrar BOOLEAN NOT NULL,
	command JSONB NOT NULL,
	administrator JSONB NOT NULL,
	actor_role_oid BIGINT NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	CONSTRAINT pk_nutrition_source_principals PRIMARY KEY (id),
	CONSTRAINT uq_nutrition_source_principals_database_oid_role_oid_role_name UNIQUE (database_oid, role_oid, role_name),
	CONSTRAINT uq_nutrition_source_principals_database_oid_actor_role__693d UNIQUE (database_oid, actor_role_oid, idempotency_key),
	CONSTRAINT ck_nutrition_source_principals_identity_class CHECK ((verified_human_id IS NULL)<>(service_id IS NULL)),
	CONSTRAINT ck_nutrition_source_principals_service_not_author CHECK (service_id IS NULL OR (user_id IS NULL AND NOT delegation_registrar)),
	CONSTRAINT ck_nutrition_source_principals_recorded_time CHECK (isfinite(recorded_at))
)

;

CREATE TABLE nutrition_source_streams (
	stream_key VARCHAR(64) NOT NULL,
	kind VARCHAR(20) NOT NULL,
	identity JSONB NOT NULL,
	revision BIGINT NOT NULL,
	head_id UUID,
	head_hash VARCHAR(64),
	CONSTRAINT pk_nutrition_source_streams PRIMARY KEY (stream_key),
	CONSTRAINT ck_nutrition_source_streams_kind CHECK (kind IN ('SOURCE','AUTHORITY','LOCK')),
	CONSTRAINT ck_nutrition_source_streams_frontier CHECK (revision>=0 AND (kind='LOCK' OR ((revision=0)=(head_id IS NULL) AND (revision=0)=(head_hash IS NULL))))
)

;

CREATE TABLE nutrition_source_receipts (
	id UUID NOT NULL,
	kind VARCHAR(20) NOT NULL,
	recorded_order BIGINT NOT NULL,
	stream_key VARCHAR(64) NOT NULL,
	sequence BIGINT NOT NULL,
	previous_id UUID,
	previous_hash VARCHAR(64),
	principal_id UUID,
	grant_event_id UUID,
	authority_generation BIGINT NOT NULL,
	provider_enrollment_id UUID,
	actor_database_oid BIGINT NOT NULL,
	actor_role_oid BIGINT NOT NULL,
	actor JSONB NOT NULL,
	subject_witness JSONB,
	delegation_event_id UUID,
	legacy_anchor JSONB,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	idempotency_key VARCHAR(100) NOT NULL,
	command_hash VARCHAR(64) NOT NULL,
	fact_hash VARCHAR(64) NOT NULL,
	CONSTRAINT pk_nutrition_source_receipts PRIMARY KEY (id),
	CONSTRAINT uq_nutrition_source_receipts_stream_key_sequence UNIQUE (stream_key, sequence),
	CONSTRAINT uq_nutrition_source_receipts_recorded_order UNIQUE (recorded_order),
	CONSTRAINT uq_nutrition_source_receipts_actor_database_oid_actor_r_a970 UNIQUE (actor_database_oid, actor_role_oid, idempotency_key),
	CONSTRAINT ck_nutrition_source_receipts_kind CHECK (kind IN ('AUTHORITY','DRAFT','REVIEW','PUBLICATION','DELEGATION','OBSERVATION','ASSESSMENT','GOAL')),
	CONSTRAINT ck_nutrition_source_receipts_sequence_time CHECK (sequence>0 AND authority_generation>=0 AND isfinite(recorded_at)),
	CONSTRAINT ck_nutrition_source_receipts_predecessor CHECK ((sequence=1)=(previous_id IS NULL) AND (sequence=1)=(previous_hash IS NULL)),
	CONSTRAINT ck_nutrition_source_receipts_authority_class CHECK ((kind='AUTHORITY')=(principal_id IS NULL) AND (kind='AUTHORITY')=(grant_event_id IS NULL))
)

;

CREATE TABLE nutrition_source_authority (
	id UUID NOT NULL,
	principal_id UUID NOT NULL,
	provider_id UUID,
	family_id VARCHAR(100),
	household_id UUID,
	member_id UUID,
	capability VARCHAR(40) NOT NULL,
	action VARCHAR(10) NOT NULL,
	protocol_fingerprint VARCHAR(64),
	fact_key VARCHAR(20),
	effective_from TIMESTAMP WITH TIME ZONE NOT NULL,
	effective_until TIMESTAMP WITH TIME ZONE NOT NULL,
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_source_authority PRIMARY KEY (id),
	CONSTRAINT ck_nutrition_source_authority_effective_interval CHECK (isfinite(effective_from) AND isfinite(effective_until) AND effective_from<effective_until),
	CONSTRAINT ck_nutrition_source_authority_action CHECK (action IN ('GRANT','REVOKE')),
	CONSTRAINT ck_nutrition_source_authority_capability CHECK (capability IN ('GUIDELINE_REVIEW','GUIDELINE_PUBLISH','GUIDELINE_WITHDRAW','ELIGIBILITY_ATTEST','MEMBER_OBSERVATION_WRITE','MEMBER_GOAL_WRITE','ROOT_SOURCE_READ','VALIDATOR_SOURCE_READ'))
)

;

CREATE TABLE nutrition_guideline_drafts (
	id UUID NOT NULL,
	provider_id UUID NOT NULL,
	family_id VARCHAR(100) NOT NULL,
	body_fingerprint VARCHAR(64) NOT NULL,
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_guideline_drafts PRIMARY KEY (id)
)

;

CREATE TABLE nutrition_guideline_reviews (
	id UUID NOT NULL,
	draft_revision_id UUID NOT NULL,
	decision VARCHAR(10) NOT NULL,
	prior_review_id UUID,
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_guideline_reviews PRIMARY KEY (id),
	CONSTRAINT ck_nutrition_guideline_reviews_decision CHECK (decision IN ('APPROVE','CANCEL'))
)

;

CREATE TABLE nutrition_guideline_publications (
	id UUID NOT NULL,
	draft_revision_id UUID NOT NULL,
	action VARCHAR(10) NOT NULL,
	review_event_id UUID,
	prior_publication_id UUID,
	effective_at TIMESTAMP WITH TIME ZONE NOT NULL,
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_guideline_publications PRIMARY KEY (id),
	CONSTRAINT ck_nutrition_guideline_publications_action CHECK (action IN ('PUBLISH','SUPERSEDE','RETIRE','RETRACT')),
	CONSTRAINT ck_nutrition_guideline_publications_effective_time CHECK (isfinite(effective_at))
)

;

CREATE TABLE nutrition_member_delegations (
	id UUID NOT NULL,
	household_id UUID NOT NULL,
	member_id UUID NOT NULL,
	grantee_principal_id UUID NOT NULL,
	operation_scope VARCHAR(30) NOT NULL,
	action VARCHAR(10) NOT NULL,
	previous_grant_id UUID,
	effective_from TIMESTAMP WITH TIME ZONE NOT NULL,
	effective_until TIMESTAMP WITH TIME ZONE NOT NULL,
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_member_delegations PRIMARY KEY (id),
	CONSTRAINT ck_nutrition_member_delegations_effective_interval CHECK (isfinite(effective_from) AND isfinite(effective_until) AND effective_from<effective_until),
	CONSTRAINT ck_nutrition_member_delegations_operation_scope CHECK (operation_scope IN ('MEMBER_GOAL_WRITE','BODY_MASS_WRITE','HEIGHT_WRITE')),
	CONSTRAINT ck_nutrition_member_delegations_action CHECK (action IN ('GRANT','REVOKE'))
)

;

CREATE TABLE nutrition_physiology_revisions (
	id UUID NOT NULL,
	household_id UUID NOT NULL,
	member_id UUID NOT NULL,
	operation VARCHAR(10) NOT NULL,
	effective_from TIMESTAMP WITH TIME ZONE NOT NULL,
	effective_until TIMESTAMP WITH TIME ZONE NOT NULL,
	fact_key VARCHAR(20) NOT NULL,
	unit VARCHAR(10) NOT NULL,
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_physiology_revisions PRIMARY KEY (id),
	CONSTRAINT ck_nutrition_physiology_revisions_fact_unit CHECK ((fact_key='BODY_MASS' AND unit='KG') OR (fact_key='HEIGHT' AND unit='CM')),
	CONSTRAINT ck_nutrition_physiology_revisions_effective_interval CHECK (isfinite(effective_from) AND isfinite(effective_until) AND effective_from<effective_until),
	CONSTRAINT ck_nutrition_physiology_revisions_operation CHECK (operation IN ('CREATE','REPLACE','CORRECT','RETRACT'))
)

;

CREATE TABLE nutrition_eligibility_revisions (
	id UUID NOT NULL,
	household_id UUID NOT NULL,
	member_id UUID NOT NULL,
	operation VARCHAR(10) NOT NULL,
	effective_from TIMESTAMP WITH TIME ZONE NOT NULL,
	effective_until TIMESTAMP WITH TIME ZONE NOT NULL,
	guideline_revision_id UUID NOT NULL,
	protocol_fingerprint VARCHAR(64) NOT NULL,
	outcome VARCHAR(20) NOT NULL,
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_eligibility_revisions PRIMARY KEY (id),
	CONSTRAINT ck_nutrition_eligibility_revisions_outcome CHECK (outcome IN ('ADMITTED','OUT_OF_SCOPE','EXCLUDED','UNDETERMINED')),
	CONSTRAINT ck_nutrition_eligibility_revisions_effective_interval CHECK (isfinite(effective_from) AND isfinite(effective_until) AND effective_from<effective_until),
	CONSTRAINT ck_nutrition_eligibility_revisions_operation CHECK (operation IN ('CREATE','REPLACE','CORRECT','RETRACT'))
)

;

CREATE TABLE nutrition_goal_revisions (
	id UUID NOT NULL,
	household_id UUID NOT NULL,
	member_id UUID NOT NULL,
	operation VARCHAR(10) NOT NULL,
	effective_from TIMESTAMP WITH TIME ZONE NOT NULL,
	effective_until TIMESTAMP WITH TIME ZONE NOT NULL,
	goal_id UUID NOT NULL,
	goal_type VARCHAR(30) NOT NULL,
	direction VARCHAR(10),
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_goal_revisions PRIMARY KEY (id),
	CONSTRAINT ck_nutrition_goal_revisions_goal_type CHECK (goal_type='ENERGY_DIRECTION'),
	CONSTRAINT ck_nutrition_goal_revisions_intent_only CHECK ((operation='RETRACT' AND direction IS NULL) OR (operation<>'RETRACT' AND direction IN ('CUT','MAINTAIN','GAIN'))),
	CONSTRAINT ck_nutrition_goal_revisions_effective_interval CHECK (isfinite(effective_from) AND isfinite(effective_until) AND effective_from<effective_until),
	CONSTRAINT ck_nutrition_goal_revisions_operation CHECK (operation IN ('CREATE','REPLACE','CORRECT','RETRACT'))
)

;

CREATE TABLE nutrition_source_evidence_artifacts (
	environment VARCHAR(30) NOT NULL,
	evidence_id VARCHAR(100) NOT NULL,
	version VARCHAR(100) NOT NULL,
	body_fingerprint VARCHAR(64) NOT NULL,
	body JSONB NOT NULL,
	CONSTRAINT pk_nutrition_source_evidence_artifacts PRIMARY KEY (environment, evidence_id, version),
	CONSTRAINT ck_nutrition_source_evidence_artifacts_environment CHECK (environment IN ('TEST_ONLY','REVIEWED_PRODUCTION'))
)

;
ALTER TABLE nutrition_source_providers ADD CONSTRAINT fk_nutrition_source_providers_previous_id_nutrition_sou_9c1b FOREIGN KEY(previous_id) REFERENCES nutrition_source_providers (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_providers ADD CONSTRAINT fk_nutrition_source_providers_provider_id_nutrition_sou_a904 FOREIGN KEY(provider_id) REFERENCES nutrition_source_providers (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_principals ADD CONSTRAINT fk_nutrition_source_principals_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_streams ADD CONSTRAINT fk_nutrition_source_streams_head_id_nutrition_source_receipts FOREIGN KEY(head_id) REFERENCES nutrition_source_receipts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_receipts ADD CONSTRAINT fk_nutrition_source_receipts_delegation_event_id_nutrit_3fef FOREIGN KEY(delegation_event_id) REFERENCES nutrition_member_delegations (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_receipts ADD CONSTRAINT fk_nutrition_source_receipts_grant_event_id_nutrition_s_9b85 FOREIGN KEY(grant_event_id) REFERENCES nutrition_source_authority (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_receipts ADD CONSTRAINT fk_nutrition_source_receipts_previous_id_nutrition_sour_4729 FOREIGN KEY(previous_id) REFERENCES nutrition_source_receipts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_receipts ADD CONSTRAINT fk_nutrition_source_receipts_principal_id_nutrition_sou_34e4 FOREIGN KEY(principal_id) REFERENCES nutrition_source_principals (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_receipts ADD CONSTRAINT fk_nutrition_source_receipts_provider_enrollment_id_nut_55ae FOREIGN KEY(provider_enrollment_id) REFERENCES nutrition_source_providers (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_receipts ADD CONSTRAINT fk_nutrition_source_receipts_stream_key_nutrition_sourc_5414 FOREIGN KEY(stream_key) REFERENCES nutrition_source_streams (stream_key) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_authority ADD CONSTRAINT fk_nutrition_source_authority_household_id_household_members FOREIGN KEY(household_id, member_id) REFERENCES household_members (household_id, id) ON DELETE RESTRICT;
ALTER TABLE nutrition_source_authority ADD CONSTRAINT fk_nutrition_source_authority_id_nutrition_source_receipts FOREIGN KEY(id) REFERENCES nutrition_source_receipts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_authority ADD CONSTRAINT fk_nutrition_source_authority_principal_id_nutrition_so_dacb FOREIGN KEY(principal_id) REFERENCES nutrition_source_principals (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_source_authority ADD CONSTRAINT fk_nutrition_source_authority_provider_id_nutrition_sou_1f40 FOREIGN KEY(provider_id) REFERENCES nutrition_source_providers (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_guideline_drafts ADD CONSTRAINT fk_nutrition_guideline_drafts_id_nutrition_source_receipts FOREIGN KEY(id) REFERENCES nutrition_source_receipts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_guideline_drafts ADD CONSTRAINT fk_nutrition_guideline_drafts_provider_id_nutrition_sou_73f2 FOREIGN KEY(provider_id) REFERENCES nutrition_source_providers (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_guideline_reviews ADD CONSTRAINT fk_nutrition_guideline_reviews_draft_revision_id_nutrit_b62e FOREIGN KEY(draft_revision_id) REFERENCES nutrition_guideline_drafts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_guideline_reviews ADD CONSTRAINT fk_nutrition_guideline_reviews_id_nutrition_source_receipts FOREIGN KEY(id) REFERENCES nutrition_source_receipts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_guideline_reviews ADD CONSTRAINT fk_nutrition_guideline_reviews_prior_review_id_nutritio_458c FOREIGN KEY(prior_review_id) REFERENCES nutrition_guideline_reviews (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_guideline_publications ADD CONSTRAINT fk_nutrition_guideline_publications_draft_revision_id_n_ca48 FOREIGN KEY(draft_revision_id) REFERENCES nutrition_guideline_drafts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_guideline_publications ADD CONSTRAINT fk_nutrition_guideline_publications_id_nutrition_source_69bd FOREIGN KEY(id) REFERENCES nutrition_source_receipts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_guideline_publications ADD CONSTRAINT fk_nutrition_guideline_publications_prior_publication_i_b54e FOREIGN KEY(prior_publication_id) REFERENCES nutrition_guideline_publications (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_guideline_publications ADD CONSTRAINT fk_nutrition_guideline_publications_review_event_id_nut_059b FOREIGN KEY(review_event_id) REFERENCES nutrition_guideline_reviews (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_member_delegations ADD CONSTRAINT fk_nutrition_member_delegations_grantee_principal_id_nu_4934 FOREIGN KEY(grantee_principal_id) REFERENCES nutrition_source_principals (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_member_delegations ADD CONSTRAINT fk_nutrition_member_delegations_household_id_household_members FOREIGN KEY(household_id, member_id) REFERENCES household_members (household_id, id) ON DELETE RESTRICT;
ALTER TABLE nutrition_member_delegations ADD CONSTRAINT fk_nutrition_member_delegations_id_nutrition_source_receipts FOREIGN KEY(id) REFERENCES nutrition_source_receipts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_member_delegations ADD CONSTRAINT fk_nutrition_member_delegations_previous_grant_id_nutri_a5eb FOREIGN KEY(previous_grant_id) REFERENCES nutrition_member_delegations (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_physiology_revisions ADD CONSTRAINT fk_nutrition_physiology_revisions_household_id_househol_8bf9 FOREIGN KEY(household_id, member_id) REFERENCES household_members (household_id, id) ON DELETE RESTRICT;
ALTER TABLE nutrition_physiology_revisions ADD CONSTRAINT fk_nutrition_physiology_revisions_id_nutrition_source_receipts FOREIGN KEY(id) REFERENCES nutrition_source_receipts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_eligibility_revisions ADD CONSTRAINT fk_nutrition_eligibility_revisions_guideline_revision_i_f9a3 FOREIGN KEY(guideline_revision_id) REFERENCES nutrition_guideline_drafts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_eligibility_revisions ADD CONSTRAINT fk_nutrition_eligibility_revisions_household_id_househo_5ded FOREIGN KEY(household_id, member_id) REFERENCES household_members (household_id, id) ON DELETE RESTRICT;
ALTER TABLE nutrition_eligibility_revisions ADD CONSTRAINT fk_nutrition_eligibility_revisions_id_nutrition_source_receipts FOREIGN KEY(id) REFERENCES nutrition_source_receipts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE nutrition_goal_revisions ADD CONSTRAINT fk_nutrition_goal_revisions_household_id_household_members FOREIGN KEY(household_id, member_id) REFERENCES household_members (household_id, id) ON DELETE RESTRICT;
ALTER TABLE nutrition_goal_revisions ADD CONSTRAINT fk_nutrition_goal_revisions_id_nutrition_source_receipts FOREIGN KEY(id) REFERENCES nutrition_source_receipts (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX ix_nutrition_source_providers_previous_id ON nutrition_source_providers (previous_id);
CREATE UNIQUE INDEX uq_nutrition_provider_identity ON nutrition_source_providers (code, version) WHERE generation = 1;
CREATE INDEX ix_nutrition_source_principals_user_id ON nutrition_source_principals (user_id);
CREATE INDEX ix_nutrition_source_streams_head_id ON nutrition_source_streams (head_id);
CREATE INDEX ix_nutrition_source_receipts_delegation_event_id ON nutrition_source_receipts (delegation_event_id);
CREATE INDEX ix_nutrition_source_receipts_grant_event_id ON nutrition_source_receipts (grant_event_id);
CREATE INDEX ix_nutrition_source_receipts_previous_id ON nutrition_source_receipts (previous_id);
CREATE INDEX ix_nutrition_source_receipts_principal_id ON nutrition_source_receipts (principal_id);
CREATE INDEX ix_nutrition_source_receipts_provider_enrollment_id ON nutrition_source_receipts (provider_enrollment_id);
CREATE INDEX ix_nutrition_source_authority_household_id_member_id ON nutrition_source_authority (household_id, member_id);
CREATE INDEX ix_nutrition_source_authority_principal_id ON nutrition_source_authority (principal_id);
CREATE INDEX ix_nutrition_source_authority_provider_id ON nutrition_source_authority (provider_id);
CREATE INDEX ix_nutrition_guideline_drafts_provider_id ON nutrition_guideline_drafts (provider_id);
CREATE INDEX ix_nutrition_guideline_reviews_draft_revision_id ON nutrition_guideline_reviews (draft_revision_id);
CREATE INDEX ix_nutrition_guideline_reviews_prior_review_id ON nutrition_guideline_reviews (prior_review_id);
CREATE INDEX ix_nutrition_guideline_publications_draft_revision_id ON nutrition_guideline_publications (draft_revision_id);
CREATE INDEX ix_nutrition_guideline_publications_prior_publication_id ON nutrition_guideline_publications (prior_publication_id);
CREATE INDEX ix_nutrition_guideline_publications_review_event_id ON nutrition_guideline_publications (review_event_id);
CREATE INDEX ix_nutrition_member_delegations_grantee_principal_id ON nutrition_member_delegations (grantee_principal_id);
CREATE INDEX ix_nutrition_member_delegations_household_id_member_id ON nutrition_member_delegations (household_id, member_id);
CREATE INDEX ix_nutrition_member_delegations_previous_grant_id ON nutrition_member_delegations (previous_grant_id);
CREATE INDEX ix_nutrition_physiology_revisions_household_id_member_id ON nutrition_physiology_revisions (household_id, member_id);
CREATE INDEX ix_nutrition_eligibility_revisions_guideline_revision_id ON nutrition_eligibility_revisions (guideline_revision_id);
CREATE INDEX ix_nutrition_eligibility_revisions_household_id_member_id ON nutrition_eligibility_revisions (household_id, member_id);
CREATE INDEX ix_nutrition_goal_revisions_household_id_member_id ON nutrition_goal_revisions (household_id, member_id);
"""

FUNCTION_SQL = r"""
-- This file is a construction scratchpad. The implementation migration receives frozen SQL.
DO $$ DECLARE n text; BEGIN
 FOREACH n IN ARRAY ARRAY['menuto_nutrition_owner','menuto_nutrition_admin','menuto_nutrition_client'] LOOP
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname=n) THEN
   EXECUTE format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS',n);
  END IF;
  IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname=n AND
    (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN
   RAISE EXCEPTION 'Unsafe existing Nutrition infrastructure role';
  END IF;
 END LOOP;
 IF EXISTS (SELECT FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid=m.member WHERE r.rolname='menuto_nutrition_owner') THEN
  RAISE EXCEPTION 'Nutrition source owner must not inherit external roles';
 END IF;
END $$;
CREATE SCHEMA menuto_nutrition AUTHORIZATION menuto_nutrition_owner;
REVOKE ALL ON SCHEMA menuto_nutrition FROM PUBLIC;
GRANT USAGE ON SCHEMA menuto_nutrition TO menuto_nutrition_admin,menuto_nutrition_client;
GRANT USAGE ON SCHEMA public TO menuto_nutrition_owner;
GRANT SELECT ON public.users,public.households,public.household_members,public.memberships,
 public.member_nutrition_profiles TO menuto_nutrition_owner;
DO $$ DECLARE ns name; BEGIN
 IF NOT EXISTS (SELECT FROM pg_catalog.pg_extension WHERE extname='sslinfo') THEN
  CREATE EXTENSION sslinfo WITH SCHEMA menuto_nutrition;
 END IF;
 SELECT n.nspname INTO STRICT ns FROM pg_catalog.pg_extension e JOIN pg_catalog.pg_namespace n ON n.oid=e.extnamespace WHERE e.extname='sslinfo';
 EXECUTE format('GRANT USAGE ON SCHEMA %I TO menuto_nutrition_owner',ns);
 EXECUTE format('GRANT EXECUTE ON FUNCTION %I.ssl_is_used() TO menuto_nutrition_owner',ns);
 EXECUTE format('CREATE FUNCTION menuto_nutrition.backend_tls() RETURNS boolean LANGUAGE sql STABLE SET search_path=pg_catalog,menuto_nutrition,pg_temp BEGIN ATOMIC SELECT %I.ssl_is_used(); END',ns);
END $$;

CREATE FUNCTION menuto_nutrition.utc(t timestamptz) RETURNS text LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
 SELECT to_char(t AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
$$;
CREATE FUNCTION menuto_nutrition.canonical(j jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE r text; BEGIN
 CASE jsonb_typeof(j)
 WHEN 'object' THEN SELECT '{'||coalesce(string_agg(to_jsonb(key)::text||':'||menuto_nutrition.canonical(value),',' ORDER BY key COLLATE "C"),'')||'}' INTO r FROM jsonb_each(j);
 WHEN 'array' THEN SELECT '['||coalesce(string_agg(menuto_nutrition.canonical(value),',' ORDER BY ord),'')||']' INTO r FROM jsonb_array_elements(j) WITH ORDINALITY a(value,ord);
 WHEN 'number' THEN
  IF j::text !~ '^-?(0|[1-9][0-9]*)$' THEN RAISE EXCEPTION 'Exact integer required'; END IF; r:=j::text;
 ELSE r:=j::text;
 END CASE; RETURN r;
END $$;
CREATE FUNCTION menuto_nutrition.hash(domain text,j jsonb) RETURNS text LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
 SELECT encode(sha256(convert_to(menuto_nutrition.canonical(jsonb_build_object('domain',domain,'value',j)),'UTF8')),'hex')
$$;
CREATE FUNCTION menuto_nutrition.uuid(j jsonb) RETURNS uuid LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE v uuid; BEGIN
 IF jsonb_typeof(j) IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'UUID string required'; END IF;
 v:=(j#>>'{}')::uuid;
 IF v::text<>(j#>>'{}') THEN RAISE EXCEPTION 'Canonical UUID required'; END IF; RETURN v;
END $$;
CREATE FUNCTION menuto_nutrition.bounds(j jsonb, maxbytes integer, depth integer DEFAULT 0) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE x jsonb; BEGIN
 IF depth>32 OR octet_length(j::text)>maxbytes THEN RAISE EXCEPTION 'Nutrition source structural/byte limit; all-or-error'; END IF;
 CASE jsonb_typeof(j)
 WHEN 'number' THEN
  IF length(j::text)>40 OR j::text !~ '^-?(0|[1-9][0-9]*)$' OR abs(j::text::numeric)>170141183460469231731687303715884105727 THEN
   RAISE EXCEPTION 'Nutrition source exact integer size limit';
  END IF;
 WHEN 'array' THEN
  IF jsonb_array_length(j)>4096 THEN RAISE EXCEPTION 'Nutrition source row limit'; END IF;
  FOR x IN SELECT value FROM jsonb_array_elements(j) LOOP PERFORM menuto_nutrition.bounds(x,maxbytes,depth+1); END LOOP;
 WHEN 'object' THEN
  FOR x IN SELECT value FROM jsonb_each(j) LOOP PERFORM menuto_nutrition.bounds(x,maxbytes,depth+1); END LOOP;
 ELSE NULL;
 END CASE;
END $$;
CREATE FUNCTION menuto_nutrition.deadline(t timestamptz) RETURNS void LANGUAGE plpgsql VOLATILE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$ BEGIN
 IF clock_timestamp()-t>interval '15 seconds' THEN RAISE EXCEPTION 'Nutrition source operation budget exceeded' USING ERRCODE='57014'; END IF;
END $$;
CREATE FUNCTION menuto_nutrition.safe_role(login name, admin_mode boolean) RETURNS void LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE r record; dbowner oid; BEGIN
 SELECT * INTO r FROM pg_catalog.pg_roles WHERE rolname=login;
 SELECT datdba INTO dbowner FROM pg_catalog.pg_database WHERE datname=current_database();
 IF r.oid IS NULL OR NOT r.rolcanlogin OR r.oid=dbowner OR
  EXISTS (SELECT FROM pg_catalog.pg_roles x WHERE
   (x.rolsuper OR x.rolcreaterole OR x.rolcreatedb OR x.rolreplication OR x.rolbypassrls OR x.oid=dbowner
    OR x.rolname IN ('pg_read_all_data','pg_write_all_data','pg_read_server_files','pg_write_server_files',
      'pg_execute_server_program','pg_signal_backend','pg_maintain','pg_checkpoint','pg_create_subscription')
    OR x.rolname ~ '^menuto_.*_owner$' OR (x.rolname ~ '^menuto_.*_admin$' AND (NOT admin_mode OR x.rolname<>'menuto_nutrition_admin')))
   AND pg_catalog.pg_has_role(r.oid,x.oid,'MEMBER')) OR
  has_schema_privilege(login,'menuto_nutrition','CREATE') THEN
  RAISE EXCEPTION 'Unsafe Nutrition source login' USING ERRCODE='42501';
 END IF;
 IF EXISTS (SELECT FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relname IN
    ('nutrition_source_providers','nutrition_source_principals','nutrition_source_streams','nutrition_source_receipts',
     'nutrition_source_authority','nutrition_guideline_drafts','nutrition_guideline_reviews','nutrition_guideline_publications',
     'nutrition_member_delegations','nutrition_physiology_revisions','nutrition_eligibility_revisions','nutrition_goal_revisions','nutrition_source_evidence_artifacts')
   AND (has_table_privilege(login,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') OR c.relowner=r.oid)) THEN
  RAISE EXCEPTION 'Source login has direct mutation privileges or unscoped source reads' USING ERRCODE='42501';
 END IF;
END $$;
CREATE FUNCTION menuto_nutrition.session_fact(admin_mode boolean) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE r record; d record; addr inet; BEGIN
 IF system_user IS DISTINCT FROM ('scram-sha-256:'||session_user) OR current_setting('role')<>'none' THEN
  RAISE EXCEPTION 'SCRAM authenticated original session required; SET ROLE is not authorship' USING ERRCODE='28000';
 END IF;
 PERFORM menuto_nutrition.safe_role(session_user,admin_mode);
 IF admin_mode AND NOT pg_catalog.pg_has_role(session_user,'menuto_nutrition_admin','MEMBER') THEN
  RAISE EXCEPTION 'Separate Nutrition enrollment administrator required' USING ERRCODE='42501';
 END IF;
 addr:=inet_client_addr();
 IF addr IS NULL OR (addr NOT IN ('127.0.0.1'::inet,'::1'::inet) AND NOT menuto_nutrition.backend_tls()) THEN
  RAISE EXCEPTION 'Remote Nutrition source requires TLS' USING ERRCODE='28000';
 END IF;
 SELECT oid,rolname INTO STRICT r FROM pg_catalog.pg_roles WHERE rolname=session_user;
 SELECT oid,datname INTO STRICT d FROM pg_catalog.pg_database WHERE datname=current_database();
 RETURN jsonb_build_object('database_oid',d.oid::bigint,'database_name',d.datname,'role_oid',r.oid::bigint,
  'role_name',r.rolname,'authentication_method','scram-sha-256','authenticated_identity',r.rolname);
END $$;
CREATE FUNCTION menuto_nutrition.interval_ok(j jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$ BEGIN
 IF (j->>'start')::timestamptz >= (j->>'end')::timestamptz THEN RAISE EXCEPTION 'Nonempty effective interval required'; END IF;
END $$;
CREATE FUNCTION menuto_nutrition.covers(outer_interval jsonb,inner_interval jsonb) RETURNS boolean LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
 SELECT (outer_interval->>'start')::timestamptz<=(inner_interval->>'start')::timestamptz
    AND (outer_interval->>'end')::timestamptz>=(inner_interval->>'end')::timestamptz
$$;
CREATE FUNCTION menuto_nutrition.amount(j jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE n numeric:=(j->>'numerator')::numeric; d numeric:=(j->>'denominator')::numeric; BEGIN
 IF n<0 OR d<=0 OR gcd(n,d)<>1 THEN RAISE EXCEPTION 'Reduced nonnegative exact rational required'; END IF;
END $$;
CREATE FUNCTION menuto_nutrition.evidence(j jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$ BEGIN
 IF j->>'body_fingerprint'<>menuto_nutrition.hash('nutrition.evidence-body.v1',j->'body') THEN RAISE EXCEPTION 'Retained evidence body differs'; END IF;
END $$;
CREATE FUNCTION menuto_nutrition.strict_sets(j jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE sorted jsonb; BEGIN
 SELECT coalesce(jsonb_agg(v ORDER BY v::text COLLATE "C"),'[]') INTO sorted FROM (SELECT DISTINCT value v FROM jsonb_array_elements(j)) q;
 IF j<>sorted THEN RAISE EXCEPTION 'Unique sorted keys required'; END IF;
END $$;
CREATE FUNCTION menuto_nutrition.authority_group(s jsonb) RETURNS jsonb LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
 SELECT CASE WHEN s->'member_id'<>'null'::jsonb THEN s||jsonb_build_object('provider_id',NULL,'family_id',NULL) ELSE s END
$$;
CREATE FUNCTION menuto_nutrition.authority_key(s jsonb) RETURNS text LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$ SELECT menuto_nutrition.hash('nutrition.authority-stream.v1',menuto_nutrition.authority_group(s)) $$;
CREATE FUNCTION menuto_nutrition.source_key(s jsonb) RETURNS text LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$ SELECT menuto_nutrition.hash('nutrition.source-stream.v1',s) $$;
CREATE FUNCTION menuto_nutrition.subject(h uuid,m uuid) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
 SELECT jsonb_build_object('contract_version','household-member-identity.v1','household_id',household_id,'member_id',id)
 FROM public.household_members WHERE household_id=h AND id=m
$$;
CREATE FUNCTION menuto_nutrition.legacy_anchor(h uuid,m uuid) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE s jsonb:=menuto_nutrition.subject(h,m); p jsonb; b jsonb; BEGIN
 IF s IS NULL THEN RAISE EXCEPTION 'Canonical household/member missing'; END IF;
 SELECT jsonb_build_object('id',id,'household_id',household_id,'member_id',member_id,'row_version',row_version,
  'body_mass_kg',body_mass_kg::text,'height_cm',height_cm::text,'created_by_user_id',created_by_user_id,'created_at',menuto_nutrition.utc(created_at))
 INTO p FROM public.member_nutrition_profiles WHERE household_id=h AND member_id=m;
 b:=jsonb_build_object('subject',s,'profile',p);
 RETURN b||jsonb_build_object('body_fingerprint',menuto_nutrition.hash('nutrition.legacy-anchor.v1',b));
END $$;
CREATE FUNCTION menuto_nutrition.subject_witness(h uuid,m uuid,u uuid) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE s jsonb:=menuto_nutrition.subject(h,m); r record; BEGIN
 IF s IS NULL THEN RAISE EXCEPTION 'Canonical household/member missing'; END IF;
 SELECT id,member_id,role INTO r FROM public.memberships WHERE household_id=h AND user_id=u;
 RETURN jsonb_build_object('subject',s,'actor_user_id',u,'membership_id',r.id,'actor_member_id',r.member_id,'role',r.role);
END $$;
CREATE FUNCTION menuto_nutrition.ensure_stream(k text,t text,i jsonb) RETURNS void LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$ BEGIN
 INSERT INTO public.nutrition_source_streams(stream_key,kind,identity,revision,head_id,head_hash) VALUES(k,t,i,0,NULL,NULL) ON CONFLICT DO NOTHING;
 IF NOT EXISTS (SELECT FROM public.nutrition_source_streams WHERE stream_key=k AND kind=t AND identity=i) THEN RAISE EXCEPTION 'Conflicting immutable stream identity'; END IF;
END $$;
CREATE FUNCTION menuto_nutrition.lock_sources(p uuid,h uuid,m uuid) RETURNS void LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE k text; BEGIN
 IF p IS NOT NULL THEN
  k:=menuto_nutrition.hash('nutrition.provider-lock.v1',jsonb_build_object('provider_id',p));
  PERFORM 1 FROM public.nutrition_source_streams WHERE stream_key=k AND kind='LOCK' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Unknown explicit provider'; END IF;
 END IF;
 IF m IS NOT NULL THEN
  k:=menuto_nutrition.hash('nutrition.member-lock.v1',menuto_nutrition.subject(h,m));
  PERFORM 1 FROM public.nutrition_source_streams WHERE stream_key=k AND kind='LOCK' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Member source not provisioned'; END IF;
 END IF;
END $$;
CREATE FUNCTION menuto_nutrition.principal(s jsonb) RETURNS uuid LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE p uuid; BEGIN
 SELECT id INTO p FROM public.nutrition_source_principals WHERE database_oid=(s->>'database_oid')::bigint
  AND database_name=s->>'database_name' AND role_oid=(s->>'role_oid')::bigint AND role_name=s->>'role_name';
 IF p IS NULL THEN RAISE EXCEPTION 'Actual Nutrition principal is not enrolled' USING ERRCODE='42501'; END IF; RETURN p;
END $$;
CREATE FUNCTION menuto_nutrition.provider(p uuid,s jsonb) RETURNS uuid LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE r record; BEGIN
 SELECT * INTO r FROM public.nutrition_source_providers WHERE provider_id=p ORDER BY generation DESC LIMIT 1;
 IF r.id IS NULL OR r.database_oid<>(s->>'database_oid')::bigint OR r.database_name<>s->>'database_name' THEN
  RAISE EXCEPTION 'Actual provider database binding differs; explicit re-enrollment required' USING ERRCODE='42501'; END IF;
 RETURN r.id;
END $$;
CREATE FUNCTION menuto_nutrition.permission(p uuid,s jsonb,cap text,protocol text,fact text,t timestamptz,ceiling bigint DEFAULT NULL) RETURNS uuid LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE found_grant record; BEGIN
 SELECT a.*,hdr.sequence INTO found_grant FROM public.nutrition_source_authority a JOIN public.nutrition_source_receipts hdr ON hdr.id=a.id
 WHERE a.principal_id=p AND a.body->'scope'=s AND a.capability=cap
  AND a.protocol_fingerprint IS NOT DISTINCT FROM protocol AND a.fact_key IS NOT DISTINCT FROM fact
  AND a.effective_from<=t AND (ceiling IS NULL OR hdr.sequence<=ceiling)
 ORDER BY hdr.sequence DESC LIMIT 1;
 IF found_grant.id IS NULL OR found_grant.action<>'GRANT' OR t>=found_grant.effective_until THEN
  RAISE EXCEPTION 'Nutrition capability denied' USING ERRCODE='42501';
 END IF; RETURN found_grant.id;
END $$;

CREATE FUNCTION menuto_nutrition.validate_json(j jsonb,s jsonb,root jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE t text; x record; option jsonb; ok boolean:=false; n numeric; BEGIN
 IF s ? '$ref' THEN PERFORM menuto_nutrition.validate_json(j,root->'$defs'->split_part(s->>'$ref','/',3),root); RETURN; END IF;
 IF s ? 'anyOf' THEN
  FOR option IN SELECT value FROM jsonb_array_elements(s->'anyOf') LOOP
   BEGIN PERFORM menuto_nutrition.validate_json(j,option,root); ok:=true; EXCEPTION WHEN raise_exception THEN NULL; END;
   EXIT WHEN ok;
  END LOOP;
  IF NOT ok THEN RAISE EXCEPTION 'Closed union contract mismatch'; END IF; RETURN;
 END IF;
 IF s ? 'oneOf' THEN
  FOR option IN SELECT value FROM jsonb_array_elements(s->'oneOf') LOOP
   BEGIN PERFORM menuto_nutrition.validate_json(j,option,root); ok:=true; EXCEPTION WHEN raise_exception THEN NULL; END;
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
  FOR x IN SELECT key,value FROM jsonb_each(j) LOOP PERFORM menuto_nutrition.validate_json(x.value,s->'properties'->x.key,root); END LOOP;
 ELSIF t='array' THEN
  IF (s ? 'minItems' AND jsonb_array_length(j)<(s->>'minItems')::int) OR (s ? 'maxItems' AND jsonb_array_length(j)>(s->>'maxItems')::int) THEN RAISE EXCEPTION 'Array bound'; END IF;
  FOR x IN SELECT value,ordinality FROM jsonb_array_elements(j) WITH ORDINALITY LOOP
   PERFORM menuto_nutrition.validate_json(x.value,coalesce(s->'prefixItems'->(x.ordinality::int-1),s->'items'),root);
  END LOOP;
 ELSIF t='string' THEN
  IF (s ? 'minLength' AND length(j#>>'{}')<(s->>'minLength')::int) OR (s ? 'maxLength' AND length(j#>>'{}')>(s->>'maxLength')::int) OR (s ? 'pattern' AND (j#>>'{}') !~ (s->>'pattern')) THEN RAISE EXCEPTION 'String contract bound'; END IF;
  IF s->>'format'='uuid' THEN PERFORM menuto_nutrition.uuid(j); END IF;
  IF s->>'format'='date-time' THEN
   IF NOT isfinite((j#>>'{}')::timestamptz) OR menuto_nutrition.utc((j#>>'{}')::timestamptz)<>j#>>'{}' THEN RAISE EXCEPTION 'Canonical finite UTC time required'; END IF;
  END IF;
 END IF;
END $$;
CREATE FUNCTION menuto_nutrition.command_schema(n text) RETURNS jsonb LANGUAGE sql IMMUTABLE SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $schemas$ SELECT ('{"NutritionAuthorityCommand": {"$defs": {"NutritionAuthorityScope": {"additionalProperties": false, "properties": {"family_id": {"anyOf": [{"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, {"type": "null"}], "title": "Family Id"}, "household_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Household Id"}, "member_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Member Id"}, "provider_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Provider Id"}}, "required": ["provider_id", "family_id", "household_id", "member_id"], "title": "NutritionAuthorityScope", "type": "object"}, "NutritionSourceEvidence": {"additionalProperties": false, "properties": {"body": {"maxLength": 16384, "minLength": 1, "title": "Body", "type": "string"}, "body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Evidence Id", "type": "string"}, "purpose": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Purpose", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["evidence_id", "version", "environment", "purpose", "body", "body_fingerprint"], "title": "NutritionSourceEvidence", "type": "object"}, "NutritionSourceInterval": {"additionalProperties": false, "properties": {"end": {"format": "date-time", "title": "End", "type": "string"}, "start": {"format": "date-time", "title": "Start", "type": "string"}}, "required": ["start", "end"], "title": "NutritionSourceInterval", "type": "object"}}, "additionalProperties": false, "properties": {"action": {"enum": ["GRANT", "REVOKE"], "title": "Action", "type": "string"}, "capability": {"enum": ["GUIDELINE_REVIEW", "GUIDELINE_PUBLISH", "GUIDELINE_WITHDRAW", "ELIGIBILITY_ATTEST", "MEMBER_OBSERVATION_WRITE", "MEMBER_GOAL_WRITE", "ROOT_SOURCE_READ", "VALIDATOR_SOURCE_READ"], "title": "Capability", "type": "string"}, "effective": {"$ref": "#/$defs/NutritionSourceInterval"}, "expected_generation": {"maximum": 9223372036854775807, "minimum": 0, "title": "Expected Generation", "type": "integer"}, "fact_key": {"anyOf": [{"enum": ["BODY_MASS", "HEIGHT"], "type": "string"}, {"type": "null"}], "title": "Fact Key"}, "idempotency_key": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Idempotency Key", "type": "string"}, "predecessor_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Predecessor Id"}, "principal_id": {"format": "uuid", "title": "Principal Id", "type": "string"}, "protocol_fingerprint": {"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "title": "Protocol Fingerprint"}, "qualification_evidence": {"$ref": "#/$defs/NutritionSourceEvidence"}, "scope": {"$ref": "#/$defs/NutritionAuthorityScope"}}, "required": ["principal_id", "scope", "capability", "protocol_fingerprint", "fact_key", "action", "effective", "qualification_evidence", "expected_generation", "predecessor_id", "idempotency_key"], "title": "NutritionAuthorityCommand", "type": "object"}, "NutritionPrincipalEnrollment": {"$defs": {"NutritionSourceEvidence": {"additionalProperties": false, "properties": {"body": {"maxLength": 16384, "minLength": 1, "title": "Body", "type": "string"}, "body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Evidence Id", "type": "string"}, "purpose": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Purpose", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["evidence_id", "version", "environment", "purpose", "body", "body_fingerprint"], "title": "NutritionSourceEvidence", "type": "object"}}, "additionalProperties": false, "properties": {"delegation_registrar": {"title": "Delegation Registrar", "type": "boolean"}, "idempotency_key": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Idempotency Key", "type": "string"}, "identity_evidence": {"$ref": "#/$defs/NutritionSourceEvidence"}, "role_name": {"maxLength": 63, "minLength": 1, "pattern": "^[^\\x00-\\x1f\\x7f]+$", "title": "Role Name", "type": "string"}, "service_id": {"anyOf": [{"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, {"type": "null"}], "title": "Service Id"}, "user_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "User Id"}, "verified_human_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Verified Human Id"}}, "required": ["role_name", "verified_human_id", "user_id", "service_id", "delegation_registrar", "identity_evidence", "idempotency_key"], "title": "NutritionPrincipalEnrollment", "type": "object"}, "NutritionProviderEnrollment": {"$defs": {"NutritionSourceEvidence": {"additionalProperties": false, "properties": {"body": {"maxLength": 16384, "minLength": 1, "title": "Body", "type": "string"}, "body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Evidence Id", "type": "string"}, "purpose": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Purpose", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["evidence_id", "version", "environment", "purpose", "body", "body_fingerprint"], "title": "NutritionSourceEvidence", "type": "object"}}, "additionalProperties": false, "properties": {"authority_evidence": {"$ref": "#/$defs/NutritionSourceEvidence"}, "code": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Code", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "expected_generation": {"maximum": 9223372036854775807, "minimum": 0, "title": "Expected Generation", "type": "integer"}, "idempotency_key": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Idempotency Key", "type": "string"}, "previous_enrollment_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Previous Enrollment Id"}, "provider_id": {"format": "uuid", "title": "Provider Id", "type": "string"}, "remit": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Remit", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["provider_id", "code", "version", "remit", "environment", "authority_evidence", "expected_generation", "previous_enrollment_id", "idempotency_key"], "title": "NutritionProviderEnrollment", "type": "object"}, "NutritionRootRequest": {"$defs": {"HouseholdMemberIdentity": {"additionalProperties": false, "properties": {"contract_version": {"const": "household-member-identity.v1", "default": "household-member-identity.v1", "title": "Contract Version", "type": "string"}, "household_id": {"format": "uuid", "title": "Household Id", "type": "string"}, "member_id": {"format": "uuid", "title": "Member Id", "type": "string"}}, "required": ["household_id", "member_id"], "title": "HouseholdMemberIdentity", "type": "object"}, "NutritionSourceInterval": {"additionalProperties": false, "properties": {"end": {"format": "date-time", "title": "End", "type": "string"}, "start": {"format": "date-time", "title": "Start", "type": "string"}}, "required": ["start", "end"], "title": "NutritionSourceInterval", "type": "object"}, "NutritionTemporalScope": {"additionalProperties": false, "properties": {"calendar": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Calendar", "type": "string"}, "interval": {"$ref": "#/$defs/NutritionSourceInterval"}, "kind": {"enum": ["EXACT_INTERVAL", "DAY", "WEEK"], "title": "Kind", "type": "string"}, "period_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Period Id", "type": "string"}, "timezone": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Timezone", "type": "string"}}, "required": ["kind", "period_id", "calendar", "timezone", "interval"], "title": "NutritionTemporalScope", "type": "object"}}, "additionalProperties": false, "properties": {"contract_version": {"const": "nutrition-root-request.v1", "default": "nutrition-root-request.v1", "title": "Contract Version", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "family_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Family Id", "type": "string"}, "goal_type": {"const": "ENERGY_DIRECTION", "title": "Goal Type", "type": "string"}, "guideline_body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Guideline Body Fingerprint", "type": "string"}, "guideline_revision_id": {"format": "uuid", "title": "Guideline Revision Id", "type": "string"}, "protocol_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Protocol Fingerprint", "type": "string"}, "provider_id": {"format": "uuid", "title": "Provider Id", "type": "string"}, "purpose": {"enum": ["ROOT", "VALIDATOR"], "title": "Purpose", "type": "string"}, "scope_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Id", "type": "string"}, "scope_version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Version", "type": "string"}, "subject": {"$ref": "#/$defs/HouseholdMemberIdentity"}, "temporal": {"$ref": "#/$defs/NutritionTemporalScope"}}, "required": ["subject", "provider_id", "family_id", "guideline_revision_id", "guideline_body_fingerprint", "protocol_fingerprint", "scope_id", "scope_version", "temporal", "environment", "purpose", "goal_type"], "title": "NutritionRootRequest", "type": "object"}, "NutritionSourceCommand": {"$defs": {"NutritionDelegationRevision": {"additionalProperties": false, "properties": {"action": {"enum": ["GRANT", "REVOKE"], "title": "Action", "type": "string"}, "authorization_evidence": {"$ref": "#/$defs/NutritionSourceEvidence"}, "effective": {"$ref": "#/$defs/NutritionSourceInterval"}, "grantee_principal_id": {"format": "uuid", "title": "Grantee Principal Id", "type": "string"}, "kind": {"const": "DELEGATION", "title": "Kind", "type": "string"}, "operation_scope": {"enum": ["MEMBER_GOAL_WRITE", "BODY_MASS_WRITE", "HEIGHT_WRITE"], "title": "Operation Scope", "type": "string"}, "previous_grant_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Previous Grant Id"}}, "required": ["kind", "action", "grantee_principal_id", "operation_scope", "effective", "authorization_evidence", "previous_grant_id"], "title": "NutritionDelegationRevision", "type": "object"}, "NutritionEligibilityProtocol": {"additionalProperties": false, "properties": {"admitted": {"$ref": "#/$defs/NutritionEvidenceRequirements"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "excluded": {"$ref": "#/$defs/NutritionEvidenceRequirements"}, "meaning": {"$ref": "#/$defs/NutritionSourceEvidence"}, "out_of_scope": {"$ref": "#/$defs/NutritionEvidenceRequirements"}, "protocol_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Protocol Id", "type": "string"}, "scope_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Id", "type": "string"}, "scope_version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Version", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["protocol_id", "version", "scope_id", "scope_version", "environment", "meaning", "admitted", "excluded", "out_of_scope"], "title": "NutritionEligibilityProtocol", "type": "object"}, "NutritionEligibilityRevision": {"additionalProperties": false, "properties": {"effective": {"$ref": "#/$defs/NutritionSourceInterval"}, "evidence": {"items": {"$ref": "#/$defs/NutritionSourceEvidence"}, "maxItems": 32, "title": "Evidence", "type": "array"}, "guideline_body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Guideline Body Fingerprint", "type": "string"}, "guideline_revision_id": {"format": "uuid", "title": "Guideline Revision Id", "type": "string"}, "kind": {"const": "ASSESSMENT", "title": "Kind", "type": "string"}, "missing_evidence_slots": {"items": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, "maxItems": 32, "title": "Missing Evidence Slots", "type": "array"}, "missing_observations": {"items": {"enum": ["BODY_MASS", "HEIGHT"], "type": "string"}, "maxItems": 2, "title": "Missing Observations", "type": "array"}, "observations": {"items": {"$ref": "#/$defs/NutritionObservationReference"}, "maxItems": 2, "title": "Observations", "type": "array"}, "operation": {"enum": ["CREATE", "REPLACE", "CORRECT", "RETRACT"], "title": "Operation", "type": "string"}, "outcome": {"enum": ["ADMITTED", "OUT_OF_SCOPE", "EXCLUDED", "UNDETERMINED"], "title": "Outcome", "type": "string"}, "protocol_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Protocol Fingerprint", "type": "string"}, "replaces": {"items": {"format": "uuid", "type": "string"}, "maxItems": 64, "title": "Replaces", "type": "array"}}, "required": ["kind", "operation", "guideline_revision_id", "guideline_body_fingerprint", "protocol_fingerprint", "outcome", "observations", "evidence", "missing_observations", "missing_evidence_slots", "effective", "replaces"], "title": "NutritionEligibilityRevision", "type": "object"}, "NutritionEvidenceRequirements": {"additionalProperties": false, "properties": {"evidence_slots": {"items": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, "maxItems": 32, "minItems": 1, "title": "Evidence Slots", "type": "array"}, "observations": {"items": {"enum": ["BODY_MASS", "HEIGHT"], "type": "string"}, "maxItems": 2, "title": "Observations", "type": "array"}}, "required": ["observations", "evidence_slots"], "title": "NutritionEvidenceRequirements", "type": "object"}, "NutritionGoalRevision": {"additionalProperties": false, "properties": {"direction": {"anyOf": [{"enum": ["CUT", "MAINTAIN", "GAIN"], "type": "string"}, {"type": "null"}], "title": "Direction"}, "effective": {"$ref": "#/$defs/NutritionSourceInterval"}, "goal_id": {"format": "uuid", "title": "Goal Id", "type": "string"}, "goal_type": {"const": "ENERGY_DIRECTION", "title": "Goal Type", "type": "string"}, "kind": {"const": "GOAL", "title": "Kind", "type": "string"}, "operation": {"enum": ["CREATE", "REPLACE", "CORRECT", "RETRACT"], "title": "Operation", "type": "string"}, "provenance": {"$ref": "#/$defs/NutritionSourceEvidence"}, "replaces": {"items": {"format": "uuid", "type": "string"}, "maxItems": 64, "title": "Replaces", "type": "array"}}, "required": ["kind", "operation", "goal_id", "goal_type", "direction", "effective", "replaces", "provenance"], "title": "NutritionGoalRevision", "type": "object"}, "NutritionGuidelineBody": {"additionalProperties": false, "properties": {"clauses": {"items": {"$ref": "#/$defs/NutritionGuidelineClause"}, "maxItems": 16, "minItems": 1, "title": "Clauses", "type": "array"}, "contract_version": {"const": "nutrition-guideline-body.v1", "default": "nutrition-guideline-body.v1", "title": "Contract Version", "type": "string"}, "edition": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Edition", "type": "string"}, "effective": {"$ref": "#/$defs/NutritionSourceInterval"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence_manifest": {"items": {"$ref": "#/$defs/NutritionSourceEvidence"}, "maxItems": 32, "minItems": 1, "title": "Evidence Manifest", "type": "array"}, "family_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Family Id", "type": "string"}, "guideline_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Guideline Id", "type": "string"}, "guideline_version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Guideline Version", "type": "string"}, "jurisdiction": {"anyOf": [{"maxLength": 4000, "minLength": 1, "pattern": "\\S", "type": "string"}, {"type": "null"}], "title": "Jurisdiction"}, "jurisdiction_status": {"enum": ["REVIEWED_SPECIFIED", "SOURCE_NOT_SPECIFIED"], "title": "Jurisdiction Status", "type": "string"}, "mandatory_hard_roots": {"items": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, "maxItems": 16, "minItems": 1, "title": "Mandatory Hard Roots", "type": "array"}, "protocol": {"$ref": "#/$defs/NutritionEligibilityProtocol"}, "provider_id": {"format": "uuid", "title": "Provider Id", "type": "string"}, "revision_id": {"format": "uuid", "title": "Revision Id", "type": "string"}}, "required": ["revision_id", "provider_id", "family_id", "guideline_id", "guideline_version", "edition", "jurisdiction", "jurisdiction_status", "environment", "effective", "protocol", "evidence_manifest", "clauses", "mandatory_hard_roots"], "title": "NutritionGuidelineBody", "type": "object"}, "NutritionGuidelineClause": {"additionalProperties": false, "properties": {"constraint": {"discriminator": {"mapping": {"MAXIMUM": "#/$defs/NutritionMaximum", "MINIMUM": "#/$defs/NutritionMinimum", "RANGE": "#/$defs/NutritionRange", "TARGET": "#/$defs/NutritionTarget"}, "propertyName": "kind"}, "oneOf": [{"$ref": "#/$defs/NutritionRange"}, {"$ref": "#/$defs/NutritionMinimum"}, {"$ref": "#/$defs/NutritionMaximum"}, {"$ref": "#/$defs/NutritionTarget"}], "title": "Constraint"}, "descriptor": {"$ref": "#/$defs/NutritionRootDescriptor"}, "interpretation": {"enum": ["GUIDELINE_HARD", "REFERENCE_CENTER"], "title": "Interpretation", "type": "string"}, "root_key": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Root Key", "type": "string"}}, "required": ["root_key", "descriptor", "interpretation", "constraint"], "title": "NutritionGuidelineClause", "type": "object"}, "NutritionGuidelineDraft": {"additionalProperties": false, "properties": {"guideline": {"$ref": "#/$defs/NutritionGuidelineBody"}, "kind": {"const": "DRAFT", "title": "Kind", "type": "string"}}, "required": ["kind", "guideline"], "title": "NutritionGuidelineDraft", "type": "object"}, "NutritionGuidelinePublication": {"additionalProperties": false, "properties": {"action": {"enum": ["PUBLISH", "SUPERSEDE", "RETIRE", "RETRACT"], "title": "Action", "type": "string"}, "body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "draft_revision_id": {"format": "uuid", "title": "Draft Revision Id", "type": "string"}, "effective_at": {"format": "date-time", "title": "Effective At", "type": "string"}, "kind": {"const": "PUBLICATION", "title": "Kind", "type": "string"}, "prior_publication_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Prior Publication Id"}, "rationale": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Rationale", "type": "string"}, "review_event_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Review Event Id"}}, "required": ["kind", "action", "draft_revision_id", "body_fingerprint", "review_event_id", "prior_publication_id", "effective_at", "rationale"], "title": "NutritionGuidelinePublication", "type": "object"}, "NutritionGuidelineReview": {"additionalProperties": false, "properties": {"body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "decision": {"enum": ["APPROVE", "CANCEL"], "title": "Decision", "type": "string"}, "draft_revision_id": {"format": "uuid", "title": "Draft Revision Id", "type": "string"}, "evidence_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Evidence Fingerprint", "type": "string"}, "kind": {"const": "REVIEW", "title": "Kind", "type": "string"}, "prior_review_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Prior Review Id"}, "protocol_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Protocol Fingerprint", "type": "string"}, "rationale": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Rationale", "type": "string"}}, "required": ["kind", "draft_revision_id", "body_fingerprint", "evidence_fingerprint", "protocol_fingerprint", "decision", "prior_review_id", "rationale"], "title": "NutritionGuidelineReview", "type": "object"}, "NutritionMaximum": {"additionalProperties": false, "properties": {"kind": {"const": "MAXIMUM", "title": "Kind", "type": "string"}, "upper": {"$ref": "#/$defs/NutritionRootAmount"}}, "required": ["kind", "upper"], "title": "NutritionMaximum", "type": "object"}, "NutritionMinimum": {"additionalProperties": false, "properties": {"kind": {"const": "MINIMUM", "title": "Kind", "type": "string"}, "lower": {"$ref": "#/$defs/NutritionRootAmount"}}, "required": ["kind", "lower"], "title": "NutritionMinimum", "type": "object"}, "NutritionObservationReference": {"additionalProperties": false, "properties": {"fact_hash": {"pattern": "^[a-f0-9]{64}$", "title": "Fact Hash", "type": "string"}, "fact_key": {"enum": ["BODY_MASS", "HEIGHT"], "title": "Fact Key", "type": "string"}, "legacy_anchor_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Legacy Anchor Fingerprint", "type": "string"}, "revision_id": {"format": "uuid", "title": "Revision Id", "type": "string"}, "unit": {"enum": ["KG", "CM"], "title": "Unit", "type": "string"}, "value": {"$ref": "#/$defs/NutritionRootAmount"}}, "required": ["fact_key", "revision_id", "fact_hash", "value", "unit", "legacy_anchor_fingerprint"], "title": "NutritionObservationReference", "type": "object"}, "NutritionObservationRevision": {"additionalProperties": false, "properties": {"effective": {"$ref": "#/$defs/NutritionSourceInterval"}, "fact_key": {"enum": ["BODY_MASS", "HEIGHT"], "title": "Fact Key", "type": "string"}, "kind": {"const": "OBSERVATION", "title": "Kind", "type": "string"}, "observed_at": {"format": "date-time", "title": "Observed At", "type": "string"}, "operation": {"enum": ["CREATE", "REPLACE", "CORRECT", "RETRACT"], "title": "Operation", "type": "string"}, "provenance": {"$ref": "#/$defs/NutritionSourceEvidence"}, "replaces": {"items": {"format": "uuid", "type": "string"}, "maxItems": 64, "title": "Replaces", "type": "array"}, "unit": {"enum": ["KG", "CM"], "title": "Unit", "type": "string"}, "value": {"anyOf": [{"$ref": "#/$defs/NutritionRootAmount"}, {"type": "null"}]}}, "required": ["kind", "operation", "fact_key", "value", "unit", "observed_at", "provenance", "effective", "replaces"], "title": "NutritionObservationRevision", "type": "object"}, "NutritionRange": {"additionalProperties": false, "properties": {"kind": {"const": "RANGE", "title": "Kind", "type": "string"}, "lower": {"$ref": "#/$defs/NutritionRootAmount"}, "upper": {"$ref": "#/$defs/NutritionRootAmount"}}, "required": ["kind", "lower", "upper"], "title": "NutritionRange", "type": "object"}, "NutritionRootAmount": {"additionalProperties": false, "properties": {"denominator": {"exclusiveMinimum": 0, "maximum": 170141183460469231731687303715884105727, "title": "Denominator", "type": "integer"}, "numerator": {"maximum": 170141183460469231731687303715884105727, "minimum": 0, "title": "Numerator", "type": "integer"}}, "required": ["numerator", "denominator"], "title": "NutritionRootAmount", "type": "object"}, "NutritionRootDescriptor": {"additionalProperties": false, "properties": {"metric": {"enum": ["ENERGY", "PROTEIN", "FAT", "CARBOHYDRATE"], "title": "Metric", "type": "string"}, "protocol_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Protocol Fingerprint", "type": "string"}, "scope_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Id", "type": "string"}, "scope_version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Scope Version", "type": "string"}, "temporal": {"$ref": "#/$defs/NutritionTemporalScope"}, "unit": {"enum": ["KCAL", "G"], "title": "Unit", "type": "string"}}, "required": ["metric", "unit", "scope_id", "scope_version", "protocol_fingerprint", "temporal"], "title": "NutritionRootDescriptor", "type": "object"}, "NutritionSourceEvidence": {"additionalProperties": false, "properties": {"body": {"maxLength": 16384, "minLength": 1, "title": "Body", "type": "string"}, "body_fingerprint": {"pattern": "^[a-f0-9]{64}$", "title": "Body Fingerprint", "type": "string"}, "environment": {"enum": ["TEST_ONLY", "REVIEWED_PRODUCTION"], "title": "Environment", "type": "string"}, "evidence_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Evidence Id", "type": "string"}, "purpose": {"maxLength": 4000, "minLength": 1, "pattern": "\\S", "title": "Purpose", "type": "string"}, "version": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Version", "type": "string"}}, "required": ["evidence_id", "version", "environment", "purpose", "body", "body_fingerprint"], "title": "NutritionSourceEvidence", "type": "object"}, "NutritionSourceInterval": {"additionalProperties": false, "properties": {"end": {"format": "date-time", "title": "End", "type": "string"}, "start": {"format": "date-time", "title": "Start", "type": "string"}}, "required": ["start", "end"], "title": "NutritionSourceInterval", "type": "object"}, "NutritionStreamIdentity": {"additionalProperties": false, "properties": {"code": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Code", "type": "string"}, "family_id": {"anyOf": [{"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "type": "string"}, {"type": "null"}], "title": "Family Id"}, "household_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Household Id"}, "kind": {"enum": ["GUIDELINE", "OBSERVATION", "GOAL", "ASSESSMENT", "DELEGATION"], "title": "Kind", "type": "string"}, "member_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Member Id"}, "provider_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Provider Id"}}, "required": ["kind", "provider_id", "family_id", "household_id", "member_id", "code"], "title": "NutritionStreamIdentity", "type": "object"}, "NutritionTarget": {"additionalProperties": false, "properties": {"center": {"$ref": "#/$defs/NutritionRootAmount"}, "kind": {"const": "TARGET", "title": "Kind", "type": "string"}}, "required": ["kind", "center"], "title": "NutritionTarget", "type": "object"}, "NutritionTemporalScope": {"additionalProperties": false, "properties": {"calendar": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Calendar", "type": "string"}, "interval": {"$ref": "#/$defs/NutritionSourceInterval"}, "kind": {"enum": ["EXACT_INTERVAL", "DAY", "WEEK"], "title": "Kind", "type": "string"}, "period_id": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Period Id", "type": "string"}, "timezone": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Timezone", "type": "string"}}, "required": ["kind", "period_id", "calendar", "timezone", "interval"], "title": "NutritionTemporalScope", "type": "object"}}, "additionalProperties": false, "properties": {"body": {"discriminator": {"mapping": {"ASSESSMENT": "#/$defs/NutritionEligibilityRevision", "DELEGATION": "#/$defs/NutritionDelegationRevision", "DRAFT": "#/$defs/NutritionGuidelineDraft", "GOAL": "#/$defs/NutritionGoalRevision", "OBSERVATION": "#/$defs/NutritionObservationRevision", "PUBLICATION": "#/$defs/NutritionGuidelinePublication", "REVIEW": "#/$defs/NutritionGuidelineReview"}, "propertyName": "kind"}, "oneOf": [{"$ref": "#/$defs/NutritionGuidelineDraft"}, {"$ref": "#/$defs/NutritionGuidelineReview"}, {"$ref": "#/$defs/NutritionGuidelinePublication"}, {"$ref": "#/$defs/NutritionObservationRevision"}, {"$ref": "#/$defs/NutritionEligibilityRevision"}, {"$ref": "#/$defs/NutritionGoalRevision"}, {"$ref": "#/$defs/NutritionDelegationRevision"}], "title": "Body"}, "contract_version": {"const": "nutrition-source-command.v1", "default": "nutrition-source-command.v1", "title": "Contract Version", "type": "string"}, "expected_revision": {"maximum": 9223372036854775807, "minimum": 0, "title": "Expected Revision", "type": "integer"}, "idempotency_key": {"maxLength": 100, "minLength": 1, "pattern": "^[A-Za-z0-9_.:-]+$", "title": "Idempotency Key", "type": "string"}, "identity": {"$ref": "#/$defs/NutritionStreamIdentity"}, "predecessor_id": {"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Predecessor Id"}, "revision_id": {"format": "uuid", "title": "Revision Id", "type": "string"}}, "required": ["revision_id", "identity", "body", "expected_revision", "predecessor_id", "idempotency_key"], "title": "NutritionSourceCommand", "type": "object"}}'::jsonb)->n $schemas$;
CREATE FUNCTION menuto_nutrition.check_command(n text,j jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$ DECLARE s jsonb:=menuto_nutrition.command_schema(n); BEGIN PERFORM menuto_nutrition.bounds(j,131072); IF s IS NULL THEN RAISE EXCEPTION 'Unknown command contract'; END IF; PERFORM menuto_nutrition.validate_json(j,s,s); END $$;

CREATE FUNCTION menuto_nutrition.provider_fact(d jsonb) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
 SELECT jsonb_build_object('id',d->'id','command',d->'command','generation',d->'generation',
  'administrator',d->'administrator','recorded_at',menuto_nutrition.utc((d->>'recorded_at')::timestamptz),'command_hash',d->'command_hash')
$$;
CREATE FUNCTION menuto_nutrition.principal_fact(d jsonb) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
 SELECT jsonb_build_object('id',d->'id','command',d->'command','database_oid',d->'database_oid',
  'database_name',d->'database_name','role_oid',d->'role_oid','administrator',d->'administrator',
  'recorded_at',menuto_nutrition.utc((d->>'recorded_at')::timestamptz),'command_hash',d->'command_hash')
$$;
CREATE FUNCTION menuto_nutrition.record_body(r public.nutrition_source_receipts) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE b jsonb; BEGIN
 CASE r.kind
 WHEN 'AUTHORITY' THEN SELECT body INTO b FROM public.nutrition_source_authority WHERE id=r.id;
 WHEN 'DRAFT' THEN SELECT body INTO b FROM public.nutrition_guideline_drafts WHERE id=r.id;
 WHEN 'REVIEW' THEN SELECT body INTO b FROM public.nutrition_guideline_reviews WHERE id=r.id;
 WHEN 'PUBLICATION' THEN SELECT body INTO b FROM public.nutrition_guideline_publications WHERE id=r.id;
 WHEN 'DELEGATION' THEN SELECT body INTO b FROM public.nutrition_member_delegations WHERE id=r.id;
 WHEN 'OBSERVATION' THEN SELECT body INTO b FROM public.nutrition_physiology_revisions WHERE id=r.id;
 WHEN 'ASSESSMENT' THEN SELECT body INTO b FROM public.nutrition_eligibility_revisions WHERE id=r.id;
 WHEN 'GOAL' THEN SELECT body INTO b FROM public.nutrition_goal_revisions WHERE id=r.id;
 ELSE RAISE EXCEPTION 'Unknown durable source class'; END CASE;
 IF b IS NULL THEN RAISE EXCEPTION 'Missing typed receipt child'; END IF; RETURN b;
END $$;
CREATE FUNCTION menuto_nutrition.record_fact(r public.nutrition_source_receipts) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE b jsonb:=menuto_nutrition.record_body(r); i jsonb; c jsonb; f jsonb; BEGIN
 SELECT identity INTO STRICT i FROM public.nutrition_source_streams WHERE stream_key=r.stream_key;
 IF r.kind='AUTHORITY' THEN
  RETURN jsonb_build_object('id',r.id,'recorded_order',r.recorded_order,'command',b,'stream_key',r.stream_key,'sequence',r.sequence,
   'previous_hash',r.previous_hash,'administrator',r.actor,'recorded_at',menuto_nutrition.utc(r.recorded_at),
   'command_hash',r.command_hash,'fact_hash',r.fact_hash);
 END IF;
 c:=jsonb_build_object('contract_version','nutrition-source-command.v1','revision_id',r.id,'identity',i,
  'body',b,'expected_revision',r.sequence-1,'predecessor_id',r.previous_id,'idempotency_key',r.idempotency_key);
 f:=jsonb_build_object('id',r.id,'recorded_order',r.recorded_order,'command',c,'stream_key',r.stream_key,'sequence',r.sequence,
  'previous_hash',r.previous_hash,'principal_id',r.principal_id,'grant_event_id',r.grant_event_id,
  'authority_generation',r.authority_generation,'provider_enrollment_id',r.provider_enrollment_id,
  'author',r.actor,'subject_witness',r.subject_witness,'delegation_event_id',r.delegation_event_id,
  'legacy_anchor',r.legacy_anchor,'recorded_at',menuto_nutrition.utc(r.recorded_at),
  'command_hash',r.command_hash,'fact_hash',r.fact_hash);
 RETURN f;
END $$;
CREATE FUNCTION menuto_nutrition.receipt(id uuid) RETURNS jsonb LANGUAGE sql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
 SELECT menuto_nutrition.record_fact(r) FROM public.nutrition_source_receipts r WHERE r.id=$1
$$;
CREATE FUNCTION menuto_nutrition.check_evidence_tree(j jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE x jsonb; BEGIN
 IF jsonb_typeof(j)='object' THEN
  IF j ? 'evidence_id' THEN PERFORM menuto_nutrition.evidence(j); END IF;
  IF j ? 'numerator' AND j ? 'denominator' THEN PERFORM menuto_nutrition.amount(j); END IF;
  IF (SELECT array_agg(key ORDER BY key) FROM jsonb_each(j))=ARRAY['end','start'] THEN
   PERFORM menuto_nutrition.interval_ok(j);
  END IF;
  FOR x IN SELECT value FROM jsonb_each(j) LOOP PERFORM menuto_nutrition.check_evidence_tree(x); END LOOP;
 ELSIF jsonb_typeof(j)='array' THEN
  FOR x IN SELECT value FROM jsonb_array_elements(j) LOOP PERFORM menuto_nutrition.check_evidence_tree(x); END LOOP;
 END IF;
END $$;
CREATE FUNCTION menuto_nutrition.register_provider(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_nutrition,pg_temp SET lock_timeout='1s' AS $$
DECLARE t timestamptz:=clock_timestamp(); s jsonb:=menuto_nutrition.session_fact(true); p uuid; new_provider_enrollment uuid;
 old public.nutrition_source_providers; retry public.nutrition_source_providers; h text; BEGIN
 PERFORM menuto_nutrition.check_command('NutritionProviderEnrollment',c);
 PERFORM menuto_nutrition.check_evidence_tree(c);
 IF c->>'environment'<>c#>>'{authority_evidence,environment}' THEN RAISE EXCEPTION 'Provider authority environment mismatch'; END IF;
 p:=(c->>'provider_id')::uuid;
 -- The immutable first enrollment is the lock anchor even after binding rotation/restore.
 PERFORM 1 FROM public.nutrition_source_providers WHERE id=p AND provider_id=p FOR UPDATE;
 IF FOUND THEN PERFORM menuto_nutrition.lock_sources(p,NULL,NULL); END IF;
 s:=menuto_nutrition.session_fact(true);
 h:=menuto_nutrition.hash('nutrition.provider-command.v1',c);
 SELECT * INTO retry FROM public.nutrition_source_providers WHERE database_oid=(s->>'database_oid')::bigint
  AND actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF FOUND THEN IF retry.command_hash<>h THEN RAISE EXCEPTION 'Provider idempotency conflict'; END IF;
  RETURN menuto_nutrition.provider_fact(to_jsonb(retry)); END IF;
 SELECT * INTO old FROM public.nutrition_source_providers WHERE provider_id=p ORDER BY generation DESC LIMIT 1;
 IF coalesce(old.generation,0)<>(c->>'expected_generation')::bigint OR old.id IS DISTINCT FROM (c->>'previous_enrollment_id')::uuid THEN
  RAISE EXCEPTION 'Provider enrollment CAS conflict'; END IF;
 IF old.id IS NOT NULL AND (old.code<>c->>'code' OR old.version<>c->>'version' OR old.environment<>c->>'environment'
    OR old.command->>'remit'<>c->>'remit') THEN RAISE EXCEPTION 'Provider identity/remit immutable across binding rotation'; END IF;
 IF EXISTS (SELECT FROM public.nutrition_source_providers WHERE code=c->>'code' AND version=c->>'version' AND provider_id<>p) THEN
  RAISE EXCEPTION 'Conflicting canonical provider identity'; END IF;
 new_provider_enrollment:=CASE WHEN old.id IS NULL THEN p ELSE gen_random_uuid() END;
 INSERT INTO public.nutrition_source_providers VALUES(new_provider_enrollment,p,old.id,coalesce(old.generation,0)+1,
  (s->>'database_oid')::bigint,s->>'database_name',(s->>'role_oid')::bigint,c->>'code',c->>'version',c->>'environment',
  c,s,clock_timestamp(),h,c->>'idempotency_key');
 PERFORM menuto_nutrition.retain_evidence(c);
 PERFORM menuto_nutrition.ensure_stream(menuto_nutrition.hash('nutrition.provider-lock.v1',jsonb_build_object('provider_id',p)),
  'LOCK',jsonb_build_object('provider_id',p));
 UPDATE public.nutrition_source_streams SET revision=revision+1
  WHERE stream_key=menuto_nutrition.hash('nutrition.provider-lock.v1',jsonb_build_object('provider_id',p));
 PERFORM menuto_nutrition.deadline(t);
 SELECT * INTO STRICT old FROM public.nutrition_source_providers WHERE nutrition_source_providers.id=new_provider_enrollment;
 RETURN menuto_nutrition.provider_fact(to_jsonb(old));
END $$;
CREATE FUNCTION menuto_nutrition.enroll_principal(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_nutrition,pg_temp SET lock_timeout='1s' AS $$
DECLARE t timestamptz:=clock_timestamp(); s jsonb:=menuto_nutrition.session_fact(true); r record;
 old public.nutrition_source_principals; h text; new_principal_id uuid:=gen_random_uuid(); BEGIN
 PERFORM menuto_nutrition.check_command('NutritionPrincipalEnrollment',c);
 PERFORM menuto_nutrition.check_evidence_tree(c);
 IF (c->'verified_human_id'='null'::jsonb)=(c->'service_id'='null'::jsonb) OR
  (c->'service_id'<>'null'::jsonb AND (c->'user_id'<>'null'::jsonb OR c->>'delegation_registrar'='true')) THEN
  RAISE EXCEPTION 'Exactly one verified human or service identity required'; END IF;
 PERFORM menuto_nutrition.safe_role((c->>'role_name')::name,false);
 SELECT oid,rolname INTO STRICT r FROM pg_catalog.pg_roles WHERE rolname=c->>'role_name';
 h:=menuto_nutrition.hash('nutrition.principal-command.v1',c);
 SELECT * INTO old FROM public.nutrition_source_principals WHERE database_oid=(s->>'database_oid')::bigint
  AND actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF FOUND THEN IF old.command_hash<>h THEN RAISE EXCEPTION 'Principal idempotency conflict'; END IF;
  RETURN menuto_nutrition.principal_fact(to_jsonb(old)); END IF;
 IF EXISTS (SELECT FROM public.nutrition_source_principals WHERE database_oid=(s->>'database_oid')::bigint
   AND role_oid=r.oid AND role_name=r.rolname) THEN RAISE EXCEPTION 'Credential binding already enrolled'; END IF;
 INSERT INTO public.nutrition_source_principals VALUES(new_principal_id,(s->>'database_oid')::bigint,s->>'database_name',r.oid::bigint,r.rolname,
  (c->>'verified_human_id')::uuid,(c->>'user_id')::uuid,c->>'service_id',(c->>'delegation_registrar')::boolean,
  c,s,(s->>'role_oid')::bigint,clock_timestamp(),h,c->>'idempotency_key');
 PERFORM menuto_nutrition.retain_evidence(c);
 PERFORM menuto_nutrition.deadline(t);
 SELECT * INTO STRICT old FROM public.nutrition_source_principals WHERE nutrition_source_principals.id=new_principal_id;
 RETURN menuto_nutrition.principal_fact(to_jsonb(old));
END $$;
CREATE FUNCTION menuto_nutrition.check_authority(c jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE s jsonb:=c->'scope'; cap text:=c->>'capability'; BEGIN
 IF (s->'provider_id'='null'::jsonb)<>(s->'family_id'='null'::jsonb) OR
    (s->'household_id'='null'::jsonb)<>(s->'member_id'='null'::jsonb) OR
    (s->'provider_id'='null'::jsonb AND s->'member_id'='null'::jsonb) THEN RAISE EXCEPTION 'Exact authority scope required'; END IF;
 IF cap LIKE 'GUIDELINE_%' AND (s->'provider_id'='null'::jsonb OR s->'member_id'<>'null'::jsonb) THEN RAISE EXCEPTION 'Reference capability is not member authorship'; END IF;
 IF cap IN ('ELIGIBILITY_ATTEST','ROOT_SOURCE_READ','VALIDATOR_SOURCE_READ') AND
  (s->'provider_id'='null'::jsonb OR s->'member_id'='null'::jsonb) THEN RAISE EXCEPTION 'Exact reference/member scope required'; END IF;
 IF cap LIKE 'MEMBER_%' AND (s->'provider_id'<>'null'::jsonb OR s->'member_id'='null'::jsonb) THEN RAISE EXCEPTION 'Member capability is not publication authority'; END IF;
 IF (cap='ELIGIBILITY_ATTEST')<>(c->'protocol_fingerprint'<>'null'::jsonb) OR
    (cap='MEMBER_OBSERVATION_WRITE')<>(c->'fact_key'<>'null'::jsonb) THEN RAISE EXCEPTION 'Exact finite fact/protocol scope required'; END IF;
 IF ((c->>'expected_generation')::bigint=0)<>(c->'predecessor_id'='null'::jsonb) THEN RAISE EXCEPTION 'Authority CAS predecessor required'; END IF;
 PERFORM menuto_nutrition.check_evidence_tree(c);
END $$;
CREATE FUNCTION menuto_nutrition.change_authority(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_nutrition,pg_temp SET lock_timeout='1s' AS $$
DECLARE t timestamptz:=clock_timestamp(); s jsonb:=menuto_nutrition.session_fact(true); sc jsonb; k text; lock_key text;
 p public.nutrition_source_principals; f public.nutrition_source_streams; retry public.nutrition_source_receipts;
 r public.nutrition_source_receipts; h text; id uuid:=gen_random_uuid(); pid uuid; fact jsonb; BEGIN
 PERFORM menuto_nutrition.check_command('NutritionAuthorityCommand',c);
 PERFORM menuto_nutrition.check_authority(c); PERFORM menuto_nutrition.check_assessor_qualification(c); sc:=c->'scope';
 PERFORM menuto_nutrition.lock_sources((sc->>'provider_id')::uuid,NULL,NULL);
 IF sc->'member_id'<>'null'::jsonb THEN
  IF menuto_nutrition.subject((sc->>'household_id')::uuid,(sc->>'member_id')::uuid) IS NULL THEN RAISE EXCEPTION 'Canonical subject missing'; END IF;
  lock_key:=menuto_nutrition.hash('nutrition.member-lock.v1',menuto_nutrition.subject((sc->>'household_id')::uuid,(sc->>'member_id')::uuid));
  -- Admin initialization only. Ordinary source commands cannot provision new scope/lock rows.
  PERFORM menuto_nutrition.ensure_stream(lock_key,'LOCK',menuto_nutrition.subject((sc->>'household_id')::uuid,(sc->>'member_id')::uuid));
 END IF;
 PERFORM menuto_nutrition.lock_sources(NULL,(sc->>'household_id')::uuid,(sc->>'member_id')::uuid);
 s:=menuto_nutrition.session_fact(true);
 IF sc->'provider_id'<>'null'::jsonb THEN pid:=menuto_nutrition.provider((sc->>'provider_id')::uuid,s); END IF;
 SELECT * INTO STRICT p FROM public.nutrition_source_principals WHERE nutrition_source_principals.id=(c->>'principal_id')::uuid;
 IF c->>'action'='GRANT' THEN
  IF p.command#>>'{identity_evidence,environment}'<>c#>>'{qualification_evidence,environment}' THEN RAISE EXCEPTION 'Principal/grant environment mismatch'; END IF;
  PERFORM menuto_nutrition.safe_role(p.role_name::name,false);
  IF p.database_oid<>(s->>'database_oid')::bigint OR p.database_name<>s->>'database_name' OR
   NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE oid=p.role_oid AND rolname=p.role_name) THEN RAISE EXCEPTION 'Actual target enrollment binding stale'; END IF;
  IF (c->>'capability' LIKE 'GUIDELINE_%' OR c->>'capability'='ELIGIBILITY_ATTEST') AND p.verified_human_id IS NULL THEN RAISE EXCEPTION 'Verified human qualification required'; END IF;
 END IF;
 IF pid IS NOT NULL AND c#>>'{qualification_evidence,environment}'<>
   (SELECT environment FROM public.nutrition_source_providers WHERE nutrition_source_providers.id=pid) THEN RAISE EXCEPTION 'Authority/content environment mismatch'; END IF;
 k:=menuto_nutrition.authority_key(sc);
 PERFORM menuto_nutrition.ensure_stream(k,'AUTHORITY',menuto_nutrition.authority_group(sc));
 SELECT * INTO STRICT f FROM public.nutrition_source_streams WHERE stream_key=k FOR UPDATE;
 h:=menuto_nutrition.hash('nutrition.authority-command.v1',c);
 SELECT * INTO retry FROM public.nutrition_source_receipts WHERE actor_database_oid=(s->>'database_oid')::bigint
  AND actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF FOUND THEN IF retry.command_hash<>h OR retry.kind<>'AUTHORITY' THEN RAISE EXCEPTION 'Authority idempotency conflict'; END IF; RETURN menuto_nutrition.record_fact(retry); END IF;
 IF f.revision<>(c->>'expected_generation')::bigint OR f.head_id IS DISTINCT FROM (c->>'predecessor_id')::uuid THEN RAISE EXCEPTION 'Authority CAS conflict'; END IF;
 IF f.revision>=64 THEN RAISE EXCEPTION 'Server authority history-depth limit; no truncation'; END IF;
 r.id:=id; r.kind:='AUTHORITY'; r.recorded_order:=nextval('public.nutrition_source_recorded_order');
 r.stream_key:=k; r.sequence:=f.revision+1; r.previous_id:=f.head_id; r.previous_hash:=f.head_hash;
 r.authority_generation:=0; r.provider_enrollment_id:=pid; r.actor_database_oid:=(s->>'database_oid')::bigint;
 r.actor_role_oid:=(s->>'role_oid')::bigint; r.actor:=s; r.recorded_at:=clock_timestamp();
 r.idempotency_key:=c->>'idempotency_key'; r.command_hash:=h;
 fact:=jsonb_build_object('id',id,'recorded_order',r.recorded_order,'command',c,'stream_key',k,'sequence',r.sequence,'previous_hash',f.head_hash,
  'administrator',s,'recorded_at',menuto_nutrition.utc(r.recorded_at),'command_hash',h);
 r.fact_hash:=menuto_nutrition.hash('nutrition.authority.v1',fact);
 INSERT INTO public.nutrition_source_receipts SELECT r.*;
 INSERT INTO public.nutrition_source_authority VALUES(id,p.id,(sc->>'provider_id')::uuid,sc->>'family_id',
  (sc->>'household_id')::uuid,(sc->>'member_id')::uuid,c->>'capability',c->>'action',c->>'protocol_fingerprint',c->>'fact_key',
  (c#>>'{effective,start}')::timestamptz,(c#>>'{effective,end}')::timestamptz,c);
 UPDATE public.nutrition_source_streams SET revision=r.sequence,head_id=id,head_hash=r.fact_hash WHERE stream_key=k;
 PERFORM menuto_nutrition.retain_evidence(c);
 PERFORM menuto_nutrition.touch_sources((sc->>'provider_id')::uuid,(sc->>'household_id')::uuid,(sc->>'member_id')::uuid);
 PERFORM menuto_nutrition.deadline(t); RETURN menuto_nutrition.record_fact(r);
END $$;

CREATE FUNCTION menuto_nutrition.retain_evidence(j jsonb) RETURNS void LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE x jsonb; old jsonb; BEGIN
 IF jsonb_typeof(j)='object' THEN
  IF j ? 'evidence_id' THEN
   PERFORM menuto_nutrition.evidence(j);
   INSERT INTO public.nutrition_source_evidence_artifacts(environment,evidence_id,version,body_fingerprint,body)
    VALUES(j->>'environment',j->>'evidence_id',j->>'version',j->>'body_fingerprint',j) ON CONFLICT DO NOTHING;
   SELECT body INTO STRICT old FROM public.nutrition_source_evidence_artifacts
    WHERE environment=j->>'environment' AND evidence_id=j->>'evidence_id' AND version=j->>'version';
   IF old<>j THEN RAISE EXCEPTION 'Conflicting immutable evidence identity/version'; END IF;
  END IF;
  FOR x IN SELECT value FROM jsonb_each(j) LOOP PERFORM menuto_nutrition.retain_evidence(x); END LOOP;
 ELSIF jsonb_typeof(j)='array' THEN
  FOR x IN SELECT value FROM jsonb_array_elements(j) LOOP PERFORM menuto_nutrition.retain_evidence(x); END LOOP;
 END IF;
END $$;
CREATE FUNCTION menuto_nutrition.check_bundle(b jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE p jsonb:=b->'protocol'; ph text; c jsonb; d jsonb; lim jsonb; keys jsonb; hard jsonb; seen text[]:=ARRAY[]::text[]; k text; req jsonb; BEGIN
 PERFORM menuto_nutrition.check_evidence_tree(b);
 IF (b->'jurisdiction'<>'null'::jsonb)<>(b->>'jurisdiction_status'='REVIEWED_SPECIFIED') THEN RAISE EXCEPTION 'Explicit jurisdiction applicability required'; END IF;
 IF p->>'environment'<>b->>'environment' OR p#>>'{meaning,environment}'<>b->>'environment' THEN RAISE EXCEPTION 'Protocol evidence environment mismatch'; END IF;
 ph:=menuto_nutrition.hash('nutrition.protocol.v1',p);
 FOREACH k IN ARRAY ARRAY['admitted','excluded','out_of_scope'] LOOP
  req:=p->k;
  PERFORM menuto_nutrition.strict_sets(req->'observations');
  PERFORM menuto_nutrition.strict_sets(req->'evidence_slots');
 END LOOP;
 SELECT coalesce(jsonb_agg(value->'evidence_id' ORDER BY ord),'[]') INTO keys FROM jsonb_array_elements(b->'evidence_manifest') WITH ORDINALITY e(value,ord);
 PERFORM menuto_nutrition.strict_sets(keys);
 IF EXISTS (SELECT FROM jsonb_array_elements(b->'evidence_manifest') e WHERE e->>'environment'<>b->>'environment') THEN RAISE EXCEPTION 'Evidence environment mismatch'; END IF;
 SELECT coalesce(jsonb_agg(value->'root_key' ORDER BY ord),'[]') INTO keys FROM jsonb_array_elements(b->'clauses') WITH ORDINALITY e(value,ord);
 PERFORM menuto_nutrition.strict_sets(keys);
 SELECT coalesce(jsonb_agg(value->'root_key' ORDER BY ord),'[]') INTO hard FROM jsonb_array_elements(b->'clauses') WITH ORDINALITY e(value,ord) WHERE value->>'interpretation'='GUIDELINE_HARD';
 IF hard='[]'::jsonb OR hard<>b->'mandatory_hard_roots' THEN RAISE EXCEPTION 'Complete nonempty hard-root manifest required'; END IF;
 FOR c IN SELECT value FROM jsonb_array_elements(b->'clauses') LOOP
  d:=c->'descriptor'; lim:=c->'constraint';
  IF (d->>'metric'='ENERGY')<>(d->>'unit'='KCAL') OR d->>'scope_id'<>p->>'scope_id'
   OR d->>'scope_version'<>p->>'scope_version' OR d->>'protocol_fingerprint'<>ph THEN RAISE EXCEPTION 'Metric/unit/applicability/protocol mismatch'; END IF;
  IF NOT menuto_nutrition.covers(b->'effective',d#>'{temporal,interval}') THEN RAISE EXCEPTION 'Root temporal interval outside publication'; END IF;
  IF (lim->>'kind'='TARGET')<>(c->>'interpretation'='REFERENCE_CENTER') THEN RAISE EXCEPTION 'TARGET is not a hard interval'; END IF;
  IF lim->>'kind'='RANGE' AND (lim#>>'{lower,numerator}')::numeric*(lim#>>'{upper,denominator}')::numeric>
     (lim#>>'{upper,numerator}')::numeric*(lim#>>'{lower,denominator}')::numeric THEN RAISE EXCEPTION 'Reversed exact root range'; END IF;
  k:=(d->>'metric')||':'||menuto_nutrition.hash('nutrition.temporal.v1',d->'temporal')||':'||(c->>'interpretation');
  IF k=ANY(seen) THEN RAISE EXCEPTION 'Duplicate metric/temporal/role root'; END IF; seen:=array_append(seen,k);
 END LOOP;
END $$;
CREATE FUNCTION menuto_nutrition.check_source_command(c jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE i jsonb:=c->'identity'; b jsonb:=c->'body'; k text:=b->>'kind'; expected_kind text; ids jsonb; BEGIN
 PERFORM menuto_nutrition.check_evidence_tree(c);
 expected_kind:=CASE WHEN k IN ('DRAFT','REVIEW','PUBLICATION') THEN 'GUIDELINE' ELSE k END;
 IF i->>'kind'<>expected_kind OR (i->'provider_id'='null'::jsonb)<>(i->'family_id'='null'::jsonb)
  OR (i->'household_id'='null'::jsonb)<>(i->'member_id'='null'::jsonb) THEN RAISE EXCEPTION 'Typed source identity mismatch'; END IF;
 IF expected_kind='GUIDELINE' THEN
  IF i->'provider_id'='null'::jsonb OR i->'member_id'<>'null'::jsonb OR i->>'code'<>'FAMILY' THEN RAISE EXCEPTION 'Exact reference family required'; END IF;
 ELSE
  IF i->'member_id'='null'::jsonb OR (expected_kind='ASSESSMENT')<>(i->'provider_id'<>'null'::jsonb) THEN RAISE EXCEPTION 'Member and global reference authorities differ'; END IF;
 END IF;
 IF ((c->>'expected_revision')::bigint=0)<>(c->'predecessor_id'='null'::jsonb) THEN RAISE EXCEPTION 'Exact source predecessor required'; END IF;
 IF k='DRAFT' THEN
  IF b#>>'{guideline,revision_id}'<>c->>'revision_id' OR b#>>'{guideline,provider_id}'<>i->>'provider_id'
    OR b#>>'{guideline,family_id}'<>i->>'family_id' THEN RAISE EXCEPTION 'Draft immutable identity mismatch'; END IF;
  PERFORM menuto_nutrition.check_bundle(b->'guideline');
 ELSIF k='REVIEW' THEN
  IF (b->>'decision'='CANCEL')<>(b->'prior_review_id'<>'null'::jsonb) THEN RAISE EXCEPTION 'Exact review cancellation lineage required'; END IF;
 ELSIF k='PUBLICATION' THEN
  IF (b->>'action' IN ('PUBLISH','SUPERSEDE'))<>(b->'review_event_id'<>'null'::jsonb)
   OR (b->>'action'='PUBLISH')<>(b->'prior_publication_id'='null'::jsonb) THEN RAISE EXCEPTION 'Finite publication/withdrawal lineage required'; END IF;
 ELSIF k='OBSERVATION' THEN
  IF i->>'code'<>b->>'fact_key' OR (b->>'fact_key'='BODY_MASS')<>(b->>'unit'='KG')
   OR (b->>'operation'='RETRACT')<>(b->'value'='null'::jsonb)
   OR (b->'value'<>'null'::jsonb AND (b#>>'{value,numerator}')::numeric=0)
   OR (b->>'observed_at')::timestamptz>(b#>>'{effective,start}')::timestamptz THEN RAISE EXCEPTION 'Physiological observation shape/unit/time mismatch'; END IF;
 ELSIF k='GOAL' THEN
  IF i->>'code'<>'ENERGY_DIRECTION' OR b->>'goal_type'<>'ENERGY_DIRECTION'
   OR (b->>'operation'='RETRACT')<>(b->'direction'='null'::jsonb) THEN RAISE EXCEPTION 'Goal direction is intent only; no default'; END IF;
 ELSIF k='ASSESSMENT' THEN
  IF i->>'code'<>b->>'protocol_fingerprint' THEN RAISE EXCEPTION 'Exact assessment protocol stream required'; END IF;
  SELECT coalesce(jsonb_agg(value->'fact_key' ORDER BY ord),'[]') INTO ids FROM jsonb_array_elements(b->'observations') WITH ORDINALITY e(value,ord); PERFORM menuto_nutrition.strict_sets(ids);
  SELECT coalesce(jsonb_agg(value->'evidence_id' ORDER BY ord),'[]') INTO ids FROM jsonb_array_elements(b->'evidence') WITH ORDINALITY e(value,ord); PERFORM menuto_nutrition.strict_sets(ids);
  PERFORM menuto_nutrition.strict_sets(b->'missing_observations'); PERFORM menuto_nutrition.strict_sets(b->'missing_evidence_slots');
  IF EXISTS (SELECT FROM jsonb_array_elements(b->'observations') o WHERE (o->>'fact_key'='BODY_MASS')<>(o->>'unit'='KG')) THEN RAISE EXCEPTION 'Assessment observation unit mismatch'; END IF;
 ELSIF k='DELEGATION' THEN
  IF i->>'code'<>(b->>'operation_scope')||':'||(b->>'grantee_principal_id') OR
    (b->>'action'='REVOKE')<>(b->'previous_grant_id'<>'null'::jsonb) THEN RAISE EXCEPTION 'Exact delegation scope/actor/lineage required'; END IF;
 END IF;
 IF k IN ('OBSERVATION','GOAL','ASSESSMENT') THEN
  PERFORM menuto_nutrition.strict_sets(b->'replaces');
  IF (b->>'operation'='CREATE')<>(b->'replaces'='[]'::jsonb) THEN RAISE EXCEPTION 'Explicit replacement coverage required'; END IF;
 END IF;
END $$;
CREATE FUNCTION menuto_nutrition.apply_timeline(segments jsonb,id uuid,b jsonb) RETURNS jsonb LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE lo timestamptz:=(b#>>'{effective,start}')::timestamptz; hi timestamptz:=(b#>>'{effective,end}')::timestamptz;
 seg jsonb; ids jsonb; cursor_at timestamptz; a timestamptz; z timestamptz; out jsonb:='[]'; max_end timestamptz; BEGIN
 SELECT coalesce(jsonb_agg(v ORDER BY v::text COLLATE "C"),'[]') INTO ids FROM (
  SELECT DISTINCT s->'id' v FROM jsonb_array_elements(segments) s
  WHERE (s->>'start')::timestamptz<hi AND (s->>'end')::timestamptz>lo) q;
 IF b->>'operation'='CREATE' THEN
  IF ids<>'[]'::jsonb OR b->'replaces'<>'[]'::jsonb THEN RAISE EXCEPTION 'CREATE cannot overlap or resurrect an existing segment'; END IF;
 ELSE
  IF ids='[]'::jsonb OR ids<>b->'replaces' THEN RAISE EXCEPTION 'Every replaced segment must be named exactly'; END IF;
  cursor_at:=lo;
  FOR seg IN SELECT s FROM jsonb_array_elements(segments) s ORDER BY (s->>'start')::timestamptz LOOP
   a:=(seg->>'start')::timestamptz; z:=(seg->>'end')::timestamptz;
   IF a<hi AND z>lo THEN
    IF a>cursor_at THEN RAISE EXCEPTION 'Replacement cannot invent absent interval coverage'; END IF;
    cursor_at:=greatest(cursor_at,least(z,hi));
   END IF;
  END LOOP;
  IF cursor_at<hi THEN RAISE EXCEPTION 'Replacement interval coverage incomplete'; END IF;
  SELECT max((s->>'end')::timestamptz) INTO max_end FROM jsonb_array_elements(segments) s;
  IF b->>'operation' IN ('REPLACE','RETRACT') AND hi<>max_end THEN RAISE EXCEPTION 'Replacement/retraction cannot resurrect later old state'; END IF;
 END IF;
 FOR seg IN SELECT value FROM jsonb_array_elements(segments) LOOP
  a:=(seg->>'start')::timestamptz; z:=(seg->>'end')::timestamptz;
  IF a<hi AND z>lo THEN
   IF a<lo THEN out:=out||jsonb_build_array(seg||jsonb_build_object('end',menuto_nutrition.utc(lo))); END IF;
   IF z>hi THEN out:=out||jsonb_build_array(seg||jsonb_build_object('start',menuto_nutrition.utc(hi))); END IF;
  ELSE out:=out||jsonb_build_array(seg); END IF;
 END LOOP;
 out:=out||jsonb_build_array(jsonb_build_object('id',id,'start',menuto_nutrition.utc(lo),'end',menuto_nutrition.utc(hi)));
 IF jsonb_array_length(out)>64 THEN RAISE EXCEPTION 'Server effective-interval limit; all-or-error'; END IF;
 SELECT jsonb_agg(s ORDER BY (s->>'start')::timestamptz) INTO out FROM jsonb_array_elements(out) s;
 RETURN out;
END $$;
CREATE FUNCTION menuto_nutrition.timeline(k text) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE segs jsonb:='[]'; r public.nutrition_source_receipts; BEGIN
 FOR r IN SELECT * FROM public.nutrition_source_receipts WHERE stream_key=k ORDER BY sequence LOOP
  segs:=menuto_nutrition.apply_timeline(segs,r.id,menuto_nutrition.record_body(r));
 END LOOP; RETURN segs;
END $$;
CREATE FUNCTION menuto_nutrition.covering_revision(k text,span jsonb) RETURNS uuid LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE id uuid; BEGIN
 SELECT (s->>'id')::uuid INTO id FROM jsonb_array_elements(menuto_nutrition.timeline(k)) s
 WHERE (s->>'start')::timestamptz<=(span->>'start')::timestamptz AND (s->>'end')::timestamptz>=(span->>'end')::timestamptz;
 RETURN id;
END $$;

CREATE FUNCTION menuto_nutrition.apply_publication(segments jsonb,id uuid,b jsonb,draft jsonb) RETURNS jsonb LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE lo timestamptz:=(b->>'effective_at')::timestamptz; hi timestamptz:=(draft#>>'{effective,end}')::timestamptz;
 seg jsonb; a timestamptz; z timestamptz; out jsonb:='[]'; prior text:=b->>'prior_publication_id'; target_found boolean:=false;
 action text:=b->>'action'; BEGIN
 IF action IN ('PUBLISH','SUPERSEDE') AND (lo<(draft#>>'{effective,start}')::timestamptz OR lo>=hi) THEN
  RAISE EXCEPTION 'Publication start outside complete guideline interval'; END IF;
 FOR seg IN SELECT value FROM jsonb_array_elements(segments) LOOP
  a:=(seg->>'start')::timestamptz; z:=(seg->>'end')::timestamptz;
  IF action='PUBLISH' THEN
   IF a<hi AND z>lo THEN RAISE EXCEPTION 'PUBLISH cannot choose a favorable overlapping version'; END IF;
   out:=out||jsonb_build_array(seg);
  ELSIF seg->>'publication_id'=prior AND z>lo THEN
   target_found:=true;
   IF a<lo THEN out:=out||jsonb_build_array(seg||jsonb_build_object('end',menuto_nutrition.utc(lo))); END IF;
   IF action IN ('RETIRE','RETRACT') THEN
    IF seg->>'draft_revision_id'<>b->>'draft_revision_id' THEN RAISE EXCEPTION 'Withdrawal target differs'; END IF;
    out:=out||jsonb_build_array(seg||jsonb_build_object('start',menuto_nutrition.utc(greatest(a,lo)),
      'publication_id',id,'active',false,'cause',CASE WHEN action='RETIRE' THEN 'SOURCE_RETIRED' ELSE 'SOURCE_RETRACTED' END));
   ELSIF z>hi THEN
    -- The superseded version must not resurrect after its replacement expires.
    out:=out||jsonb_build_array(seg||jsonb_build_object('start',menuto_nutrition.utc(hi),
      'publication_id',id,'active',false,'cause','SOURCE_OUT_OF_EFFECTIVE_RANGE'));
   END IF;
  ELSE
   IF action='SUPERSEDE' AND a<hi AND z>lo THEN RAISE EXCEPTION 'Supersession cannot truncate an unrelated scheduled version'; END IF;
   out:=out||jsonb_build_array(seg);
  END IF;
 END LOOP;
 IF action<>'PUBLISH' AND NOT target_found THEN RAISE EXCEPTION 'Exact applicable publication predecessor required'; END IF;
 IF action IN ('PUBLISH','SUPERSEDE') THEN
  out:=out||jsonb_build_array(jsonb_build_object('start',menuto_nutrition.utc(lo),'end',menuto_nutrition.utc(hi),
    'publication_id',id,'draft_revision_id',b->'draft_revision_id','active',true,'cause',NULL));
 END IF;
 IF action='SUPERSEDE' AND EXISTS (SELECT FROM jsonb_array_elements(segments) q WHERE q->>'publication_id'=prior AND (q->>'end')::timestamptz=lo) THEN target_found:=true; END IF;
 IF jsonb_array_length(out)>64 THEN RAISE EXCEPTION 'Server publication interval limit; all-or-error'; END IF;
 SELECT coalesce(jsonb_agg(s ORDER BY (s->>'start')::timestamptz),'[]') INTO out FROM jsonb_array_elements(out) s;
 RETURN out;
END $$;
CREATE FUNCTION menuto_nutrition.publication_timeline(k text) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE segs jsonb:='[]'; r record; BEGIN
 FOR r IN SELECT p.id,p.body,d.body#>'{guideline}' draft FROM public.nutrition_source_receipts h
  JOIN public.nutrition_guideline_publications p ON p.id=h.id
  JOIN public.nutrition_guideline_drafts d ON d.id=p.draft_revision_id
  WHERE h.stream_key=k ORDER BY h.sequence LOOP
  segs:=menuto_nutrition.apply_publication(segs,r.id,r.body,r.draft);
 END LOOP; RETURN segs;
END $$;
CREATE FUNCTION menuto_nutrition.published_revision(k text,span jsonb) RETURNS uuid LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE id uuid; BEGIN
 SELECT (s->>'draft_revision_id')::uuid INTO id FROM jsonb_array_elements(menuto_nutrition.publication_timeline(k)) s
 WHERE s->>'active'='true' AND (s->>'start')::timestamptz<=(span->>'start')::timestamptz
  AND (s->>'end')::timestamptz>=(span->>'end')::timestamptz;
 RETURN id;
END $$;
CREATE FUNCTION menuto_nutrition.check_review(b jsonb,k text,who uuid) RETURNS void LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE d public.nutrition_guideline_drafts; old public.nutrition_source_receipts; human uuid; BEGIN
 SELECT x.* INTO d FROM public.nutrition_guideline_drafts x JOIN public.nutrition_source_receipts r ON r.id=x.id
 WHERE x.id=(b->>'draft_revision_id')::uuid AND r.stream_key=k;
 IF d.id IS NULL OR d.body_fingerprint<>b->>'body_fingerprint'
  OR menuto_nutrition.hash('nutrition.evidence-manifest.v1',d.body#>'{guideline,evidence_manifest}')<>b->>'evidence_fingerprint'
  OR menuto_nutrition.hash('nutrition.protocol.v1',d.body#>'{guideline,protocol}')<>b->>'protocol_fingerprint' THEN
  RAISE EXCEPTION 'Complete exact draft/evidence/protocol review binding required'; END IF;
 IF b->>'decision'='CANCEL' THEN
  SELECT r.* INTO old FROM public.nutrition_source_receipts r JOIN public.nutrition_guideline_reviews rv ON rv.id=r.id
   WHERE rv.id=(b->>'prior_review_id')::uuid AND rv.decision='APPROVE' AND rv.draft_revision_id=d.id AND r.stream_key=k;
  SELECT verified_human_id INTO human FROM public.nutrition_source_principals WHERE id=who;
  IF old.id IS NULL OR human IS DISTINCT FROM (SELECT verified_human_id FROM public.nutrition_source_principals WHERE id=old.principal_id)
    OR EXISTS (SELECT FROM public.nutrition_guideline_reviews WHERE prior_review_id=old.id) THEN
   RAISE EXCEPTION 'Only the authorized verified reviewer may cancel this exact active review'; END IF;
 END IF;
END $$;
CREATE FUNCTION menuto_nutrition.check_publication(b jsonb,i jsonb,who uuid,t timestamptz) RETURNS void LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE d public.nutrition_guideline_drafts; rv public.nutrition_guideline_reviews; rr public.nutrition_source_receipts;
 sc jsonb; reviewer uuid; publisher uuid; g uuid; reviewer_binding public.nutrition_source_principals; k text:=menuto_nutrition.source_key(i); BEGIN
 SELECT x.* INTO d FROM public.nutrition_guideline_drafts x JOIN public.nutrition_source_receipts r ON r.id=x.id
 WHERE x.id=(b->>'draft_revision_id')::uuid AND r.stream_key=k;
 IF d.id IS NULL OR d.body_fingerprint<>b->>'body_fingerprint' THEN RAISE EXCEPTION 'Exact complete guideline body pin required'; END IF;
 IF b->>'action' IN ('PUBLISH','SUPERSEDE') THEN
  SELECT * INTO rv FROM public.nutrition_guideline_reviews WHERE id=(b->>'review_event_id')::uuid;
  SELECT * INTO rr FROM public.nutrition_source_receipts WHERE id=rv.id;
  IF rv.id IS NULL OR rv.decision<>'APPROVE' OR rv.draft_revision_id<>d.id OR rr.stream_key<>k
    OR EXISTS (SELECT FROM public.nutrition_guideline_reviews WHERE prior_review_id=rv.id) THEN
   RAISE EXCEPTION 'Complete current review receipt required'; END IF;
  sc:=jsonb_build_object('provider_id',i->'provider_id','family_id',i->'family_id','household_id',NULL,'member_id',NULL);
  -- Recheck reviewer authorization before even disclosing an old idempotency receipt.
  g:=menuto_nutrition.permission(rr.principal_id,sc,'GUIDELINE_REVIEW',NULL,NULL,t);
  SELECT * INTO STRICT reviewer_binding FROM public.nutrition_source_principals WHERE id=rr.principal_id;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE oid=reviewer_binding.role_oid AND rolname=reviewer_binding.role_name) THEN RAISE EXCEPTION 'Reviewer credential binding changed'; END IF;
  PERFORM menuto_nutrition.safe_role(reviewer_binding.role_name::name,false);
  IF g<>rr.grant_event_id THEN RAISE EXCEPTION 'Review grant changed; fresh review required'; END IF;
  SELECT verified_human_id INTO reviewer FROM public.nutrition_source_principals WHERE id=rr.principal_id;
  SELECT verified_human_id INTO publisher FROM public.nutrition_source_principals WHERE id=who;
  IF reviewer IS NULL OR publisher IS NULL OR reviewer=publisher THEN RAISE EXCEPTION 'Reviewer and publisher must be different verified humans'; END IF;
  PERFORM menuto_nutrition.check_review(rv.body,k,rr.principal_id);
 ELSE
  IF NOT EXISTS (SELECT FROM public.nutrition_guideline_publications p JOIN public.nutrition_source_receipts r ON r.id=p.id
    WHERE p.id=(b->>'prior_publication_id')::uuid AND p.draft_revision_id=d.id AND r.stream_key=k) THEN
   RAISE EXCEPTION 'Withdrawal requires exact same-family publication target'; END IF;
 END IF;
END $$;

CREATE FUNCTION menuto_nutrition.touch_sources(p uuid,h uuid,m uuid) RETURNS void LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$ BEGIN
 -- Actual row versions serialize mutation authorization even for a stale RR/SERIALIZABLE
 -- writer: a newer revoke makes its SELECT FOR UPDATE fail, rather than see old grants.
 IF p IS NOT NULL THEN
  UPDATE public.nutrition_source_streams SET revision=revision+1
   WHERE stream_key=menuto_nutrition.hash('nutrition.provider-lock.v1',jsonb_build_object('provider_id',p)) AND kind='LOCK';
  IF NOT FOUND THEN RAISE EXCEPTION 'Provider lock frontier missing'; END IF;
 END IF;
 IF m IS NOT NULL THEN
  UPDATE public.nutrition_source_streams SET revision=revision+1
   WHERE stream_key=menuto_nutrition.hash('nutrition.member-lock.v1',menuto_nutrition.subject(h,m)) AND kind='LOCK';
  IF NOT FOUND THEN RAISE EXCEPTION 'Member lock frontier missing'; END IF;
 END IF;
END $$;
CREATE FUNCTION menuto_nutrition.check_assessor_qualification(c jsonb) RETURNS void LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$ BEGIN
 IF c->>'action'='GRANT' AND c->>'capability'='ELIGIBILITY_ATTEST' AND NOT EXISTS (
  SELECT FROM public.nutrition_guideline_drafts d JOIN public.nutrition_guideline_publications p ON p.draft_revision_id=d.id
   WHERE d.provider_id=(c#>>'{scope,provider_id}')::uuid AND d.family_id=c#>>'{scope,family_id}'
   AND menuto_nutrition.hash('nutrition.protocol.v1',d.body#>'{guideline,protocol}')=c->>'protocol_fingerprint'
   AND p.action IN ('PUBLISH','SUPERSEDE')
 ) THEN RAISE EXCEPTION 'Assessor qualification requires exact already-reviewed published protocol'; END IF;
END $$;

CREATE FUNCTION menuto_nutrition.member_auth(i jsonb,b jsonb,p public.nutrition_source_principals,t timestamptz) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE w jsonb; d record; op text; h uuid:=(i->>'household_id')::uuid; m uuid:=(i->>'member_id')::uuid; self_author boolean; BEGIN
 w:=menuto_nutrition.subject_witness(h,m,p.user_id);
 IF b->>'kind'='ASSESSMENT' THEN
  IF p.verified_human_id IS NULL THEN RAISE EXCEPTION 'Qualified human assessor required'; END IF;
  RETURN jsonb_build_object('witness',w,'delegation_id',NULL);
 END IF;
 self_author:=p.user_id IS NOT NULL AND w->'membership_id'<>'null'::jsonb AND
  w->>'role' IN ('OWNER','EDITOR') AND (w->>'actor_member_id')::uuid=m;
 IF b->>'kind'='DELEGATION' THEN
  IF NOT self_author AND NOT (p.delegation_registrar AND p.verified_human_id IS NOT NULL) THEN
   RAISE EXCEPTION 'Subject or independently enrolled delegation registrar required'; END IF;
  IF NOT EXISTS (SELECT FROM public.nutrition_source_principals WHERE id=(b->>'grantee_principal_id')::uuid
    AND verified_human_id IS NOT NULL AND user_id IS NOT NULL) THEN RAISE EXCEPTION 'Delegation cannot turn a service into a member author'; END IF;
  IF b->>'action'='REVOKE' AND NOT EXISTS (
   SELECT FROM public.nutrition_member_delegations WHERE id=(b->>'previous_grant_id')::uuid
    AND household_id=h AND member_id=m AND grantee_principal_id=(b->>'grantee_principal_id')::uuid
    AND operation_scope=b->>'operation_scope' AND action='GRANT'
  ) THEN RAISE EXCEPTION 'Exact delegation grant to revoke required'; END IF;
  RETURN jsonb_build_object('witness',w,'delegation_id',NULL);
 END IF;
 IF p.user_id IS NULL OR w->'membership_id'='null'::jsonb OR w->>'role' NOT IN ('OWNER','EDITOR') THEN
  RAISE EXCEPTION 'Canonical member-author household access required'; END IF;
 IF self_author THEN RETURN jsonb_build_object('witness',w,'delegation_id',NULL); END IF;
 op:=CASE WHEN b->>'kind'='GOAL' THEN 'MEMBER_GOAL_WRITE'
          WHEN b->>'fact_key'='BODY_MASS' THEN 'BODY_MASS_WRITE' ELSE 'HEIGHT_WRITE' END;
 SELECT x.*,r.sequence INTO d FROM public.nutrition_member_delegations x JOIN public.nutrition_source_receipts r ON r.id=x.id
 WHERE x.household_id=h AND x.member_id=m AND x.grantee_principal_id=p.id AND x.operation_scope=op
  AND x.effective_from<=t ORDER BY r.sequence DESC LIMIT 1;
 IF d.id IS NULL OR d.action<>'GRANT' OR d.effective_until<=t OR
   d.effective_from>(b#>>'{effective,start}')::timestamptz OR d.effective_until<(b#>>'{effective,end}')::timestamptz THEN
  RAISE EXCEPTION 'Exact current subject/actor/operation delegation required'; END IF;
 RETURN jsonb_build_object('witness',w,'delegation_id',d.id);
END $$;
CREATE FUNCTION menuto_nutrition.check_observation(b jsonb,a jsonb) RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE legacy text; BEGIN
 legacy:=CASE WHEN b->>'fact_key'='BODY_MASS' THEN a#>>'{profile,body_mass_kg}' ELSE a#>>'{profile,height_cm}' END;
 IF b->'value'<>'null'::jsonb AND legacy IS NOT NULL AND
   (b#>>'{value,numerator}')::numeric<>legacy::numeric*(b#>>'{value,denominator}')::numeric THEN
  RAISE EXCEPTION 'Legacy source conflict: reconcile explicitly then append a new attestation'; END IF;
END $$;
CREATE FUNCTION menuto_nutrition.check_assessment(b jsonb,i jsonb,anchor jsonb,grant_id uuid) RETURNS void LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE d public.nutrition_guideline_drafts; p jsonb; o jsonb; obs public.nutrition_source_receipts;
 ob jsonb; ident jsonb; expected jsonb; all_facts jsonb; all_slots jsonb; facts jsonb; slots jsonb;
 missing_facts jsonb; missing_slots jsonb; own jsonb; published uuid; grant_body jsonb; BEGIN
 SELECT * INTO d FROM public.nutrition_guideline_drafts WHERE id=(b->>'guideline_revision_id')::uuid
  AND provider_id=(i->>'provider_id')::uuid AND family_id=i->>'family_id';
 IF d.id IS NULL OR d.body_fingerprint<>b->>'guideline_body_fingerprint' THEN RAISE EXCEPTION 'Exact assessment guideline pin required'; END IF;
 p:=d.body#>'{guideline,protocol}';
 IF menuto_nutrition.hash('nutrition.protocol.v1',p)<>b->>'protocol_fingerprint' THEN RAISE EXCEPTION 'Exact assessment protocol body/version required'; END IF;
 IF b->>'operation'='RETRACT' THEN
  IF b->>'outcome'<>'UNDETERMINED' THEN RAISE EXCEPTION 'Assessment retraction cannot assert SUPPORTED'; END IF;
  RETURN;
 END IF;
 SELECT body INTO STRICT grant_body FROM public.nutrition_source_authority WHERE id=grant_id;
 IF NOT menuto_nutrition.covers(grant_body->'effective',b->'effective') THEN RAISE EXCEPTION 'Assessment outside assessor qualification interval'; END IF;
 ident:=jsonb_build_object('kind','GUIDELINE','provider_id',i->'provider_id','family_id',i->'family_id',
  'household_id',NULL,'member_id',NULL,'code','FAMILY');
 published:=menuto_nutrition.published_revision(menuto_nutrition.source_key(ident),b->'effective');
 IF published IS DISTINCT FROM d.id THEN RAISE EXCEPTION 'Assessment requires applicable published protocol for entire interval'; END IF;
 FOR o IN SELECT value FROM jsonb_array_elements(b->'observations') LOOP
  SELECT * INTO obs FROM public.nutrition_source_receipts WHERE id=(o->>'revision_id')::uuid AND kind='OBSERVATION';
  IF obs.id IS NULL THEN RAISE EXCEPTION 'Exact observation source missing'; END IF;
  ob:=menuto_nutrition.record_body(obs);
  ident:=jsonb_build_object('kind','OBSERVATION','provider_id',NULL,'family_id',NULL,
    'household_id',i->'household_id','member_id',i->'member_id','code',o->'fact_key');
  IF obs.stream_key<>menuto_nutrition.source_key(ident) OR ob->>'operation'='RETRACT'
    OR menuto_nutrition.covering_revision(obs.stream_key,b->'effective') IS DISTINCT FROM obs.id THEN
   RAISE EXCEPTION 'Assessment observation subject/version/interval stale'; END IF;
  expected:=jsonb_build_object('fact_key',ob->'fact_key','revision_id',obs.id,'fact_hash',obs.fact_hash,
   'value',ob->'value','unit',ob->'unit','legacy_anchor_fingerprint',obs.legacy_anchor->'body_fingerprint');
  IF expected<>o OR obs.legacy_anchor<>anchor THEN RAISE EXCEPTION 'Observation preimage/legacy source changed; new attestation required'; END IF;
  IF ob#>>'{provenance,environment}'<>p->>'environment' THEN RAISE EXCEPTION 'TEST_ONLY observation cannot supply another source environment'; END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(v ORDER BY v::text COLLATE "C"),'[]') INTO all_facts FROM (
  SELECT DISTINCT v FROM (SELECT value v FROM jsonb_array_elements(p#>'{admitted,observations}')
   UNION SELECT value FROM jsonb_array_elements(p#>'{excluded,observations}')
   UNION SELECT value FROM jsonb_array_elements(p#>'{out_of_scope,observations}')) q) u;
 SELECT coalesce(jsonb_agg(v ORDER BY v::text COLLATE "C"),'[]') INTO all_slots FROM (
  SELECT DISTINCT v FROM (SELECT value v FROM jsonb_array_elements(p#>'{admitted,evidence_slots}')
   UNION SELECT value FROM jsonb_array_elements(p#>'{excluded,evidence_slots}')
   UNION SELECT value FROM jsonb_array_elements(p#>'{out_of_scope,evidence_slots}')) q) u;
 SELECT coalesce(jsonb_agg(value->'fact_key' ORDER BY ord),'[]') INTO facts FROM jsonb_array_elements(b->'observations') WITH ORDINALITY e(value,ord);
 SELECT coalesce(jsonb_agg(value->'evidence_id' ORDER BY ord),'[]') INTO slots FROM jsonb_array_elements(b->'evidence') WITH ORDINALITY e(value,ord);
 SELECT coalesce(jsonb_agg(v ORDER BY v::text COLLATE "C"),'[]') INTO missing_facts FROM jsonb_array_elements(all_facts) v WHERE NOT facts @> jsonb_build_array(v);
 SELECT coalesce(jsonb_agg(v ORDER BY v::text COLLATE "C"),'[]') INTO missing_slots FROM jsonb_array_elements(all_slots) v WHERE NOT slots @> jsonb_build_array(v);
 IF NOT all_facts @> facts OR NOT all_slots @> slots OR missing_facts<>b->'missing_observations' OR missing_slots<>b->'missing_evidence_slots' THEN
  RAISE EXCEPTION 'Exact evidence completeness/absence manifest required'; END IF;
 IF EXISTS (SELECT FROM jsonb_array_elements(b->'evidence') e WHERE e->>'environment'<>p->>'environment') THEN RAISE EXCEPTION 'Assessment evidence environment mismatch'; END IF;
 own:=CASE b->>'outcome' WHEN 'ADMITTED' THEN p->'admitted' WHEN 'EXCLUDED' THEN p->'excluded'
       WHEN 'OUT_OF_SCOPE' THEN p->'out_of_scope' ELSE NULL END;
 IF own IS NOT NULL AND (NOT facts @> (own->'observations') OR NOT slots @> (own->'evidence_slots')) THEN
  RAISE EXCEPTION 'Outcome-specific reviewed proof incomplete'; END IF;
END $$;
CREATE FUNCTION menuto_nutrition.append(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_nutrition,pg_temp SET lock_timeout='1s' AS $$
<<source_write>>
DECLARE started timestamptz:=clock_timestamp(); s jsonb:=menuto_nutrition.session_fact(false); i jsonb; b jsonb; k text; cap text;
 p public.nutrition_source_principals; f public.nutrition_source_streams; auth public.nutrition_source_streams;
 r public.nutrition_source_receipts; retry public.nutrition_source_receipts; sc jsonb; permission_id uuid;
 provider_id uuid; protocol text; fact text; member_auth jsonb; anchor jsonb; h text; full_fact jsonb; dummy jsonb;
 target public.nutrition_goal_revisions; t timestamptz; BEGIN
 PERFORM menuto_nutrition.check_command('NutritionSourceCommand',c);
 PERFORM menuto_nutrition.check_source_command(c);
 i:=c->'identity'; b:=c->'body'; k:=menuto_nutrition.source_key(i);
 PERFORM menuto_nutrition.lock_sources((i->>'provider_id')::uuid,(i->>'household_id')::uuid,(i->>'member_id')::uuid);
 s:=menuto_nutrition.session_fact(false); t:=clock_timestamp();
 SELECT * INTO STRICT p FROM public.nutrition_source_principals WHERE id=menuto_nutrition.principal(s);
 IF i->'provider_id'<>'null'::jsonb THEN provider_id:=menuto_nutrition.provider((i->>'provider_id')::uuid,s); END IF;
 sc:=jsonb_build_object('provider_id',i->'provider_id','family_id',i->'family_id','household_id',i->'household_id','member_id',i->'member_id');
 cap:=CASE b->>'kind' WHEN 'DRAFT' THEN 'GUIDELINE_REVIEW' WHEN 'REVIEW' THEN 'GUIDELINE_REVIEW'
  WHEN 'PUBLICATION' THEN CASE WHEN b->>'action' IN ('PUBLISH','SUPERSEDE') THEN 'GUIDELINE_PUBLISH' ELSE 'GUIDELINE_WITHDRAW' END
  WHEN 'OBSERVATION' THEN 'MEMBER_OBSERVATION_WRITE' WHEN 'GOAL' THEN 'MEMBER_GOAL_WRITE'
  WHEN 'ASSESSMENT' THEN 'ELIGIBILITY_ATTEST'
  WHEN 'DELEGATION' THEN CASE WHEN b->>'operation_scope'='MEMBER_GOAL_WRITE' THEN 'MEMBER_GOAL_WRITE' ELSE 'MEMBER_OBSERVATION_WRITE' END END;
 protocol:=CASE WHEN b->>'kind'='ASSESSMENT' THEN b->>'protocol_fingerprint' END;
 fact:=CASE WHEN b->>'kind'='OBSERVATION' THEN b->>'fact_key' WHEN b->>'kind'='DELEGATION' AND cap='MEMBER_OBSERVATION_WRITE'
   THEN CASE WHEN b->>'operation_scope'='BODY_MASS_WRITE' THEN 'BODY_MASS' ELSE 'HEIGHT' END END;
 permission_id:=menuto_nutrition.permission(p.id,sc,cap,protocol,fact,t);
 IF b->>'kind' IN ('OBSERVATION','GOAL') AND b#>>'{provenance,environment}'<>
   p.command#>>'{identity_evidence,environment}' THEN RAISE EXCEPTION 'Member source environment mismatch'; END IF;
 IF b->>'kind'='DELEGATION' AND b#>>'{authorization_evidence,environment}'<>
   p.command#>>'{identity_evidence,environment}' THEN RAISE EXCEPTION 'Delegation source environment mismatch'; END IF;
 IF i->>'kind'='GUIDELINE' THEN
  IF p.verified_human_id IS NULL THEN RAISE EXCEPTION 'Verified reference human required'; END IF;
 ELSE member_auth:=menuto_nutrition.member_auth(i,b,p,t); END IF;
 IF b->>'kind'='PUBLICATION' THEN PERFORM menuto_nutrition.check_publication(b,i,p.id,t); END IF;
 h:=menuto_nutrition.hash('nutrition.source-command.v1',c);
 SELECT * INTO retry FROM public.nutrition_source_receipts WHERE actor_database_oid=(s->>'database_oid')::bigint
  AND actor_role_oid=(s->>'role_oid')::bigint AND idempotency_key=c->>'idempotency_key';
 IF FOUND THEN
  IF retry.command_hash<>h OR retry.kind='AUTHORITY' THEN RAISE EXCEPTION 'Source idempotency conflict'; END IF;
  RETURN menuto_nutrition.record_fact(retry);
 END IF;
 PERFORM menuto_nutrition.ensure_stream(k,'SOURCE',i);
 SELECT * INTO STRICT f FROM public.nutrition_source_streams WHERE stream_key=k FOR UPDATE;
 SELECT * INTO STRICT auth FROM public.nutrition_source_streams WHERE stream_key=menuto_nutrition.authority_key(sc);
 IF f.revision<>(c->>'expected_revision')::bigint OR f.head_id IS DISTINCT FROM (c->>'predecessor_id')::uuid THEN RAISE EXCEPTION 'Source stream CAS conflict'; END IF;
 IF f.revision>=64 THEN RAISE EXCEPTION 'Server source history-depth limit; no truncation'; END IF;
 IF b->>'kind' IN ('OBSERVATION','ASSESSMENT') THEN anchor:=menuto_nutrition.legacy_anchor((i->>'household_id')::uuid,(i->>'member_id')::uuid); END IF;
 IF b->>'kind'='DRAFT' THEN
  IF b#>>'{guideline,environment}'<>(SELECT environment FROM public.nutrition_source_providers WHERE id=source_write.provider_id) THEN RAISE EXCEPTION 'Provider/reference environment mismatch'; END IF;
  IF EXISTS (SELECT FROM public.nutrition_guideline_drafts d WHERE d.provider_id=(i->>'provider_id')::uuid AND d.family_id=i->>'family_id'
   AND d.body#>>'{guideline,protocol,protocol_id}'=b#>>'{guideline,protocol,protocol_id}'
   AND d.body#>>'{guideline,protocol,version}'=b#>>'{guideline,protocol,version}'
   AND d.body#>'{guideline,protocol}'<>b#>'{guideline,protocol}') THEN RAISE EXCEPTION 'Immutable protocol/version body conflict'; END IF;
 ELSIF b->>'kind'='REVIEW' THEN PERFORM menuto_nutrition.check_review(b,k,p.id);
 ELSIF b->>'kind'='PUBLICATION' THEN
  SELECT menuto_nutrition.apply_publication(menuto_nutrition.publication_timeline(k),(c->>'revision_id')::uuid,b,d.body->'guideline')
   INTO dummy FROM public.nutrition_guideline_drafts d WHERE d.id=(b->>'draft_revision_id')::uuid;
 ELSIF b->>'kind'='OBSERVATION' THEN
  IF (b->>'observed_at')::timestamptz>t THEN RAISE EXCEPTION 'Future measurements cannot be asserted as already observed'; END IF;
  PERFORM menuto_nutrition.check_observation(b,anchor);
 ELSIF b->>'kind'='ASSESSMENT' THEN PERFORM menuto_nutrition.check_assessment(b,i,anchor,permission_id);
 ELSIF b->>'kind'='GOAL' THEN
  SELECT * INTO target FROM public.nutrition_goal_revisions WHERE id=(b->>'goal_id')::uuid;
  IF target.id IS NULL THEN
   IF b->>'goal_id'<>c->>'revision_id' THEN RAISE EXCEPTION 'New goal identity must anchor its own first revision'; END IF;
  ELSIF target.household_id<>(i->>'household_id')::uuid OR target.member_id<>(i->>'member_id')::uuid THEN
   RAISE EXCEPTION 'Goal identity belongs to another member'; END IF;
 END IF;
 IF b->>'kind' IN ('OBSERVATION','ASSESSMENT','GOAL') THEN
  dummy:=menuto_nutrition.apply_timeline(menuto_nutrition.timeline(k),(c->>'revision_id')::uuid,b);
 END IF;
 PERFORM menuto_nutrition.retain_evidence(c);
 r.id:=(c->>'revision_id')::uuid; r.kind:=b->>'kind'; r.recorded_order:=nextval('public.nutrition_source_recorded_order');
 r.stream_key:=k; r.sequence:=f.revision+1; r.previous_id:=f.head_id; r.previous_hash:=f.head_hash;
 r.principal_id:=p.id; r.grant_event_id:=permission_id; r.authority_generation:=auth.revision;
 r.provider_enrollment_id:=provider_id; r.actor_database_oid:=(s->>'database_oid')::bigint; r.actor_role_oid:=(s->>'role_oid')::bigint;
 r.actor:=s; r.subject_witness:=member_auth->'witness'; r.delegation_event_id:=(member_auth->>'delegation_id')::uuid;
 r.legacy_anchor:=anchor; r.recorded_at:=clock_timestamp(); r.idempotency_key:=c->>'idempotency_key'; r.command_hash:=h;
 full_fact:=jsonb_build_object('id',r.id,'recorded_order',r.recorded_order,'command',c,'stream_key',k,'sequence',r.sequence,'previous_hash',f.head_hash,
  'principal_id',p.id,'grant_event_id',permission_id,'authority_generation',auth.revision,'provider_enrollment_id',provider_id,
  'author',s,'subject_witness',r.subject_witness,'delegation_event_id',r.delegation_event_id,'legacy_anchor',anchor,
  'recorded_at',menuto_nutrition.utc(r.recorded_at),'command_hash',h);
 r.fact_hash:=menuto_nutrition.hash('nutrition.record.v1',full_fact);
 INSERT INTO public.nutrition_source_receipts SELECT r.*;
 CASE b->>'kind'
 WHEN 'DRAFT' THEN INSERT INTO public.nutrition_guideline_drafts VALUES(r.id,(i->>'provider_id')::uuid,i->>'family_id',menuto_nutrition.hash('nutrition.guideline-body.v1',b->'guideline'),b);
 WHEN 'REVIEW' THEN INSERT INTO public.nutrition_guideline_reviews VALUES(r.id,(b->>'draft_revision_id')::uuid,b->>'decision',(b->>'prior_review_id')::uuid,b);
 WHEN 'PUBLICATION' THEN INSERT INTO public.nutrition_guideline_publications VALUES(r.id,(b->>'draft_revision_id')::uuid,b->>'action',(b->>'review_event_id')::uuid,(b->>'prior_publication_id')::uuid,(b->>'effective_at')::timestamptz,b);
 WHEN 'DELEGATION' THEN INSERT INTO public.nutrition_member_delegations VALUES(r.id,(i->>'household_id')::uuid,(i->>'member_id')::uuid,(b->>'grantee_principal_id')::uuid,b->>'operation_scope',b->>'action',(b->>'previous_grant_id')::uuid,(b#>>'{effective,start}')::timestamptz,(b#>>'{effective,end}')::timestamptz,b);
 WHEN 'OBSERVATION' THEN INSERT INTO public.nutrition_physiology_revisions VALUES(r.id,(i->>'household_id')::uuid,(i->>'member_id')::uuid,b->>'operation',(b#>>'{effective,start}')::timestamptz,(b#>>'{effective,end}')::timestamptz,b->>'fact_key',b->>'unit',(b->>'observed_at')::timestamptz,b);
 WHEN 'ASSESSMENT' THEN INSERT INTO public.nutrition_eligibility_revisions VALUES(r.id,(i->>'household_id')::uuid,(i->>'member_id')::uuid,b->>'operation',(b#>>'{effective,start}')::timestamptz,(b#>>'{effective,end}')::timestamptz,(b->>'guideline_revision_id')::uuid,b->>'protocol_fingerprint',b->>'outcome',b);
 WHEN 'GOAL' THEN INSERT INTO public.nutrition_goal_revisions VALUES(r.id,(i->>'household_id')::uuid,(i->>'member_id')::uuid,b->>'operation',(b#>>'{effective,start}')::timestamptz,(b#>>'{effective,end}')::timestamptz,(b->>'goal_id')::uuid,b->>'goal_type',b->>'direction',b);
 END CASE;
 UPDATE public.nutrition_source_streams SET revision=r.sequence,head_id=r.id,head_hash=r.fact_hash WHERE stream_key=k;
 PERFORM menuto_nutrition.touch_sources((i->>'provider_id')::uuid,(i->>'household_id')::uuid,(i->>'member_id')::uuid);
 PERFORM menuto_nutrition.deadline(started);
 RETURN menuto_nutrition.record_fact(r);
END $$;

CREATE FUNCTION menuto_nutrition.source_in_request(i jsonb,c jsonb) RETURNS boolean LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
 SELECT CASE WHEN i->>'kind'='GUIDELINE' THEN i->'provider_id'=c->'provider_id' AND i->'family_id'=c->'family_id'
 ELSE i->'household_id'=c#>'{subject,household_id}' AND i->'member_id'=c#>'{subject,member_id}'
  AND (i->>'kind' IN ('OBSERVATION','GOAL','DELEGATION') OR
    (i->>'kind'='ASSESSMENT' AND i->'provider_id'=c->'provider_id' AND i->'family_id'=c->'family_id' AND i->'code'=c->'protocol_fingerprint')) END
$$;
CREATE FUNCTION menuto_nutrition.capture(c jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_nutrition,pg_temp SET lock_timeout='1s' AS $$
DECLARE started timestamptz:=clock_timestamp(); s jsonb:=menuto_nutrition.session_fact(false);
 p public.nutrition_source_principals; provider_binding uuid; read_scope jsonb; reference_scope jsonb; member_scope jsonb;
 reader_grant uuid; cap text; witness jsonb; h uuid; m uuid; authority_keys text[]; required jsonb:='[]'; manifests jsonb;
 i jsonb; k text; code text; kind text; item jsonb; providers jsonb; principals jsonb; authority jsonb; sources jsonb;
 ids uuid[]; provider_ids uuid[]; result jsonb; frame jsonb; completed timestamptz; rows bigint; journal_rows bigint; BEGIN
 PERFORM menuto_nutrition.check_command('NutritionRootRequest',c);
 IF current_setting('transaction_read_only')<>'on' OR current_setting('transaction_isolation') NOT IN ('repeatable read','serializable')
    OR pg_current_xact_id_if_assigned() IS NOT NULL THEN
  RAISE EXCEPTION 'Clean caller-owned read-only RR/SERIALIZABLE Nutrition capture required'; END IF;
 IF menuto_nutrition.canonical(c#>'{temporal,interval}') IS NULL THEN RAISE EXCEPTION 'Explicit temporal interval required'; END IF;
 PERFORM menuto_nutrition.interval_ok(c#>'{temporal,interval}');
 SELECT * INTO STRICT p FROM public.nutrition_source_principals WHERE id=menuto_nutrition.principal(s);
 provider_binding:=menuto_nutrition.provider((c->>'provider_id')::uuid,s);
 IF (SELECT environment FROM public.nutrition_source_providers WHERE id=provider_binding)<>c->>'environment' THEN
  RAISE EXCEPTION 'TEST_ONLY content cannot become production source authority'; END IF;
 h:=(c#>>'{subject,household_id}')::uuid; m:=(c#>>'{subject,member_id}')::uuid;
 read_scope:=jsonb_build_object('provider_id',c->'provider_id','family_id',c->'family_id','household_id',h,'member_id',m);
 cap:=CASE WHEN c->>'purpose'='ROOT' THEN 'ROOT_SOURCE_READ' ELSE 'VALIDATOR_SOURCE_READ' END;
 reader_grant:=menuto_nutrition.permission(p.id,read_scope,cap,NULL,NULL,started);
 witness:=menuto_nutrition.subject_witness(h,m,p.user_id);
 IF p.user_id IS NOT NULL AND witness->'membership_id'='null'::jsonb THEN RAISE EXCEPTION 'Canonical household read access required'; END IF;
 IF p.user_id IS NULL AND p.service_id IS NULL THEN RAISE EXCEPTION 'Exact source reader service binding required'; END IF;
 reference_scope:=jsonb_build_object('provider_id',c->'provider_id','family_id',c->'family_id','household_id',NULL,'member_id',NULL);
 member_scope:=jsonb_build_object('provider_id',NULL,'family_id',NULL,'household_id',h,'member_id',m);
 authority_keys:=ARRAY[menuto_nutrition.authority_key(reference_scope),menuto_nutrition.authority_key(member_scope)];
 SELECT count(*) INTO journal_rows FROM (SELECT r.id FROM public.nutrition_source_receipts r
  JOIN public.nutrition_source_streams st ON st.stream_key=r.stream_key
  WHERE (st.kind='AUTHORITY' AND st.stream_key=ANY(authority_keys)) OR
    (st.kind='SOURCE' AND menuto_nutrition.source_in_request(st.identity,c)) LIMIT 4097) bounded;
 IF journal_rows>4096 OR EXISTS (SELECT FROM public.nutrition_source_streams st WHERE st.revision>64 AND
   ((st.kind='AUTHORITY' AND st.stream_key=ANY(authority_keys)) OR
    (st.kind='SOURCE' AND menuto_nutrition.source_in_request(st.identity,c)))) THEN
  RAISE EXCEPTION 'Server complete source history/row limit; no truncation'; END IF;
 SELECT coalesce(jsonb_agg(menuto_nutrition.record_fact(r) ORDER BY r.stream_key,r.sequence),'[]') INTO authority
  FROM public.nutrition_source_receipts r WHERE r.kind='AUTHORITY' AND r.stream_key=ANY(authority_keys);
 SELECT coalesce(jsonb_agg(menuto_nutrition.record_fact(r) ORDER BY r.stream_key,r.sequence),'[]') INTO sources
  FROM public.nutrition_source_receipts r JOIN public.nutrition_source_streams st ON st.stream_key=r.stream_key
  WHERE st.kind='SOURCE' AND menuto_nutrition.source_in_request(st.identity,c);
 IF EXISTS (SELECT FROM jsonb_array_elements(sources) r JOIN public.nutrition_source_principals pr ON pr.id=(r->>'principal_id')::uuid
   WHERE pr.command#>>'{identity_evidence,environment}'<>c->>'environment') THEN
  RAISE EXCEPTION 'Source environment mismatch; no TEST_ONLY/production history mixing'; END IF;
 -- Required finite streams receive protected absence witnesses, even if no row exists.
 i:=jsonb_build_object('kind','GUIDELINE','provider_id',c->'provider_id','family_id',c->'family_id',
  'household_id',NULL,'member_id',NULL,'code','FAMILY');
 required:=required||jsonb_build_array(jsonb_build_object('stream_key',menuto_nutrition.source_key(i),'source_identity',i,'authority_scope',NULL));
 FOREACH code IN ARRAY ARRAY['BODY_MASS','HEIGHT','ENERGY_DIRECTION',c->>'protocol_fingerprint'] LOOP
  kind:=CASE WHEN code IN ('BODY_MASS','HEIGHT') THEN 'OBSERVATION' WHEN code='ENERGY_DIRECTION' THEN 'GOAL' ELSE 'ASSESSMENT' END;
  i:=jsonb_build_object('kind',kind,'provider_id',CASE WHEN kind='ASSESSMENT' THEN c->'provider_id' ELSE 'null'::jsonb END,
   'family_id',CASE WHEN kind='ASSESSMENT' THEN c->'family_id' ELSE 'null'::jsonb END,'household_id',h,'member_id',m,'code',code);
  required:=required||jsonb_build_array(jsonb_build_object('stream_key',menuto_nutrition.source_key(i),'source_identity',i,'authority_scope',NULL));
 END LOOP;
 FOREACH k IN ARRAY authority_keys LOOP
  item:=CASE WHEN k=menuto_nutrition.authority_key(reference_scope) THEN reference_scope ELSE member_scope END;
  required:=required||jsonb_build_array(jsonb_build_object('stream_key',k,'source_identity',NULL,'authority_scope',item));
 END LOOP;
 FOR item IN SELECT jsonb_build_object('stream_key',st.stream_key,'source_identity',st.identity,'authority_scope',NULL)
  FROM public.nutrition_source_streams st WHERE st.kind='SOURCE' AND menuto_nutrition.source_in_request(st.identity,c) LOOP
  IF NOT EXISTS (SELECT FROM jsonb_array_elements(required) q WHERE q->'stream_key'=item->'stream_key') THEN required:=required||jsonb_build_array(item); END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(q||jsonb_build_object('revision',coalesce(st.revision,0),'head_id',st.head_id,'head_hash',st.head_hash)
  ORDER BY q->>'stream_key'),'[]') INTO manifests FROM jsonb_array_elements(required) q
  LEFT JOIN public.nutrition_source_streams st ON st.stream_key=q->>'stream_key';
 IF jsonb_array_length(manifests)>512 THEN RAISE EXCEPTION 'Server stream manifest limit'; END IF;
 SELECT array_agg(DISTINCT id) INTO ids FROM (
  SELECT p.id id UNION SELECT (a#>>'{command,principal_id}')::uuid FROM jsonb_array_elements(authority) a
  UNION SELECT (r->>'principal_id')::uuid FROM jsonb_array_elements(sources) r
  UNION SELECT (r#>>'{command,body,grantee_principal_id}')::uuid FROM jsonb_array_elements(sources) r WHERE r#>>'{command,body,kind}'='DELEGATION'
 ) q;
 IF cardinality(ids)>512 THEN RAISE EXCEPTION 'Server principal manifest limit'; END IF;
 SELECT jsonb_agg(menuto_nutrition.principal_fact(to_jsonb(x)) ORDER BY x.id) INTO principals
  FROM public.nutrition_source_principals x WHERE x.id=ANY(ids);
 SELECT array_agg(DISTINCT id) INTO provider_ids FROM (
  SELECT (c->>'provider_id')::uuid id UNION SELECT (a#>>'{command,scope,provider_id}')::uuid FROM jsonb_array_elements(authority) a
  WHERE a#>>'{command,scope,provider_id}' IS NOT NULL
 ) q;
 SELECT jsonb_agg(menuto_nutrition.provider_fact(to_jsonb(x)) ORDER BY x.provider_id,x.generation) INTO providers
  FROM public.nutrition_source_providers x WHERE x.provider_id=ANY(provider_ids);
 IF jsonb_array_length(providers)>64 THEN RAISE EXCEPTION 'Server enrollment history limit'; END IF;
 rows:=jsonb_array_length(providers)+jsonb_array_length(principals)+jsonb_array_length(authority)+jsonb_array_length(sources)+jsonb_array_length(manifests);
 IF rows>4096 THEN RAISE EXCEPTION 'Server whole capture row limit; all-or-error'; END IF;
 completed:=clock_timestamp();
 IF menuto_nutrition.permission(p.id,read_scope,cap,NULL,NULL,completed)<>reader_grant THEN RAISE EXCEPTION 'Reader grant changed/expired during capture'; END IF;
 frame:=jsonb_build_object('session',s,'reader_principal_id',p.id,'reader_subject_witness',witness,'reader_grant_id',reader_grant,
  'endpoint',host(inet_server_addr())||':'||inet_server_port()::text,'backend_pid',pg_backend_pid(),
  'mvcc_snapshot',pg_current_snapshot()::text,'transaction_id','UNASSIGNED_READ_ONLY',
  'isolation',upper(current_setting('transaction_isolation')),'read_only',true,
  'started_at',menuto_nutrition.utc(started),'completed_at',menuto_nutrition.utc(completed),
  'provider_enrollment_id',provider_binding,'row_count',rows,
  'absence_stream_keys',(SELECT coalesce(jsonb_agg(q->'stream_key' ORDER BY q->>'stream_key'),'[]') FROM jsonb_array_elements(manifests) q WHERE q->>'revision'='0'));
 result:=jsonb_build_object('contract_version','nutrition-root-sources.v1','request',c,'provider_enrollments',providers,
  'principals',principals,'authority',authority,'sources',sources,'streams',manifests,
  'current_legacy_anchor',menuto_nutrition.legacy_anchor(h,m),'capture',frame);
 PERFORM menuto_nutrition.bounds(result,4194304);
 result:=result||jsonb_build_object('source_fingerprint',menuto_nutrition.hash('nutrition.sources.v1',result));
 PERFORM menuto_nutrition.deadline(started);
 RETURN result;
END $$;

CREATE FUNCTION menuto_nutrition.write_guard() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$ BEGIN
 IF current_user<>'menuto_nutrition_owner' OR current_setting('role')<>'none' THEN RAISE EXCEPTION 'Direct Nutrition source DML forbidden' USING ERRCODE='42501'; END IF;
 IF TG_OP='UPDATE' AND TG_TABLE_NAME='nutrition_source_streams' THEN
  IF NEW.stream_key<>OLD.stream_key OR NEW.kind<>OLD.kind OR NEW.identity<>OLD.identity OR NEW.revision<>OLD.revision+1 THEN
   RAISE EXCEPTION 'Only exact protected frontier advancement allowed'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION menuto_nutrition.immutable() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$ BEGIN
 RAISE EXCEPTION 'Immutable Nutrition source history; append a revision';
END $$;
CREATE FUNCTION menuto_nutrition.coherent() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_nutrition,pg_temp AS $$
DECLARE k text; r public.nutrition_source_receipts; st public.nutrition_source_streams; f jsonb; cmd jsonb;
 prev public.nutrition_source_receipts; count_rows bigint; children bigint; domain text; command_domain text; BEGIN
 IF TG_TABLE_NAME='nutrition_source_streams' THEN
  IF NEW.kind='LOCK' THEN RETURN NULL; END IF;
  k:=NEW.stream_key;
 ELSE
  SELECT * INTO STRICT r FROM public.nutrition_source_receipts WHERE id=NEW.id;
  k:=r.stream_key;
  SELECT count(*) INTO children FROM (
   SELECT id FROM public.nutrition_source_authority WHERE id=r.id UNION ALL
   SELECT id FROM public.nutrition_guideline_drafts WHERE id=r.id UNION ALL
   SELECT id FROM public.nutrition_guideline_reviews WHERE id=r.id UNION ALL
   SELECT id FROM public.nutrition_guideline_publications WHERE id=r.id UNION ALL
   SELECT id FROM public.nutrition_member_delegations WHERE id=r.id UNION ALL
   SELECT id FROM public.nutrition_physiology_revisions WHERE id=r.id UNION ALL
   SELECT id FROM public.nutrition_eligibility_revisions WHERE id=r.id UNION ALL
   SELECT id FROM public.nutrition_goal_revisions WHERE id=r.id
  ) q;
  IF children<>1 THEN RAISE EXCEPTION 'Exactly one typed durable receipt child required'; END IF;
  f:=menuto_nutrition.record_fact(r); cmd:=f->'command';
  domain:=CASE WHEN r.kind='AUTHORITY' THEN 'nutrition.authority.v1' ELSE 'nutrition.record.v1' END;
  command_domain:=CASE WHEN r.kind='AUTHORITY' THEN 'nutrition.authority-command.v1' ELSE 'nutrition.source-command.v1' END;
  IF r.fact_hash<>menuto_nutrition.hash(domain,f-'fact_hash') OR r.command_hash<>menuto_nutrition.hash(command_domain,cmd) OR
    r.actor_database_oid<>(r.actor->>'database_oid')::bigint OR r.actor_role_oid<>(r.actor->>'role_oid')::bigint OR
    r.actor->>'authentication_method'<>'scram-sha-256' OR r.actor->>'authenticated_identity'<>r.actor->>'role_name' THEN
   RAISE EXCEPTION 'Incoherent immutable Nutrition receipt/actor identity'; END IF;
  IF r.kind='AUTHORITY' THEN
   PERFORM menuto_nutrition.check_command('NutritionAuthorityCommand',cmd);
   PERFORM menuto_nutrition.check_authority(cmd);
   IF k<>menuto_nutrition.authority_key(cmd->'scope') OR (cmd->>'expected_generation')::bigint<>r.sequence-1
     OR (cmd->>'predecessor_id')::uuid IS DISTINCT FROM r.previous_id THEN RAISE EXCEPTION 'Authority stream lineage mismatch'; END IF;
  ELSE
   PERFORM menuto_nutrition.check_command('NutritionSourceCommand',cmd);
   PERFORM menuto_nutrition.check_source_command(cmd);
   IF k<>menuto_nutrition.source_key(cmd->'identity') THEN RAISE EXCEPTION 'Typed source stream key mismatch'; END IF;
   IF NOT EXISTS (SELECT FROM public.nutrition_source_principals p WHERE p.id=r.principal_id
    AND p.database_oid=r.actor_database_oid AND p.database_name=r.actor->>'database_name'
    AND p.role_oid=r.actor_role_oid AND p.role_name=r.actor->>'role_name') THEN RAISE EXCEPTION 'Canonical author enrollment mismatch'; END IF;
  END IF;
  IF r.previous_id IS NOT NULL THEN
   SELECT * INTO STRICT prev FROM public.nutrition_source_receipts WHERE id=r.previous_id;
   IF prev.stream_key<>k OR prev.sequence<>r.sequence-1 OR prev.fact_hash<>r.previous_hash
     OR prev.recorded_order>=r.recorded_order OR prev.recorded_at>r.recorded_at THEN RAISE EXCEPTION 'Noncontiguous immutable source order'; END IF;
  END IF;
 END IF;
 SELECT * INTO STRICT st FROM public.nutrition_source_streams WHERE stream_key=k;
 SELECT count(*) INTO count_rows FROM public.nutrition_source_receipts WHERE stream_key=k;
 SELECT * INTO r FROM public.nutrition_source_receipts WHERE stream_key=k ORDER BY sequence DESC LIMIT 1;
 IF st.revision<>count_rows OR st.head_id IS DISTINCT FROM r.id OR st.head_hash IS DISTINCT FROM r.fact_hash
  OR coalesce(r.sequence,0)<>st.revision THEN RAISE EXCEPTION 'Atomic event/frontier/receipt invariant violated'; END IF;
 RETURN NULL;
END $$;
DO $$ DECLARE t text; f record; BEGIN
 FOREACH t IN ARRAY ARRAY['nutrition_source_providers','nutrition_source_principals','nutrition_source_streams','nutrition_source_receipts',
  'nutrition_source_authority','nutrition_guideline_drafts','nutrition_guideline_reviews','nutrition_guideline_publications',
  'nutrition_member_delegations','nutrition_physiology_revisions','nutrition_eligibility_revisions','nutrition_goal_revisions','nutrition_source_evidence_artifacts'] LOOP
  EXECUTE format('ALTER TABLE public.%I OWNER TO menuto_nutrition_owner',t);
  EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC,menuto_nutrition_admin,menuto_nutrition_client',t);
  EXECUTE format('CREATE TRIGGER nutrition_source_write_guard BEFORE INSERT ON public.%I FOR EACH ROW EXECUTE FUNCTION menuto_nutrition.write_guard()',t);
  EXECUTE format('CREATE TRIGGER nutrition_source_no_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION menuto_nutrition.immutable()',t);
  IF t='nutrition_source_streams' THEN
   EXECUTE format('CREATE TRIGGER nutrition_source_frontier_guard BEFORE UPDATE ON public.%I FOR EACH ROW EXECUTE FUNCTION menuto_nutrition.write_guard()',t);
   EXECUTE format('CREATE TRIGGER nutrition_source_no_delete BEFORE DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION menuto_nutrition.immutable()',t);
  ELSE
   EXECUTE format('CREATE TRIGGER nutrition_source_immutable BEFORE UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION menuto_nutrition.immutable()',t);
  END IF;
  IF t NOT IN ('nutrition_source_providers','nutrition_source_principals','nutrition_source_evidence_artifacts') THEN
   EXECUTE format('CREATE CONSTRAINT TRIGGER nutrition_source_coherent AFTER INSERT OR UPDATE ON public.%I DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_nutrition.coherent()',t);
  END IF;
 END LOOP;
 ALTER SEQUENCE public.nutrition_source_recorded_order OWNER TO menuto_nutrition_owner;
 REVOKE ALL ON SEQUENCE public.nutrition_source_recorded_order FROM PUBLIC,menuto_nutrition_admin,menuto_nutrition_client;
 FOR f IN SELECT p.oid::regprocedure sig FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='menuto_nutrition' LOOP
  EXECUTE format('ALTER FUNCTION %s OWNER TO menuto_nutrition_owner',f.sig);
  EXECUTE format('REVOKE ALL ON FUNCTION %s FROM PUBLIC,menuto_nutrition_admin,menuto_nutrition_client',f.sig);
 END LOOP;
END $$;
GRANT EXECUTE ON FUNCTION menuto_nutrition.register_provider(jsonb),menuto_nutrition.enroll_principal(jsonb),menuto_nutrition.change_authority(jsonb) TO menuto_nutrition_admin;
GRANT EXECUTE ON FUNCTION menuto_nutrition.append(jsonb),menuto_nutrition.capture(jsonb) TO menuto_nutrition_client;

"""


def upgrade():
    op.execute(TABLE_SQL)
    op.execute(FUNCTION_SQL)


def downgrade():
    op.execute(r"""
    DO $$ DECLARE t text; present boolean; BEGIN
      FOREACH t IN ARRAY ARRAY['nutrition_source_providers','nutrition_source_principals','nutrition_source_streams','nutrition_source_receipts',
        'nutrition_source_authority','nutrition_guideline_drafts','nutrition_guideline_reviews','nutrition_guideline_publications',
        'nutrition_member_delegations','nutrition_physiology_revisions','nutrition_eligibility_revisions','nutrition_goal_revisions','nutrition_source_evidence_artifacts'] LOOP
        EXECUTE format('SELECT EXISTS (SELECT FROM public.%I)',t) INTO present;
        IF present THEN RAISE EXCEPTION 'Refusing destructive downgrade of populated Nutrition source history'; END IF;
      END LOOP;
    END $$;
    REVOKE SELECT ON public.users,public.households,public.household_members,public.memberships,public.member_nutrition_profiles FROM menuto_nutrition_owner;
    DO $$ DECLARE ns name; BEGIN
      SELECT n.nspname INTO ns FROM pg_catalog.pg_extension e JOIN pg_catalog.pg_namespace n ON n.oid=e.extnamespace WHERE e.extname='sslinfo';
      IF ns IS NOT NULL THEN
        EXECUTE format('REVOKE EXECUTE ON FUNCTION %I.ssl_is_used() FROM menuto_nutrition_owner',ns);
        EXECUTE format('REVOKE USAGE ON SCHEMA %I FROM menuto_nutrition_owner',ns);
      END IF;
    END $$;
    DROP SCHEMA menuto_nutrition CASCADE;
    DROP TABLE public.nutrition_source_providers,public.nutrition_source_principals,public.nutrition_source_streams,public.nutrition_source_receipts,
      public.nutrition_source_authority,public.nutrition_guideline_drafts,public.nutrition_guideline_reviews,public.nutrition_guideline_publications,
      public.nutrition_member_delegations,public.nutrition_physiology_revisions,public.nutrition_eligibility_revisions,public.nutrition_goal_revisions,
      public.nutrition_source_evidence_artifacts;
    DROP SEQUENCE public.nutrition_source_recorded_order;
    -- NOLOGIN infrastructure roles have a cluster lifecycle, not a content/enrollment seed.
    """)
