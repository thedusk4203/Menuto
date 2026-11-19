"""Identity-owned principal enrollment. Empty TEST_ONLY structural installation."""

# Frozen migration SQL: no application imports or mutable runtime DDL.
# ruff: noqa: E501
import json

from alembic import op
from sqlalchemy import text

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

ROLES = (
    "menuto_identity_source_owner",
    "menuto_identity_bootstrap",
    "menuto_identity_issuer",
    "menuto_identity_requester",
)
TABLES = (
    "roots",
    "issuers",
    "principal_bindings",
    "operation_grants",
    "frontiers",
    "command_receipts",
)
ENTRIES = {
    "bootstrap_root": "menuto_identity_bootstrap",
    "change_issuer": "menuto_identity_bootstrap",
    "change_binding": "menuto_identity_issuer",
    "change_operation_grant": "menuto_identity_issuer",
    "capture_request_source": "menuto_identity_requester",
}

LEGACY_PINS = {
    "menuto_culinary_check": {
        "signature": "menuto_culinary_check(uuid)",
        "fingerprint": "305aa17c9db68cbfa4a41b55c4d6f3954b8003b5c82592821b32909596a2bfa6",
    },
    "menuto_culinary_child": {
        "signature": "menuto_culinary_child()",
        "fingerprint": "16cbc236a35614551c3e4f1647334ab553c4cfc3b490513fb857db71f6656384",
    },
    "menuto_culinary_json": {
        "signature": "menuto_culinary_json(uuid,uuid)",
        "fingerprint": "f3542f10e2bb0c62bb1abbb0cf41f19fadcd7b9fbf338f043b05e70539d9fd33",
    },
    "menuto_culinary_signature": {
        "signature": "menuto_culinary_signature(uuid,uuid)",
        "fingerprint": "e7ff0fe932eb8d99756f1763eff10311d3bd78fb1759981d7c6ff3d1f49cc088",
    },
    "menuto_feature_append": {
        "signature": "menuto_feature_append()",
        "fingerprint": "330fbdbfe1640a73a1ba48569cb65815eba5253591e1c29d2bafca02270329be",
    },
    "menuto_feature_canonical": {
        "signature": "menuto_feature_canonical(jsonb)",
        "fingerprint": "07824963dc987bf6fe626ccf7332db80e55fc32b3744c914fe498fbd414dabaf",
    },
    "menuto_feature_check_review": {
        "signature": "menuto_feature_check_review(uuid,boolean)",
        "fingerprint": "6cb1e51b3dfded7905c22104c9d744f2c0921ffeaf4d0da4de4b0219ec4738b8",
    },
    "menuto_feature_check_scope": {
        "signature": "menuto_feature_check_scope(uuid)",
        "fingerprint": "e3b35ae6549b8fc95c86586d6786a7374cdce92f97afa7b00d0998262c6b2956",
    },
    "menuto_feature_child": {
        "signature": "menuto_feature_child()",
        "fingerprint": "e13439b7e0cf6c1e93ab71dea2f3333f09f49378043df8b12400d26490f16a09",
    },
    "menuto_feature_complete": {
        "signature": "menuto_feature_complete()",
        "fingerprint": "1ccad30e5759d1349c5c9cd011a0fbe94d86e0a650ed5785210f5487bb458674",
    },
    "menuto_feature_fence": {
        "signature": "menuto_feature_fence()",
        "fingerprint": "3de2a1dd85a30422f7152b99cb92437dcadaee371817c750ece9d367e8ff0811",
    },
    "menuto_feature_immutable": {
        "signature": "menuto_feature_immutable()",
        "fingerprint": "942ec2551f566c3273b06e6a40fb6364c54741ea6cf3f3e11108cd3e61dbb381",
    },
    "menuto_feature_key": {
        "signature": "menuto_feature_key(uuid)",
        "fingerprint": "f308915862185af0265cf7e0f9121286bf74dece290b5b1f6bca6a2d381774c2",
    },
    "menuto_feature_key_hash": {
        "signature": "menuto_feature_key_hash(uuid)",
        "fingerprint": "15ad71538725cdc0da8094eeb841d08824991faf5ea4234be39a4e26e3ad7dfe",
    },
    "menuto_feature_options": {
        "signature": "menuto_feature_options(uuid,uuid)",
        "fingerprint": "b849211bf0f3fab4fcfeb23fa5ca1417ad14ac0a96fa6c09b945ab927c5a4edf",
    },
    "menuto_feature_registry": {
        "signature": "menuto_feature_registry()",
        "fingerprint": "35af44ac5aae3b8739ec8ccf26181c9f1e984ba75b9d6a1a57d58ed405b59fec",
    },
    "menuto_feature_review_command": {
        "signature": "menuto_feature_review_command(uuid,boolean)",
        "fingerprint": "827d76433363655e37371f618fd2381dba99c30ba74efa3b0a6aae1f4990e417",
    },
    "menuto_inventory_append": {
        "signature": "menuto_inventory_append()",
        "fingerprint": "f40e01f05d088926d59490075b692edab5a9e33b32cab75efaa4d680b9dcac7f",
    },
    "menuto_inventory_balance_guard": {
        "signature": "menuto_inventory_balance_guard()",
        "fingerprint": "431dc0b07276325426d48356fd94f35aeaf1a649f0f18b8fbcf5a1f435a395fa",
    },
    "menuto_inventory_begin_lot": {
        "signature": "menuto_inventory_begin_lot()",
        "fingerprint": "3e91e89fcec65224e804a1c5976c580116a20a95006842f684ae728adf38694d",
    },
    "menuto_inventory_immutable": {
        "signature": "menuto_inventory_immutable()",
        "fingerprint": "39c81723f5cbcc262f2b90d7fb4374dde47fb5d75790d86c212d2fe9a192c5ea",
    },
    "menuto_inventory_initialize_balance": {
        "signature": "menuto_inventory_initialize_balance()",
        "fingerprint": "12de3de3089368111d36f0323e6126deb1e18ce6698f53fc4fe86020a3bc1f09",
    },
    "menuto_inventory_require_opening": {
        "signature": "menuto_inventory_require_opening()",
        "fingerprint": "cb9427fe194d8c9d5400e9e9c98e061ac2cc8f284677ee98e816c94ea2b2eb3f",
    },
    "menuto_plan_actor": {
        "signature": "menuto_plan_actor(uuid,uuid)",
        "fingerprint": "6a636cab5021662579947b3ce7190df056e949b4a5a4c949cb2cbc38009acf11",
    },
    "menuto_plan_anchor_0009": {
        "signature": "menuto_plan_anchor_0009(uuid,jsonb)",
        "fingerprint": "9d203c3eaa92be7a19a16ab3dedb7ab210e259a308ee818e3a39329719760681",
    },
    "menuto_plan_begin_proposal": {
        "signature": "menuto_plan_begin_proposal()",
        "fingerprint": "51cee590f15b6beae05dff63e8e09c4d24e2835d130e0b84a7fd52c148e4e0b1",
    },
    "menuto_plan_begin_workspace": {
        "signature": "menuto_plan_begin_workspace()",
        "fingerprint": "e850592b4f73840d8cad8d4410f626387e9401eeb1034a9dd0a39715dd929b17",
    },
    "menuto_plan_canonical": {
        "signature": "menuto_plan_canonical(jsonb)",
        "fingerprint": "ce503f177025f564a9b86bd29d9461baab5f0a47f9c23a574ae54a3e965db40e",
    },
    "menuto_plan_check": {
        "signature": "menuto_plan_check(uuid)",
        "fingerprint": "322aab40a2a2e4f29569aafa2078cc2aeedbe5bdb53778f77524ed13eeb13fb4",
    },
    "menuto_plan_check_pre_culinary_0010": {
        "signature": "menuto_plan_check_pre_culinary_0010(uuid)",
        "fingerprint": "d417b5fd1ca68e63663d433694a56129c3bf69841ff23f3f223d15432369853f",
    },
    "menuto_plan_child_insert": {
        "signature": "menuto_plan_child_insert()",
        "fingerprint": "303f1101240ad485ea28735683988f4693f59534dc97ebaccb399c2d13ddedc1",
    },
    "menuto_plan_contributions_0009": {
        "signature": "menuto_plan_contributions_0009(uuid)",
        "fingerprint": "23024e68e26fc19c9bab044b7116d014a438ad61f67305fd6d6485bb2c16462f",
    },
    "menuto_plan_cutline_0009": {
        "signature": "menuto_plan_cutline_0009(uuid,uuid)",
        "fingerprint": "c858f10c1b13140548f0b54edf0801e5b2a4a3dc424871a7723781cc9b0c61db",
    },
    "menuto_plan_delta_0009": {
        "signature": "menuto_plan_delta_0009(jsonb,jsonb,text)",
        "fingerprint": "6e0eb9818663481273578fe0aec319ea9c734cf69cd9db0ec30458ebcf9846f7",
    },
    "menuto_plan_graph": {
        "signature": "menuto_plan_graph(uuid)",
        "fingerprint": "60e6edc6c2ca5104af71f9d053004516627c4af047df7d4a5a653c4adf1ef097",
    },
    "menuto_plan_graph_pre_culinary_0010": {
        "signature": "menuto_plan_graph_pre_culinary_0010(uuid)",
        "fingerprint": "f63c157f81ae1e1e81a6aabbb5c84f64ac36f8011e56c84bafd454a2c165903b",
    },
    "menuto_plan_immutable": {
        "signature": "menuto_plan_immutable()",
        "fingerprint": "2277af049b110be7680675665ec9690227918e1d354ed670349060c33b434dca",
    },
    "menuto_plan_inventory_frontier": {
        "signature": "menuto_plan_inventory_frontier(uuid)",
        "fingerprint": "c8bb1c95a5bd33422d09c0634dc1321ed555098551882409a8306373fcea7d0b",
    },
    "menuto_plan_materialization": {
        "signature": "menuto_plan_materialization()",
        "fingerprint": "acdce4b93ff5fafe05b9c06e2e23e391df1a8c9ed564ce2dc4792cac71d77ec3",
    },
    "menuto_plan_meal_path": {
        "signature": "menuto_plan_meal_path(uuid,uuid)",
        "fingerprint": "35d6f0156aa0a4ef8452ec4e1a8f6ab973b1f1d87fc66e52471f5e707cebf70a",
    },
    "menuto_plan_no_authority": {
        "signature": "menuto_plan_no_authority()",
        "fingerprint": "150f4256492b01a6c6ec792ec819a201462e06be5769d61ee0cbeab1301fa9b8",
    },
    "menuto_plan_require_local_0009": {
        "signature": "menuto_plan_require_local_0009(uuid,uuid,jsonb,uuid)",
        "fingerprint": "6bb3793a599a3c9ad36ea9d2355493ec04c096a5d9ef2477029f94cd0f1d64e9",
    },
    "menuto_plan_reservation_target": {
        "signature": "menuto_plan_reservation_target(uuid,uuid)",
        "fingerprint": "b5539859020d052a269f75873e150c8a0c996862fcb3087def7105de14474d54",
    },
    "menuto_plan_revision": {
        "signature": "menuto_plan_revision()",
        "fingerprint": "da7c1a39554eed30ed587ed9264231c4f2d52ae37235755ee2417b24dd10e2a6",
    },
    "menuto_plan_revision_complete": {
        "signature": "menuto_plan_revision_complete()",
        "fingerprint": "f9bbbf53f5efd8b209dbdd0ff2b69ad20ab2cb304cbdaee16ee8de91931b9442",
    },
    "menuto_plan_revision_reservation": {
        "signature": "menuto_plan_revision_reservation()",
        "fingerprint": "165ff5fcc9a28ae6294da594fb0b6a4b0124938dacb0b45bb87b71c0b9c47451",
    },
    "menuto_plan_scope_0009": {
        "signature": "menuto_plan_scope_0009(uuid,uuid)",
        "fingerprint": "93b40753f0083cec2cc42e2bdf93e8e34be74373a9b612fed2fbf56d8212111b",
    },
    "menuto_plan_seal": {
        "signature": "menuto_plan_seal()",
        "fingerprint": "832f6f0ebcc72adc299cb41f525db61b4640751be28cb24709024427b447bea2",
    },
    "menuto_plan_target_meals_0009": {
        "signature": "menuto_plan_target_meals_0009(uuid,uuid,jsonb)",
        "fingerprint": "a5f4e629b4dc06f6b04382131be984f65ee7380b8e41e138bb05c470aa8356c6",
    },
    "menuto_plan_workspace_guard": {
        "signature": "menuto_plan_workspace_guard()",
        "fingerprint": "eece47614aee3730bab9e0c1005a33b7bdfee78f05017bdf3762c4e51f568299",
    },
    "menuto_preference_append": {
        "signature": "menuto_preference_append()",
        "fingerprint": "ddd37ea6b03f7dc4155c1bfd4d3c85f46c78aaab64da1430f3634a07269e47d6",
    },
    "menuto_preference_canonical": {
        "signature": "menuto_preference_canonical(jsonb)",
        "fingerprint": "5a40fdd5e2a0c95f6e71521fd1b0b294319150c714e81b4ae9ef93eab5b90f4a",
    },
    "menuto_preference_complete": {
        "signature": "menuto_preference_complete()",
        "fingerprint": "587aac13ece74eb33bd3ca679a6cdacf43714bc2b744dda4b0efad9c3d30ce84",
    },
    "menuto_preference_frontier_guard": {
        "signature": "menuto_preference_frontier_guard()",
        "fingerprint": "5efcbe34c8c905bd7f4134e9e1ec56fd465e4e8aeb5542ca0fd12977b53f8594",
    },
    "menuto_preference_immutable": {
        "signature": "menuto_preference_immutable()",
        "fingerprint": "04a0c2e7e244333aa5745ca72e289fb8490e01ee773bf826791ee812a9e0382c",
    },
    "menuto_preference_stream_guard": {
        "signature": "menuto_preference_stream_guard()",
        "fingerprint": "3348aa4b701afebb6e3d453ae216231e4c1ef9339c161e425c4c5bd4bda55e54",
    },
    "menuto_preference_term_guard": {
        "signature": "menuto_preference_term_guard()",
        "fingerprint": "1d33cbb7ae2e348855710dc17f25f562a2620a5405f3940f54a3e0c2424ace07",
    },
    "menuto_recipe_begin_version": {
        "signature": "menuto_recipe_begin_version()",
        "fingerprint": "562c3f143c55e1eb9cd2583e9651c7da56bab64180e594f8c9df8e1fa987a3a2",
    },
    "menuto_recipe_child_insert": {
        "signature": "menuto_recipe_child_insert()",
        "fingerprint": "937c34907e7e5154f24524697c51643fa790e171a41945f17e8cf128d193f60a",
    },
    "menuto_recipe_count_substitution_policy": {
        "signature": "menuto_recipe_count_substitution_policy()",
        "fingerprint": "625427a62fad03d970d96c247be01ae5d4c2faad8428e931eb269359288e069e",
    },
    "menuto_recipe_immutable": {
        "signature": "menuto_recipe_immutable()",
        "fingerprint": "7839e159b206cb36a592d39999c1d18f87193d7cf3f6065a7fb71d4cd64afb1d",
    },
    "menuto_recipe_seal": {
        "signature": "menuto_recipe_seal()",
        "fingerprint": "f0c1a1549817ee4634b046e373cb0da25ad9224343fba00a79a7d17b271fd63b",
    },
    "menuto_reject_catalog_fact_mutation": {
        "signature": "menuto_reject_catalog_fact_mutation()",
        "fingerprint": "f9d03b07d4360ac7ba6d2def05031b58e81e6fca5adc29e7e6ae92bfc0b58f7c",
    },
    "menuto_retail_check_member": {
        "signature": "menuto_retail_check_member()",
        "fingerprint": "d84cdab95fa32704530f38149d2f471a345f115ae4cfed58adfa0e09796233fa",
    },
    "menuto_retail_check_observation": {
        "signature": "menuto_retail_check_observation()",
        "fingerprint": "42a084f208036f6046443e6ca58b6987e626508125b2a3cba3c5f0a1fb27d301",
    },
    "menuto_retail_check_option": {
        "signature": "menuto_retail_check_option()",
        "fingerprint": "b999d060df757dfbf0aeb7470fdf72fedc3e0ff4be0b5b416c435d001230343c",
    },
    "menuto_retail_check_quote": {
        "signature": "menuto_retail_check_quote()",
        "fingerprint": "7012f0640e311bfedca2fe5deea8884ac414a2eaec4a5228376eb80aa239d46a",
    },
    "menuto_retail_reject_mutation": {
        "signature": "menuto_retail_reject_mutation()",
        "fingerprint": "b40db147f5568f72bf25e6c3850d87e4095afcaeb56bb83b9c221faeca0ccb64",
    },
}

