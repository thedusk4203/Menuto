"""Real PostgreSQL M1.1 tests, including direct SQL independent of contract guards."""

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from alembic import command
from app.modules.catalog.models import Ingredient
from app.modules.retail import contracts as c
from app.modules.retail.public import derive_price_quote
from app.modules.retail.repository import RetailEvidenceRepository
from retail_fixtures import chain, provenance
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session
from test_foundation_migration import legacy_database as legacy_database
from test_foundation_migration import migrate
from test_postgres_foundation import postgres_engine as postgres_engine

pytestmark = pytest.mark.postgres


@pytest.fixture
def db(postgres_engine):
    with Session(postgres_engine) as session:
        yield session
        session.rollback()


def seed(db, granularity="FIXED_PACK"):
    f = chain(granularity)
    db.add(Ingredient(id=f["mapping"].ingredient_id, name="Synthetic retail ingredient"))
    db.flush()
    repo = RetailEvidenceRepository(db)
    for key in (
        "retailer",
        "retailer_status",
        "region",
        "product",
        "package",
        "mapping",
        "observation",
        "cls",
        "member",
        "calibration",
        "book",
        "reference",
        "quote",
        "option",
    ):
        repo.add(f[key])
    return f, repo


def row(db, table, identity=None):
    sql = f"SELECT * FROM {table}" + (" WHERE id=:id" if identity else "")
    return dict(db.execute(text(sql), {"id": identity} if identity else {}).mappings().one())


def insert_sql(db, table, fields):
    db.execute(
        text(
            f"INSERT INTO {table} ({', '.join(fields)}) "
            f"VALUES ({', '.join(':' + key for key in fields)})",
        ),
        fields,
    )


def duplicate_fields(db, table, identity=None):
    fields = row(db, table, identity)
    fields["id"] = uuid4()
    if "external_record_id" in fields:
        fields["external_record_id"] = str(uuid4())
    if "version" in fields:
        fields["version"] = str(uuid4())
    return fields


def rejected_sql(db, table, fields, code="23514"):
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        insert_sql(db, table, fields)
    assert error.value.orig.sqlstate == code, error.value


@pytest.mark.parametrize("granularity", ["FIXED_PACK", "CATCH_WEIGHT", "LOOSE_SCALE"])
def test_complete_evidence_and_procurement_roundtrip(db, granularity):
    f, repo = seed(db, granularity)
    assert repo.get(c.PriceObservationFact, f["observation"].id) == f["observation"]
    assert repo.get(c.PlanningPriceQuoteDraft, f["quote"].id) == f["quote"]
    assert repo.get(c.IngredientProductMapFact, f["mapping"].id) == f["mapping"]
    snapshot = repo.procurement_snapshot(f["cls"].id)
    assert snapshot == c.ProcurementSnapshotDraft(
        procurement_class=f["cls"],
        members=(f["member"],),
        options=(f["option"],),
    )
    assert snapshot.options[0].quote.observation.provenance == f["observation"].provenance


def test_real_second_product_and_primary_backup_coverage(db):
    f, repo = seed(db)
    other_product = c.RetailProductFact.model_validate(
        f["product"].model_dump()
        | {
            "id": uuid4(),
            "sku": "backup-sku",
            "provenance": provenance(),
        }
    )
    other_pack = c.PackageFact.model_validate(
        f["package"].model_dump()
        | {
            "id": uuid4(),
            "retail_product_id": other_product.id,
            "provenance": provenance(),
            "fixed_ap_g": "600",
        }
    )
    other_map = c.IngredientProductMapFact.model_validate(
        f["mapping"].model_dump()
        | {
            "id": uuid4(),
            "retail_product_id": other_product.id,
            "provenance": provenance(),
        }
    )
    other_member = c.ProcurementClassMemberFact.model_validate(
        f["member"].model_dump()
        | {
            "mapping": other_map,
            "equivalence": "REVIEWED_EQUIVALENT",
            "provenance": provenance(),
        }
    )
    other_obs = c.PriceObservationFact.model_validate(
        f["observation"].model_dump()
        | {
            "id": uuid4(),
            "retail_product_id": other_product.id,
            "package_id": other_pack.id,
            "priced_ap_g": "600",
            "provenance": provenance("RETAIL_OBSERVATION"),
        }
    )
    inputs = f["quote_inputs"] | {"mapping": other_map, "package": other_pack}
    backup_quote = derive_price_quote(**inputs, observation=other_obs)
    backup = c.PlanningProcurementOptionDraft.model_validate(
        f["option"].model_dump()
        | {
            "id": uuid4(),
            "rank": 1,
            "quote": backup_quote,
            "provenance": provenance(),
        }
    )
    for fact in (
        other_product,
        other_pack,
        other_map,
        other_member,
        other_obs,
        backup_quote,
        backup,
    ):
        repo.add(fact)
    snapshot = repo.procurement_snapshot(f["cls"].id)
    assert [opt.rank for opt in snapshot.options] == [0, 1]
    assert len({opt.quote.mapping.retail_product_id for opt in snapshot.options}) == 2
    assert snapshot.options[1].quote.package.fixed_ap_g == Decimal(600)


