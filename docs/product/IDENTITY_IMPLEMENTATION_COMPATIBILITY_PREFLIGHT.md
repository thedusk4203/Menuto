# Identity implementation compatibility authorization preflight

**PROPOSAL ONLY: every diff below is unapplied. Separate owner authorization is required for each historical file/block.**

## Immutable source of baseline

Baseline commit32a134989b5c033a304dde1a92e9e35c8a1b8341; treee16a13ec7d7b59171f5a53deaf4543cb5e2bc227.
Canonical body hashing: SHA-256(json.dumps(body,sort_keys=True,separators=(",",":")).encode("utf-8")); default ensure_ascii=True.
Complete bodies are retained in that immutable Git tree at packages/contracts/domain.schema.json.
Its LF text SHA-256 is 9cab7704892106f98393dce6b0e4aad06407715a4334feed3ddc39a8594c0bc2. These pins are independent of future generated exports.
Future implementation reconstructs these Git bodies and compares exact equality, not only count/names. No existing body/hash fixture is edited.

## Independently authored exact19-name manifest

First18 belong to Identity/source_contracts; final carrier belongs to Policy/authenticated_intent_contracts. Transcribed from approved contracts, not inferred from future $defs.

~~~json
[
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
  "AuthenticatedPlanIntentInspectionV1"
]
~~~

Future proof: set(new)-set(baseline537)==set(manifest19); baseline537 subset new; every new[name]==baseline[name] and digest matches; len(new)==556. No extra enum/base/helper definition.
Keep515legacy/503historical/53files/59PIVpins and EPI001–064 unchanged.

## Exact inverse before old inverse

New test-only identity_compatibility_metadata.py has a literal19-name constant validated against a separately committed literal manifest, never actual exports.
Its new fixture pins every baseline file digest below, exact ordered before/after edits, final postimage and all537 bodies.
restore_identity_metadata(path,body) requires exact approved postimage digest, reverses each exact block once in reverse order, then requires exact537-era preimage digest. Missing/duplicate/unknown edits, extra content, wrong digest or path fail. Unchanged historical paths are allowed only from independently pinned baseline inventory and must match its digest; unknown paths fail. No permissive fallback.
PIV-D31 keeps515 body hashes,59 file pins and126 baseline file hashes. New inverse runs before old EPI inverse, then old seven PIV exceptions. Both old dictionaries/fixtures remain byte-identical.
EPI verify_metadata_patch keeps8files/17blocks and every old after_sha256. Direct old inverse mutation starts from its exact historical postimage.
Unknown-name/old-body/historical-assertion/incorrect-normalization mutations stay intact. Comments used by those mutation needles remain historical provenance; count556 additionally includes19 Identity names. New ITR mutations must prove every new inverse/exact-set layer rejects unknown edits.
This is test-only normalization, not an authority filter, skip, subset proof or mutable baseline refresh.

## Migration identity awaiting separate authorization

Current sole head0017/down0016. IDENTITY_MIGRATION_REVISION comes from a NEW independently approved manifest: exact revision/filename/down0017/all17 old filename+hash pins/six-table delta/no extras. Never derive expected values from installed head/files. No revision is allocated here.
assert_identity_migration_delta(ROOT) proves exact17 immutable old files plus exactly one approved new revision/file/edge, and no other migrations. Every retained PG test runs actual new head, never a hidden downgrade to0017.
Public Base/public schema108 remain108 because Identity owns separate private metadata/schema; ITR001 counts108+6=114 across both. Existing Alembic public metadata remains unchanged; new migration owns explicit frozen private DDL and ITR verifies private schema/model parity.

## Exact file/patch inventory

35 existing Python files have proposed changes: 34 tests/helpers plus import-boundary tooling. No Python file is changed on disk by this package.
Every virtual postimage parses. Hashes below use UTF-8 LF text, matching historical normalization. Zero-context BEFORE/AFTER diffs include every changed line/import and exact hunk offsets; full baseline context is pinned by commit/path/hash. Zero context keeps literal patch blank lines free of Markdown trailing whitespace. Old fixtures/frozen sources/migrations are excluded.

| Path | Baseline SHA-256 | Proposed postimage SHA-256 |
|---|---|---|
| apps/backend/tests/explicit_plan_intent_architecture_checks.py | b1b2e22122acaad9f7c529ecb93828f0764c584849d6b1d9272a1b5f571ea7d5 | abd1b1306ac2fd8effb791a2f22212c5268d5298d0754f6e59bb5ebcaf366827 |
| apps/backend/tests/hierarchy_postgres_fixtures.py | 39752ee435f898c9c677fd29897cf4aa9df3880cb7a8270299dfd6cf5ca81dc7 | e3bdd4da2f4e013924097173843c30ae60217dbbaae3b0e7ddb7aff3a9217ad4 |
| apps/backend/tests/nutrition_root_postgres_fixtures.py | 331f7425c4b67f736e0418534f0636b314b9280b230ca03669b7e1cd4dcbf731 | b94a333a9a5d12669a9eb685b84448805f722dcd130992450c93ae4d6dec9061 |
| apps/backend/tests/test_basis_applicability.py | d472d7b5935ea5e1dd05b14285a6d4c4c8da3aa19b42a8f184b5fbedeba2c60f | 06c07a41e0ab56fba13faddaa2471aa998d622c2051e0106962c060976ada222 |
| apps/backend/tests/test_candidate_feature_projection.py | 02a7baf3c120f17faffafd239add233ba48ea3de89c5674e9bfb7f6eb4f95aac | df2ca3104394df8abdb563ff72e236f0d5789628b807be486afec71d7ad929bf |
| apps/backend/tests/test_explicit_plan_intent.py | 4e758ec1b7bf448c336e5d222517d457d1f5bb114895a4fb94922c06219ad306 | 20dff38a04762c1b7f2dabfa0fa5ca50dc421cbb66f7149e6e66be29bf833413 |
| apps/backend/tests/test_explicit_plan_intent_architecture.py | 6a01bf6c0852aae6688124da8613cf9f1cb7c43f485fd8c0e2c0dd544b4300fc | 382943c94ea1e8de85e38815c36ab212331b0baecc1ce1f38243cf54050ebd2e |
| apps/backend/tests/test_explicit_plan_intent_preflight.py | f5068f542bcc4338d38c158704d7fae9dcecfd4c73270b754ac14dd5d3f7a99c | 158135d9e6423574008975065aab0b00df4830a7126dcba1ab41d4f05ab540c4 |
| apps/backend/tests/test_foundation_migration.py | cf582976fc692cd0c99d9812d7902f582245ba00149f6072aee6f5c039bc01a7 | e24bd17135a69958fc106d7b114d1a39b3bad14f1ce084022bd08a3a74f1c09c |
| apps/backend/tests/test_hierarchical_affinity_compatibility.py | 064dd3308e11e46d1938b80fda0f3ed7dc6a54d58c74982b8d2251981720b60c | f3ee75ab1a88f141522304189a5a253bea7c3fb04bd55f2131adb0d7c36aa1b9 |
| apps/backend/tests/test_hierarchy_compatibility.py | e32277e77c0b3373cdcbea32b1c7dc6bc8912a7cfcd819706bcf7909321a4a81 | 141aa6ecfcc2ee8a80b0227a1da4e7eef954d807ce7b4fed3e19030f24e8a415 |
| apps/backend/tests/test_nutrition_resolution.py | 7f8cf34f53f69ba7074a8416e731e61c27e454acca86d0b07c9b5dd376979d6b | 05407d2dcaf987fbb4683a316656e49c23b9168066be66746d488ff1a1c4c546 |
| apps/backend/tests/test_nutrition_root_architecture.py | da2b1181d6771a4c90242e6bd24c379de324725bf63884d2dad64dd159909d18 | 4869826ba73bf7bb514b046395f8b0cacd08f345860c22bf800117ddeab012ad |
| apps/backend/tests/test_policy_v2.py | 0317656cb8db783b628707d5e3078b7e3ef93d2954ef135d4cd70f21577feb01 | 44efc9154cbee3c9b57c8a41ac7c98e4acfcf31130e6fb52cb5eecc6b0da2d86 |
| apps/backend/tests/test_postgres_basis_applicability.py | 7429183591e19057fc6f9d7d99422853be749760f877199dcfd64bb05005d6a9 | 81c0350e72a6db4f83dad4bbbe24ea6704f04147baceb4f390015413e35151df |
| apps/backend/tests/test_postgres_candidate_feature_projection.py | 0dae34bebd3db0fbce2c6164968418938a63a3ac9a8fccafcd1257c7e676d215 | 48f51e6b5a92c8eb4480ea19c86dd231357374f49130f6bd9194b910488ed56f |
| apps/backend/tests/test_postgres_candidate_member_tastefit.py | 7f65d9ce32384b1f7550310a223fdfa01d6e0baeedc96e8329118ee61166a0ab | 47c206bd20e0d789853e651bbc45968caf66a1dc72c66bcd78b8b23f6e5ba00a |
| apps/backend/tests/test_postgres_exposure.py | 631409960ebfb3477a2f28ddfa1a7be193980bf46aa550970d5f0322899dcbdb | 481df0f2be0922dafd92010817bf1cd1cd93cb04648faaaa3c85aed907407b4e |
| apps/backend/tests/test_postgres_feature_exposure.py | 4ab12d858c8d23f88f2d2584a5af335152e9987f01ae6875e1081e94a495c196 | 79f0c2362f1a3c8e35979dafa7e61c440cad074e35e26572ff1588009de4b9ac |
| apps/backend/tests/test_postgres_feature_repeat.py | c640b92304a276aaa315e26218b76c8dffabcf29c589a26fe110f21adc54d5b4 | bf5396c2516b4fe0d69129f8a70017e10b8fd3e9cfc78f33614354720d9ad8e3 |
| apps/backend/tests/test_postgres_hierarchy_lifecycle.py | 29de8c9ab38201cd129178ba75eb419c72c1610943874631ab38d1bb7e1ecd50 | 87fe4b5ed650ae04fa64c529202c4a5a8b8112be789eeec7e2e45a52aff58f75 |
| apps/backend/tests/test_postgres_nutrition_resolution.py | 07d5e49ab5970e5d7b2a4b5bc468b98cf99bd6e40dadb0569f0653f2bfa50b72 | 2553ac8e480175623b8bc3b8d19331a2011a5251d2f236b435181223f1517329 |
| apps/backend/tests/test_postgres_nutrition_root_source.py | 7dd52ae7858af073d3c5aa7a068224d48a8c973f56233b2f818ca2480e60e789 | 45057035f901731316a7f1a67a6a1e45ec3dde6419fa92e21baef3050d2c0153 |
| apps/backend/tests/test_postgres_nutrition_synthesis_authority.py | 78957a6a5e1db3b1b4aec2b18ec7ad395b3be60d57e8b2354538fd57d3732893 | a86e706d44b404d15fbb3b733612db33fe0460e4855f8bcff8ff2139e0155598 |
| apps/backend/tests/test_postgres_plans.py | 4583810d445ebd6851c33b4ae811cf4270f34141a49340da679dc290dc3fbd93 | cd420a5d5ce3d0b5e1e5fb6457af79324ec4b12b3d2460c12c2497ef15046160 |
| apps/backend/tests/test_postgres_policy_v2.py | 1ad280d21cdcd330f8e36670743e95ec2a0c45e584954c7bf950fc069c760150 | 8a70941e6c0f3902626b0488f07bc8539179444411a7c74f88eec58a8c031b6a |
| apps/backend/tests/test_postgres_reference_prior_authority_extra.py | c93a452887ce81f4379d362b0c511e0266672af6c00ccbb64d5acf5cc4c70e41 | 8256d30eca1a3d0a4ea48b96473ec4748fa7274866fcb2bbd1700abbb51ff0d1 |
| apps/backend/tests/test_postgres_reference_priors.py | 2b30246b6e1894e31ae702b1f14172aac0f1ffbe748e37fcb63a0d2489bd1f24 | da5b3e0adebe4762e53ae379d8d2cbcf76202aaf961fcbbbb2fcb83ed60a4cab |
| apps/backend/tests/test_postgres_retail.py | 3cccd34ee8a64a11273a50668c9952b9a0c7773d8b14a4db3d53bd23c4f9bfe0 | 8b895131c82b1d3c05163ea2cb6f8876e0b80027aea086b783b625fd288d4242 |
| apps/backend/tests/test_postgres_shared_target_tastefit.py | 4ceeef872539ee99fb03a04d020e961b9a8e6588186f8b6e56eb63095aba3de9 | 14f7c6a789d091dbf961efb64fac2a73a9896d1e59f87c7c5333b85e58885232 |
| apps/backend/tests/test_postgres_target_affinity.py | 907a368831f47df09e4706b63592df56881f4eb33d458bdc8899fedc4c3f947a | c7215c459fcd88439468d1a833dc35cd12b7d35f1d1769e9a8dcb0ab116bf9cf |
| apps/backend/tests/test_postgres_validation.py | 60d984bab972d4c5c6ec58690ae40e9387056f71d359ce81bde7aad93cbca385 | a3535e73105a0fd7ff1b79135e943e567f3d23c42c5dd9148cd7175d6b9bc2a5 |
| apps/backend/tests/test_shared_target_tastefit_architecture.py | a1e8d0f5af35ef64f36a4687ad94fee99da6e3bd0bc1e14c1fe9be4a5224296e | 8c1f2a75411593de635916dac255b728085c36fde903b0cb5c6d966513ae99fa |
| apps/backend/tests/test_tastefit_architecture.py | f41fc5edf52d6ca07082fe5d60d250b2e2cfdaff956c3426372b8cf5b407d933 | ed41d87b36faccef46f856f7bbbba7cb0f4cf9037efbab4fa18ea0752ecb1f2b |
| tools/check_import_boundaries.py | 5dd7e73e72d42918d140752fdd70a942b6238e07b77433dfdf67a8456bd4953b | 2e2cb7b49b70f55470caf23cb57b3e9bad3973d8ef7bfe9e8f2fb7888cb23194 |

### Full proposed diffs (not applied)

