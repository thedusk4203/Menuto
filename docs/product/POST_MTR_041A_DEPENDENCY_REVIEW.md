# Post-MTR-041A dependency review

Status: **PROPOSED — awaiting architecture approval; no implementation authorized here.**

Reviewed `main` / fetched `origin/main`: **`fb6da0192421614f38ff18b94b2222cf0451a974`**.
Schema head: **`0012_preference_authorship_semantics`** (Alembic ID `0012`);
**58 domain tables**, excluding `alembic_version`. Migrations0001–0012 are unchanged.
MTR-040A and MTR-041A remain user-frozen;041A's canonical implementation is
`774405ebe51f126fec10ce61c4dd41b9d229230a`, not the later documentation/test commits.

## 1. Decision and the smallest useful next slice

**MTR-041B: READY for a narrowly scoped recipe-level, proposal-local cooldown assessment.**
Recommended name: **MTR-041B — Recipe-Level Recent Exposure Model / proposal-local policy subset**.
This is a proposed sub-slice of canonical MTR-041, not a new canonical backlog number and not
completion of the full RecentExposureModel. Implementation must await approval of this review.

It can add genuine semantics: evaluate a specified target meal's recipe against *other earlier
meals in the same current proposal*, using an explicitly supplied, versioned cooldown policy.
Exclude the target meal itself; preserve member participation; return exact positive witnesses,
time distances and the policy predicate.041A currently filters an absolute window and counts
recipe facts; it has no target-relative cooldown assessment or self-exclusion contract.

No new source of behavioral truth is needed for that restricted question. Scheduled proposal
facts support a statement about repetition **within a proposal**, even though they cannot support
a statement about what somebody ate. A production/full-history RecentExposureModel is **BLOCKED**.
Calling this subset production novelty, accepted-schedule exposure or complete041 would be wrong.

Do not make source-completion dependencies artificially mandatory for this subset:
MTR-026 is required for accepted publication, MTR-017/038 for operational cross-horizon replay,
MTR-039 for classified behavioral events, and MTR-046 for feature fingerprints. None is needed
to establish whether two explicitly proposed meals of one member repeat the same Recipe ID.
Conversely, this small step does **not** unblock MTR-024/020B/021.

No durable exposure store or migration is warranted. The next slice would add versioned pure
Learning contracts/evaluation and a read-only capture integration, not alter frozen041A.

This is a recommended implementation order, not a claim that the DAG has only one possible
topological order. A target-relative repeat policy is needed even when better sources arrive;
it therefore advances041's own semantics now.046 mappings widen fingerprints but cannot define
cooldown;039 without confirmed event producers cannot supply history;017/038 and production026
each require broader upstream branches. None needs to be pulled into this smallest next slice.

## 2. Evidence and ownership

