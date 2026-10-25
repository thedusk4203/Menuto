# MTR-040B — Explicit-source Target Affinity Profile Foundation

Status: **IMPLEMENTED / NOT FROZEN — pending architecture/freeze review**.
Approved design: [MTR-040B](MTR_040B_EXPLICIT_TARGET_AFFINITY_DESIGN.md).
Implementation base: `5cb39464fd1f07c55c82bb221dde3255c3773e64` (canonical main).
No next milestone is authorized; no root issue is closed.

## Implemented surface and ownership

- Preferences adds immutable capture/manifest/policy/input/result contracts, pure
  `profile_derivation.py`, coordinated `profile_capture.py` and lazy public facades.
- Catalog exposes ingredient identity-only reads and exact reviewed vocabulary reads.
  Recipes exposes stable identity-only reads without selecting a RecipeVersion.
- Capture accepts typed target IDs only, authenticates the actor/member through frozen040A,
  requires a clean read-only REPEATABLE READ/SERIALIZABLE caller transaction, and retains the
  complete frozen `ExplicitMemberPreferenceSnapshot`. Exact requested identity coverage is
  mandatory. Empty requested targets means empty rows, including when source history is nonempty.
- Pure replay recursively reparses copied/constructed children. It uses frozen head/state replay,
  complete versioned five-kind policies, strict canonical rational arithmetic and separate
  authorship strength rules. There are no production mappings or implied SELF/proxy weights.
- Source, manifest, policy and result fingerprints are recomputed from canonical primitives.
  New timestamps use UTC microseconds; the nested040A source uses its unchanged frozen encoding.
  Explicitly unordered sets normalize independently from member-sequence history order.
- Cached result constructors/revalidation independently recompute rows, all availability states
  and hashes. Rehashing forged summaries cannot validate them.

UNDECLARED, DECLARED LIKE, DECLARED DISLIKE, DECLARED NEUTRAL and RETRACTED remain distinct.
Only the current head determines affinity and strength. Retractions retain their actual head;
retries/revisions/history length do not add strength. Explicit zero remains AVAILABLE.

Prior and shrunk affinity remain closed UNAVAILABLE contracts. Scope is
EXPLICIT_SOURCE_TARGETS_ONLY; learned/contextual/passive evidence UNAVAILABLE;
cross-target inference and candidate aggregation NOT_PERFORMED; planner_ready=False and
activation_ready=False. This is not a complete MemberBehaviorProfile or production authority.
No TasteFit, transfer, ranking, feature cooldown, MTR-039, optimizer, Execution or persistence.

## Source trust and concurrency

Authoritative capture proves identity via owner reads in the same transaction. Pure offline
replay proves internal consistency only; it cannot authenticate database origin or liveness.
Captured historical actor/authorship/role remain unchanged after membership changes. Fresh
capture uses current access. No new signature, receipt, policy repository or PRECOMMIT authority
is introduced. Old snapshots are not authorization tokens. Capture does not commit or retry
partial reads; serialization failures require the caller to retry the whole transaction.

Real PostgreSQL tests commit a concurrent declaration plus an identity edit between preference
and owner reads. Old RR/SERIALIZABLE captures keep the old head and old identity; a fresh capture
sees the new whole-member frontier and new metadata. A target inserted after an old cut remains
unresolved there and resolves only in a fresh capture. No mock supplies snapshot behavior.

## Approved adversarial plan coverage

`U` = `test_target_affinity.py`; `PG` = `test_postgres_target_affinity.py`.

| Design case | Actual test coverage |
| --- | --- |
| 1 retries / head-only strength | PG `test_hundred_idempotent_retries_do_not_change_frontier_or_strength`; U `test_hundred_replacements_are_one_current_assertion` |
| 2–4 corrections, neutral, retraction | U `test_latest_head_only_correction_change_retraction_restore`; PG `test_real_head_replacements_preserve_full_history` |
| 5 undeclared canonical target | PG `test_owner_identity_capture_and_never_declared_targets`; U `test_exact_requested_scope_preserves_full_raw_history` |
| 6 same code/new term ID | U `test_same_feature_code_new_term_id_is_separate`; PG `test_same_code_new_id_does_not_gain_old_term_assertion` |
| 7–8 no recipe/ingredient transfer | U `test_no_recipe_feature_or_ingredient_protein_transfer`; PG owner-identity test includes undeclared recipe/terms |
| 9 member isolation | PG `test_members_are_independent_and_membership_changes_preserve_authorship`; PG invalid-owner cases; U source-owner conflicts |
| 10–11 self/proxy and historical authorship | U `test_self_proxy_authorship_is_preserved_without_implicit_order`; PG member/membership test |
| 12–13 exposures and meal outcomes | PG `test_feature_exposure_proposals_cannot_change_explicit_profile`; U `test_nonexplicit_inputs_cannot_enter_profile`; static pure-core boundary |
| 14 unavailable priors | U active/zero and forged prior/shrinkage tests; PG owner-identity test |
| 15 concurrent source cuts | PG `test_old_capture_coherent_during_concurrent_declaration_and_identity_edit` for RR and SERIALIZABLE; identity-insert test |
| 16 policy replay identity | U `test_policy_replay_changes_derived_identity_only` |
| 17 forged rows/availability/hash | U `test_forged_derived_claims_rejected_by_recomputation`, dict/copy/construct, including attacker-rehashed payloads |
| 18 zero IO / no writes | U `test_pure_derivation_uses_zero_database_network_file_io`; PG `test_capture_and_derivation_only_read_without_schema_or_row_changes`; import-boundary tests |
| 19 nonexistent UUID | PG `test_random_nonexistent_target_rejected_by_owner_read`, all five kinds |
| 20 no schema drift | PG schema/row test plus existing migration, direct-SQL and drift suites; frozen receipt |
| 21 complete policy | U `test_policy_matrix_is_explicit_complete_and_ordered` |
| 22 rational validity | U `test_invalid_rational_rejected`, canonical equivalents/zero test |
| 23 unordered canonical identity | U `test_shuffled_unordered_sets_and_roundtrip_are_canonical`, duplicate rejection |
| 24 invalid manifest/term | U source/manifest conflicts; PG DRAFT/wrong-kind/access cases |
| 25 explicit zero | U `test_explicit_zero_is_available_distinct_from_absence_and_retraction`; PG neutral replacement |
| 26 empty/subset plus full history | U exact scope; PG `test_requested_scope_never_trims_full_raw_history` |
| 27 coordinate/strength independence | U active-value, asymmetric nonzero-neutral and policy-replay tests |
| 28 owner/head/time/content conflicts | U source/manifest, forged head/state, deep-constructed children and future provenance; PG invalid owner/term |

