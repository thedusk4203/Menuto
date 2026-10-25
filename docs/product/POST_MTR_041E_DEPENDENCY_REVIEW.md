# Post-MTR-041E — dependency review for the remaining behavioral foundations

Status: **DEPENDENCY REVIEW ONLY — next design/implementation not authorized or frozen here**.

Reviewed latest canonical `main`: **`146c7cee9915c91593c4ec7518615e065d7abf53`**, PR #87.
The user has **FROZEN / APPROVED MTR-041E** at that commit. Schema is **0013 /71 domain tables**;
the domain export has237 definitions. No migration/runtime/contracts/tests/exports change in this
review. No correction to041E is required or proposed.

## 1. Decision

Recommend **designing remaining MTR-040's explicit-source, target-level MemberBehaviorProfile
derivation next**, before adding feature cooldown/decay/RepeatPenalty policies. Suggested name:
**MTR-040B — Explicit-source Target Affinity Profile Foundation**, subject to architecture approval
of suffix and detailed scope. No existing reserved040B was found in the inspected code/backlog.
This is a proposed subset of canonical040, not a renumbering or completion of the root task.

This branch has genuine reusable source truth now: frozen040A member-owned declarations, complete
member source history/frontier and reviewed target vocabulary. What is missing is an approved
**interpretation contract/policy** for affinity, derived EvidenceStrength and applicable priors.
Therefore it is **PARTIALLY READY for detailed design; not implementation-ready** under this review.
It should produce more than another wrapper around `state_for()`: a proposed profile needs an
auditable target interpretation, evidence basis, policy identity and explicit availability semantics.
Those decisions must be reviewed before code or numeric defaults are introduced.

Feature-aware041 policies are independently designable over frozen041E's supported preview facts.
They are not blocked by MemberBehaviorProfile, and remaining040 is not a fabricated upstream
dependency of full041. Choosing040 next is a prioritization decision: it fills the currently absent
preference dimension needed alongside exposure for later024, rather than adding another optional
interpretation to the exposure branch first. Neither branch alone unblocks024/020B/021.

## 2. Canonical references and current source inventory

