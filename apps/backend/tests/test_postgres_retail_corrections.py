"""0003→0004 data safety, canonical derivation, stable identity and direct SQL guards."""

from datetime import timedelta
from uuid import uuid4

import pytest
from alembic import command
from app.modules.retail import contracts as c
from app.modules.retail.public import derive_price_quote
from app.modules.retail.repository import RetailEvidenceRepository
from retail_fixtures import NOW, chain, provenance
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import Session
from test_foundation_migration import legacy_database as legacy_database
from test_foundation_migration import migrate
from test_postgres_foundation import postgres_engine as postgres_engine
from test_postgres_retail import (
    db as db,
)
from test_postgres_retail import (
    duplicate_fields,
    insert_sql,
    rejected_sql,
    row,
    seed,
)
from test_retail_contracts import changed

pytestmark = pytest.mark.postgres


def seed_0003(engine, *, calibrated=False, unmapped=False, ambiguous=False):
    """Insert the published 0003 wire semantics without using mutable ORM tables."""
    f = chain()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO ingredients(id,name) VALUES (:id,'Synthetic')"),
            {"id": f["mapping"].ingredient_id},
        )
        for key, table in (
            ("retailer", "retailers"),
            ("region", "store_regions"),
            ("product", "retail_products"),
            ("package", "retail_packages"),
            ("mapping", "ingredient_product_maps"),
            ("observation", "price_observations"),
            ("cls", "procurement_classes"),
            ("member", "procurement_class_members"),
            ("book", "reference_price_books"),
            ("reference", "reference_price_entries"),
            ("calibration", "retail_price_calibrations"),
            ("quote", "planning_price_quotes"),
            ("option", "planning_procurement_options"),
        ):
            if unmapped and key not in {"retailer", "region", "product", "package"}:
                continue
            fields = f[key].model_dump(exclude={"contract_version"})
            source = fields.pop("provenance", None)
            if source:
                source["source_kind"] = source.pop("kind")
                if source["source_uri"] is not None:
                    source["source_uri"] = str(source["source_uri"])
                fields.update(source)
            if "price" in fields:
                fields.update(fields.pop("price"))
            if key == "retailer":
                fields["status"] = "ACTIVE"
            if key == "product":
                fields.pop("canonical_ingredient_id")
            if key == "reference":
                fields.pop("book")
                fields["book_id"] = f["book"].id
            if key in {"member", "quote"}:
                fields.pop("mapping")
                fields.update(
                    mapping_id=f["mapping"].id,
                    ingredient_id=f["mapping"].ingredient_id,
                    retail_product_id=f["product"].id,
                )
            if key == "member":
                fields["id"] = uuid4()
            if key == "observation":
                fields["is_promotion"] = True
            if key == "quote":
                pair = fields.pop("reference_price_pair")
                fields.update(pair["money_for_reference_quantity"])
                fields["priced_ap_g"] = pair["priced_ap_g"]
                for name in ("package", "observation", "calibration", "reference"):
                    fields.pop(name)
                fields.update(
                    package_id=f["package"].id,
                    granularity="FIXED_PACK",
                    observation_id=f["observation"].id,
                    calibration_id=None,
                    reference_entry_id=None,
                )
                if calibrated:
                    fields.update(
                        evidence_kind="CALIBRATED",
                        amount_minor=55_000,
                        calibration_id=f["calibration"].id,
                    )
            if key == "option":
                fields.pop("quote")
                fields.pop("brittleness_policy_version")
                fields.update(
                    quote_id=f["quote"].id,
                    procurement_class_id=f["cls"].id,
                    depends_on_single_source=False,
                    depends_on_promotion=False,
                )
            insert_sql(conn, table, fields)
        if ambiguous:
            other = uuid4()
            conn.execute(
                text("INSERT INTO ingredients(id,name) VALUES (:id,'Other')"), {"id": other}
            )
            fields = dict(
                conn.execute(text("SELECT * FROM ingredient_product_maps")).mappings().one()
            )
            fields.update(id=uuid4(), ingredient_id=other, external_record_id=str(uuid4()))
            insert_sql(conn, "ingredient_product_maps", fields)
    return f


