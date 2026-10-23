# MTR-040A — Explicit Member Preference Foundation / design

Status: **IMPLEMENTED WITH AUTHORSHIP CORRECTION; NOT FROZEN**.
Current head: `0012` / 58 tables. [Authorship correction evidence](MTR_040A_AUTHORSHIP_CORRECTION_EVIDENCE.md).
User correction before implementation: raw declarations must not contain caller-authored
EvidenceStrength. That belongs to later MemberBehaviorProfile derivation. Reviewed implementation
baseline: `75d76ad2b400095d7eedf949fdec15bb969b9b5d`. Frozen migrations0001–0010 unchanged.
Reviewed main: `a50f7c275793b126d9f4f9d40097a1f3ca00f2e7`. Existing schema0010 /54 domain tables.
The user approved the [dependency review](POST_MTR_020A_DEPENDENCY_REVIEW.md) with one required
ordering correction: **MTR-040A → MTR-041 → MTR-024 → MTR-020B → MTR-021**. MTR-019D is optional
support later/in parallel, not the next prerequisite. Frozen A/B/C/020A semantics stay unchanged.

## A. Scope, truth and ownership

Canonical parent MTR-040 owns hierarchical feature/direct affinity, evidence strength and explicit
member ownership (ADR-011). MTR-040A provides its **durable explicit source subset**, not a learned
MemberBehaviorProfile or a computed candidate utility. Runtime owner: `preferences`; Catalog owns
reviewed feature vocabulary. HouseholdMember owns declarations; Household is tenancy/context;
the authenticated actor is the author, not automatically the preference subject.

Store what a person explicitly declares about a target, who declared it and how it was corrected.
This is a record of an assertion, not proof of eating, health compatibility, or universal taste.
No learning, inferred preference, execution event ingestion, preference copying between members,
affinity generalization/shrinkage, TasteFit/Adherence scalar, exposure, novelty or portfolio selection.
No Retail/Inventory/Planning identities are needed to own a declaration.

## B. Explicit targets and missing classification

Use a closed typed target union; never a generic target UUID/string/context_ref/JSON payload.

| Target | Canonical identity | Meaning / boundary |
| --- | --- | --- |
| INGREDIENT | Ingredient.id FK | Preference about this canonical ingredient; no raw/cooked or method equivalence inferred. |
| DIRECT_RECIPE | Recipe.id FK | Explicit preference about the stable recipe identity, across authored versions. No automatic feature transfer to other recipes. Version-specific reviews are deferred. |
| PROTEIN | Reviewed AffinityFeatureTerm(PROTEIN) FK | Culinary protein-family preference, not protein nutrient demand, diet rule or allergen classification. |
| METHOD | Reviewed AffinityFeatureTerm(METHOD) FK | Declared method preference. Existing Recipe.cooking_method is an Identifier, not an existing feature-term FK. |
| FLAVOR | Reviewed AffinityFeatureTerm(FLAVOR) FK | Declared flavor-category preference; no text/name-based assignment to recipes. |

Minimum new catalog primitive: immutable `AffinityFeatureTerm`, with id, kind, namespaced code,
definition/version, label, REVIEWED/DRAFT status and source provenance. Unique(kind,code,version)
and unique(id,kind) support an exact typed FK. Definitions come from authored/reviewed facts, never
LLM labels or guessed recipe names. A declaration can target only a REVIEWED term. No constants,
numeric weights or population prior are seeded as architectural truth. Migration creates empty
tables; real vocabulary is explicitly curated data, synthetic terms are test fixtures only.

A term records **what the feature means**, not which ingredients/recipes carry it. Matching
ingredient/recipe/selected-variant paths to protein/method/flavor terms remains MTR-046 source work.
Do not mutate frozen Recipe/Ingredient tables/contracts or use an equal-looking string as a match.
MTR-040A can store all five kinds; a missing term fails TARGET_UNRESOLVED, missing assignment stays
UNRESOLVED_FEATURE_MATCH downstream. Ingredient/direct-recipe declarations can operate before
feature coverage exists. Unknown classification must not block the durable source design itself.

Term corrections create new term versions/IDs. Existing declarations retain their exact target;
no silent retargeting or inheritance to a new definition. Explicit replacement targets a different
stream if its term identity changed. Later consumers must not sum both versions or assume an alias;
cross-version feature reconciliation needs a separately reviewed semantic mapping.
Reviewing a persisted DRAFT term also creates a new reviewed term version; it does not UPDATE
the draft row's status or make old declarations point to a mutable definition.

## C. Affinity, evidence strength and unknowns

Proposed explicit declaration value: `LIKE | DISLIKE | NEUTRAL`, an ordinal assertion without a
numeric preference score. Degree-of-liking/intensity, inferred feature affinity and conflict-weight
composition are deferred. DISLIKE remains soft preference, never a hard ingredient exclusion or
allergy; hard member safety retains its existing Nutrition-owned source and precedence.

