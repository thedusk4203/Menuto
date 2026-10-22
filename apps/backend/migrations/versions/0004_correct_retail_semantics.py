"""Correct M1.1 canonical reference calibration and structural evidence semantics.

Revision ID: 0004
Revises: 0003
Frozen SQL only. Legacy miscalibrated quotes/ambiguous product mappings abort upgrade.
Legacy option flags are archived; retailer status is migrated without inventing evidence.
"""

# ruff: noqa: E501 -- frozen DDL and trigger SQL
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

OLD_TABLES = (
    "reference_price_books",
    "retailers",
    "procurement_classes",
    "reference_price_entries",
    "retail_products",
    "store_regions",
    "ingredient_product_maps",
    "retail_packages",
    "retail_price_calibrations",
    "price_observations",
    "procurement_class_members",
    "planning_price_quotes",
    "planning_procurement_options",
)
NEW_TABLES = ("retailer_status_facts", "retail_legacy_option_assessments")

NEW_DDL = (
    """
CREATE TABLE retailer_status_facts (
	retailer_id UUID NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	effective_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_retailer_status_facts PRIMARY KEY (id), 
	CONSTRAINT ck_retailer_status_facts_source_kind CHECK (source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT','LEGACY_STATE')), 
	CONSTRAINT ck_retailer_status_facts_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_retailer_status_facts_source_identity CHECK (length(trim(external_record_id)) > 0 AND length(trim(source_version)) > 0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_retailer_status_facts_observed_at_finite CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_retailer_status_facts_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_retailer_status_facts_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_retailer_status_facts_source_system_external_record__fb4d UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_retailer_status_facts_retailer_id_effective_at UNIQUE (retailer_id, effective_at), 
	CONSTRAINT ck_retailer_status_facts_status CHECK (status IN ('ACTIVE','INACTIVE')), 
	CONSTRAINT ck_retailer_status_facts_effective_at_finite CHECK (isfinite(effective_at)), 
	CONSTRAINT fk_retailer_status_facts_retailer_id_retailers FOREIGN KEY(retailer_id) REFERENCES retailers (id) ON DELETE RESTRICT
)
    """,
    """
CREATE TABLE retail_legacy_option_assessments (
	option_id UUID NOT NULL, 
	legacy_depends_on_single_source BOOLEAN NOT NULL, 
	legacy_depends_on_promotion BOOLEAN NOT NULL, 
	captured_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_retail_legacy_option_assessments PRIMARY KEY (option_id), 
	CONSTRAINT fk_retail_legacy_option_assessments_option_id_planning__5dd3 FOREIGN KEY(option_id) REFERENCES planning_procurement_options (id) ON DELETE RESTRICT
)
    """,
)

QUOTE_CHECK = """
CREATE OR REPLACE FUNCTION menuto_retail_check_quote() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    mapping ingredient_product_maps%ROWTYPE;
    pack retail_packages%ROWTYPE;
    obs price_observations%ROWTYPE;
    cal retail_price_calibrations%ROWTYPE;
    ref reference_price_entries%ROWTYPE;
    book reference_price_books%ROWTYPE;
    expected_amount numeric;
    expected_quantity numeric;
    expected_currency text;
BEGIN
    IF NEW.observation_id IS NOT NULL AND NEW.calibration_id IS NOT NULL THEN
        RAISE EXCEPTION 'Calibration is reference-only' USING ERRCODE = '23514';
    END IF;
    SELECT * INTO mapping FROM ingredient_product_maps WHERE id=NEW.mapping_id;
    SELECT * INTO pack FROM retail_packages WHERE id=NEW.package_id;
    IF mapping.status <> 'REVIEWED' OR NEW.as_of < mapping.reviewed_at
        OR NEW.as_of < pack.observed_at THEN
        RAISE EXCEPTION 'Quote mapping review/package time mismatch' USING ERRCODE = '23514';
    END IF;
    IF NEW.observation_id IS NOT NULL THEN
        SELECT * INTO obs FROM price_observations WHERE id=NEW.observation_id;
        expected_amount := obs.amount_minor;
        expected_quantity := obs.priced_ap_g;
        expected_currency := obs.currency;
        IF NEW.as_of < obs.observed_at THEN
            RAISE EXCEPTION 'Quote predates observation' USING ERRCODE = '23514';
        END IF;
    ELSIF NEW.reference_entry_id IS NOT NULL THEN
        SELECT * INTO ref FROM reference_price_entries WHERE id=NEW.reference_entry_id;
        SELECT * INTO book FROM reference_price_books WHERE id=ref.book_id;
        expected_amount := ref.amount_minor;
        expected_quantity := ref.priced_ap_g;
        expected_currency := ref.currency;
        IF ref.ingredient_id <> NEW.ingredient_id OR book.region_code <> NEW.region_code
            OR NEW.as_of < book.observed_at THEN
            RAISE EXCEPTION 'Reference ingredient/region/time mismatch' USING ERRCODE = '23514';
        END IF;
        IF NEW.calibration_id IS NOT NULL THEN
            SELECT * INTO cal FROM retail_price_calibrations WHERE id=NEW.calibration_id;
            expected_amount := expected_amount * cal.factor;
            IF NEW.as_of < cal.observed_at THEN
                RAISE EXCEPTION 'Quote predates calibration' USING ERRCODE = '23514';
            END IF;
        END IF;
    END IF;
    IF NEW.reference_amount_minor IS DISTINCT FROM expected_amount
        OR NEW.currency IS DISTINCT FROM expected_currency
        OR NEW.reference_ap_g IS DISTINCT FROM expected_quantity THEN
        RAISE EXCEPTION 'Quote must recompute source money/currency/quantity without rounding'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;


"""