def test_populated_upgrade_preserves_source_pair_status_and_legacy_flags(legacy_database):
    engine, config = legacy_database
    migrate(engine, config, "0003")
    f = seed_0003(engine)
    with engine.connect() as conn:
        old_observation = row(conn, "price_observations")
        old_mapping = row(conn, "ingredient_product_maps")
    migrate(engine, config, "0004")
    with Session(engine) as db:
        repo = RetailEvidenceRepository(db)
        assert row(db, "price_observations") == old_observation
        assert row(db, "ingredient_product_maps") == old_mapping
        assert row(db, "retail_products")["canonical_ingredient_id"] == f["mapping"].ingredient_id
        quote = repo.get(c.PlanningPriceQuoteDraft, f["quote"].id)
        assert quote.reference_price_pair.money_for_reference_quantity.amount_minor == 50_000
        assert quote.reference_price_pair.priced_ap_g == 500
        assert quote.evidence_kind == "RETAIL_OBSERVED"
        status = repo.retailer_status_at(f["retailer"].id, NOW + timedelta(days=2))
        assert status.status == "ACTIVE" and status.provenance.kind == "LEGACY_STATE"
        assert status.provenance.source_system == "menuto.migration.0004"
        option = repo.get(c.PlanningProcurementOptionDraft, f["option"].id)
        assert option.depends_on_promotion  # Original false assertion is not trusted.
        assert option.brittleness_policy_version == "legacy-unversioned.0003"
        archive = (
            db.execute(text("SELECT * FROM retail_legacy_option_assessments")).mappings().one()
        )
        assert not archive["legacy_depends_on_promotion"]
        assert not archive["legacy_depends_on_single_source"]
    with engine.connect() as conn:
        config.attributes["connection"] = conn
        command.check(config)


@pytest.mark.parametrize("mode", ["calibrated", "unmapped", "ambiguous"])
def test_upgrade_fails_closed_without_reinterpreting_legacy_data(legacy_database, mode):
    engine, config = legacy_database
    migrate(engine, config, "0003")
    seed_0003(engine, **{mode: True})
    with pytest.raises(IntegrityError, match="0004:"):
        migrate(engine, config, "0004")
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0003"
        assert "retailer_status_facts" not in inspect(conn).get_table_names()
        assert conn.scalar(text("SELECT status FROM retailers")) == "ACTIVE"
        if mode == "calibrated":
            assert (
                conn.scalar(text("SELECT evidence_kind FROM planning_price_quotes")) == "CALIBRATED"
            )
            assert conn.scalar(text("SELECT amount_minor FROM planning_price_quotes")) == 55_000
        elif mode == "ambiguous":
            assert conn.scalar(text("SELECT count(*) FROM ingredient_product_maps")) == 2


def test_0004_empty_upgrade_downgrade_upgrade_and_metadata_check(legacy_database):
    engine, config = legacy_database
    migrate(engine, config, "0003")
    for _ in range(2):
        migrate(engine, config, "0004")
        with engine.connect() as conn:
            config.attributes["connection"] = conn
            command.check(config)
        migrate(engine, config, "0003", down=True)
        assert "status" in {x["name"] for x in inspect(engine).get_columns("retailers")}
        assert "canonical_ingredient_id" not in {
            x["name"] for x in inspect(engine).get_columns("retail_products")
        }
    migrate(engine, config, "head")


def test_direct_sql_calibration_only_adjusts_reference_and_never_promotes_availability(db):
    f, repo = seed(db)
    quote = derive_price_quote(
        **f["quote_inputs"], reference=f["reference"], calibration=f["calibration"]
    )
    repo.add(quote)
    stored = row(db, "planning_price_quotes", quote.id)
    assert stored["reference_amount_minor"] == 66_000 and stored["reference_ap_g"] == 1000
    assert stored["observation_id"] is None
    for changes in (
        {"reference_amount_minor": 55_000},
        {"evidence_kind": "CALIBRATED"},
        {"observation_id": f["observation"].id},
        {"reference_entry_id": None},
        {"price_basis": "PACKAGE_TOTAL"},
    ):
        rejected_sql(db, "planning_price_quotes", stored | {"id": uuid4()} | changes)
    observed = row(db, "planning_price_quotes", f["quote"].id)
    rejected_sql(
        db,
        "planning_price_quotes",
        observed
        | {
            "id": uuid4(),
            "calibration_id": f["calibration"].id,
        },
    )


def test_product_has_one_ingredient_but_multiple_yield_evidence_versions(db):
    f, repo = seed(db)
    revised = changed(
        f["mapping"], id=uuid4(), version="2", edible_yield="0.9", provenance=provenance()
    )
    repo.add(revised)
    assert repo.get(c.IngredientProductMapFact, revised.id) == revised
    from app.modules.catalog.models import Ingredient

    other = uuid4()
    db.add(Ingredient(id=other, name="Other canonical ingredient"))
    db.flush()
    fields = duplicate_fields(db, "ingredient_product_maps", f["mapping"].id) | {
        "ingredient_id": other
    }
    rejected_sql(db, "ingredient_product_maps", fields, code="23503")
    with pytest.raises(ValueError, match="canonical procurement ingredient"):
        repo.add(changed(revised, id=uuid4(), ingredient_id=other))