Keep evidence dimensions separate:

- Source origin: EXPLICIT_DECLARATION only. Neutral Provenance.kind is existing USER;
  source_system/external_record_id/source_version, optional URI/hash and observed_at are retained.
- EvidenceStrength belongs exclusively to later derived MemberBehaviorProfile, with its own
  derivation policy/version and evidence provenance. Raw declarations carry no evidence_strength,
  strength_basis or implicit default. Explicit source/authorship does not automatically set strength.
- No declaration: UNDECLARED, value absent. Explicit NEUTRAL: a real asserted value/provenance.
  Retraction: RETRACTED, current value absent, prior assertion and retraction evidence retained.
- A future assertion_confidence would be a separate optional concept, never an automatic profile
  EvidenceStrength. It is not implemented in040A.

No row is not a declaration of neutrality, dislike, familiarity or exposure. Retrying/repeating
a statement creates no learned strength. Profile strength derivation is deferred. Unknown
input must not be stored as a fake NEUTRAL/0 assertion to make later portfolio inputs complete.

## D. Actor and household boundary

One command names one household, subject member and target; never fan out to all MealParticipants.
Subject uses composite FK(household_id,member_id)→HouseholdMember. Authenticated actor_user_id is
validated against the household Membership at write time; caller-provided role/authorization flags
are not authority. No anonymous HTTP endpoint or auth system is introduced by this foundation.

Proposed V1 modes:

1. SELF iff authenticated Membership.member_id equals the subject member.
2. AUTHORIZED_REPRESENTATIVE iff that link differs from the subject; a NULL link is allowed.
   Only OWNER/EDITOR may write either mode; VIEWER cannot write. Persist the explicit mode and
   actor, rejecting a false caller-supplied mode instead of normalizing it. This supports diners
   without accounts; it grants no bulk copying or inferred preference.

Authorization reads/locks canonical membership for the command transaction (FOR SHARE, so concurrent
role changes cannot slip through a cached check). Retain actor identity FK, source and authorization
mode/role-at-write audit facts. A declaration FK must not require current membership forever merely
to read history; later membership changes do not rewrite the past. Historical role snapshot is
DB-derived for the insert, not a free client field. Current membership/permissions still control
subsequent edits/reads. Self/proxy distinction remains visible to later fit consumers; do not merge
the two sources or silently choose proxy over self outside explicit current-target revision order.

This is a narrow proposed permission rule, not a new consent/collaboration workflow. Cross-household
actor/subject or unknown member fails. Any later narrower proxy-consent requirement must be resolved
before implementation changes this write rule; schema retains subject vs author either way.

## E. Proposed relational model

Four tables are justified by vocabulary identity, member-level source frontier, target identity
and immutable declaration history. No JSONB, generic cross-domain event store or scalar profile cache.

| Table (proposed) | Owner | Important facts/constraints |
| --- | --- | --- |
| affinity_feature_terms | Catalog | Immutable reviewed vocabulary above; no recipe/ingredient classification mapping in040A. |
| member_preference_frontiers | Preferences | One row per composite household/member; DB-controlled monotonic generation/member_sequence. Detects new target streams as well as replacements, not just changes to already-known rows. |
| member_preference_streams | Preferences | Stable stream_id, composite member ownership, target_kind + ingredient_id/recipe_id/feature_term_id typed FKs, cached head_revision/head_declaration. Identity immutable; head DB-controlled. |
| member_preference_declarations | Preferences | Immutable stream-owned declaration_id, revision_no, predecessor identity/revision, member_sequence, SET/RETRACT, value/action shape, actor/proxy audit, provenance, reason, occurred_at/recorded_at, idempotency identity and command fingerprint. |

Streams have exactly one correctly typed target: ingredient or direct recipe or feature term;
feature composite FK(term_id,target_kind) prevents METHOD→PROTEIN mismatch. Five partial unique
constraints/indexes enforce one stream per household/member/target identity; NULL semantics cannot
permit duplicates. Composite stream FK on declaration binds household/member/stream. Predecessor
FK binds exact same stream/member and revision, never a foreign member/target. No bare UUID shortcut.

Initial SET is revision0 with no predecessor; later facts reference the exact current predecessor
and revision+1. Unique(stream_id,revision_no), unique(household_id,member_id,member_sequence).
SET requires a value; RETRACT requires null value and an active predecessor.
Initial RETRACT and repeated RETRACT without intervening SET reject. A deferred completeness check
prevents committing an empty stream; first stream/fact/frontier/head assemble atomically.

