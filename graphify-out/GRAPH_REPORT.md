# Graph Report - Menuto  (2026-10-21)

## Corpus Check
- 96 files · ~28,219 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 385 nodes · 616 edges · 32 communities (12 shown, 20 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 31 edges (avg confidence: 0.93)
- Token cost: UNKNOWN (the host did not expose measured input/output token usage; zero extraction placeholders are not real usage).

## Graph Freshness
- Built from commit: `2bf9b9fd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- For future updates, set GRAPHIFY_NO_AUTO_REFRESH=1 before invoking Graphify. Structural code extraction is local; changed-document semantic extraction can consume agent/model tokens and any associated provider cost. No zero-cost claim is made.

## Community Hubs (Navigation)
- Synthetic Solver and Audit
- Nutrition and Architecture Policies
- Boundary Checks and Fixture Metadata
- Contract and Benchmark Verification
- Local Client Code Generation
- Web Dependency Toolchain
- Runtime API Client
- Health API and Tests
- Neutral Benchmark Schema
- Web TypeScript Configuration
- Root Workspace Commands
- API Client TypeScript Configuration
- Unresolved Menuto Reference

## God Nodes (most connected - your core abstractions)
1. `Scenario` - 29 edges
2. `SolveConfig` - 27 edges
3. `SyntheticCpSatAdapter` - 23 edges
4. `Modular Monolith architecture requirement` - 16 edges
5. `SolveResult` - 15 edges
6. `Twelve canonical architecture invariants` - 14 edges
7. `run_case()` - 14 edges
8. `compilerOptions` - 12 edges
9. `solve_reference()` - 12 edges
10. `Synthetic v2 benchmark harness with 22 fixtures` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Versioned required stress scenarios BASE and justified base-only policy` --semantically_similar_to--> `SPEND_LIMIT deterministic stress scenarios`  [INFERRED] [semantically similar]
  benchmark/README.md → docs/MENUTO_DEVELOPMENT_SPEC_V1_2.md
- `Independent arithmetic micro-model verifier` --semantically_similar_to--> `Independent Validator requirement`  [INFERRED] [semantically similar]
  benchmark/README.md → docs/MENUTO_DEVELOPMENT_SPEC_V1_2.md
- `test_relative_import_in_package_is_resolved()` --calls--> `check_source()`  [INFERRED]
  apps/backend/tests/test_architecture.py → tools/check_import_boundaries.py
- `main()` --calls--> `create_app()`  [EXTRACTED]
  tools/export_openapi.py → apps/backend/app/main.py
- `Contribution verification and protected-main conventions` --references--> `Twelve canonical architecture invariants`  [EXTRACTED]
  CONTRIBUTING.md → docs/ARCHITECTURE_INVARIANTS.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Specified household meal demand and batch separation** — docs_menuto_development_spec_v1_2_household, docs_menuto_development_spec_v1_2_mealparticipants, docs_menuto_development_spec_v1_2_consumptiondemand, docs_menuto_development_spec_v1_2_cookingbatch [EXTRACTED 1.00]
- **Specified trusted planning boundary** — docs_menuto_development_spec_v1_2_planpolicyresolver, docs_menuto_development_spec_v1_2_groundedrecipevariant, docs_menuto_development_spec_v1_2_stage1, docs_menuto_development_spec_v1_2_independent_validator, docs_menuto_development_spec_v1_2_assistant [EXTRACTED 1.00]

## Communities (32 total, 20 thin omitted)

### Community 0 - "Synthetic Solver and Audit"
Cohesion: 0.10
Nodes (32): audit_solution_data(), purchasable(), SyntheticCpSatAdapter, capture(), BenchmarkAdapter, solve_reference(), run_case(), Scenario (+24 more)

### Community 1 - "Nutrition and Architecture Policies"
Cohesion: 0.05
Nodes (41): ADR-001 Accepted Band-First Planner, ADR-002 Accepted Nutrition Policy Engine, ADR-003 Accepted Orthogonal Plan Policy Resolution, ADR-004 Accepted Household-First Model, ADR-005 Accepted Grounded Recipe Variants, ADR-006 Accepted Retail Procurement Abstraction, ADR-007 Accepted SPEND_LIMIT Robustness, Twelve canonical architecture invariants (+33 more)

### Community 2 - "Boundary Checks and Fixture Metadata"
Cohesion: 0.07
Nodes (13): test_checker_allows_public_interfaces_and_same_context_internals(), test_checker_catches_real_dependency_violations(), test_relative_import_in_package_is_resolved(), derive_tags(), main(), check_source(), check_tree(), main() (+5 more)

### Community 3 - "Contract and Benchmark Verification"
Cohesion: 0.07
Nodes (39): Foundation CI Python and web contract gates, FastAPI backend foundation, Vietnamese foundation HTML entry point, React TypeScript Vite web consuming generated client, Independent arithmetic micro-model verifier, Independent exhaustive micro-model reference, 22 synthetic fixtures with data-derived coverage tags, Synthetic v2 benchmark harness with 22 fixtures (+31 more)

### Community 4 - "Local Client Code Generation"
Cohesion: 0.06
Nodes (30): ajv, auditReferences(), check, document, generated, healthName, rewrite(), runtime (+22 more)

### Community 5 - "Web Dependency Toolchain"
Cohesion: 0.07
Nodes (26): dependencies, @menuto/api-client, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript (+18 more)

### Community 6 - "Runtime API Client"
Cohesion: 0.13
Nodes (10): api, getHealth, App(), healthy, createMenutoApi(), HealthResponse, openapi-fetch, react (+2 more)

### Community 7 - "Health API and Tests"
Cohesion: 0.17
Nodes (3): create_app(), health(), HealthResponse

### Community 8 - "Neutral Benchmark Schema"
Cohesion: 0.20
Nodes (8): Band, Candidate, Lot, Product, Record, Slot, StressScenarioPolicy, test_invalid_empty_policy_is_not_silently_normalized()

### Community 9 - "Web TypeScript Configuration"
Cohesion: 0.14
Nodes (13): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, noEmit, resolveJsonModule (+5 more)

### Community 10 - "Root Workspace Commands"
Cohesion: 0.15
Nodes (12): engines, node, name, private, scripts, build:web, contracts:check, contracts:generate (+4 more)

### Community 11 - "API Client TypeScript Configuration"
Cohesion: 0.17
Nodes (11): compilerOptions, esModuleInterop, lib, module, moduleResolution, noEmit, resolveJsonModule, skipLibCheck (+3 more)

## Knowledge Gaps
- **23 isolated node(s):** `menuto`, `Open Behavioral Learning design`, `Open Execution State Machine design`, `Identity domain`, `Open ReferenceFeasibleCost implementation` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 179 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Twelve canonical architecture invariants` connect `Nutrition and Architecture Policies` to `Contract and Benchmark Verification`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `Scenario` (e.g. with `audit_solution_data()` and `SyntheticCpSatAdapter`) actually correct?**
  _`Scenario` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `menuto`, `Open Behavioral Learning design`, `Open Execution State Machine design` to the rest of the system?**
  _23 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Synthetic Solver and Audit` be split into smaller, more focused modules?**
  _Cohesion score 0.10338345864661654 - nodes in this community are weakly interconnected._
- **Why does `Modular Monolith architecture requirement` connect `Nutrition and Architecture Policies` to `Contract and Benchmark Verification`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `SolveConfig` (e.g. with `SyntheticCpSatAdapter` and `BenchmarkAdapter`) actually correct?**
  _`SolveConfig` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `Nutrition and Architecture Policies` be split into smaller, more focused modules?**
  _Cohesion score 0.05429864253393665 - nodes in this community are weakly interconnected._
## Incremental coverage and source snapshot

- Source snapshot: 2bf9b9fd37dd219901898cfe15211513f7a67fa2. A later graph-artifact-only commit does not alter this scanned source corpus; use manifest content hashes to assess freshness.
- Corpus: 96 files, approximately 28,219 words. Incremental extraction: 47 changed code files and 9 changed documents.
- Semantic coverage: 9/9 changed documents read completely, 309 lines; unchanged canonical specification and ADRs reused without rereading/reextracting.
- Excluded: smart-menu/ (restored legacy), .git/, .venv/, node_modules/, dist/, local imports, benchmark/results/, graphify-out/ and packages/api-client/src/generated/ (generated schemas/types/standalone validators). Generator, client wrapper/tests, source OpenAPI and contract documentation remain mapped.
- Historical shared data_problem symbol is absent after replace-on-reextract; independent audit, report/schema v2 and runtime client boundary are represented from current sources. Synthetic micro-model evidence does not establish production Planner V4 correctness.
- Semantic concept relationships remain marked EXTRACTED/INFERRED/AMBIGUOUS. Existing canonical requirements are retained as requirements, not implementation claims.
- Actual host-agent token usage and monetary cost are UNKNOWN; no external LLM API was used. No CLI auto-refresh, global skill edits or Git mutations were performed in this update.

## Graph integrity audit

- Final merged graph: 0 dangling endpoint edges, 0 missing endpoint fields, 2 self-loop edges.
- Raw changed AST diagnostic: 51 unresolved endpoint edges and 34 relation pairs collapsed by the default undirected Graph. These are extractor/representation limitations; external placeholders are not evidence that those targets were implemented or validated.
- No fake endpoint nodes were manually added to conceal diagnostic warnings. Final-graph diagnostics are post-build; raw-extraction diagnostics retain evidence that would otherwise be hidden by merge/materialization.

```text
[graphify] MultiDiGraph edge-collapse diagnostic
input: <in-memory>
input_stage: provided JSON (normal graph.json is post-build)
effective_directed: <direct-call>
nodes: 198
unverified_code_nodes: 0
raw_edges: 392
valid_candidate_edges: 338
missing_endpoint_edges: 0
dangling_endpoint_edges: 51
external_reference_edges: 3
self_loop_edges: 2
exact_duplicate_edges: 0
directed_unique_endpoint_pairs: 304
directed_same_endpoint_collapsed_edges: 34
undirected_unique_endpoint_pairs: 304
undirected_same_endpoint_collapsed_edges: 34
same_endpoint_group_count: 32
relation_variant_groups: 31
source_file_variant_groups: 0
source_location_variant_groups: 2
context_variant_groups: 1
post_build_graph_type: Graph
post_build_edges: 357
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
  - apps_web_src_api -> packages_api_client_src_index edges=3 relations=['imports_from', 're_exports'] locations=['L1', 'L2'] contexts=['export', 'import', 're-export']
  - benchmark_reference_solve_reference -> benchmark_schema_solveresult edges=3 relations=['calls', 'references', 'uses'] locations=['L107', 'L9'] contexts=['', 'call', 'generic_arg']
  - benchmark_audit_independent_data_check_audit_solution_data -> benchmark_schema_scenario edges=2 relations=['references', 'uses'] locations=['L6'] contexts=['', 'parameter_type']
  - benchmark_audit_independent_data_check_audit_solution_data -> benchmark_schema_solveresult edges=2 relations=['references', 'uses'] locations=['L6'] contexts=['', 'parameter_type']
  - benchmark_cpsat_syntheticcpsatadapter_solve -> benchmark_cpsat_syntheticcpsatadapter_solve_capture edges=2 relations=['calls', 'contains'] locations=['L111', 'L142'] contexts=['', 'call']
note: normal graph.json is post-build; raw producer loss must be measured earlier.
```

## Working-tree outputs

Only graph.json, graph.html and GRAPH_REPORT.md are public derived outputs. Runtime paths, extraction chunks, caches, manifest and unknown-cost tracker remain local under graphify-out/ via .gitignore. Canonical project documents remain authoritative.

## Graph context-size estimate

The optional Graphify token-reduction benchmark is a heuristic estimate of retrieved context size, not measured model usage, monetary savings or application runtime. Full-corpus words were supplied explicitly for this incremental update.

## Confirmed recursion and artifact freshness

The two self-loop edges are actual recursive calls in packages/api-client/generate.mjs: auditReferences() at L19 and rewrite() at L34. They were checked against the source and are not mistaken cross-module relationships.

All three public outputs describe source snapshot 2bf9b9fd37dd219901898cfe15211513f7a67fa2. An artifact-only commit or merge commit does not itself make the corpus stale; compare the saved manifest content hashes before deciding to reextract. Canonical specification/invariant/ADR files were unchanged and their existing graph contributions were reused.

The Graphify retrieval-size heuristic estimated ~37,625 naive context tokens versus ~1,610 retrieved tokens per query (23.4x ratio). This estimate is not measured model usage or monetary savings; actual token usage/cost remain UNKNOWN.
