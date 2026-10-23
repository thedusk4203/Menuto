"""Reject false representative authorship; restore frozen 0011 behavior on downgrade.

Only the append function changes. Existing history, hashes, ACLs and trigger identity
remain intact; both definitions below are frozen SQL, independent of ORM/migrations.
"""

# ruff: noqa: E501 -- frozen SQL
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

UPGRADE_SQL = r"""
CREATE OR REPLACE FUNCTION menuto_preference_append() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE membership_row record; stream_row record; prior_action text; target jsonb; payload jsonb;
BEGIN
 SELECT member_id,role INTO membership_row FROM memberships WHERE household_id=NEW.household_id AND user_id=NEW.actor_user_id FOR SHARE;
 IF NOT FOUND OR membership_row.role NOT IN ('OWNER','EDITOR') THEN RAISE EXCEPTION 'Preference actor cannot write' USING ERRCODE='23514'; END IF;
 IF NEW.authorship='SELF' AND membership_row.member_id IS DISTINCT FROM NEW.member_id THEN RAISE EXCEPTION 'SELF actor differs from subject' USING ERRCODE='23514'; END IF;
 IF NEW.authorship='AUTHORIZED_REPRESENTATIVE' AND membership_row.member_id IS NOT DISTINCT FROM NEW.member_id THEN RAISE EXCEPTION 'AUTHORIZED_REPRESENTATIVE actor equals subject; use SELF' USING ERRCODE='23514'; END IF;
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
"""

DOWNGRADE_SQL = r"""
CREATE OR REPLACE FUNCTION menuto_preference_append() RETURNS trigger LANGUAGE plpgsql AS $$
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
"""


def upgrade():
    op.execute(UPGRADE_SQL)


def downgrade():
    op.execute(DOWNGRADE_SQL)