Canonical references: [ADR-011](../adr/ADR-011-behavioral-learning-loop.md),
[ADR-009](../adr/ADR-009-execution-state-machine.md),
[ADR-010](../adr/ADR-010-independent-validator.md),
[invariants](../ARCHITECTURE_INVARIANTS.md), spec
[§8.4, §13.14, §19.1–19.8, §21, §24.3](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[backlog](BACKLOG.md), [blueprint](IMPLEMENTATION_BLUEPRINT_M0_M1.md),
[status](FOUNDATION_STATUS.md), [041A review](MTR_041A_RECENT_EXPOSURE_DOMAIN_REVIEW.md)/
[evidence](MTR_041A_RECENT_EXPOSURE_EVIDENCE.md),
[040A design](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_REVIEW.md)/
[authorship evidence](MTR_040A_AUTHORSHIP_CORRECTION_EVIDENCE.md), and
[MTR-026 dependency review](MTR_026_DEPENDENCY_REVIEW.md).
Older status paragraphs are historical; later explicit user freezes govern current status.

Concrete code at the reviewed commit (paths below are relative to `apps/backend/`):

| Source / symbol | Finding |
| --- | --- |
| `app/modules/learning/contracts.py`: ExposurePreviewSnapshot, derive_preview_facts, RecipeExposurePreviewDraft.evidence_for | Only selected-plan PROVISIONAL/PROPOSAL_PREVIEW facts; exact RecipeVersion→Recipe identity; explicit member/window; counts, not cooldown/novelty. All other fingerprint kinds reject. |
| `learning/public.py`: preview_recent_exposure, deduplicate_preview_facts | Pure replay; overlap set union; conflicting proposal ID/hash for the same household/member/plan rejects even when recipe changed. No source reconciliation/learning. |
| `planning/exposure_capture.py`: capture_exposure_preview_sources; `planning/public.py`: latest_proposal_source | Clean read-only RR/SERIALIZABLE capture of latest sealed selected proposals, canonical members and authored recipe identities. No caller-authored event ingestion. |
| `execution/public.py`: PlanRevisionService.propose/publish/horizon_handoff | Existing intent orchestration, not MealExecution. Publish requires stored authorization; horizon draft is not projection; v3 horizon handoff explicitly rejects. |
| `migrations/versions/0008_plan_revision_foundation.py`: menuto_plan_no_authority, menuto_plan_revision_insert | Authorization INSERT rejects with `PRECOMMIT authority not installed`; publication checks revision/inventory/boundary context. Frozen0009/0010 do not install an issuer. |
| `validation/public.py`: validate_subject; `validation/contracts.py`: DeferredCapability | Foundation reports remain non-authorizing, required capability gaps remain explicit; POSTFACT is DIAGNOSTIC. Exact RecipeGroundingValidator is a supported sub-capability, not full026. |
| `catalog/contracts.py`: AffinityFeatureTermFact; `preferences/contracts.py`: ExplicitMemberPreferenceSnapshot | Reviewed PROTEIN/METHOD/FLAVOR vocabulary and explicit member assertions exist. Recipe/ingredient-to-term mappings do not. Declaration history has member_sequence, not exposure history. |
| `recipes/contracts.py`, `recipes/generation.py`, `planning/culinary.py` | Authored culinary identities/rules and exact binding exist. A binding hash is not a semantic variant-family identity or feature classification. |
| `inventory/contracts.py`, `inventory/public.py` | Confirmed household material movements/reservations; no member-eating event. Raw/prepared identity and AP/EP/cooked bases remain distinct. |

Graphify was used for orientation (ADR-009 Decision7, ADR-011 Decision3, INV-030).
Its existing graph predates recent implementations; current code/tests, not graph namespace
labels, determine readiness. No new contradiction or isolated runtime defect was found.

Ownership stays separate: Planning owns proposed/accepted intent and its revision lineage;
Execution will own confirmed meal/cooking events; Inventory owns physical household assets;
Preferences owns explicit member assertions; Catalog/Recipe own reviewed descriptors;
Learning owns exposure interpretation/attribution, not source fabrication. Policy definitions
are immutable versioned inputs; Learning owns cooldown enforcement; MTR-024 later composes
separate dimensions. No planner objective, DB IO or mutation belongs in the Learning core.

## 3. Capability dependency matrix

READY means existing truth supports the stated narrow operation, not production completeness.
PARTIALLY READY identifies available identity/facts but missing derivation/coverage contracts.
BLOCKED means the named capability needs a missing upstream producer/model. Order:
**N**=recommended next041B subset; **S**=support branch before enabling its dimension;
**L**=later domain/source chain; none authorizes implementation in this task.

| Capability | Owner | Existing canonical primitives | Missing primitive | Status | Prerequisite MTR | Recommended order |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Recipe aggregation across windows, same current source | Learning | Recipe/meal/member keys, half-open windows, overlap dedup | None for selected previews; no complete history implied | READY | Frozen041A | Existing →N |
| 2. Proposal-preview reconciliation | Planning capture / Learning | Latest proposal selection; mixed revisions reject | Explicit recapture, not automatic old/new union; no materialized-source reconciliation | READY for current-proposal replacement | Frozen016/041A;017/038 for heterogeneous replay | Existing; broader L |
| 3. Accepted-schedule exposure | Planning source, Learning interpretation | ActivePlan/revision snapshots, participants and sealed graph | Production accepted-publication authority, complete source-frontier recheck, accepted-source capture | BLOCKED | Required026 source/validator branches →026 production authority with016/027 publish seam; then041 accepted-source subset | L, not next |
| 4. Confirmed exposure | Execution source / Learning | ADR event semantics; Recipe/member IDs | Confirmed contextual event with explicit attributed subject, correction lineage and ingestion completeness | BLOCKED |023/035 confirmed execution source;039 routing;017 confirmed capture →041 extension | L |
| 5. Confirmed consumption | Execution | Physical CONSUME; meal participants in intent | Confirmed member/meal/recipe consumption fact; inventory movement is insufficient | BLOCKED |035 MealExecution/member evidence,023 where cooked assets involved;039 attribution →041 | L; no Execution now |
| 6. USER_CONFIRMED_COOKED | Cooking/Execution →Learning | ADR-011 confirms exposure, not taste/consumption | Actual confirmed cooking event, subject attribution, correction identity | BLOCKED |023 cooking execution +035 confirmation →039;017 capture | L |
| 7. AUTOPILOT_ASSUMED | Operational projection →Learning | ADR provisional-only semantics | Reversible assumptions, dependency/reversal graph and resolved projection | BLOCKED |017 +036;039 routing →041 | L; never durable history |
| 8. Cross-horizon exposure bridge | Execution projection /038 | Horizon timestamps, intent IDs; selected preview overlap union | Authoritative commitment coverage, causal reconciliation, carryover contribution identity, confirmed/provisional linkage | BLOCKED as canonical bridge |017 projection +023 planned flow;036 if assumed inputs →038;026 for accepted producers | L |
| 9. Correction/reversal | Source owner / Learning | Frozen proposal replacement/retirement | Confirmed event supersession and assumption compensation lineage | PARTIALLY READY |041A handles preview replacement;035/023 confirmed corrections;017/036 assumed reversals;039 routing | Existing preview; L broader |
| 10. Member-owned exposure history | Learning projection over source facts | Explicit participants and member-scoped preview facts | Durable confirmed event stream, completeness frontier, correction replay | PARTIALLY READY |035/023 +039;017 coherent source capture →041 history | N preserves member scope; L durable |
| 11. Stable frontier / completeness | Source capture owners | Selected workspace/proposal frontier hash, RR capture | All-member/all-source enumeration and mutation frontiers; authority recheck | PARTIALLY READY |041B retains bounded manifest;017/038 source capture;026 commit guard | N bounded, L global |
| 12. Repeat cooldown | Learning enforcement; versioned policy | Exact recipe identity, explicit times and positive preview witnesses | Target-relative policy/query/output contract; no approved default duration | PARTIALLY READY |041B defines explicit externally supplied policy; no upstream producer needed for proposal-local predicate | **N** |
| 13. Decay | Learning enforcement; versioned policy | Scheduled times and provenance | Defined versioned curve/weights, evidence applicability and coverage semantics | PARTIALLY READY |Later041 policy sub-slice; reviewed/calibrated defaults are separate from implementing a deterministic evaluator | S; unavailable in N |
| 14. Novelty | Learning evidence;024 utility composition | Recipe identity; scoped absence marker | Coverage-qualified novelty policy and applicable history; no proof of never-exposed | BLOCKED for production novelty |041 source/history extensions;046 for feature novelty;024 composition | After sources; not N |
| 15. RECIPE_ID fingerprint | Recipe identity / Learning | Exact RecipeVersion.recipe_id | None for recipe-level repeat | READY | Frozen018/019A/041A | Existing →N |
| 16. Recipe-version handling | Recipe / Learning | Exact immutable version IDs, source provenance | No version-as-repeat equivalence policy;041A only groups by Recipe | READY for traceability/grouping; separate fingerprint unsupported |041 future explicit semantics if version-specific repeat needed | Existing →N |
| 17. Variant/family fingerprint | Authored Recipe/Catalog | Binding/candidate signatures | Stable authored family IDs/membership and version reconciliation; hash equality is not family | BLOCKED |046 reviewed family mapping coordinated with018/019 authored paths;041 consumer | S before family |
| 18. METHOD fingerprint | Catalog/Recipe | cooking_method Identifier; reviewed METHOD terms | Exact versioned recipe/path→term FK/assignment and coverage | BLOCKED |046 reviewed feature assignments;041 consumer | S before method |
| 19. PROTEIN fingerprint | Catalog/Recipe | Ingredient IDs; PROTEIN terms; selected culinary binding | Authored resolved-path classification/main-protein semantics and coverage | BLOCKED |046 reviewed mappings coordinated with019 grounded binding;041 consumer | S before protein |
| 20. FLAVOR fingerprint | Catalog/Recipe | FLAVOR term vocabulary | Authored recipe/variant path→term mapping and coverage | BLOCKED |046 reviewed assignments;041 consumer | S before flavor |
| 21. Cold start | Learning /Preferences /Policy | Explicit preference state; empty preview ≠never-exposed | Versioned priors and coverage-qualified novelty/affinity interpretation | PARTIALLY READY |041B preserves unknown;040 derived profile +028 priors;041 broader history/policy | N unknown only; broader S/L |
| 22. Explicit preferences interaction | Preferences owns assertions | Frozen040A declaration/retraction/member frontier | Profile affinity/shrinkage and matched feature inputs | PARTIALLY READY |Remaining040;046 when features used;024 separate composition | Preserve source now; S |
| 23. SignalAttributionRouter interaction | Learning /039 | ADR evidence categories and forced-tradeoff rules | Typed source event routing, provenance, quarantine and correction outcomes | PARTIALLY READY |039, after the source kinds enabled actually exist; no router needed for fixed proposal-preview source | L; not N prerequisite |
| 24. State projection interaction | Execution /017 | Physical snapshot; plan intent snapshots | Confirmed/Operational/Planning reconciled views; reversible assumption lineage | BLOCKED |017;036 for assumptions,023/035 for actual events | L |
| 25. HorizonBridgeResolver interaction | Execution /038 | Draft commitments; v3 handoff explicitly deferred | Resolved chronological bridge inputs/outputs and unique contribution reconciliation | BLOCKED |017 +023;036 if assumptions; then038 | L |
| 26. Reviewed classification interaction | Catalog/Recipe /046 | Reviewed term definitions and exact source IDs | Actual recipe/ingredient/variant assignments, applicability and mapping frontier | BLOCKED |046 reviewed mapping source subset (requires separate design) | S; not needed for N RECIPE_ID |
| 27. MTR-024 separable utility inputs | Policy/Planning composition; source domains |040A assertions;041A previews; future bounded cooldown witness | Covered exposure/novelty, derived affinity, contextual dimensions and versioned composition policy | BLOCKED |Remaining040/041;039/046 and006/007/008 when applicable;024 only after reviewed input coverage | Later; not unlocked by N |

## 4. Source-truth matrix

Durability below means behavioral-history truth, not whether an immutable source row exists.
Persisted proposal history is durable advice history, never durable eating history.

| Exposure source | Current canonical producer | Truth level | Durable? | Member-attributed? | Can MTR-041 consume now? | Blocker |
| --- | --- | --- | --- | --- | --- | --- |
| Latest selected sealed proposal | Planning capture, frozen041A | PROVISIONAL / PROPOSAL_PREVIEW | No behavioral durability; proposal row retained | Explicit proposed participants only | YES,041A preview; N local predicate | No full-history/global coverage |
| Old/replaced/retired proposal | Immutable Planning history | Superseded advice | Audit only | Historical proposed participants | Not additive current exposure | Fresh capture latest; never sum revision history |
| Accepted current revision |016 snapshots/publication seam | Would be accepted scheduled intent, still provisional exposure | Commitment history, not confirmed consumption | Explicit participants exist | NO production producer now |026 authority/TOCTOU; future accepted capture |
| Explicit member-confirmed eating | None | Would be confirmed consumption/exposure | Only confirmed source and corrections | Needs explicit subject | NO |035/MealExecution,039,017 |
| USER_CONFIRMED_COOKED | ADR semantics only | Confirmed cooked exposure, not eating or liking | Eligible confirmed exposure after real source/routing | Must name attributed member(s); actor alone insufficient | NO |023/035 source +039 |
| Physical inventory CONSUME | Frozen Inventory ledger | Confirmed household material outflow | Physical history only | No meal eater/recipe attribution | NO behavioral inference | Execution semantic link/subject evidence missing |
| Prepared material asset | Frozen raw/prepared physical identity primitives | Material presence, not eating | Physical history only | Household-owned | NO behavioral inference | No cooking/member exposure event producer |
| AUTOPILOT_ASSUMED | None | Would be reversible operational assumption | Never durable learning | Requires explicit resolved participant context | NO |017/036/039; no new assumptions here |
| Provisional cross-horizon handoff | Draft commitment seam only | Would be projected commitment exposure | Reversible projection | Requires captured participant identities | NO canonical bridge |017/038, accepted-source frontier; no fake bridge |
| Explicit LIKE/DISLIKE/NEUTRAL | Frozen Preferences040A | User assertion about affinity | Durable declaration lineage | Explicit subject; SELF/representative semantics | Separate input, NEVER exposure | Remaining040 derivation; no fan-out |

### Accepted publication and TOCTOU

The missing accepted source is not merely a missing SELECT adapter. Production cannot mint
authorization at all. Superuser/privileged test fixtures that seed accepted revisions do not
remove `menuto_plan_no_authority` from the production path. Existing016 revision CAS,
inventory sequence and materialization boundary checks are necessary but insufficient.

Future order remains: capture immutable ValidationSubject → independently validate required
coverage → recheck *all authoritative* safety/policy/recipe/retail/inventory/plan frontiers
inside the authorization/commit transaction → publish only if current. Inventory/safety/policy
mutation after capture invalidates authorization. Current policy/safety changes can escape the
limited source-frontier counters: see `test_postgres_validation_dependency_review.py` and
`test_validation_canonical_review.py`. A snapshot hash is not a TOCTOU guard. No production
issuer, trigger change or bypass is proposed here; PRECOMMIT stays fail-closed.

### Cross-horizon and confirmed source limitations

041A can filter a Sunday fact when capturing a window spanning Monday, and deduplicate the
same event across overlapping windows. That is **not**038: different plans may describe the
same intended real meal with different node IDs; scheduled and confirmed/assumed sources need
causal correspondence, not matching recipe/time guesses.017 must provide reconciled source
views and038 must own commitment/carryover lineage and no-double-count replay. A pure exposure
filter must never simulate projected inventory or count both raw input and prepared output.

No current source creates durable confirmed member exposure. Inventory consumption does not
identify an eater, cooking is not eating, and no user confirmation/MealExecution/ExecutionLedger
producer exists.039 cannot invent that source by routing an inventory movement. ADR-011's
USER_CONFIRMED_COOKED is compatible: a future explicit cooking event can prove *cooked exposure*
for attributed subjects without proving consumption or taste. No contradiction requires an ADR
or frozen-domain change.

## 5. Fingerprint matrix and canonical order

| Fingerprint | Canonical identity exists? | Semantic mapping exists? | Supported now? | Prerequisite |
| --- | --- | --- | --- | --- |
| RECIPE_ID | YES, stable Recipe PK captured via exact RecipeVersion FK | YES for version→Recipe identity | YES, only frozen041A repeat kind; retain for N | None |
| RECIPE_VERSION | YES, immutable version ID/provenance | Exact version identity, not distinct behavioral repeat meaning | Traceability YES; separate repeat fingerprint NO | Later041 explicit repeat policy; do not treat corrections as new dishes |
| VARIANT/FAMILY | Exact selected binding/candidate signature YES; family identity NO | NO cross-version/path family membership | NO |046 authored family identities/mappings with018/019 |
| METHOD | Recipe Identifier and reviewed METHOD vocabulary separately YES | NO binding between them | NO |046 exact reviewed versioned assignments |
| PROTEIN | Ingredient IDs and PROTEIN vocabulary separately YES | NO resolved primary-protein assignment | NO |046 authored selected-path/main-protein coverage |
| FLAVOR | Reviewed term identity YES | NO recipe/variant assignment | NO |046 authored mapping/coverage |

No inference from recipe names, equal strings, base-ingredient inheritance or binding hashes.
COUNT nutrition still requires authored item_ref-specific truth; exposure count is a count
of proposed meals, not food COUNT conversion. AP→EP Retail yield and Recipe cooking yield
stay separate; reservations never become physical movements.

041A canonical serialization is safe for its *unordered fact sets*: members, captured recipe
identities, selected sources, graph content sets and allocation supports sort by explicit IDs.
Preview facts sort by stable event key for reproducibility, **not chronological replay**.
An actual future event stream must retain effective/recorded time and explicit ledger_sequence
or source_sequence, causal parent and reversal references; equal timestamps cannot use UUID
or generic list sorting as temporal precedence. Preference member_sequence and Inventory
ledger_sequence are their own source orderings, not a shared exposure sequence.
Future ordered instructions, decay breakpoints or assumption replay must likewise carry/check
explicit ordinal/boundary semantics rather than let generic canonical sorting change meaning.

## 6. Proposed041B contract boundary, not implementation

Allowed inputs:

- One immutable041A source snapshot containing **exactly one current selected proposal**, one
  household/member and sufficient explicit capture window; derive preview facts again.
- Target plan/proposal/meal identity and Recipe ID resolved from that captured graph's positive
  planned allocation; target member must participate. No caller-authored exposure event, arbitrary
  unsupported recipe equivalence or free-standing candidate benefits.
- A new immutable versioned cooldown policy: explicit policy identity/version/provenance,
  positive duration expressed with an exact time unit, supported source/fingerprint and boundary
  semantics. Definitions may live in Policy contracts; Learning independently applies them.
  No default duration, coefficient, empirical claim or synthetic fixture as production policy.

Proposed operation: for target time `T`, select other meals' same-Recipe/member preview facts
with `T - cooldown_duration <= scheduled_at < T`. Exclude the entire target meal identity,
even if several allocations/versions support it. Equal-time meals are not earlier events;
do not manufacture an ordering. Require capture-window containment of this lookback interval
and source coherence. The window concerns the selected proposal, never all household history.

Allowed outputs (new DRAFT version, activation_ready=False):

- Source/policy/query hashes, household/member/target identities and explicit coverage.
- Exact positive cooldown witnesses, their stable event keys, time distances and source links.
- `MATCH_IN_SELECTED_PROPOSAL`, `NO_MATCH_IN_SELECTED_PROPOSAL`, or explicit
  `UNAVAILABLE_POLICY` / `INSUFFICIENT_WINDOW` / `UNSUPPORTED_SOURCE` outcomes.
  Exact wire names require implementation review; this document creates no contract.
- Accepted/confirmed/cooked/consumption history **UNAVAILABLE**; decay **UNAVAILABLE**;
  behavioral novelty **UNAVAILABLE**. No history-known boolean or implicit zero penalty.

Missing policy cannot return a neutral score; positive duration/policy supplied externally is
an explicit configuration, not invented domain evidence. Absence of a match means only absence
in that proposal/lookback. It says nothing about recent eating, never-tried status or global
cooldown satisfaction. This limited diagnostic remains useful for detecting a recipe proposed
twice too close together and is strictly weaker than production RepeatPenalty.

Why more than041A: target-relative eligibility, mandatory self-exclusion, policy boundary and
lookback sufficiency, plus independently reproducible predicate/witnesses. Merely returning
041A occurrence_count under a new class name is explicitly **not** this slice.

New evaluation must not mutate/extend041A fingerprint kinds or frozen hashes. Mixed revision
captures reject and require recapture. One-proposal restriction avoids pretending to solve038
cross-plan commitment equivalence. No DB calls from core, new persistence, full router, preference
derivation, utility weights, ranking, candidate generation, reservation or execution workflow.

### Chronology, penalty, novelty and utility are different

Raw chronology is source events plus time/order/lineage. Repeat evidence groups those facts
under an explicit matching identity and coverage. Cooldown is a versioned temporal predicate;
decay is a separately specified time-to-influence policy. A repeat *penalty* requires a policy
that maps eligible evidence to a separate dimension, not merely a count. Novelty requires its
own coverage-aware definition; empty history cannot establish it. Final Stage-2 utility belongs
to024 and combines independently sourced dimensions after safety, never persists RecipeScore.

041 owns repeat/cooldown/decay interpretation; Policy owns immutable definitions/default versions;
024 consumes supported dimensions and owns final composition. Reviewed numeric defaults remain
open per spec§24.3. N needs no default; decay/novelty/weighted penalties are deliberately deferred.

## 7. Adversarial checks and approval criteria for the next slice

Existing code/tests already establish: elapsed time remains provisional; forged confirmed/cooked/
autopilot labels reject; per-member participation; overlapping-window dedup; mixed revision and
recipe-swap conflicts; immutable old proposal preservation; coherent RO RR capture under concurrent
proposal replacement; unsupported fingerprints reject; no DB/Execution/preference runtime in core.

Required future041B tests, **not claimed implemented by this review**:

1. A proposal contains recipe R at T1 and T2: explicit policy permits a positive witness only
   when T1 is in the target-relative interval; no new empirical constant is introduced.
2. Target meal alone / two batches / two versions of R in target: never self-repeat; no count twice.
3. Boundary exactly T-duration included; exactly T excluded. Equal timestamps do not invent order.
4. Empty selected evidence returns scoped no-match plus unavailable history, never novelty or0.
5. Missing policy, insufficient captured window, cross-plan input or unsupported feature rejects/
   reports unavailable; no silent fallback. Policy changes alter result identity deterministically.
6. Current proposal replaced: recapture changes the source/predicate; old/new sources cannot sum.
7. Sunday preview in an explicitly captured same-plan lookback can match Monday; no038 claim.
8. User cooks/consumes inventory or likes a recipe: no confirmed/taste update from this evaluator.
9. Foreign member/household/target or target without positive recipe allocation is invalid.
10. Same semantics/shuffled unordered facts yield identical output; no IO/writes/authorization.

INV-003/004 preserve household/member identity;005/006 forbid new culinary possibilities;
007/009 preserve evidence vs certainty;011–013 distinguish intent, assumptions and physical facts;
015–021 preserve independent primitive validation and gating;022–030 preserve non-durable passive
evidence, separable dimensions, member ownership, explicit policy and future bridge lineage.
No invariant wording or ADR is changed. No existing test needs weakening or deletion.

## 8. Dependency order and direct answers

```text
040A FROZEN +041A FROZEN
  → proposed041B single-proposal RECIPE_ID cooldown-policy subset (next; approval required)
  → remaining041 sources / coverage / decay / novelty +remaining040 profile prerequisites
  →024 (still blocked; separately approved input coverage required)
  →020B (still blocked)
  →021 (still blocked; independent feasibility prerequisites also apply)

Support branches, enabled only when their capability is needed:
  046 reviewed recipe/path features → multi-fingerprint041
  026 upstream primitives/independent checks → production issuer/TOCTOU → accepted schedule capture
  017 reconciled views +023 planned flow →038 cross-horizon bridge
  later confirmed023/035 sources →039 routing → confirmed041 history
  017/036 reversible assumptions →039 → provisional041 extension
```

Full MTR-041 completable now? **NO**. MTR-041B production/full-source interpretation is BLOCKED;
the precisely restricted next subset is READY. Full040 also remains incomplete. MTR-024,
MTR-020B and MTR-021: **BLOCKED**, not authorized to start. Execution required now? **NO**;
do not start it to manufacture exposure truth. New migration for the proposed subset? **NO**;
the durable canonical sources already exist. A later genuinely durable source/mapping design
must justify its own forward migration after0012, not add an exposure table by convenience.

## 9. Review verification and stop boundary

Documentation-only review. No production code, contract, export or migration changes; no new
tests are necessary to establish these findings. Baseline verified from fetched main, Alembic
revision graph and explicitly registered SQLAlchemy metadata (not a claim to have queried a
live production database). Local checks: **200 existing tests passed** (041A, explicit
preferences, validation foundation/canonical review, architecture and baseline); architecture
baseline30 invariants/11 ADRs/50 tasks,16-context import boundaries, domain/OpenAPI drift and
whitespace checks all pass. No local PostgreSQL rerun is claimed for this documentation change;
PR/merge CI runs the full PostgreSQL-backed gates and is reported at delivery. Existing041A
evidence remains1403 Python /630 PostgreSQL-real; these historical counts are not a new local run.
Frozen040A/041A implementation/contracts/migrations remain untouched. No other milestone starts.

**READY FOR ARCHITECTURE REVIEW**
