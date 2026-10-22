# Graph Report - v13-baseline  (2026-10-22)

## Corpus Check
- 109 files · ~36,962 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 484 nodes · 886 edges · 41 communities (19 shown, 22 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 75 edges (avg confidence: 0.88)
- Token cost: UNKNOWN (actual agent input/output usage was not exposed; zero placeholders are not measured usage).

## Graph Freshness
- Built from commit: `536785af`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Before future Graphify invocations set GRAPHIFY_NO_AUTO_REFRESH=1. Structural extraction is local; changed-document semantic extraction may consume model tokens and any associated provider cost.

## Community Hubs (Navigation)
- Synthetic Solver and Audit
- Accepted Architecture Contracts
- Web Dependency Toolchain
- Architecture Boundary Tests
- Baseline Gates and Delivery
- Client Code Generation
- Web TypeScript Configuration
- Root Workspace Commands
- Health API and Tests
- Independent Validation Contracts
- Client TypeScript Configuration
- Attributed Behavioral Learning
- Planner Policy and Nutrition
- Shared Household Planning Seams
- Canonical Baseline Checker
- Confirmed Physical Execution
- Reversible Operational Assumptions
- Batch Material Conservation
- Validation Namespace Boundary
- Unresolved Menuto Reference

## God Nodes (most connected - your core abstractions)
1. `Menuto V1.3 Closed-Loop Canonical Architecture Baseline` - 42 edges
2. `Thirty canonical V1.3 architecture invariants` - 33 edges
3. `Per-invariant scaffold micro-model and missing production evidence` - 31 edges
4. `Scenario` - 29 edges
5. `SolveConfig` - 27 edges
6. `V1.3 closed-loop architecture and 16 namespace contracts` - 27 edges
7. `SyntheticCpSatAdapter` - 23 edges
8. `ADR-011: Attribution-Routed Behavioral Learning, Recent Exposure & Bounded Exploration [accepted architecture]` - 17 edges
9. `ADR-010: Independent Semantic Validator, Primitive Recomputation & Chronological Replay [accepted architecture]` - 16 edges
10. `SolveResult` - 15 edges

## Surprising Connections (you probably didn't know these)
- `test_relative_import_in_package_is_resolved()` --calls--> `check_source()`  [INFERRED]
  apps/backend/tests/test_architecture.py → tools/check_import_boundaries.py
- `main()` --calls--> `create_app()`  [EXTRACTED]
  tools/export_openapi.py → apps/backend/app/main.py
- `Unprovisioned persistence and infrastructure boundary` --references--> `Canonical V1.3 MTR-001 through MTR-050 backlog`  [EXTRACTED]
  infra/README.md → docs/product/BACKLOG.md
- `test_checker_catches_real_dependency_violations()` --calls--> `check_source()`  [INFERRED]
  apps/backend/tests/test_architecture.py → tools/check_import_boundaries.py
- `test_checker_allows_public_interfaces_and_same_context_internals()` --calls--> `check_source()`  [INFERRED]
  apps/backend/tests/test_architecture.py → tools/check_import_boundaries.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Specified execution truth views** — docs_adr_adr_009_execution_state_machine_activeplan_revision_contract, docs_adr_adr_009_execution_state_machine_three_state_views, docs_adr_adr_009_execution_state_machine_physical_food_lifecycle, docs_adr_adr_009_execution_state_machine_reversible_assumption_graph [EXTRACTED 1.00]
- **Specified semantic arithmetic and chronological validation** — docs_adr_adr_010_independent_validator_root_contract_validation, docs_adr_adr_010_independent_validator_primitive_recomputation, docs_adr_adr_010_independent_validator_chronological_replay, docs_adr_adr_010_independent_validator_validation_modes [EXTRACTED 1.00]
- **Specified attribution-routed bounded learning** — docs_adr_adr_011_behavioral_learning_loop_signal_attribution_router, docs_adr_adr_011_behavioral_learning_loop_member_behavior_profile, docs_adr_adr_011_behavioral_learning_loop_recent_exposure_model, docs_adr_adr_011_behavioral_learning_loop_separable_behavior_vector, docs_adr_adr_011_behavioral_learning_loop_bounded_exploration [EXTRACTED 1.00]
- **Specified canonical closed-loop handoff** — docs_menuto_development_spec_v1_3_planpolicyresolver, docs_menuto_development_spec_v1_3_planner_v4, docs_menuto_development_spec_v1_3_validator, docs_menuto_development_spec_v1_3_activeplan, docs_menuto_development_spec_v1_3_attribution_router [EXTRACTED 1.00]
- **Three independent correctness evaluation layers** — docs_menuto_development_spec_v1_3_root_contract_guards, docs_menuto_development_spec_v1_3_primitive_recomputation, docs_menuto_development_spec_v1_3_conservation_replay [EXTRACTED 1.00]

## Communities (41 total, 22 thin omitted)

### Community 0 - "Synthetic Solver and Audit"
Cohesion: 0.07
Nodes (41): audit_solution_data(), purchasable(), SyntheticCpSatAdapter, capture(), BenchmarkAdapter, solve_reference(), main(), run_case() (+33 more)

### Community 1 - "Accepted Architecture Contracts"
Cohesion: 0.08
Nodes (45): ADR-001 — Band-First Planner Architecture [accepted architecture], ADR-002 — Nutrition Policy Engine [accepted architecture], ADR-003 — Orthogonal Plan Policy Resolution [accepted architecture], ADR-004 — Household-First Data, Single Tracked Nutrition Member in V1 [accepted architecture], ADR-005 — Authored Recipe Flexibility and Pre-Solve Grounding [accepted architecture], ADR-006 — Retail Evidence and Procurement Abstraction [accepted architecture], ADR-007 — `SPEND_LIMIT` and Deterministic Robust Budget Scenarios [accepted architecture], ADR-008 — No Silent Relaxation and Verified Alternatives [accepted architecture] (+37 more)

### Community 2 - "Web Dependency Toolchain"
Cohesion: 0.05
Nodes (35): dependencies, @menuto/api-client, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript (+27 more)

### Community 3 - "Architecture Boundary Tests"
Cohesion: 0.07
Nodes (14): test_checker_allows_public_interfaces_and_same_context_internals(), test_checker_catches_real_dependency_violations(), test_relative_import_in_package_is_resolved(), test_v13_independence_cannot_use_solver_facade_or_contract_backdoor(), test_v13_independent_contracts_and_orchestration_imports_are_allowed(), derive_tags(), check_source(), check_tree() (+6 more)

### Community 4 - "Baseline Gates and Delivery"
Cohesion: 0.07
Nodes (37): Architecture baseline consistency check in CI, Foundation CI with V1.3 baseline consistency gate, Architecture dependency import checks in CI, Member-attributed signals exclude passive and forced preference contamination, Behavioral learning namespace without engine or profile store, No learning router profile store or production engine yet, FastAPI foundation with sixteen domain namespaces, Health response is process liveness with planner_ready false (+29 more)

### Community 5 - "Client Code Generation"
Cohesion: 0.06
Nodes (30): ajv, auditReferences(), check, document, generated, healthName, rewrite(), runtime (+22 more)

### Community 6 - "Web TypeScript Configuration"
Cohesion: 0.14
Nodes (13): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, noEmit, resolveJsonModule (+5 more)

### Community 7 - "Root Workspace Commands"
Cohesion: 0.15
Nodes (12): engines, node, name, private, scripts, build:web, contracts:check, contracts:generate (+4 more)

### Community 8 - "Health API and Tests"
Cohesion: 0.21
Nodes (3): create_app(), health(), HealthResponse

### Community 9 - "Independent Validation Contracts"
Cohesion: 0.23
Nodes (12): Assistant: intent and explanation outside trusted truth, Validation: independent semantic arithmetic temporal checks, Immutable PlanRevisionSnapshot history preserves materialized past, Milestone 0/1 entry requires frozen contracts bases snapshots and dependency checks, Explicit AP EP_RAW COOKED_G SERVING money and discrete bases, Required neutral benchmark and validator mutation fixture formats, PRECOMMIT gates intent with zero FATAL ERROR and matching hashes, Primitive nutrition procurement yield and safety recomputation (+4 more)

### Community 10 - "Client TypeScript Configuration"
Cohesion: 0.17
Nodes (11): compilerOptions, esModuleInterop, lib, module, moduleResolution, noEmit, resolveJsonModule, skipLibCheck (+3 more)

### Community 11 - "Attributed Behavioral Learning"
Cohesion: 0.24
Nodes (11): EvidenceClassifier and SignalAttributionRouter separate signal meaning, Separable behavioral dimensions composed only in versioned planner utility, Versioned EXPLOIT STRUCTURAL_CHAMPION EXPLORE portfolio policy, Learning: attributed multi-signal behavioral loop, Preferences: declared and member-owned affinity, FORCED_CONFLICT_RESOLUTION quarantined from voluntary preference learning, HorizonBridgeResolver chronologically honors future commitments, Thirty V1.3 invariants supersede V1.2 numbering (+3 more)

### Community 12 - "Planner Policy and Nutrition"
Cohesion: 0.20
Nodes (10): Stage 0 hard feasibility Stage 1 comfort economics Stage 2 human utility, Specified Policy Planner Validator Execution Learning closed loop, Nutrition: member physiology and policies, Planning: grounded candidates plans and orchestration, Policy: orthogonal resolved plan contracts, Recipes: authored versioned culinary flexibility, Authored immutable grounded recipe candidates, Guideline Goal Resolution Temporal Precision nutrition synthesis (+2 more)

### Community 13 - "Shared Household Planning Seams"
Cohesion: 0.25
Nodes (8): All five V1.3 seam mutation scenarios remain PENDING, Households: ownership members and shared resources, Shopping: quantitative fulfillment and actual purchases, MealParticipants preserve identity safety and derived attendance, Root guards independently evaluate canonical safety and goal contracts, Five canonical handoff contracts close subsystem seams, Shared-meal utility aggregates member profiles without copying preferences, Revision budget equals actual sunk spend plus future stress spend

### Community 14 - "Canonical Baseline Checker"
Cohesion: 0.50
Nodes (4): check_baseline(), check_links(), check_numbered_set(), main()

### Community 15 - "Confirmed Physical Execution"
Cohesion: 0.40
Nodes (6): Single stable ActivePlan with revisable future intent, State-changing command idempotency and optimistic revision locking, ConfirmedState changes only from direct evidence, Execution: physical facts and state projections, Inventory: physical lots reservations and movements, ExecutionLedger records actual facts separately from intent revisions

### Community 16 - "Reversible Operational Assumptions"
Cohesion: 0.33
Nodes (6): Assumption dependency graph with compensating reversal and conflicts, Gated AUTOPILOT_ASSUMED is provisional and reversible, ExecutionImpactAnalyzer escalates local repair before global replan, OperationalState adds reversible operational assumptions, PlanningState resolves and reconciles optimizer input, POSTFACT diagnoses reality without rejecting history

### Community 17 - "Batch Material Conservation"
Cohesion: 0.50
Nodes (4): Batch physical transformation and composition per serving, Global material conservation and chronological causal replay, Cooking: batch transformation and allocation, PreparedFoodLot household assets tracked in servings

### Community 18 - "Validation Namespace Boundary"
Cohesion: 0.67
Nodes (3): Validator contracts-only imports exclude planner internals and OR-Tools, Independent validation namespace without production orchestrator, Specified PRECOMMIT intent gate and POSTFACT reality diagnosis

## Knowledge Gaps
- **25 isolated node(s):** `Vietnamese foundation HTML entry point`, `Unprovisioned persistence and infrastructure boundary`, `@menuto/api-client`, `@types/react`, `@types/react-dom` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 191 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Menuto V1.3 Closed-Loop Canonical Architecture Baseline` connect `Accepted Architecture Contracts` to `Baseline Gates and Delivery`, `Independent Validation Contracts`, `Attributed Behavioral Learning`, `Planner Policy and Nutrition`, `Shared Household Planning Seams`, `Confirmed Physical Execution`, `Batch Material Conservation`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Menuto V1.3 Closed-Loop Canonical Architecture Baseline` (e.g. with `ADR-009: Execution State Machine, Single ActivePlan Graph & Reversible Operational Assumptions [accepted architecture]` and `ADR-010: Independent Semantic Validator, Primitive Recomputation & Chronological Replay [accepted architecture]`) actually correct?**
  _`Menuto V1.3 Closed-Loop Canonical Architecture Baseline` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Vietnamese foundation HTML entry point`, `Unprovisioned persistence and infrastructure boundary`, `@menuto/api-client` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Synthetic Solver and Audit` be split into smaller, more focused modules?**
  _Cohesion score 0.06694677871148459 - nodes in this community are weakly interconnected._
- **Why does `Foundation aligned with V1.3 architecture not closed-loop implementation` connect `Baseline Gates and Delivery` to `Accepted Architecture Contracts`, `Independent Validation Contracts`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `Scenario` (e.g. with `audit_solution_data()` and `SyntheticCpSatAdapter`) actually correct?**
  _`Scenario` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Should `Accepted Architecture Contracts` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
## V1.3 incremental baseline audit

- All outputs describe source snapshot 536785aff909c122c232e5c93949c4132b562187, in the isolated checkout C:\PERSONAL1\Menutor\v13-baseline. Only graphify-out/ was written; no source, Git, global skill, dependency or primary checkout changes were performed.
- Canonical V1.3 replaces V1.2: the deleted V1.2 source contribution was pruned, all 30 invariant requirements and 11 normalized ADRs were re-extracted, and V1.3 source vocabulary/relationships are requirements unless explicitly backed by current code.
- Intentional source replacement: 40 prior semantic nodes belong to the explicitly deleted V1.2 source; export guard bypass was limited to this verified deletion. Nondeleted semantic concepts were checked for retention. This is a derived-graph export, not a Git force update.
- Namespace, baseline checks, document coverage matrices and passing foundation tests do not prove the 30 business invariants are implemented. Validation/learning namespaces are boundaries, not production Validator V2 or behavioral learning implementations. Synthetic micro-model fixtures remain separate from the production planner.
- Corpus: 109 files / approximately 36,962 words. Incremental AST: 46 code files. Semantic coverage: 29/29 changed documents, 3504 fully-read lines, three bounded chunks; no partial semantic cache entries.
- Copied semantic cache had no valid hits for the changed V1.3 documents, so these required documents were re-extracted. Unchanged contributions were retained through build_merge; a complete repository rebuild was not performed.
- Exclusions: root user-supplied originals and root adr/, smart-menu/, .git/, dependencies/caches/build output, local imports, benchmark/results/, graphify-out/ and generated API-client schemas/types/standalone validators. Client generation/source wrapper/tests and source OpenAPI remain mapped.
- Actual token usage and monetary cost: UNKNOWN. No external LLM API or Graphify CLI was used; GRAPHIFY_NO_AUTO_REFRESH=1 was set throughout.

## Integrity diagnostics and freshness

- Final merged graph: 0 dangling endpoint edges, 0 missing endpoint fields, 2 self-loop edges.
- Raw changed AST: 64 unresolved endpoint edges, 14 collapsed relation pairs, 2 self-loops. Post-build graph diagnostics do not erase raw extraction limitations; no manual fake endpoints were added.
- The two retained generator self-loops are verified recursive auditReferences()/rewrite() calls, not false cross-module links. Generated/external placeholders are references, not verified implementations.
- Artifact-only commits and merges do not themselves change the source corpus. Compare saved manifest content hashes to assess freshness; HEAD mismatch alone is not evidence of stale source.

```text
[graphify] MultiDiGraph edge-collapse diagnostic
input: <in-memory>
input_stage: provided JSON (normal graph.json is post-build)
effective_directed: <direct-call>
nodes: 170
unverified_code_nodes: 0
raw_edges: 308
valid_candidate_edges: 241
missing_endpoint_edges: 0
dangling_endpoint_edges: 64
external_reference_edges: 3
self_loop_edges: 2
exact_duplicate_edges: 0
directed_unique_endpoint_pairs: 227
directed_same_endpoint_collapsed_edges: 14
undirected_unique_endpoint_pairs: 227
undirected_same_endpoint_collapsed_edges: 14
same_endpoint_group_count: 13
relation_variant_groups: 11
source_file_variant_groups: 0
source_location_variant_groups: 1
context_variant_groups: 1
post_build_graph_type: Graph
post_build_edges: 286
producer_suppression_sites: 12
producer_suppression_examples:
  - L1813 seen_ids arity=unknown
  - L2377 seen_ids arity=unknown
  - L2379 seen_doc_refs arity=unknown
  - L3046 seen_ids arity=unknown
  - L3193 seen_ids arity=unknown
  - L4203 seen_keys arity=unknown
  - L4389 seen_keys arity=unknown
  - L7641 seen_ids arity=unknown
examples:
  - benchmark_reference_solve_reference -> benchmark_schema_solveresult edges=3 relations=['calls', 'references', 'uses'] locations=['L107', 'L9'] contexts=['', 'call', 'generic_arg']
  - benchmark_cpsat_syntheticcpsatadapter_solve -> benchmark_cpsat_syntheticcpsatadapter_solve_capture edges=2 relations=['calls', 'contains'] locations=['L111', 'L142'] contexts=['', 'call']
  - benchmark_reference_solve_reference -> benchmark_schema_scenario edges=2 relations=['references', 'uses'] locations=['L9'] contexts=['', 'parameter_type']
  - benchmark_runner_run_case -> benchmark_schema_scenario edges=2 relations=['references', 'uses'] locations=['L23', 'L24'] contexts=['', 'parameter_type']
  - benchmark_runner_run_case -> benchmark_schema_solveconfig edges=2 relations=['references', 'uses'] locations=['L23', 'L26'] contexts=['', 'parameter_type']
note: normal graph.json is post-build; raw producer loss must be measured earlier.
```

## Derived outputs

Only graph.json, graph.html and GRAPH_REPORT.md are intended for version control. Manifest, cache, extraction chunks, runtime paths and unknown-cost tracker remain ignored local artifacts. Canonical documents remain authoritative.

## Graph context-size estimate

The optional Graphify retrieval benchmark uses the full-corpus word count and estimates context-size reduction. It is not measured model usage, monetary savings, or application runtime performance; actual usage/cost remain UNKNOWN.
