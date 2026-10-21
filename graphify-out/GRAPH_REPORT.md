# Graph Report - Menuto  (2026-10-21)

## Corpus Check
- Corpus is ~23,650 words - fits in a single context window. You may not need a graph.

## Summary
- 248 nodes · 389 edges · 27 communities (8 shown, 19 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 24 edges (avg confidence: 0.93)
- Token cost: UNKNOWN (the agent host did not expose real input/output usage; zero placeholders in internal extraction schema are not measured usage).

## Graph Freshness
- Built from commit: `093deda9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Architecture and Nutrition Policies
- Solver and Benchmark Runs
- Web Package Toolchain
- Validation and Delivery Boundaries
- Neutral Fixture Contracts
- Health API and Tests
- Fixture and Contract Utilities
- TypeScript Compiler Configuration
- Unresolved Menuto Reference

## God Nodes (most connected - your core abstractions)
1. `Scenario` - 23 edges
2. `SolveConfig` - 19 edges
3. `Modular Monolith architecture requirement` - 16 edges
4. `SyntheticCpSatAdapter` - 15 edges
5. `Twelve canonical architecture invariants` - 14 edges
6. `SolveResult` - 13 edges
7. `run_case()` - 12 edges
8. `compilerOptions` - 10 edges
9. `solve_reference()` - 10 edges
10. `Record` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Synthetic CP-SAT micro-model adapter` --semantically_similar_to--> `Stage 1 Comfort and Structural Economics specification`  [INFERRED] [semantically similar]
  benchmark/README.md → docs/MENUTO_DEVELOPMENT_SPEC_V1_2.md
- `Independent arithmetic micro-model verifier` --semantically_similar_to--> `Independent Validator requirement`  [INFERRED] [semantically similar]
  benchmark/README.md → docs/MENUTO_DEVELOPMENT_SPEC_V1_2.md
- `main()` --calls--> `create_app()`  [EXTRACTED]
  tools/export_openapi.py → apps/backend/app/main.py
- `Contribution and verification conventions` --references--> `Twelve canonical architecture invariants`  [EXTRACTED]
  CONTRIBUTING.md → docs/ARCHITECTURE_INVARIANTS.md
- `Menuto scaffold and synthetic benchmark foundation` --references--> `Twelve canonical architecture invariants`  [EXTRACTED]
  README.md → docs/ARCHITECTURE_INVARIANTS.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Implemented micro-model cross-checks** — benchmark_readme_harness, benchmark_readme_syntheticcpsatadapter, benchmark_readme_exhaustive_reference, benchmark_readme_arithmetic_verifier [EXTRACTED 1.00]
- **Specified household meal demand and batch separation** — docs_menuto_development_spec_v1_2_household, docs_menuto_development_spec_v1_2_mealparticipants, docs_menuto_development_spec_v1_2_consumptiondemand, docs_menuto_development_spec_v1_2_cookingbatch [EXTRACTED 1.00]
- **Specified trusted planning boundary** — docs_menuto_development_spec_v1_2_planpolicyresolver, docs_menuto_development_spec_v1_2_groundedrecipevariant, docs_menuto_development_spec_v1_2_stage1, docs_menuto_development_spec_v1_2_independent_validator, docs_menuto_development_spec_v1_2_assistant [EXTRACTED 1.00]

## Communities (27 total, 19 thin omitted)

### Community 0 - "Architecture and Nutrition Policies"
Cohesion: 0.05
Nodes (43): Contribution and verification conventions, ADR-001 Accepted Band-First Planner, ADR-002 Accepted Nutrition Policy Engine, ADR-003 Accepted Orthogonal Plan Policy Resolution, ADR-004 Accepted Household-First Model, ADR-005 Accepted Grounded Recipe Variants, ADR-006 Accepted Retail Procurement Abstraction, ADR-007 Accepted SPEND_LIMIT Robustness (+35 more)

### Community 1 - "Solver and Benchmark Runs"
Cohesion: 0.12
Nodes (21): SyntheticCpSatAdapter, capture(), BenchmarkAdapter, solve_reference(), main(), run_case(), data_problem(), Scenario (+13 more)

### Community 2 - "Web Package Toolchain"
Cohesion: 0.07
Nodes (29): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+21 more)

### Community 3 - "Validation and Delivery Boundaries"
Cohesion: 0.10
Nodes (22): Foundation CI checks, FastAPI backend foundation, Vietnamese foundation HTML entry point, React TypeScript Vite web foundation, Independent arithmetic micro-model verifier, Independent exhaustive micro-model reference, Synthetic benchmark harness, Synthetic CP-SAT micro-model adapter (+14 more)

### Community 4 - "Neutral Fixture Contracts"
Cohesion: 0.19
Nodes (6): Band, Candidate, Lot, Product, Record, Slot

### Community 5 - "Health API and Tests"
Cohesion: 0.24
Nodes (5): create_app(), health(), HealthResponse, test_liveness_does_not_claim_planner_readiness(), test_no_unimplemented_planning_endpoint_is_advertised()

### Community 6 - "Fixture and Contract Utilities"
Cohesion: 0.27
Nodes (4): main(), base(), fixtures(), main()

### Community 7 - "TypeScript Compiler Configuration"
Cohesion: 0.17
Nodes (11): compilerOptions, jsx, lib, module, moduleResolution, noEmit, skipLibCheck, strict (+3 more)

