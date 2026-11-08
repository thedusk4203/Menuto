"""Test-owned direct/transitive purity and exact authorized-preimage verification."""

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"
_PURE = (
    "app.modules.policy.explicit_intent",
    "app.modules.policy.explicit_intent_contracts",
    "app.modules.policy.explicit_intent_public",
    "app.modules.validation.explicit_plan_intent",
)


def imports(source):
    result = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            result.update(item.name for item in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert not node.level
            target = node.module or ""
            for item in node.names:
                assert item.name != "*"
                if target == "app.modules.policy":
                    result.add(target + "." + item.name)
                else:
                    result.add(target)
    return result


def independent_graph(graph, start="app.modules.validation.explicit_plan_intent"):
    visited, pending = set(), [start]
    while pending:
        module = pending.pop()
        if module in visited:
            continue
        visited.add(module)
        for target in imports(graph[module]):
            if target.startswith("app.modules.policy"):
                assert target == "app.modules.policy.explicit_intent_contracts", target
            if target in graph:
                pending.append(target)


def verify_independence():
    graph = {m: (ROOT / "apps/backend" / (m.replace(".", "/") + ".py")).read_text() for m in _PURE}
    independent_graph(graph)
    assert "explicit_intent_public" not in graph["app.modules.validation.explicit_plan_intent"]


def verify_purity():
    allowed = {
        "json",
        "re",
        "datetime",
        "uuid",
        "typing",
        "pydantic",
        "app.domain.canonical",
        "app.domain.contracts",
        "app.domain.snapshots",
        "app.domain.units",
        "app.modules.policy.explicit_intent_contracts",
    }
    for module in _PURE:
        source = (ROOT / "apps/backend" / (module.replace(".", "/") + ".py")).read_text()
        permitted = set(allowed)
        if module.endswith("explicit_intent_public"):
            permitted.add("app.modules.policy.explicit_intent")
        assert imports(source) <= permitted, (module, imports(source) - permitted)
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in {"open", "eval", "exec", "__import__", "input"}
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in {
                        "now",
                        "utcnow",
                        "today",
                        "time",
                        "getenv",
                        "monotonic",
                        "connect",
                    }


def restore_metadata(path, body, package):
    for edit in reversed(package["files"][path]["edits"]):
        assert body.count(edit["after"]) == 1, path
        body = body.replace(edit["after"], edit["before"], 1)
    return body


def verify_metadata_patch():
    package = json.loads((FIXTURES / "explicit_plan_intent_authorized_metadata.json").read_text())
    proof = json.loads((FIXTURES / "explicit_plan_intent_compatibility.json").read_text())
    assert len(package["files"]) == 8
    assert sum(len(data["edits"]) for data in package["files"].values()) == 17
    assert set(package["files"]) == set(proof["guard_preimages"])
    for path in package["files"]:
        body = (ROOT / path).read_text()
        original = restore_metadata(path, body, package)
        assert hashlib.sha256(original.encode()).hexdigest() == proof["guard_preimages"][path]
        assert hashlib.sha256(body.encode()).hexdigest() == package["files"][path]["after_sha256"]