TABLE_SQL = r"""
CREATE SEQUENCE menuto_identity_source.recorded_order START WITH 1;

CREATE TABLE menuto_identity_source.roots (
	id UUID NOT NULL, 
	root_id UUID NOT NULL, 
	stream_id UUID NOT NULL, 
	revision BIGINT NOT NULL, 
	recorded_order BIGINT NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	previous_id UUID, 
	previous_fingerprint VARCHAR(64), 
	action TEXT NOT NULL, 
	effective_start TIMESTAMP WITH TIME ZONE, 
	effective_end TIMESTAMP WITH TIME ZONE, 
	actor_database_oid BIGINT NOT NULL, 
	actor_role_oid BIGINT NOT NULL, 
	actor_database_name VARCHAR(63) NOT NULL, 
	actor_role_name VARCHAR(63) NOT NULL, 
	author_session JSONB NOT NULL, 
	command_body JSONB NOT NULL, 
	command_fingerprint VARCHAR(64) NOT NULL, 
	fact_fingerprint VARCHAR(64) NOT NULL, 
	idempotency_key UUID NOT NULL, 
	environment TEXT NOT NULL, 
	database_oid BIGINT NOT NULL, 
	database_name VARCHAR(63) NOT NULL, 
	deployment_context_id VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT roots_identity CHECK (stream_id=root_id AND database_oid BETWEEN 1 AND 4294967295), 
	CONSTRAINT roots_id_root_stream UNIQUE (id, root_id, stream_id), 
	CONSTRAINT roots_id_root UNIQUE (id, root_id), 
	CONSTRAINT roots_revision UNIQUE (root_id, stream_id, revision), 
	CONSTRAINT roots_order UNIQUE (recorded_order), 
	CONSTRAINT roots_predecessor FOREIGN KEY(previous_id, root_id, stream_id) REFERENCES menuto_identity_source.roots (id, root_id, stream_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT roots_positive CHECK (revision>0 AND recorded_order>0), 
	CONSTRAINT roots_previous CHECK (((revision=1 AND previous_id IS NULL AND previous_fingerprint IS NULL) OR (revision>1 AND previous_id IS NOT NULL AND previous_fingerprint ~ '^[a-f0-9]{64}$'))), 
	CONSTRAINT roots_effective CHECK (isfinite(recorded_at) AND ((action='REVOKE' AND effective_start IS NULL AND effective_end IS NULL) OR (action<>'REVOKE' AND effective_start IS NOT NULL AND effective_end IS NOT NULL AND isfinite(effective_start) AND isfinite(effective_end) AND effective_start<effective_end))), 
	CONSTRAINT roots_action CHECK (action IN ('INITIALIZE','RENEW','REVOKE')), 
	CONSTRAINT roots_oids CHECK (actor_database_oid BETWEEN 1 AND 4294967295 AND actor_role_oid BETWEEN 1 AND 4294967295), 
	CONSTRAINT roots_names CHECK (octet_length(actor_database_name) BETWEEN 1 AND 63 AND octet_length(actor_role_name) BETWEEN 1 AND 63), 
	CONSTRAINT roots_fingerprints CHECK (command_fingerprint ~ '^[a-f0-9]{64}$' AND fact_fingerprint ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT roots_typed CHECK (environment='TEST_ONLY' AND jsonb_typeof(author_session)='object' AND jsonb_typeof(command_body)='object' AND command_body->>'version'='1' AND command_body->>'kind'='ROOT' AND command_body->>'action'=action AND command_body->>'environment'='TEST_ONLY' AND (command_body->>'root_id')::uuid=root_id AND (command_body->>'idempotency_key')::uuid=idempotency_key)
)

;
CREATE INDEX roots_latest ON menuto_identity_source.roots (root_id, stream_id, revision DESC);
CREATE UNIQUE INDEX roots_one_initializer ON menuto_identity_source.roots (action) WHERE action = 'INITIALIZE';
CREATE INDEX roots_root_order ON menuto_identity_source.roots (root_id, recorded_order);

CREATE TABLE menuto_identity_source.frontiers (
	root_id UUID NOT NULL, 
	kind TEXT NOT NULL, 
	stream_id UUID NOT NULL, 
	root_initial_fact_id UUID NOT NULL, 
	revision BIGINT NOT NULL, 
	fact_count BIGINT NOT NULL, 
	head_id UUID, 
	head_fingerprint VARCHAR(64), 
	directory_entries JSONB NOT NULL, 
	directory_fingerprint VARCHAR(64), 
	PRIMARY KEY (root_id, kind, stream_id), 
	CONSTRAINT frontiers_root_initializer FOREIGN KEY(root_initial_fact_id, root_id) REFERENCES menuto_identity_source.roots (id, root_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT frontiers_kind CHECK (kind IN ('ROOT','ISSUER_DIRECTORY','BINDING','OPERATION_GRANT')), 
	CONSTRAINT frontiers_shape CHECK (revision>=0 AND fact_count>=0 AND ((revision=0 AND fact_count=0 AND head_id IS NULL AND head_fingerprint IS NULL) OR (revision>0 AND fact_count>0 AND head_id IS NOT NULL AND head_fingerprint ~ '^[a-f0-9]{64}$'))), 
	CONSTRAINT frontiers_directory CHECK ((kind='ISSUER_DIRECTORY' AND directory_fingerprint ~ '^[a-f0-9]{64}$') OR (kind<>'ISSUER_DIRECTORY' AND directory_entries='[]'::jsonb AND directory_fingerprint IS NULL))
)

;

CREATE TABLE menuto_identity_source.issuers (
	id UUID NOT NULL, 
	root_id UUID NOT NULL, 
	stream_id UUID NOT NULL, 
	revision BIGINT NOT NULL, 
	recorded_order BIGINT NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	previous_id UUID, 
	previous_fingerprint VARCHAR(64), 
	action TEXT NOT NULL, 
	effective_start TIMESTAMP WITH TIME ZONE, 
	effective_end TIMESTAMP WITH TIME ZONE, 
	actor_database_oid BIGINT NOT NULL, 
	actor_role_oid BIGINT NOT NULL, 
	actor_database_name VARCHAR(63) NOT NULL, 
	actor_role_name VARCHAR(63) NOT NULL, 
	author_session JSONB NOT NULL, 
	command_body JSONB NOT NULL, 
	command_fingerprint VARCHAR(64) NOT NULL, 
	fact_fingerprint VARCHAR(64) NOT NULL, 
	idempotency_key UUID NOT NULL, 
	environment TEXT NOT NULL, 
	root_initial_fact_id UUID NOT NULL, 
	issuer_user_id UUID NOT NULL, 
	issuer_role_oid BIGINT NOT NULL, 
	issuer_role_name VARCHAR(63) NOT NULL, 
	target_role JSONB NOT NULL, 
	capability TEXT NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT issuers_root_initializer FOREIGN KEY(root_initial_fact_id, root_id) REFERENCES menuto_identity_source.roots (id, root_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT issuers_capability CHECK (capability='BINDINGS_AND_SCOPE_GRANTS' AND issuer_role_oid BETWEEN 1 AND 4294967295), 
	CONSTRAINT issuers_id_root_stream UNIQUE (id, root_id, stream_id), 
	CONSTRAINT issuers_id_root UNIQUE (id, root_id), 
	CONSTRAINT issuers_revision UNIQUE (root_id, stream_id, revision), 
	CONSTRAINT issuers_order UNIQUE (recorded_order), 
	CONSTRAINT issuers_predecessor FOREIGN KEY(previous_id, root_id, stream_id) REFERENCES menuto_identity_source.issuers (id, root_id, stream_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT issuers_positive CHECK (revision>0 AND recorded_order>0), 
	CONSTRAINT issuers_previous CHECK (((revision=1 AND previous_id IS NULL AND previous_fingerprint IS NULL) OR (revision>1 AND previous_id IS NOT NULL AND previous_fingerprint ~ '^[a-f0-9]{64}$'))), 
	CONSTRAINT issuers_effective CHECK (isfinite(recorded_at) AND ((action='REVOKE' AND effective_start IS NULL AND effective_end IS NULL) OR (action<>'REVOKE' AND effective_start IS NOT NULL AND effective_end IS NOT NULL AND isfinite(effective_start) AND isfinite(effective_end) AND effective_start<effective_end))), 
	CONSTRAINT issuers_action CHECK (action IN ('ENROLL','RENEW','REVOKE')), 
	CONSTRAINT issuers_oids CHECK (actor_database_oid BETWEEN 1 AND 4294967295 AND actor_role_oid BETWEEN 1 AND 4294967295), 
	CONSTRAINT issuers_names CHECK (octet_length(actor_database_name) BETWEEN 1 AND 63 AND octet_length(actor_role_name) BETWEEN 1 AND 63), 
	CONSTRAINT issuers_fingerprints CHECK (command_fingerprint ~ '^[a-f0-9]{64}$' AND fact_fingerprint ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT issuers_typed CHECK (environment='TEST_ONLY' AND jsonb_typeof(author_session)='object' AND jsonb_typeof(command_body)='object' AND command_body->>'version'='1' AND command_body->>'kind'='ISSUER' AND command_body->>'action'=action AND command_body->>'environment'='TEST_ONLY' AND (command_body->>'root_id')::uuid=root_id AND (command_body->>'idempotency_key')::uuid=idempotency_key)
)

;
CREATE INDEX issuers_latest ON menuto_identity_source.issuers (root_id, stream_id, revision DESC);
CREATE INDEX issuers_root_order ON menuto_identity_source.issuers (root_id, recorded_order);
CREATE INDEX issuers_user ON menuto_identity_source.issuers (root_id, issuer_user_id);

CREATE TABLE menuto_identity_source.principal_bindings (
	id UUID NOT NULL, 
	root_id UUID NOT NULL, 
	stream_id UUID NOT NULL, 
	revision BIGINT NOT NULL, 
	recorded_order BIGINT NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	previous_id UUID, 
	previous_fingerprint VARCHAR(64), 
	action TEXT NOT NULL, 
	effective_start TIMESTAMP WITH TIME ZONE, 
	effective_end TIMESTAMP WITH TIME ZONE, 
	actor_database_oid BIGINT NOT NULL, 
	actor_role_oid BIGINT NOT NULL, 
	actor_database_name VARCHAR(63) NOT NULL, 
	actor_role_name VARCHAR(63) NOT NULL, 
	author_session JSONB NOT NULL, 
	command_body JSONB NOT NULL, 
	command_fingerprint VARCHAR(64) NOT NULL, 
	fact_fingerprint VARCHAR(64) NOT NULL, 
	idempotency_key UUID NOT NULL, 
	environment TEXT NOT NULL, 
	root_initial_fact_id UUID NOT NULL, 
	enrolling_issuer_id UUID NOT NULL, 
	author_issuer_fact_id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	role_oid BIGINT NOT NULL, 
	role_name VARCHAR(63) NOT NULL, 
	target_role JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT bindings_root_initializer FOREIGN KEY(root_initial_fact_id, root_id) REFERENCES menuto_identity_source.roots (id, root_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT bindings_author FOREIGN KEY(author_issuer_fact_id, root_id) REFERENCES menuto_identity_source.issuers (id, root_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT bindings_role CHECK (role_oid BETWEEN 1 AND 4294967295 AND octet_length(role_name) BETWEEN 1 AND 63), 
	CONSTRAINT principal_bindings_id_root_stream UNIQUE (id, root_id, stream_id), 
	CONSTRAINT principal_bindings_id_root UNIQUE (id, root_id), 
	CONSTRAINT principal_bindings_revision UNIQUE (root_id, stream_id, revision), 
	CONSTRAINT principal_bindings_order UNIQUE (recorded_order), 
	CONSTRAINT principal_bindings_predecessor FOREIGN KEY(previous_id, root_id, stream_id) REFERENCES menuto_identity_source.principal_bindings (id, root_id, stream_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT principal_bindings_positive CHECK (revision>0 AND recorded_order>0), 
	CONSTRAINT principal_bindings_previous CHECK (((revision=1 AND previous_id IS NULL AND previous_fingerprint IS NULL) OR (revision>1 AND previous_id IS NOT NULL AND previous_fingerprint ~ '^[a-f0-9]{64}$'))), 
	CONSTRAINT principal_bindings_effective CHECK (isfinite(recorded_at) AND ((action='REVOKE' AND effective_start IS NULL AND effective_end IS NULL) OR (action<>'REVOKE' AND effective_start IS NOT NULL AND effective_end IS NOT NULL AND isfinite(effective_start) AND isfinite(effective_end) AND effective_start<effective_end))), 
	CONSTRAINT principal_bindings_action CHECK (action IN ('ENROLL','RENEW','REVOKE')), 
	CONSTRAINT principal_bindings_oids CHECK (actor_database_oid BETWEEN 1 AND 4294967295 AND actor_role_oid BETWEEN 1 AND 4294967295), 
	CONSTRAINT principal_bindings_names CHECK (octet_length(actor_database_name) BETWEEN 1 AND 63 AND octet_length(actor_role_name) BETWEEN 1 AND 63), 
	CONSTRAINT principal_bindings_fingerprints CHECK (command_fingerprint ~ '^[a-f0-9]{64}$' AND fact_fingerprint ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT principal_bindings_typed CHECK (environment='TEST_ONLY' AND jsonb_typeof(author_session)='object' AND jsonb_typeof(command_body)='object' AND command_body->>'version'='1' AND command_body->>'kind'='BINDING' AND command_body->>'action'=action AND command_body->>'environment'='TEST_ONLY' AND (command_body->>'root_id')::uuid=root_id AND (command_body->>'idempotency_key')::uuid=idempotency_key)
)

;
CREATE UNIQUE INDEX bindings_reserve_name ON menuto_identity_source.principal_bindings (root_id, role_name) WHERE action = 'ENROLL';
CREATE UNIQUE INDEX bindings_reserve_oid ON menuto_identity_source.principal_bindings (root_id, role_oid) WHERE action = 'ENROLL';
CREATE INDEX bindings_user ON menuto_identity_source.principal_bindings (root_id, user_id, stream_id);
CREATE INDEX principal_bindings_latest ON menuto_identity_source.principal_bindings (root_id, stream_id, revision DESC);
CREATE INDEX principal_bindings_root_order ON menuto_identity_source.principal_bindings (root_id, recorded_order);

CREATE TABLE menuto_identity_source.operation_grants (
	id UUID NOT NULL, 
	root_id UUID NOT NULL, 
	stream_id UUID NOT NULL, 
	revision BIGINT NOT NULL, 
	recorded_order BIGINT NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	previous_id UUID, 
	previous_fingerprint VARCHAR(64), 
	action TEXT NOT NULL, 
	effective_start TIMESTAMP WITH TIME ZONE, 
	effective_end TIMESTAMP WITH TIME ZONE, 
	actor_database_oid BIGINT NOT NULL, 
	actor_role_oid BIGINT NOT NULL, 
	actor_database_name VARCHAR(63) NOT NULL, 
	actor_role_name VARCHAR(63) NOT NULL, 
	author_session JSONB NOT NULL, 
	command_body JSONB NOT NULL, 
	command_fingerprint VARCHAR(64) NOT NULL, 
	fact_fingerprint VARCHAR(64) NOT NULL, 
	idempotency_key UUID NOT NULL, 
	environment TEXT NOT NULL, 
	root_initial_fact_id UUID NOT NULL, 
	binding_initial_fact_id UUID NOT NULL, 
	binding_id UUID NOT NULL, 
	author_issuer_fact_id UUID NOT NULL, 
	operation TEXT NOT NULL, 
	household_id UUID NOT NULL, 
	tracked_member_id UUID NOT NULL, 
	membership_id UUID NOT NULL, 
	actor_member_id UUID NOT NULL, 
	membership_role TEXT NOT NULL, 
	membership_at_issue JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT grants_root_initializer FOREIGN KEY(root_initial_fact_id, root_id) REFERENCES menuto_identity_source.roots (id, root_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT grants_binding FOREIGN KEY(binding_initial_fact_id, root_id, binding_id) REFERENCES menuto_identity_source.principal_bindings (id, root_id, stream_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT grants_author FOREIGN KEY(author_issuer_fact_id, root_id) REFERENCES menuto_identity_source.issuers (id, root_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT grants_scope CHECK (operation='CAPTURE_EXPLICIT_PLAN_INTENT' AND membership_role IN ('OWNER','EDITOR')), 
	CONSTRAINT operation_grants_id_root_stream UNIQUE (id, root_id, stream_id), 
	CONSTRAINT operation_grants_id_root UNIQUE (id, root_id), 
	CONSTRAINT operation_grants_revision UNIQUE (root_id, stream_id, revision), 
	CONSTRAINT operation_grants_order UNIQUE (recorded_order), 
	CONSTRAINT operation_grants_predecessor FOREIGN KEY(previous_id, root_id, stream_id) REFERENCES menuto_identity_source.operation_grants (id, root_id, stream_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT operation_grants_positive CHECK (revision>0 AND recorded_order>0), 
	CONSTRAINT operation_grants_previous CHECK (((revision=1 AND previous_id IS NULL AND previous_fingerprint IS NULL) OR (revision>1 AND previous_id IS NOT NULL AND previous_fingerprint ~ '^[a-f0-9]{64}$'))), 
	CONSTRAINT operation_grants_effective CHECK (isfinite(recorded_at) AND ((action='REVOKE' AND effective_start IS NULL AND effective_end IS NULL) OR (action<>'REVOKE' AND effective_start IS NOT NULL AND effective_end IS NOT NULL AND isfinite(effective_start) AND isfinite(effective_end) AND effective_start<effective_end))), 
	CONSTRAINT operation_grants_action CHECK (action IN ('GRANT','RENEW','REVOKE')), 
	CONSTRAINT operation_grants_oids CHECK (actor_database_oid BETWEEN 1 AND 4294967295 AND actor_role_oid BETWEEN 1 AND 4294967295), 
	CONSTRAINT operation_grants_names CHECK (octet_length(actor_database_name) BETWEEN 1 AND 63 AND octet_length(actor_role_name) BETWEEN 1 AND 63), 
	CONSTRAINT operation_grants_fingerprints CHECK (command_fingerprint ~ '^[a-f0-9]{64}$' AND fact_fingerprint ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT operation_grants_typed CHECK (environment='TEST_ONLY' AND jsonb_typeof(author_session)='object' AND jsonb_typeof(command_body)='object' AND command_body->>'version'='1' AND command_body->>'kind'='OPERATION_GRANT' AND command_body->>'action'=action AND command_body->>'environment'='TEST_ONLY' AND (command_body->>'root_id')::uuid=root_id AND (command_body->>'idempotency_key')::uuid=idempotency_key)
)

;
CREATE INDEX grants_scope_latest ON menuto_identity_source.operation_grants (root_id, binding_id, operation, household_id, tracked_member_id, revision DESC);
CREATE INDEX operation_grants_latest ON menuto_identity_source.operation_grants (root_id, stream_id, revision DESC);
CREATE INDEX operation_grants_root_order ON menuto_identity_source.operation_grants (root_id, recorded_order);

CREATE TABLE menuto_identity_source.command_receipts (
	id UUID NOT NULL, 
	root_id UUID NOT NULL, 
	actor_role_oid BIGINT NOT NULL, 
	idempotency_key UUID NOT NULL, 
	kind TEXT NOT NULL, 
	stream_id UUID NOT NULL, 
	revision BIGINT NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	command_fingerprint VARCHAR(64) NOT NULL, 
	fact_fingerprint VARCHAR(64) NOT NULL, 
	root_fact_id UUID, 
	issuer_fact_id UUID, 
	binding_fact_id UUID, 
	grant_fact_id UUID, 
	PRIMARY KEY (id), 
	CONSTRAINT receipts_actor_key UNIQUE (root_id, actor_role_oid, idempotency_key), 
	CONSTRAINT receipts_values CHECK (revision>0 AND actor_role_oid BETWEEN 1 AND 4294967295 AND isfinite(recorded_at) AND command_fingerprint ~ '^[a-f0-9]{64}$' AND fact_fingerprint ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT receipts_typed CHECK ((kind='ROOT' AND root_fact_id IS NOT NULL AND num_nonnulls(issuer_fact_id,binding_fact_id,grant_fact_id)=0) OR (kind='ISSUER' AND issuer_fact_id IS NOT NULL AND num_nonnulls(root_fact_id,binding_fact_id,grant_fact_id)=0) OR (kind='BINDING' AND binding_fact_id IS NOT NULL AND num_nonnulls(root_fact_id,issuer_fact_id,grant_fact_id)=0) OR (kind='OPERATION_GRANT' AND grant_fact_id IS NOT NULL AND num_nonnulls(root_fact_id,issuer_fact_id,binding_fact_id)=0)), 
	CONSTRAINT receipts_root_fact FOREIGN KEY(root_fact_id, root_id) REFERENCES menuto_identity_source.roots (id, root_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT receipts_issuer_fact FOREIGN KEY(issuer_fact_id, root_id) REFERENCES menuto_identity_source.issuers (id, root_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT receipts_binding_fact FOREIGN KEY(binding_fact_id, root_id) REFERENCES menuto_identity_source.principal_bindings (id, root_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, 
	CONSTRAINT receipts_grant_fact FOREIGN KEY(grant_fact_id, root_id) REFERENCES menuto_identity_source.operation_grants (id, root_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
)

;
CREATE INDEX receipts_binding_lookup ON menuto_identity_source.command_receipts (binding_fact_id);
CREATE INDEX receipts_grant_lookup ON menuto_identity_source.command_receipts (grant_fact_id);
CREATE INDEX receipts_issuer_lookup ON menuto_identity_source.command_receipts (issuer_fact_id);
CREATE INDEX receipts_root_lookup ON menuto_identity_source.command_receipts (root_fact_id);
"""

