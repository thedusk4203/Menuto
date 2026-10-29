"""TEST_ONLY symbols and values. Nothing in this module is production nutrition content."""

from uuid import uuid4

from app.domain.feature_identity import canonical
from app.modules.nutrition import root_contracts as c


def evidence(label, *, evidence_id=None):
    body = "TEST_ONLY STRUCTURAL FIXTURE; NO CLINICAL MEANING: " + label
    return c.NutritionSourceEvidence(
        evidence_id=evidence_id or "TEST_ONLY_" + uuid4().hex,
        version="TEST_ONLY_v1",
        environment="TEST_ONLY",
        purpose="TEST_ONLY " + label,
        body=body,
        body_fingerprint=c.nutrition_root_hash("nutrition.evidence-body.v1", body),
    )


def interval(start="2026-09-01T00:00:00Z", end="2026-09-02T00:00:00Z"):
    return c.NutritionSourceInterval(start=start, end=end)


def authority_interval():
    return interval("2020-01-01T00:00:00Z", "2100-01-01T00:00:00Z")


def temporal(span=None):
    return c.NutritionTemporalScope(
        kind="DAY",
        period_id="TEST_ONLY_day",
        calendar="TEST_ONLY_calendar",
        timezone="UTC",
        interval=span or interval(),
    )


def amount(n=7, d=1):
    return c.NutritionRootAmount(numerator=n, denominator=d)


def protocol():
    marker = uuid4().hex[:16]

    def req(facts, slot):
        return dict(observations=facts, evidence_slots=("TEST_ONLY_" + slot + "_" + marker,))

    return c.NutritionEligibilityProtocol(
        protocol_id="TEST_ONLY_protocol_" + marker,
        version="TEST_ONLY_v1",
        scope_id="TEST_ONLY_scope_" + marker,
        scope_version="TEST_ONLY_v1",
        environment="TEST_ONLY",
        meaning=evidence("TEST_ONLY synthetic assertion protocol; not a population definition"),
        admitted=req(("BODY_MASS", "HEIGHT"), "admission"),
        excluded=req(("BODY_MASS",), "exclusion"),
        out_of_scope=req(("BODY_MASS",), "out_of_scope"),
    )


def guideline(provider_id, family_id, *, root_kind="RANGE", proto=None, span=None):
    proto = proto or protocol()
    span = span or interval()
    bounds = {
        "RANGE": dict(kind="RANGE", lower=amount(7), upper=amount(13)),
        "MINIMUM": dict(kind="MINIMUM", lower=amount(7)),
        "MAXIMUM": dict(kind="MAXIMUM", upper=amount(13)),
    }
    return c.NutritionGuidelineBody(
        revision_id=uuid4(),
        provider_id=provider_id,
        family_id=family_id,
        guideline_id="TEST_ONLY_guideline",
        guideline_version="TEST_ONLY_v1",
        edition="TEST_ONLY invented edition; no nutritional evidence",
        jurisdiction=None,
        jurisdiction_status="SOURCE_NOT_SPECIFIED",
        environment="TEST_ONLY",
        effective=span,
        protocol=proto,
        evidence_manifest=(evidence("TEST_ONLY symbolic root manifest"),),
        clauses=(
            dict(
                root_key="TEST_ONLY_energy",
                interpretation="GUIDELINE_HARD",
                descriptor=dict(
                    metric="ENERGY",
                    unit="KCAL",
                    scope_id=proto.scope_id,
                    scope_version=proto.scope_version,
                    protocol_fingerprint=c.nutrition_root_hash("nutrition.protocol.v1", proto),
                    temporal=temporal(span),
                ),
                constraint=bounds[root_kind],
            ),
        ),
        mandatory_hard_roots=("TEST_ONLY_energy",),
    )


def reference_identity(provider_id, family_id):
    return c.NutritionStreamIdentity(
        kind="GUIDELINE",
        provider_id=provider_id,
        family_id=family_id,
        household_id=None,
        member_id=None,
        code="FAMILY",
    )