Member/frontier and head cache mutations happen only inside the canonical database write path.
Append trigger/protected functions allocate the next member_sequence, check predecessor/CAS,
advance frontier and stream head in the same transaction. Direct SQL cannot supply a lower sequence,
rewrite heads, change stream identity, bypass target/evidence/actor shape or leave a partial stream.
Actual implementation must prove this with negative SQL tests and approved trigger/privilege patterns;
no claim of PostgreSQL protection is made by a diagram alone. Ordinary application DB role is the
boundary; a superuser disabling triggers is outside that threat model.

## F. Correction/replacement, chronology and concurrency

Historical declarations and feature terms reject UPDATE/DELETE/TRUNCATE. Correction appends a new
SET with reason INPUT_CORRECTION, changing taste appends SET/PREFERENCE_CHANGED, retraction appends
RETRACT. Original assertion and source provenance remain. Replacing a declaration does not reset
exposure, change safety constraints or revise a plan. A different target is a different stream;
retiring the old target requires an explicit retraction, not implicit copying/moving.

`recorded_at` is database time; `occurred_at/observed_at` records the explicit assertion's source
time, not permission to backdate application. Current/as-known snapshots select by committed
member_sequence/source frontier, never UUID ordering or client timestamp. Correction applies from
the new recorded fact; historical snapshots remain reproducible. Effective future schedules and
retroactive re-scoring of old plans are deferred. Future-dated or impossible assertion timestamps
must reject rather than create scheduled preference truth.

Write transaction ordering: canonical membership check/lock → member frontier lock → stream lock
→ idempotent replay/CAS → declaration append + DB head/frontier update → commit. New member-frontier
row initialization must serialize using insert-on-conflict/row locking; stale REPEATABLE READ must
retry or fail serialization, never continue using a stale source. No inventory/plan locks needed.

Commands include expected_revision and exact predecessor declaration; initial expected_revision=-1.
Two devices replacing revision4 cannot both produce revision5. Current member frontier serializes
different-target writes so snapshot generation includes new streams, and deterministic sequence
is independent of equal timestamps. All writer paths must take the same database fence.

Idempotency unique(household_id,actor_user_id,source_system,idempotency_key), with a fingerprint of
full subject/target/action/predecessor/value/provenance command content. Verify current
access first, then return same recorded fact for an exact retry **before stale-head rejection**.
Same key/different content fails; retries do not create new declarations/frontier increments.
Distinct deliberate statements may create new revisions, but never count as learned evidence.

## G. Proposed contracts and handoff

Pydantic frozen, extra=forbid, tuples/closed enums, explicit v1 schema identifiers. No ORM objects
or mutable dict payloads cross the boundary. No floats/weights/probabilities; quantities/money are
not needed for declaration truth.

- Catalog AffinityFeatureTermFact; typed PreferenceTarget union.
- SetMemberPreferenceCommand / RetractMemberPreferenceCommand, with owner/actor, expected head,
  idempotency and explicit evidence; separate command/fact fields prevent caller setting sequence,
  recorded time, authorization audit or source frontier.
- MemberPreferenceDeclarationFact and MemberPreferenceState (DECLARED/RETRACTED; no fabricated
  declaration row for UNDECLARED). Explicit-target lookup returns UNDECLARED separately if absent.
- ExplicitMemberPreferenceSnapshot, containing household/member, captured frontier/as_of, declared
  streams and immutable facts needed for replay, relevant typed target/term facts, schema/hash.
  Coverage=`EXPLICIT_DECLARATIONS_ONLY`, learned/exposure/utility resolution=`NOT_IMPLEMENTED`.

Capture one read-only RR/SERIALIZABLE source snapshot through Preferences public facade. Canonical
sort unordered streams by owned target identity and facts by member_sequence; future ordered data
needs explicit ordinal, never generic list sorting. Content/provenance/target/frontier
changes alter the snapshot hash; retrieval order does not. Validate/replay claims independently
from the cache when a future validator consumes them. No live queries inside validation/shortlist.

Missing preference source/frontier must be distinguishable from a successful capture with zero
declarations. A zero-declaration snapshot is explicit-source-empty, not proof of no likes/exposure
or a usable neutral TasteFit. Later MTR-024 consumes member-owned snapshots without averaging away
identity. Do not widen frozen GroundedDishCandidate/ValidationSubject/hash schemas; use an additive
companion contract when downstream capture is implemented.

Before the first write a member may have no frontier row: return frontier0 only after a successful
canonical member/empty-source read, never on a source lookup failure. Its first declaration creates
frontier1, so a future recheck detects that change. Historical knowledge is identified by the
captured frontier/manifest, not reconstructed from timestamps alone across concurrent commits.

