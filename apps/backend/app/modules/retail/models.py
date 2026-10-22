"""Retail owns purchase evidence and product-specific edible yield (ADR-006).

All rows remain append-only. Stable retailer identity has separate status facts (0004).
Foreign keys are relational context bindings, never cross-context Python ORM imports.
"""

from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.domain.contracts import PersistedDecimal
from app.shared.db import Base, IdentityMixin, ProvenanceMixin


class RetailNumeric(TypeDecorator):
    """StoredQuantity domain, without PostgreSQL typmod's silent scale coercion."""

    impl = Numeric()
    cache_ok = True
    adapter = TypeAdapter(PersistedDecimal)

    def process_bind_param(self, value, dialect):
        return None if value is None else self.adapter.validate_python(value)


QUALITY = "('UNKNOWN','LOW','MEDIUM','HIGH')"
GRANULARITY = "('FIXED_PACK','CATCH_WEIGHT','LOOSE_SCALE')"
AVAILABILITY = "('CONFIRMED','LIKELY','UNKNOWN','UNAVAILABLE')"


def fk(columns, table, targets):
    identity = "_".join([table, *columns, *targets])
    return ForeignKeyConstraint(
        columns,
        [f"{table}.{column}" for column in targets],
        ondelete="RESTRICT",
        name=f"fk_{table[:24]}_{sha256(identity.encode()).hexdigest()[:12]}",
    )


def positive(column):
    return CheckConstraint(
        f"{column} > 0 AND {column} < 1000000000000 AND {column} = trunc({column},6)",
        name=f"{column}_stored_positive",
    )


def quality(column):
    return CheckConstraint(f"{column} IN {QUALITY}", name=column)


def identifier(column):
    return CheckConstraint(f"{column} ~ '^[A-Za-z0-9_.:-]+$'", name=column)


def provenance_constraints(*, kind=None, legacy_state=False):
    allowed = "('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT')"
    if legacy_state:
        allowed = "('USER','REVIEWED_REFERENCE','RETAIL_OBSERVATION','RECEIPT','LEGACY_STATE')"
    return (
        CheckConstraint(
            f"source_kind = '{kind}'" if kind else f"source_kind IN {allowed}",
            name="source_kind",
        ),
        identifier("source_system"),
        CheckConstraint(
            "length(trim(external_record_id)) > 0 AND "
            "length(trim(source_version)) > 0 AND "
            "external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'",
            name="source_identity",
        ),
        CheckConstraint("isfinite(observed_at)", name="observed_at_finite"),
        CheckConstraint(
            "content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'",
            name="content_hash",
        ),
        CheckConstraint(
            "source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' "
            "AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')",
            name="source_uri",
        ),
        UniqueConstraint("source_system", "external_record_id", "source_version"),
    )


def money_constraints(amount="amount_minor", quantity="priced_ap_g"):
    return (
        CheckConstraint(f"{amount} >= 0", name="money_nonnegative"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency"),
        positive(quantity),
    )


class Retailer(IdentityMixin, Base):
    __tablename__ = "retailers"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="name"),
        CheckConstraint("country ~ '^[A-Z]{2}$'", name="country"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency"),
        UniqueConstraint("id", "currency"),
    )
    name: Mapped[str] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(2))
    currency: Mapped[str] = mapped_column(String(3))


class RetailerStatusFact(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "retailer_status_facts"
    __table_args__ = (
        *provenance_constraints(legacy_state=True),
        UniqueConstraint("retailer_id", "effective_at"),
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="status"),
        CheckConstraint("isfinite(effective_at)", name="effective_at_finite"),
    )
    retailer_id: Mapped[UUID] = mapped_column(ForeignKey("retailers.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(20))
    effective_at: Mapped[datetime]


class StoreRegion(IdentityMixin, Base):
    __tablename__ = "store_regions"
    __table_args__ = (
        UniqueConstraint("retailer_id", "region_code", "scope_kind", "scope_code"),
        UniqueConstraint("id", "retailer_id"),
        UniqueConstraint("id", "retailer_id", "region_code"),
        identifier("region_code"),
        identifier("scope_code"),
        CheckConstraint("scope_kind IN ('STORE','REGION')", name="scope_kind"),
    )
    retailer_id: Mapped[UUID] = mapped_column(ForeignKey("retailers.id", ondelete="RESTRICT"))
    region_code: Mapped[str] = mapped_column(String(100))
    scope_kind: Mapped[str] = mapped_column(String(20))
    scope_code: Mapped[str] = mapped_column(String(100))


class RetailProduct(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "retail_products"
    __table_args__ = (
        *provenance_constraints(),
        UniqueConstraint("retailer_id", "sku", "version"),
        UniqueConstraint("id", "retailer_id"),
        UniqueConstraint("id", "category"),
        UniqueConstraint("id", "canonical_ingredient_id"),
        identifier("sku"),
        identifier("version"),
        identifier("category"),
        CheckConstraint("length(trim(name)) > 0", name="name"),
        CheckConstraint("brand IS NULL OR length(trim(brand)) > 0", name="brand"),
    )
    retailer_id: Mapped[UUID] = mapped_column(ForeignKey("retailers.id", ondelete="RESTRICT"))
    sku: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))
    canonical_ingredient_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT")
    )