## Knowledge Gaps
- **22 isolated node(s):** `@types/react`, `@types/react-dom`, `typescript`, `menuto`, `Contribution and verification conventions` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 108 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Modular Monolith architecture requirement` connect `Architecture and Nutrition Policies` to `Validation and Delivery Boundaries`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Scenario` (e.g. with `SyntheticCpSatAdapter` and `BenchmarkAdapter`) actually correct?**
  _`Scenario` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@types/react`, `@types/react-dom`, `typescript` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Architecture and Nutrition Policies` be split into smaller, more focused modules?**
  _Cohesion score 0.0517120894479385 - nodes in this community are weakly interconnected._
- **Why does `Twelve canonical architecture invariants` connect `Architecture and Nutrition Policies` to `Validation and Delivery Boundaries`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `SolveConfig` (e.g. with `SyntheticCpSatAdapter` and `BenchmarkAdapter`) actually correct?**
  _`SolveConfig` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `Solver and Benchmark Runs` be split into smaller, more focused modules?**
  _Cohesion score 0.11655874190564293 - nodes in this community are weakly interconnected._
## Coverage and integrity audit

- Semantic coverage: 23 of 23 files read completely; 2521 lines; no partial file cached.
- Semantic data: 77 nodes, 106 edges; all semantic endpoints validated.
- Provenance: AST describes current source structure; semantic concepts also describe requirements and accepted architecture. A graph link does not prove a product capability has been implemented.
- Token usage and monetary cost are unavailable, not zero. No external LLM key was used.
- AST coverage limitation: vite.config.ts and pyproject.toml produced no symbols.
- GRAPH HEALTH WARNING: 51 dangling_endpoint_edges; 25 directed_same_endpoint_collapsed_edges; 25 undirected_same_endpoint_collapsed_edges.
- Unresolved AST endpoints and merged endpoint pairs originate in Graphify extraction/default undirected Graph representation. They are retained as reported limitations; no invented nodes were added to hide them.

```text
[graphify] MultiDiGraph edge-collapse diagnostic
input: <in-memory>
input_stage: provided JSON (normal graph.json is post-build)
effective_directed: <direct-call>
nodes: 230
unverified_code_nodes: 0
raw_edges: 422
valid_candidate_edges: 371
missing_endpoint_edges: 0
dangling_endpoint_edges: 51
external_reference_edges: 0
self_loop_edges: 0
exact_duplicate_edges: 0
directed_unique_endpoint_pairs: 346
directed_same_endpoint_collapsed_edges: 25
undirected_unique_endpoint_pairs: 346
undirected_same_endpoint_collapsed_edges: 25
same_endpoint_group_count: 24
relation_variant_groups: 24
source_file_variant_groups: 0
source_location_variant_groups: 0
context_variant_groups: 0
post_build_graph_type: Graph
post_build_edges: 389
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
  - benchmark_reference_solve_reference -> benchmark_schema_solveresult edges=3 relations=['calls', 'references', 'uses'] locations=['L11', 'L9'] contexts=['', 'call', 'generic_arg']
  - benchmark_cpsat_syntheticcpsatadapter_solve -> benchmark_cpsat_syntheticcpsatadapter_solve_capture edges=2 relations=['calls', 'contains'] locations=['L115', 'L88'] contexts=['', 'call']
  - benchmark_reference_solve_reference -> benchmark_schema_scenario edges=2 relations=['references', 'uses'] locations=['L9'] contexts=['', 'parameter_type']
  - benchmark_runner_run_case -> benchmark_schema_scenario edges=2 relations=['references', 'uses'] locations=['L22', 'L23'] contexts=['', 'parameter_type']
  - benchmark_runner_run_case -> benchmark_protocol_benchmarkadapter edges=2 relations=['references', 'uses'] locations=['L22', 'L24'] contexts=['', 'parameter_type']
note: normal graph.json is post-build; raw producer loss must be measured earlier.
```

## Working-tree outputs

Only graph.json, graph.html and GRAPH_REPORT.md are intended for version control. Graphify runtime paths, cache and intermediate files remain local through .gitignore. The generated graph is a derived map; canonical documents remain authoritative.

## Graphify token-reduction estimate

The Graphify CLI heuristic benchmark reported a 12,400-word source subset (~16,533 naive tokens), ~1,618 estimated tokens per query and a 10.2x estimated reduction. This is a graph-context size estimate, not measured model usage, money saved or runtime speedup. Detection covered the full 78-file / 23,650-word corpus; the CLI benchmark subset differs.

## Runtime note

Graphifyy 0.9.93 was already installed. During HTML export, its CLI auto-refreshed the separate local OpenCode Graphify skill from 0.9.30 to 0.9.93 and created SKILL.md.bak. No Git hook, background monitor or project source rewrite was installed. Future local CLI calls can set GRAPHIFY_NO_AUTO_REFRESH=1 to suppress automatic skill refresh.

## Source snapshot and artifact commits

The map describes source snapshot 093deda9190d196037b74a0288bf669a2ebf2f64. A later commit that contains only these graph artifacts does not change the scanned code/docs corpus. Use the saved Graphify manifest hashes to check content freshness; a HEAD mismatch alone after an artifact-only commit is not evidence that source changed.

## Automatic refresh remediation

The separate OpenCode SKILL.md was restored byte-for-byte from the backup created by this CLI run (SHA-256 259ab8bbe28b3dfabf36640957e9468936ead03a9dbdd72867624a92d234d63c), and its version stamp was restored to 0.9.30. The backup is preserved. The CLI also refreshed eight references/ sidecar files; their previous bytes were not backed up, so their exact prior state cannot be safely reconstructed from the available evidence. No guessed sidecar restore or deletion was performed.
