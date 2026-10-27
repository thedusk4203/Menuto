# Candidate-bound Reviewed Culinary Feature Projection Foundation

Status: **DESIGN READY FOR ARCHITECTURE REVIEW — IMPLEMENTATION NOT AUTHORIZED**.
No new MTR suffix is assigned. This document proposes contracts and acceptance criteria;
it does not add those contracts, APIs, tests, persistence or classification data.

## 1. Objective and exact dependency baseline

Bind one frozen MTR-019B/C canonical pre-selection candidate to frozen MTR-046A reviewed
METHOD / MAIN_PROTEIN / FLAVOR discovery, without a plan, proposal or cooking batch.
The result is a captured, replayable classification projection, not a second classifier.

| Baseline item | Exact receipt |
| --- | --- |
| Repository / design branch base | `thedusk4203/Menuto`, main `623218e2713faf950dd01325436c9a6e3969f638` |
| Approved dependency review | [PR #110](https://github.com/thedusk4203/Menuto/pull/110), reviewed head `e8989e41e237a81b330adc6387dee44881b67e99`, reviewed base `b42abd13226c983b9f131f0b15671e134292fcfb` |
| Actual merge | `623218e2713faf950dd01325436c9a6e3969f638`; parents are the reviewed base and head; merged tree equals the approved head; exactly five Markdown files |
| Exact post-merge push CI | [40499400731](https://github.com/thedusk4203/Menuto/actions/runs/40499400731), SUCCESS; python/web SUCCESS on the actual merge SHA |
| Retained checks | 2,978 pytest passed; SCRAM/TLS 16/16; benchmark 22/22; client 10/10; contract, export, typecheck and build checks passed |
| Exports / schema | 358 domain definitions; `0015 / 85` domain tables; no migration `0016` |
| Final parent closure | MTR-040 COMPLETE; issue #41 CLOSED / COMPLETED; all frozen 040 semantics remain unchanged |

The [approved dependency selection](POST_MTR_040_NEXT_MILESTONE_DEPENDENCY_REVIEW.md)
identifies this missing input seam before candidate/member composition. The user separately
authorized this dedicated design after PR #110's successful merge and push CI. Approval of
dependency selection is not approval of the contracts proposed here.

## 2. Problem and source-of-truth inventory

Existing Planning feature capture requires a current proposal and batch. Frozen Recipes
classification already accepts an exact authored recipe/path without that proposal. Inventing
a temporary proposal would import unrelated ownership and current-head semantics. Copying
classification rules into Planning would create competing truth. This design does neither.

| Existing source / contract | Reused meaning and limit |
| --- | --- |
| [Recipes contracts](../../apps/backend/app/modules/recipes/contracts.py): `CulinaryCandidateDraft`, `RecipeVersionSnapshot` | Exact reviewed version, source hash, tier, rule selection, resolved ingredients, transformations, servings and provenance. Current generated candidates have zero adjustment deltas. Candidate triggers are retained even though the frozen culinary candidate fingerprint excludes them. |
| [Recipes public API](../../apps/backend/app/modules/recipes/public.py): `authored_version`, `resolve_candidate_source` | Exact-version owner read and pure reconstruction of selected authored ingredients/preparation. No latest-version, title or fuzzy lookup. |
| [Planning grounding capture](../../apps/backend/app/modules/planning/grounding_capture.py) / [grounding replay](../../apps/backend/app/modules/planning/grounding.py) | Canonical 019C primitive capture and `resolve_captured_candidate`; reviewed recipe, Catalog identities, nutrition, supply and member restriction context. A self-consistent serialized `GroundedDishCandidate` alone does not prove this capture occurred. |
| [Planning contracts](../../apps/backend/app/modules/planning/contracts.py) | `CandidateGroundingRequest`, `CandidateGroundingSources`, `GroundedDishCandidate`; frozen grounding canonical serialization and fingerprint. Structural construction of a candidate is not full grounding replay. |
| Recipes `CulinaryFeatureEvaluationInput`, `discover_feature_input` | Frozen 046A source validation, applicability matching, support and dimension discovery. METHOD uses recipe cooking context; FLAVOR / MAIN_PROTEIN use selected authored path. |
| [Catalog contracts](../../apps/backend/app/modules/catalog/contracts.py) / [public API](../../apps/backend/app/modules/catalog/public.py) | Reviewed affinity terms and ingredient/protein association history and frontier. MAIN_PROTEIN support must satisfy frozen context and association rules. |
| [Existing proposal capture](../../apps/backend/app/modules/planning/feature_capture.py) | Owner read pattern, complete historical support/term manifests and coherent transaction requirements. Its proposal/current-head contracts and behavior are not changed or called with fabricated proposal nodes. |
| [Canonical feature identity](../../apps/backend/app/domain/feature_identity.py) | Deterministic new-envelope encoding; UTC microsecond times; dictionary key ordering; no floating point. Frozen child encodings remain independently intact. |

Requirements remain bounded by [Spec V1.3](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[INV-001..030](../ARCHITECTURE_INVARIANTS.md), [ADR-011](../adr/ADR-011-behavioral-learning-loop.md)
and the accepted [post-MTR-040 dependency review](POST_MTR_040_NEXT_MILESTONE_DEPENDENCY_REVIEW.md).
This design does not add acceptance obligations to completed MTR-040.

## 3. Ownership and authority

Planning owns candidate/source coordination, binding, capture and replay of this derived view.
Recipes owns authored path truth and culinary classification/applicability. Catalog owns term
identity and ingredient/protein association truth. Owner public read APIs remain the only database
ingress; the new pure layer neither publishes nor edits reviewed facts.

The caller's member/household context is retained only because frozen grounding requires it.
It grants no preference, EvidenceStrength, learned-event or global reference publication authority.
The capture adapter authenticates its read context using existing Household access checks;
a serialized user ID, reviewer ID, provenance label or fingerprint is not an access capability.

The projection is not TasteFit, member preference, novelty, RepeatPenalty, utility, role score,
ranking, hard feasibility or safety certification. It cannot issue PRECOMMIT or authorize Execution.
All new result readiness flags are literally `planner_ready=False`, `activation_ready=False`.
The frozen child's `shortlist_input_ready=True` is retained as an existing 019C fact and does not
make this feature projection planner-ready. No child flag is promoted into new authority.

## 4. Proposed contract boundary

Exactly four additive contract types are proposed in existing `planning/contracts.py`.
Existing 019B/C, proposal feature capture and 046A contract schemas stay unchanged.
All new types forbid unknown fields; UUIDs, hashes, exact amounts and aware times use existing
strict types. Collections that represent new sets reject duplicates before normalization.

| New type / version | Proposed fields and meaning |
| --- | --- |
| `CandidateFeatureProjectionRequest` / `candidate-feature-projection-request.v1` | `grounding_request: CandidateGroundingRequest`; required `expected_grounding_fingerprint: Sha256`; nonempty unique `requested_dimensions` from METHOD, MAIN_PROTEIN, FLAVOR only. No supplied feature facts, source snapshot, query terms, proposal, batch or preference input. |
| `CandidateFeatureProjectionSourceSnapshot` / `candidate-feature-projection-source.v1` | Full `request`; freshly reconstructed `grounded_candidate: GroundedDishCandidate`; `grounding_issues: tuple[GroundingIssue, ...]` from the successful frozen grounding result; `feature_input: CulinaryFeatureEvaluationInput`; `capture_started_at`, `capture_completed_at`; literal `capture_semantics=GROUNDING_AS_OF_AND_FEATURE_CAPTURE`; `fingerprint`. Retains all primitive grounding and feature sources through the children. It is replay input, not a signed database-origin certificate. |
| `CandidateFeatureBinding` / `candidate-feature-binding.v1` | `grounding_fingerprint`, `culinary_candidate_fingerprint`, `recipe_id`, `recipe_version_id`, `recipe_source_hash`, `path: FeatureSelectedPath`. Every field is derived and checked against the retained subject. No independent variant/family UUID is invented. |
| `CandidateFeatureProjectionDraft` / `candidate-feature-projection.v1` | Full `source: CandidateFeatureProjectionSourceSnapshot`; derived `binding`; one `FeatureDimensionDiscovery` per requested dimension; literal `status=DERIVED`; literal false readiness flags; `fingerprint`. DERIVED means replay completed, not complete classification coverage or downstream eligibility. |

The frozen `FeatureDimensionDiscovery` already expresses assigned terms, coverage, missingness,
applicability ID and review ID. Reuse it rather than introduce another assignment taxonomy.
The full retained source supplies typed provenance/support witnesses as specified in §9.
No naked list of feature IDs is a canonical result of this interface.

## 5. Canonical subject identity and ingress

The caller supplies a frozen grounding request and the exact fingerprint of the grounded candidate
it intends to project. That expected fingerprint is a binding expectation, not proof of origin.
Capture reloads/reconstructs canonical grounding sources from owner APIs in one transaction,
calls frozen `resolve_captured_candidate`, requires GROUNDED and requires the resulting fingerprint
to equal the expectation. A changed source cut that changes grounding identity fails explicitly;
the caller must consciously request projection of a freshly grounded candidate.

The entire grounding request must equal the request retained in the reconstructed candidate under
frozen grounding serialization. Pure replay always re-runs grounding from `candidate.request` and
`candidate.sources` and compares the entire freshly derived candidate canonical JSON, not only its
fingerprint. GROUNDED output with warnings is retained exactly in `grounding_issues` and compared
with freshly recomputed issues; the frozen candidate itself has no issues field. INCOMPLETE or
REJECTED is not converted into a usable feature subject. No hand-built `status=GROUNDED` bypass
is accepted.

These four claims are deliberately separate:

| Claim | What establishes it |
| --- | --- |
| Canonical candidate reconstruction at ingress | Owner reads plus frozen 019C replay in the authenticated coherent capture transaction |
| Equality of serialized candidate claims | Full canonical child comparison and recomputation; necessary for replay, insufficient for database origin |
| Database/source provenance | The capture path and its actual transaction/access controls; never a caller-minted label, hash or `canonical=True` flag |
| Replay identity | Retained primitive sources, child algorithms and full-source fingerprints; identifies what was captured, not current database truth |

An offline caller can construct a wholly self-consistent fictional world. Pure replay cannot prove
that world came from the canonical database. Canonical capture therefore accepts selectors and
the grounding request only, never caller-supplied source primitives or a cached projection as truth.
No new HTTP endpoint or durable certification/attestation protocol is included.

## 6. Exact candidate/path coherence

Validation is mandatory before discovery, including on deserialized or `model_construct` inputs.

1. Reparse the complete request and source envelope; validate exact frozen child versions/types.
2. Recompute the 019C child from primitives; require full child equality and expected fingerprint.
3. Require the full immutable `RecipeVersionSnapshot` in grounding sources and feature evaluation
   to agree under the frozen recipe representation. Comparing only version ID or source hash is
   insufficient. A different version is `RECIPE_VERSION_MISMATCH`; differing facts under the same
   immutable identity are `SOURCE_CUT_INCOHERENT`.
4. Derive `FeatureSelectedPath` from the verified candidate's exact tier, selected rule IDs and
   resolved requirement rows. Include one exact zero delta for every requirement, as currently
   guaranteed by 019B/C. Nonzero candidate adjustments are rejected through frozen replay;
   this slice does not add refinement candidates or adjustment envelopes.
5. Preserve selected ingredient IDs, servings, transformations and provenance through the full
   candidate. Re-run frozen Recipes binding via 019C; neither a path key nor a candidate hash
   substitutes for authored ingredient/preparation validation.
6. If only METHOD is requested, require `feature_input.path=None` under frozen recipe-context
   semantics, while the outer binding still retains the exact candidate path. Otherwise require
   exact equality with the derived `FeatureSelectedPath`, including all requirement deltas.
7. Require feature evaluation dimensions to equal the request's normalized dimension set; require
   exact recipe version on every scope. Frozen 046A validates source-owned applicability keys,
   review lineage, support and overlap. Candidate identity never becomes an applicability key.
8. Compare every repeated immutable record with the same typed owner identity across retained
   cuts. Conflicting payloads fail the entire subject, including unused historical records.
   A projection view and a different owner contract sharing an ingredient UUID are not falsely
   treated as identical records; their shared identity/path relationships are validated instead.

METHOD context is the exact reviewed RecipeVersion cooking context. It does not become a
path-level classification merely because the outer result binds a path. Two candidate paths may
legitimately discover the same METHOD facts while retaining different complete subject identities.
FLAVOR / MAIN_PROTEIN matching always uses frozen exact-path/reviewed-scope rules. No latest
recipe, family transfer, title, alias, ingredient mass or inferred dominant protein is used.

## 7. Capture, source cuts and independent clocks

`capture_candidate_feature_projection_sources` is a read adapter, not a publisher:

1. Require a clean, caller-owned, read-only REPEATABLE READ or SERIALIZABLE transaction.
   Use existing Household actor/household/member access checks. No commit, write, lock-based
   publication, CAS, idempotency receipt or new permission regime is introduced.
2. Record `capture_started_at`. Call frozen 019C canonical primitive capture and grounding replay;
   check the expected fingerprint. Access failures and source-read failures abort the whole capture.
3. Reuse that exact captured RecipeVersion for feature evaluation. Read all Recipes scopes and
   complete retained review histories for requested dimensions, with the actual recipe frontier.
4. For MAIN_PROTEIN only, capture Catalog streams for the exact union of ingredient IDs referenced
   by **all historical support rows** in those scopes, plus the actual Catalog frontier. Use the
   frozen `MainProteinFeatureSources` type. Otherwise use `RecipeFeatureSources` and do not invent
   Catalog streams/frontier. A real captured frontier of zero is valid; zero is never fabricated.
5. Capture the exact term manifest required by frozen 046A: the union of covered terms across all
   retained Recipe and applicable Catalog histories, not just the currently visible positive terms.
6. Set frozen `feature_input.captured_at` to the actual clock after source reads; construct and
   validate that input through 046A. Record `capture_completed_at` after validation. Require
   `capture_started_at <= feature_input.captured_at <= capture_completed_at`.
7. Derive/validate the source envelope and fingerprint before returning. Do not downgrade a
   failed multi-dimension capture to METHOD-only. A caller may submit a new explicit request.

The MVCC transaction gives the owner reads one coherent logical database cut. Recipe and Catalog
frontiers are independent counters; they need not equal each other or a timestamp. All retained
review sequences must satisfy the frozen per-source frontier rules and all review `recorded_at`
values must be within frozen feature capture time. Captured history cannot be truncated to hide
stale support, conflicting applicability, retraction or correction.

### Temporal meaning is explicit, not a universal historical cutoff

Frozen `grounding_request.as_of` is preserved as the 019C business-time eligibility input for
nutrition/retail/inventory and other existing grounding rules. Frozen 046A `captured_at` is the
actual feature capture clock. They are **not required to be equal**. This slice adds no universal
ordering between `as_of` and capture time beyond rules already enforced by the frozen children.
Other child effective/observation timestamps likewise retain their owner meanings.

In particular, a review recorded after grounding `as_of` but before feature capture may participate
under frozen 046A rules. The result does **not** claim all feature facts existed at grounding
`as_of`. Canonical Inventory capture already rejects an `as_of` later than its current clock;
the new adapter preserves that rejection. Offline grounding replay has no current-clock access:
an otherwise valid retained future-dated input proves no future inventory, reviews or availability.
Only captured facts and frozen eligibility rules are replayed. Consumers requiring a
different all-domains historical instant need a separate design, not a relabeled capture clock.

Historical replay means replaying this retained cut, including both time meanings, without I/O.
It does not fetch an arbitrary past MVCC snapshot or certify that the retained frontier is live.
Independent old children cannot be spliced into canonical capture. Offline checks can reject
contradictory facts/clocks/frontiers but cannot prove that two otherwise consistent invented cuts
were captured in the same real transaction. That guarantee belongs to the read adapter.

## 8. Reuse of 046A classification

After coherence checks, call frozen `discover_feature_input` on the full primitive feature input.
Do not duplicate its matcher or pass cached discovery as its input. This preserves:

- reviewed METHOD cooking-context scope;
- FLAVOR / MAIN_PROTEIN exact-path or explicitly reviewed authored-scope applicability;
- finite coverage, review revision lineage and retraction;
- MAIN_PROTEIN support for the actual authored ingredient/path, with pinned Catalog association
  valid at publication, and frozen stale-association behavior at capture;
- conflict rejection for overlapping active applicability and exact term/support manifests.

No new query-term universe is inferred. Optional unrequested dimensions are absent from the
projection, not labeled neutral, reviewed-none or eligible. One candidate and one explicit set
of one to three dimensions is the entire unit; there is no candidate aggregation or portfolio.

## 9. Result, support and coverage

`dimensions` contains exactly the frozen discoveries, ordered by dimension wire value.
Consumers can inspect METHOD / MAIN_PROTEIN / FLAVOR separately; no giant scalar or dimension
weight is provided. Each row preserves state, reason, applicability ID, review ID, coverage,
covered term IDs and positive term IDs exactly as returned by the owner resolver.

Support/provenance is explicit and replayable through the retained typed source:

| Result reference | Exact witness in retained source |
| --- | --- |
| `applicability_id` | Scope with that ID and its frozen `RecipeMethodContextKey` or `CulinaryFeaturePathKey`; use the owner key/fingerprint, not candidate identity |
| `review_id` | Exact revision, predecessor, sequence, reviewer, recorded time, authored command, command hash and provenance in that scope |
| MAIN_PROTEIN positive term | That review's `MainProteinSupport(term_id, requirement_id, ingredient_id, catalog_review_id)` rows, verified against actual selected path |
| Pinned Catalog association | Exact ingredient stream and review ID, with complete retained revision/command history and source frontier |
| Term identity / finite coverage | Full typed term manifest and the review's covered universe / PARTIAL or COMPLETE status |

No synthetic assignment ID or publication authority is created. Missing/retracted/stale rows
retain whatever applicability/review references frozen discovery supplies; a reference alone
does not mean an active positive assignment. Callers may index this retained graph but may not
strip it and claim that a bare term list is the canonical projection.

## 10. Missingness and failure taxonomy

Normal source missingness is a successful replay with explicit dimension diagnostics:

| Frozen discovery | Required interpretation |
| --- | --- |
| `ASSIGNED`, PARTIAL or COMPLETE | Positive reviewed terms exist for this dimension/path; PARTIAL still leaves uncovered terms unresolved |
| `REVIEWED_NONE`, COMPLETE | Reviewed absence within the finite covered universe; not no exposure, neutral preference, zero repeat or globally empty classification |
| `UNRESOLVED / NO_SOURCE` | Source read succeeded, but no captured scope for that requested dimension |
| `UNRESOLVED / NO_MATCHING_SCOPE` | Reviewed sources exist, but do not match this exact subject |
| `UNRESOLVED / PARTIAL_COVERAGE` | Matching partial review without positive assignment; uncovered terms remain unknown |
| `UNRESOLVED / RETRACTED` | Frozen source retraction, not reviewed-none |
| `UNRESOLVED / STALE_ASSOCIATION` | MAIN_PROTEIN support no longer uses the captured current Catalog association head under frozen rules |

The following proposed stable `ResolutionError.code` values abort the complete operation.
Reuse the existing [resolution error interface](../../apps/backend/app/domain/resolution.py);
do not introduce a second error object/transport. Human `detail` is explanatory, not identity.

| Code | Trigger / boundary |
| --- | --- |
| `INVALID_REQUEST` | Malformed request, empty/duplicate dimensions, wrong child contract version, unknown extra field or Inventory capture's nonfuture-cutoff requirement violated |
| `UNSUPPORTED_DIMENSION` | A dimension outside METHOD / MAIN_PROTEIN / FLAVOR; reject before attempting fallback |
| `CAPTURE_CONTEXT_INVALID` | Dirty, writable or insufficiently isolated transaction; malformed capture interval |
| `CAPTURE_ACCESS_DENIED` | Existing Household authorization denies the capture context |
| `CANONICAL_SOURCE_UNAVAILABLE` | Required canonical grounding identity/source cannot be loaded; never an empty feature manifest |
| `CAPTURE_IO_FAILURE` | Source read/transaction/resource failure; no partial result; original cause retained for internal diagnosis |
| `GROUNDING_INCOMPLETE` / `GROUNDING_REJECTED` | Frozen grounding cannot produce GROUNDED; preserve its issue codes in diagnostic detail, never fill missing facts |
| `EXPECTED_GROUNDING_MISMATCH` | Fresh grounding fingerprint differs from the request's pinned candidate |
| `RECIPE_VERSION_MISMATCH` | Different recipe version across grounding / feature subject |
| `PATH_MISMATCH` | Feature path or outer binding differs from the reconstructed exact candidate path |
| `SOURCE_CUT_INCOHERENT` | Conflicting repeated immutable facts, source frontier/clock violation or incompatible child cuts |
| `FEATURE_SOURCE_INVALID` | Frozen 046A rejects source shape, support, manifest, lineage or applicability conflict |
| `REPLAY_MISMATCH` | Cached child/output, binding or source/result fingerprint disagrees with recomputed primitives; includes missing required replay provenance |

Request syntax/support is checked first, capture transaction/access next, canonical grounding
next, expected binding and cross-cut coherence next, 046A validation/discovery next, cached output
comparison last. Structural child errors are translated at their owning stage; no first-error
ordering is promised among multiple errors within the same frozen child. Unsupported dimensions
can be identified at request parsing before Literal validation. Set `rejected=True` for invalid,
incoherent or tampered claims; unavailable sources, incomplete grounding and operational failures
remain unavailable without implying a culinary rejection. Preserve frozen rejection meaning for
GROUNDING_REJECTED. Error detail is not included in any successful-result fingerprint.

Source unavailability is not classification missingness. Exceptions must not be caught and
converted to empty scopes, `REVIEWED_NONE`, zero, neutral, not-applicable or acceptable/eligible.
An actual captured empty history/zero frontier has meaning only under the frozen source contract.

## 11. Primitive replay and tamper model

The pure projection operation takes the complete source envelope. It reparses all data, re-runs
019C from request + primitive sources, verifies complete child equality, derives exact binding,
checks cross-cut coherence, then re-runs 046A from primitive feature input. It computes fresh source
and result fingerprints. A supplied cached discovery or grounding hash is never the authority.

The separate public `validate_candidate_feature_projection` operation takes an untrusted result,
reconstructs all expected fields through that same pure core and compares the **entire** canonical
result, including full source, binding, discovery rows, diagnostics, flags and fingerprint. It
returns a freshly derived result. Rehashing an edited output without changing its primitive source
does not pass. Edited child sources must also pass frozen child replay and cross-cut checks.

Contract parsing supplies strict structural/fingerprint-shape checks; it does not itself certify
full semantic replay. This distinction is necessary under the existing import guard: contracts
must not import runtime, including same-domain runtime. All consumers of serialized/cached results
must call the public semantic validator before treating the projection as replay-validated.
`model_construct`, `model_copy`, a matching supplied hash or successful Pydantic parsing is no bypass.
No boolean `validated` field can replace this operation. Internal derivation computes expected
payloads without recursively calling the public result validator.

The pure core has no database, session, network, filesystem or clock access. It uses retained
times and frozen resolvers. Existing 019C pure replay calls owner pure functions exposed through
public facades; this is not permission to invoke their I/O APIs. Tests must trap I/O at execution,
not falsely claim all transitive imports are contracts-only. It neither checks current permissions
nor refreshes current heads. Self-consistency proves neither database origin nor current authority.

## 12. Deterministic full-source fingerprint

Keep frozen child hashes/encodings unchanged. Define new payloads explicitly:

```text
request_payload = {
  contract_version,
  grounding_request_json: grounding_canonical_json(request.grounding_request.model_dump(mode="json")),
  expected_grounding_fingerprint,
  requested_dimensions: sorted(unique dimension wire values)
}
source_payload = {
  contract_version,
  request: request_payload,
  grounded_candidate_json: grounded_candidate.canonical_json(),
  grounding_issues_json: grounding_canonical_json({issues: [issue.model_dump(mode="json") for issue in grounding_issues]}),
  feature_input: feature_identity.canonical(full feature_input),
  capture_semantics,
  capture_started_at,
  capture_completed_at
}
source.fingerprint = sha256(feature_identity.canonical_bytes(source_payload))
result_payload = {
  contract_version,
  source: source_payload,
  source_fingerprint: source.fingerprint,
  binding: full derived CandidateFeatureBinding including its contract_version,
  dimensions: full frozen discoveries sorted by dimension wire value,
  status,
  planner_ready: false,
  activation_ready: false
}
result.fingerprint = sha256(feature_identity.canonical_bytes(result_payload))
```

`grounding_canonical_json` is the frozen Planning serializer; embed its returned string unchanged.
`grounded_candidate.canonical_json()` likewise embeds the complete frozen candidate, including
its own child fingerprints. The new envelope uses frozen feature canonical encoding: UTF-8,
sorted dictionary keys, compact separators, aware times normalized to UTC with six microsecond
digits, no floats. Child list order/Decimal representation remains governed by each frozen child;
do not recursively sort every child list or rewrite frozen bytes. New dimension sets are sorted;
the binding path uses frozen `FeatureSelectedPath` normalization. No new equivalence for alternate
Decimal spellings or reordered frozen child histories is invented.

Only the fingerprint being computed is omitted from its own payload. Every declared semantic
field is covered: expected identity, complete candidate/request (including generation triggers),
recipe/path/ingredients/context, every retained source revision/command/provenance, full term and
support manifests, independent frontiers/times, diagnostics, coverage and readiness flags.
No runtime elapsed duration, transport tracing or error text is a result field. Adding a future
semantic field requires a deliberate contract/identity version decision, not silently omitting it.

Consequences: identical retained input replays identically; a new capture clock/cut changes
identity even if visible positive terms are unchanged. Corrections/history changes and changes
to generation triggers must change outer identity even where a frozen child hash alone does not.
This is capture/replay identity, not merely a hash of visible target rows and not an origin seal.

## 13. Module and public API proposal

| Proposed location | Responsibility |
| --- | --- |
| `apps/backend/app/modules/planning/contracts.py` | Four additive types from §4; strict shape and literal authority limits; no runtime imports or changes to frozen type fields |
| `apps/backend/app/modules/planning/candidate_feature_capture.py` | Authenticated read-only adapter; owner source reads in one transaction; expected candidate check; capture clock |
| `apps/backend/app/modules/planning/candidate_feature_projection.py` | Pure primitive replay, coherence, binding, frozen discovery, canonical payload construction and semantic result validation |
| `apps/backend/app/modules/planning/public.py` | Additive exports for the three functions below; no new external endpoint or module dependency inversion |

```python
capture_candidate_feature_projection_sources(
    session, request: CandidateFeatureProjectionRequest, *, actor_user_id: UUID
) -> CandidateFeatureProjectionSourceSnapshot

project_candidate_features(
    subject: CandidateFeatureProjectionSourceSnapshot
) -> CandidateFeatureProjectionDraft

validate_candidate_feature_projection(
    result: CandidateFeatureProjectionDraft
) -> CandidateFeatureProjectionDraft
```

Capture returns a fully validated subject; project revalidates it regardless of ingress. Validation
returns a freshly recomputed result, not a boolean attestation. Keeping these three operations
separate permits offline replay while making canonical ingress and I/O observable and testable.
No abstract provider framework, classifier plug-in, service registry or new policy coordinate is needed.

Future implementation tests should live in `test_candidate_feature_projection.py` and
`test_postgres_candidate_feature_projection.py`, using real owner publication/capture for database
cases. Strengthen import/I/O guards for this pure boundary without relaxing existing rules in
[check_import_boundaries.py](../../tools/check_import_boundaries.py). Contracts stay contracts-only;
cross-domain implementation imports remain forbidden. Preferences, Learning, solver, ranking and
utility dependencies are forbidden for the new core. None of these code/test/tool edits occur in
this design PR. Public export growth is reviewed later; no future export count is reserved here.

## 14. Persistence and resource decision

**Capture + pure replay contract; zero new persistence.** Existing owners already store all source
truth. The new envelope can be returned/serialized by a trusted caller for replay; this slice adds
no storage service, table, migration, cache, durable aggregate, production rows or source defaults.
Schema stays `0015 / 85`; no `0016`. No member profile aggregate or classification publication occurs.

Capture handles exactly one candidate and at most three dimensions. Existing source contracts
bound finite manifests; this slice adds no arbitrary numeric policy limit or history truncation.
Resource/transaction failures abort the complete capture. A later performance cache or additional
retention protocol would need a separate authority/invalidation design and review.

## 15. Acceptance matrix for a separately authorized implementation

Stable IDs CFP01–CFP60. U = pure/contract test; PG = real PostgreSQL capture test;
B = boundary/regression check. These are proposed future tests, not implemented by this PR.

| ID | Concrete input / seam | Required outcome | Layer |
| --- | --- | --- | --- |
| CFP01 | Canonical 019B candidate captured/grounded through 019C, three dimensions | Exact candidate binding and owner discoveries; no proposal/batch required | U/PG |
| CFP02 | METHOD-only request for reviewed cooking context | Exact METHOD discovery; child path=None; outer exact path retained | U/PG |
| CFP03 | MAIN_PROTEIN with valid reviewed authored-path/Catalog support | Positive term plus complete support/review/term witnesses retained | U/PG |
| CFP04 | FLAVOR exact-path review | Discovery equals frozen 046A on the selected path | U/PG |
| CFP05 | Two RecipeVersions with similar title/ingredients | Exact selected version only; no latest/title/alias fallback | U/PG |
| CFP06 | Alternate authored tier/rule path with different ingredients | Reconstructed rows/path select only matching reviewed applicability | U/PG |
| CFP07 | Transformation-sensitive context | Match frozen preparation/applicability exactly | U/PG |
| CFP08 | Nonzero delta or forged serving/ingredient/transformation claim | Reject through frozen 019C replay; no refinement support added | U |
| CFP09 | Same METHOD context on two valid candidate paths | METHOD facts may agree; outer candidate/path identity remains distinct | U |
| CFP10 | Unsupported dimension, including INGREDIENT | UNSUPPORTED_DIMENSION; no substitution or partial success | U |
| CFP11 | Empty/duplicate dimensions, extra field, wrong version | INVALID_REQUEST; duplicates not silently deduplicated | U |
| CFP12 | Same new dimension set in different order | Normalized request/result order and identical outer identity | U |
| CFP13 | Serialized GROUNDED candidate with edited claims and recomputed supplied hash | Frozen primitive replay rejects inconsistent child; hash is not authority | U |
| CFP14 | Canonical source lookup missing at ingress | CANONICAL_SOURCE_UNAVAILABLE; no caller-source override | PG |
| CFP15 | Grounding returns INCOMPLETE | GROUNDING_INCOMPLETE and preserved issue codes; no projection | U/PG |
| CFP16 | Grounding returns REJECTED | GROUNDING_REJECTED; no projection | U/PG |
| CFP17 | Capture's fresh grounding identity differs from expected pin | EXPECTED_GROUNDING_MISMATCH; no silent substitution | PG |
| CFP18 | Valid grounding with non-error warning context | Retain/recompute full grounding_issues/context; tampered warning or missing issue rejected | U |
| CFP19 | Candidate request differs from outer request | Reject full request mismatch even where selected ingredient rows agree | U |
| CFP20 | Unauthenticated/unauthorized household actor | CAPTURE_ACCESS_DENIED; no source disclosure/write | PG |
| CFP21 | Different RecipeVersion in feature input | RECIPE_VERSION_MISMATCH before discovery | U |
| CFP22 | Same RecipeVersion ID, changed immutable payload across children | SOURCE_CUT_INCOHERENT even if hashes are independently recomputed | U |
| CFP23 | Wrong tier/rule/delta vector or METHOD-only child carrying path | PATH_MISMATCH; frozen METHOD versus path semantics preserved | U |
| CFP24 | Forged binding recipe/path/candidate identity | Validator recomputes binding and rejects edited result | U |
| CFP25 | Repeated immutable review/term identity with conflicting payload | Reject complete cut, not last-write-wins, including historical unused facts | U |
| CFP26 | Scope from different recipe or requested dimensions mismatched | Reject source/subject mismatch; no dimensional downgrade | U |
| CFP27 | Missing/extra term manifest or historical support stream | FEATURE_SOURCE_INVALID under frozen exact-manifest validation | U |
| CFP28 | Unsupported MAIN_PROTEIN ingredient/path or false support review | Frozen support validation rejects; no mass/title inference | U/PG |
| CFP29 | Overlapping active scope or invalid revision/command hash | Frozen source validation rejects whole subject | U/PG |
| CFP30 | Catalog association changes after pinned support publication | Preserve frozen STALE_ASSOCIATION, no replacement support inference | U/PG |
| CFP31 | No scope for requested dimension after successful source read | UNRESOLVED / NO_SOURCE, not source-read failure or zero | U/PG |
| CFP32 | Existing scopes but none match exact candidate | UNRESOLVED / NO_MATCHING_SCOPE | U |
| CFP33 | Matching COMPLETE review with no positive terms | REVIEWED_NONE within covered universe only | U/PG |
| CFP34 | Matching PARTIAL review with no positive terms | UNRESOLVED / PARTIAL_COVERAGE | U |
| CFP35 | Matching PARTIAL review with positive terms | ASSIGNED + PARTIAL; uncovered terms remain unresolved | U |
| CFP36 | Retracted review | Preserve RETRACTED diagnostic/references; not REVIEWED_NONE | U/PG |
| CFP37 | Failed Catalog/Recipes read or aborted transaction | CAPTURE_IO_FAILURE; no empty-sources substitution or partial dimensions | PG |
| CFP38 | Dirty/writable/READ COMMITTED capture session | CAPTURE_CONTEXT_INVALID; no writes/commit by adapter | PG |
| CFP39 | Concurrent source publication during RR capture | All reads/frontiers reflect one MVCC cut; no mixed live heads | PG |
| CFP40 | Different valid grounding as_of, feature captured_at and owner counters | Preserve distinct meanings; no forced timestamp/counter equality | U/PG |
| CFP41 | Review recorded after grounding as_of, before feature capture | Frozen 046A may use it; output explicitly retains two temporal meanings | U/PG |
| CFP42 | Future grounding as_of at canonical capture versus offline replay | Preserve Inventory capture's future-cutoff rejection; clock-free replay cannot certify future history/availability | U/PG |
| CFP43 | Review after feature capture, out-of-frontier sequence or bad outer interval | Reject incoherent cut; do not falsify child clocks | U |
| CFP44 | Valid retained cut replay after live heads move | Same offline result; no live refresh or claim of current authority | U/PG |
| CFP45 | Two independent, internally consistent offline cuts with no contradictory common facts | Pure validation cannot prove common MVCC/origin; canonical capture never accepts supplied cuts | U/B |
| CFP46 | Cached child discovery/grounding mutated relative to primitive inputs | Recompute/reject; never trust supplied cached output | U |
| CFP47 | Result positive terms/coverage/reason/witnesses edited then rehashed | Semantic validator rejects against fresh owner discovery | U |
| CFP48 | Tampered source/result fingerprint or omitted required provenance | Reject; unknown-field/shape and semantic validators both exercised | U |
| CFP49 | model_construct/model_copy or ordinary successful shape parsing | Public semantic validator still reparses/replays; no bypass authority | U |
| CFP50 | Same complete subject replayed repeatedly with I/O traps installed | Byte-identical result/fingerprint; zero DB/network/filesystem/clock calls | U/B |
| CFP51 | New capture clock/frontier/history change with same visible positives | Outer fingerprint changes; complete history/cut remains identity-bearing | U |
| CFP52 | Trigger-only change excluded by frozen culinary candidate hash | Full request/candidate retained; outer identity changes without altering frozen child algorithm | U |
| CFP53 | Equivalent aware time zone representation in new envelope | UTC canonical encoding; frozen child serializer semantics unchanged | U |
| CFP54 | Reordering ordinal child history or changing frozen Decimal representation | Obey frozen validation/identity; no generic list/amount normalization | U |
| CFP55 | Missing feature, numeric zero/default field or implicit eligibility flag attempted | No zero/neutral/eligible substitution or new result authority | U/B |
| CFP56 | METHOD/protein/flavor guess from title, mass, label or absent dimension | No inference/new classifier; only frozen discovery | U/B |
| CFP57 | Preference/EvidenceStrength/TasteFit/behavioral attribution requested | No API/field/import for these; MTR-040 unchanged, 039 independent | B |
| CFP58 | Novelty/repeat/utility/ranking/role/global history requested | No computation, dimension weights, aggregation or Learning dependency | B |
| CFP59 | Safety/feasibility/planner/Execution/PRECOMMIT authority attempted | False readiness literals; no issuer/integration; old child flags not promoted | U/B |
| CFP60 | Migration/persistence/data/export/frozen regression audit | No storage/seeds/0016; frozen 019B/C, 046A and proposal feature capture unchanged; existing CI retained, additive exports explicitly reviewed later | B/PG |

Implementation evidence must map every ID to actual tests, record baseline and additive counts,
verify boundary/import checks and run the existing full CI (Python/PostgreSQL, SCRAM/TLS, benchmark,
exports/schema/contracts, client/typecheck/build). No new test count or implementation freeze is
claimed by this design. Architecture review must approve the temporal, ingress and replay boundary
before implementation can be authorized.

## 16. Non-goals and remaining gates

This slice does not add classification publication or authority, a new review policy, variant-family
inference, refined/nonzero-adjustment candidates, arbitrary historical database capture, cross-target
aggregation, new hierarchy, inherited EvidenceStrength, materialized MemberBehaviorProfile,
behavioral events, new preference coordinates or member-affinity composition.

| Work | Status after this design PR, even if later merged |
| --- | --- |
| MTR-040 / issue #41 | COMPLETE / CLOSED — COMPLETED; frozen 040A/B/C, prior/compatibility and hierarchy sources unchanged |
| Candidate-bound feature projection | Design ready for architecture review only; implementation NOT AUTHORIZED; no MTR suffix assigned |
| MTR-039 | OPEN, independent attributed-event ingress/design still required; not supplied by 040 completion |
| Full MTR-041 | PARTIAL; 041A–F frozen proposal-local semantics, no global accepted/confirmed/cross-horizon history or novelty |
| Full MTR-046 | PARTIAL; frozen 046A reused, no new coverage facts or production taxonomy/policy published |
| MTR-024 | BLOCKED; this would supply one candidate feature input, not member join/TasteFit, policy composition or utility |
| MTR-020B | BLOCKED; no semantic/structural champion, scoring/selection policy or ranking implementation here |
| MTR-021 | BLOCKED; no jointly feasible portfolio, physical allocation or validated global replay delivered |
| Execution / PRECOMMIT | NOT STARTED / FAIL-CLOSED; no authority or planner activation |

The smallest proposed implementation boundary is these four types, three functions and their
acceptance tests, using existing owners. No missing source primitive was found for that boundary.
Publication policy, later member joins, diversity, global history and ranking each remain separate
review/authorization questions. Neither PR #110's merge nor approval of this design automatically
authorizes implementation or any downstream milestone. The design PR must remain open for review.

## 17. Design verdict

```text
CANDIDATE-BOUND REVIEWED CULINARY FEATURE PROJECTION
DESIGN READY FOR ARCHITECTURE REVIEW

IMPLEMENTATION NOT AUTHORIZED
```
