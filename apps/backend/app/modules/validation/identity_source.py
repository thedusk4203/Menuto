"""Validation-owned Identity reconstruction, independent of every producer/capture evaluator."""

import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime, timezone
from uuid import UUID

from pydantic import BaseModel

from app.domain.snapshots import Horizon
from app.modules.identity.source_contracts import (
    IdentityBindingCommandV1,
    IdentityCaptureFailureV1,
    IdentityCaptureFrameV1,
    IdentityCommandReceiptV1,
    IdentityEffectiveRequestV1,
    IdentityIssuerCommandV1,
    IdentityMembershipWitnessV1,
    IdentityOperationGrantCommandV1,
    IdentityPrivilegeObjectFactV1,
    IdentityRecordedFactV1,
    IdentityRequestBindingV1,
    IdentityRoleEdgeV1,
    IdentityRoleFactV1,
    IdentityRootCommandV1,
    IdentitySessionFactV1,
    IdentitySourceCheckV1,
    IdentitySourceFrontierV1,
    IdentitySourceSnapshotV1,
)

_MODELS = {
    IdentityBindingCommandV1,
    IdentityCaptureFailureV1,
    IdentityCaptureFrameV1,
    IdentityCommandReceiptV1,
    IdentityEffectiveRequestV1,
    IdentityIssuerCommandV1,
    IdentityMembershipWitnessV1,
    IdentityOperationGrantCommandV1,
    IdentityPrivilegeObjectFactV1,
    IdentityRecordedFactV1,
    IdentityRequestBindingV1,
    IdentityRoleEdgeV1,
    IdentityRoleFactV1,
    IdentityRootCommandV1,
    IdentitySessionFactV1,
    IdentitySourceCheckV1,
    IdentitySourceFrontierV1,
    IdentitySourceSnapshotV1,
    Horizon,
}


