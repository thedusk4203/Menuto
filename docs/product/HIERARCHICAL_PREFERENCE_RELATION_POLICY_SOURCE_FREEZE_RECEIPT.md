# Canonical Reviewed Hierarchical Preference Relation & Transfer-Policy Source Foundation — Freeze Receipt

Status: **FROZEN / APPROVED**. Recorded 2026-10-27.

The user accepted PR #104's implementation, authorized merge, received the exact post-merge
verification receipt, then explicitly declared the hierarchy SOURCE frozen in the post-freeze
dependency/readiness review. This records that user decision; CI success alone did not grant freeze.
The source foundation remains descriptive and unnumbered. It is not the newly selected MTR-040C
consumer, whose runtime is not authorized.

## Canonical implementation and verification

| Receipt | Canonical value |
| --- | --- |
| Repository | `thedusk4203/Menuto` |
| Implementation PR | [#104](https://github.com/thedusk4203/Menuto/pull/104), MERGED |
| Implementation base | `4ad3f682554b7feee9f333eca1f1f5c258852f5e` |
| Code/test/export commit | `64a78f3944f0e2d863164c3d47c34d4274168187` |
| Accepted final implementation head | `4263bf5f14f0aa2b65ba646891f3acf548826f1f` |
| Canonical implementation merge/freeze SHA | `ee8a4de1b1c71ccbd56ea565e111718660711fa8` |
| Exact-head implementation CI | [40404174647](https://github.com/thedusk4203/Menuto/actions/runs/40404174647), SUCCESS |
| Exact post-merge push CI | [40432057006](https://github.com/thedusk4203/Menuto/actions/runs/40432057006), SUCCESS on exact merge SHA above |
| Required jobs | `python` SUCCESS; `web` SUCCESS |
| Python regression | 2,807 passed; 2,597 baseline identities retained +210 additive |
| Real PostgreSQL / hierarchy source cases | 1,070 /152 |
| SCRAM/TLS smoke | 16/16, including retained8 prior-source cases and8 hierarchy cases |
| Benchmark / client | 22/22 /10/10; typecheck, generated contracts and web build passed |
| Definitions | 318 retained unchanged +31 additive =349 |
| Schema | Alembic `0015`, 85 domain tables; seven new hierarchy source tables |
| Seeds / row drift | No production seeds; all seven tables empty immediately after test migration; merge tree identical to approved head |
| Frozen compatibility | 42 runtime/migration pins match baseline, including unchanged migrations0001–0014 |

The merge receipt verified canonical main at the freeze SHA. Later documentation commits do not
redefine the implementation identity. The new dependency review uses that exact implementation
baseline. This receipt does not claim an audit of a live production database; migration acceptance
uses isolated real PostgreSQL, and merge verification introduced no new source rows or policy data.

## Exact frozen scope

Preferences owns global reviewed relation/transfer-policy semantics and publication, separately
from HouseholdMember authorship, the prior publisher and Catalog/Recipes classification curation.
The internal source interface provides hierarchy-specific provider registration, principal enrollment,
provider grant/revoke, immutable publication/retraction, coherent authorized capture and pure replay.

Preserved semantics:

- Actual PostgreSQL SCRAM sessions and database/login OID/name binding establish a separate hierarchy
  trust root. Remote interfaces require verified TLS/server identity. UUIDs, GUCs, hashes, provenance,
  household roles, prior grants and classification facts cannot mint hierarchy authority.
- Protected PostgreSQL paths enforce capability after provider/frontier lock and before idempotent
  receipt lookup. Revocation defeats old successful retries. Direct DML/TRUNCATE, grant/frontier
  bypass, private-function/role/search-path escalation and unsafe normal-interface roles fail closed.
- Authored policies contain a complete closed5×5 target-kind matrix. No enabled direction creates
  an edge automatically. Exact reviewed typed endpoints, direction, policy pin, support mode and
  explicit RecipeVersion/context define each relation. No reverse/latest/default/fallback inference.
- REVIEWED_EXACT_PAIR is explicit semantic permission. CLASSIFICATION_BOUND_PAIR additionally
  requires exact positive canonical owner support, independently reconstructed/revalidated in the
  protected transaction. Classification alone is never transfer authority.
- Finite semantic mapping binds full source descriptor, DISLIKE/NEUTRAL/LIKE and exact frozen040B
  expected amount. No numeric-sign inference. NEUTRAL→0/1, DISLIKE≤0, LIKE≥0; strict semantic order
  applies where multiple states exist. Missing row remains SOURCE_VALUE_NOT_MAPPED; mapped zero
  is AVAILABLE. No interpolation, nearest neighbor, implicit zero, anti-correlation or affine default.
- Attenuation is exact reviewed policy data with0<a≤1. No member arithmetic occurs in the SOURCE;
  no production numeric coefficient is seeded or supplied as a default.
- Full replacements, tombstones, CAS/idempotency and interleaved journal/frontier updates are atomic
  under caller-owned transactions. No history mutation/deletion, no hidden semantic retry or commit
  certification. Policy supersession/retraction requires explicit relation repinning for fresh use.
- Durable rows hold owner IDs/fingerprints/frontier pins, not capture snapshots or member results.
  Authorized read-only RR/SERIALIZABLE capture includes complete provider history and required
  historical/current owner primitives. Replay is deterministic, recursively validates primitives
  and children, and performs zero DB/network/filesystem IO.
- One-hop only; inherited values cannot become parents. Multiple active incoming relations are
  counted before favorable-support/member-value filtering. No aggregation, strongest/newest winner,
  recursive propagation or diamond double-counting. Cycle rejection is topology validation only.
- Source status/reason distinctions, including missing/retracted/superseded/unresolved/reviewed-none/
  reviewed-absent, remain distinct from member NEUTRAL or numeric zero. Per-head diagnostics remain.
- Source fingerprints describe full capture/replay identity. Offline self-consistency proves neither
  canonical DB origin nor simultaneously live/current authority across different captures.

The [approved source design](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_DESIGN.md) together with
the [neutral-anchor correction](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_NEUTRAL_ANCHOR_CORRECTION.md)
remains normative. The correction supersedes only the stricter finite-map semantics. The complete
[implementation evidence and28-case acceptance map](HIERARCHICAL_PREFERENCE_RELATION_POLICY_SOURCE_IMPLEMENTATION_EVIDENCE.md)
retains its historical delivery receipts; this receipt supersedes only their current-status reading.
No frozen runtime, contract, migration, test or approved semantic requirement is modified here.

## Explicitly absent / unavailable capabilities

The SOURCE derives no member affinity or EvidenceStrength. It adds no hierarchy consumer,
MemberBehaviorProfile, learned/contextual/passive observations, profile/cache persistence, history,
repeat/novelty, TasteFit, household/candidate aggregation, planner utility, hard-safety authority,
Execution or PRECOMMIT. No production providers, grants, relations, enabled directions, mapping
rows or attenuation values exist merely because this framework is frozen.

`planner_ready=False`, `activation_ready=False`. Full040/041/046 remain PARTIAL;024/020B/021 BLOCKED;
Execution NOT STARTED; PRECOMMIT FAIL-CLOSED. Frozen040A/B,041A–F,046A, prior source and PR #100
retain their original unavailable/not-performed fields and meanings.

## Next gate

The user's [post-freeze dependency/readiness review](POST_HIERARCHY_SOURCE_FREEZE_DEPENDENCY_REVIEW.md)
selects **MTR-040C — One-hop Hierarchical Member Preference Consumer Foundation**,
**READY FOR DETAILED ARCHITECTURE/DESIGN**. This numbering applies to that future consumer only.
No runtime implementation, new migration, production transfer data or downstream integration is
authorized. The detailed design must receive its own architecture approval before a separate
implementation authorization. Parent MTR-040/issue #41 remains open and PARTIAL pending a separate
post-040C completion review.

**HIERARCHY SOURCE FROZEN — MTR-040C PURE HIERARCHY CONSUMER DESIGN REVIEW — IMPLEMENTATION NOT AUTHORIZED**
