# MTR-019A — Explicit Culinary Binding Ownership

Base:33297e89f3db68e4695ae8659f01cb16cbf1504d. Architecture recorded before implementation.
Sources: ADR-005/009/010; INV-005/006/011–013/015–021; frozen MTR-016/MTR-025;
[approved dependency review](MTR_026_DEPENDENCY_REVIEW.md). No contradiction requires redesign.

## A–E. Ownership, lifecycle and history

A. Planning owns exact culinary intent. Household/PlanWorkspace → Proposal → planned batch
→ one binding header → requirement relationship rows. RecipeVersion owns authored truth.
PlanRevision references its immutable proposal, thus retains its exact binding forever.
B. No persisted arbitrary updates: assemble a proposal and binding atomically in one transaction.
Unsealed assembly is private to that transaction, not a separately editable committed draft.
C. Proposal seal closes child insertion; binding rows are append-only from insertion.
Correction creates a new proposal, never updates a prior binding.
D. Composite ownership FKs bind household/plan/proposal/batch. Header binds RecipeVersion/tier;
rows bind requirement/rule/transformation to that exact version, plus explicit resolved ingredient,
calculated quantity/basis/item_ref and authored adjustment delta. Header carries servings,
approved combination ID, schema version, provenance and full binding fingerprint.
E. New proposal copies unchanged intent into new owned rows. Old revision/proposal rows survive.

## F–I. Version, hashes and revision boundaries

F. Introduce separate typed `plan-intent.v3`, bound proposal/command/revision contracts.
Never widen the old v1/v2 graph or frozen validation subject. V3 adds relational bindings and
per-batch `culinary_signature`. Full fingerprint includes proposal ownership; semantic signature
excludes proposal_id/fingerprint only, so copying unchanged facts does not fabricate a revision
delta. Both retain household/plan/batch identity and provenance. Graph hash includes full bindings.
No positional arrays: one requirement record contains selected rule, resolved ingredient,
quantity, adjustment and transformation. Canonical sort by requirement ID; bindings by batch ID.
G. Batch signature is part of the graph batch representation. Existing old/new closure therefore
sees binding-only changes, including shared-batch consumers. SINGLE_MEAL cannot edit a batch
shared by two meals. Reservation target comparison also includes the signature.
H. Existing own-anchor cut-line checks see batch signature changes at planned_at. Forward SQL
also compares exact semantic binding signatures for batch materialization pins, including pinned
historical source proposals. Meal pins include full batch paths. Physical facts are never rewritten.
I. V1/v2 hashes and command fingerprints keep their existing encoder. Old SQL graph builder is
retained verbatim for legacy rows; v3 wrapper adds bindings. Existing proposals/revisions need no
data rewrite. Populated downgrade with v3 history fails closed. Forward migration0010 only.

## Independent enforcement / validation input

Producer uses the existing authored culinary resolver to assemble explicit intent, without search.
Validation uses a separate imperative implementation from RecipeVersion primitive facts, not that
resolver, GroundedRecipeVariantDraft or cached valid flags. It checks all authored policies, rule
ownership/combination, COUNT prohibition, exact quantities, servings, transformations and hashes.
DB seal independently validates relational completeness, authored resolution and money-free
numeric primitives. Calculated quantities persist exactly at72/36; no quantization or floats.

New immutable `culinary-validation-input.v1` captures exact v3 proposal plus sealed RecipeVersions
under read-only RR/SERIALIZABLE. It is a companion, not a mutation or production-ready successor
to frozen ValidationSubject v1. It is self-contained; validation performs zero queries/writes.
Reports remain non-authorizing PRECOMMIT/diagnostic POSTFACT. Existing authority guard stays shut.

## J. Deferred and counterexamples

Explicit selection is enough; no full MTR-019 demand-driven VariantGenerator is needed. No nutrition,
retail/procurement, physical allocations, MTR-023 execution/batch production, assumptions, bridge,
policy synthesis, optimizer, ranking or production authorization. Planning intent proves no cooking.
AP→EP remains Retail-owned; net EP_RAW→COOKED remains Recipe-owned. COUNT substitution forbidden.
Gram adjustment does not change servings. Different method requires different authored context.

Adversarial review: copied ownership must not cause all meals to change; binding-only edit of a
shared batch must close both meals; changing only a pinned binding must fail; default raw path
must survive a substitute-only transform; wrong ingredient/count/basis/rule cannot hide behind a
correct-looking fingerprint; direct SQL late insert/UPDATE/DELETE/TRUNCATE must fail. V1/v2 and
ValidationSubject v1 hash fixtures must remain unchanged. No new execution API or physical asset.