LEGACY_ROUTINE_PINS = (
    (
        "menuto_culinary_check",
        "menuto_culinary_check(uuid)",
        "305aa17c9db68cbfa4a41b55c4d6f3954b8003b5c82592821b32909596a2bfa6",
    ),
    (
        "menuto_culinary_child",
        "menuto_culinary_child()",
        "16cbc236a35614551c3e4f1647334ab553c4cfc3b490513fb857db71f6656384",
    ),
    (
        "menuto_culinary_json",
        "menuto_culinary_json(uuid,uuid)",
        "f3542f10e2bb0c62bb1abbb0cf41f19fadcd7b9fbf338f043b05e70539d9fd33",
    ),
    (
        "menuto_culinary_signature",
        "menuto_culinary_signature(uuid,uuid)",
        "e7ff0fe932eb8d99756f1763eff10311d3bd78fb1759981d7c6ff3d1f49cc088",
    ),
    (
        "menuto_feature_append",
        "menuto_feature_append()",
        "330fbdbfe1640a73a1ba48569cb65815eba5253591e1c29d2bafca02270329be",
    ),
    (
        "menuto_feature_canonical",
        "menuto_feature_canonical(jsonb)",
        "07824963dc987bf6fe626ccf7332db80e55fc32b3744c914fe498fbd414dabaf",
    ),
    (
        "menuto_feature_check_review",
        "menuto_feature_check_review(uuid,boolean)",
        "6cb1e51b3dfded7905c22104c9d744f2c0921ffeaf4d0da4de4b0219ec4738b8",
    ),
    (
        "menuto_feature_check_scope",
        "menuto_feature_check_scope(uuid)",
        "e3b35ae6549b8fc95c86586d6786a7374cdce92f97afa7b00d0998262c6b2956",
    ),
    (
        "menuto_feature_child",
        "menuto_feature_child()",
        "e13439b7e0cf6c1e93ab71dea2f3333f09f49378043df8b12400d26490f16a09",
    ),
    (
        "menuto_feature_complete",
        "menuto_feature_complete()",
        "1ccad30e5759d1349c5c9cd011a0fbe94d86e0a650ed5785210f5487bb458674",
    ),
    (
        "menuto_feature_fence",
        "menuto_feature_fence()",
        "3de2a1dd85a30422f7152b99cb92437dcadaee371817c750ece9d367e8ff0811",
    ),
    (
        "menuto_feature_immutable",
        "menuto_feature_immutable()",
        "942ec2551f566c3273b06e6a40fb6364c54741ea6cf3f3e11108cd3e61dbb381",
    ),
    (
        "menuto_feature_key",
        "menuto_feature_key(uuid)",
        "f308915862185af0265cf7e0f9121286bf74dece290b5b1f6bca6a2d381774c2",
    ),
    (
        "menuto_feature_key_hash",
        "menuto_feature_key_hash(uuid)",
        "15ad71538725cdc0da8094eeb841d08824991faf5ea4234be39a4e26e3ad7dfe",
    ),
    (
        "menuto_feature_options",
        "menuto_feature_options(uuid,uuid)",
        "b849211bf0f3fab4fcfeb23fa5ca1417ad14ac0a96fa6c09b945ab927c5a4edf",
    ),
    (
        "menuto_feature_registry",
        "menuto_feature_registry()",
        "35af44ac5aae3b8739ec8ccf26181c9f1e984ba75b9d6a1a57d58ed405b59fec",
    ),
    (
        "menuto_feature_review_command",
        "menuto_feature_review_command(uuid,boolean)",
        "827d76433363655e37371f618fd2381dba99c30ba74efa3b0a6aae1f4990e417",
    ),
    (
        "menuto_inventory_append",
        "menuto_inventory_append()",
        "f40e01f05d088926d59490075b692edab5a9e33b32cab75efaa4d680b9dcac7f",
    ),
    (
        "menuto_inventory_balance_guard",
        "menuto_inventory_balance_guard()",
        "431dc0b07276325426d48356fd94f35aeaf1a649f0f18b8fbcf5a1f435a395fa",
    ),
    (
        "menuto_inventory_begin_lot",
        "menuto_inventory_begin_lot()",
        "3e91e89fcec65224e804a1c5976c580116a20a95006842f684ae728adf38694d",
    ),
    (
        "menuto_inventory_immutable",
        "menuto_inventory_immutable()",
        "39c81723f5cbcc262f2b90d7fb4374dde47fb5d75790d86c212d2fe9a192c5ea",
    ),
    (
        "menuto_inventory_initialize_balance",
        "menuto_inventory_initialize_balance()",
        "12de3de3089368111d36f0323e6126deb1e18ce6698f53fc4fe86020a3bc1f09",
    ),
    (
        "menuto_inventory_require_opening",
        "menuto_inventory_require_opening()",
        "cb9427fe194d8c9d5400e9e9c98e061ac2cc8f284677ee98e816c94ea2b2eb3f",
    ),
    (
        "menuto_plan_actor",
        "menuto_plan_actor(uuid,uuid)",
        "6a636cab5021662579947b3ce7190df056e949b4a5a4c949cb2cbc38009acf11",
    ),
    (
        "menuto_plan_anchor_0009",
        "menuto_plan_anchor_0009(uuid,jsonb)",
        "9d203c3eaa92be7a19a16ab3dedb7ab210e259a308ee818e3a39329719760681",
    ),
    (
        "menuto_plan_begin_proposal",
        "menuto_plan_begin_proposal()",
        "51cee590f15b6beae05dff63e8e09c4d24e2835d130e0b84a7fd52c148e4e0b1",
    ),
    (
        "menuto_plan_begin_workspace",
        "menuto_plan_begin_workspace()",
        "e850592b4f73840d8cad8d4410f626387e9401eeb1034a9dd0a39715dd929b17",
    ),
    (
        "menuto_plan_canonical",
        "menuto_plan_canonical(jsonb)",
        "ce503f177025f564a9b86bd29d9461baab5f0a47f9c23a574ae54a3e965db40e",
    ),
    (
        "menuto_plan_check",
        "menuto_plan_check(uuid)",
        "322aab40a2a2e4f29569aafa2078cc2aeedbe5bdb53778f77524ed13eeb13fb4",
    ),
    (
        "menuto_plan_check_pre_culinary_0010",
        "menuto_plan_check_pre_culinary_0010(uuid)",
        "d417b5fd1ca68e63663d433694a56129c3bf69841ff23f3f223d15432369853f",
    ),
    (
        "menuto_plan_child_insert",
        "menuto_plan_child_insert()",
        "303f1101240ad485ea28735683988f4693f59534dc97ebaccb399c2d13ddedc1",
    ),
    (
        "menuto_plan_contributions_0009",
        "menuto_plan_contributions_0009(uuid)",
        "23024e68e26fc19c9bab044b7116d014a438ad61f67305fd6d6485bb2c16462f",
    ),
    (
        "menuto_plan_cutline_0009",
        "menuto_plan_cutline_0009(uuid,uuid)",
        "c858f10c1b13140548f0b54edf0801e5b2a4a3dc424871a7723781cc9b0c61db",
    ),
    (
        "menuto_plan_delta_0009",
        "menuto_plan_delta_0009(jsonb,jsonb,text)",
        "6e0eb9818663481273578fe0aec319ea9c734cf69cd9db0ec30458ebcf9846f7",
    ),
    (
        "menuto_plan_graph",
        "menuto_plan_graph(uuid)",
        "60e6edc6c2ca5104af71f9d053004516627c4af047df7d4a5a653c4adf1ef097",
    ),
    (
        "menuto_plan_graph_pre_culinary_0010",
        "menuto_plan_graph_pre_culinary_0010(uuid)",
        "f63c157f81ae1e1e81a6aabbb5c84f64ac36f8011e56c84bafd454a2c165903b",
    ),
    (
        "menuto_plan_immutable",
        "menuto_plan_immutable()",
        "2277af049b110be7680675665ec9690227918e1d354ed670349060c33b434dca",
    ),
    (
        "menuto_plan_inventory_frontier",
        "menuto_plan_inventory_frontier(uuid)",
        "c8bb1c95a5bd33422d09c0634dc1321ed555098551882409a8306373fcea7d0b",
    ),
    (
        "menuto_plan_materialization",
        "menuto_plan_materialization()",
        "acdce4b93ff5fafe05b9c06e2e23e391df1a8c9ed564ce2dc4792cac71d77ec3",
    ),
    (
        "menuto_plan_meal_path",
        "menuto_plan_meal_path(uuid,uuid)",
        "35d6f0156aa0a4ef8452ec4e1a8f6ab973b1f1d87fc66e52471f5e707cebf70a",
    ),
    (
        "menuto_plan_no_authority",
        "menuto_plan_no_authority()",
        "150f4256492b01a6c6ec792ec819a201462e06be5769d61ee0cbeab1301fa9b8",
    ),
    (
        "menuto_plan_require_local_0009",
        "menuto_plan_require_local_0009(uuid,uuid,jsonb,uuid)",
        "6bb3793a599a3c9ad36ea9d2355493ec04c096a5d9ef2477029f94cd0f1d64e9",
    ),
    (
        "menuto_plan_reservation_target",
        "menuto_plan_reservation_target(uuid,uuid)",
        "b5539859020d052a269f75873e150c8a0c996862fcb3087def7105de14474d54",
    ),
    (
        "menuto_plan_revision",
        "menuto_plan_revision()",
        "da7c1a39554eed30ed587ed9264231c4f2d52ae37235755ee2417b24dd10e2a6",
    ),
    (
        "menuto_plan_revision_complete",
        "menuto_plan_revision_complete()",
        "f9bbbf53f5efd8b209dbdd0ff2b69ad20ab2cb304cbdaee16ee8de91931b9442",
    ),
    (
        "menuto_plan_revision_reservation",
        "menuto_plan_revision_reservation()",
        "165ff5fcc9a28ae6294da594fb0b6a4b0124938dacb0b45bb87b71c0b9c47451",
    ),
    (
        "menuto_plan_scope_0009",
        "menuto_plan_scope_0009(uuid,uuid)",
        "93b40753f0083cec2cc42e2bdf93e8e34be74373a9b612fed2fbf56d8212111b",
    ),
    (
        "menuto_plan_seal",
        "menuto_plan_seal()",
        "832f6f0ebcc72adc299cb41f525db61b4640751be28cb24709024427b447bea2",
    ),
    (
        "menuto_plan_target_meals_0009",
        "menuto_plan_target_meals_0009(uuid,uuid,jsonb)",
        "a5f4e629b4dc06f6b04382131be984f65ee7380b8e41e138bb05c470aa8356c6",
    ),
    (
        "menuto_plan_workspace_guard",
        "menuto_plan_workspace_guard()",
        "eece47614aee3730bab9e0c1005a33b7bdfee78f05017bdf3762c4e51f568299",
    ),
    (
        "menuto_preference_append",
        "menuto_preference_append()",
        "ddd37ea6b03f7dc4155c1bfd4d3c85f46c78aaab64da1430f3634a07269e47d6",
    ),
    (
        "menuto_preference_canonical",
        "menuto_preference_canonical(jsonb)",
        "5a40fdd5e2a0c95f6e71521fd1b0b294319150c714e81b4ae9ef93eab5b90f4a",
    ),
    (
        "menuto_preference_complete",
        "menuto_preference_complete()",
        "587aac13ece74eb33bd3ca679a6cdacf43714bc2b744dda4b0efad9c3d30ce84",
    ),
    (
        "menuto_preference_frontier_guard",
        "menuto_preference_frontier_guard()",
        "5efcbe34c8c905bd7f4134e9e1ec56fd465e4e8aeb5542ca0fd12977b53f8594",
    ),
    (
        "menuto_preference_immutable",
        "menuto_preference_immutable()",
        "04a0c2e7e244333aa5745ca72e289fb8490e01ee773bf826791ee812a9e0382c",
    ),
    (
        "menuto_preference_stream_guard",
        "menuto_preference_stream_guard()",
        "3348aa4b701afebb6e3d453ae216231e4c1ef9339c161e425c4c5bd4bda55e54",
    ),
    (
        "menuto_preference_term_guard",
        "menuto_preference_term_guard()",
        "1d33cbb7ae2e348855710dc17f25f562a2620a5405f3940f54a3e0c2424ace07",
    ),
    (
        "menuto_recipe_begin_version",
        "menuto_recipe_begin_version()",
        "562c3f143c55e1eb9cd2583e9651c7da56bab64180e594f8c9df8e1fa987a3a2",
    ),
    (
        "menuto_recipe_child_insert",
        "menuto_recipe_child_insert()",
        "937c34907e7e5154f24524697c51643fa790e171a41945f17e8cf128d193f60a",
    ),
    (
        "menuto_recipe_count_substitution_policy",
        "menuto_recipe_count_substitution_policy()",
        "625427a62fad03d970d96c247be01ae5d4c2faad8428e931eb269359288e069e",
    ),
    (
        "menuto_recipe_immutable",
        "menuto_recipe_immutable()",
        "7839e159b206cb36a592d39999c1d18f87193d7cf3f6065a7fb71d4cd64afb1d",
    ),
    (
        "menuto_recipe_seal",
        "menuto_recipe_seal()",
        "f0c1a1549817ee4634b046e373cb0da25ad9224343fba00a79a7d17b271fd63b",
    ),
    (
        "menuto_reject_catalog_fact_mutation",
        "menuto_reject_catalog_fact_mutation()",
        "f9d03b07d4360ac7ba6d2def05031b58e81e6fca5adc29e7e6ae92bfc0b58f7c",
    ),
    (
        "menuto_retail_check_member",
        "menuto_retail_check_member()",
        "d84cdab95fa32704530f38149d2f471a345f115ae4cfed58adfa0e09796233fa",
    ),
    (
        "menuto_retail_check_observation",
        "menuto_retail_check_observation()",
        "42a084f208036f6046443e6ca58b6987e626508125b2a3cba3c5f0a1fb27d301",
    ),
    (
        "menuto_retail_check_option",
        "menuto_retail_check_option()",
        "b999d060df757dfbf0aeb7470fdf72fedc3e0ff4be0b5b416c435d001230343c",
    ),
    (
        "menuto_retail_check_quote",
        "menuto_retail_check_quote()",
        "7012f0640e311bfedca2fe5deea8884ac414a2eaec4a5228376eb80aa239d46a",
    ),
    (
        "menuto_retail_reject_mutation",
        "menuto_retail_reject_mutation()",
        "b40db147f5568f72bf25e6c3850d87e4095afcaeb56bb83b9c221faeca0ccb64",
    ),
)