#### apps/backend/tests/explicit_plan_intent_architecture_checks.py

Reason: New exact inverse before unchanged EPI17-block inverse and old postimage hash.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/explicit_plan_intent_architecture_checks.py
+++ b/apps/backend/tests/explicit_plan_intent_architecture_checks.py
@@ -6,0 +7,4 @@
+
+from identity_compatibility_metadata import (
+    restore_identity_metadata,
+)
@@ -105 +109 @@
-        body = (ROOT / path).read_text()
+        body = restore_identity_metadata(path, (ROOT / path).read_text())
~~~

#### apps/backend/tests/hierarchy_postgres_fixtures.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/hierarchy_postgres_fixtures.py
+++ b/apps/backend/tests/hierarchy_postgres_fixtures.py
@@ -23,0 +24,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -76 +79 @@
-            assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+            assert conn.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/nutrition_root_postgres_fixtures.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/nutrition_root_postgres_fixtures.py
+++ b/apps/backend/tests/nutrition_root_postgres_fixtures.py
@@ -26,0 +27,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -123 +126 @@
-            assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+            assert db.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_basis_applicability.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_basis_applicability.py
+++ b/apps/backend/tests/test_basis_applicability.py
@@ -29,0 +30,3 @@
+from identity_compatibility_metadata import (
+    assert_identity_migration_delta,
+)
@@ -736 +739 @@
-    assert not list((ROOT / "apps/backend/migrations/versions").glob("0018*"))
+    assert_identity_migration_delta(ROOT)
~~~

#### apps/backend/tests/test_candidate_feature_projection.py

Reason: Only aggregate export metadata; historical body/hash/identity assertions remain.; Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_candidate_feature_projection.py
+++ b/apps/backend/tests/test_candidate_feature_projection.py
@@ -41,0 +42,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -727 +730 @@
-    assert len(definitions) == 537  # 528 retained +9 additive explicit plan intent.
+    assert len(definitions) == 556  # 528 retained +9 additive explicit plan intent.
@@ -744 +747 @@
-    ) == [f"{n:04}" for n in range(1, 18)]
+    ) == [f"{n:04}" for n in range(1, 18)] + [IDENTITY_MIGRATION_REVISION]
~~~

#### apps/backend/tests/test_explicit_plan_intent.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_explicit_plan_intent.py
+++ b/apps/backend/tests/test_explicit_plan_intent.py
@@ -21,0 +22,3 @@
+from identity_compatibility_metadata import (
+    assert_identity_migration_delta,
+)
@@ -621 +624 @@
-    assert not list((ROOT / "apps/backend/migrations/versions").glob("0018*"))
+    assert_identity_migration_delta(ROOT)
~~~

#### apps/backend/tests/test_explicit_plan_intent_architecture.py

Reason: Old unexpected-assertion mutation starts at exact historical EPI postimage.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_explicit_plan_intent_architecture.py
+++ b/apps/backend/tests/test_explicit_plan_intent_architecture.py
@@ -13,0 +14,3 @@
+)
+from identity_compatibility_metadata import (
+    restore_identity_metadata,
@@ -118 +121 @@
-    body = (ROOT / path).read_text()
+    body = restore_identity_metadata(path, (ROOT / path).read_text())
~~~

#### apps/backend/tests/test_explicit_plan_intent_preflight.py

Reason: Preserve exact9 EPI names and528 body hashes; add exactly19 pinned later names.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_explicit_plan_intent_preflight.py
+++ b/apps/backend/tests/test_explicit_plan_intent_preflight.py
@@ -9,0 +10,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_EXPORT_NAMES,
+)
@@ -33 +36 @@
-    assert len(baseline["definitions"]) == 528 and len(actual) == 537
+    assert len(baseline["definitions"]) == 528 and len(actual) == 556
@@ -38,2 +41,2 @@
-    assert len(new) == 537
-    assert set(new) - set(old) == set(NAMES)
+    assert len(new) == 556
+    assert set(new) - set(old) == set(NAMES) | set(IDENTITY_EXPORT_NAMES)
~~~

#### apps/backend/tests/test_foundation_migration.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_foundation_migration.py
+++ b/apps/backend/tests/test_foundation_migration.py
@@ -11,0 +12,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -229 +232 @@
-        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
@@ -264 +267 @@
-        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_hierarchical_affinity_compatibility.py

Reason: Only aggregate export metadata; historical body/hash/identity assertions remain.; Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_hierarchical_affinity_compatibility.py
+++ b/apps/backend/tests/test_hierarchical_affinity_compatibility.py
@@ -12,0 +13,4 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
+
@@ -21 +25 @@
-    assert len(pins["definitions"]) == 349 and len(schema) == 537  # 528 retained +9 intent.
+    assert len(pins["definitions"]) == 349 and len(schema) == 556  # 528 retained +9 intent.
@@ -53 +57 @@
-    ) == [f"{n:04}" for n in range(1, 18)]
+    ) == [f"{n:04}" for n in range(1, 18)] + [IDENTITY_MIGRATION_REVISION]
~~~

#### apps/backend/tests/test_hierarchy_compatibility.py

Reason: Only aggregate export metadata; historical body/hash/identity assertions remain.

~~~diff
--- a/apps/backend/tests/test_hierarchy_compatibility.py
+++ b/apps/backend/tests/test_hierarchy_compatibility.py
@@ -21 +21 @@
-    assert len(schema) == 537  # 528 retained +9 additive explicit intent definitions.
+    assert len(schema) == 556  # 528 retained +9 additive explicit intent definitions.
~~~

#### apps/backend/tests/test_nutrition_resolution.py

Reason: Extend exact union by literal19 names; SMTF historical403 stays unchanged.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_nutrition_resolution.py
+++ b/apps/backend/tests/test_nutrition_resolution.py
@@ -32,0 +33,3 @@
+)
+from identity_compatibility_metadata import (
+    IDENTITY_EXPORT_NAMES,
@@ -941 +944 @@
-                           | set(explicit_intent))
+                           | set(explicit_intent) | set(IDENTITY_EXPORT_NAMES))
~~~

#### apps/backend/tests/test_nutrition_root_architecture.py

Reason: Only aggregate export metadata; historical body/hash/identity assertions remain.; Extend exact union by literal19 names; SMTF historical403 stays unchanged.; Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_nutrition_root_architecture.py
+++ b/apps/backend/tests/test_nutrition_root_architecture.py
@@ -15,0 +16,4 @@
+from identity_compatibility_metadata import (
+    IDENTITY_EXPORT_NAMES,
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -139 +143 @@
-    assert files == [f"{i:04d}" for i in range(1, 18)]
+    assert files == [f"{i:04d}" for i in range(1, 18)] + [IDENTITY_MIGRATION_REVISION]
@@ -153 +157 @@
-    assert len(schema) == 537  # 528 retained +9 additive explicit intent definitions.
+    assert len(schema) == 556  # 528 retained +9 additive explicit intent definitions.
@@ -159 +163 @@
-    )
+    ) | set(IDENTITY_EXPORT_NAMES)
~~~

#### apps/backend/tests/test_policy_v2.py

Reason: Only aggregate export metadata; historical body/hash/identity assertions remain.; Extend exact union by literal19 names; SMTF historical403 stays unchanged.; Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; PIV-D31 inverse first; both old dictionaries and126 baseline hashes unchanged.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_policy_v2.py
+++ b/apps/backend/tests/test_policy_v2.py
@@ -21,0 +22,5 @@
+from identity_compatibility_metadata import (
+    IDENTITY_EXPORT_NAMES,
+    assert_identity_migration_delta,
+    restore_identity_metadata,
+)
@@ -643 +648 @@
-    assert len(additions) == 13 and len(defs) == 537
+    assert len(additions) == 13 and len(defs) == 556
@@ -645 +650 @@
-    assert set(defs) - set(proof["definitions"]) == additions | set(explicit_intent)
+    assert set(defs) - set(proof["definitions"]) == additions | set(explicit_intent) | set(IDENTITY_EXPORT_NAMES)
@@ -657 +662 @@
-    assert not list((ROOT / "apps/backend/migrations/versions").glob("0018*"))
+    assert_identity_migration_delta(ROOT)
@@ -771 +776,3 @@
-    body = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
+    body = restore_identity_metadata(
+        path, (ROOT / path).read_bytes().replace(b"\r\n", b"\n").decode()
+    ).encode()
~~~

#### apps/backend/tests/test_postgres_basis_applicability.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_basis_applicability.py
+++ b/apps/backend/tests/test_postgres_basis_applicability.py
@@ -11,0 +12,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -307 +310 @@
-        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert db.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_candidate_feature_projection.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_candidate_feature_projection.py
+++ b/apps/backend/tests/test_postgres_candidate_feature_projection.py
@@ -32,0 +33,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -508 +511 @@
-        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_candidate_member_tastefit.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_candidate_member_tastefit.py
+++ b/apps/backend/tests/test_postgres_candidate_member_tastefit.py
@@ -11,0 +12,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -746 +749 @@
-        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_exposure.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_exposure.py
+++ b/apps/backend/tests/test_postgres_exposure.py
@@ -11,0 +12,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -102 +105 @@
-        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_feature_exposure.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_feature_exposure.py
+++ b/apps/backend/tests/test_postgres_feature_exposure.py
@@ -14,0 +15,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -116 +119 @@
-        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_feature_repeat.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_feature_repeat.py
+++ b/apps/backend/tests/test_postgres_feature_repeat.py
@@ -31,0 +32,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -164 +167 @@
-        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert db.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_hierarchy_lifecycle.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_hierarchy_lifecycle.py
+++ b/apps/backend/tests/test_postgres_hierarchy_lifecycle.py
@@ -19,0 +20,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -304 +307 @@
-        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_nutrition_resolution.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_nutrition_resolution.py
+++ b/apps/backend/tests/test_postgres_nutrition_resolution.py
@@ -18,0 +19,3 @@
+)
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
@@ -488 +491 @@
-        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert db.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_nutrition_root_source.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_nutrition_root_source.py
+++ b/apps/backend/tests/test_postgres_nutrition_root_source.py
@@ -16,0 +17,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -51 +54 @@
-        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert db.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
@@ -981 +984 @@
-        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert db.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_nutrition_synthesis_authority.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_nutrition_synthesis_authority.py
+++ b/apps/backend/tests/test_postgres_nutrition_synthesis_authority.py
@@ -14,0 +15,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -107 +110 @@
-            assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+            assert db.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
@@ -538 +541 @@
-            assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+            assert db.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_plans.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_plans.py
+++ b/apps/backend/tests/test_postgres_plans.py
@@ -22,0 +23,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -540 +543 @@
-        assert session.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert session.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_policy_v2.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_policy_v2.py
+++ b/apps/backend/tests/test_postgres_policy_v2.py
@@ -6,0 +7,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -542 +545 @@
-        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert db.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_reference_prior_authority_extra.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_reference_prior_authority_extra.py
+++ b/apps/backend/tests/test_postgres_reference_prior_authority_extra.py
@@ -12,0 +13,3 @@
+)
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
@@ -156 +159 @@
-        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_reference_priors.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_reference_priors.py
+++ b/apps/backend/tests/test_postgres_reference_priors.py
@@ -34,0 +35,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -88 +91 @@
-            assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+            assert conn.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_retail.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_retail.py
+++ b/apps/backend/tests/test_postgres_retail.py
@@ -12,0 +13,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -540 +543 @@
-        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_shared_target_tastefit.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_shared_target_tastefit.py
+++ b/apps/backend/tests/test_postgres_shared_target_tastefit.py
@@ -21,0 +22,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -633 +636 @@
-        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert db.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_target_affinity.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_target_affinity.py
+++ b/apps/backend/tests/test_postgres_target_affinity.py
@@ -18,0 +19,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -386 +389 @@
-            assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+            assert conn.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_postgres_validation.py

Reason: Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_postgres_validation.py
+++ b/apps/backend/tests/test_postgres_validation.py
@@ -13,0 +14,3 @@
+from identity_compatibility_metadata import (
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -226 +229 @@
-        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0017"
+        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == IDENTITY_MIGRATION_REVISION
~~~

#### apps/backend/tests/test_shared_target_tastefit_architecture.py

Reason: Extend exact union by literal19 names; SMTF historical403 stays unchanged.; Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_shared_target_tastefit_architecture.py
+++ b/apps/backend/tests/test_shared_target_tastefit_architecture.py
@@ -15,0 +16,4 @@
+from identity_compatibility_metadata import (
+    IDENTITY_EXPORT_NAMES,
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -36 +40 @@
-             | set(explicit_intent))
+             | set(explicit_intent) | set(IDENTITY_EXPORT_NAMES))
@@ -53 +57 @@
-    ) == [f"{i:04}" for i in range(1, 18)]
+    ) == [f"{i:04}" for i in range(1, 18)] + [IDENTITY_MIGRATION_REVISION]
~~~

#### apps/backend/tests/test_tastefit_architecture.py

Reason: Only aggregate export metadata; historical body/hash/identity assertions remain.; Extend exact union by literal19 names; SMTF historical403 stays unchanged.; Run retained test at actual approved future head; keep exact0017 prefix and old hashes. No old-head shortcut.; New test-owned helper import; no runtime authority.; Ruff import ordering for proposed helper/constant imports; no old behavior change.

~~~diff
--- a/apps/backend/tests/test_tastefit_architecture.py
+++ b/apps/backend/tests/test_tastefit_architecture.py
@@ -13,0 +14,4 @@
+from identity_compatibility_metadata import (
+    IDENTITY_EXPORT_NAMES,
+    IDENTITY_MIGRATION_REVISION,
+)
@@ -36 +40 @@
-    ) == [f"{n:04}" for n in range(1, 18)]
+    ) == [f"{n:04}" for n in range(1, 18)] + [IDENTITY_MIGRATION_REVISION]
@@ -76 +80 @@
-    assert len(defs) == 537  # 528 retained +9 additive explicit intent definitions.
+    assert len(defs) == 556  # 528 retained +9 additive explicit intent definitions.
@@ -85,0 +90 @@
+        + len(IDENTITY_EXPORT_NAMES)
@@ -95,0 +101 @@
+        + list(IDENTITY_EXPORT_NAMES)
~~~

