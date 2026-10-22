"""M1.1 retail/procurement evidence; frozen DDL, no mutable metadata imports.

Revision ID: 0003
Revises: 0002
Downgrade refuses to drop ANY populated M1.1 table, including derived draft evidence.
"""

# ruff: noqa: E501 -- frozen generated SQL

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

TABLES = (
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

DDL = (
    """
CREATE TABLE reference_price_books (
	code VARCHAR(100) NOT NULL, 
	version VARCHAR(100) NOT NULL, 
	region_code VARCHAR(100) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_reference_price_books PRIMARY KEY (id), 
	CONSTRAINT ck_reference_price_books_source_kind CHECK (source_kind = 'REVIEWED_REFERENCE'), 
	CONSTRAINT ck_reference_price_books_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_reference_price_books_source_identity CHECK (length(trim(external_record_id)) > 0 AND length(trim(source_version)) > 0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_reference_price_books_observed_at_finite CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_reference_price_books_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_reference_price_books_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_reference_price_books_source_system_external_record__c8e9 UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_reference_price_books_code_version UNIQUE (code, version), 
	CONSTRAINT ck_reference_price_books_code CHECK (code ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_reference_price_books_version CHECK (version ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_reference_price_books_region_code CHECK (region_code ~ '^[A-Za-z0-9_.:-]+$')
)
    """,
    """
CREATE TABLE retailers (
	name VARCHAR(200) NOT NULL, 
	country VARCHAR(2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_retailers PRIMARY KEY (id), 
	CONSTRAINT ck_retailers_name CHECK (length(trim(name)) > 0), 
	CONSTRAINT ck_retailers_country CHECK (country ~ '^[A-Z]{2}$'), 
	CONSTRAINT ck_retailers_currency CHECK (currency ~ '^[A-Z]{3}$'), 
	CONSTRAINT ck_retailers_status CHECK (status IN ('ACTIVE','INACTIVE')), 
	CONSTRAINT uq_retailers_id_currency UNIQUE (id, currency)
)
    """,
    """
CREATE TABLE procurement_classes (
	code VARCHAR(100) NOT NULL, 
	version VARCHAR(100) NOT NULL, 
	ingredient_id UUID NOT NULL, 
	granularity VARCHAR(20) NOT NULL, 
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
	CONSTRAINT pk_procurement_classes PRIMARY KEY (id), 
	CONSTRAINT ck_procurement_classes_source_kind CHECK (source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')), 
	CONSTRAINT ck_procurement_classes_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_procurement_classes_source_identity CHECK (length(trim(external_record_id)) > 0 AND length(trim(source_version)) > 0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_procurement_classes_observed_at_finite CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_procurement_classes_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_procurement_classes_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_procurement_classes_source_system_external_record_id_4876 UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_procurement_classes_code_version UNIQUE (code, version), 
	CONSTRAINT uq_procurement_classes_id_ingredient_id_granularity UNIQUE (id, ingredient_id, granularity), 
	CONSTRAINT uq_procurement_classes_id_ingredient_id UNIQUE (id, ingredient_id), 
	CONSTRAINT ck_procurement_classes_code CHECK (code ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_procurement_classes_version CHECK (version ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_procurement_classes_granularity CHECK (granularity IN ('FIXED_PACK','CATCH_WEIGHT','LOOSE_SCALE')), 
	CONSTRAINT ck_procurement_classes_draft_only CHECK (status='DRAFT'), 
	CONSTRAINT fk_procurement_classes_ingredient_id_ingredients FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT
)
    """,
    """
CREATE TABLE reference_price_entries (
	book_id UUID NOT NULL, 
	ingredient_id UUID NOT NULL, 
	amount_minor BIGINT NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	priced_ap_g NUMERIC NOT NULL, 
	basis VARCHAR(20) NOT NULL, 
	confidence VARCHAR(20) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_reference_price_entries PRIMARY KEY (id), 
	CONSTRAINT ck_reference_price_entries_money_nonnegative CHECK (amount_minor >= 0), 
	CONSTRAINT ck_reference_price_entries_currency CHECK (currency ~ '^[A-Z]{3}$'), 
	CONSTRAINT ck_reference_price_entries_priced_ap_g_stored_positive CHECK (priced_ap_g > 0 AND priced_ap_g < 1000000000000 AND priced_ap_g = trunc(priced_ap_g,6)), 
	CONSTRAINT uq_reference_price_entries_book_id_ingredient_id_currency UNIQUE (book_id, ingredient_id, currency), 
	CONSTRAINT ck_reference_price_entries_basis CHECK (basis='AP_G'), 
	CONSTRAINT ck_reference_price_entries_confidence CHECK (confidence IN ('UNKNOWN','LOW','MEDIUM','HIGH')), 
	CONSTRAINT fk_reference_price_entries_book_id_reference_price_books FOREIGN KEY(book_id) REFERENCES reference_price_books (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_reference_price_entries_ingredient_id_ingredients FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT
)
    """,
    """
CREATE TABLE retail_products (
	retailer_id UUID NOT NULL, 
	sku VARCHAR(100) NOT NULL, 
	version VARCHAR(100) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	brand VARCHAR(200), 
	category VARCHAR(100) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_retail_products PRIMARY KEY (id), 
	CONSTRAINT ck_retail_products_source_kind CHECK (source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')), 
	CONSTRAINT ck_retail_products_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_retail_products_source_identity CHECK (length(trim(external_record_id)) > 0 AND length(trim(source_version)) > 0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_retail_products_observed_at_finite CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_retail_products_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_retail_products_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_retail_products_source_system_external_record_id_sou_12d7 UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_retail_products_retailer_id_sku_version UNIQUE (retailer_id, sku, version), 
	CONSTRAINT uq_retail_products_id_retailer_id UNIQUE (id, retailer_id), 
	CONSTRAINT uq_retail_products_id_category UNIQUE (id, category), 
	CONSTRAINT ck_retail_products_sku CHECK (sku ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_retail_products_version CHECK (version ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_retail_products_category CHECK (category ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_retail_products_name CHECK (length(trim(name)) > 0), 
	CONSTRAINT ck_retail_products_brand CHECK (brand IS NULL OR length(trim(brand)) > 0), 
	CONSTRAINT fk_retail_products_retailer_id_retailers FOREIGN KEY(retailer_id) REFERENCES retailers (id) ON DELETE RESTRICT
)
    """,
    """
CREATE TABLE store_regions (
	retailer_id UUID NOT NULL, 
	region_code VARCHAR(100) NOT NULL, 
	scope_kind VARCHAR(20) NOT NULL, 
	scope_code VARCHAR(100) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_store_regions PRIMARY KEY (id), 
	CONSTRAINT uq_store_regions_retailer_id_region_code_scope_kind_scope_code UNIQUE (retailer_id, region_code, scope_kind, scope_code), 
	CONSTRAINT uq_store_regions_id_retailer_id UNIQUE (id, retailer_id), 
	CONSTRAINT uq_store_regions_id_retailer_id_region_code UNIQUE (id, retailer_id, region_code), 
	CONSTRAINT ck_store_regions_region_code CHECK (region_code ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_store_regions_scope_code CHECK (scope_code ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_store_regions_scope_kind CHECK (scope_kind IN ('STORE','REGION')), 
	CONSTRAINT fk_store_regions_retailer_id_retailers FOREIGN KEY(retailer_id) REFERENCES retailers (id) ON DELETE RESTRICT
)
    """,
    """
CREATE TABLE ingredient_product_maps (
	retail_product_id UUID NOT NULL, 
	ingredient_id UUID NOT NULL, 
	version VARCHAR(100) NOT NULL, 
	source_basis VARCHAR(20) NOT NULL, 
	target_basis VARCHAR(20) NOT NULL, 
	edible_yield NUMERIC NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	confidence VARCHAR(20) NOT NULL, 
	reviewed_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_ingredient_product_maps PRIMARY KEY (id), 
	CONSTRAINT ck_ingredient_product_maps_source_kind CHECK (source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')), 
	CONSTRAINT ck_ingredient_product_maps_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_ingredient_product_maps_source_identity CHECK (length(trim(external_record_id)) > 0 AND length(trim(source_version)) > 0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_ingredient_product_maps_observed_at_finite CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_ingredient_product_maps_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_ingredient_product_maps_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_ingredient_product_maps_source_system_external_recor_6586 UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_ingredient_product_maps_retail_product_id_ingredient_8b58 UNIQUE (retail_product_id, ingredient_id, version), 
	CONSTRAINT uq_ingredient_product_maps_id_retail_product_id_ingredient_id UNIQUE (id, retail_product_id, ingredient_id), 
	CONSTRAINT ck_ingredient_product_maps_version CHECK (version ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_ingredient_product_maps_basis_chain CHECK (source_basis='AP_G' AND target_basis='EP_RAW_G'), 
	CONSTRAINT ck_ingredient_product_maps_edible_yield_stored_positive CHECK (edible_yield > 0 AND edible_yield < 1000000000000 AND edible_yield = trunc(edible_yield,6)), 
	CONSTRAINT ck_ingredient_product_maps_edible_yield_bound CHECK (edible_yield <= 1), 
	CONSTRAINT ck_ingredient_product_maps_confidence CHECK (confidence IN ('UNKNOWN','LOW','MEDIUM','HIGH')), 
	CONSTRAINT ck_ingredient_product_maps_status CHECK (status IN ('DRAFT','REVIEWED','REJECTED')), 
	CONSTRAINT ck_ingredient_product_maps_review_evidence CHECK ((status='DRAFT' AND reviewed_at IS NULL) OR (status IN ('REVIEWED','REJECTED') AND reviewed_at IS NOT NULL AND isfinite(reviewed_at) AND reviewed_at >= observed_at)), 
	CONSTRAINT fk_ingredient_product_maps_retail_product_id_retail_products FOREIGN KEY(retail_product_id) REFERENCES retail_products (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_ingredient_product_maps_ingredient_id_ingredients FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT
)
    """,
    """
CREATE TABLE retail_packages (
	retail_product_id UUID NOT NULL, 
	version VARCHAR(100) NOT NULL, 
	granularity VARCHAR(20) NOT NULL, 
	basis VARCHAR(20) NOT NULL, 
	fixed_ap_g NUMERIC, 
	expected_ap_g NUMERIC, 
	low_ap_g NUMERIC, 
	high_ap_g NUMERIC, 
	minimum_ap_g NUMERIC, 
	step_ap_g NUMERIC, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_retail_packages PRIMARY KEY (id), 
	CONSTRAINT ck_retail_packages_source_kind CHECK (source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')), 
	CONSTRAINT ck_retail_packages_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_retail_packages_source_identity CHECK (length(trim(external_record_id)) > 0 AND length(trim(source_version)) > 0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_retail_packages_observed_at_finite CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_retail_packages_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_retail_packages_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_retail_packages_source_system_external_record_id_sou_f9d5 UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_retail_packages_retail_product_id_version UNIQUE (retail_product_id, version), 
	CONSTRAINT uq_retail_packages_id_retail_product_id_granularity UNIQUE (id, retail_product_id, granularity), 
	CONSTRAINT uq_retail_packages_id_retail_product_id UNIQUE (id, retail_product_id), 
	CONSTRAINT ck_retail_packages_version CHECK (version ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_retail_packages_basis CHECK (basis = 'AP_G'), 
	CONSTRAINT ck_retail_packages_granularity CHECK (granularity IN ('FIXED_PACK','CATCH_WEIGHT','LOOSE_SCALE')), 
	CONSTRAINT ck_retail_packages_fixed_ap_g_stored_positive CHECK (fixed_ap_g > 0 AND fixed_ap_g < 1000000000000 AND fixed_ap_g = trunc(fixed_ap_g,6)), 
	CONSTRAINT ck_retail_packages_expected_ap_g_stored_positive CHECK (expected_ap_g > 0 AND expected_ap_g < 1000000000000 AND expected_ap_g = trunc(expected_ap_g,6)), 
	CONSTRAINT ck_retail_packages_low_ap_g_stored_positive CHECK (low_ap_g > 0 AND low_ap_g < 1000000000000 AND low_ap_g = trunc(low_ap_g,6)), 
	CONSTRAINT ck_retail_packages_high_ap_g_stored_positive CHECK (high_ap_g > 0 AND high_ap_g < 1000000000000 AND high_ap_g = trunc(high_ap_g,6)), 
	CONSTRAINT ck_retail_packages_minimum_ap_g_stored_positive CHECK (minimum_ap_g > 0 AND minimum_ap_g < 1000000000000 AND minimum_ap_g = trunc(minimum_ap_g,6)), 
	CONSTRAINT ck_retail_packages_step_ap_g_stored_positive CHECK (step_ap_g > 0 AND step_ap_g < 1000000000000 AND step_ap_g = trunc(step_ap_g,6)), 
	CONSTRAINT ck_retail_packages_purchase_behavior CHECK ((granularity='FIXED_PACK' AND fixed_ap_g IS NOT NULL AND expected_ap_g IS NULL AND low_ap_g IS NULL AND high_ap_g IS NULL AND minimum_ap_g IS NULL AND step_ap_g IS NULL) OR (granularity='CATCH_WEIGHT' AND fixed_ap_g IS NULL AND expected_ap_g IS NOT NULL AND low_ap_g IS NOT NULL AND high_ap_g IS NOT NULL AND minimum_ap_g IS NULL AND step_ap_g IS NULL AND low_ap_g <= expected_ap_g AND expected_ap_g <= high_ap_g AND low_ap_g < high_ap_g) OR (granularity='LOOSE_SCALE' AND fixed_ap_g IS NULL AND expected_ap_g IS NULL AND low_ap_g IS NULL AND high_ap_g IS NULL AND minimum_ap_g IS NOT NULL AND step_ap_g IS NOT NULL)), 
	CONSTRAINT fk_retail_packages_retail_product_id_retail_products FOREIGN KEY(retail_product_id) REFERENCES retail_products (id) ON DELETE RESTRICT
)
    """,
    """
CREATE TABLE retail_price_calibrations (
	retailer_id UUID NOT NULL, 
	store_region_id UUID NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	version VARCHAR(100) NOT NULL, 
	factor NUMERIC NOT NULL, 
	evidence_count INTEGER NOT NULL, 
	confidence VARCHAR(20) NOT NULL, 
	method_version VARCHAR(100) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_retail_price_calibrations PRIMARY KEY (id), 
	CONSTRAINT ck_retail_price_calibrations_source_kind CHECK (source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')), 
	CONSTRAINT ck_retail_price_calibrations_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_retail_price_calibrations_source_identity CHECK (length(trim(external_record_id)) > 0 AND length(trim(source_version)) > 0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_retail_price_calibrations_observed_at_finite CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_retail_price_calibrations_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_retail_price_calibrations_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_retail_price_calibrations_source_system_external_rec_b438 UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_retail_price_calibrations_retailer_id_store_region_i_5e96 UNIQUE (retailer_id, store_region_id, category, version), 
	CONSTRAINT uq_retail_price_calibrations_id_retailer_id_store_regio_f27c UNIQUE (id, retailer_id, store_region_id, category), 
	CONSTRAINT fk_store_regions_2b10d9855804 FOREIGN KEY(store_region_id, retailer_id) REFERENCES store_regions (id, retailer_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_retail_price_calibrations_category CHECK (category ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_retail_price_calibrations_version CHECK (version ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_retail_price_calibrations_method_version CHECK (method_version ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_retail_price_calibrations_factor_stored_positive CHECK (factor > 0 AND factor < 1000000000000 AND factor = trunc(factor,6)), 
	CONSTRAINT ck_retail_price_calibrations_confidence CHECK (confidence IN ('UNKNOWN','LOW','MEDIUM','HIGH')), 
	CONSTRAINT ck_retail_price_calibrations_evidence_count CHECK (evidence_count > 0)
)
    """,
    """
CREATE TABLE price_observations (
	retailer_id UUID NOT NULL, 
	store_region_id UUID NOT NULL, 
	retail_product_id UUID NOT NULL, 
	package_id UUID NOT NULL, 
	amount_minor BIGINT NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	priced_ap_g NUMERIC NOT NULL, 
	availability VARCHAR(20) NOT NULL, 
	is_promotion BOOLEAN NOT NULL, 
	source_quality VARCHAR(20) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_price_observations PRIMARY KEY (id), 
	CONSTRAINT ck_price_observations_source_kind CHECK (source_kind = 'RETAIL_OBSERVATION'), 
	CONSTRAINT ck_price_observations_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_price_observations_source_identity CHECK (length(trim(external_record_id)) > 0 AND length(trim(source_version)) > 0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_price_observations_observed_at_finite CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_price_observations_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_price_observations_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_price_observations_source_system_external_record_id__3181 UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT ck_price_observations_money_nonnegative CHECK (amount_minor >= 0), 
	CONSTRAINT ck_price_observations_currency CHECK (currency ~ '^[A-Z]{3}$'), 
	CONSTRAINT ck_price_observations_priced_ap_g_stored_positive CHECK (priced_ap_g > 0 AND priced_ap_g < 1000000000000 AND priced_ap_g = trunc(priced_ap_g,6)), 
	CONSTRAINT fk_store_regions_2b10d9855804 FOREIGN KEY(store_region_id, retailer_id) REFERENCES store_regions (id, retailer_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_retail_products_1f566cc7aba0 FOREIGN KEY(retail_product_id, retailer_id) REFERENCES retail_products (id, retailer_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_retail_packages_a131a19ebb31 FOREIGN KEY(package_id, retail_product_id) REFERENCES retail_packages (id, retail_product_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_retailers_b7a773080cf0 FOREIGN KEY(retailer_id, currency) REFERENCES retailers (id, currency) ON DELETE RESTRICT, 
	CONSTRAINT uq_price_observations_id_retailer_id_store_region_id_re_0cc7 UNIQUE (id, retailer_id, store_region_id, retail_product_id, package_id), 
	CONSTRAINT ck_price_observations_availability CHECK (availability IN ('CONFIRMED','LIKELY','UNKNOWN','UNAVAILABLE')), 
	CONSTRAINT ck_price_observations_source_quality CHECK (source_quality IN ('UNKNOWN','LOW','MEDIUM','HIGH'))
)
    """,
    """
CREATE TABLE procurement_class_members (
	procurement_class_id UUID NOT NULL, 
	mapping_id UUID NOT NULL, 
	retail_product_id UUID NOT NULL, 
	ingredient_id UUID NOT NULL, 
	equivalence VARCHAR(30) NOT NULL, 
	rationale VARCHAR(200) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_procurement_class_members PRIMARY KEY (id), 
	CONSTRAINT ck_procurement_class_members_source_kind CHECK (source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')), 
	CONSTRAINT ck_procurement_class_members_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_procurement_class_members_source_identity CHECK (length(trim(external_record_id)) > 0 AND length(trim(source_version)) > 0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_procurement_class_members_observed_at_finite CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_procurement_class_members_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_procurement_class_members_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_procurement_class_members_source_system_external_rec_9ca9 UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_procurement_class_members_procurement_class_id_mapping_id UNIQUE (procurement_class_id, mapping_id), 
	CONSTRAINT fk_procurement_classes_65d7150b6041 FOREIGN KEY(procurement_class_id, ingredient_id) REFERENCES procurement_classes (id, ingredient_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_ingredient_product_maps_5f9656d218c4 FOREIGN KEY(mapping_id, retail_product_id, ingredient_id) REFERENCES ingredient_product_maps (id, retail_product_id, ingredient_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_procurement_class_members_equivalence CHECK (equivalence IN ('EXACT_PRODUCT','REVIEWED_EQUIVALENT')), 
	CONSTRAINT ck_procurement_class_members_rationale CHECK (length(trim(rationale)) > 0)
)
    """,
    """
CREATE TABLE planning_price_quotes (
	procurement_class_id UUID NOT NULL, 
	mapping_id UUID NOT NULL, 
	ingredient_id UUID NOT NULL, 
	retail_product_id UUID NOT NULL, 
	package_id UUID NOT NULL, 
	granularity VARCHAR(20) NOT NULL, 
	retailer_id UUID NOT NULL, 
	store_region_id UUID NOT NULL, 
	region_code VARCHAR(100) NOT NULL, 
	product_category VARCHAR(100) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	evidence_kind VARCHAR(30) NOT NULL, 
	observation_id UUID, 
	calibration_id UUID, 
	reference_entry_id UUID, 
	amount_minor BIGINT NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	priced_ap_g NUMERIC NOT NULL, 
	as_of TIMESTAMP WITH TIME ZONE NOT NULL, 
	policy_version VARCHAR(100) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_planning_price_quotes PRIMARY KEY (id), 
	CONSTRAINT ck_planning_price_quotes_money_nonnegative CHECK (amount_minor >= 0), 
	CONSTRAINT ck_planning_price_quotes_currency CHECK (currency ~ '^[A-Z]{3}$'), 
	CONSTRAINT ck_planning_price_quotes_priced_ap_g_stored_positive CHECK (priced_ap_g > 0 AND priced_ap_g < 1000000000000 AND priced_ap_g = trunc(priced_ap_g,6)), 
	CONSTRAINT uq_planning_price_quotes_id_procurement_class_id UNIQUE (id, procurement_class_id), 
	CONSTRAINT fk_procurement_classes_333c8637e5a2 FOREIGN KEY(procurement_class_id, ingredient_id, granularity) REFERENCES procurement_classes (id, ingredient_id, granularity) ON DELETE RESTRICT, 
	CONSTRAINT fk_procurement_class_member_d25e4f06ec90 FOREIGN KEY(procurement_class_id, mapping_id) REFERENCES procurement_class_members (procurement_class_id, mapping_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_ingredient_product_maps_5f9656d218c4 FOREIGN KEY(mapping_id, retail_product_id, ingredient_id) REFERENCES ingredient_product_maps (id, retail_product_id, ingredient_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_retail_packages_70d5628637bb FOREIGN KEY(package_id, retail_product_id, granularity) REFERENCES retail_packages (id, retail_product_id, granularity) ON DELETE RESTRICT, 
	CONSTRAINT fk_retail_products_1f566cc7aba0 FOREIGN KEY(retail_product_id, retailer_id) REFERENCES retail_products (id, retailer_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_retail_products_b8bf05a1e1aa FOREIGN KEY(retail_product_id, product_category) REFERENCES retail_products (id, category) ON DELETE RESTRICT, 
	CONSTRAINT fk_store_regions_bbf65a8c5f0e FOREIGN KEY(store_region_id, retailer_id, region_code) REFERENCES store_regions (id, retailer_id, region_code) ON DELETE RESTRICT, 
	CONSTRAINT fk_retailers_b7a773080cf0 FOREIGN KEY(retailer_id, currency) REFERENCES retailers (id, currency) ON DELETE RESTRICT, 
	CONSTRAINT fk_price_observations_13faa0de6854 FOREIGN KEY(observation_id, retailer_id, store_region_id, retail_product_id, package_id) REFERENCES price_observations (id, retailer_id, store_region_id, retail_product_id, package_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_retail_price_calibration_cb3c2acf8269 FOREIGN KEY(calibration_id, retailer_id, store_region_id, product_category) REFERENCES retail_price_calibrations (id, retailer_id, store_region_id, category) ON DELETE RESTRICT, 
	CONSTRAINT ck_planning_price_quotes_draft_only CHECK (status='DRAFT'), 
	CONSTRAINT ck_planning_price_quotes_policy_version CHECK (policy_version ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_planning_price_quotes_as_of_finite CHECK (isfinite(as_of)), 
	CONSTRAINT ck_planning_price_quotes_exclusive_origin CHECK ((evidence_kind='RETAIL_OBSERVED' AND observation_id IS NOT NULL AND calibration_id IS NULL AND reference_entry_id IS NULL) OR (evidence_kind='CALIBRATED' AND observation_id IS NOT NULL AND calibration_id IS NOT NULL AND reference_entry_id IS NULL) OR (evidence_kind='REFERENCE_BASELINE' AND observation_id IS NULL AND calibration_id IS NULL AND reference_entry_id IS NOT NULL)), 
	CONSTRAINT fk_planning_price_quotes_reference_entry_id_reference_p_1c27 FOREIGN KEY(reference_entry_id) REFERENCES reference_price_entries (id) ON DELETE RESTRICT
)
    """,
    """
CREATE TABLE planning_procurement_options (
	procurement_class_id UUID NOT NULL, 
	quote_id UUID NOT NULL, 
	rank INTEGER NOT NULL, 
	package_size_brittleness VARCHAR(20) NOT NULL, 
	depends_on_single_source BOOLEAN NOT NULL, 
	depends_on_promotion BOOLEAN NOT NULL, 
	substitution_group VARCHAR(100) NOT NULL, 
	rationale VARCHAR(200) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_planning_procurement_options PRIMARY KEY (id), 
	CONSTRAINT ck_planning_procurement_options_source_kind CHECK (source_kind IN ('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')), 
	CONSTRAINT ck_planning_procurement_options_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_planning_procurement_options_source_identity CHECK (length(trim(external_record_id)) > 0 AND length(trim(source_version)) > 0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_planning_procurement_options_observed_at_finite CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_planning_procurement_options_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_planning_procurement_options_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_planning_procurement_options_source_system_external__fc67 UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_planning_procurement_options_procurement_class_id_rank UNIQUE (procurement_class_id, rank), 
	CONSTRAINT uq_planning_procurement_options_procurement_class_id_quote_id UNIQUE (procurement_class_id, quote_id), 
	CONSTRAINT fk_planning_price_quotes_0741ee4a0229 FOREIGN KEY(quote_id, procurement_class_id) REFERENCES planning_price_quotes (id, procurement_class_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_planning_procurement_options_rank CHECK (rank >= 0), 
	CONSTRAINT ck_planning_procurement_options_package_size_brittleness CHECK (package_size_brittleness IN ('UNKNOWN','LOW','MEDIUM','HIGH')), 
	CONSTRAINT ck_planning_procurement_options_substitution_group CHECK (substitution_group ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_planning_procurement_options_rationale CHECK (length(trim(rationale)) > 0)
)
    """,
)

TRIGGERS = """

CREATE FUNCTION menuto_retail_reject_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Retail evidence and derived draft facts are append-only; use a new version'
        USING ERRCODE = '23514';
END $$;

CREATE FUNCTION menuto_retail_check_observation() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE pack retail_packages%ROWTYPE;
BEGIN
    SELECT * INTO pack FROM retail_packages WHERE id=NEW.package_id;
    IF pack.granularity='FIXED_PACK' AND NEW.priced_ap_g <> pack.fixed_ap_g THEN
        RAISE EXCEPTION 'Fixed-pack observation must price exactly one declared package'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;

CREATE FUNCTION menuto_retail_check_member() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE state text;
BEGIN
    SELECT status INTO state FROM ingredient_product_maps WHERE id=NEW.mapping_id;
    IF state IS NOT NULL AND state <> 'REVIEWED' THEN
        RAISE EXCEPTION 'Procurement membership requires reviewed mapping'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;

CREATE FUNCTION menuto_retail_check_quote() RETURNS trigger LANGUAGE plpgsql AS $$
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

CREATE FUNCTION menuto_retail_check_option() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE quote planning_price_quotes%ROWTYPE;
BEGIN
    IF NEW.rank < 0 THEN RETURN NEW; END IF; -- leave invalid rank to the row CHECK
    SELECT * INTO quote FROM planning_price_quotes WHERE id=NEW.quote_id;
    IF FOUND THEN
        -- Serialize class option insertions so concurrent requotes cannot fake backups.
        PERFORM 1 FROM procurement_classes WHERE id=NEW.procurement_class_id FOR UPDATE;
        IF EXISTS (
            SELECT 1 FROM planning_procurement_options existing
            JOIN planning_price_quotes previous ON previous.id=existing.quote_id
            WHERE existing.procurement_class_id=NEW.procurement_class_id
                AND previous.retail_product_id=quote.retail_product_id
                AND previous.package_id=quote.package_id
                AND previous.store_region_id=quote.store_region_id
        ) THEN
            RAISE EXCEPTION 'Requoting the same purchasing path does not create a backup'
                USING ERRCODE = '23505';
        END IF;
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER price_observation_semantics BEFORE INSERT ON price_observations
FOR EACH ROW EXECUTE FUNCTION menuto_retail_check_observation();
CREATE TRIGGER procurement_member_review BEFORE INSERT ON procurement_class_members
FOR EACH ROW EXECUTE FUNCTION menuto_retail_check_member();
CREATE TRIGGER planning_quote_derivation BEFORE INSERT ON planning_price_quotes
FOR EACH ROW EXECUTE FUNCTION menuto_retail_check_quote();
CREATE TRIGGER planning_option_distinct_path BEFORE INSERT ON planning_procurement_options
FOR EACH ROW EXECUTE FUNCTION menuto_retail_check_option();

"""


def upgrade():
    for statement in DDL:
        op.execute(statement)
    op.execute(TRIGGERS)
    for table in TABLES:
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION menuto_retail_reject_mutation()"
        )
        op.execute(
            f"CREATE TRIGGER {table}_no_truncate BEFORE TRUNCATE ON {table} "
            "FOR EACH STATEMENT EXECUTE FUNCTION menuto_retail_reject_mutation()"
        )


def downgrade():
    # Lock BEFORE testing emptiness; concurrent inserts cannot race the preflight.
    op.execute("LOCK TABLE " + ", ".join(TABLES) + " IN ACCESS EXCLUSIVE MODE")
    for table in TABLES:
        op.execute(
            "DO $$ BEGIN IF EXISTS (SELECT 1 FROM " + table + ") THEN "
            "RAISE EXCEPTION 'M1.1 downgrade would lose retail/procurement evidence; "
            "explicit archival/migration required' USING ERRCODE = '23514'; END IF; END $$"
        )
    for table in reversed(TABLES):
        op.drop_table(table)
    for function in (
        "menuto_retail_check_option",
        "menuto_retail_check_quote",
        "menuto_retail_check_member",
        "menuto_retail_check_observation",
        "menuto_retail_reject_mutation",
    ):
        op.execute(f"DROP FUNCTION {function}()")
