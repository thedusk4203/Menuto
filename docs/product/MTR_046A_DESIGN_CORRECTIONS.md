# MTR-046A — Design correction record

Status: **DESIGN REVIEW PENDING; IMPLEMENTATION NOT AUTHORIZED; NOT FROZEN**.

Reviewed baseline: `4adc312879d647bb6a7b8dacf593704f8280dc51`, PR #83.
This documentation-only correction addresses the user's three required changes to the
[source design](MTR_046A_CULINARY_FEATURE_ASSIGNMENT_DESIGN.md). It does not reopen frozen
Recipe/Variant, Preferences or MTR-041A/B/C/D behavior.

| Finding | Corrected decision | Design sections | Required future implementation proof |
| --- | --- | --- | --- |
| METHOD incorrectly path-dependent | METHOD key is the exact RecipeVersion cooking context, without tier/slot/rule/adjustment selectors. Only FLAVOR/MAIN_PROTEIN use path keys. | 2, 3, 6, 7, 9 | Substitution, tier and micro-adjustment preserve METHOD identity; Pydantic and direct SQL reject METHOD path children. |
| Capture requires a known term before discovering assignments | Capture requests dimensions only and captures complete matching primitives. Pure discovery needs no term query; optional term resolution follows capture. | 4, 6, 9 | Discover positive terms without prior IDs; different queries reuse one subject identity; uncaptured term stays UNRESOLVED without IO. |
| Catalog association frontier unnecessarily fences METHOD/FLAVOR | Recipes frontier always applies. Catalog association generation, fence and pinned-head checks apply iff MAIN_PROTEIN is requested/written. | 6, 7, 8, 9 | Unrelated Catalog edits cannot stale METHOD/FLAVOR; MAIN_PROTEIN rejects stale Catalog support; conditional dependency manifests/hash inputs are enforced. |

## Canonical basis and adversarial reasoning

[ADR-005](../adr/ADR-005-grounded-recipe-variants.md) makes a cooking-method change a different
Recipe. Existing Recipe snapshots require each preparation transformation's method to equal the
Recipe cooking method. Therefore a tofu substitution, alternate tier or micro-adjustment cannot
change METHOD for that RecipeVersion under the same classification review. A later explicit
classification correction remains possible through append-only review history.

A future exposure consumer need not know which METHOD/FLAVOR/MAIN_PROTEIN labels exist in
order to discover them. A dimension-only capture includes positive assignments, finite covered
universes, coverage status and support/provenance. Post-capture queries cannot cause live reads
or prove absence for terms outside that captured manifest. METHOD-only capture resolves the
canonical RecipeVersion cooking context even when no exact path binding exists; requesting
FLAVOR or MAIN_PROTEIN additionally requires the frozen exact culinary binding.

An unrelated Ingredient→PROTEIN review cannot invalidate a METHOD or FLAVOR operation. Those
branches neither read/lock the association counter nor accept/hash an expected Catalog frontier.
MAIN_PROTEIN pins Catalog support and fences Catalog → Recipes. A mixed captured subject has
the union of its requested dependencies. Captured-at or proposal audit identity may change when
their own primitives change; that is distinct from making Catalog generation a false dependency.

## Preserved design and actual implementation state

Approved design elements remain: typed relational FKs; applicability independent from candidate
fingerprints; finite pinned term universes; missing assignment != absence; PARTIAL/COMPLETE
coverage; explicit co-main-protein support; immutable replacement/retraction lineage; CAS and
idempotency; declared counts/hash + assembly transaction + deferred closure; no extra seal tables.
Their implementation remains subject to real PostgreSQL adversarial proof.

The **13-table / prospective 71-table** decomposition and forward **0013** remain proposals.
Actual schema is **0012 / 58 domain tables**. This correction creates no migration, runtime
contract, ORM table, SQL function, export or test implementation. Migrations 0001–0012 and all
frozen runtime surfaces remain unchanged.

Full MTR-040/041/046 remain incomplete. MTR-024/020B/021 remain blocked. Execution has not
started and PRECOMMIT remains fail-closed. No next slice is started or authorized here.

## Verification evidence

Verification results below concern the unchanged repository and documentation consistency.
They cannot prove the proposed 0013 contracts, SQL closure or dimension-sensitive fences work.

- Local focused regression: **405 passed in 8.06s** across recent exposure, cooldown, decay,
  RepeatPenalty, explicit preferences, validation foundation/canonical review and architecture.
  Command: `.venv/Scripts/python.exe -m pytest` with those eight existing test modules,
  `--basetemp=.local/mtr-046a-correction-temp --junitxml=.local/mtr-046a-correction.xml`.
- Ruff, architecture baseline (30 invariants / 11 ADRs / 50 linked tasks), import boundaries
  (16 contexts), domain contract export and OpenAPI export checks: **PASS**.
- All **138 local Markdown links** in the seven changed documents resolve; documentation-only
  scope, `git diff --check`, metadata table count **58** and Alembic head **0012**: **PASS**.
- Diff against reviewed baseline in apps/packages/tools/.github and Alembic config: **empty**.
  No migrations, frozen algorithms/contracts, tests or exports were edited.
- PR/head and exact post-merge CI: recorded in the delivery report once completed.
- No local PostgreSQL run is claimed for this documentation-only correction.

**READY FOR MTR-046A ARCHITECTURE/DESIGN REVIEW**