class RetailPackage(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "retail_packages"
    __table_args__ = (
        *provenance_constraints(),
        UniqueConstraint("retail_product_id", "version"),
        UniqueConstraint("id", "retail_product_id", "granularity"),
        UniqueConstraint("id", "retail_product_id"),
        identifier("version"),
        CheckConstraint("basis = 'AP_G'", name="basis"),
        CheckConstraint(f"granularity IN {GRANULARITY}", name="granularity"),
        *(
            positive(c)
            for c in (
                "fixed_ap_g",
                "expected_ap_g",
                "low_ap_g",
                "high_ap_g",
                "minimum_ap_g",
                "step_ap_g",
            )
        ),
        CheckConstraint(
            "(granularity='FIXED_PACK' AND fixed_ap_g IS NOT NULL AND expected_ap_g IS NULL "
            "AND low_ap_g IS NULL AND high_ap_g IS NULL AND minimum_ap_g IS NULL "
            "AND step_ap_g IS NULL) OR "
            "(granularity='CATCH_WEIGHT' AND fixed_ap_g IS NULL AND expected_ap_g IS NOT NULL "
            "AND low_ap_g IS NOT NULL AND high_ap_g IS NOT NULL AND minimum_ap_g IS NULL "
            "AND step_ap_g IS NULL AND low_ap_g <= expected_ap_g "
            "AND expected_ap_g <= high_ap_g AND low_ap_g < high_ap_g) OR "
            "(granularity='LOOSE_SCALE' AND fixed_ap_g IS NULL AND expected_ap_g IS NULL "
            "AND low_ap_g IS NULL AND high_ap_g IS NULL AND minimum_ap_g IS NOT NULL "
            "AND step_ap_g IS NOT NULL)",
            name="purchase_behavior",
        ),
    )
    retail_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("retail_products.id", ondelete="RESTRICT")
    )
    version: Mapped[str] = mapped_column(String(100))
    granularity: Mapped[str] = mapped_column(String(20))
    basis: Mapped[str] = mapped_column(String(20))
    fixed_ap_g: Mapped[Decimal | None] = mapped_column(RetailNumeric())
    expected_ap_g: Mapped[Decimal | None] = mapped_column(RetailNumeric())
    low_ap_g: Mapped[Decimal | None] = mapped_column(RetailNumeric())
    high_ap_g: Mapped[Decimal | None] = mapped_column(RetailNumeric())
    minimum_ap_g: Mapped[Decimal | None] = mapped_column(RetailNumeric())
    step_ap_g: Mapped[Decimal | None] = mapped_column(RetailNumeric())


class IngredientProductMap(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "ingredient_product_maps"
    __table_args__ = (
        *provenance_constraints(),
        UniqueConstraint("retail_product_id", "ingredient_id", "version"),
        UniqueConstraint("id", "retail_product_id", "ingredient_id"),
        fk(
            ["retail_product_id", "ingredient_id"],
            "retail_products",
            ["id", "canonical_ingredient_id"],
        ),
        identifier("version"),
        CheckConstraint("source_basis='AP_G' AND target_basis='EP_RAW_G'", name="basis_chain"),
        positive("edible_yield"),
        CheckConstraint("edible_yield <= 1", name="edible_yield_bound"),
        quality("confidence"),
        CheckConstraint("status IN ('DRAFT','REVIEWED','REJECTED')", name="status"),
        CheckConstraint(
            "(status='DRAFT' AND reviewed_at IS NULL) OR "
            "(status IN ('REVIEWED','REJECTED') AND reviewed_at IS NOT NULL "
            "AND isfinite(reviewed_at) AND reviewed_at >= observed_at)",
            name="review_evidence",
        ),
    )
    retail_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("retail_products.id", ondelete="RESTRICT")
    )
    ingredient_id: Mapped[UUID] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    version: Mapped[str] = mapped_column(String(100))
    source_basis: Mapped[str] = mapped_column(String(20))
    target_basis: Mapped[str] = mapped_column(String(20))
    edible_yield: Mapped[Decimal] = mapped_column(RetailNumeric())
    status: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[str] = mapped_column(String(20))
    reviewed_at: Mapped[datetime | None]