#### tools/check_import_boundaries.py

Reason: Exact new module/symbol list; no global ALLOWED/PUBLIC_SURFACES changes.; Only exact symbol seams; no module/star/prefix permission or producer import in Validation.; New pure modules have no dynamic/file I/O; old checks remain.; New pure modules have no clock/environment/connection access.

~~~diff
--- a/tools/check_import_boundaries.py
+++ b/tools/check_import_boundaries.py
@@ -367,0 +368,41 @@
+# Identity exact additive symbol seams; no context-wide permission.
+IDENTITY_SYMBOL_SEAMS = {'app.modules.planning.identity_source_inspection': ['app.modules.identity.source_capture.capture_identity_request_source_v1',
+                                                     'app.modules.identity.source_contracts.IdentityCaptureFailureV1',
+                                                     'app.modules.identity.source_contracts.IdentityEffectiveRequestV1',
+                                                     'app.modules.identity.source_contracts.IdentityRequestBindingV1',
+                                                     'app.modules.identity.source_contracts.IdentitySourceSnapshotV1',
+                                                     'app.modules.policy.authenticated_intent_contracts.AuthenticatedPlanIntentInspectionV1',
+                                                     'app.modules.policy.explicit_intent_public.resolve_explicit_plan_intent_v1',
+                                                     'app.modules.validation.explicit_plan_intent.check_explicit_plan_intent_v1',
+                                                     'app.modules.validation.identity_source.check_identity_source_v1'],
+ 'app.modules.policy.authenticated_intent_contracts': ['app.modules.identity.source_contracts.IdentityCaptureFailureV1',
+                                                       'app.modules.identity.source_contracts.IdentitySourceCheckV1',
+                                                       'app.modules.identity.source_contracts.IdentitySourceSnapshotV1',
+                                                       'app.modules.policy.explicit_intent_contracts.PlanIntentCheckV1',
+                                                       'app.modules.policy.explicit_intent_contracts.PlanIntentResolutionV1'],
+ 'app.modules.validation.identity_source': ['app.modules.identity.source_contracts.IdentityBindingCommandV1',
+                                            'app.modules.identity.source_contracts.IdentityCaptureFailureV1',
+                                            'app.modules.identity.source_contracts.IdentityCaptureFrameV1',
+                                            'app.modules.identity.source_contracts.IdentityCommandReceiptV1',
+                                            'app.modules.identity.source_contracts.IdentityEffectiveRequestV1',
+                                            'app.modules.identity.source_contracts.IdentityIssuerCommandV1',
+                                            'app.modules.identity.source_contracts.IdentityMembershipWitnessV1',
+                                            'app.modules.identity.source_contracts.IdentityOperationGrantCommandV1',
+                                            'app.modules.identity.source_contracts.IdentityPrivilegeObjectFactV1',
+                                            'app.modules.identity.source_contracts.IdentityRecordedFactV1',
+                                            'app.modules.identity.source_contracts.IdentityRequestBindingV1',
+                                            'app.modules.identity.source_contracts.IdentityRoleEdgeV1',
+                                            'app.modules.identity.source_contracts.IdentityRoleFactV1',
+                                            'app.modules.identity.source_contracts.IdentityRootCommandV1',
+                                            'app.modules.identity.source_contracts.IdentitySessionFactV1',
+                                            'app.modules.identity.source_contracts.IdentitySourceCheckV1',
+                                            'app.modules.identity.source_contracts.IdentitySourceFrontierV1',
+                                            'app.modules.identity.source_contracts.IdentitySourceSnapshotV1']}
+IDENTITY_PURE_MODULES = {
+    "app.modules.identity.source_contracts", "app.modules.identity.source_primitives",
+    "app.modules.identity.source_limits", "app.modules.identity.source_replay",
+    "app.modules.policy.authenticated_intent_contracts",
+    "app.modules.validation.identity_source",
+}
+
+
@@ -382,0 +424,10 @@
+        if module in IDENTITY_SYMBOL_SEAMS and target.startswith("app.modules."):
+            if target in IDENTITY_SYMBOL_SEAMS[module]:
+                return
+            errors.append(f"{line}: IDENTITY_EXACT_SYMBOL_BOUNDARY: {target}")
+            return
+        if module in IDENTITY_PURE_MODULES and target.split(".")[0] in {
+            "sqlalchemy", "psycopg", "socket", "os", "pathlib", "time",
+            "requests", "httpx", "urllib", "subprocess", "importlib",
+        }:
+            errors.append(f"{line}: IDENTITY_PURE_IMPORT: {target}")
@@ -674,0 +726,5 @@
+            if module in IDENTITY_PURE_MODULES and node.func.id in {
+                "open", "input", "eval", "exec", "__import__", "compile"
+            }:
+                errors.append(f"{node.lineno}: IDENTITY_PURE_CALL")
+
@@ -693,0 +750,5 @@
+            if module in IDENTITY_PURE_MODULES and node.func.attr in {
+                "now", "utcnow", "today", "time", "getenv", "monotonic", "connect"
+            }:
+                errors.append(f"{node.lineno}: IDENTITY_PURE_CALL")
+
~~~

## Additional future registration seam

tools/export_domain_contracts.py needs additive imports for18 Identity models and Policy carrier, then CONTRACTS+=(19 explicit models) before export(). Existing registrations/bodies remain unchanged. No export registry/schema patch is applied here.
Before implementation PR, ITR081/082 compares actual generated556 with537 immutable bodies and exact19 names. Unexpected enum/helper is failure, not permission to extend manifest.
Tooling seam grants no runtime privilege. ITR085–087 walks transitive AST and mutates hidden sibling imports, Validation producer/capture imports, module/star/dynamic imports and DB/network/clock access. Shared primitives are shape/hash only, never authority evaluation.

##537 independently pinned body digests