@pytest.mark.parametrize(
    "fields",
    [
        {"fixed_ap_g": None},
        {"expected_ap_g": Decimal(500)},
        {"fixed_ap_g": Decimal(-1)},
        {"granularity": "FAKE_PACK"},
        {"basis": "EP_RAW_G"},
        {"fixed_ap_g": Decimal("NaN")},
        {"fixed_ap_g": Decimal("Infinity")},
        {"fixed_ap_g": Decimal("0.0000001")},
        {"fixed_ap_g": Decimal("108.215184200427")},
    ],
)
def test_direct_sql_fixed_package_constraints_and_no_silent_rounding(db, fields):
    seed(db)
    rejected_sql(db, "retail_packages", duplicate_fields(db, "retail_packages") | fields)


@pytest.mark.parametrize(
    "fields",
    [
        {"low_ap_g": Decimal(501)},
        {"high_ap_g": Decimal(499)},
        {"high_ap_g": None},
        {"fixed_ap_g": Decimal(500)},
        {"low_ap_g": Decimal(550), "expected_ap_g": Decimal(550)},
    ],
)
def test_direct_sql_catch_bounds(db, fields):
    seed(db, "CATCH_WEIGHT")
    rejected_sql(db, "retail_packages", duplicate_fields(db, "retail_packages") | fields)


@pytest.mark.parametrize(
    "fields",
    [
        {"minimum_ap_g": None},
        {"step_ap_g": Decimal(0)},
        {"expected_ap_g": Decimal(500)},
        {"step_ap_g": Decimal("0.0000001")},
    ],
)
def test_direct_sql_loose_scale_rules(db, fields):
    seed(db, "LOOSE_SCALE")
    rejected_sql(db, "retail_packages", duplicate_fields(db, "retail_packages") | fields)


@pytest.mark.parametrize(
    "fields",
    [
        {"edible_yield": Decimal(0)},
        {"edible_yield": Decimal("1.1")},
        {"edible_yield": Decimal("NaN")},
        {"target_basis": "COOKED_G"},
        {"source_basis": "EP_RAW_G"},
        {"reviewed_at": None},
        {"status": "APPROVED"},
        {"edible_yield": Decimal("0.8765432")},
    ],
)
def test_direct_sql_mapping_constraints(db, fields):
    seed(db)
    rejected_sql(
        db, "ingredient_product_maps", duplicate_fields(db, "ingredient_product_maps") | fields
    )


def test_cross_product_mapping_and_class_ingredient_fk_integrity(db):
    f, _ = seed(db)
    for field in ("retail_product_id", "ingredient_id"):
        other = uuid4()
        if field == "ingredient_id":
            db.add(Ingredient(id=other, name="Different ingredient"))
            db.flush()
        else:
            fields = duplicate_fields(db, "retail_products") | {"id": other}
            insert_sql(db, "retail_products", fields)
        cls = duplicate_fields(db, "procurement_classes", f["cls"].id)
        insert_sql(db, "procurement_classes", cls)
        member = duplicate_fields(db, "procurement_class_members") | {
            field: other,
            "procurement_class_id": cls["id"],
        }
        rejected_sql(db, "procurement_class_members", member, code="23503")
    assert row(db, "ingredient_product_maps")["ingredient_id"] == f["mapping"].ingredient_id


@pytest.mark.parametrize(
    "fields,code",
    [
        ({"retailer_id": uuid4()}, "23503"),
        ({"store_region_id": uuid4()}, "23503"),
        ({"package_id": uuid4()}, "23503"),
        ({"availability": "GUARANTEED"}, "23514"),
        ({"amount_minor": -1}, "23514"),
        ({"currency": "vnd"}, "23514"),
        ({"currency": "USD"}, "23503"),
        ({"priced_ap_g": Decimal("NaN")}, "23514"),
        ({"priced_ap_g": Decimal("Infinity")}, "23514"),
        ({"priced_ap_g": Decimal(-1)}, "23514"),
        ({"priced_ap_g": Decimal(499)}, "23514"),
        ({"source_kind": "REVIEWED_REFERENCE"}, "23514"),
        ({"source_system": " "}, "23514"),
        ({"external_record_id": " "}, "23514"),
        ({"source_version": ""}, "23514"),
        ({"content_hash": "invalid"}, "23514"),
        ({"source_uri": "https://user:password@example.com/record"}, "23514"),
    ],
)
def test_direct_sql_observation_context_price_and_provenance(db, fields, code):
    seed(db)
    rejected_sql(
        db, "price_observations", duplicate_fields(db, "price_observations") | fields, code=code
    )