Future TOCTOU recheck must compare each participating member's authoritative preference frontier,
including new streams/retractions; same old rows alone do not detect newly declared preferences.
040A supplies a source frontier, **not production PRECOMMIT authority** or a full all-source guard.

Imports: Preferences may use Household/Catalog/Recipe public/contracts only, no Planner/Execution/
Learning runtime, ORM internals from another domain, Retail/Inventory or utility implementation.
Catalog vocabulary imports no Preferences. Later Learning reads explicit immutable declarations
without overwriting them; MTR-039 inferred/contextual/passive events are not accepted by040A.

## H. Migration and acceptance plan (implemented subset evidence linked below)

Implementation uses **0011_explicit_member_preferences.py**, frozen
DDL independent of mutable ORM metadata. Do not edit0001–0010 or existing facts. Deterministic
up/down/up on empty schema; downgrade locks/checks all four new tables and fails closed if any
preference/term/frontier/history exists. No data copy or learned-score backfill; vocabulary data
must have explicit reviewed provenance. ORM drift/domain export/import tests advance additively.
Initial implementation schema was0011 /58 tables; the authorship correction advances to0012 /58. Original design baseline was0010 /54.
See [execution evidence](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_EVIDENCE.md) for actual checks and limits.

Required implementation evidence:

1. All five typed targets; wrong feature kind/foreign FK/unreviewed or missing term reject.
2. UNDECLARED vs explicit NEUTRAL vs RETRACTED; raw strength/assertion_confidence fields rejected; no unknown→0 default.
3. One member's declaration never updates another; self vs explicit authorized representative
   preserved; viewer/foreign actor/subject reject; concurrent permission revocation cannot race write.
4. SET→replacement→retraction→SET history; old snapshots unchanged; no backdated head selection.
5. Predecessor from wrong target/member/household and reused revision/sequence reject in direct SQL.
6. Concurrent same-stream updates: one success, one conflict; separate-target member writes advance
   the frontier without lost increments, including stale RR failure/retry and empty-stream rollback.
7. Exact retry returns original receipt after later revisions; changed command under same key fails.
8. UPDATE/DELETE/TRUNCATE, head/frontier tampering, partial stream commit and noncanonical source
   kinds reject with ordinary application-role direct SQL tests on PostgreSQL18.
9. Feature version correction preserves old target identity; no automatic recipe/ingredient feature
   assignment; stable Recipe identity does not become a latest-version culinary binding.
10. Snapshot deterministic hash/replay, new-target addition changes frontier, no source vs empty
    source distinguished, capture read-only; later consumers cannot mint authority from a hash.
11. No forbidden Learning/Execution/Planner/utility imports; no inferred/context signal insertion;
    dislike does not create hard safety facts; success/failure/price friction does not create taste.
12. Real PostgreSQL migration/drift/populated downgrade/concurrency/SQL integrity, all old tests,
    synthetic22/22 benchmark, client/web and CI. No weakening frozen A/B/C/020A hashes or tests.

## I. Design decisions and limits

Chosen: ordinal assertions instead of invented scalar affinity; durable append-only replacements;
member-level frontier plus stream CAS; typed FKs; reviewed feature terms without guessed feature
assignments; explicit self/proxy source modes; no raw EvidenceStrength; no defaults
or empirical constants. These are proposed decisions for architecture review, not a freeze verdict.
Implementation review must validate DB protection and permission paths above; no silent alternative
if a contradiction is found. Numeric affinity intensity, taxonomy mapping/generalization, learned
profiles/shrinkage/priors, exposure/cooldown, shared utility aggregation and Stage-2 composition
remain outside040A.

MTR-041 is next on the approved critical path **after this slice is implemented and accepted**.
MTR-024/020B/021 remain blocked; MTR-026 incomplete; PRECOMMIT fail-closed. No learning, Execution,
MTR-019D, portfolio or solver starts in this implementation slice.

Trade-offs for review: ordinal declarations deliberately defer liking intensity; member-frontier
serialization favors deterministic audit over write throughput; the vocabulary table defines
targets without pretending to complete MTR-046 feature coverage. Proposed self/proxy permissions
were accepted by the user; the raw-strength proposal was explicitly removed before code.
Even after implementation,040A would complete only the explicit-source subset of MTR-040, not the
full learned/hierarchical profile or a TasteFit producer.

## J. Implementation handoff

User approved the design with the required raw-EvidenceStrength removal. It was corrected before
implementation. [Evidence](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_EVIDENCE.md) distinguishes actual
unit/PostgreSQL/SQL/concurrency/migration checks from the acceptance plan. No frozen migration,
A/B/C/020A wire/hash or independent validator behavior is changed. Database head0012,58 tables;
full MTR-040 remains incomplete. Submit040A for architecture/freeze review, do not self-freeze.

**READY FOR ARCHITECTURE/FREEZE REVIEW**
