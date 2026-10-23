# MTR-040A — Explicit Member Preference Foundation / evidence

Implementation baseline: `75d76ad2b400095d7eedf949fdec15bb969b9b5d`.
[Approved design and required correction](MTR_040A_EXPLICIT_MEMBER_PREFERENCE_REVIEW.md).
Code commit/PR/CI are recorded after executed verification. This slice is not self-FROZEN.

## Actual implementation

- Catalog immutable reviewed/versioned AffinityFeatureTerm vocabulary; no inferred recipe or
  ingredient classification. Preferences own stable typed target streams, immutable declarations,
  DB-maintained member frontier/head and coherent read-only source snapshots.
- Five target identities; one explicit subject; authenticated internal actor checked against
  canonical membership. SELF and AUTHORIZED_REPRESENTATIVE stay visible. No declaration fan-out.
- LIKE/DISLIKE/NEUTRAL are raw assertions. **No EvidenceStrength, strength_basis,
  assertion_confidence, scalar affinity/TasteFit or learned weight in raw command/fact/table.**
  Undeclared/retracted do not become explicit neutral. DISLIKE does not alter hard safety facts.
- SET/replacement/retraction retain source/actor/role-at-write/lineage. DB allocates sequence,
  recorded_at, actor audit and canonical command hash; callers cannot author those fields. Correct
  retry is resolved before stale-head rejection; changed command under same key fails.
- Transactions belong to the caller. Membership FOR SHARE → retry-key advisory fence → member
  advisory fence → stream/frontier row locks → append/head/frontier update. DB repeats canonical
  checks; READ COMMITTED competing CAS and stale REPEATABLE READ fail without lost updates.
- Deferred stream/FK completeness prevents empty aggregates; direct DML on immutable history,
  target identity or cached heads/frontiers is rejected. Threat model excludes a privileged actor
  disabling/rewriting triggers/DDL; negative SQL uses the test database owner under ordinary DML.
- Snapshot captures all explicit member history/terms/frontier under clean read-only RR/SERIALIZABLE.
  Pure primitive replay checks ownership, sequence, lineage, targets and fingerprints. No source
  differs from a successful empty explicit source. No DB queries inside contract replay.

## Database and compatibility

Forward migration **0011_explicit_member_preferences.py**: four tables, actual registered domain
count **58**. Source DDL is frozen literal SQL; migration imports only Alembic op, no mutable
metadata. Developer-time DDL generation does not occur during migration execution.

Tables: affinity_feature_terms (Catalog), member_preference_frontiers,
member_preference_streams, member_preference_declarations (Preferences). Typed/check/unique/FKs,
append guards, canonical fingerprint derivation and ownership below the API. No JSONB storage.

0001–0010 untouched. Empty0010→0011→0010→0011 works with pre-existing household/catalog data;
populated preference or vocabulary downgrade fails closed. Existing fixture setup also checks
head→base→head and Alembic metadata drift. No fake learned-profile backfill or vocabulary defaults.

## New tests and verification

Executed locally with Python3.13 / PostgreSQL18.4:

| Check | Actual result |
| --- | --- |
| Complete Python suite | **1324 passed**,0 failures/errors/skips;165.77s |
| PostgreSQL-real included above | **589** (525 prior +64 new), independently marker-collected |
| Pre-existing test identities | **1217/1217 retained** against frozen020A XML |
| New tests | **107 =43 unit +64 real PostgreSQL** |
| Migration/metadata | Empty/current/data-bearing up/down/up, populated preference/vocabulary refusal and Alembic drift PASS |
| Frozen compatibility |162 prior schema definitions unchanged,10 additive (bundle15/172 total); prior modified-module class/function ASTs unchanged |
| Architecture |30 invariants/11 ADRs/50 tasks,16-context import boundaries PASS |
| Export checks | Domain/OpenAPI/client generation and22 fixture drift PASS |
| Benchmark | **22/22**, HARNESS_SMOKE_NOT_PLANNER_V4 |
| Client | **10/10**, typecheck/generated contract check PASS |
| Web | TypeScript/Vite build PASS |
| Ruff/whitespace | PASS |

One existing Starlette/httpx deprecation warning remains. An intermediate full run exposed
current-head/table assertions and a historical-revision ORM check; these were updated as described
below, without weakening business/hash/data-preservation checks. The final full run above passed.
Code commit and remote CI evidence are added after the workflow completes.
New tests include raw-strength/extra-field rejection; all target kinds; wrong/draft/missing feature;
UNDECLARED/NEUTRAL/RETRACTED; lineage/owner/sequence/hash corruption; zero-IO replay; idempotent retry;
provider identity/Unicode/time serialization; proxy/self/viewer/foreign-principal checks; historical
membership removal; SQL UPDATE/DELETE/TRUNCATE/cache/audit tampering; concurrent CAS in RC/RR;
same-key retry/different-target frontier races; permission revocation lock; RR capture during a
concurrent correction; feature-version non-retargeting; populated migration checks.

Ignored artifacts: `.local/preference-pg.xml`, `.local/preference-pg.log`,
`.local/preference-full.xml`, `.local/preference-full.log`, `.local/preference-benchmark.json`.
Intermediate test iteration corrected contract subclass roundtrip and flushed deferred FK events
before testing the actual TRUNCATE guard; the final results below are from the corrected tests.

## Changed file groups

Catalog contracts/models/public; Household public actor-read/lock facade; new Preferences
contracts/models/public; persistence registration; migration0011; preference fixture/unit/real-PG
tests; additive domain export/bundle/README; design/evidence/status/backlog/blueprint/glossary/
invariant coverage. Existing business/golden-hash assertions are preserved, not weakened. Current-head
migration assertions advance0010/54→0011/58; Recipe's expected head table set gains the four tables.
The explicit0009↔0010 legacy test keeps its original table/hash assertions and moves ORM drift to
current head (then returns to0010), because runtime metadata describes0011 rather than historical0010.

## Limits

No learned MemberBehaviorProfile, derived EvidenceStrength, inferred preferences, shrinkage,
cold-start priors, taxonomy feature assignment, exposure/repeat cooldown, preference aggregation,
utility/ranking or role portfolio. No HTTP auth/consent UI, per-version recipe preference, scheduled
preference application or retroactive rescoring. Curated vocabulary writes are internal source
operations, not a production importer or automatic review workflow. No Execution/Inventory/Planner
mutation, MTR-019D or production PRECOMMIT. Cross-domain source-frontier authorization still needs
its later all-source TOCTOU/validator guard; this member frontier does not grant authority.

MTR-041 is next only after acceptance of040A; full MTR-040/019/020/026 remain incomplete;
MTR-020B and MTR-021 remain blocked. **READY FOR ARCHITECTURE/FREEZE REVIEW** for040A only.