def test_external_source_identity_provider_namespace(db):
    f, repo = seed(db)
    fields = row(db, "price_observations") | {"id": uuid4(), "source_system": "another-provider"}
    insert_sql(db, "price_observations", fields)
    loaded = repo.get(c.PriceObservationFact, fields["id"])
    assert loaded.provenance.external_record_id == f["observation"].provenance.external_record_id
    assert loaded.provenance.source_system == "another-provider"
    rejected_sql(db, "price_observations", fields | {"id": uuid4()}, code="23505")


def test_calibrated_and_reference_derivations_roundtrip(db):
    f, repo = seed(db)
    for origin in ("CALIBRATED_REFERENCE", "REFERENCE_BASELINE"):
        inputs = (
            {"reference": f["reference"], "calibration": f["calibration"]}
            if origin == "CALIBRATED_REFERENCE"
            else {"reference": f["reference"]}
        )
        quote = derive_price_quote(**f["quote_inputs"], **inputs)
        repo.add(quote)
        assert repo.get(c.PlanningPriceQuoteDraft, quote.id) == quote
        assert quote.evidence_kind == origin
        assert quote.availability == "UNKNOWN"
        assert row(db, "planning_price_quotes", quote.id)["observation_id"] is None


@pytest.mark.parametrize(
    "fields",
    [
        {"reference_amount_minor": 50_001},
        {"reference_ap_g": Decimal(499)},
        {"evidence_kind": "CALIBRATED"},
        {"evidence_kind": "REFERENCE_BASELINE"},
        {"observation_id": None},
        {"as_of": provenance().observed_at - timedelta(seconds=1)},
        {"status": "READY"},
    ],
)
def test_raw_sql_quote_cannot_masquerade_or_erase_provenance(db, fields):
    seed(db)
    rejected_sql(
        db, "planning_price_quotes", duplicate_fields(db, "planning_price_quotes") | fields
    )


def test_reference_cannot_masquerade_or_cross_ingredient_region_currency(db):
    f, repo = seed(db)
    baseline = derive_price_quote(**f["quote_inputs"], reference=f["reference"])
    repo.add(baseline)
    for override, code in [
        ({"currency": "USD"}, "23514"),
        ({"reference_amount_minor": 1}, "23514"),
        ({"observation_id": f["observation"].id}, "23514"),
        ({"region_code": "OTHER"}, "23514"),
    ]:
        fields = row(db, "planning_price_quotes", baseline.id) | {"id": uuid4()} | override
        rejected_sql(db, "planning_price_quotes", fields, code=code)
    fields = duplicate_fields(db, "reference_price_books") | {"source_kind": "RETAIL_OBSERVATION"}
    rejected_sql(db, "reference_price_books", fields)


def test_calibration_context_and_fractional_minor_units_cannot_be_faked(db):
    f, repo = seed(db)
    cal = c.RetailPriceCalibrationFact.model_validate(
        f["calibration"].model_dump()
        | {
            "id": uuid4(),
            "version": "2",
            "factor": "1.000001",
            "provenance": provenance(),
        }
    )
    repo.add(cal)
    fields = duplicate_fields(db, "planning_price_quotes") | {
        "evidence_kind": "CALIBRATED_REFERENCE",
        "observation_id": None,
        "reference_entry_id": f["reference"].id,
        "reference_ap_g": Decimal(1000),
        "reference_amount_minor": 60_000,
        "calibration_id": cal.id,
    }
    rejected_sql(db, "planning_price_quotes", fields)
    other = c.RetailPriceCalibrationFact.model_validate(
        f["calibration"].model_dump()
        | {
            "id": uuid4(),
            "category": "vegetables",
            "provenance": provenance(),
        }
    )
    repo.add(other)
    rejected_sql(
        db,
        "planning_price_quotes",
        fields
        | {
            "id": uuid4(),
            "calibration_id": other.id,
            "reference_amount_minor": 66_000,
        },
        code="23503",
    )


def test_sql_duplicate_purchasing_path_is_not_a_backup(db):
    f, repo = seed(db)
    requote = derive_price_quote(**f["quote_inputs"], observation=f["observation"])
    repo.add(requote)
    fields = duplicate_fields(db, "planning_procurement_options") | {
        "rank": 1,
        "quote_id": requote.id,
    }
    rejected_sql(db, "planning_procurement_options", fields, code="23505")


