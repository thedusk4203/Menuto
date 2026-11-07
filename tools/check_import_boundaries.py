"""Static dependency checks for Menuto's modular monolith, no third-party dependency."""

import argparse
import ast
import importlib.util
from pathlib import Path

ALLOWED = {
    "identity": set(),
    "households": {"identity"},
    "catalog": set(),
    "nutrition": {"households", "catalog"},
    "recipes": {"catalog"},
    "retail": {"catalog"},
    "inventory": {"households", "catalog", "retail"},
    "preferences": {"households", "catalog", "recipes"},
    "policy": {"households", "nutrition", "preferences"},
    "cooking": {"households", "catalog", "recipes"},
    "planning": {
        "households",
        "nutrition",
        "catalog",
        "recipes",
        "retail",
        "inventory",
        "policy",
        "cooking",
        "shopping",
        "preferences",
        "validation",
        "learning",
    },
    "shopping": {"households", "retail", "inventory", "planning"},
    "execution": {
        "catalog",
        "nutrition",
        "recipes",
        "households",
        "planning",
        "cooking",
        "inventory",
        "shopping",
        "validation",
        "learning",
    },
    "validation": {
        "households",
        "nutrition",
        "catalog",
        "recipes",
        "retail",
        "inventory",
        "policy",
        "planning",
        "cooking",
        "shopping",
        "execution",
        "preferences",
    },
    "learning": {
        "households",
        "catalog",
        "recipes",
        "retail",
        "preferences",
        "planning",
        "cooking",
        "shopping",
        "execution",
    },
    "assistant": {
        "households",
        "catalog",
        "recipes",
        "retail",
        "policy",
        "planning",
        "preferences",
    },
}
PUBLIC_SURFACES = {"contracts", "public"}
# V1.3 ADR-010/011: immutable facts may cross these seams; runtime facades may not.
CONTRACT_ONLY_CONTEXTS = {"validation", "learning"}

# Reviewed TasteFit companion seam: exact modules, not a new public namespace
# exemption for private Preferences implementations or other Planning consumers.
TASTEFIT_COMPANIONS = {
    "app.modules.planning.tastefit": {
        "app.modules.preferences.tastefit_contracts",
        "app.modules.preferences.tastefit_public",
    },
    "app.modules.planning.tastefit_contracts": {
        "app.modules.preferences.tastefit_contracts",
    },
    "app.modules.planning.tastefit_capture": {
        "app.modules.preferences.tastefit_contracts",
        "app.modules.preferences.tastefit_public",
    },
}
TASTEFIT_PURE_IMPORTS = {
    "pydantic", "app.domain.feature_identity", "app.domain.resolution",
    "app.modules.planning.tastefit_contracts",
    "app.modules.planning.candidate_feature_projection",
    "app.modules.preferences.contracts", "app.modules.preferences.tastefit_contracts",
    "app.modules.preferences.tastefit_public", "app.modules.recipes.contracts",
}
TASTEFIT_TRANSPORT_IMPORTS = {
    "app.modules.planning.tastefit_contracts": {
        "math", "typing", "uuid", "pydantic", "app.domain.contracts",
        "app.domain.feature_identity", "app.domain.units", "app.modules.planning.contracts",
        "app.modules.preferences.contracts", "app.modules.preferences.tastefit_contracts",
        "app.modules.recipes.contracts",
    },
    "app.modules.preferences.tastefit_contracts": {
        "typing", "uuid", "pydantic", "app.domain.contracts", "app.domain.feature_identity",
        "app.modules.catalog.contracts", "app.modules.preferences.contracts",
        "app.modules.preferences.hierarchical_affinity_contracts",
        "app.modules.preferences.hierarchy_contracts",
        "app.modules.preferences.prior_affinity_contracts",
        "app.modules.recipes.contracts",
    },
}

