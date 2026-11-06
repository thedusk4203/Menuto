# Post-MBA dependency review — source-bound NutritionPolicy integration v2

**POST-MBA DEPENDENCY REVIEW — READY FOR INDEPENDENT ARCHITECTURE REVIEW / NO IMPLEMENTATION AUTHORIZED**

This is dependency analysis and preparation for a separately authorized detailed design.
It defines the questions and acceptance obligations for that design, not new executable
contracts, scientific policy, an implementation approval or a new structural freeze.

## 1. Canonical baseline and evidence

Reviewed repository: `thedusk4203/Menuto`; exact main
**`066125e3828fcf18384ea9aefacd1bf0503a9d9a`**. Main was re-fetched and matched the
authorized baseline. [PR #134](https://github.com/thedusk4203/Menuto/pull/134) is MERGED;
its exact-main **push** [CI 42252210550](https://github.com/thedusk4203/Menuto/actions/runs/42252210550)
is SUCCESS, including Python/web. [Docs-sync completion 6690609485](https://github.com/thedusk4203/Menuto/pull/134#issuecomment-6690609485)
does not replace the implementation freeze identity below. No canonical drift was found.

| Frozen capability | Canonical source / retained evidence |
|---|---|
| Nutrition Root | [Freeze receipt](NUTRITION_ROOT_CONTRACT_SUPPORTED_ELIGIBILITY_FREEZE_RECEIPT.md); implementation merge `6a77575fcb0ecf7a02493dae935fab88e94d09f1` |
| MTR-006 v1 structural synthesis | [Approved design](MTR_006_SOURCE_BOUND_NUTRITION_POLICY_SYNTHESIS_CONTAINMENT_DESIGN.md), [implementation evidence](MTR_006_SOURCE_BOUND_NUTRITION_POLICY_SYNTHESIS_CONTAINMENT_EVIDENCE.md), [independent PASS](https://github.com/thedusk4203/Menuto/pull/127#issuecomment-6648590537); implementation merge `45ed430ff3306939366bf82e232d02054475b360` |
| MTR-007 bounded estimator | [Design](MTR_007_SOURCE_BOUND_NUTRITION_RESOLUTION_ESTIMATOR_DESIGN.md), [evidence](MTR_007_SOURCE_BOUND_NUTRITION_RESOLUTION_ESTIMATOR_EVIDENCE.md), [freeze 6662354375](https://github.com/thedusk4203/Menuto/pull/130#issuecomment-6662354375); implementation merge `82b4a7c631acbc04ffbd522702bf3529d7e2e2d2` |
| MBA structural / TEST_ONLY | [Approved design](MEASUREMENT_BASIS_APPLICABILITY_INDEPENDENT_EVIDENCE_CONTAINMENT_DESIGN.md), [evidence](MEASUREMENT_BASIS_APPLICABILITY_INDEPENDENT_EVIDENCE_CONTAINMENT_EVIDENCE.md), [canonical freeze receipt](MEASUREMENT_BASIS_APPLICABILITY_INDEPENDENT_EVIDENCE_CONTAINMENT_FREEZE_RECEIPT.md), [formal freeze 6688245300](https://github.com/thedusk4203/Menuto/pull/133#issuecomment-6688245300) |

MBA remains frozen at implementation merge **`9d3b580ce2a2d111223b37814612a4072dbfe6a2`**,
tree **`3a68035f9c33de152b3899a083d534a537c647e1`**, reviewed head
`a22d3c37697f7ac7d73ed29acbaa1d0b26c50b49`. Its exact push
[CI 42230659936](https://github.com/thedusk4203/Menuto/actions/runs/42230659936) succeeded.
Later documentation commits are not substitute implementation identities.

The retained baseline is **4,183 tests /0 skips, 515 exported definitions, 503 historical
definition hashes and 53 frozen source/migration files; schema 0017 /108 domain tables**.
MBA001–MBA080 already have 136 executed additions, including 26 real PostgreSQL executions
covering 12 obligations. Those are historical MBA evidence, not v2 acceptance executions.
There is no0018 and no new persistence in MBA or this review.

Live parent issues [#5 / MTR-006](https://github.com/thedusk4203/Menuto/issues/5),
[#6 / MTR-007](https://github.com/thedusk4203/Menuto/issues/6) and
[#7 / MTR-008](https://github.com/thedusk4203/Menuto/issues/7) were re-read and remain OPEN.
Their namespace-only baseline wording predates the later bounded implementations. It is
partially stale capability description, not evidence that their full acceptance is complete.
No issue is changed or closed here.

## 2. Governing semantics and method

The owning sources are [Development Spec V1.3 §10.3–10.4](../MENUTO_DEVELOPMENT_SPEC_V1_3.md),
[ADR-002](../adr/ADR-002-nutrition-policy-engine.md),
[ADR-003](../adr/ADR-003-plan-policy-resolution.md),
[ADR-010](../adr/ADR-010-independent-validator.md), and
[INV-001–030](../ARCHITECTURE_INVARIANTS.md), especially INV-001/003/004/005/006 and015–020.
The prior [post-MTR-007 dependency review](POST_MTR_007_MEASUREMENT_BASIS_POLICY_V2_DEPENDENCY_REVIEW.md)
correctly placed measurement meaning before successful numeric integration. MBA now supplies
that boundary for original-source same-meaning **TEST_ONLY** cases. It does not supply a
production physiological measurement bridge.

The existing graph index was queried as a locator, then checked against actual current
source files. Its older Nutrition/Policy links are not proof of the newer MBA capability.
Repository source, retained immutable evidence and live GitHub receipts govern this review.
Readiness below is an architectural recommendation requiring independent review and separate
design authorization. A frozen adjacent primitive is not authorization to compose it.

## 3. Exact capability and dependency matrix

| Node / owner | What frozen code actually supplies | Genuinely missing / downstream dependency | Disposition |
|---|---|---|---|
| Nutrition Root / Nutrition sources; member owns observations/goals | Authenticated append-only publication, observation, eligibility, delegation and goal histories; coherent retained cut; pure root resolution and independent root checking | No production guideline/eligibility/qualification content is installed; root availability is not a complete policy or medical certification | FROZEN; reuse unchanged |
| Reviewed synthesis rules / dedicated Nutrition authority | Separate scoped review/publication, retained rule selection and exact finite language; [source capture](../../apps/backend/app/modules/nutrition/synthesis_sources.py) freshly captures/rederives the root on the same connection | No rules are authorized merely by v2 transport or matching hashes; production rule content remains absent/unapproved | FROZEN structural authority; reuse unchanged |
| MTR-006 v1 / Nutrition producer | [Synthesis](../../apps/backend/app/modules/nutrition/synthesis.py) separates hard, goal, comfort, temporal and precision claims; exact containment and source-bound rule replay | Its resolution seam accepts `TEST_ONLY_RESOLUTION_FIXTURE_V1` / `TEST_ONLY_fixture_v1`, not canonical NRE/MBA. A gap cannot be recast as its `portion_step` | FROZEN; new versioned consumer needed |
| MTR-007 / Nutrition; owner reads coordinated by Planning | [Contracts](../../apps/backend/app/modules/nutrition/resolution_contracts.py), [capture](../../apps/backend/app/modules/planning/nutrition_resolution_capture.py): complete declared finite recipe/tier/rule/reference scope, joint period vectors, configuration witnesses and exact gaps; one ordinary reader/cut | Planned ingredient input and `WHOLE_TIER_TO_SINGLE_TRACKED_MEMBER_V1` establish offered-food attribution only. No consumption or physiological equivalence | FROZEN TEST_ONLY; reuse retained primitives |
| MBA / Nutrition; Planning capture | [Projection](../../apps/backend/app/modules/nutrition/basis_projection.py) includes required root/derived/goal/hard/comfort/weekly anchors. [Capture](../../apps/backend/app/modules/planning/basis_capture.py) binds the private issued fixture context and canonical NRE cut; [replay](../../apps/backend/app/modules/nutrition/basis_applicability.py) proves same original-source planned-input meaning | Registry authority is a privileged in-memory TEST_ONLY harness, not a durable scientific publication service or hostile-Python ingress boundary. No clinical transform | STRUCTURALLY FROZEN / TEST_ONLY |
| Independent Validation / Validation | Separate [root checker](../../apps/backend/app/modules/validation/nutrition_roots.py), [v1 policy checker](../../apps/backend/app/modules/validation/nutrition_policy.py), [NRE checker](../../apps/backend/app/modules/validation/nutrition_resolution.py) and [MBA checker](../../apps/backend/app/modules/validation/basis_applicability.py) reconstruct retained semantics | No independently reconstructed integrated **v2 policy** exists. A consistent unavailable child is not a positive applicable child; fresh child and parent decisions are both required | Additive v2 verifier design READY |
| Explicit NutritionPrecision / Policy semantics, authenticated planning intent | [Selection](../../apps/backend/app/modules/nutrition/synthesis_contracts.py) pins value, `REQUEST_EXPLICIT`, version, actor, subject and evidence. Frozen capture retains DB-observed membership; v1 and NRE checkers reconstruct that witness | v2 must pin the exact same authorized selection through requirements, NRE, MBA and policy. Full default/week/request precedence is absent; a bare enum/hash is insufficient | Explicit-only seam can be designed upstream of full MTR-008 |
| MTR-006 v2 / future Nutrition producer + Validation consumer boundary | Required children now exist for bounded same-meaning TEST_ONLY composition | Versioned integration input/result, admission, joint-witness predicates, temporal/precision identity and independent full policy reconstruction are not implemented | **READY FOR DETAILED DESIGN**, not implementation |
| MTR-008 / Policy | [Current Policy contract](../../apps/backend/app/modules/policy/contracts.py) is `FOUNDATION_NO_CLINICAL_POLICY`; [request draft](../../apps/backend/app/domain/snapshots.py) carries orthogonal axes | Actual defaults/overrides/precedence, cost/effort/budget compilation and versioned ResolvedPlanPolicy remain missing; compiler must consume independently checked policy, not publish Nutrition truth | DEFERRED downstream; not complete |
| Production scientific/content/qualification authority / separately reviewed source owners | Structural enrollment/history can represent authority; TEST_ONLY evidence is explicitly non-scientific | Independently approved numerical content, population/protocol applicability, qualified actors, original measurement meaning and any transform-specific science are unavailable/not authorized | **BLOCKED; production gate CLOSED** |

### Precision ownership is an upstream input, not a dependency cycle

The existing `NutritionPrecisionSelection` is declared in a Nutrition transport but represents
Policy-owned planning intent. Its current source is only `REQUEST_EXPLICIT`; the frozen
PostgreSQL capture in `0017_nutrition_synthesis_sources.py` checks the exact actor, member
subject and household OWNER/EDITOR membership and retains `precision_witness`. The independent
v1 checker reconstructs that binding (`nutrition_policy.py`, precision authorization); the
NRE authority checker also checks it. This is planning-intent authority, **not** member-goal
representative authority or guideline authorship.

Thus a bounded explicit-only TEST_ONLY v2 design need not wait for full MTR-008. It must prove
how it reuses this authenticated source identity without letting Nutrition select a default.
Defaults, week context, request override precedence and any newly required actor path remain
separate Policy work. Missing or contradictory selection yields non-success, never STANDARD.
This review does not authorize a new precision journal or silently broaden the existing actor
permissions. If the later design cannot retain the existing witness, it must report that source
gap before implementation rather than minting a selection from request metadata.

## 4. Acyclic dependency DAG and shortest structural path

```text
Frozen Root authority + frozen reviewed synthesis-rule authority
             + Policy-owned explicit precision source/witness
                              |
                 pre-policy RequirementSpec + exact scope
                              |
Catalog / Recipes / Household primitive owner facts
                              |
       one canonical read-only NRE capture -> retained NRE primitives
                              |
     fresh independent NRE reconstruction (not a supplied report)
                              |
original root/rule measurement preimages + TEST_ONLY registry authority
                              |
     complete pre-policy MBA anchors + fresh independent MBA replay
                              |
     [future additive MTR-006 v2 source/admission boundary]
                              |
     source-bound policy synthesis + independent v2 reconstruction
                              |
     future MTR-008 ResolvedPlanPolicy / bounded preview pipeline
```

Production scientific content/qualifications/measurement evidence are a **separate closed
admission gate**, not a hidden default edge that TEST_ONLY may satisfy. Policy precision
selection precedes Nutrition; the downstream ResolvedPlanPolicy compiler does not supply its
own already-synthesized policy as an upstream requirement. Requirement and MBA anchor projection
must use retained root/rule/request primitives, not require a completed v2 policy. The final
checker then verifies the resulting claims against that independently reconstructed coverage.
No producer-to-validator-to-producer authorization loop is permitted.

The arrows describe Planning/consumer orchestration and evidence dependencies, not Nutrition
imports of Validation or a transferable validator attestation fed into the producer. Nutrition
must retain its independent producer boundary; the Validation-owned consumer freshly checks
children and the complete claimed policy. Frozen `NutritionPolicyRequirementSpec` projects
resolution requirements for COMFORT measurements; it is not a complete all-layer safety
manifest. MBA's separately reconstructed complete anchor manifest covers the additional
root/hard/goal/weekly branches. A v2 design must bind both without redefining either frozen
projection or treating the comfort-only projection as full safety coverage.

The shortest credible engineering path is: **review this recommendation → separately authorize
bounded v2 detailed design → independent architecture review → separately authorize implementation
and verification → later MTR-008 design**. This reaches a checked structural policy handoff;
it does not itself reach a production validated preview, solver feasibility or activation.

## 5. Competing next gates

| Candidate | Frozen prerequisites / missing seam | Value and decision |
|---|---|---|
| **MTR-006 Policy Integration v2 — Bounded Detailed Design (STRUCTURAL / TEST_ONLY)** | Root, rule authority, canonical NRE and MBA children exist; explicit precision witness exists. Missing composition/admission and independent policy semantics are exactly the design subject | **SELECTED.** Terminates the currently disconnected evidence chain at a source-bound NutritionPolicy contract; materially advances the Policy/preview path without scientific invention |
| Full MTR-008 first | Some input carriers exist, but no integrated verified canonical-resolution policy; full orthogonal defaults/override sources and compiler are separate | DEFERRED. Doing the downstream compiler first cannot manufacture the missing Nutrition result. Explicit upstream precision remains a required input, not deferred wholesale |
| New production measurement/scientific authority or clinical bridge | Structural journals are not scientific evidence; MBA only proves original same-meaning synthetic cases | BLOCKED for production. Essential before any production-positive route, but neither authorized nor necessary to study bounded TEST_ONLY integration |
| Another NRE/MBA wrapper or generic compatibility coordinate | Frozen terminal primitives already expose retained evidence and independent checkers | NOT NEXT. No discovered incompatibility requires an extra abstraction. Design the final Nutrition policy consumer/checker boundary instead |
| Complete MTR-007 / source expansion / serving-allocation engine | Current bounded estimator is useful; consumption/shared allocation and broader populations remain absent | DEFERRED. The selected design can stay inside the frozen single-tracked-member offered-food scope; no requirement proves full serving allocation must precede it |
| Solver, MTR-020B/021/024, preview API or activation | Additional policy, economics/flow, validation-subject and orchestration work remains | OUT OF SCOPE here; no readiness or implementation authorization inferred |

No frozen incompatibility was found. The gap is a missing additive composition contract and
consumer validation, not a defect requiring reinterpretation of frozen children.

## 6. Exact boundary the selected detailed design must settle

These are constraints and open design obligations, not approved new contract definitions.

### 6.1 Trusted capture versus retained semantic consistency

A v2 consumer must receive the retained primitive sources from the actual trusted capture
path and freshly invoke Validation-owned NRE and MBA reconstruction. Deserialized source
frames, correct hashes, fabricated `CONSISTENT` reports or `UNVERIFIED_TRANSPORT` carriers
alone cannot prove canonical origin or authorize numeric admission. The design must specify
the trusted in-process admission/capture association and replay-only interface separately;
a caller-writable receipt or boolean cannot establish that trust.

Historical replay can establish consistency of retained evidence without claiming current
authorization, present publication or scientific correctness. A fresh operational admission
requires fresh capture and current applicable authorization; an old retained success cannot
be promoted to present permission. Pure producer/checkers perform no I/O, wall-clock lookup
or environment-selected content lookup. Planning owns capture/orchestration, Nutrition owns
policy derivation, Validation owns independent admission and correctness checking.

Reuse the NRE one-reader read-only coherent cut for root/rule, Catalog, Recipes and Household
facts. MBA's registry is pinned before/after that capture, **not shared PostgreSQL MVCC**.
Bind its actual registry revision/epoch/database/reader/actor and reject changes or revoked
issued context during capture. Do not compose independently collected favorable child cuts,
or assume their matching subject/fingerprint proves a common source cut.

### 6.2 Measurement and scope must precede numeric comparison

Retain exact original root/rule source-authored measurement preimages, all required pre-policy
anchors, metric, unit, material basis, member/household, period/calendar, rule/publication,
eligibility/observation/goal versions and declared candidate universe. Equality of nutrient
name/unit or a new wrapper label cannot turn ingredient input into physiological intake.
The positive structural case is only independently reconstructed original-source same-meaning
planned input with complete TEST_ONLY evidence. Offered food is not consumed food.

Neither MBA nor v2 may create a conversion, retention factor, population definition, clinical
identity relation or default opposite bound. Unsupported/incomparable meaning fails closed
before arithmetic. Exact original-source meaning also applies to derived goal, hard, comfort
and weekly claims; checking only visible roots is incomplete coverage.

Frozen child literals, including `policy_integration=NOT_AUTHORIZED`, remain unchanged. A later
separately approved v2 companion can define its own bounded consumer permission; it cannot
flip those literals, call them proof of authorization, cast NRE as a v1 fixture or claim that
this review has already authorized integration.

### 6.3 Full resolution evidence, not a scalar surrogate

Retain complete joint nutrient vectors, exact configuration/slot witnesses, period membership,
finite-domain completeness and associated gaps. Maximum gap, minimum gap, marginal extrema
or GCD-like summaries do not establish reachable values, common nutrient support or joint
day/week configurations. The design must define the exact finite predicates by which a
policy uses these witnesses, including any resolution-insufficiency diagnosis. It must not
replace v1's `expected_step` with `maximum_gap` or create a new adapter solely for that cast.

Checking each nutrient/day separately must not invent a joint combination that no retained
configuration can realize. Weekly projections must retain linkage to the same daily choices;
no Cartesian mixing of incompatible configurations. The design must distinguish policy
coverage, resolution support and eventual solver feasibility: finite NRE evidence does not
prove feasibility outside the complete declared universe or perform a planner solve.

### 6.4 Hard, goal, comfort, weekly and precision semantics

Preserve the frozen guideline roots verbatim as hard conjuncts; independently reconstruct
any reviewed derived hard/goal protection. Explicit RANGE/MINIMUM/MAXIMUM/TARGET semantics
remain distinct. TARGET is a reference center, not an inferred interval. Missing opposite
bounds remain missing; exact matching descriptors are required before containment arithmetic.

Daily protection needs explicit daily authority even when a weekly source exists. Required
weekly goal protection remains a separate hard conjunction; weekly centering/comfort are
separately typed soft semantics. A weekly total cannot excuse a daily hard violation, and
a valid day-by-day marginal projection does not prove a common valid weekly choice. Preserve
the original aggregate root; do not demand every soft comfort combination be feasible.
No implicit daily↔weekly conversion, calendar stitching or cross-publication horizon assembly.

Goal direction must remain bound to the exact member-authored goal and reviewed rule/reference;
absence/retraction cannot become MAINTAIN or revive an older goal. Precision may select only
the reviewed nested comfort cases. Cost, budget, effort, convenience and TasteFit cannot weaken
hard/goal protection. Resolution insufficiency cannot silently widen it.

The design must type and independently check: missing/incomparable source, unauthorized source,
insufficient resolution, policy hard conflict and soft comfort violation. None is automatically
solver-proven infeasibility. A consistent negative child must not release a usable positive
policy or favorable partial witnesses. A soft violation does not become a hard physiological
conflict merely to simplify statuses; the exact result/diagnostic split remains a design task.

### 6.5 Independent v2 policy verification and terminal handoff

Calling the existing child checkers is necessary but insufficient: the new Validation-owned
companion must independently reconstruct **the integrated policy**, rule evaluation, selected
precision, complete claim coverage, temporal identity, exact witness use and containment.
It may reuse immutable contracts/primitive arithmetic and independently owned child checkers;
it must not call Nutrition's producer evaluator, accept cached producer claims or use the v1
checker as an oracle for v2 semantics. Preserve the R-127-01 consumer-boundary protection
and MBA-R133-01 publication-time authority checks, including immutable-prefix replay.

Final transport remains non-authoritative on serialization. A future MTR-008 consumer needs
fresh independent v2 checking and its own authorized input admission; report labels cannot
be reusable attestations. Validation success here is retained policy semantic consistency,
not scientific certification, whole-plan validation, activation or PRECOMMIT permission.

## 7. Readiness, source gaps and persistence

| Classification | Exact scope |
|---|---|
| **READY for detailed design** | Additive TEST_ONLY explicit-precision v2 capture/admission/result seam, exact NRE/MBA composition, independently reconstructed policy semantics, terminal Policy handoff and acceptance specification |
| **Missing engineering contracts to settle in that design** | Trusted-capture association versus replay-only admission; versioned integrated input/output and Validation coverage; exact finite joint-witness predicates; full temporal/precision pins; deterministic result states; bounded resource/accounting ownership |
| **BLOCKED pending source/authority evidence** | Any production-positive nutrition policy; clinically meaningful conversion/equivalence; production numerical rules, population/protocol content, qualification evidence, approved publishers/assessors and production precision pathways beyond proven scope |
| **DEFERRED to MTR-008 / later gates** | Defaults/week/request override precedence, full ResolvedPlanPolicy orthogonal compilation, full planner feasibility/optimization, validation subject and product/API integration |
| **OUT OF SCOPE** | New serving allocation/consumption, clinical conversion engine, solver, source expansion, production publication, new persistence, parent completion/closure, execution and activation |

No engineering evidence currently requires a new table, privilege or migration for a pure
TEST_ONLY integration companion. Expected strategy: retain frozen durable Root/rule authority,
existing owner reads and private fixture registry, with additive immutable derived contracts.
This is a design expectation, not advance approval of zero-persistence implementation or a
new authority model. If the detailed design needs durable basis authority, broader grants,
changed frozen files or a new actor model, that is a separate authorization gate. No0018 is
reserved. Production content authority remains blocked regardless of persistence choice.

TEST_ONLY taint must follow every input, rule, source artifact, estimate, applicability witness,
claim, validation result and handoff. Mixed environments or attempts to strip taint must fail
closed. Structural positives are synthetic same-meaning examples only; no production-positive
path, qualified production actors, numerical defaults or scientific content are designed here.

## 8. Acceptance proposal for the future bounded design

The following **PIV-D01–PIV-D32 are proposed design acceptance families**, not registered
contracts, executed tests or implementation authorization. Detailed design must expand them
into an explicit producer/checker/admission matrix with exact expected results and evidence.

| ID | Required proof / adversarial pair |
|---|---|
| PIV-D01 | Complete synthetic same-meaning positive path; every retained child and integrated claim independently reconstructed |
| PIV-D02 | Actual capture association admitted; fully rehashed caller-fabricated capture/frame remains untrusted |
| PIV-D03 | Forged NRE CONSISTENT report and matching public fingerprints cannot bypass fresh child reconstruction |
| PIV-D04 | Forged MBA APPLICABLE/CONSISTENT reports and fully rehashed witnesses cannot bypass authority/meaning replay |
| PIV-D05 | Forged positive final policy/report with matching pins rejected at fresh consumer checking |
| PIV-D06 | Correct negative child report does not imply positive availability/applicability or release usable partial policy |
| PIV-D07 | Exact root/rule/requirement identity preserved; modified/missing mandatory anchors rejected |
| PIV-D08 | Original source-authored meaning required for every root and derived claim; downstream label cannot supply it |
| PIV-D09 | Planned input/offered food/consumption/physiological mismatch fails before arithmetic; no implicit conversion |
| PIV-D10 | Metric/unit/material basis/member/household mismatch, unsupported descriptor or missing opposite bound fails closed |
| PIV-D11 | Exact complete declared recipe/tier/rule/reference/slot universe; missing or favorable-only child rows rejected |
| PIV-D12 | Full joint nutrient configurations reconstructed; individually attainable marginals cannot manufacture a common witness |
| PIV-D13 | Maximum/minimum gap or extrema substituted for exact reachability rejected; singleton has no adjacent gap, not a zero step; band-boundary equality and equal-vector multiple witnesses retained |
| PIV-D14 | Daily/weekly witnesses share actual configurations; incompatible day combinations cannot become a weekly witness |
| PIV-D15 | Every applicable hard root retained unchanged; RANGE/MINIMUM/MAXIMUM/TARGET and exact containment checked separately |
| PIV-D16 | Exact current member goal/reference/direction; absent/retracted/ambiguous goal cannot become MAINTAIN or old-goal fallback |
| PIV-D17 | Explicit daily protection authority required; weekly coverage cannot excuse daily hard violation |
| PIV-D18 | Weekly protected goal conjunct versus soft centering/comfort remains distinct; aggregate root is not dropped |
| PIV-D19 | Precision exact source/version/actor/subject/evidence/membership witness; enum or source-label forgery rejected |
| PIV-D20 | Same precision pin through pre-policy requirements, NRE, MBA and result; no hidden default or full-MTR-008 precedence |
| PIV-D21 | Reviewed nested comfort cases; precision/cost/budget/effort/TasteFit cannot weaken hard/goal roots |
| PIV-D22 | Resolution insufficiency, soft violation, policy conflict, source non-success and solver infeasibility remain distinct |
| PIV-D23 | Root/rule/registry valid time and recorded-prefix order; exact publication/provider/revision selection, no latest fallback |
| PIV-D24 | Expired reviewer/publisher qualification/grant at publication and complete effective coverage independently checked; later renewal cannot repair old unauthorized publication |
| PIV-D25 | Retraction/withdrawal/supersession, prospective transition and historical replay preserve cut knowledge; no current-authority claim from old retained success |
| PIV-D26 | Single coherent reader/cut plus before/after registry pin; mixed cuts or registry change cannot yield partial success |
| PIV-D27 | Temporal calendar/horizon/period/version mismatch or unsupported stitching rejected without daily/weekly conversion |
| PIV-D28 | TEST_ONLY taint propagated; mixed environment, retagging or production-admission attempt rejected |
| PIV-D29 | Validation imports no producer business evaluator; primitive mutation changes independently reconstructed policy even after rehashing |
| PIV-D30 | Server-owned bytes/integer/depth/cardinality/work/time ceilings and combined child budgets; overflow all-or-error, no truncation |
| PIV-D31 | All515 exports,503 historical hashes,53 frozen files,4183 baseline tests and0017/108 retained; old v1 fixture behavior/literals unchanged |
| PIV-D32 | No production values/authority/seed/default, no persistence/privilege widening, no MTR-008/solver/activation/PRECOMMIT authority |

**Real PostgreSQL proposals, only where source truth is exercised:** PIV-D02/11/19/26 require
end-to-end checks of the actual ordinary reader and full capture composition, precision
membership, exact owner rows and coherent snapshot. Negative controls should cover wrong
principal/database, unsafe transaction, missing row, mixed snapshot and rejected registry
advance around capture. Fresh-install/schema/privilege compatibility in PIV-D31/32 must run
against the migrated database. Pure rule/joint-set/containment/retained-history and report-forgery
checks are not made stronger merely by attaching a database fixture.

No new mandatory PG count is reserved here. Detailed design must justify the minimal actual
PostgreSQL obligations and distinguish executed integration from pure retained replay, reusing
frozen suites without claiming those suites already prove the new composition. Registry
grant/qualification replay is in-memory TEST_ONLY authority; do not call it newly protected
PostgreSQL publication authority. No PG privilege expansion is authorized for testing convenience.

## 9. Verification inventory and unchanged status

Inspected: the Development Spec/ADRs/invariants above; BACKLOG, FOUNDATION_STATUS, both
implementation blueprints; prior post-Root/post-MTR-006/post-MTR-007 reviews; Root/NPS/NRE/MBA
design, evidence and freeze records; current Root/synthesis/resolution/basis contracts and
producers; Planning NRE/MBA capture and private host; independent Validation companions;
Policy coverage/request carriers; migration0017 capture; MBA acceptance/compatibility fixture;
current CI workflow; live issues #5/#6/#7 and PR133/134 receipts.

This PR changes only this review and minimal tracking notices. Verification requires docs-only
diff/links, architecture/import checks, unchanged export/OpenAPI/fixture guards and exact-head
Foundation checks, including the full **4,183-test /0-skip** baseline, real PostgreSQL suites,
SCRAM/TLS16/16, benchmark22/22, client10/10, Python/web/typecheck/build. New v2 acceptance
families are not tests in this PR. Actual PR/head/run results belong to the PR verification
receipt; the baseline evidence above is not substituted for that new run.

Current status remains: Nutrition Root, MTR-006 v1, MTR-007 bounded estimator and MBA structural
foundations **FROZEN**; full MTR-006/007/008 **INCOMPLETE**, parent issues OPEN. MTR-040 remains
COMPLETE; MTR-039 OPEN; full MTR-041/046 PARTIAL; MTR-020B/021/024 BLOCKED.
**PRODUCTION NUTRITION/CLINICAL CONTENT GATE CLOSED**; `planner_ready=False`;
`activation_ready=False`; Execution NOT STARTED; PRECOMMIT FAIL-CLOSED.

## 10. Recommended next gate and authorization boundary

```text
NEXT RECOMMENDED GATE: MTR-006 Policy Integration v2 — Bounded Detailed Design (STRUCTURAL / TEST_ONLY)

STATUS: READY FOR DETAILED DESIGN
```

The structural children now exist; the remaining immediate engineering gap is their final
source-bound policy composition and independent policy verification. Production scientific
authority is still blocked and is not a prerequisite for **designing** this narrowly isolated
synthetic path. This recommendation does not declare production numeric integration ready.

**No detailed design is started by this document.** Independent architecture review and separate
design authorization must precede that work; implementation requires a later separate approval.
No runtime/contracts/tests/tooling/CI/migration/data changes, production content/qualifications,
scientific coefficients, serving engine, MTR-008 implementation, solver, issue closure or
downstream activation are authorized. Leave this review PR OPEN, auto-merge OFF; no self-approval.