NATIVE_DEFINITION_SQL = "menuto_identity_source._canonical_hash_v1('identity.source.v1',jsonb_build_object(\n    'extension',(SELECT e.extname FROM pg_extension e JOIN pg_depend d ON d.refobjid=e.oid\n      WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.refclassid='pg_extension'::regclass AND d.deptype='e'),\n    'extension_version',(SELECT e.extversion FROM pg_extension e JOIN pg_depend d ON d.refobjid=e.oid\n      WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.refclassid='pg_extension'::regclass AND d.deptype='e'),\n    'schema',n.nspname,'definition',pg_get_functiondef(p.oid),\n    'raw_acl_state',CASE WHEN p.proacl IS NULL THEN 'NULL' ELSE 'EXPLICIT' END,\n    'dependencies',coalesce((SELECT jsonb_agg(jsonb_build_array(d.refclassid::regclass::text,d.refobjsubid,d.deptype,\n      pg_describe_object(d.refclassid,d.refobjid,d.refobjsubid)) ORDER BY d.refclassid::regclass::text,d.refobjsubid,d.deptype,\n      pg_describe_object(d.refclassid,d.refobjid,d.refobjsubid)) FROM pg_depend d WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid),'[]'::jsonb)))"

NATIVE_CATALOG_SQL = "SELECT e.oid::bigint extension_oid,e.extnamespace::bigint namespace_oid,n.nspname namespace,\n e.extowner::bigint owner_oid,e.extversion,p.oid::bigint function_oid,p.proname name,\n p.proname||'('||pg_get_function_identity_arguments(p.oid)||')' signature,\n pg_get_function_result(p.oid) result,pg_get_functiondef(p.oid) definition,\n p.proacl::text raw_acl,\n coalesce((SELECT jsonb_agg(jsonb_build_array(a.grantee::bigint,a.grantor::bigint,a.privilege_type,a.is_grantable)\n ORDER BY a.grantee,a.grantor,a.privilege_type,a.is_grantable) FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a),'[]'::jsonb) acl,\n e.extname='sslinfo' AND e.extversion='1.2' AND e.extrelocatable AND e.extconfig IS NULL AND e.extcondition IS NULL AND (SELECT count(*) FROM pg_depend z WHERE z.refclassid='pg_extension'::regclass AND z.refobjid=e.oid AND z.deptype='e')=10 AND n.nspname IN ('public','menuto_prior')\n AND p.pronamespace=n.oid AND p.proowner=e.extowner\n AND e.extowner=(SELECT datdba FROM pg_database WHERE datname=current_database())\n AND EXISTS(SELECT FROM pg_roles WHERE oid=e.extowner AND rolsuper)\n AND p.prokind='f' AND NOT p.prosecdef AND p.prolang=(SELECT oid FROM pg_language WHERE lanname='c')\n AND p.prosrc=p.proname AND p.probin='$libdir/sslinfo' AND p.proconfig IS NULL\n AND EXISTS(SELECT FROM pg_depend d WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND\n d.refclassid='pg_extension'::regclass AND d.refobjid=e.oid AND d.deptype='e') valid\n FROM pg_extension e JOIN pg_namespace n ON n.oid=e.extnamespace\n JOIN pg_proc p ON p.proname IN ('ssl_is_used','ssl_version','ssl_cipher','ssl_client_cert_present','ssl_client_serial','ssl_client_dn','ssl_issuer_dn','ssl_client_dn_field','ssl_issuer_field','ssl_extension_info') OR EXISTS(SELECT FROM pg_depend d\n WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.refclassid='pg_extension'::regclass AND d.refobjid=e.oid AND d.deptype='e')\n WHERE e.extname='sslinfo' ORDER BY p.oid"

NATIVE_SSLINFO_PINS = {
    "menuto_prior": {
        "ssl_is_used": "a4b1867a7b3f38f2ebb5cc6d0d0a47b26956171c2b1496d82adbc4ca272fd472",
        "ssl_version": "2365cc58f0a9c4818905b3fb1fa3ab824512ab42f9e6b6768202d344068c4602",
        "ssl_cipher": "3f1b37250401d42100544750ecc2bf4de2920514ccb89876e73657cbd31b05d3",
        "ssl_client_cert_present": "453648844d7cb028767b08e15fbc34fe729e088fb3973baba879c4da19d1bd69",
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
        "ssl_client_cert_present": "8b2e38efc3604fe6bd53341600b6f5ceb6c71b9242be673d94902e76b6e85f35",
        "ssl_client_serial": "2df2133592e5a46f7a45b4709a4526d4de34af0497be3c827f00392494e895c0",
        "ssl_client_dn": "00143dd70742f20eaf8adcb911d3a6c6aa1a4f8e70d3de5dc7c2bb36cfe7a002",
        "ssl_issuer_dn": "e1b6d8c69120388b0e99a66729dea7110203de08c0ac130ca548a5d040ea48f7",
        "ssl_client_dn_field": "d89638c21de107ad256a57d68ed99bae3ee16f709841082ef005b7015c2bfab4",
        "ssl_issuer_field": "d5ded701ca043d42068f52c1005592744fe3ce0ee10e35ec44d12b2c8f242d5f",
        "ssl_extension_info": "a35809e18bdca93ddc19e751f7998fdf587da76023de889b2ef57436b82f29a3",
    },
}