LEGACY_QUOTE_CHECK = """
CREATE OR REPLACE FUNCTION menuto_retail_check_quote() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    mapping ingredient_product_maps%ROWTYPE;
    pack retail_packages%ROWTYPE;
    obs price_observations%ROWTYPE;
    cal retail_price_calibrations%ROWTYPE;
    ref reference_price_entries%ROWTYPE;
    book reference_price_books%ROWTYPE;
    expected_amount numeric;
    expected_quantity numeric;
    expected_currency text;
BEGIN
    SELECT * INTO mapping FROM ingredient_product_maps WHERE id=NEW.mapping_id;
    SELECT * INTO pack FROM retail_packages WHERE id=NEW.package_id;
    IF mapping.status <> 'REVIEWED' OR NEW.as_of < mapping.reviewed_at
        OR NEW.as_of < pack.observed_at THEN
        RAISE EXCEPTION 'Quote mapping review/package time mismatch' USING ERRCODE = '23514';
    END IF;
    IF NEW.observation_id IS NOT NULL THEN
        SELECT * INTO obs FROM price_observations WHERE id=NEW.observation_id;
        expected_amount := obs.amount_minor;
        expected_quantity := obs.priced_ap_g;
        expected_currency := obs.currency;
        IF NEW.as_of < obs.observed_at THEN
            RAISE EXCEPTION 'Quote predates observation' USING ERRCODE = '23514';
        END IF;
        IF NEW.calibration_id IS NOT NULL THEN
            SELECT * INTO cal FROM retail_price_calibrations WHERE id=NEW.calibration_id;
            expected_amount := expected_amount * cal.factor;
            IF NEW.as_of < cal.observed_at THEN
                RAISE EXCEPTION 'Quote predates calibration' USING ERRCODE = '23514';
            END IF;
        END IF;
    ELSIF NEW.reference_entry_id IS NOT NULL THEN
        SELECT * INTO ref FROM reference_price_entries WHERE id=NEW.reference_entry_id;
        SELECT * INTO book FROM reference_price_books WHERE id=ref.book_id;
        expected_amount := ref.amount_minor;
        expected_quantity := ref.priced_ap_g;
        expected_currency := ref.currency;
        IF ref.ingredient_id <> NEW.ingredient_id OR book.region_code <> NEW.region_code
            OR NEW.as_of < book.observed_at THEN
            RAISE EXCEPTION 'Reference ingredient/region/time mismatch' USING ERRCODE = '23514';
        END IF;
    END IF;
    IF NEW.amount_minor IS DISTINCT FROM expected_amount
        OR NEW.currency IS DISTINCT FROM expected_currency
        OR NEW.priced_ap_g IS DISTINCT FROM expected_quantity THEN
        RAISE EXCEPTION 'Quote must recompute source money/currency/quantity without rounding'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;


"""


