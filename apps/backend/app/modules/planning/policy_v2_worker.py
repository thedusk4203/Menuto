"""Fixed spawned pure stages. No source connection, credentials or registry handles."""

from app.domain.feature_identity import canonical_bytes


def execute(stage, body, channel):
    try:
        if stage == "derive":
            from app.modules.nutrition.policy_v2 import derive_policy_v2

            result = derive_policy_v2(body)
        elif stage == "check":
            from app.modules.nutrition.policy_v2_contracts import (
                NutritionPolicyHandoffV2,
                PolicyV2Use,
                parse_policy_v2,
            )
            from app.modules.nutrition.resolution_limits import ingest
            from app.modules.validation.nutrition_policy_v2 import check_policy_handoff_v2

            data = ingest(body, 48 * 1024 * 1024)
            h = parse_policy_v2(data["handoff"], NutritionPolicyHandoffV2, 48 * 1024 * 1024)
            use = parse_policy_v2(data["use"], PolicyV2Use, 64 * 1024)
            result = check_policy_handoff_v2(h, use)
        else:
            raise ValueError("Unknown fixed pure stage")
        output = canonical_bytes(result)
        limit = 8 * 1024 * 1024 if stage == "derive" else 256 * 1024
        if len(output) > limit:
            raise ValueError("RESOURCE_EXCEEDED: worker output")
        channel.send_bytes(output)
    finally:
        channel.close()