NATIVE_SSLINFO_PINS = {
    "menuto_prior": {
        "ssl_is_used": "a4b1867a7b3f38f2ebb5cc6d0d0a47b26956171c2b1496d82adbc4ca272fd472",
        "ssl_version": "2365cc58f0a9c4818905b3fb1fa3ab824512ab42f9e6b6768202d344068c4602",
        "ssl_cipher": "3f1b37250401d42100544750ecc2bf4de2920514ccb89876e73657cbd31b05d3",
        ("ssl_client_cert_present"): (
            "453648844d7cb028767b08e15fbc34fe729e088fb3973baba879c4da19d1bd69"
        ),
        "ssl_client_serial": "b24dbd3d1b6cacefcd7b8eaa10417de162847da435a1c18d9f339aab765dcabc",
        "ssl_client_dn": "07a832c055b1b13d996ecd8dc9aac8edbe8530e827c2eb2cb9d41545b15e510c",
        "ssl_issuer_dn": "933c3bc61d6d91e14dd71b9830151701a456fefd68f10e4cacb93cdd050cdde8",
        "ssl_client_dn_field": "08a818a754d9f559ed9985ac8bebf23abf59db4b0f75815435f14eed9c80f9fb",
        "ssl_issuer_field": "5e58c0630b470f50e897be40d090310cf7b7beb4397ab95c9f2e3f62d2ff5f11",
        "ssl_extension_info": "8cad35d0ed1b3ff25b8c12f8127f7a7ad79a03f06143da94a665d5e03ca113b2",
    },
    "public": {
        "ssl_is_used": "8c7763a975055b471d4d74f2fbe7e62fd0ca17e9232b4867e842482413241e8e",
        "ssl_version": "32551d67326da6db5d0e02dc8c9d0781c147de9f9ac428277f333dd45e2f20fe",
        "ssl_cipher": "7c9682b427b75a9191d90ad46a82bde72c75344ad6a263f86a3318ee296816ab",
        ("ssl_client_cert_present"): (
            "8b2e38efc3604fe6bd53341600b6f5ceb6c71b9242be673d94902e76b6e85f35"
        ),
        "ssl_client_serial": "2df2133592e5a46f7a45b4709a4526d4de34af0497be3c827f00392494e895c0",
        "ssl_client_dn": "00143dd70742f20eaf8adcb911d3a6c6aa1a4f8e70d3de5dc7c2bb36cfe7a002",
        "ssl_issuer_dn": "e1b6d8c69120388b0e99a66729dea7110203de08c0ac130ca548a5d040ea48f7",
        "ssl_client_dn_field": "d89638c21de107ad256a57d68ed99bae3ee16f709841082ef005b7015c2bfab4",
        "ssl_issuer_field": "d5ded701ca043d42068f52c1005592744fe3ce0ee10e35ec44d12b2c8f242d5f",
        "ssl_extension_info": "a35809e18bdca93ddc19e751f7998fdf587da76023de889b2ef57436b82f29a3",
    },
}