def member_identity(s, kind, code):
    return c.NutritionStreamIdentity(
        kind=kind,
        provider_id=s["provider_id"] if kind == "ASSESSMENT" else None,
        family_id=s["family_id"] if kind == "ASSESSMENT" else None,
        household_id=s["household_id"],
        member_id=s["member_id"],
        code=code,
    )


def root_request(s, *, purpose="ROOT", **updates):
    body = s["guideline"]
    return c.NutritionRootRequest(
        **dict(
            dict(
                subject=dict(household_id=s["household_id"], member_id=s["member_id"]),
                provider_id=s["provider_id"],
                family_id=s["family_id"],
                guideline_revision_id=body.revision_id,
                guideline_body_fingerprint=c.nutrition_root_hash(
                    "nutrition.guideline-body.v1", body
                ),
                protocol_fingerprint=c.nutrition_root_hash("nutrition.protocol.v1", body.protocol),
                scope_id=body.protocol.scope_id,
                scope_version=body.protocol.scope_version,
                temporal=body.clauses[0].descriptor.temporal,
                environment="TEST_ONLY",
                purpose=purpose,
                goal_type="ENERGY_DIRECTION",
            ),
            **updates,
        )
    )


def rehash_sources(value):
    data = canonical(value)
    data.pop("source_fingerprint", None)
    data["provider_enrollments"].sort(key=lambda x: (x["command"]["provider_id"], x["generation"]))
    data["principals"].sort(key=lambda x: x["id"])
    for key in ("authority", "sources"):
        data[key].sort(key=lambda x: (x["stream_key"], x["sequence"]))
    data["streams"].sort(key=lambda x: x["stream_key"])
    data["capture"]["absence_stream_keys"].sort()
    data["source_fingerprint"] = c.nutrition_root_hash("nutrition.sources.v1", data)
    return data


def rebuild_test_journals(value):
    """TEST_ONLY coherent alternative inputs; hashes are not database-origin proof."""
    data = canonical(value)
    manifests = {m["stream_key"]: m for m in data["streams"]}
    for collection, domain, command_domain in (
        ("authority", "nutrition.authority.v1", "nutrition.authority-command.v1"),
        ("sources", "nutrition.record.v1", "nutrition.source-command.v1"),
    ):
        groups = {}
        for record in data[collection]:
            groups.setdefault(record["stream_key"], []).append(record)
        for key, manifest in manifests.items():
            if (manifest["authority_scope"] is not None) != (collection == "authority"):
                continue
            previous = None
            for record in sorted(groups.get(key, ()), key=lambda r: r["sequence"]):
                record["previous_hash"] = previous["fact_hash"] if previous else None
                record["command_hash"] = c.nutrition_root_hash(command_domain, record["command"])
                payload = {k: v for k, v in record.items() if k != "fact_hash"}
                record["fact_hash"] = c.nutrition_root_hash(domain, payload)
                previous = record
            manifest.update(
                revision=len(groups.get(key, ())),
                head_id=previous["id"] if previous else None,
                head_hash=previous["fact_hash"] if previous else None,
            )
    data["capture"]["absence_stream_keys"] = sorted(
        m["stream_key"] for m in manifests.values() if not m["revision"]
    )
    data["capture"]["row_count"] = sum(
        len(data[k])
        for k in ("provider_enrollments", "principals", "authority", "sources", "streams")
    )
    return rehash_sources(data)


def alternate_test_constraint(source, constraint):
    data = canonical(source)
    draft = next(r for r in data["sources"] if r["command"]["body"]["kind"] == "DRAFT")
    draft["command"]["body"]["guideline"]["clauses"][0]["constraint"] = canonical(constraint)
    fp = c.nutrition_root_hash("nutrition.guideline-body.v1", draft["command"]["body"]["guideline"])
    for r in data["sources"]:
        b = r["command"]["body"]
        if b["kind"] in {"REVIEW", "PUBLICATION"}:
            b["body_fingerprint"] = fp
        if b["kind"] == "ASSESSMENT":
            b["guideline_body_fingerprint"] = fp
    data["request"]["guideline_body_fingerprint"] = fp
    return rebuild_test_journals(data)