# Additive shared-target Modules consume frozen Planning children only. These
# exact guards do not extend TASTEFIT_COMPANIONS or any existing context grant.
SHARED_TARGET_IMPORTS = {
    "app.modules.planning.shared_target_tastefit_contracts": {
        "math", "typing", "uuid", "pydantic", "app.domain.contracts",
        "app.domain.feature_identity", "app.domain.units", "app.modules.households.contracts",
        "app.modules.planning.contracts", "app.modules.planning.tastefit_contracts",
    },
    "app.modules.planning.shared_target_tastefit": {
        "fractions", "math", "pydantic", "app.domain.feature_identity", "app.domain.resolution",
        "app.modules.planning.shared_target_tastefit_contracts",
        "app.modules.planning.tastefit_contracts", "app.modules.planning.tastefit_public",
    },
    "app.modules.planning.shared_target_tastefit_capture": {
        "sqlalchemy", "app.domain.resolution",
        "app.modules.planning.candidate_feature_capture",
        "app.modules.planning.candidate_feature_projection",
        "app.modules.planning.shared_target_tastefit",
        "app.modules.planning.shared_target_tastefit_contracts",
        "app.modules.planning.tastefit_public",
    },
}

# Approved NRC companion: one immutable Nutrition handoff to one independent
# Validation implementation. This does not widen existing public surfaces.
NUTRITION_ROOT_PURE_IMPORTS = {
    "app.modules.nutrition.root_resolution": {
        "fractions", "app.domain.feature_identity", "app.modules.nutrition.root_contracts",
        "app.modules.nutrition.root_limits",
    },
    "app.modules.nutrition.root_contracts": {
        "math", "typing", "uuid", "pydantic", "app.domain.contracts",
        "app.domain.feature_identity", "app.modules.households.contracts",
        "app.modules.nutrition.root_limits",
    },
    "app.modules.nutrition.root_limits": {"datetime", "uuid", "pydantic"},
    "app.modules.validation.nutrition_roots": {
        "fractions", "app.domain.feature_identity", "app.modules.nutrition.root_contracts",
    },
}

# Approved NPS companion: immutable source transport and an independently owned
# Validation implementation. Producer business logic is never a validation oracle.
NUTRITION_SYNTHESIS_PURE_IMPORTS = {
    "app.modules.nutrition.synthesis_contracts": {
        "math", "typing", "uuid", "pydantic", "app.domain.contracts",
        "app.modules.nutrition.root_contracts",
    },
    "app.modules.nutrition.synthesis_journal": {
        "app.domain.feature_identity", "app.modules.nutrition.root_contracts",
        "app.modules.nutrition.synthesis_contracts",
    },
    "app.modules.nutrition.synthesis": {
        "json", "dataclasses", "fractions", "app.domain.feature_identity",
        "app.modules.nutrition.root_contracts", "app.modules.nutrition.root_public",
        "app.modules.nutrition.synthesis_contracts", "app.modules.nutrition.synthesis_journal",
    },
    "app.modules.validation.nutrition_policy": {
        "json", "fractions", "app.domain.feature_identity",
        "app.modules.nutrition.root_contracts", "app.modules.nutrition.synthesis_contracts",
        "app.modules.validation.nutrition_roots",
    },
}