def test_status_transitions_keep_retailer_identity_and_effective_history(db):
    f, repo = seed(db)
    rid = f["retailer"].id
    assert repo.retailer_status_at(rid, NOW - timedelta(seconds=1)) is None
    later = changed(
        f["retailer_status"],
        id=uuid4(),
        status="INACTIVE",
        effective_at=NOW + timedelta(days=1),
        provenance=c.RetailerStatusProvenance(**provenance().model_dump()),
    )
    repo.add(later)
    assert repo.retailer_status_at(rid, NOW).status == "ACTIVE"
    assert repo.retailer_status_at(rid, later.effective_at) == later
    assert repo.get(c.RetailerFact, rid) == f["retailer"]
    rejected_sql(
        db,
        "retailer_status_facts",
        duplicate_fields(db, "retailer_status_facts", later.id),
        code="23505",
    )
    fields = duplicate_fields(db, "retailer_status_facts", later.id)
    for override in ({"status": "GUARANTEED"}, {"effective_at": "infinity"}):
        rejected_sql(db, "retailer_status_facts", fields | override)


def test_no_sql_columns_or_contract_inputs_for_authored_fragility_flags(db):
    f, repo = seed(db)
    with pytest.raises(ProgrammingError) as error, db.begin_nested():
        db.execute(text("UPDATE planning_procurement_options SET depends_on_promotion=false"))
    assert error.value.orig.sqlstate == "42703"
    snapshot = repo.procurement_snapshot(f["cls"].id)
    assert snapshot.source_coverage.depends_on_single_source
    assert "depends_on_single_source" not in type(snapshot.options[0]).model_fields
    assert "amount_minor" not in {
        x["name"] for x in inspect(db.connection()).get_columns("planning_price_quotes")
    }


@pytest.mark.parametrize(
    "provider,availability,dependent",
    [
        ("synthetic", "LIKELY", True),
        ("provider-b", "LIKELY", False),
        ("provider-b", "UNAVAILABLE", True),
    ],
)
def test_two_retailer_coverage_requires_independent_provider_and_usable_path(
    db, provider, availability, dependent
):
    f, repo = seed(db)
    retailer = changed(f["retailer"], id=uuid4())
    region = changed(f["region"], id=uuid4(), retailer_id=retailer.id)
    product = changed(f["product"], id=uuid4(), retailer_id=retailer.id, provenance=provenance())
    pack = changed(f["package"], id=uuid4(), retail_product_id=product.id, provenance=provenance())
    mapping = changed(
        f["mapping"], id=uuid4(), retail_product_id=product.id, provenance=provenance()
    )
    member = changed(f["member"], mapping=mapping, provenance=provenance())
    observation = changed(
        f["observation"],
        id=uuid4(),
        retailer_id=retailer.id,
        store_region_id=region.id,
        retail_product_id=product.id,
        package_id=pack.id,
        availability=availability,
        provenance=provenance("RETAIL_OBSERVATION", source_system=provider),
    )
    quote = derive_price_quote(
        **(
            f["quote_inputs"]
            | dict(
                mapping=mapping,
                package=pack,
                retailer_id=retailer.id,
                store_region_id=region.id,
            )
        ),
        observation=observation,
    )
    option = changed(f["option"], id=uuid4(), rank=1, quote=quote, provenance=provenance())
    for fact in (retailer, region, product, pack, mapping, member, observation, quote, option):
        repo.add(fact)
    coverage = repo.procurement_snapshot(f["cls"].id).source_coverage
    assert coverage.depends_on_single_source is dependent
    assert coverage.observed_retailer_count == (1 if availability == "UNAVAILABLE" else 2)


@pytest.mark.parametrize("action", ["UPDATE", "DELETE", "TRUNCATE"])
def test_legacy_assessment_archive_is_immutable(legacy_database, action):
    engine, config = legacy_database
    migrate(engine, config, "0003")
    seed_0003(engine)
    migrate(engine, config, "0004")
    with Session(engine) as db:
        sql = {
            "UPDATE": "UPDATE retail_legacy_option_assessments "
            "SET legacy_depends_on_promotion=true",
            "DELETE": "DELETE FROM retail_legacy_option_assessments",
            "TRUNCATE": "TRUNCATE retail_legacy_option_assessments",
        }[action]
        with pytest.raises(IntegrityError), db.begin_nested():
            db.execute(text(sql))
    with pytest.raises(IntegrityError, match="0004 downgrade cannot preserve"):
        migrate(engine, config, "0003", down=True)


def test_archive_cannot_accept_new_authored_flags_after_migration(db):
    f, _ = seed(db)
    rejected_sql(db, "retail_legacy_option_assessments", {
        "option_id": f["option"].id, "legacy_depends_on_promotion": False,
        "legacy_depends_on_single_source": False,
    })