class PriceObservation(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "price_observations"
    __table_args__ = (
        *provenance_constraints(kind="RETAIL_OBSERVATION"),
        *money_constraints(),
        fk(["store_region_id", "retailer_id"], "store_regions", ["id", "retailer_id"]),
        fk(["retail_product_id", "retailer_id"], "retail_products", ["id", "retailer_id"]),
        fk(["package_id", "retail_product_id"], "retail_packages", ["id", "retail_product_id"]),
        fk(["retailer_id", "currency"], "retailers", ["id", "currency"]),
        UniqueConstraint("id", "retailer_id", "store_region_id", "retail_product_id", "package_id"),
        CheckConstraint(f"availability IN {AVAILABILITY}", name="availability"),
        quality("source_quality"),
    )
    retailer_id: Mapped[UUID]
    store_region_id: Mapped[UUID]
    retail_product_id: Mapped[UUID]
    package_id: Mapped[UUID]
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    priced_ap_g: Mapped[Decimal] = mapped_column(RetailNumeric())
    availability: Mapped[str] = mapped_column(String(20))
    is_promotion: Mapped[bool]
    source_quality: Mapped[str] = mapped_column(String(20))


class ProcurementClass(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "procurement_classes"
    __table_args__ = (
        *provenance_constraints(),
        UniqueConstraint("code", "version"),
        UniqueConstraint("id", "ingredient_id", "granularity"),
        UniqueConstraint("id", "ingredient_id"),
        identifier("code"),
        identifier("version"),
        CheckConstraint(f"granularity IN {GRANULARITY}", name="granularity"),
        CheckConstraint("status='DRAFT'", name="draft_only"),
    )
    code: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100))
    ingredient_id: Mapped[UUID] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    granularity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))


class ProcurementClassMember(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "procurement_class_members"
    __table_args__ = (
        *provenance_constraints(),
        UniqueConstraint("procurement_class_id", "mapping_id"),
        fk(
            ["procurement_class_id", "ingredient_id"],
            "procurement_classes",
            ["id", "ingredient_id"],
        ),
        fk(
            ["mapping_id", "retail_product_id", "ingredient_id"],
            "ingredient_product_maps",
            ["id", "retail_product_id", "ingredient_id"],
        ),
        CheckConstraint(
            "equivalence IN ('EXACT_PRODUCT','REVIEWED_EQUIVALENT')",
            name="equivalence",
        ),
        CheckConstraint("length(trim(rationale)) > 0", name="rationale"),
    )
    procurement_class_id: Mapped[UUID]
    mapping_id: Mapped[UUID]
    retail_product_id: Mapped[UUID]
    ingredient_id: Mapped[UUID]
    equivalence: Mapped[str] = mapped_column(String(30))
    rationale: Mapped[str] = mapped_column(String(200))


class ReferencePriceBook(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "reference_price_books"
    __table_args__ = (
        *provenance_constraints(kind="REVIEWED_REFERENCE"),
        UniqueConstraint("code", "version"),
        identifier("code"),
        identifier("version"),
        identifier("region_code"),
    )
    code: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100))
    region_code: Mapped[str] = mapped_column(String(100))


class ReferencePriceEntry(IdentityMixin, Base):
    __tablename__ = "reference_price_entries"
    __table_args__ = (
        *money_constraints(),
        UniqueConstraint("book_id", "ingredient_id", "currency"),
        CheckConstraint("basis='AP_G'", name="basis"),
        quality("confidence"),
    )
    book_id: Mapped[UUID] = mapped_column(
        ForeignKey("reference_price_books.id", ondelete="RESTRICT")
    )
    ingredient_id: Mapped[UUID] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    priced_ap_g: Mapped[Decimal] = mapped_column(RetailNumeric())
    basis: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[str] = mapped_column(String(20))


class RetailPriceCalibration(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "retail_price_calibrations"
    __table_args__ = (
        *provenance_constraints(),
        UniqueConstraint("retailer_id", "store_region_id", "category", "version"),
        UniqueConstraint("id", "retailer_id", "store_region_id", "category"),
        fk(["store_region_id", "retailer_id"], "store_regions", ["id", "retailer_id"]),
        identifier("category"),
        identifier("version"),
        identifier("method_version"),
        positive("factor"),
        quality("confidence"),
        CheckConstraint("evidence_count > 0", name="evidence_count"),
    )
    retailer_id: Mapped[UUID]
    store_region_id: Mapped[UUID]
    category: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100))
    factor: Mapped[Decimal] = mapped_column(RetailNumeric())
    evidence_count: Mapped[int]
    confidence: Mapped[str] = mapped_column(String(20))
    method_version: Mapped[str] = mapped_column(String(100))