# NRE additions are exact companion seams, not new cross-context grants. Existing
# NRC/NPS allowlists and frozen producer/checker import constraints are unchanged.
NUTRITION_RESOLUTION_IMPORTS = {
    "app.modules.nutrition.resolution_contracts": {
        "math", "typing", "uuid", "pydantic", "app.domain.contracts",
        "app.domain.feature_identity", "app.modules.catalog.contracts",
        "app.modules.households.contracts", "app.modules.recipes.contracts",
        "app.modules.nutrition.root_contracts", "app.modules.nutrition.synthesis_contracts",
        "app.modules.nutrition.resolution_limits",
    },
    "app.modules.nutrition.resolution_estimator": {
        "fractions", "itertools", "app.domain.feature_identity",
        "app.modules.nutrition.resolution_contracts", "app.modules.nutrition.resolution_limits",
        "app.modules.nutrition.synthesis",
    },
    "app.modules.nutrition.resolution_limits": {
        "json", "datetime", "decimal", "uuid", "pydantic",
    },
    "app.modules.validation.nutrition_resolution_authority": {
        "app.domain.feature_identity", "app.modules.nutrition.root_contracts",
        "app.modules.nutrition.synthesis_contracts",
    },
    "app.modules.validation.nutrition_resolution": {
        "fractions", "itertools", "app.domain.feature_identity",
        "app.modules.nutrition.resolution_contracts", "app.modules.nutrition.root_contracts",
        "app.modules.nutrition.synthesis_contracts", "app.modules.nutrition.resolution_limits",
        "app.modules.validation.nutrition_resolution_authority",
        "app.modules.validation.nutrition_roots",
    },
    "app.modules.planning.nutrition_resolution_capture": {
        "dataclasses", "threading", "time", "sqlalchemy", "app.modules.catalog.resolution_public",
        "app.modules.households.resolution_public", "app.modules.recipes.resolution_public",
        "app.modules.nutrition.root_public", "app.modules.nutrition.resolution_contracts",
        "app.modules.nutrition.resolution_limits", "app.modules.nutrition.synthesis",
        "app.modules.nutrition.synthesis_contracts", "app.modules.nutrition.synthesis_sources",
    },
    "app.modules.nutrition.resolution_public": {
        "app.modules.nutrition.resolution_contracts", "app.modules.nutrition.resolution_estimator",
    },
}


# MBA companion: exact additive imports only. No expansion of frozen NRE allowances.
BASIS_COMPANION_IMPORTS = {
    "app.modules.nutrition.basis_contracts": {
        "typing", "pydantic", "app.domain.contracts", "app.domain.feature_identity",
        "app.modules.households.contracts", "app.modules.nutrition.root_contracts",
        "app.modules.nutrition.resolution_contracts", "app.modules.nutrition.resolution_limits",
    },
    "app.modules.nutrition.basis_projection": {
        "json", "app.domain.feature_identity", "app.modules.nutrition.basis_contracts",
        "app.modules.nutrition.root_contracts", "app.modules.nutrition.synthesis",
        "app.modules.nutrition.synthesis_journal",
        "app.modules.nutrition.resolution_limits",
    },
    "app.modules.nutrition.basis_applicability": {
        "app.domain.feature_identity", "app.modules.nutrition.basis_contracts",
        "app.modules.nutrition.basis_projection", "app.modules.nutrition.resolution_estimator",
        "app.modules.nutrition.resolution_limits",
    },
    "app.modules.validation.basis_applicability": {
        "json", "app.domain.feature_identity", "app.modules.nutrition.basis_contracts",
        "app.modules.nutrition.root_contracts", "app.modules.nutrition.resolution_limits",
        "app.modules.validation.nutrition_resolution",
        "app.modules.validation.nutrition_resolution_authority",
    },
    "app.modules.planning.basis_capture": {
        "dataclasses", "threading", "time", "weakref", "sqlalchemy",
        "app.domain.feature_identity", "app.modules.nutrition.basis_contracts",
        "app.modules.nutrition.basis_applicability", "app.modules.nutrition.basis_projection",
        "app.modules.nutrition.resolution_contracts", "app.modules.nutrition.resolution_estimator",
        "app.modules.nutrition.resolution_limits",
        "app.modules.planning.nutrition_resolution_capture",
    },
    "app.modules.planning.basis_host": {
        "concurrent.futures", "app.modules.nutrition.basis_applicability",
        "app.modules.validation.basis_applicability",
    },
}


