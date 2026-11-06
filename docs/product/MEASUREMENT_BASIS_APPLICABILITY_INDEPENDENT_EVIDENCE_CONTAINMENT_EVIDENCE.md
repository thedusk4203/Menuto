# Measurement-Basis Applicability & Independent Evidence Containment — Implementation Evidence

**BOUNDED STRUCTURAL / TEST_ONLY IMPLEMENTATION — REVIEW / FREEZE CANDIDATE, NOT FROZEN.**

## Authority and exact baseline

- Implementation base/main: `83025f158306e8cebc6357ac6d13fc3caac57809`.
- Approved design: [PR #132](https://github.com/thedusk4203/Menuto/pull/132), head `803f83791bd7f41acda614268098f35b72eaa729`.
- [Architecture PASS 6678583194](https://github.com/thedusk4203/Menuto/pull/132#issuecomment-6678583194).
- [Design completion 6679271731](https://github.com/thedusk4203/Menuto/pull/132#issuecomment-6679271731).
- Exact design-merge push [42174230677 — SUCCESS](https://github.com/thedusk4203/Menuto/actions/runs/42174230677): 4,047 tests / 0 skips; 503 definitions; schema0017/108.
- Governing [approved bounded design](MEASUREMENT_BASIS_APPLICABILITY_INDEPENDENT_EVIDENCE_CONTAINMENT_DESIGN.md) is retained unchanged. Its candidate/unauthorized language describes the original design stage; the user's separate implementation authorization governs this PR.

The exact implementation head/base, final full-suite GitHub Actions run and result are recorded
in the implementation PR's final verification receipt. That external receipt avoids a self-referential
commit SHA / CI-result edit loop. A collected test count or this document alone is not a CI-success proof.

## Delivered boundary

Nutrition owns a closed same-meaning companion, never a nutrient-value converter. Positive evidence
requires original source-authored `test-only.measurement-meaning.v1` preimages retained in the exact
reviewed guideline and rule bodies. Legacy/missing evidence remains unavailable. No reinterpretation
of physiological, offered, consumed or absorbed quantities is performed.

The pre-policy projection retains **two different manifests**: the frozen comfort-only requirement,
and all original hard/reference roots plus every selected-case MAKE_CONSTRAINT branch (including
unselected precision branches, daily/goal/weekly metadata). It derives lineage/descriptors only.
No coefficients, nutrient values, comfort bands, goal amounts or safety bounds are evaluated.
A required anchor must match an exact already-reconstructed NRE period/component. Missing weekly
or other period coverage cannot be manufactured by summing days in this companion.

Planning composes the unchanged protected NRE capture on one actual ordinary PostgreSQL reader.
The separately installed artifact is pinned before capture and checked again after complete result
construction. Registry/reader frontier change aborts all output. No common MVCC with artifact memory
is claimed. Actor and synthetic-reader selectors must match the private registration; database OID/name
must match actual frozen canonical capture. No caller payload may install a registry or mint its context.

The private non-wire handle is checked by object identity in a live weak issuance registry. It pins the
complete immutable artifact, deployment, issuer epoch, actual database, actor and reader admission.
Reconstructed/copied/serialized credentials are rejected. Privileged test Python is trusted; this does
not claim a sandbox against hostile code with installer/module access.

Synthetic source history retains enrollments, exact scoped capabilities, symbolic qualification,
review, publish, supersede, retire and withdraw events. Sequence/predecessor hashes, recorded order,
valid time, body/evidence/scope and reviewer/publisher principal-subject separation are reconstructed.
Aliases of one synthetic subject do not satisfy separation. Future-effective authority/publication
changes do not act early; revocation does not rewrite a retained old cut. Competing publication
selection has no latest/provider fallback. Registry revisions append exact preimages or are rejected.
Qualifications are `SYMBOLIC_TEST_ONLY_NOT_SCIENTIFIC`, never real-human or clinical qualification.

## Module and source-object inventory

| Added module | Responsibility |
| --- | --- |
| `nutrition/basis_contracts.py` | Closed immutable companion carriers; domain-separated full-source/result identity; bounded parsing |
| `nutrition/basis_projection.py` | Fresh frozen requirement and separate complete metadata projection, no arithmetic |
| `nutrition/basis_applicability.py` | Pure provisional source/history/meaning replay, fresh frozen NRE producer reconstruction |
| `planning/basis_capture.py` | Private isolated registry issuance/revocation/append-only frontier and one-session canonical capture |
| `planning/basis_host.py` | Separate server-owned 10-second producer/checker hosting; timeout discards output |
| `validation/basis_applicability.py` | Independent fixture history, original meaning, anchor and applicability reconstruction plus fresh independent NRE checks |

Entry points: `capture_test_basis_sources`, `resolve_basis_applicability`,
`check_basis_applicability_independently`, `check_basis_handoff_independently`.
The optional Planning host runs a fresh producer/checker conjunction but returns only unverified transport.
No report, matching public hash or `CONSISTENT` label is an admission certificate.

No new SQL object exists: **0 tables, 0 protected functions, 0 roles, 0 grants, 0 persistent basis rows**.
The existing Root/NPS/NRE role and function inventories are unchanged. No migration0018.
The in-memory registry is installed only explicitly by disposable test setup; there is no startup,
HTTP, environment-path or production installer/default registry.

## Independent verification and failure semantics

Validation imports neither the Nutrition applicability producer, metadata projection, fixture registry,
policy synthesis nor optimizer. It independently walks finite rule metadata and original evidence;
its existing independent NRE checker reconstructs retained Root/rule/food/serving evidence. Nutrition
imports no Validation. Exact per-module import allowlists and adversarial guard tests enforce this split.

Results distinguish APPLICABLE_TEST_ONLY, NOT_APPLICABLE, UNAVAILABLE, UNSUPPORTED, REJECTED and
RESOURCE_EXCEEDED. Failure emits no favorable partial witnesses. Whole-result success requires all
required anchors, one exact tracked member, original source versions, material/reference manifest,
complete periods/configurations and explicit assertion selection. No shared/fractional serving is supported.

All transports retain: TEST_ONLY; scientific correctness NOT_CERTIFIED; source origin NOT_PROVED_OFFLINE;
current authorization NOT_CLAIMED; validation authority UNVERIFIED_TRANSPORT; production admission CLOSED;
policy integration NOT_AUTHORIZED; synthesis NOT_PERFORMED; hard feasibility NOT_EVALUATED;
solver infeasibility NOT_PROVEN; consumption NOT_ASSERTED; planner/activation False.
Offline semantic self-consistency is not proof of canonical database origin or present publication authority.

Server-owned limits: selector64KiB, artifact2MiB, composition32MiB (embedded frozen NRE16MiB),
128anchors/assertions, 256journal events/evidence entries, 32periods/depth, 100,000string characters,
256-bit integers, 1,000,000pure checked work operations; caller budgets only lower limits.
Byte/depth/duplicate-key/exact-number checks precede recursive construction/canonicalization.
Capture has a combined60-second watchdog and frozen statement limits. Producer/checker hosting has
separate10-second timeouts; a timed-out result is discarded, with bounded pure-work execution remaining
cooperative rather than a hostile-Python sandbox. No HTTP ingress-security claim is made.

## Compatibility and executed checks

- `fixtures/basis_compatibility.json` pins **all4,047 baseline test identities, all503 definition bodies/hashes,
  and53 frozen source/migration files** against the exact base.
- **515 definitions =503 retained unchanged +12 additive**; the names are listed below.
- Schema **0017 /108domain tables**, no0018; **ZERO NEW PERSISTENCE**.
- Existing export-total/exact-set assertions are mechanically synchronized in six legacy test files.
  Original definition/file hash checks and all original test identities remain intact. No accepted runtime
  behavior or frozen compatibility receipt is changed.
- Focused local execution: **91pure tests /0skips;26real PostgreSQL executions /0skips** covering all12
  PG obligations. Additional parameterization is not counted as new numbered requirements.
- Client contracts/typecheck/build: PASS; client10/10. Architecture/import/lint/OpenAPI/fixtures: PASS.
  Benchmark22/22. The complete full-regression and separate SCRAM/TLS16/16 evidence must be verified in
  the final exact-head PR CI receipt before delivery; earlier or collected-only evidence is insufficient.
- Complete collected target: **4,164 tests =4,047 retained +117 additive**, zero skips required.

The fresh-install PostgreSQL obligation runs migration head on an empty database, checks108domain tables,
no basis objects and zero production Nutrition source rows. Positive test setup is explicitly TEST_ONLY;
no installation/migration ships providers, qualifications, publications, scientific content, seeds or defaults.

### Additive exported definitions

- `BasisApplicabilityCheckV1`
- `BasisApplicabilityHandoffV1`
- `BasisApplicabilityResultV1`
- `BasisApplicabilitySourcesV1`
- `BasisAssertionV1`
- `BasisCaptureFrameV1`
- `BasisClaimAnchorV1`
- `BasisComparisonWitnessV1`
- `BasisFixtureArtifactV1`
- `BasisFixtureEventV1`
- `BasisSelectorsV1`
- `MeasurementMeaningV1`

## MBA001–MBA080 → executed-test matrix

PG rows are actual authenticated PostgreSQL protected-path tests, not mocks or collection-only claims.
Pure rows use retained synthetic source preimages and independently expected behavior. Parameterized
functions spanning several IDs include distinct per-case inputs; each listed obligation is mandatory.
Local JUnit receipts: `.local/mba-pure.xml` (91) and `.local/mba-pg.xml` (26); the final exact-head
GitHub Actions receipt independently binds the complete executed corpus to the submitted head.

| ID | Class | Required behavior | Executed test(s), under `apps/backend/tests/` |
| --- | --- | --- | --- |
| MBA001 | PG | Authenticated ordinary NRE reader plus registered isolated artifact yields complete sources without new privileges | `test_postgres_basis_applicability.py::test_mba001_complete_ordinary_reader` |
| MBA002 | PG | Actual DB OID/name or deployment mismatch rejects fixture context, despite matching caller labels | `test_postgres_basis_applicability.py::test_mba002_context_database_deployment_binding` |
| MBA003 | PG | Wrong login/SET ROLE/shared actor spoof cannot satisfy existing protected Root/NPS reader identity | `test_postgres_basis_applicability.py::test_mba003_actual_authentication` |
| MBA004 | PG | Revoke existing reader permission on another connection; subsequent fresh composition fails, old retained cut remains replayable | `test_postgres_basis_applicability.py::test_mba004_revoke_reader_fresh_vs_retained` |
| MBA005 | PG | Concurrent canonical recipe/reference change cannot mix before/after values in one retained NRE cut | `test_postgres_basis_applicability.py::test_mba005_concurrent_reference_uses_one_cut` |
| MBA006 | PG | Missing canonical recipe/tier/rule/reference/serving row is not replaced by fixture manifest assertions | `test_postgres_basis_applicability.py::test_mba006_missing_canonical_not_replaced_by_artifact` |
| MBA007 | PG | Cross-member/household request and non-authorized membership fail through real source reads | `test_postgres_basis_applicability.py::test_mba007_exact_member_membership` |
| MBA008 | PG | Writable/dirty/routed/multi-session or schema-translated source capture remains rejected by frozen NRE guards | `test_postgres_basis_applicability.py::test_mba008_frozen_capture_guards` |
| MBA009 | PG | Changed original guideline/rule/evidence revision invalidates an assertion pinned to the previous source cut | `test_postgres_basis_applicability.py::test_mba009_republished_rule_not_old_assertion` |
| MBA010 | PG | Registry frontier/reader admission changed during real DB capture aborts whole composition; no common-MVCC claim | `test_postgres_basis_applicability.py::test_mba010_registry_change_during_actual_capture` |
| MBA011 | PG | Fresh installation remains 0017/108 with no new source grants, basis rows, providers, qualifications or production content | `test_postgres_basis_applicability.py::test_mba011_fresh_install_no_basis_objects_or_content` |
| MBA012 | PG | End-to-end real canonical capture and fresh independent NRE/basis checks reject a forged positive report with matching public hashes | `test_postgres_basis_applicability.py::test_mba012_forged_positive_report_not_admission` |
| MBA013 | Pure | Exact authored planned-input original meaning and complete same-scope assertion gives APPLICABLE_TEST_ONLY | `test_basis_applicability.py::test_mba013_complete_same_meaning_positive` |
| MBA014 | Pure | Token equality without original interpretation/version/material preimages is not positive | `test_basis_applicability.py::test_mba014_token_alone_not_interpretation` |
| MBA015 | Pure | Planned offered intent is distinct from planned ingredient-input contributions | `test_basis_applicability.py::test_mba015_mba019_no_quantity_inference` |
| MBA016 | Pure | Observed offered food is unsupported without an observation source, never inferred from planning | `test_basis_applicability.py::test_mba015_mba019_no_quantity_inference` |
| MBA017 | Pure | Actual consumption cannot be inferred from offering/attendance/elapsed time | `test_basis_applicability.py::test_mba015_mba019_no_quantity_inference` |
| MBA018 | Pure | Physiological intake with absent or supplied unapproved protocol remains unsupported | `test_basis_applicability.py::test_mba015_mba019_no_quantity_inference` |
| MBA019 | Pure | Ingested and absorbed interpretations cannot be silently equated | `test_basis_applicability.py::test_mba015_mba019_no_quantity_inference` |
| MBA020 | Pure | Unknown meaning/version yields UNSUPPORTED, never permissive fallback | `test_basis_applicability.py::test_mba020_unknown_vocabulary_never_fallback` |
| MBA021 | Pure | Missing original root meaning yields UNAVAILABLE, including legacy TEST_ONLY fixtures | `test_basis_applicability.py::test_mba021_missing_original_meaning_legacy_unavailable` |
| MBA022 | Pure | Companion cannot contradict or replace original physiological meaning with planned-input meaning | `test_basis_applicability.py::test_mba022_external_cannot_override_original` |
| MBA023 | Pure | Wrong guideline provider/revision/body/evidence/protocol anchor rejects | `test_basis_applicability.py::test_mba023_guideline_evidence_revision_exact` |
| MBA024 | Pure | Wrong rule provider/body/case/operation/layer anchor rejects | `test_basis_applicability.py::test_mba024_rule_revision_case_operation_exact` |
| MBA025 | Pure | Exact subject identity required; no copied member/Household aggregate applicability | `test_basis_applicability.py::test_mba025_exact_subject_not_household_aggregate` |
| MBA026 | Pure | Valid evidence with wrong population/supported scope is NOT_APPLICABLE | `test_basis_applicability.py::test_mba026_different_supported_population_not_applicable` |
| MBA027 | Pure | Unqualified source/absent qualification produces no positive result | `test_basis_applicability.py::test_mba027_qualification_required` |
| MBA028 | Pure | Reviewer/publisher missing exact scoped fixture capability cannot publish | `test_basis_applicability.py::test_mba028_scoped_capability_required` |
| MBA029 | Pure | Same principal-subject under different login aliases cannot review and publish | `test_basis_applicability.py::test_mba029_alias_logins_not_distinct_subjects` |
| MBA030 | Pure | Changed body/evidence/protocol after review requires a new exact review | `test_basis_applicability.py::test_mba030_review_binding_exact_body` |
| MBA031 | Pure | Root/NPS/Catalog/Household grants cannot become basis capabilities | `test_basis_applicability.py::test_mba031_unrelated_grants_not_basis_capability` |
| MBA032 | Pure | A Git hash, reviewer string or REVIEWED label cannot enroll a fixture source | `test_basis_applicability.py::test_mba032_hash_reviewer_label_not_enrollment` |
| MBA033 | Pure | Duplicate/edited/reordered/missing journal event or wrong predecessor rejects | `test_basis_applicability.py::test_mba033_journal_identity` |
| MBA034 | Pure | Complete append-only publication and exact repeated retained selection replay deterministically | `test_basis_applicability.py::test_mba034_retained_replay_deterministic` |
| MBA035 | Pure | Withdrawn publication blocks fresh applicability; old retained replay makes no current claim | `test_basis_applicability.py::test_mba035_withdrawn_blocks_fresh_retained_old_unchanged` |
| MBA036 | Pure | Retired revision beyond admission cutoff blocks retrospective fresh admission | `test_basis_applicability.py::test_mba036_retired_blocks_retrospective_admission` |
| MBA037 | Pure | Future-effective replacement preserves pre-boundary current semantics | `test_basis_applicability.py::test_mba037_future_replacement_not_early`<br>`test_basis_applicability.py::test_mba037_valid_future_supersession_preserves_old_cut`<br>`test_basis_applicability.py::test_mba037_future_authority_change_not_early` |
| MBA038 | Pure | Cross-version request interval is unsupported; never stitched/clipped | `test_basis_applicability.py::test_mba038_cross_version_not_stitched` |
| MBA039 | Pure | Retrospective correction cannot mutate an older retained snapshot | `test_basis_applicability.py::test_mba039_retro_correction_not_mutate_retained` |
| MBA040 | Pure | Capability revocation blocks later publication actions without rewriting prior recorded events | `test_basis_applicability.py::test_mba040_revocation_blocks_subsequent_action_not_old_publication` |
| MBA041 | Pure | Qualification withdrawal blocks dependent fresh applicability | `test_basis_applicability.py::test_mba041_qualification_withdrawal_blocks_fresh_use` |
| MBA042 | Pure | Missing/ambiguous explicit assertion selection has no latest/provider fallback | `test_basis_applicability.py::test_mba042_selection_explicit_no_latest`<br>`test_basis_applicability.py::test_mba042_competing_explicit_publications_rejected` |
| MBA043 | Pure | Exact period ID/calendar/timezone/effective interval required | `test_basis_applicability.py::test_mba043_mba045_exact_descriptor` |
| MBA044 | Pure | Daily/weekly metric/unit coincidence cannot substitute temporal semantics | `test_basis_applicability.py::test_mba043_mba045_exact_descriptor` |
| MBA045 | Pure | Unit or metric mismatch rejects before any policy comparison | `test_basis_applicability.py::test_mba043_mba045_exact_descriptor` |
| MBA046 | Pure | AP/EP/raw/cooked/reference material-basis mismatch cannot be an identity bridge | `test_basis_applicability.py::test_mba046_material_basis_not_identity_bridge` |
| MBA047 | Pure | Retention/yield/loss/absorption coefficient or converter field is unsupported | `test_basis_applicability.py::test_mba047_converter_fields_forbidden` |
| MBA048 | Pure | Shared/fractional serving or inferred member portion is unsupported | `test_basis_applicability.py::test_mba048_no_fractional_shared_serving` |
| MBA049 | Pure | Root/rule/precision/requirement fingerprint pins are recomputed from complete primitives | `test_basis_applicability.py::test_mba049_pins_recomputed_not_public_hashes` |
| MBA050 | Pure | Comfort-only frozen requirement is distinct from the complete anchor manifest; hard/goal/weekly anchors need existing exact period/component coverage | `test_basis_applicability.py::test_mba050_comfort_manifest_not_all_claims` <br>`test_basis_applicability.py::test_mba050_full_week_anchors_need_original_period` |
| MBA051 | Pure | Ambiguous lineage/unsupported instruction/version/precision descriptor divergence fails closed | `test_basis_applicability.py::test_mba051_ambiguous_lineage_not_favorable_selection` |
| MBA052 | Pure | No completed NutritionPolicy/ResolvedPlanPolicy is required or accepted as source truth | `test_basis_applicability.py::test_mba052_completed_policy_not_source_input` |
| MBA053 | Pure | Missing, extra, duplicate or favorable-subset anchors prevent whole-result success | `test_basis_applicability.py::test_mba053_whole_manifest_required` |
| MBA054 | Pure | Missing slot/period/configuration coverage cannot become zero or unrestricted | `test_basis_applicability.py::test_mba054_missing_period_slot_not_zero` |
| MBA055 | Pure | NRE AVAILABLE and fresh independent consistency are both required for a positive result | `test_basis_applicability.py::test_mba055_nre_available_and_independent_check_required` |
| MBA056 | Pure | Forged NRE CONSISTENT report cannot replace fresh reconstruction | `test_basis_applicability.py::test_mba056_forged_nre_consistent_report_no_input` |
| MBA057 | Pure | Forged basis APPLICABLE/CONSISTENT labels with matching fingerprints cannot replace checks | `test_basis_applicability.py::test_mba057_forged_basis_positive_consistent_no_admission` |
| MBA058 | Pure | Rehashed meaning/source/coverage mutation is caught by independent semantic reconstruction | `test_basis_applicability.py::test_mba058_rehashed_meaning_mutation_detected_independently` |
| MBA059 | Pure | Self-consistent fabricated offline source may be retained-consistent but cannot prove trusted origin/admission | `test_basis_applicability.py::test_mba059_offline_consistency_not_origin` |
| MBA060 | Pure | Serialized context/authority stamp/report cannot be used as private harness capture credentials | `test_basis_applicability.py::test_mba060_reconstructed_or_serialized_context_rejected`<br>`test_basis_applicability.py::test_mba060_append_only_registry_rejects_history_edit` |
| MBA061 | Pure | Producer/cache-constructed result is fully recomputed, including every non-authority flag | `test_basis_applicability.py::test_mba061_all_cached_fields_recomputed` |
| MBA062 | Pure | Validation imports no producer/projection/solver oracle; Nutrition imports no Validation and accepts no prevalidation report | `test_basis_applicability.py::test_mba062_independence_enforced` |
| MBA063 | Pure | Fixture qualification never claims real human/scientific authority | `test_basis_applicability.py::test_mba063_qualification_symbolic_not_scientific` |
| MBA064 | Pure | TEST_ONLY relabeling to production/mixed environment is rejected | `test_basis_applicability.py::test_mba064_no_production_relabel` |
| MBA065 | Pure | No fixture registry/default artifact exists in production deployment behavior | `test_basis_applicability.py::test_mba065_no_default_registry_or_request_installer` |
| MBA066 | Pure | Source fingerprints retain full artifact history, scopes and absences, not only positive rows | `test_basis_applicability.py::test_mba066_full_history_absences_affect_identity` |
| MBA067 | Pure | Request/body byte and duplicate-key limits apply before recursive parsing | `test_basis_applicability.py::test_mba067_ingress_bounds_before_parse`<br>`test_basis_applicability.py::test_mba067_duplicate_original_json_not_authority` |
| MBA068 | Pure | Depth/string/integer/manifest/history/anchor caps are server-owned; caller cannot raise them | `test_basis_applicability.py::test_mba068_absolute_structure_limits` |
| MBA069 | Pure | Work overflow produces RESOURCE_EXCEEDED with no partial positive witnesses | `test_basis_applicability.py::test_mba069_work_overflow_all_or_error` |
| MBA070 | Pure | Host timeout/cancellation returns no success; pure replay uses no wall clock | `test_basis_applicability.py::test_mba070_host_timeout_no_success`<br>`test_basis_applicability.py::test_mba070_actual_host_reconstructs_not_detached_report` |
| MBA071 | Pure | Pure producer/checker perform no DB/network/filesystem/live source/global policy lookup | `test_basis_applicability.py::test_mba071_pure_modules_no_io_or_clock` |
| MBA072 | Pure | No numeric converter, transformed amount, nutrient target or production constant is exposed | `test_basis_applicability.py::test_mba072_no_numeric_conversion_or_amount_output` |
| MBA073 | Pure | Hard/goal constraints and original reference-center semantics remain untouched | `test_basis_applicability.py::test_mba073_original_hard_root_untouched` |
| MBA074 | Pure | NutritionPrecision/cost/budget/effort/TasteFit cannot mint meaning or widen protection | `test_basis_applicability.py::test_mba074_preferences_cannot_mint_meaning` |
| MBA075 | Pure | Maximum gap/GCD/exact NRE values do not constitute policy or solver feasibility | `test_basis_applicability.py::test_mba075_gaps_not_safety_or_solver_feasibility` |
| MBA076 | Pure | Handoff remains UNVERIFIED_TRANSPORT; consumer cannot use a detached report as validation proof | `test_basis_applicability.py::test_mba076_handoff_unverified_detached_report_not_credential` |
| MBA077 | Pure | Frozen Root/NPS v1/NRE exported definitions, files, accepted behavior and 4,047 baseline tests retained | `test_basis_applicability.py::test_mba077_frozen_files_and_baseline_identity_retained` |
| MBA078 | Pure | Existing 503 definition hashes unchanged; any future additive definitions explicitly inventoried | `test_basis_applicability.py::test_mba078_all_503_definitions_unchanged` |
| MBA079 | Pure | No migration0018/persistence/SQL role/grant/production seed added by the structural implementation | `test_basis_applicability.py::test_mba079_no_new_persistence_or_source_permissions` |
| MBA080 | Pure | planner/activation False, production CLOSED, no full-parent completion or downstream authorization | `test_basis_applicability.py::test_mba080_no_activation_or_parent_completion` |

## Preserved gates and remaining blockers

Nutrition Root, MTR-006 v1 structural synthesis and MTR-007 estimator remain FROZEN. FullMTR-006/007/008
remain INCOMPLETE and parent issues OPEN. Production Nutrition/clinical content remains CLOSED.
No clinical measurement bridge, conversion/retention/yield coefficient, actual population/protocol,
qualified production actor, provider, publication, seed or default is authorized by this implementation.

Production scientific evidence, verified qualification/source/publication governance, and independently
reviewed clinical applicability remain separate unresolved production gates. They do not block this
bounded symbolic TEST_ONLY implementation and cannot be filled by a hash or synthetic qualification.
MTR-006 policy-integration v2 remains a separate design/implementation gate; frozen v1 is unchanged.
No MTR-008, solver, planner activation, Execution or PRECOMMIT work is included. planner_ready=False;
activation_ready=False; Execution NOT STARTED; PRECOMMIT FAIL-CLOSED.

**IMPLEMENTATION READY FOR INDEPENDENT REVIEW / FREEZE CANDIDATE. NOT SELF-APPROVED OR FROZEN.**
Leave the PR OPEN with auto-merge OFF. STOP for independent implementation review.