FUNCTION_SQL = r"""

CREATE FUNCTION menuto_identity_source._canonical_hash_v1(tag text, typed_preimage jsonb)
RETURNS text LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_identity_source,pg_temp AS $f$
DECLARE body text; subtype text:=jsonb_typeof(typed_preimage);
BEGIN
 IF subtype='object' THEN
  SELECT '{'||coalesce(string_agg(to_jsonb(key)::text||':'||
   menuto_identity_source._canonical_hash_v1('_CANONICAL',value),','
   ORDER BY convert_to(key,'UTF8')),'')||'}' INTO body FROM jsonb_each(typed_preimage);
 ELSIF subtype='array' THEN
  SELECT '['||coalesce(string_agg(menuto_identity_source._canonical_hash_v1('_CANONICAL',value),
   ',' ORDER BY ord),'')||']' INTO body FROM jsonb_array_elements(typed_preimage) WITH ORDINALITY a(value,ord);
 ELSIF subtype='number' THEN
  body:=typed_preimage::text;
  IF body !~ '^-?(0|[1-9][0-9]{0,18})$' OR body::numeric NOT BETWEEN -9223372036854775807 AND 9223372036854775807
  THEN RAISE EXCEPTION 'Identity integer limit' USING ERRCODE='22023'; END IF;
 ELSIF subtype IN ('string','boolean','null') THEN body:=typed_preimage::text;
 ELSE RAISE EXCEPTION 'Identity canonical shape' USING ERRCODE='22023';
 END IF;
 IF tag='_CANONICAL' THEN RETURN body; END IF;
 IF tag='identity.request-preimage.v1' THEN
  IF subtype<>'string' THEN RAISE EXCEPTION 'Identity request shape' USING ERRCODE='22023'; END IF;
  body:=typed_preimage#>>'{}';
 ELSIF tag NOT IN ('identity.command.v1','identity.fact.v1','identity.source.v1',
                  'identity.check.v1','policy.identity-inspection.v1') THEN
  RAISE EXCEPTION 'Identity hash domain' USING ERRCODE='22023';
 END IF;
 RETURN encode(sha256(convert_to(tag,'UTF8')||decode('00','hex')||convert_to(body,'UTF8')),'hex');
END $f$;

CREATE FUNCTION menuto_identity_source._parameter_acl_facts_v1(actor_oid oid)
RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_identity_source,pg_temp AS $f$
DECLARE result jsonb; total bigint;
BEGIN
 SELECT count(*) INTO total FROM pg_parameter_acl;
 IF total>4096 THEN RAISE EXCEPTION 'Identity catalog limit' USING ERRCODE='54000'; END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_object(
  'version',1,'kind','PARAMETER','object_oid',p.oid::bigint,'sub_id',0,'schema_name',NULL,
  'object_name',p.parname,'owner_oid',NULL,'definition_fingerprint',NULL,
  'acl',CASE WHEN p.paracl IS NULL THEN NULL WHEN cardinality(p.paracl)=0 THEN '[]'::jsonb ELSE coalesce((
   SELECT jsonb_agg(jsonb_build_array(a.grantee::bigint,a.grantor::bigint,a.privilege_type,a.is_grantable)
     ORDER BY a.grantee,a.grantor,a.privilege_type,a.is_grantable)
   FROM aclexplode(p.paracl) a),'[]'::jsonb) END)
  ORDER BY convert_to(p.parname,'UTF8'),p.oid),'[]'::jsonb) INTO result FROM pg_parameter_acl p;
 RETURN result;
END $f$;

CREATE FUNCTION menuto_identity_source._tls_fact_v1() RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path=pg_catalog,menuto_identity_source,pg_temp
BEGIN ATOMIC
 SELECT jsonb_build_object('tls',CASE WHEN EXISTS (
  SELECT FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_extension e ON e.oid=__TLS_EXTENSION_OID__
  JOIN pg_catalog.pg_language l ON l.oid=p.prolang
  WHERE p.oid=__TLS_FUNCTION_OID__ AND p.pronamespace=__TLS_NAMESPACE_OID__
   AND e.extname='sslinfo' AND e.extnamespace=__TLS_NAMESPACE_OID__
   AND p.proowner=__TLS_OWNER_OID__ AND p.proowner=e.extowner
   AND l.lanname='c' AND p.prosrc='ssl_is_used' AND p.probin='$libdir/sslinfo'
   AND p.prorettype='pg_catalog.bool'::regtype AND p.pronargs=0 AND p.prokind='f'
   AND e.extversion='1.2' AND NOT p.prosecdef AND p.proconfig IS NULL AND p.proisstrict
   AND p.provolatile='v' AND p.proparallel='r' AND NOT p.proleakproof AND NOT p.proretset
   AND p.prosupport=0 AND p.pronargdefaults=0 AND p.procost=1 AND p.prorows=0
   AND EXISTS(SELECT FROM pg_catalog.pg_depend d WHERE d.classid='pg_catalog.pg_proc'::regclass
    AND d.objid=p.oid AND d.refclassid='pg_catalog.pg_extension'::regclass
    AND d.refobjid=e.oid AND d.deptype='e')
 ) THEN __TLS_NAMESPACE__.ssl_is_used() ELSE NULL END);
END;

CREATE FUNCTION menuto_identity_source._safe_role_v1(actor_oid oid, mode text)
RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_identity_source,pg_temp AS $f$
DECLARE native_rows jsonb; native_row jsonb; native_pins jsonb:=$native$__NATIVE_PINS__$native$::jsonb;
 native_oids jsonb:=$native$__NATIVE_OIDS__$native$::jsonb; native_acls jsonb:=$native$__NATIVE_RAW_ACLS__$native$::jsonb;
 role_rows jsonb; edge_rows jsonb; object_rows jsonb; role_ids oid[]; inherit_ids oid[];
 legacy_pins jsonb:=$itr_manifest$__LEGACY_PINS__$itr_manifest$::jsonb;
 legacy_oids jsonb:=$itr_oids$__LEGACY_OIDS__$itr_oids$::jsonb;
 reachable oid[]; catalog_ids oid[]; ids oid[]; next_ids oid[]; pass integer; dangerous boolean; owner_oid oid;
BEGIN
 IF current_setting('server_version_num')<>'180004' THEN
  RAISE EXCEPTION 'Identity native deployment version' USING ERRCODE='42501'; END IF;
 IF mode NOT IN ('BOOTSTRAP','ISSUER','REQUESTER','TARGET_ISSUER','TARGET_REQUESTER') THEN
  RAISE EXCEPTION 'Identity role mode' USING ERRCODE='42501';
 END IF;
 SELECT oid INTO STRICT owner_oid FROM pg_roles WHERE rolname='menuto_identity_source_owner';
 IF EXISTS(SELECT FROM pg_roles WHERE rolname IN ('menuto_identity_source_owner',
     'menuto_identity_bootstrap','menuto_identity_issuer','menuto_identity_requester')
     AND (rolcanlogin OR rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls))
    OR (SELECT count(*) FROM pg_roles WHERE rolname IN ('menuto_identity_source_owner',
     'menuto_identity_bootstrap','menuto_identity_issuer','menuto_identity_requester'))<>4
    OR owner_oid=(SELECT datdba FROM pg_database WHERE datname=current_database()) THEN
  RAISE EXCEPTION 'Identity unsafe infrastructure owner/group' USING ERRCODE='42501'; END IF;

 role_ids:=ARRAY[actor_oid]; reachable:=ARRAY[actor_oid]; inherit_ids:=ARRAY[actor_oid];
 FOR pass IN 1..3 LOOP
  ids:=ARRAY[actor_oid];
  LOOP
   SELECT array_agg(oid ORDER BY oid) INTO next_ids FROM (
    SELECT DISTINCT oid FROM (
      SELECT unnest(ids) oid UNION ALL
      SELECT m.roleid FROM pg_auth_members m WHERE m.member=ANY(ids)
       AND (pass=1 OR pass=2 AND (m.inherit_option OR m.set_option)
            OR pass=3 AND m.inherit_option)
    ) reached LIMIT 65
   ) bounded;
   IF cardinality(next_ids)>64 THEN
    RAISE EXCEPTION 'Identity role limit' USING ERRCODE='54000'; END IF;
   EXIT WHEN next_ids=ids;
   ids:=next_ids;
  END LOOP;
  IF pass=1 THEN role_ids:=ids;
  ELSIF pass=2 THEN reachable:=ids; ELSE inherit_ids:=ids; END IF;
 END LOOP;
 catalog_ids:=role_ids;
 SELECT array_agg(DISTINCT oid) INTO role_ids FROM pg_roles
  WHERE oid=ANY(role_ids) OR rolname IN ('menuto_identity_source_owner','menuto_identity_bootstrap',
      'menuto_identity_issuer','menuto_identity_requester')
     OR oid=(SELECT datdba FROM pg_database WHERE datname=current_database());
 IF cardinality(role_ids)>64 THEN RAISE EXCEPTION 'Identity role limit' USING ERRCODE='54000'; END IF;
 SELECT jsonb_agg(jsonb_build_object('version',1,'role_oid',oid::bigint,'role_name',rolname,
  'can_login',rolcanlogin,'superuser',rolsuper,'create_role',rolcreaterole,'create_db',rolcreatedb,
  'replication',rolreplication,'bypass_rls',rolbypassrls,'inherit',rolinherit,
  'valid_until',CASE WHEN rolvaliduntil IS NULL OR NOT isfinite(rolvaliduntil) THEN NULL ELSE
   to_char(rolvaliduntil AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') END)
   ORDER BY oid) INTO role_rows FROM pg_roles WHERE oid=ANY(role_ids);
 SELECT coalesce(jsonb_agg(jsonb_build_object('version',1,'role_oid',roleid::bigint,
  'member_oid',member::bigint,'grantor_oid',grantor::bigint,'inherit_option',inherit_option,
  'set_option',set_option,'admin_option',admin_option)
  ORDER BY member,roleid,grantor),'[]'::jsonb) INTO edge_rows FROM (
  SELECT * FROM pg_auth_members WHERE member=ANY(catalog_ids) LIMIT 129) bounded_edges;
 IF jsonb_array_length(edge_rows)>128 OR EXISTS(
   SELECT FROM pg_auth_members WHERE member=owner_oid) THEN
  RAISE EXCEPTION 'Identity role graph limit' USING ERRCODE='42501'; END IF;

 WITH objects(kind,oid,sub_id,ns,name,owner_id,acl,definition) AS (
  SELECT 'DATABASE',d.oid,0,NULL::text,d.datname::text,d.datdba,
   coalesce(d.datacl,acldefault('d',d.datdba)),NULL::text FROM pg_database d
  UNION ALL
  SELECT 'SCHEMA',n.oid,0,NULL,n.nspname::text,n.nspowner,
   coalesce(n.nspacl,acldefault('n',n.nspowner)),NULL FROM pg_namespace n
    WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema'
  UNION ALL
  SELECT CASE WHEN c.relkind='S' THEN 'SEQUENCE' ELSE 'TABLE' END,c.oid,0,n.nspname::text,
   c.relname::text,c.relowner,coalesce(c.relacl,acldefault(
    CASE WHEN c.relkind='S' THEN 'S'::"char" ELSE 'r'::"char" END,c.relowner)),NULL
   FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE c.relkind IN ('r','p','v','m','f','S') AND (n.nspname !~ '^pg_' OR mode<>'BOOTSTRAP' AND c.relowner=ANY(reachable)) AND n.nspname<>'information_schema'
  UNION ALL
  SELECT 'COLUMN',c.oid,a.attnum,n.nspname::text,c.relname::text||'.'||a.attname::text,
   c.relowner,a.attacl,NULL FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
   JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE a.attnum>0 AND NOT a.attisdropped AND a.attacl IS NOT NULL
    AND n.nspname !~ '^pg_' AND n.nspname<>'information_schema'
  UNION ALL
  SELECT 'FUNCTION',p.oid,0,n.nspname::text,p.proname::text,p.proowner,
   coalesce(p.proacl,acldefault('f',p.proowner)),
   CASE WHEN p.proname IN ('ssl_is_used','ssl_version','ssl_cipher','ssl_client_cert_present','ssl_client_serial','ssl_client_dn','ssl_issuer_dn','ssl_client_dn_field','ssl_issuer_field','ssl_extension_info') THEN menuto_identity_source._canonical_hash_v1('identity.source.v1',jsonb_build_object(
    'extension',(SELECT e.extname FROM pg_extension e JOIN pg_depend d ON d.refobjid=e.oid
      WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.refclassid='pg_extension'::regclass AND d.deptype='e'),
    'extension_version',(SELECT e.extversion FROM pg_extension e JOIN pg_depend d ON d.refobjid=e.oid
      WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.refclassid='pg_extension'::regclass AND d.deptype='e'),
    'schema',n.nspname,'definition',pg_get_functiondef(p.oid),
    'raw_acl_state',CASE WHEN p.proacl IS NULL THEN 'NULL' ELSE 'EXPLICIT' END,
    'dependencies',coalesce((SELECT jsonb_agg(jsonb_build_array(d.refclassid::regclass::text,d.refobjsubid,d.deptype,
      pg_describe_object(d.refclassid,d.refobjid,d.refobjsubid)) ORDER BY d.refclassid::regclass::text,d.refobjsubid,d.deptype,
      pg_describe_object(d.refclassid,d.refobjid,d.refobjsubid)) FROM pg_depend d WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid),'[]'::jsonb)))
   WHEN n.nspname='public' THEN
    menuto_identity_source._canonical_hash_v1('identity.source.v1',jsonb_build_object(
     'schema',n.nspname,'signature',p.proname||'('||coalesce((SELECT string_agg(format_type(t,NULL),',' ORDER BY ord) FROM unnest(p.proargtypes::oid[]) WITH ORDINALITY args(t,ord)),'')||')',
     'arguments',pg_get_function_identity_arguments(p.oid),'result',pg_get_function_result(p.oid),
     'language',(SELECT lanname FROM pg_language WHERE oid=p.prolang),'kind',p.prokind,
     'security_definer',p.prosecdef,'volatility',p.provolatile,'config',to_jsonb(p.proconfig),
     'body',p.prosrc,'library',p.probin,'parsed',p.prosqlbody::text,
     'strict',p.proisstrict,'leakproof',p.proleakproof,'parallel',p.proparallel,
     'returns_set',p.proretset,'return_type',format_type(p.prorettype,NULL),
     'cost',p.procost::text,'rows',p.prorows::text,'support',p.prosupport::regproc::text,
     'raw_acl',p.proacl::text,'definition',pg_get_functiondef(p.oid),'dependencies',coalesce((
      SELECT jsonb_agg(jsonb_build_array(d.refclassid::regclass::text,d.refobjsubid,d.deptype,
          pg_describe_object(d.refclassid,d.refobjid,d.refobjsubid))
          ORDER BY d.refclassid::regclass::text,d.refobjsubid,d.deptype,
           pg_describe_object(d.refclassid,d.refobjid,d.refobjsubid))
      FROM pg_depend d WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid),'[]'::jsonb)))
   ELSE menuto_identity_source._canonical_hash_v1('identity.source.v1',jsonb_build_object(
    'signature',pg_get_function_identity_arguments(p.oid),'result',pg_get_function_result(p.oid),
    'language',p.prolang::bigint,'body',p.prosrc,'library',p.probin,
    'parsed',p.prosqlbody::text,'config',to_jsonb(p.proconfig),'security_definer',p.prosecdef)) END
   FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
   WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema'
 )
 SELECT coalesce(jsonb_agg(jsonb_build_object('version',1,'kind',kind,'object_oid',o.oid::bigint,
   'sub_id',sub_id,'schema_name',ns,'object_name',name,'owner_oid',owner_id::bigint,
   'definition_fingerprint',definition,'acl',coalesce((SELECT jsonb_agg(
    jsonb_build_array(a.grantee::bigint,a.grantor::bigint,a.privilege_type,a.is_grantable)
    ORDER BY a.grantee,a.grantor,a.privilege_type,a.is_grantable) FROM aclexplode(o.acl) a),'[]'::jsonb))
   ORDER BY kind,o.oid,sub_id),'[]'::jsonb) INTO object_rows FROM (SELECT * FROM objects LIMIT 4097) o;
 object_rows:=object_rows||menuto_identity_source._parameter_acl_facts_v1(actor_oid);
 IF jsonb_array_length(object_rows)>4096 THEN
  RAISE EXCEPTION 'Identity catalog limit' USING ERRCODE='54000'; END IF;
 -- Exact native extension member class, independent of the 68 historical pins.
 SELECT jsonb_agg(to_jsonb(n)) INTO native_rows FROM (__NATIVE_CATALOG_SQL__) n;
 IF jsonb_array_length(native_rows) IS DISTINCT FROM 10 THEN
  RAISE EXCEPTION 'Identity native extension member set' USING ERRCODE='42501'; END IF;
 FOR native_row IN SELECT * FROM jsonb_array_elements(native_rows) LOOP
  IF NOT coalesce((native_row->>'valid')::boolean,false)
    OR native_row->>'namespace'<>'__TLS_NAMESPACE__'
    OR (native_row->>'extension_oid')::bigint<>__TLS_EXTENSION_OID__
    OR NOT native_oids ? (native_row->>'name')
    OR native_row->'function_oid' IS DISTINCT FROM native_oids->(native_row->>'name')
    OR native_row->'raw_acl' IS DISTINCT FROM native_acls->(native_row->>'name')
    OR NOT EXISTS(SELECT FROM jsonb_array_elements(object_rows) o WHERE o->>'kind'='FUNCTION'
      AND o->'object_oid'=native_row->'function_oid' AND o->>'schema_name'='__TLS_NAMESPACE__'
      AND o->>'definition_fingerprint'=native_pins->>(native_row->>'name')) THEN
   RAISE EXCEPTION 'Identity native extension catalog mismatch' USING ERRCODE='42501'; END IF;
 END LOOP;
 -- Target schema cannot acquire an unapproved CREATE route, even when ordinary reads are pinned.
 IF EXISTS(SELECT FROM pg_namespace n,LATERAL aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) a
   WHERE n.oid=__TLS_NAMESPACE_OID__ AND a.privilege_type='CREATE'
    AND a.grantee NOT IN (n.nspowner,__TLS_OWNER_OID__)) THEN
  RAISE EXCEPTION 'Identity native schema CREATE' USING ERRCODE='42501'; END IF;
 -- Every historical public routine and installed OID must be present, exact and safe.
 IF (SELECT count(*) FROM jsonb_array_elements(object_rows) o WHERE
       o->>'kind'='FUNCTION' AND o->>'schema_name'='public' AND NOT native_pins ? (o->>'object_name'))<>(SELECT count(*) FROM jsonb_object_keys(legacy_pins))
  OR EXISTS(SELECT FROM jsonb_array_elements(object_rows) o WHERE
      o->>'kind'='FUNCTION' AND o->>'schema_name'='public' AND NOT native_pins ? (o->>'object_name') AND (
       NOT legacy_pins ? (o->>'object_name') OR
       o->>'definition_fingerprint' IS DISTINCT FROM legacy_pins->(o->>'object_name')->>'fingerprint' OR
       (o->>'object_oid')::bigint IS DISTINCT FROM (legacy_oids->>(o->>'object_name'))::bigint OR
       (o->>'owner_oid')::oid IS DISTINCT FROM (SELECT datdba FROM pg_database WHERE datname=current_database())
      )) THEN
   RAISE EXCEPTION 'Identity UNDETERMINED legacy routine/dependency/ACL' USING ERRCODE='42501'; END IF;
 IF EXISTS(SELECT FROM jsonb_array_elements(object_rows) o,
    jsonb_array_elements(CASE WHEN jsonb_typeof(o->'acl')='array' THEN o->'acl' ELSE '[]'::jsonb END) a
    WHERE o->>'kind'='FUNCTION' AND o->>'schema_name'='menuto_identity_source' AND (a->>0)::oid=0) THEN
  RAISE EXCEPTION 'Identity PUBLIC protected routine capability' USING ERRCODE='42501'; END IF;
 IF NOT EXISTS(SELECT FROM pg_roles WHERE oid=actor_oid AND rolcanlogin AND
       (rolvaliduntil IS NULL OR rolvaliduntil>clock_timestamp())) THEN
  RAISE EXCEPTION 'Identity principal rejected' USING ERRCODE='42501'; END IF;
 IF mode='BOOTSTRAP' THEN
  IF NOT (EXISTS(SELECT FROM pg_roles WHERE oid=actor_oid AND rolsuper) OR
       actor_oid=(SELECT datdba FROM pg_database WHERE datname=current_database()))
      OR NOT pg_has_role(actor_oid,'menuto_identity_bootstrap','USAGE') THEN
   RAISE EXCEPTION 'Identity bootstrap rejected' USING ERRCODE='42501'; END IF;
 ELSE
  SELECT EXISTS(SELECT FROM pg_roles WHERE oid=ANY(reachable) AND
    (rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls
     OR left(rolname,3)='pg_' OR oid=owner_oid OR oid=(SELECT datdba FROM pg_database WHERE datname=current_database())))
    OR EXISTS(SELECT FROM pg_auth_members WHERE member=ANY(reachable) AND admin_option)
   INTO dangerous;
  IF dangerous OR NOT pg_has_role(actor_oid,
   CASE WHEN mode IN ('ISSUER','TARGET_ISSUER') THEN 'menuto_identity_issuer'
        ELSE 'menuto_identity_requester' END,'USAGE')
   OR pg_has_role(actor_oid,'menuto_identity_bootstrap','USAGE')
   OR pg_has_role(actor_oid,CASE WHEN mode IN ('ISSUER','TARGET_ISSUER')
     THEN 'menuto_identity_requester' ELSE 'menuto_identity_issuer' END,'USAGE') THEN
   RAISE EXCEPTION 'Identity ordinary role rejected' USING ERRCODE='42501'; END IF;
  SELECT EXISTS(
   SELECT FROM jsonb_array_elements(object_rows) o WHERE
    (o->>'owner_oid')::oid=ANY(reachable) OR EXISTS(
      SELECT FROM jsonb_array_elements(CASE WHEN jsonb_typeof(o->'acl')='array' THEN o->'acl' ELSE '[]'::jsonb END) a
      WHERE ((a->>0)::oid=ANY(inherit_ids) OR (a->>0)::oid=0) AND (
       o->>'kind'='PARAMETER'
       OR (o->>'kind' IN ('DATABASE','SCHEMA') AND a->>2='CREATE')
       OR o->>'kind' IN ('TABLE','COLUMN','SEQUENCE')
       OR (o->>'kind'='FUNCTION' AND (
        (a->>0)::oid<>0 OR has_schema_privilege(actor_oid,o->>'schema_name','USAGE'))
         AND NOT (o->>'schema_name'='public' AND legacy_pins ? (o->>'object_name'))
         AND NOT (o->>'schema_name'='__TLS_NAMESPACE__' AND native_pins ? (o->>'object_name'))
         AND NOT (o->>'schema_name'='menuto_identity_source' AND
          CASE WHEN mode IN ('ISSUER','TARGET_ISSUER')
             THEN o->>'object_name' IN ('change_binding','change_operation_grant')
             ELSE o->>'object_name'='capture_request_source' END))
      )
    )
  ) INTO dangerous;
  IF dangerous THEN RAISE EXCEPTION 'Identity unsafe privilege' USING ERRCODE='42501'; END IF;
 END IF;
 RETURN jsonb_build_object('roles',role_rows,'edges',edge_rows,'objects',object_rows);
END $f$;

CREATE FUNCTION menuto_identity_source._session_fact_v1(mode text)
RETURNS jsonb LANGUAGE plpgsql VOLATILE
SET search_path=pg_catalog,menuto_identity_source,pg_temp AS $f$
DECLARE actor oid; catalog jsonb; actual_db record; owner_oid oid; now_at timestamptz;
BEGIN
 now_at:=clock_timestamp();
 SELECT oid INTO STRICT actor FROM pg_roles WHERE rolname=session_user;
 SELECT oid,datdba,datname INTO STRICT actual_db FROM pg_database WHERE datname=current_database();
 SELECT oid INTO STRICT owner_oid FROM pg_roles WHERE rolname=current_user;
 IF current_user<>'menuto_identity_source_owner' OR
    system_user IS DISTINCT FROM 'scram-sha-256:'||session_user OR
    current_setting('role')<>'none' OR inet_client_addr() IS NULL OR
    menuto_identity_source._tls_fact_v1()->>'tls' IS DISTINCT FROM 'true' THEN
  RAISE EXCEPTION 'Identity authentication rejected' USING ERRCODE='42501'; END IF;
 catalog:=menuto_identity_source._safe_role_v1(actor,mode);
 RETURN jsonb_build_object(
  'version',1,'database_oid',actual_db.oid::bigint,'database_owner_oid',actual_db.datdba::bigint,
  'login_role_oid',actor::bigint,'execution_owner_oid',owner_oid::bigint,
  'database_name',actual_db.datname,
  'endpoint_id','PG18:'||actual_db.oid::text||':'||host(inet_server_addr())||':'||inet_server_port()::text,
  'client_address',host(inet_client_addr()),'server_address',host(inet_server_addr()),
  'server_port',inet_server_port(),'backend_pid',pg_backend_pid(),'session_user',session_user,
  'system_user',system_user,'requested_role',current_setting('role'),
  'authentication_method','scram-sha-256','tls',true,
  'isolation',upper(replace(current_setting('transaction_isolation'),' ','_')),
  'read_only',current_setting('transaction_read_only')='on',
  'observed_at',to_char(now_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
 )||catalog;
END $f$;


CREATE FUNCTION menuto_identity_source._parse_command_v1(raw_text text, kind text)
RETURNS jsonb LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_identity_source,pg_temp AS $f$
DECLARE d jsonb; expected text[]; key text; ids text[]; eff jsonb; endpoint timestamptz;
 raw_request text; child jsonb; context jsonb; bytes integer; token_depth integer:=0;
 quoted boolean:=false; escaped boolean:=false; ch text; n integer;
BEGIN
 bytes:=octet_length(raw_text);
 IF current_setting('server_encoding')<>'UTF8' OR raw_text IS NULL OR
  bytes>(CASE WHEN kind='REQUEST' THEN 131072 ELSE 16384 END) THEN
  RAISE EXCEPTION 'Identity byte limit' USING ERRCODE='54000'; END IF;
 -- Bound nesting before JSONB materialization; quoted raw child text is counted as text.
 FOR n IN 1..char_length(raw_text) LOOP
  ch:=substr(raw_text,n,1);
  IF quoted THEN
   IF escaped THEN escaped:=false;
   ELSIF ch=E'\\' THEN escaped:=true;
   ELSIF ch='"' THEN quoted:=false; END IF;
  ELSIF ch='"' THEN quoted:=true;
  ELSIF ch IN ('{','[') THEN token_depth:=token_depth+1;
   IF token_depth>9 THEN RAISE EXCEPTION 'Identity depth limit' USING ERRCODE='54000'; END IF;
  ELSIF ch IN ('}',']') THEN token_depth:=token_depth-1;
  END IF;
 END LOOP;
 IF NOT raw_text IS JSON OBJECT WITH UNIQUE KEYS THEN
  RAISE EXCEPTION 'Identity unique JSON object required' USING ERRCODE='22023'; END IF;
 d:=raw_text::jsonb;
 IF kind='REQUEST' THEN
  expected:=ARRAY['version','operation','actor_user_id','household_id','tracked_member_id',
    'request_id','request_revision','horizon','request_utf8','request_preimage_fingerprint','environment'];
  ids:=ARRAY['actor_user_id','household_id','tracked_member_id','request_id'];
 ELSE
  expected:=ARRAY['version','root_id','idempotency_key','expected_revision','predecessor_id',
    'evidence_id','evidence_version','evidence_preimage','environment','kind','action','effective'];
  ids:=ARRAY['root_id','idempotency_key','predecessor_id'];
  IF kind='ISSUER' THEN
   expected:=expected||ARRAY['issuer_id','role_name','user_id','capability'];
   ids:=ids||ARRAY['issuer_id','user_id'];
  ELSIF kind='BINDING' THEN
   expected:=expected||ARRAY['binding_id','issuer_id','user_id','role_name'];
   ids:=ids||ARRAY['binding_id','issuer_id','user_id'];
  ELSIF kind='OPERATION_GRANT' THEN
   expected:=expected||ARRAY['grant_id','binding_id','issuer_id','household_id',
     'tracked_member_id','operation'];
   ids:=ids||ARRAY['grant_id','binding_id','issuer_id','household_id','tracked_member_id'];
  ELSIF kind<>'ROOT' THEN RAISE EXCEPTION 'Identity command kind' USING ERRCODE='22023'; END IF;
 END IF;
 IF (SELECT array_agg(k ORDER BY k) FROM jsonb_object_keys(d) k) IS DISTINCT FROM
    (SELECT array_agg(k ORDER BY k) FROM unnest(expected) k)
    OR d->'version'<>'1'::jsonb OR d->>'environment' IS DISTINCT FROM 'TEST_ONLY' THEN
  RAISE EXCEPTION 'Identity exact command structure' USING ERRCODE='22023'; END IF;
 FOREACH key IN ARRAY ids LOOP
  IF key='predecessor_id' AND d->key='null'::jsonb THEN CONTINUE; END IF;
  IF jsonb_typeof(d->key)<>'string' OR d->>key !~
   '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
   RAISE EXCEPTION 'Identity canonical UUID required' USING ERRCODE='22023'; END IF;
  PERFORM (d->>key)::uuid;
 END LOOP;
 key:=CASE WHEN kind='REQUEST' THEN 'request_revision' ELSE 'expected_revision' END;
 IF jsonb_typeof(d->key)<>'number' OR d->>key !~ '^(0|[1-9][0-9]{0,18})$' OR
    (d->>key)::numeric>9223372036854775807 THEN
  RAISE EXCEPTION 'Identity exact revision required' USING ERRCODE='22023'; END IF;
 IF kind='REQUEST' THEN
  IF d->>'operation' IS DISTINCT FROM 'CAPTURE_EXPLICIT_PLAN_INTENT' OR
     jsonb_typeof(d->'request_utf8')<>'string' OR
     octet_length(d->>'request_utf8') NOT BETWEEN 1 AND 49152 OR
     d->>'request_preimage_fingerprint' !~ '^[a-f0-9]{64}$' THEN
   RAISE EXCEPTION 'Identity request binding' USING ERRCODE='22023'; END IF;
  raw_request:=d->>'request_utf8';
  IF NOT raw_request IS JSON OBJECT WITH UNIQUE KEYS THEN
   RAISE EXCEPTION 'Identity raw context JSON' USING ERRCODE='22023'; END IF;
  child:=raw_request::jsonb;context:=child->'context';
  IF jsonb_typeof(context)<>'object' OR child->>'environment' IS DISTINCT FROM 'TEST_ONLY' THEN
   RAISE EXCEPTION 'Identity request context' USING ERRCODE='22023'; END IF;
  FOREACH key IN ARRAY ARRAY['actor_user_id','household_id','tracked_member_id',
    'request_id','request_revision'] LOOP
   IF context->key IS DISTINCT FROM d->key THEN
    RAISE EXCEPTION 'Identity request context mismatch' USING ERRCODE='22023'; END IF;
  END LOOP;
  IF menuto_identity_source._canonical_hash_v1('identity.request-preimage.v1',d->'request_utf8')
     <>d->>'request_preimage_fingerprint' THEN
   RAISE EXCEPTION 'Identity request hash mismatch' USING ERRCODE='22023'; END IF;
  FOREACH key IN ARRAY ARRAY['start','end'] LOOP
   IF jsonb_typeof(d->'horizon'->key)<>'string' OR jsonb_typeof(context->'horizon'->key)<>'string'
      OR (d->'horizon'->>key) !~ 'T.*(Z|[+-][0-9]{2}:[0-9]{2})$'
      OR (context->'horizon'->>key) !~ 'T.*(Z|[+-][0-9]{2}:[0-9]{2})$' THEN
    RAISE EXCEPTION 'Identity zoned horizon' USING ERRCODE='22023'; END IF;
   endpoint:=(d->'horizon'->>key)::timestamptz;
   IF NOT isfinite(endpoint) OR endpoint IS DISTINCT FROM
      (context->'horizon'->>key)::timestamptz THEN
    RAISE EXCEPTION 'Identity horizon mismatch' USING ERRCODE='22023'; END IF;
   d:=jsonb_set(d,ARRAY['horizon',key],to_jsonb(
    to_char(endpoint AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')));
  END LOOP;
  IF (SELECT array_agg(k ORDER BY k) FROM jsonb_object_keys(d->'horizon') k)<>
      ARRAY['end','start'] OR (d->'horizon'->>'start')::timestamptz>=
      (d->'horizon'->>'end')::timestamptz THEN
   RAISE EXCEPTION 'Identity horizon shape' USING ERRCODE='22023'; END IF;
  RETURN d;
 END IF;
 IF d->>'kind' IS DISTINCT FROM kind OR d->>'action' IS NULL OR
   (kind='ROOT' AND d->>'action' NOT IN ('INITIALIZE','RENEW','REVOKE')) OR
   (kind IN ('ISSUER','BINDING') AND d->>'action' NOT IN ('ENROLL','RENEW','REVOKE')) OR
   (kind='OPERATION_GRANT' AND d->>'action' NOT IN ('GRANT','RENEW','REVOKE')) THEN
  RAISE EXCEPTION 'Identity action' USING ERRCODE='22023'; END IF;
 FOREACH key IN ARRAY ARRAY['evidence_id','evidence_version'] LOOP
  IF jsonb_typeof(d->key)<>'string' OR octet_length(d->>key) NOT BETWEEN 1 AND 64 OR
   d->>key !~ '^[!-~]+$' THEN
   RAISE EXCEPTION 'Identity evidence key' USING ERRCODE='22023'; END IF;
 END LOOP;
 IF jsonb_typeof(d->'evidence_preimage')<>'string' OR
   octet_length(d->>'evidence_preimage') NOT BETWEEN 1 AND 4096 THEN
  RAISE EXCEPTION 'Identity evidence preimage' USING ERRCODE='22023'; END IF;
 IF kind IN ('ISSUER','BINDING') AND (jsonb_typeof(d->'role_name')<>'string' OR
   octet_length(d->>'role_name') NOT BETWEEN 1 AND 63 OR EXISTS(
    SELECT FROM generate_series(1,char_length(d->>'role_name')) i
    WHERE ascii(substr(d->>'role_name',i,1))<32 OR ascii(substr(d->>'role_name',i,1)) BETWEEN 127 AND 159))
  THEN RAISE EXCEPTION 'Identity role name' USING ERRCODE='22023'; END IF;
 IF kind='ISSUER' AND d->>'capability' IS DISTINCT FROM 'BINDINGS_AND_SCOPE_GRANTS' OR
    kind='OPERATION_GRANT' AND d->>'operation' IS DISTINCT FROM 'CAPTURE_EXPLICIT_PLAN_INTENT' THEN
  RAISE EXCEPTION 'Identity operation' USING ERRCODE='22023'; END IF;
 eff:=d->'effective';
 IF d->>'action'='REVOKE' THEN
  IF eff<>'null'::jsonb THEN RAISE EXCEPTION 'Identity revoke interval' USING ERRCODE='22023'; END IF;
 ELSE
  IF jsonb_typeof(eff)<>'object' OR
   (SELECT array_agg(k ORDER BY k) FROM jsonb_object_keys(eff) k)<>ARRAY['end','mode','start','version']
   OR eff->'version'<>'1'::jsonb OR eff->>'mode' NOT IN ('IMMEDIATE','SCHEDULED')
   OR (eff->>'mode'='IMMEDIATE') IS DISTINCT FROM (eff->'start'='null'::jsonb) THEN
   RAISE EXCEPTION 'Identity effective structure' USING ERRCODE='22023'; END IF;
  FOREACH key IN ARRAY ARRAY['start','end'] LOOP
   IF key='start' AND eff->key='null'::jsonb THEN CONTINUE; END IF;
   IF jsonb_typeof(eff->key)<>'string' OR eff->>key !~ 'T.*(Z|[+-][0-9]{2}:[0-9]{2})$' THEN
    RAISE EXCEPTION 'Identity effective time' USING ERRCODE='22023'; END IF;
   endpoint:=(eff->>key)::timestamptz;
   IF NOT isfinite(endpoint) THEN RAISE EXCEPTION 'Identity finite interval' USING ERRCODE='22023'; END IF;
   eff:=jsonb_set(eff,ARRAY[key],to_jsonb(
     to_char(endpoint AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')));
  END LOOP;
  d:=jsonb_set(d,'{effective}',eff);
 END IF;
 RETURN d;
END $f$;

CREATE FUNCTION menuto_identity_source._lock_frontiers_v1(root_id uuid,binding_id uuid,grant_id uuid)
RETURNS void LANGUAGE plpgsql VOLATILE
SET search_path=pg_catalog,menuto_identity_source,pg_temp AS $f$
BEGIN
 PERFORM set_config('lock_timeout','1000ms',true);
 PERFORM pg_advisory_xact_lock(17492711,0);
 PERFORM 1 FROM menuto_identity_source.frontiers f WHERE f.root_id=_lock_frontiers_v1.root_id
  ORDER BY CASE f.kind WHEN 'ROOT' THEN 0 WHEN 'ISSUER_DIRECTORY' THEN 1
   WHEN 'BINDING' THEN 2 ELSE 3 END,f.stream_id FOR UPDATE;
END $f$;

CREATE FUNCTION menuto_identity_source._authority_at_v1(
 root_id uuid,stream_id uuid,recorded_at timestamptz,effective_start timestamptz,effective_end timestamptz)
RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,menuto_identity_source,pg_temp AS $f$
DECLARE rows jsonb; current_fact jsonb; row jsonb; cursor_at timestamptz:=effective_start;
BEGIN
 SELECT coalesce(jsonb_agg(fact ORDER BY ord),'[]'::jsonb) INTO rows FROM (
  SELECT command_body AS cmd,recorded_order ord,
   jsonb_build_object('id',id,'start',r.effective_start,'end',r.effective_end,'action',action,
     'recorded_at',r.recorded_at,'target_role',NULL::jsonb) fact
    FROM menuto_identity_source.roots r WHERE r.root_id=_authority_at_v1.root_id
      AND r.stream_id=_authority_at_v1.stream_id AND r.recorded_at<=_authority_at_v1.recorded_at
  UNION ALL
  SELECT command_body,recorded_order,
   jsonb_build_object('id',id,'start',i.effective_start,'end',i.effective_end,'action',action,
     'recorded_at',i.recorded_at,'target_role',target_role)
    FROM menuto_identity_source.issuers i WHERE i.root_id=_authority_at_v1.root_id
      AND i.stream_id=_authority_at_v1.stream_id AND i.recorded_at<=_authority_at_v1.recorded_at
  UNION ALL
  SELECT command_body,recorded_order,
   jsonb_build_object('id',id,'start',b.effective_start,'end',b.effective_end,'action',action,
     'recorded_at',b.recorded_at,'target_role',target_role)
    FROM menuto_identity_source.principal_bindings b WHERE b.root_id=_authority_at_v1.root_id
      AND b.stream_id=_authority_at_v1.stream_id AND b.recorded_at<=_authority_at_v1.recorded_at
  UNION ALL
  SELECT command_body,recorded_order,
   jsonb_build_object('id',id,'start',g.effective_start,'end',g.effective_end,'action',action,
     'recorded_at',g.recorded_at,'target_role',NULL::jsonb)
    FROM menuto_identity_source.operation_grants g WHERE g.root_id=_authority_at_v1.root_id
      AND g.stream_id=_authority_at_v1.stream_id AND g.recorded_at<=_authority_at_v1.recorded_at
 ) all_sources;
 IF jsonb_array_length(rows)>256 THEN RAISE EXCEPTION 'Identity stream limit' USING ERRCODE='54000'; END IF;
 FOR row IN SELECT value FROM jsonb_array_elements(rows) LOOP
  IF row->>'action'='REVOKE' THEN RETURN NULL; END IF;
  IF (row->>'start')::timestamptz<=recorded_at AND recorded_at<(row->>'end')::timestamptz THEN
   IF current_fact IS NOT NULL THEN RAISE EXCEPTION 'Identity ambiguous authority' USING ERRCODE='42501'; END IF;
   current_fact:=row;
  END IF;
 END LOOP;
 IF current_fact IS NULL THEN RETURN NULL; END IF;
 IF effective_start IS NULL THEN RETURN current_fact; END IF;
 FOR row IN SELECT value FROM jsonb_array_elements(rows) LOOP
  IF (row->>'start')::timestamptz<=cursor_at AND cursor_at<(row->>'end')::timestamptz THEN
   cursor_at:=(row->>'end')::timestamptz;
   IF cursor_at>=effective_end THEN RETURN current_fact; END IF;
  END IF;
 END LOOP;
 RETURN NULL;
END $f$;

CREATE FUNCTION menuto_identity_source._assert_lifecycle_v1(previous_fact jsonb,next_fact jsonb)
RETURNS void LANGUAGE plpgsql IMMUTABLE
SET search_path=pg_catalog,menuto_identity_source,pg_temp AS $f$
DECLARE cmd jsonb:=next_fact->'command'; oldcmd jsonb; ignored text[]; first_action text;
BEGIN
 ignored:=ARRAY['action','effective','idempotency_key','expected_revision','predecessor_id',
   'evidence_id','evidence_version','evidence_preimage'];
 IF previous_fact IS NULL THEN
  first_action:=CASE cmd->>'kind' WHEN 'ROOT' THEN 'INITIALIZE'
    WHEN 'OPERATION_GRANT' THEN 'GRANT' ELSE 'ENROLL' END;
  IF cmd->>'action'<>first_action OR cmd->'expected_revision'<>'0'::jsonb OR
      cmd->'predecessor_id'<>'null'::jsonb THEN
   RAISE EXCEPTION 'Identity initial CAS' USING ERRCODE='40001'; END IF;
 ELSE
  oldcmd:=previous_fact->'command';
  IF oldcmd->>'action'='REVOKE' OR cmd->>'action' NOT IN ('RENEW','REVOKE') OR
    cmd-ignored IS DISTINCT FROM oldcmd-ignored THEN
   RAISE EXCEPTION 'Identity immutable lifecycle' USING ERRCODE='42501'; END IF;
  IF (cmd->>'expected_revision')::bigint<>(previous_fact->>'revision')::bigint OR
     cmd->>'predecessor_id'<>previous_fact->>'fact_id' THEN
   RAISE EXCEPTION 'Identity CAS conflict' USING ERRCODE='40001'; END IF;
  IF cmd->>'action'<>'REVOKE' AND
     (next_fact->>'effective_start')::timestamptz < (previous_fact->>'effective_end')::timestamptz THEN
   RAISE EXCEPTION 'Identity overlapping renewal' USING ERRCODE='42501'; END IF;
 END IF;
 IF cmd->>'action'='REVOKE' THEN
  IF next_fact->'effective_start'<>'null'::jsonb OR next_fact->'effective_end'<>'null'::jsonb THEN
   RAISE EXCEPTION 'Identity revoke semantics' USING ERRCODE='22023'; END IF;
 ELSE
  IF (next_fact->>'effective_start')::timestamptz >= (next_fact->>'effective_end')::timestamptz OR
   (cmd->'effective'->>'mode'='SCHEDULED' AND
    (next_fact->>'effective_start')::timestamptz <= (next_fact->>'recorded_at')::timestamptz) THEN
   RAISE EXCEPTION 'Identity effective lifecycle' USING ERRCODE='22023'; END IF;
 END IF;
END $f$;

CREATE FUNCTION menuto_identity_source._reject_history_mutation_v1()
RETURNS trigger LANGUAGE plpgsql VOLATILE
SET search_path=pg_catalog,menuto_identity_source,pg_temp AS $f$
BEGIN
 IF TG_TABLE_NAME='frontiers' AND TG_OP IN ('INSERT','UPDATE') AND
   current_user='menuto_identity_source_owner' AND current_setting('role')='none' THEN
  IF TG_OP='UPDATE' AND (NEW.root_id<>OLD.root_id OR NEW.kind<>OLD.kind OR NEW.stream_id<>OLD.stream_id
    OR NEW.root_initial_fact_id<>OLD.root_initial_fact_id OR NEW.revision<>OLD.revision+1) THEN
   RAISE EXCEPTION 'Identity frontier transition denied' USING ERRCODE='42501'; END IF;
  RETURN NEW;
 END IF;
 IF TG_OP='INSERT' AND current_user='menuto_identity_source_owner' AND
    current_setting('role')='none' THEN RETURN NEW; END IF;
 RAISE EXCEPTION 'Identity history mutation denied' USING ERRCODE='42501';
END $f$;


CREATE FUNCTION menuto_identity_source._append_receipt_v1(kind text,fact jsonb,command jsonb)
RETURNS jsonb LANGUAGE plpgsql VOLATILE
SET search_path=pg_catalog,menuto_identity_source,pg_temp AS $f$
DECLARE root_uuid uuid:=(command->>'root_id')::uuid; stream_uuid uuid;
 actor jsonb; stamp timestamptz; lo timestamptz; hi timestamptz; root_initial record;
 previous_fact jsonb; target jsonb; membership_fact jsonb; issuer_fact jsonb;
 bound_initial menuto_identity_source.principal_bindings%ROWTYPE; receipt menuto_identity_source.command_receipts%ROWTYPE;
 target_oid oid; issuer_uuid uuid; first_id uuid; appended_id uuid:=gen_random_uuid();
 ordinal bigint; revision_no bigint; command_hash text; body jsonb; body_hash text;
 original_stream_kind text; directory jsonb; directory_hash text; answer jsonb;
 started_at timestamptz:=clock_timestamp(); previous_hash text; author_issuer_id uuid;
BEGIN
 IF fact IS NOT NULL OR kind IS DISTINCT FROM command->>'kind' OR kind NOT IN
   ('ROOT','ISSUER','BINDING','OPERATION_GRANT') THEN
  RAISE EXCEPTION 'Identity private append shape' USING ERRCODE='42501'; END IF;
 IF current_setting('transaction_isolation')<>'read committed' OR
    current_setting('transaction_read_only')<>'off' THEN
  RAISE EXCEPTION 'Identity writer transaction required' USING ERRCODE='25001'; END IF;
 stream_uuid:=CASE kind WHEN 'ROOT' THEN root_uuid
   WHEN 'ISSUER' THEN (command->>'issuer_id')::uuid
   WHEN 'BINDING' THEN (command->>'binding_id')::uuid ELSE (command->>'grant_id')::uuid END;
 PERFORM menuto_identity_source._lock_frontiers_v1(root_uuid,
   CASE WHEN kind IN ('BINDING','OPERATION_GRANT') THEN
     (command->>'binding_id')::uuid ELSE NULL END,
   CASE WHEN kind='OPERATION_GRANT' THEN stream_uuid ELSE NULL END);
 actor:=menuto_identity_source._session_fact_v1(
   CASE WHEN kind IN ('ROOT','ISSUER') THEN 'BOOTSTRAP' ELSE 'ISSUER' END);
 stamp:=(actor->>'observed_at')::timestamptz;
 IF command->>'action'='REVOKE' THEN lo:=NULL;hi:=NULL;
 ELSE
  lo:=CASE command->'effective'->>'mode' WHEN 'IMMEDIATE' THEN stamp
   ELSE (command->'effective'->>'start')::timestamptz END;
  hi:=(command->'effective'->>'end')::timestamptz;
  IF NOT (lo<hi) OR command->'effective'->>'mode'='SCHEDULED' AND lo<=stamp THEN
   RAISE EXCEPTION 'Identity invalid effective interval' USING ERRCODE='22023'; END IF;
 END IF;
 SELECT * INTO root_initial FROM menuto_identity_source.roots
  WHERE action='INITIALIZE';
 IF root_initial.id IS NOT NULL AND (root_initial.root_id<>root_uuid OR
    root_initial.database_oid<>(actor->>'database_oid')::bigint OR
    root_initial.database_name<>actor->>'database_name') THEN
  RAISE EXCEPTION 'Identity root/database mismatch' USING ERRCODE='42501'; END IF;
 IF NOT (kind='ROOT' AND command->>'action'='INITIALIZE') THEN
  IF root_initial.id IS NULL THEN
   RAISE EXCEPTION 'Identity root missing' USING ERRCODE='42501'; END IF;
  IF kind<>'ROOT' AND menuto_identity_source._authority_at_v1(root_uuid,root_uuid,stamp,lo,hi) IS NULL THEN
   RAISE EXCEPTION 'Identity root unavailable' USING ERRCODE='42501'; END IF;
 END IF;
 IF kind IN ('ISSUER','BINDING') THEN
  IF NOT EXISTS(SELECT FROM public.users WHERE id=(command->>'user_id')::uuid) THEN
   RAISE EXCEPTION 'Identity subject unavailable' USING ERRCODE='42501'; END IF;
  SELECT oid INTO target_oid FROM pg_roles WHERE rolname=command->>'role_name';
  IF target_oid IS NULL THEN RAISE EXCEPTION 'Identity role unavailable' USING ERRCODE='42501'; END IF;
  body:=menuto_identity_source._safe_role_v1(target_oid,
    CASE WHEN kind='ISSUER' THEN 'TARGET_ISSUER' ELSE 'TARGET_REQUESTER' END);
  SELECT value INTO target FROM jsonb_array_elements(body->'roles')
   WHERE (value->>'role_oid')::oid=target_oid;
 END IF;
 IF kind IN ('BINDING','OPERATION_GRANT') THEN
  issuer_uuid:=(command->>'issuer_id')::uuid;
  issuer_fact:=menuto_identity_source._authority_at_v1(root_uuid,issuer_uuid,stamp,lo,hi);
  IF issuer_fact IS NULL OR issuer_fact->'target_role'->>'role_oid'<>actor->>'login_role_oid'
    OR issuer_fact->'target_role'->>'role_name'<>actor->>'session_user'
    OR NOT EXISTS(SELECT FROM menuto_identity_source.issuers i JOIN public.users u ON
      u.id=i.issuer_user_id WHERE i.id=(issuer_fact->>'id')::uuid) THEN
   RAISE EXCEPTION 'Identity active issuer required' USING ERRCODE='42501'; END IF;
  author_issuer_id:=(issuer_fact->>'id')::uuid;
 END IF;
 IF kind='ISSUER' AND EXISTS(SELECT FROM menuto_identity_source.principal_bindings b
    WHERE b.root_id=root_uuid AND (b.user_id=(command->>'user_id')::uuid
      OR b.role_oid=target_oid OR b.role_name=command->>'role_name')) THEN
  RAISE EXCEPTION 'Identity issuer/requester separation' USING ERRCODE='42501'; END IF;
 IF kind='BINDING' THEN
  IF EXISTS(SELECT FROM menuto_identity_source.issuers i WHERE i.root_id=root_uuid AND
     (i.issuer_user_id=(command->>'user_id')::uuid OR i.issuer_role_oid=target_oid
      OR i.issuer_role_name=command->>'role_name')) THEN
   RAISE EXCEPTION 'Identity requester/issuer separation' USING ERRCODE='42501'; END IF;
  IF command->>'action'<>'ENROLL' AND NOT EXISTS(
   SELECT FROM menuto_identity_source.principal_bindings b WHERE b.root_id=root_uuid
    AND b.stream_id=stream_uuid AND b.action='ENROLL' AND b.enrolling_issuer_id=issuer_uuid
    AND b.user_id=(command->>'user_id')::uuid AND b.role_oid=target_oid
    AND b.role_name=command->>'role_name') THEN
   RAISE EXCEPTION 'Identity reserved binding mismatch' USING ERRCODE='42501'; END IF;
 END IF;
 IF kind='OPERATION_GRANT' THEN
  SELECT * INTO bound_initial FROM menuto_identity_source.principal_bindings b
    WHERE b.root_id=root_uuid AND b.stream_id=(command->>'binding_id')::uuid AND b.action='ENROLL';
  IF bound_initial.id IS NULL OR bound_initial.enrolling_issuer_id<>issuer_uuid OR
     menuto_identity_source._authority_at_v1(root_uuid,bound_initial.stream_id,stamp,lo,hi) IS NULL
     OR NOT EXISTS(SELECT FROM public.users WHERE id=bound_initial.user_id) THEN
   RAISE EXCEPTION 'Identity binding unavailable' USING ERRCODE='42501'; END IF;
  SELECT jsonb_build_object('version',1,'user_id',bound_initial.user_id,
   'household_id',(command->>'household_id')::uuid,'user_exists',true,
   'membership_id',m.id,'membership_user_id',m.user_id,'membership_household_id',m.household_id,
   'actor_member_id',m.member_id,'role',m.role,'actor_member_household_id',a.household_id,
   'target_member_id',t.id,'target_member_household_id',t.household_id,'target_member_exists',true)
   INTO membership_fact FROM public.memberships m
   JOIN public.households h ON h.id=m.household_id
   JOIN public.household_members a ON a.id=m.member_id AND a.household_id=m.household_id
   JOIN public.household_members t ON t.id=(command->>'tracked_member_id')::uuid
     AND t.household_id=m.household_id
   WHERE m.user_id=bound_initial.user_id AND m.household_id=(command->>'household_id')::uuid
    AND m.role IN ('OWNER','EDITOR') AND m.member_id IS NOT NULL;
  IF membership_fact IS NULL THEN
   RAISE EXCEPTION 'Identity exact Membership unavailable' USING ERRCODE='42501'; END IF;
 END IF;
 -- Current authentication and complete delegation coverage were checked after locks.
 -- Only now may an old identical receipt be returned.
 command_hash:=menuto_identity_source._canonical_hash_v1('identity.command.v1',command);
 SELECT * INTO receipt FROM menuto_identity_source.command_receipts r
  WHERE r.root_id=root_uuid AND r.actor_role_oid=(actor->>'login_role_oid')::bigint
   AND r.idempotency_key=(command->>'idempotency_key')::uuid;
 IF FOUND THEN
  IF receipt.command_fingerprint<>command_hash OR receipt.kind<>kind OR
     receipt.stream_id<>stream_uuid THEN
   RAISE EXCEPTION 'Identity idempotency conflict' USING ERRCODE='40001'; END IF;
  RETURN jsonb_build_object('version',1,'root_id',root_uuid,
   'fact_id',coalesce(receipt.root_fact_id,receipt.issuer_fact_id,
                     receipt.binding_fact_id,receipt.grant_fact_id),
   'stream_id',receipt.stream_id,'idempotency_key',receipt.idempotency_key,
   'author_role_oid',receipt.actor_role_oid,'revision',receipt.revision,
   'command_fingerprint',receipt.command_fingerprint,'fact_fingerprint',receipt.fact_fingerprint,
   'recorded_at',to_char(receipt.recorded_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
   'result','APPENDED');
 END IF;
 SELECT source_kind INTO original_stream_kind FROM (
   SELECT 'ROOT' source_kind FROM menuto_identity_source.roots WHERE root_id=root_uuid AND stream_id=stream_uuid
   UNION SELECT 'ISSUER' FROM menuto_identity_source.issuers WHERE root_id=root_uuid AND stream_id=stream_uuid
   UNION SELECT 'BINDING' FROM menuto_identity_source.principal_bindings WHERE root_id=root_uuid AND stream_id=stream_uuid
   UNION SELECT 'OPERATION_GRANT' FROM menuto_identity_source.operation_grants WHERE root_id=root_uuid AND stream_id=stream_uuid
 ) streams LIMIT 1;
 IF original_stream_kind IS NOT NULL AND original_stream_kind<>kind THEN
  RAISE EXCEPTION 'Identity cross-kind stream alias' USING ERRCODE='42501'; END IF;
 SELECT jsonb_build_object('command',command_body,'fact_id',id,'revision',revision,
   'effective_end',effective_end,'fact_fingerprint',fact_fingerprint) INTO previous_fact FROM (
  SELECT command_body,id,revision,effective_end,fact_fingerprint FROM menuto_identity_source.roots
   WHERE kind='ROOT' AND root_id=root_uuid AND stream_id=stream_uuid
  UNION ALL SELECT command_body,id,revision,effective_end,fact_fingerprint FROM menuto_identity_source.issuers
   WHERE kind='ISSUER' AND root_id=root_uuid AND stream_id=stream_uuid
  UNION ALL SELECT command_body,id,revision,effective_end,fact_fingerprint FROM menuto_identity_source.principal_bindings
   WHERE kind='BINDING' AND root_id=root_uuid AND stream_id=stream_uuid
  UNION ALL SELECT command_body,id,revision,effective_end,fact_fingerprint FROM menuto_identity_source.operation_grants
   WHERE kind='OPERATION_GRANT' AND root_id=root_uuid AND stream_id=stream_uuid
 ) prior ORDER BY revision DESC LIMIT 1;
 IF previous_fact IS NOT NULL AND (previous_fact->>'revision')::bigint>=256 THEN
  RAISE EXCEPTION 'Identity history limit' USING ERRCODE='54000'; END IF;
 IF previous_fact IS NULL AND kind='ROOT' AND root_initial.id IS NOT NULL THEN
  RAISE EXCEPTION 'Identity root already initialized' USING ERRCODE='42501'; END IF;
 IF previous_fact IS NULL AND kind='ISSUER' THEN
  IF (SELECT count(DISTINCT stream_id) FROM menuto_identity_source.issuers WHERE root_id=root_uuid)>=16
    OR EXISTS(SELECT FROM menuto_identity_source.issuers i WHERE i.root_id=root_uuid
       AND (i.issuer_role_oid=target_oid OR i.issuer_role_name=command->>'role_name')) THEN
   RAISE EXCEPTION 'Identity issuer reservation/limit' USING ERRCODE='42501'; END IF;
 END IF;
 IF previous_fact IS NULL AND kind='BINDING' AND EXISTS(
  SELECT FROM menuto_identity_source.principal_bindings b WHERE b.root_id=root_uuid AND
   (b.role_oid=target_oid OR b.role_name=command->>'role_name' OR
    (b.user_id=(command->>'user_id')::uuid AND b.action<>'REVOKE' AND b.effective_start<hi
      AND lo<b.effective_end AND NOT EXISTS(SELECT FROM menuto_identity_source.principal_bindings gone
        WHERE gone.root_id=root_uuid AND gone.stream_id=b.stream_id AND gone.action='REVOKE'))))
 THEN RAISE EXCEPTION 'Identity binding reservation' USING ERRCODE='42501'; END IF;
 IF previous_fact IS NULL AND kind='OPERATION_GRANT' AND EXISTS(
  SELECT FROM menuto_identity_source.operation_grants g WHERE g.root_id=root_uuid
   AND g.binding_id=bound_initial.stream_id AND g.household_id=(command->>'household_id')::uuid
   AND g.tracked_member_id=(command->>'tracked_member_id')::uuid
   AND g.action<>'REVOKE' AND g.effective_start<hi AND lo<g.effective_end
   AND NOT EXISTS(SELECT FROM menuto_identity_source.operation_grants gone WHERE gone.root_id=root_uuid
       AND gone.stream_id=g.stream_id AND gone.action='REVOKE'))
 THEN RAISE EXCEPTION 'Identity ambiguous operation grant' USING ERRCODE='42501'; END IF;
 revision_no:=coalesce((previous_fact->>'revision')::bigint,0)+1;
 ordinal:=nextval('menuto_identity_source.recorded_order');
 body:=jsonb_build_object('version',1,'fact_id',appended_id,'root_id',root_uuid,
   'stream_id',stream_uuid,'stream_kind',kind,'revision',revision_no,'recorded_order',ordinal,
   'recorded_at',to_char(stamp AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
   'previous_fact_id',previous_fact->'fact_id','previous_fact_fingerprint',previous_fact->'fact_fingerprint',
   'command',command,'command_fingerprint',command_hash,
   'effective_start',CASE WHEN lo IS NULL THEN NULL ELSE to_char(lo AT TIME ZONE 'UTC',
    'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') END,
   'effective_end',CASE WHEN hi IS NULL THEN NULL ELSE to_char(hi AT TIME ZONE 'UTC',
    'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') END,
   'author',actor,'author_issuer_fact_id',author_issuer_id,'target_role',target,
   'membership_at_issue',membership_fact);
 PERFORM menuto_identity_source._assert_lifecycle_v1(previous_fact,body);
 body_hash:=menuto_identity_source._canonical_hash_v1('identity.fact.v1',body);
 body:=body||jsonb_build_object('fact_fingerprint',body_hash);
 previous_hash:=previous_fact->>'fact_fingerprint';
 IF kind='ROOT' THEN
  INSERT INTO menuto_identity_source.roots (
   id,root_id,stream_id,revision,recorded_order,recorded_at,previous_id,previous_fingerprint,
   action,effective_start,effective_end,actor_database_oid,actor_role_oid,actor_database_name,
   actor_role_name,author_session,command_body,command_fingerprint,fact_fingerprint,idempotency_key,
   environment,database_oid,database_name,deployment_context_id)
  VALUES(appended_id,root_uuid,stream_uuid,revision_no,ordinal,stamp,
   (previous_fact->>'fact_id')::uuid,previous_hash,command->>'action',lo,hi,
   (actor->>'database_oid')::bigint,(actor->>'login_role_oid')::bigint,actor->>'database_name',
   actor->>'session_user',actor,command,command_hash,body_hash,(command->>'idempotency_key')::uuid,
   'TEST_ONLY',(actor->>'database_oid')::bigint,actor->>'database_name',root_uuid::text);
  first_id:=coalesce(root_initial.id,appended_id);
 ELSE first_id:=root_initial.id;
 END IF;
 IF kind='ISSUER' THEN
  INSERT INTO menuto_identity_source.issuers (
   id,root_id,stream_id,revision,recorded_order,recorded_at,previous_id,previous_fingerprint,
   action,effective_start,effective_end,actor_database_oid,actor_role_oid,actor_database_name,
   actor_role_name,author_session,command_body,command_fingerprint,fact_fingerprint,idempotency_key,
   environment,root_initial_fact_id,issuer_user_id,issuer_role_oid,issuer_role_name,target_role,capability)
  VALUES(appended_id,root_uuid,stream_uuid,revision_no,ordinal,stamp,
   (previous_fact->>'fact_id')::uuid,previous_hash,command->>'action',lo,hi,
   (actor->>'database_oid')::bigint,(actor->>'login_role_oid')::bigint,actor->>'database_name',
   actor->>'session_user',actor,command,command_hash,body_hash,(command->>'idempotency_key')::uuid,
   'TEST_ONLY',first_id,(command->>'user_id')::uuid,target_oid,command->>'role_name',
   target,'BINDINGS_AND_SCOPE_GRANTS');
 ELSIF kind='BINDING' THEN
  INSERT INTO menuto_identity_source.principal_bindings (
   id,root_id,stream_id,revision,recorded_order,recorded_at,previous_id,previous_fingerprint,
   action,effective_start,effective_end,actor_database_oid,actor_role_oid,actor_database_name,
   actor_role_name,author_session,command_body,command_fingerprint,fact_fingerprint,idempotency_key,
   environment,root_initial_fact_id,enrolling_issuer_id,author_issuer_fact_id,user_id,role_oid,role_name,target_role)
  VALUES(appended_id,root_uuid,stream_uuid,revision_no,ordinal,stamp,
   (previous_fact->>'fact_id')::uuid,previous_hash,command->>'action',lo,hi,
   (actor->>'database_oid')::bigint,(actor->>'login_role_oid')::bigint,actor->>'database_name',
   actor->>'session_user',actor,command,command_hash,body_hash,(command->>'idempotency_key')::uuid,
   'TEST_ONLY',first_id,issuer_uuid,author_issuer_id,(command->>'user_id')::uuid,target_oid,
   command->>'role_name',target);
 ELSIF kind='OPERATION_GRANT' THEN
  INSERT INTO menuto_identity_source.operation_grants (
   id,root_id,stream_id,revision,recorded_order,recorded_at,previous_id,previous_fingerprint,
   action,effective_start,effective_end,actor_database_oid,actor_role_oid,actor_database_name,
   actor_role_name,author_session,command_body,command_fingerprint,fact_fingerprint,idempotency_key,
   environment,root_initial_fact_id,binding_initial_fact_id,binding_id,author_issuer_fact_id,
   operation,household_id,tracked_member_id,membership_id,actor_member_id,membership_role,membership_at_issue)
  VALUES(appended_id,root_uuid,stream_uuid,revision_no,ordinal,stamp,
   (previous_fact->>'fact_id')::uuid,previous_hash,command->>'action',lo,hi,
   (actor->>'database_oid')::bigint,(actor->>'login_role_oid')::bigint,actor->>'database_name',
   actor->>'session_user',actor,command,command_hash,body_hash,(command->>'idempotency_key')::uuid,
   'TEST_ONLY',first_id,bound_initial.id,bound_initial.stream_id,author_issuer_id,
   'CAPTURE_EXPLICIT_PLAN_INTENT',(command->>'household_id')::uuid,
   (command->>'tracked_member_id')::uuid,(membership_fact->>'membership_id')::uuid,
   (membership_fact->>'actor_member_id')::uuid,membership_fact->>'role',membership_fact);
 END IF;
 IF kind='ISSUER' THEN
  SELECT coalesce(jsonb_agg(jsonb_build_array(stream_id,revision,id,fact_fingerprint,count_rows)
      ORDER BY stream_id),'[]'::jsonb) INTO directory FROM (
    SELECT DISTINCT ON (stream_id) stream_id,revision,id,fact_fingerprint,
     count(*) OVER(PARTITION BY stream_id) count_rows
    FROM menuto_identity_source.issuers WHERE root_id=root_uuid ORDER BY stream_id,revision DESC
   ) heads;
  directory_hash:=menuto_identity_source._canonical_hash_v1('identity.source.v1',
    jsonb_build_object('issuer_directory',directory));
  UPDATE menuto_identity_source.frontiers SET revision=revision+1,fact_count=fact_count+1,
    head_id=appended_id,head_fingerprint=body_hash,directory_entries=directory,
    directory_fingerprint=directory_hash
   WHERE root_id=root_uuid AND frontiers.kind='ISSUER_DIRECTORY' AND stream_id=root_uuid;
 ELSE
  INSERT INTO menuto_identity_source.frontiers (root_id,kind,stream_id,root_initial_fact_id,
   revision,fact_count,head_id,head_fingerprint,directory_entries,directory_fingerprint)
  VALUES(root_uuid,kind,stream_uuid,first_id,revision_no,revision_no,appended_id,body_hash,'[]',NULL)
  ON CONFLICT ON CONSTRAINT frontiers_pkey DO UPDATE SET revision=EXCLUDED.revision,
    fact_count=EXCLUDED.fact_count,head_id=EXCLUDED.head_id,head_fingerprint=EXCLUDED.head_fingerprint;
 END IF;
 IF kind='ROOT' AND previous_fact IS NULL THEN
  INSERT INTO menuto_identity_source.frontiers VALUES(root_uuid,'ISSUER_DIRECTORY',root_uuid,first_id,
   0,0,NULL,NULL,'[]',menuto_identity_source._canonical_hash_v1('identity.source.v1',
    '{"issuer_directory":[]}'::jsonb));
 END IF;
 INSERT INTO menuto_identity_source.command_receipts VALUES (
  gen_random_uuid(),root_uuid,(actor->>'login_role_oid')::bigint,
  (command->>'idempotency_key')::uuid,kind,stream_uuid,revision_no,stamp,command_hash,body_hash,
  CASE WHEN kind='ROOT' THEN appended_id ELSE NULL END,
  CASE WHEN kind='ISSUER' THEN appended_id ELSE NULL END,
  CASE WHEN kind='BINDING' THEN appended_id ELSE NULL END,
  CASE WHEN kind='OPERATION_GRANT' THEN appended_id ELSE NULL END);
 IF clock_timestamp()-started_at>interval '5 seconds' THEN
  RAISE EXCEPTION 'Identity operation budget exceeded' USING ERRCODE='57014'; END IF;
 RETURN jsonb_build_object('version',1,'root_id',root_uuid,'fact_id',appended_id,
   'stream_id',stream_uuid,'idempotency_key',(command->>'idempotency_key')::uuid,
   'author_role_oid',(actor->>'login_role_oid')::bigint,'revision',revision_no,
   'command_fingerprint',command_hash,'fact_fingerprint',body_hash,
   'recorded_at',to_char(stamp AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
   'result','APPENDED');
END $f$;


CREATE FUNCTION menuto_identity_source._capture_sources_v1(request_binding jsonb,observed_session jsonb)
RETURNS jsonb LANGUAGE plpgsql VOLATILE
SET search_path=pg_catalog,menuto_identity_source,pg_temp AS $f$
DECLARE initial_root menuto_identity_source.roots%ROWTYPE;
 initial_binding menuto_identity_source.principal_bindings%ROWTYPE;
 root_uuid uuid; binding_uuid uuid; issuer_uuid uuid; raw_histories jsonb; all_facts jsonb;
 root_history jsonb; issuer_history jsonb; binding_history jsonb; grant_history jsonb;
 frontier_rows jsonb; frame jsonb; source jsonb; membership_fact jsonb; grant_at record;
 after_session jsonb; at_time timestamptz; started_at timestamptz:=statement_timestamp();
 finished_at timestamptz; reason text:='SOURCE_AVAILABLE'; candidate_count integer:=0;
 witness_allowed boolean; absences jsonb:='[]'::jsonb; total_bytes bigint; row_count bigint;
BEGIN
 IF current_setting('transaction_read_only')<>'on' OR
    current_setting('transaction_isolation') NOT IN ('repeatable read','serializable') THEN
  RAISE EXCEPTION 'Identity clean read-only snapshot required' USING ERRCODE='25001'; END IF;
 SELECT * INTO initial_root FROM menuto_identity_source.roots WHERE action='INITIALIZE';
 IF initial_root.id IS NULL OR initial_root.database_oid<>(observed_session->>'database_oid')::bigint
   OR initial_root.database_name<>observed_session->>'database_name' THEN
  RAISE EXCEPTION 'Identity selected root unavailable' USING ERRCODE='42501'; END IF;
 root_uuid:=initial_root.root_id;
 SELECT * INTO initial_binding FROM menuto_identity_source.principal_bindings b
  WHERE b.root_id=root_uuid AND b.action='ENROLL'
    AND b.role_oid=(observed_session->>'login_role_oid')::bigint
    AND b.role_name=observed_session->>'session_user';
 IF initial_binding.id IS NULL OR initial_binding.user_id<>(request_binding->>'actor_user_id')::uuid THEN
  RAISE EXCEPTION 'Identity bound principal unavailable' USING ERRCODE='42501'; END IF;
 binding_uuid:=initial_binding.stream_id;issuer_uuid:=initial_binding.enrolling_issuer_id;
 -- Estimate selected immutable history before materializing its retained JSON.
 SELECT count(*),coalesce(sum(octet_length(author_session::text)+octet_length(command_body::text)+2048),0)
  INTO row_count,total_bytes FROM (
   SELECT author_session,command_body FROM menuto_identity_source.roots r WHERE r.root_id=root_uuid
   UNION ALL SELECT author_session,command_body FROM menuto_identity_source.issuers i WHERE i.root_id=root_uuid
   UNION ALL SELECT author_session,command_body FROM menuto_identity_source.principal_bindings b
    WHERE b.root_id=root_uuid AND b.stream_id=binding_uuid
   UNION ALL SELECT author_session,command_body FROM menuto_identity_source.operation_grants g
    WHERE g.root_id=root_uuid AND g.binding_id=binding_uuid
      AND g.operation='CAPTURE_EXPLICIT_PLAN_INTENT'
      AND g.household_id=(request_binding->>'household_id')::uuid
      AND g.tracked_member_id=(request_binding->>'tracked_member_id')::uuid
  ) selected;
 IF row_count>2048 OR total_bytes+2*octet_length(observed_session::text)+
    octet_length(request_binding::text)>8388608 THEN
  RAISE EXCEPTION 'Identity capture resource limit' USING ERRCODE='54000'; END IF;
 WITH selected(kind,row) AS (
  SELECT 'ROOT',to_jsonb(r) FROM menuto_identity_source.roots r WHERE r.root_id=root_uuid
  UNION ALL SELECT 'ISSUER',to_jsonb(i) FROM menuto_identity_source.issuers i WHERE i.root_id=root_uuid
  UNION ALL SELECT 'BINDING',to_jsonb(b) FROM menuto_identity_source.principal_bindings b
    WHERE b.root_id=root_uuid AND b.stream_id=binding_uuid
  UNION ALL SELECT 'OPERATION_GRANT',to_jsonb(g) FROM menuto_identity_source.operation_grants g
    WHERE g.root_id=root_uuid AND g.binding_id=binding_uuid
      AND g.operation='CAPTURE_EXPLICIT_PLAN_INTENT'
      AND g.household_id=(request_binding->>'household_id')::uuid
      AND g.tracked_member_id=(request_binding->>'tracked_member_id')::uuid
 ), facts AS (
  SELECT jsonb_build_object('version',1,'fact_id',row->'id','root_id',row->'root_id',
   'stream_id',row->'stream_id','stream_kind',kind,'revision',row->'revision',
   'recorded_order',row->'recorded_order',
   'recorded_at',to_char((row->>'recorded_at')::timestamptz AT TIME ZONE 'UTC',
      'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
   'previous_fact_id',row->'previous_id','previous_fact_fingerprint',row->'previous_fingerprint',
   'command',row->'command_body','command_fingerprint',row->'command_fingerprint',
   'effective_start',CASE WHEN row->'effective_start'='null'::jsonb THEN NULL ELSE
     to_char((row->>'effective_start')::timestamptz AT TIME ZONE 'UTC',
      'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') END,
   'effective_end',CASE WHEN row->'effective_end'='null'::jsonb THEN NULL ELSE
     to_char((row->>'effective_end')::timestamptz AT TIME ZONE 'UTC',
      'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') END,
   'author',row->'author_session','author_issuer_fact_id',row->'author_issuer_fact_id',
   'target_role',row->'target_role','membership_at_issue',row->'membership_at_issue',
   'fact_fingerprint',row->'fact_fingerprint') fact FROM selected
 )
 SELECT coalesce(jsonb_agg(fact ORDER BY (fact->>'recorded_order')::bigint),'[]'::jsonb)
  INTO all_facts FROM facts;
 SELECT coalesce(jsonb_agg(value ORDER BY (value->>'revision')::bigint),'[]'::jsonb)
  INTO root_history FROM jsonb_array_elements(all_facts) WHERE value->>'stream_kind'='ROOT';
 SELECT coalesce(jsonb_agg(value ORDER BY (value->>'recorded_order')::bigint),'[]'::jsonb)
  INTO issuer_history FROM jsonb_array_elements(all_facts) WHERE value->>'stream_kind'='ISSUER';
 SELECT coalesce(jsonb_agg(value ORDER BY (value->>'revision')::bigint),'[]'::jsonb)
  INTO binding_history FROM jsonb_array_elements(all_facts) WHERE value->>'stream_kind'='BINDING';
 SELECT coalesce(jsonb_agg(value ORDER BY (value->>'recorded_order')::bigint),'[]'::jsonb)
  INTO grant_history FROM jsonb_array_elements(all_facts) WHERE value->>'stream_kind'='OPERATION_GRANT';
 SELECT coalesce(jsonb_agg(jsonb_build_object(
  'version',1,'root_id',f.root_id,'stream_id',f.stream_id,'kind',f.kind,
  'revision',f.revision,'head_id',f.head_id,'head_fingerprint',f.head_fingerprint,
  'fact_count',f.fact_count,'directory_fingerprint',f.directory_fingerprint,
  'directory_entries',f.directory_entries) ORDER BY f.kind,f.stream_id),'[]'::jsonb)
  INTO frontier_rows FROM menuto_identity_source.frontiers f
  WHERE f.root_id=root_uuid AND (f.kind='ROOT' OR f.kind='ISSUER_DIRECTORY'
    OR f.kind='BINDING' AND f.stream_id=binding_uuid
    OR f.kind='OPERATION_GRANT' AND f.stream_id IN (
      SELECT DISTINCT (value->>'stream_id')::uuid FROM jsonb_array_elements(grant_history)));
 IF grant_history='[]'::jsonb THEN
  frontier_rows:=frontier_rows||jsonb_build_array(jsonb_build_object('version',1,'root_id',root_uuid,
   'stream_id',(request_binding->>'tracked_member_id')::uuid,'kind','OPERATION_GRANT',
   'revision',0,'fact_count',0,'head_id',NULL,'head_fingerprint',NULL,
   'directory_entries','[]'::jsonb,'directory_fingerprint',NULL));
  absences:=jsonb_build_array(jsonb_build_array('OPERATION_GRANT',request_binding->>'tracked_member_id'));
 END IF;
 at_time:=clock_timestamp();
 IF menuto_identity_source._authority_at_v1(root_uuid,root_uuid,at_time,NULL,NULL) IS NULL THEN
  reason:=CASE WHEN EXISTS(SELECT FROM menuto_identity_source.roots r WHERE r.root_id=root_uuid
    AND r.action='REVOKE') THEN 'ROOT_REVOKED' ELSE 'ROOT_EXPIRED' END;
 ELSIF menuto_identity_source._authority_at_v1(root_uuid,issuer_uuid,at_time,NULL,NULL) IS NULL THEN
  reason:=CASE WHEN EXISTS(SELECT FROM menuto_identity_source.issuers i WHERE i.root_id=root_uuid
    AND i.stream_id=issuer_uuid AND i.action='REVOKE') THEN 'ISSUER_REVOKED' ELSE 'ISSUER_EXPIRED' END;
 ELSIF menuto_identity_source._authority_at_v1(root_uuid,binding_uuid,at_time,NULL,NULL) IS NULL THEN
  reason:=CASE WHEN EXISTS(SELECT FROM menuto_identity_source.principal_bindings b
    WHERE b.root_id=root_uuid AND b.stream_id=binding_uuid AND b.action='REVOKE')
    THEN 'BINDING_REVOKED' ELSE 'BINDING_EXPIRED' END;
 END IF;
 SELECT count(*) INTO candidate_count FROM (
  SELECT DISTINCT ON (g.stream_id) g.stream_id,g.membership_at_issue
   FROM menuto_identity_source.operation_grants g
   WHERE g.root_id=root_uuid AND g.binding_id=binding_uuid
    AND g.household_id=(request_binding->>'household_id')::uuid
    AND g.tracked_member_id=(request_binding->>'tracked_member_id')::uuid
    AND g.operation='CAPTURE_EXPLICIT_PLAN_INTENT'
    AND g.action<>'REVOKE' AND g.effective_start<=at_time AND at_time<g.effective_end
    AND NOT EXISTS(SELECT FROM menuto_identity_source.operation_grants gone
      WHERE gone.root_id=root_uuid AND gone.stream_id=g.stream_id AND gone.action='REVOKE')
   ORDER BY g.stream_id,g.revision DESC
 ) active_grants;
 IF candidate_count>1 THEN RAISE EXCEPTION 'Identity ambiguous grants' USING ERRCODE='42501'; END IF;
 IF reason='SOURCE_AVAILABLE' AND candidate_count=0 THEN
  reason:=CASE WHEN EXISTS(SELECT FROM jsonb_array_elements(grant_history) item
      WHERE item->'command'->>'action'='REVOKE') THEN 'GRANT_REVOKED'
    WHEN grant_history<>'[]'::jsonb THEN 'GRANT_EXPIRED' ELSE 'GRANT_ABSENT' END;
 END IF;
 IF reason='SOURCE_AVAILABLE' THEN
  SELECT g.* INTO STRICT grant_at FROM menuto_identity_source.operation_grants g
    WHERE g.root_id=root_uuid AND g.binding_id=binding_uuid
     AND g.household_id=(request_binding->>'household_id')::uuid
     AND g.tracked_member_id=(request_binding->>'tracked_member_id')::uuid
     AND g.operation='CAPTURE_EXPLICIT_PLAN_INTENT' AND g.action<>'REVOKE'
     AND g.effective_start<=at_time AND at_time<g.effective_end
     AND NOT EXISTS(SELECT FROM menuto_identity_source.operation_grants gone
       WHERE gone.root_id=root_uuid AND gone.stream_id=g.stream_id AND gone.action='REVOKE')
     ORDER BY g.revision DESC LIMIT 1;
  SELECT jsonb_build_object('version',1,'user_id',initial_binding.user_id,
    'household_id',(request_binding->>'household_id')::uuid,
    'user_exists',EXISTS(SELECT FROM public.users WHERE id=initial_binding.user_id),
    'membership_id',m.id,'membership_user_id',m.user_id,'membership_household_id',m.household_id,
    'actor_member_id',m.member_id,'role',m.role,'actor_member_household_id',a.household_id,
    'target_member_id',t.id,'target_member_household_id',t.household_id,
    'target_member_exists',CASE WHEN t.id IS NULL THEN NULL ELSE true END)
    INTO membership_fact FROM (SELECT 1) anchor
    LEFT JOIN public.memberships m ON m.user_id=initial_binding.user_id
      AND m.household_id=(request_binding->>'household_id')::uuid
    LEFT JOIN public.household_members a ON a.id=m.member_id AND a.household_id=m.household_id
    LEFT JOIN public.household_members t ON t.id=(request_binding->>'tracked_member_id')::uuid
      AND t.household_id=m.household_id AND m.role IN ('OWNER','EDITOR')
      AND m.member_id IS NOT NULL AND a.id IS NOT NULL
      AND m.id=grant_at.membership_id AND m.member_id=grant_at.actor_member_id
      AND m.role=grant_at.membership_role;
  IF membership_fact->>'user_exists'<>'true' OR membership_fact->>'target_member_exists' IS DISTINCT FROM 'true'
     OR membership_fact->>'membership_id' IS DISTINCT FROM grant_at.membership_id::text
     OR membership_fact->>'actor_member_id' IS DISTINCT FROM grant_at.actor_member_id::text
     OR membership_fact->>'role' IS DISTINCT FROM grant_at.membership_role THEN
   reason:='AUTHORIZATION_DENIED';
   membership_fact:=membership_fact||'{"target_member_id":null,"target_member_household_id":null,"target_member_exists":null}'::jsonb;
  END IF;
  IF membership_fact->'membership_id'='null'::jsonb THEN
   absences:=absences||jsonb_build_array(jsonb_build_array('MEMBERSHIP',initial_binding.user_id));
  END IF;
 END IF;
 after_session:=menuto_identity_source._session_fact_v1('REQUESTER');
 IF observed_session-'observed_at' IS DISTINCT FROM after_session-'observed_at' THEN
  RAISE EXCEPTION 'Identity catalog changed' USING ERRCODE='40001'; END IF;
 -- Effective state is checked again at the end; crossing any availability boundary is all-or-error.
 IF (menuto_identity_source._authority_at_v1(root_uuid,root_uuid,
      (after_session->>'observed_at')::timestamptz,NULL,NULL) IS NULL) IS DISTINCT FROM
    (menuto_identity_source._authority_at_v1(root_uuid,root_uuid,at_time,NULL,NULL) IS NULL)
   OR (menuto_identity_source._authority_at_v1(root_uuid,issuer_uuid,
      (after_session->>'observed_at')::timestamptz,NULL,NULL) IS NULL) IS DISTINCT FROM
    (menuto_identity_source._authority_at_v1(root_uuid,issuer_uuid,at_time,NULL,NULL) IS NULL)
   OR (menuto_identity_source._authority_at_v1(root_uuid,binding_uuid,
      (after_session->>'observed_at')::timestamptz,NULL,NULL) IS NULL) IS DISTINCT FROM
    (menuto_identity_source._authority_at_v1(root_uuid,binding_uuid,at_time,NULL,NULL) IS NULL) THEN
  RAISE EXCEPTION 'Identity effective cut changed' USING ERRCODE='40001'; END IF;
 IF EXISTS(SELECT FROM menuto_identity_source.operation_grants g
   WHERE g.root_id=root_uuid AND g.binding_id=binding_uuid
     AND g.household_id=(request_binding->>'household_id')::uuid
     AND g.tracked_member_id=(request_binding->>'tracked_member_id')::uuid
     AND (menuto_identity_source._authority_at_v1(root_uuid,g.stream_id,
           (after_session->>'observed_at')::timestamptz,NULL,NULL) IS NULL) IS DISTINCT FROM
         (menuto_identity_source._authority_at_v1(root_uuid,g.stream_id,at_time,NULL,NULL) IS NULL)) THEN
  RAISE EXCEPTION 'Identity grant effective cut changed' USING ERRCODE='40001'; END IF;
 finished_at:=clock_timestamp();
 IF finished_at-started_at>interval '5 seconds' THEN
  RAISE EXCEPTION 'Identity capture operation budget' USING ERRCODE='57014'; END IF;
 frame:=jsonb_build_object('version',1,'root_id',root_uuid,
  'deployment_context_id',initial_root.deployment_context_id,
  'started_at',to_char(started_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'finished_at',to_char(finished_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'transaction_started_at',to_char(transaction_timestamp() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'snapshot_id',pg_current_snapshot()::text,'session_start',observed_session,'session_end',after_session,
  'frontiers',frontier_rows,'total_fact_count',row_count,
  'environment','TEST_ONLY','transport','UNVERIFIED_TRANSPORT');
 SELECT coalesce(jsonb_agg(value ORDER BY value->>0,value->>1),'[]'::jsonb) INTO absences
  FROM jsonb_array_elements(absences);
 source:=jsonb_build_object('version',1,'binding',request_binding,'frame',frame,
  'root_history',root_history,'issuer_history',issuer_history,'binding_history',binding_history,
  'grant_history',grant_history,'membership',membership_fact,'absences',absences,
  'outcome',CASE WHEN reason='SOURCE_AVAILABLE' THEN 'AVAILABLE_AT_RETAINED_CUT' ELSE 'UNAVAILABLE' END,
  'reason',reason);
 IF octet_length(source::text)>8388608 OR (SELECT count(*) FROM (
   SELECT value FROM jsonb_path_query(source,'$.**') value LIMIT 200001) bounded)>200000 THEN
  RAISE EXCEPTION 'Identity retained source budget' USING ERRCODE='54000'; END IF;
 RETURN source||jsonb_build_object('source_fingerprint',
   menuto_identity_source._canonical_hash_v1('identity.source.v1',source));
END $f$;

CREATE FUNCTION menuto_identity_source.bootstrap_root(command_text text)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_identity_source,pg_temp
SET lock_timeout='1s' AS $f$
BEGIN RETURN menuto_identity_source._append_receipt_v1(
 'ROOT',NULL,menuto_identity_source._parse_command_v1(command_text,'ROOT')); END $f$;

CREATE FUNCTION menuto_identity_source.change_issuer(command_text text)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_identity_source,pg_temp
SET lock_timeout='1s' AS $f$
BEGIN RETURN menuto_identity_source._append_receipt_v1(
 'ISSUER',NULL,menuto_identity_source._parse_command_v1(command_text,'ISSUER')); END $f$;

CREATE FUNCTION menuto_identity_source.change_binding(command_text text)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_identity_source,pg_temp
SET lock_timeout='1s' AS $f$
BEGIN RETURN menuto_identity_source._append_receipt_v1(
 'BINDING',NULL,menuto_identity_source._parse_command_v1(command_text,'BINDING')); END $f$;

CREATE FUNCTION menuto_identity_source.change_operation_grant(command_text text)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_identity_source,pg_temp
SET lock_timeout='1s' AS $f$
BEGIN RETURN menuto_identity_source._append_receipt_v1(
 'OPERATION_GRANT',NULL,menuto_identity_source._parse_command_v1(command_text,'OPERATION_GRANT')); END $f$;

CREATE FUNCTION menuto_identity_source.capture_request_source(request_binding_text text)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,menuto_identity_source,pg_temp
SET lock_timeout='1s' AS $f$
DECLARE request jsonb; session jsonb;
BEGIN
 request:=menuto_identity_source._parse_command_v1(request_binding_text,'REQUEST');
 session:=menuto_identity_source._session_fact_v1('REQUESTER');
 RETURN menuto_identity_source._capture_sources_v1(request,session);
EXCEPTION WHEN no_data_found OR too_many_rows THEN
 -- A native login/catalog identity may change while an earlier MVCC row remains retained.
 -- Never expose a prefix or let a missing descriptor fall back to another principal.
 RAISE EXCEPTION 'Identity catalog identity changed' USING ERRCODE='40001';
END $f$;

"""


