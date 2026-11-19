"""Authorized MTR040B patch36: exact inverse and mutation proofs for ITR089/094."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from identity_compatibility_metadata import (
    MTR040B_AUTHORIZED_ADDITIONAL_PATCH as PATCH,
)
from identity_compatibility_metadata import (
    PACKAGE_SHA256,
    _package,
    assert_identity_migration_delta,
    assert_mtr040b_compatibility_patch,
    restore_identity_metadata,
)

ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS = "apps/backend/migrations/versions"
RECEIPT = ROOT / PATCH["receipt_path"]
ORIGINAL_MIGRATIONS = sorted(json.loads(RECEIPT.read_text())["released_migrations"])


def _sha(body):
    return hashlib.sha256(body).hexdigest()


def test_identity_patch36_exact_inverse_and_unchanged35_ledger():
    assert PATCH["baseline"] == "68fcb688231460f1973077eb20140b8c5db440a2"
    assert PATCH["authorization"].endswith("/148#issuecomment-6969179602")
    assert PATCH["before_sha256"] == (
        "4196726aa225684fb294dbe4f7e1cd917f51180c44368c0f943a67be55e47f13"
    )
    assert PATCH["after_sha256"] == (
        "13fb1dee71b83ff6f3789133fe8481e3738458e9a87a9f05a718b9041f65746f"
    )
    body = (ROOT / PATCH["path"]).read_bytes().decode()
    restored = restore_identity_metadata(PATCH["path"], body)
    assert _sha(restored.encode()) == PATCH["before_sha256"]
    assert body == restored.replace(PATCH["before"], PATCH["after"], 1)
    assert_mtr040b_compatibility_patch(ROOT)
    assert_identity_migration_delta(ROOT)
    package = _package()
    assert len(package["files"]) == 35 and PATCH["path"] not in package["files"]
    ledger = json.loads(
        (ROOT / "docs/product/IDENTITY_EXISTING_FILE_PATCH_LEDGER.json").read_text()
    )
    assert ledger["original35"] == package["files"]
    assert ledger["original35_package_sha256"] == PACKAGE_SHA256
    assert ledger["separately_authorized36"] == PATCH
    assert ledger["existing_file_patch_count"] == 36
    assert ledger["historical_package_rewritten"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "baseline_not_postimage",
        "extra_source",
        "duplicate_insertion",
        "altered_literal",
        "altered_preimage",
        "changed_surrounding",
        "crlf_postimage",
    ],
)
def test_identity_patch36_rejects_nonexact_source(mutation):
    body = (ROOT / PATCH["path"]).read_bytes().decode()
    if mutation == "baseline_not_postimage":
        body = body.replace(PATCH["after"], PATCH["before"], 1)
    elif mutation == "extra_source":
        body += "\n# unapproved source\n"
    elif mutation == "duplicate_insertion":
        line = '        "' + PATCH["migration_path"] + '",\n'
        body = body.replace(line, line * 2, 1)
    elif mutation == "altered_literal":
        body = body.replace("0018_identity_principal_user_sources.py", "0019_not_authorized.py")
    elif mutation == "altered_preimage":
        body = body.replace(PATCH["after"], PATCH["before"] + "\n# stale preimage", 1)
    elif mutation == "changed_surrounding":
        body = body.replace('assert len(receipt["schema_definitions"]) == 237', "assert True", 1)
    else:
        body = body.replace("\n", "\r\n")
    with pytest.raises(AssertionError):
        restore_identity_metadata(PATCH["path"], body)


@pytest.fixture
def historical_tree(tmp_path, monkeypatch):
    import test_target_affinity as historical

    receipt = json.loads(RECEIPT.read_text())
    names = set(receipt["definitions"]) | {
        PATCH["path"],
        PATCH["receipt_path"],
        "packages/contracts/domain.schema.json",
    }
    names |= {p.relative_to(ROOT).as_posix() for p in (ROOT / MIGRATIONS).glob("*.py")}
    for name in names:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    monkeypatch.setattr(historical, "__file__", str(tmp_path / PATCH["path"]))
    monkeypatch.chdir(tmp_path)
    return (
        tmp_path,
        historical.test_all_frozen_040a_041abcde_046a_definitions_and_migrations_retained,
    )


def test_identity_original040b_assertions_execute_unchanged(historical_tree):
    root, original = historical_tree
    assert_mtr040b_compatibility_patch(root)
    assert_identity_migration_delta(root)
    original()  # Original AST pins, 237 definitions, 13 text hashes and exact filename set.


@pytest.mark.parametrize("name", ORIGINAL_MIGRATIONS)
def test_identity_old_migration_body_mutation_rejected_by_both_guards(historical_tree, name):
    root, original = historical_tree
    path = root / name
    path.write_bytes(path.read_bytes() + b"\n# unauthorized body mutation\n")
    with pytest.raises(AssertionError):
        original()
    with pytest.raises(AssertionError):
        assert_identity_migration_delta(root)


@pytest.mark.parametrize("mutation", ["delete_old", "rename_old", "extra0019", "extra_unknown"])
def test_identity_migration_filename_mutation_rejected_by_both_guards(historical_tree, mutation):
    root, original = historical_tree
    first = root / ORIGINAL_MIGRATIONS[0]
    if mutation == "delete_old":
        first.unlink()
    elif mutation == "rename_old":
        first.rename(first.with_name("0001_unauthorized_rename.py"))
    else:
        name = "0019_unauthorized.py" if mutation == "extra0019" else "unexpected.py"
        (root / MIGRATIONS / name).write_text("# unauthorized migration\n")
    with pytest.raises((AssertionError, FileNotFoundError)):
        original()
    with pytest.raises(AssertionError):
        assert_identity_migration_delta(root)


@pytest.mark.parametrize("mutation", ["name", "revision", "down_revision", "body"])
def test_identity0018_exact_manifest_rejects_drift(historical_tree, mutation):
    root, _ = historical_tree
    path = root / PATCH["migration_path"]
    body = path.read_text()
    if mutation == "name":
        path.rename(path.with_name("0018_unauthorized.py"))
    else:
        if mutation == "body":
            body += "\n# unauthorized body drift\n"
        elif mutation == "revision":
            assert 'revision = "0018"' in body
            body = body.replace('revision = "0018"', 'revision = "0019"', 1)
        else:
            assert 'down_revision = "0017"' in body
            body = body.replace('down_revision = "0017"', 'down_revision = "0016"', 1)
        path.write_text(body)
    with pytest.raises(AssertionError):
        assert_identity_migration_delta(root)


def test_identity_original_receipt_mutation_rejected(historical_tree):
    root, _ = historical_tree
    path = root / PATCH["receipt_path"]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(AssertionError):
        assert_mtr040b_compatibility_patch(root)
