# Post-MTR-046A — Feature-aware MTR-041 Proposal Exposure Source Integration

Status: **DESIGN PROPOSAL ONLY — implementation NOT AUTHORIZED; NOT FROZEN**.

Reviewed canonical `main`: **`428b992892ac2aeebdbedb8bb3fd5e436e76415c`**, PR #85.
The user froze MTR-046A at this commit. Actual Alembic head is **0013**, SQLAlchemy
metadata contains **71 domain tables**. This document records that user decision;
it does not reopen or independently freeze a source slice.

Recommendation, subject to architecture approval: **MTR-041E — Proposal-local Reviewed
Feature Exposure Sources**, an additive source-integration subset of MTR-041.
The suffix is justified in §15, not assigned or implementation-authorized by this PR.
No runtime, contract, test, export or migration changes are part of this design package.

## 1. Frozen boundary and decision

MTR-040A and MTR-041A/B/C/D remain FROZEN. MTR-046A now provides reviewed
METHOD, FLAVOR and MAIN_PROTEIN classification sources, but does not itself produce
member/meal exposure. Frozen041A produces Recipe-ID proposal previews, not feature exposure.
The smallest useful next source seam is their coordinated, read-only join.

This proposal yields only **provisional, proposal-local feature exposure source facts**,
coverage diagnostics, complete provenance and deterministic captured replay. Every output
remains `activation_ready=False`, `PROVISIONAL / PROPOSAL_PREVIEW`.
It is not accepted schedule, cooking, consumption, preference or durable behavioral history.

Full MTR-040, MTR-041 and MTR-046 remain incomplete. MTR-024, MTR-020B and MTR-021
remain BLOCKED. Execution is NOT STARTED and PRECOMMIT remains fail-closed.
No concrete contradiction requiring a frozen runtime correction was found.