class _Invalid(ValueError):
    def __init__(self, reason):
        self.reason = reason


class _ReplayWork:
    """Independent local accounting; caller cannot supply or increase this budget."""

    def __init__(self):
        self.left = 500_000

    def take(self, visits):
        self.left -= visits
        if self.left < 0:
            raise _Invalid("INVALID_CLAIM")


def _need(condition, reason="INVALID_AUTHORITY_HISTORY"):
    if not condition:
        raise _Invalid(reason)


def _wire(value, depth=0, remaining=None):
    remaining = [200_000] if remaining is None else remaining
    remaining[0] -= 1
    _need(remaining[0] >= 0, "INVALID_CLAIM")
    kind = type(value)
    if kind in _MODELS:
        _need(set(value.__dict__) == set(kind.model_fields), "INVALID_CLAIM")
        value, kind = value.__dict__, dict
    elif isinstance(value, BaseModel):
        raise _Invalid("NO_SOURCE")
    if kind is UUID:
        return str(value)
    if kind is datetime:
        _need(type(value.tzinfo) is timezone, "INVALID_CLAIM")
        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if kind in {dict, tuple, list}:
        _need(depth <= 8, "INVALID_CLAIM")
        if kind is dict:
            _need(
                all(type(k) is str and len(k.encode("utf-8")) <= 64 for k in value), "INVALID_CLAIM"
            )
            return {k: _wire(v, depth + 1, remaining) for k, v in value.items()}
        return [_wire(v, depth + 1, remaining) for v in value]
    if kind is str:
        _need(
            "\x00" not in value and not any(0xD800 <= ord(ch) <= 0xDFFF for ch in value),
            "INVALID_CLAIM",
        )
        return value
    if kind is int:
        _need(-(1 << 63) < value < (1 << 63), "INVALID_CLAIM")
        return value
    _need(value is None or kind is bool, "INVALID_CLAIM")
    return value