def upgrade():
    op.execute("LOCK TABLE " + ", ".join(OLD_TABLES) + " IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM planning_price_quotes WHERE evidence_kind='CALIBRATED') THEN
                RAISE EXCEPTION '0004: legacy observation-calibrated quotes require explicit archival/rederivation from real reference evidence'
                    USING ERRCODE = '23514';
            END IF;
            IF EXISTS (
                SELECT p.id FROM retail_products p
                LEFT JOIN ingredient_product_maps m ON m.retail_product_id=p.id
                GROUP BY p.id HAVING count(DISTINCT m.ingredient_id) <> 1
            ) THEN
                RAISE EXCEPTION '0004: every existing product needs one unambiguous canonical ingredient before migration'
                    USING ERRCODE = '23514';
            END IF;
        END $$;
    """)
    for statement in NEW_DDL:
        op.execute(statement)
    op.execute("""
        INSERT INTO retailer_status_facts
            (id,retailer_id,status,effective_at,created_at,source_kind,source_system,
             external_record_id,source_version,observed_at)
        SELECT md5('menuto:0004:status:' || id::text)::uuid,id,status,created_at,now(),
            'LEGACY_STATE','menuto.migration.0004',id::text,'retailer-status.0003',created_at
        FROM retailers;
        ALTER TABLE retailers DROP CONSTRAINT ck_retailers_status;
        ALTER TABLE retailers DROP COLUMN status;

        ALTER TABLE retail_products ADD COLUMN canonical_ingredient_id uuid;
        ALTER TABLE retail_products DISABLE TRIGGER retail_products_immutable;
        UPDATE retail_products p SET canonical_ingredient_id=m.ingredient_id
            FROM (SELECT DISTINCT retail_product_id,ingredient_id FROM ingredient_product_maps) m
            WHERE p.id=m.retail_product_id;
        ALTER TABLE retail_products ENABLE TRIGGER retail_products_immutable;
        ALTER TABLE retail_products ALTER COLUMN canonical_ingredient_id SET NOT NULL;
    """)
    op.execute(
        "ALTER TABLE retail_products ADD CONSTRAINT fk_retail_products_canonical_ingredient_id_ingredients FOREIGN KEY(canonical_ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT"
    )
    op.execute(
        "ALTER TABLE retail_products ADD CONSTRAINT uq_retail_products_id_canonical_ingredient_id UNIQUE (id, canonical_ingredient_id)"
    )
    op.execute(
        "ALTER TABLE ingredient_product_maps ADD CONSTRAINT fk_retail_products_bbedc803f324 FOREIGN KEY(retail_product_id, ingredient_id) REFERENCES retail_products (id, canonical_ingredient_id) ON DELETE RESTRICT"
    )
    op.execute("""
        INSERT INTO retail_legacy_option_assessments
            (option_id,legacy_depends_on_single_source,legacy_depends_on_promotion)
        SELECT id,depends_on_single_source,depends_on_promotion FROM planning_procurement_options;
        ALTER TABLE planning_procurement_options DROP COLUMN depends_on_single_source;
        ALTER TABLE planning_procurement_options DROP COLUMN depends_on_promotion;
        ALTER TABLE planning_procurement_options ADD COLUMN brittleness_policy_version varchar(100);
        ALTER TABLE planning_procurement_options DISABLE TRIGGER planning_procurement_options_immutable;
        UPDATE planning_procurement_options SET brittleness_policy_version='legacy-unversioned.0003';
        ALTER TABLE planning_procurement_options ENABLE TRIGGER planning_procurement_options_immutable;
        ALTER TABLE planning_procurement_options ALTER COLUMN brittleness_policy_version SET NOT NULL;
        ALTER TABLE planning_procurement_options ADD CONSTRAINT ck_planning_procurement_options_brittleness_policy_version
            CHECK (brittleness_policy_version ~ '^[A-Za-z0-9_.:-]+$');

        ALTER TABLE planning_price_quotes RENAME COLUMN amount_minor TO reference_amount_minor;
        ALTER TABLE planning_price_quotes RENAME COLUMN priced_ap_g TO reference_ap_g;
        ALTER TABLE planning_price_quotes RENAME CONSTRAINT ck_planning_price_quotes_priced_ap_g_stored_positive TO ck_planning_price_quotes_reference_ap_g_stored_positive;
        ALTER TABLE planning_price_quotes ADD COLUMN price_basis varchar(30) NOT NULL DEFAULT 'REFERENCE_WEIGHT_RATE';
        ALTER TABLE planning_price_quotes ALTER COLUMN price_basis DROP DEFAULT;
        ALTER TABLE planning_price_quotes ADD CONSTRAINT ck_planning_price_quotes_price_basis CHECK (price_basis='REFERENCE_WEIGHT_RATE');
        ALTER TABLE planning_price_quotes DROP CONSTRAINT ck_planning_price_quotes_exclusive_origin;
    """)
    op.execute(
        "ALTER TABLE planning_price_quotes ADD CONSTRAINT ck_planning_price_quotes_exclusive_origin CHECK ((evidence_kind='RETAIL_OBSERVED' AND observation_id IS NOT NULL AND calibration_id IS NULL AND reference_entry_id IS NULL) OR (evidence_kind='CALIBRATED_REFERENCE' AND observation_id IS NULL AND calibration_id IS NOT NULL AND reference_entry_id IS NOT NULL) OR (evidence_kind='REFERENCE_BASELINE' AND observation_id IS NULL AND calibration_id IS NULL AND reference_entry_id IS NOT NULL))"
    )
    op.execute(QUOTE_CHECK)
    op.execute(
        "CREATE TRIGGER retail_legacy_assessments_closed BEFORE INSERT ON retail_legacy_option_assessments "
        "FOR EACH ROW EXECUTE FUNCTION menuto_retail_reject_mutation()"
    )
    for table in NEW_TABLES:
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION menuto_retail_reject_mutation()"
        )
        op.execute(
            f"CREATE TRIGGER {table}_no_truncate BEFORE TRUNCATE ON {table} "
            "FOR EACH STATEMENT EXECUTE FUNCTION menuto_retail_reject_mutation()"
        )


def downgrade():
    op.execute("LOCK TABLE " + ", ".join((*OLD_TABLES, *NEW_TABLES)) + " IN ACCESS EXCLUSIVE MODE")
    for table in (*OLD_TABLES, *NEW_TABLES):
        op.execute(
            "DO $$ BEGIN IF EXISTS (SELECT 1 FROM " + table + ") THEN "
            "RAISE EXCEPTION '0004 downgrade cannot preserve populated corrected retail semantics; explicit archival/migration required' "
            "USING ERRCODE = '23514'; END IF; END $$"
        )
    op.execute(
        "ALTER TABLE ingredient_product_maps DROP CONSTRAINT fk_retail_products_bbedc803f324"
    )
    op.execute(
        "ALTER TABLE planning_price_quotes DROP CONSTRAINT ck_planning_price_quotes_exclusive_origin; ALTER TABLE planning_price_quotes ADD CONSTRAINT ck_planning_price_quotes_exclusive_origin CHECK ((evidence_kind='RETAIL_OBSERVED' AND observation_id IS NOT NULL AND calibration_id IS NULL AND reference_entry_id IS NULL) OR (evidence_kind='CALIBRATED' AND observation_id IS NOT NULL AND calibration_id IS NOT NULL AND reference_entry_id IS NULL) OR (evidence_kind='REFERENCE_BASELINE' AND observation_id IS NULL AND calibration_id IS NULL AND reference_entry_id IS NOT NULL));"
    )
    op.execute("""
        ALTER TABLE planning_price_quotes DROP CONSTRAINT ck_planning_price_quotes_price_basis;
        ALTER TABLE planning_price_quotes DROP COLUMN price_basis;
        ALTER TABLE planning_price_quotes RENAME COLUMN reference_amount_minor TO amount_minor;
        ALTER TABLE planning_price_quotes RENAME COLUMN reference_ap_g TO priced_ap_g;
        ALTER TABLE planning_price_quotes RENAME CONSTRAINT ck_planning_price_quotes_reference_ap_g_stored_positive TO ck_planning_price_quotes_priced_ap_g_stored_positive;
        ALTER TABLE planning_procurement_options DROP CONSTRAINT ck_planning_procurement_options_brittleness_policy_version;
        ALTER TABLE planning_procurement_options DROP COLUMN brittleness_policy_version;
        ALTER TABLE planning_procurement_options ADD COLUMN depends_on_single_source boolean NOT NULL;
        ALTER TABLE planning_procurement_options ADD COLUMN depends_on_promotion boolean NOT NULL;
        ALTER TABLE retail_products DROP CONSTRAINT uq_retail_products_id_canonical_ingredient_id;
        ALTER TABLE retail_products DROP CONSTRAINT fk_retail_products_canonical_ingredient_id_ingredients;
        ALTER TABLE retail_products DROP COLUMN canonical_ingredient_id;
        ALTER TABLE retailers ADD COLUMN status varchar(20) NOT NULL;
        ALTER TABLE retailers ADD CONSTRAINT ck_retailers_status CHECK (status IN ('ACTIVE','INACTIVE'));
    """)
    op.execute(LEGACY_QUOTE_CHECK)
    for table in reversed(NEW_TABLES):
        op.drop_table(table)
