"""Inventory physical ledger. Frozen DDL; never imports live ORM metadata."""

# ruff: noqa: E501 -- frozen DDL and trigger SQL
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

UPGRADE_SQL = r"""
CREATE SEQUENCE inventory_ledger_sequence AS bigint;

CREATE TABLE inventory_lots (
	id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	ingredient_id UUID, 
	asset_type VARCHAR(30) NOT NULL, 
	basis VARCHAR(20) NOT NULL, 
	item_ref VARCHAR(100), 
	acquired_amount NUMERIC NOT NULL, 
	acquired_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT clock_timestamp() NOT NULL, 
	usable_until TIMESTAMP WITH TIME ZONE, 
	observation_confidence VARCHAR(20) NOT NULL, 
	serving_definition VARCHAR(200), 
	retail_product_id UUID, 
	retail_mapping_id UUID, 
	CONSTRAINT pk_inventory_lots PRIMARY KEY (id), 
	CONSTRAINT uq_inventory_lots_household_id_id UNIQUE (household_id, id), 
	CONSTRAINT ck_inventory_lots_quantity_identity CHECK ((basis IN ('COUNT','SERVING') AND item_ref IS NOT NULL AND item_ref ~ '^[A-Za-z0-9_.:-]+$') OR (basis IN ('AP_G','EP_RAW_G','COOKED_G') AND item_ref IS NULL)), 
	CONSTRAINT ck_inventory_lots_acquired_amount_exact CHECK (acquired_amount > 0 AND acquired_amount < 1000000000000 AND acquired_amount = trunc(acquired_amount,6)), 
	CONSTRAINT ck_inventory_lots_confidence CHECK (observation_confidence IN ('CONFIRMED','STALE','UNKNOWN')), 
	CONSTRAINT ck_inventory_lots_times CHECK (isfinite(acquired_at) AND isfinite(created_at) AND (usable_until IS NULL OR (isfinite(usable_until) AND usable_until > acquired_at))), 
	CONSTRAINT ck_inventory_lots_asset_identity CHECK ((asset_type='RAW_INGREDIENT' AND ingredient_id IS NOT NULL AND basis IN ('AP_G','EP_RAW_G','COUNT') AND serving_definition IS NULL) OR (asset_type='PREPARED_COMPONENT' AND ingredient_id IS NOT NULL AND basis='COOKED_G' AND serving_definition IS NULL) OR (asset_type='COOKED_DISH' AND ingredient_id IS NULL AND basis='SERVING' AND serving_definition IS NOT NULL AND length(trim(serving_definition))>0)), 
	CONSTRAINT ck_inventory_lots_retail_origin CHECK ((retail_mapping_id IS NULL AND retail_product_id IS NULL) OR (retail_mapping_id IS NOT NULL AND retail_product_id IS NOT NULL AND asset_type='RAW_INGREDIENT' AND basis='AP_G'))
)

;

CREATE TABLE inventory_lot_balances (
	lot_id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	remaining NUMERIC NOT NULL, 
	reserved NUMERIC NOT NULL, 
	lifecycle_state VARCHAR(20) NOT NULL, 
	revision BIGINT NOT NULL, 
	last_occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	last_phase INTEGER NOT NULL, 
	CONSTRAINT pk_inventory_lot_balances PRIMARY KEY (lot_id), 
	CONSTRAINT ck_inventory_lot_balances_remaining_exact CHECK (remaining >= 0 AND remaining < 1000000000000 AND remaining = trunc(remaining,6)), 
	CONSTRAINT ck_inventory_lot_balances_reserved_exact CHECK (reserved >= 0 AND reserved < 1000000000000 AND reserved = trunc(reserved,6)), 
	CONSTRAINT ck_inventory_lot_balances_reserved_bound CHECK (reserved <= remaining), 
	CONSTRAINT ck_inventory_lot_balances_lifecycle CHECK (lifecycle_state IN ('ACTIVE','DEPLETED','EXPIRED','DISCARDED')), 
	CONSTRAINT ck_inventory_lot_balances_revision CHECK (revision > 0 AND last_phase BETWEEN 0 AND 60)
)

;

CREATE TABLE inventory_movements (
	movement_type VARCHAR(30) NOT NULL, 
	basis VARCHAR(20) NOT NULL, 
	item_ref VARCHAR(100), 
	amount NUMERIC NOT NULL, 
	correction_of UUID, 
	id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	lot_id UUID NOT NULL, 
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE DEFAULT clock_timestamp() NOT NULL, 
	ledger_sequence BIGINT DEFAULT nextval('inventory_ledger_sequence') NOT NULL, 
	phase INTEGER NOT NULL, 
	idempotency_key VARCHAR(100) NOT NULL, 
	command_fingerprint VARCHAR(64) NOT NULL, 
	source_kind VARCHAR(20) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	confirmed_by_user_id UUID NOT NULL, 
	confirmation VARCHAR(20) NOT NULL, 
	reason VARCHAR(200) NOT NULL, 
	CONSTRAINT pk_inventory_movements PRIMARY KEY (id), 
	CONSTRAINT uq_inventory_movements_household_id_source_system_idemp_7f7f UNIQUE (household_id, source_system, idempotency_key), 
	CONSTRAINT uq_inventory_movements_household_id_source_system_exter_a0f2 UNIQUE (household_id, source_system, external_record_id, source_version), 
	CONSTRAINT uq_inventory_movements_ledger_sequence UNIQUE (ledger_sequence), 
	CONSTRAINT ck_inventory_movements_explicit_evidence CHECK (source_kind IN ('USER','RECEIPT','BARCODE','EXECUTION') AND confirmation='EXPLICIT'), 
	CONSTRAINT ck_inventory_movements_identifiers CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$' AND command_fingerprint ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_inventory_movements_source_identity CHECK (length(trim(external_record_id))>0 AND external_record_id !~ '[[:cntrl:]]' AND length(trim(source_version))>0 AND source_version !~ '[[:cntrl:]]' AND length(trim(reason))>0), 
	CONSTRAINT ck_inventory_movements_event_order CHECK (isfinite(occurred_at) AND isfinite(recorded_at) AND occurred_at <= recorded_at AND ledger_sequence>0 AND phase IN (10,20,30,40,50,60)), 
	CONSTRAINT ck_inventory_movements_quantity_identity CHECK ((basis IN ('COUNT','SERVING') AND item_ref IS NOT NULL AND item_ref ~ '^[A-Za-z0-9_.:-]+$') OR (basis IN ('AP_G','EP_RAW_G','COOKED_G') AND item_ref IS NULL)), 
	CONSTRAINT ck_inventory_movements_amount_exact CHECK (amount >= 0 AND amount < 1000000000000 AND amount = trunc(amount,6)), 
	CONSTRAINT uq_inventory_movements_household_id_lot_id_id UNIQUE (household_id, lot_id, id), 
	CONSTRAINT ck_inventory_movements_movement_type CHECK ((movement_type='EXPIRE' AND amount=0) OR (movement_type IN ('ACQUIRE','CONSUME','DISCARD','RECONCILE_INCREASE','RECONCILE_DECREASE') AND amount>0)), 
	CONSTRAINT ck_inventory_movements_correction CHECK (correction_of IS NULL OR movement_type IN ('RECONCILE_INCREASE','RECONCILE_DECREASE'))
)

;

CREATE TABLE inventory_reservations (
	basis VARCHAR(20) NOT NULL, 
	item_ref VARCHAR(100), 
	amount NUMERIC NOT NULL, 
	purpose VARCHAR(200) NOT NULL, 
	id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	lot_id UUID NOT NULL, 
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE DEFAULT clock_timestamp() NOT NULL, 
	ledger_sequence BIGINT DEFAULT nextval('inventory_ledger_sequence') NOT NULL, 
	phase INTEGER NOT NULL, 
	idempotency_key VARCHAR(100) NOT NULL, 
	command_fingerprint VARCHAR(64) NOT NULL, 
	source_kind VARCHAR(20) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	confirmed_by_user_id UUID NOT NULL, 
	confirmation VARCHAR(20) NOT NULL, 
	reason VARCHAR(200) NOT NULL, 
	CONSTRAINT pk_inventory_reservations PRIMARY KEY (id), 
	CONSTRAINT uq_inventory_reservations_household_id_source_system_id_d222 UNIQUE (household_id, source_system, idempotency_key), 
	CONSTRAINT uq_inventory_reservations_household_id_source_system_ex_456e UNIQUE (household_id, source_system, external_record_id, source_version), 
	CONSTRAINT uq_inventory_reservations_ledger_sequence UNIQUE (ledger_sequence), 
	CONSTRAINT ck_inventory_reservations_explicit_evidence CHECK (source_kind IN ('USER','RECEIPT','BARCODE','EXECUTION') AND confirmation='EXPLICIT'), 
	CONSTRAINT ck_inventory_reservations_identifiers CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$' AND command_fingerprint ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_inventory_reservations_source_identity CHECK (length(trim(external_record_id))>0 AND external_record_id !~ '[[:cntrl:]]' AND length(trim(source_version))>0 AND source_version !~ '[[:cntrl:]]' AND length(trim(reason))>0), 
	CONSTRAINT ck_inventory_reservations_event_order CHECK (isfinite(occurred_at) AND isfinite(recorded_at) AND occurred_at <= recorded_at AND ledger_sequence>0 AND phase IN (10,20,30,40,50,60)), 
	CONSTRAINT ck_inventory_reservations_quantity_identity CHECK ((basis IN ('COUNT','SERVING') AND item_ref IS NOT NULL AND item_ref ~ '^[A-Za-z0-9_.:-]+$') OR (basis IN ('AP_G','EP_RAW_G','COOKED_G') AND item_ref IS NULL)), 
	CONSTRAINT ck_inventory_reservations_amount_exact CHECK (amount > 0 AND amount < 1000000000000 AND amount = trunc(amount,6)), 
	CONSTRAINT uq_inventory_reservations_household_id_lot_id_id UNIQUE (household_id, lot_id, id), 
	CONSTRAINT ck_inventory_reservations_purpose CHECK (length(trim(purpose))>0)
)

;

CREATE TABLE inventory_reservation_releases (
	reservation_id UUID NOT NULL, 
	id UUID NOT NULL, 
	household_id UUID NOT NULL, 
	lot_id UUID NOT NULL, 
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE DEFAULT clock_timestamp() NOT NULL, 
	ledger_sequence BIGINT DEFAULT nextval('inventory_ledger_sequence') NOT NULL, 
	phase INTEGER NOT NULL, 
	idempotency_key VARCHAR(100) NOT NULL, 
	command_fingerprint VARCHAR(64) NOT NULL, 
	source_kind VARCHAR(20) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	confirmed_by_user_id UUID NOT NULL, 
	confirmation VARCHAR(20) NOT NULL, 
	reason VARCHAR(200) NOT NULL, 
	CONSTRAINT pk_inventory_reservation_releases PRIMARY KEY (id), 
	CONSTRAINT uq_inventory_reservation_releases_household_id_source_s_a945 UNIQUE (household_id, source_system, idempotency_key), 
	CONSTRAINT uq_inventory_reservation_releases_household_id_source_s_51b7 UNIQUE (household_id, source_system, external_record_id, source_version), 
	CONSTRAINT uq_inventory_reservation_releases_ledger_sequence UNIQUE (ledger_sequence), 
	CONSTRAINT ck_inventory_reservation_releases_explicit_evidence CHECK (source_kind IN ('USER','RECEIPT','BARCODE','EXECUTION') AND confirmation='EXPLICIT'), 
	CONSTRAINT ck_inventory_reservation_releases_identifiers CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$' AND idempotency_key ~ '^[A-Za-z0-9_.:-]+$' AND command_fingerprint ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_inventory_reservation_releases_source_identity CHECK (length(trim(external_record_id))>0 AND external_record_id !~ '[[:cntrl:]]' AND length(trim(source_version))>0 AND source_version !~ '[[:cntrl:]]' AND length(trim(reason))>0), 
	CONSTRAINT ck_inventory_reservation_releases_event_order CHECK (isfinite(occurred_at) AND isfinite(recorded_at) AND occurred_at <= recorded_at AND ledger_sequence>0 AND phase IN (10,20,30,40,50,60)), 
	CONSTRAINT uq_inventory_reservation_releases_reservation_id UNIQUE (reservation_id)
)

;
ALTER TABLE inventory_lots ADD CONSTRAINT fk_inventory_lots_household_id_households FOREIGN KEY(household_id) REFERENCES households (id) ON DELETE RESTRICT;
ALTER TABLE inventory_lots ADD CONSTRAINT fk_inventory_lots_ingredient_id_ingredients FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT;
ALTER TABLE inventory_lots ADD CONSTRAINT fk_inventory_lots_retail_mapping_id_ingredient_product_maps FOREIGN KEY(retail_mapping_id, retail_product_id, ingredient_id) REFERENCES ingredient_product_maps (id, retail_product_id, ingredient_id) ON DELETE RESTRICT;
ALTER TABLE inventory_lot_balances ADD CONSTRAINT fk_inventory_lot_balances_household_id_inventory_lots FOREIGN KEY(household_id, lot_id) REFERENCES inventory_lots (household_id, id) ON DELETE RESTRICT;
ALTER TABLE inventory_movements ADD CONSTRAINT fk_inventory_movements_household_id_inventory_lots FOREIGN KEY(household_id, lot_id) REFERENCES inventory_lots (household_id, id) ON DELETE RESTRICT;
ALTER TABLE inventory_movements ADD CONSTRAINT fk_inventory_movements_household_id_inventory_movements FOREIGN KEY(household_id, lot_id, correction_of) REFERENCES inventory_movements (household_id, lot_id, id) ON DELETE RESTRICT;
ALTER TABLE inventory_movements ADD CONSTRAINT fk_inventory_movements_household_id_memberships FOREIGN KEY(household_id, confirmed_by_user_id) REFERENCES memberships (household_id, user_id) ON DELETE RESTRICT;
ALTER TABLE inventory_reservations ADD CONSTRAINT fk_inventory_reservations_household_id_inventory_lots FOREIGN KEY(household_id, lot_id) REFERENCES inventory_lots (household_id, id) ON DELETE RESTRICT;
ALTER TABLE inventory_reservations ADD CONSTRAINT fk_inventory_reservations_household_id_memberships FOREIGN KEY(household_id, confirmed_by_user_id) REFERENCES memberships (household_id, user_id) ON DELETE RESTRICT;
ALTER TABLE inventory_reservation_releases ADD CONSTRAINT fk_inventory_reservation_releases_household_id_inventory_lots FOREIGN KEY(household_id, lot_id) REFERENCES inventory_lots (household_id, id) ON DELETE RESTRICT;
ALTER TABLE inventory_reservation_releases ADD CONSTRAINT fk_inventory_reservation_releases_household_id_inventor_1e6a FOREIGN KEY(household_id, lot_id, reservation_id) REFERENCES inventory_reservations (household_id, lot_id, id) ON DELETE RESTRICT;
ALTER TABLE inventory_reservation_releases ADD CONSTRAINT fk_inventory_reservation_releases_household_id_memberships FOREIGN KEY(household_id, confirmed_by_user_id) REFERENCES memberships (household_id, user_id) ON DELETE RESTRICT;
-- Inventory-only functions. No frozen recipe/retail functions are replaced.


CREATE FUNCTION menuto_inventory_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'inventory history is append-only' USING ERRCODE='23514';
END $$;

CREATE FUNCTION menuto_inventory_balance_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP IN ('DELETE','TRUNCATE') OR pg_trigger_depth() <> 2 THEN
    RAISE EXCEPTION 'inventory balance is ledger-controlled' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;

CREATE FUNCTION menuto_inventory_begin_lot() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended('inventory.household:'||NEW.household_id::text,0));
  IF NEW.acquired_at > clock_timestamp() THEN
    RAISE EXCEPTION 'future acquisition is not physical stock' USING ERRCODE='23514';
  END IF;
  IF NEW.retail_mapping_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM ingredient_product_maps m WHERE m.id=NEW.retail_mapping_id
      AND m.ingredient_id=NEW.ingredient_id AND m.status='REVIEWED'
  ) THEN
    RAISE EXCEPTION 'retail origin needs reviewed exact mapping' USING ERRCODE='23514';
  END IF;
  NEW.created_at := clock_timestamp();
  RETURN NEW;
END $$;

CREATE FUNCTION menuto_inventory_initialize_balance() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO inventory_lot_balances
    (lot_id,household_id,remaining,reserved,lifecycle_state,revision,last_occurred_at,last_phase)
    VALUES (NEW.id,NEW.household_id,0,0,'DEPLETED',1,NEW.acquired_at,0);
  RETURN NEW;
END $$;

CREATE FUNCTION menuto_inventory_require_opening() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM inventory_movements WHERE lot_id=NEW.id
      AND household_id=NEW.household_id AND movement_type='ACQUIRE'
      AND occurred_at=NEW.acquired_at AND amount=NEW.acquired_amount) THEN
    RAISE EXCEPTION 'lot requires confirmed opening acquisition' USING ERRCODE='23514';
  END IF;
  RETURN NULL;
END $$;

CREATE FUNCTION menuto_inventory_append() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  l inventory_lots%ROWTYPE;
  b inventory_lot_balances%ROWTYPE;
  r inventory_reservations%ROWTYPE;
  k text;
  p integer;
  delta numeric := 0;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended('inventory.household:'||NEW.household_id::text,0));
  SELECT * INTO l FROM inventory_lots WHERE id=NEW.lot_id AND household_id=NEW.household_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'household/lot mismatch' USING ERRCODE='23503';
  END IF;
  -- This row is UPDATED after locking, essential for stale REPEATABLE READ writers.
  SELECT * INTO b FROM inventory_lot_balances WHERE lot_id=l.id FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'missing ledger balance' USING ERRCODE='23514';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM memberships WHERE household_id=NEW.household_id
      AND user_id=NEW.confirmed_by_user_id AND role IN ('OWNER','EDITOR')) THEN
    RAISE EXCEPTION 'physical command requires household editor confirmation' USING ERRCODE='23514';
  END IF;
  k := 'RESERVE';
  IF TG_TABLE_NAME='inventory_movements' THEN k := NEW.movement_type; END IF;
  p := CASE WHEN k='ACQUIRE' THEN CASE WHEN l.asset_type='RAW_INGREDIENT' THEN 10 ELSE 40 END
            WHEN k='CONSUME' THEN CASE WHEN l.asset_type='RAW_INGREDIENT' THEN 30 ELSE 50 END
            WHEN k IN ('DISCARD','EXPIRE') THEN 60 ELSE 20 END;
  NEW.recorded_at := clock_timestamp();
  NEW.phase := p;
  NEW.ledger_sequence := nextval('inventory_ledger_sequence');
  IF NOT isfinite(NEW.occurred_at) OR NEW.occurred_at > NEW.recorded_at OR
     (NEW.occurred_at,p) < (b.last_occurred_at,b.last_phase) THEN
    RAISE EXCEPTION 'nonchronological or future inventory event' USING ERRCODE='23514';
  END IF;
  IF TG_TABLE_NAME <> 'inventory_reservation_releases' THEN
    IF NEW.basis <> l.basis OR NEW.item_ref IS DISTINCT FROM l.item_ref THEN
      RAISE EXCEPTION 'movement quantity identity mismatch' USING ERRCODE='23514';
    END IF;
  END IF;
  IF TG_TABLE_NAME='inventory_movements' THEN
    IF k='ACQUIRE' THEN
      IF b.revision <> 1 OR NEW.amount <> l.acquired_amount OR NEW.occurred_at <> l.acquired_at THEN
        RAISE EXCEPTION 'opening acquisition mismatch or duplicate' USING ERRCODE='23514';
      END IF;
    ELSIF b.revision=1 THEN
      RAISE EXCEPTION 'movement before acquisition' USING ERRCODE='23514';
    END IF;
    IF k='CONSUME' AND (b.lifecycle_state='EXPIRED' OR
        (l.usable_until IS NOT NULL AND NEW.occurred_at >= l.usable_until)) THEN
      RAISE EXCEPTION 'cannot consume expired asset' USING ERRCODE='23514';
    END IF;
    IF NEW.correction_of IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM inventory_movements m WHERE m.id=NEW.correction_of
        AND m.household_id=NEW.household_id AND m.lot_id=NEW.lot_id
        AND (m.occurred_at,m.phase,m.ledger_sequence)<(NEW.occurred_at,p,NEW.ledger_sequence)
    ) THEN
      RAISE EXCEPTION 'correction needs prior same-lot evidence' USING ERRCODE='23514';
    END IF;
    IF k='EXPIRE' THEN
      IF l.usable_until IS NULL OR NEW.occurred_at < l.usable_until OR b.remaining=0 THEN
        RAISE EXCEPTION 'expiry needs remaining material and resolved expiry' USING ERRCODE='23514';
      END IF;
      b.lifecycle_state := 'EXPIRED';
      IF b.reserved>0 THEN
        RAISE EXCEPTION 'release reservations before explicit expiry' USING ERRCODE='23514';
      END IF;
    ELSE
      delta := CASE WHEN k IN ('ACQUIRE','RECONCILE_INCREASE') THEN NEW.amount ELSE -NEW.amount END;
      b.remaining := b.remaining + delta;
      IF b.remaining=0 THEN
        b.lifecycle_state := CASE WHEN k='DISCARD' THEN 'DISCARDED' ELSE 'DEPLETED' END;
      ELSIF b.lifecycle_state <> 'EXPIRED' THEN
        b.lifecycle_state := 'ACTIVE';
      END IF;
    END IF;
  ELSIF TG_TABLE_NAME='inventory_reservations' THEN
    IF b.revision=1 OR b.lifecycle_state <> 'ACTIVE' OR
        (l.usable_until IS NOT NULL AND NEW.occurred_at >= l.usable_until) THEN
      RAISE EXCEPTION 'reservation requires usable acquired stock' USING ERRCODE='23514';
    END IF;
    b.reserved := b.reserved+NEW.amount;
  ELSE
    SELECT * INTO r FROM inventory_reservations WHERE id=NEW.reservation_id
      AND household_id=l.household_id AND lot_id=l.id;
    IF NOT FOUND OR EXISTS (SELECT 1 FROM inventory_reservation_releases
        WHERE reservation_id=NEW.reservation_id) THEN
      RAISE EXCEPTION 'release requires active same-lot reservation' USING ERRCODE='23514';
    END IF;
    b.reserved := b.reserved-r.amount;
  END IF;
  IF b.remaining < 0 OR b.reserved < 0 OR b.remaining < b.reserved THEN
    RAISE EXCEPTION 'insufficient unreserved physical stock' USING ERRCODE='23514';
  END IF;
  UPDATE inventory_lot_balances SET remaining=b.remaining,reserved=b.reserved,
    lifecycle_state=b.lifecycle_state,revision=b.revision+1,
    last_occurred_at=NEW.occurred_at,last_phase=p WHERE lot_id=l.id;
  RETURN NEW;
END $$;

CREATE TRIGGER inventory_history_guard BEFORE UPDATE OR DELETE ON inventory_lots
FOR EACH ROW EXECUTE FUNCTION menuto_inventory_immutable();
CREATE TRIGGER inventory_history_truncate BEFORE TRUNCATE ON inventory_lots
FOR EACH STATEMENT EXECUTE FUNCTION menuto_inventory_immutable();
CREATE TRIGGER inventory_balance_guard BEFORE INSERT OR UPDATE OR DELETE ON inventory_lot_balances
FOR EACH ROW EXECUTE FUNCTION menuto_inventory_balance_guard();
CREATE TRIGGER inventory_balance_truncate BEFORE TRUNCATE ON inventory_lot_balances
FOR EACH STATEMENT EXECUTE FUNCTION menuto_inventory_balance_guard();
CREATE TRIGGER inventory_history_guard BEFORE UPDATE OR DELETE ON inventory_movements
FOR EACH ROW EXECUTE FUNCTION menuto_inventory_immutable();
CREATE TRIGGER inventory_history_truncate BEFORE TRUNCATE ON inventory_movements
FOR EACH STATEMENT EXECUTE FUNCTION menuto_inventory_immutable();
CREATE TRIGGER inventory_history_guard BEFORE UPDATE OR DELETE ON inventory_reservations
FOR EACH ROW EXECUTE FUNCTION menuto_inventory_immutable();
CREATE TRIGGER inventory_history_truncate BEFORE TRUNCATE ON inventory_reservations
FOR EACH STATEMENT EXECUTE FUNCTION menuto_inventory_immutable();
CREATE TRIGGER inventory_history_guard BEFORE UPDATE OR DELETE ON inventory_reservation_releases
FOR EACH ROW EXECUTE FUNCTION menuto_inventory_immutable();
CREATE TRIGGER inventory_history_truncate BEFORE TRUNCATE ON inventory_reservation_releases
FOR EACH STATEMENT EXECUTE FUNCTION menuto_inventory_immutable();
CREATE TRIGGER inventory_begin_lot BEFORE INSERT ON inventory_lots
FOR EACH ROW EXECUTE FUNCTION menuto_inventory_begin_lot();
CREATE TRIGGER inventory_initialize_balance AFTER INSERT ON inventory_lots
FOR EACH ROW EXECUTE FUNCTION menuto_inventory_initialize_balance();
CREATE CONSTRAINT TRIGGER inventory_require_opening AFTER INSERT ON inventory_lots
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION menuto_inventory_require_opening();
CREATE TRIGGER inventory_append BEFORE INSERT ON inventory_movements
FOR EACH ROW EXECUTE FUNCTION menuto_inventory_append();
CREATE TRIGGER inventory_append BEFORE INSERT ON inventory_reservations
FOR EACH ROW EXECUTE FUNCTION menuto_inventory_append();
CREATE TRIGGER inventory_append BEFORE INSERT ON inventory_reservation_releases
FOR EACH ROW EXECUTE FUNCTION menuto_inventory_append();
"""

