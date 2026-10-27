# Post-MTR-040C — Parent MTR-040 Completion Review

Status: **COMPLETION REVIEW APPROVED — MTR-040 COMPLETE; ISSUE #41 CLOSED / COMPLETED**.
The separately authorized closure is recorded in §12. The original review remains documentation-only;
no runtime or downstream implementation is authorized.
Reviewed 2026-10-27 against canonical `69241affc2d85ee534ca682a0ff9a4d23a7c7862`.

## 1. Verdict and decision boundary

**Selected conclusion A: MTR-040 COMPLETE — its canonical acceptance is satisfied.**

```text
MTR-040 COMPLETION REVIEW — PASS
MTR-040 ELIGIBLE FOR COMPLETION / ISSUE #41 CLOSURE
```

At review time, PR #108 was a completion recommendation: issue #41 remained OPEN and tracking
remained PARTIAL / closure approval pending. The user subsequently authorized the separate §11
gate; after exact post-merge verification, §12 records the completed issue/status action.
No remaining implementation slice or MTR-039 prerequisite is established by the audited acceptance.

The conclusion covers member-owned hierarchical feature/direct preference and evidence strength,
with implemented lifecycle, provenance, verification and explicit limitations. It does not certify
the entire ADR-011 learning loop, a populated production corpus, a consumer onboarding workflow,
shared-meal utility, global exposure history or a production-ready planner. Those are distinct
requirements with their own backlog entries and unresolved gates.

## 2. Canonical baseline and freeze receipts

`origin/main` was fetched before review and is exactly the SHA above. The checkout was clean.
The merge has parents `b591464e3ca495909851217141f96a55faaa35cc` and the approved implementation
head below; its file tree equals the approved head. No additional implementation was introduced.