| Definition | SHA-256 |
|---|---|
| AcquireInventoryCommand | f5b950d753d9b91c8e05d35cef69838836a17ff2150a967a97c5273d8766eec4 |
| ActivePlanSnapshot | 4f1e1023ece3f3db07bf29c520a5b22ff5a9024abc660ea464f71c769d2d6d55 |
| AdjustmentKind | 926387e1db56c5f873c46f574cb3f6ac3c2db82222f7d95ccdbe51e6fa35ffd0 |
| AffinityFeatureTermFact | d34ffabbfd02fd12add3ff0d7e413d5012b58793fcbcdc5f400a889dc94b98b5 |
| AssetType | a66f35aef4dc931c6d62b0c47f784ce2e1aa479470c1430c9fb5db765b342ef2 |
| Availability | 645d46f93579996c623cb0b6dcc21485ba81d27dff5f9b822269468996415117 |
| AvailableExactTargetProfileAffinity | 7bc90fc4ac7ce5afcf1538727776003b8da1cdbaa4335e0d2ebba630b5486aa6 |
| AvailableExplicitAffinity | 4a8243fe91fc5390711c6f94e866166ed371400984a574303bd7aced592592b9 |
| AvailableInheritedMemberPreference | 5d18eca7199ec8c175206eebeca23f901203ec265f739a5944fa7656822c8d9a |
| AvailableProposalLocalFeaturePenalty | 1ad8296accb170ba9a2e752c13617dd890dd3fec95c74137e3ef4512529c7a99 |
| AvailableReviewedReferencePrior | d899936d0ade5e54f8e67aaa4970e2f6b384bb5bb67605bdb3f16fe70923e059 |
| BasisApplicabilityCheckV1 | 137e2acca07ad0f8d47831df87fb39cf2e9395111c56b60639d0c3f4d7fe5779 |
| BasisApplicabilityHandoffV1 | d1c8bba927f50bb8378207ec18e41a151a7079df8ba4d473238f7ab6a5cd73b7 |
| BasisApplicabilityResultV1 | 64b7a91b0ef4687a150009881dd4cacc52e530c034101a01cc88b5597b4d2ab2 |
| BasisApplicabilitySourcesV1 | d02ce2751cab3eec7257750dc9c6c4d7b181702702b663b3411be15362416860 |
| BasisAssertionV1 | ec848435d14a327c1749fa8c7b1c22c561937451173b7b2d6f260b659be1339c |
| BasisCaptureFrameV1 | d62c19aece1a39ac01d28040e684793ba7e145b38144d4942bd9f5a61df271bc |
| BasisClaimAnchorV1 | 9e74be6531de93bbc4b7d9195e236468407a855968c1aa86f676475f9805e44f |
| BasisComparisonWitnessV1 | 92d12da1e9af1fb0b35ae5b5271b2240b83cdbbec8ba9ef660ec11560937c341 |
| BasisFixtureArtifactV1 | a56a65296135df24fe2cffdcdcbf4129b61e3994e2b1901d0a4e7c3c00ef0749 |
| BasisFixtureEventV1 | cf18efa4b87e74f5e8885fd0b33e6ed617b1f2e752f604bee11fa96684d76abf |
| BasisSelectorsV1 | 8267865c845de2621c3fc5d2f110537209eb827420b2f1327d54ad4975bc57c2 |
| BatchFlowLinkDraft | 2017366620421ae6f327d380988073c657cf0956c081c2f5f4a6bf1a965b8c5e |
| BoundActivePlanSnapshot | f9468eda8c3a75929e88e04d88cf277db130061d34feffb7628382c318479f2b |
| BoundCookingBatchIntent | 15dbc9c83660bffbf763f965553507f89dcac3672e676988588762a0463ba6d4 |
| BoundCulinaryFeatureContext | b111e737561d94658d4b64c3af7bf2128cefe19b063203ec1d99418a677caa83 |
| BoundPlanIntentGraph | 4d137c8b6526e984b4409a6593efa7c7de9db1f168283d141e350652a288f021 |
| BoundPlanProposalSnapshot | 0210263b11d570e24e5439e0c08d70c99cb1ebfa37bde5ee13aec4318727a593 |
| BoundPlanRevisionSnapshot | 5395a29bad89c052c84422bba71bb9580f0e9a3cd5bb1341fc7c1a856a65d383 |
| BudgetContract | 660722f0ca9f19c317f9eb92cb51c53f272fc08540e7d43f0bfce19ea62e796e |
| CalculatedNutrition | 60c98f31deb13c84e0bf3b0f15670eefd23976f6e6a9f1759f29c0064bbaa71b |
| CalculatedQuantity | a91d193ef75fa3e54a01f8c9b4ce72e8dcfe1e5e3b74aef643705214aaee2c8b |
| CandidateFeatureBinding | 7c402cc442a66d50ae74ee3d6c56663a5c286a9faa935b100315af400083cc86 |
| CandidateFeatureProjectionDraft | 5a9f27ffcee94ca703d1ada655d2ae98e99e306bb3608118fd858d1c78c21edf |
| CandidateFeatureProjectionRequest | 100e748a68626123187b40f7f675c711d815e72e7daba2da6a5d8734561e291d |
| CandidateFeatureProjectionSourceSnapshot | 57968bcf54158138c2562d86ee6ef32506a73360e0541dbe916ba3e7bd0da919 |
| CandidateGroundingRequest | 3c5fbc1ecaba91c049a18de05705ef6ff3e28e0cbdc55c410018ed2810a3d5d2 |
| CandidateGroundingResult | 24c32eefcb795d85bafbc9501c12f984c9aa272e3b8d4d10f8d6e93277906533 |
| CandidateGroundingSources | 32a262655c3142c074d87e499d7fab9b48732c980ccb8553b99ff3607fe7a96b |
| CandidateMemberTasteFitDraft | bbd326d554007f1951ea28231ce8bf20196ff66c39e0d51563f25005bf693fb0 |
| CandidateMemberTasteFitRequest | 960714afba0c4c6160bdbdf4e286aae8315e863282b37bfc64c2922b2d1dad6a |
| CandidateMemberTasteFitSources | 934b14c160c95e32724c2c12445b0725948692abe26d5197898b734d9a1ba617 |
| CanonicalMemberSafety | 17a14b98d9a8c320c919222410605aaf0e4fa82537d00fedf01f5980337284cf |
| CanonicalMemberSafetySnapshot | bb95c14ab788e5a256d80136349762ab82f6586397d86a57ff43c2e03276ce7a |
| CanonicalPreferenceTargetManifest | 5e2205e287f603132606d9f6f9752dca1995d00e033e313695e49fe5a9792266 |
| CapturedCulinaryFeatureSubjectDraft | 8227eebda1878f85ef90a751c1328ac02116bb9d7b1caa5571e6d430d9e52237 |
| ConsumeInventoryCommand | e292d1b3e9c68dab471807238dd543cbab59e13f1203aa6533790d7311dc2c1d |
| CreatePlanWorkspaceCommand | e21d0c9269688ed191f27c51183fefc5a233c78492f870bc92e180d965c3be03 |
| CulinaryCandidateDraft | 50b37076347f275f73ed76bc74fda356baacd9fed964565a5710175ea09f016e |
| CulinaryDemand | 962923bdb4347a72192c7ee42b4bd49f38a64ccb11a2983870ec954b8bf58f71 |
| CulinaryFeatureCaptureRequest | 910df125b34649e63407d6b93d366d3913d465d818fa58277f363d6b35d528cc |
| CulinaryFeatureDiscoveryDraft | 587b91ddd002451bdc65faa3a6f4a723fa5d9887dbb9c0c42943d02eae130f3b |
| CulinaryFeatureEvaluationInput | 21a29404595d4825ae671cb339d20081daa509d54086b64ea37cd3626c399dec |
| CulinaryFeaturePathKey | 24424c733da90b62a6a54b67ee2ca4788bcd867fa38c725b87e5496ce673f0b4 |
| CulinaryFeatureResolutionDraft | 6c7894b09eee615489a037985f7fdde93ca35f3d9c3ca0b46febd7c1e2a821ee |
| CulinaryFeatureReviewFact | 26674f2a77f5ba2c8bbf5fc472ca9e544effdd247b8631ebe7353fdf7aa5d6b3 |
| CulinaryFeatureScopeFact | 6501cca50aafb84f2a7f72ec160c281b637d39d6e52ca3dd76583b31f8b399df |
| CulinaryFeatureWriteReceipt | 6fc290aee36cee1f3f88410fc1beedf4f8007f0837c9e78b22c7d5530c4cb2dd |
| CulinaryGenerationLimits | 35ad9dc56643a38d2b6f3dbb2585be92f14432943d9d7e7ce5e1008344c35285 |
| CulinaryGenerationRejection | c7ca089004650f3887cd167610a732e227f7584a38aaaf8c261c415d4ebe0ad1 |
| CulinaryGenerationTrigger | f6ca6d5c565a96bad4f7567370282c979312af7997c471c4c4429c5d43a6f779 |
| CulinaryRequirementBinding | 9c10cab97842aeb09bb660cda642591041d301ab3aaa1fbcd59c231629b99c8d |
| CulinaryRuleSelection | 7535309a158f7f27c42deeb0aad37aa8f75c2329060623b8ffb9da46c1faf40e |
| CulinaryValidationInput | 6c10a3d6f034e164fd579f0685a209f847f8574fbdaf4180d33e346873d474f5 |
| DefaultBatchInputDerivation | 491dfe886aff2dcdd116683ec1ff318e5eb417c32c677fcf885a0c1feb1113d9 |
| DeferredCapability | 5b1496ae956f1cf548aa5e3c5f860e1e5fe799f1356ab05a14e79cd95e9ca3f6 |
| DerivedExplicitEvidenceStrength | 1803d68cd18fdb91514980dd7254a5698ad14b4d320d589ad2be943fd2ca659a |
| DerivedTargetAffinity | 13e88660658d3d34cdd9daf54e4315f86487e912a211d15776a917ac4e1177b0 |
| DiscardInventoryCommand | 0f50bb97b642dc0a025d84de3a33dd59fc20e2ba0ec6a630c6441ac502ed7937 |
| EvidenceKind | f8ca80e735e526648219c1fcf9f37a5dd75d3688ddefcd91ba4d5da17537e757 |
| EvidenceQuality | 5cea2d8a83bbb6bd6fc13430ef2d583bfdbebbc1577d315ddf48464e29e04562 |
| EvidenceStrengthShrinkageRule | d92abb9c11f65505b634436a0ff3a24971959a77cc3906457901c7d6d42f1195 |
| ExactTargetPriorBackedAffinityDraft | 665679c3e4933dd08182a1867dbb592037cc1adf82bfa87b1a1cd34c1aa3026a |
| ExactTargetPriorBackedAffinityInput | e771f560d438141713d46747d4e8a2b33ea673ac3e8753772426df2f984287ee |
| ExactTargetPriorCompatibilityPolicy | d9e337999afbe598c84811b180385c97e7e69b24fa809662b50372c5568ca668 |
| ExactTargetShrinkageContribution | d1e01a332c177b1b81f5d72d453c26381eaf046511fbd56b48c795b1c95105be |
| ExactTargetShrinkagePolicy | 9f0bde407bda2925d30f54b652df97cff6743e295899901ed20e79a9733542c6 |
| ExpireInventoryCommand | 5446a52f84ff981d504200c50659c0766463d0e0272660cdaea95f90d73e2733 |
| ExplicitAffinityAmount | 2c173fd7341a8a51d43bb015b4de75a238f7bc65a3ddbc9711d0d281813b4e19 |
| ExplicitAffinityValueRule | 0abeaaf25668135aef4b0d3350f84cb0fde8380cbb0d23b7f7a36b6c487897a2 |
| ExplicitAuthorshipStrengthRule | a8c631df2f389b3bb9afe1fcec140ab7edd70ae3e72524ec196bfb9bb248cc12 |
| ExplicitMemberPreferenceSnapshot | dd6c2df8fb6e5654b6bfafdeb81cec33318a0b67d63b39a8f9a22b1369c2c4ce |
| ExplicitPlanIntentBudgetV1 | b3ee8303cf860fad10b3c69f15d51ccbfcc249ead4358375ee2445921b854fc1 |
| ExplicitPlanIntentContextV1 | 9c7375bf609f165e9ca71785608c600489d2ac66dc4a40e7ebc85057f2902a89 |
| ExplicitPlanIntentRequestV1 | ef84d63e54dd2b6ee1fae7e9647f02fbc22c0e6aeb05062d45f3ce6bcc47d5b4 |
| ExplicitPlanIntentValuesV1 | 05b9caf1c169d5f9b656335d7f96580a6f11116408f6a0ac2ee13bbddac3df98 |
| ExplicitProfileMappingRule | 97867e1db3c73b1f15faf0bbe369ad6e67b8e72e5c3fd6626869f6792977a57b |
| ExplicitTargetAffinityCaptureRequest | 68b38cc9d4e6c5e9856e7a5a26c305cad1e1c4596f1931440631c1687459ce95 |
| ExplicitTargetAffinityInput | dadb194b10ce6516dda5301164a781f57317332e307e3b2d3e8d12c5614434d2 |
| ExplicitTargetAffinityPolicy | 689c160b53b91cde9c08a64073faf95442aa9a791da1b0959b9449c01bb2844e |
| ExplicitTargetAffinityProfileDraft | fb73ce8b0267b0f16f8f49755b4554b84727188499b2733681f7019415e75345 |
| ExplicitTargetAffinitySourceSnapshotDraft | 2ef757ebd855caf665ff88303405f636a60d634f787b7f8399069d1baf7008d2 |
| ExplicitTargetKindCompatibilityMap | fd305e205d53cf9b633868e8f5da4bea34980289ca627b7b9ba895f3390e7524 |
| ExplicitTargetKindPolicy | 4238c3e24f03ff0bce50706ca7ff17c2ef08d57a118dd4a62fb260e090c0e625 |
| ExposureAllocationSupport | d4f56fb4cb4d9741facf7d221a36e58dcbb6b02fe5c7026542a6910f65d3a207 |
| ExposurePreviewPolicy | e12abad50a1bfd75d1a8877d0c789c3d70c96cbe91d4a365dbdd991493532dda |
| ExposurePreviewRequest | e04aa633c895942b063e718033a8abdbc761480c8610c1cb70a7b36e8dbbafa2 |
| ExposurePreviewSnapshot | 97ef6155dfc9ad8483ce83182a0354dc7f8c59c68310fce06152611f1450df51 |
| FeatureCooldownAssessmentDraft | af5b3fb6e4d1657f6770663d4e9e23e449e798e78863d2152d2f617d70c437ae |
| FeatureCooldownInput | f164de27fe4eb88cba549c5c21191b146fbf0bf8bf1c077e04165d4e21358402 |
| FeatureCooldownPolicy | d6c59da978e6f192e37056c5b51366fde3b4f0a791f3aa0aa6599871af9a6264 |
| FeatureCooldownWitness | 0a76b238f3bafbd89e537056032538e96883fff5fa25b755c983ea2c4d226282 |
| FeatureDecayBand | bec3c19d0744468fb4fa2517e0dd58132cc8837bfaa4e49d2bc2ee121516998f |
| FeatureDecayInput | 9049bd1897956465751ddfdf1d4f1f326fa4892155d189b9b3b6006b6011a8c7 |
| FeatureDecayPolicy | da8542e3446b3f6ebfe9e68f54ccbdd913175152770fc8a27acfc984bc72c952 |
| FeatureDecayTraceDraft | c768fb4255c7b2ef2302a93f43094a92b0284d2576a5066f4387dfef363899cb |
| FeatureDecayTraceEntry | 9c17d42e8b730f0aee51ad981c1f26667a036985ac2dd436eb5eb4f86b8402d1 |
| FeatureDimensionDiscovery | c0d5b0765cf8b5814da25307a8c996f77bb797c4422f7608660cb46d24a88a0a |
| FeatureExposureAssignmentRef | 7a62753a2398b1c634b48947c191a1962462b040e0f9dff7d5474bdc06d5b950 |
| FeatureExposureCoverageDiagnostic | 464c2e0f223bfd4d2e45aa714c13909ca3ac93c9acde456778e86af697c3f911 |
| FeatureExposureEvidenceCut | 209949cfa462c71c99593b5a6b1122ff6785283af11871b4e35e098abe0af418 |
| FeatureExposurePreviewDraft | 162c038271a15939db4efceac445f50608a8a1bed6b858318086d5cbdbd0e9df |
| FeatureExposurePreviewFact | e6ab0491cc1e42b27e0cc4d76d8322ac25a8c0640adc061fd39f984fd075a53d |
| FeatureExposurePreviewRequest | fdddbff869633633123341360b9b190902baeb78c0f856e8fe783933488dc401 |
| FeatureExposureSourceKey | bbdc18d464b55b5876f007925ce2c8631a2d65aab6c9b7e8f94414f8f3541dfe |
| FeatureExposureSourceSnapshotDraft | 60984a1b829cc9845ab35f96a37958cf82e36d8f1baff381943a131f51641ae9 |
| FeatureExposureSupportWitness | 67a1d4114f4cd12e2c9f4f28c2e24938afbc1833ef60bd32ff8b99135a0348ba |
| FeatureMealTermOccurrence | 746fe34b1c6e1fac69cb65a379419113cb6d7f0e59d72262e792649e506e12ed |
| FeaturePreferenceTarget | 9c551b63f6d684f7bd0a7347fa62fd5199bccd1350679137c2c977163fcb5ccd |
| FeatureRepeatPenaltyAmount | f4fd3677563d2dbcad30d3853cbe2192ec6f6b720e685d979bfae03e2d678f07 |
| FeatureRepeatPenaltyContribution | fb8852704291d8aa831d2fd4b1d6dcc8f225b0b545125d37e7a2459ad390e18f |
| FeatureRepeatPenaltyDraft | 8e2dd69118a4abc4dcd3c8f620480fd43eaaf97dfa07beb984db4ba5ab3f024b |
| FeatureRepeatPenaltyInput | 8f3a3f6e946403900af2ae30947e1def46565ea8e45b5315c5d5a7c7a55339c3 |
| FeatureRepeatPenaltyPolicy | 52f72bb63511abc2c18980a5c65eaeef22901f9a643740bd6c598fe4d3d18e74 |
| FeatureRepeatQuery | 4dc49817d846a2a698aa8dd95808f975cf39a5436f2c64df9958fdc243a2a150 |
| FeatureRetentionMultiplier | c5f7f0af5dbcdab8b27e8b0e15f5169864dca47801135e077b0b848797ab0767 |
| FeatureReviewSource | 9366718d2c3dd35b29f7b36674230c4bc70cde65f952fae77fa7080e58ebb143 |
| FeatureSelectedPath | 470f923befe312699b08fb7d40ec116990b2f4debd024f414f810d6e74e067dd |
| FeatureSlotApplicability | e84bf066cae14f8366d83538fee13d46ba0067fa673b34f38a683cf3f42841df |
| FeatureTargetManifestEntry | 7239dc2bcc28edf627cd2e774ed46d7853de6a07aa8413265fc09d15efe0927c |
| FeatureTermCoverageCell | 2906336950651c0a5d31af9726e36bb6faf71ad6b74dcdad38a31b004ac276ee |
| FeatureTermQuery | db58121395fffcbc4e3247dabdb01e8e75520f412b67d2ccfc42848701f62142 |
| FeatureTermResolution | 447f2c4256700f538a9f537d798b48ba1241f801cb47ec2c0d154af2269e6530 |
| Granularity | c9c925333b0ec74a586f49b99a90eaef110de031264d7cdc500c366265cbb6a1 |
| GroundedDishCandidate | 3e7aeb2b069a655068d692b038087d8b66007ccaf95e9bb2529e8ab8c06d184a |
| GroundedIngredientFacts | 2eafe48c2208d1053a54ad5d0b646b1d9ec76c1476ab6dccade06add42bd8954 |
| GroundedRecipeVariantDraft | 4fa92df7135e768fceedc107cec6fe0891d7e4d7e65ddf7f35fb6e43217274ef |
| GroundingIssue | b50418bf35715e8ee537467e2ef7d455b8dad286b867825af273a062a0cd8049 |
| GroundingNutritionSelection | 4693d60e7ee824270d3ff94cda3f0065cd16a7d20a6d9f7fb33955517d1a6259 |
| HierarchyAuthorityCommand | 69b28ccec3162b7a87cef5598d25c28c50bf26ed142c149fffaa6600eae76124 |
| HierarchyAuthorityEvent | 04f956bb9d5775b304bbda764ed17b1d6c691fe6b72627393bc89b836f2b00af |
| HierarchyCaptureRequest | 131ee63331ce733ddff82e881a167df7093b7b82619c6740e2cbfbfe1e7e188f |
| HierarchyDestinationSource | e8a77579c33440101000fe502747c33fe1fae183881058211e7c98f9500b7bba |
| HierarchyDirectionPolicy | c6f2b230d41f3f23ca6c28a92f0556b1c47d19a37de4f77ba4634a4436135acc |
| HierarchyFrontier | 592d1b38747b448abd9a7de635cd159d6baf113fde0f6c3d4af41129e47b2f21 |
| HierarchyMappingLookup | 644c5b4ca6b13bf1ba1fdfc4cf6114ff9a8c68ff943f6bab30acfb7b4f1c6fbd |
| HierarchyMutationFact | aa134a84ed20d6eafd6e4d86eb5637b989aa17a23dda6aad5bc5d34da2bb7ece |
| HierarchyOwnerManifest | 37e7fa0a40b0238f98f1628dedf7ed1d4e2a91b0f24d661d17951fc49e466174 |
| HierarchyOwnerPin | d20e9de7749dfbdac0fabdf3cba5a9369ea2c32a7bff1bdb61f9ec95fe8dea31 |
| HierarchyOwnerPins | 24538fbff47f08e0c108e29d7a218b371cc3b40309e793b89a421a607e98a365 |
| HierarchyPolicyAmount | b65a55020824de1efe2e1984994f4942030a7b6e018adb84478056ebb0a55b0b |
| HierarchyPrincipalCommand | cacc420a76022f8373386082ead485c4368e40a911643591590f9539bba6c74b |
| HierarchyPrincipalFact | 78bdb246d33908a5454fc17ebb950ca3b591a236b5f5facac7eaf349a1194a6f |
| HierarchyProvenance | 7e5027f704946ec3a79c8a590f400bf5556bf8734e06c41c21b5408ef6d79674 |
| HierarchyProviderCommand | 4d849f7bb02a2ceeb30e760ae1389d14a555120407d36a1bf5851f1400cd24d9 |
| HierarchyProviderFact | 2142e769b6c667b52b1f5a028e33cc63b3f6e5ee9019dd384b6b36ef88de4a08 |
| HierarchyPublicationCommand | 0694fc4cb904525ae52595b5ff2f18ae8ed7bc325528b225f4ba8465bad27d2e |
| HierarchyRecipeBinding | a3c5932619c5cff86d38786a71aa7b6df15b65a35f8b1b509b9bcef5d62aa1fe |
| HierarchyRelationBody | dbf6ddb7ed256395a6480ee7f1b275d16a60377127fb4e052a1cee8c8310e44e |
| HierarchyRelationDiagnostic | fc796d2a9d5ac5fe57867c36fa9ead54f4bab5d400f417fbaf72588651e424bf |
| HierarchyRevisionFact | ab66790d3a7941ea23a1ffff16795036a9404bb60dc2930d78dedfa115103e8d |
| HierarchySessionFact | aa5ce04c7447e4658c10876257a1e267175c979990daf1364da9223df1106b23 |
| HierarchySourceSnapshotDraft | 28632a3aa610e08bc5063041a6082676056ee585d126a5401f1c4ab4ce99febc |
| HierarchyStreamFact | 7c712ac6d86f6547b472ba06724af1dd77ca67e70b48e34ea9fcfdd6d3d8dc04 |
| HierarchyStreamIdentity | 07b14768fd69631d01f9d4eebe985274f59e0efd6658ac76e4c113b4a33d4918 |
| HierarchyTargetIdentity | 9978bfd0c6d8f82d6322fbf1c3db45eebf80df1871acd11f0ed283843de85824 |
| HierarchyTransferMapRow | 87b019b8e55df03460ba85c9429a58441cce1bb024b9d7e016e45b4b421f7762 |
| HierarchyTransferPolicy | 1ae7d14b812022b20c9a7cb62f38b18a89be00e85ffeabcad3c5b1f8434c1576 |
| HierarchyWriteReceipt | 7959b5f8049148f8c0005592908621c8013a4f873dc363e97ed0f65ccec76c62 |
| Horizon | 7282b542052842ba5abb38c8ccb1327c0ca4f56c1b1afed351128cd925e4c6f6 |
| HorizonCommitmentsDraft | c0af7e366899e243f90dc105e76e09a4eb955bc7dd1ba0f30b5bbac944ad5ece |
| HouseholdCreate | 42a4f0b8fd8a760b574da0b268f33e878eecbaad4e85a5eff418f03f41d2b636 |
| HouseholdCreated | 3b1b691e0d05150d514b9fe92ee40035b1ef9f3d8cadecada0fb5b0249602bf4 |
| HouseholdMemberIdentity | a2c2f0e36373840b55aa23fbc8b992c94dddcb327038a002cd3c827230d78456 |
| IngredientCreate | 1ceb913f05a34bc8210a8cc938a8bdb13345c373b6342590e130962456bba169 |
| IngredientIdentityFact | ff2fb5d23c25a7d38177ab77f59b3bb1762a55f617d7f01d9bc1b5fe3a0d1fcb |
| IngredientPreferenceTarget | 5eec6f9df141730317e372af3675dfad33e159ec76303b0ee5019ea2b6ad8a4b |
| IngredientProductMapFact | 48ca5f8b713ed0e3f71c8426cdcbd1ea7d98dc5fd2ea0d87e6481290296de87c |
| IngredientProteinReviewCommand | e97551a877997db9f72fbc4152252e71f8ca8baeab6bd4a3002890a18c4cc426 |
| IngredientProteinReviewFact | 40b82dd25a17d23feb973a6e9e91deb6eb81c0ea92a8065adf80d504f1c744b3 |
| IngredientProteinStreamFact | 6da5199cdf600fb871cbe444625eb6f34c80324e5d0c9ce8ef573701c7572aa8 |
| IngredientProteinWriteReceipt | 0857cc425b65d9c30e00b0a8a69a4ffa0272937fe71aa412b779aefb07317316 |
| IngredientTargetManifestEntry | 8420640d89db76898211aa193e9961131df0af9b93533f8a01b2106b246c632a |
| InheritedMemberPreferenceAmount | 8f1b8731cf294cd93b921db0d741390a1e151a3116a5177950dd718ce3a47ebd |
| InheritedMemberPreferenceCoordinate | 378f7a9b01d17c183a20d046b212c2e1fe758f7e07e5bd09740fa5f298209d4c |
| InheritedPreferenceTrace | 1f28b5d55e810f95dc757ac0522c94ad4d0af0a0a3132d97218d6d64fc2de20c |
| InheritedTasteFitSourceCoordinate | 96d5266e8b906855237b9e2097c7457fad2b29b4d4946ed894ffc61b752e789f |
| InventoryCandidateLot | 125e09b852cfc1d6d299e803ac75857cd524b390549090f19fe6df004f103bce |
| InventoryLot | ead925b10ae7c30d32233442f9e8a676df826a96e47cd6869394eb19ca7c7ddf |
| InventoryMovement | 10bf1b3f94bbdf63c470c281a85d9b1875720e08ee606d0fa99270bdb86d210f |
| InventoryPosition | f9a4f70fe4d7a4c932669fdfb8802b863cd368081b377b23cc80c82a1e151f45 |
| InventoryReservation | 84066a33c46178c4f59fa7dd52619bc255604f9f3c55b8a5a0541d352314d057 |
| InventoryReservationRelease | 80fe49b87eb9a09c470b64dcd688eb73eea19e56ed90770f2d9fd8792d402649 |
| InventoryValidationFacts | 4c70f063805ab8da169242d0f1a665c5fa0e687148e4162e7e91df9578c77060 |
| JointPolicySupportV2 | f6d0d0396b35e179210c5872c8d3620a34f98d76ec7ffe4cabad6f157e84683a |
| Lifecycle | 8368a188ac347a12f2a6df432161458d2e254e050493b3ed8fd78ace78de7400 |
| MainProteinExposureFrontier | 64a81d429fe14ce95a329641f57612243522f77875d80aa7cd36e1f8ecf5b31a |
| MainProteinFeatureCommand | e1f47e2fadc42c9a8a2ac80e0c4331d30262b7fe562bc24e612660163d9ec479 |
| MainProteinFeatureSources | f7078c1396071958b083403739f981a1ecce6f30f1e5f106e99d47b72364c9bb |
| MainProteinSupport | dbf54d033ec128235e0e64ac4ad70ffbb238968584ecf4d6d3a3e715294d7d3e |
| MappedExplicitProfileAffinity | 7ce2d3f8733d958831eca28c531a9fc2a9cc3259381b6fd56f4d2853d8132abb |
| MappedReferenceProfileAffinity | 73fda7e407dea9dc5a579ff730cf0903e5738f3c7f4449d9944efbc04f53427d |
| MaterialBalanceDerivation | 5216b7d6792aa50440cd6aec77f39f6a1e630fe0cb263bcf96528260545bde80 |
| MealIntent | 67b39cf2313c0e38ccef95cf21c29e40765d8097f34bdc36203ef881200b42cf |
| MealParticipantIntent | ebc5580f4ceeb9f16122d1d76b9320b1b26cded2d11d7a47a15e064c7776aded |
| MealParticipants | dbf4de21bfde4ce92b729dce395e8a408fb42e2ef6ad1ae545540e4bcdb2dc46 |
| MealSlotInput | b8274337df46713f9acba20efff09555c57b385275a03fffe97d30447636442f |
| MeasurementBasis | 500c22a9f99d748e0fdb6d48314d98264d76e9328d63322a8415e4119f73ec02 |
| MeasurementMeaningV1 | a581dcd650712446f1eaab45a729b87957fc27732e07ef24295bc349a4666278 |
| MemberNutritionProfileWrite | f5e9f2f53a40ca198d23eb1bcab4b39dbc94b9247031315e8ac1d2d535841581 |
| MemberPreferenceDeclarationFact | e3d7820e4332d7eb8e4629422d7e04e668ec94f3ab1813c240dc45b116013f21 |
| MemberPreferenceState | 35a6d668c0a5dd2a8b171a4e4f1f79424e90c5e70cd9c99cddecb93cdfa721d8 |
| MemberProfileAffinityAmount | 08b25e7517ca3da9ea2fd611c5cd010c461d3dd52a26d091c73fc09e7bb56d74 |
| MemberProfileAffinityCoordinate | 32b9c6982fad0f763f7f90303a00915ec1af5236b83a627b8e15e2fa25663f76 |
| MemberSafetyConstraint | a2ef465d03eaa858a9066ebefaadae0b92e88c496aa73242972f0384bb343097 |
| MemberSafetySourceFact | ce96ae1baafd1574b6086cd429d3701ab33e8b50fea455dfc5c88d29b470dbf2 |
| Money | 923fd08c417aca61660151ff1cef1a39623749d81147159ce78eca91f5841aa2 |
| MovementType | c27a30e8129737391fcfbb02433441dae608ced65467fa0ffc23a82490e817c3 |
| MutationFixtureDraft | 9545629510656661e1712d03a4aead42e84770d62de35a220fe9f6af54c51be5 |
| NreCaptureFrame | cba61d3f42eaa8846e46dd66543be06ec149aa46e8ca70519a79d225b5740afb |
| NreDelta | d5ad9cb1a6e0c8c82a08ebb8a81e5951cb42603d830a50b95f128005328cd66e |
| NreFixtureFact | 87a403709c9c796f90fbfdee712f16f374e1e73bf3080647c239bebde9d888dd |
| NreIngredientContribution | 7812a68380c4ab06dffc1a76269015daaeb66f99efa57ff13b1be81f0b2abb2c |
| NreOwnerAbsence | 6ab7a07ce70a7dc9087174908246ece373f7ed4542874340c75f139962e4a6fb |
| NrePeriodVectors | 5f4cb801a73bd39029cbaf9ff30f589f64e2d3ecc2116388163e8849aff4990a |
| NreRational | 2b04ba861d5d4c3d27ab06867f7295aa064911f6b6c2b495c453731e376368f8 |
| NreReachableVector | 11b5dd00c374c97f85b08e09e8499808746f616bac81efac44665c784895eef9 |
| NreRecipeSeal | 1d2d2a2fe55ebee865b2377439434ee1f8c4480530c1ad2a923eb596d9139713 |
| NreRecipeSelection | 6e6c5052d060c058a421376e3f25a53b44b26155025b070cf77b8b0f80962dcd |
| NreReferenceSelection | e87ce055f706cd10c7d7907bc4e24a5af5f10aa230c949ff4c2ae86dde406cde |
| NreResolutionGap | 1ae49d82acd1d3d861d6640e5ea73ee29b16933f1f2fce4484bef3cffb36183c |
| NreResourceProfile | cc666c37b5911269d9c4e297792382aa00238f8821e7ea9a8e6796f09ff2e574 |
| NreServingDeclaration | 867c92e60d0a5eb04e2a118b331bc5997e7a0760d4f6885ee97aae8e1067a5e9 |
| NreSlot | a3410d95fd35e7f626e15e0cbac6937ed1985adb6e5def80a64f690d544c6d69 |
| NutritionAuthorityCommand | 44b4daef9abc8a491254cf73210621ada67ffaba1c8961e265689f8fdb4360ab |
| NutritionAuthorityFact | f16c1b2569f196431c1c8fab6dfa26a1d66cfcb6279f3e66c11f39bb9056943a |
| NutritionAuthorityScope | 03a81b6833c46eba8a79eb7da861ec4c219b961ec3a1c2c02081f9af25bd4556 |
| NutritionCaptureFrame | ec1c3ec3417d2d7f83997327a4e36f8a0aaefd3a37537a3c4bd3935dacb92f2b |
| NutritionDelegationRevision | a6f4948d5de4121d41dcb9a1bc8e72c52b21ad0c87e36310905ad4bd6a913fb9 |
| NutritionDerivedContainmentClaim | b406a124babe82bbe955b2dc1c80710b2586caed3d71abfe76e4a0f86ca64fb5 |
| NutritionEligibilityProtocol | 135d7e43e2a1a8281b5fe56a00036c4883f819c9f3b7507a42af032e25098bb8 |
| NutritionEligibilityRevision | 851c4ee17268c282c2e731b1e2cd7ff963c514d7a7c62206ee27d5ea3bcc1ca0 |
| NutritionEvidenceRequirements | 26ff4e5ef74973cc4478b591357e2698f89f9a13bd9ff2fabbe877d14d994296 |
| NutritionFact | 70626ab80d4a7c10d2d903f2a43a4befb33af23bbf8b121b36a002e590d76c9e |
| NutritionGoalRevision | 3c2e11c860eca4df6000a17a34330dcec17972050ec313ed8d4761cf6a174024 |
| NutritionGuidelineBody | 90b1fb51c2a20e9fc1b6ca2861ea87d5d300cd460376fb394707a1122e3827e6 |
| NutritionGuidelineClause | 1dec52dc74765241dd058343f5db9cee7843ba956704d7638fd9dbe03d49f388 |
| NutritionGuidelineDraft | 426c518ee840f62e44965add93971c756da7252925671447e200cefde00e40d1 |
| NutritionGuidelinePublication | 3205ee51809904fa54d057b07dcc95ad659eb43e1da23a4df0209e99ec66f2d9 |
| NutritionGuidelineReview | 0087aa729d2771b9466a08896e746dd419c7ce745039eefbacb4bd8318608e8c |
| NutritionLegacyAnchor | d24ed10090a649a6e66e035b324d0087e9f8ce8f50b3142eb39b437ae1c26384 |
| NutritionLegacyProfile | 07566a7cda564b893e783bf59a658177afb59c01fe680eb2ffaea12783a9777c |
| NutritionMaximum | d13577c5c827bf9f02612a167266c3c585e574500c1935eb93d4474546250bb8 |
| NutritionMinimum | 69ae495ea5de5ed33b8994c6fb7ee75245ce9f0bed029550625411df68867311 |
| NutritionObservationReference | e7dd3c8bb90c41468cef2e6b4e0f88dcc2f3e2d8c59cc646688230c681659615 |
| NutritionObservationRevision | 4eaa12c7c3100b682783259ffa5ce96d4bc1275b529cf093f6c64a76c2781d11 |
| NutritionPolicy | c86d5289ca8c723789d8bee2f9c6d3d0509ae27c7a73d756b54469a9154aa505 |
| NutritionPolicyBodyV2 | 02e70e9192b699eee9042beceacf14ffe30fb0386cf2ed31f4e67a5d7728eb8b |
| NutritionPolicyCheckV2 | a41e959fd913926397addff8c76d332ce55defffaaa5c71fe48b2c613b0afbdf |
| NutritionPolicyClaim | 48785459e5372211d469fbac9caa0b00ced2fa20c1985e16b9527075475907b4 |
| NutritionPolicyHandoffV2 | e48825a1d5875922ebdec4bad99fdd1d749308696287ed6b9fba838460ef900d |
| NutritionPolicyIntegrationInputV2 | 48f098fe46a696a79ee6e08a462e6f8cb35af0314b8c115c9de3358b743e9b50 |
| NutritionPolicyReference | 290d3d387ce5f2a5b177344b4b19e41cb90fb8311424926b2d811e0638278c33 |
| NutritionPolicyRequirementSpec | a8695bf3fe4313d3cd3950a2a97da77b847e29b883023c3095ff58fa20fd938c |
| NutritionPolicyResultV2 | eaf3b80bf5e4f376a5f4b07d6766a0b493591f4a88c738f63f994ab86ca4ada1 |
| NutritionPolicyTrace | 169cedf4f333bf27a6196084c1f57f69a886df32a183c58a855dea4b94c3adc1 |
| NutritionPolicyValidationInput | 6704093bd1b6bc0729d4d6e0a7ad230a0d21474fedb548fd873c3c89a0bffcae |
| NutritionPolicyValidationReport | 2edc358b6aca5ea9b21eb2dd7fedee861c8c2a11cba5657a086e0efcf6d8d37d |
| NutritionPrecisionSelection | 91b672b5a0897a493da80143a5cb3ff5134eaa9c97a0e1bf4cb1042e82a4a726 |
| NutritionPrincipalEnrollment | 98ff8daa3386b72798a8cc2d9dba8cc9b28881fccf17de9ca9ca8e1d5568759e |
| NutritionPrincipalFact | e2591f272d57093435c840dbebfab277f7c7dde18be0dd04df01b095bdc87457 |
| NutritionProviderEnrollment | c50e6b3c58bd99788a695aed0495d8d07857e58b4c2b448cd549862c93d2b2cb |
| NutritionProviderFact | 8d795d5a2b09e52634023db616d960146166340f5dd20f956696000ffedb42c0 |
| NutritionRange | cdae9c78c5a39e98cde6fb0ec95145dad87f3a0fdb830582a549a44e135e8d95 |
| NutritionRecordedSource | 1c48918ff84811eda7b844ddb484da67ec42811641b8d26cb9eed3f68094a63b |
| NutritionReferenceFact | 880bd37715f0de3b6862b5d0d427c2f82dae193d706320cec06577a6937cc0d4 |
| NutritionResolutionCheckV1 | 7c854cb2fb0c6ed58fe1f56fec5276592caa3e8f7c091f59540d2a7b2e2b8241 |
| NutritionResolutionEstimateV1 | 98312fa5e56aace647993b9da0468b70f5286b4bb71c3bb6a0d6e15a04db3ab2 |
| NutritionResolutionFact | 9ba3280003adbdf9510bda4bd9ea3ad86284b5d61daa9a8c1e8f44edaba4a162 |
| NutritionResolutionHandoffV2 | a8ba700b8e8cbf9ad33a11ebde9c4038e0b4a40fc2e9e9af930e036ee381aded |
| NutritionResolutionInput | 281d35e92fa2e7621c4088415b558955f727a11cecb08b139d1b83e7bfcf8718 |
| NutritionResolutionRequirement | 9b2fd6994f6f6953618bfa0a98a901e40eede3c947040521d06802b636553ebc |
| NutritionResolutionScopeRequestV1 | 69d48c17be19084987c25cf0516e327233f6069e3c62af377247cbd62d40d39f |
| NutritionResolutionScopeV1 | c16af7d8813c9addef26e0d71e43920acf4480fc4e46e49e6a17c1c4f18f6847 |
| NutritionResolutionSourcesV1 | 144e857483b748fb6c29722de4e31e88dfa7c72c98b3b0cb495d91c7145ed309 |
| NutritionResolvedRoot | e84cf1753d5381df562d273df0a85d74b3aa069ee73648f5ae29ae3d7940ae1e |
| NutritionRootAmount | e800dcd56815907c545ea821eab2c1b59570189cac3b87691870f026bf20f984 |
| NutritionRootContract | bbb8f5e705841c3ecce87d7bb671e91cb0beb3d9a94c76379d29a4629bf40bf0 |
| NutritionRootDescriptor | 9d89e33ddf04b2bda301ade7957f305ccd2e45e955516cf6d33ae05ad67cdbf1 |
| NutritionRootRequest | 4c4f134d0c9f4eacd983f83131663fcab99fca681ed493915922552ad7e4bf54 |
| NutritionRootSourceSnapshot | cc2734bd964d787042390a16f7f039d7f25179321b1854070b04c0a8fa42047f |
| NutritionRootValidationInput | dd2ca4e5d40e0cdae999e414640716a14026031a19db246d46fa4e70c5a3c2f7 |
| NutritionRootValidationReport | 49697ac3d39df0d227115ff735f86073f4b5b352c747d0218baa0182417584d0 |
| NutritionRuleApplicability | 4f7dfdf8c23aa3fd10c636a542861af4c8d04d71f74d962660ffd243adf441e8 |
| NutritionRuleCase | 6ae36c57f4ca48ba39782f011544b1b7b834a035fb857114acda3db1a7ae418a |
| NutritionSourceCommand | c79ea83ce6040332008d7489202c6bbfcf87d7b4290335e854275840afde04eb |
| NutritionSourceEvidence | bc99f897647478dc44f8016e7a80da1e5cad56033a7124e749ef0b2a03b674fc |
| NutritionSourceInterval | c7d742524164eef435facc99e64a8745dd7bb10872461b6ccadf7274bee33f98 |
| NutritionSourceSession | b25c2a93f610c2ab5242ff218249e73fbdb8a89a17adc75ed70b8bee92d7de68 |
| NutritionStreamIdentity | f4303fb018ab69f95e447e26695f555e72f061378b3b76c6297722cc69f5904c |
| NutritionStreamManifest | 44f51e340a028cd28561267f1b238031b1f54f20afa767d5121841db31bda9cc |
| NutritionSubjectWitness | 89aa789427654a8c0db6b90b33e06296cfa70dc3a8ca9e90826936c80bf48089 |
| NutritionSynthesisAuthorityFrontier | bc7a2ae04a257bdcc7176dd2f3ab160cdb7b58c00bf3105e691f4c26c2180b7f |
| NutritionSynthesisCaptureCommand | 74c1404a4c7a699f8171d17eef31731f75a9243d932cdcc2692a920a5578b862 |
| NutritionSynthesisCommand | 724b4ac308a4c1170b760b73bada4f9fae73ced1fd2fe6750b1069c7392d744f |
| NutritionSynthesisDraft | 2f52470dcbe179b25e61dbbdcd58cb3ec7223d39d235a83e726fb622fdf3a90c |
| NutritionSynthesisGrant | 0a374e5eb25645f8d3852dcfc5836dd0dc0511f3f230d8deda19f63438534869 |
| NutritionSynthesisGrantFact | 65bf06df1e9b55ab6cdca8a8aed1a0de8c8ab339e32c44ab618514cfd20fde03 |
| NutritionSynthesisOperation | b8e8dd48b72379b9ef82a44e702c1b9b63b1346b87d996a4072a788146765937 |
| NutritionSynthesisPrincipalEnrollment | f9cfaaf84cb58615ffb51afc0b239ee918f061868fb7586ce2e2bddf04172486 |
| NutritionSynthesisPrincipalFact | 11838d873476b4d3361c299df9b25dc247ceaf5602b9846a0eabf9d2c8d5fc7c |
| NutritionSynthesisPrincipalFrontier | b47413c849e1d85b1633cda1d66b7596007a4baeecf3264d310f0efb37727cf6 |
| NutritionSynthesisProviderEnrollment | c9b687eaa30cd143e18f3d051a0224bd84728155053036f2c000ba86ae30c8f9 |
| NutritionSynthesisProviderFact | 5c0c5388f676e86b4795001ce0253466aa3aac8074f691dbda0f6b86550d439e |
| NutritionSynthesisPublication | ba6ff702739ce29ae1f812846fe1f1f41edae339c53ca9f6be67a541b25b0a4f |
| NutritionSynthesisRecorded | 676878b4aa700c49e9d7603252432e6a10a51c4077517a8fadec42c13d197955 |
| NutritionSynthesisRequest | 13e8509651c67ac1ec82e6380c0c356d67430bfaa5b137333cf242f8e5d0d076 |
| NutritionSynthesisReview | 9cce4c9e727d7f301f0e0461338fd1e841cfddb5d3dfd4457b87bef5b87f4013 |
| NutritionSynthesisRuleBody | 4710d1d480338de5c04273203576f55e314161ac869753bd7dfea5427c5e89a6 |
| NutritionSynthesisSelection | 68797c0a374c638feba39de1dd221d45efc46256d2b4eaa1ce23ab5a589dc949 |
| NutritionSynthesisSourceSnapshot | 78392bb606b857c617be8512a8285fda79caeeff498aae17f9cbb3457b8b0bcc |
| NutritionTarget | 336199d820568929a1fc77c72942f913b44b8115ece63aebd7b58dd4d8b2ec02 |
| NutritionTemporalScope | 7d34b03e85cf0943544d42dc4ef76d5fb25a79373a5110bf089416d321e39652 |
| NutritionValues | f6a56202e0ea893c152dcf9cea56ce67a7c3484e9b0b54bb827d4ca9745f63b2 |
| ObservationConfidence | 89168543c7f67120c599c6d53edf8c8ea5e5c43811e03539ac296af53aeb6616 |
| ObservedAcquisitionCoverageDraft | 68fb76028d2c8636e7a42a41eb67db7a9d7f7a8a8ab76ab87f0e114383c94f63 |
| OneHopHierarchicalMemberPreferenceDraft | 8f447c136c57024b2a45b0e18e5ca96ef9def1e4a03464fa54be34ba4d16c9a3 |
| OneHopHierarchicalMemberPreferenceInput | 28141e5555c9b4e52dbca0ff75c484964488409d2c160785bfc304dc43151060 |
| PackageFact | 3d4784730e474476af779948b14bebad96a71b1500d12bfa31ace7733dc53415 |
| ParetoShortlistDraft | 77ca11109f26de94b9bf92ada07b9aba3bfbf306f27f49555781fcb8d2a63964 |
| Participant | 32243027d459291828a15842ea2bad8a59718c7bb51d227bf8e445d03d95e13b |
| ParticipantInput | f5653c36d7ca1a10a7fad4606e8c38a8811151d19f6c13a42f2ce2ca285ada24 |
| PhysicalEvidence | 9fa5bd43c6d01747f31688a93ac7c917ec0180c9a4863bb9702bda7cdc5a898f |
| PhysicalInventorySnapshot | 13634baac8f265463a50295b61bd525ed69615bd0648499a2746cc16e2aefa7d |
| PlanIntentAxisEvidenceV1 | 47118466cc86bb39ed77a06218c571e4d1c5756ba780c22a1ffc1701a635371d |
| PlanIntentCheckV1 | 8400d1bb279c7ae0e1862c95842f1a2a845a5df892de41ac37cf2cb05a73cba3 |
| PlanIntentDiagnosticV1 | b70a65a93166b084c61c962c9bc2f6e1e35ff0901c2167d1a75719cb6f607547 |
| PlanIntentGraph | 569408fc01a261b504e6d7e89dfc73be810ebae3ecaca4c87a505ab1341522c7 |
| PlanIntentResolutionV1 | 9a55a391cf5c6ae6b4015fc2339e19dd7b4afbd2dc60ef76bf0b96ddad4090f0 |
| PlanProposalSnapshot | 76fbfadada32f50ec02954f4c9c1a3abc062bc4a04b50c33903199f776a6ae75 |
| PlanRevisionSnapshot | 1a22317f82f3a0020782684632064108467bbb93bef09664fc1201f69f4dcf3e |
| PlanWorkspaceDraft | 35bda856731123e1b520c00a9247eca8a0a467bfe6973dda630758e2071f121b |
| PlannedBatchAllocationIntent | c25e573fdee8af3f74b683d691f1965d83205b553b0ff5ac41b93568e0e4d06b |
| PlannedCookingBatchIntent | d76dcf12f8d3eb93d05ce856a955ef8fbd7eebccf289351d5d79489c57f9b12d |
| PlannedCulinaryBinding | 26c9589f3cebedd7cca3b05088357bcd1fabc0aeb5accd18d23fdd60c602b8f0 |
| PlannerOutputDraft | d2033f2f7dcf8e8d0474d6ebf2a5d023ae10e93b53d3c88e0f94df57ffd1b5ce |
| PlannerRequestDraft | 0f1a657d69d634b47ec0638ccbfacf55f994ccd77b673222da11ac181fc8a0f8 |
| PlanningPriceQuoteDraft | 91fdfc792fa955a9a573886bd393fb3f14856d22ed0508578e1a0a6f7787b28f |
| PlanningProcurementOptionDraft | 94a9886cc4e921cf94f71097b83796000fa7edd1e34916f0d1b35f14d8967b55 |
| PolicyAssignmentEvaluationV2 | 11f59c261695676b8aeb7b069384a57c8a0b64a091847959c6b67048aba68ccc |
| PolicyCenterDeltaV2 | 71a8f4c426fa725c56d3c8535e96705b629b9e5987bc98f264881199159a5ea4 |
| PolicyClaimCoverageV2 | c1352c1be730bb55da1c7a5ad8769e6a265b65e313712dc7fe457ea2efe5f4df |
| PolicyDiagnosticV2 | bd74e6e75ad00f26b676d3d2745565a50cc7b760403b7b7154d2f233b7a97afc |
| PolicyIntegrationIdentityV2 | e19a5c7311346a86acddac8077c5259c3c8b1d157c5ef3a0e68d5dfb03b86bc1 |
| PolicyV2CaptureFailure | ff5adb391f3eb41239486751aba9dc0b1a256f971003aeb7465fd15cdbd170ae |
| PolicyV2Use | 1608212ecc26fa18f174c96591c4dc163fd74147366bc7438997a7eb3dd54f87 |
| PreferenceWriteCommand | 93105c4879b0e13638d148ab9ab8ded1ff40b561c701759fb0943e63ca2c625b |
| PreparationOutputEstimate | 9c9b1ca2fccab148a74f523a80394d6157f7fb3ad269cd35da15c203daf404cd |
| PreparationTransformationFact | 096e5ce2142b86c1156bb6c356e70a6821b3dd51b9261f5bd07d594cb0cd61ad |
| PreparedFoodAssetFact | 6a26e70594e7f5984f30b18e40219be7ad65005ef8d30d3e874c15ca6d1ce0b5 |
| PriceEvidenceAssessmentDraft | 21c97ae8c7b7080e30b15e7bf8a4bbd335fd0a93ab2e396ad33398d91ccf18c5 |
| PriceObservationFact | 506edba55ab6601eecb59a86853a2736f4e0f9d5a4852f3605b8f67614f9b7f7 |
| PriorInfluenceWeight | 1d97f44b1294b95ccfc7d6afa8751f5d69aef5830643400539e6d3f89410e2b2 |
| ProcurementClassFact | 90b628393dad479fe2c92654dfb6648d849659a128806cc00b826df7d128641e |
| ProcurementClassMemberFact | a68e93799eeb09eb5551714630587322eedcae7b305d6a26886e38006e78ad5b |
| ProcurementSnapshotDraft | 2fa9536ac8fd582acaa8e94ed57972d7b50ecf8074535845e280c32954a940d8 |
| ProcurementSupplyPath | 3cc9da682fca22f52a17cba4d86f5ec51fd4e1e7b320b43b59799cf92cb406c7 |
| ProductIngredientConversionFact | 6451a29b2a8752fc02d47427129dfada283238fc38c5c3629a1d5f764ffb2150 |
| ProfileTasteFitSourceCoordinate | c2e7e775319e10e6dacd4104762fbb6e99b21ab10ad9fc643f91124c0e1f5cd1 |
| ProposalExposureSource | 1eafdd53eb291f91017bab82d8c3162f908ec728b6447ccc185bb6861d28a9ae |
| ProposeBoundPlanCommand | 10022be8237440f60ac9e6fc34f59029899e41db367355d88197fda757ee1cd6 |
| ProposePlanCommand | 413145f1e0ca722b437eea2d5a20346777a0fcff4e330fa0cec04542a61c8b50 |
| Provenance | 36d4958b8ecd8b8f50a1837714b666dbd8b6e4a4fa731fc1811b332567355b12 |
| PublishPlanRevisionCommand | 4fe5da4d86e8ed8720f732320645be0a0399c76237fd8d6a0a77c2f3635fe951 |
| PurchaseIntent | 72b8da8ff43f3cc4b13a600f97eef2ff3bbb0ed615f7496d964b0b7d18cde8c2 |
| Quantity | ff7ff0063ee56e80edd7f05ac60c348aba58eb512da63a581997321618190047 |
| QuantityAdjustmentPolicy | b0cd9f3ec343533d3ce2702ef1c7ee1aa48948d21904f87238626764e19165c4 |
| QuantityIdentity | c73650b8b3935f096ee0d2027f48bb2e876f900defc78a2c6aa9621946ad2a0e |
| QuantizationPolicy | 83c35183731a7389b5ed3c065d6f6722c2ceb4a8e03436ae13dc3ac6a08c79bc |
| QuantizationResult | da888e0bad6cd860e4c0be6b1fc371d3f30796ca56e88a5c0e6b2463ac9aa22b |
| RawExplicitTasteFitCoordinate | 7332a6209b99b74c1265d44a64f86cf3bb9bb4eddd5b91b6d00d700c20b1aa93 |
| RawIngredientAssetFact | 5326d4346c9206f2ddf12ef1cc6415c41b9fcf1eafd195adf25ea2242508cec6 |
| RecipeCookingFeatureContext | 91277d7bdde67fcd18964f8c1b99630bf8ce946d88c16b211d6e3dbfce2e113c |
| RecipeCooldownAssessmentDraft | b6668a5c4c01ee3d507cfa6d72aa768833fcaf760a1bc4d914de3108a58baa8c |
| RecipeCooldownInput | b7a4681df99326211f68b1a6635ea275444ae3ff51e43c3975f66937cde57440 |
| RecipeCooldownPolicy | 2bb647bd53555a9ffef3e3a1bcb712652e6b29649a1bc06b8c2a0bf2ea023a2b |
| RecipeCooldownQuery | d0b992b387b29ae0b8c9a5192ec7b9dca6180d1e199b3dcc66a19a0f3c706ef6 |
| RecipeCooldownWitness | b32c5a5dd220e5dbeb707cb2c01401c2adacdd434efd603e625cfe06a8c0487f |
| RecipeDecayBand | 1f39df1321f89c683d8be79e4a74b040cd3d68303a109cace3f47140e048be36 |
| RecipeDecayInput | bb2d5f6995c34b13f157f70756b0ce2749f5c0c9fce4aec30cf8aacf361d16c3 |
| RecipeDecayPolicy | c3d92be8e6652ae593ec3d0ab3146910916128bcaa99a402fd23de23b983178f |
| RecipeDecayTraceDraft | 4b92c07a14716a5640805e3a2c79caa004db77cdfff03966ce101e20c1f995ba |
| RecipeDecayTraceEntry | 1cd6347f162fb82268561b01b79f260f07c18ac6299cb0b0ffabd2b9fc2a9af3 |
| RecipeExposureFrontier | 36807b5e576048f714ebb502212bd5537bbdd7efaee02f104d734b42fdffb630 |
| RecipeExposureIdentity | 4cb6c09c154f296f355245c1a1b0fd23892cdeb7f4e6cf02349d00cd6d473a77 |
| RecipeExposurePreviewDraft | dddad0d5f65b79b90fd6fc3b4e3cec8dd5af370ec85480adeef3a13377c658f6 |
| RecipeExposurePreviewFact | 7539f0fb9e16f2d8cebdd34b3463f374ead1921ceb1f2c781b7cc0713a40fee6 |
| RecipeFact | 3de7828c73357188dd3c14b5cb83f030f2cf67910d1a47dd8d455431f0ef660d |
| RecipeFeatureSources | bc341cdb5f32850ee70f179d236e609f788f0c97996a38b8f03ccbc87ddd4fb2 |
| RecipeGroundingReport | 07d3a8abe35d64d88b9546d96264b1d7ebcfce949bb2f6c708f1e1ddf17a5807 |
| RecipeIngredientFact | ccc76de737e539cbf8c0e359cdf3bfe25cebea1c2f9fdd4af696217da7b209ca |
| RecipeMethodContextKey | b8c22554dda7ec20e6f19d3d2042b38acf008caedf15fe54d73115ee4884e2ac |
| RecipeOnlyFeatureCommand | ea2b0aae0fb59054274f8fe2f77c9e7f2645ff7e520d2b8e11c7458379b1e163 |
| RecipePortionTierFact | b5a35a2080c6fa1ab6b32325f4be679c15ca52b1ddf5ebdcc5e11c9c8ed02ca0 |
| RecipePreferenceTarget | 6f20cf9e6c36e9126adf6ab2d88e64c2784d11879e9f8ab38c32a59a01c11b93 |
| RecipeProvenance | c294fee33f027a1f92c3de8dee4bd17e2aa5b04aefebcddd18466709507afcf5 |
| RecipeRepeatEvidenceDraft | eafc93d0fc33242c463949dcdef59d485bbe4eadd7582045474994bb3be79557 |
| RecipeRepeatPenaltyContribution | e46945194507023a6794d625ddaa6bc917668d572a3bfcf301f5acd4bb3728d5 |
| RecipeRepeatPenaltyDraft | 2d6fe58f0ea3fec5b62649bdfd17c64aebf8c5c77230f2e0d4d741c42467bc40 |
| RecipeRepeatPenaltyInput | 9b30ac99f1d8dfd4eb2334f70145fea54b9a0929f27a99d39ec2a276ad1c6db3 |
| RecipeRepeatPenaltyPolicy | fd36288de06a692cfa378742c9365c662b5ec0aba13d75dcf1dd60d4eb01b9ec |
| RecipeRuleCombinationFact | c8132639ac5857c8361820c5580715da7bd302f1ca1fcf01281825f6bc74228d |
| RecipeTargetManifestEntry | df885b7456646473a5f1a4406f5c9c8871bcbcc308db7317bd5028109a6fd7e8 |
| RecipeVariantRuleFact | a27c5b0c49b373d50d66c95519a8846e2b24eb12683bd58b11700149ea7d1970 |
| RecipeVersionSnapshot | 6434f5b49cf28669810b90c8edc725b26d51e6efa2efe34a04ae4f52d72ae509 |
| ReconcileInventoryCommand | a887c1ee85feb226a16b2e65fc265df54269c667f61755a580929d6303b03c20 |
| ReferencePriceBookFact | c7bb925f25cfca9261fb9c51edd86d0fa288a48563d0db0e1de5469b433cea68 |
| ReferencePriceEntryFact | f6f846adac1e7e17be484195a3b54d66b175d17a09bb87eb4d93d48747ff841f |
| ReferencePricePair | 008244624920552bfbb2f0ceeb40898f15eb41176333632a55543f7e73050021 |
| ReferencePriorAmount | 2e1f56580aa8841a39923b7492ad6f3324d32d2b37782f2f131e1c39cc702828 |
| ReferencePriorAuthorityCommand | a6969a5aed7269a939a02aef6cb9aa5feb740b795b49c317fa28f79c50c04a68 |
| ReferencePriorAuthorityEvent | 6b33008b5da57078cd5ad08a8a1fdf550341eaf6b91a15d15f88a47198369914 |
| ReferencePriorCaptureRequest | c0bd33aaca8c6dac5a160f0b739a92b4fd4e4fadc799e62f26718b567fc44670 |
| ReferencePriorCoordinate | 7c92e5f22552bd4d732fcd77aa957b409291937fef9406e6d85204a2220577c1 |
| ReferencePriorFrontier | d10a9faac4ffde9887277629ae63d89e0bc64c0187b3b540693c085f3883cc3f |
| ReferencePriorMutationFact | e93145cb59e22d60818f7cd0852b90edb1fcdb14753a0d1cbadd811ce29d2bd2 |
| ReferencePriorPrincipalCommand | 3725c8287c2aadef5970de3db11d50389d1255abfd95479e7c253d80faa8f9bb |
| ReferencePriorPrincipalFact | 75140ac5dead1e22b69aba860db598629ffa6447500abe840f24f7a9cec186e0 |
| ReferencePriorProvenance | 081d96b27724d82c7871ea837bd37ff17c8716f172441cc014c0789cb8ecc70c |
| ReferencePriorProviderCommand | e7e0c7c7309539f63d5b0f84790854d853c18356a6cd1020abfb17b0acd2d1c9 |
| ReferencePriorProviderFact | 39214fdc4faa42bbf85e350191e482e45106b8656a1523a6ebfe9d34c3436a0f |
| ReferencePriorPublishCommand | 7d5643284830041d9bc227fa37fcb14ad0f1879d49a1569bb0ce318cc7391c84 |
| ReferencePriorRetractCommand | b4cf3eceb2d62563cc10692ec860f66b4b160ba5b5a0ff5e45c63e869410e1a3 |
| ReferencePriorRevisionFact | b57f0a7a10d1698b18565bea1a6fb1fbd4843126891fe9a374fe1bc4e169830a |
| ReferencePriorSessionFact | e5eaad5f4f5520cc2474f7600871ad112eb3eefe1631077e0c0863e95a91837a |
| ReferencePriorSourceSnapshotDraft | a9bde5080160ea32cf366948dcb39c02e528e035c66cebbb700d1c771f4f0894 |
| ReferencePriorStreamFact | 4d5cbaca36b2d44a6519080cb5eaccf3e3d1af909d39071bca2abe2694e08613 |
| ReferencePriorTargetIdentity | 1f2965a3602dbaac92b37a8097bef4db13dd1a0bfab01c8cebe0ec05d2b94c74 |
| ReferencePriorWriteReceipt | b9dcfcb789cf20223a92d6421838e582f154e05a7b1f504ea86a616ab390af82 |
| ReferenceProfileMappingRule | 22ea34b24779d1d74ae01c392c725c7a78ee65785a23b7a8f25d0d1bf05fafaa |
| ReferenceTargetKindCompatibilityMap | 655b1c7b56aee1917d7a39dd3afd9479a3b22f1ba52fea80379a0827cd2ccf11 |
| ReleaseReservationCommand | 1b0c5e4612a9864638235d0ad5a34e34b5a52f67f66f951d97d5ca47720a79d2 |
| RepeatPenaltyAmount | 8a5ecf2125b40663b653374602653c4b192aeae15328bf86c4a837a796dc9730 |
| ReplaceIngredientProteinReviewCommand | e29036a668b6eba347a6d209bb824f76fb91aeb92c35f217d00bb8641225ddf8 |
| ReservationIntent | d57cec2b461ba039f54509fbd42637face8d014eec8015452f8b263839abdaeb |
| ReserveInventoryCommand | 593d0c8e0da5753b967d773205e942d9e22fca07b38a545fee36e27e2b96d4a7 |
| ResolutionConfigurationV1 | b1947a51686bee10e0faf70f86d56d33cafaf98002409b7494d6fdbbce9e8c5a |
| ResolutionMeasurementV1 | 6cd7acffc4288f704931be8d713700c207e9728afb49bfd77c39a32fe7de20f3 |
| ResolvedExplicitPlanIntentV1 | eca5152fa02007638cf391091625988aafb7d883c9d25f54a7b350d59a0ea51c |
| ResolvedNutrients | 0376d2191ef98e242b8450bc8782addfcff87558aa39cc81813904614f85925b |
| ResolvedNutritionPortion | 3a728a768992ba39092e0bed1403d09c95d2ba553aed9996cc79a5157a937de4 |
| ResolvedRecipeIngredient | d75014f21150ed9b918bafeea2b2dec9a0078753ba8514a8db9ab46b8264f3bf |
| RetailPriceCalibrationFact | 67b5eb2220efe2362c12b4a762470563a585a5e745b7e1f01fec143f5562703d |
| RetailProductFact | 644281c128c6ca007b1be561343b7828d47d86eca0afd6446f44a20324bf9f19 |
| RetailSourcedAPAssetDraft | 18b5b871247d836e45c6156b47086d1977bf3456be88c3ded84a98c3d231042c |
| RetailerFact | cba6d27a52670277a5e7235044f6daa92b26da62ded987caa0ff2a2341fafbc1 |
| RetailerStatusFact | 927671e855dc0f2162e2ccac627a18e369743f11c660367b8273567dc956a0f1 |
| RetailerStatusProvenance | 42954cc3a74d9f5ca2fd6d6f81ca5b529c6ec641e9fd27ff35dd2340c3133b42 |
| RetentionMultiplier | 017067825488bfe77277f1a975b84f522d386589c10d59ab3f2be42a3b51c5df |
| RetractIngredientProteinReviewCommand | f0dc1c98e0cf9489a53208a011cfd1cb0bd8da5284fbc53194de0633654b0e81 |
| RetractMemberPreferenceCommand | 06de88c2d32f6f0f24834ae95645c893931049c8794437bd7331f276073f73ef |
| ReviewedHierarchySourceDraft | 3776c02647d63e1327fde247ac4840b03448356aec2f884d256b7b963f417d09 |
| ReviewedReferencePriorDraft | f101bd8fe0588760f3e51759e0cd98efd04d10bb6fb00f9b9a9ddf2c03f0031b |
| RevisionScope | d00b9f8ad4cc879def3f2be316ac78ed95d7dd4faffee1d562b22758886f1704 |
| ScalingKind | 23fea56e21a3519ca886dd699532df1a5a551affcc3393032c381a8f5cffa785 |
| ScalingPolicy | b5187198382289f128f0984c992ebc8018d6ac86c0db4bc197e6d30e94e84f12 |
| ScopedInheritedMemberPreference | 33bbb7f29adf2d5c1c8d6c093eb161d8bc9f6f4de228986ef89d6ac906f02681 |
| ScopedMemberProfileAffinity | bde28a3d4e5a5f2ad476ef8fd0a1cac010b35dc7b1e43fbddc0969651d9483a3 |
| ScopedSharedMemberTargetTasteFit | 3c8c50104d1447698dff969ecc59d5834bd4633482b5f9ac6f688782b8cfbb55 |
| ScopedTargetTasteFit | 7507221b4a5721a3ce7f1dbedd018d101bc6ca5f04397f6103ea30cda0e7d3cf |
| SetMemberPreferenceCommand | cca5d98def4eed2207323b3070ac79d5c9c7283205d6410837a3fc968a5d6e24 |
| SharedMemberTargetTasteFitCoordinate | a43f7d91378cf1e8b487c8319dd8075b678efcbe1dab7787c0a595fd4289f47c |
| SharedMemberTargetTasteFitDraft | f85ac1f9122203988fec756823c2e8f5435d8a024c56cc3def9c22069c31a733 |
| SharedMemberTargetTasteFitPolicy | 12d3230aae21f1d0f80eb8681a2fe02932b071da5c4f2a41a2e7df7f9e540d7e |
| SharedMemberTargetTasteFitRequest | 622d05c2b2356aeb52a06a026c8dd4f82449ae3eb417f4d1b71abfa2da0fa712 |
| SharedMemberTargetTasteFitSources | ccdb623fc7650b48e77d8875e74aeaaf61b5264681bdba82ad80fa3e5580e7eb |
| SharedTargetTasteFitAmount | 7fa50b09f6f44c53c097cd8ca50bcdae592e069521062cf8c5e4c5d663cb7e21 |
| SharedTasteFitBridgeRule | 8de51e794c489f05cfce285d612b5375bb633b69179379fe319837981ef414a0 |
| SharedTasteFitCohortProof | 9aa381091135ce28d282b7cd323e510ca5ac6aac3871ceda795160a1ad817b52 |
| SharedTasteFitCompatibilityDecision | 38b7330440700e5c9863ed1dc8081c995c56b742495ead17e228baf459a32390 |
| SharedTasteFitCoverage | cf3f1ff710f0a2e64684aa30d8452d12de7b5e653a3e10123979138e7baddde1 |
| SharedTasteFitDirectSignalTrace | 1f00d62d7dfb05d1ab4a75977667c074888efefdd6ff6ad95de92724f4c2e8fe |
| SharedTasteFitMemberContribution | 34b1c77766773d7f692cf7a33717d5c9d399a5065bc1770770f8d1c97ba8329c |
| SharedTasteFitMemberDiagnostic | e08252196a00aa381ece711cd4fe7b0978404183a46be90728d028fe45829fa3 |
| SharedTasteFitMemberInput | a75a9a9230fdb0ef243ddc36cf932e9da4c242c2371ca7596e184fe4b40230c5 |
| SharedTasteFitMemberWeight | e3b8c2a03cf4ae4acc1c3e23d1049ad060b93385944d08e6b948d7d3b965fa92 |
| SharedTasteFitPolicyAdmission | 17df4bf0aadb6190a1f652b4cad1c4f0c1a7bf11d94dfae6681f19415b47bb9e |
| SharedTasteFitRationalTrace | 914534fe3c6415a55c8ab5a84713a9cb917d15b95ea510bb0e4ab0be82cee8ec |
| SharedTasteFitWeight | 522a0f308acadc3e7713d3069466fc977d5254360167b5c08483fa698293e0d7 |
| ShoppingDemandContributionIntent | 25589fe6cf66e8630f28a668c63da44ae0cec94a8bdd88f52d6eef69a43f67c9 |
| ShoppingRequirementIntent | 0581c5e3d228fbf83b522cf2f3864a53c0203a931f0b7a2fecd77d96a6b289b1 |
| ShortlistDominanceWitness | 55870476d5866a759452f4cac1eae2e7af050abf0369c17286d5d06f11d8994f |
| ShortlistInputFailure | 1d3bbc2f208f058a4229247ea0c4a7f8b9f144fcea80ba5d2499c8c084afe1ef |
| ShortlistPolicyDraft | 91822470f03cf4e984f22c553b004815d1994d89b7994fe8c3acd9a81b52bf55 |
| SourceCoverageDraft | c889b909c8c445e98cb44dd98a2ff3e92959f00c13158d2a46f2abd5fad9d42e |
| SourceVersion | 3f383c34de49e759d1efd934e9ae611d1ac43c2f3e8849f97678e8636539e009 |
| StoreRegionFact | e782e3f2f6463d5b749cf42b8035f5611e84a34568caee0a8a56950bba6ece18 |
| SuppressedInheritedMemberPreference | 48828c911cc33a3dd2d28111fba3afe3d2575651e39dbfbeb64bb9f34f30b90a |
| SynthesisRational | d65735cbc0010f289099f122c725c1cb7f8ee5269e2133e62c0ca22bc05167fe |
| TasteFitAmount | b104dc0115f7e8583eb3296ddcfa1ac057ef65190e168123246f240a638ede5b |
| TasteFitCaptureFrame | dae8b1d5703423380142d9d41f0713ed5f9e52de6bade373cde553774f889603 |
| TasteFitCoordinate | f81f8ff4d175da071110755f39f228cf6c4399ae26dc568a2f87dff2a122a02c |
| TasteFitInterpretationPolicy | 4b97941fcfcd8b00e7d7e294ede83537ec709bb9a932376571004dac5e18e1ec |
| TasteFitKindPolicy | 610d16aec9a342ddd7553362418fa1f32023e3b2c852e107cc87388530bde9da |
| TasteFitMappingRow | 9a425f756f9ce23eb93edd08dd8c2d9be1850f8c5f73bcbba35f663962bca875 |
| TasteFitMemberCapturePlan | baf7fc5dbd335952d655e20d2a424b29201909d598320b81a56d21cfe65f86c9 |
| TasteFitMemberInterpretationPlan | a7e7f2def65f23658eb3d35c5217c2dee6fc0d9d0abeb138ca814ebcfb8cca35 |
| TasteFitMemberSourceBundle | 428db1cc6ac5305b712757684a7c6cbec64438275f6c5005f574fe1f62cc3754 |
| TasteFitMemberSourceEntry | 9480d6eaf7614118ddf04dd1ff576574b7c1b3415e8138872808cd592d9a3607 |
| TasteFitMemberTargetPlan | a999298f583a97f84755c08d47e235d103f99b6ddd8574a61bab4b659b3bd7af |
| TasteFitMemberView | 1245d7e7567f077454dcf2ab26fc6c0be363954820165e02fb086d7fe52bd086 |
| TasteFitSubject | 158fb00e95425200bb6173a510e625cb20325f97099aa42cded198e1fcd67246 |
| TasteFitTargetInterpretation | 92f4fe607174d39a8764903fcfa1a2d44ddaa4837068793ac5385ff0119725a0 |
| TasteFitTargetProof | d621cc6a2a87e11c54df91fae6152839f95e6483bc2355256a21a2e388c73332 |
| TierQuantity | e73f3bfb0b4167f293e43a0c147e4942152a986bd72b3e018b2bff2b1100705d |
| UnavailableExactTargetProfileAffinity | fb942f87b395ef469c4f4b3c256e5362015b1ea03dcf9c7cfd953f48a4cfd42d |
| UnavailableExplicitAffinity | 4364cca2e335a55a7ba4c9fed291167549f8920e15165fa23739abf128dd0c1a |
| UnavailableInheritedMemberPreference | ba6a6e1c7e825ce982d5550e669ec3450bef73c65b063338e42f03118a9dfc21 |
| UnavailablePreferencePrior | 44e8e1e4fe8dee975baf39812e4d7284277f2771efc340163e4f9d6ffbcaa42e |
| UnavailableProposalLocalFeaturePenalty | 24ec63ca232980b54b3ef26ef269dafe62d69f12569123c2c8c9f30ca47049e9 |
| UnavailableReferenceCompatibility | 9fb8e4003106c057b88e7419a873fe05db8a8771c0b82dc01e94c5f886e9ab80 |
| UnavailableReviewedReferencePrior | ba7e909e904aeb31401839fa24db81a1c1a864e427da1f9cca31b1650f181ac5 |
| UnavailableShrunkAffinity | b820afe298488fb12980120b5b58254a90a8f0709b8f5804f861884d6f8564bc |
| ValidationCoveragePolicySnapshot | 4341a99ed1cdef6f7ca97215cce6bc187181212941eb2b73a828caa618d565f5 |
| ValidationReport | b6221f0bbb91bfacad17620f7883d222fa76cfc2d9f776f79af121298db20037 |
| ValidationReportDraft | b856b17aaba34365acf5dab8e9eb12d1463faadc01c2abf5fc7d71773cd023b2 |
| ValidationSourceFrontier | 12a0d5f49d937dc122fd3094f40a9abdb47dcc3c14d4a22f8424696e104bdae1 |
| ValidationSubjectDraft | 8e21c6aef3655bbff9b1bb2abcd985cf997c25bb528348b6693fe2138a1c2788 |
| ValidationSubjectSnapshot | 54be453114d2623754029623b8463d97f071c64efd7ae316d3d1d8337d446b98 |
| VariantGenerationRequest | 5c1c9eb9e604da32b8f12fb5d22e3882dbf8512feda78fd405c2a03e6aac063f |
| VariantGenerationResult | 7eb4f9552031c5ea767cc67b3f301f39d717a2701599536f5baa27ff1c3c0ac0 |
| VariantReason | 7697090e7af2e4b204e8184d8b6f69778ded7c1c8c805d44450402662cb33c00 |
| WriteCommand | 6915747f637b22dc86e1597233e8c3aa86815c9a73e0be6229683e6854c392d9 |
| YieldConversion | 4d7953b70b9d25a9b7439fe816ae7a0c9515906594ce23e3caf52741c124b40d |
| YieldEstimate | 730000b4b6bc8962adce56575004b4d63fdf2aa7303f14078427c0fbccf745e8 |
| app__domain__snapshots__ValidationFinding | b3b420b2abe8eafa6261021f0e36353e5fa29daacc9eea070e40d3cb3ee64648 |
| app__modules__validation__contracts__ValidationFinding | 98cfd66fd03381d7a8396319b2dfb5cd22e10e2732ded59a8f73e2e65841d112 |

## Verification and future permission

Executed for this package: current-source AST/JSON reads; unique virtual replacements; parse all virtual postimages; verify537 pins/19 names and old hash fixtures. No future ITR source test/migration executed.
Owner must separately approve each exact file/diff/preimage, migration identity, physical objects, privileges and new inverse helper/fixtures before application. Baseline drift invalidates package. No inherited seven-file/eight-file exception.
Unknown guard/preimage failures STOP. No historical fixture refresh, weaker inequality, skip/xfail, baseline reduction or frozen-body edit.