Canonical references: [ADR-011](../adr/ADR-011-behavioral-learning-loop.md),
[ADR-005](../adr/ADR-005-grounded-recipe-variants.md),
[ADR-009](../adr/ADR-009-execution-state-machine.md),
[ADR-010](../adr/ADR-010-independent-validator.md),
[invariants](../ARCHITECTURE_INVARIANTS.md), [spec](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[backlog](BACKLOG.md), [blueprint](IMPLEMENTATION_BLUEPRINT_M0_M1.md),
[046A design](MTR_046A_CULINARY_FEATURE_ASSIGNMENT_DESIGN.md),
[046A corrections](MTR_046A_DESIGN_CORRECTIONS.md) and
[046A implementation evidence](MTR_046A_IMPLEMENTATION_EVIDENCE.md).

## 2. Current source inventory — inspected code, not inferred capability

| Existing source | Actual implemented capability | Constraint on this design |
| --- | --- | --- |
| `learning/contracts.py` | Frozen041A immutable member/window/proposal snapshot; Recipe-ID grouping retains every allocation/batch/RecipeVersion support. B/C/D policies and results are explicitly RECIPE_ID. | Flatten individual supports before feature joins. Never classify one representative version after Recipe-ID grouping. Never add fields to frozen facts or generalize their fingerprint union. |
| `learning/public.py` | Pure preview and B/C/D interpretation; old dedup rejects conflicting proposal revisions for an owner. | New feature facts need their own derivation/identity. Do not pass them through the old Recipe-ID dedup helper. |
| `planning/exposure_capture.py` | Canonical member/proposal/recipe reads in a clean read-only RR/SERIALIZABLE caller-owned transaction. One member per frozen request. | Coordinate multiple selected member captures within the same transaction; preserve child snapshots unchanged. |
| `planning/feature_capture.py` | Canonical current proposal; dimension-only capture; METHOD cooking context; exact path required for FLAVOR/MAIN_PROTEIN; conditional Catalog capture. | No term query or caller classification in capture. Path-dependent capture independently grounds the whole bound proposal, not only an exposure window. |
| `planning/feature_preview.py` | Pure discovery and optional term resolution from captured primitives. | Planning coordinator may use this facade; Learning core must not import this runtime module. |
| `planning/contracts.py` | Frozen046A full captured subject and recomputed discovery contracts; proposal/household/path ownership checks; draft status. | Retain the full nested source and revalidate it, rather than trusting cached positive term IDs. |
| `recipes/contracts.py`, `recipes/feature_resolution.py` | Reviewed applicability, exact authored context/path, finite covered universe, positive assignments and explicit discovery states. | Reuse source-owned classification semantics; do not implement a second matcher inside Learning. |
| Catalog feature association contracts | Explicit reviewed Ingredient→PROTEIN streams and generation; MAIN_PROTEIN review pins supporting heads. | Association alone does not make an ingredient the dish's main protein. No Catalog dependency for METHOD/FLAVOR. |
| Plan graph / planned allocations | Explicit member participation, positive planned servings, causal batch-to-meal allocation, stable node identities. | No participation or positive eligible allocation means no feature event. Scheduled time is intent, not consumption. |

Relevant code is under `apps/backend/app/modules/`. Direct inspection also covered the
041A/B/C/D review/evidence, current 046A design/corrections/evidence, canonical status and
schema/import boundaries. Existing graph-index output was orientation only; current code
and directly read canonical documents determine this review.

Important limits found in code:

- Frozen041A captures identities for **all** proposal batches and groups eligible supports
  by stable Recipe ID. It does not discard multiple versions/batches in that group.
- Frozen046A distinguishes an invariant RecipeVersion cooking context from an exact selected
  path. A path-sensitive capture invokes the existing RecipeGroundingValidator across the
  **whole bound proposal**. Invalid unrelated bindings cannot be trimmed away to bypass it.
- Each existing capture obtains its own `captured_at`; a shared RR transaction does not imply
  identical wall-clock timestamps. Frozen subject hashes include their capture times.
- Assignment identity is relational: e.g. **(review_id, term_id)**, with its enclosing
  applicability/ownership context. There is no generic assignment UUID to invent.

## 3. Dependency matrix and ordering

READY below means canonical primitives exist, not that this new integration is implemented.

| Capability | Owner | Existing primitives | Missing primitives / work | Status | Prerequisite MTR | Recommended order |
| --- | --- | --- | --- | --- | --- | --- |
| Proposal/member/meal eligibility | Planning capture + Learning contracts | Frozen041A; current proposal; participants; positive allocations/window | No new source truth | READY | 041A, 019A | Reuse first |
| METHOD reviewed source | Recipes | Frozen046A cooking-context discovery | No new source truth | READY | 046A | Capture per eligible batch |
| FLAVOR reviewed source | Recipes | Frozen046A exact path/review/universe | Valid exact bound proposal required; reject unavailable path | READY for supported proposals | 019A + 046A | Capture after eligibility |
| MAIN_PROTEIN reviewed source | Recipes + Catalog | Contextual main-protein review + pinned association heads | Valid exact path and actual support generation required | READY for supported proposals | 019A + 046A | Conditional Catalog capture |
| Coherent feature exposure join/dedup/coverage | Planning coordinator + Learning pure core | Both frozen capture seams and immutable source contracts | Additive coordinator, contracts, pure recomputation and tests | PARTIALLY READY | Proposed 041E, after design approval | **Next narrow implementation** |
| Feature cooldown/decay/RepeatPenalty | Learning policy interpretation | Recipe-ID B/C/D only | Separate feature-aware policy semantics; no generic conversion of B/C/D | PARTIALLY READY | Later separately reviewed 041 subset after feature source | Deferred |
| Explicit-only member profile derivation | Learning, member-owned | Frozen040A declarations; reviewed feature vocabulary | Priors, derivation/EvidenceStrength policy and profile contract | PARTIALLY READY for separate design | Remaining040 | Independent branch; not a prerequisite for this join |
| Accepted-schedule exposure | Planning authority + Learning source | Draft proposals/revisions | Production validation authority and accepted-plan capture | BLOCKED | 026 authority path, then041 source | Later |
| Confirmed/member-attributed history | Execution + attribution + Learning | Physical ledger, draft planned batch intent | Actual execution/consumption and member attribution truth | BLOCKED | 023/035 execution path after authority review →039→041 | Later; do not start here |
| Assumed/operational exposure | Projection + attribution | Physical facts distinct from assumptions | Operational projections, assumption graph and attribution | BLOCKED | 017 +036 +039, then041 source policy | Later |
| Cross-horizon/carryover source | Projection/bridge | Physical ledger; stable plan/revision boundaries | Causal bridge replay and source dedup | BLOCKED | 017 + applicable023/036 →038→041 | Later |
| Variant-family exposure | Recipe identity/classification | Stable Recipe ID and exact versions | Authored family identity/mapping | BLOCKED | Remaining046 with018/019 identity design | Separate review |
| Global history / novelty / full041 | Learning | Scoped provisional A–D; reviewed feature source | Accepted/confirmed/attributed/bridge sources and global policy | BLOCKED | Source branches above + remaining041 | Not completed by this slice |
| Separable utility / role portfolio / feasibility | Policy/planning | Partial source dimensions only | Complete canonical preference/exposure/utility inputs | BLOCKED | Remaining040/041 →024→020B→021 | No start authorization |

Dependency chain for this proposal:

```text
041A canonical proposal/member/meal/allocation evidence
             + 019A exact authored culinary binding
             + 046A reviewed context/path classification
                         ↓
single coherent read-only capture
                         ↓
pure member×meal×dimension×term join + coverage diagnostics
                         ↓
later separately approved feature policy consumers
```

MTR-034 shopping fulfillment is not a substitute for member consumption history.
No dependency in this graph authorizes Execution or opens MTR-024.

## 4. Proposed additive contracts and ownership

All names below are **design proposals**, not exported or implemented contracts. They would
be frozen Pydantic models with `extra="forbid"`, explicit new schema versions, primitive-only
payloads and draft status. No ORM object crosses this boundary.

| Proposed concept | Owner | Proposed content and constraints |
| --- | --- | --- |
| `FeatureExposurePreviewRequest` v1 | Learning contract; Planning capture input | Household, **one** plan, expected current proposal ID/hash, nonempty unique selected member IDs, nonempty unique dimensions from METHOD/MAIN_PROTEIN/FLAVOR; existing `ExposurePreviewPolicy` under explicit `recipe_eligibility_policy`. No term queries, caller facts, utility or source arrays. Authenticated actor remains application context. |
| `FeatureExposureSourceSnapshotDraft` v1 | Learning immutable input; assembled by Planning | Request, `capture_completed_at`, one frozen041A snapshot per selected member, full frozen046A `CulinaryFeatureDiscoveryDraft` sources keyed by (batch_node_id, dimension), dimension frontier manifest; `activation_ready=False`. |
| Dimension frontier manifest | Learning immutable contract | Closed dimension-specific shapes: METHOD/FLAVOR contain Recipes generation and **forbid** Catalog fields; MAIN_PROTEIN requires actual Recipes and Catalog generations. No unobserved zero/default frontier. |
| `FeatureExposureSupportWitness` v1 | Learning derived evidence link | Exact participant row, frozen041A recipe-event key, allocation/batch/recipe/version identities, classification-source key, subject/discovery hashes, applicability/review and positive-assignment composite references. Every link resolves inside the attached snapshot. |
| `FeatureExposurePreviewFact` v1-draft | Learning pure derivation | Event fields in §7, resolved scheduled_at, exact proposal ID/hash, nonempty unique support witnesses; PROVISIONAL/PROPOSAL_PREVIEW and activation_ready=False. |
| `FeatureExposureCoverageDiagnostic` v1 | Learning pure derivation | **Member×meal×batch×dimension** owner, eligible allocation IDs and source key; unchanged frozen `FeatureDimensionDiscovery`: state/reason, coverage, covered/positive term IDs, applicability/review. No global or meal-level completeness boolean. |
| `FeatureExposurePreviewDraft` v1 | Learning pure result | Full input, recomputed events/diagnostics, deterministic identity; accepted/confirmed/consumption/durable/cross-horizon history and feature policy consumers explicitly UNAVAILABLE; activation_ready=False. |

The existing eligibility policy intentionally remains literal **RECIPE_ID**. It controls the
frozen041A source eligibility/window only. New feature dimensions are separate request fields;
this does not turn the old policy into a generic fingerprint policy or reuse it for feature
cooldown. No new duration/weight/interpretation policy is needed for a source-only join.

Planning owns transaction orchestration and canonical source reads. Learning owns exposure
meaning, identity and pure derivation. Recipes owns applicability/classification. Catalog owns
ingredient associations. No new table duplicates any of those truths.

Learning may import immutable cross-domain contracts only. It must not import Planning capture,
stores, `feature_preview.py`, solver, Execution, Preferences runtime or database machinery.
The Planning coordinator can produce a frozen discovery contract; Learning fully reparses it.
That existing contract independently recomputes discovery from its full nested primitive subject,
so no new classification implementation is required inside Learning.

Keeping the full frozen child snapshots repeats some proposal bytes. This is deliberate for a
small audit/replay seam: it preserves existing canonical encodings and source proofs. Replacing
them with bare IDs or a new generic normalized cross-domain store would weaken this design.

## 5. Coordinated capture topology

One caller-owned, **clean read-only REPEATABLE READ or SERIALIZABLE transaction** captures the
whole request. No child opens another connection, commits or ends that transaction. Serialization
failure retries the entire capture, never only one dimension/member fragment.

1. Read canonical household/actor/member access and current proposal; compare expected proposal
   ID/hash. Missing, foreign, stale or conflicting identities reject the request.
2. Use frozen041A capture for each selected member with exactly that one plan and the explicit
   eligibility policy, in the same session. Retain the resulting snapshots unchanged.
3. Recompute frozen041A facts and flatten their individual eligible allocation supports. Build
   the union of batch IDs contributing to these member/meal/window facts.
4. For every eligible batch and each requested dimension, use frozen046A dimension-only capture
   with a **singleton dimension** and the exact selected proposal. Produce and retain its full
   canonical discovery contract. Capture once per batch/dimension, not once per participant.
5. Capture the Recipes generation and, **iff MAIN_PROTEIN is requested**, the actual Catalog
   association generation for the outer manifest. This also applies when no eligible batch exists;
   zero eligible facts must not produce invented/default source frontiers.
6. Record `capture_completed_at`. Return the immutable draft; do not persist derived exposure.

The exact source manifest is the eligible batch set × requested dimensions. Missing or extra
sources are rejected, not silently ignored. All nested proposal/workspace canonical content,
identity/hash, recipe identity/provenance and member manifests must agree. The per-member041A
identity is intentionally different; source plan/proposal and common policy are not.
Repeated term/review/head/version facts must agree, and generation values must describe the same
RR source cut. Reusing a counter alongside conflicting source facts does not establish coherence.

Nested `captured_at` values **may differ** because current adapters each read their clock.
They must be no later than completion; existing child as-of/provenance checks still apply at
their own capture times. Do not overwrite frozen child times or compare a policy only to the
later outer completion time to bypass an earlier child's cutoff.
The authoritative adapter establishes the shared MVCC transaction. An offline hash cannot prove
that a payload came from a live complete query, nor does it grant PRECOMMIT authority.

### Failure policy — narrow and explicit

- A valid046A `UNRESOLVED` discovery is data and remains in coverage diagnostics.
- Missing exact binding, unreviewed required RecipeVersion, independent grounding failure or
  corrupt source prevents the frozen046A subject from being captured. For this first integration,
  **the entire requested capture fails with that specific source error**. It does not fabricate
  a discovery/UNRESOLVED contract the source itself cannot truthfully produce.
- A caller may explicitly issue a new METHOD-only request if that supported context is useful.
  The coordinator must not silently drop FLAVOR/MAIN_PROTEIN, infer a default path or return an
  unlabeled partial success.
- Frozen046A path capture grounds the whole proposal, including other batches. A malformed
  outside-window/retired binding cannot be removed just to make capture succeed. An alternative
  partial-capture availability union would require separate design and is deferred.

## 6. Pure join and complete support chain

The pure entry point first serializes/reparses the full proposed input and every frozen nested
contract, then recomputes eligibility and discovery. `model_construct`, `model_copy` and cached
fields are never accepted as independent evidence.

For each selected member:

1. Recompute frozen041A recipe preview facts using its existing algorithm.
2. Flatten **all** allocation supports from every Recipe-ID group, keeping meal/participant
   identity. Join the exact batch and RecipeVersion, not the group representative.
3. Resolve the captured (batch, requested dimension) discovery; retain one coverage diagnostic
   per eligible member/meal/batch/dimension, whether or not a positive exists.
4. For every ASSIGNED positive term, create a support witness and group it by the semantic event
   key in §7. Derive all output fields; never trust caller event/coverage/support summaries.

Eligibility is inherited from canonical graph validation and041A: PLANNED meal, explicit member
participation, PLANNED batch, positive PLANNED allocation and `[window.start, window.end)`.
Graph rules ensure supported HOME meals and causal batch-to-meal timing. There is no `now`
filter turning elapsed scheduled intent into consumption or deleting old proposed intent.

Each positive event must preserve this complete chain inside its immutable source:

```text
household/member → exact participant → meal
 → allocation → planned batch → RecipeVersion identity/provenance
 → METHOD cooking context OR exact selected binding/path
 → Recipes applicability + immutable review lineage
 → finite covered term universe + positive (review_id, term_id)
 → Recipes source frontier
 → MAIN_PROTEIN contextual slot support + pinned Catalog association history/frontier, if needed
```

There is no invented generic `assignment_id` or string `context_ref`. Catalog support uses its
actual review/ingredient/term keys and lineage. The nested046A subject retains those primitive
facts; witness references resolve locally rather than through later database queries.
Exact quantities, bases and provenance in bindings remain unchanged; this join converts nothing.

## 7. Semantic event identity, evidence identity and deduplication

New feature event key is a versioned canonical hash of **exactly**:

```text
household_id, member_id, plan_id, meal_node_id, dimension, feature_term_id
```

Proposal ID/hash, scheduled_at, recipe/version/batch, support cardinality and classification
review are **not** event multiplicity. They remain mandatory in the captured source, fact and
evidence/result fingerprint. Thus a proposal replacement can change the proof of one semantic
event without creating another occurrence merely because the same meal node still exists.

- Two batches → FLAVOR.spicy in one member's meal: **one event, two allocation witnesses**.
- Two terms in one meal: two events. Two meals with the same term: two events.
- Shared meal: a distinct event for every explicitly selected participating member.
- Multiple RecipeVersions or recipe IDs supporting the same term in one meal still give one
  event. Multiple MAIN_PROTEIN slot proofs support the relevant allocation; they are not meals.
- No serving, portion-factor or gram weighting creates extra occurrences.

Within a parent event, witness union is keyed by allocation/batch/dimension; participant,
term and meal are fixed by the parent. Repeated identical support is counted once; conflicting
proof under the same key rejects the input. Cached results with duplicate witnesses reject
canonical revalidation. Source graph duplicate allocation IDs already violate graph validity.

A fresh capture replaces the **whole selected preview**. Old snapshots remain replayable, not
unioned with fresh revisions/reviews. No cross-cut feature merge API is proposed. Replaying
identical immutable input is safe; combining arbitrary overlapping captures is not an authorized
extension of the frozen Recipe-ID dedup function.

## 8. Dimension-specific meaning

**METHOD:** use frozen046A reviewed RecipeVersion cooking-context semantics. Tier, substitution
and micro-adjustment do not change that context. Do not compare raw cooking_method strings
or infer categories from instructions. A distinct cooking method remains an authored recipe
decision, not an exposure generator decision.

**FLAVOR:** use the exact selected culinary path in immutable planned binding. No recipe title,
ingredient-name similarity or inferred flavor propagation is permitted.

**MAIN_PROTEIN:** require exact path, explicit contextual main-protein review, supporting slots
and pinned reviewed Ingredient→PROTEIN Catalog sources. Ingredient order, largest mass or
nutrition protein grams cannot designate main protein. The vocabulary kind PROTEIN does not
create an additional generic PROTEIN exposure dimension.

COUNT can participate only through existing valid authored identity/path support; this source
join needs no nutrition or mass conversion. It must not invent count-to-mass, COUNT substitutions
or nutritional classification. Retail AP→EP and Recipe EP_RAW→COOKED persistence ownership
remain separate and unchanged.

## 9. Coverage and unknowns

| Frozen discovery | Positive event behavior | Diagnostic meaning retained |
| --- | --- | --- |
| ASSIGNED / PARTIAL | Emit only reviewed positives | Known positive assignments, with partial coverage and exact finite universe. Unlisted terms are not absent. |
| ASSIGNED / COMPLETE | Emit reviewed positives | Complete only within this source's pinned finite reviewed universe. |
| REVIEWED_NONE | No positive event | Reviewed absence of assignment within that finite universe, with applicability/review/provenance. Never global absence. |
| UNRESOLVED | No fabricated positive | Preserve exact reason such as NO_SOURCE, NO_MATCHING_SCOPE, RETRACTED, PARTIAL_COVERAGE or STALE_ASSOCIATION. Never false, 0, NO_MATCH or neutral. |

One positive batch plus one unresolved batch preserves **both** the positive witness and the
other diagnostic. It does not make the whole meal completely classified. There is no aggregate
meal-level/global `complete`, `safe`, `novel` or `never_exposed` field.
An empty eligible support set is an explicitly scoped empty selected-proposal preview, not
global behavioral history or zero RepeatPenalty. REVIEWED_NONE also does not imply negative
preference, novelty, cooldown safety or zero policy cost.

## 10. Dimension-sensitive frontiers and identity

Singleton-dimension046A capture is deliberate. METHOD/FLAVOR branches contain Recipes facts
and frontier only; Catalog is forbidden, not null/default0. MAIN_PROTEIN carries actual Catalog
generation and supporting association history as well as Recipes. The outer mixed-dimension
request necessarily depends on the union of requested source branches; that must not introduce
a MAIN_PROTEIN hash into a METHOD/FLAVOR branch.

Recipes currently exposes an owner-wide generation. Unrelated **Recipes** edits may therefore
change a source cut. Do not invent a new dimension-level generation or claim finer invalidation
than the existing authoritative frontier provides.

Here "Catalog dependency" means the **ingredient-association generation/support branch**.
Frozen capture still reads reviewed vocabulary terms through the Catalog-owned term facade,
including METHOD/FLAVOR terms. Those immutable term identities/content remain in their source
proofs. Do not misread conditional association fencing as a prohibition on canonical vocabulary
reads, or add an unrelated Catalog association counter merely because that facade is used.

Three identities need explicit names; they answer different questions:

1. **Semantic event key** (§7): stable member/meal/dimension/term occurrence identity.
2. **Exact captured/result fingerprint:** includes complete frozen snapshots and capture audit
   times. Identical immutable input yields identical bytes/result. A fresh capture may legitimately
   have a different hash even without changed facts because `captured_at` participates in frozen
   hashes. No frozen hash field is removed or reinterpreted.
3. **Proposed dimension evidence-cut digest:** a new, explicitly versioned projection of that
   dimension's source dependencies for comparing semantic capture cuts. Include household/plan,
   selected members, eligibility policy identity/window/provenance, exact canonical workspace and
   proposal identity/hash/content, member/recipe identity manifests, eligible participation and
   allocation references, dimension-specific context/sources/scopes/lineages/universes/positives/
   vocabulary/support and actual frontiers. Exclude **only capture-clock audit fields and other
   dimension branches**; retain source observed_at/recorded_at and ordered lineage. It must not
   embed an opaque mixed-dimension or MAIN_PROTEIN source hash in METHOD/FLAVOR.

This digest is a new contract proposal, not a changed046A hash or authorization token. It makes
the requirement testable: a Catalog-only mutation leaves METHOD/FLAVOR event keys and evidence-cut
digests unchanged when their proposal/policy/member/Recipes facts are unchanged. MAIN_PROTEIN's
digest changes with its captured Catalog generation; fresh discovery can become STALE_ASSOCIATION.
Raw fresh-capture hashes may still differ because of audit time. Compare the correct identity;
do not claim timestamp-dependent frozen hashes must be equal across fresh captures.

An old MAIN_PROTEIN snapshot remains replayable after replacement; a fresh capture must read
current sources and preserve any resulting stale/unresolved classification, without rewriting
the old witness. No query occurs during replay.

Future production flow remains: capture → validate immutable subject → recheck authoritative
source frontiers inside commit/authorization boundary → authorize only if still current and all
required validation capabilities exist. This slice adds neither recheck enforcement nor authority.
Historical snapshot validity does not imply current authorization; PRECOMMIT stays fail-closed.

## 11. Canonical serialization and ordered facts

New outer contracts should have explicit versioned canonical UTF-8 serialization: sorted object
keys, compact separators, canonical UUIDs, exact numeric representations and UTC timestamps
at explicit microsecond precision. No float, silent rounding or generic quantity conversion.
Frozen children retain their existing canonical algorithms:041A `canonical_json`,046A captured
subject `canonical_bytes`, proposal graph `content`, binding `payload`, and existing discovery
recomputation. Do not recursively rewrite those encodings to match new outer conventions.

Validate duplicate/conflicting identities before sorting. Explicitly unordered collections may
be sorted by their typed identities: selected members, requested dimensions, member captures,
classification sources by (batch, dimension), events by event key, witnesses by allocation key,
coverage diagnostics by their owner key, and source-owned term/review sets according to their
existing canonical functions. Permuting such sets yields identical canonical output.

Do **not** generically sort every list. Review lineage follows source revision/sequence;
authored path, tier, instructions, transformations and other ordinal-bearing children retain
their frozen semantics. Future execution/preparation steps require explicit ordinal/sequence
or causal dependency fields. Equal timestamps do not establish earlier/later order, and UUID
ordering must never manufacture causal order. This source slice neither adds feature chronology
policy nor extends frozen Recipe-ID cooldown comparisons.

## 12. Adversarial examples and proposed test plan

These are **future implementation acceptance tests**, not tests added or executed in this PR.
U = pure unit/adversarial contract test; PG = real PostgreSQL/capture/concurrency test;
C = frozen compatibility/import/export regression test.

| # | Counterexample | Required result / proposed layer |
| --- | --- | --- |
| 1 | Two batches assign FLAVOR.spicy to one member/meal | One feature event, two distinct allocation witnesses. U/PG |
| 2 | Two positive terms in one meal | Two distinct dimension/term events. U |
| 3 | Same term in two meals | Two distinct meal events. U |
| 4 | Shared meal, two selected participants | Separate member-owned events; common classification may be captured once. U/PG |
| 5 | Selected member does not participate | No event or invented member coverage for that meal. U/PG |
| 6 | Same version with different tier/substitution/adjustment | METHOD context unchanged; FLAVOR/MAIN_PROTEIN require their exact selected paths. U/PG |
| 7 | REVIEWED_NONE | No positive; retain review/universe/coverage, no global absence/novelty/zero penalty. U |
| 8 | Valid UNRESOLVED source | Preserve exact state/reason, never NO_MATCH, false, zero or neutral. U/PG |
| 9 | MAIN_PROTEIN Catalog support replaced after capture | Old proof replays; fresh capture sees new frontier and any stale support. U/PG |
| 10 | Unrelated Catalog-only edit | METHOD/FLAVOR semantic keys and dimension evidence-cut digests unchanged; no Catalog dependency. Raw new capture audit hash may differ (§10). U/PG |
| 11 | Proposal replaced between component reads | RR/SERIALIZABLE yields one coherent old cut or whole retry/error, never mixed revisions; fresh request must bind fresh proposal. PG |
| 12 | Repeated support / duplicate allocation | Identical support union once; conflicting support rejected; invalid duplicate graph IDs rejected. U/PG |
| 13 | Different RecipeVersions support same feature in one meal | One feature event; retain every exact version/source proof, not a Recipe-ID representative. U |
| 14 | Equal meal timestamps | Separate meal IDs remain separate events; no invented chronological ordering. U |
| 15 | Shuffle unordered source/member/support facts | Canonical bytes/digests/events identical for the same captured primitives; explicit ordinals preserved. U |
| 16 | Forge cached term/coverage/support/result with construct/copy | Full nested source and output revalidation rejects/recomputes; no cached truth. U |
| 17 | Attempt IO during pure derivation | Zero database/network IO; immutable inputs only. U/PG/C |
| 18 | Capture/derive attempts side effects | Read-only source transaction, no writes/commits/physical/preference mutations. PG/C |
| 19 | Suggest feature by recipe/ingredient title or mass | No classification inference; reviewed sources only. U/C |
| 20 | Old041A/B/C/D or046A contract/hash changes | Existing schemas, hashes, algorithms and regression identities retained unchanged. C |
| 21 | Missing exact path/unreviewed required recipe | Specific whole-request capture failure; explicit new METHOD-only request allowed, no silent downgrade. U/PG |
| 22 | Conflicting source histories with matching claimed counters | Reject conflict; frontier number alone cannot validate source facts. U |
| 23 | One batch feeds multiple meals/members | Capture source once per batch/dimension, derive separate events by actual meal/participation. U/PG |
| 24 | No eligible supports in selected window | Empty exact source manifest; actual requested frontiers and explicit scoped diagnostics, not global history. U/PG |
| 25 | Child capture clocks differ in one RR transaction | Accept coherent cut and preserve each frozen time; enforce each child cutoff and outer completion. U/PG |
| 26 | Classification changes without proposal change | Fresh whole preview replaces prior proof; old immutable snapshot replays, no accumulated double count. U/PG |
| 27 | Extra/missing source, unsupported dimension, caller term query | Reject closed request/manifest; no FAMILY, generic PROTEIN or safety inference. U |
| 28 | Invalid bound batch outside selected exposure window | Frozen whole-proposal grounding still fails; no trimming to bypass046A. U/PG |

Implementation tests must additionally verify per-household/member access, strict request versions,
recipe identity agreement, policy/source provenance/time cutoffs, PARTIAL positives alongside
unresolved support, COUNT identity preservation, MAIN source lineage, raw/prepared separation
and pure-core import boundaries. Current independent recipe grounding remains reused, not replaced.
Future real-PG tests should use authoritative append/replacement services and actual concurrent
transactions, plus existing sealed-source tamper attempts; mocks cannot prove snapshot coherence.

## 13. Persistence and explicit deferred work

**No migration expected; no0014.** The durable truths already exist in proposal/recipe/binding
and0013 reviewed-source tables. This output is an immutable captured/derived draft. A new
canonical behavioral exposure ledger risks promoting provisional selected-proposal evidence into
durable behavioral truth and is unnecessary for replay. Archiving captured payloads, if separately
needed later, would not itself make them behavioral history. Schema stays0013 /71 tables.
Released0001–0013 remain unchanged.

Deferred: feature cooldown/decay/RepeatPenalty aggregation; novelty/TasteFit; MemberBehaviorProfile;
EvidenceStrength; priors/shrinkage; utility/rank/portfolio/optimizer; accepted/confirmed/cooked/
consumed exposure; durable member history; Execution; PRECOMMIT authority; cross-horizon history;
variant-family identity; allergen/diet classification. No feature intent is evidence that someone
ate, accepted or liked a dish. No planned acquisition/reservation becomes physical movement.
No partial-capture availability framework, cross-cut exposure merge, new frontier table or
generic cross-domain persistence is proposed.

## 14. Invariant mapping — design only

Exact canonical wording from [invariants](../ARCHITECTURE_INVARIANTS.md):

| Invariant | Design consequence |
| --- | --- |
| INV-005 — Recipe flexibility must be authored, not inferred. | Source join consumes exact authored path, never creates possibilities or classifications. INV-006 remains preserved. |
| INV-012 — Elapsed time is not evidence of consumption. | Scheduled exposure stays proposed even after its scheduled_at passes. |
| INV-013 — Inference may update a projection; only evidence may update confirmed reality. | PROVISIONAL only; no physical/history mutation. |
| INV-018 — Primitive facts must carry explicit measurement basis and provenance before independent recomputation. | Retain full typed source/binding/provenance; no string inference or AP/EP/COUNT conversion. |
| INV-021 — Validation of intent is gating; validation of reality is diagnostic. | No authorization token or mutation; PRECOMMIT remains fail-closed. |
| INV-022 — Passive execution assumptions must not create durable behavioral learning. | Neither elapsed proposal nor empty preview creates durable history. |
| INV-026 — Shared meals may aggregate preferences; they must not erase member-level preference ownership. | Exposure belongs to explicit participating member, with no preference copying or inference. |
| INV-027 — Behavioral dimensions remain separable until planner utility composition. | Exposure source is not TasteFit, friction, EvidenceStrength, utility or ranking. |
| INV-030 — Future commitments must be honored when projecting inventory and exposure across planning horizons. | This selected-proposal window is not a bridge implementation or global exposure truth. |

INV-015/016/017/020 independence/primitives remain intact: no planner safety summary replaces
primitive validation, no duplicated matcher/objective, no full validator completion claim.
Existing physical-ledger and materialization ownership invariants remain unchanged. This design
adds **no implemented invariant enforcement**; proposed tests above are not completed coverage.

## 15. Naming recommendation and approval boundary

Recommend **MTR-041E — Proposal-local Reviewed Feature Exposure Sources**, conditionally.
041 owns exposure interpretation. A supplies Recipe-ID sources; B/C/D implement separately
frozen Recipe-ID policy layers. The newly available046A source makes a new feature-source join
possible. This is a source integration, not another arithmetic wrapper after041D.

No existing reserved/implemented041E was found in the inspected backlog/code. The suffix must
still be approved by the architecture reviewer. This document neither renumbers canonical tasks
nor opens/closes a new canonical root issue. Calling it046B would place member/meal exposure in
the classification owner instead of Learning. Keep046A classification frozen and consume it.

The source prerequisite is sufficient to **design this narrow slice now**. It is not sufficient
to finish full041 or040, start024/020B/021, or claim global multi-fingerprint recent exposure.
No next implementation is authorized by merging this design PR. Stop for architecture approval.

## 16. Verification evidence for this documentation package

Reviewed baseline is428b992892ac2aeebdbedb8bb3fd5e436e76415c. Its exact merge
[CI40172577535](https://github.com/thedusk4203/Menuto/actions/runs/40172577535)
was independently rechecked: completed/success, matching head SHA, Python and web.
This review adds **zero runtime/contracts/tests/migrations/exports**.

Local existing gates on2026-10-25:

| Gate | Actual result |
| --- | --- |
| Full Python with real PostgreSQL18 | **1758 passed, 0 failed/errors/skipped**; one pre-existing FastAPI/Starlette httpx deprecation warning |
| Prior regression identities | All1758 baseline tests retained; no new test is claimed |
| PostgreSQL-real subset | **728 passed**,1030 deselected; explicit `-m postgres` run,0 failed/errors/skipped |
| Migration/metadata drift | Existing real-PG suite covers migration roundtrips, populated fail-closed downgrade, direct SQL and schema/ORM parity; head0013 /71 tables |
| Ruff / architecture / import boundaries | PASS;30 invariants /11 ADRs /50 linked tasks;16 registered contexts |
| OpenAPI/domain exports and synthetic fixtures | PASS; exports unchanged;22 fixtures verified |
| Synthetic benchmark | **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client contracts/typecheck/tests + web build | PASS; client **10/10** |
| Frozen compatibility / diff |9 Markdown files only; all runtime/tests/0001–0013 migrations/export bytes unchanged; all226 contract definitions unchanged; `git diff --check` PASS |
| PR / exact post-merge CI | Run links and exact head/merge identities are recorded in the final delivery receipt after GitHub completes; this local evidence table does not infer remote PASS |

Full run: `.venv/Scripts/python -m pytest --basetemp=.local/post046a-full
--junitxml=.local/post046a-full.xml` with MENUTO_TEST_POSTGRES_URL targeting local PostgreSQL18
and isolated test databases. Other gates match `.github/workflows/ci.yml`. `.local` artifacts
are local logs, not source data. The first doc-link check found and corrected a relative invariant
link; final architecture checking passed. A separate `-m postgres` attempt inside the restricted
sandbox could not reach the local server and was stopped; the authorized rerun with local
database access completed **728/728** (`.local/post046a-pg-verified.xml`). That environment failure
is not counted as a passing run. No test or database behavior was changed to obtain PASS.

These gates prove existing behavior remains green and documentation links are sound. They
**do not test the proposed feature contracts, coordinated capture or pure feature join**, which
remain unimplemented pending approval. The adversarial matrix is a future acceptance plan.

**READY FOR FEATURE-AWARE MTR-041 ARCHITECTURE/DESIGN REVIEW**