# PIV2 exact additive companion seams; frozen allowlists remain unchanged.
POLICY_V2_IMPORTS = {
    "app.modules.nutrition.policy_v2": {
        "app.domain.feature_identity",
        "app.modules.nutrition.basis_applicability",
        "app.modules.nutrition.basis_contracts",
        "app.modules.nutrition.policy_v2_contracts",
        "app.modules.nutrition.policy_v2_limits",
        "app.modules.nutrition.policy_v2_rules",
        "app.modules.nutrition.resolution_contracts",
        "app.modules.nutrition.root_public",
        "app.modules.nutrition.synthesis",
        "app.modules.nutrition.synthesis_journal",
        "fractions",
    },
    "app.modules.nutrition.policy_v2_contracts": {
        "app.domain.contracts",
        "app.domain.feature_identity",
        "app.modules.households.contracts",
        "app.modules.nutrition.basis_contracts",
        "app.modules.nutrition.resolution_contracts",
        "app.modules.nutrition.resolution_limits",
        "app.modules.nutrition.root_contracts",
        "app.modules.nutrition.synthesis_contracts",
        "pydantic",
        "typing",
        "uuid",
    },
    "app.modules.nutrition.policy_v2_limits": {
        "app.domain.feature_identity",
        "app.modules.nutrition.resolution_limits",
    },
    "app.modules.nutrition.policy_v2_public": {
        "app.domain.feature_identity",
        "app.modules.nutrition.basis_contracts",
        "app.modules.nutrition.policy_v2",
        "app.modules.nutrition.policy_v2_contracts",
    },
    "app.modules.nutrition.policy_v2_rules": {
        "app.domain.feature_identity",
        "app.modules.nutrition.root_contracts",
        "app.modules.nutrition.synthesis_contracts",
        "dataclasses",
        "fractions",
    },
    "app.modules.planning.policy_v2_capture": {
        "app.domain.feature_identity",
        "app.modules.nutrition.policy_v2_contracts",
        "app.modules.nutrition.policy_v2_public",
        "app.modules.planning.basis_capture",
        "app.modules.planning.policy_v2_worker",
        "dataclasses",
        "multiprocessing",
        "os",
        "sqlalchemy",
        "threading",
        "time",
        "weakref",
    },
    "app.modules.planning.policy_v2_worker": {
        "app.domain.feature_identity",
        "app.modules.nutrition.policy_v2",
        "app.modules.nutrition.policy_v2_contracts",
        "app.modules.nutrition.resolution_limits",
        "app.modules.validation.nutrition_policy_v2",
    },
    "app.modules.validation.nutrition_policy_v2": {
        "app.domain.feature_identity",
        "app.modules.nutrition.basis_contracts",
        "app.modules.nutrition.policy_v2_contracts",
        "app.modules.nutrition.policy_v2_limits",
        "app.modules.nutrition.resolution_contracts",
        "app.modules.nutrition.resolution_limits",
        "app.modules.nutrition.root_contracts",
        "app.modules.nutrition.synthesis_contracts",
        "app.modules.validation.basis_applicability",
        "app.modules.validation.nutrition_policy_v2_rules",
        "app.modules.validation.nutrition_resolution",
        "app.modules.validation.nutrition_resolution_authority",
        "app.modules.validation.nutrition_roots",
        "fractions",
    },
    "app.modules.validation.nutrition_policy_v2_rules": {
        "app.domain.feature_identity",
        "app.modules.nutrition.root_contracts",
        "app.modules.nutrition.synthesis_contracts",
        "fractions",
    },
}