class PlanningPriceQuote(IdentityMixin, Base):
    __tablename__ = "planning_price_quotes"
    __table_args__ = (
        *money_constraints("reference_amount_minor", "reference_ap_g"),
        CheckConstraint("price_basis='REFERENCE_WEIGHT_RATE'", name="price_basis"),
        UniqueConstraint("id", "procurement_class_id"),
        fk(
            ["procurement_class_id", "ingredient_id", "granularity"],
            "procurement_classes",
            ["id", "ingredient_id", "granularity"],
        ),
        fk(
            ["procurement_class_id", "mapping_id"],
            "procurement_class_members",
            ["procurement_class_id", "mapping_id"],
        ),
        fk(
            ["mapping_id", "retail_product_id", "ingredient_id"],
            "ingredient_product_maps",
            ["id", "retail_product_id", "ingredient_id"],
        ),
        fk(
            ["package_id", "retail_product_id", "granularity"],
            "retail_packages",
            ["id", "retail_product_id", "granularity"],
        ),
        fk(["retail_product_id", "retailer_id"], "retail_products", ["id", "retailer_id"]),
        fk(["retail_product_id", "product_category"], "retail_products", ["id", "category"]),
        fk(
            ["store_region_id", "retailer_id", "region_code"],
            "store_regions",
            ["id", "retailer_id", "region_code"],
        ),
        fk(["retailer_id", "currency"], "retailers", ["id", "currency"]),
        fk(
            ["observation_id", "retailer_id", "store_region_id", "retail_product_id", "package_id"],
            "price_observations",
            ["id", "retailer_id", "store_region_id", "retail_product_id", "package_id"],
        ),
        fk(
            ["calibration_id", "retailer_id", "store_region_id", "product_category"],
            "retail_price_calibrations",
            ["id", "retailer_id", "store_region_id", "category"],
        ),
        CheckConstraint("status='DRAFT'", name="draft_only"),
        identifier("policy_version"),
        CheckConstraint("isfinite(as_of)", name="as_of_finite"),
        CheckConstraint(
            "(evidence_kind='RETAIL_OBSERVED' AND observation_id IS NOT NULL "
            "AND calibration_id IS NULL AND reference_entry_id IS NULL) OR "
            "(evidence_kind='CALIBRATED_REFERENCE' AND observation_id IS NULL "
            "AND calibration_id IS NOT NULL AND reference_entry_id IS NOT NULL) OR "
            "(evidence_kind='REFERENCE_BASELINE' AND observation_id IS NULL "
            "AND calibration_id IS NULL AND reference_entry_id IS NOT NULL)",
            name="exclusive_origin",
        ),
    )
    procurement_class_id: Mapped[UUID]
    mapping_id: Mapped[UUID]
    ingredient_id: Mapped[UUID]
    retail_product_id: Mapped[UUID]
    package_id: Mapped[UUID]
    granularity: Mapped[str] = mapped_column(String(20))
    retailer_id: Mapped[UUID]
    store_region_id: Mapped[UUID]
    region_code: Mapped[str] = mapped_column(String(100))
    product_category: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))
    evidence_kind: Mapped[str] = mapped_column(String(30))
    observation_id: Mapped[UUID | None]
    calibration_id: Mapped[UUID | None]
    reference_entry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("reference_price_entries.id", ondelete="RESTRICT")
    )
    reference_amount_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    reference_ap_g: Mapped[Decimal] = mapped_column(RetailNumeric())
    price_basis: Mapped[str] = mapped_column(String(30))
    as_of: Mapped[datetime]
    policy_version: Mapped[str] = mapped_column(String(100))


class PlanningProcurementOption(IdentityMixin, ProvenanceMixin, Base):
    __tablename__ = "planning_procurement_options"
    __table_args__ = (
        *provenance_constraints(),
        UniqueConstraint("procurement_class_id", "rank"),
        UniqueConstraint("procurement_class_id", "quote_id"),
        fk(
            ["quote_id", "procurement_class_id"],
            "planning_price_quotes",
            ["id", "procurement_class_id"],
        ),
        CheckConstraint("rank >= 0", name="rank"),
        quality("package_size_brittleness"),
        identifier("brittleness_policy_version"),
        identifier("substitution_group"),
        CheckConstraint("length(trim(rationale)) > 0", name="rationale"),
    )
    procurement_class_id: Mapped[UUID]
    quote_id: Mapped[UUID]
    rank: Mapped[int]
    package_size_brittleness: Mapped[str] = mapped_column(String(20))
    brittleness_policy_version: Mapped[str] = mapped_column(String(100))
    substitution_group: Mapped[str] = mapped_column(String(100))
    rationale: Mapped[str] = mapped_column(String(200))


class LegacyOptionAssessment(Base):
    """Historical 0003 assertions retained for audit, never used as derived evidence."""

    __tablename__ = "retail_legacy_option_assessments"
    option_id: Mapped[UUID] = mapped_column(
        ForeignKey("planning_procurement_options.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    legacy_depends_on_single_source: Mapped[bool]
    legacy_depends_on_promotion: Mapped[bool]
    captured_at: Mapped[datetime] = mapped_column(server_default=func.now())