Read against [spec§19.2–19.5](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[ADR-011](../adr/ADR-011-behavioral-learning-loop.md),
[ADR-004](../adr/ADR-004-household-first-model.md),
[ADR-009](../adr/ADR-009-execution-state-machine.md),
[ADR-010](../adr/ADR-010-independent-validator.md),
[invariants](../ARCHITECTURE_INVARIANTS.md), [backlog](BACKLOG.md),
[blueprint](IMPLEMENTATION_BLUEPRINT_M0_M1.md), [foundation status](FOUNDATION_STATUS.md),
[040A source review](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_REVIEW.md),
[authorship correction](MTR_040A_AUTHORSHIP_CORRECTION_EVIDENCE.md),
[post041D review](POST_MTR_041D_DEPENDENCY_REVIEW.md),
[046A/041E design](POST_MTR_046A_DEPENDENCY_REVIEW.md) and
[041E evidence](MTR_041E_FEATURE_EXPOSURE_EVIDENCE.md).
Older NOT FROZEN/schema references in historical implementation records describe their original
delivery stages; the user's later freeze decisions and current source are authoritative.

| Directly inspected source | What actually exists | What it does not provide |
| --- | --- | --- |
| `preferences/contracts.py` | Five typed target kinds; raw LIKE/DISLIKE/NEUTRAL; SET/RETRACT lineage; subject/actor/authorship; explicit source provenance; member sequence/frontier; deterministic immutable complete snapshot and `state_for()` | No numeric affinity, EvidenceStrength, prior, shrinkage, candidate TasteFit or learning policy |
| `PreferenceService.snapshot()` in `preferences/public.py` | **Already enforces clean read-only RR/SERIALIZABLE**; canonical actor/member read, full member frontier/stream/declaration history and exact referenced reviewed vocabulary | No new capture prerequisite is needed merely to read the existing explicit source; it is not a derived profile or live authorization receipt |
|040A/0012 append boundary | SELF iff linked subject, representative iff different/NULL link with permitted role; immutable source audit; correction/retraction/CAS/idempotency | Authorship does not itself specify strength, affinity magnitude or confidence |
| `catalog/contracts.py` | Immutable reviewed PROTEIN/METHOD/FLAVOR vocabulary with term ID/version/provenance | No population/onboarding preference priors; a vocabulary term is not a prior or preference |
| Frozen046A Recipes/Catalog contracts | Reviewed METHOD context, FLAVOR/MAIN_PROTEIN exact path, finite universe and pinned association sources | No preference generalization rule, cross-version term reconciliation, allergen/diet classification or prior |
| Frozen041A–E Learning contracts/public | Recipe-ID scoped source/cooldown/decay/penalty; new provisional feature events/support/coverage and diagnostic source-cut identity | No confirmed/accepted/global history, feature policies, preference profile or TasteFit |
| `policy/contracts.py` | Foundation validation coverage definition | No member-profile derivation/prior/shrinkage policy; this is not a complete utility or nutrition policy engine |
| Registered ORM metadata / domain schema |0013 /71; member_nutrition_profiles plus three member_preference tables and existing feature-source tables | No member_behavior_profiles, prior-source store, behavioral event/attribution/history model |
| Existing tests | Explicit declaration replay/authorship/integrity, reviewed source matching, source preview and frozen compatibility | No tests establish a profile derivation or production prior calibration that is absent from runtime |

The existing graph index was used only for orientation; current directly inspected code and
canonical docs determine this review. No runtime contradiction reopening040A or041A–E/046A was found.

## 3. Capability dependency matrix

READY means source primitives exist for the stated scope, not that a proposed consumer is coded.

| Capability | Owner | Existing primitives | Missing primitive / design | Status | Prerequisite MTR | Recommended order |
| --- | --- | --- | --- | --- | --- | --- |
| Member explicit source / exact current target state | Preferences; HouseholdMember owner | Frozen040A snapshot, replay, target identity, authorship, provenance, member frontier | None for supported explicit snapshot | READY |040A FROZEN | Reuse |
| Pure exact-target affinity interpretation | Preferences-owned profile; contract-only pure derivation | Raw current explicit states for ingredient/protein/method/flavor/direct recipe | Approved numeric/type/availability/interpretation policy; immutable profile contract | PARTIALLY READY | Remaining040; proposed040B **design** | **Next** |
| Derived EvidenceStrength | Member profile policy | Actual active source, historical lineage, actor/mode, current source head | Meaning of NONE/LOW/MEDIUM/HIGH; policy mapping/evidence basis; replacement/retry independence | PARTIALLY READY | Remaining040 policy design | With040B design; never caller-authored raw value |
| Prior/shrinkage interpretation | Member profile policy; prior source owner explicit | Exact target IDs and policy/provenance primitives | Approved prior identity/applicability and formula; no production prior data/source currently | PARTIALLY READY for explicit supplied-policy design; BLOCKED for production cold-start prior claims | Remaining040 policy +028 for onboarding-derived priors;046 only where mappings are needed | Resolve availability/source in design; do not silently use0/neutral |
| Hierarchical/direct-to-feature generalization | Preferences/profile policy + Recipes/Catalog mapping | Raw direct recipe/ingredient preferences;046A reviewed matching sources | Approved direction/strength/coverage/conflict policy; term/family reconciliation where needed | PARTIALLY READY | Remaining040 + applicable046 mappings | Defer from first exact-target subset |
| Candidate/member preference fit | Later consumer; target profile remains member-owned | Exact binding,046A classification and raw target preferences | Approved profile, coverage-aware match and conflict/precedence contract | PARTIALLY READY | Remaining040 +046 →024 | After target profile; no TasteFit scalar now |
| MTR-039 explicit-source routing | Learning attribution |040A already labels EXPLICIT_DECLARATION | General router contract/policy absent | PARTIALLY READY for separate design; **not a hard prerequisite for explicit-only040B** |039 for broader event ingestion | Do not invent Execution to feed it |
| Learned/event-derived profile | Learning attribution → profile owner | ADR routing categories and explicit source only | Canonical observations, reasons/context, reset/invalidation and attribution lineage | BLOCKED | Applicable source producers →039 +remaining040;045 where feedback is used | Later; no consumption/like inference |
| Proposal-local METHOD/FLAVOR/MAIN_PROTEIN sources | Learning + Planning capture | Frozen041E with exact reviewed support/coverage | None within approved source scope | READY |041E +046A FROZEN | Reuse unchanged |
| Feature cooldown/decay/penalty | Learning041 policy interpretation | Frozen041E positive events and explicit coverage; Recipe-ID B/C/D demonstrate separate policy patterns | New feature-specific query/coverage/time/weight policy and result contracts; B/C/D cannot be generalized in place | PARTIALLY READY for separate design | Remaining041 after independent policy design | Useful optional parallel/later branch; not required before040 design |
| Accepted-schedule exposure | Planning authority →041 source | Stable plan/revision and sealed proposal truth | Production validation authority, applicable complete validation subjects and commit recheck; accepted-source capture | BLOCKED |026 authority path +016/027 commit seam →041 | Later; preview is not acceptance |
| Confirmed/member-attributed exposure | Execution source →039 →041 | Physical ledger and authored/planned culinary identity | Actual batch/meal evidence, member attribution and correction/coverage/frontiers | BLOCKED |023/035 source path after authority/dependency approval →039→041 | No Execution in this review |
| Assumed provisional exposure |017/036 projection →039/041 | Intent/physical distinctions only | Assumption identities, parents/status/compensation and operational state | BLOCKED |017 +036 →039/041 | Later; no durable passive learning |
| Cross-week/horizon exposure |017/038 projection +041 | Proposal horizons/timestamps, immutable history and physical ledger | Canonical future commitment bridge with lineage and no double count | BLOCKED |017 + applicable023/036 →038→041 | Later; no concatenation of previews |
| Variant-family exposure | Recipe identity/classification | Recipe ID/version only | Authored family identity and explicit version reconciliation | BLOCKED | Remaining046 with018/019 family identity design | Separate source review |
| Global history coverage / novelty |041 source coverage and policy | Local scoped evidence and explicit absence semantics | Applicable authoritative history/source coverage and novelty policy | BLOCKED | Accepted/confirmed/operational/bridge branches +remaining041 | Empty local preview is not novelty |
| Safety classification / COUNT nutrition | Catalog/Nutrition/root validation | Member restrictions, exact ingredient/binding identities, explicit count item_ref | Reviewed safety mappings/coverage; authored count-to-mass or compatible COUNT nutrition references | BLOCKED | Separate046 safety source with005/006/026;006/046 COUNT reference source design | Affinity/classification cannot substitute |
| Separable human utility |024 | Partial profile/exposure inputs, supply evidence | Approved profile/fit, applicable exposure/novelty and nutrition/context/effort policies; no missing-as-zero | BLOCKED | Remaining040/041 +006/007/008 + applicable supply/context sources →024 | No start authorization |
| Role portfolio / feasibility |020B →021 | Frozen020A conservative evidence containment | Complete role inputs, EXPLOIT/EXPLORE/diversity policy and downstream feasibility prerequisites | BLOCKED |024 +approved020B portfolio design →021 | No start authorization |

## 4. Dependency topology and the next narrow design

```text
040A member-owned explicit history + typed target vocabulary
                ↓
remaining040 explicit-target profile / strength / prior-availability policy design
                ↓
approved pure target-level profile subset (future implementation)
                ↓
later coverage-aware recipe/candidate fit + other separable inputs ──→024→020B→021

046A +041A ──→041E feature source (FROZEN) ──→later feature policies ──┘
026 authority ──→accepted-schedule source ────────────────────────────┤
actual source events ──→039 attribution ──→confirmed/history source ──┤
017/036 +038 ──→operational/cross-horizon coverage ───────────────────┘
```

These are dependency branches, not a claim that every future source kind must be fabricated or
that all downstream inputs must share a single global score. Source applicability itself needs
explicit policy. The graph grants no authorization to implement any blocked branch.

The next design should answer, before implementation:

1. **Owner:** HouseholdMember owns the profile; Preferences remains owner of declared/member
   preference semantics. Any pure Learning helper may consume only immutable source contracts;
   it does not become a second preference store or mutate040A. Resolve the concrete contract/API
   placement in the design; no generic cross-domain behavior persistence.
2. **Input scope:** full frozen040A snapshot + explicit versioned interpretation policy and an
   exact finite target manifest. Start with exact declared/retracted target identities. If adding
   requested undeclared ingredient/recipe targets, canonical capture must verify those identities;
   `state_for()` accepting a typed UUID alone does not prove that a row exists. No global target
   coverage or all-catalog neutral profile is implied.
3. **Output:** additive immutable, versioned draft target interpretations, current declaration
   references, preserved raw state, evidence basis and explicit availability of affinity/strength/
   prior/shrunk values. Fully recompute from captured primitives/policy; activation readiness and
   planner suitability must remain conservatively stated.
4. **Correction algebra:** one current target head is an assertion, not every historical revision
   an independent vote. Retries, repeated SETs and INPUT_CORRECTION cannot mechanically inflate
   strength. PREFERENCE_CHANGED supersedes current value; RETRACT preserves history but removes
   active assertion. UNDECLARED ≠ NEUTRAL ≠ RETRACTED remains observable.
5. **Policy:** specify the affinity domain, exact arithmetic and derived EvidenceStrength meaning.
   LIKE/DISLIKE magnitude and EvidenceStrength are separate axes. Explicit authorship does not
   automatically imply HIGH; SELF/representative source modes must not be merged or weighted
   differently without an approved policy. No production numeric constants are chosen here.
   EvidenceStrength is not a calibrated probability. Preserve explicit member_sequence/revision
   replay order; UUID sorting or timestamp ties must not decide which assertion is current.
6. **Priors:** distinguish an explicit versioned policy prior from an actual onboarding/catalog
   observation source. Do not claim the latter exists. If prior/shrinkage cannot truthfully be
   resolved, keep it UNAVAILABLE or fail the relevant required-policy request. A reduced subset
   may be useful, but must not be presented as the complete ADR-011 shrunk planner profile.
7. **Identity/replay:** bind source household/member/frontier, raw snapshot identity, exact target,
   policy and any applicable prior source/provenance into deterministic identity. Preserve all
   frozen source bytes. Policy changes may reinterpret evidence through an explicit new derived
   result; neither policy changes nor fresh capture rewrite declarations or historical profiles.
8. **Separation:** no recipe-to-feature preference transfer, shared-member copying, accepted/
   consumed-history input, ambiguous rejection, cooking-success-as-like, TasteFit aggregation,
   friction penalty, utility/rank/novelty or PRECOMMIT authority in this first subset.

The first subset should be meaningfully derived and auditable, not `LIKE→1` renamed as a complete
MemberBehaviorProfile. If the detailed design cannot meet that boundary with supported policy
inputs, it must return for review rather than inventing priors or weakening unavailable states.

## 5. Concrete counterexamples for the proposed design review

These are design acceptance questions, **not new runtime tests added in this documentation PR**.

| Scenario | Required boundary |
| --- | --- |
| One declaration retried100 times | Idempotency/revision lineage must not mint100 independent observations or higher strength. |
| LIKE→INPUT_CORRECTION DISLIKE | Current value is DISLIKE; old LIKE remains audit, not another positive vote. |
| LIKE→PREFERENCE_CHANGED NEUTRAL | Explicit NEUTRAL retains evidence/provenance; it is not missing data. |
| LIKE→RETRACT | Active assertion absent, history retained; not automatically explicit dislike/neutral. |
| Target never declared | Scoped UNDECLARED; no invented neutral/zero/prior unless explicitly supplied and policy-authorized. |
| Same feature code, new term ID/version | No silent reconciliation, target transfer or double-count aggregation across semantic versions. |
| RecipeA LIKE; RecipeB shares FLAVOR | No inferred RecipeB preference or feature generalization without a separately approved mapping/policy. |
| METHOD preference and exact recipe DISLIKE conflict | Preserve both target facts; first subset does not solve candidate precedence or hard safety. |
| Two members share a meal; one dislikes tofu | No profile fan-out, household-averaged source or loss of member identity. |
| Representative writes about a child | Preserve actual actor/mode/subject; do not assume weaker/stronger evidence based on role alone. |
| Membership later changes | Do not relabel historical immutable authorship or query mutable membership during pure derivation. |
| Empty041E preview, or100 proposed meals | Neither absence nor proposal count creates taste affinity, confidence or EvidenceStrength. |
| User cooked successfully / skipped due to stock | No direct taste mutation; broader observations require039 attribution and actual source truth. |
| Missing onboarding prior | Do not mint a population prior or substitute a universal0; disclose unresolved shrinkage scope. |
| New member preference commits during capture | Old RR snapshot remains coherent, fresh capture gets new frontier; offline derived profile is not a liveness receipt. |
| Policy changes with unchanged declarations | New derived policy identity/provenance; raw040A history and source hash semantics unchanged. |
| Profile DISLIKE vs hard allergen restriction | Soft preference never replaces/excuses root safety; safety taxonomy is still a separate missing source. |

## 6. Migration, blockers and approval boundary

**No migration for this review.** No migration is expected for a narrowly scoped pure derived
explicit-source profile design using already durable declarations and explicit immutable policy
inputs. Do not create a member_behavior_profiles table simply because the conceptual name appears
in the blueprint. A future durable onboarding/prior or learned-observation source could genuinely
require persistence; that would be separately justified, approved and forward-only after0013.
This review does not pre-approve0014 or modify0001–0013.

MTR-039 is not mandatory merely to consume an already typed EXPLICIT_DECLARATION snapshot. It is
mandatory for the later event-derived learning route where meaning/attribution is not already
given by that source. Neither039 nor a profile may fabricate Execution/consumption events.

Full040 cannot be called complete by an explicit-only exact-target subset: hierarchical
generalization, actual prior applicability/shrinkage, broader routed observations and fit consumers
remain separately scoped work. Full041 also remains incomplete afterE. Full046 lacks family,
safety and other coverage mappings.024/020B/021 remain **BLOCKED**. Execution NOT STARTED;
PRECOMMIT fail-closed; diagnostic exposure cuts do not close the production TOCTOU gap.

Next requested approval should be for **MTR-040B detailed design**, not implementation or freeze.
No automatic041F/040B numbering is assigned by merging this review; no root issue is closed.

## 7. Invariant and verification record

INV-022–029, especially member ownership026 and separability027, govern the proposed preference
branch. INV-012/013 keep elapsed/proposed evidence out of confirmed/learned history. INV-015–021
preserve independent primitive validation, safety precedence and fail-closed authorization.
INV-030 remains blocked on actual bridge sources; classification/proposal evidence does not
implement it. This review adds no new runtime invariant enforcement or production capability.

The frozen baseline exact [post-merge CI40183397009](https://github.com/thedusk4203/Menuto/actions/runs/40183397009)
was rechecked during this task: head146c7cee9915c91593c4ec7518615e065d7abf53, completed/success.
Baseline1860 Python /755 real-PG, benchmark22/22 and client10/10 are user-approved freeze evidence.
Current documentation-PR local verification on2026-10-25:

| Gate | Actual result |
| --- | --- |
| Full Python with loopback PostgreSQL18 | **1860 passed**,0 failures/errors/skipped,282.25s; one existing Starlette/httpx warning |
| PostgreSQL-real subset | All existing **755 marked tests** included/passed in the full run; tests are unchanged |
| Prior regression identities | **1860/1860 retained**, XML compared to the frozen041E run;0 new tests |
| Migration/drift/direct-SQL/concurrency | Existing real-PG suite PASS; no migration or database behavior changed |
| Ruff / architecture / imports | PASS;30 invariants,11 ADRs,50 linked tasks,16 registered contexts |
| OpenAPI/domain exports / synthetic fixtures | PASS; all237 domain definitions byte-identical;22 fixtures verified |
| Synthetic benchmark | **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client contracts/typecheck/tests / web build | PASS; client **10/10** |
| Diff scope/whitespace |7 Markdown files only; no runtime/contracts/tests/migrations/exports changes; `git diff --check` PASS |
| PR / exact post-merge CI | Exact head/merge and run links recorded in final delivery after remote verification; no advance PASS inference |

Full command: `.venv/Scripts/python -m pytest --basetemp=.local/post041e-review
--junitxml=.local/post041e-review.xml` with MENUTO_TEST_POSTGRES_URL set to local PostgreSQL18
and isolated test databases. Other gates match `.github/workflows/ci.yml`. Ignored `.local`
logs/XML are verification artifacts, not canonical source or production data.
These checks verify regression/doc integrity, **not an unimplemented040B profile or policy**.

**READY FOR POST-MTR-041E DEPENDENCY / MTR-040 DESIGN REVIEW**