def test_nested_evidence_cannot_reuse_identity_with_different_primitive_facts(db):
    f, repo = seed(db)
    forged_mapping = c.IngredientProductMapFact.model_validate(
        f["mapping"].model_dump()
        | {
            "edible_yield": "0.5",
        }
    )
    quote = derive_price_quote(
        **(f["quote_inputs"] | {"mapping": forged_mapping}), observation=f["observation"]
    )
    with pytest.raises(ValueError, match="persisted immutable identity"):
        repo.add(quote)


def test_real_existing_store_and_retailer_cannot_cross_context(db):
    f, repo = seed(db)
    other = c.RetailerFact.model_validate(f["retailer"].model_dump() | {"id": uuid4()})
    repo.add(other)
    region = c.StoreRegionFact.model_validate(
        f["region"].model_dump()
        | {
            "id": uuid4(),
            "retailer_id": other.id,
        }
    )
    repo.add(region)
    for override in (
        {"store_region_id": region.id},
        {"retailer_id": other.id, "store_region_id": region.id},
    ):
        rejected_sql(
            db,
            "price_observations",
            duplicate_fields(db, "price_observations") | override,
            code="23503",
        )


def test_distinct_quote_class_context_and_primary_uniqueness(db):
    seed(db)
    fields = duplicate_fields(db, "planning_procurement_options")
    rejected_sql(db, "planning_procurement_options", fields, code="23505")
    rejected_sql(
        db,
        "planning_procurement_options",
        fields
        | {
            "rank": 1,
            "procurement_class_id": uuid4(),
        },
        code="23503",
    )
    rejected_sql(db, "planning_procurement_options", fields | {"rank": -1})


TABLES = (
    "retailers",
    "store_regions",
    "retail_products",
    "retail_packages",
    "ingredient_product_maps",
    "price_observations",
    "procurement_classes",
    "procurement_class_members",
    "reference_price_books",
    "reference_price_entries",
    "retail_price_calibrations",
    "planning_price_quotes",
    "planning_procurement_options",
)
NEW_TABLES = ("retailer_status_facts", "retail_legacy_option_assessments")


@pytest.mark.parametrize("table", (*TABLES, "retailer_status_facts"))
@pytest.mark.parametrize("mutation", ["UPDATE", "DELETE", "TRUNCATE"])
def test_all_retail_facts_append_only_even_via_direct_sql(db, table, mutation):
    seed(db)
    sql = {
        "UPDATE": f"UPDATE {table} SET id=id",
        "DELETE": f"DELETE FROM {table}",
        "TRUNCATE": f"TRUNCATE {table} CASCADE",
    }[mutation]
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.execute(text(sql))
    assert error.value.orig.sqlstate == "23514"


def test_orm_rejects_float_and_excess_precision_before_binding(db):
    from app.modules.retail.models import RetailPackage

    f, _ = seed(db)
    for value in (0.1, Decimal("0.0000001")):
        with pytest.raises(StatementError), db.begin_nested():
            db.add(
                RetailPackage(
                    **(duplicate_fields(db, "retail_packages") | {"fixed_ap_g": value}),
                )
            )
            db.flush()
    assert f["package"].fixed_ap_g == Decimal(500)


def test_m11_upgrade_downgrade_upgrade_and_metadata_drift(legacy_database):
    engine, config = legacy_database
    migrate(engine, config, "0002")
    before = set(inspect(engine).get_table_names())
    migrate(engine, config, "0003")
    migrate(engine, config, "0004")
    assert set(inspect(engine).get_table_names()) - before == set((*TABLES, *NEW_TABLES))
    migrate(engine, config, "0002", down=True)
    assert set(inspect(engine).get_table_names()) == before
    migrate(engine, config, "0003")
    migrate(engine, config, "0004")
    # Runtime metadata describes current head; the 0002↔0004 roundtrip above remains explicit.
    migrate(engine, config, "head")
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.check(config)


@pytest.mark.parametrize("full_chain", [False, True])
def test_m11_downgrade_fails_closed_and_preserves_data(legacy_database, full_chain):
    engine, config = legacy_database
    migrate(engine, config, "head")
    with Session(engine) as session:
        if full_chain:
            seed(session)
        else:
            RetailEvidenceRepository(session).add(chain()["retailer"])
        session.commit()
    with pytest.raises(IntegrityError, match="0004 downgrade cannot preserve"):
        migrate(engine, config, "0002", down=True)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0007"
        assert connection.scalar(text("SELECT count(*) FROM retailers")) == 1
        if full_chain:
            assert connection.scalar(text("SELECT count(*) FROM ingredient_product_maps")) == 1
            assert connection.scalar(text("SELECT count(*) FROM price_observations")) == 1
            assert connection.scalar(text("SELECT count(*) FROM planning_price_quotes")) == 1