| Receipt | Verified identity / evidence |
| --- | --- |
| Parent acceptance | [Issue #41](https://github.com/thedusk4203/Menuto/issues/41), OPEN; body inspected directly |
| MTR-040C implementation | [PR #107](https://github.com/thedusk4203/Menuto/pull/107), MERGED; reviewed head `b138ae7eee9ca9a94dd0a00a0f4e2eb0782d80b0` |
| Implementation review | [Comment6434925372](https://github.com/thedusk4203/Menuto/pull/107#issuecomment-6434925372), PASS on that exact head; GitHub self-APPROVE rejection does not erase this explicit user review receipt |
| Merge/main/freeze SHA | `69241affc2d85ee534ca682a0ff9a4d23a7c7862` |
| Exact post-merge push CI | [40459191498](https://github.com/thedusk4203/Menuto/actions/runs/40459191498), SUCCESS on the exact merge SHA; python/web SUCCESS |
| Baseline verification | 2,978 tests passed;1,070 real-PostgreSQL cases retained; SCRAM/TLS16/16; benchmark22/22; client10/10; architecture/import/export/typecheck/build checks passed |
| Current schema / exports | Alembic0015 /85 domain tables /358 exported definitions; no0016 or production hierarchy defaults |

The user expressly declared **MTR-040C FROZEN** after that exact post-merge verification.
Earlier IMPLEMENTED / NOT FROZEN and do-not-merge wording in its delivery documents is historical.
The corrected current headers and this receipt supersede status wording, not frozen behavior.

| Frozen foundation | Canonical receipt inspected |
| --- | --- |
| 040A, including inverse authorship correction | [Foundation status: User freeze040A](FOUNDATION_STATUS.md#user-freeze040a-and-mtr-041a-preview-source-subset), freeze `06dc1dcbf38d474b90f7bfb74f04651e884285e4`; [original evidence](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_EVIDENCE.md), [0012 correction](MTR_040A_AUTHORSHIP_CORRECTION_EVIDENCE.md) |
| 040B | [Freeze/evidence](MTR_040B_EXPLICIT_TARGET_AFFINITY_EVIDENCE.md), PR #90 head `6ef6b8f9d64a6b1c45fce570857d3cd0568385c6`, merge `08ddeb87604b8913175ae3852a32ce6f4b8d1273`, exact push CI40215578850 |
| Reviewed exact-target prior source | [Freeze receipt](PREFERENCE_PRIOR_SOURCE_FREEZE_RECEIPT.md), PR #97, merge `fce85327cc8c3f4444847522d8ef474ef8d4e670`, exact push CI40293195051 |
| Exact-target compatibility/shrinkage | [Freeze receipt](EXACT_TARGET_PRIOR_SHRINKAGE_FREEZE_RECEIPT.md), PR #100, merge `5728411ac12555f583f8df72ac71861998978aa4`, exact push CI40351934792 |
| Hierarchy relation/transfer-policy SOURCE | [Freeze receipt](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_FREEZE_RECEIPT.md), PR #104, merge `ee8a4de1b1c71ccbd56ea565e111718660711fa8`, exact push CI40432057006 |
| 040C | [Approved design](MTR_040C_ONE_HOP_HIERARCHICAL_MEMBER_PREFERENCE_CONSUMER_DESIGN.md), [HC01–HC81 evidence](MTR_040C_ONE_HOP_HIERARCHICAL_MEMBER_PREFERENCE_CONSUMER_EVIDENCE.md#acceptance-mapping), PR #107 receipt above |
| Relevant classification support,046A | [Implementation/freeze evidence](MTR_046A_IMPLEMENTATION_EVIDENCE.md), PR #85, merge `428b992892ac2aeebdbedb8bb3fd5e436e76415c`, exact push CI40172577535 |

Historical freeze receipts are documentary lineage. The current exact-merge CI above is the
combined regression receipt; this review does not claim newly rerunning every historical CI job.

## 3. Requirements and interpretation method

Issue #41 has two canonical acceptance items:

> Hierarchical feature/direct affinity + evidence strength + explicit ownership.

> Có implementation và kiểm chứng phù hợp; ghi rõ invariant/ADR tác động, provenance và giới hạn.
> Không dùng namespace, tài liệu hoặc synthetic smoke test làm bằng chứng đã hoàn tất nghiệp vụ.

The issue links [Development Spec V1.3](../MENUTO_DEVELOPMENT_SPEC_V1_3.md), especially §9,
§19.2–19.8, §20.2 and §21; [ADR-011](../adr/ADR-011-behavioral-learning-loop.md);
[INV-003/022–029](../ARCHITECTURE_INVARIANTS.md); and the baseline migration policy.
The review also read BACKLOG, FOUNDATION_STATUS, both implementation blueprints,
INVARIANT_COVERAGE, the glossary and the frozen design/evidence/runtime/test sources cited below.

Spec §19.3 and ADR-011 decision2 identify the member owner, five affinity dimensions and ordinal
evidence strength, with weak-evidence shrinkage and possible feature generalization. They do not
prescribe a recursive graph, multiple-parent reducer, inherited strength formula, a database table
named MemberBehaviorProfile, or one final scalar. §19.2 / issue #40 separately assign event
classification/routing; §19.4 / issue #42 assign exposure; §19.7 / issue #43 assign learned-rule UX.

These are scope findings from the canonical text, not a claim that frozen limitations alone can
waive a requirement. Prior dependency reviews kept040 PARTIAL pending this parent audit; their
provisional broader-learning gaps are reassessed against the original acceptance here, not copied
as new requirements. Milestone numbering is not used as a dependency proof.

The existing484-node Graphify graph was used for navigation to canonical ADR/spec vocabulary only.
It predates the new consumer and cannot establish its implementation. No rebuild or LLM extraction
was performed (0 extraction tokens); runtime, tests and exact freeze receipts determine this review.

## 4. Atomic acceptance → implementation → verification

SATISFIED means the audited MTR-040 obligation has implementation and evidence. OUT OF SCOPE
does not mean the broader capability is implemented. No required obligation was found PARTIALLY
SATISFIED or NOT SATISFIED; proposed extras are classified separately in §9.

| ID / atomic obligation | Classification | Concrete implementation and evidence |
| --- | --- | --- |
| A01 Member subject is HouseholdMember, distinct from actor/household | SATISFIED | [Preferences contracts](../../apps/backend/app/modules/preferences/contracts.py): `PreferenceWriteCommand`, `MemberPreferenceDeclarationFact`, `ExplicitMemberPreferenceSnapshot.replay`; [service](../../apps/backend/app/modules/preferences/public.py): `PreferenceService._access`; [real-PG ownership tests](../../apps/backend/tests/test_postgres_preference_integrity.py): `test_member_actor_scope`, `test_proxy_subject_is_explicit_not_shared_copy`, `test_same_retry_key_cannot_fan_out_to_another_member` |
| A02 Authorship is verified, not caller-minted | SATISFIED | [Frozen0012 SQL](../../apps/backend/migrations/versions/0012_preference_authorship_semantics.py): bidirectional SELF/representative check under membership lock; [authorship tests](../../apps/backend/tests/test_postgres_preference_authorship.py): `test_service_authorship_exact_match`, `test_sql_authorship_exact_match`; historical labels are retained, not retroactively certified |
| A03 All five exact direct-affinity target kinds | SATISFIED | [040B contracts](../../apps/backend/app/modules/preferences/contracts.py): `TargetKind`, canonical manifests, complete `ExplicitTargetAffinityPolicy`; [040B capture](../../apps/backend/app/modules/preferences/profile_capture.py); [real-PG identity tests](../../apps/backend/tests/test_postgres_target_affinity.py): `test_owner_identity_capture_and_never_declared_targets`, `test_random_nonexistent_target_rejected_by_owner_read` |
| A04 LIKE/DISLIKE/NEUTRAL, UNDECLARED, RETRACTED and real zero remain distinct | SATISFIED | `MemberPreferenceState`, `_explicit_target_affinity_rows` in [contracts](../../apps/backend/app/modules/preferences/contracts.py); [040B tests](../../apps/backend/tests/test_target_affinity.py): `test_latest_head_only_correction_change_retraction_restore`, `test_explicit_zero_is_available_distinct_from_absence_and_retraction`, `test_nonzero_neutral_asymmetric_coordinates_are_not_replaced_by_defaults` |
| A05 Direct EvidenceStrength is derived ordinal policy metadata | SATISFIED | `DerivedExplicitEvidenceStrength`, authorship rules and current-head derivation in [contracts](../../apps/backend/app/modules/preferences/contracts.py); [direct tests](../../apps/backend/tests/test_target_affinity.py): `test_active_value_is_separate_from_policy_strength`, `test_self_proxy_authorship_is_preserved_without_implicit_order`; [PG retries](../../apps/backend/tests/test_postgres_target_affinity.py): `test_hundred_idempotent_retries_do_not_change_frontier_or_strength`; [raw SQL guard tests](../../apps/backend/tests/test_postgres_preference_integrity.py): `test_no_raw_strength_columns_or_global_conversion` |
| A06 Actual reviewed feature/direct hierarchy exists | SATISFIED | [Hierarchy contracts](../../apps/backend/app/modules/preferences/hierarchy_contracts.py): full25-cell policy, typed relations and RecipeVersion bindings; [source replay](../../apps/backend/app/modules/preferences/hierarchy_resolution.py); [040C runtime](../../apps/backend/app/modules/preferences/hierarchical_affinity.py): `_inherited`; [HC tests](../../apps/backend/tests/test_hierarchical_affinity.py): `test_hc01_hc42_hc69_all25_exact_typed_directions`; [context tests](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py): `test_hc42_hc43_exact_recipe_classification_context` |
| A07 Direct evidence and corrections take precedence over inheritance | SATISFIED | `_inherited` uses raw destination state before parent mapping; [HC17–24 tests](../../apps/backend/tests/test_hierarchical_affinity.py), including `test_hc19_hc20_nonzero_neutral_and_explicit_zero_suppress`, `test_hc06_hc21_optional_parent_for_suppression`; source corrections retain old replay and change fresh eligibility in [source replay tests](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py) |
| A08 Hierarchy preserves one member and exact target/coordinate binding | SATISFIED | [040C runtime](../../apps/backend/app/modules/preferences/hierarchical_affinity.py): `_derive_fields`, `_ledger`, `_immutable_facts`; [HC04/08/11–16/57–60/69/81 tests](../../apps/backend/tests/test_hierarchical_affinity.py); every repeated immutable typed fact is checked across both explicit/prior inputs and hierarchy cuts |
| A09 Versioned prior compatibility, cold start and weak-evidence shrinkage | SATISFIED | [Prior source contracts/resolution](../../apps/backend/app/modules/preferences/reference_prior_contracts.py), [pure prior resolver](../../apps/backend/app/modules/preferences/reference_prior_resolution.py), [PR #100 contracts](../../apps/backend/app/modules/preferences/prior_affinity_contracts.py), [derivation](../../apps/backend/app/modules/preferences/prior_affinity.py): `_blend`, `_derive_fields`; [tests](../../apps/backend/tests/test_prior_shrinkage.py): `test_c20_exact_blend_all_five_kinds`, `test_c24_cold_start_does_not_mint_strength`, `test_c33_ordinal_policy_chooses_exact_authored_weight` |
| A10 Canonical lifecycle, provenance and correction/retraction replay | SATISFIED |040A immutable streams/frontier and [0011](../../apps/backend/migrations/versions/0011_explicit_member_preferences.py)/[0012](../../apps/backend/migrations/versions/0012_preference_authorship_semantics.py); [integrity tests](../../apps/backend/tests/test_postgres_preference_integrity.py): correction/retraction/retry, direct DML protection, concurrency, revocation and RR capture; prior/hierarchy source append/CAS/idempotency and capture are separately implemented in frozen0014/0015 |
| A11 Derivations reject edited cached children/trace/hashes | SATISFIED | [040B derivation](../../apps/backend/app/modules/preferences/profile_derivation.py), PR #100 and [040C root validator](../../apps/backend/app/modules/preferences/hierarchical_affinity_contracts.py): primitive recomputation; [HC70–76](../../apps/backend/tests/test_hierarchical_affinity.py), [cached-source/late-policy tests](../../apps/backend/tests/test_hierarchical_affinity_source_replay.py); [compatibility pins](../../apps/backend/tests/test_hierarchical_affinity_compatibility.py) |
| A12 Verification is substantive, with documented invariant impact and limits | SATISFIED | Frozen040A/B, prior, PR #100, hierarchy SOURCE and040C evidence above plus current exact post-merge CI; real-PG owner/authority/concurrency/SQL/capture tests and actual pure child replay, not a namespace or synthetic benchmark alone; §§5–10 document impact, provenance and limits |

## 5. Ownership, direct affinity and EvidenceStrength

040A stores member declarations under an exact household/member. The actor has authenticated
membership and an audited authorship mode; it is not the owner merely because it wrote the row.
The corrected rule is SELF iff the canonical actor's linked member equals the subject; representative
iff different, including an unlinked actor where authorized. No household/participant fan-out occurs.
Historical0011 mislabels are not rewritten or retroactively declared truthful by0012.

040B captures canonical owner identity and interprets all five kinds independently. Current
LIKE/DISLIKE/NEUTRAL yields an explicit rational coordinate and policy-derived strength;
UNDECLARED/RETRACTED have no active explicit strength. A numeric zero is still a declaration.
Only the current head counts. History length, retry count and exposure events cannot upgrade strength.
NONE/LOW/MEDIUM/HIGH are ordinal categories; MEDIUM is the frozen middle wire literal.
Neither affinity nor EvidenceStrength is a probability, statistical confidence or calibrated utility.

PR #100 retains the member/target from040B. A global prior cannot become a member declaration,
and prior-only cold start cannot mint strength. Hierarchy SOURCE is global reviewed reference
truth, **not member data**; it cannot claim HouseholdMember authorship. Its independent publisher
authorization is tested, including [household/prior credentials denied](../../apps/backend/tests/test_postgres_hierarchy_authority.py):
`test_a02_real_household_roles_and_self_authorship_do_not_authorize_source` and
`test_a02_prior_credentials_and_grants_not_hierarchy_authority`.

040C requires the parent/destination to share the same household/member and complete declaration
ledger. Only the observation clock is excluded from ledger equivalence; all original cuts remain
in the result. This prevents an older destination cut from hiding a correction visible in the parent.
There is no cross-member transfer authority. Its inherited component explicitly has
`evidence_strength=NOT_DERIVED`; the complete frozen parent's strength is retained as lineage.

That fulfills the parent strength requirement through the direct component. Issue #41, Spec §19.3
and ADR-011 do not require an inherited ordinal on every value. Minting/propagating one now would
change the approved source/consumer boundary without a canonical unmet acceptance to justify it.

## 6. Hierarchy breadth and prior/shrinkage boundary

The system has executable hierarchy, not just a vocabulary or source label: a reviewed relation
and policy are published through protected SQL, captured coherently, replayed, and consumed as one
exact member's mapped explicit lineage. All25 typed kind-pairs can be explicitly enabled, with
exact owner/context support; this does not populate or enable any production pair automatically.

Only one hop and one active incoming relation are supported. Multiple incoming heads remain
unavailable before support/member eligibility filtering; there is no favorable-parent choice,
deduplication of diamonds, recursive inherited parent, traversal or aggregation. These are compatible
with canonical acceptance: the cited texts require hierarchical feature/direct affinity, not a
recursive or multi-parent algorithm. Separate human approval already froze the bounded mapping.

Direct LIKE/DISLIKE/NEUTRAL/zero at the destination suppresses inheritance; retraction suppresses
it distinctly. This implements stronger direct evidence as **semantic precedence**, not an invented
numerical ratio across incompatible coordinates. Exact finite semantic mapping followed by positive
authored attenuation limits the mapped inherited point; it does not prove a common scale with the
raw040B or PR #100 scalar. Raw or mapped sign never supplies the semantic label; inherited neutral
is exact available0/1. No global weight or hierarchy strength equation is implied by the spec.

PR #100 is **required supporting parent functionality for the §19.3/ADR-011 weak-evidence and
cold-start story**, not an unrelated optional extra; its reviewed source is the necessary source
foundation. It maps explicit and one exact-provider reference through a finite policy into the
same scoped descriptor before exact rational shrinkage. The ordinal policy enforces
LOW prior influence >= MEDIUM >= HIGH, with active influence <1. Actual weights, including an
explicitly authored zero influence, are policy choices; this review invents no universal positive
weight, production calibration or default prior. Missing/unmapped/retracted prior stays honest.

040C uses mapped_explicit from either explicit-only or blended parent lineage, **never** the
effective blend, prior contribution or prior-only value. Changes only to prior/shrinkage can change
provenance without changing inheritance. A destination prior-only component can coexist separately
with inheritance; there is no blend, chooser or ranking between them. The full published transfer
policy fingerprint defines the inherited coordinate; shrinkage provenance does not redefine it.

## 7. ADR-011 / INV-022–029 impact

Every invariant still applies. The table separates protection at the MTR-040 boundary from global
learning-loop enforcement; parent completion does not certify inactive event-routing code.

| Invariant | Current MTR-040 protection / concrete evidence | Remaining global work, outside this completion |
| --- | --- | --- |
| INV-022 passive assumptions must not create durable learning |040A accepts EXPLICIT_DECLARATION/USER source;040B rejects nonexplicit inputs;040C has no passive input or durable writes; `test_nonexplicit_inputs_cannot_enter_profile` in [040B tests](../../apps/backend/tests/test_target_affinity.py), HC09/77/78/80 | Passive event quarantine/provisional assumption lifecycle is not implemented here; MTR-039/041/Execution remain separately gated |
| INV-023 friction must not penalize taste | No retail/time/friction event input, source policy or mutation route in the profile interfaces; extra-forbid and import/zero-IO tests | Actual contextual/retail event attribution belongs to MTR-039, not a claimed profile feature |
| INV-024 cooked must not mean liked | No cooked evidence ingestion; [PG040B tests](../../apps/backend/tests/test_postgres_target_affinity.py): `test_feature_exposure_proposals_cannot_change_explicit_profile`; HC80 preserves unavailable behavioral evidence | Cooked→context/exposure routing is absent, not certified complete |
| INV-025 rejection is weak, not confirmed dislike | Only actual member declarations create explicit dislike; `EvidenceStrength` is derived from approved authorship policy, never caller rejection/count | Classifying and weighting unattributed rejection requires a future attributed-evidence path |
| INV-026 member ownership survives shared meals | Actor/subject SQL guards, member-scoped streams, independent040B capture, PR #100 outer binding,040C same-ledger check; A01/A02/A08 | Shared-meal preference aggregation is not implemented/authorized; global coverage remains partial |
| INV-027 separable dimensions until utility | Five typed exact targets and scoped coordinates, separate direct/prior/inherited outputs; no final scalar or cross-target aggregation; HC59/60/67/69/80 | Full taste/context/time/equipment/repeat/novelty composition belongs to MTR-024; not a profile acceptance prerequisite |
| INV-028 learned observations cannot rewrite explicit policy | Append-only explicit history; no learned write/event source; parent corrections/retraction suppress inheritance or change fresh replay | Learned-rule show/reset/invalidate/promote UX and suppression of re-inference from new event models remain MTR-042/future attributed learning work |
| INV-029 forced tradeoffs are not voluntary preference | No forced-conflict event input; USER explicit assertions cannot be synthesized from proposal/execution facts by these modules | Forced-resolution signal quarantine is MTR-039/MTR-031 work; no such router is claimed present |

INV-003 additionally supports the member ownership verdict. INV-009/018/017 support explicit
coordinate/provenance and primitive recomputation discipline; the consumer grants no independent
validator or PRECOMMIT authority. No invariant/ADR wording is changed. INV-026/027 coverage notes
are synchronized to existing partial foundations rather than retaining the false claim that no
actor-scoped writes or separable profile dimensions exist at all.

## 8. MTR-039 dependency proof

[Issue #40](https://github.com/thedusk4203/Menuto/issues/40) is OPEN and requires
DIRECT/CONTEXTUAL/INFERRED/PASSIVE → taste/context/exposure/retail/no-learn routing.
[Learning namespace](../../apps/backend/app/modules/learning/__init__.py) explicitly says routing
implementation is not provided. Existing Learning contracts/runtime implement proposal-local
exposure/repeat computations, not this classifier/router. No MTR-039 capability is inferred from
an enum in documentation or from the word INHERITED in040C.

The current dependency path is:

```text
HouseholdMember + canonical explicit declarations (040A)
    → policy-interpreted direct affinity + ordinal strength (040B)
    → exact-target prior-compatible derived view (PR #100 + reviewed prior source)
    → same-member one-hop interpretation (040C + reviewed hierarchy SOURCE)
```

Every required A01–A12 obligation has an implemented path above. The consumer imports the frozen
preference/owner contracts and pure child resolvers, not Learning routing; its complete input seam
contains no new behavioral-event stream. Real source persistence and primitive replay tests execute
this path without any SignalAttributionRouter. Missing prior/relation/support has a defined
unavailable result; it does not require a router to fabricate evidence.

The distinct future path would be:

```text
cooked / swap / skip / retail / forced / passive event
    → classify + attribute + quarantine (MTR-039)
    → an explicitly designed, member-scoped learned observation consumer
    → optional later profile interpretation / reset or promotion policy
```

**MTR-039 is NOT required for MTR-040 completion under the audited acceptance.** There is no
unmet A01–A12 obligation that needs the second path. It is a real dependency for activating broader
learned/contextual/inferred behavioral inputs, not a retroactive prerequisite for the existing
member-owned explicit/hierarchical capability. PASS does not implement or authorize that path.

## 9. Aggregate, persistence and proposed extra requirements

Spec §9 names PreferenceSignal/PreferenceProfile conceptually; §19.3 names MemberBehaviorProfile;
§20.2 requires a behavior-profile schema. None specifies a literal materialized object/table,
one class containing every target, a new write lifecycle or an eagerly composed global scalar.
040A supplies the durable member-owned schema and complete ledger;040B/PR #100/040C supply typed,
recomputable views over it. 040B can capture explicitly requested sets; the later consumers
deliberately retain one-exact-target boundaries. A batch profile API is not necessary to prove
five-kind support, and no existing frozen contract should be widened to manufacture one.

The raw snapshot's frozen `profile_derivation=NOT_IMPLEMENTED` describes that040A source contract,
not the absence of later additive derivation interfaces. Likewise,040B's unavailable prior/shrinkage
fields remain correct for040B; PR #100 adds a separate capability rather than rewriting them.

Existing append/CAS/idempotency/retraction and historical replay cover canonical explicit,
reference-prior and relation/policy source truth. Derived views are read-only values, so they need
no independent CAS, persistent cache or materialization retraction. Fresh corrections are recomputed;
old immutable cuts remain historical results, not current authorization tokens. No additional table,
migration, repository, materialized profile or canonical aggregate is required by this audit.

| Candidate extra obligation | Classification for parent040 | Reason / separate boundary |
| --- | --- | --- |
| Active learned/contextual/inferred behavioral ingestion | OUT OF SCOPE | No such requirement in issue #41; §19.2 / MTR-039 and future observation consumers govern admission |
| Durable learning from passive assumptions | OUT OF SCOPE and prohibited | INV-022 forbids treating assumptions as durable evidence; no completion gate should demand it |
| Recursive/multi-parent/inherited-parent computation | OUT OF SCOPE | No canonical requirement; frozen one-hop/no aggregation provides actual hierarchical interpretation |
| Inherited EvidenceStrength propagation | OUT OF SCOPE | Direct strength is implemented and preserved; no canonical propagation formula exists |
| Literal MemberBehaviorProfile table/class, batch API or cache | OUT OF SCOPE | Durable source schema and pure typed views exist; naming alone is not a persistence requirement |
| Production onboarding/prior/relation corpus and calibration | OUT OF SCOPE | Consumer capability is implemented/tested; production content/coverage and onboarding remain separate approved publication/UX gates |
| Household aggregation, TasteFit, candidate ranking or safety integration | OUT OF SCOPE | Spec §19.5 / MTR-024 and later planner/validation gates own utility; profile facts are not planner weights |
| Learned-rule UX / global exposure / Execution / PRECOMMIT | OUT OF SCOPE | Separate MTR-042/041 and operational/validation requirements remain incomplete |

No required acceptance is left partially satisfied or externally blocked. These exclusions do not
claim the broader architecture is finished. A new canonical requirement discovered later must be
reviewed as its own scope decision; it must not be silently folded into this completion verdict.

## 10. Verification quality and limits

The evidence is not namespace/doc/benchmark-only.040A/0012 exercise service and real SQL authorship,
concurrency, history and migration round trips.040B tests real owner reads and coherent RR/SERIALIZABLE
cuts. Prior and hierarchy sources exercise actual PostgreSQL privileges, SCRAM/TLS, grant revocation,
CAS/idempotency, lifecycle/support and full-cut replay. PR #100 and040C tests recompute actual frozen
children from primitive fixtures, including adversarial cache/descriptor tampering, raw/mapped
coordinate distinctions and zero-IO guards. The exact-merge suite retains those tests together.
Synthetic policy fixtures exercise the pure computation; benchmark22/22 alone would not prove it.

This audit did not access a production database or certify population, calibration or deployment
provisioning. Missing reviewed content remains unavailable, never an invented neutral/zero prior.
Offline self-consistency does not prove canonical DB origin, live grants or simultaneous currency
of independent source cuts. Full-source fingerprints retain complete history/manifests/diagnostics,
not just visible target rows. Equal scoped fractions imply neither exact-target equality nor
cross-target ranking/aggregation/utility comparability. Frozen040C remains one hop, not a general
hierarchical recommender; no behavioral event is promoted to DIRECT or durable learning.

Local validation for this docs-only PR passed: 51 existing architecture/baseline tests, architecture
baseline and import-boundary checks, Ruff, OpenAPI/domain-contract export checks, 22 synthetic
fixture checks and the client contract check. All 25 explicitly named test references in this review
were checked against the actual test definitions. Its exact-head Foundation CI receipt is recorded
in the PR delivery record. No runtime test, contract, source policy, schema, migration or production
data is changed by this review.

## 11. Proposed next gate — separate human closure approval

No new implementation slice is recommended for the audited parent acceptance. The next gate is
**approval of this completion review and the exact parent closure/status changes below**:

1. Accept conclusion A and A01–A12 as satisfying issue #41's existing acceptance, with §§7–10 limits.
2. Only after explicit approval, check both acceptance boxes on issue #41, link this review and the
   canonical040C freeze/CI receipts, and close issue #41 as completed.
3. In that separately approved documentation/status action, change the parent BACKLOG/status
   entry from PARTIAL / closure pending to COMPLETE, recording canonical acceptance satisfied;
   retain frozen040A/B/C and source/PR #100 identities, provenance and limitations unchanged.
4. Preserve full041/046 PARTIAL,039 OPEN,024/020B/021 BLOCKED, Execution NOT STARTED,
   PRECOMMIT FAIL-CLOSED, planner_ready=False and activation_ready=False. Do not infer readiness of
   any downstream milestone from closing a preference-domain acceptance item.

**PR #108 originally performed none of steps 2–3.** Its do-not-merge/closure-pending gate was
subsequently superseded by explicit user approval and the verified closure in §12. This does not
complete the wider learning loop, start downstream design/implementation or modify frozen semantics.
No new runtime code, tests, policies, migration or seeds are authorized.

**MTR-040 COMPLETION REVIEW — PASS. The separate closure approval and verification are complete below.**


## 12. Approved closure receipt

The user accepted the review in [comment 6436813145](https://github.com/thedusk4203/Menuto/pull/108#issuecomment-6436813145)
and directly authorized merging the exact head, then closing issue #41 and synchronizing canonical
status only after exact post-merge CI and scope verification. Those gates passed on 2026-10-27.

| Closure gate | Verified receipt |
| --- | --- |
| PR #108 | MERGED from reviewed head `d30f9f610af937f2e59fb4eea5962478037ff414` |
| Actual review merge/main SHA | `959e7fa3488e0c379ab37044c25da74292c2d76b`; fetched from main after merge, not a pre-merge prediction |
| Merge parents | `69241affc2d85ee534ca682a0ff9a4d23a7c7862` and reviewed head `d30f9f610af937f2e59fb4eea5962478037ff414` |
| Scope verification | Merged tree exactly equals reviewed head; exactly 10 Markdown files against reviewed base; no unrelated main delta |
| Exact post-merge CI | [40486320021](https://github.com/thedusk4203/Menuto/actions/runs/40486320021), event=push, exact SHA above, SUCCESS; python/web SUCCESS |
| Full verification | 2,978 pytest cases passed; SCRAM/TLS 16/16; synthetic benchmark 22/22; client 10/10; architecture/import/contracts/typecheck/build/OpenAPI/domain-export checks passed |
| Exports / schema | 358 definitions; Alembic 0015 / 85 domain tables; no migration 0016 |
| Issue #41 | [CLOSED / COMPLETED](https://github.com/thedusk4203/Menuto/issues/41), state_reason=completed; both canonical acceptance boxes checked |
| Parent status | **MTR-040 — COMPLETE**, against the existing canonical acceptance only |

This receipt's SHA identifies the review merge whose successful push CI authorized closure.
The later status-only documentation commit does not replace the frozen implementation identity
or imply additional runtime capability. Its own PR/merge checks are recorded in its delivery record.

PR #108 introduced no runtime/contracts/tests/migrations or production hierarchy defaults,
coefficients or rows: its full delta is Markdown only. Frozen 040A/B/C, prior source, PR #100 and
hierarchy SOURCE are unchanged. No production database population/calibration is certified.
No materialized profile, persistence expansion, recursive/multi-parent hierarchy, inherited
EvidenceStrength or behavioral-event learning is added.

Full 041/046 remain PARTIAL; MTR-039 OPEN; MTR-024/020B/021 BLOCKED; Execution NOT STARTED;
PRECOMMIT FAIL-CLOSED; planner_ready=False; activation_ready=False. No next milestone, planner
or learning-loop work is selected, authorized or started by this closure.

**MTR-040 — COMPLETE. Issue #41 — CLOSED / COMPLETED.**