def upgrade():
    db = op.get_bind()
    if db.execute(text("SHOW server_version_num")).scalar_one() != "180004":
        raise RuntimeError("Identity native manifest requires PostgreSQL 18.4")
    native = db.execute(text(NATIVE_CATALOG_SQL)).mappings().all()
    if (
        len(native) != 10
        or {row["name"] for row in native} != set(NATIVE_SSLINFO_PINS["public"])
        or any(not row["valid"] for row in native)
    ):
        raise RuntimeError("Identity sslinfo catalog trust root mismatch")
    namespace = native[0]["namespace"]
    if any(row["namespace"] != namespace for row in native):
        raise RuntimeError("Identity sslinfo namespace mismatch")
    tls_native = next(row for row in native if row["name"] == "ssl_is_used")
    # Explicit raw/direct ACL ledger: PUBLIC effective entitlement is not an Identity grant.
    tls_before = {}
    for kind, statement in (
        (
            "usage",
            "SELECT EXISTS(SELECT FROM pg_namespace n, LATERAL aclexplode(n.nspacl) a WHERE n.nspname=:ns AND a.grantee=(SELECT oid FROM pg_roles WHERE rolname='menuto_identity_source_owner') AND a.privilege_type='USAGE')",
        ),
        (
            "execute",
            "SELECT EXISTS(SELECT FROM pg_proc p, LATERAL aclexplode(p.proacl) a WHERE p.oid=:oid AND a.grantee=(SELECT oid FROM pg_roles WHERE rolname='menuto_identity_source_owner') AND a.privilege_type='EXECUTE')",
        ),
    ):
        tls_before[kind] = db.execute(
            text(statement), {"ns": namespace, "oid": tls_native["function_oid"]}
        ).scalar_one()
    if db.execute(
        text("""SELECT EXISTS(SELECT FROM pg_namespace n,LATERAL aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) a
       WHERE n.oid=:ns AND a.privilege_type='CREATE' AND a.grantee NOT IN(n.nspowner,:owner))"""),
        {"ns": tls_native["namespace_oid"], "owner": tls_native["owner_oid"]},
    ).scalar_one():
        raise RuntimeError("Identity native schema CREATE privilege")
    historical_native_readers = (
        db.execute(
            text(
                "SELECT oid::bigint FROM pg_roles WHERE rolname IN ('menuto_prior_owner','menuto_hierarchy_owner','menuto_nutrition_owner','menuto_nutrition_synthesis_owner')"
            )
        )
        .scalars()
        .all()
    )
    if len(historical_native_readers) != 4:
        raise RuntimeError("Identity native reader role inventory")
    existing_identity_owner = db.execute(
        text("SELECT oid::bigint FROM pg_roles WHERE rolname='menuto_identity_source_owner'")
    ).scalar_one_or_none()
    for row in native:
        owner = row["owner_oid"]
        expected = [[owner, owner, "EXECUTE", False]]
        if namespace == "public":
            expected.append([0, owner, "EXECUTE", False])
        if row["name"] == "ssl_is_used":
            expected += [[oid, owner, "EXECUTE", False] for oid in historical_native_readers]
            if tls_before["execute"]:
                expected.append([existing_identity_owner, owner, "EXECUTE", False])
        if row["acl"] != sorted(expected):
            raise RuntimeError("Identity native ACL not reviewed baseline")
    created = []
    for role in ROLES:
        row = (
            db.execute(
                text("""SELECT oid,rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolreplication,
          rolbypassrls,shobj_description(oid,'pg_authid') AS tag FROM pg_roles WHERE rolname=:name"""),
                {"name": role},
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            op.execute(
                f"CREATE ROLE {role} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS"
            )
            op.execute(f"COMMENT ON ROLE {role} IS 'menuto.identity.infrastructure.v1'")
            created.append(role)
        elif (
            any(
                row[key]
                for key in (
                    "rolcanlogin",
                    "rolsuper",
                    "rolcreatedb",
                    "rolcreaterole",
                    "rolreplication",
                    "rolbypassrls",
                )
            )
            or row["tag"] != "menuto.identity.infrastructure.v1"
        ):
            raise RuntimeError("Identity unsafe infrastructure role collision")
        if db.execute(
            text(
                "SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=:name)"
            ),
            {"name": role},
        ).scalar_one():
            raise RuntimeError("Identity infrastructure role inheritance")
    op.execute("CREATE SCHEMA menuto_identity_source AUTHORIZATION menuto_identity_source_owner")
    op.execute("REVOKE ALL ON SCHEMA menuto_identity_source FROM PUBLIC")
    op.execute(
        "COMMENT ON SCHEMA menuto_identity_source IS '"
        + json.dumps(
            {
                "migration": "0018",
                "created_roles": created,
                "tls_namespace": namespace,
                "tls_before": tls_before,
            },
            sort_keys=True,
        )
        + "'"
    )
    op.execute(TABLE_SQL)
    for table in TABLES:
        op.execute(
            f"ALTER TABLE menuto_identity_source.{table} OWNER TO menuto_identity_source_owner"
        )
    op.execute(
        "ALTER SEQUENCE menuto_identity_source.recorded_order OWNER TO menuto_identity_source_owner"
    )
    op.execute(
        "REVOKE ALL ON ALL TABLES IN SCHEMA menuto_identity_source FROM PUBLIC,menuto_identity_bootstrap,menuto_identity_issuer,menuto_identity_requester"
    )
    op.execute(
        "REVOKE ALL ON ALL SEQUENCES IN SCHEMA menuto_identity_source FROM PUBLIC,menuto_identity_bootstrap,menuto_identity_issuer,menuto_identity_requester"
    )
    op.execute(
        "GRANT SELECT ON public.users,public.households,public.household_members,public.memberships TO menuto_identity_source_owner"
    )
    # Exactly one catalog-proved namespace, two previously authorized TLS grants.
    op.execute(f"GRANT USAGE ON SCHEMA {namespace} TO menuto_identity_source_owner")
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {namespace}.ssl_is_used() TO menuto_identity_source_owner"
    )
    native_after = db.execute(text(NATIVE_CATALOG_SQL)).mappings().all()
    if [
        (
            x["name"],
            x["function_oid"],
            x["namespace_oid"],
            x["extension_oid"],
            x["owner_oid"],
            x["definition"],
            x["valid"],
        )
        for x in native_after
    ] != [
        (
            x["name"],
            x["function_oid"],
            x["namespace_oid"],
            x["extension_oid"],
            x["owner_oid"],
            x["definition"],
            x["valid"],
        )
        for x in native
    ]:
        raise RuntimeError("Identity sslinfo installation catalog drift")
    body = FUNCTION_SQL.replace("__NATIVE_CATALOG_SQL__", NATIVE_CATALOG_SQL)
    body = body.replace("__TLS_NAMESPACE__", namespace)
    for key in ("extension_oid", "function_oid", "namespace_oid", "owner_oid"):
        body = body.replace("__TLS_" + key.upper() + "__", str(tls_native[key]))
    body = body.replace(
        "__NATIVE_PINS__", json.dumps(NATIVE_SSLINFO_PINS[namespace], sort_keys=True)
    )
    body = body.replace(
        "__NATIVE_OIDS__",
        json.dumps({x["name"]: x["function_oid"] for x in native_after}, sort_keys=True),
    )
    body = body.replace(
        "__NATIVE_RAW_ACLS__",
        json.dumps({x["name"]: x["raw_acl"] for x in native_after}, sort_keys=True),
    )
    installed = (
        db.execute(
            text(
                """SELECT p.proname,p.oid::bigint AS oid,
        p.proname||'('||coalesce((SELECT string_agg(format_type(t,NULL),',' ORDER BY ord)
          FROM unnest(p.proargtypes::oid[]) WITH ORDINALITY args(t,ord)),'')||')' AS signature,
        p.proowner=(SELECT datdba FROM pg_database WHERE datname=current_database()) AS owned
        FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND NOT EXISTS(SELECT FROM pg_depend d WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.refclassid='pg_extension'::regclass AND d.refobjid=__INSTALL_EXTENSION__ AND d.deptype='e')""".replace(
                    "__INSTALL_EXTENSION__", str(tls_native["extension_oid"])
                )
            )
        )
        .mappings()
        .all()
    )
    if (
        len(installed) != len(LEGACY_PINS)
        or {r["proname"] for r in installed} != set(LEGACY_PINS)
        or any(
            not r["owned"] or r["signature"] != LEGACY_PINS[r["proname"]]["signature"]
            for r in installed
        )
    ):
        raise RuntimeError("Identity historical routine identity inventory mismatch")
    body = body.replace(
        "__LEGACY_PINS__", json.dumps(LEGACY_PINS, sort_keys=True, separators=(",", ": "))
    )
    body = body.replace(
        "__LEGACY_OIDS__",
        json.dumps(
            {r["proname"]: r["oid"] for r in installed}, sort_keys=True, separators=(",", ": ")
        ),
    )
    op.execute(body.replace(":null", ": null"))
    measured = (
        db.execute(
            text(
                "SELECT p.proname name,"
                + NATIVE_DEFINITION_SQL
                + " fingerprint FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE p.oid=ANY(CAST(:oids AS oid[]))"
            ),
            {"oids": [row["function_oid"] for row in native_after]},
        )
        .mappings()
        .all()
    )
    if len(measured) != 10 or any(
        row["fingerprint"] != NATIVE_SSLINFO_PINS[namespace].get(row["name"]) for row in measured
    ):
        raise RuntimeError("Identity native semantic fingerprint mismatch")
    signatures = (
        db.execute(
            text("""SELECT p.oid::regprocedure::text FROM pg_proc p
      JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='menuto_identity_source' ORDER BY p.oid""")
        )
        .scalars()
        .all()
    )
    if len(signatures) != 17:
        raise RuntimeError("Identity exact function inventory mismatch")
    for signature in signatures:
        op.execute(f"ALTER FUNCTION {signature} OWNER TO menuto_identity_source_owner")
        op.execute(
            f"REVOKE ALL ON FUNCTION {signature} FROM PUBLIC,menuto_identity_bootstrap,menuto_identity_issuer,menuto_identity_requester"
        )
    for name, role in ENTRIES.items():
        op.execute(f"GRANT EXECUTE ON FUNCTION menuto_identity_source.{name}(text) TO {role}")
    op.execute(
        "GRANT USAGE ON SCHEMA menuto_identity_source TO menuto_identity_bootstrap,menuto_identity_issuer,menuto_identity_requester"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE menuto_identity_source_owner IN SCHEMA menuto_identity_source REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC"
    )
    if not db.execute(
        text("""SELECT EXISTS(SELECT FROM pg_depend d JOIN pg_proc p ON p.oid=d.objid JOIN pg_namespace n ON n.oid=p.pronamespace
       WHERE n.nspname='menuto_identity_source' AND p.proname='_tls_fact_v1' AND p.prosqlbody IS NOT NULL
        AND d.classid='pg_proc'::regclass AND d.refclassid='pg_proc'::regclass AND d.refobjid=:oid AND d.deptype='n')"""),
        {"oid": tls_native["function_oid"]},
    ).scalar_one():
        raise RuntimeError("Identity native TLS parsed dependency mismatch")
    for table in TABLES:
        op.execute(
            f"CREATE TRIGGER identity_write_guard BEFORE INSERT OR UPDATE OR DELETE ON menuto_identity_source.{table} FOR EACH ROW EXECUTE FUNCTION menuto_identity_source._reject_history_mutation_v1()"
        )
        op.execute(
            f"CREATE TRIGGER identity_truncate_guard BEFORE TRUNCATE ON menuto_identity_source.{table} FOR EACH STATEMENT EXECUTE FUNCTION menuto_identity_source._reject_history_mutation_v1()"
        )


def downgrade():
    db = op.get_bind()
    for table in TABLES:
        if db.execute(
            text(f"SELECT EXISTS(SELECT FROM menuto_identity_source.{table})")
        ).scalar_one():
            raise RuntimeError("Identity downgrade refuses retained history/frontiers/receipts")
    metadata = json.loads(
        db.execute(
            text("SELECT obj_description('menuto_identity_source'::regnamespace,'pg_namespace')")
        ).scalar_one()
    )
    for role in metadata["created_roles"]:
        if (
            role not in ROLES
            or db.execute(
                text(
                    "SELECT EXISTS(SELECT FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=:name) OR roleid=(SELECT oid FROM pg_roles WHERE rolname=:name))"
                ),
                {"name": role},
            ).scalar_one()
        ):
            raise RuntimeError("Identity downgrade refuses role membership/dependency drift")
    for table in TABLES:
        op.execute(f"DROP TRIGGER identity_write_guard ON menuto_identity_source.{table}")
        op.execute(f"DROP TRIGGER identity_truncate_guard ON menuto_identity_source.{table}")
    # Entries first, SQL OID-bound native helper last. No CASCADE/shared extension deletion.
    signatures = (
        db.execute(
            text("""SELECT p.oid::regprocedure::text FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
       WHERE n.nspname='menuto_identity_source' ORDER BY (p.proname='_tls_fact_v1'),p.oid DESC""")
        )
        .scalars()
        .all()
    )
    for signature in signatures:
        op.execute(f"DROP FUNCTION {signature}")
    for table in (
        "command_receipts",
        "frontiers",
        "operation_grants",
        "principal_bindings",
        "issuers",
        "roots",
    ):
        op.execute(f"DROP TABLE menuto_identity_source.{table}")
    op.execute("DROP SEQUENCE menuto_identity_source.recorded_order")
    namespace = metadata["tls_namespace"]
    if namespace not in {"public", "menuto_prior"}:
        raise RuntimeError("Identity downgrade TLS namespace ledger mismatch")
    if not metadata["tls_before"]["execute"]:
        op.execute(
            f"REVOKE EXECUTE ON FUNCTION {namespace}.ssl_is_used() FROM menuto_identity_source_owner"
        )
    if not metadata["tls_before"]["usage"]:
        op.execute(f"REVOKE USAGE ON SCHEMA {namespace} FROM menuto_identity_source_owner")
    op.execute(
        "REVOKE SELECT ON public.users,public.households,public.household_members,public.memberships FROM menuto_identity_source_owner"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE menuto_identity_source_owner IN SCHEMA menuto_identity_source GRANT EXECUTE ON FUNCTIONS TO PUBLIC"
    )
    op.execute("DROP SCHEMA menuto_identity_source")
    for role in reversed(metadata["created_roles"]):
        op.execute(f"DROP ROLE {role}")
