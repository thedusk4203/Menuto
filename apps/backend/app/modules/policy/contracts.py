"""Immutable coverage definition, not NutritionPolicyEngine synthesis."""

from typing import Literal

from app.domain.canonical import canonical_hash
from app.domain.contracts import Contract, Identifier
from app.domain.units import Provenance


class ValidationCoveragePolicySnapshot(Contract):
    contract_version: Literal["validation-coverage-policy.v1"] = "validation-coverage-policy.v1"
    definition: Literal["FOUNDATION_NO_CLINICAL_POLICY"] = "FOUNDATION_NO_CLINICAL_POLICY"
    policy_version: Identifier
    provenance: Provenance
    unsupported_critical_facts: Literal["REJECT"] = "REJECT"

    @property
    def fingerprint(self):
        return canonical_hash(self)