## Frozen compatibility and persistence

`target_affinity_compatibility.json` pins the canonical base's existing040A/041A–E/046A AST
contract/algorithm definitions, all237 old domain definitions and all13 released migrations.
The existing compatibility receipts/tests remain untouched. Nineteen new exported definitions
bring the bundle to256; OpenAPI remains unchanged. No schema/model/migration/profile table/cache
is added: **0013 /71 domain tables** (72 including Alembic bookkeeping).

## Changed files

- `README.md`
- `apps/backend/app/modules/catalog/public.py`
- `apps/backend/app/modules/preferences/contracts.py`
- `apps/backend/app/modules/preferences/profile_capture.py`
- `apps/backend/app/modules/preferences/profile_derivation.py`
- `apps/backend/app/modules/preferences/public.py`
- `apps/backend/app/modules/recipes/public.py`
- `apps/backend/app/modules/recipes/repository.py`
- `apps/backend/tests/target_affinity_compatibility.json`
- `apps/backend/tests/target_affinity_fixtures.py`
- `apps/backend/tests/test_postgres_target_affinity.py`
- `apps/backend/tests/test_target_affinity.py`
- `docs/product/BACKLOG.md`
- `docs/product/IMPLEMENTATION_BLUEPRINT_M0_M1.md`
- `docs/product/INVARIANT_COVERAGE.md`
- `docs/product/MTR_040B_EXPLICIT_TARGET_AFFINITY_DESIGN.md`
- `docs/product/MTR_040B_EXPLICIT_TARGET_AFFINITY_EVIDENCE.md`
- `packages/contracts/domain.schema.json`
- `tools/check_import_boundaries.py`
- `tools/export_domain_contracts.py`

## Verification

Local verification on2026-10-26:

| Gate | Result |
| --- | --- |
| Full Python with real PostgreSQL18.4 | **2015 passed**,0 failures/errors/skips,202.11s; one existing Starlette/httpx deprecation warning |
| Existing regression identities | **1860/1860 retained**,0 removed; compared test classname/name identities with canonical design-stage `.local/040b-design.xml` |
| Additive tests | **155 new**:125 pure/contract/boundary/compatibility and30 real PostgreSQL tests |
| PostgreSQL-real total | **785** marked tests, all included/passed:755 existing +30 new |
| Old test and fixture source retention | All66 existing tracked files unchanged; no old test relaxed, replaced or renamed |
| Migration/drift/direct SQL/frozen compatibility | PASS in full real-PG suite;0013 /71 tables;13 migrations unchanged; existing receipts retained |
| Ruff / architecture / imports | PASS;30 invariants,11 ADRs,50 linked tasks,16 contexts; pure-core import restriction added |
| Domain/OpenAPI exports | PASS;237 existing definitions unchanged +19 new =256; frozen bundle ID and HTTP OpenAPI unchanged |
| Synthetic fixtures / benchmark |22 fixtures verified; **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client contracts / typecheck / tests | PASS; **10/10** |
| Web typecheck/build | PASS |
| Diff whitespace/scope | PASS;20 files; no existing ORM model, migration or test modified |

Full command: `.venv/Scripts/python -m pytest --basetemp=.local/040b-implementation-green
--junitxml=.local/040b-implementation-green.xml`, with the loopback PostgreSQL URL supplied.
The separate collected marker receipt `.local/040b-pg-identities.json` records785 real-PG test
identities. The full passing XML confirms every selected test passed. Other gates follow
`.github/workflows/ci.yml`. Exact implementation/PR head/merge and post-merge CI identities are
reported in final delivery after the remote gates finish; no in-progress run is a passing receipt. Verification uses isolated randomly named PostgreSQL test
databases on loopback PostgreSQL18.4. Existing source tests are unchanged and test identities are
compared to the canonical design-stage baseline. Local logs/XML live under ignored `.local/040b-*`.

**READY FOR MTR-040B ARCHITECTURE/FREEZE REVIEW**