def _bytes(value):
    return json.dumps(
        _wire(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _digest(tag, value):
    return hashlib.sha256(tag.encode("ascii") + b"\x00" + _bytes(value)).hexdigest()


def _parse(model, value, bound):
    if type(value) in {bytes, str}:
        raw = value.encode("utf-8") if type(value) is str else value
        _need(len(raw) <= bound, "INVALID_CLAIM")
        text = raw.decode("utf-8", "strict")
        depth, quoted, escape, digits, nodes = 0, False, False, 0, 0
        for ch in text:
            if quoted:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    quoted = False
                continue
            if ch == '"':
                quoted, digits = True, 0
            elif ch in "[{":
                depth += 1
                nodes += 1
                _need(depth <= 9 and nodes <= 200_000, "INVALID_CLAIM")
            elif ch in "]}":
                depth -= 1
            elif ch in ",:":
                nodes += 1
                _need(nodes <= 200_000, "INVALID_CLAIM")
            elif ch.isdecimal():
                digits += 1
                _need(digits <= 19, "INVALID_CLAIM")
            else:
                digits = 0

        def entries(pairs):
            item = {}
            for key, child in pairs:
                _need(key not in item, "INVALID_CLAIM")
                item[key] = child
            return item

        def reject(_):
            raise _Invalid("INVALID_CLAIM")

        value = json.loads(
            text, object_pairs_hook=entries, parse_float=reject, parse_constant=reject
        )
    raw = _bytes(value)
    _need(len(raw) <= bound, "INVALID_CLAIM")
    return model.model_validate_json(raw)


def _native_catalog(session):
    known = NATIVE_SSLINFO_PINS["public"]
    digests = {d for group in NATIVE_SSLINFO_PINS.values() for d in group.values()}
    _need(
        all(
            x["definition_fingerprint"] not in digests
            or x["kind"] == "FUNCTION"
            and x["schema_name"] in NATIVE_SSLINFO_PINS
            and NATIVE_SSLINFO_PINS[x["schema_name"]].get(x["object_name"])
            == x["definition_fingerprint"]
            for x in session["objects"]
        ),
        "INVALID_AUTHENTICATION",
    )
    rows = [x for x in session["objects"] if x["kind"] == "FUNCTION" and x["object_name"] in known]
    _need(len(rows) == 10 and {x["object_name"] for x in rows} == set(known), "INCOMPLETE_SOURCE")
    namespace = rows[0]["schema_name"]
    _need(
        namespace in NATIVE_SSLINFO_PINS and all(x["schema_name"] == namespace for x in rows),
        "INVALID_AUTHENTICATION",
    )
    owners = {x["object_name"]: x["owner_oid"] for x in session["objects"] if x["kind"] == "SCHEMA"}
    required = (
        "menuto_prior",
        "menuto_hierarchy",
        "menuto_nutrition",
        "menuto_nutrition_synthesis",
    )
    _need(all(n in owners for n in required), "INCOMPLETE_SOURCE")
    schema_rows = [x for x in session["objects"] if x["kind"] == "SCHEMA"]
    _need(len(schema_rows) == len(owners), "INVALID_AUTHENTICATION")
    chosen = next((x for x in schema_rows if x["object_name"] == namespace), None)
    _need(chosen is not None, "INCOMPLETE_SOURCE")
    _need(
        all(
            a[2] != "CREATE" or a[0] in {chosen["owner_oid"], session["database_owner_oid"]}
            for a in chosen["acl"] or ()
        ),
        "INVALID_AUTHENTICATION",
    )
    grantor = session["database_owner_oid"]
    for row in rows:
        expected = [[grantor, grantor, "EXECUTE", False]]
        if namespace == "public":
            expected.insert(0, [0, grantor, "EXECUTE", False])
        if row["object_name"] == "ssl_is_used":
            expected += [[owners[n], grantor, "EXECUTE", False] for n in required]
            expected.append([session["execution_owner_oid"], grantor, "EXECUTE", False])
        _need(
            row["owner_oid"] == grantor
            and row["definition_fingerprint"] == NATIVE_SSLINFO_PINS[namespace][row["object_name"]]
            and row["acl"] == sorted(expected),
            "INVALID_AUTHENTICATION",
        )
    return {x["object_oid"] for x in rows}


def _catalog(session, mode, *, budget):
    budget.take(
        1
        + len(session["roles"])
        + len(session["edges"])
        + len(session["objects"])
        + sum(len(item["acl"] or ()) for item in session["objects"])
    )
    by_oid = {r["role_oid"]: r for r in session["roles"]}
    _need(
        len(by_oid) == len(session["roles"])
        and len({r["role_name"] for r in by_oid.values()}) == len(by_oid)
    )
    actor = by_oid.get(session["login_role_oid"])
    owner = by_oid.get(session["execution_owner_oid"])
    _need(actor is not None and owner is not None, "INVALID_AUTHENTICATION")
    _need(
        actor["can_login"]
        and actor["role_name"] == session["session_user"]
        and session["requested_role"] == "none"
        and session["tls"]
        and session["authentication_method"] == "scram-sha-256"
        and session["system_user"] == "scram-sha-256:" + session["session_user"],
        "INVALID_AUTHENTICATION",
    )
    _need(
        actor["valid_until"] is None or session["observed_at"] < actor["valid_until"],
        "INVALID_AUTHENTICATION",
    )
    dangerous = ("superuser", "create_role", "create_db", "replication", "bypass_rls")
    _need(
        owner["role_name"] == "menuto_identity_source_owner"
        and not owner["can_login"]
        and not any(owner[k] for k in dangerous),
        "INVALID_AUTHENTICATION",
    )
    edges = session["edges"]
    _need(
        all(
            e["role_oid"] in by_oid
            and e["member_oid"] in by_oid
            and e["member_oid"] != owner["role_oid"]
            for e in edges
        ),
        "INVALID_AUTHENTICATION",
    )

    def expand(set_access):
        visit = [actor["role_oid"]]
        done = set()
        while visit:
            budget.take(len(edges))
            child = visit.pop()
            if child in done:
                continue
            done.add(child)
            _need(len(done) <= 64, "INVALID_AUTHENTICATION")
            visit.extend(
                e["role_oid"]
                for e in edges
                if e["member_oid"] == child
                and (e["inherit_option"] or set_access and e["set_option"])
            )
        return done

    _need(len({(e["role_oid"], e["member_oid"], e["grantor_oid"]) for e in edges}) == len(edges))
    inherited = expand(False)
    reachable = expand(True)
    names = {by_oid[i]["role_name"] for i in inherited}
    group_names = {
        "menuto_identity_source_owner",
        "menuto_identity_bootstrap",
        "menuto_identity_issuer",
        "menuto_identity_requester",
    }
    groups = [item for item in session["roles"] if item["role_name"] in group_names]
    _need(
        len(groups) == 4
        and all(
            not any(
                item[key]
                for key in (
                    "can_login",
                    "superuser",
                    "create_role",
                    "create_db",
                    "replication",
                    "bypass_rls",
                )
            )
            for item in groups
        )
        and session["execution_owner_oid"] != session["database_owner_oid"],
        "INVALID_AUTHENTICATION",
    )
    native_oids = _native_catalog(session)
    public_routines = [
        item
        for item in session["objects"]
        if item["kind"] == "FUNCTION"
        and item["schema_name"] == "public"
        and item["object_oid"] not in native_oids
    ]
    pinned = {row[0]: row[2] for row in LEGACY_ROUTINE_PINS}
    _need(
        len(public_routines) == len(pinned)
        and {item["object_name"] for item in public_routines} == set(pinned),
        "INCOMPLETE_SOURCE",
    )
    db_owner = session["database_owner_oid"]
    for item in public_routines:
        _need(
            item["owner_oid"] == db_owner
            and item["definition_fingerprint"] == pinned[item["object_name"]]
            and item["acl"]
            == [[0, db_owner, "EXECUTE", False], [db_owner, db_owner, "EXECUTE", False]],
            "INVALID_AUTHENTICATION",
        )
    _need(
        not any(
            item["kind"] == "FUNCTION"
            and item["schema_name"] == "menuto_identity_source"
            and any(a[0] == 0 for a in item["acl"] or ())
            for item in session["objects"]
        ),
        "INVALID_AUTHENTICATION",
    )
    if mode == "BOOTSTRAP":
        _need(
            (actor["superuser"] or actor["role_oid"] == session["database_owner_oid"])
            and "menuto_identity_bootstrap" in names,
            "INVALID_AUTHENTICATION",
        )
        return
    _need(mode in {"ISSUER", "REQUESTER"}, "INVALID_AUTHENTICATION")
    _need("menuto_identity_" + mode.lower() in names, "INVALID_AUTHENTICATION")
    _need(
        not names
        & {
            "menuto_identity_source_owner",
            "menuto_identity_bootstrap",
            "menuto_identity_requester" if mode == "ISSUER" else "menuto_identity_issuer",
        },
        "INVALID_AUTHENTICATION",
    )
    _need(
        not reachable & {session["execution_owner_oid"], session["database_owner_oid"]}
        and not any(by_oid[i][flag] for i in reachable for flag in dangerous)
        and not any(e["admin_option"] for e in edges if e["member_oid"] in reachable),
        "INVALID_AUTHENTICATION",
    )
    _need(
        not any(by_oid[oid]["role_name"].startswith("pg_") for oid in reachable),
        "INVALID_AUTHENTICATION",
    )
    items = session["objects"]
    _need(len({(x["kind"], x["object_oid"], x["sub_id"]) for x in items}) == len(items))
    role_ids = inherited | {0}
    accessible_schemas = set()
    for item in items:
        if item["kind"] == "SCHEMA" and (
            item["owner_oid"] in inherited
            or any(grant[0] in role_ids and grant[2] == "USAGE" for grant in item["acl"] or ())
        ):
            accessible_schemas.add(item["object_name"])
    entries = (
        {"change_binding", "change_operation_grant"}
        if mode == "ISSUER"
        else {"capture_request_source"}
    )
    for item in items:
        _need(item["owner_oid"] not in reachable, "INVALID_AUTHENTICATION")
        effective = [a for a in item["acl"] or () if a[0] in role_ids]
        kind = item["kind"]
        if kind == "PARAMETER":
            _need(not effective, "INVALID_AUTHENTICATION")
        elif kind in {"DATABASE", "SCHEMA"}:
            _need(not any(a[2] == "CREATE" for a in effective), "INVALID_AUTHENTICATION")
        elif kind in {"TABLE", "COLUMN", "SEQUENCE"}:
            _need(not effective, "INVALID_AUTHENTICATION")
        elif kind == "FUNCTION" and effective:
            legal = (
                item["schema_name"] == "menuto_identity_source"
                and item["object_name"] in entries
                or item["schema_name"] == "public"
                and item["object_name"] in pinned
                or item["object_oid"] in native_oids
            )
            _need(
                legal
                or (
                    item["schema_name"] not in accessible_schemas
                    and all(a[0] == 0 for a in effective)
                ),
                "INVALID_AUTHENTICATION",
            )


def _point(journal, point, known_before, *, budget):
    budget.take(3 * len(journal))
    result = None
    for event in journal:
        if event["recorded_order"] >= known_before:
            continue
        if event["command"]["action"] == "REVOKE":
            if event["recorded_at"] <= point:
                return None
        elif event["effective_start"] <= point < event["effective_end"]:
            _need(result is None)
            result = event
    return result


def _contains(journal, lo, hi, known_before, *, budget):
    budget.take(3 * len(journal))
    segments = []
    for row in journal:
        if row["recorded_order"] >= known_before:
            continue
        if row["command"]["action"] == "REVOKE":
            if row["recorded_at"] <= lo or row["recorded_at"] < hi:
                return False
        else:
            segments.append((row["effective_start"], row["effective_end"]))
    missing_from = lo
    for lower, upper in sorted(segments):
        if lower <= missing_from < upper:
            missing_from = upper
            if missing_from >= hi:
                return True
    return False


def _journal(rows, kind, root_id, last_time, *, budget):
    budget.take(len(rows))
    _need(0 < len(rows) <= 256)
    permanent = None
    previous = None
    last_end = None
    for expected_number, event in enumerate(rows, 1):
        cmd = event["command"]
        identity_field = {
            "ISSUER": "issuer_id",
            "BINDING": "binding_id",
            "OPERATION_GRANT": "grant_id",
        }.get(kind)
        stream = root_id if kind == "ROOT" else cmd.get(identity_field)
        _need(
            event["stream_kind"] == cmd["kind"] == kind
            and event["root_id"] == cmd["root_id"] == root_id
            and event["stream_id"] == rows[0]["stream_id"] == stream
            and event["revision"] == expected_number
        )
        _need(
            cmd["expected_revision"] == expected_number - 1
            and cmd["predecessor_id"] == (previous["fact_id"] if previous else None)
            and event["previous_fact_id"] == cmd["predecessor_id"]
            and event["previous_fact_fingerprint"]
            == (previous["fact_fingerprint"] if previous else None)
        )
        _need(
            event["recorded_at"] <= last_time
            and event["author"]["observed_at"] == event["recorded_at"]
        )
        if previous:
            _need(
                previous["command"]["action"] != "REVOKE"
                and previous["recorded_at"] <= event["recorded_at"]
                and previous["recorded_order"] < event["recorded_order"]
            )
        _need(
            event["command_fingerprint"] == _digest("identity.command.v1", cmd)
            and event["fact_fingerprint"]
            == _digest(
                "identity.fact.v1",
                {key: val for key, val in event.items() if key != "fact_fingerprint"},
            ),
            "FINGERPRINT_MISMATCH",
        )
        stable = {
            key: val
            for key, val in cmd.items()
            if key
            not in {
                "action",
                "effective",
                "idempotency_key",
                "expected_revision",
                "predecessor_id",
                "evidence_id",
                "evidence_version",
                "evidence_preimage",
            }
        }
        action = cmd["action"]
        if permanent is None:
            _need(
                action
                == {
                    "ROOT": "INITIALIZE",
                    "ISSUER": "ENROLL",
                    "BINDING": "ENROLL",
                    "OPERATION_GRANT": "GRANT",
                }[kind]
            )
            permanent = stable
        else:
            _need(stable == permanent and action in {"RENEW", "REVOKE"})
        if action == "REVOKE":
            _need(
                cmd["effective"] is None
                and event["effective_start"] is None
                and event["effective_end"] is None
            )
        else:
            eff = cmd["effective"]
            _need(eff is not None)
            lower = event["recorded_at"] if eff["mode"] == "IMMEDIATE" else eff["start"]
            _need(
                lower is not None
                and (eff["mode"] == "IMMEDIATE" or event["recorded_at"] < lower)
                and event["effective_start"] == lower
                and event["effective_end"] == eff["end"]
                and lower < eff["end"]
                and (last_end is None or last_end <= lower)
            )
            last_end = eff["end"]
        _catalog(
            event["author"], "BOOTSTRAP" if kind in {"ROOT", "ISSUER"} else "ISSUER", budget=budget
        )
        if kind in {"ROOT", "ISSUER"}:
            _need(event["author_issuer_fact_id"] is None)
        if kind == "ROOT":
            _need(event["target_role"] is None and event["membership_at_issue"] is None)
        if kind in {"ISSUER", "BINDING"}:
            target = event["target_role"]
            _need(
                target is not None
                and target["can_login"]
                and target["role_name"] == cmd["role_name"]
                and not any(
                    target[f]
                    for f in ("superuser", "create_role", "create_db", "replication", "bypass_rls")
                )
            )
            if previous:
                _need(
                    target["role_oid"] == rows[0]["target_role"]["role_oid"]
                    and target["role_name"] == rows[0]["target_role"]["role_name"]
                )
        previous = event


def _member(w, request):
    return w is not None and (
        w["user_exists"]
        and w["user_id"] == request["actor_user_id"]
        and w["household_id"] == request["household_id"]
        and w["membership_id"] is not None
        and w["membership_user_id"] == request["actor_user_id"]
        and w["membership_household_id"] == request["household_id"]
        and w["actor_member_id"] is not None
        and w["role"] in {"OWNER", "EDITOR"}
        and w["actor_member_household_id"] == request["household_id"]
        and w["target_member_id"] == request["tracked_member_id"]
        and w["target_member_household_id"] == request["household_id"]
        and w["target_member_exists"] is True
    )


def _verify(value, expected):
    budget = _ReplayWork()
    source = _wire(value)
    request = _wire(expected)
    _need(source["binding"] == request, "SUBJECT_MISMATCH")
    raw = request["request_utf8"].encode("utf-8")
    _need(len(raw) <= 49_152)
    _need(
        request["request_preimage_fingerprint"]
        == hashlib.sha256(b"identity.request-preimage.v1\x00" + raw).hexdigest(),
        "FINGERPRINT_MISMATCH",
    )
    # The raw child may contain invalid axes; only structural context belongs here.
    child = _parse(IdentityRequestBindingV1, expected, 131_072)
    del child

    def unique(items):
        d = {}
        for k, v in items:
            _need(k not in d)
            d[k] = v
        return d

    def nonfinite(_):
        raise _Invalid("INVALID_CLAIM")

    # Opaque finite-axis numbers are preserved in the raw request, never coerced/admitted here.
    opaque = object()
    document = json.loads(
        raw, object_pairs_hook=unique, parse_float=lambda _: opaque, parse_constant=nonfinite
    )
    pending = [(document, 0)]
    steps = 0
    while pending:
        value, level = pending.pop()
        steps += 1
        _need(steps <= 200_000 and level <= 9)
        if type(value) is dict:
            for key, item in value.items():
                _need(type(key) is str and len(key.encode("utf-8")) <= 64)
                _wire(key)
                pending.append((item, level + 1))
        elif type(value) is list:
            pending.extend((item, level + 1) for item in value)
        elif value is not opaque:
            _wire(value)
    context = document.get("context") if type(document) is dict else None
    _need(type(context) is dict and document.get("environment") == "TEST_ONLY", "SUBJECT_MISMATCH")
    for key in (
        "request_id",
        "request_revision",
        "household_id",
        "actor_user_id",
        "tracked_member_id",
    ):
        _need(
            type(context.get(key)) is type(request[key]) and context[key] == request[key],
            "SUBJECT_MISMATCH",
        )
    _need(
        _wire(Horizon.model_validate(context.get("horizon"))) == request["horizon"],
        "SUBJECT_MISMATCH",
    )
    f = source["frame"]
    _need(
        f["transaction_started_at"]
        <= f["started_at"]
        <= f["session_start"]["observed_at"]
        <= f["session_end"]["observed_at"]
        <= f["finished_at"]
    )
    started = datetime.fromisoformat(f["started_at"].replace("Z", "+00:00"))
    finished = datetime.fromisoformat(f["finished_at"].replace("Z", "+00:00"))
    _need((finished - started).total_seconds() <= 15)
    a, b = dict(f["session_start"]), dict(f["session_end"])
    a.pop("observed_at")
    b.pop("observed_at")
    _need(a == b, "INCOMPLETE_SOURCE")
    _need(a["read_only"] and a["isolation"] in {"REPEATABLE_READ", "SERIALIZABLE"})
    _catalog(f["session_start"], "REQUESTER", budget=budget)
    _catalog(f["session_end"], "REQUESTER", budget=budget)
    root, binding = source["root_history"], source["binding_history"]
    _need(root and binding)
    issuer_by_stream, grant_by_stream = defaultdict(list), defaultdict(list)
    for ev in source["issuer_history"]:
        issuer_by_stream[ev["stream_id"]].append(ev)
    for ev in source["grant_history"]:
        grant_by_stream[ev["stream_id"]].append(ev)
    _need(len(issuer_by_stream) <= 16)
    rows = root + source["issuer_history"] + binding + source["grant_history"]
    _need(
        len(rows) == f["total_fact_count"] <= 2048
        and len({x["fact_id"] for x in rows}) == len(rows)
        and len({x["recorded_order"] for x in rows}) == len(rows),
        "INCOMPLETE_SOURCE",
    )
    groups = (
        [("ROOT", root), ("BINDING", binding)]
        + [("ISSUER", x) for x in issuer_by_stream.values()]
        + [("OPERATION_GRANT", x) for x in grant_by_stream.values()]
    )
    _need(len({items[0]["stream_id"] for _, items in groups}) == len(groups))
    for kind, values in groups:
        _journal(values, kind, f["root_id"], f["finished_at"], budget=budget)
    admin = root[0]["author"]
    _need(
        all(
            (
                x["author"]["database_oid"],
                x["author"]["database_name"],
                x["author"]["execution_owner_oid"],
            )
            == (admin["database_oid"], admin["database_name"], admin["execution_owner_oid"])
            for x in rows
        ),
        "SUBJECT_MISMATCH",
    )
    _need(
        (a["database_oid"], a["database_name"], a["execution_owner_oid"])
        == (admin["database_oid"], admin["database_name"], admin["execution_owner_oid"]),
        "SUBJECT_MISMATCH",
    )
    first = binding[0]
    principal = first["target_role"]
    _need(
        first["command"]["user_id"] == request["actor_user_id"]
        and principal["role_oid"] == a["login_role_oid"]
        and principal["role_name"] == a["session_user"],
        "SUBJECT_MISMATCH",
    )
    issuer_id = first["command"]["issuer_id"]
    _need(issuer_id in issuer_by_stream)
    _need(
        request["actor_user_id"]
        not in {
            row["command"]["user_id"] for values in issuer_by_stream.values() for row in values
        },
        "SUBJECT_MISMATCH",
    )

    def authorization(parents, event):
        cut = event["recorded_order"]
        selected = _point(parents, event["recorded_at"], cut, budget=budget)
        _need(selected is not None)
        if event["command"]["action"] != "REVOKE":
            _need(
                _contains(
                    parents, event["effective_start"], event["effective_end"], cut, budget=budget
                )
            )
        return selected

    for values in issuer_by_stream.values():
        for event in values:
            authorization(root, event)
    for event in binding + source["grant_history"]:
        authorization(root, event)
        _need(event["command"]["issuer_id"] == issuer_id)
        author = authorization(issuer_by_stream[issuer_id], event)
        _need(
            author["fact_id"] == event["author_issuer_fact_id"]
            and author["target_role"]["role_oid"] == event["author"]["login_role_oid"]
            and author["target_role"]["role_name"] == event["author"]["session_user"]
        )
        if event["stream_kind"] == "OPERATION_GRANT":
            authorization(binding, event)
            cmd = event["command"]
            _need(
                cmd["binding_id"] == first["stream_id"]
                and cmd["household_id"] == request["household_id"]
                and cmd["tracked_member_id"] == request["tracked_member_id"]
                and _member(event["membership_at_issue"], request),
                "SUBJECT_MISMATCH",
            )
    front = {(x["kind"], x["stream_id"]): x for x in f["frontiers"]}
    _need(
        len(front) == len(f["frontiers"])
        and all(x["root_id"] == f["root_id"] for x in f["frontiers"]),
        "INCOMPLETE_SOURCE",
    )

    def head(kind, key, events):
        state = front.get((kind, key))
        _need(
            state is not None
            and state["revision"] == len(events)
            and state["fact_count"] == len(events)
            and state["head_id"] == (events[-1]["fact_id"] if events else None)
            and state["head_fingerprint"] == (events[-1]["fact_fingerprint"] if events else None),
            "INCOMPLETE_SOURCE",
        )
        return state

    head("ROOT", f["root_id"], root)
    head("BINDING", first["stream_id"], binding)
    all_issuers = sorted(source["issuer_history"], key=lambda row: row["recorded_order"])
    directory = head("ISSUER_DIRECTORY", f["root_id"], all_issuers)
    entries = [
        [key, len(values), values[-1]["fact_id"], values[-1]["fact_fingerprint"], len(values)]
        for key, values in sorted(issuer_by_stream.items())
    ]
    _need(
        directory["directory_entries"] == entries
        and directory["directory_fingerprint"]
        == _digest("identity.source.v1", {"issuer_directory": entries}),
        "INCOMPLETE_SOURCE",
    )
    expected_keys = {
        ("ROOT", f["root_id"]),
        ("ISSUER_DIRECTORY", f["root_id"]),
        ("BINDING", first["stream_id"]),
    }
    absences = []
    for key, events in grant_by_stream.items():
        head("OPERATION_GRANT", key, events)
        expected_keys.add(("OPERATION_GRANT", key))
    if not grant_by_stream:
        head("OPERATION_GRANT", request["tracked_member_id"], [])
        expected_keys.add(("OPERATION_GRANT", request["tracked_member_id"]))
        absences.append(["OPERATION_GRANT", request["tracked_member_id"]])
    if source["membership"] is not None and source["membership"]["membership_id"] is None:
        absences.append(["MEMBERSHIP", request["actor_user_id"]])
    _need(
        set(front) == expected_keys and source["absences"] == sorted(absences), "INCOMPLETE_SOURCE"
    )
    _need(
        all(
            x["kind"] == "ISSUER_DIRECTORY"
            or (x["directory_entries"] == [] and x["directory_fingerprint"] is None)
            for x in f["frontiers"]
        )
    )

    def functions(session):
        return sorted(
            (item["object_oid"], item["object_name"], item["definition_fingerprint"])
            for item in session["objects"]
            if item["kind"] == "FUNCTION"
            and (
                item["schema_name"] in {"menuto_identity_source", "public"}
                or item["object_name"] in NATIVE_SSLINFO_PINS["public"]
            )
        )

    original_functions = functions(admin)
    _need(
        original_functions
        and all(functions(row["author"]) == original_functions for row in rows)
        and functions(f["session_start"]) == original_functions == functions(f["session_end"]),
        "INVALID_AUTHENTICATION",
    )
    point = f["session_end"]["observed_at"]
    outcome_reason = "SOURCE_AVAILABLE"
    for journal, prefix in (
        (root, "ROOT"),
        (issuer_by_stream[issuer_id], "ISSUER"),
        (binding, "BINDING"),
    ):
        if _point(journal, point, 1 << 63, budget=budget) is None:
            outcome_reason = prefix + (
                "_REVOKED"
                if any(
                    ev["command"]["action"] == "REVOKE" and ev["recorded_at"] <= point
                    for ev in journal
                )
                else "_EXPIRED"
            )
            break
    selected = [
        v
        for group in grant_by_stream.values()
        if (v := _point(group, point, 1 << 63, budget=budget)) is not None
    ]
    _need(len(selected) <= 1)
    if outcome_reason == "SOURCE_AVAILABLE":
        if not selected:
            outcome_reason = (
                "GRANT_REVOKED"
                if any(x["command"]["action"] == "REVOKE" for x in source["grant_history"])
                else "GRANT_EXPIRED"
                if grant_by_stream
                else "GRANT_ABSENT"
            )
        elif not _member(source["membership"], request) or any(
            source["membership"][name] != selected[0]["membership_at_issue"][name]
            for name in ("membership_id", "actor_member_id", "role")
        ):
            outcome_reason = "AUTHORIZATION_DENIED"
    if outcome_reason != "SOURCE_AVAILABLE" and source["membership"] is not None:
        _need(
            all(
                source["membership"][key] is None
                for key in (
                    "target_member_id",
                    "target_member_household_id",
                    "target_member_exists",
                )
            )
        )
    outcome = "AVAILABLE_AT_RETAINED_CUT" if outcome_reason == "SOURCE_AVAILABLE" else "UNAVAILABLE"
    _need(source["outcome"] == outcome and source["reason"] == outcome_reason, "INVALID_CLAIM")
    _need(
        source["source_fingerprint"]
        == _digest(
            "identity.source.v1",
            {key: val for key, val in source.items() if key != "source_fingerprint"},
        ),
        "FINGERPRINT_MISMATCH",
    )
    return outcome


def check_identity_source_v1(snapshot_or_failure, expected_binding):
    """A report is an observation, never proof in place of fresh primitive reconstruction."""
    decision, reason, result, source_hash, request_hash = (
        "NOT_CHECKABLE",
        "NO_SOURCE",
        None,
        None,
        None,
    )
    try:
        binding = _parse(IdentityRequestBindingV1, expected_binding, 131_072)
        request_hash = binding.request_preimage_fingerprint
        if type(snapshot_or_failure) is IdentityCaptureFailureV1:
            _parse(IdentityCaptureFailureV1, snapshot_or_failure, 131_072)
        else:
            source = _parse(IdentitySourceSnapshotV1, snapshot_or_failure, 8_388_608)
            source_hash = source.source_fingerprint
            result = _verify(source, binding)
            decision = "CONSISTENT"
            reason = (
                "SOURCE_AVAILABLE" if result == "AVAILABLE_AT_RETAINED_CUT" else "FAITHFUL_NEGATIVE"
            )
    except _Invalid as error:
        decision = "NOT_CHECKABLE" if error.reason == "NO_SOURCE" else "INCONSISTENT"
        reason = error.reason
        result = None
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        decision, reason, result = "INCONSISTENT", "INVALID_CLAIM", None
    report = dict(
        version=1,
        decision=decision,
        reconstructed_outcome=result,
        reason=reason,
        checked_source_fingerprint=source_hash,
        checked_request_fingerprint=request_hash,
        environment="TEST_ONLY",
        transport="UNVERIFIED_TRANSPORT",
        numerical_use="NOT_ADMITTED",
        planner_ready=False,
        activation_ready=False,
    )
    report["check_fingerprint"] = _digest("identity.check.v1", report)
    return IdentitySourceCheckV1.model_validate_json(_bytes(report))