DOWNGRADE_SQL = r"""
LOCK TABLE inventory_lots,inventory_lot_balances,inventory_movements,
inventory_reservations,inventory_reservation_releases IN ACCESS EXCLUSIVE MODE;
DO $$ BEGIN
IF EXISTS (SELECT 1 FROM inventory_lots) OR EXISTS (SELECT 1 FROM inventory_movements)
OR EXISTS (SELECT 1 FROM inventory_reservations) OR EXISTS (SELECT 1 FROM inventory_reservation_releases)
THEN RAISE EXCEPTION '0007 downgrade would lose physical history' USING ERRCODE='23514';
END IF; END $$;
DROP TABLE inventory_reservation_releases;
DROP TABLE inventory_reservations;
DROP TABLE inventory_movements;
DROP TABLE inventory_lot_balances;
DROP TABLE inventory_lots;
DROP SEQUENCE inventory_ledger_sequence;
DROP FUNCTION menuto_inventory_append();
DROP FUNCTION menuto_inventory_require_opening();
DROP FUNCTION menuto_inventory_initialize_balance();
DROP FUNCTION menuto_inventory_begin_lot();
DROP FUNCTION menuto_inventory_balance_guard();
DROP FUNCTION menuto_inventory_immutable();
"""


def upgrade():
    op.execute(UPGRADE_SQL)


def downgrade():
    op.execute(DOWNGRADE_SQL)
