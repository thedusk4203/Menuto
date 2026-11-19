"""Test-only exact Identity inverse, before unchanged EPI/PIV historical inverses."""

import ast
import hashlib
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

IDENTITY_EXPORT_NAMES = (
    "IdentityEffectiveRequestV1",
    "IdentityRoleFactV1",
    "IdentityRoleEdgeV1",
    "IdentityPrivilegeObjectFactV1",
    "IdentitySessionFactV1",
    "IdentityRootCommandV1",
    "IdentityIssuerCommandV1",
    "IdentityBindingCommandV1",
    "IdentityOperationGrantCommandV1",
    "IdentityRecordedFactV1",
    "IdentityCommandReceiptV1",
    "IdentityRequestBindingV1",
    "IdentityMembershipWitnessV1",
    "IdentitySourceFrontierV1",
    "IdentityCaptureFrameV1",
    "IdentitySourceSnapshotV1",
    "IdentityCaptureFailureV1",
    "IdentitySourceCheckV1",
    "AuthenticatedPlanIntentInspectionV1",
)
PACKAGE_SHA256 = "f82f527841e4cc2e2c9097bf6fa36226c19e3d9397531d75c8a30e8d305095d3"


def _digest(body):
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _package():
    raw = (FIXTURES / "identity_source_authorized_metadata.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PACKAGE_SHA256
    package = json.loads(raw)
    assert package["baseline"] == "120d28f62b66720e8631b64e0b2a50cdc57e6c42"
    assert len(package["files"]) == 35
    return package


IDENTITY_MIGRATION_REVISION = "0018"

# Separately authorized patch36; the immutable PR147 package remains exactly35 entries.
MTR040B_AUTHORIZED_ADDITIONAL_PATCH = {
    "baseline": "68fcb688231460f1973077eb20140b8c5db440a2",
    "authorization": "https://github.com/thedusk4203/Menuto/pull/148#issuecomment-6969179602",
    "path": "apps/backend/tests/test_target_affinity.py",
    "before": (
        '        "apps/backend/migrations/versions/0017_nutrition_synthesis_sources.py",\n'
        "    }"
    ),
    "after": (
        '        "apps/backend/migrations/versions/0017_nutrition_synthesis_sources.py",\n'
        '        "apps/backend/migrations/versions/0018_identity_principal_user_sources.py",\n'
        "    }"
    ),
    "before_sha256": "4196726aa225684fb294dbe4f7e1cd917f51180c44368c0f943a67be55e47f13",
    "after_sha256": "13fb1dee71b83ff6f3789133fe8481e3738458e9a87a9f05a718b9041f65746f",
    "receipt_path": "apps/backend/tests/target_affinity_compatibility.json",
    "receipt_sha256": "61ccf6b0bb0c10bfc3979e062b7a3dc9563f6f694620bd8c706dab16ac9636b5",
    "migration_path": "apps/backend/migrations/versions/0018_identity_principal_user_sources.py",
    "migration_sha256": "27282e130042a202da2fee1c4e1d05dc97c2512c3dea9f380d4af8696659d7de",
}


def _restore_mtr040b_patch(body):
    item = MTR040B_AUTHORIZED_ADDITIONAL_PATCH
    assert _digest(body) == item["after_sha256"]
    assert body.count(item["after"]) == 1
    restored = body.replace(item["after"], item["before"], 1)
    assert _digest(restored) == item["before_sha256"]
    return restored


def assert_mtr040b_compatibility_patch(root):
    item = MTR040B_AUTHORIZED_ADDITIONAL_PATCH
    _restore_mtr040b_patch((root / item["path"]).read_bytes().decode("utf-8"))
    assert (
        hashlib.sha256((root / item["receipt_path"]).read_bytes()).hexdigest()
        == item["receipt_sha256"]
    )


def restore_identity_metadata(path, body):
    path = str(path).replace("\\", "/")
    package = _package()
    baseline = json.loads((FIXTURES / "identity_source_compatibility.json").read_text())
    assert path in baseline["baseline_files"], path
    if path == MTR040B_AUTHORIZED_ADDITIONAL_PATCH["path"]:
        restored = _restore_mtr040b_patch(body)
        assert _digest(restored) == baseline["baseline_files"][path]
        return restored
    if path not in package["files"]:
        assert _digest(body) == baseline["baseline_files"][path], path
        return body
    item = package["files"][path]
    assert _digest(body) == item["after_sha256"], path
    for edit in reversed(item["editorial"]):
        assert body.count(edit["after"]) == 1, path
        body = body.replace(edit["after"], edit["before"], 1)
    assert _digest(body) == item["approved_after_sha256"], path
    lines = body.splitlines(keepends=True)
    for edit in reversed(item["edits"]):
        start = edit["new_line"] - 1 if edit["new_count"] else edit["new_line"]
        expected = edit["after"].splitlines(keepends=True)
        assert lines[start : start + edit["new_count"]] == expected, path
        lines[start : start + edit["new_count"]] = edit["before"].splitlines(keepends=True)
    original = "".join(lines)
    assert _digest(original) == item["before_sha256"] == baseline["baseline_files"][path], path
    return original


def assert_identity_migration_delta(root):
    proof = json.loads((FIXTURES / "identity_source_migration_manifest.json").read_text())
    assert proof["revision"] == IDENTITY_MIGRATION_REVISION and proof["down_revision"] == "0017"
    assert proof["filename"] == "0018_identity_principal_user_sources.py"
    assert proof["private_tables"] == [
        "command_receipts",
        "frontiers",
        "issuers",
        "operation_grants",
        "principal_bindings",
        "roots",
    ]
    assert proof["public_tables"] == 108 and proof["installed_domain_tables"] == 114
    directory = root / "apps/backend/migrations/versions"
    actual = {p.name for p in directory.glob("*.py")}
    assert len(proof["old_migrations"]) == 17
    assert actual == set(proof["old_migrations"]) | {proof["filename"]}
    for name, digest in proof["old_migrations"].items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest, name
    assert (
        hashlib.sha256((directory / proof["filename"]).read_bytes()).hexdigest()
        == (MTR040B_AUTHORIZED_ADDITIONAL_PATCH["migration_sha256"])
    )
    assignments = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in ast.parse((directory / proof["filename"]).read_text()).body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in {"revision", "down_revision"}
    }
    assert assignments == dict(revision=IDENTITY_MIGRATION_REVISION, down_revision="0017")
