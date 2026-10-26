# Exact-target Prior Compatibility & Shrinkage Foundation — Freeze Receipt

Status: **FROZEN / APPROVED**.

The user accepted PR #100 after independent implementation review, authorized its merge,
verified its post-merge receipt, and explicitly approved this freeze. Recorded on 2026-10-26.
This descriptive slice is **not MTR-040C**; no milestone suffix is assigned.

## Canonical implementation and verification

| Receipt | Canonical value |
| --- | --- |
| Repository | `thedusk4203/Menuto` |
| Implementation PR | [#100](https://github.com/thedusk4203/Menuto/pull/100) |
| Implementation base | `12048deeffd8c0b30368df0684de1d971a2c4b9c` |
| Code/test/export commit | `090ef5f2a752b16fb20c876e057562a3a5e503ba` |
| Accepted final PR head | `af0c6fd9f199e19ec7e47e18b165c2eac6505c74` |
| Canonical merge/freeze SHA | `5728411ac12555f583f8df72ac71861998978aa4` |
| Exact post-merge push CI | [40351934792](https://github.com/thedusk4203/Menuto/actions/runs/40351934792), SUCCESS on the merge SHA above |
| Required jobs | `python` SUCCESS; `web` SUCCESS |
| Python regression | 2,597 passed, no skips; 2,377 retained + 220 additive |
| Real PostgreSQL / authority-source cases | 918 / 120; existing SCRAM/TLS smoke rerun 8/8 |
| Benchmark / client | 22/22 / 10/10; client typecheck and web build passed |
| Exported definitions | 318 = 299 retained unchanged + 19 additive |
| Schema | Alembic `0014`, 78 domain tables; no migration `0015` |
| Readiness | `planner_ready=False`; `activation_ready=False` |

The merge tree equals the accepted final head. Architecture/import boundaries, snapshots,
fixtures and the retained real-PostgreSQL migration/source enforcement checks passed in the
exact-merge CI. This receipt records an explicit user freeze, not a freeze inferred from CI.

## Frozen scope

Preferences owns the member-owned, one-exact-target consumer:

`derive_exact_target_prior_backed_affinity(subject)`.

Its frozen inputs are the complete 040B explicit input, coherent reviewed reference source,
authored compatibility policy and authored shrinkage policy. It recursively reparses primitives,
recomputes both frozen children, and independently verifies all mapped values, traces and hashes.
No cached/re-hashed summary supplies source authority. Replay is zero-IO and non-persistent.

Preserved decisions:

- all five exact target kinds: INGREDIENT / DIRECT_RECIPE / PROTEIN / METHOD / FLAVOR;
- complete per-kind explicit mapping pinned to the frozen explicit policy ID/version/fingerprint;
- finite exact reference lookup, one exact provider ID/immutable command hash/coordinate binding;
- no interpolation, extrapolation, nearest-neighbor mapping, provider fallback or aggregation;
- member RETRACTED yields MEMBER_RETRACTED, even with an available prior;
- active explicit + unavailable/unmapped prior yields observable explicit-only output;
- UNDECLARED + compatible prior yields prior-only cold start without minting EvidenceStrength;
- UNDECLARED, declared NEUTRAL, RETRACTED, NO_PUBLICATION and real AVAILABLE zero stay distinct;
- only the current explicit declaration head determines explicit affinity/strength; retries and history length do not increase evidence strength;
- ordinal LOW/MEDIUM/HIGH authored influence, LOW >= MEDIUM >= HIGH, active prior weights < 1;
- canonical exact rational convex arithmetic; no float, clipping, confidence or utility claims;
- VERSIONED_CONSUMER_POLICY_REPLAY with retained separate coherent source cuts;
- no simultaneous-liveness, historical AS_OF_CAPTURE policy-knowledge or canonical-DB-origin claim.

Frozen output coordinate identity is the complete descriptor:

```text
MEMBER_PROFILE_AFFINITY / coordinate_version 1
target_kind
full compatibility_policy_fingerprint
POLICY_MEMBER_PROFILE_AFFINITY_UNITS
ONE_COMPATIBILITY_POLICY_ONE_TARGET_KIND_EXACT_TARGET_ONLY
```

Mapped explicit/prior values, contributions and effective values are inseparable scoped values.
Descriptor mismatch rejects before arithmetic. Compatibility hashing covers the canonical authored
body before materializing descriptors. Shrinkage fingerprint is derivation provenance, outside
coordinate identity; changing shrinkage alone does not redefine the mapping scale.

**Exact target is bound in the outer derivation result, not in the coordinate descriptor.**
Same descriptor + same canonical fraction permits scoped numeric equality only. It does not prove
the same exact target, authorize transfer/inheritance/aggregation/ranking across targets, or grant
planner utility comparability. Different kind/policy has no defined comparison/aggregation semantics.

## Unavailable and unauthorized capabilities retained

```text
hierarchical_inference = NOT_PERFORMED
cross_target_inference = NOT_PERFORMED
candidate_aggregation = NOT_PERFORMED
learned/contextual/passive evidence = UNAVAILABLE
taste_fit = UNAVAILABLE
planner_ready = False
activation_ready = False
```

No production/default mapping or shrinkage values, prior corpus, profile persistence/cache,
HTTP endpoint, adapter, repository, worker, hierarchy, household aggregation, global history,
novelty, MTR-039 routing, TasteFit, planner integration, safety authority, Execution or PRECOMMIT
is supplied by this freeze. Full MTR-040/041/046 remain incomplete; 024/020B/021 remain BLOCKED.
Frozen 040B still returns its original unavailable prior/shrunk-affinity fields; PR #100 is additive.
Frozen 040A/B, 041A–F, 046A, prior-source contracts and migrations0001–0014 remain unchanged.

## Historical evidence and next gate

[Implementation evidence](EXACT_TARGET_PRIOR_COMPATIBILITY_SHRINKAGE_EVIDENCE.md) and
[approved design](EXACT_TARGET_PRIOR_COMPATIBILITY_SHRINKAGE_DESIGN.md) retain historical delivery
and authorization wording. Following the prior-source freeze precedent, this canonical receipt
supersedes **only their current-status interpretation**, not implementation receipts or semantics.
No current consumer remains NOT FROZEN merely because a historical delivery record says so.

[Post-freeze dependency review](POST_EXACT_TARGET_PRIOR_SHRINKAGE_DEPENDENCY_REVIEW.md) selects
**Hierarchical Preference Mapping & Derivation Foundation** for dedicated architecture/design only.
Runtime implementation, MTR-040C assignment, migration0015 and all downstream work are NOT AUTHORIZED.