def check_source(source: str, module: str, *, is_package: bool = False) -> list[str]:
    tree = ast.parse(source)
    parts = module.split(".")
    context = parts[2] if len(parts) > 2 and parts[:2] == ["app", "modules"] else None
    contract = len(parts) > 3 and parts[3] == "contracts"
    shared = module == "app.shared" or module.startswith("app.shared.")
    neutral = module == "app.domain" or module.startswith("app.domain.")
    errors = []
    capture_import_lines = {
        n.lineno for fn in tree.body if isinstance(fn, ast.FunctionDef)
        and fn.name == "capture_tastefit_member_sources"
        for n in ast.walk(fn) if isinstance(n, ast.ImportFrom)
    }

    def audit(target, line):
        if module in POLICY_V2_IMPORTS:
            if not any(
                target == p or target.startswith(p + ".") for p in POLICY_V2_IMPORTS[module]
            ):
                errors.append(f"{line}: POLICY_V2_PURE_OR_INDEPENDENT_BOUNDARY: {target}")
            return
        if module in BASIS_COMPANION_IMPORTS:
            if not any(target == p or target.startswith(p + ".")
                       for p in BASIS_COMPANION_IMPORTS[module]):
                errors.append(f"{line}: MBA_INDEPENDENT_OR_PURE_BOUNDARY: {target}")
            return
        if module in NUTRITION_RESOLUTION_IMPORTS:
            if not any(target == p or target.startswith(p + ".")
                       for p in NUTRITION_RESOLUTION_IMPORTS[module]):
                errors.append(f"{line}: NRE_PURE_OR_INDEPENDENT_BOUNDARY: {target}")
            # Exact, closed companion imports are checked above. Do not widen the
            # general Nutrition->Recipes or Validation->producer grants below.
            return
        nrc_transport = module == "app.modules.validation.nutrition_roots" and (
            target == "app.modules.nutrition.root_contracts"
            or target.startswith("app.modules.nutrition.root_contracts.")
        )
        nrc_transport = nrc_transport or (
            module == "app.modules.validation.nutrition_policy" and any(
                target == p or target.startswith(p + ".")
                for p in {"app.modules.nutrition.root_contracts",
                          "app.modules.nutrition.synthesis_contracts"}
            )
        )
        if module in NUTRITION_SYNTHESIS_PURE_IMPORTS and not any(
            target == p or target.startswith(p + ".")
            for p in NUTRITION_SYNTHESIS_PURE_IMPORTS[module]
        ):
            errors.append(f"{line}: NUTRITION_SYNTHESIS_PURE_OR_INDEPENDENT_BOUNDARY: {target}")
        if module in NUTRITION_ROOT_PURE_IMPORTS and not any(
            target == p or target.startswith(p + ".")
            for p in NUTRITION_ROOT_PURE_IMPORTS[module]
        ):
            errors.append(f"{line}: NUTRITION_ROOT_PURE_OR_INDEPENDENT_BOUNDARY: {target}")
        if module in SHARED_TARGET_IMPORTS and not any(
            target == p or target.startswith(p + ".") for p in SHARED_TARGET_IMPORTS[module]
        ):
            errors.append(f"{line}: SHARED_TARGET_TASTEFIT_BOUNDARY: {target}")
        if module == "app.modules.planning.shared_target_tastefit_public":
            functions = {
                fn.name for fn in tree.body if isinstance(fn, ast.FunctionDef)
                for n in ast.walk(fn) if isinstance(n, ast.ImportFrom) and n.lineno == line
            }
            capture = target == (
                "app.modules.planning.shared_target_tastefit_capture."
                "capture_shared_member_target_tastefit_sources"
            ) and functions == {"capture_shared_member_target_tastefit_sources"}
            pure = target in {
                "app.modules.planning.shared_target_tastefit.derive_shared_member_target_tastefit",
                "app.modules.planning.shared_target_tastefit.validate_shared_member_target_tastefit",
            } and functions <= {
                "derive_shared_member_target_tastefit", "validate_shared_member_target_tastefit"
            } and bool(functions)
            if not capture and not pure:
                errors.append(f"{line}: SHARED_TARGET_TASTEFIT_PUBLIC: {target}")
        if module in TASTEFIT_TRANSPORT_IMPORTS and not any(
            target == p or target.startswith(p + ".")
            for p in TASTEFIT_TRANSPORT_IMPORTS[module]
        ):
            errors.append(f"{line}: TASTEFIT_IMMUTABLE_TRANSPORT: {target}")
        if module == "app.modules.preferences.tastefit_public":
            pure = {
                "app.domain.feature_identity", "app.modules.preferences.contracts",
                "app.modules.preferences.hierarchical_affinity",
                "app.modules.preferences.hierarchy_resolution",
                "app.modules.preferences.prior_affinity",
                "app.modules.preferences.profile_derivation",
                "app.modules.preferences.tastefit_contracts",
            }
            lazy_capture = (
                line in capture_import_lines
                and target == ("app.modules.preferences.tastefit_sources."
                               "capture_tastefit_member_sources")
            )
            if not lazy_capture and not any(
                target == p or target.startswith(p + ".") for p in pure
            ):
                errors.append(f"{line}: TASTEFIT_MEMBER_PURE_REPLAY: {target}")
        if module == "app.modules.planning.tastefit" and not any(
            target == p or target.startswith(p + ".") for p in TASTEFIT_PURE_IMPORTS
        ):
            errors.append(f"{line}: TASTEFIT_PURE_CORE: {target}")
        if module in {
            "app.modules.planning.tastefit_contracts",
            "app.modules.preferences.tastefit_contracts",
        } and (
            target.split(".")[0] in {
                "sqlalchemy", "psycopg", "socket", "os", "pathlib", "datetime", "time",
                "requests", "httpx", "subprocess", "ortools",
            }
            or target.startswith(("app.persistence", "app.shared.db"))
        ):
            errors.append(f"{line}: TASTEFIT_IMMUTABLE_TRANSPORT: {target}")
        if module == "app.modules.planning.candidate_feature_projection" and not any(
            target == allowed or target.startswith(allowed + ".")
            for allowed in {
                "uuid", "pydantic", "app.domain.contracts", "app.domain.feature_identity",
                "app.domain.resolution", "app.modules.planning.contracts",
                "app.modules.planning.grounding", "app.modules.recipes.contracts",
            }
        ):
            errors.append(f"{line}: CANDIDATE_FEATURE_PURE_CORE: {target}")
        if module == "app.modules.preferences.reference_prior_resolution" and not any(
            target == allowed or target.startswith(allowed + ".")
            for allowed in {
                "app.domain.feature_identity",
                "app.modules.preferences.reference_prior_contracts",
            }
        ):
            errors.append(f"{line}: REFERENCE_PRIOR_PURE_CORE: {target}")
        if module == "app.modules.learning.feature_repeat" and not any(
            target == allowed or target.startswith(allowed + ".")
            for allowed in {
                "json", "datetime", "math", "uuid", "app.domain.contracts",
                "app.domain.feature_identity", "app.modules.learning.contracts",
                "app.modules.recipes.contracts",
            }
        ):
            errors.append(f"{line}: FEATURE_REPEAT_PURE_CORE: {target}")
        if module == "app.modules.preferences.profile_derivation" and not (
            target == "app.modules.preferences.contracts"
            or target.startswith("app.modules.preferences.contracts.")
        ):
            errors.append(f"{line}: EXPLICIT_AFFINITY_PURE_CORE: {target}")
        shortlist_imports = {
            "app.modules.planning.shortlist": {
                "json",
                "dataclasses",
                "hashlib",
                "app.modules.planning.contracts",
            },
            "app.modules.planning.shortlist_capture": {
                "app.modules.planning.contracts",
                "app.modules.planning.grounding_capture",
                "app.modules.planning.shortlist",
            },
        }
        if module in shortlist_imports and not any(
            target == allowed or target.startswith(allowed + ".")
            for allowed in shortlist_imports[module]
        ):
            errors.append(f"{line}: SHORTLIST_NARROW_BOUNDARY: {target}")
        if module in {"app.modules.planning.grounding", "app.modules.planning.grounding_capture"}:
            if target.startswith(
                (
                    "ortools",
                    "benchmark",
                    "app.modules.learning",
                    "app.modules.assistant",
                    "app.modules.planning.optimizer",
                    "app.modules.planning.ranking",
                    "app.modules.planning.shortlist",
                    "app.modules.planning.objectives",
                    "app.modules.planning.utility",
                )
            ):
                errors.append(f"{line}: GROUNDING_NOT_OPTIMIZATION: {target}")
        if (context == "validation" or contract) and (
            target == "ortools" or target.startswith("ortools.")
        ):
            errors.append(f"{line}: VALIDATION_OR_CONTRACT_IMPORTS_SOLVER: {target}")
        if module in {"app.modules.learning.contracts", "app.modules.learning.public"} and (
            target.split(".")[0]
            in {
                "sqlalchemy",
                "psycopg",
                "sqlite3",
                "ortools",
                "socket",
                "subprocess",
                "httpx",
                "requests",
            }
            or target.startswith(("app.persistence", "app.shared.db"))
        ):
            errors.append(f"{line}: EXPOSURE_CORE_INDEPENDENCE: {target}")
        if module in {
            "app.modules.recipes.feature_resolution",
            "app.modules.planning.feature_preview",
        } and not any(target == allowed or target.startswith(allowed + ".") for allowed in {
            "app.domain", "app.modules.recipes.contracts", "app.modules.planning.contracts",
        }):
            errors.append(f"{line}: CULINARY_FEATURE_PURE_CORE: {target}")
        if context == "validation":
            if target.endswith((".resolve_culinary_binding", ".bind_culinary_draft")):
                errors.append(f"{line}: VALIDATION_PRODUCER_ENFORCEMENT: {target}")
            if target.split(".")[0] in {
                "ortools",
                "sqlalchemy",
                "psycopg",
                "sqlite3",
                "benchmark",
                "socket",
                "subprocess",
                "httpx",
                "requests",
                "urllib",
                "os",
                "pathlib",
            } or (target.startswith(("app.persistence", "app.shared.db"))):
                errors.append(f"{line}: VALIDATION_INDEPENDENCE: {target}")
            if target.startswith("app.modules.") and target.split(".")[2] != "validation":
                tail = target.split(".")[3:]
                if (not tail or tail[0] != "contracts") and not nrc_transport:
                    errors.append(f"{line}: VALIDATION_CONTRACTS_ONLY: {target}")
        if neutral and target.startswith(("app.modules", "app.persistence", "app.shared.db")):
            errors.append(f"{line}: NEUTRAL_DOMAIN_IMPORTS_IMPLEMENTATION: {target}")
        if target == "benchmark" or target.startswith("benchmark."):
            errors.append(f"{line}: BACKEND_IMPORTS_SYNTHETIC_BENCHMARK: {target}")
        if context and (target == "importlib" or target.startswith("importlib.")):
            errors.append(f"{line}: DYNAMIC_IMPORT_REQUIRES_REVIEW: {target}")
        if context and target in {"app", "app.modules"}:
            errors.append(f"{line}: INDIRECT_APP_NAMESPACE_IMPORT: {target}")
        if not target.startswith("app.modules."):
            if context and target in {"app.main"}:
                errors.append(f"{line}: DOMAIN_IMPORTS_ENTRYPOINT: {target}")
            return
        destination = target.split(".")[2]
        if shared:
            errors.append(f"{line}: SHARED_IMPORTS_DOMAIN: {target}")
            return
        if context is None:
            return
        if context not in ALLOWED or destination not in ALLOWED:
            errors.append(f"{line}: UNREGISTERED_CONTEXT: {target}")
            return
        tail = target.split(".")[3:]
        if (
            context == "planning"
            and destination == "shopping"
            and (not tail or tail[0] != "contracts")
        ):
            errors.append(f"{line}: PLAN_SHOPPING_CONTRACTS_ONLY: {target}")
            return
        if contract and context in {"shopping", "cooking"} and destination == "planning":
            errors.append(f"{line}: PLAN_CONTRACT_CYCLE: {target}")
            return
        if contract and (not tail or tail[0] != "contracts"):
            errors.append(f"{line}: CONTRACT_IMPORTS_IMPLEMENTATION: {target}")
            return
        if destination == context:
            return
        if destination not in ALLOWED[context]:
            errors.append(f"{line}: FORBIDDEN_DIRECTION: {context} -> {destination}")
            return
        if (
            context in CONTRACT_ONLY_CONTEXTS
            and (not tail or tail[0] != "contracts")
            and not nrc_transport
        ):
            errors.append(f"{line}: FACT_READER_IMPORTS_IMPLEMENTATION: {target}")
            return
        if not tail or tail[0] not in PUBLIC_SURFACES:
            if nrc_transport:
                return
            if any(target == p or target.startswith(p + ".")
                   for p in TASTEFIT_COMPANIONS.get(module, ())):
                return
            errors.append(f"{line}: CROSS_CONTEXT_INTERNAL_IMPORT: {target}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                audit(item.name, node.lineno)
        elif isinstance(node, ast.ImportFrom):
            target = node.module or ""
            if node.level:
                package = module if is_package else module.rpartition(".")[0]
                try:
                    target = importlib.util.resolve_name("." * node.level + target, package)
                except ImportError:
                    errors.append(f"{node.lineno}: INVALID_RELATIVE_IMPORT")
                    continue
            for item in node.names:
                audit(target + "." + item.name if item.name != "*" else target, node.lineno)
                if item.name == "*" and context:
                    errors.append(f"{node.lineno}: WILDCARD_IMPORT_REQUIRES_REVIEW")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if module in POLICY_V2_IMPORTS and node.func.id in {
                "open", "input", "eval", "exec", "__import__"
            }:
                errors.append(f"{node.lineno}: POLICY_V2_NO_DYNAMIC_OR_FILE_IO")
            if module in BASIS_COMPANION_IMPORTS and node.func.id in {
                "open", "input", "eval", "exec", "__import__"
            }:
                errors.append(f"{node.lineno}: MBA_NO_DYNAMIC_OR_FILE_IO")
            if module in NUTRITION_RESOLUTION_IMPORTS and node.func.id in {
                "open", "input", "eval", "exec", "__import__"
            }:
                errors.append(f"{node.lineno}: NRE_NO_DYNAMIC_OR_FILE_IO")
            if module in NUTRITION_ROOT_PURE_IMPORTS and node.func.id in {"open", "input", "print"}:
                errors.append(f"{node.lineno}: NUTRITION_ROOT_PURE_IO")
            if context == "validation" and node.func.id == "open":
                errors.append(f"{node.lineno}: VALIDATION_INDEPENDENCE: file IO")
            if context and node.func.id in {"__import__", "eval", "exec"}:
                errors.append(f"{node.lineno}: DYNAMIC_IMPORT_REQUIRES_REVIEW")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (module in POLICY_V2_IMPORTS
                and module != "app.modules.planning.policy_v2_capture"
                and node.func.attr in {"now", "utcnow", "today", "time", "getenv", "monotonic"}):
                errors.append(f"{node.lineno}: POLICY_V2_NO_CLOCK_OR_ENVIRONMENT")
            if (module in BASIS_COMPANION_IMPORTS
                and module not in {"app.modules.planning.basis_capture",
                                   "app.modules.planning.basis_host"}
                and node.func.attr in {"now", "utcnow", "today", "time", "getenv", "monotonic"}):
                errors.append(f"{node.lineno}: MBA_NO_CLOCK_OR_ENVIRONMENT")
            if (module in NUTRITION_RESOLUTION_IMPORTS
                and module != "app.modules.planning.nutrition_resolution_capture"
                and node.func.attr in {"now", "utcnow", "today", "time", "getenv", "monotonic"}):
                errors.append(f"{node.lineno}: NRE_NO_CLOCK_OR_ENVIRONMENT")
            if module in NUTRITION_ROOT_PURE_IMPORTS and node.func.attr in {
                "now", "utcnow", "today", "time", "getenv",
            }:
                errors.append(f"{node.lineno}: NUTRITION_ROOT_PURE_CLOCK_OR_ENVIRONMENT")
    return sorted(set(errors))


def check_tree(app_root: Path) -> list[str]:
    issues = []
    module_root = app_root / "modules"
    actual = {p.name for p in module_root.iterdir() if p.is_dir() and p.name != "__pycache__"}
    for name in sorted(actual - ALLOWED.keys()):
        issues.append(f"app.modules.{name}: UNREGISTERED_CONTEXT")
    for path in sorted(app_root.rglob("*.py")):
        relative = path.relative_to(app_root.parent).with_suffix("")
        is_package = relative.name == "__init__"
        module = ".".join(relative.parts[:-1] if is_package else relative.parts)
        try:
            errors = check_source(
                path.read_text(encoding="utf-8-sig"), module, is_package=is_package
            )
        except SyntaxError as error:
            errors = [f"SYNTAX_ERROR: {error}"]
        issues.extend(f"{path.relative_to(app_root)}:{error}" for error in errors)
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--app-root", type=Path, default=Path(__file__).resolve().parents[1] / "apps/backend/app"
    )
    args = parser.parse_args()
    failures = check_tree(args.app_root)
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    print(
        f"Import boundaries passed: {len(ALLOWED)} registered contexts, public/contract surfaces, "
        "independent validation/learning, no backend benchmark dependency."
    )


if __name__ == "__main__":
    main()
